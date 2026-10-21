-- Zbiór zapytań SQL dla Laboratorium nr 3 (PostgreSQL 16)
-- Zgodne z wymaganiami poziomów 3.0, 4.0 i 5.0

-- ============================================================================
-- POZIOM 3.0: 3 PODSTAWOWE ZAPYTANIA PEŁNOTEKSTOWE + LIKE
-- ============================================================================

-- Zapytanie 1: Pojedyncze słowo w dowolnej formie gramatycznej (Stemming)
-- Szukamy form wyrazu "perform" (np. performance, performing, performed)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, rating
FROM documents
WHERE tsv @@ to_tsquery('english', 'perform')
LIMIT 10;

-- Zapytanie 1 (wariant porównawczy LIKE '%...%')
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, rating
FROM documents
WHERE content LIKE '%perform%'
LIMIT 10;

-- Zapytanie 2: Fraza — słowa obok siebie w podanej kolejności ("machine learning")
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, rating
FROM documents
WHERE tsv @@ phraseto_tsquery('english', 'machine learning')
LIMIT 10;

-- Zapytanie 3: Złożona logika boolowska z negacją: A AND (B OR C) AND NOT D
-- Przykład: database & (performance | speed) & !slow
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, rating
FROM documents
WHERE tsv @@ to_tsquery('english', 'database & (performance | speed) & !slow')
LIMIT 10;


-- ============================================================================
-- POZIOM 4.0: RANKING ORAZ AGREGACJE GROUP BY
-- ============================================================================

-- Ranking trafności za pomocą funkcji ts_rank_cd (Cover Density Ranking)
-- Top 10 dla Zapytania 1:
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, rating,
       ts_rank_cd(tsv, to_tsquery('english', 'perform')) AS rank_score
FROM documents
WHERE tsv @@ to_tsquery('english', 'perform')
ORDER BY rank_score DESC, id ASC
LIMIT 10;

-- Ranking dla Zapytania 2 (fraza):
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, rating,
       ts_rank_cd(tsv, phraseto_tsquery('english', 'machine learning')) AS rank_score
FROM documents
WHERE tsv @@ phraseto_tsquery('english', 'machine learning')
ORDER BY rank_score DESC, id ASC
LIMIT 10;

-- Ranking dla Zapytania 3 (logika z negacją):
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, rating,
       ts_rank_cd(tsv, to_tsquery('english', 'database & (performance | speed) & !slow')) AS rank_score
FROM documents
WHERE tsv @@ to_tsquery('english', 'database & (performance | speed) & !slow')
ORDER BY rank_score DESC, id ASC
LIMIT 10;

-- Agregacja GROUP BY po polu kategorycznym dla wyników zapytania FTS:
EXPLAIN (ANALYZE, BUFFERS)
SELECT category, COUNT(*) AS doc_count
FROM documents
WHERE tsv @@ to_tsquery('english', 'perform')
GROUP BY category
ORDER BY doc_count DESC;


-- ============================================================================
-- POZIOM 5.0: FACETY KONTRA GROUP BY ORAZ WYBRANE ROZSZERZENIA
-- ============================================================================

-- Odpowiednik Solra (2 facety kategoryczne + 1 facet zakresowy rating 1.0-5.0):
-- 1. Kategoria:
SELECT category, COUNT(*) AS cnt
FROM documents
WHERE tsv @@ to_tsquery('english', 'perform')
GROUP BY category
ORDER BY cnt DESC;

-- 2. Tag:
SELECT tag, COUNT(*) AS cnt
FROM documents
WHERE tsv @@ to_tsquery('english', 'perform')
GROUP BY tag
ORDER BY cnt DESC;

-- 3. Zakres ocen (odpowiednik facet.range):
SELECT 
    CASE 
        WHEN rating >= 1.0 AND rating < 2.0 THEN '[1.0, 2.0)'
        WHEN rating >= 2.0 AND rating < 3.0 THEN '[2.0, 3.0)'
        WHEN rating >= 3.0 AND rating < 4.0 THEN '[3.0, 4.0)'
        WHEN rating >= 4.0 AND rating <= 5.0 THEN '[4.0, 5.0]'
        ELSE 'Inne'
    END AS rating_bucket,
    COUNT(*) AS cnt
FROM documents
WHERE tsv @@ to_tsquery('english', 'perform')
GROUP BY rating_bucket
ORDER BY rating_bucket;

-- ROZSZERZENIE 1: Odporność na literówki (Fuzzy search) z modułem pg_trgm
-- Zapytanie z błędem w pisowni: "machne lerning" zamiast "machine learning"
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, similarity(content, 'machne lerning') AS sim_score
FROM documents
WHERE content % 'machne lerning'
ORDER BY sim_score DESC
LIMIT 10;

-- ROZSZERZENIE 2: Eliminacja duplikatów po powieleniu (Collapsing po orig_id)
-- Zwraca tylko 1 unikalny dokument na orig_id o najwyższej trafności:
EXPLAIN (ANALYZE, BUFFERS)
WITH RankedDocs AS (
    SELECT id, orig_id, title,
           ts_rank_cd(tsv, to_tsquery('english', 'perform')) AS rank_score,
           ROW_NUMBER() OVER (PARTITION BY orig_id ORDER BY ts_rank_cd(tsv, to_tsquery('english', 'perform')) DESC) as rn
    FROM documents
    WHERE tsv @@ to_tsquery('english', 'perform')
)
SELECT id, orig_id, title, rank_score
FROM RankedDocs
WHERE rn = 1
ORDER BY rank_score DESC
LIMIT 10;
