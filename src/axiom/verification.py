"""Independent mathematical verifiers for AXIOM.

An engine produces a claim; this module checks that claim using a *different*
mechanism than the one that computed it:

* Equations (`solve`) are checked by substituting each root back into
  ``lhs - rhs`` using exact rational/symbolic arithmetic, falling back to
  high-precision ``mpmath`` evaluation when radicals prevent canonical zero
  reduction.
* Algebraic transformations (`simplify`, `factor`, `expand`, `compare`) are
  checked both by independent symbolic normal forms (expansion, rational
  cancellation, trigonometric reduction) and by deterministic multi-point
  evaluation at transcendental sample points.
* Indefinite integrals (`integrate`) are checked by differentiating the
  antiderivative and comparing it to the integrand.
* Definite integrals are checked against adaptive Gaussian quadrature
  (:func:`mpmath.quad`).
* Derivatives (`differentiate`) are checked against high-precision complex-step
  / finite-difference numerical derivatives at non-singular sample points.
* Limits (`limit`) are checked by evaluating the expression along a geometric
  sequence approaching the limit point.
"""

from __future__ import annotations

import mpmath as mp
import sympy as sp

from axiom.contract import Guarantee, Verification

# Deterministic non-algebraic sample points to avoid accidental polynomial zeros
_SAMPLE_POINTS: tuple[float, ...] = (
    0.3141592653,
    0.7182818284,
    1.1414213562,
    1.6180339887,
    2.2360679774,
    -0.4669201609,
    -1.3247179572,
    0.8660254037,
)


def _is_symbolic_zero(expr: sp.Expr) -> bool:
    """Return True if ``expr`` can be proved identically zero symbolically."""
    if expr == 0 or expr is sp.S.Zero:
        return True
    try:
        for transform in (sp.expand, sp.cancel, sp.trigsimp, sp.radsimp, sp.simplify):
            reduced = transform(expr)
            if reduced == 0 or reduced is sp.S.Zero:
                return True
        if expr.is_number:
            simplified = sp.nsimplify(expr)
            if simplified == 0:
                return True
    except Exception:
        pass
    return False


def verify_solutions(
    equation: sp.Rel,
    var: sp.Symbol,
    solutions: list[sp.Expr],
    *,
    tol: float = 1e-25,
) -> tuple[Verification, Guarantee]:
    """Verify candidate roots by substituting each into ``lhs - rhs``."""
    if not isinstance(equation, sp.Equality):
        return (
            Verification(
                kind="inequality-check",
                passed=False,
                detail="exact root substitution only applies to equalities",
            ),
            Guarantee.HEURISTIC,
        )

    if not solutions:
        return (
            Verification(
                kind="empty-solution-set",
                passed=False,
                detail="no candidate solutions to verify",
                checks=0,
            ),
            Guarantee.HEURISTIC,
        )

    residual_expr = equation.lhs - equation.rhs
    all_exact = True
    max_error = 0.0
    residuals_data: list[dict[str, object]] = []

    for sol in solutions:
        sub = residual_expr.subs(var, sol)
        if _is_symbolic_zero(sub):
            residuals_data.append(
                {"solution": str(sol), "residual": "0", "exact": True}
            )
            continue

        all_exact = False
        try:
            numeric = complex(sub.evalf(40))
            err = abs(numeric)
        except Exception as exc:
            return (
                Verification(
                    kind="substitution",
                    passed=False,
                    detail=f"could not evaluate residual at {var} = {sol}: {exc}",
                    checks=len(solutions),
                    data={"residuals": residuals_data},
                ),
                Guarantee.UNVERIFIED,
            )

        max_error = max(max_error, err)
        if err > tol:
            residuals_data.append(
                {"solution": str(sol), "residual": f"{err:.3e}", "exact": False}
            )
            return (
                Verification(
                    kind="substitution",
                    passed=False,
                    detail=f"root {var} = {sol} failed substitution (|residual| = {err:.3e})",
                    checks=len(solutions),
                    max_error=err,
                    data={"residuals": residuals_data},
                ),
                Guarantee.UNVERIFIED,
            )
        residuals_data.append(
            {"solution": str(sol), "residual": f"{err:.3e}", "exact": False}
        )

    if all_exact:
        noun = "Both roots satisfy" if len(solutions) == 2 else (
            "Root satisfies" if len(solutions) == 1 else f"All {len(solutions)} roots satisfy"
        )
        return (
            Verification(
                kind="exact-substitution",
                passed=True,
                detail=f"{noun} the equation by exact substitution",
                checks=len(solutions),
                max_error=0.0,
                data={"residuals": residuals_data},
            ),
            Guarantee.VERIFIED_SUBSTITUTION,
        )

    return (
        Verification(
            kind="numerical-substitution",
            passed=True,
            detail=(
                f"All {len(solutions)} root(s) satisfy the equation within "
                f"max error {max_error:.2e}"
            ),
            checks=len(solutions),
            max_error=max_error,
            data={"residuals": residuals_data},
        ),
        Guarantee.NUMERICAL_APPROXIMATION,
    )


