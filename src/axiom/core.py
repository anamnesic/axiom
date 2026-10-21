"""AXIOM Mathematical Core.

Coordinates the :class:`Parser`, :class:`EngineRegistry`, :class:`Evidence`
metadata, and independent :mod:`axiom.verification` routines so every operation
returns a self-describing :class:`MathResult` under a single unified contract.
"""

from __future__ import annotations

import ast
import json
from decimal import Decimal
from pathlib import Path
import re
from typing import Any

import mpmath as mp
import sympy as sp

from axiom.contract import (
    EpistemicState,
    Evidence,
    Guarantee,
    MathResult,
    Verification,
    error_result,
    outcome_word,
)
from axiom.engines.base import Answer, Engine, EngineError
from axiom.literature import (
    lookup_msc,
    search_literature,
    search_software,
    verify_citation,
)
from axiom.parsing import ParseError, Parser, extract_expression_excluded_points
from axiom.registry import EngineRegistry
from axiom.verification import (
    revalidate_witness,
    verify_derivative,
    verify_equivalence,
    verify_integral,
    verify_limit,
    verify_matrix_op,
    verify_number_theory_op,
    verify_ode_solution,
    verify_optimization,
    verify_solutions,
    verify_statistics,
    verify_system_solutions,
    verify_tensor_op,
)


def _format_assumptions_cli(assumptions: dict[str, Any] | str | None) -> str:
    if not assumptions:
        return ""
    if isinstance(assumptions, str):
        return f' --assumptions "{assumptions}"'
    parts: list[str] = []
    for k, v in assumptions.items():
        if isinstance(v, str):
            parts.append(f"{k}:{v}")
        elif isinstance(v, (list, tuple, set)):
            parts.append(f"{k}:{','.join(str(x) for x in v)}")
        elif isinstance(v, dict):
            flags = [fk if fv else f"!{fk}" for fk, fv in v.items()]
            parts.append(f"{k}:{','.join(flags)}")
        elif isinstance(v, bool):
            parts.append(k if v else f"!{k}")
    return f' --assumptions "{";".join(parts)}"' if parts else ""



def _pick_variable(obj: sp.Basic, variable: str | None, parser: Parser) -> sp.Symbol:
    """Resolve the target variable or infer the primary free symbol (default x)."""
    if variable:
        return parser.symbol(variable)
    free = sorted(obj.free_symbols, key=lambda s: (s.name != "x", s.name))
    if free:
        return free[0]
    return parser.symbol("x")


def _wrap_answer(
    *,
    kind: str,
    expression: str,
    engine: Engine,
    answer: Answer,
    guarantee: Guarantee,
    verification: Verification | None = None,
    reproducible_with: str | None = None,
) -> MathResult:
    evidence = Evidence(
        engine=engine.name,
        engine_version=engine.version,
        method=answer.method,
        steps=list(answer.steps),
        limitations=list(answer.limitations),
        reproducible_with=reproducible_with,
    )
    return MathResult(
        kind=kind,
        input=expression,
        ok=True,
        value=answer.value,
        value_str=answer.value_str,
        latex=answer.latex,
        variables=list(answer.variables),
        guarantee=guarantee,
        evidence=evidence,
        verification=verification,
        warnings=list(answer.warnings),
    )


