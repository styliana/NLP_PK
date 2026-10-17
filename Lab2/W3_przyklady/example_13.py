"""
example_13.py — Ile tokenów ma to zdanie? Tokenizatory lokalnie
Wykład 3, slajd „Tokenizatory online — i jak policzyć tokeny samemu”

Uruchomienie:  python example_13.py
Wymagania:     pip install tiktoken transformers
Wszystko darmowe — tiktoken liczy lokalnie, bez klucza API.
"""

ZDANIE_PL = "Przetwarzanie języka naturalnego jest fascynujące."
ZDANIE_EN = "Natural language processing is fascinating."

print("=" * 62)
print("tiktoken — tokenizatory OpenAI, liczone LOKALNIE (bez klucza API)")
print("=" * 62)
try:
    import tiktoken
    for enc_name in ["cl100k_base", "o200k_base"]:
        enc = tiktoken.get_encoding(enc_name)
        pl = enc.encode(ZDANIE_PL)
        en = enc.encode(ZDANIE_EN)
        print(f"\n{enc_name}  (słownik: {enc.n_vocab} tokenów)")
        print(f"  PL: {len(pl):2} tokenów  {[enc.decode([t]) for t in pl]}")
        print(f"  EN: {len(en):2} tokenów  {[enc.decode([t]) for t in en]}")
        print(f"  podatek językowy: {len(pl) / len(en):.2f}×")
except ImportError:
    print("Zainstaluj: pip install tiktoken")

print()
print("=" * 62)
print("transformers — dowolny tokenizator z Hugging Face")
print("=" * 62)
try:
    from transformers import AutoTokenizer
    MODELE = [
        ("gpt2", "BPE, angielski"),
        ("allegro/herbert-base-cased", "WordPiece, polski"),
        ("google-t5/t5-small", "Unigram/SentencePiece"),
    ]
    for nazwa, opis in MODELE:
        try:
            tok = AutoTokenizer.from_pretrained(nazwa)
        except Exception as e:
            print(f"{nazwa:32} — pominięty ({type(e).__name__})")
            continue
        pl = tok.tokenize(ZDANIE_PL)
        en = tok.tokenize(ZDANIE_EN)
        print(f"\n{nazwa}  ({opis}, |V| = {tok.vocab_size})")
        print(f"  PL: {len(pl):2} tokenów  {pl}")
        print(f"  EN: {len(en):2} tokenów  {en}")
except ImportError:
    print("Zainstaluj: pip install transformers")

print()
print("To samo w przeglądarce, bez instalowania czegokolwiek:")
print("  https://platform.openai.com/tokenizer")
print("  https://huggingface.co/spaces/Xenova/the-tokenizer-playground")
