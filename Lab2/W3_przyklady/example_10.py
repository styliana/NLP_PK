"""
example_10.py — BPE: uczenie od zera i tokenizacja nowego słowa
Wykład 3, slajdy „BPE — uczenie krok po kroku” oraz „BPE w kodzie”

Uruchomienie:  python example_10.py
Wymagania:     brak (część z transformers jest opcjonalna)
"""

from collections import Counter

korpus = {"kot": 5, "kota": 4, "kotek": 3, "koty": 2}
slowa = {tuple(w): n for w, n in korpus.items()}
scalenia = []

print("Korpus:", korpus)
print("Alfabet startowy:", sorted({z for w in korpus for z in w}))
print()

def scal(slowo, para):
    """Podstawia parę (a, b) jako jedną jednostkę w krotce znaków."""
    a, b = para
    wynik, i = [], 0
    while i < len(slowo):
        if i < len(slowo) - 1 and slowo[i] == a and slowo[i + 1] == b:
            wynik.append(a + b)
            i += 2
        else:
            wynik.append(slowo[i])
            i += 1
    return tuple(wynik)

LICZBA_SCALEN = 6
for krok in range(1, LICZBA_SCALEN + 1):
    pary = Counter()
    for w, n in slowa.items():
        for a, b in zip(w, w[1:]):
            pary[(a, b)] += n          # ważymy częstością słowa
    if not pary:
        break
    best = max(pary, key=pary.get)     # przy remisie: pierwsza napotkana
    scalenia.append(best)
    print(f"krok {krok}: {dict(pary)}")
    print(f"         scalamy {best} ({pary[best]}×) → {''.join(best)!r}")
    slowa = {scal(w, best): n for w, n in slowa.items()}
    print(f"         korpus: {[' '.join(w) for w in slowa]}")
    print()

print("Lista scaleń:", [(a, b) for a, b in scalenia])
print()

# ---------------------------------------------------------------
# TOKENIZACJA NOWEGO SŁOWA — stosujemy scalenia PO KOLEI
# ---------------------------------------------------------------
def tokenizuj(slowo, scalenia):
    t = tuple(slowo)
    for para in scalenia:
        t = scal(t, para)
    return list(t)

for w in ["kotu", "kotek", "kotkowi"]:
    print(f"{w:10} → {tokenizuj(w, scalenia)}")
print()
print("Słowa 'kotu' nie było w korpusie, a rdzeń 'kot' i tak został rozpoznany.")
print()

# ---------------------------------------------------------------
# W PRAKTYCE: gotowa biblioteka
# ---------------------------------------------------------------
try:
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("gpt2")
    for w in ["kotu", "nieprzetłumaczalny"]:
        print(f"GPT-2  {w!r:22} → {tok.tokenize(w)}")
except Exception as e:
    print("(część opcjonalna) pip install transformers —", type(e).__name__)
