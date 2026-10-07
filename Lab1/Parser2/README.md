# Laboratorium NLP – Moduł Parser2 (Rola: PARSER)
> **Ocena docelowa: 5.0 | Projekt: Parser serwisu TechStore partnera**

---

## 1. O projekcie

Katalog `Lab1/Parser2` zawiera kompletne środowisko roli **PARSER** przygotowane w ramach Laboratorium 1 z Przetwarzania Języka Naturalnego. 

Zadaniem parsera było pozyskanie, oczyszczenie, analiza oraz walidacja danych z serwisu e-commerce **TechStore** przygotowanego przez partnera w architekturze SPA (Single Page Application, Poziom 5.0).

---

## 2. Szybki start

Cały proces (ekstrakcja danych, 4 testy jednostkowe, analiza statystyczna, generowanie 3 wykresów oraz badanie surowy HTML vs DOM) uruchamia się jednym poleceniem:

```powershell
python Lab1/Parser2/uruchom_calosc.py
```

Można również uruchamiać poszczególne moduły niezależnie:
```powershell
python Lab1/Parser2/parser.py                # Pobranie danych i eksport do XLSX, CSV, JSON
python Lab1/Parser2/test_parser.py           # Zestaw 4 testów jednostkowych (unittest)
python Lab1/Parser2/analiza.py               # Statystyki opisowe, outliery i wykresy PNG
python Lab1/Parser2/porownanie_html_vs_dom.py# Pomiary i weryfikacja wymogu 5.0 (HTML vs DOM)
```

---

## 3. Architektura plików projektu

```text
Lab1/Parser2/
├── strona/                     # Izolowany serwis partnera (HTML, CSS, JS, JSON)
│   ├── index.html, styles.css
│   ├── katalog.js, wspolne.js, produkt.js
│   ├── README_SERWISU.md
│   └── dane/produkty.json
│
├── parser.py                   # Główny silnik parsera (Network Sniffing, czyszczenie, eksport)
├── test_parser.py              # Zestaw 4 testów jednostkowych funkcji normalizujących
├── analiza.py                  # Analiza statystyczna (Q1, Q3, IQR, outliery) i generator wykresów
├── porownanie_html_vs_dom.py   # Pomiar surowy HTML vs DOM z wnioskiem na ocenę 5.0
├── uruchom_calosc.py           # Master skrypt automatyzujący cały proces
├── README.md                   # Niniejsza dokumentacja modułu
├── parser_instructions.md      # Szczegółowy opis deweloperski i analiza wyzwań
│
├── wyniki/                     # Oczyszczone zbiory danych:
│   ├── produkty_oczyszczone.xlsx # Rodzimy skoroszyt Excela (brak problemów z separatorem)
│   ├── produkty_oczyszczone.csv  # Plik CSV (utf-8-sig, układ kolumn 1:1 z tabelą na stronie)
│   ├── produkty_oczyszczone.json # Baza w formacie JSON
│   ├── raport_jakosci.txt        # Zestawienie kontroli jakości danych
│   └── porownanie_html_vs_dom.txt# Raport różnic surowy HTML vs DOM
│
└── wykresy/                    # Wygenerowane wykresy (PNG):
    ├── 1_histogram_cen.png       # Rozkład cen w PLN ze średnią i medianą
    ├── 2_boxplot_cen.png         # Wykres pudełkowy cen wg kategorii z outlierami
    └── 3_korelacja_cena_waga.png # Wykres rozrzutu waga vs cena z linią regresji
```

---

## 4. Tabela zgodności z wymaganiami na ocenę 5.0

