"""C1 regression harness: CTIR → narration plan bundle → prompt_context seam contract."""

from __future__ import annotations

from typing import Any

import pytest

import game.api as api_mod
from game import ctir
from game.api import _build_gpt_narration_from_authoritative_state
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.defaults import default_campaign, default_character, default_session, default_world
from game.narration_plan_bundle import attach_narration_plan_bundle
from game.narration_seam_guards import (
    NARRATION_PATH_MATRIX,
    REGISTERED_NARRATION_PATH_KINDS,
    annotate_narration_path_kind,
    require_narration_plan_bundle_for_ctir_turn,
    verify_same_turn_narration_stamp_for_retry,
)
from game.prompt_context import build_narration_context
from game.storage import get_scene_runtime
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests

pytestmark = pytest.mark.unit

# Must stay aligned with ``game.prompt_context.build_narration_context`` (anti-second-planner gate).
_INTERLOCUTOR_SCENE_RECAP_A = (
    "Prioritize the active conversation over general scene recap."
)
_INTERLOCUTOR_SCENE_RECAP_B = (
    "Do not fall back to base scene description unless the location materially changes, "
    "a new threat emerges, the player explicitly surveys the environment, or the scene needs a transition beat."
)


def _narration_kw() -> dict[str, Any]:
    session = default_session()
    session["turn_counter"] = 3
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
    resolution = {"kind": "observe", "prompt": "Look around.", "success": True, "metadata": {}}
    return {
        "campaign": default_campaign(),
        "world": world,
        "session": session,
        "character": default_character(),
        "scene": scene,
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": resolution["prompt"],
        "resolution": resolution,
        "scene_runtime": get_scene_runtime(session, "t_scene"),
        "segmented_turn": None,
        "route_choice": None,
        "directed_social_entry": None,
        "response_type_contract": None,
        "latency_sink": None,
        "normalized_action": {"type": "observe"},
    }


def _last_trace_operation(session: dict[str, Any], operation: str) -> dict[str, Any] | None:
    traces = session.get("debug_traces") if isinstance(session.get("debug_traces"), list) else []
    for t in reversed(traces):
        if isinstance(t, dict) and t.get("operation") == operation:
            return t
    return None


def test_resolved_turn_success_seam_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    """Normal resolved turn: CTIR-backed, bundle-required, plan-driven; correct path_kind."""

    def fake_call_gpt(_messages: list[dict[str, str]], **_kwargs: Any) -> dict[str, Any]:
        return {
            "player_facing_text": "You study the yard.",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
            "metadata": {},
        }

    monkeypatch.setattr(api_mod, "call_gpt", fake_call_gpt)
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)

    kw = _narration_kw()
    session = kw["session"]
    session["debug_traces"] = []
    out = _build_gpt_narration_from_authoritative_state(**kw)
    seam = (out.get("metadata") or {}).get("narration_seam") or {}
    assert seam.get("path_kind") == "resolved_turn_ctir_bundle"
    assert seam.get("ctir_backed") is True
    assert seam.get("bundle_required") is True
    assert seam.get("plan_driven") is True
    assert seam.get("emergency_nonplan_output") is False
    assert session.get(SESSION_CTIR_STAMP_KEY)
    assert isinstance(session.get("_runtime_narration_plan_bundle_v1"), dict)
    bundle = session["_runtime_narration_plan_bundle_v1"]
    assert isinstance(bundle.get("narrative_plan"), dict)


def test_bundle_requirement_negative_emits_semantic_bypass_blocked() -> None:
    session: dict[str, Any] = {"debug_traces": []}
    stamp = "1:abc:def"
    session[SESSION_CTIR_STAMP_KEY] = stamp
    attach_ctir(session, {"version": 1, "semantics": {"x": 1}})
    # Stamp aligned but bundle body missing → ``bundle_absent`` (not stamp_mismatch from empty stamp).
    session["_runtime_narration_plan_bundle_stamp_v1"] = stamp
    out = require_narration_plan_bundle_for_ctir_turn(session, turn_stamp=stamp, owner_module=__name__)
    assert out["ok"] is False
    assert out.get("error") == "bundle_absent"
    tr = _last_trace_operation(session, "semantic_bypass_blocked")
    assert tr is not None
    assert tr.get("reason") == "bundle_absent"
    detach_ctir(session)


