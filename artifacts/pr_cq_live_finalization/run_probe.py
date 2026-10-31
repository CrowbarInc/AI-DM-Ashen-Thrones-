#!/usr/bin/env python3
"""PR-CQ minimal live finalization verification.

Diagnostic only. Isolated disposable session. No application-code edits.
Production data/ is not the storage target.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "evidence"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

MAX_REQUESTS = 4
MAX_TOKENS = 120_000
MAX_TURNS = 2
REQUIRED_RESPONSE_MODEL = "gpt-4.1-mini-2025-04-14"
ALLOWED_REQUEST_MODELS = {"gpt-4.1-mini", REQUIRED_RESPONSE_MODEL}

CALLS: list[dict] = []
HALT: str | None = None
ACCOUNTING_FAILED = False
CURRENT = {"turn": "startup", "kind": "preflight", "retry_attempt": 0, "retry_reason": None}

_SECRET = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")


def redact(text: str) -> str:
    return _SECRET.sub("sk-REDACTED", text)


def save(name: str, value) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, ensure_ascii=False, default=str)
    path.write_text(redact(text), encoding="utf-8")


def status(text: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {text}"
    print(line, flush=True)
    with (OUT / "status.txt").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


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


class BudgetStop(BaseException):
    """Not an Exception, so call_gpt and the interpreter cannot swallow it."""


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


def _narration_from_raw(raw) -> str:
    text = str(raw or "")
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text
    if isinstance(data, dict):
        for key in ("narration", "player_facing_text", "text"):
            if isinstance(data.get(key), str) and data.get(key).strip():
                return data[key]
    return text


def observe_create(self, *args, **kwargs):
    global HALT, ACCOUNTING_FAILED
    reason = _budget_block_reason()
    requested = str(kwargs.get("model") or "")
    if requested and requested not in ALLOWED_REQUEST_MODELS:
        reason = f"refusing model substitution: requested {requested}"
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
        row["parsed_narration"] = _narration_from_raw(row["raw_output"])
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
        elif str(row["response_model"] or "") != REQUIRED_RESPONSE_MODEL:
            HALT = f"response model {row['response_model']!r} is not {REQUIRED_RESPONSE_MODEL}"
        return result
    except BudgetStop:
        raise
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["usable_output"] = False
        row["usage"] = {}
        row["raw_output"] = None
        row["parsed_narration"] = ""
        raise
    finally:
        row["finished"] = datetime.now(timezone.utc).isoformat()
        row["latency_seconds"] = round(time.perf_counter() - started, 3)
        save(
            "model_calls.json",
            [
                {k: v for k, v in call.items() if k != "raw_output"}
                | {"raw_output": call.get("raw_output"), "parsed_narration": call.get("parsed_narration")}
                for call in CALLS
            ],
        )


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
    get_openai_api_key,
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

PRICED = {
    "input_per_million": 0.40,
    "cached_input_per_million": 0.10,
    "output_per_million": 1.60,
}


def verify_config() -> dict:
    key = get_openai_api_key() or ""
    models = {
        "MODEL_NAME": MODEL_NAME,
        "DEFAULT_MODEL_NAME": DEFAULT_MODEL_NAME,
        "HIGH_PRECISION_MODEL_NAME": HIGH_PRECISION_MODEL_NAME,
        "RETRY_ESCALATION_MODEL_NAME": RETRY_ESCALATION_MODEL_NAME,
    }
    unknown = sorted({name for name in models.values() if name not in ALLOWED_REQUEST_MODELS})
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE") or ""
    ceiling_input = int(MAX_TOKENS * 0.95)
    ceiling_output = MAX_TOKENS - ceiling_input
    report = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "provider": "OpenAI",
        "billing_path": "Official OpenAI Python SDK Responses API (client.responses.create).",
        "endpoint": "https://api.openai.com/v1/responses" if not base_url else base_url,
        "base_url_override_present": bool(base_url),
        "models": models,
        "enable_model_routing": ENABLE_MODEL_ROUTING,
        "required_response_model": REQUIRED_RESPONSE_MODEL,
        "published_prices_usd_per_million": PRICED,
        "price_source": "https://developers.openai.com/api/docs/pricing (same published gpt-4.1-mini rates used by PR-CO)",
        "hard_budget": {
            "max_completed_gameplay_turns": MAX_TURNS,
            "max_provider_requests_including_preflight": MAX_REQUESTS,
            "max_combined_tokens": MAX_TOKENS,
        },
        "expected_cost_at_token_ceiling_usd": {
            "assumption": "120,000 tokens as gpt-4.1-mini, 95 percent input and 5 percent output, no cache.",
            "estimate_usd": round((ceiling_input * PRICED["input_per_million"] + ceiling_output * PRICED["output_per_million"]) / 1_000_000, 4),
            "all_output_ceiling_usd": round(MAX_TOKENS * PRICED["output_per_million"] / 1_000_000, 4),
        },
        "unknown_unpriced_or_substituted_models": unknown,
        "api_key_present": bool(key.startswith("sk-")),
        "api_key_length": len(key),
        "production_data_untouched_intent": True,
    }
    save("phase0_config.json", report)
    if unknown or base_url or not report["api_key_present"]:
        raise SystemExit(
            "STOP config: "
            + json.dumps(
                {
                    "unknown_models": unknown,
                    "base_url_override": bool(base_url),
                    "api_key_present": report["api_key_present"],
                }
            )
        )
    if MODEL_NAME != "gpt-4.1-mini":
        raise SystemExit(f"STOP model is {MODEL_NAME}, required gpt-4.1-mini")
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
    npc_runtime = session.get("npc_runtime") if isinstance(session.get("npc_runtime"), dict) else {}
    return {
        "turn_counter": session.get("turn_counter"),
        "active_scene_id": sid,
        "interaction_context": session.get("interaction_context"),
        "discourse_focus": session.get("discourse_focus"),
        "known_clues": session.get("known_clues"),
        "npc_runtime": npc_runtime,
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
            "name": (character or {}).get("name"),
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


def dig(obj, *keys):
    cur = obj
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _find_values(obj, key: str, limit: int = 6) -> list:
    found = []

    def walk(node, path: str) -> None:
        if len(found) >= limit:
            return
        if isinstance(node, dict):
            if key in node:
                found.append({"path": path + "." + key, "value": node[key]})
            for child_key, child in node.items():
                if child_key in {"provider_input", "messages"}:
                    continue
                walk(child, path + "." + str(child_key))
        elif isinstance(node, list):
            for index, child in enumerate(node[:40]):
                walk(child, f"{path}[{index}]")

    walk(obj, "")
    return found


def _validation_slice(meta: dict) -> dict:
    review = meta.get("decision_review") if isinstance(meta.get("decision_review"), dict) else {}
    accepted = meta.get("accepted_response") if isinstance(meta.get("accepted_response"), dict) else {}

    def attempt(name: str) -> dict | None:
        row = meta.get(name)
        if not isinstance(row, dict) and isinstance(review.get(name.replace("hard_validation_", "")), dict):
            row = review.get(name.replace("hard_validation_", ""))
        if not isinstance(row, dict):
            return None
        audit = row.get("gm_resolution_decision_audit")
        violations = []
        if isinstance(audit, dict):
            raw = audit.get("violations")
            if isinstance(raw, list):
                for item in raw[:12]:
                    if isinstance(item, dict):
                        violations.append(
                            {
                                "code": item.get("code") or item.get("pattern") or item.get("reason_code"),
                                "reason": item.get("reason") or item.get("message"),
                                "text": str(item.get("text") or item.get("claim") or "")[:400],
                            }
                        )
                    else:
                        violations.append({"text": str(item)[:400]})
        return {
            "hard_valid": row.get("hard_valid"),
            "reasons": row.get("reasons"),
            "text": row.get("text"),
            "violations": violations,
        }

    return {
        "regeneration_invoked": meta.get("regeneration_invoked"),
        "regeneration_feedback": meta.get("regeneration_feedback"),
        "acceptance": review.get("acceptance"),
        "attempt_1": attempt("hard_validation_attempt_1") or review.get("attempt_1"),
        "attempt_2": attempt("hard_validation_attempt_2") or review.get("attempt_2"),
        "accepted_provenance": accepted.get("provenance"),
        "accepted_text": accepted.get("text"),
        "accepted_authority_result": accepted.get("authority_result"),
        "accepted_attempt": accepted.get("attempt"),
        "immutable": accepted.get("immutable"),
        "tags_note": None,
    }


def extract_trace(payload: dict, before: dict, after: dict, calls: list[dict]) -> dict:
    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
    decision = meta.get("gm_resolution_decision") if isinstance(meta.get("gm_resolution_decision"), dict) else {}
    compact = payload.get("turn_trace") if isinstance(payload.get("turn_trace"), dict) else {}
    social_hits = _find_values(payload, "topic_revealed", limit=4)
    resolver_hits = _find_values(payload, "selected_resolver", limit=4)
    generations = [call for call in calls if call.get("kind") == "generation"]
    interpretations = [call for call in calls if call.get("kind") == "interpretation"]
    retries = [call for call in calls if int(call.get("retry_attempt") or 0) > 0]
    return {
        "player_facing_text": gm.get("player_facing_text") or payload.get("player_facing_text"),
        "gm_tags": gm.get("tags"),
        "selected_resolver_hits": resolver_hits,
        "topic_revealed_hits": social_hits,
        "operation": contract.get("operation") or dig(compact, "resolution_path"),
        "interlocutor_id": contract.get("interlocutor_id"),
        "outcome_classification": decision.get("outcome_classification"),
        "validation": _validation_slice(meta),
        "compact_classification": compact.get("classification"),
        "compact_resolution_path": compact.get("resolution_path"),
        "interaction_after": compact.get("interaction_after"),
        "clues": compact.get("clues"),
        "latency_ms": compact.get("latency_ms"),
        "provider_request_count": len(calls),
        "generation_count": len(generations),
        "interpretation_count": len(interpretations),
        "retry_count": len(retries),
        "provider_candidates": [
            {
                "index": call.get("index"),
                "kind": call.get("kind"),
                "retry_attempt": call.get("retry_attempt"),
                "retry_reason": call.get("retry_reason"),
                "response_model": call.get("response_model"),
                "usage": call.get("usage"),
                "latency_seconds": call.get("latency_seconds"),
                "error": call.get("error"),
                "parsed_narration": call.get("parsed_narration"),
                "raw_output": call.get("raw_output"),
            }
            for call in calls
        ],
        "npc_runtime_before": before.get("npc_runtime"),
        "npc_runtime_after": after.get("npc_runtime"),
        "known_clues_before": before.get("known_clues"),
        "known_clues_after": after.get("known_clues"),
        "visible_facts_before": before.get("scene", {}).get("visible_facts"),
        "visible_facts_after": after.get("scene", {}).get("visible_facts"),
        "turn_counter_before": before.get("turn_counter"),
        "turn_counter_after": after.get("turn_counter"),
        "active_scene_before": before.get("active_scene_id"),
        "active_scene_after": after.get("active_scene_id"),
        "interaction_context_after": after.get("interaction_context"),
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
    started = time.perf_counter()
    try:
        response = client.post("/api/chat", json={"text": player_text})
        http_status = response.status_code
        payload = response.json()
    except BudgetStop as exc:
        error = f"BudgetStop: {exc}"
        HALT = str(exc)
    except Exception:
        error = traceback.format_exc()
    wall = round(time.perf_counter() - started, 3)
    after = snapshot()
    calls = CALLS[calls_at:]
    problems = severe_mutation(before, after)
    if problems:
        HALT = "severe unauthorized state mutation: " + "; ".join(problems)
    trace = extract_trace(payload if isinstance(payload, dict) else {}, before, after, calls)
    trace["wall_seconds"] = wall
    record = {
        "turn": turn_id,
        "player_input": player_text,
        "http_status": http_status,
        "error": error,
        "halt_after": HALT,
        "severe_mutations": problems,
        "wall_seconds": wall,
        "trace": trace,
    }
    save(f"{turn_id}/turn_record.json", record)
    save(f"{turn_id}/state_after.json", after)
    save(f"{turn_id}/api_response.json", payload)
    preview = " ".join(str(trace.get("player_facing_text") or "").split())[:220]
    status(
        f"DONE {turn_id} http={http_status} calls={len(calls)} retries={trace.get('retry_count')} "
        f"tokens={spent_tokens()} wall={wall}s text={preview}"
    )
    return record


def main() -> None:
    global HALT
    config = verify_config()
    before_mtimes = production_mtimes()
    save("production_mtimes_before.json", before_mtimes)
    status("CONFIG VERIFIED " + json.dumps(config["models"]) + " ceiling_usd=" + str(config["expected_cost_at_token_ceiling_usd"]["estimate_usd"]))
    seed()
    status("OPENING TEST CLIENT")
    with TestClient(api.app) as client:
        preflight_calls = list(CALLS)
        save("preflight_calls.json", [{k: v for k, v in call.items() if k != "raw_output"} | {"raw_output": call.get("raw_output")} for call in preflight_calls])
        if HALT:
            status("HALT BEFORE GAMEPLAY " + HALT)
        elif not preflight_calls:
            HALT = "preflight made no provider request; billing path not exercised"
            status("HALT " + HALT)
        elif not (preflight_calls[-1].get("usage") or {}):
            HALT = "preflight returned no usage accounting"
            status("HALT " + HALT)
        elif str(preflight_calls[-1].get("response_model") or "") != REQUIRED_RESPONSE_MODEL:
            HALT = f"preflight model {preflight_calls[-1].get('response_model')!r} is not {REQUIRED_RESPONSE_MODEL}"
            status("HALT " + HALT)
        else:
            status(
                f"PREFLIGHT OK tokens={spent_tokens()} model={preflight_calls[-1].get('response_model')} "
                f"usage={json.dumps(preflight_calls[-1].get('usage'))}"
            )
        seed()
        initial = snapshot()
        save("initial_state.json", initial)
        captain = next((npc for npc in initial["world"]["npcs"] if isinstance(npc, dict) and npc.get("id") == "guard_captain"), {})
        status(
            "INITIAL scene="
            + str(initial.get("active_scene_id"))
            + " location="
            + str(initial["scene"].get("location"))
            + " captain_topics="
            + json.dumps((captain or {}).get("topics"))
        )
        records = []
        planned = [
            ("T1", "Guard Captain, do you prefer standing watch in the rain, or somewhere dry?"),
            ("T2", "Captain, what do you know about the missing patrol?"),
        ]
        for turn_id, player in planned:
            if HALT:
                status("HALT BEFORE " + turn_id + " " + str(HALT))
                break
            if _budget_block_reason():
                HALT = _budget_block_reason()
                status("HALT BEFORE " + turn_id + " " + str(HALT))
                break
            completed = [row for row in records if row.get("http_status") == 200 and not row.get("error")]
            if len(completed) >= MAX_TURNS:
                break
            record = run_turn(client, turn_id, player)
            records.append(record)
            if record.get("error") or record.get("http_status") != 200:
                status("TURN DID NOT COMPLETE; not rerunning " + turn_id)
            if HALT:
                status("HALT AFTER " + turn_id + " " + HALT)
                break
        save(
            "run_finished.json",
            {
                "halt": HALT,
                "completed_turn_ids": [row["turn"] for row in records if row.get("http_status") == 200 and not row.get("error")],
                "attempted_turn_ids": [row["turn"] for row in records],
                "provider_requests": len(CALLS),
                "combined_tokens": spent_tokens(),
                "accounting_failed": ACCOUNTING_FAILED,
                "calls": [
                    {
                        "index": call.get("index"),
                        "turn": call.get("turn"),
                        "kind": call.get("kind"),
                        "retry_attempt": call.get("retry_attempt"),
                        "retry_reason": call.get("retry_reason"),
                        "response_model": call.get("response_model"),
                        "usage": call.get("usage"),
                        "latency_seconds": call.get("latency_seconds"),
                        "error": call.get("error"),
                        "parsed_narration": call.get("parsed_narration"),
                    }
                    for call in CALLS
                ],
            },
        )
    after_mtimes = production_mtimes()
    save("production_mtimes_after.json", after_mtimes)
    drifted = [key for key, value in before_mtimes.items() if after_mtimes.get(key) != value]
    save("production_mtime_drift.json", drifted)
    status(
        "FINISHED halt="
        + str(HALT)
        + " requests="
        + str(len(CALLS))
        + " tokens="
        + str(spent_tokens())
        + " production_drift="
        + str(drifted)
    )


if __name__ == "__main__":
    main()
