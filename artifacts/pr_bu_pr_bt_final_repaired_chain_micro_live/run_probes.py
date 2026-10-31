#!/usr/bin/env python3
"""PR-BU / PR-BT final repaired-chain micro-live validation.

Measurement only. Exactly three semantic probes, same fixtures and player
wording as PR-BS, raw PR-BT, and selective PR-BT. No prompt edits, no
validator changes, no retry changes, no repairs, no reruns of a semantic
result, no extra turns. One infrastructure-only rerun is allowed if a probe
fails before a meaningful model generation. Production retries are not
suppressed. A response model other than gpt-4.1-mini-2025-04-14 halts the
run before the next probe.
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent / "evidence"
CALLS: list[dict] = []
CURRENT = {"probe": None, "kind": "other", "retry_attempt": 0}

PROBES = (
    {
        "id": "P1",
        "scene": "chapel",
        "player": (
            "I examine the split wooden yoke and the torn leather hanger closely. "
            "What does this damage suggest?"
        ),
    },
    {
        "id": "P2",
        "scene": "baker",
        "player": "Baker, which loaf do you usually keep for yourself?",
    },
    {
        "id": "P3",
        "scene": "chapel",
        "player": (
            "Looking at the split wooden yoke and the torn leather hanger, "
            "maybe someone cut it deliberately. Does that fit what I'm seeing?"
        ),
    },
)


def save(name: str, value) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def status(text: str) -> None:
    (OUT / "status.txt").write_text(text, encoding="utf-8")
    print(text, flush=True)


import openai.resources.responses as responses_module

Responses = responses_module.Responses
original_create = Responses.create


def _usage(dump: dict) -> dict:
    usage = dump.get("usage") if isinstance(dump, dict) else None
    if not isinstance(usage, dict):
        return {}
    details_in = usage.get("input_tokens_details")
    details_out = usage.get("output_tokens_details")
    return {
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "input_tokens_details": details_in if isinstance(details_in, dict) else details_in,
        "output_tokens_details": details_out if isinstance(details_out, dict) else details_out,
    }


def _extract_request(input_value) -> dict:
    texts: list[str] = []
    roles: list[str] = []
    if isinstance(input_value, list):
        for message in input_value:
            if not isinstance(message, dict):
                continue
            roles.append(str(message.get("role") or ""))
            texts.append(str(message.get("content") or ""))
    elif isinstance(input_value, str):
        texts.append(input_value)
    blob = "\n".join(texts)
    recipe = None
    for text in texts:
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(parsed, dict) and isinstance(parsed.get("decision_facing_answer_recipe"), dict):
            recipe = parsed["decision_facing_answer_recipe"]
            break
    serialized = json.dumps(input_value, ensure_ascii=False, default=str)
    return {
        "roles": roles,
        "input_chars": len(serialized),
        "recipe_present": recipe is not None,
        "recipe": recipe,
        "retry_context_present": "AUTHORITATIVE RETRY CONTEXT" in blob,
        "provider_input": input_value,
    }


def observe_create(self, *args, **kwargs):
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    request = _extract_request(kwargs.get("input"))
    row = {
        "index": len(CALLS) + 1,
        "probe": CURRENT.get("probe"),
        "kind": CURRENT.get("kind"),
        "retry_attempt": kwargs.get("retry_attempt", CURRENT.get("retry_attempt", 0)),
        "model": kwargs.get("model"),
        "started": started_at,
        "input_chars": request["input_chars"],
        "roles": request["roles"],
        "recipe_present": request["recipe_present"],
        "retry_context_present": request["retry_context_present"],
    }
    CALLS.append(row)
    probe = str(CURRENT.get("probe") or "startup")
    attempt = int(row["retry_attempt"] or 0) + 1
    prefix = OUT / probe
    prefix.mkdir(parents=True, exist_ok=True)
    save(
        f"{probe}/provider_request_attempt_{row['kind']}_{attempt}.json",
        {
            "measurements": {k: request[k] for k in ("roles", "input_chars", "recipe_present", "retry_context_present")},
            "decision_facing_answer_recipe": request["recipe"],
            "provider_input": request["provider_input"],
        },
    )
    save("model_calls.json", [{k: v for k, v in call.items() if k != "provider_input"} for call in CALLS])
    try:
        result = original_create(self, *args, **kwargs)
        dump = result.model_dump(mode="json")
        row["raw_output"] = result.output_text
        row["response_id"] = dump.get("id")
        row["response_model"] = dump.get("model")
        row["usage"] = _usage(dump)
        row["status"] = dump.get("status")
        row["meaningful_generation"] = bool(result.output_text) and bool(row["usage"])
        return result
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["meaningful_generation"] = False
        raise
    finally:
        row["finished"] = datetime.now(timezone.utc).isoformat()
        row["latency_seconds"] = round(time.perf_counter() - started, 3)
        save("model_calls.json", [{k: v for k, v in call.items()} for call in CALLS])


Responses.create = observe_create

from fastapi.testclient import TestClient
from game import storage
import game.api as api
import game.semantic_interpreter as interpreter
import game.api_upstream_preflight as preflight
import game.live_resolution as live_resolution
from game.defaults import (
    default_scene,
    default_session,
    default_world,
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
)
from game.gm import _safe_json
from game.gm_resolution_decision import build_decision_facing_answer_recipe


def temporal_slice(session: dict | None) -> dict:
    session = session or {}
    focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
    provenance = session.get("narration_temporal_provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    return {
        "gm_inferences": provenance.get("gm_inferences") or [],
        "player_hypotheses": provenance.get("player_hypotheses") or [],
        "accepted_incidentals": provenance.get("accepted_incidentals") or [],
        "rejected_consequential": provenance.get("rejected_consequential") or [],
        "active_claim": focus.get("active_claim"),
        "discourse_focus": focus,
        "turn_counter": session.get("turn_counter"),
        "active_scene_id": session.get("active_scene_id"),
    }


def scene_slice(scene_doc: dict | None) -> dict:
    scene = (scene_doc or {}).get("scene") if isinstance(scene_doc, dict) else {}
    if not isinstance(scene, dict):
        scene = {}
    return {
        "id": scene.get("id"),
        "location": scene.get("location"),
        "summary": scene.get("summary"),
        "visible_facts": list(scene.get("visible_facts") or []),
        "hidden_facts": list(scene.get("hidden_facts") or []),
        "discoverable_clues": list(scene.get("discoverable_clues") or []),
        "exits": list(scene.get("exits") or []),
        "enemies": list(scene.get("enemies") or []),
        "actions": list(scene.get("actions") or []),
        "interactables": list(scene.get("interactables") or []),
        "addressables": list(scene.get("addressables") or []),
    }


def world_slice(world: dict | None) -> dict:
    world = world or {}
    return {
        "npcs": world.get("npcs") or [],
        "factions": world.get("factions") or [],
        "clues": world.get("clues") or {},
        "world_flags": world.get("world_flags") or [],
        "assets": world.get("assets") or [],
    }


def snapshot() -> dict:
    session = storage.load_session()
    world = storage.load_world()
    scene = storage.load_scene(session["active_scene_id"])
    return {
        "temporal": temporal_slice(session),
        "scene": scene_slice(scene),
        "world": world_slice(world),
    }


def wrap(fn, kind):
    def observed(*args, **kwargs):
        prior = dict(CURRENT)
        CURRENT.update(kind=kind, retry_attempt=kwargs.get("retry_attempt", 0))
        try:
            return fn(*args, **kwargs)
        finally:
            CURRENT.clear()
            CURRENT.update(prior)

    return observed


DECISIONS: list[dict] = []
original_attach = live_resolution.attach_gm_resolution_decision


def observe_decision(resolution, **kwargs):
    result = original_attach(resolution, **kwargs)
    metadata = resolution.get("metadata") if isinstance(resolution, dict) else {}
    contract = metadata.get("resolution_contract") if isinstance(metadata, dict) else {}
    decision = metadata.get("gm_resolution_decision") if isinstance(metadata, dict) else {}
    recipe = build_decision_facing_answer_recipe(
        decision if isinstance(decision, dict) else None,
        contract if isinstance(contract, dict) else None,
    )
    row = {
        "index": len(DECISIONS) + 1,
        "probe": CURRENT.get("probe"),
        "contract": contract if isinstance(contract, dict) else {},
        "decision": decision if isinstance(decision, dict) else {},
        "decision_facing_answer_recipe": recipe,
    }
    DECISIONS.append(row)
    return result


live_resolution.attach_gm_resolution_decision = observe_decision
api.call_gpt = wrap(api.call_gpt, "generation")
interpreter._invoke_interpretation_model = wrap(interpreter._invoke_interpretation_model, "interpretation")
api.run_upstream_api_preflight = wrap(api.run_upstream_api_preflight, "preflight")
preflight.run_upstream_api_preflight = api.run_upstream_api_preflight


def point_storage(probe_id: str) -> None:
    base = OUT / probe_id / "isolated"
    storage.BASE_DIR = base
    storage.DATA_DIR = base / "data"
    storage.SCENES_DIR = storage.DATA_DIR / "scenes"
    for attr, filename in {
        "WORLD_PATH": "world.json",
        "SESSION_PATH": "session.json",
        "CAMPAIGN_PATH": "campaign.json",
        "CHARACTER_PATH": "character.json",
        "COMBAT_PATH": "combat.json",
        "CONDITIONS_PATH": "conditions.json",
        "SESSION_LOG_PATH": "session_log.jsonl",
    }.items():
        setattr(storage, attr, storage.DATA_DIR / filename)
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)


def seed(probe_id: str, scene_kind: str) -> None:
    point_storage(probe_id)
    for base_sid in ("frontier_gate", "market_quarter", "old_milestone"):
        storage._save_json(storage.scene_path(base_sid), default_scene(base_sid))
    if scene_kind == "chapel":
        sid = "chapel_belfry"
        scene = default_scene(sid)
        scene["scene"].update(
            id=sid,
            location="Chapel belfry",
            summary="A bronze bell hangs from a timber frame.",
            visible_facts=[
                "The bell's wooden yoke is split.",
                "The bell's leather hanger is torn.",
            ],
            hidden_facts=[],
            discoverable_clues=[],
            exits=[],
            enemies=[],
            actions=[],
            interactables=[
                {
                    "id": "chapel_bell",
                    "label": "chapel bell",
                    "aliases": ["bell", "wooden yoke", "yoke", "leather hanger", "hanger"],
                }
            ],
        )
        world = default_world()
        world["npcs"] = []
    else:
        sid = "bread_stall"
        scene = default_scene(sid)
        scene["scene"].update(
            id=sid,
            location="Bread stall",
            summary="A baker stands at a bread stall.",
            visible_facts=["A baker stands beside loaves at a bread stall."],
            hidden_facts=[],
            discoverable_clues=[],
            exits=[],
            enemies=[],
            actions=[],
            addressables=[
                {
                    "id": "baker",
                    "name": "Baker",
                    "scene_id": sid,
                    "kind": "npc",
                    "addressable": True,
                    "address_priority": 0,
                    "address_roles": ["baker", "vendor"],
                    "aliases": ["baker"],
                }
            ],
            interactables=[],
        )
        world = default_world()
        world["npcs"] = [
            {
                "id": "baker",
                "name": "Baker",
                "location": sid,
                "topics": [],
            }
        ]
    session = default_session()
    session.update(active_scene_id=sid, visited_scene_ids=[sid], turn_counter=1)
    for path, value in [
        (storage.WORLD_PATH, world),
        (storage.SESSION_PATH, session),
        (storage.CAMPAIGN_PATH, default_campaign()),
        (storage.CHARACTER_PATH, default_character()),
        (storage.COMBAT_PATH, default_combat()),
        (storage.CONDITIONS_PATH, default_conditions()),
        (storage.scene_path(sid), scene),
    ]:
        storage._save_json(path, value)
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _texts_of(rows) -> list[str]:
    found = []
    for row in rows or []:
        if isinstance(row, dict):
            found.append(str(row.get("text") or ""))
        else:
            found.append(str(row))
    return found


def _faction_clock_only(before_rows, after_rows) -> bool:
    """Default world tick adds 1 pressure and 1 agenda_progress. That is not narration leakage."""
    if not isinstance(before_rows, list) or not isinstance(after_rows, list):
        return False
    if len(before_rows) != len(after_rows):
        return False
    for before, after in zip(before_rows, after_rows):
        if not isinstance(before, dict) or not isinstance(after, dict):
            return False
        if before.get("id") != after.get("id"):
            return False
        for key, value in before.items():
            if key in {"pressure", "agenda_progress"}:
                continue
            if after.get(key) != value:
                return False
        try:
            if int(after.get("pressure") or 0) - int(before.get("pressure") or 0) != 1:
                return False
            if int(after.get("agenda_progress") or 0) - int(before.get("agenda_progress") or 0) != 1:
                return False
        except (TypeError, ValueError):
            return False
    return True


def authority_problems(before: dict, after: dict) -> list[str]:
    problems: list[str] = []
    for key in (
        "visible_facts",
        "hidden_facts",
        "discoverable_clues",
        "summary",
        "exits",
        "enemies",
        "actions",
        "interactables",
    ):
        if before["scene"].get(key) != after["scene"].get(key):
            problems.append(f"scene.{key}_changed")
    before_world = dict(before["world"])
    after_world = dict(after["world"])
    if not _faction_clock_only(before_world.get("factions"), after_world.get("factions")):
        if before_world.get("factions") != after_world.get("factions"):
            problems.append("factions_changed_beyond_default_clock")
    before_world.pop("factions", None)
    after_world.pop("factions", None)
    if before_world != after_world:
        problems.append("world_authoritative_slice_changed")
    temporal = after["temporal"]
    visible = " ".join(str(item) for item in after["scene"].get("visible_facts") or [])
    for bucket, banned_status in (
        ("gm_inferences", {"established"}),
        ("player_hypotheses", {"established"}),
    ):
        for row in temporal.get(bucket) or []:
            if not isinstance(row, dict):
                continue
            status_value = str(row.get("epistemic_status") or "")
            authority = str(row.get("authority") or "")
            provenance = str(row.get("provenance") or "")
            if status_value in banned_status or authority == "world_truth" or provenance == "authored_world_fact":
                problems.append(f"{bucket}_promoted:{status_value}:{authority}:{provenance}")
    for row in temporal.get("rejected_consequential") or []:
        text = str(row.get("text") or "").strip() if isinstance(row, dict) else ""
        if text and text in visible:
            problems.append("rejected_consequential_entered_visible_facts")
    return problems


def c18_report(gm: dict) -> dict:
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    accepted = meta.get("accepted_response") if isinstance(meta.get("accepted_response"), dict) else {}
    accepted_text = accepted.get("text")
    emitted = gm.get("player_facing_text")
    debug = meta.get("emission_debug") if isinstance(meta.get("emission_debug"), dict) else {}
    equality = debug.get("accepted_emitted_equality") if isinstance(debug.get("accepted_emitted_equality"), dict) else {}
    exact = accepted_text == emitted and accepted_text is not None
    mutation_blocked = bool(equality.get("mutation_blocked"))
    return {
        "accepted": accepted_text,
        "sealed": accepted_text,
        "emitted": emitted,
        "exact_equal": bool(exact) and not mutation_blocked,
        "string_equal": bool(exact),
        "mutation_blocked": mutation_blocked,
        "equality_debug": equality,
        "provenance": accepted.get("provenance"),
        "attempt": accepted.get("attempt"),
    }


def parse_generation(raw: str) -> dict:
    try:
        parsed = _safe_json(raw or "", require_structured_claims=True)
    except Exception as exc:
        return {"parse_error": f"{type(exc).__name__}: {exc}", "raw_output": raw}
    if not isinstance(parsed, dict):
        return {"parse_error": "non_object", "raw_output": raw}
    return {
        "player_facing_text": parsed.get("player_facing_text"),
        "declared_claims": parsed.get("declared_claims"),
        "tags": parsed.get("tags"),
        "metadata_keys": sorted((parsed.get("metadata") or {}).keys()) if isinstance(parsed.get("metadata"), dict) else [],
        "raw_output": raw,
    }


def compact_call(call: dict) -> dict:
    usage = call.get("usage") or {}
    return {
        "index": call.get("index"),
        "kind": call.get("kind"),
        "retry_attempt": call.get("retry_attempt"),
        "model": call.get("response_model") or call.get("model"),
        "response_id": call.get("response_id"),
        "input_chars": call.get("input_chars"),
        "recipe_present": call.get("recipe_present"),
        "retry_context_present": call.get("retry_context_present"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "latency_seconds": call.get("latency_seconds"),
        "status": call.get("status"),
        "error": call.get("error"),
        "meaningful_generation": call.get("meaningful_generation"),
    }


def run_probe(client: TestClient, spec: dict, *, infrastructure_rerun: bool) -> dict:
    probe_id = spec["id"]
    seed(probe_id, spec["scene"])
    before = snapshot()
    save(f"{probe_id}/state_before.json", before)
    decisions_at = len(DECISIONS)
    calls_at = len(CALLS)
    CURRENT["probe"] = probe_id
    status(f"RUNNING {probe_id}{' infrastructure_rerun' if infrastructure_rerun else ''}")
    error = None
    payload: dict = {}
    http_status = None
    try:
        response = client.post("/api/chat", json={"text": spec["player"]})
        http_status = response.status_code
        payload = response.json()
    except Exception:
        error = traceback.format_exc()
        payload = {}
    after = snapshot()
    calls = CALLS[calls_at:]
    decisions = DECISIONS[decisions_at:]
    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    review = meta.get("decision_review") if isinstance(meta.get("decision_review"), dict) else {}
    c18 = c18_report(gm)
    problems = authority_problems(before, after)
    generations = [call for call in calls if call.get("kind") == "generation"]
    parsed = []
    for index, call in enumerate(generations, start=1):
        parsed_row = parse_generation(str(call.get("raw_output") or ""))
        parsed.append(parsed_row)
        save(
            f"{probe_id}/raw_generation_attempt_{index}.json",
            {
                "response_id": call.get("response_id"),
                "model": call.get("response_model") or call.get("model"),
                "usage": call.get("usage"),
                "latency_seconds": call.get("latency_seconds"),
                "input_chars": call.get("input_chars"),
                "recipe_present": call.get("recipe_present"),
                "retry_context_present": call.get("retry_context_present"),
                "error": call.get("error"),
                "parsed": parsed_row,
            },
        )
    first_decision = decisions[0] if decisions else {}
    recipe = first_decision.get("decision_facing_answer_recipe")
    save(f"{probe_id}/resolution_contract.json", first_decision.get("contract") or {})
    save(f"{probe_id}/gm_resolution_decision.json", first_decision.get("decision") or {})
    save(f"{probe_id}/decision_facing_answer_recipe.json", recipe or {})
    save(f"{probe_id}/state_after.json", after)
    save(f"{probe_id}/api_response.json", payload)
    validation = {
        "attempt_1": review.get("attempt_1"),
        "attempt_2": review.get("attempt_2"),
        "retry_context": review.get("retry_context"),
        "acceptance": review.get("acceptance"),
        "hard_validation_attempt_1": meta.get("hard_validation_attempt_1"),
        "hard_validation_attempt_2": meta.get("hard_validation_attempt_2"),
        "regeneration_feedback": meta.get("regeneration_feedback"),
        "regeneration_invoked": meta.get("regeneration_invoked"),
    }
    save(f"{probe_id}/validation.json", validation)
    save(f"{probe_id}/c18.json", c18)
    upstream = bool((meta.get("upstream_api_error") if isinstance(meta, dict) else None))
    meaningful = any(bool(call.get("meaningful_generation")) for call in generations)
    digest = {
        "probe": probe_id,
        "player": spec["player"],
        "scene": spec["scene"],
        "infrastructure_rerun": infrastructure_rerun,
        "http_status": http_status,
        "error": error,
        "upstream_api_error": meta.get("upstream_api_error") if isinstance(meta, dict) else None,
        "meaningful_model_generation": meaningful and not upstream,
        "emitted": c18["emitted"],
        "sealed": c18["sealed"],
        "accepted": c18["accepted"],
        "c18_exact_equal": c18["exact_equal"],
        "c18_mutation_blocked": c18["mutation_blocked"],
        "provenance": c18["provenance"],
        "attempt": c18["attempt"],
        "acceptance": review.get("acceptance"),
        "initial_player_facing_text": (parsed[0].get("player_facing_text") if parsed else None),
        "initial_declared_claims": (parsed[0].get("declared_claims") if parsed else None),
        "retry_player_facing_text": (parsed[1].get("player_facing_text") if len(parsed) > 1 else None),
        "retry_declared_claims": (parsed[1].get("declared_claims") if len(parsed) > 1 else None),
        "validation_attempt_1_reasons": ((review.get("attempt_1") or {}).get("reasons") if isinstance(review.get("attempt_1"), dict) else None),
        "validation_attempt_2_reasons": ((review.get("attempt_2") or {}).get("reasons") if isinstance(review.get("attempt_2"), dict) else None),
        "authority_problems": problems,
        "temporal_after": after["temporal"],
        "calls": [compact_call(call) for call in calls],
        "contract_id": (first_decision.get("contract") or {}).get("contract_id") if isinstance(first_decision.get("contract"), dict) else None,
        "recipe_schema": (recipe or {}).get("schema") if isinstance(recipe, dict) else None,
        "recipe_requested_answer": (recipe or {}).get("requested_answer") if isinstance(recipe, dict) else None,
        "provider_recipe_present_on_generation": any(bool(call.get("recipe_present")) for call in generations),
    }
    save(f"{probe_id}/digest.json", digest)
    return digest


def _already_recorded(probe_id: str) -> dict | None:
    path = OUT / probe_id / "digest.json"
    if not path.exists():
        return None
    digest = json.loads(path.read_text(encoding="utf-8"))
    if digest.get("meaningful_model_generation") and digest.get("c18_exact_equal") and not digest.get("infrastructure_rerun"):
        return digest
    return None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not (OUT / "run_started.json").exists():
        save(
            "run_started.json",
            {
                "utc": datetime.now(timezone.utc).isoformat(),
                "probes": [row["id"] for row in PROBES],
                "note": "P3 uses a fresh chapel scene with the same authored damage, not carried state from P1.",
            },
        )
    completed: list[dict] = []
    halt = None
    status("STARTING")
    with TestClient(api.app) as client:
        save("preflight.json", preflight.get_latest_upstream_api_preflight())
        for spec in PROBES:
            recorded = _already_recorded(spec["id"])
            if recorded is not None:
                status(f"SKIP {spec['id']} already recorded")
                completed.append(recorded)
                save("completed.json", completed)
                continue
            digest = run_probe(client, spec, infrastructure_rerun=False)
            completed.append(digest)
            save("completed.json", completed)
            if not digest["meaningful_model_generation"]:
                status(f"INFRASTRUCTURE {spec['id']} — one rerun")
                digest = run_probe(client, spec, infrastructure_rerun=True)
                completed.append(digest)
                save("completed.json", completed)
                if not digest["meaningful_model_generation"]:
                    halt = f"infrastructure failure on {spec['id']} after one rerun"
                    break
            models = {
                str(call.get("model") or "")
                for call in digest.get("calls") or []
                if call.get("kind") == "generation" and call.get("model")
            }
            if models and models != {"gpt-4.1-mini-2025-04-14"}:
                halt = f"model snapshot mismatch on {spec['id']}: {sorted(models)}"
                status(f"HALT {halt}")
                break
            if not digest["c18_exact_equal"]:
                halt = f"C18 divergence on {spec['id']}"
                status(f"HALT {halt}")
                break
            if digest["authority_problems"]:
                status(
                    f"AUTHORITY {spec['id']}: {digest['authority_problems']} — recorded, continuing"
                )
            status(f"DONE {spec['id']}")
    save(
        "run_finished.json",
        {
            "halt": halt,
            "probes_recorded": [row["probe"] for row in completed],
            "model_calls": len(CALLS),
        },
    )
    status(f"FINISHED halt={halt}")
    return 0 if halt is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
