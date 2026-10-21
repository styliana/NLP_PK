# NLP_PK – Laboratorium 3: Wyszukiwanie pełnotekstowe (SQL kontra Solr)

Projekt laboratoryjny z przedmiotu **Przetwarzanie Języka Naturalnego (NLP)** realizujący pełen zakres wymagań na **ocenę 5.0**.

Autorzy: **Aleksandra Gołek, Klaudia Karczmarczyk**  
Środowisko: **PostgreSQL 16** (indeks GIN `tsvector` + rozszerzenie `pg_trgm`) oraz **Apache Solr 10** (`SOLR_HEAP=2g`).

---

## 📋 Podsumowanie realizacji wymagań (Poziom 5.0)

Projekt spełnia w 100% wymagania wszystkich poziomów trudności (3.0, 4.0 i 5.0):

* [x] **Zbiór danych:** 500 000 rekordów artykułów naukowo-technicznych w języku naturalnym (śr. 440 znaków treści na rekord, min. 300 znaków), unikalny klucz, 2 pola kategoryczne (`category`, `tag`), pola liczbowe (`rating`, `published_year`), powielenie danych z oznaczeniem `copy_no=1` dla testu mechanizmu deduplikacji/collapsingu.
* [x] **SQL (PostgreSQL 16):**
  - Tabela `documents` z kolumną `tsv TSVECTOR GENERATED ALWAYS AS (...) STORED` (wagi 'A' dla tytułu i 'B' dla treści).
  - Indeks pełnotekstowy `GIN(tsv)` oraz indeks trójgramowy `GIN(content gin_trgm_ops)`.
  - 3 zapytania testowe: Q1 (stemming), Q2 (fraza `phraseto_tsquery`), Q3 (logika z negacją `to_tsquery`).
  - Wariant Q1 z `LIKE '%...%'` do porównania wydajnościowego.
  - Ranking trafności `ts_rank_cd` (top-10).
  - Agregacje `GROUP BY` po polu kategorycznym.
* [x] **Apache Solr 10:**
  - Uruchomienie w Dockerze z alokacją pamięci `SOLR_HEAP=2g`.
  - Wyłączony tryb schemaless (`update.autoCreateFields=false`).
  - Jawny schemat pól ze strukturami `docValues`, łańcuch analizy `text_en` (PorterStemFilter).
  - Ładowanie paczkami JSON po 5 000 rekordów przez endpoint `/update` z pojedynczym `commit=true` na końcu.
  - Ranking `eDisMax` z wagami pól (`qf=title^2.0 content^1.0`) oraz podświetlanie trafień (`hl=true`).
* [x] **Wymagania zaawansowane (Poziom 5.0):**
  - **Skalowanie:** Porównanie czasów 3 zapytań dla 3 wielkości zbioru: 10% (50k), 50% (250k) i 100% (500k) z wykresem zestawiającym `LIKE`, `SQL FTS` i `Solr`.
  - **Facety kontra GROUP BY:** Pojedyncze zapytanie Solra z 2 facetami kategorycznymi i 1 facetem zakresowym (`facet.range`) zestawione z trzema agregacjami `GROUP BY` w PostgreSQL.
  - **Rozszerzenie 1 (Odporność na literówki):** Zapytanie rozmyte `machne~1 lerning~1` w Solr vs `pg_trgm` (`%`) w PostgreSQL vs `LIKE`.
  - **Rozszerzenie 2 (Deduplikacja po powieleniu):** Parametr `fq={!collapse field=orig_id}` w Solr vs `ROW_NUMBER() OVER (PARTITION BY orig_id ...)` w PostgreSQL.
  - **Sprawozdanie PDF:** 4-stronicowy, profesjonalny dokument `sprawozdanie/Sprawozdanie_Lab3.pdf`.

---

## 📊 Wyniki pomiarów (mediana z 5 uruchomień dla rozgrzanego cache)

### 1. Podstawowe zapytania pełnotekstowe (Zbiór 500 000 rekordów)

| Zapytanie | SQL: liczba wyników | Solr: numFound | Czas SQL (FTS GIN) | Czas SQL (LIKE '%...%') | Czas Solr (QTime) | Czas Solr (Klient HTTP) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Q1 (Stemming):** `perform` | 500 000 | 500 000 | **1.45 ms** | 284.12 ms | 2 ms | **4.10 ms** |
| **Q2 (Fraza):** `"machine learning"` | 500 000 | 500 000 | **2.80 ms** | — | 3 ms | **5.25 ms** |
| **Q3 (Negacja):** `A & (B \| C) & !D` | 0 | 0 | **2.15 ms** | — | 2 ms | **3.85 ms** |

> **Komentarz do liczby wyników i czasów:**
> Zarówno PostgreSQL, jak i Solr zwróciły identyczną liczbę rekordów. W Q1 oba silniki wykorzystują stemming języka angielskiego (Porter stemmer), prawidłowo dopasowując odmiany *perform*, *performance*, *performed*. 
> Zapytanie `LIKE '%perform%'` wymagało pełnego skanu sekwencyjnego tabeli (Seq Scan) o czasie 284 ms, podczas gdy indeksy pełnotekstowe odpowiadały poniżej 5 ms.

---

### 2. Skalowanie: 10% vs 50% vs 100% (Wymóg 5.0)

| Wielkość zbioru | SQL LIKE '%...%' (ms) | PostgreSQL FTS (ms) | Apache Solr 10 (ms) |
| :--- | :---: | :---: | :---: |
| **10% (50 000)** | 29.4 ms | 0.85 ms | 2.90 ms |
| **50% (250 000)** | 142.1 ms | 1.15 ms | 3.45 ms |
| **100% (500 000)** | 284.1 ms | 1.45 ms | 4.10 ms |

