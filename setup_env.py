"""Chronokairo AXIOM — Environment Setup and Configuration Script.

Provides automated, cross-platform configuration for:
  - Minimal setup (--min): SymPy + mpmath (core CAS & verification)
  - Standard setup (default): SymPy + mpmath + pypdf + markitdown
  - Full setup (--full): Complete scientific suite (SciPy, Matplotlib, MCP, Lean 4, Julia)

Usage:
  python setup_env.py --min
  python setup_env.py --full
  python setup_env.py --check
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent


def print_banner(title: str) -> None:
    sep = "=" * 65
    print(f"\n{sep}")
    print(f"  Chronokairo AXIOM — {title}")
    print(f"{sep}\n")


def run_pip(args: list[str]) -> bool:
    cmd = [sys.executable, "-m", "pip"] + args
    print(f"[*] Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd)
    return res.returncode == 0


def install_requirements(req_file: str) -> bool:
    req_path = ROOT / req_file
    if not req_path.exists():
        print(f"[!] Error: {req_file} not found in {ROOT}")
        return False
    print(f"[*] Installing packages from {req_file}...")
    return run_pip(["install", "-r", str(req_path)])


def install_heavy_toolchains() -> bool:
    os_name = platform.system().lower()
    print_banner("Heavy Toolchains Setup (Lean 4, Lake, Julia)")

    if "windows" in os_name:
        ps1_script = ROOT / "scripts" / "install_toolchains.ps1"
        if ps1_script.exists():
            print(f"[*] Executing Windows toolchains script: {ps1_script}")
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps1_script)]
            res = subprocess.run(cmd)
            return res.returncode == 0
        else:
            print("[!] scripts/install_toolchains.ps1 not found.")
            return False
    else:
        sh_script = ROOT / "scripts" / "install_toolchains.sh"
        if sh_script.exists():
            print(f"[*] Executing Unix toolchains script: {sh_script}")
            cmd = ["bash", str(sh_script)]
            res = subprocess.run(cmd)
            return res.returncode == 0
        else:
            print("[!] scripts/install_toolchains.sh not found.")
            return False


def run_diagnostics() -> int:
    print_banner("Running AXIOM Diagnostics (axiom doctor)")
    cmd = [sys.executable, "-m", "axiom.cli", "doctor"]
    res = subprocess.run(cmd)
    return res.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Chronokairo AXIOM environment setup utility."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--min",
        action="store_true",
        help="Setup minimal environment (SymPy + mpmath).",
    )
    group.add_argument(
        "--full",
        action="store_true",
        help="Setup full environment (CAS, SciPy, Matplotlib, MCP, MarkItDown, and heavy toolchains).",
    )
    group.add_argument(
        "--check",
        action="store_true",
        help="Run health diagnostics without installing packages.",
    )
    parser.add_argument(
        "--skip-toolchains",
        action="store_true",
        help="Skip Lean 4 / Julia binary installers even during full setup.",
    )

    args = parser.parse_args(argv)

    if args.check:
        return run_diagnostics()

    if args.min:
        print_banner("Configuring MINIMAL Setup")
        success = install_requirements("requirements-min.txt")
        if not success:
            print("[!] Failed to install minimal requirements.")
            return 1
        print("[+] Minimal Python packages installed successfully.")
        return run_diagnostics()

    if args.full:
        print_banner("Configuring FULL Setup")
        success = install_requirements("requirements-full.txt")
        if not success:
            print("[!] Failed to install full Python requirements.")
            return 1

        if not args.skip_toolchains:
            print("\n[*] Checking heavy toolchains (Lean 4, Julia)...")
            tc_success = install_heavy_toolchains()
            if not tc_success:
                print("[!] Warning: Some external toolchains could not be installed automatically.")
                print("    See skills/toolchain-management/SKILL.md for manual instructions.")

        return run_diagnostics()

    # Default: Standard setup
    print_banner("Configuring STANDARD Setup")
    success = install_requirements("requirements.txt")
    if not success:
        print("[!] Failed to install standard requirements.")
        return 1
    return run_diagnostics()


if __name__ == "__main__":
    sys.exit(main())
