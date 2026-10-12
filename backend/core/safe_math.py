"""Avaliador matemático restrito para expressões e células do console SymPy.

Substitui o uso de ``eval``/``exec`` por conversão direta da AST, permitindo
apenas construções matemáticas: números, símbolos, operadores, chamadas de
funções SymPy da lista de permissões e métodos matemáticos conhecidos.

Nenhuma entrada do usuário é executada como código Python. Strings só fluem
para funções que as tratam como *nomes de símbolos* (``symbols``, ``Symbol``,
``Function``, ``Wild``, ``Dummy``) ou para ``print``; para qualquer outra
função permitida, strings são pré-processadas por este mesmo avaliador e
nunca chegam ao ``sympify`` (que usa ``eval`` internamente).
"""

import ast
import re
import types

import sympy as sp


class UnsafeExpressionError(ValueError):
    """Entrada usa construções fora da DSL matemática permitida."""


# Funções SymPy permitidas (matemática pura). Nomes ausentes no sympy
# instalado são simplesmente ignorados na montagem do namespace.
_FUNCTION_NAMES = (
    # Trigonometria
    "sin", "cos", "tan", "cot", "sec", "csc",
    "asin", "acos", "atan", "atan2", "acot", "asec", "acsc",
    "sinh", "cosh", "tanh", "asinh", "acosh", "atanh",
    # Exponencial / logaritmo / raízes / arredondamento
    "exp", "log", "sqrt", "root", "Abs", "sign", "floor", "ceiling",
    "Min", "Max", "gamma", "factorial", "binomial", "zeta",
    "re", "im", "arg", "conjugate", "Heaviside", "Piecewise",
    # Cálculo e álgebra
    "diff", "integrate", "solve", "solveset", "linsolve", "dsolve", "nsolve",
    "simplify", "trigsimp", "radsimp", "ratsimp", "expand", "factor",
    "collect", "apart", "together", "cancel", "limit", "series",
    "summation", "product", "refine", "reduce_inequalities", "nsimplify",
    # Matrizes
    "Matrix", "eye", "zeros", "ones", "diag", "transpose",
    # Construtores de símbolos/números
    "symbols", "Symbol", "Function", "Wild", "Dummy",
    "Integer", "Rational", "Float",
    # Relações e lógica
    "Eq", "Ne", "Lt", "Le", "Gt", "Ge", "And", "Or", "Not", "Xor",
    "Sum", "Product", "Integral", "Derivative",
)

_MATH_FUNCTIONS = {
    name: getattr(sp, name)
    for name in _FUNCTION_NAMES
    if getattr(sp, name, None) is not None
}

_MATH_CONSTANTS = {
    "pi": sp.pi, "E": sp.E, "e": sp.E, "I": sp.I,
    "oo": sp.oo, "zoo": sp.zoo, "nan": sp.nan,
}

# Atributos permitidos no módulo sympy (sp.<attr>).
_SP_ATTRS = set(_MATH_FUNCTIONS) | set(_MATH_CONSTANTS)

# Funções que recebem strings como *nomes* (nunca como expressão matemática).
_STRING_ARG_FUNCS = {"symbols", "Symbol", "Function", "Wild", "Dummy"}

# Nomes de símbolos: identificadores (unicode) com ":" para ranges
# (ex.: ``symbols('x:5')``). Sem metacaracteres de HTML/JS — o nome chega
# ao ``sp.latex`` e, sem validação, permitiria injeção de HTML no console.
_SYMBOL_NAME_RE = re.compile(r"[\w:]+")
_SYMBOL_SPLIT_RE = re.compile(r"[\s,]+")


def _validate_symbol_names(value, func_name):
    """Valida strings usadas como nomes de símbolos/funções SymPy."""
    if isinstance(value, str):
        for name in _SYMBOL_SPLIT_RE.split(value):
            if name and not _SYMBOL_NAME_RE.fullmatch(name):
                raise UnsafeExpressionError(
                    f"Nome de símbolo inválido em {func_name}: {name!r}")
    elif isinstance(value, (list, tuple)):
        for item in value:
            _validate_symbol_names(item, func_name)

# Métodos/propriedades matemáticas permitidos em objetos SymPy.
_ALLOWED_METHODS = {
    "T", "cross", "dot", "subs", "evalf", "n", "simplify", "trigsimp",
    "radsimp", "ratsimp", "diff", "integrate", "limit", "series", "expand",
    "factor", "collect", "together", "apart", "cancel", "rewrite", "refine",
    "doit", "inv", "det", "norm", "shape", "rank", "rref", "transpose",
    "conjugate", "adjugate", "eigenvals", "eigenvects", "diagonalize",
    "rows", "cols", "row", "col", "sum", "product", "applyfunc", "reshape",
    "as_real_imag", "coeff", "coeffs", "args", "free_symbols", "is_number",
    "xreplace", "has", "match", "matches", "count", "round", "nsimplify",
}

_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a ** b,
    ast.Mod: lambda a, b: a % b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.BitXor: lambda a, b: a ** b,  # x^2 == x**2, como no sympify
    ast.MatMult: lambda a, b: a @ b,
}

