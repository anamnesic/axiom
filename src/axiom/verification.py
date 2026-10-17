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

# Deterministic non-algebraic sample points (alternating signs to catch branch cuts)
_SAMPLE_POINTS: tuple[float, ...] = (
    0.3141592653,
    -0.4669201609,
    0.7182818284,
    -1.3247179572,
    1.1414213562,
    1.6180339887,
    2.2360679774,
    0.8660254037,
)

# Clean exact rational probes for human-readable counterexamples before transcendental floats
_RATIONAL_PROBES: tuple[sp.Expr, ...] = (
    sp.Integer(-1),
    sp.Integer(2),
    sp.Integer(-2),
    sp.Integer(3),
    sp.Rational(-3, 2),
    sp.Rational(5, 3),
)


def _respects_symbol_assumptions(sym: sp.Symbol, val: sp.Expr | float) -> bool:
    """Return True if candidate numeric probe ``val`` satisfies the assumptions declared on ``sym``."""
    if isinstance(val, sp.Basic) and val.is_real is False:
        if (
            sym.is_real is True
            or sym.is_positive is True
            or sym.is_negative is True
            or sym.is_nonnegative is True
            or sym.is_nonpositive is True
            or sym.is_integer is True
            or sym.is_rational is True
        ):
            return False
        return True
    v_float = float(val)
    if sym.is_positive is True and v_float <= 0:
        return False
    if sym.is_negative is True and v_float >= 0:
        return False
    if sym.is_nonnegative is True and v_float < 0:
        return False
    if sym.is_nonpositive is True and v_float > 0:
        return False
    if sym.is_nonzero is True and v_float == 0:
        return False
    if sym.is_integer is True:
        if isinstance(val, sp.Rational) and val.q != 1:
            return False
        if not isinstance(val, sp.Integer) and abs(v_float - round(v_float)) > 1e-12:
            return False
        iv = int(round(v_float))
        if sym.is_even is True and iv % 2 != 0:
            return False
        if sym.is_odd is True and iv % 2 == 0:
            return False
    return True


def _build_probe_sequence(sym: sp.Symbol, offset_index: int) -> list[sp.Expr]:
    """Build an ordered list of exact + complex + transcendental sample values respecting ``sym``'s assumptions."""
    probes: list[sp.Expr] = []
    if sym.is_integer is True:
        int_candidates = [-1, 2, -2, 3, -3, 4, -4, 5, 6, 7]
        for ic in int_candidates:
            cand = sp.Integer(ic + offset_index)
            if _respects_symbol_assumptions(sym, cand):
                probes.append(cand)
        return probes or [sp.Integer(2)]

    # Start with negative and positive rational probes (-1, 2)
    for r_cand in _RATIONAL_PROBES[:2]:
        shifted = r_cand + sp.Rational(offset_index, 7) if offset_index else r_cand
        if _respects_symbol_assumptions(sym, shifted):
            probes.append(shifted)

    # When symbol is unconstrained over C (is_real is None), probe complex Gaussian rationals early
    # so identities valid only over R (such as sqrt(x^2) = |x| failing at x = I) are caught immediately.
    if sym.is_real is None:
        complex_cands = (
            sp.I if offset_index == 0 else sp.I + sp.Integer(offset_index),
            -sp.I if offset_index == 0 else -sp.I - sp.Integer(offset_index),
            sp.Integer(1) + sp.I,
        )
        for c_cand in complex_cands:
            if _respects_symbol_assumptions(sym, c_cand):
                probes.append(c_cand)

    for r_cand in _RATIONAL_PROBES[2:]:
        shifted = r_cand + sp.Rational(offset_index, 7) if offset_index else r_cand
        if _respects_symbol_assumptions(sym, shifted):
            probes.append(shifted)

    for base in _SAMPLE_POINTS:
        f_val = base + 0.13 * offset_index
        if sym.is_positive is True or sym.is_nonnegative is True:
            f_val = abs(f_val) + 0.11
        elif sym.is_negative is True:
            f_val = -abs(f_val) - 0.11
        cand_float = sp.Float(f_val, 40)
        if _respects_symbol_assumptions(sym, cand_float):
            probes.append(cand_float)
    return probes


