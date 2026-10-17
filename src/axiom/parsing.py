"""Safe mathematical parsing.

User input never reaches ``eval``/``exec`` or ``sympify``. Text is parsed with
:mod:`ast` and converted node by node into SymPy objects, using an allowlist of
functions, constants and attributes. Unknown identifiers become symbols.

Conveniences for agents:

* ``x^2`` behaves like ``x**2``;
* ``=`` builds an equation (``x^2 - 5*x + 6 = 0``);
* implicit multiplication (``2x``, ``3(x+1)``, ``(x+1)(x-1)``).
"""

from __future__ import annotations

import ast
import re

import sympy as sp

__all__ = ["ParseError", "Parser", "parse", "parse_equation"]


class ParseError(ValueError):
    """Input is not a valid expression in the AXIOM mathematical grammar."""


_FUNCTIONS = (
    # trigonometry
    "sin", "cos", "tan", "cot", "sec", "csc",
    "asin", "acos", "atan", "atan2", "acot", "asec", "acsc",
    "sinh", "cosh", "tanh", "asinh", "acosh", "atanh",
    # exponential / logarithm / roots / rounding
    "exp", "log", "sqrt", "root", "Abs", "sign", "floor", "ceiling",
    "Min", "Max", "gamma", "factorial", "binomial", "zeta",
    "re", "im", "arg", "conjugate", "Heaviside", "Piecewise",
    # algebra / calculus
    "diff", "integrate", "solve", "solveset", "linsolve",
    "simplify", "trigsimp", "radsimp", "ratsimp", "expand", "factor",
    "collect", "apart", "together", "cancel", "limit", "series",
    "summation", "product", "nsimplify",
    # matrices
    "Matrix", "eye", "zeros", "ones", "diag", "transpose",
    # constructors
    "symbols", "Symbol", "Function",
    # numbers
    "Integer", "Rational", "Float",
    # relations
    "Eq", "Ne", "Lt", "Le", "Gt", "Ge", "And", "Or", "Not", "Xor",
    "Sum", "Product", "Integral", "Derivative",
)

_CONSTANTS: dict[str, object] = {
    "pi": sp.pi, "E": sp.E, "e": sp.E, "I": sp.I,
    "oo": sp.oo, "zoo": sp.zoo, "nan": sp.nan, "phi": sp.GoldenRatio,
}

_STRING_ARG_FUNCS = {"symbols", "Symbol", "Function"}
_RAW_STR_ARG_FUNCS = {"Float", "Rational"}

_BINOPS: dict[type, object] = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a ** b,
    ast.Mod: lambda a, b: a % b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.BitXor: lambda a, b: a ** b,  # x^2 == x**2
    ast.MatMult: lambda a, b: a @ b,
}

_COMPARES: dict[type, object] = {
    ast.Lt: sp.StrictLessThan,
    ast.LtE: sp.LessThan,
    ast.Gt: sp.StrictGreaterThan,
    ast.GtE: sp.GreaterThan,
    ast.Eq: lambda a, b: sp.Eq(a, b, evaluate=False),
    ast.NotEq: lambda a, b: sp.Ne(a, b, evaluate=False),
}

_LONE_EQUALS = re.compile(r"(?<![=<>!])=(?!=)")
_HIGH_PREC_DECIMAL = re.compile(r"(?<![A-Za-z0-9_.'])(\d+\.\d{14,})(?![A-Za-z0-9_.']|[eE])")
_IMPLICIT_MUL = (
    (re.compile(r"(?<=[0-9])(?=[A-Za-z_(])"), "*"),      # 2x, 2(, 2sin
    (re.compile(r"(?<=\))(?=\()"), "*"),                  # )(
    (re.compile(r"(?<=\))(?=[A-Za-z0-9])"), "*"),         # )x, )2
)
_SYMBOL_NAME = re.compile(r"[\w:]+")


