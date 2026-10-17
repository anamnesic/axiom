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
        self.assertEqual(res.guarantee, Guarantee.EXACT_SYMBOLIC)
        self.assertGreaterEqual(res.value["count"], 1)
        self.assertEqual(res.value["results"][0]["name"], "Real.sin_sq_add_cos_sq")

        fermat = ax.search_mathlib("fermat little prime")
        self.assertTrue(fermat.ok and fermat.verified)
        names = [r["name"] for r in fermat.value["results"]]
        self.assertIn("ZMod.fermat_little", names)

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

    # ------------------------------------------------- setup, doctor, CLI, MCP

    def test_doctor_and_setup_with_backup(self) -> None:
        doc = run_doctor()
        self.assertTrue(doc["ok"])
        self.assertEqual(doc["mcp_tools_count"], 21)

        with tempfile.TemporaryDirectory() as td:
            fake_home = Path(td)
            claude_cfg = fake_home / ".claude.json"
            claude_cfg.write_text('{"existing": true}\n', encoding="utf-8")

            dry = configure_clients(clients=["claude-code"], apply=False, home=fake_home)
            self.assertFalse(dry["applied"])
            self.assertEqual(dry["clients"][0]["status"], "dry-run")

            applied = configure_clients(
                clients=["claude-code", "cursor"], apply=True, home=fake_home
            )
            self.assertTrue(applied["applied"])
            self.assertTrue((fake_home / ".claude.json.axiom.bak").exists())
            merged = json.loads(claude_cfg.read_text(encoding="utf-8"))
            self.assertTrue(merged["existing"])
            self.assertIn("axiom", merged["mcpServers"])

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


if __name__ == "__main__":
    unittest.main()


