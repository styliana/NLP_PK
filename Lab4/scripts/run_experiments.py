"""Build text representations, tune classifiers, and evaluate on the held-out set."""

import csv
import gzip
import json
import re
import time
import warnings
from pathlib import Path
from typing import Any

import gensim.downloader as gensim_api
import matplotlib
matplotlib.use("Agg")

import numpy as np
import optuna
from gensim.models import Doc2Vec, Word2Vec
from gensim.models.doc2vec import TaggedDocument
from matplotlib import pyplot as plt
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import (
    GridSearchCV,
    RandomizedSearchCV,
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC, SVC
from sklearn.tree import DecisionTreeClassifier


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PROCESSED_DIR = DATA_DIR / "preprocessed"
RESULTS_DIR = ROOT / "wyniki"
MATRICES_DIR = ROOT / "wykresy" / "macierze_pomylek"
RANDOM_STATE = 42
CV_SPLITS = 2
RANDOM_SEARCH_ITERATIONS = 2
OPTUNA_TRIALS = 30
CV_TUNING_SAMPLE_SIZE = 1500
TOKEN_PATTERN = re.compile(r"n't|[a-z]+(?:'[a-z]+)*")

SEARCH_SPACE: dict[str, dict[str, list[Any]]] = {
    "Logistic Regression": {
        "C": [0.1, 1.0, 10.0],
        "class_weight": [None, "balanced"],
    },
    "Linear SVC": {
        "C": [0.1, 1.0, 10.0],
        "class_weight": [None, "balanced"],
    },
    "RBF SVC": {
        "C": [0.1, 1.0, 10.0],
        "gamma": ["scale", "auto"],
        "class_weight": [None, "balanced"],
    },
    "K-Nearest Neighbors": {
        "n_neighbors": [3, 5, 7],
        "weights": ["uniform", "distance"],
    },
    "Decision Tree": {
        "max_depth": [None, 20, 50],
        "min_samples_leaf": [1, 2],
        "criterion": ["gini", "entropy"],
    },
    "Random Forest": {
        "max_depth": [None, 30],
        "min_samples_leaf": [1, 2],
        "max_features": ["sqrt", 0.5],
    },
    "SGD Classifier": {
        "alpha": [1e-5, 1e-4, 1e-3],
        "loss": ["hinge", "log_loss"],
        "class_weight": [None, "balanced"],
    },
}

GRID_SPACE: dict[str, dict[str, list[Any]]] = {
    "Logistic Regression": {
        "C": [0.1, 10.0],
        "class_weight": [None],
    },
    "Linear SVC": {
        "C": [0.1, 10.0],
        "class_weight": [None],
    },
    "RBF SVC": {
        "C": [0.1, 10.0],
        "gamma": ["scale"],
        "class_weight": [None],
    },
    "K-Nearest Neighbors": {
        "n_neighbors": [3, 7],
        "weights": ["distance"],
    },
    "Decision Tree": {
        "max_depth": [None, 20],
        "min_samples_leaf": [1],
        "criterion": ["gini"],
    },
    "Random Forest": {
        "max_depth": [None, 30],
        "min_samples_leaf": [1],
        "max_features": ["sqrt"],
    },
    "SGD Classifier": {
        "alpha": [1e-5, 1e-3],
        "loss": ["hinge"],
        "class_weight": [None],
    },
}

RESULT_FIELDS = (
    "representation",
    "classifier",
    "method",
    "cv_f1",
    "accuracy",
    "f1",
    "tn",
    "fp",
    "fn",
    "tp",
    "best_params",
)


def load_split(name: str) -> tuple[list[str], np.ndarray]:
    path = PROCESSED_DIR / f"{name}.csv"
    with path.open(encoding="utf-8", newline="") as input_file:
        rows = list(csv.DictReader(input_file))
    expected_fields = {"text", "processed_text", "label"}
    if not rows or not expected_fields.issubset(rows[0]):
        raise ValueError(f"Missing or invalid preprocessed dataset: {path}")
    texts = [row["processed_text"] for row in rows]
    labels = np.asarray([int(row["label"]) for row in rows], dtype=np.int8)
    if set(labels.tolist()) != {0, 1} or any(not text for text in texts):
        raise ValueError(f"Invalid labels or empty text in {path}")
    return texts, labels


def mean_embedding_vectors(
    documents: list[list[str]], keyed_vectors: Any, vector_size: int
) -> tuple[np.ndarray, float]:
    vectors = np.zeros((len(documents), vector_size), dtype=np.float32)
    total_tokens = 0
    known_tokens = 0
    for row, tokens in enumerate(documents):
        known_vectors = []
        for token in tokens:
            total_tokens += 1
            if token in keyed_vectors:
                known_vectors.append(keyed_vectors[token])
                known_tokens += 1
        if known_vectors:
            vectors[row] = np.mean(known_vectors, axis=0, dtype=np.float32)
    coverage = known_tokens / total_tokens if total_tokens else 0.0
    return vectors, coverage


def load_glove_subset(
    archive_path: Path, required_words: set[str], vector_size: int
) -> dict[str, np.ndarray]:
    embeddings = {}
    with gzip.open(archive_path, "rt", encoding="utf-8") as glove_file:
        for line in glove_file:
            word, separator, values = line.partition(" ")
            if not separator or word not in required_words:
                continue
            vector = np.fromstring(values, sep=" ", dtype=np.float32)
            if vector.shape != (vector_size,):
                raise ValueError(
                    f"Invalid GloVe vector for {word!r}: expected {vector_size} "
                    f"values, got {vector.size}."
                )
            embeddings[word] = vector
            if len(embeddings) == len(required_words):
                break
    return embeddings


def build_representations(
    train_texts: list[str], test_texts: list[str]
) -> tuple[dict[str, tuple[Any, Any]], dict[str, Any]]:
    representations: dict[str, tuple[Any, Any]] = {}
    details: dict[str, Any] = {}

    vectorizers = {
        "Bag-of-Words": CountVectorizer(
            min_df=2, max_features=30_000, token_pattern=TOKEN_PATTERN.pattern
        ),
        "Word TF-IDF": TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=2,
            max_features=50_000,
            token_pattern=TOKEN_PATTERN.pattern,
        ),
        "Character TF-IDF": TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), min_df=2, max_features=30_000
        ),
    }
    for name, vectorizer in vectorizers.items():
        train_matrix = vectorizer.fit_transform(train_texts)
        test_matrix = vectorizer.transform(test_texts)
        representations[name] = (train_matrix, test_matrix)
        details[name] = {
            "shape_train": list(train_matrix.shape),
            "shape_test": list(test_matrix.shape),
            "features": int(train_matrix.shape[1]),
            "parameters": vectorizer.get_params(deep=False),
        }

    train_documents = [TOKEN_PATTERN.findall(text) for text in train_texts]
    test_documents = [TOKEN_PATTERN.findall(text) for text in test_texts]
    vector_size = 100

    word2vec = Word2Vec(
        sentences=train_documents,
        vector_size=vector_size,
        window=5,
        min_count=1,
        workers=1,
        sg=1,
        epochs=20,
        seed=RANDOM_STATE,
    )
    train_vectors, train_coverage = mean_embedding_vectors(
        train_documents, word2vec.wv, vector_size
    )
    test_vectors, test_coverage = mean_embedding_vectors(
        test_documents, word2vec.wv, vector_size
    )
    scaler = StandardScaler().fit(train_vectors)
    representations["Word2Vec mean"] = (
        scaler.transform(train_vectors).astype(np.float32),
        scaler.transform(test_vectors).astype(np.float32),
    )
    details["Word2Vec mean"] = {
        "shape_train": list(train_vectors.shape),
        "shape_test": list(test_vectors.shape),
        "vector_size": vector_size,
        "training": {"window": 5, "min_count": 1, "sg": 1, "epochs": 20},
        "train_vocabulary": len(word2vec.wv),
        "token_coverage": {"train": train_coverage, "test": test_coverage},
        "scaling": "StandardScaler dopasowany wyłącznie do treningu",
    }

    tagged_documents = [
        TaggedDocument(words=tokens, tags=[f"train_{index}"])
        for index, tokens in enumerate(train_documents)
    ]
    doc2vec = Doc2Vec(
        documents=tagged_documents,
        vector_size=vector_size,
        window=5,
        min_count=2,
        workers=1,
        dm=0,
        epochs=30,
        seed=RANDOM_STATE,
    )
    train_vectors = np.asarray(
        [doc2vec.dv[f"train_{index}"] for index in range(len(train_documents))],
        dtype=np.float32,
    )
    test_vectors = np.zeros((len(test_documents), vector_size), dtype=np.float32)
    for index, tokens in enumerate(test_documents):
        known_tokens = [token for token in tokens if token in doc2vec.wv]
        if known_tokens:
            doc2vec.random.seed(RANDOM_STATE + index)
            test_vectors[index] = doc2vec.infer_vector(known_tokens, epochs=30)
    scaler = StandardScaler().fit(train_vectors)
    representations["Doc2Vec"] = (
        scaler.transform(train_vectors).astype(np.float32),
        scaler.transform(test_vectors).astype(np.float32),
    )
    details["Doc2Vec"] = {
        "shape_train": list(train_vectors.shape),
        "shape_test": list(test_vectors.shape),
        "vector_size": vector_size,
        "training": {"dm": 0, "window": 5, "min_count": 2, "epochs": 30},
        "train_vocabulary": len(doc2vec.wv),
        "test_documents_with_known_tokens": int(
            sum(any(token in doc2vec.wv for token in tokens) for tokens in test_documents)
        ),
        "scaling": "StandardScaler dopasowany wyłącznie do treningu",
    }

    glove_model_name = "glove-wiki-gigaword-100"
    print(
        "Downloading or locating pretrained GloVe vectors "
        f"({glove_model_name}); loading only words used in this dataset..."
    )
    glove_archive = Path(gensim_api.load(glove_model_name, return_path=True))
    required_words = {
        token for document in train_documents + test_documents for token in document
    }
    glove = load_glove_subset(glove_archive, required_words, vector_size)
    glove_train, train_coverage = mean_embedding_vectors(
        train_documents, glove, vector_size
    )
    glove_test, test_coverage = mean_embedding_vectors(
        test_documents, glove, vector_size
    )
    scaler = StandardScaler().fit(glove_train)
    representations["GloVe mean (pretrained)"] = (
        scaler.transform(glove_train).astype(np.float32),
        scaler.transform(glove_test).astype(np.float32),
    )
    details["GloVe mean (pretrained)"] = {
        "shape_train": list(glove_train.shape),
        "shape_test": list(glove_test.shape),
        "model": glove_model_name,
        "vector_size": vector_size,
        "vocabulary_words_loaded": len(glove),
        "token_coverage": {"train": train_coverage, "test": test_coverage},
        "scaling": "StandardScaler dopasowany wyłącznie do treningu",
    }
    return representations, details


