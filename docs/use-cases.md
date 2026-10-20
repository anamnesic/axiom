# AXIOM Use Cases & Mathematical Verification Guide

> **Research Math for All Time by [Chronokairo](https://chronokairo.com)**

This guide provides 10 end-to-end, reproducible use cases demonstrating AXIOM's CLI and MCP tools across the **Four Epistemic States** ([ADR-0017](adr/0017-four-epistemic-states-and-soundness-governance.md)):
1. **Proof**: Machine-checked Lean 4 kernel theorems, exact symbolic identities, and verified equation roots.
2. **Approximation**: Bounded numerical evaluations and tolerance-constrained comparisons.
3. **Refutation**: Active counterexample discovery and rejection of fake tautologies.
4. **Inconclusive**: Fail-closed handling of undecidable, unproven, or broken derivation steps.

---

## 1. Verified Algebraic Equation Solving (`math_solve` / `axiom solve`)

- **Epistemic State**: **Proof**
- **Guarantee Level**: `verified-substitution`
- **Verification Rule**: Every root $r$ must satisfy $|f(r)| = 0$ exactly via symbolic substitution. Extraneous roots and singularities are filtered out.

### CLI
```bash
axiom solve "x^2 - 5*x + 6 = 0"
```
**Output**:
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

### MCP JSON-RPC
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "math_solve",
    "arguments": {
      "equation": "x^2 - 5*x + 6 = 0",
      "variable": "x"
    }
  }
}
```

---

## 2. Certified Symbolic Identity & Calculus (`math_simplify` / `axiom simplify`)

- **Epistemic State**: **Proof**
- **Guarantee Level**: `exact-symbolic`
- **Verification Rule**: Algebraic equivalence established via canonical simplification and zero-residual polynomial reduction.

### CLI
```bash
axiom simplify "cos(x)^2 + sin(x)^2"
```
**Output**:
```text
┌─ AXIOM · simplify ─────────────────────────────────────────────────────────────────┐
│ Simplify         cos(x)^2 + sin(x)^2                                               │
│ Result           1                                                                 │
│ LaTeX            1                                                                 │
│ Engine           sympy 1.14.0                                                      │
│ Method           symmetric simplification (sympy.simplify)                         │
│ Verification     symbolic-identity: PASSED                                         │
│ Detail           Symbolic difference reduces to 0 and 10 numerical sample(s) agree │
│ Epistemic State  PROOF                                                             │
│ Guarantee        [VERIFIED] EXACT-SYMBOLIC                                         │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### MCP JSON-RPC
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "math_simplify",
    "arguments": {
      "expression": "cos(x)^2 + sin(x)^2"
    }
  }
}
```

---

## 3. Machine-Checked Theorem Proving in Lean 4 (`math_prove` / `axiom prove`)

- **Epistemic State**: **Proof**
- **Guarantee Level**: `formal-proof`
- **Verification Rule**: Lean 4 kernel elaboration with `#print axioms` confirming zero unproved axioms (`sorry`/`admit` forbidden), depth-aware signature audit, and sandboxed execution (`-M 2048 -T 100000`).

### CLI
```bash
axiom prove "theorem nat_add_comm (n m : Nat) : n + m = m + n := by omega" --engine lean
```
**Output**:
```text
┌─ AXIOM · prove ──────────────────────────────────────────────────────┐
│ Result        theorem nat_add_comm (n m : Nat) : n + m = m + n       │
│ Guarantee     [VERIFIED] FORMAL-PROOF                                │
│ Engine        lean 4 (Lake environment sandbox)                      │
│ Verification  lean4-kernel: PASSED (#print axioms: [])               │
└──────────────────────────────────────────────────────────────────────┘
```

