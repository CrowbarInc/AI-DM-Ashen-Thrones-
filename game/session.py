"""Session module: playthrough state management and reset.

Does NOT touch world, campaign, scenes, locations, npcs, or clues.
"""
from __future__ import annotations

from typing import Any, Dict

from game.clocks import DEFAULT_CLOCKS
from game.interaction_context import clear_for_scene_change


def reset_session_state(session: Dict[str, Any]) -> Dict[str, Any]:
    """Clears runtime playthrough state but preserves campaign/world data.

    Mutates only runtime fields in the session dict. Does not touch world,
    world.scenes, world.locations, world.npcs, or world.clues.
    """
    # Clear scene runtime (discovered_clues, pending_leads, last_exploration_action_key, etc.)
    session["scene_runtime"] = {}

    # Reset to starting scene
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]

    # Reset counters and date
    session["turn_counter"] = 0
    session["current_date"] = "Day 1"

    # Reset clocks to defaults
    session["clocks"] = dict(DEFAULT_CLOCKS)

    # Clear clue knowledge state (discovered + inferred)
    session["clue_knowledge"] = {}

    # Clear NPC runtime (attitude, trust, fear, etc.)
    session["npc_runtime"] = {}
    clear_for_scene_change(session)

    # Clear debug and flags
    session["last_action_debug"] = None
    session["debug_traces"] = []
    session["flags"] = {}
    # Mark fresh campaign so build_messages does not inject prior chat logs
    session["chat_history"] = []

    # Preserve response_mode (user preference)
    session.setdefault("response_mode", "standard")

    print("[SESSION RESET] runtime state cleared")
    return session
