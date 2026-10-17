"""Reproducible mathematical investigation sessions and snapshots.

Allows agents and researchers to chain multiple computations, track conjectures,
compute the weakest-link guarantee of a multi-step derivation, and export a
complete Markdown or JSON audit trail.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from axiom.contract import Evidence, Guarantee, MathResult, Verification


@dataclass
class Hypothesis:
    """A mathematical conjecture or claim tracked during a research session."""

    statement: str
    status: str = "open"  # "open", "verified", "refuted", "plausible"
    guarantee: str = Guarantee.UNVERIFIED.value
    detail: str = ""


@dataclass
class ResearchSession:
    """Persistent or in-memory log of verified mathematical steps and conjectures."""

    name: str = "default"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    entries: list[dict[str, Any]] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)

    def record(self, result: MathResult, *, note: str = "") -> int:
        """Append a :class:`MathResult` to the session and return its step index."""
        idx = len(self.entries) + 1
        item = result.to_dict()
        if note:
            item["note"] = note
        item["step_index"] = idx
        self.entries.append(item)
        return idx

    def add_hypothesis(
        self,
        statement: str,
        *,
        status: str = "open",
        guarantee: Guarantee = Guarantee.UNVERIFIED,
        detail: str = "",
    ) -> Hypothesis:
        hyp = Hypothesis(
            statement=statement,
            status=status,
            guarantee=guarantee.value,
            detail=detail,
        )
        self.hypotheses.append(hyp)
        return hyp

    @property
    def chain_guarantee(self) -> Guarantee:
        """Weakest guarantee across all recorded steps (logical chain strength)."""
        if not self.entries:
            return Guarantee.UNVERIFIED
        current = Guarantee.FORMAL_PROOF
        for entry in self.entries:
            if not entry.get("ok", False):
                return Guarantee.UNVERIFIED
            g_str = entry.get("guarantee", Guarantee.UNVERIFIED.value)
            try:
                g = Guarantee(g_str)
            except ValueError:
                g = Guarantee.UNVERIFIED
            current = current.weakest(g)
        return current

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "created_at": self.created_at,
            "steps_count": len(self.entries),
            "chain_guarantee": self.chain_guarantee.value,
            "hypotheses": [asdict(h) for h in self.hypotheses],
            "entries": self.entries,
        }

    def to_markdown(self) -> str:
        """Render a reproducible Markdown research report."""
        lines = [
            f"# AXIOM Research Session: `{self.name}`",
            "",
            f"- **Created:** {self.created_at}",
            f"- **Steps:** {len(self.entries)}",
            f"- **Chain Guarantee (weakest link):** `{self.chain_guarantee.value}`",
            "",
        ]
        if self.hypotheses:
            lines.append("## Hypotheses & Conjectures")
            lines.append("")
            lines.append("| # | Statement | Status | Guarantee | Detail |")
            lines.append("| --- | --- | --- | --- | --- |")
            for idx, h in enumerate(self.hypotheses, start=1):
                lines.append(
                    f"| {idx} | `{h.statement}` | **{h.status.upper()}** | `{h.guarantee}` | {h.detail} |"
                )
            lines.append("")

        if self.entries:
            lines.append("## Derivation & Evidence Log")
            lines.append("")
            for entry in self.entries:
                step = entry.get("step_index", "?")
                kind = entry.get("kind", "step")
                inp = entry.get("input", "")
                val = entry.get("value_str", "")
                guar = entry.get("guarantee", "unverified")
                ver = entry.get("verification") or {}
                ev = entry.get("evidence") or {}
                lines.append(f"### Step {step}: `{kind}` — `{inp}`")
                if entry.get("note"):
                    lines.append(f"- **Note:** {entry['note']}")
                lines.append(f"- **Result:** `{val}`")
                lines.append(f"- **Guarantee:** `{guar}`")
                if ver:
                    status = "PASSED" if ver.get("passed") else "FAILED"
                    lines.append(
                        f"- **Verification:** `{ver.get('kind')}` ({status}) — {ver.get('detail', '')}"
                    )
                if ev.get("reproducible_with"):
                    lines.append(f"- **Reproduce:** `{ev['reproducible_with']}`")
                lines.append("")

        return "\n".join(lines)

    def save(self, directory: Path | str = ".axiom/sessions") -> Path:
        folder = Path(directory)
        folder.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in self.name)
        path = folder / f"{safe_name}.json"
        path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return path

    @classmethod
    def load(
        cls, name: str = "default", directory: Path | str = ".axiom/sessions"
    ) -> "ResearchSession":
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        path = Path(directory) / f"{safe_name}.json"
        if not path.exists():
            return cls(name=name)
        data = json.loads(path.read_text(encoding="utf-8"))
        session = cls(
            name=data.get("name", name),
            created_at=data.get("created_at", ""),
            entries=list(data.get("entries", [])),
            hypotheses=[
                Hypothesis(**h) for h in data.get("hypotheses", [])
            ],
        )
        return session

    def as_math_result(self, action: str) -> MathResult:
        payload = self.to_dict()
        return MathResult(
            kind="session",
            input=f"{self.name}:{action}",
            ok=True,
            value=payload,
            value_str=(
                f"session '{self.name}': {len(self.entries)} step(s), "
                f"{len(self.hypotheses)} hypothesis(es), "
                f"chain_guarantee={self.chain_guarantee.value}"
            ),
            guarantee=self.chain_guarantee,
            evidence=Evidence(
                engine="axiom-session",
                engine_version="0.1.0",
                method="weakest-link derivation chain tracking",
                reproducible_with=f"axiom session show --name {self.name}",
            ),
            verification=Verification(
                kind="chain-audit",
                passed=self.chain_guarantee != Guarantee.UNVERIFIED,
                detail=f"Weakest link across {len(self.entries)} recorded step(s) is {self.chain_guarantee.value}",
                checks=len(self.entries),
            ),
        )
