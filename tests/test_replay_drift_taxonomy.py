from __future__ import annotations

import pytest

from tests.failure_classification_contract import ALLOWED_OWNER_DRIFT_BUCKETS
from tests.helpers.failure_classifier import classify_replay_failure, validate_failure_classification_row
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.golden_replay_api import build_long_session_stability_scorecard, compare_golden_replay_reruns
from tests.helpers.replay_drift_taxonomy import (
    aggregate_long_session_stability_classifications,
    classify_owner_drift_bucket,
    classify_rerun_delta_owner_drift_bucket,
    owner_drift_classifications_from_per_turn_deltas,
    stability_classification_rows_from_scorecard,
)
from tests.helpers.replay_observed_row_fixtures import observed_failure_row, synthetic_rerun_turn


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


def test_compare_golden_replay_reruns_identical_runs_have_zero_deltas():
    turns = [
        synthetic_rerun_turn(turn_index=0, turn_id="t01"),
        synthetic_rerun_turn(turn_index=1, turn_id="t02", route_kind="action", selected_speaker_id=None),
    ]

    scorecard = compare_golden_replay_reruns(turns, [dict(turn) for turn in turns])

    assert scorecard["report_only"] is True
    assert scorecard["total_turns_compared"] == 2
    assert scorecard["summary"] == {
        "speaker_delta_count": 0,
        "route_delta_count": 0,
        "fallback_delta_count": 0,
        "text_fingerprint_delta_count": 0,
        "scaffold_delta_count": 0,
        "runtime_lineage_delta_count": 0,
        "semantic_delta_frequency_delta_count": 0,
    }
    assert scorecard["per_turn_deltas"] == []


def test_compare_golden_replay_reruns_counts_speaker_only_drift():
    previous = [synthetic_rerun_turn(selected_speaker_id="runner")]
    current = [synthetic_rerun_turn(selected_speaker_id="guard")]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["speaker_delta_count"] == 1
    assert scorecard["summary"]["route_delta_count"] == 0
    assert scorecard["per_turn_deltas"][0]["deltas"]["speaker"] == {
        "previous": "runner",
        "current": "guard",
    }
    assert scorecard["frequencies"]["speakers"]["delta"] == {"guard": 1, "runner": -1}


def test_compare_golden_replay_reruns_counts_route_only_drift():
    previous = [synthetic_rerun_turn(route_kind="dialogue")]
    current = [synthetic_rerun_turn(route_kind="action")]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["route_delta_count"] == 1
    assert scorecard["summary"]["speaker_delta_count"] == 0
    assert scorecard["per_turn_deltas"][0]["deltas"]["route"] == {
        "previous": "dialogue",
        "current": "action",
    }
    assert scorecard["frequencies"]["routes"]["delta"] == {"action": 1, "dialogue": -1}


def test_compare_golden_replay_reruns_counts_fallback_frequency_drift():
    event = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner="game.final_emission_gate",
        fallback_kind="sealed_or_global_replacement",
        fallback_selection_owner="final_emission_gate",
    )
    previous = [synthetic_rerun_turn()]
    current = [
        synthetic_rerun_turn(
            fallback_family="gate_terminal_repair",
            fallback_owner="sealed_gate",
            runtime_lineage_events=[event],
        )
    ]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["fallback_delta_count"] == 1
    assert scorecard["summary"]["runtime_lineage_delta_count"] == 1
    assert scorecard["frequencies"]["fallback_families"]["delta"] == {"gate_terminal_repair": 1}
    assert scorecard["frequencies"]["fallback_owners"]["delta"] == {"sealed_gate": 1}
    assert (
        scorecard["frequencies"]["runtime_lineage"]["frequency_deltas"]["fallback_frequency"]["delta"]
        == {"sealed_or_global_replacement": 1}
    )


def test_compare_golden_replay_reruns_reports_text_fingerprints_without_failing():
    previous = [synthetic_rerun_turn(final_text="The runner answers.")]
    current = [synthetic_rerun_turn(final_text="The runner answers with a warning.")]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["text_fingerprint_delta_count"] == 1
    fingerprint_delta = scorecard["per_turn_deltas"][0]["deltas"]["text_fingerprint"]
    assert fingerprint_delta["previous"] != fingerprint_delta["current"]
    assert len(fingerprint_delta["previous"]) == 16
    assert len(fingerprint_delta["current"]) == 16
    assert scorecard["report_only"] is True


