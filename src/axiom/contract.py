"""The AXIOM result contract.

Every computation returns a :class:`MathResult`. The contract makes three
things explicit that a bare answer hides:

1. **What** was computed (``value``/``value_str``/``latex``),
2. **How** it was computed (``Evidence``: engine, version, method, steps,
   limitations, and how to reproduce it),
3. **How strongly** the result is guaranteed (``Guarantee``) and whether an
   *independent* check was performed (``Verification``).

The guarantee level is the core idea of the project: a symbolic identity, a
numerically-checked approximation, and a machine-checked proof are not the
same kind of claim and must never be presented as if they were.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Guarantee(str, Enum):
    """Logical strength or epistemic classification of a result, from strongest to weakest."""

    # Mathematical correctness guarantees (require a passing independent Verification)
    FORMAL_PROOF = "formal-proof"
    EXACT_SYMBOLIC = "exact-symbolic"
    VERIFIED_SUBSTITUTION = "verified-substitution"
    NUMERICAL_APPROXIMATION = "numerical-approximation"

    # Operational / non-proof states (parsing, catalog lookup, plotting, heuristics)
    STRUCTURAL_PARSE = "structural-parse"
    CATALOG_LOOKUP = "catalog-lookup"
    SAMPLED_VISUALIZATION = "sampled-visualization"
    HEURISTIC = "heuristic"

    # Unverified, refuted, or failed verification
    UNVERIFIED = "unverified"

    @property
    def rank(self) -> int:
        """Higher is stronger. Useful to compare or downgrade claims."""
        return _GUARANTEE_RANK[self]

    @property
    def is_mathematical_claim(self) -> bool:
        """True only for guarantees representing a verified mathematical calculation or proof."""
        return self in (
            Guarantee.FORMAL_PROOF,
            Guarantee.EXACT_SYMBOLIC,
            Guarantee.VERIFIED_SUBSTITUTION,
            Guarantee.NUMERICAL_APPROXIMATION,
        )

    def at_least(self, other: "Guarantee") -> bool:
        return self.rank >= other.rank

    def weakest(self, other: "Guarantee") -> "Guarantee":
        return self if self.rank <= other.rank else other


class EpistemicState(str, Enum):
    """The four mutually exclusive epistemic states of mathematical reasoning."""

    PROOF = "proof"
    APPROXIMATION = "approximation"
    REFUTATION = "refutation"
    INCONCLUSIVE = "inconclusive"


# Verification kinds that carry *positive evidence of falsity*: each one
# records a structured witness (see :func:`has_refutation_evidence`) that
# decisively shows the checked claim to be false.
#
# A verification that merely *fails* is NOT a refutation. Checks such as
# ``constant-exact-inconclusive``, ``unevaluated-integral``,
# ``definite-integral-check``, ``inequality-check``,
# ``empty-solution-set``, ``system-empty-solution-set`` or
# ``substitution-indeterminate`` fail because the question could not be
# decided (or was out of scope), which is an INCONCLUSIVE outcome, not a
# mathematical disproof.
REFUTING_VERIFICATION_KINDS: frozenset[str] = frozenset(
    {
        "approximate-disproof",
        "assumption-violation",
        "constant-exact-disproof",
        "counterexample-search",
        "divergent-integral",
        "domain-mismatch",
        "interior-singularity-check",
        "numerical-quadrature",
        "substitution",
        "substitution-domain-error",
        "system-substitution",
    }
)

# Payload statuses that assert falsity.
REFUTING_STATUSES: frozenset[str] = frozenset({"disproven", "refuted"})


def has_refutation_evidence(
    verification: Verification | None, value: Any = None
) -> bool:
    """True when a verification carries positive evidence that a claim is false.

    A *failed* verification is not by itself a refutation: the check may have
    been undecidable, out of scope, or aborted by a parse/timeout error. Only
    a **structured witness** qualifies, so that ``REFUTATION`` is never used
    as a synonym for "the check did not succeed".

    The witness is one of:

    * a structured witness record (``verification.data["witness"]``) produced
      by the verifier: a machine-readable falsity certificate carrying the
      expression that was evaluated, the substitution point, and the observed
      value. Such a witness is *replayable* via
      :func:`axiom.verification.revalidate_witness`;
    * an explicit counterexample mapping recorded by the verifier
      (``verification.data["counterexample"]``) or carried by the result
      payload (``value["counterexample"]``).

    A prose sentence in ``Verification.detail`` is **not** admissible on its
    own: it is a human-readable summary of the witness, not the witness.
    """
    if verification is None or verification.passed:
        return False

    # Only a verification kind that is, by construction, a disproof may ever
    # carry a refutation; an undecidable check can never be promoted to one.
    if verification.kind not in REFUTING_VERIFICATION_KINDS:
        return False

    data = verification.data or {}
    witness = data.get("witness")
    if isinstance(witness, dict) and witness:
        return True
    if data.get("counterexample"):
        return True
    if isinstance(value, dict) and value.get("counterexample"):
        return True
    return False


def outcome_word(
    verification: Verification | None, value: Any = None
) -> str:
    """Classify a verification outcome as a single status word.

    * ``verified`` - the independent check passed;
    * ``refuted`` - the check produced positive evidence of falsity;
    * ``inconclusive`` - the check failed without deciding the question.
    """
    if verification is not None and verification.passed:
        return "verified"
    if has_refutation_evidence(verification, value):
        return "refuted"
    return "inconclusive"


_GUARANTEE_RANK = {
    Guarantee.FORMAL_PROOF: 5,
    Guarantee.EXACT_SYMBOLIC: 4,
    Guarantee.VERIFIED_SUBSTITUTION: 3,
    Guarantee.NUMERICAL_APPROXIMATION: 2,
    Guarantee.STRUCTURAL_PARSE: 1,
    Guarantee.CATALOG_LOOKUP: 1,
    Guarantee.SAMPLED_VISUALIZATION: 1,
    Guarantee.HEURISTIC: 1,
    Guarantee.UNVERIFIED: 0,
}


@dataclass
class Evidence:
    """Provenance of a computation: who computed it, how, and its limits."""

    engine: str
    engine_version: str = ""
    method: str = ""
    steps: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    reproducible_with: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v not in ("", None, [], {})}


@dataclass
class Verification:
    """Result of an *independent* check of a claim."""

    kind: str
    passed: bool
    detail: str = ""
    checks: int = 0
    max_error: float | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v not in ("", None, [], {})}


@dataclass
class MathResult:
    """A single, self-describing mathematical result."""

    kind: str
    input: str
    ok: bool = True
    value: Any = None
    value_str: str = ""
    latex: str | None = None
    variables: list[str] = field(default_factory=list)
    guarantee: Guarantee = Guarantee.UNVERIFIED
    evidence: Evidence | None = None
    verification: Verification | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    def __post_init__(self) -> None:
        """Enforce that no mathematical claim guarantee is granted without a passing Verification."""
        if self.guarantee.is_mathematical_claim and not (
            self.verification is not None and self.verification.passed
        ):
            raise ValueError(
                f"Guarantee {self.guarantee.value!r} is a mathematical correctness claim "
                "and requires a Verification object with passed=True"
            )

    # ---------------------------------------------------------------- helpers

    @property
    def verified(self) -> bool:
        """True when an independent verification actually passed."""
        return bool(self.verification and self.verification.passed)

    @property
    def has_refutation_evidence(self) -> bool:
        """True only when this result carries positive evidence that a claim is false.

        A *failed* verification is not by itself a refutation: the check may
        have been undecidable, out of scope, or aborted by a parse/timeout
        error. Only an explicit witness qualifies, so that ``REFUTATION`` is
        never used as a synonym for "the check did not succeed".

        The witness is one of:

        * an explicit counterexample/witness recorded by the verifier
          (``verification.data``);
        * a ``disproven``/``refuted`` status recorded by the verifier or
          carried by the result payload;
        * a verification kind that is, by construction, a disproof
          (:data:`REFUTING_VERIFICATION_KINDS`) with a non-empty detail
          describing the witness.
        """
        return has_refutation_evidence(self.verification, self.value)

    @property
    def outcome(self) -> str:
        """Single status word for this result: verified / refuted / inconclusive."""
        return outcome_word(self.verification, self.value)

    @property
    def epistemic_state(self) -> EpistemicState:
        """Categorize this result into one of the four foundational epistemic states."""
        # 1. Active refutation: requires positive evidence of falsity (a witness).
        if self.has_refutation_evidence:
            return EpistemicState.REFUTATION

        # 2. Certified proof (kernel-checked formal proof or exact symbolic derivation)
        if (
            self.guarantee
            in (
                Guarantee.FORMAL_PROOF,
                Guarantee.EXACT_SYMBOLIC,
                Guarantee.VERIFIED_SUBSTITUTION,
            )
            and self.verified
        ):
            return EpistemicState.PROOF

        # 3. Bounded numerical approximation
        if self.guarantee == Guarantee.NUMERICAL_APPROXIMATION:
            return EpistemicState.APPROXIMATION

        # 4. Fail-closed inconclusive
        return EpistemicState.INCONCLUSIVE

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "kind": self.kind,
            "input": self.input,
            "ok": self.ok,
            "epistemic_state": self.epistemic_state.value,
        }
        if self.ok:
            d["value"] = self.value
            d["value_str"] = self.value_str
            if self.latex:
                d["latex"] = self.latex
            if self.variables:
                d["variables"] = self.variables
        d["guarantee"] = self.guarantee.value
        if self.evidence:
            d["evidence"] = self.evidence.to_dict()
        if self.verification:
            d["verification"] = self.verification.to_dict()
        if self.warnings:
            d["warnings"] = self.warnings
        if self.error:
            d["error"] = self.error
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def render(self) -> str:
        """Human- and agent-readable rendering, REA-style evidence block."""
        lines: list[str] = []
        title = self.kind.replace("_", " ").title()
        lines.append(f"{title}: {self.input}")
        if not self.ok:
            lines.append(f"  ERROR: {self.error}")
            return "\n".join(lines)
        lines.append(f"  Result:    {self.value_str}")
        if self.latex:
            lines.append(f"  LaTeX:     {self.latex}")
        lines.append(f"  Guarantee: {self.guarantee.value.upper()}")
        if self.evidence:
            ev = self.evidence
            lines.append(f"  Engine:    {ev.engine} {ev.engine_version}".rstrip())
            if ev.method:
                lines.append(f"  Method:    {ev.method}")
            for step in ev.steps:
                lines.append(f"  Step:      {step}")
        if self.verification:
            v = self.verification
            status = "passed" if v.passed else "FAILED"
            lines.append(f"  Verified:  {v.kind} ({status}) — {v.detail}")
        for note in self.warnings:
            lines.append(f"  Warning:   {note}")
        if self.evidence and self.evidence.limitations:
            for lim in self.evidence.limitations:
                lines.append(f"  Limit:     {lim}")
        return "\n".join(lines)


def error_result(kind: str, expression: str, message: str, *,
                 engine: str | None = None, limitation: str | None = None
                 ) -> MathResult:
    """Build a failed result that still carries provenance."""
    evidence = Evidence(
        engine=engine or "axiom",
        limitations=[limitation] if limitation else [],
    )
    return MathResult(
        kind=kind,
        input=expression,
        ok=False,
        error=message,
        evidence=evidence,
        guarantee=Guarantee.UNVERIFIED,
    )