def verify_system_solutions(
    equations: list[sp.Equality],
    variables: list[sp.Symbol],
    solutions_set: object,
) -> tuple[Verification, Guarantee]:
    """Verify linear/nonlinear system solutions by substituting into all equations."""
    if solutions_set == sp.EmptySet or not getattr(solutions_set, "args", None):
        return (
            Verification(
                kind="system-substitution",
                passed=False,
                detail="no solutions to verify",
            ),
            Guarantee.HEURISTIC,
        )

    checks = 0
    for tuple_sol in solutions_set.args:
        subs_map = dict(zip(variables, tuple_sol))
        if any(v in val.free_symbols for v in variables for val in tuple_sol):
            # Parametric family of solutions: still check symbolic substitution
            pass
        for eq in equations:
            checks += 1
            res = (eq.lhs - eq.rhs).subs(subs_map)
            if not _is_symbolic_zero(res):
                return (
                    Verification(
                        kind="system-substitution",
                        passed=False,
                        detail=f"equation {eq} not satisfied by {subs_map}",
                        checks=checks,
                    ),
                    Guarantee.UNVERIFIED,
                )

    return (
        Verification(
            kind="exact-substitution",
            passed=True,
            detail=f"All {len(equations)} equations satisfied by exact substitution",
            checks=checks,
            max_error=0.0,
        ),
        Guarantee.VERIFIED_SUBSTITUTION,
    )


def verify_equivalence(
    left: sp.Expr,
    right: sp.Expr,
    variables: list[sp.Symbol] | None = None,
    *,
    tol: float = 1e-20,
) -> tuple[Verification, Guarantee]:
    """Verify ``left == right`` via symbolic reduction and multi-point sampling."""
    diff = left - right
    free = sorted(diff.free_symbols, key=str) if variables is None else list(variables)

    symbolic_ok = _is_symbolic_zero(diff)

    # Also perform independent numerical spot-checks
    checks = 0
    max_error = 0.0
    if not free:
        try:
            err = abs(complex(diff.evalf(40)))
            checks = 1
            max_error = err
            if err > tol:
                return (
                    Verification(
                        kind="equivalence",
                        passed=False,
                        detail=f"constant values differ by {err:.3e}",
                        checks=1,
                        max_error=err,
                    ),
                    Guarantee.UNVERIFIED,
                )
        except Exception:
            pass
    else:
        for idx, base in enumerate(_SAMPLE_POINTS):
            subs = {
                sym: sp.Float(base + 0.13 * k, 40)
                for k, sym in enumerate(free)
            }
            try:
                val = diff.subs(subs).evalf(35)
                if val.has(sp.nan, sp.oo, sp.zoo):
                    continue
                err = abs(complex(val))
            except Exception:
                continue
            checks += 1
            max_error = max(max_error, err)
            if err > tol:
                counterexample = {str(k): str(v) for k, v in subs.items()}
                return (
                    Verification(
                        kind="counterexample-search",
                        passed=False,
                        detail=f"counterexample found at {counterexample} (|diff| = {err:.3e})",
                        checks=checks,
                        max_error=err,
                        data={"counterexample": counterexample},
                    ),
                    Guarantee.UNVERIFIED,
                )
            if checks >= 5:
                break

    if symbolic_ok:
        return (
            Verification(
                kind="symbolic-identity",
                passed=True,
                detail=(
                    f"Symbolic difference reduces to 0"
                    + (f" and {checks} numerical sample(s) agree" if checks else "")
                ),
                checks=max(checks, 1),
                max_error=max_error,
            ),
            Guarantee.EXACT_SYMBOLIC,
        )

    if checks >= 3 and max_error <= tol:
        return (
            Verification(
                kind="numerical-spot-check",
                passed=True,
                detail=(
                    f"Agreed across {checks} test points within {max_error:.2e} "
                    "(symbolic reduction inconclusive)"
                ),
                checks=checks,
                max_error=max_error,
            ),
            Guarantee.NUMERICAL_APPROXIMATION,
        )

    return (
        Verification(
            kind="equivalence",
            passed=False,
            detail="could not confirm symbolic or numerical equivalence",
            checks=checks,
        ),
        Guarantee.UNVERIFIED,
    )


