# Scrape, sync, build, and deploy to Surge (same steps as the daily GitHub Action).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "==> Scraping events..."
& .\.venv\Scripts\python.exe run.py --priority 1 @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Syncing events.json..."
& .\.venv\Scripts\python.exe scripts\sync_events.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Building site..."
Set-Location web
pnpm install
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
pnpm build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Deploying to Surge..."
pnpm surge
exit $LASTEXITCODE
