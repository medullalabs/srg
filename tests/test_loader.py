"""Tests for Issue 4 — YAML loader."""
from __future__ import annotations

from pathlib import Path

import pytest

from srg.models.node import NodeKind
from srg.runtime.loader import LoadError, load_graph


@pytest.fixture()
def valid_yaml(tmp_path: Path) -> Path:
    content = """\
name: test_graph
nodes:
  - id: step_one
    kind: deterministic
    inputs: [x]
    outputs: [y]
    function_ref: my_func
edges: []
"""
    p = tmp_path / "valid.yaml"
    p.write_text(content)
    return p


@pytest.fixture()
def valid_pipeline_yaml(tmp_path: Path) -> Path:
    content = """\
name: pipeline
description: A test pipeline
version: "1.0"
nodes:
  - id: validate
    kind: deterministic
    inputs: [raw]
    outputs: [clean]
  - id: score
    kind: agentic
    inputs: [clean]
    outputs: [result]
    output_schema:
      type: object
      properties:
        score:
          type: number
    contracts:
      - result is nonempty
edges:
  - from_node: validate
    to_node: score
    kind: data_flow
"""
    p = tmp_path / "pipeline.yaml"
    p.write_text(content)
    return p


class TestLoadGraph:
    def test_load_valid_yaml(self, valid_yaml: Path) -> None:
        graph = load_graph(valid_yaml)
        assert graph.name == "test_graph"
        assert len(graph.nodes) == 1
        assert graph.nodes[0].id == "step_one"
        assert graph.nodes[0].kind == NodeKind.DETERMINISTIC

    def test_load_pipeline(self, valid_pipeline_yaml: Path) -> None:
        graph = load_graph(valid_pipeline_yaml)
        assert graph.name == "pipeline"
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.edges[0].from_node == "validate"

    def test_file_not_found(self) -> None:
        with pytest.raises(LoadError, match="File not found"):
            load_graph("/nonexistent/path.yaml")

    def test_unsupported_extension(self, tmp_path: Path) -> None:
        p = tmp_path / "file.txt"
        p.write_text("name: test")
        with pytest.raises(LoadError, match="Unsupported file type"):
            load_graph(p)

    def test_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.yaml"
        p.write_text(":\n  - :\n    - [invalid")
        with pytest.raises(LoadError, match="Invalid YAML"):
            load_graph(p)

    def test_yaml_not_a_mapping(self, tmp_path: Path) -> None:
        p = tmp_path / "list.yaml"
        p.write_text("- item1\n- item2\n")
        with pytest.raises(LoadError, match="YAML root must be a mapping"):
            load_graph(p)

    def test_schema_validation_error(self, tmp_path: Path) -> None:
        p = tmp_path / "missing_fields.yaml"
        p.write_text("name: test\n")
        with pytest.raises(LoadError, match="Schema validation failed"):
            load_graph(p)

    def test_yml_extension_accepted(self, tmp_path: Path) -> None:
        content = """\
name: yml_test
nodes:
  - id: n1
    kind: deterministic
    inputs: []
    outputs: []
edges: []
"""
        p = tmp_path / "file.yml"
        p.write_text(content)
        graph = load_graph(p)
        assert graph.name == "yml_test"

    def test_load_with_string_path(self, valid_yaml: Path) -> None:
        graph = load_graph(str(valid_yaml))
        assert graph.name == "test_graph"
