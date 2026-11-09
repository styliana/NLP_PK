#!/usr/bin/env python3
"""
Zamienia wyniki/benchmark_results.json na wyniki/benchmark_summary.md - tabele gotowe do sprawozdania.
Użycie samodzielne: python scripts/summary.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import RESULTS_DIR  # noqa: E402


def n(x):
    return f"{x:,}".replace(",", " ") if isinstance(x, int) else str(x)


def t(x):
    if x is None:
        return "—"
    return f"{x:.1f}" if x >= 10 else f"{x:.2f}"


def table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(" --- " for _ in header) + "|"]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def write_summary(r, path):
    out = []
    w = out.append
    env = r["environment"]
    w("# Wyniki pomiarów: PostgreSQL vs Apache Solr\n")
    w(f"Wygenerowano: {r['generated_at']}. Mediana z {r['runs']} uruchomień po jednym rozgrzewającym "
      f"(rozgrzany cache). Czasy w ms.\n")

    w("## Środowisko\n")
    w(table(["Parametr", "Wartość"], [
        ["Procesor", env.get("cpu")], ["RAM [GB]", env.get("ram_gb")], ["Dysk", env.get("disk")],
        ["System", env.get("os")], ["Pamięć dla Dockera [GB]", env.get("docker_mem_gb")],
        ["PostgreSQL", env.get("postgres_version")],
        ["shared_buffers / work_mem", f"{env.get('postgres_shared_buffers')} / {env.get('postgres_work_mem')}"],
        ["Solr", env.get("solr_version")], ["Java (Solr)", env.get("solr_jvm")],
        ["Heap Solra (SOLR_HEAP) [MB]", env.get("solr_heap_max_mb")], ["Python", env.get("python")],
    ]))

    ds = r.get("dataset_stats")
    if ds:
        w("## Zbiór danych\n")
        w(table(["Cecha", "Wartość"], [
            ["Źródło", ds["source_url"]], ["Licencja", ds["license"]], ["Próbkowanie", ds["sampling"]],
            ["Rekordy", f"{n(ds['total_records'])} ({n(ds['originals'])} oryginałów + {n(ds['copies'])} kopii)"],
            ["Powielenie", ds["copy_rule"]], ["Rozmiar CSV [MB]", ds["csv_size_mb"]],
            ["Długość abstraktu [znaki]", f"śr. {ds['abstract_chars_avg']}, mediana {ds['abstract_chars_median']}, "
                                          f"min {ds['abstract_chars_min']}, max {ds['abstract_chars_max']}"],
            ["field (grupa arXiv)", f"{ds['distinct_fields']} wartości"],
            ["category (kategoria główna)", f"{ds['distinct_categories']} wartości"],
            ["year", f"{ds['year_min']}–{ds['year_max']}"],
        ]))
        w("Rozkład pola `field`:\n")
        w(table(["field", "liczba oryginałów"], [[k, n(v)] for k, v in ds["field_counts"].items()]))
        w("Przykładowy rekord:\n\n```json\n" + json.dumps(ds["sample_record"], indent=2, ensure_ascii=False)
          + "\n```\n")

    lt = r.get("load_times")
    if lt:
        w("## Ładowanie i indeksowanie\n")
        rows = []
        for label, v in lt.items():
            pg, so = v["postgres"], v["solr"]
            rows.append([label, n(v["rows"]), pg["copy_s"], pg["index_s"], pg["vacuum_analyze_s"], pg["total_s"],
                         pg["table_total_mb"], so["upload_s"], so["commit_s"], so["total_s"], so["index_mb"]])
        w(table(["Zbiór", "Rekordy", "PG COPY [s]", "PG indeksy [s]", "PG VACUUM ANALYZE [s]", "PG razem [s]",
                 "PG rozmiar [MB]", "Solr wysyłka [s]", "Solr commit [s]", "Solr razem [s]", "Solr indeks [MB]"],
                rows))
        w("PG COPY obejmuje wyliczenie kolumny `tsv` (GENERATED STORED); \"PG indeksy\" = GIN na tsv, "
          "trigramy na title, B-tree na orig_id. Solr: paczki po 5000 dokumentów, jeden commit na końcu.\n")

    q = r["queries"]
    w(f"## Zapytania Q1–Q3 (pełny zbiór, {n(r['records'])} rekordów)\n")
    w(table(["Zapytanie", "LIKE: wyniki", "SQL FTS: wyniki", "Solr: numFound",
             "LIKE [ms]", "FTS count [ms]", "FTS top-10 ranking [ms]", "Solr QTime", "Solr klient [ms]",
             "Solr z cache wyników [ms]"],
            [[v["name"], n(v["like_count"]), n(v["fts_count"]), n(v["solr_numFound"]),
              t(v["like"]["median_ms"]), t(v["fts_count_query"]["median_ms"]), t(v["fts_top10_query"]["median_ms"]),
              v["solr"]["median_qtime_ms"], t(v["solr"]["median_client_ms"]), t(v["solr_cached"]["median_client_ms"])]
             for v in q.values()]))
    w("Czasy SQL wg EXPLAIN ANALYZE (Execution Time, bez narzutu sieci/klienta):\n")
    w(table(["Zapytanie", "LIKE", "FTS count", "FTS top-10"],
            [[k, t(v["like"].get("explain_execution_ms")), t(v["fts_count_query"].get("explain_execution_ms")),
              t(v["fts_top10_query"].get("explain_execution_ms"))] for k, v in q.items()]))

    w("### Dokładne zapytania\n")
    for k, v in q.items():
        w(f"**{v['name']}**\n")
        w(f"- LIKE: `{v['like']['sql']}`")
        w(f"- SQL FTS: `{v['fts_count_query']['sql']}`")
        w(f"- SQL ranking: `{v['fts_top10_query']['sql']}`")
        w(f"- Solr (lucene): {v['solr_cached']['url']}")
        w(f"- Solr (fq, fl, sort, rows): {v['solr_fq_sort_example']['url']} → numFound "
          f"{n(v['solr_fq_sort_example']['numFound'])} (SQL z `year >= 2015`: {n(v['sql_fq_example_count'])})")
        w(f"- Solr eDisMax + hl: {v['edismax']['url']}\n")

    w("## Ranking top-10: ts_rank_cd vs eDisMax (qf=title^3 abstract)\n")
    w(table(["Zapytanie", "Wspólne id w top-10", "Pary kopii w top-10 SQL", "Pary kopii w top-10 Solr",
             "eDisMax+hl [ms]", "ts_headline top-10 [ms]"],
            [[k, f"{v['top10_overlap']}/10", v["top10_duplicate_pairs_sql"], v["top10_duplicate_pairs_solr"],
              t(v["edismax"]["median_client_ms"]), t(v["ts_headline"]["median_ms"])] for k, v in q.items()]))
    for k, v in q.items():
        w(f"### {v['name']}\n")
        rows = []
        for i in range(10):
            s = v["top10_sql"][i] if i < len(v["top10_sql"]) else None
            o = v["top10_solr"][i] if i < len(v["top10_solr"]) else None
            rows.append([i + 1,
                         f"{s['id']} ({s['score']}) {s['title'][:70]}" if s else "",
                         f"{o['id']} ({o['score']}) {o['title'][:70]}" if o else ""])
        w(table(["#", "PostgreSQL ts_rank_cd: id (rank) tytuł", "Solr eDisMax: id (score) tytuł"], rows))
        w(f"Podświetlanie dokumentu {v['highlight_doc_id']}:\n")
        w(f"- Solr `hl`: {v['highlight_solr']}")
        w(f"- PostgreSQL `ts_headline`: {v['highlight_sql']}\n")

    g = r["groupby"]
    w("## GROUP BY dla wyników Q1 (4.0)\n")
    w(f"`{g['sql']}` — {t(g['median_ms'])} ms\n")
    w(table(["field", "liczba"], [[a, n(b)] for a, b in g["result"]]))

    w("## Skalowanie 10% / 50% / 100% (5.0)\n")
    rows = []
    for label, v in r["scaling"].items():
        for k, m in v["queries"].items():
            rows.append([label, n(v["records"]), k, n(m["fts_count"]), n(m["solr_numFound"]), t(m["like_ms"]),
                         t(m["fts_count_ms"]), t(m["fts_top10_ms"]), t(m["solr_client_ms"]), m["solr_qtime_ms"]])
    w(table(["Zbiór", "Rekordy", "Zapytanie", "FTS wyniki", "Solr numFound", "LIKE [ms]", "FTS count [ms]",
             "FTS top-10 [ms]", "Solr klient [ms]", "Solr QTime"], rows))

    w("## Facety vs GROUP BY (5.0)\n")
    w("Jedno zapytanie Solra: `facet.field=field`, `facet.field=category` (top 10), "
      "`facet.range=year` (1990–2025, co 5 lat) wobec trzech zapytań GROUP BY i jednego z GROUPING SETS.\n")
    rows = []
    for label, v in r["facets_vs_groupby"].items():
        rows.append(["Q1 (simulate)" if label == "Q1" else "cały zbiór (*:*)", n(v["solr"]["numFound"]),
                     t(v["solr"]["median_client_ms"]), v["solr"]["median_qtime_ms"],
                     t(v["sql_field"]["median_ms"]), t(v["sql_category"]["median_ms"]), t(v["sql_year"]["median_ms"]),
                     t(v["sql_three_queries_ms"]), t(v["sql_grouping_sets"]["median_ms"]),
                     ", ".join(f"{a}: {'tak' if b else 'nie'}" for a, b in v["counts_equal"].items())])
    w(table(["Zapytanie", "Dokumenty", "Solr klient [ms]", "Solr QTime", "GROUP BY field", "GROUP BY category",
             "GROUP BY year", "SQL razem (3 zapytania)", "SQL GROUPING SETS", "Liczności zgodne"], rows))
    for label, v in r["facets_vs_groupby"].items():
        w(f"Liczności dla {label}:\n")
        keys = list(v["solr_counts"]["year"].keys())
        w(table(["Przedział lat", "Solr", "SQL"],
                [[k, n(v["solr_counts"]["year"].get(k)), n(v["sql_counts"]["year"].get(k, 0))] for k in keys]))
        w(table(["field", "Solr", "SQL"],
                [[k, n(c), n(v["sql_counts"]["field"].get(k, 0))] for k, c in v["solr_counts"]["field"].items()]))

    c = r["ext_collapse"]
    w("## Wpływ powielenia danych i rozszerzenie: collapse po orig_id\n")
    w(table(["Wariant", "Dokumenty / grupy", "Pary kopii w top-10", "Czas [ms]"], [
        ["Solr eDisMax bez deduplikacji", n(c["solr_plain"]["numFound"]), c["solr_plain"]["duplicate_pairs"],
         t(c["solr_plain"]["median_client_ms"])],
        ["Solr `fq={!collapse field=orig_id}`", n(c["solr_collapse"]["numFound"]),
         c["solr_collapse"]["duplicate_pairs"], t(c["solr_collapse"]["median_client_ms"])],
        ["Solr `fq=copy_no:0`", n(c["solr_numFound_without_copies"]), "—", "—"],
        ["SQL top-10 bez deduplikacji", "—", c["sql_plain_top10"]["duplicate_pairs"],
         t(c["sql_plain_top10"]["median_ms"])],
        ["SQL `DISTINCT ON (orig_id)`", n(c["sql_distinct_orig_count"]), c["sql_distinct_on"]["duplicate_pairs"],
         t(c["sql_distinct_on"]["median_ms"])],
    ]))

    w("## Rozszerzenie: odporność na literówki\n")
    rows = []
    for typo, v in r["ext_fuzzy"].items():
        rows.append([f"{typo} (→ {v['correct_word']})", f"{n(v['like']['count'])} / {t(v['like']['median_ms'])}",
                     f"{n(v['pg_trgm']['count'])} / {t(v['pg_trgm']['median_ms'])}",
                     f"{n(v['solr_exact']['count'])} / {t(v['solr_exact']['median_client_ms'])}",
                     f"{n(v['solr_fuzzy']['count'])} / {t(v['solr_fuzzy']['median_client_ms'])}",
                     n(v["solr_correct_word_count"])])
    w(table(["Słowo z błędem", "LIKE w tytule: wyniki / ms", "pg_trgm `<%`: wyniki / ms",
             "Solr dokładnie: wyniki / ms", "Solr `~2`: wyniki / ms", "Solr poprawne słowo: wyniki"], rows))
    for typo, v in r["ext_fuzzy"].items():
        w(f"Przykłady dla `{typo}` — pg_trgm: " + "; ".join(f"{a} ({b})" for a, b in v["pg_trgm"]["top5"][:3]))
        w(f"Solr fuzzy: " + "; ".join(v["solr_fuzzy"]["top5"][:3]) + "\n")

    w("## Rozszerzenie: własny typ pola `text_en_lab` + Analysis vs to_tsvector\n")
    for a in r["ext_analysis"]:
        w(f"**{a['sentence']}**\n")
        w(f"- Solr (Analysis, łańcuch: {' → '.join(s['stage'] for s in a['solr_chain'])}): "
          f"`{' '.join(a['solr_tokens'])}`")
        w(f"- PostgreSQL `to_tsvector('english', …)`: `{a['pg_to_tsvector']}`\n")

    w("## Rozszerzenie: głębokie stronicowanie\n")
    w(table(["Pozycja", "Solr start/rows [ms]", "Solr cursorMark [ms]", "Ta sama strona",
             "SQL OFFSET [ms]", "SQL keyset (id > x) [ms]"],
            [[n(p["position"]), t(p["solr_start_ms"]), t(p["solr_cursor_ms"]), "tak" if p["solr_same_page"] else "nie",
              t(p["sql_offset_ms"]), t(p["sql_keyset_ms"])] for p in r["ext_deep_paging"]]))

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Zapisano {path}")


if __name__ == "__main__":
    with open(os.path.join(RESULTS_DIR, "benchmark_results.json"), encoding="utf-8") as f:
        write_summary(json.load(f), os.path.join(RESULTS_DIR, "benchmark_summary.md"))
