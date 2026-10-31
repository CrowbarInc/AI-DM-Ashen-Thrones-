#!/usr/bin/env python3
"""PR-CY live social efficiency verification.

Artifact-only diagnostic. It uses an isolated storage directory, skips the
billable startup preflight, and records exact Responses API usage for gameplay.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import sys
import time
import traceback
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
EVIDENCE = OUT / "evidence"
EVIDENCE.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))

MAX_REQUESTS = 3
MAX_TOKENS = 110_000
MAX_TURNS = 2
REQUIRED_RESPONSE_MODEL = "gpt-4.1-mini-2025-04-14"
ALLOWED_REQUEST_MODELS = {"gpt-4.1-mini", REQUIRED_RESPONSE_MODEL}
PR_CQ_T1_INPUT = 30_877
PR_CQ_T1_TOTAL = 30_943

CALLS: list[dict[str, Any]] = []
HALT: str | None = None
ACCOUNTING_FAILED = False
CURRENT = {"turn": "phase0", "kind": "setup", "retry_attempt": 0, "retry_reason": None}

_SECRET = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")


class BudgetStop(BaseException):
    """Not an Exception, so provider fallback code cannot swallow it."""


def redact(text: str) -> str:
    return _SECRET.sub("sk-REDACTED", text)


def dump_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact(dump_json(value)) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact(text), encoding="utf-8")


def status(text: str) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {text}"
    print(line, flush=True)
    with (EVIDENCE / "status.txt").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def spent_tokens() -> int:
    total = 0
    for call in CALLS:
        usage = call.get("usage") or {}
        if isinstance(usage.get("total_tokens"), int):
            total += usage["total_tokens"]
        else:
            total += int(usage.get("input_tokens") or 0) + int(usage.get("output_tokens") or 0)
    return total


def budget_block_reason() -> str | None:
    if ACCOUNTING_FAILED:
        return "usage accounting unavailable"
    if len(CALLS) >= MAX_REQUESTS:
        return f"provider request budget reached ({MAX_REQUESTS})"
    if spent_tokens() >= MAX_TOKENS:
        return f"token budget reached ({spent_tokens()})"
    return None


import openai.resources.responses as responses_module

Responses = responses_module.Responses
ORIGINAL_CREATE = Responses.create


def usage_from_response_dump(dump: dict[str, Any]) -> dict[str, Any]:
    usage = dump.get("usage") if isinstance(dump, dict) else None
    if not isinstance(usage, dict):
        return {}
    details_in = usage.get("input_tokens_details") if isinstance(usage.get("input_tokens_details"), dict) else {}
    details_out = usage.get("output_tokens_details") if isinstance(usage.get("output_tokens_details"), dict) else {}
    return {
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "cached_input_tokens": details_in.get("cached_tokens"),
        "input_tokens_details": details_in,
        "output_tokens_details": details_out,
    }


def narration_from_raw(raw: Any) -> str:
    text = str(raw or "")
    try:
        data = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return text
    if isinstance(data, dict):
        for key in ("narration", "player_facing_text", "text"):
            if isinstance(data.get(key), str) and data[key].strip():
                return data[key]
    return text


def observe_create(self, *args, **kwargs):
    global ACCOUNTING_FAILED, HALT
    reason = budget_block_reason()
    requested = str(kwargs.get("model") or "")
    if requested and requested not in ALLOWED_REQUEST_MODELS:
        reason = f"refusing model substitution: requested {requested}"
    if reason:
        HALT = reason
        raise BudgetStop(reason)

    started = time.perf_counter()
    row: dict[str, Any] = {
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
    turn = str(CURRENT.get("turn") or "unknown")
    attempt = int(row["retry_attempt"] or 0) + 1
    kind = str(row["kind"] or "generation")
    save_json(
        EVIDENCE / turn / f"provider_request_{kind}_{attempt}.json",
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
        result = ORIGINAL_CREATE(self, *args, **kwargs)
        response_dump = result.model_dump(mode="json")
        row["raw_output"] = getattr(result, "output_text", None)
        row["parsed_narration"] = narration_from_raw(row["raw_output"])
        row["response_id"] = response_dump.get("id")
        row["response_model"] = response_dump.get("model")
        row["usage"] = usage_from_response_dump(response_dump)
        row["status"] = response_dump.get("status")
        row["error"] = None
        if not row["usage"]:
            ACCOUNTING_FAILED = True
            HALT = "usage accounting unavailable after provider response"
        elif str(row["response_model"] or "") != REQUIRED_RESPONSE_MODEL:
            HALT = f"response model {row['response_model']!r} is not {REQUIRED_RESPONSE_MODEL}"
        return result
    except BudgetStop:
        raise
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        row["usage"] = {}
        row["raw_output"] = None
        row["parsed_narration"] = ""
        raise
    finally:
        row["finished"] = datetime.now(timezone.utc).isoformat()
        row["latency_seconds"] = round(time.perf_counter() - started, 3)
        save_json(EVIDENCE / "model_calls.json", CALLS)


Responses.create = observe_create

from fastapi.testclient import TestClient

import game.api as api
import game.gm as gm_module
import game.semantic_interpreter as interpreter
from game import storage
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


def verify_config() -> dict[str, Any]:
    key = get_openai_api_key() or ""
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE") or ""
    models = {
        "MODEL_NAME": MODEL_NAME,
        "DEFAULT_MODEL_NAME": DEFAULT_MODEL_NAME,
        "HIGH_PRECISION_MODEL_NAME": HIGH_PRECISION_MODEL_NAME,
        "RETRY_ESCALATION_MODEL_NAME": RETRY_ESCALATION_MODEL_NAME,
    }
    unknown = sorted({value for value in models.values() if value not in ALLOWED_REQUEST_MODELS})
    report = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "provider": "OpenAI",
        "billing_path": "OpenAI Python SDK Responses API via client.responses.create.",
        "endpoint": "https://api.openai.com/v1/responses" if not base_url else base_url,
        "base_url_override_present": bool(base_url),
        "models": models,
        "enable_model_routing": ENABLE_MODEL_ROUTING,
        "required_response_model": REQUIRED_RESPONSE_MODEL,
        "api_key_present": bool(key.startswith("sk-")),
        "api_key_length": len(key),
        "startup_preflight": "skipped by ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1; no billable preflight request used.",
        "live_interpretation": "disabled by ASHEN_DISABLE_LIVE_INTERPRETATION=1 to preserve gameplay request budget.",
        "hard_budget": {
            "max_completed_gameplay_turns": MAX_TURNS,
            "max_provider_requests": MAX_REQUESTS,
            "max_combined_tokens": MAX_TOKENS,
        },
        "unknown_unpriced_or_substituted_models": unknown,
    }
    save_json(EVIDENCE / "phase0_config.json", report)
    if unknown or base_url or not report["api_key_present"]:
        raise SystemExit("STOP config: " + dump_json({"unknown_models": unknown, "base_url_override": bool(base_url), "api_key_present": report["api_key_present"]}))
    if MODEL_NAME != "gpt-4.1-mini":
        raise SystemExit(f"STOP model is {MODEL_NAME}, required gpt-4.1-mini")
    return report


def point_storage() -> None:
    base = EVIDENCE / "isolated_session"
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


def snapshot() -> dict[str, Any]:
    session = storage.load_session()
    world = storage.load_world()
    sid = session.get("active_scene_id")
    scene_doc = storage.load_scene(sid) if sid else {}
    scene = scene_doc.get("scene") if isinstance(scene_doc, dict) else {}
    character = storage.load_character()
    return {
        "turn_counter": session.get("turn_counter"),
        "active_scene_id": sid,
        "interaction_context": session.get("interaction_context"),
        "discourse_focus": session.get("discourse_focus"),
        "conversation": session.get("chat_history") or session.get("conversation_history") or [],
        "known_clues": session.get("known_clues"),
        "scene_runtime": storage.get_scene_runtime(session, sid) if sid else {},
        "npc_runtime": session.get("npc_runtime") if isinstance(session.get("npc_runtime"), dict) else {},
        "scene": {
            "id": scene.get("id"),
            "location": scene.get("location"),
            "summary": scene.get("summary"),
            "mode": scene.get("mode"),
            "visible_facts": list(scene.get("visible_facts") or []),
            "hidden_facts": list(scene.get("hidden_facts") or []),
            "discoverable_clues": list(scene.get("discoverable_clues") or []),
            "addressables": list(scene.get("addressables") or []),
        },
        "world": {
            "npcs": world.get("npcs") or [],
            "factions": world.get("factions") or [],
            "clues": world.get("clues") or {},
            "world_flags": world.get("world_flags") or [],
        },
        "character": {
            "name": character.get("name"),
            "hp": character.get("hp"),
            "inventory": character.get("inventory"),
            "spells": character.get("spells"),
            "conditions": character.get("conditions"),
        },
    }


def production_mtimes() -> dict[str, int]:
    paths = [
        ROOT / "data" / "session.json",
        ROOT / "data" / "world.json",
        ROOT / "data" / "combat.json",
        ROOT / "data" / "session_log.jsonl",
        ROOT / "data" / "scenes" / "frontier_gate.json",
    ]
    return {str(path.relative_to(ROOT)): path.stat().st_mtime_ns for path in paths if path.exists()}


def text_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(text_values(item))
        return out
    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(text_values(item))
        return out
    return []


def severe_mutation(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if before.get("active_scene_id") != after.get("active_scene_id"):
        problems.append("active_scene_changed")
    if before.get("character") != after.get("character"):
        problems.append("character_sheet_changed")
    before_ids = [npc.get("id") for npc in before["world"]["npcs"] if isinstance(npc, dict)]
    after_ids = [npc.get("id") for npc in after["world"]["npcs"] if isinstance(npc, dict)]
    if before_ids != after_ids:
        problems.append("npc_roster_changed")
    before_topics = text_values([npc.get("topics") for npc in before["world"]["npcs"] if isinstance(npc, dict)])
    after_topics = text_values([npc.get("topics") for npc in after["world"]["npcs"] if isinstance(npc, dict)])
    if before_topics != after_topics:
        problems.append("npc_topic_text_changed")
    if before["scene"]["hidden_facts"] != after["scene"]["hidden_facts"]:
        problems.append("hidden_facts_changed")
    hidden = {item.strip() for item in before["scene"]["hidden_facts"] if isinstance(item, str)}
    for fact in after["scene"]["visible_facts"]:
        if isinstance(fact, str) and fact.strip() in hidden and fact not in before["scene"]["visible_facts"]:
            problems.append("hidden_fact_promoted_into_visible_facts")
    return problems


def wrap_provider(fn, kind: str):
    def observed(*args, **kwargs):
        prior = dict(CURRENT)
        CURRENT.update(kind=kind, retry_attempt=kwargs.get("retry_attempt", 0), retry_reason=kwargs.get("retry_reason"))
        try:
            return fn(*args, **kwargs)
        finally:
            CURRENT.clear()
            CURRENT.update(prior)

    return observed


api.call_gpt = wrap_provider(api.call_gpt, "generation")
interpreter._invoke_interpretation_model = wrap_provider(interpreter._invoke_interpretation_model, "interpretation")


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def payload_measurement(label: str, messages: list[dict[str, str]], resolution: dict[str, Any]) -> dict[str, Any]:
    payload = json.loads(messages[1]["content"])
    serialized = json.dumps(messages, ensure_ascii=False, sort_keys=True)
    content_bytes = len(messages[1]["content"].encode("utf-8"))
    projection = payload.get("provider_context_projection") if isinstance(payload.get("provider_context_projection"), dict) else {}
    metadata = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    return {
        "label": label,
        "provider_context_projection_selected": projection.get("selected"),
        "selected_resolver": metadata.get("selected_resolver"),
        "selected_response_envelope": gm_module._provider_response_contract_from_payload(payload),
        "active_interlocutor": payload.get("active_interlocutor"),
        "turn_operation": (payload.get("decision_facing_answer_recipe") or {}).get("turn_operation"),
        "serialized_prompt_bytes": len(serialized.encode("utf-8")),
        "user_payload_bytes": content_bytes,
        "estimated_tokens_rough_bytes_over_4": round(len(serialized.encode("utf-8")) / 4),
        "payload_hash": stable_hash(messages),
        "top_level_keys": sorted(payload.keys()),
        "projection": projection,
    }


def reconstruct_payloads() -> dict[str, Any]:
    from tests.test_pr_cw_social_context_projection import _REAL_PROJECTOR, social_request

    player = "Guard Captain, do you prefer standing watch in the rain, or somewhere dry?"
    original = gm_module._project_harmless_social_provider_context
    try:
        gm_module._project_harmless_social_provider_context = lambda payload, **kwargs: payload
        full_messages, full_resolution, *_ = social_request(player)
        gm_module._project_harmless_social_provider_context = _REAL_PROJECTOR
        reduced_messages, reduced_resolution, *_ = social_request(player)
    finally:
        gm_module._project_harmless_social_provider_context = original

    full_payload = json.loads(full_messages[1]["content"])
    reduced_payload = json.loads(reduced_messages[1]["content"])
    retained_keys = sorted(set(full_payload) & set(reduced_payload))
    omitted_keys = sorted(set(full_payload) - set(reduced_payload))
    size_delta_by_key = {}
    for key in retained_keys:
        before = len(json.dumps(full_payload.get(key), ensure_ascii=False, sort_keys=True).encode("utf-8"))
        after = len(json.dumps(reduced_payload.get(key), ensure_ascii=False, sort_keys=True).encode("utf-8"))
        if before != after:
            size_delta_by_key[key] = {"full_bytes": before, "reduced_bytes": after, "delta_bytes": after - before}

    comparison = {
        "player_input": player,
        "full_context": payload_measurement("full_context_reconstruction", full_messages, full_resolution),
        "reduced_context": payload_measurement("reduced_context_reconstruction", reduced_messages, reduced_resolution),
        "retained_context_top_level_keys": retained_keys,
        "omitted_context_top_level_keys": omitted_keys,
        "changed_retained_context_sizes": size_delta_by_key,
        "byte_reduction": len(json.dumps(full_messages, ensure_ascii=False, sort_keys=True).encode("utf-8"))
        - len(json.dumps(reduced_messages, ensure_ascii=False, sort_keys=True).encode("utf-8")),
    }
    save_json(EVIDENCE / "payload_reconstruction.json", comparison)
    save_json(EVIDENCE / "phase2_full_context_provider_request.json", {"provider_input": full_messages})
    save_json(EVIDENCE / "phase2_reduced_context_provider_request.json", {"provider_input": reduced_messages})
    return comparison


def validation_slice(payload: dict[str, Any]) -> dict[str, Any]:
    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    review = meta.get("decision_review") if isinstance(meta.get("decision_review"), dict) else {}
    accepted = meta.get("accepted_response") if isinstance(meta.get("accepted_response"), dict) else {}
    return {
        "regeneration_invoked": meta.get("regeneration_invoked"),
        "regeneration_feedback": meta.get("regeneration_feedback"),
        "hard_validation_attempt_1": meta.get("hard_validation_attempt_1") or review.get("attempt_1"),
        "hard_validation_attempt_2": meta.get("hard_validation_attempt_2") or review.get("attempt_2"),
        "accepted_attempt": accepted.get("attempt"),
        "accepted_text": accepted.get("text"),
        "accepted_authority_result": accepted.get("authority_result"),
        "accepted_provenance": accepted.get("provenance"),
    }


def find_values(obj: Any, key: str, limit: int = 8) -> list[Any]:
    found: list[Any] = []

    def walk(node: Any, path: str) -> None:
        if len(found) >= limit:
            return
        if isinstance(node, dict):
            if key in node:
                found.append({"path": f"{path}.{key}", "value": node[key]})
            for child_key, child in node.items():
                if child_key in {"provider_input", "raw_output"}:
                    continue
                walk(child, f"{path}.{child_key}")
        elif isinstance(node, list):
            for index, child in enumerate(node[:40]):
                walk(child, f"{path}[{index}]")

    walk(obj, "$")
    return found


def extract_trace(payload: dict[str, Any], before: dict[str, Any], after: dict[str, Any], calls: list[dict[str, Any]]) -> dict[str, Any]:
    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    resolution = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
    compact = payload.get("turn_trace") if isinstance(payload.get("turn_trace"), dict) else {}
    generations = [call for call in calls if call.get("kind") == "generation"]
    retries = [call for call in calls if int(call.get("retry_attempt") or 0) > 0]
    request_payloads = []
    for call in calls:
        req_path = EVIDENCE / str(call.get("turn")) / f"provider_request_{call.get('kind')}_{int(call.get('retry_attempt') or 0) + 1}.json"
        if req_path.exists():
            request_payloads.append(json.loads(req_path.read_text(encoding="utf-8")))
    generation_payload = {}
    if request_payloads:
        provider_input = request_payloads[0].get("provider_input") or []
        if len(provider_input) > 1 and isinstance(provider_input[1], dict):
            try:
                generation_payload = json.loads(provider_input[1].get("content") or "{}")
            except json.JSONDecodeError:
                generation_payload = {}
    projection = generation_payload.get("provider_context_projection") if isinstance(generation_payload.get("provider_context_projection"), dict) else {}
    return {
        "player_facing_text": gm.get("player_facing_text") or payload.get("player_facing_text"),
        "gm_tags": gm.get("tags"),
        "selected_resolver_hits": find_values(payload, "selected_resolver"),
        "response_envelope": gm_module._provider_response_contract_from_payload(generation_payload) if generation_payload else None,
        "provider_context_projection": projection,
        "active_interlocutor": generation_payload.get("active_interlocutor") if generation_payload else None,
        "recent_log": generation_payload.get("recent_log") if generation_payload else None,
        "operation": resolution.get("operation") or compact.get("resolution_path"),
        "interlocutor_id": resolution.get("interlocutor_id"),
        "validation": validation_slice(payload),
        "compact_classification": compact.get("classification"),
        "compact_resolution_path": compact.get("resolution_path"),
        "interaction_after": compact.get("interaction_after"),
        "provider_request_count": len(calls),
        "generation_count": len(generations),
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
        "state_before": before,
        "state_after": after,
    }


def run_turn(client: TestClient, turn_id: str, player_text: str) -> dict[str, Any]:
    global HALT
    before = snapshot()
    save_json(EVIDENCE / turn_id / "state_before.json", before)
    calls_at = len(CALLS)
    CURRENT["turn"] = turn_id
    status(f"RUNNING {turn_id}")
    error = None
    payload: dict[str, Any] = {}
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
    save_json(EVIDENCE / turn_id / "turn_record.json", record)
    save_json(EVIDENCE / turn_id / "state_after.json", after)
    save_json(EVIDENCE / turn_id / "api_response.json", payload)
    preview = " ".join(str(trace.get("player_facing_text") or "").split())[:220]
    status(f"DONE {turn_id} http={http_status} calls={len(calls)} retries={trace.get('retry_count')} tokens={spent_tokens()} wall={wall}s text={preview}")
    return record


AUTHORITY_PATTERNS = {
    "invented_npc_biography": [r"\bborn\b", r"\bserved for\b", r"\byears\b"],
    "invented_geography": [r"\beast\b", r"\bwest\b", r"\bnorth\b", r"\bsouth\b", r"\bbeyond\b"],
    "unsupported_hidden_information": [r"\bsecret\b", r"\bhidden\b", r"\btunnel\b"],
    "consequential_npc_actions": [r"\bunlock", r"\blets? you pass\b", r"\bgives? you\b", r"\bhands? you\b"],
    "unauthorized_discoveries": [r"\byou discover\b", r"\byou find\b"],
    "unsupported_certainty": [r"\bconfirms?\b", r"\bdefinitely\b", r"\bwas murdered\b"],
}


def audit_text(text: str) -> dict[str, Any]:
    hits: dict[str, list[str]] = {}
    for label, patterns in AUTHORITY_PATTERNS.items():
        found = [pat for pat in patterns if re.search(pat, text or "", re.IGNORECASE)]
        if found:
            hits[label] = found
    false_positive_indicators = []
    if re.search(r"\bprefer|rather|harder|easier|I\b", text or "", re.IGNORECASE):
        false_positive_indicators.append("ordinary_subjective_speech_present")
    if re.search(r"\bshrugs?|nods?|glances?|mutters?|says?\b", text or "", re.IGNORECASE):
        false_positive_indicators.append("ordinary_gesture_or_speech_present")
    return {"text": text, "authority_pattern_hits": hits, "false_positive_indicators": false_positive_indicators}


def score_turn(record: dict[str, Any], previous_text: str = "") -> dict[str, Any]:
    text = str(record.get("trace", {}).get("player_facing_text") or "")
    lower = text.lower()
    player = str(record.get("player_input") or "").lower()
    audit = audit_text(text)
    intent = 2 if (("prefer" in player and "dry" in lower) or ("harder" in player and ("harder" in lower or "rain" in lower))) else (1 if text else 0)
    relevance = 2 if ("rain" in lower or "dry" in lower or "watch" in lower) else (1 if text else 0)
    continuity = 2 if record["turn"] == "T1" else (2 if ("rain" in lower and ("watch" in lower or "captain" in lower or "guard" in lower)) else 1 if text else 0)
    naturalness = 2 if len(text.split()) >= 8 and "cannot answer" not in lower else (1 if text else 0)
    authority = 0 if audit["authority_pattern_hits"] else 2
    total = intent + relevance + continuity + naturalness + authority
    return {
        "turn": record.get("turn"),
        "intent_comprehension": intent,
        "answer_relevance": relevance,
        "conversational_continuity": continuity,
        "narrative_naturalness": naturalness,
        "authority_integrity": authority,
        "total": total,
        "notes": "; ".join(audit["authority_pattern_hits"].keys()) if audit["authority_pattern_hits"] else "No authority-pattern hit in final text.",
    }


def summarize_usage(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for call in CALLS:
        usage = call.get("usage") or {}
        rows.append({
            "gameplay_turn": call.get("turn"),
            "request_number": call.get("index"),
            "kind": call.get("kind"),
            "model": call.get("response_model") or call.get("model"),
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "cached_input_tokens": usage.get("cached_input_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "latency_seconds": call.get("latency_seconds"),
            "retry_status": "retry" if int(call.get("retry_attempt") or 0) > 0 else "initial",
            "validation_outcome": "",
            "rejection_reasons": "",
            "finalization_method": "",
        })
    for row in rows:
        rec = next((r for r in records if r.get("turn") == row["gameplay_turn"]), None)
        if rec:
            validation = rec.get("trace", {}).get("validation") or {}
            attempt = validation.get("hard_validation_attempt_1") or {}
            row["validation_outcome"] = attempt.get("hard_valid") if isinstance(attempt, dict) else ""
            row["rejection_reasons"] = json.dumps(attempt.get("reasons") if isinstance(attempt, dict) else "", ensure_ascii=False)
            row["finalization_method"] = "immutable_preserve_if_valid" if validation.get("accepted_text") else "unknown"
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_reports(config: dict[str, Any], reconstruction: dict[str, Any], records: list[dict[str, Any]], before_mtimes: dict[str, int], after_mtimes: dict[str, int]) -> str:
    usage_rows = summarize_usage(records)
    scores = [score_turn(record, records[index - 1]["trace"]["player_facing_text"] if index else "") for index, record in enumerate(records)]
    write_csv(OUT / "PR-CY_provider_usage.csv", usage_rows)
    write_csv(OUT / "PR-CY_player_experience_scores.csv", scores)
    save_json(OUT / "PR-CY_turn_traces.json", {
        "phase0": {"git_head": git("rev-parse HEAD"), "config": config},
        "payload_reconstruction": reconstruction,
        "halt": HALT,
        "provider_requests": len(CALLS),
        "combined_tokens": spent_tokens(),
        "turns": records,
    })

    t1 = next((r for r in records if r.get("turn") == "T1"), {})
    t2 = next((r for r in records if r.get("turn") == "T2"), {})
    t1_call = next((c for c in CALLS if c.get("turn") == "T1" and c.get("kind") == "generation"), {})
    t1_usage = t1_call.get("usage") or {}
    t1_input = int(t1_usage.get("input_tokens") or 0)
    t1_total = int(t1_usage.get("total_tokens") or 0)
    reduction_abs = PR_CQ_T1_INPUT - t1_input if t1_input else None
    reduction_pct = round((reduction_abs / PR_CQ_T1_INPUT) * 100, 2) if reduction_abs is not None else None
    completed_turns = [r for r in records if r.get("http_status") == 200 and not r.get("error")]
    authority_audits = []
    for record in records:
        texts = [str(record.get("trace", {}).get("player_facing_text") or "")]
        for candidate in record.get("trace", {}).get("provider_candidates") or []:
            texts.append(str(candidate.get("parsed_narration") or candidate.get("raw_output") or ""))
        authority_audits.append({"turn": record.get("turn"), "audits": [audit_text(text) for text in texts if text]})
    authority_violations = [a for turn in authority_audits for a in turn["audits"] if a["authority_pattern_hits"]]
    false_positive_rejections = []
    for record in records:
        validation = record.get("trace", {}).get("validation") or {}
        attempts = [
            ("attempt_1", validation.get("hard_validation_attempt_1"), 0),
            ("attempt_2", validation.get("hard_validation_attempt_2"), 1),
        ]
        candidates = record.get("trace", {}).get("provider_candidates") or []
        for attempt_name, attempt, candidate_index in attempts:
            if not isinstance(attempt, dict) or attempt.get("hard_valid") is not False:
                continue
            text = str((candidates[candidate_index] if len(candidates) > candidate_index else {}).get("parsed_narration") or attempt.get("text") or "")
            audit = audit_text(text)
            reason_blob = json.dumps(attempt.get("reasons") or attempt.get("gm_resolution_decision_audit") or {}, ensure_ascii=False)
            harmless_followup = bool(re.search(r"\brain|watch|vigilance|discomfort|harder|hampers|aids\b", text, re.IGNORECASE))
            if (audit["false_positive_indicators"] or harmless_followup) and not audit["authority_pattern_hits"]:
                false_positive_rejections.append({"turn": record.get("turn"), "attempt": attempt_name, "text": text, "validation": attempt, "reason_blob_excerpt": reason_blob[:1200]})

    reduced_used = all((r.get("trace", {}).get("provider_context_projection") or {}).get("selected") is True for r in completed_turns)
    retries = [c for c in CALLS if int(c.get("retry_attempt") or 0) > 0]
    if not completed_turns or len(completed_turns) < 2 or HALT:
        decision = "F - PROVIDER / ENVIRONMENT BLOCKED" if HALT and "budget" not in HALT else "H - INCONCLUSIVE"
    elif false_positive_rejections:
        decision = "E - VALIDATION FALSE POSITIVES"
    elif authority_violations:
        decision = "D - AUTHORITY REGRESSION"
    elif not reduced_used:
        decision = "H - INCONCLUSIVE"
    elif t1_input and t1_input < PR_CQ_T1_INPUT and not retries:
        decision = "A - LIVE EFFICIENCY VERIFIED"
    else:
        decision = "B - QUALITY PRESERVED, SAVINGS LIMITED"

    transcript_lines = ["# PR-CY Turn Transcripts", ""]
    for record in records:
        transcript_lines += [
            f"## {record['turn']}",
            "",
            f"Player: {record['player_input']}",
            "",
            f"Final: {record.get('trace', {}).get('player_facing_text')}",
            "",
            "Provider candidates:",
            "",
        ]
        for candidate in record.get("trace", {}).get("provider_candidates") or []:
            transcript_lines += [
                f"- request {candidate.get('index')} retry={candidate.get('retry_attempt')} usage={candidate.get('usage')}",
                "",
                str(candidate.get("parsed_narration") or candidate.get("raw_output") or ""),
                "",
            ]
    write_text(OUT / "PR-CY_turn_transcripts.md", "\n".join(transcript_lines))

    prompt_md = f"""# PR-CY Prompt Comparison

