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
python Lab4/prepare_data.py
```

W `Lab4/data/processed/` powstaną `train.csv`, `test.csv` oraz
`dataset_summary.json` z rozmiarami i liczebnościami klas. Korpus i wygenerowane
pliki są lokalne i wykluczone z Git; nie będą dołączane do archiwum oddania.
