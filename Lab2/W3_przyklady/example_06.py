"""
example_06.py — Normalizacja tekstu i pułapka na polszczyznę
Wykład 3, slajd „Normalizacja w kodzie — i pułapka na polszczyznę”

Uruchomienie:  python example_06.py
Wymagania:     brak
"""

import re
import unicodedata

s = "  Łódź   to   MIASTO! "

s = unicodedata.normalize("NFC", s)      # ujednolicenie zapisu znaków
s = re.sub(r"\s+", " ", s).strip()       # zwinięcie białych znaków
print("po czyszczeniu:      ", repr(s))
print("lowercase:           ", repr(s.lower()))
print("bez interpunkcji:    ", repr(re.sub(r"[^\w\s]", "", s)))
print()

# ---------------------------------------------------------------
# POPULARNA SZTUCZKA NA USUWANIE DIAKRYTYKÓW — I DLACZEGO NIE
# ---------------------------------------------------------------
def bez_ogonkow(t: str) -> str:
    return unicodedata.normalize("NFD", t).encode("ascii", "ignore").decode()

for slowo in ["kąt", "łaska", "Łódź", "gęś", "źrebię"]:
    print(f"{slowo:10} → {bez_ogonkow(slowo)!r}")
print()
print("kąt  → 'kat'   : zupełnie inne słowo")
print("łaska→ 'aska'  : ł nie ma rozkładu kanonicznego, więc znika")
print("Łódź → 'odz'   : zostały trzy litery z czterech")
print()
print("Jeśli naprawdę musisz — użyj jawnej tablicy podmian:")
TABLICA = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
for slowo in ["kąt", "łaska", "Łódź"]:
    print(f"{slowo:10} → {slowo.translate(TABLICA)!r}")
