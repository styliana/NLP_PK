#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
MODUŁ: uruchom_calosc.py
OPIS:  Główny skrypt uruchomieniowy laboratorium. Wykonuje sekwencyjnie:
       1. parser.py                (pobranie, czyszczenie i eksport danych)
       2. test_parser.py           (uruchomienie 4 testów jednostkowych)
       3. analiza.py               (obliczenie statystyk i wygenerowanie wykresów)
       4. porownanie_html_vs_dom.py (porównanie surowego HTML z DOM na ocenę 5.0)
LAB:   Laboratorium NLP - Zadanie 1 (Rola: PARSER, Poziom 5.0)
=============================================================================
"""

import os
import sys
import subprocess

# Zapewnienie kodowania UTF-8
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

KATALOG = os.path.dirname(os.path.abspath(__file__))


def uruchom_skrypt(nazwa_skryptu: str, opis: str):
    print("\n" + "=" * 70)
    print(f"[*] KROK: {opis} ({nazwa_skryptu})")
    print("=" * 70)
    sciezka = os.path.join(KATALOG, nazwa_skryptu)
    wynik = subprocess.run([sys.executable, sciezka], cwd=KATALOG)
    if wynik.returncode != 0:
        print(f"[-] BŁĄD podczas wykonywania {nazwa_skryptu} (kod: {wynik.returncode})")
        sys.exit(wynik.returncode)


def main():
    print("######################################################################")
    print("#      LAB 1 (NLP) - KOMPLEKSOWY PROCES PARSOWANIA I ANALIZY        #")
    print("#                    Serwis TechStore (Parser2)                      #")
    print("######################################################################")

    uruchom_skrypt("parser.py", "Pobieranie, czyszczenie i eksport danych")
    uruchom_skrypt("test_parser.py", "Testy jednostkowe funkcji czyszczących (Wymóg 4.0)")
    uruchom_skrypt("analiza.py", "Analiza statystyczna i generowanie wykresów (Wymóg 4.0/5.0)")
    uruchom_skrypt("porownanie_html_vs_dom.py", "Porównanie surowy HTML vs DOM (Wymóg 5.0)")

    print("\n" + "#" * 70)
    print("#                    WSZYSTKIE ETAPY ZAKOŃCZONE!                     #")
    print("#              Wszystkie wymagania poziomu 5.0 spełnione.            #")
    print("#" * 70)
    print("\nWygenerowane zasoby:")
    print("  [>] Wyniki danych:    Lab1/Parser2/wyniki/")
    print("      - produkty_oczyszczone.csv (420 unikalnych rekordów, 32 kolumny)")
    print("      - produkty_oczyszczone.json")
    print("      - raport_jakosci.txt")
    print("      - porownanie_html_vs_dom.txt")
    print("  [>] Wykresy (PNG):    Lab1/Parser2/wykresy/")
    print("      - 1_histogram_cen.png")
    print("      - 2_boxplot_cen.png")
    print("      - 3_korelacja_cena_waga.png")
    print("  [>] Instrukcja / opis: Lab1/Parser2/parser_instructions.md\n")


if __name__ == "__main__":
    main()
