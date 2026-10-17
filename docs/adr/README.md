# Architecture Decision Records (ADR Log) — AXIOM

> **Research Math for All Time by [Chronokairo](https://chronokairo.com)**

This directory records the architectural decisions made in the design and evolution of **AXIOM — Mathematical Reasoning Engine** (`One MCP for mathematical computation, exploration, and verification`).

## ADR Index

| ID | Title | Status | Date | Summary |
| :--- | :--- | :---: | :---: | :--- |
| [ADR-0001](0001-repositioning-mathtools-to-axiom-mcp.md) | Repositioning from MathTools Offline to AXIOM MCP Harness | Accepted | 2026-10-17 | Pivot from a monolithic Tauri desktop app to a universal MCP + CLI mathematical reasoning harness inspired by [morluto/rea](https://github.com/morluto/rea). |
| [ADR-0002](0002-safe-ast-mathematical-parser.md) | Safe AST Mathematical Parser without `eval` or `sympify` | Accepted | 2026-10-17 | Parse all mathematical inputs through Python's `ast` module with strict allowlists, implicit multiplication, and precedence-correct `^` exponentiation. |
| [ADR-0003](0003-six-tier-guarantee-and-independent-verification.md) | Mandatory Independent Verification & 6-Tier Guarantee Hierarchy | Accepted | 2026-10-17 | Require every engine result to pass an independent mathematical audit and classify results into 6 explicit logical guarantee tiers. |
| [ADR-0004](0004-multi-engine-adapter-registry.md) | Unified `MathResult` Contract & Multi-Engine Registry | Accepted | 2026-10-17 | Decouple mathematical domains from backend software (`sympy`, `numeric`/`mpmath`, `lean`, `sagemath`, `julia`) behind a single JSON-RPC / CLI contract. |
| [ADR-0005](0005-research-sessions-weakest-link-guarantee.md) | Reproducible Research Sessions & Weakest-Link Guarantee Chain | Accepted | 2026-10-17 | Persist multi-step mathematical explorations in `.axiom/sessions/` and compute `chain_guarantee` as the weakest guarantee in the derivation chain. |
| [ADR-0006](0006-tensor-calculus-mathlib-search-and-zero-dep-svg.md) | Levi-Civita Verified Tensor Calculus, Hybrid Mathlib4 Search & Native SVG Plots | Accepted | 2026-10-17 | Expand AXIOM beyond competing MCP servers (`sympy-mcp`, `fermat-mcp`, `lean-lsp-mcp`) with verified differential geometry, offline+Loogle Mathlib4 search, and zero-dependency SVG/ASCII plotting. |
