"""
example_12.py — SentencePiece / Unigram: znak ▁ i bezstratna detokenizacja
Wykład 3, slajd „SentencePiece w kodzie”

Uruchomienie:  python example_12.py
Wymagania:     pip install transformers sentencepiece
"""

from transformers import AutoTokenizer

# T5 używa SentencePiece z modelem Unigram
tok = AutoTokenizer.from_pretrained("google-t5/t5-small")

teksty = ["Kot siedzi na macie.", "Ala  ma   dużo   spacji"]

for t in teksty:
    tokeny = tok.tokenize(t)
    print(f"tekst:   {t!r}")
    print(f"tokeny:  {tokeny}")
    print(f"odtworzony: {tok.convert_tokens_to_string(tokeny)!r}")
    print()

print("Znak ▁ (U+2581) oznacza początek słowa — spacja jest CZĘŚCIĄ tokenu.")
print("Dzięki temu sklejenie tokenów odtwarza tekst razem z odstępami.")
print()

# --- uczenie własnego modelu SentencePiece (opcjonalnie) ----------
print("Aby wytrenować własny model SentencePiece:")
print("""
    import sentencepiece as spm
    spm.SentencePieceTrainer.train(
        input="korpus_pl.txt", model_prefix="pl",
        vocab_size=8000, model_type="unigram")   # albo "bpe"
    sp = spm.SentencePieceProcessor(model_file="pl.model")
    sp.encode("Kot siedzi na macie.", out_type=str)
""")
