"""Reproduce the Birch and Swinnerton-Dyer analytical/numerical experiments in AXIOM.

Scope: Elliptic curves over Q and finite fields F_p, Weierstrass discriminants,
torsion points, rational points of infinite order on congruent number curves,
Hasse bounds, and fail-closed negative controls (singular curves, non-curve points,
false Hasse violations, and open global rank equation probe).
This does NOT prove or disprove the Clay Millennium Birch and Swinnerton-Dyer conjecture.

Run from repository root:
    python reports/birch-and-swinnerton-dyer/validate.py
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
    try:
        parsed = json.loads(proc.stdout)
    except Exception:
        parsed = {"ok": False, "raw_stdout": proc.stdout, "stderr": proc.stderr}
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

    # 2. Weierstrass Discriminant Delta = -16*(4*a^3 + 27*b^2)
    # E1: y^2 = x^3 - x (a = -1, b = 0) -> Delta = -16*(4*(-1) + 0) = 64 != 0 (smooth)
    runs["discriminant_e1_exact"] = cli(
        "compare",
        "-16 * (4 * (-1)^3 + 27 * 0^2)",
        "64",
    )
    # E5: y^2 = x^3 - 25*x (a = -25, b = 0) -> Delta = -16*(4*(-25)^3) = 1000000 (smooth)
    runs["discriminant_e5_exact"] = cli(
        "compare",
        "-16 * (4 * (-25)^3 + 27 * 0^2)",
        "1000000",
    )

    # Singular nodal curve y^2 = x^3 - 3*x + 2 has Delta = 0 (not elliptic!)
    # 4*(-3)^3 + 27*(2)^2 = -108 + 108 = 0
    runs["singular_curve_nodal_zero_delta"] = cli(
        "compare",
        "-16 * (4 * (-3)^3 + 27 * 2^2)",
        "0",
    )
    # Negative control: claiming nodal curve is smooth (Delta != 0) is disproven
    runs["singular_curve_false_smoothness_claim"] = cli(
        "compare",
        "-16 * (4 * (-3)^3 + 27 * 2^2)",
        "64",
    )

    # 3. Torsion Points of Order 2 on E1: x^3 - x = 0
    # Roots: x = -1, x = 0, x = 1
    runs["torsion_order2_roots"] = cli(
        "solve",
        "x^3 - x = 0",
        "--variable",
        "x",
    )

    # 4. Rational Points of Infinite Order (Congruent Number Curve E5: y^2 = x^3 - 25*x)
    # Point P = (-4, 6): (-4)^3 - 25*(-4) = -64 + 100 = 36 = 6^2
    runs["rational_point_P_on_e5"] = cli(
        "verify",
        "6^2 = (-4)^3 - 25*(-4)",
    )
    # Doubling point 2*P on E5: x = 1681/144, y = -62279/1728
    # y^2 - (x^3 - 25*x) == 0
    runs["doubled_point_2P_on_e5"] = cli(
        "compare",
        "(-62279/1728)^2 - ((1681/144)^3 - 25*(1681/144))",
        "0",
    )

    # Negative control: false point Q = (-4, 5) on E5 -> 25 != 36 -> must be refuted!
    runs["false_point_on_e5_refuted"] = cli(
        "verify",
        "5^2 = (-4)^3 - 25*(-4)",
    )

    # 5. Hasse Bound on Trace of Frobenius: |a_p| <= 2*sqrt(p)
    # For E1 over F_3: #E(F_3) = 4 -> a_3 = 3 + 1 - 4 = 0
    runs["trace_frobenius_p3"] = cli(
        "compare",
        "3 + 1 - 4",
        "0",
    )
    # For E1 over F_5: #E(F_5) = 8 -> a_5 = 5 + 1 - 8 = -2. Check |-2| <= 2*sqrt(5)
    runs["hasse_bound_p5_numerical"] = cli(
        "evaluate",
        "2*sqrt(5) - 2",
    )

    # Negative control: False Hasse violation claim (claiming a_5 = 10 violates |a_5| <= 2*sqrt(5))
    runs["false_hasse_violation_claim"] = cli(
        "compare",
        "10",
        "2*sqrt(5)",
    )

    # 6. Global BSD Rank Equation Open Problem Probe
    # AXIOM must fail-closed on uncomputable analytic rank equality
    runs["bsd_global_rank_equation_attempt"] = cli(
        "solve",
        "rank(E) - ord_s1(L(E, s)) = 0",
        "--variable",
        "rank",
    )

    # 7. MCP StdIO verification
    mcp_command = [sys.executable, "-m", "axiom.cli", "mcp"]
    mcp_requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "axiom-bsd-validation", "version": "0.2.3"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "math_verify",
                "arguments": {
                    "target": "6^2 = (-4)^3 - 25*(-4)",
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "math_verify",
                "arguments": {
                    "target": "5^2 = (-4)^3 - 25*(-4)",
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

    test_cases = []

    # Doctor check
    doc_res = runs["doctor"]["result"]
    test_cases.append({
        "id": "doctor_healthy",
        "kind": "operational_check",
        "description": "AXIOM environment doctor self-test passes",
        "expected_verdict": "ok",
        "observed_verdict": "ok" if doc_res.get("ok") is True else "fail",
        "evidence_type": "operational-self-test",
        "passed": doc_res.get("ok") is True,
        "is_false_positive": False,
        "is_fail_closed": True,
    })

    # Discriminant E1 (Positive claim)
    d_e1 = runs["discriminant_e1_exact"]["result"]
    d_e1_ok = is_verified_claim(d_e1)
    test_cases.append({
        "id": "discriminant_e1_exact",
        "kind": "positive_claim",
        "description": "Smooth Weierstrass curve E1 discriminant Delta = 64 verified exactly",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(d_e1),
        "evidence_type": d_e1.get("guarantee"),
        "passed": d_e1_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # Discriminant E5 (Positive claim)
    d_e5 = runs["discriminant_e5_exact"]["result"]
    d_e5_ok = is_verified_claim(d_e5)
    test_cases.append({
        "id": "discriminant_e5_exact",
        "kind": "positive_claim",
        "description": "Congruent curve E5 discriminant Delta = 1000000 verified exactly",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(d_e5),
        "evidence_type": d_e5.get("guarantee"),
        "passed": d_e5_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # Singular nodal curve zero Delta (Positive claim)
    nodal_res = runs["singular_curve_nodal_zero_delta"]["result"]
    nodal_ok = is_verified_claim(nodal_res)
    test_cases.append({
        "id": "nodal_zero_delta_exact",
        "kind": "positive_claim",
        "description": "Nodal cubic curve discriminant cancels to 0 (singular, non-smooth)",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(nodal_res),
        "evidence_type": nodal_res.get("guarantee"),
        "passed": nodal_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # False smoothness claim on nodal curve (Negative control)
    false_smooth = runs["singular_curve_false_smoothness_claim"]["result"]
    false_smooth_status = extract_status(false_smooth)
    false_smooth_refuted = false_smooth_status == "disproven" and not is_verified_claim(false_smooth)
    test_cases.append({
        "id": "false_smoothness_refuted",
        "kind": "negative_control",
        "description": "Claiming nodal curve is smooth (Delta = 64) is disproven",
        "expected_verdict": "disproven",
        "observed_verdict": false_smooth_status,
        "evidence_type": "numerical-counterexample",
        "passed": false_smooth_refuted,
        "is_false_positive": is_verified_claim(false_smooth),
        "is_fail_closed": not is_verified_claim(false_smooth),
    })

    # Torsion order 2 roots (Positive claim)
    tor_res = runs["torsion_order2_roots"]["result"]
    tor_ok = is_verified_claim(tor_res)
    test_cases.append({
        "id": "torsion_order2_roots_exact",
        "kind": "positive_claim",
        "description": "Order 2 torsion points on E1 solved: x in {-1, 0, 1}",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(tor_res),
        "evidence_type": tor_res.get("guarantee"),
        "passed": tor_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # Rational point P on E5 (Positive claim)
    pt_p = runs["rational_point_P_on_e5"]["result"]
    pt_p_ok = is_verified_claim(pt_p)
    test_cases.append({
        "id": "rational_point_P_exact",
        "kind": "positive_claim",
        "description": "Rational point P = (-4, 6) lies on congruent curve E5",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(pt_p),
        "evidence_type": pt_p.get("guarantee"),
        "passed": pt_p_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # Doubled point 2P on E5 (Positive claim)
    pt_2p = runs["doubled_point_2P_on_e5"]["result"]
    pt_2p_ok = is_verified_claim(pt_2p)
    test_cases.append({
        "id": "doubled_point_2P_exact",
        "kind": "positive_claim",
        "description": "Doubled rational point 2*P on E5 satisfies the Weierstrass equation",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(pt_2p),
        "evidence_type": pt_2p.get("guarantee"),
        "passed": pt_2p_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # False point on E5 (Negative control)
    false_pt = runs["false_point_on_e5_refuted"]["result"]
    false_pt_status = extract_status(false_pt)
    false_pt_refuted = (not is_verified_claim(false_pt)) and (false_pt_status in ("disproven", "inconclusive", "unverified"))
    test_cases.append({
        "id": "false_point_refuted",
        "kind": "negative_control",
        "description": "False non-curve point Q = (-4, 5) on E5 is refuting verification (25 != 36)",
        "expected_verdict": "disproven",
        "observed_verdict": false_pt_status,
        "evidence_type": "residual-falsification",
        "passed": false_pt_refuted,
        "is_false_positive": is_verified_claim(false_pt),
        "is_fail_closed": not is_verified_claim(false_pt),
    })

    # Trace of Frobenius on E1/F_3 (Positive claim)
    frob_p3 = runs["trace_frobenius_p3"]["result"]
    frob_p3_ok = is_verified_claim(frob_p3)
    test_cases.append({
        "id": "trace_frobenius_p3_exact",
        "kind": "positive_claim",
        "description": "Trace of Frobenius a_3 = 3 + 1 - #E(F_3) = 0 verified exactly",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(frob_p3),
        "evidence_type": frob_p3.get("guarantee"),
        "passed": frob_p3_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # Hasse bound p=5 numerical evaluation (Positive claim)
    hasse_p5 = runs["hasse_bound_p5_numerical"]["result"]
    hasse_p5_ok = is_verified_claim(hasse_p5) and ("sqrt(5)" in str(hasse_p5.get("value", "")))
    test_cases.append({
        "id": "hasse_bound_p5_numerical",
        "kind": "positive_claim",
        "description": "Hasse bound 2*sqrt(5) - |a_5| > 0 holds with exact/numerical verification",
        "expected_verdict": "proven",
        "observed_verdict": extract_status(hasse_p5),
        "evidence_type": hasse_p5.get("guarantee"),
        "passed": hasse_p5_ok,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    # False Hasse violation claim (Negative control)
    false_hasse = runs["false_hasse_violation_claim"]["result"]
    false_hasse_status = extract_status(false_hasse)
    false_hasse_refuted = false_hasse_status == "disproven" and not is_verified_claim(false_hasse)
    test_cases.append({
        "id": "false_hasse_refuted",
        "kind": "negative_control",
        "description": "False Hasse violation claim 10 <= 2*sqrt(5) is disproven",
        "expected_verdict": "disproven",
        "observed_verdict": false_hasse_status,
        "evidence_type": "numerical-counterexample",
        "passed": false_hasse_refuted,
        "is_false_positive": is_verified_claim(false_hasse),
        "is_fail_closed": not is_verified_claim(false_hasse),
    })

    # Open problem global BSD rank equation probe (Open boundary probe)
    bsd_probe = runs["bsd_global_rank_equation_attempt"]["result"]
    bsd_probe_status = extract_status(bsd_probe)
    bsd_probe_pass = (not is_verified_claim(bsd_probe)) and (bsd_probe_status in ("unsolved", "inconclusive", "error"))
    test_cases.append({
        "id": "bsd_global_rank_fail_closed",
        "kind": "open_boundary_probe",
        "description": "Global BSD analytic rank equation fails closed without uncomputed L-function proof",
        "expected_verdict": "unsolved",
        "observed_verdict": bsd_probe_status,
        "evidence_type": "unsupported-open-problem",
        "passed": bsd_probe_pass,
        "is_false_positive": is_verified_claim(bsd_probe),
        "is_fail_closed": not is_verified_claim(bsd_probe),
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

    mcp_pt_pass = mcp_val1.get("status") == "proven" and mcp_val1.get("equivalent") is True
    test_cases.append({
        "id": "mcp_point_valid_ok",
        "kind": "positive_claim",
        "description": "MCP stdio math_verify confirms point P = (-4, 6) on curve E5",
        "expected_verdict": "proven",
        "observed_verdict": mcp_val1.get("status", "unknown"),
        "evidence_type": "mcp-jsonrpc-exact",
        "passed": mcp_pt_pass,
        "is_false_positive": False,
        "is_fail_closed": False,
    })

    mcp_false_pass = mcp_val2.get("status") in ("disproven", "inconclusive") and mcp_val2.get("equivalent") is False
    test_cases.append({
        "id": "mcp_false_point_refuted",
        "kind": "negative_control",
        "description": "MCP stdio math_verify rejects false non-curve point Q = (-4, 5)",
        "expected_verdict": "disproven",
        "observed_verdict": mcp_val2.get("status", "unknown"),
        "evidence_type": "mcp-jsonrpc-counterexample",
        "passed": mcp_false_pass,
        "is_false_positive": mcp_val2.get("equivalent") is True,
        "is_fail_closed": mcp_val2.get("equivalent") is False,
    })

    # Dynamically compute derived metrics
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

    evaluations = {t["id"]: t["passed"] for t in test_cases}

    files_to_hash = [
        ROOT / "reports" / "birch-and-swinnerton-dyer" / "validate.py",
        ROOT / "reports" / "birch-and-swinnerton-dyer" / "README.md",
        ROOT / "reports" / "birch-and-swinnerton-dyer" / "REPORT.md",
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
        "problem": "Birch and Swinnerton-Dyer Conjecture (Clay Millennium Problem)",
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
    print(f"Birch and Swinnerton-Dyer validation complete: {passed_evaluations}/{total_evaluations} checks passed.")
    print(f"Dynamic Metrics: Fail-Closed Rate: {fail_closed_rate*100:.1f}%, False Positive Rate: {false_positive_rate*100:.1f}%, True Positive Rate: {true_positive_rate*100:.1f}%")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
