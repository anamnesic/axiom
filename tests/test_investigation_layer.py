"""Mathematical Investigation Layer Suite (v0.3.0, ADR-0019).

Validates the eight high-level investigation primitives:

1. ``math_investigate`` creates a persistent, self-describing dossier.
2. ``math_analyze_claim`` decomposes a claim into variables, hypotheses and
   boundary conditions.
3. ``math_trace_dependencies`` builds an auditable DAG and keeps *structural*
   integrity separate from *demonstrated logical implication*.
4. ``math_find_counterexample`` actively refutes a false claim and produces a
   structured, replayable witness.
5. ``math_compare_proofs`` surfaces the hypotheses each proof route needs.
6. ``math_list_unknowns`` reports the honest Unknown Ledger.
7. ``math_get_evidence_bundle`` exports SHA-256 provenance over every artifact.
8. ``math_export_investigation`` renders the reproducible dossier report.

The suite runs WITHOUT mocks in the critical path: every classification is
driven by a real AXIOM computation.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from axiom import Axiom, EpistemicState
from axiom.investigation import Investigation


class TestInvestigationLayerContract(unittest.TestCase):
    def setUp(self) -> None:
        self.ax = Axiom()
        self._tmp = tempfile.TemporaryDirectory()
        self.root = str(Path(self._tmp.name) / "investigations")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ------------------------------------------------------- helper utilities

    def _new_investigation(self, statement: str) -> str:
        res = self.ax.investigate(statement, root=self.root)
        self.assertTrue(res.ok, res.error)
        return res.value["investigation_id"]

    def _dossier(self, investigation_id: str) -> Investigation:
        return Investigation(self.root, investigation_id)

    # ------------------------------------------------------------- primitive 1

    def test_investigate_creates_the_dossier_layout(self) -> None:
        """The dossier is a directory with the ADR-0019 layout."""
        inv_id = self._new_investigation("sin(x)^2 + cos(x)^2 = 1")
        inv = self._dossier(inv_id)
        self.assertTrue(inv.dir.is_dir())
        self.assertTrue(inv.spec_path.exists())
        self.assertTrue(inv.graph_path.exists())
        self.assertTrue(inv.unknowns_path.exists())
        self.assertTrue(inv.evidence_dir.is_dir())

        spec = json.loads(inv.spec_path.read_text(encoding="utf-8"))
        self.assertEqual(spec["investigation_id"], inv_id)
        self.assertEqual(spec["statement"], "sin(x)^2 + cos(x)^2 = 1")
        self.assertIn("sympy", spec["engines"])
        self.assertIn("axiom_version", spec)

    def test_investigate_rejects_a_duplicate_id(self) -> None:
        """Re-using an explicit dossier id must fail closed, not overwrite."""
        res = self.ax.investigate("x + 1 = 2", investigation_id="dup", root=self.root)
        self.assertTrue(res.ok)
        again = self.ax.investigate("x + 1 = 3", investigation_id="dup", root=self.root)
        self.assertFalse(again.ok)
        spec = self._dossier("dup").read_spec()
        self.assertEqual(spec["statement"], "x + 1 = 2")

    def test_investigate_requires_a_statement(self) -> None:
        """An empty claim is rejected."""
        res = self.ax.investigate("   ", root=self.root)
        self.assertFalse(res.ok)

    # ------------------------------------------------------------- primitive 2

    def test_analyze_claim_extracts_scope_and_boundaries(self) -> None:
        """The analysis surfaces variables, hypotheses and boundary conditions."""
        inv_id = self._new_investigation("(x^2 - 1)/(x - 1) = x + 1")
        res = self.ax.analyze_claim(inv_id, root=self.root)
        self.assertTrue(res.ok, res.error)
        analysis = res.value["analysis"]
        self.assertTrue(analysis["parse_ok"])
        self.assertEqual(analysis["variables"], ["x"])
        self.assertIn("x - 1 != 0", analysis["domain_constraints"])
        self.assertEqual(analysis["excluded_points"], {"x": ["1"]})
        self.assertTrue(analysis["boundary_conditions"])

    def test_analyze_claim_reports_an_unparsable_claim(self) -> None:
        """A malformed claim is reported as unparsed, never as analysed."""
        inv_id = self._new_investigation("x +* 1 =")
        res = self.ax.analyze_claim(inv_id, root=self.root)
        self.assertTrue(res.ok)
        self.assertFalse(res.value["analysis"]["parse_ok"])
        self.assertIsNotNone(res.value["analysis"]["error"])

    def test_analyze_claim_rejects_an_unknown_dossier(self) -> None:
        """An unknown investigation id is an error, not a crash."""
        res = self.ax.analyze_claim("does-not-exist", root=self.root)
        self.assertFalse(res.ok)
        self.assertIn("unknown investigation", (res.error or "").lower())

    # ------------------------------------------------------------- primitive 3

    def test_trace_dependencies_classifies_each_lemma(self) -> None:
        """Each lemma carries its own status and guarantee."""
        inv_id = self._new_investigation("sin(x)^2 + cos(x)^2 = 1")
        res = self.ax.trace_dependencies(
            inv_id,
            ["sin(x)^2 + cos(x)^2 = 1", "x + 1 = 1"],
            root=self.root,
        )
        self.assertTrue(res.ok, res.error)
        counts = res.value["status_counts"]
        self.assertEqual(counts.get("proven"), 1)
        self.assertEqual(counts.get("refuted"), 1)

    def test_trace_dependencies_never_claims_logical_implication(self) -> None:
        """A dependency list certifies structure only, never implication."""
        inv_id = self._new_investigation("x + 1 = 1")
        res = self.ax.trace_dependencies(inv_id, ["x + 1 = 1"], root=self.root)
        self.assertTrue(res.value["dag_structural_integrity"])
        self.assertFalse(res.value["logical_implication_proven"])

    def test_trace_dependencies_detects_a_cycle(self) -> None:
        """A cyclic dependency graph breaks structural integrity."""
        inv_id = self._new_investigation("x + 1 = 1")
        lemma_a = "lemma A"
        lemma_b = "lemma B"
        res = self.ax.trace_dependencies(
            inv_id,
            [
                {"statement": lemma_a, "depends_on": [f"lemma-{_digest(lemma_b)}"]},
                {"statement": lemma_b, "depends_on": [f"lemma-{_digest(lemma_a)}"]},
            ],
            root=self.root,
        )
        self.assertTrue(res.ok, res.error)
        self.assertFalse(res.value["dag_structural_integrity"])
        self.assertTrue(res.value["cycles"])

    def test_trace_dependencies_requires_lemmas(self) -> None:
        """Tracing with no lemma is rejected."""
        inv_id = self._new_investigation("x + 1 = 1")
        res = self.ax.trace_dependencies(inv_id, [], root=self.root)
        self.assertFalse(res.ok)

    # ------------------------------------------------------------- primitive 4

    def test_find_counterexample_refutes_a_false_claim(self) -> None:
        """A false identity is refuted with a structured witness."""
        inv_id = self._new_investigation("(x^2 - 1)/(x - 1) = x + 1")
        res = self.ax.find_counterexample(inv_id, root=self.root)
        self.assertTrue(res.ok, res.error)
        self.assertTrue(res.value["refuted"])
        witness = res.value["witness"]
        self.assertIsInstance(witness, dict)
        # A structured witness always names its type and states what was seen.
        self.assertIn("type", witness)
        self.assertIn("expected", witness)
        self.assertTrue(witness.get("expression") or witness.get("substitutions"))

        ledger = self._dossier(inv_id).read_unknowns()
        kinds = {u["kind"] for u in ledger["unknowns"]}
        self.assertIn("refuted-claim", kinds)

    def test_find_counterexample_on_a_true_claim_is_not_an_unknown(self) -> None:
        """A proven claim is decided: it must not linger in the Unknown Ledger."""
        inv_id = self._new_investigation("sin(x)^2 + cos(x)^2 = 1")
        res = self.ax.find_counterexample(inv_id, root=self.root)
        self.assertTrue(res.ok)
        self.assertFalse(res.value["refuted"])
        self.assertTrue(res.value["proven"])
        self.assertIn("proven", res.value_str)

        ledger = self._dossier(inv_id).read_unknowns()
        kinds = {u["kind"] for u in ledger["unknowns"]}
        self.assertNotIn("no-counterexample-found", kinds)

    def test_find_counterexample_does_not_claim_a_proof(self) -> None:
        """Failure to find a counterexample is never reported as a proof."""
        # A constant comparison that AXIOM cannot decide either way.
        inv_id = self._new_investigation("BesselI(1, 2) = 0.5767248077568734")
        res = self.ax.find_counterexample(inv_id, root=self.root)
        self.assertTrue(res.ok)
        self.assertFalse(res.value["proven"], "an undecidable constant must not be proven")
        self.assertFalse(res.value["refuted"])
        self.assertIn("undecided", res.value_str)

        ledger = self._dossier(inv_id).read_unknowns()
        entry = next(
            (u for u in ledger["unknowns"] if u["kind"] == "no-counterexample-found"), None
        )
        self.assertIsNotNone(entry)
        self.assertIn("NOT a proof", entry["description"])

    # ------------------------------------------------------------- primitive 5

    def test_compare_proofs_surfaces_route_specific_hypotheses(self) -> None:
        """The comparison distinguishes shared from route-specific hypotheses."""
        inv_id = self._new_investigation("sqrt(x^2) = x")
        res = self.ax.compare_proofs(
            inv_id,
            [
                {"statement": "sqrt(x^2) = x", "label": "unrestricted"},
                {"statement": "sqrt(x^2) = x", "label": "with-assumption"},
            ],
            root=self.root,
        )
        self.assertTrue(res.ok, res.error)
        self.assertEqual(len(res.value["routes"]), 2)
        self.assertIn("shared_hypotheses", res.value)
        self.assertEqual(len(res.value["route_specific_hypotheses"]), 2)

    def test_compare_proofs_requires_two_routes(self) -> None:
        """Comparing a single route is rejected."""
        inv_id = self._new_investigation("x + 1 = 1")
        res = self.ax.compare_proofs(inv_id, ["x + 1 = 1"], root=self.root)
        self.assertFalse(res.ok)

    # ------------------------------------------------------------- primitive 6

    def test_list_unknowns_reports_blocking_gaps(self) -> None:
        """The ledger distinguishes blocking gaps from informational ones."""
        inv_id = self._new_investigation("(x^2 - 1)/(x - 1) = x + 1")
        self.ax.find_counterexample(inv_id, root=self.root)
        res = self.ax.list_unknowns(inv_id, root=self.root)
        self.assertTrue(res.ok, res.error)
        self.assertGreater(res.value["count"], 0)
        self.assertGreater(res.value["blocking"], 0)
        for unknown in res.value["unknowns"]:
            self.assertIn(unknown["severity"], ("blocking", "non-blocking"))
            self.assertTrue(unknown["description"])

    def test_list_unknowns_rejects_an_unknown_dossier(self) -> None:
        """An unknown investigation id is an error."""
        res = self.ax.list_unknowns("nope", root=self.root)
        self.assertFalse(res.ok)

    # ------------------------------------------------------------- primitive 7

    def test_evidence_bundle_hashes_every_artifact(self) -> None:
        """The bundle pins every artifact with a SHA-256 digest."""
        inv_id = self._new_investigation("sin(x)^2 + cos(x)^2 = 1")
        self.ax.analyze_claim(inv_id, root=self.root)
        res = self.ax.get_evidence_bundle(inv_id, root=self.root)
        self.assertTrue(res.ok, res.error)
        bundle = res.value["bundle"]
        self.assertGreater(bundle["artifact_count"], 0)
        for artifact in bundle["artifacts"]:
            self.assertEqual(len(artifact["sha256"]), 64)
        self.assertEqual(len(bundle["bundle_digest"]), 64)
        self.assertIn("sympy", bundle["engines"])

    def test_evidence_bundle_digest_changes_with_the_artifact(self) -> None:
        """Mutating an artifact must change the bundle digest."""
        inv_id = self._new_investigation("sin(x)^2 + cos(x)^2 = 1")
        first = self.ax.get_evidence_bundle(inv_id, root=self.root)
        inv = self._dossier(inv_id)
        graph = inv.read_graph()
        graph["nodes"].append({"id": "tampered", "kind": "lemma", "statement": "x = 1",
                               "status": "open", "guarantee": "unverified",
                               "depends_on": [], "detail": "injected"})
        inv.write_graph(graph)
        second = self.ax.get_evidence_bundle(inv_id, root=self.root)
        self.assertNotEqual(
            first.value["bundle"]["bundle_digest"],
            second.value["bundle"]["bundle_digest"],
        )

    # ------------------------------------------------------------- primitive 8

    def test_export_investigation_renders_the_dossier_report(self) -> None:
        """The report carries the analysis, the Mermaid graph and the ledger."""
        inv_id = self._new_investigation("(x^2 - 1)/(x - 1) = x + 1")
        self.ax.analyze_claim(inv_id, root=self.root)
        self.ax.trace_dependencies(inv_id, ["x + 1 = 1"], root=self.root)
        self.ax.find_counterexample(inv_id, root=self.root)
        self.ax.get_evidence_bundle(inv_id, root=self.root)
        res = self.ax.export_investigation(inv_id, root=self.root)
        self.assertTrue(res.ok, res.error)
        report = res.value["report"]
        self.assertIn("```mermaid", report)
        self.assertIn("graph TD", report)
        self.assertIn("## 3. Unknown Ledger", report)
        self.assertIn("## 4. Evidence Bundle", report)
        self.assertIn("Logical implication proven", report)
        self.assertIn("certifies the *structure*", report)
        self.assertTrue(Path(res.value["path"]).exists())

    def test_export_investigation_rejects_an_unknown_dossier(self) -> None:
        """An unknown investigation id is an error."""
        res = self.ax.export_investigation("nope", root=self.root)
        self.assertFalse(res.ok)

    # ----------------------------------------------------------------- contract

    def test_investigation_results_are_operational_not_proofs(self) -> None:
        """An investigation orchestrates proofs; it does not itself certify one."""
        inv_id = self._new_investigation("sin(x)^2 + cos(x)^2 = 1")
        for res in (
            self.ax.analyze_claim(inv_id, root=self.root),
            self.ax.trace_dependencies(inv_id, ["x + 1 = 1"], root=self.root),
            self.ax.list_unknowns(inv_id, root=self.root),
            self.ax.export_investigation(inv_id, root=self.root),
        ):
            self.assertTrue(res.ok)
            self.assertEqual(res.epistemic_state, EpistemicState.INCONCLUSIVE)
            # `verified` means "an independent mathematical check passed".
            # An investigation has had none, so it must never claim otherwise.
            self.assertFalse(res.verified)
            self.assertFalse(res.guarantee.is_mathematical_claim)

    def test_mcp_tools_expose_the_eight_primitives(self) -> None:
        """All eight primitives are reachable over the MCP contract."""
        from axiom.mcp_server import TOOL_DEFINITIONS, dispatch_tool

        names = {t["name"] for t in TOOL_DEFINITIONS}
        for expected in (
            "math_investigate",
            "math_analyze_claim",
            "math_trace_dependencies",
            "math_find_counterexample",
            "math_compare_proofs",
            "math_list_unknowns",
            "math_get_evidence_bundle",
            "math_export_investigation",
        ):
            self.assertIn(expected, names)

        created = dispatch_tool(
            "math_investigate", {"statement": "sin(x)^2 + cos(x)^2 = 1", "root": self.root}
        )
        self.assertTrue(created.ok, created.error)
        inv_id = created.value["investigation_id"]
        for tool, args in (
            ("math_analyze_claim", {"investigation_id": inv_id}),
            ("math_trace_dependencies", {"investigation_id": inv_id, "lemmas": ["x + 1 = 1"]}),
            ("math_find_counterexample", {"investigation_id": inv_id}),
            ("math_compare_proofs", {"investigation_id": inv_id, "statements": ["x + 1 = 1", "x = 1"]}),
            ("math_list_unknowns", {"investigation_id": inv_id}),
            ("math_get_evidence_bundle", {"investigation_id": inv_id}),
            ("math_export_investigation", {"investigation_id": inv_id}),
        ):
            out = dispatch_tool(tool, {**args, "root": self.root})
            self.assertTrue(out.ok, f"{tool}: {out.error}")


def _digest(statement: str) -> str:
    import hashlib

    return hashlib.sha256(f"lemma:{statement}".encode("utf-8")).hexdigest()[:8]


if __name__ == "__main__":
    unittest.main()