_COMPARES = {
    ast.Lt: sp.StrictLessThan,
    ast.LtE: sp.LessThan,
    ast.Gt: sp.StrictGreaterThan,
    ast.GtE: sp.GreaterThan,
    ast.Eq: sp.Eq,
    ast.NotEq: sp.Ne,
}


class SafeMathEvaluator:
    """Converte strings/células em objetos SymPy sem executar código Python."""

    def __init__(self, session=None, stdout=None):
        self.session = session if session is not None else {}
        self.stdout = stdout
        self.modules = {"sp": sp, "sympy": sp}
        self.functions = dict(_MATH_FUNCTIONS)
        if stdout is not None:
            def _print(*args, sep=" ", end="\n", file=None, flush=False):
                print(*args, sep=sep, end=end, file=stdout, flush=flush)
            self.functions["print"] = _print

    # ------------------------------------------------------------------ API

    def parse_expression(self, text):
        """Converte uma única expressão matemática em objeto SymPy."""
        if not isinstance(text, str):
            return sp.sympify(text) if not isinstance(text, (sp.Basic,)) else text
        tree = ast.parse(text.strip(), mode="eval")
        return self._as_expr(self._convert(tree.body))

    def execute_cell(self, code):
        """Executa uma célula do console na DSL restrita.

        Retorna o valor da última expressão avaliada (ou ``None``).
        """
        tree = ast.parse(code, mode="exec")
        last_value = None
        for stmt in tree.body:
            value = self._exec_statement(stmt)
            if isinstance(stmt, ast.Expr):
                last_value = value
        return last_value

    # ----------------------------------------------------------- statements

    def _exec_statement(self, stmt):
        if isinstance(stmt, ast.Expr):
            return self._convert(stmt.value)
        if isinstance(stmt, ast.Assign):
            value = self._convert(stmt.value)
            for target in stmt.targets:
                self._bind(target, value)
            return None
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                if alias.name != "sympy":
                    raise UnsafeExpressionError(
                        f"Import não permitido: {alias.name!r} (apenas 'sympy')")
                self.modules[alias.asname or alias.name] = sp
            return None
        if isinstance(stmt, ast.ImportFrom):
            if stmt.module != "sympy" or stmt.level != 0:
                raise UnsafeExpressionError(
                    f"Import não permitido: {stmt.module!r} (apenas 'sympy')")
            for alias in stmt.names:
                if alias.name not in _SP_ATTRS:
                    raise UnsafeExpressionError(
                        f"Nome não permitido em 'from sympy': {alias.name!r}")
                self.session[alias.asname or alias.name] = getattr(sp, alias.name)
            return None
        raise UnsafeExpressionError(
            f"Construção não permitida: {type(stmt).__name__}")

    def _bind(self, target, value):
        if isinstance(target, ast.Name):
            if target.id.startswith("_"):
                raise UnsafeExpressionError(
                    f"Nome de variável não permitido: {target.id!r}")
            if isinstance(value, types.ModuleType):
                self.modules[target.id] = value
            else:
                self.session[target.id] = value
        elif isinstance(target, (ast.Tuple, ast.List)):
            try:
                values = list(value)
            except TypeError:
                raise UnsafeExpressionError(
                    "Não é possível desempacotar valor não iterável")
            if len(values) != len(target.elts):
                raise UnsafeExpressionError(
                    f"Desempacotamento com tamanho incorreto: "
                    f"esperado {len(target.elts)}, obtido {len(values)}")
            for sub, val in zip(target.elts, values):
                self._bind(sub, val)
        else:
            raise UnsafeExpressionError(
                f"Alvo de atribuição não permitido: {type(target).__name__}")

    # ---------------------------------------------------------- expressions

    def _convert(self, node):
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, bool) or value is None:
                return value
            if isinstance(value, (int, float, complex)):
                return sp.sympify(value)
            if isinstance(value, str):
                return value
            raise UnsafeExpressionError("Constante não permitida")
        if isinstance(node, ast.Name):
            return self._resolve_name(node.id)
        if isinstance(node, ast.Tuple):
            return tuple(self._convert(e) for e in node.elts)
        if isinstance(node, ast.List):
            return [self._convert(e) for e in node.elts]
        if isinstance(node, ast.Dict):
            if any(k is None for k in node.keys):
                raise UnsafeExpressionError("Expansão ** não permitida")
            return {self._convert(k): self._convert(v)
                    for k, v in zip(node.keys, node.values)}
        if isinstance(node, ast.BinOp):
            op = _BINOPS.get(type(node.op))
            if op is None:
                raise UnsafeExpressionError(
                    f"Operador não permitido: {type(node.op).__name__}")
            return op(self._as_expr(self._convert(node.left)),
                      self._as_expr(self._convert(node.right)))
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.UAdd):
                return +self._as_expr(self._convert(node.operand))
            if isinstance(node.op, ast.USub):
                return -self._as_expr(self._convert(node.operand))
            raise UnsafeExpressionError(
                f"Operador unário não permitido: {type(node.op).__name__}")
        if isinstance(node, ast.Compare):
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise UnsafeExpressionError("Comparação encadeada não permitida")
            op = _COMPARES.get(type(node.ops[0]))
            if op is None:
                raise UnsafeExpressionError(
                    f"Comparação não permitida: {type(node.ops[0]).__name__}")
            return op(self._as_expr(self._convert(node.left)),
                      self._as_expr(self._convert(node.comparators[0])))
        if isinstance(node, ast.Call):
            return self._convert_call(node)
        if isinstance(node, ast.Attribute):
            return self._convert_attribute(node)
        if isinstance(node, ast.Subscript):
            value = self._as_expr(self._convert(node.value))
            sl = node.slice
            if isinstance(sl, ast.Slice):
                lower = self._convert(sl.lower) if sl.lower else None
                upper = self._convert(sl.upper) if sl.upper else None
                step = self._convert(sl.step) if sl.step else None
                return value[lower:upper:step]
            return value[self._as_expr(self._convert(sl))]
        raise UnsafeExpressionError(
            f"Construção não permitida: {type(node).__name__}")

    def _resolve_name(self, name):
        if name.startswith("_"):
            raise UnsafeExpressionError(f"Nome não permitido: {name!r}")
        if name in self.session:
            return self.session[name]
        if name in self.functions:
            return self.functions[name]
        if name in _MATH_CONSTANTS:
            return _MATH_CONSTANTS[name]
        if name in self.modules:
            return self.modules[name]
        # Como o _ensure_symbols original: identificadores desconhecidos
        # viram símbolos.
        symbol = sp.Symbol(name)
        self.session[name] = symbol
        return symbol

    def _convert_attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id in self.modules:
            if node.attr in _SP_ATTRS:
                return getattr(sp, node.attr)
            raise UnsafeExpressionError(
                f"Atributo não permitido no módulo sympy: {node.attr!r}")
        if node.attr.startswith("_"):
            raise UnsafeExpressionError(f"Atributo não permitido: {node.attr!r}")
        if node.attr in _ALLOWED_METHODS:
            base = self._as_expr(self._convert(node.value))
            return getattr(base, node.attr)
        raise UnsafeExpressionError(f"Atributo não permitido: {node.attr!r}")

    def _convert_call(self, node):
        if any(isinstance(arg, ast.Starred) for arg in node.args):
            raise UnsafeExpressionError("Expansão * não permitida")
        if any(kw.arg is None for kw in node.keywords):
            raise UnsafeExpressionError("Expansão ** não permitida")
        func, func_name = self._resolve_callable(node.func)
        args = [self._preparse(self._convert(arg), func_name)
                for arg in node.args]
        kwargs = {kw.arg: self._preparse(self._convert(kw.value), func_name)
                  for kw in node.keywords}
        return func(*args, **kwargs)

    def _resolve_callable(self, node):
        if isinstance(node, ast.Name):
            name = node.id
            if name.startswith("_"):
                raise UnsafeExpressionError(f"Nome não permitido: {name!r}")
            if name in self.session:
                value = self.session[name]
                if callable(value):
                    return value, name
                raise UnsafeExpressionError(f"{name!r} não é chamável")
            if name in self.functions:
                return self.functions[name], name
            raise UnsafeExpressionError(f"Função não permitida: {name!r}")
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id in self.modules:
                if node.attr in _SP_ATTRS:
                    return getattr(sp, node.attr), node.attr
                raise UnsafeExpressionError(
                    f"Atributo não permitido no módulo sympy: {node.attr!r}")
            if node.attr.startswith("_"):
                raise UnsafeExpressionError(
                    f"Atributo não permitido: {node.attr!r}")
            if node.attr in _ALLOWED_METHODS:
                base = self._as_expr(self._convert(node.value))
                attr = getattr(base, node.attr)
                if not callable(attr):
                    raise UnsafeExpressionError(f"{node.attr!r} não é chamável")
                return attr, node.attr
            raise UnsafeExpressionError(f"Método não permitido: {node.attr!r}")
        raise UnsafeExpressionError(
            f"Chamada não permitida: {type(node).__name__}")

    # --------------------------------------------------------------- helpers

    def _as_expr(self, value):
        """Garante que strings virem expressões antes de operações SymPy."""
        if isinstance(value, str):
            return self.parse_expression(value)
        return value

    def _preparse(self, value, func_name):
        """Pré-processa strings (e coleções) antes de funções permitidas.

        Strings nunca chegam como estão a funções SymPy que poderiam
        encaminhá-las ao ``sympify``/``eval``; exceto as funções que tratam
        strings como nomes de símbolos e o ``print``.
        """
        if func_name in _STRING_ARG_FUNCS:
            _validate_symbol_names(value, func_name)
            return value
        if func_name == "print":
            return value
        if isinstance(value, str):
            return self.parse_expression(value)
        if isinstance(value, list):
            return [self._preparse(v, func_name) for v in value]
        if isinstance(value, tuple):
            return tuple(self._preparse(v, func_name) for v in value)
        if isinstance(value, dict):
            return {self._preparse(k, func_name): self._preparse(v, func_name)
                    for k, v in value.items()}
        return value
