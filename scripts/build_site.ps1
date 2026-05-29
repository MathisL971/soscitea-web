# Sync scraper export, then build the frontend.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
& .\.venv\Scripts\python.exe scripts\sync_events.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Set-Location web
pnpm install
pnpm build
exit $LASTEXITCODE
