"""
example_01.py — Znak to liczba: ASCII i kody znaków
Wykład 3, slajd „Pierwszy pomysł: tabela znak → liczba”

Uruchomienie:  python example_01.py
Wymagania:     brak (sama biblioteka standardowa)
"""

# ord() zamienia znak na jego numer w Unicode, chr() robi odwrotnie
print("ord('A') =", ord("A"))
print("ord('a') =", ord("a"))
print("ord('ż') =", ord("ż"))
print()
print("chr(65)  =", chr(65))
print("chr(380) =", chr(380))
print()

# Cały wyraz jako ciąg liczb
slowo = "kot"
print(f"{slowo!r} jako kody znaków:", [ord(z) for z in slowo])
print(f"{slowo!r} szesnastkowo:     ", [hex(ord(z)) for z in slowo])
print()

# PYTANIE DO SALI:
# czy ciąg [107, 111, 116] jest "bliżej" słowa 'pies' czy słowa 'koty'?
for inne in ("kod", "koty", "pies"):
    kody = [ord(z) for z in inne]
    print(f"{inne!r:8} → {kody}")
print()
print("Wniosek: odległość między kodami nie ma nic wspólnego ze znaczeniem.")