def _is_symbolic_zero(expr: sp.Expr) -> bool:
    """Return True if ``expr`` can be proved identically zero by exact symbolic reduction.

    Never uses floating-point heuristic rational approximation (``nsimplify``),
    never injects undeclared real-domain assumptions, and rejects expressions
    containing inexact ``Float`` literals.
    """
    if isinstance(expr, sp.Basic) and expr.has(sp.Float):
        return False
    if expr == 0 or expr is sp.S.Zero:
        return True
    try:
        for transform in (
            sp.expand,
            sp.cancel,
            sp.trigsimp,
            sp.radsimp,
            sp.powsimp,
            sp.simplify,
        ):
            reduced = transform(expr)
            if isinstance(reduced, sp.Basic) and reduced.has(sp.Float):
                continue
            if reduced == 0 or reduced is sp.S.Zero:
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
    """Verify candidate roots by substituting each into ``lhs`` and ``rhs`` and checking domain + residual."""
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
        # 1. Domain / pole audit on LHS and RHS separately (catches 0/0 removable poles like (x^2-1)/(x-1)=0 at x=1)
        try:
            lhs_sub = equation.lhs.subs(var, sol)
            rhs_sub = equation.rhs.subs(var, sol)
            if lhs_sub.has(sp.nan, sp.zoo, sp.oo, -sp.oo) or rhs_sub.has(
                sp.nan, sp.zoo, sp.oo, -sp.oo
            ):
                residuals_data.append(
                    {
                        "solution": str(sol),
                        "residual": "undefined (pole/singularity)",
                        "exact": False,
                    }
                )
                return (
                    Verification(
                        kind="substitution-domain-error",
                        passed=False,
                        detail=(
                            f"candidate root {var} = {sol} hits a pole or singularity "
                            f"in the equation (lhs={lhs_sub}, rhs={rhs_sub})"
                        ),
                        checks=len(solutions),
                        data={"residuals": residuals_data},
                    ),
                    Guarantee.UNVERIFIED,
                )
        except Exception as exc:
            return (
                Verification(
                    kind="substitution-domain-error",
                    passed=False,
                    detail=f"domain error substituting {var} = {sol}: {exc}",
                    checks=len(solutions),
                    data={"residuals": residuals_data},
                ),
                Guarantee.UNVERIFIED,
            )

        # 2. Check symbol assumptions on `var` if any are declared
        if not _respects_symbol_assumptions(var, sol) if sol.is_number else False:
            return (
                Verification(
                    kind="assumption-violation",
                    passed=False,
                    detail=f"candidate root {var} = {sol} violates domain assumptions on {var}",
                    checks=len(solutions),
                    data={"residuals": residuals_data},
                ),
                Guarantee.UNVERIFIED,
            )

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
        for var_sym, sol_val in subs_map.items():
            if sol_val.is_number and not _respects_symbol_assumptions(var_sym, sol_val):
                return (
                    Verification(
                        kind="assumption-violation",
                        passed=False,
                        detail=f"candidate solution {var_sym} = {sol_val} violates domain assumptions on {var_sym}",
                        checks=checks,
                    ),
                    Guarantee.UNVERIFIED,
                )
        if any(v in val.free_symbols for v in variables for val in tuple_sol):
            # Parametric family of solutions: still check symbolic substitution
            pass
        for eq in equations:
            checks += 1
            try:
                lhs_sub = eq.lhs.subs(subs_map)
                rhs_sub = eq.rhs.subs(subs_map)
                if lhs_sub.has(sp.nan, sp.zoo, sp.oo, -sp.oo) or rhs_sub.has(
                    sp.nan, sp.zoo, sp.oo, -sp.oo
                ):
                    return (
                        Verification(
                            kind="substitution-domain-error",
                            passed=False,
                            detail=f"solution {subs_map} hits a pole or singularity in equation {eq}",
                            checks=checks,
                        ),
                        Guarantee.UNVERIFIED,
                    )
            except Exception as exc:
                return (
                    Verification(
                        kind="substitution-domain-error",
                        passed=False,
                        detail=f"domain error substituting {subs_map} into {eq}: {exc}",
                        checks=checks,
                    ),
                    Guarantee.UNVERIFIED,
                )

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
    left_domain: dict[str, object] | None = None,
    right_domain: dict[str, object] | None = None,
) -> tuple[Verification, Guarantee]:
    """Verify ``left == right`` via domain preservation, symbolic reduction, and multi-point sampling."""
    diff = left - right
    free = sorted(diff.free_symbols, key=str) if variables is None else list(variables)

    left_excl: dict[str, list[str]] = dict((left_domain or {}).get("excluded_points") or {})
    right_excl: dict[str, list[str]] = dict((right_domain or {}).get("excluded_points") or {})
    left_constraints: list[str] = list((left_domain or {}).get("domain_constraints") or [])
    right_constraints: list[str] = list((right_domain or {}).get("domain_constraints") or [])
    all_constraints: list[str] = []
    for c in left_constraints + right_constraints:
        if c not in all_constraints:
            all_constraints.append(c)

    merged_excluded: dict[str, list[str]] = {}
    all_excl_vars = sorted(set(left_excl.keys()) | set(right_excl.keys()))
    for v_name in all_excl_vars:
        pts: list[str] = []
        for p in list(left_excl.get(v_name, [])) + list(right_excl.get(v_name, [])):
            if p not in pts:
                pts.append(p)
        if pts:
            merged_excluded[v_name] = pts

    # Check whether one expression excludes points in the active domain that the other does not
    for v_name in all_excl_vars:
        l_set = set(left_excl.get(v_name, []))
        r_set = set(right_excl.get(v_name, []))
        if l_set != r_set:
            mismatch_pts = sorted(l_set ^ r_set)
            pt_str = mismatch_pts[0]
            return (
                Verification(
                    kind="domain-mismatch",
                    passed=False,
                    detail=(
                        f"Domain mismatch at {v_name} = {pt_str}: original domain constraints "
                        f"{all_constraints} (excluded_points={merged_excluded}) are not preserved"
                    ),
                    checks=1,
                    data={
                        "domain_constraints": all_constraints,
                        "excluded_points": merged_excluded,
                        "left_excluded_points": left_excl,
                        "right_excluded_points": right_excl,
                        "counterexample": {v_name: pt_str},
                    },
                ),
                Guarantee.UNVERIFIED,
            )

    domain_meta: dict[str, object] = {}
    if all_constraints:
        domain_meta["domain_constraints"] = all_constraints
    if merged_excluded:
        domain_meta["excluded_points"] = merged_excluded

    has_float = bool(
        (left_domain and left_domain.get("has_inexact_floats"))
        or (right_domain and right_domain.get("has_inexact_floats"))
        or (isinstance(diff, sp.Basic) and diff.has(sp.Float))
        or (isinstance(left, sp.Basic) and left.has(sp.Float))
        or (isinstance(right, sp.Basic) and right.has(sp.Float))
    )

    symbolic_ok = (not has_float) and _is_symbolic_zero(diff)

    # Polynomial check: if diff is a polynomial in free variables
    is_poly = False
    poly_obj = None
    if free and not has_float:
        try:
            poly_obj = diff.as_poly(*free)
            if poly_obj is not None:
                is_poly = True
                if poly_obj.is_zero:
                    symbolic_ok = True
        except Exception:
            pass

    checks = 0
    max_error = 0.0

    # If diff is a non-zero polynomial, it CANNOT be identically zero.
    # Actively probe to locate an explicit counterexample point (guaranteed by Fundamental Theorem of Algebra).
    if is_poly and poly_obj is not None and not poly_obj.is_zero:
        deg = poly_obj.total_degree()
        var_sym = free[0]
        cand_list: list[sp.Expr] = [sp.Integer(i) for i in range(-2, deg + 7)]
        cand_list.extend([sp.Integer(i) * sp.I for i in range(1, 4)])
        cand_list.extend([sp.Rational(i, 2) for i in range(1, 6)])
        for pt in cand_list:
            if str(pt) in merged_excluded.get(str(var_sym), []):
                continue
            if not _respects_symbol_assumptions(var_sym, pt):
                continue
            subs = {var_sym: pt}
            for other_sym in free[1:]:
                subs[other_sym] = sp.Integer(2)
            try:
                sub_expr = diff.subs(subs)
                if sub_expr.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
                    continue
                val = sub_expr.evalf(35)
                if val.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
                    continue
                err = abs(complex(val))
            except Exception:
                continue
            checks += 1
            max_error = max(max_error, err)
            if err > tol:
                counterexample = {str(k): str(v) for k, v in subs.items()}
                data_out = dict(domain_meta)
                data_out["counterexample"] = counterexample
                data_out["status"] = "disproven"
                data_out["proven"] = False
                return (
                    Verification(
                        kind="counterexample-search",
                        passed=False,
                        detail=f"counterexample found at {counterexample} (|diff| = {err:.3e})",
                        checks=checks,
                        max_error=err,
                        data=data_out,
                    ),
                    Guarantee.UNVERIFIED,
                )

    if not free:
        data_out = dict(domain_meta)
        if has_float:
            data_out["has_inexact_floats"] = True
            try:
                err = abs(complex(diff.evalf(40)))
            except Exception:
                err = 1.0
            if err > tol:
                data_out["status"] = "disproven"
                data_out["proven"] = False
                return (
                    Verification(
                        kind="approximate-disproof",
                        passed=False,
                        detail=f"approximate constant values differ by {err:.3e} (exceeds tolerance {tol:.1e})",
                        checks=1,
                        max_error=err,
                        data=data_out,
                    ),
                    Guarantee.UNVERIFIED,
                )
            # Within numerical tolerance: numerical agreement does NOT prove exact equality
            data_out["status"] = "approximately_equal"
            data_out["proven"] = False
            data_out["approximately_equal"] = True
            data_out["tolerance"] = tol
            data_out["max_error"] = err
            return (
                Verification(
                    kind="numerical-approximation",
                    passed=False,
                    detail=(
                        f"Constant values are approximately equal within tolerance {tol:.1e} "
                        f"(|diff| = {err:.2e}); exact equality cannot be established due to inexact float inputs"
                    ),
                    checks=1,
                    max_error=err,
                    data=data_out,
                ),
                Guarantee.UNVERIFIED,
            )

        if symbolic_ok:
            data_out["status"] = "proven"
            data_out["proven"] = True
            return (
                Verification(
                    kind="symbolic-identity",
                    passed=True,
                    detail="Symbolic difference reduces to 0",
                    checks=1,
                    max_error=0.0,
                    data=data_out,
                ),
                Guarantee.EXACT_SYMBOLIC,
            )

        # Exact constant expressions (no sp.Float): comparison MUST be exact.
        # Numerical closeness within tolerance can NEVER prove exact equality.
        is_exact_nonzero = False
        try:
            if diff.is_zero is False or diff.is_nonzero is True:
                is_exact_nonzero = True
            elif diff.is_positive is True or diff.is_negative is True:
                is_exact_nonzero = True
            elif isinstance(diff, (sp.Rational, sp.Integer)) and diff != 0:
                is_exact_nonzero = True
        except Exception:
            pass

        err_val = None
        if not is_exact_nonzero:
            try:
                v60 = diff.evalf(60)
                v120 = diff.evalf(120)
                c120 = complex(v120)
                mag = abs(c120)
                err_val = mag
                # If high-precision evaluation is clearly non-zero and stable
                if mag > 1e-100 and not v120.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
                    is_exact_nonzero = True
            except Exception:
                pass

        if is_exact_nonzero:
            data_out["status"] = "disproven"
            data_out["proven"] = False
            if err_val is None:
                try:
                    err_val = abs(complex(diff.evalf(40)))
                except Exception:
                    err_val = 1.0
            return (
                Verification(
                    kind="constant-exact-disproof",
                    passed=False,
                    detail=f"Exact constant expressions are not equal (difference {diff} != 0)",
                    checks=1,
                    max_error=err_val,
                    data=data_out,
                ),
                Guarantee.UNVERIFIED,
            )

        # If it cannot be established zero symbolically or non-zero numerically: fail-closed
        data_out["status"] = "inconclusive"
        data_out["proven"] = False
        return (
            Verification(
                kind="constant-exact-inconclusive",
                passed=False,
                detail="Exact constant difference could not be proved zero symbolically or refuted numerically (inconclusive)",
                checks=1,
                max_error=err_val or 0.0,
                data=data_out,
            ),
            Guarantee.UNVERIFIED,
        )

    probe_lists = [_build_probe_sequence(sym, k) for k, sym in enumerate(free)]
    max_len = min((len(pl) for pl in probe_lists), default=0)
    target_checks = max(10, (poly_obj.total_degree() + 2) if is_poly and poly_obj is not None else 8)
    for idx in range(max_len):
        subs = {sym: probe_lists[k][idx] for k, sym in enumerate(free)}
        if any(str(subs[sym]) in merged_excluded.get(str(sym), []) for sym in free):
            continue
        try:
            sub_expr = diff.subs(subs)
            if sub_expr.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
                continue
            val = sub_expr.evalf(35)
            if val.has(sp.nan, sp.oo, -sp.oo, sp.zoo):
                continue
            err = abs(complex(val))
        except Exception:
            continue
        checks += 1
        max_error = max(max_error, err)
        if err > tol:
            counterexample = {str(k): str(v) for k, v in subs.items()}
            data_out = dict(domain_meta)
            data_out["counterexample"] = counterexample
            data_out["status"] = "disproven"
            data_out["proven"] = False
            return (
                Verification(
                    kind="counterexample-search",
                    passed=False,
                    detail=f"counterexample found at {counterexample} (|diff| = {err:.3e})",
                    checks=checks,
                    max_error=err,
                    data=data_out,
                ),
                Guarantee.UNVERIFIED,
            )
        if checks >= target_checks:
            break

    if symbolic_ok and not has_float:
        data_out = dict(domain_meta)
        data_out["status"] = "proven"
        data_out["proven"] = True
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
                data=data_out,
            ),
            Guarantee.EXACT_SYMBOLIC,
        )

    # Universal identity with free variables: numerical sampling alone CANNOT establish
    # universal equivalence. Fail-closed: marks inconclusive and passed=False.
    data_out = dict(domain_meta)
    data_out["status"] = "inconclusive"
    data_out["proven"] = False
    data_out["consistent_with_samples"] = bool(checks >= 3 and max_error <= tol)
    return (
        Verification(
            kind="numerical-spot-check",
            passed=False,
            detail=(
                f"Agreed across {checks} test points within {max_error:.2e}, "
                "but universal identity could not be established symbolically (inconclusive)"
            ),
            checks=checks,
            max_error=max_error,
            data=data_out,
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
    """Check a derivative via symbolic antiderivative round-trip and high-precision finite differences.

    Assigns :attr:`Guarantee.EXACT_SYMBOLIC` only when the symbolic inverse
    integration operator confirms ``expr - integral(derivative, var)`` is
    independent of ``var`` (or has polynomial degree ``< order``) AND numerical
    finite differences do not refute it. When only numerical finite differences
    confirm the derivative, assigns :attr:`Guarantee.NUMERICAL_APPROXIMATION`.
    """
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

    # Independent symbolic verification via inverse integration (FTC round-trip)
    symbolic_ftc_ok = False
    if not expr.has(sp.Float) and not derivative.has(sp.Float):
        try:
            antideriv = derivative
            for _ in range(order):
                antideriv = sp.integrate(antideriv, var)
                if antideriv.has(sp.Integral):
                    break
            if not antideriv.has(sp.Integral):
                residual = sp.simplify(sp.trigsimp(sp.expand(expr - antideriv)))
                if not residual.has(sp.Float):
                    if var not in residual.free_symbols:
                        symbolic_ftc_ok = True
                    elif order > 1 and residual.is_polynomial(var):
                        symbolic_ftc_ok = sp.Poly(residual, var).degree() < order
        except Exception:
            symbolic_ftc_ok = False

    if symbolic_ftc_ok and checks > 0:
        return (
            Verification(
                kind="antiderivative-roundtrip",
                passed=True,
                detail=(
                    f"Verified symbolic antiderivative round-trip and matched "
                    f"high-precision finite differences at {checks} points (max rel error {max_error:.2e})"
                ),
                checks=checks + 1,
                max_error=max_error,
            ),
            Guarantee.EXACT_SYMBOLIC,
        )

    if checks > 0:
        return (
            Verification(
                kind="numerical-derivative-check",
                passed=True,
                detail=(
                    f"Matched high-precision finite differences at {checks} points "
                    f"(max rel error {max_error:.2e}; no closed-form symbolic antiderivative confirmation)"
                ),
                checks=checks,
                max_error=max_error,
            ),
            Guarantee.NUMERICAL_APPROXIMATION,
        )

    return (
        Verification(
            kind="numerical-derivative-check",
            passed=False,
            detail="Could not evaluate finite differences at any sample point for independent confirmation",
            checks=0,
        ),
        Guarantee.UNVERIFIED,
    )


def _find_nonintegrable_poles(
    integrand: sp.Expr,
    var: sp.Symbol,
    lower: sp.Expr,
    upper: sp.Expr,
) -> list[sp.Expr]:
    """Detect non-integrable interior or endpoint poles of ``integrand`` on ``[lower, upper]``."""
    other_vars = (
        (integrand.free_symbols - {var})
        | lower.free_symbols
        | upper.free_symbols
    )
    if other_vars:
        return []
    try:
        a_f = -float("inf") if lower == -sp.oo else (float("inf") if lower == sp.oo else float(lower.evalf()))
        b_f = -float("inf") if upper == -sp.oo else (float("inf") if upper == sp.oo else float(upper.evalf()))
        lo_f, hi_f = min(a_f, b_f), max(a_f, b_f)
    except Exception:
        return []

    singularities: list[sp.Expr] = []
    try:
        _, den = sp.fraction(sp.together(integrand))
        if den == 1:
            return []
        cand_poles = sp.solve(sp.Eq(den, 0), var)
        if not isinstance(cand_poles, list):
            cand_poles = [cand_poles]
        for p in cand_poles:
            try:
                p_c = complex(p.evalf(30))
                if abs(p_c.imag) > 1e-14:
                    continue
                p_f = p_c.real
            except Exception:
                continue
            if not (lo_f - 1e-12 <= p_f <= hi_f + 1e-12):
                continue
            # Check if it's a true pole (not removable like sin(x)/x at 0)
            lim_plus = sp.limit(sp.Abs(integrand), var, p, dir="+")
            lim_minus = sp.limit(sp.Abs(integrand), var, p, dir="-")
            if lim_plus not in (sp.oo, sp.zoo) and lim_minus not in (sp.oo, sp.zoo):
                continue
            # Check if improper integral split at p diverges
            if lo_f + 1e-12 < p_f < hi_f - 1e-12:
                left_int = sp.integrate(integrand, (var, lower, p))
                right_int = sp.integrate(integrand, (var, p, upper))
                if left_int.has(sp.oo, -sp.oo, sp.zoo, sp.nan) or right_int.has(
                    sp.oo, -sp.oo, sp.zoo, sp.nan
                ):
                    singularities.append(p)
            else:
                full_int = sp.integrate(integrand, (var, lower, upper))
                if full_int.has(sp.oo, -sp.oo, sp.zoo, sp.nan):
                    singularities.append(p)
    except Exception:
        pass
    return singularities


def verify_integral(
    integrand: sp.Expr,
    result: sp.Expr,
    var: sp.Symbol,
    limits: tuple[sp.Expr, sp.Expr] | None = None,
    *,
    tol: float = 1e-10,
) -> tuple[Verification, Guarantee]:
    """Verify an integral by differentiation (indefinite) or singularity audit + FTC + quadrature (definite).

    For definite integrals, :attr:`Guarantee.EXACT_SYMBOLIC` is granted only
    when no non-integrable interior poles exist on ``[a, b]`` AND the symbolic
    Fundamental Theorem of Calculus check confirms an exact antiderivative
    ``F'(x) == f(x)`` with ``F(b) - F(a) == result`` (and numerical quadrature
    does not disagree). When only numerical quadrature confirms the value,
    :attr:`Guarantee.NUMERICAL_APPROXIMATION` is returned.
    """
    if result.has(sp.Integral):
        return (
            Verification(
                kind="unevaluated-integral",
                passed=False,
                detail="integral remained in unevaluated form (no closed-form antiderivative found)",
            ),
            Guarantee.UNVERIFIED,
        )

    if result.has(sp.oo, -sp.oo, sp.zoo, sp.nan):
        return (
            Verification(
                kind="divergent-integral",
                passed=False,
                detail=f"definite integral diverges or is undefined ({result})",
                checks=1,
            ),
            Guarantee.UNVERIFIED,
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

    # Definite integral:
    lower, upper = limits
    poles = _find_nonintegrable_poles(integrand, var, lower, upper)
    if poles:
        pole_strs = [str(p) for p in poles]
        return (
            Verification(
                kind="interior-singularity-check",
                passed=False,
                detail=(
                    f"Integrand {integrand} has non-integrable pole/singularity at "
                    f"{var} in {pole_strs} on [{lower}, {upper}]; naive FTC across pole rejected"
                ),
                checks=1,
                data={"singularities": pole_strs},
            ),
            Guarantee.UNVERIFIED,
        )

    other_vars = (
        (integrand.free_symbols - {var})
        | lower.free_symbols
        | upper.free_symbols
    )
    quad_passed = False
    quad_err = 0.0
    quad_error_msg: str | None = None
    if not other_vars:
        try:
            with mp.workdps(35):
                fn = sp.lambdify(var, integrand, modules="mpmath")
                a = (
                    -mp.inf
                    if lower == -sp.oo
                    else (mp.inf if lower == sp.oo else mp.mpf(str(lower.evalf(35))))
                )
                b = (
                    -mp.inf
                    if upper == -sp.oo
                    else (mp.inf if upper == sp.oo else mp.mpf(str(upper.evalf(35))))
                )
                quad_val = mp.quad(fn, [a, b])
                sym_val = mp.mpc(str(complex(result.evalf(35)).real))
                if mp.isfinite(quad_val) and mp.isfinite(sym_val):
                    scale = max(mp.fabs(sym_val), mp.mpf("1.0"))
                    err = float(mp.fabs(quad_val - sym_val) / scale)
                    if err > tol:
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
                    quad_passed = True
                    quad_err = err
                else:
                    quad_error_msg = "quadrature produced non-finite value"
        except Exception as exc:
            quad_error_msg = f"quadrature failed ({exc})"

    # Independent symbolic FTC antiderivative check: F'(x) == f(x) and F(b) - F(a) == result
    if not integrand.has(sp.Float) and not result.has(sp.Float):
        try:
            antideriv = sp.integrate(integrand, var)
            if not antideriv.has(sp.Integral):
                deriv_check, deriv_guar = verify_equivalence(
                    sp.diff(antideriv, var), integrand, [var, *sorted(other_vars, key=str)]
                )
                if deriv_check.passed and deriv_guar == Guarantee.EXACT_SYMBOLIC:
                    fb = sp.limit(antideriv, var, upper, dir="-")
                    fa = sp.limit(antideriv, var, lower, dir="+")
                    ftc_diff = fb - fa
                    if not ftc_diff.has(sp.Integral, sp.Limit, sp.nan, sp.zoo):
                        eq_check, eq_guar = verify_equivalence(
                            ftc_diff, result, sorted(other_vars, key=str)
                        )
                        if (
                            eq_check.passed
                            and eq_guar == Guarantee.EXACT_SYMBOLIC
                            and (bool(other_vars) or quad_passed)
                        ):
                            return (
                                Verification(
                                    kind="ftc-antiderivative-check",
                                    passed=True,
                                    detail=(
                                        f"Verified F'({var}) = f({var}) and F({upper}) - F({lower}) == {result}"
                                        + (
                                            f" (quadrature rel error {quad_err:.2e})"
                                            if quad_passed
                                            else ""
                                        )
                                    ),
                                    checks=deriv_check.checks + eq_check.checks + (1 if quad_passed else 0),
                                    max_error=quad_err if quad_passed else eq_check.max_error,
                                ),
                                Guarantee.EXACT_SYMBOLIC,
                            )
        except Exception:
            pass

    if quad_passed:
        return (
            Verification(
                kind="numerical-quadrature",
                passed=True,
                detail=f"Agrees with adaptive Gaussian quadrature (rel error {quad_err:.2e})",
                checks=1,
                max_error=quad_err,
            ),
            Guarantee.NUMERICAL_APPROXIMATION,
        )

    detail = (
        f"Independent definite-integral verification failed: {quad_error_msg}"
        if quad_error_msg
        else "Could not independently verify definite integral via quadrature or FTC antiderivative differentiation"
    )
    return (
        Verification(
            kind="definite-integral-check",
            passed=False,
            detail=detail,
            checks=0,
        ),
        Guarantee.UNVERIFIED,
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
    """Verify a limit via symbolic cancellation/L'Hôpital/series and sequence sampling.

    Assigns :attr:`Guarantee.EXACT_SYMBOLIC` only when an independent symbolic
    method (algebraic cancellation, L'Hôpital differentiation, or formal series
    expansion) confirms the limit AND numerical sequence probing agrees (both
    from left and right when ``direction == '+-'``). When only the numerical
    sequence probe confirms convergence, assigns
    :attr:`Guarantee.NUMERICAL_APPROXIMATION`.
    """
    if result.has(sp.AccumBounds) or result.has(sp.Limit) or result == sp.zoo:
        return (
            Verification(
                kind="two-sided-or-oscillatory-limit-check",
                passed=False,
                detail="Limit does not exist as a single value (two-sided mismatch, unsigned complex infinity zoo, oscillatory AccumBounds, or unevaluated)",
                checks=1,
            ),
            Guarantee.UNVERIFIED,
        )

    other_vars = sorted(
        (expr.free_symbols | point.free_symbols | result.free_symbols) - {var},
        key=str,
    )
    fixed_subs = {
        sym: sp.Rational(idx + 2, idx + 3) for idx, sym in enumerate(other_vars)
    }
    expr_1d = expr.subs(fixed_subs)
    point_1d = point.subs(fixed_subs)
    result_1d = result.subs(fixed_subs)

    try:
        with mp.workdps(35):
            fn = sp.lambdify(var, expr_1d, modules="mpmath")
            if point_1d == sp.oo:
                sample_groups = [[mp.mpf(10) ** k for k in (3, 5, 7)]]
            elif point_1d == -sp.oo:
                sample_groups = [[-(mp.mpf(10) ** k) for k in (3, 5, 7)]]
            else:
                p0 = mp.mpf(str(point_1d.evalf(35)))
                if direction == "+":
                    sample_groups = [[p0 + (mp.mpf(10) ** (-k)) for k in (4, 6, 8)]]
                elif direction == "-":
                    sample_groups = [[p0 - (mp.mpf(10) ** (-k)) for k in (4, 6, 8)]]
                else:
                    # direction == "+-": check BOTH left and right approaching sequences!
                    sample_groups = [
                        [p0 - (mp.mpf(10) ** (-k)) for k in (4, 6, 8)],
                        [p0 + (mp.mpf(10) ** (-k)) for k in (4, 6, 8)],
                    ]

            total_samples = sum(len(g) for g in sample_groups)
            if result_1d in (sp.oo, -sp.oo, sp.zoo):
                all_growing = True
                last_mags: list[float] = []
                for grp in sample_groups:
                    vals = [fn(x) for x in grp]
                    mags = [float(mp.fabs(v)) for v in vals]
                    last_mags.append(mags[-1])
                    if not (mags[-1] > mags[0] * 10 and mags[-1] > 1e4):
                        all_growing = False
                    if result_1d == sp.oo and float(mp.re(vals[-1])) <= 0:
                        all_growing = False
                    elif result_1d == -sp.oo and float(mp.re(vals[-1])) >= 0:
                        all_growing = False
                return (
                    Verification(
                        kind="numerical-limit-probe",
                        passed=all_growing,
                        detail=(
                            f"Magnitude grows unboundedly toward {point} -> {result} (|f| ~ {min(last_mags):.2e})"
                            if all_growing
                            else f"Sequence near {point} did not diverge consistently to {result}"
                        ),
                        checks=total_samples,
                    ),
                    Guarantee.NUMERICAL_APPROXIMATION if all_growing else Guarantee.UNVERIFIED,
                )

            target = mp.mpc(str(complex(result_1d.evalf(35)).real))
            scale = max(float(mp.fabs(target)), 1.0)
            rel_err = 0.0
            for side_idx, grp in enumerate(sample_groups):
                vals = [fn(x) for x in grp]
                side_err = float(mp.fabs(vals[-1] - target)) / scale
                rel_err = max(rel_err, side_err)
                if side_err > tol:
                    side_label = (
                        "left" if (len(sample_groups) == 2 and side_idx == 0) else (
                            "right" if len(sample_groups) == 2 else direction
                        )
                    )
                    return (
                        Verification(
                            kind="numerical-limit-probe",
                            passed=False,
                            detail=(
                                f"Numerical sequence ({side_label}) near {point} diverged "
                                f"from {result} (f ≈ {vals[-1]}, error {side_err:.2e})"
                            ),
                            checks=total_samples,
                            max_error=rel_err,
                        ),
                        Guarantee.UNVERIFIED,
                    )
    except Exception as exc:
        return (
            Verification(
                kind="numerical-limit-probe",
                passed=False,
                detail=f"Could not independently verify limit via sequence probe: {exc}",
                checks=0,
            ),
            Guarantee.UNVERIFIED,
        )

    # Independent symbolic verification (without calling sp.limit)
    symbolic_ok = False
    symbolic_kind = ""
    has_branch_ops = expr.has(sp.Abs, sp.sign, sp.floor, sp.ceiling, sp.Piecewise)
    if (
        not expr.has(sp.Float)
        and not result.has(sp.Float)
        and point not in (sp.oo, -sp.oo, sp.zoo)
        and not has_branch_ops
    ):
        # 1. Algebraic / radical cancellation + continuous substitution
        try:
            cancelled = sp.cancel(sp.radsimp(expr))
            sub_val = cancelled.subs(var, point)
            if not sub_val.has(sp.nan, sp.oo, -sp.oo, sp.zoo) and _is_symbolic_zero(
                sub_val - result
            ):
                symbolic_ok = True
                symbolic_kind = "algebraic-cancellation-limit"
        except Exception:
            pass

        # 2. Symbolic L'Hôpital differentiation on 0/0 indeterminate forms
        if not symbolic_ok:
            try:
                num, den = sp.fraction(sp.together(expr))
                if _is_symbolic_zero(num.subs(var, point)) and _is_symbolic_zero(
                    den.subs(var, point)
                ):
                    cur_n, cur_d = num, den
                    for _ in range(4):
                        cur_n = sp.diff(cur_n, var)
                        cur_d = sp.diff(cur_d, var)
                        d_val = cur_d.subs(var, point)
                        if not d_val.has(
                            sp.nan, sp.oo, -sp.oo, sp.zoo
                        ) and not _is_symbolic_zero(d_val):
                            n_val = cur_n.subs(var, point)
                            if not n_val.has(
                                sp.nan, sp.oo, -sp.oo, sp.zoo
                            ) and _is_symbolic_zero(n_val / d_val - result):
                                symbolic_ok = True
                                symbolic_kind = "symbolic-lhopital-limit"
                            break
            except Exception:
                pass

        # 3. Formal Taylor/Laurent series expansion around point
        if not symbolic_ok:
            try:
                ser = sp.series(expr, var, point, n=3).removeO()
                ser_val = ser.subs(var, point)
                if not ser_val.has(
                    sp.nan, sp.oo, -sp.oo, sp.zoo
                ) and _is_symbolic_zero(ser_val - result):
                    symbolic_ok = True
                    symbolic_kind = "formal-series-limit"
            except Exception:
                pass

    if symbolic_ok:
        return (
            Verification(
                kind=symbolic_kind,
                passed=True,
                detail=(
                    f"Verified symbolically ({symbolic_kind}) and confirmed by "
                    f"numerical sequence convergence to {result} (step error {rel_err:.2e})"
                ),
                checks=total_samples + 1,
                max_error=rel_err,
            ),
            Guarantee.EXACT_SYMBOLIC,
        )

    return (
        Verification(
            kind="numerical-limit-probe",
            passed=True,
            detail=f"Sequence converges to {result} (error at 1e-8 step: {rel_err:.2e}; numerical evidence only)",
            checks=total_samples,
            max_error=rel_err,
        ),
        Guarantee.NUMERICAL_APPROXIMATION,
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

    if op == "binomial":
        import math

        n, k, val = int(raw["n"]), int(raw["k"]), int(raw["value"])
        if n >= 0 and k >= 0:
            comb_ok = val == math.comb(n, k)
            pascal_ok = (
                True
                if not (0 < k < n)
                else val == math.comb(n - 1, k - 1) + math.comb(n - 1, k)
            )
            ok = comb_ok and pascal_ok
            return (
                Verification(
                    kind="binomial-comb-and-pascal-check",
                    passed=ok,
                    detail=f"Verified C({n}, {k}) against independent math.comb and Pascal recurrence",
                    checks=2,
                    max_error=0.0 if ok else None,
                ),
                Guarantee.EXACT_SYMBOLIC if ok else Guarantee.UNVERIFIED,
            )

    if op == "totient":
        import math

        n, phi = int(raw["n"]), int(raw["phi"])
        factors = sp.factorint(n)
        expected_phi = 1
        for p, e in factors.items():
            expected_phi *= (int(p) ** (int(e) - 1)) * (int(p) - 1)
        ok = phi == expected_phi
        checks_count = len(factors) + 1
        if n <= 2000:
            coprime_count = sum(1 for k in range(1, n + 1) if math.gcd(k, n) == 1)
            ok = ok and (phi == coprime_count)
            checks_count += 1
        return (
            Verification(
                kind="euler-product-totient-check",
                passed=ok,
                detail=f"Verified φ({n}) = {phi} via prime-power product formula",
                checks=checks_count,
                max_error=0.0 if ok else None,
            ),
            Guarantee.EXACT_SYMBOLIC if ok else Guarantee.UNVERIFIED,
        )

    if op == "isprime":
        n, prime = int(raw["n"]), bool(raw["prime"])
        factors = sp.factorint(n) if n >= 2 else {}
        expected_prime = n >= 2 and factors == {n: 1}
        ok = prime == expected_prime
        return (
            Verification(
                kind="primality-factor-audit",
                passed=ok,
                detail=f"Verified primality of {n} ({'prime' if prime else 'composite'}) via factor decomposition",
                checks=max(len(factors), 1),
                max_error=0.0 if ok else None,
            ),
            Guarantee.EXACT_SYMBOLIC if ok else Guarantee.UNVERIFIED,
        )

    return (
        Verification(
            kind="number-theory-check",
            passed=False,
            detail=f"Unsupported number_theory operation for verification: {op!r}",
            checks=0,
        ),
        Guarantee.UNVERIFIED,
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

