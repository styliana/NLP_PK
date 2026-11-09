#!/usr/bin/env python3
"""
Pełny potok Laboratorium nr 3 (poziom 5.0):
1. pobranie i przygotowanie zbioru arXiv (scripts/prepare_data.py)
2. konfiguracja rdzeni Solra (solr/setup_solr.py)
3. załadowanie 10% / 50% / 100% do PostgreSQL i Solra (scripts/loader.py)
4. pomiary (scripts/benchmark.py) -> wyniki/benchmark_results.json + benchmark_summary.md
5. wykresy (scripts/generate_plots.py) -> wykresy/*.png
6. archiwum ZIP do oddania (scripts/package_submission.py)

Wymaga działających kontenerów: docker compose up -d
"""

import argparse
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run_step(title, script, *args):
    print(f"\n{'=' * 70}\n>> {title}\n{'=' * 70}", flush=True)
    res = subprocess.run([sys.executable, os.path.join(BASE_DIR, script), *args])
    if res.returncode != 0:
        sys.exit(f"BŁĄD w kroku: {title} (kod {res.returncode})")


def main():
    parser = argparse.ArgumentParser(description="Pełny potok Lab 3")
    parser.add_argument("--skip-prepare", action="store_true", help="nie przygotowuj danych ponownie")
    parser.add_argument("--skip-load", action="store_true", help="nie ładuj danych ponownie")
    parser.add_argument("--originals", default="500000", help="liczba unikalnych artykułów")
    args = parser.parse_args()

    if not args.skip_prepare:
        run_step("Przygotowanie zbioru arXiv", "scripts/prepare_data.py", "--originals", args.originals)
    if not args.skip_load:
        run_step("Konfiguracja Solra", "solr/setup_solr.py")
        run_step("Ładowanie danych (10%, 50%, 100%)", "scripts/loader.py")
    run_step("Pomiary", "scripts/benchmark.py")
    run_step("Wykresy", "scripts/generate_plots.py")
    run_step("Archiwum ZIP", "scripts/package_submission.py")
    print("\nGotowe. Tabele: wyniki/benchmark_summary.md, wykresy: wykresy/")


if __name__ == "__main__":
    main()
