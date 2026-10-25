-- Inicjalizacja bazy PostgreSQL dla Laboratorium nr 3 (uruchamiana przez docker-entrypoint).
-- Tabele tworzy loader (scripts/loader.py) z szablonów 02_schema.sql i 03_indexes.sql,
-- żeby osobno zmierzyć czas ładowania (COPY) i czas budowy indeksów.

CREATE EXTENSION IF NOT EXISTS pg_trgm;
