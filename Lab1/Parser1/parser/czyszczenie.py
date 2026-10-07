import re
from datetime import date, datetime, timedelta

# Teksty, którymi serwis oznacza brak wartości
BRAKI = {"", "-", "—", "brak", "brak oceny", "brak ocen", "brak informacji", "brak danych", "none", "null"}

WALUTY = {"zł": "PLN", "pln": "PLN", "eur": "EUR", "€": "EUR", "$": "USD", "usd": "USD"}

MIESIACE_SLOWNIE = {"dożywotnia producenta": None, "zgodnie z rękojmią": 24}


def normalizuj(tekst):
    if tekst is None:
        return None
    tekst = re.sub(r"\s+", " ", str(tekst).replace("\xa0", " ")).strip()
    return None if tekst.lower() in BRAKI else tekst


def parsuj_cene(tekst):
    tekst = normalizuj(tekst)
    if tekst is None:
        return None, None
    waluta = next((kod for znak, kod in WALUTY.items() if znak in tekst.lower()), None)
    liczba = re.sub(r"[^\d,.]", "", tekst)
    if not liczba:
        return None, waluta
    if "," in liczba and "." in liczba:          # format z separatorem tysięcy: ostatni znak to separator dziesiętny
        dziesietny = "," if liczba.rfind(",") > liczba.rfind(".") else "."
        tysiace = "." if dziesietny == "," else ","
        liczba = liczba.replace(tysiace, "").replace(dziesietny, ".")
    elif "," in liczba:                           # polski zapis: przecinek dziesiętny
        liczba = liczba.replace(",", ".")
    return float(liczba), waluta


def parsuj_ocene(tekst):
    tekst = normalizuj(tekst)
    if tekst is None:
        return None
    dopasowanie = re.search(r"\d+(?:[.,]\d+)?", tekst)
    return float(dopasowanie.group().replace(",", ".")) if dopasowanie else None


def parsuj_liczbe_calkowita(tekst):
    tekst = normalizuj(tekst)
    if tekst is None:
        return None
    dopasowanie = re.search(r"\d[\d ]*", tekst)
    return int(dopasowanie.group().replace(" ", "")) if dopasowanie else None


def parsuj_gwarancje(tekst):
    tekst = normalizuj(tekst)
    if tekst is None:
        return None, None
    if tekst.lower() in MIESIACE_SLOWNIE:
        return tekst, MIESIACE_SLOWNIE[tekst.lower()]
    dopasowanie = re.search(r"(\d+)\s*(mies|lat|rok)", tekst.lower())
    if not dopasowanie:
        return tekst, None
    liczba = int(dopasowanie.group(1))
    return tekst, liczba * 12 if dopasowanie.group(2) in ("lat", "rok") else liczba


def parsuj_date(tekst, dzis=None):
    """Ujednolica datę do ISO 'RRRR-MM-DD'.

    Obsługuje: '2026-08-26', '26.08.2026', '26/08/2026', 'dzisiaj', 'wczoraj', 'przedwczoraj', 'N dni temu'.
    Daty względne liczone są od `dzis` (domyślnie dzień uruchomienia parsera).
    """
    tekst = normalizuj(tekst)
    if tekst is None:
        return None
    dzis = dzis or date.today()
    wzgledne = {"dzisiaj": 0, "dziś": 0, "wczoraj": 1, "przedwczoraj": 2}
    if tekst.lower() in wzgledne:
        return (dzis - timedelta(days=wzgledne[tekst.lower()])).isoformat()
    dni_temu = re.fullmatch(r"(\d+)\s+dni\s+temu", tekst.lower())
    if dni_temu:
        return (dzis - timedelta(days=int(dni_temu.group(1)))).isoformat()
    for wzorzec in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(tekst, wzorzec).date().isoformat()
        except ValueError:
            continue
    return None


def parsuj_wage(tekst):
    tekst = normalizuj(tekst)
    if tekst is None:
        return None
    dopasowanie = re.search(r"\d+(?:[.,]\d+)?", tekst)
    return float(dopasowanie.group().replace(",", ".")) if dopasowanie else None


def parsuj_tak_nie(tekst):
    tekst = normalizuj(tekst)
    if tekst is None:
        return None
    return {"tak": True, "nie": False}.get(tekst.lower())


def wyczysc_rekord(surowy, dzis=None):
    cena, waluta = parsuj_cene(surowy.get("cena"))
    gwarancja, gwarancja_mies = parsuj_gwarancje(surowy.get("gwarancja"))
    return {
        "id": parsuj_liczbe_calkowita(surowy.get("id")),
        "nazwa": normalizuj(surowy.get("nazwa")),
        "kategoria": normalizuj(surowy.get("kategoria")),
        "producent": normalizuj(surowy.get("producent")),
        "cena": cena,
        "waluta": waluta,
        "dostepnosc": normalizuj(surowy.get("dostepnosc")),
        "stan": normalizuj(surowy.get("stan")),
        "ocena": parsuj_ocene(surowy.get("ocena")),
        "liczba_opinii": parsuj_liczbe_calkowita(surowy.get("liczba_opinii")),
        "gwarancja": gwarancja,
        "gwarancja_miesiace": gwarancja_mies,
        "data_dodania": parsuj_date(surowy.get("data_dodania"), dzis),
        "darmowa_dostawa": parsuj_tak_nie(surowy.get("darmowa_dostawa")),
        "sku": normalizuj(surowy.get("sku")),
        "ean": normalizuj(surowy.get("ean")),
        "kolor": normalizuj(surowy.get("kolor")),
        "waga_kg": parsuj_wage(surowy.get("waga")),
        "wymiary": normalizuj(surowy.get("wymiary")),
        "material": normalizuj(surowy.get("material")),
        "kraj_pochodzenia": normalizuj(surowy.get("kraj_pochodzenia")),
        "zasilanie": normalizuj(surowy.get("zasilanie")),
        "certyfikaty": normalizuj(surowy.get("certyfikaty")),
        "zawartosc_zestawu": normalizuj(surowy.get("zawartosc_zestawu")),
        "specyfikacja_ukryta": normalizuj(surowy.get("specyfikacja_ukryta")),
        "opis": normalizuj(surowy.get("opis")),
        "link": normalizuj(surowy.get("link")),
        "zrodlo_listy": surowy.get("zrodlo"),
        "strona_listy": surowy.get("strona"),
    }
