# ADR-0004: Unified `MathResult` Contract & Multi-Engine Registry

- **Status:** Accepted
- **Date:** 2026-10-17
- **Author:** Chronokairo ([chronokairo.com](https://chronokairo.com))

## Context

Different mathematical tasks require different computational engines: symbolic manipulation (`SymPy`, `SageMath`), arbitrary-precision numerical evaluation (`mpmath`, `Julia`), and formal theorem proving (`Lean 4`). Agents should not have to learn separate tool schemas or output formats for each backend.

## Decision

1. Define a single self-describing contract (`MathResult`, `Evidence`, `Verification`, `Guarantee` in `src/axiom/contract.py`) shared across all engines, CLI commands, and MCP tools.
2. Implement `EngineRegistry` (`src/axiom/registry.py`) managing 5 engine adapters:
   - `SymPyEngine` (`sympy`) — symbolic algebra, calculus, matrices, ODEs, number theory, optimization, statistics, and tensor calculus.
   - `NumericEngine` (`numeric` via `mpmath`) — arbitrary-precision evaluation, root-finding, and adaptive quadrature.
   - `LeanEngine` (`lean`) — Lean 4 formal kernel verification, equality auto-formalization, and Mathlib 4 search.
   - `SageEngine` (`sagemath`) — external SageMath CLI adapter when installed on host.
   - `JuliaEngine` (`julia`) — external Julia CLI adapter when installed on host.

## Consequences

- Swapping or adding engines does not change the MCP schema or CLI output structure.
- Every computation records full provenance (`engine`, `engine_version`, `method`, `steps`, `reproducible_with`).
