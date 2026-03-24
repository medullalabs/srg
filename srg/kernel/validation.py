"""Issue 8 — Built-in JSON Schema output validation (no external deps)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Result of validating output against a JSON schema."""

    valid: bool
    errors: list[str] = Field(default_factory=list)


def _type_matches(value: Any, expected_type: str) -> bool:
    """Check if *value* matches the JSON Schema *expected_type*."""
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "null":
        return value is None
    return False


def _validate_value(
    value: Any,
    schema: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    """Recursively validate *value* against *schema*, appending to *errors*."""

    # --- type check ---
    schema_type = schema.get("type")
    if schema_type is not None:
        if not _type_matches(value, schema_type):
            errors.append(
                f"{path}: expected type '{schema_type}', "
                f"got {type(value).__name__}"
            )
            return  # cannot inspect further if type is wrong

    # --- enum ---
    enum_values = schema.get("enum")
    if enum_values is not None:
        if value not in enum_values:
            errors.append(
                f"{path}: value {value!r} not in enum {enum_values}"
            )

    # --- numeric constraints ---
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(
                f"{path}: {value} < minimum {schema['minimum']}"
            )
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(
                f"{path}: {value} > maximum {schema['maximum']}"
            )

    # --- object: properties + required ---
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for req_field in required:
            if req_field not in value:
                errors.append(f"{path}: missing required field '{req_field}'")

        for prop_name, prop_schema in properties.items():
            if prop_name in value:
                _validate_value(
                    value[prop_name],
                    prop_schema,
                    f"{path}.{prop_name}",
                    errors,
                )

    # --- array: items ---
    if isinstance(value, list):
        items_schema = schema.get("items")
        if items_schema is not None:
            for i, item in enumerate(value):
                _validate_value(
                    item,
                    items_schema,
                    f"{path}[{i}]",
                    errors,
                )


def validate_output_schema(
    output: dict[str, Any],
    schema: dict[str, Any],
) -> ValidationResult:
    """Validate *output* against a JSON Schema *schema*.

    Supports: type, required, properties (nested), enum, array items,
    minimum, maximum.  No external dependencies.
    """
    errors: list[str] = []
    _validate_value(output, schema, "$", errors)
    return ValidationResult(valid=len(errors) == 0, errors=errors)
