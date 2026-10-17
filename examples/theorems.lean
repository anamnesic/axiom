-- Example formal theorems for `axiom prove examples/theorems.lean --engine lean`

theorem add_zero_right (n : Nat) : n + 0 = n := by
  rfl

theorem eq_refl_nat (a : Nat) : a = a := by
  rfl
