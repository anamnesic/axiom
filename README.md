# AXIOM

**Mathematical Reasoning Engine**

*One MCP for mathematical investigation, computation, and verification.*

**[Research Math for All Time by Chronokairo](https://chronokairo.com)**

**English** · [简体中文](docs/readme/README_zh.md) · [繁體中文](docs/readme/README_zh-TW.md) · [日本語](docs/readme/README_ja.md) · [한국어](docs/readme/README_ko.md) · [Türkçe](docs/readme/README_tr.md) · [Русский](docs/readme/README_ru.md) · [Tiếng Việt](docs/readme/README_vi.md) · [ไทย](docs/readme/README_th.md) · [Deutsch](docs/readme/README_de.md) · [Español](docs/readme/README_es.md) · [Français](docs/readme/README_fr.md) · [Português (Brasil)](docs/readme/README_pt-BR.md) · [العربية](docs/readme/README_ar.md) · [فارسی](docs/readme/README_fa.md) · [Italiano](docs/readme/README_it.md) · [Ελληνικά](docs/readme/README_el.md)

AXIOM is a computational mathematics infrastructure for AI agents, researchers, students, and developers. It connects any Model Context Protocol (MCP) client to specialized mathematics engines — **SymPy**, **mpmath / SciPy**, **SageMath**, **Julia**, and **Lean 4 / Mathlib 4** — through a unified contract, where every result carries structured evidence and is **independently verified**.

It is not an AI-powered calculator. It is not another Mathematica, SageMath, or Lean. It is the neuro-symbolic infrastructure that lets reasoning agents interact with all of them through a single verified interface.

> Inspired by the philosophy of [REA](https://github.com/morluto/rea): *reverse engineer anything* → **investigate mathematics with agents**.

---

## Why AXIOM

When an AI agent claims it solved an equation, standard tools take its word for it. AXIOM **requires independent mathematical verification** before a claim is accepted.

```bash
axiom solve "x^2 - 5*x + 6 = 0"
```

```text
┌─ AXIOM · solve ───────────────────────────────────────────────────────────────────────┐
│ Solve            x^2 - 5*x + 6 = 0                                                    │
│ Result           ['2', '3']                                                           │
│ LaTeX            2, 3                                                                 │
│ Engine           sympy 1.14.0                                                         │
│ Method           algebraic solve (sympy.solve + domain & solveset completeness audit) │
│ Verification     exact-substitution: PASSED                                           │
│ Detail           Both roots satisfy the equation by exact substitution                │
│ Epistemic State  PROOF                                                                │
│ Guarantee        [VERIFIED] VERIFIED-SUBSTITUTION                                     │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

---

## The Four Epistemic States

AXIOM strictly categorizes all mathematical reasoning and computational output into **four mutually exclusive epistemic states** ([ADR-0017](docs/adr/0017-four-epistemic-states-and-soundness-governance.md)):

| Epistemic State | Underlying Guarantees | Epistemic Definition | Fail-Closed Verification Criteria |
| :--- | :--- | :--- | :--- |
| **Proof** | `formal-proof`, `exact-symbolic`, `verified-substitution` | Certified mathematical truth. An exact symbolic identity, machine-checked Lean 4 kernel derivation (`#print axioms`), or verified equation roots. | `Verification.passed == True`, exact symbolic residual $0$, no unverified axioms/hypotheses, congruent spec alignment. |
| **Approximation** | `numerical-approximation` | Quantitative evaluation or bounded sequence probing within specified tolerance $\epsilon$. Inexact float absorption is rejected. | Finite error $\le \epsilon$, `equivalent == False`, `approximately_equal == True`. Never granted `EXACT_SYMBOLIC`. |
| **Refutation** | `[REFUTED] DISPROVEN` | The proposition is decisively proven false via a concrete counterexample ($f(x^*) \neq 0$), contradiction, or non-zero residual. | Independent verification disproves the claim. `Verification.passed == False`, witness recorded in `detail`. |
| **Inconclusive** | `[UNVERIFIED] UNVERIFIED` | Truth value cannot be established within available symbolic algorithms, branch bounds, or execution timeouts. | Fail-closed state. `guarantee == Guarantee.UNVERIFIED`. Never promoted to proof. |

### Guarantee Hierarchy

Not every computation carries the same logical strength. AXIOM separates **mathematical correctness claims** (`is_mathematical_claim == True`, requiring an executed `Verification(passed=True)`) from **operational states** (`is_mathematical_claim == False`):

| Level | Category | Meaning |
| :--- | :--- | :--- |
| `formal-proof` | Mathematical Claim | Proof verified by the Lean 4 kernel (`#print axioms` confirmed, `sorry`/`admit` and trivial $X = X$ tautologies rejected) |
| `exact-symbolic` | Mathematical Claim | Verified symbolic identity (canonical simplification, FTC antiderivative round-trip, symbolic L'Hôpital, with optional `assumptions`) |
| `verified-substitution` | Mathematical Claim | Solution validated by independent substitution ($f(r)=0$, $A A^{-1}=I$, $\nabla_\lambda g_{\mu\nu}=0$) with pole & domain-error rejection |
| `numerical-approximation` | Mathematical Claim | Arbitrary-precision evaluation, finite-difference check, adaptive quadrature, or two-sided sequence limit probe with declared `max_error` |
| `structural-parse` | Operational State | Safe AST parse validated by canonical re-parse equivalence (`ast-roundtrip`) |
| `catalog-lookup` | Operational State | Indexed declaration retrieved from the curated Mathlib 4 catalog or Loogle API |
| `sampled-visualization` | Operational State | Sampled 1D curve coordinates rendered to vector SVG and ASCII preview |
| `heuristic` | Operational State | Plausible pattern, exploratory summary, or open conjecture not yet verified |
| `unverified` | Operational State | Refuted claim, interior pole / jump discontinuity failure, or inconclusive computation |

Every result carries structured `Evidence` metadata: `engine`, `engine_version`, `method`, `steps`, `limitations`, and `reproducible_with`.

---

## Architecture

```text
┌──────────────────────────────────────────────────────────┐
│  AI Agents                                               │
│  Antigravity · Codex · Claude Code · Cursor · Copilot    │
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

---

## Quick Start

```bash
# Clone and install locally
git clone https://github.com/chronokairo/axiom.git
cd axiom
pip install -e .

# Run environment & verification diagnostics
axiom doctor

# Auto-configure Antigravity, Claude Code, Cursor, Gemini CLI, and Codex
axiom setup --apply

# Start the MCP stdio server
axiom mcp
```

---

## The Four Epistemic States in Action (CLI & MCP)

### 1. Proof (Certified Mathematical Truth)

```bash
axiom solve "x^2 - 5*x + 6 = 0"
```
```text
┌─ AXIOM · solve ───────────────────────────────────────────────────────────────────────┐
│ Solve            x^2 - 5*x + 6 = 0                                                    │
│ Result           ['2', '3']                                                           │
│ LaTeX            2, 3                                                                 │
│ Engine           sympy 1.14.0                                                         │
│ Method           algebraic solve (sympy.solve + domain & solveset completeness audit) │
│ Verification     exact-substitution: PASSED                                           │
│ Detail           Both roots satisfy the equation by exact substitution                │
│ Epistemic State  PROOF                                                                │
│ Guarantee        [VERIFIED] VERIFIED-SUBSTITUTION                                     │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Approximation (Bounded Numerical Evidence)

```bash
axiom compare "pi" "3.141592653589793" --tolerance 1e-12
```
```text
┌─ AXIOM · compare ──────────────────────────────────────────────────────────────────────────────┐
│ Compare          pi == 3.141592653589793                                                                       │
│ Result           approximately equal within tolerance 1.0e-12 (max error: 2.33e-16, exact equality not proven) │
│ LaTeX            \pi \approx 3.141592653589793                                                                 │
│ Engine           sympy 1.14.0                                                                                  │
│ Method           symbolic difference reduction + domain & multi-point sampling                                 │
│ Verification     numerical-tolerance: PASSED                                                                   │
│ Detail           numerical-tolerance: PASSED (error <= 1e-12)                                                  │
│ Epistemic State  APPROXIMATION                                                                                 │
│ Guarantee        [APPROXIMATE] NUMERICAL-APPROXIMATION                                                         │
│ Invariant        equivalent=False, approximately_equal=True                                                    │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3. Refutation (Active Counterexample Discovery)

```bash
axiom compare "(x+1)*(x-2)*(x^2+1)*(x^2-2*x+2)" "0"
```
```text
┌─ AXIOM · compare ─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Compare          (x+1)*(x-2)*(x^2+1)*(x^2-2*x+2) == 0                                                             │
│ Result           not equivalent (counterexample: {'x': '-2'})                                                     │
│ LaTeX            \left(x - 2\right) \left(x + 1\right) \left(x^{2} + 1\right) \left(x^{2} - 2 x + 2\right) \neq 0 │
│ Engine           sympy 1.14.0                                                                                     │
│ Method           symbolic difference reduction + domain & multi-point sampling                                    │
│ Verification     counterexample-search: FAILED                                                                    │
│ Detail           counterexample found at {'x': '-2'} (|diff| = 2.000e+02)                                         │
│ Epistemic State  REFUTATION                                                                                       │
│ Guarantee        [REFUTED] DISPROVEN                                                                              │
│ Invariant        equivalent=False, approximately_equal=False                                                      │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4. Inconclusive (Fail-Closed Indecidability)

```bash
axiom integrate "exp(-x^3)" --variable x
```
```text
┌─ AXIOM · integrate ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Integrate        exp(-x^3)                                                                                                                     │
│ Result           gamma(1/3)*lowergamma(1/3, x**3)/(9*gamma(4/3))                                                                               │
│ LaTeX            \frac{\Gamma\left(\frac{1}{3}\right) \gamma\left(\frac{1}{3}, x^{3}\right)}{9 \Gamma\left(\frac{4}{3}\right)}                 │
│ Engine           sympy 1.14.0                                                                                                                  │
│ Method           symbolic indefinite integration (sympy.integrate)                                                                             │
│ Verification     differentiate-antiderivative: FAILED                                                                                          │
│ Detail           d/dx(gamma(1/3)*lowergamma(1/3, x**3)/(9*gamma(4/3))) = x**2*exp(-x**3)*gamma(1/3)/(3*(x**3)**(2/3)*gamma(4/3)) != exp(-x**3) │
│ Epistemic State  INCONCLUSIVE                                                                                                                  │
│ Guarantee        [UNVERIFIED] UNVERIFIED                                                                                                       │
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 21 Composable MCP Tools

| Category | Count | Tools |
| :--- | :---: | :--- |
| **1. Mathematical Computation** | 12 | `math_simplify`, `math_solve`, `math_differentiate`, `math_integrate`, `math_limit`, `math_evaluate`, `math_matrix`, `math_ode`, `math_number_theory`, `math_optimize`, `math_statistics`, `math_tensor` |
| **2. Verification & Formal Proof** | 3 | `math_prove`, `math_verify`, `math_compare` |
| **3. Structural & Diagnostic** | 3 | `math_parse`, `math_explain`, `math_explore` |
| **4. Catalog Lookup** | 1 | `math_search_mathlib` |
| **5. Visualization & Session** | 2 | `math_plot`, `math_session` |

---

## Scientific Research & Academic Foundation

AXIOM operates as a rigorous neuro-symbolic research harness. For theoretical justifications, statistical bounds, literature positioning, and formal arithmetic proofs, see:

- **[Scientific Research Whitepaper (`RESEARCH.md`)](RESEARCH.md)** — Core research document detailing:
  - Epistemological taxonomy and proof theory foundations;
  - Decidability bounds (Richardson's Theorem, Gödel Incompleteness, MRDP Theorem);
  - **Benchmark EXP-0001 ($n=21$ targeted adversarial cases)**: 0.0% False Positive Rate, 95% CI upper bound $\approx 14.3\%$ via Rule of Three (Clopper-Pearson: $[0.0\%, 13.1\%]$) vs 46.2% in naive CAS baseline (unwrapped SymPy 1.12);
  - **Millennium Boundary Probes ($n=111$ criteria, 40 negative controls)**: 95% CI upper bound $\le 7.5\%$;
  - **Boundary Stress-Test Disclaimer**: Clarifies that AXIOM makes **no claim** of solving open Millennium Prize Problems (Poincaré is verified as solved by Perelman; Navier-Stokes validates known Taylor-Green analytical solutions while refusing to certify unproven regularity);
  - **Versioned Arithmetic Corpus (`research/arithmetic/`)**: Machine-checked Lean 4 proofs (Bézout, Euclid's Lemma, Fundamental Theorem of Arithmetic Existence and Uniqueness, Euclid's Infinitude of Primes) based on Abramo Hefez.
- **[Research Proposal (`proposal.md`)](proposal.md)** & **[Experimental Methodology (`methodology.md`)](methodology.md)**.
- **[Curriculum Track (`curriculum.md`)](curriculum.md)** & **[Daily Research Log (`study-log.md`)](study-log.md)**.
- **[Academic Citation (`CITATION.cff`)](CITATION.cff)**.

---

## Roadmap

- [x] **v0.1.0 — Verified Foundation**: 21-tool MCP server, CLI, safe AST parser, fail-closed verifiers, Lean 4 `#print axioms` audit + Lake environment support, and 6/6 cross-platform CI matrix.
- [x] **v0.1.1 — Verification Integrity**: Separation between `exact-symbolic` identities and `numerical-approximation` evidence, plus non-empty theorem confirmation in `#print axioms`.
- [x] **v0.1.2 — Formal Integration**: Live Lean 4 + Lake formal verification in GitHub Actions CI (`formal-lean`).
- [x] **v0.2.0 — Mathematical Coverage**: Operational states separation, domain `assumptions`, branch-cut counterexample generation, interior pole rejection, and Lean 4 tautology detection (`37` tests).
- [x] **v0.2.1 — Domain Integrity**: Pre-evaluation AST denominator tracking ($\frac{x-1}{x-1} \neq 1$), complex Gaussian probes ($\sqrt{x^2} \neq |x|$ over $\mathbb{C}$), and benchmark `EXP-0001` (`42` tests).
- [x] **v0.2.2 — Adversarial Hardening**: Ternary equivalence semantics, adversarial polynomial refutation, relational assumption grammar, and system solvers (`45` tests).
- [x] **v0.2.3 — Scientific Benchmark Integrity**: Taylor-Green analytical kinetic energy $E(t) = \pi^2 e^{-4\nu t}$, evidence isolation, and boundary stress probes across all 7 Clay Millennium problems (`49` tests).
- [x] **v0.2.4 — Formal Specification Soundness**: Semantic alignment auditor, SymPy kernel validity gating, Navier-Stokes viscous dissipation $D(t) = 4\nu\pi^2 e^{-4\nu t}$ derived from velocity gradients, and Lean 4 forced variant model (`51` tests).
- [x] **v0.2.5 — Formal Statement Integrity**: Lean 4 binder and signature parsing, 4-state semantic alignment, and kinetic energy spatial integration derivation (`54` tests).
- [x] **v0.2.6 — Four Epistemic States & Adversarial Soundness**: 4-epistemic-state separation, Lean sandbox with resource bounds, authorized path restriction, and zero-mock adversarial test suite ([ADR-0017](docs/adr/0017-four-epistemic-states-and-soundness-governance.md), `63` tests).
- [x] **v0.2.7 — Evidence Integrity & Sandboxing**: Untrusted JSON session quarantine, sanitized process environment for Lean, and interface alignment ([ADR-0018](docs/adr/0018-evidence-integrity-sandboxing-and-interface-alignment.md), `73` tests).
- [x] **v0.2.8 — CI Recovery, Tamper-Resistant Revalidation & Versioned Arithmetic Corpus**: Recover 6-platform failing CI matrix; strict semantic value comparison for tamper detection across all operations; hypothesis downgrading on load; versioned Abramo Hefez Lean 4 arithmetic corpus in `research/arithmetic/` ([ADR-0026](docs/adr/0026-ci-recovery-tamper-detection-and-versioned-arithmetic-corpus.md), `84` automated tests).
- [ ] **v0.3.0 — The Mathematical Investigation Layer (Porting REA to Mathematics)**: Mathematical Investigation Dossiers (`.axiom/investigations/<id>/`), Proof Dependency Graphs (DAG), the **Unknown Ledger** (`list_unknowns`), Evidence Bundles with SHA-256 provenance hashes (`get_evidence_bundle`), 8 high-level investigation primitives, and reproducible cross-engine validation across Lean 4, SymPy, SageMath, and Julia ([ADR-0019](docs/adr/0019-mathematical-investigation-layer-rea-paradigm.md)).

---

## Repository Layout

```text
axiom/
├── README.md                  # Developer & user quickstart guide
├── RESEARCH.md                # Academic research whitepaper, bounds & methodology
├── TUTORIAL.md                # Comprehensive user tutorial & agent guide
├── TODO.md                    # Gap audit & roadmap tracking
├── LICENSE                    # MIT License
├── CITATION.cff               # Academic citation metadata
├── AGENTS.md                  # Multi-agent coordination & skills index
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
│       ├── contract.py        # MathResult, Evidence, Verification, EpistemicState, Guarantee
│       ├── parsing.py         # Safe AST mathematical parser & relational assumptions
│       ├── verification.py    # Independent verifiers & ternary equivalence
│       ├── registry.py        # Multi-engine registry
│       ├── mcp_server.py      # 21-tool MCP JSON-RPC 2.0 stdio server
│       ├── cli.py             # CLI & Unicode evidence box renderer
│       ├── session.py         # Reproducible research sessions
│       ├── setup_agent.py     # Agent auto-config (setup) & diagnostics (doctor)
│       └── engines/           # sympy, numeric (mpmath), lean, sagemath, julia
├── experiments/
│   └── exp-0001/              # Domain integrity & adversarial benchmark (n=21, results.json, REPORT.md)
├── reports/                   # Boundary stress tests & epistemic sanity probes across Clay problems
├── research/
│   ├── arithmetic/            # Versioned, Git-tracked Lean 4 arithmetic corpus (Days 04-07)
│   ├── conjectures/           # Working hypotheses & empirical claims
│   ├── lemmas/                # Proven lemmas & Lean 4 kernel-checked proofs
│   └── counterexamples/       # Systematically cataloged refutations
├── benchmarks/
│   ├── millennium/            # Consolidated Millennium Bench (111 criteria, 40 negative controls)
│   └── run_benchmarks.py      # Execution time benchmarks
├── skills/                    # Standardized GitHub Agent Skills
├── examples/                  # Verified Lean 4 example proofs
├── tests/
│   ├── test_axiom.py          # 56 automated unit tests
│   ├── test_adversarial.py    # 9 adversarial soundness & isolation tests
│   ├── test_use_cases.py      # 10 end-to-end workflow tests
│   ├── test_tamper_detection.py # 5 payload tamper detection & hypothesis integrity tests
│   ├── test_skills.py         # 4 agent skill specification tests
│   └── lean_project/          # Lake workspace for live Lean 4 formal CI tests
└── docs/
    ├── adr/                   # Architecture Decision Records (ADR-0001..0026)
    ├── use-cases.md           # 10 end-to-end CLI & MCP workflows
    ├── mcp-contracts.md       # JSON-RPC schemas & guarantee contracts
    ├── analise-concorrencia-mcp-2026.md # Competitive landscape analysis
    └── readme/                # 17 localized README translations
```

---

## License

MIT — **[Research Math for All Time by Chronokairo](https://chronokairo.com)**
