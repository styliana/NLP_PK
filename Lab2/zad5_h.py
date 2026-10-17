import os
import re

import matplotlib.pyplot as plt
from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers
from transformers import AutoTokenizer

PLOTS_DIR = 'wykresy'
RESULTS_FILE = 'wyniki5_h.txt'
CORPUS = 'books/pan-tadeusz.txt'

VOCAB_SIZES = [1000, 5000, 30000]
MAIN_VOCAB = 5000                      # wariant porównywany z gotowymi tokenizatorami
CURVE_SIZES = [300, 500, 1000, 2000, 3000, 5000, 7500, 10000, 15000, 20000, 30000]

WORDS = ['nieprzetłumaczalny', 'hiperparametryzacja', 'kotkowi', 'Soplicowo']

SENTENCES = {
    'PL': [
        'Litwo! Ojczyzno moja! ty jesteś jak zdrowie.',
        'Tymczasem przenoś moją duszę utęsknioną do tych pagórków leśnych, do tych łąk zielonych.',
        'Przetwarzanie języka naturalnego to dziedzina sztucznej inteligencji.',
        'Wczoraj wieczorem pojechałam tramwajem do centrum handlowego, żeby kupić nowy telefon.',
        'Rząd zapowiedział podwyżkę podatków od przyszłego roku kalendarzowego.',
    ],
    'EN': [
        'To be, or not to be, that is the question.',
        'There are more things in heaven and earth, Horatio, than are dreamt of in your philosophy.',
        'Natural language processing is a field of artificial intelligence.',
        'Yesterday evening I took the tram to the shopping centre to buy a new phone.',
        'The government announced a tax increase starting next calendar year.',
    ],
}

# Bielik-1.5B-v3 jest na Hugging Face repozytorium z ograniczonym dostępem (gated);
# jeśli nie da się go pobrać, bierzemy tokenizator z otwartego modelu tej samej rodziny v3
BIELIK_REPOS = ['speakleash/Bielik-1.5B-v3', 'speakleash/Bielik-4.5B-v3.0-Instruct']
HF_TOKENIZERS = {'gpt2': 'gpt2', 'HerBERT': 'allegro/herbert-base-cased'}


def read_book(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f'File {filename} not found')
        return None


def strip_wolne_lektury(book):
    # stopka licencyjna Wolnych Lektur zaczyna sie od linii "-----"
    footer = book.rfind('\n-----\n')
    if footer != -1:
        book = book[:footer]
    # nagłówek: usuwamy linie z numerem ISBN
    book = re.sub(r'^ISBN.*$', '', book, flags=re.MULTILINE)
    return book


def train_bpe(lines, vocab_size):
    tokenizer = Tokenizer(models.BPE(unk_token='[UNK]'))
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=True)
    tokenizer.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(
        vocab_size=vocab_size,
        min_frequency=2,
        special_tokens=['[UNK]', '[CLS]', '[SEP]', '[PAD]', '[MASK]'],
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
        show_progress=False,
    )
    tokenizer.train_from_iterator(lines, trainer)
    return tokenizer


def readable_tokens(tokenizer, text):
    # tokeny ByteLevel zapisują polskie litery jako bajty ("Å‚"), więc dekodujemy każdy osobno
    return [tokenizer.decode([i]) for i in tokenizer.encode(text).ids]


def load_bielik():
    for repo in BIELIK_REPOS:
        try:
            return repo, AutoTokenizer.from_pretrained(repo)
        except OSError as e:
            print(f'{repo}: nie udało się pobrać ({type(e).__name__})')
    raise RuntimeError('Brak dostępu do żadnego tokenizatora Bielika')


def plot_average(averages):
    names = list(averages)
    x = range(len(names))
    width = 0.38
    plt.figure(figsize=(10, 6))
    bars_pl = plt.bar([i - width / 2 for i in x], [averages[n]['PL'] for n in names],
                      width, label='polski', color='indianred')
    bars_en = plt.bar([i + width / 2 for i in x], [averages[n]['EN'] for n in names],
                      width, label='angielski', color='steelblue')
    plt.bar_label(bars_pl, fmt='%.1f')
    plt.bar_label(bars_en, fmt='%.1f')
    plt.xticks(list(x), names)
    plt.ylabel('Średnia liczba tokenów na zdanie')
    plt.title('Średnia liczba tokenów na zdanie', fontsize=12, fontweight='bold')
    plt.legend()
    plt.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plt.savefig(os.path.join(PLOTS_DIR, '5h_srednia_tokenow.png'), dpi=120)
    plt.show()


