"""Engine registry for AXIOM.

Manages available mathematical engines (symbolic, numerical, formal proof, and
external scientific providers) and dispatches operations to an appropriate
backend while preserving a uniform result contract.
"""

from __future__ import annotations

from pathlib import Path

from axiom.engines.base import Engine, EngineError, EngineInfo
from axiom.engines.external_engines import JuliaEngine, SageEngine
from axiom.engines.lean_engine import LeanEngine
from axiom.engines.numeric_engine import NumericEngine
from axiom.engines.sympy_engine import SymPyEngine


class EngineRegistry:
    """Registry of mathematical engines indexed by name."""

    def __init__(
        self,
        *,
        register_defaults: bool = True,
        lean_binary: str | Path | None = None,
    ) -> None:
        self._engines: dict[str, Engine] = {}
        self._default_order: list[str] = []
        if register_defaults:
            self.register(SymPyEngine(), default=True)
            self.register(NumericEngine())
            self.register(LeanEngine(lean_binary=lean_binary))
            self.register(SageEngine())
            self.register(JuliaEngine())

    def register(self, engine: Engine, *, default: bool = False) -> None:
        """Register an engine instance."""
        self._engines[engine.name] = engine
        if engine.name in self._default_order:
            self._default_order.remove(engine.name)
        if default:
            self._default_order.insert(0, engine.name)
        else:
            self._default_order.append(engine.name)

    def get(self, name: str) -> Engine:
        """Retrieve an engine by name or raise :class:`EngineError`."""
        key = name.lower().strip()
        if key not in self._engines:
            available = ", ".join(self._engines) or "none"
            raise EngineError(
                f"unknown engine '{name}' (available: {available})"
            )
        return self._engines[key]

    def select(self, operation: str, preferred: str | None = None) -> Engine:
        """Return an engine capable of ``operation``."""
        if preferred:
            engine = self.get(preferred)
            engine.require(operation)
            return engine
        for name in self._default_order:
            engine = self._engines[name]
            if engine.supports(operation):
                return engine
        available = ", ".join(self._engines) or "none"
        raise EngineError(
            f"no registered engine supports '{operation}' "
            f"(registered: {available})"
        )

    def list_engines(self) -> list[EngineInfo]:
        """Return metadata for all registered engines in priority order."""
        return [self._engines[name].info for name in self._default_order]

    def names(self) -> list[str]:
        return list(self._default_order)