### MCP JSON-RPC
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "math_prove",
    "arguments": {
      "statement": "theorem nat_add_comm (n m : Nat) : n + m = m + n := by omega",
      "engine": "lean"
    }
  }
}
```

---

## 4. High-Precision Numerical Equivalence Probing (`math_compare` / `axiom compare`)

- **Epistemic State**: **Approximation**
- **Guarantee Level**: `numerical-approximation`
- **Verification Rule**: Distinguishes exact symbolic equality from bounded numerical approximation. Finite floating-point tolerance satisfies $\Delta \le \epsilon$ but never claims `EXACT_SYMBOLIC`.

### CLI
```bash
axiom compare "pi" "3.141592653589793" --tolerance 1e-12
```
**Output**:
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

### MCP JSON-RPC
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "math_compare",
    "arguments": {
      "a": "pi",
      "b": "3.141592653589793",
      "tolerance": 1e-12
    }
  }
}
```

---

## 5. Arbitrary-Precision Arithmetic (`math_evaluate` / `axiom evaluate`)

- **Epistemic State**: **Approximation**
- **Guarantee Level**: `numerical-approximation`
- **Verification Rule**: Guard digits prevent catastrophic cancellation; arbitrary bit precision evaluated via `mpmath`.

### CLI
```bash
axiom evaluate "sqrt(2)" --precision 50
```
**Output**:
```text
┌─ AXIOM · evaluate ───────────────────────────────────────────────────┐
│ Evaluate         sqrt(2)                                             │
│ Result           1.4142135623730950488016887242096980785696718753769 │
│ LaTeX            1.4142135623730950488016887242096980785696718753769 │
│ Engine           numeric 1.3.0                                       │
│ Method           arbitrary-precision float evaluation (dps=50)       │
│ Verification     arbitrary-precision-eval: PASSED                    │
│ Detail           Evaluated with 50 digits of working precision       │
│ Epistemic State  APPROXIMATION                                       │
│ Guarantee        [APPROXIMATE] NUMERICAL-APPROXIMATION               │
│ Limitation       rounded to 50 significant digits                    │
└──────────────────────────────────────────────────────────────────────┘
```

### MCP JSON-RPC
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "math_evaluate",
    "arguments": {
      "expression": "sqrt(2)",
      "precision": 50
    }
  }
}
```

---

## 6. Active Refutation of Adversarial Algebraic Claims (`math_compare` / `axiom compare`)

- **Epistemic State**: **Refutation**
- **Guarantee Level**: `[REFUTED] DISPROVEN`
- **Verification Rule**: A constructed 6-root adversarial polynomial $P(x) = (x+1)(x-2)(x-i)(x+i)(x-1-i)(x+2) == 0$ is tested against root probes and refuted by discovering an explicit counterexample ($P(-2) = 200 \neq 0$).

### CLI
```bash
axiom compare "(x+1)*(x-2)*(x^2+1)*(x^2-2*x+2)" "0"
```
**Output**:
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

### MCP JSON-RPC
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "tools/call",
  "params": {
    "name": "math_compare",
    "arguments": {
      "a": "(x+1)*(x-2)*(x^2+1)*(x^2-2*x+2)",
      "b": "0"
    }
  }
}
```

---

## 7. Rejection of Fake Lean Tautologies (`math_prove` / `axiom prove`)

- **Epistemic State**: **Inconclusive / Refused Certification**
- **Guarantee Level**: `unverified`
- **Verification Rule**: Lean proofs using `sorry` or `admit`, trivial reflexive identities $X = X$, or keyword spoofing with mismatched specifications are rejected immediately fail-closed.

### CLI
```bash
axiom prove "theorem fake_claim : 1 = 2 := by admit" --engine lean
```
**Output**:
```text
┌─ AXIOM · prove ──────────────────────────────────────────────────────┐
│ Result        theorem fake_claim : 1 = 2                             │
│ Guarantee     [UNVERIFIED] UNVERIFIED                                │
│ Verification  FAILED: untrusted axiom 'sorryAx' / 'admit' detected   │
└──────────────────────────────────────────────────────────────────────┘
```

