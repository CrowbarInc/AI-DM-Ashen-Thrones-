"""Strict-social terminal fallback: dialogue continuity under retry exhaustion (18a block 2)."""
from __future__ import annotations

from typing import Any

import pytest

from game.defaults import default_scene, default_session, default_world
from game.final_emission_gate import apply_final_emission_gate
from game.gm import (
    ensure_minimal_social_resolution,
    force_terminal_retry_fallback,
    repair_strict_social_terminal_dialogue_fallback_if_needed,
    strict_social_terminal_dialogue_fallback_valid,
)
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.narration_visibility import validate_player_facing_first_mentions
from game.social_exchange_emission import lawful_strict_social_dialogue_emergency_fallback_line
from game.storage import get_scene_runtime

pytestmark = pytest.mark.unit


def _dialogue_contract_resolution(*, npc_id: str = "tavern_runner") -> dict[str, Any]:
    return {
        "kind": "question",
        "metadata": {
            "response_type_contract": {"required_response_type": "dialogue"},
        },
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": npc_id,
            "npc_name": "Tavern Runner",
            "npc_reply_expected": True,
            "reply_kind": "answer",
            "target_resolved": True,
        },
    }


def _session(*, npc_id: str = "tavern_runner") -> dict[str, Any]:
    return {
        "interaction_context": {
            "active_interaction_target_id": npc_id,
            "interaction_mode": "social",
        }
    }


def _world() -> dict[str, Any]:
    return {
        "npcs": [
            {"id": "tavern_runner", "name": "Tavern Runner", "location": "scene_investigate"},
        ]
    }


def _scene_env() -> dict[str, Any]:
    return {"scene": {"id": "scene_investigate"}}


def test_strict_social_retry_exhaustion_emits_dialogue_presence(monkeypatch: Any) -> None:
    """Forced retry fallback with dialogue contract yields quoted NPC speech."""
    monkeypatch.setattr("game.gm.apply_social_exchange_retry_fallback_gm", lambda *a, **k: {})

    def _bad_minimal(_res: Any) -> str:
        return "Tavern Runner answers with visible caution."

    monkeypatch.setattr("game.gm.minimal_social_emergency_fallback_line", _bad_minimal)

    out = force_terminal_retry_fallback(
        session=_session(),
        original_text="",
        failure={"failure_class": "scene_stall", "reasons": ["stall"]},
        player_text="What did you hear?",
        scene_envelope=_scene_env(),
        world=_world(),
        resolution=_dialogue_contract_resolution(),
        base_gm={
            "player_facing_text": "",
            "tags": [],
            "response_policy": {"response_type_contract": {"required_response_type": "dialogue"}},
        },
    )
    text = str(out.get("player_facing_text") or "")
    assert '"' in text
    assert "tavern runner" in text.lower()
    assert strict_social_terminal_dialogue_fallback_valid(text, _dialogue_contract_resolution())


def test_grounded_interlocutor_remains_speaker() -> None:
    """Active interlocutor matches resolution NPC; repair attributes speech to that speaker."""
    res = _dialogue_contract_resolution()
    text, did = repair_strict_social_terminal_dialogue_fallback_if_needed(
        "Tavern Runner answers with visible caution.",
        resolution=res,
        base_gm={"response_policy": {"response_type_contract": {"required_response_type": "dialogue"}}},
        session=_session(),
        world=_world(),
        scene_id="scene_investigate",
        retry_terminal=True,
    )
    assert did is True
    assert "tavern runner" in text.lower()
    assert '"' in text


def test_interruption_bridge_rejected_and_replaced() -> None:
    """Interruption-shaped emergency text fails validation; lawful repair is dialogue-shaped."""
    res = _dialogue_contract_resolution()
    bad = (
        "Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd."
    )
    assert strict_social_terminal_dialogue_fallback_valid(bad, res) is False
    fixed = lawful_strict_social_dialogue_emergency_fallback_line(res)
    assert strict_social_terminal_dialogue_fallback_valid(fixed, res) is True
    assert "crowd" not in fixed.lower()


def test_non_dialogue_contract_skips_repair() -> None:
    """Answer (non-dialogue) contract does not invoke strict-social dialogue terminal repair."""
    res = _dialogue_contract_resolution()
    res["metadata"] = {"response_type_contract": {"required_response_type": "answer"}}
    original = "Tavern Runner answers with visible caution."
    text, did = repair_strict_social_terminal_dialogue_fallback_if_needed(
        original,
        resolution=res,
        base_gm={},
        session=_session(),
        world=_world(),
        scene_id="scene_investigate",
        retry_terminal=True,
    )
    assert did is False
    assert text == original


