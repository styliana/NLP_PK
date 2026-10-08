"""Rozszerzenie 5.0: wykrycie i wykorzystanie źródła danych strony (plik JSON).
"""
import argparse
import json
import time
import tracemalloc
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from czyszczenie import wyczysc_rekord

KATALOG = Path(__file__).resolve().parent
POROWNYWANE = ["nazwa", "kategoria", "producent", "cena", "waluta", "dostepnosc", "stan", "ocena", "liczba_opinii",
               "gwarancja", "darmowa_dostawa", "sku", "ean", "kolor", "waga_kg", "wymiary", "material",
               "kraj_pochodzenia", "zasilanie", "certyfikaty", "zawartosc_zestawu", "specyfikacja_ukryta", "opis"]


def rekord_z_json(p):
    """Rekord z pliku JSON w tym samym kształcie co surowy rekord ze strony."""
    surowy = dict(p)
    surowy["sku"] = p.get("kod_produktu")
    # opis w JSON zawiera znaczniki i encje HTML – przeglądarka pokazuje go jako czysty tekst
    surowy["opis"] = BeautifulSoup(p.get("opis") or "", "html.parser").get_text()
    return surowy


def main():
    argumenty = argparse.ArgumentParser(description="Pobranie danych bezpośrednio z pliku JSON serwisu")
    argumenty.add_argument("--url", default="http://localhost:8000")
    argumenty.add_argument("--wyniki", default=str(KATALOG / "wyniki"))
    arg = argumenty.parse_args()
    wyniki = Path(arg.wyniki)

    tracemalloc.start()
    start = time.perf_counter()
    odpowiedz = requests.get(arg.url.rstrip("/") + "/data/products.json", timeout=30)
    odpowiedz.raise_for_status()
    rekordy = odpowiedz.json()
    dzis = date.today()
    unikalne = {}
    for p in rekordy:
        unikalne.setdefault(p["id"], p)
    czyste = [wyczysc_rekord(rekord_z_json(p), dzis) for p in unikalne.values()]
    czas_json = time.perf_counter() - start
    _, pamiec_szczyt = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    json_df = pd.DataFrame(czyste).set_index("id")
    wynik = {
        "rekordy_w_pliku": len(rekordy),
        "rekordy_unikalne": len(unikalne),
        "rozmiar_pliku_kb": round(len(odpowiedz.content) / 1024, 1),
        "czas_json_s": round(czas_json, 2),
        "pamiec_szczyt_python_mb": round(pamiec_szczyt / 2**20, 1),
    }

    plik_selenium = wyniki / "produkty.csv"
    if plik_selenium.exists():
        selenium_df = pd.read_csv(plik_selenium, encoding="utf-8-sig", dtype={"ean": str, "sku": str}).set_index("id")
        wspolne = json_df.index.intersection(selenium_df.index)
        rozbieznosci = {}
        for kolumna in POROWNYWANE:
            a = json_df.loc[wspolne, kolumna]
            b = selenium_df.loc[wspolne, kolumna]
            rozne = ~((a == b) | (a.isna() & b.isna()))
            if rozne.any():
                przyklad = rozne[rozne].index[0]
                rozbieznosci[kolumna] = {"liczba": int(rozne.sum()), "przyklad_id": int(przyklad),
                                         "json": str(a[przyklad]), "selenium": str(b[przyklad])}
        wynik["porownanie_z_selenium"] = {"wspolne_id": len(wspolne), "kolumny": len(POROWNYWANE),
                                          "rozbieznosci": rozbieznosci}
        podsumowanie = wyniki / "podsumowanie.json"
        if podsumowanie.exists():
            czas_selenium = json.loads(podsumowanie.read_text(encoding="utf-8"))["czas_s"]
            wynik["czas_selenium_s"] = czas_selenium
            wynik["przyspieszenie_x"] = round(czas_selenium / czas_json)

    (wyniki / "porownanie_json.json").write_text(json.dumps(wynik, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(wynik, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
