# AXIOM

**Mathematical Reasoning Engine**

*One MCP for mathematical computation, exploration, and verification.*

**[Research Math for All Time by Chronokairo](https://chronokairo.com)**

**English** · [简体中文](docs/readme/README_zh.md) · [繁體中文](docs/readme/README_zh-TW.md) · [日本語](docs/readme/README_ja.md) · [한국어](docs/readme/README_ko.md) · [Türkçe](docs/readme/README_tr.md) · [Русский](docs/readme/README_ru.md) · [Tiếng Việt](docs/readme/README_vi.md) · [ไทย](docs/readme/README_th.md) · [Deutsch](docs/readme/README_de.md) · [Español](docs/readme/README_es.md) · [Français](docs/readme/README_fr.md) · [Português (Brasil)](docs/readme/README_pt-BR.md) · [العربية](docs/readme/README_ar.md) · [فارسی](docs/readme/README_fa.md) · [Italiano](docs/readme/README_it.md) · [Ελληνικά](docs/readme/README_el.md)

AXIOM is a computational mathematics infrastructure for AI agents, researchers, students, and developers. It connects any MCP client to specialized mathematics engines — **SymPy**, **mpmath / SciPy**, **SageMath**, **Julia**, and **Lean 4 / Mathlib 4** — through a unified contract, with traceable results that are **independently verified**.

It is not an AI-powered calculator. It is not another Mathematica, SageMath, or Lean. It is the infrastructure that lets agents use all of them through a single interface.

> Inspired by the philosophy of [REA](https://github.com/morluto/rea): *reverse engineer anything* → **analyze mathematics**.

## Why AXIOM

An agent may claim it solved an equation. AXIOM **requires independent verification** before a result is trusted.

```bash
axiom solve "x^2 - 5*x + 6 = 0"
```

```text
┌─ AXIOM · solve ──────────────────────────────────────────────────────┐
│ Input         x^2 - 5*x + 6 = 0                                      │
│ Result        [2, 3]                                                 │
│ LaTeX         2, 3                                                   │
│ Guarantee     [VERIFIED] VERIFIED-SUBSTITUTION                       │
│ Engine        sympy 1.14.0 (symbolic algebraic solver (sympy.solve)) │
│ Verification  exact-substitution: PASSED — All 2 solution(s)         │
│               verified by exact symbolic substitution (max residual  │
│               0.00e+00)                                              │
│ Reproduce     axiom solve "x^2 - 5*x + 6 = 0" --variable x           │
└──────────────────────────────────────────────────────────────────────┘
```

### Guarantee levels

Not every mathematical result carries the same logical strength. AXIOM explicitly distinguishes 6 hierarchical levels:

| Level | Meaning |
| --- | --- |
| `formal-proof` | Proof verified by a formal proof kernel (Lean 4, with `sorry`/`admit` strictly rejected) |
| `exact-symbolic` | Verified symbolic identity (e.g., canonical simplification, antiderivative differentiation) |
| `verified-substitution` | Solution validated by independent substitution ($f(r)=0$, $A A^{-1}=I$, $\nabla_\lambda g_{\mu\nu}=0$) |
| `numerical-approximation` | Arbitrary-precision numerical computation with declared error tolerance |
| `heuristic` | Plausible pattern or open conjecture, not yet verified |
| `unverified` | Raw or refuted computation |

Every result carries structured `Evidence` metadata: `engine`, `engine_version`, `method`, `steps`, `limitations`, and `reproducible_with`.

## Philosophy (inherited from REA)

| REA | AXIOM |
| --- | --- |
| Reverse engineer anything | Analyze mathematics |
| Binary analysis | Expression and structure analysis |
| Ghidra / Hopper / IDA | SymPy / SageMath / Julia / Lean 4 |
| Code tracing | Solution tracing |
| Reverse-engineering evidence | Mathematical evidence |
| Decompilation | Simplification and algebraic decomposition |
| Function inspection | Function analysis |
| Behavior comparison | Equivalence verification |
| MCP for agents | MCP for mathematical agents |
| CLI | Mathematical CLI |

## Architecture

```text
┌──────────────────────────────────────────────────────────┐
│  AI Agents                                               │
│  Codex · Claude Code · Cursor · Gemini CLI · MCP clients │
└────────────────────────┬─────────────────────────────────┘
                         │  MCP (21 tools) / CLI
┌────────────────────────▼─────────────────────────────────┐
│  AXIOM Core                                              │
│  Safe AST Parser · Dispatcher · Engine Registry ·        │
│  Evidence · Independent Verification · Research Sessions │
└──┬──────────┬──────────┬──────────┬───────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
 Symbolic   Numerical   Formal     Visualization
 SymPy      mpmath      Lean 4     Native Vector SVG
 SageMath   Julia       Mathlib4   ASCII Preview · Matplotlib
```

The same contract holds regardless of which software performs the computation: swapping engines changes neither the result format nor the guarantee level.

## Quick Start

```bash
pip install -e .

# Run environment & verification diagnostics
axiom doctor

# Auto-configure Claude Code, Cursor, Gemini CLI, and Codex
axiom setup --apply

# Start the MCP stdio server
axiom mcp
```

## Domains & Capabilities

| Module | Capabilities & Independent Verification |
| --- | --- |
| `arithmetic` | Exact rationals, arbitrary-precision `mpmath` evaluation |
| `algebra` | Equations, non-linear systems, polynomials, factoring, simplification |
| `calculus` | Limits (Gruntz + sequence probes), derivatives, definite/indefinite integrals, Taylor series |
| `linear-algebra` | Matrices (`eigen`, `inv`, `det`, `lu`, `rref`, `solve`, `trace`) verified via $A A^{-1}=I$, $PA=LU$, $Av=\lambda v$ |
| `tensor` | Differential geometry: $g^{\mu\nu}$, Christoffel $\Gamma^\lambda_{\mu\nu}$, Riemann, Ricci, Einstein tensors verified via Levi-Civita $\nabla_\lambda g_{\mu\nu}=0$ |
| `number-theory` | Prime factorization (`factorint`), primality, Extended GCD (Bézout check), Chinese Remainder Theorem (`crt`), Euler totient, binomials |
| `differential-equations` | Symbolic ODE solver (`dsolve`) verified by back-substitution into the differential equation |
| `optimization` | Symbolic/numerical minimization & maximization verified via $f'(x^*)=0$ and neighborhood perturbations |
| `statistics` | Exact rational/symbolic mean, median, variance, stdev verified via König-Huygens identity $\sigma^2 = E[X^2] - \mu^2$ |
| `proof` | Lean 4 kernel checking, symbolic-to-Lean auto-formalization, and Mathlib 4 theorem search (`math_search_mathlib`) |
| `visualization` | Zero-dependency vector SVG generation, terminal ASCII curve preview, and optional Matplotlib export |
| `research` | Multi-step persistent sessions (`math_session`) with weakest-link `chain_guarantee` tracking and Markdown export |

## 21 Composable MCP Tools

```text
math_parse            math_simplify         math_solve
math_differentiate    math_integrate        math_limit
math_evaluate         math_plot             math_prove
math_verify           math_explain          math_compare
math_explore          math_matrix           math_ode
math_number_theory    math_optimize         math_statistics
math_tensor           math_search_mathlib   math_session
```

### CLI Examples

```bash
axiom solve "x^2 - 5*x + 6 = 0"
axiom integrate "sin(x)^2" --variable x
axiom matrix "[[4, 1], [2, 3]]" --op eigen
axiom ode "diff(y(x), x) + 2*y(x) = exp(x)"
axiom number-theory crt --remainders 2,3,2 --moduli 3,5,7
axiom tensor sphere
axiom search-mathlib "binomial square"
axiom plot "sin(x)/x" --range -10:10 --output sinc.svg
axiom prove examples/theorems.lean --engine lean
axiom verify solution.json
```

## Documentation & ADR Log

- **[Architecture Decision Records (ADR Log)](docs/adr/README.md)** — Full history of architectural decisions (`ADR-0001` through `ADR-0007`).
- **[MCP Contracts Specification](docs/mcp-contracts.md)** — JSON-RPC 2.0 schemas, `MathResult` payload format, and guarantee rules.
- **[Competitive Landscape Analysis (2026)](docs/analise-concorrencia-mcp-2026.md)** — Comparison against `sympy-mcp`, `fermat-mcp`, `Wolfram-MCP`, and `lean-lsp-mcp`.
- **[Agent Instructions (`AGENTS.md`)](AGENTS.md)** & **[Mathematics Skill (`skills/mathematics/SKILL.md`)](skills/mathematics/SKILL.md)**.

## Roadmap

- [x] **v0.1.0 — Verified Foundation**: 21-tool MCP server, CLI, safe AST parser, hardened independent verifiers (never elevating guarantees without evidence), Lean 4 `#print axioms` audit + Lake environment support, and 6/6 cross-platform CI matrix (Python 3.10 & 3.12 on Ubuntu, Windows, macOS).
- [ ] **v0.2 — Numerical & Scientific Scale**: Deep SciPy / Julia solvers, PDE stencils, large-scale numerical linear algebra, and certified interval arithmetic (`mpmath.iv`).
- [ ] **v0.3 — Interactive Formal Verification**: Persistent Lean 4 Lake/Mathlib workspace, automated tactic synthesis loop, and step-by-step goal inspection.
- [ ] **v0.4 — Interactive Visualization**: 2D/3D Plotly & Manim scene generation, vector fields, and phase-portrait rendering.
- [ ] **v1.0 — Autonomous Mathematical Research**: Multi-agent conjecture discovery, counterexample search, and automated theorem formalization pipelines.

## Repository Layout

```text
axiom/
├── README.md
├── LICENSE
├── AGENTS.md
├── pyproject.toml
├── src/
│   └── axiom/
│       ├── core.py            # Mathematical core & dispatcher
│       ├── contract.py        # MathResult, Evidence, Verification, Guarantee
│       ├── parsing.py         # Safe AST mathematical parser
│       ├── verification.py    # Independent verifiers for all domains
│       ├── registry.py        # Multi-engine registry
│       ├── mcp_server.py      # 21-tool MCP JSON-RPC 2.0 stdio server
│       ├── cli.py             # CLI & Unicode box renderer
│       ├── session.py         # Reproducible research sessions
│       ├── setup_agent.py     # Agent auto-config (setup) & diagnostics (doctor)
│       └── engines/           # sympy, numeric (mpmath), lean, sagemath, julia
├── skills/
│   └── mathematics/SKILL.md
├── examples/
│   └── theorems.lean
├── benchmarks/
│   └── run_benchmarks.py
├── tests/
│   └── test_axiom.py
└── docs/
    ├── adr/                   # Architecture Decision Records (ADR-0001..0006)
    ├── mcp-contracts.md
    ├── analise-concorrencia-mcp-2026.md
    └── readme/                # 17 localized README translations
```

## License

MIT — **[Research Math for All Time by Chronokairo](https://chronokairo.com)**
