# Laboratorium NLP – Moduł Lab2: Od tekstu do tokenów
> **Ocena docelowa: 5.0 | Projekt: n-gramy, sprowadzanie form, odległość edycyjna i tokenizacja podsłowowa (BPE)**

---

## 1. O projekcie

Moduł `Lab2` stanowi realizację drugiego laboratorium z przedmiotu **Przetwarzanie Języka Naturalnego (NLP)** na Politechnice Krakowskiej.

Celem laboratorium jest przejście kompletnej ścieżki przetwarzania tekstu – od surowego pliku tekstowego do jednostek podsłowowych (*subwords*), na których operują współczesne modele językowe (LLM):
1. **Czyszczenie i tokenizacja**: normalizacja tekstu, podział na zdania i słowa, ekstrakcja n-gramów oraz badanie rozkładów częstości (prawo Zipfa).
2. **Sprowadzanie form wyrazowych**: porównanie algorytmicznego stemmingu (Porter, Lancaster, Snowball) z lematyzacją morfosyntaktyczną (WordNet, spaCy `pl_core_news_sm`).
3. **Mierzenie podobieństwa napisów**: badanie odległości edycyjnych i metryk podobieństwa (Levenshtein, Damerau-Levenshtein, Jaro-Winkler, Jaccard).
4. **Filtrowanie i ekstrakcja regułowa**: eliminacja słów funkcyjnych (*stop words*) oraz detekcja nazw własnych z wykorzystaniem wyrażeń regularnych (RegEx z asercjami wstecznymi *lookbehind*).
5. **Tokenizacja podsłowowa BPE**: wytrenowanie od zera własnego tokenizatora BPE (*Byte-Pair Encoding*) w bibliotece `tokenizers` (Hugging Face) dla różnych rozmiarów słownika, benchmarking z modelami `gpt2`, `allegro/herbert-base-cased` i `speakleash/Bielik-1.5B-v3` oraz ilościowe zbadanie zjawiska **podatku językowego** (*language tax*).
6. **Synteza metod**: wielowymiarowe porównanie czterech paradygmatów reprezentacji tekstu (surowe wyrazy, lematy, tekst bez stop words, tokeny podsłowowe BPE).

