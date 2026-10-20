"""EXP-0001: Verificação Quantitativa de Integridade de Domínio e Comportamento Fail-Closed.

Compara o comportamento do AXIOM v0.2.1 frente a um CAS ingênuo (SymPy cru sem contratos)
em 21 casos críticos de fronteira de domínio, branch cuts, singularidades e polos.

Uso:
    python experiments/exp-0001/run.py

Nota de proveniência (ADR-0031): o baseline "Naive CAS" é um *emulador* do
comportamento de um CAS sem contrato, executado sobre SymPy. Ele NÃO é o
SymPy 1.12 cru, e a ramo ``formal_proof`` é *simulado* (não invoca o
compilador Lean). Ver ``BASELINE_PROVENANCE`` e ``summary["baseline"]`` para
os metadados exatos registrados em ``results.json``.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

# Garantir importação do pacote local axiom
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from axiom import Axiom, Guarantee
import sympy as sp


# Metadados de proveniência do baseline. Registrados em ``results.json`` para
# que qualquer leitor possa distinguir *medição observada* de *simulação*.
BASELINE_PROVENANCE = {
    "name": "Naive CAS (emulated)",
    "kind": "emulated-on-sympy",
    "sympy_version": sp.__version__,
    "description": (
        "Emulation of an unguarded CAS: sp.simplify / sp.evalf without AST "
        "denominator analysis, without orthogonal proof contracts, and with a "
        "fixed 6-point sampling probe (-1, 2, I, -I, 1+I, -2) that is applied "
        "to the residual before declaring equivalence."
    ),
    "includes_fixed_point_sampling": True,
    "fixed_probe_points": ["-1", "2", "I", "-I", "1 + I", "-2"],
    "formal_proof_branch": "simulated: returns accepted=True without invoking the Lean compiler",
    "is_observed_measurement": False,
    "caveat": (
        "The formal_proof baseline row is a SIMULATION of an unaudited Lean "
        "runner, not an observed execution of an external compiler. The "
        "reported false-positive rate therefore describes the emulation, not "
        "a measured SymPy/Lean toolchain."
    ),
}


def run_naive_cas(test_type: str, item: dict) -> dict:
    """Emulate the execution of an unguarded CAS.

    This is *not* unwrapped SymPy: the equivalence branch adds a fixed
    6-point sampling probe on the residual, and the ``formal_proof`` branch
    is simulated (the Lean compiler is never invoked). See
    :data:`BASELINE_PROVENANCE`.
    """
    try:
        if test_type == "equivalence":
            lhs = sp.sympify(item["left"])
            rhs = sp.sympify(item["right"])
            # CAS ingênuo simplifica a diferença; se der 0 OU se os primeiros 6 pontos de amostragem
            # avaliarem para zero, declara equivalente sem provar formalmente nem checar domínio
            diff = sp.simplify(lhs - rhs)
            is_equiv = bool(diff == 0)
            if not is_equiv and diff.free_symbols:
                sym_x = next(iter(diff.free_symbols))
                probe_6 = [-1, 2, sp.I, -sp.I, 1 + sp.I, -2]
                try:
                    if all(abs(complex(diff.subs(sym_x, pt).evalf())) < 1e-12 for pt in probe_6):
                        is_equiv = True
                except Exception:
                    pass
            return {"accepted": is_equiv, "detail": f"simplify(lhs - rhs) == {diff}"}
        elif test_type == "root_verification":
            eq = sp.Eq(sp.sympify(item["lhs"]), sp.sympify(item["rhs"]))
            sym = sp.Symbol(item["var"])
            cand = sp.sympify(item["candidate"])
            # CAS ingênuo substitui e avalia f(cand); se zero, aceita sem checar denominadores originais
            sub = sp.simplify(eq.lhs.subs(sym, cand) - eq.rhs.subs(sym, cand))
            return {"accepted": bool(sub == 0), "detail": f"sub = {sub}"}
        elif test_type == "limit":
            expr = sp.sympify(item["expression"])
            var = sp.Symbol(item["var"])
            pt = sp.sympify(item["point"])
            # CAS ingênuo usa limite unidirecional padrão sem auditar salto ou polos opostos
            lim = sp.limit(expr, var, pt)
            return {"accepted": bool(lim != sp.zoo and not lim.has(sp.Limit)), "value": str(lim)}
        elif test_type == "definite_integral":
            expr = sp.sympify(item["expression"])
            var = sp.Symbol(item["var"])
            low = sp.sympify(item["lower"])
            upp = sp.sympify(item["upper"])
            # CAS ingênuo aplica TFC F(b) - F(a) sem auditar polos internos
            res = sp.integrate(expr, (var, low, upp))
            is_finite = not res.has(sp.Integral, sp.zoo, sp.nan, sp.oo, -sp.oo)
            return {"accepted": is_finite, "value": str(res)}
        elif test_type == "formal_proof":
            # SIMULATED BASELINE (no Lean invocation).
            # Runner ingênuo sem auditoria de axiomas (#print axioms):
            # O compilador Lean aceita teoremas com 'sorry' emitindo apenas warning com exit code 0;
            # Um verificador sem auditoria rigorosa de axiomas aceita a declaração como provada.
            # NOTE: this row is a SIMULATION, not an observed external-executor
            # measurement. It is flagged as such in the emitted results.
            return {
                "accepted": True,
                "detail": "SIMULATED: lean accepted with exit code 0 (unaudited sorryAx)",
                "simulated": True,
            }
    except Exception as exc:
        return {"accepted": False, "error": str(exc)}
    return {"accepted": False, "detail": "unknown"}



def main() -> int:
    ax = Axiom()
    test_cases = [
        # Categoria 1: Branch Cuts e Semântica de Domínio Complexo vs Real
        {
            "id": "TC-01",
            "category": "Branch Cut / Complex Domain",
            "type": "equivalence",
            "left": "sqrt(x^2)",
            "right": "x",
            "assumptions": None,
            "mathematically_valid_unrestricted": False,
            "description": "sqrt(x^2) = x sem hipóteses (falso em x = -1)",
            "axiom_runner": lambda: ax.compare("sqrt(x^2)", "x"),
        },
        {
            "id": "TC-02",
            "category": "Branch Cut / Complex Domain",
            "type": "equivalence",
            "left": "sqrt(x^2)",
            "right": "x",
            "assumptions": {"x": "positive"},
            "mathematically_valid_unrestricted": True,
            "description": "sqrt(x^2) = x com hipótese x > 0 (verdadeiro)",
            "axiom_runner": lambda: ax.compare("sqrt(x^2)", "x", assumptions={"x": "positive"}),
        },
        {
            "id": "TC-03",
            "category": "Branch Cut / Complex Domain",
            "type": "equivalence",
            "left": "sqrt(x^2)",
            "right": "Abs(x)",
            "assumptions": None,
            "mathematically_valid_unrestricted": False,
            "description": "sqrt(x^2) = |x| sobre C sem hipóteses (falso em x = I)",
            "axiom_runner": lambda: ax.compare("sqrt(x^2)", "Abs(x)"),
        },
        {
            "id": "TC-04",
            "category": "Branch Cut / Complex Domain",
            "type": "equivalence",
            "left": "sqrt(x^2)",
            "right": "Abs(x)",
            "assumptions": {"x": "real"},
            "mathematically_valid_unrestricted": True,
            "description": "sqrt(x^2) = |x| com hipótese x real (verdadeiro)",
            "axiom_runner": lambda: ax.compare("sqrt(x^2)", "Abs(x)", assumptions={"x": "real"}),
        },
        # Categoria 2: Singularidades Removíveis e Preservação de Denominadores
        {
            "id": "TC-05",
            "category": "Domain Integrity / Rational",
            "type": "equivalence",
            "left": "(x - 1)/(x - 1)",
            "right": "1",
            "assumptions": None,
            "mathematically_valid_unrestricted": False,
            "description": "(x - 1)/(x - 1) = 1 irrestrito (falso em x = 1)",
            "axiom_runner": lambda: ax.compare("(x - 1)/(x - 1)", "1"),
        },
        {
            "id": "TC-06",
            "category": "Domain Integrity / Rational",
            "type": "equivalence",
            "left": "x/x",
            "right": "1",
            "assumptions": {"x": "nonzero"},
            "mathematically_valid_unrestricted": True,
            "description": "x/x = 1 com hipótese x != 0 (verdadeiro)",
            "axiom_runner": lambda: ax.compare("x/x", "1", assumptions={"x": "nonzero"}),
        },
        {
            "id": "TC-07",
            "category": "Domain Integrity / Rational",
            "type": "equivalence",
            "left": "(x^2 - 1)/(x - 1)",
            "right": "x + 1",
            "assumptions": None,
            "mathematically_valid_unrestricted": False,
            "description": "(x^2 - 1)/(x - 1) = x + 1 irrestrito (falso em x = 1)",
            "axiom_runner": lambda: ax.compare("(x^2 - 1)/(x - 1)", "x + 1"),
        },
        {
            "id": "TC-08",
            "category": "Root Verification / Extraneous Pole",
            "type": "root_verification",
            "lhs": "(x^2 - 1)/(x - 1)",
            "rhs": "0",
            "var": "x",
            "candidate": "1",
            "mathematically_valid_unrestricted": False,
            "description": "Verificação de raiz espúria x = 1 em (x^2 - 1)/(x - 1) = 0",
            "axiom_runner": lambda: ax.verify("(x^2 - 1)/(x - 1) = 0", candidate="1"),
        },
        {
            "id": "TC-09",
            "category": "Root Verification / Genuine Root",
            "type": "root_verification",
            "lhs": "(x^2 - 1)/(x - 1)",
            "rhs": "0",
            "var": "x",
            "candidate": "-1",
            "mathematically_valid_unrestricted": True,
            "description": "Verificação de raiz legítima x = -1 em (x^2 - 1)/(x - 1) = 0",
            "axiom_runner": lambda: ax.verify("(x^2 - 1)/(x - 1) = 0", candidate="-1"),
        },
        # Categoria 3: Limites Bilaterais e Polos
        {
            "id": "TC-10",
            "category": "Limits / Jump Discontinuity",
            "type": "limit",
            "expression": "Abs(x)/x",
            "var": "x",
            "point": "0",
            "direction": "+-",
            "mathematically_valid_unrestricted": False,
            "description": "lim_{x->0} |x|/x bilateral (não existe: -1 != +1)",
            "axiom_runner": lambda: ax.limit("Abs(x)/x", variable="x", point="0", direction="+-"),
        },
        {
            "id": "TC-11",
            "category": "Limits / Essential Pole",
            "type": "limit",
            "expression": "1/x",
            "var": "x",
            "point": "0",
            "direction": "+-",
            "mathematically_valid_unrestricted": False,
            "description": "lim_{x->0} 1/x bilateral (não existe: -oo != +oo)",
            "axiom_runner": lambda: ax.limit("1/x", variable="x", point="0", direction="+-"),
        },
        {
            "id": "TC-12",
            "category": "Limits / Even Pole",
            "type": "limit",
            "expression": "1/x^2",
            "var": "x",
            "point": "0",
            "direction": "+-",
            "mathematically_valid_unrestricted": True,
            "description": "lim_{x->0} 1/x^2 bilateral (diverge para +oo em ambos os lados)",
            "axiom_runner": lambda: ax.limit("1/x^2", variable="x", point="0", direction="+-"),
        },
        {
            "id": "TC-13",
            "category": "Limits / Riemann Pole",
            "type": "limit",
            "expression": "zeta(s)",
            "var": "s",
            "point": "1",
            "direction": "+-",
            "mathematically_valid_unrestricted": False,
            "description": "lim_{s->1} zeta(s) bilateral (não existe no eixo real: -oo != +oo)",
            "axiom_runner": lambda: ax.limit("zeta(s)", variable="s", point="1", direction="+-"),
        },
        {
            "id": "TC-14",
            "category": "Limits / Residue",
            "type": "limit",
            "expression": "(s - 1)*zeta(s)",
            "var": "s",
            "point": "1",
            "direction": "+-",
            "mathematically_valid_unrestricted": True,
            "description": "Resíduo lim_{s->1} (s-1)*zeta(s) = 1 (removível)",
            "axiom_runner": lambda: ax.limit("(s - 1)*zeta(s)", variable="s", point="1"),
        },
        # Categoria 4: Singularidades Internas em Integrais Definidas
        {
            "id": "TC-15",
            "category": "Integrals / Interior Pole",
            "type": "definite_integral",
            "expression": "1/x^2",
            "var": "x",
            "lower": "-1",
            "upper": "1",
            "mathematically_valid_unrestricted": False,
            "description": "integral_{-1}^{1} 1/x^2 dx (divergente por polo interno em 0; FTC ingênuo dá -2)",
            "axiom_runner": lambda: ax.integrate("1/x^2", variable="x", lower="-1", upper="1"),
        },
        {
            "id": "TC-16",
            "category": "Integrals / Interior Pole",
            "type": "definite_integral",
            "expression": "1/x",
            "var": "x",
            "lower": "-1",
            "upper": "1",
            "mathematically_valid_unrestricted": False,
            "description": "integral_{-1}^{1} 1/x dx (divergente por polo não integrável em 0)",
            "axiom_runner": lambda: ax.integrate("1/x", variable="x", lower="-1", upper="1"),
        },
        {
            "id": "TC-17",
            "category": "Integrals / Convergent Improper",
            "type": "definite_integral",
            "expression": "1/sqrt(x)",
            "var": "x",
            "lower": "0",
            "upper": "1",
            "mathematically_valid_unrestricted": True,
            "description": "integral_{0}^{1} 1/sqrt(x) dx = 2 (imprópria convergente)",
            "axiom_runner": lambda: ax.integrate("1/sqrt(x)", variable="x", lower="0", upper="1"),
        },
        {
            "id": "TC-18",
            "category": "Integrals / Mellin Riemann",
            "type": "definite_integral",
            "expression": "x/(exp(x) - 1)",
            "var": "x",
            "lower": "0",
            "upper": "oo",
            "mathematically_valid_unrestricted": True,
            "description": "integral_{0}^{oo} x/(exp(x) - 1) dx = pi^2/6 (integral de Bose-Einstein)",
            "axiom_runner": lambda: ax.integrate("x/(exp(x) - 1)", variable="x", lower="0", upper="oo"),
        },
        # Categoria 5: Aritmética e Provas Formais
        {
            "id": "TC-19",
            "category": "Arithmetic / Truth Audit",
            "type": "equivalence",
            "left": "zeta(2)",
            "right": "pi^2/8",
            "assumptions": None,
            "mathematically_valid_unrestricted": False,
            "description": "zeta(2) == pi^2/8 (afirmação falsa)",
            "axiom_runner": lambda: ax.compare("zeta(2)", "pi^2/8"),
        },
        {
            "id": "TC-20",
            "category": "Formal Proof / Axiom Audit",
            "type": "formal_proof",
            "statement": "theorem fake_zero : 1 = 0 := by sorry",
            "mathematically_valid_unrestricted": False,
            "description": "Afirmação matematicamente falsa (1 = 0) mascarada com sorry em Lean 4",
            "axiom_runner": lambda: ax.prove("theorem fake_zero : 1 = 0 := by sorry", engine="lean"),
        },
        {
            "id": "TC-21",
            "category": "Adversarial Equivalence / Roots Sampling",
            "type": "equivalence",
            "left": "(x + 1)*(x - 2)*(x - I)*(x + I)*(x - 1 - I)*(x + 2)",
            "right": "0",
            "assumptions": None,
            "mathematically_valid_unrestricted": False,
            "description": "Polinômio adversarial de grau 6 com raízes exatamente nos 6 primeiros pontos de teste (falso em x=0 e x=3)",
            "axiom_runner": lambda: ax.compare("(x + 1)*(x - 2)*(x - I)*(x + I)*(x - 1 - I)*(x + 2)", "0"),
        },
    ]


    results = []
    t0 = time.perf_counter()

    for tc in test_cases:
        expected_valid = tc["mathematically_valid_unrestricted"]
        # Execução AXIOM
        ax_res = tc["axiom_runner"]()
        ax_accepted = bool(
            ax_res.ok
            and ax_res.verified
            and ax_res.guarantee.is_mathematical_claim
            and ax_res.guarantee != Guarantee.UNVERIFIED
        )

        # Execução Naive CAS
        naive_res = run_naive_cas(tc["type"], tc)
        naive_accepted = bool(naive_res.get("accepted"))

        # Avaliação de Erro
        # Falso positivo: o sistema aceita/confirma algo matematicamente inválido
        ax_fp = bool(ax_accepted and not expected_valid)
        naive_fp = bool(naive_accepted and not expected_valid)

        # Falso negativo: o sistema rejeita algo matematicamente válido
        ax_fn = bool(not ax_accepted and expected_valid)
        naive_fn = bool(not naive_accepted and expected_valid)

        results.append({
            "id": tc["id"],
            "category": tc["category"],
            "description": tc["description"],
            "mathematically_valid": expected_valid,
            "axiom": {
                "accepted": ax_accepted,
                "guarantee": ax_res.guarantee.value,
                "verification_kind": ax_res.verification.kind if ax_res.verification else None,
                "verification_passed": ax_res.verification.passed if ax_res.verification else None,
                "is_false_positive": ax_fp,
                "is_false_negative": ax_fn,
            },
            "naive_cas": {
                "accepted": naive_accepted,
                "detail": naive_res.get("detail", naive_res.get("value", "")),
                "is_false_positive": naive_fp,
                "is_false_negative": naive_fn,
                "simulated": bool(naive_res.get("simulated", False)),
            },
        })

    elapsed = time.perf_counter() - t0
    n = len(results)
    invalid_cases = sum(1 for r in results if not r["mathematically_valid"])
    valid_cases = sum(1 for r in results if r["mathematically_valid"])

    ax_fp_count = sum(1 for r in results if r["axiom"]["is_false_positive"])
    naive_fp_count = sum(1 for r in results if r["naive_cas"]["is_false_positive"])

    ax_fn_count = sum(1 for r in results if r["axiom"]["is_false_negative"])
    naive_fn_count = sum(1 for r in results if r["naive_cas"]["is_false_negative"])

    ax_fail_closed_rate = sum(
        1 for r in results if not r["mathematically_valid"] and not r["axiom"]["accepted"]
    ) / invalid_cases

    naive_fail_closed_rate = sum(
        1 for r in results if not r["mathematically_valid"] and not r["naive_cas"]["accepted"]
    ) / invalid_cases

    summary = {
        "experiment_id": "EXP-0001",
        "title": "Verificação Quantitativa de Integridade de Domínio e Comportamento Fail-Closed",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 3),
        "total_test_cases": n,
        "valid_cases": valid_cases,
        "invalid_cases": invalid_cases,
        "baseline": BASELINE_PROVENANCE,
        "metrics": {
            "axiom": {
                "false_positives": ax_fp_count,
                "false_positive_rate": round(ax_fp_count / invalid_cases, 4),
                "false_negatives": ax_fn_count,
                "accuracy": round((n - ax_fp_count - ax_fn_count) / n, 4),
                "fail_closed_rate": round(ax_fail_closed_rate, 4),
            },
            "naive_cas": {
                "false_positives": naive_fp_count,
                "false_positive_rate": round(naive_fp_count / invalid_cases, 4),
                "false_negatives": naive_fn_count,
                "accuracy": round((n - naive_fp_count - naive_fn_count) / n, 4),
                "fail_closed_rate": round(naive_fail_closed_rate, 4),
            },
        },
        "results": results,
    }

    out_file = Path(__file__).with_name("results.json")
    out_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"EXP-0001 concluído em {elapsed:.2f}s!")
    print(f"Resultados gravados em {out_file}")
    print(f"AXIOM:     False Positives: {ax_fp_count}/{invalid_cases} (FPR: {summary['metrics']['axiom']['false_positive_rate']:.1%}) | Fail-Closed: {ax_fail_closed_rate:.1%}")
    print(f"Naive CAS: False Positives: {naive_fp_count}/{invalid_cases} (FPR: {summary['metrics']['naive_cas']['false_positive_rate']:.1%}) | Fail-Closed: {naive_fail_closed_rate:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
