# CLAUDE.md — Chronokairo AXIOM Guidelines for Claude

Welcome to **Chronokairo AXIOM** — verifiable computational mathematics infrastructure for AI agents, inspired by [morluto/rea](https://github.com/morluto/rea).

> **Core Directive for Claude:** Never trust a bare mathematical claim when AXIOM can verify it independently. Always inspect `guarantee` and `verification.passed` on every `MathResult`. Never present heuristic or raw computation as proven.

---

## 1. Quick Reference & Common Commands

### 1.1 Running Tests
```bash
# Run full automated test suite (101 tests across 6 suites)
python -m pytest tests/

# Run specific test suites
python -m pytest tests/test_epistemic_states.py   # Epistemic states & integer precision (> 2^53)
python -m pytest tests/test_tamper_detection.py   # Tamper detection and payload revalidation
python -m pytest tests/test_adversarial.py       # Zero-mock adversarial stress tests
python -m pytest tests/test_axiom.py             # Core engine, MCP dispatch & sessions
python -m pytest tests/test_skills.py           # Standardized agent skills test suite
python -m pytest tests/test_use_cases.py         # End-to-end integration use cases

# Run Millennium Research Bench (111 analytical criteria across 7 Clay problems)
python -m benchmarks.millennium.run_millennium_bench
```

### 1.2 Compiling & Auditing Lean 4 Formal Proofs
```bash
# Audit specific Lean 4 formal proofs
lean research/arithmetic/HefezTheorems.lean
lean research/arithmetic/dia_04_bezout.lean
lean research/arithmetic/dia_05_euclid_lemma.lean
lean research/arithmetic/dia_06_fundamental_theorem_existence.lean
lean research/arithmetic/dia_07_fundamental_theorem_uniqueness.lean
lean research/arithmetic/dia_08_euclid_infinitude.lean
lean research/arithmetic/dia_09_diophantine.lean
lean research/arithmetic/dia_10_congruences.lean

# Verify via AXIOM CLI or Python
axiom prove research/arithmetic/dia_10_congruences.lean --engine lean
```

### 1.3 Running AXIOM CLI
```bash
axiom solve "x^2 - 5*x + 6 = 0"
axiom simplify "sin(x)^2 + cos(x)^2"
axiom integrate "sin(x)^2" --variable x
axiom differentiate "x^3 * exp(x)" --variable x
axiom limit "sin(x)/x" --variable x --to 0
axiom evaluate "pi" --precision 50
axiom compare "(x + 1)^2" "x^2 + 2*x + 1"
axiom verify "x^2 - 5*x + 6 = 0" --solutions 2,3
axiom explore "x^3 - 3*x"
axiom number-theory factorint -n 360
axiom number-theory nextprime -n 10
axiom number-theory divisors -n 12
axiom number-theory primefactors -n 360
```
Pass `--json` to any command for structured JSON output matching the MCP contract.

---

## 2. Claude Desktop & Claude Code MCP Configuration

Configure AXIOM as an MCP stdio server in `claude_desktop_config.json` or `.mcp.json`:

```json
{
  "mcpServers": {
    "axiom": {
      "command": "python",
      "args": ["-m", "axiom.mcp_server"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

Or with Claude Code CLI:
```bash
claude mcp add axiom -- python -m axiom.mcp_server
```

---

## 3. Mathematical Epistemic Architecture

### 3.1 Guarantee Hierarchy (Highest to Lowest)
1. `formal-proof` (Rank 5): Machine-checked by Lean 4 kernel with 0 `sorry` and trusted axioms.
2. `exact-symbolic` (Rank 4): Verified symbolic identity (canonical reduction to 0 + spot-checks).
3. `verified-substitution` (Rank 3): Exact algebraic/rational root substitution verified.
4. `numerical-approximation` (Rank 2): Verified numerically within declared `max_error` tolerance.
5. `heuristic` (Rank 1): Plausible output whose independent check was inconclusive.
6. `unverified` (Rank 0): Raw, unverified, or refuted computation.

### 3.2 Four Epistemic States
- **`PROOF`**: Certified formal proof or exact symbolic derivation.
- **`APPROXIMATION`**: Rigorously bounded numerical evaluation with explicit error bounds.
- **`REFUTATION`**: Strictly requires an explicit counterexample witness or violating substitution.
- **`INCONCLUSIVE`**: Fail-closed state when a verification check cannot decide the claim.

### 3.3 Critical Code Invariants
- **Exact Integer Integrity:** In `src/axiom/core.py`, `_values_semantically_equal()` compares integers strictly as exact `int` or `Decimal`. Never route integer comparison through binary `float`, which collapses distinct integers above $2^{53}$.
- **Evidence-Based Refutation:** In `src/axiom/contract.py`, `has_refutation_evidence()` never accepts a bare `"refuted"` label. It requires an explicit witness dictionary or a refuting verification kind.
- **MCP Sandbox:** In `src/axiom/mcp_server.py`, file access is restricted strictly to workspace (`Path.cwd()`) and `<temp>/axiom` (CWE-22 / Least Privilege).
- **Zero Mocks in Verification:** Never use mocks in the critical verification path or adversarial tests.

---

## 4. Coding & Contribution Conventions

- **Language:** Python 3.10+ with strict type annotations on all function signatures.
- **Formality:** Preserve existing docstrings, ADR references, and formal comments.
- **Lean Compatibility:** All Lean 4 formal proofs must maintain dual compatibility with Lean 4.14.0 (CI-pinned toolchain) and Lean 4.35.0 (local development).
- **ADRs:** Any significant architectural, algorithmic, or security change requires recording a new Architecture Decision Record in `docs/adr/`.

---

## 5. Issues & Community Support

* **Found a Bug or Soundness Issue?** Open an issue on GitHub: [https://github.com/chronokairo/axiom/issues](https://github.com/chronokairo/axiom/issues). Provide the mathematical expression, toolchain versions, and reproduction commands.
* **Support AXIOM:** If this project aids your mathematical research or agentic coding, please **Star** the repository on GitHub: [https://github.com/chronokairo/axiom](https://github.com/chronokairo/axiom).
