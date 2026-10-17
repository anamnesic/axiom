# ADR-0007: Lean 4 `#print axioms` Auditing, Verifier Fail-Closed Hardening, and Codex `config.toml`

- **Status:** Accepted
- **Date:** 2026-10-17
- **Author:** Chronokairo ([chronokairo.com](https://chronokairo.com))

## Context

Following the code review of commit `7f15084028` and the first GitHub Actions CI run (`Ubuntu`/`Windows`/`macOS` × Python `3.10`/`3.12`), five high-priority engineering issues were identified:

1. **CI Python 3.10 Syntax Error:** `src/axiom/core.py` used a backslash inside an f-string expression (`{'=' if equivalent else r'\\neq'}`), which is valid in Python 3.12 (PEP 701) but raises `SyntaxError` in Python 3.10.
2. **P0 — Lean 4 Axiom Auditing:** Rejecting `sorry` and `admit` by regex alone does not prevent a proof from depending on a user-declared `axiom`, `unsafe`, `@[implemented_by]`, or indirect `sorryAx`.
3. **P0 — Verifier Fail-Closed Discipline:** `verify_integral()`, `verify_limit()`, and `verify_derivative()` could fall back to returning `Guarantee.EXACT_SYMBOLIC` if numerical quadrature or sequence probing raised an exception.
4. **P1 — Lean 4 Lake Environment:** Invoking `lean` directly on a standalone file without `lake env lean` prevents local Lake project and Mathlib 4 imports from resolving.
5. **P1 — OpenAI Codex Configuration Format:** OpenAI Codex CLI reads MCP server definitions from `~/.codex/config.toml` (`[mcp_servers.axiom]`), not `.codex/mcp.json`.

## Decision

1. **Python 3.10 AST Compatibility Guard:**
   - Remove all backslashes inside f-string `{...}` expressions and add `test_python310_fstring_compatibility` to scan every `.py` file's AST on every test run.
2. **Lean 4 `#print axioms` & Lake Project Execution (`src/axiom/engines/lean_engine.py`):**
   - Strip comments before scanning declarations; detect user-declared `axiom`, `unsafe`, `opaque`, and `@[implemented_by]`/`@[extern]`/`@[csimp]` attributes.
   - Rewrite anonymous `example` headers into named `_axiom_example_N` theorems and automatically append `#print axioms <name>` for every theorem/lemma.
   - Parse Lean 4's `#print axioms` output and allow only standard foundational Lean 4 axioms (`propext`, `Classical.choice`, `Quot.sound`, `Lean.ofReduceBool`, `Lean.trustCompiler`). Any dependency on `sorryAx` or custom axioms downgrades the result to `Guarantee.UNVERIFIED`.
   - Detect `lakefile.lean` / `lakefile.toml` in ancestor directories and run `lake env lean <file>` inside the project root when `lake` is available.
3. **Fail-Closed Verifiers (`src/axiom/verification.py`):**
   - Remove all optimistic fallback returns from `verify_derivative`, `verify_integral`, and `verify_limit`.
   - For definite integrals where numerical quadrature is inapplicable (e.g., symbolic parameters), attempt an independent FTC antiderivative check ($F'(x) = f(x)$ and $F(b) - F(a) = \text{result}$). If neither quadrature nor independent FTC verification succeeds, return `passed=False` and `Guarantee.UNVERIFIED`.
4. **Codex `~/.codex/config.toml` Support (`src/axiom/setup_agent.py`):**
   - Configure Codex via `~/.codex/config.toml` (`[mcp_servers.axiom]`) with `.axiom.bak` backup and provide the `codex mcp add axiom` CLI command in dry-run output.

## Consequences

- All 6 OS × Python CI combinations pass cleanly.
- No verifier in AXIOM can ever elevate a computation to `EXACT_SYMBOLIC` or `FORMAL_PROOF` without positive independent evidence.
