#!/usr/bin/env bash
# Scrape, sync, build, and deploy to Surge (same steps as the daily GitHub Action).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="python"
fi

echo "==> Scraping events..."
"$PYTHON" run.py --priority 1 "$@"

echo "==> Syncing events.json..."
"$PYTHON" scripts/sync_events.py

echo "==> Building site..."
cd web
pnpm install
pnpm build

echo "==> Deploying to Surge..."
pnpm surge

echo "==> Done."
