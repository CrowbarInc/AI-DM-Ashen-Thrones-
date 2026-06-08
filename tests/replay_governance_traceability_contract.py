"""Traceability contract between replay governance decisions and approvals.

Governance-only validation surface. This module links approval metadata to the
static governance decision registry without adding waiver behavior, override
behavior, workflow automation, replay execution changes, or acceptance changes.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from tests.replay_governance_approval_contract import (
    REPLAY_GOVERNANCE_APPROVAL_STATUS_APPROVED,
    REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
    approval_record_shape_errors,
)
from tests.replay_governance_registry import (
    governance_record_key,
    replay_governance_registry,
)

REPLAY_GOVERNANCE_DECISION_REFERENCE_SEPARATOR = ":"
REPLAY_GOVERNANCE_DECISION_REFERENCE_FIELDS: tuple[str, ...] = (
    "drift_bucket",
    "owner_bucket",
    "category",
    "severity",
)


def governance_decision_reference(record: Mapping[str, Any]) -> str:
    """Return the canonical decision reference for a governance registry record."""
    return REPLAY_GOVERNANCE_DECISION_REFERENCE_SEPARATOR.join(governance_record_key(record))


def governance_decision_reference_set(
    registry: Sequence[Mapping[str, Any]] | None = None,
) -> frozenset[str]:
    """Return all canonical decision references for ``registry``."""
    records = replay_governance_registry() if registry is None else registry
    return frozenset(governance_decision_reference(record) for record in records)


def is_valid_governance_decision_reference(
    decision_reference: Any,
    *,
    registry: Sequence[Mapping[str, Any]] | None = None,
) -> bool:
    """Return whether ``decision_reference`` resolves to a registry decision."""
    if not isinstance(decision_reference, str) or not decision_reference.strip():
        return False
    return decision_reference in governance_decision_reference_set(registry)


def approval_references_unknown_decision(
    approval_record: Mapping[str, Any] | None,
    *,
    registry: Sequence[Mapping[str, Any]] | None = None,
) -> bool:
    """Return whether an approval record has a valid shape but unknown decision reference."""
    if approval_record_shape_errors(approval_record):
        return False
    assert approval_record is not None
    return not is_valid_governance_decision_reference(
        approval_record.get("decision_reference"),
        registry=registry,
    )


def replay_governance_traceability_audit(
    approval_records: Sequence[Mapping[str, Any]] | None,
    *,
    registry: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build an audit-only summary of approval-to-decision traceability."""
    decision_refs = governance_decision_reference_set(registry)
    approvals = [record for record in (approval_records or ()) if isinstance(record, Mapping)]

    approved_refs: set[str] = set()
    pending_refs: set[str] = set()
    orphan_approvals: list[dict[str, Any]] = []
    invalid_approvals: list[dict[str, Any]] = []

    for index, approval in enumerate(approvals):
        errors = approval_record_shape_errors(approval)
        if errors:
            invalid_approvals.append(
                {
                    "index": index,
                    "decision_reference": approval.get("decision_reference"),
                    "errors": errors,
                }
            )
            continue

        ref = str(approval.get("decision_reference") or "")
        if ref not in decision_refs:
            orphan_approvals.append(
                {
                    "index": index,
                    "decision_reference": ref,
                    "approval_status": approval.get("approval_status"),
                }
            )
            continue

        status = approval.get("approval_status")
        if status == REPLAY_GOVERNANCE_APPROVAL_STATUS_APPROVED:
            approved_refs.add(ref)
        elif status == REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW:
            pending_refs.add(ref)

    return {
        "governed_decisions": sorted(decision_refs),
        "approved_decisions": sorted(approved_refs),
        "pending_decisions": sorted(pending_refs),
        "orphan_approvals": orphan_approvals,
        "invalid_approvals": invalid_approvals,
    }
