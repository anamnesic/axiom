import subprocess
import shutil
import re
from pathlib import Path

from backend.core.safe_math import SafeMathEvaluator


# Pre-built theorem templates for common identities
THEOREM_TEMPLATES = {
    "quadratic": {
        "name": "quadratic_formula",
        "statement": (
            "theorem quadratic_formula (a b c x : ℝ) (h : a*x^2 + b*x + c = 0) "
            "(hdiscrim : b^2 - 4*a*c ≥ 0) :\n"
            "  x = (-b + Real.sqrt (b^2 - 4*a*c)) / (2*a) ∨\n"
            "  x = (-b - Real.sqrt (b^2 - 4*a*c)) / (2*a) :="
        ),
        "proof": "by\n  sorry",
    },
    "pythagoras": {
        "name": "pythagorean_theorem",
        "statement": (
            "theorem pythagorean_theorem (a b c : ℝ) (h : a^2 + b^2 = c^2) :\n"
            "  a^2 + b^2 = c^2 :="
        ),
        "proof": "by\n  exact h",
    },
    "sin2_cos2": {
        "name": "sin_squared_add_cos_squared",
        "statement": (
            "theorem sin_squared_add_cos_squared (x : ℝ) :\n"
            "  Real.sin x ^ 2 + Real.cos x ^ 2 = 1 :="
        ),
        "proof": "by\n  exact Real.sin_sq_add_cos_sq x",
    },
    "derivative_power": {
        "name": "derivative_power_rule",
        "statement": (
            "theorem derivative_power_rule (x : ℝ) (n : ℕ) :\n"
            "  deriv (λ x => x ^ (n+1 : ℕ)) x = (n+1 : ℝ) * x ^ n :="
        ),
        "proof": "by\n  simp [deriv, pow_succ]",
    },
}


