"""Parser serwisu TechStore (Parser1) – rola PARSER, poziom 5.0.

Przebieg:
  1. surowy HTML przez requests (bez przeglądarki) – liczba rekordów do porównania z DOM,
  2. Selenium: „Wczytaj więcej” aż do wyczerpania rekordów – liczba rekordów w DOM,
  3. Selenium: wszystkie podstrony katalogu (?page=N) – karty + wiersze tabeli,
  4. Selenium: podstrona szczegółów każdego produktu (z rozwinięciem <details>),
  5. połączenie danych, czyszczenie, usunięcie duplikatów, eksport CSV + JSON + XLSX.

Odporność: jawne oczekiwanie (WebDriverWait), ponawianie z opóźnieniem wykładniczym (1 s, 2 s, 4 s…),
obsługa kodu 429 z nagłówkiem Retry-After, zrzut ekranu i źródła strony przy błędzie,
zapis postępu (checkpoint) i wznawianie przerwanej sesji, log do pliku.

Uruchomienie (serwis partnera musi działać: `py server.py` w folderze Parser1):
    py scraper.py                     # pełny przebieg
    py scraper.py --limit 5           # test: tylko 5 podstron szczegółów
    py scraper.py --headless          # bez okna przeglądarki
"""
import argparse
import json
import logging
import time
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from czyszczenie import wyczysc_rekord

KATALOG = Path(__file__).resolve().parent
SELEKTOR_REKORDU = "[data-id]"
SELEKTOR_KARTY = "article.produkt-karta"
SELEKTOR_WIERSZA = "tr.produkt-wiersz"
MAKS_PROB = 5

log = logging.getLogger("parser")
statystyki = Counter()

def tekst(element, selektor):
    znalezione = element.find_elements(By.CSS_SELECTOR, selektor)
    return znalezione[0].text if znalezione else None


def karta_na_slownik(karta):
    return {
        "zrodlo": "karta",
        "id": karta.get_attribute("data-id"),
        "sku": karta.get_attribute("data-sku"),
        "ean": karta.get_attribute("data-ean"),
        "nazwa": tekst(karta, ".nazwa-produktu"),
        "cena": tekst(karta, ".cena"),
        "kategoria": tekst(karta, ".kategoria"),
        "producent": tekst(karta, ".producent"),
        "dostepnosc": tekst(karta, ".dostepnosc"),
        "ocena": tekst(karta, ".ocena"),
        "liczba_opinii": tekst(karta, ".liczba-opinii"),
        "gwarancja": tekst(karta, ".gwarancja"),
        "data_dodania": tekst(karta, ".data-dodania"),
        "stan": tekst(karta, ".stan"),
        "darmowa_dostawa": tekst(karta, ".darmowa-dostawa"),
        "link": karta.find_element(By.CSS_SELECTOR, ".nazwa-produktu").get_attribute("href"),
    }


def wiersz_na_slownik(wiersz):
    akapit = tekst(wiersz, ".niezamkniety-akapit")  # "Stan: Powystawowy | EAN: 590000000026"
    stan = None
    if akapit and "Stan:" in akapit:
        stan = akapit.split("|")[0].replace("Stan:", "").strip()

    return {
        "zrodlo": "tabela",
        "id": wiersz.get_attribute("data-id"),
        "sku": wiersz.get_attribute("data-sku"),
        "ean": wiersz.get_attribute("data-ean"),
        "nazwa": tekst(wiersz, ".nazwa-produktu"),
        "cena": tekst(wiersz, ".kol-cena"),
        "kategoria": tekst(wiersz, ".kol-kategoria"),
        "producent": tekst(wiersz, ".kol-producent"),
        "dostepnosc": tekst(wiersz, ".kol-dostepnosc"),
        "ocena": tekst(wiersz, ".kol-ocena"),
        "liczba_opinii": None,      # brak w tabeli
        "gwarancja": tekst(wiersz, ".kol-gwarancja"),
        "data_dodania": tekst(wiersz, ".kol-data"),
        "stan": stan,
        "darmowa_dostawa": None,    # brak w tabeli
        "link": wiersz.find_element(By.CSS_SELECTOR, ".nazwa-produktu").get_attribute("href"),
    }


def element_na_slownik(element):
    return karta_na_slownik(element) if element.tag_name == "article" else wiersz_na_slownik(element)


