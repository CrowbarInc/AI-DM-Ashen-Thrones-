from tests.replay_governance_approval_contract import (
    REPLAY_GOVERNANCE_APPROVAL_STATUS_APPROVED,
    REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
    REPLAY_GOVERNANCE_APPROVAL_STATUS_REJECTED,
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


def _approval_record(decision_reference: str, approval_status: str) -> dict[str, str]:
    return {
        "approval_status": approval_status,
        "decision_reference": decision_reference,
        "approval_reason": "Traceability fixture.",
        "reviewed_by": "governance-review",
        "review_date": "2026-06-08",
        "approval_source": "tests/test_replay_governance_traceability_contract.py",
    }


def _small_registry() -> tuple[dict[str, str], ...]:
    return (
        {
            "drift_bucket": "exact_drift",
            "owner_bucket": "replay_drift_unclassified",
            "category": "replay_drift",
            "severity": "low",
            "governance_decision": "ACCEPTED",
            "governance_reason": "Fixture accepted decision.",
            "policy_source": "fixture",
        },
        {
            "drift_bucket": "structural_drift",
            "owner_bucket": "speaker_drift",
            "category": "speaker",
            "severity": "critical",
            "governance_decision": "BLOCKED",
            "governance_reason": "Fixture blocked decision.",
            "policy_source": "fixture",
        },
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
    record = _small_registry()[1]

    assert governance_decision_reference(record) == "structural_drift:speaker_drift:speaker:critical"


def test_every_registry_record_has_unique_stable_identifier() -> None:
    refs = [governance_decision_reference(record) for record in replay_governance_registry()]

    assert refs
    assert len(refs) == len(set(refs))
    assert refs == [governance_decision_reference(record) for record in replay_governance_registry()]


def test_governance_decision_reference_set_is_deterministic() -> None:
    first = governance_decision_reference_set(_small_registry())
    second = governance_decision_reference_set(_small_registry())

    assert first == second == frozenset(
        {
            "exact_drift:replay_drift_unclassified:replay_drift:low",
            "structural_drift:speaker_drift:speaker:critical",
        }
    )


def test_is_valid_governance_decision_reference_resolves_known_registry_reference() -> None:
    assert is_valid_governance_decision_reference(
        "structural_drift:speaker_drift:speaker:critical",
        registry=_small_registry(),
    )
    assert not is_valid_governance_decision_reference(
        "structural_drift:speaker_drift:speaker:medium",
        registry=_small_registry(),
    )
    assert not is_valid_governance_decision_reference("", registry=_small_registry())
    assert not is_valid_governance_decision_reference(None, registry=_small_registry())


def test_approval_references_unknown_decision_detects_orphan_valid_approval() -> None:
    assert approval_references_unknown_decision(
        _approval_record(
            "structural_drift:speaker_drift:speaker:medium",
            REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
        ),
        registry=_small_registry(),
    )
    assert not approval_references_unknown_decision(
        _approval_record(
            "structural_drift:speaker_drift:speaker:critical",
            REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
        ),
        registry=_small_registry(),
    )


def test_approval_references_unknown_decision_ignores_invalid_approval_shape() -> None:
    assert not approval_references_unknown_decision(
        {"approval_status": "PENDING_REVIEW"},
        registry=_small_registry(),
    )


def test_traceability_audit_reports_approved_pending_orphan_and_invalid_records() -> None:
    approvals = [
        _approval_record(
            "exact_drift:replay_drift_unclassified:replay_drift:low",
            REPLAY_GOVERNANCE_APPROVAL_STATUS_APPROVED,
        ),
        _approval_record(
            "structural_drift:speaker_drift:speaker:critical",
            REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
        ),
        _approval_record(
            "structural_drift:speaker_drift:speaker:medium",
            REPLAY_GOVERNANCE_APPROVAL_STATUS_REJECTED,
        ),
        {"approval_status": "APPROVED"},
    ]

    audit = replay_governance_traceability_audit(approvals, registry=_small_registry())

    assert audit == {
        "governed_decisions": [
            "exact_drift:replay_drift_unclassified:replay_drift:low",
            "structural_drift:speaker_drift:speaker:critical",
        ],
        "approved_decisions": ["exact_drift:replay_drift_unclassified:replay_drift:low"],
        "pending_decisions": ["structural_drift:speaker_drift:speaker:critical"],
        "orphan_approvals": [
            {
                "index": 2,
                "decision_reference": "structural_drift:speaker_drift:speaker:medium",
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
    audit = replay_governance_traceability_audit([], registry=_small_registry())

    assert audit == {
        "governed_decisions": [
            "exact_drift:replay_drift_unclassified:replay_drift:low",
            "structural_drift:speaker_drift:speaker:critical",
        ],
        "approved_decisions": [],
        "pending_decisions": [],
        "orphan_approvals": [],
        "invalid_approvals": [],
    }
