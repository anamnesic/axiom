"""High-precision numerical engine backed by mpmath (and SciPy when available)."""

from __future__ import annotations

import mpmath as mp
import sympy as sp

from axiom.engines.base import Answer, Engine, EngineError


class NumericEngine(Engine):
    """Arbitrary-precision numerical evaluation, root-finding, and quadrature."""

    name = "numeric"
    version = mp.__version__
    capabilities = (
        "evaluate",
        "nsolve",
        "nintegrate",
        "sample",
    )

    def evaluate(self, expr: sp.Expr, precision: int = 50,
                 substitutions: dict[sp.Symbol, object] | None = None) -> Answer:
        target = expr.subs(substitutions) if substitutions else expr
        free = sorted(target.free_symbols, key=str)
        if free:
            raise EngineError(
                f"cannot numerically evaluate expression with free variables: "
                f"{', '.join(str(s) for s in free)}"
            )
        val = target.evalf(precision)
        return Answer(
            value=str(val),
            value_str=str(val),
            latex=sp.latex(val),
            method=f"arbitrary-precision float evaluation (dps={precision})",
            steps=[f"evalf({target}, {precision})", f"-> {val}"],
            limitations=[f"rounded to {precision} significant digits"],
            raw={"object": val, "precision": precision},
        )

    def nsolve(self, equation: sp.Rel, var: sp.Symbol,
               guess: float | tuple[float, float] = 1.0,
               precision: int = 30) -> Answer:
        expr = (
            equation.lhs - equation.rhs
            if isinstance(equation, sp.Equality)
            else equation
        )
        try:
            with mp.workdps(precision):
                sol = sp.nsolve(expr, var, guess, prec=precision)
        except Exception as exc:
            raise EngineError(f"numerical root finding failed: {exc}") from exc
        return Answer(
            value=[str(sol)],
            value_str=f"[{sol}]",
            latex=sp.latex(sol),
            method=f"numerical root-finding (mpmath/sympy.nsolve, dps={precision})",
            steps=[f"nsolve({expr} = 0, {var}, guess={guess})", f"-> {sol}"],
            limitations=[
                "finds a single local root near the initial guess",
                f"numerical precision: {precision} digits",
            ],
            variables=[str(var)],
            raw={"solutions": [sol], "var": var, "equation": equation},
        )

    def nintegrate(self, expr: sp.Expr, var: sp.Symbol,
                   lower: sp.Expr, upper: sp.Expr,
                   precision: int = 30) -> Answer:
        with mp.workdps(precision):
            if lower == sp.oo:
                a = mp.inf
            elif lower == -sp.oo:
                a = -mp.inf
            else:
                a = mp.mpf(str(lower.evalf(precision)))

            if upper == sp.oo:
                b = mp.inf
            elif upper == -sp.oo:
                b = -mp.inf
            else:
                b = mp.mpf(str(upper.evalf(precision)))
            val, err = mp.quad(fn, [a, b], error=True)
            val_str = mp.nstr(val, min(precision, 15))
            err_float = float(err) if err is not None else 0.0
        return Answer(
            value=val_str,
            value_str=val_str,
            latex=val_str,
            method=f"adaptive Gaussian quadrature (mpmath.quad, dps={precision})",
            steps=[
                f"quad({expr}, {var} in [{lower}, {upper}])",
                f"-> {val_str} (est. error {err_float:.2e})",
            ],
            limitations=[f"numerical quadrature error estimate: {err_float:.2e}"],
            variables=[str(var)],
            raw={
                "object": sp.Float(val_str),
                "error": err_float,
                "expr": expr,
                "var": var,
                "limits": (lower, upper),
            },
        )
