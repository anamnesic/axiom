"""Reproduce the Day 12 kernel/axiom audits; never certify prose alignment."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re

from axiom import Axiom, Guarantee, ResearchSession, __version__


ROOT = Path(__file__).resolve().parents[2]
PROOF = Path("research/arithmetic/dia_12_wilson.lean")
CANONICAL = "Wilson: for p >= 2, p is prime iff p divides (p-1)! + 1"
TRUSTED = {"propext", "Classical.choice", "Quot.sound"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean-bin", action="append", default=[],
                        help="Lean executable; repeat for multiple toolchains")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "reports/dia-12-wilson/validation.json")
    args = parser.parse_args()
    os.chdir(ROOT)
    source = PROOF.read_text(encoding="utf-8")
    names = ["Dia12Wilson." + n for n in re.findall(r"^theorem (\w+)", source, re.M)]
    session = ResearchSession(name="dia-12-wilson")
    audits = []
    original_bin = os.environ.get("AXIOM_LEAN_BIN")
    try:
        for executable in args.lean_bin or [original_bin]:
            if executable:
                os.environ["AXIOM_LEAN_BIN"] = executable
            ax = Axiom()
            result = ax.verify_lean_file(PROOF, timeout=120)
            require(result.ok and result.guarantee == Guarantee.FORMAL_PROOF
                    and result.verification.passed, str(result.to_dict()))
            value = result.value
            kernel = value["formal_manifest"]["kernel_validity"]
            require(set(value["audited_theorems"]) == set(names), "Incomplete theorem audit")
            require(kernel["audit_complete"] and not kernel["has_sorry"], "Incomplete proof")
            require(not value["untrusted_axioms"]
                    and set(value["axioms_used"]) <= TRUSTED, "Unexpected axioms")
            session.record(result, depends_on=[], note=value["lean_version"])

            # An intentionally false boundary claim must fail in the real kernel.
            negative = ax.prove(
                "import Init.Data.Nat.Basic\n"
                "theorem wrong_boundary : ¬ ((1 : Nat) ∣ 2) := by decide\n",
                engine="lean", timeout=120,
            )
            require(negative.guarantee == Guarantee.UNVERIFIED
                    and not negative.verification.passed, "False boundary claim accepted")

            # This is deliberately a separate call: the prose alignment checker
            # only establishes thematic overlap, not equivalence of propositions.
            alignment = ax.verify_lean_file(PROOF, canonical_statement=CANONICAL, timeout=120)
            alignment_data = alignment.value["formal_manifest"]["spec_alignment"]
            require(alignment_data["status"] == "candidate"
                    and alignment.guarantee == Guarantee.UNVERIFIED
                    and not alignment.verification.passed, "Unexpected alignment behavior")
            audits.append({
                "lean_version": value["lean_version"],
                "guarantee": result.guarantee.value,
                "verification_passed": result.verification.passed,
                "audited_theorems": value["audited_theorems"],
                "axioms_used": value["axioms_used"],
                "untrusted_axioms": value["untrusted_axioms"],
                "has_sorry": kernel["has_sorry"],
                "audit_complete": kernel["audit_complete"],
                "axiom_audit": value["diagnostics"],
                "negative_control": {
                    "statement": "not (1 divides 2)",
                    "guarantee": negative.guarantee.value,
                    "verification_passed": negative.verification.passed,
                },
                "prose_alignment": {
                    "canonical_statement": CANONICAL,
                    "status": alignment_data["status"],
                    "congruent": alignment_data["congruent"],
                    "guarantee": alignment.guarantee.value,
                    "verification_passed": alignment.verification.passed,
                    "scope_notes": alignment_data["scope_notes"],
                },
            })
            print(f"{value['lean_version']}: {len(names)} theorems, formal-proof; "
                  "negative control rejected; prose alignment remains candidate")
    finally:
        if original_bin is None:
            os.environ.pop("AXIOM_LEAN_BIN", None)
        else:
            os.environ["AXIOM_LEAN_BIN"] = original_bin

    session_file = session.save(directory=ROOT / ".axiom/sessions")
    files = [PROOF, Path(__file__).relative_to(ROOT), Path("src/axiom/core.py"),
             Path("src/axiom/engines/lean_engine.py"), Path("src/axiom/contract.py")]
    manifest = {
        "formal_statement": "forall p : Nat, 2 <= p -> "
                            "(IsPrime p <-> p divides (fact (p-1) + 1))",
        "scope": "The Wilson iff; not the stronger composite-factorial corollary.",
        "environment": {
            "python": platform.python_version(), "platform": platform.platform(),
            "axiom_source_version": __version__,
            **{p: importlib.metadata.version(p) for p in ("axiom-math", "sympy", "mpmath")},
        },
        "source_sha256": {p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        "audits": audits,
        "session": str(Path(session_file).relative_to(ROOT)).replace("\\", "/"),
        "session_chain_guarantee": session.chain_guarantee.value,
        "session_logical_implication_proven": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
