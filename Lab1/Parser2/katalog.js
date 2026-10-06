// Katalog TechStore: rekordy pobierane przez fetch z pliku dane/produkty.json i dodawane porcjami.
// W źródle HTML nie ma żadnych rekordów – wiersze tabeli i karty powstają tutaj.
// Porcja = podstrona katalogu: index.html?strona=N zaczyna od porcji N, „Wczytaj więcej” dokłada kolejne.
"use strict";

const DANE_URL = "dane/produkty.json";

const stan = { katalog: null, stronaStartowa: 1, nastepnaPorcja: 0, produkty: [], laduje: false };

const $ = (sel) => document.querySelector(sel);
const wiersze = $("#wiersze-produktow");
const karty = $("#lista-kart");
const przycisk = $("#wczytaj-wiecej");
const wskaznik = $("#wskaznik-ladowania");
const status = $("#status-wczytywania");
const filtry = $("#filtry");

function renderujWiersz(p) {
  const ocena = p.ocena === null
    ? '<td class="ocena brak-danych"></td>'
    : `<td class="ocena" data-ocena="${p.ocena}"><span class="gwiazdki" aria-hidden="true">${gwiazdki(p.ocena)}</span> ${String(p.ocena).replace(".", ",")}</td>`;
  const gwarancja = "gwarancja" in p
    ? `<td class="gwarancja">${esc(p.gwarancja)}</td>`
    : '<td class="gwarancja brak-danych">—</td>';
  const tr = document.createElement("tr");
  tr.className = "produkt";
  tr.dataset.id = p.id;
  tr.dataset.kategoria = slug(p.kategoria);
  tr.innerHTML = `
    <td class="kod-sku">${esc(p.sku)}</td>
    <td class="nazwa"><a class="link-produktu" href="${esc(p.link)}">${esc(p.nazwa)}</a></td>
    <td class="kategoria">${esc(p.kategoria)}</td>
    <td class="producent">${esc(p.producent)}</td>
    <td class="cena">${cenaHtml(p)}</td>
    <td class="dostepnosc ${KLASY_DOSTEPNOSCI[p.dostepnosc] || ""}" data-stan="${p.stan_magazynowy}">${esc(p.dostepnosc)}</td>
    ${ocena}
    <td class="liczba-opinii">${p.liczba_opinii}</td>
    <td class="data-dodania"><time datetime="${p.data_dodania}">${formatDaty(p.data_dodania)}</time></td>
    ${gwarancja}
    <td class="kolor">${esc(p.kolor)}</td>
    <td class="waga">${esc(p.waga)}</td>`;
  return tr;
}

function renderujKarte(p) {
  const karta = document.createElement("article");
  karta.className = "produkt karta-produktu";
  karta.dataset.id = p.id;
  karta.dataset.kategoria = slug(p.kategoria);
  karta.innerHTML = `${p.cena_poprzednia ? '<span class="etykieta-promocja">Promocja</span>' : ""}
    <header class="naglowek-karty">
      <p class="kategoria">${esc(p.kategoria)}</p>
      <h3 class="nazwa"><a class="link-produktu" href="${esc(p.link)}">${esc(p.nazwa)}</a></h3>
      <p class="producent">Producent: <span class="producent-nazwa">${esc(p.producent)}</span></p>
    </header>
    <div class="cena">${cenaHtml(p)}</div>
    <dl class="parametry">${parametryPodstawowe(p)}
    </dl>
    <details class="szczegoly-techniczne">
      <summary>Pokaż szczegóły techniczne</summary>
      <div class="zawartosc-szczegolow"></div>
    </details>
    <footer class="stopka-karty">
      <a class="link-produktu przycisk" href="${esc(p.link)}">Zobacz szczegóły</a>
    </footer>`;

  // Szczegóły techniczne trafiają do DOM dopiero przy pierwszym rozwinięciu <details>.
  const details = karta.querySelector("details");
  details.addEventListener("toggle", () => {
    const kontener = details.querySelector(".zawartosc-szczegolow");
    if (!details.open || kontener.childElementCount) return;
    kontener.innerHTML = `
      <dl class="parametry">
        <dt>Kod EAN</dt><dd class="ean">${esc(p.ean)}</dd>
        <dt>Numer katalogowy</dt><dd class="numer-katalogowy">${esc(p.numer_katalogowy)}</dd>
        <dt>Wymiary</dt><dd class="wymiary">${esc(p.wymiary)}</dd>
        <dt>Materiał</dt><dd class="material">${esc(p.material)}</dd>
      </dl>`;
  });
  return karta;
}

