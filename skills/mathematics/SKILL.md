---
name: mathematics
description: Use the AXIOM Mathematical Reasoning Engine (MCP & CLI) to parse, simplify, solve, differentiate, integrate, evaluate, compare, explore, plot, and formally verify mathematical claims with independent verification and explicit guarantee levels.
---

# AXIOM — Mathematical Reasoning Skill

Use **AXIOM** whenever a task involves symbolic algebra, calculus, equation solving, numerical approximation, equivalence checking, or formal proof verification.

## Core Principles

1. **Never compute by mental arithmetic or unverified LLM generation** when an engine can compute and independently verify the result.
2. **Always check the `guarantee` level** on every `MathResult`:
   - `formal-proof` — Verified by the Lean 4 kernel without `sorry` or `admit`.
   - `exact-symbolic` — Verified symbolic identity + numerical spot-checks.
   - `verified-substitution` — Candidate roots substituted back into the original equation with exact arithmetic.
   - `numerical-approximation` — Numerical evaluation or quadrature with a declared `max_error`.
   - `heuristic` — Plausible result where independent verification is incomplete.
   - `unverified` — Failed verification or raw output; never present as proven.
3. **Preserve `evidence` and `reproducible_with`** when reporting results to the user.

## Composable MCP Tools

- `math_parse(expression)` — Parse into AST, detect free variables and structure.
- `math_simplify(expression, mode="simplify"|"factor"|"expand")` — Transform and verify equivalence.
- `math_solve(expression, variable=None, engine=None)` — Solve equations or `;`-separated systems and verify roots by substitution.
- `math_differentiate(expression, variable="x", order=1)` — Differentiate and verify against high-precision finite differences.
- `math_integrate(expression, variable="x", lower=None, upper=None)` — Integrate and verify by differentiating the antiderivative or comparing with quadrature.
- `math_limit(expression, variable="x", point="0", direction="+-")` — Compute limits and verify via sequence probing.
- `math_evaluate(expression, precision=None, substitutions=None)` — Exact or arbitrary-precision evaluation.
- `math_compare(left, right)` — Prove equivalence or find a concrete counterexample.
- `math_verify(target, candidate=None, variable=None)` — Independently verify roots, identities, or `MathResult` JSON payloads.
- `math_explain(expression, operation="solve")` — Step-by-step traceable derivation.
- `math_explore(expression, variable="x")` — Zeros, critical points, derivatives, parity, Taylor series, and sample table.
- `math_plot(expression, min=-10, max=10, points=101, output=None)` — Sample 1D curve and optionally save a plot.
- `math_prove(statement, proof="", engine="lean")` — Verify formal Lean 4 theorems.
