"""Lean 4 formal proof engine adapter for AXIOM.

Checks Lean 4 theorem statements and scripts via ``lean`` / ``lake`` when
installed. Critically, a proof containing ``sorry`` or ``admit`` is never
accepted as verified. When the Lean toolchain is unavailable on the host, the
engine clearly reports that limitation rather than fabricating a formal proof.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from axiom.engines.base import Answer, Engine

_INCOMPLETE_TOKENS = re.compile(r"\b(sorry|admit)\b")

# Curated offline Mathlib4 & Lean 4 Core theorem catalog for zero-network resilience
_MATHLIB_CATALOG: tuple[dict[str, str], ...] = (
    {
        "name": "Nat.add_comm",
        "module": "Init.Data.Nat.Basic",
        "type": "∀ (n m : ℕ), n + m = m + n",
        "tactic_hint": "omega / ring",
        "doc": "Commutativity of addition on natural numbers.",
        "tags": "nat add commutative addition comm",
    },
    {
        "name": "Nat.mul_comm",
        "module": "Init.Data.Nat.Basic",
        "type": "∀ (n m : ℕ), n * m = m * n",
        "tactic_hint": "ring",
        "doc": "Commutativity of multiplication on natural numbers.",
        "tags": "nat mul multiplication commutative comm",
    },
    {
        "name": "Nat.add_assoc",
        "module": "Init.Data.Nat.Basic",
        "type": "∀ (n m k : ℕ), n + m + k = n + (m + k)",
        "tactic_hint": "omega / ring",
        "doc": "Associativity of addition on natural numbers.",
        "tags": "nat add associative associativity",
    },
    {
        "name": "Int.add_comm",
        "module": "Init.Data.Int.Order",
        "type": "∀ (a b : ℤ), a + b = b + a",
        "tactic_hint": "omega / ring",
        "doc": "Commutativity of integer addition.",
        "tags": "int integer add commutative",
    },
    {
        "name": "add_sq",
        "module": "Mathlib.Algebra.Ring.Parity",
        "type": "∀ [CommSemiring α] (a b : α), (a + b) ^ 2 = a ^ 2 + 2 * a * b + b ^ 2",
        "tactic_hint": "ring",
        "doc": "Binomial expansion of (a + b)^2 in any commutative semiring.",
        "tags": "binomial square expand ring algebra (a+b)^2",
    },
    {
        "name": "sub_sq",
        "module": "Mathlib.Algebra.Ring.Parity",
        "type": "∀ [CommRing α] (a b : α), (a - b) ^ 2 = a ^ 2 - 2 * a * b + b ^ 2",
        "tactic_hint": "ring",
        "doc": "Binomial expansion of (a - b)^2 in a commutative ring.",
        "tags": "binomial square difference ring algebra (a-b)^2",
    },
    {
        "name": "sq_sub_sq",
        "module": "Mathlib.Algebra.Ring.Basic",
        "type": "∀ [CommRing α] (a b : α), a ^ 2 - b ^ 2 = (a + b) * (a - b)",
        "tactic_hint": "ring",
        "doc": "Difference of two squares factorization a^2 - b^2 = (a + b)(a - b).",
        "tags": "difference of squares factor ring algebra a^2-b^2",
    },
    {
        "name": "geom_sum_mul",
        "module": "Mathlib.Algebra.BigOperators.Ring",
        "type": "∀ [Ring α] (x : α) (n : ℕ), (∑ i ∈ range n, x ^ i) * (x - 1) = x ^ n - 1",
        "tactic_hint": "induction n <;> ring",
        "doc": "Finite geometric series identity.",
        "tags": "geometric series sum power finset range",
    },
    {
        "name": "Finset.sum_range_id",
        "module": "Mathlib.Algebra.BigOperators.Intervals",
        "type": "∀ (n : ℕ), ∑ i ∈ range n, i = n * (n - 1) / 2",
        "tactic_hint": "induction n / omega",
        "doc": "Gauss formula for the sum of the first n natural numbers.",
        "tags": "gauss sum arithmetic series natural numbers range",
    },
    {
        "name": "Real.sin_sq_add_cos_sq",
        "module": "Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic",
        "type": "∀ (x : ℝ), Real.sin x ^ 2 + Real.cos x ^ 2 = 1",
        "tactic_hint": "exact Real.sin_sq_add_cos_sq x",
        "doc": "Pythagorean trigonometric identity sin²(x) + cos²(x) = 1.",
        "tags": "trig trigonometry sin cos pythagorean identity real",
    },
    {
        "name": "Real.cos_two_mul",
        "module": "Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic",
        "type": "∀ (x : ℝ), Real.cos (2 * x) = 2 * Real.cos x ^ 2 - 1",
        "tactic_hint": "rw [Real.cos_two_mul]",
        "doc": "Double-angle formula for cosine.",
        "tags": "trig cosine double angle real",
    },
    {
        "name": "Real.sin_two_mul",
        "module": "Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic",
        "type": "∀ (x : ℝ), Real.sin (2 * x) = 2 * Real.sin x * Real.cos x",
        "tactic_hint": "rw [Real.sin_two_mul]",
        "doc": "Double-angle formula for sine.",
        "tags": "trig sine double angle real",
    },
    {
        "name": "Nat.Infinite.primes",
        "module": "Mathlib.Data.Nat.Prime.Infinite",
        "type": "∀ (n : ℕ), ∃ p, n ≤ p ∧ Nat.Prime p",
        "tactic_hint": "exact Nat.exists_infinite_primes n",
        "doc": "Euclid's theorem: there are infinitely many prime numbers.",
        "tags": "prime primes infinite euclid number theory nat",
    },
    {
        "name": "ZMod.fermat_little",
        "module": "Mathlib.FieldTheory.Finite.Basic",
        "type": "∀ {p : ℕ} [Fact p.Prime] {a : ZMod p} (ha : a ≠ 0), a ^ (p - 1) = 1",
        "tactic_hint": "exact ZMod.pow_card_sub_one_eq_one ha",
        "doc": "Fermat's Little Theorem in ZMod p.",
        "tags": "fermat little theorem prime modular arithmetic zmod number theory",
    },
    {
        "name": "Nat.gcd_eq_gcd_ab",
        "module": "Mathlib.Data.Nat.GCD.Basic",
        "type": "∀ (x y : ℕ), (Nat.gcd x y : ℤ) = x * Nat.gcdA x y + y * Nat.gcdB x y",
        "tactic_hint": "exact Nat.gcd_eq_gcd_ab x y",
        "doc": "Bézout's identity relating gcd(x, y) to integer linear combinations.",
        "tags": "bezout gcd extended euclidean number theory",
    },
    {
        "name": "quadratic_eq_zero_iff",
        "module": "Mathlib.Algebra.QuadraticDiscriminant",
        "type": "a ≠ 0 → (a * x * x + b * x + c = 0 ↔ x = (-b + s) / (2 * a) ∨ x = (-b - s) / (2 * a))",
        "tactic_hint": "linear_combination / ring",
        "doc": "Quadratic formula characterization via discriminant square root s.",
        "tags": "quadratic formula roots discriminant algebra equation",
    },
    {
        "name": " HasDerivAt.add",
        "module": "Mathlib.Analysis.Calculus.Deriv.Add",
        "type": "HasDerivAt f f' x → HasDerivAt g g' x → HasDerivAt (fun y => f y + g y) (f' + g') x",
        "tactic_hint": "HasDerivAt.add",
        "doc": "Linearity of differentiation (derivative of a sum).",
        "tags": "derivative calculus diff sum linearity analysis",
    },
    {
        "name": "integral_deriv_eq_sub",
        "module": "Mathlib.MeasureTheory.Integral.FundThmCalculus",
        "type": "(∫ x in a..b, deriv f x) = f b - f a",
        "tactic_hint": "apply integral_deriv_eq_sub",
        "doc": "Fundamental Theorem of Calculus Part 2 for interval integrals.",
        "tags": "integral ftc fundamental theorem calculus deriv",
    },
    {
        "name": "Matrix.det_mul",
        "module": "Mathlib.LinearAlgebra.Matrix.Determinant.Basic",
        "type": "∀ (M N : Matrix n n R), (M * N).det = M.det * N.det",
        "tactic_hint": "exact Matrix.det_mul M N",
        "doc": "Multiplicativity of the determinant: det(M * N) = det(M) * det(N).",
        "tags": "matrix determinant mul linear algebra det",
    },
    {
        "name": "Matrix.mul_nonsing_inv",
        "module": "Mathlib.LinearAlgebra.Matrix.NonsingularInverse",
        "type": "IsUnit M.det → M * M⁻¹ = 1",
        "tactic_hint": "exact Matrix.mul_nonsing_inv M h",
        "doc": "Right inverse property M * M⁻¹ = I for nonsingular matrices.",
        "tags": "matrix inverse identity linear algebra nonsingular",
    },
)


class LeanEngine(Engine):
    """Formal verification adapter for the Lean 4 theorem prover."""

    name = "lean"
    version = "4"
    capabilities = ("prove", "search_mathlib")

    def __init__(self) -> None:
        self.lean_bin = self._find_binary("lean")
        self.lake_bin = self._find_binary("lake")
        if self.lean_bin:
            self.version = self._detect_version(self.lean_bin)

    @staticmethod
    def _find_binary(name: str) -> str | None:
        found = shutil.which(name)
        if found:
            return found
        elan_bin = Path.home() / ".elan" / "bin"
        for candidate in (elan_bin / name, elan_bin / f"{name}.exe"):
            if candidate.exists():
                return str(candidate)
        return None

    @staticmethod
    def _detect_version(lean_bin: str) -> str:
        try:
            proc = subprocess.run(
                [lean_bin, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            first_line = (proc.stdout or "").splitlines()
            return first_line[0].strip() if first_line else "4"
        except Exception:
            return "4"

    @property
    def available(self) -> bool:
        return self.lean_bin is not None

    def prove(self, statement_or_path: str, proof: str = "") -> Answer:
        """Check a Lean 4 theorem file or inline snippet."""
        source, origin = self._load_source(statement_or_path, proof)
        has_hole = bool(_INCOMPLETE_TOKENS.search(source))
        warnings: list[str] = []
        if has_hole:
            warnings.append("proof contains 'sorry' or 'admit' (incomplete proof)")

        if not self.lean_bin:
            return Answer(
                value={"checked": False, "complete": not has_hole, "source": source},
                value_str="Lean 4 binary not found on host; syntax recorded only",
                method="lean4 kernel check (unavailable)",
                steps=[f"loaded Lean source from {origin}"],
                warnings=warnings,
                limitations=[
                    "Lean 4 toolchain (lean/elan) is not installed on this machine; "
                    "formal kernel verification could not be executed."
                ],
                raw={
                    "kernel_verified": False,
                    "has_hole": has_hole,
                    "diagnostics": ["lean binary not found in PATH or ~/.elan/bin"],
                },
            )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".lean", encoding="utf-8", delete=False
        ) as tmp:
            tmp.write(source)
            tmp_path = Path(tmp.name)

        try:
            proc = subprocess.run(
                [self.lean_bin, str(tmp_path)],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            diagnostics = [
                line
                for line in (proc.stdout + "\n" + proc.stderr).splitlines()
                if line.strip()
            ]
            kernel_ok = proc.returncode == 0 and not has_hole
            status_str = (
                "verified by Lean 4 kernel"
                if kernel_ok
                else "rejected by Lean 4 kernel"
            )
            return Answer(
                value={
                    "checked": True,
                    "verified": kernel_ok,
                    "returncode": proc.returncode,
                    "diagnostics": diagnostics,
                },
                value_str=status_str,
                method="Lean 4 typechecker kernel",
                steps=[
                    f"source: {origin}",
                    f"lean exit code: {proc.returncode}",
                ],
                warnings=warnings,
                limitations=[] if kernel_ok else diagnostics[:5],
                raw={
                    "kernel_verified": kernel_ok,
                    "has_hole": has_hole,
                    "diagnostics": diagnostics,
                },
            )
        finally:
            tmp_path.unlink(missing_ok=True)

    def search_mathlib(
        self,
        query: str,
        *,
        max_results: int = 8,
        online: bool = False,
    ) -> Answer:
        """Search Mathlib4 & Lean 4 Core theorems by concept, name, or type pattern.

        Combines deterministic offline search across AXIOM's curated Mathlib4
        catalog with optional live queries to the Loogle JSON API
        (``https://loogle.lean-lang.org/json``).
        """
        q_clean = query.strip()
        tokens = [
            tok.lower()
            for tok in re.split(r"[^a-zA-Z0-9_^\-+*=<>]+", q_clean)
            if tok
        ]

        scored: list[tuple[int, dict[str, Any]]] = []
        for entry in _MATHLIB_CATALOG:
            haystack = " ".join(
                [
                    entry["name"].lower(),
                    entry["type"].lower(),
                    entry["doc"].lower(),
                    entry["tags"].lower(),
                    entry["module"].lower(),
                ]
            )
            score = 0
            if q_clean.lower() in entry["name"].lower():
                score += 10
            if q_clean.lower() in haystack:
                score += 6
            for tok in tokens:
                if tok in entry["name"].lower():
                    score += 4
                elif tok in entry["tags"].lower():
                    score += 3
                elif tok in haystack:
                    score += 1
            if score > 0:
                scored.append(
                    (
                        score,
                        {
                            "name": entry["name"].strip(),
                            "module": entry["module"],
                            "type": entry["type"],
                            "tactic_hint": entry["tactic_hint"],
                            "doc": entry["doc"],
                            "source": "axiom-mathlib-catalog",
                        },
                    )
                )

        scored.sort(key=lambda item: item[0], reverse=True)
        hits: list[dict[str, Any]] = [item[1] for item in scored[:max_results]]
        sources_used = ["axiom-mathlib-catalog"]

        if online and len(hits) < max_results:
            try:
                url = (
                    "https://loogle.lean-lang.org/json?q="
                    + urllib.parse.quote(q_clean)
                )
                req = urllib.request.Request(
                    url, headers={"User-Agent": "AXIOM-Math-Engine/0.1"}
                )
                with urllib.request.urlopen(req, timeout=2.5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("hits", [])[: max_results - len(hits)]:
                    name = item.get("name", "")
                    if any(h["name"] == name for h in hits):
                        continue
                    hits.append(
                        {
                            "name": name,
                            "module": item.get("module", "Mathlib"),
                            "type": item.get("type", ""),
                            "tactic_hint": f"exact {name}",
                            "doc": item.get("doc", "") or "Loogle Mathlib4 match",
                            "source": "loogle-live",
                        }
                    )
                sources_used.append("loogle-live")
            except Exception:
                pass

        top_names = [h["name"] for h in hits[:5]]
        summary = (
            f"found {len(hits)} Mathlib4 theorem(s): {', '.join(top_names)}"
            if hits
            else f"no Mathlib4 matches for {q_clean!r}"
        )
        return Answer(
            value={
                "query": q_clean,
                "count": len(hits),
                "sources": sources_used,
                "results": hits,
            },
            value_str=summary,
            method=f"Mathlib4 semantic & signature search ({', '.join(sources_used)})",
            steps=[
                f"query: {q_clean!r}",
                f"matched {len(hits)} declaration(s)",
                *([f"top match: {hits[0]['name']} : {hits[0]['type']}"] if hits else []),
            ],
            raw={"query": q_clean, "hits": hits},
        )

    @staticmethod
    def _load_source(statement_or_path: str, proof: str = "") -> tuple[str, str]:
        candidate = Path(statement_or_path)
        if (
            "\n" not in statement_or_path
            and candidate.suffix == ".lean"
            and candidate.exists()
        ):
            content = candidate.read_text(encoding="utf-8")
            return content, str(candidate)
        source = statement_or_path.strip()
        if not source.startswith(("theorem ", "lemma ", "example ", "import ", "--")):
            if "=" in source and ":=" not in source:
                source = LeanEngine.formalize_equality(source, proof=proof)
                return source, "auto-formalized equality"
        if proof.strip():
            if not source.endswith(":="):
                source = f"{source} :="
            source = f"{source}\n{proof.strip()}\n"
        return source, "inline snippet"

    @staticmethod
    def formalize_equality(
        equality_text: str,
        *,
        domain: str = "Int",
        proof: str = "",
    ) -> str:
        """Translate a symbolic equality like ``(x + y)^2 = x^2 + 2*x*y + y^2`` into Lean 4."""
        from axiom.parsing import Parser

        parser = Parser()
        eq = parser.parse_equation(equality_text)
        free_vars = sorted((str(s) for s in eq.free_symbols))
        lhs_lean = str(eq.lhs).replace("**", "^")
        rhs_lean = str(eq.rhs).replace("**", "^")
        binders = f"({' '.join(free_vars)} : {domain}) " if free_vars else ""
        tactic = proof.strip() or ("by omega" if "^" not in lhs_lean else "by ring")
        if not tactic.startswith("by"):
            tactic = f"by\n  {tactic}"
        return f"theorem axiom_identity {binders}: {lhs_lean} = {rhs_lean} :=\n  {tactic}\n"