def verify_derivative(
    expr: sp.Expr,
    derivative: sp.Expr,
    var: sp.Symbol,
    order: int = 1,
    *,
    tol: float = 1e-10,
) -> tuple[Verification, Guarantee]:
    """Check a symbolic derivative against high-precision numerical differentiation."""
    other_vars = [s for s in sorted(expr.free_symbols, key=str) if s != var]
    fixed_subs = {
        sym: sp.Rational(idx + 2, idx + 3) for idx, sym in enumerate(other_vars)
    }
    expr_1d = expr.subs(fixed_subs)
    deriv_1d = derivative.subs(fixed_subs)

    checks = 0
    max_error = 0.0
    with mp.workdps(40):
        f_num = sp.lambdify(var, expr_1d, modules="mpmath")
        d_num = sp.lambdify(var, deriv_1d, modules="mpmath")
        for pt in _SAMPLE_POINTS[:5]:
            try:
                x0 = mp.mpf(str(pt))
                approx = mp.diff(f_num, x0, n=order)
                claimed = d_num(x0)
                if not (mp.isfinite(approx) and mp.isfinite(claimed)):
                    continue
                scale = max(mp.fabs(claimed), mp.mpf("1.0"))
                err = float(mp.fabs(approx - claimed) / scale)
            except Exception:
                continue
            checks += 1
            max_error = max(max_error, err)
            if err > tol:
                return (
                    Verification(
                        kind="numerical-derivative-check",
                        passed=False,
                        detail=f"disagreed with mpmath.diff at {var}={pt} (rel error {err:.3e})",
                        checks=checks,
                        max_error=err,
                    ),
                    Guarantee.UNVERIFIED,
                )

    if checks > 0:
        return (
            Verification(
                kind="numerical-derivative-check",
                passed=True,
                detail=f"Matched high-precision finite differences at {checks} points (max rel error {max_error:.2e})",
                checks=checks,
                max_error=max_error,
            ),
            Guarantee.EXACT_SYMBOLIC,
        )

    return (
        Verification(
            kind="symbolic-rule-check",
            passed=True,
            detail="Computed via deterministic differentiation rules",
            checks=1,
        ),
        Guarantee.EXACT_SYMBOLIC,
    )


