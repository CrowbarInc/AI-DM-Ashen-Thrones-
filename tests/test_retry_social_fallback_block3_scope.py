"""Block #3: gate deterministic social-shaped retry fallbacks using Block #1 world-action signals."""

from __future__ import annotations

from game.campaign_state import create_fresh_session_document
from game.gm import (
    apply_deterministic_retry_fallback,
    detect_retry_failures,
    force_terminal_retry_fallback,
    inspect_retry_social_answer_fallback_scope,
)
from game.interaction_context import (
    evaluate_world_action_social_continuity_break,
    rebuild_active_scene_entities,
    world_action_turn_suppresses_npc_answer_fallback,
)
from game.gm_retry import prioritize_retry_failures_for_social_answer_candidate
from game.storage import load_scene

import pytest

pytestmark = pytest.mark.unit


def _gate_session_scene():
    session = create_fresh_session_document()
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    st = session["scene_state"]
    st["active_entities"] = ["guard_captain", "tavern_runner", "refugee", "threadbare_watcher"]
    st.setdefault("entity_presence", {})
    st["entity_presence"].update({e: "active" for e in st["active_entities"]})
    world = {
        "npcs": [
            {"id": "guard_captain", "name": "Guard Captain", "location": "frontier_gate"},
            {"id": "tavern_runner", "name": "Runner", "location": "frontier_gate"},
        ]
    }
    scene = load_scene("frontier_gate")
    scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    return session, scene, world


def _bind_guard_social(session: dict) -> None:
    ctx = session.setdefault("interaction_context", {})
    ctx["active_interaction_target_id"] = "guard_captain"
    ctx["active_interaction_kind"] = "social"
    ctx["interaction_mode"] = "social"
    ctx["engagement_level"] = "engaged"


def test_block1_retry_signal_matches_canonical_when_interlocutor_active():
    session, scene, world = _gate_session_scene()
    _bind_guard_social(session)
    text = "Where does he end up?"
    sup = world_action_turn_suppresses_npc_answer_fallback(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    can = evaluate_world_action_social_continuity_break(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=None,
        raw_text=text,
    )
    assert sup is True
    assert can is True


def test_world_action_follow_up_rejects_social_exchange_retry_fallback():
    """After disengagement semantics: stale strict resolution must not select NPC deterministic social retry."""
    session, scene, world = _gate_session_scene()
    session.setdefault("interaction_context", {})["active_interaction_target_id"] = ""
    session["interaction_context"]["interaction_mode"] = "activity"
    resolution = {
        "kind": "question",
        "prompt": "Where does he end up?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "guard_captain",
            "npc_name": "Guard Captain",
            "target_resolved": True,
            "npc_reply_expected": True,
        },
    }
    out = apply_deterministic_retry_fallback(
        {"player_facing_text": "The air is tense.", "tags": []},
        failure={"failure_class": "unresolved_question", "reasons": ["test"]},
        player_text="Where does he end up?",
        scene_envelope=scene,
        session=session,
        world=world,
        resolution=resolution,
        segmented_turn=None,
    )
    tags = [str(t).lower() for t in (out.get("tags") or []) if isinstance(t, str)]
    assert "social_exchange_retry_fallback" not in tags
    dbg = str(out.get("debug_notes") or "")
    assert "retry_fallback_chosen:nonsocial_uncertainty_pool_after_block1_social_out_of_scope" in dbg
    assert "retry_social_fallback_scope:block1_signal=True" in dbg


def test_detect_retry_failures_suppresses_recent_dialogue_known_fact_under_block1_signal(monkeypatch):
    from game import gm_retry as gr

    def _fake_resolve(pt, **kwargs):
        return {
            "text": "The runner is by the east arch.",
            "source": "recent_dialogue_continuity",
            "subject": "runner",
            "position": "east arch",
            "speaker": {"role": "narrator", "name": ""},
        }

    monkeypatch.setattr(gr, "resolve_known_fact_before_uncertainty", _fake_resolve)
    session, scene, world = _gate_session_scene()
    _bind_guard_social(session)
    failures = detect_retry_failures(
        player_text="What do we see ahead?",
        gm_reply={"player_facing_text": "Mist and banners.", "tags": []},
        scene_envelope=scene,
        session=session,
        world=world,
        resolution={"kind": "question", "social": {"social_intent_class": "social_exchange"}},
        segmented_turn=None,
    )
    uq = [f for f in failures if isinstance(f, dict) and f.get("failure_class") == "unresolved_question"]
    assert uq
    assert "known_fact_context" not in uq[0]
    assert uq[0].get("retry_social_known_fact_carry_suppressed") == "block1_world_action_signal"


