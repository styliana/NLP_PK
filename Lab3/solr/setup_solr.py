#!/usr/bin/env python3
"""
Konfiguracja rdzeni Apache Solr 10 dla Laboratorium nr 3.

Rdzenie nlp_lab3 (100%), nlp_lab3_p50 i nlp_lab3_p10 tworzy kontener (precreate-core w docker-compose.yml),
każdy z własną kopią configsetu _default. Skrypt dla każdego rdzenia:
- wyłącza tryb schemaless (update.autoCreateFields=false),
- dodaje / podmienia typy pól, pola i copyField z solr/schema_api.json przez Schema API,
- zapisuje końcowy schemat rdzenia nlp_lab3 do solr/managed-schema.json (do sprawozdania).
"""

import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from common import DATASETS, SOLR_URL  # noqa: E402

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema_api.json")
SCHEMA_DUMP = os.path.join(os.path.dirname(__file__), "managed-schema.json")


def wait_for_solr(retries=60):
    """Czeka, aż Solr i wszystkie rdzenie odpowiadają na ping (rdzenie ładują się po starcie)."""
    for _ in range(retries):
        try:
            if all(requests.get(f"{SOLR_URL}/{ds['core']}/admin/ping", timeout=3).status_code == 200
                   for ds in DATASETS):
                return True
        except requests.RequestException:
            pass
        time.sleep(2)
    return False


def post(url, payload):
    r = requests.post(url, json=payload, timeout=60)
    body = r.json()
    if r.status_code != 200 or body.get("error"):
        raise RuntimeError(f"{url}: {json.dumps(body.get('error', body), ensure_ascii=False)[:500]}")
    return body


def configure_core(core, schema):
    base = f"{SOLR_URL}/{core}"
    status = requests.get(f"{SOLR_URL}/admin/cores", params={"action": "STATUS", "core": core}).json()
    if not status.get("status", {}).get(core):
        raise RuntimeError(f"Brak rdzenia '{core}' - uruchom kontener z docker-compose.yml z tego katalogu.")

    post(f"{base}/config", {"set-user-property": {"update.autoCreateFields": "false"}})

    current = requests.get(f"{base}/schema").json()["schema"]
    types = {t["name"] for t in current.get("fieldTypes", [])}
    fields = {f["name"] for f in current.get("fields", [])}
    copies = {(c["source"], c["dest"]) for c in current.get("copyFields", [])}

    commands = []
    for ft in schema["field_types"]:
        commands.append({("replace-field-type" if ft["name"] in types else "add-field-type"): ft})
    for f in schema["fields"]:
        commands.append({("replace-field" if f["name"] in fields else "add-field"): f})
    for c in schema["copy_fields"]:
        if (c["source"], c["dest"]) not in copies:
            commands.append({"add-copy-field": c})

    for cmd in commands:
        post(f"{base}/schema", cmd)
    print(f"  {core}: schemaless wyłączony, {len(commands)} zmian schematu")


def main():
    if not wait_for_solr():
        sys.exit(f"Solr nie odpowiada pod {SOLR_URL} - uruchom: docker compose up -d")
    with open(SCHEMA_FILE, encoding="utf-8") as f:
        schema = json.load(f)

    print("Konfiguracja rdzeni Solr:")
    for ds in DATASETS:
        configure_core(ds["core"], schema)

    full_core = DATASETS[-1]["core"]
    dump = requests.get(f"{SOLR_URL}/{full_core}/schema").json()["schema"]
    with open(SCHEMA_DUMP, "w", encoding="utf-8") as f:
        json.dump(dump, f, indent=2, ensure_ascii=False)
    print(f"Zapisano schemat rdzenia {full_core} do {SCHEMA_DUMP}")


if __name__ == "__main__":
    main()
