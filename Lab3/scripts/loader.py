#!/usr/bin/env python3
"""
Moduł ładowania danych do PostgreSQL i Apache Solr 10.
- PostgreSQL: wykorzystuje szybki strumień COPY (psycopg2)
- Solr 10: ładuje paczkami (5 000 dokumentów w JSON) przez endpoint /update,
  z pojedynczym zatwierdzeniem (commit=true) na końcu.
Mierzy i zwraca dokładne czasy ładowania oraz indeksowania.
"""

import os
import csv
import json
import time
import requests
import psycopg2

PG_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "nlp_lab3",
    "user": "postgres",
    "password": "postgres"
}

SOLR_BASE_URL = "http://localhost:8983/solr"
CORE_NAME = "nlp_lab3"


def load_to_postgres(csv_path, batch_size=50000):
    print("\n--- Rozpoczynanie ładowania danych do PostgreSQL ---")
    start_time = time.time()

    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    # Czyszczenie istniejących danych
    print("Czyszczenie tabeli documents...")
    cur.execute("TRUNCATE TABLE documents RESTART IDENTITY;")
    conn.commit()

    print(f"Strumieniowanie z pliku: {csv_path} przez COPY...")
    copy_start = time.time()
    with open(csv_path, "r", encoding="utf-8") as f:
        copy_sql = """
        COPY documents(id, orig_id, title, content, category, tag, rating, published_year, copy_no)
        FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER ',');
        """
        cur.copy_expert(copy_sql, f)
    conn.commit()
    copy_duration = time.time() - copy_start

    # Weryfikacja liczby wierszy
    cur.execute("SELECT count(*) FROM documents;")
    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    total_duration = time.time() - start_time
    print(f"Zakończono ładowanie do PostgreSQL: {count} rekordów.")
    print(f"Czas COPY: {copy_duration:.2f} s | Całkowity czas: {total_duration:.2f} s")
    return {
        "count": count,
        "copy_time": copy_duration,
        "total_time": total_duration
    }


def load_to_solr(csv_path, batch_size=5000):
    print("\n--- Rozpoczynanie ładowania danych do Apache Solr 10 ---")
    start_time = time.time()

    update_url = f"{SOLR_BASE_URL}/{CORE_NAME}/update"

    # Czyszczenie istniejących dokumentów w Solr
    print("Usuwanie starych dokumentów z rdzenia Solr...")
    requests.post(update_url, json={"delete": {"query": "*:*"}}, headers={"Content-Type": "application/json"})
    requests.post(f"{update_url}?commit=true")

    print(f"Wysyłanie paczek dokumentów po {batch_size} do {update_url}...")
    batch = []
    total_loaded = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc = {
                "id": row["id"],
                "orig_id": int(row["orig_id"]),
                "title": row["title"],
                "content": row["content"],
                "category": row["category"],
                "tag": row["tag"],
                "rating": float(row["rating"]),
                "published_year": int(row["published_year"]),
                "copy_no": int(row["copy_no"])
            }
            batch.append(doc)

            if len(batch) >= batch_size:
                r = requests.post(f"{update_url}?commit=false", json=batch, headers={"Content-Type": "application/json"})
                if r.status_code != 200:
                    print(f"Błąd ładowania paczki: {r.text}")
                total_loaded += len(batch)
                if total_loaded % 50000 == 0:
                    print(f"  Załadowano do Solr: {total_loaded} dokumentów...")
                batch = []

        if batch:
            requests.post(f"{update_url}?commit=false", json=batch, headers={"Content-Type": "application/json"})
            total_loaded += len(batch)

    print("Wykonywanie końcowego zatwierdzenia (commit=true)...")
    commit_start = time.time()
    r = requests.post(f"{update_url}?commit=true")
    commit_duration = time.time() - commit_start

    # Weryfikacja liczby dokumentów
    verify_url = f"{SOLR_BASE_URL}/{CORE_NAME}/select?q=*:*&rows=0"
    res = requests.get(verify_url).json()
    num_found = res.get("response", {}).get("numFound", 0)

    total_duration = time.time() - start_time
    print(f"Zakończono ładowanie do Solr: {num_found} dokumentów.")
    print(f"Czas wysyłki paczek: {(total_duration - commit_duration):.2f} s | Czas commit: {commit_duration:.2f} s | Całkowity czas: {total_duration:.2f} s")

    return {
        "count": num_found,
        "commit_time": commit_duration,
        "total_time": total_duration
    }


if __name__ == "__main__":
    csv_file = os.path.join(os.path.dirname(__file__), "..", "data", "documents.csv")
    if not os.path.exists(csv_file):
        print(f"Brak pliku {csv_file}. Wygeneruj go najpierw za pomocą data_generator.py")
    else:
        # Próba ładowania jeśli usługi są włączone
        try:
            load_to_postgres(csv_file)
        except Exception as e:
            print(f"Błąd ładowania PostgreSQL: {e}")

        try:
            load_to_solr(csv_file)
        except Exception as e:
            print(f"Błąd ładowania Solr: {e}")
