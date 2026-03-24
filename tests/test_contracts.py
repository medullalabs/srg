"""Tests for Issue 8 — Contract checking."""
from __future__ import annotations

from srg.kernel.contracts import ContractResult, check_contracts


class TestRangeContract:
    def test_in_range_passes(self) -> None:
        result = check_contracts(["score in 0..100"], {"score": 50})
        assert result.ok
        assert result.passed == ["score in 0..100"]
        assert result.violations == []

    def test_in_range_boundary_low(self) -> None:
        result = check_contracts(["score in 0..100"], {"score": 0})
        assert result.ok

    def test_in_range_boundary_high(self) -> None:
        result = check_contracts(["score in 0..100"], {"score": 100})
        assert result.ok

    def test_below_range_fails(self) -> None:
        result = check_contracts(["score in 0..100"], {"score": -1})
        assert not result.ok
        assert len(result.violations) == 1

    def test_above_range_fails(self) -> None:
        result = check_contracts(["score in 0..100"], {"score": 101})
        assert not result.ok

    def test_range_missing_field(self) -> None:
        result = check_contracts(["score in 0..100"], {})
        assert not result.ok
        assert "not found" in result.violations[0]

    def test_range_non_numeric(self) -> None:
        result = check_contracts(["score in 0..100"], {"score": "fifty"})
        assert not result.ok
        assert "not numeric" in result.violations[0]

    def test_negative_range(self) -> None:
        result = check_contracts(["temp in -50..50"], {"temp": -25})
        assert result.ok

    def test_float_range(self) -> None:
        result = check_contracts(["ratio in 0.0..1.0"], {"ratio": 0.5})
        assert result.ok


class TestNonemptyContract:
    def test_nonempty_string_passes(self) -> None:
        result = check_contracts(["name is nonempty"], {"name": "Alice"})
        assert result.ok

    def test_empty_string_fails(self) -> None:
        result = check_contracts(["name is nonempty"], {"name": ""})
        assert not result.ok

    def test_nonempty_list_passes(self) -> None:
        result = check_contracts(["items is nonempty"], {"items": [1, 2]})
        assert result.ok

    def test_empty_list_fails(self) -> None:
        result = check_contracts(["items is nonempty"], {"items": []})
        assert not result.ok

    def test_empty_dict_fails(self) -> None:
        result = check_contracts(["data is nonempty"], {"data": {}})
        assert not result.ok

    def test_none_fails(self) -> None:
        result = check_contracts(["val is nonempty"], {"val": None})
        assert not result.ok

    def test_missing_field(self) -> None:
        result = check_contracts(["val is nonempty"], {})
        assert not result.ok

    def test_number_passes(self) -> None:
        """A non-None, non-empty value should pass nonempty."""
        result = check_contracts(["val is nonempty"], {"val": 42})
        assert result.ok


class TestExistsContract:
    def test_field_exists_passes(self) -> None:
        result = check_contracts(["field exists"], {"field": "anything"})
        assert result.ok

    def test_field_missing_fails(self) -> None:
        result = check_contracts(["field exists"], {})
        assert not result.ok

    def test_field_exists_none_passes(self) -> None:
        """Exists only checks key presence, not value."""
        result = check_contracts(["field exists"], {"field": None})
        assert result.ok


class TestComparisonContract:
    def test_gte_passes(self) -> None:
        result = check_contracts(["score >= 0"], {"score": 0})
        assert result.ok

    def test_gte_fails(self) -> None:
        result = check_contracts(["score >= 0"], {"score": -1})
        assert not result.ok

    def test_lte_passes(self) -> None:
        result = check_contracts(["score <= 100"], {"score": 100})
        assert result.ok

    def test_lte_fails(self) -> None:
        result = check_contracts(["score <= 100"], {"score": 101})
        assert not result.ok

    def test_gt_passes(self) -> None:
        result = check_contracts(["x > 0"], {"x": 1})
        assert result.ok

    def test_gt_fails_on_equal(self) -> None:
        result = check_contracts(["x > 0"], {"x": 0})
        assert not result.ok

    def test_lt_passes(self) -> None:
        result = check_contracts(["x < 10"], {"x": 9})
        assert result.ok

    def test_eq_passes(self) -> None:
        result = check_contracts(["x == 5"], {"x": 5})
        assert result.ok

    def test_eq_fails(self) -> None:
        result = check_contracts(["x == 5"], {"x": 6})
        assert not result.ok

    def test_ne_passes(self) -> None:
        result = check_contracts(["x != 0"], {"x": 1})
        assert result.ok

    def test_ne_fails(self) -> None:
        result = check_contracts(["x != 0"], {"x": 0})
        assert not result.ok

    def test_comparison_missing_field(self) -> None:
        result = check_contracts(["x >= 0"], {})
        assert not result.ok

    def test_comparison_non_numeric(self) -> None:
        result = check_contracts(["x >= 0"], {"x": "abc"})
        assert not result.ok


class TestMultipleContracts:
    def test_all_pass(self) -> None:
        contracts = ["score >= 0", "score <= 100", "name is nonempty"]
        values = {"score": 50, "name": "test"}
        result = check_contracts(contracts, values)
        assert result.ok
        assert len(result.passed) == 3

    def test_mixed_pass_fail(self) -> None:
        contracts = ["score >= 0", "score <= 100", "name is nonempty"]
        values = {"score": 150, "name": ""}
        result = check_contracts(contracts, values)
        assert not result.ok
        assert len(result.passed) == 1  # score >= 0
        assert len(result.violations) == 2

    def test_empty_contracts(self) -> None:
        result = check_contracts([], {"any": "value"})
        assert result.ok
        assert result.passed == []


class TestUnsupportedContract:
    def test_unsupported_pattern(self) -> None:
        result = check_contracts(["something weird"], {"x": 1})
        assert not result.ok
        assert "unsupported" in result.violations[0]


class TestContractResultModel:
    def test_ok_property(self) -> None:
        assert ContractResult(passed=["a"], violations=[]).ok is True
        assert ContractResult(passed=[], violations=["b"]).ok is False