def create_classifier(name: str, params: dict[str, Any] | None = None) -> Any:
    params = params or {}
    if name == "Logistic Regression":
        return LogisticRegression(
            max_iter=1500, solver="liblinear", random_state=RANDOM_STATE, **params
        )
    if name == "Linear SVC":
        return LinearSVC(random_state=RANDOM_STATE, max_iter=5000, **params)
    if name == "RBF SVC":
        return SVC(cache_size=512, **params)
    if name == "K-Nearest Neighbors":
        return KNeighborsClassifier(n_jobs=1, **params)
    if name == "Decision Tree":
        return DecisionTreeClassifier(random_state=RANDOM_STATE, **params)
    if name == "Random Forest":
        return RandomForestClassifier(
            n_estimators=50, random_state=RANDOM_STATE, n_jobs=1, **params
        )
    if name == "SGD Classifier":
        return SGDClassifier(
            max_iter=2000, tol=1e-3, random_state=RANDOM_STATE, **params
        )
    raise ValueError(f"Unknown classifier: {name}")


def get_tuning_data(
    train_matrix: Any, train_labels: np.ndarray
) -> tuple[Any, np.ndarray]:
    if len(train_labels) <= CV_TUNING_SAMPLE_SIZE:
        return train_matrix, train_labels
    sampled_matrix, _, sampled_labels, _ = train_test_split(
        train_matrix,
        train_labels,
        train_size=CV_TUNING_SAMPLE_SIZE,
        random_state=RANDOM_STATE,
        stratify=train_labels,
    )
    return sampled_matrix, sampled_labels


