#!/usr/bin/env python3
"""
Pomiary i porównanie funkcjonalne PostgreSQL 16 (tsvector + GIN) i Apache Solr 10 - Lab 3, poziom 5.0.

Wszystko jest mierzone na żywych bazach; bez połączenia skrypt kończy się błędem.
Metodyka: 1 uruchomienie rozgrzewające, potem RUNS (5) pomiarów i mediana.
SQL: czas po stronie klienta + "Execution Time" z EXPLAIN (ANALYZE, BUFFERS) (plany w wyniki/explain/).
Solr: QTime + czas po stronie klienta; wariant bez cache wyników ({!... cache=false}) jako główny,
bo PostgreSQL nie ma cache wyników zapytań - wariant z cache zapisujemy obok.

Zakres:
  3.0  Q1-Q3 w SQL (LIKE + FTS) i w Solrze (q, fq, fl, sort, rows) + pełne URL-e
  4.0  ranking top-10 (ts_rank_cd vs eDisMax z qf), GROUP BY, facety, podświetlanie, porównanie top-10,
       czasy ładowania (z loadera)
  5.0  skalowanie 10/50/100%, facety (2 pola + facet.range) vs GROUP BY
  Rozszerzenia: literówki (fuzzy vs pg_trgm vs LIKE), własny typ pola + Analysis vs to_tsvector,
       duplikaty po powieleniu (collapse vs DISTINCT ON), głębokie stronicowanie (start vs cursorMark)
"""

import json
import os
import platform
import re
import statistics
import subprocess
import sys
import time

import psycopg2
import requests

sys.path.insert(0, os.path.dirname(__file__))
from common import (DATASETS, FULL, PG_CONFIG, QUERIES, RESULTS_DIR, RUNS, SOLR_URL,  # noqa: E402
                    solr_lucene_q)

EXPLAIN_DIR = os.path.join(RESULTS_DIR, "explain")
SESSION = requests.Session()
EDISMAX_QF = "title^3 abstract"
HEADLINE_OPTS = "MaxFragments=1, MaxWords=25, MinWords=12, StartSel=<em>, StopSel=</em>"


# ---------------------------------------------------------------------------- pomiary

def ms(t0):
    return (time.perf_counter() - t0) * 1000.0


def sql_measure(cur, sql, name=None, runs=RUNS):
    """Mediana czasu klienta z `runs` uruchomień (po rozgrzewce) + EXPLAIN ANALYZE."""
    cur.execute(sql)
    rows = cur.fetchall()
    times = []
    for _ in range(runs):
        t0 = time.perf_counter()
        cur.execute(sql)
        rows = cur.fetchall()
        times.append(ms(t0))
    result = {"sql": " ".join(sql.split()), "median_ms": round(statistics.median(times), 2),
              "times_ms": [round(t, 2) for t in times], "rows": rows}
    if name:
        cur.execute("EXPLAIN (ANALYZE, BUFFERS) " + sql)
        plan = "\n".join(r[0] for r in cur.fetchall())
        os.makedirs(EXPLAIN_DIR, exist_ok=True)
        with open(os.path.join(EXPLAIN_DIR, f"{name}.txt"), "w", encoding="utf-8") as f:
            f.write(result["sql"] + "\n\n" + plan + "\n")
        m = re.search(r"Execution Time: ([\d.]+) ms", plan)
        result["explain_execution_ms"] = float(m.group(1)) if m else None
    return result


def solr_url(core, params, handler="select"):
    return requests.Request("GET", f"{SOLR_URL}/{core}/{handler}", params=params).prepare().url


def solr_get(core, params, handler="select"):
    r = SESSION.get(f"{SOLR_URL}/{core}/{handler}", params=params, timeout=120)
    body = r.json()
    if r.status_code != 200 or "error" in body:
        raise RuntimeError(f"Solr {core}: {body.get('error', {}).get('msg', r.text[:300])}\n{r.url}")
    return body


def solr_measure(core, params, runs=RUNS):
    body = solr_get(core, params)
    client, qtimes = [], []
    for _ in range(runs):
        t0 = time.perf_counter()
        body = solr_get(core, params)
        client.append(ms(t0))
        qtimes.append(body["responseHeader"]["QTime"])
    return {"url": solr_url(core, params), "median_client_ms": round(statistics.median(client), 2),
            "median_qtime_ms": statistics.median(qtimes), "qtimes_ms": qtimes,
            "numFound": body.get("response", {}).get("numFound"), "body": body}


