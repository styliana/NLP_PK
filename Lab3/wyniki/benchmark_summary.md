# Wyniki pomiarów: PostgreSQL vs Apache Solr

Wygenerowano: 2026-10-22 19:53:20. Mediana z 5 uruchomień po jednym rozgrzewającym (rozgrzany cache). Czasy w ms.

## Środowisko

| Parametr | Wartość |
| --- | --- |
| Procesor | 13th Gen Intel(R) Core(TM) i7-13700H |
| RAM [GB] | 31,5 |
| Dysk | SAMSUNG MZAL8512HDLU-00BL2 (SSD) |
| System | Windows-11-10.0.26300-SP0 |
| Pamięć dla Dockera [GB] | 15.4 |
| PostgreSQL | 16.15 (Debian 16.15-1.pgdg13+2) |
| shared_buffers / work_mem | 1GB / 64MB |
| Solr | 10.0.0 |
| Java (Solr) | 25.0.4.1 25.0.4.1+1-LTS |
| Heap Solra (SOLR_HEAP) [MB] | 2048 |
| Python | 3.14.2 |

## Zbiór danych

| Cecha | Wartość |
| --- | --- |
| Źródło | https://huggingface.co/datasets/gfissore/arxiv-abstracts-2021 |
| Licencja | CC0 1.0 (metadane arXiv); autorzy i zgłaszający pominięci - brak danych osobowych |
| Próbkowanie | 500000 z 1999486 artykułów o najmniejszym crc32(arxiv_id) (deterministyczna, równomierna próbka) |
| Rekordy | 550 000 (500 000 oryginałów + 50 000 kopii) |
| Powielenie | co 10. oryginał powielony (copy_no=1, orig_id=id oryginału) |
| Rozmiar CSV [MB] | 555.2 |
| Długość abstraktu [znaki] | śr. 910.2, mediana 862, min 3, max 4196 |
| field (grupa arXiv) | 8 wartości |
| category (kategoria główna) | 172 wartości |
| year | 1991–2021 |

Rozkład pola `field`:

| field | liczba oryginałów |
| --- | --- |
| Physics | 290 850 |
| Mathematics | 102 634 |
| Computer Science | 82 271 |
| Statistics | 8 937 |
| Electrical Engineering and Systems Science | 6 494 |
| Quantitative Biology | 5 645 |
| Quantitative Finance | 2 283 |
| Economics | 886 |

Przykładowy rekord:

```json
{
  "id": 1,
  "orig_id": 1,
  "copy_no": 0,
  "arxiv_id": "0704.0004",
  "title": "A determinant of Stirling cycle numbers counts unlabeled acyclic single-source automata",
  "abstract": "We show that a determinant of Stirling cycle numbers counts unlabeled acyclic single-source automata. The proof involves a bijection from these automata to certain marked lattice paths and a sign-reversing involution to evaluate the determinant.",
  "field": "Mathematics",
  "category": "math.CO",
  "categories": "math.CO",
  "year": 2007,
  "n_versions": 1
}
```

## Ładowanie i indeksowanie

| Zbiór | Rekordy | PG COPY [s] | PG indeksy [s] | PG VACUUM ANALYZE [s] | PG razem [s] | PG rozmiar [MB] | Solr wysyłka [s] | Solr commit [s] | Solr razem [s] | Solr indeks [MB] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10% | 55 000 | 13.21 | 4.18 | 1.1 | 18.49 | 138.8 | 18.21 | 0.75 | 18.96 | 58.4 |
| 50% | 275 000 | 73.64 | 25.68 | 1.89 | 101.21 | 710.6 | 92.69 | 0.84 | 93.53 | 300.5 |
| 100% | 550 000 | 149.54 | 75.11 | 2.49 | 227.15 | 1407.3 | 189.44 | 2.36 | 191.8 | 597.8 |