def test_force_terminal_skips_minimal_social_when_block1_signal(monkeypatch):
    monkeypatch.setattr(
        "game.gm.apply_social_exchange_retry_fallback_gm",
        lambda *a, **k: {"player_facing_text": "", "tags": []},
    )
    session, scene, world = _gate_session_scene()
    ctx = session.setdefault("interaction_context", {})
    ctx["active_interaction_target_id"] = "guard_captain"
    ctx["interaction_mode"] = "social"
    ctx["active_interaction_kind"] = "social"
    session["player_input"] = "Where does he end up?"
    resolution = {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "guard_captain",
            "target_resolved": True,
        },
    }
    out = force_terminal_retry_fallback(
        session=session,
        original_text="",
        failure={"failure_class": "unresolved_question", "reasons": ["t"]},
        player_text="Where does he end up?",
        scene_envelope=scene,
        world=world,
        resolution=resolution,
        base_gm={"player_facing_text": "", "tags": []},
        segmented_turn=None,
    )
    dbg = str(out.get("debug_notes") or "")
    assert "retry_terminal_skipped_social_terminal:block1_world_action_signal" in dbg
    low = (out.get("player_facing_text") or "").lower()
    assert "they answer cautiously" not in low


def test_same_npc_in_scope_question_allows_social_exchange_retry_fallback():
    session, scene, world = _gate_session_scene()
    _bind_guard_social(session)
    resolution = {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "guard_captain",
            "npc_name": "Guard Captain",
            "target_resolved": True,
            "npc_reply_expected": True,
        },
    }
    out = apply_deterministic_retry_fallback(
        {"player_facing_text": "vague", "tags": []},
        failure={"failure_class": "unresolved_question", "reasons": ["test"]},
        player_text="Who sent them?",
        scene_envelope=scene,
        session=session,
        world=world,
        resolution=resolution,
    )
    tags = [str(t).lower() for t in (out.get("tags") or []) if isinstance(t, str)]
    assert "social_exchange_retry_fallback" in tags or "known_fact_guard" in tags
    dbg = str(out.get("debug_notes") or "")
    assert "social_shaped_in_scope=True" in dbg


def test_open_social_narrator_known_fact_still_wins(monkeypatch):
    import game.gm_retry as gm_retry_mod

    monkeypatch.setattr(
        gm_retry_mod,
        "resolve_known_fact_before_uncertainty",
        lambda *a, **k: {
            "text": "Posted notice: patrol east.",
            "source": "notice_board",
            "speaker": {"role": "narrator", "name": ""},
        },
    )
    session, scene, world = _gate_session_scene()
    resolution = {
        "kind": "question",
        "social": {
            "social_intent_class": "open_call",
            "open_social_solicitation": True,
            "candidate_addressable_ids": ["tavern_runner", "guard_captain"],
            "target_resolved": False,
            "npc_reply_expected": False,
        },
    }
    out = apply_deterministic_retry_fallback(
        {"player_facing_text": "vague", "tags": []},
        failure={"failure_class": "unresolved_question", "reasons": ["test"]},
        player_text="What does the notice say?",
        scene_envelope=scene,
        session=session,
        world=world,
        resolution=resolution,
    )
    tags = [str(t).lower() for t in (out.get("tags") or []) if isinstance(t, str)]
    assert "known_fact_guard" in tags
    assert "open_social_recovery" not in tags


def test_prioritize_social_answer_skipped_when_block1_signal():
    session, scene, world = _gate_session_scene()
    _bind_guard_social(session)
    resolution = {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "guard_captain",
        },
    }
    failures = [{"failure_class": "scene_stall", "priority": 40, "reasons": ["x"]}]
    out, dbg = prioritize_retry_failures_for_social_answer_candidate(
        failures,
        player_text="What do we see ahead?",
        resolution=resolution,
        session=session,
        scene_envelope=scene,
        world=world,
    )
    assert out == failures
    assert dbg.get("retry_social_answer_priority_skipped") == "block1_world_action_signal"


def test_inspect_retry_scope_exposes_debug_fields():
    session, scene, world = _gate_session_scene()
    _bind_guard_social(session)
    info = inspect_retry_social_answer_fallback_scope(
        player_text="Who sent them?",
        scene_envelope=scene,
        session=session,
        world=world,
    )
    assert info.get("retry_social_fallback_considered") is True
    assert info.get("social_shaped_fallback_in_scope") is True
    assert info.get("block1_world_action_signal") is False
