# Soscitea

Montreal social-science events aggregator: a Python scraper feeds a React bulletin site.

## Structure

| Path | Purpose |
|---|---|
| `scraper/` | Nightly scraper adapters, filters, SQLite store |
| `data/` | Scraper output (`upcoming_events.json`, local DB) |
| `web/` | Vite + React frontend |
| `web/public/events.json` | Events feed consumed by the site (synced from scraper export) |
| `sources.json` | Source registry for adapters |

## Local development

### 1. Python scraper

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
python -m playwright install chromium
python run.py --priority 1
python scripts/sync_events.py
```

Optional: re-apply location/time enrichment to an existing export without re-scraping:

```powershell
python scripts/reprocess_export.py
python scripts/sync_events.py
```

### 2. Frontend

```powershell
cd web
pnpm install
pnpm dev
```

Open http://localhost:5173 — the app loads `/events.json` from `web/public/`.

### One-shot refresh + build

```powershell
.\scripts\run_daily.ps1
.\scripts\build_site.ps1
```

## Deploy pipeline

GitHub Actions workflow `.github/workflows/deploy.yml` runs **once per day**:

1. Scrape sources (`python run.py --priority 1`)
2. Sync `data/upcoming_events.json` → `web/public/events.json`
3. Run scraper tests
4. Build the Vite site (`web/dist/`)
5. Deploy to **[Surge](https://surge.sh)**

**Triggers:** daily at 11:00 UTC (~6–7 AM Montreal), or **Run workflow** manually in the Actions tab.

Code changes are **not** auto-deployed on push — they go live on the next daily run (or trigger the workflow by hand).

### Publish now (local)

Same pipeline as CI, one command:

```powershell
.\scripts\publish.ps1
```

Requires Surge login (`surge login`) or `SURGE_TOKEN` in the environment. Domain is set in `web/surge.json`.

### GitHub Actions (MathisL971)

The daily workflow lives in `.github/workflows/deploy.yml`. One-time setup:

1. Log into GitHub CLI as **MathisL971** (not another account):

   ```powershell
   gh auth login
   ```

2. Run the setup script from the repo root:

   ```powershell
   .\scripts\setup_github_automation.ps1
   ```

   This creates `MathisL971/soscitea-web` (if needed), pushes the code, and sets `SURGE_TOKEN` + `SURGE_DOMAIN` secrets.

3. Optional — trigger the first deploy immediately:

   ```powershell
   gh workflow run deploy.yml --repo MathisL971/soscitea-web
   ```

**Triggers:** daily at 11:00 UTC (~6–7 AM Montreal), or manual dispatch in Actions.

### Local deploy (build only, skip scrape)

```powershell
.\scripts\build_site.ps1
.\scripts\deploy_surge.ps1
```

Or from `web/` after editing `surge.json`:

```powershell
pnpm build
pnpm surge
```

The site is served at the root of your Surge domain (`base: /`), so assets and `/events.json` resolve normally.

## Tests

```powershell
pip install -r requirements-dev.txt
pytest tests/ -q
```

## Data enrichment

The scraper fills missing **locations** and **times** from event titles/descriptions when adapters leave them blank — e.g. McGill `Location:` lines, `@ Salle …`, `Campus de …`, and `Time:` / `de 17:00 à 19:00` patterns.

Enrichment runs at scrape time (`scraper/enrich.py`) and again at export filtering (`scraper/filters.py`).