def strip(m):
    """Usuwa z wyniku pomiaru surowe dane (wiersze / odpowiedź), zostawia liczby i zapytanie."""
    return {k: v for k, v in m.items() if k not in ("rows", "body")}


# ---------------------------------------------------------------------------- środowisko

def environment(cur):
    env = {"python": platform.python_version(), "os": platform.platform()}
    cur.execute("SHOW server_version;")
    env["postgres_version"] = cur.fetchone()[0]
    for setting in ("shared_buffers", "work_mem", "max_parallel_workers_per_gather", "jit"):
        cur.execute(f"SHOW {setting};")
        env[f"postgres_{setting}"] = cur.fetchone()[0]
    info = SESSION.get(f"{SOLR_URL}/admin/info/system", timeout=10).json()
    env["solr_version"] = info.get("lucene", {}).get("solr-spec-version")
    env["solr_jvm"] = info.get("jvm", {}).get("version")
    env["solr_heap_max_mb"] = round(info.get("jvm", {}).get("memory", {}).get("raw", {}).get("max", 0) / 1024 ** 2)
    if platform.system() == "Windows":
        def ps(cmd):
            return subprocess.run(["powershell", "-NoProfile", "-Command", cmd],
                                  capture_output=True, text=True).stdout.strip()
        env["cpu"] = ps("(Get-CimInstance Win32_Processor).Name")
        env["ram_gb"] = ps("[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)")
        env["disk"] = ps("(Get-PhysicalDisk | Select-Object -First 1 | "
                         "ForEach-Object { $_.FriendlyName + ' (' + $_.MediaType + ')' })")
    else:
        env["cpu"] = platform.processor()
    try:
        env["docker_mem_gb"] = round(int(subprocess.run(
            ["docker", "info", "--format", "{{.MemTotal}}"], capture_output=True, text=True).stdout) / 1024 ** 3, 1)
    except (ValueError, OSError):
        env["docker_mem_gb"] = None
    return env


# ---------------------------------------------------------------------------- 3.0 / 4.0: zapytania

def top10_sql(tsquery, table):
    return (f"SELECT id, orig_id, title, ts_rank_cd(tsv, {tsquery}) AS rank FROM {table} "
            f"WHERE tsv @@ {tsquery} ORDER BY rank DESC, id LIMIT 10")


def duplicate_pairs(docs):
    origs = [int(d["orig_id"]) for d in docs]
    return sum(1 for o in set(origs) if origs.count(o) > 1)