def test_bundle_requirement_negative_stamp_mismatch() -> None:
    session: dict[str, Any] = {"debug_traces": []}
    stamp = "1:abc:def"
    session[SESSION_CTIR_STAMP_KEY] = stamp
    attach_ctir(session, {"version": 1, "semantics": {}})
    attach_narration_plan_bundle(
        session,
        {
            "plan_metadata": {"ctir_stamp": stamp},
            "narrative_plan": {"narrative_mode": "continuation"},
            "renderer_inputs": {},
        },
    )
    session["_runtime_narration_plan_bundle_stamp_v1"] = "other-stamp"
    out = require_narration_plan_bundle_for_ctir_turn(session, turn_stamp=stamp, owner_module=__name__)
    assert out["ok"] is False
    assert out.get("error") == "narration_plan_bundle_stamp_mismatch"
    tr = _last_trace_operation(session, "semantic_bypass_blocked")
    assert tr is not None
    assert tr.get("reason") == "narration_plan_bundle_stamp_mismatch"
    detach_ctir(session)


def test_bundle_requirement_negative_missing_narrative_plan() -> None:
    session: dict[str, Any] = {"debug_traces": []}
    stamp = "1:abc:def"
    session[SESSION_CTIR_STAMP_KEY] = stamp
    attach_ctir(session, {"version": 1, "semantics": {}})
    attach_narration_plan_bundle(
        session,
        {
            "plan_metadata": {"ctir_stamp": stamp, "semantic_bypass_blocked": True},
            "narrative_plan": None,
            "renderer_inputs": {},
        },
    )
    session["_runtime_narration_plan_bundle_stamp_v1"] = stamp
    out = require_narration_plan_bundle_for_ctir_turn(session, turn_stamp=stamp, owner_module=__name__)
    assert out["ok"] is False
    assert out.get("error") == "narrative_plan_missing"
    tr = _last_trace_operation(session, "semantic_bypass_blocked")
    assert tr is not None
    assert tr.get("reason") == "narrative_plan_missing"
    detach_ctir(session)


