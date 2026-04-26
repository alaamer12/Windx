"""Dynamic cross-field validation engine driven by YAML configuration.

Reads validation rules from YAML page configs and evaluates them against
form data at runtime. No hardcoded field names, tolerances, or formulas.

Supported rule types inside an attribute's ``validation_rules`` block:

    required_when:
        operator: equals
        field: some_field
        value: some_value
      error_message: "..."

    tolerance_check:
        compare_field: other_field
        max_difference: 50
        unit: mm
        error_message: "..."

    formula_check:
        formula: "field_a * field_b"
        tolerance: 0.1          # 10%
        error_message: "..."
"""
from __future__ import annotations

import logging
import operator as _op
from typing import Any

from app.core.config_loader import RuntimeConfigLoader

logger = logging.getLogger(__name__)

# Whitelist of safe arithmetic operators for formula evaluation
_SAFE_OPS: dict[str, Any] = {
    "*": _op.mul,
    "/": _op.truediv,
    "+": _op.add,
    "-": _op.sub,
}


def _eval_formula(formula: str, form_data: dict[str, Any]) -> float | None:
    """Safely evaluate a two-operand arithmetic formula using form_data values.

    Supports exactly one operator between two field names, e.g.:
        "price_per_meter * length_of_beam"

    Returns None if either operand is missing or non-numeric.
    Never calls eval() — whitelist approach only.
    """
    formula = formula.strip()
    for op_str, op_fn in _SAFE_OPS.items():
        if op_str in formula:
            parts = formula.split(op_str, 1)
            if len(parts) == 2:
                left_key = parts[0].strip()
                right_key = parts[1].strip()
                left = form_data.get(left_key)
                right = form_data.get(right_key)
                if left is None or right is None:
                    return None
                try:
                    return op_fn(float(left), float(right))
                except (TypeError, ValueError, ZeroDivisionError):
                    return None
    # Single field reference (no operator)
    val = form_data.get(formula)
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _render_message(template: str, context: dict[str, Any]) -> str:
    """Render an error message template with context variables.

    e.g. "Max diff is {max_difference}{unit}" → "Max diff is 50mm"
    Returns the template unchanged if a key is missing.
    """
    try:
        return template.format(**context)
    except (KeyError, ValueError):
        return template


class DynamicValidationEngine:
    """Validate form data against cross-field rules defined in YAML.

    Usage::

        engine = DynamicValidationEngine()
        errors = engine.validate_form(form_data, "profile")
        # errors: {"field_name": "error message", ...}
    """

    def __init__(self) -> None:
        # Import here to avoid circular import (entry.py imports this module)
        from app.services.entry import ConditionEvaluator
        self._condition_evaluator = ConditionEvaluator()

    def validate_field(
        self,
        field_name: str,
        field_value: Any,
        form_data: dict[str, Any],
        field_config: dict[str, Any],
    ) -> str | None:
        """Validate one field against its YAML cross-field rules.

        Checks in order: required_when → tolerance_check → formula_check.
        Returns an error message string on first failure, None if all pass.
        Basic rules (min/max/pattern) are handled separately by validate_field_value().
        """
        rules = field_config.get("validation_rules") or {}
        field_label = field_config.get("display_name") or field_name

        # --- required_when ---
        if "required_when" in rules:
            condition = rules["required_when"]
            is_required = self._condition_evaluator.evaluate_condition(condition, form_data)
            if is_required and (field_value is None or field_value == ""):
                default_msg = f"{field_label} is required"
                return _render_message(
                    rules.get("error_message", default_msg),
                    {"field_label": field_label},
                )

        # --- tolerance_check ---
        if "tolerance_check" in rules and field_value is not None:
            tc = rules["tolerance_check"]
            compare_field = tc.get("compare_field")
            max_diff = tc.get("max_difference")
            compare_value = form_data.get(compare_field) if compare_field else None

            if compare_value is not None and max_diff is not None:
                try:
                    diff = abs(float(field_value) - float(compare_value))
                    if diff > float(max_diff):
                        unit = tc.get("unit", "")
                        default_msg = (
                            f"{field_label} should not differ from "
                            f"{compare_field} by more than {max_diff}{unit}"
                        )
                        return _render_message(
                            tc.get("error_message", default_msg),
                            {
                                "field_label": field_label,
                                "compare_field": compare_field,
                                "max_difference": max_diff,
                                "unit": unit,
                            },
                        )
                except (TypeError, ValueError):
                    pass

        # --- formula_check ---
        if "formula_check" in rules and field_value is not None:
            fc = rules["formula_check"]
            formula = fc.get("formula", "")
            tolerance = float(fc.get("tolerance", 0.1))
            expected = _eval_formula(formula, form_data)

            if expected is not None and expected != 0:
                try:
                    actual = float(field_value)
                    if abs(actual - expected) > abs(expected) * tolerance:
                        default_msg = f"{field_label} should be approximately {formula}"
                        return _render_message(
                            fc.get("error_message", default_msg),
                            {
                                "field_label": field_label,
                                "formula": formula,
                                "tolerance": f"{int(tolerance * 100)}%",
                            },
                        )
                except (TypeError, ValueError):
                    pass

        return None

    def validate_form(
        self,
        form_data: dict[str, Any],
        page_type: str,
    ) -> dict[str, str]:
        """Validate all cross-field rules for a page type.

        Loads the page YAML config, iterates attributes that have cross-field
        rules, and returns {field_name: error_message} for all failures.
        """
        errors: dict[str, str] = {}
        config = RuntimeConfigLoader.load_page_config(page_type)

        for attr in config.get("attributes", []):
            field_name = attr.get("name")
            if not field_name:
                continue

            rules = attr.get("validation_rules") or {}
            has_cross_field = any(
                k in rules for k in ("required_when", "tolerance_check", "formula_check")
            )
            if not has_cross_field:
                continue

            field_value = form_data.get(field_name)
            error = self.validate_field(field_name, field_value, form_data, attr)
            if error:
                errors[field_name] = error

        return errors
