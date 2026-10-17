# Lemmas & Formal Proofs — AXIOM Research

Registry of auxiliary mathematical lemmas proven symbolically or formalized via the Lean 4 kernel.

## Structure of a Lemma Entry

Every lemma entry (`LEMMA-####.md` or `.lean`) must specify:
1. **Title and Mathematical Statement**.
2. **Context and Application**.
3. **Engine Used**: SymPy (`exact-symbolic`) or Lean 4 (`formal-proof`).
4. **Lean 4 Formal Code and `#print axioms` Audit**:
   - Must prove non-empty axiom coverage.
   - Must not contain unverified `sorry` or unchecked axioms.
5. **Reproducibility Command**.
