# ADR-0028: Gap Audit Traceability, Security Policy & Contribution Governance

- **Status:** Accepted
- **Date:** 2026-10-20
- **Authors:** AXIOM Engineering Team & Chronokairo Research
- **Deciders:** Mathematical Core Working Group
- **Consulted:** Automated Reasoning & Epistemic Verification Team
- **Informed:** AI Coding & Research Agents (Antigravity, Codex, Claude Code, Cursor)

---

## Context & Problem Statement

Following the initial gap audit conducted on v0.2.5 (commit `66307c3`), numerous soundness improvements, subprocess sandboxing measures, and session revalidation features were merged across ADR-0017 through ADR-0027. However:
1. `TODO.md` required a comprehensive update reflecting current execution status across all 43 audit items and confirming completion of the 10/10 acceptance criteria.
2. `limitations.md` still identified the engine as v0.2.1 and needed updating to reflect v0.2.8, including sandbox boundaries, Lean syntax parsing limits, and algebraic completeness guarantees.
3. Open-source governance files (`SECURITY.md` and `CONTRIBUTING.md`, gaps P2-20 and P2-21) were missing from the repository root.
4. `docs/readme/README_pt-BR.md` and `reports/README.md` contained legacy references to preliminary tool counts and commands.
5. In Lean 4 formal test workspaces, Lake 5.0 configuration format migration (`lakefile.toml`) was needed to ensure seamless integration with modern Lean toolchains.

---

## Decision Drivers

1. **Epistemic Traceability**: Explicitly track every identified gap with its resolution commit, ADR, or planned milestone.
2. **Security & Threat Model Transparency**: Clearly document the execution threat model, AST parser allowlists, path restrictions, and responsible disclosure process in `SECURITY.md`.
3. **Open-Source Contribution Integrity**: Mandate zero-mock test invariants and fail-closed defaults in `CONTRIBUTING.md`.
4. **Documentation Alignment**: Synchronize Portuguese documentation and reports with the current 21 MCP tools, 4 epistemic states, and 111 benchmark criteria.

---

## Decision Outcome

1. **Updated `TODO.md`**:
   - Confirmed 10/10 acceptance criteria completed (100%).
   - Categorized all 54 audit items: 4/4 P0 gaps completed (100%), 20/28 P1 gaps completed (71.4%), 9/22 P2 gaps completed (40.9%).
   - Established roadmap toward v0.3.0 (Mathematical Investigation Layer / REA paradigm).
2. **Published `SECURITY.md` & `CONTRIBUTING.md`**:
   - Added vulnerability reporting protocol, threat boundary definitions, and pull request invariants.
3. **Updated `limitations.md` to v0.2.8**:
   - Clarified theoretical barriers (Richardson, Gödel, Matiyasevich), process sandboxing limits, and algebraic completeness verification.
4. **Updated `tests/lean_project/lakefile.toml`**:
   - Modernized Lake workspace configuration for Lake 5.0+ compatibility.
5. **Synchronized `docs/readme/README_pt-BR.md` & `reports/README.md`**:
   - Aligned tool definitions, epistemic states, and benchmark criteria counts.
