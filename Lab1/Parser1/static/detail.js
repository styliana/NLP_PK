/**
 * TechStore - Dynamiczny skrypt podstrony szczegółów (Poziom 5.0 - Pink Edition)
 * Wymagania:
 * - Wstrzykiwanie danych przez fetch()
 * - Minimum 22 atrybuty łącznie (tutaj 24 atrybuty)
 * - Minimum jeden atrybut widoczny dopiero po interakcji (rozwinięcie details lub kliknięcie zakładki)
 */

document.addEventListener("DOMContentLoaded", async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const productId = parseInt(urlParams.get("id")) || 1;

  const ladowanieBox = document.getElementById("ladowanie-box");
  const kontenerSzczegoly = document.getElementById("kontener-szczegoly");

  try {
    let product = null;
    try {
      const apiResp = await fetch(`/api/product?id=${productId}`);
      if (apiResp.ok) {
        product = await apiResp.json();
      }
    } catch (e) {
      // Fallback
    }

    if (!product) {
      const resp = await fetch("/data/products.json");
      if (!resp.ok) throw new Error("Nie można pobrać bazy produktów");
      const all = await resp.json();
      product = all.find(p => p.id === productId);
    }

    if (!product) {
      kontenerSzczegoly.innerHTML = `<div class="badge" style="background: #ffe4e6; color: #be123c; font-size: 1.1rem; padding: 1rem 1.5rem; display: block; text-align: center;">Nie znaleziono produktu o ID ${productId}!</div>`;
      kontenerSzczegoly.style.display = "block";
      return;
    }

    renderujSzczegoly(product);
  } catch (err) {
    console.error("Błąd podczas ładowania szczegółów:", err);
    kontenerSzczegoly.innerHTML = `<div class="badge" style="background: #ffe4e6; color: #be123c; font-size: 1.1rem; padding: 1rem 1.5rem; display: block; text-align: center;">Wystąpił błąd podczas ładowania danych: ${err.message}</div>`;
    kontenerSzczegoly.style.display = "block";
  } finally {
    ladowanieBox.classList.remove("aktywny");
    kontenerSzczegoly.style.display = "block";
  }

  function renderujSzczegoly(p) {
    kontenerSzczegoly.innerHTML = `
      <article class="szczegoly-karta" data-id="${p.id}" data-sku="${p.kod_produktu}" data-ean="${p.ean}">
        <header>
          <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
            <div>
              <span class="badge" style="background: #fdf2f8; color: #db2777; font-weight: 700; padding: 0.35rem 0.8rem; border-radius: 9999px; border: 1px solid #fbcfe8;">🌸 ${p.kategoria}</span>
              <h1 class="nazwa-produktu" style="margin-top: 0.6rem; font-size: 2rem; color: #3b072e; font-weight: 800;">${p.nazwa}</h1>
              <p style="color: #86557e; font-size: 0.95rem; margin-top: 0.25rem;">Producent: <strong class="producent" style="color: #be185d;">${p.producent}</strong> &bull; Kod SKU: <span class="kod-produktu">${p.kod_produktu}</span> &bull; EAN: <span class="ean">${p.ean}</span></p>
            </div>
            <div style="text-align: right;">
              <div class="cena cena-wyrozniona" style="font-size: 2.2rem; color: #be185d; font-weight: 800; letter-spacing: -0.5px;">${p.cena}</div>
              <span class="dostepnosc badge" style="background: #fce7f3; color: #9d174d; font-weight: 700; padding: 0.4rem 1rem; border-radius: 9999px; border: 1px solid #fbcfe8;">✨ ${p.dostepnosc}</span>
            </div>
          </div>
        </header>

        <section style="margin: 2rem 0;">
          <h2 style="font-size: 1.3rem; margin-bottom: 0.75rem; color: #be185d; font-weight: 800;">Opis produktu</h2>
          <div class="opis-tresc" style="line-height: 1.8; color: #4a154b; background: #fff8fa; padding: 1.25rem; border-radius: 12px; border: 1px solid #fce7f3;">
            ${p.opis}
          </div>
        </section>

        <!-- Zestawienie 24 atrybutów podzielonych na sekcje -->
        <div class="szczegoly-siatka">
          
          <div class="grupa-parametrow">
            <h3>Podstawowe informacje</h3>
            <ul style="list-style: none; display: flex; flex-direction: column; gap: 0.6rem;">
              <li><strong>ID:</strong> <span class="id">${p.id}</span></li>
              <li><strong>Stan:</strong> <span class="stan">${p.stan}</span></li>
              <li><strong>Ocena klientów:</strong> <span class="ocena">${p.ocena ? p.ocena + ' / 5.0 ⭐' : 'Brak ocen'}</span></li>
              <li><strong>Liczba opinii:</strong> <span class="liczba-opinii">${p.liczba_opinii}</span></li>
              <li><strong>Gwarancja:</strong> <span class="gwarancja">${p.gwarancja || 'Brak danych'}</span></li>
              <li><strong>Darmowa dostawa:</strong> <span class="darmowa-dostawa">${p.darmowa_dostawa}</span></li>
              <li><strong>Data dodania:</strong> <span class="data-dodania">${p.data_dodania}</span></li>
            </ul>
          </div>

          <div class="grupa-parametrow">
            <h3>Wymiary i Cechy Fizyczne</h3>
            <ul style="list-style: none; display: flex; flex-direction: column; gap: 0.6rem;">
              <li><strong>Kolor:</strong> <span class="kolor">${p.kolor}</span></li>
              <li><strong>Waga:</strong> <span class="waga">${p.waga}</span></li>
              <li><strong>Wymiary:</strong> <span class="wymiary">${p.wymiary}</span></li>
              <li><strong>Materiał obudowy:</strong> <span class="material">${p.material}</span></li>
              <li><strong>Kraj pochodzenia:</strong> <span class="kraj-pochodzenia">${p.kraj_pochodzenia}</span></li>
            </ul>
          </div>

          <div class="grupa-parametrow">
            <h3>Zasilanie i Certyfikaty</h3>
            <ul style="list-style: none; display: flex; flex-direction: column; gap: 0.6rem;">
              <li><strong>Zasilanie:</strong> <span class="zasilanie">${p.zasilanie}</span></li>
              <li><strong>Certyfikaty zgodności:</strong> <span class="certyfikaty">${p.certyfikaty}</span></li>
              <li><strong>Zawartość zestawu:</strong> <span class="zawartosc-zestawu">${p.zawartosc_zestawu}</span></li>
            </ul>
          </div>

        </div>

        <!-- UTRUDNIENIE POZIOMU 5.0:
             Minimum jeden atrybut widoczny dopiero po interakcji:
             1. Element <details> do rozwinięcia
             2. System zakładek (tabów) z leniwym wstrzyknięciem danych
        -->
        <details class="specyfikacja-interaktywna" id="sekcja-ukryta-details">
          <summary class="rozwin-naglowek" id="btn-rozwin-details">
            &#9654; Pokaż zaawansowaną specyfikację inżynieryjną (Wymaga kliknięcia)
          </summary>
          <div class="ukryta-zawartosc" id="zawartosc-details">
            <p><strong>Zastrzeżona specyfikacja laboratoryjna:</strong></p>
            <div class="specyfikacja-ukryta-tekst wartosc-specyfikacja-ukryta" style="font-family: monospace; background: white; padding: 1rem; border-radius: 8px; margin-top: 0.6rem; border: 1.5px solid #fbcfe8; color: #831843;">
              ${p.specyfikacja_ukryta}
            </div>
          </div>
        </details>

        <!-- Dodatkowo: Interaktywne zakładki (Tab Navigation) -->
        <div class="zakladki-kontener">
          <div class="zakladki-przyciski">
            <button class="tab-btn aktywny" data-target="tab-gwarancja">Warunki wsparcia</button>
            <button class="tab-btn" id="tab-btn-interaktywny" data-target="tab-laboratorium">Diagnostyka laboratoryjna (Interakcja ✨)</button>
          </div>

          <div id="tab-gwarancja" class="tab-panel aktywny">
            <p>Produkt objęty oficjalnym programem wsparcia producenta ${p.producent}. Okres ochrony: ${p.gwarancja || 'Zgodnie z rękojmią'}.</p>
          </div>

          <div id="tab-laboratorium" class="tab-panel">
            <p><strong>Parametry z testów laboratoryjnych:</strong></p>
            <div class="parametr-laboratoryjny-tresc" style="margin-top: 0.6rem; padding: 0.8rem; background: white; border-radius: 8px; border: 1px solid #fbcfe8; color: #831843; font-family: monospace;">
              ${p.specyfikacja_ukryta}
            </div>
          </div>
        </div>

      </article>
    `;

    const tabButtons = kontenerSzczegoly.querySelectorAll(".tab-btn");
    const tabPanels = kontenerSzczegoly.querySelectorAll(".tab-panel");

    tabButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        const targetId = btn.getAttribute("data-target");

        tabButtons.forEach(b => b.classList.remove("aktywna", "aktywny"));
        tabPanels.forEach(p => p.classList.remove("aktywny"));

        btn.classList.add("aktywny");
        const panel = document.getElementById(targetId);
        if (panel) {
          panel.classList.add("aktywny");
        }
      });
    });
  }
});
