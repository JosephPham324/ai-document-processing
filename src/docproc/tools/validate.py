"""Field and business rule validation tool."""

from docproc.schemas.tools import (
    ValidateFieldsInput,
    ValidateFieldsOutput,
    ValidationResultItem,
    ValidationRuleRequest,
)
from docproc.tools.base import BaseTool


def evaluate_single_rule(rule: ValidationRuleRequest) -> ValidationResultItem:
    """Evaluates an individual rule condition against actual and expected values."""
    cond = rule.expected_condition
    act = rule.actual_value
    exp = rule.expected_value
    srcs = rule.sources

    if act is None:
        return ValidationResultItem(
            rule_id=rule.rule_id,
            status="unknown",
            message=f"Rule '{rule.rule_id}' failed: Actual value for '{rule.field_name}' was not found.",
            sources=srcs,
        )

    try:
        if cond == "equals":
            passed = str(act).strip().lower() == str(exp).strip().lower()
            msg = (
                f"Rule '{rule.rule_id}' passed: '{rule.field_name}' matches expected '{exp}'."
                if passed
                else f"Rule '{rule.rule_id}' failed: '{rule.field_name}' is '{act}', expected '{exp}'."
            )

        elif cond == "not_equals":
            passed = str(act).strip().lower() != str(exp).strip().lower()
            msg = (
                f"Rule '{rule.rule_id}' passed: '{rule.field_name}' differs from '{exp}'."
                if passed
                else f"Rule '{rule.rule_id}' failed: '{rule.field_name}' equals forbidden value '{exp}'."
            )

        elif cond == "must_not_exceed":
            act_num = float(act)
            exp_num = float(exp)
            passed = act_num <= exp_num
            msg = (
                f"Rule '{rule.rule_id}' passed: {act_num} does not exceed threshold {exp_num}."
                if passed
                else f"Rule '{rule.rule_id}' failed: {act_num} exceeds allowable limit of {exp_num}."
            )

        elif cond == "must_at_least":
            act_num = float(act)
            exp_num = float(exp)
            passed = act_num >= exp_num
            msg = (
                f"Rule '{rule.rule_id}' passed: {act_num} satisfies minimum requirement of {exp_num}."
                if passed
                else f"Rule '{rule.rule_id}' failed: {act_num} is below minimum requirement of {exp_num}."
            )

        elif cond == "contains":
            passed = str(exp).lower() in str(act).lower()
            msg = (
                f"Rule '{rule.rule_id}' passed: '{act}' contains '{exp}'."
                if passed
                else f"Rule '{rule.rule_id}' failed: '{act}' does not contain '{exp}'."
            )

        elif cond == "in_set":
            options = [
                str(x).strip().lower()
                for x in (exp if isinstance(exp, (list, tuple, set)) else [exp])
            ]
            passed = str(act).strip().lower() in options
            msg = (
                f"Rule '{rule.rule_id}' passed: '{act}' is in approved set."
                if passed
                else f"Rule '{rule.rule_id}' failed: '{act}' is not in approved set ({exp})."
            )

        else:
            return ValidationResultItem(
                rule_id=rule.rule_id,
                status="unknown",
                message=f"Unsupported validation condition: {cond}",
                sources=srcs,
            )

        return ValidationResultItem(
            rule_id=rule.rule_id,
            status="passed" if passed else "failed",
            message=msg,
            sources=srcs,
        )

    except (ValueError, TypeError) as conv_err:
        return ValidationResultItem(
            rule_id=rule.rule_id,
            status="unknown",
            message=f"Type error evaluating rule '{rule.rule_id}': {conv_err}",
            sources=srcs,
        )


class ValidateFieldsTool(BaseTool):
    """Evaluates business and policy rules against extracted evidence."""

    name = "validate_fields"
    description = (
        "Validates extracted values against explicit policies or benchmark thresholds "
        "(e.g. equals, must_not_exceed, must_at_least, contains)."
    )
    input_schema = ValidateFieldsInput
    output_schema = ValidateFieldsOutput

    async def run(self, args: ValidateFieldsInput) -> ValidateFieldsOutput:
        results = [evaluate_single_rule(r) for r in args.rules]
        return ValidateFieldsOutput(
            validation_results=results,
            status="completed",
            error=None,
        )
