"""Tests for payload tamper detection and imported hypothesis integrity.

Validates:
1. Recomputed values are strictly compared against persisted payload values.
2. Tampered values in saved JSON payloads are detected and rejected.
3. Semantically equivalent values (symbolic algebraic equality, dict key ordering, int/float) are accepted.
4. Imported hypotheses from disk are downgraded to unverified until active revalidation.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from axiom import Axiom, Guarantee
from axiom.session import ResearchSession


class TestTamperDetectionAndHypothesisIntegrity(unittest.TestCase):
    def setUp(self) -> None:
        self.ax = Axiom()

    def test_tampered_payload_value_is_rejected(self) -> None:
        """A JSON payload with tampered value must be rejected with recomputed_value_mismatch."""
        # Genuine solve: x^2 - 4 = 0 has roots -2, 2
        genuine = self.ax.solve("x**2 - 4 = 0", variable="x")
        self.assertTrue(genuine.ok)
        payload = genuine.to_dict()

        # Tamper value to claim roots are 5, -5
        payload["value"] = ["-5", "5"]
        tampered_res = self.ax.verify(payload)
        self.assertFalse(tampered_res.verified)
        self.assertFalse(tampered_res.ok)
        self.assertIn("tamper", tampered_res.error.lower())

    def test_tampered_derivative_value_is_rejected(self) -> None:
        """A JSON payload with tampered derivative must be rejected."""
        genuine = self.ax.differentiate("x**3", variable="x")
        self.assertTrue(genuine.ok)
        payload = genuine.to_dict()

        # Tamper value
        payload["value"] = "4*x**2"
        tampered_res = self.ax.verify(payload)
        self.assertFalse(tampered_res.verified)
        self.assertFalse(tampered_res.ok)
        self.assertIn("tamper", tampered_res.error.lower())

    def test_semantically_equivalent_payload_accepted(self) -> None:
        """Equivalent expressions (e.g. x + y vs y + x) are recognized as valid."""
        res = self.ax.simplify("x + y")
        payload = res.to_dict()
        payload["value"] = "y + x"
        verified_res = self.ax.verify(payload)
        self.assertTrue(verified_res.verified)

    def test_imported_hypotheses_downgraded_on_load(self) -> None:
        """Hypotheses loaded from JSON must be downgraded to UNVERIFIED until revalidation."""
        with tempfile.TemporaryDirectory() as td:
            session = ResearchSession(name="hyp_test")
            session.add_hypothesis("2 + 2 = 4", detail="Arithmetic claim")
            # Revalidate so it becomes verified in current session
            session.revalidate_all(self.ax)
            self.assertEqual(session.hypotheses[0].guarantee, Guarantee.EXACT_SYMBOLIC.value)
            session.save(directory=td)

            # Load
            loaded = ResearchSession.load(name="hyp_test", directory=td)
            self.assertEqual(loaded.hypotheses[0].guarantee, Guarantee.UNVERIFIED.value)
            self.assertEqual(loaded.hypotheses[0].status, "imported_unverified")

            # Actively revalidate
            loaded.revalidate_all(self.ax)
            self.assertEqual(loaded.hypotheses[0].guarantee, Guarantee.EXACT_SYMBOLIC.value)
            self.assertEqual(loaded.hypotheses[0].status, "verified")

    def test_fraudulent_imported_hypothesis_refuted(self) -> None:
        """Tampered hypothesis loaded from disk claiming false statement is refuted upon revalidation."""
        with tempfile.TemporaryDirectory() as td:
            session = ResearchSession(name="fraud_test")
            session.add_hypothesis("x + 1 = x", detail="False claim")
            session.save(directory=td)

            # Tamper the saved JSON on disk to falsely claim it was proven
            session_file = Path(td) / "fraud_test.json"
            data = json.loads(session_file.read_text(encoding="utf-8"))
            data["hypotheses"][0]["guarantee"] = "formal-proof"
            data["hypotheses"][0]["status"] = "verified"
            session_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

            # Load
            loaded = ResearchSession.load(name="fraud_test", directory=td)
            self.assertEqual(loaded.hypotheses[0].guarantee, Guarantee.UNVERIFIED.value)
            self.assertEqual(loaded.hypotheses[0].status, "imported_unverified")

            # Actively revalidate
            loaded.revalidate_all(self.ax)
            self.assertNotEqual(loaded.hypotheses[0].guarantee, Guarantee.FORMAL_PROOF.value)
            self.assertEqual(loaded.hypotheses[0].status, "refuted")
