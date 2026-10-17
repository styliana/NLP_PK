"""
example_08.py — Stemming: Porter, Lancaster, Snowball (i dlaczego nie po polsku)
Wykład 3, slajd „Stemming w kodzie — i dlaczego nie po polsku”

Uruchomienie:  python example_08.py
Wymagania:     pip install nltk
"""

from nltk.stem import PorterStemmer, LancasterStemmer, SnowballStemmer

porter = PorterStemmer()
lancaster = LancasterStemmer()
snowball = SnowballStemmer("english")

slowa = ["running", "runner", "flies", "studies", "happily",
         "organization", "better", "cats", "universities"]

print(f"{'słowo':14} {'Porter':12} {'Lancaster':12} {'Snowball'}")
print("-" * 52)
for w in slowa:
    print(f"{w:14} {porter.stem(w):12} {lancaster.stem(w):12} {snowball.stem(w)}")
print()
print("flies  → 'fli'    : rdzeń nie musi być słowem")
print("better → 'bet'    : Lancaster ucina za dużo (nadmierne obcinanie)")
print()

# ---------------------------------------------------------------
# SNOWBALL NIE OBSŁUGUJE POLSKIEGO
# ---------------------------------------------------------------
print("języki Snowballa:", SnowballStemmer.languages)
print("czy jest polski?", "polish" in SnowballStemmer.languages)
print()
print("Co się stanie, gdy mimo to podamy polskie słowa angielskiemu stemmerowi:")
for w in ["koty", "kotka", "kotami", "psami", "biegać"]:
    print(f"  {w:10} → {snowball.stem(w)!r}")
print()
print("Wniosek: dla polszczyzny stemming odpada — używamy lematyzacji.")
print("(Istnieje biblioteka pystempel/Stempel, ale w praktyce sięga się od razu po lematyzację.)")
