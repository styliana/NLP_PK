"""
example_03.py — Tokenizacja znakowa
Wykład 3, slajd „Tokenizacja znakowa — przykład”

Uruchomienie:  python example_03.py
Wymagania:     brak
"""

text = "Kot siedzi na macie."

chars = list(text)                 # podział na znaki
print("liczba tokenów:", len(chars))
print("pierwsze sześć:", chars[:6])
print()

# Czytelny podgląd — spacje pokazane jako ␣
print(" ".join(z if z != " " else "␣" for z in chars))
print()

# Bez spacji byłoby ich mniej — to też decyzja projektowa
bez_spacji = [z for z in chars if not z.isspace()]
print("bez spacji:", len(bez_spacji), "tokenów")
print()

# UWAGA: list() dzieli na ZNAKI, nie na bajty
w = "żółw"
print(f"{w!r}: {len(w)} znaki, ale {len(w.encode('utf-8'))} bajtów")
print("znaki:", list(w))
print("bajty:", list(w.encode("utf-8")))
