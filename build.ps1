param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --name discografia `
  discografia_app.py
