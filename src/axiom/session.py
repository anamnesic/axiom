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

    def record(
        self,
        result: MathResult,
        *,
        note: str = "",
        depends_on: list[int] | None = None,
    ) -> int:
        """Append a :class:`MathResult` to the session and return its step index."""
        idx = len(self.entries) + 1
        item = result.to_dict()
        if note:
            item["note"] = note
        item["step_index"] = idx

        # Item 4: Step validity tracked separately from dependency chain validity
        step_valid = bool(result.ok and result.verified)
        step_guar_str = item.get("guarantee", Guarantee.UNVERIFIED.value)
        try:
            step_guar = Guarantee(step_guar_str)
        except ValueError:
            step_guar = Guarantee.UNVERIFIED

        # Resolve explicit or default dependencies
        if depends_on is None:
            deps = [idx - 1] if idx > 1 else []
        else:
            deps = [int(d) for d in depends_on if int(d) != idx]

        broken_deps: list[int] = []
        chain_guar = step_guar if step_valid else Guarantee.UNVERIFIED

        for d_idx in deps:
            if d_idx <= 0 or d_idx >= idx or d_idx > len(self.entries):
                broken_deps.append(d_idx)
                continue
            prev_entry = self.entries[d_idx - 1]
            if not prev_entry.get("step_valid", False) or not prev_entry.get("chain_valid", False):
                broken_deps.append(d_idx)
            prev_cg = prev_entry.get("chain_guarantee", Guarantee.UNVERIFIED.value)
            try:
                g = Guarantee(prev_cg)
            except ValueError:
                g = Guarantee.UNVERIFIED
            chain_guar = chain_guar.weakest(g)

        chain_valid = step_valid and len(broken_deps) == 0
        if not chain_valid:
            chain_guar = Guarantee.UNVERIFIED

        item["depends_on"] = deps
        item["step_valid"] = step_valid
        item["step_guarantee"] = step_guar.value
        item["chain_valid"] = chain_valid
        item["chain_guarantee"] = chain_guar.value
        item["broken_dependencies"] = broken_deps
        item["imported"] = False
        item["revalidated"] = True

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
    def all_steps_valid(self) -> bool:
        """True if every step individually is locally valid and verified."""
        if not self.entries:
            return False
        return all(entry.get("step_valid", False) for entry in self.entries)

    @property
    def chain_valid(self) -> bool:
        """True if the entire dependency chain is unbroken and valid."""
        if not self.entries:
            return False
        return all(entry.get("chain_valid", False) for entry in self.entries)

    @property
    def step_validity(self) -> dict[str, Any]:
        """Summary of isolated per-step validity."""
        valid_steps = [e["step_index"] for e in self.entries if e.get("step_valid", False)]
        invalid_steps = [e["step_index"] for e in self.entries if not e.get("step_valid", False)]
        return {
            "all_steps_valid": self.all_steps_valid,
            "valid_steps": valid_steps,
            "invalid_steps": invalid_steps,
            "valid_count": len(valid_steps),
            "total_count": len(self.entries),
        }

    @property
    def dependency_chain_validity(self) -> dict[str, Any]:
        """Summary of dependency chain validity across all derivation steps."""
        broken_steps = [
            e["step_index"] for e in self.entries if not e.get("chain_valid", False)
        ]
        return {
            "chain_valid": self.chain_valid,
            "chain_guarantee": self.chain_guarantee.value,
            "broken_steps": broken_steps,
            "unbroken_count": len(self.entries) - len(broken_steps),
            "total_count": len(self.entries),
        }

    @property
    def chain_guarantee(self) -> Guarantee:
        """Weakest guarantee across all steps and their dependency chains."""
        if not self.entries:
            return Guarantee.UNVERIFIED
        current = Guarantee.FORMAL_PROOF
        for entry in self.entries:
            if not entry.get("ok", False):
                return Guarantee.UNVERIFIED
            g_str = entry.get("chain_guarantee", entry.get("guarantee", Guarantee.UNVERIFIED.value))
            try:
                g = Guarantee(g_str)
            except ValueError:
                g = Guarantee.UNVERIFIED
            # Item 3: Imported/cached results never get formal-proof without revalidation
            if g == Guarantee.FORMAL_PROOF and entry.get("imported") and not entry.get("revalidated", False):
                g = Guarantee.UNVERIFIED
            current = current.weakest(g)
        return current

    def _recompute_chain_states(self) -> None:
        """Recompute chain validity and chain guarantees across all entries in topological order."""
        for idx, entry in enumerate(self.entries, start=1):
            entry["step_index"] = idx
            step_valid = bool(entry.get("step_valid", False))
            step_guar_str = entry.get("step_guarantee") or entry.get("guarantee", Guarantee.UNVERIFIED.value)
            try:
                step_guar = Guarantee(step_guar_str)
            except ValueError:
                step_guar = Guarantee.UNVERIFIED

            if entry.get("imported") and not entry.get("revalidated", False) and step_guar == Guarantee.FORMAL_PROOF:
                step_guar = Guarantee.UNVERIFIED
                entry["step_guarantee"] = Guarantee.UNVERIFIED.value

            deps = entry.get("depends_on", [])
            broken: list[int] = []
            cg = step_guar if step_valid else Guarantee.UNVERIFIED

            for d in deps:
                if d <= 0 or d >= idx or d > len(self.entries):
                    broken.append(d)
                else:
                    prev = self.entries[d - 1]
                    if not prev.get("step_valid", False) or not prev.get("chain_valid", False):
                        broken.append(d)
                    else:
                        try:
                            prev_cg = Guarantee(prev.get("chain_guarantee", Guarantee.UNVERIFIED.value))
                            cg = cg.weakest(prev_cg)
                        except ValueError:
                            cg = Guarantee.UNVERIFIED

            chain_valid = step_valid and len(broken) == 0
            entry["broken_dependencies"] = broken
            entry["chain_valid"] = chain_valid
            entry["chain_guarantee"] = cg.value if chain_valid else Guarantee.UNVERIFIED.value

    def revalidate_step(self, step_idx: int, axiom: Any = None) -> bool:
        """Revalidate an imported or cached step on the current host."""
        if step_idx <= 0 or step_idx > len(self.entries):
            return False
        entry = self.entries[step_idx - 1]
        if axiom is None:
            from axiom.core import Axiom
            axiom = Axiom()
        res = axiom.verify(entry)
        step_valid = bool(res.ok and res.verified)
        entry["step_valid"] = step_valid
        entry["step_guarantee"] = res.guarantee.value
        entry["revalidated"] = True
        self._recompute_chain_states()
        return step_valid

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "created_at": self.created_at,
            "steps_count": len(self.entries),
            "step_validity": self.step_validity,
            "dependency_chain_validity": self.dependency_chain_validity,
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
            f"- **Step Validity:** {self.step_validity['valid_count']}/{len(self.entries)} valid (`all_valid={self.all_steps_valid}`)",
            f"- **Dependency Chain Validity:** {'VALID' if self.chain_valid else 'BROKEN'}",
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
                step_val = "VALID" if entry.get("step_valid", False) else "INVALID"
                chain_val = "UNBROKEN" if entry.get("chain_valid", False) else "BROKEN"
                ver = entry.get("verification") or {}
                ev = entry.get("evidence") or {}
                lines.append(f"### Step {step}: `{kind}` — `{inp}`")
                if entry.get("note"):
                    lines.append(f"- **Note:** {entry['note']}")
                lines.append(f"- **Result:** `{val}`")
                lines.append(f"- **Step Validity:** `{step_val}` (Step Guarantee: `{entry.get('step_guarantee', guar)}`)")
                lines.append(f"- **Chain Validity:** `{chain_val}` (Chain Guarantee: `{entry.get('chain_guarantee', guar)}`)")
                if entry.get("depends_on"):
                    lines.append(f"- **Depends On:** {entry['depends_on']}")
                if entry.get("broken_dependencies"):
                    lines.append(f"- **Broken Dependencies:** {entry['broken_dependencies']}")
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
        entries = list(data.get("entries", []))
        for e in entries:
            e["imported"] = True
            is_reval = bool(e.get("revalidated_locally", False))
            e["revalidated"] = is_reval
            if not is_reval:
                if e.get("guarantee") == Guarantee.FORMAL_PROOF.value:
                    e["unverified_claimed_guarantee"] = Guarantee.FORMAL_PROOF.value
                    e["guarantee"] = Guarantee.UNVERIFIED.value
                if e.get("step_guarantee") == Guarantee.FORMAL_PROOF.value:
                    e["step_guarantee"] = Guarantee.UNVERIFIED.value
                if e.get("chain_guarantee") == Guarantee.FORMAL_PROOF.value:
                    e["chain_guarantee"] = Guarantee.UNVERIFIED.value
        session = cls(
            name=data.get("name", name),
            created_at=data.get("created_at", ""),
            entries=entries,
            hypotheses=[
                Hypothesis(**h) for h in data.get("hypotheses", [])
            ],
        )
        session._recompute_chain_states()
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
                f"step_validity={self.step_validity['valid_count']}/{len(self.entries)}, "
                f"chain_valid={self.chain_valid}, "
                f"chain_guarantee={self.chain_guarantee.value}"
            ),
            guarantee=self.chain_guarantee,
            evidence=Evidence(
                engine="axiom-session",
                engine_version="0.1.0",
                method="weakest-link derivation chain tracking with step/chain validity separation",
                reproducible_with=f"axiom session show --name {self.name}",
            ),
            verification=Verification(
                kind="chain-audit",
                passed=self.chain_valid and self.chain_guarantee != Guarantee.UNVERIFIED,
                detail=(
                    f"Step validity: {self.step_validity['valid_count']}/{len(self.entries)} valid; "
                    f"Chain validity: {'UNBROKEN' if self.chain_valid else 'BROKEN'}; "
                    f"Weakest link is {self.chain_guarantee.value}"
                ),
                checks=len(self.entries),
                data={
                    "step_validity": self.step_validity,
                    "dependency_chain_validity": self.dependency_chain_validity,
                    "chain_valid": self.chain_valid,
                    "chain_guarantee": self.chain_guarantee.value,
                },
            ),
        )

