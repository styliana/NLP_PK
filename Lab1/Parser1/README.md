# Laboratorium 1 &ndash; Rola AUTOR (Poziom 5.0)

Projekt serwisu e-commerce **TechStore** przygotowany w ramach laboratorium NLP. Serwis spełnia kompletne wymagania na ocenę **5.0** (oraz dziedziczone wymagania poziomów 3.0 i 4.0) dla roli **AUTOR**.

---

## 1. Jak uruchomić serwis

### Wymagania wstępne
* Python 3.10+ (brak konieczności instalowania zewnętrznych bibliotek dla serwera &ndash; korzysta ze standardowej biblioteki Pythona).

### Uruchomienie serwera
W katalogu `Lab1/Parser1`:
```bash
python server.py
```
Domyślnie serwer uruchamia się pod adresem: **http://localhost:8000/**

Dostępne adresy URL:
* Katalog główny: [http://localhost:8000/](http://localhost:8000/)
* Przykładowa podstrona szczegółów: [http://localhost:8000/detail.html?id=1](http://localhost:8000/detail.html?id=1)
* Endpoint API listy produktów: [http://localhost:8000/api/products?page=1&limit=50](http://localhost:8000/api/products?page=1&limit=50)
* Endpoint API pojedynczego produktu: [http://localhost:8000/api/product?id=1](http://localhost:8000/api/product?id=1)
* Surowy plik JSON z bazą: [http://localhost:8000/data/products.json](http://localhost:8000/data/products.json)

### Uruchomienie testów weryfikacyjnych
```bash
python -u test_author_service.py
```

### (Opcjonalnie) Ponowne wygenerowanie bazy produktów
```bash
python generate_data.py
```

---

## 2. Struktura katalogów i plików

```text
Lab1/Parser1/
├── server.py                 # Dedykowany serwer HTTP (Rate Limiter 429, sztuczne opóźnienie, routing)
├── generate_data.py          # Deterministyczny generator bazy 430 produktów
├── test_author_service.py    # Zautomatyzowane testy weryfikujące wszystkie wymogi oceny 5.0
├── README.md                 # Niniejsza dokumentacja techniczna
├── data/
│   └── products.json         # Wygenerowana baza 430 rekordów (24+ atrybuty, braki danych, duplikaty)
└── static/
    ├── index.html            # Główny szablon katalogu (0 produktów w źródle HTML - wymóg 5.0)
    ├── detail.html           # Szablon podstrony szczegółów produktu
    ├── app.js                # Obsługa fetch(), doładowywania porcjami, paginacji, losowania kolejności
    ├── detail.js             # Obsługa dynamicznych szczegółów, elementu <details> i zakładek
    └── styles.css            # Nowoczesna, czytelna oprawa wizualna
```

---

## 3. Zestawienie spełnionych wymagań (Poziomy 3.0, 4.0, 5.0)

### Poziom 3.0 (Wymagania bazowe)
* [x] **Liczba rekordów:** Wygenerowano **430 rekordów** (wymóg: min. 60).
* [x] **Liczba atrybutów:** Każdy rekord posiada **24 atrybuty** (wymóg: min. 10).
* [x] **Dwie różne struktury:** Rekordy są prezentowane jednocześnie w dwóch strukturach:
  * **Karty:** `<article class="produkt-karta">` w kontenerze `#siatka-kart`.
  * **Tabela:** Wiersze `<tr>` w tabeli `<table class="tabela-produktow">`.
* [x] **Semantyczne selektory:** Nazwy klas i identyfikatorów są semantyczne (`produkt-karta`, `nazwa`, `cena`, `kategoria`, `producent`, `dostepnosc`, `ocena`, `gwarancja`, `data-sku`, `data-id`). Brak losowych identyfikatorów typu `a3jX9`.

### Poziom 4.0 (Wymagania rozszerzone)
* [x] **Paginacja:** 9 podstron po 50 rekordów (wymóg: min. 5 podstron, min. 200 rekordów).
* [x] **Podstrony szczegółów:** Każdy rekord ma podstronę `detail.html?id=X` z 10 dodatkowymi atrybutami (łącznie 24 atrybuty).
* [x] **Wybrane utrudnienia z poziomu 4.0 (zrealizowano 7, wymagane min. 3):**
  1. *Różne waluty i formatowanie cen:* Ceny zapisane w formacie polskim z przecinkiem i spacją twardą (`1 299,00 zł`), a u części rekordów w EUR (`799,00 EUR`) i USD (`$649.99`).
  2. *Braki danych u min. 15% rekordów:* W polach `ocena` (17.7% braków) oraz `gwarancja` (21.2% braków).
  3. *Zduplikowane rekordy:* Dokładnie 10 zduplikowanych rekordów rozrzuconych po różnych podstronach katalogu.
  4. *Atrybuty w znacznikach `data-*`:* Kody SKU oraz EAN umieszczone w `data-sku="..."` oraz `data-ean="..."`.
  5. *Niespójne formaty dat:* Daty w formatach ISO (`2026-08-26`), kropkowym (`26.08.2026`), ukośnikowym (`26/08/2026`) oraz relatywnym (`wczoraj`, `dzisiaj`, `przedwczoraj`).
  6. *Encje i znaki specjalne:* W opisach obecne encje HTML (`&nbsp;`, `&oacute;`, `&amp;`, `&eogon;`, `&lstrok;`).
  7. *Tabela bez `<tbody>` i niezamknięte znaczniki:* Wiersze tabeli dodawane bezpośrednio pod `<table>`, a opisy w komórkach zawierają celowo niezamknięte akapity `<p>`.

### Poziom 5.0 (Wymagania najwyższe)
* [x] **Brak rekordów w surowym źródle HTML (Ctrl+U):** W pliku `index.html` oraz `detail.html` nie ma żadnych rekordów produktów. Wszystkie dane są wstrzykiwane asynchronicznie przez JavaScript za pomocą `fetch()`.
* [x] **Doładowywanie porcjami:** Zaimplementowany przycisk `"Wczytaj więcej produktów (↓)"` doładowujący kolejne porcje bez przeładowania strony.
* [x] **Min. 400 rekordów i min. 22 atrybuty:** 430 rekordów, 24 atrybuty.
* [x] **Sztuczne opóźnienie 300–2000 ms:** Serwer oraz frontend wprowadzają sztuczne opóźnienie (350–850 ms) przy każdym pobraniu danych.
* [x] **Wybrane utrudnienia z poziomu 5.0:**
  1. *Dedykowany serwer Python z kodem HTTP 429 i nagłówkiem `Retry-After`:* Serwer `server.py` implementuje mechanizm rate limitera &ndash; wysłanie więcej niż 6 zapytań w oknie 2 sekund powoduje zwrócenie odpowiedzi `429 Too Many Requests` wraz z nagłówkiem `Retry-After: 2`.
  2. *Atrybut widoczny dopiero po interakcji:* Na podstronie szczegółów atrybut `specyfikacja_ukryta` znajduje się w elemencie `<details id="sekcja-ukryta-details">` wymagającym kliknięcia `<summary>`, a dodatkowo w interaktywnej zakładce ("Diagnostyka laboratoryjna").
  3. *Losowa kolejność atrybutów w karcie produktu:* W kartach produktów (`.produkt-karta`) wiersze z atrybutami są losowo przetasowane dla każdego rekordu algorytmem Fishera-Yatesa &ndash; scraper musi korzystać z etykiet lub klas, a nie stałych pozycji/indeksów w drzewie DOM.
  4. *Filtrowanie i sortowanie na żywo:* Zmiana kategorii lub sortowania cen/nazw bez przeładowania strony.

---

## 4. Pełna lista 24 atrybutów każdego produktu

| Lp. | Nazwa atrybutu | Miejsce występowania | Przykładowa wartość |
|:---:|:---|:---|:---|
| 1 | `id` | Lista + Szczegóły | `1` |
| 2 | `nazwa` | Lista + Szczegóły | `Lenovo ThinkPad T14 #1` |
| 3 | `cena` | Lista + Szczegóły | `3 499,00 zł` / `799,00 EUR` / `$649.99` |
| 4 | `kategoria` | Lista + Szczegóły | `Laptopy` |
| 5 | `producent` | Lista + Szczegóły | `Lenovo` |
| 6 | `dostepnosc` | Lista + Szczegóły | `W magazynie` |
| 7 | `ocena` | Lista + Szczegóły (braki ~18%) | `4.8` |
| 8 | `liczba_opinii` | Lista + Szczegóły | `142` |
| 9 | `data_dodania` | Lista + Szczegóły (różne formaty) | `2026-08-26`, `26.08.2026`, `wczoraj` |
| 10 | `gwarancja` | Lista + Szczegóły (braki ~18%) | `24 miesiące` |
| 11 | `kod_produktu` | Atrybut `data-sku` | `SKU-10001` |
| 12 | `ean` | Atrybut `data-ean` | `590000000001` |
| 13 | `stan` | Lista + Szczegóły | `Nowy` / `Powystawowy` |
| 14 | `darmowa_dostawa` | Lista + Szczegóły | `Tak` / `Nie` |
| 15 | `opis` | Podstrona szczegółów | Tekst ze znacznikami HTML i encjami |
| 16 | `kolor` | Podstrona szczegółów | `Czarny mat` |
| 17 | `waga` | Podstrona szczegółów | `1.75 kg` |
| 18 | `wymiary` | Podstrona szczegółów | `35 x 24 x 2 cm` |
| 19 | `kraj_pochodzenia` | Podstrona szczegółów | `Polska` |
| 20 | `certyfikaty` | Podstrona szczegółów | `CE, RoHS, Energy Star` |
| 21 | `material` | Podstrona szczegółów | `Stop magnezu i aluminium` |
| 22 | `zasilanie` | Podstrona szczegółów | `USB-C Power Delivery 65W` |
| 23 | `zawartosc_zestawu` | Podstrona szczegółów | `Urządzenie, kabel zasilający, instrukcja` |
| 24 | `specyfikacja_ukryta` | Podstrona szczegółów (wymaga interakcji) | `Taktowanie magistrali: 4800 MHz; Hałas: 22 dB...` |
