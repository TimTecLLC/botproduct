# Stock labels and contact QA

Date: 2026-09-22. Repo: `TimTecLLC/botproduct`. Live site: https://timtec-catalog-bot.onrender.com/

## What changed

- A01 and A02 show `In stock (Orlando, Florida): Yes` or `No`, and lead time `about 1 business day`.
- A03 (and A04) shows `Extended overseas stock` and lead time `1-3 weeks`. An Orlando Yes/No column on those rows is not printed.
- The page footer is TimTec, LLC, 1950 East Irlo Bronson Memorial Highway, Suite 301, Kissimmee, Florida 34744, phone 302-292-8500, fax 302-292-8520, timtec@timtec.org, www.timtec.org.
- Each catalog hit links to `https://structure.timtec.org/api/coa/pdf?id=` and `https://structure.timtec.org/api/msds/pdf?id=`.
- MCL-5000 is answered as a virtual collection. No structure, formula, or price is invented for it.
- The old `timtec_bot_v_2.html` template redirected to `index.html` so it no longer rendered a stock line from the retired column name.

## Catalog check

`catalog/TimTec_CATALOG_SOURCE.json` has 194,361 products: A01 131,037 and A02 63,324. There are no A03 rows in this file. The A03 label is covered by `tests/catalog.test.js` so a later export is not stamped Orlando.

Checked against the file:

| ID | Library | Label |
| --- | --- | --- |
| ST091907 | A01 | In stock (Orlando, Florida): Yes · about 1 business day · purity 90% |
| ST4000116 | A02 | In stock (Orlando, Florida): Yes |
| ST046822 | A02 | In stock (Orlando, Florida): No |

CoA and SDS for ST091907 returned `application/pdf` from structure.timtec.org on 2026-09-22.

## Tests

`node --test tests/catalog.test.js` — 9 passed, including the full-file lookups above.

## Render redeploy

Merge to `main`, then in the Render dashboard open **timtec-catalog-bot** and deploy the latest commit (or wait for auto-deploy). Hard-refresh `/`. The build command still downloads the catalog JSON from the `main` media URL; this change does not replace that file. Confirm the Kissimmee Suite 301 footer and an `ST091907` card whose CoA link opens `https://structure.timtec.org/api/coa/pdf?id=ST091907`.
