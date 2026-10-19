---
name: axiom-navier-stokes-euler-blowup
description: Guide AI agents on formalizing, analyzing, and auditing finite-time blowup singularities for 3D incompressible Navier-Stokes (Clay Millennium Alternatives C/D) and Euler equations in Lean 4 with multi-kernel verification (Comparator/Nanoda).
---

# 3D Navier–Stokes & Euler Finite-Time Blowup Verification

Use this skill when investigating continuum fluid dynamics, singularity formation, vorticity blowup, and formal proof verification for the **3D Incompressible Navier–Stokes** and **Euler equations**, based on the formalization methodology established by OpenAI (`openai/NavierStokesAndEuler`) and Google DeepMind (`google-deepmind/formal-conjectures`).

---

## 1. Mathematical Background & The Clay Millennium Problem

In Charles Fefferman's official Clay Mathematics Institute formulation, the Navier–Stokes Millennium Prize Problem consists of four distinct statements for the 3D incompressible system:

$$\frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u} \cdot \nabla)\mathbf{u} = -\nabla p + \nu \Delta \mathbf{u} + \mathbf{f}, \quad \nabla \cdot \mathbf{u} = 0$$

with viscosity $\nu > 0$, velocity field $\mathbf{u}(x, t)$, pressure $p(x, t)$, and body forcing $\mathbf{f}(x, t)$.

### The Four Official Clay Alternatives:
1. **(A) Global Smoothness on $\mathbb{R}^3$ ($f = 0$):** Every smooth divergence-free initial datum with compact/rapid decay has a smooth global solution with uniformly bounded kinetic energy. (*Open*)
2. **(B) Global Smoothness on $\mathbb{T}^3 = \mathbb{R}^3/\mathbb{Z}^3$ ($f = 0$):** Every smooth periodic initial datum has a smooth global periodic solution. (*Open*)
3. **(C) Breakdown on $\mathbb{R}^3$ ($f \neq 0$):** There exist smooth initial data and physically admissible forcing $\mathbf{f}$ for which no global smooth solution exists with uniformly bounded energy. (*Formalized by OpenAI*)
4. **(D) Breakdown on $\mathbb{T}^3$ ($f \neq 0$):** There exist smooth periodic initial data and forcing $\mathbf{f}$ for which no global smooth periodic solution exists. (*Formalized by OpenAI*)

### The Unforced 3D Euler Equation:
For inviscid fluid flow ($\nu = 0$, unforced $\mathbf{f} = 0$):
$$\frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u} \cdot \nabla)\mathbf{u} = -\nabla p, \quad \nabla \cdot \mathbf{u} = 0$$
OpenAI formalizes that smooth, compactly supported initial velocity on $\mathbb{R}^3$ develops a finite-time singularity where the $C^1$ velocity norm and the time integral of the vorticity $L^\infty$ norm diverge:
$$\int_0^{T^*} \|\boldsymbol{\omega}(\cdot, t)\|_{L^\infty} \, dt = \infty \quad \text{(Beale–Kato–Majda criterion)}$$

---

## 2. Epistemic Separation & Dual-Layer Architecture

Following the **Principle of Epistemic Separation** ([ADR-0020](../../docs/adr/0020-agent-skills-architecture-and-governance.md)), never conflate problem specifications with candidate proof certificates:

