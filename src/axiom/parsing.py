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
    ast.Eq: sp.Eq,
    ast.NotEq: sp.Ne,
}

_LONE_EQUALS = re.compile(r"(?<![=<>!])=(?!=)")
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
    return text


class Parser:
    """Converts text into SymPy objects without executing code."""

    def __init__(self, symbols: dict[str, sp.Symbol] | None = None,
                 locals_: dict[str, object] | None = None):
        self.symbols: dict[str, sp.Symbol] = dict(symbols or {})
        self.locals: dict[str, object] = dict(locals_ or {})
        self.functions = {
            name: getattr(sp, name)
            for name in _FUNCTIONS
            if getattr(sp, name, None) is not None
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
            self.symbols[name] = sp.Symbol(name)
        return self.symbols[name]

    # ------------------------------------------------------------- internals

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
            return op(self._sym(node.left), self._sym(node.right))
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
