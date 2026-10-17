# ADR-0005: Reproducible Research Sessions & Weakest-Link Guarantee Chain

- **Status:** Accepted
- **Date:** 2026-10-17
- **Author:** Chronokairo ([chronokairo.com](https://chronokairo.com))

## Context

In multi-step mathematical research, an AI agent may combine formal proofs, exact symbolic identities, numerical approximations, and unverified conjectures. A derivation chain is only as strong as its weakest step, yet standard chat contexts lose track of which steps were formally proved versus numerically approximated.

## Decision

1. Introduce `ResearchSession` (`src/axiom/session.py`), exposed via `axiom session` and MCP tool `math_session` (`show`, `record`, `hypothesis`, `export`, `clear`).
2. Compute `chain_guarantee` across all recorded steps using a strict **weakest-link ordering**:
   $$\text{chain\_guarantee} = \min_{i} \text{rank}(\text{step}_i.\text{guarantee})$$
3. Persist sessions as JSON in `.axiom/sessions/<name>.json` and support one-command Markdown export (`axiom session export`) with full reproduction commands and conjecture verification status.

## Consequences

- Multi-step mathematical explorations become auditable, reproducible artifacts.
- If a 10-step symbolic derivation relies on a single numerical approximation or unverified step, the session's `chain_guarantee` automatically reflects that limitation.
