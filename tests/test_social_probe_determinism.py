"""Deterministic conversational contracts for classified social_probe moves (no new topic row)."""
from __future__ import annotations

from game.clues import _social_resolution_carries_information
from game.defaults import default_character, default_world
from game.narration_state_consistency import reconcile_final_text_with_structured_state
from game.social import classify_social_probe_move, resolve_social_action
from game.storage import get_npc_runtime


import pytest

pytestmark = pytest.mark.integration

def _npc_rt(session: dict, npc_id: str) -> dict:
    return get_npc_runtime(session, npc_id)


def test_classify_social_probe_move_families() -> None:
    assert classify_social_probe_move(
        player_text="For stew and stories!",
        segmented_turn=None,
        current_target_id="tavern_runner",
        current_topic_key=None,
    )["probe_move"] == "transactional"
    assert classify_social_probe_move(
        player_text="Tell me more.",
        segmented_turn=None,
        current_target_id=None,
        current_topic_key=None,
    )["probe_move"] == "followup"
    assert classify_social_probe_move(
        player_text="But you haven't told me anything at all!",
        segmented_turn=None,
        current_target_id="guard_captain",
        current_topic_key=None,
    )["probe_move"] == "challenge"
    assert classify_social_probe_move(
        player_text="Where should I start?",
        segmented_turn=None,
        current_target_id="refugee",
        current_topic_key=None,
    )["probe_move"] == "directional"


def test_transactional_probe_after_runner_topic_exhausted_yields_redirect_contract() -> None:
    world = default_world()
    scene = {"scene": {"id": "frontier_gate"}}
    session: dict = {}
    char = default_character()
    ask = {
        "id": "q-runner",
        "label": "Ask runner",
        "type": "question",
        "prompt": "What's the word on the stew?",
        "target_id": "tavern_runner",
    }
    r0 = resolve_social_action(scene, session, world, ask, raw_player_text=ask["prompt"], character=char, turn_counter=1)
    assert r0["success"] is True
    probe = {
        "id": "p-runner",
        "label": "Stew offer",
        "type": "social_probe",
        "prompt": "For stew and stories!",
        "target_id": "tavern_runner",
    }
    r1 = resolve_social_action(
        scene, session, world, probe, raw_player_text="For stew and stories!", character=char, turn_counter=2
    )
    soc = r1["social"]
    assert soc["social_probe_move"] == "transactional"
    assert soc["reply_kind"] == "explanation"
    assert r1["success"] is True
    assert soc["npc_reply_expected"] is True
    assert soc.get("social_probe_engine_contract") is True
    assert "no new information was revealed" not in (r1.get("hint") or "").lower()
    assert _social_resolution_carries_information(r1)


def test_refugee_followup_probe_is_guarded_explicit_not_generic_reaction() -> None:
    world = default_world()
    world["npcs"] = list(world.get("npcs") or [])
    world["npcs"].append(
        {
            "id": "refugee",
            "name": "Ragged stranger",
            "location": "frontier_gate",
            "disposition": "wary",
            "topics": [],
        }
    )
    scene = {"scene": {"id": "frontier_gate"}}
    session: dict = {}
    probe = {
        "id": "p-ref",
        "label": "More",
        "type": "social_probe",
        "prompt": "Tell me more.",
        "target_id": "refugee",
    }
    r = resolve_social_action(
        scene, session, world, probe, raw_player_text="Tell me more.", character=default_character(), turn_counter=1
    )
    soc = r["social"]
    assert soc["social_probe_move"] == "followup"
    assert soc["reply_kind"] == "explanation"
    assert soc["npc_reply_expected"] is True
    assert soc["reply_kind"] != "reaction"
    assert soc.get("probe_outcome") == "guarded_continuation"
    assert "no new information was revealed" not in (r.get("hint") or "").lower()


def test_challenge_probe_after_guard_prior_answer_not_generic_reaction() -> None:
    world = default_world()
    scene = {"scene": {"id": "frontier_gate"}}
    session: dict = {}
    char = default_character()
    ask = {
        "id": "q-guard",
        "label": "Patrol",
        "type": "question",
        "prompt": "What about the missing patrol?",
        "target_id": "guard_captain",
    }
    resolve_social_action(scene, session, world, ask, raw_player_text=ask["prompt"], character=char, turn_counter=1)
    probe = {
        "id": "p-guard",
        "label": "Push",
        "type": "social_probe",
        "prompt": "You haven't told me anything at all!",
        "target_id": "guard_captain",
    }
    r = resolve_social_action(
        scene,
        session,
        world,
        probe,
        raw_player_text="You haven't told me anything at all!",
        character=char,
        turn_counter=2,
    )
    soc = r["social"]
    assert soc["social_probe_move"] == "challenge"
    assert soc["reply_kind"] != "reaction"
    assert soc["npc_reply_expected"] is True
    assert r["success"] is True
    assert soc.get("probe_outcome") == "friction_or_explicit_limit"
    assert int(_npc_rt(session, "guard_captain").get("suspicion") or 0) >= 1
    assert "no new information was revealed" not in (r.get("hint") or "").lower()


def test_directional_probe_prefers_actionable_lead_contract() -> None:
    world = default_world()
    world["npcs"] = list(world.get("npcs") or [])
    world["npcs"].append(
        {
            "id": "refugee",
            "name": "Ragged stranger",
            "location": "frontier_gate",
            "disposition": "wary",
            "topics": [],
        }
    )
    scene = {"scene": {"id": "frontier_gate"}}
    session: dict = {}
    probe = {
        "id": "p-dir",
        "label": "Where start",
        "type": "social_probe",
        "prompt": "Where should I start?",
        "target_id": "refugee",
    }
    r = resolve_social_action(
        scene, session, world, probe, raw_player_text="Where should I start?", character=default_character(), turn_counter=1
    )
    soc = r["social"]
    assert soc["social_probe_move"] == "directional"
    assert soc["reply_kind"] == "explanation"
    assert soc.get("probe_outcome") == "actionable_lead_or_redirect"
    assert "no new information was revealed" not in (r.get("hint") or "").lower()


def test_narration_reconcile_does_not_scrub_when_engine_hint_already_substantive() -> None:
    """Probe contract sets informational resolution; sharpened narration should not trigger empty-payload repair."""
    session: dict = {}
    world = default_world()
    scene = {"scene": {"id": "frontier_gate"}}
    res = {
        "kind": "social_probe",
        "success": True,
        "clue_id": None,
        "discovered_clues": [],
        "hint": (
            "Tavern Runner should treat this as a concrete offer (coin, meal, favor) and answer with either "
            "a partial honest detail they are willing to sell *or* a sharp redirect"
        ),
        "social": {
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "target_resolved": True,
            "topic_revealed": None,
            "reply_kind": "explanation",
            "social_probe_engine_contract": True,
            "social_probe_move": "transactional",
            "probe_outcome": "actionable_redirect",
        },
        "requires_check": False,
    }
    assert _social_resolution_carries_information(res)
    gm = {
        "player_facing_text": (
            'The runner pockets the coin without smiling. "Start at the notice board—then ask the watch sergeant."'
        ),
        "tags": [],
        "debug_notes": "no new information was revealed | gm_note",
    }
    meta = reconcile_final_text_with_structured_state(
        session=session, scene=scene, world=world, resolution=res, gm_output=gm
    )
    assert meta.get("mismatch_repair_applied") == "none"
    assert "no new information was revealed" in (gm.get("debug_notes") or "").lower()
