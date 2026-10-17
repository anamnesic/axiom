"""AXIOM benchmark suite across algebraic, calculus, matrix, ODE, and number-theory tasks."""

from __future__ import annotations

import json
import time
from typing import Callable

from axiom import Axiom


def run_suite() -> dict[str, object]:
    ax = Axiom()
    tasks: list[tuple[str, Callable[[], object]]] = [
        ("solve_quadratic", lambda: ax.solve("x^2 - 5*x + 6 = 0")),
        ("solve_system_2x2", lambda: ax.solve("x + y = 5; x - y = 1")),
        ("simplify_trig", lambda: ax.simplify("sin(x)^2 + cos(x)^2")),
        ("differentiate_product", lambda: ax.differentiate("x^4 * exp(x) * sin(x)")),
        ("integrate_indefinite", lambda: ax.integrate("sin(x)^2", variable="x")),
        ("integrate_definite", lambda: ax.integrate("sin(x)", variable="x", lower="0", upper="pi")),
        ("matrix_eigen_2x2", lambda: ax.matrix("[[4, 1], [2, 3]]", operation="eigen")),
        ("ode_first_order", lambda: ax.ode("diff(y(x), x) + 2*y(x) = exp(x)")),
        ("nt_factorint", lambda: ax.number_theory("factorint", n=360360)),
        ("optimize_quadratic", lambda: ax.optimize("x^2 - 6*x + 13", mode="minimize")),
        ("tensor_sphere_curvature", lambda: ax.tensor("sphere")),
        ("mathlib_search", lambda: ax.search_mathlib("binomial square")),
    ]

    results = []
    for name, fn in tasks:
        t0 = time.perf_counter()
        res = fn()
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        results.append(
            {
                "task": name,
                "ok": res.ok,
                "verified": res.verified,
                "guarantee": res.guarantee.value,
                "elapsed_ms": round(elapsed_ms, 2),
            }
        )

    return {
        "tasks_count": len(results),
        "all_verified": all(r["verified"] for r in results),
        "total_ms": round(sum(r["elapsed_ms"] for r in results), 2),
        "benchmarks": results,
    }


if __name__ == "__main__":
    print(json.dumps(run_suite(), indent=2))
