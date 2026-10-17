"""Agent onboarding (``axiom setup``) and diagnostics (``axiom doctor``).

Inspired by ``npx rea-agents setup`` in REA:

* ``axiom doctor`` checks the host environment, registered engines, optional
  scientific/formal toolchains, and runs a live verification self-test.
* ``axiom setup`` generates or installs the AXIOM MCP server entry for popular
  MCP clients (Claude Code, Cursor, Gemini CLI, Codex) with automatic backup of
  any existing configuration file.
"""

from __future__ import annotations

import importlib.metadata
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from axiom.core import Axiom
from axiom.mcp_server import TOOL_DEFINITIONS


def mcp_server_entry(python_executable: str | None = None) -> dict[str, Any]:
    """Return the standard MCP server entry for AXIOM."""
    exe = python_executable or sys.executable
    return {
        "command": exe,
        "args": ["-m", "axiom.mcp_server"],
    }


def client_config_paths(home: Path | None = None) -> dict[str, Path]:
    """Return default MCP configuration file paths for supported AI agents."""
    base = home or Path.home()
    return {
        "claude-code": base / ".claude.json",
        "cursor": base / ".cursor" / "mcp.json",
        "gemini": base / ".gemini" / "settings.json",
        "codex": base / ".codex" / "mcp.json",
    }


def configure_clients(
    *,
    clients: list[str] | None = None,
    apply: bool = False,
    home: Path | None = None,
    python_executable: str | None = None,
) -> dict[str, Any]:
    """Inspect or update MCP client config files with the ``axiom`` server."""
    paths = client_config_paths(home=home)
    selected = (
        list(paths.keys())
        if not clients or "all" in clients
        else [c.lower().strip() for c in clients]
    )
    server_cfg = mcp_server_entry(python_executable=python_executable)
    actions: list[dict[str, Any]] = []

    for name in selected:
        if name not in paths:
            actions.append(
                {
                    "client": name,
                    "status": "unsupported",
                    "detail": f"unknown client '{name}' (supported: {', '.join(paths)})",
                }
            )
            continue

        cfg_path = paths[name]
        existing_exists = cfg_path.exists()
        backup_path: str | None = None

        if not apply:
            actions.append(
                {
                    "client": name,
                    "config_path": str(cfg_path),
                    "exists": existing_exists,
                    "status": "dry-run",
                    "proposed_mcpServers_axiom": server_cfg,
                }
            )
            continue

        data: dict[str, Any] = {}
        if existing_exists:
            try:
                raw_text = cfg_path.read_text(encoding="utf-8")
                if raw_text.strip():
                    data = json.loads(raw_text)
            except Exception as exc:
                actions.append(
                    {
                        "client": name,
                        "config_path": str(cfg_path),
                        "status": "error",
                        "detail": f"failed to parse existing JSON config: {exc}",
                    }
                )
                continue
            bak = cfg_path.with_suffix(cfg_path.suffix + ".axiom.bak")
            shutil.copy2(cfg_path, bak)
            backup_path = str(bak)

        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        mcp_servers = data.setdefault("mcpServers", {})
        mcp_servers["axiom"] = server_cfg
        cfg_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        actions.append(
            {
                "client": name,
                "config_path": str(cfg_path),
                "backup_path": backup_path,
                "status": "configured",
                "mcpServers_axiom": server_cfg,
            }
        )

    return {
        "applied": apply,
        "mcp_server": {"axiom": server_cfg},
        "clients": actions,
    }


def _pkg_version(pkg: str) -> str | None:
    try:
        return importlib.metadata.version(pkg)
    except importlib.metadata.PackageNotFoundError:
        return None


def run_doctor(axiom: Axiom | None = None) -> dict[str, Any]:
    """Run environment, engine, and verification self-tests."""
    ax = axiom or Axiom()

    packages = {
        pkg: _pkg_version(pkg)
        for pkg in ("sympy", "mpmath", "scipy", "matplotlib", "mcp", "pytest")
    }
    binaries = {
        bin_name: shutil.which(bin_name)
        for bin_name in ("lean", "lake", "sage", "julia")
    }
    # Also check ~/.elan/bin for lean/lake
    elan_bin = Path.home() / ".elan" / "bin"
    for b in ("lean", "lake"):
        if not binaries[b]:
            for cand in (elan_bin / b, elan_bin / f"{b}.exe"):
                if cand.exists():
                    binaries[b] = str(cand)
                    break

    engines_info = [
        {
            "name": info.name,
            "version": info.version,
            "capabilities": list(info.capabilities),
        }
        for info in ax.registry.list_engines()
    ]

    # Live verification self-checks
    checks = {
        "algebra_solve": ax.solve("x^2 - 5*x + 6 = 0").verified,
        "calculus_integrate": ax.integrate("sin(x)^2", variable="x").verified,
        "linear_algebra_eigen": ax.matrix("[[2, 0], [0, 3]]", operation="eigen").verified,
        "ode_dsolve": ax.ode("diff(y(x), x) - y(x) = 0").verified,
        "number_theory_factorint": ax.number_theory("factorint", n=360).verified,
        "tensor_levi_civita": ax.tensor("polar").verified,
        "mathlib_search": ax.search_mathlib("binomial square").verified,
    }
    all_passed = all(checks.values())

    return {
        "ok": all_passed,
        "python": sys.version.split()[0],
        "mcp_tools_count": len(TOOL_DEFINITIONS),
        "packages": packages,
        "external_toolchains": binaries,
        "engines": engines_info,
        "self_tests": checks,
    }