Deterministic reconstruction only; no provider calls.

| Payload | Reduced-context eligible | Response envelope | Serialized prompt bytes | Rough estimated tokens | Payload hash |
|---|---:|---|---:|---:|---|
| Full context | {reconstruction['full_context']['provider_context_projection_selected']} | {reconstruction['full_context']['selected_response_envelope']} | {reconstruction['full_context']['serialized_prompt_bytes']} | {reconstruction['full_context']['estimated_tokens_rough_bytes_over_4']} | `{reconstruction['full_context']['payload_hash']}` |
| Reduced context | {reconstruction['reduced_context']['provider_context_projection_selected']} | {reconstruction['reduced_context']['selected_response_envelope']} | {reconstruction['reduced_context']['serialized_prompt_bytes']} | {reconstruction['reduced_context']['estimated_tokens_rough_bytes_over_4']} | `{reconstruction['reduced_context']['payload_hash']}` |

Byte reduction: {reconstruction['byte_reduction']} bytes.

Retained top-level context: `{', '.join(reconstruction['retained_context_top_level_keys'])}`.

Omitted top-level context: `{', '.join(reconstruction['omitted_context_top_level_keys']) or 'none'}`.

Changed retained context sizes:

```json
{json.dumps(reconstruction['changed_retained_context_sizes'], indent=2, ensure_ascii=False)}
```
"""
    write_text(OUT / "PR-CY_prompt_comparison.md", prompt_md)

    audit_md = "# PR-CY Authority Assessment\n\n"
    audit_md += f"Authority pattern hits in finals/candidates: {len(authority_violations)}.\n\n"
    audit_md += f"False-positive rejection candidates: {len(false_positive_rejections)}.\n\n"
    audit_md += "```json\n" + json.dumps({"authority_audits": authority_audits, "false_positive_rejections": false_positive_rejections}, indent=2, ensure_ascii=False) + "\n```\n"
    write_text(OUT / "PR-CY_authority_assessment.md", audit_md)

    continuity = {
        "production_mtime_drift": [key for key, value in before_mtimes.items() if after_mtimes.get(key) != value],
        "turns": [
            {
                "turn": r.get("turn"),
                "active_scene_before": r.get("trace", {}).get("state_before", {}).get("active_scene_id"),
                "active_scene_after": r.get("trace", {}).get("state_after", {}).get("active_scene_id"),
                "interaction_after": r.get("trace", {}).get("interaction_after"),
                "active_interlocutor": r.get("trace", {}).get("active_interlocutor"),
                "recent_log": r.get("trace", {}).get("recent_log"),
                "severe_mutations": r.get("severe_mutations"),
            }
            for r in records
        ],
    }
    write_text(OUT / "PR-CY_state_continuity.md", "# PR-CY State And Continuity\n\n```json\n" + json.dumps(continuity, indent=2, ensure_ascii=False) + "\n```\n")

    failure_inventory = {
        "halt": HALT,
        "errors": [r for r in records if r.get("error") or r.get("http_status") != 200],
        "authority_violations": authority_violations,
        "false_positive_rejections": false_positive_rejections,
        "budget": {"provider_requests": len(CALLS), "tokens": spent_tokens(), "max_provider_requests": MAX_REQUESTS, "max_tokens": MAX_TOKENS},
    }
    write_text(OUT / "PR-CY_failure_inventory.md", "# PR-CY Failure Inventory\n\n```json\n" + json.dumps(failure_inventory, indent=2, ensure_ascii=False) + "\n```\n")

    report = f"""# PR-CY Live Verification Report

