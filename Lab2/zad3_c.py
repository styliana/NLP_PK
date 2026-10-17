from collections import Counter

import textdistance

RESULTS_FILE = 'wyniki3_c.txt'

S1 = 'Ala ma kota'
S2 = 'Ala posiada kota'


def compute_dp_matrix(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,        # usunięcie znaku z s1
                dp[i][j - 1] + 1,        # wstawienie znaku do s1 (z s2)
                dp[i - 1][j - 1] + cost  # zamiana / dopasowanie
            )

    return dp


def backtrack_operations(s1, s2, dp):
    i, j = len(s1), len(s2)
    operations = []

    while i > 0 or j > 0:
        cost = 0 if (i > 0 and j > 0 and s1[i - 1] == s2[j - 1]) else 1

        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + cost:
            op_name = 'Zgodność' if cost == 0 else 'Zamiana'
            operations.append((op_name, s1[i - 1], s2[j - 1], cost))
            i -= 1
            j -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            operations.append(('Wstawienie', ' ', s2[j - 1], 1))
            j -= 1
        else:
            operations.append(('Usunięcie', s1[i - 1], ' ', 1))
            i -= 1

    operations.reverse()
    return operations


def format_matrix(s1, s2, dp):
    header = '        #  ' + '  '.join(f'{ch}' for ch in s2)
    lines = [header, '   ' + '-' * (len(header) - 3)]

    for i in range(len(s1) + 1):
        label = '#' if i == 0 else s1[i - 1]
        row_str = '  '.join(f'{dp[i][j]:2}' for j in range(len(s2) + 1))
        lines.append(f' {label!r:<4} {row_str}')

    return '\n'.join(lines)


def format_alignment(operations):
    line_s1 = []
    line_op = []
    line_s2 = []

    for op, c1, c2, _ in operations:
        c1_disp = c1 if c1 != ' ' else '_'
        c2_disp = c2 if c2 != ' ' else '_'

        if op == 'Zgodność':
            marker = '|'
        elif op == 'Zamiana':
            marker = '*'
        elif op == 'Wstawienie':
            c1_disp = '-'
            marker = '+'
        else:
            c2_disp = '-'
            marker = '-'

        line_s1.append(c1_disp)
        line_op.append(marker)
        line_s2.append(c2_disp)

    legend = 'Legenda wyrównania: "|" = dopasowanie (koszt 0), "*" = zamiana (koszt 1), "+" = wstawienie (koszt 1), "_" = spacja'
    return f"{''.join(line_s1)}\n{''.join(line_op)}\n{''.join(line_s2)}\n\n{legend}"


def run_analysis(s1, s2):
    output = []
    output.append('=================================================================================')
    output.append('Część C: Odległość edycyjna Levenshteina (biblioteka textdistance)')
    output.append('=================================================================================\n')
    output.append(f'Zdanie 1 (s1): "{s1}" (długość: {len(s1)} znaków)')
    output.append(f'Zdanie 2 (s2): "{s2}" (długość: {len(s2)} znaków)\n')

    # 1. Wyniki z biblioteki textdistance
    dist = textdistance.levenshtein(s1, s2)
    sim = textdistance.levenshtein.similarity(s1, s2)
    norm_dist = textdistance.levenshtein.normalized_distance(s1, s2)
    norm_sim = textdistance.levenshtein.normalized_similarity(s1, s2)

    output.append('--- 1. Wyniki biblioteki textdistance (poziom znakowy) ---')
    output.append(f'Odległość Levenshteina:          {dist}')
    output.append(f'Podobieństwo (similarity):       {sim}')
    output.append(f'Znormalizowana odległość:        {norm_dist:.4f} ({dist}/{max(len(s1), len(s2))})')
    output.append(f'Znormalizowane podobieństwo:     {norm_sim:.4f} ({sim}/{max(len(s1), len(s2))})\n')

    # 2. Rekonstrukcja operacji edycyjnych
    dp = compute_dp_matrix(s1, s2)
    ops = backtrack_operations(s1, s2, dp)
    op_counts = Counter(op[0] for op in ops)

    output.append('--- 2. Rozbicie na operacje edycyjne ---')
    output.append(f"Łączna liczba operacji edycyjnych: {dist}")
    output.append(f"  - Wstawienia (insertions):       {op_counts.get('Wstawienie', 0)}")
    output.append(f"  - Zamiany (substitutions):       {op_counts.get('Zamiana', 0)}")
    output.append(f"  - Usunięcia (deletions):         {op_counts.get('Usunięcie', 0)}")
    output.append(f"  - Zgodne znaki (matches, k=0):   {op_counts.get('Zgodność', 0)}\n")

    output.append('Krok po kroku:')
    lines_steps = [f"{'Krok':<6} {'Operacja':<12} {'Znak s1':<10} {'Znak s2':<10} {'Koszt':<6}"]
    lines_steps.append('-' * 46)
    step_num = 1
    for op, c1, c2, cost in ops:
        c1_str = repr(c1) if c1 != ' ' else "' '"
        c2_str = repr(c2) if c2 != ' ' else "' '"
        lines_steps.append(f"{step_num:<6} {op:<12} {c1_str:<10} {c2_str:<10} {cost:<6}")
        step_num += 1
    output.append('\n'.join(lines_steps))
    output.append('')

    output.append('--- 3. Wizualne wyrównanie ciągów (alignment) ---')
    output.append(format_alignment(ops))
    output.append('')

    output.append('--- 4. Macierz programowania dynamicznego (Levenshtein) ---')
    output.append(format_matrix(s1, s2, dp))
    output.append('')

    # 5. Porównanie z poziomem słów (tokenów)
    words1 = s1.split()
    words2 = s2.split()
    word_dist = textdistance.levenshtein(words1, words2)
    word_sim = textdistance.levenshtein.similarity(words1, words2)

    output.append('--- 5. Poziom wyrazów (tokenów) dla porównania ---')
    output.append(f'Tokeny s1: {words1}')
    output.append(f'Tokeny s2: {words2}')
    output.append(f'Odległość Levenshteina na poziomie słów: {word_dist}')
    output.append(f'Podobieństwo na poziomie słów:          {word_sim}')
    output.append('Wyjaśnienie: na poziomie słów następuje tylko 1 operacja: zamiana słowa "ma" -> "posiada".\n')

    return '\n'.join(output)


if __name__ == '__main__':
    report = run_analysis(S1, S2)
    print(report)
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        f.write(report + '\n')
