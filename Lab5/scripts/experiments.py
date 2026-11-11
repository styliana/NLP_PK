"""Wszystkie eksperymenty Lab5 (poziomy 3.0, 4.0 i 5.0).

3.0  MLE n=1,2,3 dla PL i EN, 100 słów, 10/50/80/100% tekstu
4.0  Laplace i Kneser-Ney (n=2,3), perplexity 90/10, temperatura i top-k
5.0  poezja (Quebonafide, Taco Hemingway, Jan-rapowanie): model słowny,
     znakowy i markovify; odsetek skopiowanych 5- i 6-gramów słów
"""

from __future__ import annotations

import csv
import json
import math
import random
import time
from pathlib import Path

import markovify
import numpy as np

from ngram_lm import EOS, NgramLM, apply_vocab, build_vocab, generate, generate_unit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
GEN = ROOT / "wygenerowane"
RES = ROOT / "wyniki"

RANDOM_SEED = 42
N_WORDS = 100
PORTIONS = [10, 50, 80, 100]
COPY_NS = [4, 5, 6]
# seed musi występować w tekście — także w pierwszych 10% (sprawdzane w kodzie)
SEEDS = {"en": ["sherlock", "holmes"], "pl": ["pan", "ignacy"]}
LANG_NAMES = {"en": "angielski (A. C. Doyle, The Adventures of Sherlock Holmes)",
              "pl": "polski (B. Prus, Lalka, t. I)"}
TEMPERATURES = [0.5, 1.0, 1.5]
TOP_KS = [3, 10, 50]
ARTIST_NAMES = {"quebonafide": "Quebonafide", "taco_hemingway": "Taco Hemingway",
                "jan_rapowanie": "Jan-rapowanie"}

NO_SPACE_BEFORE = set(".,!?;:)]}…%»”")
NO_SPACE_AFTER = set("([{„«“")


def is_word(token: str) -> bool:
    return any(ch.isalnum() for ch in token)


def detokenize(tokens: list[str]) -> str:
    out = ""
    for tok in tokens:
        if not out or out.endswith("\n") or tok in NO_SPACE_BEFORE or out[-1] in NO_SPACE_AFTER:
            out += tok
        else:
            out += " " + tok
    return out


def split_units(tokens: list[str]) -> list[list[str]]:
    units, cur = [], []
    for t in tokens:
        if t == EOS:
            if cur:
                units.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        units.append(cur)
    return units


def render(tokens: list[str]) -> str:
    """Tekst z </s> zamienionym na podział akapitu po każdym zdaniu."""
    return "\n".join(detokenize(u) for u in split_units(tokens))


# -------------------------------------------------------- skopiowane n-gramy
def ngram_set(units: list[list[str]], n: int) -> set[tuple]:
    s = set()
    for u in units:
        for i in range(len(u) - n + 1):
            s.add(tuple(u[i : i + n]))
    return s


def copied_ratio(units: list[list[str]], source: set[tuple], n: int) -> tuple[float, int]:
    grams = [tuple(u[i : i + n]) for u in units for i in range(len(u) - n + 1)]
    if not grams:
        return math.nan, 0
    return sum(g in source for g in grams) / len(grams), len(grams)


def longest_copied_span(units: list[list[str]], source_sets: dict[int, set]) -> int:
    best = 0
    max_n = max(source_sets)
    for u in units:
        for i in range(len(u)):
            for n in range(max(best + 1, 1), min(max_n, len(u) - i) + 1):
                if tuple(u[i : i + n]) in source_sets[n]:
                    best = n
                else:
                    break
    return best


class CopyChecker:
    """Zbiory n-gramów tekstu źródłowego (w obrębie zdań/wersów) do mierzenia kopiowania."""

    def __init__(self, units: list[list[str]], max_n: int = 12):
        self.sets = {n: ngram_set(units, n) for n in range(1, max_n + 1)}

    def measure(self, units: list[list[str]]) -> dict:
        row = {}
        for n in COPY_NS:
            ratio, total = copied_ratio(units, self.sets[n], n)
            row[f"copied_{n}gram"] = ratio
            row[f"total_{n}gram"] = total
        row["longest_copied_span"] = longest_copied_span(units, self.sets)
        return row


def header(**meta) -> str:
    parts = [f"{k}: {v}" for k, v in meta.items()]
    return "# " + " | ".join(parts) + "\n\n"


def write_csv(path: Path, rows: list[dict]) -> None:
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


