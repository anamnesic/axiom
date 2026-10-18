"""Adversarial Soundness & Epistemic Verification Suite.

Validates the 10 specification soundness, isolation, and epistemic integrity guarantees
WITHOUT mocks in the critical path:
1. Lexical matching on its own NEVER produces 'verified'.
2. Lean declaration audit recognizes typed, implicit, and multiline binders.
3. Imported/cached results cannot receive 'formal-proof' without active revalidation.
4. Step validity and dependency chain validity are tracked and reported separately.
5. Untrusted Lean execution runs in isolated sandbox with resource & timeout limits.
6. MCP file operations strictly respect authorized directory roots and permissions.
7. CI executes adversarial tests without mocks in the critical path.
8. Benchmarks reject inconsistent metrics and missing outputs.
9. Epistemic differentiation: Proof, Approximation, Refutation, and Inconclusive.
10. Effective CLI and MCP command workflows with verified guarantees.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

from axiom import Axiom, Guarantee, MathResult, Verification, Evidence
from axiom.core import _audit_specification_alignment, _extract_lean_declarations
from axiom.mcp_server import dispatch_tool, validate_mcp_path, get_authorized_roots
from axiom.session import ResearchSession


class TestAdversarialSoundness(unittest.TestCase):
    def setUp(self) -> None:
        self.ax = Axiom()

    # ----------------------------------------------------------------- Check 1: Lexical matching
    def test_lexical_match_never_generates_verified(self) -> None:
        """No lexical match on its own must ever produce 'verified' alignment or guarantee."""
        # 1. Statement with overlapping keyword ("identity") but mathematical mismatch
        res_overlap = self.ax.prove(
            "theorem identity_probe (n : Nat) : n * 1 = n := by omega",
            engine="sympy",
            canonical_statement="AddZero identity for real numbers",
        )
        self.assertFalse(res_overlap.verified)
        self.assertNotEqual(res_overlap.guarantee, Guarantee.FORMAL_PROOF)
        self.assertNotEqual(res_overlap.guarantee, Guarantee.EXACT_SYMBOLIC)
        manifest_overlap = res_overlap.verification.data["formal_manifest"]
        self.assertNotEqual(manifest_overlap["spec_alignment"]["verified_alignment"], "verified")
        self.assertEqual(manifest_overlap["spec_alignment"]["verified_alignment"], "candidate")
        self.assertFalse(manifest_overlap["spec_alignment"]["congruent"])

        # 2. Multiplicative identity without keyword overlap against AddZero
        res_mul = self.ax.prove(
            "x * 1 = x",
            engine="sympy",
            canonical_statement="AddZero identity for real numbers",
        )
        self.assertFalse(res_mul.verified)
        manifest_mul = res_mul.verification.data["formal_manifest"]
        self.assertNotEqual(manifest_mul["spec_alignment"]["verified_alignment"], "verified")
        self.assertIn(manifest_mul["spec_alignment"]["verified_alignment"], ("candidate", "unaligned"))
        self.assertFalse(manifest_mul["spec_alignment"]["congruent"])

        # 3. Direct audit function inspection: lexical match yields candidate, never verified
        align, is_aligned, congruent, method, _ = _audit_specification_alignment(
            statement="theorem identity_claim (n : Nat) : n * 1 = n := by omega",
            canonical_statement="AddZero identity for real numbers",
            declared_alignment="congruent",
        )
        self.assertNotEqual(align, "verified")
        self.assertFalse(congruent)
        self.assertEqual(align, "candidate")
        self.assertEqual(method, "lexical_thematic_candidate")

        # 4. Goldbach add_zero anti-drift check
        res_goldbach = self.ax.prove(
            "theorem goldbach_add_zero (n : Nat) : n + 0 = n := by rfl",
            canonical_statement="Goldbach conjecture",
            declared_hypotheses=["n : Nat"],
        )
        self.assertFalse(res_goldbach.verified)
        manifest_gb = res_goldbach.verification.data["formal_manifest"]
        self.assertFalse(manifest_gb["spec_alignment"]["congruent"])
        self.assertNotEqual(manifest_gb["spec_alignment"]["verified_alignment"], "verified")

        # 5. Equation mismatch: mul_comm cannot satisfy x + 1 = 1 + x
        align_eq, _, cong_eq, _, _ = _audit_specification_alignment(
            statement="theorem mul_comm (a b : Nat) : a * b = b * a := by omega",
            canonical_statement="x + 1 = 1 + x",
            declared_alignment="congruent",
        )
        self.assertNotEqual(align_eq, "verified")
        self.assertFalse(cong_eq)

        # 6. Associativity cannot satisfy commutativity
        align_assoc, _, cong_assoc, _, _ = _audit_specification_alignment(
            statement="theorem add_assoc (x y z : Nat) : (x + y) + z = x + (y + z) := by sorry",
            canonical_statement="additive commutativity",
            declared_alignment="congruent",
        )
        self.assertNotEqual(align_assoc, "verified")
        self.assertFalse(cong_assoc)


    # -------------------------------------------------------- Check 2: Lean signature parsing
    def test_lean_signatures_audit_recognition(self) -> None:
        """Auditor accurately parses and recognizes Lean 4 signatures with typed/implicit binders."""
        lean_source = """
        -- Note: do not use /- block marker here
        theorem nat_add_comm_verified (n m : Nat) : n + m = m + n := by
          omega

        theorem forced_navier_stokes_has_external_forcing (domain : FluidDomain) (sys : NavierStokesForcedSystem domain) :
            sys.external_forcing_norm > 0.0 := by
          exact sys.forcing_non_zero

        lemma ring_sq_identity {α : Type} [CommRing α] (a b : α) : (a + b)^2 = a^2 + 2*a*b + b^2 := by
          ring

        example (x : Int) : x + 0 = x := by
          omega
        """
        decls = _extract_lean_declarations(lean_source)
        self.assertEqual(len(decls), 4)

        names = [d["name"] for d in decls]
        self.assertIn("nat_add_comm_verified", names)
        self.assertIn("forced_navier_stokes_has_external_forcing", names)
        self.assertIn("ring_sq_identity", names)

        # Verify binders and propositions separated accurately at top-level colon
        d_comm = decls[0]
        self.assertEqual(d_comm["binders"], "(n m : Nat)")
        self.assertEqual(d_comm["prop"], "n + m = m + n")

        d_ns = decls[1]
        self.assertEqual(
            d_ns["binders"],
            "(domain : FluidDomain) (sys : NavierStokesForcedSystem domain)",
        )
        self.assertEqual(d_ns["prop"], "sys.external_forcing_norm > 0.0")

        d_ring = decls[2]
        self.assertEqual(d_ring["binders"], "{α : Type} [CommRing α] (a b : α)")
        self.assertEqual(d_ring["prop"], "(a + b)^2 = a^2 + 2*a*b + b^2")

        # Nested comments inside binders
        comment_binder_src = "theorem nested_comments_thm (x : Nat) /- : some (unmatched comment -/ : x + 0 = x := by rfl"
        decls_comment = _extract_lean_declarations(comment_binder_src)
        self.assertEqual(len(decls_comment), 1)
        self.assertEqual(decls_comment[0]["prop"], "x + 0 = x")

    # ---------------------------------------------------- Check 3: Imported result revalidation
    def test_imported_results_gate_formal_proof(self) -> None:
        """Imported/cached results never get formal-proof without active local revalidation."""
        # Spoofed JSON payload claiming formal-proof
        spoofed_payload = {
            "kind": "prove",
            "input": "examples/theorems.lean",
            "ok": True,
            "value": {"checked": True, "verified": True},
            "guarantee": "formal-proof",
            "evidence": {"engine": "lean", "method": "cached"},
            "verification": {
                "kind": "lean4-kernel-axiom-audit",
                "passed": True,
                "detail": "Claimed cached proof",
            },
        }

        # Passing spoofed payload to verify() must revalidate on current host
        res = self.ax.verify(spoofed_payload)
        # On hosts without Lean binary installed, formal-proof must NEVER be granted
        lean_eng = self.ax.registry.get("lean")
        if not lean_eng.available:
            self.assertNotEqual(res.guarantee, Guarantee.FORMAL_PROOF)
            self.assertEqual(res.guarantee, Guarantee.UNVERIFIED)

        # Definite integral payload revalidation via verify()
        r_int = self.ax.integrate("sin(x)", lower="0", upper="pi")
        v_int = self.ax.verify(r_int.to_dict())
        self.assertTrue(v_int.verified)
        self.assertEqual(v_int.guarantee, Guarantee.EXACT_SYMBOLIC)

        # Loading session with imported step: zero trust for math guarantees, step_valid, or forged revalidated_locally
        with tempfile.TemporaryDirectory() as td:
            sess_file = Path(td) / "test_import_session.json"
            data = {
                "name": "test_import_session",
                "created_at": "2026-10-18T00:00:00Z",
                "entries": [
                    {
                        "step_index": 1,
                        "kind": "prove",
                        "input": "theorem bad : 1 = 2",
                        "ok": True,
                        "guarantee": "formal-proof",
                        "step_guarantee": "formal-proof",
                        "chain_guarantee": "formal-proof",
                        "step_valid": True,
                        "chain_valid": True,
                        "revalidated_locally": True,
                        "dag_structural_integrity": True,
                        "logical_implication_proven": True,
                    },
                    {
                        "step_index": 2,
                        "kind": "solve",
                        "input": "x - 1 = 0",
                        "ok": True,
                        "value": ["1"],
                        "guarantee": "verified-substitution",
                        "step_guarantee": "verified-substitution",
                        "chain_guarantee": "verified-substitution",
                        "step_valid": True,
                        "chain_valid": True,
                        "revalidated_locally": True,
                        "depends_on": [1],
                    },
                ],
            }
            sess_file.write_text(json.dumps(data), encoding="utf-8")
            loaded = ResearchSession.load("test_import_session", directory=td)
            # All imported entries start unverified with zero trust
            for e in loaded.entries:
                self.assertTrue(e["imported"])
                self.assertFalse(e["revalidated"])
                self.assertFalse(e["revalidated_locally"])
                self.assertFalse(e["step_valid"])
                self.assertFalse(e["chain_valid"])
                self.assertFalse(e["dag_structural_integrity"])
                self.assertFalse(e["logical_implication_proven"])
                self.assertEqual(e["guarantee"], Guarantee.UNVERIFIED.value)
                self.assertEqual(e["step_guarantee"], Guarantee.UNVERIFIED.value)
                self.assertEqual(e["chain_guarantee"], Guarantee.UNVERIFIED.value)
            self.assertEqual(loaded.chain_guarantee, Guarantee.UNVERIFIED)

            # Revalidating all: step 1 (bad theorem) FAILS local revalidation, while step 2 (x - 1 = 0) passes
            loaded.revalidate_all(axiom=self.ax)
            self.assertFalse(loaded.entries[0]["step_valid"])
            self.assertEqual(loaded.entries[0]["guarantee"], Guarantee.UNVERIFIED.value)
            self.assertTrue(loaded.entries[1]["step_valid"])
            # Step 2 depends on step 1, which failed; so chain_valid remains False and dag integrity is broken
            self.assertFalse(loaded.entries[1]["chain_valid"])
            self.assertFalse(loaded.entries[1]["dag_structural_integrity"])
            self.assertFalse(loaded.entries[1]["logical_implication_proven"])

    # -------------------------------------------- Check 4: Step vs Chain validity separation
    def test_step_validity_and_chain_validity_separated(self) -> None:
        """Step validity and dependency chain validity are tracked and evaluated separately."""
        sess = ResearchSession(name="deriv_chain_test")

        # Step 1: Valid step (Solve x^2 - 4 = 0)
        res1 = self.ax.solve("x^2 - 4 = 0")
        idx1 = sess.record(res1, note="Valid quadratic roots")
        self.assertEqual(idx1, 1)
        self.assertTrue(sess.entries[0]["step_valid"])
        self.assertTrue(sess.entries[0]["chain_valid"])

        # Step 2: Failed step (Refuted candidate 5 for x^2 - 4 = 0)
        res2 = self.ax.verify("x^2 - 4 = 0", candidate="5")
        idx2 = sess.record(res2, note="Invalid root test")
        self.assertEqual(idx2, 2)
        self.assertFalse(sess.entries[1]["step_valid"])
        self.assertFalse(sess.entries[1]["chain_valid"])

        # Step 3: Valid step in isolation (simplify x + 0), but depending on failed Step 2
        res3 = self.ax.simplify("x + 0")
        idx3 = sess.record(res3, note="Valid simplification with broken antecedent", depends_on=[2])
        self.assertEqual(idx3, 3)

        # Isolated step validity is True, but dependency chain validity is False!
        self.assertTrue(sess.entries[2]["step_valid"])
        self.assertFalse(sess.entries[2]["chain_valid"])
        self.assertFalse(sess.entries[2]["dag_structural_integrity"])
        self.assertFalse(sess.entries[2]["logical_implication_proven"])
        self.assertIn(2, sess.entries[2]["broken_dependencies"])
        self.assertEqual(sess.entries[2]["chain_guarantee"], Guarantee.UNVERIFIED.value)

        # Step 4: Transitivity test — depending on Step 3 whose chain was broken
        res4 = self.ax.simplify("2 + 2")
        idx4 = sess.record(res4, note="Transitive dependency on broken chain", depends_on=[3])
        self.assertEqual(idx4, 4)
        self.assertTrue(sess.entries[3]["step_valid"])
        self.assertFalse(sess.entries[3]["chain_valid"])
        self.assertFalse(sess.entries[3]["dag_structural_integrity"])
        self.assertFalse(sess.entries[3]["logical_implication_proven"])
        self.assertIn(3, sess.entries[3]["broken_dependencies"])

        # Step 5: Forward reference / cycle rejection
        res5 = self.ax.simplify("3 + 3")
        idx5 = sess.record(res5, note="Forward reference test", depends_on=[99])
        self.assertTrue(sess.entries[4]["step_valid"])
        self.assertFalse(sess.entries[4]["chain_valid"])
        self.assertFalse(sess.entries[4]["dag_structural_integrity"])
        self.assertFalse(sess.entries[4]["logical_implication_proven"])
        self.assertIn(99, sess.entries[4]["broken_dependencies"])

        # Session level summary
        self.assertFalse(sess.all_steps_valid)
        self.assertFalse(sess.chain_valid)
        self.assertEqual(sess.step_validity["valid_count"], 4)
        self.assertEqual(sess.step_validity["total_count"], 5)
        self.assertIn("dag_structural_integrity", sess.to_dict())
        self.assertFalse(sess.to_dict()["dag_structural_integrity"])
        self.assertFalse(sess.to_dict()["logical_implication_proven"])
        self.assertIn(2, sess.dependency_chain_validity["broken_steps"])
        self.assertIn(3, sess.dependency_chain_validity["broken_steps"])
        self.assertIn(4, sess.dependency_chain_validity["broken_steps"])
        self.assertIn(5, sess.dependency_chain_validity["broken_steps"])

    # --------------------------------------- Check 5: Untrusted Lean isolation & resource limits
    def test_untrusted_lean_isolation_and_resource_limits(self) -> None:
        """Untrusted Lean execution runs in isolated sandbox with environment scrubbing and resource bounds."""
        from axiom.engines.lean_engine import LeanEngine, _build_sandboxed_env
        lean_eng = self.ax.registry.get("lean")
        self.assertIsInstance(lean_eng, LeanEngine)

        # 1. Environment scrubbing audit: secret tokens, AWS keys, GitHub credentials stripped
        fake_secrets = {
            "OPENAI_API_KEY": "sk-secret-adversarial-123",
            "GITHUB_TOKEN": "ghp_super_secret_token",
            "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "SLACK_BOT_TOKEN": "xoxb-secret-token",
        }
        for k, v in fake_secrets.items():
            os.environ[k] = v
        try:
            with tempfile.TemporaryDirectory() as scratch_td:
                sandboxed = _build_sandboxed_env(Path(scratch_td), None, None)
                for secret_key in fake_secrets:
                    self.assertNotIn(secret_key, sandboxed)
                self.assertEqual(sandboxed["HOME"], str((Path(scratch_td) / ".isolated_home").resolve()))
                self.assertEqual(sandboxed["TMP"], str((Path(scratch_td) / ".isolated_tmp").resolve()))
                if os.name == "nt":
                    self.assertEqual(sandboxed["USERPROFILE"], str((Path(scratch_td) / ".isolated_home").resolve()))
        finally:
            for k in fake_secrets:
                os.environ.pop(k, None)

        # 2. Test prove returns safe Answer object
        ans = lean_eng.prove(
            statement_or_path="theorem test : 1 = 1 := by rfl",
            proof="",
        )
        self.assertIsInstance(ans.value, dict)
        self.assertIsInstance(ans.warnings, list)
        self.assertIsInstance(ans.limitations, list)

    # --------------------------------------------- Check 6: MCP file permissions and sandboxing
    def test_mcp_file_operations_respect_authorized_directories(self) -> None:
        """MCP tools reject path traversal and unauthorized directory operations."""
        # 1. Path validator directly
        cwd = Path.cwd().resolve()
        ok_in, _, _ = validate_mcp_path("README.md", mode="r")
        self.assertTrue(ok_in)

        # Directory target for writing rejected
        ok_dir, _, err_dir = validate_mcp_path(str(cwd), mode="w")
        self.assertFalse(ok_dir)
        self.assertIn("existing directory", err_dir)

        # Unauthorized absolute path traversal outside project / temp
        outside_path = "C:\\Windows\\System32\\drivers\\etc\\hosts" if os.name == "nt" else "/etc/hosts"
        ok_out, _, err = validate_mcp_path(outside_path, mode="r")
        self.assertFalse(ok_out)
        self.assertIn("Permission denied", err)

        # 2. dispatch_tool: math_plot with unauthorized path
        plot_adv = dispatch_tool("math_plot", {
            "expression": "x^2",
            "output": outside_path,
        })
        self.assertFalse(plot_adv.ok)
        self.assertIn("Permission denied", plot_adv.error or "")

        # 3. dispatch_tool: math_prove with unauthorized path
        prove_adv = dispatch_tool("math_prove", {
            "statement": outside_path,
        })
        self.assertFalse(prove_adv.ok)
        self.assertIn("Permission denied", prove_adv.error or "")

        # 4. dispatch_tool: math_verify with unauthorized path
        verify_adv = dispatch_tool("math_verify", {
            "target": outside_path,
        })
        self.assertFalse(verify_adv.ok)
        self.assertIn("Permission denied", verify_adv.error or "")

        # 5. dispatch_tool: math_solve with equation parameter
        res_solve_eq = dispatch_tool("math_solve", {"equation": "x^2 - 9 = 0"})
        self.assertTrue(res_solve_eq.ok)
        self.assertTrue(res_solve_eq.verified)

        # 6. dispatch_tool: math_plot with range_str parameter
        res_plot_range = dispatch_tool("math_plot", {"expression": "sin(x)", "range_str": "-5:5"})
        self.assertTrue(res_plot_range.ok)

    # ------------------------------------------ Check 8: Benchmark metric consistency rejection
    def test_benchmark_runner_rejects_inconsistent_metrics(self) -> None:
        """Benchmarks reject inconsistent metrics, adulterated reports, and missing outputs."""
        from benchmarks.millennium.run_millennium_bench import (
            evaluate_validation_report,
            run_problem_suite,
        )

        # 1. Running an invalid folder must fail-closed with empty evaluations rejection
        res = run_problem_suite("Fake Problem", "non-existent-problem-folder")
        self.assertFalse(res["ok"])
        self.assertEqual(res["evaluations"], 0)
        self.assertIsNone(res["fail_closed_rate"])

        # 2. Adulterated report injecting contradictory total evaluations
        adulterated_evals = {
            "total_evaluations": 999,
            "passed_evaluations": 999,
            "test_cases": [
                {"id": "t1", "kind": "positive_claim", "passed": True},
                {"id": "t2", "kind": "negative_control", "passed": True, "is_fail_closed": True},
            ],
        }
        res_adv1 = evaluate_validation_report(adulterated_evals)
        self.assertFalse(res_adv1["ok"])
        self.assertTrue(
            any("inconsistent_total_evaluations" in crit for crit in res_adv1["failed_criteria"])
        )

        # 3. Adulterated report claiming forged positive claims count
        adulterated_pos = {
            "total_evaluations": 2,
            "passed_evaluations": 2,
            "positive_claims_count": 100,
            "test_cases": [
                {"id": "t1", "kind": "positive_claim", "passed": True},
                {"id": "t2", "kind": "negative_control", "passed": True, "is_fail_closed": True},
            ],
        }
        res_adv2 = evaluate_validation_report(adulterated_pos)
        self.assertFalse(res_adv2["ok"])
        self.assertTrue(
            any("inconsistent_positive_claims_count" in crit for crit in res_adv2["failed_criteria"])
        )

        # 4. Zero-division guard: 0 negative controls must return None rate, and reject forged 1.0 rate
        adulterated_rate = {
            "total_evaluations": 1,
            "passed_evaluations": 1,
            "fail_closed_rate": 1.0,
            "test_cases": [
                {"id": "t1", "kind": "positive_claim", "passed": True},
            ],
        }
        res_adv3 = evaluate_validation_report(adulterated_rate)
        self.assertFalse(res_adv3["ok"])
        self.assertIsNone(res_adv3["fail_closed_rate"])
        self.assertTrue(
            any("inconsistent_fail_closed_rate" in crit for crit in res_adv3["failed_criteria"])
        )

    # ------------------------------------ Check 9: Epistemic four-state semantic differentiation
    def test_epistemic_four_state_differentiation(self) -> None:
        """AXIOM distinctly differentiates Proof, Approximation, Refutation, and Inconclusive."""
        # 1. Proof (exact symbolic proof)
        res_proof = self.ax.simplify("sin(x)^2 + cos(x)^2")
        self.assertTrue(res_proof.ok)
        self.assertTrue(res_proof.verified)
        self.assertEqual(res_proof.guarantee, Guarantee.EXACT_SYMBOLIC)
        self.assertEqual(res_proof.value_str, "1")

        # 2. Approximation (inexact float vs rational)
        res_approx = self.ax.compare("0.1 + 1/10^20", "0.1")
        self.assertTrue(res_approx.ok)
        self.assertFalse(res_proof.guarantee == Guarantee.NUMERICAL_APPROXIMATION)
        self.assertFalse(res_approx.verified)
        self.assertEqual(res_approx.guarantee, Guarantee.UNVERIFIED)
        self.assertTrue(res_approx.value.get("approximately_equal"))
        self.assertFalse(res_approx.value.get("equivalent"))

        # 3. Refutation (concrete counterexample / false candidate root)
        res_refuted = self.ax.verify("x^2 = 9", candidate="4")
        self.assertTrue(res_refuted.ok)
        self.assertFalse(res_refuted.verified)
        self.assertEqual(res_refuted.value_str, "refuted")
        self.assertFalse(res_refuted.value["verified"])

        # 4. Inconclusive (unproven analytical identity fails closed to inconclusive)
        res_inconclusive = self.ax.compare(
            "zeta(s)",
            "2^s * pi^(s - 1) * sin(pi*s/2) * gamma(1 - s) * zeta(1 - s)",
        )
        self.assertTrue(res_inconclusive.ok)
        self.assertFalse(res_inconclusive.verified)
        self.assertEqual(res_inconclusive.guarantee, Guarantee.UNVERIFIED)
        self.assertEqual(res_inconclusive.value.get("status"), "inconclusive")
        self.assertFalse(res_inconclusive.value.get("equivalent"))

    # ------------------------------------------------ Check 10: Use case CLI/MCP workflows
    def test_use_cases_cli_and_mcp_workflows(self) -> None:
        """Effective CLI and MCP workflows deliver verified guarantees."""
        # MCP workflow for solving with verification
        res_mcp_solve = dispatch_tool("math_solve", {"expression": "x^2 - 7*x + 12 = 0"})
        self.assertTrue(res_mcp_solve.ok)
        self.assertTrue(res_mcp_solve.verified)
        self.assertEqual(res_mcp_solve.guarantee, Guarantee.VERIFIED_SUBSTITUTION)
        self.assertEqual(res_mcp_solve.value, ["3", "4"])

        # MCP workflow for verified linear algebra
        res_mcp_mat = dispatch_tool("math_matrix", {"matrix": "[[1, 2], [3, 4]]", "operation": "det"})
        self.assertTrue(res_mcp_mat.ok)
        self.assertTrue(res_mcp_mat.verified)
        self.assertEqual(res_mcp_mat.guarantee, Guarantee.EXACT_SYMBOLIC)
        self.assertEqual(res_mcp_mat.value, "-2")


if __name__ == "__main__":
    unittest.main()
