"""Canonical replay governance decision contract.

Governance-only schema surface for replay drift decision records. This module
does not import replay runners, classifiers, dashboards, scorecards, or runtime
game code, and it does not decide replay acceptance.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REPLAY_GOVERNANCE_DECISION_ACCEPTED = "ACCEPTED"
REPLAY_GOVERNANCE_DECISION_BLOCKED = "BLOCKED"
REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED = "REVIEW_REQUIRED"

ALLOWED_REPLAY_GOVERNANCE_DECISIONS: frozenset[str] = frozenset(
    {
        REPLAY_GOVERNANCE_DECISION_ACCEPTED,
        REPLAY_GOVERNANCE_DECISION_BLOCKED,
        REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
    }
)

REQUIRED_REPLAY_GOVERNANCE_RECORD_FIELDS: frozenset[str] = frozenset(
    {
        "drift_bucket",
        "owner_bucket",
        "category",
        "severity",
        "governance_decision",
        "governance_reason",
        "policy_source",
    }
)


def is_valid_governance_decision(value: Any) -> bool:
    """Return whether ``value`` is one of the canonical governance decisions."""
    return value in ALLOWED_REPLAY_GOVERNANCE_DECISIONS


def governance_record_shape_errors(record: Mapping[str, Any] | None) -> list[str]:
    """Validate only the governance record shape and decision vocabulary.

    This helper intentionally does not validate drift buckets, owner buckets,
    classifier categories, severities, policy semantics, or acceptance outcomes.
    Those remain owned by their existing contracts and policy documents.
    """
    if not isinstance(record, Mapping):
        return ["governance record must be a mapping"]

    errors: list[str] = []
    for field in sorted(REQUIRED_REPLAY_GOVERNANCE_RECORD_FIELDS):
        if field not in record:
            errors.append(f"missing governance field: {field}")

    decision = record.get("governance_decision")
    if not is_valid_governance_decision(decision):
        errors.append(f"invalid governance_decision: {decision!r}")

    for field in ("governance_reason", "policy_source"):
        value = record.get(field)
        if field in record and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{field} must be a non-empty string")

    return errors
