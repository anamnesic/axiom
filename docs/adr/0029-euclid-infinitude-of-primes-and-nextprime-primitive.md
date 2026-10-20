# ADR-0029: Euclid's Infinitude of Primes Verification & Prime Generation Primitives (Day 08)

- **Status:** Accepted
- **Date:** 2026-10-20
- **Authors:** AXIOM Engineering Team & Chronokairo Research
- **Deciders:** Mathematical Core Working Group
- **Consulted:** Automated Reasoning & Formal Arithmetic Team
- **Informed:** AI Coding & Research Agents (Antigravity, Codex, Claude Code, Cursor)

---

## Context & Problem Statement

As part of the 120-Day Formal Mathematical Verification Roadmap (`research/math/CHECKLIST_PROVAS.md`), Day 08 requires formal machine-checked verification of **Euclid's Theorem on the Infinitude of Prime Numbers** based on Abramo Hefez's *"Iniciação à Aritmética"* (Chapter 2.4, Page 40).

The roadmap mandates:
1. Formalization in Lean 4 without holes (`sorry`), using constructive witnesses rather than non-constructive classical logic alone;
2. Independent audit and kernel certification via AXIOM (`ax.verify_lean_file`);
3. Expansion of computational mathematics primitives in AXIOM for prime generation and minimality verification;
4. Reproducible research session recording and revalidation under zero-trust imported semantics.

---

## Decision Drivers

1. **Constructive Witness Integrity**: Rather than relying purely on classical non-constructive contradiction ($\neg \neg \exists p$), prove constructively that for every $n \in \mathbb{N}$, the smallest prime factor of $n! + 1$ satisfies $p > n$.
2. **Computational Prime Minimality**: Provide a verified computational primitive (`nextprime`) that not only checks primality of candidate $p > n$, but independently verifies minimality by ensuring no prime exists in the open interval $(n, p)$.
3. **Ergonomic Formal Audit API**: Expose `ax.verify_lean_file` on the `Axiom` harness to streamline CI and agentic proof checking workflows.
4. **Reproducible Session Dossier**: Record all derivation steps in `.axiom/sessions/dia-08-euclid-infinitude.json` with weakest-link guarantee tracking.

---

## Decision Outcome

1. **Formalized Day 08 in Lean 4 (`research/arithmetic/dia_08_euclid_infinitude.lean`)**:
   - Defined constructive minimum factor search `minFacAux` and `minFac`;
   - Formally proved:
     - `fact_pos`: $1 \le n!$
     - `minFac_prime`: the least factor $\ge 2$ of $n \ge 2$ is prime;
     - `exists_prime_dvd`: constructive existence of a prime divisor;
     - `dvd_fact`: $p \le n \implies p \mid n!$;
     - `prime_dvd_consecutive`: $p \mid a + 1 \land p \mid a \implies p \mid 1$;
     - `hefez_euclid_infinitude_primes`: $\forall n \in \mathbb{N}, \exists p, \operatorname{IsPrime}(p) \land n < p$;
     - `hefez_primes_unbounded`: $\neg \exists L \in \mathbb{N}, \forall p \in \mathbb{P}, p \le L$.
   - Verified 8 computational `#eval` test cases for Euclid numbers $E_n = n! + 1$ (OEIS A006862).
2. **Added Verified Prime Generation Primitive (`nextprime`)**:
   - Integrated into `SymPyEngine.number_theory("nextprime")` and exposed via `ax.nextprime(n)`.
   - Independent verification check `nextprime-primality-and-minimality-check` audits that:
     1. $p \ge 2$ and $p$ is prime;
     2. $p > n$;
     3. $\operatorname{prevprime}(p) \le n$ (proving minimality and non-existence of primes in $(n, p)$).
3. **Added `ax.verify_lean_file` Convenience Method**:
   - Direct alias for `ax.prove(path, engine="lean")`, matching CI audit scripts and CLI contracts.
4. **Recorded and Revalidated Session**:
   - Created `.axiom/sessions/dia-08-euclid-infinitude.json` (5 valid steps, `chain_valid = True`, `chain_guarantee = verified-substitution`).
5. **Updated Checklist**:
   - Advanced `research/math/CHECKLIST_PROVAS.md` to 8/120 days completed.
