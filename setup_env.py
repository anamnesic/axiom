"""Chronokairo AXIOM — Environment Setup and Configuration Script.

Provides automated, cross-platform configuration for:
  - Minimal setup (--min): SymPy + mpmath (core CAS & verification)
  - Standard setup (default): SymPy + mpmath + pypdf + markitdown
  - Full setup (--full): Complete scientific suite (SciPy, Matplotlib, MCP, Lean 4, Julia)
  - Custom setup (--custom / --checklist): Interactive checklist to select exact components

Usage:
  python setup_env.py --min
  python setup_env.py --full
  python setup_env.py --custom
  python setup_env.py --select cas,docs,lean
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
from typing import Any


ROOT = Path(__file__).resolve().parent

COMPONENTS: list[dict[str, Any]] = [
    {
        "id": "cas",
        "name": "Core CAS & Symbolic Arithmetic",
        "detail": "SymPy 1.14 + mpmath (exact symbolic manipulation & equations)",
        "pip_packages": ["sympy>=1.12", "mpmath>=1.3"],
        "default": True,
        "required": True,
    },
    {
        "id": "docs",
        "name": "Scientific Document Extraction",
        "detail": "pypdf + Microsoft MarkItDown (PDF, Word, Excel, preprints)",
        "pip_packages": ["pypdf>=5.0.0", "markitdown>=0.1.0"],
        "default": True,
        "required": False,
    },
    {
        "id": "scipy",
        "name": "Numerical Computing & Optimization",
        "detail": "SciPy (scientific routines, numerical integration, matrices)",
        "pip_packages": ["scipy>=1.12"],
        "default": False,
        "required": False,
    },
    {
        "id": "plots",
        "name": "Visualization & Plotting",
        "detail": "Matplotlib (phase portraits, function plots, vector fields)",
        "pip_packages": ["matplotlib>=3.8"],
        "default": False,
        "required": False,
    },
    {
        "id": "mcp",
        "name": "Agent MCP Server Protocol",
        "detail": "MCP Python SDK for Claude Code, Codex, and Antigravity stdio integration",
        "pip_packages": ["mcp>=1.2.0"],
        "default": True,
        "required": False,
    },
    {
        "id": "dev",
        "name": "Testing & Verification Suite",
        "detail": "pytest + pytest-cov (test execution and regression suites)",
        "pip_packages": ["pytest>=8.0", "pytest-cov>=5.0"],
        "default": True,
        "required": False,
    },
    {
        "id": "lean",
        "name": "Formal Proof Assistant (Lean 4)",
        "detail": "elan, Lean 4 kernel, Lake, and Mathlib integration (P0 - Provas)",
        "toolchain": "lean",
        "default": False,
        "required": False,
    },
    {
        "id": "julia",
        "name": "High-Performance Toolchain (Julia)",
        "detail": "Julia engine for PDE simulations & high-speed scientific linear algebra",
        "toolchain": "julia",
        "default": False,
        "required": False,
    },
]


def print_banner(title: str) -> None:
    sep = "=" * 68
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


def install_toolchain(tool: str) -> bool:
    os_name = platform.system().lower()
    print(f"\n[*] Installing toolchain: {tool.upper()} on {platform.system()}...")

    if "windows" in os_name:
        ps1_script = ROOT / "scripts" / "install_toolchains.ps1"
        if not ps1_script.exists():
            print("[!] scripts/install_toolchains.ps1 not found.")
            return False
        flag = "-LeanOnly" if tool == "lean" else "-JuliaOnly"
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps1_script), flag]
        res = subprocess.run(cmd)
        return res.returncode == 0
    else:
        sh_script = ROOT / "scripts" / "install_toolchains.sh"
        if not sh_script.exists():
            print("[!] scripts/install_toolchains.sh not found.")
            return False
        cmd = ["bash", str(sh_script)]
        res = subprocess.run(cmd)
        return res.returncode == 0


def run_diagnostics() -> int:
    print_banner("Running AXIOM Diagnostics (axiom doctor)")
    cmd = [sys.executable, "-m", "axiom.cli", "doctor"]
    res = subprocess.run(cmd)
    return res.returncode


def run_custom_checklist(preselected_ids: set[str] | None = None) -> list[str]:
    """Run an interactive checklist allowing the user to toggle components."""
    # Initialize state
    state: dict[str, bool] = {}
    for comp in COMPONENTS:
        cid = comp["id"]
        if preselected_ids is not None:
            state[cid] = cid in preselected_ids or comp.get("required", False)
        else:
            state[cid] = comp["default"]

    is_interactive = sys.stdin.isatty()

    if not is_interactive and preselected_ids is None:
        print("[*] Non-interactive environment detected. Using default checklist selection.")
        return [c["id"] for c in COMPONENTS if state[c["id"]]]

    while True:
        print_banner("Custom Setup Checklist (Personalizado)")
        print("Toggle items by typing numbers separated by space or comma.")
        print("Commands: 'all' to select all, 'min' for minimal, 'done' or ENTER to proceed.\n")

        for idx, comp in enumerate(COMPONENTS, 1):
            cid = comp["id"]
            checked = "[X]" if state[cid] else "[ ]"
            req_tag = " (Obrigatório)" if comp.get("required") else ""
            print(f"  {checked} {idx}. {comp['name']}{req_tag}")
            print(f"       -> {comp['detail']}")

        selected_names = [comp["name"] for comp in COMPONENTS if state[comp["id"]]]
        print(f"\nCurrently selected: {len(selected_names)}/{len(COMPONENTS)} components")

        try:
            choice = input("\nEnter numbers to toggle (or press ENTER to install): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSetup cancelled.")
            sys.exit(130)

        if not choice or choice.lower() in ("done", "install", "ok", "y", "yes"):
            break

        if choice.lower() in ("all", "*"):
            for comp in COMPONENTS:
                state[comp["id"]] = True
            continue

        if choice.lower() == "min":
            for comp in COMPONENTS:
                state[comp["id"]] = comp.get("required", False)
            continue

        # Parse number inputs
        tokens = choice.replace(",", " ").split()
        for tok in tokens:
            if tok.isdigit():
                num = int(tok)
                if 1 <= num <= len(COMPONENTS):
                    comp = COMPONENTS[num - 1]
                    cid = comp["id"]
                    if comp.get("required"):
                        print(f"  [!] Note: {comp['name']} is required by AXIOM core.")
                        state[cid] = True
                    else:
                        state[cid] = not state[cid]
            else:
                # Match by id prefix
                matched = False
                for comp in COMPONENTS:
                    if comp["id"].lower() == tok.lower():
                        if comp.get("required"):
                            state[comp["id"]] = True
                        else:
                            state[comp["id"]] = not state[comp["id"]]
                        matched = True
                        break
                if not matched:
                    print(f"  [!] Unrecognized option: '{tok}'")

    selected = [comp["id"] for comp in COMPONENTS if state[comp["id"]]]
    return selected


def apply_custom_selection(selected_ids: list[str]) -> int:
    """Install packages and toolchains corresponding to chosen components."""
    print_banner("Applying Custom Component Setup")

    pip_pkgs: list[str] = []
    toolchains_to_install: list[str] = []

    for comp in COMPONENTS:
        if comp["id"] in selected_ids:
            if "pip_packages" in comp:
                pip_pkgs.extend(comp["pip_packages"])
            if "toolchain" in comp:
                toolchains_to_install.append(comp["toolchain"])

    # Install Python packages
    if pip_pkgs:
        print(f"[*] Installing {len(pip_pkgs)} Python packages...")
        success = run_pip(["install"] + pip_pkgs)
        if not success:
            print("[!] Warning: Error occurred while installing some Python packages.")

    # Install external toolchains
    for tc in toolchains_to_install:
        tc_ok = install_toolchain(tc)
        if not tc_ok:
            print(f"[!] Warning: Could not complete automated setup for {tc}.")
            print("    Please refer to skills/toolchain-management/SKILL.md.")

    return run_diagnostics()


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
        "--custom",
        "--checklist",
        "-c",
        action="store_true",
        help="Setup environment via interactive checklist (personalizado).",
    )
    group.add_argument(
        "--select",
        type=str,
        help="Comma-separated list of component IDs to install (cas, docs, scipy, plots, mcp, dev, lean, julia).",
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

    if args.select:
        selected_ids = [s.strip().lower() for s in args.select.split(",") if s.strip()]
        return apply_custom_selection(selected_ids)

    if args.custom:
        chosen = run_custom_checklist()
        return apply_custom_selection(chosen)

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
            install_toolchain("lean")
            install_toolchain("julia")

        return run_diagnostics()

    # Interactive menu if run with no arguments on an interactive terminal
    if sys.stdin.isatty() and not any(getattr(args, k) for k in ("min", "full", "custom", "check", "select")):
        print_banner("Interactive Environment Setup")
        print("Choose a setup profile:")
        print("  1) Minimal Setup   (Core CAS: SymPy + mpmath)")
        print("  2) Standard Setup  (Core CAS + Document Extraction with MarkItDown)")
        print("  3) Full Setup      (Everything + Heavy Toolchains Lean 4 / Julia)")
        print("  4) Custom Setup    (Interactive Checklist / Personalizado)")
        print("  5) Check Status    (Run axiom doctor diagnostics)")

        try:
            ans = input("\nSelect profile [1-5] (default: 2): ").strip()
        except (EOFError, KeyboardInterrupt):
            ans = "2"

        if ans == "1":
            return main(["--min"])
        elif ans == "3":
            return main(["--full"])
        elif ans == "4":
            return main(["--custom"])
        elif ans == "5":
            return main(["--check"])

    # Default: Standard setup
    print_banner("Configuring STANDARD Setup")
    success = install_requirements("requirements.txt")
    if not success:
        print("[!] Failed to install standard requirements.")
        return 1
    return run_diagnostics()


if __name__ == "__main__":
    sys.exit(main())
