# ADR-0008: Verification Integrity (`v0.1.1`) and Live Lean 4 / Lake CI Integration (`v0.1.2`)

- **Status:** Accepted
- **Date:** 2026-10-17
- **Author:** Chronokairo ([chronokairo.com](https://chronokairo.com))

## Context

Following the review of commit `7e7656e8f59c` (where all 7/7 CI jobs passed), three critical improvements for rigorous mathematical verification semantics were identified:

1. **P0 — Lean 4 Audited Declaration Coverage (`formal-proof`):** `LeanEngine.prove()` verified `proc.returncode == 0`, `not has_hole`, and `len(untrusted_axioms) == 0`, but did not require a non-empty list of theorem/lemma declarations (`theorem_names`) or confirm that Lean's stdout actually emitted `#print axioms` audit lines covering every declared theorem.
2. **P0 — Separation of Numerical Evidence from Exact Symbolic Identity (`exact-symbolic` vs `numerical-approximation`):**
   - `verify_derivative()` granted `Guarantee.EXACT_SYMBOLIC` after finite-difference agreement at 5 sample points without an independent symbolic proof.
   - `verify_integral()` on definite integrals granted `Guarantee.EXACT_SYMBOLIC` from numerical quadrature (`mpmath.quad`) alone before checking the symbolic Fundamental Theorem of Calculus (FTC).
   - `verify_limit()` granted `Guarantee.EXACT_SYMBOLIC` from 3-point numerical sequence probing alone.
   - `_is_symbolic_zero()` invoked `sp.nsimplify()`, which could round small `Float` values (e.g., `1e-16`) to `0`.
3. **P1 — Live Lean 4 + Lake Integration in CI:** The GitHub Actions workflow did not install `elan` / Lean 4 / `lake` to execute real formal proofs (both valid and invalid) against the live Lean 4 kernel.

## Decision

1. **Mandatory Audited Theorem Coverage (`src/axiom/engines/lean_engine.py`, `src/axiom/core.py`):**
   - Add `LeanEngine.extract_audited_theorems()` and `LeanEngine.verify_theorem_audit_coverage()` to parse every `'thm' depends on axioms: [...]` and `'thm' does not depend on any axioms` line from Lean's output.
   - Require `len(theorem_names) > 0` and confirmation that every declared theorem in `theorem_names` appears in `audited_theorems` before setting `kernel_ok = True` or granting `Guarantee.FORMAL_PROOF`. Declaration-free files (e.g., comments or `#check` only) are strictly classified as `Guarantee.UNVERIFIED`.
2. **Strict Separation of Symbolic vs Numerical Guarantees (`src/axiom/verification.py`):**
   - Remove `sp.nsimplify()` from `_is_symbolic_zero()` and reject any expression containing `sp.Float` from being classified as an exact symbolic zero.
   - In `verify_derivative()`, perform an independent symbolic antiderivative round-trip ($\text{var} \notin \text{free\_symbols}(f(x) - \int g(x)\,dx)$) alongside 80-digit central finite differences. Grant `Guarantee.EXACT_SYMBOLIC` only when the symbolic round-trip and finite differences both succeed; when only finite differences succeed, return `Guarantee.NUMERICAL_APPROXIMATION`.
   - In `verify_integral()` for definite integrals, require both the symbolic FTC check ($F'(x) = f(x)$ and $F(b) - F(a) = R$ by exact symbolic reduction) and numerical quadrature agreement (when non-parametric) for `Guarantee.EXACT_SYMBOLIC`. When only numerical quadrature confirms the integral, return `Guarantee.NUMERICAL_APPROXIMATION`.
   - In `verify_limit()`, perform independent symbolic verification via algebraic cancellation, L'Hôpital differentiation, or formal Taylor/Laurent series expansion (`sp.series`). Grant `Guarantee.EXACT_SYMBOLIC` only when a symbolic method and sequence probing both pass; when only numerical sequence probing passes, return `Guarantee.NUMERICAL_APPROXIMATION`.
3. **Live Lean 4 + Lake CI Job (`.github/workflows/ci.yml`, `tests/lean_project/`):**
   - Add a dedicated `formal-lean` CI job that installs `elan` and `leanprover/lean4:v4.14.0` (with `~/.elan` caching) and sets `AXIOM_REQUIRE_LEAN=1`.
   - Add `tests/lean_project/` (`lakefile.lean`, `lean-toolchain`, `AxiomFormalTests.lean`) and `test_lean4_live_kernel_and_lake_integration` testing constructive proofs, classical proofs (`Classical.choice`), anonymous `example` declarations, `sorry` rejection, custom `axiom` rejection via `#print axioms`, declaration-free rejection, and false theorem rejection.

## Consequences

- `Guarantee.EXACT_SYMBOLIC` and `Guarantee.FORMAL_PROOF` now have strict, mathematically rigorous semantics backed by both unit tests and live Lean 4 kernel execution in CI.
