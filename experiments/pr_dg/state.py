"""Copied session bundles and the authoritative state tuple."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from game.clues import get_all_known_clue_ids, get_known_clues_with_presentation
from game.clocks import advance_clock
from game.defaults import default_campaign, default_character, default_combat, default_conditions
from game.storage import build_effective_scene, list_scene_ids, load_scene
from game.world import advance_world_tick
from tests.test_combat_resolution import _scene_with_goblin
from tests.test_pr_db_speaker_grounding import (
    TURN_1,
    TURN_2,
    _bind_guard,
    _focus,
    _gate_session_scene,
    play_turn,
)


@dataclass
class Bundle:
    session: dict[str, Any]
    world: dict[str, Any]
    scene: dict[str, Any]
    combat: dict[str, Any]
    character: dict[str, Any]
    campaign: dict[str, Any]
    conditions: dict[str, Any]
    hidden_strings: list[str] = field(default_factory=list)
    dice: int | None = None
    lane: str = "social"

    def clone(self) -> "Bundle":
        return Bundle(
            session=deepcopy(self.session),
            world=deepcopy(self.world),
            scene=deepcopy(self.scene),
            combat=deepcopy(self.combat),
            character=deepcopy(self.character),
            campaign=deepcopy(self.campaign),
            conditions=deepcopy(self.conditions),
            hidden_strings=list(self.hidden_strings),
            dice=self.dice,
            lane=self.lane,
        )


def _effective(scene: dict) -> dict:
    if scene.get("_is_canon"):
        return build_effective_scene(scene, {})
    return scene


def _hidden_from_scene(scene: dict) -> list[str]:
    facts = (scene.get("scene") or {}).get("hidden_facts") or []
    return [item for item in facts if isinstance(item, str) and item.strip()]


def frontier_bundle(*, bind: bool = False) -> Bundle:
    session, scene, world = _gate_session_scene()
    scene = _effective(scene)
    if bind:
        _bind_guard(session)
        _focus(session, "guard_captain", "Guard Captain")
    return Bundle(
        session=session,
        world=world,
        scene=scene,
        combat=default_combat(),
        character=default_character(),
        campaign=default_campaign(),
        conditions=default_conditions(),
        hidden_strings=_hidden_from_scene(scene),
        lane="social",
    )


def exploration_bundle() -> Bundle:
    bundle = frontier_bundle()
    bundle.lane = "exploration"
    return bundle


def skill_bundle() -> Bundle:
    character = default_character()
    character.setdefault("skills", {})["perception"] = 2
    scene = {
        "scene": {
            "id": "x",
            "location": "X",
            "visible_facts": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
            "skill_check_defaults": {"investigate": {"skill_id": "perception", "dc": 8}},
        }
    }
    session = {"active_scene_id": "x", "turn_counter": 1, "scene_state": {"active_scene_id": "x"}}
    return Bundle(
        session=session,
        world={"npcs": []},
        scene=scene,
        combat=default_combat(),
        character=character,
        campaign=default_campaign(),
        conditions=default_conditions(),
        hidden_strings=[],
        lane="skill",
    )


def combat_bundle(*, extra_hidden: list[str] | None = None) -> Bundle:
    scene = {"scene": deepcopy(_scene_with_goblin()["scene"])}
    combat = {
        "in_combat": True,
        "round": 1,
        "initiative_order": [],
        "turn_index": 0,
        "active_actor_id": "galinor",
        "player_turn_used": False,
    }
    return Bundle(
        session={
            "active_scene_id": "frontier_gate",
            "turn_counter": 1,
            "scene_state": {"active_scene_id": "frontier_gate"},
        },
        world={"npcs": []},
        scene=scene,
        combat=combat,
        character=default_character(),
        campaign=default_campaign(),
        conditions=default_conditions(),
        hidden_strings=list(extra_hidden or []),
        dice=10,
        lane="combat",
    )


def followup_bundle() -> Bundle:
    """S1 completed the way PR-DE builds S2. The measured turn applies the tick."""
    bundle = frontier_bundle()
    play_turn(bundle.session, bundle.scene, bundle.world, TURN_1)
    bundle.session["turn_counter"] = int(bundle.session.get("turn_counter") or 0) + 1
    bundle.lane = "social"
    return bundle


def courier_bundle() -> Bundle:
    bundle = frontier_bundle()
    ids = list_scene_ids()
    destination = "market_quarter" if "market_quarter" in ids else next(
        (item for item in ids if item != "frontier_gate"), ""
    )
    bundle.world.setdefault("npcs", []).append(
        {
            "id": "df_mobile_courier",
            "name": "Courier",
            "location": "frontier_gate",
            "scene_id": "frontier_gate",
            "availability": "mobile",
            "agenda_move_to_scene_id": destination,
        }
    )
    bundle.session["_pr_dg_courier_destination"] = destination
    bundle.lane = "social"
    return bundle


def h1_hidden_strings() -> list[str]:
    return _hidden_from_scene(_effective(load_scene("frontier_gate")))


def apply_shared_tick(bundle: Bundle) -> dict[str, Any]:
    """One world tick and one time_pressure step, in chat's pre-classification order."""
    if bundle.session.get("_pr_dg_tick"):
        clocks = bundle.session.get("clocks") if isinstance(bundle.session.get("clocks"), dict) else {}
        return {
            "code": "already_applied",
            "time_pressure": clocks.get("time_pressure"),
            "event_types": list(bundle.session.get("_pr_dg_tick_events") or []),
        }
    tick = advance_world_tick(bundle.world, bundle.campaign)
    pressure = advance_clock(bundle.session, "time_pressure", 1)
    bundle.session["turn_counter"] = int(bundle.session.get("turn_counter") or 0) + 1
    event_types = [str(item.get("type") or "") for item in (tick.get("events") or []) if isinstance(item, dict)]
    bundle.session["_pr_dg_tick"] = True
    bundle.session["_pr_dg_tick_events"] = event_types
    return {"code": "ok", "time_pressure": pressure, "event_types": event_types}


