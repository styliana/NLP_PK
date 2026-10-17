import os
import re
from collections import Counter

import matplotlib.pyplot as plt
import nltk
from nltk.util import ngrams
from stop_words import get_stop_words

nltk.download('punkt_tab', quiet=True)

PLOTS_DIR = 'wykresy'

UPPER = 'A-ZĄĆĘŁŃÓŚŹŻ'
LOWER = 'a-ząćęłńóśźż'
# wyraz z wielkiej litery, przed którym w tej samej linii stoi inny wyraz
# (ewentualnie z przecinkiem, średnikiem lub dwukropkiem) i spacja;
# odpada więc początek zdania (po . ! ? lub myślniku) i początek wersu
PROPER_NAME = re.compile(rf'(?<=[\w,;:] )[{UPPER}][{LOWER}]+')


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


def clean_book(book):
    book = re.sub(r'[^\w\s]', '', book)
    book = book.lower()
    book = re.sub(r'\s+', ' ', book)
    return book.strip()


def tokenize_words(book):
    raw_tokens = nltk.word_tokenize(clean_book(book), language='polish')
    return [word for word in raw_tokens if word.isalnum()]


def count_ngrams(words):
    return {n: Counter(ngrams(words, n)) for n in (1, 2, 3)}


def plot_top_ngrams(counts, nazwa, filename, color):
    plt.figure(figsize=(12, 8))
    top_ngrams = counts.most_common(10)
    top_ngrams.reverse()
    labels = [" ".join(gram) for gram, count in top_ngrams]
    values = [count for gram, count in top_ngrams]
    plt.barh(labels, values, color=color)
    plt.title(f"Top 10 {nazwa}", fontsize=12, fontweight='bold')
    plt.xlabel("Liczba wystąpień")
    plt.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plt.savefig(os.path.join(PLOTS_DIR, filename), dpi=120)
    plt.show()


def print_side_by_side(with_stop, without_stop, nazwa, n=10):
    print(f"\n--- Top {n} {nazwa}: ze stop words | bez stop words ---")
    left = with_stop.most_common(n)
    right = without_stop.most_common(n)
    for (g1, c1), (g2, c2) in zip(left, right):
        print(f"{' '.join(g1):<28} {c1:>5}   | {' '.join(g2):<32} {c2:>4}")


def distribution_stats(counts, nazwa):
    total = sum(counts.values())
    unique = len(counts)
    hapax = sum(1 for c in counts.values() if c == 1)
    top10 = sum(c for _, c in counts.most_common(10))
    print(f"{nazwa:<26} wystąpień: {total:>6}  unikalnych: {unique:>6}  "
          f"jednokrotnych: {hapax / unique:6.1%}  "
          f"top10 pokrywa: {top10 / total:6.2%}  "
          f"max: {counts.most_common(1)[0][1]}")


def find_proper_names(book):
    names = Counter()
    for line in book.splitlines():
        names.update(PROPER_NAME.findall(line))
    return names


pan_tadeusz = read_book('books/pan-tadeusz.txt')
pan_tadeusz = strip_wolne_lektury(pan_tadeusz)

# 1. usunięcie stop words
stop = set(get_stop_words('polish'))
words = tokenize_words(pan_tadeusz)
content_words = [w for w in words if w not in stop]
print(f"Lista stop words (biblioteka stop-words): {len(stop)} słów")
print(f"Wyrazów przed usunięciem stop words: {len(words)}")
print(f"Wyrazów po usunięciu stop words:     {len(content_words)} "
      f"(usunięto {1 - len(content_words) / len(words):.1%})")

# 2. analiza n-gramów na obu wariantach
with_stop = count_ngrams(words)
without_stop = count_ngrams(content_words)
for n, nazwa in ((1, "unigramów"), (2, "bigramów"), (3, "trigramów")):
    print_side_by_side(with_stop[n], without_stop[n], nazwa)

print("\n--- Porównanie rozkładów ---")
for n, nazwa in ((1, "unigramy"), (2, "bigramy"), (3, "trigramy")):
    distribution_stats(with_stop[n], f"{nazwa} ze stop words")
    distribution_stats(without_stop[n], f"{nazwa} bez stop words")

for n, nazwa in ((1, "unigram"), (2, "bigram"), (3, "trigram")):
    plot_top_ngrams(without_stop[n], f"{nazwa} bez stop words",
                    f"5g_top10_{nazwa}_bez_stop_words.png", 'lightcoral')

# 4-5. nazwy własne
names = find_proper_names(pan_tadeusz)
print(f"\nKandydaci na nazwy własne: {sum(names.values())} wystąpień, "
      f"{len(names)} różnych wyrazów")
print("\n--- Top 10 nazw własnych ---")
for name, count in names.most_common(10):
    print(f"{name:<16} {count:>4}")
plot_top_ngrams(Counter({(name,): c for name, c in names.items()}),
                "nazw własnych", "5g_top10_nazwy_wlasne.png", 'mediumseagreen')
