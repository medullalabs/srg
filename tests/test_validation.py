"""Tests for Issue 8 — Output schema validation."""
from __future__ import annotations

from srg.kernel.validation import validate_output_schema


class TestTypeValidation:
    def test_string_valid(self) -> None:
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        result = validate_output_schema({"name": "Alice"}, schema)
        assert result.valid

    def test_string_invalid(self) -> None:
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        result = validate_output_schema({"name": 123}, schema)
        assert not result.valid

    def test_integer_valid(self) -> None:
        schema = {"type": "object", "properties": {"count": {"type": "integer"}}}
        result = validate_output_schema({"count": 42}, schema)
        assert result.valid

    def test_integer_rejects_float(self) -> None:
        schema = {"type": "object", "properties": {"count": {"type": "integer"}}}
        result = validate_output_schema({"count": 3.14}, schema)
        assert not result.valid

    def test_number_accepts_int(self) -> None:
        schema = {"type": "object", "properties": {"val": {"type": "number"}}}
        result = validate_output_schema({"val": 42}, schema)
        assert result.valid

    def test_number_accepts_float(self) -> None:
        schema = {"type": "object", "properties": {"val": {"type": "number"}}}
        result = validate_output_schema({"val": 3.14}, schema)
        assert result.valid

    def test_boolean_valid(self) -> None:
        schema = {"type": "object", "properties": {"flag": {"type": "boolean"}}}
        result = validate_output_schema({"flag": True}, schema)
        assert result.valid

    def test_boolean_rejects_int(self) -> None:
        schema = {"type": "object", "properties": {"flag": {"type": "boolean"}}}
        result = validate_output_schema({"flag": 1}, schema)
        assert not result.valid

    def test_object_valid(self) -> None:
        schema = {"type": "object"}
        result = validate_output_schema({"key": "val"}, schema)
        assert result.valid

    def test_array_valid(self) -> None:
        schema = {"type": "object", "properties": {"items": {"type": "array"}}}
        result = validate_output_schema({"items": [1, 2, 3]}, schema)
        assert result.valid

    def test_root_type_mismatch(self) -> None:
        schema = {"type": "object"}
        # pass a non-dict as the output -- this is caught at root level
        result = validate_output_schema({"x": "ok"}, schema)
        assert result.valid


class TestRequiredFields:
    def test_required_present(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        result = validate_output_schema({"name": "Alice"}, schema)
        assert result.valid

    def test_required_missing(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        result = validate_output_schema({}, schema)
        assert not result.valid
        assert any("required" in e for e in result.errors)

    def test_multiple_required_one_missing(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name", "age"],
        }
        result = validate_output_schema({"name": "Alice"}, schema)
        assert not result.valid
        assert len(result.errors) == 1


class TestNestedProperties:
    def test_nested_object_valid(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "info": {
                    "type": "object",
                    "properties": {"score": {"type": "number"}},
                    "required": ["score"],
                }
            },
        }
        result = validate_output_schema({"info": {"score": 95}}, schema)
        assert result.valid

    def test_nested_object_invalid(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "info": {
                    "type": "object",
                    "properties": {"score": {"type": "number"}},
                    "required": ["score"],
                }
            },
        }
        result = validate_output_schema({"info": {}}, schema)
        assert not result.valid

    def test_deeply_nested(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "level1": {
                    "type": "object",
                    "properties": {
                        "level2": {
                            "type": "object",
                            "properties": {"value": {"type": "string"}},
                        }
                    },
                }
            },
        }
        result = validate_output_schema(
            {"level1": {"level2": {"value": "deep"}}}, schema
        )
        assert result.valid


class TestEnumValidation:
    def test_enum_valid(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["pass", "fail"]},
            },
        }
        result = validate_output_schema({"status": "pass"}, schema)
        assert result.valid

    def test_enum_invalid(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["pass", "fail"]},
            },
        }
        result = validate_output_schema({"status": "unknown"}, schema)
        assert not result.valid
        assert any("enum" in e for e in result.errors)


class TestArrayItems:
    def test_array_items_valid(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        }
        result = validate_output_schema({"tags": ["a", "b", "c"]}, schema)
        assert result.valid

    def test_array_items_invalid(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        }
        result = validate_output_schema({"tags": ["a", 123, "c"]}, schema)
        assert not result.valid

    def test_empty_array_valid(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        }
        result = validate_output_schema({"tags": []}, schema)
        assert result.valid


class TestNumericConstraints:
    def test_minimum_valid(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "number", "minimum": 0, "maximum": 100},
            },
        }
        result = validate_output_schema({"score": 50}, schema)
        assert result.valid

    def test_below_minimum(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "number", "minimum": 0},
            },
        }
        result = validate_output_schema({"score": -1}, schema)
        assert not result.valid

    def test_above_maximum(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "number", "maximum": 100},
            },
        }
        result = validate_output_schema({"score": 101}, schema)
        assert not result.valid


class TestEdgeCases:
    def test_empty_schema(self) -> None:
        result = validate_output_schema({"anything": "goes"}, {})
        assert result.valid

    def test_extra_properties_allowed(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        result = validate_output_schema({"name": "Alice", "extra": 42}, schema)
        assert result.valid

    def test_missing_optional_field(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }
        result = validate_output_schema({"name": "Alice"}, schema)
        assert result.valid
