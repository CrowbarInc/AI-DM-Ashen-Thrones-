"""PR-EG dialogue quality. Frozen holdouts are behavioral, not a phrase table."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from game.dialogue_authority import (
    attach_dialogue_authority,
    build_dialogue_authority,
    remember_dialogue_commitment,
    requested_information,
    response_class,
)
from game.social import (
    _bounded_social_reply_plan_for_missing_topic,
    authored_answer_sufficient_for_question,
    authored_topic_relevant_to_question,
)

pytestmark = pytest.mark.unit

HOLDOUTS = json.loads(
    (Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "pr_eg_dialogue_holdouts.json").read_text(
        encoding="utf-8"
    )
)
ROAD = "The street beyond the gate is the north road."
PARTIAL = "A patrol sometimes passes the waystation. I have not seen one on the north road."


def _npc(case: dict) -> dict:
    topics = []
    if case.get("topic_text"):
        topics.append({"id": "partial", "text": case["topic_text"]})
    elif case.get("expect_topic") and case.get("requested_information") == "general":
        topics.append({"id": "street", "text": ROAD})
    return {
        "id": case.get("npc_id") or "sergeant_mara",
        "name": case.get("npc_name") or "Sergeant Mara",
        "role": "guard" if "mara" in str(case.get("npc_id") or "sergeant_mara") else "porter",
        "disposition": "neutral",
        "topics": topics,
    }


def _classify(case: dict) -> dict:
    npc = _npc(case)
    player = case["player"]
    topic = (npc.get("topics") or [None])[0]
    relevant = bool(topic) and authored_topic_relevant_to_question(
        player, topic, npc=npc, speaker_name=npc["name"]
    )
    sufficient = bool(topic) and authored_answer_sufficient_for_question(player, topic)
    plan = _bounded_social_reply_plan_for_missing_topic(
        action_type="question",
        player_text=player,
        npc=npc,
        topic_revealed=bool(case.get("prior_topic_revealed")) and not sufficient,
    )
    # The missing-topic resolver does not treat an older topic as this answer.
    if not sufficient:
        plan = _bounded_social_reply_plan_for_missing_topic(
            action_type="question",
            player_text=player,
            npc=npc,
            topic_revealed=False,
        )
    social = {
        "npc_id": npc["id"],
        "npc_name": npc["name"],
        "target_resolved": True,
        "topic_revealed": dict(topic) if sufficient else None,
        "reply_plan_kind": plan["reply_plan_kind"] if not sufficient else "authoritative_answer_available",
        "npc_speech_authority": plan["npc_speech_authority"] if not sufficient else "none",
        "incidental_subjective_allowed": plan["incidental_subjective_allowed"] if not sufficient else False,
        "objective_world_fact_authority": plan["objective_world_fact_authority"],
    }
    if case.get("prior_topic_revealed") and not sufficient:
        social["reply_plan_kind"] = "authoritative_answer_available"
        social["npc_speech_authority"] = "none"
    authority = attach_dialogue_authority(social, player, npc, {"conversational_context": {}})
    line = authority.get("player_line") or (topic or {}).get("text") or ""
    return {"social": social, "authority": authority, "line": line, "relevant": relevant, "sufficient": sufficient}


def score_case(case: dict, found: dict) -> dict[str, bool]:
    authority = found["authority"]
    social = found["social"]
    line = str(found["line"] or "")
    lowered = line.lower()
    kind = requested_information(case["player"])
    scores = {
        "relevance": kind == case.get("requested_information", kind),
        "groundedness": "unauthorized" not in lowered and response_class(line) != "consequential",
        "naturalness": response_class(line) != "internal" and "settled here" not in lowered,
        "npc_consistency": (
            not line
            or str(social.get("npc_name") or "") in line
            or authority.get("knowledge_posture") in {"established", "partial"}
        ),
        "uncertainty_quality": True,
        "continuity": authority.get("canonical") is False,
        "improvisation_boundaries": authority.get("improvisation_permitted") is case.get(
            "expect_improvisation", authority.get("improvisation_permitted")
        ),
        "player_utility": True,
        "efficiency": True,
    }
    if "expect_topic" in case:
        scores["groundedness"] = scores["groundedness"] and (found["sufficient"] is case["expect_topic"])
    if case.get("expect_posture"):
        scores["uncertainty_quality"] = authority.get("knowledge_posture") == case["expect_posture"]
    if case.get("expect_narration_determined") is not None:
        scores["efficiency"] = authority.get("narration_determined") is case["expect_narration_determined"]
    if case.get("reply_plan"):
        scores["improvisation_boundaries"] = scores["improvisation_boundaries"] and (
            social.get("reply_plan_kind") == case["reply_plan"]
        )
    if case.get("reply_plan_not"):
        scores["groundedness"] = scores["groundedness"] and social.get("reply_plan_kind") not in case["reply_plan_not"]
    if case.get("response_class"):
        scores["uncertainty_quality"] = scores["uncertainty_quality"] and (
            response_class(line) == case["response_class"] or not line
        )
    for banned in case.get("response_must_not_contain") or []:
        if banned.lower() in lowered:
            scores["relevance"] = False
            scores["naturalness"] = False
    if case.get("response_must_contain_any") and line:
        scores["player_utility"] = any(bit.lower() in lowered for bit in case["response_must_contain_any"])
    if case.get("expect_improvisation") is True:
        scores["improvisation_boundaries"] = (
            authority.get("improvisation_permitted") is True and authority.get("canonical") is False
        )
    return scores


@pytest.mark.parametrize("case", HOLDOUTS["cases"], ids=[row["id"] for row in HOLDOUTS["cases"]])
def test_frozen_holdout_dimensions(case):
    found = _classify(case)
    scores = score_case(case, found)
    for name, ok in scores.items():
        assert ok, f"{case['id']} failed {name}: {found['authority']}"


def test_identity_topic_does_not_answer_whether_the_road_is_watched():
    topic = {"id": "street", "text": ROAD}
    question = "I ask Sergeant Mara whether the north road is watched."
    assert authored_topic_relevant_to_question(question, topic, speaker_name="Sergeant Mara")
    assert authored_answer_sufficient_for_question(question, topic) is False


def test_prior_topic_does_not_claim_an_authoritative_answer():
    social = {
        "npc_id": "sergeant_mara",
        "npc_name": "Sergeant Mara",
        "target_resolved": True,
        "topic_revealed": None,
        "reply_plan_kind": "authoritative_answer_available",
        "npc_speech_authority": "none",
        "incidental_subjective_allowed": False,
        "objective_world_fact_authority": "none",
    }
    record = attach_dialogue_authority(social, "Who made the lantern, then?", {"name": "Sergeant Mara"}, None)
    assert social["reply_plan_kind"] != "authoritative_answer_available"
    assert social["npc_speech_authority"] == "none"
    assert record["narration_determined"] is True
    assert record["reconciled_plan"] == "authoritative_without_answer"


def test_commitment_survives_save_shape_and_is_not_canonical():
    session = {"conversational_context": {}, "turn_counter": 2}
    social = {
        "npc_id": "sergeant_mara",
        "npc_name": "Sergeant Mara",
        "dialogue_authority": build_dialogue_authority(
            "I ask Mara who forged the lantern.",
            npc={"id": "sergeant_mara", "name": "Sergeant Mara"},
            social={
                "npc_id": "sergeant_mara",
                "npc_name": "Sergeant Mara",
                "reply_plan_kind": "genuine_uncertainty",
                "npc_speech_authority": "none",
            },
        ),
    }
    line = social["dialogue_authority"]["player_line"]
    remembered = remember_dialogue_commitment(
        session, social=social, player_text="I ask Mara who forged the lantern.", line=line, turn=2
    )
    assert remembered["canonical"] is False
    reloaded = copy.deepcopy(session)
    again = build_dialogue_authority(
        "Who forged it?",
        npc={"id": "sergeant_mara", "name": "Sergeant Mara"},
        social={"npc_id": "sergeant_mara", "npc_name": "Sergeant Mara", "reply_plan_kind": "genuine_uncertainty"},
        session=reloaded,
    )
    assert again["player_line"] == line
    assert again["canonical"] is False


def test_chat_unknown_question_skips_narration_and_does_not_invent(tmp_path, monkeypatch):
    from game.api import chat
    from game.models import ChatRequest
    from game import storage
    from tests.test_pr_ed_provider_efficiency import _seed

    _seed(tmp_path, monkeypatch)
    calls = {"n": 0}

    def _boom(*_args, **_kwargs):
        calls["n"] += 1
        return {
            "player_facing_text": 'Sergeant Mara says, "There is usually a patrol, and the password is ash."',
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
        }

    monkeypatch.setattr("game.api.call_gpt", _boom)
    monkeypatch.setattr("game.gm.call_gpt", _boom)
    before = storage.load_world()
    response = chat(ChatRequest(text="I ask Sergeant Mara whether the north road is watched."))
    text = response["gm_output"]["player_facing_text"]
    social = response["resolution"]["social"]
    authority = social["dialogue_authority"]
    assert calls["n"] == 0
    assert social.get("topic_revealed") is None
    assert authority["requested_information"] == "surveillance"
    assert authority["narration_determined"] is True
    assert "street beyond the gate" not in text.lower()
    assert "settled here" not in text.lower()
    assert "usually a patrol" not in text.lower()
    assert "password" not in text.lower()
    assert response_class(text) == "uncertainty"
    after = storage.load_world()
    assert after["npcs"] == before["npcs"]
    session = storage.load_session()
    commitments = session["conversational_context"]["dialogue_commitments"]
    assert commitments[-1]["canonical"] is False
    storage.save_session(session)
    assert storage.load_session()["conversational_context"]["dialogue_commitments"][-1]["text"] == commitments[-1]["text"]


def test_personal_question_keeps_a_harmless_quote_and_skips_retry():
    from game.immutable_valid_response import run_preserve_if_valid

    def _retry(_feedback):
        raise AssertionError("retry")

    resolution = {
        "social": {
            "target_resolved": True,
            "npc_id": "sergeant_mara",
            "npc_name": "Sergeant Mara",
            "dialogue_authority": {
                "improvisation_permitted": True,
                "requested_information": "personal_state",
            },
        },
        "metadata": {
            "resolution_contract": {
                "operation": "ask",
                "interlocutor_id": "sergeant_mara",
                "raw_input": "What troubles you?",
            }
        },
    }
    out = run_preserve_if_valid(
        {
            "player_facing_text": (
                'Sergeant Mara glances at the gate. "It\'s this quiet watch," they say. '
                '"The road beyond is usually calmer at night, but something\'s lurking."'
            ),
            "metadata": {},
        },
        regenerate=_retry,
        resolution=resolution,
        player_text="What troubles you, standing out here?",
        scene={"scene": {"text": "Sergeant Mara looks concerned."}},
        world={},
        session={},
    )
    text = out["player_facing_text"]
    assert text == 'Sergeant Mara says, "The watch wears on me. That is all."'
    assert out["metadata"]["accepted_response"]["authorization_source"] == "conversational_continuity.bounded_personal_line"
    assert "usually calmer" not in text.lower()
    assert "lurking" not in text.lower()
