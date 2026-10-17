"""
example_02.py — Unicode i UTF-8: znaki kontra bajty
Wykład 3, slajd „Unicode i UTF-8: świat poza alfabetem angielskim”

Uruchomienie:  python example_02.py
Wymagania:     brak
"""

import unicodedata

s = "Zażółć gęślą jaźń"
print("tekst:              ", s)
print("długość w ZNAKACH:  ", len(s))
print("długość w BAJTACH:  ", len(s.encode("utf-8")))
print()

# Tabela: znak → code point → bajty UTF-8
print(f"{'znak':6} {'code point':12} {'UTF-8':14} {'nazwa'}")
for z in "aąłż€😀":
    cp = f"U+{ord(z):04X}"
    bajty = " ".join(f"{b:02X}" for b in z.encode("utf-8"))
    try:
        nazwa = unicodedata.name(z)
    except ValueError:
        nazwa = "?"
    print(f"{z:6} {cp:12} {bajty:14} {nazwa}")
print()

# PUŁAPKA: ten sam wygląd, dwa różne napisy
a = "\u00e9"                 # U+00E9 — jeden znak (é)
b = "e\u0301"                # e + znak łączący U+0301 — dwa znaki
print(f"a = {a!r}  len={len(a)}")
print(f"b = {b!r}  len={len(b)}")
print("a == b ?", a == b)
print("po normalizacji NFC:", unicodedata.normalize("NFC", a) == unicodedata.normalize("NFC", b))