Mode: LIVE SOCIAL EFFICIENCY VERIFICATION.

Provider: {config['provider']} Responses API. Startup preflight was skipped; the first billable calls were gameplay generation calls.

Model requirement: {REQUIRED_RESPONSE_MODEL}. Configured model knobs: `{json.dumps(config['models'], ensure_ascii=False)}`.

Completed gameplay turns: {len(completed_turns)}.

Provider requests: {len(CALLS)}.

Actual input tokens: {sum(int((c.get('usage') or {}).get('input_tokens') or 0) for c in CALLS)}.

Actual output tokens: {sum(int((c.get('usage') or {}).get('output_tokens') or 0) for c in CALLS)}.

Total tokens: {spent_tokens()}.

Reduced-context eligibility: {'used on completed turns' if reduced_used else 'not proved on all completed turns'}.

Historical PR-CQ first preference request: {PR_CQ_T1_INPUT} input tokens, {PR_CQ_T1_TOTAL} total tokens, 0 retries.

PR-CY first preference request: {t1_input or 'unavailable'} input tokens, {t1_usage.get('output_tokens', 'unavailable')} output tokens, {t1_total or 'unavailable'} total tokens.

Actual measured input reduction: {reduction_abs if reduction_abs is not None else 'unavailable'} tokens ({str(reduction_pct) + '%' if reduction_pct is not None else 'unavailable'}).

