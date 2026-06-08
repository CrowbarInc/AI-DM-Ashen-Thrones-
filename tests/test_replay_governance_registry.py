from tests.replay_governance_contract import (
    ALLOWED_REPLAY_GOVERNANCE_DECISIONS,
    REPLAY_GOVERNANCE_DECISION_ACCEPTED,
    REPLAY_GOVERNANCE_DECISION_BLOCKED,
    REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
    governance_record_shape_errors,
)
from tests.replay_governance_registry import (
    governance_record_key,
    governance_records_for_bucket,
    governance_records_for_owner_bucket,
    replay_governance_registry,
)


def test_replay_governance_registry_records_satisfy_contract() -> None:
    registry = replay_governance_registry()

    assert registry
    for record in registry:
        assert governance_record_shape_errors(record) == []
        assert record["governance_decision"] in ALLOWED_REPLAY_GOVERNANCE_DECISIONS


def test_replay_governance_registry_has_no_duplicate_keys() -> None:
    registry = replay_governance_registry()
    keys = [governance_record_key(record) for record in registry]

    assert len(keys) == len(set(keys))


def test_replay_governance_registry_order_is_deterministic() -> None:
    first = replay_governance_registry()
    second = replay_governance_registry()

    assert first == second
    assert [governance_record_key(record) for record in first] == [
        governance_record_key(record) for record in second
    ]


def test_replay_governance_registry_returns_copies() -> None:
    registry = replay_governance_registry()
    registry[0]["governance_decision"] = "CHANGED"

    assert replay_governance_registry()[0]["governance_decision"] != "CHANGED"


def test_replay_governance_registry_covers_core_decision_examples() -> None:
    exact = governance_records_for_bucket("exact_drift")
    lineage = governance_records_for_bucket("lineage_drift")
    speaker = governance_records_for_owner_bucket("speaker_drift")

    assert exact[0]["governance_decision"] == REPLAY_GOVERNANCE_DECISION_ACCEPTED
    assert lineage[0]["governance_decision"] == REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED
    assert speaker[0]["governance_decision"] == REPLAY_GOVERNANCE_DECISION_BLOCKED
    assert "protected speaker" in speaker[0]["governance_reason"]


def test_governance_records_for_bucket_filters_by_drift_bucket() -> None:
    records = governance_records_for_bucket("structural_drift")

    assert records
    assert all(record["drift_bucket"] == "structural_drift" for record in records)


def test_governance_records_for_owner_bucket_filters_by_owner_bucket() -> None:
    records = governance_records_for_owner_bucket("emission_drift")

    assert records
    assert all(record["owner_bucket"] == "emission_drift" for record in records)


def test_registry_contains_accepted_blocked_and_review_required_decisions() -> None:
    decisions = {record["governance_decision"] for record in replay_governance_registry()}

    assert decisions == {
        REPLAY_GOVERNANCE_DECISION_ACCEPTED,
        REPLAY_GOVERNANCE_DECISION_BLOCKED,
        REPLAY_GOVERNANCE_DECISION_REVIEW_REQUIRED,
    }
