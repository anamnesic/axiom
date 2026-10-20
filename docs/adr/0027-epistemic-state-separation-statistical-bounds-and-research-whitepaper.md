# ADR-0027: Epistemic State Separation, Statistical Confidence Bounds, and Research Whitepaper Architecture

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** Chronokairo AXIOM Core Architecture & Verification Team
- **Context:** Post-Audit External Review (19/10/2026), Reviewer Feedback on Epistemic Clarity, Statistical Framing, and Repository Architecture

---

## 1. Context and Problem Statement

Following the successful remediation of CI matrix blockers and evidence integrity gaps in ADR-0026, an external peer review raised 6 critical points regarding scientific presentation and architectural clarity:

1. **Statistical Framing of Benchmark EXP-0001:** Stating "0% false positives" on $n = 21$ cases without reporting sample size, confidence intervals (via the Rule of Three), or defining the "naive CAS baseline" risks appearing overclaimed and vulnerable to selection bias.
2. **Millennium Prize Problems Positioning:** Phrasing such as "100% fail-closed integrity audits across all seven Clay problems" could be misread as mathematical progress toward solving the conjectures. The Poincaré Conjecture was solved by Grigori Perelman, and Navier-Stokes investigations reproduce known exact solutions (Taylor-Green) while auditing fail-closed boundaries.
3. **Test Count Consistency:** The roadmap cited 73 tests in v0.2.7 and 63 in v0.2.6, while the repository layout text showed $54 + 9 = 63$. The exact breakdown across all test suites needed formal synchronization.
4. **Refutation vs. Guarantee Level Disambiguation:** In the four epistemic states, refutations were displayed as `Guarantee: [REFUTED] UNVERIFIED`, creating confusion between decisive refutation (proof of falsehood $\neg P$) and fail-closed inconclusive states.
5. **README Cognitive Load & Language Mixture:** The README had grown excessively long and contained mixed-language headings (Portuguese parentheticals within English text).
6. **Reproducibility of Documentation Examples:** Output boxes in the README and use-cases needed to be verified against the exact, literal stdout of CLI execution.

---

## 2. Architectural Decisions

### 2.1 Explicit Two-Axis Classification: `EpistemicState` & `Guarantee`
- Defined `EpistemicState(str, Enum)` with 4 mutually exclusive states:
  - `PROOF`: Certified mathematical truth (`formal-proof`, `exact-symbolic`, `verified-substitution`).
  - `APPROXIMATION`: Bounded numerical evaluation within declared tolerance $\epsilon$ (`numerical-approximation`).
  - `REFUTATION`: Decisive mathematical disproof via concrete counterexample or contradiction (`[REFUTED] DISPROVEN`).
  - `INCONCLUSIVE`: Indecidable or unverified computation (`[UNVERIFIED] UNVERIFIED`).
- Added the `epistemic_state` property to `MathResult` and included it in JSON-RPC serialization (`to_dict()`).
- Updated `cli.py` (`render_box`) to explicitly display both axes:
  ```text
  │ Epistemic State  REFUTATION
  │ Guarantee        [REFUTED] DISPROVEN
  ```
  eliminating the ambiguous `[REFUTED] UNVERIFIED` output.

### 2.2 Rigorous Statistical Bounds & Baseline Definition (EXP-0001 & Millennium Bench)
- In `RESEARCH.md`, `experiments/exp-0001/REPORT.md`, and `benchmarks/millennium/README.md`:
  - Explicitly declared sample size $n = 21$ for EXP-0001 and $n = 111$ for Millennium Bench (with 40 negative controls).
  - Derived and reported 95% confidence intervals via the Rule of Three.
  - Clarified that EXP-0001 is a **targeted adversarial benchmark** focusing on singular points and branch cuts rather than a uniform random distribution.
  - Formally defined the **Naive CAS Baseline**.

