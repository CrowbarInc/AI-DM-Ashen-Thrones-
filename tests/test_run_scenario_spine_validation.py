"""Tests for ``tools/run_scenario_spine_validation.py`` (no live model; no OpenAI)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.helpers.opening_fallback_evidence import successful_opening_fem_meta

pytestmark = pytest.mark.unit

_ROOT = Path(__file__).resolve().parents[1]


def _stub_metadata_session_health_fields(*, passed: bool = True, checked: int = 2, gaps: int = 0) -> dict:
    from game.scenario_spine_eval import SCENARIO_SPINE_IDENTITY_KEYS, TRANSCRIPT_TURN_META_ENVELOPE_KEYS

    miss = {k: (1 if k == "narration_seam" and not passed else 0) for k in TRANSCRIPT_TURN_META_ENVELOPE_KEYS}
    if passed:
        miss = {k: 0 for k in TRANSCRIPT_TURN_META_ENVELOPE_KEYS}
    fb = {} if passed else {"narration_seam": 0}
    fss = {} if passed else {}
    return {
        "metadata_completeness_passed": passed,
        "turns_checked": checked,
        "turns_missing_meta": gaps,
        "missing_by_key": miss,
        "first_missing_turn_by_key": fb,
        "missing_scenario_spine_identity_by_key": {k: 0 for k in SCENARIO_SPINE_IDENTITY_KEYS},
        "first_missing_turn_by_scenario_spine_identity_key": fss,
    }
_TOOL = _ROOT / "tools" / "run_scenario_spine_validation.py"
_spec = importlib.util.spec_from_file_location("run_scenario_spine_validation_tool", _TOOL)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules["run_scenario_spine_validation_tool"] = _mod
_spec.loader.exec_module(_mod)
_COMPARE_TOOL = _ROOT / "tools" / "compare_scenario_spine_reruns.py"
_compare_spec = importlib.util.spec_from_file_location("compare_scenario_spine_reruns_tool", _COMPARE_TOOL)
assert _compare_spec and _compare_spec.loader
_compare_mod = importlib.util.module_from_spec(_compare_spec)
sys.modules["compare_scenario_spine_reruns_tool"] = _compare_mod
_compare_spec.loader.exec_module(_compare_mod)

FIXTURE = _ROOT / "data" / "validation" / "scenario_spines" / "frontier_gate_long_session.json"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fabricated_spine_artifact_dir(
    root: Path,
    *,
    spine_id: str = "spine_alpha",
    branch_id: str = "branch_one",
    classification: str = "clean",
    score: int = 100,
    speaker: str = "runner",
    route: str = "dialogue",
    gm_text: str = "The runner answers with a steady lead.",
    include_optional: bool = True,
) -> Path:
    run_dir = root / spine_id / branch_id
    turns = [
        {
            "turn_index": 0,
            "turn_id": "turn_001",
            "player_prompt": "What did you see?",
            "gm_text": gm_text,
            "api_ok": True,
            "resolution_kind": route,
            "selected_speaker_id": speaker,
            "fallback_family": None,
            "meta": {
                "scenario_spine": {
                    "spine_id": spine_id,
                    "branch_id": branch_id,
                    "turn_id": "turn_001",
                    "turn_index": 0,
                    "smoke": False,
                    "max_turns": None,
                    "resume_entry_first_turn": False,
                    "artifact_schema_version": 1,
                },
                "runtime_lineage_events": [
                    {
                        "event_type": "runtime_lineage",
                        "event_kind": "gate_outcome",
                        "stage": "gate",
                        "owner": "game.final_emission_gate",
                        "source": "synthetic",
                        "gate_path": "strict_social_accept",
                        "recurrence_key": "gate_outcome:gate:game.final_emission_gate:strict_social_accept",
                    }
                ],
            },
        }
    ]
    _write_json(
        run_dir / "transcript.json",
        {
            "schema_version": 1,
            "spine_id": spine_id,
            "branch_id": branch_id,
            "turn_count": len(turns),
            "turns": turns,
        },
    )
    _write_json(
        run_dir / "session_health_summary.json",
        {
            "schema_version": 1,
            "session_health": {
                "classification": classification,
                "score": score,
                "overall_passed": classification == "clean",
                "turn_count": len(turns),
            },
            "axes": {
                "state_continuity": {
                    "passed": classification == "clean",
                    "failure_codes": [] if classification == "clean" else ["continuity_lost"],
                    "warning_codes": [] if classification == "clean" else ["continuity_weak"],
                },
                "referent_persistence": {"passed": True, "failure_codes": [], "warning_codes": []},
                "project_progression": {"passed": True, "failure_codes": [], "warning_codes": []},
            },
            "detected_failures": [] if classification == "clean" else [{"axis": "state_continuity", "code": "continuity_lost"}],
            "warnings": [] if classification == "clean" else [{"axis": "state_continuity", "code": "continuity_weak"}],
            "checkpoint_results": [] if classification == "clean" else [{"issues": [{"code": "continuity_weak"}]}],
            "degradation_over_time": {
                "progressive_degradation_detected": classification != "clean",
                "reason_codes": [] if classification == "clean" else ["late_continuity_weak"],
            },
        },
    )
    if include_optional:
        _write_json(
            run_dir / "runtime_lineage_summary.json",
            {
                "total_events": 1,
                "by_event_kind": {"gate_outcome": 1},
                "by_stage": {"gate": 1},
                "by_recurrence_key": {"gate_outcome:gate:game.final_emission_gate:strict_social_accept": 1},
                "fallback_frequency": {},
                "fallback_authorship_frequency": {},
                "fallback_owner_bucket_frequency": {},
                "fallback_selection_owner_frequency": {},
                "fallback_content_owner_frequency": {},
                "speaker_repair_frequency": {},
                "mutation_kind_frequency": {},
                "gate_path_frequency": {"strict_social_accept": 1},
                "recurring_events": [],
            },
        )
        _write_json(run_dir / "branch_divergence.json", {"distinct_outcomes_detected": True, "reason_codes": []})
    return run_dir


def _load_spine():
    spine, errs = _mod.load_spine(FIXTURE)
    assert errs == []
    return spine


def _patch_session_storage(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from game import storage

    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(storage, "SESSION_PATH", storage.DATA_DIR / "session.json")


def test_list_main_stdout_lists_canonical_branches(capsys) -> None:
    code = _mod.main(["--list"])
    assert code == 0
    out = capsys.readouterr().out
    assert "frontier_gate_long_session" in out
    assert "branch_social_inquiry" in out
    assert "branch_direct_intrusion" in out
    assert "branch_cautious_observe" in out


def test_subprocess_list_matches_fixture() -> None:
    proc = subprocess.run(
        [sys.executable, str(_TOOL), "--list"],
        cwd=str(_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "branch_social_inquiry" in proc.stdout


def test_compare_scenario_spine_reruns_identical_artifacts_have_zero_deltas(tmp_path: Path) -> None:
    previous = _fabricated_spine_artifact_dir(tmp_path / "previous")
    current = _fabricated_spine_artifact_dir(tmp_path / "current")

    scorecard = _compare_mod.compare_scenario_spine_rerun_dirs(previous, current)

    assert scorecard["report_only"] is True
    assert scorecard["identity"]["mismatch"] is False
    assert scorecard["summary"]["turn_count_delta"] == 0
    assert scorecard["summary"]["route_delta_count"] == 0
    assert scorecard["summary"]["speaker_delta_count"] == 0
    assert scorecard["summary"]["text_fingerprint_delta_count"] == 0
    assert scorecard["summary"]["health_changed_field_count"] == 0
    assert scorecard["summary"]["runtime_lineage_changed_key_count"] == 0
    assert scorecard["transcript"]["per_turn_deltas"] == []


def test_compare_scenario_spine_reruns_reports_health_delta(tmp_path: Path) -> None:
    previous = _fabricated_spine_artifact_dir(tmp_path / "previous")
    current = _fabricated_spine_artifact_dir(tmp_path / "current", classification="degraded", score=65)

    scorecard = _compare_mod.compare_scenario_spine_rerun_dirs(previous, current)
    health = scorecard["health"]["deltas"]

    assert health["classification"] == {"previous": "clean", "current": "degraded", "changed": True}
    assert health["score"] == {"previous": 100, "current": 65, "changed": True}
    assert health["tracked_axis_warning_counts"]["delta"] == {"state_continuity": 1}
    assert health["checkpoint_issue_counts"]["delta"] == {"continuity_weak": 1}
    assert health["degradation_reason_counts"]["delta"] == {"late_continuity_weak": 1}


def test_compare_scenario_spine_reruns_reports_transcript_route_speaker_text_deltas(tmp_path: Path) -> None:
    previous = _fabricated_spine_artifact_dir(tmp_path / "previous")
    current = _fabricated_spine_artifact_dir(
        tmp_path / "current",
        speaker="guard",
        route="action",
        gm_text="The guard redirects the answer toward the west road.",
    )

    scorecard = _compare_mod.compare_scenario_spine_rerun_dirs(previous, current)

    assert scorecard["summary"]["route_delta_count"] == 1
    assert scorecard["summary"]["speaker_delta_count"] == 1
    assert scorecard["summary"]["text_fingerprint_delta_count"] == 1
    assert scorecard["transcript"]["frequencies"]["routes"]["delta"] == {"action": 1, "dialogue": -1}
    assert scorecard["transcript"]["frequencies"]["speakers"]["delta"] == {"guard": 1, "runner": -1}
    row = scorecard["transcript"]["per_turn_deltas"][0]
    assert sorted(row["deltas"]) == ["route", "speaker", "text_fingerprint"]


def test_compare_scenario_spine_reruns_missing_optional_files_do_not_crash(tmp_path: Path) -> None:
    previous = _fabricated_spine_artifact_dir(tmp_path / "previous", include_optional=False)
    current = _fabricated_spine_artifact_dir(tmp_path / "current", include_optional=False)

    scorecard = _compare_mod.compare_scenario_spine_rerun_dirs(previous, current)

    assert scorecard["summary"]["runtime_lineage_changed_key_count"] == 0
    assert scorecard["runtime_lineage"]["previous_source"] == "derived_from_transcript"
    assert scorecard["runtime_lineage"]["current_source"] == "derived_from_transcript"
    assert scorecard["missing_or_unavailable"]["previous"]["branch_divergence.json"] == "missing"
    assert scorecard["branch_divergence"]["previous_available"] is False


def test_compare_scenario_spine_reruns_reports_identity_mismatch(tmp_path: Path) -> None:
    previous = _fabricated_spine_artifact_dir(tmp_path / "previous", spine_id="spine_alpha", branch_id="branch_one")
    current = _fabricated_spine_artifact_dir(tmp_path / "current", spine_id="spine_beta", branch_id="branch_two")

    scorecard = _compare_mod.compare_scenario_spine_rerun_dirs(previous, current)

    assert scorecard["identity"]["mismatch"] is True
    assert scorecard["identity"]["mismatch_fields"] == ["spine_id", "branch_id"]
    assert scorecard["summary"]["identity_mismatch"] is True


def test_compare_scenario_spine_reruns_markdown_contains_operator_summary(tmp_path: Path) -> None:
    previous = _fabricated_spine_artifact_dir(tmp_path / "previous")
    current = _fabricated_spine_artifact_dir(
        tmp_path / "current",
        classification="degraded",
        score=70,
        speaker="guard",
        gm_text="The guard shifts the answer.",
    )

    scorecard = _compare_mod.compare_scenario_spine_rerun_dirs(previous, current)
    markdown = _compare_mod.render_scenario_spine_rerun_delta_markdown(scorecard)

    assert "# Scenario-Spine Rerun Delta Advisory" in markdown
    assert "## Operator Summary" in markdown
    assert "- Report only: `true`" in markdown
    assert "- Route / speaker / fallback deltas: `0` / `1` / `0`" in markdown
    assert "## Health Delta" in markdown
    assert "classification: `clean` -> `degraded`" in markdown


def test_compare_scenario_spine_reruns_cli_writes_markdown_and_json(tmp_path: Path) -> None:
    previous = _fabricated_spine_artifact_dir(tmp_path / "previous")
    current = _fabricated_spine_artifact_dir(tmp_path / "current", gm_text="A changed answer.")
    md_out = tmp_path / "rerun_delta.md"
    json_out = tmp_path / "rerun_delta.json"

    code = _compare_mod.main(
        [
            "--previous",
            str(previous),
            "--current",
            str(current),
            "--out",
            str(md_out),
            "--json-out",
            str(json_out),
        ],
    )

    assert code == 0
    assert "Scenario-Spine Rerun Delta Advisory" in md_out.read_text(encoding="utf-8")
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["summary"]["text_fingerprint_delta_count"] == 1


def test_effective_turn_limit_smoke_and_max_turns() -> None:
    assert _mod.effective_turn_limit(25, smoke=True, max_turns=None) == 5
    assert _mod.effective_turn_limit(25, smoke=True, max_turns=3) == 3
    assert _mod.effective_turn_limit(25, smoke=False, max_turns=10) == 10
    assert _mod.effective_turn_limit(8, smoke=True, max_turns=None) == 5


def test_build_operator_summary_includes_c1a_opening_convergence_section() -> None:
    eval_result = {
        "session_health": {
            "classification": "clean",
            "score": 100,
            "overall_passed": True,
            **_stub_metadata_session_health_fields(passed=True, checked=2, gaps=0),
            "opening_turns_checked": 2,
            "opening_plan_backed_count": 2,
            "opening_plan_missing_count": 0,
            "opening_invalid_plan_count": 0,
            "opening_anchor_grounding_failures": 0,
            "opening_stock_fallback_hits": 0,
            "opening_resume_entry_checked": 0,
            "opening_seam_failure_count": 0,
            "opening_convergence_verdict": "pass",
            "opening_repeated_generic_first_line": False,
            "opening_convergence_failure_details": [],
        },
        "axes": {
            "state_continuity": {"passed": True, "failure_codes": [], "warning_codes": []},
        },
        "detected_failures": [],
        "warnings": [],
    }
    md = _mod.build_operator_summary_md(
        spine_id="test_spine",
        branch_id="branch_x",
        spine_branch_turns=10,
        executed_turns=2,
        scope_label="smoke",
        eval_result=eval_result,
    )
    assert "## C1-A opening convergence (observational)" in md
    assert "**Pass**" in md
    assert "Opening turns checked" in md
    assert "Seam hard failures" in md
    assert "**Metadata completeness:**" in md
    assert "metadata" in md.lower()


def test_build_operator_summary_metadata_completeness_fail_line() -> None:
    from game.scenario_spine_eval import SCENARIO_SPINE_IDENTITY_KEYS, TRANSCRIPT_TURN_META_ENVELOPE_KEYS

    miss = {k: 0 for k in TRANSCRIPT_TURN_META_ENVELOPE_KEYS}
    miss["planner_convergence"] = 2
    eval_result = {
        "session_health": {
            "classification": "clean",
            "score": 100,
            "overall_passed": True,
            "metadata_completeness_passed": False,
            "turns_checked": 5,
            "turns_missing_meta": 2,
            "missing_by_key": miss,
            "first_missing_turn_by_key": {"planner_convergence": 1},
            "missing_scenario_spine_identity_by_key": {k: 0 for k in SCENARIO_SPINE_IDENTITY_KEYS},
            "first_missing_turn_by_scenario_spine_identity_key": {},
            "opening_turns_checked": 0,
            "opening_plan_backed_count": 0,
            "opening_plan_missing_count": 0,
            "opening_invalid_plan_count": 0,
            "opening_anchor_grounding_failures": 0,
            "opening_stock_fallback_hits": 0,
            "opening_resume_entry_checked": 0,
            "opening_seam_failure_count": 0,
            "opening_convergence_verdict": "no_observations",
            "opening_repeated_generic_first_line": False,
            "opening_convergence_failure_details": [],
        },
        "axes": {},
        "detected_failures": [],
        "warnings": [],
    }
    md = _mod.build_operator_summary_md(
        spine_id="test_spine",
        branch_id="branch_x",
        spine_branch_turns=10,
        executed_turns=5,
        scope_label="full",
        eval_result=eval_result,
    )
    assert "**Metadata completeness:**" in md
    assert "**fail**" in md
    assert "turns_with_gaps=2" in md
    assert "first_envelope_gap_turn_index=1" in md


def test_build_operator_summary_c1a_failure_table_rows() -> None:
    details = [
        {
            "turn_index": i,
            "opening_reason": "campaign_start",
            "scene_id": "s_gate",
            "marker": "plan_or_scene_opening_missing",
            "seam_failure_reason": None,
            "anchor_grounding_category": None,
            "suspected_source": "CTIR",
        }
        for i in range(20)
    ]
    eval_result = {
        "session_health": {
            "classification": "failed",
            "score": 10,
            "overall_passed": False,
            **_stub_metadata_session_health_fields(passed=True, checked=20, gaps=0),
            "opening_turns_checked": 20,
            "opening_plan_backed_count": 0,
            "opening_plan_missing_count": 20,
            "opening_invalid_plan_count": 0,
            "opening_anchor_grounding_failures": 0,
            "opening_stock_fallback_hits": 0,
            "opening_resume_entry_checked": 0,
            "opening_seam_failure_count": 0,
            "opening_convergence_verdict": "fail",
            "opening_repeated_generic_first_line": False,
            "opening_convergence_failure_details": details,
        },
        "axes": {},
        "detected_failures": [{"axis": "opening_convergence", "code": "x", "detail": "y"}],
        "warnings": [],
    }
    md = _mod.build_operator_summary_md(
        spine_id="test_spine",
        branch_id="branch_x",
        spine_branch_turns=20,
        executed_turns=20,
        scope_label="full",
        eval_result=eval_result,
    )
    assert "| Turn |" in md
    assert "more failure row" in md.lower()
    assert "| `11` |" in md
    assert "| `12` |" not in md


def test_artifacts_written_and_session_health_is_evaluator(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "apply_new_campaign_hard_reset", lambda: None)
    spine = _load_spine()
    br = next(b for b in spine.branches if b.branch_id == "branch_direct_intrusion")

    def chat(_text: str) -> dict:
        return {"ok": True, "gm_output": {"player_facing_text": "Gate serjeant nods. Missing patrol rumor deepens."}}

    run_dir = tmp_path / "run1"
    res = _mod.run_scenario_spine_branch(
        spine,
        br,
        branch_id_requested="branch_direct_intrusion",
        chat_call=chat,
        apply_reset=False,
        smoke=False,
        max_turns=None,
        run_dir=run_dir,
    )
    assert res.executed_turns == len(br.turns)
    for name in ("transcript.json", "session_health_summary.json", "run_debug.json", "compact_operator_summary.md"):
        assert (run_dir / name).is_file()

    health_path = run_dir / "session_health_summary.json"
    ev = json.loads(health_path.read_text(encoding="utf-8"))
    assert ev.get("schema_version") == 1
    assert ev.get("branch_id") == "branch_direct_intrusion"
    assert "session_health" in ev
    assert "axes" in ev
    assert ev["session_health"].get("metadata_completeness_passed") is True

    op_md = (run_dir / "compact_operator_summary.md").read_text(encoding="utf-8")
    assert "**Metadata completeness:**" in op_md


def _assert_transcript_meta_envelope(row: dict, *, spine_id: str, branch_id: str, smoke: bool, max_turns, resume: bool) -> None:
    assert "meta" in row
    m = row["meta"]
    assert isinstance(m, dict)
    for k in _mod.TRANSCRIPT_TURN_META_ENVELOPE_KEYS:
        assert k in m
    ss = m["scenario_spine"]
    assert isinstance(ss, dict)
    assert ss.get("spine_id") == spine_id
    assert ss.get("branch_id") == branch_id
    assert ss.get("turn_id") == row.get("turn_id")
    assert ss.get("turn_index") == row.get("turn_index")
    assert ss.get("smoke") is smoke
    assert ss.get("max_turns") == max_turns
    assert ss.get("resume_entry_first_turn") is resume
    assert ss.get("artifact_schema_version") == _mod.SCENARIO_SPINE_ARTIFACT_SCHEMA_VERSION


def test_transcript_turn_meta_stable_envelope(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "apply_new_campaign_hard_reset", lambda: None)
    _patch_session_storage(monkeypatch, tmp_path)
    spine = _load_spine()
    br = next(b for b in spine.branches if b.branch_id == "branch_direct_intrusion")

    def chat(_text: str) -> dict:
        return {"ok": True, "gm_output": {"player_facing_text": "Gate serjeant nods."}}

    run_dir = tmp_path / "env"
    _mod.run_scenario_spine_branch(
        spine,
        br,
        branch_id_requested=br.branch_id,
        chat_call=chat,
        apply_reset=False,
        smoke=True,
        max_turns=2,
        run_dir=run_dir,
        resume_entry_first_turn=True,
    )
    t = json.loads((run_dir / "transcript.json").read_text(encoding="utf-8"))
    dbg = json.loads((run_dir / "run_debug.json").read_text(encoding="utf-8"))
    for row in t["turns"]:
        _assert_transcript_meta_envelope(
            row,
            spine_id=spine.spine_id,
            branch_id=br.branch_id,
            smoke=True,
            max_turns=2,
            resume=True,
        )
    for row in dbg["turns_debug"]:
        _assert_transcript_meta_envelope(
            row,
            spine_id=spine.spine_id,
            branch_id=br.branch_id,
            smoke=True,
            max_turns=2,
            resume=True,
        )
        assert "gm_metadata_malformed_diagnostic" not in row


def test_transcript_meta_preserves_api_gm_metadata_keys(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "apply_new_campaign_hard_reset", lambda: None)
    spine = _load_spine()
    br = next(b for b in spine.branches if b.branch_id == "branch_cautious_observe")

    def chat(_text: str) -> dict:
        return {
            "ok": True,
            "gm_output": {
                "player_facing_text": "ok",
                "metadata": {
                    "custom_probe": {"x": 1},
                    "response_type_contract": {"required_response_type": "dialogue"},
                    "planner_convergence_report": {"ok": True, "probe": "from_api"},
                    "scenario_spine": {"extra_from_api": "keep_me"},
                },
            },
        }

    run_dir = tmp_path / "preserve"
    _mod.run_scenario_spine_branch(
        spine,
        br,
        branch_id_requested=br.branch_id,
        chat_call=chat,
        apply_reset=False,
        smoke=True,
        max_turns=1,
        run_dir=run_dir,
    )
    row = json.loads((run_dir / "transcript.json").read_text(encoding="utf-8"))["turns"][0]
    m = row["meta"]
    assert m.get("custom_probe") == {"x": 1}
    assert m.get("response_type_contract") == {"required_response_type": "dialogue"}
    assert m.get("planner_convergence") == {"ok": True, "probe": "from_api"}
    ss = m["scenario_spine"]
    assert ss.get("extra_from_api") == "keep_me"
    assert ss.get("spine_id") == spine.spine_id
    assert ss.get("branch_id") == br.branch_id


def test_transcript_meta_runtime_lineage_prefers_projected_bundle_and_projects_fem_fallback() -> None:
    spine = _load_spine()
    projected = {
        "event_type": "runtime_lineage",
        "event_kind": "speaker_repair",
        "stage": "gate",
        "owner": "game.speaker_contract_enforcement",
        "source": "contract",
        "gate_path": None,
        "mutation_kind": None,
        "fallback_kind": None,
        "repair_kind": "local_rebind",
        "recurrence_key": "speaker_repair:gate:game.speaker_contract_enforcement:local_rebind",
        "notes": [],
    }
    from_bundle = _mod.build_transcript_turn_meta(
        {
            "ok": True,
            "gm_output": {
                "player_facing_text": "ok",
                "metadata": {"observational_telemetry_bundle": {"fem_runtime_lineage_events": [projected]}},
                "_final_emission_meta": successful_opening_fem_meta(),
            },
        },
        spine=spine,
        branch_id_resolved="branch_direct_intrusion",
        turn_index=0,
        turn_id="turn_0",
        smoke=True,
        max_turns=1,
        resume_entry_first_turn=False,
    )
    assert from_bundle["runtime_lineage_events"] == [projected]

    projected_from_fem = _mod.build_transcript_turn_meta(
        {
            "ok": True,
            "gm_output": {
                "player_facing_text": "ok",
                "_final_emission_meta": successful_opening_fem_meta(),
            },
        },
        spine=spine,
        branch_id_resolved="branch_direct_intrusion",
        turn_index=0,
        turn_id="turn_0",
        smoke=True,
        max_turns=1,
        resume_entry_first_turn=False,
    )
    events = projected_from_fem["runtime_lineage_events"]
    fallback_selected = next(event for event in events if event["event_kind"] == "fallback_selected")
    assert fallback_selected["fallback_kind"] == "scene_opening"
    assert fallback_selected["owner"] == "game.final_emission_gate"
    assert fallback_selected["fallback_authorship_source"] == "upstream_prepared_opening_fallback"
    assert fallback_selected["fallback_owner_bucket"] == "upstream-prepared"
    assert any(event["event_kind"] == "gate_outcome" and event["gate_path"] == "opening_fallback" for event in events)
    assert json.loads(json.dumps(events)) == events

    projected_visibility_from_fem = _mod.build_transcript_turn_meta(
        {
            "ok": True,
            "gm_output": {
                "player_facing_text": "ok",
                "_final_emission_meta": {
                    "final_route": "replaced",
                    "final_emitted_source": "global_scene_fallback",
                    "visibility_replacement_applied": True,
                    "visibility_fallback_owner_bucket": "sealed-gate",
                    "visibility_fallback_pool": "global_scene_narrative",
                    "visibility_fallback_kind": "narrative_safe_fallback",
                    "sealed_fallback_owner_bucket": "sealed-gate",
                },
            },
        },
        spine=spine,
        branch_id_resolved="branch_direct_intrusion",
        turn_index=0,
        turn_id="turn_0",
        smoke=True,
        max_turns=1,
        resume_entry_first_turn=False,
    )
    visibility_events = projected_visibility_from_fem["runtime_lineage_events"]
    visibility_summary = _mod.build_runtime_lineage_summary(
        {"visibility": [{"meta": {"runtime_lineage_events": visibility_events}}]}
    )
    assert visibility_summary["fallback_frequency"] == {"visibility_hard_replacement": 1}
    assert visibility_summary["gate_path_frequency"] == {"visibility_hard_replaced": 1}

    empty = _mod.build_transcript_turn_meta(
        {"ok": True, "gm_output": {"player_facing_text": "ok"}},
        spine=spine,
        branch_id_resolved="branch_direct_intrusion",
        turn_index=0,
        turn_id="turn_0",
        smoke=True,
        max_turns=1,
        resume_entry_first_turn=False,
    )
    assert empty["runtime_lineage_events"] == []


def test_build_runtime_lineage_summary_counts_frequency_and_recurrence_without_scoring_fields() -> None:
    def event(kind: str, key: str, **fields) -> dict:
        return {"event_type": "runtime_lineage", "event_kind": kind, "stage": "gate", "recurrence_key": key, **fields}

    fallback = event(
        "fallback_selected",
        "fallback_selected:gate:owner:scene_opening",
        fallback_kind="scene_opening",
        fallback_authorship_source="upstream_prepared_opening_fallback",
        fallback_owner_bucket="upstream-prepared",
    )
    transcripts = {
        "branch_a": [
            {"meta": {"runtime_lineage_events": [fallback, event("gate_outcome", "gate_outcome:gate:owner:opening_fallback", gate_path="opening_fallback")]}},
        ],
        "branch_b": [
            {"meta": {"runtime_lineage_events": [
                fallback,
                event("speaker_repair", "speaker_repair:gate:owner:local_rebind", repair_kind="local_rebind"),
                event("mutation", "mutation:gate:owner:speaker_repair_mutation", mutation_kind="speaker_repair_mutation"),
            ]}},
        ],
    }
    summary = _mod.build_runtime_lineage_summary(transcripts)
    assert summary["total_events"] == 5
    assert summary["by_event_kind"] == {
        "fallback_selected": 2,
        "gate_outcome": 1,
        "mutation": 1,
        "speaker_repair": 1,
    }
    assert summary["by_stage"] == {"gate": 5}
    assert summary["by_recurrence_key"]["fallback_selected:gate:owner:scene_opening"] == 2
    assert summary["fallback_frequency"] == {"scene_opening": 2}
    assert summary["fallback_authorship_frequency"] == {"upstream_prepared_opening_fallback": 2}
    assert summary["fallback_owner_bucket_frequency"] == {"upstream-prepared": 2}
    assert summary["speaker_repair_frequency"] == {"local_rebind": 1}
    assert summary["mutation_kind_frequency"] == {"speaker_repair_mutation": 1}
    assert summary["gate_path_frequency"] == {"opening_fallback": 1}
    assert summary["recurring_events"] == [
        {"recurrence_key": "fallback_selected:gate:owner:scene_opening", "count": 2},
    ]
    assert "score" not in summary
    assert "overall_passed" not in summary


def test_scenario_spine_runtime_lineage_summary_uses_shared_reporting_surface() -> None:
    from tests.helpers.runtime_lineage_reporting import (
        build_runtime_lineage_summary_from_branch_transcripts,
        runtime_lineage_markdown_lines,
    )

    assert _mod.build_runtime_lineage_summary({}) == build_runtime_lineage_summary_from_branch_transcripts({})

    summary = _mod.build_runtime_lineage_summary(
        {
            "branch_a": [
                {
                    "meta": {
                        "runtime_lineage_events": [
                            {
                                "event_type": "runtime_lineage",
                                "event_kind": "fallback_selected",
                                "stage": "gate",
                                "fallback_kind": "scene_opening",
                            }
                        ]
                    }
                }
            ]
        }
    )
    markdown = "\n".join(runtime_lineage_markdown_lines(summary, profile="spine_aggregate"))
    assert "## Runtime Lineage Summary" in markdown
    assert "Top fallback kinds" in markdown
    assert "Top recurring recurrence keys" in markdown
    assert "Top fallback selection owners" not in markdown


def test_cycle_i_opening_attribution_survives_prepared_payload_gate_lineage_and_diagnostics() -> None:
    from tests.helpers.emission_smoke_assertions import apply_final_emission_gate_consumer
    from game.final_emission_meta import read_final_emission_meta_dict
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events
    from game.upstream_response_repairs import (
        UPSTREAM_PREPARED_OPENING_FALLBACK_KEY,
        build_upstream_prepared_opening_fallback_payload,
    )
    from tests.helpers.opening_fallback_evidence import (
        EXPECTED_FRONTIER_GATE_OPENING_FALLBACK,
        opening_gm_output,
    )

    successful_gm = opening_gm_output()
    prepared = build_upstream_prepared_opening_fallback_payload(successful_gm)
    successful_gm[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = prepared
    successful_gm["player_facing_text"] = "Nearby crates appear disturbed."
    successful_gm["tags"] = []
    successful, _ = apply_final_emission_gate_consumer(
        successful_gm,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    assert prepared["prepared_opening_fallback_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert successful["player_facing_text"] == prepared["prepared_opening_fallback_text"]

    successful_events = build_fem_runtime_lineage_events(read_final_emission_meta_dict(successful))
    successful_selected = next(event for event in successful_events if event["event_kind"] == "fallback_selected")
    assert successful_selected["fallback_kind"] == "scene_opening"
    assert successful_selected["owner"] == "game.final_emission_gate"
    assert successful_selected["fallback_authorship_source"] == "upstream_prepared_opening_fallback"
    assert successful_selected["fallback_owner_bucket"] == "upstream-prepared"
    assert any(
        event["event_kind"] == "gate_outcome" and event["gate_path"] == "opening_fallback"
        for event in successful_events
    )

    fail_closed_gm = opening_gm_output()
    fail_closed_gm["opening_curated_facts"] = []
    fail_closed_gm["opening_selector_selected_facts"] = []
    fail_closed_gm["player_facing_text"] = "Nearby crates appear disturbed."
    fail_closed_gm["tags"] = []
    fail_closed, _ = apply_final_emission_gate_consumer(
        fail_closed_gm,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    fail_closed_events = build_fem_runtime_lineage_events(read_final_emission_meta_dict(fail_closed))
    fail_closed_selected = next(event for event in fail_closed_events if event["event_kind"] == "fallback_selected")
    assert fail_closed_selected["fallback_kind"] == "opening_failed_closed"
    assert fail_closed_selected["owner"] == "game.final_emission_gate"
    assert fail_closed_selected["fallback_owner_bucket"] == "sealed-gate"
    assert fail_closed_selected["fallback_authorship_source"] is None
    assert fail_closed_selected["fallback_kind"] != successful_selected["fallback_kind"]

    summary = _mod.build_runtime_lineage_summary(
        {
            "successful": [{"meta": {"runtime_lineage_events": successful_events}}],
            "fail_closed": [{"meta": {"runtime_lineage_events": fail_closed_events}}],
        }
    )
    assert summary["fallback_frequency"] == {"opening_failed_closed": 1, "scene_opening": 1}
    assert summary["fallback_authorship_frequency"] == {"upstream_prepared_opening_fallback": 1}
    assert summary["fallback_owner_bucket_frequency"] == {"sealed-gate": 1, "upstream-prepared": 1}
    assert summary["gate_path_frequency"] == {"opening_failed_closed": 1, "opening_fallback": 1}

    md = _mod.build_aggregate_operator_summary_md(
        _load_spine(),
        {"spine_id": "cycle_i_contract", "runtime_lineage_summary": summary},
        [],
    )
    assert "`upstream_prepared_opening_fallback` (1)" in md
    assert "`upstream-prepared` (1)" in md
    assert "`sealed-gate` (1)" in md
    assert "`opening_fallback` (1)" in md


def test_malformed_gm_metadata_does_not_crash_transcript_json(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "apply_new_campaign_hard_reset", lambda: None)
    spine = _load_spine()
    br = next(b for b in spine.branches if b.branch_id == "branch_cautious_observe")

    def chat(_text: str) -> dict:
        return {
            "ok": True,
            "gm_output": {
                "player_facing_text": "ok",
                "metadata": "not-a-dict",
            },
        }

    run_dir = tmp_path / "badmd"
    _mod.run_scenario_spine_branch(
        spine,
        br,
        branch_id_requested=br.branch_id,
        chat_call=chat,
        apply_reset=False,
        smoke=True,
        max_turns=1,
        run_dir=run_dir,
    )
    row = json.loads((run_dir / "transcript.json").read_text(encoding="utf-8"))["turns"][0]
    assert isinstance(row["meta"], dict)
    assert row["meta"]["narration_seam"] is None
    dbg_row = json.loads((run_dir / "run_debug.json").read_text(encoding="utf-8"))["turns_debug"][0]
    assert dbg_row.get("gm_metadata_malformed_diagnostic") == "not-a-dict"


def test_api_failure_rows_degrade_without_crash(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "apply_new_campaign_hard_reset", lambda: None)
    spine = _load_spine()
    br = next(b for b in spine.branches if b.branch_id == "branch_cautious_observe")

    def chat(_text: str) -> dict:
        return {"ok": False, "error": "synthetic transport failure"}

    run_dir = tmp_path / "run2"
    res = _mod.run_scenario_spine_branch(
        spine,
        br,
        branch_id_requested="branch_cautious_observe",
        chat_call=chat,
        apply_reset=False,
        smoke=False,
        max_turns=4,
        run_dir=run_dir,
    )
    rows = json.loads((run_dir / "transcript.json").read_text(encoding="utf-8"))["turns"]
    assert all(r["api_ok"] is False for r in rows)
    cls = res.eval_result.get("session_health", {}).get("classification")
    assert cls in ("failed", "degraded", "warning")


def test_full_social_branch_mocked(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "apply_new_campaign_hard_reset", lambda: None)
    spine = _load_spine()
    br = next(b for b in spine.branches if b.branch_id == "branch_social_inquiry")
    n = len(br.turns)
    assert n >= 25

    def chat(text: str) -> dict:
        # Plausible diegetic stubs to avoid trivial evaluator tripwires on empty GM.
        body = (
            f"{text} — Cinderwatch Gate District, rain and notice board. "
            "Captain Thoran named; missing patrol route pressure; Ash Compact census choke; "
            "muddy prints northwest among crates; watch tightens at the gate."
        )
        return {"ok": True, "gm_output": {"player_facing_text": body}}

    run_dir = tmp_path / "run3"
    res = _mod.run_scenario_spine_branch(
        spine,
        br,
        branch_id_requested="branch_social_inquiry",
        chat_call=chat,
        apply_reset=False,
        smoke=False,
        max_turns=None,
        run_dir=run_dir,
    )
    assert res.executed_turns == n
    assert res.scope_label == "full"


def test_short_branches_accepted_explicit_and_all_branches(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "apply_new_campaign_hard_reset", lambda: None)
    spine = _load_spine()

    def chat(_text: str) -> dict:
        return {"ok": True, "gm_output": {"player_facing_text": "Scene holds; notice and patrol thread remain."}}

    for bid in ("branch_direct_intrusion", "branch_cautious_observe"):
        br = next(b for b in spine.branches if b.branch_id == bid)
        run_dir = tmp_path / bid
        _mod.run_scenario_spine_branch(
            spine,
            br,
            branch_id_requested=bid,
            chat_call=chat,
            apply_reset=False,
            smoke=False,
            max_turns=None,
            run_dir=run_dir,
        )
        assert (run_dir / "session_health_summary.json").exists()

    branches = sorted(spine.branches, key=lambda b: b.branch_id)
    stamp = "test_stamp"
    base = tmp_path / "all"
    for br in branches:
        run_dir = base / stamp / spine.spine_id / br.branch_id
        _mod.run_scenario_spine_branch(
            spine,
            br,
            branch_id_requested=br.branch_id,
            chat_call=chat,
            apply_reset=False,
            smoke=False,
            max_turns=None,
            run_dir=run_dir,
        )


def test_alias_resolves_fixture_id_in_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "apply_new_campaign_hard_reset", lambda: None)
    spine = _load_spine()
    br = _mod.get_branch(spine, "social_investigation")
    assert br is not None

    def chat(_text: str) -> dict:
        return {"ok": True, "gm_output": {"player_facing_text": "Captain Thoran and the notice board."}}

    run_dir = tmp_path / "alias"
    _mod.run_scenario_spine_branch(
        spine,
        br,
        branch_id_requested="social_investigation",
        chat_call=chat,
        apply_reset=False,
        smoke=True,
        max_turns=None,
        run_dir=run_dir,
    )
    t = json.loads((run_dir / "transcript.json").read_text(encoding="utf-8"))
    assert t["branch_id"] == "branch_social_inquiry"
    assert t["branch_id_requested"] == "social_investigation"


def test_transcript_excludes_raw_chat_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "apply_new_campaign_hard_reset", lambda: None)
    spine = _load_spine()
    br = next(b for b in spine.branches if b.branch_id == "branch_direct_intrusion")

    def chat(_text: str) -> dict:
        return {
            "ok": True,
            "gm_output": {"player_facing_text": "ok"},
            "session": {"secret": "x"},
        }

    run_dir = tmp_path / "t"
    _mod.run_scenario_spine_branch(
        spine,
        br,
        branch_id_requested="branch_direct_intrusion",
        chat_call=chat,
        apply_reset=False,
        smoke=True,
        max_turns=2,
        run_dir=run_dir,
    )
    raw = (run_dir / "transcript.json").read_text(encoding="utf-8")
    assert "secret" not in raw
    dbg = json.loads((run_dir / "run_debug.json").read_text(encoding="utf-8"))
    assert any("chat_response" in row for row in dbg.get("turns_debug", []))


def test_run_scenario_spine_branch_does_not_write_aggregate_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "apply_new_campaign_hard_reset", lambda: None)
    spine = _load_spine()
    br = next(b for b in spine.branches if b.branch_id == "branch_direct_intrusion")

    def chat(_text: str) -> dict:
        return {"ok": True, "gm_output": {"player_facing_text": "Gate holds."}}

    stamp = "single_stamp"
    run_dir = tmp_path / stamp / spine.spine_id / br.branch_id
    _mod.run_scenario_spine_branch(
        spine,
        br,
        branch_id_requested=br.branch_id,
        chat_call=chat,
        apply_reset=False,
        smoke=True,
        max_turns=None,
        run_dir=run_dir,
    )
    agg_dir = tmp_path / stamp / spine.spine_id
    assert not (agg_dir / "aggregate_session_health_summary.json").exists()
    assert not (agg_dir / "aggregate_operator_summary.md").exists()
    assert not (agg_dir / "runtime_lineage_summary.json").exists()


def test_all_branches_aggregate_artifacts_and_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "apply_new_campaign_hard_reset", lambda: None)
    spine = _load_spine()
    branches = sorted(spine.branches, key=lambda b: b.branch_id)

    lineage_event = {
        "event_type": "runtime_lineage",
        "event_kind": "fallback_selected",
        "stage": "gate",
        "owner": "game.final_emission_gate",
        "source": "selected_fallback",
        "fallback_kind": "scene_opening",
        "fallback_authorship_source": "upstream_prepared_opening_fallback",
        "fallback_owner_bucket": "upstream-prepared",
        "repair_kind": None,
        "mutation_kind": None,
        "gate_path": None,
        "recurrence_key": "fallback_selected:gate:game.final_emission_gate:scene_opening",
        "notes": [],
    }

    def chat(_text: str) -> dict:
        return {
            "ok": True,
            "gm_output": {
                "player_facing_text": "Scene holds; notice and patrol thread remain.",
                "metadata": {
                    "observational_telemetry_bundle": {"fem_runtime_lineage_events": [lineage_event]},
                },
            },
        }

    stamp = "agg_stamp"
    results = []
    for br in branches:
        run_dir = tmp_path / stamp / spine.spine_id / br.branch_id
        results.append(
            _mod.run_scenario_spine_branch(
                spine,
                br,
                branch_id_requested=br.branch_id,
                chat_call=chat,
                apply_reset=False,
                smoke=False,
                max_turns=None,
                run_dir=run_dir,
            ),
        )

    agg_dir = tmp_path / stamp / spine.spine_id
    ts = "2026-01-01T00:00:00+00:00"
    _mod.write_aggregate_spine_artifacts(
        spine,
        agg_dir,
        results,
        smoke=False,
        max_turns=None,
        run_timestamp=ts,
    )
    assert (agg_dir / "aggregate_session_health_summary.json").is_file()
    assert (agg_dir / "aggregate_operator_summary.md").is_file()
    assert (agg_dir / "runtime_lineage_summary.json").is_file()

    agg = json.loads((agg_dir / "aggregate_session_health_summary.json").read_text(encoding="utf-8"))
    assert agg.get("spine_id") == spine.spine_id
    assert agg.get("run_timestamp") == ts
    assert set(agg.get("branches_run") or []) == {b.branch_id for b in branches}
    expected_total = sum(len(b.turns) for b in branches)
    assert agg.get("total_executed_turns") == expected_total
    assert "degradation_over_time_by_branch" in agg
    deg = agg["degradation_over_time_by_branch"]
    assert isinstance(deg, dict)
    for bid in agg["branches_run"]:
        assert bid in deg
        assert "progressive_degradation_detected" in deg[bid]

    assert "branch_divergence" in agg
    div = agg["branch_divergence"]
    assert isinstance(div, dict)
    assert div.get("schema_version") == 1
    assert set(div.get("branches_compared") or []) == {b.branch_id for b in branches}
    lineage = agg["runtime_lineage_summary"]
    assert lineage["total_events"] == expected_total
    assert lineage["by_event_kind"] == {"fallback_selected": expected_total}
    assert lineage["fallback_frequency"] == {"scene_opening": expected_total}
    assert lineage["fallback_authorship_frequency"] == {"upstream_prepared_opening_fallback": expected_total}
    assert lineage["fallback_owner_bucket_frequency"] == {"upstream-prepared": expected_total}
    assert lineage["recurring_events"] == [
        {
            "recurrence_key": "fallback_selected:gate:game.final_emission_gate:scene_opening",
            "count": expected_total,
        },
    ]
    standalone_lineage = json.loads((agg_dir / "runtime_lineage_summary.json").read_text(encoding="utf-8"))
    assert standalone_lineage["spine_id"] == spine.spine_id
    assert standalone_lineage["total_events"] == expected_total
    assert standalone_lineage["fallback_frequency"] == {"scene_opening": expected_total}
    assert standalone_lineage["fallback_authorship_frequency"] == {"upstream_prepared_opening_fallback": expected_total}
    assert standalone_lineage["fallback_owner_bucket_frequency"] == {"upstream-prepared": expected_total}

    md = (agg_dir / "aggregate_operator_summary.md").read_text(encoding="utf-8")
    assert "aggregate" in md.lower()
    assert "branch_direct_intrusion" in md
    assert "Divergence" in md
    assert "Runtime Lineage Summary" in md
    assert f"**Total lineage events:** {expected_total}" in md
    assert f"`upstream_prepared_opening_fallback` ({expected_total})" in md
    assert f"`upstream-prepared` ({expected_total})" in md
    assert "| Metadata |" in md

    assert agg.get("coverage_band_met") is True
    meta = agg.get("aggregate_meta") or {}
    assert meta.get("coverage_turn_total_long_scripted_branches") == 50
    assert set(meta.get("long_scripted_branch_ids") or []) == {
        "branch_direct_intrusion",
        "branch_social_inquiry",
    }


def test_frontier_gate_long_branch_50_turn_advisory_aggregate_artifacts(tmp_path) -> None:
    spine = _load_spine()
    long_branch_ids = ("branch_direct_intrusion", "branch_social_inquiry")
    long_branches = [next(b for b in spine.branches if b.branch_id == bid) for bid in long_branch_ids]
    assert [len(branch.turns) for branch in long_branches] == [25, 25]

    stamp = "u9_advisory_aggregate"
    aggregate_dir = tmp_path / stamp / spine.spine_id
    results = []
    for branch in long_branches:
        branch_dir = aggregate_dir / branch.branch_id
        branch_dir.mkdir(parents=True, exist_ok=True)
        lineage_event = {
            "event_type": "runtime_lineage",
            "event_kind": "gate_outcome",
            "stage": "gate",
            "owner": "tests.advisory_aggregate",
            "source": "mocked_transcript",
            "gate_path": f"{branch.branch_id}_path",
            "fallback_kind": None,
            "fallback_authorship_source": None,
            "fallback_owner_bucket": None,
            "repair_kind": None,
            "mutation_kind": None,
            "recurrence_key": f"gate_outcome:gate:tests.advisory_aggregate:{branch.branch_id}",
            "notes": [],
        }
        turns = [
            {
                "turn_index": idx,
                "turn_id": turn.turn_id,
                "player_prompt": turn.player_prompt,
                "gm_text": (
                    f"{branch.branch_id} advisory aggregate turn {idx}: Cinderwatch Gate, notice board, "
                    "Captain Thoran, Ash Compact census pressure, missing patrol route, muddy crates, "
                    "and branch-specific consequence remain visible."
                ),
                "api_ok": True,
                "meta": {
                    "runtime_lineage_events": [lineage_event],
                },
            }
            for idx, turn in enumerate(branch.turns)
        ]
        (branch_dir / "transcript.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "spine_id": spine.spine_id,
                    "branch_id": branch.branch_id,
                    "turn_count": len(turns),
                    "turns": turns,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        eval_result = {
            "session_health": {
                "turn_count": 25,
                "scripted_turn_count": 25,
                "full_length_branch": True,
                "classification": "clean",
                "score": 100,
                "overall_passed": True,
                **_stub_metadata_session_health_fields(passed=True, checked=25, gaps=0),
            },
            "degradation_over_time": {
                "progressive_degradation_detected": False,
                "reason_codes": [],
                "early_window": {"signals": []},
                "middle_window": {"signals": []},
                "late_window": {"signals": []},
            },
            "detected_failures": [],
            "warnings": [],
            "axes": {
                "branch_coherence": {"passed": True, "failure_codes": [], "warning_codes": []},
                "narrative_grounding": {"passed": True, "failure_codes": [], "warning_codes": []},
            },
        }
        results.append(
            _mod.BranchRunResult(
                branch_id_requested=branch.branch_id,
                branch_id_resolved=branch.branch_id,
                run_dir=branch_dir,
                eval_result=eval_result,
                executed_turns=25,
                spine_branch_turns=25,
                scope_label="full",
            ),
        )

    _mod.write_aggregate_spine_artifacts(
        spine,
        aggregate_dir,
        results,
        smoke=False,
        max_turns=None,
        run_timestamp="2026-05-30T00:00:00+00:00",
    )

    aggregate_path = aggregate_dir / "aggregate_session_health_summary.json"
    lineage_path = aggregate_dir / "runtime_lineage_summary.json"
    operator_path = aggregate_dir / "aggregate_operator_summary.md"
    assert aggregate_path.is_file()
    assert lineage_path.is_file()
    assert operator_path.is_file()

    aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
    assert aggregate["branches_run"] == list(long_branch_ids)
    assert aggregate["branch_turn_counts"] == {
        "branch_direct_intrusion": 25,
        "branch_social_inquiry": 25,
    }
    assert aggregate["total_executed_turns"] == 50
    assert aggregate["long_branch_count"] == 2
    assert aggregate["coverage_band_met"] is True
    assert aggregate["all_full_length_branches_passed"] is True
    assert aggregate["aggregate_meta"]["coverage_turn_total_long_scripted_branches"] == 50
    assert aggregate["aggregate_meta"]["long_scripted_branch_ids"] == list(long_branch_ids)
    assert aggregate["aggregate_meta"]["long_targets_complete"] is True
    assert aggregate["aggregate_meta"]["long_targets_all_passed"] is True
    assert set(aggregate["degradation_over_time_by_branch"]) == set(long_branch_ids)
    assert all(
        aggregate["degradation_over_time_by_branch"][bid]["progressive_degradation_detected"] is False
        for bid in long_branch_ids
    )
    assert set(aggregate["branch_divergence"]["branches_compared"]) == set(long_branch_ids)
    assert "divergence_score" in aggregate["branch_divergence"]
    assert aggregate["runtime_lineage_summary"]["total_events"] == 50
    assert aggregate["runtime_lineage_summary"]["by_event_kind"] == {"gate_outcome": 50}

    standalone_lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
    assert standalone_lineage["branches_run"] == list(long_branch_ids)
    assert standalone_lineage["total_events"] == 50

    md = operator_path.read_text(encoding="utf-8")
    assert "branch_direct_intrusion" in md
    assert "branch_social_inquiry" in md
    assert "**Total executed turns (all branches):** 50" in md
    assert "40–60 turn band" in md
    assert "## Divergence (cross-branch)" in md
    assert "## Runtime Lineage Summary" in md
    assert "## Degradation (per branch)" in md


def test_all_branches_aggregate_smoke_does_not_claim_coverage_band(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "apply_new_campaign_hard_reset", lambda: None)
    spine = _load_spine()
    branches = sorted(spine.branches, key=lambda b: b.branch_id)

    def chat(_text: str) -> dict:
        return {"ok": True, "gm_output": {"player_facing_text": "Stub."}}

    stamp = "smoke_agg"
    results = []
    for br in branches:
        run_dir = tmp_path / stamp / spine.spine_id / br.branch_id
        results.append(
            _mod.run_scenario_spine_branch(
                spine,
                br,
                branch_id_requested=br.branch_id,
                chat_call=chat,
                apply_reset=False,
                smoke=True,
                max_turns=None,
                run_dir=run_dir,
            ),
        )
    agg = _mod.build_aggregate_session_health_summary(
        spine,
        results,
        smoke=True,
        max_turns=None,
        run_timestamp="2026-01-02T00:00:00+00:00",
    )
    assert agg.get("coverage_band_met") is False
    assert agg.get("total_executed_turns") == 15
