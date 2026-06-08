"""Canonical replay governance approval-record contract.

Governance-only schema surface for approval/review metadata. This module does
not create waiver behavior, override behavior, workflow automation, replay
execution changes, or acceptance changes.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REPLAY_GOVERNANCE_APPROVAL_STATUS_APPROVED = "APPROVED"
REPLAY_GOVERNANCE_APPROVAL_STATUS_REJECTED = "REJECTED"
REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW = "PENDING_REVIEW"

ALLOWED_REPLAY_GOVERNANCE_APPROVAL_STATUSES: frozenset[str] = frozenset(
    {
        REPLAY_GOVERNANCE_APPROVAL_STATUS_APPROVED,
        REPLAY_GOVERNANCE_APPROVAL_STATUS_REJECTED,
        REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
    }
)

REQUIRED_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS: frozenset[str] = frozenset(
    {
        "approval_status",
        "decision_reference",
        "approval_reason",
        "reviewed_by",
        "review_date",
        "approval_source",
    }
)

OPTIONAL_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS: frozenset[str] = frozenset({"notes"})

ALLOWED_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS: frozenset[str] = (
    REQUIRED_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS
    | OPTIONAL_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS
)


def is_valid_approval_status(value: Any) -> bool:
    """Return whether ``value`` is a canonical governance approval status."""
    return value in ALLOWED_REPLAY_GOVERNANCE_APPROVAL_STATUSES


def approval_record_shape_errors(record: Mapping[str, Any] | None) -> list[str]:
    """Validate only approval metadata shape and approval status vocabulary."""
    if not isinstance(record, Mapping):
        return ["approval record must be a mapping"]

    errors: list[str] = []
    for field in sorted(REQUIRED_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS):
        if field not in record:
            errors.append(f"missing approval field: {field}")

    status = record.get("approval_status")
    if not is_valid_approval_status(status):
        errors.append(f"invalid approval_status: {status!r}")

    for field in (
        "decision_reference",
        "approval_reason",
        "reviewed_by",
        "review_date",
        "approval_source",
    ):
        value = record.get(field)
        if field in record and (not isinstance(value, str) or not value.strip()):
            errors.append(f"{field} must be a non-empty string")

    notes = record.get("notes")
    if "notes" in record and notes is not None and not isinstance(notes, str):
        errors.append("notes must be a string when present")

    unknown_fields = sorted(set(record) - ALLOWED_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS)
    for field in unknown_fields:
        errors.append(f"unknown approval field: {field}")

    return errors