def run_queries(cur):
    t, core = FULL["table"], FULL["core"]
    out = {}
    for key, q in QUERIES.items():
        print(f"  {key}...")
        like = sql_measure(cur, f"SELECT count(*) FROM {t} WHERE {q['like']}", f"{key}_like_count")
        fts_count = sql_measure(cur, f"SELECT count(*) FROM {t} WHERE tsv @@ {q['tsquery']}", f"{key}_fts_count")
        fts_top = sql_measure(cur, top10_sql(q["tsquery"], t), f"{key}_fts_top10")

        base = {"df": "text_all", "rows": 10, "fl": "id,orig_id,title,score"}
        solr_nocache = solr_measure(core, dict(base, q=solr_lucene_q(q["solr"], cache=False)))
        solr_cache = solr_measure(core, dict(base, q=q["solr"]))

        # wariant z pozostałymi parametrami z instrukcji: fq, fl, sort, rows
        fq_params = {"q": q["solr"], "df": "text_all", "fq": "year:[2015 TO *]",
                     "fl": "id,title,year,category", "sort": "year desc,score desc", "rows": 5}
        solr_fq = solr_measure(core, fq_params, runs=1)
        sql_fq = sql_measure(cur, f"SELECT count(*) FROM {t} WHERE tsv @@ {q['tsquery']} AND year >= 2015", runs=1)

        # 4.0: eDisMax z wagami pól + podświetlanie
        edismax_params = {"defType": "edismax", "q": q["solr"], "qf": EDISMAX_QF, "rows": 10,
                          "fl": "id,orig_id,title,score", "hl": "true", "hl.fl": "abstract",
                          "hl.snippets": 1, "hl.fragsize": 160}
        edismax = solr_measure(core, edismax_params)
        headline = sql_measure(
            cur, f"SELECT id, ts_headline('english', abstract, {q['tsquery']}, '{HEADLINE_OPTS}') "
                 f"FROM {t} WHERE id IN (SELECT id FROM ({top10_sql(q['tsquery'], t)}) s)",
            f"{key}_ts_headline")

        sql_docs = [{"id": str(r[0]), "orig_id": r[1], "title": r[2], "score": round(float(r[3]), 4)}
                    for r in fts_top["rows"]]
        solr_docs = [{"id": d["id"], "orig_id": d["orig_id"], "title": d["title"], "score": round(d["score"], 3)}
                     for d in edismax["body"]["response"]["docs"]]
        overlap = len({d["id"] for d in sql_docs} & {d["id"] for d in solr_docs})
        first_id = solr_docs[0]["id"] if solr_docs else None
        hl_solr = (edismax["body"].get("highlighting", {}).get(first_id, {}).get("abstract") or [""])[0]
        cur.execute(f"SELECT ts_headline('english', abstract, {q['tsquery']}, '{HEADLINE_OPTS}') "
                    f"FROM {t} WHERE id = %s", (int(first_id),))
        hl_sql = cur.fetchone()[0] if first_id else None

        out[key] = {
            "name": q["name"], "short": q["short"],
            "like_count": like["rows"][0][0], "like": strip(like),
            "fts_count": fts_count["rows"][0][0], "fts_count_query": strip(fts_count),
            "fts_top10_query": strip(fts_top),
            "solr_numFound": solr_nocache["numFound"],
            "solr": strip(solr_nocache), "solr_cached": strip(solr_cache),
            "solr_fq_sort_example": dict(strip(solr_fq), docs=solr_fq["body"]["response"]["docs"]),
            "sql_fq_example_count": sql_fq["rows"][0][0],
            "edismax": dict(strip(edismax), numFound=edismax["numFound"]),
            "ts_headline": strip(headline),
            "top10_sql": sql_docs, "top10_solr": solr_docs,
            "top10_overlap": overlap,
            "top10_duplicate_pairs_sql": duplicate_pairs(sql_docs),
            "top10_duplicate_pairs_solr": duplicate_pairs(solr_docs),
            "highlight_doc_id": first_id, "highlight_solr": hl_solr, "highlight_sql": hl_sql,
        }
    return out


def groupby_4_0(cur):
    q = QUERIES["Q1"]["tsquery"]
    m = sql_measure(cur, f"SELECT field, count(*) FROM {FULL['table']} WHERE tsv @@ {q} "
                         f"GROUP BY field ORDER BY 2 DESC", "Q1_groupby_field")
    return dict(strip(m), result=[list(r) for r in m["rows"]])


# ---------------------------------------------------------------------------- 5.0: skalowanie

def scaling(cur):
    out = {}
    for ds in DATASETS:
        cur.execute(f"SELECT to_regclass('{ds['table']}') IS NOT NULL")
        if not cur.fetchone()[0]:
            print(f"  pomijam {ds['label']} - brak tabeli {ds['table']} (uruchom loader)")
            continue
        cur.execute(f"SELECT count(*) FROM {ds['table']}")
        rows = cur.fetchone()[0]
        print(f"  {ds['label']} ({rows} rekordów)...")
        per_q = {}
        for key, q in QUERIES.items():
            like = sql_measure(cur, f"SELECT count(*) FROM {ds['table']} WHERE {q['like']}")
            fts_count = sql_measure(cur, f"SELECT count(*) FROM {ds['table']} WHERE tsv @@ {q['tsquery']}")
            fts_top = sql_measure(cur, top10_sql(q["tsquery"], ds["table"]))
            solr = solr_measure(ds["core"], {"q": solr_lucene_q(q["solr"], cache=False), "rows": 10,
                                             "fl": "id,score"})
            per_q[key] = {
                "like_ms": like["median_ms"], "like_count": like["rows"][0][0],
                "fts_count_ms": fts_count["median_ms"], "fts_count": fts_count["rows"][0][0],
                "fts_top10_ms": fts_top["median_ms"],
                "solr_client_ms": solr["median_client_ms"], "solr_qtime_ms": solr["median_qtime_ms"],
                "solr_numFound": solr["numFound"],
            }
        out[ds["label"]] = {"records": rows, "queries": per_q}
    return out


# ---------------------------------------------------------------------------- 5.0: facety vs GROUP BY

