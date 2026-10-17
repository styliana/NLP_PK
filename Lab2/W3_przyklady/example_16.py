"""
example_16.py — n-gramy znakowe
Wykład 3, slajd „n-gramy znakowe — przykład”

Uruchomienie:  python example_16.py
Wymagania:     pip install nltk  (jest też wersja bez nltk)
"""

text = "statystyka"
chars = list(text)

print(f"słowo: {text!r}  ({len(text)} znaków)")
print()

# --- wersja bez żadnej biblioteki ---------------------------------
print("bez bibliotek:")
for n in (1, 2, 3, 4):
    grams = [text[i:i + n] for i in range(len(text) - n + 1)]
    print(f"  n={n}  ({len(grams)}): {', '.join(grams)}")
print()
print("liczba n-gramów = L - n + 1 = 10 - n + 1")
print()

# --- to samo przez nltk -------------------------------------------
try:
    from nltk.util import ngrams
    print("przez nltk.util.ngrams:")
    for n in (1, 2, 3, 4):
        grams = ["".join(g) for g in ngrams(chars, n)]
        print(f"  n={n}  ({len(grams)}): {', '.join(grams)}")
except ImportError:
    print("Zainstaluj: pip install nltk")
print()

# --- do czego to służy: odcisk palca języka ------------------------
from collections import Counter

PROBKI = {
    "polski":    "Szczęście sprzyja odważnym, a czasem przypadek rzeczywiście pomaga",
    "angielski": "Fortune favours the bold, and sometimes chance really does help",
}
print("najczęstsze trigramy znakowe:")
for jezyk, probka in PROBKI.items():
    t = probka.lower().replace(" ", "")
    tri = Counter(t[i:i + 3] for i in range(len(t) - 2))
    print(f"  {jezyk:10} {[g for g, _ in tri.most_common(6)]}")
