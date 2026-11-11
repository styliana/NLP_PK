"""Preprocessing tekstów do Lab5.

* usunięcie nagłówków/stopek serwisów (Gutenberg, Wolne Lektury),
* podział prozy na zdania (punkt NLTK), poezji/rapu — na wersy,
* lowercase, interpunkcja jako osobne tokeny.

Wynik: ``data/processed/{en,pl,poetry}.json`` — listy zdań/wersów jako listy tokenów.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import nltk

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

TOKEN_RE = re.compile(r"\w+(?:['’\-]\w+)*|[^\w\s]", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def ensure_punkt() -> None:
    try:
        nltk.data.find("tokenizers/punkt_tab/polish")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("﻿", "")
    return text.replace(" ", " ")


# ----------------------------------------------------------------------- proza
def clean_sherlock(text: str) -> list[str]:
    start = text.index("*** START OF")
    end = text.index("*** END OF")
    body = text[text.index("\n", start) : end]
    # pomijamy spis treści — tekst zaczyna się od drugiego nagłówka pierwszego opowiadania
    first = body.index("To Sherlock Holmes she is always")
    body = body[body.rindex("I. A SCANDAL IN BOHEMIA", 0, first) :]
    body = body.replace("_", "")
    paragraphs = [" ".join(p.split()) for p in re.split(r"\n\s*\n", body)]
    return [p for p in paragraphs if p]


def clean_lalka(text: str) -> list[str]:
    body = text[: text.index("\n-----\n")]
    body = body[body.index("Tom I") + len("Tom I") :]
    paragraphs = [" ".join(p.split()) for p in body.split("\n")]
    return [p for p in paragraphs if p]


CHAPTER_RE = re.compile(r"^[IVXLC]+\.\s")


def split_sentences(paragraphs: list[str], language: str) -> list[list[str]]:
    sentences = []
    for paragraph in paragraphs:
        if CHAPTER_RE.match(paragraph) and len(paragraph) < 120:
            continue  # tytuły rozdziałów („I. A SCANDAL IN BOHEMIA”)
        for sentence in nltk.sent_tokenize(paragraph, language=language):
            tokens = tokenize(sentence)
            if tokens:
                sentences.append(tokens)
    return sentences


# ---------------------------------------------------------------------- poezja
HEADER_RE = re.compile(r"^\s*[\[\(<{]([^\]\)>}]*)[\]\)>}]\s*:?\s*$")
INLINE_TAG_RE = re.compile(r"\[[^\]]*\]|\{[^}]*\}")
REPEAT_RE = re.compile(r"\(?\s*[x×]\s*\d+\s*\)?\s*$|\(?\s*\d+\s*[x×]\s*\)?\s*$", re.IGNORECASE)
SECTION_WORDS = ("zwrotka", "zwortka", "refren", "ref", "hook", "intro", "outro", "bridge", "verse",
                 "chorus", "przedrefren", "przed-refren", "pre-refren", "pre", "pre-intro", "interlude",
                 "post-refren", "break", "x2", "skit")
FOOTNOTE_RE = re.compile(r"\*[^*]*\*")


def is_header(line: str) -> bool:
    """Nagłówek sekcji bez nawiasów, np. „Refren: Sentino”, „2 zwrotka:”, „ref. 3-6”."""
    words = re.sub(r"[^\w\s:\-]", " ", line.lower()).split()
    words = [w for w in words if not w.isdigit()]
    if not words:
        return False
    first = words[0].rstrip(":")
    return first in SECTION_WORDS and (":" in line or len(words) <= 3)


def clean_song(raw: str, own_names: list[str]) -> list[str]:
    """Zwraca wersy utworu; pomija zwrotki gości oznaczone w nagłówku [Zwrotka: X]."""
    lines: list[str] = []
    keep = True
    for line in normalize(raw).split("\n"):
        line = line.strip()
        if not line:
            continue
        header = HEADER_RE.match(line)
        if line.startswith("*"):
            continue  # przypisy redakcyjne serwisu („* acne - szwedzka marka…”)
        if header or is_header(line):
            label = (header.group(1) if header else line).lower()
            if ":" in label or " - " in label or " – " in label:
                who = re.split(r":| - | – ", label, maxsplit=1)[1]
                keep = (not who.strip()) or any(name in who for name in own_names)
            elif any(word in label for word in SECTION_WORDS):
                keep = True
            # pozostałe linie w nawiasach (ad-liby, „(2x)”) są pomijane bez zmiany sekcji
            continue
        if not keep:
            continue
        line = FOOTNOTE_RE.sub("", INLINE_TAG_RE.sub("", line)).replace("*", "")
        line = REPEAT_RE.sub("", line).strip()
        if len(tokenize(line)) >= 2:
            lines.append(line)
    # refreny powtarzają się wielokrotnie — każdy wers liczymy raz w obrębie utworu
    return list(dict.fromkeys(lines))


def load_poetry() -> dict[str, list[list[str]]]:
    if __package__:
        from .fetch_data import ARTISTS
    else:
        from fetch_data import ARTISTS
    corpus = {}
    for artist, (_, names) in ARTISTS.items():
        songs = json.loads((RAW / "lyrics" / f"{artist}.json").read_text(encoding="utf-8"))
        seen_lines: set[str] = set()
        seen_songs: set[str] = set()
        lines = []
        for song in songs:
            song_lines = clean_song(song["text"], names)
            fingerprint = " ".join(song_lines[:4]).lower()
            if not song_lines or fingerprint in seen_songs:
                continue  # duplikaty (np. remiksy/blendy z identycznym tekstem)
            seen_songs.add(fingerprint)
            for line in song_lines:
                key = line.lower()
                if key in seen_lines:
                    continue
                seen_lines.add(key)
                lines.append(tokenize(line))
        corpus[artist] = {"songs": len(seen_songs), "lines": lines}
    return corpus


def main() -> None:
    ensure_punkt()
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}

    en = split_sentences(clean_sherlock(normalize((RAW / "sherlock.txt").read_text(encoding="utf-8"))), "english")
    pl = split_sentences(clean_lalka(normalize((RAW / "lalka1.txt").read_text(encoding="utf-8"))), "polish")
    for name, data in [("en", en), ("pl", pl)]:
        (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        summary[name] = {
            "sentences": len(data),
            "tokens": sum(len(s) for s in data),
            "words": sum(1 for s in data for t in s if any(c.isalnum() for c in t)),
            "types": len({t for s in data for t in s}),
        }

    poetry = load_poetry()
    (OUT / "poetry.json").write_text(json.dumps(poetry, ensure_ascii=False), encoding="utf-8")
    summary["poetry"] = {
        artist: {
            "songs": d["songs"],
            "lines": len(d["lines"]),
            "tokens": sum(len(l) for l in d["lines"]),
            "types": len({t for l in d["lines"] for t in l}),
        }
        for artist, d in poetry.items()
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
