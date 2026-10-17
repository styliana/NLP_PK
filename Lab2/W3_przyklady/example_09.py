"""
example_09.py — Lematyzacja: angielski (WordNet) i polski (spaCy)
Wykład 3, slajd „Lematyzacja w kodzie”

Uruchomienie:  python example_09.py
Wymagania:     pip install nltk spacy
               python -m spacy download pl_core_news_sm
"""

import nltk

# --- angielski: WordNet -------------------------------------------
try:
    nltk.data.find("corpora/wordnet")
except LookupError:
    nltk.download("wordnet")

from nltk.stem import WordNetLemmatizer

lem = WordNetLemmatizer()
print("=== angielski (WordNet) ===")
print("cats            →", lem.lemmatize("cats"))
print("better (bez pos)→", lem.lemmatize("better"))
print("better (pos='a')→", lem.lemmatize("better", pos="a"), "  ← stemming tego nie potrafi")
print("running (pos='v')→", lem.lemmatize("running", pos="v"))
print()
print("Bez podania części mowy (pos) lematyzator zgaduje 'rzeczownik' i wynik bywa gorszy.")
print()

# --- polski: spaCy -------------------------------------------------
print("=== polski (spaCy) ===")
try:
    import spacy
    nlp = spacy.load("pl_core_news_sm")
    doc = nlp("Koty biegały po łące. Psami zajmował się najlepszy weterynarz.")
    print(f"{'token':14} {'lemat':14} {'część mowy'}")
    print("-" * 40)
    for t in doc:
        if not t.is_punct:
            print(f"{t.text:14} {t.lemma_:14} {t.pos_}")
    print()
    print("spaCy zwraca lemat RAZEM z częścią mowy — to ten sam model rozstrzyga oba pytania.")
except OSError:
    print("Brak modelu. Zainstaluj:  python -m spacy download pl_core_news_sm")
except ImportError:
    print("Zainstaluj:  pip install spacy")
