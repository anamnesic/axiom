"""Comprehensive test suite for the AXIOM Mathematical Reasoning Engine.

Compatible with both ``pytest`` and standard-library ``python -m unittest``.
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

# Ensure `src/` is importable when running `python -m unittest` from repo root
_SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from axiom import (  # noqa: E402
    TOOL_DEFINITIONS,
    Axiom,
    Guarantee,
    ParseError,
    Parser,
    dispatch_tool,
    solve_expression,
)
from axiom.cli import main as cli_main  # noqa: E402
from axiom.cli import render_box  # noqa: E402
from axiom.mcp_server import handle_jsonrpc_message  # noqa: E402
from axiom.setup_agent import configure_clients, run_doctor  # noqa: E402


class TestAxiom(unittest.TestCase):
    # ----------------------------------------------------------------- parser

    def test_parser_implicit_multiplication_and_caret(self) -> None:
        parser = Parser()
        eq = parser.parse_equation("x^2 - 5x + 6 = 0")
        self.assertEqual(str(eq), "Eq(x**2 - 5*x + 6, 0)")

    def test_parser_blocks_unsafe_constructs(self) -> None:
        parser = Parser()
        for malicious in (
            "__import__('os').system('echo pwned')",
            "(1).__class__.__mro__",
            "eval('1+1')",
            "lambda x: x",
        ):
            with self.assertRaises(ParseError):
                parser.parse(malicious)

    # ------------------------------------------------------ guarantee ranking

    def test_guarantee_hierarchy(self) -> None:
        self.assertTrue(Guarantee.FORMAL_PROOF.at_least(Guarantee.EXACT_SYMBOLIC))
        self.assertTrue(Guarantee.EXACT_SYMBOLIC.at_least(Guarantee.VERIFIED_SUBSTITUTION))
        self.assertTrue(
            Guarantee.VERIFIED_SUBSTITUTION.at_least(Guarantee.NUMERICAL_APPROXIMATION)
        )
        self.assertTrue(Guarantee.NUMERICAL_APPROXIMATION.at_least(Guarantee.HEURISTIC))
        self.assertTrue(Guarantee.HEURISTIC.at_least(Guarantee.UNVERIFIED))
        self.assertEqual(
            Guarantee.EXACT_SYMBOLIC.weakest(Guarantee.VERIFIED_SUBSTITUTION),
            Guarantee.VERIFIED_SUBSTITUTION,
        )

    # ---------------------------------------------------------- core: algebra

    def test_solve_quadratic_verified_substitution(self) -> None:
        ax = Axiom()
        res = ax.solve("x^2 - 5*x + 6 = 0")
        self.assertTrue(res.ok)
        self.assertEqual(res.value, ["2", "3"])
        self.assertTrue(res.verified)
        self.assertEqual(res.guarantee, Guarantee.VERIFIED_SUBSTITUTION)
        self.assertIsNotNone(res.evidence)
        assert res.evidence is not None
        self.assertEqual(res.evidence.engine, "sympy")

    def test_solve_system_verified_substitution(self) -> None:
        ax = Axiom()
        res = ax.solve("x + y = 5; x - y = 1")
        self.assertTrue(res.ok)
        self.assertTrue(res.verified)
        self.assertEqual(res.guarantee, Guarantee.VERIFIED_SUBSTITUTION)
        self.assertEqual(res.value, [{"x": "3", "y": "2"}])

    def test_simplify_and_trig_identity(self) -> None:
        ax = Axiom()
        res = ax.simplify("sin(x)^2 + cos(x)^2")
        self.assertTrue(res.ok)
        self.assertEqual(res.value, "1")
        self.assertTrue(res.verified)
        self.assertEqual(res.guarantee, Guarantee.EXACT_SYMBOLIC)

    def test_factor_and_expand(self) -> None:
        ax = Axiom()
        factored = ax.factor("x^2 - 5*x + 6")
        self.assertTrue(factored.ok and factored.verified)
        self.assertEqual(factored.guarantee, Guarantee.EXACT_SYMBOLIC)

        expanded = ax.expand("(x - 2)*(x - 3)")
        self.assertTrue(expanded.ok and expanded.verified)
        self.assertEqual(expanded.value, "x**2 - 5*x + 6")

    def test_evaluate_symbolic_and_numeric(self) -> None:
        ax = Axiom()
        exact = ax.evaluate("sqrt(2)^2 + Rational(1, 3)")
        self.assertTrue(exact.ok)
        self.assertEqual(exact.value, "7/3")
        self.assertEqual(exact.guarantee, Guarantee.EXACT_SYMBOLIC)

        approx = ax.evaluate("pi", precision=30)
        self.assertTrue(approx.ok)
        self.assertTrue(approx.value.startswith("3.1415926535897932384626433832"))
        self.assertEqual(approx.guarantee, Guarantee.NUMERICAL_APPROXIMATION)

    # --------------------------------------------------------- core: calculus

    def test_differentiate_verified(self) -> None:
        ax = Axiom()
        res = ax.differentiate("x^3 * sin(x)", variable="x")
        self.assertTrue(res.ok)
        self.assertTrue(res.verified)
        self.assertEqual(res.guarantee, Guarantee.EXACT_SYMBOLIC)

    def test_integrate_indefinite_verified_by_differentiation(self) -> None:
        ax = Axiom()
        res = ax.integrate("sin(x)^2", variable="x")
        self.assertTrue(res.ok)
        self.assertTrue(res.verified)
        self.assertEqual(res.guarantee, Guarantee.EXACT_SYMBOLIC)
        assert res.verification is not None
        self.assertEqual(res.verification.kind, "differentiate-antiderivative")

    def test_integrate_definite_verified_by_quadrature(self) -> None:
        ax = Axiom()
        res = ax.integrate("sin(x)", variable="x", lower="0", upper="pi")
        self.assertTrue(res.ok)
        self.assertEqual(res.value, "2")
        self.assertTrue(res.verified)
        self.assertEqual(res.guarantee, Guarantee.EXACT_SYMBOLIC)

    def test_limit_and_series(self) -> None:
        ax = Axiom()
        lim = ax.limit("sin(x)/x", variable="x", point="0")
        self.assertTrue(lim.ok)
        self.assertEqual(lim.value, "1")
        self.assertTrue(lim.verified)
        self.assertEqual(lim.guarantee, Guarantee.EXACT_SYMBOLIC)

        ser = ax.series("exp(x)", variable="x", point="0", order=4)
        self.assertTrue(ser.ok)
        self.assertIn("x**3/6", ser.value)

    # --------------------------------------------- core: compare & verify

    def test_compare_equivalent_and_non_equivalent(self) -> None:
        ax = Axiom()
        eq_res = ax.compare("(x + 1)^2", "x^2 + 2*x + 1")
        self.assertTrue(eq_res.ok)
        self.assertIs(eq_res.value["equivalent"], True)
        self.assertEqual(eq_res.guarantee, Guarantee.EXACT_SYMBOLIC)

        neq_res = ax.compare("(x + 1)^2", "x^2 + 1")
        self.assertTrue(neq_res.ok)
        self.assertIs(neq_res.value["equivalent"], False)
        self.assertEqual(neq_res.guarantee, Guarantee.UNVERIFIED)
        assert neq_res.verification is not None
        self.assertFalse(neq_res.verification.passed)

    def test_verify_accepts_true_roots_and_rejects_false_roots(self) -> None:
        ax = Axiom()
        good = ax.verify("x^2 - 5*x + 6 = 0", candidate=["2", "3"])
        self.assertTrue(good.ok and good.verified)
        self.assertEqual(good.guarantee, Guarantee.VERIFIED_SUBSTITUTION)

        bad = ax.verify("x^2 - 5*x + 6 = 0", candidate=["2", "4"])
        self.assertTrue(bad.ok and not bad.verified)
        self.assertEqual(bad.guarantee, Guarantee.UNVERIFIED)

        # Re-verify from saved JSON file (`axiom verify solution.json`)
        solved = solve_expression("x^2 - 5*x + 6 = 0")
        with tempfile.TemporaryDirectory() as td:
            json_file = Path(td) / "solution.json"
            json_file.write_text(solved.to_json(), encoding="utf-8")
            from_file = ax.verify(str(json_file))
            self.assertTrue(from_file.ok and from_file.verified)
            self.assertEqual(from_file.guarantee, Guarantee.VERIFIED_SUBSTITUTION)

    # ----------------------------------- core: explain, explore, plot, prove

    def test_explain_explore_plot_prove(self) -> None:
        ax = Axiom()
        exp = ax.explain("x^2 - 5*x + 6 = 0", operation="solve")
        self.assertTrue(exp.ok and exp.verified)
        self.assertTrue(
            any("Factored form" in step for step in exp.value["explanation"])
        )

        xpl = ax.explore("x^3 - 3*x", variable="x")
        self.assertTrue(xpl.ok)
        self.assertEqual(xpl.value["parity"], "odd")
        self.assertEqual(set(xpl.value["critical_points"]), {"-1", "1"})

        with tempfile.TemporaryDirectory() as td:
            svg_out = Path(td) / "sinc.svg"
            plt_res = ax.plot(
                "sin(x)/x", range_=(-10.0, 10.0), points=21, output=str(svg_out)
            )
            self.assertTrue(plt_res.ok)
            self.assertEqual(plt_res.value["valid_points"], 21)
            self.assertIn("<svg", plt_res.value["svg"])
            self.assertTrue(len(plt_res.value["ascii_preview"].splitlines()) == 11)
            self.assertTrue(svg_out.exists())
            self.assertIn("<polyline", svg_out.read_text(encoding="utf-8"))

        # Proof containing 'sorry' must never receive FORMAL_PROOF guarantee
        sorry_proof = ax.prove("theorem t (x : Nat) : x = x :=", proof="by sorry")
        self.assertEqual(sorry_proof.guarantee, Guarantee.UNVERIFIED)
        self.assertFalse(sorry_proof.verified)

    # ------------------------- v0.2 domains: matrix, ode, nt, optimize, stats, tensor, mathlib

    def test_tensor_differential_geometry_verified(self) -> None:
        ax = Axiom()
        # 2D Polar coordinates: flat plane -> R = 0, Gamma^r_{theta,theta} = -r
        polar = ax.tensor("polar")
        self.assertTrue(polar.ok and polar.verified)
        self.assertEqual(polar.guarantee, Guarantee.VERIFIED_SUBSTITUTION)
        self.assertEqual(polar.value["ricci_scalar"], "0")
        self.assertEqual(
            polar.value["nonzero_christoffel"]["Gamma^r_{theta,theta}"], "-r"
        )

        # Unit 2-sphere: constant positive Gaussian curvature K=1 -> Ricci scalar R = 2
        sphere = ax.tensor("sphere")
        self.assertTrue(sphere.ok and sphere.verified)
        self.assertEqual(sphere.guarantee, Guarantee.VERIFIED_SUBSTITUTION)
        self.assertEqual(sphere.value["ricci_scalar"], "2")

        # Custom metric tensor literal
        custom = ax.tensor("[[1, 0], [0, r^2]]", coordinates=["r", "theta"], operation="christoffel")
        self.assertTrue(custom.ok and custom.verified)
        self.assertEqual(custom.guarantee, Guarantee.VERIFIED_SUBSTITUTION)

    def test_search_mathlib_catalog(self) -> None:
        ax = Axiom()
        res = ax.search_mathlib("sin_sq_add_cos_sq")
        self.assertTrue(res.ok and res.verified)
        self.assertEqual(res.guarantee, Guarantee.CATALOG_LOOKUP)
        self.assertFalse(res.guarantee.is_mathematical_claim)
        self.assertGreaterEqual(res.value["count"], 1)
        self.assertEqual(res.value["results"][0]["name"], "Real.sin_sq_add_cos_sq")

        fermat = ax.search_mathlib("fermat little prime")
        self.assertTrue(fermat.ok and fermat.verified)
        self.assertEqual(fermat.guarantee, Guarantee.CATALOG_LOOKUP)
        names = [r["name"] for r in fermat.value["results"]]
        self.assertIn("ZMod.fermat_little", names)

        no_match = ax.search_mathlib("nonexistent_theorem_xyz_999999")
        self.assertTrue(no_match.ok and not no_match.verified)
        self.assertEqual(no_match.guarantee, Guarantee.UNVERIFIED)

    def test_matrix_operations_verified(self) -> None:
        ax = Axiom()
        eig = ax.matrix("[[4, 1], [2, 3]]", operation="eigen")
        self.assertTrue(eig.ok and eig.verified)
        self.assertEqual(eig.guarantee, Guarantee.VERIFIED_SUBSTITUTION)

        inv = ax.matrix("[[1, 2], [3, 5]]", operation="inv")
        self.assertTrue(inv.ok and inv.verified)
        self.assertEqual(inv.guarantee, Guarantee.VERIFIED_SUBSTITUTION)

        lu = ax.matrix("[[2, 1], [4, 3]]", operation="lu")
        self.assertTrue(lu.ok and lu.verified)
        self.assertEqual(lu.guarantee, Guarantee.EXACT_SYMBOLIC)

        sol = ax.matrix("[[2, 1], [1, 3]]", operation="solve", rhs="[[5], [10]]")
        self.assertTrue(sol.ok and sol.verified)
        self.assertEqual(sol.value, [["1"], ["3"]])
        self.assertEqual(sol.guarantee, Guarantee.VERIFIED_SUBSTITUTION)

        det = ax.matrix("[[1, 2], [3, 4]]", operation="det")
        self.assertTrue(det.ok and det.verified)
        self.assertEqual(det.value, "-2")

    def test_ode_verified_by_substitution(self) -> None:
        ax = Axiom()
        res = ax.ode("diff(y(x), x) + 2*y(x) = exp(x)")
        self.assertTrue(res.ok and res.verified)
        self.assertEqual(res.guarantee, Guarantee.VERIFIED_SUBSTITUTION)

    def test_number_theory_verified(self) -> None:
        ax = Axiom()
        fac = ax.number_theory("factorint", n=360)
        self.assertTrue(fac.ok and fac.verified)
        self.assertEqual(fac.value, {"2": 3, "3": 2, "5": 1})
        self.assertEqual(fac.guarantee, Guarantee.VERIFIED_SUBSTITUTION)

        bez = ax.number_theory("extgcd", a=240, b=46)
        self.assertTrue(bez.ok and bez.verified)
        self.assertEqual(bez.value["gcd"], 2)
        self.assertEqual(bez.guarantee, Guarantee.VERIFIED_SUBSTITUTION)

        crt = ax.number_theory("crt", remainders=[2, 3, 2], moduli=[3, 5, 7])
        self.assertTrue(crt.ok and crt.verified)
        self.assertEqual(crt.value["x"], 23)
        self.assertEqual(crt.guarantee, Guarantee.VERIFIED_SUBSTITUTION)

    def test_optimize_and_statistics_verified(self) -> None:
        ax = Axiom()
        opt = ax.optimize("x^2 - 4*x + 5", mode="minimize")
        self.assertTrue(opt.ok and opt.verified)
        self.assertEqual(opt.value["point"], "2")
        self.assertEqual(opt.value["objective_value"], "1")
        self.assertEqual(opt.guarantee, Guarantee.VERIFIED_SUBSTITUTION)

        st = ax.statistics("2, 4, 4, 4, 5, 5, 7, 9")
        self.assertTrue(st.ok and st.verified)
        self.assertEqual(st.value["mean"], "5")
        self.assertEqual(st.value["population_variance"], "4")
        self.assertEqual(st.guarantee, Guarantee.EXACT_SYMBOLIC)

    def test_research_session_and_auto_formalization(self) -> None:
        from axiom.engines.lean_engine import LeanEngine

        lean_code = LeanEngine.formalize_equality("(x + y)^2 = x^2 + 2*x*y + y^2")
        self.assertIn("theorem axiom_identity (x y : Int)", lean_code)
        self.assertIn("by ring", lean_code)

        ax = Axiom()
        self.assertEqual(
            ax.registry.names(),
            ["sympy", "numeric", "lean", "sagemath", "julia"],
        )

        with tempfile.TemporaryDirectory() as td:
            r1 = ax.session(
                "record",
                name="demo",
                expression="sin(x)^2 + cos(x)^2",
                operation="simplify",
                note="Pythagorean trig identity",
                directory=td,
            )
            self.assertTrue(r1.ok)
            self.assertEqual(r1.guarantee, Guarantee.EXACT_SYMBOLIC)

            r2 = ax.session(
                "record",
                name="demo",
                expression="x^2 - 5*x + 6 = 0",
                operation="solve",
                note="Quadratic roots",
                directory=td,
            )
            self.assertTrue(r2.ok)
            # Weakest link between EXACT_SYMBOLIC and VERIFIED_SUBSTITUTION is VERIFIED_SUBSTITUTION
            self.assertEqual(r2.guarantee, Guarantee.VERIFIED_SUBSTITUTION)

            r3 = ax.session(
                "hypothesis",
                name="demo",
                hypothesis="(x + 1)^2 = x^2 + 2*x + 1",
                directory=td,
            )
            self.assertEqual(r3.value["hypotheses"][0]["status"], "verified")

            exp = ax.session("export", name="demo", directory=td)
            self.assertIn("# AXIOM Research Session: `demo`", exp.value_str)
            self.assertIn("VERIFIED", exp.value_str)

            # Direct result recording
            res_direct = ax.solve("2*x - 4 = 0")
            r4 = ax.session("record", name="demo", result=res_direct, note="Direct result recording", directory=td)
            self.assertTrue(r4.ok)

            # Direct file recording
            sample_lean = Path(td) / "sample.lean"
            sample_lean.write_text("theorem test_thm (n : Nat) : n + 0 = n := rfl\n", encoding="utf-8")
            r5 = ax.session("record", name="demo", file=sample_lean, note="Direct file recording", directory=td)
            self.assertTrue(r5.ok)

    # ------------------------------------------------- setup, doctor, CLI, MCP

    def test_doctor_and_setup_with_backup(self) -> None:
        doc = run_doctor()
        self.assertTrue(doc["ok"])
        self.assertEqual(doc["mcp_tools_count"], 21)

        with tempfile.TemporaryDirectory() as td:
            fake_home = Path(td)
            claude_cfg = fake_home / ".claude.json"
            claude_cfg.write_text('{"existing": true}\n', encoding="utf-8")
            codex_cfg = fake_home / ".codex" / "config.toml"
            codex_cfg.parent.mkdir(parents=True, exist_ok=True)
            codex_cfg.write_text('model = "o3"\n', encoding="utf-8")

            dry = configure_clients(
                clients=["claude-code", "codex"], apply=False, home=fake_home
            )
            self.assertFalse(dry["applied"])
            self.assertEqual(dry["clients"][0]["status"], "dry-run")
            self.assertIn("codex mcp add axiom", dry["clients"][1]["cli_command"])

            applied = configure_clients(
                clients=["claude-code", "cursor", "codex", "antigravity", "agy"], apply=True, home=fake_home
            )
            self.assertTrue(applied["applied"])
            self.assertTrue((fake_home / ".claude.json.axiom.bak").exists())
            self.assertTrue((fake_home / ".codex" / "config.toml.axiom.bak").exists())
            merged = json.loads(claude_cfg.read_text(encoding="utf-8"))
            self.assertTrue(merged["existing"])
            self.assertIn("axiom", merged["mcpServers"])

            agy_cfg = fake_home / ".gemini" / "config" / "mcp_config.json"
            self.assertTrue(agy_cfg.exists())
            agy_data = json.loads(agy_cfg.read_text(encoding="utf-8"))
            self.assertIn("axiom", agy_data["mcpServers"])

            toml_text = codex_cfg.read_text(encoding="utf-8")
            self.assertIn('model = "o3"', toml_text)
            self.assertIn("[mcp_servers.axiom]", toml_text)
            self.assertIn("axiom.mcp_server", toml_text)

    def test_lean4_axiom_audit_and_lake_environment(self) -> None:
        from unittest.mock import MagicMock, patch
        from axiom.engines.lean_engine import LeanEngine

        # 1. prepare_audited_source injects #print axioms and ignores 'sorry' inside comments
        src = (
            "-- this comment mentions sorry but the proof is complete\n"
            "theorem add_zero_right (n : Nat) : n + 0 = n := by rfl\n"
            "example (a : Nat) : a = a := by rfl\n"
        )
        audited, thms, custom_ax, has_hole = LeanEngine.prepare_audited_source(src)
        self.assertFalse(has_hole)
        self.assertEqual(custom_ax, [])
        self.assertEqual(thms, ["add_zero_right", "_axiom_example_1"])
        self.assertIn("#print axioms add_zero_right", audited)
        self.assertIn("#print axioms _axiom_example_1", audited)

        # 1b. Namespaces and nested sections correctly qualify theorem names
        ns_src = (
            "namespace Algebra\n"
            "section Sub\n"
            "theorem sub_thm (x : Nat) : x = x := by rfl\n"
            "end Sub\n"
            "end Algebra\n"
        )
        ns_audited, ns_thms, _, _ = LeanEngine.prepare_audited_source(ns_src)
        self.assertEqual(ns_thms, ["Algebra.sub_thm"])
        self.assertIn("#print axioms Algebra.sub_thm", ns_audited)
        cov_ns, _ = LeanEngine.verify_theorem_audit_coverage(["sub_thm"], ["Algebra.sub_thm"])
        self.assertTrue(cov_ns)
        cov_ns2, _ = LeanEngine.verify_theorem_audit_coverage(["Algebra.sub_thm"], ["Algebra.sub_thm"])
        self.assertTrue(cov_ns2)

        # 2. User-declared `axiom` or `unsafe` in source is caught and rejected
        bad_src = (
            "axiom bogus : 1 = 2\n"
            "theorem fake : 1 = 2 := bogus\n"
        )
        _, _, bad_custom_ax, _ = LeanEngine.prepare_audited_source(bad_src)
        self.assertEqual(bad_custom_ax, ["bogus"])
        ax_res = Axiom().prove(bad_src)
        self.assertFalse(ax_res.verified)
        self.assertEqual(ax_res.guarantee, Guarantee.UNVERIFIED)

        # 3. parse_axiom_audit & verify_theorem_audit_coverage require confirmed #print axioms output
        clean_diag = [
            "'thm1' depends on axioms: [propext, Classical.choice, Quot.sound]",
            "'thm2' does not depend on any axioms",
        ]
        used, untrusted, has_sorry = LeanEngine.parse_axiom_audit(clean_diag)
        audited_thms = LeanEngine.extract_audited_theorems(clean_diag)
        self.assertEqual(used, ["propext", "Classical.choice", "Quot.sound"])
        self.assertEqual(untrusted, [])
        self.assertFalse(has_sorry)
        self.assertEqual(audited_thms, ["thm1", "thm2"])
        cov_ok, missing = LeanEngine.verify_theorem_audit_coverage(["thm1", "thm2"], audited_thms)
        self.assertTrue(cov_ok)
        self.assertEqual(missing, [])

        # Missing #print axioms output or empty theorem list must fail coverage
        cov_empty, _ = LeanEngine.verify_theorem_audit_coverage([], [])
        self.assertFalse(cov_empty)
        cov_partial, missing_partial = LeanEngine.verify_theorem_audit_coverage(
            ["thm1", "thm2"], ["thm1"]
        )
        self.assertFalse(cov_partial)
        self.assertEqual(missing_partial, ["thm2"])

        tainted_diag = [
            "'thm_bad' depends on axioms: [propext, my_secret_axiom, sorryAx]",
        ]
        used2, untrusted2, has_sorry2 = LeanEngine.parse_axiom_audit(tainted_diag)
        self.assertIn("my_secret_axiom", untrusted2)
        self.assertTrue(has_sorry2)

        # 4. Declaration-free Lean source (-- comment / #check) must NEVER receive FORMAL_PROOF
        # even if the Lean binary exits with returncode == 0
        ax = Axiom()
        lean_eng = ax.registry.get("lean")
        with patch.object(lean_eng, "lean_bin", "/usr/bin/lean"), patch(
            "axiom.engines.lean_engine.subprocess.run"
        ) as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Nat : Type\n", stderr="")
            no_thm_res = ax.prove("-- just a comment\n#check Nat")
            self.assertFalse(no_thm_res.verified)
            self.assertEqual(no_thm_res.guarantee, Guarantee.UNVERIFIED)

            # Theorem declared, but Lean stdout did not confirm #print axioms -> UNVERIFIED
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            unconfirmed_res = ax.prove("theorem t (n : Nat) : n = n := rfl")
            self.assertFalse(unconfirmed_res.verified)
            self.assertEqual(unconfirmed_res.guarantee, Guarantee.UNVERIFIED)

            # Theorem declared AND confirmed by #print axioms -> FORMAL_PROOF
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="'t' does not depend on any axioms\n",
                stderr="",
            )
            confirmed_res = ax.prove("theorem t (n : Nat) : n = n := rfl")
            self.assertTrue(confirmed_res.verified)
            self.assertEqual(confirmed_res.guarantee, Guarantee.FORMAL_PROOF)

        # 5. Lake project detection (`lake env lean`)
        with tempfile.TemporaryDirectory() as td:
            proj = Path(td)
            (proj / "lakefile.lean").write_text("-- lake project\n", encoding="utf-8")
            sub_dir = proj / "MyPkg"
            sub_dir.mkdir()
            thm_file = sub_dir / "Basic.lean"
            thm_file.write_text("theorem t : 1 = 1 := rfl\n", encoding="utf-8")

            found_root = LeanEngine.find_lake_project_root(thm_file)
            self.assertEqual(found_root, proj.resolve())

            eng = LeanEngine()
            eng.lake_bin = "/usr/bin/lake"
            cmd, cwd = eng.build_lean_command(thm_file, origin_path=thm_file)
            self.assertEqual(cmd[:3], ["/usr/bin/lake", "env", "lean"])
            self.assertEqual(cwd, str(proj.resolve()))

    def test_lean4_live_kernel_and_lake_integration(self) -> None:
        import os
        from axiom.engines.lean_engine import LeanEngine

        eng = LeanEngine()
        if os.environ.get("AXIOM_REQUIRE_LEAN") == "1":
            self.assertTrue(
                eng.available,
                "AXIOM_REQUIRE_LEAN=1 is set, but Lean 4 binary was not found",
            )
            self.assertIsNotNone(
                eng.lake_bin,
                "AXIOM_REQUIRE_LEAN=1 is set, but Lake binary was not found",
            )
        if not eng.available:
            return

        ax = Axiom()
        # 1. Verify Lake project file via `lake env lean`
        lake_test_file = (
            Path(__file__).resolve().parent / "lean_project" / "AxiomFormalTests.lean"
        )
        res_file = ax.prove(str(lake_test_file))
        self.assertTrue(res_file.ok and res_file.verified, msg=res_file.to_json())
        self.assertEqual(res_file.guarantee, Guarantee.FORMAL_PROOF)
        assert res_file.verification is not None
        self.assertEqual(
            res_file.verification.data["audited_theorems"],
            ["nat_add_comm_verified", "int_linear_identity"],
        )

        # 2. Valid classical proof using Classical.choice & propext
        res_classical = ax.prove(
            "open Classical in\ntheorem em_holds (P : Prop) : P ∨ ¬P := em P"
        )
        self.assertTrue(res_classical.ok and res_classical.verified)
        self.assertEqual(res_classical.guarantee, Guarantee.FORMAL_PROOF)
        assert res_classical.verification is not None
        self.assertIn("Classical.choice", res_classical.verification.data["axioms_used"])

        # 3. Valid anonymous example rewritten and audited via #print axioms
        res_ex = ax.prove("example (a b : Nat) : a + b = b + a := by omega")
        self.assertTrue(res_ex.ok and res_ex.verified)
        self.assertEqual(res_ex.guarantee, Guarantee.FORMAL_PROOF)

        # 4. Invalid proof with `sorry` -> rejected as UNVERIFIED
        res_sorry = ax.prove("theorem bad_sorry (n : Nat) : n = n + 1 := by sorry")
        self.assertFalse(res_sorry.verified)
        self.assertEqual(res_sorry.guarantee, Guarantee.UNVERIFIED)

        # 5. Sneaky proof with user-declared `axiom` -> rejected by #print axioms audit
        res_custom_ax = ax.prove(
            "axiom fake_eq : 1 = 2\ntheorem bad_ax : 1 = 2 := fake_eq"
        )
        self.assertFalse(res_custom_ax.verified)
        self.assertEqual(res_custom_ax.guarantee, Guarantee.UNVERIFIED)
        assert res_custom_ax.verification is not None
        self.assertIn("fake_eq", res_custom_ax.verification.data["untrusted_axioms"])

        # 6. Declaration-free file (#check only) -> rejected as UNVERIFIED
        res_empty = ax.prove("-- no theorem here\n#check Nat")
        self.assertFalse(res_empty.verified)
        self.assertEqual(res_empty.guarantee, Guarantee.UNVERIFIED)

        # 7. False statement with failing tactic -> rejected by Lean kernel
        res_false = ax.prove("theorem wrong : 1 + 1 = 3 := by rfl")
        self.assertFalse(res_false.verified)
        self.assertEqual(res_false.guarantee, Guarantee.UNVERIFIED)

    def test_verifiers_never_elevate_without_evidence(self) -> None:
        import sympy as sp
        from axiom.verification import (
            _is_symbolic_zero,
            verify_derivative,
            verify_integral,
            verify_limit,
        )

        x = sp.Symbol("x")
        a = sp.Symbol("a")

        # Small non-zero Float must NEVER be treated as exact symbolic zero via nsimplify
        self.assertFalse(_is_symbolic_zero(sp.Float("1e-16")))
        self.assertTrue(_is_symbolic_zero(sp.sin(x) ** 2 + sp.cos(x) ** 2 - 1))

        # False definite integral must be rejected as UNVERIFIED
        ver_bad, guar_bad = verify_integral(
            sp.sin(x), sp.Integer(99), x, limits=(sp.Integer(0), sp.pi)
        )
        self.assertFalse(ver_bad.passed)
        self.assertEqual(guar_bad, Guarantee.UNVERIFIED)

        # Definite integral with perturbed rational value within quadrature tolerance (2 + 1e-11)
        # passes numerical quadrature but is NOT an exact symbolic identity -> NUMERICAL_APPROXIMATION
        perturbed_two = sp.Rational(200000000001, 100000000000)
        ver_quad_only, guar_quad_only = verify_integral(
            sp.sin(x), perturbed_two, x, limits=(sp.Integer(0), sp.pi)
        )
        self.assertTrue(ver_quad_only.passed)
        self.assertEqual(ver_quad_only.kind, "numerical-quadrature")
        self.assertEqual(guar_quad_only, Guarantee.NUMERICAL_APPROXIMATION)

        # Parametric definite integral: verified via independent FTC antiderivative check
        ver_param, guar_param = verify_integral(
            2 * x, a**2, x, limits=(sp.Integer(0), a)
        )
        self.assertTrue(ver_param.passed)
        self.assertEqual(ver_param.kind, "ftc-antiderivative-check")
        self.assertEqual(guar_param, Guarantee.EXACT_SYMBOLIC)

        # Wrong parametric definite integral must be rejected as UNVERIFIED
        ver_param_bad, guar_param_bad = verify_integral(
            2 * x, a**3, x, limits=(sp.Integer(0), a)
        )
        self.assertFalse(ver_param_bad.passed)
        self.assertEqual(guar_param_bad, Guarantee.UNVERIFIED)

        # Unevaluated integral must return UNVERIFIED
        uneval = sp.Integral(sp.exp(x**3), x)
        ver_un, guar_un = verify_integral(sp.exp(x**3), uneval, x)
        self.assertFalse(ver_un.passed)
        self.assertEqual(guar_un, Guarantee.UNVERIFIED)

        # Oscillatory limit (AccumBounds) must be rejected as UNVERIFIED
        ver_lim, guar_lim = verify_limit(
            sp.sin(x), x, sp.oo, "+-", sp.AccumBounds(-1, 1)
        )
        self.assertFalse(ver_lim.passed)
        self.assertEqual(guar_lim, Guarantee.UNVERIFIED)

        # Limit confirmed only by numerical sequence probing at infinity -> NUMERICAL_APPROXIMATION
        ver_lim_num, guar_lim_num = verify_limit(
            1 / x, x, sp.oo, "+-", sp.Integer(0)
        )
        self.assertTrue(ver_lim_num.passed)
        self.assertEqual(guar_lim_num, Guarantee.NUMERICAL_APPROXIMATION)

        # Derivative that only matches numerically within tolerance (perturbed by 1e-13)
        # must receive NUMERICAL_APPROXIMATION, never EXACT_SYMBOLIC
        ver_d_num, guar_d_num = verify_derivative(
            sp.sin(x), sp.cos(x) + sp.Float("1e-13"), x
        )
        self.assertTrue(ver_d_num.passed)
        self.assertEqual(guar_d_num, Guarantee.NUMERICAL_APPROXIMATION)

        # Derivative that fails evaluation everywhere must return UNVERIFIED
        undef_fn = sp.Function("undef_fn")(x)
        ver_d, guar_d = verify_derivative(undef_fn, sp.Integer(0), x)
        self.assertFalse(ver_d.passed)
        self.assertEqual(guar_d, Guarantee.UNVERIFIED)

    def test_python310_fstring_compatibility(self) -> None:
        import ast

        repo_root = Path(__file__).resolve().parent.parent
        for py_file in repo_root.rglob("*.py"):
            src = py_file.read_text(encoding="utf-8")
            # On Python 3.10, ast.parse itself raises SyntaxError on backslashes in f-strings.
            tree = ast.parse(src, filename=str(py_file))
            if sys.version_info >= (3, 12):
                for node in ast.walk(tree):
                    if isinstance(node, ast.FormattedValue):
                        seg = ast.get_source_segment(src, node) or ""
                        self.assertNotIn(
                            "\\",
                            seg,
                            f"Python 3.10 incompatible backslash inside f-string at {py_file}:{node.lineno}",
                        )

    def test_cli_box_and_json_output(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main(["solve", "x^2 - 5*x + 6 = 0", "--json"])
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["value"], ["2", "3"])
        self.assertEqual(payload["guarantee"], "verified-substitution")

        res = solve_expression("x^2 - 5*x + 6 = 0")
        box = render_box(res)
        self.assertIn("VERIFIED-SUBSTITUTION", box)
        self.assertIn("┌─", box)
        self.assertIn("└─", box)

    def test_cli_negative_expression_leading_dash(self) -> None:
        """Ensure expressions with leading '-' can be passed to CLI without argparse option confusion."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main(
                [
                    "compare",
                    "--json",
                    "-A",
                    "nu:positive; t:positive",
                    "--",
                    "-4*nu*pi^2*exp(-4*nu*t)",
                    "0",
                ]
            )
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["value"]["status"], "disproven")
        self.assertFalse(payload["value"]["equivalent"])

    def test_constant_equality_soundness_exact_vs_approximate(self) -> None:
        """Ensure non-zero exact constants (e.g. 1/10^30) are NEVER promoted to 'proven' via numerical tolerance."""
        ax = Axiom()

        # 1. Exact non-zero constants vs 0: must be disproven, NOT proven
        res_rational = ax.compare("1/10^30", "0")
        self.assertTrue(res_rational.ok)
        self.assertEqual(res_rational.value["status"], "disproven")
        self.assertFalse(res_rational.value["equivalent"])
        self.assertEqual(res_rational.guarantee.value, "unverified")
        self.assertFalse(res_rational.verification.passed)

        res_tiny = ax.compare("1/10^50", "0")
        self.assertEqual(res_tiny.value["status"], "disproven")
        self.assertFalse(res_tiny.value["equivalent"])

        # 2. Exact identical constants: must be proven with exact-symbolic guarantee
        res_equal = ax.compare("1/2", "2/4")
        self.assertTrue(res_equal.ok)
        self.assertEqual(res_equal.value["status"], "proven")
        self.assertTrue(res_equal.value["equivalent"])
        self.assertEqual(res_equal.guarantee.value, "exact-symbolic")
        self.assertTrue(res_equal.verification.passed)

        # 3. Approximate float literals within tolerance: approximately_equal, NOT proven
        res_float = ax.compare("1.0*10^(-25)", "0")
        self.assertTrue(res_float.ok)
        self.assertEqual(res_float.value["status"], "approximately_equal")
        self.assertFalse(res_float.value["equivalent"])
        self.assertTrue(res_float.value.get("approximately_equal"))
        self.assertIn("approx", res_float.latex)
        self.assertEqual(res_float.guarantee.value, "unverified")

        # 4. CLI end-to-end check for 1/10^30 != 0
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main(["compare", "--json", "1/10^30", "0"])
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["value"]["status"], "disproven")
        self.assertFalse(payload["value"]["equivalent"])

    def test_mcp_all_21_tools_and_jsonrpc(self) -> None:
        self.assertEqual(len(TOOL_DEFINITIONS), 21)
        names = {t["name"] for t in TOOL_DEFINITIONS}
        self.assertEqual(
            names,
            {
                "math_parse",
                "math_simplify",
                "math_solve",
                "math_differentiate",
                "math_integrate",
                "math_limit",
                "math_evaluate",
                "math_plot",
                "math_prove",
                "math_verify",
                "math_explain",
                "math_compare",
                "math_explore",
                "math_matrix",
                "math_ode",
                "math_number_theory",
                "math_optimize",
                "math_statistics",
                "math_session",
                "math_tensor",
                "math_search_mathlib",
            },
        )

        init_resp = handle_jsonrpc_message(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
        )
        assert init_resp is not None
        self.assertEqual(init_resp["result"]["serverInfo"]["name"], "axiom")

        call_resp = handle_jsonrpc_message(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "math_solve",
                    "arguments": {"expression": "x^2 - 5*x + 6 = 0"},
                },
            }
        )
        assert call_resp is not None
        structured = call_resp["result"]["structuredContent"]
        self.assertIs(structured["ok"], True)
        self.assertEqual(structured["value"], ["2", "3"])
        self.assertEqual(structured["guarantee"], "verified-substitution")

        self.assertTrue(dispatch_tool("math_parse", {"expression": "2x + 1 = 0"}).ok)
        self.assertTrue(
            dispatch_tool("math_simplify", {"expression": "(x^2 - 1)/(x - 1)"}).ok
        )
        self.assertTrue(dispatch_tool("math_differentiate", {"expression": "cos(x)"}).ok)
        self.assertTrue(dispatch_tool("math_integrate", {"expression": "2*x"}).ok)
        self.assertTrue(
            dispatch_tool("math_limit", {"expression": "sin(x)/x", "point": "0"}).ok
        )
        self.assertEqual(
            dispatch_tool("math_evaluate", {"expression": "2^10"}).value, "1024"
        )
        self.assertTrue(
            dispatch_tool("math_compare", {"left": "x + x", "right": "2*x"}).verified
        )
        self.assertTrue(
            dispatch_tool(
                "math_verify", {"target": "x - 3 = 0", "candidate": "3"}
            ).verified
        )
        self.assertTrue(
            dispatch_tool("math_explain", {"expression": "x^2 - 4 = 0"}).ok
        )
        self.assertTrue(dispatch_tool("math_explore", {"expression": "x^2"}).ok)
        self.assertTrue(
            dispatch_tool("math_plot", {"expression": "x^2", "points": 11}).ok
        )
        self.assertTrue(
            dispatch_tool(
                "math_prove",
                {"statement": "(x + 1)^2 = x^2 + 2*x + 1", "engine": "sympy"},
            ).verified
        )
        self.assertTrue(
            dispatch_tool(
                "math_matrix",
                {"matrix": "[[1, 2], [3, 5]]", "operation": "inv"},
            ).verified
        )
        self.assertTrue(
            dispatch_tool(
                "math_ode",
                {"equation": "diff(y(x), x) - y(x) = 0"},
            ).verified
        )
        self.assertTrue(
            dispatch_tool(
                "math_number_theory",
                {"operation": "factorint", "n": 120},
            ).verified
        )
        self.assertTrue(
            dispatch_tool(
                "math_optimize",
                {"expression": "(x - 3)^2 + 2", "mode": "minimize"},
            ).verified
        )
        self.assertTrue(
            dispatch_tool(
                "math_statistics",
                {"data": [1, 2, 3, 4, 5]},
            ).verified
        )
        self.assertTrue(
            dispatch_tool(
                "math_session",
                {"action": "show", "name": "test_mcp"},
            ).ok
        )
        self.assertTrue(
            dispatch_tool(
                "math_tensor",
                {"metric": "polar"},
            ).verified
        )
        self.assertTrue(
            dispatch_tool(
                "math_search_mathlib",
                {"query": "binomial square"},
            ).verified
        )

    def test_mcp_stdio_subprocess_roundtrip(self) -> None:
        import subprocess
        import sys

        requests = "\n".join(
            [
                json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}),
                json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": "math_solve",
                            "arguments": {"expression": "x^2 - 5*x + 6 = 0"},
                        },
                    }
                ),
            ]
        ) + "\n"

        proc = subprocess.run(
            [sys.executable, "-m", "axiom.mcp_server"],
            input=requests,
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
        lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 3)
        r_init = json.loads(lines[0])
        r_list = json.loads(lines[1])
        r_call = json.loads(lines[2])
        self.assertEqual(r_init["result"]["serverInfo"]["name"], "axiom")
        self.assertEqual(len(r_list["result"]["tools"]), 21)
        self.assertEqual(
            r_call["result"]["structuredContent"]["guarantee"],
            "verified-substitution",
        )

    # --------------------------------------- v0.2.0 contract & coverage tests

    def test_contract_parse_plot_and_catalog_guarantees(self) -> None:
        from axiom.contract import MathResult, Verification

        ax = Axiom()

        # 1. math_parse uses STRUCTURAL_PARSE with AST round-trip verification (never EXACT_SYMBOLIC with verification=None)
        parsed = ax.parse("2x + 1 = 0")
        self.assertTrue(parsed.ok and parsed.verified)
        self.assertEqual(parsed.guarantee, Guarantee.STRUCTURAL_PARSE)
        self.assertFalse(parsed.guarantee.is_mathematical_claim)
        assert parsed.verification is not None
        self.assertEqual(parsed.verification.kind, "ast-roundtrip")

        # 2. math_plot uses SAMPLED_VISUALIZATION
        plotted = ax.plot("sin(x)/x", points=11)
        self.assertTrue(plotted.ok and plotted.verified)
        self.assertEqual(plotted.guarantee, Guarantee.SAMPLED_VISUALIZATION)
        self.assertFalse(plotted.guarantee.is_mathematical_claim)

        # 3. MathResult.__post_init__ forbids any mathematical claim without passed Verification
        for claim_g in (
            Guarantee.FORMAL_PROOF,
            Guarantee.EXACT_SYMBOLIC,
            Guarantee.VERIFIED_SUBSTITUTION,
            Guarantee.NUMERICAL_APPROXIMATION,
        ):
            with self.assertRaises(ValueError):
                MathResult(
                    kind="test",
                    input="x",
                    ok=True,
                    guarantee=claim_g,
                    verification=None,
                )
            with self.assertRaises(ValueError):
                MathResult(
                    kind="test",
                    input="x",
                    ok=True,
                    guarantee=claim_g,
                    verification=Verification(kind="test", passed=False, detail="failed"),
                )

    def test_domain_assumptions_and_branch_cuts(self) -> None:
        ax = Axiom()

        # Over general reals (default), sqrt(x^2) != x: refuted with clean rational counterexample x = -1
        over_reals = ax.compare("sqrt(x^2)", "x")
        self.assertTrue(over_reals.ok and not over_reals.verified)
        self.assertIs(over_reals.value["equivalent"], False)
        self.assertEqual(over_reals.guarantee, Guarantee.UNVERIFIED)
        assert over_reals.verification is not None
        self.assertEqual(
            over_reals.verification.data["counterexample"], {"x": "-1"}
        )

        # Over complex numbers (default unconstrained), sqrt(x^2) != Abs(x): refuted at x = I
        unconstrained = ax.compare("sqrt(x^2)", "Abs(x)")
        self.assertTrue(unconstrained.ok and not unconstrained.verified)
        self.assertIs(unconstrained.value["equivalent"], False)
        self.assertEqual(unconstrained.guarantee, Guarantee.UNVERIFIED)
        assert unconstrained.verification is not None
        self.assertEqual(unconstrained.verification.data["counterexample"], {"x": "I"})

        # Over reals (assumptions={"x": "real"}), sqrt(x^2) == Abs(x) holds identically
        abs_id = ax.compare("sqrt(x^2)", "Abs(x)", assumptions={"x": "real"})
        self.assertTrue(abs_id.ok and abs_id.verified)
        self.assertIs(abs_id.value["equivalent"], True)
        self.assertEqual(abs_id.guarantee, Guarantee.EXACT_SYMBOLIC)

        # Under assumption x > 0 (positive), sqrt(x^2) == x holds as EXACT_SYMBOLIC
        pos_id = ax.compare("sqrt(x^2)", "x", assumptions={"x": "positive"})
        self.assertTrue(pos_id.ok and pos_id.verified)
        self.assertIs(pos_id.value["equivalent"], True)
        self.assertEqual(pos_id.guarantee, Guarantee.EXACT_SYMBOLIC)

        # Under assumption x < 0 (negative), sqrt(x^2) == -x holds as EXACT_SYMBOLIC
        neg_id = ax.compare("sqrt(x^2)", "-x", assumptions={"x": "negative"})
        self.assertTrue(neg_id.ok and neg_id.verified)
        self.assertIs(neg_id.value["equivalent"], True)
        self.assertEqual(neg_id.guarantee, Guarantee.EXACT_SYMBOLIC)

        # Simplification with positive assumption reduces sqrt(x^2) -> x
        simp_pos = ax.simplify("sqrt(x^2)", assumptions={"x": "positive"})
        self.assertTrue(simp_pos.ok and simp_pos.verified)
        self.assertEqual(simp_pos.value, "x")
        self.assertEqual(simp_pos.guarantee, Guarantee.EXACT_SYMBOLIC)

    def test_contradictory_and_invalid_assumptions_rejected(self) -> None:
        ax = Axiom()

        bad_contradiction = ax.simplify(
            "sqrt(x^2)", assumptions={"x": ["positive", "negative"]}
        )
        self.assertFalse(bad_contradiction.ok)
        self.assertIn("contradictory assumptions", bad_contradiction.error or "")

        bad_parity = ax.compare(
            "n", "n", assumptions={"n": ["even", "odd"]}
        )
        self.assertFalse(bad_parity.ok)
        self.assertIn("contradictory assumptions", bad_parity.error or "")

        bad_unknown = ax.simplify("x", assumptions={"x": "superluminal"})
        self.assertFalse(bad_unknown.ok)
        self.assertIn("unsupported assumption", bad_unknown.error or "")

    def test_definite_integral_interior_singularities_and_divergence(self) -> None:
        import sympy as sp
        from axiom.verification import verify_integral

        ax = Axiom()
        x = sp.Symbol("x", real=True)

        # 1. Divergent integral with interior pole at x = 0: integral_{-1}^{1} 1/x^2 dx -> oo
        div_res = ax.integrate("1/x^2", variable="x", lower="-1", upper="1")
        self.assertTrue(div_res.ok and not div_res.verified)
        self.assertEqual(div_res.guarantee, Guarantee.UNVERIFIED)
        assert div_res.verification is not None
        self.assertEqual(div_res.verification.kind, "divergent-integral")

        # 2. Naive FTC claim F(1) - F(-1) = (-1/1) - (-1/-1) = -2 across pole at x = 0 must be rejected!
        ver_naive, guar_naive = verify_integral(
            1 / x**2,
            sp.Integer(-2),
            x,
            limits=(sp.Integer(-1), sp.Integer(1)),
        )
        self.assertFalse(ver_naive.passed)
        self.assertEqual(guar_naive, Guarantee.UNVERIFIED)
        self.assertEqual(ver_naive.kind, "interior-singularity-check")
        self.assertEqual(ver_naive.data["singularities"], ["0"])

        # 3. Non-integrable odd pole 1/x on [-1, 1] (even if someone claims 0 by principal value)
        ver_pv, guar_pv = verify_integral(
            1 / x,
            sp.Integer(0),
            x,
            limits=(sp.Integer(-1), sp.Integer(1)),
        )
        self.assertFalse(ver_pv.passed)
        self.assertEqual(guar_pv, Guarantee.UNVERIFIED)
        self.assertEqual(ver_pv.kind, "interior-singularity-check")

        # 4. Convergent improper integral 1/sqrt(x) on [0, 1] = 2 still passes as EXACT_SYMBOLIC
        conv_res = ax.integrate("1/sqrt(x)", variable="x", lower="0", upper="1")
        self.assertTrue(conv_res.ok and conv_res.verified)
        self.assertEqual(conv_res.value, "2")
        self.assertEqual(conv_res.guarantee, Guarantee.EXACT_SYMBOLIC)

    def test_two_sided_limits_and_jump_discontinuities(self) -> None:
        ax = Axiom()

        # 1. Jump discontinuity at x = 0: Abs(x)/x has left=-1, right=+1 -> two-sided limit DNE
        jump = ax.limit("Abs(x)/x", variable="x", point="0", direction="+-")
        self.assertTrue(jump.ok and not jump.verified)
        self.assertEqual(jump.guarantee, Guarantee.UNVERIFIED)
        self.assertIn("left=-1", jump.value_str)
        self.assertIn("right=1", jump.value_str)

        # 2. One-sided limits of Abs(x)/x at x = 0 exist and are verified
        right_lim = ax.limit("Abs(x)/x", variable="x", point="0", direction="+")
        self.assertTrue(right_lim.ok and right_lim.verified)
        self.assertEqual(right_lim.value, "1")

        left_lim = ax.limit("Abs(x)/x", variable="x", point="0", direction="-")
        self.assertTrue(left_lim.ok and left_lim.verified)
        self.assertEqual(left_lim.value, "-1")

        # 3. Odd pole 1/x at x = 0: left=-oo, right=+oo -> two-sided limit DNE
        odd_pole = ax.limit("1/x", variable="x", point="0", direction="+-")
        self.assertTrue(odd_pole.ok and not odd_pole.verified)
        self.assertEqual(odd_pole.guarantee, Guarantee.UNVERIFIED)

        # 4. Even pole 1/x^2 at x = 0: both left and right -> +oo -> verified
        even_pole = ax.limit("1/x^2", variable="x", point="0", direction="+-")
        self.assertTrue(even_pole.ok and even_pole.verified)
        self.assertEqual(even_pole.value, "oo")
        self.assertEqual(even_pole.guarantee, Guarantee.NUMERICAL_APPROXIMATION)

    def test_extraneous_roots_and_periodic_solution_sets(self) -> None:
        ax = Axiom()

        # 1. (x^2 - 1)/(x - 1) = 0 has root x = -1; x = 1 is an extraneous removable pole (0/0)
        rat_eq = ax.solve("(x^2 - 1)/(x - 1) = 0")
        self.assertTrue(rat_eq.ok and rat_eq.verified)
        self.assertEqual(rat_eq.value, ["-1"])
        self.assertEqual(rat_eq.guarantee, Guarantee.VERIFIED_SUBSTITUTION)

        # 2. Explicitly verifying the extraneous root x = 1 must fail domain audit
        bad_pole_root = ax.verify("(x^2 - 1)/(x - 1) = 0", candidate="1")
        self.assertTrue(bad_pole_root.ok and not bad_pole_root.verified)
        self.assertEqual(bad_pole_root.guarantee, Guarantee.UNVERIFIED)
        assert bad_pole_root.verification is not None
        self.assertEqual(bad_pole_root.verification.kind, "substitution-domain-error")

        # 3. Solving with domain assumption x > 0 rejects negative root when verifying
        violated_assump = ax.verify(
            "x^2 - 4 = 0", candidate="-2", assumptions={"x": "positive"}
        )
        self.assertTrue(violated_assump.ok and not violated_assump.verified)
        self.assertEqual(violated_assump.guarantee, Guarantee.UNVERIFIED)

        # 4. Periodic equation sin(x) = 0 reports principal roots + solveset periodic family metadata
        trig_eq = ax.solve("sin(x) = 0")
        self.assertTrue(trig_eq.ok and trig_eq.verified)
        self.assertEqual(trig_eq.value, ["0", "pi"])
        assert trig_eq.verification is not None
        self.assertTrue(trig_eq.verification.data.get("periodic_family"))
        self.assertIn("ImageSet", str(trig_eq.verification.data.get("solution_set")))

    def test_lean4_trivial_reflexive_tautology_detection(self) -> None:
        from axiom.engines.lean_engine import LeanEngine

        triv = LeanEngine.detect_trivial_reflexive_theorems(
            "theorem refl_nat (x : Nat) : x = x := by rfl\n"
            "theorem non_triv (a b : Nat) : a + b = b + a := by omega\n"
        )
        self.assertEqual(triv, ["refl_nat"])

    def test_domain_preservation_and_mismatch(self) -> None:
        ax = Axiom()

        # 1. Parsing (x - 1)/(x - 1) preserves variable x and records domain restrictions
        parsed = ax.parse("(x - 1)/(x - 1)")
        self.assertTrue(parsed.ok)
        self.assertIn("x", parsed.variables)
        self.assertIn("x", parsed.value["free_symbols"])
        self.assertEqual(parsed.value["domain_constraints"], ["x - 1 != 0"])
        self.assertEqual(parsed.value["excluded_points"], {"x": ["1"]})
        self.assertTrue(any("x - 1 != 0" in w for w in parsed.warnings))

        # 2. Algebraic simplification carries the domain constraint limitation and warning
        simplified = ax.simplify("(x - 1)/(x - 1)")
        self.assertTrue(simplified.ok and simplified.verified)
        self.assertEqual(simplified.value, "1")
        self.assertIn("x", simplified.variables)
        assert simplified.verification is not None
        self.assertEqual(
            simplified.verification.data["domain_constraints"], ["x - 1 != 0"]
        )
        self.assertTrue(
            any("x - 1 != 0" in lim for lim in simplified.evidence.limitations)
        )

        # 3. Comparing (x - 1)/(x - 1) to 1 without assumptions is refuted at x = 1
        cmp_unrestricted = ax.compare("(x - 1)/(x - 1)", "1")
        self.assertTrue(cmp_unrestricted.ok and not cmp_unrestricted.verified)
        self.assertIs(cmp_unrestricted.value["equivalent"], False)
        self.assertEqual(cmp_unrestricted.guarantee, Guarantee.UNVERIFIED)
        assert cmp_unrestricted.verification is not None
        self.assertEqual(cmp_unrestricted.verification.kind, "domain-mismatch")
        self.assertEqual(
            cmp_unrestricted.verification.data["counterexample"], {"x": "1"}
        )

        # 4. Under assumptions that explicitly exclude the singularity, equivalence holds
        cmp_nonzero = ax.compare("x/x", "1", assumptions={"x": "nonzero"})
        self.assertTrue(cmp_nonzero.ok and cmp_nonzero.verified)
        self.assertIs(cmp_nonzero.value["equivalent"], True)
        self.assertEqual(cmp_nonzero.guarantee, Guarantee.EXACT_SYMBOLIC)

    def test_solution_completeness_and_sample_roots(self) -> None:
        ax = Axiom()

        # Polynomial equation has complete finite solution set
        poly = ax.solve("x^2 - 5*x + 6 = 0")
        self.assertTrue(poly.ok and poly.verified)
        assert poly.verification is not None
        self.assertIs(poly.verification.data["solution_complete"], True)

        # Periodic equation sin(x) = 0 has incomplete sample roots
        trig = ax.solve("sin(x) = 0")
        self.assertTrue(trig.ok and trig.verified)
        assert trig.verification is not None
        self.assertIs(trig.verification.data["solution_complete"], False)
        self.assertEqual(trig.verification.data["sample_solutions"], ["0", "pi"])
        self.assertTrue(trig.verification.data["periodic_family"])

    def test_mcp_and_cli_assumptions_exposure(self) -> None:
        from axiom import TOOL_DEFINITIONS, dispatch_tool

        tools_with_assumptions = {
            "math_parse",
            "math_simplify",
            "math_solve",
            "math_differentiate",
            "math_integrate",
            "math_limit",
            "math_evaluate",
            "math_verify",
            "math_compare",
        }
        for tool_def in TOOL_DEFINITIONS:
            name = tool_def["name"]
            if name in tools_with_assumptions:
                props = tool_def["inputSchema"]["properties"]
                self.assertIn(
                    "assumptions",
                    props,
                    f"Tool {name} must declare assumptions in inputSchema",
                )

        # MCP dispatch with string assumption format 'x:real'
        res_real = dispatch_tool(
            "math_compare",
            {"left": "sqrt(x^2)", "right": "Abs(x)", "assumptions": "x:real"},
        )
        self.assertTrue(res_real.ok and res_real.verified)
        self.assertEqual(res_real.guarantee, Guarantee.EXACT_SYMBOLIC)

        # MCP dispatch without assumptions refutes over complex C
        res_complex = dispatch_tool(
            "math_compare",
            {"left": "sqrt(x^2)", "right": "Abs(x)"},
        )
        self.assertTrue(res_complex.ok and not res_complex.verified)
        self.assertEqual(res_complex.guarantee, Guarantee.UNVERIFIED)

        # CLI execution with --assumptions
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = cli_main(
                [
                    "--plain",
                    "compare",
                    "sqrt(x^2)",
                    "Abs(x)",
                    "-A",
                    "x:real",
                ]
            )
        self.assertEqual(ret, 0)
        self.assertIn("EXACT-SYMBOLIC", buf.getvalue())

    def test_high_precision_decimal_literals_and_zeta_pole(self) -> None:
        ax = Axiom()

        # 30-digit literal preservation without IEEE-754 truncation
        pi_literal = "3.141592653589793238462643383279"
        parsed = ax.parse(pi_literal)
        self.assertTrue(parsed.ok)
        self.assertEqual(parsed.value_str, pi_literal)

        # Removable singularity at s = 1 for (s - 1)*zeta(s)
        lim_rem = ax.limit("(s - 1)*zeta(s)", variable="s", point="1")
        self.assertTrue(lim_rem.ok and lim_rem.verified)
        self.assertEqual(lim_rem.value, "1")
        self.assertEqual(lim_rem.guarantee, Guarantee.NUMERICAL_APPROXIMATION)

        # Two-sided pole of zeta(s) at s = 1 must be refuted / unverified
        lim_pole = ax.limit("zeta(s)", variable="s", point="1", direction="+-")
        self.assertTrue(lim_pole.ok and not lim_pole.verified)
        self.assertEqual(lim_pole.guarantee, Guarantee.UNVERIFIED)

    def test_number_theory_extended_verification(self) -> None:
        ax = Axiom()

        tot = ax.number_theory("totient", n=10)
        self.assertTrue(tot.ok and tot.verified)
        self.assertEqual(tot.value, 4)
        assert tot.evidence is not None
        self.assertEqual(tot.evidence.reproducible_with, "axiom number-theory totient --n 10")

        bin_res = ax.number_theory("binomial", n=5, k=2)
        self.assertTrue(bin_res.ok and bin_res.verified)
        self.assertEqual(bin_res.value, 10)
        assert bin_res.evidence is not None
        self.assertEqual(
            bin_res.evidence.reproducible_with,
            "axiom number-theory binomial --n 5 --k 2",
        )

        isp = ax.number_theory("isprime", n=17)
        self.assertTrue(isp.ok and isp.verified)
        self.assertEqual(isp.value, True)
        assert isp.evidence is not None
        self.assertEqual(isp.evidence.reproducible_with, "axiom number-theory isprime --n 17")

    def test_adversarial_polynomial_counterexample_and_ternary_soundness(self) -> None:
        ax = Axiom()

        # P(x) = (x+1)(x-2)(x-i)(x+i)(x-1-i)(x+2) zeroes out on the first 6 fixed sample points,
        # but is not identically zero (e.g. P(0) = 4 + 4i != 0 and P(3) = 400 - 200i != 0).
        adv_expr = "(x + 1)*(x - 2)*(x - I)*(x + I)*(x - 1 - I)*(x + 2)"
        res = ax.compare(adv_expr, "0")
        self.assertTrue(res.ok)
        self.assertFalse(res.verified)
        self.assertEqual(res.guarantee, Guarantee.UNVERIFIED)
        self.assertEqual(res.value["status"], "disproven")
        self.assertIs(res.value["equivalent"], False)
        self.assertIn("counterexample", res.value)
        self.assertIn("counterexample", res.value_str)

        # Exact symbolic identity gets status='proven', equivalent=True
        proven_res = ax.compare("(x + 1)^2", "x^2 + 2*x + 1")
        self.assertTrue(proven_res.ok and proven_res.verified)
        self.assertEqual(proven_res.guarantee, Guarantee.EXACT_SYMBOLIC)
        self.assertEqual(proven_res.value["status"], "proven")
        self.assertIs(proven_res.value["equivalent"], True)

        # Transcendental equation where numerical samples agree but symbolic proof is inconclusive
        # must fail-closed: status='inconclusive', equivalent=False, consistent_with_samples=True, Guarantee.UNVERIFIED
        zeta_func = ax.compare(
            "zeta(s)",
            "2^s * pi^(s - 1) * sin(pi*s/2) * gamma(1 - s) * zeta(1 - s)",
        )
        self.assertTrue(zeta_func.ok)
        self.assertFalse(zeta_func.verified)
        self.assertEqual(zeta_func.guarantee, Guarantee.UNVERIFIED)
        self.assertEqual(zeta_func.value["status"], "inconclusive")
        self.assertIs(zeta_func.value["equivalent"], False)
        self.assertIs(zeta_func.value["consistent_with_samples"], True)
        self.assertIn("inconclusive", zeta_func.value_str)

    def test_relational_assumptions_and_domain_preservation(self) -> None:
        ax = Axiom()

        # Format 'x!=1' is recognized and enables proving equivalence without domain mismatch
        res_rel = ax.compare("(x - 1)/(x - 1)", "1", assumptions="x!=1")
        self.assertTrue(res_rel.ok and res_rel.verified)
        self.assertEqual(res_rel.guarantee, Guarantee.EXACT_SYMBOLIC)
        self.assertEqual(res_rel.value["status"], "proven")
        self.assertIs(res_rel.value["equivalent"], True)

        # Relational format 'x>0' sets real + positive
        res_gt = ax.compare("sqrt(x^2)", "x", assumptions="x>0")
        self.assertTrue(res_gt.ok and res_gt.verified)
        self.assertEqual(res_gt.guarantee, Guarantee.EXACT_SYMBOLIC)
        self.assertEqual(res_gt.value["status"], "proven")

        # Relational format 'x<=0' sets real + nonpositive
        res_le = ax.compare("sqrt(x^2)", "-x", assumptions="x<=0")
        self.assertTrue(res_le.ok and res_le.verified)
        self.assertEqual(res_le.guarantee, Guarantee.EXACT_SYMBOLIC)
        self.assertEqual(res_le.value["status"], "proven")

    def test_solve_system_with_assumptions(self) -> None:
        ax = Axiom()

        # Non-linear system x^2 + y^2 = 25 and x - y = 1 has solutions (4, 3) and (-3, -4)
        # Declaring assumptions="x:positive,y:positive" must filter out (-3, -4) and verify (4, 3)
        res = ax.solve("x^2 + y^2 = 25; x - y = 1", assumptions="x:positive,y:positive")
        self.assertTrue(res.ok and res.verified)
        self.assertEqual(res.guarantee, Guarantee.VERIFIED_SUBSTITUTION)
        self.assertEqual(res.value, [{"x": "4", "y": "3"}])
        assert res.verification is not None
        self.assertIn("assumptions", res.verification.data)
        self.assertIn("x", res.verification.data["assumptions"])
        self.assertIn("y", res.verification.data["assumptions"])
        self.assertEqual(res.evidence.reproducible_with, 'axiom solve "x^2 + y^2 = 25; x - y = 1" --assumptions "x:positive,y:positive"')


    def test_inexact_float_absorption_soundness(self) -> None:
        ax = Axiom()

        # Float absorption: 0.1 + 1/10^20 vs 0.1 simplifies diff to 0 in naive float logic,
        # but inexact float tracking MUST prevent exact symbolic proof and EXACT_SYMBOLIC guarantee.
        res = ax.compare("0.1 + 1/10^20", "0.1")
        self.assertFalse(res.verified)
        self.assertNotEqual(res.guarantee, Guarantee.EXACT_SYMBOLIC)
        self.assertEqual(res.guarantee, Guarantee.UNVERIFIED)
        self.assertEqual(res.value.get("status"), "approximately_equal")
        self.assertIs(res.value.get("equivalent"), False)
        self.assertIs(res.value.get("approximately_equal"), True)

        # Inexact float 0.1 vs exact rational 1/10
        res_rational = ax.compare("0.1", "1/10")
        self.assertNotEqual(res_rational.guarantee, Guarantee.EXACT_SYMBOLIC)
        self.assertIn(res_rational.value.get("status"), ("approximately_equal", "inconclusive"))

        # High precision decimal literal tracking
        res_high_prec = ax.compare("0.100000000000000000000000000001", "0.1")
        self.assertNotEqual(res_high_prec.guarantee, Guarantee.EXACT_SYMBOLIC)

        # Variable with float vs rational: x + 0.1 vs x + 1/10
        res_var = ax.compare("x + 0.1", "x + 1/10")
        self.assertNotEqual(res_var.guarantee, Guarantee.EXACT_SYMBOLIC)
        self.assertFalse(res_var.verified)

    def test_prove_formal_manifest_three_layers(self) -> None:
        ax = Axiom()

        res = ax.prove(
            "x + 0 = x",
            engine="sympy",
            canonical_statement="AddZero identity for real numbers",
            declared_hypotheses=["x is real"],
            spec_alignment="congruent",
        )
        self.assertTrue(res.ok and res.verified)
        self.assertEqual(res.guarantee, Guarantee.EXACT_SYMBOLIC)
        self.assertIsNotNone(res.verification)
        assert res.verification is not None
        manifest = res.verification.data.get("formal_manifest")
        self.assertIsInstance(manifest, dict)
        self.assertIn("kernel_validity", manifest)
        self.assertIn("assumptions_audit", manifest)
        self.assertIn("spec_alignment", manifest)

        # Layer 1: Kernel validity (SymPy algebraic engine does not execute an interactive formal kernel)
        self.assertFalse(manifest["kernel_validity"]["verified"])
        self.assertEqual(manifest["kernel_validity"]["runner"], "sympy")
        self.assertEqual(manifest["kernel_validity"]["status"], "not_applicable")
        self.assertIn("SymPy algebraic verification", manifest["kernel_validity"]["detail"])
        self.assertIsInstance(manifest["kernel_validity"]["axioms"], list)

        # Layer 2: Assumptions audit
        self.assertEqual(manifest["assumptions_audit"]["declared_hypotheses"], ["x is real"])
        self.assertEqual(manifest["assumptions_audit"]["status"], "clean")

        # Layer 3: Spec alignment
        self.assertEqual(manifest["spec_alignment"]["canonical_statement"], "AddZero identity for real numbers")
        self.assertEqual(manifest["spec_alignment"]["status"], "congruent")
        self.assertTrue(manifest["spec_alignment"]["is_aligned"])

        # Anti-drift tautology control rejection
        res_tautology = ax.prove(
            "theorem fake : 2 + 2 = 4 := by rfl",
            canonical_statement="Riemann Hypothesis",
            spec_alignment="tautology_control",
        )
        self.assertFalse(res_tautology.verified)
        self.assertEqual(res_tautology.guarantee, Guarantee.UNVERIFIED)
        assert res_tautology.verification is not None
        taut_manifest = res_tautology.verification.data.get("formal_manifest")
        self.assertFalse(taut_manifest["spec_alignment"]["is_aligned"])
        self.assertEqual(taut_manifest["spec_alignment"]["status"], "tautology_control")

    def test_prove_adversarial_misalignment_and_sympy_kernel_gating(self) -> None:
        ax = Axiom()

        # Reviewer adversarial test: SymPy engine claiming canonical Millennium problem
        res = ax.prove("x + 0 = x", engine="sympy", canonical_statement="Riemann Hypothesis")
        self.assertFalse(res.verified)
        self.assertEqual(res.guarantee, Guarantee.UNVERIFIED)
        manifest = res.verification.data["formal_manifest"]
        self.assertFalse(manifest["spec_alignment"]["is_aligned"])
        self.assertFalse(manifest["kernel_validity"]["verified"])
        self.assertEqual(manifest["spec_alignment"]["verified_alignment"], "unaligned")
        self.assertEqual(manifest["kernel_validity"]["status"], "not_applicable")

        # Adversarial declared alignment override: caller declares congruent, but semantically unaligned
        res_adv = ax.prove(
            "x + 0 = x",
            engine="sympy",
            canonical_statement="Riemann Hypothesis",
            spec_alignment="congruent",
        )
        self.assertFalse(res_adv.verified)
        adv_manifest = res_adv.verification.data["formal_manifest"]
        self.assertEqual(adv_manifest["spec_alignment"]["declared_alignment"], "congruent")
        self.assertEqual(adv_manifest["spec_alignment"]["verified_alignment"], "unaligned")
        self.assertFalse(adv_manifest["spec_alignment"]["is_aligned"])
        self.assertFalse(adv_manifest["spec_alignment"]["congruent"])

        # Lean 4 external forcing variant vs Navier-Stokes canonical statement
        res_forced = ax.prove(
            "examples/navier_stokes_forced.lean",
            engine="lean",
            canonical_statement="Clay Millennium Navier-Stokes Existence and Smoothness (unforced homogeneous 3D)",
            spec_alignment="scoped_forced_variant",
        )
        self.assertFalse(res_forced.verified)
        forced_manifest = res_forced.verification.data["formal_manifest"]
        self.assertIn(forced_manifest["spec_alignment"]["verified_alignment"], ("scoped", "scoped_forced_variant"))
        self.assertTrue(forced_manifest["spec_alignment"]["is_aligned"])
        if forced_manifest["kernel_validity"]["status"] == "kernel_verified":
            self.assertTrue(forced_manifest["kernel_validity"]["verified"])
        else:
            self.assertFalse(forced_manifest["kernel_validity"]["verified"])

        # Adversarial elementary theorem against Navier-Stokes canonical
        res_ns_mismatch = ax.prove(
            "examples/theorems.lean",
            engine="lean",
            canonical_statement="Clay Millennium Navier-Stokes Existence and Smoothness (unforced homogeneous 3D)",
            spec_alignment="congruent",
        )
        self.assertFalse(res_ns_mismatch.verified)
        ns_manifest = res_ns_mismatch.verification.data["formal_manifest"]
        self.assertEqual(ns_manifest["spec_alignment"]["declared_alignment"], "congruent")
        self.assertEqual(ns_manifest["spec_alignment"]["verified_alignment"], "unaligned")
        self.assertFalse(ns_manifest["spec_alignment"]["is_aligned"])

    def test_assumptions_audit_undeclared_hypotheses(self) -> None:
        ax = Axiom()

        # When theorem source has hypotheses but caller declared None/empty,
        # assumptions audit must flag undeclared hypotheses and fail-closed to warning_undeclared_hypotheses
        res = ax.prove(
            "examples/theorems.lean",
            engine="lean",
            canonical_statement="AddZero identity for natural numbers",
        )
        manifest = res.verification.data["formal_manifest"]
        audit = manifest["assumptions_audit"]
        self.assertTrue(audit["implicit_hypotheses_flagged"])
        self.assertEqual(audit["status"], "warning_undeclared_hypotheses")
        self.assertTrue(len(audit["detected_hypotheses"]) > 0)
        self.assertEqual(audit["declared_hypotheses"], [])

    def test_prove_adversarial_keyword_spoofing_rejected(self) -> None:
        ax = Axiom()

        # Reviewer adversarial probe: elementary Nat arithmetic with 'zeta' in identifier
        # claiming the Riemann Hypothesis
        adv_src = (
            "theorem zeta_add_zero (n : Nat) : n + 0 = n := by\n"
            "  rfl\n"
        )
        res = ax.prove(
            adv_src,
            engine="lean",
            canonical_statement="Riemann Hypothesis",
            spec_alignment="congruent",
        )
        self.assertFalse(res.verified)
        self.assertEqual(res.guarantee, Guarantee.UNVERIFIED)
        manifest = res.verification.data["formal_manifest"]
        self.assertFalse(manifest["spec_alignment"]["congruent"])
        self.assertIn(manifest["spec_alignment"]["verified_alignment"], ("unaligned", "candidate"))

        # Pure comment keyword spoofing must be stripped and rejected as unaligned
        adv_comment_src = (
            "-- Riemann hypothesis complex zeros zeta critical line\n"
            "theorem arithmetic_identity (n : Nat) : n + 1 = 1 + n := by\n"
            "  omega\n"
        )
        res_comment = ax.prove(
            adv_comment_src,
            engine="lean",
            canonical_statement="Riemann Hypothesis",
            spec_alignment="congruent",
        )
        self.assertFalse(res_comment.verified)
        comment_manifest = res_comment.verification.data["formal_manifest"]
        self.assertFalse(comment_manifest["spec_alignment"]["congruent"])
        self.assertFalse(comment_manifest["spec_alignment"]["is_aligned"])
        self.assertEqual(comment_manifest["spec_alignment"]["verified_alignment"], "unaligned")

    def test_kernel_validity_independent_of_spec_alignment(self) -> None:
        from unittest.mock import MagicMock, patch
        ax = Axiom()
        lean_eng = ax.registry.get("lean")

        # When Lean 4 kernel verifies a theorem, kernel_validity.verified is True,
        # but if the theorem is unaligned with canonical_statement, res.verified is False
        with patch.object(lean_eng, "lean_bin", "/usr/bin/lean"), patch(
            "axiom.engines.lean_engine.subprocess.run"
        ) as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="'t' does not depend on any axioms\n",
                stderr="",
            )
            res = ax.prove(
                "theorem t (n : Nat) : n = n := rfl",
                canonical_statement="Riemann Hypothesis",
                declared_hypotheses=["n : Nat"],
            )
            manifest = res.verification.data["formal_manifest"]
            self.assertTrue(manifest["kernel_validity"]["verified"])
            self.assertFalse(manifest["spec_alignment"]["congruent"])
            self.assertFalse(manifest["spec_alignment"]["is_aligned"])
            self.assertFalse(res.verified)
            self.assertEqual(res.guarantee, Guarantee.UNVERIFIED)

    def test_undeclared_hypotheses_block_canonical_proof(self) -> None:
        from unittest.mock import MagicMock, patch
        ax = Axiom()
        lean_eng = ax.registry.get("lean")

        with patch.object(lean_eng, "lean_bin", "/usr/bin/lean"), patch(
            "axiom.engines.lean_engine.subprocess.run"
        ) as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="'add_zero' does not depend on any axioms\n",
                stderr="",
            )
            res = ax.prove(
                "theorem add_zero (n : Nat) : n + 0 = n := rfl",
                canonical_statement="AddZero identity for natural numbers",
            )
            manifest = res.verification.data["formal_manifest"]
            self.assertTrue(manifest["assumptions_audit"]["implicit_hypotheses_flagged"])
            self.assertEqual(manifest["assumptions_audit"]["status"], "warning_undeclared_hypotheses")
            self.assertFalse(res.verified)
            self.assertEqual(res.guarantee, Guarantee.UNVERIFIED)
            self.assertIn("undeclared hypotheses", res.verification.detail)


if __name__ == "__main__":
    unittest.main()


