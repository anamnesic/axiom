# GEMINI.md — Chronokairo AXIOM Guidelines for Google Gemini & Antigravity

Welcome to **Chronokairo AXIOM** — verifiable computational mathematics infrastructure for AI agents, inspired by [morluto/rea](https://github.com/morluto/rea).

> **Core Directive for Gemini:** Never trust a bare mathematical claim when AXIOM can verify it independently. Always inspect `guarantee`, `epistemic_state`, and `verification.passed` on every `MathResult`. Enforce fail-closed reporting at all times.

---

## 1. Quick Reference & Commands

### 1.1 Running Tests
```bash
# Full test suite (101 tests across 6 suites)
python -m pytest tests/

# Key regression suites
python -m pytest tests/test_epistemic_states.py   # Epistemic states & integer precision (> 2^53)
python -m pytest tests/test_tamper_detection.py   # Tamper detection and payload revalidation
python -m pytest tests/test_adversarial.py       # Zero-mock adversarial stress tests

# Millennium Research Bench (111 criteria, 40 negative controls)
python -m benchmarks.millennium.run_millennium_bench
```

### 1.2 Lean 4 Formal Proof Audit
```bash
# Verify arithmetic corpus in Lean 4
lean research/arithmetic/dia_04_bezout.lean
lean research/arithmetic/dia_05_euclid_lemma.lean
lean research/arithmetic/dia_06_fundamental_theorem_existence.lean
lean research/arithmetic/dia_07_fundamental_theorem_uniqueness.lean
lean research/arithmetic/dia_08_euclid_infinitude.lean
lean research/arithmetic/dia_09_diophantine.lean
lean research/arithmetic/dia_10_congruences.lean

# Verify via Python API
python -c "from axiom import Axiom; res = Axiom().verify_lean_file('research/arithmetic/dia_10_congruences.lean'); print(res.epistemic_state, res.verified)"
```

### 1.3 Deterministic CLI Quick Reference
```bash
axiom solve "x^2 - 5*x + 6 = 0"
axiom simplify "sin(x)^2 + cos(x)^2"
axiom integrate "sin(x)^2" --variable x
axiom differentiate "x^3 * exp(x)" --variable x
axiom limit "sin(x)/x" --variable x --to 0
axiom evaluate "pi" --precision 50
axiom compare "(x + 1)^2" "x^2 + 2*x + 1"
axiom verify "x^2 - 5*x + 6 = 0" --solutions 2,3
axiom number-theory factorint -n 360
axiom number-theory nextprime -n 10
axiom number-theory divisors -n 12
axiom number-theory primefactors -n 360
```

---

## 2. Model Context Protocol (MCP) Integration

AXIOM exposes 21 standardized mathematical tools over MCP stdio:
```bash
axiom mcp
# or: python -m axiom.mcp_server
```

### Gemini Code Assist / Antigravity MCP Settings:
```json
{
  "mcpServers": {
    "axiom": {
      "command": "python",
      "args": ["-m", "axiom.mcp_server"]
    }
  }
}
```

---

## 3. Mathematical Epistemic Principles

### 3.1 Guarantee Hierarchy
| Guarantee | Level | Description |
| :--- | :---: | :--- |
| `formal-proof` | 5 | Lean 4 kernel-checked proof (0 `sorry`, trusted axioms only) |
| `exact-symbolic` | 4 | Proven algebraic identity (canonical zero + spot-checks) |
| `verified-substitution` | 3 | Exact root back-substitution verified |
| `numerical-approximation`| 2 | Numerically verified within declared `max_error` |
| `heuristic` | 1 | Plausible result; verification was inconclusive |
| `unverified` | 0 | Raw or refuted; never present as verified |

### 3.2 Epistemic States
- **`EpistemicState.PROOF`**: Machine-checked or analytically proven identity.
- **`EpistemicState.APPROXIMATION`**: Rigorous numerical approximation with explicit error bounds.
- **`EpistemicState.REFUTATION`**: Strictly requires explicit falsity evidence (counterexample/witness).
- **`EpistemicState.INCONCLUSIVE`**: Default fail-closed state when an identity cannot be resolved.

### 3.3 Strict Invariants for Gemini Agents
1. **Never Round Large Integers:** For integers above $2^{53}$, IEEE-754 binary floats collapse distinct values ($2^{53} == 2^{53} + 1$). Always compare integers exactly or via `Decimal`.
2. **Refutation Requires Witnesses:** Never classify a result as `REFUTATION` merely because a test failed or returned `"refuted"` text. A counterexample or violating substitution is mandatory.
3. **Sandbox Compliance:** MCP file operations are restricted to `Path.cwd()` and `<temp>/axiom`. Respect least privilege.
4. **No Mocking:** All mathematical tests must execute against real engines without mocking in the verification path.

---

## 4. Skills & ADR Governance

- Standard Agent Skills reside in [`skills/`](skills/) (17 standardized skills across foundational, formal, research, computational, verification, and scientific categories).
- Before designing new capabilities, check existing Architecture Decision Records in [`docs/adr/`](docs/adr/).

---

## 5. Issues & Community Support

* **Found a Bug or Soundness Issue?** Open an issue on GitHub: [https://github.com/chronokairo/axiom/issues](https://github.com/chronokairo/axiom/issues) with reproduction commands, system details, and mathematical context.
* **Support AXIOM:** Star the repository on GitHub: [https://github.com/chronokairo/axiom](https://github.com/chronokairo/axiom) to support verifiable mathematics for AI agents.
