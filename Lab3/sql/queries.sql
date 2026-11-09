-- Zapytania SQL dla Laboratorium nr 3 (PostgreSQL 16) - te same, które wykonuje scripts/benchmark.py.
-- Tabela documents = 100% zbioru; documents_p50 i documents_p10 = test skalowania.
-- Czas: EXPLAIN (ANALYZE, BUFFERS) -> "Execution Time" (plany zapisuje benchmark w wyniki/explain/).

-- ============================================================================
-- 3.0: trzy zapytania pełnotekstowe + LIKE
-- ============================================================================

-- Q1: pojedyncze słowo w dowolnej formie (simulate -> simulation, simulated, simulating, simulations)
EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*) FROM documents WHERE tsv @@ to_tsquery('english', 'simulate');

-- Q1 przez LIKE (skan sekwencyjny, bez stemmingu, z rozróżnianiem wielkości liter)
EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*) FROM documents WHERE (title || ' ' || abstract) LIKE '%simulate%';

-- Q2: fraza - słowa obok siebie, w podanej kolejności ('neural' <-> 'network')
EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*) FROM documents WHERE tsv @@ phraseto_tsquery('english', 'neural network');

-- Q3: logika z negacją - A oraz (B lub C), bez D
EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*) FROM documents
WHERE tsv @@ to_tsquery('english', 'quantum & (entanglement | teleportation) & !photon');

-- ============================================================================
-- 4.0: ranking top-10, GROUP BY, podświetlanie
-- ============================================================================

-- ranking (tytuł waga A = 1.0, abstrakt waga B = 0.4)
SELECT id, orig_id, title, ts_rank_cd(tsv, to_tsquery('english', 'simulate')) AS rank
FROM documents WHERE tsv @@ to_tsquery('english', 'simulate')
ORDER BY rank DESC, id LIMIT 10;

SELECT id, orig_id, title, ts_rank_cd(tsv, phraseto_tsquery('english', 'neural network')) AS rank
FROM documents WHERE tsv @@ phraseto_tsquery('english', 'neural network')
ORDER BY rank DESC, id LIMIT 10;

SELECT id, orig_id, title,
       ts_rank_cd(tsv, to_tsquery('english', 'quantum & (entanglement | teleportation) & !photon')) AS rank
FROM documents WHERE tsv @@ to_tsquery('english', 'quantum & (entanglement | teleportation) & !photon')
ORDER BY rank DESC, id LIMIT 10;

-- GROUP BY po polu kategorycznym dla wyników zapytania pełnotekstowego
SELECT field, count(*) FROM documents
WHERE tsv @@ to_tsquery('english', 'simulate')
GROUP BY field ORDER BY 2 DESC;

-- podświetlanie trafień (odpowiednik hl w Solrze)
SELECT id, ts_headline('english', abstract, to_tsquery('english', 'simulate'),
                       'MaxFragments=1, MaxWords=25, MinWords=12, StartSel=<em>, StopSel=</em>')
FROM documents WHERE tsv @@ to_tsquery('english', 'simulate')
ORDER BY ts_rank_cd(tsv, to_tsquery('english', 'simulate')) DESC, id LIMIT 10;

-- ============================================================================
-- 5.0: agregacje odpowiadające facetom Solra (2 pola + zakres lat co 5)
-- ============================================================================

SELECT field, count(*) FROM documents
WHERE tsv @@ to_tsquery('english', 'simulate') GROUP BY field ORDER BY 2 DESC;

SELECT category, count(*) FROM documents
WHERE tsv @@ to_tsquery('english', 'simulate') GROUP BY category ORDER BY 2 DESC LIMIT 10;

SELECT 1990 + 5 * ((year - 1990) / 5) AS y, count(*) FROM documents
WHERE tsv @@ to_tsquery('english', 'simulate') AND year >= 1990 GROUP BY y ORDER BY y;

-- to samo jednym zapytaniem
SELECT field, category, 1990 + 5 * ((year - 1990) / 5) AS y, count(*) FROM documents
WHERE tsv @@ to_tsquery('english', 'simulate')
GROUP BY GROUPING SETS ((field), (category), (1990 + 5 * ((year - 1990) / 5)));

-- ============================================================================
-- Rozszerzenia
-- ============================================================================

-- literówki: LIKE (0 trafień) vs pg_trgm (word_similarity, indeks GIN gin_trgm_ops na title)
SELECT count(*) FROM documents WHERE title LIKE '%entanglment%';
SELECT title, word_similarity('entanglment', title) AS s FROM documents
WHERE 'entanglment' <% title ORDER BY s DESC LIMIT 5;

-- analiza tekstu (porównanie z zakładką Analysis w Solrze)
SELECT to_tsvector('english', 'The simulated annealing algorithms were simulating complex networks'' behaviour.');

-- duplikaty po powieleniu: jeden wynik na oryginał
SELECT id, orig_id, title, rank FROM (
    SELECT DISTINCT ON (orig_id) id, orig_id, title, ts_rank_cd(tsv, to_tsquery('english', 'simulate')) AS rank
    FROM documents WHERE tsv @@ to_tsquery('english', 'simulate')
    ORDER BY orig_id, rank DESC, id
) s ORDER BY rank DESC, id LIMIT 10;

-- głębokie stronicowanie: OFFSET vs keyset
SELECT id FROM documents ORDER BY id LIMIT 10 OFFSET 500000;
SELECT id FROM documents WHERE id > 500000 ORDER BY id LIMIT 10;
