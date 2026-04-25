from __future__ import annotations

from game.defaults import default_session, default_world
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.social import (
    apply_structured_social_answer_candidate_to_resolution,
    classify_social_question_dimension,
    format_structured_fact_social_line,
    select_best_social_answer_candidate,
)
from game.social_exchange_emission import build_final_strict_social_response
from game.storage import get_scene_runtime


import pytest

pytestmark = pytest.mark.unit

def _session_with_topic_pressure_caden() -> tuple[dict, dict, str]:
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    rebuild_active_scene_entities(session, world, sid)
    set_social_target(session, "tavern_runner")
    rt = get_scene_runtime(session, sid)
    rt["topic_pressure"] = {
        "topic:referr": {
            "repeat_count": 1,
            "low_progress_streak": 0,
            "progress_score_total": 1.5,
            "last_answer": (
                'The Tavern Runner narrows their eyes. "He\'s known as Caden. A dangerous man, tied to House Verevin. '
                'They say he was last seen lingering near the old milestone, possibly tied to the missing patrol."'
            ),
            "last_turn": 5,
            "speaker_targets": {"tavern_runner": {"repeat_count": 1, "last_turn": 5}},
            "last_player_input": 'Who is the he you\'re referring to?',
        }
    }
    rt["topic_pressure_current"] = {
        "topic_key": "topic:referr",
        "speaker_key": "tavern_runner",
        "turn": 5,
        "player_text": "Who is the he you're referring to?",
        "interaction_kind": "social",
        "interaction_mode": "social",
        "social_intent_class": "social_exchange",
        "npc_name": "Tavern Runner",
    }
    return session, world, sid


def test_classify_dimension_identity_and_location():
    assert classify_social_question_dimension("Who is the he you're referring to?") == "identity"
    assert classify_social_question_dimension("Where was he seen last?") == "location"


def test_select_best_who_question_uses_topic_pressure_last_answer():
    session, _world, sid = _session_with_topic_pressure_caden()
    resolution = {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "reply_kind": "refusal",
        },
    }
    cand = select_best_social_answer_candidate(
        session=session,
        scene_id=sid,
        npc_id="tavern_runner",
        topic_key=None,
        player_text="Who is the he you're referring to?",
        resolution=resolution,
    )
    assert cand["answer_kind"] == "structured_fact"
    assert cand["source"] == "topic_pressure:last_answer"
    assert "Caden" in (cand.get("text") or "")


def test_select_best_where_question_uses_location_slice():
    session, _world, sid = _session_with_topic_pressure_caden()
    resolution = {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
        },
    }
    cand = select_best_social_answer_candidate(
        session=session,
        scene_id=sid,
        npc_id="tavern_runner",
        topic_key=None,
        player_text="Where was he seen?",
        resolution=resolution,
    )
    assert cand["answer_kind"] == "structured_fact"
    assert "milestone" in (cand.get("text") or "").lower()


def test_select_best_refusal_when_no_stored_fact():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    rebuild_active_scene_entities(session, world, sid)
    rt = get_scene_runtime(session, sid)
    rt["topic_pressure"] = {}
    rt["topic_pressure_current"] = {
        "topic_key": "topic:empty",
        "speaker_key": "tavern_runner",
    }
    cand = select_best_social_answer_candidate(
        session=session,
        scene_id=sid,
        npc_id="tavern_runner",
        topic_key="topic:empty",
        player_text="Who is he?",
        resolution={"social": {"social_intent_class": "social_exchange", "npc_id": "tavern_runner"}},
    )
    assert cand["answer_kind"] == "refusal"
    assert cand.get("text") is None


def test_apply_structured_refreshes_hint_without_blocking_narration_repair():
    session, _world, sid = _session_with_topic_pressure_caden()
    resolution = {
        "kind": "question",
        "success": None,
        "hint": "No new information was revealed. Narrate refusal.",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "reply_kind": "refusal",
        },
    }
    apply_structured_social_answer_candidate_to_resolution(
        session=session,
        scene_id=sid,
        player_text="Who is the he you're referring to?",
        resolution=resolution,
    )
    assert resolution.get("success") is None
    assert resolution["social"]["reply_kind"] == "refusal"
    assert resolution["social"]["refusal_suppressed_by_structured_fact"] is True
    assert "No new information was revealed" not in (resolution.get("hint") or "")
    assert resolution["social"]["answer_candidate_selected"] == "structured_fact"


def test_build_final_strict_social_prefers_structured_fact_over_rejection():
    session, _world, sid = _session_with_topic_pressure_caden()
    resolution = {
        "kind": "question",
        "prompt": "Who is the he you're referring to?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "reply_kind": "refusal",
            "npc_reply_expected": True,
        },
    }
    bad = "For a breath, the scene holds while voices shift around you."
    text, details = build_final_strict_social_response(
        bad,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=_world,
    )
    assert "Caden" in text
    assert details.get("final_emitted_source") == "structured_fact_candidate_emission"
    assert details.get("used_internal_fallback") is False


def test_build_final_route_illegal_without_topic_fact_does_not_emit_structured_fact():
    """Route-illegal sanitizer text must not pick structured facts when none exist in session."""
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    rebuild_active_scene_entities(session, world, sid)
    set_social_target(session, "tavern_runner")
    resolution = {
        "kind": "question",
        "prompt": "Who is he?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "reply_kind": "refusal",
            "npc_reply_expected": True,
        },
    }
    bad = "For a breath, the scene holds while voices shift around you."
    text, details = build_final_strict_social_response(
        bad,
        resolution=resolution,
        tags=[],
        session=session,
        scene_id=sid,
        world=world,
    )
    assert details.get("final_emitted_source") != "structured_fact_candidate_emission"
    low = text.lower()
    assert "for a breath" not in low and "scene holds" not in low and "voices shift around you" not in low
    assert "tavern runner" in low


def test_format_structured_fact_social_line_single_sentence():
    res = {
        "social": {"npc_name": "Tavern Runner", "npc_id": "tavern_runner"},
    }
    line = format_structured_fact_social_line(res, "He's known as Caden—Verevin.")
    assert line.startswith("Tavern Runner mutters,")
    assert "Caden" in line
    assert "Word is" in line
