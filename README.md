# NLP_PK – Przetwarzanie Języka Naturalnego (Politechnika Krakowska)

Repozytorium projektów laboratoryjnych z przedmiotu **Przetwarzanie Języka Naturalnego (NLP)**.

---

## Repo list

- **Lab1** – **Pozyskiwanie i parsowanie danych webowych (Web Scraping & Data Cleaning)**
  - **Parser1:** Serwis demonstracyjny TechStore w architekturze SPA (rola AUTOR) oraz scraper oparty o Selenium 4.50, requests/BeautifulSoup, pandas, matplotlib i pytest (rola PARSER).
  - **Parser2:** Silnik parsera dla serwisu partnera na ocenę 5.0 (inżynieria wsteczna endpointu JSON, normalizacja pandas/openpyxl, wykresy matplotlib, testy unittest).
- **Lab2** – `[tbd]`

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
└── README.md             # Główna dokumentacja repozytorium
```

---

## Szybkie uruchomienie

### Moduł Parser2 (Rola PARSER – Ocena 5.0):
```powershell
python Lab1/Parser2/uruchom_calosc.py
```

### Moduł Parser1 (Serwis + Parser Selenium):
```powershell
python Lab1/Parser1/server.py
python Lab1/Parser1/parser/scraper.py --headless
```

Pełna dokumentacja: [Lab1/Parser1/README.md](file:///C:/Users/DELL/Documents/nlp/Lab1/Parser1/README.md) oraz [Lab1/Parser2/README.md](file:///C:/Users/DELL/Documents/nlp/Lab1/Parser2/README.md).