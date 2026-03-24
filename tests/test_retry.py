"""Tests for Issue 8 — Retry policy."""
from __future__ import annotations

from srg.kernel.retry import should_retry
from srg.models.node import RetryPolicy


class TestShouldRetry:
    def test_retry_allowed(self) -> None:
        policy = RetryPolicy(max_attempts=3, retry_on=["schema_failure"])
        assert should_retry("schema_failure", policy, attempt=1) is True

    def test_retry_allowed_second_attempt(self) -> None:
        policy = RetryPolicy(max_attempts=3, retry_on=["schema_failure"])
        assert should_retry("schema_failure", policy, attempt=2) is True

    def test_retry_exhausted(self) -> None:
        policy = RetryPolicy(max_attempts=3, retry_on=["schema_failure"])
        assert should_retry("schema_failure", policy, attempt=3) is False

    def test_failure_type_not_in_policy(self) -> None:
        policy = RetryPolicy(max_attempts=3, retry_on=["schema_failure"])
        assert should_retry("contract_failure", policy, attempt=1) is False

    def test_default_policy(self) -> None:
        policy = RetryPolicy()
        assert should_retry("schema_failure", policy, attempt=1) is True
        assert should_retry("contract_failure", policy, attempt=1) is True
        assert should_retry("schema_failure", policy, attempt=2) is False

    def test_max_attempts_one(self) -> None:
        policy = RetryPolicy(max_attempts=1, retry_on=["schema_failure"])
        assert should_retry("schema_failure", policy, attempt=1) is False

    def test_unknown_failure_type(self) -> None:
        policy = RetryPolicy(max_attempts=3, retry_on=["schema_failure"])
        assert should_retry("llm_error", policy, attempt=1) is False
