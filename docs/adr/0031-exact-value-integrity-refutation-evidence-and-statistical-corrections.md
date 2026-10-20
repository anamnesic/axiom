# ADR-0031: Exact Value Integrity, Refutation Evidence, and Statistical Correction

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Chronokairo AXIOM Core Architecture & Verification Team
- **Context:** Post-Audit External Review (20/10/2026) of `b9dcd00d` and its successors — findings on integer precision in the tamper comparator, evidence-free refutation, and inconsistent statistical bounds.

---

## 1. Context and Problem Statement

The 20/10/2026 external audit of the `b9dcd00d` update raised two P0 blockers (a CI test asserting a hardcoded session step ordinal, and a Lean lemma absent from the CI-pinned toolchain) and three substantive integrity findings beyond the CI:

1. **Integer precision loss in the tamper comparator.** `_values_semantically_equal()` reconciled a recomputed value with a persisted payload through a binary `float` comparison. IEEE-754 doubles collapse distinct integers above $2^{53}$, so a payload whose value had been altered by **one unit** was accepted as authentic.
2. **Refutation without evidence.** `MathResult.epistemic_state` returned `REFUTATION` whenever `value_str == "refuted"` or the payload carried `status = "disproven"`, without requiring a certificate of falsity. A verification that merely *failed* (undecidable, out of scope, aborted) was therefore reported as a mathematical disproof.
3. **Inconsistent statistical bounds.** The Clopper-Pearson upper bound published for $0/21$ ($13.06\%$) matched *no* convention (two-sided: $16.11\%$; one-sided: $13.29\%$), the documents mixed one-sided and two-sided conventions across cases, and the false-positive rate was reported against $n = 21$ instead of the $n = 13$ mathematically invalid cases.

Two further defects were found while reproducing the audit locally, beyond its scope:

4. **A new Lean 4.14.0 incompatibility.** The `Nat.gcd_add_self_right` blocker had already been remediated at `af70b97`, but the replacement proof introduced `Int.add_neg_eq_sub`, which is itself absent from Lean 4.14.0 — the toolchain pinned by the `formal-lean` CI job. The corpus therefore still failed on CI.
5. **A report/artifact divergence.** `experiments/exp-0001/REPORT.md` reported 3 false negatives for the baseline while `results.json` recorded 4, so the published global accuracy (57.1%) did not match the artifact (52.4%).

---

## 2. Architectural Decisions

