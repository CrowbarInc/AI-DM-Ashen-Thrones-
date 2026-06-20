"""Tests for protected replay observation expansion (BQ-C1)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from tests.helpers.protected_replay_observation_corpus import (
    protected_replay_observation_expansion_rows,
    render_protected_replay_observation_corpus_report,
)
from tests.helpers.replay_bug_recurrence import (
    RECURRENCE_MATURITY_MIN_KEYS,
    RECURRENCE_MATURITY_MIN_OBSERVATIONS,
    build_recurrence_key,
    is_commit_worthy_recurrence_event,
)

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "expand_protected_replay_observations.py"
SPEC = importlib.util.spec_from_file_location("expand_protected_replay_observations_tool", TOOL)
assert SPEC and SPEC.loader
EXPAND = importlib.util.module_from_spec(SPEC)
sys.modules["expand_protected_replay_observations_tool"] = EXPAND
SPEC.loader.exec_module(EXPAND)


def test_observation_corpus_maps_to_three_distinct_recurrence_keys() -> None:
    rows = protected_replay_observation_expansion_rows()
    keys = {build_recurrence_key(row) for row in rows}

    assert len(rows) == 3
    assert len(keys) == 3
    assert all(str(row.get("scenario_id") or "").strip() for row in rows)
    assert all(str(row.get("test_node_id") or "").strip() for row in rows)


def test_observation_corpus_report_parses_into_three_rows() -> None:
    from tools.backfill_bug_recurrence_history import parse_failure_report_classification_rows

    markdown = render_protected_replay_observation_corpus_report()
    rows = parse_failure_report_classification_rows(markdown)

    assert len(rows) == 3
    scenario_ids = {row["scenario_id"] for row in rows}
    assert scenario_ids == {
        "wrong_speaker_strict_social_emission",
        "directed_npc_question",
        "sanitizer_scaffold_leakage",
    }


def test_expand_protected_replay_observations_meets_volume_targets(tmp_path: Path) -> None:
    corpus_path = tmp_path / "replay_failure_corpus_observations.md"
    corpus_path.write_text(render_protected_replay_observation_corpus_report(), encoding="utf-8")
    seed_log = {
        "schema_version": 1,
        "report_only": True,
        "advisory_only": True,
        "events": [
            {
                "event_source": "protected_replay_failure",
                "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
                "scenario_id": "vocative_override_after_prior_continuity",
                "turn_index": 1,
                "category": "projection",
                "owner_drift_bucket": "speaker_drift",
                "field_path": "selected_speaker_id",
                "investigate_first": "tests/helpers/golden_replay.py",
                "primary_owner": "projection",
                "event_index": 0,
                "recurrence_key": (
                    "recurrence:v1:speaker_drift|projection|selected_speaker_id|tests/helpers/golden_replay.py"
                ),
                "recorded_at": "2026-06-04T22:31:59Z",
            }
        ]
        * 2,
    }
    (tmp_path / "bug_recurrence_event_log.json").write_text(json.dumps(seed_log), encoding="utf-8")

    result = EXPAND.expand_protected_replay_observations(
        corpus_report_path=corpus_path,
        event_log_path=tmp_path / "bug_recurrence_event_log.json",
        history_json_path=tmp_path / "bug_recurrence_history.json",
        history_md_path=tmp_path / "bug_recurrence_history.md",
    )

    history = json.loads((tmp_path / "bug_recurrence_history.json").read_text(encoding="utf-8"))
    event_log = json.loads((tmp_path / "bug_recurrence_event_log.json").read_text(encoding="utf-8"))

    assert result["append_count"] == 3
    assert result["data_volume_target_met"] is True
    assert result["total_observations"] >= RECURRENCE_MATURITY_MIN_OBSERVATIONS
    assert result["unique_recurrence_count"] >= RECURRENCE_MATURITY_MIN_KEYS
    assert history["unique_recurrence_count"] >= RECURRENCE_MATURITY_MIN_KEYS
    assert len(event_log["events"]) == 5
    for event in event_log["events"]:
        worthy, _reason = is_commit_worthy_recurrence_event(event)
        assert worthy is True


def test_expand_protected_replay_observations_is_idempotent(tmp_path: Path) -> None:
    corpus_path = tmp_path / "replay_failure_corpus_observations.md"
    corpus_path.write_text(render_protected_replay_observation_corpus_report(), encoding="utf-8")
    kwargs = {
        "corpus_report_path": corpus_path,
        "event_log_path": tmp_path / "bug_recurrence_event_log.json",
        "history_json_path": tmp_path / "bug_recurrence_history.json",
        "history_md_path": tmp_path / "bug_recurrence_history.md",
    }

    first = EXPAND.expand_protected_replay_observations(**kwargs)
    second = EXPAND.expand_protected_replay_observations(**kwargs)

    assert first["append_count"] == 3
    assert second["append_count"] == 0
    assert second["skipped_duplicate_count"] == 3


def test_expand_confidence_metrics_move_toward_graduation(tmp_path: Path) -> None:
    corpus_path = tmp_path / "replay_failure_corpus_observations.md"
    corpus_path.write_text(render_protected_replay_observation_corpus_report(), encoding="utf-8")
    seed_log = {
        "schema_version": 1,
        "report_only": True,
        "advisory_only": True,
        "events": [
            {
                "event_source": "protected_replay_failure",
                "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
                "scenario_id": "vocative_override_after_prior_continuity",
                "turn_index": 1,
                "category": "projection",
                "owner_drift_bucket": "speaker_drift",
                "field_path": "selected_speaker_id",
                "investigate_first": "tests/helpers/golden_replay.py",
                "primary_owner": "projection",
                "event_index": index,
                "recurrence_key": (
                    "recurrence:v1:speaker_drift|projection|selected_speaker_id|tests/helpers/golden_replay.py"
                ),
                "recorded_at": "2026-06-04T22:31:59Z",
            }
            for index in range(2)
        ],
    }
    (tmp_path / "bug_recurrence_event_log.json").write_text(json.dumps(seed_log), encoding="utf-8")

    result = EXPAND.expand_protected_replay_observations(
        corpus_report_path=corpus_path,
        event_log_path=tmp_path / "bug_recurrence_event_log.json",
        history_json_path=tmp_path / "bug_recurrence_history.json",
        history_md_path=tmp_path / "bug_recurrence_history.md",
    )

    assert result["forecast_confidence"] >= 0.75
    assert result["governance_confidence"] >= 0.75
    assert result["effectiveness_confidence"] >= 0.75
    assert result["operational_readiness_score"] >= 60.0
