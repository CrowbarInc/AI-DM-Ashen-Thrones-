"""Live manual-play pipeline tests for :mod:`game.planner_convergence` (Block B)."""

from __future__ import annotations

from typing import Any

import pytest

import game.api as api_mod
from game.api import _build_gpt_narration_from_authoritative_state
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY
from game.defaults import default_campaign, default_character, default_session, default_world
from game.narration_plan_bundle import SESSION_NARRATION_PLAN_BUNDLE_STAMP_KEY
from game.planner_convergence import planner_convergence_ok
from game.storage import get_scene_runtime

pytestmark = pytest.mark.unit


def _base_kw(*, resolution: dict, normalized_action: dict | None = None, route_choice: str | None = None) -> dict[str, Any]:
    session = default_session()
    session["turn_counter"] = 5
    session["active_scene_id"] = "t_scene"
    session.setdefault("scene_runtime", {})
    world = default_world()
    scene = {
        "scene": {
            "id": "t_scene",
            "location": "Yard",
            "summary": "Open ground.",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
        }
    }
    na = normalized_action if normalized_action is not None else {"type": str(resolution.get("kind") or "observe")}
    return {
        "campaign": default_campaign(),
        "world": world,
        "session": session,
        "character": default_character(),
        "scene": scene,
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": str(resolution.get("prompt") or "x"),
        "resolution": resolution,
        "scene_runtime": get_scene_runtime(session, "t_scene"),
        "segmented_turn": None,
        "route_choice": route_choice,
        "directed_social_entry": None,
        "response_type_contract": None,
        "latency_sink": None,
        "normalized_action": na,
    }


def _last_debug_op(session: dict, operation: str) -> dict | None:
    traces = session.get("debug_traces") if isinstance(session.get("debug_traces"), list) else []
    for t in reversed(traces):
        if isinstance(t, dict) and t.get("operation") == operation:
            return t
    return None


def test_action_outcome_convergence_report_matches_session_stamps(monkeypatch: pytest.MonkeyPatch) -> None:
    resolution = {"kind": "observe", "prompt": "Look.", "success": True, "metadata": {}}
    kw = _base_kw(resolution=resolution)

    def fake_gpt(_m: list, **_k: Any) -> dict[str, Any]:
        return {
            "player_facing_text": "You look.",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
            "metadata": {},
        }

    monkeypatch.setattr(api_mod, "call_gpt", fake_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_k: [])
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)
    out = _build_gpt_narration_from_authoritative_state(**kw)
    rep = (out.get("metadata") or {}).get("planner_convergence_report")
    assert isinstance(rep, dict)
    assert rep.get("path_label") == "action_outcome"
    assert rep.get("stamp_matches") is True
    assert planner_convergence_ok(rep) is True
    sess = kw["session"]
    assert rep.get("ctir_stamp") == str(sess.get(SESSION_CTIR_STAMP_KEY) or "")
    assert rep.get("narrative_plan_stamp") == str(sess.get(SESSION_NARRATION_PLAN_BUNDLE_STAMP_KEY) or "")


def test_dialogue_social_path_label_and_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    resolution = {
        "kind": "question",
        "prompt": "Who guards the gate?",
        "success": True,
        "social": {"npc_id": "npc_gate"},
        "metadata": {},
    }
    kw = _base_kw(resolution=resolution, route_choice="dialogue")

    def fake_gpt(*_a: Any, **_k: Any) -> dict[str, Any]:
        return {
            "player_facing_text": "The sergeant shrugs.",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
            "metadata": {},
        }

    monkeypatch.setattr(api_mod, "call_gpt", fake_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_k: [])
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)
    out = _build_gpt_narration_from_authoritative_state(**kw)
    rep = (out.get("metadata") or {}).get("planner_convergence_report")
    assert isinstance(rep, dict)
    assert rep.get("path_label") == "dialogue_social"
    assert planner_convergence_ok(rep) is True


def test_exposition_answer_path_label_and_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    resolution = {
        "kind": "adjudication_query",
        "prompt": "What is the DC?",
        "success": True,
        "metadata": {},
    }
    kw = _base_kw(resolution=resolution, normalized_action=None)

    def fake_gpt(*_a: Any, **_k: Any) -> dict[str, Any]:
        return {
            "player_facing_text": "The DC is 15.",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
            "metadata": {},
        }

    monkeypatch.setattr(api_mod, "call_gpt", fake_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_k: [])
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)
    out = _build_gpt_narration_from_authoritative_state(**kw)
    rep = (out.get("metadata") or {}).get("planner_convergence_report")
    assert isinstance(rep, dict)
    assert rep.get("path_label") == "exposition_answer"
    assert planner_convergence_ok(rep) is True


