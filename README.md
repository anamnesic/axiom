# AXIOM

**Mathematical Reasoning Engine**

*One MCP for mathematical computation, exploration, and verification.*

**English** · [简体中文](docs/readme/README_zh.md) · [繁體中文](docs/readme/README_zh-TW.md) · [日本語](docs/readme/README_ja.md) · [한국어](docs/readme/README_ko.md) · [Türkçe](docs/readme/README_tr.md) · [Русский](docs/readme/README_ru.md) · [Tiếng Việt](docs/readme/README_vi.md) · [ไทย](docs/readme/README_th.md) · [Deutsch](docs/readme/README_de.md) · [Español](docs/readme/README_es.md) · [Français](docs/readme/README_fr.md) · [Português (Brasil)](docs/readme/README_pt-BR.md) · [العربية](docs/readme/README_ar.md) · [فارسی](docs/readme/README_fa.md) · [Italiano](docs/readme/README_it.md) · [Ελληνικά](docs/readme/README_el.md)

AXIOM is a computational mathematics infrastructure for AI agents, researchers, students, and developers. It connects any MCP client to specialized mathematics engines — SymPy, SciPy, SageMath, Lean 4 — through a unified contract, with traceable results that are **independently verified**.

It is not an AI-powered calculator. It is not another Mathematica, SageMath, or Lean. It is the infrastructure that lets agents use all of them through a single interface.

> Inspired by the philosophy of [REA](https://github.com/morluto/rea): *reverse engineer anything* → **analyze mathematics**.

## Why AXIOM

An agent may claim it solved an equation. AXIOM **requires independent verification** before a result is trusted.

```
math solve "x^2 - 5*x + 6 = 0"
```

```text
┌─────────────────────────────────────────────────┐
│ Quadratic equation                             │
│   x² - 5x + 6 = 0                              │
│                                                 │
│ Solutions                                       │
│   x = 2  or  x = 3                              │
│                                                 │
│ Engine        SymPy                             │
│ Verification  Exact substitution (fractions)    │
│ Guarantee     VERIFIED-SUBSTITUTION             │
│ Result        Both roots satisfy the equation   │
└─────────────────────────────────────────────────┘
```

### Guarantee levels

Not every mathematical result carries the same logical strength. AXIOM explicitly distinguishes each level:

| Level | Meaning |
| --- | --- |
| `exact-symbolic` | Verified symbolic identity (e.g., canonical simplification) |
| `verified-substitution` | Solution validated by substitution with exact arithmetic |
| `numerical-approximation` | Numerical approximation with a declared error |
| `formal-proof` | Proof verified by a proof kernel (Lean 4) |
| `heuristic` | Likely result, not fully verified |
| `unverified` | Raw computation, not yet verified |

Every result carries evidence metadata: `engine`, `engine_version`, `steps`, `limitations`, and `reproducible_with`.

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
│  Codex · Claude Code · Gemini CLI · other MCP clients    │
└────────────────────────┬─────────────────────────────────┘
                         │  MCP / CLI
┌────────────────────────▼─────────────────────────────────┐
│  AXIOM Core                                              │
│  Parser · Dispatcher · Engine Registry · Evidence ·      │
│  Verification                                            │
└──┬──────────┬──────────┬──────────┬───────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
 Symbolic   Numerical   Formal     Visualization
 SymPy      SciPy       Lean 4     Plotly · Manim
 SageMath   Julia       Mathlib
```

The same contract holds regardless of which software performs the computation: swapping engines changes neither the result format nor the guarantee level.

## Modules

| Module | Capabilities |
| --- | --- |
| `arithmetic` | Exact arithmetic, fractions, arbitrary precision |
| `algebra` | Equations, polynomials, factoring, simplification |
| `calculus` | Limits, derivatives, integrals, series |
| `linear-algebra` | Matrices, eigenvalues, decompositions |
| `geometry` | Euclidean, analytic, and differential geometry |
| `number-theory` | Primes, congruences, Diophantine equations |
| `discrete` | Combinatorics, graphs, logic |
| `statistics` | Probability, distributions, inference |
| `optimization` | Linear, nonlinear, and convex optimization |
| `differential-equations` | ODEs, PDEs, and dynamical systems |
| `numerical` | Numerical methods, approximations, and errors |
| `symbolic` | General symbolic manipulation |
| `proof` | Proofs, counterexamples, and formal verification |
| `visualization` | 2D/3D plots, animations, and vector fields |
| `research` | Conjecture exploration, hypotheses, and experiments |

## MCP tools

Small, composable tools:

```
math_parse        math_simplify     math_solve
math_differentiate   math_integrate  math_limit
math_evaluate      math_plot         math_prove
math_verify        math_explain      math_compare
math_explore
```

Proposed CLI:

```bash
math solve "x^2 - 5*x + 6 = 0"
math integrate "sin(x)^2" --variable x
math plot "sin(x)/x" --range -10:10
math prove theorem.lean --engine lean
math verify solution.json
```

## Roadmap

- [ ] **v0.1 — Foundation**: CLI, MCP, expression parser, SymPy, equation solving, and evidence.
- [ ] **v0.2 — Numerical**: SciPy, matrices, numerical integration, optimization, and error evaluation.
- [ ] **v0.3 — Verification**: independent verifiers and optional Lean 4 integration.
- [ ] **v0.4 — Visualization**: interactive plots, geometry, and dynamical-system visualization.
- [ ] **v1.0 — Research**: automated tool composition, reproducible experiments, and assisted conjecture exploration.

We start with three engines: **SymPy** (symbolic), **SciPy** (numerical), and **Lean 4** (formal proofs).

## Repository layout

```
axiom/
├── README.md
├── LICENSE
├── AGENTS.md
├── Cargo.toml
├── crates/
│   ├── core/
│   ├── cli/
│   ├── mcp/
│   ├── evidence/
│   ├── verification/
│   └── engine-registry/
├── engines/
│   ├── sympy/
│   ├── sagemath/
│   ├── scipy/
│   ├── julia/
│   └── lean/
├── domains/
│   ├── algebra/
│   ├── calculus/
│   ├── geometry/
│   ├── discrete/
│   ├── number-theory/
│   ├── dynamical-systems/
│   └── optimization/
├── skills/
│   └── mathematics/
├── examples/
├── benchmarks/
├── tests/
└── docs/
```

## Name

**AXIOM** — *Mathematical Reasoning Engine*. Its own identity, aligned with formal mathematics and research.

## License

MIT

## Relationship with MathTools Offline

This repository was *MathTools Offline* (an offline desktop suite for LaTeX/SymPy/Lean). It was renamed to **AXIOM** and repositioned as computational mathematics infrastructure for agents. The engines (SymPy, Lean 4) are conceptually shared, but the focus is now the unified MCP contract and independent verification of results.