def unikalne_id(driver):
    return {el.get_attribute("data-id") for el in driver.find_elements(By.CSS_SELECTOR, SELEKTOR_REKORDU)}


POLA_SZCZEGOLOW = {
    "nazwa": ".nazwa-produktu",
    "producent": ".producent",
    "sku": ".kod-produktu",
    "ean": ".ean",
    "cena": ".cena",
    "stan": ".stan",
    "ocena": ".ocena",
    "liczba_opinii": ".liczba-opinii",
    "gwarancja": ".gwarancja",
    "darmowa_dostawa": ".darmowa-dostawa",
    "data_dodania": ".data-dodania",
    "kolor": ".kolor",
    "waga": ".waga",
    "wymiary": ".wymiary",
    "material": ".material",
    "kraj_pochodzenia": ".kraj-pochodzenia",
    "zasilanie": ".zasilanie",
    "certyfikaty": ".certyfikaty",
    "zawartosc_zestawu": ".zawartosc-zestawu",
    "opis": ".opis-tresc",
}


def szczegoly_na_slownik(driver):
    karta = driver.find_element(By.CSS_SELECTOR, "article.szczegoly-karta")
    wynik = {pole: tekst(karta, selektor) for pole, selektor in POLA_SZCZEGOLOW.items()}
    wynik["id"] = karta.get_attribute("data-id")

    # Specyfikacja jest ukryta w zwiniętym <details>: .text zwraca pusty napis, dopóki nie klikniemy <summary>.
    ukryta = karta.find_element(By.CSS_SELECTOR, ".specyfikacja-ukryta-tekst")
    if ukryta.text:
        log.warning("Specyfikacja widoczna przed kliknięciem (id=%s)", wynik["id"])
    karta.find_element(By.CSS_SELECTOR, "#btn-rozwin-details").click()
    WebDriverWait(driver, 5).until(lambda d: ukryta.is_displayed() and ukryta.text.strip())
    wynik["specyfikacja_ukryta"] = ukryta.text
    return wynik


class Blad429(Exception):
    def __init__(self, retry_after, adresy):
        super().__init__(f"HTTP 429 dla: {', '.join(adresy)} (Retry-After: {retry_after} s)")
        self.retry_after = retry_after


class Przegladarka:
    def __init__(self, url_bazowy, opoznienie, headless, katalog_bledow):
        opcje = webdriver.ChromeOptions()
        if headless:
            opcje.add_argument("--headless=new")
        opcje.add_argument("--window-size=1400,1000")
        opcje.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        opcje.add_experimental_option("prefs", {"net.network_prediction_options": 2})
        self.driver = webdriver.Chrome(options=opcje)
        self.driver.set_page_load_timeout(30)
        self.url_bazowy = url_bazowy.rstrip("/")
        self.opoznienie = opoznienie
        self.katalog_bledow = katalog_bledow
        self.ostatnie_zadanie = 0.0

    def _statusy(self):
        wynik = []
        for wpis in self.driver.get_log("performance"):
            wiadomosc = json.loads(wpis["message"])["message"]
            if wiadomosc["method"] != "Network.responseReceived":
                continue
            odp = wiadomosc["params"]["response"]
            if odp["url"].startswith(self.url_bazowy):
                naglowki = {k.lower(): v for k, v in odp["headers"].items()}
                wynik.append((odp["status"], odp["url"][len(self.url_bazowy):], naglowki.get("retry-after")))
        return wynik

    def otworz(self, sciezka, gotowe):
        odczekaj = self.opoznienie - (time.monotonic() - self.ostatnie_zadanie)
        if odczekaj > 0:
            time.sleep(odczekaj)
        self._statusy()  # wyczyść dziennik
        self.ostatnie_zadanie = time.monotonic()
        statystyki["wejscia_na_strony"] += 1
        self.driver.get(self.url_bazowy + sciezka)

        odpowiedzi = []

        def gotowe_albo_429(driver):
            odpowiedzi.extend(self._statusy())
            return any(s == 429 for s, _, _ in odpowiedzi) or gotowe(driver)

        WebDriverWait(self.driver, 15).until(gotowe_albo_429)
        odrzucone = [(adres, ra) for s, adres, ra in odpowiedzi if s == 429]
        if odrzucone and not gotowe(self.driver):
            statystyki["odpowiedzi_429"] += len(odrzucone)
            retry_after = max(int(ra) if ra and str(ra).isdigit() else 1 for _, ra in odrzucone)
            raise Blad429(retry_after, [adres for adres, _ in odrzucone])

    def zrzut_bledu(self, opis):
        self.katalog_bledow.mkdir(parents=True, exist_ok=True)
        nazwa = f"{time.strftime('%Y%m%d-%H%M%S')}_{opis}".replace("?", "_").replace("/", "_").replace("=", "-")
        try:
            self.driver.save_screenshot(str(self.katalog_bledow / f"{nazwa}.png"))
            (self.katalog_bledow / f"{nazwa}.html").write_text(self.driver.page_source, encoding="utf-8")
        except WebDriverException:
            log.exception("Nie udało się zapisać zrzutu błędu")

    def zamknij(self):
        self.driver.quit()