def test_transition_path_label_and_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    resolution = {
        "kind": "travel",
        "prompt": "We go north.",
        "success": True,
        "resolved_transition": True,
        "target_scene_id": "other",
        "metadata": {},
    }
    kw = _base_kw(resolution=resolution, normalized_action={"type": "travel"})

    def fake_gpt(*_a: Any, **_k: Any) -> dict[str, Any]:
        return {
            "player_facing_text": "The road opens.",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
            "metadata": {},
        }

    monkeypatch.setattr(api_mod, "call_gpt", fake_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_k: [])
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)
    out = _build_gpt_narration_from_authoritative_state(**kw)
    rep = (out.get("metadata") or {}).get("planner_convergence_report")
    assert isinstance(rep, dict)
    assert rep.get("path_label") == "transition"
    assert planner_convergence_ok(rep) is True


def test_missing_narrative_plan_skips_build_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    bm_calls: list[int] = []

    def counting_build_messages(*_a: Any, **_k: Any) -> list[dict[str, str]]:
        bm_calls.append(1)
        return [{"role": "system", "content": "x"}, {"role": "user", "content": "{}"}]

    def bad_plan_bundle(**_kwargs: Any) -> dict[str, Any]:
        return {
            "plan_metadata": {"ctir_stamp": ""},
            "narrative_plan": None,
            "renderer_inputs": {},
        }

    monkeypatch.setattr(api_mod, "build_messages", counting_build_messages)
    monkeypatch.setattr(api_mod, "build_narration_plan_bundle", bad_plan_bundle)
    monkeypatch.setattr(api_mod, "call_gpt", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("GPT must not run")))
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)

    resolution = {"kind": "observe", "prompt": "Look.", "success": True, "metadata": {}}
    kw = _base_kw(resolution=resolution)
    out = _build_gpt_narration_from_authoritative_state(**kw)
    assert bm_calls == []
    assert _last_debug_op(kw["session"], "emergency_nonplan_output") is not None
    seam = (out.get("metadata") or {}).get("narration_seam") or {}
    assert seam.get("path_kind") == "resolved_turn_ctir_planner_convergence_seam"


def test_retry_preserves_ctir_and_bundle_stamp_params(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_verify(
        session: dict,
        *,
        expected_ctir_stamp: str,
        owner_module: str,
        expected_narration_plan_bundle_stamp: str | None = None,
    ) -> bool:
        captured["ctir"] = expected_ctir_stamp
        captured["bundle"] = expected_narration_plan_bundle_stamp
        return True

    monkeypatch.setattr(api_mod, "verify_same_turn_narration_stamp_for_retry", fake_verify)
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_k: [{"failure_class": "validator_voice", "priority": 20, "reasons": ["x"]}])
    monkeypatch.setattr(api_mod, "choose_retry_strategy", lambda f: f[0] if f else None)
    monkeypatch.setattr(api_mod, "build_retry_prompt_for_failure", lambda *_a, **_k: "retry")
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)

    def fake_gpt(messages: list, **_k: Any) -> dict[str, Any]:
        if len(messages) <= 2:
            return {
                "player_facing_text": "TRIGGER_VALIDATOR",
                "tags": [],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": "",
                "metadata": {},
            }
        return {
            "player_facing_text": "Steadied narration.",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
            "metadata": {},
        }

    monkeypatch.setattr(api_mod, "call_gpt", fake_gpt)
    resolution = {"kind": "observe", "prompt": "Look.", "success": True, "metadata": {}}
    kw = _base_kw(resolution=resolution)
    _build_gpt_narration_from_authoritative_state(**kw)
    assert captured.get("ctir") == captured.get("bundle")
    assert len(str(captured.get("ctir") or "")) > 3


def test_convergence_emergency_registers_explicit_nonplan_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    bm_calls: list[int] = []

    def counting_build_messages(*_a: Any, **_k: Any) -> list[dict[str, str]]:
        bm_calls.append(1)
        return [{"role": "system", "content": "x"}, {"role": "user", "content": "{}"}]

    monkeypatch.setattr(api_mod, "build_messages", counting_build_messages)
    monkeypatch.setattr(api_mod, "build_narration_plan_bundle", lambda **_k: {
        "plan_metadata": {},
        "narrative_plan": None,
        "renderer_inputs": {},
    })
    monkeypatch.setattr(api_mod, "call_gpt", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("no gpt")))
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)

    resolution = {"kind": "observe", "prompt": "Look.", "success": True, "metadata": {}}
    kw = _base_kw(resolution=resolution)
    _build_gpt_narration_from_authoritative_state(**kw)
    assert bm_calls == []
    em = _last_debug_op(kw["session"], "emergency_nonplan_output")
    assert isinstance(em, dict)
    assert em.get("reason") == "planner_convergence_seam_failure"

