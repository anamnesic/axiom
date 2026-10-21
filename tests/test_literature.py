"""Unit tests for zbMATH Open literature search and citation verification (arXiv:2106.04664)."""

import json
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
        res = search_literature("riemann hypothesis", online=False)
        self.assertTrue(res.ok)
        self.assertEqual(res.guarantee, Guarantee.CATALOG_LOOKUP)
        self.assertGreater(res.value["count"], 0)
        first = res.value["matches"][0]
        self.assertIn("Riemann", str(first["authors"]))
        self.assertIn("11M06", first["msc"])

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
        self.assertEqual(first["short_title"], "Number theory")

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
        # Verified citation of the zbMATH Open paper itself (arXiv:2106.04664)
        res = verify_citation("arXiv:2106.04664", online=False)
        self.assertTrue(res.ok)
        self.assertTrue(res.verified)
        self.assertEqual(res.guarantee, Guarantee.EXACT_SYMBOLIC)
        self.assertEqual(res.epistemic_state, EpistemicState.PROOF)
        self.assertEqual(res.value["zbl_id"], "7706766")
        self.assertIn("Petrera", str(res.value["canonical_authors"]))

    def test_verify_citation_hallucination_refuted(self) -> None:
        # Fictitious paper identifier should trigger fail-closed refutation with witness
        res = verify_citation("arXiv:9999.99999 Nonexistent False Paper on Zeros", online=False)
        self.assertTrue(res.ok)
        self.assertFalse(res.verified)
        self.assertEqual(res.guarantee, Guarantee.UNVERIFIED)
        self.assertEqual(res.epistemic_state, EpistemicState.REFUTATION)
        self.assertTrue(res.has_refutation_evidence)
        self.assertIn("falsity_witness", res.value)
        self.assertEqual(res.value["falsity_witness"]["registry"], "zbMATH Open (https://zbmath.org)")

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
        self.assertEqual(res_cit.epistemic_state, EpistemicState.PROOF)
        self.assertIn("Cook", str(res_cit.value["canonical_authors"]))

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
        self.assertEqual(r4.epistemic_state, EpistemicState.PROOF)

        # 5. Verify citation mode (fake / hallucinated)
        r5 = dispatch_tool("math_search_literature", {"query": "arXiv:9999.00000", "mode": "verify_citation", "online": False})
        self.assertTrue(r5.ok and not r5.verified)
        self.assertEqual(r5.epistemic_state, EpistemicState.REFUTATION)


if __name__ == "__main__":
    unittest.main()