def test_compare_golden_replay_reruns_handles_missing_optional_metadata():
    previous = [{"turn_index": 0, "final_text": "Rain falls."}]
    current = [{"turn_index": 0, "final_text": "Rain falls.", "runtime_lineage_events": "not-a-list"}]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["total_turns_compared"] == 1
    assert scorecard["summary"]["speaker_delta_count"] == 0
    assert scorecard["summary"]["route_delta_count"] == 0
    assert scorecard["summary"]["fallback_delta_count"] == 0
    assert scorecard["summary"]["runtime_lineage_delta_count"] == 0
    assert scorecard["summary"]["semantic_delta_frequency_delta_count"] == 0
    assert scorecard["frequencies"]["response_delta"]["previous"]["response_delta_unknown_count"] == 1
    assert scorecard["frequencies"]["response_delta"]["current"]["response_delta_unknown_count"] == 1
    assert scorecard["per_turn_deltas"] == []


def test_compare_golden_replay_reruns_reports_response_delta_frequency_deltas():
    previous = [
        synthetic_rerun_turn(
            response_delta_checked=True,
            response_delta_failed=False,
            response_delta_repaired=False,
            response_delta_kind="new_fact",
            response_delta_echo_overlap_band="low",
        )
    ]
    current = [
        synthetic_rerun_turn(
            response_delta_checked=True,
            response_delta_failed=True,
            response_delta_repaired=True,
            response_delta_kind="new_actionable_lead",
            response_delta_echo_overlap_band="high",
        )
    ]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["semantic_delta_frequency_delta_count"] == 1
    response_delta = scorecard["frequencies"]["response_delta"]
    assert response_delta["failed"]["delta"] == {"failed": 1}
    assert response_delta["repaired"]["delta"] == {"repaired": 1}
    assert response_delta["kinds"]["delta"] == {"new_actionable_lead": 1, "new_fact": -1}
    assert response_delta["echo_overlap_bands"]["delta"] == {"high": 1, "low": -1}
    assert scorecard["per_turn_deltas"][0]["deltas"]["response_delta"]["response_delta_failed"] == {
        "previous": False,
        "current": True,
    }


def test_stability_classification_rows_from_scorecard_projects_owner_fields():
    scorecard = build_long_session_stability_scorecard(
        scenario_id="projection_probe",
        observations=[
            {"turn_index": 0, "route_kind": "dialogue", "selected_speaker_id": "runner"},
            {"turn_index": 1, "route_kind": "social", "selected_speaker_id": "runner"},
        ],
    )

    rows = stability_classification_rows_from_scorecard(scorecard)
    assert rows
    assert rows[0]["scenario_id"] == "projection_probe"
    assert {"signal", "owner_drift_bucket", "severity_hint", "stability_status", "reason", "evidence"} <= set(rows[0])
    assert rows[0]["owner_drift_bucket"] == "route_drift"

    aggregation = aggregate_long_session_stability_classifications([scorecard])
    assert aggregation["total_scorecards"] == 1
    assert aggregation["bucket_frequencies"]["route_drift"] == 1
    assert aggregation["scenario_frequencies"]["projection_probe"] == 1
    assert aggregation["stability_status_counts"]["stable"] == 1
    assert aggregation == aggregate_long_session_stability_classifications([scorecard])


def test_stability_ownership_projection_stable_scorecard_empty():
    scorecard = build_long_session_stability_scorecard(
        scenario_id="stable_projection_probe",
        observations=[
            {"turn_index": 0, "route_kind": "dialogue", "selected_speaker_id": "runner"},
            {"turn_index": 1, "route_kind": "dialogue", "selected_speaker_id": "runner"},
        ],
    )
    assert stability_classification_rows_from_scorecard(scorecard) == []


def test_stability_ownership_projection_degraded_scorecard_surfaces_rows():
    scorecard = build_long_session_stability_scorecard(
        scenario_id="degraded_projection_probe",
        observations=[{"turn_index": 0, "route_kind": "dialogue", "selected_speaker_id": "runner"}],
        continuity_result={
            "evaluation": {
                "session_health": {"classification": "warning", "overall_passed": False},
                "degradation_over_time": {
                    "progressive_degradation_detected": True,
                    "reason_codes": ["rising_generic_filler_progressive"],
                },
            }
        },
    )
    rows = stability_classification_rows_from_scorecard(scorecard)
    assert rows
    assert all(row["stability_status"] == "degraded" for row in rows)
    assert any(row["owner_drift_bucket"] == "semantic_drift" for row in rows)
