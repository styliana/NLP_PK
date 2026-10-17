import re

import nltk
from nltk.corpus import wordnet
from nltk.stem import PorterStemmer, WordNetLemmatizer

for resource in ('punkt_tab', 'wordnet', 'averaged_perceptron_tagger_eng'):
    nltk.download(resource, quiet=True)

RESULTS_FILE = 'wyniki3_b.txt'

CHOSEN = [
    'Neither a borrower',
    'more things in heaven',
    'The lady doth protest',
    'Frailty, thy name',
    'The slings and arrows',
]


def read_book(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f'File {filename} not found')
        return None


def strip_gutenberg(book):
    # zostawiamy tylko treść między znacznikami START/END Project Gutenberg
    start = book.find('*** START OF')
    end = book.find('*** END OF')
    if start != -1:
        book = book[book.find('\n', start) + 1:]
        end = book.find('*** END OF')
    if end != -1:
        book = book[:end]
    return book


def clean_play(book):
    book = re.sub(r'\[\d+\]', '', book)              # odnośniki do przypisów, np. [77]
    book = re.sub(r'_[A-Z][a-z]*\._', '', book)      # oznaczenia mówiących, np. _Ham._
    book = re.sub(r'--+', ' ', book)                 # myślniki z podwójnych łączników
    book = book.replace('_', '')                     # znaczniki kursywy
    book = re.sub(r'\s+', ' ', book)
    return book.strip()


def choose_sentences(book):
    sentences = nltk.sent_tokenize(book, language='english')
    chosen = []
    for phrase in CHOSEN:
        chosen.append(next(s for s in sentences if phrase in s))
    return chosen


def wordnet_pos(tag):
    # tagi Penn Treebank -> części mowy WordNetu (domyślnie rzeczownik)
    if tag.startswith('J'):
        return wordnet.ADJ
    if tag.startswith('V'):
        return wordnet.VERB
    if tag.startswith('R'):
        return wordnet.ADV
    return wordnet.NOUN


def process(sentence, stemmer, lemmatizer):
    tokens = nltk.word_tokenize(sentence, language='english')
    tagged = nltk.pos_tag(tokens)
    rows = []
    for token, tag in tagged:
        if not any(ch.isalpha() for ch in token):
            continue  # pomijamy interpunkcję
        stem = stemmer.stem(token)
        lemma = lemmatizer.lemmatize(token.lower(), pos=wordnet_pos(tag))
        rows.append((token, tag, stem, lemma))
    return rows


def format_table(rows):
    lines = [f"{'token':<14} {'POS':<5} {'rdzeń (Porter)':<16} {'lemat (WordNet)':<16}",
             '-' * 60]
    for token, tag, stem, lemma in rows:
        mark = '  <-- różne' if stem != lemma else ''
        lines.append(f"{token:<14} {tag:<5} {stem:<16} {lemma:<16}{mark}")
    return '\n'.join(lines)


hamlet = read_book('books/hamlet-en.txt')
hamlet = clean_play(strip_gutenberg(hamlet))
sentences = choose_sentences(hamlet)

stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()

output = []
differences = {}
for i, sentence in enumerate(sentences, 1):
    rows = process(sentence, stemmer, lemmatizer)
    output.append(f'Zdanie {i}: {sentence}\n\n{format_table(rows)}\n')
    for token, _, stem, lemma in rows:
        if stem != lemma:
            differences.setdefault(token.lower(), (stem, lemma))

output.append(f'Słowa, dla których stemming i lematyzacja dały różne wyniki ({len(differences)}):')
for token, (stem, lemma) in differences.items():
    output.append(f'  {token:<14} rdzeń: {stem:<14} lemat: {lemma}')

report = '\n'.join(output)
print(report)
with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
    f.write(report + '\n')
