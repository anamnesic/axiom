"""Epistemic State Separation & Exact-Value Integrity Suite.

Adversarial regression suite for ADR-0031. It covers the two integrity gaps
found in the 20/10/2026 audit:

1. **Refutation must carry evidence.** The four epistemic states must not
   collapse: a *failed* verification is not a refutation. Only a result with
   an explicit witness (counterexample, violating substitution, divergence)
   may be reported as ``REFUTATION``; everything else is fail-closed
   ``INCONCLUSIVE``.

2. **Exact value comparison must not round through binary floats.** The
   tamper-detection comparator reconciles a recomputed value with a persisted
   payload. IEEE-754 doubles collapse distinct integers above ``2**53``
   (``float(2**53) == float(2**53 + 1)`` is ``True``), so an integer must
   never be routed through a float comparison.

The suite runs WITHOUT mocks in the critical path: every state transition is
driven by a real AXIOM computation.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from axiom import Axiom, EpistemicState, Guarantee, MathResult, Verification
from axiom.contract import REFUTING_VERIFICATION_KINDS, outcome_word
from axiom.core import _values_semantically_equal
from axiom.verification import revalidate_witness


class TestEpistemicStateSeparation(unittest.TestCase):
    def setUp(self) -> None:
        self.ax = Axiom()

    # ------------------------------------------------------------ PROOF state
    def test_proof_state_for_certified_identities(self) -> None:
        """A certified symbolic identity is a PROOF, not an approximation."""
        res = self.ax.compare("sin(x)^2 + cos(x)^2", "1")
        self.assertTrue(res.ok and res.verified)
        self.assertEqual(res.epistemic_state, EpistemicState.PROOF)
        self.assertEqual(res.outcome, "verified")
        self.assertIn(
            res.guarantee,
            (Guarantee.EXACT_SYMBOLIC, Guarantee.VERIFIED_SUBSTITUTION),
        )

    def test_proof_state_for_exact_root_substitution(self) -> None:
        """A candidate that satisfies the equation by exact substitution is a PROOF."""
        res = self.ax.verify("x^2 - 5*x + 6 = 0", candidate="2")
        self.assertTrue(res.ok and res.verified)
        self.assertEqual(res.epistemic_state, EpistemicState.PROOF)
        self.assertEqual(res.outcome, "verified")

    # --------------------------------------------------------- REFUTATION state
    def test_refutation_state_requires_a_witness(self) -> None:
        """A rejected candidate root is a REFUTATION: the substitution is the witness."""
        res = self.ax.verify("x^2 - 5*x + 6 = 0", candidate="7")
        self.assertTrue(res.ok)
        self.assertFalse(res.verified)
        self.assertEqual(res.epistemic_state, EpistemicState.REFUTATION)
        self.assertEqual(res.outcome, "refuted")
        self.assertIsNotNone(res.verification)
        self.assertTrue(res.verification.detail)

    def test_refutation_state_for_counterexample(self) -> None:
        """An explicit counterexample is a REFUTATION and records the witness."""
        res = self.ax.compare("sqrt(x^2)", "x")
        self.assertTrue(res.ok)
        self.assertEqual(res.epistemic_state, EpistemicState.REFUTATION)
        self.assertIsNotNone(res.verification)
        self.assertEqual(res.verification.kind, "counterexample-search")
        self.assertTrue(res.verification.data.get("counterexample"))

    def test_failed_verification_alone_is_not_a_refutation(self) -> None:
        """A failed check without falsity evidence must stay INCONCLUSIVE.

        This is the core fail-closed guarantee: 'the check did not succeed'
        is NOT the same claim as 'the claim is false'.
        """
        inconclusive = Verification(
            kind="constant-exact-inconclusive",
            passed=False,
            detail="Exact constant difference could not be decided",
            checks=1,
        )
        res = MathResult(
            kind="compare",
            input="x + y",
            ok=True,
            value={"status": "inconclusive"},
            value_str="inconclusive",
            guarantee=Guarantee.UNVERIFIED,
            verification=inconclusive,
        )
        self.assertFalse(res.has_refutation_evidence)
        self.assertEqual(res.epistemic_state, EpistemicState.INCONCLUSIVE)
        self.assertEqual(res.outcome, "inconclusive")

    def test_value_str_refuted_without_evidence_is_inconclusive(self) -> None:
        """A bare 'refuted' label is not evidence: it must not alone force REFUTATION."""
        res = MathResult(
            kind="verify",
            input="integral(x)",
            ok=True,
            value={},
            value_str="refuted",
            guarantee=Guarantee.UNVERIFIED,
            verification=Verification(
                kind="unevaluated-integral",
                passed=False,
                detail="integral remained in unevaluated form",
            ),
        )
        self.assertFalse(res.has_refutation_evidence)
        self.assertEqual(res.epistemic_state, EpistemicState.INCONCLUSIVE)

    def test_status_disproven_without_refuting_kind_or_witness_is_inconclusive(self) -> None:
        """A status: disproven without a refuting verification kind or witness is inconclusive."""
        res = MathResult(
            kind="verify",
            input="integral(x)",
            ok=True,
            value={"status": "disproven"},
            value_str="disproven",
            guarantee=Guarantee.UNVERIFIED,
            verification=Verification(
                kind="unevaluated-integral",
                passed=False,
                detail="integral remained in unevaluated form",
                data={"status": "disproven"},
            ),
        )
        self.assertFalse(res.has_refutation_evidence)
        self.assertEqual(res.epistemic_state, EpistemicState.INCONCLUSIVE)

    def test_unevaluated_integral_is_inconclusive_not_refutation(self) -> None:
        """An integral that cannot be evaluated is inconclusive, not falsified."""
        res = self.ax.integrate("x**x", variable="x", lower="0", upper="1")
        self.assertTrue(res.ok)
        self.assertNotEqual(res.epistemic_state, EpistemicState.REFUTATION)

    def test_refuting_kinds_exclude_inconclusive_kinds(self) -> None:
        """The refuting-kind whitelist must not contain any undecidable check."""
        for kind in (
            "constant-exact-inconclusive",
            "unevaluated-integral",
            "definite-integral-check",
            "inequality-check",
            "empty-solution-set",
            "numerical-spot-check",
        ):
            self.assertNotIn(kind, REFUTING_VERIFICATION_KINDS)

    def test_outcome_word_distinguishes_failure_from_falsity(self) -> None:
        """``outcome_word`` must report 'refuted' only with a structured witness.

        A recognised refutation *kind* plus a prose ``detail`` is not enough:
        the detail is a human-readable summary, not machine-checkable evidence.
        """
        # Prose only -> not a refutation.
        self.assertEqual(
            outcome_word(Verification(kind="substitution", passed=False, detail="residual 5 != 0")),
            "inconclusive",
        )
        # Structured witness -> refutation.
        self.assertEqual(
            outcome_word(
                Verification(
                    kind="substitution",
                    passed=False,
                    detail="root x = 7 failed substitution",
                    data={
                        "witness": {
                            "type": "residual",
                            "expression": "x**2 - 5*x + 6",
                            "substitutions": {"x": "7"},
                            "expected": "0",
                        }
                    },
                )
            ),
            "refuted",
        )
        self.assertEqual(
            outcome_word(Verification(kind="exact-substitution", passed=True, detail="ok")),
            "verified",
        )
        self.assertEqual(outcome_word(None), "inconclusive")

    # ----------------------------------------------------- INCONCLUSIVE state
    def test_inconclusive_for_nonexistent_bilateral_limit(self) -> None:
        """A two-sided limit that does not exist is INCONCLUSIVE, never a proof."""
        res = self.ax.limit("Abs(x)/x", variable="x", point="0", direction="+-")
        self.assertTrue(res.ok)
        self.assertFalse(res.verified)
        self.assertEqual(res.epistemic_state, EpistemicState.INCONCLUSIVE)

    def test_session_hypothesis_is_fail_closed_without_evidence(self) -> None:
        """A hypothesis is only 'refuted' when the check carries falsity evidence."""
        with tempfile.TemporaryDirectory() as td:
            ax = Axiom()
            # A false hypothesis: the comparison yields a concrete counterexample.
            false_hyp = ax.session(
                "hypothesis",
                name="demo",
                hypothesis="x + 1 = 1",
                directory=td,
            )
            self.assertTrue(false_hyp.ok)
            hyp = false_hyp.value["hypotheses"][0]
            self.assertEqual(hyp["status"], "refuted")
            self.assertIn("counterexample", hyp["detail"].lower())

            # A true hypothesis is verified.
            true_hyp = ax.session(
                "hypothesis",
                name="demo2",
                hypothesis="(x + 1)^2 = x^2 + 2*x + 1",
                directory=td,
            )
            self.assertTrue(true_hyp.ok)
            self.assertEqual(true_hyp.value["hypotheses"][0]["status"], "verified")


class TestStructuredFalsityWitnesses(unittest.TestCase):
    """ADR-0032: a refutation must carry a *structured*, replayable witness."""

    def setUp(self) -> None:
        self.ax = Axiom()

    def test_prose_detail_alone_is_not_a_witness(self) -> None:
        """A recognised kind plus a prose detail must NOT be a refutation."""
        res = MathResult(
            kind="compare",
            input="x",
            ok=True,
            value={},
            value_str="refuted",
            guarantee=Guarantee.UNVERIFIED,
            verification=Verification(
                kind="counterexample-search",
                passed=False,
                detail="counterexample found somewhere (trust me)",
            ),
        )
        self.assertFalse(res.has_refutation_evidence)
        self.assertEqual(res.epistemic_state, EpistemicState.INCONCLUSIVE)

    def test_real_counterexample_carries_a_replayable_witness(self) -> None:
        """A genuine counterexample ships a structured, replayable witness."""
        res = self.ax.compare("sqrt(x^2)", "x")
        self.assertEqual(res.epistemic_state, EpistemicState.REFUTATION)
        assert res.verification is not None
        witness = (res.verification.data or {}).get("witness")
        self.assertIsInstance(witness, dict)
        self.assertEqual(witness["type"], "counterexample")
        self.assertIn("expression", witness)
        self.assertIn("substitutions", witness)

    def test_witness_replay_confirms_the_refutation(self) -> None:
        """Replaying the recorded witness must confirm that the claim is false."""
        res = self.ax.compare("sqrt(x^2)", "x")
        status, detail = revalidate_witness(res.verification)
        self.assertEqual(status, "confirmed", detail)

    def test_witness_replay_detects_a_doctored_witness(self) -> None:
        """A witness doctored so the expression vanishes must not re-validate."""
        res = self.ax.compare("sqrt(x^2)", "x")
        assert res.verification is not None
        data = dict(res.verification.data or {})
        witness = dict(data["witness"])
        # Point the witness at an expression that IS zero at that point.
        witness["expression"] = "x - x"
        data["witness"] = witness
        doctored = Verification(
            kind=res.verification.kind,
            passed=False,
            detail=res.verification.detail,
            checks=res.verification.checks,
            max_error=res.verification.max_error,
            data=data,
        )
        status, detail = revalidate_witness(doctored)
        self.assertEqual(status, "failed", detail)

    def test_missing_witness_is_absent(self) -> None:
        """A verification with no structured witness is not re-validatable."""
        status, _ = revalidate_witness(
            Verification(kind="substitution", passed=False, detail="no witness")
        )
        self.assertEqual(status, "absent")

    def test_undeterminable_substitution_is_not_a_refutation(self) -> None:
        """A residual that could not even be evaluated is inconclusive."""
        res = MathResult(
            kind="verify",
            input="x = 1",
            ok=True,
            value={},
            value_str="inconclusive",
            guarantee=Guarantee.UNVERIFIED,
            verification=Verification(
                kind="substitution-indeterminate",
                passed=False,
                detail="could not evaluate residual at x = 1",
            ),
        )
        self.assertNotIn("substitution-indeterminate", REFUTING_VERIFICATION_KINDS)
        self.assertEqual(res.epistemic_state, EpistemicState.INCONCLUSIVE)


class TestPersistedPayloadIntegrity(unittest.TestCase):
    """ADR-0032: a persisted payload must not be able to skip its own audit."""

    def setUp(self) -> None:
        self.ax = Axiom()

    def test_missing_value_field_is_rejected_for_every_kind(self) -> None:
        """Deleting the persisted 'value' must be detected, not silently accepted."""
        cases = [
            self.ax.number_theory("factorint", n=60),
            self.ax.solve("x**2 - 4 = 0", variable="x"),
            self.ax.differentiate("x**3", variable="x"),
            self.ax.limit("sin(x)/x", variable="x", point="0"),
            self.ax.statistics("[1,2,3,4]"),
        ]
        for res in cases:
            payload = res.to_dict()
            del payload["value"]
            out = self.ax.verify(payload)
            self.assertFalse(out.ok, f"{res.kind} accepted a payload with no value")
            self.assertFalse(out.verified)
            self.assertIn("tamper", (out.error or "").lower(), res.kind)

    def test_null_value_field_is_rejected(self) -> None:
        """A null 'value' is as suspicious as an absent one."""
        payload = self.ax.number_theory("factorint", n=60).to_dict()
        payload["value"] = None
        out = self.ax.verify(payload)
        self.assertFalse(out.ok)
        self.assertIn("tamper", (out.error or "").lower())

    def test_failed_operation_payload_is_not_reverifiable(self) -> None:
        """A persisted failed operation carries no re-verifiable value."""
        payload = self.ax.number_theory("factorint", n=60).to_dict()
        payload["ok"] = False
        payload.pop("value", None)
        out = self.ax.verify(payload)
        self.assertFalse(out.ok)
        self.assertIn("tamper", (out.error or "").lower())

    def test_untampered_payload_is_still_accepted(self) -> None:
        """The integrity gate must not break legitimate re-verification."""
        for res in (
            self.ax.number_theory("factorint", n=60),
            self.ax.solve("x**2 - 4 = 0", variable="x"),
            self.ax.differentiate("x**3", variable="x"),
        ):
            out = self.ax.verify(res.to_dict())
            self.assertTrue(out.ok, out.error)
            self.assertTrue(out.verified, res.kind)


class TestExactValueIntegrity(unittest.TestCase):
    """The persisted-value comparator must never lose integer precision."""

    def test_large_integers_are_not_reconciled_through_float(self) -> None:
        """2**53 and 2**53 + 1 are distinct integers and must not compare equal."""
        a = 9007199254740992  # 2**53
        b = 9007199254740993  # 2**53 + 1
        self.assertNotEqual(a, b)
        # Precondition of the defect: the binary float path collapses them.
        self.assertEqual(float(a), float(b))
        # The comparator must NOT inherit that collapse.
        self.assertFalse(_values_semantically_equal(a, b))
        self.assertTrue(_values_semantically_equal(a, a))
        self.assertTrue(_values_semantically_equal(b, b))

    def test_large_integer_versus_numeric_string(self) -> None:
        """A persisted numeric string is compared exactly, not via a float."""
        self.assertFalse(_values_semantically_equal(9007199254740992, "9007199254740993"))
        self.assertTrue(_values_semantically_equal(9007199254740993, "9007199254740993"))
        self.assertFalse(_values_semantically_equal(9007199254740993, "9007199254740992.0"))

    def test_large_integer_versus_float_is_not_reconciled(self) -> None:
        """An exact integer must not be accepted against a lossy float."""
        self.assertFalse(_values_semantically_equal(9007199254740993, 9007199254740992.0))
        self.assertTrue(_values_semantically_equal(10, 10.0))

    def test_float_approximations_still_compare(self) -> None:
        """Genuinely approximate (float) payloads keep the tolerant behaviour."""
        self.assertTrue(_values_semantically_equal(0.1, 0.1))
        self.assertTrue(_values_semantically_equal(0.1, "0.1"))
        self.assertFalse(_values_semantically_equal(1.0, 1.0000001))

    def test_tampered_large_integer_payload_is_detected(self) -> None:
        """End-to-end: a persisted payload with an altered large integer is rejected.

        ``binomial(100, 50)`` is far above 2**53, so the legacy float-mediated
        comparator would have accepted the tampered value.
        """
        ax = Axiom()
        res = ax.number_theory("binomial", n=100, k=50)
        self.assertTrue(res.ok and res.verified)
        self.assertGreater(res.value, 2**53)
        # Precondition of the defect: the binary float path collapses the pair.
        self.assertEqual(float(res.value), float(res.value + 1))

        payload = {
            "kind": res.kind,
            "input": res.input,
            "value": res.value,
            "value_str": res.value_str,
            "guarantee": res.guarantee.value,
            "verification": res.verification.to_dict(),
        }
        # Integrity check on the untampered payload must succeed.
        good = ax.verify(payload)
        self.assertTrue(good.ok, good.error)

        # Now tamper with the persisted value by one unit.
        payload["value"] = res.value + 1
        tampered = ax.verify(payload)
        self.assertFalse(tampered.ok)
        self.assertIn("tamper", (tampered.error or "").lower())


if __name__ == "__main__":
    unittest.main()
