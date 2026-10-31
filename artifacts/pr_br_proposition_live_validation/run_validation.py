#!/usr/bin/env python3
"""Six-turn PR-BR proposition-level live validation.

Measurement only. Two fresh three-turn sequences share state within each
sequence. No production edits, turn reruns, or exploratory gameplay calls.
"""
from __future__ import annotations

import hashlib
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
OUT = ROOT / "artifacts" / "pr_br_proposition_live_validation" / STAMP
BASE_SCENES = ("frontier_gate", "market_quarter", "old_milestone")


def _dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


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


def _npc(
    npc_id: str,
    name: str,
    scene_id: str,
    role: str,
    aliases: list[str],
    topic: str,
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
        "topics": [{"id": "work", "text": topic}],
    }


def _scene(
    scene_id: str,
    location: str,
    summary: str,
    visible_facts: list[Any],
    *,
    npcs: list[dict[str, Any]] | None = None,
    mode: str = "exploration",
) -> dict[str, Any]:
    present = npcs or []
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
            "exits": [],
            "enemies": [],
            "actions": [],
            "addressables": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "scene_id": scene_id,
                    "kind": "npc",
                    "addressable": True,
                    "address_priority": 0,
                    "address_roles": [row["role"], *(row.get("aliases") or [])],
                    "aliases": list(row.get("aliases") or []),
                }
                for row in present
            ],
            "interactables": [],
        }
    }


TAVIA = _npc(
    "tavia",
    "Tavia",
    "archive_lift_hall",
    "archive clerk",
    ["clerk", "archive clerk"],
    "Tavia sorts blank record tags at a side desk.",
)

SCENE_A = _scene(
    "observatory_service_room",
    "Rookhaven observatory service room",
    (
        "The roof-hatch mechanism fills one wall. Its brass counterweight lies on the "
        "stone floor, and one link of the hanging chain is snapped. A chalk star chart "
        "rests on a lectern, and a wool cover lies folded over a stool. Nothing states "
        "a cause, actor, time, history, or organization behind the damage."
    ),
    [
        _fact(
            "The roof-hatch counterweight lies on the stone floor, and one link of its hanging chain is snapped.",
            {
                "kind": "world_fact",
                "subject": "roof_hatch_chain",
                "subject_aliases": [
                    "roof-hatch chain",
                    "hatch chain",
                    "chain",
                    "counterweight chain",
                    "counterweight",
                ],
                "relation": "observation",
                "value": "snapped link",
                "value_aliases": ["snapped", "snapped link", "broken link", "counterweight lies"],
                "polarity": "positive",
            },
        ),
        "A chalk star chart rests on a lectern.",
        "A wool cover lies folded over a stool.",
    ],
)

SCENE_B = _scene(
    "archive_lift_hall",
    "Rookhaven civic archive lift hall",
    (
        "A hand-cranked document lift rises through a square shaft beside a courtyard "
        "sundial. The document lift stops running when the courtyard sundial falls "
        "fully into shade. Tavia, an ordinary archive clerk, sorts blank record tags "
        "at a side desk. Nothing states access before or after that condition, who may "
        "use the lift, why the rule exists, or when service resumes."
    ),
    [
        "The document lift stops running when the courtyard sundial falls fully into shade.",
        "Blank record tags are stacked at a side desk.",
        "Tavia sorts the blank record tags.",
    ],
    npcs=[TAVIA],
    mode="social",
)


def _campaign() -> dict[str, Any]:
    value = default_campaign()
    value["premise"] = "Galinor is spending the day in Rookhaven, a town of scholars and civic archives."
    value["starting_context"] = value["premise"]
    value["world_pressures"] = ["Ordinary work and maintenance continue in Rookhaven."]
    value["gm_guidance"] = [
        "Use only the current scene's authored consequential facts as world truth.",
        "People present are ordinary workers unless the scene says otherwise.",
    ]
    value["long_term_goals"] = ["Spend an ordinary day in Rookhaven."]
    return value


def _world(npcs: list[dict[str, Any]]) -> dict[str, Any]:
    value = default_world()
    value["settlements"] = [
        {
            "id": "rookhaven",
            "name": "Rookhaven",
            "type": "scholars_town",
            "tags": ["archive", "observatory"],
            "status": "ordinary",
            "notes": "A town of scholars, instruments, and civic records.",
        }
    ]
    value["factions"] = []
    value["npcs"] = npcs
    value["assets"] = []
    value["projects"] = []
    value["world_flags"] = []
    value["event_log"] = []
    value["clues"] = {}
    value["world_state"] = {"flags": {}, "counters": {}, "clocks": {}}
    return value


