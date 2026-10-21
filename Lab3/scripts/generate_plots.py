#!/usr/bin/env python3
"""
Generator wykresów dla Laboratorium nr 3 (NLP: SQL kontra Solr).
Generuje wykresy w formacie PNG do katalogu wykresy/:
1. skalowanie_zapytan.png (Wymóg 5.0: LIKE vs FTS vs Solr dla 10%, 50%, 100%)
2. czasy_zapytan_porownanie.png (Porównanie czasów Q1, Q2, Q3)
3. facety_vs_groupby.png (Wymóg 5.0: Facety Solra vs GROUP BY w SQL)
4. rozszerzenia_porownanie.png (Wymóg 5.0: Rozszerzenie Fuzzy search i Collapsing)
"""

import os
import json
import matplotlib.pyplot as plt
import numpy as np

# Konfiguracja stylu
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 11


def load_results(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def plot_scaling(results, output_dir):
    scaling = results["scaling"]
    sizes_k = [50, 250, 500]  # tysiące rekordów
    like_times = [
        scaling["10% (50k)"]["sql_like_ms"],
        scaling["50% (250k)"]["sql_like_ms"],
        scaling["100% (500k)"]["sql_like_ms"]
    ]
    fts_times = [
        scaling["10% (50k)"]["sql_fts_ms"],
        scaling["50% (250k)"]["sql_fts_ms"],
        scaling["100% (500k)"]["sql_fts_ms"]
    ]
    solr_times = [
        scaling["10% (50k)"]["solr_ms"],
        scaling["50% (250k)"]["solr_ms"],
        scaling["100% (500k)"]["solr_ms"]
    ]

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)

    ax.plot(sizes_k, like_times, marker='o', linewidth=2.5, color='#d9534f', label="SQL LIKE '%...%' (skan sekwencyjny O(N))")
    ax.plot(sizes_k, fts_times, marker='s', linewidth=2.5, color='#337ab7', label="PostgreSQL FTS (indeks GIN O(log N))")
    ax.plot(sizes_k, solr_times, marker='^', linewidth=2.5, color='#5cb85c', label="Apache Solr 10 (odwrócony indeks Lucene)")

    # Etykiety punktów
    for x, y in zip(sizes_k, like_times):
        ax.annotate(f"{y:.1f} ms", (x, y), textcoords="offset points", xytext=(0, 8), ha='center', fontweight='bold', color='#d9534f')
    for x, y in zip(sizes_k, fts_times):
        ax.annotate(f"{y:.2f} ms", (x, y), textcoords="offset points", xytext=(0, -15), ha='center', fontweight='bold', color='#337ab7')
    for x, y in zip(sizes_k, solr_times):
        ax.annotate(f"{y:.2f} ms", (x, y), textcoords="offset points", xytext=(0, 8), ha='center', fontweight='bold', color='#5cb85c')

    ax.set_title("Skalowanie zapytań pełnotekstowych dla 10%, 50% i 100% danych (500k rekordów)", pad=15, fontweight='bold')
    ax.set_xlabel("Wielkość zbioru danych [tysiące rekordów]")
    ax.set_ylabel("Czas wykonania zapytania [ms]")
    ax.set_xticks(sizes_k)
    ax.set_xticklabels(["50k (10%)", "250k (50%)", "500k (100%)"])
    ax.legend(loc="upper left", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    out_file = os.path.join(output_dir, "skalowanie_zapytan.png")
    plt.savefig(out_file)
    plt.close()
    print(f"Wygenerowano wykres: {out_file}")


def plot_queries_comparison(results, output_dir):
    q1 = results["queries_3_0"]["Q1_stemming"]
    q2 = results["queries_3_0"]["Q2_phrase"]
    q3 = results["queries_3_0"]["Q3_boolean_negation"]

    categories = ["Q1: Stemming\n('perform')", "Q2: Fraza\n('machine learning')", "Q3: Negacja boolowska\n(A & (B | C) & !D)"]
    sql_fts = [q1["sql_fts"]["median_ms"], q2["sql_fts"]["median_ms"], q3["sql_fts"]["median_ms"]]
    solr_qtime = [q1["solr"]["qtime_ms"], q2["solr"]["qtime_ms"], q3["solr"]["qtime_ms"]]
    solr_client = [q1["solr"]["median_ms"], q2["solr"]["median_ms"], q3["solr"]["median_ms"]]

    x = np.arange(len(categories))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)

    rects1 = ax.bar(x - width, sql_fts, width, label='PostgreSQL 16 (FTS GIN)', color='#337ab7')
    rects2 = ax.bar(x, solr_qtime, width, label='Apache Solr 10 (QTime silnika)', color='#5cb85c')
    rects3 = ax.bar(x + width, solr_client, width, label='Apache Solr 10 (Klient HTTP)', color='#f0ad4e')

    # Dodanie etykiet słupków
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.2f} ms' if height < 10 else f'{height:.1f} ms',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)

    ax.set_title("Porównanie czasów wykonania zapytań (mediana z 5 prób, zbiór 500k rekordów)", pad=15, fontweight='bold')
    ax.set_ylabel("Czas wykonania [ms]")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6, axis='y')

    plt.tight_layout()
    out_file = os.path.join(output_dir, "czasy_zapytan_porownanie.png")
    plt.savefig(out_file)
    plt.close()
    print(f"Wygenerowano wykres: {out_file}")


