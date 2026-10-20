"""Mathematical Investigation Layer (ADR-0019) Test Suite.

Adversarial and structural tests for the eight investigation primitives:
1. math_investigate
2. math_analyze_claim
3. math_trace_dependencies
4. math_find_counterexample
5. math_compare_proofs
6. math_list_unknowns
7. math_get_evidence_bundle
8. math_export_investigation
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from axiom import Axiom, EpistemicState
from axiom.mcp_server import dispatch_tool


class TestInvestigationLayer(unittest.TestCase):
    def setUp(self) -> None:
        self.ax = Axiom()

    def test_investigate_creates_dossier_structure(self) -> None:
        """Primitive 1: math_investigate creates persistent spec, graph and unknowns."""
        with tempfile.TemporaryDirectory() as td:
            res = self.ax.investigate(
                "x^2 - 1 = (x - 1)*(x + 1)",
                root=td,
                investigation_id="test_inv_01",
            )
            self.assertTrue(res.ok)
            self.assertEqual(res.value["investigation_id"], "test_inv_01")

            dossier_dir = Path(td) / "test_inv_01"
            self.assertTrue(dossier_dir.is_dir())
            self.assertTrue((dossier_dir / "spec.json").is_file())
            self.assertTrue((dossier_dir / "graph.json").is_file())
            self.assertTrue((dossier_dir / "unknowns.json").is_file())

    def test_analyze_claim_decomposes_variables_and_boundaries(self) -> None:
        """Primitive 2: math_analyze_claim extracts variables, domain constraints and hypotheses."""
        with tempfile.TemporaryDirectory() as td:
            self.ax.investigate("1 / (x - 2) = y", root=td, investigation_id="test_ana")
            res = self.ax.analyze_claim("test_ana", root=td)
            self.assertTrue(res.ok)
            analysis = res.value["analysis"]
            self.assertIn("x", analysis["variables"])
            self.assertIn("y", analysis["variables"])
            self.assertTrue(analysis["parse_ok"])

    def test_trace_dependencies_audits_dag_and_cycles(self) -> None:
        """Primitive 3: math_trace_dependencies builds DAG and detects cycles."""
        with tempfile.TemporaryDirectory() as td:
            self.ax.investigate("a = c", root=td, investigation_id="test_dag")

            # Acyclic chain with valid dependencies
            res = self.ax.trace_dependencies(
                "test_dag",
                [
                    "a = b",
                    "b = c",
                ],
                root=td,
            )
            self.assertTrue(res.ok)
            self.assertTrue(res.value["dag_structural_integrity"])
            self.assertEqual(len(res.value["cycles"]), 0)

            # Dangling dependency triggers structural integrity failure
            res_dangling = self.ax.trace_dependencies(
                "test_dag",
                [
                    {"statement": "c = d", "depends_on": ["nonexistent_node_id"]},
                ],
                root=td,
            )
            self.assertTrue(res_dangling.ok)
            self.assertFalse(res_dangling.value["dag_structural_integrity"])

    def test_find_counterexample_detects_false_claims(self) -> None:
        """Primitive 4: math_find_counterexample hunts algebraic/numerical counterexamples."""
        with tempfile.TemporaryDirectory() as td:
            self.ax.investigate("sqrt(x^2) = x", root=td, investigation_id="test_ce")
            res = self.ax.find_counterexample("test_ce", root=td)
            self.assertTrue(res.ok)
            self.assertTrue(res.value.get("refuted"))
            self.assertIsNotNone(res.value.get("counterexample"))

    def test_compare_proofs_surfaces_hypotheses(self) -> None:
        """Primitive 5: math_compare_proofs identifies required hypotheses per proof route."""
        with tempfile.TemporaryDirectory() as td:
            self.ax.investigate("sin(x)^2 + cos(x)^2 = 1", root=td, investigation_id="test_cmp")
            res = self.ax.compare_proofs(
                "test_cmp",
                [
                    "sin(x)^2 + cos(x)^2 = 1",
                    "1 - cos(x)^2 = sin(x)^2",
                ],
                root=td,
            )
            self.assertTrue(res.ok)
            self.assertEqual(len(res.value["routes"]), 2)

    def test_unknown_ledger_tracks_gaps(self) -> None:
        """Primitive 6: math_list_unknowns catalogs open proof obligations."""
        with tempfile.TemporaryDirectory() as td:
            self.ax.investigate("x^2 + 1 = 0", root=td, investigation_id="test_unk")
            res = self.ax.list_unknowns("test_unk", root=td)
            self.assertTrue(res.ok)
            self.assertGreaterEqual(res.value["count"], 1)

    def test_get_evidence_bundle_computes_sha256(self) -> None:
        """Primitive 7: math_get_evidence_bundle exports bundle.json with hashes."""
        with tempfile.TemporaryDirectory() as td:
            self.ax.investigate("x = x", root=td, investigation_id="test_bun")
            self.ax.analyze_claim("test_bun", root=td)
            res = self.ax.get_evidence_bundle("test_bun", root=td)
            self.assertTrue(res.ok)
            bundle = res.value["bundle"]
            self.assertIn("bundle_digest", bundle)
            self.assertGreater(len(bundle["artifacts"]), 0)
            for art in bundle["artifacts"]:
                self.assertEqual(len(art["sha256"]), 64)

    def test_export_investigation_generates_report(self) -> None:
        """Primitive 8: math_export_investigation compiles Markdown report."""
        with tempfile.TemporaryDirectory() as td:
            self.ax.investigate("x + 1 = 1 + x", root=td, investigation_id="test_exp")
            self.ax.analyze_claim("test_exp", root=td)
            self.ax.get_evidence_bundle("test_exp", root=td)
            res = self.ax.export_investigation("test_exp", root=td)
            self.assertTrue(res.ok)
            report_file = Path(res.value["path"])
            self.assertTrue(report_file.is_file())
            content = report_file.read_text(encoding="utf-8")
            self.assertIn("# Investigation Dossier:", content)
            self.assertIn("## 1. Claim Analysis", content)
            self.assertIn("## 2. Proof Dependency Graph", content)

    def test_mcp_dispatch_investigation_tools(self) -> None:
        """Test all 8 tools through MCP JSON-RPC dispatch."""
        with tempfile.TemporaryDirectory() as td:
            r1 = dispatch_tool(
                "math_investigate",
                {"statement": "x^3 - x = x*(x - 1)*(x + 1)", "investigation_id": "mcp_test", "root": td},
            )
            self.assertTrue(r1.ok)

            r2 = dispatch_tool("math_analyze_claim", {"investigation_id": "mcp_test", "root": td})
            self.assertTrue(r2.ok)

            r3 = dispatch_tool(
                "math_trace_dependencies",
                {"investigation_id": "mcp_test", "lemmas": ["x*(x^2 - 1) = x^3 - x"], "root": td},
            )
            self.assertTrue(r3.ok)

            r4 = dispatch_tool("math_find_counterexample", {"investigation_id": "mcp_test", "root": td})
            self.assertTrue(r4.ok)

            r5 = dispatch_tool("math_list_unknowns", {"investigation_id": "mcp_test", "root": td})
            self.assertTrue(r5.ok)

            r6 = dispatch_tool("math_get_evidence_bundle", {"investigation_id": "mcp_test", "root": td})
            self.assertTrue(r6.ok)

            r7 = dispatch_tool("math_export_investigation", {"investigation_id": "mcp_test", "root": td})
            self.assertTrue(r7.ok)
