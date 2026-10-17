"""Symbolic engine backed by SymPy.

Every operation returns an :class:`Answer` carrying not just the value but the
*method* used and human-readable steps, which the core turns into evidence.
The engine never claims verification — verification belongs to the core and
must use methods independent of the one that produced the answer.
"""

from __future__ import annotations

import sympy as sp
from sympy.ntheory.modular import crt as sympy_crt

from axiom.engines.base import Answer, Engine, EngineError


def _fmt(obj) -> str:
    if isinstance(obj, (list, tuple)):
        return "[" + ", ".join(_fmt(o) for o in obj) + "]"
    return str(obj)


def _latex(obj) -> str | None:
    try:
        if isinstance(obj, (list, tuple)):
            return ", ".join(sp.latex(o) for o in obj) or None
        if isinstance(obj, sp.Basic) or isinstance(obj, sp.MatrixBase):
            return sp.latex(obj)
    except Exception:
        return None
    return None


def _matrix_to_list(mat: sp.Matrix) -> list[list[str]]:
    return [[str(mat[i, j]) for j in range(mat.cols)] for i in range(mat.rows)]


class SymPyEngine(Engine):
    name = "sympy"
    version = sp.__version__
    capabilities = (
        "evaluate",
        "simplify",
        "factor",
        "expand",
        "solve",
        "solve_system",
        "differentiate",
        "integrate",
        "limit",
        "series",
        "matrix",
        "ode",
        "number_theory",
        "optimize",
        "statistics",
        "tensor",
    )

    # ------------------------------------------------------------- algebra

    def evaluate(self, expr: sp.Expr) -> Answer:
        exact = sp.nsimplify(expr, rational=False) if expr.is_number else expr
        value = exact if exact.is_number else sp.simplify(expr)
        return Answer(
            value=str(value),
            value_str=str(value),
            latex=_latex(value),
            method="exact evaluation (nsimplify) / simplify",
            steps=[f"evaluate {expr}", f"result {value}"],
            raw={"object": value},
        )

    def simplify(self, expr: sp.Expr) -> Answer:
        result = sp.simplify(expr)
        return Answer(
            value=str(result),
            value_str=str(result),
            latex=_latex(result),
            method="symmetric simplification (sympy.simplify)",
            steps=[f"input {expr}", f"simplify -> {result}"],
            raw={"object": result},
        )

    def factor(self, expr: sp.Expr) -> Answer:
        result = sp.factor(expr)
        return Answer(
            value=str(result),
            value_str=str(result),
            latex=_latex(result),
            method="polynomial factorization (sympy.factor)",
            steps=[f"input {expr}", f"factor -> {result}"],
            raw={"object": result},
        )

    def expand(self, expr: sp.Expr) -> Answer:
        result = sp.expand(expr)
        return Answer(
            value=str(result),
            value_str=str(result),
            latex=_latex(result),
            method="polynomial expansion (sympy.expand)",
            steps=[f"input {expr}", f"expand -> {result}"],
            raw={"object": result},
        )

    # -------------------------------------------------------------- solving

    def solve(self, equation: sp.Rel, var: sp.Symbol) -> Answer:
        solutions = sp.solve(equation, var)
        if not isinstance(solutions, list):
            solutions = [solutions]
        return Answer(
            value=[str(s) for s in solutions],
            value_str=str([str(s) for s in solutions]),
            latex=_latex(solutions),
            method="algebraic solve (sympy.solve)",
            steps=[
                f"solve {equation} for {var}",
                f"solutions: {_fmt([str(s) for s in solutions])}",
            ],
            warnings=[] if solutions else ["no solutions found"],
            variables=[str(var)],
            raw={"solutions": solutions, "var": var, "equation": equation},
        )

    def solve_system(self, equations: list, variables: list) -> Answer:
        result = sp.linsolve(equations, variables)
        solutions = [
            {str(v): str(val) for v, val in zip(variables, sol)}
            for sol in (result.args if result != sp.EmptySet else [])
        ]
        return Answer(
            value=solutions,
            value_str=str(solutions),
            latex=_latex(result),
            method="linear system solver (sympy.linsolve)",
            steps=[
                f"system with {len(equations)} equations",
                f"solutions: {len(solutions)}",
            ],
            variables=[str(v) for v in variables],
            raw={
                "solutions": result,
                "vars": variables,
                "equations": equations,
            },
        )

    # ------------------------------------------------------------- calculus

    def differentiate(
        self, expr: sp.Expr, var: sp.Symbol, order: int = 1
    ) -> Answer:
        result = sp.diff(expr, var, order)
        return Answer(
            value=str(result),
            value_str=str(result),
            latex=_latex(result),
            method=f"symbolic differentiation, order {order} (sympy.diff)",
            steps=[f"d/d{var} ({order}x) of {expr}", f"-> {result}"],
            variables=[str(var)],
            raw={"object": result, "expr": expr, "var": var},
        )

    def integrate(
        self,
        expr: sp.Expr,
        var: sp.Symbol,
        limits: tuple | None = None,
    ) -> Answer:
        if limits:
            result = sp.integrate(expr, (var, *limits))
            method = "symbolic definite integration (sympy.integrate)"
            label = f"integral from {limits[0]} to {limits[1]} of {expr}"
        else:
            result = sp.integrate(expr, var)
            method = "symbolic indefinite integration (sympy.integrate)"
            label = f"integral of {expr} d{var}"
        return Answer(
            value=str(result),
            value_str=str(result),
            latex=_latex(result),
            method=method,
            steps=[label, f"-> {result}"],
            variables=[str(var)],
            raw={
                "object": result,
                "expr": expr,
                "var": var,
                "limits": limits,
            },
        )

    def limit(
        self,
        expr: sp.Expr,
        var: sp.Symbol,
        point: sp.Expr,
        direction: str = "+-",
    ) -> Answer:
        kwargs = {}
        if direction == "+":
            kwargs["dir"] = "+"
        elif direction == "-":
            kwargs["dir"] = "-"
        result = sp.limit(expr, var, point, **kwargs)
        return Answer(
            value=str(result),
            value_str=str(result),
            latex=_latex(result),
            method="symbolic limit (sympy.limit)",
            steps=[f"limit {var} -> {point} of {expr}", f"-> {result}"],
            variables=[str(var)],
            raw={
                "object": result,
                "expr": expr,
                "var": var,
                "point": point,
                "direction": direction,
            },
        )

    def series(
        self, expr: sp.Expr, var: sp.Symbol, point: sp.Expr, order: int = 6
    ) -> Answer:
        result = sp.series(expr, var, point, order)
        return Answer(
            value=str(result),
            value_str=str(result),
            latex=_latex(result),
            method=f"Taylor/Laurent expansion around {point}, O({var}^{order})",
            steps=[f"series of {expr} at {var} = {point}", f"-> {result}"],
            variables=[str(var)],
            raw={"object": result},
        )

    # ------------------------------------------------------- linear algebra

    def matrix(
        self,
        mat: sp.Matrix,
        operation: str = "eigen",
        rhs: sp.Matrix | None = None,
    ) -> Answer:
        op = operation.lower().strip()
        if op == "det":
            if mat.rows != mat.cols:
                raise EngineError("determinant requires a square matrix")
            det_val = mat.det()
            return Answer(
                value=str(det_val),
                value_str=str(det_val),
                latex=_latex(det_val),
                method="exact matrix determinant (sympy.Matrix.det)",
                steps=[f"{mat.rows}x{mat.cols} matrix", f"det -> {det_val}"],
                raw={"matrix": mat, "result": det_val, "op": "det"},
            )

        if op == "trace":
            if mat.rows != mat.cols:
                raise EngineError("trace requires a square matrix")
            tr_val = mat.trace()
            return Answer(
                value=str(tr_val),
                value_str=str(tr_val),
                latex=_latex(tr_val),
                method="matrix trace (sum of diagonal entries)",
                steps=[f"trace -> {tr_val}"],
                raw={"matrix": mat, "result": tr_val, "op": "trace"},
            )

        if op == "inv":
            if mat.rows != mat.cols:
                raise EngineError("inverse requires a square matrix")
            if mat.det() == 0:
                raise EngineError("matrix is singular (det = 0); inverse does not exist")
            inv_mat = mat.inv()
            return Answer(
                value=_matrix_to_list(inv_mat),
                value_str=str(_matrix_to_list(inv_mat)),
                latex=_latex(inv_mat),
                method="exact matrix inversion (sympy.Matrix.inv)",
                steps=[f"det = {mat.det()} != 0", f"inv -> {_matrix_to_list(inv_mat)}"],
                raw={"matrix": mat, "result": inv_mat, "op": "inv"},
            )

        if op == "rref":
            rref_mat, pivots = mat.rref()
            payload = {
                "rref": _matrix_to_list(rref_mat),
                "pivots": [int(p) for p in pivots],
                "rank": len(pivots),
            }
            return Answer(
                value=payload,
                value_str=f"rank={len(pivots)}, pivots={list(pivots)}, rref={_matrix_to_list(rref_mat)}",
                latex=_latex(rref_mat),
                method="Gauss-Jordan elimination to reduced row echelon form",
                steps=[f"rref pivots: {pivots}", f"rank: {len(pivots)}"],
                raw={"matrix": mat, "result": rref_mat, "pivots": pivots, "op": "rref"},
            )

        if op == "eigen":
            if mat.rows != mat.cols:
                raise EngineError("eigenanalysis requires a square matrix")
            evects = mat.eigenvects()
            eigen_data = []
            raw_pairs: list[tuple[sp.Expr, list[sp.Matrix]]] = []
            for val, mult, basis in evects:
                vecs_str = [_matrix_to_list(v) for v in basis]
                eigen_data.append(
                    {
                        "eigenvalue": str(val),
                        "multiplicity": int(mult),
                        "eigenvectors": vecs_str,
                    }
                )
                raw_pairs.append((val, basis))
            summary = ", ".join(
                f"λ={d['eigenvalue']} (m={d['multiplicity']})" for d in eigen_data
            )
            return Answer(
                value=eigen_data,
                value_str=summary,
                latex=_latex([val for val, _, _ in evects]),
                method="characteristic polynomial & eigenspace basis (sympy.Matrix.eigenvects)",
                steps=[
                    f"characteristic polynomial roots: {[str(v) for v, _, _ in evects]}",
                    f"eigenpairs found: {len(eigen_data)}",
                ],
                raw={"matrix": mat, "eigenpairs": raw_pairs, "op": "eigen"},
            )

        if op == "lu":
            lower_m, upper_m, perm = mat.LUdecomposition()
            return Answer(
                value={
                    "L": _matrix_to_list(lower_m),
                    "U": _matrix_to_list(upper_m),
                    "perm": perm,
                },
                value_str=f"L={_matrix_to_list(lower_m)}, U={_matrix_to_list(upper_m)}",
                latex=f"L={_latex(lower_m)}, U={_latex(upper_m)}",
                method="exact LU decomposition with row pivoting",
                steps=["computed P*A = L*U"],
                raw={
                    "matrix": mat,
                    "L": lower_m,
                    "U": upper_m,
                    "perm": perm,
                    "op": "lu",
                },
            )

        if op == "solve":
            if rhs is None:
                raise EngineError("matrix 'solve' operation requires a right-hand side vector/matrix 'rhs'")
            sol = mat.LUsolve(rhs)
            return Answer(
                value=_matrix_to_list(sol),
                value_str=str(_matrix_to_list(sol)),
                latex=_latex(sol),
                method="exact linear system solve A*x = b (sympy.Matrix.LUsolve)",
                steps=[f"solved {mat.rows}x{mat.cols} system A*x = b"],
                raw={"matrix": mat, "rhs": rhs, "solution": sol, "op": "solve"},
            )

        raise EngineError(
            f"unsupported matrix operation '{operation}' "
            "(choose from: det, trace, inv, rref, eigen, lu, solve)"
        )

    # ---------------------------------------------- differential equations

    def ode(
        self,
        equation: sp.Rel,
        func_name: str = "y",
        var: sp.Symbol | None = None,
        ics: dict | None = None,
    ) -> Answer:
        x_sym = var or sp.Symbol("x")
        f_app = sp.Function(func_name)(x_sym)
        sol = sp.dsolve(equation, f_app, ics=ics or None)
        sol_list = sol if isinstance(sol, list) else [sol]
        rhs_list = [s.rhs if isinstance(s, sp.Equality) else s for s in sol_list]
        val_strs = [str(s) for s in sol_list]
        return Answer(
            value=val_strs[0] if len(val_strs) == 1 else val_strs,
            value_str="; ".join(val_strs),
            latex=_latex(sol),
            method="symbolic ODE solver (sympy.dsolve)",
            steps=[
                f"ODE: {equation}",
                f"general/particular solution for {f_app}: {'; '.join(val_strs)}",
            ],
            variables=[str(x_sym)],
            raw={
                "equation": equation,
                "func": f_app,
                "var": x_sym,
                "solutions": sol_list,
                "rhs_list": rhs_list,
            },
        )

    # ---------------------------------------------- number theory & discrete

    def number_theory(self, operation: str, args: dict) -> Answer:
        op = operation.lower().strip()

        if op == "factorint":
            n = int(args["n"])
            factors = sp.factorint(n)
            str_factors = {str(p): int(e) for p, e in factors.items()}
            pretty = " * ".join(
                f"{p}^{e}" if e > 1 else f"{p}" for p, e in factors.items()
            ) or str(n)
            return Answer(
                value=str_factors,
                value_str=f"{n} = {pretty}",
                method="integer prime factorization (sympy.factorint)",
                steps=[f"factorint({n}) -> {str_factors}"],
                raw={"op": "factorint", "n": n, "factors": factors},
            )

        if op == "isprime":
            n = int(args["n"])
            prime = bool(sp.isprime(n))
            return Answer(
                value=prime,
                value_str="prime" if prime else "composite",
                method="deterministic Miller-Rabin / Baillie-PSW primality test",
                steps=[f"isprime({n}) -> {prime}"],
                raw={"op": "isprime", "n": n, "prime": prime},
            )

        if op == "extgcd":
            a, b = int(args["a"]), int(args["b"])
            x, y, g = sp.gcdex(a, b)
            x_i, y_i, g_i = int(x), int(y), int(g)
            return Answer(
                value={"gcd": g_i, "x": x_i, "y": y_i, "identity": f"{a}*({x_i}) + {b}*({y_i}) = {g_i}"},
                value_str=f"gcd({a}, {b}) = {g_i} = {a}*({x_i}) + {b}*({y_i})",
                method="Extended Euclidean Algorithm (sympy.gcdex)",
                steps=[f"{a}*({x_i}) + {b}*({y_i}) = {g_i}"],
                raw={"op": "extgcd", "a": a, "b": b, "x": x_i, "y": y_i, "gcd": g_i},
            )

        if op == "crt":
            moduli = [int(m) for m in args["moduli"]]
            remainders = [int(r) for r in args["remainders"]]
            res = sympy_crt(moduli, remainders)
            if res is None:
                raise EngineError("system of congruences has no solution (moduli incompatible)")
            x_sol, mod_lcm = int(res[0]), int(res[1])
            return Answer(
                value={"x": x_sol, "modulus": mod_lcm},
                value_str=f"x ≡ {x_sol} (mod {mod_lcm})",
                method="Chinese Remainder Theorem (sympy.ntheory.modular.crt)",
                steps=[
                    f"remainders={remainders}, moduli={moduli}",
                    f"x ≡ {x_sol} (mod {mod_lcm})",
                ],
                raw={
                    "op": "crt",
                    "moduli": moduli,
                    "remainders": remainders,
                    "x": x_sol,
                    "modulus": mod_lcm,
                },
            )

        if op == "totient":
            n = int(args["n"])
            if n < 1:
                raise EngineError("Euler totient requires n >= 1")
            phi = int(sp.totient(n))
            return Answer(
                value=phi,
                value_str=f"φ({n}) = {phi}",
                method="Euler totient function (sympy.totient)",
                steps=[f"totient({n}) -> {phi}"],
                raw={"op": "totient", "n": n, "phi": phi},
            )

        if op == "binomial":
            n, k = int(args["n"]), int(args["k"])
            val = int(sp.binomial(n, k))
            return Answer(
                value=val,
                value_str=f"C({n}, {k}) = {val}",
                method="exact binomial coefficient (sympy.binomial)",
                steps=[f"binomial({n}, {k}) -> {val}"],
                raw={"op": "binomial", "n": n, "k": k, "value": val},
            )

        raise EngineError(
            f"unsupported number_theory operation '{operation}' "
            "(choose from: factorint, isprime, extgcd, crt, totient, binomial)"
        )

    # --------------------------------------------------------- optimization

    def optimize(
        self,
        expr: sp.Expr,
        var: sp.Symbol,
        mode: str = "minimize",
        interval: tuple[sp.Expr, sp.Expr] | None = None,
    ) -> Answer:
        d1 = sp.diff(expr, var)
        d2 = sp.diff(d1, var)
        crit = sp.solve(sp.Eq(d1, 0), var)
        real_crit: list[sp.Expr] = []
        for c in crit:
            if c.is_real is True:
                real_crit.append(c)
            elif c.is_real is None:
                try:
                    c_complex = complex(c.evalf(20))
                    if abs(c_complex.imag) < 1e-15:
                        real_crit.append(c)
                except Exception:
                    pass

        candidates = list(real_crit)
        if interval is not None:
            a, b = interval
            a_f, b_f = float(a.evalf()), float(b.evalf())
            candidates = [
                c for c in candidates if a_f - 1e-12 <= float(c.evalf()) <= b_f + 1e-12
            ]
            candidates.extend([a, b])

        if not candidates:
            raise EngineError(f"no real stationary points found for {expr}")

        scored: list[tuple[float, sp.Expr, sp.Expr, sp.Expr]] = []
        for pt in candidates:
            val = sp.simplify(expr.subs(var, pt))
            curv = sp.simplify(d2.subs(var, pt))
            scored.append((float(val.evalf(30)), pt, val, curv))

        want_max = mode.lower().startswith("max")
        scored.sort(key=lambda item: item[0], reverse=want_max)
        _, best_x, best_val, best_curv = scored[0]
        kind_label = "maximum" if want_max else "minimum"
        return Answer(
            value={
                "mode": kind_label,
                "point": str(best_x),
                "objective_value": str(best_val),
                "first_derivative_at_point": str(sp.simplify(d1.subs(var, best_x))),
                "second_derivative_at_point": str(best_curv),
                "stationary_points": [str(c) for c in real_crit],
            },
            value_str=f"{kind_label} = {best_val} at {var} = {best_x}",
            latex=f"f({sp.latex(best_x)}) = {sp.latex(best_val)}",
            method="symbolic critical-point & second-derivative analysis",
            steps=[
                f"f'({var}) = {d1}",
                f"f''({var}) = {d2}",
                f"stationary points: {[str(c) for c in real_crit]}",
                f"optimal {kind_label}: f({best_x}) = {best_val}",
            ],
            variables=[str(var)],
            raw={
                "expr": expr,
                "var": var,
                "mode": kind_label,
                "point": best_x,
                "value": best_val,
                "d1": d1,
                "d2": d2,
                "interval": interval,
            },
        )

    # ----------------------------------------------------------- statistics

    def statistics(self, values: list[sp.Expr]) -> Answer:
        n = len(values)
        if n == 0:
            raise EngineError("statistics requires a non-empty list of numbers")
        exact_mean = sp.simplify(sum(values, sp.S.Zero) / sp.Integer(n))
        pop_var = sp.simplify(
            sum((x - exact_mean) ** 2 for x in values) / sp.Integer(n)
        )
        samp_var = (
            sp.simplify(
                sum((x - exact_mean) ** 2 for x in values) / sp.Integer(n - 1)
            )
            if n > 1
            else sp.S.Zero
        )
        sorted_vals = sorted(values, key=lambda v: float(v.evalf()))
        if n % 2 == 1:
            median = sorted_vals[n // 2]
        else:
            median = sp.simplify(
                (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / sp.Integer(2)
            )
        payload = {
            "count": n,
            "mean": str(exact_mean),
            "median": str(median),
            "population_variance": str(pop_var),
            "population_stdev": str(sp.simplify(sp.sqrt(pop_var))),
            "sample_variance": str(samp_var),
            "sample_stdev": str(sp.simplify(sp.sqrt(samp_var))),
            "min": str(sorted_vals[0]),
            "max": str(sorted_vals[-1]),
        }
        return Answer(
            value=payload,
            value_str=(
                f"n={n}, mean={exact_mean}, median={median}, "
                f"pop_var={pop_var}, sample_var={samp_var}"
            ),
            latex=rf"\mu = {sp.latex(exact_mean)}, \sigma^2 = {sp.latex(pop_var)}",
            method="exact rational/symbolic moment computation",
            steps=[
                f"n = {n}",
                f"mean = {exact_mean}",
                f"population variance = {pop_var}",
            ],
            raw={
                "values": values,
                "mean": exact_mean,
                "pop_var": pop_var,
                "samp_var": samp_var,
            },
        )

    # ------------------------------------------ tensor & differential geometry

    def tensor(
        self,
        metric: sp.Matrix,
        coords: list[sp.Symbol],
        operation: str = "all",
    ) -> Answer:
        """Compute metric inverse, Christoffel symbols, Riemann/Ricci/Einstein tensors, and scalar curvature."""
        n = len(coords)
        if metric.rows != n or metric.cols != n:
            raise EngineError(
                f"metric dimension ({metric.rows}x{metric.cols}) must match number of coordinates ({n})"
            )
        op = operation.lower().strip()
        if op not in ("all", "christoffel", "riemann", "ricci", "scalar", "einstein", "metric"):
            raise EngineError(
                f"unsupported tensor operation '{operation}' "
                "(choose from: all, christoffel, riemann, ricci, scalar, einstein, metric)"
            )

        g = metric.applyfunc(sp.simplify)
        det_g = sp.simplify(g.det())
        if det_g == 0:
            raise EngineError("metric tensor is degenerate (det(g) = 0)")
        g_inv = g.inv().applyfunc(sp.simplify)

        # Christoffel symbols of the second kind:
        # \Gamma^k_{ij} = 1/2 g^{km} (\partial_i g_{jm} + \partial_j g_{im} - \partial_m g_{ij})
        gamma: list[list[list[sp.Expr]]] = [
            [[sp.S.Zero for _ in range(n)] for _ in range(n)] for _ in range(n)
        ]
        nonzero_christoffel: dict[str, str] = {}
        coord_names = [str(c) for c in coords]

        for k in range(n):
            for i in range(n):
                for j in range(i, n):
                    acc = sp.S.Zero
                    for m in range(n):
                        if g_inv[k, m] == 0:
                            continue
                        term = (
                            sp.diff(g[j, m], coords[i])
                            + sp.diff(g[i, m], coords[j])
                            - sp.diff(g[i, j], coords[m])
                        )
                        acc += g_inv[k, m] * term
                    val = sp.simplify(sp.expand_trig(sp.Rational(1, 2) * acc))
                    gamma[k][i][j] = val
                    gamma[k][j][i] = val
                    if val != 0:
                        key = f"Gamma^{coord_names[k]}_{{{coord_names[i]},{coord_names[j]}}}"
                        nonzero_christoffel[key] = str(val)

        # Riemann tensor R^rho_{sigma, mu, nu}
        # R^r_{s,m,n} = d_m Gamma^r_{n,s} - d_n Gamma^r_{m,s}
        #               + sum_l (Gamma^r_{m,l} Gamma^l_{n,s} - Gamma^r_{n,l} Gamma^l_{m,s})
        riemann: list[list[list[list[sp.Expr]]]] = [
            [
                [[sp.S.Zero for _ in range(n)] for _ in range(n)]
                for _ in range(n)
            ]
            for _ in range(n)
        ]
        nonzero_riemann: dict[str, str] = {}
        need_curvature = op in ("all", "riemann", "ricci", "scalar", "einstein")
        if need_curvature:
            for r in range(n):
                for s in range(n):
                    for m in range(n):
                        for nu in range(n):
                            if m == nu:
                                continue
                            term = sp.diff(gamma[r][nu][s], coords[m]) - sp.diff(
                                gamma[r][m][s], coords[nu]
                            )
                            for l_idx in range(n):
                                term += (
                                    gamma[r][m][l_idx] * gamma[l_idx][nu][s]
                                    - gamma[r][nu][l_idx] * gamma[l_idx][m][s]
                                )
                            val = sp.simplify(sp.expand_trig(term))
                            riemann[r][s][m][nu] = val
                            if val != 0 and m < nu:
                                key = (
                                    f"R^{coord_names[r]}_"
                                    f"{{{coord_names[s]},{coord_names[m]},{coord_names[nu]}}}"
                                )
                                nonzero_riemann[key] = str(val)

        # Ricci tensor R_{sigma, nu} = sum_rho R^rho_{sigma, rho, nu}
        ricci = sp.zeros(n, n)
        ricci_scalar = sp.S.Zero
        einstein = sp.zeros(n, n)
        if need_curvature:
            for s in range(n):
                for nu in range(s, n):
                    acc = sum((riemann[r][s][r][nu] for r in range(n)), sp.S.Zero)
                    val = sp.simplify(sp.expand_trig(acc))
                    ricci[s, nu] = val
                    ricci[nu, s] = val

            for s in range(n):
                for nu in range(n):
                    if g_inv[s, nu] != 0 and ricci[s, nu] != 0:
                        ricci_scalar += g_inv[s, nu] * ricci[s, nu]
            ricci_scalar = sp.simplify(sp.expand_trig(ricci_scalar))

            for i in range(n):
                for j in range(n):
                    einstein[i, j] = sp.simplify(
                        sp.expand_trig(ricci[i, j] - sp.Rational(1, 2) * ricci_scalar * g[i, j])
                    )

        payload = {
            "operation": op,
            "coordinates": coord_names,
            "dimension": n,
            "metric": _matrix_to_list(g),
            "inverse_metric": _matrix_to_list(g_inv),
            "metric_determinant": str(det_g),
            "nonzero_christoffel": nonzero_christoffel,
        }
        if need_curvature:
            payload.update(
                {
                    "nonzero_riemann": nonzero_riemann,
                    "ricci_tensor": _matrix_to_list(ricci),
                    "ricci_scalar": str(ricci_scalar),
                    "einstein_tensor": _matrix_to_list(einstein),
                }
            )

        summary_parts = [
            f"dim={n} ({', '.join(coord_names)})",
            f"det(g)={det_g}",
            f"|Gamma != 0|={len(nonzero_christoffel)}",
        ]
        if need_curvature:
            summary_parts.append(f"R={ricci_scalar}")

        return Answer(
            value=payload,
            value_str=", ".join(summary_parts),
            latex=(
                rf"R = {sp.latex(ricci_scalar)}"
                if need_curvature
                else rf"\det(g) = {sp.latex(det_g)}"
            ),
            method="symbolic Levi-Civita connection & Riemann curvature tensor contractions",
            steps=[
                f"coordinates: {coord_names}",
                f"det(g) = {det_g}",
                f"non-zero Christoffel symbols (symmetric pairs): {nonzero_christoffel or '0 (flat in these coords)'}",
                *(
                    [
                        f"Ricci scalar R = {ricci_scalar}",
                    ]
                    if need_curvature
                    else []
                ),
            ],
            variables=coord_names,
            raw={
                "op": op,
                "coords": coords,
                "g": g,
                "g_inv": g_inv,
                "det_g": det_g,
                "gamma": gamma,
                "riemann": riemann,
                "ricci": ricci,
                "ricci_scalar": ricci_scalar,
                "einstein": einstein,
                "need_curvature": need_curvature,
            },
        )

    # ------------------------------------------------------------ utilities

    @staticmethod
    def ready() -> tuple[bool, str]:
        try:
            return True, f"sympy {sp.__version__}"
        except Exception as exc:  # pragma: no cover - import already happened
            return False, str(exc)


def engine_or_error(engine: Engine, operation: str):
    try:
        return engine.require(operation)
    except EngineError as exc:
        raise EngineError(str(exc)) from exc
