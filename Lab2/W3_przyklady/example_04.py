"""
example_04.py — Tokenizacja słowna: split() kontra word_tokenize()
Wykład 3, slajd „Tokenizacja słowna — przykład”

Uruchomienie:  python example_04.py
Wymagania:     pip install nltk
Pierwsze uruchomienie pobiera model punkt (potrzebny internet).
"""

import nltk

try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab")

text = "Ala ma koty i kotka."

print("tekst:          ", text)
print("split():        ", text.split())
print("word_tokenize():", nltk.word_tokenize(text))
print()
print("Różnica: split() zostawia kropkę przyklejoną do 'kotka',")
print("word_tokenize() traktuje ją jako osobny token.")
print()

# Na trudniejszym zdaniu widać to jeszcze lepiej
trudne = "Nie mogę dojechać na 8.30 — pociąg z Kraków-Płaszów ma opóźnienie!"
print("tekst:          ", trudne)
print("split():        ", trudne.split())
print("word_tokenize():", nltk.word_tokenize(trudne))
