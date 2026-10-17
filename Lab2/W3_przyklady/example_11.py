"""
example_11.py — WordPiece: BERT i HerBERT
Wykład 3, slajd „WordPiece w kodzie”

Uruchomienie:  python example_11.py
Wymagania:     pip install transformers
Pierwsze uruchomienie pobiera pliki tokenizatorów (potrzebny internet).
"""

from transformers import AutoTokenizer

zdania = ["tokenization", "nieprzetłumaczalny", "Kot siedzi na macie."]

for nazwa in ["bert-base-uncased", "allegro/herbert-base-cased"]:
    print("=" * 60)
    print("tokenizator:", nazwa)
    try:
        tok = AutoTokenizer.from_pretrained(nazwa)
    except Exception as e:
        print("  nie udało się pobrać:", type(e).__name__)
        continue
    print("  rozmiar słownika:", tok.vocab_size)
    for z in zdania:
        tokeny = tok.tokenize(z)
        print(f"  {z!r:24} → {len(tokeny):2} tok.  {tokeny}")
    print()

# Prefiks ## oznacza kontynuację słowa
tok = AutoTokenizer.from_pretrained("bert-base-uncased")
print("identyfikatory dla ['token', '##ization']:",
      tok.convert_tokens_to_ids(["token", "##ization"]))