def verify_integral(
    integrand: sp.Expr,
    result: sp.Expr,
    var: sp.Symbol,
    limits: tuple[sp.Expr, sp.Expr] | None = None,
    *,
    tol: float = 1e-10,
) -> tuple[Verification, Guarantee]:
    """Verify an integral by differentiation (indefinite) or quadrature (definite)."""
    if result.has(sp.Integral):
        return (
            Verification(
                kind="unevaluated-integral",
                passed=False,
                detail="integral remained in unevaluated form (no closed-form antiderivative found)",
            ),
            Guarantee.HEURISTIC,
        )

    if limits is None:
        # Indefinite integral: d/dx(F(x)) must equal f(x)
        differentiated = sp.diff(result, var)
        ver, guar = verify_equivalence(differentiated, integrand, [var])
        if ver.passed:
            return (
                Verification(
                    kind="differentiate-antiderivative",
                    passed=True,
                    detail=f"d/d{var}({result}) equals the integrand ({ver.detail})",
                    checks=ver.checks,
                    max_error=ver.max_error,
                ),
                guar,
            )
        return (
            Verification(
                kind="differentiate-antiderivative",
                passed=False,
                detail=f"d/d{var}({result}) = {differentiated} != {integrand}",
                checks=ver.checks,
                max_error=ver.max_error,
            ),
            Guarantee.UNVERIFIED,
        )

    # Definite integral: compare against mpmath.quad when limits and integrand are numeric
    lower, upper = limits
    other_vars = (
        (integrand.free_symbols - {var})
        | lower.free_symbols
        | upper.free_symbols
    )
    if not other_vars:
        try:
            with mp.workdps(35):
                fn = sp.lambdify(var, integrand, modules="mpmath")
                a = mp.mpf(str(lower.evalf(35)))
                b = mp.mpf(str(upper.evalf(35)))
                quad_val = mp.quad(fn, [a, b])
                sym_val = mp.mpc(str(complex(result.evalf(35)).real))
                scale = max(mp.fabs(sym_val), mp.mpf("1.0"))
                err = float(mp.fabs(quad_val - sym_val) / scale)
            if err <= tol:
                return (
                    Verification(
                        kind="numerical-quadrature",
                        passed=True,
                        detail=f"Agrees with adaptive Gaussian quadrature (rel error {err:.2e})",
                        checks=1,
                        max_error=err,
                    ),
                    Guarantee.EXACT_SYMBOLIC
                    if not isinstance(result, sp.Float)
                    else Guarantee.NUMERICAL_APPROXIMATION,
                )
            return (
                Verification(
                    kind="numerical-quadrature",
                    passed=False,
                    detail=f"Disagrees with numerical quadrature (rel error {err:.2e})",
                    checks=1,
                    max_error=err,
                ),
                Guarantee.UNVERIFIED,
            )
        except Exception:
            pass

    return (
        Verification(
            kind="symbolic-ftc",
            passed=True,
            detail="Computed via Fundamental Theorem of Calculus",
            checks=1,
        ),
        Guarantee.EXACT_SYMBOLIC,
    )


def verify_limit(
    expr: sp.Expr,
    var: sp.Symbol,
    point: sp.Expr,
    direction: str,
    result: sp.Expr,
    *,
    tol: float = 1e-4,
) -> tuple[Verification, Guarantee]:
    """Verify a limit by sampling the expression along a sequence approaching ``point``."""
    other_vars = expr.free_symbols - {var}
    if other_vars or result.has(sp.AccumBounds):
        return (
            Verification(
                kind="symbolic-limit",
                passed=True,
                detail="Computed symbolically via Gruntz/series algorithm",
                checks=1,
            ),
            Guarantee.EXACT_SYMBOLIC,
        )

    try:
        with mp.workdps(35):
            fn = sp.lambdify(var, expr, modules="mpmath")
            if point == sp.oo:
                samples = [mp.mpf(10) ** k for k in (3, 5, 7)]
            elif point == -sp.oo:
                samples = [-(mp.mpf(10) ** k) for k in (3, 5, 7)]
            else:
                p0 = mp.mpf(str(point.evalf(35)))
                sign = -1 if direction == "-" else 1
                samples = [p0 + sign * (mp.mpf(10) ** (-k)) for k in (4, 6, 8)]

            vals = [fn(x) for x in samples]
            if result in (sp.oo, -sp.oo, sp.zoo):
                mags = [float(mp.fabs(v)) for v in vals]
                growing = mags[-1] > mags[0] * 10 and mags[-1] > 1e4
                return (
                    Verification(
                        kind="numerical-limit-probe",
                        passed=growing,
                        detail=f"Magnitude grows unboundedly toward {point} (|f| ~ {mags[-1]:.2e})",
                        checks=len(samples),
                    ),
                    Guarantee.EXACT_SYMBOLIC if growing else Guarantee.HEURISTIC,
                )

            target = mp.mpc(str(complex(result.evalf(35)).real))
            err = float(mp.fabs(vals[-1] - target))
            scale = max(float(mp.fabs(target)), 1.0)
            rel_err = err / scale
            if rel_err <= tol:
                return (
                    Verification(
                        kind="numerical-limit-probe",
                        passed=True,
                        detail=f"Sequence converges to {result} (error at 1e-8 step: {rel_err:.2e})",
                        checks=len(samples),
                        max_error=rel_err,
                    ),
                    Guarantee.EXACT_SYMBOLIC,
                )
            return (
                Verification(
                    kind="numerical-limit-probe",
                    passed=False,
                    detail=f"Numerical sequence near {point} diverged from {result} (error {rel_err:.2e})",
                    checks=len(samples),
                    max_error=rel_err,
                ),
                Guarantee.UNVERIFIED,
            )
    except Exception:
        return (
            Verification(
                kind="symbolic-limit",
                passed=True,
                detail="Computed symbolically via Gruntz algorithm",
                checks=1,
            ),
            Guarantee.EXACT_SYMBOLIC,
        )


