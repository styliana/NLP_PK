# NLP_PK – Przetwarzanie Języka Naturalnego (Politechnika Krakowska)

Repozytorium projektów laboratoryjnych z przedmiotu **Przetwarzanie Języka Naturalnego (NLP)**.

---

## Repo list

- **Lab1** – **Pozyskiwanie i parsowanie danych webowych (Web Scraping & Data Cleaning)**
  - **Parser1 (Rola: AUTOR):** Serwis demonstracyjny e-commerce TechStore przygotowany pod parsowanie (architektura SPA, dane wstrzykiwane asynchronicznie z JSON, paginacja, opóźnienia sieciowe oraz celowe utrudnienia w danych).
  - **Parser2 (Rola: PARSER):** Kompletny silnik parsera dla serwisu partnera realizujący poziom oceny 5.0 (inżynieria wsteczna endpointu JSON, normalizacja cen i walut, obsługa braków, deduplikacja, testy jednostkowe, analiza statystyczna z wykresami oraz badanie surowy HTML vs DOM).
- **Lab2** – `[tbd]`

---

## Struktura repozytorium

```text
.
├── Lab1/
│   ├── Lab1.pdf          # Wymagania i instrukcja do laboratorium
│   ├── Parser1/          # Implementacja serwisu (rola AUTOR – Poziom 5.0)
│   └── Parser2/          # Silnik parsera i analiza (rola PARSER – Poziom 5.0)
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

### Lab 1 – Parser i analiza (rola PARSER):
```powershell
python Lab1/Parser2/uruchom_calosc.py
```
Pełna dokumentacja modułu znajduje się w pliku `Lab1/Parser2/README.md`.