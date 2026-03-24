"""Tests for Issue 7 — Deterministic registry."""
from __future__ import annotations

from typing import Any

import pytest

from srg.runtime.deterministic_registry import DeterministicRegistry, RegistryError


class TestDeterministicRegistry:
    def test_register_and_get(self) -> None:
        reg = DeterministicRegistry()

        def my_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {"y": state["x"] * 2}

        reg.register("my_fn", my_fn)
        assert reg.get("my_fn") is my_fn

    def test_get_missing_raises(self) -> None:
        reg = DeterministicRegistry()
        with pytest.raises(RegistryError, match="No function registered"):
            reg.get("nonexistent")

    def test_has_registered(self) -> None:
        reg = DeterministicRegistry()
        reg.register("fn", lambda s: s)
        assert reg.has("fn") is True
        assert reg.has("missing") is False

    def test_list_functions_sorted(self) -> None:
        reg = DeterministicRegistry()
        reg.register("zebra", lambda s: s)
        reg.register("alpha", lambda s: s)
        reg.register("middle", lambda s: s)
        assert reg.list_functions() == ["alpha", "middle", "zebra"]

    def test_list_functions_empty(self) -> None:
        reg = DeterministicRegistry()
        assert reg.list_functions() == []

    def test_decorator_pattern(self) -> None:
        reg = DeterministicRegistry()

        @reg.register("decorated")
        def my_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {"out": 42}

        assert reg.has("decorated")
        assert reg.get("decorated") is my_fn

    def test_decorator_returns_original_function(self) -> None:
        reg = DeterministicRegistry()

        @reg.register("fn")
        def my_fn(state: dict[str, Any]) -> dict[str, Any]:
            return {"out": 1}

        # The decorator should return the original function
        assert my_fn({"x": 1}) == {"out": 1}

    def test_overwrite_registration(self) -> None:
        reg = DeterministicRegistry()

        def fn1(state: dict[str, Any]) -> dict[str, Any]:
            return {"v": 1}

        def fn2(state: dict[str, Any]) -> dict[str, Any]:
            return {"v": 2}

        reg.register("fn", fn1)
        reg.register("fn", fn2)
        assert reg.get("fn") is fn2

    def test_callable_execution(self) -> None:
        reg = DeterministicRegistry()

        def double(state: dict[str, Any]) -> dict[str, Any]:
            return {"result": state["x"] * 2}

        reg.register("double", double)
        fn = reg.get("double")
        assert fn({"x": 5}) == {"result": 10}
