---
name: axiom-uncertainty-and-units
description: Guide AI agents on performing dimensional analysis, verifying physical unit consistency, evaluating scale invariance, and propagating interval uncertainty bounds across equations.
---

# Uncertainty, Units & Dimensional Analysis

Use this skill when analyzing physical equations, continuum mechanics models, or numerical approximations where dimensional consistency and error bounds must be formally audited.

---

## 1. Principles of Dimensional & Uncertainty Analysis

1. **Buckingham $\pi$ Theorem & Homogeneity**:
   Every physically meaningful equation must be dimensionally homogeneous. Both sides of an equality and all terms in an additive expression must share identical dimensional powers:
   $$[A + B] \implies [A] = [B]$$
2. **Dimensionless Ratios**:
   Arguments to transcendental functions ($\exp(x)$, $\sin(x)$, $\ln(x)$) must be dimensionless:
   $$\left[\exp\left(-\frac{2\nu t}{L^2}\right)\right] \implies \left[\frac{\nu t}{L^2}\right] = 1$$
   *(e.g., in Navier-Stokes Taylor-Green vortex: $[\nu] = L^2 T^{-1}$, $[t] = T$, $[L] = L \implies [\nu t / L^2] = 1$)*.
3. **Rigorous Uncertainty Propagation**:
   When evaluating floating-point quantities or experimental parameters, propagate interval bounds:
   $$\delta(A \cdot B) \approx |B| \delta A + |A| \delta B$$
   AXIOM outputs must explicitly report `max_error` and `tolerance` whenever `guarantee == "numerical-approximation"`.

---

## 2. AXIOM Workflows for Dimensional Verification

### Example: Verifying the Dimensionless Argument of the Taylor-Green Vortex

In the 2D Taylor-Green velocity field:
$$u(x, y, t) = \sin(x)\cos(y) e^{-2\nu t}$$

Verify that the time-derivative and viscous dissipation terms match dimensions:
```bash
# Time derivative: du/dt = -2*nu*sin(x)*cos(y)*exp(-2*nu*t)
axiom diff "sin(x)*cos(y)*exp(-2*nu*t)" -v t

# Viscous Laplacian: nu * (d^2u/dx^2 + d^2u/dy^2) = -2*nu*sin(x)*cos(y)*exp(-2*nu*t)
axiom compare "-2*nu*sin(x)*cos(y)*exp(-2*nu*t)" "nu * (-sin(x)*cos(y)*exp(-2*nu*t) - sin(x)*cos(y)*exp(-2*nu*t))"
```

### Probing Numerical Approximations with Explicit Tolerance
```bash
# Compare with declared error tolerance
axiom compare "1.0000000000000001" "1.0" --tolerance 1e-15
# Returns: approximately_equal (max_error: 1e-16, tolerance: 1e-15)
```

---

## 3. Epistemic Invariants for Agents

- **Exact vs. Approximate**: Never confuse an approximate equality ($A \approx B$) with an exact symbolic identity ($A = B$).
- If physical units clash, flag the derivation as **DIMENSIONALLY INVALID** immediately before attempting numerical calculation.
