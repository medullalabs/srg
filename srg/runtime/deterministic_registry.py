"""Issue 7 — Deterministic function registry."""
from __future__ import annotations

from typing import Any, Callable, overload


class RegistryError(Exception):
    """Raised when a registry lookup fails."""


class DeterministicRegistry:
    """Maps function_ref strings to Python callables."""

    def __init__(self) -> None:
        self._functions: dict[str, Callable[..., Any]] = {}

    @overload
    def register(self, name: str, fn: Callable[..., Any]) -> None: ...

    @overload
    def register(self, name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...

    def register(
        self,
        name: str,
        fn: Callable[..., Any] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]] | None:
        """Register a callable under *name*.

        Can be used directly::

            registry.register("my_fn", my_fn)

        Or as a decorator::

            @registry.register("my_fn")
            def my_fn(state):
                ...
        """
        if fn is not None:
            self._functions[name] = fn
            return None

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self._functions[name] = func
            return func

        return decorator

    def get(self, name: str) -> Callable[..., Any]:
        """Return the callable for *name*, or raise ``RegistryError``."""
        try:
            return self._functions[name]
        except KeyError:
            raise RegistryError(
                f"No function registered for '{name}'"
            ) from None

    def has(self, name: str) -> bool:
        """Return ``True`` if *name* is registered."""
        return name in self._functions

    def list_functions(self) -> list[str]:
        """Return sorted list of registered function names."""
        return sorted(self._functions.keys())
