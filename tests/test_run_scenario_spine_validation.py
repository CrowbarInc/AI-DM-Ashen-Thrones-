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
