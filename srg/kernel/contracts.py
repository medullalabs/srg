"""Issue 8 — Contract checking for node outputs."""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field


class ContractResult(BaseModel):
    """Result of checking a set of contracts against values."""

    passed: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0


# ---- contract patterns -----------------------------------------------

_RANGE_RE = re.compile(
    r"^(\w+)\s+in\s+(-?[\d.]+)\.\.(-?[\d.]+)$"
)
_NONEMPTY_RE = re.compile(r"^(\w+)\s+is\s+nonempty$")
_EXISTS_RE = re.compile(r"^(\w+)\s+exists$")
_CMP_RE = re.compile(
    r"^(\w+)\s*(>=|<=|>|<|==|!=)\s*(-?[\d.]+)$"
)


def _check_one(contract: str, values: dict[str, Any]) -> str | None:
    """Return a violation message, or ``None`` if the contract passes."""

    # field in min..max
    m = _RANGE_RE.match(contract)
    if m:
        field, lo, hi = m.group(1), float(m.group(2)), float(m.group(3))
        if field not in values:
            return f"Contract '{contract}': field '{field}' not found"
        val = values[field]
        if not isinstance(val, (int, float)):
            return f"Contract '{contract}': '{field}' is not numeric"
        if not (lo <= val <= hi):
            return (
                f"Contract '{contract}': {field}={val} "
                f"not in {lo}..{hi}"
            )
        return None

    # field is nonempty
    m = _NONEMPTY_RE.match(contract)
    if m:
        field = m.group(1)
        if field not in values:
            return f"Contract '{contract}': field '{field}' not found"
        val = values[field]
        if isinstance(val, str) and len(val) == 0:
            return f"Contract '{contract}': '{field}' is empty string"
        if isinstance(val, (list, dict)) and len(val) == 0:
            return f"Contract '{contract}': '{field}' is empty"
        if val is None:
            return f"Contract '{contract}': '{field}' is None"
        return None

    # field exists
    m = _EXISTS_RE.match(contract)
    if m:
        field = m.group(1)
        if field not in values:
            return f"Contract '{contract}': field '{field}' not found"
        return None

    # field >= / <= / > / < / == / != number
    m = _CMP_RE.match(contract)
    if m:
        field, op, rhs_str = m.group(1), m.group(2), m.group(3)
        rhs = float(rhs_str)
        if field not in values:
            return f"Contract '{contract}': field '{field}' not found"
        val = values[field]
        if not isinstance(val, (int, float)):
            return f"Contract '{contract}': '{field}' is not numeric"
        ops: dict[str, bool] = {
            ">=": val >= rhs,
            "<=": val <= rhs,
            ">": val > rhs,
            "<": val < rhs,
            "==": val == rhs,
            "!=": val != rhs,
        }
        if not ops[op]:
            return (
                f"Contract '{contract}': {field}={val} "
                f"does not satisfy {op} {rhs}"
            )
        return None

    return f"Contract '{contract}': unsupported contract pattern"


def check_contracts(
    contracts: list[str],
    values: dict[str, Any],
) -> ContractResult:
    """Check all *contracts* against *values* and return a ``ContractResult``."""
    passed: list[str] = []
    violations: list[str] = []

    for contract in contracts:
        violation = _check_one(contract, values)
        if violation is None:
            passed.append(contract)
        else:
            violations.append(violation)

    return ContractResult(passed=passed, violations=violations)