def _session(scene_id: str) -> dict[str, Any]:
    value = create_fresh_session_document()
    value["active_scene_id"] = scene_id
    value["visited_scene_ids"] = [scene_id]
    value["scene_state"] = _fresh_scene_state(scene_id)
    value["campaign_started"] = True
    value["turn_counter"] = 0
    value["debug_traces"] = []
    value["chat_history"] = []
    return value


def _seed(sequence: str) -> None:
    scene = SCENE_A if sequence == "A" else SCENE_B
    npcs = [] if sequence == "A" else [TAVIA]
    for scene_id in BASE_SCENES:
        storage._save_json(storage.scene_path(scene_id), default_scene(scene_id))
    storage._save_json(storage.scene_path(scene["scene"]["id"]), scene)
    storage._save_json(storage.CAMPAIGN_PATH, _campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    storage._save_json(storage.WORLD_PATH, _world(npcs))
    storage.save_session(_session(scene["scene"]["id"]))
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


def _a2_from_a1(text: str) -> str:
    lower = text.lower()
    if any(token in lower for token in ("deliberat", "cut ", "tool mark", "tamper")):
        return "So if someone deliberately damaged the chain, who could have reached the roof-hatch mechanism?"
    if any(token in lower for token in ("strain", "wear", "fatigue", "failed", "failure")):
        return "So if unusual strain or wear snapped the chain, who could have put that strain on the roof-hatch mechanism?"
    return "If the damage happened the way you just suggested, who could have caused it?"


def _meta(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
    res_meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    gm_output = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    gm_meta = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
    return resolution, res_meta, gm_meta


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="prbr_prop_live_"))
    _isolate(tmp)
    _seed("A")

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
        result = real_call(messages, **kwargs)
        generations.append(
            {
                "purpose": kwargs.get("purpose"),
                "retry_attempt": kwargs.get("retry_attempt"),
                "retry_reason": kwargs.get("retry_reason"),
                "prompt": _prompt_projection(messages),
                "result": result,
            }
        )
        return result

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
            result = real_preflight(*args, **kwargs)
            row["result"] = result
            return result
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
    _dump(
        OUT / "run_setup.json",
        {
            "stamp": STAMP,
            "head": _git(["rev-parse", "HEAD"]),
            "head_subject": _git(["log", "-1", "--format=%s"]),
            "status_short": _git(["status", "--short"]),
            "isolated_storage": str(tmp),
            "sequence_a_authored_state": SCENE_A,
            "sequence_b_authored_state": SCENE_B,
        },
    )

    rows: list[dict[str, Any]] = []
    a1_emitted = ""
    fixed_turns = [
        ("A", "A1", "I examine the snapped counterweight chain and the roof-hatch mechanism. What does the damage suggest?"),
        ("A", "A2", None),
        ("A", "A3", "Do we actually know that, or is that only a possibility? What does the observation establish, and what remains unknown?"),
        ("B", "B1", "When does the archive's document lift stop running?"),
        ("B", "B2", "So can visitors still send records up before the sundial is fully in shade?"),
        (
            "B",
            "B3",
            "All right—so whether visitors may use it before then still isn't settled. I ask Tavia what she's tying those blank tags with and whether her fingers are sore from the work.",
        ),
    ]

    with TestClient(app) as client:
        active_sequence = ""
        for sequence, label, fixed_text in fixed_turns:
            if sequence != active_sequence:
                _seed(sequence)
                active_sequence = sequence
                _dump(OUT / f"sequence_{sequence}_initial_state.json", _authoritative_state())
            player_text = fixed_text if fixed_text is not None else _a2_from_a1(a1_emitted)
            turn_dir = OUT / f"turn_{label}"
            turn_dir.mkdir(parents=True, exist_ok=True)
            before = _authoritative_state()
            _dump(turn_dir / "authoritative_state_before.json", before)
            _dump(turn_dir / "player_input.json", {"sequence": sequence, "turn": label, "text": player_text})
            gen_start = len(generations)
            int_start = len(interpretations)
            pre_start = len(preflights)
            try:
                response = client.post("/api/chat", json={"text": player_text})
                payload = response.json()
                status = response.status_code
            except Exception as exc:
                _dump(
                    turn_dir / "execution_error.json",
                    {"error_type": type(exc).__name__, "traceback": traceback.format_exc()},
                )
                rows.append({"turn": label, "status": "execution_error", "error": str(exc)})
                print(f"ERROR {label}: {type(exc).__name__}: {exc}", flush=True)
                continue

            emitted = _gm_text_from_chat_payload(payload) if isinstance(payload, dict) else ""
            if label == "A1":
                a1_emitted = emitted
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
            _dump(turn_dir / "api_response.json", payload)
            _dump(turn_dir / "resolution.json", resolution)
            _dump(turn_dir / "gm_output.json", payload.get("gm_output") if isinstance(payload, dict) else {})
            _dump(turn_dir / "generation_calls.json", turn_generations)
            _dump(turn_dir / "interpretation_calls.json", turn_interpretations)
            _dump(turn_dir / "authoritative_state_after.json", after)
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
                    "claim_level_authority_results": (
                        (accepted.get("hard_validation") or {}).get("authority")
                        if isinstance(accepted.get("hard_validation"), dict)
                        else None
                    ),
                    "authorized_coverage": (
                        (gm_meta.get("emission_debug") or {}).get("best_safe_coverage")
                        if isinstance(gm_meta.get("emission_debug"), dict)
                        else None
                    ),
                    "consequential_residuals": (
                        (accepted.get("hard_validation") or {}).get("gm_resolution_decision_audit")
                        if isinstance(accepted.get("hard_validation"), dict)
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
                    "temporal_provenance_after": (
                        (after.get("session") or {}).get("narration_temporal_provenance")
                    ),
                    "bounded_improvisation_after": (
                        (after.get("session") or {}).get("bounded_improvisation")
                    ),
                },
            )
            initial_calls = sum(
                1 for call in turn_generations if int(call.get("retry_attempt") or 0) == 0
            )
            retry_calls = len(turn_generations) - initial_calls
            row = {
                "turn": label,
                "sequence": sequence,
                "http_status": status,
                "player_input": player_text,
                "emitted_response": emitted,
                "initial_generation_calls": initial_calls,
                "retry_generation_calls": retry_calls,
                "interpretation_calls": len(turn_interpretations),
                "preflight_calls_during_turn": len(preflights) - pre_start,
                "contract_id": (res_meta.get("resolution_contract") or {}).get("contract_id"),
                "decision_contract_id": decision.get("contract_id"),
                "decision_outcome": decision.get("outcome_classification"),
                "accepted_provenance": accepted.get("provenance"),
                "accepted_exact_emitted": accepted.get("text") == emitted,
            }
            rows.append(row)
            print(
                f"DONE {label} initial={initial_calls} retries={retry_calls} "
                f"interpretations={len(turn_interpretations)}",
                flush=True,
            )
            print(f"PLAYER {player_text}", flush=True)
            print(f"EMIT {emitted}", flush=True)

    after_hashes = _production_hashes()
    _dump(OUT / "production_freeze_after.json", after_hashes)
    production_changes = {
        key: {"before": before_hashes.get(key), "after": after_hashes.get(key)}
        for key in sorted(set(before_hashes) | set(after_hashes))
        if before_hashes.get(key) != after_hashes.get(key)
    }
    initial_count = sum(1 for call in generations if int(call.get("retry_attempt") or 0) == 0)
    retry_count = len(generations) - initial_count
    other_calls = 0
    manifest = {
        "stamp": STAMP,
        "head": _git(["rev-parse", "HEAD"]),
        "gameplay_turns": len(rows),
        "successful_http_turns": sum(1 for row in rows if row.get("http_status") == 200),
        "initial_generation_calls": initial_count,
        "retry_generation_calls": retry_count,
        "interpretation_calls": len(interpretations),
        "preflight_calls": len(preflights),
        "other_model_calls": other_calls,
        "total_model_api_calls": len(generations) + len(interpretations) + len(preflights) + other_calls,
        "production_hash_changes_after_live_start": production_changes,
        "turns": rows,
        "no_reruns": True,
    }
    _dump(OUT / "generation_calls.json", generations)
    _dump(OUT / "interpretation_calls.json", interpretations)
    _dump(OUT / "preflight_calls.json", preflights)
    _dump(OUT / "run_manifest.json", manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False), flush=True)
    print(str(OUT), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
