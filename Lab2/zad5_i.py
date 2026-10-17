import os
import re

import spacy
from stop_words import get_stop_words
from tokenizers import Tokenizer

RESULTS_FILE = 'wyniki5_i.txt'
TOKENIZER_FILE = 'tokenizer_pl.json'
CORPUS_FILE = 'books/pan-tadeusz.txt'

INWOKACJA = """
Litwo! Ojczyzno moja! ty jesteś jak zdrowie.
Ile cię trzeba cenić, ten tylko się dowie,
Kto cię stracił. Dziś piękność twą w całej ozdobie
Widzę i opisuję, bo tęsknię po tobie.
Panno Święta, co Jasnej bronisz Częstochowy
I w Ostrej świecisz Bramie! Ty, co gród zamkowy
Nowogródzki ochraniasz z jego wiernym ludem!
Jak mnie dziecko do zdrowia powróciłaś cudem,
(Gdy od płaczącej matki pod Twoją opiekę
Ofiarowany, martwą podniosłem powiekę
I zaraz mogłem pieszo do Twych świątyń progu
Iść za wrócone życie podziękować Bogu),
Tak nas powrócisz cudem na Ojczyzny łono.
Tymczasem przenoś moją duszę utęsknioną
Do tych pagórków leśnych, do tych łąk zielonych,
Szeroko nad błękitnym Niemnem rozciągnionych;
Do tych pól malowanych zbożem rozmaitem,
Wyzłacanych pszenicą, posrebrzanych żytem;
Gdzie bursztynowy świerzop, gryka jak śnieg biała,
Gdzie panieńskim rumieńcem dzięcielina pała,
A wszystko przepasane, jakby wstęgą, miedzą
Zieloną, na niej z rzadka ciche grusze siedzą.
""".strip()


def load_tools():
    nlp = spacy.load('pl_core_news_sm')
    stop_list = set(get_stop_words('polish'))
    tokenizer = Tokenizer.from_file(TOKENIZER_FILE)
    return nlp, stop_list, tokenizer


def process_text_variants(text, nlp, stop_list, tokenizer):
    # 1. same wyrazy (tokeny alfanumeryczne w małych literach)
    doc = nlp(text)
    words = [t.text.lower() for t in doc if t.is_alpha]

    # 2. wyrazy po lematyzacji
    lemmas = [t.lemma_.lower() for t in doc if t.is_alpha]

    # 3. wyrazy bez stop words
    words_no_stop = [w for w in words if w not in stop_list]

    # 4. tokeny podsłowowe z własnego tokenizatora BPE
    # kodujemy tekst złączonych wyrazów, aby porównywać ten sam materiał leksykalny
    enc = tokenizer.encode(' '.join(words))
    subwords = [tokenizer.decode([i]).strip() for i in enc.ids]
    # usuwamy ewentualne puste elementy powstałe przy dekodowaniu
    subwords = [sw for sw in subwords if sw]

    return {
        'same wyrazy': words,
        'wyrazy po lematyzacji': lemmas,
        'wyrazy bez stop words': words_no_stop,
        'tokeny podslowowe (BPE)': subwords,
    }


def format_token_mapping_table(text, nlp, stop_list, tokenizer, limit=35):
    doc = nlp(text)
    alpha_tokens = [t for t in doc if t.is_alpha]

    header = f"{'Lp.':<5} {'Oryginalny wyraz':<20} {'Lemat (spaCy)':<20} {'Bez stop words':<20} {'Tokeny BPE':<25}"
    lines = [header, '-' * len(header)]

    for idx, token in enumerate(alpha_tokens[:limit], 1):
        w = token.text.lower()
        lem = token.lemma_.lower()
        no_stop = w if w not in stop_list else '[USUNIĘTE]'
        bpe_pieces = [tokenizer.decode([i]).strip() for i in tokenizer.encode(token.text).ids]
        bpe_str = ' | '.join(p for p in bpe_pieces if p)

        lines.append(f"{idx:<5} {w:<20} {lem:<20} {no_stop:<20} {bpe_str:<25}")

    if len(alpha_tokens) > limit:
        lines.append(f"... (pokazano {limit} z {len(alpha_tokens)} wyrazów)")

    return '\n'.join(lines)


