# Kulisy implementacji parsera TechStore (Parser2)
> **Dziennik deweloperski, wyzwania inżynieryjne oraz analiza rezultatów na ocenę 5.0**

---

## Rozdział 1: Na czym skupiał się developer parsera?

Głównym zadaniem dewelopera było stworzenie odpornego, szybkiego i w pełni zautomatyzowanego parsera dla serwisu e-commerce **TechStore** (Parser2), który został celowo najeżony utrudnieniami na ocenę 5.0.

Poniżej przedstawiono kluczowe wyzwania i decyzje architektoniczne podjęte podczas pracy:

### 1. Rozpracowanie dynamicznego ładowania danych (Architektura SPA)
- **Pierwsza pułapka:** Pobranie kodu źródłowego (`Ctrl+U` / standardowe `requests.get()`) ujawniło, że **na stronie nie ma ani jednego produktu**. W źródle HTML znajdowały się wyłącznie puste szkielety tabeli (`<tbody id="wiersze-produktow">`) oraz kart (`<div id="lista-kart">`).
- **Inżynieria wsteczna frontendu:** Analiza skryptu `katalog.js` oraz zakładki *Network* w DevTools wykazała, że frontend wykonuje asynchroniczne zapytanie `fetch("dane/produkty.json")`, a następnie JavaScriptem generuje elementy DOM w porcjach po 48 rekordów z losowym opóźnieniem sieciowym (300–2000 ms).
- **Decyzja architektoniczna:** Zamiast powolnej symulacji klikania w przeglądarce (Selenium wymagałoby kilkunastu sekund na odczekanie sztucznych opóźnień), wykorzystano oficjalnie punktowane rozszerzenie poziomu 5.0 z regulaminu: *„Wykrycie i wykorzystanie źródła danych, z którego korzysta strona (plik JSON), wraz z omówieniem, dlaczego jest to szybsze”*. Pozwoliło to zredukować czas pobrania danych do **poniżej 30 ms**.

### 2. Normalizacja wielowalutowości cen
- W bazie serwisu ceny podane były w 3 różnych walutach i formatach: polskie złote (`5 429,99 zł`), euro (`302,99 €`) oraz dolary amerykańskie (`$324.99`), dodatkowo ze spacjami twardymi (`\xa0`) i zmiennymi separatorami dziesiętnymi.
- Developer zaimplementował funkcję `parsuj_cene()`, która:
  - Rozpoznaje walutę na podstawie prefiksów i sufiksów,
  - Usuwa znaki walutowe i spacje twarde,
  - Normalizuje separator dziesiętny do formatu liczbowego `float`,
  - Przelicza kwoty w obcych walutach na wspólną walutę (PLN) według stałych kursów serwisu (EUR: 4.30, USD: 4.00).

### 3. Bezpieczna obsługa braków danych (Missing Values)
- Serwis celowo zawierał braki w danych: brak oceny (`null`, ok. 18.3% rekordów) oraz brak gwarancji (brak klucza w obiekcie, ok. 17.4% rekordów).
- Standardowy parser zakończyłby działanie błędem `KeyError` lub `TypeError`.
- Developer zabezpieczył ekstrakcję metodą `dict.get()` z domyślnym `None`, a brakujące wartości w wyjściowych tabelach reprezentowane są jako czyste puste komórki lub czytelny komunikat `"brak informacji"`.

### 4. Wykrywanie i eliminacja duplikatów
- Autor serwisu celowo rozrzucił 12 zduplikowanych produktów po różnych porcjach katalogu (np. produkt o ID 1150 został sztucznie wstawiony na 7. pozycję w porcji pierwszej, podczas gdy jego oryginał znajdował się w porcji czwartej).
- Parser śledzi zbiór unikalnych identyfikatorów (`seen_ids`) – w momencie natrafienia na powtórzony rekord zlicza go do statystyk i odrzuca.

### 5. Spójność wizualna i sortowanie wg ID
- Aby dane w wygenerowanym pliku idealnie odpowiadały temu, co użytkownik widzi na stronie, developer wprowadził:
  - **Sortowanie po `id` rosnąco (1001–1420):** Dzięki temu wiersze w pliku nie „skaczą” i odpowiadają logicznej kolejności produktów.
  - **Układ kolumn 1:1 z tabelą w przeglądarce:** Kolumny ułożono dokładnie tak, jak w nagłówkach strony: `SKU -> Nazwa -> Kategoria -> Producent -> Cena -> Dostępność -> Ocena -> Opinie -> Data dodania -> Gwarancja -> Kolor -> Waga`, a dopiero po nich umieszczono parametry ze strony szczegółów.
  - **Ujednolicenie formatów:** Daty sformatowano jako `DD.MM.YYYY` (zgodnie z widokiem strony), a wagę zapisano w dwóch formach: czytelny tekst (`1,43 kg`) oraz czysta liczba zmiennoprzecinkowa (`1.43`).

