"""Golden replay scenario seeds and chat-integration stubs (Cycle AC-1).

Test-only harness helpers for protected replay integration scenarios. Does not
own replay projection, expectations, or runtime behavior.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from game import storage
from game.defaults import default_scene, default_world
from tests.helpers.golden_replay_projection import project_turn_observation

_INVESTIGATOR_SCENE_ID = "scene_investigate"

_RUNNER_NPC: dict[str, Any] = {
    "id": "runner",
    "name": "Tavern Runner",
    "location": _INVESTIGATOR_SCENE_ID,
    "topics": [
        {
            "id": "lanes",
            "text": "They were seen near the east lanes.",
            "clue_id": "east_lanes",
        }
    ],
}

_GUARD_NPC: dict[str, Any] = {
    "id": "guard",
    "name": "Gate Guard",
    "location": _INVESTIGATOR_SCENE_ID,
    "topics": [
        {
            "id": "patrol",
            "text": "The guard saw fresh mud by the north arch.",
            "clue_id": "north_arch_mud",
        }
    ],
}


def gm_response(
    text: str,
    *,
    tags: Sequence[str] | None = None,
    debug_notes: str = "",
) -> dict[str, Any]:
    """Minimal fake ``call_gpt`` return dict for golden replay integration tests."""
    return {
        "player_facing_text": text,
        "tags": list(tags or []),
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": debug_notes,
    }


def suppress_intent_parsers(
    monkeypatch: Any,
    *,
    social: bool = True,
    exploration: bool = True,
    intent: bool = True,
) -> None:
    """Null out API intent parsers so replay scenarios drive routing deterministically."""
    if social:
        monkeypatch.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
    if exploration:
        monkeypatch.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
    if intent:
        monkeypatch.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)


def install_golden_chat_callable(monkeypatch: Any, callback: Callable[..., dict[str, Any]]) -> None:
    """Patch ``game.api.call_gpt`` with a custom callback."""
    monkeypatch.setattr("game.api.call_gpt", callback)


def install_golden_chat_stub(
    monkeypatch: Any,
    *,
    response_text: str,
    tags: Sequence[str] | None = None,
    debug_notes: str = "",
    suppress_social: bool = True,
    suppress_exploration: bool = True,
    suppress_intent: bool = True,
) -> None:
    """Patch ``call_gpt`` to return fixed text and optionally suppress intent parsers."""
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=lambda _messages: gm_response(
            response_text,
            tags=tags,
            debug_notes=debug_notes,
        ),
        suppress_social=suppress_social,
        suppress_exploration=suppress_exploration,
        suppress_intent=suppress_intent,
    )


def golden_replay_chat_stubs(
    monkeypatch: Any,
    *,
    gpt_callback: Callable[..., dict[str, Any]],
    suppress_social: bool = True,
    suppress_exploration: bool = True,
    suppress_intent: bool = True,
) -> None:
    """Canonical golden replay integration setup: deterministic GPT + intent suppression."""
    install_golden_chat_callable(monkeypatch, gpt_callback)
    suppress_intent_parsers(
        monkeypatch,
        social=suppress_social,
        exploration=suppress_exploration,
        intent=suppress_intent,
    )


def _save_investigator_scene(*, summary: str) -> None:
    scene = default_scene(_INVESTIGATOR_SCENE_ID)
    scene["scene"]["id"] = _INVESTIGATOR_SCENE_ID
    scene["scene"]["location"] = "Investigator's Office"
    scene["scene"]["summary"] = summary
    storage._save_json(storage.scene_path(_INVESTIGATOR_SCENE_ID), scene)


def _set_investigator_session() -> None:
    session = storage.load_session()
    session["active_scene_id"] = _INVESTIGATOR_SCENE_ID
    session["visited_scene_ids"] = [_INVESTIGATOR_SCENE_ID]
    storage.save_session(session)


def seed_investigator_runner_world() -> None:
    """Investigator office with a single runner NPC (directed question scenarios)."""
    _save_investigator_scene(summary="Rain taps the shutters while patrol notices curl on the desk.")
    world = default_world()
    world["npcs"] = [dict(_RUNNER_NPC)]
    storage._save_json(storage.WORLD_PATH, world)
    _set_investigator_session()


def seed_runner_guard_world() -> None:
    """Investigator office with runner and gate guard NPCs."""
    _save_investigator_scene(summary="A runner and a guard wait beside rain-spattered patrol maps.")
    world = default_world()
    world["npcs"] = [dict(_RUNNER_NPC), dict(_GUARD_NPC)]
    storage._save_json(storage.WORLD_PATH, world)
    _set_investigator_session()


def seed_runner_continuity_world() -> None:
    """Runner/guard world with engaged social continuity pinned to runner."""
    seed_runner_guard_world()
    session = storage.load_session()
    session_ctx = session.setdefault("interaction_context", {})
    session_ctx["active_interaction_target_id"] = "runner"
    session_ctx["active_interaction_kind"] = "social"
    session_ctx["interaction_mode"] = "social"
    session_ctx["engagement_level"] = "engaged"
    session.setdefault("scene_state", {})["current_interlocutor"] = "runner"
    storage.save_session(session)


def seed_tavern_patrol_lead_world() -> None:
    """Tavern + old milestone scenes with patrol-lead runner NPC."""
    tavern = default_scene("tavern")
    tavern["scene"]["id"] = "tavern"
    tavern["scene"]["location"] = "Rain Barrel Tavern"
    tavern["scene"]["summary"] = "A crowded tavern hums around a runner with news of the missing patrol."
    tavern["scene"]["exits"] = [{"label": "Path to the old milestone", "target_scene_id": "old_milestone"}]
    storage._save_json(storage.scene_path("tavern"), tavern)

    milestone = default_scene("old_milestone")
    milestone["scene"]["id"] = "old_milestone"
    milestone["scene"]["location"] = "Old Milestone"
    storage._save_json(storage.scene_path("old_milestone"), milestone)

    world = default_world()
    world["npcs"] = [
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "tavern",
            "topics": [
                {
                    "id": "patrol_milestone",
                    "text": "The patrol never came back from the old milestone.",
                    "clue_id": "c_patrol_milestone",
                    "leads_to_scene": "old_milestone",
                }
            ],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)

    session = storage.load_session()
    session["active_scene_id"] = "tavern"
    session["visited_scene_ids"] = ["tavern"]
    storage.save_session(session)


def seed_scene_object_investigation_world() -> None:
    """Investigator office with notice-board investigation interactables."""
    scene = default_scene(_INVESTIGATOR_SCENE_ID)
    scene["scene"]["id"] = _INVESTIGATOR_SCENE_ID
    scene["scene"]["location"] = "Investigator's Office"
    scene["scene"]["summary"] = "A rain-damp office holds patrol maps, a desk, and a public notice board."
    scene["scene"]["visible_facts"] = [
        "A notice board carries a posting about the missing patrol.",
        "An ink-stained desk is crowded with patrol maps.",
    ]
    scene["scene"]["interactables"] = [
        {
            "id": "notice_board",
            "label": "Notice board",
            "aliases": ["notice", "posting about the missing patrol"],
            "type": "investigate",
            "reveals_clue": "notice_patrol_details",
        }
    ]
    scene["scene"]["discoverable_clues"] = [
        {"id": "notice_patrol_details", "text": "The missing patrol was last seen below the east ridge."}
    ]
    storage._save_json(storage.scene_path(_INVESTIGATOR_SCENE_ID), scene)

    world = default_world()
    world["npcs"] = []
    storage._save_json(storage.WORLD_PATH, world)
    _set_investigator_session()


def seed_spine_three_branch_world() -> None:
    """Runner/guard investigator world extended for three-branch spine smoke."""
    seed_runner_guard_world()
    scene = storage.load_scene(_INVESTIGATOR_SCENE_ID)
    scene["scene"]["visible_facts"] = [
        "A runner waits by the desk with road gossip.",
        "A gate guard studies muddy patrol marks.",
        "A notice board carries a posting about the missing patrol.",
    ]
    scene["scene"]["interactables"] = [
        {
            "id": "notice_board",
            "label": "Notice board",
            "aliases": ["notice", "posting about the missing patrol"],
            "type": "investigate",
            "reveals_clue": "notice_patrol_details",
        }
    ]
    scene["scene"]["discoverable_clues"] = [
        {"id": "notice_patrol_details", "text": "The missing patrol was last seen below the east ridge."}
    ]
    storage._save_json(storage.scene_path(_INVESTIGATOR_SCENE_ID), scene)


def seed_frontier_gate_world() -> None:
    """Frontier Gate long-session bootstrap (25-turn social inquiry / intrusion branches)."""
    scene = default_scene("frontier_gate")
    scene["scene"]["id"] = "frontier_gate"
    scene["scene"]["location"] = "Cinderwatch Gate District"
    scene["scene"]["summary"] = (
        "Rain, choke traffic, a notice board, and gate watch pressure frame the missing patrol inquiry."
    )
    scene["scene"]["visible_facts"] = [
        "The notice board lists taxes, curfew rules, and a warning about a missing patrol.",
        "A gate serjeant manages the crowd and keeps one eye on the roster board.",
        "A tavern runner trades hot stew and rumors near the rain barrel.",
        "Threadbare watchers and refugees cluster along the muddy gate line.",
        "Ash Compact census delays have tightened the eastern caravan choke point.",
    ]
    scene["scene"]["interactables"] = [
        {
            "id": "notice_board",
            "label": "Notice board",
            "aliases": ["notice", "board", "curfew notice", "missing patrol warning"],
            "type": "investigate",
            "reveals_clue": "notice_patrol_route",
        }
    ]
    scene["scene"]["discoverable_clues"] = [
        {
            "id": "notice_patrol_route",
            "text": "The missing patrol was last seen taking the northwest mud track past the crates.",
        }
    ]
    storage._save_json(storage.scene_path("frontier_gate"), scene)

    world = default_world()
    world["npcs"] = [
        {
            "id": "gate_guard",
            "name": "Gate Guard",
            "location": "frontier_gate",
            "aliases": ["guard", "watch", "watch guard"],
            "topics": [
                {
                    "id": "watch_command",
                    "text": "Captain Thoran commands the gate watch tonight.",
                    "clue_id": "captain_thoran_watch",
                }
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
                    "clue_id": "patrol_route_change",
                }
            ],
        },
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "aliases": ["runner", "tavern runner"],
            "topics": [
                {
                    "id": "patrol_rumor",
                    "text": "The runner heard the patrol vanished near muddy footprints northwest of the crates.",
                    "clue_id": "muddy_footprints_northwest",
                }
            ],
        },
    ]
    storage._save_json(storage.WORLD_PATH, world)

    session = storage.load_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    storage.save_session(session)


def fem_payload(meta: Mapping[str, Any] | None = None, /, **fields: Any) -> dict[str, Any]:
    """Build a synthetic ``_final_emission_meta`` dict for projection tests."""
    if meta is None:
        return dict(fields)
    out = dict(meta)
    out.update(fields)
    return out


def minimal_gm_output_payload(*, fem_meta: Mapping[str, Any] | None = None, **gm_output: Any) -> dict[str, Any]:
    """Build a synthetic chat ``payload`` fragment containing ``gm_output``."""
    gm = dict(gm_output)
    if fem_meta is not None:
        gm["_final_emission_meta"] = dict(fem_meta)
    return {"gm_output": gm}


def minimal_turn_payload(
    *,
    scenario_id: str,
    gm_text: str = "",
    turn_index: int = 0,
    player_text: str = "",
    payload: Mapping[str, Any] | None = None,
    fem_meta: Mapping[str, Any] | None = None,
    resolution: Mapping[str, Any] | None = None,
    replay_identity: Mapping[str, Any] | None = None,
    **payload_fields: Any,
) -> dict[str, Any]:
    """Build a synthetic turn payload for ``project_turn_observation``."""
    snap: dict[str, Any] = {"turn_index": turn_index, "gm_text": gm_text}
    if player_text:
        snap["player_text"] = player_text

    if payload is not None:
        resolved_payload = dict(payload)
    else:
        resolved_payload = dict(payload_fields)
        if fem_meta is not None:
            gm_output = dict(resolved_payload.get("gm_output") or {})
            gm_output["_final_emission_meta"] = dict(fem_meta)
            resolved_payload["gm_output"] = gm_output

    if resolution is not None:
        resolved_payload["resolution"] = dict(resolution)

    turn_payload: dict[str, Any] = {
        "scenario_id": scenario_id,
        "snap": snap,
        "payload": resolved_payload,
    }
    if replay_identity is not None:
        turn_payload["replay_identity"] = dict(replay_identity)
    return turn_payload


def project_synthetic_turn(**kwargs: Any) -> dict[str, Any]:
    """Project a synthetic turn payload through the canonical replay adapter."""
    return project_turn_observation(minimal_turn_payload(**kwargs))


def _merge_direct_seam_extra_fields(observed: dict[str, Any], extra_fields: Mapping[str, Any]) -> None:
    """Merge direct-seam-only assertion fields onto a projected observation."""
    for key, value in extra_fields.items():
        if key == "trace" and isinstance(value, Mapping):
            trace = dict(observed.get("trace") or {})
            for trace_key, trace_value in value.items():
                if trace_key == "canonical_entry" and isinstance(trace_value, Mapping):
                    canonical_entry = dict(trace.get("canonical_entry") or {})
                    canonical_entry.update(trace_value)
                    trace["canonical_entry"] = canonical_entry
                else:
                    trace[trace_key] = trace_value
            observed["trace"] = trace
        else:
            observed[key] = value


def observed_turn_from_gate_output(
    *,
    scenario_id: str,
    gm_output: Mapping[str, Any],
    resolution: Mapping[str, Any] | None = None,
    turn_index: int = 0,
    player_text: str = "",
    extra_fields: Mapping[str, Any] | None = None,
    unavailable: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Project a final-emission gate ``gm_output`` dict into a golden observed turn.

    Uses :func:`project_turn_observation` for canonical FEM/fallback/trace projection.
    ``extra_fields`` merges direct-seam-only assertion keys (for example alias trace
    stamps or ``dialogue_plan_valid``) without rewriting runtime FEM on *gm_output*.
    """
    gm = dict(gm_output)
    payload: dict[str, Any] = {"gm_output": gm}
    if resolution is not None:
        payload["resolution"] = dict(resolution)
    snap = {
        "turn_index": turn_index,
        "gm_text": str(gm.get("player_facing_text") or ""),
        "player_text": player_text,
    }
    observed = project_turn_observation(
        {
            "scenario_id": scenario_id,
            "snap": snap,
            "payload": payload,
        }
    )
    if extra_fields:
        _merge_direct_seam_extra_fields(observed, extra_fields)
    if unavailable is not None:
        observed["unavailable"] = sorted({str(item) for item in unavailable if str(item).strip()})
    return observed