### 2.1 Exact Integer Comparison (P0)
- `_values_semantically_equal()` in `src/axiom/core.py` no longer routes integer equality through a binary `float`:
  - two exact integers are compared **exactly**; a mismatch returns `False` and is never reconciled;
  - an exact integer against a *numeric string* is compared as an exact `Decimal`, so `$2^{53}+1$ is not accepted against the string `"9007199254740992"`;
  - an exact integer against a *float* is decided by the exact Python comparison only (Python compares an `int` with a `float` without rounding the integer), and a lossy float is never accepted;
  - tolerances remain admissible only between values that are already floating-point approximations.
- The symbolic fallback was audited and is sound: `Parser.parse_expression()` produces a SymPy `Integer` for integer literals, so `simplify(lhs - rhs) == 0` cannot collapse two distinct large integers.

### 2.2 Refutation Requires a Witness (P1)
- `src/axiom/contract.py` introduces `REFUTING_VERIFICATION_KINDS` (kinds that are *by construction* a disproof: `counterexample-search`, `constant-exact-disproof`, `approximate-disproof`, `domain-mismatch`, `substitution`, `substitution-domain-error`, `system-substitution`, `assumption-violation`, `divergent-integral`, `interior-singularity-check`, `numerical-quadrature`) and `has_refutation_evidence()`.
- `MathResult.epistemic_state` now returns `REFUTATION` **only** when a witness exists: an explicit counterexample/witness in `verification.data`, a `disproven`/`refuted` status, or a refuting verification kind with a non-empty detail. Everything else is fail-closed `INCONCLUSIVE`.
- Kinds that fail because the question could not be decided (`constant-exact-inconclusive`, `unevaluated-integral`, `definite-integral-check`, `inequality-check`, `empty-solution-set`, `numerical-spot-check`) are explicitly *excluded* from the refuting set.
- `outcome_word()` centralises the `verified` / `refuted` / `inconclusive` tri-state and replaces the previous `value_str = "verified" if ver.passed else "refuted"` idiom in `core.py` (root-substitution and definite-integral paths) and in the session hypothesis paths (`core.py`, `session.py`).

### 2.3 Lean 4.14.0 Compatibility of the Arithmetic Corpus (P0)
- `research/arithmetic/dia_10_congruences.lean` replaced `Int.add_neg_eq_sub` with `Int.sub_eq_add_neg`, which exists in **both** Lean 4.14.0 (`Init/Data/Int/Lemmas.lean`) and 4.35.0. The whole corpus (`HefezTheorems.lean`, `dia_04` … `dia_10`) was compiled against both toolchains to prove the CI contract.

### 2.4 Positional Test Assertions Replaced by Semantic Identification (P0)
- `tests/test_axiom.py` no longer asserts a hardcoded session step ordinal. The Lean step is identified by its operation kind (`kind == "prove"`), because the ordinal is positional: it shifts whenever a hypothesis or an extra record is added. The previous assertion (`assertIn(5, invalid_steps)`) was false — the session returns `[4]` — and it only ever executed on runners *without* a Lean toolchain, i.e. precisely on the CI matrix.

### 2.5 Statistical Bounds and Baseline Provenance (P1)
- A single, explicitly labelled **two-sided (bilateral) 95% Clopper-Pearson** convention is adopted across `RESEARCH.md`, `experiments/exp-0001/REPORT.md`, `benchmarks/millennium/README.md`, and `README.md`:

  | Observed | Rule of Three | Two-sided 95% CP | One-sided 95% upper |
  | --- | --- | --- | --- |
  | $0/13$ (EXP-0001 invalid cases) | $23.08\%$ | $[0.00\%, 24.71\%]$ | $20.58\%$ |
  | $0/21$ (EXP-0001 full battery) | $14.29\%$ | $[0.00\%, 16.11\%]$ | $13.29\%$ |
  | $0/40$ (Millennium negative controls) | $7.50\%$ | $[0.00\%, 8.81\%]$ | $7.22\%$ |

- The false-positive rate is reported over the $n = 13$ mathematically invalid cases; the $n = 21$ battery is reported separately.
- The baseline is described as what it actually is: an **emulated unguarded CAS on SymPy** that includes a fixed 6-point sampling probe, whose `formal_proof` row is **simulated** (the Lean compiler is never invoked). The provenance is now emitted machine-readably under `summary["baseline"]` in `results.json`, with the simulated row flagged as `simulated: true`.
- `REPORT.md` was corrected to the artifact values (4 baseline false negatives; 52.4% global accuracy) and a new §3.1 enumerates the four false negatives.

### 2.6 Dedicated Adversarial Suite for the Epistemic States
- `tests/test_epistemic_states.py` adds a dedicated suite covering: the four-state classification; the *absence* of refutation evidence for undecidable checks; the exclusion of inconclusive kinds from the refuting whitelist; the exact-integer comparator at and above $2^{53}$; and an end-to-end tamper detection on a persisted `binomial(100, 50)` payload (a value far above $2^{53}$), which the pre-fix comparator silently accepted.

---

## 3. Consequences and Validation

- **Integrity restored:** a payload tampered by one unit above $2^{53}$ is now rejected; the regression test reproduces the pre-fix acceptance.
- **Fail-closed preserved:** `REFUTATION` now means "a witness exists", and `INCONCLUSIVE` covers every undecidable outcome.
- **CI contract proven locally:** the Lean corpus compiles on the CI-pinned Lean 4.14.0 *and* on 4.35.0; the full test suite passes both with and without a Lean toolchain on `PATH`.
- **Test count:** 84 → 100 automated tests across 6 suites.

---

## 4. Supersession and Follow-up

- Amends [ADR-0027](0027-epistemic-state-separation-statistical-bounds-and-research-whitepaper.md) §2.2 (statistical bounds and baseline definition).
- Amends [ADR-0026](0026-ci-recovery-tamper-detection-and-versioned-arithmetic-corpus.md) in the scope of the tamper comparator (exact integer semantics).
- The Investigation Layer ([ADR-0019](0019-mathematical-investigation-layer-rea-paradigm.md)) remains **deferred** until the v0.2.8 CI matrix is confirmed green.
