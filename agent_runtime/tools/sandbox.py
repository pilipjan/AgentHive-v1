"""Simulated Agent Tool Sandbox for safe, bounded execution."""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional


@dataclass
class ToolExecutionResult:
    """Outcome of sandboxed tool invocation."""

    success: bool
    tool_name: str
    output: Any
    error: Optional[str] = None
    execution_time_seconds: float = 0.0


class ToolSandbox:
    """Isolated execution environment for simulated agent tools with strict parameter validation."""

    @staticmethod
    def _tool_calculator(expression: str) -> float:
        """Safe arithmetic calculation."""
        # Whitelist safe characters
        clean = expression.strip()
        if not all(c in "0123456789+-*/(). " for c in clean):
            raise ValueError("Expression contains invalid non-arithmetic characters.")
        # Evaluate simple arithmetic
        result = eval(clean, {"__builtins__": None}, {})
        return float(result)

    @staticmethod
    def _tool_json_validator(json_string: str) -> Dict[str, Any]:
        """Validate and parse JSON string."""
        return json.loads(json_string)

    @staticmethod
    def _tool_word_counter(text: str) -> Dict[str, int]:
        """Count words and characters in text."""
        words = text.split()
        return {"word_count": len(words), "character_count": len(text)}

    @classmethod
    def get_registered_tools(cls) -> Dict[str, Callable]:
        """Return dictionary of permitted tool handlers."""
        return {
            "calculator": cls._tool_calculator,
            "json_validator": cls._tool_json_validator,
            "word_counter": cls._tool_word_counter,
        }

    @classmethod
    async def execute_tool(
        cls,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout_seconds: float = 10.0,
    ) -> ToolExecutionResult:
        """Execute a registered tool within the isolated sandbox."""
        start_time = time.time()
        tools = cls.get_registered_tools()

        if tool_name not in tools:
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                output=None,
                error=f"Tool '{tool_name}' is not registered in the safe execution sandbox.",
                execution_time_seconds=round(time.time() - start_time, 4),
            )

        handler = tools[tool_name]
        try:
            output = handler(**parameters)
            return ToolExecutionResult(
                success=True,
                tool_name=tool_name,
                output=output,
                execution_time_seconds=round(time.time() - start_time, 4),
            )
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                tool_name=tool_name,
                output=None,
                error=f"Execution error: {str(e)}",
                execution_time_seconds=round(time.time() - start_time, 4),
            )