```
┌──────────────────────────────────────────────────────────────────┐
│  Specification Layer (Reference Challenge)                       │
│  - DeepMind FormalConjectures / ComparatorChallenges             │
│  - Pure, independent definition of PDE smoothness and breakdown │
└─────────────────────────────────┬────────────────────────────────┘
                                  │ audited alignment
┌─────────────────────────────────▼────────────────────────────────┐
│  Solution / Proof Layer (Candidate Certificate)                  │
│  - OpenAI NavierStokesAndEuler / CandidateProperties             │
│  - Parabolic scaling, periodization, angular vorticity growth    │
└─────────────────────────────────┬────────────────────────────────┘
                                  │ kernel typecheck + #print axioms
┌─────────────────────────────────▼────────────────────────────────┐
│  Multi-Kernel Verification Layer                                 │
│  - Lean 4 Core Kernel + Nanoda External Typechecker             │
│  - Permitted Axioms: propext, Quot.sound, Classical.choice      │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Candidate Invariant Structure in Lean 4

When formalizing or auditing a Navier–Stokes breakdown candidate in Lean 4:

```lean
structure CandidateProperties (ν : ℝ) (u : VelocityField) (p : PressureField)
    (f : VelocityField) (K : Set Space) : Prop where
  velocity_smooth     : ContDiffOn ℝ ∞ u preSingularDomain
  pressure_smooth     : ContDiffOn ℝ ∞ p preSingularDomain
  force_smooth        : ContDiff ℝ ∞ f
  velocity_periodic   : UnitSpatialPeriodsOn (Ico 0 1) u
  pressure_periodic   : UnitSpatialPeriodsOn (Ico 0 1) p
  force_periodic      : UnitSpatialPeriodsOn (Ici 0) f
  support_compact     : IsCompact K
  support_interior    : K ⊆ fundamentalInterior
  zero_initial_vel    : ∀ x, u (0, x) = 0
  force_time_support  : CompactFutureTimeSupport f
  divergence_free     : ∀ t ∈ Ico 0 1, ∀ x, spatialDivergence u t x = 0
  navier_stokes       : ∀ t ∈ Ioo 0 1, ∀ x, navierStokesResidual ν u p t x = f (t, x)
  speed_unbounded     : SpeedUnboundedAtOne u
```

---

## 4. Verification Workflow with AXIOM

### Step 1: Formal Kernel Verification & Axiom Audit
Run AXIOM on the formal candidate file to verify machine acceptance and check for untrusted axioms:
```bash
axiom prove path/to/NavierStokesSolution.lean --engine lean
```
Verify that:
- `guarantee` is `formal-proof`
- `axioms_used` contains only canonical foundational axioms (`propext`, `Quot.sound`, `Classical.choice`)
- `has_hole` is `False` (zero `sorry` or `admit`)

### Step 2: Specification Alignment Audit
Audit against the canonical Clay Millennium Problem specification:
```bash
axiom prove path/to/NavierStokesSolution.lean \
  --engine lean \
  --canonical-statement "Clay Millennium Navier-Stokes (Alternative D - Periodic Breakdown with Forcing)" \
  --spec-alignment scoped_forced_variant
```

### Step 3: Physical Invariant & Conservation Probing
Use AXIOM's computer algebra engine to symbolically check local divergence, dissipation balance, and scaling:
```bash
# Verify spatial divergence free condition symbolically
axiom diff "u_x" -v x
axiom diff "u_y" -v y
axiom diff "u_z" -v z
axiom compare "diff(u_x, x) + diff(u_y, y) + diff(u_z, z)" "0"
```

### Step 4: Multi-Kernel Audit via Comparator / Nanoda
When working within a Lake workspace containing the Comparator setup:
```bash
lake exe comparator ComparatorChallenges/NavierStokes.json
lake exe comparator ComparatorChallenges/Euler.json
```

---

## 5. Epistemic Soundness Rules for Agents

> [!WARNING]
> **1. Forcing Scope Governance:**
> Proving finite-time blowup with external forcing $\mathbf{f} \neq 0$ resolves **Alternative (C) or (D)** of the Clay Prize Problem. It **DOES NOT** resolve the unforced homogeneous existence problem (Alternatives A and B). Agents must NEVER claim that the unforced 3D Navier–Stokes problem is resolved by a forced solution.

> [!IMPORTANT]
> **2. Forcing Admissibility Criteria:**
> Under Clay rules, the forcing $\mathbf{f}(x, t)$ must be smooth, compactly supported in time, or decay rapidly in space ($|\partial_x^\alpha \partial_t^m \mathbf{f}| \le C_{K, m} (1 + |x| + t)^{-K}$). A force that diverges or creates a trivial singularity directly in $\mathbf{f}$ is invalid.

> [!TIP]
> **3. Euler Unforced Singularity:**
> Unlike Navier–Stokes, the 3D incompressible Euler blowup established by OpenAI is **unforced** ($\mathbf{f} = 0$), proving that nonlinear vortex stretching alone is sufficient to overcome inertia in the inviscid regime.
