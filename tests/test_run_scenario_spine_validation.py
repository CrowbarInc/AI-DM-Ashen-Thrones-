"""Tests for ``tools/run_scenario_spine_validation.py`` (no live model; no OpenAI)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

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

FIXTURE = _ROOT / "data" / "validation" / "scenario_spines" / "frontier_gate_long_session.json"


def _load_spine():
    spine, errs = _mod.load_spine(FIXTURE)
    assert errs == []
    return spine


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


def test_all_branches_aggregate_artifacts_and_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_mod, "apply_new_campaign_hard_reset", lambda: None)
    spine = _load_spine()
    branches = sorted(spine.branches, key=lambda b: b.branch_id)

    def chat(_text: str) -> dict:
        return {"ok": True, "gm_output": {"player_facing_text": "Scene holds; notice and patrol thread remain."}}

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

    md = (agg_dir / "aggregate_operator_summary.md").read_text(encoding="utf-8")
    assert "aggregate" in md.lower()
    assert "branch_direct_intrusion" in md
    assert "Divergence" in md
    assert "| Metadata |" in md

    assert agg.get("coverage_band_met") is True
    meta = agg.get("aggregate_meta") or {}
    assert meta.get("coverage_turn_total_long_scripted_branches") == 50
    assert set(meta.get("long_scripted_branch_ids") or []) == {
        "branch_direct_intrusion",
        "branch_social_inquiry",
    }


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