def _enemy_hp(scene: dict) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for enemy in (scene.get("scene") or {}).get("enemies") or []:
        if isinstance(enemy, dict) and enemy.get("id"):
            hp = enemy.get("hp") if isinstance(enemy.get("hp"), dict) else {}
            out[str(enemy["id"])] = hp.get("current")
    return out


def _npc_locations(world: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for npc in world.get("npcs") or []:
        if isinstance(npc, dict) and npc.get("id"):
            out[str(npc["id"])] = str(npc.get("location") or npc.get("scene_id") or "")
    return out


def _ledger(session: dict) -> list[dict[str, str]]:
    ledger = session.get("bounded_improvisation") if isinstance(session.get("bounded_improvisation"), dict) else {}
    rows = []
    for entry in ledger.get("entries") or []:
        if isinstance(entry, dict):
            rows.append({"id": str(entry.get("id") or ""), "kind": str(entry.get("kind") or "")})
    return rows


def _interlocutor(session: dict) -> str | None:
    ctx = session.get("interaction_context") if isinstance(session.get("interaction_context"), dict) else {}
    focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
    slot = focus.get("interlocutor") if isinstance(focus.get("interlocutor"), dict) else {}
    scene_state = session.get("scene_state") if isinstance(session.get("scene_state"), dict) else {}
    value = ctx.get("active_interaction_target_id") or slot.get("id") or scene_state.get("current_interlocutor")
    text = str(value or "").strip()
    return text or None


def _flags(world: dict) -> dict[str, Any]:
    ws = world.get("world_state") if isinstance(world.get("world_state"), dict) else {}
    flags = ws.get("flags") if isinstance(ws.get("flags"), dict) else {}
    return {str(key): flags[key] for key in sorted(flags)}


def _entity_ids(scene: dict, world: dict) -> list[str]:
    found: set[str] = set()
    body = scene.get("scene") if isinstance(scene.get("scene"), dict) else {}
    for key in ("interactables", "objects", "addressables", "enemies"):
        for item in body.get(key) or []:
            if isinstance(item, dict) and item.get("id"):
                found.add(str(item["id"]))
    for npc in world.get("npcs") or []:
        if isinstance(npc, dict) and npc.get("id"):
            found.add(str(npc["id"]))
    return sorted(found)


def state_tuple(bundle: Bundle) -> dict[str, Any]:
    clocks = bundle.session.get("clocks") if isinstance(bundle.session.get("clocks"), dict) else {}
    clues = get_known_clues_with_presentation(bundle.session)
    scene_id = str((bundle.scene.get("scene") or {}).get("id") or bundle.session.get("active_scene_id") or "")
    return {
        "scene_id": scene_id,
        "known_clue_ids": sorted(get_all_known_clue_ids(bundle.session)),
        "known_clue_texts": sorted(str(item.get("text") or "") for item in clues if item.get("text")),
        "in_combat": bool(bundle.combat.get("in_combat")),
        "enemy_hp": _enemy_hp(bundle.scene),
        "time_pressure": clocks.get("time_pressure"),
        "tick_event_types": list(bundle.session.get("_pr_dg_tick_events") or []),
        "interlocutor_id": _interlocutor(bundle.session),
        "ledger": _ledger(bundle.session),
        "world_flags": _flags(bundle.world),
        "npc_locations": _npc_locations(bundle.world),
        "entity_ids": _entity_ids(bundle.scene, bundle.world),
        "turn_counter": bundle.session.get("turn_counter"),
        "provider_narration_requested": False,
        "visible_facts": list((bundle.scene.get("scene") or {}).get("visible_facts") or []),
    }


def state_hash(bundle: Bundle) -> str:
    payload = json.dumps(state_tuple(bundle), ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def tuple_diff(before: dict, after: dict) -> dict[str, dict[str, Any]]:
    diffs: dict[str, dict[str, Any]] = {}
    for key in sorted(set(before) | set(after)):
        if before.get(key) != after.get(key):
            diffs[key] = {"before": before.get(key), "after": after.get(key)}
    return diffs


def hidden_hits(value: Any, needles: list[str]) -> list[str]:
    try:
        blob = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        blob = str(value)
    return [item for item in needles if item and item in blob]