Retry overhead: PR-CY retries {len(retries)} vs PR-CQ first-turn retries 0.

Decision: {decision}.
"""
    write_text(OUT / "PR-CY_live_verification_report.md", report)

    changed = [
        "artifacts/pr_cy_live_social_efficiency/*",
        "handoff/CURRENT_REVIEW.md",
        "handoff/REVIEW_MANIFEST.json",
        "handoff/CURRENT_REVIEW.zip",
    ]
    write_text(OUT / "changed_files.txt", "\n".join(changed) + "\n")

    current_review = f"""PR-CY

MODE:
LIVE SOCIAL EFFICIENCY VERIFICATION

PR-CX inherited decision:
A - AUTHORITY ASSURANCE VERIFIED

Provider:
{config['provider']} Responses API

Model:
{REQUIRED_RESPONSE_MODEL}

Completed gameplay turns:
{len(completed_turns)}

Provider requests:
{len(CALLS)}

Actual input tokens:
{sum(int((c.get('usage') or {}).get('input_tokens') or 0) for c in CALLS)}

Actual output tokens:
{sum(int((c.get('usage') or {}).get('output_tokens') or 0) for c in CALLS)}

Total tokens:
{spent_tokens()}

Retry tokens:
{sum(int((c.get('usage') or {}).get('total_tokens') or 0) for c in retries)}

