"""Shared social escalation session/topic-pressure fixtures (Cycle AL1b).

Support residue for escalation consumer suites; escalation semantics stay owned
by ``tests/test_social_escalation.py``.
"""
from __future__ import annotations

from game.storage import get_scene_runtime


def session_with_pressure(scene_id: str, topic_key: str, speaker_key: str, repeat_count: int) -> dict:
    session: dict = {"turn_counter": 1}

    rt = get_scene_runtime(session, scene_id)
    rt["topic_pressure_current"] = {
        "topic_key": topic_key,
        "speaker_key": speaker_key,
        "turn": 1,
        "player_text": "Who ordered it?",
        "interaction_kind": "social",
        "interaction_mode": "social",
        "social_intent_class": "social_exchange",
        "npc_name": "Runner",
    }
    rt["topic_pressure"] = {
        topic_key: {
            "repeat_count": repeat_count,
            "low_progress_streak": 0,
            "progress_score_total": 0.0,
            "last_answer": "",
            "last_turn": 1,
            "speaker_targets": {
                speaker_key: {
                    "repeat_count": repeat_count,
                    "low_progress_streak": 0,
                    "patience": 3,
                    "last_turn": 1,
                }
            },
        }
    }
    return session
