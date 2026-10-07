#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
MODUŁ: test_parser.py
OPIS:  Testy jednostkowe (unittest) funkcji czyszczących dane parsera.
       Spełnia wymóg rozszerzenia poziomu 4.0:
       "minimum 3 testy jednostkowe funkcji czyszczących dane".
LAB:   Laboratorium NLP - Zadanie 1 (Rola: PARSER)
=============================================================================
"""

import sys
import unittest
from parser import parsuj_cene, oczysc_produkt, filtruj_i_deduplikuj

# Zapewnienie kodowania UTF-8 w konsoli
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class TestFunkcjiCzyszczacychParsera(unittest.TestCase):
    """Zestaw testów weryfikujących poprawność czyszczenia i normalizacji danych."""

    def test_1_parsuj_cene_rozne_waluty_i_formaty(self):
        """Test 1: Sprawdza poprawne wyodrębnienie kwoty, waluty i przeliczenia na PLN."""
        # 1. Standardowa polska cena ze spacją i przecinkiem
        kwota, waluta, pln = parsuj_cene("1 299,00 zł")
        self.assertEqual(kwota, 1299.00)
        self.assertEqual(waluta, "PLN")
        self.assertEqual(pln, 1299.00)

        # 2. Cena w EUR z symbolem euro
        kwota_eur, waluta_eur, pln_eur = parsuj_cene("100,00 €")
        self.assertEqual(kwota_eur, 100.00)
        self.assertEqual(waluta_eur, "EUR")
        self.assertEqual(pln_eur, 430.00)  # 100 * 4.30

        # 3. Cena w USD z symbolem dolara na początku
        kwota_usd, waluta_usd, pln_usd = parsuj_cene("$250.00")
        self.assertEqual(kwota_usd, 250.00)
        self.assertEqual(waluta_usd, "USD")
        self.assertEqual(pln_usd, 1000.00)  # 250 * 4.00

        # 4. Cena z twardą spacją (non-breaking space \xa0)
        kwota_nbsp, _, _ = parsuj_cene("3\xa0499,99 zł")
        self.assertEqual(kwota_nbsp, 3499.99)

        # 5. Pusta cena lub None
        self.assertEqual(parsuj_cene(None), (None, None, None))
        self.assertEqual(parsuj_cene(""), (None, None, None))

    def test_2_bezpieczna_obsuga_brakow_danych(self):
        """Test 2: Sprawdza, czy braki pól (ocena: null, brak klucza gwarancja) nie rzucają wyjątków."""
        produkt_z_brakami = {
            "id": 9999,
            "sku": "TEST-001",
            "nazwa": "Produkt Testowy",
            "kategoria": "Akcesoria",
            "cena": "99,00 zł",
            "ocena": None,              # Celowy brak oceny (null)
            # Celowo brak klucza "gwarancja"
        }

        # Funkcja nie może rzucić błędu (np. KeyError)
        oczyszczony = oczysc_produkt(produkt_z_brakami)

        self.assertIsNone(oczyszczony["ocena"])
        self.assertEqual(oczyszczony["gwarancja"], "brak informacji")
        self.assertEqual(oczyszczony["nazwa"], "Produkt Testowy")
        self.assertEqual(oczyszczony["cena_pln"], 99.00)

    def test_3_deduplikacja_rekordow(self):
        """Test 3: Sprawdza wykrywanie i odrzucanie zduplikowanych rekordów po identyfikatorze id."""
        dane_testowe = [
            {"id": 1, "sku": "A1", "nazwa": "Produkt 1", "cena": "100 zł"},
            {"id": 2, "sku": "A2", "nazwa": "Produkt 2", "cena": "200 zł"},
            {"id": 1, "sku": "A1", "nazwa": "Produkt 1 (duplikat)", "cena": "100 zł"},
            {"id": 3, "sku": "A3", "nazwa": "Produkt 3", "cena": "300 zł"},
            {"id": 2, "sku": "A2", "nazwa": "Produkt 2 (duplikat)", "cena": "200 zł"},
        ]

        unikalne, stats = filtruj_i_deduplikuj(dane_testowe)

        self.assertEqual(len(unikalne), 3)
        self.assertEqual(stats["odrzucone_duplikaty"], 2)
        self.assertEqual(stats["pobrane_ogolem"], 5)
        self.assertEqual([r["id"] for r in unikalne], [1, 2, 3])

    def test_4_walidacja_typow_kolumn(self):
        """Test 4: Sprawdza, czy kolumny liczbowe mają właściwe typy (float/int), a tekstowe są stringami."""
        produkt = {
            "id": 500,
            "sku": "LAP-123",
            "nazwa": "Laptop Pro",
            "cena": "2 500,50 zł",
            "waga": "1,85 kg",
            "ocena": "4.5",
            "liczba_opinii": "12",
        }
        wynik = oczysc_produkt(produkt)

        self.assertIsInstance(wynik["id"], int)
        self.assertIsInstance(wynik["cena_pln"], float)
        self.assertIsInstance(wynik["waga_kg"], float)
        self.assertIsInstance(wynik["ocena"], float)
        self.assertIsInstance(wynik["nazwa"], str)


if __name__ == "__main__":
    print("=== URUCHOMIENIE TESTÓW JEDNOSTKOWYCH PARSERA ===")
    unittest.main(verbosity=2)
