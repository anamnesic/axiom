# ADR-0021: Lean 4 Namespace-Aware Proof Auditing, UTF-8 Console Resilience & Mathematical Corpus Verification

## Status
Accepted

## Date
2026-10-19

## Context
During real-world formal verification experiments on primary mathematical literature from `research/math` (specifically the formalization and machine-checked proof of 9 foundational number theory theorems from *Iniciação à Aritmética* by Prof. Abramo Hefez, SBM/OBMEP), three key technical friction points were identified in AXIOM's verification pipeline:

1. **Namespace Blindness in `#print axioms` Ingestion:**
   When formal proofs in Lean 4 were organized inside module namespaces (e.g., `namespace HefezArithmetic ... end HefezArithmetic`), AXIOM's regular expression extractor captured only the bare theorem identifier (`hefez_dvd_linear_comb`) and injected `#print axioms hefez_dvd_linear_comb` at the end of the file. Because this injection occurred outside the closed `namespace` block, the Lean 4 compiler failed with `unknown constant`, improperly downgrading valid formal proofs to `unverified`.

2. **Windows Console Encoding Crashes (`cp1252` vs. `UTF-8`):**
   Standard Windows command prompts and PowerShell instances default to legacy code page encodings (such as `cp1252`), which cannot encode mathematical Unicode characters (such as the divisibility relation symbol `∣` `\u2223`, checkmarks `✓` `\u2713`, or mathematical blackboard bold notations). When printing diagnostics or theorem verification trees, Python would abort with unhandled `UnicodeEncodeError`.

3. **Incremental Corpus Verification Framework:**
   To systematically improve AXIOM through daily verification of the complete mathematics repository (`research/math`), a structured, 120-day pedagogical curriculum was required, enforcing the Epistemic Separation Principle (ADR-0020) and ensuring internal formal proofs remain isolated in `build/` (gitignored) rather than exposed in public educational content.

---

## Decision

We make the following improvements to AXIOM's engine and verification architecture:

### 1. Lexical Scope & Namespace Stack Tracking in LeanEngine
In [`src/axiom/engines/lean_engine.py`](../../src/axiom/engines/lean_engine.py), `prepare_audited_source` now tracks open `namespace` and `section` blocks using a document-order lexical scanner:
- Tracks nested namespace hierarchies (e.g., `namespace Math.Algebra`).
- Correctly distinguishes `section` scoping from `namespace` qualification.
- Generates fully qualified `#print axioms <Full.Qualified.Name>` directives.
- In `verify_theorem_audit_coverage`, bidirectional matching is enforced:
  ```python
  matched = any(
      actual == expected
      or actual.endswith(f".{expected}")
      or expected.endswith(f".{actual}")
      for actual in audited_theorems
  )
  ```

### 2. UTF-8 Stream Reconfiguration for Windows Consoles
At the entry point of the CLI in [`src/axiom/cli.py`](../../src/axiom/cli.py), `sys.stdout` and `sys.stderr` are reconfigured to `utf-8` with fallback error replacement on `win32` platforms:
```python
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
```

### 3. Interactive Component Setup via Checklist
[`setup_env.py`](../../setup_env.py), [`setup.ps1`](../../setup.ps1), and [`setup.sh`](../../setup.sh) are enhanced with a `--custom` / `--checklist` mode:
- Enables interactive component-by-component selection (CAS, MarkItDown, SciPy, Matplotlib, MCP, Test Suite, Lean 4, Julia).
- Supports batch non-interactive selection via `--select cas,docs,lean`.

### 4. 120-Day Mathematical Corpus Roadmap
A comprehensive roadmap has been deployed directly to [`research/math/CHECKLIST_PROVAS.md`](../../../math/CHECKLIST_PROVAS.md), detailing 120 daily milestone theorems across:
- **Mês 1 (Dias 01-30):** Fundações, Aritmética de Peano, Divisibilidade e Teoria dos Números.
- **Mês 2 (Dias 31-60):** Lógica, Teoria dos Conjuntos e Álgebra Abstrata (Grupos, Anéis, Espaços Vetoriais).
- **Mês 3 (Dias 61-90):** Análise Real, Cálculo Rigoroso e Teorema Fundamental do Cálculo.
- **Mês 4 (Dias 91-120):** Análise no $\mathbb{R}^n$, EDOs, Análise Complexa e Geometria Diferencial (Gauss-Bonnet).

---

## Consequences

- **Robust Namespace Auditing:** Lean 4 modules with arbitrary nested namespaces and sections are audited seamlessly without manual namespace stripping.
- **Console Stability:** AXIOM CLI and doctor reports can safely emit mathematical symbols, proof trees, and Unicode diagnostic messages on Windows without encoding exceptions.
- **Continuous Engine Improvement:** Each theorem proven from the curriculum progressively stresses AXIOM's formal and symbolic engines, ensuring test-driven hardening across higher mathematics.
