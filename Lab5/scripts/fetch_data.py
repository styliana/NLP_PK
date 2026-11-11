"""Pobranie tekstów źródłowych do Lab5.

* proza: Sherlock Holmes (Project Gutenberg) i „Lalka” t. I (Wolne Lektury),
* poezja/rap: teksty Quebonafide, Taco Hemingwaya i Jana-rapowanie z tekstowo.pl.

Teksty piosenek są chronione prawem autorskim, dlatego trafiają wyłącznie do
lokalnego katalogu ``data/`` (ignorowanego przez Git i niedołączanego do paczki)
i służą jedynie do trenowania modeli na potrzeby zajęć.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
LYRICS_DIR = RAW_DIR / "lyrics"

PROSE = {
    "sherlock.txt": "https://www.gutenberg.org/files/1661/1661-0.txt",
    "lalka1.txt": "https://wolnelektury.pl/media/book/txt/lalka-tom-pierwszy.txt",
}

BASE = "https://www.tekstowo.pl"
# autor -> (slugi katalogów na tekstowo.pl, wzorce nazw autora w nagłówkach zwrotek)
ARTISTS = {
    "quebonafide": (["quebonafide"], ["quebo", "kuba"]),
    "taco_hemingway": (["taco-hemingway"], ["taco", "filip"]),
    "jan_rapowanie": (["jan-rapowanie-2", "jan-rapowanie-nocny"], ["jan", "rapowanie"]),
}
HEADERS = {"User-Agent": "Mozilla/5.0 (Lab5 NLP student project)"}
DELAY = 0.4


def get(url: str) -> str:
    for attempt in range(4):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                response.encoding = "utf-8"
                return response.text
        except requests.RequestException:
            pass
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Nie udało się pobrać {url}")


def song_links(slug: str) -> list[str]:
    links: list[str] = []
    page = 1
    while True:
        url = f"{BASE}/{slug}" + (f"?strona={page}" if page > 1 else "")
        soup = BeautifulSoup(get(url), "html.parser")
        found = [
            a["href"]
            for a in soup.find_all("a", href=True)
            if a["href"].startswith(f"/{slug}/")
        ]
        new = [h for h in dict.fromkeys(found) if h not in links]
        if not new:
            break
        links.extend(new)
        has_next = any(f"strona={page + 1}" in a["href"] for a in soup.find_all("a", href=True))
        if not has_next:
            break
        page += 1
        time.sleep(DELAY)
    return links


def lyrics_from_page(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", class_="song-text")
    if container is None:
        return ""
    inner = container.find("div", class_="inner-text")
    if inner is None:
        return ""
    for br in inner.find_all("br"):
        br.replace_with("\n")
    return inner.get_text()


def fetch_prose() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in PROSE.items():
        path = RAW_DIR / name
        if path.exists():
            continue
        path.write_bytes(requests.get(url, headers=HEADERS, timeout=60).content)
        print(f"Pobrano {name}")


def fetch_lyrics() -> None:
    LYRICS_DIR.mkdir(parents=True, exist_ok=True)
    for artist, (slugs, _) in ARTISTS.items():
        out = LYRICS_DIR / f"{artist}.json"
        if out.exists():
            print(f"{artist}: już pobrane")
            continue
        songs = []
        for slug in slugs:
            links = song_links(slug)
            print(f"{artist}/{slug}: {len(links)} utworów")
            for href in links:
                text = lyrics_from_page(get(BASE + href))
                time.sleep(DELAY)
                if len(text.split()) < 30:
                    continue
                songs.append({"url": BASE + href, "slug": href.rsplit("/", 1)[-1], "text": text})
        out.write_text(json.dumps(songs, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{artist}: zapisano {len(songs)} tekstów")


if __name__ == "__main__":
    fetch_prose()
    fetch_lyrics()
