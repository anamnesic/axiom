---
name: axiom-markitdown-document-converter
description: Convert academic papers (PDFs), Office documents (Word, Excel, PowerPoint), presentations, and multimedia into clean, structured Markdown using Microsoft MarkItDown for downstream mathematical extraction, proof auditing, and evidence synthesis.
---

# Microsoft MarkItDown: Scientific & Mathematical Document Conversion

This skill guides AI agents on converting heterogeneous scientific and mathematical documents (academic PDFs, Office files, spreadsheets, presentations, and audio/image artifacts) into structured Markdown using **Microsoft MarkItDown** (`microsoft/markitdown`).

---

## 1. Role in the AXIOM REA Investigation Paradigm

Under the **REA (Reverse Engineer Anything) paradigm** ([ADR-0019](../../docs/adr/0019-mathematical-investigation-layer-rea-paradigm.md)), AI agents investigate mathematical statements and scientific claims from diverse primary artifacts:
- **Preprints and Monografias (PDF)**: arXiv preprints, Clay Institute problem monographs, conference proceedings.
- **Experimental Data (Excel/CSV)**: Numerical grid evaluations, error convergence tables, eigenvalue tables.
- **Seminar Slides (PowerPoint)**: High-level proof sketches, lemma roadmaps, and conference slide decks.
- **Manuscripts and Notes (Word)**: Colleague drafts, thesis chapters, and informal writeups.
- **Multimedia & Diagrams**: Scientific figures, whiteboard photos with equations, or recorded seminar talks.

**MarkItDown** bridges raw binary/unstructured artifacts and AXIOM's symbolic/formal engines by providing a unified conversion pipeline to clean, parseable Markdown.

---

## 2. Epistemic Separation Principle Guardrail

> [!IMPORTANT]
> **Extracted Content is Unverified Input ([ADR-0020](../../docs/adr/0020-agent-skills-architecture-and-governance.md)):**
> - MarkItDown performs **format extraction**, not mathematical validation.
> - Any text or LaTeX formula extracted via MarkItDown holds the initial epistemic status of `unverified` / `structural-extraction`.
> - Extracted equations, lemmas, or bounds **MUST** be verified through AXIOM's formal proof kernel (Lean 4) or symbolic/numeric engines (`math_solve`, `math_verify`, `math_compare`) before being treated as mathematically sound.
> - **OCR & Transcription Warning**: OCR may introduce typographic bugs (e.g., flipping signs $+ \leftrightarrow -$, confusing greek letters $\nu \leftrightarrow v$, or dropping indices). Always cross-reference with [`verification/property-based-testing`](../../verification/property-based-testing/SKILL.md) and [`research/proof-auditing`](../../research/proof-auditing/SKILL.md).

---

## 3. Toolchain Installation Protocol

Per [`skills/toolchain-management`](../../toolchain-management/SKILL.md), agents **must notify the user** before running package installations.

### Pre-Installation Agent Notification
When MarkItDown is needed to process user files, announce:
```text
"To extract and convert [document.pdf] into structured Markdown for mathematical analysis and proof verification, the Microsoft MarkItDown package is required. Proceeding to install: pip install markitdown"
```

### Installation Commands
```bash
# Core package
pip install markitdown

# Optional: Full feature set (OCR, speech transcription, cloud extensions)
pip install "markitdown[all]"
```

---

## 4. Practical Workflows

### A. Command-Line Workflow

```bash
# 1. Convert an academic PDF preprint to Markdown
markitdown research_paper.pdf > paper.md

# 2. Convert a presentation slide deck with theorem sketches
markitdown seminar_slides.pptx -o slides.md

# 3. Convert an experimental numerical dataset
markitdown simulation_grid.xlsx -o dataset.md
```

### B. Python API Workflow

```python
from markitdown import MarkItDown

md = MarkItDown()

# Convert scientific monograph or paper
result = md.convert("monograph.pdf")
markdown_text = result.text_content

# Save to workspace for analysis
with open("extracted_paper.md", "w", encoding="utf-8") as f:
    f.write(markdown_text)
```

### C. End-to-End AXIOM Investigation Pipeline

When an agent is tasked with evaluating a claim from a PDF paper or thesis:

```
[Academic PDF / PPTX / XLSX]
            │
            ▼ (MarkItDown)
[Structured Markdown Document]
            │
            ├─► Extract Formal Statements / Claims
            │         │
            │         ▼ (math_parse & statement-alignment)
            │   [Canonical Proposition in Lean 4]
            │         │
            │         ▼ (math_prove / lean4)
            │   [Machine-Checked Formal Proof]
            │
            ├─► Extract Symbolic Formulas & Integrals
            │         │
            │         ▼ (math_solve & math_verify)
            │   [Exact Symbolic Certificate]
            │
            └─► Extract Empirical / Simulation Grids
                      │
                      ▼ (math_compare & uncertainty-and-units)
                [Numerical Bound Validation]
```

1. **Extraction**: Run MarkItDown to obtain structured markdown text.
2. **Identification**: Locate theorem statements, definitions, and equations in the markdown.
3. **Auditing**: Apply [`research/proof-auditing`](../../research/proof-auditing/SKILL.md) to inspect proof steps and identify hidden premises or gap candidates.
4. **Formalization**: Use [`formal/statement-alignment`](../../formal/statement-alignment/SKILL.md) and [`formal/lean4`](../../formal/lean4/SKILL.md) to formalize propositions into Lean 4 without drift.
5. **Dossier Generation**: Save evidence and bibliographic citations using [`scientific/reproducibility-statement`](../../scientific/reproducibility-statement/SKILL.md) and [`scientific/citation-verification`](../../scientific/citation-verification/SKILL.md).

---

## 5. Supported Formats Reference

| Format | Extension | Research Application in AXIOM |
| :--- | :--- | :--- |
| **Portable Document Format** | `.pdf` | arXiv preprints, journal papers, Clay Monographs, lecture notes. |
| **Microsoft Word** | `.docx` | Research drafts, collaborator notes, thesis manuscripts. |
| **Microsoft PowerPoint** | `.pptx` | Conference slides, workshop presentations, lemma roadmaps. |
| **Microsoft Excel** | `.xlsx` | Numerical benchmarks, finite element tables, grid convergence data. |
| **Images** | `.jpg`, `.png` | Mathematical whiteboard captures, plots with EXIF metadata, diagrams. |
| **Audio** | `.wav`, `.mp3` | Seminar recordings and technical discussions (via transcription). |
| **Structured Data** | `.csv`, `.json`, `.xml` | Raw numerical outputs, benchmark logs, solver matrices. |
| **Web & Archives** | `.html`, `.zip`, URLs | Web documentation, Wikipedia mathematical articles, ZIP repositories. |
