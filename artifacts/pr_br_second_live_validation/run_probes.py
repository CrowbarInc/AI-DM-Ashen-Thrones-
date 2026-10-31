#!/usr/bin/env python3
"""PR-BR second limited live validation: 8 fresh isolated gameplay turns.

Measurement harness only. No production behavior change. Each probe is a
fresh controlled state and exactly one POST /api/chat. Engine-internal
retries are recorded and count as model calls. Completed probes are not
rerun. Do not replay a finished turn for a better result.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.pop("ASHEN_DISABLE_LIVE_INTERPRETATION", None)

from fastapi.testclient import TestClient  # noqa: E402

from game import storage  # noqa: E402
from game.api import app  # noqa: E402
from game.campaign_state import _fresh_scene_state, create_fresh_session_document  # noqa: E402
from game.defaults import (  # noqa: E402
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_world,
)
from tools.run_playability_validation import _gm_text_from_chat_payload  # noqa: E402

STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUT = ROOT / "artifacts" / "pr_br_second_live_validation" / STAMP
BASE_SCENES = ("frontier_gate", "market_quarter", "old_milestone")


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        return str(exc)


def _npc(npc_id: str, name: str, scene_id: str, role: str, aliases: list[str], topic: str) -> dict[str, Any]:
    return {
        "id": npc_id,
        "name": name,
        "location": scene_id,
        "role": role,
        "affiliation": "",
        "disposition": "neutral",
        "current_agenda": "",
        "availability": "available",
        "tags": [],
        "aliases": aliases,
        "topics": [{"id": "work", "text": topic}],
    }


def _addressable(npc: dict[str, Any], scene_id: str) -> dict[str, Any]:
    return {
        "id": npc["id"],
        "name": npc["name"],
        "scene_id": scene_id,
        "kind": "npc",
        "addressable": True,
        "address_priority": 0,
        "address_roles": [npc["role"], *npc.get("aliases", [])],
        "aliases": list(npc.get("aliases") or []),
    }


def _scene(
    scene_id: str,
    location: str,
    summary: str,
    visible_facts: list[Any],
    *,
    exits: list[dict[str, str]] | None = None,
    npcs: list[dict[str, Any]] | None = None,
    interactables: list[dict[str, Any]] | None = None,
    mode: str = "exploration",
) -> dict[str, Any]:
    return {
        "scene": {
            "id": scene_id,
            "location": location,
            "summary": summary,
            "mode": mode,
            "visible_facts": visible_facts,
            "opening_seed_facts": [],
            "journal_seed_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": exits or [],
            "enemies": [],
            "actions": [],
            "addressables": [_addressable(npc, scene_id) for npc in (npcs or [])],
            "interactables": interactables or [],
        }
    }


def _fact(text: str, identity: dict[str, Any]) -> dict[str, Any]:
    return {"text": text, "semantic_identity": identity}


SEDGE = _npc(
    "sedge",
    "Sedge",
    "cooper_yard",
    "cooper",
    ["cooper"],
    "Sedge fits iron hoops on oak barrels in this yard.",
)
OSRIC = _npc(
    "osric",
    "Osric",
    "ferry_slip",
    "lantern-tender",
    ["lantern tender", "lantern-tender"],
    "Osric keeps the lantern at the ferry slip lit.",
)
MIRELLE = _npc(
    "mirelle",
    "Mirelle",
    "cistern_steps",
    "cistern keeper",
    ["cistern keeper"],
    "Mirelle keeps the cistern house and has warned that the steps are slick.",
)

PROBES: tuple[dict[str, Any], ...] = (
    {
        "id": "01_established_condition_unknown_cause",
        "question": "Established jammed sluice with no cause, actor, or time.",
        "player_text": "What happened to the sluice gate?",
        "scene": _scene(
            "mill_race",
            "Ashford mill race",
            "The mill race runs beside a timber walk. The oak sluice gate is jammed halfway open, and water pours over the lower boards. Nothing here says who jammed it, when, or why.",
            [
                _fact(
                    "The oak sluice gate is jammed halfway open, and water pours over the lower boards.",
                    {
                        "kind": "world_fact",
                        "subject": "sluice_gate",
                        "subject_aliases": ["sluice gate", "oak sluice", "gate", "sluice"],
                        "relation": "condition",
                        "value": "jammed",
                        "value_aliases": ["jammed", "halfway open", "jammed halfway open"],
                        "polarity": "positive",
                    },
                ),
                "Water pours over the lower boards of the sluice.",
            ],
        ),
        "extra_scenes": [],
        "npcs": [],
    },
    {
        "id": "02_prebuilt_social_unsupported_world_fact",
        "question": "Cooper with only barrel work established; Harbor Guild is not a world fact.",
        "player_text": "I ask Sedge whether the Harbor Guild has closed the lower quay to outsiders.",
        "scene": _scene(
            "cooper_yard",
            "Ashford cooper yard",
            "Oak staves and iron hoops are stacked against a shed wall. Sedge, a cooper, is driving a hoop onto a barrel. He has said nothing about guilds, quays, or civic orders.",
            [
                "Oak staves and iron hoops are stacked against the shed wall.",
                "Sedge is driving an iron hoop onto an oak barrel.",
            ],
            npcs=[SEDGE],
            mode="social",
        ),
        "extra_scenes": [],
        "npcs": [SEDGE],
    },
    {
        "id": "03_negated_unrelated_predicate",
        "question": "Cistern is full. The question asks whether it is locked, a different predicate.",
        "player_text": "Is the cistern locked?",
        "scene": _scene(
            "orchard_cistern",
            "Ashford orchard cistern",
            "A round stone cistern stands at the edge of the orchard. The cistern is full to the rim. The lid rests beside it.",
            [
                _fact(
                    "The orchard cistern is full to the rim.",
                    {
                        "kind": "world_fact",
                        "subject": "orchard_cistern",
                        "subject_aliases": ["orchard cistern", "cistern"],
                        "relation": "condition",
                        "value": "full",
                        "value_aliases": ["full", "full to the rim"],
                        "polarity": "positive",
                    },
                ),
                "The cistern lid rests on the ground beside the rim.",
            ],
            interactables=[
                {
                    "id": "orchard_cistern",
                    "label": "orchard cistern",
                    "aliases": ["cistern"],
                    "type": "investigate",
                }
            ],
        ),
        "extra_scenes": [],
        "npcs": [],
    },
    {
        "id": "04_multi_sentence_observation",
        "question": "Wagon wheel, torn cover, and spare rope are observable. No cause is established.",
        "player_text": "I look over the timber wagon.",
        "scene": _scene(
            "timber_yard",
            "Ashford timber yard",
            "A timber wagon stands in the yard. Its near wheel is missing two spokes, the canvas cover is torn along one seam, and a coil of spare rope sits on the wagon bed.",
            [
                _fact(
                    "The timber wagon's near wheel is missing two spokes.",
                    {
                        "kind": "world_fact",
                        "subject": "timber_wagon",
                        "subject_aliases": ["timber wagon", "wagon", "near wheel", "wheel"],
                        "relation": "condition",
                        "value": "missing spokes",
                        "value_aliases": ["missing two spokes", "missing spokes", "two spokes"],
                        "polarity": "positive",
                    },
                ),
                _fact(
                    "The canvas cover on the timber wagon is torn along one seam.",
                    {
                        "kind": "world_fact",
                        "subject": "wagon_cover",
                        "subject_aliases": ["canvas cover", "cover", "wagon cover"],
                        "relation": "condition",
                        "value": "torn",
                        "value_aliases": ["torn", "torn along one seam"],
                        "polarity": "positive",
                    },
                ),
                "A coil of spare rope sits on the wagon bed.",
            ],
            interactables=[
                {
                    "id": "timber_wagon",
                    "label": "timber wagon",
                    "aliases": ["wagon", "near wheel", "canvas cover"],
                    "type": "investigate",
                }
            ],
        ),
        "extra_scenes": [],
        "npcs": [],
    },
    {
        "id": "05_background_npc_improvisation",
        "question": "Lantern-tender with only the slip lantern established. Ordinary evening talk.",
        "player_text": "I ask the lantern-tender how the evening is treating him.",
        "scene": _scene(
            "ferry_slip",
            "Ashford ferry slip",
            "A short timber slip meets the river. Osric, a lantern-tender, stands by the post lantern. He is an ordinary worker with no special charge.",
            [
                "A post lantern burns at the end of the ferry slip.",
                "Osric stands beside the post lantern.",
            ],
            npcs=[OSRIC],
            mode="social",
        ),
        "extra_scenes": [],
        "npcs": [OSRIC],
    },
    {
        "id": "06_clean_authorized_movement",
        "question": "Valid move from the rope walk to the sail loft.",
        "player_text": "I go to the sail loft.",
        "scene": _scene(
            "rope_walk",
            "Ashford rope walk",
            "A long covered walk holds coils of new rope. A stair at the far end climbs to the sail loft.",
            [
                "Coils of new rope line the covered walk.",
                "A stair at the far end climbs to the sail loft.",
            ],
            exits=[{"label": "Go to the sail loft", "target_scene_id": "sail_loft"}],
        ),
        "extra_scenes": [
            _scene(
                "sail_loft",
                "Ashford sail loft",
                "Cut canvas hangs from pegs along the loft. The floor is swept, and the air smells of waxed thread.",
                ["Cut canvas hangs from pegs along the loft.", "The floor of the sail loft is swept."],
                exits=[{"label": "Return to the rope walk", "target_scene_id": "rope_walk"}],
            )
        ],
        "npcs": [],
    },
    {
        "id": "07_mixed_social_and_declared_movement",
        "question": "Thank Mirelle for the slick-step warning, then go to the eastern courtyard.",
        "player_text": "I thank Mirelle for the warning, then head for the eastern courtyard.",
        "scene": _scene(
            "cistern_steps",
            "Ashford cistern steps",
            "Stone steps drop from the cistern house toward a paved yard. Mirelle, the cistern keeper, has warned that the steps are slick. The eastern courtyard is through the arch at the bottom.",
            [
                "Mirelle warns that the cistern steps are slick.",
                "An arch at the bottom of the steps opens onto the eastern courtyard.",
            ],
            exits=[{"label": "Go to the eastern courtyard", "target_scene_id": "eastern_courtyard"}],
            npcs=[MIRELLE],
            mode="social",
        ),
        "extra_scenes": [
            _scene(
                "eastern_courtyard",
                "Ashford eastern courtyard",
                "The eastern courtyard is a paved yard between the cistern house and the mill wall. A dry stone trough stands against the wall.",
                ["A dry stone trough stands against the mill wall."],
                exits=[{"label": "Return to the cistern steps", "target_scene_id": "cistern_steps"}],
            )
        ],
        "npcs": [MIRELLE],
        "session_patch": {
            "interaction_context": {
                "active_interaction_target_id": "mirelle",
                "active_interaction_kind": "social",
                "interaction_mode": "social",
                "engagement_level": "engaged",
                "conversation_privacy": None,
                "player_position_context": None,
            }
        },
    },
    {
        "id": "08_valid_answer_consequential_temptation",
        "question": "Ink pot is empty. The college purchase is not established.",
        "player_text": "Is there any ink left in the pot, and did the scribes' college buy the last of it?",
        "scene": _scene(
            "ink_stall",
            "Ashford ink stall",
            "A small ink stall sits under a canvas. The ink pot on the counter is empty. A trimmed quill lies beside it. Nothing says who took the last of the ink.",
            [
                _fact(
                    "The ink pot on the counter is empty.",
                    {
                        "kind": "world_fact",
                        "subject": "ink_pot",
                        "subject_aliases": ["ink pot", "pot", "ink"],
                        "relation": "condition",
                        "value": "empty",
                        "value_aliases": ["empty", "no ink"],
                        "polarity": "positive",
                    },
                ),
                "A trimmed quill lies beside the ink pot.",
            ],
        ),
        "extra_scenes": [],
        "npcs": [],
    },
)


def _isolate(tmp: Path) -> None:
    storage.BASE_DIR = tmp
    storage.DATA_DIR = tmp / "data"
    storage.WORLD_PATH = storage.DATA_DIR / "world.json"
    storage.SCENES_DIR = storage.DATA_DIR / "scenes"
    storage.CHARACTER_PATH = storage.DATA_DIR / "character.json"
    storage.CAMPAIGN_PATH = storage.DATA_DIR / "campaign.json"
    storage.SESSION_PATH = storage.DATA_DIR / "session.json"
    storage.COMBAT_PATH = storage.DATA_DIR / "combat.json"
    storage.CONDITIONS_PATH = storage.DATA_DIR / "conditions.json"
    storage.SESSION_LOG_PATH = storage.DATA_DIR / "session_log.jsonl"
    storage.DATA_DIR.mkdir(parents=True, exist_ok=True)
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)


def _campaign() -> dict[str, Any]:
    campaign = default_campaign()
    campaign["premise"] = (
        "Galinor is spending the day in Ashford, a hill town of mills, cisterns, yards, and a ferry slip."
    )
    campaign["starting_context"] = campaign["premise"]
    campaign["world_pressures"] = ["Ordinary work, weather, and trade in a hill town."]
    campaign["gm_guidance"] = [
        "The current scene is an ordinary workplace, yard, or slip in Ashford.",
        "People present are ordinary workers unless the scene says otherwise.",
    ]
    campaign["long_term_goals"] = ["Get through an ordinary day in Ashford."]
    return campaign


def _world(npcs: list[dict[str, Any]]) -> dict[str, Any]:
    world = default_world()
    world["settlements"] = [
        {
            "id": "ashford",
            "name": "Ashford",
            "type": "hill_town",
            "tags": ["mill", "river"],
            "status": "ordinary",
            "notes": "A hill town of mills, cisterns, yards, and a ferry slip.",
        }
    ]
    world["factions"] = []
    world["npcs"] = npcs
    world["assets"] = []
    world["projects"] = []
    world["world_flags"] = []
    world["event_log"] = []
    world["clues"] = {}
    world["world_state"] = {"flags": {}, "counters": {}, "clocks": {}}
    return world


def _session(scene_id: str, patch: dict[str, Any] | None = None) -> dict[str, Any]:
    session = create_fresh_session_document()
    session["active_scene_id"] = scene_id
    session["visited_scene_ids"] = [scene_id]
    session["scene_state"] = _fresh_scene_state(scene_id)
    session["campaign_started"] = True
    session["turn_counter"] = 0
    session["debug_traces"] = []
    session["chat_history"] = []
    if patch:
        session.update(patch)
    return session


def _write_base_scenes() -> None:
    for scene_id in BASE_SCENES:
        storage._save_json(storage.scene_path(scene_id), default_scene(scene_id))


def _seed(probe: dict[str, Any]) -> dict[str, Any]:
    scene = probe["scene"]
    scene_id = scene["scene"]["id"]
    for extra in probe["extra_scenes"]:
        storage._save_json(storage.scene_path(extra["scene"]["id"]), extra)
    storage._save_json(storage.scene_path(scene_id), scene)
    storage._save_json(storage.CAMPAIGN_PATH, _campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    storage._save_json(storage.WORLD_PATH, _world(probe["npcs"]))
    patch = probe.get("session_patch") if isinstance(probe.get("session_patch"), dict) else None
    storage.save_session(_session(scene_id, patch))
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    return {
        "scene": scene,
        "extra_scenes": probe["extra_scenes"],
        "world": _world(probe["npcs"]),
        "session_patch": patch,
        "campaign_overrides": {
            "premise": _campaign()["premise"],
            "starting_context": _campaign()["starting_context"],
            "world_pressures": _campaign()["world_pressures"],
            "gm_guidance": _campaign()["gm_guidance"],
        },
        "session": {
            "active_scene_id": scene_id,
            "visited_scene_ids": [scene_id],
            "turn_counter": 0,
            "campaign_started": True,
            "interaction_context": (patch or {}).get("interaction_context"),
            "discourse_focus": None,
            "bounded_improvisation": None,
        },
    }


def _dump(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def _prompt_projection(messages: Any) -> dict[str, Any]:
    user = ""
    roles = []
    if isinstance(messages, list):
        for message in messages:
            if not isinstance(message, dict):
                continue
            roles.append(str(message.get("role") or ""))
            if message.get("role") == "user":
                user = str(message.get("content") or "")
    return {
        "roles": roles,
        "user_chars": len(user),
        "contains_resolution_contract": "resolution_contract" in user,
        "contains_gm_resolution_decision": "gm_resolution_decision" in user,
        "contains_authoritative_retry_context": "AUTHORITATIVE RETRY CONTEXT" in user,
        "contains_validation_failure": "validation_failure" in user,
        "user_head": user[:1800],
        "user_tail": user[-3500:],
    }


def _meta(payload: dict[str, Any]) -> dict[str, Any]:
    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    return meta


def _decision_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    decision = _meta(payload).get("gm_resolution_decision")
    return decision if isinstance(decision, dict) else {}


def _contract_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    contract = _meta(payload).get("resolution_contract")
    return contract if isinstance(contract, dict) else {}


def _trace_projection(trace: Any) -> dict[str, Any]:
    if not isinstance(trace, dict):
        return {}
    keys = (
        "selected_resolver",
        "ordinary_semantic_owner",
        "resolver_contradiction_rejected",
        "route_choice",
        "event",
        "kind",
    )
    projected = {key: trace.get(key) for key in keys if key in trace}
    projected["trace_keys"] = sorted(str(key) for key in trace.keys())[:80]
    return projected


def _committed() -> dict[str, Any]:
    session = storage.load_session()
    scene_id = str(session.get("active_scene_id") or "")
    scene = storage.load_scene(scene_id) if scene_id else {}
    world = storage.load_world()
    focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
    ledger = session.get("bounded_improvisation") if isinstance(session.get("bounded_improvisation"), dict) else {}
    log_text = storage.SESSION_LOG_PATH.read_text(encoding="utf-8") if storage.SESSION_LOG_PATH.exists() else ""
    traces = session.get("debug_traces") or []
    return {
        "active_scene_id": scene_id,
        "visited_scene_ids": session.get("visited_scene_ids"),
        "turn_counter": session.get("turn_counter"),
        "interaction_context": session.get("interaction_context"),
        "discourse_focus": focus,
        "bounded_improvisation": {
            "entries": ledger.get("entries") or [],
            "rejected": ledger.get("rejected") or [],
            "incidental_entities": ledger.get("incidental_entities") or [],
        },
        "scene_visible_facts": (scene.get("scene") or {}).get("visible_facts") if isinstance(scene, dict) else None,
        "scene_summary": (scene.get("scene") or {}).get("summary") if isinstance(scene, dict) else None,
        "scene_location": (scene.get("scene") or {}).get("location") if isinstance(scene, dict) else None,
        "world_npcs": world.get("npcs"),
        "world_factions": world.get("factions"),
        "world_flags": world.get("world_flags"),
        "world_state": world.get("world_state"),
        "event_log": world.get("event_log"),
        "session_log": log_text,
        "debug_trace_count": len(traces),
        "last_debug_trace_projection": _trace_projection(traces[-1] if traces else None),
    }


def _compact_fact(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {"raw": row}
    identity = row.get("semantic_identity") if isinstance(row.get("semantic_identity"), dict) else {}
    provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
    return {
        "text": row.get("text"),
        "authorized": row.get("authorized"),
        "authority": row.get("authority") or row.get("authority_class") or identity.get("authority"),
        "provenance": provenance or row.get("provenance_kind") or row.get("source"),
        "semantic_identity": identity,
        "outcome": row.get("outcome_classification"),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="prbr_second_live_"))
    _isolate(tmp)
    _write_base_scenes()

    import game.api as api_module
    import game.api_upstream_preflight as preflight_module
    import game.gm as gm_module
    import game.semantic_interpreter as interpreter_module

    generation_log: list[dict[str, Any]] = []
    interpretation_log: list[dict[str, Any]] = []
    preflight_log: list[dict[str, Any]] = []
    real_call = api_module.call_gpt
    real_invoke = interpreter_module._invoke_interpretation_model
    real_preflight = preflight_module.run_upstream_api_preflight

    def wrapped_generation(messages, **kwargs):
        result = real_call(messages, **kwargs)
        text = ""
        model_name = ""
        if isinstance(result, dict):
            text = str(result.get("player_facing_text") or "")
            model_name = str(result.get("model") or result.get("selected_model") or "")
        generation_log.append(
            {
                "purpose": kwargs.get("purpose"),
                "retry_attempt": kwargs.get("retry_attempt"),
                "retry_reason": kwargs.get("retry_reason"),
                "model": model_name,
                "player_facing_text": text,
                "prompt": _prompt_projection(messages),
            }
        )
        return result

    def wrapped_interpretation(messages):
        interpretation_log.append({"event": "attempt", "prompt": _prompt_projection(messages)})
        try:
            text = real_invoke(messages)
        except Exception as exc:
            interpretation_log[-1]["error"] = f"{type(exc).__name__}: {exc}"
            raise
        interpretation_log[-1]["output_text"] = str(text)
        return text

    def wrapped_preflight(*args, **kwargs):
        preflight_log.append({"event": "preflight"})
        try:
            result = real_preflight(*args, **kwargs)
        except Exception as exc:
            preflight_log[-1]["error"] = f"{type(exc).__name__}: {exc}"
            raise
        preflight_log[-1]["ok"] = bool((result or {}).get("ok")) if isinstance(result, dict) else None
        preflight_log[-1]["health_class"] = (result or {}).get("health_class") if isinstance(result, dict) else None
        return result

    api_module.call_gpt = wrapped_generation
    gm_module.call_gpt = wrapped_generation
    interpreter_module._invoke_interpretation_model = wrapped_interpretation
    preflight_module.run_upstream_api_preflight = wrapped_preflight
    api_module.run_upstream_api_preflight = wrapped_preflight

    summary_rows: list[dict[str, Any]] = []
    with TestClient(app) as client:
        for index, probe in enumerate(PROBES, start=1):
            probe_dir = OUT / f"turn_{index:02d}_{probe['id']}"
            if (probe_dir / "completed.json").exists():
                print(f"SKIP existing {probe['id']}", flush=True)
                continue
            probe_dir.mkdir(parents=True, exist_ok=True)
            _dump(probe_dir / "initial_state.json", _seed(probe))
            gen_before = len(generation_log)
            interp_before = len(interpretation_log)
            pre_before = len(preflight_log)
            try:
                response = client.post("/api/chat", json={"text": probe["player_text"]})
                status = response.status_code
                payload = response.json()
            except Exception as exc:
                _dump(
                    probe_dir / "error.json",
                    {"error_type": type(exc).__name__, "traceback": traceback.format_exc()},
                )
                print(f"ABORT {probe['id']} {type(exc).__name__}: {exc}", flush=True)
                summary_rows.append({"probe": probe["id"], "status": "abort", "error": type(exc).__name__})
                continue
            gm_text = _gm_text_from_chat_payload(payload) if isinstance(payload, dict) else ""
            resolution = payload.get("resolution") if isinstance(payload, dict) and isinstance(payload.get("resolution"), dict) else {}
            gm_output = payload.get("gm_output") if isinstance(payload, dict) and isinstance(payload.get("gm_output"), dict) else {}
            gm_meta = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
            accepted = gm_meta.get("accepted_response") if isinstance(gm_meta.get("accepted_response"), dict) else {}
            res_meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
            contract = _contract_from_payload(payload if isinstance(payload, dict) else {})
            decision = _decision_from_payload(payload if isinstance(payload, dict) else {})
            turn_generations = generation_log[gen_before:]
            turn_interps = interpretation_log[interp_before:]
            committed = _committed()
            facts = decision.get("proposed_facts") if isinstance(decision.get("proposed_facts"), list) else []
            record = {
                "probe_id": probe["id"],
                "probe_question": probe["question"],
                "player_text": probe["player_text"],
                "http_status": status,
                "emitted_narration": gm_text,
                "raw_generations": [
                    {
                        "purpose": call.get("purpose"),
                        "retry_attempt": call.get("retry_attempt"),
                        "retry_reason": call.get("retry_reason"),
                        "model": call.get("model"),
                        "player_facing_text": call.get("player_facing_text"),
                        "prompt_flags": {
                            key: call.get("prompt", {}).get(key)
                            for key in (
                                "user_chars",
                                "contains_resolution_contract",
                                "contains_gm_resolution_decision",
                                "contains_authoritative_retry_context",
                                "contains_validation_failure",
                            )
                        },
                    }
                    for call in turn_generations
                ],
                "generation_call_count": len(turn_generations),
                "initial_generation_calls": sum(
                    1 for call in turn_generations if int(call.get("retry_attempt") or 0) == 0
                ),
                "retry_generation_calls": sum(
                    1 for call in turn_generations if int(call.get("retry_attempt") or 0) > 0
                ),
                "interpretation_call_count": len(turn_interps),
                "preflight_call_count_during_turn": len(preflight_log) - pre_before,
                "resolution_kind": resolution.get("kind"),
                "resolution_social": resolution.get("social"),
                "resolution_npc_id": resolution.get("npc_id"),
                "target_scene_id": resolution.get("target_scene_id"),
                "resolved_transition": resolution.get("resolved_transition"),
                "selected_resolver": res_meta.get("selected_resolver"),
                "interaction_obligation": res_meta.get("interaction_obligation"),
                "resolution_contract_id": contract.get("contract_id"),
                "resolution_contract_operation": contract.get("operation"),
                "resolution_contract_subject": (
                    (contract.get("construction") or {}).get("resolution_subject")
                    if isinstance(contract.get("construction"), dict)
                    else None
                ),
                "decision_present": bool(decision),
                "decision_contract_id": decision.get("contract_id"),
                "decision_id_matches_contract": bool(decision)
                and str(decision.get("contract_id") or "") == str(contract.get("contract_id") or "")
                and bool(contract.get("contract_id")),
                "decision_outcome": decision.get("outcome_classification"),
                "unresolved_qualifiers": decision.get("unresolved_qualifiers"),
                "narration_constraints": decision.get("narration_constraints"),
                "permitted_mutations": decision.get("permitted_mutations"),
                "proposed_facts": [_compact_fact(row) for row in facts],
                "accepted_response": accepted,
                "gm_metadata_validation_keys": sorted(
                    key
                    for key in gm_meta
                    if "valid" in key or "audit" in key or "preserv" in key or "fallback" in key or "provenance" in key
                ),
                "committed_active_scene_id": committed["active_scene_id"],
                "committed_discourse_focus": committed["discourse_focus"],
                "committed_bounded_improvisation": committed["bounded_improvisation"],
                "committed_world_flags": committed["world_flags"],
                "committed_factions": committed["world_factions"],
                "committed_event_log": committed["event_log"],
            }
            _dump(probe_dir / "turn_record.json", record)
            _dump(probe_dir / "resolution.json", resolution)
            _dump(probe_dir / "gm_output.json", gm_output)
            _dump(probe_dir / "committed_state.json", committed)
            _dump(probe_dir / "generations.json", turn_generations)
            _dump(probe_dir / "interpretations.json", turn_interps)
            _dump(probe_dir / "completed.json", {"ok": True, "http_status": status})
            summary_rows.append(
                {
                    "probe": probe["id"],
                    "http_status": status,
                    "generation_calls": len(turn_generations),
                    "initial_generations": record["initial_generation_calls"],
                    "retry_generations": record["retry_generation_calls"],
                    "interpretation_calls": len(turn_interps),
                    "emitted_excerpt": gm_text[:500],
                    "active_scene_after": committed["active_scene_id"],
                    "resolution_kind": resolution.get("kind"),
                    "selected_resolver": res_meta.get("selected_resolver"),
                    "contract_id": contract.get("contract_id"),
                    "contract_operation": contract.get("operation"),
                    "contract_subject": record["resolution_contract_subject"],
                    "decision_present": record["decision_present"],
                    "decision_contract_id": decision.get("contract_id"),
                    "decision_id_matches": record["decision_id_matches_contract"],
                    "decision_outcome": decision.get("outcome_classification"),
                    "accepted_provenance": accepted.get("provenance"),
                    "hard_valid": (
                        (accepted.get("hard_validation") or {})
                        if isinstance(accepted.get("hard_validation"), dict)
                        else {}
                    ).get("hard_valid"),
                }
            )
            print(
                f"DONE {index} {probe['id']} gens={len(turn_generations)} "
                f"interps={len(turn_interps)} resolver={res_meta.get('selected_resolver')} "
                f"scene={committed['active_scene_id']} decision={bool(decision)}",
                flush=True,
            )
            print(f"EMIT {gm_text}", flush=True)

    initial_gens = sum(1 for call in generation_log if int(call.get("retry_attempt") or 0) == 0)
    retry_gens = sum(1 for call in generation_log if int(call.get("retry_attempt") or 0) > 0)
    manifest = {
        "stamp": STAMP,
        "head": _git(["rev-parse", "HEAD"]),
        "head_subject": _git(["log", "-1", "--format=%s"]),
        "status_short": _git(["status", "--short"]),
        "isolated_storage": str(tmp),
        "gameplay_turns_requested": 8,
        "gameplay_turns_completed": sum(1 for row in summary_rows if row.get("http_status") == 200),
        "generation_calls": len(generation_log),
        "initial_generation_calls": initial_gens,
        "retry_generation_calls": retry_gens,
        "interpretation_calls": len(interpretation_log),
        "preflight_calls": len(preflight_log),
        "total_model_api_calls": len(generation_log) + len(interpretation_log) + len(preflight_log),
        "rows": summary_rows,
        "production_code_changed": False,
        "forbidden_replay": True,
    }
    _dump(OUT / "run_manifest.json", manifest)
    _dump(OUT / "generation_calls.json", generation_log)
    _dump(OUT / "interpretation_calls.json", interpretation_log)
    _dump(OUT / "preflight_calls.json", preflight_log)
    print(json.dumps({k: manifest[k] for k in manifest if k != "status_short"}, indent=2, default=str), flush=True)
    print(OUT, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
