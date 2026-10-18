"""Millennium Research Bench — Consolidated Evaluation Runner.

Runs the analytical validation suites for all 7 Clay Millennium Problems in AXIOM:
- Riemann Hypothesis
- P vs NP
- Navier-Stokes Equation
- Birch and Swinnerton-Dyer Conjecture
- Hodge Conjecture
- Yang-Mills and the Mass Gap
- Poincaré Conjecture

All metrics (fail_closed_rate, false_positive_rate, true_positive_rate) are dynamically
computed from structured test counts rather than hardcoded constants.

Usage:
    python benchmarks/millennium/run_millennium_bench.py
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


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
            "positive_claims_count": 0,
            "true_positives_count": 0,
            "negative_controls_count": 0,
            "fail_closed_count": 0,
            "false_positives_count": 0,
            "fail_closed_rate": 0.0,
            "false_positive_rate": 0.0,
            "true_positive_rate": 0.0,
        }

    repo_validation_json = REPORTS / folder / "validation.json"
    temp_dir = tempfile.mkdtemp(prefix=f"axiom_bench_{folder}_")
    isolated_validation_json = Path(temp_dir) / "validation.json"

    env = os.environ.copy()
    env["AXIOM_VALIDATION_OUT"] = str(isolated_validation_json)

    start_time = time.time()
    cmd = [sys.executable, str(validate_script)]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False, env=env)

    target_json = isolated_validation_json

    eval_count = 0
    passed_count = 0
    pos_count = 0
    tp_count = 0
    neg_count = 0
    fc_count = 0
    fp_count = 0
    fail_closed_rate = 1.0
    false_pos_rate = 0.0
    true_pos_rate = 1.0

    failed_criteria: list[str] = []
    if not target_json.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {
            "name": name,
            "folder": folder,
            "ok": False,
            "returncode": proc.returncode,
            "error": "validation.json was not generated in isolated directory",
            "evaluations": 0,
            "passed": 0,
            "positive_claims_count": 0,
            "true_positives_count": 0,
            "negative_controls_count": 0,
            "fail_closed_count": 0,
            "false_positives_count": 0,
            "fail_closed_rate": 0.0,
            "false_positive_rate": 0.0,
            "true_positive_rate": 0.0,
            "failed_criteria": ["missing_fresh_validation_json"],
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    try:
        mtime = target_json.stat().st_mtime
        if mtime < start_time - 1.0:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "name": name,
                "folder": folder,
                "ok": False,
                "returncode": proc.returncode,
                "error": f"validation.json is stale (mtime {mtime} < start_time {start_time})",
                "evaluations": 0,
                "passed": 0,
                "positive_claims_count": 0,
                "true_positives_count": 0,
                "negative_controls_count": 0,
                "fail_closed_count": 0,
                "false_positives_count": 0,
                "fail_closed_rate": 0.0,
                "false_positive_rate": 0.0,
                "true_positive_rate": 0.0,
                "failed_criteria": ["stale_mtime_validation_json"],
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
    except Exception:
        pass

    try:
        raw_text = target_json.read_text(encoding="utf-8")
        data = json.loads(raw_text)
        if target_json == isolated_validation_json:
            try:
                repo_validation_json.write_text(raw_text, encoding="utf-8")
            except Exception:
                pass
        checks_dict = data.get("evaluations") or data.get("checks") or {}
        if isinstance(checks_dict, dict) and checks_dict:
            eval_count = len(checks_dict)
            passed_count = sum(1 for v in checks_dict.values() if v is True)
            failed_criteria = [k for k, v in checks_dict.items() if not v]
        else:
            eval_count = data.get("total_evaluations", 0)
            passed_count = data.get("passed_evaluations", 0)
            if isinstance(data.get("test_cases"), list):
                failed_criteria = [t.get("id", "unknown") for t in data["test_cases"] if not t.get("passed")]

        pos_count = data.get("positive_claims_count", 0)
        tp_count = data.get("true_positives_count", 0)
        neg_count = data.get("negative_controls_count", 0)
        fc_count = data.get("fail_closed_count", 0)
        fp_count = data.get("false_positives_count", 0)

        fail_closed_rate = data.get("fail_closed_rate", (fc_count / neg_count) if neg_count > 0 else 1.0)
        false_pos_rate = data.get("false_positive_rate", (fp_count / neg_count) if neg_count > 0 else 0.0)
        true_pos_rate = data.get("true_positive_rate", (tp_count / pos_count) if pos_count > 0 else 1.0)
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {
            "name": name,
            "folder": folder,
            "ok": False,
            "error": f"Failed to parse validation.json: {exc}",
            "evaluations": eval_count,
            "passed": passed_count,
            "positive_claims_count": pos_count,
            "true_positives_count": tp_count,
            "negative_controls_count": neg_count,
            "fail_closed_count": fc_count,
            "false_positives_count": fp_count,
            "fail_closed_rate": fail_closed_rate,
            "false_positive_rate": false_pos_rate,
            "true_positive_rate": true_pos_rate,
            "failed_criteria": failed_criteria,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }

    shutil.rmtree(temp_dir, ignore_errors=True)

    if eval_count == 0:
        failed_criteria.append("empty_evaluation_suite")

    suite_ok = (
        (proc.returncode == 0)
        and (eval_count > 0)
        and (passed_count == eval_count)
        and (fp_count == 0)
    )

    return {
        "name": name,
        "folder": folder,
        "ok": suite_ok,
        "returncode": proc.returncode,
        "evaluations": eval_count,
        "passed": passed_count,
        "positive_claims_count": pos_count,
        "true_positives_count": tp_count,
        "negative_controls_count": neg_count,
        "fail_closed_count": fc_count,
        "false_positives_count": fp_count,
        "fail_closed_rate": fail_closed_rate,
        "false_positive_rate": false_pos_rate,
        "true_positive_rate": true_pos_rate,
        "failed_criteria": failed_criteria,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main() -> int:
    print("=" * 80)
    print("CHRONOKAIRO AXIOM — MILLENNIUM RESEARCH BENCH")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)

    results = []
    total_evals = 0
    total_passed = 0
    global_pos_claims = 0
    global_true_positives = 0
    global_neg_controls = 0
    global_fail_closed = 0
    global_false_positives = 0

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
        print(f"    {status_sym} ({res['passed']}/{res['evaluations']} criteria passed, {res['fail_closed_rate']*100:.1f}% fail-closed, {res['false_positive_rate']*100:.1f}% FP)")
        if not res["ok"]:
            if res.get("failed_criteria"):
                print(f"    [!] Failed criteria: {', '.join(res['failed_criteria'])}")
            if res.get("stdout"):
                for line in res["stdout"].strip().splitlines()[-10:]:
                    print(f"        {line}")
            if res.get("stderr") and res["stderr"].strip():
                for line in res["stderr"].strip().splitlines()[-5:]:
                    print(f"        [STDERR] {line}")
        total_evals += res["evaluations"]
        total_passed += res["passed"]
        global_pos_claims += res["positive_claims_count"]
        global_true_positives += res["true_positives_count"]
        global_neg_controls += res["negative_controls_count"]
        global_fail_closed += res["fail_closed_count"]
        global_false_positives += res["false_positives_count"]

    global_fail_closed_rate = (global_fail_closed / global_neg_controls) if global_neg_controls > 0 else 1.0
    global_false_positive_rate = (global_false_positives / global_neg_controls) if global_neg_controls > 0 else 0.0
    global_true_positive_rate = (global_true_positives / global_pos_claims) if global_pos_claims > 0 else 1.0

    print("\n" + "=" * 80)
    print("CONSOLIDATED MILLENNIUM SCORECARD")
    print("=" * 80)
    print(f"{'Problem Name':<30} | {'Directory':<26} | {'Criteria':<8} | {'FC Rate':<8} | {'Status'}")
    print("-" * 80)

    all_ok = True
    for r in results:
        status_text = "PASS" if r["ok"] else f"FAIL (exit {r.get('returncode', '?')})"
        print(f"{r['name']:<30} | {r['folder']:<26} | {r['passed']}/{r['evaluations']:<6} | {r['fail_closed_rate']*100:>5.1f}% | {status_text}")
        if not r["ok"]:
            all_ok = False

    print("-" * 80)
    print(f"Total Evaluated Criteria: {total_passed}/{total_evals}")
    print(f"Global Positive Claims: {global_true_positives}/{global_pos_claims} ({global_true_positive_rate*100:.1f}% true positive rate)")
    print(f"Global Negative Controls: {global_fail_closed}/{global_neg_controls} ({global_fail_closed_rate*100:.1f}% fail-closed rate)")
    print(f"Global False Positive Rate: {global_false_positive_rate*100:.1f}% ({global_false_positives}/{global_neg_controls})")
    print("=" * 80)

    summary_file = Path(__file__).with_name("scorecard.json")
    summary_file.write_text(
        json.dumps(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "all_ok": all_ok,
                "total_criteria": total_evals,
                "passed_criteria": total_passed,
                "global_positive_claims": global_pos_claims,
                "global_true_positives": global_true_positives,
                "global_true_positive_rate": global_true_positive_rate,
                "global_negative_controls": global_neg_controls,
                "global_fail_closed_count": global_fail_closed,
                "global_fail_closed_rate": global_fail_closed_rate,
                "global_false_positives_count": global_false_positives,
                "global_false_positive_rate": global_false_positive_rate,
                "problems": results,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"Scorecard saved to {summary_file}")
    return 0 if (all_ok and global_false_positives == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
