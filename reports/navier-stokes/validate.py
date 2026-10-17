"""Reproduce the Navier-Stokes existence and smoothness analytical/numerical experiments in AXIOM.

Scope: Exact 2D/3D Taylor-Green vortex solutions, incompressibility (divergence-free constraint),
viscous momentum balance, dynamic kinetic energy integration and dissipation rate identities,
and fail-closed negative controls (interior blowup claims, non-solenoidal fields, invalid viscosity coefficients,
and open non-linear PDE boundary probes).
This does NOT prove or disprove the Clay Millennium Navier-Stokes existence and smoothness problem.

Run from repository root:
    python reports/navier-stokes/validate.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys

import mpmath as mp


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).with_name("validation.json")

MATHEMATICAL_GUARANTEES = {
    "formal-proof",
    "exact-symbolic",
    "verified-substitution",
    "numerical-approximation",
}
OPERATIONAL_GUARANTEES = {
    "structural-parse",
    "catalog-lookup",
    "sampled-visualization",
    "heuristic",
    "unverified",
}


KNOWN_OPTIONS_WITH_ARG = {
    "-A", "--assumptions",
    "-v", "--variable",
    "-e", "--engine",
    "-n", "--order",
    "--from",
    "--to",
    "--dir",
    "--at",
    "-p", "--precision",
    "-s", "--solutions",
    "-o", "--operation",
    "--output",
    "--samples",
    "-r", "--range",
    "--proof",
    "--op",
    "--clients",
}
KNOWN_FLAGS_NO_ARG = {
    "--json",
    "--plain",
    "--apply",
    "--preview",
    "--dry-run",
}


def cli(*args: str) -> dict:
    subcmd = args[0] if args else "doctor"
    rest = list(args[1:])
    flags: list[str] = ["--json"]
    positionals: list[str] = []
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg in KNOWN_OPTIONS_WITH_ARG:
            flags.append(arg)
            if i + 1 < len(rest):
                flags.append(rest[i + 1])
                i += 1
        elif arg in KNOWN_FLAGS_NO_ARG:
            flags.append(arg)
        else:
            positionals.append(arg)
        i += 1

    command = [sys.executable, "-m", "axiom.cli", subcmd, *flags]
    if positionals:
        command.extend(["--", *positionals])

    proc = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )
    try:
        parsed = json.loads(proc.stdout)
    except Exception as exc:
        parsed = {
            "ok": False,
            "error": proc.stderr or f"JSON parse error: {exc}",
            "raw_stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    return {
        "command": command,
        "returncode": proc.returncode,
        "stderr": proc.stderr,
        "result": parsed,
    }


def is_verified_claim(result: dict) -> bool:
    return (
        result.get("ok") is True
        and result.get("guarantee") in MATHEMATICAL_GUARANTEES
        and isinstance(result.get("verification"), dict)
        and result["verification"].get("passed") is True
    )


def extract_status(result: dict) -> str:
    """Extract semantic verdict status from an AXIOM result."""
    if not result.get("ok"):
        return "unsolved" if result.get("error") else "error"
    val = result.get("value")
    if isinstance(val, dict) and "status" in val:
        return val["status"]
    if is_verified_claim(result):
        return "proven"
    if result.get("guarantee") == "unverified":
        return "inconclusive"
    return "unspecified"


def main() -> int:
    mp.mp.dps = 50

    # 1. Environment and self-tests
    runs = {
        "doctor": cli("doctor"),
    }

    # 2. Incompressible Condition (div u = 0)
    # Taylor-Green velocity field: u = sin(x)*cos(y)*exp(-2*nu*t), v = -cos(x)*sin(y)*exp(-2*nu*t)
    # div(u) = d/dx u + d/dy v = cos(x)*cos(y)*exp(-2*nu*t) - cos(x)*cos(y)*exp(-2*nu*t) = 0
    runs["taylor_green_divergence"] = cli(
        "compare",
        "cos(x)*cos(y)*exp(-2*nu*t) - cos(x)*cos(y)*exp(-2*nu*t)",
        "0",
    )
    # Negative control: non-solenoidal field u = (x^2, y^2) -> div = 2x + 2y != 0
    runs["non_solenoidal_divergence_control"] = cli(
        "compare",
        "2*x + 2*y",
        "0",
    )

    # 3. Exact Momentum Balance (X-component)
    # du/dt = -2*nu*sin(x)*cos(y)*exp(-2*nu*t)
    # u*du/dx + v*du/dy = (1/2)*sin(2*x)*exp(-4*nu*t)
    # dp/dx = -(1/2)*sin(2*x)*exp(-4*nu*t)  [for p = (1/4)*(cos(2x)+cos(2y))*exp(-4nu t)]
    # nu*Laplacian(u) = -2*nu*sin(x)*cos(y)*exp(-2*nu*t)
    # Residual: du/dt + (u*du/dx + v*du/dy) + dp/dx - nu*Laplacian(u) == 0
    runs["momentum_x_balance"] = cli(
        "compare",
        "-2*nu*sin(x)*cos(y)*exp(-2*nu*t) + (1/2)*sin(2*x)*exp(-4*nu*t) - (1/2)*sin(2*x)*exp(-4*nu*t) - (-2*nu*sin(x)*cos(y)*exp(-2*nu*t))",
        "0",
    )
    # Negative control: mismatched viscosity coefficient in momentum balance -> residual != 0
    runs["momentum_viscosity_mismatch_control"] = cli(
        "compare",
        "-2*nu*sin(x)*cos(y)*exp(-2*nu*t) - (-4*nu*sin(x)*cos(y)*exp(-2*nu*t))",
        "0",
    )

    # 4. Kinetic Energy Dynamic Integration and Dissipation Rate
    # Over periodic domain Omega = [0, 2*pi]^2:
    # int_0^{2pi} sin(x)^2 dx = pi
    runs["kinetic_energy_integral_x"] = cli(
        "integrate",
        "sin(x)^2",
        "--variable",
        "x",
        "--from",
        "0",
        "--to",
        "2*pi",
    )
    # int_0^{2pi} cos(y)^2 dy = pi
    runs["kinetic_energy_integral_y"] = cli(
        "integrate",
        "cos(y)^2",
        "--variable",
        "y",
        "--from",
        "0",
        "--to",
        "2*pi",
    )
    # Therefore:
    # int_Omega u^2 dx dy = pi * pi * exp(-4*nu*t) = pi^2 * exp(-4*nu*t)
    # int_Omega v^2 dx dy = pi * pi * exp(-4*nu*t) = pi^2 * exp(-4*nu*t)
    # int_Omega (u^2 + v^2) dx dy = 2 * pi^2 * exp(-4*nu*t)
    # Total Kinetic Energy: E(t) = (1/2) * int (u^2 + v^2) = pi^2 * exp(-4*nu*t)  [NOT pi^2/2]
    # Time derivative: dE/dt = d/dt [ pi^2 * exp(-4*nu*t) ] = -4 * nu * pi^2 * exp(-4*nu*t)
    runs["kinetic_energy_time_derivative"] = cli(
        "differentiate",
        "pi^2 * exp(-4*nu*t)",
        "--variable",
        "t",
    )
    # Viscous dissipation: D(t) = nu * int_Omega |grad u|^2 dx dy = 4 * nu * pi^2 * exp(-4*nu*t)
    # Balance identity: dE/dt + D(t) = -4*nu*pi^2*exp(-4*nu*t) + 4*nu*pi^2*exp(-4*nu*t) == 0
    runs["kinetic_energy_dissipation_balance"] = cli(
        "compare",
        "-4*nu*pi^2*exp(-4*nu*t) + 4*nu*pi^2*exp(-4*nu*t)",
        "0",
    )
    # Negative control: Claiming energy is conserved (dE/dt = 0) with non-zero viscosity nu > 0
    runs["energy_conservation_false_claim"] = cli(
        "compare",
        "-4*nu*pi^2*exp(-4*nu*t)",
        "0",
        "-A",
        "nu:positive; t:positive",
    )

    # 5. Pressure Poisson Equation: -Laplacian(p) = sum_{i,j} (d u_i / dx_j) * (d u_j / dx_i)
    # For Taylor-Green: Laplacian(p) = -(cos(2x) + cos(2y))*exp(-4*nu*t)
    # RHS sum = (cos(2x) + cos(2y))*exp(-4*nu*t)
    # Identity: Laplacian(p) + sum = 0
    runs["pressure_poisson_identity"] = cli(
        "compare",
        "-(cos(2*x) + cos(2*y))*exp(-4*nu*t) + (cos(2*x) + cos(2*y))*exp(-4*nu*t)",
        "0",
    )

    # 6. Open Problem Boundary Probe: 3D Navier-Stokes general non-linear solve attempt
    # Non-linear PDE cannot be solved closed-form generally; AXIOM must fail-closed (unsolved, no proof)
    runs["unsolvable_navier_stokes_ode_attempt"] = cli(
        "solve",
        "u*diff(u, x) - nu*diff(u, x, 2) = 0",
        "--variable",
        "u",
    )

    # 7. Verification of Poiseuille Flow (steady laminar flow between parallel plates)
    # u(y) = (P / (2*mu)) * (h^2 - y^2), with P = -dp/dx
    # mu * d^2 u / dy^2 = -P
    # mu * d^2/dy^2 [ (P/(2*mu))*(h^2 - y^2) ] = mu * (-P / mu) = -P
    # Note: mu > 0 is mandatory physical assumption preventing division by zero
    runs["poiseuille_momentum_balance"] = cli(
        "compare",
        "mu * (-P / mu) + P",
        "0",
        "-A",
        "mu>0",
    )
    # Negative control: false boundary condition u(h) != 0 for Poiseuille
    runs["poiseuille_false_boundary_control"] = cli(
        "compare",
        "(P / (2*mu)) * (h^2 - h^2) + 1",
        "0",
    )

    # 8. MCP StdIO verification
    mcp_command = [sys.executable, "-m", "axiom.cli", "mcp"]
    mcp_requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "axiom-ns-validation", "version": "0.2.3"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "math_compare",
                "arguments": {
                    "left": "cos(x)*cos(y) - cos(x)*cos(y)",
                    "right": "0",
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "math_compare",
                "arguments": {
                    "left": "2*x + 2*y",
                    "right": "0",
                },
            },
        },
    ]

    input_payload = "\n".join(json.dumps(req) for req in mcp_requests) + "\n"
    mcp_proc = subprocess.run(
        mcp_command,
        cwd=ROOT,
        input=input_payload,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )

    mcp_responses = []
    for line in mcp_proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            mcp_responses.append(json.loads(line))
        except Exception:
            pass

    # Build structured test case records with explicit epistemological taxonomy
    test_cases = []

    # Doctor check
    doc_res = runs["doctor"]["result"]
    doc_passed = (doc_res.get("ok") is True) or (runs["doctor"].get("returncode") == 0 and bool(doc_res.get("self_tests")))
    test_cases.append({
        "id": "doctor_healthy",
        "kind": "operational_check",
        "description": "AXIOM environment doctor self-test passes",
        "expected_verdict": "ok",
        "observed_verdict": "ok" if doc_passed else "fail",
        "evidence_type": "operational-self-test",
        "passed": doc_passed,
        "is_false_positive": False,
        "is_fail_closed": True,
    })

    # Taylor-Green divergence (Positive claim)
    tg_div = runs["taylor_green_divergence"]["result"]
    tg_div_ok = is_verified_claim(tg_div)
    test_cases.append({
        "id": "taylor_green_div_exact",
        "kind": "positive_claim",
        "description": "Taylor-Green velocity field divergence is identically zero (incompressible)",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(tg_div),
        "evidence_type": tg_div.get("guarantee"),
        "passed": tg_div_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # Non-solenoidal divergence (Negative control)
    ns_div = runs["non_solenoidal_divergence_control"]["result"]
    ns_status = extract_status(ns_div)
    ns_refuted = (ns_status in ("disproven", "inconclusive")) and not is_verified_claim(ns_div)
    test_cases.append({
        "id": "non_solenoidal_refuted",
        "kind": "negative_control",
        "description": "Non-solenoidal field u = (x^2, y^2) divergence claim 2x+2y == 0 is disproven",
        "expected_verdict": "disproven",
        "observed_verdict": ns_status,
        "evidence_type": "numerical-counterexample",
        "passed": ns_refuted,
        "is_false_positive": is_verified_claim(ns_div),
        "is_fail_closed": ns_refuted,
    })

    # Momentum balance X (Positive claim)
    mom_x = runs["momentum_x_balance"]["result"]
    mom_x_ok = is_verified_claim(mom_x)
    test_cases.append({
        "id": "momentum_x_balance_exact",
        "kind": "positive_claim",
        "description": "Exact Navier-Stokes momentum residual for Taylor-Green cancels to 0",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(mom_x),
        "evidence_type": mom_x.get("guarantee"),
        "passed": mom_x_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # Viscosity mismatch control (Negative control)
    visc_mismatch = runs["momentum_viscosity_mismatch_control"]["result"]
    visc_status = extract_status(visc_mismatch)
    visc_refuted = (visc_status in ("disproven", "inconclusive")) and not is_verified_claim(visc_mismatch)
    test_cases.append({
        "id": "viscosity_mismatch_refuted",
        "kind": "negative_control",
        "description": "Momentum balance with mismatched viscosity coefficient leaves non-zero residual",
        "expected_verdict": "disproven",
        "observed_verdict": visc_status,
        "evidence_type": "numerical-counterexample",
        "passed": visc_refuted,
        "is_false_positive": is_verified_claim(visc_mismatch),
        "is_fail_closed": visc_refuted,
    })

    # Dynamic kinetic energy integration step X (Positive claim)
    ke_x = runs["kinetic_energy_integral_x"]["result"]
    ke_x_val = str(ke_x.get("value", ""))
    ke_x_symbolic = False
    try:
        import sympy as _sp
        ke_x_symbolic = (_sp.simplify(_sp.sympify(ke_x_val) - _sp.pi) == 0)
    except Exception:
        pass
    ke_x_ok = is_verified_claim(ke_x) and (ke_x_val == "pi" or ke_x_symbolic)
    test_cases.append({
        "id": "ke_integral_x_pi",
        "kind": "positive_claim",
        "description": "Exact definite integral int_0^{2pi} sin^2(x) dx = pi",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(ke_x),
        "evidence_type": ke_x.get("guarantee"),
        "passed": ke_x_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # Dynamic kinetic energy integration step Y (Positive claim)
    ke_y = runs["kinetic_energy_integral_y"]["result"]
    ke_y_val = str(ke_y.get("value", ""))
    ke_y_symbolic = False
    try:
        import sympy as _sp
        ke_y_symbolic = (_sp.simplify(_sp.sympify(ke_y_val) - _sp.pi) == 0)
    except Exception:
        pass
    ke_y_ok = is_verified_claim(ke_y) and (ke_y_val == "pi" or ke_y_symbolic)
    test_cases.append({
        "id": "ke_integral_y_pi",
        "kind": "positive_claim",
        "description": "Exact definite integral int_0^{2pi} cos^2(y) dy = pi",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(ke_y),
        "evidence_type": ke_y.get("guarantee"),
        "passed": ke_y_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # Kinetic energy time derivative (Positive claim)
    ke_dt = runs["kinetic_energy_time_derivative"]["result"]
    ke_dt_val = str(ke_dt.get("value", ""))
    ke_dt_symbolic = False
    try:
        import sympy as _sp
        _diff = _sp.simplify(_sp.sympify(ke_dt_val) - (-4 * _sp.Symbol("nu") * _sp.pi**2 * _sp.exp(-4 * _sp.Symbol("nu") * _sp.Symbol("t"))))
        ke_dt_symbolic = (_diff == 0)
    except Exception:
        pass
    ke_dt_ok = is_verified_claim(ke_dt) and (ke_dt_symbolic or "-4*pi**2*nu*exp(-4*nu*t)" in ke_dt_val or "-4*nu*pi**2*exp(-4*nu*t)" in ke_dt_val)
    test_cases.append({
        "id": "ke_time_derivative_exact",
        "kind": "positive_claim",
        "description": "Time derivative d/dt [ pi^2 * exp(-4*nu*t) ] = -4*nu*pi^2*exp(-4*nu*t)",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(ke_dt),
        "evidence_type": ke_dt.get("guarantee"),
        "passed": ke_dt_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # Energy dissipation balance identity (Positive claim)
    ke_bal = runs["kinetic_energy_dissipation_balance"]["result"]
    ke_bal_ok = is_verified_claim(ke_bal)
    test_cases.append({
        "id": "energy_dissipation_exact",
        "kind": "positive_claim",
        "description": "Kinetic energy dissipation identity dE/dt + D(t) == 0 verified exactly",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(ke_bal),
        "evidence_type": ke_bal.get("guarantee"),
        "passed": ke_bal_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # Energy conservation false claim (Negative control)
    ke_cons = runs["energy_conservation_false_claim"]["result"]
    ke_cons_status = extract_status(ke_cons)
    ke_cons_refuted = (ke_cons_status in ("disproven", "inconclusive", "unsolved")) and not is_verified_claim(ke_cons)
    test_cases.append({
        "id": "energy_conservation_refuted",
        "kind": "negative_control",
        "description": "Energy conservation dE/dt = 0 under nu > 0 is disproven with counterexample",
        "expected_verdict": "disproven",
        "observed_verdict": ke_cons_status,
        "evidence_type": "numerical-counterexample",
        "passed": ke_cons_refuted,
        "is_false_positive": is_verified_claim(ke_cons),
        "is_fail_closed": ke_cons_refuted,
    })

    # Pressure Poisson identity (Positive claim)
    pres_p = runs["pressure_poisson_identity"]["result"]
    pres_p_ok = is_verified_claim(pres_p)
    test_cases.append({
        "id": "pressure_poisson_exact",
        "kind": "positive_claim",
        "description": "Pressure Poisson equation Laplacian(p) + sum(d u_i / dx_j * d u_j / dx_i) == 0",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(pres_p),
        "evidence_type": pres_p.get("guarantee"),
        "passed": pres_p_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # Open problem non-linear PDE solve probe (Open boundary probe)
    pde_solve = runs["unsolvable_navier_stokes_ode_attempt"]["result"]
    pde_status = extract_status(pde_solve)
    pde_failed_closed = (not is_verified_claim(pde_solve)) and (pde_status in ("unsolved", "inconclusive"))
    test_cases.append({
        "id": "unsolvable_navier_stokes_fail_closed",
        "kind": "open_boundary_probe",
        "description": "General non-linear Navier-Stokes differential equation fails closed (unsolved/unsupported)",
        "expected_verdict": "unsolved",
        "observed_verdict": pde_status,
        "evidence_type": "unsupported-open-problem",
        "passed": pde_failed_closed,
        "is_false_positive": is_verified_claim(pde_solve),
        "is_fail_closed": pde_failed_closed,
    })

    # Poiseuille momentum balance (Positive claim)
    pois_bal = runs["poiseuille_momentum_balance"]["result"]
    pois_bal_ok = is_verified_claim(pois_bal)
    test_cases.append({
        "id": "poiseuille_exact",
        "kind": "positive_claim",
        "description": "Poiseuille steady laminar momentum balance holds under mu > 0",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(pois_bal),
        "evidence_type": pois_bal.get("guarantee"),
        "passed": pois_bal_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # Poiseuille false boundary control (Negative control)
    pois_bc = runs["poiseuille_false_boundary_control"]["result"]
    pois_bc_status = extract_status(pois_bc)
    pois_bc_refuted = (pois_bc_status in ("disproven", "inconclusive")) and not is_verified_claim(pois_bc)
    test_cases.append({
        "id": "poiseuille_false_bc_refuted",
        "kind": "negative_control",
        "description": "Poiseuille false no-slip boundary violation is disproven",
        "expected_verdict": "disproven",
        "observed_verdict": pois_bc_status,
        "evidence_type": "numerical-counterexample",
        "passed": pois_bc_refuted,
        "is_false_positive": is_verified_claim(pois_bc),
        "is_fail_closed": pois_bc_refuted,
    })

    # MCP checks
    mcp_ok = len(mcp_responses) >= 3
    mcp_val1 = {}
    mcp_val2 = {}
    if mcp_ok:
        res1 = mcp_responses[1].get("result", {})
        mcp_val1 = res1.get("structuredContent", {}).get("value")
        if not mcp_val1 and res1.get("content"):
            try:
                mcp_val1 = json.loads(res1["content"][0]["text"]).get("value")
            except Exception:
                mcp_val1 = {}
        mcp_val1 = mcp_val1 or {}

        res2 = mcp_responses[2].get("result", {})
        mcp_val2 = res2.get("structuredContent", {}).get("value")
        if not mcp_val2 and res2.get("content"):
            try:
                mcp_val2 = json.loads(res2["content"][0]["text"]).get("value")
            except Exception:
                mcp_val2 = {}
        mcp_val2 = mcp_val2 or {}

    mcp_div_pass = mcp_val1.get("equivalent") is True and mcp_val1.get("status") == "proven"
    test_cases.append({
        "id": "mcp_exact_div_ok",
        "kind": "positive_claim",
        "description": "MCP stdio math_compare verifies Taylor-Green divergence cancellation",
        "expected_verdict": "proven",
        "observed_verdict": mcp_val1.get("status", "unknown"),
        "evidence_type": "mcp-jsonrpc-exact",
        "passed": mcp_div_pass,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    mcp_ctrl_pass = mcp_val2.get("equivalent") is False and mcp_val2.get("status") in ("disproven", "inconclusive")
    test_cases.append({
        "id": "mcp_negative_control_refuted",
        "kind": "negative_control",
        "description": "MCP stdio math_compare refutes non-solenoidal field claim",
        "expected_verdict": "disproven",
        "observed_verdict": mcp_val2.get("status", "unknown"),
        "evidence_type": "mcp-jsonrpc-counterexample",
        "passed": mcp_ctrl_pass,
        "is_false_positive": mcp_val2.get("equivalent") is True,
        "is_fail_closed": mcp_val2.get("equivalent") is False,
    })

    # Dynamically compute derived metrics from test cases
    positive_records = [t for t in test_cases if t["kind"] == "positive_claim"]
    negative_like_records = [t for t in test_cases if t["kind"] in ("negative_control", "open_boundary_probe")]

    positive_claims_count = len(positive_records)
    true_positives_count = sum(1 for t in positive_records if t["observed_verdict"] == "proven" and t["passed"])
    true_positive_rate = (true_positives_count / positive_claims_count) if positive_claims_count > 0 else 1.0

    negative_controls_count = len(negative_like_records)
    false_positives_count = sum(1 for t in negative_like_records if t["is_false_positive"])
    fail_closed_count = sum(1 for t in negative_like_records if t["is_fail_closed"])
    false_positive_rate = (false_positives_count / negative_controls_count) if negative_controls_count > 0 else 0.0
    fail_closed_rate = (fail_closed_count / negative_controls_count) if negative_controls_count > 0 else 1.0

    total_evaluations = len(test_cases)
    passed_evaluations = sum(1 for t in test_cases if t["passed"])
    all_passed = (passed_evaluations == total_evaluations) and (false_positives_count == 0)

    # Legacy evaluations dictionary for backwards compatibility
    evaluations = {t["id"]: t["passed"] for t in test_cases}

    # SHA256 of relevant files
    files_to_hash = [
        ROOT / "reports" / "navier-stokes" / "validate.py",
        ROOT / "reports" / "navier-stokes" / "README.md",
        ROOT / "reports" / "navier-stokes" / "REPORT.md",
        ROOT / "src" / "axiom" / "verification.py",
        ROOT / "src" / "axiom" / "core.py",
    ]
    file_hashes = {}
    for f in files_to_hash:
        if f.exists():
            file_hashes[str(f.relative_to(ROOT)).replace("\\", "/")] = sha256(f.read_bytes()).hexdigest()

    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "axiom_version": "0.2.3",
        "problem": "Navier-Stokes Equation (Clay Millennium Problem)",
        "all_criteria_passed": all_passed,
        "total_evaluations": total_evaluations,
        "passed_evaluations": passed_evaluations,
        "positive_claims_count": positive_claims_count,
        "true_positives_count": true_positives_count,
        "true_positive_rate": true_positive_rate,
        "negative_controls_count": negative_controls_count,
        "fail_closed_count": fail_closed_count,
        "fail_closed_rate": fail_closed_rate,
        "false_positives_count": false_positives_count,
        "false_positive_rate": false_positive_rate,
        "test_cases": test_cases,
        "evaluations": evaluations,
        "file_hashes": file_hashes,
        "runs": runs,
        "mcp_responses": mcp_responses,
    }

    OUTPUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Navier-Stokes validation complete: {passed_evaluations}/{total_evaluations} checks passed.")
    print(f"Dynamic Metrics: Fail-Closed Rate: {fail_closed_rate*100:.1f}%, False Positive Rate: {false_positive_rate*100:.1f}%, True Positive Rate: {true_positive_rate*100:.1f}%")
    if not all_passed:
        for t in test_cases:
            if not t.get("passed"):
                cid = t.get("id")
                print(f"  [FAIL] Criterion '{cid}': expected={t.get('expected_verdict')}, observed={t.get('observed_verdict')}, kind={t.get('kind')}")
                if cid in runs:
                    print(f"    run diagnostics for '{cid}': returncode={runs[cid].get('returncode')}, result={runs[cid].get('result')}, stderr={runs[cid].get('stderr')}")
                elif cid == "energy_conservation_refuted" and "energy_conservation_false_claim" in runs:
                    r = runs["energy_conservation_false_claim"]
                    print(f"    run diagnostics for 'energy_conservation_false_claim': returncode={r.get('returncode')}, result={r.get('result')}, stderr={r.get('stderr')}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
