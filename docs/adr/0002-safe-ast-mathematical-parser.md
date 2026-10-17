# ADR-0002: Safe AST Mathematical Parser without `eval` or `sympify`

- **Status:** Accepted
- **Date:** 2026-10-17
- **Author:** Chronokairo ([chronokairo.com](https://chronokairo.com))

## Context

Passing untrusted mathematical strings from LLM agents or users into Python's `eval()` or SymPy's default `sympify()` (which internally invokes `eval`) creates arbitrary code execution vulnerabilities. Additionally, agents frequently write `x^2` for exponentiation and `2x` or `(x+1)(x-1)` for implicit multiplication. In Python's grammar, `^` is bitwise XOR (`ast.BitXor`), which has lower operator precedence than `+` and `*`, causing naive AST translations to misparse `x^2 - 5*x + 6` as `x**(2 - 5*x + 6)`.

## Decision

1. Implement `axiom.parsing.Parser` using `ast.parse(..., mode="eval")` and walk the AST node-by-node against an explicit allowlist of mathematical functions, constants, and operators.
2. Normalize `^` to `**` prior to AST parsing so exponentiation binds with true mathematical precedence (`**` tighter than `*`, `/`, `+`, `-`).
3. Support implicit multiplication (`2x`, `3(x+1)`, `(x+1)(x-1)`) without breaking multi-digit numeric literals (`4*x` stays `4*x`, never `4*0`).

## Consequences

- Arbitrary code execution via mathematical expressions is structurally impossible (`__import__('os').system(...)` is rejected at the AST level).
- Natural mathematical notation from humans and LLMs parses deterministically into canonical SymPy expressions, relations, and matrices.