# ------------------------------------------------------------------- proza
def prose_generation(lang: str, sentences: list[list[str]]) -> list[dict]:
    rows = []
    seed = SEEDS[lang]
    out_dir = GEN / "proza"
    out_dir.mkdir(parents=True, exist_ok=True)
    for pct in PORTIONS:
        part = sentences[: round(len(sentences) * pct / 100)]
        joined = [" ".join(s) for s in part]
        assert any(" ".join(seed) in s for s in joined), f"seed {seed} nie występuje w {pct}% tekstu"
        checker = CopyChecker(part)
        configs = [("mle", n) for n in (1, 2, 3)]
        if pct == 100:
            configs += [(m, n) for m in ("laplace", "kn") for n in (2, 3)]
        for method, n in configs:
            model = NgramLM(n, method).fit(part)
            model_seed = seed[-(n - 1) :] if n > 1 else []
            tokens = generate(model, model_seed, N_WORDS, RANDOM_SEED)
            # seed jest częścią wyniku tylko dla n>1; dla n=1 zapisujemy go w nagłówku
            name = f"{lang}_n{n}_{pct}proc.txt" if method == "mle" else f"{lang}_{method}_n{n}_{pct}proc.txt"
            meta = dict(jezyk=lang, metoda=method, n=n, czesc_tekstu=f"{pct}%", seed=" ".join(seed),
                        seed_uzyty=" ".join(model_seed) or "(brak — unigram nie korzysta z kontekstu)",
                        random_seed=RANDOM_SEED, temperatura=1.0, top_k="brak", slow=N_WORDS)
            text = render(tokens)
            (out_dir / name).write_text(header(**meta) + text + "\n", encoding="utf-8")
            row = dict(meta, plik=f"proza/{name}", **checker.measure(split_units(tokens)))
            row["sentences_generated"] = len(split_units(tokens))
            rows.append(row)
            print(f"  {name}")
    return rows


def perplexity_table(lang: str, sentences: list[list[str]]) -> tuple[list[dict], dict]:
    cut = round(len(sentences) * 0.9)
    train_raw, test_raw = sentences[:cut], sentences[cut:]
    vocab = build_vocab(train_raw, min_count=2)
    train, test = apply_vocab(train_raw, vocab), apply_vocab(test_raw, vocab)
    oov = sum(t == "<unk>" for s in test for t in s) / sum(len(s) for s in test)
    info = {"train_sentences": len(train), "test_sentences": len(test), "vocab_size": len(vocab) + 2,
            "test_oov_rate": oov}
    rows = []
    for method, ns in [("mle", [1, 2, 3, 4]), ("laplace", [1, 2, 3, 4]), ("kn", [2, 3, 4])]:
        for n in ns:
            t0 = time.perf_counter()
            model = NgramLM(n, method).fit(train)
            r = model.perplexity(test)
            rows.append({"jezyk": lang, "metoda": method, "n": n, "perplexity": r["perplexity"],
                         "tokeny_testowe": r["tokens"], "tokeny_p0": r["zero_prob_tokens"],
                         "odsetek_p0": r["zero_prob_tokens"] / r["tokens"],
                         "czas_s": round(time.perf_counter() - t0, 2)})
            print(f"  PPL {lang} {method} n={n}: {r['perplexity']:.2f} (p=0: {r['zero_prob_tokens']})")

    # dobór dyskonta KN na zbiorze walidacyjnym (80–90% tekstu), bez zaglądania do testu
    dev_cut = round(len(sentences) * 0.8)
    dev_vocab = build_vocab(sentences[:dev_cut], 2)
    dev_train = apply_vocab(sentences[:dev_cut], dev_vocab)
    dev = apply_vocab(sentences[dev_cut:cut], dev_vocab)
    discounts = []
    for D in [0.3, 0.5, 0.75, 0.9, 1.0]:
        ppl = NgramLM(3, "kn", discount=D).fit(dev_train).perplexity(dev)["perplexity"]
        discounts.append({"jezyk": lang, "D": D, "dev_perplexity": ppl})
    info["kn_discount_search"] = discounts
    best_D = min(discounts, key=lambda r: r["dev_perplexity"])["D"]
    info["best_D"] = best_D
    if best_D != 0.75:
        ppl = NgramLM(3, "kn", discount=best_D).fit(train).perplexity(test)["perplexity"]
        info["kn3_bestD_test_perplexity"] = ppl
    return rows, info


