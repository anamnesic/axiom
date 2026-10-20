# ADR-0030: Linear Diophantine Equations, Modular Arithmetic & Book 1 Completion (Days 09 & 10)

- **Status:** Accepted
- **Date:** 2026-10-20
- **Authors:** AXIOM Engineering Team & Chronokairo Research
- **Deciders:** Mathematical Core Working Group
- **Consulted:** Formal Arithmetic & Number Theory Group
- **Informed:** AI Coding & Research Agents (Antigravity, Codex, Claude Code, Cursor)

---

## Context & Problem Statement

Days 09 and 10 of the 120-Day Formal Verification Roadmap (`research/math/CHECKLIST_PROVAS.md`) conclude the foundational study of the first textbook in the acervo: *"Iniciação à Aritmética"* (Prof. Abramo Hefez, SBM/OBMEP).

The objectives are:
1. **Day 09 (Linear Diophantine Equations, Hefez Cap. 3.10)**:
   - Prove the necessary and sufficient solvability criterion: $a x + b y = c$ has integer solutions if and only if $\gcd(a, b) \mid c$;
   - Prove Hefez's Theorem 3.5 establishing the exact general solution family $(x_0 + t \cdot b, y_0 - t \cdot a)$ for coprime coefficients;
   - Formally verify the canonical postal stamps problem (Problema 3.54: $3x + 5y = 50$).
2. **Day 10 (Congruence Relations & Modular Arithmetic, Hefez Cap. 4)**:
   - Formalize the congruence relation $a \equiv b \pmod m \iff m \mid (a - b)$;
   - Prove that congruence is an equivalence relation (reflexive, symmetric, transitive);
   - Prove algebraic compatibility with addition, subtraction, multiplication, and powers ($\forall k \in \mathbb{N}, a^k \equiv b^k \pmod m$);
   - Formally prove modular invertibility via Bézout's identity: $\exists x, a x \equiv 1 \pmod m \iff \gcd(a, m) = 1$.
3. **Book 1 Completion Milestone**:
   - Conclude 100% of all curriculum milestones selected from Abramo Hefez's textbook, advancing the global checklist to 10/120 days.

---

## Decision Drivers

1. **Constructive & Self-Contained Proofs**: Keep all proofs independent of external Mathlib dependencies, relying purely on the Lean 4 core kernel and the `omega` tactic for cross-version compatibility between CI (v4.14.0) and local development (v4.35.0).
2. **Zero-Trust Session Revalidation**: Ensure each derivation step is logged into reproducible research sessions (`.axiom/sessions/dia-09-diophantine.json` and `.axiom/sessions/dia-10-congruences.json`) and successfully re-verified locally.
3. **Zero Sorry Guarantee**: Every theorem, lemma, and auxiliary relation must pass `#print axioms` auditing with zero sorry holes and only trusted kernel axioms (`propext`, `Quot.sound`).

---

## Decision Outcome

1. **Formalized Day 09 (`research/arithmetic/dia_09_diophantine.lean`)**:
   - Proved `diophantine_dvd_c`, `diophantine_particular_solution`, `coprime_dvd_mul_int`, `diophantine_general_valid`, `hefez_diophantine_complete`, and `hefez_selos_valid` with 10 audited theorems/examples.
2. **Formalized Day 10 (`research/arithmetic/dia_10_congruences.lean`)**:
   - Proved `cong_refl`, `cong_symm`, `cong_trans`, `cong_add`, `cong_sub`, `cong_mul`, `cong_pow`, `invertible_of_bezout`, and `bezout_of_invertible` with 12 audited theorems/examples.
3. **Audited via AXIOM**:
   - Both files verified with `ax.verify_lean_file` returning `guarantee: formal-proof` and `verification.passed = True`.
4. **Recorded and Revalidated Sessions**:
   - Saved and revalidated `.axiom/sessions/dia-09-diophantine.json` and `.axiom/sessions/dia-10-congruences.json`.
5. **Advanced Roadmap to 10/120 Days**:
   - Completed 100% of Book 1 (*Iniciação à Aritmética*). Next on the roadmap: Day 11 (Fermat's Little Theorem from Brochero et al.).