class LeanBridge:
    def __init__(self):
        self.lake_path = self._find_lake()

    def _find_lake(self) -> str | None:
        """Search for lake in PATH and common install locations."""
        path = shutil.which("lake")
        if path:
            return path
        home = Path.home()
        candidates = [
            home / ".elan" / "bin" / "lake",
            home / ".elan" / "bin" / "lake.exe",
            Path("C:/Program Files/elan/bin/lake.exe"),
            Path("C:/Program Files/Lean/bin/lake.exe"),
        ]
        for c in candidates:
            if c.exists():
                return str(c)
        return None

    def verify(self, theorem: str, proof: str = "") -> dict:
        env = None
        elan_bin = Path.home() / ".elan" / "bin"
        if elan_bin.exists():
            env = {"PATH": str(elan_bin) + ";" + __import__("os").environ.get("PATH", "")}

        if not self.lake_path:
            return {
                "verified": False,
                "diagnostics": [
                    "Lean 4 (lake) não encontrado.\n"
                    "Instalação automática em andamento... "
                    "Tente novamente em alguns minutos.",
                ],
            }

        code = f"""
import Mathlib
open Real

{theorem}
"""
        if proof:
            code += f"\n{proof}"

        lean_dir = str(Path(__file__).parent.parent.parent / "lean")
        try:
            result = subprocess.run(
                [self.lake_path, "run"],
                input=code,
                text=True,
                capture_output=True,
                timeout=60,
                cwd=lean_dir,
                env=env,
            )
            diagnostics = self._parse_diagnostics(result.stdout + result.stderr)
            return {
                "verified": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "diagnostics": diagnostics,
            }
        except subprocess.TimeoutExpired:
            return {"verified": False, "diagnostics": ["Lean verification timed out (60s)"]}
        except Exception as e:
            return {"verified": False, "diagnostics": [str(e)]}

    def _parse_diagnostics(self, output: str) -> list:
        """Parse Lean output into structured diagnostic messages."""
        messages = []
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Classify severity
            if "error" in line.lower():
                level = "error"
            elif "warning" in line.lower():
                level = "warning"
            elif "info" in line.lower():
                level = "info"
            else:
                level = "info"
            messages.append({"level": level, "message": line})
        return messages

    def get_templates(self) -> list:
        """Return available theorem templates."""
        return [
            {"id": tid, "name": tpl["name"], "statement": tpl["statement"]}
            for tid, tpl in THEOREM_TEMPLATES.items()
        ]

    def sympy_to_lean(self, expression: str) -> str:
        """Convert a SymPy expression string to Lean syntax."""
        try:
            # Handle equality expressions: split on '=' outside parens
            eq_parts = self._split_equality(expression)
            if eq_parts is not None:
                lhs, rhs = eq_parts
                return f"{self._sympy_to_lean_inner(lhs)} = {self._sympy_to_lean_inner(rhs)}"
            return self._sympy_to_lean_inner(expression)
        except Exception:
            return f"theorem conversion_error : sorry := by sorry"

    def _split_equality(self, s: str):
        """Split an expression on the top-level = outside any brackets/parens."""
        depth = 0
        for i, ch in enumerate(s):
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "=" and depth == 0 and i > 0 and i < len(s) - 1:
                return s[:i].strip(), s[i+1:].strip()
        return None

    def _sympy_to_lean_inner(self, expression: str) -> str:
        """Convert a single SymPy expression (no equality) to Lean syntax."""
        expr = SafeMathEvaluator().parse_expression(expression)
        lean_str = repr(expr)

        # Basic operator replacements
        lean_str = lean_str.replace("**", " ^ ")

        # Function mappings
        func_map = {
            "sin": "Real.sin", "cos": "Real.cos", "tan": "Real.tan",
            "asin": "Real.arcsin", "acos": "Real.arccos", "atan": "Real.arctan",
            "sinh": "Real.sinh", "cosh": "Real.cosh", "tanh": "Real.tanh",
            "exp": "Real.exp", "log": "Real.log", "sqrt": "Real.sqrt",
            "Abs": "abs", "sign": "sign",
        }
        for old, new in func_map.items():
            lean_str = lean_str.replace(old + "(", new + " (")

        # Constants
        lean_str = lean_str.replace("pi", "Real.pi")
        lean_str = lean_str.replace(",", " , ")
        lean_str = re.sub(r'\s+', ' ', lean_str).strip()

        return lean_str

    def generate_proof(self, expression: str, theorem_name: str = "auto") -> dict:
        """Generate a Lean theorem + proof scaffold from a SymPy expression."""
        lean_expr = self.sympy_to_lean(expression)

        # If conversion failed, use sorry
        if "conversion_error" in lean_expr or "sorry" in lean_expr:
            proof = "by\n  sorry"
        # Trig identities
        elif "Real.sin" in lean_expr or "Real.cos" in lean_expr:
            proof = "by\n  simp [Real.sin_sq_add_cos_sq]"
        # Equality with recognizable arithmetic operations
        elif "=" in lean_expr and any(op in lean_expr for op in ["^", " * ", " + ", " - ", " / "]):
            proof = "by\n  native_decide"
        # Power expressions (non-equality)
        elif "^" in lean_expr:
            proof = "by\n  ring"
        # Fallback for unknown expressions
        else:
            proof = "by\n  sorry"

        theorem = (
            f"theorem {theorem_name} : {lean_expr} :=\n{proof}"
        )
        return {
            "theorem": theorem,
            "lean_expression": lean_expr,
            "proof_tactic": proof,
        }

    def extract_goal(self, code: str) -> dict:
        """Extract context and target goal from Lean code (syntactic analysis)."""
        import re
        context = []
        target = ""
        lines = code.strip().split("\n")

        for line in lines:
            line = line.strip()
            # Find theorem signature
            if line.startswith("theorem "):
                # Pattern: theorem name (binders) : target :=
                m = re.match(
                    r"^theorem\s+\w+\s*((?:\([^)]*\)\s*)*):(.*?):=",
                    line,
                )
                if m:
                    target = m.group(2).strip()
                    binder_section = m.group(1)
                    # Parse each (...) group
                    for bg in re.findall(r"\(([^()]*)\)", binder_section):
                        if ":" in bg:
                            # Handle "a b c : Type" (multiple names, one type)
                            bg = bg.strip()
                            type_part = bg.split(":", 1)[1].strip()
                            names_part = bg.split(":", 1)[0].strip()
                            for name in names_part.split():
                                context.append({
                                    "name": name.strip(),
                                    "type": type_part,
                                })

        return {
            "context": context,
            "target": target,
        }
