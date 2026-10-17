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

Not every operation carries the same logical strength. AXIOM separates **mathematical correctness claims** (`guarantee.is_mathematical_claim == True`, which strictly require an executed `Verification(passed=True)` in `MathResult`) from **operational / structural states** (`is_mathematical_claim == False`):

| Level | Category | Meaning |
| --- | --- | --- |
| `formal-proof` | Mathematical Claim | Proof verified by the Lean 4 kernel (`#print axioms` confirmed, `sorry`/`admit` and trivial `X = X` tautologies rejected) |
| `exact-symbolic` | Mathematical Claim | Verified symbolic identity (canonical simplification, FTC antiderivative round-trip, symbolic L'Hôpital, with optional `assumptions`) |
| `verified-substitution` | Mathematical Claim | Solution validated by independent substitution ($f(r)=0$, $A A^{-1}=I$, $\nabla_\lambda g_{\mu\nu}=0$) with pole & domain-error rejection |
| `numerical-approximation` | Mathematical Claim | Arbitrary-precision evaluation, finite-difference check, adaptive quadrature, or two-sided sequence limit probe with declared `max_error` |
| `structural-parse` | Operational State | Safe AST parse validated by canonical re-parse equivalence (`ast-roundtrip`) |
| `catalog-lookup` | Operational State | Indexed declaration retrieved from the curated Mathlib 4 catalog or Loogle API |
| `sampled-visualization` | Operational State | Sampled 1D curve coordinates rendered to vector SVG and ASCII preview |
| `heuristic` | Operational State | Plausible pattern, exploratory summary, or open conjecture not yet verified |
| `unverified` | Operational State | Refuted claim, interior pole / jump discontinuity failure, or unverified computation |

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
| `algebra` | Equations, non-linear systems, polynomials, factoring, simplification, symbol `assumptions`, periodic solution families |
| `calculus` | Two-sided & directional limits, derivatives, definite/indefinite integrals with interior pole detection, Taylor series |
| `linear-algebra` | Matrices (`eigen`, `inv`, `det`, `lu`, `rref`, `solve`, `trace`) verified via $A A^{-1}=I$, $PA=LU$, $Av=\lambda v$ |
| `tensor` | Differential geometry: $g^{\mu\nu}$, Christoffel $\Gamma^\lambda_{\mu\nu}$, Riemann, Ricci, Einstein tensors verified via Levi-Civita $\nabla_\lambda g_{\mu\nu}=0$ |
| `number-theory` | Prime factorization (`factorint`), primality, Extended GCD (Bézout check), Chinese Remainder Theorem (`crt`), Euler totient, binomials |
| `differential-equations` | Symbolic ODE solver (`dsolve`) verified by back-substitution into the differential equation |
| `optimization` | Symbolic/numerical minimization & maximization verified via $f'(x^*)=0$ and neighborhood perturbations |
| `statistics` | Exact rational/symbolic mean, median, variance, stdev verified via König-Huygens identity $\sigma^2 = E[X^2] - \mu^2$ |
| `proof` | Lean 4 kernel checking (`#print axioms` + `X = X` tautology audit), symbolic-to-Lean auto-formalization, and Mathlib 4 theorem search |
| `visualization` | Zero-dependency vector SVG generation, terminal ASCII curve preview, and optional Matplotlib export (`sampled-visualization`) |
| `research` | Multi-step persistent sessions (`math_session`) with weakest-link `chain_guarantee` tracking and Markdown export |

## 21 Composable MCP Tools (by Category)

| Category | Count | Tools |
| --- | :---: | --- |
| **1. Mathematical Computation** (independently verified) | 12 | `math_simplify`, `math_solve`, `math_differentiate`, `math_integrate`, `math_limit`, `math_evaluate`, `math_matrix`, `math_ode`, `math_number_theory`, `math_optimize`, `math_statistics`, `math_tensor` |
| **2. Verification & Formal Proof** | 3 | `math_prove`, `math_verify`, `math_compare` |
| **3. Structural & Diagnostic** | 3 | `math_parse` (`structural-parse`), `math_explain`, `math_explore` (`heuristic`) |
| **4. Catalog Lookup** | 1 | `math_search_mathlib` (`catalog-lookup`) |
| **5. Visualization & Session** | 2 | `math_plot` (`sampled-visualization`), `math_session` (weakest-link `chain_guarantee`) |

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

- **[Architecture Decision Records (ADR Log)](docs/adr/README.md)** — Full history of architectural decisions (`ADR-0001` through `ADR-0011`).
- **[MCP Contracts Specification](docs/mcp-contracts.md)** — JSON-RPC 2.0 schemas, `MathResult` payload format, and guarantee rules.
- **[Competitive Landscape Analysis (2026)](docs/analise-concorrencia-mcp-2026.md)** — Comparison against `symkit-mcp` (`nsforge-mcp`), Official Wolfram MCP (`AgentTools`, Cloud MCP, and API MCP Service), `oOo0oOo/lean-lsp-mcp`, `Jsewill/math-mcp`, and `sympy-mcp`.
- **[Agent Instructions (`AGENTS.md`)](AGENTS.md)** & **[Mathematics Skill (`skills/mathematics/SKILL.md`)](skills/mathematics/SKILL.md)**.

## Scientific Research & Academic Foundation

AXIOM operates as a rigorous neuro-symbolic research harness designed for mathematical exploration, cross-checking computer algebra against interactive theorem provers, and enforcing fail-closed formal guarantees for AI reasoning agents.

- **[Research Proposal (`proposal.md`)](proposal.md)** — Delimits the central research question: *To what extent can an independent neuro-symbolic mediation layer eliminate algebraic/branch-cut hallucinations and enforce formal semantic soundness in AI agents?*
- **[Curriculum & Study Program (`curriculum.md`)](curriculum.md)** — Graduate-level study track across 7 foundational disciplines (Calculus, Linear Algebra, Real Analysis, Abstract Algebra, Differential Geometry, Analytic Number Theory, and Interactive Theorem Proving in Lean 4).
- **[Study Log & Demonstrations (`study-log.md`)](study-log.md)** — Daily research log recording formal demonstrations, counterexamples, and dual SymPy + Lean 4 cross-verifications.
- **[Related Work (`related-work.md`)](related-work.md)** — Systematic positioning against AlphaGeometry, Minerva, SymKit-MCP, Lean-LSP, and Wolfram Language.
- **[Methodology & Validation (`methodology.md`)](methodology.md)** — Mathematical guarantee hierarchy, invariant contracts, verification protocols, and empirical evaluation metrics.
- **[Benchmark EXP-0001 (`experiments/exp-0001/`)](experiments/exp-0001/REPORT.md)** — Empirical benchmark of domain integrity: AXIOM achieves **0.0% False Positive Rate** and **100% Fail-Closed Rate** on singular, complex, and adversarial cases vs. 46.2% false positives in naive CAS baselines.
- **[Theoretical & Implementation Limitations (`limitations.md`)](limitations.md)** — Explicit analysis of undecidability boundaries (Richardson's theorem, Gödel incompleteness, Matiyasevich DPRM) and operational boundaries.
- **[Field Reports & Millennium Problems (`reports/`)](reports/README.md)** — Dedicated research workspaces, autonomous validation suites (`validate.py`), and 100% fail-closed integrity audits across all seven Clay Millennium Prize Problems (Riemann Hypothesis, P vs NP, Navier-Stokes, Birch-Swinnerton-Dyer, Hodge, Yang-Mills, Poincaré).
- **[Citation Metadata (`CITATION.cff`)](CITATION.cff)** — Machine-readable academic citation schema.

## Roadmap

- [x] **v0.1.0 — Verified Foundation**: 21-tool MCP server, CLI, safe AST parser, hardened fail-closed verifiers, Lean 4 `#print axioms` audit + Lake environment support, and 6/6 cross-platform CI matrix (Python 3.10 & 3.12 on Ubuntu, Windows, macOS).
- [x] **v0.1.1 — Verification Integrity**: Strict separation between `exact-symbolic` identities (FTC antiderivative round-trip, symbolic L'Hôpital/series) and `numerical-approximation` evidence (finite differences, quadrature, sequence probes), plus mandatory non-empty theorem confirmation in `#print axioms`.
- [x] **v0.1.2 — Formal Integration**: Live Lean 4 + Lake formal verification job in GitHub Actions CI (`formal-lean`) validating constructive, classical, and invalid/spoofed proofs end-to-end.
- [x] **v0.2.0 — Mathematical Coverage**: Separation of mathematical correctness claims from operational states (`structural-parse`, `catalog-lookup`, `sampled-visualization`), domain `assumptions`, branch-cut counterexample generation ($\sqrt{x^2} \neq x$ over $\mathbb{R}$), definite integral interior pole rejection, two-sided limit discontinuity rejection, extraneous pole filtering & periodic solution sets (`solveset`), and Lean 4 `X = X` reflexive tautology detection (`37` `pytest` tests).
- [x] **v0.2.1 — Domain Integrity & Academic Research Foundation**: Pre-evaluation AST denominator tracking preventing silent domain loss ($\frac{x-1}{x-1} \neq 1$), complex Gaussian probes ($i, -i, 1+i$) invalidating unstated real branch-cuts ($\sqrt{x^2} \neq |x|$ over $\mathbb{C}$), explicit `assumptions` exposed across all MCP schemas and CLI commands (`-A`), periodic solution completeness flags, quantitative validation on Riemann Hypothesis (`reports/riemann-hypothesis/`), empirical benchmark `EXP-0001`, and formal research artifacts (`42` tests).
- [x] **v0.2.2 — Verification Soundness & Adversarial Hardening**: Ternary equivalence semantics (`proven`, `disproven`, `inconclusive`), adversarial polynomial refutation ($P(x) = (x+1)(x-2)(x-i)(x+i)(x-1-i)(x+2) == 0$ refuted via non-zero polynomial inspection and active counterexample search), relational assumption grammar (`x!=1`, `x>0`, `x<=0`), assumptions propagated to system solvers (`solve_system`) with nonlinear fallback, revised EXP-0001 benchmark (21 cases, 0% FPR vs 46.2% naive CAS), and hardened test suite (`45` tests).
- [ ] **v0.3.0 — Research Reliability**: Reproducible cross-engine benchmarks comparing AXIOM results against SageMath, SymPy, SciPy, and Julia.

## Repository Layout

```text
axiom/
├── README.md
├── LICENSE
├── CITATION.cff               # Academic citation metadata
├── AGENTS.md
├── curriculum.md              # Research study program & bibliography
├── study-log.md               # Daily research log & Lean 4 cross-checks
├── proposal.md                # Neuro-symbolic research proposal
├── related-work.md            # Literature review & scientific comparison
├── methodology.md             # Experimental methodology & invariants
├── limitations.md             # Theoretical & implementation limitations
├── pyproject.toml
├── src/
│   └── axiom/
│       ├── core.py            # Mathematical core & dispatcher
│       ├── contract.py        # MathResult, Evidence, Verification, Guarantee
│       ├── parsing.py         # Safe AST mathematical parser & relational assumptions
│       ├── verification.py    # Independent verifiers & ternary equivalence
│       ├── registry.py        # Multi-engine registry
│       ├── mcp_server.py      # 21-tool MCP JSON-RPC 2.0 stdio server
│       ├── cli.py             # CLI & Unicode box renderer
│       ├── session.py         # Reproducible research sessions
│       ├── setup_agent.py     # Agent auto-config (setup) & diagnostics (doctor)
│       └── engines/           # sympy, numeric (mpmath), lean, sagemath, julia
├── experiments/
│   └── exp-0001/              # Domain integrity & adversarial benchmark (run.py, results.json, REPORT.md)
├── reports/
│   ├── birch-and-swinnerton-dyer/ # Elliptic curves and L-functions queue
│   ├── hodge-conjecture/          # Algebraic cycles & cohomology queue
│   ├── navier-stokes/             # 3D fluid existence & smoothness
│   ├── p-vs-np/                   # Combinatorial verification audit
│   ├── poincare-conjecture/       # Solved 3-manifold geometrization study
│   ├── riemann-hypothesis/        # Critical line zero audits (RH)
│   └── yang-mills-mass-gap/       # Quantum gauge theory mass gap queue
├── skills/
│   └── mathematics/SKILL.md
├── examples/
│   └── theorems.lean
├── benchmarks/
│   └── run_benchmarks.py
├── tests/
│   ├── test_axiom.py          # 45 automated test_* methods
│   └── lean_project/          # Lake workspace for live Lean 4 formal CI tests
└── docs/
    ├── adr/                   # Architecture Decision Records (ADR-0001..0011)
    ├── mcp-contracts.md
    ├── analise-concorrencia-mcp-2026.md
    └── readme/                # 17 localized README translations
```


## License

MIT — **[Research Math for All Time by Chronokairo](https://chronokairo.com)**
