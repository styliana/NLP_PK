#!/usr/bin/env python3
"""
Wspólna konfiguracja dla loadera i benchmarku (Laboratorium nr 3: SQL kontra Solr).

Zbiór danych: abstrakty arXiv (gfissore/arxiv-abstracts-2021, licencja CC0 1.0).
Trzy wielkości zbioru do testu skalowania (10%, 50%, 100%) są osobnymi tabelami
w PostgreSQL i osobnymi rdzeniami w Solrze, ładowanymi z prefiksu tego samego pliku CSV.
"""

import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULTS_DIR = os.path.join(BASE_DIR, "wyniki")
PLOTS_DIR = os.path.join(BASE_DIR, "wykresy")
SQL_DIR = os.path.join(BASE_DIR, "sql")
CSV_PATH = os.path.join(DATA_DIR, "documents.csv")

PG_CONFIG = {
    "host": "localhost",
    "port": 5433,  # port z docker-compose.yml
    "dbname": "nlp_lab3",
    "user": "postgres",
    "password": "postgres",
}

SOLR_URL = "http://localhost:8983/solr"

# Kolejność ma znaczenie: od najmniejszego do pełnego zbioru.
DATASETS = [
    {"label": "10%", "fraction": 0.10, "table": "documents_p10", "core": "nlp_lab3_p10"},
    {"label": "50%", "fraction": 0.50, "table": "documents_p50", "core": "nlp_lab3_p50"},
    {"label": "100%", "fraction": 1.00, "table": "documents", "core": "nlp_lab3"},
]
FULL = DATASETS[-1]

CSV_COLUMNS = [
    "id", "orig_id", "copy_no", "arxiv_id", "title", "abstract",
    "field", "category", "categories", "year", "n_versions",
]

# Tekst przeszukiwany przez LIKE - te same pola, które trafiają do tsvector i do text_all w Solrze.
LIKE_TEXT = "(title || ' ' || abstract)"

# Trzy zapytania z poziomu 3.0 w trzech "dialektach".
QUERIES = {
    "Q1": {
        "name": "Q1: pojedyncze słowo w dowolnej formie (simulate)",
        "short": "Q1: simulate (dowolna forma)",
        "like": f"{LIKE_TEXT} LIKE '%simulate%'",
        "tsquery": "to_tsquery('english', 'simulate')",
        "solr": "simulate",
    },
    "Q2": {
        "name": "Q2: fraza (\"neural network\")",
        "short": "Q2: fraza \"neural network\"",
        "like": f"{LIKE_TEXT} LIKE '%neural network%'",
        "tsquery": "phraseto_tsquery('english', 'neural network')",
        "solr": "\"neural network\"",
    },
    "Q3": {
        "name": "Q3: quantum AND (entanglement OR teleportation) AND NOT photon",
        "short": "Q3: quantum ∧ (entanglement ∨ teleportation) ∧ ¬photon",
        "like": (f"{LIKE_TEXT} LIKE '%quantum%' AND ({LIKE_TEXT} LIKE '%entanglement%' "
                 f"OR {LIKE_TEXT} LIKE '%teleportation%') AND {LIKE_TEXT} NOT LIKE '%photon%'"),
        "tsquery": "to_tsquery('english', 'quantum & (entanglement | teleportation) & !photon')",
        "solr": "quantum AND (entanglement OR teleportation) AND NOT photon",
    },
}

# Liczba pomiarów (mediana) po jednym uruchomieniu rozgrzewającym.
RUNS = 5


def solr_lucene_q(query, cache=True):
    """Zapytanie standardowym parserem po polu text_all (tytuł + abstrakt).
    cache=False wyłącza queryResultCache dla tego zapytania, żeby Solr liczył wynik od nowa
    (PostgreSQL nie ma cache wyników, tylko cache stron danych)."""
    if cache:
        return query
    return "{!lucene df=text_all cache=false}" + query
