# COPILOT.md — Chronokairo AXIOM Guidelines for GitHub Copilot

Welcome to **Chronokairo AXIOM** — verifiable computational mathematics infrastructure for AI agents, inspired by [morluto/rea](https://github.com/morluto/rea).

> **Core Directive for GitHub Copilot:** Never guess mathematical results, identities, or roots. Always verify via AXIOM CLI or MCP tools. Never present an unverified or approximate calculation as proven fact.

---

## 1. Quick Development Commands

```bash
# Run all tests
python -m pytest tests/

# Run critical test suites
python -m pytest tests/test_epistemic_states.py   # Large integer comparison & refutation logic
python -m pytest tests/test_tamper_detection.py   # Payload revalidation & tamper detection
python -m pytest tests/test_adversarial.py       # Zero-mock adversarial tests

# Millennium Research Bench
python -m benchmarks.millennium.run_millennium_bench

# Compile Lean 4 proofs
lean research/arithmetic/dia_10_congruences.lean
```

---

## 2. Coding Rules for Copilot Completions

1. **Strict Type Annotations:** Every Python function and method must declare return types and parameter types (`from __future__ import annotations`, `str | None`, `list[int]`, etc.).
2. **Never Cast Large Integers to Float:**
   - Do NOT write `float(a) == float(b)` for integers. Python integers have arbitrary precision, while IEEE-754 floats lose precision above $2^{53}$.
   - Use `_is_exact_int` and exact equality (`==`) or `Decimal`.
3. **No Mocks in Verification Paths:**
   - When writing tests for mathematical verification, use the real `Axiom` instance and actual engines. Never mock `sympify`, `solve`, or `prove`.
4. **Lean 4 Dual Compatibility:**
   - All `.lean` files must compile under Lean 4.14.0 (the CI-pinned compiler) and Lean 4.35.0 (local).
   - Use `omega` for linear integer arithmetic. Avoid lemmas introduced only in newer versions (such as `Int.add_neg_eq_sub` or `Nat.gcd_add_self_right`).
5. **Epistemic State Contracts:**
   - A `MathResult` carries an `epistemic_state` (`PROOF`, `APPROXIMATION`, `REFUTATION`, `INCONCLUSIVE`).
   - `REFUTATION` is only valid when a concrete falsity witness or counterexample exists. Failed or undecidable checks must evaluate to `INCONCLUSIVE`.

---

## 3. MCP & CLI Reference

Start the MCP server:
```bash
axiom mcp
# or: python -m axiom.mcp_server
```

Common CLI invocations:
```bash
axiom solve "x^2 - 5*x + 6 = 0"
axiom simplify "sin(x)^2 + cos(x)^2"
axiom verify "x^2 - 5*x + 6 = 0" --solutions 2,3
axiom number-theory factorint -n 360
axiom number-theory nextprime -n 10
axiom number-theory divisors -n 12
axiom number-theory primefactors -n 360
```

---

## 4. Issues & Community Support

* **Found a Bug or Soundness Issue?** Open an issue on GitHub: [https://github.com/chronokairo/axiom/issues](https://github.com/chronokairo/axiom/issues). Provide the mathematical expression, toolchain versions, expected vs. actual guarantee, and minimal reproduction CLI/Python command.
* **Support AXIOM:** Star the repository on GitHub: [https://github.com/chronokairo/axiom](https://github.com/chronokairo/axiom) to support verifiable computational mathematics for AI agents.
