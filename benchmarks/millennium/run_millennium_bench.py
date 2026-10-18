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


def _format_rate(rate: float | None) -> str:
    if rate is None:
        return "N/A"
    return f"{rate * 100:.1f}%"


def evaluate_validation_report(
    data: dict, proc_stdout: str = "ok", returncode: int = 0
) -> dict:
    failed_criteria: list[str] = []

    test_cases = data.get("test_cases")
    if isinstance(test_cases, list) and len(test_cases) > 0:
        raw_eval_count = len(test_cases)
        raw_passed_count = sum(1 for t in test_cases if t.get("passed"))
        failed_criteria.extend([t.get("id", "unknown") for t in test_cases if not t.get("passed")])

        raw_pos = [t for t in test_cases if t.get("kind") == "positive_claim"]
        raw_pos_count = len(raw_pos)
        raw_tp_count = sum(1 for t in raw_pos if t.get("passed"))

        raw_neg = [t for t in test_cases if t.get("kind") in ("negative_control", "open_boundary_probe")]
        raw_neg_count = len(raw_neg)
        raw_fc_count = sum(1 for t in raw_neg if t.get("is_fail_closed") or (t.get("passed") and not t.get("is_false_positive")))
        raw_fp_count = sum(1 for t in raw_neg if t.get("is_false_positive") or (not t.get("passed") and not t.get("is_fail_closed")))

        # Check for contradictory summary metrics in report
        if "positive_claims_count" in data and data["positive_claims_count"] != raw_pos_count:
            failed_criteria.append(f"inconsistent_positive_claims_count (reported {data['positive_claims_count']} != raw {raw_pos_count})")
        if "true_positives_count" in data and data["true_positives_count"] != raw_tp_count:
            failed_criteria.append(f"inconsistent_true_positives_count (reported {data['true_positives_count']} != raw {raw_tp_count})")
        if "negative_controls_count" in data and data["negative_controls_count"] != raw_neg_count:
            failed_criteria.append(f"inconsistent_negative_controls_count (reported {data['negative_controls_count']} != raw {raw_neg_count})")
        if "fail_closed_count" in data and data["fail_closed_count"] != raw_fc_count:
            failed_criteria.append(f"inconsistent_fail_closed_count (reported {data['fail_closed_count']} != raw {raw_fc_count})")
        if "false_positives_count" in data and data["false_positives_count"] != raw_fp_count:
            failed_criteria.append(f"inconsistent_false_positives_count (reported {data['false_positives_count']} != raw {raw_fp_count})")
        if "total_evaluations" in data and data["total_evaluations"] != raw_eval_count:
            failed_criteria.append(f"inconsistent_total_evaluations (reported {data['total_evaluations']} != raw {raw_eval_count})")
        if "passed_evaluations" in data and data["passed_evaluations"] != raw_passed_count:
            failed_criteria.append(f"inconsistent_passed_evaluations (reported {data['passed_evaluations']} != raw {raw_passed_count})")

        eval_count = raw_eval_count
        passed_count = raw_passed_count
        pos_count = raw_pos_count
        tp_count = raw_tp_count
        neg_count = raw_neg_count
        fc_count = raw_fc_count
        fp_count = raw_fp_count
    else:
        checks_dict = data.get("evaluations") or data.get("checks") or {}
        if isinstance(checks_dict, dict) and checks_dict:
            eval_count = len(checks_dict)
            passed_count = sum(1 for v in checks_dict.values() if v is True)
            failed_criteria.extend([k for k, v in checks_dict.items() if not v])
        else:
            eval_count = data.get("total_evaluations", 0)
            passed_count = data.get("passed_evaluations", 0)

        pos_count = data.get("positive_claims_count", 0)
        tp_count = data.get("true_positives_count", 0)
        neg_count = data.get("negative_controls_count", 0)
        fc_count = data.get("fail_closed_count", 0)
        fp_count = data.get("false_positives_count", 0)

    # Strictly guard against zero-division (never default to 1.0 or 100%)
    fail_closed_rate = (fc_count / neg_count) if neg_count > 0 else None
    false_pos_rate = (fp_count / neg_count) if neg_count > 0 else None
    true_pos_rate = (tp_count / pos_count) if pos_count > 0 else None

    # Verify rates claimed in report
    if "fail_closed_rate" in data:
        rep_fc = data["fail_closed_rate"]
        if neg_count == 0 and rep_fc is not None:
            failed_criteria.append("inconsistent_fail_closed_rate (claimed rate with 0 negative controls)")
        elif neg_count > 0 and rep_fc is not None and fail_closed_rate is not None and abs(rep_fc - fail_closed_rate) > 1e-4:
            failed_criteria.append(f"inconsistent_fail_closed_rate (reported {rep_fc} != calculated {fail_closed_rate})")
    if "false_positive_rate" in data:
        rep_fp = data["false_positive_rate"]
        if neg_count == 0 and rep_fp is not None:
            failed_criteria.append("inconsistent_false_positive_rate (claimed rate with 0 negative controls)")
        elif neg_count > 0 and rep_fp is not None and false_pos_rate is not None and abs(rep_fp - false_pos_rate) > 1e-4:
            failed_criteria.append(f"inconsistent_false_positive_rate (reported {rep_fp} != calculated {false_pos_rate})")
    if "true_positive_rate" in data:
        rep_tp = data["true_positive_rate"]
        if pos_count == 0 and rep_tp is not None:
            failed_criteria.append("inconsistent_true_positive_rate (claimed rate with 0 positive claims)")
        elif pos_count > 0 and rep_tp is not None and true_pos_rate is not None and abs(rep_tp - true_pos_rate) > 1e-4:
            failed_criteria.append(f"inconsistent_true_positive_rate (reported {rep_tp} != calculated {true_pos_rate})")

    # Benchmarks reject missing outputs and empty suites
    if not proc_stdout or not proc_stdout.strip():
        failed_criteria.append("missing_stdout_output")
    if eval_count == 0:
        failed_criteria.append("empty_evaluation_suite")

    # Count range checks
    if any(c < 0 for c in (pos_count, tp_count, neg_count, fc_count, fp_count, eval_count, passed_count)):
        failed_criteria.append("negative_count_metric")
    if tp_count > pos_count:
        failed_criteria.append(f"inconsistent_true_positives ({tp_count} > {pos_count})")
    if fc_count > neg_count:
        failed_criteria.append(f"inconsistent_fail_closed ({fc_count} > {neg_count})")
    if fp_count > neg_count:
        failed_criteria.append(f"inconsistent_false_positives ({fp_count} > {neg_count})")
    if passed_count > eval_count:
        failed_criteria.append(f"inconsistent_passed_evaluations ({passed_count} > {eval_count})")
    if pos_count + neg_count > eval_count:
        failed_criteria.append(f"inconsistent_claims_exceed_total ({pos_count} + {neg_count} > {eval_count})")
    if neg_count > 0 and (fc_count + fp_count != neg_count):
        failed_criteria.append(f"inconsistent_negative_controls_sum ({fc_count} + {fp_count} != {neg_count})")

    suite_ok = (
        (returncode == 0)
        and (eval_count > 0)
        and (passed_count == eval_count)
        and (fp_count == 0)
        and (len(failed_criteria) == 0)
    )

    return {
        "ok": suite_ok,
        "returncode": returncode,
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
    }


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
            "fail_closed_rate": None,
            "false_positive_rate": None,
            "true_positive_rate": None,
            "failed_criteria": ["missing_validate_script"],
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
            "fail_closed_rate": None,
            "false_positive_rate": None,
            "true_positive_rate": None,
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
                "fail_closed_rate": None,
                "false_positive_rate": None,
                "true_positive_rate": None,
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
        eval_res = evaluate_validation_report(
            data, proc_stdout=proc.stdout, returncode=proc.returncode
        )
        eval_res["name"] = name
        eval_res["folder"] = folder
        eval_res["stdout"] = proc.stdout
        eval_res["stderr"] = proc.stderr
        shutil.rmtree(temp_dir, ignore_errors=True)
        return eval_res
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {
            "name": name,
            "folder": folder,
            "ok": False,
            "error": f"Failed to parse validation.json: {exc}",
            "evaluations": 0,
            "passed": 0,
            "positive_claims_count": 0,
            "true_positives_count": 0,
            "negative_controls_count": 0,
            "fail_closed_count": 0,
            "false_positives_count": 0,
            "fail_closed_rate": None,
            "false_positive_rate": None,
            "true_positive_rate": None,
            "failed_criteria": [f"parse_error: {exc}"],
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
        print(
            f"    {status_sym} ({res['passed']}/{res['evaluations']} criteria passed, "
            f"{_format_rate(res['fail_closed_rate'])} fail-closed, "
            f"{_format_rate(res['false_positive_rate'])} FP)"
        )
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

    global_fail_closed_rate = (global_fail_closed / global_neg_controls) if global_neg_controls > 0 else None
    global_false_positive_rate = (global_false_positives / global_neg_controls) if global_neg_controls > 0 else None
    global_true_positive_rate = (global_true_positives / global_pos_claims) if global_pos_claims > 0 else None

    print("\n" + "=" * 80)
    print("CONSOLIDATED MILLENNIUM SCORECARD")
    print("=" * 80)
    print(f"{'Problem Name':<30} | {'Directory':<26} | {'Criteria':<8} | {'FC Rate':<8} | {'Status'}")
    print("-" * 80)

    all_ok = True
    for r in results:
        status_text = "PASS" if r["ok"] else f"FAIL (exit {r.get('returncode', '?')})"
        print(f"{r['name']:<30} | {r['folder']:<26} | {r['passed']}/{r['evaluations']:<6} | {_format_rate(r['fail_closed_rate']):>8} | {status_text}")
        if not r["ok"]:
            all_ok = False

    print("-" * 80)
    print(f"Total Evaluated Criteria: {total_passed}/{total_evals}")
    print(f"Global Positive Claims: {global_true_positives}/{global_pos_claims} ({_format_rate(global_true_positive_rate)} true positive rate)")
    print(f"Global Negative Controls: {global_fail_closed}/{global_neg_controls} ({_format_rate(global_fail_closed_rate)} fail-closed rate)")
    print(f"Global False Positive Rate: {_format_rate(global_false_positive_rate)} ({global_false_positives}/{global_neg_controls})")
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
