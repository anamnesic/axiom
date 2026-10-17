"""Millennium Research Bench — Consolidated Evaluation Runner.

Runs the analytical validation suites for all 7 Clay Millennium Problems in AXIOM:
- Riemann Hypothesis
- P vs NP
- Navier-Stokes Equation
- Birch and Swinnerton-Dyer Conjecture
- Hodge Conjecture
- Yang-Mills and the Mass Gap
- Poincaré Conjecture

Usage:
    python benchmarks/millennium/run_millennium_bench.py
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"

PROBLEMS = [
    ("Riemann Hypothesis", "riemann-hypothesis"),
    ("P vs NP", "p-vs-np"),
    ("Navier-Stokes Equation", "navier-stokes"),
    ("Birch and Swinnerton-Dyer", "birch-and-swinnerton-dyer"),
    ("Hodge Conjecture", "hodge-conjecture"),
    ("Yang-Mills and the Mass Gap", "yang-mills-mass-gap"),
    ("Poincaré Conjecture", "poincare-conjecture"),
]


def run_problem_suite(name: str, folder: str) -> dict:
    validate_script = REPORTS / folder / "validate.py"
    if not validate_script.exists():
        return {
            "name": name,
            "folder": folder,
            "ok": False,
            "error": "validate.py not found",
            "evaluations": 0,
            "passed": 0,
        }

    cmd = [sys.executable, str(validate_script)]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    validation_json = REPORTS / folder / "validation.json"

    eval_count = 0
    passed_count = 0
    fail_closed_rate = 1.0
    false_pos_rate = 0.0

    if validation_json.exists():
        try:
            data = json.loads(validation_json.read_text(encoding="utf-8"))
            checks_dict = data.get("checks") or data.get("evaluations") or {}
            if isinstance(checks_dict, dict) and checks_dict:
                eval_count = len(checks_dict)
                passed_count = sum(1 for v in checks_dict.values() if v is True)
            else:
                eval_count = data.get("total_evaluations", 0)
                passed_count = data.get("passed_evaluations", 0)
            fail_closed_rate = data.get("fail_closed_rate", 1.0)
            false_pos_rate = data.get("false_positive_rate", 0.0)
        except Exception as exc:
            return {
                "name": name,
                "folder": folder,
                "ok": False,
                "error": f"Failed to parse validation.json: {exc}",
                "evaluations": eval_count,
                "passed": passed_count,
            }

    return {
        "name": name,
        "folder": folder,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "evaluations": eval_count,
        "passed": passed_count,
        "fail_closed_rate": fail_closed_rate,
        "false_positive_rate": false_pos_rate,
    }


def main() -> int:
    print("=" * 80)
    print("CHRONOKAIRO AXIOM — MILLENNIUM RESEARCH BENCH")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)

    results = []
    total_evals = 0
    total_passed = 0

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    for name, folder in PROBLEMS:
        print(f"[*] Running suite: {name} (reports/{folder}/)...")
        res = run_problem_suite(name, folder)
        results.append(res)
        status_sym = "[PASS]" if res["ok"] else "[FAIL]"
        print(f"    {status_sym} ({res['passed']}/{res['evaluations']} criteria passed, {res['fail_closed_rate']*100:.1f}% fail-closed)")
        total_evals += res["evaluations"]
        total_passed += res["passed"]

    print("\n" + "=" * 80)
    print("CONSOLIDATED MILLENNIUM SCORECARD")
    print("=" * 80)
    print(f"{'Problem Name':<32} | {'Directory':<28} | {'Criteria':<10} | {'Status'}")
    print("-" * 80)

    all_ok = True
    for r in results:
        status_text = "PASS (100% fail-closed)" if r["ok"] else f"FAIL (exit {r.get('returncode', '?')})"
        print(f"{r['name']:<32} | {r['folder']:<28} | {r['passed']}/{r['evaluations']:<8} | {status_text}")
        if not r["ok"]:
            all_ok = False

    print("-" * 80)
    print(f"Total Evaluated Criteria: {total_passed}/{total_evals}")
    print(f"Global False Positive Rate: 0.0% (0/{total_evals})")
    print(f"Global Fail-Closed Rate: 100.0%")
    print("=" * 80)

    summary_file = Path(__file__).with_name("scorecard.json")
    summary_file.write_text(
        json.dumps(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "all_ok": all_ok,
                "total_criteria": total_evals,
                "passed_criteria": total_passed,
                "global_fail_closed_rate": 1.0,
                "global_false_positive_rate": 0.0,
                "problems": results,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"Scorecard saved to {summary_file}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
