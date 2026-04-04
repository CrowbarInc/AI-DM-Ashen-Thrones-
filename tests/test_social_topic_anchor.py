"""Active topic anchor: explicit player corrections must not be overridden by mystery/lead salience."""

from __future__ import annotations

from game.defaults import default_session, default_world
from game.gm import register_topic_probe
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.leads import SESSION_LEAD_REGISTRY_KEY, LeadLifecycle, LeadStatus
from game.prompt_context import build_narration_context
from game.social import explicit_player_topic_anchor_state, select_best_social_answer_candidate
from game.storage import get_scene_runtime

import pytest

pytestmark = pytest.mark.unit


def _scene_envelope(sid: str = "frontier_gate") -> dict:
    return {"scene": {"id": sid, "visible_facts": [], "exits": [], "enemies": []}}


def _resolution_social_tavern_runner() -> dict:
    return {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
        },
    }


def test_explicit_topic_anchor_detection_and_focus():
    st = explicit_player_topic_anchor_state('No, I meant the refugees—what have you heard?')
    assert st["active"] is True
    assert "refugee" in st["focus_fragment"].lower()

    st2 = explicit_player_topic_anchor_state("I'm asking about the eastern road—any safe camps?")
    assert st2["active"] is True
    assert "eastern" in st2["focus_fragment"].lower() or "road" in st2["focus_fragment"].lower()

    assert explicit_player_topic_anchor_state("What about the eastern road?")["active"] is False


def test_refugee_question_topic_key_not_missing_patrol_cluster():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    rebuild_active_scene_entities(session, world, sid)
    set_social_target(session, "tavern_runner")
    session["turn_counter"] = 1
    meta = register_topic_probe(
        session=session,
        scene_envelope=_scene_envelope(sid),
        player_text="What are the refugees saying about the eastern road?",
        resolution=_resolution_social_tavern_runner(),
    )
    assert meta.get("tracked") is True
    assert meta.get("topic_key") != "missing_patrol"


def test_east_follow_up_does_not_reuse_prior_missing_patrol_topic_key():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    rebuild_active_scene_entities(session, world, sid)
    set_social_target(session, "tavern_runner")
    session["turn_counter"] = 1
    register_topic_probe(
        session=session,
        scene_envelope=_scene_envelope(sid),
        player_text="Where is the missing patrol?",
        resolution=_resolution_social_tavern_runner(),
    )
    rt = get_scene_runtime(session, sid)
    assert rt.get("topic_pressure_last_topic_key") == "missing_patrol"

    session["turn_counter"] = 2
    meta2 = register_topic_probe(
        session=session,
        scene_envelope=_scene_envelope(sid),
        player_text="What can you tell me about the eastern road?",
        resolution=_resolution_social_tavern_runner(),
    )
    assert meta2.get("tracked") is True
    assert meta2.get("topic_key") != "missing_patrol"


def test_explicit_correction_skips_topic_pressure_last_answer():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    rebuild_active_scene_entities(session, world, sid)
    set_social_target(session, "tavern_runner")
    rt = get_scene_runtime(session, sid)
    rt["topic_pressure"] = {
        "missing_patrol": {
            "repeat_count": 2,
            "low_progress_streak": 0,
            "progress_score_total": 1.0,
            "last_answer": (
                "The runner leans in. \"People say the patrol vanished near the old crossroads—nothing but "
                "scuffed mail and a torn report.\""
            ),
            "last_turn": 3,
            "speaker_targets": {"tavern_runner": {"repeat_count": 2, "last_turn": 3}},
        }
    }
    rt["topic_pressure_current"] = {
        "topic_key": "missing_patrol",
        "speaker_key": "tavern_runner",
        "turn": 4,
        "player_text": "",
        "interaction_kind": "social",
        "interaction_mode": "social",
        "social_intent_class": "social_exchange",
        "npc_name": "Tavern Runner",
    }
    resolution = {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "reply_kind": "answer",
        },
    }
    cand = select_best_social_answer_candidate(
        session=session,
        scene_id=sid,
        npc_id="tavern_runner",
        topic_key="missing_patrol",
        player_text='No, I meant the refugees—what are people saying about them?',
        resolution=resolution,
    )
    assert cand["answer_kind"] == "refusal"
    assert cand.get("source") == "none"


def test_correction_disables_anaphora_glue_to_previous_topic():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    rebuild_active_scene_entities(session, world, sid)
    set_social_target(session, "tavern_runner")
    session["turn_counter"] = 1
    register_topic_probe(
        session=session,
        scene_envelope=_scene_envelope(sid),
        player_text="What happened to the missing patrol?",
        resolution=_resolution_social_tavern_runner(),
    )
    session["turn_counter"] = 2
    meta = register_topic_probe(
        session=session,
        scene_envelope=_scene_envelope(sid),
        player_text="No, I meant the refugees. What did they see on the road?",
        resolution=_resolution_social_tavern_runner(),
    )
    assert meta.get("tracked") is True
    assert meta.get("topic_key") != "missing_patrol"


def test_mystery_question_still_matches_topic_pressure_without_anchor():
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


def _session_with_pursued_patrol_lead() -> dict:
    return {
        "active_scene_id": "frontier_gate",
        "turn_counter": 5,
        "interaction_context": {
            "active_interaction_target_id": "tavern_runner",
            "active_interaction_kind": "question",
            "interaction_mode": "social",
            "engagement_level": "engaged",
            "conversation_privacy": None,
            "player_position_context": None,
        },
        SESSION_LEAD_REGISTRY_KEY: {
            "lead_missing_patrol": {
                "id": "lead_missing_patrol",
                "title": "Missing patrol",
                "summary": "Patrol vanished near crossroads.",
                "type": "mystery",
                "status": LeadStatus.PURSUED.value,
                "lifecycle": LeadLifecycle.COMMITTED.value,
                "confidence": 0.9,
                "priority": 5,
                "next_step": "Ask the Watch",
                "last_updated_turn": 4,
                "last_touched_turn": 3,
                "related_npc_ids": ["tavern_runner"],
                "related_location_ids": [],
            }
        },
    }


def test_narration_context_includes_anchor_rule_under_social_authority():
    session = _session_with_pursued_patrol_lead()
    world = {
        "npcs": [
            {
                "id": "tavern_runner",
                "name": "Tavern Runner",
                "location": "frontier_gate",
                "stance_toward_player": "wary",
                "information_reliability": "partial",
                "knowledge_scope": ["scene:frontier_gate", "rumors"],
                "origin_kind": "scene_actor",
            }
        ]
    }
    public_scene = {"id": "frontier_gate", "visible_facts": [], "exits": [], "enemies": []}
    ctx = build_narration_context(
        campaign={"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        world=world,
        session=session,
        character={"name": "Hero", "hp": {}, "ac": {}},
        scene={"scene": public_scene},
        combat={"in_combat": False},
        recent_log=[],
        user_text="No, I meant the refugees—what are they saying?",
        resolution=None,
        scene_runtime={"pending_leads": []},
        public_scene=public_scene,
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["question"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=[],
    )
    assert ctx["active_topic_anchor"]["active"] is True
    joined = "\n".join(ctx["instructions"])
    assert "ACTIVE TOPIC ANCHOR" in joined
    assert "currently_pursued_lead" in joined
