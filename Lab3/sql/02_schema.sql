-- Szablon tabeli; {t} = documents (100%), documents_p50 (50%), documents_p10 (10%).
-- Kolumna tsv jest wyliczana przy wstawianiu wiersza: tytuł z wagą A, abstrakt z wagą B,
-- konfiguracja 'english' = stoplista angielska + stemmer Snowball (Porter2).

CREATE TABLE {t} (
    id          BIGINT PRIMARY KEY,
    orig_id     BIGINT   NOT NULL,   -- id oryginału (kopie wskazują na oryginał)
    copy_no     SMALLINT NOT NULL,   -- 0 = oryginał, 1 = kopia
    arxiv_id    TEXT     NOT NULL,
    title       TEXT     NOT NULL,
    abstract    TEXT     NOT NULL,
    field       TEXT     NOT NULL,   -- grupa arXiv (8 wartości)
    category    TEXT     NOT NULL,   -- kategoria główna (~150 wartości)
    categories  TEXT     NOT NULL,   -- wszystkie kategorie, rozdzielone spacją
    year        SMALLINT NOT NULL,
    n_versions  SMALLINT NOT NULL,
    tsv TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('english', title), 'A') ||
        setweight(to_tsvector('english', abstract), 'B')
    ) STORED
);