def get_refit_data(
    classifier_name: str, train_matrix: Any, train_labels: np.ndarray
) -> tuple[Any, np.ndarray]:
    if classifier_name == "RBF SVC":
        return get_tuning_data(train_matrix, train_labels)
    return train_matrix, train_labels


def save_results(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "best_params": json.dumps(
                        row["best_params"], ensure_ascii=False, sort_keys=True
                    ),
                }
            )


def evaluate(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    representation: str,
    classifier: str,
    method: str,
    cv_f1: float,
    best_params: dict[str, Any],
) -> dict[str, Any]:
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1])
    return {
        "representation": representation,
        "classifier": classifier,
        "method": method,
        "cv_f1": float(cv_f1),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred, pos_label=1)),
        "tn": int(matrix[0, 0]),
        "fp": int(matrix[0, 1]),
        "fn": int(matrix[1, 0]),
        "tp": int(matrix[1, 1]),
        "best_params": best_params,
    }


def save_confusion_matrix(row: dict[str, Any], path: Path, title_suffix: str) -> None:
    matrix = np.asarray([[row["tn"], row["fp"]], [row["fn"], row["tp"]]])
    fig, axis = plt.subplots(figsize=(4.8, 4.2))
    image = axis.imshow(matrix, cmap="Blues")
    fig.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    axis.set(
        xticks=[0, 1],
        yticks=[0, 1],
        xticklabels=["negatywny", "pozytywny"],
        yticklabels=["negatywny", "pozytywny"],
        xlabel="Predykcja",
        ylabel="Etykieta rzeczywista",
        title=(
            f"{row['representation']} × {row['classifier']}\n"
            f"{title_suffix}; F1={row['f1']:.3f}"
        ),
    )
    threshold = matrix.max() / 2 if matrix.size else 0
    for true_label in range(2):
        for predicted_label in range(2):
            axis.text(
                predicted_label,
                true_label,
                str(matrix[true_label, predicted_label]),
                ha="center",
                va="center",
                color="white" if matrix[true_label, predicted_label] > threshold else "black",
            )
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def run_searches(
    representations: dict[str, tuple[Any, Any]],
    train_labels: np.ndarray,
    test_labels: np.ndarray,
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]]]:
    cv = StratifiedKFold(
        n_splits=CV_SPLITS, shuffle=True, random_state=RANDOM_STATE
    )
    results: list[dict[str, Any]] = []
    pair_results: dict[tuple[str, str], list[dict[str, Any]]] = {}
    total_pairs = len(representations) * len(SEARCH_SPACE)
    completed_pairs = 0
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    for representation_name, (train_matrix, test_matrix) in representations.items():
        for classifier_name, distributions in SEARCH_SPACE.items():
            completed_pairs += 1
            print(
                f"[{completed_pairs}/{total_pairs}] {representation_name} × "
                f"{classifier_name}: RandomizedSearchCV and GridSearchCV"
            )
            estimator = create_classifier(classifier_name)
            tuning_matrix, tuning_labels = get_tuning_data(train_matrix, train_labels)
            random_search = RandomizedSearchCV(
                estimator=estimator,
                param_distributions=distributions,
                n_iter=RANDOM_SEARCH_ITERATIONS,
                scoring="f1",
                cv=cv,
                random_state=RANDOM_STATE,
                n_jobs=1,
                refit=True,
                error_score="raise",
            )
            random_search.fit(tuning_matrix, tuning_labels)
            refit_matrix, refit_labels = get_refit_data(
                classifier_name, train_matrix, train_labels
            )
            random_best = clone(random_search.best_estimator_).fit(
                refit_matrix, refit_labels
            )
            random_row = evaluate(
                test_labels,
                random_best.predict(test_matrix),
                representation_name,
                classifier_name,
                "RandomizedSearchCV",
                random_search.best_score_,
                random_search.best_params_,
            )
            results.append(random_row)

            grid_search = GridSearchCV(
                estimator=estimator,
                param_grid=GRID_SPACE[classifier_name],
                scoring="f1",
                cv=cv,
                n_jobs=1,
                refit=True,
                error_score="raise",
            )
            grid_search.fit(tuning_matrix, tuning_labels)
            grid_best = clone(grid_search.best_estimator_).fit(
                refit_matrix, refit_labels
            )
            grid_row = evaluate(
                test_labels,
                grid_best.predict(test_matrix),
                representation_name,
                classifier_name,
                "GridSearchCV",
                grid_search.best_score_,
                grid_search.best_params_,
            )
            results.append(grid_row)
            pair_results[(representation_name, classifier_name)] = [
                random_row,
                grid_row,
            ]
            save_results(RESULTS_DIR / "search_results.csv", results)
    return results, pair_results


