/**
 * TechStore - Dynamiczny skrypt obsługi katalogu (Poziom 5.0 - Pink Edition)
 * Wymagania:
 * - Wstrzykiwanie danych przez fetch() z JSON/API (brak rekordów w surowym HTML)
 * - Doładowywanie porcjami (przycisk "Wczytaj więcej") oraz Paginacja (min. 5 podstron)
 * - Dwie struktury: Karty (article) oraz Tabela (table bez znacznika tbody)
 * - Losowa kolejność atrybutów w kartach produktu
 * - Atrybuty w data-* (data-sku, data-ean, data-id)
 * - Filtrowanie i sortowanie w czasie rzeczywistym
 */

document.addEventListener("DOMContentLoaded", () => {
  let allProducts = [];
  let filteredProducts = [];
  let currentPage = 1;
  const itemsPerPage = 50; // 430 rekordów / 50 = 9 stron

  const ladowanieBox = document.getElementById("ladowanie-box");
  const siatkaKart = document.getElementById("siatka-kart");
  const tabelaProduktow = document.getElementById("tabela-produktow");
  const btnWczytajWiecej = document.getElementById("btn-wczytaj-wiecej");
  const paginacjaKontener = document.getElementById("paginacja");
  const licznikProduktow = document.getElementById("licznik-produktow");
  const licznikKarty = document.getElementById("licznik-karty");
  const licznikTabela = document.getElementById("licznik-tabela");

  const filtrKategoria = document.getElementById("filtr-kategoria");
  const sortowanieCena = document.getElementById("sortowanie-cena");
  const trybWyswietlania = document.getElementById("tryb-wyswietlania");
  const kontenerKart = document.getElementById("kontener-sekcji-kart");
  const kontenerTabeli = document.getElementById("kontener-sekcji-tabeli");

  // Odczytaj stronę z URL (np. ?page=2)
  const urlParams = new URLSearchParams(window.location.search);
  const initialPage = parseInt(urlParams.get("page")) || 1;

  async function fetchAllData() {
    pokazLadowanie(true);
    try {
      const resp = await fetch("/data/products.json");
      if (!resp.ok) {
        throw new Error(`Błąd HTTP: ${resp.status}`);
      }
      allProducts = await resp.json();
      filteredProducts = [...allProducts];

      currentPage = initialPage;
      zastosujFiltryISortowanie(false);
      zbudujPaginacje();
    } catch (err) {
      console.error("Błąd podczas pobierania danych:", err);
      licznikProduktow.textContent = "Błąd pobierania bazy danych!";
      licznikProduktow.style.backgroundColor = "#fee2e2";
      licznikProduktow.style.color = "#dc2626";
    } finally {
      pokazLadowanie(false);
    }
  }

  function pokazLadowanie(stan) {
    if (stan) {
      ladowanieBox.classList.add("aktywny");
      btnWczytajWiecej.disabled = true;
    } else {
      ladowanieBox.classList.remove("aktywny");
      btnWczytajWiecej.disabled = false;
    }
  }

  function zastosujFiltryISortowanie(resetPaginacji = true) {
    const kategoria = filtrKategoria.value;
    const sort = sortowanieCena.value;

    let items = [...allProducts];

    // Filtrowanie
    if (kategoria !== "all") {
      items = items.filter(p => p.kategoria === kategoria);
    }

    // Sortowanie
    if (sort === "price_asc") {
      items.sort((a, b) => a.cena_raw - b.cena_raw);
    } else if (sort === "price_desc") {
      items.sort((a, b) => b.cena_raw - a.cena_raw);
    } else if (sort === "name_asc") {
      items.sort((a, b) => a.nazwa.localeCompare(b.nazwa));
    }

    filteredProducts = items;
    if (resetPaginacji) {
      currentPage = 1;
    }

    renderujStrone(currentPage, false);
    zbudujPaginacje();
  }

  function renderujStrone(strona, doladuj = false) {
    pokazLadowanie(true);

    setTimeout(() => {
      const startIndex = doladuj ? 0 : (strona - 1) * itemsPerPage;
      const endIndex = strona * itemsPerPage;
      const itemsToShow = filteredProducts.slice(startIndex, endIndex);

      if (!doladuj) {
        siatkaKart.innerHTML = "";
        const existingRows = tabelaProduktow.querySelectorAll("tr.produkt-wiersz");
        existingRows.forEach(row => row.remove());
      }

      const half = Math.ceil(itemsToShow.length / 2);
      const itemsForCards = itemsToShow.slice(0, half);
      const itemsForTable = itemsToShow.slice(half);

      // Renderowanie Kart
      renderujKarty(itemsForCards, doladuj);

      // Renderowanie Tabeli
      renderujTabele(itemsForTable, doladuj);

      // Liczniki
      const calkowitaLiczba = filteredProducts.length;
      const aktualnieWidoczne = Math.min(endIndex, calkowitaLiczba);
      licznikProduktow.textContent = `Widoczne: ${aktualnieWidoczne} z ${calkowitaLiczba} rekordów (Strona ${strona})`;
      licznikKarty.textContent = `${siatkaKart.children.length} kart`;
      licznikTabela.textContent = `${tabelaProduktow.querySelectorAll("tr.produkt-wiersz").length} wierszy`;

      // Aktualizacja przycisku "Wczytaj więcej"
      if (aktualnieWidoczne >= calkowitaLiczba) {
        btnWczytajWiecej.disabled = true;
        btnWczytajWiecej.textContent = "Załadowano wszystkie pozycje (Koniec katalogu)";
      } else {
        btnWczytajWiecej.disabled = false;
        btnWczytajWiecej.textContent = `Wczytaj kolejną porcję (${aktualnieWidoczne}/${calkowitaLiczba}) (\u2193)`;
      }

      pokazLadowanie(false);
    }, 350);
  }

  function renderujKarty(items, doladuj) {
    if (!doladuj) {
      siatkaKart.innerHTML = "";
    }

    items.forEach(prod => {
      const card = document.createElement("article");
      card.className = "produkt-karta";
      card.setAttribute("data-id", prod.id);
      card.setAttribute("data-sku", prod.kod_produktu);
      card.setAttribute("data-ean", prod.ean);

      const naglowek = document.createElement("div");
      naglowek.className = "karta-naglowek";
      naglowek.innerHTML = `
        <h3 class="nazwa"><a class="nazwa-produktu" href="detail.html?id=${prod.id}">${prod.nazwa}</a></h3>
        <div class="cena cena-wyrozniona">${prod.cena}</div>
      `;
      card.appendChild(naglowek);

      // UTRUDNIENIE 5.0: Losowa kolejność atrybutów w karcie produktu
      const atrybutyLista = [
        { etykieta: "Kategoria", klasa: "kategoria", wartosc: prod.kategoria },
        { etykieta: "Producent", klasa: "producent", wartosc: prod.producent },
        { etykieta: "Dostępność", klasa: "dostepnosc", wartosc: prod.dostepnosc },
        { etykieta: "Ocena", klasa: "ocena", wartosc: prod.ocena ? `${prod.ocena}/5.0 ⭐` : "Brak oceny" },
        { etykieta: "Opinie", klasa: "liczba-opinii", wartosc: `${prod.liczba_opinii} opinii` },
        { etykieta: "Gwarancja", klasa: "gwarancja", wartosc: prod.gwarancja || "Brak informacji" },
        { etykieta: "Data dodania", klasa: "data-dodania", wartosc: prod.data_dodania },
        { etykieta: "Stan", klasa: "stan", wartosc: prod.stan },
        { etykieta: "Darmowa dostawa", klasa: "darmowa-dostawa", wartosc: prod.darmowa_dostawa }
      ];

      tasujTablice(atrybutyLista);

      const kontenerAtrybutow = document.createElement("div");
      kontenerAtrybutow.className = "karta-atrybuty";

      atrybutyLista.forEach(atr => {
        const wiersz = document.createElement("div");
        wiersz.className = "atrybut-wiersz";
        wiersz.innerHTML = `
          <span class="atrybut-etykieta">${atr.etykieta}:</span>
          <span class="atrybut-wartosc ${atr.klasa}">${atr.wartosc}</span>
        `;
        kontenerAtrybutow.appendChild(wiersz);
      });
      card.appendChild(kontenerAtrybutow);

      const stopka = document.createElement("div");
      stopka.className = "karta-stopka";
      stopka.innerHTML = `
        <span class="sku-info" style="font-size: 0.82rem; color: #a27296; font-weight: 600;">ID: #${prod.id}</span>
        <a class="link-szczegoly" href="detail.html?id=${prod.id}">Szczeg&oacute;&lstrok;y &rarr;</a>
      `;
      card.appendChild(stopka);

      siatkaKart.appendChild(card);
    });
  }

  function renderujTabele(items, doladuj) {
    if (!doladuj) {
      const existingRows = tabelaProduktow.querySelectorAll("tr.produkt-wiersz");
      existingRows.forEach(row => row.remove());
    }

    items.forEach(prod => {
      const tr = document.createElement("tr");
      tr.className = "produkt-wiersz";
      tr.setAttribute("data-id", prod.id);
      tr.setAttribute("data-sku", prod.kod_produktu);
      tr.setAttribute("data-ean", prod.ean);

      tr.innerHTML = `
        <td class="kol-id" style="font-weight: 700; color: #be185d;">${prod.id}</td>
        <td class="kol-nazwa">
          <a class="nazwa-produktu link-szczegoly" href="detail.html?id=${prod.id}">${prod.nazwa}</a>
          <p class="niezamkniety-akapit" style="font-size: 0.8rem; color: #9d658c; margin-top: 0.2rem;">Stan: ${prod.stan} | EAN: ${prod.ean}
        </td>
        <td class="kol-cena cena">${prod.cena}</td>
        <td class="kol-kategoria kategoria"><span class="badge" style="padding: 0.2rem 0.6rem; font-size: 0.8rem;">${prod.kategoria}</span></td>
        <td class="kol-producent producent" style="font-weight: 600;">${prod.producent}</td>
        <td class="kol-dostepnosc dostepnosc">${prod.dostepnosc}</td>
        <td class="kol-ocena ocena">${prod.ocena ? prod.ocena : "-"}</td>
        <td class="kol-gwarancja gwarancja">${prod.gwarancja ? prod.gwarancja : "-"}</td>
        <td class="kol-data data-dodania" style="font-size: 0.85rem; color: #86557e;">${prod.data_dodania}</td>
        <td class="kol-akcja">
          <a class="link-szczegoly" href="detail.html?id=${prod.id}">Przejd&zacute; &rarr;</a>
        </td>
      `;

      tabelaProduktow.appendChild(tr);
    });
  }

  function zbudujPaginacje() {
    paginacjaKontener.innerHTML = "";
    const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);

    for (let p = 1; p <= totalPages; p++) {
      const btn = document.createElement("button");
      btn.textContent = p;
      btn.setAttribute("data-page", p);
      if (p === currentPage) {
        btn.classList.add("aktywna");
      }
      btn.addEventListener("click", () => {
        currentPage = p;
        window.history.pushState({}, "", `?page=${p}`);
        renderujStrone(currentPage, false);
        zaktualizujAktywnyPrzyciskPaginacji(p);
      });
      paginacjaKontener.appendChild(btn);
    }
  }

  function zaktualizujAktywnyPrzyciskPaginacji(activePage) {
    const buttons = paginacjaKontener.querySelectorAll("button");
    buttons.forEach(b => {
      const p = parseInt(b.getAttribute("data-page"));
      if (p === activePage) {
        b.classList.add("aktywna");
      } else {
        b.classList.remove("aktywna");
      }
    });
  }

  btnWczytajWiecej.addEventListener("click", () => {
    currentPage++;
    renderujStrone(currentPage, true);
    zaktualizujAktywnyPrzyciskPaginacji(currentPage);
  });

  filtrKategoria.addEventListener("change", () => zastosujFiltryISortowanie(true));
  sortowanieCena.addEventListener("change", () => zastosujFiltryISortowanie(false));

  trybWyswietlania.addEventListener("change", (e) => {
    const tryb = e.target.value;
    if (tryb === "karty") {
      kontenerKart.style.display = "block";
      kontenerTabeli.style.display = "none";
    } else if (tryb === "tabela") {
      kontenerKart.style.display = "none";
      kontenerTabeli.style.display = "block";
    } else {
      kontenerKart.style.display = "block";
      kontenerTabeli.style.display = "block";
    }
  });

  function tasujTablice(array) {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }

  fetchAllData();
});
