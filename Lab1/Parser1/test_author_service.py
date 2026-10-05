"""
Skrypt weryfikacyjny dla Zadania AUTOR (Poziom 5.0)
Sprawdza:
1. Brak rekordów produktów w surowym kodzie HTML (Ctrl+U)
2. Strukturę pliku JSON i liczbę rekordów (min. 400, tutaj 430)
3. Liczbę atrybutów per rekord (min. 22, tutaj 24)
4. Występowanie duplikatów (min. 8)
5. Występowanie braków danych w 2 polach (min. 15%)
6. Działanie serwera HTTP, endpointów API oraz Rate Limitingu (kod 429 + Retry-After)
"""

import sys
import os
import json
import time
import socketserver
import threading
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "products.json")
INDEX_HTML = os.path.join(BASE_DIR, "static", "index.html")
DETAIL_HTML = os.path.join(BASE_DIR, "static", "detail.html")

def test_static_html():
    print("[TEST 1] Weryfikacja surowego kodu HTML (brak produktów w źródle)...", flush=True)
    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        content = f.read()

    assert "ThinkPad" not in content, "BŁĄD: Nazwa produktu znaleziona w statycznym HTML!"
    assert "Galaxy S24" not in content, "BŁĄD: Nazwa produktu znaleziona w statycznym HTML!"
    assert "siatka-kart" in content, "Brak kontenera siatka-kart w HTML"
    assert "tabela-produktow" in content, "Brak kontenera tabela-produktow w HTML"
    print("  -> OK: W surowym kodzie HTML nie ma żadnych rekordów produktów (zgodność z 5.0).", flush=True)

def test_json_structure():
    print("\n[TEST 2] Weryfikacja bazy danych JSON (data/products.json)...", flush=True)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    total_records = len(products)
    print(f"  -> Liczba rekordów: {total_records} (Wymóg: min. 400)", flush=True)
    assert total_records >= 400, f"Zbyt mało rekordów: {total_records} < 400"

    sample = products[0]
    num_attributes = len(sample)
    print(f"  -> Liczba atrybutów rekordu: {num_attributes} (Wymóg: min. 22)", flush=True)
    assert num_attributes >= 22, f"Zbyt mało atrybutów: {num_attributes} < 22"

    ids = [p["id"] for p in products]
    duplicate_count = total_records - len(set(ids))
    print(f"  -> Liczba zduplikowanych rekordów: {duplicate_count} (Wymóg: min. 8)", flush=True)
    assert duplicate_count >= 8, f"Zbyt mało duplikatów: {duplicate_count} < 8"

    missing_rating = sum(1 for p in products if not p.get("ocena"))
    missing_warranty = sum(1 for p in products if not p.get("gwarancja"))
    pct_rating = (missing_rating / total_records) * 100
    pct_warranty = (missing_warranty / total_records) * 100

    print(f"  -> Braki w polu 'ocena': {missing_rating} ({pct_rating:.1f}%) [Wymóg: min. 15%]", flush=True)
    print(f"  -> Braki w polu 'gwarancja': {missing_warranty} ({pct_warranty:.1f}%) [Wymóg: min. 15%]", flush=True)
    assert pct_rating >= 15.0, f"Braki w 'ocena' poniżej 15%: {pct_rating}%"
    assert pct_warranty >= 15.0, f"Braki w 'gwarancja' poniżej 15%: {pct_warranty}%"

    currencies = set(p["waluta"] for p in products)
    print(f"  -> Zastosowane waluty: {currencies}", flush=True)
    assert len(currencies) >= 2, "Brak zróżnicowania walut"

    print("  -> OK: Baza danych spełnia wszystkie wymagania.", flush=True)

def test_server_and_rate_limiting():
    print("\n[TEST 3] Weryfikacja serwera HTTP i Rate Limitingu (HTTP 429)...", flush=True)
    from server import AuthorServerHandler
    test_port = 8899

    # Uruchom serwer w wątku demona
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", test_port), AuthorServerHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.3)

    base_url = f"http://127.0.0.1:{test_port}"

    try:
        # Test pobrania index.html
        req = urllib.request.urlopen(f"{base_url}/")
        assert req.status == 200
        print("  -> Endpoint / (index.html): OK (HTTP 200)", flush=True)

        # Test pobrania pojedynczego produktu
        req_prod = urllib.request.urlopen(f"{base_url}/api/product?id=1")
        assert req_prod.status == 200
        prod_data = json.loads(req_prod.read().decode("utf-8"))
        assert prod_data["id"] == 1
        print(f"  -> Endpoint /api/product?id=1: OK (zwrócono produkt: {prod_data['nazwa']})", flush=True)

        # Test pobrania listy produktów z paginacją
        req_list = urllib.request.urlopen(f"{base_url}/api/products?page=1&limit=10")
        assert req_list.status == 200
        list_data = json.loads(req_list.read().decode("utf-8"))
        assert len(list_data["products"]) == 10
        print(f"  -> Endpoint /api/products: OK (strona 1, 10 pozycji, łącznie stron: {list_data['total_pages']})", flush=True)

        # Test Rate Limitera: równoległe zapytania
        print("  -> Testowanie Rate Limitera (wysyłanie równoległych żądań)...", flush=True)

        def make_request(i):
            try:
                urllib.request.urlopen(f"{base_url}/api/stats")
                return 200, None
            except urllib.error.HTTPError as e:
                return e.code, e.headers.get("Retry-After")
            except Exception as e:
                return 500, None

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(make_request, range(10)))

        codes = [r[0] for r in results]
        retry_afters = [r[1] for r in results if r[1] is not None]

        print(f"  -> Kody odpowiedzi: {codes}", flush=True)
        print(f"  -> Nagłówki Retry-After: {retry_afters}", flush=True)

        hit_429 = 429 in codes
        assert hit_429, "BŁĄD: Serwer nie zwrócił kodu HTTP 429 przy intensywnym ruchu równoległym!"
        assert len(retry_afters) > 0, "BŁĄD: Brak nagłówka Retry-After w odpowiedzi 429!"
        print("  -> OK: Rate Limiter zwrócił HTTP 429 i nagłówek Retry-After.", flush=True)

    finally:
        httpd.shutdown()
        httpd.server_close()
        print("  -> Testowy serwer HTTP pomyślnie zatrzymany.", flush=True)

if __name__ == "__main__":
    test_static_html()
    test_json_structure()
    test_server_and_rate_limiting()
    print("\n==============================================")
    print(" WSZYSTKIE TESTY DLA AUTOR (POZIOM 5.0) ZDANE! ")
    print("==============================================")
