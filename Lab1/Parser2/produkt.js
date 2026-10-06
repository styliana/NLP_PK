// Podstrona szczegółów: produkt.html?id=<id> pobiera dane/produkty.json i wyświetla rekord o danym id.
"use strict";

const status = document.querySelector("#status-wczytywania");
const kontener = document.querySelector("#kontener-produktu");

function renderujSzczegoly(p) {
  const specyfikacja = Object.entries(p.specyfikacja)
    .map(([nazwa, wartosc]) =>
      `<tr class="parametr-specyfikacji ${slug(nazwa)}"><th scope="row">${esc(nazwa)}</th><td>${esc(wartosc)}</td></tr>`)
    .join("\n");

  kontener.innerHTML = `
    <article class="produkt szczegoly-produktu" id="produkt-${p.id}" data-id="${p.id}" data-kategoria="${slug(p.kategoria)}">
      ${p.cena_poprzednia ? '<span class="etykieta-promocja">Promocja</span>' : ""}
      <header class="naglowek-szczegolow">
        <p class="kategoria">${esc(p.kategoria)}</p>
        <h1 class="nazwa">${esc(p.nazwa)}</h1>
        <p class="producent">Producent: <span class="producent-nazwa">${esc(p.producent)}</span></p>
        <div class="cena">${cenaHtml(p)}</div>
      </header>

      <div class="kolumny-szczegolow">
        <section class="sekcja-szczegolow podstawowe-informacje" aria-labelledby="tytul-podstawowe">
          <h2 id="tytul-podstawowe">Podstawowe informacje</h2>
          <dl class="parametry">${parametryPodstawowe(p)}
          </dl>
        </section>

        <section class="sekcja-szczegolow dodatkowe-informacje" aria-labelledby="tytul-dodatkowe">
          <h2 id="tytul-dodatkowe">Dodatkowe informacje</h2>
          <dl class="parametry">
            <dt>Kod EAN</dt><dd class="ean">${esc(p.ean)}</dd>
            <dt>Numer katalogowy</dt><dd class="numer-katalogowy">${esc(p.numer_katalogowy)}</dd>
            <dt>Wymiary (dł. × szer. × wys.)</dt><dd class="wymiary">${esc(p.wymiary)}</dd>
            <dt>Materiał obudowy</dt><dd class="material">${esc(p.material)}</dd>
            <dt>Kraj pochodzenia</dt><dd class="kraj-pochodzenia">${esc(p.kraj_pochodzenia)}</dd>
            <dt>Data premiery</dt><dd class="data-premiery"><time datetime="${p.data_premiery}">${formatDaty(p.data_premiery)}</time></dd>
            <dt>Sprzedawca</dt><dd class="sprzedawca">${esc(p.sprzedawca)}</dd>
            <dt>Zawartość zestawu</dt><dd class="zawartosc-zestawu">${esc(p.zawartosc_zestawu)}</dd>
          </dl>
        </section>
      </div>

      <section class="sekcja-szczegolow specyfikacja-techniczna" aria-labelledby="tytul-specyfikacja">
        <h2 id="tytul-specyfikacja">Specyfikacja techniczna</h2>
        <table class="specyfikacja">
          <tbody>
            ${specyfikacja}
          </tbody>
        </table>
      </section>

      <section class="sekcja-szczegolow dostawa" aria-labelledby="tytul-dostawa">
        <h2 id="tytul-dostawa">Dostawa</h2>
        <dl class="parametry">
          <dt>Czas dostawy</dt><dd class="czas-dostawy">${esc(p.czas_dostawy)}</dd>
          <dt>Koszt dostawy</dt><dd class="koszt-dostawy">${esc(p.koszt_dostawy)}</dd>
        </dl>
      </section>

      <section class="sekcja-szczegolow opis-produktu" aria-labelledby="tytul-opis">
        <h2 id="tytul-opis">Opis</h2>
        <p class="opis">${esc(p.opis)}</p>
      </section>

      <p><a class="przycisk" href="index.html">« Wróć do katalogu</a></p>
    </article>`;
}

async function start() {
  const id = parseInt(new URLSearchParams(location.search).get("id"), 10);
  if (!id) {
    status.textContent = "Brak identyfikatora produktu w adresie (produkt.html?id=…).";
    return;
  }
  kontener.innerHTML = '<div class="szkielet-szczegolow" aria-hidden="true"></div>';
  try {
    const { produkty } = await pobierzJson("dane/produkty.json");
    const p = produkty.find((produkt) => produkt.id === id);
    if (!p) throw new Error("brak produktu");
    document.title = `${p.nazwa} – TechStore`;
    document.querySelector("#okruszek-kategoria").textContent = p.kategoria;
    renderujSzczegoly(p);
    status.remove();
  } catch (blad) {
    kontener.innerHTML = "";
    status.textContent = blad.message === "brak produktu"
      ? `Nie znaleziono produktu o identyfikatorze ${id}.`
      : `Nie udało się wczytać produktu (${blad.message}).`;
  }
}

start();
