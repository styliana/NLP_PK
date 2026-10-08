import argparse
import json
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

KATALOG = Path(__file__).resolve().parent
WYNIKI = KATALOG / "wyniki"
WYKRESY = WYNIKI / "wykresy"
# Przybliżone kursy – tylko do sprowadzenia cen do wspólnej waluty w analizie
KURSY_PLN = {"PLN": 1.0, "EUR": 4.30, "USD": 4.00}
LICZBOWE = ["cena", "cena_pln", "ocena", "liczba_opinii", "gwarancja_miesiace", "waga_kg"]


def tabela_md(df, indeks=True, format_liczb="{:.2f}"):
    df = df.rename_axis(df.index.name or "cecha").reset_index() if indeks else df
    wiersze = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    for _, wiersz in df.iterrows():
        komorki = [format_liczb.format(v) if isinstance(v, float) else str(v) for v in wiersz]
        wiersze.append("| " + " | ".join(komorki) + " |")
    return "\n".join(wiersze)


def kontrola_jakosci(df, podsumowanie, lista):
    sekcje = ["## 1. Kontrola jakości danych\n"]
    lista_df = pd.DataFrame(lista)
    sekcje.append(f"- Liczba rekordów po czyszczeniu: **{len(df)}**, liczba kolumn: **{len(df.columns)}**.")

    braki = pd.DataFrame({"braki_szt": df.isna().sum(), "braki_%": (df.isna().mean() * 100).round(1)})
    braki = braki[braki["braki_szt"] > 0].sort_values("braki_szt", ascending=False)
    sekcje.append("\n### Braki w kolumnach\n")
    sekcje.append(tabela_md(braki, format_liczb="{:.1f}") if len(braki) else "Brak braków.")
    sekcje.append("\nKolumny nieujęte w tabeli nie mają braków.")
    dozywotnia = (df["gwarancja"] == "Dożywotnia producenta").sum()
    sekcje.append("\n- `ocena` i `gwarancja`: braki zapisane w serwisie jako „Brak oceny” / „-” / „Brak informacji” "
                  "(utrudnienie autora) – parser zamienił je na puste wartości.")
    sekcje.append(f"- `gwarancja_miesiace` ma więcej braków niż `gwarancja`: oprócz {df['gwarancja'].isna().sum()} "
                  f"brakujących gwarancji jest {dozywotnia} gwarancji „Dożywotnia producenta”, których nie da się "
                  "wyrazić w miesiącach – to świadoma decyzja, nie błąd parsera.")

    dom = podsumowanie["dom_wczytaj_wiecej"][-1]
    sekcje.append("\n### Duplikaty\n")
    sekcje.append(tabela_md(pd.DataFrame([
        {"etap": "DOM po „Wczytaj więcej” (wszystkie elementy [data-id])", "rekordy": dom["elementy"], "unikalne id": dom["unikalne"]},
        {"etap": "lista z 9 podstron (karty + tabela)", "rekordy": len(lista_df), "unikalne id": lista_df["id"].nunique()},
        {"etap": "po usunięciu duplikatów", "rekordy": len(df), "unikalne id": df["id"].nunique()},
    ]), indeks=False))
    powtorzone = lista_df[lista_df.duplicated("id", keep=False)].groupby("id")["strona"].apply(list)
    sekcje.append(f"\nZduplikowane id w katalogu ({len(powtorzone)}): "
                  + ", ".join(f"{i} (strony {s})" for i, s in powtorzone.items()) + ".")

    sekcje.append("\n### Typy kolumn liczbowych\n")
    typy = pd.DataFrame({"typ": df[LICZBOWE].dtypes.astype(str),
                         "czy_liczbowa": [pd.api.types.is_numeric_dtype(df[k]) for k in LICZBOWE]})
    sekcje.append(tabela_md(typy))

    sekcje.append("\n### Wartości odstające (reguła 1,5 × IQR)\n")
    odstajace = []
    for kolumna in ["cena", "cena_pln", "ocena", "liczba_opinii", "waga_kg"]:
        s = df[kolumna].dropna()
        q1, q3 = s.quantile([0.25, 0.75])
        dol, gora = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        poza = s[(s < dol) | (s > gora)]
        odstajace.append({"kolumna": kolumna, "dolna_granica": dol, "gorna_granica": gora,
                          "odstajace_szt": len(poza), "min": s.min(), "max": s.max()})
    sekcje.append(tabela_md(pd.DataFrame(odstajace), indeks=False))
    top = df.nlargest(5, "cena_pln")[["id", "nazwa", "cena", "waluta", "cena_pln"]]
    sekcje.append("\nNajdroższe produkty po przeliczeniu na PLN:\n\n" + tabela_md(top, indeks=False))
    obce = df[df["waluta"] != "PLN"]
    sekcje.append(f"\n**Interpretacja:** w walucie oryginalnej (`cena`) nie ma wartości odstających. Wszystkie "
                  f"wartości odstające `cena_pln` to produkty w EUR/USD (łącznie {len(obce)} szt.) po przeliczeniu "
                  "kursem. To anomalia danych, a nie błąd parsera: generator serwisu losuje ceny z tego samego zakresu "
                  "niezależnie od waluty, więc np. smartfon za 7825 EUR (ok. 33 tys. zł) jest nierealistyczny. "
                  "Dlatego ceny analizowane są osobno w walucie oryginalnej i po przeliczeniu.")
    sekcje.append(f"\nKontrola błędu przecinka: maksymalna cena w walucie oryginalnej to {df['cena'].max():.2f} "
                  f"(gdyby parser zgubił przecinek, ceny byłyby rzędu setek tysięcy).")
    return "\n".join(sekcje)


