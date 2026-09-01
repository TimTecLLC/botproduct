#!/usr/bin/env python3
"""Prepare catalog/TimTec_CATALOG_SOURCE.json for the static chatbot.

The page fetches this file at runtime and normalizes raw keys in the browser.
Default output is the FULL catalog (all products). Optional flags produce a
lighter file for local preview or constrained hosts.

Examples:
  # Full catalog (copy as-is)
  python3 scripts/prepare_catalog.py --source /path/to/TimTec_CATALOG_SOURCE.json

  # Full catalog, compacted (~22% smaller, same 105,466 products)
  python3 scripts/prepare_catalog.py --source /path/to/TimTec_CATALOG_SOURCE.json --compact

  # Curated subset for a lighter deploy
  python3 scripts/prepare_catalog.py --source scripts/sample_catalog.json
  python3 scripts/prepare_catalog.py --source /path/to/TimTec_CATALOG_SOURCE.json --limit 500 --compact
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "catalog" / "TimTec_CATALOG_SOURCE.json"
SAMPLE = REPO_ROOT / "scripts" / "sample_catalog.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=SAMPLE,
        help="Raw TimTec catalog JSON (default: scripts/sample_catalog.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Destination path (default: catalog/TimTec_CATALOG_SOURCE.json)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Keep only the first N products (0 = all). Use for a curated subset.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Write minified JSON (same products, smaller file).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser()
    if not source.is_file():
        print(f"Source not found: {source}", file=sys.stderr)
        return 1

    output = args.output.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)

    if not args.limit and not args.compact:
        shutil.copyfile(source, output)
        print(f"Copied {source} -> {output} ({output.stat().st_size} bytes).")
        return 0

    with source.open(encoding="utf-8") as fh:
        catalog = json.load(fh)

    if not isinstance(catalog, list):
        print("Catalog source must be a JSON array of products.", file=sys.stderr)
        return 1

    if args.limit and args.limit > 0:
        catalog = catalog[: args.limit]

    if args.compact:
        text = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"))
    else:
        text = json.dumps(catalog, ensure_ascii=False, indent=4)

    output.write_text(text + "\n", encoding="utf-8")
    print(
        f"Wrote {output} ({len(catalog)} products, {output.stat().st_size} bytes) "
        f"from {source}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
