"""ATGB-R2-02 speech-participant grounding.

Historical rows replay captured interpretations. They are not new model calls.
Unrelated-name cases are related variations written with this repair, not
held-out evidence and not a gameplay-benchmark result.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from game.conversational_orchestration import decision_from_interpretation_record
from game.defaults import default_character
from game.interaction_completion import addressed_person_nominal, speech_participant_head
from game.ordinary_semantic_ownership import assess_addressee_grounding
from game.player_interpretation_bridge import normalized_action_from_interpretation
from game.social import resolve_social_action

ROOT = Path(__file__).resolve().parents[1]
TRACES = ROOT / "artifacts" / "atgb" / "atgb_r2_01" / "representative_traces.json"
WORLD = json.loads((ROOT / "data" / "world.json").read_text(encoding="utf-8"))
SCENE = json.loads((ROOT / "data" / "scenes" / "frontier_gate.json").read_text(encoding="utf-8"))
HIDDEN = (
    "noble house",
    "ash cowl",
    "coordinated signal",
    "paid for in silver",
    "northwest mud track",
    "captain thoran",
    "route changed",
)


def _traces() -> dict[str, dict]:
    rows = json.loads(TRACES.read_text(encoding="utf-8"))
    return {row["turn_id"]: row for row in rows}


def _runner_session() -> dict:
    return {
        "active_scene_id": "frontier_gate",
        "turn_counter": 2,
        "clocks": {"suspicion": 0, "unrest": 0, "danger": 0},
        "interaction_context": {
            "active_interaction_target_id": "tavern_runner",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
            "engagement_level": "engaged",
        },
    }


def _npc(entity_id: str, name: str, *, aliases: list[str] | None = None, description: str = "") -> dict:
    return {
        "id": entity_id,
        "name": name,
        "location": "yard",
        "aliases": aliases or [],
        "description": description,
        "role": "",
        "topics": [],
    }


def _yard(npcs: list[dict]) -> tuple[dict, dict]:
    return {"scene": {"id": "yard", "summary": "A plain yard.", "visible_facts": []}}, {"npcs": npcs}


def _social(active: str | None) -> dict:
    if not active:
        return {"interaction_context": {}}
    return {
        "interaction_context": {
            "active_interaction_kind": "social",
            "active_interaction_target_id": active,
        }
    }


def _ground(text: str, npcs: list[dict], *, active: str | None = None, proposed: str | None = None) -> dict:
    scene, world = _yard(npcs)
    return assess_addressee_grounding(
        text,
        scene=scene,
        world=world,
        session=_social(active),
        proposed_target_id=proposed,
    )


PORTER = _npc("porter_hale", "Porter Hale", aliases=["porter", "hale"])
CLERK = _npc("clerk_ivo", "Clerk Ivo", aliases=["clerk", "ivo"])
USHER = _npc("usher_bel", "Usher Bel", aliases=["usher", "bel"])


@pytest.mark.parametrize(
    ("text", "nominal"),
    [
        ("If I ask you again later, will you still tell me that same thing?", "you"),
        ("Tell me more about that.", "me"),
        ("Can I ask you something else?", "you"),
        ("Can you tell me what happened?", "me"),
        ("Can you tell me more?", "me"),
        ("can i speak with you?", "you"),
        ("I ask you later", "you"),
        ("TELL ME MORE ABOUT THAT.", "ME"),
        ("Can I ask you, again, later?", "you"),
        ('"Tell me more," I say.', "me"),
        ("Clerk Ivo, tell me more.", "Clerk Ivo"),
        ("I turn to Guard B and ask what happened.", "Guard B"),
        ("What did Guard B tell you?", "you"),
        ("I ask Porter Hale whether the road is watched.", "Porter Hale"),
        ("I ask the sergeant again about the patrol.", "the sergeant"),
        ("I ask one of them what happened.", "one of them"),
        ("I ask someone nearby what the shouting was.", "someone nearby"),
        ("Who told you that?", ""),
        ("What did you mean by the north road?", ""),
        ("What did she mean by the road?", ""),
    ],
)
def test_speech_role_nominal_is_not_a_fabricated_name(text: str, nominal: str) -> None:
    assert addressed_person_nominal(text) == nominal


def test_s03_3_replay_keeps_the_established_runner() -> None:
    row = _traces()["S03.3"]
    text = row["player_input"]
    session = _runner_session()
    before = copy.deepcopy(session)
    world = copy.deepcopy(WORLD)
    grounding = assess_addressee_grounding(
        text,
        scene=SCENE,
        world=world,
        session=session,
        proposed_target_id="tavern_runner",
    )
    decision = decision_from_interpretation_record(
        row["adapted_interpretation"],
        player_text=text,
        scene=SCENE,
        world=world,
        session=session,
    )
    public = decision.to_public_dict()
    assert addressed_person_nominal(text) == "you"
    assert grounding["target_id"] == "tavern_runner"
    assert grounding["target_provenance"] == "established_interlocutor"
    assert grounding["operation_eligibility"] == "executable"
    assert grounding["target_resolution"] == "contextual"
    assert "you again later" not in json.dumps(grounding).lower()
    assert public["category"] == "EXECUTE"
    assert public["reason"] == "single_authoritative_component"
    assert public["proposed_target"] == "tavern_runner"
    assert public["player_facing_text"] == ""
    assert public["reason"] != "unresolved_addressee"
    assert "which person" not in public["player_facing_text"].lower()
    pending = ((public.get("context_update") or {}).get("conversational_context") or {}).get("pending_clarification")
    assert pending is None
    assert session == before
    assert world["world_state"] == WORLD["world_state"]


def test_s05_3_replay_grounds_recipient_without_answering_the_subject() -> None:
    row = _traces()["S05.3"]
    text = row["player_input"]
    session = _runner_session()
    before = copy.deepcopy(session)
    record = copy.deepcopy(row["adapted_interpretation"])
    evidence_before = copy.deepcopy(record["public_evidence"])
    grounding = assess_addressee_grounding(
        text,
        scene=SCENE,
        world=WORLD,
        session=session,
        proposed_target_id="tavern_runner",
    )
    decision = decision_from_interpretation_record(
        record,
        player_text=text,
        scene=SCENE,
        world=WORLD,
        session=session,
    )
    public = decision.to_public_dict()
    assert addressed_person_nominal(text) == "me"
    assert grounding["target_id"] == "tavern_runner"
    assert grounding["target_provenance"] == "established_interlocutor"
    assert grounding["operation_eligibility"] == "executable"
    assert "me more" not in json.dumps(grounding).lower()
    assert public["category"] == "EXECUTE"
    assert public["player_facing_text"] == ""
    assert "which person" not in public["player_facing_text"].lower()
    assert "muddy footprints" not in public["player_facing_text"].lower()
    assert record["public_evidence"] == evidence_before
    assert session == before
    # The captured model subject is not adopted as a new host fact.
    assert "subject" not in grounding


def test_established_second_person_keeps_porter() -> None:
    grounding = _ground(
        "Can I ask you something else?",
        [PORTER, CLERK],
        active="porter_hale",
        proposed="porter_hale",
    )
    assert grounding["target_id"] == "porter_hale"
    assert grounding["operation_eligibility"] == "executable"
    assert grounding["target_provenance"] == "established_interlocutor"
    assert grounding["clarification"] == ""


def test_explicit_addressee_change_is_not_overridden_by_the_old_speaker() -> None:
    grounding = _ground(
        "I turn to Clerk Ivo and ask what happened.",
        [PORTER, CLERK],
        active="porter_hale",
        proposed="porter_hale",
    )
    assert grounding["target_id"] == "clerk_ivo"
    assert grounding["operation_eligibility"] == "executable"
    assert grounding["target_provenance"] == "explicit_canonical"
    assert grounding["conflict_status"] == "resolved_by_explicit_wording"
    assert grounding["pending_intention_relationship"] == "starts_new"


def test_second_person_without_a_unique_addressee_stays_unresolved() -> None:
    grounding = _ground(
        "Can you tell me what happened?",
        [PORTER, CLERK],
        active=None,
        proposed="porter_hale",
    )
    assert grounding["target_id"] is None
    assert grounding["operation_eligibility"] == "requires_clarification"
    assert grounding["mutation_eligibility"] is False
    assert grounding["target_resolution"] in {"ambiguous", "unresolved"}
    assert "porter_hale" not in str(grounding["target_id"])


def test_departed_speaker_is_not_still_available() -> None:
    present = [CLERK, USHER]
    grounding = _ground(
        "Can you tell me more?",
        present,
        active="porter_hale",
        proposed="porter_hale",
    )
    assert grounding["target_id"] != "porter_hale"
    assert grounding["target_id"] is None
    assert grounding["operation_eligibility"] == "requires_clarification"
    labels = [choice["entity_id"] for choice in grounding["choices"]]
    assert "porter_hale" not in labels
    assert set(labels) == {"clerk_ivo", "usher_bel"}


def test_third_party_name_stays_the_subject() -> None:
    grounding = _ground(
        "What did Clerk Ivo tell you?",
        [PORTER, CLERK],
        active="porter_hale",
        proposed="porter_hale",
    )
    assert addressed_person_nominal("What did Clerk Ivo tell you?") == "you"
    assert grounding["target_id"] == "porter_hale"
    assert grounding["target_provenance"] == "established_interlocutor"
    assert grounding["target_id"] != "clerk_ivo"


def test_subject_can_stay_unresolved_after_the_recipient_is_known() -> None:
    grounding = _ground(
        "Can you tell me more?",
        [PORTER, CLERK],
        active="porter_hale",
        proposed="porter_hale",
    )
    assert grounding["target_id"] == "porter_hale"
    assert grounding["operation_eligibility"] == "executable"
    assert "subject" not in grounding
    assert grounding["clarification"] == ""


@pytest.mark.parametrize(
    "text",
    [
        "Can I ask you something else?",
        "I will speak with you again.",
        "Please tell me more.",
        "May I ask you later?",
        "We should ask you again later.",
        "Tell us more.",
        "I want you to tell me.",
        "Can I see your notes and ask you again?",
        "ASK YOU LATER.",
        "tell me more",
    ],
)
def test_grammatical_speech_roles_use_the_established_addressee(text: str) -> None:
    nominal = addressed_person_nominal(text)
    assert nominal.lower() in {"you", "me", "us", "your"}
    grounding = _ground(text, [PORTER, CLERK, USHER], active="usher_bel", proposed="usher_bel")
    assert grounding["target_id"] == "usher_bel"
    assert grounding["operation_eligibility"] == "executable"
    assert nominal.lower() not in {npc["id"] for npc in (PORTER, CLERK, USHER)}


def test_mismatched_provider_candidate_does_not_replace_the_speech_role() -> None:
    grounding = _ground(
        "Can I ask you something else?",
        [PORTER, CLERK],
        active="porter_hale",
        proposed="clerk_ivo",
    )
    assert grounding["target_id"] is None
    assert grounding["operation_eligibility"] == "requires_clarification"
    assert grounding["conflict_details"]["provider_target"] == "clerk_ivo"
    assert grounding["conflict_details"]["established_interlocutor"] == "porter_hale"


def test_nonunique_and_unknown_references_still_clarify() -> None:
    someone = _ground(
        "I ask someone nearby what the shouting was.",
        [PORTER, CLERK],
        active="porter_hale",
        proposed="clerk_ivo",
    )
    either = _ground("I ask either clerk about the ledger.", [PORTER, CLERK], active="porter_hale")
    missing = _ground(
        "I ask Warden Cole what happened.",
        [PORTER, CLERK],
        active="porter_hale",
        proposed="porter_hale",
    )
    for grounding in (someone, either, missing):
        assert grounding["target_id"] is None
        assert grounding["operation_eligibility"] == "requires_clarification"
        assert grounding["mutation_eligibility"] is False


def test_first_person_and_possessive_roles_are_not_npc_names() -> None:
    assert speech_participant_head("I again later") == "I"
    assert addressed_person_nominal("I ask I later.") == "I"
    speaker = _ground("I ask I later.", [PORTER, CLERK], active="porter_hale", proposed="porter_hale")
    assert speaker["target_id"] == "porter_hale"
    assert speaker["target_id"] != "i"
    mine = _ground(
        "I speak with my clerk.",
        [PORTER, CLERK],
        active="porter_hale",
        proposed="porter_hale",
    )
    assert addressed_person_nominal("I speak with my clerk.") == "clerk"
    assert mine["target_id"] == "clerk_ivo"
    yours = _ground(
        "I speak with your clerk again.",
        [PORTER, CLERK],
        active="porter_hale",
        proposed="porter_hale",
    )
    assert addressed_person_nominal("I speak with your clerk again.") == "clerk"
    assert yours["target_id"] == "clerk_ivo"
    party = _ground("We need you to tell us more.", [PORTER, CLERK], active="porter_hale", proposed="porter_hale")
    assert addressed_person_nominal("We need you to tell us more.").lower() in {"you", "us"}
    assert party["target_id"] == "porter_hale"


def test_single_visible_pronoun_still_uses_unique_context() -> None:
    grounding = _ground("I ask him what he saw.", [PORTER], active=None, proposed="porter_hale")
    assert grounding["target_id"] == "porter_hale"
    assert grounding["target_provenance"] == "unique_contextual"


def test_third_person_gm_question_does_not_inherit_the_speaker() -> None:
    scene, world = _yard([PORTER, CLERK])
    grounding = assess_addressee_grounding(
        "What did she mean by the road?",
        scene=scene,
        world=world,
        session=_social("porter_hale"),
        proposed_target_id="porter_hale",
    )
    assert grounding["target_id"] is None
    assert grounding["operation_eligibility"] == "not_assessed"
    assert grounding["direct_address"] is False


def test_speech_role_authority_matches_an_explicit_address() -> None:
    explicit = _ground(
        "I ask Porter Hale what happened.",
        [PORTER, CLERK],
        active="porter_hale",
        proposed="clerk_ivo",
    )
    role = _ground(
        "Can I ask you what happened?",
        [PORTER, CLERK],
        active="porter_hale",
        proposed="porter_hale",
    )
    assert explicit["target_id"] == "porter_hale"
    assert role["target_id"] == "porter_hale"
    assert explicit["operation_eligibility"] == role["operation_eligibility"] == "executable"
    assert explicit["mutation_eligibility"] is True
    assert role["mutation_eligibility"] is True
    assert explicit["allowed_operation"] == role["allowed_operation"] == "ask"


def test_bridge_still_rejects_an_absent_target_and_an_ambiguous_you() -> None:
    row = copy.deepcopy(_traces()["S03.3"]["adapted_interpretation"])
    accepted, meta = normalized_action_from_interpretation(
        row,
        scene=SCENE,
        world=WORLD,
        player_text="If I ask you again later, will you still tell me that same thing?",
        session=_runner_session(),
    )
    assert meta["accepted"] is True
    assert meta["target_ref"] == "tavern_runner"
    assert accepted["target_id"] == "tavern_runner"

    departed = copy.deepcopy(WORLD)
    for npc in departed["npcs"]:
        if npc["id"] == "tavern_runner":
            npc["location"] = "elsewhere"
    speech = assess_addressee_grounding(
        "If I ask you again later, will you still tell me that same thing?",
        scene=SCENE,
        world=departed,
        session=_runner_session(),
        proposed_target_id="tavern_runner",
    )
    assert speech["target_id"] != "tavern_runner"
    assert speech["operation_eligibility"] == "requires_clarification"
    rejected, rejection = normalized_action_from_interpretation(
        row,
        scene=SCENE,
        world=departed,
        player_text="I ask the Tavern Runner about the rumor.",
        session=_runner_session(),
        authorized_target_id="tavern_runner",
    )
    assert rejected is None
    assert rejection["accepted"] is False
    assert rejection["reason"] == "target_not_visible"

    ambiguous = {
        "communication_mode": "IN_WORLD_ACTION",
        "interpretation_status": "INTERPRETED",
        "communication": {"recipient": "NPC", "purpose": "QUESTION", "evidence_refs": []},
        "action_components": [{"operation_class": "ASK", "target_ref": "porter_hale", "description": "ask"}],
        "references": {"permitted_entity_ids": ["porter_hale"], "unresolved_references": []},
        "public_evidence": {},
    }
    scene, world = _yard([PORTER, CLERK])
    action, bridge = normalized_action_from_interpretation(
        ambiguous,
        scene=scene,
        world=world,
        player_text="Can you tell me what happened?",
        session=_social(None),
    )
    assert action is None
    assert bridge["accepted"] is False
    assert bridge["reason"] == "ambiguous_addressee"


def test_resolver_does_not_gain_hidden_facts_from_the_grounded_ask() -> None:
    text = "Tell me more about that."
    session = _runner_session()
    session["npc_runtime"] = {
        "tavern_runner": {"revealed_topics": ["patrol_rumor"]},
    }
    world = copy.deepcopy(WORLD)
    before_world = copy.deepcopy(world)
    before_clocks = copy.deepcopy(session["clocks"])
    before_turn = session["turn_counter"]
    explicit = resolve_social_action(
        SCENE,
        copy.deepcopy(session),
        copy.deepcopy(world),
        {
            "id": "tavern_runner",
            "label": "Tavern Runner",
            "type": "question",
            "prompt": "I ask the Tavern Runner to tell me more about that.",
            "target_id": "tavern_runner",
        },
        raw_player_text="I ask the Tavern Runner to tell me more about that.",
        character=default_character(),
        turn_counter=2,
    )
    role = resolve_social_action(
        SCENE,
        session,
        world,
        {
            "id": "tavern_runner",
            "label": "Tavern Runner",
            "type": "question",
            "prompt": text,
            "target_id": "tavern_runner",
        },
        raw_player_text=text,
        character=default_character(),
        turn_counter=2,
    )
    blob = json.dumps(role).lower()
    for forbidden in HIDDEN:
        assert forbidden not in blob
    assert role.get("social", {}).get("npc_id") == explicit.get("social", {}).get("npc_id") == "tavern_runner"
    assert world["world_state"] == before_world["world_state"]
    assert world["factions"] == before_world["factions"]
    assert session["clocks"] == before_clocks
    assert session["turn_counter"] == before_turn
    # Subject text is the resolver's existing authored-topic choice, not a new host fact.
    role_topic = ((role.get("social") or {}).get("topic_revealed") or {})
    explicit_topic = ((explicit.get("social") or {}).get("topic_revealed") or {})
    assert role_topic.get("id") == explicit_topic.get("id")
    assert role_topic.get("text") == explicit_topic.get("text")