PG COPY obejmuje wyliczenie kolumny `tsv` (GENERATED STORED); "PG indeksy" = GIN na tsv, trigramy na title, B-tree na orig_id. Solr: paczki po 5000 dokumentów, jeden commit na końcu.

## Zapytania Q1–Q3 (pełny zbiór, 550 000 rekordów)

| Zapytanie | LIKE: wyniki | SQL FTS: wyniki | Solr: numFound | LIKE [ms] | FTS count [ms] | FTS top-10 ranking [ms] | Solr QTime | Solr klient [ms] | Solr z cache wyników [ms] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q1: pojedyncze słowo w dowolnej formie (simulate) | 10 594 | 56 540 | 56 557 | 875.1 | 51.1 | 272.0 | 10 | 15.8 | 6.13 |
| Q2: fraza ("neural network") | 13 500 | 16 043 | 16 197 | 891.7 | 81.0 | 185.5 | 8 | 13.9 | 4.63 |
| Q3: quantum AND (entanglement OR teleportation) AND NOT photon | 3 949 | 5 094 | 5 095 | 762.9 | 7.82 | 66.7 | 8 | 14.4 | 5.84 |

Czasy SQL wg EXPLAIN ANALYZE (Execution Time, bez narzutu sieci/klienta):

| Zapytanie | LIKE | FTS count | FTS top-10 |
| --- | --- | --- | --- |
| Q1 | 856.4 | 54.8 | 265.7 |
| Q2 | 880.7 | 84.0 | 172.2 |
| Q3 | 800.8 | 6.72 | 67.5 |

### Dokładne zapytania

**Q1: pojedyncze słowo w dowolnej formie (simulate)**

- LIKE: `SELECT count(*) FROM documents WHERE (title || ' ' || abstract) LIKE '%simulate%'`
- SQL FTS: `SELECT count(*) FROM documents WHERE tsv @@ to_tsquery('english', 'simulate')`
- SQL ranking: `SELECT id, orig_id, title, ts_rank_cd(tsv, to_tsquery('english', 'simulate')) AS rank FROM documents WHERE tsv @@ to_tsquery('english', 'simulate') ORDER BY rank DESC, id LIMIT 10`
- Solr (lucene): http://localhost:8983/solr/nlp_lab3/select?df=text_all&rows=10&fl=id%2Corig_id%2Ctitle%2Cscore&q=simulate
- Solr (fq, fl, sort, rows): http://localhost:8983/solr/nlp_lab3/select?q=simulate&df=text_all&fq=year%3A%5B2015+TO+%2A%5D&fl=id%2Ctitle%2Cyear%2Ccategory&sort=year+desc%2Cscore+desc&rows=5 → numFound 32 953 (SQL z `year >= 2015`: 32 937)
- Solr eDisMax + hl: http://localhost:8983/solr/nlp_lab3/select?defType=edismax&q=simulate&qf=title%5E3+abstract&rows=10&fl=id%2Corig_id%2Ctitle%2Cscore&hl=true&hl.fl=abstract&hl.snippets=1&hl.fragsize=160

**Q2: fraza ("neural network")**

- LIKE: `SELECT count(*) FROM documents WHERE (title || ' ' || abstract) LIKE '%neural network%'`
- SQL FTS: `SELECT count(*) FROM documents WHERE tsv @@ phraseto_tsquery('english', 'neural network')`
- SQL ranking: `SELECT id, orig_id, title, ts_rank_cd(tsv, phraseto_tsquery('english', 'neural network')) AS rank FROM documents WHERE tsv @@ phraseto_tsquery('english', 'neural network') ORDER BY rank DESC, id LIMIT 10`
- Solr (lucene): http://localhost:8983/solr/nlp_lab3/select?df=text_all&rows=10&fl=id%2Corig_id%2Ctitle%2Cscore&q=%22neural+network%22
- Solr (fq, fl, sort, rows): http://localhost:8983/solr/nlp_lab3/select?q=%22neural+network%22&df=text_all&fq=year%3A%5B2015+TO+%2A%5D&fl=id%2Ctitle%2Cyear%2Ccategory&sort=year+desc%2Cscore+desc&rows=5 → numFound 15 495 (SQL z `year >= 2015`: 15 346)
- Solr eDisMax + hl: http://localhost:8983/solr/nlp_lab3/select?defType=edismax&q=%22neural+network%22&qf=title%5E3+abstract&rows=10&fl=id%2Corig_id%2Ctitle%2Cscore&hl=true&hl.fl=abstract&hl.snippets=1&hl.fragsize=160