def statystyki(df):
    sekcje = ["## 2. Statystyki opisowe\n"]
    wiersze = []
    for kolumna in LICZBOWE:
        s = df[kolumna].dropna().astype(float)
        moda = s.mode()
        wiersze.append({"cecha": kolumna, "n": len(s), "średnia": s.mean(), "mediana": s.median(),
                        "moda": moda.iloc[0] if len(moda) else None, "Q1": s.quantile(0.25),
                        "Q3": s.quantile(0.75), "min": s.min(), "max": s.max()})
    sekcje.append(tabela_md(pd.DataFrame(wiersze), indeks=False))
    sekcje.append("\nModa cen jest mało informatywna – ceny są ciągłe i prawie każda występuje raz, więc moda to po "
                  "prostu najmniejsza wartość. Średnia `cena_pln` jest wyraźnie wyższa od mediany przez ceny w EUR/USD "
                  "(rozkład prawoskośny).")

    sekcje.append("\n### Rozkłady kategoryczne\n")
    for kolumna in ["kategoria", "waluta", "dostepnosc", "stan"]:
        licznosci = df[kolumna].value_counts(dropna=False).rename("liczba").to_frame()
        sekcje.append(f"**{kolumna}**\n\n" + tabela_md(licznosci) + "\n")
    return "\n".join(sekcje)


def wykresy(df):
    WYKRESY.mkdir(parents=True, exist_ok=True)
    pliki = []

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(df["cena_pln"].dropna(), bins=30, color="#4C72B0", edgecolor="white")
    ax.set(title="Rozkład cen (przeliczonych na PLN)", xlabel="cena [PLN]", ylabel="liczba produktów")
    pliki.append(("Histogram cen", "histogram_cen.png"))
    fig.tight_layout(); fig.savefig(WYKRESY / pliki[-1][1], dpi=120); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(df["ocena"].dropna(), bins=19, color="#55A868", edgecolor="white")
    ax.set(title="Rozkład ocen klientów", xlabel="ocena", ylabel="liczba produktów")
    pliki.append(("Histogram ocen", "histogram_ocen.png"))
    fig.tight_layout(); fig.savefig(WYKRESY / pliki[-1][1], dpi=120); plt.close(fig)

    kategorie = sorted(df["kategoria"].dropna().unique())
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.boxplot([df.loc[df["kategoria"] == k, "cena_pln"].dropna() for k in kategorie], tick_labels=kategorie)
    ax.set(title="Ceny wg kategorii (PLN)", ylabel="cena [PLN]")
    ax.tick_params(axis="x", rotation=30)
    pliki.append(("Wykres pudełkowy cen wg kategorii", "boxplot_cen_kategorie.png"))
    fig.tight_layout(); fig.savefig(WYKRESY / pliki[-1][1], dpi=120); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    oceniane = df.dropna(subset=["ocena"])
    ax.scatter(oceniane["ocena"], oceniane["liczba_opinii"], alpha=0.5, s=14)
    ax.set(title="Ocena a liczba opinii", xlabel="ocena", ylabel="liczba opinii")
    pliki.append(("Ocena a liczba opinii", "scatter_ocena_opinie.png"))
    fig.tight_layout(); fig.savefig(WYKRESY / pliki[-1][1], dpi=120); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    przedzialy = range(0, int(df["cena"].max()) + 200, 200)  # wspólne przedziały po 200 dla obu grup
    for wartosc, kolor in ((True, "#55A868"), (False, "#C44E52")):
        ax.hist(df.loc[df["darmowa_dostawa"] == wartosc, "cena"], bins=przedzialy, alpha=0.8, color=kolor,
                label=f"darmowa dostawa: {'tak' if wartosc else 'nie'}")
    ax.axvline(300, color="black", linestyle="--", linewidth=1)
    ax.set(title="Cena a darmowa dostawa", xlabel="cena (waluta oryginalna)", ylabel="liczba produktów")
    ax.legend()
    pliki.append(("Cena a darmowa dostawa", "cena_darmowa_dostawa.png"))
    fig.tight_layout(); fig.savefig(WYKRESY / pliki[-1][1], dpi=120); plt.close(fig)

    return "## 3. Wykresy\n\n" + "\n\n".join(f"### {tytul}\n\n![{tytul}](wykresy/{plik})" for tytul, plik in pliki)