def facets_vs_groupby(cur):
    t, core = FULL["table"], FULL["core"]
    out = {}
    for label, where, solr_q in (("Q1", f"tsv @@ {QUERIES['Q1']['tsquery']}", solr_lucene_q(QUERIES["Q1"]["solr"], False)),
                                 ("all", "TRUE", "{!lucene cache=false}*:*")):
        print(f"  facety dla {label}...")
        params = {"q": solr_q, "rows": 0, "facet": "true",
                  "facet.field": ["field", "category"], "f.category.facet.limit": 10,
                  "f.field.facet.limit": -1, "facet.mincount": 1,
                  "facet.range": "year", "facet.range.start": 1990, "facet.range.end": 2025,
                  "facet.range.gap": 5}
        solr = solr_measure(core, params)
        ff = solr["body"]["facet_counts"]["facet_fields"]
        pairs = lambda lst: dict(zip(lst[::2], lst[1::2]))  # noqa: E731
        solr_res = {"field": pairs(ff["field"]), "category": pairs(ff["category"]),
                    "year": pairs(solr["body"]["facet_counts"]["facet_ranges"]["year"]["counts"])}

        bucket = "1990 + 5 * ((year - 1990) / 5)"
        g1 = sql_measure(cur, f"SELECT field, count(*) FROM {t} WHERE {where} GROUP BY field ORDER BY 2 DESC",
                         f"facet_{label}_groupby_field")
        g2 = sql_measure(cur, f"SELECT category, count(*) FROM {t} WHERE {where} GROUP BY category "
                              f"ORDER BY 2 DESC LIMIT 10", f"facet_{label}_groupby_category")
        g3 = sql_measure(cur, f"SELECT {bucket} AS y, count(*) FROM {t} WHERE {where} AND year >= 1990 "
                              f"GROUP BY y ORDER BY y", f"facet_{label}_groupby_year")
        gs = sql_measure(cur, f"SELECT field, category, {bucket} AS y, count(*) FROM {t} WHERE {where} "
                              f"GROUP BY GROUPING SETS ((field), (category), ({bucket}))",
                         f"facet_{label}_grouping_sets")
        sql_res = {"field": {r[0]: r[1] for r in g1["rows"]},
                   "category": {r[0]: r[1] for r in g2["rows"]},
                   "year": {str(r[0]): r[1] for r in g3["rows"]}}
        out[label] = {
            "solr": dict(strip(solr), numFound=solr["numFound"]),
            "solr_counts": solr_res,
            "sql_field": strip(g1), "sql_category": strip(g2), "sql_year": strip(g3),
            "sql_three_queries_ms": round(g1["median_ms"] + g2["median_ms"] + g3["median_ms"], 2),
            "sql_grouping_sets": strip(gs),
            "sql_counts": sql_res,
            "counts_equal": {k: solr_res[k] == sql_res[k] for k in solr_res},
        }
    return out


# ---------------------------------------------------------------------------- rozszerzenia

def ext_fuzzy(cur):
    t, core = FULL["table"], FULL["core"]
    out = {}
    for typo, correct in (("entanglment", "entanglement"), ("superconductivty", "superconductivity")):
        print(f"  literówka '{typo}'...")
        like = sql_measure(cur, f"SELECT count(*) FROM {t} WHERE title LIKE '%{typo}%'", f"fuzzy_{typo}_like")
        trgm = sql_measure(cur, f"SELECT count(*) FROM {t} WHERE '{typo}' <% title", f"fuzzy_{typo}_trgm")
        trgm_top = sql_measure(cur, f"SELECT title, word_similarity('{typo}', title) AS s FROM {t} "
                                    f"WHERE '{typo}' <% title ORDER BY s DESC, id LIMIT 5", runs=1)
        exact = solr_measure(core, {"q": f"title_exact:{typo}", "rows": 0})
        fuzzy = solr_measure(core, {"q": f"{{!lucene cache=false}}title_exact:{typo}~2", "rows": 5, "fl": "title"})
        correct_q = solr_measure(core, {"q": f"title_exact:{correct}", "rows": 0}, runs=1)
        out[typo] = {
            "correct_word": correct,
            "like": dict(strip(like), count=like["rows"][0][0]),
            "pg_trgm": dict(strip(trgm), count=trgm["rows"][0][0],
                            top5=[[r[0], round(float(r[1]), 3)] for r in trgm_top["rows"]]),
            "solr_exact": dict(strip(exact), count=exact["numFound"]),
            "solr_fuzzy": dict(strip(fuzzy), count=fuzzy["numFound"],
                               top5=[d["title"] for d in fuzzy["body"]["response"]["docs"]]),
            "solr_correct_word_count": correct_q["numFound"],
        }
    return out