**Q3: quantum AND (entanglement OR teleportation) AND NOT photon**

- LIKE: `SELECT count(*) FROM documents WHERE (title || ' ' || abstract) LIKE '%quantum%' AND ((title || ' ' || abstract) LIKE '%entanglement%' OR (title || ' ' || abstract) LIKE '%teleportation%') AND (title || ' ' || abstract) NOT LIKE '%photon%'`
- SQL FTS: `SELECT count(*) FROM documents WHERE tsv @@ to_tsquery('english', 'quantum & (entanglement | teleportation) & !photon')`
- SQL ranking: `SELECT id, orig_id, title, ts_rank_cd(tsv, to_tsquery('english', 'quantum & (entanglement | teleportation) & !photon')) AS rank FROM documents WHERE tsv @@ to_tsquery('english', 'quantum & (entanglement | teleportation) & !photon') ORDER BY rank DESC, id LIMIT 10`
- Solr (lucene): http://localhost:8983/solr/nlp_lab3/select?df=text_all&rows=10&fl=id%2Corig_id%2Ctitle%2Cscore&q=quantum+AND+%28entanglement+OR+teleportation%29+AND+NOT+photon
- Solr (fq, fl, sort, rows): http://localhost:8983/solr/nlp_lab3/select?q=quantum+AND+%28entanglement+OR+teleportation%29+AND+NOT+photon&df=text_all&fq=year%3A%5B2015+TO+%2A%5D&fl=id%2Ctitle%2Cyear%2Ccategory&sort=year+desc%2Cscore+desc&rows=5 → numFound 2 371 (SQL z `year >= 2015`: 2 370)
- Solr eDisMax + hl: http://localhost:8983/solr/nlp_lab3/select?defType=edismax&q=quantum+AND+%28entanglement+OR+teleportation%29+AND+NOT+photon&qf=title%5E3+abstract&rows=10&fl=id%2Corig_id%2Ctitle%2Cscore&hl=true&hl.fl=abstract&hl.snippets=1&hl.fragsize=160

## Ranking top-10: ts_rank_cd vs eDisMax (qf=title^3 abstract)

| Zapytanie | Wspólne id w top-10 | Pary kopii w top-10 SQL | Pary kopii w top-10 Solr | eDisMax+hl [ms] | ts_headline top-10 [ms] |
| --- | --- | --- | --- | --- | --- |
| Q1 | 1/10 | 0 | 0 | 18.2 | 271.9 |
| Q2 | 3/10 | 1 | 1 | 15.6 | 184.6 |
| Q3 | 1/10 | 0 | 0 | 17.0 | 72.2 |

### Q1: pojedyncze słowo w dowolnej formie (simulate)

