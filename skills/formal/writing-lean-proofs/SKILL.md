---
name: axiom-writing-lean-proofs
description: Guide AI agents on decomposing complex mathematical proofs into modular Lean 4 lemmas, selecting effective Mathlib tactics (omega, ring, linarith, aesop, simp), and structuring proof libraries.
---

# Writing Structured Lean 4 Proofs

Use this skill when designing or restructuring non-trivial Lean 4 proofs, libraries, and lemmata.

---

## 1. Modular Decomposition Protocol

Monolithic Lean proofs that attempt to prove a major theorem in a single `by ...` block frequently cause timeout errors or unsolvable state explosions. Follow this decomposition protocol:

1. **Top-Level Goal**: State the target theorem cleanly with typed binders and explicit assumptions.
2. **Helper Lemmas (`lemma`)**: Split independent arithmetic, algebraic, or topological subgoals into private/local lemmas before the main theorem.
3. **Tactical Specialization**: Choose the right tactic for the algebraic domain:
   - **`omega`**: Presburger arithmetic on `Nat` and `Int` (linear integer equalities, inequalities, divisions by constants).
   - **`ring`**: Equational identities in commutative rings or fields (polynomial expansion, factorization identities).
   - **`linarith`**: Linear real/rational inequalities with linear constraints.
   - **`aesop`**: Automated search for propositional logic, inductive types, and simple relational chains.
   - **`simp [lemmas]`**: Canonical simplification using equational rewrite rules.
   - **`exact` / `apply`**: Direct term-mode application of known Mathlib theorems.

---

## 2. Recommended Structure Template

```lean
import Mathlib.Tactic.Ring
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Omega

namespace AxiomInvestigation

-- Step 1: Auxiliary lemma for algebraic identity
lemma sq_diff_factor (x y : ℝ) : x^2 - y^2 = (x - y) * (x + y) := by
  ring

-- Step 2: Bound lemma under domain assumptions
lemma positive_product_bound {x y : ℝ} (hx : x > 0) (hy : y > 0) : x * y > 0 := by
  exact mul_pos hx hy

-- Step 3: Main target theorem composing the lemmas
theorem target_bound (a b : ℝ) (ha : a > 0) (hb : b > a) : b^2 - a^2 > 0 := by
  rw [sq_diff_factor]
  have hdiff : b - a > 0 := by linarith
  have hsum : b + a > 0 := by linarith
  exact positive_product_bound hdiff hsum

end AxiomInvestigation
```

---

## 3. Validation via AXIOM

Always run the completed file through AXIOM's Lean engine:

```bash
axiom prove path/to/structured_proof.lean --engine lean
```

Verify that all auxiliary lemmas and the target theorem appear in `audited_theorems` with clean axiom audit logs.
