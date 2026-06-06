from __future__ import annotations

import pytest

from tests.failure_classification_contract import ALLOWED_OWNER_DRIFT_BUCKETS
from tests.helpers.failure_classifier import classify_replay_failure, validate_failure_classification_row
from tests.helpers.golden_replay import compare_golden_replay_reruns
from tests.helpers.replay_drift_taxonomy import (
    classify_owner_drift_bucket,
    classify_rerun_delta_owner_drift_bucket,
    owner_drift_classifications_from_per_turn_deltas,
)
from tests.helpers.replay_observed_row_fixtures import observed_failure_row


@pytest.mark.parametrize(
    ("field_path", "category", "measurement", "tags", "expected"),
    [
        ("route_kind", "route", "structural_drift", ["route_mismatch", "structural_drift"], "route_drift"),
        ("selected_speaker_id", "speaker", "structural_drift", ["speaker_mismatch"], "speaker_drift"),
        ("fallback_family", "fallback", "structural_drift", ["fallback_family_mismatch"], "fallback_drift"),
        (
            "opening_fallback_owner_bucket",
            "fallback",
            "structural_drift",
            ["fallback_family_mismatch"],
            "ownership_drift",
        ),
        (
            "response_type_repair_used",
            "emission",
            "structural_drift",
            ["response_type_repair_mismatch"],
            "emission_drift",
        ),
        ("scaffold_leakage", "sanitizer", "semantic_drift", ["scaffold_leakage"], "semantic_drift"),
        ("schema_contract", "normalization", "structural_drift", [], "projection_drift"),
        ("final_text", "replay_drift", "exact_drift", ["exact_drift"], "replay_drift_unclassified"),
    ],
)
def test_classify_owner_drift_bucket_covers_canonical_buckets(
    field_path: str,
    category: str,
    measurement: str,
    tags: list[str],
    expected: str,
) -> None:
    assert (
        classify_owner_drift_bucket(
            field_path=field_path,
            category=category,
            measurement_drift_bucket=measurement,
            replay_tags=tags,
        )
        == expected
    )
    assert expected in ALLOWED_OWNER_DRIFT_BUCKETS


def test_classify_owner_drift_bucket_lineage_is_rerun_only() -> None:
    assert "lineage_drift" not in {
        classify_owner_drift_bucket(
            field_path="route_kind",
            category="route",
            measurement_drift_bucket="structural_drift",
            replay_tags=["structural_drift"],
        )
    }


@pytest.mark.parametrize(
    ("delta_key", "payload", "expected"),
    [
        ("speaker", {"previous": "runner", "current": "guard"}, "speaker_drift"),
        ("route", {"previous": "dialogue", "current": "action"}, "route_drift"),
        (
            "fallback",
            {"previous_family": "social", "current_family": "scene_opening", "previous_owner": "a", "current_owner": "b"},
            "fallback_drift",
        ),
        (
            "fallback",
            {"previous_family": "social", "current_family": "social", "previous_owner": "a", "current_owner": "b"},
            "ownership_drift",
        ),
        ("response_delta", {"response_delta_failed": {"previous": False, "current": True}}, "emission_drift"),
        ("scaffold", {"previous": False, "current": True}, "semantic_drift"),
        ("runtime_lineage", {"total_event_delta": 1}, "lineage_drift"),
        ("text_fingerprint", {"previous": "abc", "current": "def"}, "replay_drift_unclassified"),
    ],
)
def test_classify_rerun_delta_owner_drift_bucket(delta_key: str, payload: dict, expected: str) -> None:
    assert classify_rerun_delta_owner_drift_bucket(delta_key, payload) == expected


def test_owner_drift_classifications_from_per_turn_deltas() -> None:
    rows = owner_drift_classifications_from_per_turn_deltas(
        [
            {
                "turn_index": 2,
                "deltas": {
                    "speaker": {"previous": "runner", "current": "guard"},
                    "route": {"previous": "dialogue", "current": "action"},
                },
            }
        ]
    )
    assert rows == [
        {"turn_index": 2, "owner_drift_bucket": "speaker_drift", "delta_key": "speaker"},
        {"turn_index": 2, "owner_drift_bucket": "route_drift", "delta_key": "route"},
    ]


def test_classify_replay_failure_emits_owner_drift_bucket() -> None:
    observed = observed_failure_row(
        selected_speaker_id="guard",
        route_kind="dialogue",
    )
    rows = classify_replay_failure(
        scenario_id="wrong_speaker",
        turn_index=0,
        observed_turn=observed,
        drift_rows=[
            {
                "field_path": "selected_speaker_id",
                "expected": "runner",
                "actual": "guard",
                "reason": "equals mismatch",
                "drift_bucket": "structural_drift",
                "replay_tags": ["structural_drift"],
            }
        ],
    )
    assert len(rows) == 1
    assert rows[0]["owner_drift_bucket"] == "speaker_drift"
    assert rows[0]["category"] == "speaker"
    assert rows[0]["primary_owner"] == "speaker"
    assert validate_failure_classification_row(rows[0]) == []