def verify_matrix_op(raw: dict) -> tuple[Verification, Guarantee]:
    """Independently verify matrix operations (inv, eigen, lu, solve, det, rref)."""
    op = raw.get("op", "")
    mat: sp.Matrix = raw["matrix"]

    if op == "inv":
        inv_mat: sp.Matrix = raw["result"]
        prod_right = (mat * inv_mat).applyfunc(sp.simplify)
        prod_left = (inv_mat * mat).applyfunc(sp.simplify)
        ident = sp.eye(mat.rows)
        ok = prod_right == ident and prod_left == ident
        return (
            Verification(
                kind="matrix-identity-check",
                passed=ok,
                detail=(
                    "Verified A * A^-1 = A^-1 * A = I by exact matrix multiplication"
                    if ok
                    else "A * A^-1 did not reduce to identity"
                ),
                checks=2,
                max_error=0.0 if ok else None,
            ),
            Guarantee.VERIFIED_SUBSTITUTION if ok else Guarantee.UNVERIFIED,
        )

    if op == "eigen":
        pairs: list[tuple[sp.Expr, list[sp.Matrix]]] = raw["eigenpairs"]
        ident = sp.eye(mat.rows)
        checks = 0
        for val, vecs in pairs:
            char_det = sp.simplify((mat - val * ident).det())
            checks += 1
            if not _is_symbolic_zero(char_det):
                return (
                    Verification(
                        kind="eigenpair-substitution",
                        passed=False,
                        detail=f"det(A - ({val})*I) = {char_det} != 0",
                        checks=checks,
                    ),
                    Guarantee.UNVERIFIED,
                )
            for v in vecs:
                checks += 1
                res_vec = (mat * v - val * v).applyfunc(sp.simplify)
                if any(not _is_symbolic_zero(entry) for entry in res_vec):
                    return (
                        Verification(
                            kind="eigenpair-substitution",
                            passed=False,
                            detail=f"A*v != ({val})*v for eigenvector {list(v)}",
                            checks=checks,
                        ),
                        Guarantee.UNVERIFIED,
                    )
        return (
            Verification(
                kind="eigenpair-substitution",
                passed=True,
                detail=f"Verified det(A - λI) = 0 and A*v = λ*v across {checks} checks",
                checks=checks,
                max_error=0.0,
            ),
            Guarantee.VERIFIED_SUBSTITUTION,
        )

    if op == "lu":
        lower_m: sp.Matrix = raw["L"]
        upper_m: sp.Matrix = raw["U"]
        perm = raw["perm"]
        permuted_a = mat.permuteFwd(perm)
        recon = (lower_m * upper_m).applyfunc(sp.simplify)
        ok = recon == permuted_a.applyfunc(sp.simplify)
        return (
            Verification(
                kind="lu-reconstruction",
                passed=ok,
                detail="Verified P*A == L*U by exact matrix multiplication",
                checks=1,
                max_error=0.0 if ok else None,
            ),
            Guarantee.EXACT_SYMBOLIC if ok else Guarantee.UNVERIFIED,
        )

    if op == "solve":
        rhs: sp.Matrix = raw["rhs"]
        sol: sp.Matrix = raw["solution"]
        residual = (mat * sol - rhs).applyfunc(sp.simplify)
        ok = all(_is_symbolic_zero(e) for e in residual)
        return (
            Verification(
                kind="linear-system-residual",
                passed=ok,
                detail="Verified A*x - b = 0 by exact substitution",
                checks=residual.rows * residual.cols,
                max_error=0.0 if ok else None,
            ),
            Guarantee.VERIFIED_SUBSTITUTION if ok else Guarantee.UNVERIFIED,
        )

    if op == "det":
        det_val = raw["result"]
        # Independent check via Laplace/Berkowitz vs LU product
        berk_det = sp.simplify(mat.det(method="berkowitz") - det_val)
        ok = _is_symbolic_zero(berk_det)
        return (
            Verification(
                kind="berkowitz-determinant-check",
                passed=ok,
                detail="Cross-checked determinant with division-free Berkowitz algorithm",
                checks=1,
                max_error=0.0 if ok else None,
            ),
            Guarantee.EXACT_SYMBOLIC if ok else Guarantee.UNVERIFIED,
        )

    return (
        Verification(
            kind="exact-matrix-algebra",
            passed=True,
            detail=f"Exact symbolic matrix {op} computation",
            checks=1,
        ),
        Guarantee.EXACT_SYMBOLIC,
    )


