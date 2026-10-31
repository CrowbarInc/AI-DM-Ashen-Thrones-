#!/usr/bin/env python3
"""PR-BR multi-turn provenance validation harness.

Measurement only. Not production. Two isolated sequences, four gameplay
turns each. Within a sequence the next turn loads the committed session,
discourse, provenance, and scenes left by the previous turn. Nothing in
this file patches prompts, validators, resolvers, or state between turns.

Commands are files so the process stays up for one startup preflight:

    control/command.json
        {"op": "turn", "sequence": "A", "turn_id": "A1", "player_text": "..."}
        {"op": "seed_b"}
        {"op": "stop"}
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
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
OUT = ROOT / "artifacts" / "pr_br_multiturn_provenance" / STAMP
CONTROL = OUT / "control"
BASE_SCENES = ("frontier_gate", "market_quarter", "old_milestone")


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        return str(exc)


def _dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


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


def _npc(
    npc_id: str,
    name: str,
    scene_id: str,
    role: str,
    aliases: list[str],
    topics: list[dict[str, str]],
    *,
    knowledge_scope: list[str],
    information_reliability: str,
) -> dict[str, Any]:
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
        "topics": topics,
        "knowledge_scope": knowledge_scope,
        "information_reliability": information_reliability,
        "stance_toward_player": "neutral",
        "origin_kind": "authored_background",
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


def _inert_base(scene_id: str) -> dict[str, Any]:
    """Keep the exit graph valid without shipping patrol, notice, or footprint prose."""
    scene = default_scene(scene_id)
    inner = scene["scene"]
    inner["summary"] = "Unused holding scene. It is not part of this validation."
    inner["visible_facts"] = []
    inner["opening_seed_facts"] = []
    inner["journal_seed_facts"] = []
    inner["discoverable_clues"] = []
    inner["hidden_facts"] = []
    inner["enemies"] = []
    inner["actions"] = []
    inner["addressables"] = []
    inner["interactables"] = []
    return scene


def _campaign() -> dict[str, Any]:
    campaign = default_campaign()
    campaign["premise"] = (
        "Galinor is spending an ordinary day in Reedbank, a riverside hamlet of small craft sheds."
    )
    campaign["tone"] = "ordinary craft work in a quiet hamlet"
    campaign["character_role"] = "A traveler passing through Reedbank."
    campaign["starting_context"] = campaign["premise"]
    campaign["character_secret"] = {
        "title": "None",
        "description": "No secret is in play for this validation.",
        "implications": [],
        "hidden_truth": "",
    }
    campaign["world_pressures"] = ["Ordinary craft work and the weather in a riverside hamlet."]
    campaign["environmental_threats"] = []
    campaign["gm_guidance"] = [
        "The current scene is an ordinary craft shed in Reedbank.",
        "People present are ordinary workers unless the scene says otherwise.",
        "Do not invent a cause, an actor, an organization, or a hidden place for an unexplained condition.",
    ]
    campaign["long_term_goals"] = ["Get through an ordinary day in Reedbank."]
    campaign["campaign_structure"] = "A short ordinary day in Reedbank."
    return campaign


def _world(npcs: list[dict[str, Any]]) -> dict[str, Any]:
    world = default_world()
    world["settlements"] = [
        {
            "id": "reedbank",
            "name": "Reedbank",
            "type": "riverside_hamlet",
            "tags": ["craft", "river"],
            "status": "ordinary",
            "notes": "A hamlet of small craft sheds along a slow river.",
        }
    ]
    world["factions"] = []
    world["npcs"] = npcs
    world["assets"] = []
    world["projects"] = []
    world["world_flags"] = []
    world["event_log"] = []
    world["clues"] = {}
    world["inference_rules"] = []
    world["world_state"] = {"flags": {}, "counters": {}, "clocks": {}}
    return world


def _session(scene_id: str) -> dict[str, Any]:
    session = create_fresh_session_document()
    session["active_scene_id"] = scene_id
    session["visited_scene_ids"] = [scene_id]
    session["scene_state"] = _fresh_scene_state(scene_id)
    session["campaign_started"] = True
    session["turn_counter"] = 0
    session["debug_traces"] = []
    session["chat_history"] = []
    return session


LINDEN = _npc(
    "linden",
    "Linden",
    "seat_shop",
    "chair-seater",
    ["chair-seater", "chair seater"],
    [
        {"id": "work", "text": "Linden seats wooden chairs with woven rush."},
        {
            "id": "brine_hearsay",
            "text": (
                "Linden heard a carter claim that the brine cask at the curing house was found unbunged. "
                "Linden did not see the cask and does not know whether that claim is true."
            ),
        },
    ],
    knowledge_scope=["rush_seating"],
    information_reliability="partial",
)


SEQUENCE_A = {
    "id": "A",
    "scene": _scene(
        "clay_shed",
        "Reedbank clay shed",
        (
            "A low shed holds unfired pots on plank shelves. The large water jar on the center shelf "
            "is split from lip to base, and the clay inside it has dried into pale flakes. A stack of "
            "unused coil-pots sits intact on the lower shelf. The shed door stands open to the yard. "
            "Nothing here says who split the jar, when, or why."
        ),
        [
            _fact(
                "The large water jar on the center shelf is split from lip to base.",
                {
                    "kind": "world_fact",
                    "subject": "water_jar",
                    "subject_aliases": ["water jar", "jar", "large water jar"],
                    "relation": "condition",
                    "value": "split",
                    "value_aliases": ["split", "split from lip to base"],
                    "polarity": "positive",
                },
            ),
            _fact(
                "The clay inside the split water jar has dried into pale flakes.",
                {
                    "kind": "world_fact",
                    "subject": "jar_clay",
                    "subject_aliases": ["clay", "dried clay", "pale flakes", "flakes"],
                    "relation": "condition",
                    "value": "dried flakes",
                    "value_aliases": ["dried", "pale flakes", "dried into pale flakes"],
                    "polarity": "positive",
                },
            ),
            _fact(
                "A stack of unused coil-pots sits intact on the lower shelf.",
                {
                    "kind": "world_fact",
                    "subject": "coil_pots",
                    "subject_aliases": ["coil-pots", "coil pots", "pots", "unused coil-pots"],
                    "relation": "condition",
                    "value": "intact",
                    "value_aliases": ["intact", "unused", "stack"],
                    "polarity": "positive",
                },
            ),
            _fact(
                "The shed door stands open to the yard.",
                {
                    "kind": "world_fact",
                    "subject": "shed_door",
                    "subject_aliases": ["shed door", "door"],
                    "relation": "condition",
                    "value": "open",
                    "value_aliases": ["open", "stands open"],
                    "polarity": "positive",
                },
            ),
        ],
        interactables=[
            {
                "id": "water_jar",
                "label": "split water jar",
                "aliases": ["water jar", "jar", "large water jar", "clay"],
                "type": "investigate",
            }
        ],
    ),
    "extra_scenes": [],
    "npcs": [],
}


SEQUENCE_B = {
    "id": "B",
    "scene": _scene(
        "seat_shop",
        "Reedbank seat shop",
        (
            "A narrow shop smells of damp rush. Linden, a chair-seater, is seating a wooden chair "
            "with green rush. Bundles of dried rush lean against the wall. An open side door looks "
            "out toward the osier rack. Linden is an ordinary worker with no special charge."
        ),
        [
            "Linden is seating a wooden chair with green rush.",
            "Bundles of dried rush lean against the shop wall.",
        ],
        exits=[{"label": "Go out to the osier rack", "target_scene_id": "osier_rack"}],
        npcs=[LINDEN],
        mode="social",
    ),
    "extra_scenes": [
        _scene(
            "osier_rack",
            "Reedbank osier rack",
            (
                "Split withies hang in rows from a long drying rack behind the seat shop. "
                "The ground under the rack is pale and dry."
            ),
            [
                "Split withies hang in rows from the drying rack.",
                "The ground under the osier rack is pale and dry.",
            ],
            exits=[{"label": "Return to the seat shop", "target_scene_id": "seat_shop"}],
        )
    ],
    "npcs": [LINDEN],
}


def _write_base_scenes() -> None:
    for scene_id in BASE_SCENES:
        storage._save_json(storage.scene_path(scene_id), _inert_base(scene_id))


def _seed(spec: dict[str, Any]) -> dict[str, Any]:
    scene = spec["scene"]
    scene_id = scene["scene"]["id"]
    _write_base_scenes()
    for extra in spec["extra_scenes"]:
        storage._save_json(storage.scene_path(extra["scene"]["id"]), extra)
    storage._save_json(storage.scene_path(scene_id), scene)
    storage._save_json(storage.CAMPAIGN_PATH, _campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    storage._save_json(storage.WORLD_PATH, _world(spec["npcs"]))
    storage.save_session(_session(scene_id))
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    return {
        "sequence": spec["id"],
        "scene": scene,
        "extra_scenes": spec["extra_scenes"],
        "world": _world(spec["npcs"]),
        "campaign": _campaign(),
        "note": (
            "Controlled seed. Unused holding scenes exist only so the default exit graph validates. "
            "Their prose, clues, and addressables were cleared. No facts were inserted between turns."
        ),
    }


def _prompt_projection(messages: Any) -> dict[str, Any]:
    user = ""
    system = ""
    roles = []
    if isinstance(messages, list):
        for message in messages:
            if not isinstance(message, dict):
                continue
            roles.append(str(message.get("role") or ""))
            content = str(message.get("content") or "")
            if message.get("role") == "user":
                user = content
            elif message.get("role") == "system":
                system = content
    return {
        "roles": roles,
        "system_chars": len(system),
        "user_chars": len(user),
        "contains_resolution_contract": "resolution_contract" in user or "Resolution Contract" in user,
        "contains_gm_resolution_decision": "gm_resolution_decision" in user or "GMResolutionDecision" in user,
        "contains_authoritative_retry_context": "AUTHORITATIVE RETRY CONTEXT" in user,
        "contains_validation_failure": "validation_failure" in user,
        "system_text": system,
        "user_text": user,
    }


def _all_scenes() -> dict[str, Any]:
    found: dict[str, Any] = {}
    if storage.SCENES_DIR.exists():
        for path in sorted(storage.SCENES_DIR.glob("*.json")):
            try:
                found[path.stem] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                found[path.stem] = {"unreadable": True}
    return found


def _authoritative() -> dict[str, Any]:
    session = storage.load_session()
    scene_id = str(session.get("active_scene_id") or "")
    world = storage.load_world()
    log_text = storage.SESSION_LOG_PATH.read_text(encoding="utf-8") if storage.SESSION_LOG_PATH.exists() else ""
    return {
        "session": session,
        "world": world,
        "scenes": _all_scenes(),
        "active_scene_id": scene_id,
        "session_log": log_text,
    }


def _meta(payload: dict[str, Any]) -> dict[str, Any]:
    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    return meta


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CONTROL.mkdir(parents=True, exist_ok=True)
    storage_a = OUT / "storage_a"
    storage_b = OUT / "storage_b"
    _isolate(storage_a)
    seeded_a = _seed(SEQUENCE_A)
    _dump(OUT / "sequence_A" / "A0_initial_state.json", seeded_a)
    _dump(OUT / "sequence_A" / "A0_authoritative.json", _authoritative())

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
                "at": datetime.now(timezone.utc).isoformat(),
                "purpose": kwargs.get("purpose"),
                "retry_attempt": kwargs.get("retry_attempt"),
                "retry_reason": kwargs.get("retry_reason"),
                "model": model_name,
                "player_facing_text": text,
                "result_keys": sorted(str(key) for key in result.keys()) if isinstance(result, dict) else [],
                "prompt": _prompt_projection(messages),
            }
        )
        return result

    def wrapped_interpretation(messages):
        interpretation_log.append(
            {"at": datetime.now(timezone.utc).isoformat(), "event": "attempt", "prompt": _prompt_projection(messages)}
        )
        try:
            text = real_invoke(messages)
        except Exception as exc:
            interpretation_log[-1]["error"] = f"{type(exc).__name__}: {exc}"
            raise
        interpretation_log[-1]["output_text"] = str(text)
        return text

    def wrapped_preflight(*args, **kwargs):
        preflight_log.append({"at": datetime.now(timezone.utc).isoformat(), "event": "preflight"})
        try:
            result = real_preflight(*args, **kwargs)
        except Exception as exc:
            preflight_log[-1]["error"] = f"{type(exc).__name__}: {exc}"
            raise
        if isinstance(result, dict):
            preflight_log[-1]["ok"] = bool(result.get("ok"))
            preflight_log[-1]["health_class"] = result.get("health_class")
        else:
            preflight_log[-1]["ok"] = getattr(result, "ok", None)
            preflight_log[-1]["health_class"] = getattr(result, "health_class", None)
            preflight_log[-1]["result_type"] = type(result).__name__
        return result

    api_module.call_gpt = wrapped_generation
    gm_module.call_gpt = wrapped_generation
    interpreter_module._invoke_interpretation_model = wrapped_interpretation
    preflight_module.run_upstream_api_preflight = wrapped_preflight
    api_module.run_upstream_api_preflight = wrapped_preflight

    active_sequence = "A"
    b_seeded = False
    summary_rows: list[dict[str, Any]] = []

    def _counts() -> dict[str, int]:
        initial = sum(1 for call in generation_log if int(call.get("retry_attempt") or 0) == 0)
        retry = sum(1 for call in generation_log if int(call.get("retry_attempt") or 0) > 0)
        return {
            "gameplay_turns_completed": sum(1 for row in summary_rows if row.get("http_status") == 200),
            "initial_generation_calls": initial,
            "retry_generation_calls": retry,
            "generation_calls": len(generation_log),
            "interpretation_calls": len(interpretation_log),
            "preflight_calls": len(preflight_log),
            "total_model_api_calls": len(generation_log) + len(interpretation_log) + len(preflight_log),
        }

    def _write_status(state: str, extra: dict[str, Any] | None = None) -> None:
        payload = {"state": state, "stamp": STAMP, "out": str(OUT), "active_sequence": active_sequence, **_counts()}
        if extra:
            payload.update(extra)
        _dump(CONTROL / "status.json", payload)
        print(f"STATUS {json.dumps(payload, default=str)}", flush=True)

    def _run_turn(sequence: str, turn_id: str, player_text: str) -> None:
        nonlocal active_sequence
        if sequence != active_sequence:
            raise RuntimeError(f"sequence {sequence} is not active ({active_sequence})")
        turn_dir = OUT / f"sequence_{sequence}" / turn_id
        if (turn_dir / "completed.json").exists():
            raise RuntimeError(f"{turn_id} already completed; refusing rerun")
        turn_dir.mkdir(parents=True, exist_ok=True)
        before = _authoritative()
        _dump(turn_dir / "state_before.json", before)
        gen_before = len(generation_log)
        interp_before = len(interpretation_log)
        pre_before = len(preflight_log)
        response = client.post("/api/chat", json={"text": player_text})
        status = response.status_code
        payload = response.json()
        gm_text = _gm_text_from_chat_payload(payload) if isinstance(payload, dict) else ""
        resolution = payload.get("resolution") if isinstance(payload, dict) and isinstance(payload.get("resolution"), dict) else {}
        gm_output = payload.get("gm_output") if isinstance(payload, dict) and isinstance(payload.get("gm_output"), dict) else {}
        gm_meta = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
        res_meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
        contract = res_meta.get("resolution_contract") if isinstance(res_meta.get("resolution_contract"), dict) else {}
        decision = res_meta.get("gm_resolution_decision") if isinstance(res_meta.get("gm_resolution_decision"), dict) else {}
        after = _authoritative()
        turn_generations = generation_log[gen_before:]
        turn_interps = interpretation_log[interp_before:]
        record = {
            "sequence": sequence,
            "turn_id": turn_id,
            "player_text": player_text,
            "http_status": status,
            "emitted_narration": gm_text,
            "selected_resolver": res_meta.get("selected_resolver"),
            "interaction_obligation": res_meta.get("interaction_obligation"),
            "executable_obligations": decision.get("executable_obligations"),
            "resolution_contract": contract,
            "gm_resolution_decision": decision,
            "decision_contract_id": decision.get("contract_id"),
            "contract_id": contract.get("contract_id"),
            "decision_id_matches_contract": bool(decision)
            and str(decision.get("contract_id") or "") == str(contract.get("contract_id") or "")
            and bool(contract.get("contract_id")),
            "generation_call_count": len(turn_generations),
            "initial_generation_calls": sum(1 for call in turn_generations if int(call.get("retry_attempt") or 0) == 0),
            "retry_generation_calls": sum(1 for call in turn_generations if int(call.get("retry_attempt") or 0) > 0),
            "interpretation_call_count": len(turn_interps),
            "preflight_calls_during_turn": len(preflight_log) - pre_before,
            "active_scene_before": before.get("active_scene_id"),
            "active_scene_after": after.get("active_scene_id"),
        }
        _dump(turn_dir / "turn_record.json", record)
        _dump(turn_dir / "resolution.json", resolution)
        _dump(turn_dir / "gm_output.json", gm_output)
        _dump(turn_dir / "state_after.json", after)
        _dump(
            turn_dir / "generations.json",
            [
                {
                    **{key: call[key] for key in call if key != "prompt"},
                    "prompt_flags": {
                        key: (call.get("prompt") or {}).get(key)
                        for key in (
                            "user_chars",
                            "system_chars",
                            "contains_resolution_contract",
                            "contains_gm_resolution_decision",
                            "contains_authoritative_retry_context",
                            "contains_validation_failure",
                        )
                    },
                    "player_facing_text": call.get("player_facing_text"),
                }
                for call in turn_generations
            ],
        )
        _dump(turn_dir / "generation_prompts.json", turn_generations)
        _dump(turn_dir / "interpretations.json", turn_interps)
        _dump(turn_dir / "completed.json", {"ok": status == 200, "http_status": status})
        summary_rows.append(
            {
                "turn_id": turn_id,
                "http_status": status,
                "player_text": player_text,
                "emitted_narration": gm_text,
                "active_scene_before": before.get("active_scene_id"),
                "active_scene_after": after.get("active_scene_id"),
                "selected_resolver": res_meta.get("selected_resolver"),
                "contract_id": contract.get("contract_id"),
                "decision_contract_id": decision.get("contract_id"),
                "decision_present": bool(decision),
                "decision_outcome": decision.get("outcome_classification"),
                "initial_generations": record["initial_generation_calls"],
                "retry_generations": record["retry_generation_calls"],
                "interpretation_calls": len(turn_interps),
            }
        )
        _dump(OUT / "summary_rows.json", summary_rows)
        print(f"TURN {turn_id} status={status} scene={after.get('active_scene_id')} resolver={res_meta.get('selected_resolver')}", flush=True)
        print(f"EMIT {gm_text}", flush=True)

    _dump(
        ROOT / "artifacts" / "pr_br_multiturn_provenance" / "ACTIVE.json",
        {"stamp": STAMP, "out": str(OUT), "head": _git(["rev-parse", "HEAD"])},
    )
    _write_status("starting")
    with TestClient(app) as client:
        _write_status("ready")
        while True:
            command_path = CONTROL / "command.json"
            if not command_path.exists():
                time.sleep(0.4)
                continue
            try:
                command = json.loads(command_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                time.sleep(0.2)
                continue
            command_path.unlink(missing_ok=True)
            op = str(command.get("op") or "")
            _write_status("running", {"op": op, "turn_id": command.get("turn_id")})
            try:
                if op == "stop":
                    break
                if op == "seed_b":
                    if b_seeded:
                        raise RuntimeError("sequence B already seeded")
                    _isolate(storage_b)
                    seeded_b = _seed(SEQUENCE_B)
                    _dump(OUT / "sequence_B" / "B0_initial_state.json", seeded_b)
                    _dump(OUT / "sequence_B" / "B0_authoritative.json", _authoritative())
                    b_seeded = True
                    active_sequence = "B"
                    _dump(CONTROL / "ack.json", {"op": "seed_b", "ok": True, "active_scene_id": "seat_shop"})
                elif op == "turn":
                    _run_turn(str(command["sequence"]), str(command["turn_id"]), str(command["player_text"]))
                    _dump(CONTROL / "ack.json", {"op": "turn", "ok": True, "turn_id": command.get("turn_id"), **_counts()})
                else:
                    raise RuntimeError(f"unknown op {op}")
            except Exception as exc:
                _dump(
                    CONTROL / "ack.json",
                    {"op": op, "ok": False, "error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()},
                )
                print(f"COMMAND_ERROR {type(exc).__name__}: {exc}", flush=True)
            _write_status("ready")

    manifest = {
        "stamp": STAMP,
        "head": _git(["rev-parse", "HEAD"]),
        "head_subject": _git(["log", "-1", "--format=%s"]),
        "status_short": _git(["status", "--short"]),
        "production_code_changed": False,
        "sequences_isolated": True,
        "state_sanitized_between_turns": False,
        "rows": summary_rows,
        **_counts(),
    }
    _dump(OUT / "run_manifest.json", manifest)
    _dump(OUT / "generation_calls.json", generation_log)
    _dump(OUT / "interpretation_calls.json", interpretation_log)
    _dump(OUT / "preflight_calls.json", preflight_log)
    _write_status("stopped")
    print("STOPPED", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
