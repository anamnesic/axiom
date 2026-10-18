# Chronokairo AXIOM — Heavy Toolchains Installer for Windows (PowerShell)
# Installs and configures Lean 4 (elan), Lake, Mathlib, and Julia.

param(
    [switch]$LeanOnly,
    [switch]$JuliaOnly,
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  Chronokairo AXIOM — Heavy Toolchains Installer (Windows)       " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Lean 4 / elan installation
if (-not $JuliaOnly) {
    Write-Host "`n[*] Checking Lean 4 / elan toolchain..." -ForegroundColor Yellow
    $elanPath = Get-Command elan -ErrorAction SilentlyContinue
    $elanHomeBin = "$HOME\.elan\bin"

    if (-not $elanPath -and -not (Test-Path "$elanHomeBin\elan.exe")) {
        Write-Host "[-] elan is not installed. Installing via official installer..." -ForegroundColor Green
        try {
            $elanInit = "$env:TEMP\elan-init.ps1"
            Invoke-WebRequest -Uri "https://raw.githubusercontent.com/leanprover/elan/master/elan-init.ps1" -OutFile $elanInit
            & powershell -ExecutionPolicy Bypass -File $elanInit -y
            Remove-Item -Force $elanInit -ErrorAction SilentlyContinue
            Write-Host "[+] elan successfully installed to $elanHomeBin!" -ForegroundColor Green
        } catch {
            Write-Host "[!] Web install failed, attempting winget install..." -ForegroundColor Yellow
            winget install --id Lean.Elan -e --accept-package-agreements --accept-source-agreements
        }
    } else {
        Write-Host "[+] elan is already installed!" -ForegroundColor Green
    }

    # Ensure ~/.elan/bin is in current session and User PATH
    if (Test-Path $elanHomeBin) {
        if ($env:PATH -notlike "*$elanHomeBin*") {
            $env:PATH = "$elanHomeBin;$env:PATH"
        }
        $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if ($userPath -notlike "*$elanHomeBin*") {
            [Environment]::SetEnvironmentVariable("Path", "$elanHomeBin;$userPath", "User")
            Write-Host "[+] Added $elanHomeBin to User PATH." -ForegroundColor Green
        }
    }

    # Install Lean 4 stable
    if (Get-Command elan -ErrorAction SilentlyContinue) {
        Write-Host "[*] Ensuring Lean 4 stable toolchain is installed and default..." -ForegroundColor Yellow
        elan default stable
        lean --version
        lake --version
    }
}

# 2. Julia installation
if (-not $LeanOnly) {
    Write-Host "`n[*] Checking Julia toolchain..." -ForegroundColor Yellow
    $juliaPath = Get-Command julia -ErrorAction SilentlyContinue

    if (-not $juliaPath) {
        Write-Host "[-] Julia is not installed. Attempting installation via winget..." -ForegroundColor Green
        try {
            winget install --id Julialang.Julia -e --accept-package-agreements --accept-source-agreements
            Write-Host "[+] Julia installed via winget." -ForegroundColor Green
        } catch {
            Write-Host "[!] Winget install failed or unavailable. Please download from https://julialang.org/downloads/" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[+] Julia is already installed: $($juliaPath.Source)" -ForegroundColor Green
        julia --version
    }
}

# 3. Verify with AXIOM Doctor
Write-Host "`n[*] Running AXIOM Doctor self-test with new toolchains..." -ForegroundColor Yellow
python -m axiom.cli doctor

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "  Toolchains provisioning complete!                              " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