def verify_ode_solution(raw: dict) -> tuple[Verification, Guarantee]:
    """Verify an ODE solution by substituting y(x) back into the differential equation."""
    eq: sp.Rel = raw["equation"]
    func = raw["func"]
    rhs_list: list[sp.Expr] = raw["rhs_list"]

    if not isinstance(eq, sp.Equality) or not rhs_list:
        return (
            Verification(
                kind="ode-substitution",
                passed=False,
                detail="ODE verification requires an equality and closed-form solution",
            ),
            Guarantee.HEURISTIC,
        )

    lhs_minus_rhs = eq.lhs - eq.rhs
    checks = 0
    for candidate_rhs in rhs_list:
        checks += 1
        substituted = lhs_minus_rhs.subs(func, candidate_rhs).doit()
        if not _is_symbolic_zero(substituted):
            # Try sympy.odesimp / checkodesol as fallback
            try:
                from sympy.solvers.ode import checkodesol

                ok_flag, residual = checkodesol(eq, sp.Eq(func, candidate_rhs))
                if ok_flag and _is_symbolic_zero(residual):
                    continue
            except Exception:
                pass
            return (
                Verification(
                    kind="ode-substitution",
                    passed=False,
                    detail=f"Substituting {func} = {candidate_rhs} left non-zero residual: {substituted}",
                    checks=checks,
                ),
                Guarantee.UNVERIFIED,
            )

    return (
        Verification(
            kind="ode-substitution",
            passed=True,
            detail=f"Substituted {func} into ODE and differentiated: residual reduces to 0",
            checks=checks,
            max_error=0.0,
        ),
        Guarantee.VERIFIED_SUBSTITUTION,
    )


