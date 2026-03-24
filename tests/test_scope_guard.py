"""Issue 16 — Scope guard tests.

Permanent guardrails against scope drift. These tests ensure that
SRG stays narrowly focused on semantic reasoning graphs and does
not accumulate workflow engine, adapter, or orchestration baggage.
"""
from __future__ import annotations

from pathlib import Path


from srg.models.node import NodeKind, ReasoningNode


# ---- locate the srg package root --------------------------------------

SRG_ROOT = Path(__file__).resolve().parent.parent / "srg"


def _all_module_names() -> set[str]:
    """Walk the srg package and collect all sub-module names (leaf names)."""
    names: set[str] = set()
    for item in SRG_ROOT.rglob("*.py"):
        names.add(item.stem)
    # Also check for directories that are Python packages
    for item in SRG_ROOT.rglob("__init__.py"):
        names.add(item.parent.name)
    return names


# ---- forbidden module tests -------------------------------------------


class TestNoForbiddenModules:
    """Assert no module with a forbidden name exists anywhere in srg/."""

    def test_no_adapter_module(self) -> None:
        assert "adapter" not in _all_module_names(), \
            "Found a module named 'adapter' in srg/ — this violates scope"

    def test_no_workflow_module(self) -> None:
        assert "workflow" not in _all_module_names(), \
            "Found a module named 'workflow' in srg/ — this violates scope"

    def test_no_scheduler_module(self) -> None:
        assert "scheduler" not in _all_module_names(), \
            "Found a module named 'scheduler' in srg/ — this violates scope"

    def test_no_stream_module(self) -> None:
        assert "stream" not in _all_module_names(), \
            "Found a module named 'stream' in srg/ — this violates scope"

    def test_no_transport_module(self) -> None:
        assert "transport" not in _all_module_names(), \
            "Found a module named 'transport' in srg/ — this violates scope"


# ---- NodeKind enum guard ----------------------------------------------


class TestNodeKindScope:
    def test_only_deterministic_and_agentic(self) -> None:
        """NodeKind MUST only have DETERMINISTIC and AGENTIC values."""
        members = set(NodeKind.__members__.keys())
        assert members == {"DETERMINISTIC", "AGENTIC"}, (
            f"NodeKind has unexpected members: {members}. "
            f"Only DETERMINISTIC and AGENTIC are allowed."
        )

    def test_node_kind_values(self) -> None:
        assert NodeKind.DETERMINISTIC.value == "deterministic"
        assert NodeKind.AGENTIC.value == "agentic"


# ---- ReasoningNode field guards ----------------------------------------


class TestReasoningNodeScope:
    def test_no_transform_field(self) -> None:
        """ReasoningNode MUST NOT have a 'transform' field."""
        field_names = set(ReasoningNode.model_fields.keys())
        assert "transform" not in field_names, \
            "ReasoningNode has a 'transform' field — this violates scope"

    def test_no_adapter_field(self) -> None:
        """ReasoningNode MUST NOT have an 'adapter' field."""
        field_names = set(ReasoningNode.model_fields.keys())
        assert "adapter" not in field_names, \
            "ReasoningNode has an 'adapter' field — this violates scope"

    def test_allowed_fields_only(self) -> None:
        """Smoke-check that the known fields are present."""
        field_names = set(ReasoningNode.model_fields.keys())
        expected = {
            "id",
            "kind",
            "inputs",
            "outputs",
            "description",
            "function_ref",
            "prompt_template",
            "output_schema",
            "contracts",
            "effects",
            "retry_policy",
            "metadata",
        }
        assert expected.issubset(field_names), (
            f"Missing expected fields: {expected - field_names}"
        )
