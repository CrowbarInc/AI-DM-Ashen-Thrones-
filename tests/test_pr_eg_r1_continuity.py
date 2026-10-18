"""PR-EG-R1 conversational continuity. Expectations were frozen before the repair."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from game.conversational_continuity import (
    continuity_directive,
    delivered_exchanges,
    record_delivered_exchange,
)
from game.dialogue_authority import (
    attach_dialogue_authority,
    build_dialogue_authority,
    remember_dialogue_commitment,
)

pytestmark = pytest.mark.unit

HOLDOUTS = json.loads(
    (Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "pr_eg_r1_continuity_holdouts.json").read_text(
        encoding="utf-8"
    )
)
SCENE = "courtyard"
ROAD = {
    "speaker_id": "sergeant_mara",
    "speaker_name": "Sergeant Mara",
    "ownership": "npc",
    "player_text": "I ask Sergeant Mara what the street beyond the gate is called.",
    "delivered_text": 'Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."',
    "supplied_text": "Word is, the street beyond the gate is the north road.",
    "subject": "street",
    "requested_information": "general",
    "uncertain": False,
    "scene_id": SCENE,
    "turn": 2,
    "active": False,
}
PREFERENCE = {
    "speaker_id": "sergeant_mara",
    "speaker_name": "Sergeant Mara",
    "ownership": "npc",
    "player_text": "Do you prefer the morning or the evening?",
    "delivered_text": 'Sergeant Mara says, "I prefer the morning."',
    "supplied_text": "I prefer the morning.",
    "subject": "morning",
    "requested_information": "opinion",
    "uncertain": False,
    "scene_id": SCENE,
    "turn": 3,
    "active": True,
}
WATCH = {
    "speaker_id": "sergeant_mara",
    "speaker_name": "Sergeant Mara",
    "ownership": "npc",
    "player_text": "Has anyone been keeping an eye on it after dark?",
    "delivered_text": 'Sergeant Mara says, "I couldn\'t tell you."',
    "supplied_text": "I couldn't tell you.",
    "subject": "after dark",
    "requested_information": "surveillance",
    "uncertain": True,
    "scene_id": SCENE,
    "turn": 4,
    "active": True,
}
BREN = {
    "speaker_id": "corporal_bren",
    "speaker_name": "Corporal Bren",
    "ownership": "npc",
    "player_text": "What did you see?",
    "delivered_text": 'Corporal Bren says, "I saw the lantern."',
    "supplied_text": "I saw the lantern.",
    "subject": "lantern",
    "requested_information": "general",
    "uncertain": False,
    "scene_id": SCENE,
    "turn": 5,
    "active": True,
}
LIBRARY = {"road": ROAD, "preference": PREFERENCE, "watch_unknown": WATCH, "bren_line": BREN}


def _world(present: list[str]) -> dict:
    people = [
        ("sergeant_mara", "Sergeant Mara"),
        ("corporal_bren", "Corporal Bren"),
    ]
    return {
        "npcs": [
            {
                "id": npc_id,
                "name": name,
                "location": SCENE if npc_id in present else "elsewhere",
                "role": "guard",
            }
            for npc_id, name in people
        ]
    }


def _session(case: dict) -> dict:
    active = case.get("active") or ""
    session = {
        "conversational_context": {
            "delivered_exchanges": [copy.deepcopy(LIBRARY[name]) for name in case.get("exchanges") or []],
        },
        "interaction_context": {
            "active_interaction_kind": "social" if active else None,
            "active_interaction_target_id": active or None,
        },
    }
    if case.get("executed"):
        session["conversational_context"]["last_executed_intention"] = {
            "status": "executed",
            "text": "I ask Sergeant Mara what troubles her.",
            "operation": "ASK",
            "target": "sergeant_mara",
            "scene_id": SCENE,
        }
    if case.get("pending_move"):
        session["conversational_context"]["pending_intention"] = {
            "status": "pending",
            "operation": "MOVE",
            "scene_id": SCENE,
            "text": "I walk through the gate.",
        }
    if "morning" in (case.get("commitments") or []):
        session["conversational_context"]["dialogue_commitments"] = [
            {
                "npc_id": "sergeant_mara",
                "kind": "opinion",
                "subject": "morning",
                "text": 'Sergeant Mara says, "I prefer the morning."',
                "canonical": False,
                "status": "active",
                "turn": 3,
            }
        ]
    return session


def _scene() -> dict:
    return {"scene": {"id": SCENE}}


def _directive(case: dict):
    return continuity_directive(
        case["player"],
        session=_session(case),
        scene=_scene(),
        world=_world(case.get("present") or []),
    )


def _contains(text: str, bits: list[str] | None) -> bool:
    lowered = text.lower()
    return all(bit.lower() in lowered for bit in (bits or []))


def _excludes(text: str, bits: list[str] | None) -> bool:
    lowered = text.lower()
    return all(bit.lower() not in lowered for bit in (bits or []))


@pytest.mark.parametrize("case", HOLDOUTS["cases"], ids=[row["id"] for row in HOLDOUTS["cases"]])
def test_frozen_continuity_holdout(case):
    if case.get("expect_bound"):
        session = {"conversational_context": {}}
        social = {
            "npc_id": "sergeant_mara",
            "dialogue_authority": {
                "knowledge_posture": "belief",
                "npc_id": "sergeant_mara",
                "subject": "morning",
                "requested_information": "opinion",
            },
        }
        for number in range(30):
            social["dialogue_authority"]["subject"] = f"remark {number}"
            remember_dialogue_commitment(
                session,
                social=social,
                player_text=f"remark {number}",
                line=f'Sergeant Mara says, "Note {number}."',
                turn=number,
            )
        rows = session["conversational_context"]["dialogue_commitments"]
        assert len(rows) <= case["expect_bound"]
        assert all(row.get("canonical") is False for row in rows)
        return

    directive = _directive(case)
    action = None if directive is None else directive.get("action")
    if "expect_action" in case:
        assert action == case["expect_action"], directive
    if case.get("expect_npc"):
        assert directive["npc_id"] == case["expect_npc"]
    if case.get("expect_ownership"):
        assert directive["owner"] == case["expect_ownership"]
    if case.get("expect_reason"):
        assert directive["reason"] == case["expect_reason"]
    line = "" if directive is None else str(directive.get("line") or "")
    if case.get("must_contain"):
        assert _contains(line, case["must_contain"]), line
    if case.get("must_not_contain"):
        assert _excludes(line, case["must_not_contain"]), line
    if case.get("must_not_execute"):
        assert action != "ask"

    session = _session(case)
    if case.get("rejected"):
        assert case["rejected"] not in json.dumps(session)

    if case.get("quote_must_contain") or case.get("quote_must_not_contain"):
        authority = build_dialogue_authority(
            case["player"],
            npc={"id": "sergeant_mara", "name": "Sergeant Mara"},
            social={"npc_id": "sergeant_mara", "npc_name": "Sergeant Mara", "reply_plan_kind": "genuine_uncertainty"},
            session=session,
        )
        quote = str(authority.get("player_line") or "")
        assert authority.get("narration_determined") is True
        assert _contains(quote, case.get("quote_must_contain"))
        assert _excludes(quote, case.get("quote_must_not_contain"))
        assert "password" not in quote.lower()

    if case.get("expect_reuse"):
        authority = build_dialogue_authority(
            case["player"],
            npc={"id": "sergeant_mara", "name": "Sergeant Mara"},
            social={
                "npc_id": "sergeant_mara",
                "npc_name": "Sergeant Mara",
                "reply_plan_kind": "genuine_uncertainty",
                "incidental_subjective_allowed": True,
            },
            session=session,
        )
        assert authority["reuse_prior_speech"] is True
        assert authority["narration_determined"] is True
        assert _contains(authority["player_line"], case.get("reuse_must_contain"))
        social = {
            "npc_id": "sergeant_mara",
            "npc_name": "Sergeant Mara",
            "reply_plan_kind": "genuine_uncertainty",
            "npc_speech_authority": "claim_only",
            "incidental_subjective_allowed": True,
        }
        attach_dialogue_authority(social, case["player"], {"id": "sergeant_mara", "name": "Sergeant Mara"}, session)
        assert social["incidental_subjective_allowed"] is False
        assert social["npc_speech_authority"] == "none"

    if case.get("save_load"):
        stored = {"conversational_context": {}}
        record_delivered_exchange(
            stored,
            player_text=ROAD["player_text"],
            delivered_text=ROAD["delivered_text"],
            scene_id=SCENE,
            turn=2,
            ownership="npc",
            social={
                "npc_id": "sergeant_mara",
                "npc_name": "Sergeant Mara",
                "dialogue_authority": {
                    "npc_id": "sergeant_mara",
                    "npc_name": "Sergeant Mara",
                    "subject": "street",
                    "requested_information": "general",
                    "knowledge_posture": "established",
                },
            },
        )
        reloaded = copy.deepcopy(stored)
        again = record_delivered_exchange(
            reloaded,
            player_text=ROAD["player_text"],
            delivered_text=ROAD["delivered_text"],
            scene_id=SCENE,
            turn=2,
            ownership="npc",
            social={
                "npc_id": "sergeant_mara",
                "npc_name": "Sergeant Mara",
                "dialogue_authority": {
                    "npc_id": "sergeant_mara",
                    "npc_name": "Sergeant Mara",
                    "subject": "street",
                    "knowledge_posture": "established",
                },
            },
        )
        assert len(delivered_exchanges(reloaded)) == 1
        assert again["delivered_text"] == ROAD["delivered_text"]
        assert "password" not in json.dumps(reloaded).lower()


def test_personal_ignorance_is_replaced_without_a_retry():
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
                "requested_information": "opinion",
            },
        },
        "metadata": {
            "resolution_contract": {
                "operation": "ask",
                "interlocutor_id": "sergeant_mara",
                "raw_input": "Do you prefer the morning or the evening?",
            }
        },
    }
    out = run_preserve_if_valid(
        {"player_facing_text": 'Sergeant Mara says, "I do not know enough to answer that."', "metadata": {}},
        regenerate=_retry,
        resolution=resolution,
        player_text="Do you prefer the morning or the evening?",
        scene={"scene": {"id": SCENE}},
        world={},
        session={},
    )
    text = out["player_facing_text"].lower()
    assert "prefer" in text
    assert "do not know enough" not in text
    assert "patrol" not in text
    assert "silver" not in text


def test_followup_quotes_the_delivered_line_without_narration(tmp_path, monkeypatch):
    from game.api import chat
    from game.models import ChatRequest
    from game import storage
    from tests.test_pr_ed_provider_efficiency import _seed

    _seed(tmp_path, monkeypatch)
    session = storage.load_session()
    session["interaction_context"] = {
        "active_interaction_kind": "social",
        "active_interaction_target_id": "sergeant_mara",
    }
    record_delivered_exchange(
        session,
        player_text="I ask Sergeant Mara what the street beyond the gate is called.",
        delivered_text='Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."',
        scene_id="waystation_courtyard",
        turn=1,
        ownership="npc",
        social={
            "npc_id": "sergeant_mara",
            "npc_name": "Sergeant Mara",
            "dialogue_authority": {
                "npc_id": "sergeant_mara",
                "npc_name": "Sergeant Mara",
                "subject": "street",
                "requested_information": "general",
                "knowledge_posture": "established",
            },
        },
    )
    storage.save_session(session)
    calls = {"n": 0}

    def _boom(*_args, **_kwargs):
        calls["n"] += 1
        return {"player_facing_text": 'Sergeant Mara says, "I couldn\'t tell you."', "tags": []}

    monkeypatch.setattr("game.api.call_gpt", _boom)
    monkeypatch.setattr("game.gm.call_gpt", _boom)
    response = chat(ChatRequest(text="What did you mean by that?"))
    text = response["gm_output"]["player_facing_text"]
    assert calls["n"] == 0
    assert "north road" in text.lower()
    assert "not been established" not in text.lower()
    assert "couldn't tell you" not in text.lower()
