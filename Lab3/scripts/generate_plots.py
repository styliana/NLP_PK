#!/usr/bin/env python3
"""
Wykresy PNG do sprawozdania z wyniki/benchmark_results.json (tylko prawdziwe pomiary).

1. skalowanie_zapytan.png        - 5.0: LIKE vs SQL FTS vs Solr dla 10/50/100% (Q1-Q3)
2. czasy_zapytan_porownanie.png  - Q1-Q3 na pełnym zbiorze
3. facety_vs_groupby.png         - 5.0: facety Solra vs GROUP BY
4. glebokie_stronicowanie.png    - rozszerzenie: start/rows vs cursorMark, OFFSET vs keyset
5. rozszerzenia_porownanie.png   - rozszerzenia: literówki i collapse
"""

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
from common import PLOTS_DIR, RESULTS_DIR  # noqa: E402

# Stałe kolory na system (ten sam system = ten sam kolor na każdym wykresie).
C_LIKE = "#eb6834"
C_PG = "#2a78d6"
C_SOLR = "#1baf7a"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "legend.frameon": False, "text.color": INK,
})


def save(fig, name):
    os.makedirs(PLOTS_DIR, exist_ok=True)
    path = os.path.join(PLOTS_DIR, name)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Zapisano {path}")


def bars(ax, groups, series, log=True):
    """Słupki pogrupowane; series = [(etykieta, kolor, [wartości], hatch)]."""
    width = 0.8 / len(series)
    for i, (label, color, values, hatch) in enumerate(series):
        xs = [g + (i - (len(series) - 1) / 2) * width for g in range(len(groups))]
        ax.bar(xs, values, width * 0.92, label=label, color=color, hatch=hatch,
               edgecolor="white" if not hatch else color, facecolor=color if not hatch else "white", linewidth=0.8)
        for x, v in zip(xs, values):
            ax.annotate(f"{v:.1f}" if v >= 10 else f"{v:.2f}", (x, v), xytext=(0, 2), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7, color=INK_2)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    if log:
        ax.set_yscale("log")


def plot_scaling(r):
    sc = r["scaling"]
    labels = list(sc.keys())
    recs = [sc[l]["records"] / 1000 for l in labels]
    queries = list(next(iter(sc.values()))["queries"].keys())
    fig, axes = plt.subplots(1, len(queries), figsize=(11, 3.6), sharey=True)
    for ax, q in zip(axes, queries):
        for label, color, key, ls in (("SQL LIKE '%…%'", C_LIKE, "like_ms", "-"),
                                      ("PostgreSQL FTS (GIN), ranking top-10", C_PG, "fts_top10_ms", "-"),
                                      ("PostgreSQL FTS (GIN), sam count(*)", C_PG, "fts_count_ms", "--"),
                                      ("Solr (bez cache wyników)", C_SOLR, "solr_client_ms", "-")):
            ys = [sc[l]["queries"][q][key] for l in labels]
            ax.plot(recs, ys, ls, color=color, lw=2, marker="o", ms=5, label=label)
            ax.annotate(f"{ys[-1]:.1f}" if ys[-1] >= 10 else f"{ys[-1]:.2f}", (recs[-1], ys[-1]),
                        xytext=(4, 0), textcoords="offset points", va="center", fontsize=7, color=INK_2)
        ax.set_title(r["queries"][q].get("short", q), loc="left", fontsize=9)
        ax.set_xticks(recs)
        ax.set_xticklabels([f"{l}\n{int(x)}k" for l, x in zip(labels, recs)])
        ax.set_yscale("log")
        ax.set_xlabel("wielkość zbioru [tys. rekordów]")
    axes[0].set_ylabel("czas zapytania [ms] (skala log.)")
    handles, lbls = axes[0].get_legend_handles_labels()
    fig.legend(handles, lbls, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.06))
    fig.suptitle("Skalowanie: czas zapytań dla 10%, 50% i 100% zbioru (mediana z 5)", y=1.12, fontweight="bold")
    save(fig, "skalowanie_zapytan.png")


def plot_queries(r):
    q = r["queries"]
    keys = list(q.keys())
    fig, ax = plt.subplots(figsize=(8, 4))
    bars(ax, keys, [
        ("SQL LIKE '%…%' (count)", C_LIKE, [q[k]["like"]["median_ms"] for k in keys], None),
        ("PostgreSQL FTS ranking top-10", C_PG, [q[k]["fts_top10_query"]["median_ms"] for k in keys], None),
        ("PostgreSQL FTS count(*)", C_PG, [q[k]["fts_count_query"]["median_ms"] for k in keys], "///"),
        ("Solr (bez cache wyników)", C_SOLR, [q[k]["solr"]["median_client_ms"] for k in keys], None),
    ])
    ax.set_ylabel("czas [ms] (skala log.)")
    ax.set_title(f"Zapytania Q1–Q3 na pełnym zbiorze ({r['records']:,} rekordów)".replace(",", " "), loc="left")
    ax.legend(loc="upper center", ncol=2, bbox_to_anchor=(0.5, -0.1))
    save(fig, "czasy_zapytan_porownanie.png")


