"""
example_14.py — Trenowanie WŁASNEGO tokenizatora BPE na polskim tekście
Wykład 3, slajd „Własny tokenizator — kilka linijek kodu”

Uruchomienie:  python example_14.py
Wymagania:     pip install tokenizers
               (pobranie korpusu wymaga internetu; przy jego braku
                skrypt użyje wbudowanego mini-korpusu)

Wszystko darmowe: biblioteka tokenizers od Hugging Face + teksty
z Wolnych Lektur (domena publiczna).
"""

import os
import urllib.request

from tokenizers import Tokenizer, models, trainers, pre_tokenizers, decoders

KORPUS = "pan_tadeusz.txt"
URL = "https://wolnelektury.pl/media/book/txt/pan-tadeusz.txt"

# --- 1. Korpus ----------------------------------------------------
if not os.path.exists(KORPUS):
    try:
        print("pobieram korpus…")
        urllib.request.urlretrieve(URL, KORPUS)
    except Exception as e:
        print("nie udało się pobrać:", type(e).__name__, "— używam mini-korpusu")
        with open(KORPUS, "w", encoding="utf-8") as f:
            f.write(("Litwo, Ojczyzno moja! ty jesteś jak zdrowie. "
                     "Ile cię trzeba cenić, ten tylko się dowie, "
                     "kto cię stracił. Dziś piękność twą w całej ozdobie "
                     "widzę i opisuję, bo tęsknię po tobie.\n") * 500)

rozmiar = os.path.getsize(KORPUS) / 1024
print(f"korpus: {KORPUS} ({rozmiar:.0f} kB)")

# --- 2. Definicja tokenizatora -----------------------------------
tokenizer = Tokenizer(models.BPE(unk_token="[UNK]"))
tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=True)
tokenizer.decoder = decoders.ByteLevel()

trainer = trainers.BpeTrainer(
    vocab_size=5000,                       # docelowy rozmiar słownika
    min_frequency=2,
    special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
)

# --- 3. Uczenie ---------------------------------------------------
print("uczę tokenizatora…")
tokenizer.train([KORPUS], trainer)
tokenizer.save("tokenizer_pl.json")
print("zapisano: tokenizer_pl.json")
print("rozmiar słownika:", tokenizer.get_vocab_size())
print()

# --- 4. Test ------------------------------------------------------
TESTY = [
    "Litwo, Ojczyzno moja!",
    "nieprzetłumaczalny",
    "Przetwarzanie języka naturalnego",
    "Natural language processing",
]
for t in TESTY:
    enc = tokenizer.encode(t)
    print(f"{t!r:36} → {len(enc.tokens):2} tok.  {enc.tokens}")
print()

# --- 5. Porównanie z gotowym tokenizatorem ------------------------
try:
    from transformers import AutoTokenizer
    gpt2 = AutoTokenizer.from_pretrained("gpt2")
    print(f"{'tekst':36} {'nasz':>6} {'GPT-2':>7}")
    print("-" * 52)
    for t in TESTY:
        n_nasz = len(tokenizer.encode(t).tokens)
        n_gpt2 = len(gpt2.tokenize(t))
        print(f"{t!r:36} {n_nasz:6} {n_gpt2:7}")
    print()
    print("Tokenizator uczony na polskim tekście potrzebuje mniej tokenów")
    print("na polszczyznę — i więcej na angielski. To ta sama zależność,")
    print("co na slajdzie o podatku językowym.")
except Exception as e:
    print("(porównanie pominięte)", type(e).__name__)
