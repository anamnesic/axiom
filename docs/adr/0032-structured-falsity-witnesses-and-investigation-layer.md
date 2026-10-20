# ADR-0032: Structured Falsity Witnesses, Strict Payload Integrity, and the Mathematical Investigation Layer

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Chronokairo AXIOM Core Architecture & Verification Team
- **Context:** Post-Audit External Review (20/10/2026) of `454ad8b` — findings on refutation evidence, imported-result integrity, and the start of the v0.3.0 Investigation Layer.

---

## 1. Context and Problem Statement

The 20/10/2026 external review of `454ad8b` confirmed a green CI (run 39473664653, 8/8 jobs, 101/101 tests) and raised two remaining hardening opportunities, plus recommended the long-deferred v0.3.0 work.

1. **Refutation could rest on prose.** `has_refutation_evidence()` accepted a recognised refutation *kind* accompanied only by a human-readable `detail` string. For autonomous research the ideal is a *structured* counterexample that can be stored and re-validated.
2. **A missing persisted value failed open.** `_values_semantically_equal()` returned `True` when the persisted value was `None`, and the payload dispatch guarded every tamper check with `val is not None` — so a payload whose `value` field had been *removed* skipped the revalidation entirely.
3. **The Investigation Layer did not exist.** ADR-0019 specified the eight high-level primitives and the dossier layout, but nothing was implemented.

---

## 2. Architectural Decisions

### 2.1 Structured, Replayable Falsity Witnesses (P1)

- `src/axiom/verification.py` gains `_make_witness(...)`, which builds a uniform, machine-readable falsity certificate:

  ```python
  {"type": "counterexample", "expression": "-x + sqrt(x**2)",
   "substitutions": {"x": "-1"}, "observed": "|diff| = 2.000e+00", "expected": "0"}
  ```

- Every refuting verification kind now records one: `counterexample-search`, `domain-mismatch`, `substitution`, `substitution-domain-error`, `assumption-violation`, `system-substitution`, `constant-exact-disproof`, `approximate-disproof`, `divergent-integral`, `interior-singularity-check`, `numerical-quadrature` (17 instrumented sites in total).
- `revalidate_witness(verification)` **replays** the witness: it re-evaluates the recorded expression at the recorded substitution point and reports one of `confirmed` / `not-replayable` / `failed` / `absent`.
- `has_refutation_evidence()` now requires a *structured* witness (a `witness` record, or a `counterexample` mapping) **and** a refuting verification kind. A prose `detail` is no longer admissible on its own — it is a summary of the witness, not the witness.
- Two kinds that were silently mis-classified were corrected:
  - `substitution` with a residual that *could not be evaluated* is now `substitution-indeterminate` (inconclusive, not a refutation);
  - `system-substitution` with an empty solution set is now `system-empty-solution-set` (inconclusive, not a refutation).
- The payload revalidation path replays the persisted witness: a recorded refutation that no longer reproduces is rejected as an integrity violation.

### 2.2 Strict Payload Integrity (P0)

- `_values_semantically_equal()` no longer treats a missing persisted value as equal to a present recomputed value; a missing value only matches another missing value.
- `_verify_dict_payload()` gains an **integrity gate** keyed by `_VALUE_REQUIRED_KINDS`. A persisted payload is an *audit artifact*, never a fresh computation request: for the 20 operation kinds that always carry a `value`, a payload whose `value` is absent or null is rejected as `tamper/integrity violation` instead of silently skipping the revalidation. A payload recording a failed operation is likewise not re-verifiable.
- This closed a **live hole**: a persisted `number_theory` payload with its `value` deleted was previously accepted as *verified* with no value check at all. The other kinds were fail-closed but reported a misleading `unsupported result payload kind` error.

### 2.3 The Mathematical Investigation Layer (v0.3.0)

- `src/axiom/investigation.py` implements the eight primitives of ADR-0019 over a persistent dossier (`.axiom/investigations/<id>/` with `spec.json`, `graph.json`, `unknowns.json`, `evidence/`, `bundle.json`, `REPORT.md`):

  | Primitive | Behaviour |
  | :--- | :--- |
  | `math_investigate` | Creates the dossier, registers the target claim as an undecided node, records the first unknown. |
  | `math_analyze_claim` | Decomposes the claim into free variables, implicit/explicit hypotheses, and boundary conditions (excluded points, inexact floats). |
  | `math_trace_dependencies` | Classifies each lemma by independent verification and audits the DAG (cycles, dangling edges). |
  | `math_find_counterexample` | Actively refutes the claim, recording the structured counterexample and witness. |
  | `math_compare_proofs` | Compares proof routes and diffs their hypothesis sets (shared vs. route-specific). |
  | `math_list_unknowns` | The Unknown Ledger: blocking gaps, unproved lemmas, pending hypotheses, evidence markers. |
  | `math_get_evidence_bundle` | SHA-256 provenance over every artifact, plus engine versions and per-node verifications. |
  | `math_export_investigation` | Renders `REPORT.md` with the analysis, a Mermaid dependency graph, the ledger and the bundle. |

- The same eight primitives are exposed over **MCP** (29 tools) and the **CLI** (`investigate`, `analyze-claim`, `trace-dependencies`, `find-counterexample`, `compare-proofs`, `list-unknowns`, `get-evidence-bundle`, `export-investigation`).
- **Epistemic contract of the layer:** an investigation orchestrates verified computations but is never itself a proof. Its results carry `guarantee = heuristic`, `epistemic_state = inconclusive`, and **no** `Verification` object — `MathResult.verified` means "an independent mathematical check passed", and an investigation has not had one. Every claim inside the dossier keeps its own guarantee.
- **Semantic anti-drift:** a dependency list certifies graph *structure* only. `dag_structural_integrity` and `logical_implication_proven` are recorded as separate fields, and the latter is always `False` unless a kernel-checked proof establishes the chain.
- A claim is read as an **identity** by default (`mode="identity"`), with `mode="equation"` available for propositions to be solved. The interpretation used is recorded in the dossier so the reading can never drift silently.

---

## 3. Consequences and Validation

- **Refutation means a witness.** A `REFUTATION` now always carries machine-checkable evidence, and the evidence can be replayed on another host.
- **A truncated payload cannot certify itself.** The `number_theory` live hole is closed, and every operation kind now fails closed with an honest error.
- **The Investigation Layer is real.** The eight primitives are implemented, tested (23 dedicated tests), and reachable over MCP and CLI.
- **Test count:** 101 → 143 automated tests across 8 suites.

---

## 4. Supersession and Follow-up

- Extends [ADR-0031](0031-exact-value-integrity-refutation-evidence-and-statistical-corrections.md) (exact value integrity) with the structured-witness contract and the payload integrity gate.
- Implements [ADR-0019](0019-mathematical-investigation-layer-rea-paradigm.md) (Mathematical Investigation Layer), which was previously deferred behind the v0.2.8 CI recovery.
- A real operating-system sandbox for autonomous Lean execution remains the next hardening step before untrusted proof execution is enabled by default.
