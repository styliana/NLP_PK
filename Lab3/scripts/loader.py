#!/usr/bin/env python3
"""
Ładowanie zbioru do PostgreSQL i Apache Solr 10 - trzy wielkości zbioru (10%, 50%, 100%).

PostgreSQL: CREATE TABLE (z kolumną tsvector GENERATED), COPY z pliku CSV, potem budowa indeksów
GIN i VACUUM ANALYZE - każdy etap mierzony osobno.
Solr: paczki po 5 000 dokumentów JSON przez /update bez commita, jeden commit na końcu.

Czasy zapisywane są do wyniki/load_times.json (benchmark dołącza je do wyników).
Użycie:  python scripts/loader.py                 # wszystkie trzy zbiory
         python scripts/loader.py --only 100%     # tylko pełny zbiór
"""

import argparse
import csv
import itertools
import json
import os
import sys
import time

import psycopg2
import requests

sys.path.insert(0, os.path.dirname(__file__))
from common import CSV_PATH, DATASETS, PG_CONFIG, RESULTS_DIR, SOLR_URL, SQL_DIR  # noqa: E402

LOAD_TIMES = os.path.join(RESULTS_DIR, "load_times.json")
SOLR_BATCH = 5000


class HeadReader:
    """Plikopodobny obiekt dla COPY: oddaje nagłówek i pierwsze `rows` wierszy CSV
    (prepare_data.py zapisuje jeden rekord na linię)."""

    def __init__(self, f, rows):
        self.f = f
        self.left = rows + 1

    def readline(self, size=-1):
        if self.left <= 0:
            return ""
        line = self.f.readline()
        if line:
            self.left -= 1
        return line

    def read(self, size=-1):
        parts, total = [], 0
        while self.left > 0 and (size is None or size < 0 or total < size):
            line = self.readline()
            if not line:
                break
            parts.append(line)
            total += len(line)
        return "".join(parts)


def count_rows(path):
    with open(path, encoding="utf-8") as f:
        return sum(1 for _ in f) - 1


def sql_template(name, table):
    with open(os.path.join(SQL_DIR, name), encoding="utf-8") as f:
        return f.read().replace("{t}", table)


def load_postgres(table, rows):
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    cur.execute(f"DROP TABLE IF EXISTS {table};")
    cur.execute(sql_template("02_schema.sql", table))
    conn.commit()

    t0 = time.perf_counter()
    with open(CSV_PATH, encoding="utf-8") as f:
        cur.copy_expert(
            f"COPY {table} (id, orig_id, copy_no, arxiv_id, title, abstract, field, category, "
            f"categories, year, n_versions) FROM STDIN WITH (FORMAT csv, HEADER true)",
            HeadReader(f, rows),
        )
    conn.commit()
    copy_s = time.perf_counter() - t0

    t0 = time.perf_counter()
    cur.execute(sql_template("03_indexes.sql", table))
    conn.commit()
    index_s = time.perf_counter() - t0

    conn.autocommit = True
    t0 = time.perf_counter()
    cur.execute(f"VACUUM ANALYZE {table};")
    vacuum_s = time.perf_counter() - t0

    cur.execute(f"SELECT count(*), pg_total_relation_size('{table}'), "
                f"pg_relation_size('{table}_tsv_gin') FROM {table};")
    count, total_bytes, gin_bytes = cur.fetchone()
    cur.close()
    conn.close()
    return {
        "rows": count,
        "copy_s": round(copy_s, 2),
        "index_s": round(index_s, 2),
        "vacuum_analyze_s": round(vacuum_s, 2),
        "total_s": round(copy_s + index_s + vacuum_s, 2),
        "table_total_mb": round(total_bytes / 1024 ** 2, 1),
        "gin_index_mb": round(gin_bytes / 1024 ** 2, 1),
    }


def to_solr_doc(row):
    return {
        "id": row["id"],
        "orig_id": int(row["orig_id"]),
        "copy_no": int(row["copy_no"]),
        "arxiv_id": row["arxiv_id"],
        "title": row["title"],
        "abstract": row["abstract"],
        "field": row["field"],
        "category": row["category"],
        "categories": row["categories"].split(),
        "year": int(row["year"]),
        "n_versions": int(row["n_versions"]),
    }


def load_solr(core, rows):
    session = requests.Session()
    update = f"{SOLR_URL}/{core}/update"
    session.post(update, params={"commit": "true"}, json={"delete": {"query": "*:*"}}).raise_for_status()

    t0 = time.perf_counter()
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = itertools.islice(csv.DictReader(f), rows)
        while True:
            batch = [to_solr_doc(r) for r in itertools.islice(reader, SOLR_BATCH)]
            if not batch:
                break
            r = session.post(update, json=batch, timeout=300)
            if r.status_code != 200:
                raise RuntimeError(f"Błąd paczki do {core}: {r.text[:500]}")
    upload_s = time.perf_counter() - t0

    t0 = time.perf_counter()
    session.post(update, json={"commit": {}}, timeout=600).raise_for_status()
    commit_s = time.perf_counter() - t0

    num_found = session.get(f"{SOLR_URL}/{core}/select", params={"q": "*:*", "rows": 0}).json()["response"]["numFound"]
    status = session.get(f"{SOLR_URL}/admin/cores", params={"action": "STATUS", "core": core}).json()
    index_bytes = status["status"][core]["index"]["sizeInBytes"]
    return {
        "docs": num_found,
        "upload_s": round(upload_s, 2),
        "commit_s": round(commit_s, 2),
        "total_s": round(upload_s + commit_s, 2),
        "index_mb": round(index_bytes / 1024 ** 2, 1),
        "batch_size": SOLR_BATCH,
    }


def main():
    parser = argparse.ArgumentParser(description="Loader PostgreSQL + Solr dla Lab 3")
    parser.add_argument("--only", choices=[d["label"] for d in DATASETS], help="załaduj tylko jeden zbiór")
    args = parser.parse_args()

    if not os.path.exists(CSV_PATH):
        sys.exit(f"Brak {CSV_PATH} - uruchom najpierw: python scripts/prepare_data.py")

    total = count_rows(CSV_PATH)
    results = {}
    if os.path.exists(LOAD_TIMES):
        with open(LOAD_TIMES, encoding="utf-8") as f:
            results = json.load(f)

    for ds in DATASETS:
        if args.only and ds["label"] != args.only:
            continue
        rows = int(total * ds["fraction"])
        print(f"\n=== Zbiór {ds['label']}: {rows} rekordów -> tabela {ds['table']}, rdzeń {ds['core']} ===")
        pg = load_postgres(ds["table"], rows)
        print(f"PostgreSQL: COPY {pg['copy_s']} s, indeksy {pg['index_s']} s, "
              f"VACUUM ANALYZE {pg['vacuum_analyze_s']} s, {pg['rows']} wierszy, {pg['table_total_mb']} MB")
        solr = load_solr(ds["core"], rows)
        print(f"Solr: wysyłka {solr['upload_s']} s, commit {solr['commit_s']} s, "
              f"{solr['docs']} dokumentów, indeks {solr['index_mb']} MB")
        if pg["rows"] != solr["docs"]:
            print("UWAGA: liczba rekordów w PostgreSQL i Solrze się różni!")
        results[ds["label"]] = {"rows": rows, "postgres": pg, "solr": solr}

        os.makedirs(RESULTS_DIR, exist_ok=True)
        with open(LOAD_TIMES, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nZapisano czasy ładowania do {LOAD_TIMES}")


if __name__ == "__main__":
    main()
