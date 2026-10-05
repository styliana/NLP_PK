"""
Serwer HTTP dla Zadania AUTOR (Poziom 5.0)
Funkcjonalności:
- Obsługa plików statycznych (HTML, CSS, JS)
- Endpointy danych (/data/products.json, /api/products, /api/product)
- Sztuczne opóźnienie (300-1000 ms) symulujące opóźnienie sieciowe przy doładowywaniu
- Rate limiter: zwraca kod HTTP 429 Too Many Requests z nagłówkiem Retry-After przy > 6 req / 2s
"""

import http.server
import socketserver
import os
import json
import time
import random
import urllib.parse
import threading
from collections import defaultdict

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.join(BASE_DIR, "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")

# Pamięć podręczna na produkty
ALL_PRODUCTS = []
if os.path.exists(PRODUCTS_FILE):
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        ALL_PRODUCTS = json.load(f)

# Rate limiter z blokadą wielowątkową
REQUEST_HISTORY = defaultdict(list)
RATE_LIMIT_LOCK = threading.Lock()
RATE_LIMIT_MAX_REQUESTS = 6
RATE_LIMIT_WINDOW_SECONDS = 2.0
RETRY_AFTER_SECONDS = 2

class AuthorServerHandler(http.server.BaseHTTPRequestHandler):
    def is_rate_limited(self, client_ip):
        now = time.time()
        with RATE_LIMIT_LOCK:
            # Wyczyść historię starszą niż okno czasowe
            REQUEST_HISTORY[client_ip] = [
                t for t in REQUEST_HISTORY[client_ip]
                if now - t < RATE_LIMIT_WINDOW_SECONDS
            ]
            if len(REQUEST_HISTORY[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
                return True
            REQUEST_HISTORY[client_ip].append(now)
            return False

    def send_rate_limit_response(self):
        body = json.dumps({
            "status": 429,
            "error": "Too Many Requests",
            "message": "Przekroczono limit żądań! Serwer nakłada ograniczenie prędkości.",
            "retry_after": RETRY_AFTER_SECONDS
        }, ensure_ascii=False).encode("utf-8")

        self.send_response(429)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Retry-After", str(RETRY_AFTER_SECONDS))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        client_ip = self.client_address[0]
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # Sprawdzenie limitu żądań (Rate Limiting)
        if self.is_rate_limited(client_ip):
            print(f"[429 BLOCKED] Zablokowano zapytanie z {client_ip} do {path} (Rate limit exceeded)", flush=True)
            self.send_rate_limit_response()
            return

        # Obsługa sztucznego opóźnienia (300 - 900 ms) dla API i pobierania danych JSON
        if path.startswith("/api/") or path.startswith("/data/"):
            delay = random.uniform(0.35, 0.85)
            time.sleep(delay)

        # Routing endpointów
        if path == "/" or path == "/index.html":
            self.serve_file(os.path.join(STATIC_DIR, "index.html"), "text/html; charset=utf-8")
        elif path == "/detail.html":
            self.serve_file(os.path.join(STATIC_DIR, "detail.html"), "text/html; charset=utf-8")
        elif path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            file_path = os.path.abspath(os.path.join(STATIC_DIR, rel_path))
            if file_path.startswith(STATIC_DIR) and os.path.exists(file_path):
                content_type = self.guess_content_type(file_path)
                self.serve_file(file_path, content_type)
            else:
                self.send_error(404, "Plik statyczny nie znaleziony")
        elif path == "/data/products.json":
            self.serve_file(PRODUCTS_FILE, "application/json; charset=utf-8")
        elif path == "/api/products":
            self.handle_api_products(query)
        elif path == "/api/product":
            self.handle_api_single_product(query)
        elif path == "/api/stats":
            self.handle_api_stats()
        else:
            # Bezpośrednie serwowanie z katalogu static (np. /styles.css, /app.js, /detail.js)
            direct_file = os.path.join(STATIC_DIR, path.lstrip("/"))
            if os.path.exists(direct_file) and not os.path.isdir(direct_file):
                self.serve_file(direct_file, self.guess_content_type(direct_file))
            else:
                self.send_error(404, f"Nie znaleziono ścieżki: {path}")

    def handle_api_products(self, query):
        page = int(query.get("page", [1])[0])
        limit = int(query.get("limit", [50])[0])
        category = query.get("category", [None])[0]
        sort_by = query.get("sort", [None])[0]

        data = list(ALL_PRODUCTS)

        if category and category != "all":
            data = [p for p in data if p["kategoria"] == category]

        if sort_by == "price_asc":
            data.sort(key=lambda x: x["cena_raw"])
        elif sort_by == "price_desc":
            data.sort(key=lambda x: x["cena_raw"], reverse=True)
        elif sort_by == "name_asc":
            data.sort(key=lambda x: x["nazwa"])

        total_items = len(data)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_items = data[start_idx:end_idx]

        response = {
            "total": total_items,
            "page": page,
            "limit": limit,
            "total_pages": (total_items + limit - 1) // limit,
            "has_more": end_idx < total_items,
            "products": paginated_items
        }

        body = json.dumps(response, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def handle_api_single_product(self, query):
        prod_id = query.get("id", [None])[0]
        if not prod_id:
            self.send_error(400, "Brak parametru id")
            return

        try:
            prod_id_int = int(prod_id)
        except ValueError:
            self.send_error(400, "Nieprawidłowy parametr id")
            return

        product = next((p for p in ALL_PRODUCTS if p["id"] == prod_id_int), None)
        if not product:
            self.send_error(404, "Produkt o podanym ID nie został znaleziony")
            return

        body = json.dumps(product, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def handle_api_stats(self):
        stats = {
            "total_records": len(ALL_PRODUCTS),
            "unique_ids": len(set(p["id"] for p in ALL_PRODUCTS)),
            "attributes_count": len(ALL_PRODUCTS[0]) if ALL_PRODUCTS else 0,
            "categories": sorted(list(set(p["kategoria"] for p in ALL_PRODUCTS))),
            "currencies": sorted(list(set(p["waluta"] for p in ALL_PRODUCTS)))
        }
        body = json.dumps(stats, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def serve_file(self, filepath, content_type):
        if not os.path.exists(filepath):
            self.send_error(404, "Plik nie istnieje")
            return

        with open(filepath, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def guess_content_type(self, filepath):
        if filepath.endswith(".html"):
            return "text/html; charset=utf-8"
        elif filepath.endswith(".css"):
            return "text/css; charset=utf-8"
        elif filepath.endswith(".js"):
            return "application/javascript; charset=utf-8"
        elif filepath.endswith(".json"):
            return "application/json; charset=utf-8"
        elif filepath.endswith(".png"):
            return "image/png"
        elif filepath.endswith(".jpg") or filepath.endswith(".jpeg"):
            return "image/jpeg"
        elif filepath.endswith(".svg"):
            return "image/svg+xml"
        return "text/plain; charset=utf-8"

    def log_message(self, format, *args):
        # Format logowania
        print(f"[{self.log_date_time_string()}] {format % args}", flush=True)

def run_server(port=PORT):
    global ALL_PRODUCTS
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            ALL_PRODUCTS = json.load(f)
    print(f"Załadowano {len(ALL_PRODUCTS)} produktów z bazy danych.", flush=True)

    server_address = ("", port)
    httpd = socketserver.TCPServer(server_address, AuthorServerHandler, bind_and_activate=True)
    print(f"=== Serwer serwisu e-commerce uruchomiony na porcie {port} ===", flush=True)
    print(f"-> Główny katalog: http://localhost:{port}/", flush=True)
    print(f"-> Endpoint API:  http://localhost:{port}/api/products", flush=True)
    print(f"-> Plik JSON:     http://localhost:{port}/data/products.json", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nZatrzymywanie serwera...", flush=True)
        httpd.server_close()

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(port)
