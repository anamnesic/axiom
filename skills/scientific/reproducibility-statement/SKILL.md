---
name: axiom-reproducibility-statement
description: Guide AI agents on authoring cryptographic reproducibility statements, generating SHA-256 evidence manifests, recording toolchain versions, and publishing self-contained reproduction commands.
---

# Reproducibility Statements & Cryptographic Evidence Dossiers

Use this skill when finalizing an AXIOM investigation, benchmark, or research dossier to ensure that third-party researchers and independent agents can reproduce all claims exactly.

---

## 1. Pillars of Mathematical Reproducibility

Every verified claim and research report produced with AXIOM must be accompanied by a **Reproducibility Statement** containing four pillars:

1. **Self-Contained Reproduction Command (`reproducible_with`)**:
   Every step must provide the exact CLI invocation that reproduces the output without ambient state dependencies.
   *(Example: `axiom solve "x^2 - 5*x + 6 = 0" --engine sympy`)*
2. **Cryptographic Source Manifest (SHA-256)**:
   All tracked source files, theorem files, and data fixtures must be digested with SHA-256 to guarantee that evidence cannot be silently modified.
3. **Environment & Toolchain Specification**:
   Document the exact versions of Python, SymPy, mpmath, Lean 4, elan, Lake, and OS architecture.
4. **Independent Revalidation Script**:
   Provide a standalone Python script (`validate.py`) that re-executes all checks from scratch and validates that metrics meet fail-closed invariants ($100\%$ fail-closed, $0\%$ false positives).

---

## 2. Standard Reproducibility Statement Template

Add this section to all research reports (`reports/*/REPORT.md` or `validation.json`):

```markdown
## Reproducibility Statement

### 1. Environment & Engine Versions
- **AXIOM Version**: 0.2.7
- **Python**: 3.14.7 (CPython, x86_64)
- **SymPy**: 1.14.0
- **mpmath**: 1.3.0
- **Lean 4**: 4.35.0 (commit eb6cafb7290e, Release)
- **Lake**: 4.35.0

### 2. Cryptographic Source Hashes (SHA-256)
- `src/axiom/core.py`: `d41d8cd98f00b204e9800998ecf8427e...`
- `src/axiom/engines/lean_engine.py`: `e3b0c44298fc1c149afbf4c8996fb924...`
- `reports/p-vs-np/validate.py`: `8f434346648f6b96df89dda901c5176b...`

### 3. Automated Reproduction
To verify all results independently from repository root:
```bash
python reports/p-vs-np/validate.py
python benchmarks/millennium/run_millennium_bench.py
```
```

---

## 3. Automated Export via AXIOM

AXIOM research sessions automatically embed evidence steps and reproduction commands:

```bash
# Export the complete session markdown dossier
axiom session export --name "my-investigation"
```
The exported markdown contains individual `reproducible_with` tags for every recorded step, guaranteeing full auditability.