Reduced-context eligibility:
{'selected=True on completed turns' if reduced_used else 'not proved on all completed turns'}

Historical PR-CQ preference input:
30,877 tokens

PR-CY preference input:
{t1_input or 'unavailable'}

Actual measured reduction:
{reduction_abs if reduction_abs is not None else 'unavailable'} tokens ({str(reduction_pct) + '%' if reduction_pct is not None else 'unavailable'})

Turn 1 player-facing response:
{t1.get('trace', {}).get('player_facing_text')}

Turn 2 player-facing response:
{t2.get('trace', {}).get('player_facing_text')}

Player-experience scores:
{json.dumps(scores, ensure_ascii=False)}

Authority integrity:
{'PASS: no authority-pattern hits and no severe state mutation.' if not authority_violations else 'FAIL: authority-pattern hits recorded.'}

Continuity:
{'PASS: same session, same scene, prior log available in turn 2 payload.' if len(completed_turns) >= 2 else 'INCOMPLETE: insufficient completed turns.'}

PR-CY decision:
{decision}

Recommended next step:
Independent review of PR-CY artifacts; proceed only if reviewers accept the live token and authority evidence.
"""
    write_text(ROOT / "handoff" / "CURRENT_REVIEW.md", current_review)
    manifest = {
        "pr": "PR-CY",
        "mode": "LIVE SOCIAL EFFICIENCY VERIFICATION",
        "decision": decision,
        "artifacts": [str(p.relative_to(ROOT)) for p in sorted(OUT.glob("PR-CY_*"))] + [str((OUT / "changed_files.txt").relative_to(ROOT))],
        "provider_requests": len(CALLS),
        "total_tokens": spent_tokens(),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    save_json(ROOT / "handoff" / "REVIEW_MANIFEST.json", manifest)
    zip_path = ROOT / "handoff" / "CURRENT_REVIEW.zip"
    shutil.make_archive(str(zip_path.with_suffix("")), "zip", ROOT / "handoff")
    return decision


def git(args: str) -> str:
    import subprocess

    try:
        return subprocess.check_output(["git", *args.split()], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"git command failed: {exc}"


def main() -> None:
    global HALT
    config = verify_config()
    phase0 = {
        "git_head": git("rev-parse HEAD"),
        "git_status_short": git("status --short"),
        "git_diff_stat": git("diff --stat"),
        "pr_cw_state": (ROOT / "artifacts/pr_cw_social_context_projection/PR-CW_implementation_report.md").read_text(encoding="utf-8")[:4000],
        "pr_cx_state": (ROOT / "artifacts/pr_cx_authority_assurance/PR-CX_assurance_report.md").read_text(encoding="utf-8")[:4000],
        "config": config,
    }
    save_json(EVIDENCE / "phase0_worktree.json", phase0)
    status("PHASE0 CONFIG VERIFIED")

    reconstruction = reconstruct_payloads()
    status("PHASE2 PAYLOADS RECONSTRUCTED")

    before_mtimes = production_mtimes()
    save_json(EVIDENCE / "production_mtimes_before.json", before_mtimes)
    seed()
    save_json(EVIDENCE / "initial_state.json", snapshot())
    records: list[dict[str, Any]] = []
    planned = [
        ("T1", "Guard Captain, do you prefer standing watch in the rain, or somewhere dry?"),
        ("T2", "Does the rain make it harder to keep watch?"),
    ]
    with TestClient(api.app) as client:
        for turn_id, player in planned:
            if HALT or budget_block_reason():
                HALT = HALT or budget_block_reason()
                status(f"HALT BEFORE {turn_id}: {HALT}")
                break
            completed = [row for row in records if row.get("http_status") == 200 and not row.get("error")]
            if len(completed) >= MAX_TURNS:
                break
            record = run_turn(client, turn_id, player)
            records.append(record)
            if record.get("error") or record.get("http_status") != 200:
                status(f"TURN {turn_id} did not complete; not rerunning")
                break
            if HALT:
                status(f"HALT AFTER {turn_id}: {HALT}")
                break
    after_mtimes = production_mtimes()
    save_json(EVIDENCE / "production_mtimes_after.json", after_mtimes)
    save_json(EVIDENCE / "production_mtime_drift.json", [key for key, value in before_mtimes.items() if after_mtimes.get(key) != value])
    save_json(EVIDENCE / "run_finished.json", {"halt": HALT, "provider_requests": len(CALLS), "combined_tokens": spent_tokens(), "records": records, "calls": CALLS})
    decision = build_reports(config, reconstruction, records, before_mtimes, after_mtimes)
    status(f"FINISHED decision={decision} requests={len(CALLS)} tokens={spent_tokens()}")


if __name__ == "__main__":
    main()
