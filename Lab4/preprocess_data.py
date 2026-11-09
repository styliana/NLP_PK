"""Normalize and lemmatize the already-split sentiment dataset."""

import csv
import json
import re
from collections import Counter
from pathlib import Path

import nltk
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


DATA_DIR = Path(__file__).resolve().parent / "data"
INPUT_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "preprocessed"
TOKEN_PATTERN = re.compile(r"n't|[a-z]+(?:'[a-z]+)*")
NEGATION_AND_CONTRAST = {
    "but",
    "cannot",
    "hardly",
    "however",
    "neither",
    "never",
    "no",
    "nor",
    "not",
    "although",
    "without",
    "yet",
}
PENN_TO_WORDNET = {
    "J": "a",
    "N": "n",
    "R": "r",
    "V": "v",
}


def ensure_nltk_resource(resource: str) -> None:
    base_path = (
        f"taggers/{resource}"
        if resource == "averaged_perceptron_tagger_eng"
        else f"corpora/{resource}"
    )
    for path in (f"{base_path}/", f"{base_path}.zip", base_path):
        try:
            nltk.data.find(path)
            return
        except LookupError:
            continue

    print(f"Downloading NLTK resource: {resource}")
    if not nltk.download(resource, quiet=True):
        raise RuntimeError(f"Could not download NLTK resource: {resource}")
    for path in (f"{base_path}/", f"{base_path}.zip", base_path):
        try:
            nltk.data.find(path)
            return
        except LookupError:
            continue
    raise RuntimeError(f"NLTK reported success but resource is unavailable: {resource}")


def preprocess_text(text: str, lemmatizer: WordNetLemmatizer) -> str:
    tokens = TOKEN_PATTERN.findall(text.lower())
    if not tokens:
        raise ValueError(f"Sentence contains no alphabetic tokens: {text!r}")
    tagged_tokens = nltk.pos_tag(tokens)
    processed_tokens = []

    for token, penn_tag in tagged_tokens:
        is_negation_or_contrast = (
            token in NEGATION_AND_CONTRAST or token.endswith("n't")
        )
        if token in ENGLISH_STOP_WORDS and not is_negation_or_contrast:
            continue

        wordnet_pos = PENN_TO_WORDNET.get(penn_tag[:1], wordnet.NOUN)
        processed_tokens.append(lemmatizer.lemmatize(token, pos=wordnet_pos))

    if not processed_tokens:
        processed_tokens = [
            lemmatizer.lemmatize(
                token, pos=PENN_TO_WORDNET.get(penn_tag[:1], wordnet.NOUN)
            )
            for token, penn_tag in tagged_tokens
        ]
    return " ".join(processed_tokens)


def read_split(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as input_file:
        records = list(csv.DictReader(input_file))
    if not records or any(
        not record.get("text", "").strip()
        or record.get("label") not in {"0", "1"}
        for record in records
    ):
        raise ValueError(f"Empty or invalid dataset split: {path}")
    return records


def write_split(path: Path, records: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(
            output_file, fieldnames=("text", "processed_text", "label")
        )
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    for resource in ("wordnet", "averaged_perceptron_tagger_eng"):
        ensure_nltk_resource(resource)

    lemmatizer = WordNetLemmatizer()
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "preprocessing": [
            "lowercase",
            "regex word tokenization",
            "English stopword removal",
            "Penn Treebank POS tagging",
            "WordNet POS-aware lemmatization",
        ],
        "preserved_negation_and_contrast": sorted(NEGATION_AND_CONTRAST),
        "splits": {},
    }

    for split_name in ("train", "test"):
        input_path = INPUT_DIR / f"{split_name}.csv"
        records = read_split(input_path)
        output_records = [
            {
                "text": record["text"],
                "processed_text": preprocess_text(record["text"], lemmatizer),
                "label": record["label"],
            }
            for record in records
        ]
        output_path = OUTPUT_DIR / f"{split_name}.csv"
        write_split(output_path, output_records)
        summary["splits"][split_name] = {
            "examples": len(output_records),
            "class_counts": dict(
                sorted(Counter(record["label"] for record in output_records).items())
            ),
            "mean_tokens_before": round(
                sum(len(TOKEN_PATTERN.findall(record["text"].lower())) for record in records)
                / len(records),
                2,
            ),
            "mean_tokens_after": round(
                sum(
                    len(record["processed_text"].split())
                    for record in output_records
                )
                / len(output_records),
                2,
            ),
        }

    summary_path = OUTPUT_DIR / "preprocessing_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Preprocessed {summary['splits']['train']['examples']} training and "
        f"{summary['splits']['test']['examples']} test sentences."
    )
    print(f"Saved processed splits and summary under {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
