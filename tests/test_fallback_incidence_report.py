"""Focused tests for the read-only fallback incidence report."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from game.runtime_lineage_telemetry import make_runtime_lineage_event

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "fallback_incidence_report.py"
SPEC = importlib.util.spec_from_file_location("fallback_incidence_report_tool", TOOL)
assert SPEC and SPEC.loader
REPORT = importlib.util.module_from_spec(SPEC)
sys.modules["fallback_incidence_report_tool"] = REPORT
SPEC.loader.exec_module(REPORT)

BV1B_TOOL = ROOT / "tools" / "bv1b_fallback_incidence_validation.py"
BV1B_SPEC = importlib.util.spec_from_file_location("bv1b_fallback_incidence_validation_tool", BV1B_TOOL)
assert BV1B_SPEC and BV1B_SPEC.loader
BV1B = importlib.util.module_from_spec(BV1B_SPEC)
sys.modules["bv1b_fallback_incidence_validation_tool"] = BV1B
BV1B_SPEC.loader.exec_module(BV1B)


def _fallback_event(kind: str = "scene_opening", **kwargs: object) -> dict[str, object]:
    return make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner=kwargs.pop("owner", "game.final_emission_gate"),
        fallback_kind=kind,
        gate_path=kwargs.pop("gate_path", "opening_fallback"),
        **kwargs,
    )


def _turn(
    *,
    route: str | None = "social",
    events: list[dict[str, object]] | None = None,
    fem: dict[str, object] | None = None,
    observed_family: str | None = None,
) -> dict[str, object]:
    turn: dict[str, object] = {
        "meta": {
            "runtime_lineage_events": list(events or []),
            "final_emission_meta": dict(fem or {}),
        },
    }
    if route is not None:
        turn["resolution"] = {"kind": route}
    if observed_family is not None:
        turn["fallback_family"] = observed_family
    return turn


def test_no_turns_has_zero_rate_and_empty_frequencies() -> None:
    report = REPORT.build_fallback_incidence_report([])

    assert report["eligible_turn_count"] == 0
    assert report["fallback_turn_count"] == 0
    assert report["fallback_event_count"] == 0
    assert report["fallback_trigger_rate"] == 0.0
    assert all(values == {} for values in report["frequency"].values())


def test_turns_without_fallbacks_still_populate_route_denominator() -> None:
    report = REPORT.build_fallback_incidence_report([_turn(route="social"), _turn(route="action")])

    assert report["eligible_turn_count"] == 2
    assert report["fallback_turn_count"] == 0
    assert report["fallback_event_count"] == 0
    assert report["route_turn_count"] == {"action": 1, "social": 1}
    assert report["route_fallback_trigger_rate"] == {"action": 0.0, "social": 0.0}


def test_single_fallback_turn_computes_turn_and_route_rates() -> None:
    report = REPORT.build_fallback_incidence_report(
        [
            _turn(route="social"),
            _turn(route="social", events=[_fallback_event("strict_social_fallback")]),
        ]
    )

    assert report["fallback_turn_count"] == 1
    assert report["fallback_event_count"] == 1
    assert report["fallback_trigger_rate"] == 0.5
    assert report["frequency"]["fallback_kind"] == {"strict_social_fallback": 1}
    assert report["route_fallback_turn_count"] == {"social": 1}
    assert report["route_fallback_trigger_rate"] == {"social": 0.5}


def test_existing_fallback_trigger_rate_is_unchanged_by_classification_fields() -> None:
    report = REPORT.build_fallback_incidence_report(
        [
            _turn(route="social"),
            _turn(route="social", events=[_fallback_event("strict_social_fallback")]),
            _turn(route="action", events=[_fallback_event("visibility_hard_replacement")]),
        ]
    )

    assert report["eligible_turn_count"] == 3
    assert report["fallback_turn_count"] == 2
    assert report["fallback_event_count"] == 2
    assert report["fallback_trigger_rate"] == pytest.approx(2 / 3)


def test_classifies_governed_bounded_fallback_as_active_governed() -> None:
    classified = REPORT.classify_fallback_incidence_event(
        {
            "event_kind": "fallback_selected",
            "fallback_kind": "scene_opening",
            "realization_family": "upstream_prepared_emission",
            "fallback_authorship_source": "upstream_prepared_opening_fallback",
            "fallback_owner_bucket": "upstream-prepared",
            "final_route": "replaced",
        }
    )

    assert classified["compatibility_status"] == "active_governed"
    assert classified["governed_classification"] == "BOUNDED"


def test_classifies_legacy_runtime_fallback_from_registry() -> None:
    classified = REPORT.classify_fallback_incidence_event(
        {
            "event_kind": "fallback_selected",
            "fallback_kind": "legacy_bridge",
            "realization_family": "legacy_diegetic_fallback",
            "fallback_owner_bucket": "legacy-renderer",
        }
    )

    assert classified["compatibility_status"] == "legacy_runtime"
    assert classified["governed_classification"] == "LEGACY"


def test_classifies_legacy_compatibility_local_opening_as_read_only() -> None:
    classified = REPORT.classify_fallback_incidence_event(
        {
            "event_kind": "fallback_selected",
            "fallback_kind": "scene_opening",
            "fallback_authorship_source": "compatibility_local_opening_deterministic",
            "fallback_owner_bucket": "unknown-ambiguous",
        }
    )

    assert classified["compatibility_status"] == "legacy_read_only"


def test_classifies_unknown_unclassified_fallback() -> None:
    classified = REPORT.classify_fallback_incidence_event(
        {
            "event_kind": "fallback_selected",
            "fallback_kind": "unmapped_runtime_fallback",
            "realization_family": "legacy_unclassified",
            "fallback_owner_bucket": "unknown-ambiguous",
        }
    )

    assert classified["compatibility_status"] == "unknown_unclassified"
    assert classified["governed_classification"] == "UNKNOWN"


@pytest.mark.parametrize(
    ("fallback_kind", "gate_path", "expected_site", "expected_condition"),
    [
        (
            "upstream_fast_fallback",
            "unknown",
            "upstream_fast_fallback",
            "upstream_provider_or_budget_failure",
        ),
        (
            "referential_clarity_hard_replacement",
            "referential_clarity_hard_replaced",
            "referential_clarity_hard_replacement",
            "referential_clarity_gate_failed",
        ),
        (
            "opening_failed_closed",
            "opening_failed_closed",
            "opening_failed_closed",
            "empty_curated_facts",
        ),
    ],
)
def test_classifies_trigger_site_and_condition(
    fallback_kind: str,
    gate_path: str,
    expected_site: str,
    expected_condition: str,
) -> None:
    classified = REPORT.classify_fallback_incidence_event(
        {"event_kind": "fallback_selected", "fallback_kind": fallback_kind, "gate_path": gate_path}
    )

    assert classified["trigger_site"] == expected_site
    assert classified["trigger_condition"] == expected_condition


def test_multi_event_turn_counts_one_turn_and_all_events() -> None:
    report = REPORT.build_fallback_incidence_report(
        [_turn(events=[_fallback_event("scene_opening"), _fallback_event("visibility_hard_replacement")])]
    )

    assert report["eligible_turn_count"] == 1
    assert report["fallback_turn_count"] == 1
    assert report["fallback_event_count"] == 2
    assert report["frequency"]["fallback_kind"] == {
        "scene_opening": 1,
        "visibility_hard_replacement": 1,
    }


def test_only_recorded_runtime_fallback_selected_events_count() -> None:
    speaker_repair = make_runtime_lineage_event(event_kind="speaker_repair", repair_kind="speaker_grounding")
    wrong_event_type = {**_fallback_event(), "event_type": "other"}
    report = REPORT.build_fallback_incidence_report(
        [_turn(events=[speaker_repair, wrong_event_type, _fallback_event("scene_opening")])]
    )

    assert report["fallback_turn_count"] == 1
    assert report["fallback_event_count"] == 1
    assert report["frequency"]["fallback_kind"] == {"scene_opening": 1}


def test_missing_route_is_unknown_and_not_known_route_coverage() -> None:
    report = REPORT.build_fallback_incidence_report([_turn(route=None, events=[_fallback_event()])])

    assert report["route_turn_count"] == {"unknown": 1}
    assert report["unknown_route_turn_count"] == 1
    assert report["route_fallback_turn_count"] == {"unknown": 1}
    assert report["metadata_coverage"]["fallback_events_with_known_route"] == 0


def test_family_taxonomies_remain_separate() -> None:
    report = REPORT.build_fallback_incidence_report(
        [
            _turn(
                events=[_fallback_event()],
                fem={
                    "final_route": "replaced",
                    "fallback_family_used": "scene_opening",
                    "realization_fallback_family": "gate_terminal_repair",
                },
                observed_family="compatibility_opening",
            )
        ]
    )

    frequency = report["frequency"]
    assert frequency["diegetic_family"] == {"scene_opening": 1}
    assert frequency["realization_family"] == {"gate_terminal_repair": 1}
    assert frequency["observed_family"] == {"compatibility_opening": 1}
    assert frequency["final_route"] == {"replaced": 1}
    assert frequency["compatibility_status"] == {"active_governed": 1}
    assert frequency["governed_classification"] == {"BOUNDED": 1}


def test_owner_dimensions_and_cross_tabs_remain_separate() -> None:
    event = _fallback_event(
        owner="game.final_emission_gate",
        fallback_owner_bucket="upstream-prepared",
        fallback_selection_owner="game.final_emission_gate",
        fallback_content_owner="game.opening_deterministic_fallback",
        fallback_authorship_source="upstream_prepared",
    )
    report = REPORT.build_fallback_incidence_report(
        [_turn(route="opening", events=[event], fem={"final_route": "replaced"})]
    )

    assert report["frequency"]["fallback_owner_bucket"] == {"upstream-prepared": 1}
    assert report["frequency"]["event_owner"] == {"game.final_emission_gate": 1}
    assert report["frequency"]["fallback_selection_owner"] == {"game.final_emission_gate": 1}
    assert report["frequency"]["fallback_content_owner"] == {"game.opening_deterministic_fallback": 1}
    assert report["frequency"]["fallback_authorship_source"] == {"upstream_prepared": 1}
    assert report["cross_tabs"]["route_kind_x_fallback_kind"] == {"opening": {"scene_opening": 1}}
    assert report["cross_tabs"]["route_kind_x_final_route"] == {"opening": {"replaced": 1}}
    assert report["cross_tabs"]["compatibility_status_by_family"] == {
        "unknown_unclassified": {"scene_opening": 1}
    }
    assert report["cross_tabs"]["compatibility_status_by_route"] == {
        "unknown_unclassified": {"replaced": 1}
    }
    assert report["cross_tabs"]["trigger_site_by_family"] == {"opening_fallback": {"scene_opening": 1}}
    assert report["cross_tabs"]["owner_by_compatibility_status"] == {
        "game.final_emission_gate": {"unknown_unclassified": 1}
    }


def test_report_schema_includes_classification_frequency_keys() -> None:
    report = REPORT.build_fallback_incidence_report(
        [
            _turn(
                events=[_fallback_event("upstream_fast_fallback", gate_path="unknown")],
                fem={"final_route": "replaced", "realization_fallback_family": "gpt_budget_or_provider_failure"},
            )
        ]
    )

    for key in (
        "compatibility_status",
        "governed_classification",
        "trigger_site",
        "trigger_condition",
    ):
        assert key in report["frequency"]
    for key in (
        "compatibility_status_by_family",
        "compatibility_status_by_route",
        "trigger_site_by_family",
        "owner_by_compatibility_status",
    ):
        assert key in report["cross_tabs"]
    assert report["frequency"]["compatibility_status"] == {"active_governed": 1}
    assert report["frequency"]["governed_classification"] == {"BOUNDED": 1}
    assert report["frequency"]["trigger_site"] == {"upstream_fast_fallback": 1}
    assert report["frequency"]["trigger_condition"] == {"upstream_provider_or_budget_failure": 1}


def test_bv1b_primary_only_refresh_does_not_rewrite_supporting_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact_dir = tmp_path / "golden_replay"
    artifact_dir.mkdir()
    primary_json = artifact_dir / "bv1b_fallback_incidence_report.json"
    primary_md = artifact_dir / "bv1b_fallback_incidence_report.md"
    summary_path = tmp_path / "bv1b_fallback_summary.json"
    supporting_paths = [
        summary_path,
        artifact_dir / "fallback_incidence_history.json",
        artifact_dir / "fallback_incidence_trends.md",
        artifact_dir / "fallback_recurrence_report.json",
        artifact_dir / "fallback_incidence_anomalies.json",
        artifact_dir / "fallback_risk_report.json",
        artifact_dir / "fallback_roi_report.json",
        artifact_dir / "fallback_maintenance_economics.json",
    ]
    for path in supporting_paths:
        path.write_text("sentinel", encoding="utf-8")
    primary_json.write_text(
        json.dumps({"artifact_scan": {"generated_at": "2026-06-21T13:45:36.418647Z"}}),
        encoding="utf-8",
    )
    primary_md.write_text("old primary", encoding="utf-8")

    monkeypatch.setattr(BV1B, "ARTIFACT_DIR", artifact_dir)
    monkeypatch.setattr(BV1B, "BV1B_REPORT_JSON", primary_json)
    monkeypatch.setattr(BV1B, "BV1B_REPORT_MD", primary_md)
    monkeypatch.setattr(BV1B, "HISTORY_PATH", artifact_dir / "fallback_incidence_history.json")
    monkeypatch.setattr(BV1B, "ROOT", tmp_path)
    monkeypatch.setattr(BV1B, "MEASUREMENT_ROOTS", (tmp_path,))
    monkeypatch.setattr(
        BV1B,
        "scan_canonical_fem_turns",
        lambda: (
            [
                _turn(
                    route="observe",
                    events=[
                        _fallback_event(
                            "referential_clarity_hard_replacement",
                            gate_path="referential_clarity_hard_replaced",
                        )
                    ],
                    fem={"final_route": "replaced", "realization_fallback_family": "gate_terminal_repair"},
                )
            ],
            1,
        ),
    )

    report = BV1B.run_instrumentation_pipeline(primary_only=True)

    assert report["artifact_scan"]["generated_at"] == "2026-06-21T13:45:36.418647Z"
    refreshed = json.loads(primary_json.read_text(encoding="utf-8"))
    assert refreshed["frequency"]["compatibility_status"] == {"active_governed": 1}
    assert "compatibility_status_by_family" in refreshed["cross_tabs"]
    assert "## Compatibility Status" in primary_md.read_text(encoding="utf-8")
    for path in supporting_paths:
        assert path.read_text(encoding="utf-8") == "sentinel"


def _guard_report(
    *,
    rate: float = 0.019801980198019802,
    events: int = 2,
    turns: int = 2,
    unknown: int = 1,
    active: int = 1,
    family: dict[str, int] | None = None,
    owner: dict[str, int] | None = None,
    route: dict[str, int] | None = None,
) -> dict[str, object]:
    return {
        "eligible_turn_count": 101,
        "fallback_event_count": events,
        "fallback_turn_count": turns,
        "fallback_trigger_rate": rate,
        "frequency": {
            "compatibility_status": {
                key: value
                for key, value in {
                    "active_governed": active,
                    "unknown_unclassified": unknown,
                }.items()
                if value
            },
            "fallback_kind": family
            or {
                "referential_clarity_hard_replacement": 1,
                "sealed_unknown_replacement": 1,
            },
            "fallback_authorship_source": {},
            "event_owner": owner or {"game.final_emission_gate": events},
            "final_route": route or {"replaced": events},
            "governed_classification": {"BOUNDED": active, "UNKNOWN": unknown},
            "trigger_site": {
                "referential_clarity_hard_replacement": active,
                "sealed_terminal_replacement": unknown,
            },
        },
    }


def test_bv1b_baseline_guard_equal_report_passes() -> None:
    baseline = _guard_report()
    result = BV1B.compare_bv1b_primary_baseline(baseline, baseline)

    assert result["status"] == "pass"
    assert result["hard_failures"] == []


def test_bv1b_baseline_guard_tolerates_small_movement() -> None:
    result = BV1B.compare_bv1b_primary_baseline(
        _guard_report(),
        _guard_report(
            rate=0.049,
            events=5,
            turns=5,
            unknown=2,
            active=3,
            family={"referential_clarity_hard_replacement": 2, "sealed_unknown_replacement": 3},
        ),
    )

    assert result["status"] == "pass"
    assert result["hard_failures"] == []
    assert result["warnings"]


def test_bv1b_baseline_guard_fails_rate_above_threshold() -> None:
    result = BV1B.compare_bv1b_primary_baseline(_guard_report(), _guard_report(rate=0.051))

    assert result["status"] == "fail"
    assert any("fallback_trigger_rate_above_5_percent" in item for item in result["hard_failures"])


def test_bv1b_baseline_guard_fails_event_delta_above_threshold() -> None:
    result = BV1B.compare_bv1b_primary_baseline(_guard_report(), _guard_report(events=6, rate=0.049))

    assert result["status"] == "fail"
    assert any("fallback_event_count_delta_above_3" in item for item in result["hard_failures"])


def test_bv1b_baseline_guard_fails_unknown_unclassified_delta_above_threshold() -> None:
    result = BV1B.compare_bv1b_primary_baseline(
        _guard_report(),
        _guard_report(events=4, rate=0.039, unknown=3, active=1),
    )

    assert result["status"] == "fail"
    assert any("unknown_unclassified_delta_above_1" in item for item in result["hard_failures"])


def test_bv1b_check_baseline_mode_does_not_rewrite_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact_dir = tmp_path / "golden_replay"
    artifact_dir.mkdir()
    primary_json = artifact_dir / "bv1b_fallback_incidence_report.json"
    primary_md = artifact_dir / "bv1b_fallback_incidence_report.md"
    supporting = artifact_dir / "fallback_incidence_history.json"
    baseline = _guard_report()
    primary_json.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    primary_md.write_text("primary sentinel", encoding="utf-8")
    supporting.write_text("supporting sentinel", encoding="utf-8")

    monkeypatch.setattr(BV1B, "ROOT", tmp_path)
    monkeypatch.setattr(BV1B, "MEASUREMENT_ROOTS", (tmp_path,))
    monkeypatch.setattr(BV1B, "BV1B_REPORT_JSON", primary_json)
    monkeypatch.setattr(BV1B, "BV1B_REPORT_MD", primary_md)
    monkeypatch.setattr(BV1B, "HISTORY_PATH", supporting)
    current_turns = [
        _turn(
            route="observe",
            events=[
                _fallback_event(
                    "referential_clarity_hard_replacement",
                    gate_path="referential_clarity_hard_replaced",
                )
            ],
            fem={"final_route": "replaced", "realization_fallback_family": "gate_terminal_repair"},
        ),
        _turn(
            route="question",
            events=[_fallback_event("sealed_unknown_replacement", gate_path="replaced_or_sealed")],
            fem={"final_route": "replaced"},
        ),
        *[_turn(route="scene_opening") for _ in range(99)],
    ]
    monkeypatch.setattr(
        BV1B,
        "scan_canonical_fem_turns",
        lambda: (current_turns, 101),
    )

    assert BV1B.main(["--check-baseline"]) == 0
    output = capsys.readouterr().out
    assert "BV1B fallback incidence baseline guard: pass" in output
    assert primary_json.read_text(encoding="utf-8") == json.dumps(baseline, indent=2, sort_keys=True) + "\n"
    assert primary_md.read_text(encoding="utf-8") == "primary sentinel"
    assert supporting.read_text(encoding="utf-8") == "supporting sentinel"


def test_route_precedence_prefers_explicit_route_over_trace_and_resolution() -> None:
    turn = _turn(route="resolution-route", events=[_fallback_event()])
    turn["route_kind"] = "observed-route"
    turn["trace"] = {"social_contract_trace": {"route_selected": "trace-route"}}

    report = REPORT.build_fallback_incidence_report([turn])

    assert report["route_turn_count"] == {"observed-route": 1}


def test_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    input_path = tmp_path / "transcript.json"
    json_out = tmp_path / "nested" / "fallback_incidence.json"
    markdown_out = tmp_path / "nested" / "fallback_incidence.md"
    input_path.write_text(
        json.dumps({"turns": [_turn(events=[_fallback_event()], fem={"final_route": "replaced"})]}),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--input",
            str(input_path),
            "--json-out",
            str(json_out),
            "--md-out",
            str(markdown_out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(json_out.read_text(encoding="utf-8"))["fallback_trigger_rate"] == 1.0
    markdown = markdown_out.read_text(encoding="utf-8")
    assert "# Fallback Incidence Report" in markdown
    assert "**Fallback trigger rate:** 100.00%" in markdown
    assert "## Route Trigger Rates" in markdown
    assert str(json_out) in completed.stdout
    assert str(markdown_out) in completed.stdout


def test_cli_rejects_missing_turns_list(tmp_path: Path) -> None:
    input_path = tmp_path / "bad.json"
    input_path.write_text("{}", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--input",
            str(input_path),
            "--json-out",
            str(tmp_path / "out.json"),
            "--md-out",
            str(tmp_path / "out.md"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "top-level 'turns' list" in completed.stderr
