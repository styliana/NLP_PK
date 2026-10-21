-- Inicjalizacja bazy danych PostgreSQL dla Laboratorium nr 3
-- Poziom 5.0

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS documents (
    id BIGINT PRIMARY KEY,
    orig_id BIGINT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    tag VARCHAR(50) NOT NULL,
    rating NUMERIC(3, 1) NOT NULL,
    published_year INT NOT NULL,
    copy_no INT NOT NULL DEFAULT 0,
    tsv TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') || 
        setweight(to_tsvector('english', coalesce(content, '')), 'B')
    ) STORED
);

-- Indeks pełnotekstowy GIN na kolumnie tsvector
CREATE INDEX IF NOT EXISTS idx_documents_tsv ON documents USING GIN(tsv);

-- Indeksy pod zapytania filtrowane, sortowanie i agregacje
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_tag ON documents(tag);
CREATE INDEX IF NOT EXISTS idx_documents_rating ON documents(rating);
CREATE INDEX IF NOT EXISTS idx_documents_year ON documents(published_year);
CREATE INDEX IF NOT EXISTS idx_documents_orig_id ON documents(orig_id);
CREATE INDEX IF NOT EXISTS idx_documents_copy_no ON documents(copy_no);

-- Indeks trójgramowy GIN dla rozszerzenia: odporność na literówki (pg_trgm)
CREATE INDEX IF NOT EXISTS idx_documents_content_trgm ON documents USING GIN(content gin_trgm_ops);
