"""
example_18.py — Odległość edycyjna (Levenshteina)
Wykład 3, slajdy „Odległość Levenshteina — kot i kto” oraz „w kodzie”

Uruchomienie:  python example_18.py
Wymagania:     brak (część z bibliotekami jest opcjonalna)
"""

def levenshtein(a, b, pokaz_macierz=False):
    D = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        D[i][0] = i
    for j in range(len(b) + 1):
        D[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            koszt = 0 if a[i - 1] == b[j - 1] else 1
            D[i][j] = min(D[i - 1][j] + 1,        # usunięcie
                          D[i][j - 1] + 1,        # wstawienie
                          D[i - 1][j - 1] + koszt)  # zamiana
    if pokaz_macierz:
        print("     ∅ " + " ".join(b))
        for i, wiersz in enumerate(D):
            etykieta = "∅" if i == 0 else a[i - 1]
            print(f"  {etykieta}  " + " ".join(str(v) for v in wiersz))
    return D[-1][-1]

print("=== macierz dla 'kot' → 'kto' ===")
d = levenshtein("kot", "kto", pokaz_macierz=True)
print("odległość =", d, " (wynik z prawego dolnego rogu)")
print()

PARY = [("kot", "kota"), ("tokenizacja", "tokenizacji"),
        ("Kraków", "Krakow"), ("kot", "kto"),
        ("Ala ma kota", "Ala posiada kota")]
print(f"{'A':16} {'B':18} {'odległość'}")
print("-" * 46)
for a, b in PARY:
    print(f"{a:16} {b:18} {levenshtein(a, b)}")
print()

# --- gotowe biblioteki --------------------------------------------
try:
    from rapidfuzz.distance import Levenshtein, DamerauLevenshtein, Jaro, JaroWinkler
    print("=== rapidfuzz: kilka miar obok siebie ===")
    print(f"{'para':28} {'Lev':>5} {'Dam':>5} {'Jaro':>7} {'JaroW':>7}")
    print("-" * 56)
    for a, b in PARY:
        print(f"{a + ' / ' + b:28} "
              f"{Levenshtein.distance(a, b):>5} "
              f"{DamerauLevenshtein.distance(a, b):>5} "
              f"{Jaro.similarity(a, b):>7.3f} "
              f"{JaroWinkler.similarity(a, b):>7.3f}")
    print()
    print("Damerau liczy przestawienie sąsiednich liter jako JEDNĄ operację,")
    print("dlatego 'kot' → 'kto' kosztuje u niego 1, a nie 2.")
except ImportError:
    print("(opcjonalnie) pip install rapidfuzz")

print()
try:
    import textdistance
    print("=== textdistance (biblioteka z laboratorium) ===")
    a, b = "Ala ma kota", "Ala posiada kota"
    print("Levenshtein:", textdistance.levenshtein(a, b))
    print("Hamming:    ", textdistance.hamming(a, b))
    print("Jaccard:    ", round(textdistance.jaccard(a.split(), b.split()), 3))
    print("Cosine:     ", round(textdistance.cosine(a.split(), b.split()), 3))
except ImportError:
    print("(opcjonalnie) pip install textdistance")
