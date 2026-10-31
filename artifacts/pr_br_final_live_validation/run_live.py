#!/usr/bin/env python3
"""Four-turn PR-BR final live validation.

Measurement only. One fresh domain, one persistent production TestClient,
at most four gameplay turns, and no replay of a completed turn.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
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
CAMPAIGN_ROOT = ROOT / "artifacts" / "pr_br_final_live_validation"
OUT = CAMPAIGN_ROOT / STAMP
CONTROL = OUT / "control"
ACTIVE = CAMPAIGN_ROOT / "ACTIVE.json"
MAX_TURNS = 4
BASE_SCENES = ("frontier_gate", "market_quarter", "old_milestone")


def _dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        return str(exc)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _production_hashes() -> dict[str, str]:
    rows: dict[str, str] = {}
    for base in (ROOT / "game", ROOT / "prompts"):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                rows[path.relative_to(ROOT).as_posix()] = _sha256(path)
    return rows


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


def _fact(text: str, identity: dict[str, Any]) -> dict[str, Any]:
    return {"text": text, "semantic_identity": identity}


NESSA = {
    "id": "nessa",
    "name": "Nessa",
    "location": "bathhouse_pump_alcove",
    "role": "bath attendant",
    "affiliation": "",
    "disposition": "neutral",
    "current_agenda": "",
    "availability": "available",
    "tags": [],
    "aliases": ["attendant", "bath attendant"],
    "topics": [
        {
            "id": "towels",
            "text": "Nessa is folding clean towels beside the cedar bench.",
        }
    ],
}

SCENE = {
    "scene": {
        "id": "bathhouse_pump_alcove",
        "location": "Dunmere public bathhouse pump alcove",
        "summary": (
            "A tiled pump alcove serves an ordinary public bathhouse. The long iron "
            "pump handle is visibly bowed, and its pivot pin is sheared through. "
            "Two folded towels rest on a cedar bench. A blue-glazed soap dish sits "
            "beside the washbasin. Nessa, an ordinary bath attendant, folds towels "
            "nearby. Nothing states a cause, responsible actor, event time, history, "
            "explanation, or corroborating evidence for the damage."
        ),
        "mode": "social",
        "visible_facts": [
            _fact(
                "The bathhouse pump's long iron handle is visibly bowed, and its pivot pin is sheared through.",
                {
                    "kind": "world_fact",
                    "subject": "bathhouse_pump_handle",
                    "subject_aliases": [
                        "bathhouse pump",
                        "pump",
                        "pump handle",
                        "iron handle",
                        "pivot pin",
                    ],
                    "relation": "observation",
                    "value": "bowed handle and sheared pivot pin",
                    "value_aliases": [
                        "bowed",
                        "bent handle",
                        "sheared",
                        "sheared pin",
                        "broken pivot pin",
                    ],
                    "polarity": "positive",
                },
            ),
            "Two folded towels rest on a cedar bench.",
            "A blue-glazed soap dish sits beside the washbasin.",
            "Nessa folds clean towels beside the cedar bench.",
        ],
        "opening_seed_facts": [],
        "journal_seed_facts": [],
        "discoverable_clues": [],
        "hidden_facts": [],
        "exits": [],
        "enemies": [],
        "actions": [],
        "addressables": [
            {
                "id": "nessa",
                "name": "Nessa",
                "scene_id": "bathhouse_pump_alcove",
                "kind": "npc",
                "addressable": True,
                "address_priority": 0,
                "address_roles": ["bath attendant", "attendant"],
                "aliases": ["attendant", "bath attendant"],
            }
        ],
        "interactables": [],
    }
}


def _campaign() -> dict[str, Any]:
    value = default_campaign()
    value["premise"] = "Galinor is spending an ordinary afternoon in Dunmere."
    value["starting_context"] = value["premise"]
    value["world_pressures"] = ["Daily work continues around Dunmere."]
    value["gm_guidance"] = [
        "Use only the current scene's authored consequential facts as world truth.",
        "Nessa is an ordinary bath attendant unless the scene says otherwise.",
    ]
    value["long_term_goals"] = ["Spend an ordinary afternoon in Dunmere."]
    return value


def _world() -> dict[str, Any]:
    value = default_world()
    value["settlements"] = [
        {
            "id": "dunmere",
            "name": "Dunmere",
            "type": "river_town",
            "tags": ["bathhouse"],
            "status": "ordinary",
            "notes": "A small river town with a public bathhouse.",
        }
    ]
    value["factions"] = []
    value["npcs"] = [NESSA]
    value["assets"] = []
    value["projects"] = []
    value["world_flags"] = []
    value["event_log"] = []
    value["clues"] = {}
    value["world_state"] = {"flags": {}, "counters": {}, "clocks": {}}
    return value


def _session() -> dict[str, Any]:
    value = create_fresh_session_document()
    value["active_scene_id"] = "bathhouse_pump_alcove"
    value["visited_scene_ids"] = ["bathhouse_pump_alcove"]
    value["scene_state"] = _fresh_scene_state("bathhouse_pump_alcove")
    value["campaign_started"] = True
    value["turn_counter"] = 0
    value["debug_traces"] = []
    value["chat_history"] = []
    return value


def _seed() -> None:
    for scene_id in BASE_SCENES:
        storage._save_json(storage.scene_path(scene_id), default_scene(scene_id))
    storage._save_json(storage.scene_path("bathhouse_pump_alcove"), SCENE)
    storage._save_json(storage.CAMPAIGN_PATH, _campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    storage._save_json(storage.WORLD_PATH, _world())
    storage.save_session(_session())
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _authoritative_state() -> dict[str, Any]:
    session = storage.load_session()
    scene_id = str(session.get("active_scene_id") or "")
    return {
        "scene": storage.load_scene(scene_id) if scene_id else {},
        "world": storage.load_world(),
        "campaign": storage.load_campaign(),
        "character": storage.load_character(),
        "combat": storage.load_combat(),
        "conditions": storage.load_conditions(),
        "session": session,
        "session_log": (
            storage.SESSION_LOG_PATH.read_text(encoding="utf-8")
            if storage.SESSION_LOG_PATH.exists()
            else ""
        ),
    }


def _prompt_projection(messages: Any) -> dict[str, Any]:
    user = ""
    roles: list[str] = []
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
        "contains_temporal_provenance": "temporal_provenance" in user,
        "contains_authoritative_retry_context": "AUTHORITATIVE RETRY CONTEXT" in user,
        "contains_validation_failure": "validation_failure" in user,
        "user_content": user,
    }


def _meta(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
    res_meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    gm_output = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    gm_meta = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
    return resolution, res_meta, gm_meta


def _provenance_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    session = state.get("session") if isinstance(state.get("session"), dict) else {}
    temporal = (
        session.get("narration_temporal_provenance")
        if isinstance(session.get("narration_temporal_provenance"), dict)
        else {}
    )
    focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
    return {
        "gm_inferences": temporal.get("gm_inferences") or [],
        "player_hypotheses": temporal.get("player_hypotheses") or [],
        "accepted_incidentals": temporal.get("accepted_incidentals") or [],
        "rejected_consequential": temporal.get("rejected_consequential") or [],
        "discourse_focus_active_claim": focus.get("active_claim"),
        "full_temporal_provenance": temporal,
        "full_discourse_focus": focus,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=False)
    CONTROL.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="prbr_final_live_"))
    _isolate(tmp)
    _seed()

    import game.api as api_module
    import game.api_upstream_preflight as preflight_module
    import game.gm as gm_module
    import game.semantic_interpreter as interpreter_module

    generations: list[dict[str, Any]] = []
    interpretations: list[dict[str, Any]] = []
    preflights: list[dict[str, Any]] = []
    real_call = api_module.call_gpt
    real_interpret = interpreter_module._invoke_interpretation_model
    real_preflight = preflight_module.run_upstream_api_preflight

    def wrapped_generation(messages, **kwargs):
        row = {
            "purpose": kwargs.get("purpose"),
            "retry_attempt": kwargs.get("retry_attempt"),
            "retry_reason": kwargs.get("retry_reason"),
            "prompt": _prompt_projection(messages),
        }
        generations.append(row)
        try:
            row["result"] = real_call(messages, **kwargs)
            return row["result"]
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            raise

    def wrapped_interpretation(messages):
        row = {"event": "attempt", "prompt": _prompt_projection(messages)}
        interpretations.append(row)
        try:
            row["output_text"] = str(real_interpret(messages))
            return row["output_text"]
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            raise

    def wrapped_preflight(*args, **kwargs):
        row: dict[str, Any] = {"event": "preflight"}
        preflights.append(row)
        try:
            row["result"] = real_preflight(*args, **kwargs)
            return row["result"]
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            raise

    api_module.call_gpt = wrapped_generation
    gm_module.call_gpt = wrapped_generation
    interpreter_module._invoke_interpretation_model = wrapped_interpretation
    preflight_module.run_upstream_api_preflight = wrapped_preflight
    api_module.run_upstream_api_preflight = wrapped_preflight

    before_hashes = _production_hashes()
    _dump(OUT / "production_freeze_before.json", before_hashes)
    initial_state = _authoritative_state()
    _dump(OUT / "initial_authoritative_state.json", initial_state)
    _dump(
        OUT / "run_setup.json",
        {
            "stamp": STAMP,
            "head": _git(["rev-parse", "HEAD"]),
            "head_subject": _git(["log", "-1", "--format=%s"]),
            "status_short": _git(["status", "--short"]),
            "isolated_storage": str(tmp),
            "max_gameplay_turns": MAX_TURNS,
            "authored_scene": SCENE,
            "no_reruns": True,
        },
    )
    _dump(
        ACTIVE,
        {
            "stamp": STAMP,
            "output_dir": str(OUT),
            "command_path": str(CONTROL / "command.json"),
            "status": "starting",
        },
    )

    turns: list[dict[str, Any]] = []
    completed_ids: set[str] = set()

    def write_manifest(status: str) -> None:
        initial_count = sum(
            1 for call in generations if int(call.get("retry_attempt") or 0) == 0
        )
        retry_count = len(generations) - initial_count
        _dump(
            OUT / "run_manifest.json",
            {
                "stamp": STAMP,
                "head": _git(["rev-parse", "HEAD"]),
                "status": status,
                "gameplay_turns": len(turns),
                "successful_http_turns": sum(
                    1 for row in turns if row.get("http_status") == 200
                ),
                "initial_generation_calls": initial_count,
                "retry_generation_calls": retry_count,
                "interpretation_calls": len(interpretations),
                "preflight_calls": len(preflights),
                "other_model_calls": 0,
                "total_model_api_calls": (
                    len(generations) + len(interpretations) + len(preflights)
                ),
                "turns": turns,
                "no_reruns": True,
                "maximum_gameplay_turns": MAX_TURNS,
            },
        )
        _dump(OUT / "generation_calls.json", generations)
        _dump(OUT / "interpretation_calls.json", interpretations)
        _dump(OUT / "preflight_calls.json", preflights)

    exit_code = 0
    try:
        with TestClient(app) as client:
            _dump(
                ACTIVE,
                {
                    "stamp": STAMP,
                    "output_dir": str(OUT),
                    "command_path": str(CONTROL / "command.json"),
                    "status": "waiting_for_turn_1",
                },
            )
            write_manifest("waiting_for_turn_1")
            while len(turns) < MAX_TURNS:
                command_path = CONTROL / "command.json"
                if not command_path.exists():
                    time.sleep(0.2)
                    continue
                try:
                    command = json.loads(command_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    time.sleep(0.2)
                    continue
                command_path.unlink(missing_ok=True)
                turn_id = str(command.get("turn_id") or "")
                player_text = str(command.get("player_text") or "").strip()
                expected_id = str(len(turns) + 1)
                if command.get("op") != "turn" or turn_id != expected_id or not player_text:
                    _dump(
                        CONTROL / "ack.json",
                        {
                            "accepted": False,
                            "reason": "expected one non-empty sequential turn command",
                            "expected_turn_id": expected_id,
                        },
                    )
                    continue
                if turn_id in completed_ids:
                    _dump(
                        CONTROL / "ack.json",
                        {"accepted": False, "reason": "turn already completed"},
                    )
                    continue

                turn_dir = OUT / f"turn_{turn_id}"
                turn_dir.mkdir(parents=True, exist_ok=False)
                before = _authoritative_state()
                _dump(turn_dir / "authoritative_state_before.json", before)
                _dump(turn_dir / "player_input.json", {"turn": turn_id, "text": player_text})
                gen_start = len(generations)
                int_start = len(interpretations)
                pre_start = len(preflights)
                try:
                    response = client.post("/api/chat", json={"text": player_text})
                    payload = response.json()
                    http_status = response.status_code
                except Exception as exc:
                    _dump(
                        turn_dir / "execution_error.json",
                        {
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                            "traceback": traceback.format_exc(),
                        },
                    )
                    turns.append(
                        {
                            "turn": turn_id,
                            "player_input": player_text,
                            "status": "execution_error",
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    completed_ids.add(turn_id)
                    write_manifest("stopped_after_execution_error")
                    exit_code = 1
                    break

                emitted = _gm_text_from_chat_payload(payload) if isinstance(payload, dict) else ""
                resolution, res_meta, gm_meta = _meta(payload if isinstance(payload, dict) else {})
                decision = (
                    res_meta.get("gm_resolution_decision")
                    if isinstance(res_meta.get("gm_resolution_decision"), dict)
                    else {}
                )
                accepted = (
                    gm_meta.get("accepted_response")
                    if isinstance(gm_meta.get("accepted_response"), dict)
                    else {}
                )
                after = _authoritative_state()
                turn_generations = generations[gen_start:]
                turn_interpretations = interpretations[int_start:]
                temporal_after = _provenance_snapshot(after)

                _dump(turn_dir / "api_response.json", payload)
                _dump(turn_dir / "resolution.json", resolution)
                _dump(
                    turn_dir / "gm_output.json",
                    payload.get("gm_output") if isinstance(payload, dict) else {},
                )
                _dump(turn_dir / "generation_calls.json", turn_generations)
                _dump(turn_dir / "interpretation_calls.json", turn_interpretations)
                _dump(turn_dir / "authoritative_state_after.json", after)
                _dump(turn_dir / "temporal_provenance_after.json", temporal_after)
                _dump(
                    turn_dir / "trace_index.json",
                    {
                        "resolution_contract": res_meta.get("resolution_contract"),
                        "interaction_obligation": res_meta.get("interaction_obligation"),
                        "gm_resolution_decision": decision,
                        "epistemic_acts": decision.get("epistemic_acts"),
                        "proposed_facts": decision.get("proposed_facts"),
                        "semantic_identities": [
                            row.get("semantic_identity")
                            for row in (decision.get("proposed_facts") or [])
                            if isinstance(row, dict)
                        ],
                        "raw_initial_generation": (
                            turn_generations[0].get("result") if turn_generations else None
                        ),
                        "raw_retry_generations": [
                            row.get("result")
                            for row in turn_generations
                            if int(row.get("retry_attempt") or 0) > 0
                        ],
                        "narrated_claims_initial": (
                            (gm_meta.get("hard_validation_attempt_1") or {}).get(
                                "gm_resolution_decision_audit"
                            )
                            if isinstance(gm_meta.get("hard_validation_attempt_1"), dict)
                            else None
                        ),
                        "narrated_claims_accepted": (
                            (accepted.get("hard_validation") or {}).get(
                                "gm_resolution_decision_audit"
                            )
                            if isinstance(accepted.get("hard_validation"), dict)
                            else None
                        ),
                        "claim_level_audit": (
                            (accepted.get("hard_validation") or {}).get(
                                "gm_resolution_decision_audit"
                            )
                            if isinstance(accepted.get("hard_validation"), dict)
                            else None
                        ),
                        "residual_claims": (
                            (accepted.get("hard_validation") or {}).get(
                                "gm_resolution_decision_audit"
                            )
                            if isinstance(accepted.get("hard_validation"), dict)
                            else None
                        ),
                        "hard_validation": accepted.get("hard_validation"),
                        "retry_reason": gm_meta.get("regeneration_feedback"),
                        "retry_context_present": any(
                            bool(row.get("prompt", {}).get("contains_authoritative_retry_context"))
                            for row in turn_generations
                        ),
                        "preservation_evidence": {
                            key: value
                            for key, value in gm_meta.items()
                            if "preserv" in key or "fallback" in key
                        },
                        "post_preservation_audit": (
                            accepted.get("hard_validation")
                            if accepted.get("provenance") == "bounded_preservation"
                            else None
                        ),
                        "accepted_response": accepted,
                        "validation_audit": {
                            key: value
                            for key, value in gm_meta.items()
                            if "valid" in key
                            or "audit" in key
                            or "decision_review" in key
                            or "regeneration" in key
                            or "preserv" in key
                            or "fallback" in key
                        },
                        "final_sealed_response": accepted.get("text"),
                        "exact_emitted_response": emitted,
                        "state_after": after,
                        "temporal_provenance_after": temporal_after,
                        "active_claim_after": temporal_after.get(
                            "discourse_focus_active_claim"
                        ),
                    },
                )

                initial_calls = sum(
                    1 for call in turn_generations if int(call.get("retry_attempt") or 0) == 0
                )
                retry_calls = len(turn_generations) - initial_calls
                row = {
                    "turn": turn_id,
                    "http_status": http_status,
                    "player_input": player_text,
                    "emitted_response": emitted,
                    "initial_generation_calls": initial_calls,
                    "retry_generation_calls": retry_calls,
                    "interpretation_calls": len(turn_interpretations),
                    "preflight_calls_during_turn": len(preflights) - pre_start,
                    "contract_id": (res_meta.get("resolution_contract") or {}).get(
                        "contract_id"
                    ),
                    "decision_contract_id": decision.get("contract_id"),
                    "decision_outcome": decision.get("outcome_classification"),
                    "accepted_provenance": accepted.get("provenance"),
                    "accepted_exact_emitted": accepted.get("text") == emitted,
                }
                turns.append(row)
                completed_ids.add(turn_id)
                _dump(turn_dir / "completed.json", row)
                next_status = (
                    "completed_four_turns"
                    if len(turns) == MAX_TURNS
                    else f"waiting_for_turn_{len(turns) + 1}"
                )
                write_manifest(next_status)
                _dump(
                    CONTROL / "ack.json",
                    {
                        "accepted": True,
                        "turn_id": turn_id,
                        "turn_dir": str(turn_dir),
                        "emitted_response": emitted,
                        "next_status": next_status,
                    },
                )
                _dump(
                    ACTIVE,
                    {
                        "stamp": STAMP,
                        "output_dir": str(OUT),
                        "command_path": str(CONTROL / "command.json"),
                        "status": next_status,
                    },
                )
                print(f"DONE TURN {turn_id}", flush=True)
                print(f"PLAYER {player_text}", flush=True)
                print(f"EMIT {emitted}", flush=True)
    finally:
        after_hashes = _production_hashes()
        _dump(OUT / "production_freeze_after.json", after_hashes)
        production_changes = {
            key: {"before": before_hashes.get(key), "after": after_hashes.get(key)}
            for key in sorted(set(before_hashes) | set(after_hashes))
            if before_hashes.get(key) != after_hashes.get(key)
        }
        _dump(OUT / "production_hash_changes_after_live_start.json", production_changes)
        final_status = (
            "completed_four_turns"
            if len(turns) == MAX_TURNS and exit_code == 0
            else "stopped_incomplete"
        )
        write_manifest(final_status)
        _dump(
            ACTIVE,
            {
                "stamp": STAMP,
                "output_dir": str(OUT),
                "status": final_status,
                "gameplay_turns": len(turns),
                "exit_code": exit_code,
            },
        )

    print(json.dumps(json.loads((OUT / "run_manifest.json").read_text()), indent=2))
    print(str(OUT))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
