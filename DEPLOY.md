# Deploy the TimTec Product Chatbot

Customer-facing stock label is **Orlando, Florida** (not Tampa). Public catalog JSON is **A01 + A02 only** (full A01 + full A02 (~194k) from Helix `catalog.db` (some A02 IDs may be alternate identifiers for the same chemical)); remaining milligrams are not included in the public file.


This repo is a **fully static** site. There is no backend, no database, and no
environment variables. The browser loads `index.html`, fetches
`catalog/TimTec_CATALOG_SOURCE.json` (~82 MB, 105,466 products, stored with
Git LFS), normalizes the raw catalog keys in-page, and searches locally.

Default data: **full catalog** at runtime via `fetch('./catalog/TimTec_CATALOG_SOURCE.json')`.

## 1. One-time Git LFS setup (required)

The catalog is tracked as a Git LFS object. Anyone who clones or deploys this
repo must have Git LFS installed.

```bash
# macOS
brew install git-lfs

# Ubuntu/Debian
sudo apt-get install git-lfs

git lfs install
```

If you cloned before LFS was configured, pull the real JSON (not the pointer):

```bash
git lfs pull
ls -lh catalog/TimTec_CATALOG_SOURCE.json
# expect ~79M, not a 130-byte pointer file
```

### If the 82 MB catalog is missing from this branch

The page still expects `catalog/TimTec_CATALOG_SOURCE.json`. Copy the source
catalog, then commit it through LFS:

```bash
git lfs install
git checkout cursor/grok-deploy-ready-75a2

# .gitattributes already tracks catalog/TimTec_CATALOG_SOURCE.json
mkdir -p catalog
python3 scripts/prepare_catalog.py \
  --source /path/to/TimTec_CATALOG_SOURCE.json

# or copy directly:
# cp /path/to/TimTec_CATALOG_SOURCE.json catalog/TimTec_CATALOG_SOURCE.json

git add .gitattributes catalog/TimTec_CATALOG_SOURCE.json
git commit -m "Add full TimTec catalog via Git LFS"
git push origin cursor/grok-deploy-ready-75a2
```

Confirm GitHub stored the object, not the pointer, as the blob:

```bash
git lfs ls-files
# catalog/TimTec_CATALOG_SOURCE.json should be listed
```

## 2. Deploy on Render (static site)

The site is static: Render only needs to publish the repo root after the
catalog JSON is in place. No Node/Python build, no env vars.

Render static builders do **not** have Git LFS, so the Blueprint
`buildCommand` does **not** run `git lfs pull`. It curls the public GitHub
media URL for `catalog/TimTec_CATALOG_SOURCE.json` instead (the same
command already used by the live service). The LFS-tracked catalog file
stays in the repo for local clones.

### Option A — Blueprint (`render.yaml`)

1. Push this branch (or merge it to the branch Render should deploy).
2. In [Render](https://dashboard.render.com), click **New** → **Blueprint**.
3. Connect `TimTecLLC/botproduct` and select this branch.
4. Render reads `render.yaml` and creates a static site named
   `timtec-catalog-bot` with:
   - **Runtime:** static
   - **Build command:** curl the public GitHub media URL for
     `catalog/TimTec_CATALOG_SOURCE.json` (see `render.yaml`; Render
     static has no `git-lfs`)
   - **Publish directory:** `.` (repo root)
5. Click **Apply**. When the deploy finishes, open the
   `https://<service>.onrender.com` URL Render assigns.

### Option B — Manual static site

1. [dashboard.render.com](https://dashboard.render.com) → **New** → **Static Site**.
2. Connect `github.com/TimTecLLC/botproduct`.
3. Set:
   - **Branch:** `cursor/grok-deploy-ready-75a2` (or `main` after merge)
   - **Build Command:** the `buildCommand` from `render.yaml` (curl the
     public GitHub media URL; do not use `git lfs pull` — Render static
     has no Git LFS)
   - **Publish Directory:** `.`
4. Leave environment variables empty.
5. Create the site and wait for the first deploy.

### After it is live

- Home page: `https://<service>.onrender.com/`
- Catalog JSON: `https://<service>.onrender.com/catalog/TimTec_CATALOG_SOURCE.json`
- Search `ST091907` or `ST082075` (TimTec ID), an exact SMILES string, or an
  IUPAC substring. The first load downloads the full catalog; later visits
  can use the browser cache (Render sets a 1-day `Cache-Control` on
  `/catalog/*`).

### Render free-tier caveats

- Free static sites spin down after idle time. The **first request after
  idle** can take 30–60 seconds, then the ~82 MB catalog still has to
  download into the browser.
- Free bandwidth is limited. Serving an 82 MB JSON on every cold visit adds
  up. Use the lighter-data alternative below if that becomes a problem.
- Render static has no Git LFS. If the deploy log shows a 130-byte pointer
  instead of the real JSON, confirm the build command curls
  `https://media.githubusercontent.com/media/TimTecLLC/botproduct/main/catalog/TimTec_CATALOG_SOURCE.json`
  (as in `render.yaml`) and that the file is a non-empty JSON payload.
- Do not add a catch-all rewrite of `/*` → `/index.html`. That would break
  the catalog `fetch`.

## 3. Local preview (same files Render publishes)

```bash
git lfs pull
python3 -m http.server 3000 --bind 0.0.0.0 --directory .
# open http://localhost:3000
```

## 4. Lighter-data alternative (optional)

The default deliverable is the **full** 105,466-product catalog. An 82 MB
JSON parsed in the browser is heavy (memory, first-paint, free-tier
bandwidth). These options keep the same `index.html` and search behavior.

| Approach | How | Typical size | Trade-off |
|---|---|---|---|
| **Compact JSON** (recommended first step) | `python3 scripts/prepare_catalog.py --source /path/to/TimTec_CATALOG_SOURCE.json --compact` | ~61 MB, still 105,466 products | Same search coverage, ~22% less download |
| **Curated subset** | `python3 scripts/prepare_catalog.py --source /path/to/TimTec_CATALOG_SOURCE.json --limit 500 --compact` | hundreds of KB | Fast load; only the first N products are searchable |
| **Bundled sample** | `python3 scripts/prepare_catalog.py --source scripts/sample_catalog.json` | ~12 products | Local/demo only |

After rewriting `catalog/TimTec_CATALOG_SOURCE.json`, commit through LFS and
redeploy. No HTML changes are required.

Splitting the catalog into shards (for example by ID prefix) would need a
small client change to pick a shard before search. That is **not** the
default; use compact or `--limit` unless you are ready to change
`index.html`.

## 5. What you do not need

- No server, Docker, or runtime besides a static file host
- No API keys or Render environment variables
- Do not inline the 82 MB catalog into `timtec_bot_v_2.html` for production
  (`REPLACE_ME_WITH_JSON` is only suitable for small samples)
