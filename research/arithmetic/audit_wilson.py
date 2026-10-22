"""Reproduce Day 12's kernel/axiom audits and research-session revalidation.

Run with each supported executable, for example:
    python research/arithmetic/audit_wilson.py --lean-bin /path/to/lean

Evidence is written only after every fail-closed assertion succeeds. It
certifies the named Lean declarations, not an automatic semantic alignment
of arbitrary natural-language statements.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from axiom import Axiom, Guarantee


def audit(lean_bin: str) -> dict:
    binary = Path(lean_bin).resolve(strict=True)
    version = subprocess.run(
        [str(binary), "--version"], check=True, capture_output=True,
        text=True, encoding="utf-8", timeout=30,
    ).stdout.strip()
    source = ROOT / "research/arithmetic/dia_12_wilson.lean"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    previous = os.environ.get("AXIOM_LEAN_BIN")
    try:
        os.environ["AXIOM_LEAN_BIN"] = str(binary)
        ax = Axiom()
        result = ax.verify_lean_file(source, timeout=120)
        if not (result.ok and result.guarantee == Guarantee.FORMAL_PROOF
                and result.verification and result.verification.passed):
            raise RuntimeError(result.to_json())
        data = result.verification.data
        audited = data["audited_theorems"]
        expected = {
            "Dia12Wilson.wilson_forward", "Dia12Wilson.wilson_converse",
            "Dia12Wilson.wilson_iff", "Dia12Wilson.wilson_congruence",
            "Dia12Wilson.boundary_one",
        }
        if not expected.issubset(audited) or data.get("untrusted_axioms"):
            raise RuntimeError("Missing theorem coverage or untrusted axioms")
        if data["formal_manifest"]["kernel_validity"].get("has_sorry"):
            raise RuntimeError("Proof holes found")
        with tempfile.TemporaryDirectory(prefix="axiom-wilson-session-") as td:
            created = ax.session("new", name="dia-12-wilson", directory=td)
            if not created.ok:
                raise RuntimeError(created.to_json())
            recorded = ax.session(
                "record", name="dia-12-wilson", result=result,
                note="Wilson biconditional for p >= 2; kernel + axiom audit",
                directory=td,
            )
            status = ax.session("status", name="dia-12-wilson", directory=td)
            if not (recorded.ok and status.ok
                    and status.value["step_validity"]["all_steps_valid"]
                    and status.guarantee == Guarantee.FORMAL_PROOF):
                raise RuntimeError(status.to_json())
            session = {
                "name": "dia-12-wilson",
                "guarantee": status.guarantee.value,
                "step_validity": status.value["step_validity"],
                "logical_implication_proven": False,
            }
        if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise RuntimeError("Source changed during the audit")
        return {
            "source": source.relative_to(ROOT).as_posix(),
            "sha256": digest,
            "lean_version": version,
            "guarantee": result.guarantee.value,
            "verification_passed": result.verification.passed,
            "audited_theorems": audited,
            "axioms_used": data["axioms_used"],
            "untrusted_axioms": data["untrusted_axioms"],
            "session_revalidation": session,
        }
    finally:
        if previous is None:
            os.environ.pop("AXIOM_LEAN_BIN", None)
        else:
            os.environ["AXIOM_LEAN_BIN"] = previous


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean-bin", required=True, action="append")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    evidence = {"audits": [audit(binary) for binary in args.lean_bin]}
    text = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
