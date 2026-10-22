# Literature lookup and citation resolution

Bibliographic lookup is operational evidence, **not a mathematical proof**.

| Outcome | Guarantee | `verification.passed` | Epistemic state |
| --- | --- | --- | --- |
| Matching catalog record / resolved citation | `catalog-lookup` | `true` | `inconclusive` |
| No record in the searched catalog | `unverified` | `false` | `inconclusive` |
| Resolved identifier with mismatched claimed authors | `unverified` | `false` | `inconclusive` |

Here a passing verification means bibliographic resolution succeeded. Always
inspect the guarantee as well: it never certifies a cited theorem. Absence
from a finite catalog is not proof of fabrication and must not become
`refutation`. `hallucination_suspected` requests review, not a verdict.

## Public result fields

- `search_literature`: `value.matches` contains records with `authors`, `msc`,
  `doi`, `arxiv`, `zbmath_id`, `zbl`, and `provenance`.
- `lookup_msc`: each match contains `code`, `long_title`, `parent`, and `url`.
  The public label is `long_title`, not `short_title`.
- `verify_citation`: `value.citation_status` is `resolved`,
  `attribution_mismatch`, or `unresolved`. A matched record lives under
  `value.record`; its authors are `value.record.authors`.
- `zbmath_id` (internal document id) and `zbl` (bibliographic classification
  identifier) are distinct and may be null. Do not infer either from another
  paper by the same author or from a record merely citing the paper.

For example, the offline record for `arXiv:2106.04664` has no indexed
`zbmath_id`. The identifier `7706766` belongs to the separate record
*The integration of OEIS links in zbMATH Open* (`10.4171/MAG/132`).

## Offline coverage and regression tests

`online=False` searches only the curated subset; it does not query zbMATH or
assert that every relevant paper is included. For example, `cook 1971`
matches that subset, whereas `riemann hypothesis` currently does not.
Missing coverage is reported explicitly rather than filled with invented
metadata. Tests check exact identifiers, normalization, attribution mismatch,
unknown identifiers despite a familiar title, and fail-closed empty searches:

```bash
python -m pytest tests/test_literature.py -q
```

These tests exercise offline data and Python/MCP interfaces. They do **not**
provide live registry verification. The six failures recorded during Day 12
were stale expectations of guarantees and fields, including an unrelated
document id; fixing them must not weaken the existing epistemic contract.
