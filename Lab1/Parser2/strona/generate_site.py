"""Generator danych katalogu TechStore.

Strona nie zawiera rekordów w HTML – wszystko jest wczytywane JavaScriptem z jednego pliku
dane/produkty.json. Kolejność rekordów w pliku wyznacza porcje (po PER_CHUNK), czyli podstrony
katalogu (index.html?strona=N). Podstrona szczegółów (produkt.html?id=<id>) korzysta z tego samego pliku.

Utrudnienia zapisane w danych:
  1. ceny w formacie „1 299,00 zł”, a u części rekordów w EUR („302,99 €”) lub USD („$324.99”),
  2. braki wartości w polach „ocena” (null) i „gwarancja” (brak klucza), każde u >= 15% rekordów,
  3. 12 zduplikowanych rekordów, każdy w innej porcji (podstronie) niż oryginał.

Uruchomienie:  py generate_site.py
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 2026
ROOT = Path(__file__).resolve().parent
TOTAL_UNIQUE = 420
CHUNK_COUNT = 9          # porcja = podstrona katalogu (?strona=N)
PER_CHUNK = 48           # 9 × 48 = 432 rekordy = 420 unikalnych + 12 duplikatów
MISSING_SHARE_RATING = 0.183    # ok. 18% rekordów bez oceny
MISSING_SHARE_WARRANTY = 0.174  # ok. 17% rekordów bez gwarancji
FOREIGN_SHARE = 0.12     # ok. 12% cen w EUR / USD
RATES = {"EUR": 4.30, "USD": 4.00}

CATEGORIES = {
    "Laptopy": {
        "models": {"Lenovo": ["ThinkPad E14", "IdeaPad Slim 5", "Yoga 7"], "Dell": ["Inspiron 15", "Latitude 5440", "Vostro 3520"],
                   "ASUS": ["VivoBook 16", "ZenBook 14", "TUF Gaming A15"], "HP": ["ProBook 450", "Pavilion 15", "EliteBook 840"],
                   "Acer": ["Swift Go 14", "Aspire 5", "Nitro V15"]},
        "variants": ["8/256 GB", "16/512 GB", "16/1 TB", "32/1 TB", "32/2 TB"], "variant_is_color": False,
        "price": (2299, 7999), "warranty": 24, "weight": (1.2, 2.4),
        "set": "laptop, zasilacz, instrukcja",
        "specs": [("Procesor", "procesor", ["Intel Core i5-1335U", "Intel Core i7-1355U", "AMD Ryzen 5 7530U", "AMD Ryzen 7 7735HS"]),
                  ("Ekran", "ekran", ["14\" 1920×1200", "15,6\" 1920×1080", "16\" 2560×1600"]),
                  ("System operacyjny", "system-operacyjny", ["Windows 11 Home", "Windows 11 Pro", "bez systemu"])],
    },
    "Smartfony": {
        "models": {"Samsung": ["Galaxy A55", "Galaxy S24", "Galaxy A35"], "Xiaomi": ["Redmi Note 13", "Poco X6", "14T"],
                   "Motorola": ["Moto G84", "Edge 40", "Edge 50 Neo"], "Google": ["Pixel 8a", "Pixel 9"],
                   "Nokia": ["G42", "X30", "G60"], "Apple": ["iPhone 15"]},
        "variants": ["6/128 GB", "8/128 GB", "8/256 GB", "12/256 GB", "12/512 GB"], "variant_is_color": False,
        "price": (699, 4499), "warranty": 24, "weight": (0.16, 0.23),
        "set": "telefon, kabel USB-C, kluczyk do karty SIM",
        "specs": [("Przekątna ekranu", "przekatna-ekranu", ["6,1\"", "6,6\"", "6,7\""]),
                  ("Aparat główny", "aparat", ["50 Mpx", "64 Mpx", "108 Mpx", "200 Mpx"]),
                  ("Bateria", "bateria", ["4500 mAh", "5000 mAh", "5500 mAh"])],
    },
    "Słuchawki": {
        "models": {"Sony": ["WH-1000XM5", "WF-C700N", "WH-CH720N", "WF-1000XM5"], "JBL": ["Tune 760NC", "Live 670NC", "Tune Beam"],
                   "Sennheiser": ["HD 450BT", "Momentum 4", "Accentum"], "Jabra": ["Elite 85t", "Elite 8 Active"],
                   "Logitech": ["Zone Vibe 100", "G435"], "Bose": ["QuietComfort Ultra"]},
        "variants": ["czarne", "białe", "niebieskie", "beżowe", "zielone"], "variant_is_color": True,
        "price": (149, 1799), "warranty": 12, "weight": (0.04, 0.35),
        "set": "słuchawki, etui, kabel USB-C",
        "specs": [("Typ", "typ-sluchawek", ["nauszne", "douszne", "dokanałowe"]),
                  ("Łączność", "lacznosc", ["Bluetooth 5.3", "Bluetooth 5.2", "Bluetooth 5.3 + jack 3,5 mm"]),
                  ("Czas pracy", "czas-pracy", ["30 h", "40 h", "50 h", "60 h"])],
    },
    "Monitory": {
        "models": {"LG": ["27GP850", "24MR400", "32UN650"], "Dell": ["P2723DE", "S2721DS", "U2424H"],
                   "AOC": ["24G2U", "Q27G3XMN", "U32P2"], "BenQ": ["GW2785TC", "EW3280U", "MOBIUZ EX2710Q"],
                   "iiyama": ["ProLite XUB2493", "G-Master GB2770"], "Samsung": ["Odyssey G5"]},
        "variants": ["", "+ kabel DisplayPort", "+ uchwyt VESA", "+ kabel USB-C", "+ głośniki USB"], "variant_is_color": False,
        "price": (499, 2999), "warranty": 36, "weight": (3.2, 7.8),
        "set": "monitor, podstawa, kabel zasilający, kabel HDMI",
        "specs": [("Przekątna", "przekatna", ["23,8\"", "27\"", "31,5\""]),
                  ("Rozdzielczość", "rozdzielczosc", ["1920×1080", "2560×1440", "3840×2160"]),
                  ("Odświeżanie", "odswiezanie", ["75 Hz", "144 Hz", "165 Hz", "180 Hz"])],
    },
    "Drukarki": {
        "models": {"Brother": ["DCP-L2620DW", "MFC-L2800DW", "HL-L2445DW"], "HP": ["LaserJet M110we", "OfficeJet Pro 9120e", "Smart Tank 580"],
                   "Canon": ["PIXMA G650", "i-SENSYS MF453dw", "PIXMA TS5350i"], "Epson": ["EcoTank L3270", "EcoTank L8050", "WorkForce WF-2930"],
                   "Xerox": ["B230", "C235", "B225"]},
        "variants": ["", "+ zapasowy toner", "+ ryza papieru A4", "+ kabel USB", "+ etui na dokumenty"], "variant_is_color": False,
        "price": (349, 2499), "warranty": 24, "weight": (5.5, 15.0),
        "set": "drukarka, startowy materiał eksploatacyjny, kabel zasilający",
        "specs": [("Technologia druku", "technologia-druku", ["laserowa mono", "atramentowa kolor", "laserowa kolor"]),
                  ("Prędkość druku", "predkosc-druku", ["20 str./min", "30 str./min", "34 str./min"]),
                  ("Łączność", "lacznosc", ["Wi-Fi, USB", "Wi-Fi, LAN, USB", "USB"])],
    },
    "Akcesoria": {
        "models": {"Logitech": ["MX Master 3S", "K380", "MX Keys S", "G502 X"], "Razer": ["DeathAdder V3", "BlackWidow V4", "Basilisk V3"],
                   "SteelSeries": ["Apex 3 TKL", "Rival 3", "Aerox 5"], "Microsoft": ["Ergonomic Keyboard", "Bluetooth Mouse"],
                   "Trust": ["GXT 711 Dominus", "Ozaa", "GXT 922 Ybar"]},
        "variants": ["czarny", "biały", "grafitowy", "różowy", "niebieski"], "variant_is_color": True,
        "price": (79, 899), "warranty": 24, "weight": (0.07, 1.2),
        "set": "urządzenie, odbiornik/kabel, instrukcja",
        "specs": [("Łączność", "lacznosc", ["przewodowa USB", "bezprzewodowa 2,4 GHz", "Bluetooth"]),
                  ("Zasilanie", "zasilanie", ["bateria AA", "akumulator", "z kabla USB"]),
                  ("Kompatybilność", "kompatybilnosc", ["Windows, macOS", "Windows, macOS, Linux", "Windows"])],
    },
}
AVAILABILITY = [("dostepny", "Dostępny"), ("dostepny", "Dostępny"), ("dostepny", "Dostępny"),
                ("ostatnie-sztuki", "Ostatnie sztuki"), ("na-zamowienie", "Na zamówienie"), ("niedostepny", "Niedostępny")]
DELIVERY = {"dostepny": "24 h", "ostatnie-sztuki": "1–2 dni robocze", "na-zamowienie": "do 14 dni", "niedostepny": "brak terminu"}
COLORS = ["czarny", "srebrny", "biały", "grafitowy", "niebieski", "szary"]
MATERIALS = ["aluminium", "tworzywo sztuczne", "aluminium i tworzywo", "stal i tworzywo"]
COUNTRIES = ["Chiny", "Tajwan", "Wietnam", "Malezja", "Tajlandia", "Indie"]
NOUNS = {"Laptopy": "laptop", "Smartfony": "smartfon", "Słuchawki": "słuchawki", "Monitory": "monitor",
         "Drukarki": "drukarka", "Akcesoria": "akcesorium komputerowe"}
SELLERS = ["TechStore", "TechStore", "TechStore Outlet", "Partner: ElektroHurt"]


def slug(text):
    tr = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
    out = "".join(c if c.isalnum() else "-" for c in text.translate(tr).lower())
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


def money(value, currency):
    if currency == "USD":
        return f"${value:,.2f}"
    pl = f"{value:,.2f}".replace(",", " ").replace(".", ",")
    return f"{pl} €" if currency == "EUR" else f"{pl} zł"


def dec(value):
    return str(value).replace(".", ",")


def make_products():
    rng = random.Random(SEED)
    pools = {}
    for cat, cfg in CATEGORIES.items():
        combos = [(maker, model, var) for maker, models in cfg["models"].items() for model in models for var in cfg["variants"]]
        rng.shuffle(combos)
        pools[cat] = combos

    cats = list(CATEGORIES)
    products = []
    for i in range(TOTAL_UNIQUE):
        cat = cats[i % len(cats)]
        cfg = CATEGORIES[cat]
        maker, model, variant = pools[cat].pop()
        lo, hi = cfg["price"]
        price_pln = round(rng.uniform(lo, hi) / 10) * 10 - 0.01
        currency = "PLN"
        if rng.random() < FOREIGN_SHARE:
            currency = rng.choice(["EUR", "USD"])
        price = price_pln if currency == "PLN" else round(price_pln / RATES[currency]) - 0.01
        old_price = round(price * rng.uniform(1.08, 1.3)) - 0.01 if rng.random() < 0.3 else None
        avail_cls, avail_lbl = rng.choice(AVAILABILITY)
        added = date(2024, 1, 1) + timedelta(days=rng.randint(0, 990))
        w_lo, w_hi = cfg["weight"]
        weight = round(rng.uniform(w_lo, w_hi), 2)
        pid = 1001 + i
        products.append({
            "id": pid,
            "sku": f"{slug(cat)[:3].upper()}-{rng.randint(10000, 99999)}",
            "nazwa": " ".join(part for part in (maker, model, variant) if part),
            "kategoria": cat,
            "producent": maker,
            "cena": price,
            "cena_poprzednia": old_price,
            "waluta": currency,
            "dostepnosc": (avail_cls, avail_lbl),
            "stan": {"niedostepny": 0, "na-zamowienie": 0, "ostatnie-sztuki": rng.randint(1, 4)}.get(avail_cls, rng.randint(5, 120)),
            "ocena": round(rng.uniform(3.1, 5.0), 1),
            "opinie": rng.randint(0, 2400),
            "data": added,
            "gwarancja": cfg["warranty"] + rng.choice([0, 0, 12]),
            "kolor": variant if cfg["variant_is_color"] else rng.choice(COLORS),
            "waga": weight,
            # atrybuty widoczne tylko na podstronie szczegółów
            "ean": "590" + "".join(str(rng.randint(0, 9)) for _ in range(10)),
            "numer_katalogowy": f"{slug(maker)[:2].upper()}{slug(model).upper().replace('-', '')[:8]}-{rng.randint(100, 999)}",
            "wymiary": " × ".join(dec(round(rng.uniform(a, b), 1)) for a, b in [(4, 60), (3, 45), (1, 25)]) + " cm",
            "material": rng.choice(MATERIALS),
            "kraj": rng.choice(COUNTRIES),
            "czas_dostawy": DELIVERY[avail_cls],
            "koszt_dostawy": 0.0 if price_pln >= 300 else 14.99,
            "zestaw": cfg["set"],
            "sprzedawca": rng.choice(SELLERS),
            "data_premiery": added - timedelta(days=rng.randint(30, 700)),
            "specyfikacja": [(label, cls, rng.choice(values)) for label, cls, values in cfg["specs"]],
            "opis": (f"{maker} {model} to {NOUNS[cat]} z oferty TechStore. "
                     f"Produkt dostarczany jest w oryginalnym opakowaniu producenta i objęty pełną obsługą serwisową."),
        })

    # Braki wartości: ocena i gwarancja (niezależnie wylosowane rekordy)
    for p in rng.sample(products, round(len(products) * MISSING_SHARE_RATING)):
        p["ocena"] = None
    for p in rng.sample(products, round(len(products) * MISSING_SHARE_WARRANTY)):
        p["gwarancja"] = None
    return products, rng


def paginate(products, rng, page_count, per_page):
    """Dzieli unikalne rekordy na strony i dokłada duplikaty na innych stronach niż oryginał."""
    total = len(products)
    base_sizes = [total // page_count + (1 if i < total % page_count else 0) for i in range(page_count)]
    pages, start = [], 0
    for size in base_sizes:
        pages.append(list(products[start:start + size]))
        start += size
    home_page = {p["id"]: n for n, page in enumerate(pages) for p in page}

    used = set()
    duplicates = []
    for n, page in enumerate(pages):
        while len(page) < per_page:
            candidates = [p for p in products if home_page[p["id"]] != n and p["id"] not in used]
            original = rng.choice(candidates)
            used.add(original["id"])
            page.insert(rng.randint(0, len(page)), original)
            duplicates.append((original["id"], home_page[original["id"]] + 1, n + 1))
    return pages, home_page, duplicates

def json_record(p):
    """Rekord w pliku JSON. Wartości zapisane tak jak na stronie (ceny jako tekst w walucie oferty)."""
    rec = {
        "id": p["id"],
        "sku": p["sku"],
        "nazwa": p["nazwa"],
        "kategoria": p["kategoria"],
        "producent": p["producent"],
        "cena": money(p["cena"], p["waluta"]),
        "cena_poprzednia": money(p["cena_poprzednia"], p["waluta"]) if p["cena_poprzednia"] else None,
        "dostepnosc": p["dostepnosc"][1],
        "stan_magazynowy": p["stan"],
        "ocena": p["ocena"],  # brak oceny -> null
        "liczba_opinii": p["opinie"],
        "data_dodania": p["data"].isoformat(),
        "kolor": p["kolor"],
        "waga": f"{dec(p['waga'])} kg",
        "ean": p["ean"],
        "numer_katalogowy": p["numer_katalogowy"],
        "wymiary": p["wymiary"],
        "material": p["material"],
        "kraj_pochodzenia": p["kraj"],
        "data_premiery": p["data_premiery"].isoformat(),
        "sprzedawca": p["sprzedawca"],
        "zawartosc_zestawu": p["zestaw"],
        "czas_dostawy": p["czas_dostawy"],
        "koszt_dostawy": money(p["koszt_dostawy"], "PLN"),
        "specyfikacja": {label: value for label, _cls, value in p["specyfikacja"]},
        "opis": p["opis"],
        "link": f"produkt.html?id={p['id']}",
    }
    if p["gwarancja"] is not None:  # brak gwarancji -> brak klucza
        rec["gwarancja"] = f"{p['gwarancja']} mies."
    return rec


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def share(items, pred):
    return sum(1 for p in items if pred(p)) / len(items)


def main():
    products, rng = make_products()
    chunks, _home, duplicates = paginate(products, rng, CHUNK_COUNT, PER_CHUNK)

    listed = [p for chunk in chunks for p in chunk]
    write_json(ROOT / "dane" / "produkty.json", {
        "liczba_rekordow": len(listed),
        "liczba_porcji": CHUNK_COUNT,
        "rozmiar_porcji": PER_CHUNK,
        "produkty": [json_record(p) for p in listed],
    })

    print(f"Porcje (podstrony): {len(chunks)}, rekordów {len(listed)}, unikalnych {len(products)}")
    for name, items in (("unikalne", products), ("z duplikatami", listed)):
        print(f"   [{name}] obca waluta {share(items, lambda p: p['waluta'] != 'PLN'):.1%}, "
              f"brak oceny {share(items, lambda p: p['ocena'] is None):.1%}, "
              f"brak gwarancji {share(items, lambda p: p['gwarancja'] is None):.1%}")
    print("Duplikaty (id: porcja oryginału -> porcja kopii): " + ", ".join(f"{pid}: {a}->{b}" for pid, a, b in duplicates))
    print(f"Atrybuty rekordu: {len(json_record(products[0])) + 2} (specyfikacja = 3 parametry)")


if __name__ == "__main__":
    main()
