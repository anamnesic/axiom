#!/usr/bin/env bash
# Chronokairo AXIOM — Heavy Toolchains Installer for Linux / macOS
# Installs and configures Lean 4 (elan), Lake, and Julia.

set -euo pipefail

echo "================================================================="
echo "  Chronokairo AXIOM — Heavy Toolchains Installer (POSIX)         "
echo "================================================================="

# 1. Lean 4 / elan installation
if ! command -v elan >/dev/null 2>&1 && [ ! -f "$HOME/.elan/bin/elan" ]; then
    echo "[*] Installing elan (Lean 4 toolchain manager)..."
    curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh -s -- -y
    export PATH="$HOME/.elan/bin:$PATH"
    echo "[+] elan successfully installed!"
else
    echo "[+] elan is already installed."
    export PATH="$HOME/.elan/bin:$PATH"
fi

elan default stable
echo "[*] Installed Lean version:"
lean --version
lake --version

# 2. Julia installation check
if ! command -v julia >/dev/null 2>&1; then
    echo "[*] Julia is not found in PATH."
    if command -v juliaup >/dev/null 2>&1; then
        juliaup add release
        juliaup default release
    elif command -v brew >/dev/null 2>&1; then
        brew install --cask julia
    elif command -v apt-get >/dev/null 2>&1; then
        echo "[*] Install Julia on Debian/Ubuntu via juliaup:"
        curl -fsSL https://install.julialang.org | sh -s -- -y
    fi
else
    echo "[+] Julia is already installed:"
    julia --version
fi

# 3. Verify with AXIOM Doctor
echo "[*] Running AXIOM Doctor..."
python3 -m axiom.cli doctor

echo "================================================================="
echo "  Toolchains provisioning complete!                              "
echo "================================================================="
