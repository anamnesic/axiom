"""AXIOM — Mathematical Reasoning Engine.

Computational mathematics infrastructure for agents: engines are pluggable,
results carry evidence, and claims are independently verified.

    >>> import axiom
    >>> ax = axiom.Axiom()
    >>> r = ax.solve("x^2 - 5*x + 6 = 0")
    >>> r.value_str, r.guarantee.value
    ("['2', '3']", 'verified-substitution')
"""

from axiom.contract import Evidence, Guarantee, MathResult, Verification
from axiom.core import Axiom, solve_expression
from axiom.engines.base import Engine, EngineError
from axiom.engines.external_engines import JuliaEngine, SageEngine
from axiom.engines.lean_engine import LeanEngine
from axiom.engines.numeric_engine import NumericEngine
from axiom.engines.sympy_engine import SymPyEngine
from axiom.mcp_server import TOOL_DEFINITIONS, dispatch_tool
from axiom.parsing import ParseError, Parser
from axiom.registry import EngineRegistry
from axiom.session import ResearchSession

__version__ = "0.1.0"

__all__ = [
    "Axiom",
    "Engine",
    "EngineError",
    "EngineRegistry",
    "Evidence",
    "Guarantee",
    "JuliaEngine",
    "LeanEngine",
    "MathResult",
    "NumericEngine",
    "ParseError",
    "Parser",
    "ResearchSession",
    "SageEngine",
    "SymPyEngine",
    "TOOL_DEFINITIONS",
    "Verification",
    "dispatch_tool",
    "solve_expression",
    "__version__",
]
