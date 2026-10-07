#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
MODUŁ: parser.py
OPIS:  Główny silnik parsera dla serwisu TechStore (Parser2).
       Pobiera dane, normalizuje waluty i daty, czyści wagi i oceny,
       eliminuje duplikaty, sortuje rekordy rosnąco wg ID
       oraz eksportuje do CSV, XLSX (Excel) i JSON.
LAB:   Laboratorium NLP - Zadanie 1 (Rola: PARSER, Poziom 5.0)
=============================================================================
"""

import os
import re
import csv
import sys
import json
import argparse
import statistics
import urllib.request
import urllib.error
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional

# Zapewnienie kodowania UTF-8 na wyjściu konsoli Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Stałe ścieżek
KATALOG_BAZOWY = os.path.dirname(os.path.abspath(__file__))
DOMYSLNY_URL = "http://localhost:8000/dane/produkty.json"
DOMYSLNY_PLIK_LOKALNY = os.path.join(KATALOG_BAZOWY, "strona", "dane", "produkty.json")
FOLDER_WYNIKOW = os.path.join(KATALOG_BAZOWY, "wyniki")

# Kursy walut określone w specyfikacji serwisu TechStore
KURSY_WALUT = {
    "PLN": 1.0,
    "EUR": 4.30,
    "USD": 4.00,
}


def parsuj_cene(cena_str: Optional[str]) -> Tuple[Optional[float], Optional[str], Optional[float]]:
    """
    Czyści i normalizuje tekst ceny z różnych walut (PLN, EUR, USD).
    Zwraca: (cena_oryginalna, waluta, cena_przeliczona_na_pln)
    """
    if not cena_str:
        return None, None, None

    surowa = str(cena_str).replace("\xa0", " ").strip()

    if surowa.startswith("$"):
        waluta = "USD"
    elif "€" in surowa:
        waluta = "EUR"
    else:
        waluta = "PLN"

    czysta_liczba = re.sub(r"[^\d,\.]", "", surowa)

    if waluta == "USD":
        czysta_liczba = czysta_liczba.replace(",", "")
    else:
        czysta_liczba = czysta_liczba.replace(",", ".")

    try:
        kwota = round(float(czysta_liczba), 2)
        kurs = KURSY_WALUT.get(waluta, 1.0)
        kwota_pln = round(kwota * kurs, 2)
        return kwota, waluta, kwota_pln
    except ValueError:
        return None, waluta, None


def parsuj_wage(waga_str: Optional[str]) -> Optional[float]:
    """Konwertuje tekst wagi (np. '1,43 kg') na liczbę zmiennoprzecinkową w kg."""
    if not waga_str:
        return None
    czysta = str(waga_str).replace("kg", "").replace(",", ".").strip()
    try:
        return round(float(czysta), 3)
    except ValueError:
        return None


def formatuj_date_pl(data_str: Optional[str]) -> Optional[str]:
    """
    Konwertuje datę do formatu wyświetlanego na stronie (DD.MM.YYYY).
    Np. '2024-11-15' -> '15.11.2024'.
    """
    if not data_str:
        return None
    s = str(data_str).strip()
    # Format YYYY-MM-DD -> DD.MM.YYYY
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        r, m, d = s.split("-")
        return f"{d}.{m}.{r}"
    return s


def parsuj_gwarancje(gwarancja_raw: Any) -> Tuple[Optional[int], str]:
    """Wyodrębnia liczbę miesięcy gwarancji i czytelny tekst."""
    if gwarancja_raw in (None, "", "—", "brak informacji"):
        return None, "brak informacji"
    znalezione = re.findall(r"\d+", str(gwarancja_raw))
    if znalezione:
        miesiace = int(znalezione[0])
        return miesiace, f"{miesiace} mies."
    return None, str(gwarancja_raw).strip()


def oczysc_produkt(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizuje atrybuty produktu.
    Kolejność kolumn odpowiada DOKŁADNIE kolejności kolumn w tabeli na stronie:
    SKU -> Nazwa -> Kategoria -> Producent -> Cena -> Dostępność -> Ocena -> Opinie -> Data dodania -> Gwarancja -> Kolor -> Waga.
    """
    cena_wartosc, cena_waluta, cena_pln = parsuj_cene(p.get("cena"))
    koszt_dost_wartosc, _, _ = parsuj_cene(p.get("koszt_dostawy"))

    # Ocena (jako float)
    ocena = p.get("ocena")
    if ocena is not None:
        try:
            ocena = round(float(ocena), 2)
        except (ValueError, TypeError):
            ocena = None

    # Waga
    waga_tekst = str(p.get("waga", "")).strip()
    waga_liczba = parsuj_wage(p.get("waga"))

    # Gwarancja
    gw_miesiace, gw_tekst = parsuj_gwarancje(p.get("gwarancja"))

    # Daty (format DD.MM.YYYY zgodny z widokiem strony)
    data_dodania = formatuj_date_pl(p.get("data_dodania"))
    data_premiery = formatuj_date_pl(p.get("data_premiery"))

    # Spłaszczenie specyfikacji technicznej za pomocą ' | '
    specyfikacja_dict = p.get("specyfikacja", {}) or {}
    specyfikacja_tekst = " | ".join(f"{k}: {v}" for k, v in specyfikacja_dict.items())

    # Układ kolumn zgodny 1:1 z tabelą na stronie internetowej
    rekord = {
        # Identyfikatory i dane podstawowe
        "id": p.get("id"),
        "sku": p.get("sku", ""),
        "nazwa": p.get("nazwa", "").strip(),
        "kategoria": p.get("kategoria", "").strip(),
        "producent": p.get("producent", "").strip(),

        # Ceny (znormalizowane i waluty)
        "cena_pln": cena_pln,
        "waluta": cena_waluta,
        "cena_oryginalna": cena_wartosc,

        # Kolumny dokładnie w kolejności tabeli na stronie
        "dostepnosc": p.get("dostepnosc", ""),
        "ocena": ocena,
        "liczba_opinii": p.get("liczba_opinii", 0),
        "data_dodania": data_dodania,
        "gwarancja": gw_tekst,
        "kolor": p.get("kolor", ""),
        "waga": waga_tekst,
        "waga_kg": waga_liczba,

        # Dodatkowe atrybuty ze strony szczegółów
        "stan_magazynowy": p.get("stan_magazynowy", 0),
        "wymiary": p.get("wymiary", ""),
        "material": p.get("material", ""),
        "kraj_pochodzenia": p.get("kraj_pochodzenia", ""),
        "data_premiery": data_premiery,
        "sprzedawca": p.get("sprzedawca", ""),
        "czas_dostawy": p.get("czas_dostawy", ""),
        "koszt_dostawy_pln": koszt_dost_wartosc if koszt_dost_wartosc is not None else 0.0,
        "ean": p.get("ean", ""),
        "numer_katalogowy": p.get("numer_katalogowy", ""),
        "zawartosc_zestawu": p.get("zawartosc_zestawu", ""),
        "specyfikacja": specyfikacja_tekst,
        "opis": p.get("opis", ""),
        "link": p.get("link", ""),
    }
    return rekord


