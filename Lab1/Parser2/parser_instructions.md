# Laboratorium NLP – Parser serwisu TechStore (Parser2)
> **Rola: PARSER | Ocena docelowa: 5.0**

---

## 1. Szybki start (1 polecenie)

Wszystkie etapy (pobranie danych, 4 testy jednostkowe, statystyki opisowe, 3 wykresy PNG i badanie HTML vs DOM) uruchamia się jednym poleceniem:

```powershell
python Lab1/Parser2/uruchom_calosc.py
```

---

## 2. Architektura projektu

```text
Lab1/Parser2/
├── strona/                     # Izolowany serwis partnera (SPA: dane pobierane przez JS z JSON)
│   ├── index.html, styles.css
│   ├── katalog.js, wspolne.js, produkt.js
│   └── dane/produkty.json
│
├── parser.py                   # Silnik parsera (API Network Sniffing, czyszczenie, eksport)
├── test_parser.py              # 4 testy jednostkowe (waluty, braki, deduplikacja, typy)
├── analiza.py                  # Statystyki opisowe (Q1, Q3, IQR, outliery) i generator wykresów
├── porownanie_html_vs_dom.py   # Weryfikacja wymogu 5.0 (surowy HTML vs DOM)
├── uruchom_calosc.py           # Master skrypt sekwencyjny
├── README.md                   # Niniejsza dokumentacja dla prowadzącego
│
├── wyniki/                     # Wygenerowane zbiory danych:
│   ├── produkty_oczyszczone.xlsx # Arkusz Excel (rodzimy format .xlsx – bez problemów z separatorem)
│   ├── produkty_oczyszczone.csv  # Plik CSV (utf-8-sig, kolumny ułożone 1:1 z tabelą na stronie)
│   ├── produkty_oczyszczone.json # Baza w formacie JSON
│   ├── raport_jakosci.txt        # Podsumowanie braków i walut
│   └── porownanie_html_vs_dom.txt# Raport pomiarowy HTML vs DOM
│
└── wykresy/                    # Wykresy wysokiej rozdzielczości (PNG):
    ├── 1_histogram_cen.png       # Rozkład cen w PLN ze średnią i medianą
    ├── 2_boxplot_cen.png         # Wykres pudełkowy cen wg kategorii z outlierami
    └── 3_korelacja_cena_waga.png # Korelacja waga vs cena z linią trendu liniowego
```

---

## 3. Spełnienie kryteriów regulaminu na ocenę 5.0

| Wymóg z regulaminu (Lab1.pdf) | Realizacja w kodzie | Wynik w projekcie |
|---|---|---|
| **Liczba rekordów** (min. 200) | Pobranie i deduplikacja bazy | **420 unikalnych rekordów** (sortowane rosnąco wg ID 1001–1420) |
| **Liczba atrybutów** (min. 18) | Spłaszczenie pól z listy i podstron | **30 atrybutów** (kolumny w kolejności 1:1 jak na stronie) |
| **Normalizacja cen** | Regex w `parsuj_cene` | Przeliczenie cen z EUR/USD na PLN po stałym kursie |
| **Bezpieczne braki danych** | Wartości `None` bez wyjątków | Ocena: **18.33%**, Gwarancja: **17.38%** (wymóg: >15%) |
| **Deduplikacja** | Filtracja po unikalnym `id` | Wykryto i odrzucono dokładnie **12 duplikatów** |
| **Formaty wyjściowe** (Rozszerzenie 4.0) | Eksport do wielu formatów | **XLSX (Excel)** + **CSV (utf-8-sig)** + **JSON** |
| **Testy jednostkowe** (Rozszerzenie 4.0) | `unittest` w `test_parser.py` | **4 testy jednostkowe – 100% OK** |
| **Statystyki i wykresy** (Wymóg 4.0/5.0) | `analiza.py` (matplotlib/pandas) | **Histogram, Box-plot, Wykres korelacji** (w `wykresy/`) |
| **Wymóg poziomu 5.0 (HTML vs DOM)** | `porownanie_html_vs_dom.py` | Surowy HTML: **0 rekordów**, Drzewo DOM: **432 rekordy** |
| **Rozszerzenie poziomu 5.0** | Wykrycie asynchronicznego źródła JSON | Czas pobrania: **< 30 ms** (zamiast powolnego Selenium) |

---

## 4. Twarde dane do sprawozdania

### A. Kontrola jakości danych
- Pobrane rekordy: **432** | Unikalne rekordy: **420** | Odrzucone duplikaty: **12**
- Braki w polu `ocena`: **77 szt. (18.33%)**
- Braki w polu `gwarancja`: **73 szt. (17.38%)**
- Rozkład walut: **PLN: 379**, **EUR: 19**, **USD: 22**

### B. Statystyki opisowe cen (PLN)
- Średnia: **1 993.86 zł** | Mediana: **1 504.99 zł** | Moda: **639.99 zł**
- Kwartyle: **Q1 = 739.99 zł**, **Q3 = 2 537.49 zł** | Rozstęp **IQR = 1 797.50 zł**
- Wartości odstające (ceny powyżej 5 233.74 zł): **28 urządzeń** *(flagowe laptopy/smartfony – poprawny segment premium, a nie błąd)*.

### C. Zestawienie: Surowy HTML vs Drzewo DOM (Wymóg 5.0)
| Parametr | Surowy HTML (requests / Ctrl+U) | Drzewo DOM (po wykonaniu JS) |
|---|---|---|
| **Czas odpowiedzi** | ~60 ms | ~25 ms |
| **Rozmiar danych** | 4.7 KB | 493 KB |
| **Liczba produktów** | **0 (0.0%)** | **432 (100.0%)** |
| **Wniosek** | Tradycyjny scraper bez JS nie widzi żadnych produktów. Dane są wstrzykiwane dynamicznie z pliku `dane/produkty.json`. Bezpośrednie użycie endpointu pozwala na błyskawiczne pozyskanie danych. |

---

## 5. Gotowe odpowiedzi na obronę

1. **Dlaczego requests/BeautifulSoup zwrócił 0 produktów na stronie głównej?**  
   Serwis partnera to aplikacja SPA – w surowym kodzie HTML (Ctrl+U) są wyłącznie puste kontenery (`<tbody id="wiersze-produktow">`), a rekordy wstrzykuje asynchronicznie `katalog.js`.
2. **Dlaczego inżynieria wsteczna (Network Sniffing) zamiast Selenium?**  
   Zgodnie z oficjalną listą rozszerzeń na ocenę 5.0 w regulaminie: *„Wykrycie i wykorzystanie źródła danych, z którego korzysta strona (plik JSON), wraz z omówieniem, dlaczego jest to szybsze”*. Pobranie trwa poniżej 30 ms zamiast kilkunastu sekund klikania w przeglądarce.
3. **Jak zapewniono spójność danych?**  
   - Rekordy posortowano po `id` rosnąco (1001–1420),
   - Kolumny ułożono dokładnie w kolejności tabeli na stronie (`SKU -> Nazwa -> Cena -> Dostępność -> Ocena -> Opinie -> Data -> Gwarancja -> Kolor -> Waga`),
   - Daty sformatowano w formacie `DD.MM.YYYY`, a wagi w kg.
