"""Optional external mathematical engine adapters (SageMath and Julia).

Follows the REA provider pattern: when the host has ``sage`` or ``julia``
installed on ``PATH``, AXIOM can dispatch symbolic or numerical computations to
them while preserving the exact same :class:`MathResult` contract. All inputs
are validated as mathematical ASTs before constructing the subprocess command.
"""

from __future__ import annotations

import shutil
import subprocess
import sympy as sp

from axiom.engines.base import Answer, Engine, EngineError


class SageEngine(Engine):
    """Adapter for SageMath (``sage -c``)."""

    name = "sagemath"
    version = "external"
    capabilities = ("evaluate", "simplify", "factor")

    def __init__(self) -> None:
        self.binary = shutil.which("sage")

    @property
    def available(self) -> bool:
        return self.binary is not None

    def _run_sage(self, expr: sp.Expr, op: str) -> Answer:
        if not self.binary:
            raise EngineError(
                "SageMath ('sage') binary is not installed on PATH; "
                "use engine='sympy' or install SageMath."
            )
        free = sorted((str(s) for s in expr.free_symbols))
        decl = f"var({free!r}); " if free else ""
        code = f"{decl}print({op}({expr}))"
        proc = subprocess.run(
            [self.binary, "-c", code],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if proc.returncode != 0:
            raise EngineError(f"SageMath error: {proc.stderr.strip()}")
        out = proc.stdout.strip()
        return Answer(
            value=out,
            value_str=out,
            method=f"SageMath {op} via sage -c",
            steps=[f"sage: {code}", f"-> {out}"],
            variables=free,
            raw={"object": expr},
        )

    def evaluate(self, expr: sp.Expr) -> Answer:
        return self._run_sage(expr, " SR")

    def simplify(self, expr: sp.Expr) -> Answer:
        return self._run_sage(expr, "simplify")

    def factor(self, expr: sp.Expr) -> Answer:
        return self._run_sage(expr, "factor")


class JuliaEngine(Engine):
    """Adapter for Julia numerical evaluation (``julia -e``)."""

    name = "julia"
    version = "external"
    capabilities = ("evaluate",)

    def __init__(self) -> None:
        self.binary = shutil.which("julia")

    @property
    def available(self) -> bool:
        return self.binary is not None

    def evaluate(self, expr: sp.Expr) -> Answer:
        if not self.binary:
            raise EngineError(
                "Julia ('julia') binary is not installed on PATH; "
                "use engine='numeric' or install Julia."
            )
        if expr.free_symbols:
            raise EngineError("Julia numeric evaluation requires a closed numeric expression")
        julia_expr = str(expr).replace("**", "^")
        proc = subprocess.run(
            [self.binary, "-e", f"println({julia_expr})"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if proc.returncode != 0:
            raise EngineError(f"Julia error: {proc.stderr.strip()}")
        out = proc.stdout.strip()
        return Answer(
            value=out,
            value_str=out,
            method="Julia numeric evaluation (julia -e)",
            steps=[f"julia: {julia_expr}", f"-> {out}"],
            limitations=["IEEE-754 Float64 evaluation in Julia"],
            raw={"object": sp.sympify(out)},
        )
