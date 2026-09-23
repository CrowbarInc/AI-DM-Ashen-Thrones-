"""PR-BI: interruption narration must not become answer authority."""
from __future__ import annotations

from game.response_policy_enforcement import apply_response_policy_enforcement
from game.social import (
    realize_authored_knowledge_answer,
    select_best_social_answer_candidate,
)
from game.storage import get_scene_runtime

INTERRUPTION = (
    "The runner begins to respond before noise from the crowd pulls their attention away."
)
AUTHORED = "The patrol never came back from the old milestone."
PLAYER = '"Runner," Galinor says, "ignore the noise and tell me about the patrol."'


def _session_with_last_answer(last_answer: str) -> dict:
    return {
        "active_scene_id": "tavern",
        "turn_counter": 3,
        "scene_runtime": {
            "tavern": {
                "topic_pressure_current": {
                    "topic_key": "topic:happen_patrol_runner",
                    "speaker_key": "tavern_runner",
                    "interaction_kind": "social",
                    "interaction_mode": "social",
                    "social_intent_class": "social_exchange",
                    "npc_name": "Tavern Runner",
                },
                "topic_pressure": {
                    "topic:happen_patrol_runner": {
                        "last_answer": last_answer,
                        "progress_score_total": 1.5,
                        "low_progress_streak": 1,
                        "repeat_count": 2,
                        "speaker_targets": {
                            "tavern_runner": {
                                "repeat_count": 2,
                                "low_progress_streak": 1,
                                "patience": 2,
                            }
                        },
                    }
                },
            }
        },
    }


def _resolution() -> dict:
    return {
        "kind": "social_probe",
        "prompt": PLAYER,
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "reply_kind": "explanation",
        },
    }


def _scene_envelope() -> dict:
    return {"scene": {"id": "tavern", "location": "Tavern"}}


def test_interruption_breakoff_does_not_replace_authoritative_last_answer() -> None:
    session = _session_with_last_answer(AUTHORED)
    apply_response_policy_enforcement(
        {
            "player_facing_text": INTERRUPTION,
            "tags": [],
            "metadata": {},
            "debug_notes": "",
        },
        response_policy={
            "must_answer": False,
            "forbid_state_invention": False,
            "forbid_secret_leak": False,
            "diegetic_only": False,
            "prefer_scene_momentum": False,
            "prefer_specificity": False,
        },
        player_text=PLAYER,
        scene_envelope=_scene_envelope(),
        session=session,
        world={"npcs": []},
        resolution=_resolution(),
        discovered_clues=[],
    )
    entry = get_scene_runtime(session, "tavern")["topic_pressure"]["topic:happen_patrol_runner"]
    assert entry["last_answer"] == AUTHORED
    assert "begins to respond" not in entry["last_answer"]
    assert int(entry["low_progress_streak"]) == 2


def test_ordinary_reply_still_commits_last_answer() -> None:
    session = _session_with_last_answer("")
    apply_response_policy_enforcement(
        {
            "player_facing_text": AUTHORED,
            "tags": [],
            "metadata": {},
            "debug_notes": "",
        },
        response_policy={
            "must_answer": False,
            "forbid_state_invention": False,
            "forbid_secret_leak": False,
            "diegetic_only": False,
            "prefer_scene_momentum": False,
            "prefer_specificity": False,
        },
        player_text=PLAYER,
        scene_envelope=_scene_envelope(),
        session=session,
        world={"npcs": []},
        resolution=_resolution(),
        discovered_clues=[],
    )
    entry = get_scene_runtime(session, "tavern")["topic_pressure"]["topic:happen_patrol_runner"]
    assert entry["last_answer"] == AUTHORED


def test_interruption_shaped_last_answer_is_not_selected_as_fact() -> None:
    session = _session_with_last_answer(INTERRUPTION)
    session["clue_knowledge"] = {
        "c_patrol_milestone": {
            "text": AUTHORED,
            "source_scene": "tavern",
            "presentation": "actionable",
        }
    }
    cand = select_best_social_answer_candidate(
        session=session,
        scene_id="tavern",
        npc_id="tavern_runner",
        topic_key=None,
        player_text=PLAYER,
        resolution=_resolution(),
    )
    assert cand.get("source") != "topic_pressure:last_answer"
    assert "begins to respond" not in str(cand.get("text") or "").lower()
    assert "milestone" in str(cand.get("text") or "").lower()


def test_authorized_last_answer_remains_eligible() -> None:
    session = _session_with_last_answer(AUTHORED)
    cand = select_best_social_answer_candidate(
        session=session,
        scene_id="tavern",
        npc_id="tavern_runner",
        topic_key=None,
        player_text=PLAYER,
        resolution=_resolution(),
    )
    assert cand.get("source") == "topic_pressure:last_answer"
    assert "milestone" in str(cand.get("text") or "").lower()


def test_interruption_last_answer_does_not_block_owned_topic() -> None:
    session = _session_with_last_answer(INTERRUPTION)
    world = {
        "npcs": [
            {
                "id": "tavern_runner",
                "name": "Tavern Runner",
                "location": "tavern",
                "topics": [
                    {
                        "id": "patrol_milestone",
                        "text": AUTHORED,
                        "clue_id": "c_patrol_milestone",
                    }
                ],
            }
        ]
    }
    realized = realize_authored_knowledge_answer(
        session=session,
        scene_id="tavern",
        player_text=PLAYER,
        resolution=_resolution(),
        world=world,
    )
    assert realized is not None
    text = str(realized.get("text") or "")
    assert "milestone" in text.lower()
    assert "begins to respond" not in text.lower()
    assert "word is, the runner begins" not in text.lower()