### Badane korpusy tekstowe
- **Język polski**: Adam Mickiewicz, *Pan Tadeusz* ([Wolne Lektury](https://wolnelektury.pl/media/book/txt/pan-tadeusz.txt)) – 68 185 wyrazów, 18 763 unikalnych form, 3 827 zdań.
- **Język angielski**: William Shakespeare, *Hamlet* ([Project Gutenberg](https://www.gutenberg.org/ebooks/27761)) – 4 505 unikalnych słów w słowniku dramatu.

Wszystkie narzędzia są w pełni darmowe, otwarte i uruchamiane w 100% lokalnie.

---

## 2. Szybki start

### Wymagania wstępne
Zainstalowane środowisko Python 3.10+ oraz wymagane pakiety:
```powershell
pip install nltk stop-words spacy matplotlib textdistance tokenizers transformers sentencepiece
python -m spacy download pl_core_news_sm
```

### Uruchomienie poszczególnych zadań

Każda część laboratorium posiada autonomiczny skrypt generujący raporty tekstowe oraz wykresy:

```powershell
# Poziom 3.0 (Wymagania bazowe)
python Lab2/zad3_a.py    # Część A: n-gramy, rozkład Zipfa ("Pan Tadeusz")
python Lab2/zad3_b.py    # Część B: stemming (Porter) vs lematyzacja (WordNet) w Hamlecie
python Lab2/zad3_c.py    # Część C: odległość Levenshteina ("Ala ma kota" vs "Ala posiada kota")

# Poziom 4.0 (Wymagania rozszerzone)
python Lab2/zad4_d.py    # Część D: porównanie stemmerów Porter vs Lancaster (over/understemming)
python Lab2/zad4_e.py    # Część E: spaCy pl_core_news_sm vs angielski Snowball na polszczyźnie
python Lab2/zad4_f.py    # Część F: 4 miary podobieństwa (Levenshtein, Damerau, Jaro-Winkler, Jaccard)

# Poziom 5.0 (Wymagania najwyższe)
python Lab2/zad5_g.py    # Część G: stop words i ekstrakcja nazw własnych RegEx-em
python Lab2/zad5_h.py    # Część H: trening tokenizatora BPE (1k/5k/30k), benchmark LLM i podatek językowy
python Lab2/zad5_i.py    # Część I: wielowymiarowe porównanie 4 metod reprezentacji tekstu
```

---

## 3. Architektura plików projektu

```text
Lab2/
├── Lab2.pdf                  # Oficjalne wymagania i instrukcja laboratoryjna
├── README.md                 # Niniejsza kompleksowa dokumentacja modułu
│
├── books/                    # Badane teksty źródłowe w domenie publicznej:
│   ├── pan-tadeusz.txt       # Adam Mickiewicz, "Pan Tadeusz" (Wolne Lektury)
│   └── hamlet-en.txt         # William Shakespeare, "Hamlet" (Project Gutenberg)
│
├── W3_przyklady/             # Przykłady referencyjne z Wykładu 3 (example_01.py – example_18.py)
│   └── requirements.txt      # Wykaz pakietów referencyjnych
│
├── zad3_a.py                 # Skrypt zadania 3A (n-gramy, tokenizacja, rozkłady)
├── zad3_b.py                 # Skrypt zadania 3B (stemming vs lematyzacja w j. angielskim)
├── zad3_c.py                 # Skrypt zadania 3C (odległość edycyjna Levenshteina)
├── zad4_d.py                 # Skrypt zadania 4D (porównanie stemmerów Porter vs Lancaster)
├── zad4_e.py                 # Skrypt zadania 4E (analiza polszczyzny: spaCy vs Snowball)
├── zad4_f.py                 # Skrypt zadania 4F (4 miary podobieństwa w textdistance)
├── zad5_g.py                 # Skrypt zadania 5G (usuwanie stop words i nazwy własne RegEx)
├── zad5_h.py                 # Skrypt zadania 5H (uczenie BPE, benchmark tokenizatorów)
├── zad5_i.py                 # Skrypt zadania 5I (porównanie wszystkich 4 metod przetwarzania)
│
├── odpowiedzi3_a.txt         # Odpowiedzi teoretyczne i interpretacja wyników dla zadania 3A
├── odpowiedzi3_b.txt         # Zestawienie 22 słów o rozbieżnych formach w zadaniu 3B
├── odpowiedzi3_c.txt         # Analityczny rozkład operacji edycyjnych w zadaniu 3C
├── odpowiedzi4_d.txt         # Analiza overstemmingu i understemmingu w zadaniu 4D
├── odpowiedzi4_e.txt         # Analiza fleksyjna polszczyzny i brak polskiego w Snowballu (4E)
├── odpowiedzi4_f.txt         # Zasady działania metryk i analiza par testowych (4F)
├── odpowiedzi5_g.txt         # Raport z filtracji stop words i detekcji nazw własnych (5G)
├── odpowiedzi5_h.txt         # Analiza BPE, rozmiarów słownika, benchmarku i podatku językowego (5H)
├── odpowiedzi5_i.txt         # Zbiorcze zestawienie i trade-off słownik vs długość sekwencji (5I)
│
├── wyniki3_b.txt             # Tabela token -> rdzeń -> lemat dla 5 zdań z Hamleta
├── wyniki3_c.txt             # Numeryczne wyniki textdistance i macierz programowania dynamicznego
├── wyniki4_d.txt             # Pełne zestawienie 1805 rozbieżnych słów (Porter vs Lancaster)
├── wyniki4_e.txt             # Wyniki spaCy vs Snowball dla polszczyzny oraz lista języków
├── wyniki4_f.txt             # Wyniki 4 miar podobieństwa dla wszystkich badanych par zdań
├── wyniki5_h.txt             # Liczba tokenów na zdanie (GPT-2, HerBERT, Bielik, BPE) i podziały słów
├── wyniki5_i.txt             # Tabela jednostka-po-jednostce oraz statystyki leksykalne dla 4 metod
│
├── tokenizer_pl.json         # Wytrenowany tokenizator BPE (rozmiar słownika: 5 000)
├── tokenizer_pl_1000.json    # Wytrenowany tokenizator BPE (rozmiar słownika: 1 000)
├── tokenizer_pl_30000.json   # Wytrenowany tokenizator BPE (rozmiar słownika: max korpusu = 14 058)
│
└── wykresy/                  # Wygenerowane wizualizacje (matplotlib, 120 DPI):
    ├── 3a_top10_unigram.png                  # Top 10 unigramów z "Pana Tadeusza"
    ├── 3a_top10_bigram.png                   # Top 10 bigramów (dominacja słów funkcyjnych)
    ├── 3a_top10_trigram.png                  # Top 10 trigramów (formuły epickie)
    ├── 3a_top10_bigram_bez_stop_words.png    # Top 10 bigramów po odfiltrowaniu stop words
    ├── 3a_ranga_czestosc.png                 # Wykres log-log ranga-częstość (prawo Zipfa)
    ├── 5g_top10_unigram_bez_stop_words.png   # Top 10 unigramów treściowych
    ├── 5g_top10_bigram_bez_stop_words.png    # Top 10 bigramów treściowych
    ├── 5g_top10_trigram_bez_stop_words.png   # Top 10 trigramów treściowych
    ├── 5g_top10_nazwy_wlasne.png             # Top 10 nazw własnych wykrytych RegEx-em
    ├── 5h_srednia_tokenow.png                # Porównanie tokenizatorów: PL vs EN (podatek językowy)
    └── 5h_tokeny_vs_slownik.png              # Krzywa kompresji: liczba tokenów vs rozmiar słownika BPE
```

---

## 4. Tabela zgodności z wymaganiami na ocenę 5.0

| Poziom | Część | Wymóg z regulaminu (Lab2.pdf) | Plik źródłowy | Kluczowy wynik / Realizacja |
|:---:|:---:|---|---|---|
| **3.0** | **A** | Tokenizacja, n-gramy, histogramy i statystyki j. polskiego | `zad3_a.py` | 3 827 zdań, 68 185 wyrazów; wykresy ranga-częstość (Zipf), analiza unigramów/bigramów/trigramów |
| **3.0** | **B** | Stemming i lematyzacja tekstu angielskiego (5 zdań z Hamleta) | `zad3_b.py` | Tabela token → rdzeń (Porter) → lemat (WordNet); wskazano 22 rozbieżne słowa (m.in. formy nieregularne) |
| **3.0** | **C** | Odległość Levenshteina (*textdistance*) i interpretacja operacji | `zad3_c.py` | Odległość = 6 (1 substytucja `m`→`p`, 5 insersji `o,s,i,a,d`), znormalizowane podobieństwo = 0.6250 |
| **4.0** | **D** | Porównanie stemmerów angielskich (Porter vs Lancaster) | `zad4_d.py` | 1805 rozbieżnych słów (40.1%); identyfikacja zjawisk *overstemmingu* i *understemmingu* |
| **4.0** | **E** | Narzędzia dedykowane dla polszczyzny vs angielski Snowball | `zad4_e.py` | Analiza morfosyntaktyczna spaCy `pl_core_news_sm`; wykazanie destrukcyjnego działania Snowballa na polszczyznę; omówienie 26 języków Snowballa |
| **4.0** | **F** | 4 miary podobieństwa napisów (Levenshtein, Damerau, Jaro-Winkler, Jaccard) | `zad4_f.py` | Porównanie 4 metryk na 4 zróżnicowanych parach zdań (literówki, transpozycje, diakrytyki, permutacje słów) |
| **5.0** | **G** | Stop words (335 słów) i ekstrakcja nazw własnych RegEx-em | `zad5_g.py` | Usunięto 36.0% tekstu; RegEx `(?<=[\w,;:] )[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+` wykrył m.in. Tadeusza (151), Soplicę (108), Hrabiego (90) |
| **5.0** | **H** | Własny tokenizator BPE (1k/5k/30k) + benchmark modeli LLM | `zad5_h.py` | Trening modelu ByteLevel; korpus nasycił się na 14 058 tokenach; wykazano 2.8x wyższy koszt tokenizacji polszczyzny w GPT-2 (*podatek językowy*) |
| **5.0** | **I** | Wielowymiarowe zestawienie 4 metod przetwarzania tekstu | `zad5_i.py` | Macierz dla Inwokacji i 2 000 słów; sformułowanie fundamentalnego kompromisu NLP: rozmiar słownika vs długość sekwencji |

---

## 5. Szczegółowe omówienie wyników i wniosków badawczych

### Część A – N-gramy i rozkłady częstości w języku polskim (`zad3_a.py`)
- **Charakterystyka korpusu**: 3 827 zdań, 68 185 wyrazów (18 763 unikalne formy fleksyjne).
- **Dominacja słów funkcyjnych**: Najczęstsze unigramy to spójniki i przyimki: `i` (2 128), `w` (1 426), `się` (1 185), `z` (1 054), `na` (950). W rezultacie w surowych bigramach dominują połączenia gramatyczne: `się w` (76), `i z` (72), `się z` (67), `się i` (61), które odzwierciedlają strukturę języka polskiego (wysoka frekwencja czasowników zwrotnych), a nie treść utworu.
- **Rozkład ranga-częstość (Prawo Zipfa)**:
  - Unigramy: 10 najczęstszych słów stanowi aż **16.44%** całego tekstu, a 63.1% wyrazów to *hapax legomena* (występujące tylko raz).
  - Bigramy: Rozkład ulega silnemu spłaszczeniu – aż **92.7%** unikalnych bigramów pojawia się dokładnie 1 raz, a top 10 pokrywa zaledwie **0.76%** tekstu.
  - Trigramy: **99.1%** trigramów występuje jednokrotnie. Topowe trigramy ujawniają powtarzalne formuły epickie poetyckiego stylu Mickiewicza (np. okrzyk bitewny `hejże na soplicę` [6] oraz formułę metryczną `idąc kłaniał się` [4]).

### Część B – Sprowadzanie form w języku angielskim (`zad3_b.py`)
Przeanalizowano 5 klasycznych wersów z *Hamleta* Shakespeare'a (m.in. monolog *To be, or not to be*, kwestie Poloniusza i Horacego):
- Stemmer Portera opiera się wyłącznie na heurystycznym obcinaniu sufiksów, podczas gdy lematyzator WordNet korzysta z bazy słownikowej i tagowania części mowy (POS).
- Zidentyfikowano **22 słowa o rozbieżnych wynikach**. Najważniejsze kategorie:
  1. **Czasowniki nieregularne**: `is` / `are` $\to$ rdzeń: `is` / `are` vs lemat: `be`; `had` $\to$ `had` vs `have`; `fed` $\to$ `fed` vs `feed`. Stemmer jest ślepy na fleksję nieregularną.
  2. **Imiesłowy**: `grown` $\to$ `grown` vs `grow`; `opposing` $\to$ `oppos` vs `oppose`.
  3. **Rzeczowniki z końcówką `-y` $\to$ `-ies`**: `Frailty` $\to$ `frailti` (zamiana `y` na `i`) vs `frailty`.

### Część C – Odległość edycyjna Levenshteina (`zad3_c.py`)
Dla badanej pary zdań:
- $s_1$: `"Ala ma kota"` (długość 11 znaków)
- $s_2$: `"Ala posiada kota"` (długość 16 znaków)

Algorytm programowania dynamicznego z biblioteki `textdistance` wyznaczył odległość **Levenshteina = 6**.
Wynik składa się z dokładnie 6 elementarnych operacji o jednostkowym koszcie 1:
1. Zamiana znaku (substitution): `'m'` $\to$ `'p'` na pozycji 4.
2. Wstawienie znaku (insertion): litera `'o'` na pozycji 5.
3. Wstawienie znaku (insertion): litera `'s'` na pozycji 6.
4. Wstawienie znaku (insertion): litera `'i'` na pozycji 7.
5. Wstawienie znaku (insertion): litera `'a'` na pozycji 8.
6. Wstawienie znaku (insertion): litera `'d'` na pozycji 9.

Wspólny prefiks `"Ala "` (4 znaki) oraz sufiks `" kota"` (5 znaków) pozostały nienaruszone (koszt 0).
- Znormalizowana odległość: $\frac{6}{\max(11, 16)} = \frac{6}{16} = \mathbf{0.3750}$
- Znormalizowane podobieństwo: $1 - 0.3750 = \mathbf{0.6250}$

### Część D – Porównanie stemmerów angielskich: Porter vs Lancaster (`zad4_d.py`)
Zbadano cały słownik dramatu *Hamlet* (4 505 unikalnych słów o długości min. 3 liter):
- Porter i Lancaster dały **odmienne rdzenie dla 1 805 słów (40.1%)**.
- Liczba unikalnych rdzeni: **Porter: 3 547**, **Lancaster: 3 165**. Lancaster redukuje słownik znacznie silniej, wykazując skrajną agresywność reguł.
- **Nadmierne obcinanie (overstemming)** w Lancasterze prowadzi do utraty semantyki:
  - `police` oraz `policy` $\to$ zredukowane do `polic`.
  - `organization` oraz `organ` $\to$ zredukowane do `org`.
  - `winter` oraz `wind` $\to$ zredukowane do `win`.
- **Niedostateczne obcinanie (understemming)** w Porterze:
  - Brak sprowadzenia form `knave` i `knavery` (zostawia `knave` i `knaveri`).
  - Pozostawienie form zaimkowych i nieregularnych bez integracji leksykalnej.

### Część E – Specyfika polszczyzny: spaCy vs Snowball (`zad4_e.py`)
1. **Analiza dedykowana**: Model `pl_core_news_sm` w spaCy łączy lematyzator słownikowy z neuronowym taggerem morfosyntaktycznym. Bezbłędnie sprowadza formy z obocznościami rdzeniowymi (`wiózł` $\to$ `wieźć`, `ręce` $\to$ `ręka`, `ludzi` $\to$ `człowiek`).
2. **Eksperyment negatywny**: Zastosowanie angielskiego `SnowballStemmer("english")` do polskich słów zakończyło się całkowitym niepowodzeniem:
   - Słowa typowo fleksyjne (`uczący`, `piękny`, `miasto`) pozostały niezmienione, ponieważ polskie morfémy koniugacyjne i deklinacyjne nie figurują w regułach angielskich.
   - Słowa przypadkowo dopasowane zostały zniekształcone: `sprawdzanie` $\to$ `sprawdzani` (usunięcie końcowego `e`), `domowy` $\to$ `domowi` (zamiana `y` na `i`).
3. **Analiza pakietu Snowball**: Biblioteka wspiera 26 języków (m.in. angielski, niemiecki, francuski, hiszpański, rosyjski, fiński, węgierski). **Język polski jest nieobecny**. Wynika to z bogactwa polskiej fleksji, licznych oboczności fonologicznych wewnątrz rdzenia (np. *o:ó*, *ę:ą*, *ch:sz*) oraz prefiksacji, których nie da się obsłużyć prostym algorytmem obcinania końcówek bez obszernego słownika bazowego.

### Część F – Miary podobieństwa napisów (`zad4_f.py`)
Porównano 4 miary z biblioteki `textdistance` na 4 parach tekstów testowych:

| Badana para tekstów | Levenshtein (dist) | Damerau-Lev. (dist) | Jaro-Winkler (sim) | Jaccard n=2 (sim) | Kluczowy wniosek |
|---|:---:|:---:|:---:|:---:|---|
| **Para 1**: `"Ala ma kota"` vs `"Ala posiada kota"` | 6 | 6 | 0.7625 | 0.4286 | Długa insercja obniża Jaccarda; Jaro-Winkler premiuje identyczny prefiks `"Ala "` |
| **Para 2 (literówka/transpozycja)**: `"szkoła"` vs `"szkoła"` / `"wieczór"` vs `"wieczro"` | 2 | **1** | 0.9429 | 0.6000 | **Damerau-Levenshtein traktuje przestawienie liter jako 1 operację** (w Levenshteinie koszt = 2) |
| **Para 3 (diakrytyki)**: `"zażółć gęślą jaźń"` vs `"zazolc gesla jazn"` | 6 | 6 | 0.8875 | 0.2857 | Różnica 6 znaków; drastyczny spadek podobieństwa bigramowego Jaccarda |
| **Para 4 (permutacja słów)**: `"kot pije mleko"` vs `"mleko pije kot"` | 10 | 10 | 0.6190 | **0.8000** | **Największa rozbieżność metryk!** Levenshtein mierzy pozycję znaków (duży koszt), a Jaccard operuje na zbiorze podciągów |

### Część G – Stop words i ekstrakcja nazw własnych RegEx-em (`zad5_g.py`)
- **Filtracja stop words**: Zastosowano listę 335 polskich słów funkcyjnych z biblioteki `stop-words`.
  - Liczba słów spadła z **68 185 do 43 614** (usunięto aż **36.0%** objętości tekstu).
  - Słownik unikalnych wyrazów zmniejszył się jedynie o **1.5%** (z 18 763 do 18 489). Świadczy to o tym, że słowa funkcyjne stanowią znikomą część słownika, ale odpowiadają za olbrzymią masę tekstu.
  - Oczyszczone n-gramy natychmiast ujawniły treść poematu: `rzekł sędzia` (14), `jaśnie wielmożny` (9), `jenerał dąbrowski` (8), `ksiądz robak` (8), `rzekł hrabia` (8).
- **Ekstrakcja nazw własnych z RegEx**:
  Użyto wyrażenia regularnego z pozytywną asercją wsteczną (*positive lookbehind*):
  ```python
  PROPER_NAME = re.compile(r'(?<=[\w,;:] )[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+')
  ```
  Wzorzec wymaga, aby słowo pisane wielką literą było poprzedzone w tej samej linii innym wyrazem lub znakiem interpunkcyjnym i spacją. Eliminuje to automatycznie pierwsze słowa zdań i wersów.
  - Wykryto 5 198 wystąpień i 1 475 unikalnych wyrazów.
  - **Top 10 nazw własnych**: `Tadeusz` (151), `Soplica` (108), `Hrabia` (90), `Telimena` (89), `Robak` (85), `Sędzia` (83), `Wojski` (73), `Gerwazy` (68), `Litwa` (62), `Protazy` (45).

### Część H – Własny tokenizator BPE i zjawisko podatku językowego (`zad5_h.py`)
Wytrenowano tokenizer `ByteLevel BPE` na korpusie *Pana Tadeusza*:
1. **Asymptota korpusu**:
   - Dla zadanego limitu 30 000 tokenów algorytm zatrzymał się na **14 058 tokenach**. Przy parametrze `min_frequency = 2` w korpusie wyczerpały się pary znaków do scalenia. Wskazuje to, że rozmiar słownika w BPE jest ograniczony bogactwem korpusu treningowego.
2. **Podział słów podsłowowych**:
   - Słowo wewnątrzdomenowe `Soplicowo`: BPE 1k $\to$ 3 tokeny (`Sopli|co|wo`), BPE 5k $\to$ 2 tokeny (`Soplico|wo`), BPE 30k $\to$ **1 token (`Soplicowo`)**.
   - Słowo pozadomenowe `hiperparametryzacja`: nawet przy słowniku 14k jest cięte na 9-10 drobnych fragmentów sylabowych (`hi|p|er|pa|ra|me|try|za|cja`).
3. **Benchmark tokenizatorów (Średnia liczba tokenów na zdanie)**:

| Tokenizator | Liczba tokenów: Zdania polskie (PL) | Liczba tokenów: Zdania angielskie (EN) | Stosunek PL / EN |
|---|:---:|:---:|:---:|
| **Własny BPE (5 000)** | 24.4 | 41.0 | 0.60 |
| **allegro/herbert-base-cased** | 14.2 | 25.2 | 0.56 |
| **speakleash/Bielik-1.5B-v3** | **13.8** | 24.0 | 0.58 |
| **gpt2** (OpenAI) | **38.6** | **14.2** | **2.72** |

> [!IMPORTANT]
> **Podatek językowy (Language Tax)**:
> Model `gpt2`, którego tokenizator trenowano na przeważająco angielskim korpusie WebText, potrzebuje aż **38.6 tokenów na polskie zdanie** w porównaniu do **14.2 na angielskie** (blisko 3-krotne przebicie!).
> Oznacza to, że użytkownik przetwarzający język polski w modelu anglocentrycznym płaci trzykrotnie więcej za API, traci 2/3 okna kontekstowego (*context window*), a proces inferencji jest proporcjonalnie wolniejszy. Modele dedykowane (HerBERT, Bielik) całkowicie eliminują ten narzut.

### Część I – Wielowymiarowe porównanie metod przetwarzania tekstu (`zad5_i.py`)

Zestawienie 4 wariantów reprezentacji dla fragmentu *Inwokacji* oraz próbki 2 000 słów:

| Wariant przetwarzania tekstu | Liczba jednostek w tekście | Rozmiar unikalnego słownika | TTR (*Type-Token Ratio*) | Współczynnik jednostek / wyraz | Wpływ na rozmiar słownika |
|---|:---:|:---:|:---:|:---:|:---:|
| **1. Same wyrazy (baza)** | 1 990 | 1 230 | 0.618 | 1.00 | 0.0% (baza) |
| **2. Wyrazy po lematyzacji** (spaCy) | 1 990 | 1 020 | 0.513 | 1.00 | **-17.1%** |
| **3. Wyrazy bez stop words** | 1 271 | 1 090 | 0.858 | 0.64 | **-11.4%** |
| **4. Tokeny podsłowowe BPE** (5 000) | 3 290 | 1 258 | 0.382 | **1.65** | **+2.3%** (w skali dzieła: **-73.4%**) |

#### Fundamentalny kompromis w NLP:
- **Usunięcie stop words** redukuje tekst najmocniej lokalnie, lecz niszczy strukturę syntaktyczną (tekst staje się zbiorem *bag-of-words*, uniemożliwiając generowanie sekwencyjne).
- **Lematyzacja** zachowuje długość tekstu (1:1), redukuje formy fleksyjne, ale traci niuanse gramatyczne (czas, osoba, przypadek) i wymaga ciężkich reguł lingwistycznych.
- **Tokenizacja podsłowowa BPE**:
  - W skali globalnego korpusu gwarantuje **sztywny, skończony słownik** (np. 5 000 lub 32 000 tokenów) niezależnie od prawa Heapsa.
  - Jest **w 100% bezstratna i odwracalna** (obsługuje dowolne neologizmy i słowa spoza słownika poprzez rozbicie na bajty).
  - Kosztem jest **wydłużenie sekwencji o 65%**, co przy kwadratowej złożoności mechanizmu atencji w architekturze Transformer ($O(N^2)$) zwiększa narzut pamięciowy i obliczeniowy.

---

## 6. Pytania i odpowiedzi na obronę projektu

### 1. Jakie bigramy dominują w analizowanym tekście i dlaczego?
Dominują bigramy złożone ze słów funkcyjnych (zaimek zwrotny `się`, spójniki `i`, `a`, przyimki `w`, `z`, `na`): `się w` (76), `i z` (72), `się z` (67). Wynika to z faktu, że najczęstsze słowa w korpusie mają najwyższe prawdopodobieństwo wystąpienia obok siebie. Obrazują one gramatykę polszczyzny, a nie fabułę. Dopiero po odfiltrowaniu stop words pojawiają się bigramy semantyczne (`rzekł sędzia`, `ksiądz robak`).

### 2. Czy trigramy pokazują powtarzalne zwroty charakterystyczne dla autora?
Tak. Trigramy o najwyższej częstości ujawniają **formuły epickie** charakterystyczne dla poematu heroicznego Adama Mickiewicza: `hejże na soplicę` (refren sceny zajazdu), `ostatniego z horeszków` (stały epitet Gerwazego), `pro publico bono` (makaronizm szlachecki) oraz ciąg wersyfikacyjny `idąc kłaniał się`.

### 3. Czym różni się rozkład unigramów od rozkładu bigramów (prawo Zipfa)?
Rozkład unigramów jest silnie skoncentrowany (top 10 pokrywa 16.4% tekstu, a najczęstsze słowo `i` występuje 2 128 razy). Rozkład bigramów jest drastycznie bardziej rozproszony – unikalnych bigramów jest 3x więcej niż słów, aż **92.7% występuje tylko jeden raz**, a top 10 stanowi poniżej 1% korpusu. Wraz ze wzrostem $n$ gwałtownie nasila się problem rzadkości danych (*data sparsity*).

### 4. Na czym polega różnica między stemmingiem a lematyzacją?
- **Stemming** to szybki, heurystyczny proces odcinania znanych afiksów gramatycznych za pomocą sztywnych reguł bez znajomości kontekstu. Zwracany rdzeń (*stem*) często nie jest poprawnym słowem w słowniku (np. `frailti`, `organ`).
- **Lematyzacja** to pełna analiza morfosyntaktyczna uwzględniająca część mowy (POS) i kontekst zdania, która sprowadza formę wyrazową do jej poprawnego hasła słownikowego (*lematu*). Obsługuje formy nieregularne (`is` $\to$ `be`, `ludzie` $\to$ `człowiek`).

### 5. Dlaczego angielski Snowball nie nadaje się do języka polskiego i dlaczego polskiego nie ma w Snowballu?
Polszczyzna jest językiem fleksyjnym o bogatej syntezie morfologicznej z powszechnymi **obocznościami wewnątrzrdzeniowymi** (*wiózł / wieźć / wozić*, *ręka / ręce*). Zwykłe odcięcie końcówki przez Snowballa pozostawia niespójne rdzenie. Polskiego nie ma wśród 26 języków Snowballa, ponieważ poprawny stemming polski wymaga albo potężnych słowników leksykalnych, albo dedykowanych algorytmów uwzględniających alternacje fonologiczne (np. algorytm Stempla).

### 6. Czym różni się odległość Damerau-Levenshteina od Levenshteina?
Damerau-Levenshtein dodaje czwartą operację edycyjną: **transpozycję** (zamianę dwóch sąsiadujących znaków, np. `wieczro` $\to$ `wieczór`). W klasycznym Levenshteinie transpozycja kosztuje 2 operacje (usunięcie + wstawienie lub 2 zamiany), natomiast w Damerau-Levenshteinie koszt wynosi 1, co idealnie modeluje ludzkie błędy klawiaturowe.

### 7. Czym jest podatek językowy (language tax) w modelach LLM i jak go zniwelować?
Podatek językowy to zjawisko nadmiernej fragmentacji tekstu na tokeny w modelach LLM trenowanych głównie na języku angielskim (np. GPT-2, LLaMA). Polskie słowa są w nich rozbijane na pojedyncze litery lub bajty, co powoduje generowanie 2.5–3x większej liczby tokenów za tę samą treść. Skutkuje to wyższym kosztem finansowym zapytań API, drastycznym skracaniem efektywnego okna kontekstowego oraz gorszą reprezentacją semantyczną. Rozwiązaniem jest trenowanie modeli i tokenizatorów na dedykowanych korpusach narodowych (jak HerBERT czy Bielik).
