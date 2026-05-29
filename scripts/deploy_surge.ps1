# Build and deploy to Surge (uses web/surge.json for domain).
$ErrorActionPreference = "Stop"
Set-Location (Join-Path (Split-Path $PSScriptRoot -Parent) "web")
pnpm build
pnpm surge
