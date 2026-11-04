"""Deterministic numeric calculation tool (pure Python arithmetic)."""

import math

from docproc.schemas.tools import CalculateNumericInput, CalculateNumericOutput
from docproc.tools.base import BaseTool


def fmt(n: float) -> str:
    """Formats float without unnecessary decimal point if integer."""
    return str(int(n)) if n.is_integer() else str(n)


class CalculateNumericTool(BaseTool):
    """Performs deterministic arithmetic operations to prevent LLM calculation hallucinations."""

    name = "calculate_numeric"
    description = (
        "Calculates exact numeric results (add, subtract, multiply, divide, percentages). "
        "Operates deterministically in pure Python."
    )
    input_schema = CalculateNumericInput
    output_schema = CalculateNumericOutput

    async def run(self, args: CalculateNumericInput) -> CalculateNumericOutput:
        op = args.operation.lower()
        operands = args.operands
        unit = args.unit

        if not operands:
            return CalculateNumericOutput(
                formula_expressed="Error: No operands provided",
                status="failed",
                error="At least one operand is required.",
            )

        try:
            if op in ("add", "sum"):
                res = sum(operands)
                formula = f"{' + '.join(fmt(o) for o in operands)} = {fmt(res)}"

            elif op in ("subtract", "difference"):
                if len(operands) < 2:
                    return CalculateNumericOutput(
                        formula_expressed="Error: Subtraction requires >= 2 operands",
                        status="failed",
                        error="Subtraction requires at least two operands.",
                    )
                res = operands[0] - sum(operands[1:])
                formula = (
                    f"{fmt(operands[0])} - {' - '.join(fmt(o) for o in operands[1:])} = {fmt(res)}"
                )

            elif op == "multiply":
                res = math.prod(operands)
                formula = f"{' * '.join(fmt(o) for o in operands)} = {fmt(res)}"

            elif op == "divide":
                if len(operands) < 2:
                    return CalculateNumericOutput(
                        formula_expressed="Error: Division requires 2 operands",
                        status="failed",
                        error="Division requires at least two operands.",
                    )
                if operands[1] == 0:
                    return CalculateNumericOutput(
                        formula_expressed=f"{fmt(operands[0])} / 0 = Undefined",
                        status="failed",
                        error="Division by zero is undefined.",
                    )
                res = operands[0] / operands[1]
                formula = f"{fmt(operands[0])} / {fmt(operands[1])} = {fmt(res)}"

            elif op == "percentage_difference":
                if len(operands) < 2:
                    return CalculateNumericOutput(
                        formula_expressed="Error: Percentage difference requires 2 operands",
                        status="failed",
                        error="Percentage difference requires baseline and comparison operands.",
                    )
                baseline = operands[0]
                val = operands[1]
                if baseline == 0:
                    return CalculateNumericOutput(
                        formula_expressed="Error: Baseline operand is zero",
                        status="failed",
                        error="Cannot calculate percentage difference against zero baseline.",
                    )
                diff = abs(val - baseline)
                res = (diff / baseline) * 100.0
                formula = f"|{fmt(val)} - {fmt(baseline)}| / {fmt(baseline)} * 100 = {res:.2f}%"
                unit = unit or "%"

            elif op == "percentage_of":
                if len(operands) < 2:
                    return CalculateNumericOutput(
                        formula_expressed="Error: Percentage of requires 2 operands",
                        status="failed",
                        error="Requires numerator and denominator.",
                    )
                if operands[1] == 0:
                    return CalculateNumericOutput(
                        formula_expressed=f"{fmt(operands[0])} / 0 = Undefined",
                        status="failed",
                        error="Denominator cannot be zero.",
                    )
                res = (operands[0] / operands[1]) * 100.0
                formula = f"({fmt(operands[0])} / {fmt(operands[1])}) * 100 = {res:.2f}%"
                unit = unit or "%"

            else:
                return CalculateNumericOutput(
                    formula_expressed=f"Unsupported operation {op}",
                    status="failed",
                    error=f"Operation '{op}' is not supported.",
                )

            return CalculateNumericOutput(
                result=round(res, 4),
                unit=unit,
                formula_expressed=formula,
                status="completed",
                error=None,
            )

        except Exception as exc:
            return CalculateNumericOutput(
                formula_expressed="Computation exception",
                status="failed",
                error=f"Calculation error: {exc}",
            )
