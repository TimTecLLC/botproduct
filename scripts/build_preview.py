#!/usr/bin/env python3
"""Build a runnable local preview of the TimTec catalog chatbot.

The committed page (``timtec_bot_v_2.html``) ships with a ``REPLACE_ME_WITH_JSON``
placeholder because the product catalog is injected at build/deploy time. This
script fills that placeholder with a catalog so the site is fully functional
during local development, without modifying the source template.

Catalog source resolution order:
  1. ``$CATALOG_SOURCE`` (path to a raw TimTec catalog JSON), if set and present.
  2. ``scripts/sample_catalog.json`` (a small representative slice bundled here).

The output is written to ``dev/index.html`` (git-ignored).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = REPO_ROOT / "timtec_bot_v_2.html"
SAMPLE_CATALOG = REPO_ROOT / "scripts" / "sample_catalog.json"
OUTPUT_DIR = REPO_ROOT / "dev"
OUTPUT = OUTPUT_DIR / "index.html"
PLACEHOLDER = "REPLACE_ME_WITH_JSON"

DOSES = ["1mg", "2mg", "5mg", "10mg", "15mg", "20mg", "30mg", "50mg"]


def normalize(raw: dict) -> dict:
    """Map raw catalog keys onto the shape the page template expects."""
    product = {
        "TimTec_ID": raw.get("TimTec_ID"),
        "SMILES": raw.get("SMILES"),
        "IUPAC": raw.get("IUPAC"),
        "Amount": raw.get("Amount/mg", raw.get("Amount")),
        "InStock_Tampa": raw.get("In Stock Tampa, FL", raw.get("InStock_Tampa")),
        "Purity": raw.get("Purity %", raw.get("Purity")),
        "MolecularWeight": raw.get("Molecular weight", raw.get("MolecularWeight")),
    }
    for dose in DOSES:
        product[f"Price_{dose}"] = raw.get(f"Price_{dose}")
    return product


def resolve_catalog_path() -> Path:
    env_path = os.environ.get("CATALOG_SOURCE")
    if env_path:
        candidate = Path(env_path).expanduser()
        if candidate.is_file():
            return candidate
        print(f"CATALOG_SOURCE={env_path} not found; falling back to sample.", file=sys.stderr)
    return SAMPLE_CATALOG


def embed_for_template_literal(json_text: str) -> str:
    """Escape a string so it survives inside a JS backtick template literal."""
    return (
        json_text.replace("\\", "\\\\")
        .replace("`", "\\`")
        .replace("${", "\\${")
    )


def main() -> int:
    if not TEMPLATE.is_file():
        print(f"Template not found: {TEMPLATE}", file=sys.stderr)
        return 1

    catalog_path = resolve_catalog_path()
    if not catalog_path.is_file():
        print(f"Catalog source not found: {catalog_path}", file=sys.stderr)
        return 1

    with catalog_path.open(encoding="utf-8") as fh:
        raw_catalog = json.load(fh)

    catalog = [normalize(item) for item in raw_catalog]
    compact = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"))

    template_html = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template_html:
        print(f"Placeholder '{PLACEHOLDER}' not found in template.", file=sys.stderr)
        return 1

    rendered = template_html.replace(PLACEHOLDER, embed_for_template_literal(compact))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(rendered, encoding="utf-8")

    print(
        f"Built {OUTPUT.relative_to(REPO_ROOT)} "
        f"from {catalog_path.name} ({len(catalog)} products)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