| # | PostgreSQL ts_rank_cd: id (rank) tytuł | Solr eDisMax: id (score) tytuł |
| --- | --- | --- |
| 1 | 309025 (8.6) Simulation Typology and Termination Risks | 205661 (9.445) The Simulator: An Engine to Streamline Simulations |
| 2 | 205661 (8.0) The Simulator: An Engine to Streamline Simulations | 334329 (8.73) Using asynchronous simulation approach for interactive simulation |
| 3 | 315692 (7.4) Simulation Credibility Assessment Methodology with FPGA-based Hardware | 80522 (8.517) Simulations of the Hyades |
| 4 | 96875 (7.2) Efficient Computing Budget Allocation for Simulation-based Optimizatio | 72651 (8.517) Simulation in Statistics |
| 5 | 349702 (6.2) A Study on the Challenges of Using Robotics Simulators for Testing | 125590 (8.517) Quantum Simulation |
| 6 | 235698 (5.8) Unlocking the Potential of Simulators: Design with RL in Mind | 323099 (8.517) The Quijote simulations |
| 7 | 375624 (5.8) Fast simulation of quantum algorithms using circuit optimization | 463515 (8.517) Sociophysics Simulations |
| 8 | 105483 (5.6) Physics Educators as Designers of Simulation using Easy Java Simulatio | 352892 (8.411) LGSVL Simulator: A High Fidelity Simulator for Autonomous Driving |
| 9 | 306945 (5.6) XR: Enabling training mode in the human brain XR: Enabling training mo | 274304 (8.115) Introducing the Simulated Flying Shapes and Simulated Planar Manipulat |
| 10 | 49466 (5.4) Optimisation of a Crossdocking Distribution Centre Simulation Model | 402045 (8.115) Cathode to Target Simulations for Scorpius: I. Simulation Codes and Mo |

Podświetlanie dokumentu 205661:

- Solr `hl`: The syntax of the <em>simulator</em> leads to <em>simulation</em> code that is easily human-readable. Other benefits of using the <em>simulator</em> include the ability to "step in" to a <em>simulation</em> and change one aspect without having to rerun the entire <em>simulation</em> from scratch, the straightforward integration of parallel computing into <em>simulations</em>, and the ability to rapidly generate plots, tables, and reports with minimal effort.
- PostgreSQL `ts_headline`: <em>simulator</em> is an R package that streamlines the process of performing <em>simulations</em> by creating a common infrastructure that can be easily used and reused across

### Q2: fraza ("neural network")

| # | PostgreSQL ts_rank_cd: id (rank) tytuł | Solr eDisMax: id (score) tytuł |
| --- | --- | --- |
| 1 | 265326 (5.6) Cortex Neural Network: learning with Neural Network groups | 476658 (15.253) Neural Networks |
| 2 | 371641 (5.4) Extending Answer Set Programs with Neural Networks | 265326 (15.065) Cortex Neural Network: learning with Neural Network groups |
| 3 | 310601 (5.0) Quantifying the generalization error in deep learning in terms of data | 356845 (15.065) Graphon Neural Networks and the Transferability of Graph Neural Networ |
| 4 | 371971 (5.0) Theoretical Analysis of the Advantage of Deepening Neural Networks | 351980 (14.534) Can a powerful neural network be a teacher for a weaker neural network |
| 5 | 351980 (4.8) Can a powerful neural network be a teacher for a weaker neural network | 192099 (14.204) Bitwise Neural Networks |
| 6 | 280356 (4.6) Quantum Neural Network States: A Brief Review of Methods and Applicati | 181978 (14.204) Tensorizing Neural Networks |
| 7 | 280357 (4.6) Quantum Neural Network States: A Brief Review of Methods and Applicati | 315635 (14.204) Neural Networks on Groups |
| 8 | 315635 (4.6) Neural Networks on Groups | 304391 (14.204) Preference Neural Network |
| 9 | 351068 (4.6) Neural Network Solutions to Differential Equations in Non-Convex Domai | 304392 (14.204) Preference Neural Network |
| 10 | 393592 (4.6) Generating Probabilistic Safety Guarantees for Neural Network Controll | 269172 (14.204) Optical Neural Networks |

Podświetlanie dokumentu 476658:

- Solr `hl`: We review the theory of <em>neural networks</em>, as it has emerged in the last ten years or so within the physics community, emphasizing questions of biological relevance over those of importance in mathematical statistics and machine learning theory.
- PostgreSQL `ts_headline`: review the theory of <em>neural</em> <em>networks</em>, as it has emerged in the last ten years or so within the physics community, emphasizing questions of biological