### MCP JSON-RPC
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "math_prove",
    "arguments": {
      "statement": "theorem fake_claim : 1 = 2 := by admit",
      "engine": "lean"
    }
  }
}
```

---

## 8. Multi-Step Research Derivations: Step vs. Chain Validity (`math_session` / `axiom session`)

- **Epistemic State**: **Composite Derivation**
- **Invariants**:
  - `step_valid`: True if the local computation passes verification in isolation.
  - `chain_valid`: True only if all antecedent dependencies in the derivation DAG are verified.
  - An imported JSON payload is marked `imported=True, revalidated=False` until local kernel re-execution.

### CLI
```bash
axiom session new --title "Navier-Stokes Dissipation Derivation"
axiom session record --step 1 --command "axiom solve 'x - 1 = 0'"
axiom session record --step 2 --command "axiom prove 'x = 2' --engine sympy" --depends-on 1
axiom session status
```
**Output**:
```text
Step 1: step_valid=True, chain_valid=True, guarantee=verified-substitution
Step 2: step_valid=False, chain_valid=False, broken_dependencies=[1]
Session: all_steps_valid=False, chain_valid=False, chain_guarantee=unverified
```

### MCP JSON-RPC
```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "method": "tools/call",
  "params": {
    "name": "math_session",
    "arguments": {
      "action": "record",
      "expression": "x = 2",
      "depends_on": [1]
    }
  }
}
```

---

## 9. Differential Geometry & Levi-Civita Tensor Calculus (`math_tensor` / `axiom tensor`)

- **Epistemic State**: **Proof**
- **Guarantee Level**: `verified-substitution`
- **Verification Rule**: Christoffel symbols $\Gamma^\lambda_{\mu\nu}$, Riemann tensor $R^\rho_{\sigma\mu\nu}$, and Einstein tensor $G_{\mu\nu}$ are verified via Levi-Civita metric compatibility $\nabla_\lambda g_{\mu\nu} = 0$.

### CLI
```bash
axiom tensor sphere
```
**Output**:
```text
┌─ AXIOM · tensor ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Tensor           sphere                                                                                                                                             │
│ Result           dim=2 (theta, phi), det(g)=sin(theta)**2, |Gamma != 0|=2, R=2                                                                                      │
│ LaTeX            R = 2                                                                                                                                              │
│ Engine           sympy 1.14.0                                                                                                                                       │
│ Method           symbolic Levi-Civita connection & Riemann curvature tensor contractions                                                                            │
│ Verification     levi-civita-metric-compatibility: PASSED                                                                                                           │
│ Detail           Verified g*g^-1 = I, torsion-free symmetry (Gamma^k_ij = Gamma^k_ji), and Levi-Civita metric compatibility (nabla_k g_ij = 0) across 13 identities │
│ Epistemic State  PROOF                                                                                                                                              │
│ Guarantee        [VERIFIED] VERIFIED-SUBSTITUTION                                                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### MCP JSON-RPC
```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "method": "tools/call",
  "params": {
    "name": "math_tensor",
    "arguments": {
      "metric_type": "sphere"
    }
  }
}
```

---

## 10. Vector Plotting with Sandboxed Output Security (`math_plot` / `axiom plot`)

- **Epistemic State**: **Operational State**
- **Guarantee Level**: `sampled-visualization`
- **Security Rule**: Output path is strictly verified against authorized roots (`validate_mcp_path`). Path traversals (`../`) or writes outside authorized workspace directories are rejected with `Permission denied`.

### CLI
```bash
axiom plot "sin(x)/x" --range -10:10 --output sinc.svg
```
**Output**:
```text
┌─ AXIOM · plot ───────────────────────────────────────────────────────┐
│ Function      sin(x)/x                                               │
│ Range         [-10.0, 10.0]                                          │
│ Output        sinc.svg (SVG vector graphic)                          │
│ Guarantee     [SAMPLED] SAMPLED-VISUALIZATION                        │
│ Security      Path authorized within project root                    │
└──────────────────────────────────────────────────────────────────────┘
```

### MCP JSON-RPC
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "tools/call",
  "params": {
    "name": "math_plot",
    "arguments": {
      "expression": "sin(x)/x",
      "range_str": "-10:10",
      "output": "sinc.svg"
    }
  }
}
```
