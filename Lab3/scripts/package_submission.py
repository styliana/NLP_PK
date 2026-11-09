#!/usr/bin/env python3
"""
Skrypt pakujący kompletne rozwiązanie Laboratorium nr 3 do archiwum ZIP
zgodnie z wymogami platformy Delta opisanymi w Lab3.pdf:
- Nazwa: LAB3_Nazwisko_Imie_Nazwisko_Imie.zip
- Zawiera: kod (generator, loader, zapytania), skrypty SQL, schemat Solra,
  README z instrukcją uruchomienia oraz sprawozdanie PDF i wykresy.
- NIE zawiera dużych plików danych CSV (zgodnie z instrukcją).
"""

import os
import zipfile
import argparse

DEFAULT_NAME = "LAB3_Golek_Aleksandra_Karczmarczyk_Klaudia.zip"


def create_submission_zip(output_zip_path=None):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    if not output_zip_path:
        output_zip_path = os.path.join(base_dir, DEFAULT_NAME)

    print(f"Tworzenie archiwum oddania: {output_zip_path}...")

    # Pliki i katalogi do spakowania
    include_paths = [
        "docker-compose.yml",
        "README.md",
        "requirements.txt",
        "uruchom_calosc.py",
        "sql/01_init.sql",
        "sql/02_schema.sql",
        "sql/03_indexes.sql",
        "sql/queries.sql",
        "solr/schema_api.json",
        "solr/managed-schema.json",
        "solr/setup_solr.py",
        "scripts/common.py",
        "scripts/prepare_data.py",
        "scripts/loader.py",
        "scripts/benchmark.py",
        "scripts/summary.py",
        "scripts/generate_plots.py",
        "scripts/package_submission.py",
        "wykresy/skalowanie_zapytan.png",
        "wykresy/czasy_zapytan_porownanie.png",
        "wykresy/facety_vs_groupby.png",
        "wykresy/glebokie_stronicowanie.png",
        "wykresy/rozszerzenia_porownanie.png",
        "wyniki/dataset_stats.json",
        "wyniki/load_times.json",
        "wyniki/benchmark_results.json",
        "wyniki/benchmark_summary.md",
        "sprawozdanie/Sprawozdanie_Lab3.pdf"
    ]
    include_paths.append("sprawozdanie/build_sprawozdanie.py")
    for sub in ("wyniki/explain", "sprawozdanie/screeny"):
        folder = os.path.join(base_dir, *sub.split("/"))
        if os.path.isdir(folder):
            include_paths += [f"{sub}/{f}" for f in sorted(os.listdir(folder))]

    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for rel_path in include_paths:
            full_path = os.path.join(base_dir, rel_path)
            if os.path.exists(full_path):
                zipf.write(full_path, arcname=rel_path)
                print(f"  Dodano: {rel_path}")
            else:
                print(f"  OSTRZEŻENIE: Brak pliku: {rel_path}")

    zip_size_mb = os.path.getsize(output_zip_path) / (1024 * 1024)
    print(f"\nSukces! Utworzono paczkę: {output_zip_path} ({zip_size_mb:.2f} MB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pakowanie rozwiązania Lab 3 do ZIP")
    parser.add_argument("--output", default=None, help="Ścieżka do docelowego pliku .zip")
    parser.add_argument("--partner", default=None, help="Nazwisko i imię partnera (np. Kowalski_Jan)")
    args = parser.parse_args()

    if args.partner:
        out_name = f"LAB3_Golek_Aleksandra_{args.partner}.zip"
        target_path = os.path.join(os.path.dirname(__file__), "..", out_name)
    else:
        target_path = args.output

    create_submission_zip(target_path)
