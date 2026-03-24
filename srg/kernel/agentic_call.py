"""Issue 9 — Contract-enforced agentic call primitive."""
from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from srg.kernel.contracts import check_contracts
from srg.kernel.retry import should_retry
from srg.kernel.validation import validate_output_schema
from srg.models.evidence import EvidenceRecord
from srg.models.node import RetryPolicy


# ---- protocols --------------------------------------------------------


class LLMProvider(Protocol):
    """Minimal protocol for LLM backends."""

    def generate(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]: ...


# ---- spec / result dataclasses ----------------------------------------


@dataclass
class AgenticCallSpec:
    node_id: str
    prompt: str
    output_schema: dict[str, Any]
    contracts: list[str]
    retry_policy: RetryPolicy | None = None


@dataclass
class AgenticResult:
    outputs: dict[str, Any]
    evidence: list[EvidenceRecord] = field(default_factory=list)
    success: bool = True
    error: str | None = None


# ---- helpers -----------------------------------------------------------


def _hash_str(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---- core call ---------------------------------------------------------


def agentic_call(
    spec: AgenticCallSpec,
    llm_provider: LLMProvider,
    graph_name: str = "",
) -> AgenticResult:
    """Execute a contract-enforced agentic call with retry logic.

    Flow
    ----
    1. Call LLM with prompt + schema guidance
    2. Parse JSON response
    3. Validate against output_schema
    4. Check contracts
    5. On failure: build refinement prompt, retry per policy
    6. Emit EvidenceRecord per attempt
    7. Return AgenticResult
    """
    policy = spec.retry_policy or RetryPolicy()
    evidence: list[EvidenceRecord] = []
    prompt = spec.prompt
    last_error: str | None = None

    for attempt in range(1, policy.max_attempts + 1):
        t0 = time.monotonic()
        failure_type: str | None = None
        error_detail: str | None = None
        raw_output: dict[str, Any] = {}

        # --- 1. call LLM ---
        try:
            raw_output = llm_provider.generate(
                prompt=prompt,
                output_schema=spec.output_schema,
            )
        except Exception as exc:
            failure_type = "llm_error"
            error_detail = str(exc)

        duration_ms = (time.monotonic() - t0) * 1000.0

        # --- 2/3. validate schema ---
        if failure_type is None:
            vr = validate_output_schema(raw_output, spec.output_schema)
            if not vr.valid:
                failure_type = "schema_failure"
                error_detail = "; ".join(vr.errors)

        # --- 4. check contracts ---
        if failure_type is None:
            cr = check_contracts(spec.contracts, raw_output)
            if not cr.ok:
                failure_type = "contract_failure"
                error_detail = "; ".join(cr.violations)

        # --- 6. emit evidence ---
        status = "success" if failure_type is None else "failure"
        ev = EvidenceRecord(
            graph_name=graph_name,
            node_id=spec.node_id,
            attempt=attempt,
            status=status,
            timestamp=_now_iso(),
            validation_outcome=failure_type,
            duration_ms=round(duration_ms, 2),
            prompt_hash=_hash_str(prompt),
            output_hash=_hash_str(json.dumps(raw_output, sort_keys=True)),
            retry_reason=failure_type,
            contract_summary=error_detail,
        )
        evidence.append(ev)

        # --- success path ---
        if failure_type is None:
            return AgenticResult(
                outputs=raw_output,
                evidence=evidence,
                success=True,
            )

        # --- 5. retry? ---
        last_error = error_detail
        if should_retry(failure_type, policy, attempt):
            prompt = (
                f"{spec.prompt}\n\n"
                f"[Retry attempt {attempt + 1}] "
                f"Previous attempt failed: {error_detail}\n"
                f"Please fix the output and try again."
            )
        else:
            break

    return AgenticResult(
        outputs=raw_output,
        evidence=evidence,
        success=False,
        error=last_error,
    )


# ---- OllamaProvider ---------------------------------------------------


class OllamaProvider:
    """LLM provider using a local Ollama instance via urllib."""

    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(
        self,
        prompt: str,
        output_schema: dict[str, Any] | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """Call Ollama /api/generate and parse the JSON response."""
        full_prompt = prompt
        if output_schema is not None:
            schema_str = json.dumps(output_schema, indent=2)
            full_prompt = (
                f"{prompt}\n\n"
                f"You MUST respond with valid JSON matching this schema:\n"
                f"{schema_str}\n\n"
                f"Respond ONLY with the JSON object, no extra text."
            )

        payload = json.dumps({
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "format": "json",
        }).encode()

        timeout_s = (timeout_ms / 1000.0) if timeout_ms else 120.0

        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                body = json.loads(resp.read().decode())
        except (urllib.error.URLError, OSError) as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

        raw_text: str = body.get("response", "")

        try:
            parsed: dict[str, Any] = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Ollama returned non-JSON response: {raw_text!r}"
            ) from exc

        if not isinstance(parsed, dict):
            raise RuntimeError(
                f"Ollama returned non-object JSON: {type(parsed).__name__}"
            )

        return parsed