def test_classify_replay_failure_preserves_existing_classification_fields() -> None:
    observed = observed_failure_row(selected_speaker_id="guard")
    drift_row = {
        "field_path": "selected_speaker_id",
        "expected": "runner",
        "actual": "guard",
        "reason": "equals mismatch",
        "drift_bucket": "structural_drift",
        "replay_tags": ["structural_drift"],
    }

    rows = classify_replay_failure(
        scenario_id="baseline",
        turn_index=0,
        observed_turn=observed,
        drift_rows=[drift_row],
    )
    row = rows[0]
    assert row["owner_drift_bucket"] == "speaker_drift"
    assert row["category"] == "speaker"
    assert row["primary_owner"] == "speaker"
    assert row["secondary_owner"] == "emission"
    assert row["severity"] == "critical"
    assert "speaker_mismatch" in row["replay_tags"]
    assert row["investigate_first"] == "game/speaker_contract_enforcement.py"
    assert validate_failure_classification_row(row) == []


def test_compare_golden_replay_reruns_emits_owner_drift_classifications() -> None:
    previous = [
        {
            "turn_index": 0,
            "selected_speaker_id": "runner",
            "route_kind": "dialogue",
            "final_text": "Same text.",
        }
    ]
    current = [
        {
            "turn_index": 0,
            "selected_speaker_id": "guard",
            "route_kind": "action",
            "final_text": "Different text.",
        }
    ]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["report_only"] is True
    assert scorecard["owner_drift_classifications"] == [
        {"turn_index": 0, "owner_drift_bucket": "speaker_drift", "delta_key": "speaker"},
        {"turn_index": 0, "owner_drift_bucket": "route_drift", "delta_key": "route"},
        {"turn_index": 0, "owner_drift_bucket": "replay_drift_unclassified", "delta_key": "text_fingerprint"},
    ]


def test_compare_golden_replay_reruns_identical_runs_have_empty_owner_drift_classifications() -> None:
    turn = {
        "selected_speaker_id": "runner",
        "route_kind": "dialogue",
        "final_text": "Stable.",
        "scaffold_leakage": False,
    }
    scorecard = compare_golden_replay_reruns([turn], [dict(turn)])
    assert scorecard["report_only"] is True
    assert scorecard["owner_drift_classifications"] == []


def test_summarize_owner_drift_buckets_counts_classifications() -> None:
    from tests.helpers.replay_drift_taxonomy import summarize_owner_drift_buckets

    counts = summarize_owner_drift_buckets(
        [
            {"owner_drift_bucket": "route_drift"},
            {"owner_drift_bucket": "route_drift"},
            {"owner_drift_bucket": "speaker_drift"},
            {"owner_drift_bucket": "invalid_ignored"},
        ]
    )
    assert counts["route_drift"] == 2
    assert counts["speaker_drift"] == 1
    assert counts["fallback_drift"] == 0
    assert sum(counts.values()) == 3


def test_summarize_owner_drift_buckets_empty_input() -> None:
    from tests.helpers.replay_drift_taxonomy import ALLOWED_OWNER_DRIFT_BUCKETS, summarize_owner_drift_buckets

    counts = summarize_owner_drift_buckets([])
    assert set(counts) == set(ALLOWED_OWNER_DRIFT_BUCKETS)
    assert sum(counts.values()) == 0


def test_render_protected_replay_failure_report_includes_owner_drift_bucket() -> None:
    from tests.helpers.failure_dashboard_report import render_protected_replay_failure_report
    from tests.helpers.replay_observed_row_fixtures import observed_failure_row

    observed = observed_failure_row(selected_speaker_id="guard")
    rows = classify_replay_failure(
        scenario_id="report_probe",
        turn_index=0,
        observed_turn=observed,
        drift_rows=[
            {
                "field_path": "selected_speaker_id",
                "expected": "runner",
                "actual": "guard",
                "reason": "equals mismatch",
                "drift_bucket": "structural_drift",
                "replay_tags": ["structural_drift"],
            }
        ],
    )
    enriched = dict(rows[0])
    enriched["test_node_id"] = "tests/test_golden_replay.py::probe"
    enriched["failed_invariant"] = "selected_speaker_id: equals mismatch"

    report = render_protected_replay_failure_report([enriched], generated_at="2026-06-06T00:00:00Z")
    assert "| Owner Drift Bucket |" in report
    assert "speaker_drift" in report
    assert "## Owner Drift Breakdown" in report


def test_render_rerun_scorecard_includes_owner_drift_summary() -> None:
    from tests.helpers.failure_dashboard_report import render_rerun_drift_scorecard_markdown

    scorecard = compare_golden_replay_reruns(
        [{"selected_speaker_id": "runner", "route_kind": "dialogue", "final_text": "A."}],
        [{"selected_speaker_id": "guard", "route_kind": "dialogue", "final_text": "A."}],
    )
    markdown = render_rerun_drift_scorecard_markdown(scorecard, generated_at="2026-06-06T00:00:00Z")
    assert "## Owner Drift Summary" in markdown
    assert "| `speaker_drift` | `1` |" in markdown
    assert scorecard["report_only"] is True


def test_render_rerun_scorecard_empty_owner_drift_summary() -> None:
    from tests.helpers.failure_dashboard_report import render_rerun_drift_scorecard_markdown

    scorecard = compare_golden_replay_reruns(
        [{"selected_speaker_id": "runner", "final_text": "Stable."}],
        [{"selected_speaker_id": "runner", "final_text": "Stable."}],
    )
    markdown = render_rerun_drift_scorecard_markdown(scorecard)
    assert "## Owner Drift Summary" in markdown
    assert "No owner drift classifications." in markdown
