"""Base tool interface for opensre.

All tools must inherit from BaseTool and implement the required methods
as defined in .cursor/rules/tools.mdc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Encapsulates the result of a tool execution."""

    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.success


class BaseTool(ABC):
    """Abstract base class for all opensre tools.

    Subclasses must provide:
      - my_tool_name  (class-level str)
      - MyToolName    (the class name itself)
      - is_available  (classmethod)
      - extract_params
      - run

    Example
    -------
    >>> class EchoTool(BaseTool):
    ...     my_tool_name = "echo"
    ...
    ...     @classmethod
    ...     def is_available(cls) -> bool:
    ...         return True
    ...
    ...     def extract_params(self, raw: dict[str, Any]) -> dict[str, Any]:
    ...         return {"message": raw.get("message", "")}
    ...
    ...     def run(self, params: dict[str, Any]) -> ToolResult:
    ...         return ToolResult(success=True, output=params["message"])
    """

    #: Unique snake_case identifier for this tool (required by tools.mdc)
    my_tool_name: str = ""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "my_tool_name", ""):
            raise TypeError(
                f"{cls.__name__} must define a non-empty 'my_tool_name' class attribute."
            )

    # ------------------------------------------------------------------
    # Required interface
    # ------------------------------------------------------------------

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Return True if the tool's dependencies / env are satisfied."""

    @abstractmethod
    def extract_params(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalise *raw* input into a clean params dict.

        Raise ValueError with a descriptive message when required keys are
        missing or values are out of range.
        """

    @abstractmethod
    def run(self, params: dict[str, Any]) -> ToolResult:
        """Execute the tool with pre-validated *params*.

        Always returns a ToolResult; never raises unless there is an
        unrecoverable programming error.
        """

    # ------------------------------------------------------------------
    # Convenience helper
    # ------------------------------------------------------------------

    def execute(self, raw: dict[str, Any]) -> ToolResult:
        """High-level entry point: extract params then run.

        Catches extraction errors and surfaces them as a failed ToolResult
        so callers don't need to handle ValueError themselves.
        """
        if not self.is_available():
            # NOTE: I added this availability check so callers get a clear
            # error message instead of a cryptic failure mid-run.
            return ToolResult(
                success=False,
                error=f"Tool '{self.my_tool_name}' is not available in the current environment.",
            )
        try:
            params = self.extract_params(raw)
        except ValueError as exc:
            return ToolResult(success=False, error=str(exc))
        return self.run(params)
