"""Shared replay governance record fixtures for contract consumers."""
from __future__ import annotations

from typing import Any

from tests.replay_governance_approval_contract import (
    REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
)
from tests.replay_governance_contract import (
    REPLAY_GOVERNANCE_DECISION_ACCEPTED,
    REPLAY_GOVERNANCE_DECISION_BLOCKED,
)

ACCEPTED_DECISION_REFERENCE = "exact_drift:replay_drift_unclassified:replay_drift:low"
BLOCKED_DECISION_REFERENCE = "structural_drift:speaker_drift:speaker:critical"
UNKNOWN_DECISION_REFERENCE = "structural_drift:speaker_drift:speaker:medium"


def governance_decision_record_fixture(**overrides: Any) -> dict[str, Any]:
    """Return a valid replay governance decision record."""
    record: dict[str, Any] = {
        "drift_bucket": "structural_drift",
        "owner_bucket": "speaker_drift",
        "category": "speaker",
        "severity": "critical",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_BLOCKED,
        "governance_reason": "Existing protected speaker invariant mismatch blocks when asserted.",
        "policy_source": "docs/testing/protected_replay_manifest.md",
    }
    record.update(overrides)
    return record


def approval_record_fixture(**overrides: Any) -> dict[str, Any]:
    """Return a valid replay governance approval record."""
    record: dict[str, Any] = {
        "approval_status": REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
        "decision_reference": BLOCKED_DECISION_REFERENCE,
        "approval_reason": "Protected speaker invariant review is pending.",
        "reviewed_by": "governance-review",
        "review_date": "2026-06-08",
        "approval_source": "docs/testing/replay_governance_registry.md",
    }
    record.update(overrides)
    return record


def traceability_registry_fixture() -> tuple[dict[str, Any], ...]:
    """Return a small decision registry for approval traceability tests."""
    return (
        governance_decision_record_fixture(
            drift_bucket="exact_drift",
            owner_bucket="replay_drift_unclassified",
            category="replay_drift",
            severity="low",
            governance_decision=REPLAY_GOVERNANCE_DECISION_ACCEPTED,
            governance_reason="Fixture accepted decision.",
            policy_source="fixture",
        ),
        governance_decision_record_fixture(
            governance_reason="Fixture blocked decision.",
            policy_source="fixture",
        ),
    )
