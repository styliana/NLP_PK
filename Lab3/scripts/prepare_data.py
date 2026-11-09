#!/usr/bin/env python3
"""
Pobranie i przygotowanie zbioru danych dla Laboratorium nr 3.

Źródło: arXiv abstracts 2021 - https://huggingface.co/datasets/gfissore/arxiv-abstracts-2021
Licencja: CC0 1.0 (metadane arXiv). Plik: arxiv-abstracts.jsonl.gz (~940 MB, ~2 mln artykułów).

Co robi skrypt:
1. pobiera plik .jsonl.gz do data/ (jeśli go jeszcze nie ma),
2. wybiera deterministyczną, równomierną próbkę: N artykułów o najmniejszym crc32(identyfikatora arXiv)
   (dwa strumieniowe przebiegi po pliku - plik jest posortowany po dacie, więc nie bierzemy "pierwszych N"),
3. pomija dane osobowe (autorzy, zgłaszający) - zostają tylko tytuł, abstrakt i metadane,
4. wylicza pola: field (grupa arXiv, 8 wartości), category (kategoria główna), year (z id arXiv),
5. co N-ty rekord powiela (copy_no=1, orig_id = id oryginału) - kopia trafia zaraz za oryginał,
   więc każdy prefiks pliku (10%, 50%) ma ten sam udział kopii,
6. zapisuje data/documents.csv oraz statystyki do wyniki/dataset_stats.json.
"""

import argparse
import csv
import gzip
import json
import os
import re
import sys
import time
import zlib

import requests

sys.path.insert(0, os.path.dirname(__file__))
from common import CSV_COLUMNS, CSV_PATH, DATA_DIR, RESULTS_DIR  # noqa: E402

SOURCE_URL = "https://huggingface.co/datasets/gfissore/arxiv-abstracts-2021/resolve/main/arxiv-abstracts.jsonl.gz"
SOURCE_FILE = os.path.join(DATA_DIR, "arxiv-abstracts.jsonl.gz")
SOURCE_SIZE = 939_914_256

# Grupy arXiv (https://arxiv.org/category_taxonomy) + stare archiwa sprzed reorganizacji.
FIELD_BY_ARCHIVE = {
    "cs": "Computer Science", "cmp-lg": "Computer Science",
    "math": "Mathematics", "alg-geom": "Mathematics", "dg-ga": "Mathematics",
    "funct-an": "Mathematics", "q-alg": "Mathematics",
    "stat": "Statistics", "bayes-an": "Statistics",
    "q-bio": "Quantitative Biology",
    "q-fin": "Quantitative Finance",
    "eess": "Electrical Engineering and Systems Science",
    "econ": "Economics",
}

WHITESPACE = re.compile(r"\s+")


def download(url, path):
    if os.path.exists(path) and os.path.getsize(path) == SOURCE_SIZE:
        print(f"Plik źródłowy już pobrany: {path}")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"Pobieranie {url}\n  -> {path} (~{SOURCE_SIZE / 1024 ** 2:.0f} MB)")
    tmp = path + ".part"
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        done = 0
        last = time.time()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                done += len(chunk)
                if time.time() - last > 5:
                    print(f"  {done / 1024 ** 2:.0f} / {SOURCE_SIZE / 1024 ** 2:.0f} MB")
                    last = time.time()
    os.replace(tmp, path)


def year_from_arxiv_id(arxiv_id):
    # nowy format: YYMM.NNNNN, stary: archiwum/YYMMNNN
    yy = int(arxiv_id.split("/")[-1][:2])
    return 1900 + yy if yy >= 91 else 2000 + yy


def field_from_category(category):
    archive = re.split(r"[.]", category)[0]
    return FIELD_BY_ARCHIVE.get(archive, "Physics")


def clean(text):
    return WHITESPACE.sub(" ", text or "").strip()


def sample_key(arxiv_id):
    return zlib.crc32(arxiv_id.encode()), arxiv_id


def is_usable(rec):
    return bool(clean(rec.get("title")) and clean(rec.get("abstract")) and rec.get("categories"))


def pick_threshold(originals):
    """Przebieg 1: klucz próbkowania każdego artykułu; zwraca klucz N-tego najmniejszego.
    Dzięki temu próbka jest równomierna w całym pliku (plik jest posortowany po id, czyli po dacie)."""
    keys = []
    with gzip.open(SOURCE_FILE, "rt", encoding="utf-8") as src:
        for line in src:
            rec = json.loads(line)
            if is_usable(rec):
                keys.append(sample_key(rec["id"]))
    keys.sort()
    print(f"  artykułów w źródle: {len(keys)}")
    if originals >= len(keys):
        return keys[-1], len(keys)
    return keys[originals - 1], len(keys)


