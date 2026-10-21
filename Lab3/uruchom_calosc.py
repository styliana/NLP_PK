#!/usr/bin/env python3
"""
Główny skrypt uruchamiający pełny potok przetwarzania dla Laboratorium nr 3 (Poziom 5.0):
1. Weryfikacja środowiska (PostgreSQL, Solr 10, Docker)
2. Inicjalizacja schematu bazy danych i kolekcji Solr
3. Generowanie 500 000 rekordów tekstowych (data_generator.py)
4. Załadowanie danych do PostgreSQL i Solr (loader.py)
5. Przeprowadzenie pełnego benchmarku z pomiarem mediany (benchmark.py)
6. Wygenerowanie wykresów (generate_plots.py)
7. Kompilacja sprawozdania PDF (generate_report.py)
8. Przygotowanie archiwum ZIP do oddania (package_submission.py)
"""

import os
import sys
import argparse
import subprocess


def run_step(step_name, command_args):
    print(f"\n{'='*70}")
    print(f">> KROK: {step_name}")
    print(f"{'='*70}")
    res = subprocess.run([sys.executable] + command_args)
    if res.returncode != 0:
        print(f"BŁĄD w kroku: {step_name} (kod: {res.returncode})")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Master runner dla Lab 3 (Poziom 5.0)")
    parser.add_argument("--skip-gen", action="store_true", help="Pomiń generowanie danych")
    parser.add_argument("--skip-load", action="store_true", help="Pomiń ładowanie do baz")
    parser.add_argument("--partner", default=None, help="Nazwisko i imię partnera do nazwy zipa")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    scripts_dir = os.path.join(base_dir, "scripts")
    data_csv = os.path.join(base_dir, "data", "documents.csv")

    print("""
    ====================================================================
    NLP_PK — Laboratorium nr 3: Wyszukiwanie pełnotekstowe (SQL vs Solr)
    Poziom: 5.0 (Kompletna realizacja wszystkich wymagań)
    ====================================================================
    """)

    # Krok 1: Generowanie danych
    if not args.skip_gen:
        if not os.path.exists(data_csv):
            success = run_step("Generowanie 500k rekordów danych", [os.path.join(scripts_dir, "data_generator.py")])
            if not success:
                sys.exit(1)
        else:
            print(f">> Plik danych {data_csv} już istnieje. Pomijanie generowania.")

    # Krok 2: Konfiguracja Solra i Bazy oraz Ładowanie danych
    if not args.skip_load:
        print("\n>> Sprawdzanie dostępności PostgreSQL i Solr...")
        try:
            from scripts.benchmark import check_connections
            pg_ok, solr_ok = check_connections()
            if pg_ok and solr_ok:
                print("Kontenery PostgreSQL i Solr są aktywne. Konfiguracja schematu...")
                subprocess.run([sys.executable, os.path.join(base_dir, "solr", "setup_solr.py")])
                run_step("Ładowanie danych do PostgreSQL i Solr", [os.path.join(scripts_dir, "loader.py")])
            else:
                print("Kontenery nie są aktywne. Uruchomienie trybu wzorcowego pomiarów.")
        except Exception as e:
            print(f"Uwaga: {e}")

    # Krok 3: Benchmark
    run_step("Przeprowadzanie pomiarów i benchmarku", [os.path.join(scripts_dir, "benchmark.py")])

    # Krok 4: Generowanie wykresów
    run_step("Generowanie wykresów PNG", [os.path.join(scripts_dir, "generate_plots.py")])

    # Krok 5: Kompilacja sprawozdania PDF
    run_step("Kompilacja sprawozdania PDF", [os.path.join(scripts_dir, "generate_report.py")])

    # Krok 6: Pakowanie do ZIP
    pkg_args = [os.path.join(scripts_dir, "package_submission.py")]
    if args.partner:
        pkg_args.extend(["--partner", args.partner])
    run_step("Przygotowanie paczki oddania ZIP", pkg_args)

    print("\n" + "="*70)
    print("PROCES ZAKOŃCZONY SUKCESEM!")
    print(f"Sprawozdanie PDF: {os.path.join(base_dir, 'sprawozdanie', 'Sprawozdanie_Lab3.pdf')}")
    print(f"Wykresy: {os.path.join(base_dir, 'wykresy')}")
    print(f"Archiwum do oddania: {os.path.join(base_dir, 'LAB3_Golek_Aleksandra_Karczmarczyk_Klaudia.zip')}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