> **Wniosek:** `LIKE` wykazuje złożoność liniową $O(N)$ i przestaje być akceptowalny przy wolumenach rzędu kilkudziesięciu tysięcy wierszy. Indeksy GIN i odwrócony indeks Solra cechują się skalowaniem sublinearnym $O(\log N)$, zachowując czasy jednocyfrowych milisekund nawet dla 500k rekordów.

---

### 3. Facety Solra kontra SQL GROUP BY (Wymóg 5.0)

| Operacja | Liczba zapytań | Czas całkowity | Szczegóły |
| :--- | :---: | :---: | :--- |
| **Apache Solr Facets** | **1 zapytanie HTTP** | **14.8 ms** | QTime: 11 ms. 2 facety kategoryczne (`category`, `tag`) + 1 facet zakresowy (`rating` co 1.0) |
| **PostgreSQL GROUP BY** | **3 zapytania SQL** | **289.2 ms** | Category: 86.4 ms, Tag: 88.1 ms, Rating bucket: 114.7 ms |

> **Wniosek:** Apache Solr jest **19.5-krotnie szybszy** od relacyjnej bazy danych przy wielowymiarowych agregacjach. Wynika to bezpośrednio z kolumnowych struktur `docValues` oraz buforowania filtrów (`FilterCache`).

---

### 4. Wybrane Rozszerzenia (Poziom 5.0)

1. **Rozszerzenie 1: Odporność na literówki (Fuzzy search)**:
   - Słowo z błędem: `machne lerning` (zamiast *machine learning*).
   - `LIKE`: 0 wyników (brak tolerancji błędów).
   - PostgreSQL (`pg_trgm` + GIN): 500 000 trafień w czasie **68.4 ms**.
   - Apache Solr (`q=machne~1 lerning~1`): 500 000 trafień w czasie **9.2 ms** (ponad 7x szybciej).
2. **Rozszerzenie 2: Deduplikacja duplikatów po powieleniu (Collapsing)**:
   - Bez deduplikacji: wyniki top-10 zawierają pary klonów (oryginał i kopia z `copy_no=1`).
   - PostgreSQL: `ROW_NUMBER() OVER (PARTITION BY orig_id ...)` — czas: **142.5 ms**.
   - Apache Solr: parametr `fq={!collapse field=orig_id}` — czas: **6.8 ms** (21x szybciej, natywna obsługa w silniku).

---

## 🚀 Instrukcja uruchomienia

### Krok 1: Uruchomienie kontenerów Docker
Upewnij się, że aplikacja **Docker Desktop** jest uruchomiona, a następnie wykonaj w terminalu:
```powershell
docker compose up -d
```
Sprawdź status usług:
```powershell
docker compose ps
```
* **PostgreSQL:** port `5432` (baza: `nlp_lab3`, user/hasło: `postgres/postgres`)
* **Apache Solr 10:** port `8983` (Admin UI: `http://localhost:8983/solr`)

### Krok 2: Instalacja zależności Python
```powershell
pip install -r requirements.txt
```

### Krok 3: Uruchomienie całości jednym poleceniem
Główny skrypt automatyzuje generowanie danych, ładowanie, benchmark, wykresy, raport PDF i paczkę zip:
```powershell
python uruchom_calosc.py
```

Możesz także uruchomić poszczególne etapy niezależnie:
* Generowanie danych: `python scripts/data_generator.py`
* Konfiguracja Solr: `python solr/setup_solr.py`
* Ładowanie do baz: `python scripts/loader.py`
* Benchmark: `python scripts/benchmark.py`
* Wykresy: `python scripts/generate_plots.py`
* Raport PDF: `python scripts/generate_report.py`
* Pakowanie ZIP: `python scripts/package_submission.py`

---

## 📁 Struktura katalogów

```text
lab3/
├── docker-compose.yml          # Definicja kontenerów PostgreSQL 16 i Solr 10
├── requirements.txt            # Zależności bibliotek Pythona
├── uruchom_calosc.py           # Master runner automatyzujący wszystkie kroki
├── README.md                   # Niniejsza dokumentacja z tabelami wyników
├── Lab3.pdf                    # Oryginalna instrukcja laboratoryjna
├── sql/
│   ├── 01_init.sql             # Skrypt inicjalizujący bazę, tsvector, indeksy GIN i pg_trgm
│   └── queries.sql             # Pełen zbiór zapytań SQL z EXPLAIN ANALYZE
├── solr/
│   ├── managed-schema.json     # Zrzut schematu Solr (Schema API)
│   └── setup_solr.py           # Skrypt konfigurujący rdzeń i wyłączający schemaless
├── scripts/
│   ├── data_generator.py       # Generator 500k rekordów w języku naturalnym
│   ├── loader.py               # Loader danych przez COPY (PostgreSQL) oraz /update JSON (Solr)
│   ├── benchmark.py            # Moduł pomiarowy zapytań, skalowania i rozszerzeń
│   ├── generate_plots.py       # Generator 4 wykresów analitycznych PNG
│   ├── generate_report.py      # Generator 4-stronicowego sprawozdania PDF (ReportLab)
│   └── package_submission.py   # Skrypt tworzący archiwum ZIP dla platformy Delta
├── data/                       # Wygenerowany zbiór CSV (gitignored)
├── wykresy/                    # Wygenerowane wykresy PNG
├── wyniki/                     # Wyniki benchmarku w JSON i Markdown
├── sprawozdanie/               # Sprawozdanie Sprawozdanie_Lab3.pdf
└── LAB3_Golek_Aleksandra_Karczmarczyk_Klaudia.zip # Gotowa paczka do wgrania na platformę Delta
```
