"""AXIOM Mathematical Investigation Layer (v0.3.0).

Implements the eight high-level investigation primitives defined by
[ADR-0019](docs/adr/0019-mathematical-investigation-layer-rea-paradigm.md),
porting the REA ("Reverse Engineer Anything") paradigm to mathematics.

A *CAS* answers a question. An *investigation* pursues a claim: it formalises
the claim, decomposes it, tracks the lemmas it depends on, hunts for
counterexamples, compares proof routes, catalogues what remains unknown, and
exports a reproducible dossier of evidence.

The layer is deliberately **fail-closed**: an investigation never promotes an
undecided claim to a proof. Every node of the proof dependency graph keeps its
own guarantee, and the dossier records the *structural* integrity of the graph
separately from any *demonstrated logical implication* (which a dependency
list alone never establishes).

Dossier layout (``.axiom/investigations/<id>/``)::

    spec.json       formalised target statement and domain scope
    graph.json      Proof Dependency Graph with audited nodes and edges
    unknowns.json   Unknown Ledger (gaps, pending hypotheses, unproved steps)
    evidence/       per-step evidence artifacts
    bundle.json     atomic provenance package (SHA-256 digests)
    REPORT.md       reproducible dossier report
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import secrets
from typing import Any

from axiom.contract import (
    EpistemicState,
    Evidence,
    Guarantee,
    MathResult,
    error_result,
)
from axiom.core import Axiom
from axiom.parsing import ParseError, Parser

#: Root directory (relative to the workspace) holding every investigation.
INVESTIGATION_ROOT = ".axiom/investigations"

#: Node kinds used in the proof dependency graph.
NODE_CLAIM = "claim"
NODE_LEMMA = "lemma"
NODE_ASSUMPTION = "assumption"
NODE_OBLIGATION = "obligation"

#: Statuses a graph node may carry.
STATUS_PROVEN = "proven"
STATUS_CANDIDATE = "candidate"
STATUS_REFUTED = "refuted"
STATUS_OPEN = "open"

_LEAN_THEOREM_RE = re.compile(r"^\s*(theorem|lemma|example)\b", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_name(name: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return cleaned.strip("_") or "default"


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return path


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _split_equality(text: str) -> tuple[str, str] | None:
    """Split a top-level ``==`` / ``=`` into its two sides.

    Parenthesised and bracketed sub-expressions are respected, and a single
    ``=`` that is part of ``==``, ``>=``, ``<=`` or ``!=`` is ignored.
    """
    depth = 0
    for i, ch in enumerate(text):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "=" and depth == 0:
            prev = text[i - 1] if i else ""
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if prev in ("<", ">", "!", "=") or nxt == "=":
                continue
            left, right = text[:i].strip(), text[i + 1 :].strip()
            if left and right:
                return left, right
            return None
    return None


def _engine_versions(ax: Axiom) -> dict[str, str]:
    versions: dict[str, str] = {}
    try:
        import sympy as sp

        versions["sympy"] = sp.__version__
    except Exception:
        versions["sympy"] = "unavailable"
    try:
        import mpmath as mp

        versions["mpmath"] = mp.__version__
    except Exception:
        versions["mpmath"] = "unavailable"
    try:
        lean = ax.registry.get("lean")
        versions["lean"] = getattr(lean, "version", "") or ("available" if lean.available else "unavailable")
    except Exception:
        versions["lean"] = "unavailable"
    return versions


# --------------------------------------------------------------------------- #
# The dossier
# --------------------------------------------------------------------------- #


class Investigation:
    """A persistent mathematical investigation dossier.

    The dossier is a directory on disk; every mutation is written through
    immediately so that a crashed agent leaves a readable, auditable trail.
    """

    def __init__(self, root: Path | str, investigation_id: str) -> None:
        self.root = Path(root)
        self.investigation_id = investigation_id
        self.dir = self.root / _safe_name(investigation_id)
        self.evidence_dir = self.dir / "evidence"

    # ------------------------------------------------------------ filesystem

    @property
    def spec_path(self) -> Path:
        return self.dir / "spec.json"

    @property
    def graph_path(self) -> Path:
        return self.dir / "graph.json"

    @property
    def unknowns_path(self) -> Path:
        return self.dir / "unknowns.json"

    @property
    def bundle_path(self) -> Path:
        return self.dir / "bundle.json"

    @property
    def report_path(self) -> Path:
        return self.dir / "REPORT.md"

    def exists(self) -> bool:
        return self.spec_path.exists()

    # ----------------------------------------------------------------- state

    def read_spec(self) -> dict[str, Any]:
        if not self.spec_path.exists():
            return {}
        return _read_json(self.spec_path)

    def write_spec(self, spec: dict[str, Any]) -> None:
        _write_json(self.spec_path, spec)

    def read_graph(self) -> dict[str, Any]:
        if not self.graph_path.exists():
            return {"nodes": [], "edges": []}
        return _read_json(self.graph_path)

    def write_graph(self, graph: dict[str, Any]) -> None:
        _write_json(self.graph_path, graph)

    def read_unknowns(self) -> dict[str, Any]:
        if not self.unknowns_path.exists():
            return {"unknowns": []}
        return _read_json(self.unknowns_path)

    def write_unknowns(self, unknowns: dict[str, Any]) -> None:
        _write_json(self.unknowns_path, unknowns)

    def write_evidence(self, name: str, payload: Any) -> Path:
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        return _write_json(self.evidence_dir / f"{_safe_name(name)}.json", payload)

    def list_ids(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(
            p.name
            for p in self.root.iterdir()
            if p.is_dir() and (p / "spec.json").exists()
        )

    # ------------------------------------------------------------- the graph

    def upsert_node(self, node: dict[str, Any]) -> None:
        graph = self.read_graph()
        nodes = graph.setdefault("nodes", [])
        for existing in nodes:
            if existing["id"] == node["id"]:
                existing.update(node)
                break
        else:
            nodes.append(node)
        graph["edges"] = _rebuild_edges(nodes)
        graph["dag_structural_integrity"] = _structural_integrity(nodes)
        graph["logical_implication_proven"] = False
        graph["cycles"] = _find_cycles(nodes)
        self.write_graph(graph)

    def find_node(self, statement: str) -> dict[str, Any] | None:
        for node in self.read_graph().get("nodes", []):
            if node.get("statement") == statement:
                return node
        return None

    def add_unknown(self, entry: dict[str, Any]) -> None:
        unknowns = self.read_unknowns()
        items = unknowns.setdefault("unknowns", [])
        for existing in items:
            if existing.get("id") == entry.get("id"):
                existing.update(entry)
                break
        else:
            items.append(entry)
        unknowns["count"] = len(items)
        unknowns["updated_at"] = _now()
        self.write_unknowns(unknowns)


def _rebuild_edges(nodes: list[dict[str, Any]]) -> list[dict[str, str]]:
    known = {n["id"] for n in nodes}
    edges: list[dict[str, str]] = []
    for node in nodes:
        for dep in node.get("depends_on", []):
            if dep in known and dep != node["id"]:
                edges.append({"from": dep, "to": node["id"], "kind": "depends-on"})
    return edges


def _structural_integrity(nodes: list[dict[str, Any]]) -> bool:
    """True when the dependency graph is a well-formed DAG.

    This certifies *structure* only (no dangling edges, no cycles). It never
    certifies that a dependency implies its dependant.
    """
    known = {n["id"] for n in nodes}
    for node in nodes:
        for dep in node.get("depends_on", []):
            if dep not in known or dep == node["id"]:
                return False
    return not _find_cycles(nodes)


def _find_cycles(nodes: list[dict[str, Any]]) -> list[list[str]]:
    """Return the elementary cycles of the dependency graph (empty if acyclic)."""
    graph = {n["id"]: list(n.get("depends_on", [])) for n in nodes}
    cycles: list[list[str]] = []
    state: dict[str, int] = {}

    def visit(node: str, stack: list[str]) -> None:
        state[node] = 1
        stack.append(node)
        for dep in graph.get(node, []):
            if dep not in graph:
                continue
            if state.get(dep, 0) == 1:
                idx = stack.index(dep)
                cycles.append(stack[idx:] + [dep])
            elif state.get(dep, 0) == 0:
                visit(dep, stack)
        stack.pop()
        state[node] = 2

    for node in list(graph):
        if state.get(node, 0) == 0:
            visit(node, [])
    return cycles


# --------------------------------------------------------------------------- #
# Claim analysis
# --------------------------------------------------------------------------- #


def _analyze(ax: Axiom, statement: str) -> dict[str, Any]:
    """Decompose a claim into variables, hypotheses and boundary conditions."""
    analysis: dict[str, Any] = {
        "statement": statement,
        "parse_ok": False,
        "variables": [],
        "hypotheses": [],
        "domain_constraints": [],
        "excluded_points": {},
        "boundary_conditions": [],
        "has_inexact_floats": False,
        "interpretation": "unparsed",
        "error": None,
    }
    try:
        parser = Parser()
        pair = _split_equality(statement)
        if pair is not None:
            left, right = pair
            analysis["interpretation"] = "identity"
            parser.parse_expression(left)
            parser.parse_expression(right)
        else:
            analysis["interpretation"] = "equation"
            parser.parse_equation(statement)
        analysis["parse_ok"] = True
    except ParseError as exc:
        analysis["error"] = str(exc)
        return analysis
    except Exception as exc:  # pragma: no cover - defensive
        analysis["error"] = f"unexpected parse failure: {exc}"
        return analysis

    symbols = sorted(parser.seen_symbols, key=str)
    domain = parser.domain_info(symbols)
    analysis["variables"] = [str(s) for s in symbols]
    analysis["domain_constraints"] = list(domain.get("domain_constraints") or [])
    analysis["excluded_points"] = dict(domain.get("excluded_points") or {})
    analysis["has_inexact_floats"] = bool(domain.get("has_inexact_floats"))
    for var, assumptions in (parser.symbol_assumptions or {}).items():
        for key, value in (assumptions or {}).items():
            analysis["hypotheses"].append(
                {"source": "explicit", "symbol": str(var), "kind": str(key), "value": value}
            )
    for constraint in analysis["domain_constraints"]:
        analysis["hypotheses"].append(
            {"source": "implicit", "symbol": None, "kind": "domain-constraint", "value": constraint}
        )
    for var, points in (analysis["excluded_points"] or {}).items():
        for point in points:
            analysis["boundary_conditions"].append(
                {"symbol": str(var), "kind": "excluded-point", "value": str(point)}
            )
    if analysis["has_inexact_floats"]:
        analysis["boundary_conditions"].append(
            {"symbol": None, "kind": "inexact-float", "value": "float inputs cannot certify exact identities"}
        )
    return analysis


def _classify(ax: Axiom, statement: str, mode: str = "identity") -> dict[str, Any]:
    """Determine the epistemic status of a single statement.

    The result is deliberately honest: a statement that cannot be decided is
    reported as ``open``/``inconclusive``, never as proven.
    """
    info: dict[str, Any] = {
        "statement": statement,
        "status": STATUS_OPEN,
        "guarantee": Guarantee.UNVERIFIED.value,
        "method": "none",
        "detail": "not evaluated",
        "counterexample": None,
        "witness": None,
        "epistemic_state": EpistemicState.INCONCLUSIVE.value,
    }

    if _LEAN_THEOREM_RE.match(statement) and ":=" in statement:
        res = ax.prove(statement, engine="lean")
        info["method"] = "lean4-kernel"
        info["guarantee"] = res.guarantee.value
        info["detail"] = (
            res.verification.detail if res.verification else (res.error or "no verification")
        )
        info["epistemic_state"] = res.epistemic_state.value
        if res.guarantee == Guarantee.FORMAL_PROOF and res.verified:
            info["status"] = STATUS_PROVEN
        elif res.epistemic_state == EpistemicState.REFUTATION:
            info["status"] = STATUS_REFUTED
        return info

    pair = _split_equality(statement)
    if mode == "equation" or pair is None:
        res = ax.verify(statement)
        info["method"] = "exact-substitution"
        info["guarantee"] = res.guarantee.value
        info["detail"] = (
            res.verification.detail if res.verification else (res.error or "no verification")
        )
        info["epistemic_state"] = res.epistemic_state.value
        if res.verified and res.guarantee.is_mathematical_claim:
            info["status"] = STATUS_PROVEN
        elif res.epistemic_state == EpistemicState.REFUTATION:
            info["status"] = STATUS_REFUTED
        return info

    res = ax.compare(pair[0], pair[1])
    info["method"] = "symbolic-reduction+probing"
    info["guarantee"] = res.guarantee.value
    info["detail"] = (
        res.verification.detail if res.verification else (res.error or "no verification")
    )
    info["epistemic_state"] = res.epistemic_state.value
    if res.verified and res.guarantee.is_mathematical_claim:
        info["status"] = STATUS_PROVEN
    elif res.epistemic_state == EpistemicState.REFUTATION:
        info["status"] = STATUS_REFUTED
        data = (res.verification.data or {}) if res.verification else {}
        info["counterexample"] = data.get("counterexample")
        info["witness"] = data.get("witness")
    return info


# --------------------------------------------------------------------------- #
# The eight primitives
# --------------------------------------------------------------------------- #


def investigate(
    ax: Axiom,
    statement: str,
    *,
    root: Path | str = INVESTIGATION_ROOT,
    investigation_id: str | None = None,
    scope: dict[str, Any] | None = None,
    assumptions: dict[str, Any] | str | None = None,
) -> MathResult:
    """Primitive 1 — create a persistent investigation dossier."""
    if not statement or not statement.strip():
        return error_result("investigate", str(statement), "an investigation requires a target statement")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    inv_id = _safe_name(investigation_id or f"inv-{stamp}-{secrets.token_hex(3)}")
    inv = Investigation(root, inv_id)
    if inv.exists():
        return error_result(
            "investigate", statement, f"investigation {inv_id!r} already exists at {inv.dir}"
        )

    analysis = _analyze(ax, statement)
    spec: dict[str, Any] = {
        "investigation_id": inv_id,
        "statement": statement,
        "status": "open",
        "created_at": _now(),
        "axiom_version": _axiom_version(),
        "engines": _engine_versions(ax),
        "scope": scope or {},
        "assumptions": assumptions or {},
        "analysis": analysis,
    }
    inv.dir.mkdir(parents=True, exist_ok=True)
    inv.evidence_dir.mkdir(parents=True, exist_ok=True)
    inv.write_spec(spec)
    inv.write_graph({"nodes": [], "edges": [], "dag_structural_integrity": True,
                      "logical_implication_proven": False, "cycles": []})
    inv.write_unknowns({"unknowns": [], "count": 0, "updated_at": _now()})

    node_id = _node_id(NODE_CLAIM, statement)
    inv.upsert_node({
        "id": node_id,
        "kind": NODE_CLAIM,
        "statement": statement,
        "status": STATUS_OPEN,
        "guarantee": Guarantee.UNVERIFIED.value,
        "depends_on": [],
        "detail": "target claim registered; not yet analysed or proved",
        "epistemic_state": EpistemicState.INCONCLUSIVE.value,
    })
    inv.add_unknown({
        "id": f"unknown-{node_id}",
        "kind": "undecided-claim",
        "description": f"The target claim has not been decided yet: {statement}",
        "severity": "blocking",
        "related": [node_id],
    })

    value = {
        "investigation_id": inv_id,
        "path": str(inv.dir),
        "statement": statement,
        "analysis": analysis,
        "spec": spec,
        "status": "open",
    }
    return _result(
        "investigate",
        statement,
        value,
        f"investigation '{inv_id}' created at {inv.dir}",
        Evidence(
            engine="axiom",
            engine_version=_axiom_version(),
            method="investigation dossier initialisation",
            steps=[
                f"parsed target statement ({analysis.get('interpretation')})",
                f"variables: {analysis.get('variables')}",
                f"domain constraints: {analysis.get('domain_constraints')}",
            ],
            reproducible_with=f"axiom investigate \"{statement}\"",
        ),
    )


def analyze_claim(
    ax: Axiom,
    investigation_id: str,
    *,
    root: Path | str = INVESTIGATION_ROOT,
    statement: str | None = None,
) -> MathResult:
    """Primitive 2 — decompose a claim into variables, hypotheses and boundaries."""
    inv = Investigation(root, investigation_id)
    if not inv.exists():
        return error_result("analyze_claim", investigation_id, f"unknown investigation: {investigation_id}")
    spec = inv.read_spec()
    target = statement or spec.get("statement", "")
    analysis = _analyze(ax, target)
    spec["analysis"] = analysis
    spec["updated_at"] = _now()
    inv.write_spec(spec)
    inv.write_evidence("analysis", {"investigation_id": inv.investigation_id, "analysis": analysis})

    node_id = _node_id(NODE_CLAIM, target)
    inv.upsert_node({
        "id": node_id,
        "kind": NODE_CLAIM,
        "statement": target,
        "status": STATUS_OPEN,
        "guarantee": Guarantee.UNVERIFIED.value,
        "depends_on": [],
        "detail": (
            f"analysed: {len(analysis['variables'])} variable(s), "
            f"{len(analysis['hypotheses'])} hypothesis/ies, "
            f"{len(analysis['boundary_conditions'])} boundary condition(s)"
        ),
        "epistemic_state": EpistemicState.INCONCLUSIVE.value,
    })
    for hypothesis in analysis["hypotheses"]:
        inv.add_unknown({
            "id": f"hyp-{node_id}-{len(hypothesis['kind'])}-{hypothesis['value']}",
            "kind": "pending-hypothesis",
            "description": (
                f"{hypothesis['source']} hypothesis on "
                f"{hypothesis.get('symbol') or 'the claim'}: {hypothesis['value']}"
            ),
            "severity": "non-blocking",
            "related": [node_id],
        })
    return _result(
        "analyze_claim",
        target,
        {"investigation_id": inv.investigation_id, "analysis": analysis, "path": str(inv.dir)},
        f"claim analysed: {len(analysis['variables'])} variable(s), "
        f"{len(analysis['hypotheses'])} hypothesis/ies, "
        f"{len(analysis['boundary_conditions'])} boundary condition(s)",
        Evidence(
            engine="axiom",
            engine_version=_axiom_version(),
            method="safe AST parsing + domain/assumption extraction",
            steps=[
                f"interpretation: {analysis.get('interpretation')}",
                f"free variables: {analysis.get('variables')}",
                f"domain constraints: {analysis.get('domain_constraints')}",
                f"excluded points: {analysis.get('excluded_points')}",
            ],
            reproducible_with=f"axiom analyze-claim {investigation_id}",
        ),
    )


def trace_dependencies(
    ax: Axiom,
    investigation_id: str,
    lemmas: list[Any],
    *,
    root: Path | str = INVESTIGATION_ROOT,
    mode: str = "identity",
) -> MathResult:
    """Primitive 3 — build and audit the proof dependency graph."""
    inv = Investigation(root, investigation_id)
    if not inv.exists():
        return error_result("trace_dependencies", investigation_id, f"unknown investigation: {investigation_id}")
    if not lemmas:
        return error_result("trace_dependencies", investigation_id, "at least one lemma is required")

    spec = inv.read_spec()
    claim = spec.get("statement", "")
    claim_node = _node_id(NODE_CLAIM, claim)
    nodes_added: list[str] = []
    statuses: dict[str, int] = {}

    for index, item in enumerate(lemmas, start=1):
        if isinstance(item, dict):
            statement = str(item.get("statement") or item.get("lemma") or "")
            depends_on = [str(d) for d in (item.get("depends_on") or [])]
        else:
            statement = str(item)
            depends_on = []
        if not statement.strip():
            continue
        info = _classify(ax, statement, mode=mode)
        node_id = _node_id(NODE_LEMMA, statement)
        if not depends_on:
            depends_on = [claim_node] if claim_node != node_id else []
        inv.upsert_node({
            "id": node_id,
            "kind": NODE_LEMMA,
            "statement": statement,
            "status": info["status"],
            "guarantee": info["guarantee"],
            "depends_on": depends_on,
            "detail": info["detail"],
            "method": info["method"],
            "epistemic_state": info["epistemic_state"],
        })
        nodes_added.append(node_id)
        statuses[info["status"]] = statuses.get(info["status"], 0) + 1
        if info["status"] != STATUS_PROVEN:
            inv.add_unknown({
                "id": f"unknown-{node_id}",
                "kind": "unproved-lemma",
                "description": f"Lemma is {info['status']}, not proven: {statement} ({info['detail']})",
                "severity": "blocking",
                "related": [node_id, claim_node],
            })

    graph = inv.read_graph()
    inv.write_evidence("graph", graph)
    value = {
        "investigation_id": inv.investigation_id,
        "nodes": graph.get("nodes", []),
        "edges": graph.get("edges", []),
        "dag_structural_integrity": graph.get("dag_structural_integrity", False),
        "logical_implication_proven": False,
        "cycles": graph.get("cycles", []),
        "status_counts": statuses,
        "path": str(inv.dir),
    }
    return _result(
        "trace_dependencies",
        investigation_id,
        value,
        f"{len(nodes_added)} lemma(s) audited; structural integrity="
        f"{value['dag_structural_integrity']}; logical implication NOT proven",
        Evidence(
            engine="axiom",
            engine_version=_axiom_version(),
            method="per-lemma independent verification + DAG audit",
            steps=[
                f"nodes: {len(graph.get('nodes', []))}",
                f"edges: {len(graph.get('edges', []))}",
                f"status counts: {statuses}",
            ],
            limitations=[
                "A dependency list certifies graph structure only; it does not "
                "certify that a dependency logically implies its dependant."
            ],
            reproducible_with=f"axiom trace-dependencies {investigation_id}",
        ),
    )


def find_counterexample(
    ax: Axiom,
    investigation_id: str,
    *,
    root: Path | str = INVESTIGATION_ROOT,
    statement: str | None = None,
    mode: str = "identity",
) -> MathResult:
    """Primitive 4 — actively hunt a counterexample to the target claim."""
    inv = Investigation(root, investigation_id)
    if not inv.exists():
        return error_result("find_counterexample", investigation_id, f"unknown investigation: {investigation_id}")
    spec = inv.read_spec()
    target = statement or spec.get("statement", "")
    info = _classify(ax, target, mode=mode)
    node_id = _node_id(NODE_CLAIM, target)

    inv.write_evidence("counterexample", {"investigation_id": inv.investigation_id, "result": info})
    if info["status"] == STATUS_REFUTED:
        inv.upsert_node({
            "id": node_id,
            "kind": NODE_CLAIM,
            "statement": target,
            "status": STATUS_REFUTED,
            "guarantee": info["guarantee"],
            "depends_on": [],
            "detail": info["detail"],
            "epistemic_state": info["epistemic_state"],
        })
        inv.add_unknown({
            "id": f"unknown-{node_id}",
            "kind": "refuted-claim",
            "description": f"The claim was refuted by an explicit counterexample: {info['detail']}",
            "severity": "blocking",
            "related": [node_id],
        })
    else:
        if info["status"] == STATUS_PROVEN:
            # The claim was decided: no unknown to log.
            pass
        else:
            inv.add_unknown({
                "id": f"unknown-{node_id}-ce",
                "kind": "no-counterexample-found",
                "description": (
                    "No counterexample was found; this is NOT a proof of the claim "
                    f"(status={info['status']}, method={info['method']})."
                ),
                "severity": "non-blocking",
                "related": [node_id],
            })
    if info["status"] == STATUS_PROVEN:
        detail = (
            "no counterexample exists: the claim was proven "
            f"({info['guarantee']}); {info['detail']}"
        )
    elif info["status"] == STATUS_REFUTED:
        detail = f"claim REFUTED: {info['detail']}"
    else:
        detail = (
            f"no counterexample found (status={info['status']}); "
            "the claim remains undecided"
        )
    return _result(
        "find_counterexample",
        target,
        {
            "investigation_id": inv.investigation_id,
            "result": info,
            "counterexample": info.get("counterexample"),
            "witness": info.get("witness"),
            "refuted": info["status"] == STATUS_REFUTED,
            "proven": info["status"] == STATUS_PROVEN,
        },
        detail,
        Evidence(
            engine="axiom",
            engine_version=_axiom_version(),
            method="complex Gaussian probing + polynomial residual inspection",
            steps=[f"method: {info['method']}", f"detail: {info['detail']}"],
            limitations=[
                "Failure to find a counterexample is not a proof of the claim."
            ],
            reproducible_with=f"axiom find-counterexample {investigation_id}",
        ),
    )


def compare_proofs(
    ax: Axiom,
    investigation_id: str,
    statements: list[Any],
    *,
    root: Path | str = INVESTIGATION_ROOT,
    mode: str = "identity",
) -> MathResult:
    """Primitive 5 — compare proof routes and surface the hypotheses they need."""
    inv = Investigation(root, investigation_id)
    if not inv.exists():
        return error_result("compare_proofs", investigation_id, f"unknown investigation: {investigation_id}")
    if len(statements) < 2:
        return error_result("compare_proofs", investigation_id, "at least two proof attempts are required")

    routes: list[dict[str, Any]] = []
    for item in statements:
        if isinstance(item, dict):
            statement = str(item.get("statement") or "")
            label = str(item.get("label") or statement[:48])
        else:
            statement = str(item)
            label = statement[:48]
        info = _classify(ax, statement, mode=mode)
        analysis = _analyze(ax, statement)
        routes.append({
            "label": label,
            "statement": statement,
            "status": info["status"],
            "guarantee": info["guarantee"],
            "method": info["method"],
            "detail": info["detail"],
            "hypotheses": analysis["hypotheses"],
            "variables": analysis["variables"],
        })

    hypothesis_sets = [
        {f"{h.get('symbol') or '*'}:{h['kind']}={h['value']}" for h in r["hypotheses"]}
        for r in routes
    ]
    shared = set.intersection(*hypothesis_sets) if hypothesis_sets else set()
    unique = [
        {
            "label": r["label"],
            "extra_hypotheses": sorted(hypothesis_sets[i] - shared),
        }
        for i, r in enumerate(routes)
    ]
    inv.write_evidence("proof_comparison", {"investigation_id": inv.investigation_id, "routes": routes})

    value = {
        "investigation_id": inv.investigation_id,
        "routes": routes,
        "shared_hypotheses": sorted(shared),
        "route_specific_hypotheses": unique,
        "path": str(inv.dir),
    }
    return _result(
        "compare_proofs",
        investigation_id,
        value,
        f"{len(routes)} proof route(s) compared; {len(shared)} shared hypothesis/ies",
        Evidence(
            engine="axiom",
            engine_version=_axiom_version(),
            method="per-route independent verification + hypothesis-set diff",
            steps=[f"route: {r['label']} -> {r['status']} ({r['method']})" for r in routes],
            reproducible_with=f"axiom compare-proofs {investigation_id}",
        ),
    )


def list_unknowns(
    ax: Axiom,
    investigation_id: str,
    *,
    root: Path | str = INVESTIGATION_ROOT,
) -> MathResult:
    """Primitive 6 — the Unknown Ledger."""
    inv = Investigation(root, investigation_id)
    if not inv.exists():
        return error_result("list_unknowns", investigation_id, f"unknown investigation: {investigation_id}")
    ledger = inv.read_unknowns()
    graph = inv.read_graph()
    spec = inv.read_spec()

    # Surface any `sorry` / untrusted-axiom marker found in the evidence.
    sorry_hits: list[str] = []
    if inv.evidence_dir.exists():
        for path in sorted(inv.evidence_dir.glob("*.json")):
            try:
                blob = path.read_text(encoding="utf-8")
            except Exception:
                continue
            if "sorry" in blob.lower():
                sorry_hits.append(path.name)

    unknowns = list(ledger.get("unknowns", []))
    for node in graph.get("nodes", []):
        if node.get("status") == STATUS_REFUTED:
            unknowns.append({
                "id": f"unknown-{node['id']}-refuted",
                "kind": "refuted-node",
                "description": f"Node was refuted: {node.get('statement')}",
                "severity": "blocking",
                "related": [node["id"]],
            })
    value = {
        "investigation_id": inv.investigation_id,
        "unknowns": unknowns,
        "count": len(unknowns),
        "blocking": sum(1 for u in unknowns if u.get("severity") == "blocking"),
        "sorry_evidence": sorry_hits,
        "claim": spec.get("statement", ""),
        "path": str(inv.dir),
    }
    return _result(
        "list_unknowns",
        investigation_id,
        value,
        f"{len(unknowns)} unknown(s) recorded ({value['blocking']} blocking)",
        Evidence(
            engine="axiom",
            engine_version=_axiom_version(),
            method="aggregation of undecided nodes, pending hypotheses and evidence markers",
            reproducible_with=f"axiom list-unknowns {investigation_id}",
        ),
    )


def get_evidence_bundle(
    ax: Axiom,
    investigation_id: str,
    *,
    root: Path | str = INVESTIGATION_ROOT,
) -> MathResult:
    """Primitive 7 — export the immutable provenance package."""
    inv = Investigation(root, investigation_id)
    if not inv.exists():
        return error_result("get_evidence_bundle", investigation_id, f"unknown investigation: {investigation_id}")
    spec = inv.read_spec()
    graph = inv.read_graph()

    artifacts: list[dict[str, Any]] = []
    if inv.dir.exists():
        for path in sorted(inv.dir.rglob("*")):
            if path.is_file() and path.name != "bundle.json":
                artifacts.append({
                    "path": str(path.relative_to(inv.dir)).replace("\\", "/"),
                    "bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                })

    verifications: list[dict[str, Any]] = []
    for node in graph.get("nodes", []):
        verifications.append({
            "node": node.get("id"),
            "kind": node.get("kind"),
            "status": node.get("status"),
            "guarantee": node.get("guarantee"),
            "epistemic_state": node.get("epistemic_state"),
            "detail": node.get("detail"),
        })

    bundle = {
        "investigation_id": inv.investigation_id,
        "created_at": _now(),
        "axiom_version": _axiom_version(),
        "engines": _engine_versions(ax),
        "statement": spec.get("statement", ""),
        "scope": spec.get("scope", {}),
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "verifications": verifications,
        "bundle_digest": hashlib.sha256(
            "".join(a["sha256"] for a in artifacts).encode("utf-8")
        ).hexdigest(),
    }
    _write_json(inv.bundle_path, bundle)
    return _result(
        "get_evidence_bundle",
        investigation_id,
        {"investigation_id": inv.investigation_id, "bundle": bundle, "path": str(inv.bundle_path)},
        f"bundle written with {len(artifacts)} artifact(s); digest {bundle['bundle_digest'][:16]}...",
        Evidence(
            engine="axiom",
            engine_version=_axiom_version(),
            method="SHA-256 provenance digests over every dossier artifact",
            steps=[f"{a['path']}: {a['sha256'][:16]}..." for a in artifacts],
            reproducible_with=f"axiom get-evidence-bundle {investigation_id}",
        ),
    )


def export_investigation(
    ax: Axiom,
    investigation_id: str,
    *,
    root: Path | str = INVESTIGATION_ROOT,
) -> MathResult:
    """Primitive 8 — render the reproducible dossier report."""
    inv = Investigation(root, investigation_id)
    if not inv.exists():
        return error_result("export_investigation", investigation_id, f"unknown investigation: {investigation_id}")
    spec = inv.read_spec()
    graph = inv.read_graph()
    ledger = inv.read_unknowns()
    bundle = _read_json(inv.bundle_path) if inv.bundle_path.exists() else {}

    lines: list[str] = []
    lines.append(f"# Investigation Dossier: `{inv.investigation_id}`")
    lines.append("")
    lines.append(f"- **Claim:** `{spec.get('statement', '')}`")
    lines.append(f"- **Status:** {spec.get('status', 'open')}")
    lines.append(f"- **Created:** {spec.get('created_at', '')}")
    lines.append(f"- **AXIOM version:** {spec.get('axiom_version', '')}")
    lines.append(f"- **Engines:** {spec.get('engines', {})}")
    lines.append("")

    analysis = spec.get("analysis") or {}
    lines.append("## 1. Claim Analysis")
    lines.append("")
    lines.append(f"- **Interpretation:** {analysis.get('interpretation', 'unknown')}")
    lines.append(f"- **Free variables:** {analysis.get('variables', [])}")
    lines.append(f"- **Hypotheses:** {len(analysis.get('hypotheses', []))}")
    for hypothesis in analysis.get("hypotheses", []):
        lines.append(f"  - `{hypothesis.get('source')}` {hypothesis.get('symbol') or ''}: {hypothesis.get('value')}")
    lines.append(f"- **Boundary conditions:** {len(analysis.get('boundary_conditions', []))}")
    for condition in analysis.get("boundary_conditions", []):
        lines.append(f"  - `{condition.get('kind')}` {condition.get('symbol') or ''}: {condition.get('value')}")
    lines.append("")

    lines.append("## 2. Proof Dependency Graph")
    lines.append("")
    lines.append("```mermaid")
    lines.append("graph TD")
    for node in graph.get("nodes", []):
        label = f"{node.get('id')}: {node.get('status')}"
        lines.append(f'    {node.get("id")}["{label}"]')
    for edge in graph.get("edges", []):
        lines.append(f'    {edge.get("from")} --> {edge.get("to")}')
    lines.append("```")
    lines.append("")
    lines.append("| Node | Kind | Status | Guarantee | Depends on | Detail |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for node in graph.get("nodes", []):
        lines.append(
            f"| `{node.get('id')}` | {node.get('kind')} | **{node.get('status')}** | "
            f"`{node.get('guarantee')}` | {', '.join(node.get('depends_on', [])) or '—'} | "
            f"{str(node.get('detail', ''))[:120]} |"
        )
    lines.append("")
    lines.append(f"- **DAG structural integrity:** `{graph.get('dag_structural_integrity')}`")
    lines.append(f"- **Logical implication proven:** `{graph.get('logical_implication_proven')}`")
    lines.append("")
    lines.append(
        "> A dependency list certifies the *structure* of the derivation, never that a "
        "dependency logically implies its dependant. Only a kernel-checked proof does that."
    )
    lines.append("")

    lines.append("## 3. Unknown Ledger")
    lines.append("")
    unknowns = ledger.get("unknowns", [])
    if not unknowns:
        lines.append("_No unknowns recorded._")
    else:
        lines.append("| # | Kind | Severity | Description |")
        lines.append("| --- | --- | --- | --- |")
        for index, unknown in enumerate(unknowns, start=1):
            lines.append(
                f"| {index} | {unknown.get('kind')} | **{unknown.get('severity')}** | "
                f"{str(unknown.get('description', ''))[:160]} |"
            )
    lines.append("")

    lines.append("## 4. Evidence Bundle")
    lines.append("")
    if bundle:
        lines.append(f"- **Bundle digest:** `{bundle.get('bundle_digest')}`")
        lines.append(f"- **Artifacts:** {bundle.get('artifact_count')}")
        lines.append("")
        lines.append("| Artifact | Bytes | SHA-256 |")
        lines.append("| --- | --- | --- |")
        for artifact in bundle.get("artifacts", []):
            lines.append(
                f"| `{artifact.get('path')}` | {artifact.get('bytes')} | `{artifact.get('sha256')}` |"
            )
    else:
        lines.append("_No evidence bundle yet — run `math_get_evidence_bundle` first._")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("> Generated by AXIOM v0.3.0 — Mathematical Investigation Layer (ADR-0019).")
    lines.append("> Every claim above is reported with its own guarantee; nothing is promoted to a proof.")

    report = "\n".join(lines) + "\n"
    inv.dir.mkdir(parents=True, exist_ok=True)
    inv.report_path.write_text(report, encoding="utf-8")
    return _result(
        "export_investigation",
        investigation_id,
        {
            "investigation_id": inv.investigation_id,
            "report": report,
            "path": str(inv.report_path),
        },
        f"dossier report written to {inv.report_path}",
        Evidence(
            engine="axiom",
            engine_version=_axiom_version(),
            method="Markdown dossier rendering with Mermaid dependency graph",
            reproducible_with=f"axiom export-investigation {investigation_id}",
        ),
    )


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #


def _node_id(kind: str, statement: str) -> str:
    digest = hashlib.sha256(f"{kind}:{statement}".encode("utf-8")).hexdigest()[:8]
    return f"{kind}-{digest}"


def _axiom_version() -> str:
    try:
        from axiom import __version__

        return __version__
    except Exception:  # pragma: no cover - defensive
        return "unknown"


def _result(
    kind: str,
    input_text: str,
    value: dict[str, Any],
    detail: str,
    evidence: Evidence,
) -> MathResult:
    """Build an investigation-level result.

    Investigation operations are *operational*, not mathematical claims: they
    orchestrate verified computations, they do not themselves certify a
    proposition. The guarantee is therefore operational and the per-item
    guarantees live inside the dossier.

    No ``Verification`` is attached on purpose: ``MathResult.verified`` means
    "an independent mathematical check passed", and an investigation has not
    had one. The provenance lives in :class:`Evidence` and in the dossier
    itself, where every claim keeps its own guarantee.
    """
    return MathResult(
        kind=kind,
        input=input_text,
        ok=True,
        value=value,
        value_str=detail,
        guarantee=Guarantee.HEURISTIC,
        evidence=evidence,
    )
