const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const api = require("../catalog.js");

const root = path.join(__dirname, "..");

function read(name) {
  return fs.readFileSync(path.join(root, name), "utf8");
}

test("fractional purity matches the CoA percent style", () => {
  assert.equal(api.formatPurity("0.9"), "90%");
  assert.equal(api.formatPurity("0.995"), "99.5%");
  assert.equal(api.displayPrice("request availability and price"), "Request");
  assert.equal(api.displayPrice("120"), "$120");
});

test("A01 and A02 use Orlando Yes/No and about a 1-day lead", () => {
  const yes = api.normalizeProduct({
    TimTec_ID: "ST091907",
    Library: "A01",
    "In Stock Orlando, FL": "Yes",
    "Lead Time": "1 business day",
    "Purity %": "0.9",
    "Molecular weight": 344.293457,
    IUPAC: "ethyl example",
    SMILES: "CCO",
  });
  assert.equal(yes.stock, "In stock (Orlando, Florida): Yes");
  assert.equal(yes.lead, "about 1 business day");
  assert.equal(yes.purity, "90%");
  assert.equal(yes.molecularWeight, "344.29");

  const no = api.normalizeProduct({
    TimTec_ID: "ST046822",
    Library: "a02",
    "In Stock Orlando, FL": "No",
    "Lead Time": "1 business day",
  });
  assert.equal(no.library, "A02");
  assert.equal(no.stock, "In stock (Orlando, Florida): No");
  assert.equal(no.lead, "about 1 business day");
});

test("A03 is extended overseas stock and is not labeled Orlando", () => {
  const overseas = api.normalizeProduct({
    TimTec_ID: "A03-ROW",
    Library: "A03",
    "In Stock Orlando, FL": "Yes",
    "Lead Time": "1 business day",
  });
  assert.equal(overseas.stock, "Extended overseas stock");
  assert.equal(overseas.lead, "1-3 weeks");
  assert.equal(overseas.stock.toLowerCase().includes("orlando"), false);
  assert.equal(JSON.stringify(overseas).toLowerCase().includes("tampa"), false);
  assert.equal(overseas.iupac, "");
  assert.equal(overseas.smiles, "");
});

test("legacy stock column is read and the old city is not shown", () => {
  const product = api.normalizeProduct({
    TimTec_ID: "ST000114",
    Library: "A01",
    "In Stock Tampa, FL": "Yes",
  });
  assert.equal(product.stock, "In stock (Orlando, Florida): Yes");
  assert.equal(JSON.stringify(product).toLowerCase().includes("tampa"), false);
});

test("MCL-5000 is virtual and not searched as a compound", () => {
  assert.equal(api.isVirtualCollectionQuery("MCL-5000"), true);
  assert.equal(api.isVirtualCollectionQuery(" mcl5000 "), true);
  const found = api.searchCatalog([], "MCL-5000");
  assert.equal(found.virtual, true);
  assert.equal(found.total, 0);
  const notice = "MCL-5000 is a virtual screening collection. It is not a purchasable compound.";
  assert.equal(notice.toLowerCase().includes("smiles"), false);
});

test("CoA and SDS deep links stay on structure.timtec.org", () => {
  assert.equal(api.coaUrl("ST091907"), "https://structure.timtec.org/api/coa/pdf?id=ST091907");
  assert.equal(api.sdsUrl("ST091907"), "https://structure.timtec.org/api/msds/pdf?id=ST091907");
  assert.equal(api.inquiryMailto({ id: "ST091907", library: "A01", iupac: "n", smiles: "" }).startsWith("mailto:timtec@timtec.org"), true);
});

test("contact block is Kissimmee Suite 301", () => {
  const text = api.CONTACT.join("\n");
  assert.match(text, /1950 East Irlo Bronson Memorial Highway, Suite 301/);
  assert.match(text, /Kissimmee, Florida 34744/);
  assert.match(text, /302-292-8500/);
  assert.match(text, /302-292-8520/);
  assert.match(text, /timtec@timtec.org/);
  assert.match(text, /www\.timtec\.org/);
  assert.equal(/tampa|timtec\.net/i.test(text), false);
});

test("customer pages do not mention the old city or timtec.net", () => {
  const pages = ["index.html", "bot.js", "bot.css", "timtec_bot_v_2.html"].map(read).join("\n");
  assert.equal(/tampa|timtec\.net|tampa bay plaza/i.test(pages), false);
});

test("full catalog maps A01 and A02 without labeling an A03 row as Orlando", () => {
  const fullPath = path.join(root, "catalog", "TimTec_CATALOG_SOURCE.json");
  if (!fs.existsSync(fullPath) || fs.statSync(fullPath).size < 1000) return;
  const raw = JSON.parse(fs.readFileSync(fullPath, "utf8"));
  const products = raw.map(api.normalizeProduct);
  const a01 = api.searchCatalog(products, "ST091907");
  assert.equal(a01.total, 1);
  assert.equal(a01.results[0].stock, "In stock (Orlando, Florida): Yes");
  assert.equal(a01.results[0].lead, "about 1 business day");
  assert.equal(a01.results[0].library, "A01");

  const a02yes = api.searchCatalog(products, "ST4000116");
  assert.equal(a02yes.results[0].library, "A02");
  assert.equal(a02yes.results[0].stock, "In stock (Orlando, Florida): Yes");

  const a02no = api.searchCatalog(products, "ST046822");
  assert.equal(a02no.results[0].stock, "In stock (Orlando, Florida): No");

  const overseas = products.filter((product) => product.library === "A03" || product.library.startsWith("A03"));
  for (const product of overseas) {
    assert.equal(product.stock, "Extended overseas stock");
    assert.equal(product.stock.includes("Orlando"), false);
  }
  assert.equal(products.some((product) => /tampa/i.test(product.stock)), false);
});
