"""Wykresy do sprawozdania Lab5 (PNG w katalogu wykresy/)."""

import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "wyniki"
OUT = ROOT / "wykresy"

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
METHOD_COLORS = {"mle": BLUE, "laplace": ORANGE, "kn": AQUA}
METHOD_LABELS = {"mle": "MLE", "laplace": "Laplace", "kn": "Kneser-Ney"}
LANGS = {"en": "angielski (Sherlock Holmes)", "pl": "polski (Lalka)"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": INK2,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
})


def read(name):
    with (RES / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def perplexity_plot():
    rows = read("perplexity.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    width = 0.26
    for ax, lang in zip(axes, LANGS):
        for j, method in enumerate(["mle", "laplace", "kn"]):
            for r in rows:
                if r["jezyk"] != lang or r["metoda"] != method:
                    continue
                n = int(r["n"])
                x = n + (j - 1) * width
                ppl = float(r["perplexity"])
                if math.isinf(ppl):
                    ax.text(x, 12, "∞", ha="center", va="bottom", color=INK, fontsize=12)
                else:
                    ax.bar(x, ppl, width=width - 0.03, color=METHOD_COLORS[method],
                           label=METHOD_LABELS[method] if n == 2 or (method == "mle" and n == 1) else None)
                    ax.text(x, ppl * 1.08, f"{ppl:.0f}", ha="center", va="bottom", fontsize=7, color=INK2)
        ax.set_yscale("log")
        ax.set_ylim(10, 10000)
        ax.set_xticks([1, 2, 3, 4])
        ax.set_xlabel("rząd modelu n")
        ax.set_title(LANGS[lang], color=INK, fontsize=11)
    axes[0].set_ylabel("perplexity (skala log.)")
    handles, labels = axes[0].get_legend_handles_labels()
    uniq = dict(zip(labels, handles))
    fig.legend(uniq.values(), uniq.keys(), loc="upper center", ncol=3, frameon=False)
    fig.text(0.5, 0.005, "∞ — MLE przypisuje zerowe prawdopodobieństwo niewidzianym n-gramom",
             ha="center", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 0.92))
    fig.savefig(OUT / "perplexity.png", dpi=160)
    plt.close(fig)


def copy_vs_size_plot():
    rows = [r for r in read("generowanie_proza.csv") if r["metoda"] == "mle"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ax, lang in zip(axes, LANGS):
        for n, color in [("2", ORANGE), ("3", BLUE)]:
            pts = [(int(r["czesc_tekstu"].rstrip("%")), float(r["copied_5gram"]) * 100)
                   for r in rows if r["jezyk"] == lang and r["n"] == n]
            pts.sort()
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, linewidth=2,
                    marker="o", markersize=7, markeredgecolor="white", label=f"MLE n={n}")
            ax.annotate(f"n={n}", (pts[-1][0], pts[-1][1]), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=8, color=INK2)
        ax.set_xticks([10, 50, 80, 100])
        ax.set_xlabel("część tekstu użyta do uczenia [%]")
        ax.set_title(LANGS[lang], color=INK, fontsize=11)
        ax.set_ylim(0, 100)
    axes[0].set_ylabel("skopiowane 5-gramy [%]")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(OUT / "kopiowanie_vs_ilosc_tekstu.png", dpi=160)
    plt.close(fig)


def poetry_copy_plot():
    rows = read("poezja_kopiowanie_zbiorczo.csv")
    labels = [f"{r['metoda']}, n={r['n']}" for r in rows]
    v5 = [float(r["copied_5gram"]) * 100 for r in rows]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    y = range(len(rows))
    ax.barh(list(y), v5, color=BLUE, height=0.6)
    for i, v in zip(y, v5):
        ax.text(v + 1, i, f"{v:.1f}%", va="center", fontsize=8, color=INK2)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 105)
    ax.set_xlabel("skopiowane 5-gramy słów [%] (5 wierszy łącznie)")
    ax.set_title("Poezja: odsetek 5-gramów obecnych w korpusie źródłowym", color=INK, fontsize=11)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(OUT / "poezja_kopiowanie.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    perplexity_plot()
    copy_vs_size_plot()
    poetry_copy_plot()
    print("Wykresy zapisane w", OUT)
