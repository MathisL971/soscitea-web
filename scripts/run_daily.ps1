# Nightly inventory refresh — schedule in Windows Task Scheduler (daily ~2:00 AM)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
& .\.venv\Scripts\python.exe run.py --priority 1 @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .\.venv\Scripts\python.exe scripts\sync_events.py
exit $LASTEXITCODE
