"""Issue 8 — Retry policy helpers."""
from __future__ import annotations

from srg.models.node import RetryPolicy


def should_retry(
    failure_type: str,
    policy: RetryPolicy,
    attempt: int,
) -> bool:
    """Return ``True`` if the current *attempt* should be retried.

    Parameters
    ----------
    failure_type:
        A failure category string, e.g. ``"schema_failure"`` or
        ``"contract_failure"``.
    policy:
        The retry policy governing this node.
    attempt:
        The 1-based attempt number that just failed.
    """
    if attempt >= policy.max_attempts:
        return False
    return failure_type in policy.retry_on