def korelacje(df):
    kolumny = ["cena_pln", "ocena", "liczba_opinii", "gwarancja_miesiace", "waga_kg", "darmowa_dostawa_int"]
    dane = df.assign(darmowa_dostawa_int=df["darmowa_dostawa"].astype(float))[kolumny].astype(float)
    pearson = dane.corr(method="pearson")
    spearman = dane.corr(method="spearman")
    prog = df["cena"] > 300
    zgodnosc = (prog == df["darmowa_dostawa"]).mean() * 100
    oceniane = df.dropna(subset=["ocena"])
    return "\n".join([
        "## 4. Korelacje\n",
        "### Pearson\n", tabela_md(pearson),
        "\n### Spearman\n", tabela_md(spearman),
        "\n### Komentarz\n",
        f"- **cena ↔ darmowa dostawa**: współczynnik jest niski (Spearman "
        f"{spearman.loc['cena_pln', 'darmowa_dostawa_int']:.2f}), choć zależność jest pełna: reguła „darmowa dostawa, "
        f"gdy cena > 300” zgadza się w {zgodnosc:.1f}% rekordów. Zależność jest progowa, a produktów tańszych niż 300 "
        f"jest tylko {(df['cena'] <= 300).sum()}, więc korelacja (miara zależności liniowej / monotonicznej w całym "
        "zakresie) jej nie oddaje. Ma ona sens merytoryczny – to typowa polityka sklepu.",
        f"- **ocena ↔ liczba opinii** (tylko produkty z oceną, n={len(oceniane)}): Pearson "
        f"{oceniane['ocena'].corr(oceniane['liczba_opinii']):.2f} – brak zależności. W prawdziwym sklepie można by "
        "oczekiwać słabej dodatniej korelacji; tu dane są fikcyjne i losowane niezależnie.",
        f"- **cena ↔ waga**: Pearson {pearson.loc['cena_pln', 'waga_kg']:.2f} – brak zależności, co jest "
        "podejrzane merytorycznie (np. laptopy są i cięższe, i droższe od akcesoriów), ale wynika z losowego generatora danych.",
        "- Pozostałe pary mają współczynniki bliskie zera – cechy są w danych niezależne.",
    ])


def main():
    global WYNIKI, WYKRESY
    argumenty = argparse.ArgumentParser(description="Analiza danych z parsera")
    argumenty.add_argument("--wyniki", default=str(WYNIKI))
    WYNIKI = Path(argumenty.parse_args().wyniki)
    WYKRESY = WYNIKI / "wykresy"
    df = pd.read_csv(WYNIKI / "produkty.csv", encoding="utf-8-sig", dtype={"ean": str, "sku": str})
    podsumowanie = json.loads((WYNIKI / "podsumowanie.json").read_text(encoding="utf-8"))
    lista = json.loads((WYNIKI / "surowe_lista.json").read_text(encoding="utf-8"))
    df["cena_pln"] = (df["cena"] * df["waluta"].map(KURSY_PLN)).round(2)

    html = podsumowanie["surowy_html"]["katalog"]
    dom = podsumowanie["dom_wczytaj_wiecej"]
    naglowek = "\n".join([
        "# Raport analizy danych – TechStore (Parser1)\n",
        f"Data parsowania: {podsumowanie['data_parsowania']}, czas działania parsera: {podsumowanie['czas_s']:.0f} s "
        f"({podsumowanie['tryb']}).\n",
        "## 0. Surowy HTML a drzewo DOM\n",
        tabela_md(pd.DataFrame([
            {"źródło": "surowy HTML (requests, bez JS)", "elementy z data-id": html["rekordy_data_id"], "unikalne id": 0},
            {"źródło": "DOM po wczytaniu strony (Selenium)", "elementy z data-id": dom[0]["elementy"], "unikalne id": dom[0]["unikalne"]},
            {"źródło": f"DOM po {len(dom) - 1} × „Wczytaj więcej”", "elementy z data-id": dom[-1]["elementy"], "unikalne id": dom[-1]["unikalne"]},
        ]), indeks=False),
        f"\nKontrolnie: surowy HTML zawiera {html['naglowki_tabeli_kontrolnie']} nagłówków tabeli, więc parsowanie "
        "działa – rekordów brak, bo dodaje je dopiero JavaScript (app.js).\n",
    ])
    raport = "\n\n".join([naglowek, kontrola_jakosci(df, podsumowanie, lista), statystyki(df), wykresy(df), korelacje(df)])
    (WYNIKI / "raport_analizy.md").write_text(raport, encoding="utf-8")
    print(f"Zapisano {WYNIKI / 'raport_analizy.md'} i wykresy w {WYKRESY}")


if __name__ == "__main__":
    main()