ANALYSIS_SENTENCES = [
    "The simulated annealing algorithms were simulating complex networks' behaviour.",
    "Next-to-leading order QCD corrections for e+e- annihilation at 10 TeV energies.",
    "We don't observe photons; the photonic crystals' band gaps were measured in 2019.",
]


def ext_analysis(cur):
    core = FULL["core"]
    out = []
    for s in ANALYSIS_SENTENCES:
        body = solr_get(core, {"analysis.fieldtype": "text_en_lab", "analysis.fieldvalue": s},
                        handler="analysis/field")
        stages = body["analysis"]["field_types"]["text_en_lab"]["index"]
        chain = []
        for i in range(0, len(stages), 2):
            chain.append({"stage": stages[i].split(".")[-1], "tokens": [tok["text"] for tok in stages[i + 1]]})
        cur.execute("SELECT to_tsvector('english', %s)::text", (s,))
        out.append({"sentence": s, "solr_chain": chain, "solr_tokens": chain[-1]["tokens"],
                    "pg_to_tsvector": cur.fetchone()[0]})
    return out


def ext_collapse(cur):
    t, core = FULL["table"], FULL["core"]
    q = QUERIES["Q1"]
    print("  collapse po orig_id...")
    plain = solr_measure(core, {"defType": "edismax", "q": q["solr"], "qf": EDISMAX_QF, "rows": 10,
                                "fl": "id,orig_id,copy_no,title,score"})
    collapsed = solr_measure(core, {"defType": "edismax", "q": q["solr"], "qf": EDISMAX_QF, "rows": 10,
                                    "fl": "id,orig_id,copy_no,title,score", "fq": "{!collapse field=orig_id}"})
    no_copies = solr_measure(core, {"defType": "edismax", "q": q["solr"], "qf": EDISMAX_QF, "rows": 0,
                                    "fq": "copy_no:0"}, runs=1)
    sql_plain = sql_measure(cur, top10_sql(q["tsquery"], t))
    sql_dedup = sql_measure(cur, (
        f"SELECT id, orig_id, title, rank FROM ("
        f"SELECT DISTINCT ON (orig_id) id, orig_id, title, ts_rank_cd(tsv, {q['tsquery']}) AS rank "
        f"FROM {t} WHERE tsv @@ {q['tsquery']} ORDER BY orig_id, rank DESC, id) s "
        f"ORDER BY rank DESC, id LIMIT 10"), "collapse_sql_distinct_on")
    sql_distinct_count = sql_measure(cur, f"SELECT count(DISTINCT orig_id) FROM {t} WHERE tsv @@ {q['tsquery']}",
                                     runs=1)

    def docs(m):
        return [{"id": d["id"], "orig_id": d["orig_id"], "copy_no": d["copy_no"], "title": d["title"]}
                for d in m["body"]["response"]["docs"]]

    return {
        "query": q["name"],
        "solr_plain": dict(strip(plain), duplicate_pairs=duplicate_pairs(docs(plain)), docs=docs(plain)),
        "solr_collapse": dict(strip(collapsed), duplicate_pairs=duplicate_pairs(docs(collapsed)),
                              docs=docs(collapsed)),
        "solr_numFound_without_copies": no_copies["numFound"],
        "sql_plain_top10": dict(strip(sql_plain),
                                duplicate_pairs=duplicate_pairs([{"orig_id": r[1]} for r in sql_plain["rows"]])),
        "sql_distinct_on": dict(strip(sql_dedup),
                                duplicate_pairs=duplicate_pairs([{"orig_id": r[1]} for r in sql_dedup["rows"]])),
        "sql_distinct_orig_count": sql_distinct_count["rows"][0][0],
    }


