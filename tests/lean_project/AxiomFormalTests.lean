-- Valid Lean 4 formal proofs audited by AXIOM via `lake env lean` and `#print axioms`

theorem nat_add_comm_verified (n m : Nat) : n + m = m + n := by
  omega

theorem int_linear_identity (x y : Int) : (x + y) - y = x := by
  omega
