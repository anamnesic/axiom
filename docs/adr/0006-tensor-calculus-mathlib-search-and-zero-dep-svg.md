# ADR-0006: Levi-Civita Verified Tensor Calculus, Hybrid Mathlib4 Search & Native SVG Plots

- **Status:** Accepted
- **Date:** 2026-10-17
- **Author:** Chronokairo ([chronokairo.com](https://chronokairo.com))

## Context

A competitive analysis of the 2026 MCP mathematics landscape (`docs/analise-concorrencia-mcp-2026.md`) identified three specialized features across competing servers:
1. `sdiehl/sympy-mcp` offered tensor/differential-geometry calculation (`metric`, `christoffel`, `riemann`, `ricci`), but without independent verification.
2. `project-numina/lean-lsp-mcp` offered Mathlib4 theorem search (`loogle`), but required live external servers and lacked a symbolic/numerical CAS.
3. `abhiphile/fermat-mcp` offered plot image export via `matplotlib`, which fails in lightweight environments where `matplotlib` is not installed.

## Decision

1. **Verified Differential Geometry & Tensor Calculus (`math_tensor` / `axiom tensor`):**
   - Implement symbolic computation of $g^{\mu\nu}$, $\det(g)$, Christoffel symbols $\Gamma^\lambda_{\mu\nu}$, Riemann tensor $R^\rho_{\ \sigma\mu\nu}$, Ricci tensor $R_{\mu\nu}$, Ricci scalar $R$, and Einstein tensor $G_{\mu\nu}$ (with presets `polar`, `sphere`, `spherical_2d`, `cylindrical`, `minkowski`, `schwarzschild` and custom matrices).
   - Independently verify every tensor result via `verify_tensor_op`, checking $g_{\mu\alpha} g^{\alpha\nu} = \delta^\nu_\mu$, torsion-free symmetry $\Gamma^\lambda_{\mu\nu} = \Gamma^\lambda_{\nu\mu}$, and **Levi-Civita metric compatibility** ($\nabla_\lambda g_{\mu\nu} = 0$).
2. **Hybrid Mathlib 4 Search (`math_search_mathlib` / `axiom search-mathlib`):**
   - Embed a curated offline Mathlib 4 & Lean 4 Core catalog (`_MATHLIB_CATALOG`) with exact signatures and tactic hints for 100% offline determinism, and optionally merge live results from the Loogle JSON API (`--online`).
3. **Zero-Dependency Vector SVG + ASCII Plot Renderer (`math_plot` / `axiom plot`):**
   - Generate self-contained vector SVG markup (`_render_svg_plot`) and terminal ASCII previews (`_render_ascii_plot`) natively in `src/axiom/core.py` without requiring `matplotlib`, while preserving `matplotlib` `.png`/`.pdf` output when installed.

## Consequences

- AXIOM surpasses both CAS-only MCPs (`sympy-mcp`, `fermat-mcp`) and formal-only MCPs (`lean-lsp-mcp`) within a single verified 21-tool harness.
