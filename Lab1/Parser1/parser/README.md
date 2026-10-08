# Lab 1 – rola PARSER, poziom 5.0

Parser serwisu TechStore  (folder `Parser1`). Selenium + requests/BeautifulSoup + pandas.

## Uruchomienie

1. Serwis – w folderze `Parser1`:
   ```bash
   py server.py
   ```
2. Parser – w folderze `Parser1/parser` (z aktywnym `.venv`):
   ```bash
   py scraper.py --headless        # pełny przebieg, ok. 25 min (limit serwisu: 6 żądań / 2 s)
   py zrodlo_json.py               # rozszerzenie: dane prosto z pliku JSON + porównanie
   py analiza.py                   # kontrola jakości, statystyki, wykresy
   py -m pytest -v                 # testy funkcji czyszczących
   ```

Opcje `scraper.py`: `--url`, `--wyjscie`, `--opoznienie` (domyślnie 2 s, min. 0,5 s), `--limit N` (szczegóły tylko N produktów – do testów), `--headless`, `--od-nowa` (bez wznawiania).

## Pliki

| Plik | Zawartość |
|---|---|
| `scraper.py` | Selenium: surowy HTML, „Wczytaj więcej”, 9 podstron, podstrony szczegółów, ponawianie, 429, checkpoint, log, eksport |
| `czyszczenie.py` | funkcje czyszczące (ceny, oceny, daty, gwarancja, waga…) – bez Selenium |
| `test_czyszczenie.py` | testy jednostkowe funkcji czyszczących (pytest) |
| `zrodlo_json.py` | pobranie `/data/products.json` bez przeglądarki, porównanie wyników i czasu z Selenium |
| `analiza.py` | kontrola jakości, statystyki opisowe, wykresy, korelacje → `wyniki/raport_analizy.md` |
| `wyniki/produkty.csv`, `.json`, `.xlsx` | dane wynikowe (UTF-8) |
| `wyniki/podsumowanie.json` | liczby z przebiegu: surowy HTML, DOM, duplikaty, błędy, 429, czas |
| `wyniki/parser.log` | log przebiegu |
| `wyniki/surowe_*.json` | surowe dane przed czyszczeniem |
| `wyniki/bledy/` | zrzuty ekranu i źródła stron przy błędach |

## Wymagania

### 3.0
| Wymaganie | Realizacja |
|---|---|
| CSV/XLSX, wiersz = rekord, kolumna = atrybut | `produkty.csv` i `produkty.xlsx` |
| min. 60 wierszy z obu struktur, wspólny format | karty (`article.produkt-karta`) i tabela (`tr.produkt-wiersz`) → te same klucze, kolumna `zrodlo_listy` |
| cena jako liczba | `cena` (float) + osobna kolumna `waluta` |
| UTF-8, polskie znaki | CSV w `utf-8-sig` (poprawnie otwiera się w Excelu) |
| opóźnienie między żądaniami | min. 2 s między wejściami na strony (`--opoznienie`) |

### 4.0
| Wymaganie | Realizacja |
|---|---|
| min. 200 rekordów, 18 atrybutów | 420 rekordów, 29 kolumn |
| wszystkie podstrony + podstrony szczegółów, łączenie danych | 9 podstron `?page=N` + `detail.html?id=N` dla każdego produktu, łączenie po `id` |
| czyszczenie: ceny, formaty, duplikaty | `czyszczenie.py`: ceny PLN/EUR/USD, 4 formaty dat + daty względne, oceny, gwarancja; duplikaty usuwane po `id` |
| brak danych = pusta wartość | funkcje zwracają `None` zamiast wyjątku |
| opóźnienie min. 0,5 s | domyślnie 2 s, wymuszone min. 0,5 s |
| **rozszerzenie: testy jednostkowe** | `test_czyszczenie.py` – 34 przypadki testowe |
| **rozszerzenie: eksport do dwóch formatów** | CSV + JSON (+ XLSX) |
| dodatkowo: log do pliku, parametry z linii poleceń | `parser.log` z podsumowaniem; `argparse` |

### 5.0
| Wymaganie | Realizacja |
|---|---|
| Selenium | `scraper.py` |
| jawne oczekiwanie (`WebDriverWait`), bez sztywnego `sleep` | każde czekanie na stronę/dane to `WebDriverWait` z warunkiem |
| doładowywanie aż do wyczerpania rekordów | „Wczytaj więcej” do momentu, gdy nie przybywa nowych `id` |
| ponawianie z opóźnieniem wykładniczym i limitem prób | `ponawiaj()`: 1 s, 2 s, 4 s, 8 s, maks. 5 prób |
| porównanie surowego HTML i DOM | `podsumowanie.json` → `surowy_html` i `dom_wczytaj_wiecej`; tabela w `raport_analizy.md` |
| **rozszerzenie: kod 429 z `Retry-After`** | kody HTTP odczytywane z dziennika sieci Chrome; przy 429 czekanie wg `Retry-After` |
| **rozszerzenie: wykrycie źródła danych (JSON)** | `zrodlo_json.py` |
| dodatkowo: zrzut ekranu i źródła strony przy błędzie | `wyniki/bledy/` |
| dodatkowo: wznawianie przerwanej sesji | `wyniki/checkpoint_szczegoly.json` |