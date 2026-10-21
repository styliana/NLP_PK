# NLP_PK – Przetwarzanie Języka Naturalnego (Politechnika Krakowska)

Repozytorium projektów laboratoryjnych z przedmiotu **Przetwarzanie Języka Naturalnego (NLP)**.

---

## Repo list

- **Lab1** – **Pozyskiwanie i parsowanie danych webowych (Web Scraping & Data Cleaning)**
  - **Parser1:** Serwis demonstracyjny TechStore w architekturze SPA (rola AUTOR) oraz scraper oparty o Selenium 4.50, requests/BeautifulSoup, pandas, matplotlib i pytest (rola PARSER).
  - **Parser2:** Silnik parsera dla serwisu partnera na ocenę 5.0 (inżynieria wsteczna endpointu JSON, normalizacja pandas/openpyxl, wykresy matplotlib, testy unittest).
- **Lab2** – **Od tekstu do tokenów: n-gramy, sprowadzanie form, odległość edycyjna i tokenizacja podsłowowa (BPE)** (Poziom 5.0)
  - Analiza n-gramów i rozkładów częstości (prawo Zipfa) w *Panu Tadeuszu*.
  - Porównanie stemmingu i lematyzacji w języku angielskim (*Hamlet*, Porter vs WordNet) oraz w języku polskim (spaCy `pl_core_news_sm` vs Snowball).
  - Pomiary podobieństwa napisów w bibliotece `textdistance` (Levenshtein, Damerau-Levenshtein, Jaro-Winkler, Jaccard).
  - Eliminacja stop words oraz ekstrakcja nazw własnych za pomocą wyrażeń regularnych (RegEx z lookbehind).
  - Trening od zera własnego tokenizatora BPE (*ByteLevel*, 1k/5k/30k), benchmark modeli LLM (`gpt2`, `HerBERT`, `Bielik`) oraz analiza podatku językowego (*language tax*).
  - Wielowymiarowe porównanie czterech metod przetwarzania tekstu (wyrazy, lematyzacja, bez stop words, subwordy BPE).
- **Lab3** – **Wyszukiwanie pełnotekstowe: SQL kontra Solr** (Poziom 5.0)
  - Porównanie funkcjonalne i wydajnościowe na zbiorze **500 000 rekordów** w języku naturalnym.
  - PostgreSQL 16 (indeks GIN `tsvector` z wagami 'A'/'B', ranking `ts_rank_cd`, rozszerzenie `pg_trgm`).
  - Apache Solr 10 (obraz Docker, `SOLR_HEAP=2g`, wyłączony schemaless, model BM25, parser `eDisMax`, facety, highlighting).
  - Wymagania poziomu 5.0: wykres skalowania (10%, 50%, 100% dla LIKE vs FTS vs Solr), pomiar Facety vs GROUP BY (Solr szybszy 19.5x).
  - Zaawansowane rozszerzenia: odporność na literówki (*fuzzy search* ~ vs `pg_trgm`) oraz eliminacja duplikatów (*collapsing* po `orig_id`).
  - Kompletne 4-stronicowe sprawozdanie PDF (`sprawozdanie/Sprawozdanie_Lab3.pdf`) i gotowa paczka oddania `LAB3_Golek_Aleksandra_Karczmarczyk_Klaudia.zip`.

---

## Struktura repozytorium

