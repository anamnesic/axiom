# AGENTS.md — AXIOM Mathematical Reasoning Engine

AXIOM is a verifiable computational mathematics infrastructure for AI agents, inspired by [morluto/rea](https://github.com/morluto/rea).

> **Core rule for agents:** Never trust a bare mathematical claim when AXIOM can verify it independently. Always inspect `guarantee` and `verification.passed` on every `MathResult`.

---

## 1. Guarantee Hierarchy

Every AXIOM tool returns a `MathResult` with an explicit `guarantee` field ordered from strongest to weakest:

| Rank | Guarantee | Meaning |
| --- | --- | --- |
| 5 | `formal-proof` | Checked by the Lean 4 kernel with no `sorry` or `admit` holes |
| 4 | `exact-symbolic` | Verified symbolic identity (canonical reduction to `0` + numerical spot-checks) |
| 3 | `verified-substitution` | Candidate equation roots verified by exact rational/symbolic substitution |
| 2 | `numerical-approximation` | Verified numerically within a declared `max_error` tolerance |
| 1 | `heuristic` | Plausible output whose independent check was inconclusive |
| 0 | `unverified` | Raw or refuted computation — **do not present as verified** |

---

## 2. MCP Tools Reference

Start the MCP stdio server with:

```bash
axiom mcp
# or: python -m axiom.mcp_server
```

| Tool | Purpose |
| --- | --- |
| `math_parse` | Parse an expression or equation into a canonical AST, free variables, and LaTeX |
| `math_simplify` | Simplify, factor, or expand an expression and verify symbolic equivalence |
| `math_solve` | Solve an equation or `;`-separated system and verify roots by exact substitution |
| `math_differentiate` | Differentiate symbolically and verify against high-precision finite differences |
| `math_integrate` | Integrate (indefinite or definite) and verify by differentiating or quadrature |
| `math_limit` | Compute a limit and verify by numerical sequence probing |
| `math_evaluate` | Evaluate an expression exactly or to arbitrary precision (`precision=50`) |
| `math_plot` | Sample a 1D function over `[min, max]` and optionally render a plot |
| `math_prove` | Check a Lean 4 theorem/proof (`engine="lean"`) or symbolic identity (`engine="sympy"`) |
| `math_verify` | Independently verify candidate roots, an equality `lhs = rhs`, or a `MathResult` JSON |
| `math_explain` | Produce a traceable step-by-step derivation with verification metadata |
| `math_compare` | Test whether two expressions are equivalent or find a counterexample |
| `math_explore` | Analyze zeros, derivatives, critical points, parity, Taylor series, and samples |

---

## 3. CLI Quick Reference

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
axiom plot "sin(x)/x" --range -10:10
axiom prove theorem.lean --engine lean
```

Pass `--json` to any command for structured JSON output matching the MCP contract.
