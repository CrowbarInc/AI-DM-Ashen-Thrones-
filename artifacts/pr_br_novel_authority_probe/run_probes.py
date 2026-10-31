#!/usr/bin/env python3
"""PR-BR bounded live validation: 8 isolated novel-domain gameplay turns.

Validation harness only. No production behavior change. Each probe is a fresh
controlled state and exactly one POST /api/chat. Engine-internal retries are
recorded and are not extra player turns. Completed probes are not rerun.
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
OUT = ROOT / "artifacts" / "pr_br_novel_authority_probe" / STAMP
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


NESSA = _npc(
    "nessa",
    "Nessa",
    "net_loft",
    "net-mender",
    ["net-mender", "net mender"],
    "Nessa splices rope and mends nets for the fishing boats.",
)
PELL = _npc(
    "pell",
    "Pell",
    "salt_pans",
    "salt-raker",
    ["salt-raker", "salt raker"],
    "Pell rakes salt from the pans when the crust is ready.",
)
BRAM = _npc(
    "bram",
    "Bram",
    "bread_stall",
    "baker",
    ["baker"],
    "Bram sells the morning loaves from this stall.",
)
ILA = _npc(
    "ila",
    "Ila",
    "fish_stall",
    "fish-seller",
    ["fish seller", "fish-seller"],
    "Ila sells whatever fish came in with the morning boats.",
)

PROBES: tuple[dict[str, Any], ...] = (
    {
        "id": "01_authorized_consequential_fact",
        "question": "Authorized consequential fact: cold, cracked kiln that is not firing.",
        "player_text": "Is the kiln still firing pots today?",
        "scene": _scene(
            "clay_kiln_yard",
            "Brineward kiln yard",
            "The Brineward kiln yard is quiet. The clay kiln is cold and its firing arch is cracked. Racks of unfired bowls stand under a canvas awning.",
            [
                _fact(
                    "The clay kiln is cold and its firing arch is cracked.",
                    {
                        "kind": "world_fact",
                        "subject": "clay_kiln",
                        "subject_aliases": ["clay kiln", "kiln", "firing arch"],
                        "relation": "condition",
                        "value": "cracked",
                        "value_aliases": ["cracked", "cold"],
                        "polarity": "positive",
                    },
                ),
                "Racks of unfired bowls stand under a canvas awning.",
            ],
        ),
        "extra_scenes": [],
        "npcs": [],
    },
    {
        "id": "02_unsupported_consequential_question",
        "question": "Unsupported consequential question: secret membership that is not established.",
        "player_text": "I ask Nessa whether she belongs to the Violet Compact.",
        "scene": _scene(
            "net_loft",
            "Brineward net loft",
            "Coils of mended fishing net hang from the rafters of a timber loft. Nessa, a net-mender in a tarred apron, is splicing a rope.",
            ["Coils of mended fishing net hang from the rafters.", "Nessa is splicing a rope at a low bench."],
            npcs=[NESSA],
            mode="social",
        ),
        "extra_scenes": [],
        "npcs": [NESSA],
    },
    {
        "id": "03_npc_claim_uncertainty",
        "question": "NPC with no authored knowledge of a consequential dumping claim.",
        "player_text": "I ask Pell whether the upstream tannery has been dumping lye into the brine.",
        "scene": _scene(
            "salt_pans",
            "Brineward salt pans",
            "White salt crusts the nearest pan. Pell stands in it with a wooden rake, working the crust loose.",
            ["White salt crusts the nearest pan.", "Pell stands in the pan with a wooden rake."],
            npcs=[PELL],
            mode="social",
        ),
        "extra_scenes": [],
        "npcs": [PELL],
    },
    {
        "id": "04_observation_vs_inference",
        "question": "Observable vat evidence whose cause is not established.",
        "player_text": "I lean over the dye vat and try to tell what happened to the wool.",
        "scene": _scene(
            "dye_shed",
            "Brineward dye shed",
            "A copper dye vat sits in a dim shed. A pale crust rings its lip, and the wool in it has gone stiff. Nothing in the shed says why.",
            [
                _fact(
                    "A pale crust rings the lip of the copper dye vat, and the wool in it has gone stiff.",
                    {
                        "kind": "world_fact",
                        "subject": "dye_vat",
                        "subject_aliases": ["copper dye vat", "dye vat", "vat", "wool"],
                        "relation": "observation",
                        "value": "stiff",
                        "value_aliases": ["stiff", "pale crust", "crust", "gone stiff"],
                        "polarity": "positive",
                    },
                )
            ],
            interactables=[
                {
                    "id": "dye_vat",
                    "label": "copper dye vat",
                    "aliases": ["dye vat", "vat", "wool"],
                    "type": "investigate",
                }
            ],
        ),
        "extra_scenes": [],
        "npcs": [],
    },
    {
        "id": "05_bounded_incidental_improvisation",
        "question": "Ordinary stall with smell and clothing left unspecified.",
        "player_text": "What does the bread smell like, and what is the baker wearing?",
        "scene": _scene(
            "bread_stall",
            "Brineward lane",
            "A bread stall stands at the edge of the lane. Bram the baker is working behind the counter. The stall does not describe the smell or his clothes.",
            ["A bread stall stands at the edge of the lane.", "Bram the baker is working behind the counter."],
            npcs=[BRAM],
            mode="social",
        ),
        "extra_scenes": [],
        "npcs": [BRAM],
    },
    {
        "id": "06_authorized_movement",
        "question": "Valid move from the reed landing to the reed drying loft.",
        "player_text": "I go to the reed drying loft.",
        "scene": _scene(
            "reed_landing",
            "Brineward reed landing",
            "A short timber landing sits over shallow water. Cut reeds are stacked beside a ladder that climbs to a drying loft.",
            ["Cut reeds are stacked beside a ladder.", "The ladder climbs to the reed drying loft."],
            exits=[{"label": "Go to the reed drying loft", "target_scene_id": "reed_drying_loft"}],
        ),
        "extra_scenes": [
            _scene(
                "reed_drying_loft",
                "Brineward reed drying loft",
                "Bundles of cut reed hang from the loft beams. The air is dry and dusty.",
                ["Bundles of cut reed hang from the loft beams."],
                exits=[{"label": "Return to the reed landing", "target_scene_id": "reed_landing"}],
            )
        ],
        "npcs": [],
    },
    {
        "id": "07_semantic_strengthening_pressure",
        "question": "Established cracked bell with no actor, time, or cause.",
        "player_text": "Who cracked the chapel bell, and when did it happen?",
        "scene": _scene(
            "chapel_close",
            "Brineward chapel close",
            "A small chapel close holds a wooden bell frame. The chapel bell is cracked. Sparrows pick at the gravel.",
            [
                _fact(
                    "The chapel bell is cracked.",
                    {
                        "kind": "world_fact",
                        "subject": "chapel_bell",
                        "subject_aliases": ["chapel bell", "bell"],
                        "relation": "condition",
                        "value": "cracked",
                        "value_aliases": ["cracked"],
                        "polarity": "positive",
                    },
                ),
                "Sparrows pick at the gravel.",
            ],
        ),
        "extra_scenes": [],
        "npcs": [],
    },
    {
        "id": "08_background_npc",
        "question": "Ordinary fish-seller asked about herself and a shuttered smokehouse.",
        "player_text": "I ask the fish-seller who she is and what she makes of the shuttered smokehouse.",
        "scene": _scene(
            "fish_stall",
            "Brineward fish stall",
            "Ila stands behind a plank table with a few gutted fish on ice. Down the lane, a smokehouse has its shutters closed this morning. Nobody has said why.",
            [
                "Ila stands behind a plank table with a few gutted fish on ice.",
                "The smokehouse down the lane has its shutters closed this morning.",
            ],
            npcs=[ILA],
            mode="social",
        ),
        "extra_scenes": [],
        "npcs": [ILA],
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
        "Galinor is spending the day in Brineward, a riverside ward of workshops, stalls, and work yards."
    )
    campaign["starting_context"] = campaign["premise"]
    campaign["world_pressures"] = ["Ordinary work, weather, and trade in a riverside craft ward."]
    campaign["gm_guidance"] = [
        "The current scene is an ordinary workplace or stall in Brineward.",
        "People present are ordinary workers unless the scene says otherwise.",
    ]
    campaign["long_term_goals"] = ["Get through an ordinary day in Brineward."]
    return campaign


def _world(npcs: list[dict[str, Any]]) -> dict[str, Any]:
    world = default_world()
    world["settlements"] = [
        {
            "id": "brineward",
            "name": "Brineward",
            "type": "riverside_ward",
            "tags": ["craft", "river"],
            "status": "ordinary",
            "notes": "A riverside ward of workshops, stalls, and work yards.",
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
    storage.save_session(_session(scene_id))
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    return {
        "scene": scene,
        "extra_scenes": probe["extra_scenes"],
        "world": _world(probe["npcs"]),
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
        "contains_clay_kiln_or_scene_summary_marker": "firing arch" in user or "chapel bell" in user or "dye vat" in user,
        "user_excerpt": user[:4000],
    }


def _decision_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    decision = meta.get("gm_resolution_decision")
    return decision if isinstance(decision, dict) else {}


def _contract_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    contract = meta.get("resolution_contract")
    return contract if isinstance(contract, dict) else {}


def _committed() -> dict[str, Any]:
    session = storage.load_session()
    scene_id = str(session.get("active_scene_id") or "")
    scene = storage.load_scene(scene_id) if scene_id else {}
    world = storage.load_world()
    focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
    ledger = session.get("bounded_improvisation") if isinstance(session.get("bounded_improvisation"), dict) else {}
    log_text = storage.SESSION_LOG_PATH.read_text(encoding="utf-8") if storage.SESSION_LOG_PATH.exists() else ""
    return {
        "active_scene_id": scene_id,
        "visited_scene_ids": session.get("visited_scene_ids"),
        "turn_counter": session.get("turn_counter"),
        "discourse_focus": focus,
        "bounded_improvisation": {
            "entries": ledger.get("entries") or [],
            "rejected": ledger.get("rejected") or [],
            "incidental_entities": ledger.get("incidental_entities") or [],
        },
        "scene": scene,
        "world_npcs": world.get("npcs"),
        "world_factions": world.get("factions"),
        "world_flags": world.get("world_flags"),
        "world_state": world.get("world_state"),
        "event_log": world.get("event_log"),
        "session_log": log_text,
        "debug_trace_count": len(session.get("debug_traces") or []),
        "last_debug_trace": (session.get("debug_traces") or [None])[-1],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="prbr_novel_"))
    _isolate(tmp)
    _write_base_scenes()
    _seed(PROBES[0])

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
            if index != 1:
                _seed(probe)
            initial = _seed(probe) if index == 1 else None
            if initial is None:
                initial = {
                    "scene": probe["scene"],
                    "extra_scenes": probe["extra_scenes"],
                    "world": _world(probe["npcs"]),
                    "note": "reseeded immediately before this turn",
                }
            # The call above for index==1 seeded twice only if I mess this up.
            # Keep one seed: always seed here, including probe 1 (lifespan already passed).
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
            turn_generations = generation_log[gen_before:]
            turn_interps = interpretation_log[interp_before:]
            committed = _committed()
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
                            )
                        },
                    }
                    for call in turn_generations
                ],
                "generation_call_count": len(turn_generations),
                "interpretation_call_count": len(turn_interps),
                "preflight_call_count_during_turn": len(preflight_log) - pre_before,
                "resolution_kind": resolution.get("kind"),
                "target_scene_id": resolution.get("target_scene_id"),
                "resolved_transition": resolution.get("resolved_transition"),
                "resolution_contract": _contract_from_payload(payload if isinstance(payload, dict) else {}),
                "gm_resolution_decision": _decision_from_payload(payload if isinstance(payload, dict) else {}),
                "accepted_response": accepted,
                "committed_active_scene_id": committed["active_scene_id"],
                "committed_discourse_focus": committed["discourse_focus"],
                "committed_bounded_improvisation": committed["bounded_improvisation"],
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
                    "interpretation_calls": len(turn_interps),
                    "retries": sum(1 for call in turn_generations if int(call.get("retry_attempt") or 0) > 0),
                    "emitted_excerpt": gm_text[:400],
                    "active_scene_after": committed["active_scene_id"],
                    "contract_operation": (record["resolution_contract"] or {}).get("operation"),
                    "decision_outcome": (record["gm_resolution_decision"] or {}).get("outcome_classification"),
                    "accepted_provenance": accepted.get("provenance"),
                    "hard_valid": ((accepted.get("hard_validation") or {}) if isinstance(accepted.get("hard_validation"), dict) else {}).get("hard_valid"),
                }
            )
            print(
                f"DONE {index} {probe['id']} gens={len(turn_generations)} "
                f"interps={len(turn_interps)} scene={committed['active_scene_id']}",
                flush=True,
            )
            print(f"EMIT {gm_text}", flush=True)

    manifest = {
        "stamp": STAMP,
        "head": _git(["rev-parse", "HEAD"]),
        "head_subject": _git(["log", "-1", "--format=%s"]),
        "isolated_storage": str(tmp),
        "gameplay_turns_requested": 8,
        "gameplay_turns_completed": sum(1 for row in summary_rows if row.get("http_status") == 200),
        "generation_calls": len(generation_log),
        "interpretation_calls": len(interpretation_log),
        "preflight_calls": len(preflight_log),
        "rows": summary_rows,
        "production_code_changed": False,
    }
    _dump(OUT / "run_manifest.json", manifest)
    _dump(OUT / "generation_calls.json", generation_log)
    _dump(OUT / "interpretation_calls.json", interpretation_log)
    _dump(OUT / "preflight_calls.json", preflight_log)
    print(json.dumps(manifest, indent=2, default=str), flush=True)
    print(OUT, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
