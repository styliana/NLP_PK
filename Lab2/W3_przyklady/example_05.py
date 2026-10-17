"""
example_05.py — Tokenizacja zdaniowa: dlaczego kropka nie wystarcza
Wykład 3, slajd „Tokenizacja zdaniowa — przykład”

Uruchomienie:  python example_05.py
Wymagania:     pip install nltk
"""

import nltk

try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab")

text = "Dr hab. Nowak przyjechał o 8.30. Spotkanie zaczęło się punktualnie."

print("tekst:", text)
print()

naiwnie = text.split(".")
print("split('.') — fragmentów:", len(naiwnie))
for i, frag in enumerate(naiwnie, 1):
    print(f"  {i}. {frag!r}")
print()

zdania = nltk.sent_tokenize(text)
print("sent_tokenize() — zdań:", len(zdania))
for i, z in enumerate(zdania, 1):
    print(f"  {i}. {z!r}")
print()
print("Uwaga: model punkt jest uczony na angielskim i nie zna polskich skrótów.")
print("Dla polszczyzny właściwym wyborem są spaCy (pl_core_news_sm) albo Stanza.")