function wybraneProdukty() {
  const szukaj = $("#filtr-szukaj").value.trim().toLowerCase();
  const kategoria = $("#filtr-kategoria").value;
  const dostepnosc = $("#filtr-dostepnosc").value;
  const tylkoPromocje = $("#filtr-promocje").checked;
  const sortowanie = $("#sortowanie").value;

  const wynik = stan.produkty.filter(({ produkt: p }) =>
    (!szukaj || p.nazwa.toLowerCase().includes(szukaj)) &&
    (!kategoria || p.kategoria === kategoria) &&
    (!dostepnosc || p.dostepnosc === dostepnosc) &&
    (!tylkoPromocje || p.cena_poprzednia));

  const porownania = {
    "cena-rosnaco": (a, b) => cenaWPln(a.produkt.cena) - cenaWPln(b.produkt.cena),
    "cena-malejaco": (a, b) => cenaWPln(b.produkt.cena) - cenaWPln(a.produkt.cena),
    "ocena-malejaco": (a, b) => (b.produkt.ocena ?? -1) - (a.produkt.ocena ?? -1),
    "najnowsze": (a, b) => b.produkt.data_dodania.localeCompare(a.produkt.data_dodania),
    "nazwa": (a, b) => a.produkt.nazwa.localeCompare(b.produkt.nazwa, "pl"),
  };
  const porownaj = porownania[sortowanie];
  return porownaj ? wynik.sort((a, b) => porownaj(a, b) || a.kolejnosc - b.kolejnosc) : wynik;
}

// Ponowne uruchomienie animacji CSS na elemencie.
function animuj(element, klasa) {
  element.classList.remove(klasa);
  void element.offsetWidth;
  element.classList.add(klasa);
}

// Każdy rekord ma stałą strukturę (tabela albo karta) nadaną przy wczytaniu porcji.
// Nowo wczytane rekordy wjeżdżają kolejno; po zmianie filtrów cała lista płynnie się przenika.
function odswiezListe(zFiltrow = false) {
  const widoczne = wybraneProdukty();
  const fragmentWierszy = document.createDocumentFragment();
  const fragmentKart = document.createDocumentFragment();
  const licznik = { tabela: 0, karta: 0 };
  widoczne.forEach((wpis) => {
    const { produkt, struktura } = wpis;
    const element = struktura === "tabela" ? renderujWiersz(produkt) : renderujKarte(produkt);
    if (wpis.nowy) {
      element.classList.add("animacja-wejscia");
      element.style.setProperty("--opoznienie", `${Math.min(licznik[struktura]++, 24) * 35}ms`);
    }
    (struktura === "tabela" ? fragmentWierszy : fragmentKart).appendChild(element);
  });
  stan.produkty.forEach((wpis) => { wpis.nowy = false; });
  wiersze.replaceChildren(fragmentWierszy);
  karty.replaceChildren(fragmentKart);
  if (zFiltrow) {
    animuj(wiersze, "odswiezenie");
    animuj(karty, "odswiezenie");
  }
  if (!widoczne.length && stan.produkty.length) {
    karty.innerHTML = '<p class="komunikat-brak-wynikow">Brak produktów spełniających kryteria.</p>';
  }
  aktualizujStatus(widoczne.length);
}

function aktualizujStatus(widoczne) {
  const { katalog: indeks, produkty, stronaStartowa, nastepnaPorcja } = stan;
  if (!indeks) return;
  const zakres = nastepnaPorcja > stronaStartowa ? `porcje ${stronaStartowa}–${nastepnaPorcja}` : `porcja ${stronaStartowa}`;
  status.textContent = `Wyświetlono ${widoczne} z ${produkty.length} wczytanych produktów ` +
    `(${zakres} z ${indeks.liczba_porcji}, łącznie w katalogu: ${indeks.liczba_rekordow}).`;
  animuj(status, "zmiana");
}

