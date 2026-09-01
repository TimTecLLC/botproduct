#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

echo "Searching for Joomla configuration.php under ${ROOT}..."
CONFIG="$(find "$ROOT" -name configuration.php -path '*/public_html/*' -o -name configuration.php | head -1 || true)"

if [[ -z "$CONFIG" ]]; then
  echo "configuration.php not found. Listing top-level paths:"
  find "$ROOT" -maxdepth 3 -type d | head -40
  exit 1
fi

echo "Found: $CONFIG"
grep -E "^\s*public \\\$" "$CONFIG" | sed 's/password.*/password = [REDACTED]/' || true

echo
echo "Searching for SQL dumps..."
find "$ROOT" -type f \( -name '*.sql' -o -name '*.sql.gz' \) | head -20
