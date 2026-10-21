#!/usr/bin/env python3
"""
Generator zbioru danych dla Laboratorium nr 3 (NLP: SQL kontra Solr).
Generuje 500 000 rekordów technicznych artykułów/recenzji w języku naturalnym.
Zawiera:
- Unikalny klucz id i orig_id
- Tytuł oraz bogatą treść w języku naturalnym (średnia długość > 350 znaków)
- Prawdziwe słownictwo z odmianami gramatycznymi (stemming) i frazami
- 2 pola kategoryczne (category, tag)
- Pola liczbowe/daty (rating, published_year)
- Obsługę powielenia z flagą copy_no (dla rozszerzenia Collapsing / DISTINCT)
"""

import os
import csv
import random
import time

CATEGORIES = [
    "Artificial Intelligence",
    "Cloud Computing",
    "Cybersecurity",
    "Data Science",
    "Software Engineering"
]

TAGS = [
    "Python",
    "Docker",
    "Algorithms",
    "Databases",
    "DevOps",
    "NLP",
    "Performance",
    "Security"
]

TITLES_PARTS_1 = [
    "Modern Architectural Patterns for",
    "Comprehensive Analysis of",
    "Optimizing and Benchmarking",
    "Practical Guide to",
    "Evaluation and Performance of",
    "Scalable Deployments with",
    "Deep Dive into",
    "Empirical Comparison of",
    "Advanced Strategies for",
    "Production Ready Systems with"
]

TITLES_PARTS_2 = [
    "Distributed High Throughput Services",
    "Modern Natural Language Processing Models",
    "Enterprise Cloud Infrastructure and Security",
    "Database Query Optimization and Indexing",
    "Machine Learning Pipelines in Kubernetes",
    "Resilient Microservices with Low Latency",
    "Automated Vulnerability Detection in Code",
    "Scalable Full Text Search Engines",
    "Event Driven Real Time Data Streams",
    "High Performance Vector Databases"
]

SENTENCE_POOL_1 = [
    "In this comprehensive study, we explore how software engineers perform critical benchmarks on modern architectures.",
    "Engineers consistently perform rigorous evaluation of production workloads to maintain minimal latency.",
    "Recent experiments demonstrated that the team performed extensive profiling before deploying the search cluster.",
    "The overall system performance improves drastically when indexing strategies are aligned with query execution plans.",
    "Performing automated stress testing revealed significant bottlenecks in concurrent connection pooling."
]

SENTENCE_POOL_2 = [
    "We investigate state of the art machine learning models running on distributed clusters.",
    "The integration of modern machine learning techniques allows real-time classification of incoming text streams.",
    "When training complex machine learning models, memory bandwidth and vector acceleration play a crucial role.",
    "Applied machine learning methods require clean data pipelines and robust feature validation."
]

SENTENCE_POOL_3 = [
    "Database performance and operational speed are paramount when serving millions of active users without slow response times.",
    "A properly configured database delivers exceptional speed while eliminating slow query degradation under heavy load.",
    "Modern database engines prioritize query speed and execution throughput to ensure no slow transactions block the queue.",
    "Optimizing database indices guarantees high transactional speed and prevents slow table scans across large datasets."
]

SENTENCE_POOL_4 = [
    "Additionally, the architecture incorporates fault tolerance mechanisms to mitigate unexpected hardware failures.",
    "Furthermore, security audits showed that strict authorization policies prevented unauthorized data exposure.",
    "The experimental evaluation confirmed that caching layers reduce backend round trips by more than sixty percent.",
    "Statistical metrics gathered across thousands of runs provide strong empirical support for our hypotheses.",
    "Our findings highlight the trade-offs between memory footprint, processing throughput, and retrieval accuracy."
]


def generate_dataset(output_path, total_records=500000, unique_records=250000):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    start_time = time.time()
    print(f"Rozpoczynanie generowania {total_records} rekordów ({unique_records} unikalnych, 1 powielenie)...")

    # Ustalony seed dla pełnej deterministyczności wyników
    random.seed(42)

    fieldnames = ["id", "orig_id", "title", "content", "category", "tag", "rating", "published_year", "copy_no"]

    total_chars = 0

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Bufor na unikalne rekordy, by je powielić
        unique_samples = []

        # Krok 1: Generowanie unikalnych rekordów
        for i in range(1, unique_records + 1):
            t1 = TITLES_PARTS_1[i % len(TITLES_PARTS_1)]
            t2 = TITLES_PARTS_2[(i * 3) % len(TITLES_PARTS_2)]
            title = f"{t1} {t2} #{i}"

            s1 = SENTENCE_POOL_1[(i + 1) % len(SENTENCE_POOL_1)]
            s2 = SENTENCE_POOL_2[(i + 3) % len(SENTENCE_POOL_2)]
            s3 = SENTENCE_POOL_3[(i + 7) % len(SENTENCE_POOL_3)]
            s4 = SENTENCE_POOL_4[(i + 11) % len(SENTENCE_POOL_4)]
            content = f"{s1} {s2} {s3} {s4}"

            total_chars += len(content)

            category = CATEGORIES[i % len(CATEGORIES)]
            tag = TAGS[(i * 2) % len(TAGS)]
            rating = round(random.uniform(1.0, 5.0), 1)
            published_year = random.randint(2018, 2026)

            record = {
                "id": i,
                "orig_id": i,
                "title": title,
                "content": content,
                "category": category,
                "tag": tag,
                "rating": rating,
                "published_year": published_year,
                "copy_no": 0
            }
            writer.writerow(record)

            # Zapisujemy wybrane pola dla powielenia
            unique_samples.append((title, content, category, tag, rating, published_year))

            if i % 50000 == 0:
                print(f"  Wygenerowano unikalnych: {i}/{unique_records}...")

        # Krok 2: Powielenie (kopia z zachowaniem orig_id i copy_no=1)
        remaining = total_records - unique_records
        for j in range(1, remaining + 1):
            doc_id = unique_records + j
            orig_id = j
            sample = unique_samples[j - 1]

            record = {
                "id": doc_id,
                "orig_id": orig_id,
                "title": sample[0],
                "content": sample[1],
                "category": sample[2],
                "tag": sample[3],
                "rating": sample[4],
                "published_year": sample[5],
                "copy_no": 1
            }
            writer.writerow(record)

            if j % 50000 == 0:
                print(f"  Wygenerowano kopii: {j}/{remaining}...")

    elapsed = time.time() - start_time
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    avg_chars = total_chars / unique_records

    print(f"\nSukces! Wygenerowano plik: {output_path}")
    print(f"Liczba rekordów: {total_records}")
    print(f"Średnia długość tekstu (content): {avg_chars:.1f} znaków (wymóg: min. 300)")
    print(f"Rozmiar pliku CSV: {file_size_mb:.2f} MB")
    print(f"Czas generowania: {elapsed:.2f} s")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generator zbioru danych dla Lab 3")
    parser.add_argument("--output", default=os.path.join(os.path.dirname(__file__), "..", "data", "documents.csv"))
    parser.add_argument("--total", type=int, default=500000)
    parser.add_argument("--unique", type=int, default=250000)
    args = parser.parse_args()

    generate_dataset(args.output, args.total, args.unique)