> [!WARNING]
> **Amended by [ADR-0031](0031-exact-value-integrity-refutation-evidence-and-statistical-corrections.md) (20/10/2026).** The original version of this section stated the Clopper-Pearson upper bounds as $[0.00\%, 13.06\%]$ ($0/21$), $[0.00\%, 24.71\%]$ ($0/13$) and $[0.00\%, 7.22\%]$ ($0/40$), and described the baseline as "standard unwrapped SymPy 1.12". Both were defective:
>
> - **$13.06\%$ matched no Clopper-Pearson convention.** For $n = 21$ the two-sided 95% upper bound is $16.11\%$ and the one-sided 95% upper bound is $13.29\%$. The same document also mixed conventions across cases ($7.22\%$ is the *one-sided* bound for $n = 40$, while $24.71\%$ is the *two-sided* bound for $n = 13$).
> - **The false-positive denominator was $13$, not $21$.** A false positive is only defined over the mathematically invalid cases.
> - **The baseline was not "unwrapped SymPy".** `experiments/exp-0001/run.py` implements an *emulated* unguarded CAS that additionally applies a fixed 6-point sampling probe, and its `formal_proof` row is *simulated* (the Lean compiler is never invoked).
>
> The corrected, consistently two-sided values are: $0/13 \rightarrow [0.00\%, 24.71\%]$, $0/21 \rightarrow [0.00\%, 16.11\%]$, $0/40 \rightarrow [0.00\%, 8.81\%]$. The baseline provenance is now emitted machine-readably under `baseline` in `experiments/exp-0001/results.json`.

### 2.3 Clay Millennium Boundary Stress-Test Positioning
- Renamed problem directories and documentation from "Field Reports" to **"Boundary Stress Tests & Epistemic Sanity Probes"**.
- Added prominent disclaimers explicitly stating that AXIOM makes **no claim** of solving or advancing open Millennium Prize Problems.
- Explicitly documented that the Poincaré Conjecture is **solved by Grigori Perelman (2002–2003)** (AXIOM audits differential geometry invariants), and Navier-Stokes validates known analytical Taylor-Green decaying solutions while refusing to certify unproven regularity or finite-time blowup.

### 2.4 Separation of Concerns: `RESEARCH.md` & Developer-Centric `README.md`
- Extracted theoretical justifications, Gödel/Richardson/MRDP decidability limits, statistical bounds, literature positioning, and formal arithmetic corpus details into [`RESEARCH.md`](../RESEARCH.md).
- Streamlined [`README.md`](../README.md) to be developer- and agent-centric, focused on installation, quickstart, CLI and MCP commands, architecture, and tool tables, written in 100% clean English without mixed language.

### 2.5 Literal Execution Box Synchronization & Test Audit
- Synchronized all example boxes in `README.md` and `docs/use-cases.md` with the exact, literal terminal output generated by `axiom`.
- Synchronized test counts across all documentation and layout trees to reflect **84 automated tests** across 5 suites:
  - `tests/test_axiom.py`: 56 tests
  - `tests/test_adversarial.py`: 9 tests
  - `tests/test_use_cases.py`: 10 tests
  - `tests/test_tamper_detection.py`: 5 tests
  - `tests/test_skills.py`: 4 tests

---

## 3. Consequences and Validation

- **Epistemic Clarity:** Refutations are now clearly distinguished from inconclusive fallbacks in both CLI boxes and JSON outputs.
- **Academic Defensibility:** Statistical bounds (Rule of Three, Clopper-Pearson), baseline definitions, and adversarial selection criteria are fully qualified, withstanding strict peer review scrutiny.
- **Honest Positioning:** Millennium problem suites are transparently framed as fail-closed sanity probes and invariant regression audits.
- **Reproducibility:** 100% of documentation examples match the live CLI output verbatim.
- **Zero Regressions:** Complete test suite passes with 84/84 tests green in 156 seconds.

> [!NOTE]
> **Amended by [ADR-0031](0031-exact-value-integrity-refutation-evidence-and-statistical-corrections.md) (20/10/2026).** The test count above was accurate at the time of this ADR and is retained as a historical record. The suite now carries **100 tests across 6 suites** (the additional suite is `tests/test_epistemic_states.py`, dedicated to the four epistemic states and to exact-value integrity). The "Academic Defensibility" claim above is also qualified: the statistical bounds and baseline definition originally published here were defective and have been corrected by ADR-0031.
