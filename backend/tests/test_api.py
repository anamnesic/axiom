"""Integration tests for all API endpoints.

Tests use httpx AsyncClient against a fresh FastAPI app instance.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost:8080") as ac:
        yield ac


pytestmark = pytest.mark.asyncio(loop_scope="module")


class TestHealthEndpoint:
    """Feature: Diagnóstico — health check"""

    async def test_health_returns_ok(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "engines" in data
        assert data["engines"]["sympy"]["status"] == "ok"


class TestSolveAPI:
    """Feature: Manipulação Simbólica (SymPy) via REST"""

    async def test_solve_quadratic(self, client):
        resp = await client.post("/api/v1/solve", json={"expression": "x**2 - 4", "variable": "x"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert "-2" in data["solutions"]
        assert "2" in data["solutions"]

    async def test_evaluate(self, client):
        resp = await client.post("/api/v1/solve/evaluate", json={"expression": "sin(pi/2)"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True

    async def test_simplify(self, client):
        resp = await client.post("/api/v1/solve/simplify", json={"expression": "sin(x)**2 + cos(x)**2"})
        assert resp.status_code == 200
        data = resp.json()
        assert "1" in data["result"]

    async def test_differentiate(self, client):
        resp = await client.post("/api/v1/solve/differentiate", json={"expression": "x**3", "variable": "x", "order": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert "3*x**2" in data["result"]

    async def test_integrate(self, client):
        resp = await client.post("/api/v1/solve/integrate", json={"expression": "x**2", "variable": "x"})
        assert resp.status_code == 200
        data = resp.json()
        assert "x**3/3" in data["result"]

    async def test_integrate_definite(self, client):
        resp = await client.post("/api/v1/solve/integrate", json={"expression": "x", "variable": "x", "lower": 0, "upper": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert "1/2" in data["result"]

    async def test_expand(self, client):
        resp = await client.post("/api/v1/solve/expand", json={"expression": "(x + 1)**2"})
        assert resp.status_code == 200
        data = resp.json()
        assert "x**2" in data["result"]

    async def test_factor(self, client):
        resp = await client.post("/api/v1/solve/factor", json={"expression": "x**2 - 4"})
        assert resp.status_code == 200
        data = resp.json()
        assert "(x - 2)" in data["result"]

    async def test_limit(self, client):
        resp = await client.post("/api/v1/solve/limit", json={"expression": "sin(x)/x"}, params={"variable": "x", "point": "0"})
        assert resp.status_code == 200
        data = resp.json()
        assert "1" in data["result"]

    async def test_exec_code(self, client):
        resp = await client.post("/api/v1/solve/exec", json={"code": "x = 1\ny = 2\nx + y"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "exec"

    async def test_exec_session_chain(self, client):
        """Sessão exec deve preservar estado entre chamadas."""
        # Reset first
        await client.post("/api/v1/solve/reset")
        # Cell 1
        c1 = await client.post("/api/v1/solve/exec", json={"code": "a, b, t = sp.symbols('a b t')\nsp.Matrix([a, b, t])"})
        assert c1.status_code == 200
        # Cell 2 — uses variables from cell 1
        c2 = await client.post("/api/v1/solve/exec", json={"code": "sp.diff(sp.Matrix([a, b, t]), t)"})
        assert c2.status_code == 200
        data = c2.json()
        assert data["type"] == "exec"

    async def test_reset_session(self, client):
        resp = await client.post("/api/v1/solve/reset")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    async def test_symbols(self, client):
        resp = await client.get("/api/v1/solve/symbols")
        assert resp.status_code == 200
        data = resp.json()
        assert "symbols" in data

    async def test_sympy_to_lean(self, client):
        resp = await client.post("/api/v1/solve/sympy-to-lean", json={"expression": "x**2", "theorem_name": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert "theorem" in data


class TestExplainAPI:
    """Feature: Explicador Multinível via REST"""

    async def test_explain_medio(self, client):
        resp = await client.post("/api/v1/explain", json={"expression": "derivative", "level": "medio"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["level"] == "medio"
        assert len(data["explanation"]) > 50

    async def test_explain_graduacao(self, client):
        resp = await client.post("/api/v1/explain", json={"expression": "integral", "level": "graduacao"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["level"] == "graduacao"
        assert "Teorema Fundamental" in data["explanation"]

    async def test_explain_posgraduacao(self, client):
        resp = await client.post("/api/v1/explain", json={"expression": "derivative", "level": "posgraduacao"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["level"] == "posgraduacao"
        assert "Fréchet" in data["explanation"] or "Banach" in data["explanation"]

    async def test_explain_invalid_level(self, client):
        resp = await client.post("/api/v1/explain", json={"expression": "derivative", "level": "invalido"})
        assert resp.status_code == 400


class TestVerifyAPI:
    """Feature: Verificação Formal (Lean 4) via REST"""

    async def test_verify_templates(self, client):
        resp = await client.get("/api/v1/verify/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["templates"]) >= 4

    async def test_verify_proof(self, client):
        resp = await client.post("/api/v1/verify", json={
            "theorem": "theorem t : 1 = 1 :=",
            "proof": "by rfl",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "verified" in data

    async def test_sympy_to_lean_endpoint(self, client):
        resp = await client.post("/api/v1/verify/sympy-to-lean", json={
            "expression": "sin(x)**2 + cos(x)**2 = 1",
            "theorem_name": "trig_id",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "theorem" in data or "lean_expression" in data

    async def test_extract_goal(self, client):
        resp = await client.post("/api/v1/verify/extract-goal", json={
            "theorem": "theorem ex (x : ℝ) : x = x :=",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "context" in data
        assert "target" in data


class TestTemplatesAPI:
    """Feature: Templates de conteúdo para frontend"""

    async def test_editor_template(self, client):
        resp = await client.get("/api/v1/templates/editor")
        assert resp.status_code == 200
        data = resp.json()
        assert "content" in data
        assert "filename" in data
        assert data["filename"].endswith(".tex")

    async def test_sympy_session(self, client):
        resp = await client.get("/api/v1/templates/sympy/session")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["cells"]) == 5

    async def test_lean_theorem(self, client):
        resp = await client.get("/api/v1/templates/lean/theorem")
        assert resp.status_code == 200
        data = resp.json()
        assert "code" in data
        assert "helix_curvature" in data["code"]

    async def test_explainer_content(self, client):
        resp = await client.get("/api/v1/templates/explainer/content")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["steps"]) == 4

    async def test_quiz_check_correct(self, client):
        resp = await client.post("/api/v1/templates/quiz/check", json={
            "question": "For the helix γ(t) = (4 cos t, 4 sin t, 3 t), what is the curvature κ?",
            "answer": "A",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["correct"] is True

    async def test_quiz_check_wrong(self, client):
        resp = await client.post("/api/v1/templates/quiz/check", json={
            "question": "For the helix γ(t) = (4 cos t, 4 sin t, 3 t), what is the curvature κ?",
            "answer": "B",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["correct"] is False


class TestExportAPI:
    """Feature: Exportação PDF via REST"""

    async def test_export_pdf(self, client):
        resp = await client.post("/api/v1/export", json={"content": "# Hello", "format": "pdf"})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["ok"] is True

    async def test_export_invalid_format(self, client):
        resp = await client.post("/api/v1/export", json={"content": "# Hello", "format": "docx"})
        assert resp.status_code == 400