### Q3: quantum AND (entanglement OR teleportation) AND NOT photon

| # | PostgreSQL ts_rank_cd: id (rank) tytuł | Solr eDisMax: id (score) tytuł |
| --- | --- | --- |
| 1 | 361896 (4.0797) Identifying genuine quantum teleportation | 548615 (24.6) Entanglement Teleportation by Qutrits |
| 2 | 548995 (3.9018) Quantum Entanglement and Communication Complexity | 77256 (23.443) Quantum entanglement and teleportation in pulsed cavity-optomechanics |
| 3 | 346101 (3.4951) Distribution of quantum entanglement: Principles and applications | 545428 (23.443) Quantum channels with correlated noise and entanglement teleportation |
| 4 | 200285 (3.269) Quantum transitions and quantum entanglement from Dirac-like dynamics  | 545562 (23.443) Quantum teleportation using three-particle entanglement |
| 5 | 281271 (3.1906) Cosmological spectrum of two-point correlation function from vacuum fl | 64410 (22.178) Quantum Entanglement: Separability, Measure, Fidelity of Teleportation |
| 6 | 320479 (3.1312) On the effects of an impurity in an Ising-$XXZ$ diamond chain on the t | 544835 (22.178) Effects of noisy entangled state transmission on quantum teleportation |
| 7 | 544823 (3.0146) Direct detection of quantum entanglement | 549574 (22.0) Entanglement Teleportation via Werner States |
| 8 | 64410 (3.0141) Quantum Entanglement: Separability, Measure, Fidelity of Teleportation | 5122 (21.042) Long-distance entanglement and quantum teleportation in XX spin chains |
| 9 | 99698 (2.9059) Dynamics of quantum entanglement in the reservoir with memory effects | 383676 (21.042) Quantum teleportation and entanglement swapping with long baseline in  |
| 10 | 290908 (2.6038) Quantum teleportation of shared quantum secret | 544934 (21.042) Continuous variable quantum teleportation with a finite-basis entangle |

Podświetlanie dokumentu 548615:

- Solr `hl`: <em>Quantum</em> <em>entanglement</em>, like othre resources, is now coonsidered to be a resource which can be produced, concentrated if required, transported and consumed. 
- PostgreSQL `ts_headline`: <em>Quantum</em> <em>entanglement</em>, like othre resources, is now coonsidered to be a resource which can be produced, concentrated if required, transported and consumed. After its inception

## GROUP BY dla wyników Q1 (4.0)

`SELECT field, count(*) FROM documents WHERE tsv @@ to_tsquery('english', 'simulate') GROUP BY field ORDER BY 2 DESC` — 76.7 ms

| field | liczba |
| --- | --- |
| Physics | 38 624 |
| Computer Science | 8 803 |
| Mathematics | 2 969 |
| Statistics | 2 955 |
| Electrical Engineering and Systems Science | 1 629 |
| Quantitative Biology | 1 163 |
| Quantitative Finance | 264 |
| Economics | 133 |

## Skalowanie 10% / 50% / 100% (5.0)

| Zbiór | Rekordy | Zapytanie | FTS wyniki | Solr numFound | LIKE [ms] | FTS count [ms] | FTS top-10 [ms] | Solr klient [ms] | Solr QTime |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10% | 55 000 | Q1 | 4 794 | 4 794 | 198.4 | 6.45 | 22.2 | 7.41 | 1 |
| 10% | 55 000 | Q2 | 103 | 103 | 202.8 | 2.01 | 2.34 | 9.58 | 2 |
| 10% | 55 000 | Q3 | 617 | 617 | 78.3 | 2.07 | 8.47 | 9.39 | 3 |
| 50% | 275 000 | Q1 | 28 400 | 28 405 | 441.3 | 30.9 | 124.5 | 9.41 | 3 |
| 50% | 275 000 | Q2 | 3 954 | 3 973 | 457.0 | 20.7 | 41.9 | 8.09 | 2 |
| 50% | 275 000 | Q3 | 2 772 | 2 773 | 410.9 | 6.56 | 37.6 | 7.82 | 3 |
| 100% | 550 000 | Q1 | 56 540 | 56 557 | 869.0 | 56.6 | 260.8 | 9.25 | 3 |
| 100% | 550 000 | Q2 | 16 043 | 16 197 | 901.6 | 78.1 | 172.7 | 9.78 | 4 |
| 100% | 550 000 | Q3 | 5 094 | 5 095 | 794.5 | 11.8 | 80.7 | 9.41 | 4 |

