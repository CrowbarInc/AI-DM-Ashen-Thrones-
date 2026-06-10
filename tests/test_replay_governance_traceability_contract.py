from tests.replay_governance_approval_contract import (
    REPLAY_GOVERNANCE_APPROVAL_STATUS_APPROVED,
    REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
    REPLAY_GOVERNANCE_APPROVAL_STATUS_REJECTED,
)
from tests.helpers.replay_governance_fixtures import (
    ACCEPTED_DECISION_REFERENCE,
    BLOCKED_DECISION_REFERENCE,
    UNKNOWN_DECISION_REFERENCE,
    approval_record_fixture,
    traceability_registry_fixture,
)
from tests.replay_governance_registry import replay_governance_registry
from tests.replay_governance_traceability_contract import (
    REPLAY_GOVERNANCE_DECISION_REFERENCE_FIELDS,
    REPLAY_GOVERNANCE_DECISION_REFERENCE_SEPARATOR,
    approval_references_unknown_decision,
    governance_decision_reference,
    governance_decision_reference_set,
    is_valid_governance_decision_reference,
    replay_governance_traceability_audit,
)


def test_decision_reference_format_constants_are_contract_locked() -> None:
    assert REPLAY_GOVERNANCE_DECISION_REFERENCE_SEPARATOR == ":"
    assert REPLAY_GOVERNANCE_DECISION_REFERENCE_FIELDS == (
        "drift_bucket",
        "owner_bucket",
        "category",
        "severity",
    )


def test_governance_decision_reference_uses_canonical_key_fields() -> None:
    record = traceability_registry_fixture()[1]

    assert governance_decision_reference(record) == BLOCKED_DECISION_REFERENCE


def test_every_registry_record_has_unique_stable_identifier() -> None:
    refs = [governance_decision_reference(record) for record in replay_governance_registry()]

    assert refs
    assert len(refs) == len(set(refs))
    assert refs == [governance_decision_reference(record) for record in replay_governance_registry()]


def test_governance_decision_reference_set_is_deterministic() -> None:
    first = governance_decision_reference_set(traceability_registry_fixture())
    second = governance_decision_reference_set(traceability_registry_fixture())

    assert first == second == frozenset(
        {
            ACCEPTED_DECISION_REFERENCE,
            BLOCKED_DECISION_REFERENCE,
        }
    )


def test_is_valid_governance_decision_reference_resolves_known_registry_reference() -> None:
    assert is_valid_governance_decision_reference(
        BLOCKED_DECISION_REFERENCE,
        registry=traceability_registry_fixture(),
    )
    assert not is_valid_governance_decision_reference(
        UNKNOWN_DECISION_REFERENCE,
        registry=traceability_registry_fixture(),
    )
    assert not is_valid_governance_decision_reference("", registry=traceability_registry_fixture())
    assert not is_valid_governance_decision_reference(None, registry=traceability_registry_fixture())


def test_approval_references_unknown_decision_detects_orphan_valid_approval() -> None:
    assert approval_references_unknown_decision(
        approval_record_fixture(
            decision_reference=UNKNOWN_DECISION_REFERENCE,
            approval_status=REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
        ),
        registry=traceability_registry_fixture(),
    )
    assert not approval_references_unknown_decision(
        approval_record_fixture(
            decision_reference=BLOCKED_DECISION_REFERENCE,
            approval_status=REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
        ),
        registry=traceability_registry_fixture(),
    )


def test_approval_references_unknown_decision_ignores_invalid_approval_shape() -> None:
    assert not approval_references_unknown_decision(
        {"approval_status": "PENDING_REVIEW"},
        registry=traceability_registry_fixture(),
    )


def test_traceability_audit_reports_approved_pending_orphan_and_invalid_records() -> None:
    approvals = [
        approval_record_fixture(
            decision_reference=ACCEPTED_DECISION_REFERENCE,
            approval_status=REPLAY_GOVERNANCE_APPROVAL_STATUS_APPROVED,
        ),
        approval_record_fixture(
            decision_reference=BLOCKED_DECISION_REFERENCE,
            approval_status=REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
        ),
        approval_record_fixture(
            decision_reference=UNKNOWN_DECISION_REFERENCE,
            approval_status=REPLAY_GOVERNANCE_APPROVAL_STATUS_REJECTED,
        ),
        {"approval_status": "APPROVED"},
    ]

    audit = replay_governance_traceability_audit(approvals, registry=traceability_registry_fixture())

    assert audit == {
        "governed_decisions": [
            ACCEPTED_DECISION_REFERENCE,
            BLOCKED_DECISION_REFERENCE,
        ],
        "approved_decisions": [ACCEPTED_DECISION_REFERENCE],
        "pending_decisions": [BLOCKED_DECISION_REFERENCE],
        "orphan_approvals": [
            {
                "index": 2,
                "decision_reference": UNKNOWN_DECISION_REFERENCE,
                "approval_status": "REJECTED",
            }
        ],
        "invalid_approvals": [
            {
                "index": 3,
                "decision_reference": None,
                "errors": [
                    "missing approval field: approval_reason",
                    "missing approval field: approval_source",
                    "missing approval field: decision_reference",
                    "missing approval field: review_date",
                    "missing approval field: reviewed_by",
                ],
            }
        ],
    }


def test_traceability_audit_empty_input_is_deterministic() -> None:
    audit = replay_governance_traceability_audit([], registry=traceability_registry_fixture())

    assert audit == {
        "governed_decisions": [
            ACCEPTED_DECISION_REFERENCE,
            BLOCKED_DECISION_REFERENCE,
        ],
        "approved_decisions": [],
        "pending_decisions": [],
        "orphan_approvals": [],
        "invalid_approvals": [],
    }