def format_stats_table(variants, base_key='same wyrazy'):
    base_units = len(variants[base_key])
    base_vocab = len(set(variants[base_key]))

    header = (
        f"{'Wariant przetwarzania':<28} "
        f"{'Liczba jednostek':>18} "
        f"{'Rozmiar słownika':>18} "
        f"{'TTR':>8} "
        f"{'Jedn./wyraz':>12} "
        f"{'Zmiana słownika':>18}"
    )
    lines = [header, '-' * len(header)]

    for name, units in variants.items():
        n_units = len(units)
        vocab_size = len(set(units))
        ttr = vocab_size / n_units if n_units > 0 else 0
        ratio = n_units / base_units if base_units > 0 else 0
        vocab_change = ((vocab_size - base_vocab) / base_vocab) * 100

        change_str = f"{vocab_change:+.1f}%" if name != base_key else "0.0% (baza)"

        lines.append(
            f"{name:<28} "
            f"{n_units:>18} "
            f"{vocab_size:>18} "
            f"{ttr:>8.3f} "
            f"{ratio:>12.2f} "
            f"{change_str:>18}"
        )

    return '\n'.join(lines)


def run_comparison():
    nlp, stop_list, tokenizer = load_tools()

    output = []
    output.append('=================================================================================')
    output.append('Część I: Porównanie wszystkich metod przetwarzania tekstu polskiego')
    output.append('=================================================================================\n')

    output.append('Badany materiał: fragment "Pana Tadeusza" (Inwokacja - 22 wersy).')
    output.append('Metody przetwarzania:')
    output.append('  1. Same wyrazy: czysta tokenizacja słowna (małe litery, bez interpunkcji)')
    output.append('  2. Wyrazy po lematyzacji: sprowadzenie form fleksyjnych do formy bazowej (spaCy pl_core_news_sm)')
    output.append('  3. Wyrazy bez stop words: odfiltrowanie słów funkcyjnych (biblioteka stop-words)')
    output.append('  4. Tokeny podsłowowe: tokenizacja BPE z własnego tokenizatora (5 000 tokenów, część H)\n')

    # Przetwarzanie Inwokacji
    variants_inw = process_text_variants(INWOKACJA, nlp, stop_list, tokenizer)

    output.append('--- 1. Tabela porównawcza jednostek dla fragmentu tekstu (Inwokacja) ---')
    output.append(format_token_mapping_table(INWOKACJA, nlp, stop_list, tokenizer, limit=30))
    output.append('')

    output.append('--- 2. Tabela statystyk: liczba jednostek i rozmiar słownika (Inwokacja) ---')
    output.append(format_stats_table(variants_inw))
    output.append('')

    # Skala makro: pierwsze 2000 wyrazów z Pana Tadeusza (dla rzetelności statystycznej)
    if os.path.exists(CORPUS_FILE):
        with open(CORPUS_FILE, 'r', encoding='utf-8') as f:
            corpus_raw = f.read()
        # bierzemy fragment ok. 2000 słów z początku utworu
        corpus_words = corpus_raw.split()[:2000]
        corpus_excerpt = ' '.join(corpus_words)
        variants_corpus = process_text_variants(corpus_excerpt, nlp, stop_list, tokenizer)

        output.append('--- 3. Tabela statystyk w większej skali (próbka 2 000 wyrazów z Pana Tadeusza) ---')
        output.append(format_stats_table(variants_corpus))
        output.append('')

    output.append('--- 4. Podsumowanie i wnioski ---')
    output.append('Szczegółowy komentarz, analiza kosztów i wnioski znajdują się w pliku odpowiedzi5_i.txt.\n')

    return '\n'.join(output)


if __name__ == '__main__':
    report = run_comparison()
    print(report)
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        f.write(report + '\n')
