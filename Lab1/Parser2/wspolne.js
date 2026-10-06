// Funkcje wspólne dla katalogu (index.html) i podstrony szczegółów (produkt.html).
"use strict";

const OPOZNIENIE_MIN = 300;   // ms
const OPOZNIENIE_MAX = 2000;  // ms
const KURSY = { PLN: 1, EUR: 4.3, USD: 4.0 };  // tylko do sortowania po cenie
const KLASY_DOSTEPNOSCI = {
  "Dostępny": "dostepny",
  "Ostatnie sztuki": "ostatnie-sztuki",
  "Na zamówienie": "na-zamowienie",
  "Niedostępny": "niedostepny",
};

function esc(text) {
  return String(text)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function slug(text) {
  const pl = { ą: "a", ć: "c", ę: "e", ł: "l", ń: "n", ó: "o", ś: "s", ź: "z", ż: "z" };
  return text.toLowerCase().replace(/[ąćęłńóśźż]/g, (c) => pl[c]).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

// Sztuczne opóźnienie 300–2000 ms przed pobraniem danych.
function opoznienie() {
  const ms = OPOZNIENIE_MIN + Math.floor(Math.random() * (OPOZNIENIE_MAX - OPOZNIENIE_MIN + 1));
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function pobierzJson(url) {
  await opoznienie();
  const odp = await fetch(url);
  if (!odp.ok) throw new Error(`HTTP ${odp.status}`);
  return odp.json();
}

function walutaCeny(tekst) {
  if (tekst.startsWith("$")) return "USD";
  return tekst.endsWith("€") ? "EUR" : "PLN";
}

// "1 299,99 zł" / "302,99 €" / "$1,249.99" -> wartość w PLN (do sortowania)
function cenaWPln(tekst) {
  if (tekst.startsWith("$")) {
    return parseFloat(tekst.slice(1).replace(/,/g, "")) * KURSY.USD;
  }
  const liczba = parseFloat(tekst.replace(/[^\d,]/g, "").replace(",", "."));
  return liczba * KURSY[walutaCeny(tekst)];
}

function formatDaty(iso) {
  const [r, m, d] = iso.split("-");
  return `${d}.${m}.${r}`;
}

function gwiazdki(ocena) {
  const pelne = Math.round(ocena);
  return "★".repeat(pelne) + "☆".repeat(5 - pelne);
}

function cenaHtml(p) {
  const stara = p.cena_poprzednia ? ` <s class="cena-poprzednia">${esc(p.cena_poprzednia)}</s>` : "";
  return `<span class="cena-aktualna" data-waluta="${walutaCeny(p.cena)}">${esc(p.cena)}</span>${stara}`;
}

// Lista <dt>/<dd> z podstawowymi atrybutami – używana w kartach i na podstronie szczegółów.
function parametryPodstawowe(p) {
  const ocena = p.ocena === null
    ? '<dd class="ocena brak-danych">brak ocen</dd>'
    : `<dd class="ocena" data-ocena="${p.ocena}"><span class="gwiazdki" aria-hidden="true">${gwiazdki(p.ocena)}</span> ${String(p.ocena).replace(".", ",")} / 5</dd>`;
  const gwarancja = "gwarancja" in p
    ? `<dd class="gwarancja">${esc(p.gwarancja)}</dd>`
    : '<dd class="gwarancja brak-danych">brak informacji</dd>';
  return `
      <dt>Dostępność</dt><dd class="dostepnosc ${KLASY_DOSTEPNOSCI[p.dostepnosc] || ""}" data-stan="${p.stan_magazynowy}">${esc(p.dostepnosc)}</dd>
      <dt>Ocena</dt>${ocena}
      <dt>Opinie</dt><dd class="liczba-opinii">${p.liczba_opinii}</dd>
      <dt>Dodano</dt><dd class="data-dodania"><time datetime="${p.data_dodania}">${formatDaty(p.data_dodania)}</time></dd>
      <dt>Gwarancja</dt>${gwarancja}
      <dt>Kolor</dt><dd class="kolor">${esc(p.kolor)}</dd>
      <dt>Waga</dt><dd class="waga">${esc(p.waga)}</dd>
      <dt>SKU</dt><dd class="kod-sku">${esc(p.sku)}</dd>`;
}
