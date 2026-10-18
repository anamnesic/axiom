---
name: axiom-citation-verification
description: Guide AI agents on auditing academic citations, validating BibTeX entries against DOI and arXiv registries, detecting hallucinatory references, and ensuring research integrity.
---

# Citation Verification & Reference Hygiene

Use this skill when auditing academic citations, checking bibliography files (`.bib`), or verifying that cited papers, authors, and theorems exist.

---

## 1. The Citation Hallucination Risk

LLMs frequently generate realistic-sounding citations with plausible authors, fictitious journal volumes, or hallucinated arXiv numbers.

To maintain scientific integrity in AXIOM research dossiers:
1. **Never accept an unvalidated citation**: Every cited paper must be confirmed against an authoritative registry:
   - **arXiv**: Verified by identifier format (e.g. `arXiv:2104.xxxxx`).
   - **DOI**: Resolvable via `https://doi.org/<doi>`.
   - **Clay Mathematics Institute**: Verified against official problem descriptions (`claymath.org`).
2. **Attribution Accuracy**: Verify that the cited author actually proved the claimed theorem, rather than attributing a known classical result to a contemporary paper.
3. **BibTeX Field Hygiene**: Ensure `title`, `author`, `year`, `journal` or `booktitle`, and `doi`/`eprint` fields are accurate and consistent.

---

## 2. Citation Verification Checklist

When compiling research reports in `reports/`:

- [ ] Does the citation include a valid DOI or arXiv identifier?
- [ ] Has the publication venue and year been confirmed?
- [ ] Does the cited paper contain the exact lemma or theorem referenced?
- [ ] Are historical priority attributions correct (e.g., Cook-Levin, Baker-Gill-Solovay, Razborov-Rudich)?
- [ ] Are BibTeX keys standardized (`authorYearKeyword`, e.g., `Bombieri2000Riemann`)?

---

## 3. Integrating with AXIOM Research Dossiers

In research reports (such as `reports/p-vs-np/REPORT.md` or `reports/riemann-hypothesis/REPORT.md`), maintain an explicit sources manifest containing:
```markdown
### Primary References
- **Cook, S. A. (1971)**. *The complexity of theorem-proving procedures*. Proc. 3rd ACM STOC, pp. 151–158. DOI: 10.1145/800157.805047.
- **Baker, T., Gill, J., & Solovay, R. (1975)**. *Relativizations of the P =? NP question*. SIAM J. Comput., 4(4), 431–442. DOI: 10.1137/0204037.
- **Razborov, A. A., & Rudich, S. (1997)**. *Natural proofs*. J. Comput. Syst. Sci., 55(1), 24–35. DOI: 10.1006/jcss.1997.1494.
```
