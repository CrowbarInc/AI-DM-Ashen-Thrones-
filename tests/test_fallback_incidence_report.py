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


def test_multi_event_turn_counts_one_turn_and_all_events() -> None:
    report = REPORT.build_fallback_incidence_report(
        [_turn(events=[_fallback_event("scene_opening"), _fallback_event("visibility_or_scene_replacement")])]
    )

    assert report["eligible_turn_count"] == 1
    assert report["fallback_turn_count"] == 1
    assert report["fallback_event_count"] == 2
    assert report["frequency"]["fallback_kind"] == {
        "scene_opening": 1,
        "visibility_or_scene_replacement": 1,
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
