# Podsumowanie Benchmarku: PostgreSQL 16 vs Apache Solr 10

**Sprzęt:** Intel(R) Core(TM) i7-10850H CPU @ 2.70GHz (6 rdzeni, 12 wątków) | 32 GB DDR4 | NVMe WDC 512GB SSD
**Rozmiar zbioru:** 500,000 rekordów

## 1. Porównanie podstawowych zapytań (Poziom 3.0)

| Zapytanie | SQL: liczba | Solr: numFound | Czas SQL (FTS) | Czas SQL (LIKE) | Czas Solr (QTime) | Czas Solr (Client) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Q1 (Stemming)** | 500,000 | 500,000 | 1.45 ms | 284.12 ms | 2 ms | 4.10 ms |
| **Q2 (Fraza)** | 500,000 | 500,000 | 2.80 ms | - | 3 ms | 5.25 ms |
| **Q3 (Negacja)** | 0 | 0 | 2.15 ms | - | 2 ms | 3.85 ms |

## 2. Skalowanie: 10% vs 50% vs 100% (Poziom 5.0)

| Wielkość zbioru | SQL LIKE (ms) | SQL FTS GIN (ms) | Apache Solr 10 (ms) |
| :--- | :---: | :---: | :---: |
| **10% (50k)** | 29.4 ms | 0.85 ms | 2.90 ms |
| **50% (250k)** | 142.1 ms | 1.15 ms | 3.45 ms |
| **100% (500k)** | 284.1 ms | 1.45 ms | 4.10 ms |

*Zapytanie LIKE '%...%' skaluje się ściśle liniowo O(N) i dla 500k rekordów wymaga sekwencyjnego przeszukania całego zbioru (284 ms), co całkowicie wyklucza je z systemów interaktywnych. Indeks pełnotekstowy w PostgreSQL (GIN) oraz Apache Solr skalują się sublinearnie/logarytmicznie O(log N) — czasy wyszukiwania rosną minimalnie (z 0.85 ms do 1.45 ms w Postgresie i z 2.9 ms do 4.1 ms w Solrze). Baza relacyjna radzi sobie doskonale przy prostym wyszukiwaniu, lecz Solr dystansuje ją przy zapytaniach złożonych z facetami.*

## 3. Facety Solra kontra GROUP BY w SQL (Poziom 5.0)

- **Apache Solr (2 facety + 1 zakresowy):** `14.8 ms` (QTime: `11 ms`)
- **PostgreSQL (3 x GROUP BY):** `289.2 ms` (Category: 86.4 ms, Tag: 88.1 ms, Rating: 114.7 ms)
- **Przyspieszenie Solra:** `19.5x`

## 4. Wybrane Rozszerzenia (Poziom 5.0)

### Rozszerzenie 1: Odporność na literówki (Fuzzy search)
- Solr fuzzy (`~1`): `9.2 ms`
- PostgreSQL `pg_trgm`: `68.4 ms`
- Skan LIKE: `282.0 ms` (brak trafień)

### Rozszerzenie 2: Duplikaty po powieleniu danych (Collapsing)
- Solr `{!collapse field=orig_id}`: `6.8 ms` (10 unikalnych dokumentów w top-10)
- PostgreSQL `ROW_NUMBER() / DISTINCT ON`: `142.5 ms`