def pobierz_surowe_dane(url: str = DOMYSLNY_URL, local_path: str = DOMYSLNY_PLIK_LOKALNY) -> List[Dict[str, Any]]:
    """Pobiera dane z serwera HTTP lub jako fallback z pliku lokalnego."""
    print(f"[*] Próba pobrania danych z: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TechStore-NLP-Parser/2.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                dane = json.loads(resp.read().decode("utf-8"))
                produkty = dane.get("produkty", [])
                print(f"    [+] Pomyślnie pobrano {len(produkty)} produktów przez HTTP.")
                return produkty
    except Exception as e:
        print(f"    [-] Połączenie HTTP ({e}). Używam lokalnego pliku: {local_path}")

    sciezki = [
        local_path,
        os.path.join(KATALOG_BAZOWY, "strona", "dane", "produkty.json"),
        os.path.join(KATALOG_BAZOWY, "dane", "produkty.json"),
    ]
    for s in sciezki:
        if os.path.exists(s):
            with open(s, "r", encoding="utf-8") as f:
                dane = json.load(f)
                produkty = dane.get("produkty", [])
                print(f"    [+] Wczytano {len(produkty)} produktów z pliku lokalnego: {s}")
                return produkty

    raise FileNotFoundError(f"Nie znaleziono pliku danych pod adresem {url} ani lokalnie.")


def filtruj_i_deduplikuj(surowe_produkty: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Oczyszcza produkty, eliminuje duplikaty oraz sortuje rekordy wg ID rosnąco (1001..1420).
    """
    widziane_id = set()
    unikalne_rekordy: List[Dict[str, Any]] = []
    licznik_duplikatow = 0
    braki_oceny = 0
    braki_gwarancji = 0
    waluty_stat = {"PLN": 0, "EUR": 0, "USD": 0}
    ceny_pln: List[float] = []
    oceny: List[float] = []

    for item in surowe_produkty:
        p_id = item.get("id")
        if p_id in widziane_id:
            licznik_duplikatow += 1
            continue

        widziane_id.add(p_id)
        oczyszczony = oczysc_produkt(item)
        unikalne_rekordy.append(oczyszczony)

        if oczyszczony["ocena"] is None:
            braki_oceny += 1
        else:
            oceny.append(oczyszczony["ocena"])

        if oczyszczony["gwarancja"] == "brak informacji":
            braki_gwarancji += 1

        waluta = oczyszczony["waluta"]
        if waluta in waluty_stat:
            waluty_stat[waluta] += 1

        if oczyszczony["cena_pln"] is not None:
            ceny_pln.append(oczyszczony["cena_pln"])

    # Kluczowe: sortowanie wg ID rosnąco, aby rekordy były ułożone od 1001 w górę
    unikalne_rekordy.sort(key=lambda x: x["id"])

    n = len(unikalne_rekordy)
    statystyki = {
        "pobrane_ogolem": len(surowe_produkty),
        "unikalne_rekordy": n,
        "odrzucone_duplikaty": licznik_duplikatow,
        "braki_oceny": braki_oceny,
        "braki_oceny_procent": round((braki_oceny / n) * 100, 2) if n else 0,
        "braki_gwarancji": braki_gwarancji,
        "braki_gwarancji_procent": round((braki_gwarancji / n) * 100, 2) if n else 0,
        "waluty": waluty_stat,
        "cena_min_pln": min(ceny_pln) if ceny_pln else 0,
        "cena_max_pln": max(ceny_pln) if ceny_pln else 0,
        "cena_srednia_pln": round(statistics.mean(ceny_pln), 2) if ceny_pln else 0,
        "cena_mediana_pln": round(statistics.median(ceny_pln), 2) if ceny_pln else 0,
        "ocena_srednia": round(statistics.mean(oceny), 2) if oceny else 0,
    }
    return unikalne_rekordy, statystyki


def zapisz_wyniki(rekordy: List[Dict[str, Any]], folder: str = FOLDER_WYNIKOW) -> Tuple[str, str, str]:
    """Zapisuje oczyszczone dane do uporządkowanego pliku CSV, XLSX (Excel) oraz JSON."""
    os.makedirs(folder, exist_ok=True)
    sciezka_csv = os.path.join(folder, "produkty_oczyszczone.csv")
    sciezka_xlsx = os.path.join(folder, "produkty_oczyszczone.xlsx")
    sciezka_json = os.path.join(folder, "produkty_oczyszczone.json")

    pola = list(rekordy[0].keys())

    # 1. Zapis CSV (utf-8-sig z separatorem ;)
    try:
        with open(sciezka_csv, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=pola, delimiter=";")
            writer.writeheader()
            for r in rekordy:
                row_dict = {k: ("" if v is None else v) for k, v in r.items()}
                writer.writerow(row_dict)
        print(f"[+] Zapisano CSV  : {sciezka_csv} ({len(rekordy)} rekordów, {len(pola)} kolumn)")
    except PermissionError:
        print(f"[!] Info: Plik CSV jest otwarty w Excelu ({sciezka_csv}) – pomijam nadpisywanie.")

    # 2. Zapis XLSX (rodzimy format Excela - 0 problemów z separatorami)
    try:
        df = pd.DataFrame(rekordy)
        df.to_excel(sciezka_xlsx, index=False)
        print(f"[+] Zapisano XLSX : {sciezka_xlsx} (gotowy plik do otwarcia w MS Excel)")
    except PermissionError:
        print(f"[!] Info: Plik XLSX jest otwarty w Excelu ({sciezka_xlsx}) – pomijam nadpisywanie.")
    print(f"[+] Zapisano JSON : {sciezka_json}")
    return sciezka_csv, sciezka_xlsx, sciezka_json


def generuj_raport_tekstowy(stats: Dict[str, Any], folder: str = FOLDER_WYNIKOW) -> str:
    """Tworzy raport kontroli jakości danych i zapisuje go do pliku."""
    tekst = f"""============================================================
             RAPORT KONTROLI JAKOŚCI DANYCH
============================================================
Liczba pobranych rekordów ogółem : {stats['pobrane_ogolem']}
Liczba unikalnych rekordów        : {stats['unikalne_rekordy']}
Liczba odrzuconych duplikatów     : {stats['odrzucone_duplikaty']}
------------------------------------------------------------
Braki w polu 'ocena'              : {stats['braki_oceny']} ({stats['braki_oceny_procent']}%)
Braki w polu 'gwarancja'          : {stats['braki_gwarancji']} ({stats['braki_gwarancji_procent']}%)
------------------------------------------------------------
Rozkład walut:
  - PLN: {stats['waluty']['PLN']} ofert
  - EUR: {stats['waluty']['EUR']} ofert
  - USD: {stats['waluty']['USD']} ofert
------------------------------------------------------------
Statystyki cenowe (w PLN):
  - Minimalna cena : {stats['cena_min_pln']} zł
  - Maksymalna cena: {stats['cena_max_pln']} zł
  - Średnia cena   : {stats['cena_srednia_pln']} zł
  - Mediana cen    : {stats['cena_mediana_pln']} zł
  - Średnia ocen   : {stats['ocena_srednia']} / 5.0
============================================================
"""
    sciezka_raportu = os.path.join(folder, "raport_jakosci.txt")
    with open(sciezka_raportu, "w", encoding="utf-8") as f:
        f.write(tekst)
    return tekst


def main():
    parser_cli = argparse.ArgumentParser(description="Parser serwisu TechStore (Parser2)")
    parser_cli.add_argument("--url", default=DOMYSLNY_URL, help="URL źródła danych JSON")
    parser_cli.add_argument("--output-dir", default=FOLDER_WYNIKOW, help="Folder na pliki wyjściowe")
    args = parser_cli.parse_args()

    print("=== START PARSERA TECHSTORE (Parser2) ===")
    surowe = pobierz_surowe_dane(url=args.url)
    oczyszczone, statystyki = filtruj_i_deduplikuj(surowe)

    zapisz_wyniki(oczyszczone, folder=args.output_dir)
    raport = generuj_raport_tekstowy(statystyki, folder=args.output_dir)
    print("\n" + raport)
    print("=== PARSER ZAKOŃCZYŁ DZIAŁANIE POMYŚLNIE ===")


if __name__ == "__main__":
    main()
