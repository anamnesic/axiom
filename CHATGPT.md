# CHATGPT.md — Chronokairo AXIOM Guidelines for ChatGPT & OpenAI Agents

Welcome to **Chronokairo AXIOM** — verifiable computational mathematics infrastructure for AI agents, inspired by [morluto/rea](https://github.com/morluto/rea).

> **Core Directive for ChatGPT / OpenAI Agents:** Never trust a bare mathematical claim or conjecture when AXIOM can verify it independently. Inspect `guarantee`, `epistemic_state`, and `verification.passed` on every `MathResult`. Never present heuristic or raw computation as proven.

---

## 1. Interaction Modes

### 1.1 Model Context Protocol (MCP) Mode
When running as an agent connected to the AXIOM MCP stdio server:
- Execute `math_parse`, `math_simplify`, `math_solve`, `math_differentiate`, `math_integrate`, `math_limit`, `math_evaluate`, `math_compare`, `math_matrix`, `math_number_theory`, `math_ode`, or `math_prove`.
- Always inspect the returned JSON `guarantee` (`formal-proof`, `exact-symbolic`, `verified-substitution`, `numerical-approximation`, `heuristic`, `unverified`) and `epistemic_state` (`PROOF`, `APPROXIMATION`, `REFUTATION`, `INCONCLUSIVE`).

### 1.2 Python / Code Interpreter Mode
When running code in an environment with AXIOM installed:
```python
from axiom import Axiom

ax = Axiom()
res = ax.solve("x^2 - 5*x + 6 = 0")
print(res.epistemic_state, res.verified, res.guarantee)

res_proof = ax.verify_lean_file("research/arithmetic/dia_10_congruences.lean")
print(res_proof.epistemic_state, res_proof.verified, res_proof.guarantee)
```

---

## 2. Epistemic Integrity Invariants

1. **Exact Integer Comparisons:**
   - Integers larger than $2^{53}$ must never be converted to `float` for equality testing ($2^{53} == 2^{53} + 1$ in IEEE-754). Use exact integer equality or `Decimal`.
2. **Witness Requirement for Refutation:**
   - A mathematical refutation is only certified if an explicit counterexample witness is identified and recorded in `verification.data`. Failed checks without witnesses must be labeled `INCONCLUSIVE`.
3. **Fail-Closed Principle:**
   - If an algorithm or theorem prover cannot decide an equality, do not guess or assert truth. State clearly that the proof is inconclusive.
4. **Sandboxed File Operations:**
   - All file operations must respect authorized directories (`cwd` and `<temp>/axiom`).

---

## 3. Quick CLI Commands

```bash
axiom solve "x^2 - 5*x + 6 = 0"
axiom simplify "sin(x)^2 + cos(x)^2"
axiom compare "(x + 1)^2" "x^2 + 2*x + 1"
axiom verify "x^2 - 5*x + 6 = 0" --solutions 2,3
axiom number-theory factorint -n 360
axiom number-theory nextprime -n 10
axiom number-theory divisors -n 12
axiom number-theory primefactors -n 360
```

---

## 4. Issues & Community Support

* **Found a Bug or Soundness Issue?** Open an issue on GitHub: [https://github.com/chronokairo/axiom/issues](https://github.com/chronokairo/axiom/issues). Provide the mathematical expression, toolchain versions, expected vs. actual guarantee, and minimal reproduction commands.
* **Support AXIOM:** Star the repository on GitHub: [https://github.com/chronokairo/axiom](https://github.com/chronokairo/axiom) to support verifiable computational mathematics for AI agents.