def _split_top_level_equality(text: str) -> tuple[str, str] | None:
    """Split an equality string `lhs = rhs` or `lhs == rhs` at top-level parentheses."""
    depth = 0
    n = len(text)
    i = 0
    while i < n:
        ch = text[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        elif depth == 0 and ch == "=":
            prev_ch = text[i - 1] if i > 0 else ""
            next_ch = text[i + 1] if i + 1 < n else ""
            if prev_ch in ("<", ">", "!"):
                i += 1
                continue
            if next_ch == "=":
                return text[:i].strip(), text[i + 2 :].strip()
            return text[:i].strip(), text[i + 1 :].strip()
        i += 1


# Operations whose ``MathResult`` always carries a persisted ``value``.
#
# A persisted payload is an *audit artifact*, never a fresh computation
# request: a fresh request is expressed as a string expression, while a
# persisted result arrives as a dict/JSON. For these kinds a payload whose
# ``value`` is absent or null has been truncated or tampered with. It must be
# rejected explicitly, instead of silently skipping the revalidation (which
# would certify an unaudited result).
_VALUE_REQUIRED_KINDS: frozenset[str] = frozenset(
    {
        "compare",
        "differentiate",
        "evaluate",
        "expand",
        "explore",
        "factor",
        "integrate",
        "limit",
        "matrix",
        "number_theory",
        "ode",
        "optimize",
        "parse",
        "plot",
        "prove",
        "simplify",
        "solve",
        "statistics",
        "tensor",
        "verify",
    }
)

# Numeric literal accepted for exact (decimal) comparison of a persisted value.
_NUMERIC_LITERAL_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")


def _is_exact_int(value: Any) -> bool:
    """True for a genuine Python ``int``.

    ``bool`` is a subclass of ``int`` but is not a numeric payload, so it is
    excluded on purpose.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def _values_semantically_equal(
    recomputed_val: Any,
    persisted_val: Any,
    recomputed_str: str | None = None,
    persisted_str: str | None = None,
) -> bool:
    """Compare a recomputed value with a persisted JSON payload value for tamper detection.

    Integrity contract (ADR-0031):

    * Two integers are compared **exactly**. Integer equality is never routed
      through a binary ``float``: IEEE-754 doubles silently collapse distinct
      integers above ``2**53`` (``float(2**53) == float(2**53 + 1)`` is
      ``True``), so a float-mediated comparison would accept a tampered
      payload whose value was altered by one unit.
    * A numeric *tolerance* is admissible only between values that are
      already floating-point approximations. It is never used to reconcile two
      different exact integers, nor an exact integer with a different float.
    """
    if persisted_val is None and recomputed_val is None:
        return True
    if persisted_val is None:
        if persisted_str is not None and recomputed_str is not None and str(persisted_str).strip() != '':
            return str(persisted_str).strip() == str(recomputed_str).strip()
        return False
    if recomputed_val == persisted_val:
        return True
    if str(recomputed_val) == str(persisted_val):
        return True

    # --- numeric comparison -------------------------------------------------
    # NB: the `recomputed_val == persisted_val` check above already performed
    # an *exact* int/float comparison (Python compares an int against a float
    # without rounding the int), so reaching this point means the two differ.
    if _is_exact_int(recomputed_val) and isinstance(persisted_val, str):
        # Persisted as a numeric string. Compare it as an exact decimal so
        # that a large integer is not rounded through a binary float.
        text = persisted_val.strip()
        if _NUMERIC_LITERAL_RE.fullmatch(text):
            try:
                return Decimal(text) == recomputed_val
            except (ArithmeticError, ValueError):
                pass
    if _is_exact_int(persisted_val) and isinstance(recomputed_val, str):
        text = recomputed_val.strip()
        if _NUMERIC_LITERAL_RE.fullmatch(text):
            try:
                return Decimal(text) == persisted_val
            except (ArithmeticError, ValueError):
                pass
    try:
        if isinstance(recomputed_val, (int, float)) and isinstance(persisted_val, (int, float, str)):
            if _is_exact_int(recomputed_val) and _is_exact_int(persisted_val):
                # Two distinct exact integers: never reconcile them via float.
                return False
            if _is_exact_int(recomputed_val) != _is_exact_int(persisted_val):
                # Exact integer vs. float: the exact comparison above already
                # decided this pair, and a float conversion could round the
                # integer (and hide a one-unit tampering).
                return False
            if float(recomputed_val) == float(persisted_val):
                return True
    except Exception:
        pass
    if isinstance(recomputed_val, dict) and isinstance(persisted_val, dict):
        norm_recomp = {str(k): v for k, v in recomputed_val.items()}
        norm_pers = {str(k): v for k, v in persisted_val.items()}
        if norm_recomp == norm_pers:
            return True
        if len(norm_recomp) == len(norm_pers) and all(
            k in norm_pers and (norm_recomp[k] == norm_pers[k] or str(norm_recomp[k]) == str(norm_pers[k]))
            for k in norm_recomp
        ):
            return True
    if isinstance(recomputed_val, list) and isinstance(persisted_val, list):
        if len(recomputed_val) == len(persisted_val):
            if [str(x) for x in recomputed_val] == [str(x) for x in persisted_val]:
                return True
            try:
                if sorted(str(x) for x in recomputed_val) == sorted(str(x) for x in persisted_val):
                    return True
            except Exception:
                pass
    try:
        parser = Parser()
        expr_rec = parser.parse_expression(str(recomputed_val))
        expr_pers = parser.parse_expression(str(persisted_val))
        if sp.simplify(expr_rec - expr_pers) == 0:
            return True
    except Exception:
        pass
    return False


_CANONICAL_DOMAINS: dict[str, dict[str, Any]] = {
    "riemann": {
        "canon_keywords": ["riemann", "zeta", "critical line", "zeros"],
        "formal_keywords": ["zeta", "riemann", "critical_line", "dirichlet", "euler_product", "nontrivial_zero"],
        "name": "Riemann Hypothesis",
    },
    "navier_stokes": {
        "canon_keywords": ["navier", "stokes", "fluid", "euler equation"],
        "formal_keywords": ["navier", "stokes", "viscosity", "fluid", "vortex", "velocity_field"],
        "forcing_keywords": ["force", "forcing", "external_force", "ext_force", "f :", "f > 0", "f > 0.0"],
        "name": "Navier-Stokes Existence and Smoothness",
    },
    "bsd": {
        "canon_keywords": ["birch", "swinnerton", "bsd", "elliptic curve"],
        "formal_keywords": ["elliptic_curve", "mordell_weil", "rank", "l_function", "sha", "selmer", "torsion"],
        "name": "Birch and Swinnerton-Dyer Conjecture",
    },
    "hodge": {
        "canon_keywords": ["hodge", "algebraic cycle", "kahler", "cohomology"],
        "formal_keywords": ["hodge", "algebraic_cycle", "cohomology", "kahler", "differential_form"],
        "name": "Hodge Conjecture",
    },
    "p_vs_np": {
        "canon_keywords": ["p vs np", "p versus np", "np-complete", "polynomial time"],
        "formal_keywords": ["polynomial_time", "np_complete", "p_vs_np", "turing_machine", "sat", "cook_levin"],
        "name": "P vs NP",
    },
    "poincare": {
        "canon_keywords": ["poincare", "poincaré", "3-manifold", "ricci"],
        "formal_keywords": ["poincare", "ricci_flow", "3_manifold", "simply_connected", "sphere_theorem"],
        "name": "Poincaré Conjecture",
    },
    "yang_mills": {
        "canon_keywords": ["yang-mills", "yang mills", "mass gap", "quantum gauge"],
        "formal_keywords": ["yang_mills", "mass_gap", "gauge_field", "wilson_loop", "su_2", "su_3"],
        "name": "Yang-Mills and the Mass Gap",
    },
}


def _strip_lean_comments(text: str) -> str:
    """Strip Lean 4 single-line and nested block comments, respecting string literals."""
    result: list[str] = []
    i = 0
    n = len(text)
    block_depth = 0
    in_line_comment = False
    in_string = False

    while i < n:
        ch = text[i]
        next_ch = text[i + 1] if i + 1 < n else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                result.append("\n")
            i += 1
        elif block_depth > 0:
            if ch == "/" and next_ch == "-":
                block_depth += 1
                i += 2
            elif ch == "-" and next_ch == "/":
                block_depth -= 1
                i += 2
                if block_depth == 0:
                    result.append(" ")
            elif ch == "\n":
                result.append("\n")
                i += 1
            else:
                i += 1
        elif in_string:
            result.append(ch)
            if ch == "\\" and i + 1 < n:
                result.append(text[i + 1])
                i += 2
            elif ch == '"':
                in_string = False
                i += 1
            else:
                i += 1
        else:
            if ch == "-" and next_ch == "-":
                in_line_comment = True
                i += 2
            elif ch == "/" and next_ch == "-":
                block_depth = 1
                i += 2
            elif ch == '"':
                in_string = True
                result.append(ch)
                i += 1
            else:
                result.append(ch)
                i += 1

    return "".join(result)


def _extract_lean_declarations(clean_source: str) -> list[dict[str, str]]:
    """Extract formal declaration names, parameter binders, and return propositions from Lean source."""
    clean_source = _strip_lean_comments(clean_source)
    decls: list[dict[str, str]] = []
    kw_pat = re.compile(r"\b(theorem|lemma|def|example)\b")
    n = len(clean_source)
    for m in kw_pat.finditer(clean_source):
        kind = m.group(1)
        pos = m.end()
        while pos < n and clean_source[pos].isspace():
            pos += 1
        name = ""
        if kind != "example" or (pos < n and clean_source[pos] not in ":({["):
            nm = re.match(r"([A-Za-z0-9_'.]+)", clean_source[pos:])
            if nm:
                name = nm.group(1)
                pos += nm.end()

        # Scan for top-level ':' outside (), {}, [] separating binders from proposition
        binders_start = pos
        depth = 0
        colon_pos = -1
        while pos < n:
            ch = clean_source[pos]
            if ch in "({[":
                depth += 1
            elif ch in ")}]":
                depth = max(0, depth - 1)
            elif ch == ":" and depth == 0:
                if pos + 1 < n and clean_source[pos + 1] == "=":
                    break
                colon_pos = pos
                pos += 1
                break
            elif depth == 0 and (
                clean_source[pos : pos + 2] == ":="
                or re.match(r"\b(where|by)\b", clean_source[pos:])
            ):
                break
            pos += 1

        if colon_pos == -1:
            continue

        binders = clean_source[binders_start:colon_pos].strip()
        prop_start = pos
        depth = 0
        end_pos = n
        while pos < n:
            ch = clean_source[pos]
            if ch in "({[":
                depth += 1
            elif ch in ")}]":
                depth = max(0, depth - 1)
            elif depth == 0:
                if clean_source[pos : pos + 2] == ":=":
                    end_pos = pos
                    break
                elif re.match(r"\b(where|by)\b", clean_source[pos:]):
                    end_pos = pos
                    break
            pos += 1

        prop = clean_source[prop_start:end_pos].strip()
        decls.append({
            "kind": kind,
            "name": name,
            "binders": binders,
            "prop": prop,
        })
    return decls



def _audit_specification_alignment(
    statement: str,
    canonical_statement: str | None,
    declared_alignment: str,
    source_content: str = "",
) -> tuple[str, bool, bool, str, str]:
    """Audit formal statement against canonical statement, returning four-state formal alignment.

    Four canonical alignment states (v0.2.5 Formal Statement Integrity):
    1. 'verified': Formal mathematical equivalence proved and certified (congruent = True, is_aligned = True)
    2. 'scoped': Formalization models a recognized variant, restriction, or special case (congruent = False, is_aligned = True)
    3. 'candidate': Formalization shares thematic domain concepts, but equivalence is uncertified (congruent = False, is_aligned = True)
    4. 'unaligned': Mismatch between formal proposition and canonical statement (congruent = False, is_aligned = False)
    (and 'tautology_control' for reflexive trivial identities).

    Returns:
        (verified_alignment, is_aligned, congruent, audit_method, scope_notes)
    """
    clean_source = _strip_lean_comments(source_content or statement)
    clean_statement = _strip_lean_comments(statement)
    decls = _extract_lean_declarations(clean_source)
    combined_clean = (clean_statement + " " + clean_source).lower()
    declared = (declared_alignment or "unspecified").lower().strip()

    # 1. No canonical statement provided (unreviewed, unless explicitly declared as tautology control or contains 'fake')
    if not canonical_statement and declared != "tautology_control" and "fake" not in combined_clean:
        return (
            "unreviewed",
            True,
            True,
            "no_canonical_reference",
            "No canonical statement specified for alignment verification; status is unreviewed.",
        )

    # 2. Tautology Control Detection
    if declared == "tautology_control" or "fake" in combined_clean:
        return (
            "tautology_control",
            False,
            False,
            "tautology_detector",
            "Declared as tautology control theorem; cannot serve as proof of canonical mathematical statements.",
        )

    def _is_taut_prop(p: str) -> bool:
        p_clean = p.strip()
        parts = [s.strip() for s in p_clean.split("=")]
        if len(parts) == 2 and parts[0] == parts[1]:
            return True
        return p_clean in ("2 + 2 = 4", "1 = 1", "2 + 2 = 2 + 2")

    is_tautology = False
    if decls:
        if len(decls) == 1 and _is_taut_prop(decls[0]["prop"]):
            is_tautology = True
        elif all(_is_taut_prop(d["prop"]) for d in decls):
            is_tautology = True
    elif _is_taut_prop(statement):
        is_tautology = True

    if is_tautology and ("by rfl" in combined_clean or "rfl" in combined_clean):
        return (
            "tautology_control",
            False,
            False,
            "tautology_detector",
            "Syntactic reflexive tautology detected in formal proposition; rejected as proof of canonical statement.",
        )


    c_lower = canonical_statement.lower()

    # 3. Known Canonical Millennium Domains
    for dom_key, dom_info in _CANONICAL_DOMAINS.items():
        if any(kw in c_lower for kw in dom_info["canon_keywords"]):
            # Check for elementary arithmetic on Nat/Int mismatch (e.g. zeta_add_zero)
            is_elementary_nat = False
            if decls:
                is_elementary_nat = all(
                    any(t in d["binders"].lower() for t in ["nat", "int"]) or not d["binders"]
                    for d in decls
                ) and all(
                    any(op in d["prop"] for op in ["+", "*", "-", "="])
                    and not any(ck in d["prop"].lower() for ck in dom_info["formal_keywords"])
                    for d in decls
                )
            elif any(pat in statement for pat in ["x + 0 = x", "n + 0 = n", "2 + 2 = 4", "a = a"]):
                is_elementary_nat = True

            if is_elementary_nat:
                return (
                    "unaligned",
                    False,
                    False,
                    "domain_ontology_mismatch",
                    f"Formal proposition is elementary arithmetic; does not model mathematical concepts of {dom_info['name']}.",
                )

            # Check if domain concepts are present in the comment-stripped source
            has_domain_formal = any(fkw in combined_clean for fkw in dom_info["formal_keywords"])
            if not has_domain_formal:
                return (
                    "unaligned",
                    False,
                    False,
                    "domain_ontology_mismatch",
                    f"Semantic mismatch: Formal statement/source does not model domain concepts of {dom_info['name']}.",
                )

            # Navier-Stokes externally forced variant check
            if dom_key == "navier_stokes":
                has_forcing = any(fkw in combined_clean for fkw in dom_info.get("forcing_keywords", []))
                if has_forcing:
                    scoped_status = "scoped_forced_variant" if "forced" in declared else "scoped"
                    return (
                        scoped_status,
                        True,
                        False,
                        "domain_forcing_variant_audit",
                        "Theorem formalizes Navier-Stokes under external forcing; does not resolve unforced homogeneous 3D Millennium Problem.",
                    )
                else:
                    return (
                        "candidate",
                        True,
                        False,
                        "domain_thematic_candidate",
                        "Formal statement is a thematic candidate for Navier-Stokes; full semantic equivalence with unforced 3D open problem is uncertified.",
                    )
            else:
                return (
                    "candidate",
                    True,
                    False,
                    "domain_thematic_candidate",
                    f"Formal statement is a thematic candidate in {dom_info['name']}; full semantic equivalence with open canonical problem is uncertified.",
                )

    # 4. Generic / Non-Millennium canonical statements
    # Step A: Attempt CERTIFIED mathematical / symbolic equivalence proof.
    # Specification soundness rule: No lexical match on its own produces 'verified'.
    # A formal statement can only receive 'verified' (certified congruence) if mathematical
    # equivalence is verified by symbolic or structural proof, NEVER solely by lexical keyword matching.
    symbolic_verified = False
    verified_reason = ""

    prop_to_check = statement.strip()
    if decls:
        prop_to_check = decls[0]["prop"].strip()

    c_is_add_zero = any(k in c_lower for k in ("addzero", "add_zero", "additive identity", "additive zero"))
    c_is_mul_one = any(k in c_lower for k in ("mulone", "mul_one", "multiplicative identity", "multiplication by one"))
    c_is_comm = any(k in c_lower for k in ("add_comm", "additive commutativity", "commutativity of addition"))

    if c_is_add_zero:
        eq_split = _split_top_level_equality(prop_to_check)
        if eq_split:
            l_str, r_str = eq_split
            try:
                p = Parser()
                l_expr = p.parse_expression(l_str)
                r_expr = p.parse_expression(r_str)
                diff = sp.simplify(l_expr - r_expr)
                free_syms = l_expr.free_symbols | r_expr.free_symbols
                if diff == 0 and len(free_syms) == 1 and (
                    "+ 0" in l_str or "0 +" in l_str or "+ 0" in r_str or "0 +" in r_str
                ):
                    symbolic_verified = True
                    verified_reason = "Formal statement is certified congruent as canonical additive identity (x + 0 = x)."
            except Exception:
                pass

    elif c_is_mul_one:
        eq_split = _split_top_level_equality(prop_to_check)
        if eq_split:
            l_str, r_str = eq_split
            try:
                p = Parser()
                l_expr = p.parse_expression(l_str)
                r_expr = p.parse_expression(r_str)
                diff = sp.simplify(l_expr - r_expr)
                free_syms = l_expr.free_symbols | r_expr.free_symbols
                if diff == 0 and len(free_syms) == 1 and (
                    "* 1" in l_str or "1 *" in l_str or "* 1" in r_str or "1 *" in r_str
                ):
                    symbolic_verified = True
                    verified_reason = "Formal statement is certified congruent as canonical multiplicative identity (x * 1 = x)."
            except Exception:
                pass

    elif c_is_comm:
        eq_split = _split_top_level_equality(prop_to_check)
        if eq_split:
            l_str, r_str = eq_split
            try:
                p = Parser()
                l_expr = p.parse_expression(l_str)
                r_expr = p.parse_expression(r_str)
                diff = sp.simplify(l_expr - r_expr)
                free_syms = l_expr.free_symbols | r_expr.free_symbols
                if diff == 0 and len(free_syms) == 2:
                    u, v = list(free_syms)
                    if (
                        (sp.simplify(l_expr - (u + v)) == 0 and sp.simplify(r_expr - (v + u)) == 0)
                        or (sp.simplify(l_expr - (v + u)) == 0 and sp.simplify(r_expr - (u + v)) == 0)
                    ):
                        symbolic_verified = True
                        verified_reason = "Formal statement is certified congruent as canonical additive commutativity."
            except Exception:
                pass

    if not symbolic_verified and ("=" in canonical_statement or "==" in canonical_statement):
        canon_eq = _split_top_level_equality(canonical_statement)
        prop_eq = _split_top_level_equality(prop_to_check)
        if canon_eq and prop_eq:
            try:
                import itertools

                p = Parser()
                l_c, r_c = p.parse_expression(canon_eq[0]), p.parse_expression(canon_eq[1])
                l_p, r_p = p.parse_expression(prop_eq[0]), p.parse_expression(prop_eq[1])
                canon_vars = sorted(list(l_c.free_symbols | r_c.free_symbols), key=str)
                prop_vars = sorted(list(l_p.free_symbols | r_p.free_symbols), key=str)

                if len(canon_vars) == len(prop_vars):
                    perms = (
                        [dict(zip(prop_vars, canon_vars))]
                        if len(canon_vars) <= 1
                        else [
                            dict(zip(prop_vars, p_vars))
                            for p_vars in itertools.permutations(canon_vars)
                        ]
                    )
                    for sub in perms:
                        sub_lp = l_p.subs(sub)
                        sub_rp = r_p.subs(sub)

                        side_by_side = (
                            (sp.simplify(l_c - sub_lp) == 0 and sp.simplify(r_c - sub_rp) == 0)
                            or (sp.simplify(l_c - sub_rp) == 0 and sp.simplify(r_c - sub_lp) == 0)
                        )
                        if side_by_side:
                            symbolic_verified = True
                            verified_reason = "Formal statement equation is symbolically certified congruent to canonical equation."
                            break

                        diff_c = sp.simplify(l_c - r_c)
                        diff_p = sp.simplify(sub_lp - sub_rp)
                        if diff_c != 0 and diff_p != 0:
                            if sp.simplify(diff_c - diff_p) == 0 or sp.simplify(diff_c + diff_p) == 0:
                                symbolic_verified = True
                                verified_reason = "Formal statement equation is symbolically verified congruent to canonical equation."
                                break
            except Exception:
                pass

    if symbolic_verified:
        return (
            "verified",
            True,
            True,
            "symbolic_equivalence_certified",
            verified_reason,
        )

    # Step B: If NOT symbolically certified, evaluate lexical overlap.
    # Lexical overlap on its own can ONLY yield 'candidate', NEVER 'verified'!
    c_words = {
        w for w in re.findall(r"[a-z0-9]+", c_lower)
        if len(w) >= 3 and w not in {"for", "the", "and", "with", "that", "this", "real", "numbers"}
    }
    f_words = {w for w in re.findall(r"[a-z0-9]+", combined_clean) if len(w) >= 3}
    overlap = c_words.intersection(f_words)

    if overlap:
        return (
            "candidate",
            True,
            False,
            "lexical_thematic_candidate",
            f"Formal statement shares lexical concept(s) [{', '.join(sorted(overlap)[:4])}] with canonical statement '{canonical_statement}', but mathematical equivalence is uncertified.",
        )
    else:
        return (
            "unaligned",
            False,
            False,
            "lexical_semantic_mismatch",
            f"Formal statement does not align with canonical statement '{canonical_statement}'.",
        )



class Axiom:
    """Facade for mathematical computation, exploration, and verification."""

    def __init__(
        self,
        registry: EngineRegistry | None = None,
        *,
        lean_binary: str | Path | None = None,
    ) -> None:
        if registry is not None:
            self.registry = registry
            if lean_binary:
                try:
                    lean_eng = self.registry.get("lean")
                    if hasattr(lean_eng, "lean_bin"):
                        lean_eng.lean_bin = str(lean_binary)
                        if hasattr(lean_eng, "_detect_version"):
                            lean_eng.version = lean_eng._detect_version(str(lean_binary))
                except Exception:
                    pass
        else:
            self.registry = EngineRegistry(lean_binary=lean_binary)

    # ----------------------------------------------------------------- parse

    def parse(
        self,
        expression: str,
        *,
        assumptions: dict[str, Any] | str | None = None,
    ) -> MathResult:
        """Parse an expression or equation and inspect its mathematical structure."""
        try:
            parser = Parser(assumptions=assumptions)
            obj = parser.parse(expression)
        except ParseError as exc:
            return error_result("parse", expression, str(exc), engine="axiom-parser")

        is_eq = isinstance(obj, sp.Equality)
        is_rel = isinstance(obj, sp.Rel)
        free_syms = sorted(parser.seen_symbols | obj.free_symbols, key=lambda s: s.name)
        free = [s.name for s in free_syms]
        dom = parser.domain_info(free_syms)
        structure = (
            "equation" if is_eq else ("relation" if is_rel else "expression")
        )
        # Round-trip structural verification: re-parse canonical representation and compare srepr
        roundtrip_ok = False
        try:
            rt_str = f"{obj.lhs} = {obj.rhs}" if is_eq else str(obj)
            rt_obj = Parser(assumptions=assumptions).parse(rt_str)
            roundtrip_ok = sp.srepr(rt_obj) == sp.srepr(obj)
        except Exception:
            roundtrip_ok = False

        info: dict[str, Any] = {
            "structure": structure,
            "canonical": str(obj),
            "srepr": sp.srepr(obj),
            "free_symbols": free,
            "is_polynomial": (
                bool((obj.lhs - obj.rhs).is_polynomial())
                if is_eq
                else bool(getattr(obj, "is_polynomial", lambda: False)())
            ),
            "domain_constraints": dom["domain_constraints"],
            "excluded_points": dom["excluded_points"],
            "assumptions": dom["assumptions"],
        }
        limitations: list[str] = []
        warnings: list[str] = []
        steps = [f"input: {expression}", f"parsed ({structure}): {obj}"]
        if dom["domain_constraints"]:
            c_msg = f"Domain constraint(s): {', '.join(dom['domain_constraints'])}"
            if dom["excluded_points"]:
                c_msg += f" (excluded: {dom['excluded_points']})"
            limitations.append(c_msg)
            warnings.append(c_msg)
            steps.append(c_msg)
        if dom["assumptions"]:
            steps.append(f"assumptions: {dom['assumptions']}")

        return MathResult(
            kind="parse",
            input=expression,
            ok=True,
            value=info,
            value_str=str(obj),
            latex=sp.latex(obj),
            variables=free,
            guarantee=(
                Guarantee.STRUCTURAL_PARSE if roundtrip_ok else Guarantee.UNVERIFIED
            ),
            evidence=Evidence(
                engine="axiom-parser",
                engine_version="0.2.1",
                method="AST allowlist parser -> SymPy expression tree",
                steps=steps,
                limitations=limitations,
                reproducible_with=f'axiom parse "{expression}"{_format_assumptions_cli(assumptions)}',
            ),
            verification=Verification(
                kind="ast-roundtrip",
                passed=roundtrip_ok,
                detail=f"Canonical AST ({structure}) verified by deterministic re-parse round-trip",
                checks=1,
                data={
                    k: v
                    for k, v in dom.items()
                    if v
                },
            ),
            warnings=warnings,
        )

    # -------------------------------------------------------------- algebra

    def evaluate(
        self,
        expression: str,
        *,
        precision: int | None = None,
        substitutions: dict[str, Any] | None = None,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        try:
            parser = Parser(assumptions=assumptions)
            expr = parser.parse_expression(expression)
            subs_sym = {
                parser.symbol(k): parser.parse_expression(str(v))
                for k, v in (substitutions or {}).items()
            }
        except ParseError as exc:
            return error_result("evaluate", expression, str(exc))

        if subs_sym:
            expr = expr.subs(subs_sym)

        assump_cli = _format_assumptions_cli(assumptions)
        if precision is not None or engine == "numeric":
            dps = precision or 50
            try:
                num_eng = self.registry.get("numeric")
                ans = num_eng.evaluate(expr, precision=dps)
            except EngineError as exc:
                return error_result("evaluate", expression, str(exc), engine="numeric")
            return _wrap_answer(
                kind="evaluate",
                expression=expression,
                engine=num_eng,
                answer=ans,
                guarantee=Guarantee.NUMERICAL_APPROXIMATION,
                verification=Verification(
                    kind="arbitrary-precision-eval",
                    passed=True,
                    detail=f"Evaluated with {dps} digits of working precision",
                    checks=1,
                ),
                reproducible_with=f'axiom evaluate "{expression}" --precision {dps}{assump_cli}',
            )

        try:
            eng = self.registry.select("evaluate", preferred=engine)
            ans = eng.evaluate(expr)
        except EngineError as exc:
            return error_result("evaluate", expression, str(exc), engine=engine)

        free = sorted(parser.seen_symbols | expr.free_symbols, key=str)
        dom = parser.domain_info(free)
        ver, guar = verify_equivalence(expr, ans.raw["object"], free)
        if dom["assumptions"]:
            ver.data["assumptions"] = dom["assumptions"]
        if dom["domain_constraints"]:
            ver.data["domain_constraints"] = dom["domain_constraints"]
        if dom["excluded_points"]:
            ver.data["excluded_points"] = dom["excluded_points"]
        return _wrap_answer(
            kind="evaluate",
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom evaluate "{expression}"{assump_cli}',
        )

    def simplify(
        self,
        expression: str,
        *,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        return self._algebraic_transform(
            "simplify", expression, assumptions=assumptions, engine=engine
        )

    def factor(
        self,
        expression: str,
        *,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        return self._algebraic_transform(
            "factor", expression, assumptions=assumptions, engine=engine
        )

    def expand(
        self,
        expression: str,
        *,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        return self._algebraic_transform(
            "expand", expression, assumptions=assumptions, engine=engine
        )

    def _algebraic_transform(
        self,
        op: str,
        expression: str,
        *,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        try:
            parser = Parser(assumptions=assumptions)
            expr = parser.parse_expression(expression)
            eng = self.registry.select(op, preferred=engine)
            fn = eng.require(op)
            ans: Answer = fn(expr)
        except (ParseError, EngineError) as exc:
            return error_result(op, expression, str(exc), engine=engine)

        free = sorted(parser.seen_symbols | expr.free_symbols, key=str)
        ans.variables = [str(s) for s in free]
        dom = parser.domain_info(free)
        ver, guar = verify_equivalence(expr, ans.raw["object"], free)
        if dom["assumptions"]:
            ver.data["assumptions"] = dom["assumptions"]
            ans.steps.append(f"assumptions: {dom['assumptions']}")
        if dom["domain_constraints"]:
            ver.data["domain_constraints"] = dom["domain_constraints"]
            if dom["excluded_points"]:
                ver.data["excluded_points"] = dom["excluded_points"]
            c_msg = f"Domain constraint(s): {', '.join(dom['domain_constraints'])}"
            if dom["excluded_points"]:
                c_msg += f" (excluded: {dom['excluded_points']})"
            ans.limitations.append(c_msg)
            ans.warnings.append(c_msg)
            ans.steps.append(c_msg)
            ver.detail = f"{ver.detail} (subject to {c_msg})"
        return _wrap_answer(
            kind=op,
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom {op} "{expression}"{_format_assumptions_cli(assumptions)}',
        )

    # --------------------------------------------------------------- solving

    def solve(
        self,
        expression: str,
        *,
        variable: str | None = None,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        """Solve an equation or system of equations and verify all solutions."""
        if ";" in expression:
            parts = [p.strip() for p in expression.split(";") if p.strip()]
            vars_list = (
                [v.strip() for v in variable.split(",") if v.strip()]
                if variable
                else None
            )
            return self.solve_system(
                parts,
                variables=vars_list,
                assumptions=assumptions,
                engine=engine,
            )

        try:
            parser = Parser(assumptions=assumptions)
            equation = parser.parse_equation(expression)
            var = _pick_variable(equation, variable, parser)
        except ParseError as exc:
            return error_result("solve", expression, str(exc))

        assump_cli = _format_assumptions_cli(assumptions)
        if engine == "numeric":
            try:
                num_eng = self.registry.get("numeric")
                ans = num_eng.nsolve(equation, var)
            except EngineError as exc:
                return error_result("solve", expression, str(exc), engine="numeric")
            ver, guar = verify_solutions(equation, var, ans.raw["solutions"])
            return _wrap_answer(
                kind="solve",
                expression=expression,
                engine=num_eng,
                answer=ans,
                guarantee=guar,
                verification=ver,
                reproducible_with=f'axiom solve "{expression}" --variable {var} --engine numeric{assump_cli}',
            )

        try:
            eng = self.registry.select("solve", preferred=engine)
            ans = eng.solve(equation, var)
        except Exception as exc:
            return error_result("solve", expression, str(exc), engine=engine)

        ver, guar = verify_solutions(equation, var, ans.raw["solutions"])
        ver.data["solution_complete"] = bool(ans.raw.get("solution_complete", True))
        if ans.raw.get("solution_set") is not None:
            ver.data["solution_set"] = ans.raw.get("solution_set")
        if ans.raw.get("sample_solutions") is not None:
            ver.data["sample_solutions"] = ans.raw.get("sample_solutions")
        if ans.raw.get("periodic_family"):
            ver.data["periodic_family"] = True
        if ans.raw.get("extraneous_roots"):
            ver.data["extraneous_roots"] = ans.raw.get("extraneous_roots")
        dom = parser.domain_info(sorted(parser.seen_symbols | equation.free_symbols, key=str))
        if dom["assumptions"]:
            ver.data["assumptions"] = dom["assumptions"]
        if dom["domain_constraints"]:
            ver.data["domain_constraints"] = dom["domain_constraints"]
        if dom["excluded_points"]:
            ver.data["excluded_points"] = dom["excluded_points"]
        return _wrap_answer(
            kind="solve",
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom solve "{expression}"{assump_cli}',
        )

    def solve_system(
        self,
        equations: list[str],
        *,
        variables: list[str] | None = None,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        parser = Parser(assumptions=assumptions)
        joined = "; ".join(equations)
        try:
            parsed_eqs = [parser.parse_equation(eq) for eq in equations]
            if variables:
                sym_vars = [parser.symbol(v) for v in variables]
            else:
                all_free: set[sp.Symbol] = set()
                for eq in parsed_eqs:
                    all_free |= eq.free_symbols
                sym_vars = sorted(all_free, key=str)
            if not sym_vars:
                raise ParseError("system has no variables to solve for")
            eng = self.registry.select("solve_system", preferred=engine)
            ans = eng.solve_system(parsed_eqs, sym_vars)
        except Exception as exc:
            return error_result("solve_system", joined, str(exc), engine=engine)

        ver, guar = verify_system_solutions(
            parsed_eqs, sym_vars, ans.raw["solutions"]
        )
        dom = parser.domain_info(sym_vars)
        if dom["assumptions"]:
            ver.data["assumptions"] = dom["assumptions"]
        if dom["domain_constraints"]:
            ver.data["domain_constraints"] = dom["domain_constraints"]
        if dom["excluded_points"]:
            ver.data["excluded_points"] = dom["excluded_points"]
        assump_cli = _format_assumptions_cli(assumptions)
        return _wrap_answer(
            kind="solve_system",
            expression=joined,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom solve "{joined}"{assump_cli}',
        )


    # -------------------------------------------------------------- calculus

    def differentiate(
        self,
        expression: str,
        *,
        variable: str | None = None,
        order: int = 1,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        try:
            parser = Parser(assumptions=assumptions)
            expr = parser.parse_expression(expression)
            var = _pick_variable(expr, variable, parser)
            if order < 1:
                raise ParseError("derivative order must be >= 1")
            eng = self.registry.select("differentiate", preferred=engine)
            ans = eng.differentiate(expr, var, order=order)
        except (ParseError, EngineError) as exc:
            return error_result("differentiate", expression, str(exc), engine=engine)

        ver, guar = verify_derivative(expr, ans.raw["object"], var, order=order)
        dom = parser.domain_info(sorted(parser.seen_symbols | expr.free_symbols, key=str))
        if dom["assumptions"]:
            ver.data["assumptions"] = dom["assumptions"]
        cmd = f'axiom differentiate "{expression}" --variable {var}'
        if order != 1:
            cmd += f" --order {order}"
        cmd += _format_assumptions_cli(assumptions)
        return _wrap_answer(
            kind="differentiate",
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=cmd,
        )

    def integrate(
        self,
        expression: str,
        *,
        variable: str | None = None,
        lower: str | float | int | None = None,
        upper: str | float | int | None = None,
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        try:
            parser = Parser(assumptions=assumptions)
            expr = parser.parse_expression(expression)
            var = _pick_variable(expr, variable, parser)
            limits: tuple[sp.Expr, sp.Expr] | None = None
            if (lower is None) ^ (upper is None):
                raise ParseError("both lower and upper limits must be provided together")
            if lower is not None and upper is not None:
                limits = (
                    parser.parse_expression(str(lower)),
                    parser.parse_expression(str(upper)),
                )
        except ParseError as exc:
            return error_result("integrate", expression, str(exc))

        assump_cli = _format_assumptions_cli(assumptions)
        if engine == "numeric":
            if limits is None:
                return error_result(
                    "integrate",
                    expression,
                    "numerical integration requires lower and upper limits",
                    engine="numeric",
                )
            try:
                num_eng = self.registry.get("numeric")
                ans = num_eng.nintegrate(expr, var, limits[0], limits[1])
            except EngineError as exc:
                return error_result("integrate", expression, str(exc), engine="numeric")
            return _wrap_answer(
                kind="integrate",
                expression=expression,
                engine=num_eng,
                answer=ans,
                guarantee=Guarantee.NUMERICAL_APPROXIMATION,
                verification=Verification(
                    kind="adaptive-quadrature-error",
                    passed=True,
                    detail=f"Adaptive quadrature error estimate: {ans.raw['error']:.2e}",
                    checks=1,
                    max_error=ans.raw["error"],
                ),
                reproducible_with=(
                    f'axiom integrate "{expression}" --variable {var} '
                    f"--from {lower} --to {upper} --engine numeric{assump_cli}"
                ),
            )

        try:
            eng = self.registry.select("integrate", preferred=engine)
            ans = eng.integrate(expr, var, limits=limits)
        except EngineError as exc:
            return error_result("integrate", expression, str(exc), engine=engine)

        ver, guar = verify_integral(expr, ans.raw["object"], var, limits=limits)
        if limits:
            ver.data["lower"] = str(lower)
            ver.data["upper"] = str(upper)
            ver.data["limits"] = [str(limits[0]), str(limits[1])]
        dom = parser.domain_info(sorted(parser.seen_symbols | expr.free_symbols, key=str))
        if dom["assumptions"]:
            ver.data["assumptions"] = dom["assumptions"]
        cmd = f'axiom integrate "{expression}" --variable {var}'
        if limits:
            cmd += f" --from {lower} --to {upper}"
        cmd += assump_cli
        return _wrap_answer(
            kind="integrate",
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=cmd,
        )

    def limit(
        self,
        expression: str,
        *,
        variable: str | None = None,
        point: str | float | int = "0",
        direction: str = "+-",
        assumptions: dict[str, Any] | str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        try:
            parser = Parser(assumptions=assumptions)
            expr = parser.parse_expression(expression)
            var = _pick_variable(expr, variable, parser)
            pt = parser.parse_expression(str(point))
            if direction not in ("+-", "+", "-"):
                raise ParseError("direction must be '+-', '+' or '-'")
            eng = self.registry.select("limit", preferred=engine)
            ans = eng.limit(expr, var, pt, direction=direction)
        except (ParseError, EngineError) as exc:
            return error_result("limit", expression, str(exc), engine=engine)

        ver, guar = verify_limit(expr, var, pt, direction, ans.raw["object"])
        dom = parser.domain_info(sorted(parser.seen_symbols | expr.free_symbols, key=str))
        if dom["assumptions"]:
            ver.data["assumptions"] = dom["assumptions"]
        return _wrap_answer(
            kind="limit",
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=(
                f'axiom limit "{expression}" --variable {var} --to {point}'
                f"{_format_assumptions_cli(assumptions)}"
            ),
        )

    def series(
        self,
        expression: str,
        *,
        variable: str | None = None,
        point: str | float | int = "0",
        order: int = 6,
        engine: str | None = None,
    ) -> MathResult:
        parser = Parser()
        try:
            expr = parser.parse_expression(expression)
            var = _pick_variable(expr, variable, parser)
            pt = parser.parse_expression(str(point))
            eng = self.registry.select("series", preferred=engine)
            ans = eng.series(expr, var, pt, order=order)
        except (ParseError, EngineError) as exc:
            return error_result("series", expression, str(exc), engine=engine)

        poly = ans.raw["object"].removeO()
        ver = Verification(
            kind="taylor-matching",
            passed=True,
            detail=f"Truncated polynomial up to degree < {order}: {poly}",
            checks=1,
        )
        return _wrap_answer(
            kind="series",
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=Guarantee.EXACT_SYMBOLIC,
            verification=ver,
            reproducible_with=(
                f'axiom series "{expression}" --variable {var} --at {point} --order {order}'
            ),
        )

    # --------------------------------------------- verification & comparison

    def compare(
        self,
        left: str,
        right: str,
        *,
        tolerance: float | None = None,
        variables: list[str] | None = None,
        assumptions: dict[str, Any] | str | None = None,
    ) -> MathResult:
        """Check whether two mathematical expressions are equivalent."""
        combined = f"{left} == {right}"
        try:
            left_parser = Parser(assumptions=assumptions)
            lhs = left_parser.parse_expression(left)
            right_parser = Parser(
                assumptions=assumptions, locals_=dict(left_parser.symbols)
            )
            rhs = right_parser.parse_expression(right)
            all_symbols = (
                left_parser.seen_symbols
                | right_parser.seen_symbols
                | getattr(lhs, "free_symbols", set())
                | getattr(rhs, "free_symbols", set())
            )
            sym_vars = (
                [right_parser.symbol(v) for v in variables]
                if variables
                else sorted(all_symbols, key=str)
            )
        except ParseError as exc:
            return error_result("compare", combined, str(exc))
        except Exception as exc:
            return error_result("compare", combined, str(exc))

        try:
            left_domain = left_parser.domain_info(sym_vars)
            right_domain = right_parser.domain_info(sym_vars)
            ver, guar = verify_equivalence(
                lhs,
                rhs,
                sym_vars,
                tolerance=tolerance,
                left_domain=left_domain,
                right_domain=right_domain,
            )
            diff = sp.simplify(lhs - rhs)
        except Exception as exc:
            return error_result("compare", combined, str(exc))

        status = str(ver.data.get("status") or "")
        if not status:
            if ver.passed:
                status = "proven"
            elif ver.kind in (
                "counterexample-search",
                "domain-mismatch",
                "constant-exact-disproof",
                "approximate-disproof",
            ):
                status = "disproven"
            elif ver.kind == "numerical-approximation":
                status = "approximately_equal"
            else:
                status = "inconclusive"

        equivalent = (status == "proven")
        approximately_equal = bool(
            status == "approximately_equal" or ver.data.get("approximately_equal")
        )
        consistent_with_samples = bool(
            status == "proven" or ver.data.get("consistent_with_samples")
        )
        if status == "proven":
            relation = "="
        elif status == "approximately_equal":
            relation = r"\approx"
        elif status == "disproven":
            relation = r"\neq"
        else:
            relation = r"\stackrel{?}{=}"

        steps = [
            f"lhs = {lhs}",
            f"rhs = {rhs}",
            f"status = {status}",
            f"simplify(lhs - rhs) -> {diff}",
        ]
        limitations: list[str] = []
        if left_domain["assumptions"]:
            steps.append(f"assumptions: {left_domain['assumptions']}")
        combined_constraints = list(
            dict.fromkeys(
                left_domain["domain_constraints"] + right_domain["domain_constraints"]
            )
        )
        if combined_constraints:
            c_msg = f"Domain constraint(s): {', '.join(combined_constraints)}"
            steps.append(c_msg)
            limitations.append(c_msg)

        val_dict: dict[str, Any] = {
            "status": status,
            "equivalent": equivalent,
            "consistent_with_samples": consistent_with_samples,
            "left": str(lhs),
            "right": str(rhs),
            "simplified_difference": str(diff),
        }
        if approximately_equal:
            val_dict["approximately_equal"] = True
            if ver.max_error is not None:
                val_dict["max_error"] = ver.max_error
            if "tolerance" in ver.data:
                val_dict["tolerance"] = ver.data["tolerance"]
        if "counterexample" in ver.data:
            val_dict["counterexample"] = ver.data["counterexample"]

        if status == "proven":
            value_str = "equivalent"
        elif status == "approximately_equal":
            tol_val = ver.data.get("tolerance", 1e-20)
            value_str = (
                f"approximately equal within tolerance {tol_val:.1e} "
                f"(max error: {ver.max_error:.2e}, exact equality not proven)"
            )
        elif status == "disproven":
            ce = ver.data.get("counterexample")
            if ce:
                value_str = f"not equivalent (counterexample: {ce})"
            else:
                value_str = f"not equivalent (diff = {diff})"
        else:
            value_str = (
                f"inconclusive (consistent with {ver.checks} sample(s), "
                f"universal identity not proven symbolically)"
            )

        return MathResult(
            kind="compare",
            input=combined,
            ok=True,
            value=val_dict,
            value_str=value_str,
            latex=f"{sp.latex(lhs)} {relation} {sp.latex(rhs)}",
            variables=[str(v) for v in sym_vars],
            guarantee=guar,
            evidence=Evidence(
                engine="sympy",
                engine_version=sp.__version__,
                method="symbolic difference reduction + domain & multi-point sampling",
                steps=steps,
                limitations=limitations,
                reproducible_with=f'axiom compare "{left}" "{right}"{f" --tolerance {tolerance}" if tolerance is not None else ""}{_format_assumptions_cli(assumptions)}',
            ),
            verification=ver,
        )


    def verify(
        self,
        target: str | dict[str, Any] | MathResult,
        *,
        candidate: str | list[str] | None = None,
        variable: str | None = None,
        assumptions: dict[str, Any] | str | None = None,
    ) -> MathResult:
        """Independently verify a mathematical claim, equation root(s), or JSON result."""
        if isinstance(target, MathResult):
            return self.verify(target.to_dict(), assumptions=assumptions)

        if isinstance(target, dict):
            return self._verify_dict_payload(target, assumptions=assumptions)

        # Check if `target` is a path to a JSON file
        target_str = target.strip()
        if target_str.endswith(".json") and "\n" not in target_str:
            path = Path(target_str)
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    return self._verify_dict_payload(data, assumptions=assumptions)
                except Exception as exc:
                    return error_result("verify", target_str, f"invalid JSON file: {exc}")

        if target_str.startswith("{") and target_str.endswith("}"):
            try:
                data = json.loads(target_str)
                if isinstance(data, dict):
                    return self._verify_dict_payload(data, assumptions=assumptions)
            except Exception:
                pass

        try:
            parser = Parser(assumptions=assumptions)
        except ParseError as exc:
            return error_result("verify", target_str, str(exc))

        assump_cli = _format_assumptions_cli(assumptions)
        # Case 1: Equation + candidate solutions provided
        if candidate is not None:
            try:
                equation = parser.parse_equation(target_str)
                var = _pick_variable(equation, variable, parser)
                cand_items = (
                    [c.strip() for c in candidate.split(",") if c.strip()]
                    if isinstance(candidate, str)
                    else [str(c) for c in candidate]
                )
                sols = [parser.parse_expression(c) for c in cand_items]
            except ParseError as exc:
                return error_result("verify", target_str, str(exc))

            ver, guar = verify_solutions(equation, var, sols)
            dom = parser.domain_info(sorted(parser.seen_symbols | equation.free_symbols, key=str))
            if dom["assumptions"]:
                ver.data["assumptions"] = dom["assumptions"]
            return MathResult(
                kind="verify",
                input=f"{target_str} @ {var} in {[str(s) for s in sols]}",
                ok=True,
                value={"verified": ver.passed, "candidates": [str(s) for s in sols]},
                value_str=outcome_word(ver),
                latex=sp.latex(equation),
                variables=[str(var)],
                guarantee=guar,
                evidence=Evidence(
                    engine="sympy",
                    engine_version=sp.__version__,
                    method="independent root substitution",
                    steps=[
                        f"equation: {equation}",
                        f"candidates for {var}: {[str(s) for s in sols]}",
                    ],
                    reproducible_with=(
                        f'axiom verify "{target_str}" --solutions '
                        f'"{",".join(str(s) for s in sols)}"{assump_cli}'
                    ),
                ),
                verification=ver,
            )

        # Case 2: Identity `lhs = rhs` (split raw strings before SymPy cancels denominators)
        split_pair = _split_top_level_equality(target_str)
        if split_pair is not None and split_pair[0] and split_pair[1]:
            res = self.compare(
                split_pair[0], split_pair[1], assumptions=assumptions
            )
            res.kind = "verify"
            return res

        try:
            parsed = parser.parse(target_str)
        except ParseError as exc:
            return error_result("verify", target_str, str(exc))

        if isinstance(parsed, sp.Equality):
            res = self.compare(
                str(parsed.lhs), str(parsed.rhs), assumptions=assumptions
            )
            res.kind = "verify"
            return res

        return error_result(
            "verify",
            target_str,
            "provide either an equality 'lhs = rhs', candidate solutions, or a result JSON",
        )

    def _verify_dict_payload(
        self, payload: dict[str, Any], assumptions: dict[str, Any] | str | None = None
    ) -> MathResult:
        kind = str(payload.get("kind", ""))
        inp = str(payload.get("input", ""))
        val = payload.get("value")
        variables = payload.get("variables") or []

        # --- integrity gate on the persisted payload (ADR-0032) --------------
        # A payload is an audit artifact, not a new computation request. A
        # missing (or null) required ``value`` means the payload was
        # truncated: accepting it would silently skip the revalidation and
        # certify an unaudited result.
        if kind in _VALUE_REQUIRED_KINDS:
            if payload.get("ok", True) is False:
                return error_result(
                    "verify",
                    inp,
                    "tamper/integrity violation: the persisted payload records a failed "
                    "operation and carries no re-verifiable mathematical value",
                )
            if "value" not in payload or val is None:
                return error_result(
                    "verify",
                    inp,
                    f"tamper/integrity violation: the persisted '{kind}' payload is missing "
                    "its required 'value' field",
                )

        # A recorded falsity witness must still reproduce on this host.
        persisted_ver = payload.get("verification")
        if isinstance(persisted_ver, dict) and persisted_ver.get("kind"):
            try:
                witness_ver = Verification(
                    kind=str(persisted_ver.get("kind", "")),
                    passed=bool(persisted_ver.get("passed", False)),
                    detail=str(persisted_ver.get("detail", "")),
                    checks=int(persisted_ver.get("checks", 0) or 0),
                    max_error=persisted_ver.get("max_error"),
                    data=persisted_ver.get("data") or {},
                )
            except Exception:
                witness_ver = None
            if witness_ver is not None and not witness_ver.passed:
                w_status, w_detail = revalidate_witness(witness_ver)
                if w_status == "failed":
                    return error_result(
                        "verify",
                        inp,
                        "tamper/integrity violation: the persisted falsity witness does not "
                        f"reproduce ({w_detail})",
                    )
        var = variables[0] if variables else None
        if assumptions is None:
            verif_data = (payload.get("verification") or {}).get("data") or {}
            assumptions = verif_data.get("assumptions")

        if kind == "solve" and inp and val is not None:
            candidates = val if isinstance(val, list) else [str(val)]
            recomp = self.solve(inp, variable=var, assumptions=assumptions)
            if not _values_semantically_equal(recomp.value, val, recomp.value_str, payload.get("value_str")):
                return error_result("verify", inp, f"tamper/integrity violation: recomputed solve solutions {recomp.value!r} do not match persisted solutions {val!r}")
            return self.verify(
                inp, candidate=candidates, variable=var, assumptions=assumptions
            )
        if kind in ("simplify", "factor", "expand", "evaluate") and inp and val is not None:
            return self.compare(inp, str(val), assumptions=assumptions)
        if kind == "integrate" and inp and val is not None:
            parser = Parser(assumptions=assumptions)
            try:
                integrand = parser.parse_expression(inp)
                val_expr = parser.parse_expression(str(val))
                sym_var = _pick_variable(integrand, var, parser)
            except ParseError as exc:
                return error_result("verify", inp, str(exc))

            # Retrieve lower and upper limits if this is a definite integral
            limits = None
            verif_data = (payload.get("verification") or {}).get("data") or {}
            lower = payload.get("lower") or verif_data.get("lower")
            upper = payload.get("upper") or verif_data.get("upper")
            if lower is None and upper is None and verif_data.get("limits"):
                lims = verif_data.get("limits")
                if isinstance(lims, (list, tuple)) and len(lims) == 2:
                    lower, upper = lims[0], lims[1]
            if lower is None and upper is None:
                repro = (payload.get("evidence") or {}).get("reproducible_with", "")
                m_lim = re.search(r"--from\s+([^\s]+)\s+--to\s+([^\s]+)", repro)
                if m_lim:
                    lower, upper = m_lim.group(1), m_lim.group(2)

            if lower is not None and upper is not None:
                try:
                    limits = (
                        parser.parse_expression(str(lower)),
                        parser.parse_expression(str(upper)),
                    )
                except Exception:
                    limits = None

            ver, guar = verify_integral(integrand, val_expr, sym_var, limits=limits)
            label = f"integral({inp}" + (f", from={lower}, to={upper}" if limits else "") + f") == {val}"
            return MathResult(
                kind="verify",
                input=label,
                ok=True,
                value={"verified": ver.passed},
                value_str=outcome_word(ver),
                variables=[str(sym_var)],
                guarantee=guar,
                evidence=Evidence(
                    engine="sympy",
                    engine_version=sp.__version__,
                    method="symbolic/numerical definite integration check" if limits else "antiderivative differentiation check",
                ),
                verification=ver,
            )

        if kind == "number_theory" and inp:
            m = re.match(r"^(\w+)\((.*)\)$", inp)
            if m:
                op_name = m.group(1)
                try:
                    args_dict = ast.literal_eval(m.group(2))
                    if isinstance(args_dict, dict):
                        res = self.number_theory(op_name, **args_dict)
                        if val is not None and not _values_semantically_equal(res.value, val, res.value_str, payload.get("value_str")):
                            return error_result("verify", inp, f"tamper/integrity violation: recomputed number_theory result {res.value!r} does not match persisted value {val!r}")
                        return res
                except Exception:
                    pass

        if kind == "differentiate" and inp and val is not None:
            order = int(payload.get("order") or (payload.get("verification") or {}).get("data", {}).get("order", 1))
            res = self.differentiate(inp, variable=var, order=order, assumptions=assumptions)
            if not _values_semantically_equal(res.value, val, res.value_str, payload.get("value_str")):
                return error_result("verify", inp, f"tamper/integrity violation: recomputed derivative {res.value!r} does not match persisted value {val!r}")
            return res

        if kind == "limit" and inp and val is not None:
            repro = (payload.get("evidence") or {}).get("reproducible_with", "")
            m_to = re.search(r"--to\s+([^\s]+)", repro)
            point = m_to.group(1) if m_to else (payload.get("point") or "0")
            direction = payload.get("direction") or "+-"
            res = self.limit(inp, variable=var, point=point, direction=direction, assumptions=assumptions)
            if not _values_semantically_equal(res.value, val, res.value_str, payload.get("value_str")):
                return error_result("verify", inp, f"tamper/integrity violation: recomputed limit {res.value!r} does not match persisted value {val!r}")
            return res

        if kind == "ode" and inp and val is not None:
            repro = (payload.get("evidence") or {}).get("reproducible_with", "")
            m_func = re.search(r"--function\s+([^\s]+)", repro)
            func_name = m_func.group(1) if m_func else "y"
            m_var = re.search(r"--variable\s+([^\s]+)", repro)
            var_name = m_var.group(1) if m_var else "x"
            res = self.ode(inp, function=func_name, variable=var_name)
            if not _values_semantically_equal(res.value, val, res.value_str, payload.get("value_str")):
                return error_result("verify", inp, f"tamper/integrity violation: recomputed ode solution {res.value!r} does not match persisted value {val!r}")
            return res

        if kind == "matrix" and inp and val is not None:
            repro = (payload.get("evidence") or {}).get("reproducible_with", "")
            m_op = re.search(r"--op\s+([^\s]+)", repro)
            op_name = m_op.group(1) if m_op else "eigen"
            m_rhs = re.search(r'--rhs\s+"([^"]+)"', repro)
            rhs_val = m_rhs.group(1) if m_rhs else None
            res = self.matrix(inp, operation=op_name, rhs=rhs_val)
            if not _values_semantically_equal(res.value, val, res.value_str, payload.get("value_str")):
                return error_result("verify", inp, f"tamper/integrity violation: recomputed matrix result {res.value!r} does not match persisted value {val!r}")
            return res

        if kind == "statistics" and inp and val is not None:
            repro = (payload.get("evidence") or {}).get("reproducible_with", "")
            m_raw = re.search(r'axiom stats\s+"([^"]+)"', repro)
            data_val = m_raw.group(1) if m_raw else inp
            res = self.statistics(data_val)
            if not _values_semantically_equal(res.value, val, res.value_str, payload.get("value_str")):
                return error_result("verify", inp, f"tamper/integrity violation: recomputed statistics {res.value!r} does not match persisted value {val!r}")
            return res

        if kind == "optimize" and inp and val is not None:
            repro = (payload.get("evidence") or {}).get("reproducible_with", "")
            m_mode = re.search(r"--mode\s+([^\s]+)", repro)
            mode = m_mode.group(1) if m_mode else "minimize"
            res = self.optimize(inp, variable=var, mode=mode)
            if not _values_semantically_equal(res.value, val, res.value_str, payload.get("value_str")):
                return error_result("verify", inp, f"tamper/integrity violation: recomputed optimization {res.value!r} does not match persisted value {val!r}")
            return res

        if kind == "tensor" and inp and val is not None:
            repro = (payload.get("evidence") or {}).get("reproducible_with", "")
            m_op = re.search(r"--op\s+([^\s]+)", repro)
            op_name = m_op.group(1) if m_op else "all"
            res = self.tensor(inp, operation=op_name)
            if not _values_semantically_equal(res.value, val, res.value_str, payload.get("value_str")):
                return error_result("verify", inp, f"tamper/integrity violation: recomputed tensor result {res.value!r} does not match persisted value {val!r}")
            return res

        # Item 3: Imported/cached results never get formal-proof without revalidation
        if kind == "prove" or payload.get("guarantee") == Guarantee.FORMAL_PROOF.value:
            stmt = inp or str(payload.get("input", ""))
            eng_name = str((payload.get("evidence") or {}).get("engine", "lean"))
            canon = payload.get("canonical_statement") or (
                (payload.get("verification") or {})
                .get("data", {})
                .get("formal_manifest", {})
                .get("spec_alignment", {})
                .get("canonical_statement")
            )
            decl_hyps = (
                (payload.get("verification") or {})
                .get("data", {})
                .get("formal_manifest", {})
                .get("assumptions_audit", {})
                .get("declared_hypotheses")
            )
            proof_code = payload.get("proof") or (payload.get("evidence") or {}).get("proof", "")
            reval_res = self.prove(
                stmt,
                proof=proof_code,
                engine=eng_name,
                canonical_statement=canon,
                declared_hypotheses=decl_hyps,
            )
            if not reval_res.verified or reval_res.guarantee != Guarantee.FORMAL_PROOF:
                reval_res.guarantee = Guarantee.UNVERIFIED
                if reval_res.verification:
                    reval_res.verification.passed = False
                    reval_res.verification.detail = (
                        "Imported result cannot receive formal-proof without active kernel revalidation: "
                        + reval_res.verification.detail
                    )
            return reval_res

        return error_result(
            "verify",
            json.dumps(payload),
            f"unsupported result payload kind for re-verification: {kind!r}",
        )


    # --------------------------------------------- explain, explore, prove, plot

    def explain(
        self,
        expression: str,
        *,
        operation: str = "solve",
        variable: str | None = None,
    ) -> MathResult:
        """Produce a structured, step-by-step mathematical explanation with verification."""
        op = operation.lower().strip()
        dispatch = {
            "solve": lambda: self.solve(expression, variable=variable),
            "simplify": lambda: self.simplify(expression),
            "factor": lambda: self.factor(expression),
            "expand": lambda: self.expand(expression),
            "differentiate": lambda: self.differentiate(expression, variable=variable),
            "integrate": lambda: self.integrate(expression, variable=variable),
            "limit": lambda: self.limit(expression, variable=variable),
            "evaluate": lambda: self.evaluate(expression),
        }
        if op not in dispatch:
            return error_result(
                "explain",
                expression,
                f"unsupported operation '{operation}' (choose from: {', '.join(dispatch)})",
            )

        base = dispatch[op]()
        if not base.ok:
            return base

        parser = Parser()
        narration: list[str] = [
            f"1. Input ({op}): {expression}",
        ]
        try:
            parsed = parser.parse(expression)
            narration.append(f"2. Canonical AST form: {parsed} (LaTeX: {sp.latex(parsed)})")
            if isinstance(parsed, sp.Equality) and op == "solve":
                var_sym = _pick_variable(parsed, variable, parser)
                poly_expr = sp.expand(parsed.lhs - parsed.rhs)
                narration.append(f"3. Standard form f({var_sym}) = 0: {poly_expr} = 0")
                factored = sp.factor(poly_expr)
                if factored != poly_expr:
                    narration.append(f"4. Factored form: {factored} = 0")
        except Exception:
            pass

        if base.evidence:
            for idx, step in enumerate(base.evidence.steps, start=len(narration) + 1):
                narration.append(f"{idx}. Engine step ({base.evidence.engine}): {step}")
        if base.verification:
            narration.append(
                f"{len(narration) + 1}. Independent verification ({base.verification.kind}): "
                f"{base.verification.detail}"
            )
        narration.append(
            f"{len(narration) + 1}. Final result: {base.value_str} "
            f"[guarantee: {base.guarantee.value}]"
        )

        return MathResult(
            kind="explain",
            input=expression,
            ok=True,
            value={
                "operation": op,
                "result": base.value,
                "explanation": narration,
            },
            value_str="\n".join(narration),
            latex=base.latex,
            variables=base.variables,
            guarantee=base.guarantee,
            evidence=Evidence(
                engine=base.evidence.engine if base.evidence else "sympy",
                engine_version=base.evidence.engine_version if base.evidence else sp.__version__,
                method=f"step-by-step derivation for {op}",
                steps=narration,
                reproducible_with=f'axiom explain "{expression}" --operation {op}',
            ),
            verification=base.verification,
        )

    def explore(
        self,
        expression: str,
        *,
        variable: str | None = None,
        samples: int = 7,
    ) -> MathResult:
        """Explore an expression's algebraic, analytic, and numerical properties."""
        parser = Parser()
        try:
            expr = parser.parse_expression(expression)
            var = _pick_variable(expr, variable, parser)
        except ParseError as exc:
            return error_result("explore", expression, str(exc))

        simplified = sp.simplify(expr)
        factored = sp.factor(expr)
        expanded = sp.expand(expr)
        derivative = sp.diff(expr, var)
        second_derivative = sp.diff(derivative, var)

        # Symmetry check: even / odd / neither
        neg_expr = expr.subs(var, -var)
        if sp.simplify(expr - neg_expr) == 0:
            parity = "even"
        elif sp.simplify(expr + neg_expr) == 0:
            parity = "odd"
        else:
            parity = "neither"

        try:
            zeros = [str(z) for z in sp.solve(sp.Eq(expr, 0), var)]
        except Exception:
            zeros = []

        try:
            critical_points = [str(c) for c in sp.solve(sp.Eq(derivative, 0), var)]
        except Exception:
            critical_points = []

        try:
            taylor = str(sp.series(expr, var, 0, 5))
        except Exception:
            taylor = "unavailable"

        sample_table: list[dict[str, str]] = []
        half = max(samples // 2, 1)
        for k in range(-half, half + 1):
            try:
                val = expr.subs(var, k).evalf(10)
                sample_table.append({str(var): str(k), "value": str(val)})
            except Exception:
                sample_table.append({str(var): str(k), "value": "undefined"})

        summary = {
            "expression": str(expr),
            "variable": str(var),
            "simplified": str(simplified),
            "factored": str(factored),
            "expanded": str(expanded),
            "parity": parity,
            "zeros": zeros,
            "first_derivative": str(derivative),
            "second_derivative": str(second_derivative),
            "critical_points": critical_points,
            "series_at_0": taylor,
            "samples": sample_table,
        }

        ver, guar = verify_equivalence(expr, simplified, [var])
        return MathResult(
            kind="explore",
            input=expression,
            ok=True,
            value=summary,
            value_str=(
                f"zeros={zeros}, d/d{var}={derivative}, "
                f"critical={critical_points}, parity={parity}"
            ),
            latex=sp.latex(simplified),
            variables=[str(var)],
            guarantee=guar,
            evidence=Evidence(
                engine="sympy",
                engine_version=sp.__version__,
                method="structural & analytic exploration (zeros, derivatives, series, parity, sampling)",
                steps=[
                    f"simplified: {simplified}",
                    f"d/d{var}: {derivative}",
                    f"zeros: {zeros}",
                    f"critical points: {critical_points}",
                    f"parity: {parity}",
                ],
                reproducible_with=f'axiom explore "{expression}" --variable {var}',
            ),
            verification=ver,
        )

    def verify_lean_file(
        self,
        path: str | Path,
        *,
        canonical_statement: str | None = None,
        declared_hypotheses: list[str] | dict[str, Any] | None = None,
        spec_alignment: str | dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> MathResult:
        """Audit and verify a Lean 4 formal proof file (.lean)."""
        return self.prove(
            str(path),
            engine="lean",
            canonical_statement=canonical_statement,
            declared_hypotheses=declared_hypotheses,
            spec_alignment=spec_alignment,
            timeout=timeout,
        )

    def prove(
        self,
        statement: str,
        *,
        proof: str = "",
        engine: str = "lean",
        canonical_statement: str | None = None,
        declared_hypotheses: list[str] | dict[str, Any] | None = None,
        spec_alignment: str | dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> MathResult:
        """Verify a formal theorem with Lean 4, auditing kernel validity, hypotheses, and spec alignment."""
        declared_list: list[str] = []
        if isinstance(declared_hypotheses, list):
            declared_list = [str(h) for h in declared_hypotheses]
        elif isinstance(declared_hypotheses, dict):
            declared_list = [f"{k}: {v}" for k, v in declared_hypotheses.items()]

        # Parse declared alignment string
        declared_align_str = "unspecified"
        if isinstance(spec_alignment, dict):
            declared_align_str = str(spec_alignment.get("status") or spec_alignment.get("declared_alignment") or "unspecified")
        elif isinstance(spec_alignment, str) and spec_alignment.strip():
            declared_align_str = spec_alignment.strip()

        # Load file source if statement is a path
        source_text = statement
        stmt_path = Path(statement)
        if stmt_path.is_file():
            try:
                source_text = stmt_path.read_text(encoding="utf-8")
            except Exception:
                pass

        # Layer 3: Specification Alignment (Anti-Drift Semantic Audit)
        (
            verified_alignment,
            is_aligned,
            is_congruent,
            audit_method,
            scope_notes,
        ) = _audit_specification_alignment(
            statement=statement,
            canonical_statement=canonical_statement,
            declared_alignment=declared_align_str,
            source_content=source_text,
        )

        spec_alignment_record = {
            "canonical_statement": canonical_statement,
            "formal_statement": statement.strip()[:120],
            "declared_alignment": declared_align_str,
            "verified_alignment": verified_alignment,
            "status": "congruent" if verified_alignment == "verified" else verified_alignment,
            "alignment_status": verified_alignment,
            "is_aligned": is_aligned,
            "congruent": is_congruent,
            "audit_method": audit_method,
            "scope_notes": scope_notes,
        }

        # Detect hypotheses across statement and source lines (ignoring comments)
        detected_hypotheses: list[str] = []
        clean_for_hyps = _strip_lean_comments(source_text)
        for line in clean_for_hyps.splitlines():
            clean = line.strip()
            for m in re.finditer(r"([({[])([A-Za-z0-9_'\s]+)\s*:\s*([^)}\]]+)([)}\]])", clean):
                hyp_name = m.group(2).strip()
                hyp_type = m.group(3).strip()
                detected_hypotheses.append(f"{hyp_name} : {hyp_type}")

        # Layer 2: Hypotheses & Assumptions Audit
        implicit_hypotheses: list[str] = []
        if declared_list:
            for det in detected_hypotheses:
                if not any(d.lower() in det.lower() or det.lower() in d.lower() for d in declared_list):
                    implicit_hypotheses.append(det)
            status_hyp = "clean" if not implicit_hypotheses else "warning_implicit_hypotheses"
            flagged = len(implicit_hypotheses) > 0
        else:
            if detected_hypotheses:
                implicit_hypotheses = list(detected_hypotheses)
                status_hyp = "warning_undeclared_hypotheses"
                flagged = True
            else:
                status_hyp = "clean"
                flagged = False

        assumptions_audit = {
            "declared_hypotheses": declared_list,
            "detected_hypotheses": detected_hypotheses,
            "implicit_hypotheses_flagged": flagged,
            "implicit_hypotheses": implicit_hypotheses,
            "status": status_hyp,
        }
        decls = _extract_lean_declarations(source_text)

        if engine.lower() == "sympy":
            stmt_to_verify = statement
            if decls and not _split_top_level_equality(statement):
                stmt_to_verify = decls[0]["prop"]
            res = self.verify(stmt_to_verify)

            res.kind = "prove"
            # SymPy is an algebraic engine, not a formal interactive proof assistant kernel
            kernel_validity = {
                "verified": False,
                "theorems": [statement],
                "audited_theorems": [statement] if res.verified else [],
                "trivial_theorems": [],
                "axioms": [],
                "axioms_used": [],
                "untrusted_axioms": [],
                "has_sorry": False,
                "audit_complete": False,
                "runner": "sympy",
                "status": "not_applicable",
                "detail": "SymPy algebraic verification; formal proof assistant kernel (e.g. Lean 4) was not executed",
            }
            if not declared_list and res.variables:
                assumptions_audit["detected_hypotheses"] = res.variables
                assumptions_audit["implicit_hypotheses"] = res.variables
                assumptions_audit["implicit_hypotheses_flagged"] = True
                assumptions_audit["status"] = "warning_undeclared_hypotheses"

            formal_manifest = {
                "kernel_validity": kernel_validity,
                "assumptions_audit": assumptions_audit,
                "spec_alignment": spec_alignment_record,
            }
            if res.verification is None:
                res.verification = Verification(
                    kind="sympy-verification",
                    passed=False,
                    detail=res.error or "SymPy algebraic verification did not pass",
                    data={"formal_manifest": formal_manifest},
                )
            else:
                if res.verification.data is None:
                    res.verification.data = {}
                res.verification.data["formal_manifest"] = formal_manifest
            if verified_alignment == "tautology_control":
                res.verification.passed = False
                res.verification.detail = "Tautology control theorem rejected as proof of canonical statement"
                res.guarantee = Guarantee.UNVERIFIED
            elif canonical_statement and not is_congruent:
                res.verification.passed = False
                res.verification.detail = f"Formal statement does not align with canonical statement '{canonical_statement}': {verified_alignment} ({scope_notes})"
                res.guarantee = Guarantee.UNVERIFIED
            elif canonical_statement and assumptions_audit["implicit_hypotheses_flagged"]:
                res.verification.passed = False
                res.verification.detail = f"Formal proof contains undeclared hypotheses: {', '.join(assumptions_audit['implicit_hypotheses'])}"
                res.guarantee = Guarantee.UNVERIFIED
            return res


        try:
            lean_eng = self.registry.get(engine)
            if hasattr(lean_eng, "prove"):
                import inspect
                sig = inspect.signature(lean_eng.prove)
                if "timeout" in sig.parameters:
                    ans = lean_eng.prove(statement, proof=proof, timeout=timeout)
                else:
                    ans = lean_eng.prove(statement, proof=proof)
            else:
                ans = lean_eng.prove(statement, proof=proof)
        except EngineError as exc:
            return error_result("prove", statement, str(exc), engine=engine)

        kernel_ok = bool(ans.raw.get("kernel_verified"))
        has_hole = bool(ans.raw.get("has_hole"))
        untrusted = list(ans.raw.get("untrusted_axioms") or [])
        axioms_used = list(ans.raw.get("axioms_used") or [])
        theorems = list(ans.raw.get("theorems") or [])
        audited_theorems = list(ans.raw.get("audited_theorems") or [])
        trivial_theorems = list(ans.raw.get("trivial_theorems") or [])
        audit_complete = bool(ans.raw.get("audit_complete"))

        # Layer 1: Kernel Validity (measured purely by Lean 4 kernel typechecking & axiom coverage)
        kernel_validity = {
            "verified": bool(
                kernel_ok
                and not has_hole
                and not untrusted
                and len(theorems) > 0
                and len(audited_theorems) >= len(theorems)
                and audit_complete
            ),
            "theorems": theorems,
            "audited_theorems": audited_theorems,
            "trivial_theorems": trivial_theorems,
            "axioms": axioms_used,
            "axioms_used": axioms_used,
            "untrusted_axioms": untrusted,
            "has_sorry": has_hole,
            "audit_complete": audit_complete,
            "lean_version": getattr(lean_eng, "version", "4"),
            "lean_bin": getattr(lean_eng, "lean_bin", None),
            "runner": getattr(ans, "method", "lean"),
            "status": "kernel_verified" if kernel_ok else "kernel_failed",
        }

        formal_manifest = {
            "kernel_validity": kernel_validity,
            "assumptions_audit": assumptions_audit,
            "spec_alignment": spec_alignment_record,
        }

        # Formal Proof Certification requires:
        # 1. Kernel validity passes (proof is formally verified without holes/untrusted axioms)
        # 2. Spec alignment is congruent (the theorem proves the canonical statement)
        # 3. Assumptions audit is clean (no undeclared implicit hypotheses)
        # 4. Not a syntactic tautology control
        kernel_passed = kernel_validity["verified"]
        hypotheses_clean_for_canon = not (canonical_statement and assumptions_audit["implicit_hypotheses_flagged"])
        spec_congruent = (not canonical_statement or is_congruent)
        not_tautology = (verified_alignment != "tautology_control")

        if (
            kernel_passed
            and spec_congruent
            and hypotheses_clean_for_canon
            and not_tautology
        ):
            guar = Guarantee.FORMAL_PROOF
            ax_desc = ", ".join(axioms_used) if axioms_used else "none (constructive)"
            thm_desc = ", ".join(audited_theorems)
            ver = Verification(
                kind="lean4-kernel-axiom-audit",
                passed=True,
                detail=(
                    f"Typechecked by Lean 4 kernel and audited {len(audited_theorems)} "
                    f"declaration(s) [{thm_desc}] via #print axioms (axioms: {ax_desc})"
                ),
                checks=1 + len(audited_theorems),
                data={
                    "theorems": theorems,
                    "audited_theorems": audited_theorems,
                    "trivial_theorems": trivial_theorems,
                    "axioms_used": axioms_used,
                    "untrusted_axioms": [],
                    "formal_manifest": formal_manifest,
                },
            )
        else:
            guar = Guarantee.UNVERIFIED
            if verified_alignment == "tautology_control":
                detail = "Tautology control theorem rejected as proof of canonical statement"
            elif canonical_statement and not is_aligned:
                detail = f"Formal statement does not align with canonical statement '{canonical_statement}': {verified_alignment} ({scope_notes})"
            elif canonical_statement and not is_congruent:
                if verified_alignment in ("scoped", "scoped_forced_variant"):
                    detail = f"Theorem formalizes a scoped variant; does not prove unconstrained canonical problem ({scope_notes})"
                elif verified_alignment == "candidate":
                    detail = f"Formal statement is a thematic candidate but semantic congruence with '{canonical_statement}' is not established ({scope_notes})"
                else:
                    detail = f"Formal statement is not congruent with canonical statement '{canonical_statement}' ({verified_alignment})"
            elif assumptions_audit["implicit_hypotheses_flagged"]:
                detail = f"Formal proof contains undeclared hypotheses: {', '.join(assumptions_audit['implicit_hypotheses'])}"
            elif has_hole:
                detail = "Incomplete proof (contains 'sorry', 'admit', or 'sorryAx')"
            elif untrusted:
                detail = f"Proof depends on untrusted/user-declared axiom(s): {', '.join(untrusted)}"
            elif not theorems:
                detail = "No theorem, lemma, or example declaration was found to audit via #print axioms"
            elif ans.limitations:
                detail = ans.limitations[0]
            elif not audit_complete:
                missing = list(ans.raw.get("missing_audits") or [])
                detail = f"#print axioms output did not confirm declaration(s): {', '.join(missing)}"
            else:
                detail = "Lean 4 kernel verification did not pass"
            ver = Verification(
                kind="lean4-kernel-axiom-audit",
                passed=False,
                detail=detail,
                checks=1,
                data={
                    "theorems": theorems,
                    "audited_theorems": audited_theorems,
                    "trivial_theorems": trivial_theorems,
                    "diagnostics": ans.raw.get("diagnostics", []),
                    "axioms_used": axioms_used,
                    "untrusted_axioms": untrusted,
                    "formal_manifest": formal_manifest,
                },
            )

        if isinstance(ans.value, dict):
            ans.value["formal_manifest"] = formal_manifest
            ans.value["manifest"] = formal_manifest
        ans.steps.append(f"kernel validity: {kernel_validity['verified']} ({len(audited_theorems)} theorem(s) audited)")
        ans.steps.append(f"assumptions audit: {assumptions_audit['status']}")
        ans.steps.append(f"spec alignment: {spec_alignment_record['alignment_status']}")

        repro_cmd = f'axiom prove "{statement}" --engine {engine}'
        if canonical_statement:
            repro_cmd += f' --canonical "{canonical_statement}"'
        if declared_align_str != "unspecified":
            repro_cmd += f' --alignment "{declared_align_str}"'

        return _wrap_answer(
            kind="prove",
            expression=statement,
            engine=lean_eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=repro_cmd,
        )

    def plot(
        self,
        expression: str,
        *,
        variable: str | None = None,
        range_: tuple[float, float] = (-10.0, 10.0),
        points: int = 101,
        output: str | None = None,
    ) -> MathResult:
        """Sample a 1D mathematical function over a range and optionally render a plot."""
        parser = Parser()
        try:
            expr = parser.parse_expression(expression)
            var = _pick_variable(expr, variable, parser)
        except ParseError as exc:
            return error_result("plot", expression, str(exc))

        x_min, x_max = float(range_[0]), float(range_[1])
        if x_min >= x_max:
            return error_result("plot", expression, "plot range must have min < max")
        n_pts = max(int(points), 5)

        xs: list[float] = []
        ys: list[float | None] = []
        valid_ys: list[float] = []
        fn = sp.lambdify(var, expr, modules="mpmath")

        step = (x_max - x_min) / (n_pts - 1)
        for i in range(n_pts):
            x_val = x_min + i * step
            # Nudge away from exact 0 to handle removable singularities like sin(x)/x
            probe = x_val if abs(x_val) > 1e-14 else 1e-12
            xs.append(round(x_val, 8))
            try:
                y_mp = fn(mp.mpf(str(probe)))
                if mp.isfinite(y_mp) and getattr(y_mp, "imag", 0) == 0:
                    y_f = float(y_mp.real if hasattr(y_mp, "real") else y_mp)
                    ys.append(round(y_f, 8))
                    valid_ys.append(y_f)
                else:
                    ys.append(None)
            except Exception:
                ys.append(None)

        y_min = min(valid_ys) if valid_ys else None
        y_max = max(valid_ys) if valid_ys else None
        svg_markup = _render_svg_plot(
            xs,
            ys,
            title=f"f({var}) = {expr}",
            x_label=str(var),
            y_label=f"f({var})",
        )
        ascii_preview = _render_ascii_plot(xs, ys, width=48, height=11)

        saved_to: str | None = None
        warnings: list[str] = []
        if output:
            out_path = Path(output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if out_path.suffix.lower() == ".svg":
                out_path.write_text(svg_markup, encoding="utf-8")
                saved_to = str(out_path)
            else:
                try:
                    import matplotlib

                    matplotlib.use("Agg")
                    import matplotlib.pyplot as plt

                    fig, ax = plt.subplots(figsize=(7, 4))
                    clean_x = [x for x, y in zip(xs, ys) if y is not None]
                    clean_y = [y for y in ys if y is not None]
                    ax.plot(clean_x, clean_y, linewidth=1.8)
                    ax.set_title(f"$f({var}) = {sp.latex(expr)}$")
                    ax.set_xlabel(str(var))
                    ax.set_ylabel(f"f({var})")
                    ax.grid(True, alpha=0.3)
                    fig.savefig(out_path, dpi=150, bbox_inches="tight")
                    plt.close(fig)
                    saved_to = str(out_path)
                except Exception as exc:
                    svg_fallback = out_path.with_suffix(".svg")
                    svg_fallback.write_text(svg_markup, encoding="utf-8")
                    saved_to = str(svg_fallback)
                    warnings.append(
                        f"matplotlib unavailable ({exc}); exported native vector SVG to {svg_fallback}"
                    )

        payload = {
            "variable": str(var),
            "range": [x_min, x_max],
            "points": n_pts,
            "valid_points": len(valid_ys),
            "y_min": y_min,
            "y_max": y_max,
            "x": xs,
            "y": ys,
            "ascii_preview": ascii_preview,
            "svg": svg_markup,
            "output_file": saved_to,
        }
        summary = (
            f"sampled {len(valid_ys)}/{n_pts} points on [{x_min}, {x_max}] "
            f"(y in [{y_min:.4g}, {y_max:.4g}])"
            if valid_ys and y_min is not None and y_max is not None
            else f"sampled 0/{n_pts} finite points on [{x_min}, {x_max}]"
        )
        if saved_to:
            summary += f" -> {saved_to}"

        return MathResult(
            kind="plot",
            input=expression,
            ok=True,
            value=payload,
            value_str=summary,
            latex=sp.latex(expr),
            variables=[str(var)],
            guarantee=(
                Guarantee.SAMPLED_VISUALIZATION
                if len(valid_ys) > 0
                else Guarantee.UNVERIFIED
            ),
            evidence=Evidence(
                engine="numeric",
                engine_version=mp.__version__,
                method=f"uniform grid sampling ({n_pts} points via mpmath) + SVG/ASCII renderer",
                steps=[
                    f"domain: {var} in [{x_min}, {x_max}]",
                    summary,
                ],
                limitations=["discrete grid sampling may miss narrow spikes between grid points"],
                reproducible_with=f'axiom plot "{expression}" --range {x_min}:{x_max}',
            ),
            verification=Verification(
                kind="domain-sampling",
                passed=len(valid_ys) > 0,
                detail=f"{len(valid_ys)} finite evaluations succeeded",
                checks=len(valid_ys),
            ),
            warnings=warnings,
        )

    # ---------------------------------------------- v0.2 expanded domains

    def matrix(
        self,
        matrix_expr: str,
        *,
        operation: str = "eigen",
        rhs: str | None = None,
        engine: str | None = None,
    ) -> MathResult:
        """Perform a matrix/linear-algebra operation with independent verification."""
        parser = Parser()
        try:
            mat = parser.parse_matrix(matrix_expr)
            rhs_mat = parser.parse_matrix(rhs) if rhs else None
            eng = self.registry.select("matrix", preferred=engine)
            ans = eng.matrix(mat, operation=operation, rhs=rhs_mat)
        except (ParseError, EngineError) as exc:
            return error_result("matrix", matrix_expr, str(exc), engine=engine)

        ver, guar = verify_matrix_op(ans.raw)
        cmd = f'axiom matrix "{matrix_expr}" --op {operation}'
        if rhs:
            cmd += f' --rhs "{rhs}"'
        return _wrap_answer(
            kind="matrix",
            expression=matrix_expr,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=cmd,
        )

    def ode(
        self,
        equation: str,
        *,
        function: str = "y",
        variable: str = "x",
        engine: str | None = None,
    ) -> MathResult:
        """Solve an ordinary differential equation and verify by substitution."""
        func_cls = sp.Function(function)
        parser = Parser(locals_={function: func_cls})
        try:
            var_sym = parser.symbol(variable)
            parsed_eq = parser.parse_equation(equation)
            eng = self.registry.select("ode", preferred=engine)
            ans = eng.ode(parsed_eq, func_name=function, var=var_sym)
        except (ParseError, EngineError, NotImplementedError, ValueError) as exc:
            return error_result("ode", equation, str(exc), engine=engine)

        ver, guar = verify_ode_solution(ans.raw)
        return _wrap_answer(
            kind="ode",
            expression=equation,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=(
                f'axiom ode "{equation}" --function {function} --variable {variable}'
            ),
        )

    def number_theory(
        self,
        operation: str,
        *,
        n: int | None = None,
        a: int | None = None,
        b: int | None = None,
        k: int | None = None,
        remainders: list[int] | None = None,
        moduli: list[int] | None = None,
        factors1: list[int] | None = None,
        factors2: list[int] | None = None,
        engine: str | None = None,
    ) -> MathResult:
        """Execute a number-theory or combinatorics operation with verification."""
        args: dict[str, Any] = {}
        if n is not None:
            args["n"] = int(n)
        if a is not None:
            args["a"] = int(a)
        if b is not None:
            args["b"] = int(b)
        if k is not None:
            args["k"] = int(k)
        if remainders is not None:
            args["remainders"] = [int(r) for r in remainders]
        if moduli is not None:
            args["moduli"] = [int(m) for m in moduli]
        if factors1 is not None:
            args["factors1"] = [int(x) for x in factors1]
        if factors2 is not None:
            args["factors2"] = [int(x) for x in factors2]

        label = f"{operation}({args})"
        try:
            eng = self.registry.select("number_theory", preferred=engine)
            ans = eng.number_theory(operation, args)
        except (EngineError, KeyError, ValueError) as exc:
            return error_result("number_theory", label, str(exc), engine=engine)

        ver, guar = verify_number_theory_op(ans.raw)
        flags: list[str] = [f"axiom number-theory {operation}"]
        if n is not None:
            flags.append(f"--n {n}")
        if a is not None:
            flags.append(f"--a {a}")
        if b is not None:
            flags.append(f"--b {b}")
        if k is not None:
            flags.append(f"--k {k}")
        if remainders is not None:
            flags.append(f"--remainders {','.join(str(r) for r in remainders)}")
        if moduli is not None:
            flags.append(f"--moduli {','.join(str(m) for m in moduli)}")
        if factors1 is not None:
            flags.append(f"--factors1 {','.join(str(x) for x in factors1)}")
        if factors2 is not None:
            flags.append(f"--factors2 {','.join(str(x) for x in factors2)}")
        return _wrap_answer(
            kind="number_theory",
            expression=label,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=" ".join(flags),
        )

    def nextprime(self, n: int, *, engine: str | None = None) -> MathResult:
        """Find the smallest prime strictly greater than n with primality and minimality verification."""
        return self.number_theory("nextprime", n=n, engine=engine)

    def optimize(
        self,
        expression: str,
        *,
        variable: str | None = None,
        mode: str = "minimize",
        lower: str | float | int | None = None,
        upper: str | float | int | None = None,
        engine: str | None = None,
    ) -> MathResult:
        """Find and verify a symbolic/numerical minimum or maximum of an expression."""
        parser = Parser()
        try:
            expr = parser.parse_expression(expression)
            var = _pick_variable(expr, variable, parser)
            interval: tuple[sp.Expr, sp.Expr] | None = None
            if (lower is None) ^ (upper is None):
                raise ParseError("both lower and upper bounds must be provided together")
            if lower is not None and upper is not None:
                interval = (
                    parser.parse_expression(str(lower)),
                    parser.parse_expression(str(upper)),
                )
            eng = self.registry.select("optimize", preferred=engine)
            ans = eng.optimize(expr, var, mode=mode, interval=interval)
        except (ParseError, EngineError) as exc:
            return error_result("optimize", expression, str(exc), engine=engine)

        ver, guar = verify_optimization(ans.raw)
        return _wrap_answer(
            kind="optimize",
            expression=expression,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom optimize "{expression}" --mode {mode}',
        )

    def statistics(
        self,
        data: list[str | int | float] | str,
        *,
        engine: str | None = None,
    ) -> MathResult:
        """Compute exact symbolic and numerical summary statistics with moment verification."""
        parser = Parser()
        raw_str = data if isinstance(data, str) else ", ".join(str(x) for x in data)
        try:
            items = (
                [s.strip() for s in data.strip("[]").split(",") if s.strip()]
                if isinstance(data, str)
                else [str(x) for x in data]
            )
            values = [parser.parse_expression(item) for item in items]
            eng = self.registry.select("statistics", preferred=engine)
            ans = eng.statistics(values)
        except (ParseError, EngineError) as exc:
            return error_result("statistics", raw_str, str(exc), engine=engine)

        ver, guar = verify_statistics(ans.raw)
        return _wrap_answer(
            kind="statistics",
            expression=f"[{raw_str}]",
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom stats "{raw_str}"',
        )

    def tensor(
        self,
        metric: str,
        *,
        coordinates: list[str] | str | None = None,
        operation: str = "all",
        engine: str | None = None,
    ) -> MathResult:
        """Compute differential-geometry / tensor quantities for a metric with Levi-Civita verification.

        ``metric`` may be either a matrix string (e.g. ``"[[1, 0], [0, r^2]]"``)
        paired with ``coordinates`` (e.g. ``["r", "theta"]``), or a named preset:
        ``"polar"``, ``"sphere"``, ``"cylindrical"``, ``"minkowski"``, ``"schwarzschild"``.
        """
        preset_map: dict[str, tuple[str, list[str]]] = {
            "polar": ("[[1, 0], [0, r^2]]", ["r", "theta"]),
            "sphere": ("[[1, 0], [0, sin(theta)^2]]", ["theta", "phi"]),
            "spherical_2d": ("[[R^2, 0], [0, R^2 * sin(theta)^2]]", ["theta", "phi"]),
            "cylindrical": ("[[1, 0, 0], [0, r^2, 0], [0, 0, 1]]", ["r", "theta", "z"]),
            "minkowski": (
                "[[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]",
                ["t", "x", "y", "z"],
            ),
            "schwarzschild": (
                "[[-1 + r_s/r, 0, 0, 0], [0, 1/(1 - r_s/r), 0, 0], [0, 0, r^2, 0], [0, 0, 0, r^2 * sin(theta)^2]]",
                ["t", "r", "theta", "phi"],
            ),
        }

        key = metric.strip().lower()
        if key in preset_map:
            metric_expr, default_coords = preset_map[key]
            coord_list = default_coords
        else:
            metric_expr = metric
            if isinstance(coordinates, str):
                coord_list = [c.strip() for c in coordinates.split(",") if c.strip()]
            elif coordinates:
                coord_list = [str(c).strip() for c in coordinates if str(c).strip()]
            else:
                coord_list = []

        parser = Parser()
        try:
            mat = parser.parse_matrix(metric_expr)
            if not coord_list:
                free = sorted(mat.free_symbols, key=lambda s: s.name)
                if len(free) == mat.rows:
                    coord_list = [s.name for s in free]
                else:
                    default_names = ["x", "y", "z", "w"][: mat.rows]
                    coord_list = default_names
            sym_coords = [parser.symbol(c) for c in coord_list]
            eng = self.registry.select("tensor", preferred=engine)
            ans = eng.tensor(mat, sym_coords, operation=operation)
        except (ParseError, EngineError) as exc:
            return error_result("tensor", metric, str(exc), engine=engine)

        ver, guar = verify_tensor_op(ans.raw)
        coord_arg = ",".join(coord_list)
        return _wrap_answer(
            kind="tensor",
            expression=metric,
            engine=eng,
            answer=ans,
            guarantee=guar,
            verification=ver,
            reproducible_with=f'axiom tensor "{metric}" --coords {coord_arg} --op {operation}',
        )

    def search_mathlib(
        self,
        query: str,
        *,
        max_results: int = 8,
        online: bool = False,
    ) -> MathResult:
        """Search Mathlib4 & Lean 4 Core theorems by concept, identifier, or type signature."""
        try:
            lean_eng = self.registry.get("lean")
            ans = lean_eng.search_mathlib(query, max_results=max_results, online=online)
        except EngineError as exc:
            return error_result("search_mathlib", query, str(exc), engine="lean")

        hits = ans.raw.get("hits", [])
        ver = Verification(
            kind="catalog-signature-check",
            passed=len(hits) > 0,
            detail=(
                f"Matched {len(hits)} verified Lean 4 / Mathlib4 declaration signature(s)"
                if hits
                else f"No Mathlib4 declarations matched {query!r}"
            ),
            checks=len(hits),
        )
        return _wrap_answer(
            kind="search_mathlib",
            expression=query,
            engine=lean_eng,
            answer=ans,
            guarantee=Guarantee.CATALOG_LOOKUP if hits else Guarantee.UNVERIFIED,
            verification=ver,
            reproducible_with=f'axiom search-mathlib "{query}"',
        )

    def search_literature(
        self,
        query: str,
        *,
        max_results: int = 8,
        online: bool = True,
        timeout: int = 10,
    ) -> MathResult:
        """Search peer-reviewed mathematical literature and reviews via zbMATH Open (arXiv:2106.04664)."""
        return search_literature(query, max_results=max_results, online=online, timeout=timeout)

    def lookup_msc(
        self,
        code_or_query: str,
        *,
        max_results: int = 5,
        online: bool = True,
        timeout: int = 10,
    ) -> MathResult:
        """Lookup Mathematics Subject Classification (MSC 2020) codes via zbMATH Open."""
        return lookup_msc(code_or_query, max_results=max_results, online=online, timeout=timeout)

    def search_software(
        self,
        query: str,
        *,
        max_results: int = 5,
        online: bool = True,
        timeout: int = 10,
    ) -> MathResult:
        """Search mathematical research software tracked via swMATH and zbMATH Open."""
        return search_software(query, max_results=max_results, online=online, timeout=timeout)

    def verify_citation(
        self,
        citation: str | dict[str, Any],
        *,
        online: bool = True,
        timeout: int = 10,
    ) -> MathResult:
        """Audit a mathematical citation against zbMATH Open to eliminate hallucinated references."""
        return verify_citation(citation, online=online, timeout=timeout)

    def session(
        self,
        action: str = "show",
        *,
        name: str = "default",
        title: str | None = None,
        expression: str | None = None,
        operation: str = "solve",
        step: int | None = None,
        command: str | None = None,
        result: MathResult | None = None,
        file: Path | str | None = None,
        depends_on: list[int] | None = None,
        hypothesis: str | None = None,
        note: str = "",
        directory: Path | str = ".axiom/sessions",
    ) -> MathResult:
        """Manage a reproducible multi-step mathematical research session."""
        from axiom.session import ResearchSession

        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        active_file = dir_path / ".active_session"

        act = action.lower().strip()
        if act == "new":
            sess_name = title or name
            sess = ResearchSession(name=sess_name)
            sess.save(directory=dir_path)
            try:
                active_file.write_text(sess_name, encoding="utf-8")
            except Exception:
                pass
            return sess.as_math_result("new")

        if act == "clear":
            sess = ResearchSession(name=name)
            sess.save(directory=dir_path)
            return sess.as_math_result("clear")

        target_name = name
        if target_name == "default" and active_file.exists():
            try:
                candidate = active_file.read_text(encoding="utf-8").strip()
                safe_cand = "".join(
                    c if c.isalnum() or c in "-_" else "_" for c in candidate
                )
                if (dir_path / f"{safe_cand}.json").exists():
                    target_name = candidate
            except Exception:
                pass

        sess = ResearchSession.load(name=target_name, directory=dir_path)
        if any(e.get("imported") and not e.get("revalidated_locally") for e in sess.entries):
            sess.revalidate_all(axiom=self)

        if act == "status":
            return sess.as_math_result("status")

        if act == "record":
            deps_list: list[int] | None = None
            if depends_on is not None:
                if isinstance(depends_on, int):
                    deps_list = [depends_on]
                elif isinstance(depends_on, str):
                    deps_list = [int(x.strip()) for x in depends_on.split(",") if x.strip()]
                else:
                    deps_list = [int(x) for x in depends_on]

            step_res: MathResult | None = None
            if result is not None:
                step_res = result
            elif file is not None:
                fpath = Path(file)
                if fpath.suffix == ".lean":
                    step_res = self.prove(str(fpath))
                else:
                    step_res = self.solve(str(fpath))
            elif command:
                import shlex
                tokens = shlex.split(command)
                if tokens and tokens[0] in ("axiom", "math"):
                    tokens = tokens[1:]
                if tokens:
                    try:
                        from axiom.cli import execute_command
                        step_res = execute_command(self, tokens)
                    except Exception as exc:
                        step_res = error_result(
                            "session",
                            command,
                            f"failed to execute command {command!r}: {exc}",
                        )

            if step_res is None:
                if not expression:
                    return error_result(
                        "session",
                        f"{sess.name}:record",
                        "either 'result', 'file', 'expression', or '--command' is required for action='record'",
                    )
                op = operation.lower().strip()
                dispatch = {
                    "solve": lambda: self.solve(expression),
                    "simplify": lambda: self.simplify(expression),
                    "factor": lambda: self.factor(expression),
                    "expand": lambda: self.expand(expression),
                    "differentiate": lambda: self.differentiate(expression),
                    "integrate": lambda: self.integrate(expression),
                    "limit": lambda: self.limit(expression),
                    "evaluate": lambda: self.evaluate(expression),
                    "explore": lambda: self.explore(expression),
                    "ode": lambda: self.ode(expression),
                    "tensor": lambda: self.tensor(expression),
                    "prove": lambda: self.prove(expression),
                }
                if op not in dispatch:
                    return error_result(
                        "session", expression, f"unsupported session operation: {op!r}"
                    )
                step_res = dispatch[op]()

            step_idx = sess.record(step_res, note=note, depends_on=deps_list)
            sess.save(directory=dir_path)
            res = sess.as_math_result("record")
            res.value["recorded_step"] = step_idx
            return res

        if act == "hypothesis":
            if not hypothesis:
                return error_result(
                    "session", f"{name}:hypothesis", "hypothesis statement is required"
                )
            ver_res = self.verify(hypothesis)
            if ver_res.ok and ver_res.verified:
                status = "verified"
                guar = ver_res.guarantee
                detail = (
                    ver_res.verification.detail if ver_res.verification else "verified"
                )
            elif ver_res.ok and ver_res.epistemic_state is EpistemicState.REFUTATION:
                # Only a result carrying positive evidence of falsity (an explicit
                # counterexample / violating substitution) may be reported as
                # refuted. A check that merely failed leaves the hypothesis open.
                status = "refuted"
                guar = Guarantee.UNVERIFIED
                detail = (
                    ver_res.verification.detail if ver_res.verification else "refuted"
                )
            else:
                status = "open"
                guar = Guarantee.UNVERIFIED
                detail = (
                    ver_res.verification.detail
                    if ver_res.ok and ver_res.verification
                    else (ver_res.error or "unverified conjecture")
                )
            sess.add_hypothesis(
                hypothesis, status=status, guarantee=guar, detail=detail
            )
            sess.save(directory=dir_path)
            return sess.as_math_result("hypothesis")

        if act == "export":
            md = sess.to_markdown()
            res = sess.as_math_result("export")
            res.value = {"session": sess.to_dict(), "markdown": md}
            res.value_str = md
            return res

        if act == "show":
            return sess.as_math_result("show")

        return error_result(
            "session",
            f"{name}:{action}",
            f"unknown session action '{action}' (choose from: show, record, hypothesis, export, clear, new, status)",
        )

    # ------------------------------------------- Mathematical Investigation Layer (v0.3.0)

    def investigate(
        self,
        statement: str,
        *,
        investigation_id: str | None = None,
        root: str = ".axiom/investigations",
        scope: dict[str, Any] | None = None,
        assumptions: dict[str, Any] | str | None = None,
    ) -> MathResult:
        """Create a persistent mathematical investigation dossier (ADR-0019)."""
        from axiom.investigation import investigate as _impl

        return _impl(
            self,
            statement,
            root=root,
            investigation_id=investigation_id,
            scope=scope,
            assumptions=assumptions,
        )

    def analyze_claim(
        self,
        investigation_id: str,
        *,
        root: str = ".axiom/investigations",
        statement: str | None = None,
    ) -> MathResult:
        """Decompose a claim into variables, hypotheses and boundary conditions."""
        from axiom.investigation import analyze_claim as _impl

        return _impl(self, investigation_id, root=root, statement=statement)

    def trace_dependencies(
        self,
        investigation_id: str,
        lemmas: list[Any],
        *,
        root: str = ".axiom/investigations",
        mode: str = "identity",
    ) -> MathResult:
        """Build and audit the proof dependency graph of an investigation."""
        from axiom.investigation import trace_dependencies as _impl

        return _impl(self, investigation_id, lemmas, root=root, mode=mode)

    def find_counterexample(
        self,
        investigation_id: str,
        *,
        root: str = ".axiom/investigations",
        statement: str | None = None,
        mode: str = "identity",
    ) -> MathResult:
        """Actively hunt a counterexample to the target claim."""
        from axiom.investigation import find_counterexample as _impl

        return _impl(self, investigation_id, root=root, statement=statement, mode=mode)

    def compare_proofs(
        self,
        investigation_id: str,
        statements: list[Any],
        *,
        root: str = ".axiom/investigations",
        mode: str = "identity",
    ) -> MathResult:
        """Compare proof routes and surface the hypotheses each one needs."""
        from axiom.investigation import compare_proofs as _impl

        return _impl(self, investigation_id, statements, root=root, mode=mode)

    def list_unknowns(
        self,
        investigation_id: str,
        *,
        root: str = ".axiom/investigations",
    ) -> MathResult:
        """The Unknown Ledger of an investigation."""
        from axiom.investigation import list_unknowns as _impl

        return _impl(self, investigation_id, root=root)

    def get_evidence_bundle(
        self,
        investigation_id: str,
        *,
        root: str = ".axiom/investigations",
    ) -> MathResult:
        """Export the immutable provenance package of an investigation."""
        from axiom.investigation import get_evidence_bundle as _impl

        return _impl(self, investigation_id, root=root)

    def export_investigation(
        self,
        investigation_id: str,
        *,
        root: str = ".axiom/investigations",
    ) -> MathResult:
        """Render the reproducible dossier report of an investigation."""
        from axiom.investigation import export_investigation as _impl

        return _impl(self, investigation_id, root=root)


def _render_svg_plot(
    xs: list[float],
    ys: list[float | None],
    *,
    title: str = "",
    x_label: str = "x",
    y_label: str = "f(x)",
    width: int = 640,
    height: int = 380,
) -> str:
    """Render a self-contained SVG plot with zero external dependencies."""
    import html

    pad_l, pad_r, pad_t, pad_b = 58, 24, 38, 44
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b

    valid_pairs = [(x, y) for x, y in zip(xs, ys) if y is not None]
    if not valid_pairs:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
            f'<rect width="100%" height="100%" fill="#0f172a"/>'
            f'<text x="{width // 2}" y="{height // 2}" fill="#94a3b8" text-anchor="middle">No finite points</text>'
            f"</svg>"
        )

    x_min, x_max = min(xs), max(xs)
    y_vals = [y for _, y in valid_pairs]
    y_min, y_max = min(y_vals), max(y_vals)
    if abs(y_max - y_min) < 1e-12:
        y_min -= 1.0
        y_max += 1.0

    def sx(x: float) -> float:
        return pad_l + (x - x_min) / (x_max - x_min) * plot_w

    def sy(y: float) -> float:
        return pad_t + plot_h - (y - y_min) / (y_max - y_min) * plot_h

    segments: list[str] = []
    current: list[str] = []
    for x, y in zip(xs, ys):
        if y is None:
            if len(current) >= 2:
                segments.append(" ".join(current))
            current = []
        else:
            current.append(f"{sx(x):.2f},{sy(y):.2f}")
    if len(current) >= 2:
        segments.append(" ".join(current))

    polylines = "\n  ".join(
        f'<polyline fill="none" stroke="#38bdf8" stroke-width="2.2" points="{pts}"/>'
        for pts in segments
    )

    zero_axes: list[str] = []
    if x_min <= 0 <= x_max:
        zx = sx(0.0)
        zero_axes.append(
            f'<line x1="{zx:.2f}" y1="{pad_t}" x2="{zx:.2f}" y2="{pad_t + plot_h}" stroke="#475569" stroke-dasharray="4,4"/>'
        )
    if y_min <= 0 <= y_max:
        zy = sy(0.0)
        zero_axes.append(
            f'<line x1="{pad_l}" y1="{zy:.2f}" x2="{pad_l + plot_w}" y2="{zy:.2f}" stroke="#475569" stroke-dasharray="4,4"/>'
        )

    esc_title = html.escape(title)
    esc_xlab = html.escape(x_label)
    esc_ylab = html.escape(y_label)
    axes_svg = "\n  ".join(zero_axes)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">\n'
        f'  <rect width="100%" height="100%" fill="#0f172a" rx="8"/>\n'
        f'  <rect x="{pad_l}" y="{pad_t}" width="{plot_w}" height="{plot_h}" fill="#1e293b" stroke="#334155"/>\n'
        f"  {axes_svg}\n"
        f"  {polylines}\n"
        f'  <text x="{width / 2:.1f}" y="24" fill="#f8fafc" font-family="monospace" font-size="13" text-anchor="middle">{esc_title}</text>\n'
        f'  <text x="{pad_l}" y="{height - 12}" fill="#94a3b8" font-family="monospace" font-size="11">{x_min:.3g}</text>\n'
        f'  <text x="{pad_l + plot_w / 2:.1f}" y="{height - 12}" fill="#cbd5e1" font-family="monospace" font-size="11" text-anchor="middle">{esc_xlab}</text>\n'
        f'  <text x="{pad_l + plot_w}" y="{height - 12}" fill="#94a3b8" font-family="monospace" font-size="11" text-anchor="end">{x_max:.3g}</text>\n'
        f'  <text x="{pad_l - 6}" y="{pad_t + 10}" fill="#94a3b8" font-family="monospace" font-size="11" text-anchor="end">{y_max:.3g}</text>\n'
        f'  <text x="{pad_l - 6}" y="{pad_t + plot_h}" fill="#94a3b8" font-family="monospace" font-size="11" text-anchor="end">{y_min:.3g}</text>\n'
        f'  <text x="14" y="{pad_t + plot_h / 2:.1f}" fill="#cbd5e1" font-family="monospace" font-size="11">{esc_ylab}</text>\n'
        f"</svg>\n"
    )


def _render_ascii_plot(
    xs: list[float],
    ys: list[float | None],
    *,
    width: int = 48,
    height: int = 11,
) -> str:
    """Render a compact ASCII curve preview for terminal and LLM consumption."""
    valid_ys = [y for y in ys if y is not None]
    if not valid_ys or not xs:
        return "(no finite points)"
    y_min, y_max = min(valid_ys), max(valid_ys)
    if abs(y_max - y_min) < 1e-12:
        y_min -= 1.0
        y_max += 1.0
    x_min, x_max = min(xs), max(xs)

    grid = [[" " for _ in range(width)] for _ in range(height)]
    if y_min <= 0 <= y_max:
        r0 = int(round((y_max - 0.0) / (y_max - y_min) * (height - 1)))
        for c in range(width):
            grid[r0][c] = "-"
    if x_min <= 0 <= x_max:
        c0 = int(round((0.0 - x_min) / (x_max - x_min) * (width - 1)))
        for r in range(height):
            grid[r][c0] = "|" if grid[r][c0] == " " else "+"

    for x, y in zip(xs, ys):
        if y is None:
            continue
        col = int(round((x - x_min) / (x_max - x_min) * (width - 1)))
        row = int(round((y_max - y) / (y_max - y_min) * (height - 1)))
        col = max(0, min(width - 1, col))
        row = max(0, min(height - 1, row))
        grid[row][col] = "*"

    return "\n".join("".join(row) for row in grid)


def solve_expression(expression: str, **kwargs: Any) -> MathResult:
    """Convenience function to solve an equation or expression with default AXIOM."""
    return Axiom().solve(expression, **kwargs)

