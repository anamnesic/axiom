# Millennium Research Bench — AXIOM

Consolidated empirical and analytical benchmark covering the **Seven Clay Millennium Prize Problems**.

## Scope and Principles

1. **Not a claim of resolution**: This benchmark does not claim to solve open Millennium problems. It evaluates the reasoning engine's capability to compute known invariants, verify solutions, detect singularities, and refute false claims.
2. **Strict Fail-Closed Enforcement**: Mathematical claims must strictly require logical proof or exact symbolic cancellation. Unproven assertions, negative controls, and open-problem boundary probes must fail-closed (`unverified` with `passed = False` or `status in ("disproven", "inconclusive")`).
3. **Four Testing Levels**:
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