def ponawiaj(przegladarka, opis, funkcja):
    """Wywołuje `funkcja()`; przy błędzie ponawia z opóźnieniem 1 s, 2 s, 4 s, 8 s (maks. MAKS_PROB prób).
    Przy 429 czeka co najmniej tyle, ile podaje nagłówek Retry-After."""
    for proba in range(1, MAKS_PROB + 1):
        try:
            return funkcja()
        except (Blad429, TimeoutException, StaleElementReferenceException, WebDriverException) as blad:
            statystyki["bledy"] += 1
            przegladarka.zrzut_bledu(opis)
            if proba == MAKS_PROB:
                log.error("%s: niepowodzenie po %d próbach (%s)", opis, proba, type(blad).__name__)
                raise
            czekaj = 2 ** (proba - 1)
            if isinstance(blad, Blad429):
                czekaj = max(czekaj, blad.retry_after)
            statystyki["ponowienia"] += 1
            log.warning("%s: próba %d nieudana (%s: %s) – ponawiam za %d s",
                        opis, proba, type(blad).__name__, str(blad).splitlines()[0][:120], czekaj)
            time.sleep(czekaj)

def surowy_html(url_bazowy, opoznienie):
    wynik = {}
    for nazwa, sciezka in (("katalog", "/"), ("szczegoly", "/detail.html?id=1")):
        odp = requests.get(url_bazowy + sciezka, timeout=15)
        soup = BeautifulSoup(odp.text, "html.parser")
        wynik[nazwa] = {
            "status": odp.status_code,
            "znakow": len(odp.text),
            "rekordy_data_id": len(soup.select(SELEKTOR_REKORDU)),
            "karty": len(soup.select(SELEKTOR_KARTY)),
            "wiersze_tabeli": len(soup.select(SELEKTOR_WIERSZA)),
            "naglowki_tabeli_kontrolnie": len(soup.select("table th")),
            "skrypty": [s.get("src") for s in soup.select("script[src]")],
        }
        time.sleep(opoznienie)
    return wynik


def wczytaj_wszystko(przegladarka):
    driver = przegladarka.driver
    przegladarka.otworz("/", lambda d: d.find_elements(By.CSS_SELECTOR, SELEKTOR_KARTY))
    przebieg = [{"klikniecie": 0, "elementy": len(driver.find_elements(By.CSS_SELECTOR, SELEKTOR_REKORDU)),
                 "unikalne": len(unikalne_id(driver))}]
    while True:
        przycisk = driver.find_element(By.CSS_SELECTOR, "#btn-wczytaj-wiecej")
        if not przycisk.is_enabled():
            break
        przed_elementy = przebieg[-1]["elementy"]
        przed_unikalne = przebieg[-1]["unikalne"]
        przycisk.click()
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, SELEKTOR_REKORDU)) > przed_elementy)
        stan = {"klikniecie": len(przebieg), "elementy": len(driver.find_elements(By.CSS_SELECTOR, SELEKTOR_REKORDU)),
                "unikalne": len(unikalne_id(driver))}
        przebieg.append(stan)
        log.info("Wczytaj więcej #%d: elementów w DOM %d, unikalnych %d", stan["klikniecie"], stan["elementy"], stan["unikalne"])
        # Przycisk partnera nie wyłącza się na końcu katalogu – koniec poznajemy po braku nowych id.
        if stan["unikalne"] == przed_unikalne:
            break
    return przebieg