### 6. Odporność na blokady plików w systemie Windows
- Gdy użytkownik ma otwarty plik CSV/XLSX w programie Microsoft Excel, system Windows zakłada wyłączną blokadę zapisu.
- Zamiast rzucać błąd `PermissionError: [Errno 13]`, parser przechwytuje wyjątek i informuje użytkownika o pominięciu nadpisywania otwartego pliku.

---

## Rozdział 2: Efekt implementacji – Jak to zostało zbudowane?

Moduł został podzielony na wyspecjalizowane, modularne skrypty w katalogu `Lab1/Parser2`:

| Plik | Rola techniczna | Co realizuje |
|---|---|---|
| **`parser.py`** | Główny silnik ekstrakcji | Pobiera dane z endpointu HTTP (lub pliku lokalnego), czyści waluty, deduplikuje, sortuje i eksportuje do **XLSX**, **CSV** i **JSON**. |
| **`test_parser.py`** | Weryfikacja jakości | 4 testy jednostkowe (`unittest`): parsowanie walut, obsługa braków, deduplikacja, walidacja typów kolumn. |
| **`analiza.py`** | Analityka statystyczna | Wylicza pełne statystyki opisowe (średnia, mediana, moda, Q1, Q3, IQR, outliery) i generuje 3 wykresy PNG w `wykresy/`. |
| **`porownanie_html_vs_dom.py`** | Diagnostyka wymogu 5.0 | Bada surowy HTML (bez JS) kontra drzewo DOM i tworzy raport z twardymi liczbami. |
| **`uruchom_calosc.py`** | Master skrypt | Integruje cały potok przetwarzania i uruchamia wszystkie kroki sekwencyjnie. |

---

## Rozdział 3: Jak wyglądają pozyskane dane i rezultaty?

### 1. Twarde liczby z kontroli jakości danych
- **Pobrane rekordy ogółem:** 432
- **Unikalne rekordy po czyszczeniu:** 420
- **Wykryte i odrzucone duplikaty:** 12
- **Braki w polu `ocena`:** 77 sztuk (**18.33%**)
- **Braki w polu `gwarancja`:** 73 sztuki (**17.38%**)
- **Rozkład walut:** PLN: 379 ofert, EUR: 19 ofert, USD: 22 oferty

### 2. Zestawienie surowy HTML vs Drzewo DOM (Wymóg 5.0)
| Parametr | Surowy HTML (bez JS / Ctrl+U) | Drzewo DOM / Po wykonaniu JS |
|---|---|---|
| **Czas odpowiedzi** | ~60 ms | ~25 ms |
| **Rozmiar pobranych danych** | 4.7 KB | 493 KB |
| **Liczba produktów w tabeli** | 0 | 216 |
| **Liczba produktów w kartach** | 0 | 216 |
| **ŁĄCZNA LICZBA PRODUKTÓW** | **0 (0.0%)** | **432 (100.0%)** |

> **Wniosek:** Próba scrapowania surowego HTML daje 0 rekordów. Zastosowanie inżynierii wstecznej i bezpośredniego endpointu JSON pozwoliło pozyskać 100% bazy w czasie poniżej 30 ms.

### 3. Statystyki opisowe cen i cech liczbowych
- **Cena w PLN:** min = 79.99 zł, max = 7 949.99 zł, średnia = 1 993.86 zł, mediana = 1 504.99 zł, moda = 639.99 zł, IQR = 1 797.50 zł.
- **Wartości odstające (outliery):** 28 produktów powyżej 5 233.74 zł (flagowe laptopy i smartfony – naturalny segment premium, nie błąd parsera).
- **Ocena:** min = 3.1, max = 5.0, średnia = 4.05 / 5.0, mediana = 4.0.
- **Waga:** min = 0.04 kg, max = 14.72 kg, średnia = 3.12 kg, mediana = 1.19 kg.
- **Korelacja waga vs cena:** współczynnik Pearsona $r = -0.077$ (brak bezpośredniej korelacji liniowej między samą wagą a ceną).

### 4. Wygenerowane pliki i wykresy
- **Katalog `wyniki/`:**
  - `produkty_oczyszczone.xlsx` – arkusz Excel z 420 wierszami i 30 kolumnami,
  - `produkty_oczyszczone.csv` – plik CSV z kodowaniem UTF-8 z BOM,
  - `produkty_oczyszczone.json` – baza danych w formacie JSON,
  - `raport_jakosci.txt` i `porownanie_html_vs_dom.txt` – raporty tekstowe.
- **Katalog `wykresy/`:**
  - `1_histogram_cen.png` – histogram rozkładu cen w PLN ze średnią i medianą,
  - `2_boxplot_cen.png` – wykres pudełkowy cen z podziałem na kategorie produktowe,
  - `3_korelacja_cena_waga.png` – wykres rozrzutu z naniesioną linią trendu regresji.

---

## Rozdział 4: Sposób weryfikacji

Aby zweryfikować poprawne działanie całego modułu na żywo:
```powershell
python Lab1/Parser2/uruchom_calosc.py
```
Wszystkie 4 moduły kończą pracę z kodem `0`, a wygenerowane zbiory danych w `wyniki/` są natychmiast gotowe do inspekcji w programie Microsoft Excel lub dowolnym edytorze.