def run_optuna(
    representations: dict[str, tuple[Any, Any]],
    train_labels: np.ndarray,
    test_labels: np.ndarray,
) -> tuple[dict[str, Any], Any]:
    cv = StratifiedKFold(
        n_splits=CV_SPLITS, shuffle=True, random_state=RANDOM_STATE
    )
    representation_names = list(representations)
    classifier_names = list(SEARCH_SPACE)

    def objective(trial: optuna.Trial) -> float:
        representation_name = trial.suggest_categorical(
            "representation", representation_names
        )
        classifier_name = trial.suggest_categorical("classifier", classifier_names)
        params = {
            parameter: trial.suggest_categorical(
                f"{classifier_name}__{parameter}", values
            )
            for parameter, values in SEARCH_SPACE[classifier_name].items()
        }
        train_matrix, _ = representations[representation_name]
        tuning_matrix, tuning_labels = get_tuning_data(train_matrix, train_labels)
        scores = cross_val_score(
            create_classifier(classifier_name, params),
            tuning_matrix,
            tuning_labels,
            scoring="f1",
            cv=cv,
            n_jobs=1,
            error_score="raise",
        )
        return float(np.mean(scores))

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE),
        study_name="lab4-sentiment-model-selection",
    )
    study.optimize(objective, n_trials=OPTUNA_TRIALS, show_progress_bar=True)

    representation_name = study.best_params["representation"]
    classifier_name = study.best_params["classifier"]
    best_params = {
        parameter: study.best_params[f"{classifier_name}__{parameter}"]
        for parameter in SEARCH_SPACE[classifier_name]
    }
    train_matrix, test_matrix = representations[representation_name]
    refit_matrix, refit_labels = get_refit_data(
        classifier_name, train_matrix, train_labels
    )
    estimator = create_classifier(classifier_name, best_params)
    estimator.fit(refit_matrix, refit_labels)
    row = evaluate(
        test_labels,
        estimator.predict(test_matrix),
        representation_name,
        classifier_name,
        "Optuna (30 prób)",
        study.best_value,
        best_params,
    )
    study.trials_dataframe().to_csv(
        RESULTS_DIR / "optuna_trials.csv", index=False, encoding="utf-8"
    )
    return row, study