def zbierz_liste(przegladarka):
    driver = przegladarka.driver
    rekordy = []
    strona, liczba_stron = 1, None
    while liczba_stron is None or strona <= liczba_stron:
        def wczytaj_strone():
            przegladarka.otworz(f"/?page={strona}", lambda d: (
                d.find_elements(By.CSS_SELECTOR, SELEKTOR_REKORDU)
                and f"(Strona {strona})" in d.find_element(By.ID, "licznik-produktow").text))
            elementy = driver.find_elements(By.CSS_SELECTOR, SELEKTOR_REKORDU)
            return [dict(element_na_slownik(el), strona=strona) for el in elementy]

        z_strony = ponawiaj(przegladarka, f"lista_strona_{strona}", wczytaj_strone)
        if liczba_stron is None:
            liczba_stron = len(driver.find_elements(By.CSS_SELECTOR, "#paginacja button"))
        kart = sum(r["zrodlo"] == "karta" for r in z_strony)
        log.info("Strona %d/%d: %d rekordów (karty %d, tabela %d)", strona, liczba_stron, len(z_strony), kart, len(z_strony) - kart)
        rekordy.extend(z_strony)
        strona += 1
    statystyki["strony_listy"] = liczba_stron
    return rekordy


def zbierz_szczegoly(przegladarka, identyfikatory, plik_checkpoint):
    zebrane = {}
    if plik_checkpoint.exists():
        zebrane = json.loads(plik_checkpoint.read_text(encoding="utf-8"))
        log.info("Wznowienie sesji: %d produktów już pobranych (checkpoint)", len(zebrane))
    do_pobrania = [i for i in identyfikatory if i not in zebrane]
    for n, id_ in enumerate(do_pobrania, start=1):
        def pobierz():
            przegladarka.otworz(f"/detail.html?id={id_}",
                                lambda d: d.find_elements(By.CSS_SELECTOR, "article.szczegoly-karta"))
            return szczegoly_na_slownik(przegladarka.driver)
        try:
            zebrane[id_] = ponawiaj(przegladarka, f"szczegoly_{id_}", pobierz)
        except Exception:
            statystyki["szczegoly_nieudane"] += 1
            continue
        plik_checkpoint.write_text(json.dumps(zebrane, ensure_ascii=False), encoding="utf-8")
        if n % 25 == 0 or n == len(do_pobrania):
            log.info("Szczegóły: %d/%d (łącznie zebrane %d)", n, len(do_pobrania), len(zebrane))
    return zebrane


def polacz(lista, szczegoly, dzis):
    unikalne = {}
    for rekord in lista:
        unikalne.setdefault(rekord["id"], rekord)
    wynik = []
    for id_, z_listy in unikalne.items():
        z_detalu = {k: v for k, v in szczegoly.get(id_, {}).items() if v is not None}
        wynik.append(wyczysc_rekord({**z_listy, **z_detalu}, dzis))
    return wynik
 

def konfiguruj_log(plik):
    log.setLevel(logging.INFO)
    format_ = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%H:%M:%S")
    for obsluga in (logging.FileHandler(plik, encoding="utf-8"), logging.StreamHandler()):
        obsluga.setFormatter(format_)
        log.addHandler(obsluga)


