---
name: axiom-fluidsim-pde
description: Guide AI agents on analyzing fluid dynamics PDEs, verifying Taylor-Green vortex incompressibility (div u = 0), momentum balance, and exact kinetic energy decay for Navier-Stokes investigations.
---

# Fluid Dynamics PDE Exploration & Navier-Stokes Probing

Use this skill when investigating continuum fluid mechanics, Partial Differential Equations (PDEs), or experimental simulations related to the **Navier-Stokes Millennium Problem**.

---

## 1. Mathematical Background: The Taylor-Green Vortex

The 2D Taylor-Green vortex is an exact analytical solution to the incompressible Navier-Stokes equations on the periodic torus $\mathbb{T}^2 = [0, 2\pi]^2$:

$$\mathbf{u}(x, y, t) = \begin{pmatrix} u(x, y, t) \\ v(x, y, t) \end{pmatrix} = \begin{pmatrix} \sin(x)\cos(y) e^{-2\nu t} \\ -\cos(x)\sin(y) e^{-2\nu t} \end{pmatrix}$$
$$p(x, y, t) = \frac{1}{4} \left(\cos(2x) + \cos(2y)\right) e^{-4\nu t}$$

### Key Invariant Checks:
1. **Incompressibility (Solenoidal Condition)**:
   $$\nabla \cdot \mathbf{u} = \frac{\partial u}{\partial x} + \frac{\partial v}{\partial y} = \cos(x)\cos(y)e^{-2\nu t} - \cos(x)\cos(y)e^{-2\nu t} = 0$$
2. **Exact Momentum Balance (X-component)**:
   $$\frac{\partial u}{\partial t} + u\frac{\partial u}{\partial x} + v\frac{\partial u}{\partial y} + \frac{\partial p}{\partial x} - \nu \nabla^2 u = 0$$
3. **Kinetic Energy Decay**:
   $$E(t) = \frac{1}{2} \int_{\mathbb{T}^2} (u^2 + v^2) \, dx dy = \pi^2 e^{-4\nu t}$$
4. **Energy Dissipation Rate**:
   $$\frac{dE}{dt} = -4\nu \pi^2 e^{-4\nu t} = -2\nu \int_{\mathbb{T}^2} |\nabla \mathbf{u}|^2 \, dx dy$$

---

## 2. Verification Protocol with AXIOM

```bash
# 1. Verify incompressibility
axiom diff "sin(x)*cos(y)*exp(-2*nu*t)" -v x
axiom diff "-cos(x)*sin(y)*exp(-2*nu*t)" -v y
axiom compare "(cos(x)*cos(y)*exp(-2*nu*t)) + (-cos(x)*cos(y)*exp(-2*nu*t))" "0"

# 2. Verify momentum balance residual
axiom compare "-2*nu*sin(x)*cos(y)*exp(-2*nu*t) + (1/2)*sin(2*x)*exp(-4*nu*t) - (1/2)*sin(2*x)*exp(-4*nu*t) - (-2*nu*sin(x)*cos(y)*exp(-2*nu*t))" "0"

# 3. Verify kinetic energy time derivative
axiom diff "pi^2 * exp(-4*nu*t)" -v t
axiom compare "diff(pi^2 * exp(-4*nu*t), t)" "-4*nu*pi^2 * exp(-4*nu*t)"
```

---

## 3. Epistemic Warning for Millennium Problem Probing

> [!WARNING]
> **Simulations $\neq$ Global Smoothness Proofs:**
> Verifying exact solutions (Taylor-Green) or executing numerical grid simulations demonstrates that specific initial data remain smooth. However, it **does NOT prove** global existence and smoothness for *all* $C^\infty$ divergence-free initial conditions on $\mathbb{R}^3$, which is the open Millennium Problem requirement. Always classify simulation findings as `verified-substitution` or `numerical-approximation`, never as a proof of the Millennium Problem.