def plot_facets(r):
    f = r["facets_vs_groupby"]
    keys = list(f.keys())
    names = ["Q1 (simulate)" if k == "Q1" else "cały zbiór (*:*)" for k in keys]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars(ax, names, log=False, series=[
        ("Solr: 1 zapytanie (2 facety + facet.range)", C_SOLR, [f[k]["solr"]["median_client_ms"] for k in keys], None),
        ("PostgreSQL: 3 zapytania GROUP BY", C_PG, [f[k]["sql_three_queries_ms"] for k in keys], None),
        ("PostgreSQL: 1 zapytanie GROUPING SETS", C_PG, [f[k]["sql_grouping_sets"]["median_ms"] for k in keys], "///"),
    ])
    ax.set_ylabel("czas [ms]")
    ax.set_title("Facety (field, category, zakres year) vs agregacje SQL", loc="left")
    ax.legend(loc="upper center", ncol=1, bbox_to_anchor=(0.5, -0.1))
    save(fig, "facety_vs_groupby.png")


def plot_deep_paging(r):
    p = r["ext_deep_paging"]
    xs = [max(d["position"], 1) for d in p]
    fig, ax = plt.subplots(figsize=(7, 4))
    for label, color, key, ls in (("Solr start/rows", C_SOLR, "solr_start_ms", "--"),
                                  ("Solr cursorMark", C_SOLR, "solr_cursor_ms", "-"),
                                  ("PostgreSQL OFFSET", C_PG, "sql_offset_ms", "--"),
                                  ("PostgreSQL keyset (id > x)", C_PG, "sql_keyset_ms", "-")):
        ys = [d[key] for d in p]
        ax.plot(xs, ys, ls, color=color, lw=2, marker="o", ms=5, label=label)
    ax.set_xscale("symlog", linthresh=1000)
    ax.set_yscale("log")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{d['position']:,}".replace(",", " ") for d in p], rotation=30)
    ax.set_xlabel("pozycja pierwszego wyniku na stronie")
    ax.set_ylabel("czas pobrania strony 10 wyników [ms]")
    ax.set_title("Głębokie stronicowanie", loc="left")
    ax.legend()
    save(fig, "glebokie_stronicowanie.png")


def plot_extensions(r):
    fz = r["ext_fuzzy"]
    c = r["ext_collapse"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4))
    typos = list(fz.keys())
    bars(a1, typos, log=False, series=[
        ("LIKE '%…%' (title)", C_LIKE, [fz[t]["like"]["median_ms"] for t in typos], None),
        ("pg_trgm  słowo <% title", C_PG, [fz[t]["pg_trgm"]["median_ms"] for t in typos], None),
        ("Solr fuzzy ~2", C_SOLR, [fz[t]["solr_fuzzy"]["median_client_ms"] for t in typos], None),
    ])
    for i, t in enumerate(typos):
        a1.annotate(f"wyniki: LIKE {fz[t]['like']['count']}, trgm {fz[t]['pg_trgm']['count']}, "
                    f"Solr {fz[t]['solr_fuzzy']['count']}", (i, 0), xytext=(0, -28), textcoords="offset points",
                    xycoords=("data", "axes fraction"), ha="center", fontsize=7, color=INK_2)
    a1.set_ylabel("czas [ms]")
    a1.set_title("Odporność na literówki", loc="left")
    a1.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.16))

    bars(a2, ["bez deduplikacji", "z deduplikacją"], log=False, series=[
        ("PostgreSQL (top-10 / DISTINCT ON)", C_PG,
         [c["sql_plain_top10"]["median_ms"], c["sql_distinct_on"]["median_ms"]], None),
        ("Solr (eDisMax / collapse)", C_SOLR,
         [c["solr_plain"]["median_client_ms"], c["solr_collapse"]["median_client_ms"]], None),
    ])
    a2.set_ylabel("czas [ms]")
    a2.set_title("Duplikaty po powieleniu: collapse po orig_id", loc="left")
    a2.legend(loc="upper center", ncol=2, bbox_to_anchor=(0.5, -0.1))
    save(fig, "rozszerzenia_porownanie.png")


def main():
    with open(os.path.join(RESULTS_DIR, "benchmark_results.json"), encoding="utf-8") as f:
        r = json.load(f)
    plot_scaling(r)
    plot_queries(r)
    plot_facets(r)
    plot_deep_paging(r)
    plot_extensions(r)


if __name__ == "__main__":
    main()
