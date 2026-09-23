"""PR-BH: explicit addressee identity must constrain NPC selection.

Authored names, aliases, and roles still bind. Unsupported titles/names must
not collapse onto a present NPC via a shared prefix token or sole-NPC fallback.
"""
from __future__ import annotations

from copy import deepcopy

from game.defaults import default_character, default_session
from game.intent_parser import segment_mixed_player_turn
from game.interaction_context import (
    find_addressed_npc_id_for_turn,
    rebuild_active_scene_entities,
    resolve_authoritative_social_target,
    resolve_declared_actor_switch,
)
from game.social import authoritative_knowledge_npc_ids_for_speaker, resolve_social_action

RECOVERED = 'I turn to the Gate Serjeant. "Did the census choke change the route?"'

GATE_ADDRESSABLES = [
    {
        "id": "guard_captain",
        "name": "Guard Captain",
        "scene_id": "frontier_gate",
        "kind": "npc",
        "addressable": True,
        "address_priority": 0,
        "address_roles": ["guard", "watchman", "sentry", "guardsman", "captain"],
        "aliases": [],
    },
    {
        "id": "tavern_runner",
        "name": "Tavern Runner",
        "scene_id": "frontier_gate",
        "kind": "npc",
        "addressable": True,
        "address_priority": 1,
        "address_roles": ["runner", "informant"],
        "aliases": [],
    },
]

GATE_NPCS = [
    {
        "id": "gate_guard",
        "name": "Gate Guard",
        "location": "frontier_gate",
        "role": "guard",
        "aliases": ["guard", "watch", "watch guard"],
        "topics": [
            {"id": "watch_command", "text": "Captain Thoran commands the gate watch tonight."}
        ],
    },
    {
        "id": "gate_serjeant",
        "name": "Gate Serjeant",
        "location": "frontier_gate",
        "aliases": ["serjeant", "watch serjeant", "gate serjeant"],
        "topics": [
            {
                "id": "route_change",
                "text": "The patrol route changed after the Ash Compact census choke worsened.",
            }
        ],
    },
    {
        "id": "tavern_runner",
        "name": "Tavern Runner",
        "location": "frontier_gate",
        "aliases": ["runner", "tavern runner"],
        "topics": [{"id": "patrol_rumor", "text": "The runner heard a rumor."}],
    },
]


def _scene(addressables=None) -> dict:
    return {
        "scene": {
            "id": "frontier_gate",
            "addressables": deepcopy(addressables if addressables is not None else GATE_ADDRESSABLES),
            "visible_facts": [],
            "hidden_facts": [],
            "discoverable_clues": [],
            "interactables": [],
            "exits": [],
        }
    }


def _pack(npcs: list[dict], addressables=None) -> tuple[dict, dict, dict]:
    scene = _scene(addressables)
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    session["interaction_context"] = {}
    session["character"] = default_character()
    world = {"npcs": deepcopy(npcs), "settlements": [], "factions": []}
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    return session, world, scene


def _auth(text: str, session: dict, world: dict, scene: dict) -> dict:
    return resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text=text,
        scene_envelope=scene,
        segmented_turn=segment_mixed_player_turn(text),
    )


def _bind(text: str, session: dict, world: dict, scene: dict) -> tuple[str | None, str | None]:
    addressed = find_addressed_npc_id_for_turn(text, session, world, scene)
    auth = _auth(text, session, world, scene)
    return addressed, auth.get("npc_id")


def test_recovered_gate_serjeant_binds_authored_serjeant_not_guard():
    session, world, scene = _pack(GATE_NPCS)
    addressed, auth_id = _bind(RECOVERED, session, world, scene)
    assert addressed == "gate_serjeant"
    assert auth_id == "gate_serjeant"
    sw = resolve_declared_actor_switch(
        session=session,
        scene=scene,
        segmented_turn=segment_mixed_player_turn(RECOVERED),
        raw_text=RECOVERED,
    )
    assert sw.get("target_actor_id") == "gate_serjeant"
    knowledge = authoritative_knowledge_npc_ids_for_speaker(
        world=world,
        session=session,
        scene_id="frontier_gate",
        speaker_id="gate_serjeant",
        speaker_name="Gate Serjeant",
        scene=scene,
    )
    assert "gate_serjeant" in knowledge
    assert "gate_guard" not in knowledge


def test_canonical_and_alias_identities_still_bind():
    session, world, scene = _pack(GATE_NPCS)
    assert _bind('I turn to the Gate Guard. "What happened here?"', session, world, scene) == (
        "gate_guard",
        "gate_guard",
    )
    assert _bind("Gate Guard, what happened here?", session, world, scene) == (
        "gate_guard",
        "gate_guard",
    )
    assert _bind("Serjeant, what happened here?", session, world, scene) == (
        "gate_serjeant",
        "gate_serjeant",
    )
    assert _bind("Gate Serjeant, what happened here?", session, world, scene) == (
        "gate_serjeant",
        "gate_serjeant",
    )
    assert _bind("Captain, what happened here?", session, world, scene) == (
        "guard_captain",
        "guard_captain",
    )
    assert _bind("Runner, what happened here?", session, world, scene) == (
        "tavern_runner",
        "tavern_runner",
    )


def test_later_to_the_guard_beats_earlier_pronoun_preposition():
    session, world, scene = _pack(
        [
            GATE_NPCS[0],
            {
                "id": "ragged_stranger",
                "name": "Ragged Stranger",
                "location": "frontier_gate",
                "topics": [],
            },
        ],
        addressables=[],
    )
    text = "I look back at him, then to the guard — any word on the patrol?"
    addressed, auth_id = _bind(text, session, world, scene)
    assert addressed == "gate_guard"
    assert auth_id == "gate_guard"