def sampling_experiment(lang: str, sentences: list[list[str]], method: str, n: int) -> list[dict]:
    out_dir = GEN / "losowanie"
    out_dir.mkdir(parents=True, exist_ok=True)
    model = NgramLM(n, method).fit(sentences)
    checker = CopyChecker(sentences)
    seed = SEEDS[lang][-(n - 1) :]
    rows = []
    settings = [("temperatura", t, dict(temperature=t)) for t in TEMPERATURES]
    settings += [("top_k", k, dict(top_k=k)) for k in TOP_KS]
    for kind, value, kw in settings:
        tokens = generate(model, seed, N_WORDS, RANDOM_SEED, **kw)
        name = f"{lang}_{method}_n{n}_{kind}_{value}.txt"
        meta = dict(jezyk=lang, metoda=method, n=n, czesc_tekstu="100%", seed=" ".join(seed),
                    random_seed=RANDOM_SEED, temperatura=kw.get("temperature", 1.0),
                    top_k=kw.get("top_k", "brak"), slow=N_WORDS)
        (out_dir / name).write_text(header(**meta) + render(tokens) + "\n", encoding="utf-8")
        units = split_units(tokens)
        words = [t for u in units for t in u]
        row = dict(meta, plik=f"losowanie/{name}", strategia=kind, wartosc=value, **checker.measure(units))
        row["unikalne_tokeny"] = len(set(words)) / len(words)
        row["sr_dl_zdania"] = float(np.mean([len(u) for u in units]))
        rows.append(row)
        print(f"  {name}")
    return rows


# ------------------------------------------------------------------ poezja
POEM_SEEDS = ["ja", "życie", "miasto", "noc", "znowu"]
POEM_RANDOM_SEEDS = [101, 202, 303, 404, 505]


def poem_lengths() -> list[int]:
    rng = np.random.default_rng(RANDOM_SEED)
    return [int(x) for x in rng.integers(4, 9, size=5)]


def word_poems(lines, n, method="kn", temperature=1.0, top_k=None):
    model = NgramLM(n, method).fit(lines)
    poems = []
    for seed_word, rs, length in zip(POEM_SEEDS, POEM_RANDOM_SEEDS, poem_lengths()):
        rng = np.random.default_rng(rs)
        verses = []
        for i in range(length):
            verse = []
            while len(verse) < 3:  # pomijamy zbyt krótkie wersy (np. pojedynczy wykrzyknik)
                verse = generate_unit(model, rng, seed=[seed_word] if i == 0 else [],
                                      temperature=temperature, top_k=top_k, max_len=25)
            verses.append(verse)
        poems.append({"seed": seed_word, "random_seed": rs, "verses": verses})
    return poems


def char_poems(char_lines, n, temperature=1.0):
    model = NgramLM(n, "kn").fit(char_lines)
    poems = []
    for seed_word, rs, length in zip(POEM_SEEDS, POEM_RANDOM_SEEDS, poem_lengths()):
        rng = np.random.default_rng(rs)
        verses = []
        for i in range(length):
            chars = []
            while len("".join(chars).split()) < 3:
                chars = generate_unit(model, rng, seed=list(seed_word + " ") if i == 0 else [],
                                      temperature=temperature, max_len=120)
            verses.append("".join(chars))
        poems.append({"seed": seed_word, "random_seed": rs, "verses": verses})
    return poems


def markovify_poems(text_lines, state_size):
    model = markovify.NewlineText("\n".join(text_lines), state_size=state_size)
    poems = []
    for seed_word, rs, length in zip(POEM_SEEDS, POEM_RANDOM_SEEDS, poem_lengths()):
        random.seed(rs)
        verses = []
        for i in range(length):
            verse = None
            if i == 0:
                try:
                    verse = model.make_sentence_with_start(seed_word, strict=False, tries=200)
                except (KeyError, markovify.text.ParamError):
                    verse = None
            while verse is None:
                verse = model.make_sentence(tries=200)
            verses.append(verse)
        poems.append({"seed": seed_word, "random_seed": rs, "verses": verses})
    return poems


