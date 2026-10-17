"""
example_15.py — Ile tokenów kosztuje polszczyzna? Bielik kontra reszta
Wykład 3, slajd „Bielik i polskie tokenizatory”

Uruchomienie:  python example_15.py
Wymagania:     pip install transformers
Pobierane są WYŁĄCZNIE pliki tokenizatorów (kilkaset kB), nie wagi modeli.
Wszystko darmowe.
"""

from transformers import AutoTokenizer

TEKSTY = {
    "PL": "Przetwarzanie języka naturalnego to dziedzina sztucznej inteligencji.",
    "EN": "Natural language processing is a field of artificial intelligence.",
}

MODELE = [
    ("gpt2",                        "BPE, korpus angielski"),
    ("allegro/herbert-base-cased",  "WordPiece, korpus polski"),
    ("speakleash/Bielik-1.5B-v3",   "polski model SpeakLeash"),
    ("google-t5/t5-small",          "Unigram, angielski"),
]

wyniki = {}
for nazwa, opis in MODELE:
    try:
        tok = AutoTokenizer.from_pretrained(nazwa)
    except Exception as e:
        print(f"{nazwa:32} — pominięty ({type(e).__name__})")
        continue
    wyniki[nazwa] = {j: len(tok.tokenize(t)) for j, t in TEKSTY.items()}
    wyniki[nazwa]["opis"] = opis
    wyniki[nazwa]["V"] = tok.vocab_size

print()
print(f"{'tokenizator':32} {'|V|':>8} {'PL':>4} {'EN':>4} {'PL/EN':>7}")
print("-" * 62)
for nazwa, w in wyniki.items():
    stosunek = w["PL"] / w["EN"] if w["EN"] else 0
    print(f"{nazwa:32} {w['V']:>8} {w['PL']:>4} {w['EN']:>4} {stosunek:>7.2f}")
print()
print("Im niższy stosunek PL/EN, tym tańsza polszczyzna dla danego modelu.")
print("Tokenizator uczony na polskim korpusie tnie polskie słowa w sensownych")
print("miejscach — anglocentryczny rozbija je na pojedyncze litery.")
print()

# Podgląd konkretnego podziału
for nazwa in list(wyniki)[:2]:
    tok = AutoTokenizer.from_pretrained(nazwa)
    print(f"{nazwa}:")
    print("  ", tok.tokenize("nieprzetłumaczalny"))