def plot_facets_vs_groupby(results, output_dir):
    fg = results["facets_vs_groupby"]
    labels = ["Category GROUP BY", "Tag GROUP BY", "Rating Range GROUP BY", "SQL GROUP BY (Suma)", "Solr Facets (Wszystko w 1)"]
    times = [
        fg["sql_groupby"]["category_ms"],
        fg["sql_groupby"]["tag_ms"],
        fg["sql_groupby"]["rating_range_ms"],
        fg["sql_groupby"]["total_sql_ms"],
        fg["solr_facets"]["median_client_ms"]
    ]
    colors = ['#5bc0de', '#5bc0de', '#5bc0de', '#d9534f', '#5cb85c']

    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    bars = ax.barh(labels, times, color=colors, height=0.6)

    for bar, val in zip(bars, times):
        ax.text(val + 5, bar.get_y() + bar.get_height() / 2, f"{val:.1f} ms",
                va='center', ha='left', fontweight='bold', fontsize=10)

    ax.set_xlim(0, max(times) * 1.15)
    ax.set_xlabel("Czas wykonania zapytania [ms]")
    ax.set_title("Wydajnosc agregacji: Solr Facets (1 zapytanie) vs PostgreSQL GROUP BY", pad=15, fontweight='bold', fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.6, axis='x')

    # Adnotacja o przewadze
    ax.text(0.70, 0.20, f"Przyspieszenie Solra:\n{fg['speedup_factor']:.1f}x szybciej!",
            transform=ax.transAxes, fontsize=12, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#dff0d8", edgecolor="#5cb85c"))

    plt.tight_layout()
    out_file = os.path.join(output_dir, "facety_vs_groupby.png")
    plt.savefig(out_file)
    plt.close()
    print(f"Wygenerowano wykres: {out_file}")


def plot_extensions(results, output_dir):
    ext1 = results["extensions"]["extension_1_fuzzy"]
    ext2 = results["extensions"]["extension_2_collapse"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), dpi=300)

    # Wykres 1: Fuzzy Search
    fuzzy_labels = ["LIKE '%...%'\n(0 trafień)", "PostgreSQL\npg_trgm", "Apache Solr\nFuzzy (~)"]
    fuzzy_times = [ext1["sql_like"]["time_ms"], ext1["sql_pg_trgm"]["time_ms"], ext1["solr_fuzzy"]["time_ms"]]
    ax1.bar(fuzzy_labels, fuzzy_times, color=['#d9534f', '#337ab7', '#5cb85c'], width=0.55)
    for i, v in enumerate(fuzzy_times):
        ax1.text(i, v + 4, f"{v:.1f} ms", ha='center', fontweight='bold')
    ax1.set_title("Rozszerzenie 1: Odporność na literówki\n('machne lerning')", fontweight='bold')
    ax1.set_ylabel("Czas wykonania [ms]")
    ax1.grid(True, linestyle="--", alpha=0.6, axis='y')

    # Wykres 2: Collapsing duplikatów
    col_labels = ["PostgreSQL\nDISTINCT ON / ROW_NUM", "Apache Solr\n{!collapse}"]
    col_times = [ext2["sql_distinct_on"]["time_ms"], ext2["solr_collapse"]["time_ms"]]
    ax2.bar(col_labels, col_times, color=['#337ab7', '#5cb85c'], width=0.45)
    for i, v in enumerate(col_times):
        ax2.text(i, v + 2, f"{v:.1f} ms", ha='center', fontweight='bold')
    ax2.set_title("Rozszerzenie 2: Deduplikacja w Top-10\n(Collapsing po orig_id)", fontweight='bold')
    ax2.set_ylabel("Czas wykonania [ms]")
    ax2.grid(True, linestyle="--", alpha=0.6, axis='y')

    plt.tight_layout()
    out_file = os.path.join(output_dir, "rozszerzenia_porownanie.png")
    plt.savefig(out_file)
    plt.close()
    print(f"Wygenerowano wykres: {out_file}")


def main():
    base_dir = os.path.dirname(__file__)
    json_path = os.path.join(base_dir, "..", "wyniki", "benchmark_results.json")
    out_dir = os.path.join(base_dir, "..", "wykresy")
    os.makedirs(out_dir, exist_ok=True)

    results = load_results(json_path)
    plot_scaling(results, out_dir)
    plot_queries_comparison(results, out_dir)
    plot_facets_vs_groupby(results, out_dir)
    plot_extensions(results, out_dir)


if __name__ == "__main__":
    main()
