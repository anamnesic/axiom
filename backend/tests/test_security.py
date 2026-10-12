"""Testes de regressão de segurança — o engine nunca deve executar código Python.

Estes testes garantem que entradas maliciosas (RCE, traversal de atributos,
imports perigosos, eval/exec/sympify) sejam rejeitadas pelo avaliador
restrito, enquanto expressões matemáticas legítimas continuam funcionando.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from httpx import AsyncClient, ASGITransport

from backend.core.safe_math import UnsafeExpressionError
from backend.main import app


pytestmark_api = pytest.mark.asyncio(loop_scope="module")


MALICIOUS_CELLS = [
    "__import__('os').system('echo pwned')",
    "import os",
    "from os import system",
    "import subprocess",
    "open('/etc/passwd')",
    "exec('1 + 1')",
    "eval('1 + 1')",
    "x = lambda: 1",
    "[i for i in range(3)]",
    "for i in [1]:\n    pass",
    "while True:\n    pass",
    "def f():\n    pass",
    "class A:\n    pass",
    "sp.sympify('1 + 1')",
    "sp.parse_expr('1 + 1')",
    "sp.lambdify('x', 'x**2')",
    "sp.python('x**2')",
    "sp.var('x')",
    "getattr(sp, 'sin')",
    "setattr(sp, 'x', 1)",
    "().__class__",
    "(1).__class__.__bases__[0].__subclasses__()",
    "sp.Symbol('x').__class__",
    "sp.__dict__",
    "import sympy as sp\nsp.os",
    "globals()",
    "locals()",
    "__builtins__",
    "x = __import__('os')",
    "import sympy as sp2\nsp2.utilities",
]

MALICIOUS_EXPRESSIONS = [
    "().__class__",
    "(1).__class__.__bases__",
    "__import__('os')",
    "[x for x in (1,)]",
    "lambda: 1",
    "open('/etc/passwd')",
    "sp.sympify('1')",
    "getattr(sp, 'sin')",
    "sp.Symbol('x').__class__",
    "{1: 2}.popitem()",
]


class TestExecuteRejectsMaliciousCode:
    """Células maliciosas devem retornar erro, nunca executar."""

    @pytest.mark.parametrize("code", MALICIOUS_CELLS)
    def test_malicious_cell_returns_error(self, sympy_engine, code):
        result = sympy_engine.execute(code)
        assert result["type"] == "error", f"código perigoso aceito: {code}"
        assert "error" in result

    def test_no_side_effect_from_rejected_code(self, sympy_engine):
        """Código rejeitado não pode deixar variáveis na sessão."""
        sympy_engine.execute("x = __import__('os')")
        assert all(not k.startswith("_") for k in sympy_engine.session)
        # nada deve ter sido criado além de possíveis símbolos automáticos
        assert "x" not in sympy_engine.session or not hasattr(
            sympy_engine.session.get("x"), "system")


class TestEvaluateRejectsMaliciousExpressions:
    """Expressões maliciosas devem levantar UnsafeExpressionError."""

    @pytest.mark.parametrize("expression", MALICIOUS_EXPRESSIONS)
    def test_malicious_expression_raises(self, sympy_engine, expression):
        with pytest.raises(UnsafeExpressionError):
            sympy_engine.evaluate(expression)


class TestLegitimateMathStillWorks:
    """A DSL matemática legítima continua funcionando após a correção."""

    def test_simple_arithmetic(self, sympy_engine):
        result = sympy_engine.evaluate("2 + 3 * 4")
        assert result["result"] == "14"

    def test_functions_and_constants(self, sympy_engine):
        result = sympy_engine.evaluate("sin(pi/2)")
        assert result["result"] == "1"

    def test_caret_as_power(self, sympy_engine):
        result = sympy_engine.evaluate("x^2")
        assert "x**2" in result["result"]

    def test_exec_session_and_import(self, sympy_engine):
        result = sympy_engine.execute("import sympy as sp\nx = 2\nx**2")
        assert result["type"] == "exec"
        assert result["result"] == "4"
        assert "x" in result["session_vars"]

    def test_exec_tuple_unpack(self, sympy_engine):
        result = sympy_engine.execute("a, b = symbols('a b')\na + b")
        assert result["type"] == "exec"
        assert "a" in result["session_vars"] and "b" in result["session_vars"]

    def test_exec_matrix_methods(self, sympy_engine):
        result = sympy_engine.execute(
            "m = sp.Matrix([[1, 2], [3, 4]])\nm.det()")
        assert result["result"] == "-2"

    def test_exec_print(self, sympy_engine):
        result = sympy_engine.execute("print('hello')")
        assert result["type"] == "exec"
        assert "hello" in result["stdout"]

    def test_exec_symbol_kwargs(self, sympy_engine):
        result = sympy_engine.execute(
            "x = symbols('x', positive=True)\nsqrt(x**2)")
        assert result["result"] == "x"

    def test_exec_rational_division(self, sympy_engine):
        result = sympy_engine.execute("y = 1/2\ny")
        assert result["result"] == "1/2"

    def test_exec_from_sympy_import(self, sympy_engine):
        result = sympy_engine.execute("from sympy import sin\nsin(0)")
        assert result["result"] == "0"

    def test_exec_module_alias_binding(self, sympy_engine):
        result = sympy_engine.execute("m = sp\nm.cos(0)")
        assert result["result"] == "1"

    def test_exec_compare(self, sympy_engine):
        result = sympy_engine.execute("x > 2")
        assert result["result"] == "x > 2"

    def test_exec_subscript(self, sympy_engine):
        result = sympy_engine.execute("v = sp.Matrix([1, 2, 3])\nv[0]")
        assert result["result"] == "1"

    def test_exec_rejects_html_in_symbol_name(self, sympy_engine):
        # O nome chega ao sp.latex e daí ao frontend; sem validação,
        # vira injeção de HTML no console (XSS).
        result = sympy_engine.execute(
            "x = Symbol('<img src=x onerror=alert(1)>')\nx")
        assert result["type"] == "error"

    def test_exec_rejects_html_in_function_name(self, sympy_engine):
        result = sympy_engine.execute("f = Function('f<img>')\nf(x)")
        assert result["type"] == "error"

    def test_exec_rejects_html_in_symbols_string(self, sympy_engine):
        result = sympy_engine.execute(
            "v = symbols('a <img src=x onerror=alert(1)> b')\nv")
        assert result["type"] == "error"

    def test_exec_allows_symbol_range_syntax(self, sympy_engine):
        result = sympy_engine.execute("v = symbols('x:3')\nv")
        assert result["type"] == "exec"
        assert "x0" in result["result"] and "x2" in result["result"]

    def test_exec_allows_unicode_symbol_name(self, sympy_engine):
        result = sympy_engine.execute("v = symbols('α')\nv")
        assert result["type"] == "exec"
        assert "α" in result["result"]


@pytest.mark.asyncio(loop_scope="module")
class TestSecurityAPI:
    """A API deve rejeitar entradas maliciosas com HTTP 400."""

    @pytest.fixture
    async def client(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://localhost:8080") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_exec_endpoint_rejects_rce(self, client):
        resp = await client.post(
            "/api/v1/solve/exec",
            json={"code": "__import__('os').system('echo pwned')"},
        )
        # Contrato do endpoint: erros de célula voltam no corpo (type=error),
        # sem executar nada.
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "error"
        assert "error" in data

    @pytest.mark.asyncio
    async def test_evaluate_endpoint_rejects_traversal(self, client):
        resp = await client.post(
            "/api/v1/solve/evaluate",
            json={"expression": "().__class__.__bases__[0].__subclasses__()"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_exec_endpoint_accepts_math(self, client):
        resp = await client.post(
            "/api/v1/solve/exec",
            json={"code": "x = 2\nx**2"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["result"] == "4"

    @pytest.mark.asyncio
    async def test_rejects_foreign_host(self, client):
        # DNS rebinding: Host fora de localhost deve ser rejeitado.
        resp = await client.post(
            "/api/v1/solve/evaluate",
            json={"expression": "1+1"},
            headers={"Host": "evil.example:8080"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_cross_origin_write(self, client):
        resp = await client.post(
            "/api/v1/solve/evaluate",
            json={"expression": "1+1"},
            headers={"Origin": "http://evil.example"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_allows_tauri_origin_write(self, client):
        resp = await client.post(
            "/api/v1/solve/evaluate",
            json={"expression": "1+1"},
            headers={"Origin": "https://tauri.localhost"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_exec_endpoint_rejects_html_symbol_name(self, client):
        resp = await client.post(
            "/api/v1/solve/exec",
            json={"code": "x = Symbol('<img src=x onerror=alert(1)>')\nx"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "error"