def ext_deep_paging(cur):
    t, core = FULL["table"], FULL["core"]
    total = solr_get(core, {"q": "*:*", "rows": 0})["response"]["numFound"]
    positions = [p for p in (0, 1_000, 10_000, 100_000, 250_000, 500_000) if p < total - 10]
    print(f"  zbieranie cursorMark dla pozycji {positions}...")
    step = 1000
    marks, cursor, pos = {0: "*"}, "*", 0
    while pos < positions[-1]:
        body = solr_get(core, {"q": "*:*", "sort": "id asc", "rows": step, "fl": "id", "cursorMark": cursor})
        cursor = body["nextCursorMark"]
        pos += step
        marks[pos] = cursor

    out = []
    for p in positions:
        print(f"  strona od pozycji {p}...")
        start = solr_measure(core, {"q": "{!lucene cache=false}*:*", "sort": "id asc", "rows": 10,
                                    "start": p, "fl": "id"})
        cur_m = solr_measure(core, {"q": "{!lucene cache=false}*:*", "sort": "id asc", "rows": 10,
                                    "cursorMark": marks[p], "fl": "id"})
        same = [d["id"] for d in start["body"]["response"]["docs"]] == \
               [d["id"] for d in cur_m["body"]["response"]["docs"]]
        offset = sql_measure(cur, f"SELECT id FROM {t} ORDER BY id LIMIT 10 OFFSET {p}")
        cur.execute(f"SELECT id FROM {t} ORDER BY id OFFSET {p - 1} LIMIT 1" if p else "SELECT 0")
        key = cur.fetchone()[0]
        keyset = sql_measure(cur, f"SELECT id FROM {t} WHERE id > {key} ORDER BY id LIMIT 10")
        out.append({
            "position": p,
            "solr_start_ms": start["median_client_ms"], "solr_start_qtime_ms": start["median_qtime_ms"],
            "solr_cursor_ms": cur_m["median_client_ms"], "solr_cursor_qtime_ms": cur_m["median_qtime_ms"],
            "solr_same_page": same,
            "sql_offset_ms": offset["median_ms"], "sql_keyset_ms": keyset["median_ms"],
            "solr_start_url": start["url"],
        })
    return out


# ---------------------------------------------------------------------------- main

def check_services():
    try:
        psycopg2.connect(**PG_CONFIG, connect_timeout=3).close()
    except psycopg2.Error as e:
        sys.exit(f"Brak połączenia z PostgreSQL ({e}). Uruchom: docker compose up -d")
    try:
        SESSION.get(f"{SOLR_URL}/{FULL['core']}/admin/ping", timeout=5).raise_for_status()
    except requests.RequestException as e:
        sys.exit(f"Brak połączenia z Solrem ({e}). Uruchom: docker compose up -d")


def main():
    check_services()
    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"SELECT count(*) FROM {FULL['table']}")
    full_rows = cur.fetchone()[0]
    solr_docs = solr_get(FULL["core"], {"q": "*:*", "rows": 0})["response"]["numFound"]
    if full_rows == 0 or full_rows != solr_docs:
        sys.exit(f"Niespójne dane: PostgreSQL {full_rows} wierszy, Solr {solr_docs} dokumentów - uruchom loader.")

    results = {"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "runs": RUNS, "records": full_rows}
    print("Środowisko...")
    results["environment"] = environment(cur)
    for name in ("dataset_stats", "load_times"):
        path = os.path.join(RESULTS_DIR, f"{name}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                results[name] = json.load(f)

    steps = [
        ("queries", "Zapytania Q1-Q3 (3.0/4.0)", run_queries),
        ("groupby", "GROUP BY (4.0)", groupby_4_0),
        ("scaling", "Skalowanie 10/50/100% (5.0)", scaling),
        ("facets_vs_groupby", "Facety vs GROUP BY (5.0)", facets_vs_groupby),
        ("ext_fuzzy", "Rozszerzenie: literówki", ext_fuzzy),
        ("ext_analysis", "Rozszerzenie: własny typ pola + Analysis", ext_analysis),
        ("ext_collapse", "Rozszerzenie: duplikaty / collapse", ext_collapse),
        ("ext_deep_paging", "Rozszerzenie: głębokie stronicowanie", ext_deep_paging),
    ]
    for key, label, fn in steps:
        print(f"\n== {label} ==")
        results[key] = fn(cur)

    cur.close()
    conn.close()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out = os.path.join(RESULTS_DIR, "benchmark_results.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nZapisano {out}")

    from summary import write_summary
    write_summary(results, os.path.join(RESULTS_DIR, "benchmark_summary.md"))


if __name__ == "__main__":
    main()
