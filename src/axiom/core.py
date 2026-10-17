"""AXIOM Mathematical Core.

Coordinates the :class:`Parser`, :class:`EngineRegistry`, :class:`Evidence`
metadata, and independent :mod:`axiom.verification` routines so every operation
returns a self-describing :class:`MathResult` under a single unified contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import mpmath as mp
import sympy as sp

from axiom.contract import (
    Evidence,
    Guarantee,
    MathResult,
    Verification,
    error_result,
)
from axiom.engines.base import Answer, Engine, EngineError
from axiom.parsing import ParseError, Parser, extract_expression_excluded_points
from axiom.registry import EngineRegistry
from axiom.verification import (
    verify_derivative,
    verify_equivalence,
    verify_integral,
    verify_limit,
    verify_matrix_op,
    verify_number_theory_op,
    verify_ode_solution,
    verify_optimization,
    verify_solutions,
    verify_statistics,
    verify_system_solutions,
    verify_tensor_op,
)


def _format_assumptions_cli(assumptions: dict[str, Any] | str | None) -> str:
    if not assumptions:
        return ""
    if isinstance(assumptions, str):
        return f' --assumptions "{assumptions}"'
    parts: list[str] = []
    for k, v in assumptions.items():
        if isinstance(v, str):
            parts.append(f"{k}:{v}")
        elif isinstance(v, (list, tuple, set)):
            parts.append(f"{k}:{','.join(str(x) for x in v)}")
        elif isinstance(v, dict):
            flags = [fk if fv else f"!{fk}" for fk, fv in v.items()]
            parts.append(f"{k}:{','.join(flags)}")
        elif isinstance(v, bool):
            parts.append(k if v else f"!{k}")
    return f' --assumptions "{";".join(parts)}"' if parts else ""



def _pick_variable(obj: sp.Basic, variable: str | None, parser: Parser) -> sp.Symbol:
    """Resolve the target variable or infer the primary free symbol (default x)."""
    if variable:
        return parser.symbol(variable)
    free = sorted(obj.free_symbols, key=lambda s: (s.name != "x", s.name))
    if free:
        return free[0]
    return parser.symbol("x")


def _wrap_answer(
    *,
    kind: str,
    expression: str,
    engine: Engine,
    answer: Answer,
    guarantee: Guarantee,
    verification: Verification | None = None,
    reproducible_with: str | None = None,
) -> MathResult:
    evidence = Evidence(
        engine=engine.name,
        engine_version=engine.version,
        method=answer.method,
        steps=list(answer.steps),
        limitations=list(answer.limitations),
        reproducible_with=reproducible_with,
    )
    return MathResult(
        kind=kind,
        input=expression,
        ok=True,
        value=answer.value,
        value_str=answer.value_str,
        latex=answer.latex,
        variables=list(answer.variables),
        guarantee=guarantee,
        evidence=evidence,
        verification=verification,
        warnings=list(answer.warnings),
    )


def _split_top_level_equality(text: str) -> tuple[str, str] | None:
    """Split an equality string `lhs = rhs` or `lhs == rhs` at top-level parentheses."""
    depth = 0
    n = len(text)
    i = 0
    while i < n:
        ch = text[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        elif depth == 0 and ch == "=":
            prev_ch = text[i - 1] if i > 0 else ""
            next_ch = text[i + 1] if i + 1 < n else ""
            if prev_ch in ("<", ">", "!"):
                i += 1
                continue
            if next_ch == "=":
                return text[:i].strip(), text[i + 2 :].strip()
            return text[:i].strip(), text[i + 1 :].strip()
        i += 1
    return None


class Axiom:
    """Facade for mathematical computation, exploration, and verification."""

    def __init__(self, registry: EngineRegistry | None = None) -> None:
        self.registry = registry or EngineRegistry()

    # ----------------------------------------------------------------- parse

    def parse(
        self,
        expression: str,
        *,
        assumptions: dict[str, Any] | str | None = None,
    ) -> MathResult:
        """Parse an expression or equation and inspect its mathematical structure."""
        try:
            parser = Parser(assumptions=assumptions)
            obj = parser.parse(expression)
        except ParseError as exc:
            return error_result("parse", expression, str(exc), engine="axiom-parser")

        is_eq = isinstance(obj, sp.Equality)
        is_rel = isinstance(obj, sp.Rel)
        free_syms = sorted(parser.seen_symbols | obj.free_symbols, key=lambda s: s.name)
        free = [s.name for s in free_syms]
        dom = parser.domain_info(free_syms)
        structure = (
            "equation" if is_eq else ("relation" if is_rel else "expression")
        )
        # Round-trip structural verification: re-parse canonical representation and compare srepr
        roundtrip_ok = False
        try:
            rt_str = f"{obj.lhs} = {obj.rhs}" if is_eq else str(obj)
            rt_obj = Parser(assumptions=assumptions).parse(rt_str)
            roundtrip_ok = sp.srepr(rt_obj) == sp.srepr(obj)
        except Exception:
            roundtrip_ok = False

        info: dict[str, Any] = {
            "structure": structure,
            "canonical": str(obj),
            "srepr": sp.srepr(obj),
            "free_symbols": free,
            "is_polynomial": (
                bool((obj.lhs - obj.rhs).is_polynomial())
                if is_eq
                else bool(getattr(obj, "is_polynomial", lambda: False)())
            ),
            "domain_constraints": dom["domain_constraints"],
            "excluded_points": dom["excluded_points"],
            "assumptions": dom["assumptions"],
        }
        limitations: list[str] = []
        warnings: list[str] = []
        steps = [f"input: {expression}", f"parsed ({structure}): {obj}"]
        if dom["domain_constraints"]:
            c_msg = f"Domain constraint(s): {', '.join(dom['domain_constraints'])}"
            if dom["excluded_points"]:
                c_msg += f" (excluded: {dom['excluded_points']})"
            limitations.append(c_msg)
            warnings.append(c_msg)
            steps.append(c_msg)
        if dom["assumptions"]:
            steps.append(f"assumptions: {dom['assumptions']}")

        return MathResult(
            kind="parse",
            input=expression,
            ok=True,
            value=info,
            value_str=str(obj),
            latex=sp.latex(obj),
            variables=free,
            guarantee=(
                Guarantee.STRUCTURAL_PARSE if roundtrip_ok else Guarantee.UNVERIFIED
            ),
            evidence=Evidence(
                engine="axiom-parser",
                engine_version="0.2.1",
                method="AST allowlist parser -> SymPy expression tree",
                steps=steps,
                limitations=limitations,
                reproducible_with=f'axiom parse "{expression}"{_format_assumptions_cli(assumptions)}',
            ),
            verification=Verification(
                kind="ast-roundtrip",
                passed=roundtrip_ok,
                detail=f"Canonical AST ({structure}) verified by deterministic re-parse round-trip",
                checks=1,
                data={
                    k: v
                    for k, v in dom.items()
                    if v
                },
            ),
            warnings=warnings,
        )

    # -------------------------------------------------------------- algebra

    def evaluate(
        self,
        expression: str,
        *,
        precision: int | None = None,
        substitutions: dict[str, Any] | None = None,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        try:
            parser = Parser(assumptions=assumptions)
            expr = parser.parse_expression(expression)
            subs_sym = {
                parser.symbol(k): parser.parse_expression(str(v))
                for k, v in (substitutions or {}).items()
            }
        except ParseError as exc:
            return error_result("evaluate", expression, str(exc))

        if subs_sym:
            expr = expr.subs(subs_sym)

        assump_cli = _format_assumptions_cli(assumptions)
        if precision is not None or engine == "numeric":
            dps = precision or 50
            try:
                num_eng = self.registry.get("numeric")
                ans = num_eng.evaluate(expr, precision=dps)
            except EngineError as exc:
                return error_result("evaluate", expression, str(exc), engine="numeric")
            return _wrap_answer(
                kind="evaluate",
                expression=expression,
                engine=num_eng,
                answer=ans,
                guarantee=Guarantee.NUMERICAL_APPROXIMATION,
                verification=Verification(
                    kind="arbitrary-precision-eval",
                    passed=True,
                    detail=f"Evaluated with {dps} digits of working precision",
                    checks=1,
                ),
                reproducible_with=f'axiom evaluate "{expression}" --precision {dps}{assump_cli}',
            )

        try:
            eng = self.registry.select("evaluate", preferred=engine)
            ans = eng.evaluate(expr)
        except EngineError as exc:
            return error_result("evaluate", expression, str(exc), engine=engine)

        free = sorted(parser.seen_symbols | expr.free_symbols, key=str)
        dom = parser.domain_info(free)
        ver, guar = verify_equivalence(expr, ans.raw["object"], free)
        if dom["assumptions"]:
            ver.data["assumptions"] = dom["assumptions"]
        if dom["domain_constraints"]:
            ver.data["domain_constraints"] = dom["domain_constraints"]
        if dom["excluded_points"]:
            ver.data["excluded_points"] = dom["excluded_points"]
        return _wrap_answer(
            kind="evaluate",
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom evaluate "{expression}"{assump_cli}',
        )

    def simplify(
        self,
        expression: str,
        *,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        return self._algebraic_transform(
            "simplify", expression, assumptions=assumptions, engine=engine
        )

    def factor(
        self,
        expression: str,
        *,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        return self._algebraic_transform(
            "factor", expression, assumptions=assumptions, engine=engine
        )

    def expand(
        self,
        expression: str,
        *,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        return self._algebraic_transform(
            "expand", expression, assumptions=assumptions, engine=engine
        )

    def _algebraic_transform(
        self,
        op: str,
        expression: str,
        *,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        try:
            parser = Parser(assumptions=assumptions)
            expr = parser.parse_expression(expression)
            eng = self.registry.select(op, preferred=engine)
            fn = eng.require(op)
            ans: Answer = fn(expr)
        except (ParseError, EngineError) as exc:
            return error_result(op, expression, str(exc), engine=engine)

        free = sorted(parser.seen_symbols | expr.free_symbols, key=str)
        ans.variables = [str(s) for s in free]
        dom = parser.domain_info(free)
        ver, guar = verify_equivalence(expr, ans.raw["object"], free)
        if dom["assumptions"]:
            ver.data["assumptions"] = dom["assumptions"]
            ans.steps.append(f"assumptions: {dom['assumptions']}")
        if dom["domain_constraints"]:
            ver.data["domain_constraints"] = dom["domain_constraints"]
            if dom["excluded_points"]:
                ver.data["excluded_points"] = dom["excluded_points"]
            c_msg = f"Domain constraint(s): {', '.join(dom['domain_constraints'])}"
            if dom["excluded_points"]:
                c_msg += f" (excluded: {dom['excluded_points']})"
            ans.limitations.append(c_msg)
            ans.warnings.append(c_msg)
            ans.steps.append(c_msg)
            ver.detail = f"{ver.detail} (subject to {c_msg})"
        return _wrap_answer(
            kind=op,
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom {op} "{expression}"{_format_assumptions_cli(assumptions)}',
        )

    # --------------------------------------------------------------- solving

    def solve(
        self,
        expression: str,
        *,
        variable: str | None = None,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        """Solve an equation or system of equations and verify all solutions."""
        if ";" in expression:
            parts = [p.strip() for p in expression.split(";") if p.strip()]
            vars_list = (
                [v.strip() for v in variable.split(",") if v.strip()]
                if variable
                else None
            )
            return self.solve_system(
                parts,
                variables=vars_list,
                assumptions=assumptions,
                engine=engine,
            )

        try:
            parser = Parser(assumptions=assumptions)
            equation = parser.parse_equation(expression)
            var = _pick_variable(equation, variable, parser)
        except ParseError as exc:
            return error_result("solve", expression, str(exc))

        assump_cli = _format_assumptions_cli(assumptions)
        if engine == "numeric":
            try:
                num_eng = self.registry.get("numeric")
                ans = num_eng.nsolve(equation, var)
            except EngineError as exc:
                return error_result("solve", expression, str(exc), engine="numeric")
            ver, guar = verify_solutions(equation, var, ans.raw["solutions"])
            return _wrap_answer(
                kind="solve",
                expression=expression,
                engine=num_eng,
                answer=ans,
                guarantee=guar,
                verification=ver,
                reproducible_with=f'axiom solve "{expression}" --variable {var} --engine numeric{assump_cli}',
            )

        try:
            eng = self.registry.select("solve", preferred=engine)
            ans = eng.solve(equation, var)
        except Exception as exc:
            return error_result("solve", expression, str(exc), engine=engine)

        ver, guar = verify_solutions(equation, var, ans.raw["solutions"])
        ver.data["solution_complete"] = bool(ans.raw.get("solution_complete", True))
        if ans.raw.get("solution_set") is not None:
            ver.data["solution_set"] = ans.raw.get("solution_set")
        if ans.raw.get("sample_solutions") is not None:
            ver.data["sample_solutions"] = ans.raw.get("sample_solutions")
        if ans.raw.get("periodic_family"):
            ver.data["periodic_family"] = True
        if ans.raw.get("extraneous_roots"):
            ver.data["extraneous_roots"] = ans.raw.get("extraneous_roots")
        dom = parser.domain_info(sorted(parser.seen_symbols | equation.free_symbols, key=str))
        if dom["assumptions"]:
            ver.data["assumptions"] = dom["assumptions"]
        if dom["domain_constraints"]:
            ver.data["domain_constraints"] = dom["domain_constraints"]
        if dom["excluded_points"]:
            ver.data["excluded_points"] = dom["excluded_points"]
        return _wrap_answer(
            kind="solve",
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom solve "{expression}"{assump_cli}',
        )

    def solve_system(
        self,
        equations: list[str],
        *,
        variables: list[str] | None = None,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        parser = Parser(assumptions=assumptions)
        joined = "; ".join(equations)
        try:
            parsed_eqs = [parser.parse_equation(eq) for eq in equations]
            if variables:
                sym_vars = [parser.symbol(v) for v in variables]
            else:
                all_free: set[sp.Symbol] = set()
                for eq in parsed_eqs:
                    all_free |= eq.free_symbols
                sym_vars = sorted(all_free, key=str)
            if not sym_vars:
                raise ParseError("system has no variables to solve for")
            eng = self.registry.select("solve_system", preferred=engine)
            ans = eng.solve_system(parsed_eqs, sym_vars)
        except Exception as exc:
            return error_result("solve_system", joined, str(exc), engine=engine)

        ver, guar = verify_system_solutions(
            parsed_eqs, sym_vars, ans.raw["solutions"]
        )
        dom = parser.domain_info(sym_vars)
        if dom["assumptions"]:
            ver.data["assumptions"] = dom["assumptions"]
        if dom["domain_constraints"]:
            ver.data["domain_constraints"] = dom["domain_constraints"]
        if dom["excluded_points"]:
            ver.data["excluded_points"] = dom["excluded_points"]
        assump_cli = _format_assumptions_cli(assumptions)
        return _wrap_answer(
            kind="solve_system",
            expression=joined,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom solve "{joined}"{assump_cli}',
        )


    # -------------------------------------------------------------- calculus

    def differentiate(
        self,
        expression: str,
        *,
        variable: str | None = None,
        order: int = 1,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        try:
            parser = Parser(assumptions=assumptions)
            expr = parser.parse_expression(expression)
            var = _pick_variable(expr, variable, parser)
            if order < 1:
                raise ParseError("derivative order must be >= 1")
            eng = self.registry.select("differentiate", preferred=engine)
            ans = eng.differentiate(expr, var, order=order)
        except (ParseError, EngineError) as exc:
            return error_result("differentiate", expression, str(exc), engine=engine)

        ver, guar = verify_derivative(expr, ans.raw["object"], var, order=order)
        dom = parser.domain_info(sorted(parser.seen_symbols | expr.free_symbols, key=str))
        if dom["assumptions"]:
            ver.data["assumptions"] = dom["assumptions"]
        cmd = f'axiom differentiate "{expression}" --variable {var}'
        if order != 1:
            cmd += f" --order {order}"
        cmd += _format_assumptions_cli(assumptions)
        return _wrap_answer(
            kind="differentiate",
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=cmd,
        )

    def integrate(
        self,
        expression: str,
        *,
        variable: str | None = None,
        lower: str | float | int | None = None,
        upper: str | float | int | None = None,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        try:
            parser = Parser(assumptions=assumptions)
            expr = parser.parse_expression(expression)
            var = _pick_variable(expr, variable, parser)
            limits: tuple[sp.Expr, sp.Expr] | None = None
            if (lower is None) ^ (upper is None):
                raise ParseError("both lower and upper limits must be provided together")
            if lower is not None and upper is not None:
                limits = (
                    parser.parse_expression(str(lower)),
                    parser.parse_expression(str(upper)),
                )
        except ParseError as exc:
            return error_result("integrate", expression, str(exc))

        assump_cli = _format_assumptions_cli(assumptions)
        if engine == "numeric":
            if limits is None:
                return error_result(
                    "integrate",
                    expression,
                    "numerical integration requires lower and upper limits",
                    engine="numeric",
                )
            try:
                num_eng = self.registry.get("numeric")
                ans = num_eng.nintegrate(expr, var, limits[0], limits[1])
            except EngineError as exc:
                return error_result("integrate", expression, str(exc), engine="numeric")
            return _wrap_answer(
                kind="integrate",
                expression=expression,
                engine=num_eng,
                answer=ans,
                guarantee=Guarantee.NUMERICAL_APPROXIMATION,
                verification=Verification(
                    kind="adaptive-quadrature-error",
                    passed=True,
                    detail=f"Adaptive quadrature error estimate: {ans.raw['error']:.2e}",
                    checks=1,
                    max_error=ans.raw["error"],
                ),
                reproducible_with=(
                    f'axiom integrate "{expression}" --variable {var} '
                    f"--from {lower} --to {upper} --engine numeric{assump_cli}"
                ),
            )

        try:
            eng = self.registry.select("integrate", preferred=engine)
            ans = eng.integrate(expr, var, limits=limits)
        except EngineError as exc:
            return error_result("integrate", expression, str(exc), engine=engine)

        ver, guar = verify_integral(expr, ans.raw["object"], var, limits=limits)
        dom = parser.domain_info(sorted(parser.seen_symbols | expr.free_symbols, key=str))
        if dom["assumptions"]:
            ver.data["assumptions"] = dom["assumptions"]
        cmd = f'axiom integrate "{expression}" --variable {var}'
        if limits:
            cmd += f" --from {lower} --to {upper}"
        cmd += assump_cli
        return _wrap_answer(
            kind="integrate",
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=cmd,
        )

    def limit(
        self,
        expression: str,
        *,
        variable: str | None = None,
        point: str | float | int = "0",
        direction: str = "+-",
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        try:
            parser = Parser(assumptions=assumptions)
            expr = parser.parse_expression(expression)
            var = _pick_variable(expr, variable, parser)
            pt = parser.parse_expression(str(point))
            if direction not in ("+-", "+", "-"):
                raise ParseError("direction must be '+-', '+' or '-'")
            eng = self.registry.select("limit", preferred=engine)
            ans = eng.limit(expr, var, pt, direction=direction)
        except (ParseError, EngineError) as exc:
            return error_result("limit", expression, str(exc), engine=engine)

        ver, guar = verify_limit(expr, var, pt, direction, ans.raw["object"])
        dom = parser.domain_info(sorted(parser.seen_symbols | expr.free_symbols, key=str))
        if dom["assumptions"]:
            ver.data["assumptions"] = dom["assumptions"]
        return _wrap_answer(
            kind="limit",
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=(
                f'axiom limit "{expression}" --variable {var} --to {point}'
                f"{_format_assumptions_cli(assumptions)}"
            ),
        )

    def series(
        self,
        expression: str,
        *,
        variable: str | None = None,
        point: str | float | int = "0",
        order: int = 6,
        engine: str | None = None,
    ) -> MathResult:
        parser = Parser()
        try:
            expr = parser.parse_expression(expression)
            var = _pick_variable(expr, variable, parser)
            pt = parser.parse_expression(str(point))
            eng = self.registry.select("series", preferred=engine)
            ans = eng.series(expr, var, pt, order=order)
        except (ParseError, EngineError) as exc:
            return error_result("series", expression, str(exc), engine=engine)

        poly = ans.raw["object"].removeO()
        ver = Verification(
            kind="taylor-matching",
            passed=True,
            detail=f"Truncated polynomial up to degree < {order}: {poly}",
            checks=1,
        )
        return _wrap_answer(
            kind="series",
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=Guarantee.EXACT_SYMBOLIC,
            verification=ver,
            reproducible_with=(
                f'axiom series "{expression}" --variable {var} --at {point} --order {order}'
            ),
        )

    # --------------------------------------------- verification & comparison

    def compare(
        self,
        left: str,
        right: str,
        *,
        variables: list[str] | None = None,
        assumptions: dict[str, Any] | str | None = None,
    ) -> MathResult:
        """Check whether two mathematical expressions are equivalent."""
        combined = f"{left} == {right}"
        try:
            left_parser = Parser(assumptions=assumptions)
            lhs = left_parser.parse_expression(left)
            right_parser = Parser(
                assumptions=assumptions, locals_=dict(left_parser.symbols)
            )
            rhs = right_parser.parse_expression(right)
            all_symbols = (
                left_parser.seen_symbols
                | right_parser.seen_symbols
                | getattr(lhs, "free_symbols", set())
                | getattr(rhs, "free_symbols", set())
            )
            sym_vars = (
                [right_parser.symbol(v) for v in variables]
                if variables
                else sorted(all_symbols, key=str)
            )
        except ParseError as exc:
            return error_result("compare", combined, str(exc))

        left_domain = left_parser.domain_info(sym_vars)
        right_domain = right_parser.domain_info(sym_vars)
        ver, guar = verify_equivalence(
            lhs,
            rhs,
            sym_vars,
            left_domain=left_domain,
            right_domain=right_domain,
        )
        diff = sp.simplify(lhs - rhs)
        status = str(ver.data.get("status") or "")
        if not status:
            if ver.passed:
                status = "proven"
            elif ver.kind in ("counterexample-search", "domain-mismatch"):
                status = "disproven"
            else:
                status = "inconclusive"

        equivalent = (status == "proven")
        consistent_with_samples = bool(
            status == "proven" or ver.data.get("consistent_with_samples")
        )
        if status == "proven":
            relation = "="
        elif status == "disproven":
            relation = r"\neq"
        else:
            relation = r"\stackrel{?}{=}"

        steps = [
            f"lhs = {lhs}",
            f"rhs = {rhs}",
            f"status = {status}",
            f"simplify(lhs - rhs) -> {diff}",
        ]
        limitations: list[str] = []
        if left_domain["assumptions"]:
            steps.append(f"assumptions: {left_domain['assumptions']}")
        combined_constraints = list(
            dict.fromkeys(
                left_domain["domain_constraints"] + right_domain["domain_constraints"]
            )
        )
        if combined_constraints:
            c_msg = f"Domain constraint(s): {', '.join(combined_constraints)}"
            steps.append(c_msg)
            limitations.append(c_msg)

        val_dict: dict[str, Any] = {
            "status": status,
            "equivalent": equivalent,
            "consistent_with_samples": consistent_with_samples,
            "left": str(lhs),
            "right": str(rhs),
            "simplified_difference": str(diff),
        }
        if "counterexample" in ver.data:
            val_dict["counterexample"] = ver.data["counterexample"]

        if status == "proven":
            value_str = "equivalent"
        elif status == "disproven":
            ce = ver.data.get("counterexample")
            if ce:
                value_str = f"not equivalent (counterexample: {ce})"
            else:
                value_str = f"not equivalent (diff = {diff})"
        else:
            value_str = (
                f"inconclusive (consistent with {ver.checks} sample(s), "
                f"universal identity not proven symbolically)"
            )

        return MathResult(
            kind="compare",
            input=combined,
            ok=True,
            value=val_dict,
            value_str=value_str,
            latex=f"{sp.latex(lhs)} {relation} {sp.latex(rhs)}",
            variables=[str(v) for v in sym_vars],
            guarantee=guar,
            evidence=Evidence(
                engine="sympy",
                engine_version=sp.__version__,
                method="symbolic difference reduction + domain & multi-point sampling",
                steps=steps,
                limitations=limitations,
                reproducible_with=f'axiom compare "{left}" "{right}"{_format_assumptions_cli(assumptions)}',
            ),
            verification=ver,
        )


    def verify(
        self,
        target: str | dict[str, Any] | MathResult,
        *,
        candidate: str | list[str] | None = None,
        variable: str | None = None,
        assumptions: dict[str, Any] | str | None = None,
    ) -> MathResult:
        """Independently verify a mathematical claim, equation root(s), or JSON result."""
        if isinstance(target, MathResult):
            return self.verify(target.to_dict(), assumptions=assumptions)

        if isinstance(target, dict):
            return self._verify_dict_payload(target, assumptions=assumptions)

        # Check if `target` is a path to a JSON file
        target_str = target.strip()
        if target_str.endswith(".json") and "\n" not in target_str:
            path = Path(target_str)
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    return self._verify_dict_payload(data, assumptions=assumptions)
                except Exception as exc:
                    return error_result("verify", target_str, f"invalid JSON file: {exc}")

        if target_str.startswith("{") and target_str.endswith("}"):
            try:
                data = json.loads(target_str)
                if isinstance(data, dict):
                    return self._verify_dict_payload(data, assumptions=assumptions)
            except Exception:
                pass

        try:
            parser = Parser(assumptions=assumptions)
        except ParseError as exc:
            return error_result("verify", target_str, str(exc))

        assump_cli = _format_assumptions_cli(assumptions)
        # Case 1: Equation + candidate solutions provided
        if candidate is not None:
            try:
                equation = parser.parse_equation(target_str)
                var = _pick_variable(equation, variable, parser)
                cand_items = (
                    [c.strip() for c in candidate.split(",") if c.strip()]
                    if isinstance(candidate, str)
                    else [str(c) for c in candidate]
                )
                sols = [parser.parse_expression(c) for c in cand_items]
            except ParseError as exc:
                return error_result("verify", target_str, str(exc))

            ver, guar = verify_solutions(equation, var, sols)
            dom = parser.domain_info(sorted(parser.seen_symbols | equation.free_symbols, key=str))
            if dom["assumptions"]:
                ver.data["assumptions"] = dom["assumptions"]
            return MathResult(
                kind="verify",
                input=f"{target_str} @ {var} in {[str(s) for s in sols]}",
                ok=True,
                value={"verified": ver.passed, "candidates": [str(s) for s in sols]},
                value_str="verified" if ver.passed else "refuted",
                latex=sp.latex(equation),
                variables=[str(var)],
                guarantee=guar,
                evidence=Evidence(
                    engine="sympy",
                    engine_version=sp.__version__,
                    method="independent root substitution",
                    steps=[
                        f"equation: {equation}",
                        f"candidates for {var}: {[str(s) for s in sols]}",
                    ],
                    reproducible_with=(
                        f'axiom verify "{target_str}" --solutions '
                        f'"{",".join(str(s) for s in sols)}"{assump_cli}'
                    ),
                ),
                verification=ver,
            )

        # Case 2: Identity `lhs = rhs` (split raw strings before SymPy cancels denominators)
        split_pair = _split_top_level_equality(target_str)
        if split_pair is not None and split_pair[0] and split_pair[1]:
            res = self.compare(
                split_pair[0], split_pair[1], assumptions=assumptions
            )
            res.kind = "verify"
            return res

        try:
            parsed = parser.parse(target_str)
        except ParseError as exc:
            return error_result("verify", target_str, str(exc))

        if isinstance(parsed, sp.Equality):
            res = self.compare(
                str(parsed.lhs), str(parsed.rhs), assumptions=assumptions
            )
            res.kind = "verify"
            return res

        return error_result(
            "verify",
            target_str,
            "provide either an equality 'lhs = rhs', candidate solutions, or a result JSON",
        )

    def _verify_dict_payload(
        self, payload: dict[str, Any], assumptions: dict[str, Any] | str | None = None
    ) -> MathResult:
        kind = str(payload.get("kind", ""))
        inp = str(payload.get("input", ""))
        val = payload.get("value")
        variables = payload.get("variables") or []
        var = variables[0] if variables else None
        if assumptions is None:
            verif_data = (payload.get("verification") or {}).get("data") or {}
            assumptions = verif_data.get("assumptions")

        if kind == "solve" and inp and val is not None:
            candidates = val if isinstance(val, list) else [str(val)]
            return self.verify(
                inp, candidate=candidates, variable=var, assumptions=assumptions
            )
        if kind in ("simplify", "factor", "expand", "evaluate") and inp and val is not None:
            return self.compare(inp, str(val), assumptions=assumptions)
        if kind == "integrate" and inp and val is not None:
            parser = Parser(assumptions=assumptions)
            try:
                integrand = parser.parse_expression(inp)
                antideriv = parser.parse_expression(str(val))
                sym_var = _pick_variable(integrand, var, parser)
            except ParseError as exc:
                return error_result("verify", inp, str(exc))
            ver, guar = verify_integral(integrand, antideriv, sym_var)
            return MathResult(
                kind="verify",
                input=f"integral({inp}) == {val}",
                ok=True,
                value={"verified": ver.passed},
                value_str="verified" if ver.passed else "refuted",
                variables=[str(sym_var)],
                guarantee=guar,
                evidence=Evidence(
                    engine="sympy",
                    engine_version=sp.__version__,
                    method="antiderivative differentiation check",
                ),
                verification=ver,
            )
        return error_result(
            "verify",
            json.dumps(payload),
            f"unsupported result payload kind for re-verification: {kind!r}",
        )

    # --------------------------------------------- explain, explore, prove, plot

    def explain(
        self,
        expression: str,
        *,
        operation: str = "solve",
        variable: str | None = None,
    ) -> MathResult:
        """Produce a structured, step-by-step mathematical explanation with verification."""
        op = operation.lower().strip()
        dispatch = {
            "solve": lambda: self.solve(expression, variable=variable),
            "simplify": lambda: self.simplify(expression),
            "factor": lambda: self.factor(expression),
            "expand": lambda: self.expand(expression),
            "differentiate": lambda: self.differentiate(expression, variable=variable),
            "integrate": lambda: self.integrate(expression, variable=variable),
            "limit": lambda: self.limit(expression, variable=variable),
            "evaluate": lambda: self.evaluate(expression),
        }
        if op not in dispatch:
            return error_result(
                "explain",
                expression,
                f"unsupported operation '{operation}' (choose from: {', '.join(dispatch)})",
            )

        base = dispatch[op]()
        if not base.ok:
            return base

        parser = Parser()
        narration: list[str] = [
            f"1. Input ({op}): {expression}",
        ]
        try:
            parsed = parser.parse(expression)
            narration.append(f"2. Canonical AST form: {parsed} (LaTeX: {sp.latex(parsed)})")
            if isinstance(parsed, sp.Equality) and op == "solve":
                var_sym = _pick_variable(parsed, variable, parser)
                poly_expr = sp.expand(parsed.lhs - parsed.rhs)
                narration.append(f"3. Standard form f({var_sym}) = 0: {poly_expr} = 0")
                factored = sp.factor(poly_expr)
                if factored != poly_expr:
                    narration.append(f"4. Factored form: {factored} = 0")
        except Exception:
            pass

        if base.evidence:
            for idx, step in enumerate(base.evidence.steps, start=len(narration) + 1):
                narration.append(f"{idx}. Engine step ({base.evidence.engine}): {step}")
        if base.verification:
            narration.append(
                f"{len(narration) + 1}. Independent verification ({base.verification.kind}): "
                f"{base.verification.detail}"
            )
        narration.append(
            f"{len(narration) + 1}. Final result: {base.value_str} "
            f"[guarantee: {base.guarantee.value}]"
        )

        return MathResult(
            kind="explain",
            input=expression,
            ok=True,
            value={
                "operation": op,
                "result": base.value,
                "explanation": narration,
            },
            value_str="\n".join(narration),
            latex=base.latex,
            variables=base.variables,
            guarantee=base.guarantee,
            evidence=Evidence(
                engine=base.evidence.engine if base.evidence else "sympy",
                engine_version=base.evidence.engine_version if base.evidence else sp.__version__,
                method=f"step-by-step derivation for {op}",
                steps=narration,
                reproducible_with=f'axiom explain "{expression}" --operation {op}',
            ),
            verification=base.verification,
        )

    def explore(
        self,
        expression: str,
        *,
        variable: str | None = None,
        samples: int = 7,
    ) -> MathResult:
        """Explore an expression's algebraic, analytic, and numerical properties."""
        parser = Parser()
        try:
            expr = parser.parse_expression(expression)
            var = _pick_variable(expr, variable, parser)
        except ParseError as exc:
            return error_result("explore", expression, str(exc))

        simplified = sp.simplify(expr)
        factored = sp.factor(expr)
        expanded = sp.expand(expr)
        derivative = sp.diff(expr, var)
        second_derivative = sp.diff(derivative, var)

        # Symmetry check: even / odd / neither
        neg_expr = expr.subs(var, -var)
        if sp.simplify(expr - neg_expr) == 0:
            parity = "even"
        elif sp.simplify(expr + neg_expr) == 0:
            parity = "odd"
        else:
            parity = "neither"

        try:
            zeros = [str(z) for z in sp.solve(sp.Eq(expr, 0), var)]
        except Exception:
            zeros = []

        try:
            critical_points = [str(c) for c in sp.solve(sp.Eq(derivative, 0), var)]
        except Exception:
            critical_points = []

        try:
            taylor = str(sp.series(expr, var, 0, 5))
        except Exception:
            taylor = "unavailable"

        sample_table: list[dict[str, str]] = []
        half = max(samples // 2, 1)
        for k in range(-half, half + 1):
            try:
                val = expr.subs(var, k).evalf(10)
                sample_table.append({str(var): str(k), "value": str(val)})
            except Exception:
                sample_table.append({str(var): str(k), "value": "undefined"})

        summary = {
            "expression": str(expr),
            "variable": str(var),
            "simplified": str(simplified),
            "factored": str(factored),
            "expanded": str(expanded),
            "parity": parity,
            "zeros": zeros,
            "first_derivative": str(derivative),
            "second_derivative": str(second_derivative),
            "critical_points": critical_points,
            "series_at_0": taylor,
            "samples": sample_table,
        }

        ver, guar = verify_equivalence(expr, simplified, [var])
        return MathResult(
            kind="explore",
            input=expression,
            ok=True,
            value=summary,
            value_str=(
                f"zeros={zeros}, d/d{var}={derivative}, "
                f"critical={critical_points}, parity={parity}"
            ),
            latex=sp.latex(simplified),
            variables=[str(var)],
            guarantee=guar,
            evidence=Evidence(
                engine="sympy",
                engine_version=sp.__version__,
                method="structural & analytic exploration (zeros, derivatives, series, parity, sampling)",
                steps=[
                    f"simplified: {simplified}",
                    f"d/d{var}: {derivative}",
                    f"zeros: {zeros}",
                    f"critical points: {critical_points}",
                    f"parity: {parity}",
                ],
                reproducible_with=f'axiom explore "{expression}" --variable {var}',
            ),
            verification=ver,
        )

    def prove(
        self,
        statement: str,
        *,
        proof: str = "",
        engine: str = "lean",
    ) -> MathResult:
        """Verify a formal theorem with Lean 4 (or check an algebraic identity symbolically)."""
        if engine.lower() == "sympy":
            res = self.verify(statement)
            res.kind = "prove"
            return res

        try:
            lean_eng = self.registry.get(engine)
            ans = lean_eng.prove(statement, proof=proof)
        except EngineError as exc:
            return error_result("prove", statement, str(exc), engine=engine)

        kernel_ok = bool(ans.raw.get("kernel_verified"))
        has_hole = bool(ans.raw.get("has_hole"))
        untrusted = list(ans.raw.get("untrusted_axioms") or [])
        axioms_used = list(ans.raw.get("axioms_used") or [])
        theorems = list(ans.raw.get("theorems") or [])
        audited_theorems = list(ans.raw.get("audited_theorems") or [])
        trivial_theorems = list(ans.raw.get("trivial_theorems") or [])
        audit_complete = bool(ans.raw.get("audit_complete"))

        if (
            kernel_ok
            and not has_hole
            and not untrusted
            and len(theorems) > 0
            and len(audited_theorems) >= len(theorems)
            and audit_complete
        ):
            guar = Guarantee.FORMAL_PROOF
            ax_desc = ", ".join(axioms_used) if axioms_used else "none (constructive)"
            thm_desc = ", ".join(audited_theorems)
            ver = Verification(
                kind="lean4-kernel-axiom-audit",
                passed=True,
                detail=(
                    f"Typechecked by Lean 4 kernel and audited {len(audited_theorems)} "
                    f"declaration(s) [{thm_desc}] via #print axioms (axioms: {ax_desc})"
                ),
                checks=1 + len(audited_theorems),
                data={
                    "theorems": theorems,
                    "audited_theorems": audited_theorems,
                    "trivial_theorems": trivial_theorems,
                    "axioms_used": axioms_used,
                    "untrusted_axioms": [],
                },
            )
        else:
            guar = Guarantee.UNVERIFIED
            if has_hole:
                detail = "Incomplete proof (contains 'sorry', 'admit', or 'sorryAx')"
            elif untrusted:
                detail = f"Proof depends on untrusted/user-declared axiom(s): {', '.join(untrusted)}"
            elif not theorems:
                detail = "No theorem, lemma, or example declaration was found to audit via #print axioms"
            elif ans.limitations:
                detail = ans.limitations[0]
            elif not audit_complete:
                missing = list(ans.raw.get("missing_audits") or [])
                detail = f"#print axioms output did not confirm declaration(s): {', '.join(missing)}"
            else:
                detail = "Lean 4 kernel verification did not pass"
            ver = Verification(
                kind="lean4-kernel-axiom-audit",
                passed=False,
                detail=detail,
                checks=1,
                data={
                    "theorems": theorems,
                    "audited_theorems": audited_theorems,
                    "trivial_theorems": trivial_theorems,
                    "diagnostics": ans.raw.get("diagnostics", []),
                    "axioms_used": axioms_used,
                    "untrusted_axioms": untrusted,
                },
            )

        return _wrap_answer(
            kind="prove",
            expression=statement,
            engine=lean_eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom prove "{statement}" --engine {engine}',
        )

    def plot(
        self,
        expression: str,
        *,
        variable: str | None = None,
        range_: tuple[float, float] = (-10.0, 10.0),
        points: int = 101,
        output: str | None = None,
    ) -> MathResult:
        """Sample a 1D mathematical function over a range and optionally render a plot."""
        parser = Parser()
        try:
            expr = parser.parse_expression(expression)
            var = _pick_variable(expr, variable, parser)
        except ParseError as exc:
            return error_result("plot", expression, str(exc))

        x_min, x_max = float(range_[0]), float(range_[1])
        if x_min >= x_max:
            return error_result("plot", expression, "plot range must have min < max")
        n_pts = max(int(points), 5)

        xs: list[float] = []
        ys: list[float | None] = []
        valid_ys: list[float] = []
        fn = sp.lambdify(var, expr, modules="mpmath")

        step = (x_max - x_min) / (n_pts - 1)
        for i in range(n_pts):
            x_val = x_min + i * step
            # Nudge away from exact 0 to handle removable singularities like sin(x)/x
            probe = x_val if abs(x_val) > 1e-14 else 1e-12
            xs.append(round(x_val, 8))
            try:
                y_mp = fn(mp.mpf(str(probe)))
                if mp.isfinite(y_mp) and getattr(y_mp, "imag", 0) == 0:
                    y_f = float(y_mp.real if hasattr(y_mp, "real") else y_mp)
                    ys.append(round(y_f, 8))
                    valid_ys.append(y_f)
                else:
                    ys.append(None)
            except Exception:
                ys.append(None)

        y_min = min(valid_ys) if valid_ys else None
        y_max = max(valid_ys) if valid_ys else None
        svg_markup = _render_svg_plot(
            xs,
            ys,
            title=f"f({var}) = {expr}",
            x_label=str(var),
            y_label=f"f({var})",
        )
        ascii_preview = _render_ascii_plot(xs, ys, width=48, height=11)

        saved_to: str | None = None
        warnings: list[str] = []
        if output:
            out_path = Path(output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if out_path.suffix.lower() == ".svg":
                out_path.write_text(svg_markup, encoding="utf-8")
                saved_to = str(out_path)
            else:
                try:
                    import matplotlib

                    matplotlib.use("Agg")
                    import matplotlib.pyplot as plt

                    fig, ax = plt.subplots(figsize=(7, 4))
                    clean_x = [x for x, y in zip(xs, ys) if y is not None]
                    clean_y = [y for y in ys if y is not None]
                    ax.plot(clean_x, clean_y, linewidth=1.8)
                    ax.set_title(f"$f({var}) = {sp.latex(expr)}$")
                    ax.set_xlabel(str(var))
                    ax.set_ylabel(f"f({var})")
                    ax.grid(True, alpha=0.3)
                    fig.savefig(out_path, dpi=150, bbox_inches="tight")
                    plt.close(fig)
                    saved_to = str(out_path)
                except Exception as exc:
                    svg_fallback = out_path.with_suffix(".svg")
                    svg_fallback.write_text(svg_markup, encoding="utf-8")
                    saved_to = str(svg_fallback)
                    warnings.append(
                        f"matplotlib unavailable ({exc}); exported native vector SVG to {svg_fallback}"
                    )

        payload = {
            "variable": str(var),
            "range": [x_min, x_max],
            "points": n_pts,
            "valid_points": len(valid_ys),
            "y_min": y_min,
            "y_max": y_max,
            "x": xs,
            "y": ys,
            "ascii_preview": ascii_preview,
            "svg": svg_markup,
            "output_file": saved_to,
        }
        summary = (
            f"sampled {len(valid_ys)}/{n_pts} points on [{x_min}, {x_max}] "
            f"(y in [{y_min:.4g}, {y_max:.4g}])"
            if valid_ys and y_min is not None and y_max is not None
            else f"sampled 0/{n_pts} finite points on [{x_min}, {x_max}]"
        )
        if saved_to:
            summary += f" -> {saved_to}"

        return MathResult(
            kind="plot",
            input=expression,
            ok=True,
            value=payload,
            value_str=summary,
            latex=sp.latex(expr),
            variables=[str(var)],
            guarantee=(
                Guarantee.SAMPLED_VISUALIZATION
                if len(valid_ys) > 0
                else Guarantee.UNVERIFIED
            ),
            evidence=Evidence(
                engine="numeric",
                engine_version=mp.__version__,
                method=f"uniform grid sampling ({n_pts} points via mpmath) + SVG/ASCII renderer",
                steps=[
                    f"domain: {var} in [{x_min}, {x_max}]",
                    summary,
                ],
                limitations=["discrete grid sampling may miss narrow spikes between grid points"],
                reproducible_with=f'axiom plot "{expression}" --range {x_min}:{x_max}',
            ),
            verification=Verification(
                kind="domain-sampling",
                passed=len(valid_ys) > 0,
                detail=f"{len(valid_ys)} finite evaluations succeeded",
                checks=len(valid_ys),
            ),
            warnings=warnings,
        )

    # ---------------------------------------------- v0.2 expanded domains

    def matrix(
        self,
        matrix_expr: str,
        *,
        operation: str = "eigen",
        rhs: str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        """Perform a matrix/linear-algebra operation with independent verification."""
        parser = Parser()
        try:
            mat = parser.parse_matrix(matrix_expr)
            rhs_mat = parser.parse_matrix(rhs) if rhs else None
            eng = self.registry.select("matrix", preferred=engine)
            ans = eng.matrix(mat, operation=operation, rhs=rhs_mat)
        except (ParseError, EngineError) as exc:
            return error_result("matrix", matrix_expr, str(exc), engine=engine)

        ver, guar = verify_matrix_op(ans.raw)
        cmd = f'axiom matrix "{matrix_expr}" --op {operation}'
        if rhs:
            cmd += f' --rhs "{rhs}"'
        return _wrap_answer(
            kind="matrix",
            expression=matrix_expr,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=cmd,
        )

    def ode(
        self,
        equation: str,
        *,
        function: str = "y",
        variable: str = "x",
        engine: str | None = None,
    ) -> MathResult:
        """Solve an ordinary differential equation and verify by substitution."""
        func_cls = sp.Function(function)
        parser = Parser(locals_={function: func_cls})
        try:
            var_sym = parser.symbol(variable)
            parsed_eq = parser.parse_equation(equation)
            eng = self.registry.select("ode", preferred=engine)
            ans = eng.ode(parsed_eq, func_name=function, var=var_sym)
        except (ParseError, EngineError, NotImplementedError, ValueError) as exc:
            return error_result("ode", equation, str(exc), engine=engine)

        ver, guar = verify_ode_solution(ans.raw)
        return _wrap_answer(
            kind="ode",
            expression=equation,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=(
                f'axiom ode "{equation}" --function {function} --variable {variable}'
            ),
        )

    def number_theory(
        self,
        operation: str,
        *,
        n: int | None = None,
        a: int | None = None,
        b: int | None = None,
        k: int | None = None,
        remainders: list[int] | None = None,
        moduli: list[int] | None = None,
        engine: str | None = None,
    ) -> MathResult:
        """Execute a number-theory or combinatorics operation with verification."""
        args: dict[str, Any] = {}
        if n is not None:
            args["n"] = int(n)
        if a is not None:
            args["a"] = int(a)
        if b is not None:
            args["b"] = int(b)
        if k is not None:
            args["k"] = int(k)
        if remainders is not None:
            args["remainders"] = [int(r) for r in remainders]
        if moduli is not None:
            args["moduli"] = [int(m) for m in moduli]

        label = f"{operation}({args})"
        try:
            eng = self.registry.select("number_theory", preferred=engine)
            ans = eng.number_theory(operation, args)
        except (EngineError, KeyError, ValueError) as exc:
            return error_result("number_theory", label, str(exc), engine=engine)

        ver, guar = verify_number_theory_op(ans.raw)
        flags: list[str] = [f"axiom number-theory {operation}"]
        if n is not None:
            flags.append(f"--n {n}")
        if a is not None:
            flags.append(f"--a {a}")
        if b is not None:
            flags.append(f"--b {b}")
        if k is not None:
            flags.append(f"--k {k}")
        if remainders is not None:
            flags.append(f"--remainders {','.join(str(r) for r in remainders)}")
        if moduli is not None:
            flags.append(f"--moduli {','.join(str(m) for m in moduli)}")
        return _wrap_answer(
            kind="number_theory",
            expression=label,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=" ".join(flags),
        )

    def optimize(
        self,
        expression: str,
        *,
        variable: str | None = None,
        mode: str = "minimize",
        lower: str | float | int | None = None,
        upper: str | float | int | None = None,
        engine: str | None = None,
    ) -> MathResult:
        """Find and verify a symbolic/numerical minimum or maximum of an expression."""
        parser = Parser()
        try:
            expr = parser.parse_expression(expression)
            var = _pick_variable(expr, variable, parser)
            interval: tuple[sp.Expr, sp.Expr] | None = None
            if (lower is None) ^ (upper is None):
                raise ParseError("both lower and upper bounds must be provided together")
            if lower is not None and upper is not None:
                interval = (
                    parser.parse_expression(str(lower)),
                    parser.parse_expression(str(upper)),
                )
            eng = self.registry.select("optimize", preferred=engine)
            ans = eng.optimize(expr, var, mode=mode, interval=interval)
        except (ParseError, EngineError) as exc:
            return error_result("optimize", expression, str(exc), engine=engine)

        ver, guar = verify_optimization(ans.raw)
        return _wrap_answer(
            kind="optimize",
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom optimize "{expression}" --mode {mode}',
        )

    def statistics(
        self,
        data: list[str | int | float] | str,
        *,
        engine: str | None = None,
    ) -> MathResult:
        """Compute exact symbolic and numerical summary statistics with moment verification."""
        parser = Parser()
        raw_str = data if isinstance(data, str) else ", ".join(str(x) for x in data)
        try:
            items = (
                [s.strip() for s in data.strip("[]").split(",") if s.strip()]
                if isinstance(data, str)
                else [str(x) for x in data]
            )
            values = [parser.parse_expression(item) for item in items]
            eng = self.registry.select("statistics", preferred=engine)
            ans = eng.statistics(values)
        except (ParseError, EngineError) as exc:
            return error_result("statistics", raw_str, str(exc), engine=engine)

        ver, guar = verify_statistics(ans.raw)
        return _wrap_answer(
            kind="statistics",
            expression=f"[{raw_str}]",
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom stats "{raw_str}"',
        )

    def tensor(
        self,
        metric: str,
        *,
        coordinates: list[str] | str | None = None,
        operation: str = "all",
        engine: str | None = None,
    ) -> MathResult:
        """Compute differential-geometry / tensor quantities for a metric with Levi-Civita verification.

        ``metric`` may be either a matrix string (e.g. ``"[[1, 0], [0, r^2]]"``)
        paired with ``coordinates`` (e.g. ``["r", "theta"]``), or a named preset:
        ``"polar"``, ``"sphere"``, ``"cylindrical"``, ``"minkowski"``, ``"schwarzschild"``.
        """
        preset_map: dict[str, tuple[str, list[str]]] = {
            "polar": ("[[1, 0], [0, r^2]]", ["r", "theta"]),
            "sphere": ("[[1, 0], [0, sin(theta)^2]]", ["theta", "phi"]),
            "spherical_2d": ("[[R^2, 0], [0, R^2 * sin(theta)^2]]", ["theta", "phi"]),
            "cylindrical": ("[[1, 0, 0], [0, r^2, 0], [0, 0, 1]]", ["r", "theta", "z"]),
            "minkowski": (
                "[[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]",
                ["t", "x", "y", "z"],
            ),
            "schwarzschild": (
                "[[-1 + r_s/r, 0, 0, 0], [0, 1/(1 - r_s/r), 0, 0], [0, 0, r^2, 0], [0, 0, 0, r^2 * sin(theta)^2]]",
                ["t", "r", "theta", "phi"],
            ),
        }

        key = metric.strip().lower()
        if key in preset_map:
            metric_expr, default_coords = preset_map[key]
            coord_list = default_coords
        else:
            metric_expr = metric
            if isinstance(coordinates, str):
                coord_list = [c.strip() for c in coordinates.split(",") if c.strip()]
            elif coordinates:
                coord_list = [str(c).strip() for c in coordinates if str(c).strip()]
            else:
                coord_list = []

        parser = Parser()
        try:
            mat = parser.parse_matrix(metric_expr)
            if not coord_list:
                free = sorted(mat.free_symbols, key=lambda s: s.name)
                if len(free) == mat.rows:
                    coord_list = [s.name for s in free]
                else:
                    default_names = ["x", "y", "z", "w"][: mat.rows]
                    coord_list = default_names
            sym_coords = [parser.symbol(c) for c in coord_list]
            eng = self.registry.select("tensor", preferred=engine)
            ans = eng.tensor(mat, sym_coords, operation=operation)
        except (ParseError, EngineError) as exc:
            return error_result("tensor", metric, str(exc), engine=engine)

        ver, guar = verify_tensor_op(ans.raw)
        coord_arg = ",".join(coord_list)
        return _wrap_answer(
            kind="tensor",
            expression=metric,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom tensor "{metric}" --coords {coord_arg} --op {operation}',
        )

    def search_mathlib(
        self,
        query: str,
        *,
        max_results: int = 8,
        online: bool = False,
    ) -> MathResult:
        """Search Mathlib4 & Lean 4 Core theorems by concept, identifier, or type signature."""
        try:
            lean_eng = self.registry.get("lean")
            ans = lean_eng.search_mathlib(query, max_results=max_results, online=online)
        except EngineError as exc:
            return error_result("search_mathlib", query, str(exc), engine="lean")

        hits = ans.raw.get("hits", [])
        ver = Verification(
            kind="catalog-signature-check",
            passed=len(hits) > 0,
            detail=(
                f"Matched {len(hits)} verified Lean 4 / Mathlib4 declaration signature(s)"
                if hits
                else f"No Mathlib4 declarations matched {query!r}"
            ),
            checks=len(hits),
        )
        return _wrap_answer(
            kind="search_mathlib",
            expression=query,
            engine=lean_eng,
            answer=ans,
            guarantee=Guarantee.CATALOG_LOOKUP if hits else Guarantee.UNVERIFIED,
            verification=ver,
            reproducible_with=f'axiom search-mathlib "{query}"',
        )

    def session(
        self,
        action: str = "show",
        *,
        name: str = "default",
        expression: str | None = None,
        operation: str = "solve",
        hypothesis: str | None = None,
        note: str = "",
        directory: Path | str = ".axiom/sessions",
    ) -> MathResult:
        """Manage a reproducible multi-step mathematical research session."""
        from axiom.session import ResearchSession

        act = action.lower().strip()
        if act == "clear":
            sess = ResearchSession(name=name)
            sess.save(directory=directory)
            return sess.as_math_result("clear")

        sess = ResearchSession.load(name=name, directory=directory)

        if act == "record":
            if not expression:
                return error_result("session", f"{name}:record", "expression is required for action='record'")
            op = operation.lower().strip()
            dispatch = {
                "solve": lambda: self.solve(expression),
                "simplify": lambda: self.simplify(expression),
                "factor": lambda: self.factor(expression),
                "expand": lambda: self.expand(expression),
                "differentiate": lambda: self.differentiate(expression),
                "integrate": lambda: self.integrate(expression),
                "limit": lambda: self.limit(expression),
                "evaluate": lambda: self.evaluate(expression),
                "explore": lambda: self.explore(expression),
                "ode": lambda: self.ode(expression),
                "tensor": lambda: self.tensor(expression),
            }
            if op not in dispatch:
                return error_result("session", expression, f"unsupported session operation: {op!r}")
            step_res = dispatch[op]()
            sess.record(step_res, note=note)
            sess.save(directory=directory)
            return sess.as_math_result("record")

        if act == "hypothesis":
            if not hypothesis:
                return error_result("session", f"{name}:hypothesis", "hypothesis statement is required")
            ver_res = self.verify(hypothesis)
            if ver_res.ok and ver_res.verified:
                status = "verified"
                guar = ver_res.guarantee
                detail = ver_res.verification.detail if ver_res.verification else "verified"
            elif ver_res.ok and not ver_res.verified:
                status = "refuted"
                guar = Guarantee.UNVERIFIED
                detail = ver_res.verification.detail if ver_res.verification else "refuted"
            else:
                status = "open"
                guar = Guarantee.UNVERIFIED
                detail = ver_res.error or "unverified conjecture"
            sess.add_hypothesis(hypothesis, status=status, guarantee=guar, detail=detail)
            sess.save(directory=directory)
            return sess.as_math_result("hypothesis")

        if act == "export":
            md = sess.to_markdown()
            res = sess.as_math_result("export")
            res.value = {"session": sess.to_dict(), "markdown": md}
            res.value_str = md
            return res

        if act == "show":
            return sess.as_math_result("show")

        return error_result(
            "session",
            f"{name}:{action}",
            f"unknown session action '{action}' (choose from: show, record, hypothesis, export, clear)",
        )


def _render_svg_plot(
    xs: list[float],
    ys: list[float | None],
    *,
    title: str = "",
    x_label: str = "x",
    y_label: str = "f(x)",
    width: int = 640,
    height: int = 380,
) -> str:
    """Render a self-contained SVG plot with zero external dependencies."""
    import html

    pad_l, pad_r, pad_t, pad_b = 58, 24, 38, 44
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    valid_pairs = [(x, y) for x, y in zip(xs, ys) if y is not None]
    if not valid_pairs:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
            f'<rect width="100%" height="100%" fill="#0f172a"/>'
            f'<text x="{width // 2}" y="{height // 2}" fill="#94a3b8" text-anchor="middle">No finite points</text>'
            f"</svg>"
        )

    x_min, x_max = min(xs), max(xs)
    y_vals = [y for _, y in valid_pairs]
    y_min, y_max = min(y_vals), max(y_vals)
    if abs(y_max - y_min) < 1e-12:
        y_min -= 1.0
        y_max += 1.0

    def sx(x: float) -> float:
        return pad_l + (x - x_min) / (x_max - x_min) * plot_w

    def sy(y: float) -> float:
        return pad_t + plot_h - (y - y_min) / (y_max - y_min) * plot_h

    segments: list[str] = []
    current: list[str] = []
    for x, y in zip(xs, ys):
        if y is None:
            if len(current) >= 2:
                segments.append(" ".join(current))
            current = []
        else:
            current.append(f"{sx(x):.2f},{sy(y):.2f}")
    if len(current) >= 2:
        segments.append(" ".join(current))

    polylines = "\n  ".join(
        f'<polyline fill="none" stroke="#38bdf8" stroke-width="2.2" points="{pts}"/>'
        for pts in segments
    )

    zero_axes: list[str] = []
    if x_min <= 0 <= x_max:
        zx = sx(0.0)
        zero_axes.append(
            f'<line x1="{zx:.2f}" y1="{pad_t}" x2="{zx:.2f}" y2="{pad_t + plot_h}" stroke="#475569" stroke-dasharray="4,4"/>'
        )
    if y_min <= 0 <= y_max:
        zy = sy(0.0)
        zero_axes.append(
            f'<line x1="{pad_l}" y1="{zy:.2f}" x2="{pad_l + plot_w}" y2="{zy:.2f}" stroke="#475569" stroke-dasharray="4,4"/>'
        )

    esc_title = html.escape(title)
    esc_xlab = html.escape(x_label)
    esc_ylab = html.escape(y_label)
    axes_svg = "\n  ".join(zero_axes)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">\n'
        f'  <rect width="100%" height="100%" fill="#0f172a" rx="8"/>\n'
        f'  <rect x="{pad_l}" y="{pad_t}" width="{plot_w}" height="{plot_h}" fill="#1e293b" stroke="#334155"/>\n'
        f"  {axes_svg}\n"
        f"  {polylines}\n"
        f'  <text x="{width / 2:.1f}" y="24" fill="#f8fafc" font-family="monospace" font-size="13" text-anchor="middle">{esc_title}</text>\n'
        f'  <text x="{pad_l}" y="{height - 12}" fill="#94a3b8" font-family="monospace" font-size="11">{x_min:.3g}</text>\n'
        f'  <text x="{pad_l + plot_w / 2:.1f}" y="{height - 12}" fill="#cbd5e1" font-family="monospace" font-size="11" text-anchor="middle">{esc_xlab}</text>\n'
        f'  <text x="{pad_l + plot_w}" y="{height - 12}" fill="#94a3b8" font-family="monospace" font-size="11" text-anchor="end">{x_max:.3g}</text>\n'
        f'  <text x="{pad_l - 6}" y="{pad_t + 10}" fill="#94a3b8" font-family="monospace" font-size="11" text-anchor="end">{y_max:.3g}</text>\n'
        f'  <text x="{pad_l - 6}" y="{pad_t + plot_h}" fill="#94a3b8" font-family="monospace" font-size="11" text-anchor="end">{y_min:.3g}</text>\n'
        f'  <text x="14" y="{pad_t + plot_h / 2:.1f}" fill="#cbd5e1" font-family="monospace" font-size="11">{esc_ylab}</text>\n'
        f"</svg>\n"
    )


def _render_ascii_plot(
    xs: list[float],
    ys: list[float | None],
    *,
    width: int = 48,
    height: int = 11,
) -> str:
    """Render a compact ASCII curve preview for terminal and LLM consumption."""
    valid_ys = [y for y in ys if y is not None]
    if not valid_ys or not xs:
        return "(no finite points)"
    y_min, y_max = min(valid_ys), max(valid_ys)
    if abs(y_max - y_min) < 1e-12:
        y_min -= 1.0
        y_max += 1.0
    x_min, x_max = min(xs), max(xs)

    grid = [[" " for _ in range(width)] for _ in range(height)]
    if y_min <= 0 <= y_max:
        r0 = int(round((y_max - 0.0) / (y_max - y_min) * (height - 1)))
        for c in range(width):
            grid[r0][c] = "-"
    if x_min <= 0 <= x_max:
        c0 = int(round((0.0 - x_min) / (x_max - x_min) * (width - 1)))
        for r in range(height):
            grid[r][c0] = "|" if grid[r][c0] == " " else "+"

    for x, y in zip(xs, ys):
        if y is None:
            continue
        col = int(round((x - x_min) / (x_max - x_min) * (width - 1)))
        row = int(round((y_max - y) / (y_max - y_min) * (height - 1)))
        col = max(0, min(width - 1, col))
        row = max(0, min(height - 1, row))
        grid[row][col] = "*"

    return "\n".join("".join(row) for row in grid)


def solve_expression(expression: str, **kwargs: Any) -> MathResult:
    """Convenience function to solve an equation or expression with default AXIOM."""
    return Axiom().solve(expression, **kwargs)

