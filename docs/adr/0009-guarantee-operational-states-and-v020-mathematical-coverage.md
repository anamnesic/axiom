# ADR-0009: Operational Guarantee States & v0.2.0 Mathematical Coverage

- **Status:** Accepted
- **Date:** 2026-10-17

## Context

An architectural and competitive audit of `v0.1.2` identified two classes of gaps:

1. **Epistemic Overclaiming on Non-Proof Operations (`Guarantee` Contract):**
   - `Axiom.parse` previously returned `Guarantee.EXACT_SYMBOLIC` with `verification=None` (`res.verified == False`), even though parsing an AST is a structural transformation rather than a proof of an algebraic identity.
   - `Axiom.search_mathlib` previously returned `Guarantee.EXACT_SYMBOLIC` whenever at least one theorem matched in the catalog, conflating a catalog signature lookup with an independently verified symbolic identity.
   - `Axiom.plot` previously returned `Guarantee.NUMERICAL_APPROXIMATION`, conflating discrete curve visualization with a bounded-error numerical calculation.

2. **Edge-Case Mathematical Coverage (`v0.2.0`):**
   - **Branch Cuts & Symbol Assumptions:** Expressions like $\sqrt{x^2} = x$ hold only for $x \ge 0$, not over general reals ($x = -1$ is a counterexample), and users/agents needed a declarative `assumptions` interface with contradiction checking.
   - **Definite Integrals Across Interior Singularities:** Naive Fundamental Theorem of Calculus evaluation $F(b) - F(a)$ across a non-integrable interior pole (such as $\int_{-1}^1 \frac{1}{x^2}\,dx$) must never be accepted.
   - **Two-Sided Limits (`direction="+-"`):** SymPy's `sp.limit(expr, var, point)` defaults to `dir="+"` (right-hand limit only!). Computing a two-sided limit without explicitly comparing `dir="-"` and `dir="+"` silently accepted jump discontinuities like $\lim_{x \to 0} |x|/x$ as `1`.
   - **Extraneous Roots & Periodic Solution Sets:** Candidate roots that hit removable or non-removable poles (`0/0` or `oo` in `lhs` or `rhs`, such as $x = 1$ in $(x^2 - 1)/(x - 1) = 0$) must be rejected, and periodic equations ($\sin(x) = 0$) should expose their full `solveset` family.

## Decision

1. **Separate Mathematical Claims from Operational States in `Guarantee` (`src/axiom/contract.py`):**
   - Retain the 4 mathematical correctness claims (`FORMAL_PROOF`, `EXACT_SYMBOLIC`, `VERIFIED_SUBSTITUTION`, `NUMERICAL_APPROXIMATION`) where `Guarantee.is_mathematical_claim == True`.
   - Add 3 explicit operational states (`STRUCTURAL_PARSE`, `CATALOG_LOOKUP`, `SAMPLED_VISUALIZATION`) alongside `HEURISTIC` and `UNVERIFIED` where `Guarantee.is_mathematical_claim == False`.
   - Enforce in `MathResult.__post_init__` that instantiating a `MathResult` with `guarantee.is_mathematical_claim == True` without `verification is not None and verification.passed is True` raises `ValueError`.
   - Assign `STRUCTURAL_PARSE` (with an `ast-roundtrip` verification) to `Axiom.parse`, `CATALOG_LOOKUP` to `Axiom.search_mathlib`, and `SAMPLED_VISUALIZATION` to `Axiom.plot`.

2. **Deliver `v0.2.0 — Mathematical Coverage` (`src/axiom/parsing.py`, `src/axiom/verification.py`, `src/axiom/engines/sympy_engine.py`, `src/axiom/engines/lean_engine.py`):**
   - Add `assumptions` support (`positive`, `negative`, `real`, `integer`, `even`, `odd`, `nonzero`, etc.) and contradiction detection (`positive` + `negative`, `even` + `odd`) to `Parser`, `Axiom.simplify`, `Axiom.compare`, `Axiom.solve`, `Axiom.verify`, and `Axiom.parse`.
   - Probe clean exact rationals (`-1`, `2`, `-2`, `3`, `-3/2`) and alternating-sign transcendentals in `verify_equivalence` so branch-cut false identities like $\sqrt{x^2} = x$ are deterministically refuted with `{"x": "-1"}`.
   - Detect non-integrable interior and endpoint poles in `_find_nonintegrable_poles` / `verify_integral`.
   - Explicitly compute and compare both left (`dir="-"`) and right (`dir="+"`) limits in `SymPyEngine.limit` and `verify_limit` when `direction == "+-"`.
   - Audit `lhs` and `rhs` separately for pole/domain violations (`nan`, `zoo`, `oo`) in `SymPyEngine.solve` and `verify_solutions`, and annotate periodic infinite solution sets via `sp.solveset`.
   - Flag syntactic reflexive tautologies (`X = X`) via `LeanEngine.detect_trivial_reflexive_theorems`.

## Consequences

- No non-proof operation (`parse`, `search_mathlib`, `plot`) can ever be misclassified as `EXACT_SYMBOLIC` or `NUMERICAL_APPROXIMATION`, and `MathResult.__post_init__` enforces verification presence at runtime.
- Branch cuts, interior poles in definite integrals, jump discontinuities in two-sided limits, and extraneous roots at removable singularities are deterministically caught and tested by the 37-test suite.