def main():
    argumenty = argparse.ArgumentParser(description="Parser serwisu TechStore (Selenium)")
    argumenty.add_argument("--url", default="http://localhost:8000", help="adres serwisu")
    argumenty.add_argument("--wyjscie", default=str(KATALOG / "wyniki"), help="folder na wyniki")
    argumenty.add_argument("--opoznienie", type=float, default=2.0,
                           help="min. odstęp między wejściami na strony w s (min. 0,5; serwis ma limit 6 żądań / 2 s)")
    argumenty.add_argument("--limit", type=int, default=None, help="pobierz szczegóły tylko N produktów (test)")
    argumenty.add_argument("--headless", action="store_true", help="przeglądarka bez okna")
    argumenty.add_argument("--od-nowa", action="store_true", help="zignoruj zapisany postęp (checkpoint)")
    arg = argumenty.parse_args()
    arg.opoznienie = max(arg.opoznienie, 0.5)

    wyjscie = Path(arg.wyjscie)
    wyjscie.mkdir(parents=True, exist_ok=True)
    konfiguruj_log(wyjscie / "parser.log")
    checkpoint = wyjscie / "checkpoint_szczegoly.json"
    if arg.od_nowa and checkpoint.exists():
        checkpoint.unlink()

    start = time.monotonic()
    log.info("Start: %s, tryb %s, opóźnienie %.1f s", arg.url, "headless" if arg.headless else "z oknem", arg.opoznienie)

    try:
        html = surowy_html(arg.url, arg.opoznienie)
    except requests.exceptions.RequestException as blad:
        log.error("Serwis %s nie odpowiada (%s). Uruchom `py server.py` w folderze Parser1.", arg.url, blad)
        return
    log.info("Surowy HTML katalogu: %d rekordów (kontrolnie nagłówków tabeli: %d)",
             html["katalog"]["rekordy_data_id"], html["katalog"]["naglowki_tabeli_kontrolnie"])

    przegladarka = Przegladarka(arg.url, arg.opoznienie, arg.headless, wyjscie / "bledy")
    try:
        doladowanie = ponawiaj(przegladarka, "wczytaj_wiecej", lambda: wczytaj_wszystko(przegladarka))
        lista = zbierz_liste(przegladarka)
        identyfikatory = list(dict.fromkeys(r["id"] for r in lista))
        if arg.limit:
            identyfikatory = identyfikatory[:arg.limit]
        szczegoly = zbierz_szczegoly(przegladarka, identyfikatory, checkpoint)
    finally:
        przegladarka.zamknij()

    dzis = date.today()
    produkty = polacz(lista, szczegoly, dzis)
    if arg.limit:
        produkty = [p for p in produkty if str(p["id"]) in szczegoly]

    (wyjscie / "surowe_lista.json").write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")
    (wyjscie / "surowe_szczegoly.json").write_text(json.dumps(szczegoly, ensure_ascii=False, indent=1), encoding="utf-8")
    tabela = pd.DataFrame(produkty)
    # liczby całkowite z brakami: typ Int64 (bez niego pandas zapisałby 12 jako 12.0)
    for kolumna in ("id", "liczba_opinii", "gwarancja_miesiace", "strona_listy"):
        tabela[kolumna] = tabela[kolumna].astype("Int64")
    tabela.to_csv(wyjscie / "produkty.csv", index=False, encoding="utf-8-sig")
    tabela.to_json(wyjscie / "produkty.json", orient="records", force_ascii=False, indent=1)
    tabela.to_excel(wyjscie / "produkty.xlsx", index=False)

    czas = time.monotonic() - start
    podsumowanie = {
        "data_parsowania": dzis.isoformat(),
        "tryb": "headless" if arg.headless else "z oknem",
        "czas_s": round(czas, 1),
        "surowy_html": html,
        "dom_wczytaj_wiecej": doladowanie,
        "lista": {
            "strony": statystyki["strony_listy"],
            "rekordy_z_duplikatami": len(lista),
            "rekordy_unikalne": len({r["id"] for r in lista}),
            "duplikaty_usuniete": len(lista) - len({r["id"] for r in lista}),
            "z_kart": sum(r["zrodlo"] == "karta" for r in lista),
            "z_tabeli": sum(r["zrodlo"] == "tabela" for r in lista),
        },
        "szczegoly_pobrane": len(szczegoly),
        "rekordy_wynikowe": len(produkty),
        "atrybuty": len(tabela.columns),
        "wejscia_na_strony": statystyki["wejscia_na_strony"],
        "bledy": statystyki["bledy"],
        "ponowienia": statystyki["ponowienia"],
        "odpowiedzi_429": statystyki["odpowiedzi_429"],
        "szczegoly_nieudane": statystyki["szczegoly_nieudane"],
    }
    (wyjscie / "podsumowanie.json").write_text(json.dumps(podsumowanie, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info("KONIEC: %d rekordów, %d atrybutów, stron listy %d, wejść na strony %d, błędów %d, ponowień %d, "
             "odpowiedzi 429: %d, czas %.0f s", len(produkty), len(tabela.columns), statystyki["strony_listy"],
             statystyki["wejscia_na_strony"], statystyki["bledy"], statystyki["ponowienia"],
             statystyki["odpowiedzi_429"], czas)


if __name__ == "__main__":
    main()