// Migoczące szkielety kart i wierszy na czas wczytywania porcji (bez klasy „produkt”).
function pokazSzkielety(widoczne) {
  document.querySelectorAll(".szkielet-karty, .szkielet-wiersz").forEach((el) => el.remove());
  if (!widoczne) return;
  for (let i = 0; i < 4; i++) {
    const tr = document.createElement("tr");
    tr.className = "szkielet-wiersz";
    tr.setAttribute("aria-hidden", "true");
    tr.innerHTML = "<td><span></span></td>".repeat(12);
    wiersze.appendChild(tr);
    const karta = document.createElement("div");
    karta.className = "szkielet-karty";
    karta.setAttribute("aria-hidden", "true");
    karty.appendChild(karta);
  }
}

function zbudujPaginacje() {
  const liczba = stan.katalog.liczba_porcji;
  const biezaca = stan.stronaStartowa;
  const link = (n, tekst, klasa, rel = "") =>
    `<li><a class="${klasa}" ${rel ? `rel="${rel}" ` : ""}href="?strona=${n}">${tekst}</a></li>`;
  const nieaktywny = (tekst, klasa) => `<li><span class="${klasa} nieaktywna">${tekst}</span></li>`;
  const elementy = [biezaca > 1 ? link(biezaca - 1, "« Poprzednia", "poprzednia-strona", "prev") : nieaktywny("« Poprzednia", "poprzednia-strona")];
  for (let n = 1; n <= liczba; n++) {
    elementy.push(n === biezaca
      ? `<li><span class="numer-strony aktualna-strona" aria-current="page">${n}</span></li>`
      : link(n, n, "numer-strony"));
  }
  elementy.push(biezaca < liczba ? link(biezaca + 1, "Następna »", "nastepna-strona", "next") : nieaktywny("Następna »", "nastepna-strona"));
  const nav = $("#paginacja");
  nav.dataset.strona = biezaca;
  nav.dataset.liczbaStron = liczba;
  nav.innerHTML = `<ul class="lista-stron">${elementy.join("")}</ul>`;
  $("#numer-strony").textContent = biezaca;
  $("#liczba-stron").textContent = liczba;
}

async function wczytajPorcje() {
  if (stan.laduje || stan.nastepnaPorcja >= stan.katalog.liczba_porcji) return;
  stan.laduje = true;
  przycisk.disabled = true;
  przycisk.classList.add("laduje");
  wskaznik.hidden = false;
  pokazSzkielety(true);
  try {
    await opoznienie();
    const { produkty, rozmiar_porcji: rozmiar } = stan.katalog;
    const porcja = produkty.slice(stan.nastepnaPorcja * rozmiar, (stan.nastepnaPorcja + 1) * rozmiar);
    const polowa = Math.ceil(porcja.length / 2);
    porcja.forEach((produkt, i) => stan.produkty.push({
      produkt,
      struktura: i < polowa ? "tabela" : "karta",
      kolejnosc: stan.produkty.length,
      nowy: true,
    }));
    stan.nastepnaPorcja += 1;
    odswiezListe();
  } catch (blad) {
    status.textContent = `Nie udało się wczytać produktów (${blad.message}). Spróbuj ponownie.`;
  } finally {
    stan.laduje = false;
    pokazSzkielety(false);
    przycisk.classList.remove("laduje");
    wskaznik.hidden = true;
    const koniec = stan.nastepnaPorcja >= stan.katalog.liczba_porcji;
    przycisk.disabled = koniec;
    przycisk.hidden = koniec;
    if (koniec && !$(".koniec-katalogu")) {
      wskaznik.insertAdjacentHTML("afterend", '<p class="koniec-katalogu">To już ostatnia strona katalogu.</p>');
    }
  }
}

async function start() {
  try {
    const odp = await fetch(DANE_URL);
    if (!odp.ok) throw new Error(`HTTP ${odp.status}`);
    stan.katalog = await odp.json();
  } catch (blad) {
    status.textContent = "Nie udało się pobrać danych katalogu. Uruchom stronę przez serwer HTTP (np. py -m http.server).";
    return;
  }
  const zadana = parseInt(new URLSearchParams(location.search).get("strona"), 10);
  stan.stronaStartowa = Math.min(Math.max(zadana || 1, 1), stan.katalog.liczba_porcji);
  stan.nastepnaPorcja = stan.stronaStartowa - 1;
  zbudujPaginacje();

  przycisk.addEventListener("click", wczytajPorcje);
  filtry.addEventListener("input", () => odswiezListe(true));
  filtry.addEventListener("submit", (e) => e.preventDefault());
  await wczytajPorcje();
}

start();
