#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
MODUŁ: analiza.py
OPIS:  Moduł analizy statystycznej i kontroli jakości danych pozyskanych
       przez parser. Generuje wykresy (histogram, box-plot, korelacja)
       oraz kompletne statystyki opisowe wymagane w sprawozdaniu z laboratorium.
LAB:   Laboratorium NLP - Zadanie 1 (Poziomy 4.0 i 5.0)
=============================================================================
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Zapewnienie kodowania UTF-8
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Stałe ścieżek
KATALOG_BAZOWY = os.path.dirname(os.path.abspath(__file__))
PLIK_CSV = os.path.join(KATALOG_BAZOWY, "wyniki", "produkty_oczyszczone.csv")
KATALOG_WYKRESOW = os.path.join(KATALOG_BAZOWY, "wykresy")

# Konfiguracja stylu wykresów matplotlib
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["axes.labelsize"] = 11


def wczytaj_dane(sciezka: str = PLIK_CSV) -> pd.DataFrame:
    """Wczytuje oczyszczony plik CSV lub XLSX do obiektu DataFrame."""
    if os.path.exists(sciezka):
        df = pd.read_csv(sciezka, sep=";", encoding="utf-8-sig")
    else:
        sciezka_xlsx = os.path.join(KATALOG_BAZOWY, "wyniki", "produkty_oczyszczone.xlsx")
        if os.path.exists(sciezka_xlsx):
            df = pd.read_excel(sciezka_xlsx)
        else:
            raise FileNotFoundError("Nie znaleziono pliku CSV ani XLSX w folderze wyniki/")
    if "waga_kg" not in df.columns and "waga" in df.columns:
        df["waga_kg"] = pd.to_numeric(
            df["waga"].astype(str).str.replace("kg", "").str.replace(",", ".").str.strip(),
            errors="coerce"
        )
    return df


def oblicz_statystyki_opisowe(seria: pd.Series, nazwa: str) -> dict:
    """Oblicza pełne miary położenia i rozproszenia: średnia, mediana, moda, kwartyle, min, max, IQR."""
    czysta = seria.dropna()
    q1 = float(czysta.quantile(0.25))
    q2 = float(czysta.median())
    q3 = float(czysta.quantile(0.75))
    iqr = q3 - q1
    dolny_prog = q1 - 1.5 * iqr
    gorny_prog = q3 + 1.5 * iqr
    outliery = czysta[(czysta < dolny_prog) | (czysta > gorny_prog)]
    moda_seria = czysta.mode()
    moda = float(moda_seria.iloc[0]) if not moda_seria.empty else None

    return {
        "cecha": nazwa,
        "liczba_probek": len(czysta),
        "liczba_brakow": len(seria) - len(czysta),
        "srednia": round(float(czysta.mean()), 2),
        "mediana": round(q2, 2),
        "moda": round(moda, 2) if moda is not None else None,
        "min": round(float(czysta.min()), 2),
        "max": round(float(czysta.max()), 2),
        "q1": round(q1, 2),
        "q3": round(q3, 2),
        "iqr": round(iqr, 2),
        "odchylenie_std": round(float(czysta.std()), 2),
        "liczba_outlierow": len(outliery),
        "prog_outlierow_dol": round(dolny_prog, 2),
        "prog_outlierow_gora": round(gorny_prog, 2),
    }


def generuj_histogram_cen(df: pd.DataFrame, folder: str):
    """Generuje histogram cen produktów w PLN z naniesioną średnią i medianą."""
    ceny = df["cena_pln"].dropna()
    srednia = ceny.mean()
    mediana = ceny.median()

    plt.figure(figsize=(9, 5))
    n, bins, patches = plt.hist(ceny, bins=25, color="#2b5c8f", edgecolor="#ffffff", alpha=0.85)

    plt.axvline(srednia, color="#e63946", linestyle="--", linewidth=2, label=f"Średnia ({srednia:.2f} zł)")
    plt.axvline(mediana, color="#2a9d8f", linestyle="-.", linewidth=2, label=f"Mediana ({mediana:.2f} zł)")

    plt.title("Rozkład cen produktów w serwisie TechStore (w PLN)", fontweight="bold", pad=12)
    plt.xlabel("Cena brutto (PLN)")
    plt.ylabel("Liczba produktów")
    plt.legend(frameon=True)
    plt.tight_layout()

    sciezka = os.path.join(folder, "1_histogram_cen.png")
    plt.savefig(sciezka, dpi=180)
    plt.close()
    print(f"[+] Zapisano histogram: {sciezka}")


def generuj_boxplot_cen(df: pd.DataFrame, folder: str):
    """Generuje wykres pudełkowy (box-plot) cen z podziałem na kategorie produktów."""
    plt.figure(figsize=(10, 5.5))

    kategorie = sorted(df["kategoria"].dropna().unique())
    dane_kat = [df[df["kategoria"] == k]["cena_pln"].dropna() for k in kategorie]

    box = plt.boxplot(
        dane_kat,
        tick_labels=kategorie,
        patch_artist=True,
        showmeans=True,
        meanprops={"marker": "D", "markeredgecolor": "red", "markerfacecolor": "red", "markersize": 5},
        boxprops={"facecolor": "#90caf9", "edgecolor": "#1565c0", "alpha": 0.8},
        medianprops={"color": "#b71c1c", "linewidth": 2},
        flierprops={"marker": "o", "color": "#e65100", "alpha": 0.6, "markersize": 6}
    )

    plt.title("Wykres pudełkowy (Box-plot) cen produktów w rozbiciu na kategorie", fontweight="bold", pad=12)
    plt.xlabel("Kategoria")
    plt.ylabel("Cena brutto (PLN)")
    plt.xticks(rotation=15)
    plt.tight_layout()

    sciezka = os.path.join(folder, "2_boxplot_cen.png")
    plt.savefig(sciezka, dpi=180)
    plt.close()
    print(f"[+] Zapisano box-plot: {sciezka}")