def plot_curve(curve, words_in_corpus):
    sizes = [s for s, _ in curve]
    counts = [c for _, c in curve]
    plt.figure(figsize=(10, 6))
    plt.plot(sizes, counts, marker='o', color='darkorange')
    plt.axhline(words_in_corpus, linestyle='--', color='gray',
                label=f'liczba wyrazów w korpusie ({words_in_corpus})')
    plt.xscale('log')
    plt.xlabel('Rozmiar słownika (skala log)')
    plt.ylabel('Liczba tokenów w całym korpusie')
    plt.title('Liczba tokenów a rozmiar słownika (Pan Tadeusz)', fontsize=12, fontweight='bold')
    plt.legend()
    plt.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plt.savefig(os.path.join(PLOTS_DIR, '5h_tokeny_vs_slownik.png'), dpi=120)
    plt.show()


book = strip_wolne_lektury(read_book(CORPUS))
lines = [line for line in book.splitlines() if line.strip()]
words_in_corpus = len(book.split())
output = [f'Korpus: {CORPUS}, {len(book)} znaków, {words_in_corpus} wyrazów (podział po spacjach)', '']

# 1-2. trzy tokenizatory BPE o różnych rozmiarach słownika
own = {}
for size in VOCAB_SIZES:
    tokenizer = train_bpe(lines, size)
    own[size] = tokenizer
    name = 'tokenizer_pl.json' if size == MAIN_VOCAB else f'tokenizer_pl_{size}.json'
    tokenizer.save(name)
    output.append(f'BPE {size:>6}: faktyczny rozmiar słownika {tokenizer.get_vocab_size():>6}, zapisano {name}')
output.append('')

# 3. podział wybranych słów
output.append('--- Podział słów ---')
for word in WORDS:
    output.append(word)
    for size, tokenizer in own.items():
        tokens = readable_tokens(tokenizer, word)
        output.append(f'  BPE {size:>6}: {len(tokens):>2} tok.  {" | ".join(t.strip() for t in tokens)}')
output.append('')

# 4. liczba tokenów na zdanie dla czterech tokenizatorów
bielik_repo, bielik = load_bielik()
counters = {f'własny BPE {MAIN_VOCAB}': lambda s: len(own[MAIN_VOCAB].encode(s).tokens)}
for label, repo in HF_TOKENIZERS.items():
    tok = AutoTokenizer.from_pretrained(repo)
    counters[label] = lambda s, tok=tok: len(tok.tokenize(s))
counters['Bielik'] = lambda s: len(bielik.tokenize(s))
for size in VOCAB_SIZES:
    if size != MAIN_VOCAB:
        counters[f'własny BPE {size}'] = lambda s, size=size: len(own[size].encode(s).tokens)

output.append(f'Bielik: tokenizator z {bielik_repo} (rozmiar słownika {len(bielik)})')
output.append('')
names = list(counters)
header = f"{'zdanie':<6} {'wyrazy':>6} " + ''.join(f'{n:>17}' for n in names)
averages = {n: {} for n in names}
for lang, sentences in SENTENCES.items():
    output.append(f'--- Liczba tokenów: {lang} ---')
    output.append(header)
    totals = {n: 0 for n in names}
    for i, s in enumerate(sentences, 1):
        counts = {n: f(s) for n, f in counters.items()}
        for n in names:
            totals[n] += counts[n]
        output.append(f'{lang}{i:<4} {len(s.split()):>6} ' + ''.join(f'{counts[n]:>17}' for n in names))
    for n in names:
        averages[n][lang] = totals[n] / len(sentences)
    output.append(f"{'średnio':<6} {'':>6} " + ''.join(f'{averages[n][lang]:>17.1f}' for n in names))
    output.append('')
for lang, sentences in SENTENCES.items():
    output.append(f'Zdania {lang}:')
    output.extend(f'  {lang}{i}: {s}' for i, s in enumerate(sentences, 1))
output.append('')

# zależność liczby tokenów od rozmiaru słownika (cały korpus)
output.append('--- Liczba tokenów w całym korpusie a rozmiar słownika ---')
curve = []
for size in CURVE_SIZES:
    tokenizer = own[size] if size in own else train_bpe(lines, size)
    n_tokens = sum(len(enc.tokens) for enc in tokenizer.encode_batch(lines))
    curve.append((size, n_tokens))
    output.append(f'  słownik {size:>6}: {n_tokens:>7} tokenów  ({n_tokens / words_in_corpus:.2f} tok./wyraz)')

report = '\n'.join(output)
print(report)
with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
    f.write(report + '\n')

plot_average({n: averages[n] for n in [f'własny BPE {MAIN_VOCAB}', 'gpt2', 'HerBERT', 'Bielik']})
plot_curve(curve, words_in_corpus)