## Facety vs GROUP BY (5.0)

Jedno zapytanie Solra: `facet.field=field`, `facet.field=category` (top 10), `facet.range=year` (1990–2025, co 5 lat) wobec trzech zapytań GROUP BY i jednego z GROUPING SETS.

| Zapytanie | Dokumenty | Solr klient [ms] | Solr QTime | GROUP BY field | GROUP BY category | GROUP BY year | SQL razem (3 zapytania) | SQL GROUPING SETS | Liczności zgodne |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Q1 (simulate) | 56 557 | 12.0 | 7 | 92.5 | 119.9 | 99.3 | 311.8 | 91.3 | field: nie, category: nie, year: nie |
| cały zbiór (*:*) | 550 000 | 34.8 | 28 | 179.7 | 170.8 | 161.9 | 512.5 | 519.4 | field: tak, category: tak, year: tak |

Liczności dla Q1:

| Przedział lat | Solr | SQL |
| --- | --- | --- |
| 1990 | 336 | 336 |
| 1995 | 1 807 | 1 807 |
| 2000 | 3 655 | 3 655 |
| 2005 | 6 381 | 6 381 |
| 2010 | 11 425 | 11 424 |
| 2015 | 20 345 | 20 334 |
| 2020 | 12 608 | 12 603 |

| field | Solr | SQL |
| --- | --- | --- |
| Computer Science | 8 806 | 8 803 |
| Economics | 134 | 133 |
| Electrical Engineering and Systems Science | 1 629 | 1 629 |
| Mathematics | 2 970 | 2 969 |
| Physics | 38 635 | 38 624 |
| Quantitative Biology | 1 163 | 1 163 |
| Quantitative Finance | 264 | 264 |
| Statistics | 2 956 | 2 955 |

Liczności dla all:

| Przedział lat | Solr | SQL |
| --- | --- | --- |
| 1990 | 5 592 | 5 592 |
| 1995 | 27 660 | 27 660 |
| 2000 | 50 438 | 50 438 |
| 2005 | 75 839 | 75 839 |
| 2010 | 115 937 | 115 937 |
| 2015 | 175 384 | 175 384 |
| 2020 | 99 150 | 99 150 |

| field | Solr | SQL |
| --- | --- | --- |
| Computer Science | 90 616 | 90 616 |
| Economics | 971 | 971 |
| Electrical Engineering and Systems Science | 7 183 | 7 183 |
| Mathematics | 112 934 | 112 934 |
| Physics | 319 829 | 319 829 |
| Quantitative Biology | 6 188 | 6 188 |
| Quantitative Finance | 2 505 | 2 505 |
| Statistics | 9 774 | 9 774 |

## Wpływ powielenia danych i rozszerzenie: collapse po orig_id

| Wariant | Dokumenty / grupy | Pary kopii w top-10 | Czas [ms] |
| --- | --- | --- | --- |
| Solr eDisMax bez deduplikacji | 56 557 | 0 | 5.81 |
| Solr `fq={!collapse field=orig_id}` | 51 416 | 0 | 5.72 |
| Solr `fq=copy_no:0` | 51 416 | — | — |
| SQL top-10 bez deduplikacji | — | 0 | 281.3 |
| SQL `DISTINCT ON (orig_id)` | 51 400 | 0 | 269.4 |

## Rozszerzenie: odporność na literówki