def test_ordinary_guard_role_still_binds_when_authority_is_clear():
    session, world, scene = _pack([GATE_NPCS[0]], addressables=[])
    addressed, auth_id = _bind("Guard, what happened here?", session, world, scene)
    assert addressed == "gate_guard"
    assert auth_id == "gate_guard"
    addressed, auth_id = _bind('I turn to the guard. "What happened here?"', session, world, scene)
    assert addressed == "gate_guard"
    assert auth_id == "gate_guard"


def test_unsupported_title_does_not_steal_present_npc():
    session, world, scene = _pack(GATE_NPCS)
    for text in (
        'I turn to the Commander. "What happened here?"',
        "Lord Aldric, what happened here?",
    ):
        addressed, auth_id = _bind(text, session, world, scene)
        assert addressed is None, text
        assert auth_id in (None, ""), text


def test_sole_npc_unsupported_explicit_addressee_does_not_bind():
    session, world, scene = _pack([GATE_NPCS[0]], addressables=[])
    for text in (
        RECOVERED,
        "Captain, what happened here?",
        "Foreman, what happened here?",
        "Lord Aldric, what happened here?",
        'I turn to the Clerk. "What happened here?"',
    ):
        addressed, auth_id = _bind(text, session, world, scene)
        assert addressed is None, text
        assert auth_id in (None, ""), text


def test_sole_npc_undirected_question_still_binds():
    session, world, scene = _pack([GATE_NPCS[0]], addressables=[])
    addressed, _auth_id = _bind("What happened here?", session, world, scene)
    assert addressed == "gate_guard"
    addressed, _auth_id = _bind("Where did the missing patrol go?", session, world, scene)
    assert addressed == "gate_guard"


def test_sole_npc_supported_explicit_addressee_still_binds():
    session, world, scene = _pack([GATE_NPCS[0]], addressables=[])
    addressed, auth_id = _bind("Gate Guard, what happened here?", session, world, scene)
    assert addressed == "gate_guard"
    assert auth_id == "gate_guard"


def test_multiple_npc_compound_name_does_not_bind_shared_prefix():
    session, world, scene = _pack(
        [GATE_NPCS[0], GATE_NPCS[2]],
        addressables=[GATE_ADDRESSABLES[0], GATE_ADDRESSABLES[1]],
    )
    addressed, auth_id = _bind(
        'I turn to the Guard Captain. "What happened here?"', session, world, scene
    )
    assert addressed == "guard_captain"
    assert auth_id == "guard_captain"
    addressed, auth_id = _bind("Serjeant, what happened here?", session, world, scene)
    assert addressed is None
    assert auth_id in (None, "")


def test_kiln_porter_identities_generalize():
    scene = {
        "scene": {
            "id": "ember_kiln",
            "addressables": [
                {
                    "id": "night_porter",
                    "name": "Night Porter",
                    "scene_id": "ember_kiln",
                    "kind": "npc",
                    "addressable": True,
                    "aliases": ["porter"],
                    "address_roles": ["porter"],
                }
            ],
            "visible_facts": [],
            "hidden_facts": [],
            "discoverable_clues": [],
            "interactables": [],
            "exits": [],
        }
    }
    session = default_session()
    session["active_scene_id"] = "ember_kiln"
    session["interaction_context"] = {}
    world = {
        "npcs": [
            {
                "id": "night_porter",
                "name": "Night Porter",
                "location": "ember_kiln",
                "role": "porter",
                "aliases": ["porter"],
                "topics": [{"id": "kiln_spur_closed", "text": "The kiln spur is barred."}],
            }
        ]
    }
    rebuild_active_scene_entities(session, world, "ember_kiln", scene_envelope=scene)

    def kiln_bind(text: str) -> tuple[str | None, str | None]:
        addressed = find_addressed_npc_id_for_turn(text, session, world, scene)
        auth = resolve_authoritative_social_target(
            session,
            world,
            "ember_kiln",
            player_text=text,
            scene_envelope=scene,
            segmented_turn=segment_mixed_player_turn(text),
        )
        return addressed, auth.get("npc_id")

    assert kiln_bind("Night Porter, what happened here?") == ("night_porter", "night_porter")
    assert kiln_bind("Porter, what happened here?") == ("night_porter", "night_porter")
    assert kiln_bind('I turn to the Night Porter. "What happened here?"') == (
        "night_porter",
        "night_porter",
    )
    assert kiln_bind("Foreman, what happened here?") == (None, None)
    assert kiln_bind('I turn to the Clerk. "What happened here?"') == (None, None)
    assert kiln_bind("Lord Aldric, what happened here?") == (None, None)
    assert kiln_bind("What happened here?")[0] == "night_porter"


def test_wrong_npc_does_not_inherit_other_npc_topics():
    session, world, scene = _pack(GATE_NPCS)
    social = resolve_social_action(
        scene,
        session,
        world,
        {
            "type": "question",
            "label": RECOVERED,
            "prompt": RECOVERED,
            "target_id": "gate_serjeant",
        },
        raw_player_text=RECOVERED,
        character=default_character(),
    )
    inner = social.get("social") if isinstance(social, dict) else {}
    assert (inner or {}).get("npc_id") == "gate_serjeant"
    assert (inner or {}).get("topic_id") != "watch_command"
