"""Tests for bug recurrence event log lane migration (BQ3.7)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from tests.helpers import failure_dashboard_recurrence as FDR
from tests.helpers.failure_dashboard_report import assert_recurrence_payload_scoped_populations
from tests.helpers.replay_bug_recurrence import (
    DEFAULT_EVENT_SOURCE,
    PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
    append_recurrence_events,
    build_recurrence_key,
    empty_recurrence_event_log,
    load_recurrence_event_log,
    write_recurrence_event_log,
)

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "migrate_bug_recurrence_event_log.py"
SPEC = importlib.util.spec_from_file_location("migrate_bug_recurrence_event_log_tool", TOOL)
assert SPEC and SPEC.loader
MIGRATE = importlib.util.module_from_spec(SPEC)
sys.modules["migrate_bug_recurrence_event_log_tool"] = MIGRATE
SPEC.loader.exec_module(MIGRATE)

REGENERATE_TOOL = ROOT / "tools" / "regenerate_bug_recurrence_history.py"
REGENERATE_SPEC = importlib.util.spec_from_file_location(
    "regenerate_bug_recurrence_history_tool",
    REGENERATE_TOOL,
)
assert REGENERATE_SPEC and REGENERATE_SPEC.loader
REGENERATE = importlib.util.module_from_spec(REGENERATE_SPEC)
sys.modules["regenerate_bug_recurrence_history_tool"] = REGENERATE
REGENERATE_SPEC.loader.exec_module(REGENERATE)

FIXED_GENERATED_AT = "2026-06-28T19:40:00Z"


def _classification_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "scenario_id": "vocative_override_after_prior_continuity",
        "turn_index": 1,
        "category": "projection",
        "primary_owner": "projection",
        "owner_drift_bucket": "speaker_drift",
        "field_path": "selected_speaker_id",
        "investigate_first": "tests/helpers/golden_replay.py",
    }
    row.update(overrides)
    return row


def _build_unified_fixture_log() -> dict[str, object]:
    protected = append_recurrence_events(
        empty_recurrence_event_log(),
        [_classification_row()],
        event_metadata={
            "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
            "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
            "recorded_at": "2026-06-04T22:31:59Z",
        },
    )
    session = append_recurrence_events(
        protected,
        [
            _classification_row(
                scenario_id=None,
                field_path="route_kind",
                investigate_first="unknown",
                owner_drift_bucket="route_drift",
            )
        ],
        event_source=DEFAULT_EVENT_SOURCE,
        recorded_at="2026-06-10T00:00:00Z",
    )
    synthetic = append_recurrence_events(
        session,
        [
            _classification_row(
                scenario_id=None,
                field_path="fallback_family",
                investigate_first="unknown",
                owner_drift_bucket="fallback_drift",
            )
        ],
        event_metadata={
            "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
            "artifact_source": "artifacts/golden_replay/replay_failure_report.md",
            "recorded_at": "2026-06-11T00:00:00Z",
        },
    )
    return synthetic


def _migration_paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "event_log": tmp_path / "bug_recurrence_event_log.json",
        "session_diagnostic": tmp_path / "bug_recurrence_session_diagnostic_event_log.json",
        "session": tmp_path / "bug_recurrence_session_event_log.json",
        "synthetic": tmp_path / "bug_recurrence_synthetic_test_artifact_event_log.json",
        "history_json": tmp_path / "bug_recurrence_history.json",
        "history_md": tmp_path / "bug_recurrence_history.md",
        "legacy": tmp_path / "bug_recurrence_event_log.legacy.json",
        "report": tmp_path / "BQ37_recurrence_history_migration.md",
    }


def _write_fresh_unified_source(paths: dict[str, Path]) -> None:
    for path in paths.values():
        if path.exists():
            path.unlink()
    trajectory_path = paths["history_json"].with_name("recurrence_trajectory_history.json")
    if trajectory_path.exists():
        trajectory_path.unlink()
    write_recurrence_event_log(paths["event_log"], _build_unified_fixture_log())


def _read_recurrence_artifact_bytes(paths: dict[str, Path]) -> dict[str, bytes]:
    return {
        "protected_event_log": paths["event_log"].read_bytes(),
        "session_event_log": paths["session"].read_bytes(),
        "synthetic_test_artifact_event_log": paths["synthetic"].read_bytes(),
        "history_json": paths["history_json"].read_bytes(),
        "history_md": paths["history_md"].read_bytes(),
    }


def _existing_output_names(paths: dict[str, Path]) -> set[str]:
    output_paths = {
        paths["event_log"],
        paths["session"],
        paths["synthetic"],
        paths["history_json"],
        paths["history_md"],
        paths["session_diagnostic"],
        paths["legacy"],
        paths["report"],
        paths["history_json"].with_name("recurrence_trajectory_history.json"),
    }
    return {path.name for path in output_paths if path.exists()}


def test_migration_creates_byte_for_byte_legacy_archive(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    unified = _build_unified_fixture_log()
    write_recurrence_event_log(paths["event_log"], unified)
    original_bytes = paths["event_log"].read_bytes()

    MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        session_event_log_path=paths["session"],
        synthetic_test_artifact_event_log_path=paths["synthetic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
    )

    assert paths["legacy"].read_bytes() == original_bytes
    assert paths["report"].is_file()


def test_migration_split_counts_equal_original(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    unified = _build_unified_fixture_log()
    write_recurrence_event_log(paths["event_log"], unified)
    original_count = len(unified["events"])

    result = MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        session_event_log_path=paths["session"],
        synthetic_test_artifact_event_log_path=paths["synthetic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
    )

    protected_log = load_recurrence_event_log(paths["event_log"])
    diagnostic_log = load_recurrence_event_log(paths["session_diagnostic"])
    session_log = load_recurrence_event_log(paths["session"])
    synthetic_log = load_recurrence_event_log(paths["synthetic"])

    assert result["verification"]["no_events_lost"] is True
    assert len(protected_log["events"]) + len(diagnostic_log["events"]) == original_count
    assert result["summary"]["protected_event_count"] == 1
    assert result["summary"]["session_diagnostic_event_count"] == 1
    assert result["summary"]["synthetic_test_artifact_event_count"] == 1
    assert result["summary"]["diagnostic_event_count"] == original_count - 1
    assert diagnostic_log["compatibility_only"] is True
    assert diagnostic_log["events"] == session_log["events"] + synthetic_log["events"]
    assert [event["event_source"] for event in session_log["events"]] == [DEFAULT_EVENT_SOURCE]
    assert [event["event_source"] for event in synthetic_log["events"]] == [
        PROTECTED_REPLAY_FAILURE_EVENT_SOURCE
    ]
    assert session_log["events"][0]["recurrence_key"] != synthetic_log["events"][0]["recurrence_key"]


def test_migration_is_idempotent(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    write_recurrence_event_log(paths["event_log"], _build_unified_fixture_log())
    kwargs = {
        "event_log_path": paths["event_log"],
        "session_diagnostic_event_log_path": paths["session_diagnostic"],
        "session_event_log_path": paths["session"],
        "synthetic_test_artifact_event_log_path": paths["synthetic"],
        "history_json_path": paths["history_json"],
        "history_md_path": paths["history_md"],
        "legacy_archive_path": paths["legacy"],
        "report_path": paths["report"],
    }

    first = MIGRATE.migrate_bug_recurrence_event_log(**kwargs)
    protected_after_first = paths["event_log"].read_text(encoding="utf-8")
    diagnostic_after_first = paths["session_diagnostic"].read_text(encoding="utf-8")
    session_after_first = paths["session"].read_text(encoding="utf-8")
    synthetic_after_first = paths["synthetic"].read_text(encoding="utf-8")
    history_after_first = paths["history_json"].read_text(encoding="utf-8")
    legacy_bytes = paths["legacy"].read_bytes()

    second = MIGRATE.migrate_bug_recurrence_event_log(**kwargs)

    assert first["summary"] == second["summary"]
    assert paths["event_log"].read_text(encoding="utf-8") == protected_after_first
    assert paths["session_diagnostic"].read_text(encoding="utf-8") == diagnostic_after_first
    assert paths["session"].read_text(encoding="utf-8") == session_after_first
    assert paths["synthetic"].read_text(encoding="utf-8") == synthetic_after_first
    assert paths["history_json"].read_text(encoding="utf-8") == history_after_first
    assert paths["legacy"].read_bytes() == legacy_bytes


def test_protected_history_regenerated_from_protected_lane_only(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    write_recurrence_event_log(paths["event_log"], _build_unified_fixture_log())

    result = MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        session_event_log_path=paths["session"],
        synthetic_test_artifact_event_log_path=paths["synthetic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
    )

    history = json.loads(paths["history_json"].read_text(encoding="utf-8"))
    protected_metric = result["protected"]["regression_recurrence_rate"]

    assert history["total_rows"] == 1
    assert history["unique_recurrence_count"] == 1
    assert history["regression_recurrence_rate"]["numerator"] == protected_metric["numerator"] == 0
    assert history["regression_recurrence_rate"]["denominator"] == protected_metric["denominator"] == 1
    assert history["regression_recurrence_rate"]["rate"] == 0.0
    assert history["protected_replay_regression_recurrence_rate"]["population"] == "protected_replay_history"
    assert_recurrence_payload_scoped_populations(history)
    assert history["session_diagnostic_regression_recurrence_rate"]["denominator"] == 1
    assert history["session_diagnostic_regression_recurrence_rate"]["numerator"] == 0
    assert history["synthetic_test_artifact_regression_recurrence_rate"]["denominator"] == 1
    assert history["synthetic_test_artifact_regression_recurrence_rate"]["numerator"] == 0
    assert history["protected_replay_regression_recurrence_rate"]["numerator"] == 0
    assert history["protected_replay_regression_recurrence_rate"]["denominator"] == 1


def test_diagnostic_events_never_appear_in_protected_history(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    write_recurrence_event_log(paths["event_log"], _build_unified_fixture_log())

    MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        session_event_log_path=paths["session"],
        synthetic_test_artifact_event_log_path=paths["synthetic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
    )

    diagnostic_log = load_recurrence_event_log(paths["session_diagnostic"])
    history = json.loads(paths["history_json"].read_text(encoding="utf-8"))
    diagnostic_keys = {
        str(event.get("recurrence_key") or build_recurrence_key(event))
        for event in diagnostic_log["events"]
    }
    history_keys = {str(entry["recurrence_key"]) for entry in history["recurrences"]}

    assert diagnostic_keys
    assert history_keys
    assert diagnostic_keys.isdisjoint(history_keys)


def test_dry_run_does_not_write_artifacts(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    write_recurrence_event_log(paths["event_log"], _build_unified_fixture_log())
    original_bytes = paths["event_log"].read_bytes()

    result = MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        session_event_log_path=paths["session"],
        synthetic_test_artifact_event_log_path=paths["synthetic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert paths["event_log"].read_bytes() == original_bytes
    assert not paths["legacy"].exists()
    assert not paths["history_json"].exists()
    assert not paths["report"].exists()


def test_recurrence_only_mode_writes_only_recurrence_artifacts(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    write_recurrence_event_log(paths["event_log"], _build_unified_fixture_log())

    result = MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        session_event_log_path=paths["session"],
        synthetic_test_artifact_event_log_path=paths["synthetic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
        emit_compatibility_artifacts=False,
        emit_governance_docs=False,
        emit_audit_docs=False,
        generated_at=FIXED_GENERATED_AT,
    )

    assert paths["event_log"].is_file()
    assert paths["session"].is_file()
    assert paths["synthetic"].is_file()
    assert paths["history_json"].is_file()
    assert paths["history_md"].is_file()
    assert not paths["session_diagnostic"].exists()
    assert not paths["legacy"].exists()
    assert not paths["report"].exists()
    assert result["written_paths"]["recurrence_artifacts"] == [
        paths["event_log"].as_posix(),
        paths["session"].as_posix(),
        paths["synthetic"].as_posix(),
        paths["history_json"].as_posix(),
        paths["history_md"].as_posix(),
    ]
    assert result["written_paths"]["compatibility_artifacts"] == []
    assert result["written_paths"]["governance_reports"] == []
    assert result["written_paths"]["audit_reports"] == []


def test_governance_suppression_prevents_governance_markdown_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _migration_paths(tmp_path)
    governance_paths = [
        tmp_path / "graduation.md",
        tmp_path / "calibration.md",
        tmp_path / "final_decision.md",
        tmp_path / "outcome.md",
    ]
    for doc_path in governance_paths:
        doc_path.write_text("sentinel\n", encoding="utf-8")
    monkeypatch.setattr(FDR, "BUG_RECURRENCE_HISTORY_JSON_PATH", paths["history_json"])
    monkeypatch.setattr(FDR, "RECURRENCE_GRADUATION_AUDIT_DOC_PATH", governance_paths[0])
    monkeypatch.setattr(FDR, "RECURRENCE_CONFIDENCE_CALIBRATION_DOC_PATH", governance_paths[1])
    monkeypatch.setattr(FDR, "RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH", governance_paths[2])
    monkeypatch.setattr(FDR, "RECURRENCE_OUTCOME_VALIDATION_DOC_PATH", governance_paths[3])
    write_recurrence_event_log(paths["event_log"], _build_unified_fixture_log())

    result = MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        session_event_log_path=paths["session"],
        synthetic_test_artifact_event_log_path=paths["synthetic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
        emit_governance_docs=False,
        emit_audit_docs=False,
        generated_at=FIXED_GENERATED_AT,
    )

    assert result["written_paths"]["governance_reports"] == []
    assert [path.read_text(encoding="utf-8") for path in governance_paths] == ["sentinel\n"] * 4
    assert not (tmp_path / "recurrence_trajectory_history.json").exists()


def test_default_mode_emits_governance_and_audit_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = _migration_paths(tmp_path)
    graduation_path = tmp_path / "graduation.md"
    calibration_path = tmp_path / "calibration.md"
    final_decision_path = tmp_path / "final_decision.md"
    outcome_path = tmp_path / "outcome.md"
    monkeypatch.setattr(FDR, "BUG_RECURRENCE_HISTORY_JSON_PATH", paths["history_json"])
    monkeypatch.setattr(FDR, "RECURRENCE_GRADUATION_AUDIT_DOC_PATH", graduation_path)
    monkeypatch.setattr(FDR, "RECURRENCE_CONFIDENCE_CALIBRATION_DOC_PATH", calibration_path)
    monkeypatch.setattr(FDR, "RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH", final_decision_path)
    monkeypatch.setattr(FDR, "RECURRENCE_OUTCOME_VALIDATION_DOC_PATH", outcome_path)
    write_recurrence_event_log(paths["event_log"], _build_unified_fixture_log())

    result = MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        session_event_log_path=paths["session"],
        synthetic_test_artifact_event_log_path=paths["synthetic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
        generated_at=FIXED_GENERATED_AT,
    )

    assert paths["legacy"].is_file()
    assert paths["session_diagnostic"].is_file()
    assert paths["report"].is_file()
    assert graduation_path.is_file()
    assert calibration_path.is_file()
    assert final_decision_path.is_file()
    assert (tmp_path / "recurrence_trajectory_history.json").is_file()
    assert result["written_paths"]["audit_reports"] == [paths["report"].as_posix()]


def test_audit_suppression_prevents_migration_report(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    write_recurrence_event_log(paths["event_log"], _build_unified_fixture_log())

    result = MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        session_event_log_path=paths["session"],
        synthetic_test_artifact_event_log_path=paths["synthetic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
        emit_governance_docs=False,
        emit_audit_docs=False,
        generated_at=FIXED_GENERATED_AT,
    )

    assert not paths["report"].exists()
    assert result["written_paths"]["audit_reports"] == []


def test_compatibility_suppression_does_not_affect_recurrence_generation(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    _write_fresh_unified_source(paths)

    result = MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        session_event_log_path=paths["session"],
        synthetic_test_artifact_event_log_path=paths["synthetic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
        emit_compatibility_artifacts=False,
        emit_governance_docs=False,
        emit_audit_docs=False,
        generated_at=FIXED_GENERATED_AT,
    )

    assert paths["event_log"].is_file()
    assert paths["session"].is_file()
    assert paths["synthetic"].is_file()
    assert paths["history_json"].is_file()
    assert paths["history_md"].is_file()
    assert not paths["session_diagnostic"].exists()
    assert not paths["legacy"].exists()
    assert result["verification"]["metrics_regenerated"] is True
    history = json.loads(paths["history_json"].read_text(encoding="utf-8"))
    assert_recurrence_payload_scoped_populations(history)


def test_supported_emission_modes_write_expected_artifacts_and_identical_recurrence_payloads(
    tmp_path: Path,
) -> None:
    paths = _migration_paths(tmp_path)
    recurrence_names = {
        paths["event_log"].name,
        paths["session"].name,
        paths["synthetic"].name,
        paths["history_json"].name,
        paths["history_md"].name,
    }
    expected_outputs = {
        "default": recurrence_names
        | {
            paths["session_diagnostic"].name,
            paths["legacy"].name,
            paths["report"].name,
            "recurrence_trajectory_history.json",
        },
        "recurrence_only": recurrence_names,
        "no_governance_docs": recurrence_names
        | {
            paths["session_diagnostic"].name,
            paths["legacy"].name,
            paths["report"].name,
        },
        "no_audit_docs": recurrence_names
        | {
            paths["session_diagnostic"].name,
            paths["legacy"].name,
            "recurrence_trajectory_history.json",
        },
        "no_compatibility_artifacts": recurrence_names
        | {
            paths["report"].name,
            "recurrence_trajectory_history.json",
        },
    }
    mode_kwargs = {
        "default": {},
        "recurrence_only": {
            "emit_compatibility_artifacts": False,
            "emit_governance_docs": False,
            "emit_audit_docs": False,
        },
        "no_governance_docs": {"emit_governance_docs": False},
        "no_audit_docs": {"emit_audit_docs": False},
        "no_compatibility_artifacts": {"emit_compatibility_artifacts": False},
    }
    baseline_recurrence_bytes: dict[str, bytes] | None = None

    for mode, kwargs in mode_kwargs.items():
        _write_fresh_unified_source(paths)
        result = MIGRATE.migrate_bug_recurrence_event_log(
            event_log_path=paths["event_log"],
            session_diagnostic_event_log_path=paths["session_diagnostic"],
            session_event_log_path=paths["session"],
            synthetic_test_artifact_event_log_path=paths["synthetic"],
            history_json_path=paths["history_json"],
            history_md_path=paths["history_md"],
            legacy_archive_path=paths["legacy"],
            report_path=paths["report"],
            generated_at=FIXED_GENERATED_AT,
            **kwargs,
        )

        assert _existing_output_names(paths) == expected_outputs[mode]
        assert result["verification"]["metrics_regenerated"] is True
        recurrence_bytes = _read_recurrence_artifact_bytes(paths)
        if baseline_recurrence_bytes is None:
            baseline_recurrence_bytes = recurrence_bytes
        else:
            assert recurrence_bytes == baseline_recurrence_bytes


def test_migration_and_regeneration_write_byte_identical_recurrence_history(tmp_path: Path) -> None:
    paths = _migration_paths(tmp_path)
    write_recurrence_event_log(paths["event_log"], _build_unified_fixture_log())

    result = MIGRATE.migrate_bug_recurrence_event_log(
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        session_event_log_path=paths["session"],
        synthetic_test_artifact_event_log_path=paths["synthetic"],
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        legacy_archive_path=paths["legacy"],
        report_path=paths["report"],
        emit_governance_docs=False,
        emit_audit_docs=False,
        generated_at=FIXED_GENERATED_AT,
    )
    migration_json = paths["history_json"].read_bytes()
    migration_md = paths["history_md"].read_bytes()

    REGENERATE.regenerate_bug_recurrence_history(
        history_json_path=paths["history_json"],
        history_md_path=paths["history_md"],
        event_log_path=paths["event_log"],
        session_diagnostic_event_log_path=paths["session_diagnostic"],
        session_event_log_path=paths["session"],
        synthetic_test_artifact_event_log_path=paths["synthetic"],
        generated_at=FIXED_GENERATED_AT,
        command_used=result["command_used"],
    )

    assert paths["history_json"].read_bytes() == migration_json
    assert paths["history_md"].read_bytes() == migration_md
