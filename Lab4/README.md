# Laboratorium 4 — analiza sentymentu

## Krok 1: zbiór danych i podział

Wybrano zadanie B z instrukcji: klasyfikację sentymentu zdań z recenzji filmowych.
Źródłem jest **Cornell Sentence Polarity v1.0** (Pang i Lee, 2005), dostępny
także jako korpus `sentence_polarity` w NLTK. Zawiera 10 662 zdania: 5 331
negatywnych (etykieta `0`) i 5 331 pozytywnych (etykieta `1`).

Skrypt pobiera korpus przez NLTK, jeśli nie jest jeszcze zainstalowany, sprawdza
liczebności klas oraz unikalność zdań, a następnie tworzy stratyfikowany podział
80/20 z ustalonym ziarnem `42`. Każde zdanie trafia tylko do jednego podzbioru.
Podział jest wykonywany przed preprocessingiem i uczeniem, aby przygotować
niezależny zbiór testowy.

### Uruchomienie

Wymagany jest Python 3.10+ oraz dostęp do sieci przy pierwszym pobraniu korpusu:

```powershell
python -m pip install -r Lab4/requirements.txt
python Lab4/scripts/prepare_data.py
```

W `Lab4/data/processed/` powstaną `train.csv`, `test.csv` oraz
`dataset_summary.json` z rozmiarami i liczebnościami klas. Korpus i wygenerowane
pliki są lokalne i wykluczone z Git; nie będą dołączane do archiwum oddania.

## Krok 2: preprocessing

Po podziale każdy podzbiór jest przetwarzany niezależnie, bez dopasowywania
jakichkolwiek parametrów do testu. Preprocessing obejmuje zamianę na małe litery,
tokenizację słów, usuwanie angielskich stop words, tagowanie części mowy
(Penn Treebank) i lematyzację WordNet z uwzględnieniem części mowy. Stop words
istotne dla polaryzacji — m.in. `not`, `no`, `never` i `but` — pozostają, aby
nie usuwać negacji ani kontrastu zmieniającego sens zdania.

Oryginalny tekst jest zachowany obok `processed_text` do audytu i porównań z
alternatywnymi wariantami preprocessingu. Jeśli usuwanie stop words usunęłoby
wszystkie tokeny zdania, skrypt zachowuje jego zlematyzowaną treść, zamiast tworzyć
pusty przykład.
W `Lab4/data/preprocessed/` powstaną pliki CSV dla treningu i testu oraz
`preprocessing_summary.json` ze statystykami tokenów. Brakujące korpusy WordNet
i tagger NLTK są pobierane przy pierwszym uruchomieniu.

```powershell
python Lab4/scripts/preprocess_data.py
python -m unittest discover -s Lab4 -p "test_*.py"
```

## Kroki 3–6: reprezentacje, klasyfikacja i raport

Po przygotowaniu i preprocessingu zbioru wykonaj pełne eksperymenty:

```powershell
python Lab4/scripts/run_all.py
```

Kompletne uruchomienie można też wykonać etapami, aby powtórzyć tylko wybrany
krok:

```powershell
python Lab4/scripts/run_experiments.py
python Lab4/scripts/generate_plots.py
python Lab4/scripts/generate_report.py
python Lab4/scripts/package_submission.py
```

### Struktura katalogów

- `scripts/` — przygotowanie i preprocessing danych, eksperymenty, wykresy,
  raportowanie, pakowanie oraz testy.
- `data/` — korpusy i podziały treningowy/testowy generowane lokalnie; katalog
  jest ignorowany przez Git i nie trafia do paczki.
- `wyniki/` — CSV i JSON z metrykami, parametrami oraz historią prób Optuny.
- `wykresy/` — wykresy porównawcze oraz podkatalog `macierze_pomylek/`.
- `sprawozdanie/` — końcowy raport PDF i jego edytowalna wersja Markdown.
- `oddanie/` — gotowe archiwum ZIP do przekazania.

`run_experiments.py` buduje sześć reprezentacji:

1. Bag-of-Words,
2. słowny TF-IDF,
3. znakowy TF-IDF,
4. średnia z Word2Vec (Skip-gram, uczony na treningu),
5. Doc2Vec DBOW (uczony na treningu),
6. średnia z gotowych wektorów GloVe `glove-wiki-gigaword-100`.

Oprócz korpusu Cornell GloVe jest pobierany przy pierwszym uruchomieniu
`gensim.downloader` (wymagane połączenie z internetem i miejsce na cache Gensim).
Każda z 42 par reprezentacja–klasyfikator jest strojoną przez RandomizedSearchCV
i GridSearchCV. Optuna wykonuje jedno globalne badanie TPE z 30 próbami, które
wybiera reprezentację, klasyfikator i jego hiperparametry. Wszystkie metody używają
2-fold `StratifiedKFold`, `random_state=42` i F1 klasy pozytywnej do wyboru; dwa
foldy pozwalają utrzymać porównywalny i wykonalny budżet dla wszystkich 42 par
oraz 30 prób Optuny. Zbiór testowy jest używany dopiero do oceny końcowej.
Każda metoda stroi modele na tej samej, powtarzalnej, stratyfikowanej próbce
1 500 rekordów treningowych. Wybrane konfiguracje dopasowuje się ponownie na pełnym
zbiorze treningowym, z wyjątkiem RBF SVC, którego końcowe dopasowanie pozostaje
na tej próbce ze względu na kwadratową złożoność obliczania jądra. Dzięki temu
próbki walidacyjne i budżet strojenia są wspólne dla wszystkich reprezentacji
oraz klasyfikatorów.

Wyniki są zapisywane w `Lab4/wyniki/`: `all_results.csv` zawiera testowe accuracy,
F1, TN/FP/FN/TP i parametry dla 84 kombinacji Random/Grid oraz najlepszego modelu
Optuny; `experiment_summary.json` i `representation_details.json` podają
konfigurację, wymiary, pokrycie embeddingów i czas. `optuna_trials.csv` zawiera
historię prób. W `Lab4/wykresy/` znajdują się porównania wyników, a w
`Lab4/wykresy/macierze_pomylek/` macierze dla wszystkich par model–reprezentacja
oraz najlepszego modelu Optuny. Raport PDF i jego edytowalna treść Markdown są w
`Lab4/sprawozdanie/`.

Na końcu `scripts/package_submission.py` tworzy w `oddanie/` archiwum
`LAB4_Golek_Aleksandra_Karczmarczyk_Klaudia.zip`. Zawiera kod, dokumentację,
wyniki, wykresy i sprawozdanie, ale celowo nie dołącza danych źródłowych ani
podziałów.
