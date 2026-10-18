"""AXIOM Model Context Protocol (MCP) server.

Exposes the 13 composable mathematical tools defined by the AXIOM contract:

* ``math_parse``
* ``math_simplify``
* ``math_solve``
* ``math_differentiate``
* ``math_integrate``
* ``math_limit``
* ``math_evaluate``
* ``math_plot``
* ``math_prove``
* ``math_verify``
* ``math_explain``
* ``math_compare``
* ``math_explore``

Can run either through the official ``mcp`` Python SDK (when installed) or via
the built-in zero-dependency JSON-RPC 2.0 stdio transport so agents can connect
out-of-the-box in any environment.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

from axiom.contract import MathResult, error_result
from axiom.core import Axiom


_ASSUMPTIONS_PROPERTY: dict[str, Any] = {
    "oneOf": [
        {
            "type": "object",
            "description": "Mapping from symbol to assumptions, e.g. {'x': 'positive'} or {'x': {'real': true}}.",
        },
        {
            "type": "string",
            "description": "Assumption string, e.g. 'x:positive' or 'x:real,nonzero;y:positive'.",
        },
    ],
    "description": "Mathematical domain assumptions for variables (e.g. positive, real, integer, nonzero).",
}

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "math_parse",
        "description": (
            "Parse a mathematical expression or equation into a canonical AST, "
            "extracting free variables, structure type, and LaTeX."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression or equation, e.g. 'x^2 - 5*x + 6 = 0'.",
                },
                "assumptions": _ASSUMPTIONS_PROPERTY,
            },
            "required": ["expression"],
        },
    },
    {
        "name": "math_simplify",
        "description": (
            "Simplify, factor, or expand an algebraic/trigonometric expression "
            "with independent equivalence verification."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Expression to simplify."},
                "mode": {
                    "type": "string",
                    "enum": ["simplify", "factor", "expand"],
                    "default": "simplify",
                    "description": "Transformation mode.",
                },
                "assumptions": _ASSUMPTIONS_PROPERTY,
                "engine": {"type": "string", "description": "Optional engine name (default: sympy)."},
            },
            "required": ["expression"],
        },
    },
    {
        "name": "math_solve",
        "description": (
            "Solve an equation (or ';'-separated system of equations) and "
            "independently verify all roots by exact substitution."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Equation or system, e.g. 'x^2 - 5*x + 6 = 0' or 'x + y = 5; x - y = 1'.",
                },
                "variable": {
                    "type": "string",
                    "description": "Variable (or comma-separated variables) to solve for.",
                },
                "assumptions": _ASSUMPTIONS_PROPERTY,
                "engine": {
                    "type": "string",
                    "description": "Engine to use ('sympy' for exact symbolic, 'numeric' for nsolve).",
                },
            },
            "required": ["expression"],
        },
    },
    {
        "name": "math_differentiate",
        "description": (
            "Differentiate an expression symbolically and verify against "
            "high-precision numerical differentiation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Expression to differentiate."},
                "variable": {"type": "string", "description": "Differentiation variable (default: x)."},
                "order": {"type": "integer", "default": 1, "description": "Derivative order (>= 1)."},
                "assumptions": _ASSUMPTIONS_PROPERTY,
            },
            "required": ["expression"],
        },
    },
    {
        "name": "math_integrate",
        "description": (
            "Compute an indefinite or definite integral and verify by "
            "differentiating the antiderivative or comparing with quadrature."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Integrand expression."},
                "variable": {"type": "string", "description": "Integration variable (default: x)."},
                "lower": {"type": "string", "description": "Optional lower limit for definite integral."},
                "upper": {"type": "string", "description": "Optional upper limit for definite integral."},
                "assumptions": _ASSUMPTIONS_PROPERTY,
                "engine": {"type": "string", "description": "Optional engine ('sympy' or 'numeric')."},
            },
            "required": ["expression"],
        },
    },
    {
        "name": "math_limit",
        "description": (
            "Compute the limit of an expression as a variable approaches a point "
            "and verify via numerical sequence probing."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Expression whose limit to take."},
                "variable": {"type": "string", "description": "Variable (default: x)."},
                "point": {"type": "string", "default": "0", "description": "Limit point (e.g. '0', 'oo')."},
                "direction": {
                    "type": "string",
                    "enum": ["+-", "+", "-"],
                    "default": "+-",
                    "description": "Direction of approach.",
                },
                "assumptions": _ASSUMPTIONS_PROPERTY,
            },
            "required": ["expression"],
        },
    },
    {
        "name": "math_evaluate",
        "description": (
            "Evaluate an expression exactly or to arbitrary numerical precision "
            "with optional variable substitutions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Expression to evaluate."},
                "precision": {
                    "type": "integer",
                    "description": "Decimal digits of precision for numerical evaluation.",
                },
                "substitutions": {
                    "type": "object",
                    "description": "Mapping of variable names to values/expressions.",
                },
                "assumptions": _ASSUMPTIONS_PROPERTY,
            },
            "required": ["expression"],
        },
    },
    {
        "name": "math_plot",
        "description": (
            "Sample a 1D mathematical function over a domain [min, max] and "
            "optionally save a plot image."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Function expression to sample/plot."},
                "variable": {"type": "string", "description": "Independent variable (default: x)."},
                "min": {"type": "number", "default": -10.0, "description": "Domain minimum."},
                "max": {"type": "number", "default": 10.0, "description": "Domain maximum."},
                "points": {"type": "integer", "default": 101, "description": "Number of sample points."},
                "output": {"type": "string", "description": "Optional file path to save PNG/SVG plot."},
            },
            "required": ["expression"],
        },
    },
    {
        "name": "math_prove",
        "description": (
            "Check a formal proof using the Lean 4 kernel (or verify a symbolic identity)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "statement": {
                    "type": "string",
                    "description": "Lean 4 theorem statement, path to a .lean file, or symbolic equality.",
                },
                "proof": {"type": "string", "default": "", "description": "Optional Lean 4 proof body."},
                "engine": {"type": "string", "default": "lean", "description": "Engine ('lean' or 'sympy')."},
                "canonical_statement": {
                    "type": "string",
                    "description": "Canonical informal mathematical formulation for anti-drift alignment check.",
                },
                "declared_hypotheses": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Explicitly declared hypotheses to audit against implicit assumptions.",
                },
                "spec_alignment": {
                    "type": "string",
                    "description": "Declared alignment status ('congruent', 'scoped_forced_variant', etc.).",
                },
            },
            "required": ["statement"],
        },
    },
    {
        "name": "math_verify",
        "description": (
            "Independently verify a mathematical claim: candidate roots for an "
            "equation, an identity 'lhs = rhs', or a MathResult JSON payload."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Equation, identity 'lhs = rhs', JSON string, or path to JSON file.",
                },
                "candidate": {
                    "oneOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "string"}},
                    ],
                    "description": "Optional candidate solution(s) to substitute into the equation.",
                },
                "variable": {"type": "string", "description": "Target variable name."},
                "assumptions": _ASSUMPTIONS_PROPERTY,
            },
            "required": ["target"],
        },
    },
    {
        "name": "math_explain",
        "description": (
            "Generate a traceable step-by-step derivation and verification "
            "report for a mathematical operation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Expression or equation."},
                "operation": {
                    "type": "string",
                    "enum": [
                        "solve",
                        "simplify",
                        "factor",
                        "expand",
                        "differentiate",
                        "integrate",
                        "limit",
                        "evaluate",
                    ],
                    "default": "solve",
                },
                "variable": {"type": "string", "description": "Optional variable name."},
            },
            "required": ["expression"],
        },
    },
    {
        "name": "math_compare",
        "description": (
            "Compare two mathematical expressions for equivalence via symbolic "
            "reduction and multi-point counterexample search."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "left": {"type": "string", "description": "Left-hand expression."},
                "right": {"type": "string", "description": "Right-hand expression."},
                "variables": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional explicit variable list.",
                },
                "assumptions": _ASSUMPTIONS_PROPERTY,
            },
            "required": ["left", "right"],
        },
    },
    {
        "name": "math_explore",
        "description": (
            "Explore an expression: simplified/factored/expanded forms, parity, "
            "zeros, first and second derivatives, critical points, Taylor series, and samples."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Expression to explore."},
                "variable": {"type": "string", "description": "Variable to analyze (default: x)."},
                "samples": {"type": "integer", "default": 7, "description": "Number of sample evaluations."},
            },
            "required": ["expression"],
        },
    },
    {
        "name": "math_matrix",
        "description": (
            "Perform linear algebra operations (det, trace, inv, rref, eigen, lu, solve) "
            "on a matrix literal with independent verification."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "matrix": {
                    "type": "string",
                    "description": "Matrix literal, e.g. '[[1, 2], [3, 4]]'.",
                },
                "operation": {
                    "type": "string",
                    "enum": ["eigen", "det", "trace", "inv", "rref", "lu", "solve"],
                    "default": "eigen",
                },
                "rhs": {
                    "type": "string",
                    "description": "Right-hand side vector/matrix when operation is 'solve', e.g. '[[5], [11]]'.",
                },
            },
            "required": ["matrix"],
        },
    },
    {
        "name": "math_ode",
        "description": (
            "Solve an ordinary differential equation symbolically and verify "
            "by substituting the solution back into the ODE."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "equation": {
                    "type": "string",
                    "description": "ODE such as 'diff(y(x), x) + 2*y(x) = exp(x)'.",
                },
                "function": {"type": "string", "default": "y", "description": "Unknown function name."},
                "variable": {"type": "string", "default": "x", "description": "Independent variable."},
            },
            "required": ["equation"],
        },
    },
    {
        "name": "math_number_theory",
        "description": (
            "Execute verified number-theory and combinatorics operations: "
            "factorint, isprime, extgcd, crt, totient, binomial."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["factorint", "isprime", "extgcd", "crt", "totient", "binomial"],
                },
                "n": {"type": "integer", "description": "Integer input for factorint, isprime, totient, binomial."},
                "a": {"type": "integer", "description": "First integer for extgcd."},
                "b": {"type": "integer", "description": "Second integer for extgcd."},
                "k": {"type": "integer", "description": "k parameter for binomial(n, k)."},
                "remainders": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Remainders r_i for Chinese Remainder Theorem (crt).",
                },
                "moduli": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Moduli m_i for Chinese Remainder Theorem (crt).",
                },
            },
            "required": ["operation"],
        },
    },
    {
        "name": "math_optimize",
        "description": (
            "Find and verify minima or maxima of a mathematical expression "
            "via stationary points and neighborhood perturbation checks."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Objective expression."},
                "variable": {"type": "string", "description": "Decision variable (default: x)."},
                "mode": {
                    "type": "string",
                    "enum": ["minimize", "maximize"],
                    "default": "minimize",
                },
                "lower": {"type": "string", "description": "Optional lower bound of interval."},
                "upper": {"type": "string", "description": "Optional upper bound of interval."},
            },
            "required": ["expression"],
        },
    },
    {
        "name": "math_statistics",
        "description": (
            "Compute exact symbolic and numerical summary statistics (mean, median, "
            "population/sample variance and stdev) with algebraic moment verification."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "data": {
                    "oneOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "number"}},
                    ],
                    "description": "Comma-separated values or array of numbers.",
                },
            },
            "required": ["data"],
        },
    },
    {
        "name": "math_session",
        "description": (
            "Record verified mathematical steps and conjectures into a reproducible "
            "research session, tracking the weakest-link guarantee across the chain."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["show", "record", "hypothesis", "export", "clear"],
                    "default": "show",
                },
                "name": {"type": "string", "default": "default", "description": "Session name."},
                "expression": {"type": "string", "description": "Expression to evaluate and record when action='record'."},
                "operation": {"type": "string", "default": "solve", "description": "Operation for action='record'."},
                "hypothesis": {"type": "string", "description": "Conjecture/equality statement for action='hypothesis'."},
                "note": {"type": "string", "default": "", "description": "Optional research note for recorded step."},
            },
            "required": ["action"],
        },
    },
    {
        "name": "math_tensor",
        "description": (
            "Compute differential-geometry and tensor-calculus quantities (inverse metric, "
            "Christoffel symbols, Riemann/Ricci/Einstein tensors, Ricci scalar curvature) "
            "with independent Levi-Civita metric-compatibility verification (nabla_k g_ij = 0)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": (
                        "Metric matrix literal (e.g. '[[1, 0], [0, r^2]]') or preset name "
                        "('polar', 'sphere', 'spherical_2d', 'cylindrical', 'minkowski', 'schwarzschild')."
                    ),
                },
                "coordinates": {
                    "oneOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "string"}},
                    ],
                    "description": "Coordinate symbols (e.g. ['r', 'theta'] or 't,r,theta,phi').",
                },
                "operation": {
                    "type": "string",
                    "enum": ["all", "christoffel", "riemann", "ricci", "scalar", "einstein", "metric"],
                    "default": "all",
                },
            },
            "required": ["metric"],
        },
    },
    {
        "name": "math_search_mathlib",
        "description": (
            "Search Lean 4 / Mathlib4 theorems, type signatures, and tactic hints by "
            "mathematical concept, identifier, or expression pattern."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g. 'binomial square', 'sin^2 + cos^2', 'Nat.add_comm', 'fermat').",
                },
                "max_results": {
                    "type": "integer",
                    "default": 8,
                    "description": "Maximum number of matching declarations to return.",
                },
                "online": {
                    "type": "boolean",
                    "default": False,
                    "description": "Also query the live Loogle Mathlib4 JSON API when True.",
                },
            },
            "required": ["query"],
        },
    },
]


def get_authorized_roots() -> list[Path]:
    """Return authorized directory roots for MCP file reads and writes."""
    roots = [Path.cwd().resolve(), Path(tempfile.gettempdir()).resolve()]
    env_dirs = os.environ.get("AXIOM_ALLOWED_DIRS", "")
    if env_dirs:
        for p in env_dirs.split(os.pathsep):
            if p.strip():
                try:
                    roots.append(Path(p.strip()).resolve())
                except Exception:
                    pass
    return roots


def validate_mcp_path(path_str: str, mode: str = "r") -> tuple[bool, Path | None, str]:
    """Validate that path_str resolves to an authorized directory with permitted access."""
    if not path_str or not isinstance(path_str, str):
        return False, None, "Path cannot be empty"
    try:
        p = Path(path_str).resolve()
    except Exception as exc:
        return False, None, f"Invalid path syntax: {exc}"

    roots = get_authorized_roots()
    is_authorized = any(p == r or r in p.parents for r in roots)
    if not is_authorized:
        return (
            False,
            p,
            f"Permission denied: path '{path_str}' is outside authorized MCP directories {roots}",
        )

    if mode == "r":
        if not p.exists():
            return False, p, f"File not found: '{path_str}'"
        if not p.is_file():
            return False, p, f"Path is not a regular file: '{path_str}'"
    elif mode == "w":
        if p.exists() and p.is_dir():
            return False, p, f"Path is an existing directory, not a file target: '{path_str}'"
        parent = p.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                return False, p, f"Cannot create directory for path '{path_str}': {exc}"
    return True, p, ""


def dispatch_tool(
    name: str,
    arguments: dict[str, Any] | None = None,
    *,
    axiom: Axiom | None = None,
) -> MathResult:
    """Execute one of the 21 AXIOM MCP tools and return a :class:`MathResult`."""
    ax = axiom or Axiom()
    args = dict(arguments or {})

    if name == "math_parse":
        return ax.parse(args["expression"], assumptions=args.get("assumptions"))

    if name == "math_simplify":
        mode = args.get("mode", "simplify")
        eng = args.get("engine")
        assump = args.get("assumptions")
        if mode == "factor":
            return ax.factor(args["expression"], assumptions=assump, engine=eng)
        if mode == "expand":
            return ax.expand(args["expression"], assumptions=assump, engine=eng)
        return ax.simplify(args["expression"], assumptions=assump, engine=eng)

    if name == "math_solve":
        expr = args.get("expression") or args.get("equation")
        if not expr:
            return error_result("math_solve", "", "missing required parameter 'expression'")
        return ax.solve(
            expr,
            variable=args.get("variable"),
            assumptions=args.get("assumptions"),
            engine=args.get("engine"),
        )

    if name == "math_differentiate":
        return ax.differentiate(
            args["expression"],
            variable=args.get("variable"),
            order=int(args.get("order", 1)),
            assumptions=args.get("assumptions"),
        )

    if name == "math_integrate":
        return ax.integrate(
            args["expression"],
            variable=args.get("variable"),
            lower=args.get("lower"),
            upper=args.get("upper"),
            assumptions=args.get("assumptions"),
            engine=args.get("engine"),
        )

    if name == "math_limit":
        return ax.limit(
            args["expression"],
            variable=args.get("variable"),
            point=args.get("point", "0"),
            direction=args.get("direction", "+-"),
            assumptions=args.get("assumptions"),
        )

    if name == "math_evaluate":
        return ax.evaluate(
            args["expression"],
            precision=args.get("precision"),
            substitutions=args.get("substitutions"),
            assumptions=args.get("assumptions"),
        )

    if name == "math_plot":
        x_min = float(args.get("min", -10.0))
        x_max = float(args.get("max", 10.0))
        range_str = args.get("range_str")
        if range_str and ":" in str(range_str):
            try:
                parts = str(range_str).split(":")
                x_min, x_max = float(parts[0]), float(parts[1])
            except Exception:
                pass
        output_path = args.get("output")
        if output_path:
            ok, valid_path, err = validate_mcp_path(output_path, mode="w")
            if not ok:
                return error_result("math_plot", output_path, err)
            output_path = str(valid_path)
        return ax.plot(
            args["expression"],
            variable=args.get("variable"),
            range_=(x_min, x_max),
            points=int(args.get("points", 101)),
            output=output_path,
        )

    if name == "math_prove":
        stmt = args["statement"]
        is_path_like = (
            stmt.endswith(".lean")
            or (
                len(stmt) < 260
                and "\n" not in stmt
                and ("/" in stmt or "\\" in stmt or Path(stmt).is_file())
            )
        ) and not stmt.startswith(("theorem ", "lemma ", "def ", "example ", "--"))
        if is_path_like:
            ok, valid_path, err = validate_mcp_path(stmt, mode="r")
            if not ok:
                return error_result("math_prove", stmt, err)
            stmt = str(valid_path)
        return ax.prove(
            stmt,
            proof=args.get("proof", ""),
            engine=args.get("engine", "lean"),
            canonical_statement=args.get("canonical_statement"),
            declared_hypotheses=args.get("declared_hypotheses"),
            spec_alignment=args.get("spec_alignment"),
        )

    if name == "math_verify":
        target = args["target"]
        if isinstance(target, str) and (
            target.endswith(".json")
            or (
                len(target) < 260
                and "\n" not in target
                and ("/" in target or "\\" in target or Path(target).is_file())
            )
        ):
            ok, valid_path, err = validate_mcp_path(target, mode="r")
            if not ok:
                return error_result("math_verify", target, err)
            target = str(valid_path)
        return ax.verify(
            target,
            candidate=args.get("candidate"),
            variable=args.get("variable"),
            assumptions=args.get("assumptions"),
        )


    if name == "math_explain":
        return ax.explain(
            args["expression"],
            operation=args.get("operation", "solve"),
            variable=args.get("variable"),
        )

    if name == "math_compare":
        return ax.compare(
            args["left"],
            args["right"],
            variables=args.get("variables"),
            assumptions=args.get("assumptions"),
        )

    if name == "math_explore":
        return ax.explore(
            args["expression"],
            variable=args.get("variable"),
            samples=int(args.get("samples", 7)),
        )

    if name == "math_matrix":
        return ax.matrix(
            args["matrix"],
            operation=args.get("operation", "eigen"),
            rhs=args.get("rhs"),
        )

    if name == "math_ode":
        return ax.ode(
            args["equation"],
            function=args.get("function", "y"),
            variable=args.get("variable", "x"),
        )

    if name == "math_number_theory":
        return ax.number_theory(
            args["operation"],
            n=args.get("n"),
            a=args.get("a"),
            b=args.get("b"),
            k=args.get("k"),
            remainders=args.get("remainders"),
            moduli=args.get("moduli"),
        )

    if name == "math_optimize":
        return ax.optimize(
            args["expression"],
            variable=args.get("variable"),
            mode=args.get("mode", "minimize"),
            lower=args.get("lower"),
            upper=args.get("upper"),
        )

    if name == "math_statistics":
        return ax.statistics(args["data"])

    if name == "math_session":
        return ax.session(
            args.get("action", "show"),
            name=args.get("name", "default"),
            expression=args.get("expression"),
            operation=args.get("operation", "solve"),
            hypothesis=args.get("hypothesis"),
            note=args.get("note", ""),
        )

    if name == "math_tensor":
        return ax.tensor(
            args["metric"],
            coordinates=args.get("coordinates"),
            operation=args.get("operation", "all"),
        )

    if name == "math_search_mathlib":
        return ax.search_mathlib(
            args["query"],
            max_results=int(args.get("max_results", 8)),
            online=bool(args.get("online", False)),
        )

    return error_result(name, str(args), f"unknown MCP tool: {name!r}")


def handle_jsonrpc_message(
    message: dict[str, Any], *, axiom: Axiom | None = None
) -> dict[str, Any] | None:
    """Process a single MCP JSON-RPC 2.0 request and return the response dict."""
    method = message.get("method", "")
    msg_id = message.get("id")
    params = message.get("params") or {}

    # Notifications do not have an id and expect no response
    if msg_id is None:
        return None

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "axiom", "version": "0.1.0"},
            },
        }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": TOOL_DEFINITIONS},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments") or {}
        try:
            res = dispatch_tool(tool_name, tool_args, axiom=axiom)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {"type": "text", "text": res.to_json(indent=2)},
                    ],
                    "structuredContent": res.to_dict(),
                    "isError": not res.ok,
                },
            }
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps({"ok": False, "error": str(exc)})}
                    ],
                    "isError": True,
                },
            }

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def run_stdio_server() -> int:
    """Run the AXIOM MCP server over standard input/output (JSON-RPC 2.0 lines)."""
    ax = Axiom()
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()
            continue

        resp = handle_jsonrpc_message(msg, axiom=ax)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


def main() -> int:
    return run_stdio_server()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
