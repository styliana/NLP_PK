import os

import nltk
from nltk.stem import SnowballStemmer
import spacy

RESULTS_FILE = 'wyniki4_e.txt'

SAMPLE_SENTENCES = [
    'Litwo! Ojczyzno moja! ty jesteś jak zdrowie.',
    'Ile cię trzeba cenić, ten tylko się dowie, kto cię stracił.',
    'Koty biegały po zielonej łące, a psami opiekował się najlepszy weterynarz.',
]

TEST_WORDS = [
    'koty',
    'kotka',
    'kotami',
    'psami',
    'biegać',
    'uczniowie',
    'nauczyciele',
    'książkami',
    'warszawie',
    'drzewo',
    'myślałem',
    'najlepszy',
]


def load_spacy_model():
    try:
        return spacy.load('pl_core_news_sm')
    except OSError:
        from spacy.cli import download
        download('pl_core_news_sm')
        return spacy.load('pl_core_news_sm')


def format_doc_table(doc, stemmer_en):
    lines = [
        f"{'Token':<16} {'POS':<8} {'Lemat (spaCy)':<18} {'Rdzeń (Snowball EN)':<18} {'Komentarz'}",
        '-' * 80,
    ]
    for token in doc:
        if token.is_punct:
            continue
        t_text = token.text
        t_pos = token.pos_
        t_lemma = token.lemma_
        t_stem = stemmer_en.stem(t_text.lower())

        comment = ''
        if t_lemma.lower() != t_text.lower() and t_stem == t_text.lower():
            comment = 'lemat zmienił formę, stemmer EN bez zmian'
        elif t_stem != t_text.lower() and t_stem != t_lemma.lower():
            comment = f'stemmer EN uciął obcą regułą ({t_stem})'
        elif t_lemma.lower() != t_text.lower():
            comment = 'lemat sprowadził formę'

        lines.append(f"{t_text:<16} {t_pos:<8} {t_lemma:<18} {t_stem:<18} {comment}")
    return '\n'.join(lines)


def format_words_comparison(words, nlp, stemmer_en):
    lines = [
        f"{'Polskie słowo':<16} {'Lemat (spaCy)':<16} {'Snowball EN':<16} {'Ocena działania stemmera EN'}",
        '-' * 78,
    ]
    for w in words:
        doc = nlp(w)
        lemma = doc[0].lemma_ if len(doc) > 0 else w
        stem = stemmer_en.stem(w)

        if stem == w and lemma != w:
            ocena = 'Brak redukcji (nie zna polskiej końcówki)'
        elif stem != w and stem != lemma:
            ocena = f'Błędna reguła angielska ({stem})'
        elif stem == lemma:
            ocena = 'Przypadkowo zgodny'
        else:
            ocena = 'Brak zmian'

        lines.append(f"{w:<16} {lemma:<16} {stem:<16} {ocena}")
    return '\n'.join(lines)


def run_experiment():
    nlp = load_spacy_model()
    stemmer_en = SnowballStemmer('english')

    output = []
    output.append('=================================================================================')
    output.append('Część E: Polszczyzna wymaga innych narzędzi (spaCy vs SnowballStemmer)')
    output.append('=================================================================================\n')

    # 1. Tokenizacja, POS-tagging i lematyzacja fragmentu tekstu polskiego dedykowanym modelem spaCy
    output.append('--- 1. Analiza tekstu polskiego modelem spaCy (pl_core_news_sm) ---')
    output.append('Uwaga: Narzędzia dedykowane dla języka polskiego (spaCy, Stanza, Morfeusz) nie')
    output.append('stosują regułowego stemmingu, lecz pełną lematyzację opartą na analizie morfologicznej.\n')

    for idx, sentence in enumerate(SAMPLE_SENTENCES, 1):
        output.append(f'Fragment {idx}: "{sentence}"')
        doc = nlp(sentence)
        output.append(format_doc_table(doc, stemmer_en))
        output.append('')

    # 2. Zastosowanie angielskiego stemmera Snowball do polskich słów
    output.append('--- 2. Angielski stemmer (SnowballStemmer("english")) a polskie słowa ---')
    output.append('Porównanie działania lematyzatora spaCy i angielskiego stemmera na wybranych wyrazach:')
    output.append(format_words_comparison(TEST_WORDS, nlp, stemmer_en))
    output.append('')

    # Przykład rodziny słowa "kot"
    output.append('Demonstracja problemu paradygmatu ("koty", "kotka", "kotami"):')
    for w in ['koty', 'kotka', 'kotami']:
        doc = nlp(w)
        output.append(f'  {w:<10} -> lemat spaCy: {doc[0].lemma_:<8} | stemmer EN: {stemmer_en.stem(w)}')
    output.append('Wniosek: spaCy sprowadza "koty" i "kotami" do lematu "kot", natomiast')
    output.append('angielski stemmer daje 3 różne formy: "koti", "kotka", "kotami".\n')

    # 3. Lista języków obsługiwanych przez SnowballStemmer
    langs = sorted(list(SnowballStemmer.languages))
    output.append('--- 3. Języki obsługiwane przez SnowballStemmer ---')
    output.append(f'Liczba obsługiwanych języków: {len(langs)}')
    output.append('Lista: ' + ', '.join(langs))
    output.append(f'Czy język polski ("polish") jest na liście? {"TAK" if "polish" in langs else "NIE (False)"}')
    output.append('')
    output.append('Komentarz:')
    output.append('- Snowball powstał w środowisku anglosaskim (autorstwa Martina Portera) i wspiera')
    output.append('  głównie języki germańskie i romańskie o prostej strukturze fleksyjnej.')
    output.append('- Brak języka polskiego w Snowballu wynika z jego struktury: w języku wysoce fleksyjnym')
    output.append('  i fuzyjnym z powszechnymi obocznościami tematu proste obcinanie afiksów nie zdaje egzaminu.')
    output.append('- Dla języka polskiego standardem branżowym jest lematyzacja (spaCy, Stanza, Morfeusz).\n')

    return '\n'.join(output)


if __name__ == '__main__':
    report = run_experiment()
    print(report)
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        f.write(report + '\n')
