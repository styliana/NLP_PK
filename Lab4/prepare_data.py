"""Download the Cornell sentence-polarity corpus and create a reproducible split."""

import csv
import json
from collections import Counter
from pathlib import Path

import nltk
from nltk.corpus import sentence_polarity
from sklearn.model_selection import train_test_split


RANDOM_STATE = 42
TEST_SIZE = 0.2
EXPECTED_PER_CLASS = 5331
OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "processed"


def load_records() -> list[tuple[str, int]]:
    try:
        categories = sentence_polarity.categories()
    except LookupError:
        print("Downloading the NLTK sentence_polarity corpus...")
        if not nltk.download("sentence_polarity", quiet=True):
            raise RuntimeError("Could not download the NLTK sentence_polarity corpus.")
        categories = sentence_polarity.categories()

    if not {"neg", "pos"}.issubset(categories):
        raise ValueError(f"Unexpected corpus categories: {categories}")

    records = [
        (" ".join(tokens), label)
        for category, label in (("neg", 0), ("pos", 1))
        for tokens in sentence_polarity.sents(categories=category)
    ]
    counts = Counter(label for _, label in records)
    if counts != {0: EXPECTED_PER_CLASS, 1: EXPECTED_PER_CLASS}:
        raise ValueError(
            "Unexpected sentence-polarity corpus size: "
            f"expected {EXPECTED_PER_CLASS} sentences per class, got {dict(counts)}."
        )
    if any(not text.strip() for text, _ in records):
        raise ValueError("The corpus contains an empty sentence.")
    if len({text for text, _ in records}) != len(records):
        raise ValueError("The corpus contains duplicate sentence texts.")

    return records


def write_split(path: Path, records: list[tuple[str, int]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(("text", "label"))
        writer.writerows(records)


def main() -> None:
    records = load_records()
    texts = [text for text, _ in records]
    labels = [label for _, label in records]
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts,
        labels,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=labels,
    )
    train_records = list(zip(train_texts, train_labels))
    test_records = list(zip(test_texts, test_labels))

    if set(train_texts).intersection(test_texts):
        raise ValueError("A sentence occurs in both the training and test sets.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    train_path = OUTPUT_DIR / "train.csv"
    test_path = OUTPUT_DIR / "test.csv"
    write_split(train_path, train_records)
    write_split(test_path, test_records)

    summary = {
        "dataset": "Cornell Sentence Polarity v1.0 (NLTK sentence_polarity)",
        "source": "https://www.cs.cornell.edu/people/pabo/movie-review-data/",
        "total_examples": len(records),
        "class_counts": dict(sorted(Counter(labels).items())),
        "test_size": TEST_SIZE,
        "random_state": RANDOM_STATE,
        "splits": {
            "train": {
                "examples": len(train_records),
                "class_counts": dict(sorted(Counter(train_labels).items())),
            },
            "test": {
                "examples": len(test_records),
                "class_counts": dict(sorted(Counter(test_labels).items())),
            },
        },
        "cross_split_duplicate_texts": 0,
    }
    summary_path = OUTPUT_DIR / "dataset_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Dataset: {len(records)} sentences (5,331 negative, 5,331 positive)")
    print(f"Training set: {len(train_records)}; test set: {len(test_records)}")
    print(f"Saved splits and summary under {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
