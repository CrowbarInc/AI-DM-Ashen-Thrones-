"""PR-ED turn profiler.

Profiles the production chat path on a disposable campaign. Provider calls stay
disabled unless --live is passed. Live mode is capped by the provider budget
environment variables set below. Secrets are never written.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4) if text else 0


def _nested_sizes(value, *, limit: int = 8) -> list[dict]:
    if not isinstance(value, dict):
        return []
    rows = []
    for key, child in value.items():
        blob = json.dumps(child, ensure_ascii=False)
        rows.append({"key": key, "chars": len(blob), "estimated_tokens": _estimate_tokens(blob)})
    rows.sort(key=lambda row: row["chars"], reverse=True)
    return rows[:limit]


def _payload_anatomy(content: str) -> dict:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    rows = []
    for key, value in payload.items():
        blob = json.dumps(value, ensure_ascii=False)
        rows.append({"key": key, "chars": len(blob), "estimated_tokens": _estimate_tokens(blob)})
    rows.sort(key=lambda row: row["chars"], reverse=True)
    instructions = payload.get("instructions")
    instruction_rows = [str(item) for item in instructions if isinstance(item, str)] if isinstance(instructions, list) else []
    unique_instructions = list(dict.fromkeys(instruction_rows))
    return {
        "largest_payload_keys": rows[:12],
        "instruction_count": len(instruction_rows),
        "unique_instruction_count": len(unique_instructions),
        "instruction_chars": sum(len(item) for item in instruction_rows),
        "longest_instructions": [
            {"chars": len(item), "prefix": item[:140]}
            for item in sorted(unique_instructions, key=len, reverse=True)[:8]
        ],
        "response_policy_children": _nested_sizes(payload.get("response_policy")),
        "turn_packet_children": _nested_sizes(payload.get("turn_packet")),
        "narrative_plan_children": _nested_sizes(payload.get("narrative_plan")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-output", type=int, default=600)
    parser.add_argument("--input-limit", type=int, default=80000)
    parser.add_argument("--only", default="")
    args = parser.parse_args()

    os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "0" if args.live else "1"
    os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "0" if args.live else "1"
    if args.live:
        os.environ["ASHEN_PROVIDER_REQUEST_LIMIT"] = "8"
        os.environ["ASHEN_PROVIDER_INPUT_TOKEN_LIMIT"] = str(args.input_limit)
        os.environ["ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT"] = "16000"
        os.environ["ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT"] = str(args.input_limit + 16000)
        os.environ["ASHEN_NARRATION_MAX_OUTPUT_TOKENS"] = str(args.max_output)
        os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(Path(args.out).with_suffix(".usage.jsonl"))

    from experiments.pr_dq.world import (
        COURTYARD_ID,
        GATE_ID,
        MARA_ID,
        STREET_ID,
        build_disposable_world,
    )
    from game import gm as gm_mod
    from game import storage
    from game.api import chat
    from game.config import DEFAULT_MODEL_NAME, ENABLE_MODEL_ROUTING, HIGH_PRECISION_MODEL_NAME
    from game.gm_retry import MAX_TARGETED_RETRY_ATTEMPTS
    from game.models import ChatRequest
    from game.provider_budget import snapshot

    tmp = Path(tempfile.mkdtemp(prefix="pr_ed_profile_"))
    data = tmp / "data"
    data.mkdir()
    (data / "scenes").mkdir()
    storage.BASE_DIR = tmp
    storage.DATA_DIR = data
    storage.WORLD_PATH = data / "world.json"
    storage.SCENES_DIR = data / "scenes"
    storage.CHARACTER_PATH = data / "character.json"
    storage.CAMPAIGN_PATH = data / "campaign.json"
    storage.SESSION_PATH = data / "session.json"
    storage.COMBAT_PATH = data / "combat.json"
    storage.CONDITIONS_PATH = data / "conditions.json"
    storage.SESSION_LOG_PATH = data / "session_log.jsonl"

    built = build_disposable_world()
    courtyard = built["scenes"][COURTYARD_ID]
    courtyard["scene"]["exits"] = [
        {
            "id": GATE_ID,
            "label": "courtyard gate",
            "aliases": ["gate", "the gate", "courtyard gate"],
            "target_scene_id": STREET_ID,
        }
    ]
    street = built["scenes"][STREET_ID]
    street["scene"]["exits"] = [
        {
            "id": "street_gate",
            "label": "waystation courtyard",
            "aliases": ["courtyard", "waystation courtyard", "back to the courtyard"],
            "target_scene_id": COURTYARD_ID,
        }
    ]
    session = copy.deepcopy(built["session"])
    session.setdefault("scene_state", {})["active_scene_id"] = COURTYARD_ID
    storage.save_session(session)
    storage._save_json(storage.WORLD_PATH, built["world"])
    storage._save_json(storage.CHARACTER_PATH, built["character"])
    storage._save_json(storage.COMBAT_PATH, built["combat"])
    storage._save_json(storage.CONDITIONS_PATH, {"conditions": []})
    storage._save_json(storage.CAMPAIGN_PATH, {"title": "PR-ED", "premise": "", "tone": "", "gm_guidance": []})
    for scene_id, envelope in built["scenes"].items():
        storage._save_json(storage.scene_path(scene_id), envelope)
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    calls: list[dict] = []
    persist_ms = {"save_session": 0, "save_world": 0, "save_session_count": 0, "save_world_count": 0}
    original_call = gm_mod.call_gpt
    original_save_session = storage.save_session
    original_save_world = storage.save_world

    def wrapped_call(messages, **kwargs):
        started = time.perf_counter()
        system = ""
        user = ""
        if isinstance(messages, list) and messages:
            system = str((messages[0] or {}).get("content") or "")
            if len(messages) > 1:
                user = str((messages[1] or {}).get("content") or "")
        anatomy = _payload_anatomy(user)
        record = {
            "purpose": kwargs.get("purpose"),
            "retry_attempt": kwargs.get("retry_attempt") or 0,
            "retry_reason": kwargs.get("retry_reason"),
            "message_count": len(messages) if isinstance(messages, list) else 0,
            "system_chars": len(system),
            "system_estimated_tokens": _estimate_tokens(system),
            "user_chars": len(user),
            "user_estimated_tokens": _estimate_tokens(user),
            "contract": "narration_only" if "NARRATION-ONLY RESPONSE CONTRACT" in system else "structured_realization",
            **anatomy,
        }
        result = original_call(messages, **kwargs)
        record["latency_ms"] = int(round((time.perf_counter() - started) * 1000))
        record["result_chars"] = len(str((result or {}).get("player_facing_text") or ""))
        calls.append(record)
        return result

    def wrapped_save_session(document):
        started = time.perf_counter()
        original_save_session(document)
        persist_ms["save_session"] += int(round((time.perf_counter() - started) * 1000))
        persist_ms["save_session_count"] += 1

    def wrapped_save_world(document):
        started = time.perf_counter()
        original_save_world(document)
        persist_ms["save_world"] += int(round((time.perf_counter() - started) * 1000))
        persist_ms["save_world_count"] += 1

    gm_mod.call_gpt = wrapped_call
    storage.save_session = wrapped_save_session
    storage.save_world = wrapped_save_world
    import game.api as api_mod

    api_mod.call_gpt = wrapped_call
    api_mod.save_session = wrapped_save_session
    api_mod.save_world = wrapped_save_world

    selected = {item.strip() for item in args.only.split(",") if item.strip()}
    scenarios = [
        ("simple_contextual_question", "Where are we?"),
        ("ordinary_movement", "I go through the courtyard gate."),
        ("movement_alternative_wording", "I make for the waystation courtyard."),
        ("npc_dialogue_initiation", "I ask Sergeant Mara about the road beyond the gate."),
        ("npc_followup", "Which road did you mean?"),
        ("ambiguous_inspection", "I look at it more closely."),
        ("clarification_continuation", "The lantern."),
        ("straightforward_consequential", "I examine the courtyard lantern."),
        ("compound_intention", "I examine the lantern and then go through the gate."),
        ("conversation_exit_then_activity", "I leave this conversation and look around."),
    ]
    if selected:
        scenarios = [row for row in scenarios if row[0] in selected]

    turns = []
    for index, (category, text) in enumerate(scenarios, start=1):
        before_calls = len(calls)
        before_session_saves = persist_ms["save_session"]
        before_world_saves = persist_ms["save_world"]
        before_usage = snapshot()
        started = time.perf_counter()
        response = chat(ChatRequest(text=text))
        elapsed = int(round((time.perf_counter() - started) * 1000))
        session_now = storage.load_session()
        traces = session_now.get("debug_traces") if isinstance(session_now.get("debug_traces"), list) else []
        latest = traces[-1] if traces else {}
        latency = latest.get("latency_ms") if isinstance(latest, dict) else {}
        gm = response.get("gm_output") if isinstance(response, dict) else {}
        resolution = response.get("resolution") if isinstance(response, dict) else {}
        meta = resolution.get("metadata") if isinstance(resolution, dict) and isinstance(resolution.get("metadata"), dict) else {}
        provider_calls = meta.get("provider_calls") if isinstance(meta.get("provider_calls"), dict) else {}
        turn_calls = calls[before_calls:]
        after_usage = snapshot()
        facing = str((gm or {}).get("player_facing_text") or "")
        turns.append(
            {
                "turn_id": index,
                "scenario_id": "pr_ed_courtyard",
                "category": category,
                "player_text": text,
                "elapsed_ms": elapsed,
                "latency_ms": latency if isinstance(latency, dict) else {},
                "narration_provider_calls": len(turn_calls),
                "interpretation_requests": provider_calls.get("interpretation_requests"),
                "narration_requests_meta": provider_calls.get("narration_requests"),
                "retries_meta": provider_calls.get("retries"),
                "retry_reasons": [row.get("retry_reason") for row in turn_calls if row.get("retry_attempt")],
                "prompt_estimated_input_tokens": sum(
                    row["system_estimated_tokens"] + row["user_estimated_tokens"] for row in turn_calls
                ),
                "persistence_ms": {
                    "save_session": persist_ms["save_session"] - before_session_saves,
                    "save_world": persist_ms["save_world"] - before_world_saves,
                },
                "usage_delta_requests": after_usage["requests"] - before_usage["requests"],
                "usage_delta_input_tokens": after_usage["input_tokens"] - before_usage["input_tokens"],
                "usage_delta_output_tokens": after_usage["output_tokens"] - before_usage["output_tokens"],
                "resolution_kind": resolution.get("kind") if isinstance(resolution, dict) else None,
                "scene_after": (session_now.get("scene_state") or {}).get("active_scene_id"),
                "active_target": (session_now.get("interaction_context") or {}).get("active_interaction_target_id")
                if isinstance(session_now.get("interaction_context"), dict)
                else None,
                "successful": bool(response.get("ok")) and bool(facing.strip()),
                "response_excerpt": facing[:400],
                "calls": turn_calls,
            }
        )

    report = {
        "live": bool(args.live),
        "model": {
            "default": DEFAULT_MODEL_NAME,
            "high_precision": HIGH_PRECISION_MODEL_NAME,
            "routing_enabled": ENABLE_MODEL_ROUTING,
        },
        "retry_ceiling": MAX_TARGETED_RETRY_ATTEMPTS,
        "manual_play_gpt_ceiling": 6,
        "narration_timeout": "openai_sdk_default",
        "provider_budget_defaults": {
            "request_limit_env": "ASHEN_PROVIDER_REQUEST_LIMIT",
            "input_default_when_limit_set": 8000,
            "output_default_when_limit_set": 2000,
            "total_default_when_limit_set": 10000,
            "narration_max_output_tokens_env": "ASHEN_NARRATION_MAX_OUTPUT_TOKENS",
            "narration_max_output_default": 600,
            "interpretation_max_output": 320,
        },
        "caching": "No application-level prompt cache. Provider prompt caching is not configured in call sites.",
        "instrumentation": "External wrappers around call_gpt, save_session, and save_world. No production edit.",
        "seed_ids": {"courtyard": COURTYARD_ID, "street": STREET_ID, "npc": MARA_ID},
        "turns": turns,
        "provider_snapshot": snapshot() if args.live else {"requests": 0, "note": "provider calls disabled"},
        "persist_totals": persist_ms,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "out": str(out),
                "live": args.live,
                "turns": len(turns),
                "narration_calls": sum(row["narration_provider_calls"] for row in turns),
                "median_elapsed_ms": sorted(row["elapsed_ms"] for row in turns)[len(turns) // 2],
            }
        )
    )


if __name__ == "__main__":
    main()
