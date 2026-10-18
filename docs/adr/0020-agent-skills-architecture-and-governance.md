# ADR-0020: Agent Skills Architecture, Taxonomy and Epistemic Governance

## Status
Accepted

## Date
2026-10-18

## Context
As Chronokairo AXIOM expands under the REA (Reverse Engineer Anything) paradigm for mathematics (ADR-0019), AI agents (such as Claude Code, Codex, Antigravity, Copilot Workspace, and autonomous research subagents) interact with AXIOM across multiple investigation stages:
1. Mathematical conjecture analysis and literature investigation.
2. Formalization and theorem proving in Lean 4 / Mathlib.
3. Computational experimentation, PDE simulation, and numerical probing.
4. Independent verification, property-based testing, and mutation auditing.
5. Scientific documentation, citation verification, and reproducible dossiers.

Previously, AXIOM provided only a single root skill ([`skills/mathematics/SKILL.md`](../../skills/mathematics/SKILL.md)) and an operational toolchain skill ([`skills/toolchain-management/SKILL.md`](../../skills/toolchain-management/SKILL.md)). As external agent skills proliferate across GitHub (e.g. Trail of Bits, K-Dense AI, Kalaris Labs, Superpowers, AI4Math), there is a critical architectural danger:
**Instructions in Markdown (Skills) must NEVER be confused with mathematical certificates or proofs.**
An LLM prompt or agent instruction can guide an agent to verify a condition, but only the AXIOM verification kernel, computer algebra engines (SymPy, mpmath), and formal proof assistants (Lean 4) can issue mathematical certificates (`formal-proof`, `exact-symbolic`, `verified-substitution`, `numerical-approximation`).

## Decision

We establish a formal **Agent Skills Architecture and Epistemic Governance Framework** for Chronokairo AXIOM:

### 1. Functional Taxonomy
All agent skills in AXIOM are organized by area of responsibility under `skills/`:

```
skills/
├── README.md                      # Index of all available skills and guidelines
├── mathematics/                   # Foundational MCP & CLI interface skill
├── toolchain-management/          # Host OS installer & notification skill
├── research/                      # Open mathematical problem investigation
│   ├── math-research/             # Hypothesis tracking, barrier analysis, sessions
│   └── proof-auditing/            # Informal LaTeX proof auditing & logic gap detection
├── formal/                        # Interactive theorem proving & spec alignment
│   ├── lean4/                     # Lean 4 kernel, Lake, #print axioms, sorryAx detection
│   ├── writing-lean-proofs/       # Proof structure, Mathlib tactics, modular lemmas
│   └── statement-alignment/       # Canonical statement anti-drift & ontology audit
├── computational/                 # Symbolic & numerical experimentation
│   ├── uncertainty-and-units/     # Dimensional analysis & interval error propagation
│   └── fluidsim/                  # PDE dynamics, Navier-Stokes Taylor-Green probes
├── verification/                  # Adversarial testing & contract compliance
│   ├── property-based-testing/    # Invariant testing & counterexample search
│   ├── mutation-testing/          # Specification mutation & fail-closed test auditing
│   └── spec-to-code-compliance/   # Contract checking & behavioral compliance
└── scientific/                    # Reproducibility & academic documentation
    ├── literature-review/         # Systematic survey & theorem corpus mapping
    ├── citation-verification/     # BibTeX hygiene, DOI/arXiv validation, hallucination checks
    └── reproducibility-statement/ # Cryptographic SHA-256 dossiers & reproduction scripts
```

### 2. Epistemic Invariants & Governance Rules
Every AXIOM Agent Skill must strictly enforce the following invariants:

1. **The Separation Principle**:
   - Skills are *agent protocols*, not mathematical engines.
   - A skill must strictly distinguish between:
     - A **Conjecture** (unproven hypothesis, `guarantee: unverified`).
     - A **Proof Attempt** (heuristic reasoning or incomplete derivation).
     - **Computational Evidence** (numerical approximation or finite sampling).
     - A **Certified Proof** (`formal-proof` verified by Lean 4 kernel without `sorry`).
2. **Fail-Closed Rule**:
   - If an engine or toolchain is unavailable, or if verification fails, the skill must mandate falling back to `Guarantee.UNVERIFIED` with `verification.passed = False`.
   - Never allow an agent to declare success or equivalence based solely on lexical keyword matching.
3. **Reproducibility Mandate**:
   - Every result reported to the user or recorded in a session must include the exact CLI command or MCP call (`reproducible_with`) and evidence metadata.
4. **Mandatory User Justification**:
   - Skills that trigger external toolchain installations must require the agent to notify and explain the reason to the user before running OS package managers.

## Consequences

### Positive
- Standardized, discoverable protocols for LLM agents working with AXIOM.
- Prevents cognitive hallucination and premature claims of mathematical breakthroughs.
- Directly addresses gaps P0-01 through P0-04 identified in repository audits.
- Organizes skills systematically by responsibility rather than an unmaintainable flat directory.

### Negative
- Requires maintaining YAML frontmatter and documentation consistency across skills.
- Adds test obligations to verify skill metadata integrity.
