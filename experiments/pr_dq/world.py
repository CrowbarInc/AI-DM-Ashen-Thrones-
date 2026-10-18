"""In-memory courtyard and street. Nothing here is written to data/."""

from __future__ import annotations

import copy
from typing import Any

from game.defaults import default_character, default_world

LANTERN_TEXT = "A soot-streaked lantern burns beside the courtyard gate."
NOTICE_TEXT = "The board names the north road past the waystation."
MARA_ANSWER = "The street beyond the gate is the north road."
STREET_ARRIVAL = "The waystation street runs north from the courtyard gate. A notice board stands by the road."

COURTYARD_ID = "waystation_courtyard"
STREET_ID = "waystation_street"
LANTERN_ID = "courtyard_lantern"
GATE_ID = "courtyard_gate"
NOTICE_ID = "notice_board"
MARA_ID = "sergeant_mara"


def build_disposable_world() -> dict[str, Any]:
    world = copy.deepcopy(default_world())
    npcs = list(world.get("npcs") or [])
    npcs.append(
        {
            "id": MARA_ID,
            "name": "Sergeant Mara",
            "location": COURTYARD_ID,
            "role": "guard",
            "disposition": "neutral",
            "topics": [{"id": "street", "text": MARA_ANSWER, "clue_id": "north_road"}],
        }
    )
    world["npcs"] = npcs
    courtyard = {
        "scene": {
            "id": COURTYARD_ID,
            "location": "Waystation courtyard",
            "summary": "A walled courtyard. A lit lantern hangs beside the gate.",
            "visible_facts": [LANTERN_TEXT],
            "interactables": [
                {
                    "id": LANTERN_ID,
                    "label": "courtyard lantern",
                    "type": "examine",
                    "description": LANTERN_TEXT,
                }
            ],
            "exits": [
                {
                    "id": GATE_ID,
                    "label": "Courtyard gate",
                    "target_scene_id": STREET_ID,
                }
            ],
        }
    }
    street = {
        "scene": {
            "id": STREET_ID,
            "location": "Waystation street",
            "summary": STREET_ARRIVAL,
            "visible_facts": [STREET_ARRIVAL],
            "discoverable_clues": [{"id": "street_notice", "text": NOTICE_TEXT}],
            "interactables": [
                {
                    "id": NOTICE_ID,
                    "label": "notice board",
                    "type": "read",
                    "reveals_clue": "street_notice",
                }
            ],
            "exits": [],
        }
    }
    session = {
        "active_scene_id": COURTYARD_ID,
        "visited_scene_ids": [COURTYARD_ID],
        "turn_counter": 0,
        "clocks": {
            "suspicion": 0,
            "unrest": 0,
            "danger": 0,
            "occult_instability": 0,
            "time_pressure": 0,
        },
        "npc_runtime": {},
        "scene_runtime": {},
        "scene_state": {"active_scene_id": COURTYARD_ID},
        "flags": {},
        "inventory": [],
    }
    return {
        "session": session,
        "world": world,
        "scenes": {COURTYARD_ID: courtyard, STREET_ID: street},
        "character": copy.deepcopy(default_character()),
        "combat": {"in_combat": False, "player_turn_used": False, "round": 0},
    }
