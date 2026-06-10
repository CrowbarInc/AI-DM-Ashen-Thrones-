from tests.replay_governance_approval_contract import (
    ALLOWED_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS,
    ALLOWED_REPLAY_GOVERNANCE_APPROVAL_STATUSES,
    OPTIONAL_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS,
    REPLAY_GOVERNANCE_APPROVAL_STATUS_APPROVED,
    REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW,
    REPLAY_GOVERNANCE_APPROVAL_STATUS_REJECTED,
    REQUIRED_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS,
    approval_record_shape_errors,
    is_valid_approval_status,
)
from tests.helpers.replay_governance_fixtures import approval_record_fixture


def test_approval_status_vocabulary_is_contract_locked() -> None:
    assert ALLOWED_REPLAY_GOVERNANCE_APPROVAL_STATUSES == frozenset(
        {
            "APPROVED",
            "REJECTED",
            "PENDING_REVIEW",
        }
    )
    assert REPLAY_GOVERNANCE_APPROVAL_STATUS_APPROVED == "APPROVED"
    assert REPLAY_GOVERNANCE_APPROVAL_STATUS_REJECTED == "REJECTED"
    assert REPLAY_GOVERNANCE_APPROVAL_STATUS_PENDING_REVIEW == "PENDING_REVIEW"


def test_approval_record_fields_are_contract_locked() -> None:
    assert REQUIRED_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS == frozenset(
        {
            "approval_status",
            "decision_reference",
            "approval_reason",
            "reviewed_by",
            "review_date",
            "approval_source",
        }
    )
    assert OPTIONAL_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS == frozenset({"notes"})
    assert ALLOWED_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS == (
        REQUIRED_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS
        | OPTIONAL_REPLAY_GOVERNANCE_APPROVAL_RECORD_FIELDS
    )


def test_is_valid_approval_status_accepts_only_canonical_values() -> None:
    for value in ALLOWED_REPLAY_GOVERNANCE_APPROVAL_STATUSES:
        assert is_valid_approval_status(value)

    assert not is_valid_approval_status("ACCEPTED")
    assert not is_valid_approval_status("BLOCKED")
    assert not is_valid_approval_status("")
    assert not is_valid_approval_status(None)


def test_approval_record_shape_errors_accepts_valid_record() -> None:
    assert approval_record_shape_errors(approval_record_fixture()) == []


def test_approval_record_shape_errors_accepts_optional_notes() -> None:
    record = approval_record_fixture()
    record["notes"] = "Documentary approval metadata only."

    assert approval_record_shape_errors(record) == []


def test_approval_record_shape_errors_requires_mapping() -> None:
    assert approval_record_shape_errors(None) == ["approval record must be a mapping"]


def test_approval_record_shape_errors_reports_missing_fields() -> None:
    record = approval_record_fixture()
    del record["approval_reason"]
    del record["reviewed_by"]

    assert approval_record_shape_errors(record) == [
        "missing approval field: approval_reason",
        "missing approval field: reviewed_by",
    ]


def test_approval_record_shape_errors_rejects_invalid_status() -> None:
    record = approval_record_fixture()
    record["approval_status"] = "WAIVED"

    assert approval_record_shape_errors(record) == ["invalid approval_status: 'WAIVED'"]


def test_approval_record_shape_errors_requires_text_fields() -> None:
    record = approval_record_fixture()
    record["decision_reference"] = ""
    record["approval_reason"] = " "
    record["approval_source"] = None

    assert approval_record_shape_errors(record) == [
        "decision_reference must be a non-empty string",
        "approval_reason must be a non-empty string",
        "approval_source must be a non-empty string",
    ]


def test_approval_record_shape_errors_rejects_non_text_notes() -> None:
    record = approval_record_fixture()
    record["notes"] = 123

    assert approval_record_shape_errors(record) == ["notes must be a string when present"]


def test_approval_record_shape_errors_rejects_unknown_fields() -> None:
    record = approval_record_fixture()
    record["waiver_override"] = "not allowed"

    assert approval_record_shape_errors(record) == ["unknown approval field: waiver_override"]


def test_approval_record_shape_errors_is_deterministic() -> None:
    record = {
        "approval_status": "OVERRIDE",
        "unknown_b": "b",
        "unknown_a": "a",
    }

    assert approval_record_shape_errors(record) == [
        "missing approval field: approval_reason",
        "missing approval field: approval_source",
        "missing approval field: decision_reference",
        "missing approval field: review_date",
        "missing approval field: reviewed_by",
        "invalid approval_status: 'OVERRIDE'",
        "unknown approval field: unknown_a",
        "unknown approval field: unknown_b",
    ]
