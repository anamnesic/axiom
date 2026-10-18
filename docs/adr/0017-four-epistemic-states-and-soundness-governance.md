# ADR-0017: Four Epistemic States, Specification Soundness Governance & Execution Isolation

- **Status:** Accepted
- **Date:** 2026-10-18
- **Authors:** AXIOM Engineering Team & Chronokairo Research
- **Deciders:** Mathematical Core Working Group
- **Consulted:** Automated Reasoning & Neuro-Symbolic Verification Team
- **Informed:** AI Coding & Research Agents (Antigravity, Codex, Claude Code, Cursor)

---

## Context & Problem Statement

In automated mathematical reasoning and neuro-symbolic systems, models frequently blur the boundaries between distinct epistemic states:
1. Conflating a numerical approximation or empirical check with an exact formal proof.
2. Promoting a statement to `verified` merely on lexical overlap with a canonical specification name.
3. Granting `formal-proof` to imported or cached JSON payloads without executing the underlying proof assistant kernel on the local machine.
4. Conflating local step validity with multi-step dependency chain soundness.
5. Executing untrusted Lean 4 scripts without isolation, resource bounds, or timeout guarantees.
6. Permitting MCP file operations to traverse outside authorized directories.
7. Accepting inconsistent benchmark metrics or missing validation outputs.

To establish true mathematical reliability, AXIOM must systematically enforce the 10 specification soundness and epistemic integrity requirements.

---

## Decision Drivers

1. **Epistemic Rigor**: Strict differentiation among four mathematical states:
   - **Proof (Prova)**
   - **Approximation (Aproximação)**
   - **Refutation (Refutação)**
   - **Inconclusive (Inconclusão)**
2. **Anti-Hallucination & Anti-Spoofing**: No lexical match alone can ever produce `verified` alignment or certification.
3. **Formal Statement Integrity**: Robust depth-aware extraction of Lean 4 declaration binders (typed, implicit, and typeclass) and return propositions.
4. **Revalidation Gating**: Imported or cached results can never receive `formal-proof` without active local re-verification through the Lean 4 kernel.
5. **Separation of Validity**: In research derivations, isolated step validity and dependency chain validity are tracked and audited separately.
6. **Execution Isolation & Sandbox Bounds**: Untrusted Lean execution is sandboxed with strict memory (`-M 2048`), elaborator heartbeats (`-T 100000`), and process timeouts.
7. **MCP Directory Security**: MCP file operations (`math_plot`, `math_prove`, `math_verify`, `math_session`) are strictly confined to authorized project roots.
8. **Benchmark Invariant Enforcement**: Millennium Research Bench must fail-closed on inconsistent metric counts/rates or missing outputs.
9. **CI Verification**: Adversarial test suites execute without mocks in the critical path.

---

## Considered Options

- **Option A (Heuristic)**: Rely on string heuristics and permissive caching. *(Rejected: permits specification drift and false positives).*
- **Option B (Strict Epistemic Governance — Chosen)**: Formally separate the four epistemic states, require certified symbolic/kernel equivalence for `verified`, isolate untrusted executions, gate imported claims, and validate metric invariants.

---

## Decision Outcome

Adopted **Option B**.

### 1. Four Epistemic States Architecture

AXIOM explicitly categorizes every computation into one of four mutually exclusive epistemic states:

| Epistemic State | Guarantees / Status | Definition & Invariants | Verification Criteria |
| :--- | :--- | :--- | :--- |
| **Proof (Prova)** | `formal-proof`, `exact-symbolic`, `verified-substitution` | Certified mathematical truth. An exact symbolic identity, machine-checked Lean 4 kernel derivation, or verified equation roots. | `Verification.passed == True`, exact symbolic residual $0$, no untrusted axioms, congruent spec alignment. |
| **Approximation (Aproximação)** | `numerical-approximation`, `approximately_equal` | Numerical evaluation or bounded sequence probing within specified tolerance $\epsilon$. Inexact float absorption is rejected. | Finite error $\le \epsilon$, `equivalent == False`, `approximately_equal == True`. Never granted `EXACT_SYMBOLIC`. |
| **Refutation (Refutação)** | `refuted`, `disproven` | Concrete counterexample discovered, candidate root fails substitution ($f(r) \neq 0$), or reflexive tautology rejected. | Independent verification proves the claim is false. `Verification.passed == False`, `value_str == "refuted"`. |
| **Inconclusive (Inconclusão)** | `inconclusive`, `unverified` | Truth or equivalence cannot be determined within available symbolic algorithms, samples, or timeouts. | Fail-closed state. `guarantee == Guarantee.UNVERIFIED`. Never promoted to proof. |

### 2. Lexical Matching Rule

Lexical keyword overlap between a formal source and a canonical statement produces at most `candidate` (`congruent = False`, `is_aligned = True`), NEVER `verified`. The `verified` state requires certified symbolic reduction or interactive theorem proving equivalence.

### 3. Lean Signature Audit

Replaced brittle regular expressions with a depth-aware tokenizer (`_extract_lean_declarations`) tracking nested parentheses `()`, braces `{}`, and brackets `[]` to correctly isolate parameter binders from the top-level proposition separator `:`.

### 4. Imported Result Revalidation

Any payload loaded from disk or JSON claiming `formal-proof` is marked `revalidated = False` and downgraded to `unverified` in derivation chains unless actively revalidated by executing Lean 4 on the current host.

### 5. Step vs. Chain Validity

Every step in `ResearchSession` records:
- `step_valid`: Local verification in isolation.
- `chain_valid`: Unbroken validity across all transitive dependencies.
- `step_guarantee` vs. `chain_guarantee`.

### 6. Sandboxing & Resource Bounds

Untrusted Lean 4 scripts run in an isolated temporary sandbox (`tempfile.mkdtemp` or `.axiom_scratch`) with `-M 2048`, `-T 100000`, and strict configurable timeout. `subprocess.TimeoutExpired` is handled gracefully without unhandled exceptions.

### 7. MCP Directory Restrictions

Path arguments across MCP tools are resolved and checked against authorized project and temp directory roots via `validate_mcp_path()`. Path traversal attempts are rejected with `Permission denied`.

### 8. Benchmark Invariant Rejection

`run_millennium_bench.py` and `run_benchmarks.py` validate metric counts (`pos_count`, `neg_count`, `tp_count`, `fc_count`, `fp_count`) and rates for mathematical consistency and reject missing stdout/files.

---

## Consequences

- **Positive**: Complete elimination of false positives from lexical matching and un-revalidated imports.
- **Positive**: Safe multi-step derivation graphs where broken intermediate steps invalidate dependent chains without discarding locally valid steps.
- **Positive**: Full adversarial test suite (`tests/test_adversarial.py`) running in CI with 0 mocks in the critical path.
