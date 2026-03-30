"""Campaign layering and canonical fresh *runtime* state.

Layering (what persists across a "New Campaign" hard reset vs what is reapplied):

1. Static configuration — rules, condition definitions, scene graph on disk, importer
   output. Not wiped by resetting runtime; treat as shipped/editor content.

2. Intentional bootstrap seed — persisted defaults the author expects at campaign start:
   ``campaign.json`` (premise, tone, gm_guidance), ``world.json`` template fields
   (settlements, faction *definitions*, NPC *templates*), ``data/scenes/*.json``,
   ``character.json`` sheet. These survive a session reset by design; a future
   "restore bootstrap" would re-copy from packaged defaults, not from runtime.

3. Runtime session state — playthrough residue: ``session.json`` fields below,
   ``combat.json``, ``session_log.jsonl``, and any GM/world *mutations* that
   represent emergent play (e.g. ``world.event_log`` entries, ``world_state.flags``
   from ticks). Must reset to a clean graph on New Campaign; do not spread prior
   session dicts into the new state.

Journal/codex: ``build_player_journal`` seeds ``known_facts`` from
``scene.journal_seed_facts`` (or a capped prefix of ``visible_facts``), plus
runtime ``revealed_hidden_facts`` — not a wholesale copy of ``visible_facts``.
It still merges ``clue_knowledge`` / ``scene_runtime`` clues. ``world.event_log``
and ``world_state`` may mix intentional empty structure with emergent entries —
treat appended log lines and flags as runtime unless the author pre-seeded them
in shipped data.

Canonical factories below define layer (3) only. They construct new dict/list
graphs and must not alias nested structures from previous state.
"""
from __future__ import annotations

import secrets
from typing import Any, Dict

from game.clocks import DEFAULT_CLOCKS
from game.leads import SESSION_LEAD_REGISTRY_KEY

# Bootstrap-aligned opening location; matches seeded ``data/scenes/*.json`` and
# ``ensure_data_files_exist``. Not runtime residue — part of new-campaign seed.
DEFAULT_STARTING_SCENE_ID = "frontier_gate"


def _fresh_interaction_context() -> Dict[str, Any]:
    return {
        "active_interaction_target_id": None,
        "active_interaction_kind": None,
        "interaction_mode": "none",
        "engagement_level": "none",
        "conversation_privacy": None,
        "player_position_context": None,
    }


def _fresh_scene_state(scene_id: str) -> Dict[str, Any]:
    return {
        "active_scene_id": scene_id,
        "active_entities": [],
        "entity_presence": {},
        "current_interlocutor": None,
        "emergent_addressables": [],
        "promoted_actor_npc_map": {},
    }


def create_fresh_session_document() -> Dict[str, Any]:
    """Return a new session document for a new campaign (runtime layer only).

    No shared references with any previously loaded session; safe to
    ``session.clear(); session.update(...)``.

    Contamination-sensitive fields (interaction locks, ``scene_runtime`` momentum /
    topic pressure, clue memory, debug traces) must not survive New Campaign; see
    :mod:`game.fresh_campaign_verify` for dev checks that bootstrap seed is preserved
    while turn-scoped runtime residue is absent.
    """
    sid = DEFAULT_STARTING_SCENE_ID
    # New campaign run id: invalidates client-side assumptions and log correlation.
    run_id = secrets.token_hex(12)
    return {
        "active_scene_id": sid,
        "visited_scene_ids": [sid],
        "current_date": "Day 1",
        "turn_counter": 0,
        "response_mode": "standard",
        "clocks": dict(DEFAULT_CLOCKS),
        "interaction_context": _fresh_interaction_context(),
        "scene_state": _fresh_scene_state(sid),
        "scene_runtime": {},
        "clue_knowledge": {},
        SESSION_LEAD_REGISTRY_KEY: {},
        "npc_runtime": {},
        "last_action_debug": None,
        "debug_traces": [],
        "flags": {},
        "chat_history": [],
        # Cleared so compose_state can sync from character.json (bootstrap sheet).
        "character_name": None,
        "campaign_run_id": run_id,
        "session_id": run_id,
    }


def create_fresh_combat_state() -> Dict[str, Any]:
    """Return idle combat state (no encounter, no initiative)."""
    return {
        "in_combat": False,
        "round": 0,
        "initiative_order": [],
        "turn_index": 0,
        "active_actor_id": None,
        "player_turn_used": False,
    }


def create_fresh_campaign_state() -> Dict[str, Any]:
    """Full runtime bundle for a new campaign: session + combat.

    Does not include campaign/world/character/scenes — those are bootstrap or static.
    """
    return {
        "session": create_fresh_session_document(),
        "combat": create_fresh_combat_state(),
    }


# Alias for readers grepping the design doc / camelCase name.
createFreshCampaignState = create_fresh_campaign_state
