# AXIOM Agent Skills Library

Welcome to the **Chronokairo AXIOM Agent Skills Library**.

This repository contains specialized, standardized Agent Skills (following the Agent Skill format with YAML frontmatter) designed to guide AI agents (Claude Code, Antigravity, Codex, Copilot Workspace, and subagents) in performing rigorous mathematical investigation, formal theorem proving, verification, and reproducible research.

> [!IMPORTANT]
> **The Epistemic Separation Principle ([ADR-0020](../docs/adr/0020-agent-skills-architecture-and-governance.md)):**
> Skills are **cognitive protocols and execution instructions** for agents. They do NOT replace or bypass mathematical verification kernels. A claim is only verified when certified by AXIOM's formal proof assistant (Lean 4) or symbolic/numeric computer algebra engines (SymPy, mpmath).

---

## Skills Taxonomy & Index

### 1. Foundational Skills
- [`mathematics`](mathematics/SKILL.md) — Core MCP & CLI interface for algebraic computation, calculus, equation solving, and verification.
- [`toolchain-management`](toolchain-management/SKILL.md) — OS-aware detection and guided installation of heavy toolchains (Lean 4, Lake, Julia) with mandatory user justification.

### 2. Formalization & Interactive Proofs (`formal/`)
- [`formal/lean4`](formal/lean4/SKILL.md) (`axiom-lean4-proofs`) — Interactive Lean 4 proof development, compilation, and `#print axioms` auditing (detecting `sorryAx` and untrusted axioms).
- [`formal/writing-lean-proofs`](formal/writing-lean-proofs/SKILL.md) (`axiom-writing-lean-proofs`) — Modular theorem decomposition, tactic selection (`omega`, `ring`, `aesop`, `simp`), and Mathlib convention compliance.
- [`formal/statement-alignment`](formal/statement-alignment/SKILL.md) (`axiom-statement-alignment`) — Anti-drift semantic audit: ensuring formal propositions accurately align with canonical problems and preventing lexical keyword spoofing.

### 3. Open Mathematical Research (`research/`)
- [`research/math-research`](research/math-research/SKILL.md) (`axiom-math-research`) — Structured exploration of open problems, tracking proven milestones vs. known theoretical barriers (e.g. Relativization, Natural Proofs, Algebrization) in `.axiom/sessions/`.
- [`research/proof-auditing`](research/proof-auditing/SKILL.md) (`axiom-proof-auditing`) — Auditing informal mathematical papers and LaTeX derivations to identify logic gaps, circular reasoning, and undeclared assumptions.

### 4. Computational Experimentation & Physics (`computational/`)
- [`computational/uncertainty-and-units`](computational/uncertainty-and-units/SKILL.md) (`axiom-uncertainty-and-units`) — Dimensional analysis, physical unit consistency, and interval error propagation across equations.
- [`computational/fluidsim`](computational/fluidsim/SKILL.md) (`axiom-fluidsim-pde`) — PDE experimentation, Taylor-Green vortex simulation, kinetic energy decay, and Navier-Stokes dissipation probing.

### 5. Adversarial Verification & Integrity (`verification/`)
- [`verification/property-based-testing`](verification/property-based-testing/SKILL.md) (`axiom-property-based-testing`) — Algebraic invariant testing, boundary value probing, and automated counterexample generation.
- [`verification/mutation-testing`](verification/mutation-testing/SKILL.md) (`axiom-mutation-testing`) — Mutation testing of mathematical specifications and test suites to ensure 100% fail-closed detection.
- [`verification/spec-to-code-compliance`](verification/spec-to-code-compliance/SKILL.md) (`axiom-spec-to-code-compliance`) — Validating that algorithmic implementations strictly satisfy declared formal contracts.

### 6. Scientific Documentation & Reproducibility (`scientific/`)
- [`scientific/literature-review`](scientific/literature-review/SKILL.md) (`axiom-literature-review`) — Systematic literature reviews, prior art taxonomies, and theorem dependency mapping.
- [`scientific/citation-verification`](scientific/citation-verification/SKILL.md) (`axiom-citation-verification`) — Auditing bibliography files, validating DOIs/arXiv identifiers, and eliminating hallucinatory citations.
- [`scientific/reproducibility-statement`](scientific/reproducibility-statement/SKILL.md) (`axiom-reproducibility-statement`) — Generating cryptographic SHA-256 evidence dossiers and self-contained reproduction commands.

---

## Agent Usage Guidelines

When an AI agent engages with a user request involving mathematical reasoning or verification:
1. **Identify the relevant skill** from the taxonomy above.
2. **Follow the skill's instructions** and invoke AXIOM via MCP tools (`math_*`) or CLI (`axiom *`).
3. **Inspect the `guarantee` and `verification` fields**:
   - `formal-proof`: Machine-checked proof verified by Lean 4 kernel.
   - `exact-symbolic`: Analytically proven symbolic identity.
   - `verified-substitution`: Candidate solution verified by exact back-substitution.
   - `numerical-approximation`: Validated numerical evaluation with explicit `max_error`.
   - `unverified` / `heuristic`: Non-proven conjectures or refutations.
4. **Enforce fail-closed reporting**: Never claim a result is proven without an explicit `formal-proof` or `exact-symbolic` certificate.
