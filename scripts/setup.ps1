# One-time setup
Set-Location $PSScriptRoot\..
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\playwright install chromium

Write-Host "Setup complete. Run: .\.venv\Scripts\python run.py"