def _normalize(text: str) -> str:
    text = text.strip()
    if not text:
        raise ParseError("empty expression")
    text = text.replace("^", "**")
    for pattern, repl in _IMPLICIT_MUL:
        text = pattern.sub(repl, text)
    text = _HIGH_PREC_DECIMAL.sub(
        lambda m: f"Float('{m.group(1)}', {len(m.group(1).replace('.', ''))})",
        text,
    )
    return text


_ALLOWED_ASSUMPTIONS = frozenset(
    {
        "real",
        "positive",
        "negative",
        "nonnegative",
        "nonpositive",
        "nonzero",
        "integer",
        "rational",
        "prime",
        "even",
        "odd",
        "complex",
        "commutative",
        "finite",
    }
)

_CONTRADICTORY_PAIRS = (
    ("positive", "negative"),
    ("positive", "nonpositive"),
    ("negative", "nonnegative"),
    ("even", "odd"),
)


def _parse_assumption_spec(spec: object) -> dict[str, bool]:
    """Normalize an assumption specification (string, list, or dict) into SymPy keyword flags."""
    flags: dict[str, bool] = {}
    if isinstance(spec, str):
        for tok in re.split(r"[\s,&;]+", spec.strip()):
            if not tok:
                continue
            neg = tok.startswith(("!", "~", "not_"))
            clean = tok.lstrip("!~").removeprefix("not_").lower()
            if clean not in _ALLOWED_ASSUMPTIONS:
                raise ParseError(f"unsupported assumption flag: {tok!r}")
            flags[clean] = not neg
    elif isinstance(spec, dict):
        for k, v in spec.items():
            clean = str(k).lower().strip()
            if clean not in _ALLOWED_ASSUMPTIONS:
                raise ParseError(f"unsupported assumption flag: {k!r}")
            flags[clean] = bool(v)
    elif isinstance(spec, (list, tuple, set)):
        for item in spec:
            flags.update(_parse_assumption_spec(item))
    for a, b in _CONTRADICTORY_PAIRS:
        if flags.get(a) is True and flags.get(b) is True:
            raise ParseError(f"contradictory assumptions: {a!r} and {b!r}")
    return flags


def _root_matches_symbol_assumptions(sym: sp.Symbol, val: sp.Expr) -> bool:
    """Return True if candidate point ``val`` belongs to the declared domain of ``sym``."""
    if sym.is_real is True and val.is_real is False:
        return False
    if sym.is_positive is True:
        if val.is_real is False or not bool(val.is_positive):
            return False
    if sym.is_negative is True:
        if val.is_real is False or not bool(val.is_negative):
            return False
    if sym.is_nonnegative is True:
        if val.is_real is False or bool(val.is_negative):
            return False
    if sym.is_nonpositive is True:
        if val.is_real is False or bool(val.is_positive):
            return False
    if sym.is_nonzero is True and (val == 0 or val is sp.S.Zero):
        return False
    if sym.is_integer is True and not bool(val.is_integer):
        return False
    if sym.is_even is True and not (bool(val.is_integer) and int(val) % 2 == 0):
        return False
    if sym.is_odd is True and not (bool(val.is_integer) and int(val) % 2 == 1):
        return False
    return True


def extract_expression_excluded_points(expr: sp.Basic) -> dict[str, list[str]]:
    """Extract single-variable denominator excluded points still present in a SymPy expression."""
    excluded: dict[str, list[str]] = {}
    if not isinstance(expr, sp.Basic):
        return excluded
    denoms: list[sp.Expr] = []
    try:
        _, d = sp.fraction(expr)
        if d != 1 and d.free_symbols:
            denoms.append(d)
        for sub in sp.preorder_traversal(expr):
            if isinstance(sub, sp.Pow) and sub.exp.is_number and sub.exp.is_real and sub.exp < 0:
                if sub.base.free_symbols:
                    denoms.append(sub.base)
    except Exception:
        pass
    for denom in denoms:
        if len(denom.free_symbols) == 1:
            sym = next(iter(denom.free_symbols))
            try:
                roots = sp.solve(sp.Eq(denom, 0), sym)
            except Exception:
                roots = []
            for r in roots:
                if _root_matches_symbol_assumptions(sym, r):
                    r_str = str(sp.simplify(r))
                    bucket = excluded.setdefault(str(sym), [])
                    if r_str not in bucket:
                        bucket.append(r_str)
    return excluded


