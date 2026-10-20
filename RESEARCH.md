# AXIOM: Scientific Research & Academic Foundation

> **Independent Neuro-Symbolic Verification for Mathematical Exploration and AI Reasoning**  
> *Chronokairo Research Group · Version 0.2.8 (October 2026)*

---

## 1. Research Question & Academic Motivation

As large language models (LLMs) and autonomous agents are increasingly deployed in scientific research, computational mathematics faces a severe challenge: **semantic drift and algebraic hallucination**. General-purpose agents routinely:
- Cancel denominators across domain boundaries (e.g., treating $\frac{x-1}{x-1}$ as identically equal to $1$ over all $x \in \mathbb{C}$);
- Conflate multi-valued complex branch cuts (e.g., assuming $\sqrt{x^2} = x$ without specifying real, positive domains);
- Absorb numerical float approximations as exact proofs;
- Hallucinate mathematical proofs without machine-checked derivation.

The primary research question of the **Chronokairo AXIOM** project is:
> *To what extent can an independent, multi-engine neuro-symbolic mediation layer eliminate algebraic and branch-cut hallucinations, enforce fail-closed epistemic guarantees, and provide machine-checked provenance for automated mathematical reasoning?*

---

## 2. Epistemological Framework: The Four Epistemic States

AXIOM strictly partitions all computational and reasoning outputs into **four mutually exclusive, non-overlapping epistemic states** ([ADR-0017](docs/adr/0017-four-epistemic-states-and-soundness-governance.md)):

```text
                             Mathematical Claim / Probe
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
          [Decisive Truth]                              [Undecided / Bounded]
                 │                                               │
        ┌────────┴────────┐                             ┌────────┴────────┐
        ▼                 ▼                             ▼                 ▼
   1. PROOF         3. REFUTATION                2. APPROXIMATION   4. INCONCLUSIVE
  (Certified)      (Counterexample)                 (Bounded ε)       (Fail-Closed)
```

1. **Proof (`PROOF`)**:
   - **Guarantees:** `formal-proof`, `exact-symbolic`, `verified-substitution`.
   - **Definition:** The proposition is proven to hold identically within its declared mathematical domain.
   - **Invariants:** `Verification.passed == True`, exact symbolic residual identically $0$, no unverified hypotheses, kernel-checked Lean 4 derivation (`#print axioms` without `sorry` or trivial $X=X$ tautology).

2. **Approximation (`APPROXIMATION`)**:
   - **Guarantees:** `numerical-approximation`.
   - **Definition:** Quantitative evaluation or sequence probing bounded by an explicit numerical tolerance $\epsilon > 0$.
   - **Invariants:** Finite residual $\le \epsilon$, `approximately_equal == True`, `equivalent == False`. Inexact floating-point absorption is rejected from `EXACT_SYMBOLIC`.

3. **Refutation (`REFUTATION`)**:
   - **Guarantees:** `[REFUTED] DISPROVEN`.
   - **Definition:** The claim is decisively disproven by discovering an explicit counterexample ($f(x^*) \neq 0$), demonstrating a non-zero algebraic difference, or rejecting an invalid root.
   - **Invariants:** Decisive mathematical disproof. An explicit witness/counterexample is recorded in `Verification.detail`.

4. **Inconclusive (`INCONCLUSIVE`)**:
   - **Guarantees:** `[UNVERIFIED] UNVERIFIED`.
   - **Definition:** The truth value cannot be decisively established within available algorithms, branch bounds, or execution timeouts.
   - **Invariants:** Strict fail-closed fallback. An unverified claim is never promoted to proof.

---

## 3. Theoretical Boundaries & Decidability Limits

AXIOM's verification contracts are constructed upon the foundational limits of mathematical logic and computation theory ([limitations.md](limitations.md)):

1. **Richardson's Theorem (1968):**
   The identity problem ($E = 0$) for the class of elementary expressions comprising rational numbers, $\pi$, $\ln(2)$, addition, multiplication, composition, and the sine, exponential, and absolute value functions is **algorithmically undecidable**.
   *Implication for AXIOM:* AXIOM does not claim to decide arbitrary transcendental equivalence; whenever symbolic simplification fails to reduce an expression to zero, AXIOM falls back to multi-point complex Gaussian probing and reports `INCONCLUSIVE` rather than guessing.

2. **Gödel's Incompleteness Theorems (1931):**
   No consistent formal system capable of expressing arithmetic can prove all truths within its domain.
   *Implication for AXIOM:* Formal guarantees (`formal-proof`) are strictly kernel-relative (Lean 4 core calculus of inductive constructions). AXIOM audits `#print axioms` to ensure no ad-hoc axioms or unproven conjectures are introduced into the trusted kernel.

