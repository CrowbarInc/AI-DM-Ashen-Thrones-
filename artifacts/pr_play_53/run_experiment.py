"""PR-PLAY-53 live quarantine experiment.

Resolves investigations through the existing chat pipeline, then asks the
existing expression adapter for one quarantined prelude. Player-facing provider
calls stay disabled. This script does not modify canonical campaign files.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_53"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_PLAYTEST_DISABLE_SDK_RETRIES"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ["ASHEN_PROVIDER_REQUEST_LIMIT"] = "6"
os.environ["ASHEN_PROVIDER_INPUT_TOKEN_LIMIT"] = "8000"
os.environ["ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT"] = "1000"
os.environ["ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT"] = "10000"

LEDGER = OUT / "provider_usage.jsonl"
EVIDENCE = OUT / "hook_evidence"
RAW: list[dict] = []
CREATE_CALLS = 0

CANARIES = (
    "CANARY_UNDISCOVERED_CLUE",
    "CANARY_GM_NOTE",
    "CANARY_NPC_MOTIVE",
    "CANARY_HIDDEN_DESTINATION",
    "CANARY_QUEST_TWIST",
    "CANARY_MECHANICAL_ID",
    "CANARY_UNRELATED_WORLD",
)
NOTICE = "I examine the notice board."
BARREL = "I examine the rain barrel."
ROUTE = "The missing patrol was last seen taking the northwest mud track past the crates."


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
        return text
    if isinstance(value, dict):
        return {str(key): redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def write_json(name: str, value) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    text = json.dumps(redact(value), indent=2, ensure_ascii=False) + "\n"
    for blob in secret_blobs():
        if blob.decode() in text:
            raise RuntimeError("credential leaked into " + name)
    (OUT / name).write_text(text, encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def campaign_hashes() -> dict:
    data = ROOT / "data"
    files = {}
    if data.exists():
        for path in sorted(item for item in data.rglob("*") if item.is_file()):
            if "__pycache__" in path.parts:
                continue
            files[path.relative_to(data).as_posix()] = sha(path)
    env_path = ROOT / ".env"
    return {"files": files, "env_sha256": sha(env_path) if env_path.exists() else None}


def install_capture():
    import openai
    from openai import OpenAI as RealOpenAI

    class _Responses:
        def __init__(self, real):
            self._real = real

        def create(self, **kwargs):
            global CREATE_CALLS
            if CREATE_CALLS >= 6:
                raise RuntimeError("experiment request ceiling")
            CREATE_CALLS += 1
            started = now()
            perf = time.perf_counter()
            try:
                response = self._real.create(**kwargs)
            except Exception as exc:
                RAW.append({
                    "create_index": CREATE_CALLS,
                    "ok": False,
                    "started_at": started,
                    "completed_at": now(),
                    "latency_ms": round((time.perf_counter() - perf) * 1000, 3),
                    "error_type": type(exc).__name__,
                    "error": redact(str(exc))[:500],
                })
                raise
            payload = {
                "create_index": CREATE_CALLS,
                "ok": True,
                "started_at": started,
                "completed_at": now(),
                "latency_ms": round((time.perf_counter() - perf) * 1000, 3),
            }
            try:
                dumped = response.model_dump(mode="json") if hasattr(response, "model_dump") else {}
                payload["response"] = json.loads(json.dumps(dumped, default=str))
            except Exception as exc:
                payload["response"] = {
                    "id": getattr(response, "id", None),
                    "model": getattr(response, "model", None),
                    "output_text": getattr(response, "output_text", None),
                    "serialization_error": type(exc).__name__,
                }
            usage = getattr(response, "usage", None)
            payload["provider_usage"] = None if usage is None else {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }
            RAW.append(redact(payload))
            return response

    class _Client:
        def __init__(self, real):
            self.responses = _Responses(real.responses)

    def factory(*args, **kwargs):
        return _Client(RealOpenAI(*args, **kwargs))

    openai.OpenAI = factory


def isolate(tmp: Path):
    from game import storage

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
    if storage.SCENES_DIR.exists():
        shutil.rmtree(storage.SCENES_DIR)
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    for path in (ROOT / "data" / "scenes").glob("*.json"):
        shutil.copy2(path, storage.SCENES_DIR / path.name)


def seed(tmp: Path, scene_id: str) -> None:
    from game import storage
    from game.defaults import default_campaign, default_character, default_combat, default_conditions, default_session, default_world

    isolate(tmp)
    scene_path = storage.scene_path(scene_id)
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    hidden = list(scene["scene"].get("hidden_facts") or [])
    hidden.append("CANARY_HIDDEN_DESTINATION")
    scene["scene"]["hidden_facts"] = hidden
    scene["scene"]["gm_notes"] = ["CANARY_GM_NOTE"]
    scene["scene"]["private_notes"] = "CANARY_NPC_MOTIVE"
    scene["scene"]["discoverable_clues"] = list(scene["scene"].get("discoverable_clues") or [])
    scene["scene"]["discoverable_clues"].append({"id": "CANARY_MECHANICAL_ID", "text": "CANARY_UNDISCOVERED_CLUE"})
    storage._save_json(scene_path, scene)
    world = default_world()
    world["gm_only"] = {"motivation": "CANARY_NPC_MOTIVE", "quest": "CANARY_QUEST_TWIST"}
    world["unrelated_state"] = "CANARY_UNRELATED_WORLD"
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = scene_id
    session["visited_scene_ids"] = [scene_id]
    session["campaign_started"] = True
    session["turn_counter"] = 1
    storage.save_session(session)
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def snapshot():
    from game import storage

    return {
        "session": storage.load_session(),
        "world": storage.load_world(),
        "character": storage.load_character(),
        "combat": storage.load_combat(),
        "conditions": storage.load_conditions() if storage.CONDITIONS_PATH.exists() else None,
        "log": storage.load_log(),
    }


def scrub(value):
    if isinstance(value, dict):
        return {
            key: scrub(item)
            for key, item in value.items()
            if "timestamp" not in str(key) and "latency" not in str(key) and "stamp" not in str(key)
            and str(key) not in {"run_id", "trace_id", "campaign_run_id", "session_id", "canonical_gm_object_id"}
        }
    if isinstance(value, list):
        return [scrub(item) for item in value]
    return value


def diff(left, right, path="$"):
    if type(left) is not type(right):
        return [f"{path}: {type(left).__name__} != {type(right).__name__}"]
    if isinstance(left, dict):
        rows = []
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                rows.append(f"{path}.{key}: present {key in left} vs {key in right}")
            else:
                rows.extend(diff(left[key], right[key], f"{path}.{key}"))
        return rows
    if isinstance(left, list):
        if len(left) != len(right):
            return [f"{path}: len {len(left)} != {len(right)}"]
        rows = []
        for index, (a, b) in enumerate(zip(left, right)):
            rows.extend(diff(a, b, f"{path}[{index}]"))
        return rows
    if left != right:
        return [f"{path}: values differ"]
    return []


def mechanical(body: dict) -> dict:
    resolution = body.get("resolution") if isinstance(body.get("resolution"), dict) else {}
    changes = resolution.get("state_changes") if isinstance(resolution.get("state_changes"), dict) else {}
    return {
        "kind": resolution.get("kind"),
        "success": resolution.get("success"),
        "action_id": resolution.get("action_id"),
        "interactable_id": resolution.get("interactable_id"),
        "clue_id": resolution.get("clue_id"),
        "clue_text": resolution.get("clue_text"),
        "discovered_clues": resolution.get("discovered_clues"),
        "state_changes": {
            "clue_revealed": changes.get("clue_revealed"),
            "already_searched": changes.get("already_searched"),
            "skill_check_failed": changes.get("skill_check_failed"),
            "interactable_id": changes.get("interactable_id"),
        },
    }


def facing(body: dict) -> str:
    gm = body.get("gm_output") if isinstance(body.get("gm_output"), dict) else {}
    return str(gm.get("player_facing_text") or "")


def leaks(value) -> list[str]:
    blob = json.dumps(value, ensure_ascii=False)
    found = [item for item in CANARIES if item in blob]
    for token in ("notice_patrol_route", "CANARY_MECHANICAL_ID", "skill_check", "gm_notes"):
        if token in blob:
            found.append(token)
    hidden = (
        "An agent of a noble house is watching new arrivals from the square's edge.",
        "A contact tied to the Ash Cowl smuggling web is scouting the crowd for arcane talent.",
    )
    found.extend(item for item in hidden if item in blob)
    return found


def play(tmp: Path, text: str, *, live: bool, fault: str, label: str) -> dict:
    from fastapi.testclient import TestClient

    from game import api
    from game.quarantined_investigation_narration import (
        EVIDENCE_ENV,
        FAULT_ENV,
        GATE_ENV,
        LABEL_ENV,
        LIVE_ENV,
        clear_evidence,
        evidence_records,
    )

    seed(tmp, "frontier_gate")
    before = snapshot()
    clear_evidence()
    if live or fault:
        os.environ[GATE_ENV] = "1"
        os.environ[LIVE_ENV] = "1" if live else "0"
        os.environ[FAULT_ENV] = fault
        os.environ[LABEL_ENV] = label
        os.environ[EVIDENCE_ENV] = str(EVIDENCE)
    else:
        os.environ.pop(GATE_ENV, None)
        os.environ.pop(LIVE_ENV, None)
        os.environ[FAULT_ENV] = ""
    started_at = now()
    perf = time.perf_counter()
    client = TestClient(api.app)
    client.__enter__()
    try:
        response = client.post("/api/chat?ui_mode=player", json={"text": text})
        status = response.status_code
        body = response.json()
    finally:
        completed_at = now()
        elapsed_ms = round((time.perf_counter() - perf) * 1000, 3)
        try:
            client.__exit__(None, None, None)
        except Exception:
            pass
    after = snapshot()
    record = evidence_records()[-1] if evidence_records() else None
    return {
        "label": label,
        "player_text": text,
        "live": live,
        "fault": fault or None,
        "status_code": status,
        "started_at": started_at,
        "completed_at": completed_at,
        "turn_latency_ms": elapsed_ms,
        "player_facing": facing(body),
        "mechanical": mechanical(body),
        "state_differences_within_turn": diff(scrub(before), scrub(after)),
        "quarantine": record,
        "context_leaks": leaks({
            "hook_input": None if record is None else record.get("hook_input"),
            "message": None if record is None else (record.get("live_provider") or {}).get("sanitized_provider_user_message"),
        }),
    }


def preflight() -> dict:
    from game.config import DEFAULT_MODEL_NAME, get_openai_api_key
    from game.expressive_dialogue import _OUTPUT_CAP
    from game.gm import provider_timeout_seconds
    from game.provider_budget import provider_calls_disabled, sdk_retry_options

    key_present = False
    try:
        key_present = len(get_openai_api_key()) > 8
    except Exception:
        key_present = False
    dns_error = None
    try:
        socket.getaddrinfo("api.openai.com", 443)
    except Exception as exc:
        dns_error = type(exc).__name__
    blockers = []
    if not key_present:
        blockers.append("credentials_unavailable")
    if dns_error:
        blockers.append("provider_dns_unavailable:" + dns_error)
    if _OUTPUT_CAP > 1000:
        blockers.append("configured_output_cap_exceeds_experiment")
    if not DEFAULT_MODEL_NAME:
        blockers.append("model_unconfigured")
    report = {
        "time": now(),
        "provider": "openai",
        "adapter": "game.expressive_dialogue.request_expression",
        "model": DEFAULT_MODEL_NAME,
        "timeout_seconds": provider_timeout_seconds(),
        "sdk_retry_options": sdk_retry_options(),
        "host_retries_disabled": os.environ.get("ASHEN_DISABLE_PROVIDER_RETRIES") == "1",
        "output_cap_tokens": _OUTPUT_CAP,
        "experiment_output_ceiling": 1000,
        "experiment_request_ceiling": 6,
        "experiment_total_token_ceiling": 10000,
        "gameplay_provider_calls_disabled": provider_calls_disabled(),
        "usage_ledger": str(LEDGER),
        "key_present": key_present,
        "dns_ok": dns_error is None,
        "blockers": blockers,
        "estimated_cost_supported": False,
    }
    write_json("preflight.json", report)
    return report


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    before = campaign_hashes()
    write_json("campaign_hashes_before.json", before)
    report = preflight()
    if report["blockers"]:
        write_json("dispatch_aborted.json", {"time": now(), "blockers": report["blockers"], "provider_requests": 0})
        print(json.dumps({"aborted": report["blockers"]}, indent=2))
        return 2
    if LEDGER.exists():
        raise RuntimeError("usage ledger already exists")
    os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(LEDGER)
    from game.provider_budget import initialize_accounting
    from game.quarantined_investigation_narration import reset_live_budget

    initialize_accounting()
    install_capture()
    reset_live_budget()
    tmp = OUT / "tmp_runs"
    if tmp.exists():
        shutil.rmtree(tmp)
    results = []
    try:
        baseline_a = play(tmp / "a_base", NOTICE, live=False, fault="", label="A_baseline")
        live_a = play(tmp / "a_live", NOTICE, live=True, fault="", label="A_success")
        results.extend([baseline_a, live_a])
        write_json("scenarios_partial.json", results)
        live_record = live_a.get("quarantine") or {}
        provider = live_record.get("live_provider") or {}
        error = str(provider.get("provider_error") or "")
        if error in {"AuthenticationError", "PermissionDeniedError", "APIConnectionError"} or CREATE_CALLS == 0:
            live_a["stopped_remaining"] = error or "no_provider_request"
        else:
            baseline_b = play(tmp / "b_base", BARREL, live=False, fault="", label="B_baseline")
            live_b = play(tmp / "b_live", BARREL, live=True, fault="", label="B_limited")
            results.extend([baseline_b, live_b])
        failure = play(tmp / "c_fault", NOTICE, live=False, fault="timeout", label="C_provider_failure")
        results.append(failure)
    except Exception:
        write_json("experiment_exception.json", {"time": now(), "traceback": traceback.format_exc()[-4000:], "create_calls": CREATE_CALLS})
        raise
    finally:
        after = campaign_hashes()
        changed = sorted(name for name, digest in before["files"].items() if after["files"].get(name) != digest)
        changed += sorted(set(after["files"]) - set(before["files"]))
        write_json("campaign_hashes_after.json", {"changed": changed, "env_unchanged": before["env_sha256"] == after["env_sha256"]})
    pairs = []
    by_label = {row["label"]: row for row in results}
    for live_label, base_label in (("A_success", "A_baseline"), ("B_limited", "B_baseline")):
        if live_label not in by_label or base_label not in by_label:
            continue
        live_row = by_label[live_label]
        base_row = by_label[base_label]
        pairs.append({
            "scenario": live_label,
            "player_facing_identical": live_row["player_facing"] == base_row["player_facing"],
            "mechanical_identical": live_row["mechanical"] == base_row["mechanical"],
            "within_turn_state_differences": live_row["state_differences_within_turn"],
            "context_leaks": live_row["context_leaks"],
            "route_in_limited_context": ROUTE in json.dumps((live_row.get("quarantine") or {}).get("live_provider") or {}),
        })
    from game.provider_budget import snapshot as usage_snapshot

    summary = {
        "time": now(),
        "create_calls": CREATE_CALLS,
        "usage": usage_snapshot(),
        "pairs": pairs,
        "results": results,
        "raw_provider_responses": RAW,
    }
    write_json("scenario_results.json", summary)
    print(json.dumps({
        "create_calls": CREATE_CALLS,
        "usage": {
            "requests": summary["usage"].get("dispatched_requests"),
            "input_tokens": summary["usage"].get("input_tokens"),
            "output_tokens": summary["usage"].get("output_tokens"),
            "total_tokens": summary["usage"].get("total_tokens"),
        },
        "pairs": pairs,
        "diagnostics": [
            {
                "label": row["label"],
                "diagnostic": None if not row.get("quarantine") else row["quarantine"].get("diagnostic"),
                "facing": row["player_facing"][:120],
                "mechanical": row["mechanical"],
            }
            for row in results
        ],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