def test_prompt_context_mandatory_narrative_plan_audit_visible() -> None:
    """CTIR present but stamp-matched bundle missing narrative_plan → seam audit, not silent."""
    base = {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": {},
        "session": {
            "active_scene_id": "s1",
            "turn_counter": 2,
            "visited_scene_ids": ["s1"],
            "interaction_context": {
                "active_interaction_target_id": "npc_a",
                "active_interaction_kind": "dialogue",
                "interaction_mode": "directed",
            },
        },
        "character": {"name": "Hero", "hp": {}, "ac": {}},
        "scene": {"scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []}},
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": "Hello.",
        "resolution": {"kind": "social", "label": "x"},
        "scene_runtime": {},
        "public_scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []},
        "discoverable_clues": [],
        "gm_only_hidden_facts": [],
        "gm_only_discoverable_locked": [],
        "discovered_clue_records": [],
        "undiscovered_clue_records": [],
        "pending_leads": [],
        "intent": {"labels": ["general"], "allow_discoverable_clues": True},
        "world_state_view": {"flags": {}, "counters": {}, "clocks_summary": []},
        "mode_instruction": "Standard.",
        "recent_log_for_prompt": [],
    }
    session = dict(base["session"])
    stamp = "audit_stamp_v1"
    session[SESSION_CTIR_STAMP_KEY] = stamp
    c = ctir.build_ctir(
        turn_id=2,
        scene_id="s1",
        player_input="Hello.",
        builder_source="tests.c1.audit_visible",
        intent={"raw_text": "Hello.", "labels": ["general"], "mode": "activity"},
        resolution={"kind": "social", "label": "x"},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    attach_ctir(session, c)
    attach_narration_plan_bundle(
        session,
        {
            "plan_metadata": {"ctir_stamp": stamp, "narration_plan_bundle_error": "synthetic_test_missing_plan"},
            "narrative_plan": None,
            "renderer_inputs": {},
        },
    )
    session["_runtime_narration_plan_bundle_stamp_v1"] = stamp
    try:
        payload = build_narration_context(**{**base, "session": session})
    finally:
        detach_ctir(session)
    audit = payload.get("narration_seam_audit")
    assert isinstance(audit, dict)
    assert audit.get("narrative_plan_mandatory_seam") is True
    assert audit.get("semantic_bypass_blocked") is True
    assert payload.get("narrative_plan") in (None, {})


def test_build_gpt_annotates_seam_failure_not_plan_driven(monkeypatch: pytest.MonkeyPatch) -> None:
    """If bundle seam verification fails, GM metadata must not claim a normal plan-driven success path."""

    def fake_call_gpt(_messages: list[dict[str, str]], **_kwargs: Any) -> dict[str, Any]:
        return {
            "player_facing_text": "Fallback narration.",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
            "metadata": {},
        }

    monkeypatch.setattr(api_mod, "call_gpt", fake_call_gpt)
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)

    def boom_require(*_a: Any, **_k: Any) -> dict[str, Any]:
        return {"ok": False, "error": "synthetic_contract_test"}

    monkeypatch.setattr(api_mod, "require_narration_plan_bundle_for_ctir_turn", boom_require)

    kw = _narration_kw()
    out = _build_gpt_narration_from_authoritative_state(**kw)
    seam = (out.get("metadata") or {}).get("narration_seam") or {}
    assert seam.get("plan_driven") is False
    assert seam.get("emergency_nonplan_output") is True
    extra = seam.get("extra") or {}
    assert extra.get("bundle_seam_requirement_failed") is True


def test_same_turn_retry_stable_stamp_ok() -> None:
    session: dict[str, Any] = {"debug_traces": []}
    session[SESSION_CTIR_STAMP_KEY] = "turn-stamp-z"
    assert verify_same_turn_narration_stamp_for_retry(
        session, expected_ctir_stamp="turn-stamp-z", owner_module=__name__
    )
    assert _last_trace_operation(session, "semantic_bypass_blocked") is None


def test_same_turn_retry_ctir_stamp_drift_surfaces() -> None:
    session: dict[str, Any] = {"debug_traces": []}
    session[SESSION_CTIR_STAMP_KEY] = "drifted"
    ok = verify_same_turn_narration_stamp_for_retry(
        session, expected_ctir_stamp="expected-stamp", owner_module=__name__
    )
    assert ok is False
    tr = _last_trace_operation(session, "semantic_bypass_blocked")
    assert tr is not None
    assert tr.get("reason") == "same_turn_retry_ctir_stamp_drift"
    assert tr.get("expected") == "expected-stamp"
    assert tr.get("current") == "drifted"


def test_path_matrix_contract_rows_present() -> None:
    """Lightweight lock: matrix must retain C1 contract rows (prevents silent rot)."""
    joined = " ".join(str(r.get("path")) for r in NARRATION_PATH_MATRIX).lower()
    assert "resolved_turn_ctir_bundle" in joined
    assert "resolved_turn_ctir_upstream_fast_fallback" in joined or "force_terminal" in joined
    assert "chat procedural" in joined
    assert "manual_play" in joined or "budget exceeded" in joined
    assert "engine" in joined


def test_registered_path_kinds_cover_matrix_intent() -> None:
    assert "resolved_turn_ctir_bundle" in REGISTERED_NARRATION_PATH_KINDS
    assert "non_resolution_model_narration" in REGISTERED_NARRATION_PATH_KINDS
    assert "manual_play_gpt_budget_exceeded" in REGISTERED_NARRATION_PATH_KINDS
    assert "engine_check_required_prompt" in REGISTERED_NARRATION_PATH_KINDS


def test_path_kind_contract_significant_fields() -> None:
    """Contract-significant flags for representative runtime path_kinds (mirrors matrix intent)."""
    cases: tuple[tuple[str, dict[str, Any]], ...] = (
        (
            "resolved_turn_ctir_bundle",
            {
                "ctir_backed": True,
                "bundle_required": True,
                "plan_driven": True,
                "emergency_nonplan_output": False,
            },
        ),
        (
            "resolved_turn_ctir_upstream_fast_fallback",
            {
                "ctir_backed": True,
                "bundle_required": True,
                "plan_driven": False,
                "emergency_nonplan_output": True,
            },
        ),
        (
            "resolved_turn_ctir_force_terminal_fallback",
            {
                "ctir_backed": True,
                "bundle_required": True,
                "plan_driven": False,
                "emergency_nonplan_output": True,
            },
        ),
        (
            "non_resolution_model_narration",
            {
                "ctir_backed": False,
                "bundle_required": False,
                "plan_driven": False,
                "emergency_nonplan_output": False,
            },
        ),
        (
            "manual_play_gpt_budget_exceeded",
            {
                "ctir_backed": False,
                "bundle_required": False,
                "plan_driven": False,
                "emergency_nonplan_output": True,
            },
        ),
        (
            "engine_check_required_prompt",
            {
                "ctir_backed": False,
                "bundle_required": False,
                "plan_driven": False,
                "emergency_nonplan_output": False,
            },
        ),
    )
    for path_kind, expected in cases:
        gm: dict[str, Any] = {"metadata": {}}
        annotate_narration_path_kind(
            gm,
            path_kind=path_kind,
            ctir_backed=expected["ctir_backed"],
            bundle_required=expected["bundle_required"],
            plan_driven=expected["plan_driven"],
            emergency_nonplan_output=expected["emergency_nonplan_output"],
            explicit_nonplan_model_narration=(path_kind == "non_resolution_model_narration"),
        )
        seam = gm["metadata"]["narration_seam"]
        assert seam["path_kind"] == path_kind
        for k, v in expected.items():
            assert seam[k] is v, f"{path_kind}: {k}"


def test_c1_narration_seam_audit_tool_ok() -> None:
    from tools.c1_narration_seam_audit import run_c1_narration_seam_audit

    out = run_c1_narration_seam_audit()
    assert out["ok"], out["issues"]


def test_prompt_context_no_interlocutor_recap_pair_when_plan_driven_ctir() -> None:
    """CTIR + narrative_plan present → local interlocutor-vs-scene recap pair must not compete with the plan."""
    session = {
        "active_scene_id": "s1",
        "turn_counter": 2,
        "visited_scene_ids": ["s1"],
        "interaction_context": {
            "active_interaction_target_id": "npc_gate",
            "active_interaction_kind": "dialogue",
            "interaction_mode": "directed",
        },
    }
    c = ctir.build_ctir(
        turn_id=2,
        scene_id="s1",
        player_input="Press the guard.",
        builder_source="tests.c1.no_recap_pair",
        intent={"raw_text": "Press the guard.", "labels": ["general"], "mode": "activity"},
        resolution={"kind": "social", "label": "strict"},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    attach_ctir(session, c)
    if not str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip():
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"
    kw = {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": {},
        "session": session,
        "character": {"name": "Hero", "hp": {}, "ac": {}},
        "scene": {"scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []}},
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": "Press the guard.",
        "resolution": {"kind": "social", "label": "strict"},
        "scene_runtime": {},
        "public_scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []},
        "discoverable_clues": [],
        "gm_only_hidden_facts": [],
        "gm_only_discoverable_locked": [],
        "discovered_clue_records": [],
        "undiscovered_clue_records": [],
        "pending_leads": [],
        "intent": {"labels": ["general"], "allow_discoverable_clues": True},
        "world_state_view": {"flags": {}, "counters": {}, "clocks_summary": []},
        "mode_instruction": "Standard.",
        "recent_log_for_prompt": [],
    }
    ensure_narration_plan_bundle_for_manual_ctir_tests(session, kw)
    try:
        payload = build_narration_context(**kw)
    finally:
        detach_ctir(session)
    assert isinstance(payload.get("narrative_plan"), dict)
    instr = " ".join(payload.get("instructions") or [])
    assert _INTERLOCUTOR_SCENE_RECAP_A not in instr
    assert _INTERLOCUTOR_SCENE_RECAP_B not in instr


def test_prompt_context_interlocutor_recap_pair_without_narrative_plan() -> None:
    """No CTIR / no narrative_plan: local recap shaping remains available (non-plan path)."""
    session = {
        "active_scene_id": "s1",
        "turn_counter": 2,
        "visited_scene_ids": ["s1"],
        "interaction_context": {
            "active_interaction_target_id": "npc_gate",
            "active_interaction_kind": "dialogue",
            "interaction_mode": "directed",
        },
    }
    payload = build_narration_context(
        campaign={"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        world={},
        session=session,
        character={"name": "Hero", "hp": {}, "ac": {}},
        scene={"scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []}},
        combat={"in_combat": False},
        recent_log=[],
        user_text="What do you see?",
        resolution=None,
        scene_runtime={},
        public_scene={"id": "s1", "visible_facts": [], "exits": [], "enemies": []},
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["general"], "allow_discoverable_clues": True},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=[],
    )
    assert payload.get("narrative_plan") is None
    instr = " ".join(payload.get("instructions") or [])
    assert _INTERLOCUTOR_SCENE_RECAP_A in instr
    assert _INTERLOCUTOR_SCENE_RECAP_B in instr


def test_helpers_marked_non_production() -> None:
    from tests.helpers import ctir_narration_bundle as h

    src = h.__doc__ or ""
    assert "non-production" in src.lower() or "Non-production" in src
    assert "ensure_narration_plan_bundle_for_manual_ctir_tests" in dir(h)