| Wymóg z regulaminu (Lab1.pdf) | Realizacja w module | Wynik w danych |
|---|---|---|
| **Liczba rekordów** (min. 200) | Pobranie i deduplikacja bazy | **420 unikalnych rekordów** (posortowanych rosnąco wg ID 1001–1420) |
| **Liczba atrybutów** (min. 18) | Spłaszczenie pól z listy i podstron | **30 atrybutów** (układ 1:1 z widokiem tabeli na stronie) |
| **Normalizacja cen** | Wyrażenia regularne w `parsuj_cene` | Przeliczenie cen z EUR/USD na PLN po stałym kursie |
| **Bezpieczne braki danych** | Domyślne wartości `None` bez wyjątków | Ocena: **18.33%**, Gwarancja: **17.38%** (wymóg: >15%) |
| **Deduplikacja** | Odrzucenie rekordów po unikalnym `id` | Wykryto i odrzucono dokładnie **12 duplikatów** |
| **Formaty wyjściowe** (Rozszerzenie 4.0) | Jednoczesny eksport do 3 formatów | **XLSX (Excel)** + **CSV (utf-8-sig)** + **JSON** |
| **Testy jednostkowe** (Rozszerzenie 4.0) | `unittest` w `test_parser.py` | **4 testy jednostkowe – 100% zaliczone** |
| **Wykresy i statystyki** (Wymóg 4.0/5.0) | `analiza.py` (matplotlib/pandas) | **Histogram, Box-plot, Wykres korelacji** (w `wykresy/`) |
| **Wymóg poziomu 5.0 (HTML vs DOM)** | `porownanie_html_vs_dom.py` | Surowy HTML: **0 rekordów**, Drzewo DOM: **432 rekordy** |
| **Rozszerzenie poziomu 5.0** | Wykrycie asynchronicznego źródła JSON | Czas pobrania: **< 30 ms** (zamiast powolnego Selenium) |

---

## 5. Podsumowanie kontroli jakości i statystyk

### A. Kontrola jakości danych
- Pobrane ogółem: **432** | Unikalne rekordy: **420** | Odrzucone duplikaty: **12**
- Braki w polu `ocena`: **77 szt. (18.33%)**
- Braki w polu `gwarancja`: **73 szt. (17.38%)**
- Rozkład walut w ofertach: **PLN: 379**, **EUR: 19**, **USD: 22**

### B. Statystyki cenowe (w PLN)
- Średnia arytmetyczna: **1 993.86 zł** | Mediana (Q2): **1 504.99 zł** | Moda: **639.99 zł**
- Kwartyle: **Q1 = 739.99 zł**, **Q3 = 2 537.49 zł** | Rozstęp międzykwartylowy **IQR = 1 797.50 zł**
- Wartości odstające (ceny powyżej 5 233.74 zł): **28 urządzeń** *(flagowe laptopy/smartfony – prawidłowa cecha rynku premium, a nie błąd)*.

### C. Porównanie surowy HTML vs DOM (Wymóg 5.0)
| Parametr | Surowy HTML (requests / Ctrl+U) | Drzewo DOM (po wykonaniu JS) |
|---|---|---|
| **Czas pobrania** | ~60 ms | ~25 ms |
| **Rozmiar danych** | 4.7 KB | 493 KB |
| **Liczba produktów** | **0 (0.0%)** | **432 (100.0%)** |
| **Wniosek** | Tradycyjny scraper bez silnika JS nie widzi żadnych produktów (puste kontenery w kodzie źródłowym). Cała treść powstaje asynchronicznie przez JavaScript. |

---

## 6. Pytania i odpowiedzi na obronę projektu

1. **Dlaczego zwykły parser HTML (BeautifulSoup) zwrócił 0 produktów na stronie głównej?**  
   Serwis partnera to aplikacja SPA – w surowym kodzie HTML (`Ctrl+U`) znajdują się wyłącznie puste szkielety (`<tbody id="wiersze-produktow">`), a rekordy wstrzykuje asynchronicznie skrypt `katalog.js`.
2. **Dlaczego inżynieria wsteczna (Network Sniffing) zamiast Selenium?**  
   Jest to oficjalne rozszerzenie na poziom 5.0 w regulaminie: *„Wykrycie i wykorzystanie źródła danych, z którego korzysta strona (plik JSON), wraz z omówieniem, dlaczego jest to szybsze”*. Pobranie danych bezpośrednio z endpointu trwa poniżej 30 ms zamiast kilkunastu sekund klikania w przeglądarce.
3. **Jak zapewniono spójność i czytelność danych?**  
   - Posortowano rekordy rosnąco wg `id` (1001–1420),
   - Ułożono kolumny dokładnie w kolejności tabeli na stronie (`SKU -> Nazwa -> Cena -> Dostępność -> Ocena -> Opinie -> Data -> Gwarancja -> Kolor -> Waga`),
   - Ujednolicono format dat do `DD.MM.YYYY` i wag do kg,
   - Wygenerowano plik `.xlsx`, który otwiera się w polskim Excelu bez jakichkolwiek problemów ze średnikami.