def main() -> None:
    warnings.filterwarnings("default", category=UserWarning)
    start_time = time.perf_counter()
    train_texts, train_labels = load_split("train")
    test_texts, test_labels = load_split("test")
    if len(train_texts) != 8529 or len(test_texts) != 2133:
        raise ValueError("Unexpected split sizes; rerun prepare_data.py first.")

    print("Building the six required text representations...")
    representations, representation_details = build_representations(
        train_texts, test_texts
    )
    if len(representations) != 6:
        raise ValueError(f"Expected six representations, got {len(representations)}")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    MATRICES_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "representation_details.json").write_text(
        json.dumps(representation_details, ensure_ascii=False, indent=2, default=str)
        + "\n",
        encoding="utf-8",
    )

    search_rows, pair_results = run_searches(
        representations, train_labels, test_labels
    )
    optuna_row, study = run_optuna(representations, train_labels, test_labels)
    search_rows.append(optuna_row)
    save_results(RESULTS_DIR / "all_results.csv", search_rows)

    selected_rows = []
    for pair, rows in pair_results.items():
        selected = max(rows, key=lambda row: row["cv_f1"])
        selected_rows.append(selected)
        representation_name, classifier_name = pair
        filename = (
            f"{representation_name}__{classifier_name}"
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
            + ".png"
        )
        save_confusion_matrix(
            selected,
            MATRICES_DIR / filename,
            f"najlepszy CV spośród Random/Grid ({selected['method']})",
        )
    save_confusion_matrix(
        optuna_row, MATRICES_DIR / "optuna_best_model.png", "najlepszy model Optuna"
    )

    best_by_method = {}
    for method in ("RandomizedSearchCV", "GridSearchCV"):
        candidates = [row for row in search_rows if row["method"] == method]
        best = max(candidates, key=lambda row: row["cv_f1"])
        best_by_method[method] = best
    best_by_method["Optuna"] = optuna_row

    elapsed = time.perf_counter() - start_time
    summary = {
        "dataset": "Cornell Sentence Polarity v1.0",
        "train_examples": len(train_labels),
        "test_examples": len(test_labels),
        "random_state": RANDOM_STATE,
        "cross_validation": {
            "method": "StratifiedKFold",
            "splits": CV_SPLITS,
            "shuffle": True,
            "scoring": "F1 positive",
        },
        "random_search_iterations_per_pair": RANDOM_SEARCH_ITERATIONS,
        "cv_tuning_sample_size": min(CV_TUNING_SAMPLE_SIZE, len(train_labels)),
        "non_rbf_final_fit_size": len(train_labels),
        "rbf_svc_final_fit_size": min(CV_TUNING_SAMPLE_SIZE, len(train_labels)),
        "grid_search_candidates_per_pair": {
            name: int(np.prod([len(values) for values in grid.values()]))
            for name, grid in GRID_SPACE.items()
        },
        "optuna_trials": len(study.trials),
        "pairings": len(representations) * len(SEARCH_SPACE),
        "search_result_rows": len(search_rows) - 1,
        "selected_confusion_matrices": len(selected_rows),
        "elapsed_seconds": round(elapsed, 2),
        "representation_details": representation_details,
        "best_by_method": best_by_method,
    }
    (RESULTS_DIR / "experiment_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(f"Finished in {elapsed / 60:.1f} minutes.")
    for method, row in best_by_method.items():
        print(
            f"{method}: {row['representation']} + {row['classifier']}, "
            f"test accuracy={row['accuracy']:.4f}, F1={row['f1']:.4f}"
        )


if __name__ == "__main__":
    main()