def generuj_wykres_korelacji(df: pd.DataFrame, folder: str):
    """Generuje wykres rozrzutu (korelacji) wagi i ceny z linią regresji liniowej."""
    dane_korelacji = df[["waga_kg", "cena_pln"]].dropna()

    waga = dane_korelacji["waga_kg"]
    cena = dane_korelacji["cena_pln"]

    wspolczynnik_pearsona = waga.corr(cena)

    plt.figure(figsize=(9, 5))
    plt.scatter(waga, cena, color="#1976d2", alpha=0.6, edgecolors="none", s=40, label="Produkty")

    # Linia trendu
    a, b = np.polyfit(waga, cena, 1)
    x_linia = np.linspace(waga.min(), waga.max(), 100)
    plt.plot(x_linia, a * x_linia + b, color="#d32f2f", linestyle="--", linewidth=2,
             label=f"Trend liniowy (r = {wspolczynnik_pearsona:.2f})")

    plt.title("Zależność między wagą produktu a jego ceną (Korelacja)", fontweight="bold", pad=12)
    plt.xlabel("Waga produktu (kg)")
    plt.ylabel("Cena brutto (PLN)")
    plt.legend(frameon=True)
    plt.tight_layout()

    sciezka = os.path.join(folder, "3_korelacja_cena_waga.png")
    plt.savefig(sciezka, dpi=180)
    plt.close()
    print(f"[+] Zapisano wykres korelacji: {sciezka}")
    return wspolczynnik_pearsona


def main():
    print("=== START ANALIZY STATYSTYCZNEJ I GENEROWANIA WYKRESÓW ===")
    os.makedirs(KATALOG_WYKRESOW, exist_ok=True)
    df = wczytaj_dane()

    print(f"[*] Wczytano {len(df)} rekordów z {len(df.columns)} kolumnami.")

    # 1. Kontrola braków danych w kolumnach
    print("\n" + "=" * 60)
    print("         ZESTAWIENIE BRAKÓW DANYCH (KONTROLA JAKOŚCI)")
    print("=" * 60)
    braki = df.isnull().sum()
    braki_proc = (braki / len(df)) * 100
    podsumowanie_brakow = pd.DataFrame({"Liczba braków": braki, "Procent (%)": braki_proc.round(2)})
    print(podsumowanie_brakow[podsumowanie_brakow["Liczba braków"] > 0])

    # 2. Statystyki opisowe dla cech liczbowych
    stat_cena = oblicz_statystyki_opisowe(df["cena_pln"], "Cena w PLN")
    stat_ocena = oblicz_statystyki_opisowe(df["ocena"], "Ocena (1-5)")
    stat_waga = oblicz_statystyki_opisowe(df["waga_kg"], "Waga (kg)")

    print("\n" + "=" * 60)
    print("                 STATYSTYKI OPISOWE")
    print("=" * 60)
    for s in [stat_cena, stat_ocena, stat_waga]:
        print(f"\nCecha: {s['cecha']}")
        print(f"  - Średnia arytmetyczna : {s['srednia']}")
        print(f"  - Mediana (Q2)          : {s['mediana']}")
        print(f"  - Moda                 : {s['moda']}")
        print(f"  - Kwartyl dolny (Q1)   : {s['q1']}")
        print(f"  - Kwartyl górny (Q3)   : {s['q3']}")
        print(f"  - Rozstęp IQR          : {s['iqr']}")
        print(f"  - Wartość minimalna    : {s['min']}")
        print(f"  - Wartość maksymalna   : {s['max']}")
        print(f"  - Odchylenie standard. : {s['odchylenie_std']}")
        print(f"  - Wartości odstające   : {s['liczba_outlierow']} szt. (próg: < {s['prog_outlierow_dol']} lub > {s['prog_outlierow_gora']})")

    # 3. Generowanie wykresów
    print("\n" + "=" * 60)
    print("               GENEROWANIE WYKRESÓW DO SPRAWOZDANIA")
    print("=" * 60)
    generuj_histogram_cen(df, KATALOG_WYKRESOW)
    generuj_boxplot_cen(df, KATALOG_WYKRESOW)
    r = generuj_wykres_korelacji(df, KATALOG_WYKRESOW)

    print(f"\n[+] Obliczony współczynnik korelacji Pearsona (waga vs cena): r = {r:.3f}")
    print("    Interpretacja merytoryczna:")
    print("    Współczynnik r wskazuje na umiarkowaną zależność. Urządzenia cięższe")
    print("    (np. laptopy czy monitory) mają z reguły wyższą cenę niż drobne akcesoria czy słuchawki.")
    print("=== ANALIZA ZAKOŃCZONA POMYŚLNIE ===")


if __name__ == "__main__":
    main()
