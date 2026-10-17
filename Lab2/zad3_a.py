import os
import re
from collections import Counter

import matplotlib.pyplot as plt
import nltk
from nltk.util import ngrams
from stop_words import get_stop_words

nltk.download('punkt_tab', quiet=True)

PLOTS_DIR = 'wykresy'


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


def plot_top_ngrams(counts, nazwa):
    plt.figure(figsize=(12, 8))
    top_ngrams = counts.most_common(10)
    top_ngrams.reverse()
    labels = [" ".join(gram) for gram, count in top_ngrams]
    values = [count for gram, count in top_ngrams]
    plt.barh(labels, values, color='skyblue')
    plt.title(f"Top 10 {nazwa}", fontsize=12, fontweight='bold')
    plt.xlabel("Liczba wystąpień")
    plt.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plt.savefig(os.path.join(PLOTS_DIR, f"3a_top10_{nazwa.replace(' ', '_')}.png"), dpi=120)
    plt.show()


def print_top(counts, nazwa, n=10):
    print(f"\n--- Top {n} {nazwa} ---")
    for gram, count in counts.most_common(n):
        print(f"'{' '.join(gram)}': {count} razy")


def distribution_stats(counts, nazwa):
    total = sum(counts.values())
    unique = len(counts)
    hapax = sum(1 for c in counts.values() if c == 1)
    top10 = sum(c for _, c in counts.most_common(10))
    print(f"{nazwa:<10} wystąpień: {total:>7}  unikalnych: {unique:>7}  "
          f"jednokrotnych: {hapax / unique:6.1%}  "
          f"top10 pokrywa: {top10 / total:6.2%}  "
          f"max: {counts.most_common(1)[0][1]}")


def plot_rank_frequency(counters):
    # wykres ranga-częstość (log-log) - porównanie kształtu rozkładów
    plt.figure(figsize=(10, 6))
    for nazwa, counts in counters.items():
        freqs = sorted(counts.values(), reverse=True)
        plt.loglog(range(1, len(freqs) + 1), freqs, label=nazwa)
    plt.title("Rozkład ranga-częstość n-gramów", fontsize=12, fontweight='bold')
    plt.xlabel("Ranga (log)")
    plt.ylabel("Liczba wystąpień (log)")
    plt.legend()
    plt.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    plt.savefig(os.path.join(PLOTS_DIR, "3a_ranga_czestosc.png"), dpi=120)
    plt.show()


def tokenization(book, language):
    # zdania liczymy na tekście z interpunkcją - po czyszczeniu nie ma kropek
    sentences = nltk.sent_tokenize(book, language=language)
    sentences = [s for s in (clean_book(s) for s in sentences) if s]
    sentence_count = len(sentences)

    cleaned = clean_book(book)
    raw_tokens = nltk.word_tokenize(cleaned, language=language)
    words = [word for word in raw_tokens if word.isalnum()]
    word_count = len(words)

    print(f"Liczba zdań: {sentence_count}")
    print(f"Liczba wyrazów: {word_count}")
    return sentences, words


def analyze(words, stop_list):
    unigram_counts = Counter(ngrams(words, 1))
    bigram_counts = Counter(ngrams(words, 2))
    trigram_counts = Counter(ngrams(words, 3))

    print_top(unigram_counts, "unigramów")
    print_top(bigram_counts, "bigramów")
    print_top(trigram_counts, "trigramów")

    # bigramy/trigramy bez słów funkcyjnych - lepiej widać treść i styl autora
    stop = set(stop_list)
    content_bigrams = Counter({g: c for g, c in bigram_counts.items()
                               if not any(w in stop for w in g)})
    content_trigrams = Counter({g: c for g, c in trigram_counts.items()
                                if not all(w in stop for w in g)})
    print_top(content_bigrams, "bigramów bez stop words")
    print_top(content_trigrams, "trigramów (nie same stop words)", n=15)

    print("\n--- Porównanie rozkładów ---")
    distribution_stats(unigram_counts, "unigramy")
    distribution_stats(bigram_counts, "bigramy")
    distribution_stats(trigram_counts, "trigramy")

    plot_top_ngrams(unigram_counts, "unigram")
    plot_top_ngrams(bigram_counts, "bigram")
    plot_top_ngrams(trigram_counts, "trigram")
    plot_top_ngrams(content_bigrams, "bigram bez stop words")
    plot_rank_frequency({"unigramy": unigram_counts,
                         "bigramy": bigram_counts,
                         "trigramy": trigram_counts})


pan_tadeusz = read_book('books/pan-tadeusz.txt')
pan_tadeusz = strip_wolne_lektury(pan_tadeusz)
sentences, words = tokenization(pan_tadeusz, 'polish')
analyze(words, get_stop_words('polish'))

