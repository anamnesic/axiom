# ADR-0001: Repositioning from MathTools Offline to AXIOM MCP Harness

- **Status:** Accepted
- **Date:** 2026-10-17
- **Author:** Chronokairo ([chronokairo.com](https://chronokairo.com))

## Context

The repository originally housed *MathTools Offline*, a Tauri/React/FastAPI desktop application bundling local LaTeX/Typst editing and SymPy/Lean wrappers. Meanwhile, AI coding and research agents (Claude Code, Cursor, Gemini CLI, Codex, etc.) increasingly require a standardized, verifiable mathematical infrastructure accessible over the **Model Context Protocol (MCP)** and a composable **CLI**.

Inspired by [morluto/rea](https://github.com/morluto/rea) (*Reverse Engineer Anything*), which provides a unified MCP + CLI harness over specialized binary-analysis engines (Ghidra, IDA, Hopper) returning structured evidence, we needed an equivalent architecture for computational and formal mathematics.

## Decision

1. Rename the project and package root to **AXIOM — Mathematical Reasoning Engine** (*One MCP for mathematical computation, exploration, and verification*).
2. Flatten the Python package into the repository root (`pyproject.toml`, `src/axiom/`, `tests/`, `benchmarks/`) and remove legacy desktop UI/SaaS folders (`frontend/`, `backend/`, `src-tauri/`).
3. Expose all capabilities simultaneously through:
   - **21 composable MCP tools** over JSON-RPC 2.0 `stdio` (`axiom mcp` / `axiom-mcp`).
   - **A rich CLI** (`axiom <subcommand>`) with box-formatted human output, `--plain`, and `--json`.
   - **Zero-friction agent onboarding** (`axiom setup` and `axiom doctor`).

## Consequences

- Any MCP-compatible agent can invoke AXIOM without GUI dependencies or proprietary API keys.
- All legacy desktop bloat is eliminated in favor of a focused, testable, zero-compromise mathematical reasoning core.
