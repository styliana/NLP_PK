# Lab 1 – rola AUTOR, poziom 5.0

Serwis TechStore: fikcyjny katalog produktów elektronicznych przygotowany do sparsowania.
Wszystkie rekordy są wczytywane JavaScriptem z pliku `dane/produkty.json` – w źródle HTML (Ctrl+U) nie ma żadnego produktu.

## Uruchomienie

W folderze `Parser2`:

```bash
py -m http.server 8000
```

- katalog: http://localhost:8000/ (podstrony: `?strona=1` … `?strona=9`)
- szczegóły produktu: http://localhost:8000/produkt.html?id=1001

Serwer jest potrzebny, bo `fetch` nie działa przy otwieraniu pliku z dysku.

## Pliki

| Plik | Co to jest |
|---|---|
| `index.html`, `katalog.js` | katalog: tabela + karty, paginacja, „Wczytaj więcej”, filtry |
| `produkt.html`, `produkt.js` | podstrona szczegółów produktu |
| `wspolne.js` | funkcje wspólne (opóźnienie, formatowanie) |
| `dane/produkty.json` | wszystkie rekordy (432); kolejne 48 rekordów = 1 porcja = 1 podstrona |
| `styles.css` | style (ciemny motyw) |
| `generate_site.py` | generator danych JSON (`py generate_site.py`) |

## Wymagania i realizacja

### Poziom 3.0

| Wymaganie | Realizacja |
|---|---|
| min. 60 rekordów | 432 rekordy |
| min. 10 atrybutów | 12 atrybutów w tabeli i kartach |
| dwie struktury: tabela i karty | z każdej porcji 24 rekordy trafiają do `<table>`, 24 do `<article>` |
| semantyczne klasy i id | np. `produkt`, `cena`, `dostepnosc`, `data-id` |
| strona statyczna, bez JS | zastąpione wymaganiem 5.0 (treść wstrzykiwana JavaScriptem) |

### Poziom 4.0

| Wymaganie | Realizacja |
|---|---|
| paginacja: min. 5 podstron, min. 200 rekordów | 9 podstron (`?strona=N`) po 48 rekordów (432) |
| strony szczegółów: +8 atrybutów, razem min. 18 | `produkt.html?id=N` – 30 atrybutów, w tym 14 niewidocznych na liście |
| utrudnienie 1: ceny „1 299,00 zł” i inna waluta | ceny w zł oraz w € (`302,99 €`) i $ (`$324.99`), ok. 10% w obcej walucie |
| utrudnienie 2: braki w 2 polach u min. 15% | brak oceny 18,3%, brak gwarancji 17,4% |
| utrudnienie 3: min. 8 duplikatów na różnych podstronach | 12 duplikatów, każdy na innej podstronie niż oryginał |

### Poziom 5.0

| Wymaganie | Realizacja |
|---|---|
| rekordy z JSON przez `fetch`, brak rekordów w Ctrl+U | `katalog.js` i `produkt.js` pobierają `dane/produkty.json` |
| doładowywanie porcjami | przycisk „Wczytaj więcej” dokłada kolejną porcję 48 rekordów |
| min. 400 rekordów i 22 atrybuty | 432 rekordy (420 + 12 duplikatów), 30 atrybutów |
| opóźnienie 300–2000 ms | losowe opóźnienie przed wyświetleniem każdej porcji |
| utrudnienie 1: atrybut widoczny po interakcji | EAN, numer katalogowy, wymiary i materiał w karcie pojawiają się po rozwinięciu `<details>` |
| utrudnienie 2: filtrowanie / sortowanie bez przeładowania | filtr kategorii, dostępności, promocji, wyszukiwarka i sortowanie |

## Co pokazać na zajęciach

1. Ctrl+U: w źródle są tylko pusta tabela i pusty kontener kart, bez produktów.
2. F12 → Network: strona pobiera `dane/produkty.json`; „Wczytaj więcej” dokłada porcję po losowym opóźnieniu (skeleton w trakcie).
3. Paginacja: przejście na inną podstronę (`?strona=N`), tabela i karty na każdej z nich.
4. Szczegóły produktu: kliknięcie nazwy otwiera `produkt.html?id=N` z 30 atrybutami.
5. F12 → Elements: szczegóły techniczne w karcie pojawiają się w kodzie dopiero po rozwinięciu.
6. Filtry i sortowanie zmieniają listę bez przeładowania strony.
