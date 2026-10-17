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
    """Logical strength of a result, from strongest to weakest."""

    FORMAL_PROOF = "formal-proof"
    EXACT_SYMBOLIC = "exact-symbolic"
    VERIFIED_SUBSTITUTION = "verified-substitution"
    NUMERICAL_APPROXIMATION = "numerical-approximation"
    HEURISTIC = "heuristic"
    UNVERIFIED = "unverified"

    @property
    def rank(self) -> int:
        """Higher is stronger. Useful to compare or downgrade claims."""
        return _GUARANTEE_RANK[self]

    def at_least(self, other: "Guarantee") -> bool:
        return self.rank >= other.rank

    def weakest(self, other: "Guarantee") -> "Guarantee":
        return self if self.rank <= other.rank else other


_GUARANTEE_RANK = {
    Guarantee.FORMAL_PROOF: 5,
    Guarantee.EXACT_SYMBOLIC: 4,
    Guarantee.VERIFIED_SUBSTITUTION: 3,
    Guarantee.NUMERICAL_APPROXIMATION: 2,
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

    # ---------------------------------------------------------------- helpers

    @property
    def verified(self) -> bool:
        """True when an independent verification actually passed."""
        return bool(self.verification and self.verification.passed)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "kind": self.kind,
            "input": self.input,
            "ok": self.ok,
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
