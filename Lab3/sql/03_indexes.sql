-- Indeksy budowane po załadowaniu danych (szybciej niż aktualizacja indeksu wiersz po wierszu).

-- indeks pełnotekstowy (odwrócony) na tsvector
CREATE INDEX {t}_tsv_gin ON {t} USING GIN (tsv);

-- indeks trójgramowy na tytule - rozszerzenie "odporność na literówki" (operator <%)
CREATE INDEX {t}_title_trgm ON {t} USING GIN (title gin_trgm_ops);

-- deduplikacja kopii (DISTINCT ON orig_id)
CREATE INDEX {t}_orig_id ON {t} (orig_id);