```text
.
├── Lab1/
│   ├── Lab1.pdf          # Wymagania i instrukcja do laboratorium
│   ├── Parser1/          # Serwis (AUTOR) + Parser Selenium
│   │   ├── server.py     # Serwer z Rate Limiterem (429) i opóźnieniem
│   │   ├── static/       # Frontend SPA (index.html, app.js, styles.css)
│   │   ├── data/         # Baza JSON produktów
│   │   └── parser/       # Parser Selenium (scraper.py, test_czyszczenie.py, analiza.py)
│   └── Parser2/          # Serwis partnera + Silnik Parser2 (5.0)
│       ├── strona/       # Izolowany serwis partnera
│       ├── parser.py     # Główny silnik ekstrakcji i czyszczenia danych
│       ├── test_parser.py# Testy jednostkowe funkcji normalizujących
│       ├── analiza.py    # Statystyki opisowe i generowanie wykresów
│       ├── porownanie_html_vs_dom.py # Weryfikacja wymogu 5.0
│       ├── uruchom_calosc.py # Master skrypt automatyzujący całość
│       ├── wyniki/       # Oczyszczone zbiory (XLSX, CSV, JSON)
│       └── wykresy/      # Wygenerowane wykresy (PNG)
├── Lab2/
│   ├── Lab2.pdf          # Wymagania i instrukcja do laboratorium 2
│   ├── README.md         # Kompleksowa dokumentacja modułu Lab2 (Poziom 5.0)
│   ├── books/            # Korpusy tekstowe ("Pan Tadeusz", "Hamlet")
│   ├── W3_przyklady/     # Przykłady referencyjne z Wykładu 3
│   ├── zad3_a.py do zad5_i.py # Skrypty zadań (3.0, 4.0, 5.0)
│   ├── odpowiedzi*.txt   # Opracowania teoretyczne i interpretacje
│   ├── wyniki*.txt       # Wyniki numeryczne, tabele i macierze
│   ├── tokenizer_pl*.json# Wytrenowane modele BPE (1k, 5k, 30k/14k)
│   └── wykresy/          # Wygenerowane histogramy i wykresy (11 plików PNG)
├── lab3/
│   ├── Lab3.pdf          # Wymagania i instrukcja do laboratorium 3
│   ├── README.md         # Dokumentacja modułu Lab3 (Poziom 5.0)
│   ├── docker-compose.yml# Kontenery PostgreSQL 16 i Solr 10
│   ├── uruchom_calosc.py # Główny skrypt automatyzujący cały potok
│   ├── sql/              # Skrypty SQL (inicjalizacja i zapytania testowe)
│   ├── solr/             # Schemat i konfiguracja Apache Solr 10
│   ├── scripts/          # Generator danych, loader, benchmark, wykresy, raport
│   ├── wykresy/          # 4 wygenerowane wykresy (skalowanie, zapytania, facety, rozszerzenia)
│   ├── sprawozdanie/     # Gotowe sprawozdanie PDF (Sprawozdanie_Lab3.pdf)
│   └── LAB3_Golek_Aleksandra_Karczmarczyk_Klaudia.zip # Archiwum oddania na platformę Delta
└── README.md             # Główna dokumentacja repozytorium
```

---

## Szybkie uruchomienie

### Moduł Lab3 (SQL vs Solr – Ocena 5.0):
```powershell
cd lab3
# Uruchomienie bazy PostgreSQL i silnika Solr 10:
docker compose up -d

# Pełny potok (generowanie 500k rekordów, ładowanie, benchmark, wykresy, PDF, ZIP):
python uruchom_calosc.py
```

### Moduł Lab2 (Od tekstu do tokenów – Ocena 5.0):
```powershell
# Przykładowe uruchomienie analizy n-gramów (Część A) oraz treningu i benchmarku BPE (Część H):
python Lab2/zad3_a.py
python Lab2/zad5_h.py
```

### Moduł Lab1 – Parser2 (Rola PARSER – Ocena 5.0):
```powershell
python Lab1/Parser2/uruchom_calosc.py
```

### Moduł Lab1 – Parser1 (Serwis + Parser Selenium):
```powershell
python Lab1/Parser1/server.py
python Lab1/Parser1/parser/scraper.py --headless
```

Pełna dokumentacja modułów:
- **Lab1**: [Lab1/Parser1/README.md](file:///C:/Users/DELL/Documents/nlp/Lab1/Parser1/README.md) oraz [Lab1/Parser2/README.md](file:///C:/Users/DELL/Documents/nlp/Lab1/Parser2/README.md)
- **Lab2**: [Lab2/README.md](file:///C:/Users/DELL/Documents/nlp/Lab2/README.md)
- **Lab3**: [lab3/README.md](file:///C:/Users/DELL/Documents/nlp/lab3/README.md)