import re
from collections import Counter, defaultdict

import nltk
from nltk.stem import LancasterStemmer, PorterStemmer, WordNetLemmatizer

for resource in ('punkt_tab', 'wordnet'):
    nltk.download(resource, quiet=True)

RESULTS_FILE = 'wyniki4_d.txt'
TOP = 25


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


def lemma(word, lemmatizer):
    # bez kontekstu nie znamy części mowy - bierzemy pierwszą, która zmienia słowo
    for pos in ('v', 'n', 'a', 'r'):
        lem = lemmatizer.lemmatize(word, pos=pos)
        if lem != word:
            return lem
    return word


def compare_table(words, freq, stemmers):
    names = list(stemmers)
    lines = [f"{'słowo':<16} {'liczba':>6}  " + ''.join(f'{n:<14}' for n in names),
             '-' * (24 + 14 * len(names))]
    for w in words:
        lines.append(f'{w:<16} {freq[w]:>6}  ' + ''.join(f'{s.stem(w):<14}' for s in stemmers.values()))
    return '\n'.join(lines)


def overstemming(vocab, freq, stemmer, lemmatizer):
    # nadmierne obcinanie: ten sam rdzeń, ale słowa o różnych lematach,
    # z których żaden nie jest przedłużeniem drugiego (to nie ta sama rodzina słów)
    groups = defaultdict(set)
    for w in vocab:
        groups[stemmer.stem(w)].add(w)
    found = []
    for stem, words in groups.items():
        lemmas = {lemma(w, lemmatizer) for w in words}
        if len(lemmas) < 2:
            continue
        if any(a != b and (a.startswith(b) or b.startswith(a)) for a in lemmas for b in lemmas):
            continue
        found.append((stem, sorted(words, key=lambda w: -freq[w])))
    found.sort(key=lambda g: -sum(freq[w] for w in g[1]))
    return found


def understemming(vocab, freq, stemmer, lemmatizer):
    # niedostateczne obcinanie: ten sam lemat, ale różne rdzenie
    groups = defaultdict(set)
    for w in vocab:
        groups[lemma(w, lemmatizer)].add(w)
    found = []
    for lem, words in groups.items():
        stems = {stemmer.stem(w) for w in words}
        if len(stems) > 1:
            found.append((lem, sorted(words, key=lambda w: -freq[w])))
    found.sort(key=lambda g: -sum(freq[w] for w in g[1]))
    return found


def format_groups(groups, stemmer, title):
    lines = [title]
    for key, words in groups[:TOP]:
        lines.append(f'  {key:<14} ' + ', '.join(f'{w} -> {stemmer.stem(w)}' for w in words))
    return '\n'.join(lines)


hamlet = read_book('books/hamlet-en.txt')
hamlet = clean_play(strip_gutenberg(hamlet))
tokens = [t.lower() for t in nltk.word_tokenize(hamlet, language='english')]
freq = Counter(t for t in tokens if t.isalpha() and len(t) > 2)
vocab = list(freq)

stemmers = {'Porter': PorterStemmer(), 'Lancaster': LancasterStemmer()}
porter, lancaster = stemmers.values()
lemmatizer = WordNetLemmatizer()

different = [w for w, _ in freq.most_common() if porter.stem(w) != lancaster.stem(w)]

output = [
    f'Słownik tekstu: {len(vocab)} różnych słów (małe litery, min. 3 znaki)',
    f'Porter i Lancaster dają różne rdzenie dla {len(different)} słów '
    f'({len(different) / len(vocab):.1%})',
    f"Liczba różnych rdzeni: Porter {len({porter.stem(w) for w in vocab})}, "
    f"Lancaster {len({lancaster.stem(w) for w in vocab})}",
    '',
    f'--- {TOP} najczęstszych słów z różnymi rdzeniami ---',
    compare_table(different[:TOP], freq, stemmers),
    '',
]
for name, stemmer in stemmers.items():
    output.append(format_groups(overstemming(vocab, freq, stemmer, lemmatizer), stemmer,
                                f'--- {name}: nadmierne obcinanie (różne słowa, ten sam rdzeń) ---'))
    output.append('')
    output.append(format_groups(understemming(vocab, freq, stemmer, lemmatizer), stemmer,
                                f'--- {name}: niedostateczne obcinanie (ten sam lemat, różne rdzenie) ---'))
    output.append('')

report = '\n'.join(output)
print(report)
with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
    f.write(report + '\n')
