"""Reproduce the Riemann Hypothesis analytical/numerical experiments and AXIOM v0.2.0 checks.

Scope: Classical properties of the Riemann zeta function (Euler values at even integers,
trivial zeros, simple pole at s=1 with two-sided vs directional limits, Mellin integral,
functional equation spot-check, truncated Euler product, critical-line numerical probe,
and v0.2.0 negative controls).
This does NOT prove or disprove the Riemann Hypothesis.

Run from repository root:
    python reports/riemann-hypothesis/validate.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from fractions import Fraction
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


def cli(*args: str) -> dict:
    command = [sys.executable, "-m", "axiom.cli", *args, "--json"]
    proc = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=90,
        check=False,
    )
    return {
        "command": command,
        "returncode": proc.returncode,
        "stderr": proc.stderr,
        "result": json.loads(proc.stdout),
    }


def is_verified_claim(result: dict) -> bool:
    return (
        result.get("ok") is True
        and result.get("guarantee") in MATHEMATICAL_GUARANTEES
        and isinstance(result.get("verification"), dict)
        and result["verification"].get("passed") is True
    )


def main() -> int:
    mp.mp.dps = 50

    runs = {
        "doctor": cli("doctor"),
        # 1. Operational state: structural-parse
        "parse_functional_rhs": cli(
            "parse",
            "2^s * pi^(s - 1) * sin(pi*s/2) * gamma(1 - s) * zeta(1 - s)",
        ),
        # 2. Exact special values & trivial zeros
        "zeta_2_exact": cli("evaluate", "zeta(2)"),
        "zeta_4_exact": cli("evaluate", "zeta(4)"),
        "zeta_0_exact": cli("evaluate", "zeta(0)"),
        "zeta_neg1_exact": cli("evaluate", "zeta(-1)"),
        "trivial_zero_neg2": cli("evaluate", "zeta(-2)"),
        "trivial_zero_neg4": cli("evaluate", "zeta(-4)"),
        "compare_basel": cli("compare", "zeta(2)", "pi^2/6"),
        "compare_basel_false": cli("compare", "zeta(2)", "pi^2/8"),
        "verify_constant_equality_probe": cli("verify", "zeta(2) = pi^2/6"),
        # 3. Pole at s = 1: residue vs directional vs two-sided limit (v0.2.0)
        "residue_at_s1": cli("limit", "(s - 1)*zeta(s)", "--variable", "s", "--to", "1"),
        "pole_right_limit": cli("limit", "zeta(s)", "--variable", "s", "--to", "1", "--dir", "+"),
        "pole_left_limit": cli("limit", "zeta(s)", "--variable", "s", "--to", "1", "--dir", "-"),
        "pole_two_sided_limit": cli("limit", "zeta(s)", "--variable", "s", "--to", "1", "--dir", "+-"),
        # 4. Functional equation equivalence check
        "functional_equation_compare": cli(
            "compare",
            "zeta(s)",
            "2^s * pi^(s - 1) * sin(pi*s/2) * gamma(1 - s) * zeta(1 - s)",
        ),
        # 5. Mellin integral representation for s=2 vs interior pole control (v0.2.0)
        "mellin_integral_s2": cli(
            "integrate",
            "x/(exp(x) - 1)",
            "--variable",
            "x",
            "--from",
            "0",
            "--to",
            "oo",
        ),
        "interior_pole_integral_control": cli(
            "integrate",
            "1/x^2",
            "--variable",
            "x",
            "--from",
            "-1",
            "--to",
            "1",
        ),
        # 6. Euler product primes & primorial factorization
        "factorint_30030": cli("number-theory", "factorint", "-n", "30030"),
        "totient_30030": cli("number-theory", "totient", "-n", "30030"),
        "euler_product_p13_exact": cli(
            "evaluate",
            "(1/(1 - 2^(-2)))*(1/(1 - 3^(-2)))*(1/(1 - 5^(-2)))*(1/(1 - 7^(-2)))*(1/(1 - 11^(-2)))*(1/(1 - 13^(-2)))",
        ),
        # 7. Critical line Re(s) = 1/2 numerical probes & solver limitation
        "zeta_half_real": cli("evaluate", "zeta(1/2)", "--precision", "30"),
        "first_nontrivial_zero_residual": cli(
            "evaluate",
            "Abs(zeta(1/2 + 14.134725141734693790457251983562*I))",
            "--precision",
            "30",
        ),
        "solve_zeta_zero_attempt": cli("solve", "zeta(s) = 0", "--variable", "s"),
        # 8. Catalog lookup, visualization & formal Lean controls
        "mathlib_search_prime": cli("search-mathlib", "prime"),
        "mathlib_search_empty": cli("search-mathlib", "nonexistent_riemann_proof_xyz_999"),
        "plot_regularized_zeta": cli(
            "plot",
            "(s - 1)*zeta(s)",
            "--variable",
            "s",
            "--range",
            "1.1:4.0",
            "--points",
            "25",
        ),
        "lean_control_file": cli("prove", "examples/theorems.lean", "--engine", "lean"),
        "lean_tautology_control": cli(
            "prove",
            "theorem fake_rh : 2 + 2 = 2 + 2 := by rfl",
            "--engine",
            "lean",
        ),
    }

    # Test MCP JSON-RPC 2.0 stdio server with v0.2.0 assumptions and zeta tools
    mcp_requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "axiom-riemann-validation", "version": "0.2.0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "math_compare",
                "arguments": {
                    "left": "sqrt(x^2)",
                    "right": "x",
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "math_compare",
                "arguments": {
                    "left": "sqrt(x^2)",
                    "right": "x",
                    "assumptions": {"x": "positive"},
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "math_evaluate",
                "arguments": {
                    "expression": "zeta(2) - pi^2/6",
                },
            },
        },
    ]

    mcp_command = [sys.executable, "-m", "axiom.mcp_server"]
    mcp_proc = subprocess.run(
        mcp_command,
        cwd=ROOT,
        input="".join(json.dumps(req) + "\n" for req in mcp_requests),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=45,
        check=False,
    )
    mcp_responses = [
        json.loads(line) for line in mcp_proc.stdout.splitlines() if line.strip()
    ]
    mcp_by_id = {resp["id"]: resp for resp in mcp_responses if "id" in resp}
    mcp_branch_unassumed = (
        mcp_by_id.get(3, {}).get("result", {}).get("structuredContent", {})
    )
    mcp_branch_positive = (
        mcp_by_id.get(4, {}).get("result", {}).get("structuredContent", {})
    )
    mcp_basel_diff = (
        mcp_by_id.get(5, {}).get("result", {}).get("structuredContent", {})
    )

    # Independent reference calculations using Python's fractions, math, and mpmath
    primes_up_to_13 = [2, 3, 5, 7, 11, 13]
    euler_prod_fraction = Fraction(1, 1)
    for p in primes_up_to_13:
        euler_prod_fraction *= Fraction(1, 1) / (Fraction(1, 1) - Fraction(1, p * p))

    gamma_1 = mp.mpf("14.134725141734693790457251983562")
    mp_zeta_half = mp.zeta(mp.mpf("0.5"))
    mp_first_zero_abs = abs(mp.zeta(mp.mpc("0.5", gamma_1)))
    mp_basel = (mp.pi ** 2) / 6

    doctor = runs["doctor"]["result"]
    lean_available = bool(doctor.get("external_toolchains", {}).get("lean"))

    checks = {
        "doctor_self_tests_pass": doctor.get("ok") is True,
        "parse_uses_structural_parse_guarantee": (
            runs["parse_functional_rhs"]["result"].get("guarantee") == "structural-parse"
            and runs["parse_functional_rhs"]["result"].get("verification", {}).get("passed") is True
        ),
        "zeta_2_exact_verified": (
            is_verified_claim(runs["zeta_2_exact"]["result"])
            and runs["zeta_2_exact"]["result"].get("value") == "pi**2/6"
        ),
        "zeta_4_exact_verified": (
            is_verified_claim(runs["zeta_4_exact"]["result"])
            and runs["zeta_4_exact"]["result"].get("value") == "pi**4/90"
        ),
        "trivial_zeros_verified_zero": (
            is_verified_claim(runs["trivial_zero_neg2"]["result"])
            and runs["trivial_zero_neg2"]["result"].get("value") == "0"
            and is_verified_claim(runs["trivial_zero_neg4"]["result"])
            and runs["trivial_zero_neg4"]["result"].get("value") == "0"
        ),
        "zeta_0_and_neg1_bernoulli_values": (
            runs["zeta_0_exact"]["result"].get("value") == "-1/2"
            and runs["zeta_neg1_exact"]["result"].get("value") == "-1/12"
        ),
        "compare_basel_exact_symbolic": (
            is_verified_claim(runs["compare_basel"]["result"])
            and runs["compare_basel"]["result"].get("guarantee") == "exact-symbolic"
        ),
        "compare_basel_false_refuted": (
            runs["compare_basel_false"]["result"].get("guarantee") == "unverified"
            and runs["compare_basel_false"]["result"].get("verification", {}).get("passed") is False
        ),
        "residue_at_pole_s1_verified": (
            is_verified_claim(runs["residue_at_s1"]["result"])
            and runs["residue_at_s1"]["result"].get("value") == "1"
        ),
        "two_sided_limit_at_pole_rejected_v020": (
            runs["pole_two_sided_limit"]["result"].get("guarantee") == "unverified"
            and runs["pole_two_sided_limit"]["result"]
            .get("verification", {})
            .get("passed")
            is False
        ),
        "functional_equation_spot_checked_numerical": (
            is_verified_claim(runs["functional_equation_compare"]["result"])
            and runs["functional_equation_compare"]["result"].get("guarantee")
            == "numerical-approximation"
        ),
        "mellin_integral_s2_verified": (
            is_verified_claim(runs["mellin_integral_s2"]["result"])
            and runs["mellin_integral_s2"]["result"].get("value") == "pi**2/6"
        ),
        "interior_pole_integral_rejected_v020": (
            runs["interior_pole_integral_control"]["result"].get("guarantee") == "unverified"
            and runs["interior_pole_integral_control"]["result"]
            .get("verification", {})
            .get("passed")
            is False
        ),
        "primorial_30030_factorint_and_totient": (
            is_verified_claim(runs["factorint_30030"]["result"])
            and runs["factorint_30030"]["result"].get("value")
            == {"2": 1, "3": 1, "5": 1, "7": 1, "11": 1, "13": 1}
            and runs["totient_30030"]["result"].get("value") == 5760
            and math.prod(p - 1 for p in primes_up_to_13) == 5760
        ),
        "euler_product_p13_matches_independent_fraction": (
            is_verified_claim(runs["euler_product_p13_exact"]["result"])
            and runs["euler_product_p13_exact"]["result"].get("value")
            == f"{euler_prod_fraction.numerator}/{euler_prod_fraction.denominator}"
        ),
        "zeta_half_nonzero_matches_mpmath": (
            is_verified_claim(runs["zeta_half_real"]["result"])
            and abs(
                float(runs["zeta_half_real"]["result"]["value"]) - float(mp_zeta_half)
            )
            < 1e-14
        ),
        "first_nontrivial_zero_residual_small": (
            is_verified_claim(runs["first_nontrivial_zero_residual"]["result"])
            and float(runs["first_nontrivial_zero_residual"]["result"]["value"]) < 1e-25
            and abs(
                float(runs["first_nontrivial_zero_residual"]["result"]["value"])
                - float(mp_first_zero_abs)
            )
            < 1e-25
        ),
        "solve_zeta_zero_fails_closed": (
            runs["solve_zeta_zero_attempt"]["result"].get("ok") is False
            and runs["solve_zeta_zero_attempt"]["result"].get("guarantee") == "unverified"
        ),
        "mathlib_search_uses_catalog_lookup_guarantee": (
            runs["mathlib_search_prime"]["result"].get("guarantee") == "catalog-lookup"
            and runs["mathlib_search_empty"]["result"].get("guarantee") == "unverified"
            and runs["mathlib_search_empty"]["result"]
            .get("verification", {})
            .get("passed")
            is False
        ),
        "plot_uses_sampled_visualization_guarantee": (
            runs["plot_regularized_zeta"]["result"].get("guarantee")
            == "sampled-visualization"
        ),
        "mcp_branch_cut_refuted_without_assumptions": (
            mcp_branch_unassumed.get("guarantee") == "unverified"
            and mcp_branch_unassumed.get("verification", {}).get("passed") is False
            and mcp_branch_unassumed.get("verification", {})
            .get("data", {})
            .get("counterexample")
            == {"x": "-1"}
        ),
        "mcp_branch_cut_verified_with_positive_assumption": (
            is_verified_claim(mcp_branch_positive)
            and mcp_branch_positive.get("guarantee") == "exact-symbolic"
        ),
        "mcp_basel_diff_zero": (
            is_verified_claim(mcp_basel_diff)
            and mcp_basel_diff.get("value") == "0"
        ),
        "lean_expected_fail_closed": (
            runs["lean_tautology_control"]["result"].get("guarantee") == "unverified"
            and runs["lean_tautology_control"]["result"]
            .get("verification", {})
            .get("passed")
            is False
        ),
    }

    tracked_files = [
        "src/axiom/contract.py",
        "src/axiom/parsing.py",
        "src/axiom/core.py",
        "src/axiom/verification.py",
        "src/axiom/engines/lean_engine.py",
        "src/axiom/engines/sympy_engine.py",
        "src/axiom/mcp_server.py",
        "src/axiom/cli.py",
        "examples/theorems.lean",
    ]

    record = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": (
            "Analytical, number-theoretic, and numerical properties of the Riemann zeta "
            "function (Bombieri Clay exposition) + AXIOM v0.2.0 contract & edge-case validation"
        ),
        "riemann_hypothesis_proven": False,
        "sources": [
            "https://www.claymath.org/millennium/riemann-hypothesis/",
            "https://www.claymath.org/wp-content/uploads/2022/05/riemann.pdf",
        ],
        "source_sha256": {
            path: sha256((ROOT / path).read_bytes()).hexdigest()
            for path in tracked_files
        },
        "independent_checks": {
            "euler_product_p_le_13_s2_fraction": f"{euler_prod_fraction.numerator}/{euler_prod_fraction.denominator}",
            "euler_product_p_le_13_s2_float": float(euler_prod_fraction),
            "basel_pi2_over_6_float": float(mp_basel),
            "euler_product_truncation_error_s2": float(mp_basel - mp.mpf(euler_prod_fraction.numerator) / mp.mpf(euler_prod_fraction.denominator)),
            "mpmath_zeta_half": mp.nstr(mp_zeta_half, 30),
            "mpmath_first_zero_abs_residual": mp.nstr(mp_first_zero_abs, 10),
            "totient_30030_product": math.prod(p - 1 for p in primes_up_to_13),
        },
        "cli_runs": runs,
        "mcp": {
            "command": mcp_command,
            "returncode": mcp_proc.returncode,
            "stderr": mcp_proc.stderr,
            "requests": mcp_requests,
            "responses": mcp_responses,
        },
        "checks": checks,
        "validation_passed": all(checks.values()),
        "formal_verification_available_locally": lean_available,
    }

    OUTPUT.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "validation_passed": record["validation_passed"],
                "checks": checks,
                "formal_verification_available_locally": lean_available,
                "summary_guarantees": {
                    name: {
                        "ok": run["result"].get("ok"),
                        "guarantee": run["result"].get("guarantee"),
                        "verification_passed": (
                            run["result"].get("verification", {}).get("passed")
                            if isinstance(run["result"].get("verification"), dict)
                            else None
                        ),
                    }
                    for name, run in runs.items()
                    if name != "doctor"
                },
            },
            indent=2,
        )
    )
    return 0 if record["validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
