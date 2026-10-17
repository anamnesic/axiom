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

### Guarantee Levels (`Guarantee`)

AXIOM separates **mathematical correctness claims** (`guarantee.is_mathematical_claim == True`, which strictly require a non-null `Verification(passed=True)` or raise `ValueError`) from **operational / structural states** (`is_mathematical_claim == False`):

| Guarantee | Rank | `is_mathematical_claim` | Independent Verification / Operational Meaning |
| :--- | :---: | :---: | :--- |
| `formal-proof` | 5 | `True` | Checked by the Lean 4 typechecker kernel with zero `sorry`/`admit` holes, confirmed `#print axioms` output, and no trivial `X = X` reflexive tautologies |
| `exact-symbolic` | 4 | `True` | Symbolic normal-form reduction to `0` + multi-point rational/transcendental sampling (with optional symbol `assumptions`) |
| `verified-substitution` | 3 | `True` | Exact rational/symbolic substitution into original equation, ODE, or matrix/tensor identity (with pole and domain-violation rejection) |
| `numerical-approximation` | 2 | `True` | High-precision `mpmath` evaluation, finite-difference check, adaptive quadrature, or two-sided sequence probing with declared `max_error` |
| `structural-parse` | 1 | `False` | Safe AST parsing validated by canonical re-parse equivalence (`ast-roundtrip`) |
| `catalog-lookup` | 1 | `False` | Indexed declaration retrieved from the curated Mathlib 4 catalog or Loogle API |
| `sampled-visualization` | 1 | `False` | Sampled 1D curve coordinates rendered to zero-dependency vector SVG / ASCII preview |
| `heuristic` | 1 | `False` | Plausible pattern, exploratory report, or open conjecture where verification is inconclusive |
| `unverified` | 0 | `False` | Refuted claim, interior pole / discontinuity failure, or unverified computation |

---

## 2. Generated MCP Tool Catalog (21 Tools across 5 Categories)

| Category | Tool | Domain | Default Guarantee Tier | Description |
| :--- | :--- | :--- | :--- | :--- |
| **1. Mathematical Computation (12)** | `math_simplify` | Algebra | `exact-symbolic` | Simplify, factor, or expand an expression (with optional `assumptions`) and verify equivalence |
| | `math_solve` | Algebra | `verified-substitution` | Solve an equation or `;`-separated system, reject pole/domain errors, and report periodic families |
| | `math_differentiate` | Calculus | `exact-symbolic` / `numerical-approximation` | Differentiate symbolically and verify via FTC round-trip or high-precision finite differences |
| | `math_integrate` | Calculus | `exact-symbolic` / `numerical-approximation` | Compute indefinite or definite integrals, detect interior non-integrable poles, and verify via differentiation or quadrature |
| | `math_limit` | Calculus | `exact-symbolic` / `numerical-approximation` | Compute two-sided (`+-`) or directional (`+`, `-`) limits and verify left/right agreement |
| | `math_evaluate` | Arithmetic / Numeric | `exact-symbolic` / `numerical-approximation` | Evaluate an expression exactly or to arbitrary precision (`precision=50`) |
| | `math_matrix` | Linear Algebra | `verified-substitution` | Compute `eigen`, `det`, `trace`, `inv`, `rref`, `lu`, or `solve` ($Ax=b$) with algebraic identity verification |
| | `math_ode` | Differential Equations | `verified-substitution` | Solve an ODE (`dsolve`) and verify by substituting $y(x)$ back into the differential equation |
| | `math_number_theory` | Number Theory | `verified-substitution` / `exact-symbolic` | Execute verified `factorint`, `isprime`, `extgcd` (Bézout), `crt`, `totient`, `binomial` |
| | `math_optimize` | Optimization | `verified-substitution` / `numerical-approximation` | Find minima/maxima and verify via $f'(x^*)=0$ and neighborhood perturbations |
| | `math_statistics` | Statistics | `exact-symbolic` | Compute exact rational/symbolic moments and verify $\sum(x_i-\mu)=0$ and $\sigma^2=E[X^2]-\mu^2$ |
| | `math_tensor` | Differential Geometry | `verified-substitution` | Compute $g^{\mu\nu}$, Christoffel $\Gamma^\lambda_{\mu\nu}$, Riemann, Ricci, Einstein, and Kretschmann, verified via $\nabla_\lambda g_{\mu\nu}=0$ |
| **2. Verification & Proof (3)** | `math_prove` | Formal Proof | `formal-proof` / `exact-symbolic` | Verify a Lean 4 theorem/proof (`engine="lean"`) or symbolic identity (`engine="sympy"`) |
| | `math_verify` | Verification | `verified-substitution` / `exact-symbolic` | Independently verify candidate roots, an equality `lhs = rhs` (with `assumptions`), or a `MathResult` JSON |
| | `math_compare` | Equivalence | `exact-symbolic` / `unverified` | Test whether two expressions are equivalent (with `assumptions`) or find a concrete counterexample |
| **3. Structural & Diagnostic (3)** | `math_parse` | Core | `structural-parse` | Parse an expression or equation into a canonical AST, free variables, and LaTeX (`ast-roundtrip` verified) |
| | `math_explain` | Explanation | `exact-symbolic` / `verified-substitution` | Produce a traceable step-by-step derivation with verification metadata |
| | `math_explore` | Research | `heuristic` | Explore zeros, derivatives, critical points, parity, Taylor series, and sample table |
| **4. Catalog Lookup (1)** | `math_search_mathlib` | Formal Catalog | `catalog-lookup` | Search Mathlib 4 theorems by name, concept, or type signature (offline catalog + Loogle API) |
| **5. Visualization & Session (2)** | `math_plot` | Visualization | `sampled-visualization` | Sample a 1D curve on `[min, max]` and render vector SVG + ASCII preview |
| | `math_session` | Research Session | Weakest-link `chain_guarantee` | Record, inspect, or export multi-step mathematical research sessions |

