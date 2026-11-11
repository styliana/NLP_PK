"""Własna implementacja n-gramowego modelu języka.

Obsługiwane metody estymacji:

* ``mle``     — największa wiarygodność, P(w|h) = c(h,w) / c(h),
* ``laplace`` — wygładzanie add-one, P(w|h) = (c(h,w) + 1) / (c(h) + |V|),
* ``kn``      — interpolowany Kneser-Ney z dyskontem absolutnym D.

Model jest niezależny od rodzaju tokenów: dla modelu słownego tokenami są słowa
i znaki interpunkcyjne, dla modelu znakowego — pojedyncze znaki.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Iterable, Sequence

import numpy as np

BOS = "<s>"
EOS = "</s>"
UNK = "<unk>"


class NgramLM:
    def __init__(self, order: int, method: str = "mle", discount: float = 0.75):
        if order < 1:
            raise ValueError("order musi być >= 1")
        if method not in {"mle", "laplace", "kn"}:
            raise ValueError(f"Nieznana metoda: {method}")
        self.n = order
        self.method = method
        self.discount = discount

    # ------------------------------------------------------------------ uczenie
    def pad(self, sentence: Sequence[str]) -> list[str]:
        return [BOS] * (self.n - 1) + list(sentence) + [EOS]

    def fit(self, sentences: Iterable[Sequence[str]]) -> "NgramLM":
        n = self.n
        # counts[k][(h, w)] — liczba wystąpień k-gramu; h to krotka długości k-1
        self.counts: list[dict[tuple, Counter]] = [None] + [defaultdict(Counter) for _ in range(n)]
        for sentence in sentences:
            tokens = self.pad(sentence)
            for i in range(n - 1, len(tokens)):
                for k in range(1, n + 1):
                    h = tuple(tokens[i - k + 1 : i])
                    self.counts[k][h][tokens[i]] += 1

        vocab = set(self.counts[1][()])
        vocab.discard(BOS)
        self.vocab = sorted(vocab)
        self.index = {w: i for i, w in enumerate(self.vocab)}
        self.V = len(self.vocab)
        self.ctx_total = [None] + [
            {h: sum(c.values()) for h, c in self.counts[k].items()} for k in range(1, n + 1)
        ]

        if self.method == "kn":
            # liczby kontynuacji N1+(• h w): ile różnych słów poprzedza (h, w)
            self.cont: list[dict[tuple, Counter]] = [None] + [defaultdict(Counter) for _ in range(n)]
            for k in range(2, n + 1):
                for h, followers in self.counts[k].items():
                    lower_h = h[1:]
                    for w in followers:
                        self.cont[k - 1][lower_h][w] += 1
            self.cont_total = [None] + [
                {h: sum(c.values()) for h, c in self.cont[k].items()} for k in range(1, n)
            ]
        return self

    # --------------------------------------------------------- prawdopodobieństwo
    def _table(self, k: int):
        """Tablica liczności używana na poziomie k (zwykłe albo kontynuacji)."""
        if self.method == "kn" and k < self.n:
            return self.cont[k], self.cont_total[k]
        return self.counts[k], self.ctx_total[k]

    def prob(self, word: str, context: Sequence[str]) -> float:
        context = tuple(context)[-(self.n - 1) :] if self.n > 1 else ()
        if len(context) < self.n - 1:
            context = (BOS,) * (self.n - 1 - len(context)) + context
        if self.method == "mle":
            total = self.ctx_total[self.n].get(context, 0)
            return self.counts[self.n][context][word] / total if total else 0.0
        if self.method == "laplace":
            total = self.ctx_total[self.n].get(context, 0)
            c = self.counts[self.n][context].get(word, 0) if total else 0
            return (c + 1) / (total + self.V)
        return self._kn(word, context, self.n)

    def _kn(self, word: str, context: tuple, k: int) -> float:
        D = self.discount
        table, totals = self._table(k)
        h = context[len(context) - (k - 1) :] if k > 1 else ()
        total = totals.get(h, 0)
        if k == 1:
            # najniższy poziom: prawdopodobieństwo kontynuacji interpolowane z rozkładem jednostajnym
            c = table[()].get(word, 0)
            return max(c - D, 0) / total + D * len(table[()]) / total / self.V
        if total == 0:
            return self._kn(word, context, k - 1)
        followers = table[h]
        c = followers.get(word, 0)
        lam = D * len(followers) / total
        return max(c - D, 0) / total + lam * self._kn(word, context, k - 1)

    def distribution(self, context: Sequence[str]) -> np.ndarray:
        """Pełny rozkład P(·|h) nad słownikiem (wektor numpy, suma = 1)."""
        context = tuple(context)[-(self.n - 1) :] if self.n > 1 else ()
        if self.method == "kn":
            return self._kn_vector(context, self.n)
        if self.n == 1:
            if getattr(self, "_unigram_cache", None) is None:
                self._unigram_cache = self._count_vector(())
            return self._unigram_cache
        return self._count_vector(context)

    def _count_vector(self, context: tuple) -> np.ndarray:
        total = self.ctx_total[self.n].get(context, 0)
        p = np.zeros(self.V)
        followers = self.counts[self.n].get(context, {})
        for w, c in followers.items():
            p[self.index[w]] = c
        if self.method == "laplace":
            p = (p + 1) / (total + self.V)
        elif total:
            p /= total
        return p

    def _kn_vector(self, context: tuple, k: int) -> np.ndarray:
        if k == 1:
            # rozkład najniższego rzędu nie zależy od kontekstu — liczymy go raz
            if getattr(self, "_unigram_cache", None) is None:
                self._unigram_cache = self._kn_vector_level(context, 1)
            return self._unigram_cache
        return self._kn_vector_level(context, k)

    def _kn_vector_level(self, context: tuple, k: int) -> np.ndarray:
        D = self.discount
        table, totals = self._table(k)
        h = context[len(context) - (k - 1) :] if k > 1 else ()
        total = totals.get(h, 0)
        if k > 1 and total == 0:
            return self._kn_vector(context, k - 1)
        followers = table[h]
        p = np.zeros(self.V)
        for w, c in followers.items():
            if w in self.index:
                p[self.index[w]] = max(c - D, 0) / total
        lam = D * len(followers) / total
        lower = np.full(self.V, 1.0 / self.V) if k == 1 else self._kn_vector(context, k - 1)
        return p + lam * lower

    # ---------------------------------------------------------------- ewaluacja
    def perplexity(self, sentences: Iterable[Sequence[str]]) -> dict:
        log_sum = 0.0
        tokens = 0
        zero = 0
        for sentence in sentences:
            padded = self.pad(sentence)
            for i in range(self.n - 1, len(padded)):
                p = self.prob(padded[i], padded[i - self.n + 1 : i] if self.n > 1 else ())
                tokens += 1
                if p <= 0:
                    zero += 1
                else:
                    log_sum += math.log2(p)
        ppl = math.inf if zero else 2 ** (-log_sum / tokens)
        return {"perplexity": ppl, "tokens": tokens, "zero_prob_tokens": zero}


# ------------------------------------------------------------------ słownik <unk>
def build_vocab(sentences: Iterable[Sequence[str]], min_count: int = 2) -> set[str]:
    counter = Counter(t for s in sentences for t in s)
    return {w for w, c in counter.items() if c >= min_count}


def apply_vocab(sentences: Iterable[Sequence[str]], vocab: set[str]) -> list[list[str]]:
    return [[t if t in vocab else UNK for t in s] for s in sentences]


# ---------------------------------------------------------------------- losowanie
def sample_next(
    model: NgramLM,
    context: Sequence[str],
    rng: np.random.Generator,
    temperature: float = 1.0,
    top_k: int | None = None,
    banned: Iterable[str] = (UNK,),
) -> str:
    p = model.distribution(context).copy()
    for w in banned:
        if w in model.index:
            p[model.index[w]] = 0.0
    if p.sum() <= 0:
        raise ValueError(f"Brak kontynuacji dla kontekstu {tuple(context)}")
    if top_k is not None and top_k < np.count_nonzero(p):
        keep = np.argsort(-p, kind="stable")[:top_k]
        mask = np.zeros_like(p, dtype=bool)
        mask[keep] = True
        p = np.where(mask, p, 0.0)
    if temperature != 1.0:
        nz = p > 0
        logp = np.full_like(p, -np.inf)
        logp[nz] = np.log(p[nz]) / temperature
        logp -= logp[nz].max()
        p = np.exp(logp)
    p /= p.sum()
    return model.vocab[rng.choice(model.V, p=p)]


def generate(
    model: NgramLM,
    seed: Sequence[str],
    n_words: int,
    random_seed: int,
    temperature: float = 1.0,
    top_k: int | None = None,
    is_word=lambda t: any(ch.isalnum() for ch in t),
) -> list[str]:
    """Generuje ``n_words`` kolejnych słów (tokeny interpunkcyjne i </s> nie są liczone).

    Wynik zawiera seed na początku; granice zdań oznaczone są tokenem ``</s>``.
    Po wylosowaniu ``</s>`` kontekst jest zerowany do ``<s> ... <s>``.
    """
    rng = np.random.default_rng(random_seed)
    history = [BOS] * (model.n - 1) + list(seed)
    out = list(seed)
    words = 0
    while words < n_words:
        token = sample_next(model, history[-(model.n - 1) :] if model.n > 1 else (), rng, temperature, top_k)
        out.append(token)
        if token == EOS:
            history = [BOS] * (model.n - 1)
            continue
        history.append(token)
        if is_word(token):
            words += 1
    return out


def generate_unit(
    model: NgramLM,
    rng: np.random.Generator,
    seed: Sequence[str] = (),
    temperature: float = 1.0,
    top_k: int | None = None,
    max_len: int = 200,
) -> list[str]:
    """Generuje jedną jednostkę (zdanie / wers) od <s> do </s>."""
    history = [BOS] * (model.n - 1) + list(seed)
    out = list(seed)
    while len(out) < max_len:
        token = sample_next(model, history[-(model.n - 1) :] if model.n > 1 else (), rng, temperature, top_k)
        if token == EOS:
            break
        out.append(token)
        history.append(token)
    return out
