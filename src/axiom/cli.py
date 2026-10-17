"""Command-line interface for AXIOM (``axiom`` / ``math``).

Provides composable mathematical commands with traceable evidence and
independent verification, plus ``axiom mcp`` to launch the MCP stdio server.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from axiom.contract import MathResult
from axiom.core import Axiom
from axiom.mcp_server import run_stdio_server
from axiom.setup_agent import configure_clients, run_doctor


def render_box(result: MathResult) -> str:
    """Render a :class:`MathResult` in a clean REA-style evidence box."""
    rows: list[tuple[str, str]] = [
        (result.kind.replace("_", " ").title(), result.input),
    ]
    if not result.ok:
        rows.append(("Status", "ERROR"))
        rows.append(("Error", str(result.error or "unknown error")))
    else:
        rows.append(("Result", result.value_str))
        if result.latex:
            rows.append(("LaTeX", result.latex))
        if result.evidence:
            eng_label = f"{result.evidence.engine} {result.evidence.engine_version}".strip()
            rows.append(("Engine", eng_label))
            if result.evidence.method:
                rows.append(("Method", result.evidence.method))
        if result.verification:
            ver_status = "PASSED" if result.verification.passed else "FAILED"
            rows.append(
                ("Verification", f"{result.verification.kind} ({ver_status})")
            )
            if result.verification.detail:
                rows.append(("Detail", result.verification.detail))
        rows.append(("Guarantee", result.guarantee.value.upper()))
        for warn in result.warnings:
            rows.append(("Warning", warn))
        if result.evidence:
            for lim in result.evidence.limitations:
                rows.append(("Limitation", lim))

    key_width = max(len(k) for k, _ in rows)
    formatted_lines: list[str] = []
    for k, v in rows:
        sublines = str(v).splitlines() or [""]
        formatted_lines.append(f"{k:<{key_width}}  {sublines[0]}")
        for extra in sublines[1:]:
            formatted_lines.append(f"{'':<{key_width}}  {extra}")

    inner_width = max(max(len(line) for line in formatted_lines), 45)
    top = "┌─" + "─" * inner_width + "─┐"
    bot = "└─" + "─" * inner_width + "─┘"
    body = [f"│ {line:<{inner_width}} │" for line in formatted_lines]
    return "\n".join([top, *body, bot])


def _parse_range(spec: str) -> tuple[float, float]:
    parts = spec.split(":")
    if len(parts) != 2:
        raise ValueError(f"range must be 'min:max', got {spec!r}")
    return float(parts[0]), float(parts[1])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="axiom",
        description=(
            "AXIOM — Mathematical Reasoning Engine. "
            "One MCP & CLI for mathematical computation, exploration, and verification."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output.",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Emit plain text instead of a Unicode evidence box.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # parse
    p_parse = sub.add_parser("parse", help="Parse an expression or equation into a canonical AST.")
    p_parse.add_argument("expression")
    p_parse.add_argument(
        "-A", "--assumptions", help="Domain assumptions (e.g. 'x:positive', 'x:real;y:positive', or JSON)."
    )
    p_parse.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # solve
    p_solve = sub.add_parser("solve", help="Solve an equation or ';'-separated system and verify roots.")
    p_solve.add_argument("expression")
    p_solve.add_argument("-v", "--variable", help="Variable(s) to solve for.")
    p_solve.add_argument(
        "-A", "--assumptions", help="Domain assumptions (e.g. 'x:positive', 'x:real;y:positive', or JSON)."
    )
    p_solve.add_argument("-e", "--engine", help="Engine name (sympy, numeric).")
    p_solve.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # simplify / factor / expand
    for cmd_name, help_text in (
        ("simplify", "Simplify a mathematical expression and verify equivalence."),
        ("factor", "Factor a polynomial/algebraic expression and verify equivalence."),
        ("expand", "Expand a mathematical expression and verify equivalence."),
    ):
        p_alg = sub.add_parser(cmd_name, help=help_text)
        p_alg.add_argument("expression")
        p_alg.add_argument(
            "-A", "--assumptions", help="Domain assumptions (e.g. 'x:positive', 'x:real;y:positive', or JSON)."
        )
        p_alg.add_argument("-e", "--engine", help="Engine name.")
        p_alg.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # differentiate
    p_diff = sub.add_parser("differentiate", aliases=["diff"], help="Differentiate an expression.")
    p_diff.add_argument("expression")
    p_diff.add_argument("-v", "--variable", help="Differentiation variable (default: x).")
    p_diff.add_argument("-n", "--order", type=int, default=1, help="Derivative order (default: 1).")
    p_diff.add_argument(
        "-A", "--assumptions", help="Domain assumptions (e.g. 'x:positive', 'x:real;y:positive', or JSON)."
    )
    p_diff.add_argument("-e", "--engine", help="Engine name.")
    p_diff.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # integrate
    p_int = sub.add_parser("integrate", help="Compute an indefinite or definite integral.")
    p_int.add_argument("expression")
    p_int.add_argument("-v", "--variable", help="Integration variable (default: x).")
    p_int.add_argument("--from", dest="lower", help="Lower limit for definite integral.")
    p_int.add_argument("--to", dest="upper", help="Upper limit for definite integral.")
    p_int.add_argument(
        "-A", "--assumptions", help="Domain assumptions (e.g. 'x:positive', 'x:real;y:positive', or JSON)."
    )
    p_int.add_argument("-e", "--engine", help="Engine name (sympy, numeric).")
    p_int.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # limit
    p_lim = sub.add_parser("limit", help="Compute the limit of an expression.")
    p_lim.add_argument("expression")
    p_lim.add_argument("-v", "--variable", help="Variable (default: x).")
    p_lim.add_argument("--to", dest="point", default="0", help="Point approached (default: 0).")
    p_lim.add_argument("--dir", dest="direction", default="+-", choices=["+-", "+", "-"])
    p_lim.add_argument(
        "-A", "--assumptions", help="Domain assumptions (e.g. 'x:positive', 'x:real;y:positive', or JSON)."
    )
    p_lim.add_argument("-e", "--engine", help="Engine name.")
    p_lim.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # series
    p_ser = sub.add_parser("series", help="Compute a Taylor/Laurent series expansion.")
    p_ser.add_argument("expression")
    p_ser.add_argument("-v", "--variable", help="Variable (default: x).")
    p_ser.add_argument("--at", dest="point", default="0", help="Expansion point (default: 0).")
    p_ser.add_argument("-n", "--order", type=int, default=6, help="Truncation order (default: 6).")
    p_ser.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # evaluate
    p_eval = sub.add_parser("evaluate", aliases=["eval"], help="Evaluate an expression symbolically or numerically.")
    p_eval.add_argument("expression")
    p_eval.add_argument("-p", "--precision", type=int, help="Decimal digits of precision.")
    p_eval.add_argument(
        "-A", "--assumptions", help="Domain assumptions (e.g. 'x:positive', 'x:real;y:positive', or JSON)."
    )
    p_eval.add_argument("-e", "--engine", help="Engine name.")
    p_eval.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # compare
    p_cmp = sub.add_parser("compare", help="Check whether two expressions are mathematically equivalent.")
    p_cmp.add_argument("left")
    p_cmp.add_argument("right")
    p_cmp.add_argument(
        "-A", "--assumptions", help="Domain assumptions (e.g. 'x:positive', 'x:real;y:positive', or JSON)."
    )
    p_cmp.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # verify
    p_ver = sub.add_parser("verify", help="Independently verify an equation root, identity, or JSON result file.")
    p_ver.add_argument("target", help="Equation, 'lhs = rhs' identity, or path to result.json.")
    p_ver.add_argument("-s", "--solutions", help="Comma-separated candidate roots to verify.")
    p_ver.add_argument("-v", "--variable", help="Variable name.")
    p_ver.add_argument(
        "-A", "--assumptions", help="Domain assumptions (e.g. 'x:positive', 'x:real;y:positive', or JSON)."
    )
    p_ver.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # explain
    p_exp = sub.add_parser("explain", help="Produce a step-by-step mathematical explanation.")
    p_exp.add_argument("expression")
    p_exp.add_argument(
        "-o",
        "--operation",
        default="solve",
        choices=["solve", "simplify", "factor", "expand", "differentiate", "integrate", "limit", "evaluate"],
    )
    p_exp.add_argument("-v", "--variable", help="Variable name.")
    p_exp.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # explore
    p_xpl = sub.add_parser("explore", help="Explore zeros, derivatives, parity, series, and samples.")
    p_xpl.add_argument("expression")
    p_xpl.add_argument("-v", "--variable", help="Variable name.")
    p_xpl.add_argument("--samples", type=int, default=7, help="Number of sample points.")
    p_xpl.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # plot
    p_plot = sub.add_parser("plot", help="Sample a function over a range and optionally save a plot.")
    p_plot.add_argument("expression")
    p_plot.add_argument("-v", "--variable", help="Variable name (default: x).")
    p_plot.add_argument("-r", "--range", default="-10:10", help="Domain as min:max (default: -10:10).")
    p_plot.add_argument("--points", type=int, default=101, help="Number of grid points.")
    p_plot.add_argument("-o", "--output", help="Optional output image path (.png/.svg).")
    p_plot.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # prove
    p_prove = sub.add_parser("prove", help="Check a formal proof via Lean 4 or symbolic identity check.")
    p_prove.add_argument("statement", help="Path to .lean file or theorem statement.")
    p_prove.add_argument("--proof", default="", help="Optional Lean 4 proof body.")
    p_prove.add_argument("-e", "--engine", default="lean", help="Engine (lean or sympy).")
    p_prove.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # matrix
    p_mat = sub.add_parser("matrix", help="Linear algebra operations (eigen, det, trace, inv, rref, lu, solve).")
    p_mat.add_argument("matrix", help="Matrix literal, e.g. '[[1, 2], [3, 4]]'.")
    p_mat.add_argument(
        "--op",
        default="eigen",
        choices=["eigen", "det", "trace", "inv", "rref", "lu", "solve"],
        help="Matrix operation (default: eigen).",
    )
    p_mat.add_argument("--rhs", help="Right-hand side vector/matrix for --op solve.")
    p_mat.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # ode
    p_ode = sub.add_parser("ode", help="Solve an ordinary differential equation and verify by substitution.")
    p_ode.add_argument("equation", help="ODE expression, e.g. 'diff(y(x), x) + 2*y(x) = exp(x)'.")
    p_ode.add_argument("-f", "--function", default="y", help="Unknown function name (default: y).")
    p_ode.add_argument("-v", "--variable", default="x", help="Independent variable (default: x).")
    p_ode.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # number-theory
    p_nt = sub.add_parser(
        "number-theory",
        aliases=["nt"],
        help="Verified number theory & combinatorics (factorint, isprime, extgcd, crt, totient, binomial).",
    )
    p_nt.add_argument(
        "operation",
        choices=["factorint", "isprime", "extgcd", "crt", "totient", "binomial"],
    )
    p_nt.add_argument("-n", type=int, help="Integer parameter n.")
    p_nt.add_argument("-a", type=int, help="Integer parameter a (for extgcd).")
    p_nt.add_argument("-b", type=int, help="Integer parameter b (for extgcd).")
    p_nt.add_argument("-k", type=int, help="Integer parameter k (for binomial).")
    p_nt.add_argument("--remainders", help="Comma-separated remainders for crt.")
    p_nt.add_argument("--moduli", help="Comma-separated moduli for crt.")
    p_nt.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # optimize
    p_opt = sub.add_parser("optimize", help="Find and verify minima or maxima of an expression.")
    p_opt.add_argument("expression")
    p_opt.add_argument("-v", "--variable", help="Decision variable (default: x).")
    p_opt.add_argument("-m", "--mode", default="minimize", choices=["minimize", "maximize"])
    p_opt.add_argument("--from", dest="lower", help="Optional interval lower bound.")
    p_opt.add_argument("--to", dest="upper", help="Optional interval upper bound.")
    p_opt.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # stats
    p_st = sub.add_parser("stats", aliases=["statistics"], help="Exact summary statistics with moment verification.")
    p_st.add_argument("data", help="Comma-separated numbers or list literal.")
    p_st.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # tensor
    p_ten = sub.add_parser(
        "tensor",
        help="Differential geometry & tensor calculus (metric inverse, Christoffel, Riemann, Ricci, Einstein).",
    )
    p_ten.add_argument(
        "metric",
        help="Metric matrix literal (e.g. '[[1, 0], [0, r^2]]') or preset ('polar', 'sphere', 'cylindrical', 'minkowski', 'schwarzschild').",
    )
    p_ten.add_argument(
        "-c",
        "--coords",
        help="Comma-separated coordinate symbols (e.g. 'r,theta' or 't,r,theta,phi').",
    )
    p_ten.add_argument(
        "--op",
        default="all",
        choices=["all", "christoffel", "riemann", "ricci", "scalar", "einstein", "metric"],
        help="Tensor computation target (default: all).",
    )
    p_ten.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # search-mathlib
    p_sml = sub.add_parser(
        "search-mathlib",
        aliases=["mathlib"],
        help="Search Lean 4 / Mathlib4 theorems, signatures, and tactic hints.",
    )
    p_sml.add_argument("query", help="Theorem name, concept, or signature pattern.")
    p_sml.add_argument("-n", "--max-results", type=int, default=8, help="Max results (default: 8).")
    p_sml.add_argument("--online", action="store_true", help="Also query the live Loogle Mathlib4 API.")
    p_sml.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # session
    p_sess = sub.add_parser(
        "session",
        help="Manage reproducible research sessions and conjecture snapshots (show, record, hypothesis, export, clear).",
    )
    p_sess.add_argument(
        "action",
        nargs="?",
        default="show",
        choices=["show", "record", "hypothesis", "export", "clear"],
    )
    p_sess.add_argument("--name", default="default", help="Session name (default: default).")
    p_sess.add_argument("-e", "--expression", help="Expression to record when action=record.")
    p_sess.add_argument("-o", "--operation", default="solve", help="Operation for action=record (default: solve).")
    p_sess.add_argument("--hypothesis", help="Conjecture statement for action=hypothesis.")
    p_sess.add_argument("--note", default="", help="Optional note for recorded step.")
    p_sess.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # engines
    p_eng = sub.add_parser("engines", help="List registered mathematical engines and capabilities.")
    p_eng.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # doctor
    p_doc = sub.add_parser("doctor", help="Run environment, engine, and verification diagnostics.")
    p_doc.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # setup
    p_set = sub.add_parser("setup", help="Register AXIOM MCP server with AI coding agents (Claude, Cursor, Gemini, Codex).")
    p_set.add_argument(
        "-c",
        "--client",
        default="all",
        help="Comma-separated client names (claude-code,cursor,gemini,codex or all).",
    )
    p_set.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to client config files (with automatic .axiom.bak backup).",
    )
    p_set.add_argument("--json", action="store_true", default=argparse.SUPPRESS)

    # mcp
    sub.add_parser("mcp", help="Start the AXIOM MCP server over stdio.")

    seen: set[int] = set()
    for sp_item in sub.choices.values():
        if id(sp_item) not in seen:
            seen.add(id(sp_item))
            sp_item.add_argument("--plain", action="store_true", default=argparse.SUPPRESS)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "mcp":
        return run_stdio_server()

    ax = Axiom()

    if args.command == "engines":
        infos = [
            {
                "name": info.name,
                "version": info.version,
                "capabilities": list(info.capabilities),
            }
            for info in ax.registry.list_engines()
        ]
        if getattr(args, "json", False):
            print(json.dumps({"engines": infos}, indent=2))
        else:
            for item in infos:
                caps = ", ".join(item["capabilities"])
                print(f"{item['name']} (v{item['version']}): {caps}")
        return 0

    if args.command == "doctor":
        report = run_doctor(ax)
        if getattr(args, "json", False):
            print(json.dumps(report, indent=2))
        else:
            print(f"AXIOM Doctor — status: {'OK' if report['ok'] else 'FAILED'}")
            print(f"  Python:     {report['python']}")
            print(f"  MCP tools:  {report['mcp_tools_count']}")
            print("  Packages:")
            for k, v in report["packages"].items():
                print(f"    - {k:<12} {v or 'not installed'}")
            print("  Self-tests:")
            for k, passed in report["self_tests"].items():
                print(f"    - {k:<26} {'PASSED' if passed else 'FAILED'}")
        return 0 if report["ok"] else 1

    if args.command == "setup":
        client_list = [c.strip() for c in args.client.split(",") if c.strip()]
        report = configure_clients(clients=client_list, apply=args.apply)
        if getattr(args, "json", False):
            print(json.dumps(report, indent=2))
        else:
            mode_label = "APPLIED" if args.apply else "DRY-RUN (pass --apply to write)"
            print(f"AXIOM Agent Setup [{mode_label}]")
            for item in report["clients"]:
                print(f"  - {item['client']}: {item['status']} ({item.get('config_path', '')})")
        return 0

    cmd = args.command
    assump = getattr(args, "assumptions", None)
    if cmd == "parse":
        res = ax.parse(args.expression, assumptions=assump)
    elif cmd == "solve":
        res = ax.solve(
            args.expression, variable=args.variable, assumptions=assump, engine=args.engine
        )
    elif cmd == "simplify":
        res = ax.simplify(args.expression, assumptions=assump, engine=args.engine)
    elif cmd == "factor":
        res = ax.factor(args.expression, assumptions=assump, engine=args.engine)
    elif cmd == "expand":
        res = ax.expand(args.expression, assumptions=assump, engine=args.engine)
    elif cmd in ("differentiate", "diff"):
        res = ax.differentiate(
            args.expression,
            variable=args.variable,
            order=args.order,
            assumptions=assump,
            engine=args.engine,
        )
    elif cmd == "integrate":
        res = ax.integrate(
            args.expression,
            variable=args.variable,
            lower=args.lower,
            upper=args.upper,
            assumptions=assump,
            engine=args.engine,
        )
    elif cmd == "limit":
        res = ax.limit(
            args.expression,
            variable=args.variable,
            point=args.point,
            direction=args.direction,
            assumptions=assump,
            engine=args.engine,
        )
    elif cmd == "series":
        res = ax.series(
            args.expression,
            variable=args.variable,
            point=args.point,
            order=args.order,
        )
    elif cmd in ("evaluate", "eval"):
        res = ax.evaluate(
            args.expression,
            precision=args.precision,
            assumptions=assump,
            engine=args.engine,
        )
    elif cmd == "compare":
        res = ax.compare(args.left, args.right, assumptions=assump)
    elif cmd == "verify":
        res = ax.verify(
            args.target,
            candidate=args.solutions,
            variable=args.variable,
            assumptions=assump,
        )
    elif cmd == "explain":
        res = ax.explain(
            args.expression,
            operation=args.operation,
            variable=args.variable,
        )
    elif cmd == "explore":
        res = ax.explore(
            args.expression,
            variable=args.variable,
            samples=args.samples,
        )
    elif cmd == "plot":
        try:
            r_min, r_max = _parse_range(args.range)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        res = ax.plot(
            args.expression,
            variable=args.variable,
            range_=(r_min, r_max),
            points=args.points,
            output=args.output,
        )
    elif cmd == "prove":
        res = ax.prove(args.statement, proof=args.proof, engine=args.engine)
    elif cmd == "matrix":
        res = ax.matrix(args.matrix, operation=args.op, rhs=args.rhs)
    elif cmd == "ode":
        res = ax.ode(args.equation, function=args.function, variable=args.variable)
    elif cmd in ("number-theory", "nt"):
        rems = (
            [int(x.strip()) for x in args.remainders.split(",") if x.strip()]
            if args.remainders
            else None
        )
        mods = (
            [int(x.strip()) for x in args.moduli.split(",") if x.strip()]
            if args.moduli
            else None
        )
        res = ax.number_theory(
            args.operation,
            n=args.n,
            a=args.a,
            b=args.b,
            k=args.k,
            remainders=rems,
            moduli=mods,
        )
    elif cmd == "optimize":
        res = ax.optimize(
            args.expression,
            variable=args.variable,
            mode=args.mode,
            lower=args.lower,
            upper=args.upper,
        )
    elif cmd in ("stats", "statistics"):
        res = ax.statistics(args.data)
    elif cmd == "tensor":
        res = ax.tensor(args.metric, coordinates=args.coords, operation=args.op)
    elif cmd in ("search-mathlib", "mathlib"):
        res = ax.search_mathlib(args.query, max_results=args.max_results, online=args.online)
    elif cmd == "session":
        res = ax.session(
            args.action,
            name=args.name,
            expression=args.expression,
            operation=args.operation,
            hypothesis=args.hypothesis,
            note=args.note,
        )
    else:  # pragma: no cover
        parser.error(f"unknown command: {cmd}")
        return 2

    if getattr(args, "json", False):
        _safe_print(res.to_json(indent=2))
    elif getattr(args, "plain", False):
        _safe_print(res.render())
    else:
        _safe_print(render_box(res))

    return 0 if res.ok else 1


def _safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "ascii"
        safe_text = text.encode(enc, errors="replace").decode(enc, errors="replace")
        print(safe_text)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