def test_strict_social_terminal_fallback_grimace_line_survives_first_mention_gate() -> None:
    """Lawful terminal dialogue without lexical grounding cue passes final gate when speaker is grounded."""
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "focused"
    session["interaction_context"] = ic
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "What did you hear?"
    res = _dialogue_contract_resolution()
    text = 'Tavern Runner grimaces. "Not something I can say here."'
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": []},
        resolution=res,
        session=session,
        scene_id=sid,
        world=world,
        scene=default_scene(sid),
    )
    assert "grimaces" in out["player_facing_text"].lower()
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("first_mention_validation_passed") is True
    assert meta.get("first_mention_replacement_applied") is False
    assert meta.get("first_mention_strict_social_grounded_speaker_exemption_entity_id") == "tavern_runner"


def test_first_mention_grounding_exemption_requires_flag_grimace_fails_without_it() -> None:
    """Without exemption, grimace-only attribution fails first-mention grounding; with entity id, it passes."""
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    scene = default_scene(sid)
    text = 'Tavern Runner grimaces. "Not something I can say here."'
    no_ex = validate_player_facing_first_mentions(
        text,
        session=session,
        scene=scene,
        world=world,
    )
    assert no_ex.get("ok") is False
    assert any(
        isinstance(v, dict) and v.get("kind") == "first_mention_missing_grounding"
        for v in (no_ex.get("violations") or [])
    )
    with_ex = validate_player_facing_first_mentions(
        text,
        session=session,
        scene=scene,
        world=world,
        grounded_speaker_first_mention_exemption_entity_id="tavern_runner",
    )
    assert with_ex.get("ok") is True


def test_grounding_exemption_does_not_bypass_unearned_familiarity() -> None:
    """Grounded-speaker exemption applies only to missing grounding, not familiarity violations."""
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    scene = default_scene(sid)
    text = "Tavern Runner stands near the gate; you recognize him immediately."
    r = validate_player_facing_first_mentions(
        text,
        session=session,
        scene=scene,
        world=world,
        grounded_speaker_first_mention_exemption_entity_id="tavern_runner",
    )
    assert r.get("ok") is False
    kinds = [v.get("kind") for v in (r.get("violations") or []) if isinstance(v, dict)]
    assert "first_mention_unearned_familiarity" in kinds


def test_retry_terminal_repaired_dialogue_survives_first_mention_gate(monkeypatch: Any) -> None:
    """After terminal dialogue repair (retry_terminal), final emission does not re-replace for grounding."""
    monkeypatch.setattr("game.gm.apply_social_exchange_retry_fallback_gm", lambda *a, **k: {})

    res = _dialogue_contract_resolution()
    repaired, did = repair_strict_social_terminal_dialogue_fallback_if_needed(
        "Tavern Runner answers with visible caution.",
        resolution=res,
        base_gm={"response_policy": {"response_type_contract": {"required_response_type": "dialogue"}}},
        session=_session(),
        world=_world(),
        scene_id="scene_investigate",
        retry_terminal=True,
    )
    assert did is True
    assert strict_social_terminal_dialogue_fallback_valid(repaired, res) is True

    session = default_session()
    world = _world()
    sid = "scene_investigate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid, scene_envelope=_scene_env())
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "focused"
    session["interaction_context"] = ic
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Who saw it?"
    out = apply_final_emission_gate(
        {"player_facing_text": repaired, "tags": ["targeted_retry_terminal"]},
        resolution=res,
        session=session,
        scene_id=sid,
        world=world,
        scene=_scene_env(),
    )
    assert '"' in out["player_facing_text"]
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("first_mention_replacement_applied") is False
    assert meta.get("first_mention_validation_passed") is True


def test_ensure_minimal_social_repairs_stall_bridge_for_dialogue_contract(monkeypatch: Any) -> None:
    """ensure_minimal_social_resolution applies dialogue repair when contextual line is stall-only."""
    monkeypatch.setattr("game.gm.minimal_social_emergency_fallback_line", lambda *_a, **_k: "")

    def _ctx_social(*, gm: Any, session: Any, world: Any = None) -> tuple[str, str]:
        return "Tavern Runner answers with visible caution.", "question_ack"

    monkeypatch.setattr("game.gm_retry._contextual_social_repair_line", _ctx_social)

    out = ensure_minimal_social_resolution(
        gm={"player_facing_text": "", "tags": []},
        session=_session(),
        reason="test_ctx_bridge",
        world=_world(),
        resolution=_dialogue_contract_resolution(),
        scene_envelope=_scene_env(),
        player_text="Who saw it?",
    )
    text = str(out.get("player_facing_text") or "")
    assert '"' in text
    assert "strict_social_dialogue_terminal_repair" in str(out.get("debug_notes") or "")
