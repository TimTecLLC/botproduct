(function () {
  const api = window.TimTecCatalog;
  const chat = document.getElementById("chat-box");
  const form = document.getElementById("composer");
  const input = document.getElementById("query");
  const button = document.getElementById("search");
  const contact = document.getElementById("contact");
  let products = [];
  let ready = false;

  api.CONTACT.forEach((line, index) => {
    const row = document.createElement("span");
    if (index === 0) {
      row.className = "contact-name";
      row.textContent = line;
    } else if (line.startsWith("Email:")) {
      row.appendChild(document.createTextNode("Email: "));
      const mail = document.createElement("a");
      mail.href = "mailto:timtec@timtec.org";
      mail.textContent = "timtec@timtec.org";
      row.appendChild(mail);
    } else if (line.startsWith("Website:")) {
      row.appendChild(document.createTextNode("Website: "));
      const site = document.createElement("a");
      site.href = "https://www.timtec.org";
      site.textContent = "www.timtec.org";
      row.appendChild(site);
    } else if (line.startsWith("Phone:")) {
      row.appendChild(document.createTextNode("Phone: "));
      const phone = document.createElement("a");
      phone.href = "tel:+13022928500";
      phone.textContent = "302-292-8500";
      row.appendChild(phone);
    } else {
      row.textContent = line;
    }
    contact.appendChild(row);
  });

  function addRow(sender, content) {
    const row = document.createElement("div");
    row.className = sender === "user" ? "row user" : "row bot";
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    if (typeof content === "string") bubble.textContent = content;
    else bubble.appendChild(content);
    row.appendChild(bubble);
    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;
  }

  function productCard(product) {
    const card = document.createElement("article");
    card.className = "card";

    const title = document.createElement("h2");
    title.textContent = product.id || "Unknown ID";

    const library = document.createElement("p");
    library.className = "library";
    library.textContent = product.library ? `Library ${product.library}` : "Library not listed";

    const name = document.createElement("p");
    name.className = "iupac";
    name.textContent = product.iupac || "Name not listed";

    const meta = document.createElement("p");
    meta.className = "meta";
    meta.textContent = `Formula ${product.formula} · MW ${product.molecularWeight} · Purity ${product.purity}`;

    const stock = document.createElement("p");
    stock.className = "stock";
    stock.textContent = product.stock;

    const lead = document.createElement("p");
    lead.className = "lead";
    lead.textContent = `Lead time: ${product.lead}`;

    const prices = document.createElement("ul");
    prices.className = "prices";
    product.prices.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = `${item.dose}: ${item.price}`;
      prices.appendChild(li);
    });

    card.append(title, library, name, meta, stock, lead, prices);

    if (product.id) {
      const actions = document.createElement("div");
      actions.className = "actions";
      const coa = document.createElement("a");
      coa.href = api.coaUrl(product.id);
      coa.target = "_blank";
      coa.rel = "noopener noreferrer";
      coa.textContent = "CoA PDF";
      const sds = document.createElement("a");
      sds.href = api.sdsUrl(product.id);
      sds.target = "_blank";
      sds.rel = "noopener noreferrer";
      sds.textContent = "SDS PDF";
      const mail = document.createElement("a");
      mail.href = api.inquiryMailto(product);
      mail.textContent = "Email TimTec";
      actions.append(coa, sds, mail);
      card.appendChild(actions);
    }

    return card;
  }

  function virtualNotice() {
    const wrap = document.createElement("div");
    const title = document.createElement("p");
    title.className = "summary";
    title.textContent = "MCL-5000 is a virtual screening collection. It is not a purchasable compound.";
    const detail = document.createElement("p");
    detail.textContent = "This catalog does not list a structure, formula, price, or stock location for it. For library questions, email timtec@timtec.org.";
    wrap.append(title, detail);
    return wrap;
  }

  function renderResults(query, found) {
    const wrap = document.createElement("div");
    if (found.virtual) return virtualNotice();
    if (!found.total) {
      const empty = document.createElement("p");
      empty.textContent = `No products found matching “${query}”. Check the TimTec ID, or use the CoA and SDS tools for compounds outside this file.`;
      const tools = document.createElement("p");
      tools.className = "actions";
      const coa = document.createElement("a");
      coa.href = "https://structure.timtec.org/coa";
      coa.target = "_blank";
      coa.rel = "noopener noreferrer";
      coa.textContent = "CoA tool";
      const sds = document.createElement("a");
      sds.href = "https://structure.timtec.org/msds";
      sds.target = "_blank";
      sds.rel = "noopener noreferrer";
      sds.textContent = "SDS tool";
      tools.append(coa, sds);
      wrap.append(empty, tools);
      return wrap;
    }
    const summary = document.createElement("p");
    summary.className = "summary";
    summary.textContent = found.capped
      ? `Showing ${found.results.length} of ${found.total} matches. Search a full TimTec ID for one compound.`
      : `Found ${found.total} matching product${found.total === 1 ? "" : "s"}.`;
    wrap.appendChild(summary);
    found.results.forEach((product) => wrap.appendChild(productCard(product)));
    return wrap;
  }

  function setReady(isReady) {
    ready = isReady;
    input.disabled = !isReady;
    button.disabled = !isReady;
    if (isReady) input.focus();
  }

  function performSearch() {
    const query = input.value.trim();
    if (!query) return;
    addRow("user", query);
    input.value = "";
    if (!ready) {
      addRow("bot", "The catalog is still loading. Please wait a moment and try again.");
      return;
    }
    addRow("bot", renderResults(query, api.searchCatalog(products, query)));
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    performSearch();
  });

  async function loadCatalog() {
    const url = api.catalogRequestUrl(window.location.search);
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const raw = await response.json();
      if (!Array.isArray(raw)) throw new Error("Catalog file is not a product list");
      products = raw.map(api.normalizeProduct);
      chat.textContent = "";
      setReady(true);
      addRow(
        "bot",
        `Catalog loaded (${products.length.toLocaleString()} products). A01 and A02 show Orlando stock as Yes or No, with about a 1 business day lead. A03 is extended overseas stock.`
      );
    } catch (error) {
      chat.textContent = "";
      setReady(false);
      addRow("bot", `The catalog could not be loaded (${error.message}). Refresh the page, or email timtec@timtec.org.`);
    }
  }

  loadCatalog();
})();