class Parser:
    """Converts text into SymPy objects without executing code."""

    def __init__(
        self,
        symbols: dict[str, sp.Symbol] | None = None,
        locals_: dict[str, object] | None = None,
        assumptions: dict[str, object] | str | None = None,
    ):
        self.symbols: dict[str, sp.Symbol] = dict(symbols or {})
        self.locals: dict[str, object] = dict(locals_ or {})
        self.default_assumptions: dict[str, bool] = {}
        self.symbol_assumptions: dict[str, dict[str, bool]] = {}
        self.denominators: list[sp.Expr] = []
        self.domain_constraints: list[str] = []
        self._load_assumptions(assumptions)
        self.functions = {
            name: getattr(sp, name)
            for name in _FUNCTIONS
            if getattr(sp, name, None) is not None
        }

    def _load_assumptions(self, assumptions: dict[str, object] | str | None) -> None:
        if assumptions is None:
            return
        if isinstance(assumptions, str):
            raw = assumptions.strip()
            if not raw:
                return
            if raw.startswith("{") and raw.endswith("}"):
                import json

                try:
                    parsed_json = json.loads(raw)
                    if isinstance(parsed_json, dict):
                        self._load_assumptions(parsed_json)
                        return
                except Exception as exc:
                    raise ParseError(f"invalid JSON assumptions: {exc}") from exc
            if ":" in raw:
                segments = re.split(r";|,(?=\s*[A-Za-z_]\w*\s*:)", raw)
                for seg in segments:
                    seg = seg.strip()
                    if not seg:
                        continue
                    if ":" in seg:
                        sym_name, spec_str = seg.split(":", 1)
                        self.symbol_assumptions[sym_name.strip()] = _parse_assumption_spec(
                            spec_str.strip()
                        )
                    else:
                        self.default_assumptions.update(_parse_assumption_spec(seg))
                return
            self.default_assumptions = _parse_assumption_spec(raw)
            return
        if isinstance(assumptions, dict):
            for sym_name, spec in assumptions.items():
                if sym_name in _ALLOWED_ASSUMPTIONS and isinstance(spec, bool):
                    self.default_assumptions[sym_name] = spec
                else:
                    self.symbol_assumptions[str(sym_name)] = _parse_assumption_spec(spec)

    def describe_assumptions(self) -> dict[str, object]:
        """Return a human-readable dictionary of declared domain assumptions."""
        out: dict[str, object] = {}
        if self.default_assumptions:
            out["*"] = dict(self.default_assumptions)
        for name, flags in sorted(self.symbol_assumptions.items()):
            out[name] = dict(flags)
        for name, sym in sorted(self.symbols.items()):
            if name not in out and self.default_assumptions:
                out[name] = dict(self.default_assumptions)
        return out

    @property
    def seen_symbols(self) -> set[sp.Symbol]:
        """All symbols instantiated or encountered by this parser."""
        return set(self.symbols.values())

    def domain_info(self, variables: Any = None) -> dict[str, Any]:
        """Compute syntactic domain constraints and excluded points captured before simplification."""
        excluded_points: dict[str, list[str]] = {}
        active_constraints: list[str] = []
        for denom in self.denominators:
            c_str = f"{denom} != 0"
            if len(denom.free_symbols) == 1:
                sym = next(iter(denom.free_symbols))
                try:
                    roots = sp.solve(sp.Eq(denom, 0), sym)
                except Exception:
                    roots = []
                matched_any = False
                for r in roots:
                    if _root_matches_symbol_assumptions(sym, r):
                        matched_any = True
                        r_str = str(sp.simplify(r))
                        bucket = excluded_points.setdefault(str(sym), [])
                        if r_str not in bucket:
                            bucket.append(r_str)
                if matched_any or not roots:
                    if c_str not in active_constraints:
                        active_constraints.append(c_str)
            elif denom.free_symbols:
                if c_str not in active_constraints:
                    active_constraints.append(c_str)
        return {
            "domain_constraints": list(self.domain_constraints),
            "active_domain_constraints": active_constraints,
            "excluded_points": excluded_points,
            "assumptions": self.describe_assumptions(),
        }

    # ------------------------------------------------------------------ API

    def parse(self, text: str):
        """Parse an expression, relation or equation."""
        tree = self._tree(text)
        return self._expr(tree.body)

    def parse_expression(self, text: str) -> sp.Expr:
        """Parse a plain expression (a bare relation becomes its lhs)."""
        obj = self.parse(text)
        if isinstance(obj, sp.Equality):
            return obj.lhs - obj.rhs
        if isinstance(obj, sp.Rel):
            raise ParseError(f"expected an expression, got a relation: {text!r}")
        return obj

    def parse_equation(self, text: str) -> sp.Equality | sp.Rel:
        """Parse an equation; a bare expression is read as ``expr = 0``."""
        obj = self.parse(text)
        if isinstance(obj, sp.Rel):
            return obj
        return sp.Eq(obj, 0)

    def parse_matrix(self, text: str) -> sp.Matrix:
        """Parse a matrix literal ``[[1, 2], [3, 4]]`` or ``Matrix(...)``."""
        obj = self.parse(text)
        if isinstance(obj, sp.MatrixBase):
            return sp.Matrix(obj)
        if isinstance(obj, (list, tuple)):
            try:
                return sp.Matrix(obj)
            except Exception as exc:
                raise ParseError(f"invalid matrix literal: {exc}") from exc
        raise ParseError(f"expected a matrix or list of rows, got: {text!r}")

    def symbol(self, name: str) -> sp.Symbol:
        if not _SYMBOL_NAME.fullmatch(name or ""):
            raise ParseError(f"invalid variable name: {name!r}")
        if name not in self.symbols:
            flags = dict(self.default_assumptions)
            if name in self.symbol_assumptions:
                flags.update(self.symbol_assumptions[name])
            for a, b in _CONTRADICTORY_PAIRS:
                if flags.get(a) is True and flags.get(b) is True:
                    raise ParseError(f"contradictory assumptions for {name!r}: {a!r} and {b!r}")
            try:
                self.symbols[name] = sp.Symbol(name, **flags)
            except Exception as exc:
                raise ParseError(f"invalid assumptions for symbol {name!r}: {exc}") from exc
        return self.symbols[name]

    # ------------------------------------------------------------- internals

    def _record_denominator(self, denom: object) -> None:
        if isinstance(denom, sp.Basic) and denom.free_symbols:
            constraint = f"{denom} != 0"
            if constraint not in self.domain_constraints:
                self.domain_constraints.append(constraint)
                self.denominators.append(denom)

    def _tree(self, text: str) -> ast.Expression:
        normalized = _normalize(_LONE_EQUALS.sub("==", text))
        try:
            return ast.parse(normalized, mode="eval")
        except SyntaxError as exc:
            raise ParseError(f"cannot parse {text!r}: {exc.msg}") from exc

    def _expr(self, node: ast.AST):
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, bool) or value is None:
                return value
            if isinstance(value, (int, float, complex)):
                return sp.sympify(value)
            if isinstance(value, str):
                return value
            raise ParseError("unsupported constant")
        if isinstance(node, ast.Name):
            return self._resolve(node.id)
        if isinstance(node, ast.Tuple):
            return tuple(self._expr(e) for e in node.elts)
        if isinstance(node, ast.List):
            return [self._expr(e) for e in node.elts]
        if isinstance(node, ast.BinOp):
            op = _BINOPS.get(type(node.op))
            if op is None:
                raise ParseError(f"operator not allowed: {type(node.op).__name__}")
            left_val = self._sym(node.left)
            right_val = self._sym(node.right)
            if isinstance(node.op, ast.Div):
                self._record_denominator(right_val)
            elif isinstance(node.op, (ast.Pow, ast.BitXor)):
                if (
                    isinstance(right_val, sp.Basic)
                    and right_val.is_number
                    and right_val.is_real
                    and right_val < 0
                ):
                    self._record_denominator(left_val)
            return op(left_val, right_val)
        if isinstance(node, ast.UnaryOp):
            value = self._sym(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +value
            if isinstance(node.op, ast.USub):
                return -value
            raise ParseError(f"operator not allowed: {type(node.op).__name__}")
        if isinstance(node, ast.Compare):
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise ParseError("chained comparisons are not allowed")
            op = _COMPARES.get(type(node.ops[0]))
            if op is None:
                raise ParseError(f"comparison not allowed: {type(node.ops[0]).__name__}")
            return op(self._sym(node.left), self._sym(node.comparators[0]))
        if isinstance(node, ast.Call):
            return self._call(node)
        raise ParseError(f"construct not allowed: {type(node).__name__}")

    def _call(self, node: ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ParseError("only direct calls to allowed functions are supported")
        name = node.func.id
        if name.startswith("_"):
            raise ParseError(f"name not allowed: {name!r}")
        func = self.locals.get(name) or self.functions.get(name)
        if func is None or not callable(func):
            raise ParseError(f"function not allowed: {name!r}")
        args = [self._prepare(self._expr(a), name) for a in node.args]
        kwargs = {kw.arg: self._prepare(self._expr(kw.value), name)
                  for kw in node.keywords if kw.arg}
        if name in ("tan", "sec") and len(args) == 1:
            self._record_denominator(sp.cos(args[0]))
        elif name in ("cot", "csc") and len(args) == 1:
            self._record_denominator(sp.sin(args[0]))
        elif name == "log" and len(args) >= 1:
            self._record_denominator(args[0])
        return func(*args, **kwargs)

    def _resolve(self, name: str):
        if name.startswith("_"):
            raise ParseError(f"name not allowed: {name!r}")
        if name in self.locals:
            return self.locals[name]
        if name in self.functions:
            return self.functions[name]
        if name in _CONSTANTS:
            return _CONSTANTS[name]
        return self.symbol(name)

    def _sym(self, node: ast.AST):
        """Convert, turning raw strings into expressions before algebra."""
        value = self._expr(node)
        if isinstance(value, str):
            return self.parse_expression(value)
        return value

    def _prepare(self, value, func_name: str):
        if func_name in _STRING_ARG_FUNCS:
            self._validate_symbol_names(value, func_name)
            return value
        if func_name in _RAW_STR_ARG_FUNCS and isinstance(value, str):
            return value
        if isinstance(value, str):
            return self.parse_expression(value)
        if isinstance(value, list):
            return [self._prepare(v, func_name) for v in value]
        if isinstance(value, tuple):
            return tuple(self._prepare(v, func_name) for v in value)
        return value

    @staticmethod
    def _validate_symbol_names(value, func_name: str) -> None:
        if isinstance(value, str):
            for name in re.split(r"[\s,]+", value):
                if name and not _SYMBOL_NAME.fullmatch(name):
                    raise ParseError(
                        f"invalid symbol name in {func_name}: {name!r}")
        elif isinstance(value, (list, tuple)):
            for item in value:
                Parser._validate_symbol_names(item, func_name)


def parse(text: str, **kwargs):
    """Parse ``text`` with a fresh :class:`Parser`."""
    return Parser(**kwargs).parse(text)


def parse_equation(text: str, **kwargs):
    """Parse ``text`` as an equation, defaulting to ``expr = 0``."""
    return Parser(**kwargs).parse_equation(text)