3. **Matiyasevich-Robinson-Davis-Putnam (MRDP) Theorem (1970):**
   Hilbert's 10th Problem is unsolvable: there is no general algorithm to determine whether an arbitrary Diophantine equation has integer solutions.
   *Implication for AXIOM:* Non-linear Diophantine solvers are restricted to solvable classes (linear via Extended Euclidean Algorithm, quadratic congruences, elliptic curves with bounded rank) and declare `INCONCLUSIVE` outside certified domains.

---

## 4. Empirical Benchmarks: Methodology & Statistical Bounds

### 4.1 Benchmark EXP-0001 (Domain Integrity & Adversarial CAS Probes)

The **EXP-0001** benchmark ([experiments/exp-0001/REPORT.md](experiments/exp-0001/REPORT.md)) evaluates how mathematical reasoning harnesses handle adversarial and singular inputs:

- **Sample Size:** $n = 21$ hand-crafted adversarial benchmark cases targeting known computer algebra failure modes:
  - 7 removable and essential singularities (e.g., $\frac{x-1}{x-1}$, $\frac{\sin(x)}{x}$ at $x=0$, $\frac{1}{x(x-1)}$);
  - 7 branch cuts and multi-valued complex functions (e.g., $\sqrt{x^2}$ over $\mathbb{C}$, $\ln(x^2) - 2\ln(x)$ for negative/complex arguments);
  - 7 constructed adversarial polynomials with non-trivial roots designed to defeat simple random evaluations.
- **Methodology & Selection Bias:** The benchmark cases were deliberately selected as **adversarial edge cases** rather than drawn from a uniform random distribution of textbook expressions. Standard CAS failures cluster sharply at boundary points; targeted stress-testing is standard practice in software security and formal methods.
- **Statistical Confidence Bounds (Rule of Three):**
  - Observed False Positive Rate (AXIOM): $0 / 21$ ($0.0\%$).
  - Under the standard statistical **Rule of Three** for zero observed events, the upper bound of the 95% confidence interval is:
    $$\text{Upper } 95\% \text{ CI} \approx \frac{3}{n} = \frac{3}{21} \approx 14.28\%$$
  - Exact binomial Clopper-Pearson 95% confidence interval: $[0.00\%, 13.06\%]$.
- **Baseline Definition:**
  - The comparison baseline (*"Naive CAS"*) is explicitly defined as **standard unwrapped SymPy 1.12** invoking `sp.simplify()` and `sp.evalf()` without pre-evaluation AST denominator analysis, complex Gaussian probe injection, or independent substitution verification.
  - Naive CAS exhibited a **46.2% false positive rate** on this adversarial set by silently simplifying singular expressions to 1 and dropping domain constraints.

### 4.2 Millennium Bench (Stress-Testing Boundary Probes)

The Millennium Bench ([benchmarks/millennium/](benchmarks/millennium/)) comprises **111 criteria**:
- 40 negative controls / adversarial refutation probes (e.g., false polynomial zeros, perturbed Riemann zeta zeros, unproven blowup claims);
- 28 numerical and analytical sanity checks;
- 43 exact invariant verifications.
- **Observed False Positive Rate on Negative Controls:** $0 / 40$ ($0.0\%$).
- **Rule of Three 95% Confidence Upper Bound:** $\frac{3}{40} = 7.5\%$.
- Exact binomial Clopper-Pearson 95% confidence interval: $[0.00\%, 7.22\%]$.

---

## 5. Clay Millennium Problems: Boundary Stress Tests & Epistemic Sanity Probes

> [!IMPORTANT]
> **Explicit Disclaimer:** Chronokairo AXIOM makes **NO claim** of having solved, advanced, or discovered novel mathematical proofs for any of the open Clay Millennium Prize Problems. The suites in [`reports/`](reports/README.md) are **boundary stress tests and epistemic sanity probes**, designed to verify that the verifier correctly refuses to certify unproven claims and accurately reproduces known analytical results.

1. **Poincaré Conjecture (Topology / Differential Geometry):**
   - *Status:* **Solved by Grigori Perelman (2002–2003)**; verified by the international mathematical community.
   - *AXIOM Probe:* Validates differential geometry invariants, Levi-Civita connection $\nabla_\lambda g_{\mu\nu} = 0$, Ricci tensor contractions, and Einstein tensors on known 3-manifolds. Does not attempt or claim a new proof.
