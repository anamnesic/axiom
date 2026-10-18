---
name: axiom-mutation-testing
description: Guide AI agents on conducting mutation testing on mathematical specifications, injecting deliberate perturbations (sign flips, boundary shifts, off-by-one errors) to ensure verifiers fail-closed.
---

# Mutation Testing for Mathematical Soundness

Use this skill to audit the resilience of AXIOM's verification test suites and benchmark criteria against subtle mathematical defects.

---

## 1. What is Mathematical Mutation Testing?

A test suite can show 100% code coverage while failing to detect incorrect mathematical claims if assertions are too lenient or check only superficial metadata.

Mutation testing introduces **deliberate mathematical perturbations (mutants)** into specifications, inputs, or solver outputs to ensure that:
1. Every mutated claim is actively **killed** (detected and rejected).
2. The verification system **fails closed** (`guarantee: unverified`, `verification.passed: false`).
3. Zero false positives are produced ($FPR = 0.0\%$).

---

## 2. Standard Mutation Operators for Mathematical Software

| Mutation Operator | Original Expression | Mutated Expression (Mutant) | Expected Verifier Response |
| :--- | :--- | :--- | :--- |
| **Sign Inversion** | $x^2 - 4 = 0$ | $x^2 + 4 = 0$ | Roots $\{2, -2\}$ must be **refuted** for the mutated equation. |
| **Constant Perturbation** | $\zeta(2) = \frac{\pi^2}{6}$ | $\zeta(2) = \frac{\pi^2}{8}$ | Must be **refuted** (`compare_basel_false`). |
| **Tolerance Bypass** | $10^{-30} = 0$ | $10^{-30} \neq 0$ | Must **reject exact equality**, classified as `approximately_equal` only if tolerance is explicitly passed. |
| **Pole Boundary Crossing** | $\int_0^1 \frac{1}{\sqrt{x}} dx = 2$ | $\int_{-1}^1 \frac{1}{x^2} dx$ | Must **reject** divergent Cauchy principal value. |
| **Tautology Spoofing** | $\text{Navier-Stokes unforced}$ | $2 + 2 = 2 + 2$ (`fake_rh`) | Must be **rejected** by `spec_alignment` as `tautology_control`. |
| **Undeclared Hypothesis** | $\forall n \in \mathbb{N}, n + 0 = n$ | Assumes $n > 0$ implicitly | Must emit `warning_undeclared_hypotheses` and block canonical proof. |

---

## 3. Auditing Process with AXIOM

1. **Construct Mutants**: Create an adversarial variant of a verified claim.
2. **Execute AXIOM Verifier**: Run `axiom verify` or `axiom compare`.
3. **Assert Mutant Rejection**:
   ```python
   # Verify mutant is killed
   res = ax.compare("zeta(2)", "pi^2/8")
   assert res.verification.passed is False
   assert res.value["status"] == "disproven"
   assert res.guarantee == Guarantee.UNVERIFIED
   ```
4. **Benchmark Verification**: Run `python benchmarks/millennium/run_millennium_bench.py` to confirm all negative controls fail closed.
