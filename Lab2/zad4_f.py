import textdistance

RESULTS_FILE = 'wyniki4_f.txt'

MEASURES = [
    ('Levenshtein', textdistance.levenshtein, 'Odległość edycyjna: wstawienie, usunięcie, zamiana'),
    ('Damerau-Levenshtein', textdistance.damerau_levenshtein, 'Edycyjna + transpozycja sąsiednich znaków'),
    ('Jaro-Winkler', textdistance.jaro_winkler, 'Zgodność znaków w oknie + waga wspólnego prefiksu'),
    ('Jaccard', textdistance.jaccard, 'Miara zbiorowa: |A & B| / |A | B| (ignoruje kolejnosc)'),
]

PAIRS = [
    ('Ala ma kota', 'Ala posiada kota', 'Para bazowa z zadania (wymiana/rozbudowa słowa)'),
    ('kot', 'kto', 'Przestawione sąsiednie litery (transpozycja)'),
    ('Kraków', 'Krakow', 'Różnica tylko w diakrytykach (ó vs o)'),
    ('profesor', 'proffesor', 'Literówka (podwojona litera / wstawienie)'),
    ('kot w butach', 'butach w kot', 'Przestawienie wyrazów (inna kolejność słów)'),
]


def format_table_raw(pairs, measures):
    col_names = ['Levenshtein', 'Damerau-Lev', 'Jaro-Winkler', 'Jaccard']
    header = f"{'Para napisów':<38} " + ''.join(f"{name:>16}" for name in col_names)
    lines = [header, '-' * len(header)]

    for s1, s2, _ in pairs:
        label = f'"{s1}" / "{s2}"'
        row = [f"{label:<38}"]
        for _, m, _ in measures:
            dist = m.distance(s1, s2)
            if isinstance(dist, float):
                row.append(f"{dist:>16.4f}")
            else:
                row.append(f"{dist:>16}")
        lines.append(''.join(row))

    return '\n'.join(lines)


def format_table_norm(pairs, measures):
    col_names = ['Levenshtein', 'Damerau-Lev', 'Jaro-Winkler', 'Jaccard']
    header = f"{'Para napisów':<38} " + ''.join(f"{name:>16}" for name in col_names) + f"{'Rozstęp (max-min)':>20}"
    lines = [header, '-' * len(header)]

    discrepancies = []

    for s1, s2, desc in pairs:
        label = f'"{s1}" / "{s2}"'
        row = [f"{label:<38}"]
        sims = []
        for _, m, _ in measures:
            nsim = m.normalized_similarity(s1, s2)
            sims.append(nsim)
            row.append(f"{nsim:>16.4f}")

        spread = max(sims) - min(sims)
        row.append(f"{spread:>20.4f}")
        lines.append(''.join(row))
        discrepancies.append((spread, s1, s2, desc, sims))

    return '\n'.join(lines), discrepancies


def run_experiment():
    output = []
    output.append('=================================================================================')
    output.append('Część F: Więcej miar podobieństwa napisów (biblioteka textdistance)')
    output.append('=================================================================================\n')

    output.append('--- 1. Wybrane miary podobieństwa i zasada ich działania ---\n')
    for idx, (name, _, desc) in enumerate(MEASURES, 1):
        output.append(f'{idx}. {name}:')
        output.append(f'   Opis: {desc}')
    output.append('')

    output.append('--- 2. Surowe odległości (distance) ---')
    output.append(format_table_raw(PAIRS, MEASURES))
    output.append('')

    output.append('--- 3. Znormalizowane podobieństwo (normalized_similarity w przedziale [0, 1]) ---')
    table_norm, discrepancies = format_table_norm(PAIRS, MEASURES)
    output.append(table_norm)
    output.append('')

    output.append('--- 4. Szczegółowe zestawienie dla każdej badanej pary ---\n')
    for s1, s2, desc in PAIRS:
        output.append(f'Para: "{s1}"  vs  "{s2}"')
        output.append(f'Typ testu: {desc}')
        output.append(f"{'Miara':<22} {'Odległość':>12} {'Podobieństwo':>14} {'Znorm. podobieństwo':>22}")
        output.append('-' * 74)
        for name, m, _ in MEASURES:
            dist = m.distance(s1, s2)
            sim = m.similarity(s1, s2)
            nsim = m.normalized_similarity(s1, s2)
            dist_str = f"{dist:.4f}" if isinstance(dist, float) else f"{dist}"
            sim_str = f"{sim:.4f}" if isinstance(sim, float) else f"{sim}"
            output.append(f"{name:<22} {dist_str:>12} {sim_str:>14} {nsim:>22.4f}")
        output.append('')

    output.append('--- 5. Analiza największych rozbieżności między miarami ---')
    discrepancies.sort(key=lambda x: -x[0])
    for rank, (spread, s1, s2, desc, sims) in enumerate(discrepancies, 1):
        output.append(f'{rank}. Para "{s1}" / "{s2}" ({desc}): rozstęp miar = {spread:.4f}')

    max_pair = discrepancies[0]
    output.append(f'\nPara o NAJWIĘKSZEJ rozbieżności miar: "{max_pair[1]}" / "{max_pair[2]}" (rozstęp: {max_pair[0]:.4f})')
    output.append('Wyjaśnienie dlaczego:')
    output.append('- Jaccard traktuje napisy jako zbiory znaków, całkowicie ignorując kolejność liter/słów.')
    output.append('  Dla anagramów i przestawień daje podobieństwo 1.0000 (identyczne zbiory liter).')
    output.append('- Klasyczny Levenshtein operuje na pozycjach i wymaga sekwencji wielu usunięć i wstawień,')
    output.append('  przez co uznaje te napisy za niemal zupełnie odmienne (podobieństwo bliskie 0).')
    output.append('- Podobny silny kontrast widać dla pary "kot" / "kto" (Damerau=0.6667, Jaccard=1.0000 vs Levenshtein=0.3333).\n')

    return '\n'.join(output)


if __name__ == '__main__':
    report = run_experiment()
    print(report)
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        f.write(report + '\n')
