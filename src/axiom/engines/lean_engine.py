"""Lean 4 formal proof engine adapter for AXIOM.

Checks Lean 4 theorem statements and scripts via ``lean`` / ``lake`` when
installed. Critically, a proof containing ``sorry`` or ``admit`` is never
accepted as verified. When the Lean toolchain is unavailable on the host, the
engine clearly reports that limitation rather than fabricating a formal proof.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from axiom.engines.base import Answer, Engine

_INCOMPLETE_TOKENS = re.compile(r"\b(sorry|admit|sorryAx)\b")
_CUSTOM_AXIOM_DECL = re.compile(
    r"(?:^|\n)\s*(?:private\s+|protected\s+|noncomputable\s+)*(?:axiom|unsafe|opaque)\s+([A-Za-z_][A-Za-z0-9_']*)",
    re.MULTILINE,
)
_UNSAFE_ATTR = re.compile(r"@\s*\[\s*(?:implemented_by|extern|csimp)\b")
_THEOREM_DECL = re.compile(
    r"(?:^|\n)\s*(?:private\s+|protected\s+|noncomputable\s+)*(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_'.]*)",
    re.MULTILINE,
)
_ANON_EXAMPLE_DECL = re.compile(
    r"(^|\n)(\s*(?:private\s+|protected\s+|noncomputable\s+)*)example(\s*[:({\s])",
    re.MULTILINE,
)
_AXIOMS_LINE = re.compile(r"^'([^']+)'\s+depends on axioms:\s*\[([^\]]*)\]")
_NO_AXIOMS_LINE = re.compile(r"^'([^']+)'\s+does not depend on any axioms")

# Standard foundational axioms trusted in Lean 4 / Mathlib 4
STANDARD_LEAN4_AXIOMS: frozenset[str] = frozenset(
    {
        "propext",
        "Classical.choice",
        "Quot.sound",
        "Lean.ofReduceBool",
        "Lean.trustCompiler",
    }
)


def _strip_lean_comments(source: str) -> str:
    """Remove Lean 4 line comments (--) and block comments (/- ... -/)."""
    without_block = re.sub(r"/\-.*?\-/", "", source, flags=re.DOTALL)
    return re.sub(r"--[^\n]*", "", without_block)


def _preexec_lean_resource_bounds() -> None:
    """Enforce POSIX process resource limits (address space / memory)."""
    try:
        import resource
        mem_limit = 3 * 1024 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_limit, mem_limit))
    except Exception:
        pass


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
                encoding="utf-8",
                errors="replace",
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

    @staticmethod
    def prepare_audited_source(
        source: str,
    ) -> tuple[str, list[str], list[str], bool]:
        """Prepare Lean 4 source for kernel + ``#print axioms`` verification.

        * Strips comments before scanning for ``sorry``/``admit``/``sorryAx`` and
          user-declared ``axiom``/``unsafe``/``opaque``/``@[implemented_by]`` constructs.
        * Rewrites anonymous ``example`` headers into named theorems so their
          axiom dependencies can also be inspected via ``#print axioms``.
        * Appends ``#print axioms <name>`` for every theorem/lemma in the file.
        """
        stripped = _strip_lean_comments(source)
        has_hole = bool(_INCOMPLETE_TOKENS.search(stripped))

        custom_axioms: list[str] = [
            m.group(1) for m in _CUSTOM_AXIOM_DECL.finditer(stripped)
        ]
        if _UNSAFE_ATTR.search(stripped):
            custom_axioms.append("@[implemented_by/extern/csimp]")

        # Convert anonymous `example` declarations into named theorems for #print axioms
        counter = 0

        def _name_anon(match: re.Match[str]) -> str:
            nonlocal counter
            counter += 1
            return f"{match.group(1)}{match.group(2)}theorem _axiom_example_{counter}{match.group(3)}"

        rewritten = _ANON_EXAMPLE_DECL.sub(_name_anon, source)
        rewritten_stripped = _strip_lean_comments(rewritten)

        lean_structure_pat = re.compile(
            r"(?:^|\n)\s*(?:"
            r"(?P<scope>namespace|section)\s*(?P<ns>[A-Za-z_][A-Za-z0-9_'.]*)?|"
            r"end(?:\s+(?P<end_ns>[A-Za-z_][A-Za-z0-9_'.]*))?(?:\s|$)|"
            r"(?:private\s+|protected\s+|noncomputable\s+)*(?:theorem|lemma)\s+(?P<thm>[A-Za-z_][A-Za-z0-9_'.]*)"
            r")"
        )

        stack: list[tuple[str, str]] = []
        theorem_names: list[str] = []

        for m in lean_structure_pat.finditer(rewritten_stripped):
            if m.group("scope"):
                stype = m.group("scope")
                sname = m.group("ns") or ""
                stack.append((stype, sname))
            elif m.group("thm"):
                raw_thm = m.group("thm")
                active_ns = [name for (st, name) in stack if st == "namespace" and name]
                qual_thm = ".".join(active_ns) + "." + raw_thm if active_ns else raw_thm
                if qual_thm not in theorem_names:
                    theorem_names.append(qual_thm)
            elif "end" in m.group(0):
                end_name = m.group("end_ns")
                if end_name:
                    idx = -1
                    for i in range(len(stack) - 1, -1, -1):
                        if stack[i][1] == end_name:
                            idx = i
                            break
                    if idx >= 0:
                        stack = stack[:idx]
                    elif stack:
                        stack.pop()
                elif stack:
                    stack.pop()

        audit_lines = [
            f"#print axioms {name}"
            for name in theorem_names
            if f"#print axioms {name}" not in rewritten_stripped
            and f"#print axioms {name.split('.')[-1]}" not in rewritten_stripped
        ]
        if audit_lines:
            audited_source = rewritten.rstrip() + "\n\n" + "\n".join(audit_lines) + "\n"
        else:
            audited_source = rewritten

        return audited_source, theorem_names, custom_axioms, has_hole

    @staticmethod
    def parse_axiom_audit(
        diagnostics: list[str],
        declared_custom_axioms: list[str] | None = None,
    ) -> tuple[list[str], list[str], bool]:
        """Parse ``#print axioms`` output lines from Lean 4 stdout/stderr.

        Returns ``(axioms_used, untrusted_axioms, has_sorry_ax)``.
        """
        axioms_used: list[str] = []
        untrusted: list[str] = list(declared_custom_axioms or [])
        has_sorry_ax = False

        for line in diagnostics:
            clean = line.strip()
            m_dep = _AXIOMS_LINE.match(clean)
            if m_dep:
                raw_list = [
                    ax.strip() for ax in m_dep.group(2).split(",") if ax.strip()
                ]
                for ax in raw_list:
                    if ax not in axioms_used:
                        axioms_used.append(ax)
                    if ax == "sorryAx":
                        has_sorry_ax = True
                    elif ax not in STANDARD_LEAN4_AXIOMS and ax not in untrusted:
                        untrusted.append(ax)
                continue
            _NO_AXIOMS_LINE.match(clean)

        return axioms_used, untrusted, has_sorry_ax

    @staticmethod
    def extract_audited_theorems(diagnostics: list[str]) -> list[str]:
        """Extract declaration names confirmed by ``#print axioms`` output lines."""
        audited: list[str] = []
        for line in diagnostics:
            clean = line.strip()
            m_dep = _AXIOMS_LINE.match(clean)
            if m_dep:
                thm = m_dep.group(1).strip()
                if thm and thm not in audited:
                    audited.append(thm)
                continue
            m_no = _NO_AXIOMS_LINE.match(clean)
            if m_no:
                thm = m_no.group(1).strip()
                if thm and thm not in audited:
                    audited.append(thm)
        return audited

    @staticmethod
    def verify_theorem_audit_coverage(
        expected_theorems: list[str],
        audited_theorems: list[str],
    ) -> tuple[bool, list[str]]:
        """Confirm at least one theorem was declared and every declared theorem was audited."""
        if not expected_theorems:
            return False, ["<no-theorem-declared>"]
        missing: list[str] = []
        for expected in expected_theorems:
            matched = any(
                actual == expected
                or actual.endswith(f".{expected}")
                or expected.endswith(f".{actual}")
                for actual in audited_theorems
            )
            if not matched:
                missing.append(expected)
        return len(missing) == 0, missing

    @staticmethod
    def find_lake_project_root(start_dir: Path | None = None) -> Path | None:
        """Locate the nearest ancestor directory containing ``lakefile.lean`` or ``lakefile.toml``."""
        candidates: list[Path] = []
        if start_dir is not None:
            candidates.append(start_dir if start_dir.is_dir() else start_dir.parent)
        candidates.append(Path.cwd())

        seen: set[Path] = set()
        for base in candidates:
            try:
                resolved = base.resolve()
            except Exception:
                continue
            for directory in (resolved, *resolved.parents):
                if directory in seen:
                    continue
                seen.add(directory)
                if (directory / "lakefile.lean").exists() or (
                    directory / "lakefile.toml"
                ).exists():
                    return directory
        return None

    def build_lean_command(
        self, target_file: Path, *, origin_path: Path | None = None
    ) -> tuple[list[str], str | None]:
        """Build the subprocess command and working directory for Lean 4 verification.

        Uses ``lake env lean <file>`` inside the detected Lake project root when
        both ``lake`` and a ``lakefile`` are available, enabling Mathlib imports.
        """
        lake_root = self.find_lake_project_root(origin_path)
        if self.lake_bin and lake_root is not None:
            return [self.lake_bin, "env", "lean", str(target_file)], str(lake_root)
        return [self.lean_bin or "lean", str(target_file)], None

    @staticmethod
    def detect_trivial_reflexive_theorems(source: str) -> list[str]:
        """Detect theorems whose statement is a syntactic reflexive tautology ``X = X``."""
        trivial: list[str] = []
        try:
            from axiom.core import _extract_lean_declarations
            decls = _extract_lean_declarations(_strip_lean_comments(source))
            for d in decls:
                prop = d.get("prop", "").strip()
                if "=" in prop and "≠" not in prop and "<=" not in prop and ">=" not in prop:
                    parts = [p.strip() for p in prop.split("=")]
                    if len(parts) == 2 and parts[0] == parts[1]:
                        name = d.get("name") or "<anonymous>"
                        if name not in trivial:
                            trivial.append(name)
                elif prop in ("2 + 2 = 4", "1 = 1", "2 + 2 = 2 + 2"):
                    name = d.get("name") or "<anonymous>"
                    if name not in trivial:
                        trivial.append(name)
            return trivial
        except Exception:
            pass

        stripped = _strip_lean_comments(source)
        decl_pat = re.compile(
            r"(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_'.]*)\s*(.*?):=",
            re.DOTALL,
        )
        for m in decl_pat.finditer(stripped):
            name = m.group(1)
            header = m.group(2)
            depth = 0
            colon_idx = -1
            for i, ch in enumerate(header):
                if ch in "({[":
                    depth += 1
                elif ch in ")}]":
                    depth = max(0, depth - 1)
                elif ch == ":" and depth == 0:
                    colon_idx = i
                    break
            if colon_idx < 0:
                continue
            prop = header[colon_idx + 1 :].strip()
            if "=" in prop and "≠" not in prop and "<=" not in prop and ">=" not in prop:
                parts = prop.split("=")
                if len(parts) == 2 and parts[0].strip() == parts[1].strip():
                    trivial.append(name)
        return trivial

    @staticmethod
    def _build_sandboxed_env(sandbox_dir: Path, lean_bin: str | None = None, lake_bin: str | None = None) -> dict[str, str]:
        """Construct a scrubbed, isolated environment dictionary for untrusted Lean processes."""
        isolated_home = (sandbox_dir / ".isolated_home").resolve()
        isolated_home.mkdir(parents=True, exist_ok=True)
        isolated_tmp = (sandbox_dir / ".isolated_tmp").resolve()
        isolated_tmp.mkdir(parents=True, exist_ok=True)

        minimal_path_dirs: list[str] = []
        for bin_path in (lean_bin, lake_bin):
            if bin_path:
                d = str(Path(bin_path).parent.resolve())
                if d not in minimal_path_dirs:
                    minimal_path_dirs.append(d)

        system_defaults = (
            [r"C:\Windows\System32", r"C:\Windows"]
            if os.name == "nt"
            else ["/usr/bin", "/bin", "/usr/local/bin"]
        )
        for d in system_defaults:
            if Path(d).exists() and d not in minimal_path_dirs:
                minimal_path_dirs.append(d)

        scrubbed_path = os.pathsep.join(minimal_path_dirs)

        env: dict[str, str] = {
            "PATH": scrubbed_path,
            "HOME": str(isolated_home),
            "USERPROFILE": str(isolated_home),
            "TMP": str(isolated_tmp),
            "TEMP": str(isolated_tmp),
            "TMPDIR": str(isolated_tmp),
            "LEAN_NO_TELEMETRY": "1",
            "LAKE_NO_NET": "1",
            "PYTHONIOENCODING": "utf-8",
        }

        if "ELAN_HOME" in os.environ:
            env["ELAN_HOME"] = os.environ["ELAN_HOME"]
        elif lean_bin and ".elan" in lean_bin:
            p = Path(lean_bin).resolve()
            for parent in p.parents:
                if parent.name == ".elan":
                    env["ELAN_HOME"] = str(parent)
                    break

        safe_keys = {
            "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "LANG", "LC_ALL", "TERM"
        }
        drop_patterns = (
            "KEY", "TOKEN", "SECRET", "AUTH", "PASS", "CRED", "API",
            "AWS", "GITHUB", "OPENAI", "GEMINI", "COPILOT"
        )

        for k, v in os.environ.items():
            k_upper = k.upper()
            if any(p in k_upper for p in drop_patterns):
                continue
            if k_upper in safe_keys:
                env[k] = v

        return env

    def prove(self, statement_or_path: str, proof: str = "") -> Answer:
        """Check a Lean 4 theorem file or inline snippet with ``#print axioms`` auditing."""
        source, origin = self._load_source(statement_or_path, proof)
        audited_source, theorem_names, custom_axioms, has_hole = (
            self.prepare_audited_source(source)
        )
        trivial_theorems = self.detect_trivial_reflexive_theorems(audited_source)
        warnings: list[str] = []
        if not theorem_names:
            warnings.append(
                "no theorem, lemma, or example declaration found to audit via #print axioms"
            )
        if has_hole:
            warnings.append(
                "proof contains 'sorry', 'admit', or 'sorryAx' (incomplete proof)"
            )
        if custom_axioms:
            warnings.append(
                f"source declares custom/unsafe axiom construct(s): {', '.join(custom_axioms)}"
            )
        if trivial_theorems:
            warnings.append(
                f"syntactic reflexive tautology (X = X) detected in: {', '.join(trivial_theorems)}"
            )

        origin_path = (
            Path(origin)
            if origin not in ("inline snippet", "auto-formalized equality")
            else None
        )

        if not self.lean_bin:
            return Answer(
                value={
                    "checked": False,
                    "complete": bool(theorem_names) and not has_hole and not custom_axioms,
                    "theorems": theorem_names,
                    "audited_theorems": [],
                    "trivial_theorems": trivial_theorems,
                    "untrusted_axioms": custom_axioms,
                    "source": source,
                },
                value_str="Lean 4 binary not found on host; syntax and axiom declarations audited only",
                method="lean4 kernel + #print axioms audit (toolchain unavailable)",
                steps=[
                    f"loaded Lean source from {origin}",
                    f"audited declarations: {theorem_names or ['none']}",
                ],
                warnings=warnings,
                limitations=[
                    "Lean 4 toolchain (lean/elan) is not installed on this machine; "
                    "formal kernel verification could not be executed."
                ],
                raw={
                    "kernel_verified": False,
                    "has_hole": has_hole,
                    "theorems": theorem_names,
                    "audited_theorems": [],
                    "trivial_theorems": trivial_theorems,
                    "audit_complete": False,
                    "axioms_used": [],
                    "untrusted_axioms": custom_axioms,
                    "diagnostics": ["lean binary not found in PATH or ~/.elan/bin"],
                },
            )

        # Place temporary file inside an isolated sandbox / scratch directory
        lake_root = self.find_lake_project_root(origin_path)
        sandbox_dir: Path | None = None
        if self.lake_bin and lake_root is not None:
            scratch_dir = lake_root / ".axiom_scratch"
            scratch_dir.mkdir(parents=True, exist_ok=True)
            sandbox_dir = scratch_dir
        else:
            sandbox_dir = Path(tempfile.mkdtemp(prefix="axiom_lean_isolated_"))

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".lean", dir=str(sandbox_dir), encoding="utf-8", delete=False
        ) as tmp:
            tmp.write(audited_source)
            tmp_path = Path(tmp.name)

        timeout_sec = int(os.environ.get("AXIOM_LEAN_TIMEOUT", "30"))

        try:
            cmd, cwd = self.build_lean_command(tmp_path, origin_path=origin_path)
            # Add resource constraints before target file (2GB max memory, 100k heartbeats)
            if "-M" not in cmd:
                cmd = cmd[:-1] + ["-M", "2048", "-T", "100000"] + [cmd[-1]]

            try:
                sandboxed_env = self._build_sandboxed_env(
                    sandbox_dir, lean_bin=self.lean_bin, lake_bin=self.lake_bin
                )
                preexec_fn = _preexec_lean_resource_bounds if os.name != "nt" else None
                proc = subprocess.run(
                    cmd,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=sandboxed_env,
                    preexec_fn=preexec_fn,
                    timeout=timeout_sec,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                timeout_diag = [f"TimeoutExpired: Lean 4 execution exceeded {timeout_sec}s resource limit"]
                return Answer(
                    value={
                        "checked": True,
                        "verified": False,
                        "timeout": True,
                        "theorems": theorem_names,
                        "audited_theorems": [],
                        "trivial_theorems": trivial_theorems,
                        "axioms_used": [],
                        "untrusted_axioms": custom_axioms,
                        "diagnostics": timeout_diag,
                    },
                    value_str=f"Lean 4 execution timed out ({timeout_sec}s resource limit exceeded)",
                    method=f"Lean 4 kernel (isolated sandbox, timed out after {timeout_sec}s)",
                    steps=[
                        f"source: {origin}",
                        f"execution timed out after {timeout_sec}s",
                    ],
                    warnings=warnings + [f"execution exceeded {timeout_sec}s resource limit"],
                    limitations=[f"Resource limit exceeded: execution exceeded {timeout_sec}s timeout"],
                    raw={
                        "kernel_verified": False,
                        "timeout": True,
                        "theorems": theorem_names,
                        "audited_theorems": [],
                        "trivial_theorems": trivial_theorems,
                        "audit_complete": False,
                        "axioms_used": [],
                        "untrusted_axioms": custom_axioms,
                        "diagnostics": timeout_diag,
                    },
                )
            except Exception as exc:
                err_diag = [f"Execution error: {exc}"]
                return Answer(
                    value={
                        "checked": True,
                        "verified": False,
                        "theorems": theorem_names,
                        "audited_theorems": [],
                        "trivial_theorems": trivial_theorems,
                        "axioms_used": [],
                        "untrusted_axioms": custom_axioms,
                        "diagnostics": err_diag,
                    },
                    value_str=f"Lean 4 execution error: {exc}",
                    method="Lean 4 kernel (isolated sandbox error)",
                    warnings=warnings + [str(exc)],
                    limitations=[f"Process execution failure: {exc}"],
                    raw={
                        "kernel_verified": False,
                        "theorems": theorem_names,
                        "audited_theorems": [],
                        "trivial_theorems": trivial_theorems,
                        "audit_complete": False,
                        "axioms_used": [],
                        "untrusted_axioms": custom_axioms,
                        "diagnostics": err_diag,
                    },
                )

            raw_output = f"{proc.stdout or ''}\n{proc.stderr or ''}"
            diagnostics = [
                line
                for line in raw_output.splitlines()
                if line.strip()
            ]
            axioms_used, untrusted_axioms, has_sorry_ax = self.parse_axiom_audit(
                diagnostics, declared_custom_axioms=custom_axioms
            )
            audited_theorems = self.extract_audited_theorems(diagnostics)
            audit_complete, missing_audits = self.verify_theorem_audit_coverage(
                theorem_names, audited_theorems
            )
            if has_sorry_ax:
                has_hole = True
                warnings.append("proof depends on 'sorryAx' via #print axioms audit")
            if untrusted_axioms:
                warnings.append(
                    f"proof depends on untrusted axiom(s): {', '.join(untrusted_axioms)}"
                )
            if theorem_names and not audit_complete:
                warnings.append(
                    f"#print axioms output missing confirmation for: {', '.join(missing_audits)}"
                )

            kernel_ok = (
                proc.returncode == 0
                and not has_hole
                and len(untrusted_axioms) == 0
                and len(theorem_names) > 0
                and audit_complete
            )
            status_str = (
                "verified by Lean 4 kernel (#print axioms clean)"
                if kernel_ok
                else "rejected by Lean 4 kernel or axiom audit"
            )
            runner_label = "lake env lean" if cwd else "lean"
            failure_limitations: list[str] = []
            if not kernel_ok:
                if not theorem_names:
                    failure_limitations.append(
                        "no theorem, lemma, or example declaration found to audit"
                    )
                elif not audit_complete:
                    failure_limitations.append(
                        f"unconfirmed #print axioms audit for: {', '.join(missing_audits)}"
                    )
                elif untrusted_axioms:
                    failure_limitations.append(
                        f"untrusted axioms: {', '.join(untrusted_axioms)}"
                    )
                else:
                    failure_limitations.extend(diagnostics[:5])

            return Answer(
                value={
                    "checked": True,
                    "verified": kernel_ok,
                    "returncode": proc.returncode,
                    "theorems": theorem_names,
                    "audited_theorems": audited_theorems,
                    "trivial_theorems": trivial_theorems,
                    "axioms_used": axioms_used,
                    "untrusted_axioms": untrusted_axioms,
                    "diagnostics": diagnostics,
                },
                value_str=status_str,
                method=f"Lean 4 typechecker kernel + #print axioms ({runner_label})",
                steps=[
                    f"source: {origin}",
                    f"runner: {runner_label} (exit code: {proc.returncode})",
                    f"audited theorems: {audited_theorems or ['none']}",
                    f"axioms used: {axioms_used or ['none (constructive)']}",
                ],
                warnings=warnings,
                limitations=failure_limitations,
                raw={
                    "kernel_verified": kernel_ok,
                    "has_hole": has_hole,
                    "theorems": theorem_names,
                    "audited_theorems": audited_theorems,
                    "trivial_theorems": trivial_theorems,
                    "audit_complete": audit_complete,
                    "missing_audits": missing_audits,
                    "axioms_used": axioms_used,
                    "untrusted_axioms": untrusted_axioms,
                    "diagnostics": diagnostics,
                },
            )
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)
            if sandbox_dir and ".axiom_scratch" not in str(sandbox_dir):
                shutil.rmtree(sandbox_dir, ignore_errors=True)


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


_build_sandboxed_env = LeanEngine._build_sandboxed_env

