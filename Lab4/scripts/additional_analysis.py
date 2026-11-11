"""Dodatkowe analizy do sprawozdania (sekcja 6).

1. Przykłady błędnych klasyfikacji (FP / FN) najlepszego modelu testowego.
2. Top 10 słów najbardziej pozytywnych i negatywnych (wagi Linear SVC na TF-IDF).
3. Czas uczenia i predykcji vs. F1 dla 42 par reprezentacja–klasyfikator.

Skrypt nie stroi modeli ponownie: używa hiperparametrów zapisanych w
``wyniki/all_results.csv`` (wariant o wyższym CV F1 spośród Random/Grid, tak jak
macierze pomyłek) i mierzy czas jednego dopasowania na danych końcowych.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_experiments import (  # noqa: E402
    PROCESSED_DIR,
    RESULTS_DIR,
    ROOT,
    build_representations,
    create_classifier,
    get_refit_data,
    load_split,
)

PLOTS_DIR = ROOT / "wykresy"
ANALYSIS_REPRESENTATION = "Word TF-IDF"
ANALYSIS_CLASSIFIER = "Linear SVC"
EXAMPLES_PER_TYPE = 8
TOP_WORDS = 10
NEGATION_WORDS = {"not", "no", "never", "but", "without", "nor", "n't"}
POSITIVE_COLOR = "#2a78d6"
NEGATIVE_COLOR = "#eb6834"
TEXT_SECONDARY = "#52514e"


def load_original_texts(name: str) -> list[str]:
    with (PROCESSED_DIR / f"{name}.csv").open(encoding="utf-8", newline="") as file:
        return [row["text"] for row in csv.DictReader(file)]


def selected_configurations() -> list[dict[str, Any]]:
    """Wariant o najwyższym CV F1 dla każdej pary (pierwszy przy remisie)."""
    with (RESULTS_DIR / "all_results.csv").open(encoding="utf-8", newline="") as file:
        rows = [row for row in csv.DictReader(file) if row["method"] != "Optuna (30 prób)"]
    selected: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["representation"], row["classifier"])
        if key not in selected or float(row["cv_f1"]) > float(selected[key]["cv_f1"]):
            selected[key] = row
    return list(selected.values())


def timing_benchmark(
    representations: dict[str, tuple[Any, Any]],
    representation_seconds: dict[str, float],
    train_labels: np.ndarray,
    test_labels: np.ndarray,
) -> list[dict[str, Any]]:
    rows = []
    for config in selected_configurations():
        representation = config["representation"]
        classifier_name = config["classifier"]
        params = json.loads(config["best_params"])
        train_matrix, test_matrix = representations[representation]
        fit_matrix, fit_labels = get_refit_data(classifier_name, train_matrix, train_labels)
        model = create_classifier(classifier_name, params)
        start = time.perf_counter()
        model.fit(fit_matrix, fit_labels)
        fit_seconds = time.perf_counter() - start
        start = time.perf_counter()
        predictions = model.predict(test_matrix)
        predict_seconds = time.perf_counter() - start
        row = {
            "representation": representation,
            "classifier": classifier_name,
            "method": config["method"],
            "best_params": config["best_params"],
            "train_examples": int(fit_matrix.shape[0]),
            "representation_seconds": round(representation_seconds[representation], 3),
            "fit_seconds": round(fit_seconds, 3),
            "predict_seconds": round(predict_seconds, 3),
            "accuracy": round(accuracy_score(test_labels, predictions), 4),
            "f1": round(f1_score(test_labels, predictions), 4),
            "f1_reported": round(float(config["f1"]), 4),
        }
        rows.append(row)
        print(
            f"{representation:>24} + {classifier_name:<20} "
            f"fit={fit_seconds:7.2f}s predict={predict_seconds:6.2f}s F1={row['f1']:.4f}"
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_time_vs_f1(rows: list[dict[str, Any]], path: Path) -> None:
    classifiers = list(dict.fromkeys(row["classifier"] for row in rows))
    representations = list(dict.fromkeys(row["representation"] for row in rows))
    colors = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]
    markers = ["o", "s", "^", "D", "v", "P"]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for row in rows:
        ax.scatter(
            row["fit_seconds"] + row["predict_seconds"],
            row["f1"],
            s=70,
            color=colors[classifiers.index(row["classifier"])],
            marker=markers[representations.index(row["representation"])],
            edgecolors="white",
            linewidths=1.5,
            zorder=3,
        )
    best = max(rows, key=lambda row: row["f1"])
    ax.annotate(
        f"{best['representation']} + {best['classifier']}\nF1={best['f1']:.3f}",
        (best["fit_seconds"] + best["predict_seconds"], best["f1"]),
        xytext=(4, -62),
        arrowprops={"arrowstyle": "-", "color": TEXT_SECONDARY, "linewidth": 0.8},
        textcoords="offset points",
        fontsize=9,
        color=TEXT_SECONDARY,
    )
    ax.set_xscale("log")
    ax.set_xlabel("Czas uczenia + predykcji jednego modelu [s] (skala log)")
    ax.set_ylabel("F1 na zbiorze testowym")
    ax.set_title("Koszt obliczeniowy vs. jakość — 42 pary reprezentacja–klasyfikator")
    ax.grid(True, color="#e6e5e1", linewidth=0.8, zorder=0)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    classifier_handles = [
        plt.Line2D([], [], marker="o", linestyle="", color=colors[i], markersize=8, label=name)
        for i, name in enumerate(classifiers)
    ]
    representation_handles = [
        plt.Line2D([], [], marker=markers[i], linestyle="", color=TEXT_SECONDARY, markersize=8, label=name)
        for i, name in enumerate(representations)
    ]
    first = ax.legend(handles=classifier_handles, title="Klasyfikator", loc="upper left",
                      bbox_to_anchor=(1.01, 1.0), frameon=False)
    ax.add_artist(first)
    ax.legend(handles=representation_handles, title="Reprezentacja", loc="lower left",
              bbox_to_anchor=(1.01, 0.0), frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_top_words(positive: list[tuple[str, float]], negative: list[tuple[str, float]], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharex=True)
    for ax, words, color, title in (
        (axes[0], negative, NEGATIVE_COLOR, "Top 10 cech negatywnych"),
        (axes[1], positive, POSITIVE_COLOR, "Top 10 cech pozytywnych"),
    ):
        labels = [word for word, _ in words][::-1]
        values = [abs(weight) for _, weight in words][::-1]
        ax.barh(labels, values, color=color, height=0.6, edgecolor="white", linewidth=2)
        ax.set_title(title)
        ax.tick_params(axis="x", labelbottom=True)
        ax.set_xlabel("|waga| w modelu Linear SVC")
        ax.grid(True, axis="x", color="#e6e5e1", linewidth=0.8)
        ax.set_axisbelow(True)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
    fig.suptitle(f"Najsilniejsze cechy: {ANALYSIS_REPRESENTATION} + {ANALYSIS_CLASSIFIER} (C=0.1)")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> None:
    train_texts, train_labels = load_split("train")
    test_texts, test_labels = load_split("test")
    original_test = load_original_texts("test")

    start = time.perf_counter()
    representations, details = build_representations(train_texts, test_texts)
    total_representation_seconds = time.perf_counter() - start
    # Czas budowy każdej reprezentacji mierzymy osobno, budując je jeszcze raz.
    representation_seconds = measure_representation_times(train_texts, test_texts)

    timing_rows = timing_benchmark(representations, representation_seconds, train_labels, test_labels)
    write_csv(RESULTS_DIR / "czas_vs_wynik.csv", timing_rows)
    plot_time_vs_f1(timing_rows, PLOTS_DIR / "czas_vs_f1.png")

    # --- Analiza błędów i najważniejszych cech dla najlepszego modelu testowego ---
    from sklearn.feature_extraction.text import TfidfVectorizer
    from run_experiments import TOKEN_PATTERN

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2), min_df=2, max_features=50_000, token_pattern=TOKEN_PATTERN.pattern
    )
    train_matrix = vectorizer.fit_transform(train_texts)
    test_matrix = vectorizer.transform(test_texts)
    model = create_classifier(ANALYSIS_CLASSIFIER, {"C": 0.1, "class_weight": None})
    model.fit(train_matrix, train_labels)
    scores = model.decision_function(test_matrix)
    predictions = (scores > 0).astype(int)

    features = vectorizer.get_feature_names_out()
    coefficients = model.coef_.ravel()
    order = np.argsort(coefficients)
    negative = [(features[i], float(coefficients[i])) for i in order[:TOP_WORDS]]
    positive = [(features[i], float(coefficients[i])) for i in order[::-1][:TOP_WORDS]]
    write_csv(
        RESULTS_DIR / "top_slowa.csv",
        [{"polarity": "positive", "rank": r + 1, "feature": w, "weight": round(c, 4)} for r, (w, c) in enumerate(positive)]
        + [{"polarity": "negative", "rank": r + 1, "feature": w, "weight": round(c, 4)} for r, (w, c) in enumerate(negative)],
    )
    plot_top_words(positive, negative, PLOTS_DIR / "top_slowa.png")

    error_rows = []
    for error_type, true_label in (("FP", 0), ("FN", 1)):
        indices = np.where((test_labels == true_label) & (predictions != true_label))[0]
        indices = indices[np.argsort(-np.abs(scores[indices]))][:EXAMPLES_PER_TYPE]
        for index in indices:
            error_rows.append({
                "type": error_type,
                "true_label": int(true_label),
                "predicted": int(predictions[index]),
                "decision_score": round(float(scores[index]), 3),
                "text": original_test[index],
                "processed_text": test_texts[index],
            })
    write_csv(RESULTS_DIR / "bledne_klasyfikacje.csv", error_rows)

    has_negation = np.array([
        any(token in NEGATION_WORDS or token.endswith("n't") for token in TOKEN_PATTERN.findall(t))
        for t in test_texts
    ])
    wrong = predictions != test_labels

    # --- Negacja a reprezentacja: ten sam klasyfikator (Linear SVC) na każdej reprezentacji ---
    configs = {(c["representation"], c["classifier"]): c for c in selected_configurations()}
    shown_fp_fn = [i for i in np.where(wrong)[0]]
    negation_by_representation = []
    for representation, (rep_train, rep_test) in representations.items():
        config = configs[(representation, "Linear SVC")]
        rep_model = create_classifier("Linear SVC", json.loads(config["best_params"]))
        rep_model.fit(rep_train, train_labels)
        rep_wrong = rep_model.predict(rep_test) != test_labels
        negation_by_representation.append({
            "representation": representation,
            "error_with_negation": round(float(rep_wrong[has_negation].mean()), 4),
            "error_without_negation": round(float(rep_wrong[~has_negation].mean()), 4),
            "gap_pp": round(100 * float(rep_wrong[has_negation].mean() - rep_wrong[~has_negation].mean()), 1),
            "also_wrong_on_tfidf_errors": round(float(rep_wrong[shown_fp_fn].mean()), 4),
        })

    # --- Zdania testowe ze złożoną negacją (napisane ręcznie, spoza zbioru) ---
    probe_rows = negation_probes(
        vectorizer, model, train_texts, train_labels, configs
    )

    # --- Pozycja przykładowych słów z notatek (masterpiece, brilliant, ...) ---
    from nltk.stem import WordNetLemmatizer
    from preprocess_data import preprocess_text

    lemmatizer = WordNetLemmatizer()
    ranking = {features[i]: rank for rank, i in enumerate(order[::-1], start=1)}
    example_words = []
    for word in ("masterpiece", "brilliant", "thrilling", "boring", "awful", "worst"):
        lemma = preprocess_text(word, lemmatizer)
        index = vectorizer.vocabulary_.get(lemma)
        if index is None:
            example_words.append({"word": word, "lemma": lemma, "weight": None, "rank_positive": None})
            continue
        example_words.append({
            "word": word,
            "lemma": lemma,
            "weight": round(float(coefficients[index]), 4),
            "rank_positive": ranking[lemma],
            "rank_negative": len(features) + 1 - ranking[lemma],
            "train_documents": int((train_matrix[:, index] > 0).sum()),
        })

    summary = {
        "model": f"{ANALYSIS_REPRESENTATION} + {ANALYSIS_CLASSIFIER} (C=0.1)",
        "test_accuracy": round(accuracy_score(test_labels, predictions), 4),
        "test_f1": round(f1_score(test_labels, predictions), 4),
        "false_positives": int(((test_labels == 0) & (predictions == 1)).sum()),
        "false_negatives": int(((test_labels == 1) & (predictions == 0)).sum()),
        "sentences_with_negation_or_contrast": int(has_negation.sum()),
        "error_rate_with_negation_or_contrast": round(float(wrong[has_negation].mean()), 4),
        "error_rate_without_negation_or_contrast": round(float(wrong[~has_negation].mean()), 4),
        "top_positive": positive,
        "top_negative": negative,
        "negation_by_representation": negation_by_representation,
        "negation_probes": probe_rows,
        "example_words": example_words,
        "negation_ngrams": [
            {
                "feature": f,
                "weight": round(float(coefficients[vectorizer.vocabulary_[f]]), 4),
                "train_documents": int((train_matrix[:, vectorizer.vocabulary_[f]] > 0).sum()),
            }
            for f in ("bad", "not", "not bad", "good", "not good", "but")
            if f in vectorizer.vocabulary_
        ],
        "vocabulary_size": int(len(features)),
        "representation_build_seconds": representation_seconds,
        "all_representations_build_seconds": round(total_representation_seconds, 2),
        "timing_note": "Jedno dopasowanie z wybranymi hiperparametrami; RBF SVC na próbce 1500, pozostałe na 8529 przykładach.",
    }
    (RESULTS_DIR / "analiza_dodatkowa.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in summary.items() if not k.startswith("top")}, ensure_ascii=False, indent=2))


NEGATION_PROBES = (
    ("the film was not as bad as i expected .", 1),
    ("not bad at all , actually quite good .", 1),
    ("never boring and never dull for a second .", 1),
    ("i expected a masterpiece , but it was not good .", 0),
    ("it is not funny , not clever and not worth your time .", 0),
    ("a brilliant cast wasted on a terrible script .", 0),
)


def negation_probes(
    vectorizer: Any,
    tfidf_model: Any,
    train_texts: list[str],
    train_labels: np.ndarray,
    configs: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Ręcznie napisane zdania ze złożoną negacją: Word TF-IDF vs GloVe mean."""
    import gensim.downloader as gensim_api
    from nltk.stem import WordNetLemmatizer
    from sklearn.preprocessing import StandardScaler

    from preprocess_data import preprocess_text
    from run_experiments import TOKEN_PATTERN, load_glove_subset, mean_embedding_vectors

    lemmatizer = WordNetLemmatizer()
    processed = [preprocess_text(text, lemmatizer) for text, _ in NEGATION_PROBES]
    tfidf_scores = tfidf_model.decision_function(vectorizer.transform(processed))

    train_docs = [TOKEN_PATTERN.findall(t) for t in train_texts]
    probe_docs = [TOKEN_PATTERN.findall(t) for t in processed]
    archive = Path(gensim_api.load("glove-wiki-gigaword-100", return_path=True))
    glove = load_glove_subset(archive, {t for d in train_docs + probe_docs for t in d}, 100)
    train_vectors, _ = mean_embedding_vectors(train_docs, glove, 100)
    probe_vectors, _ = mean_embedding_vectors(probe_docs, glove, 100)
    scaler = StandardScaler().fit(train_vectors)
    params = json.loads(configs[("GloVe mean (pretrained)", "Linear SVC")]["best_params"])
    glove_model = create_classifier("Linear SVC", params).fit(scaler.transform(train_vectors), train_labels)
    glove_scores = glove_model.decision_function(scaler.transform(probe_vectors))

    rows = []
    for (text, label), prep, s_tfidf, s_glove in zip(NEGATION_PROBES, processed, tfidf_scores, glove_scores):
        rows.append({
            "text": text,
            "processed_text": prep,
            "true_label": label,
            "tfidf_prediction": int(s_tfidf > 0),
            "tfidf_score": round(float(s_tfidf), 3),
            "glove_prediction": int(s_glove > 0),
            "glove_score": round(float(s_glove), 3),
        })
    return rows


