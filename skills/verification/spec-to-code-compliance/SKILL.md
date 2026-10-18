---
name: axiom-spec-to-code-compliance
description: Guide AI agents on ensuring mathematical implementations and solvers strictly satisfy their formal specification contracts, verifying preconditions, postconditions, and invariant guarantees.
---

# Specification-to-Code Compliance

Use this skill when auditing or implementing algorithms in AXIOM to ensure code strictly adheres to its mathematical specification without semantic shortcuts or behavioral drift.

---

## 1. Specification Soundness Principles

Every mathematical function in AXIOM is governed by a formal behavioral contract:

1. **Precondition Gating**: Inputs must be checked for domain validity before AST transformation (e.g. non-empty expressions, valid syntax delimiters, authorized directory paths).
2. **Invariant Preservation**: Algebraic simplifications must produce expressions that evaluate identically on all admissible points:
   $$\forall x \in \text{Domain}, \quad f_{\text{simplified}}(x) = f_{\text{original}}(x)$$
3. **Postcondition Integrity**:
   - If `ok == True` and `verified == True`, `verification.passed` MUST be `True`.
   - If `status == "proven"`, `equivalent` MUST be `True` and `guarantee` must be `exact-symbolic` or `formal-proof`.
   - If `status == "inconclusive"`, `guarantee` MUST be `unverified`.
4. **No Lexical Shortcuts**: An engine or auditor must never declare two statements equivalent based on string matching or keyword overlap.

---

## 2. Compliance Checklist for Code Audits

When reviewing or adding code to `src/axiom/`:

- [ ] **Contract Invariant**: Does `MathResult.__post_init__` validate that `verified == (verification is not None and verification.passed)`?
- [ ] **Path Sandboxing**: Do all file operations pass through `validate_mcp_path()` to prevent traversal outside authorized project/temp directories?
- [ ] **Environment Isolation**: Does external engine execution (Lean, Julia) scrub sensitive environment keys (`OPENAI_API_KEY`, `GITHUB_TOKEN`, etc.)?
- [ ] **Resource Limits**: Are memory limits (`-M 2048`) and execution timeouts enforced on all subprocesses?
- [ ] **DAG Soundness**: In multi-step sessions, is step validity separated from dependency chain validity?
- [ ] **Import Distrust**: Are imported session JSON files treated as unauthenticated until locally re-executed?

---

## 3. Automated Compliance Testing

Run the full adversarial regression suite to verify compliance:

```bash
# Run 10 use cases demonstrating compliant contracts
python -m pytest tests/test_use_cases.py -v

# Run 9 adversarial tests without mocks
python -m pytest tests/test_adversarial.py -v
```
