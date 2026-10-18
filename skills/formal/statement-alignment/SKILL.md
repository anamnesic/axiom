---
name: axiom-statement-alignment
description: Guide AI agents on auditing formal mathematical propositions against canonical statements, preventing keyword spoofing, detecting tautology controls, and avoiding scope drift (e.g. externally forced vs unforced Navier-Stokes).
---

# Formal Statement Alignment & Anti-Drift Audit

Use this skill whenever verifying a formal statement against an external or canonical mathematical conjecture (e.g., Clay Millennium Problems, Goldbach conjecture, or external research claims).

---

## 1. The Specification Drift Problem

A formal theorem may be valid inside Lean 4 (`kernel_verified = True`), yet fail to prove the target mathematical problem because:
1. **Keyword Spoofing**: An elementary theorem named `goldbach_add_zero` or `riemann_trivial_zero` matching keywords must **NEVER** be promoted to a proof of the canonical conjecture.
2. **Domain/Ontology Mismatch**: Elementary arithmetic on `Nat` cannot serve as a proof for smooth PDEs in continuous manifolds.
3. **Scoped/Forced Variants**: Proving Navier-Stokes under external continuous body forcing $f \neq 0$ is a *scoped variant*, NOT a proof of the homogeneous unforced Millennium problem.
4. **Tautology Controls**: Tautologies like $2 + 2 = 2 + 2$ or reflexive identities ($X = X$) must be identified and rejected as proofs of non-trivial mathematical problems.

---

## 2. AXIOM's 4 Alignment States

When auditing alignment via AXIOM's `_audit_specification_alignment`, the formal proposition is classified into one of 4 epistemic alignment states:

| Alignment State | `is_aligned` | `congruent` | Meaning |
| :--- | :---: | :---: | :--- |
| **`verified`** | `True` | `True` | Formally or symbolically proven equivalent to the canonical target statement. |
| **`scoped`** / **`scoped_forced_variant`** | `True` | `False` | Valid within a restricted or forced sub-case; does not resolve the unconstrained problem. |
| **`candidate`** | `True` | `False` | Lexical or thematic match with the target domain; mathematical equivalence is uncertified. |
| **`unaligned`** | `False` | `False` | Domain or ontological mismatch with the canonical statement. |
| **`tautology_control`** | `False` | `False` | Syntactic reflexive tautology ($X = X$, `rfl`) against a canonical claim; rejected fail-closed. |

---

## 3. Invocation Protocol

Always pass `--canonical-statement` and the declared alignment when invoking AXIOM:

### CLI Example
```bash
axiom prove examples/navier_stokes_forced.lean \
  --engine lean \
  --canonical-statement "Clay Millennium Navier-Stokes Existence and Smoothness (unforced homogeneous 3D)" \
  --spec-alignment scoped_forced_variant
```

### Verification Checks for Agents
1. Ensure `spec_alignment["congruent"] == True` before claiming a conjecture is resolved.
2. Ensure `assumptions_audit["status"] == "clean"`: no undeclared implicit hypotheses.
3. If `spec_alignment["status"] == "scoped"`, clearly document the restricted domain boundaries in the research report.
