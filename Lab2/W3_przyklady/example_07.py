"""
example_07.py — Stop words po angielsku i po polsku
Wykład 3, slajd „Stop words w kodzie — i kiedy ich nie ruszać”

Uruchomienie:  python example_07.py
Wymagania:     pip install nltk stop-words
"""

import nltk

# --- angielski: lista jest w nltk ---------------------------------
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

from nltk.corpus import stopwords

en = stopwords.words("english")
print("angielskich stop words:", len(en))
print("pierwsze osiem:", en[:8])
print()
print("języki dostępne w nltk:", len(stopwords.fileids()))
print("czy jest polski?", "polish" in stopwords.fileids())
print()

# --- polski: trzeba innej biblioteki ------------------------------
try:
    from stop_words import get_stop_words
    pl = get_stop_words("pl")
    print("polskich stop words:", len(pl))
    print("pierwsze osiem:", pl[:8])
except ImportError:
    print("Zainstaluj: pip install stop-words")
    pl = ["i", "w", "na", "nie", "to", "się", "z", "że", "do", "jest"]

print()
# --- dlaczego bezmyślne usuwanie boli -----------------------------
zdanie = "Nie polecam tej książki"
tokeny = zdanie.lower().split()
po_filtrze = [t for t in tokeny if t not in pl]
print("przed:", tokeny)
print("po:   ", po_filtrze)
print()
print("Jeśli 'nie' jest na liście stop words, z 'nie polecam' zostaje 'polecam'.")
print("czy 'nie' jest na polskiej liście?", "nie" in pl)
