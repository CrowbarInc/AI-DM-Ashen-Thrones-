"""Narration vs deterministic resolution alignment (Block 5)."""
from __future__ import annotations

from game.clues import _social_resolution_carries_information, get_all_known_clue_ids
from game.defaults import default_world
from game.narration_state_consistency import (
    detect_narration_state_mismatch,
    reconcile_final_text_with_structured_state,
)


import pytest

pytestmark = pytest.mark.unit

def _scene_envelope(scene_id: str) -> dict:
    return {"scene": {"id": scene_id}}


def _empty_question_resolution(*, hint_has_no_new_info: bool = True) -> dict:
    hint = (
        "Player spoke with Guard. No new information was revealed. Narrate refusal."
        if hint_has_no_new_info
        else "Player asked the guard something. Narrate the reply."
    )
    return {
        "kind": "question",
        "action_id": "q",
        "label": "Ask",
        "prompt": "Ask",
        "success": None,
        "clue_id": None,
        "discovered_clues": [],
        "hint": hint,
        "social": {
            "npc_id": "gate_guard",
            "npc_name": "Gate Guard",
            "target_resolved": True,
            "topic_revealed": None,
            "social_intent_class": "social_exchange",
        },
        "requires_check": False,
    }


def test_refusal_text_with_location_repair_updates_state_and_clues():
    session: dict = {}
    world = default_world()
    scene = _scene_envelope("frontier_gate")
    res = _empty_question_resolution()
    gm = {
        "player_facing_text": (
            "The guard shrugs. \"I don't know names—but ask around the old trading crossroads; "
            "that's where the talk gathers.\""
        ),
        "tags": [],
    }

    assert not _social_resolution_carries_information(res)

    meta = detect_narration_state_mismatch(
        resolution=res,
        gm_output=gm,
        session=session,
        scene=scene,
        world=world,
    )

    assert meta["narration_state_mismatch_detected"] is True
    assert meta["mismatch_repair_applied"] == "extracted_actionable_leads"
    assert "canonical_social_lead_landing" in (meta.get("mismatch_repairs_applied") or [])
    assert _social_resolution_carries_information(res)
    assert res.get("success") is True
    assert "no new information was revealed" not in (res.get("hint") or "").lower()
    assert get_all_known_clue_ids(session)


def test_explanation_with_directional_hook_not_left_as_empty_payload():
    session: dict = {}
    world = default_world()
    scene = _scene_envelope("gate")
    res = _empty_question_resolution()
    gm = {
        "player_facing_text": 'The runner hesitates. "I cannot say more—go to the captain of the watch."',
        "tags": [],
    }

    meta = detect_narration_state_mismatch(
        resolution=res,
        gm_output=gm,
        session=session,
        scene=scene,
        world=world,
    )

    assert meta["narration_state_mismatch_detected"] is True
    assert meta["mismatch_repair_applied"] in {"extracted_actionable_leads", "contextual_lead_clues"}
    assert _social_resolution_carries_information(res)
    nsc = (res.get("metadata") or {}).get("narration_state_consistency") or {}
    assert nsc.get("narration_state_mismatch_detected") is True


def test_truly_empty_refusal_stays_consistent_no_repair():
    session: dict = {}
    world = default_world()
    scene = _scene_envelope("gate")
    res = _empty_question_resolution()
    gm = {
        "player_facing_text": '"I do not know anything about that," the guard says flatly.',
        "tags": [],
    }

    meta = detect_narration_state_mismatch(
        resolution=res,
        gm_output=gm,
        session=session,
        scene=scene,
        world=world,
    )

    assert meta["narration_state_mismatch_detected"] is False
    assert meta["mismatch_repair_applied"] == "none"
    assert (meta.get("mismatch_repairs_applied") or []) == []
    assert not _social_resolution_carries_information(res)
    assert "no new information was revealed" in (res.get("hint") or "").lower()


def test_speaker_name_alone_does_not_trigger_mismatch():
    session: dict = {}
    world = default_world()
    scene = _scene_envelope("scene_investigate")
    res = _empty_question_resolution()
    res["social"]["npc_id"] = "runner"
    res["social"]["npc_name"] = "Tavern Runner"
    gm = {
        "player_facing_text": 'Tavern Runner frowns. "I have nothing more to add."',
        "tags": [],
    }

    meta = detect_narration_state_mismatch(
        resolution=res,
        gm_output=gm,
        session=session,
        scene=scene,
        world=world,
    )

    assert meta["narration_state_mismatch_detected"] is False


