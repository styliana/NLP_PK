#!/usr/bin/env python3
"""
Skrypt konfiguracji kolekcji/rdzenia Apache Solr 10 dla Laboratorium 3.
- Tworzy rdzeń 'nlp_lab3' (jeśli nie istnieje)
- Wyłącza tryb schemaless (update.autoCreateFields=false)
- Konfiguruje jawny schemat pól za pomocą Schema API
"""

import sys
import time
import requests

SOLR_BASE_URL = "http://localhost:8983/solr"
CORE_NAME = "nlp_lab3"


def wait_for_solr(max_retries=30, delay=2):
    url = f"{SOLR_BASE_URL}/admin/info/system"
    print(f"Oczekiwanie na dostępność Solr 10 pod {SOLR_BASE_URL}...")
    for i in range(max_retries):
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                print("Solr 10 jest gotowy!")
                return True
        except Exception:
            pass
        time.sleep(delay)
    print("BŁĄD: Nie można połączyć się z Solr 10.")
    return False


def ensure_core_exists():
    cores_url = f"{SOLR_BASE_URL}/admin/cores?action=STATUS"
    resp = requests.get(cores_url).json()
    status = resp.get("status", {})
    if CORE_NAME in status:
        print(f"Rdzeń '{CORE_NAME}' już istnieje.")
        return True

    print(f"Tworzenie rdzenia '{CORE_NAME}'...")
    create_url = f"{SOLR_BASE_URL}/admin/cores?action=CREATE&name={CORE_NAME}&instanceDir={CORE_NAME}"
    r = requests.get(create_url)
    if r.status_code in [200, 201]:
        print(f"Rdzeń '{CORE_NAME}' utworzony pomyślnie.")
        return True
    else:
        print(f"Ostrzeżenie przy tworzeniu rdzenia: {r.text}")
        return False


def disable_schemaless():
    print("Wyłączanie trybu schemaless (update.autoCreateFields=false)...")
    config_url = f"{SOLR_BASE_URL}/{CORE_NAME}/config"
    payload = {
        "set-user-property": {
            "update.autoCreateFields": "false"
        }
    }
    r = requests.post(config_url, json=payload)
    if r.status_code == 200:
        print("Tryb schemaless został wyłączony.")
    else:
        print(f"Odpowiedź config: {r.text}")


def setup_schema():
    print("Definiowanie schematu pól przez Schema API...")
    schema_url = f"{SOLR_BASE_URL}/{CORE_NAME}/schema"

    # Pobierz istniejące pola
    existing_fields = set()
    try:
        r = requests.get(f"{schema_url}/fields")
        if r.status_code == 200:
            existing_fields = {f["name"] for f in r.json().get("fields", [])}
    except Exception as e:
        print(f"Uwaga przy pobieraniu pól: {e}")

    fields_to_add = [
        {"name": "orig_id", "type": "plong", "indexed": True, "stored": True, "docValues": True},
        {"name": "title", "type": "text_en", "indexed": True, "stored": True},
        {"name": "content", "type": "text_en", "indexed": True, "stored": True},
        {"name": "category", "type": "string", "indexed": True, "stored": True, "docValues": True},
        {"name": "tag", "type": "string", "indexed": True, "stored": True, "docValues": True},
        {"name": "rating", "type": "pfloat", "indexed": True, "stored": True, "docValues": True},
        {"name": "published_year", "type": "pint", "indexed": True, "stored": True, "docValues": True},
        {"name": "copy_no", "type": "pint", "indexed": True, "stored": True, "docValues": True}
    ]

    for field in fields_to_add:
        action = "replace-field" if field["name"] in existing_fields else "add-field"
        payload = {action: field}
        resp = requests.post(schema_url, json=payload)
        if resp.status_code == 200:
            print(f"Pole '{field['name']}': {action} OK.")
        else:
            print(f"Pole '{field['name']}' ({action}): {resp.text}")

    print("Schemat Solr został pomyślnie zsynchronizowany!")


def main():
    if not wait_for_solr(max_retries=10, delay=1):
        sys.exit(1)
    ensure_core_exists()
    disable_schemaless()
    setup_schema()


if __name__ == "__main__":
    main()
