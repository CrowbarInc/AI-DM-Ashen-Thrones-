"""Retry strategy: social answer candidates must beat scene_stall / echo_or_repetition."""

from __future__ import annotations

from game.defaults import default_session, default_world
from game.gm import choose_retry_strategy, prioritize_retry_failures_for_social_answer_candidate
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.storage import get_scene_runtime


def _session_runner_topic_caden():
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
            "last_player_input": "Who is the he you're referring to?",
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
    return session, sid


def test_prioritize_suppresses_scene_stall_when_structured_candidate_exists():
    session, sid = _session_runner_topic_caden()
    resolution = {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
        },
    }
    scene_envelope = {"scene": {"id": sid}}
    failures = [
        {"failure_class": "scene_stall", "priority": 40, "reasons": ["scene_stall:test"]},
    ]
    out, dbg = prioritize_retry_failures_for_social_answer_candidate(
        failures,
        player_text="Who is the he you're referring to?",
        resolution=resolution,
        session=session,
        scene_envelope=scene_envelope,
    )
    assert dbg["strategy_forced_to_answer"] is True
    assert "scene_stall" in dbg["suppressed_fallback_strategies"]
    assert resolution["social"]["strategy_forced_to_answer"] is True
    assert resolution["social"]["suppressed_fallback_strategies"] == ["scene_stall"]
    assert "Caden" in (resolution["social"].get("social_answer_retry_anchor_text") or "")
    chosen = choose_retry_strategy(out)
    assert chosen is not None
    assert chosen.get("failure_class") == "answer"


def test_prioritize_suppresses_echo_when_reconciled_candidate_exists():
    session, sid = _session_runner_topic_caden()
    session["clue_knowledge"] = {
        "clue_x": {
            "text": "Word is the east road convoy left an hour ago; guards argue about which sergeant signed the relief.",
            "source_scene": sid,
            "presentation": "actionable",
        }
    }
    resolution = {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
        },
    }
    scene_envelope = {"scene": {"id": sid}}
    failures = [
        {"failure_class": "echo_or_repetition", "priority": 50, "reasons": ["echo:test"]},
    ]
    out, dbg = prioritize_retry_failures_for_social_answer_candidate(
        failures,
        player_text="What happened on the east road?",
        resolution=resolution,
        session=session,
        scene_envelope=scene_envelope,
    )
    assert dbg["strategy_forced_to_answer"] is True
    assert "echo_or_repetition" in dbg["suppressed_fallback_strategies"]
    chosen = choose_retry_strategy(out)
    assert chosen is not None
    assert chosen.get("failure_class") == "answer"


def test_prioritize_leaves_stall_when_no_social_candidate():
    session, sid = _session_runner_topic_caden()
    rt = get_scene_runtime(session, sid)
    rt["topic_pressure"] = {}
    resolution = {
        "kind": "question",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
        },
    }
    scene_envelope = {"scene": {"id": sid}}
    failures = [
        {"failure_class": "scene_stall", "priority": 40, "reasons": ["scene_stall:test"]},
    ]
    out, dbg = prioritize_retry_failures_for_social_answer_candidate(
        failures,
        player_text="Who is the secret archmage nobody knows?",
        resolution=resolution,
        session=session,
        scene_envelope=scene_envelope,
    )
    assert dbg["strategy_forced_to_answer"] is False
    assert out == failures
    assert choose_retry_strategy(out).get("failure_class") == "scene_stall"


def test_prioritize_not_applied_outside_social_exchange():
    session, sid = _session_runner_topic_caden()
    resolution = {"kind": "question", "social": {"social_intent_class": "question", "npc_id": "tavern_runner"}}
    scene_envelope = {"scene": {"id": sid}}
    failures = [
        {"failure_class": "scene_stall", "priority": 40, "reasons": ["scene_stall:test"]},
    ]
    out, dbg = prioritize_retry_failures_for_social_answer_candidate(
        failures,
        player_text="Who is the he you're referring to?",
        resolution=resolution,
        session=session,
        scene_envelope=scene_envelope,
    )
    assert dbg["strategy_forced_to_answer"] is False
    assert out == failures
