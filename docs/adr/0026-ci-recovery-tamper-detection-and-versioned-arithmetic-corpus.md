# ADR-0026: CI Recovery, Tamper-Resistant Revalidation, Imported Hypothesis Downgrading, and Versioned Arithmetic Corpus

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** Chronokairo AXIOM Core Architecture & Verification Team
- **Context:** External Audit Report (19/10/2026), HEAD `8c87fa40613b`, Version `0.2.7`

---

## 1. Context and Problem Statement

An external comprehensive audit performed on 19/10/2026 identified four critical issues requiring immediate remediation:

1. **P1 (CI Blocker — 6/8 matrix jobs failing):**
   `tests/test_axiom.py::TestAxiom::test_research_session_and_auto_formalization` failed on Ubuntu, macOS, and Windows runners in the standard pytest matrix. The test registered a formal Lean proof step alongside symbolic and number-theoretic operations, asserting `all_steps_valid == True`. However, standard matrix jobs do not install `elan` or Lean 4 (which is exclusively installed in the dedicated `formal-lean` job). When Lean was absent, the fail-closed verification pipeline correctly flagged the Lean step as invalid, causing `AssertionError: False is not true`.

2. **P0 (Evidence Integrity Gap — Tamper Detection):**
   In `Axiom._verify_dict_payload()`, revalidating an imported payload checked whether the operation could be re-executed, but did not strictly verify that the recomputed result semantically matched the persisted value in the payload. A tampered JSON file with altered mathematical values could pass revalidation if the underlying operation itself was syntactically executable.

3. **P0 (Hypothesis Integrity Gap — Untrusted Imported Conjectures):**
   When loading a research session from disk, hypotheses were deserialized with their declared `status` (e.g., `"verified"`) and `guarantee` (e.g., `"formal-proof"`), violating fail-closed security. Furthermore, `session.revalidate_all()` did not actively re-verify hypotheses against the local kernel.

4. **P1 (Formal Proof Reproducibility — Gitignored Arithmetic Files):**
   ADR-0024 and ADR-0025 recorded formal Lean 4 demonstrations for Bézout's Identity, Euclid's Lemma, and the Fundamental Theorem of Arithmetic (Existence and Uniqueness), but the proofs resided in `build/book_investigation/`, which is ignored by Git (`.gitignore`). External researchers and open-source contributors could not audit or reproduce these proofs from the repository.

---

## 2. Decision Drivers

- **Fail-Closed Security by Default:** Absence of an external proof engine (e.g., Lean 4) must produce unverified steps without compromising test assertions or masking missing toolchains.
- **Tamper-Proof Epistemic Verification:** Revalidating any persisted payload must certify that the recorded value matches the ground truth recomputed by the local engine. Any deviation must trigger an explicit tamper violation error.
- **Scientific Reproducibility:** Every formal theorem and milestone proof cited in documentation and ADRs must be versioned in Git and continuously validated in CI.

---

## 3. Considered Options & Decisions

### 3.1 CI Matrix Resilience with Strict Fail-Closed Semantics
- **Decision:** Updated `test_research_session_and_auto_formalization` to dynamically query `ax.registry.get("lean").available`.
  - When Lean 4 is installed (local developer workstations, dedicated `formal-lean` CI job): asserts `all_steps_valid == True`.
  - When Lean 4 is absent (6 standard multi-OS/multi-Python matrix runners): asserts `all_steps_valid == False`, verifies that exactly step 5 (the Lean step) is flagged in `invalid_steps`, and asserts `valid_count == len(entries) - 1`.
  - Maintains strict fail-closed behavior without false positives.

### 3.2 Semantic Tamper Detection (`_values_semantically_equal`)
- **Decision:** Implemented `_values_semantically_equal` and integrated tamper verification across all operations in `_verify_dict_payload()`:
  - Supported operations: `solve`, `differentiate`, `integrate`, `limit`, `ode`, `matrix`, `statistics`, `optimize`, `number_theory`, and `tensor`.
  - Value comparisons include:
    - Direct equality and string representations.
    - Numerical float tolerance equivalence.
    - Dictionary key normalization and subset matching.
    - List ordering and multiset permutations (for root sets and factorizations).
    - Symbolic algebraic equivalence via SymPy (`sp.simplify(rec - pers) == 0`).
  - Mismatches immediately return `error_result` with status `tamper/integrity violation` and set `verified = False` / `guarantee = UNVERIFIED`.

### 3.3 Epistemic Downgrading and Active Hypothesis Revalidation
- **Decision:**
  - In `ResearchSession.load()`, all deserialized hypotheses are automatically downgraded:
    - `guarantee = Guarantee.UNVERIFIED.value`
    - `status = "imported_unverified"`
  - In `ResearchSession.revalidate_all()`, every hypothesis is actively passed through `axiom.verify(h.statement)`:
    - If verified: `status = "verified"`, `guarantee` elevated to engine guarantee.
    - If refuted: `status = "refuted"`, `guarantee = UNVERIFIED`.
    - If error/unsolvable: `status = "open"`, `guarantee = UNVERIFIED`.

### 3.4 Versioned Formal Arithmetic Corpus (`research/arithmetic/`)
- **Decision:** Created a canonical Git-tracked directory `research/arithmetic/` containing:
  - `HefezTheorems.lean`: Foundational divisibility and division algorithm.
  - `dia_04_bezout.lean`: Extended Euclidean Algorithm (XGCD) and Bézout's Identity.
  - `dia_05_euclid_lemma.lean`: Coprimality and Euclid's Lemma ($p \mid ab \implies p \mid a \lor p \mid b$).
  - `dia_06_fundamental_theorem_existence.lean`: Constructive prime factorization and existence of prime factor decomposition.
  - `dia_07_fundamental_theorem_uniqueness.lean`: Multiset permutation equivalence and uniqueness of prime factor decomposition.
  - `README.md`: Formal index, reproduction instructions, and epistemic specifications.

### 3.5 Automated CI Compilation of Versioned Proofs
- **Decision:** Updated `.github/workflows/ci.yml` in the `formal-lean` job to:
  1. Compile all `research/arithmetic/*.lean` files directly with `lean` CLI (leanprover/lean4:v4.14.0+).
  2. Audit all formal proofs through `Axiom.verify_lean_file()` with zero axioms and zero `sorry`.

---

## 4. Consequences and Validation

### Positive Consequences
- **Green CI Matrix:** Pytest suites on Ubuntu 3.11/3.12, macOS 3.11/3.12, and Windows 3.11/3.12 now pass cleanly.
- **Robust Tamper Resistance:** Persistent sessions and external JSON files cannot deceive the epistemic verifier.
- **Full Scientific Transparency:** Abramo Hefez formal proofs are openly available in the repository for audit and compilation.
- **Dedicated Regression Suite:** Added `tests/test_tamper_detection.py` validating tamper detection, semantic equivalence, and hypothesis lifecycle.

### Negative Consequences / Trade-offs
- Recomputing and verifying large session payloads incurs small additional CPU overhead during session loading. Mitigated by optional `revalidate=False` flag for fast inspection.
