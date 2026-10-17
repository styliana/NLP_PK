"""
example_17.py — n-gramy słowne
Wykład 3, slajd „n-gramy słowne — przykład”

Uruchomienie:  python example_17.py
Wymagania:     pip install nltk
"""

from collections import Counter

sentence = "Ala ma kota"
words = sentence.split()

print(f"zdanie: {sentence!r}  ({len(words)} wyrazy)")
print()
for n in (1, 2, 3, 4):
    grams = [tuple(words[i:i + n]) for i in range(len(words) - n + 1)]
    nazwa = {1: "unigramy", 2: "bigramy", 3: "trigramy", 4: "czterogramy"}[n]
    print(f"{nazwa:12} (n={n}): {grams}")
print()
print("Dla n = 4 przy trzech słowach lista jest PUSTA — to nie błąd.")
print()

try:
    from nltk.util import ngrams
    print("nltk.util.ngrams(words, 2) →", list(ngrams(words, 2)))
except ImportError:
    print("Zainstaluj: pip install nltk")
print()

# --- po co: bigramy widzą negację, unigramy nie -------------------
A = "film jest dobry"
B = "film nie jest dobry"
print("unigramy:")
print("  ", sorted(A.split()), "\n  ", sorted(B.split()))
print("bigramy:")
for z in (A, B):
    w = z.split()
    print("  ", [" ".join(w[i:i + 2]) for i in range(len(w) - 1)])
print()
print("Na poziomie unigramów oba zdania różnią się jednym słowem.")
print("Bigram 'nie jest' jest osobną cechą i od razu niesie negację.")
print()

# --- częstości na dłuższym tekście --------------------------------
tekst = ("Ala ma kota a kot ma Alę i Ala ma psa "
         "a pies ma Alę i Ala ma rybki")
w = tekst.split()
bigramy = Counter(zip(w, w[1:]))
print("najczęstsze bigramy:", bigramy.most_common(3))
