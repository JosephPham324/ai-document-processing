"""Fixed allowlist tool registry and execution dispatcher."""

import asyncio
import logging
import time
from typing import Any

from pydantic import ValidationError

from docproc.config import get_settings
from docproc.schemas.tools import ToolExecutionRecord
from docproc.tools.base import BaseTool
from docproc.tools.calculate import CalculateNumericTool
from docproc.tools.compare import CompareDocumentValuesTool
from docproc.tools.extract import ExtractStructuredFieldsTool
from docproc.tools.validate import ValidateFieldsTool

logger = logging.getLogger(__name__)

# Fixed tool registry dictionary
TOOL_REGISTRY: dict[str, BaseTool] = {
    "extract_structured_fields": ExtractStructuredFieldsTool(),
    "validate_fields": ValidateFieldsTool(),
    "compare_document_values": CompareDocumentValuesTool(),
    "calculate_numeric": CalculateNumericTool(),
}


def get_allowlisted_tools() -> list[str]:
    """Returns list of allowed tool names."""
    return list(TOOL_REGISTRY.keys())


async def execute_tool(
    tool_name: str,
    raw_args: dict[str, Any],
    timeout_seconds: int | None = None,
) -> ToolExecutionRecord:
    """Validates arguments against typed tool schemas and safely executes tool."""
    settings = get_settings()
    timeout = timeout_seconds or settings.TOOL_TIMEOUT_SECONDS

    # 1. Allowlist validation
    if tool_name not in TOOL_REGISTRY:
        logger.warning(f"Attempted execution of unallowlisted tool: '{tool_name}'")
        return ToolExecutionRecord(
            tool_name=tool_name,
            status="failed",
            duration_ms=0,
            error=f"Tool '{tool_name}' is not in the allowlist. Allowed: {get_allowlisted_tools()}",
            result=None,
        )

    tool = TOOL_REGISTRY[tool_name]
    start_time = time.perf_counter()

    # 2. Schema validation
    try:
        validated_input = tool.input_schema.model_validate(raw_args)
    except ValidationError as val_err:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        logger.warning(f"Tool '{tool_name}' validation failed: {val_err}")
        return ToolExecutionRecord(
            tool_name=tool_name,
            status="failed",
            duration_ms=elapsed_ms,
            error=f"Invalid arguments for tool '{tool_name}': {val_err.errors()}",
            result=None,
        )

    # 3. Execution with timeout guardrail
    try:
        output = await asyncio.wait_for(tool.run(validated_input), timeout=timeout)
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return ToolExecutionRecord(
            tool_name=tool_name,
            status="completed",
            duration_ms=elapsed_ms,
            error=None,
            result=output.model_dump(),
        )
    except TimeoutError:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error(f"Tool '{tool_name}' timed out after {timeout} seconds.")
        return ToolExecutionRecord(
            tool_name=tool_name,
            status="failed",
            duration_ms=elapsed_ms,
            error=f"Tool '{tool_name}' execution timed out after {timeout}s.",
            result=None,
        )
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        logger.error(f"Tool '{tool_name}' execution exception: {exc}", exc_info=True)
        return ToolExecutionRecord(
            tool_name=tool_name,
            status="failed",
            duration_ms=elapsed_ms,
            error=f"Tool execution failed: {exc}",
            result=None,
        )
