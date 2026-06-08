from tests.replay_governance_contract import (
    ALLOWED_REPLAY_GOVERNANCE_DECISIONS,
    REPLAY_GOVERNANCE_DECISION_ACCEPTED,
    REPLAY_GOVERNANCE_DECISION_BLOCKED,
    REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
    REQUIRED_REPLAY_GOVERNANCE_RECORD_FIELDS,
    governance_record_shape_errors,
    is_valid_governance_decision,
)


def _valid_record() -> dict[str, str]:
    return {
        "drift_bucket": "structural_drift",
        "owner_bucket": "speaker_drift",
        "category": "speaker",
        "severity": "critical",
        "governance_decision": REPLAY_GOVERNANCE_DECISION_BLOCKED,
        "governance_reason": "Existing protected speaker invariant mismatch blocks when asserted.",
        "policy_source": "docs/testing/protected_replay_manifest.md",
    }


def test_replay_governance_decision_vocabulary_is_contract_locked() -> None:
    assert ALLOWED_REPLAY_GOVERNANCE_DECISIONS == frozenset(
        {
            "ACCEPTED",
            "BLOCKED",
            "REVIEW_REQUIRED",
        }
    )
    assert REPLAY_GOVERNANCE_DECISION_ACCEPTED == "ACCEPTED"
    assert REPLAY_GOVERNANCE_DECISION_BLOCKED == "BLOCKED"
    assert REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED == "REVIEW_REQUIRED"


def test_required_governance_record_fields_are_contract_locked() -> None:
    assert REQUIRED_REPLAY_GOVERNANCE_RECORD_FIELDS == frozenset(
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


def test_is_valid_governance_decision_accepts_only_canonical_values() -> None:
    for value in ALLOWED_REPLAY_GOVERNANCE_DECISIONS:
        assert is_valid_governance_decision(value)

    assert not is_valid_governance_decision("WARNING")
    assert not is_valid_governance_decision("REPORT_ONLY")
    assert not is_valid_governance_decision("")
    assert not is_valid_governance_decision(None)


def test_governance_record_shape_errors_accepts_valid_record() -> None:
    assert governance_record_shape_errors(_valid_record()) == []


def test_governance_record_shape_errors_requires_mapping() -> None:
    assert governance_record_shape_errors(None) == ["governance record must be a mapping"]


def test_governance_record_shape_errors_reports_missing_fields() -> None:
    record = _valid_record()
    del record["owner_bucket"]
    del record["policy_source"]

    assert governance_record_shape_errors(record) == [
        "missing governance field: owner_bucket",
        "missing governance field: policy_source",
    ]


def test_governance_record_shape_errors_rejects_invalid_decision() -> None:
    record = _valid_record()
    record["governance_decision"] = "REPORT_ONLY"

    assert governance_record_shape_errors(record) == ["invalid governance_decision: 'REPORT_ONLY'"]


def test_governance_record_shape_errors_requires_reason_and_source_text() -> None:
    record = _valid_record()
    record["governance_reason"] = " "
    record["policy_source"] = ""

    assert governance_record_shape_errors(record) == [
        "governance_reason must be a non-empty string",
        "policy_source must be a non-empty string",
    ]