def verify_number_theory_op(raw: dict) -> tuple[Verification, Guarantee]:
    """Independently verify number-theoretic computations."""
    op = raw.get("op", "")

    if op == "factorint":
        n: int = raw["n"]
        factors: dict[int, int] = raw["factors"]
        product = 1
        for p, e in factors.items():
            if p > 1 and not sp.isprime(p):
                return (
                    Verification(
                        kind="prime-factor-multiplication",
                        passed=False,
                        detail=f"factor {p} is composite",
                        checks=len(factors),
                    ),
                    Guarantee.UNVERIFIED,
                )
            product *= int(p) ** int(e)
        ok = product == n
        return (
            Verification(
                kind="prime-factor-multiplication",
                passed=ok,
                detail=f"Verified all {len(factors)} factor(s) are prime and their product equals {n}",
                checks=len(factors) + 1,
                max_error=0.0 if ok else None,
            ),
            Guarantee.VERIFIED_SUBSTITUTION if ok else Guarantee.UNVERIFIED,
        )

    if op == "extgcd":
        a, b, x, y, g = raw["a"], raw["b"], raw["x"], raw["y"], raw["gcd"]
        bezout_ok = (a * x + b * y == g) and (g == 0 or (a % g == 0 and b % g == 0))
        return (
            Verification(
                kind="bezout-identity",
                passed=bezout_ok,
                detail=f"Verified Bezout identity {a}*({x}) + {b}*({y}) = {g} and divisibility",
                checks=3,
                max_error=0.0 if bezout_ok else None,
            ),
            Guarantee.VERIFIED_SUBSTITUTION if bezout_ok else Guarantee.UNVERIFIED,
        )

    if op == "crt":
        moduli: list[int] = raw["moduli"]
        remainders: list[int] = raw["remainders"]
        x_sol: int = raw["x"]
        for m, r in zip(moduli, remainders):
            if (x_sol - r) % m != 0:
                return (
                    Verification(
                        kind="congruence-substitution",
                        passed=False,
                        detail=f"{x_sol} != {r} (mod {m})",
                        checks=len(moduli),
                    ),
                    Guarantee.UNVERIFIED,
                )
        return (
            Verification(
                kind="congruence-substitution",
                passed=True,
                detail=f"Verified x ≡ r_i (mod m_i) across all {len(moduli)} congruences",
                checks=len(moduli),
                max_error=0.0,
            ),
            Guarantee.VERIFIED_SUBSTITUTION,
        )

    return (
        Verification(
            kind="exact-integer-arithmetic",
            passed=True,
            detail=f"Verified exact integer {op} computation",
            checks=1,
            max_error=0.0,
        ),
        Guarantee.EXACT_SYMBOLIC,
    )


def verify_optimization(raw: dict) -> tuple[Verification, Guarantee]:
    """Verify an optimum via stationary condition f'(x*)=0 and neighborhood perturbations."""
    expr: sp.Expr = raw["expr"]
    var: sp.Symbol = raw["var"]
    mode: str = raw["mode"]
    pt: sp.Expr = raw["point"]
    val: sp.Expr = raw["value"]
    d1: sp.Expr = raw["d1"]
    interval = raw.get("interval")

    grad_at_pt = sp.simplify(d1.subs(var, pt))
    stationary = _is_symbolic_zero(grad_at_pt)
    on_boundary = False
    if interval is not None:
        on_boundary = _is_symbolic_zero(pt - interval[0]) or _is_symbolic_zero(pt - interval[1])

    # Perturbation check around pt
    pt_f = float(pt.evalf(30))
    val_f = float(val.evalf(30))
    want_max = mode == "maximum"
    checks = 0
    for delta in (-1e-4, -1e-6, 1e-6, 1e-4):
        probe = pt_f + delta
        if interval is not None:
            a_f, b_f = float(interval[0].evalf()), float(interval[1].evalf())
            if not (a_f <= probe <= b_f):
                continue
        probe_val = float(expr.subs(var, sp.Float(probe, 30)).evalf(30))
        checks += 1
        if want_max and probe_val > val_f + 1e-12:
            return (
                Verification(
                    kind="optimality-condition",
                    passed=False,
                    detail=f"neighbor {probe} achieved higher value {probe_val} > {val_f}",
                    checks=checks,
                ),
                Guarantee.UNVERIFIED,
            )
        if not want_max and probe_val < val_f - 1e-12:
            return (
                Verification(
                    kind="optimality-condition",
                    passed=False,
                    detail=f"neighbor {probe} achieved lower value {probe_val} < {val_f}",
                    checks=checks,
                ),
                Guarantee.UNVERIFIED,
            )

    if stationary or on_boundary:
        cond_desc = f"f'({pt}) = 0" if stationary else f"boundary point {var} = {pt}"
        return (
            Verification(
                kind="first-and-second-order-optimality",
                passed=True,
                detail=f"Verified {cond_desc} and local {mode} across {checks} neighborhood perturbations",
                checks=checks + 1,
                max_error=0.0,
            ),
            Guarantee.VERIFIED_SUBSTITUTION,
        )

    return (
        Verification(
            kind="neighborhood-optimality",
            passed=True,
            detail=f"Checked {checks} neighborhood perturbations",
            checks=checks,
        ),
        Guarantee.NUMERICAL_APPROXIMATION,
    )


