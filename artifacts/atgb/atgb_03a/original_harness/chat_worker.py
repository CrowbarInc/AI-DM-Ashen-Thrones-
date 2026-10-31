"""Execute one ATGB scenario through POST /api/chat in an isolated data directory.

The game package is imported only after the data directory is accepted.
This module does not score replies and does not change production behavior.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from tools.atgb import UNAVAILABLE, UNCONTROLLED
from tools.atgb.budget import Budget, estimated_cost, stop_reason
from tools.atgb.driver import HOST_ORIGIN, LIVE_ORIGIN, build_chat_request
from tools.atgb.isolation import UnsafeBenchmarkDataDir, assert_imported_data_dir, assert_safe_benchmark_data_dir
from tools.atgb.results import recorded_or_missing, unavailable_telemetry
from tools.atgb.baseline import BaselineError, load_baseline, verify_files
from tools.atgb.preflight import check_start


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _state_slice() -> dict[str, Any]:
    from game.storage import load_log, load_session, load_world

    session = load_session()
    world = load_world()
    clues: list[str] = []
    overlays = session.get("runtime_scene_overlays") if isinstance(session, dict) else None
    if isinstance(overlays, dict):
        for overlay in overlays.values():
            if not isinstance(overlay, dict):
                continue
            for key in ("discovered_clue_ids", "discovered_clues"):
                value = overlay.get(key)
                if isinstance(value, list):
                    clues.extend(str(item) for item in value)
    interaction = session.get("interaction_context") if isinstance(session, dict) else None
    interlocutor = interaction.get("active_interaction_target_id") if isinstance(interaction, dict) else None
    world_flags = world.get("world_flags") if isinstance(world, dict) else None
    world_state = world.get("world_state") if isinstance(world, dict) else None
    flag_names = list(world_state.get("flags") or {}) if isinstance(world_state, dict) and isinstance(world_state.get("flags"), dict) else []
    return {
        "scene_id": session.get("active_scene_id") if isinstance(session, dict) else None,
        "discovered_clues": clues,
        "world_flag_names": [str(item) for item in world_flags] if isinstance(world_flags, list) else [],
        "world_state_flag_names": [str(item) for item in flag_names],
        "interlocutor": interlocutor,
        "transcript_entries": len(load_log()),
    }


def _first(mapping: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in mapping and mapping[name] not in (None, ""):
            return mapping[name]
    return UNAVAILABLE


def _telemetry_from(resolution: dict[str, Any]) -> dict[str, Any]:
    metadata = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    performance = metadata.get("performance") if isinstance(metadata.get("performance"), dict) else None
    if performance is None:
        telemetry = unavailable_telemetry()
    else:
        telemetry = {
            "elapsed_ms": recorded_or_missing(performance.get("elapsed_ms")),
            "provider_call_count": recorded_or_missing(performance.get("provider_call_count")),
            "input_tokens": recorded_or_missing(performance.get("input_tokens")),
            "output_tokens": recorded_or_missing(performance.get("output_tokens")),
            "retry_count": recorded_or_missing(performance.get("retry_count")),
            "estimated_cost": {"status": UNAVAILABLE, "value": None},
        }
    provider_calls = metadata.get("provider_calls") if isinstance(metadata.get("provider_calls"), dict) else {}
    telemetry["provider_call_detail"] = {
        "interpretation_requests": provider_calls.get("interpretation_requests", UNAVAILABLE),
        "narration_requests": provider_calls.get("narration_requests", UNAVAILABLE),
        "retries": provider_calls.get("retries", UNAVAILABLE),
    }
    return telemetry


def _capture_payload(payload: dict[str, Any], *, origin: str) -> dict[str, Any]:
    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
    metadata = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    gm_meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    accounting = gm_meta.get("provider_accounting") if isinstance(gm_meta.get("provider_accounting"), dict) else {}
    text = gm.get("player_facing_text") if isinstance(gm.get("player_facing_text"), str) else ""
    disabled = bool(gm_meta.get("provider_calls_disabled")) or "provider_calls_disabled" in tags
    request_count = accounting.get("request_count")
    telemetry = _telemetry_from(resolution)
    tokens_recorded = telemetry["input_tokens"]["status"] == "recorded" or telemetry["output_tokens"]["status"] == "recorded"
    request_sent = (isinstance(request_count, int) and request_count > 0) or tokens_recorded
    if disabled and not request_sent:
        request_sent = False
        count = telemetry["provider_call_count"]
        if count.get("status") == "recorded" and isinstance(count.get("value"), int) and count["value"] > 0:
            telemetry["provider_call_count_note"] = (
                "The host performance counter included a provider-disabled narration fallback. "
                "The counter is preserved. It is not evidence that a provider request was sent."
            )
    return {
        "response_text": text,
        "response_origin": origin,
        "simulated": False,
        "telemetry": telemetry,
        "provider_calls_disabled": disabled,
        "provider_request_sent": request_sent,
        "resolution_kind": resolution.get("kind", UNAVAILABLE),
        "communication_mode": _first(metadata, ("communication_mode", "textual_mode")),
        "conversational_decision": _first(metadata, ("conversational_decision", "decision", "category", "processing_outcome")),
        "addressee": _first(metadata, ("addressee", "speaker_id", "target_id", "interlocutor_id")),
        "authoritative_mutation": metadata.get("authoritative_mutation", UNAVAILABLE),
        "capture_status": "captured" if text else "missing_player_facing_text",
        "error": None if text else "The chat response did not include player-facing text.",
    }


def _provider_activity(turn: dict[str, Any]) -> bool:
    """True only when evidence says a provider request was sent."""

    if turn.get("provider_request_sent") is True:
        return True
    detail = turn["telemetry"].get("provider_call_detail") or {}
    for name in ("interpretation_requests", "narration_requests"):
        value = detail.get(name)
        if isinstance(value, int) and value > 0:
            return True
    return False


def _model_configuration() -> dict[str, Any]:
    from game.config import (
        DEFAULT_MODEL_NAME,
        ENABLE_MODEL_ROUTING,
        HIGH_PRECISION_MODEL_NAME,
        RETRY_ESCALATION_MODEL_NAME,
    )

    return {
        "default_model_name": DEFAULT_MODEL_NAME,
        "high_precision_model_name": HIGH_PRECISION_MODEL_NAME,
        "retry_escalation_model_name": RETRY_ESCALATION_MODEL_NAME,
        "model_routing_enabled": ENABLE_MODEL_ROUTING,
        "sampling": UNCONTROLLED,
        "api_key_recorded": False,
    }


def execute_job(job: dict[str, Any]) -> dict[str, Any]:
    mode = str(job["mode"])
    if mode == "live_provider" and not job.get("confirm_live_provider"):
        raise LiveRunBlocked("Live provider execution was not confirmed.")
    if mode not in {"provider_disabled_host", "live_provider"}:
        raise LiveRunBlocked("The chat worker does not run the simulated test double.")
    data_dir = Path(job["data_dir"])
    player_campaign = Path(job["player_campaign_dir"])
    repo = Path(job["repo_root"])
    assert_safe_benchmark_data_dir(data_dir, repo=repo, player_campaign_dir=player_campaign)
    os.environ["ASHEN_DATA_DIR"] = str(data_dir)
    if mode == "provider_disabled_host":
        os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
        os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
        os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
        os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
        os.environ["ASHEN_PROVIDER_REQUEST_LIMIT"] = "0"
        os.environ.pop("OPENAI_API_KEY", None)

    # Validate before game imports can silently synthesize missing bootstrap files.
    _, baseline = load_baseline(repo)
    verify_files(data_dir, baseline)
    from game.storage import DATA_DIR, load_log, load_session, load_world, load_combat

    assert_imported_data_dir(DATA_DIR, data_dir, repo=repo, player_campaign_dir=player_campaign)
    from game.campaign_reset import apply_new_campaign_hard_reset

    reset_meta = apply_new_campaign_hard_reset()
    preflight = check_start(repo=repo, data_dir=data_dir, imported_data_dir=DATA_DIR,
                            player_campaign_dir=player_campaign,
                            expected_location_id=job.get("expected_location_id"),
                            session=load_session(), world=load_world(), combat=load_combat(), log=load_log())
    if not preflight["ok"] or job.get("preflight_only"):
        return {"ok": preflight["ok"], "reset_invoked": True, "preflight": preflight,
                "context_establishment": "preflight_passed" if preflight["ok"] else "preflight_failed",
                "context_limitation": None if preflight["ok"] else "; ".join(preflight["critical_failures"]),
                "turns": [], "stop_reason": None if preflight["ok"] else "preflight_failed",
                "unexpected_provider_activity": False, "model_configuration": None}
    opening = _state_slice()
    expected = job.get("expected_location_id")
    if expected and opening.get("scene_id") != expected:
        return {
            "ok": False,
            "reset_invoked": True,
            "reset": {"campaign_run_id": reset_meta.get("campaign_run_id"), "session_id": reset_meta.get("session_id")},
            "context_establishment": "location_mismatch",
            "context_limitation": (
                f"The fresh campaign scene is {opening.get('scene_id')!r}. "
                f"The fixture requires {expected!r}. No scene was forced, and no player turn was submitted."
            ),
            "scene_after_reset": opening,
            "model_configuration": _model_configuration(),
            "turns": [],
            "stop_reason": None,
            "unexpected_provider_activity": False,
        }
    if mode == "provider_disabled_host":
        os.environ.pop("OPENAI_API_KEY", None)
    origin = HOST_ORIGIN if mode == "provider_disabled_host" else LIVE_ORIGIN
    from fastapi.testclient import TestClient
    from game.api import app

    turns: list[dict[str, Any]] = []
    unexpected = False
    stop = None
    with TestClient(app) as client:
        for spec in job["turns"]:
            if job.get("deadline_epoch") is not None and time.time() >= float(job["deadline_epoch"]):
                stop = "elapsed_time_ceiling"
                break
            used_calls = 0
            calls_known = True
            used_tokens = 0
            tokens_known = True
            used_cost = 0.0
            cost_known = True
            price_budget = Budget(
                max_provider_calls=job.get("max_provider_calls"),
                max_tokens=job.get("max_tokens"),
                max_estimated_cost=job.get("max_estimated_cost"),
                price_per_million_input_tokens=job.get("price_per_million_input_tokens"),
                price_per_million_output_tokens=job.get("price_per_million_output_tokens"),
            )
            for previous in turns:
                call = previous["telemetry"]["provider_call_count"]
                if call.get("status") == "recorded" and isinstance(call.get("value"), int):
                    used_calls += int(call["value"])
                else:
                    calls_known = False
                incoming = previous["telemetry"]["input_tokens"]
                outgoing = previous["telemetry"]["output_tokens"]
                if incoming.get("status") == "recorded" and outgoing.get("status") == "recorded":
                    used_tokens += int(incoming["value"]) + int(outgoing["value"])
                elif mode == "live_provider" and call.get("value"):
                    tokens_known = False
                priced = estimated_cost(previous["telemetry"], price_budget)
                if priced["status"] == "recorded" and isinstance(priced.get("value"), (int, float)):
                    used_cost += float(priced["value"])
                elif mode == "live_provider" and job.get("max_estimated_cost") is not None and call.get("value"):
                    cost_known = False
            if mode == "live_provider":
                stop = stop_reason(
                    budget=price_budget,
                    mode=mode,
                    elapsed_seconds=0.0,
                    provider_calls=used_calls if calls_known else None,
                    tokens=used_tokens if tokens_known else None,
                    token_status="recorded" if tokens_known else "unavailable",
                    cost=used_cost if cost_known else None,
                    cost_status="recorded" if cost_known else "unavailable",
                )
                if stop:
                    break
            before = _state_slice()
            request = build_chat_request(str(spec["player_input"]))
            response = client.post("/api/chat", json=request)
            body: dict[str, Any]
            try:
                parsed = response.json()
                body = parsed if isinstance(parsed, dict) else {}
            except Exception:
                body = {}
            captured = _capture_payload(body, origin=origin) if response.status_code == 200 and body.get("ok") is True else {
                "response_text": "",
                "response_origin": origin,
                "simulated": False,
                "telemetry": unavailable_telemetry(),
                "resolution_kind": UNAVAILABLE,
                "communication_mode": UNAVAILABLE,
                "conversational_decision": UNAVAILABLE,
                "addressee": UNAVAILABLE,
                "authoritative_mutation": UNAVAILABLE,
                "capture_status": "http_error",
                "error": f"POST /api/chat returned status {response.status_code}.",
            }
            captured["turn_id"] = spec["turn_id"]
            captured["request"] = request
            captured["http_status"] = response.status_code
            captured["state_evidence"] = {"before": before, "after": _state_slice()}
            if mode == "provider_disabled_host" and _provider_activity(captured):
                unexpected = True
                captured["error"] = "Provider activity was observed while providers were disabled. The scenario stopped."
                turns.append(captured)
                stop = "unexpected_provider_activity"
                break
            turns.append(captured)
            if captured["capture_status"] != "captured":
                stop = stop or "capture_failed"
                break
    return {
        "ok": not unexpected and stop not in {"capture_failed", "unexpected_provider_activity"},
        "preflight": preflight,
        "reset_invoked": True,
        "reset": {"campaign_run_id": reset_meta.get("campaign_run_id"), "session_id": reset_meta.get("session_id")},
        "context_establishment": "fresh_campaign_reset",
        "context_limitation": None,
        "scene_after_reset": opening,
        "model_configuration": _model_configuration(),
        "turns": turns,
        "stop_reason": stop,
        "unexpected_provider_activity": unexpected,
    }


class LiveRunBlocked(RuntimeError):
    """The worker refused to start a live or simulated request."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one isolated ATGB scenario through /api/chat.")
    parser.add_argument("--job", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    job = json.loads(args.job.read_text(encoding="utf-8"))
    try:
        payload = execute_job(job)
    except (UnsafeBenchmarkDataDir, LiveRunBlocked, BaselineError) as exc:
        payload = {
            "ok": False,
            "reset_invoked": False,
            "context_establishment": "refused",
            "context_limitation": str(exc),
            "turns": [],
            "stop_reason": "baseline_refused" if isinstance(exc, BaselineError) else "isolation_refused",
            "preflight": {"ok": False, "critical_failures": [str(exc)]},
            "unexpected_provider_activity": False,
            "model_configuration": None,
        }
    _write(args.output, payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
