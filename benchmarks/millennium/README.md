# Millennium Research Bench — AXIOM

Consolidated empirical and analytical benchmark covering the **Seven Clay Millennium Prize Problems**.

## Scope and Principles

1. **Not a claim of resolution**: This benchmark does **NOT claim to solve or advance** any open Clay Millennium problems. It evaluates the reasoning engine's capability to compute known invariants, verify classical exact solutions, detect singularities, and refute false claims.
   - **Poincaré Conjecture**: Solved by Grigori Perelman (2002–2003); AXIOM audits known differential geometry invariants (Levi-Civita connection, Ricci tensor, Einstein metrics) and makes no claim of a new proof.
   - **Navier-Stokes**: Validates known analytical decaying Taylor-Green vortex solutions ($E(t) = \pi^2 e^{-4\nu t}$, $D(t) = 4\nu\pi^2 e^{-4\nu t}$) while strictly refusing to certify unproven regularity or finite-time blowup claims.
2. **Statistical Bounds on Negative Controls**:
   - Total Criteria: $n = 111$.
   - Negative Controls & Adversarial Probes: $n_{neg} = 40$.
   - Observed False Positives: $0 / 40$ ($0.0\%$).
   - Statistical 95% Confidence Upper Bound (Rule of Three): $\approx 3/40 = 7.5\%$ (Clopper-Pearson 95% CI: $[0.00\%, 7.22\%]$).
3. **Strict Fail-Closed Enforcement**: Mathematical claims must strictly require logical proof or exact symbolic cancellation. Unproven assertions, negative controls, and open-problem boundary probes must fail-closed (`unverified` with `passed = False` or `status in ("disproven", "inconclusive")`).
4. **Four Testing Levels**:
   - **Level 1**: Exact positive reproduction of published identities and classical solutions.
   - **Level 2**: Negative controls and adversarial counterexample refutations.
   - **Level 3**: Formal theorem and lemma verification with Lean 4 kernel checks.
   - **Level 4**: Fail-closed exploratory probes on open mathematical statements.

## Running the Full Benchmark

From the repository root:

```powershell
python benchmarks/millennium/run_millennium_bench.py
```

This executes all seven validation suites in `reports/` and generates a consolidated status report.
