# ADR-0003: Mandatory Independent Verification & 6-Tier Guarantee Hierarchy

- **Status:** Accepted
- **Date:** 2026-10-17
- **Author:** Chronokairo ([chronokairo.com](https://chronokairo.com))

## Context

Existing mathematical MCP servers (`sympy-mcp`, `fermat-mcp`, `Wolfram-MCP`) act as pass-through calculator wrappers: they return whatever the underlying CAS outputs without independent checking, and they conflate exact identities, numerical approximations, and formal proofs.

## Decision

1. Enforce **independent verification** (`src/axiom/verification.py`) in the AXIOM core before returning any `MathResult`:
   - **Equations & Systems:** Substitute candidate roots back into `lhs - rhs` using exact arithmetic + high-precision `mpmath`.
   - **Integrals:** Differentiate the antiderivative $F'(x)$ and verify equivalence with the integrand $f(x)$ (or cross-check definite integrals via adaptive Gaussian quadrature).
   - **Derivatives & Limits:** Cross-check symbolic derivatives against 35-digit finite differences and limits against asymptotic sequence probes.
   - **Linear Algebra:** Verify $A A^{-1} = I$, $\det(A - \lambda I) = 0$, $Av = \lambda v$, $PA = LU$, $Ax - b = 0$, and division-free Berkowitz determinants.
   - **ODEs:** Substitute $y(x)$ back into the differential equation and reduce residuals to zero.
   - **Number Theory:** Multiply prime factors back to $n$ (checking primality of each factor), verify Bézout's identity $ax + by = g$, and check all CRT congruences.
   - **Proofs (Lean 4):** Reject any proof containing `sorry` or `admit` from ever receiving a formal guarantee.
2. Classify every result using a strict 6-tier `Guarantee` enum ordered by logical strength:
   `formal-proof` > `exact-symbolic` > `verified-substitution` > `numerical-approximation` > `heuristic` > `unverified`.

## Consequences

- Hallucinated or bogus candidate solutions (`axiom verify "x^2 - 5*x + 6 = 0" --solutions 2,4`) are deterministically refuted and downgraded to `unverified`.
- AI agents can programmatically inspect `result.verified` and `result.guarantee` to know the exact epistemic status of every step.