def prepare(originals, copy_every):
    download(SOURCE_URL, SOURCE_FILE)

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    t0 = time.time()
    print(f"Przebieg 1: wybór {originals} artykułów o najmniejszym crc32(id)...")
    threshold, source_total = pick_threshold(originals)
    print(f"Przebieg 2: zapis CSV, powielenie co {copy_every}. rekordu...")

    next_id = 1
    n_orig = n_copies = 0
    abstract_lens = []
    field_counts = {}
    categories_seen = set()
    years = []
    sample_record = None

    with gzip.open(SOURCE_FILE, "rt", encoding="utf-8") as src, \
            open(CSV_PATH, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for line in src:
            rec = json.loads(line)
            arxiv_id = rec["id"]
            if not is_usable(rec) or sample_key(arxiv_id) > threshold:
                continue
            title = clean(rec.get("title"))
            abstract = clean(rec.get("abstract"))
            cats = " ".join(rec.get("categories") or []).split()
            if not cats:
                continue

            row = {
                "id": next_id,
                "orig_id": next_id,
                "copy_no": 0,
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "field": field_from_category(cats[0]),
                "category": cats[0],
                "categories": " ".join(cats),
                "year": year_from_arxiv_id(arxiv_id),
                "n_versions": len(rec.get("versions") or []) or 1,
            }
            writer.writerow(row)
            n_orig += 1
            next_id += 1
            if sample_record is None:
                sample_record = dict(row)

            abstract_lens.append(len(abstract))
            field_counts[row["field"]] = field_counts.get(row["field"], 0) + 1
            categories_seen.add(row["category"])
            years.append(row["year"])

            if copy_every and n_orig % copy_every == 0:
                copy = dict(row, id=next_id, copy_no=1)
                writer.writerow(copy)
                n_copies += 1
                next_id += 1

            if n_orig % 50_000 == 0:
                print(f"  oryginałów: {n_orig}, kopii: {n_copies}")

    abstract_lens.sort()
    stats = {
        "source": "arXiv abstracts 2021 (gfissore/arxiv-abstracts-2021, Hugging Face)",
        "source_url": "https://huggingface.co/datasets/gfissore/arxiv-abstracts-2021",
        "license": "CC0 1.0 (metadane arXiv); autorzy i zgłaszający pominięci - brak danych osobowych",
        "source_articles": source_total,
        "sampling": f"{n_orig} z {source_total} artykułów o najmniejszym crc32(arxiv_id) "
                    f"(deterministyczna, równomierna próbka)",
        "originals": n_orig,
        "copies": n_copies,
        "total_records": n_orig + n_copies,
        "copy_rule": f"co {copy_every}. oryginał powielony (copy_no=1, orig_id=id oryginału)",
        "csv_size_mb": round(os.path.getsize(CSV_PATH) / 1024 ** 2, 1),
        "abstract_chars_avg": round(sum(abstract_lens) / len(abstract_lens), 1),
        "abstract_chars_median": abstract_lens[len(abstract_lens) // 2],
        "abstract_chars_min": abstract_lens[0],
        "abstract_chars_max": abstract_lens[-1],
        "distinct_fields": len(field_counts),
        "field_counts": dict(sorted(field_counts.items(), key=lambda kv: -kv[1])),
        "distinct_categories": len(categories_seen),
        "year_min": min(years),
        "year_max": max(years),
        "sample_record": sample_record,
        "prepare_time_s": round(time.time() - t0, 1),
    }
    with open(os.path.join(RESULTS_DIR, "dataset_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"\nZapisano {CSV_PATH}")
    print(f"Rekordów: {stats['total_records']} ({n_orig} oryginałów + {n_copies} kopii), "
          f"{stats['csv_size_mb']} MB")
    print(f"Długość abstraktu: śr. {stats['abstract_chars_avg']} znaków, "
          f"mediana {stats['abstract_chars_median']}, min {stats['abstract_chars_min']}")
    print(f"Pola kategoryczne: field = {stats['distinct_fields']} wartości, "
          f"category = {stats['distinct_categories']} wartości; lata {stats['year_min']}-{stats['year_max']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Przygotowanie zbioru arXiv dla Lab 3")
    parser.add_argument("--originals", type=int, default=500_000, help="liczba unikalnych artykułów")
    parser.add_argument("--copy-every", type=int, default=10, help="powiel co N-ty artykuł (0 = bez kopii)")
    args = parser.parse_args()
    prepare(args.originals, args.copy_every)