def poetry_experiment(poetry: dict) -> tuple[list[dict], list[dict]]:
    from preprocess import tokenize

    out_dir = GEN / "poezja"
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [l for a in poetry.values() for l in a["lines"]]
    text_lines = [detokenize(l) for l in lines]
    char_lines = [list(t) for t in text_lines]
    checker = CopyChecker(lines)

    configs = [("słowny MLE", "word_mle", 2, lambda: word_poems(lines, 2, "mle")),
               ("słowny MLE", "word_mle", 3, lambda: word_poems(lines, 3, "mle")),
               ("słowny Kneser-Ney", "word_kn", 2, lambda: word_poems(lines, 2, "kn")),
               ("słowny Kneser-Ney", "word_kn", 3, lambda: word_poems(lines, 3, "kn")),
               ("słowny Kneser-Ney", "word_kn", 4, lambda: word_poems(lines, 4, "kn")),
               ("słowny Kneser-Ney T=0.7", "word_kn_T0.7", 3,
                lambda: word_poems(lines, 3, "kn", temperature=0.7)),
               ("słowny Kneser-Ney top-k=10", "word_kn_top10", 3,
                lambda: word_poems(lines, 3, "kn", top_k=10)),
               ("znakowy Kneser-Ney", "char_kn", 5, lambda: char_poems(char_lines, 5)),
               ("znakowy Kneser-Ney", "char_kn", 7, lambda: char_poems(char_lines, 7)),
               ("znakowy Kneser-Ney", "char_kn", 9, lambda: char_poems(char_lines, 9)),
               ("markovify", "markovify", 2, lambda: markovify_poems(text_lines, 2)),
               ("markovify", "markovify", 3, lambda: markovify_poems(text_lines, 3))]
    rows, all_poems = [], []
    for label, key, n, fn in configs:
        poems = fn()
        name = f"{key}_n{n}.txt"
        chunks = []
        for i, poem in enumerate(poems, 1):
            verses = [v if isinstance(v, str) else detokenize(v) for v in poem["verses"]]
            temp = 0.7 if "T=0.7" in label else 1.0
            topk = 10 if "top-k" in label else "brak"
            meta = dict(wiersz=i, metoda=label, n=n, seed=poem["seed"], random_seed=poem["random_seed"],
                        temperatura=temp, top_k=topk, wersy=len(verses))
            chunks.append(header(**meta) + "\n".join(verses))
            units = [tokenize(v) for v in verses]
            row = dict(meta, plik=f"poezja/{name}", **checker.measure(units))
            rows.append(row)
            all_poems.append(dict(meta, plik=f"poezja/{name}", verses=verses))
        (out_dir / name).write_text("\n\n".join(chunks) + "\n", encoding="utf-8")
        print(f"  {name}")
    return rows, all_poems


def aggregate(rows: list[dict], keys: list[str]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault(tuple(r[k] for k in keys), []).append(r)
    out = []
    for g, rs in groups.items():
        row = dict(zip(keys, g))
        for n in COPY_NS:
            num = sum(r[f"copied_{n}gram"] * r[f"total_{n}gram"] for r in rs if r[f"total_{n}gram"])
            den = sum(r[f"total_{n}gram"] for r in rs)
            row[f"copied_{n}gram"] = num / den if den else math.nan
        row["longest_copied_span_max"] = max(r["longest_copied_span"] for r in rs)
        out.append(row)
    return out


def main() -> None:
    RES.mkdir(parents=True, exist_ok=True)
    summary = json.loads((DATA / "summary.json").read_text(encoding="utf-8"))
    prose_rows, ppl_rows, sampling_rows, ppl_info, best = [], [], [], {}, {}
    for lang in ["en", "pl"]:
        sentences = json.loads((DATA / f"{lang}.json").read_text(encoding="utf-8"))
        print(f"[{lang}] generowanie")
        prose_rows += prose_generation(lang, sentences)
        print(f"[{lang}] perplexity")
        rows, info = perplexity_table(lang, sentences)
        ppl_rows += rows
        ppl_info[lang] = info
        # najlepszy model spośród wymaganych (n=2,3) — najniższa perplexity
        candidates = [r for r in rows if r["n"] in (2, 3) and math.isfinite(r["perplexity"])]
        b = min(candidates, key=lambda r: r["perplexity"])
        best[lang] = {"metoda": b["metoda"], "n": b["n"], "perplexity": b["perplexity"]}
        print(f"[{lang}] losowanie dla {b['metoda']} n={b['n']}")
        sampling_rows += sampling_experiment(lang, sentences, b["metoda"], b["n"])

    poetry = json.loads((DATA / "poetry.json").read_text(encoding="utf-8"))
    print("[poezja]")
    poem_rows, poems = poetry_experiment(poetry)

    write_csv(RES / "generowanie_proza.csv", prose_rows)
    write_csv(RES / "perplexity.csv", ppl_rows)
    write_csv(RES / "losowanie.csv", sampling_rows)
    write_csv(RES / "poezja_kopiowanie.csv", poem_rows)
    write_csv(RES / "poezja_kopiowanie_zbiorczo.csv", aggregate(poem_rows, ["metoda", "n"]))
    (RES / "wyniki.json").write_text(json.dumps({
        "data_summary": summary, "perplexity_info": ppl_info, "best_models": best,
        "prose": prose_rows, "perplexity": ppl_rows, "sampling": sampling_rows,
        "poems": poems, "poem_copy": poem_rows,
        "poem_copy_aggregate": aggregate(poem_rows, ["metoda", "n"]),
        "random_seed": RANDOM_SEED, "seeds": SEEDS, "poem_seeds": POEM_SEEDS,
        "poem_random_seeds": POEM_RANDOM_SEEDS,
    }, ensure_ascii=False, indent=1, default=lambda x: None), encoding="utf-8")
    print("Gotowe.")


if __name__ == "__main__":
    main()
