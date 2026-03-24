"""Tests for Issue 9 — Agentic call primitive."""
from __future__ import annotations

from typing import Any

import pytest

from srg.kernel.agentic_call import (
    AgenticCallSpec,
    AgenticResult,
    LLMProvider,
    agentic_call,
)
from srg.models.node import RetryPolicy


# ---- Mock LLM provider ------------------------------------------------


class MockLLMProvider:
    """Mock LLM provider that returns a sequence of responses."""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = list(responses)
        self._call_count = 0
        self.prompts: list[str] = []

    def generate(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        self.prompts.append(prompt)
        idx = min(self._call_count, len(self._responses) - 1)
        self._call_count += 1
        return self._responses[idx]


class FailingLLMProvider:
    """Mock LLM provider that raises on generate."""

    def generate(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        raise RuntimeError("LLM connection failed")


# ---- Tests -------------------------------------------------------------


class TestAgenticCallSuccess:
    def test_success_on_first_attempt(self) -> None:
        provider = MockLLMProvider([{"score": 85, "explanation": "Good data"}])
        spec = AgenticCallSpec(
            node_id="score_node",
            prompt="Score this data",
            output_schema={
                "type": "object",
                "properties": {
                    "score": {"type": "number", "minimum": 0, "maximum": 100},
                    "explanation": {"type": "string"},
                },
                "required": ["score", "explanation"],
            },
            contracts=["score >= 0", "score <= 100", "explanation is nonempty"],
        )
        result = agentic_call(spec, provider, graph_name="test_graph")

        assert result.success is True
        assert result.outputs == {"score": 85, "explanation": "Good data"}
        assert result.error is None
        assert len(result.evidence) == 1
        assert result.evidence[0].attempt == 1
        assert result.evidence[0].status == "success"
        assert result.evidence[0].graph_name == "test_graph"
        assert result.evidence[0].node_id == "score_node"

    def test_evidence_has_timestamps(self) -> None:
        provider = MockLLMProvider([{"val": "ok"}])
        spec = AgenticCallSpec(
            node_id="n",
            prompt="test",
            output_schema={"type": "object"},
            contracts=["val is nonempty"],
        )
        result = agentic_call(spec, provider, graph_name="g")
        assert result.evidence[0].timestamp  # not empty
        # ISO 8601 format check
        assert "T" in result.evidence[0].timestamp

    def test_evidence_has_hashes(self) -> None:
        provider = MockLLMProvider([{"val": "ok"}])
        spec = AgenticCallSpec(
            node_id="n",
            prompt="test",
            output_schema={"type": "object"},
            contracts=["val is nonempty"],
        )
        result = agentic_call(spec, provider, graph_name="g")
        assert result.evidence[0].prompt_hash is not None
        assert result.evidence[0].output_hash is not None


class TestAgenticCallSchemaRetry:
    def test_retry_on_schema_failure(self) -> None:
        """First response has wrong type, second is correct."""
        provider = MockLLMProvider([
            {"score": "not a number"},  # bad type
            {"score": 50},  # correct
        ])
        spec = AgenticCallSpec(
            node_id="n",
            prompt="test",
            output_schema={
                "type": "object",
                "properties": {"score": {"type": "number"}},
                "required": ["score"],
            },
            contracts=["score >= 0"],
            retry_policy=RetryPolicy(max_attempts=3, retry_on=["schema_failure"]),
        )
        result = agentic_call(spec, provider, graph_name="g")
        assert result.success is True
        assert len(result.evidence) == 2
        assert result.evidence[0].status == "failure"
        assert result.evidence[0].validation_outcome == "schema_failure"
        assert result.evidence[1].status == "success"

    def test_schema_failure_exhausts_retries(self) -> None:
        provider = MockLLMProvider([
            {"score": "bad"},
            {"score": "still bad"},
        ])
        spec = AgenticCallSpec(
            node_id="n",
            prompt="test",
            output_schema={
                "type": "object",
                "properties": {"score": {"type": "number"}},
                "required": ["score"],
            },
            contracts=[],
            retry_policy=RetryPolicy(max_attempts=2, retry_on=["schema_failure"]),
        )
        result = agentic_call(spec, provider, graph_name="g")
        assert result.success is False
        assert len(result.evidence) == 2
        assert result.error is not None


class TestAgenticCallContractRetry:
    def test_retry_on_contract_failure(self) -> None:
        provider = MockLLMProvider([
            {"score": -10},  # fails contract
            {"score": 50},  # passes
        ])
        spec = AgenticCallSpec(
            node_id="n",
            prompt="test",
            output_schema={
                "type": "object",
                "properties": {"score": {"type": "number"}},
            },
            contracts=["score >= 0"],
            retry_policy=RetryPolicy(
                max_attempts=3,
                retry_on=["contract_failure"],
            ),
        )
        result = agentic_call(spec, provider, graph_name="g")
        assert result.success is True
        assert len(result.evidence) == 2
        assert result.evidence[0].validation_outcome == "contract_failure"

    def test_contract_failure_not_retried_if_not_in_policy(self) -> None:
        provider = MockLLMProvider([
            {"score": -10},
        ])
        spec = AgenticCallSpec(
            node_id="n",
            prompt="test",
            output_schema={
                "type": "object",
                "properties": {"score": {"type": "number"}},
            },
            contracts=["score >= 0"],
            retry_policy=RetryPolicy(
                max_attempts=3,
                retry_on=["schema_failure"],  # no contract_failure
            ),
        )
        result = agentic_call(spec, provider, graph_name="g")
        assert result.success is False
        assert len(result.evidence) == 1


class TestAgenticCallLLMError:
    def test_llm_error_no_retry(self) -> None:
        provider = FailingLLMProvider()
        spec = AgenticCallSpec(
            node_id="n",
            prompt="test",
            output_schema={"type": "object"},
            contracts=[],
            retry_policy=RetryPolicy(max_attempts=2, retry_on=["schema_failure"]),
        )
        result = agentic_call(spec, provider, graph_name="g")
        assert result.success is False
        assert result.evidence[0].validation_outcome == "llm_error"


class TestAgenticCallRefinementPrompt:
    def test_retry_prompt_includes_error_feedback(self) -> None:
        provider = MockLLMProvider([
            {"score": -10},  # contract fail
            {"score": 50},  # ok
        ])
        spec = AgenticCallSpec(
            node_id="n",
            prompt="Give a score",
            output_schema={
                "type": "object",
                "properties": {"score": {"type": "number"}},
            },
            contracts=["score >= 0"],
            retry_policy=RetryPolicy(max_attempts=3, retry_on=["contract_failure"]),
        )
        agentic_call(spec, provider, graph_name="g")
        assert len(provider.prompts) == 2
        assert "Retry attempt" in provider.prompts[1]
        assert "failed" in provider.prompts[1].lower()


class TestAgenticCallDefaultPolicy:
    def test_uses_default_retry_policy(self) -> None:
        """When no retry_policy is specified, default (max_attempts=2) is used."""
        provider = MockLLMProvider([
            {"score": "bad"},  # schema fail
            {"score": 50},  # ok
        ])
        spec = AgenticCallSpec(
            node_id="n",
            prompt="test",
            output_schema={
                "type": "object",
                "properties": {"score": {"type": "number"}},
            },
            contracts=[],
            # no retry_policy -- should default to RetryPolicy()
        )
        result = agentic_call(spec, provider, graph_name="g")
        assert result.success is True
        assert len(result.evidence) == 2
