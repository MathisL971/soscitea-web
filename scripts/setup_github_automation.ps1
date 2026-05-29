# Finish GitHub Actions daily deploy under MathisL971.
$ErrorActionPreference = "Stop"

$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

function Invoke-GitCommand {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$CommandArgs,
    [switch]$Silent
  )

  $previousPreference = $ErrorActionPreference
  $ErrorActionPreference = "SilentlyContinue"
  if ($Silent) {
    & git @CommandArgs 2>$null | Out-Null
  } else {
    & git @CommandArgs
  }
  $exitCode = $LASTEXITCODE
  $ErrorActionPreference = $previousPreference
  return $exitCode
}

$Gh = "$env:ProgramFiles\GitHub CLI\gh.exe"
if (-not (Test-Path $Gh)) {
  throw "GitHub CLI not found. Install from https://cli.github.com/"
}

$ExpectedUser = "MathisL971"
$Repo = "$ExpectedUser/soscitea-web"
$SurgeDomain = "soscitea.surge.sh"

$ActiveUser = & $Gh api user -q .login
if ($ActiveUser -ne $ExpectedUser) {
  Write-Host ""
  Write-Host "GitHub CLI is logged in as '$ActiveUser', not '$ExpectedUser'." -ForegroundColor Yellow
  Write-Host "Run this first, then re-run this script:" -ForegroundColor Yellow
  Write-Host "  gh auth login" -ForegroundColor Cyan
  Write-Host ""
  exit 1
}

Write-Host "==> Using GitHub account: $ExpectedUser"

$HasCommit = (Invoke-GitCommand -Silent @("rev-parse", "--verify", "HEAD")) -eq 0

if (-not $HasCommit) {
  Write-Host "==> Creating initial commit..."

  if ((Invoke-GitCommand @("add", "-A")) -ne 0) {
    throw "git add failed"
  }

  $commitMessage = @'
Initialize Soscitea scraper and web app with daily Surge deploy workflow.

Adds Montreal social-science events bulletin, nightly scrape pipeline, and GitHub Actions automation.
'@

  $messageFile = Join-Path $env:TEMP "soscitea-commit-msg.txt"
  Set-Content -Path $messageFile -Value $commitMessage -Encoding utf8NoBOM

  try {
    if ((Invoke-GitCommand @("commit", "-F", $messageFile)) -ne 0) {
      throw "git commit failed"
    }
  } finally {
    Remove-Item $messageFile -ErrorAction SilentlyContinue
  }
} else {
  Write-Host "==> Repository already has commits"
}

$RemoteUrl = "https://github.com/$Repo.git"
$previousPreference = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
$remotes = git remote
$ErrorActionPreference = $previousPreference
$HasOrigin = ($remotes -match "^origin$")

if (-not $HasOrigin) {
  if ((Invoke-GitCommand @("remote", "add", "origin", $RemoteUrl)) -ne 0) {
    throw "git remote add failed"
  }
} else {
  if ((Invoke-GitCommand @("remote", "set-url", "origin", $RemoteUrl)) -ne 0) {
    throw "git remote set-url failed"
  }
}

Write-Host "==> Ensuring repository exists: $Repo"
$previousPreference = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
& $Gh repo view $Repo 2>$null | Out-Null
$RepoExists = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = $previousPreference

if (-not $RepoExists) {
  Write-Host "==> Creating GitHub repository and pushing..."
  if ($HasOrigin) {
    & $Gh repo create $Repo --public --description "Montreal social-science events bulletin" --push --source .
  } else {
    & $Gh repo create $Repo --public --description "Montreal social-science events bulletin" --source . --remote origin --push
  }
  if ($LASTEXITCODE -ne 0) {
    Write-Host "==> gh repo create reported an issue; trying git push..."
    if ((Invoke-GitCommand @("push", "-u", "origin", "main")) -ne 0) {
      throw "git push failed"
    }
  }
} else {
  Write-Host "==> Pushing to $Repo"
  if ((Invoke-GitCommand @("push", "-u", "origin", "main")) -ne 0) {
    throw "git push failed"
  }
}

Write-Host "==> Configuring Surge secrets"
$SurgeToken = $env:SURGE_TOKEN
if (-not $SurgeToken) {
  Push-Location (Join-Path $Root "web")
  $SurgeToken = (pnpm exec surge token 2>&1 | Select-String -Pattern "[a-f0-9]{32}" | ForEach-Object { $_.Matches.Value } | Select-Object -First 1)
  Pop-Location
}

if (-not $SurgeToken) {
  throw "Could not read Surge token. Run 'pnpm exec surge token' in web/ or set SURGE_TOKEN."
}

& $Gh secret set SURGE_TOKEN --body $SurgeToken --repo $Repo
& $Gh secret set SURGE_DOMAIN --body $SurgeDomain --repo $Repo

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "  Repo:    https://github.com/$Repo"
Write-Host "  Site:    https://$SurgeDomain"
Write-Host "  Actions: https://github.com/$Repo/actions"
Write-Host ""
Write-Host "Daily workflow runs at 11:00 UTC. Trigger now:" -ForegroundColor Cyan
Write-Host "  gh workflow run deploy.yml --repo $Repo"
