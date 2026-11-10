"""PR-PLAY-50 quarantined narration experiment.

This harness is not a gameplay entry point. It never starts a campaign session.
Provider text is written only under artifacts/pr_play_50.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_50"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Process-local controls. These do not edit .env, models, or token ceilings.
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_PLAYTEST_DISABLE_SDK_RETRIES"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ.pop("ASHEN_DATA_DIR", None)

MAX_REQUESTS = 4
LEDGER = OUT / "provider_ledger.jsonl"
SYSTEM_PROMPT = (
    "The investigation is already complete. Its mechanical result is authoritative. "
    "Write one descriptive prelude of about 20 to 60 words, and end on a complete sentence. "
    "You are writing prose only. Do not decide the outcome. "
    "Do not invent rewards, possessions, currency, health, conditions, travel, quests, or any other mechanical change. "
    "Do not invent definitive conclusions, culprits, counts, links, or destinations. "
    "Preserve uncertainty that the result leaves open. "
    "Do not reveal information that is absent from the supplied context. "
    "Harmless incidental atmosphere is allowed and creates no new facts or mechanics. "
    "Avoid generic filler. Do not repeat the authorized discovery; the engine appends that sentence separately."
)
PLAN = (
    {"request_id": "A1", "sample": "A1", "investigation_id": "notice_board", "fixture": "frontier_gate"},
    {"request_id": "A2", "sample": "A2", "investigation_id": "notice_board", "fixture": "frontier_gate"},
    {"request_id": "B1", "sample": "B1", "investigation_id": "footprints", "fixture": "old_milestone"},
    {"request_id": "B2", "sample": "B2", "investigation_id": "footprints", "fixture": "old_milestone"},
)
CANARIES = (
    "UNSEEN_CLUE_K42",
    "PRIVATE_GM_NOTE_K42",
    "NPC_MOTIVE_K42",
    "HIDDEN_DESTINATION_K42",
    "PRIVATE_WORLD_K42",
    "QUEST_TWIST_K42",
)
SINKS = (
    "game.api._apply_post_gm_updates",
    "game.api.remember_recent_contextual_leads",
    "game.api.promote_accepted_bounded_improvisation",
    "game.api._validate_gm_scene_update_for_legacy_adoption",
    "game.api._validate_gm_world_updates_for_legacy_adoption",
    "game.api.apply_normalized_world_updates",
    "game.gm.remember_recent_contextual_leads",
    "game.world.apply_world_updates",
    "game.world.apply_resolution_world_updates",
    "game.world.apply_normalized_world_updates",
    "game.storage.save_campaign",
    "game.storage.save_character",
    "game.storage.save_session",
    "game.storage.save_world",
    "game.storage.save_combat",
    "game.storage.save_scene",
    "game.bounded_improvisation.promote_accepted_bounded_improvisation",
    "game.clues.apply_authoritative_clue_discovery",
    "game.exploration.resolve_exploration_action",
    "game.expressive_dialogue.apply_expression",
    "game.leads.promote_lead_confidence",
    "game.leads.promote_session_lead_confidence",
    "game.npc_promotion.promote_scene_actor_to_npc",
    "game.world_progression.apply_progression_delta",
    "game.campaign_reset.apply_new_campaign_hard_reset",
)
_SINK_CALLS: list[str] = []
_CREATE_CALLS = 0
_RAW_RESPONSES: list[dict] = []


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def secret_blobs() -> list[bytes]:
    blobs = []
    for name in ("OPENAI_API_KEY", "API_KEY", "OPENAI_TOKEN"):
        value = os.environ.get(name, "").strip()
        if len(value) > 8:
            blobs.append(value.encode())
    return blobs


def redact(value):
    if isinstance(value, str):
        text = value
        for blob in secret_blobs():
            text = text.replace(blob.decode(), "[REDACTED]")
        text = re.sub(r"sk-(?:proj-)?[A-Za-z0-9_\-]{12,}", "[REDACTED]", text)
        return text
    if isinstance(value, dict):
        return {str(k): redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, tuple):
        return [redact(v) for v in value]
    return value


def dump(name: str, value) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    text = json.dumps(redact(value), indent=2, ensure_ascii=False) + "\n"
    for blob in secret_blobs():
        if blob.decode() in text:
            raise RuntimeError("credential leaked into evidence write")
    (OUT / name).write_text(text, encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def campaign_snapshot() -> dict:
    from game.storage import DATA_DIR

    files = {}
    if DATA_DIR.exists():
        for path in sorted(p for p in DATA_DIR.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
            files[path.relative_to(DATA_DIR).as_posix()] = {
                "sha256": sha(path),
                "bytes": path.stat().st_size,
            }
    env_path = ROOT / ".env"
    return {
        "time": now(),
        "data_dir": str(DATA_DIR),
        "files": files,
        "env_file_sha256": sha(env_path) if env_path.exists() else None,
    }


def load_fixture(name: str) -> dict:
    path = ROOT / "artifacts" / "pr_play_49" / f"evidence_fixture_{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def narration_payload(row: dict) -> dict:
    from game.gm import _scene_layers

    public, _, _ = _scene_layers(row["scene"])
    return {
        "scene": {
            "public": public,
            "discovered_clues": [{"text": t} for t in row.get("known") or []],
            "discoverable_clues": row["scene"]["scene"].get("discoverable_clues", []),
        },
        "world": {"private": CANARIES[4]},
        "metadata": {"gm_notes": CANARIES[1]},
        "unexpected": {"nested": {"public": {"summary": CANARIES[5]}}, CANARIES[0]: CANARIES[1]},
    }


def withheld_strings(row: dict) -> list[str]:
    scene = row["scene"]["scene"]
    withheld = list(CANARIES)
    withheld.extend(str(x) for x in scene.get("hidden_facts") or [] if str(x).strip())
    for clue in scene.get("discoverable_clues") or []:
        if isinstance(clue, dict) and clue.get("id"):
            withheld.append(str(clue["id"]))
    for exit_row in scene.get("exits") or []:
        if isinstance(exit_row, dict) and exit_row.get("target_scene_id"):
            withheld.append(str(exit_row["target_scene_id"]))
    hint = str((row.get("resolution") or {}).get("hint") or "")
    if hint:
        withheld.append(hint)
    # Authorized discovery text is allowed. Remove it from the withheld scan.
    allowed = set()
    for clue in (row.get("resolution") or {}).get("discovered_clues") or []:
        allowed.add(clue)
    return [item for item in dict.fromkeys(withheld) if item not in allowed and item not in " ".join(allowed)]


def build_contexts() -> dict:
    from game.anchored_investigation_narration import authorize_anchored_investigation, prelude_request
    from game.config import DEFAULT_MODEL_NAME
    from game.expressive_dialogue import _OUTPUT_CAP, request_expression
    from game.gm import provider_timeout_seconds
    from game.provider_budget import limits, provider_calls_disabled

    source = inspect.getsource(request_expression)
    temperature = re.search(r"temperature\s*=\s*([0-9.]+)", source)
    contexts = {}
    for spec in PLAN:
        if spec["fixture"] in contexts:
            continue
        row = load_fixture(spec["fixture"])
        contract = authorize_anchored_investigation(row["resolution"], narration_payload(row))
        request = prelude_request(contract)
        saved = row["prelude_request"]
        if request != saved:
            raise RuntimeError(f"projection drifted for {spec['fixture']}")
        user = {
            "player_action": row["player"],
            "requested_prelude_length": "about 20-60 words",
            "authorized_narration_projection": request,
        }
        message = json.dumps(user, ensure_ascii=False)
        leaked = [item for item in withheld_strings(row) if item and item in message]
        leaked += [item for item in CANARIES if item in message]
        contexts[spec["fixture"]] = {
            "player_action": row["player"],
            "anchor_text": contract.anchors[0].text,
            "anchors": [
                {"order": a.order, "source": a.source, "status": a.status, "text": a.text}
                for a in contract.anchors
            ],
            "prelude_request": request,
            "provider_user_message": user,
            "withheld_checked": withheld_strings(row),
            "leaked_into_provider_message": leaked,
            "saved_projection_matches": True,
        }
    ceilings = limits()
    estimated_input = max(
        1,
        (len(SYSTEM_PROMPT) + len(json.dumps(contexts["frontier_gate"]["provider_user_message"]))) // 4,
    )
    return {
        "configured_model": DEFAULT_MODEL_NAME,
        "provider": "openai",
        "adapter": "game.expressive_dialogue.request_expression",
        "adapter_purpose": "expression",
        "temperature": float(temperature.group(1)) if temperature else None,
        "max_output_tokens": _OUTPUT_CAP,
        "timeout_seconds": provider_timeout_seconds(),
        "sdk_max_retries": 0,
        "provider_calls_disabled": provider_calls_disabled(),
        "existing_request_limit_before_experiment_ceiling": os.environ.get("ASHEN_PROVIDER_REQUEST_LIMIT"),
        "existing_input_token_limit": os.environ.get("ASHEN_PROVIDER_INPUT_TOKEN_LIMIT"),
        "existing_output_token_limit": os.environ.get("ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT"),
        "existing_total_token_limit": os.environ.get("ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT"),
        "code_default_ceilings_when_request_limit_set": ceilings,
        "estimated_input_tokens_per_request": estimated_input,
        "estimated_output_reservation": _OUTPUT_CAP,
        "system_prompt": SYSTEM_PROMPT,
        "contexts": contexts,
        "adapter_source_has_temperature_0_2": "temperature=0.2" in source.replace(" ", ""),
        "adapter_does_not_call_gameplay_sinks": not any(
            name.split(".")[-1] in source
            for name in (
                "save_session",
                "save_world",
                "save_character",
                "resolve_exploration_action",
                "apply_expression",
                "apply_world_updates",
                "_apply_post_gm_updates",
            )
        ),
    }


def install_sinks() -> list[str]:
    import importlib

    missing = []
    for qual in SINKS:
        module_name, func_name = qual.rsplit(".", 1)
        module = importlib.import_module(module_name)
        original = getattr(module, func_name, None)
        if original is None or getattr(original, "_pr50_wrapped", False):
            if original is None:
                missing.append(qual)
            continue

        def wrapper(*args, __qual=qual, **kwargs):
            _SINK_CALLS.append(__qual)
            raise RuntimeError("quarantine_sink_called:" + __qual)

        wrapper._pr50_wrapped = True
        setattr(module, func_name, wrapper)
    return missing


def install_capture():
    import openai
    from openai import OpenAI as RealOpenAI

    class _Responses:
        def __init__(self, real):
            self._real = real

        def create(self, **kwargs):
            global _CREATE_CALLS
            if _CREATE_CALLS >= MAX_REQUESTS:
                raise RuntimeError("provider request ceiling exceeded")
            _CREATE_CALLS += 1
            try:
                response = self._real.create(**kwargs)
            except Exception as exc:
                _RAW_RESPONSES.append({
                    "create_index": _CREATE_CALLS,
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error": redact(str(exc))[:500],
                })
                raise
            payload = {"create_index": _CREATE_CALLS, "ok": True}
            try:
                dumped = response.model_dump(mode="json") if hasattr(response, "model_dump") else {
                    "id": getattr(response, "id", None),
                    "model": getattr(response, "model", None),
                    "output_text": getattr(response, "output_text", None),
                    "status": getattr(response, "status", None),
                }
                payload["response"] = json.loads(json.dumps(dumped, default=str))
            except Exception as exc:
                payload["response"] = {
                    "id": getattr(response, "id", None),
                    "model": getattr(response, "model", None),
                    "output_text": getattr(response, "output_text", None),
                    "status": getattr(response, "status", None),
                    "serialization_error": type(exc).__name__,
                }
            usage = getattr(response, "usage", None)
            payload["provider_usage"] = None if usage is None else {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }
            _RAW_RESPONSES.append(payload)
            return response

    class _Client:
        def __init__(self, real):
            self.responses = _Responses(real.responses)

    real_openai = RealOpenAI

    def factory(*args, **kwargs):
        # Pass the constructor through unchanged. Do not log args or kwargs.
        return _Client(real_openai(*args, **kwargs))

    # request_expression imports OpenAI from openai at call time.
    openai.OpenAI = factory
    return factory


def preflight() -> dict:
    built = build_contexts()
    leaks = {
        name: ctx["leaked_into_provider_message"]
        for name, ctx in built["contexts"].items()
        if ctx["leaked_into_provider_message"]
    }
    missing = install_sinks()
    before = campaign_snapshot()
    # Projection and sink installation must not themselves mutate campaign files.
    after = campaign_snapshot()
    changed = sorted(set(before["files"]) ^ set(after["files"]))
    changed += sorted(
        name for name in before["files"]
        if name in after["files"] and before["files"][name] != after["files"][name]
    )
    estimated = built["estimated_input_tokens_per_request"]
    output_cap = built["max_output_tokens"]
    ceilings = built["code_default_ceilings_when_request_limit_set"]
    # Do not raise configured ceilings. If the environment already set a lower one, honor it.
    env_input = os.environ.get("ASHEN_PROVIDER_INPUT_TOKEN_LIMIT")
    env_output = os.environ.get("ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT")
    env_total = os.environ.get("ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT")
    env_requests = os.environ.get("ASHEN_PROVIDER_REQUEST_LIMIT")
    input_ceiling = int(env_input) if env_input else (ceilings[1] if ceilings else 8000)
    output_ceiling = int(env_output) if env_output else (ceilings[2] if ceilings else 2000)
    total_ceiling = int(env_total) if env_total else (ceilings[3] if ceilings else 10000)
    request_ceiling = int(env_requests) if env_requests else MAX_REQUESTS
    fits = (
        request_ceiling >= MAX_REQUESTS
        and MAX_REQUESTS * estimated <= input_ceiling
        and MAX_REQUESTS * output_cap <= output_ceiling
        and MAX_REQUESTS * (estimated + output_cap) <= total_ceiling
    )
    blockers = []
    if leaks:
        blockers.append("hidden_information_in_provider_message")
    if built["provider_calls_disabled"]:
        blockers.append("provider_calls_disabled")
    if not built["configured_model"]:
        blockers.append("model_unconfigured")
    if built["temperature"] != 0.2 or built["max_output_tokens"] != 80:
        blockers.append("adapter_settings_unexpected")
    if not built["adapter_does_not_call_gameplay_sinks"]:
        blockers.append("adapter_references_gameplay_sink")
    if changed or before["env_file_sha256"] != after["env_file_sha256"] or _SINK_CALLS:
        blockers.append("preflight_state_mutation")
    if not fits:
        blockers.append("request_does_not_fit_existing_ceiling")
    if _CREATE_CALLS:
        blockers.append("provider_called_during_preflight")
    report = {
        "time": now(),
        "phase": "preflight",
        "provider_requests": 0,
        "isolation_passed": not blockers,
        "blockers": blockers,
        "missing_sinks": missing,
        "sink_calls": list(_SINK_CALLS),
        "campaign_snapshot": before,
        "campaign_unchanged_during_preflight": not changed and before["env_file_sha256"] == after["env_file_sha256"],
        "preflight_changed_files": changed,
        "fits_existing_ceilings": fits,
        "ceilings_honored": {
            "requests": request_ceiling,
            "input_tokens": input_ceiling,
            "output_tokens": output_ceiling,
            "total_tokens": total_ceiling,
        },
        "no_campaign_session": True,
        "mechanical_resolver_invoked": False,
        **{k: v for k, v in built.items() if k != "contexts"},
        "contexts": built["contexts"],
    }
    dump("preflight.json", report)
    print(json.dumps({
        "isolation_passed": report["isolation_passed"],
        "blockers": blockers,
        "model": built["configured_model"],
        "temperature": built["temperature"],
        "max_output_tokens": built["max_output_tokens"],
        "estimated_input_tokens": estimated,
        "leaks": leaks,
        "files": len(before["files"]),
        "provider_requests": 0,
    }, indent=2))
    return report


def dispatch() -> dict:
    report = preflight()
    if not report["isolation_passed"]:
        dump("dispatch_aborted.json", {"time": now(), "reason": report["blockers"], "provider_requests": 0})
        print("DISPATCH ABORTED")
        return report
    if LEDGER.exists():
        raise RuntimeError("usage ledger already exists; refusing to append or reset it")
    os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(LEDGER)
    # A process-local cap of 4. Never raise an already-lower environment ceiling.
    existing = os.environ.get("ASHEN_PROVIDER_REQUEST_LIMIT", "").strip()
    if existing and int(existing) < MAX_REQUESTS:
        raise RuntimeError("existing request ceiling is below the four-request plan")
    os.environ["ASHEN_PROVIDER_REQUEST_LIMIT"] = str(min(int(existing), MAX_REQUESTS) if existing else MAX_REQUESTS)
    from game.expressive_dialogue import request_expression
    from game.provider_budget import initialize_accounting

    initialize_accounting()
    install_capture()
    before = campaign_snapshot()
    records = []
    prior_text = []
    for spec in PLAN:
        if _CREATE_CALLS >= MAX_REQUESTS:
            break
        ctx = report["contexts"][spec["fixture"]]
        user = json.dumps(ctx["provider_user_message"], ensure_ascii=False)
        if any(text and text in user for text in prior_text):
            raise RuntimeError("later request contains an earlier sample")
        if any(item for item in ctx["leaked_into_provider_message"]):
            raise RuntimeError("hidden information reached provider message")
        started = time.perf_counter()
        result = request_expression({"prompt": {"system": SYSTEM_PROMPT, "user": user}})
        outer_ms = round((time.perf_counter() - started) * 1000, 3)
        raw = _RAW_RESPONSES[-1] if _RAW_RESPONSES else None
        text = result.get("text") if isinstance(result, dict) else ""
        record = {
            "request_id": spec["request_id"],
            "sample": spec["sample"],
            "investigation_id": spec["investigation_id"],
            "fixture": spec["fixture"],
            "player_action": ctx["player_action"],
            "authoritative_discovery": ctx["anchor_text"],
            "provider": "openai",
            "configured_model": report["configured_model"],
            "generation_settings": {
                "temperature": report["temperature"],
                "max_output_tokens": report["max_output_tokens"],
                "timeout_seconds": report["timeout_seconds"],
                "sdk_max_retries": 0,
                "adapter": report["adapter"],
            },
            "sanitized_provider_messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            "raw_provider_response": raw,
            "extracted_narration_text": text,
            "adapter_result": {k: v for k, v in result.items() if k != "text"} if isinstance(result, dict) else {},
            "provider_reported_usage": (result.get("usage") if isinstance(result, dict) else None),
            "wall_clock_latency_ms": result.get("latency_ms") if isinstance(result, dict) else None,
            "outer_latency_ms": outer_ms,
            "provider_error": None if result.get("ok") else {
                "sent": result.get("sent"),
                "reason": result.get("reason"),
                "error": result.get("error"),
            },
            "create_calls_after": _CREATE_CALLS,
            "sink_calls_after": list(_SINK_CALLS),
            "evidence_timestamp": now(),
            "validator_not_run": True,
            "assembled_preview": None,
            "fallback_output": None,
        }
        records.append(record)
        dump("requests_partial.json", records)
        if isinstance(text, str) and text:
            prior_text.append(text)
        # Authentication or connection failure will not succeed on a later sample.
        # Do not spend the remaining ceiling repeating one unavailable-service error.
        error_name = str((record["provider_error"] or {}).get("error") or "")
        if error_name in {"AuthenticationError", "PermissionDeniedError", "APIConnectionError"}:
            record["stopped_remaining_plan"] = "configured provider unavailable; no fallback and no retry"
            break
    after = campaign_snapshot()
    from game.provider_budget import snapshot

    changed = sorted(set(before["files"]) ^ set(after["files"]))
    changed += sorted(
        name for name in before["files"]
        if name in after["files"] and before["files"][name] != after["files"][name]
    )
    summary = {
        "time": now(),
        "provider_create_calls": _CREATE_CALLS,
        "successful_responses": sum(1 for row in records if row["raw_provider_response"] and row["raw_provider_response"].get("ok") and row["extracted_narration_text"]),
        "records": len(records),
        "sink_calls": list(_SINK_CALLS),
        "campaign_unchanged": not changed and before["env_file_sha256"] == after["env_file_sha256"],
        "changed_files": changed,
        "env_file_unchanged": before["env_file_sha256"] == after["env_file_sha256"],
        "accounting": snapshot(),
        "stopped_early": len(records) < MAX_REQUESTS,
    }
    dump("state_before.json", before)
    dump("state_after.json", after)
    dump("requests.json", records)
    dump("dispatch_summary.json", summary)
    print(json.dumps({
        "provider_create_calls": _CREATE_CALLS,
        "records": len(records),
        "successful_text": summary["successful_responses"],
        "campaign_unchanged": summary["campaign_unchanged"],
        "sink_calls": summary["sink_calls"],
        "stopped_early": summary["stopped_early"],
    }, indent=2))
    return summary


def main() -> int:
    phase = sys.argv[1] if len(sys.argv) > 1 else "preflight"
    try:
        if phase == "preflight":
            report = preflight()
            return 0 if report["isolation_passed"] else 2
        if phase == "dispatch":
            dispatch()
            return 0
        raise SystemExit("phase must be preflight or dispatch")
    except Exception:
        dump("experiment_exception.json", {"time": now(), "trace": redact(traceback.format_exc()), "create_calls": _CREATE_CALLS})
        print("EXPERIMENT EXCEPTION")
        print(redact(traceback.format_exc())[-2000:])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
