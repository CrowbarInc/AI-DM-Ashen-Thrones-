"""PR-PLAY-40: action admission outside the Cinderwatch fixture.

Synthetic scenes use different ids, labels, and descriptions. No provider client
is constructed. A failed recognition is recorded as a non-invention result.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from game.conversational_orchestration import (
    authored_travel_admission,
    decision_from_interpretation_record,
    unavailable_referent_decision,
)
from game.intent_parser import parse_freeform_to_action
from game.ordinary_semantic_ownership import assess_addressee_grounding
from game.route_authority import route_status

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "validation" / "atgb" / "baselines" / "frontier-gate-v1"


def _banquet():
    scene = {
        "scene": {
            "id": "amber_hall",
            "location": "The Amber Hall",
            "summary": "Three people linger after the feast.",
            "visible_facts": [
                "Lady Vesper discusses political rumors at the high table.",
                "Master Quill discusses caravan trade beside the salt cellar.",
                "Pell discusses palace gossip near the side door.",
            ],
            "exits": [],
            "interactables": [],
        }
    }
    world = {
        "npcs": [
            {
                "id": "lady_vesper",
                "name": "Lady Vesper",
                "location": "amber_hall",
                "aliases": ["noble"],
                "description": "discusses political rumors at the high table",
                "topics": [{"id": "court_whisper", "discovery_categories": ["rumor"], "text": "The harbor levy split the council."}],
            },
            {
                "id": "master_quill",
                "name": "Master Quill",
                "location": "amber_hall",
                "aliases": ["merchant"],
                "description": "discusses caravan trade and market rumors",
                "topics": [{"id": "salt_prices", "text": "Salt prices rose after the estuary closed."}],
            },
            {
                "id": "pell_servant",
                "name": "Pell",
                "location": "amber_hall",
                "aliases": ["servant"],
                "description": "discusses palace gossip in the service corridor",
                "topics": [{"id": "buttery_letter", "discovery_categories": ["rumor"], "text": "The steward hid a letter in the buttery."}],
            },
        ]
    }
    return scene, world


def _dungeon():
    scene = {
        "scene": {
            "id": "cistern_junction",
            "location": "Cistern Junction",
            "summary": "Three ways leave the wet stone room.",
            "visible_facts": ["Water drips from a crack overhead."],
            "discoverable_clues": [],
            "exits": [
                {"label": "Descending staircase", "target_scene_id": "lower_cistern"},
                {"label": "Flooded passage", "target_scene_id": "drowned_gallery", "locked": True},
                {"label": "Collapsed ceiling opening", "target_scene_id": "roof_crack"},
            ],
            "interactables": [],
        }
    }
    return scene, {"npcs": []}


def _wild():
    scene = {
        "scene": {
            "id": "briar_crossroads",
            "location": "Briar Crossroads",
            "summary": "Two trails and a closed ford meet at a standing stone.",
            "visible_facts": ["A standing stone marks the fork."],
            "discoverable_clues": [
                {"id": "stone_scratch", "text": "A fresh scratch marks the standing stone."}
            ],
            "exits": [
                {"label": "North quarry trail", "target_scene_id": "quarry_lip"},
                {"label": "South quarry trail", "target_scene_id": "quarry_floor"},
                {"label": "Washed-out ford", "target_scene_id": "far_bank", "locked": True},
            ],
            "interactables": [
                {
                    "id": "standing_stone",
                    "label": "Standing stone",
                    "aliases": ["stone", "cairn", "marker stone"],
                    "type": "investigate",
                    "reveals_clue": "stone_scratch",
                }
            ],
        }
    }
    world = {
        "npcs": [
            {
                "id": "wayfinder_bramble",
                "name": "Wayfinder Bramble",
                "location": "briar_crossroads",
                "aliases": ["wayfinder"],
                "description": "watches the ford and warns travelers off the washed crossing",
                "topics": [{"id": "ford_warning", "text": "The ford is closed until the water drops."}],
            }
        ]
    }
    return scene, world


def _ground(text, scene, world, session=None, proposed=None):
    return assess_addressee_grounding(
        text, scene=scene, world=world, session=session or {}, proposed_target_id=proposed,
    )


def test_banquet_explicit_servant_and_unique_gossip_resolve():
    scene, world = _banquet()
    before = copy.deepcopy(world)
    servant = _ground("I ask the servant what was overheard in the corridor.", scene, world)
    gossip = _ground("What palace gossip is being repeated?", scene, world)
    assert servant["target_id"] == "pell_servant"
    assert servant["operation_eligibility"] == "executable"
    assert gossip["target_id"] == "pell_servant"
    assert gossip["target_provenance"] == "unique_contextual"
    assert world == before


def test_banquet_shared_rumor_word_clarifies_and_unknown_guest_is_not_created():
    scene, world = _banquet()
    before = copy.deepcopy(world)
    shared = _ground("Have you heard any interesting rumors lately?", scene, world, proposed="lady_vesper")
    unknown = _ground("I ask Duke Halvern what he wants from the feast.", scene, world, proposed="duke_halvern")
    assert shared["target_id"] is None
    assert shared["operation_eligibility"] == "requires_clarification"
    assert {choice["entity_id"] for choice in shared["choices"]} == {"lady_vesper", "master_quill"}
    assert unknown["target_id"] is None
    assert unknown["operation_eligibility"] != "executable"
    assert all(npc["id"] != "duke_halvern" for npc in world["npcs"])
    assert world == before


def test_banquet_established_conversation_continues_without_a_new_person():
    scene, world = _banquet()
    session = {
        "interaction_context": {
            "active_interaction_kind": "social",
            "active_interaction_target_id": "pell_servant",
        }
    }
    continued = _ground("What else can you tell me?", scene, world, session=session, proposed="pell_servant")
    assert continued["target_id"] == "pell_servant"
    assert continued["target_provenance"] == "established_interlocutor"
    assert all(npc["id"] != "invented_guest" for npc in world["npcs"])


def test_dungeon_known_label_resolves_and_paraphrase_does_not_invent():
    scene, world = _dungeon()
    before = copy.deepcopy(scene)
    taken = authored_travel_admission(
        "I take the descending staircase.", scene=scene, world=world, session={},
    )
    downstairs = authored_travel_admission(
        "I head downstairs.", scene=scene, world=world, session={},
    )
    ceiling = authored_travel_admission(
        "I climb through the hole in the ceiling.", scene=scene, world=world, session={},
    )
    secret = authored_travel_admission(
        "I leave through the secret door.", scene=scene, world=world, session={},
    )
    assert taken is not None and taken.category.value == "EXECUTE"
    assert taken.proposed_target == "leave_for_descending_staircase"
    assert downstairs is None
    assert ceiling is None
    assert secret is None or secret.category.value != "EXECUTE"
    parsed = parse_freeform_to_action("I head downstairs.", scene, session={}, world=world)
    assert parsed is None or not parsed.get("target_scene_id")
    assert scene == before


def test_dungeon_blocked_passage_stays_blocked_and_stay_does_not_move():
    scene, world = _dungeon()
    flooded = authored_travel_admission(
        "I take the flooded passage.", scene=scene, world=world, session={},
    )
    assert flooded is not None and flooded.category.value == "EXECUTE"
    row = next(row for row in scene["scene"]["exits"] if row["label"] == "Flooded passage")
    assert route_status(row, "cistern_junction", {}, world) == "blocked"
    stay = parse_freeform_to_action("I stay here.", scene, session={}, world=world)
    assert stay is not None
    assert stay.get("type") != "scene_transition"
    assert (stay.get("metadata") or {}).get("parser_lane") == "explicit_stay"
    assert stay.get("target_scene_id") in {None, ""}


def test_dungeon_clarification_record_does_not_override_a_unique_label():
    scene, world = _dungeon()
    record = {
        "interpretation_status": "CLARIFICATION_REQUIRED",
        "clarification_question": "How do you want to take the stairs, and with whom?",
        "action_components": [],
        "references": {"unresolved_references": []},
    }
    decision = decision_from_interpretation_record(
        record, player_text="I take the descending staircase.", scene=scene, world=world, session={},
    )
    assert decision.category.value == "EXECUTE"
    assert decision.proposed_operation == "MOVE"
    assert "with whom" not in decision.player_facing_text.casefold()


def test_wilderness_named_trail_blocked_ford_npc_and_landmark():
    scene, world = _wild()
    named = authored_travel_admission(
        "I follow the north quarry trail.", scene=scene, world=world, session={},
    )
    ambiguous = authored_travel_admission(
        "I follow the quarry trail.", scene=scene, world=world, session={},
    )
    blocked = authored_travel_admission(
        "I take the washed-out ford.", scene=scene, world=world, session={},
    )
    speaker = _ground("I speak to Wayfinder Bramble about the crossing.", scene, world)
    looked = parse_freeform_to_action("I examine the standing stone.", scene, session={}, world=world)
    missing = unavailable_referent_decision(
        "I examine the silver compass.",
        {
            "interpretation_status": "CLARIFICATION_REQUIRED",
            "clarification_question": "With what means?",
            "references": {"unresolved_references": ["silver compass"]},
        },
        scene=scene,
        world=world,
    )
    assert named is not None and named.category.value == "EXECUTE"
    assert named.proposed_target == "leave_for_north_quarry_trail"
    assert ambiguous is not None and ambiguous.category.value == "CLARIFY"
    assert blocked is not None and blocked.category.value == "EXECUTE"
    ford = next(row for row in scene["scene"]["exits"] if "ford" in row["label"].casefold())
    assert route_status(ford, "briar_crossroads", {}, world) == "blocked"
    assert speaker["target_id"] == "wayfinder_bramble"
    assert speaker["operation_eligibility"] == "executable"
    assert looked is not None and looked.get("type") == "investigate"
    assert looked.get("target_id") == "standing_stone"
    assert missing is not None and missing.reason == "referent_not_in_scene"
    assert "silver compass" not in json.dumps(scene)


def test_frontier_fixture_supports_notice_travel_and_destination_prints_only():
    gate = json.loads((FIXTURE / "scenes" / "frontier_gate.json").read_text(encoding="utf-8"))
    milestone = json.loads((FIXTURE / "scenes" / "old_milestone.json").read_text(encoding="utf-8"))
    market = json.loads((FIXTURE / "scenes" / "market_quarter.json").read_text(encoding="utf-8"))
    gate_ids = [item.get("id") for item in gate["scene"].get("interactables") or []]
    mile_ids = [item.get("id") for item in milestone["scene"].get("interactables") or []]
    assert gate_ids == ["notice_board"]
    assert "prints" not in gate_ids
    assert "prints" in mile_ids
    print_aliases = next(item["aliases"] for item in milestone["scene"]["interactables"] if item["id"] == "prints")
    assert "footprints" in print_aliases
    assert market["scene"]["id"] == "market_quarter"
    assert market["scene"].get("interactables") in (None, [])
    notice = parse_freeform_to_action("I examine the notice board.", gate, session={}, world={"npcs": []})
    absent = parse_freeform_to_action("I examine the footprints.", gate, session={}, world={"npcs": []})
    present = parse_freeform_to_action("I examine the footprints.", milestone, session={}, world={"npcs": []})
    assert notice is not None and notice.get("target_id") == "notice_board"
    assert absent is None or absent.get("target_id") != "prints"
    assert present is not None and present.get("target_id") == "prints"
