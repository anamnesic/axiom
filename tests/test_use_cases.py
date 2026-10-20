"""Automated end-to-end test suite for the 10 AXIOM use cases (docs/use-cases.md).

Tests both CLI commands (invoked programmatically via cli.main) and MCP JSON-RPC
tools (invoked via mcp_server.dispatch_tool) across the Four Epistemic States:
1. Verified Algebraic Equation Solving (Proof)
2. Certified Symbolic Identity & Calculus (Proof)
3. Machine-Checked Theorem Proving in Lean 4 (Proof)
4. High-Precision Numerical Equivalence Probing (Approximation)
5. Arbitrary-Precision Arithmetic (Approximation)
6. Active Refutation of Adversarial Algebraic Claims (Refutation)
7. Rejection of Fake Lean Tautologies (Inconclusive / Refused Certification)
8. Multi-Step Research Derivations: Step vs. Chain Validity (Composite Derivation)
9. Differential Geometry & Levi-Civita Tensor Calculus (Proof)
10. Vector Plotting with Sandboxed Output Security (Operational State)
"""

from __future__ import annotations

import io
import json
import os
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest

from axiom import Guarantee
from axiom.cli import main as cli_main
from axiom.mcp_server import dispatch_tool


class TestUseCases(unittest.TestCase):
    """Execute all 10 end-to-end use cases via CLI and MCP."""

    # ----------------------------------------------------------- Use Case 1
    def test_use_case_1_solve(self) -> None:
        """Use Case 1: Verified Algebraic Equation Solving."""
        # 1. CLI
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main(["solve", "x^2 - 5*x + 6 = 0", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["value"], ["2", "3"])
        self.assertEqual(data["guarantee"], "verified-substitution")

        # 2. MCP JSON-RPC
        res = dispatch_tool(
            "math_solve",
            {"equation": "x^2 - 5*x + 6 = 0", "variable": "x"},
        )
        self.assertTrue(res.ok)
        self.assertTrue(res.verified)
        self.assertEqual(res.guarantee, Guarantee.VERIFIED_SUBSTITUTION)
        self.assertEqual(res.value, ["2", "3"])

    # ----------------------------------------------------------- Use Case 2
    def test_use_case_2_simplify(self) -> None:
        """Use Case 2: Certified Symbolic Identity & Calculus."""
        # 1. CLI
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main(["simplify", "cos(x)^2 + sin(x)^2", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(str(data["value"]), "1")
        self.assertEqual(data["guarantee"], "exact-symbolic")

        # 2. MCP JSON-RPC
        res = dispatch_tool(
            "math_simplify",
            {"expression": "cos(x)^2 + sin(x)^2"},
        )
        self.assertTrue(res.ok)
        self.assertTrue(res.verified)
        self.assertEqual(res.guarantee, Guarantee.EXACT_SYMBOLIC)
        self.assertEqual(str(res.value), "1")

    # ----------------------------------------------------------- Use Case 3
    def test_use_case_3_prove_lean(self) -> None:
        """Use Case 3: Machine-Checked Theorem Proving in Lean 4."""
        stmt = "theorem nat_add_comm (n m : Nat) : n + m = m + n := by omega"

        # 1. CLI
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main(["prove", stmt, "--engine", "lean", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertIn("nat_add_comm", str(data["value"]))

        # 2. MCP JSON-RPC
        res = dispatch_tool("math_prove", {"statement": stmt, "engine": "lean"})
        self.assertTrue(res.ok)
        self.assertIn("nat_add_comm", str(res.value))

    # ----------------------------------------------------------- Use Case 4
    def test_use_case_4_compare_tolerance(self) -> None:
        """Use Case 4: High-Precision Numerical Equivalence Probing."""
        # 1. CLI
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main(["compare", "pi", "3.141592653589793", "--tolerance", "1e-12", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["guarantee"], "numerical-approximation")
        self.assertFalse(data["value"]["equivalent"])
        self.assertTrue(data["value"]["approximately_equal"])

        # 2. MCP JSON-RPC (using 'a', 'b', and 'tolerance')
        res = dispatch_tool(
            "math_compare",
            {"a": "pi", "b": "3.141592653589793", "tolerance": 1e-12},
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.guarantee, Guarantee.NUMERICAL_APPROXIMATION)
        self.assertFalse(res.value.get("equivalent"))
        self.assertTrue(res.value.get("approximately_equal"))

    # ----------------------------------------------------------- Use Case 5
    def test_use_case_5_evaluate_precision(self) -> None:
        """Use Case 5: Arbitrary-Precision Arithmetic."""
        # 1. CLI
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main(["evaluate", "sqrt(2)", "--precision", "50", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["guarantee"], "numerical-approximation")
        self.assertTrue(str(data["value"]).startswith("1.4142135623730950488016887242096980785696718753769"))

        # 2. MCP JSON-RPC
        res = dispatch_tool(
            "math_evaluate",
            {"expression": "sqrt(2)", "precision": 50},
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.guarantee, Guarantee.NUMERICAL_APPROXIMATION)
        self.assertTrue(str(res.value).startswith("1.4142135623730950488016887242096980785696718753769"))

    # ----------------------------------------------------------- Use Case 6
    def test_use_case_6_adversarial_polynomial_refutation(self) -> None:
        """Use Case 6: Active Refutation of Adversarial Algebraic Claims."""
        expr = "(x+1)*(x-2)*(x^2+1)*(x^2-2*x+2)"

        # 1. CLI
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main(["compare", expr, "0", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["guarantee"], "unverified")
        self.assertFalse(data["value"]["equivalent"])
        self.assertIn(data["value"]["status"], ("refuted", "disproven"))
        self.assertIn("not equivalent", data["value_str"])

        # 2. MCP JSON-RPC
        res = dispatch_tool("math_compare", {"a": expr, "b": "0"})
        self.assertTrue(res.ok)
        self.assertFalse(res.verified)
        self.assertEqual(res.guarantee, Guarantee.UNVERIFIED)
        self.assertFalse(res.value.get("equivalent"))
        self.assertIn(res.value.get("status"), ("refuted", "disproven"))
        self.assertIn("not equivalent", res.value_str)

    # ----------------------------------------------------------- Use Case 7
    def test_use_case_7_rejection_of_fake_tautologies(self) -> None:
        """Use Case 7: Rejection of Fake Lean Tautologies."""
        fake_claim = "theorem fake_claim : 1 = 2 := by admit"

        # 1. CLI
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main(["prove", fake_claim, "--engine", "lean", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["guarantee"], "unverified")
        self.assertFalse(data["verification"]["passed"])

        # 2. MCP JSON-RPC
        res = dispatch_tool("math_prove", {"statement": fake_claim, "engine": "lean"})
        self.assertTrue(res.ok)
        self.assertFalse(res.verified)
        self.assertEqual(res.guarantee, Guarantee.UNVERIFIED)

    # ----------------------------------------------------------- Use Case 8
    def test_use_case_8_session_step_vs_chain_validity(self) -> None:
        """Use Case 8: Multi-Step Research Derivations: Step vs. Chain Validity."""
        with tempfile.TemporaryDirectory() as td:
            # We set current working directory to td so .axiom/sessions is isolated
            prev_cwd = os.getcwd()
            os.chdir(td)
            try:
                # 1. CLI Workflow
                buf_new = io.StringIO()
                with redirect_stdout(buf_new):
                    rc1 = cli_main(["session", "new", "--title", "Navier-Stokes Dissipation Derivation"])
                self.assertEqual(rc1, 0)

                buf_step1 = io.StringIO()
                with redirect_stdout(buf_step1):
                    rc2 = cli_main(["session", "record", "--step", "1", "--command", "axiom solve 'x - 1 = 0'"])
                self.assertEqual(rc2, 0)

                buf_step2 = io.StringIO()
                with redirect_stdout(buf_step2):
                    rc3 = cli_main(["session", "record", "--step", "2", "--command", "axiom prove 'x = 2' --engine sympy", "--depends-on", "1"])
                self.assertEqual(rc3, 0)

                buf_status = io.StringIO()
                with redirect_stdout(buf_status):
                    rc4 = cli_main(["session", "status"])
                self.assertEqual(rc4, 0)
                status_text = buf_status.getvalue().strip()

                self.assertIn("Step 1: step_valid=True, chain_valid=True, guarantee=verified-substitution", status_text)
                self.assertIn("Step 2: step_valid=False, chain_valid=False, broken_dependencies=[1]", status_text)
                self.assertIn("Session: all_steps_valid=False, chain_valid=False, chain_guarantee=unverified", status_text)

                # 2. MCP JSON-RPC Workflow
                mcp_new = dispatch_tool("math_session", {"action": "new", "title": "MCP Derivation Session"})
                self.assertTrue(mcp_new.ok)

                mcp_rec1 = dispatch_tool(
                    "math_session",
                    {"action": "record", "step": 1, "command": "axiom solve 'x - 1 = 0'"},
                )
                self.assertTrue(mcp_rec1.ok)

                mcp_rec2 = dispatch_tool(
                    "math_session",
                    {"action": "record", "step": 2, "command": "axiom prove 'x = 2' --engine sympy", "depends_on": [1]},
                )
                self.assertTrue(mcp_rec2.ok)

                mcp_stat = dispatch_tool("math_session", {"action": "status"})
                self.assertTrue(mcp_stat.ok)
                self.assertIn("Step 1: step_valid=True, chain_valid=True", mcp_stat.value_str)
                self.assertIn("Step 2: step_valid=False, chain_valid=False, broken_dependencies=[1]", mcp_stat.value_str)
                self.assertIn("Session: all_steps_valid=False, chain_valid=False", mcp_stat.value_str)
            finally:
                os.chdir(prev_cwd)

    # ----------------------------------------------------------- Use Case 9
    def test_use_case_9_tensor_sphere(self) -> None:
        """Use Case 9: Differential Geometry & Levi-Civita Tensor Calculus."""
        # 1. CLI
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main(["tensor", "sphere", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["guarantee"], "verified-substitution")
        self.assertIn(str(data["value"]["ricci_scalar"]).replace(" ", ""), ("2", "2/R**2", "2/R^2"))

        # 2. MCP JSON-RPC (using 'metric_type')
        res = dispatch_tool("math_tensor", {"metric_type": "sphere"})
        self.assertTrue(res.ok)
        self.assertTrue(res.verified)
        self.assertEqual(res.guarantee, Guarantee.VERIFIED_SUBSTITUTION)
        self.assertIn(str(res.value.get("ricci_scalar")).replace(" ", ""), ("2", "2/R**2", "2/R^2"))

    # ----------------------------------------------------------- Use Case 10
    def test_use_case_10_plot_sandboxed(self) -> None:
        """Use Case 10: Vector Plotting with Sandboxed Output Security."""
        # The MCP file layer authorizes only the workspace and its dedicated
        # temp sandbox ('<temp>/axiom'); an arbitrary temp directory is
        # *not* an authorized root. The output file must therefore be created
        # inside an authorized root, which is exactly the behaviour under test.
        sandbox_root = Path(tempfile.gettempdir()).resolve() / "axiom"
        sandbox_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=str(sandbox_root)) as td:
            out_file = Path(td) / "sinc.svg"

            # 1. CLI
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = cli_main(["plot", "sin(x)/x", "--range=-10:10", "--output", str(out_file), "--json"])
            self.assertEqual(rc, 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(data["guarantee"], "sampled-visualization")
            self.assertTrue(out_file.exists())

            # 2. MCP JSON-RPC (using 'range_str' and 'output')
            out_file_mcp = Path(td) / "sinc_mcp.svg"
            res = dispatch_tool(
                "math_plot",
                {"expression": "sin(x)/x", "range_str": "-10:10", "output": str(out_file_mcp)},
            )
            self.assertTrue(res.ok)
            self.assertEqual(res.guarantee, Guarantee.SAMPLED_VISUALIZATION)
            self.assertTrue(out_file_mcp.exists())


if __name__ == "__main__":
    unittest.main()
