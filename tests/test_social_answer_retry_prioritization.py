"""Retry strategy: social answer candidates must beat scene_stall / echo_or_repetition."""

from __future__ import annotations

import pytest

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


@pytest.mark.parametrize(
    "failure_class,player_text,anchor_substring",
    [
        ("scene_stall", "Who is the he you're referring to?", "Caden"),
        ("echo_or_repetition", "What happened on the east road?", None),
    ],
)
def test_prioritize_suppresses_stall_or_echo_when_structured_candidate_exists(
    failure_class: str,
    player_text: str,
    anchor_substring: str | None,
) -> None:
    session, sid = _session_runner_topic_caden()
    if failure_class == "echo_or_repetition":
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
            "npc_name": "Tavern Runner",
        },
    }
    scene_envelope = {"scene": {"id": sid}}
    failures = [
        {"failure_class": failure_class, "priority": 40 if failure_class == "scene_stall" else 50, "reasons": [f"{failure_class}:test"]},
    ]
    out, dbg = prioritize_retry_failures_for_social_answer_candidate(
        failures,
        player_text=player_text,
        resolution=resolution,
        session=session,
        scene_envelope=scene_envelope,
    )
    assert dbg["strategy_forced_to_answer"] is True
    assert failure_class in dbg["suppressed_fallback_strategies"]
    assert resolution["social"]["strategy_forced_to_answer"] is True
    assert resolution["social"]["suppressed_fallback_strategies"] == [failure_class]
    if anchor_substring:
        assert anchor_substring in (resolution["social"].get("social_answer_retry_anchor_text") or "")
    chosen = choose_retry_strategy(out)
    assert chosen is not None
    assert chosen.get("failure_class") == "answer"


def test_prioritize_skips_forcing_when_inapplicable() -> None:
    session, sid = _session_runner_topic_caden()
    rt = get_scene_runtime(session, sid)
    rt["topic_pressure"] = {}
    resolution_stall = {
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
        resolution=resolution_stall,
        session=session,
        scene_envelope=scene_envelope,
    )
    assert dbg["strategy_forced_to_answer"] is False
    assert out == failures
    assert choose_retry_strategy(out).get("failure_class") == "scene_stall"

    session2, sid2 = _session_runner_topic_caden()
    resolution_question = {
        "kind": "question",
        "social": {"social_intent_class": "question", "npc_id": "tavern_runner"},
    }
    out2, dbg2 = prioritize_retry_failures_for_social_answer_candidate(
        failures,
        player_text="Who is the he you're referring to?",
        resolution=resolution_question,
        session=session2,
        scene_envelope={"scene": {"id": sid2}},
    )
    assert dbg2["strategy_forced_to_answer"] is False
    assert out2 == failures
