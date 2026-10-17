"""Engine abstraction: any mathematics backend that answers AXIOM operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class EngineError(Exception):
    """An engine could not perform the requested operation."""


@dataclass
class Answer:
    """Raw engine output, later wrapped into a :class:`MathResult` by the core.

    ``value`` must be JSON-serializable (it travels over MCP). ``raw`` holds
    live SymPy objects used by the core for independent verification and is
    never serialized into evidence.
    """

    value: Any
    value_str: str
    latex: str | None = None
    method: str = ""
    steps: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EngineInfo:
    name: str
    version: str
    capabilities: tuple[str, ...]


class Engine:
    """Base class for mathematics engines.

    Subclasses set :attr:`name`, :attr:`version`, :attr:`capabilities` and
    implement the operations they advertise.
    """

    name: str = "engine"
    version: str = "0"
    capabilities: tuple[str, ...] = ()

    @property
    def info(self) -> EngineInfo:
        return EngineInfo(self.name, self.version, tuple(self.capabilities))

    def supports(self, operation: str) -> bool:
        return operation in self.capabilities

    def require(self, operation: str):
        """Return the bound method for ``operation`` or raise EngineError."""
        if not self.supports(operation):
            raise EngineError(
                f"engine '{self.name}' does not support '{operation}' "
                f"(capabilities: {', '.join(self.capabilities) or 'none'})")
        return getattr(self, operation)
