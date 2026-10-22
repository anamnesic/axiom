"""Day 12: source-bound evidence and live kernel checks for Wilson's theorem."""

import hashlib
import json
import os
from pathlib import Path
import unittest

from axiom import Axiom, Guarantee


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/arithmetic/dia_12_wilson.lean"
EVIDENCE = ROOT / "research/arithmetic/evidence/dia_12_wilson.json"


class TestWilson(unittest.TestCase):
    def test_wilson_evidence_is_bound_to_source(self) -> None:
        """Historical certificates name the same source hash and both toolchains."""
        audits = json.loads(EVIDENCE.read_text(encoding="utf-8"))["audits"]
        self.assertEqual(len(audits), 2)
        digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        for version, audit in zip(("4.14.0", "4.35.0"), audits):
            self.assertIn(version, audit["lean_version"])
            self.assertEqual(audit["sha256"], digest)
            self.assertEqual(audit["guarantee"], "formal-proof")
            self.assertTrue(audit["verification_passed"])
            self.assertEqual(audit["untrusted_axioms"], [])
            self.assertTrue(audit["session_revalidation"]["step_validity"]["all_steps_valid"])
            self.assertIn("Dia12Wilson.wilson_iff", audit["audited_theorems"])
            self.assertIn("Dia12Wilson.boundary_one", audit["audited_theorems"])

    def test_wilson_existing_computational_primitives(self) -> None:
        """Exact factorial/remainder evaluation already covers numerical examples."""
        ax = Axiom()
        for p, expected in ((2, "0"), (7, "0"), (11, "0"), (4, "3"), (9, "1")):
            result = ax.evaluate(f"(factorial({p - 1}) + 1) % {p}")
            self.assertTrue(result.ok, result.error)
            self.assertEqual(result.guarantee, Guarantee.EXACT_SYMBOLIC)
            self.assertTrue(result.verification and result.verification.passed)
            self.assertEqual(result.value_str, expected)

    def test_lean_wilson_biconditional_and_boundary(self) -> None:
        """Re-audit the universal theorem, not just its finite examples."""
        ax = Axiom()
        if not ax.registry.get("lean").available:
            if os.environ.get("AXIOM_REQUIRE_LEAN") == "1":
                self.fail("AXIOM_REQUIRE_LEAN=1 but Lean is unavailable")
            self.skipTest("Lean toolchain is unavailable")
        result = ax.verify_lean_file(SOURCE, timeout=120)
        self.assertTrue(result.ok, result.error)
        self.assertEqual(result.guarantee, Guarantee.FORMAL_PROOF)
        self.assertTrue(result.verification and result.verification.passed)
        data = result.verification.data
        self.assertEqual(data["untrusted_axioms"], [])
        for name in ("wilson_forward", "wilson_converse", "wilson_iff",
                     "wilson_congruence", "boundary_one"):
            self.assertIn(f"Dia12Wilson.{name}", data["audited_theorems"])


if __name__ == "__main__":
    unittest.main()
