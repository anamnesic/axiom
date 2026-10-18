---
name: axiom-literature-review
description: Guide AI agents on conducting systematic mathematical literature reviews, mapping prior art taxonomies, tracing theorem dependencies, and synthesizing research context.
---

# Systematic Mathematical Literature Review

Use this skill when mapping the landscape of an existing mathematical field, surveying prior attacks on a conjecture, or synthesizing research context.

---

## 1. Review Methodology for Mathematics

1. **Theorem Lineage Mapping**:
   Trace each modern claim back to its foundational origins (e.g. Clay Problem expositions by Bombieri, Fefferman, Cook, Carlson, Jaffe-Witten, Wiles).
2. **Taxonomy of Prior Attacks**:
   Group existing attempts by mathematical machinery:
   - Sieve methods vs. analytic contour integration.
   - Convex integration vs. Leray-Hopf weak solutions.
   - Geometric flows (Ricci flow with surgery) vs. topological surgeries.
   - Circuit complexity lower bounds vs. algebraic reductions.
3. **Barrier & Bottleneck Identification**:
   Clearly identify *why* prior attacks stalled:
   - What known barrier blocks the approach (e.g. Parity problem in sieve theory)?
   - Which assumptions cannot be lifted without new mathematical structures?

---

## 2. Documenting Literature in AXIOM Sessions

Use AXIOM's session engine to maintain a persistent record of reviewed theorems and lemmas:

```bash
axiom session new --name "riemann-literature" --title "Literature Review: Zeros and Prime Distribution"

# Record landmark theorems as hypothesis notes
axiom session hypothesis --name "riemann-literature" "Euler product identity: sum(1/n^s) = prod(1/(1-p^(-s))) for Re(s) > 1"
axiom session hypothesis --name "riemann-literature" "Bombieri Clay formulation: critical line zeros at Re(s) = 1/2"

# Search Mathlib for formalized lemmas
axiom mathlib "riemann zeta"
```

---

## 3. Review Synthesis Structure

When compiling a literature review dossier:
- **Foundational Statement**: Precise canonical formulation with domain definitions.
- **Milestones Chronology**: Table of published results, theorems proven, and limitations.
- **Formalization Status**: What percentage of the theory is formalized in Lean 4 / Mathlib.
- **Active Research Frontiers**: Leading modern variants, approximations, and numerical verification bounds.
