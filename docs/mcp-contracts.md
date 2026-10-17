# AXIOM MCP Contracts & Tool Catalog

Every tool exposed by the AXIOM MCP server (`python -m axiom.mcp_server` or `axiom mcp`) returns a structured `MathResult` conforming to a single unified contract.

---

## 1. Unified Result Schema (`MathResult`)

```json
{
  "kind": "solve",
  "input": "x^2 - 5*x + 6 = 0",
  "ok": true,
  "value": ["2", "3"],
  "value_str": "['2', '3']",
  "latex": "2, 3",
  "variables": ["x"],
  "guarantee": "verified-substitution",
  "evidence": {
    "engine": "sympy",
    "engine_version": "1.14.0",
    "method": "algebraic solve (sympy.solve)",
    "steps": [
      "solve Eq(x**2 - 5*x + 6, 0) for x",
      "solutions: [2, 3]"
    ],
    "reproducible_with": "axiom solve \"x^2 - 5*x + 6 = 0\""
  },
  "verification": {
    "kind": "exact-substitution",
    "passed": true,
    "detail": "Both roots satisfy the equation by exact substitution",
    "checks": 2,
    "max_error": 0.0
  }
}
```

### Guarantee Levels

| Guarantee | Rank | Independent Verification Mechanism |
| :--- | :---: | :--- |
| `formal-proof` | 5 | Checked by the Lean 4 typechecker kernel with zero `sorry`/`admit` holes |
| `exact-symbolic` | 4 | Symbolic normal-form reduction to `0` + multi-point transcendental sampling |
| `verified-substitution` | 3 | Exact rational/symbolic substitution into original equation, ODE, or matrix identity |
| `numerical-approximation` | 2 | High-precision `mpmath` evaluation or adaptive quadrature with declared `max_error` |
| `heuristic` | 1 | Plausible result where independent verification is inconclusive |
| `unverified` | 0 | Refuted claim or unverified computation |

---

## 2. Generated MCP Tool Catalog (18 Tools)

| Tool | Domain | Description |
| :--- | :--- | :--- |
| `math_parse` | Core | Parse an expression or equation into a canonical AST, free variables, and LaTeX |
| `math_simplify` | Algebra | Simplify, factor, or expand an expression and verify symbolic equivalence |
| `math_solve` | Algebra | Solve an equation or `;`-separated system and verify roots by exact substitution |
| `math_differentiate` | Calculus | Differentiate symbolically and verify against high-precision finite differences |
| `math_integrate` | Calculus | Compute indefinite or definite integrals and verify by differentiating or quadrature |
| `math_limit` | Calculus | Compute limits and verify via sequence convergence probing |
| `math_evaluate` | Arithmetic / Numeric | Evaluate an expression exactly or to arbitrary precision (`precision=50`) |
| `math_matrix` | Linear Algebra | Compute `eigen`, `det`, `trace`, `inv`, `rref`, `lu`, or `solve` ($Ax=b$) with verification |
| `math_ode` | Differential Equations | Solve an ODE (`dsolve`) and verify by substituting $y(x)$ back into the ODE |
| `math_number_theory` | Number Theory & Discrete | Execute verified `factorint`, `isprime`, `extgcd` (Bézout), `crt`, `totient`, `binomial` |
| `math_optimize` | Optimization | Find minima/maxima and verify via $f'(x^*)=0$ and neighborhood perturbations |
| `math_statistics` | Statistics | Compute exact rational/symbolic moments and verify $\sum(x_i-\mu)=0$ and $\sigma^2=E[X^2]-\mu^2$ |
| `math_plot` | Visualization | Sample a 1D curve on `[min, max]` and optionally export a Matplotlib figure |
| `math_prove` | Formal Proof | Verify a Lean 4 theorem/proof (`engine="lean"`) or symbolic identity (`engine="sympy"`) |
| `math_verify` | Verification | Independently verify candidate roots, an equality `lhs = rhs`, or a `MathResult` JSON |
| `math_explain` | Explanation | Produce a traceable step-by-step derivation with verification metadata |
| `math_compare` | Equivalence | Test whether two expressions are equivalent or find a concrete counterexample |
| `math_explore` | Research | Explore zeros, derivatives, critical points, parity, Taylor series, and sample table |