2. **Navier-Stokes Existence and Smoothness (Fluid Mechanics):**
   - *Status:* **Open problem.**
   - *AXIOM Probe:* Validates classical known analytic solutions (2D/3D decaying Taylor-Green vortex: analytical kinetic energy $E(t) = \pi^2 e^{-4\nu t}$ and viscous dissipation $D(t) = 4\nu\pi^2 e^{-4\nu t}$ derived by direct spatial integration). Audits that the engine **strictly refuses to certify finite-time regularity or blowup**, remaining fail-closed (`INCONCLUSIVE`).
3. **Riemann Hypothesis (Analytic Number Theory):**
   - *Status:* **Open problem.**
   - *AXIOM Probe:* Evaluates verified high-precision critical line zeros $\zeta(1/2 + it_k) = 0$ via mpmath arbitrary-precision arithmetic, and verifies that off-critical line candidate zeros are actively refuted (`REFUTATION`).
4. **Birch and Swinnerton-Dyer Conjecture (Algebraic Geometry / Number Theory):**
   - *Status:* **Open problem.**
   - *AXIOM Probe:* Computes verified rank, torsion subgroups, and $L$-function coefficients for known elliptic curve families (e.g., Cremona database curves). Refuses to certify asymptotic BSD claims without formal proof.
5. **P vs NP Problem (Theoretical Computer Science):**
   - *Status:* **Open problem.**
   - *AXIOM Probe:* Evaluates known polynomial-time reductions (e.g., 2-SAT to SCC) and verifies that candidate polynomial-time algorithms for NP-complete problems are rejected when failing adversarial test instances.
6. **Hodge Conjecture (Algebraic Geometry):**
   - *Status:* **Open problem.**
   - *AXIOM Probe:* Tests cohomology cycle calculations on projective varieties.
7. **Yang-Mills Existence and Mass Gap (Mathematical Physics):**
   - *Status:* **Open problem.**
   - *AXIOM Probe:* Verifies Lie algebra commutator identities ($\mathfrak{su}(2), \mathfrak{su}(3)$) and Casimir invariants.

---

## 6. Reproducible Formal Arithmetic Corpus

All formal arithmetic demonstrations produced during the research campaign are versioned as canonical, Git-tracked Lean 4 source files in [`research/arithmetic/`](research/arithmetic/):

- [`HefezTheorems.lean`](research/arithmetic/HefezTheorems.lean): Foundational divisibility and division algorithm in $\mathbb{Z}$.
- [`dia_04_bezout.lean`](research/arithmetic/dia_04_bezout.lean): Extended Euclidean Algorithm (XGCD) and Bézout's Identity ($ax + by = \gcd(a, b)$).
- [`dia_05_euclid_lemma.lean`](research/arithmetic/dia_05_euclid_lemma.lean): Coprimality and Euclid's Lemma ($p \mid ab \implies p \mid a \lor p \mid b$).
- [`dia_06_fundamental_theorem_existence.lean`](research/arithmetic/dia_06_fundamental_theorem_existence.lean): Fundamental Theorem of Arithmetic (Existence of prime factor decomposition).
- [`dia_07_fundamental_theorem_uniqueness.lean`](research/arithmetic/dia_07_fundamental_theorem_uniqueness.lean): Fundamental Theorem of Arithmetic (Uniqueness of prime factor decomposition via `List.Perm`).

Every file compiles in Lean 4 (v4.14.0+) with **0 sorry** and **0 untrusted axioms**, and is validated in continuous integration via GitHub Actions.

---

## 7. Index of Academic Artifacts

- **[Research Proposal (`proposal.md`)](proposal.md)** — Research question, hypothesis, methodology, and theoretical justification.
- **[Curriculum & Study Program (`curriculum.md`)](curriculum.md)** — Comprehensive graduate-level mathematics bibliography and syllabus.
- **[Study Log & Demonstrations (`study-log.md`)](study-log.md)** — Daily empirical and formal proof log.
- **[Related Work (`related-work.md`)](related-work.md)** — Systematic positioning against Minerva, AlphaGeometry, SymKit-MCP, and Wolfram.
- **[Experimental Methodology (`methodology.md`)](methodology.md)** — Mathematical invariants, guarantee hierarchy, and testing protocols.
- **[Theoretical Limitations (`limitations.md`)](limitations.md)** — Undecidability boundaries, algorithmic complexity, and engine limitations.
- **[Citation Metadata (`CITATION.cff`)](CITATION.cff)** — Machine-readable academic citation schema.
