---
name: axiom-property-based-testing
description: Guide AI agents on formulating algebraic property-based tests, generating dense stochastic inputs, testing mathematical invariants, and finding counterexamples using AXIOM's verification tools.
---

# Property-Based Testing & Counterexample Search

Use this skill when testing mathematical transformations, algorithms, or equations across large parameter spaces to uncover edge cases and boundary counterexamples.

---

## 1. Principles of Mathematical Property-Based Testing

Unlike unit tests with fixed numbers (e.g. testing with $x=2$), property-based testing defines **invariants that must hold for all inputs in a domain**:

1. **Algebraic Invariants**:
   - Commutativity: $f(a, b) = f(b, a)$
   - Associativity: $f(f(a, b), c) = f(a, f(b, c))$
   - Distributivity: $a \cdot (b + c) = a \cdot b + a \cdot c$
   - Identity: $f(x, e) = x$
   - Idempotence: $f(f(x)) = f(x)$
2. **Boundary & Singularity Probing**:
   - Zero boundaries: $x \to 0^+$, $x \to 0^-$
   - Infinities: $x \to \infty$, $x \to -\infty$
   - Branch cuts: negative inputs for $\sqrt{x}$, $\ln(x)$, fractional powers $x^{1/3}$
   - Poles and resonant frequencies.

---

## 2. Using AXIOM for Property-Based Verification

AXIOM's `math_compare` and `math_verify` tools combine symbolic reduction with randomized multi-point sampling:

### Testing Commutativity of an Algebraic Operator
```bash
axiom compare "x * y" "y * x"
```

### Probing Branch-Cut Sensitivity
```bash
# Test if sqrt(x^2) = x holds universally
axiom compare "sqrt(x^2)" "x"
# Returns: disproven with counterexample x = -1

# Test with explicit domain assumption
axiom compare "sqrt(x^2)" "x" --assumptions "x:positive"
# Returns: proven (equivalent)
```

### Probing Polynomial Identities Across Complex Slices
```bash
axiom compare "(x + 1)^4" "x^4 + 4*x^3 + 6*x^2 + 4*x + 1"
# Returns: proven (symbolic identity confirmed)
```

---

## 3. Automation Protocol for Agents

When implementing new solvers or verifiers in AXIOM:
1. Define the universal property: $\forall x \in D, P(x) = Q(x)$.
2. Call `math_compare(left="P(x)", right="Q(x)", assumptions=domain)`
3. If `status == "disproven"`, extract `counterexample = res.verification.data["counterexample"]`.
4. Add the discovered counterexample to the test suite as a permanent regression test in `tests/test_adversarial.py`.
