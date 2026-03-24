from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from srg.models.graph import ReasoningGraph


class LoadError(Exception):
    """Raised when a YAML graph file cannot be loaded or parsed."""


def load_graph(path: str | Path) -> ReasoningGraph:
    """Load a YAML file and return a validated ReasoningGraph."""
    file_path = Path(path)

    if not file_path.exists():
        raise LoadError(f"File not found: {file_path}")

    if file_path.suffix not in (".yaml", ".yml"):
        raise LoadError(f"Unsupported file type: {file_path.suffix}")

    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except OSError as e:
        raise LoadError(f"Cannot read file: {e}") from e

    try:
        data: Any = yaml.safe_load(raw_text)
    except yaml.YAMLError as e:
        raise LoadError(f"Invalid YAML: {e}") from e

    if not isinstance(data, dict):
        raise LoadError("YAML root must be a mapping")

    try:
        graph = ReasoningGraph.model_validate(data)
    except ValidationError as e:
        raise LoadError(f"Schema validation failed: {e}") from e

    return graph