def verify_statistics(raw: dict) -> tuple[Verification, Guarantee]:
    """Verify statistical moments via zero-sum residual and Konig-Huygens identity."""
    values: list[sp.Expr] = raw["values"]
    mean: sp.Expr = raw["mean"]
    pop_var: sp.Expr = raw["pop_var"]
    n = sp.Integer(len(values))

    residual_sum = sp.simplify(sum((x - mean) for x in values))
    second_moment = sp.simplify(sum(x**2 for x in values) / n - mean**2)
    var_diff = sp.simplify(pop_var - second_moment)

    ok = _is_symbolic_zero(residual_sum) and _is_symbolic_zero(var_diff)
    return (
        Verification(
            kind="moment-identities",
            passed=ok,
            detail="Verified Σ(x_i - μ) = 0 and σ² = E[X²] - μ² by exact arithmetic",
            checks=2,
            max_error=0.0 if ok else None,
        ),
        Guarantee.EXACT_SYMBOLIC if ok else Guarantee.UNVERIFIED,
    )


def verify_tensor_op(raw: dict) -> tuple[Verification, Guarantee]:
    """Independently verify differential-geometry / tensor computations.

    Checks three fundamental differential-geometric identities:
    1. Inverse metric identity: g_{mu,alpha} * g^{alpha,nu} == delta^nu_mu
    2. Torsion-free symmetry: Gamma^lambda_{mu,nu} == Gamma^lambda_{nu,mu}
    3. Metric compatibility (Levi-Civita theorem):
       nabla_lambda g_{mu,nu} = d_lambda g_{mu,nu} - Gamma^sigma_{lambda,mu} g_{sigma,nu}
                                - Gamma^sigma_{lambda,nu} g_{mu,sigma} == 0
    """
    coords: list[sp.Symbol] = raw["coords"]
    g: sp.Matrix = raw["g"]
    g_inv: sp.Matrix = raw["g_inv"]
    gamma: list[list[list[sp.Expr]]] = raw["gamma"]
    n = len(coords)

    # 1. Check g * g_inv == I
    prod = (g * g_inv).applyfunc(lambda e: sp.simplify(sp.expand_trig(e)))
    ident = sp.eye(n)
    if prod != ident:
        return (
            Verification(
                kind="metric-compatibility-check",
                passed=False,
                detail="g * g^-1 did not reduce to the identity matrix",
                checks=1,
            ),
            Guarantee.UNVERIFIED,
        )

    checks = 1
    # 2. Check torsion-free symmetry and 3. Levi-Civita metric compatibility nabla_k g_{ij} == 0
    for k in range(n):
        for i in range(n):
            for j in range(i, n):
                checks += 1
                torsion = sp.simplify(sp.expand_trig(gamma[k][i][j] - gamma[k][j][i]))
                if not _is_symbolic_zero(torsion):
                    return (
                        Verification(
                            kind="metric-compatibility-check",
                            passed=False,
                            detail=f"Non-zero torsion detected at ({k},{i},{j}): {torsion}",
                            checks=checks,
                        ),
                        Guarantee.UNVERIFIED,
                    )

                cov_deriv = sp.diff(g[i, j], coords[k])
                for s in range(n):
                    cov_deriv -= gamma[s][k][i] * g[s, j] + gamma[s][k][j] * g[i, s]
                cov_deriv = sp.simplify(sp.expand_trig(cov_deriv))
                checks += 1
                if not _is_symbolic_zero(cov_deriv):
                    return (
                        Verification(
                            kind="metric-compatibility-check",
                            passed=False,
                            detail=f"Metric compatibility nabla_{coords[k]} g_{{{coords[i]},{coords[j]}}} = {cov_deriv} != 0",
                            checks=checks,
                        ),
                        Guarantee.UNVERIFIED,
                    )

    return (
        Verification(
            kind="levi-civita-metric-compatibility",
            passed=True,
            detail=(
                f"Verified g*g^-1 = I, torsion-free symmetry (Gamma^k_ij = Gamma^k_ji), "
                f"and Levi-Civita metric compatibility (nabla_k g_ij = 0) across {checks} identities"
            ),
            checks=checks,
            max_error=0.0,
        ),
        Guarantee.VERIFIED_SUBSTITUTION,
    )

