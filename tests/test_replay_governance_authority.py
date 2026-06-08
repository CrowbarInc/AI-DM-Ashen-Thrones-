from tests.replay_governance_approval_contract import (
    ALLOWED_REPLAY_GOVERNANCE_APPROVAL_STATUSES,
    REPLAY_GOVERNANCE_APPROVAL_STATUS_APPROVED,
    REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
    REPLAY_GOVERNANCE_APPROVAL_STATUS_REJECTED,
    approval_record_shape_errors,
)
from tests.replay_governance_contract import (
    ALLOWED_REPLAY_GOVERNANCE_DECISIONS,
    REPLAY_GOVERNANCE_DECISION_ACCEPTED,
    REPLAY_GOVERNANCE_DECISION_BLOCKED,
    REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
    governance_record_shape_errors,
)
from tests.replay_governance_registry import replay_governance_registry
from tests.replay_governance_traceability_contract import (
    REPLAY_GOVERNANCE_DECISION_REFERENCE_FIELDS,
    REPLAY_GOVERNANCE_DECISION_REFERENCE_SEPARATOR,
    governance_decision_reference,
)


def _approval_record(decision_reference: str) -> dict[str, str]:
    return {
        "approval_status": REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
        "decision_reference": decision_reference,
        "approval_reason": "Authority synchronization fixture.",
        "reviewed_by": "governance-review",
        "review_date": "2026-06-08",
        "approval_source": "tests/test_replay_governance_authority.py",
    }


def test_level_1_governance_decision_vocabulary_is_canonical() -> None:
    assert ALLOWED_REPLAY_GOVERNANCE_DECISIONS == frozenset(
        {
            REPLAY_GOVERNANCE_DECISION_ACCEPTED,
            REPLAY_GOVERNANCE_DECISION_BLOCKED,
            REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
        }
    )
    assert ALLOWED_REPLAY_GOVERNANCE_DECISIONS == frozenset(
        {
            "ACCEPTED",
            "BLOCKED",
            "REVIEW_REQUIRED",
        }
    )


def test_level_2_registry_records_remain_level_1_contract_valid() -> None:
    registry = replay_governance_registry()

    assert registry
    for record in registry:
        assert governance_record_shape_errors(record) == []
        assert record["governance_decision"] in ALLOWED_REPLAY_GOVERNANCE_DECISIONS


def test_level_3_approval_status_vocabulary_is_canonical() -> None:
    assert ALLOWED_REPLAY_GOVERNANCE_APPROVAL_STATUSES == frozenset(
        {
            REPLAY_GOVERNANCE_APPROVAL_STATUS_APPROVED,
            REPLAY_GOVERNANCE_APPROVAL_STATUS_REJECTED,
            REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
        }
    )
    assert ALLOWED_REPLAY_GOVERNANCE_APPROVAL_STATUSES == frozenset(
        {
            "APPROVED",
            "REJECTED",
            "PENDING_REVIEW",
        }
    )


def test_level_3_approval_records_remain_shape_valid_for_level_2_references() -> None:
    for record in replay_governance_registry():
        approval = _approval_record(governance_decision_reference(record))
        assert approval_record_shape_errors(approval) == []


def test_level_4_traceability_identifier_format_is_canonical() -> None:
    assert REPLAY_GOVERNANCE_DECISION_REFERENCE_SEPARATOR == ":"
    assert REPLAY_GOVERNANCE_DECISION_REFERENCE_FIELDS == (
        "drift_bucket",
        "owner_bucket",
        "category",
        "severity",
    )


def test_level_4_traceability_identifiers_are_unique_for_registry() -> None:
    references = [governance_decision_reference(record) for record in replay_governance_registry()]

    assert references
    assert len(references) == len(set(references))
    assert all(reference.count(":") == 3 for reference in references)
