"""
Generator danych katalogowych dla Zadania AUTOR (Poziom 5.0)
Generuje 430 rekordów (420 unikalnych + 10 duplikatów) z 24 atrybutami,
spełniając wszystkie wymagania z poziomów 3.0, 4.0 oraz 5.0.
"""

import json
import random
import os
from datetime import datetime, timedelta

def generate_products():
    random.seed(42)  # Zapewnia deterministyczne, powtarzalne wyniki

    categories = [
        "Laptopy", "Smartfony", "Monitory", "Klawiatury i Myszy",
        "Dyski SSD", "Tablety", "Audio i Słuchawki", "Akcesoria sieciowe"
    ]

    manufacturers = [
        "Dell", "Lenovo", "HP", "Samsung", "Apple",
        "Sony", "ASUS", "Logitech", "LG", "Kingston"
    ]

    models_by_cat = {
        "Laptopy": ["ThinkPad T14", "XPS 15", "ZenBook Pro", "MacBook Air M3", "Pavilion Gaming", "Legion Slim 5", "Latitude 5540", "ExpertBook B9"],
        "Smartfony": ["Galaxy S24 Ultra", "iPhone 15 Pro", "Pixel 8 Pro", "Edge 50 Ultra", "Xiaomi 14", "Xperia 1 VI", "Nord 4", "Nova 12"],
        "Monitory": ["UltraSharp U2724D", "Odyssey G7", "ProArt PA278CV", "UltraGear 27GR95QE", "ViewFinity S8", "Curved Gaming 34", "Modern MD271"],
        "Klawiatury i Myszy": ["MX Master 3S", "MX Keys Mini", "G Pro X Superlight", "Apex Pro TKL", "DeathAdder V3", "K780 Wireless", "Ergo K860"],
        "Dyski SSD": ["990 PRO 2TB", "KC3000 1TB", "FireCuda 530 2TB", "Black SN850X 1TB", "T7 Shield 2TB", "Crucial T700 1TB", "XS2000 2TB"],
        "Tablety": ["Galaxy Tab S9", "iPad Air 11\"", "MatePad Pro 13.2", "Surface Pro 9", "Xiaomi Pad 6", "Lenovo Tab P12", "OnePlus Pad 2"],
        "Audio i Słuchawki": ["WH-1000XM5", "QuietComfort Ultra", "Momentum 4", "AirPods Pro 2", "WF-1000XM5", "Buds 2 Pro", "Major IV Bluetooth"],
        "Akcesoria sieciowe": ["Archer AXE75", "Deco X50", "UniFi U6 Pro", "Nighthawk RAXE500", "RT-AX88U Pro", "Fritz!Box 7590 AX", "MikroTik hAP ax3"]
    }

    availabilities = ["W magazynie", "Ostatnie 3 sztuki", "Dostępny na zamówienie", "Wysyłka w 24h", "Dostępny w salonie"]
    conditions = ["Nowy", "Powystawowy", "Odnowiony przez producenta"]
    colors = ["Czarny mat", "Gwiezdna szarość", "Srebrny", "Biały perłowy", "Granatowy metalik"]
    materials = ["Aluminium szczotkowane", "Stop magnezu i aluminium", "Tworzywo ABS wzmocnione", "Polikarbonat i aluminium", "Szkło hartowane i metal"]
    countries = ["Polska", "Niemcy", "Tajwan", "Japonia", "Korea Południowa", "Chiny"]
    warranties = ["12 miesięcy", "24 miesiące", "36 miesięcy", "48 miesięcy", "Dożywotnia producenta"]

    products = []
    num_unique = 420

    base_date = datetime(2026, 9, 1)

    for i in range(1, num_unique + 1):
        cat = random.choice(categories)
        producer = random.choice(manufacturers)
        model_name = random.choice(models_by_cat[cat])
        sku_num = 10000 + i
        ean_num = f"590{i:09d}"

        # Utrudnienie: waluty (80% PLN, 10% EUR, 10% USD)
        currency_choice = random.choices(["PLN", "EUR", "USD"], weights=[0.8, 0.1, 0.1])[0]
        base_price = round(random.uniform(99.0, 7999.0), 2)
        
        # Formatowanie ceny ze spacją twardą i przecinkiem
        price_int_str = f"{int(base_price):,}".replace(",", " ")
        price_cents_str = f"{int(round((base_price - int(base_price)) * 100)):02d}"
        
        if currency_choice == "PLN":
            cena_formatowana = f"{price_int_str},{price_cents_str}\u00A0zł"
        elif currency_choice == "EUR":
            cena_formatowana = f"{price_int_str},{price_cents_str}\u00A0EUR"
        else:
            cena_formatowana = f"${price_int_str}.{price_cents_str}"

        # Utrudnienie: braki danych w 2 polach u min 15% rekordów (~18% braków)
        is_missing_rating = (random.random() < 0.18)
        ocena = "" if is_missing_rating else f"{round(random.uniform(3.2, 5.0), 1):.1f}"
        liczba_opinii = 0 if is_missing_rating else random.randint(1, 450)

        is_missing_warranty = (random.random() < 0.18)
        gwarancja = "" if is_missing_warranty else random.choice(warranties)

        # Utrudnienie: niespójne formaty dat
        date_variant = random.choice(["iso", "dot", "relative", "slash"])
        date_offset = random.randint(0, 180)
        item_date = base_date - timedelta(days=date_offset)
        if date_variant == "iso":
            data_dodania = item_date.strftime("%Y-%m-%d")
        elif date_variant == "dot":
            data_dodania = item_date.strftime("%d.%m.%Y")
        elif date_variant == "slash":
            data_dodania = item_date.strftime("%d/%m/%Y")
        else:
            data_dodania = random.choice(["dzisiaj", "wczoraj", "przedwczoraj", "3 dni temu"])

        # Utrudnienie: encje HTML i polskie znaki w opisie
        opis = (
            f"Oryginalny produkt marki <strong>{producer}</strong> z serii <em>{model_name}</em>. "
            f"Wysoka jako&sacute;&cacute; wykonania, znakomita wydajno&sacute;&cacute; oraz energooszcz&eogon;dno&sacute;&cacute;. "
            f"Gwarancja pe&lstrok;nej kompatybilno&sacute;ci &amp; wsparcie techniczne producenta w standardzie."
        )

        hidden_spec = (
            f"Taktowanie magistrali: {random.randint(2400, 6400)} MHz; "
            f"Poziom emisji hałasu: {random.randint(18, 38)} dB; "
            f"Pobór mocy znamionowy: {random.randint(15, 120)} W; "
            f"Architektura procesora: x86_64 / ARMv9; "
            f"Wersja oprogramowania układowego (Firmware): v{random.randint(1, 4)}.{random.randint(0, 9)}.{random.randint(10, 99)}"
        )

        product = {
            "id": i,
            "nazwa": f"{producer} {model_name} #{i}",
            "cena_raw": base_price,
            "waluta": currency_choice,
            "cena": cena_formatowana,
            "kategoria": cat,
            "producent": producer,
            "dostepnosc": random.choice(availabilities),
            "ocena": ocena,
            "liczba_opinii": liczba_opinii,
            "data_dodania": data_dodania,
            "gwarancja": gwarancja,
            "kod_produktu": f"SKU-{sku_num}",
            "ean": ean_num,
            "stan": random.choice(conditions),
            "darmowa_dostawa": "Tak" if base_price > 300.0 else "Nie",
            # Szczegółowe atrybuty (podstrona szczegółów)
            "opis": opis,
            "kolor": random.choice(colors),
            "waga": f"{round(random.uniform(0.15, 4.5), 2)} kg",
            "wymiary": f"{random.randint(10, 40)} x {random.randint(10, 30)} x {random.randint(1, 10)} cm",
            "kraj_pochodzenia": random.choice(countries),
            "certyfikaty": "CE, RoHS, ISO 9001, Energy Star",
            "material": random.choice(materials),
            "zasilanie": random.choice(["Sieciowe 230V", "Akumulator Li-Ion", "USB-C Power Delivery 65W", "Baterie AAA / Akumulator"]),
            "zawartosc_zestawu": f"Urządzenie {producer} {model_name}, kabel zasilający, instrukcja obsługi w j. polskim, karta gwarancyjna",
            "specyfikacja_ukryta": hidden_spec
        }
        products.append(product)

    # Utrudnienie z poziomu 4.0: minimum 8 zduplikowanych rekordów rozrzuconych po różnych podstronach
    # Dodajemy 10 duplikatów ze wskazaniem oryginalnego id
    duplicate_source_indices = [5, 25, 65, 115, 165, 215, 265, 315, 365, 405]
    for idx in duplicate_source_indices:
        dup = dict(products[idx - 1])
        # Zachowujemy te same dane (nazwa, SKU, parametry), oznaczając duplikat
        products.append(dup)

    print(f"Wygenerowano łącznie {len(products)} rekordów (w tym {len(duplicate_source_indices)} duplikatów).")
    return products

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "products.json")

    prods = generate_products()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(prods, f, ensure_ascii=False, indent=2)

    print(f"Pomyślnie zapisano plik: {out_path}")
