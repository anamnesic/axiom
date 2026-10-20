# Contributing to Chronokairo AXIOM

Thank you for your interest in contributing to **AXIOM — Mathematical Reasoning Engine**.

AXIOM is built for AI agents and human mathematicians who require verifiable computational certainty. Our core invariant is **honesty and fail-closed verification**: we prefer an explicit `unverified` result over a plausible but hallucinated mathematical claim.

---

## 1. Development Principles & Code Standards

1. **Fail-Closed by Design**:
   - Every verifier must default to `passed=False` and `Guarantee.UNVERIFIED` unless independent symbolic or kernel evidence proves otherwise.
   - Never convert coincidental string matches or heuristic proximity into `verified` status.
2. **Zero Mocks in the Critical Verification Path**:
   - Tests in `tests/test_adversarial.py` and `tests/test_tamper_detection.py` must run against the real engine adapters and AST parser without monkey-patching verification outcomes.
3. **Four Epistemic States**:
   - Respect the separation among **Proof**, **Approximation**, **Refutation**, and **Inconclusive** ([ADR-0017](docs/adr/0017-four-epistemic-states-and-soundness-governance.md)).
4. **Architecture Decision Records (ADRs)**:
   - Any architectural change, guarantee modification, or new engine integration must be documented with a new ADR in `docs/adr/`.

---

## 2. Local Setup

Clone the repository and install with development dependencies:

```bash
git clone https://github.com/chronokairo/axiom.git
cd axiom
python -m pip install -e ".[dev]"
```

Run the built-in diagnostics tool:

```bash
axiom doctor
```

---

## 3. Running the Test Suite

Before submitting a Pull Request, verify that all test suites pass:

```bash
# 1. Full pytest suite
python -m pytest -v

# 2. Adversarial soundness tests (no mocks)
python -m pytest tests/test_adversarial.py -v

# 3. Tamper detection tests
python -m pytest tests/test_tamper_detection.py -v

# 4. Use cases integration tests
python -m pytest tests/test_use_cases.py -v

# 5. Millennium Research Bench (all 7 suites)
python benchmarks/millennium/run_millennium_bench.py
```

If you have Lean 4 and Lake installed, you can also run the formal integration tests:

```bash
python -m pytest tests/test_axiom.py -k "lean"
```

---

## 4. Pull Request Checklist

When submitting a pull request, ensure:

- [ ] New functionality includes tests in `tests/`.
- [ ] If changing a verifier, include negative controls and adversarial boundary cases.
- [ ] No regression in the 0.0% false-positive rate across benchmarks.
- [ ] Preserved all existing docstrings, type annotations, and comments.
- [ ] Documented any interface or contract change in `docs/adr/` and updated `docs/use-cases.md`.