def measure_representation_times(train_texts: list[str], test_texts: list[str]) -> dict[str, float]:
    """Czas budowy każdej reprezentacji (fit na treningu + transform testu)."""
    import gensim.downloader as gensim_api
    from gensim.models import Doc2Vec, Word2Vec
    from gensim.models.doc2vec import TaggedDocument
    from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
    from run_experiments import TOKEN_PATTERN, load_glove_subset, mean_embedding_vectors

    times: dict[str, float] = {}
    for name, vectorizer in {
        "Bag-of-Words": CountVectorizer(min_df=2, max_features=30_000, token_pattern=TOKEN_PATTERN.pattern),
        "Word TF-IDF": TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=50_000, token_pattern=TOKEN_PATTERN.pattern),
        "Character TF-IDF": TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, max_features=30_000),
    }.items():
        start = time.perf_counter()
        vectorizer.fit_transform(train_texts)
        vectorizer.transform(test_texts)
        times[name] = time.perf_counter() - start

    train_docs = [TOKEN_PATTERN.findall(t) for t in train_texts]
    test_docs = [TOKEN_PATTERN.findall(t) for t in test_texts]
    start = time.perf_counter()
    w2v = Word2Vec(sentences=train_docs, vector_size=100, window=5, min_count=1, workers=1, sg=1, epochs=20, seed=42)
    mean_embedding_vectors(train_docs, w2v.wv, 100)
    mean_embedding_vectors(test_docs, w2v.wv, 100)
    times["Word2Vec mean"] = time.perf_counter() - start

    start = time.perf_counter()
    d2v = Doc2Vec(
        documents=[TaggedDocument(words=d, tags=[f"train_{i}"]) for i, d in enumerate(train_docs)],
        vector_size=100, window=5, min_count=2, workers=1, dm=0, epochs=30, seed=42,
    )
    for i, tokens in enumerate(test_docs):
        known = [t for t in tokens if t in d2v.wv]
        if known:
            d2v.random.seed(42 + i)
            d2v.infer_vector(known, epochs=30)
    times["Doc2Vec"] = time.perf_counter() - start

    start = time.perf_counter()
    archive = Path(gensim_api.load("glove-wiki-gigaword-100", return_path=True))
    glove = load_glove_subset(archive, {t for d in train_docs + test_docs for t in d}, 100)
    mean_embedding_vectors(train_docs, glove, 100)
    mean_embedding_vectors(test_docs, glove, 100)
    times["GloVe mean (pretrained)"] = time.perf_counter() - start
    return {name: round(value, 2) for name, value in times.items()}


if __name__ == "__main__":
    main()
