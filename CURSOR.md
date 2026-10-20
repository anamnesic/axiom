# CURSOR.md — Chronokairo AXIOM Guidelines for Cursor AI

Welcome to **Chronokairo AXIOM** — verifiable computational mathematics infrastructure for AI agents, inspired by [morluto/rea](https://github.com/morluto/rea).

> **Core Directive for Cursor:** Never trust a bare mathematical claim when AXIOM can verify it independently. Always check `guarantee` and `verification.passed` on every `MathResult`. Respect fail-closed verification.

---

## 1. Quick Development Workflow

```bash
# Run tests
python -m pytest tests/
python -m pytest tests/test_epistemic_states.py

# Millennium Bench
python -m benchmarks.millennium.run_millennium_bench

# Lean 4 proof check
lean research/arithmetic/dia_10_congruences.lean
```

---

## 2. Cursor Rules & Conventions

- **Precision Safety:** Do not convert integers to `float` when checking equality or verifying hashes/payloads. Integers $> 2^{53}$ collapse in IEEE-754 binary floats.
- **Fail-Closed Reporting:** `REFUTATION` requires an explicit witness or counterexample in `verification.data` or `value`. An inconclusive or undecidable check must remain `INCONCLUSIVE`.
- **MCP Sandbox:** In `src/axiom/mcp_server.py`, file operations are restricted to `Path.cwd()` and `<temp>/axiom` (CWE-22 / Least Privilege).
- **Dual Toolchain Lean 4:** Ensure proofs in `research/arithmetic/` compile cleanly under both Lean 4.14.0 (pinned on CI) and Lean 4.35.0 (local).
- **Zero Mocks in Critical Path:** Never mock mathematical verification, algebraic simplification, or Lean kernels.

---

## 3. Cursor MCP Setup

Add AXIOM to your Cursor MCP settings (`Cursor Settings > Features > MCP`):
- **Name:** `axiom`
- **Type:** `command`
- **Command:** `python -m axiom.mcp_server`

---

## 4. Issues & Community Support

* **Report an Issue:** [https://github.com/chronokairo/axiom/issues](https://github.com/chronokairo/axiom/issues)
* **Star the Repo:** [https://github.com/chronokairo/axiom](https://github.com/chronokairo/axiom)
