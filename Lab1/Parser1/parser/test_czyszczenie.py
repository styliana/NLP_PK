from datetime import date

import pytest

from czyszczenie import (normalizuj, parsuj_cene, parsuj_date, parsuj_gwarancje, parsuj_liczbe_calkowita,
                         parsuj_ocene, parsuj_tak_nie, parsuj_wage, wyczysc_rekord)

DZIS = date(2026, 10, 7)


@pytest.mark.parametrize("tekst, oczekiwane", [
    ("1 201,35\xa0zł", (1201.35, "PLN")),       # twarda spacja przed walutą
    ("7 726,24 zł", (7726.24, "PLN")),
    ("99,00 zł", (99.0, "PLN")),
    ("799,00\xa0EUR", (799.0, "EUR")),
    ("$649.99", (649.99, "USD")),
    ("$1 234.56", (1234.56, "USD")),            # separator tysięcy w cenie w dolarach
    ("$1,234.56", (1234.56, "USD")),
    ("1.234,56 €", (1234.56, "EUR")),
    (None, (None, None)),
    ("", (None, None)),
])
def test_parsuj_cene(tekst, oczekiwane):
    assert parsuj_cene(tekst) == oczekiwane


def test_cena_nie_jest_mnozona_przez_100():
    # klasyczny błąd parsera: usunięcie przecinka daje 120135 zamiast 1201.35
    assert parsuj_cene("1 201,35 zł")[0] < 2000


@pytest.mark.parametrize("tekst, oczekiwane", [
    ("4.7/5.0 ⭐", 4.7),
    ("4.7 / 5.0 ⭐", 4.7),
    ("3.2", 3.2),
    ("Brak oceny", None),
    ("Brak ocen", None),
    ("-", None),
    (None, None),
])
def test_parsuj_ocene(tekst, oczekiwane):
    assert parsuj_ocene(tekst) == oczekiwane


@pytest.mark.parametrize("tekst, oczekiwane", [
    ("2026-04-03", "2026-04-03"),
    ("03.04.2026", "2026-04-03"),
    ("03/04/2026", "2026-04-03"),
    ("dzisiaj", "2026-10-07"),
    ("wczoraj", "2026-10-06"),
    ("przedwczoraj", "2026-10-05"),
    ("3 dni temu", "2026-10-04"),
    ("nieznany format", None),
    (None, None),
])
def test_parsuj_date(tekst, oczekiwane):
    assert parsuj_date(tekst, DZIS) == oczekiwane


@pytest.mark.parametrize("tekst, oczekiwane", [
    ("24 miesiące", ("24 miesiące", 24)),
    ("12 miesięcy", ("12 miesięcy", 12)),
    ("Dożywotnia producenta", ("Dożywotnia producenta", None)),
    ("Brak informacji", (None, None)),
    ("-", (None, None)),
])
def test_parsuj_gwarancje(tekst, oczekiwane):
    assert parsuj_gwarancje(tekst) == oczekiwane


def test_pozostale_parsery():
    assert parsuj_liczbe_calkowita("142 opinii") == 142
    assert parsuj_liczbe_calkowita("0 opinii") == 0
    assert parsuj_wage("1.75 kg") == 1.75
    assert parsuj_tak_nie("Tak") is True
    assert parsuj_tak_nie("Nie") is False
    assert normalizuj("  Dell \xa0 ") == "Dell"
    assert normalizuj("Brak danych") is None


def test_wyczysc_rekord_z_brakami_nie_rzuca_wyjatku():
    rekord = wyczysc_rekord({"id": "5", "cena": "99,00 zł", "ocena": "-", "gwarancja": None}, DZIS)
    assert rekord["id"] == 5
    assert rekord["cena"] == 99.0
    assert rekord["ocena"] is None
    assert rekord["gwarancja"] is None
    assert rekord["kolor"] is None
