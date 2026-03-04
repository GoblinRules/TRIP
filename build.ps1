# TRIP (Tray IP) — Build Script
# Produces:
#   dist\TRIP.exe          (portable)
#   dist\TRIP_Setup.exe    (installer, requires Inno Setup)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
if (-not $root) { $root = (Get-Location).Path }

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TRIP Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ── 1) Install / upgrade build deps ──
Write-Host "`n[1/4] Installing build dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip pyinstaller | Out-Null
python -m pip install -r "$root\requirements.txt" | Out-Null

# ── 2) Run icon setup ──
Write-Host "[2/4] Generating icon variants..." -ForegroundColor Yellow
python "$root\setup_icons.py"

# ── 3) PyInstaller ──
Write-Host "[3/4] Building portable EXE with PyInstaller..." -ForegroundColor Yellow
python -m PyInstaller "$root\trip.spec" --noconfirm --clean --distpath "$root\dist" --workpath "$root\build"

if (-not (Test-Path "$root\dist\TRIP.exe")) {
    Write-Error "PyInstaller build failed — TRIP.exe not found."
    exit 1
}
Write-Host "  -> dist\TRIP.exe created" -ForegroundColor Green

# ── 4) Inno Setup (optional) ──
$iscc = Get-Command iscc -ErrorAction SilentlyContinue
if (-not $iscc) {
    # Try common install paths
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $iscc = Get-Item $c; break }
    }
}

if ($iscc) {
    Write-Host "[4/4] Building installer with Inno Setup..." -ForegroundColor Yellow
    & $iscc.FullName "$root\installer.iss"
    if (Test-Path "$root\dist\TRIP_Setup.exe") {
        Write-Host "  -> dist\TRIP_Setup.exe created" -ForegroundColor Green
    } else {
        Write-Warning "Inno Setup ran but TRIP_Setup.exe not found."
    }
} else {
    Write-Host "[4/4] Inno Setup not found — skipping installer build." -ForegroundColor DarkYellow
    Write-Host "  Install Inno Setup 6 to build the installer." -ForegroundColor DarkYellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Build complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

# Create portable.flag next to the exe for portable mode
New-Item -ItemType File -Path "$root\dist\portable.flag" -Force | Out-Null
Write-Host "  portable.flag created in dist\ (portable mode)" -ForegroundColor DarkGray
