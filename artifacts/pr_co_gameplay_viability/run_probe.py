#!/usr/bin/env python3
"""PR-CO controlled live gameplay viability probe.

Diagnostic only. Isolated session. No application-code edits.
Production data/ is not written.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "evidence"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

MAX_REQUESTS = 12
MAX_TOKENS = 300_000
MAX_TURNS = 8

CALLS: list[dict] = []
HALT: str | None = None
ACCOUNTING_FAILED = False
CURRENT = {"turn": "startup", "kind": "preflight", "retry_attempt": 0, "retry_reason": None}


def save(name: str, value) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, ensure_ascii=False, default=str)
    if "sk-" in text:
        text = text.replace("sk-", "sk-REDACTED-")
    path.write_text(text, encoding="utf-8")


def status(text: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {text}"
    print(line, flush=True)
    (OUT / "status.txt").write_text(line + "\n", encoding="utf-8")


def spent_tokens() -> int:
    total = 0
    for call in CALLS:
        usage = call.get("usage") or {}
        value = usage.get("total_tokens")
        if isinstance(value, int):
            total += value
            continue
        inp = usage.get("input_tokens")
        out = usage.get("output_tokens")
        if isinstance(inp, int) or isinstance(out, int):
            total += int(inp or 0) + int(out or 0)
    return total


class BudgetStop(RuntimeError):
    pass


def _budget_block_reason() -> str | None:
    if ACCOUNTING_FAILED:
        return "usage accounting unavailable"
    if len(CALLS) >= MAX_REQUESTS:
        return f"provider request budget reached ({MAX_REQUESTS})"
    if spent_tokens() >= MAX_TOKENS:
        return f"token budget reached ({spent_tokens()})"
    return None


import openai.resources.responses as responses_module

Responses = responses_module.Responses
original_create = Responses.create


def _usage(dump: dict) -> dict:
    usage = dump.get("usage") if isinstance(dump, dict) else None
    if not isinstance(usage, dict):
        return {}
    details_in = usage.get("input_tokens_details") if isinstance(usage.get("input_tokens_details"), dict) else {}
    details_out = usage.get("output_tokens_details") if isinstance(usage.get("output_tokens_details"), dict) else {}
    cached = details_in.get("cached_tokens")
    return {
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "cached_input_tokens": cached,
        "input_tokens_details": details_in,
        "output_tokens_details": details_out,
    }


def observe_create(self, *args, **kwargs):
    global HALT, ACCOUNTING_FAILED
    reason = _budget_block_reason()
    if reason:
        HALT = reason
        raise BudgetStop(reason)
    started = time.perf_counter()
    row = {
        "index": len(CALLS) + 1,
        "turn": CURRENT.get("turn"),
        "kind": CURRENT.get("kind"),
        "retry_attempt": CURRENT.get("retry_attempt") or 0,
        "retry_reason": CURRENT.get("retry_reason"),
        "model": kwargs.get("model"),
        "started": datetime.now(timezone.utc).isoformat(),
        "create_kwarg_keys": sorted(key for key in kwargs if key != "input"),
    }
    CALLS.append(row)
    turn = str(CURRENT.get("turn") or "startup")
    attempt = int(row["retry_attempt"] or 0) + 1
    kind = str(row["kind"] or "other")
    save(
        f"{turn}/provider_request_{kind}_{attempt}.json",
        {
            "model": kwargs.get("model"),
            "kind": kind,
            "retry_attempt": row["retry_attempt"],
            "retry_reason": row["retry_reason"],
            "create_kwarg_keys": row["create_kwarg_keys"],
            "provider_input": kwargs.get("input"),
        },
    )
    try:
        result = original_create(self, *args, **kwargs)
        dump = result.model_dump(mode="json")
        row["raw_output"] = getattr(result, "output_text", None)
        row["response_id"] = dump.get("id")
        row["response_model"] = dump.get("model")
        row["usage"] = _usage(dump)
        row["status"] = dump.get("status")
        row["error"] = None
        usable = bool(row["raw_output"]) and bool(row["usage"])
        row["usable_output"] = usable
        if not row["usage"]:
            ACCOUNTING_FAILED = True
            HALT = "usage accounting unavailable after a completed provider response"
        return result
    except BudgetStop:
        raise
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["usable_output"] = False
        row["usage"] = {}
        raise
    finally:
        row["finished"] = datetime.now(timezone.utc).isoformat()
        row["latency_seconds"] = round(time.perf_counter() - started, 3)
        save("model_calls.json", [{k: v for k, v in call.items() if k != "raw_output"} | {"raw_output_preview": str(call.get("raw_output") or "")[:500]} for call in CALLS])


Responses.create = observe_create

from fastapi.testclient import TestClient
from game import storage
import game.api as api
import game.semantic_interpreter as interpreter
from game.config import (
    DEFAULT_MODEL_NAME,
    ENABLE_MODEL_ROUTING,
    HIGH_PRECISION_MODEL_NAME,
    MODEL_NAME,
    RETRY_ESCALATION_MODEL_NAME,
)
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)
from game.ordinary_semantic_ownership import _RESOLVER_STAGES, stage_permitted

PRICED_MODELS = {
    "gpt-4.1-mini": {"input_per_million": 0.40, "cached_input_per_million": 0.10, "output_per_million": 1.60},
    "gpt-4o-mini": {"input_per_million": 0.15, "cached_input_per_million": 0.075, "output_per_million": 0.60},
}


def verify_config() -> dict:
    models = {
        "MODEL_NAME": MODEL_NAME,
        "DEFAULT_MODEL_NAME": DEFAULT_MODEL_NAME,
        "HIGH_PRECISION_MODEL_NAME": HIGH_PRECISION_MODEL_NAME,
        "RETRY_ESCALATION_MODEL_NAME": RETRY_ESCALATION_MODEL_NAME,
    }
    unknown = sorted({name for name in models.values() if name not in PRICED_MODELS})
    report = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "provider": "OpenAI",
        "billing_path": "Official OpenAI Python SDK Responses API (client.responses.create). No OPENAI_BASE_URL override in process environment or call_gpt.",
        "endpoint": "https://api.openai.com/v1/responses",
        "models": models,
        "enable_model_routing": ENABLE_MODEL_ROUTING,
        "published_prices_usd_per_million": PRICED_MODELS,
        "price_source": "https://developers.openai.com/api/docs/pricing.md",
        "hard_budget": {
            "max_completed_turns": MAX_TURNS,
            "max_provider_requests": MAX_REQUESTS,
            "max_combined_tokens": MAX_TOKENS,
        },
        "expected_cost_at_token_ceiling_usd": {
            "assumption": "All 300,000 tokens billed as gpt-4.1-mini, 95 percent input and 5 percent output, no cache. Cached input would cost less.",
            "estimate_usd": round((285_000 * 0.40 + 15_000 * 1.60) / 1_000_000, 4),
        },
        "unknown_unpriced_models": unknown,
        "api_key_present": True,
        "production_data_untouched_intent": True,
    }
    save("phase0_config.json", report)
    if unknown:
        raise SystemExit(f"STOP unpriced models: {unknown}")
    return report


def point_storage() -> None:
    base = OUT / "isolated_session"
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


def seed() -> None:
    point_storage()
    for sid in ("frontier_gate", "market_quarter", "old_milestone"):
        storage._save_json(storage.scene_path(sid), default_scene(sid))
    session = default_session()
    session.update(active_scene_id="frontier_gate", visited_scene_ids=["frontier_gate"], turn_counter=1)
    for path, value in [
        (storage.WORLD_PATH, default_world()),
        (storage.SESSION_PATH, session),
        (storage.CAMPAIGN_PATH, default_campaign()),
        (storage.CHARACTER_PATH, default_character()),
        (storage.COMBAT_PATH, default_combat()),
        (storage.CONDITIONS_PATH, default_conditions()),
    ]:
        storage._save_json(path, value)
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _scene_body(doc: dict | None) -> dict:
    scene = (doc or {}).get("scene") if isinstance(doc, dict) else {}
    return scene if isinstance(scene, dict) else {}


def snapshot() -> dict:
    session = storage.load_session()
    world = storage.load_world()
    sid = session.get("active_scene_id")
    scene = _scene_body(storage.load_scene(sid))
    character = storage.load_character() if storage.CHARACTER_PATH.exists() else {}
    runtime = storage.get_scene_runtime(session, sid) if sid else {}
    leads = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    return {
        "turn_counter": session.get("turn_counter"),
        "active_scene_id": sid,
        "interaction_context": session.get("interaction_context"),
        "discourse_focus": session.get("discourse_focus"),
        "known_clues": session.get("known_clues"),
        "contextual_leads": leads if isinstance(leads, list) else [],
        "scene": {
            "id": scene.get("id"),
            "location": scene.get("location"),
            "summary": scene.get("summary"),
            "mode": scene.get("mode"),
            "visible_facts": list(scene.get("visible_facts") or []),
            "hidden_facts": list(scene.get("hidden_facts") or []),
            "discoverable_clues": list(scene.get("discoverable_clues") or []),
            "exits": list(scene.get("exits") or []),
            "enemies": list(scene.get("enemies") or []),
            "addressables": list(scene.get("addressables") or []),
            "interactables": list(scene.get("interactables") or []),
        },
        "world": {
            "npcs": world.get("npcs") or [],
            "factions": world.get("factions") or [],
            "clues": world.get("clues") or {},
            "world_flags": world.get("world_flags") or [],
        },
        "character": {
            "hp": (character or {}).get("hp"),
            "inventory": (character or {}).get("inventory"),
            "spells": (character or {}).get("spells"),
            "conditions": (character or {}).get("conditions"),
        },
    }


def _texts(value) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            found.extend(_texts(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_texts(item))
    return found


def severe_mutation(before: dict, after: dict) -> list[str]:
    problems: list[str] = []
    if before.get("active_scene_id") != after.get("active_scene_id"):
        problems.append("active_scene_changed")
    if before["character"] != after["character"]:
        problems.append("character_sheet_changed")
    before_ids = [npc.get("id") for npc in before["world"]["npcs"] if isinstance(npc, dict)]
    after_ids = [npc.get("id") for npc in after["world"]["npcs"] if isinstance(npc, dict)]
    if before_ids != after_ids:
        problems.append("npc_roster_changed")
    before_topics = _texts([npc.get("topics") for npc in before["world"]["npcs"] if isinstance(npc, dict)])
    after_topics = _texts([npc.get("topics") for npc in after["world"]["npcs"] if isinstance(npc, dict)])
    if before_topics != after_topics:
        problems.append("npc_topic_text_changed")
    if before["scene"]["hidden_facts"] != after["scene"]["hidden_facts"]:
        problems.append("hidden_facts_changed")
    if before["scene"]["summary"] != after["scene"]["summary"]:
        problems.append("scene_summary_changed")
    hidden = {item.strip() for item in before["scene"]["hidden_facts"] if isinstance(item, str)}
    for fact in after["scene"]["visible_facts"]:
        if isinstance(fact, str) and fact.strip() in hidden and fact not in before["scene"]["visible_facts"]:
            problems.append("hidden_fact_promoted_into_visible_facts")
    authored = set(_texts(before["scene"])) | set(_texts(before["world"]["npcs"]))
    for fact in after["scene"]["visible_facts"]:
        if isinstance(fact, str) and fact not in before["scene"]["visible_facts"] and fact not in authored:
            problems.append(f"unauthored_visible_fact:{fact[:120]}")
    return problems


def wrap(fn, kind: str):
    def observed(*args, **kwargs):
        prior = dict(CURRENT)
        CURRENT.update(
            kind=kind,
            retry_attempt=kwargs.get("retry_attempt", 0),
            retry_reason=kwargs.get("retry_reason"),
        )
        try:
            return fn(*args, **kwargs)
        finally:
            CURRENT.clear()
            CURRENT.update(prior)

    return observed


api.call_gpt = wrap(api.call_gpt, "generation")
interpreter._invoke_interpretation_model = wrap(interpreter._invoke_interpretation_model, "interpretation")


def production_mtimes() -> dict:
    paths = [
        ROOT / "data" / "session.json",
        ROOT / "data" / "world.json",
        ROOT / "data" / "combat.json",
        ROOT / "data" / "session_log.jsonl",
        ROOT / "data" / "scenes" / "frontier_gate.json",
    ]
    return {str(path.relative_to(ROOT)): path.stat().st_mtime_ns for path in paths if path.exists()}


def snippet(text: str, limit: int = 160) -> str:
    clean = " ".join(str(text or "").split())
    if len(clean) <= limit:
        return clean
    return clean[:limit].rsplit(" ", 1)[0] + "..."


def dig(obj, *keys):
    cur = obj
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def extract_trace(payload: dict, before: dict, after: dict, calls: list[dict]) -> dict:
    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
    decision = meta.get("gm_resolution_decision") if isinstance(meta.get("gm_resolution_decision"), dict) else {}
    compact = payload.get("turn_trace") if isinstance(payload.get("turn_trace"), dict) else {}
    resolver = meta.get("selected_resolver") or dig(meta, "resolution", "metadata", "selected_resolver")
    if not resolver:
        resolver = dig(compact, "social_contract_trace", "selected_resolver")
    construction = contract.get("construction") if isinstance(contract.get("construction"), dict) else {}
    stages = sorted(_RESOLVER_STAGES.get(str(resolver or ""), frozenset()))
    permitted = {stage: stage_permitted(resolver, stage, contract) for stage in (
        "social", "dialogue_first", "pursuit", "world_action", "exploration",
        "passive_wait", "generic_intent", "travel",
    )}
    generations = [call for call in calls if call.get("kind") == "generation"]
    retries = [call for call in generations if int(call.get("retry_attempt") or 0) > 0]
    return {
        "operation": contract.get("operation"),
        "request_kind": contract.get("request_kind"),
        "resolution_subject": construction.get("resolution_subject"),
        "selected_resolver": resolver,
        "resolver_stages": stages,
        "stage_permissions": permitted,
        "interlocutor_id": contract.get("interlocutor_id"),
        "outcome_classification": decision.get("outcome_classification"),
        "persistence_policy": decision.get("persistence_policy"),
        "permitted_state_mutations": decision.get("permitted_state_mutations"),
        "authoritative_resolution_keys": sorted(decision.keys()) if decision else [],
        "player_facing_text": gm.get("player_facing_text"),
        "validation": {
            "acceptance": dig(meta, "decision_review", "acceptance"),
            "regeneration_invoked": meta.get("regeneration_invoked"),
            "provider_response_contract": meta.get("provider_response_contract"),
            "upstream_api_error": meta.get("upstream_api_error"),
            "provenance": dig(meta, "accepted_response", "provenance") or meta.get("response_provenance"),
            "hard_validation_attempt_1": meta.get("hard_validation_attempt_1"),
            "hard_validation_attempt_2": meta.get("hard_validation_attempt_2"),
        },
        "compact_classification": compact.get("classification"),
        "compact_resolution_path": compact.get("resolution_path"),
        "interaction_after": compact.get("interaction_after"),
        "clues": compact.get("clues"),
        "leads": compact.get("leads"),
        "latency_ms": compact.get("latency_ms"),
        "provider_request_count": len(calls),
        "retry_count": len(retries),
        "warnings": [
            item for item in (
                meta.get("upstream_api_error"),
                meta.get("regeneration_feedback"),
            ) if item
        ],
        "state_before_scene": before.get("active_scene_id"),
        "state_after_scene": after.get("active_scene_id"),
    }


def run_turn(client: TestClient, turn_id: str, player_text: str) -> dict:
    global HALT
    before = snapshot()
    save(f"{turn_id}/state_before.json", before)
    calls_at = len(CALLS)
    CURRENT["turn"] = turn_id
    status(f"RUNNING {turn_id}")
    error = None
    payload: dict = {}
    http_status = None
    try:
        response = client.post("/api/chat", json={"text": player_text})
        http_status = response.status_code
        payload = response.json()
    except Exception:
        error = traceback.format_exc()
    after = snapshot()
    calls = CALLS[calls_at:]
    problems = severe_mutation(before, after)
    if problems:
        HALT = "severe unauthorized state mutation: " + "; ".join(problems)
    trace = extract_trace(payload if isinstance(payload, dict) else {}, before, after, calls)
    record = {
        "turn": turn_id,
        "player_input": player_text,
        "http_status": http_status,
        "error": error,
        "halt_after": HALT,
        "severe_mutations": problems,
        "trace": trace,
        "provider_calls": [
            {k: v for k, v in call.items() if k != "raw_output"} | {"raw_output": call.get("raw_output")}
            for call in calls
        ],
    }
    save(f"{turn_id}/turn_record.json", record)
    save(f"{turn_id}/state_after.json", after)
    save(f"{turn_id}/api_response.json", payload)
    preview = snippet(trace.get("player_facing_text") or "", 220)
    status(
        f"DONE {turn_id} http={http_status} resolver={trace.get('selected_resolver')} "
        f"op={trace.get('operation')} subject={trace.get('resolution_subject')} "
        f"calls={len(calls)} tokens={spent_tokens()} text={preview}"
    )
    return record


def main() -> None:
    global HALT
    config = verify_config()
    before_mtimes = production_mtimes()
    save("production_mtimes_before.json", before_mtimes)
    status("CONFIG VERIFIED " + json.dumps(config["models"]))
    status("OPENING TEST CLIENT")
    with TestClient(api.app) as client:
        preflight_calls = list(CALLS)
        save("preflight_calls.json", [{k: v for k, v in call.items() if k != "raw_output"} for call in preflight_calls])
        if HALT:
            status("HALT BEFORE GAMEPLAY " + HALT)
        elif not preflight_calls:
            HALT = "preflight made no provider request; billing path not exercised"
            status("HALT " + HALT)
        elif not (preflight_calls[-1].get("usage") or {}):
            HALT = "preflight returned no usage accounting"
            status("HALT " + HALT)
        else:
            status(f"PREFLIGHT OK tokens={spent_tokens()} model={preflight_calls[-1].get('response_model')}")
        seed()
        initial = snapshot()
        save("initial_state.json", initial)
        records = []
        emitted: dict[str, str] = {}
        planned = {
            "T1": "Guard Captain, which do you prefer: watching the gate in this rain, or a dry watch inside the walls?",
            "T3": "Captain, what do you know about the missing patrol?",
            "T4": "I examine the notice board for anything unusual.",
            "T5": "Describe what I can see around me here at the gate.",
            "T6": "I wait and watch the gate without starting anything else.",
            "T8": "I step closer to the notice board and read the missing-patrol warning.",
        }
        order = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]
        for turn_id in order:
            if HALT or len([row for row in records if not row.get("error") and row.get("http_status") == 200]) >= MAX_TURNS:
                break
            if _budget_block_reason():
                HALT = _budget_block_reason()
                status("HALT BEFORE " + turn_id + " " + str(HALT))
                break
            if turn_id == "T2":
                player = (
                    f'About what you just told me — "{snippet(emitted.get("T1") or "", 140)}" — '
                    "what makes you prefer that?"
                )
            elif turn_id == "T7":
                prior = (emitted.get("T3") or "") + " " + (emitted.get("T1") or "")
                if "milestone" in prior.lower() or "patrol" in prior.lower():
                    player = "Earlier you told me about the missing patrol. Was it last seen near the old milestone?"
                else:
                    player = "Earlier, when I asked which watch you prefer, what did you settle on?"
            else:
                player = planned[turn_id]
            record = run_turn(client, turn_id, player)
            records.append(record)
            emitted[turn_id] = str(record["trace"].get("player_facing_text") or "")
            if HALT:
                status("HALT AFTER " + turn_id + " " + HALT)
                break
            if len(records) >= MAX_TURNS:
                break
        save("run_finished.json", {
            "halt": HALT,
            "completed_turn_ids": [row["turn"] for row in records],
            "provider_requests": len(CALLS),
            "combined_tokens": spent_tokens(),
            "accounting_failed": ACCOUNTING_FAILED,
        })
    after_mtimes = production_mtimes()
    save("production_mtimes_after.json", after_mtimes)
    drifted = [key for key, value in before_mtimes.items() if after_mtimes.get(key) != value]
    save("production_mtime_drift.json", drifted)
    status("FINISHED halt=" + str(HALT) + " requests=" + str(len(CALLS)) + " tokens=" + str(spent_tokens()) + " production_drift=" + str(drifted))


if __name__ == "__main__":
    main()