| Słowo z błędem | LIKE w tytule: wyniki / ms | pg_trgm `<%`: wyniki / ms | Solr dokładnie: wyniki / ms | Solr `~2`: wyniki / ms | Solr poprawne słowo: wyniki |
| --- | --- | --- | --- | --- | --- |
| entanglment (→ entanglement) | 0 / 2.05 | 4 121 / 126.0 | 0 / 4.25 | 3 261 / 29.4 | 3 200 |
| superconductivty (→ superconductivity) | 0 / 1.58 | 6 996 / 164.6 | 0 / 4.55 | 1 792 / 22.7 | 1 773 |

Przykłady dla `entanglment` — pg_trgm: A measure of qubit environment entanglement for pure dephasing evolutions (0.818); Group Invariant Entanglements in Generalized Tensor Products (0.727); Off-resonant entanglement generation in a lossy cavity (0.727)
Solr fuzzy: Entanglement-annihilating and entanglement-breaking channels; Entanglement Classification via Single Entanglement Measure; Maximal Entanglement - A New Measure of Entanglement

Przykłady dla `superconductivty` — pg_trgm: Mechanism for Odd Parity Superconductivity in Iron-Based Superconductors (0.882); Topological Odd-Parity Superconductivity at Type-II 2D Van Hove Singularities (0.882); Possible high temperature odd parity superconductivity in LaNi$_{7/8}$Co$_{1/8}$O$_3$ (111) bilayers (0.882)
Solr fuzzy: Transient superconductivity without superconductivity; Transient superconductivity without superconductivity; Heat Superconductivity

## Rozszerzenie: własny typ pola `text_en_lab` + Analysis vs to_tsvector

**The simulated annealing algorithms were simulating complex networks' behaviour.**

- Solr (Analysis, łańcuch: StandardTokenizer → LowerCaseFilter → StopFilter → EnglishPossessiveFilter → SnowballFilter): `simul anneal algorithm were simul complex network behaviour`
- PostgreSQL `to_tsvector('english', …)`: `'algorithm':4 'anneal':3 'behaviour':9 'complex':7 'network':8 'simul':2,6`

**Next-to-leading order QCD corrections for e+e- annihilation at 10 TeV energies.**

- Solr (Analysis, łańcuch: StandardTokenizer → LowerCaseFilter → StopFilter → EnglishPossessiveFilter → SnowballFilter): `next lead order qcd correct e e annihil 10 tev energi`
- PostgreSQL `to_tsvector('english', …)`: `'10':13 'annihil':11 'correct':7 'e':9,10 'energi':15 'lead':4 'next':2 'next-to-lead':1 'order':5 'qcd':6 'tev':14`

**We don't observe photons; the photonic crystals' band gaps were measured in 2019.**

- Solr (Analysis, łańcuch: StandardTokenizer → LowerCaseFilter → StopFilter → EnglishPossessiveFilter → SnowballFilter): `we don't observ photon photon crystal band gap were measur 2019`
- PostgreSQL `to_tsvector('english', …)`: `'2019':14 'band':9 'crystal':8 'gap':10 'measur':12 'observ':4 'photon':5,7`

## Rozszerzenie: głębokie stronicowanie

| Pozycja | Solr start/rows [ms] | Solr cursorMark [ms] | Ta sama strona | SQL OFFSET [ms] | SQL keyset (id > x) [ms] |
| --- | --- | --- | --- | --- | --- |
| 0 | 16.9 | 16.9 | tak | 0.73 | 0.75 |
| 1 000 | 19.6 | 16.9 | tak | 0.81 | 0.73 |
| 10 000 | 29.3 | 17.4 | tak | 1.47 | 0.75 |
| 100 000 | 128.4 | 19.8 | tak | 7.79 | 0.79 |
| 250 000 | 469.7 | 23.8 | tak | 18.1 | 1.04 |
| 500 000 | 671.6 | 29.3 | tak | 42.2 | 0.84 |
