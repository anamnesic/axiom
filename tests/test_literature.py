"""Offline catalog contract: bibliographic resolution is not a mathematical proof.

All checks use the curated local subset. Missing records remain unresolved;
the suite neither requires network access nor certifies the live registries.
"""

import unittest

from axiom.contract import EpistemicState, Guarantee
from axiom.core import Axiom
from axiom.literature import (
    lookup_msc,
    search_literature,
    search_software,
    verify_citation,
)
from axiom.mcp_server import TOOL_DEFINITIONS, dispatch_tool


class TestZbmathLiterature(unittest.TestCase):
    """Test suite for zbMATH Open integration, MSC lookup, swMATH, and citation verification."""

    def setUp(self) -> None:
        self.ax = Axiom()

    def test_literature_search_offline_curated(self) -> None:
        res = search_literature("cook 1971", online=False)
        self.assertTrue(res.ok)
        self.assertEqual(res.guarantee, Guarantee.CATALOG_LOOKUP)
        self.assertGreater(res.value["count"], 0)
        first = res.value["matches"][0]
        self.assertIn("Cook", str(first["authors"]))
        self.assertIn("68T15", first["msc"])
        self.assertEqual(first["doi"], "10.1145/800157.805047")
        self.assertEqual(res.epistemic_state, EpistemicState.INCONCLUSIVE)
        self.assertFalse(res.guarantee.is_mathematical_claim)

    def test_literature_search_outside_offline_subset(self) -> None:
        res = search_literature("riemann hypothesis", online=False)
        self.assertTrue(res.ok)
        self.assertEqual(res.value["count"], 0)
        self.assertEqual(res.value["matches"], [])
        self.assertEqual(res.guarantee, Guarantee.UNVERIFIED)
        self.assertFalse(res.verified)
        self.assertEqual(res.epistemic_state, EpistemicState.INCONCLUSIVE)

    def test_literature_search_empty_query(self) -> None:
        res = search_literature("   ", online=False)
        self.assertFalse(res.ok)
        self.assertIn("must not be empty", str(res.error))

    def test_msc_lookup_offline(self) -> None:
        res = lookup_msc("11-XX", online=False)
        self.assertTrue(res.ok)
        self.assertEqual(res.guarantee, Guarantee.CATALOG_LOOKUP)
        self.assertGreaterEqual(res.value["count"], 1)
        first = res.value["matches"][0]
        self.assertEqual(first["code"], "11-XX")
        self.assertEqual(first["long_title"], "Number theory")

    def test_msc_lookup_empty_query(self) -> None:
        res = lookup_msc("", online=False)
        self.assertFalse(res.ok)

    def test_swmath_software_lookup_offline(self) -> None:
        res = search_software("lean", online=False)
        self.assertTrue(res.ok)
        self.assertEqual(res.guarantee, Guarantee.CATALOG_LOOKUP)
        self.assertGreaterEqual(res.value["count"], 1)
        names = [m["name"].lower() for m in res.value["matches"]]
        self.assertTrue(any("lean" in n for n in names))

    def test_verify_citation_valid_offline(self) -> None:
        # Resolved bibliographic metadata, not a proof of the paper's claims.
        res = verify_citation("arXiv:2106.04664", online=False)
        self.assertTrue(res.ok)
        self.assertTrue(res.verified)
        self.assertEqual(res.guarantee, Guarantee.CATALOG_LOOKUP)
        self.assertEqual(res.epistemic_state, EpistemicState.INCONCLUSIVE)
        self.assertEqual(res.value["citation_status"], "resolved")
        record = res.value["record"]
        self.assertEqual(record["arxiv"], "2106.04664")
        self.assertIsNone(record["zbmath_id"])
        self.assertIsNone(record["zbl"])
        self.assertIn("Petrera", str(record["authors"]))
        self.assertTrue(any("AXIOM offline catalog" in step for step in res.evidence.steps))

    def test_verify_citation_unresolved_is_not_refuted(self) -> None:
        # A finite catalog cannot establish that an unlisted paper is fictitious.
        res = verify_citation("arXiv:9999.99999 Nonexistent False Paper on Zeros", online=False)
        self.assertTrue(res.ok)
        self.assertFalse(res.verified)
        self.assertEqual(res.guarantee, Guarantee.UNVERIFIED)
        self.assertEqual(res.epistemic_state, EpistemicState.INCONCLUSIVE)
        self.assertFalse(res.has_refutation_evidence)
        self.assertEqual(res.value["citation_status"], "unresolved")
        self.assertTrue(res.value["hallucination_suspected"])
        self.assertNotIn("falsity_witness", res.value)

    def test_citation_does_not_borrow_an_unrelated_zbmath_identifier(self) -> None:
        res = verify_citation("10.4171/MAG/132", online=False)
        self.assertTrue(res.ok and res.verified)
        self.assertEqual(res.value["record"]["zbmath_id"], "7706766")
        self.assertEqual(res.value["record"]["title"], "The integration of OEIS links in zbMATH Open")
        self.assertEqual(res.guarantee, Guarantee.CATALOG_LOOKUP)

    def test_citation_author_mismatch_fails_closed(self) -> None:
        res = verify_citation(
            {"doi": "10.1145/800157.805047", "authors": ["Invented, Alice"]},
            online=False,
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.value["citation_status"], "attribution_mismatch")
        self.assertIn("invented", res.value["missing_authors"])
        self.assertFalse(res.verified)
        self.assertEqual(res.guarantee, Guarantee.UNVERIFIED)
        self.assertEqual(res.epistemic_state, EpistemicState.INCONCLUSIVE)

    def test_unknown_identifier_is_not_resolved_by_a_known_title(self) -> None:
        res = verify_citation(
            {"doi": "10.9999/unlisted", "title": "The complexity of theorem-proving procedures"},
            online=False,
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.value["citation_status"], "unresolved")
        self.assertFalse(res.verified)
        self.assertFalse(res.has_refutation_evidence)

    def test_identifier_normalization_preserves_the_record(self) -> None:
        for citation, field, identifier in (
            ("https://doi.org/10.1145/800157.805047", "doi", "10.1145/800157.805047"),
            ("arXiv:2106.04664v2", "arxiv", "2106.04664"),
            ("arXiv:math/0211159v1", "arxiv", "math/0211159"),
        ):
            with self.subTest(citation=citation):
                res = verify_citation(citation, online=False)
                self.assertTrue(res.ok and res.verified)
                self.assertEqual(res.value["record"][field], identifier)
                self.assertEqual(res.guarantee, Guarantee.CATALOG_LOOKUP)
                self.assertEqual(res.epistemic_state, EpistemicState.INCONCLUSIVE)

    def test_axiom_methods(self) -> None:
        res_lit = self.ax.search_literature("fermat", online=False)
        self.assertTrue(res_lit.ok)

        res_msc = self.ax.lookup_msc("35Q30", online=False)
        self.assertTrue(res_msc.ok)
        self.assertIn("Navier-Stokes", res_msc.value_str)

        res_sw = self.ax.search_software("sympy", online=False)
        self.assertTrue(res_sw.ok)

        res_cit = self.ax.verify_citation("10.1145/800157.805047", online=False)
        self.assertTrue(res_cit.ok)
        self.assertEqual(res_cit.epistemic_state, EpistemicState.INCONCLUSIVE)
        self.assertEqual(res_cit.guarantee, Guarantee.CATALOG_LOOKUP)
        self.assertIn("Cook", str(res_cit.value["record"]["authors"]))

    def test_mcp_literature_tool_dispatch(self) -> None:
        names = {t["name"] for t in TOOL_DEFINITIONS}
        self.assertIn("math_search_literature", names)

        # 1. Search mode
        r1 = dispatch_tool("math_search_literature", {"query": "cook 1971", "online": False})
        self.assertTrue(r1.ok)
        self.assertEqual(r1.guarantee, Guarantee.CATALOG_LOOKUP)

        # 2. Classification mode
        r2 = dispatch_tool("math_search_literature", {"query": "68Q15", "mode": "classification", "online": False})
        self.assertTrue(r2.ok)
        self.assertIn("Complexity", r2.value_str)

        # 3. Software mode
        r3 = dispatch_tool("math_search_literature", {"query": "flint", "mode": "software", "online": False})
        self.assertTrue(r3.ok)
        self.assertIn("FLINT", r3.value_str)

        # 4. Verify citation mode (valid)
        r4 = dispatch_tool("math_search_literature", {"query": "2106.04664", "mode": "verify_citation", "online": False})
        self.assertTrue(r4.ok and r4.verified)
        self.assertEqual(r4.epistemic_state, EpistemicState.INCONCLUSIVE)
        self.assertEqual(r4.guarantee, Guarantee.CATALOG_LOOKUP)

        # 5. Verify citation mode (fake / hallucinated)
        r5 = dispatch_tool("math_search_literature", {"query": "arXiv:9999.00000", "mode": "verify_citation", "online": False})
        self.assertTrue(r5.ok and not r5.verified)
        self.assertEqual(r5.epistemic_state, EpistemicState.INCONCLUSIVE)
        self.assertEqual(r5.value["citation_status"], "unresolved")


if __name__ == "__main__":
    unittest.main()
