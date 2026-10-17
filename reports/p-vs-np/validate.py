"""Reproduce the Clay example and local AXIOM environment checks.

This checks finite arithmetic and tool behavior, not P = NP or P != NP.
Run from any directory: python path/to/reports/p-vs-np/validate.py
"""

from datetime import datetime, timezone
from hashlib import sha256
import json
from math import comb
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).with_name("validation.json")


def cli(*args):
    command = [sys.executable, "-m", "axiom.cli", *args, "--json"]
    proc = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", timeout=90, check=False,
    )
    return {
        "command": command,
        "returncode": proc.returncode,
        "stderr": proc.stderr,
        "result": json.loads(proc.stdout),
    }


def verified(result):
    return (
        result.get("ok") is True
        and result.get("guarantee") in {
            "formal-proof", "exact-symbolic", "verified-substitution",
            "numerical-approximation",
        }
        and result.get("verification", {}).get("passed") is True
    )


def main():
    runs = {
        "doctor": cli("doctor"),
        "clay_groups": cli("number-theory", "binomial", "-n", "400", "-k", "100"),
        "candidate_pairs": cli("number-theory", "binomial", "-n", "100", "-k", "2"),
        "negative_root": cli(
            "verify", "x^2 - 5*x + 6 = 0", "--solutions", "4", "--variable", "x",
        ),
        "constant_equality_probe": cli("verify", "2 + 2 = 5"),
        "lean_control": cli("prove", "examples/theorems.lean", "--engine", "lean"),
    }
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "axiom-local-validation", "version": "1"},
        }},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "math_number_theory", "arguments": {
                "operation": "binomial", "n": 400, "k": 100,
            },
        }},
    ]
    mcp_command = [sys.executable, "-m", "axiom.mcp_server"]
    proc = subprocess.run(
        mcp_command, cwd=ROOT,
        input="".join(json.dumps(item) + "\n" for item in requests),
        capture_output=True, text=True, encoding="utf-8", timeout=30, check=False,
    )
    responses = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    indexed = {response["id"]: response for response in responses}
    mcp_result = indexed.get(3, {}).get("result", {}).get("structuredContent", {})
    doctor = runs["doctor"]["result"]
    groups = runs["clay_groups"]["result"]
    pairs = runs["candidate_pairs"]["result"]
    negative = runs["negative_root"]["result"]
    lean = runs["lean_control"]["result"]
    checks = {
        "doctor_self_tests_pass": doctor.get("ok") is True,
        "groups_verified_exact": verified(groups) and groups["guarantee"] == "exact-symbolic",
        "groups_independent_math_comb": groups.get("value") == comb(400, 100),
        "pairs_verified_exact": verified(pairs) and pairs["guarantee"] == "exact-symbolic",
        "pairs_independent_math_comb": pairs.get("value") == comb(100, 2),
        "incorrect_root_refuted": (
            negative.get("guarantee") == "unverified"
            and negative.get("verification", {}).get("passed") is False
            and negative.get("value", {}).get("verified") is False
        ),
        "mcp_initialization": indexed.get(1, {}).get("result", {}).get("serverInfo", {}).get("name") == "axiom",
        "mcp_tool_catalog": len(indexed.get(2, {}).get("result", {}).get("tools", [])) == doctor["mcp_tools_count"],
        "mcp_binomial_verified": verified(mcp_result) and mcp_result.get("value") == comb(400, 100),
        "mcp_exit_success": proc.returncode == 0,
    }
    equality_probe = runs["constant_equality_probe"]["result"]
    checks["false_equality_2plus2_refuted"] = (
        equality_probe.get("guarantee") == "unverified"
        and equality_probe.get("verification", {}).get("passed") is False
    )
    lean_available = bool(doctor.get("external_toolchains", {}).get("lean"))
    checks["lean_control_expected_status"] = (
        verified(lean) and lean.get("guarantee") == "formal-proof"
        if lean_available else
        lean.get("guarantee") == "unverified"
        and lean.get("verification", {}).get("passed") is False
    )

    positive_keys = [
        "groups_verified_exact", "groups_independent_math_comb",
        "pairs_verified_exact", "pairs_independent_math_comb",
        "mcp_binomial_verified"
    ]
    negative_keys = ["incorrect_root_refuted", "false_equality_2plus2_refuted"]
    positive_claims_count = len(positive_keys)
    true_positives_count = sum(1 for k in positive_keys if checks.get(k) is True)
    true_positive_rate = true_positives_count / positive_claims_count if positive_claims_count > 0 else 1.0

    negative_controls_count = len(negative_keys)
    fail_closed_count = sum(1 for k in negative_keys if checks.get(k) is True)
    false_positives_count = negative_controls_count - fail_closed_count
    fail_closed_rate = fail_closed_count / negative_controls_count if negative_controls_count > 0 else 1.0
    false_positive_rate = false_positives_count / negative_controls_count if negative_controls_count > 0 else 0.0

    paths = [
        "src/axiom/contract.py", "src/axiom/parsing.py", "src/axiom/core.py",
        "src/axiom/verification.py", "src/axiom/engines/lean_engine.py",
        "src/axiom/engines/sympy_engine.py", "src/axiom/mcp_server.py",
        "src/axiom/cli.py", "src/axiom/setup_agent.py", "examples/theorems.lean",
    ]
    record = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "axiom_version": "0.2.3",
        "scope": "Clay finite combinatorial example and AXIOM environment only",
        "p_vs_np_proven": False,
        "sources": [
            "https://www.claymath.org/millennium/p-vs-np/",
            "https://www.claymath.org/wp-content/uploads/2022/06/pvsnp.pdf",
        ],
        "source_sha256": {path: sha256((ROOT / path).read_bytes()).hexdigest() for path in paths},
        "cli_runs": runs,
        "mcp": {"command": mcp_command, "returncode": proc.returncode,
                "stderr": proc.stderr, "requests": requests, "responses": responses},
        "independent_checks": {"math_comb_400_100": comb(400, 100), "math_comb_100_2": comb(100, 2)},
        "checks": checks,
        "evaluations": checks,
        "total_evaluations": len(checks),
        "passed_evaluations": sum(1 for v in checks.values() if v is True),
        "positive_claims_count": positive_claims_count,
        "true_positives_count": true_positives_count,
        "true_positive_rate": true_positive_rate,
        "negative_controls_count": negative_controls_count,
        "fail_closed_count": fail_closed_count,
        "fail_closed_rate": fail_closed_rate,
        "false_positives_count": false_positives_count,
        "false_positive_rate": false_positive_rate,
        "validation_passed": all(checks.values()),
        "formal_verification_available": lean_available,
    }
    OUTPUT.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT), "checks": checks,
        "formal_verification_available": lean_available,
        "math_results": {
            name: {"guarantee": run["result"].get("guarantee"),
                   "verification_passed": run["result"].get("verification", {}).get("passed")}
            for name, run in runs.items() if name != "doctor"
        },
        "mcp_result": {"guarantee": mcp_result.get("guarantee"),
                       "verification_passed": mcp_result.get("verification", {}).get("passed")},
    }, indent=2))
    return 0 if record["validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
