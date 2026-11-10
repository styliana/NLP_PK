"""Generate result-summary plots from the saved model evaluation table."""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "wyniki" / "all_results.csv"
OUTPUT_DIR = ROOT / "wykresy"
METHODS = ("RandomizedSearchCV", "GridSearchCV")


def load_results() -> list[dict[str, str]]:
    with RESULTS_PATH.open(encoding="utf-8", newline="") as input_file:
        rows = list(csv.DictReader(input_file))
    if not rows:
        raise ValueError(f"No experiment results found in {RESULTS_PATH}")
    return rows


def save_search_heatmaps(rows: list[dict[str, str]]) -> None:
    representations = list(dict.fromkeys(row["representation"] for row in rows))
    classifiers = list(dict.fromkeys(row["classifier"] for row in rows))
    fig, axes = plt.subplots(1, 2, figsize=(18, 7), constrained_layout=True)
    for axis, method in zip(axes, METHODS):
        selected = [row for row in rows if row["method"] == method]
        scores = {
            (row["classifier"], row["representation"]): float(row["f1"])
            for row in selected
        }
        matrix = np.asarray(
            [
                [scores[(classifier, representation)] for representation in representations]
                for classifier in classifiers
            ]
        )
        image = axis.imshow(matrix, vmin=0.0, vmax=1.0, cmap="YlGnBu", aspect="auto")
        axis.set_xticks(range(len(representations)), representations, rotation=35, ha="right")
        axis.set_yticks(range(len(classifiers)), classifiers)
        axis.set_title(f"Testowy F1 — {method}")
        axis.set_xlabel("Reprezentacja tekstu")
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                axis.text(j, i, f"{matrix[i, j]:.3f}", ha="center", va="center", fontsize=7)
    fig.colorbar(image, ax=axes, label="F1-score (klasa pozytywna)", shrink=0.8)
    fig.suptitle("Porównanie 42 par reprezentacja–klasyfikator")
    fig.savefig(OUTPUT_DIR / "f1_wszystkie_polaczenia.png", dpi=180)
    plt.close(fig)


def save_tuning_comparison(rows: list[dict[str, str]]) -> None:
    best_by_method = {}
    for method in (*METHODS, "Optuna (30 prób)"):
        candidates = [row for row in rows if row["method"] == method]
        if not candidates:
            if method == "Optuna (30 prób)":
                candidates = [row for row in rows if row["method"].startswith("Optuna")]
            if not candidates:
                raise ValueError(f"Missing results for tuning method {method}")
        best_by_method[method] = max(candidates, key=lambda row: float(row["cv_f1"]))

    labels = ["Random Search", "Grid Search", "Optuna"]
    methods = list(best_by_method)
    accuracy = [float(best_by_method[method]["accuracy"]) for method in methods]
    f1 = [float(best_by_method[method]["f1"]) for method in methods]
    x = np.arange(len(labels))
    width = 0.36
    fig, axis = plt.subplots(figsize=(9, 5))
    bars_accuracy = axis.bar(x - width / 2, accuracy, width, label="Accuracy")
    bars_f1 = axis.bar(x + width / 2, f1, width, label="F1 pozytywnej")
    axis.set_xticks(x, labels)
    axis.set_ylim(0, 1)
    axis.set_ylabel("Wynik na zbiorze testowym")
    axis.set_title("Najlepszy model każdego strojenia (wybór według CV F1)")
    axis.legend()
    axis.bar_label(bars_accuracy, fmt="%.3f", padding=2, fontsize=8)
    axis.bar_label(bars_f1, fmt="%.3f", padding=2, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "porownanie_metod_strojenia.png", dpi=180)
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_results()
    save_search_heatmaps(rows)
    save_tuning_comparison(rows)
    print(f"Generated plots under {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