def test_usable_location_in_text_updates_structured_topic_and_clues():
    session: dict = {}
    world = default_world()
    scene = _scene_envelope("frontier_gate")
    res = _empty_question_resolution()
    gm = {
        "player_facing_text": (
            "The guard points east. \"House Verevin keeps a stronghold on the outskirts—"
            "you'll hear the rest there.\""
        ),
        "tags": [],
    }
    meta = reconcile_final_text_with_structured_state(
        session=session, scene=scene, world=world, resolution=res, gm_output=gm
    )
    assert meta["narration_state_mismatch_detected"] is True
    topic = (res.get("social") or {}).get("topic_revealed") or {}
    assert isinstance(topic, dict)
    assert topic.get("clue_id") or res.get("clue_id")
    assert get_all_known_clue_ids(session)


def test_named_figure_sets_emergent_actor_hint_flag():
    session: dict = {}
    world = default_world()
    scene = _scene_envelope("frontier_gate")
    res = _empty_question_resolution()
    gm = {
        "player_facing_text": (
            'The guard mutters, "Not me—you want Captain Aldric; he runs the watch desk."'
        ),
        "tags": [],
    }
    meta = reconcile_final_text_with_structured_state(
        session=session, scene=scene, world=world, resolution=res, gm_output=gm
    )
    assert meta["narration_state_mismatch_detected"] is True
    assert meta.get("emergent_actor_hint_detected") is True
    assert _social_resolution_carries_information(res)


def test_refusal_reply_kind_upgraded_when_narration_has_hooks():
    session: dict = {}
    world = default_world()
    scene = _scene_envelope("gate")
    res = _empty_question_resolution()
    res.setdefault("social", {})["reply_kind"] = "refusal"
    gm = {
        "player_facing_text": "Try the old milestone by the wall—carvings still show the trade seal.",
        "tags": [],
    }
    reconcile_final_text_with_structured_state(
        session=session, scene=scene, world=world, resolution=res, gm_output=gm
    )
    assert str((res.get("social") or {}).get("reply_kind") or "").lower() != "refusal"


def test_exhausted_social_escalation_skips_operational_hallucination_repair():
    """Engine-exhausted thread: do not upgrade empty resolution from operational-sounding narration."""
    session: dict = {}
    world = default_world()
    scene = _scene_envelope("frontier_gate")
    res = _empty_question_resolution()
    res["social"]["social_escalation"] = {
        "escalation_level": 3,
        "escalation_reason": "third_attempt_same_topic",
        "escalation_effect": "explicit_exhaustion_plus_where_to_next",
        "topic_exhausted": True,
        "force_actionable_lead": True,
        "force_partial_answer": False,
        "add_suspicion": False,
        "trigger_scene_momentum": False,
        "convert_refusal_to_conditioned_offer": False,
    }
    gm = {
        "player_facing_text": (
            "The guard leans in. \"House Verevin's people were seen near the stronghold—that is all I can say.\""
        ),
        "tags": [],
    }
    meta = reconcile_final_text_with_structured_state(
        session=session, scene=scene, world=world, resolution=res, gm_output=gm
    )
    assert meta["narration_state_mismatch_detected"] is False
    assert not _social_resolution_carries_information(res)


def test_gm_debug_scrubbed_when_text_carries_hooks():
    session: dict = {}
    world = default_world()
    scene = _scene_envelope("frontier_gate")
    res = _empty_question_resolution()
    gm = {
        "player_facing_text": "Ask around the old trading crossroads; that's where merchants gossip.",
        "tags": [],
        "debug_notes": "engine: no new information was revealed | other",
    }
    reconcile_final_text_with_structured_state(
        session=session, scene=scene, world=world, resolution=res, gm_output=gm
    )
    low = (gm.get("debug_notes") or "").lower()
    assert "no new information was revealed" not in low
    assert "scrubbed_misleading" in low or "repaired" in low
