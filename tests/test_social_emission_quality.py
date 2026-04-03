"""Strict-social emission: grounded answer preservation vs degraded normalized candidates."""

from __future__ import annotations

import pytest

from game.defaults import default_session, default_world
from game.final_emission_gate import apply_final_emission_gate
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.social_exchange_emission import (
    build_final_strict_social_response,
    select_best_grounded_social_answer_text,
)
from game.storage import get_scene_runtime


pytestmark = pytest.mark.integration

_LIRAEL_LAST_ANSWER = (
    "Speak to Lirael if you want the sheepfold rumor straight—she keeps to the fold "
    "on the north road by the old milestone."
)


def _base_session_scene():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    set_social_target(session, "tavern_runner")
    rebuild_active_scene_entities(session, world, sid)
    return session, world, sid


def _strict_social_resolution_tavern_runner(*, prompt: str, **social_extras: object) -> dict:
    soc = {
        "social_intent_class": "social_exchange",
        "npc_id": "tavern_runner",
        "npc_name": "Tavern Runner",
        "reply_kind": "answer",
        **social_extras,
    }
    return {
        "kind": "question",
        "prompt": prompt,
        "success": True,
        "social": soc,
    }


@pytest.mark.transcript
@pytest.mark.emission
@pytest.mark.social
def test_transcript_lirael_who_next_then_where_preserves_grounded_location():
    """Transcript-style Lirael failure (location follow-up).

    Turn 1 — Player asks Tavern Runner who to talk to next; engine records ``last_answer`` naming Lirael with
    sheepfold / north-road / milestone grounding (simulated below).
    Turn 2 — Player asks where Lirael can be found; the normalized candidate is legal but clips to the name.
    Final emission must restore the substantive grounded line, not the clipped quote.
    """
    session, world, sid = _base_session_scene()
    rt = get_scene_runtime(session, sid)
    rt["topic_pressure"] = {"lirael_thread": {"last_answer": _LIRAEL_LAST_ANSWER}}
    rt["topic_pressure_current"] = {"topic_key": "lirael_thread", "speaker_key": ""}

    rt["last_player_action_text"] = (
        "Tavern Runner, who should I talk to next about the sheepfold rumor?"
    )
    res_who_next = _strict_social_resolution_tavern_runner(prompt=rt["last_player_action_text"])
    grounded_after_turn1 = select_best_grounded_social_answer_text(
        session=session, scene_id=sid, resolution=res_who_next
    )
    assert "lirael" in str(grounded_after_turn1.get("text") or "").lower()
    assert grounded_after_turn1.get("source") == "topic_pressure:last_answer"

    rt["last_player_action_text"] = "Where can I find Lirael?"
    res_where = _strict_social_resolution_tavern_runner(prompt="Where can I find Lirael?")
    clipped = 'The tavern runner mutters, "lirael."'
    out, det = build_final_strict_social_response(
        clipped,
        resolution=res_where,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out.lower()
    assert "tavern runner" in low
    assert "north road" in low or "sheepfold" in low or "milestone" in low
    assert det.get("resolved_answer_preferred") is True
    assert det.get("final_emitted_source") == "resolved_grounded_social_answer"
    assert det.get("candidate_quality_degraded") is True
    assert det.get("resolved_answer_source") == "topic_pressure:last_answer"
    assert det.get("resolved_answer_preference_reason")

    gate_out = apply_final_emission_gate(
        {"player_facing_text": clipped, "tags": []},
        resolution=res_where,
        session=session,
        scene_id=sid,
        world=world,
    )
    meta = gate_out.get("_final_emission_meta") or {}
    g_low = gate_out["player_facing_text"].lower()
    assert "tavern runner" in g_low
    assert "north road" in g_low or "sheepfold" in g_low or "milestone" in g_low
    assert meta.get("resolved_answer_preferred") is True
    assert meta.get("final_emitted_source") == "resolved_grounded_social_answer"
    assert meta.get("candidate_quality_degraded") is True
    assert meta.get("resolved_answer_source") == "topic_pressure:last_answer"
    assert meta.get("resolved_answer_preference_reason")


@pytest.mark.transcript
@pytest.mark.emission
@pytest.mark.social
def test_transcript_anyone_else_talk_to_manifests_preserves_redirect_not_fragment():
    """Transcript-style: broad follow-up on manifests; grounded redirect must beat a fragmentary accepted line."""
    session, world, sid = _base_session_scene()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Anyone else I should talk to about the manifests?"
    rt["topic_pressure"] = {
        "manifest_thread": {
            "last_answer": (
                "If manifests matter, speak to the harbor clerk; they work the late ledger "
                "from a desk by the west pier."
            ),
        }
    }
    rt["topic_pressure_current"] = {"topic_key": "manifest_thread", "speaker_key": ""}
    resolution = _strict_social_resolution_tavern_runner(prompt=rt["last_player_action_text"])
    clipped = 'The tavern runner mutters, "manifests."'
    out, details = build_final_strict_social_response(
        clipped,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out.lower()
    assert "tavern runner" in low
    assert "harbor" in low and "clerk" in low
    assert "west pier" in low or "pier" in low
    assert details.get("resolved_answer_preferred") is True
    assert details.get("final_emitted_source") == "resolved_grounded_social_answer"
    assert details.get("candidate_quality_degraded") is True
    assert details.get("resolved_answer_source") == "topic_pressure:last_answer:redirect"
    assert details.get("resolved_answer_preference_reason")

    gate_out = apply_final_emission_gate(
        {"player_facing_text": clipped, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    meta = gate_out.get("_final_emission_meta") or {}
    assert meta.get("final_emitted_source") == "resolved_grounded_social_answer"
    assert meta.get("resolved_answer_source") == "topic_pressure:last_answer:redirect"


@pytest.mark.emission
@pytest.mark.social
def test_refusal_stays_coherent_when_no_grounded_actionable_answer():
    """No matching engine-grounded line: a coherent refusal must not be replaced by unrelated background text."""
    session, world, sid = _base_session_scene()
    session["clue_knowledge"] = {
        "stale_whisper": {
            "source_scene": sid,
            "text": "Somebody once mentioned wet ink and cheap seals near the river market.",
        }
    }
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Who runs the forged seal trade out of this ward?"
    rt["topic_pressure"] = {
        "patrols": {
            "last_answer": "The night patrol doubled the east gate watches before dawn; nothing about seals.",
        }
    }
    rt["topic_pressure_current"] = {"topic_key": "patrols", "speaker_key": ""}
    resolution = _strict_social_resolution_tavern_runner(prompt=rt["last_player_action_text"])
    refusal = (
        'The tavern runner exhales through their teeth. '
        '"I don\'t trade in seal gossip—the ward clerk watches those papers, not me."'
    )
    out, details = build_final_strict_social_response(
        refusal,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out.lower()
    assert "river" not in low and "wet ink" not in low
    assert "seal gossip" in low or "clerk" in low
    assert details.get("resolved_answer_preferred") is False
    assert details.get("candidate_quality_degraded") is False
    assert details.get("final_emitted_source") in ("generated_candidate", "normalized_social_candidate")
    assert len(out) >= 40


def test_clipped_candidate_loses_to_topic_pressure_last_answer():
    session, world, sid = _base_session_scene()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Where did the east market crowd run to?"
    rt["topic_pressure"] = {
        "east_market": {
            "last_answer": (
                "They ran from the east market square down the long lane toward the river gate and the old patrol checkpoint."
            ),
        }
    }
    rt["topic_pressure_current"] = {"topic_key": "east_market", "speaker_key": ""}
    resolution = {
        "kind": "question",
        "prompt": "Where did the east market crowd run to?",
        "success": True,
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "npc_reply_expected": True,
            "reply_kind": "answer",
        },
    }
    clipped = (
        'The tavern runner mutters, "east market."'
    )
    out, details = build_final_strict_social_response(
        clipped,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out.lower()
    assert "tavern runner" in low
    assert "river gate" in low or "patrol checkpoint" in low or "long lane" in low
    assert details.get("resolved_answer_preferred") is True
    assert details.get("candidate_quality_degraded") is True
    assert details.get("resolved_answer_source") == "topic_pressure:last_answer"
    assert details.get("resolved_answer_preference_reason")
    assert details.get("final_emitted_source") == "resolved_grounded_social_answer"


def test_coherent_candidate_passes_through_unchanged():
    session, world, sid = _base_session_scene()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Where did they go?"
    rt["topic_pressure"] = {
        "rumor": {
            "last_answer": "I heard they slipped toward the east road past the mill.",
        }
    }
    rt["topic_pressure_current"] = {"topic_key": "rumor", "speaker_key": ""}
    resolution = {
        "kind": "question",
        "prompt": "Where did they go?",
        "success": True,
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "reply_kind": "answer",
        },
    }
    coherent = (
        'The tavern runner leans in. "They slipped toward the east road past the mill—same as I said."'
    )
    out, details = build_final_strict_social_response(
        coherent,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out.lower()
    assert "east road" in low and "mill" in low
    assert details.get("resolved_answer_preferred") is False
    assert details.get("candidate_quality_degraded") is False
    assert details.get("final_emitted_source") in ("generated_candidate", "normalized_social_candidate")
    assert details.get("final_emitted_source") != "resolved_grounded_social_answer"


def test_refusal_candidate_loses_to_topic_revealed_next_step():
    session, world, sid = _base_session_scene()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "What should I do next?"
    resolution = {
        "kind": "question",
        "prompt": "What should I do next?",
        "success": True,
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "reply_kind": "answer",
            "topic_revealed": {
                "clue_text": "Head to the river gate and speak to the dock clerk before the shift change.",
            },
        },
    }
    cand = 'The tavern runner shakes their head. "I don\'t know."'
    out, details = build_final_strict_social_response(
        cand,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out.lower()
    assert "tavern runner" in low
    assert "river gate" in low or "dock clerk" in low
    assert "don't know" not in low
    assert details.get("resolved_answer_preferred") is True
    assert details.get("candidate_quality_degraded") is True
    assert details.get("resolved_answer_source") == "resolution:topic_revealed"
    assert details.get("resolved_answer_preference_reason")
    assert details.get("final_emitted_source") == "resolved_grounded_social_answer"


def test_stronger_answer_not_chosen_when_it_fails_strict_legality():
    session, world, sid = _base_session_scene()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "What should I do next?"
    resolution = {
        "kind": "question",
        "prompt": "What should I do next?",
        "success": True,
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "reply_kind": "answer",
            "topic_revealed": {
                "clue_text": "You should go straight to the east gate and ask the sergeant there.",
            },
        },
    }
    cand = 'The tavern runner shrugs. "I can\'t help you."'
    out, details = build_final_strict_social_response(
        cand,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    low = out.lower()
    assert "can't help" in low or "cannot help" in low
    assert "you should" not in low
    assert details.get("candidate_quality_degraded") is True
    assert details.get("resolved_answer_preferred") is False
    assert details.get("resolved_answer_preference_reason") == "stronger_answer_failed_strict_legality"
    assert details.get("final_emitted_source") in ("generated_candidate", "normalized_social_candidate")
    assert details.get("final_emitted_source") != "resolved_grounded_social_answer"


def test_final_emission_gate_meta_records_preference_decision():
    session, world, sid = _base_session_scene()
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Which way from the east market?"
    rt["topic_pressure"] = {
        "east_market": {
            "last_answer": (
                "They left the east market by the south road toward the river docks and the night watch post."
            ),
        }
    }
    # Empty speaker_key: alignment check in select_best_social_answer_candidate must not depend
    # on matching reconcile_strict_social_resolution_speaker's npc_id (roster order varies).
    rt["topic_pressure_current"] = {
        "topic_key": "east_market",
        "speaker_key": "",
    }
    resolution = {
        "kind": "question",
        "prompt": "Which way from the east market?",
        "success": True,
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "reply_kind": "answer",
        },
    }
    # Short quote must still satisfy first-sentence substantive contract (overlap with question tokens).
    gate_out = apply_final_emission_gate(
        {"player_facing_text": 'The tavern runner mutters, "east market."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    meta = gate_out.get("_final_emission_meta") or {}
    low = gate_out["player_facing_text"].lower()
    assert "river docks" in low or "night watch" in low or "south road" in low
    assert meta.get("resolved_answer_preferred") is True
    assert meta.get("candidate_quality_degraded") is True
    assert meta.get("resolved_answer_source")
    assert meta.get("resolved_answer_preference_reason")


def test_select_best_grounded_social_answer_text_returns_engine_snippet():
    session, _world, sid = _base_session_scene()
    rt = get_scene_runtime(session, sid)
    rt["topic_pressure"] = {"t1": {"last_answer": "The east gate is where they were seen last."}}
    rt["topic_pressure_current"] = {"topic_key": "t1", "speaker_key": ""}
    resolution = {
        "kind": "question",
        "prompt": "Where were they seen?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
        },
    }
    g = select_best_grounded_social_answer_text(
        session=session, scene_id=sid, resolution=resolution
    )
    assert g.get("text")
    assert "east" in str(g.get("text")).lower()
