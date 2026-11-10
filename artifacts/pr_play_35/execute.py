"""PR-PLAY-35 observational live gameplay controller.

Uses the existing isolated-store harness and production worker. Does not change
gameplay, prompts, provider routing, or fixtures. Does not retry a turn.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from tools.atgb.baseline import digest, load_baseline
from tools.atgb.isolation import player_campaign_dir_from_env, prepare_isolated_store
from tools.playtest import runner

MISSION_REQUEST_CEILING = 10
HTTP_TIMEOUT = 90
TURNS = (
    {"step_id": "T1", "player_input": "What is available here?",
     "intent": "available offerings"},
    {"step_id": "T2", "player_input": "Have you heard any interesting rumors lately?",
     "intent": "local rumors"},
    {"step_id": "T3", "player_input": "I want to investigate the footprints.",
     "intent": "investigate footprints"},
    {"step_id": "T4", "player_input": "I want to follow the trail connected to the missing patrol.",
     "intent": "follow missing patrol lead"},
    {"step_id": "T5", "player_input": "I examine the footprints here more carefully.",
     "intent": "examine footprints at destination"},
)
INTERPRETER_IMAGES = {"python.exe", "pythonw.exe", "py.exe"}
K = ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class Entry(ctypes.Structure):
    _fields_ = [
        ("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("th32ProcessID", w.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", w.DWORD),
        ("cntThreads", w.DWORD), ("th32ParentProcessID", w.DWORD),
        ("pcPriClassBase", w.LONG), ("dwFlags", w.DWORD), ("szExeFile", w.WCHAR * 260),
    ]


K.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
K.CreateToolhelp32Snapshot.restype = w.HANDLE
K.Process32FirstW.argtypes = K.Process32NextW.argtypes = [w.HANDLE, ctypes.POINTER(Entry)]
K.CloseHandle.argtypes = [w.HANDLE]
K.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
K.OpenProcess.restype = w.HANDLE
K.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)]


def secrets_from(env):
    return [value for key, value in env.items()
            if isinstance(value, str) and len(value) > 8
            and any(part in key.lower() for part in ("key", "token", "secret", "password", "credential"))]


def redact(text, hidden):
    for value in hidden:
        if value:
            text = text.replace(value, "[REDACTED]")
    return text


def dump(path, value, hidden):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, indent=2, default=str)
    path.write_text(redact(raw, hidden) + "\n", encoding="utf-8")


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    rows = {}
    for folder in ("game", "tools/playtest", "tools/atgb"):
        for path in (ROOT / folder).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            rows[path.relative_to(ROOT).as_posix()] = sha256_file(path)
    return rows


def campaign_fingerprint(path):
    resolved = Path(path)
    view = {"path": str(resolved), "exists": resolved.exists()}
    if not resolved.exists():
        return view
    files = {}
    for file in resolved.rglob("*"):
        if not file.is_file() or "__pycache__" in file.parts or file.name.startswith("."):
            continue
        rel = file.relative_to(resolved).as_posix()
        size = file.stat().st_size
        row = {"bytes": size}
        if size <= 2 * 1024 * 1024 and file.suffix in {".json", ".jsonl", ".md", ".txt"}:
            row["sha256"] = sha256_file(file)
        files[rel] = row
    view["file_count"] = len(files)
    view["files"] = files
    return view


def process_table():
    handle = K.CreateToolhelp32Snapshot(2, 0)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    result = {}
    try:
        entry = Entry()
        entry.dwSize = ctypes.sizeof(entry)
        more = K.Process32FirstW(handle, ctypes.byref(entry))
        if not more:
            raise ctypes.WinError(ctypes.get_last_error())
        while more:
            result[entry.th32ProcessID] = {
                "pid": entry.th32ProcessID,
                "parent_pid": entry.th32ParentProcessID,
                "image": entry.szExeFile,
            }
            more = K.Process32NextW(handle, ctypes.byref(entry))
    finally:
        K.CloseHandle(handle)
    return result


def image_of(pid):
    handle = K.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return {"query_error": ctypes.get_last_error()}
    try:
        image = ctypes.create_unicode_buffer(32768)
        size = w.DWORD(len(image))
        if K.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)):
            return {"executable": image.value}
        return {"query_error": ctypes.get_last_error()}
    finally:
        K.CloseHandle(handle)


def ownership(process):
    table = process_table()
    pid = process.pid
    row = table.get(pid, {})
    children = []
    for item in table.values():
        if item["parent_pid"] == pid:
            child = dict(item)
            child.update(image_of(child["pid"]))
            children.append(child)
    worker = image_of(pid)
    return {
        "controller_pid": os.getpid(),
        "popen_pid": pid,
        "parent_pid": row.get("parent_pid"),
        "reported_image": row.get("image"),
        "worker_executable": worker.get("executable"),
        "base_executable": getattr(sys, "_base_executable", None),
        "children": children,
        "interpreter_children": [
            child for child in children
            if str(child.get("image") or "").lower() in INTERPRETER_IMAGES
        ],
        "process_alive": process.poll() is None,
    }


def same_path(left, right):
    if not left or not right:
        return False
    return str(left).replace("\\", "/").lower() == str(right).replace("\\", "/").lower()


def unwrap(document):
    if isinstance(document, dict) and isinstance(document.get("payload"), dict) and "persistence_version" in document:
        return document["payload"]
    return document if isinstance(document, dict) else {}


def clue_states(value):
    if not isinstance(value, dict):
        return None
    states = {}
    for key, item in value.items():
        if isinstance(item, dict):
            states[key] = item.get("state") or item.get("lifecycle")
        else:
            states[key] = item
    return states


def compact_state(docs):
    session = unwrap(docs.get("session.json"))
    world = unwrap(docs.get("world.json"))
    character = unwrap(docs.get("character.json"))
    campaign = unwrap(docs.get("campaign.json"))
    overlays = session.get("runtime_scene_overlays") if isinstance(session.get("runtime_scene_overlays"), dict) else {}
    discovered = {}
    for scene_id, overlay in overlays.items():
        if isinstance(overlay, dict) and overlay.get("discovered_clues"):
            discovered[scene_id] = overlay.get("discovered_clues")
    inventory = character.get("inventory") if isinstance(character.get("inventory"), list) else character.get("inventory")
    hp = character.get("hp") if isinstance(character.get("hp"), dict) else {}
    present = sorted(docs)
    return {
        "campaign_title": campaign.get("title"),
        "campaign_run_id": session.get("campaign_run_id"),
        "session_id": session.get("session_id"),
        "campaign_started": session.get("campaign_started"),
        "active_scene_id": session.get("active_scene_id"),
        "visited_scene_ids": session.get("visited_scene_ids"),
        "current_date": session.get("current_date"),
        "clocks": session.get("clocks"),
        "turn_counter": session.get("turn_counter"),
        "chat_history_len": len(session.get("chat_history") or []),
        "log_entries": len(docs.get("session_log.jsonl") or []),
        "discovered_clues_by_scene": discovered,
        "clue_knowledge": clue_states(session.get("clue_knowledge")),
        "deferred_intentions": session.get("deferred_intentions"),
        "deferred_steps": session.get("deferred_steps"),
        "active_quests": session.get("quests") or session.get("active_quests") or campaign.get("quests"),
        "character": {
            "id": character.get("id"),
            "name": character.get("name"),
            "hp_current": hp.get("current"),
            "hp_max": hp.get("max"),
            "gold": character.get("gold"),
            "inventory_count": len(inventory) if isinstance(inventory, list) else None,
        },
        "world_clue_ids": sorted((world.get("clues") or {}).keys()) if isinstance(world.get("clues"), dict) else None,
        "documents_present": present,
        "observability_gaps": [
            name for name, value in (
                ("campaign_run_id", session.get("campaign_run_id")),
                ("session_id", session.get("session_id")),
                ("active_scene_id", session.get("active_scene_id")),
                ("current_date", session.get("current_date")),
                ("clocks", session.get("clocks")),
                ("turn_counter", session.get("turn_counter")),
                ("active_quests", session.get("quests") or session.get("active_quests") or campaign.get("quests")),
            ) if value is None
        ],
    }


def changed_documents(before, after):
    names = sorted(set(before) | set(after))
    changed = []
    for name in names:
        if before.get(name) != after.get(name):
            changed.append(name)
    return changed


def shrink(value, depth=0):
    if isinstance(value, str):
        return value if len(value) <= 600 else value[:600] + f"...[{len(value)} chars]"
    if isinstance(value, list):
        items = [shrink(item, depth + 1) for item in value[:12]]
        if len(value) > 12:
            items.append(f"...[{len(value)} items]")
        return items
    if isinstance(value, dict):
        if depth >= 4:
            return {"keys": sorted(value)[:40], "truncated": True}
        kept = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 40:
                kept["truncated_keys"] = len(value) - 40
                break
            kept[str(key)] = shrink(item, depth + 1)
        return kept
    return value


def player_text(body):
    if not isinstance(body, dict):
        return ""
    gm = body.get("gm_output") if isinstance(body.get("gm_output"), dict) else {}
    text = gm.get("player_facing_text")
    if isinstance(text, str) and text.strip():
        return text
    for key in ("player_facing_text", "reply", "narration", "message", "error"):
        value = body.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def engine_view(body):
    if not isinstance(body, dict):
        return {"available": False, "body_type": type(body).__name__}
    resolution = body.get("resolution") if isinstance(body.get("resolution"), dict) else {}
    gm = body.get("gm_output") if isinstance(body.get("gm_output"), dict) else {}
    metadata = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    gm_meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    live = metadata.get("live_chat_interpretation") if isinstance(metadata.get("live_chat_interpretation"), dict) else {}
    accepted = gm_meta.get("accepted_response") if isinstance(gm_meta.get("accepted_response"), dict) else {}
    return {
        "ok": body.get("ok"),
        "status": body.get("status"),
        "error": body.get("error"),
        "resolution_keys": sorted(resolution),
        "action_type": resolution.get("action_type") or resolution.get("type"),
        "intent": resolution.get("intent") or resolution.get("player_intent"),
        "success": resolution.get("success"),
        "resolved_transition": resolution.get("resolved_transition"),
        "target_scene_id": resolution.get("target_scene_id"),
        "prompt": resolution.get("prompt"),
        "noncombat_resolution": shrink(resolution.get("noncombat_resolution")),
        "authoritative_mutation": metadata.get("authoritative_mutation"),
        "resolution_metadata_keys": sorted(metadata),
        "live_interpretation": shrink(live) if live else None,
        "tags": gm.get("tags"),
        "hard_valid": (accepted.get("hard_validation") or {}).get("hard_valid") if isinstance(accepted.get("hard_validation"), dict) else accepted.get("hard_valid"),
        "gm_metadata_keys": sorted(gm_meta)[:40],
        "missing_observability": [
            name for name, present in (
                ("resolution", bool(resolution)),
                ("recognized_intent", bool(resolution.get("intent") or resolution.get("player_intent") or live)),
                ("selected_action", bool(resolution.get("action_type") or resolution.get("type") or resolution.get("noncombat_resolution"))),
                ("validation", "accepted_response" in gm_meta or "hard_validation" in gm_meta),
            ) if not present
        ],
    }


def provider_slice(events):
    rows = []
    for event in events:
        if event.get("event") not in {"dispatch_attempted", "completed", "rejected", "admitted"} and event.get("stage") != "provider_response":
            if event.get("event") == "initialized":
                continue
        rows.append({
            "event": event.get("event"),
            "stage": event.get("stage"),
            "purpose": event.get("purpose"),
            "owner": event.get("owner"),
            "configured_model": event.get("configured_model"),
            "model": event.get("model"),
            "input_tokens": event.get("input_tokens"),
            "output_tokens": event.get("output_tokens"),
            "total_tokens": event.get("total_tokens"),
            "latency_ms": event.get("latency_ms"),
            "completion_status": event.get("completion_status"),
            "error": event.get("error"),
            "classification": event.get("classification"),
            "provider_status": event.get("provider_status"),
            "sdk_retries": event.get("sdk_retries"),
            "host_retries": event.get("host_retries"),
            "refusal": event.get("refusal"),
            "admission": event.get("admission"),
        })
    return rows


def read_events(run):
    path = run / "diagnostics" / "provider_usage.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def budget(run):
    path = run / "diagnostics" / "budget_snapshot.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    hidden = secrets_from({**os.environ})
    from dotenv import dotenv_values
    file_env = {key: value for key, value in dotenv_values(ROOT / ".env").items() if value is not None}
    hidden = secrets_from({**file_env, **os.environ})
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12]
    run = ROOT / "artifacts" / "atgb" / "pr_play_35" / "live" / stamp
    result = {
        "experiment": "PR-PLAY-35",
        "run_id": stamp,
        "run_path": str(run),
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "turns": [],
        "opening": None,
        "stop_reason": None,
        "provider_requests_before_gameplay": None,
    }
    process = None
    logger = None
    started = time.monotonic()
    hashes_before = source_hashes()
    player = player_campaign_dir_from_env(ROOT)
    user_before = campaign_fingerprint(player)
    try:
        source, manifest = load_baseline(ROOT)
        scenario = runner.load_scenario("FiveTurnGameplay")
        fixture_ceiling = scenario["provider_request_ceiling"]
        scenario["provider_request_ceiling"] = MISSION_REQUEST_CEILING
        runner_text = (ROOT / "tools" / "playtest" / "runner.py").read_text(encoding="utf-8")
        launch_present = (
            "def start_worker" in runner_text
            and "_base_executable" in runner_text
            and "Harness base interpreter unavailable" in runner_text
        )
        env = runner.child_environment(run, scenario, "Live", "success")
        effective_ceiling = int(env["ASHEN_PROVIDER_REQUEST_LIMIT"])
        if effective_ceiling > MISSION_REQUEST_CEILING:
            raise RuntimeError("Request ceiling exceeded the mission limit")
        disabled = [key for key in ("ASHEN_DISABLE_LIVE_INTERPRETATION", "ASHEN_DISABLE_EXPRESSION_GENERATION", "ASHEN_DISABLE_PROVIDER_CALLS")
                    if env.get(key, "").lower() in {"1", "true", "yes", "on"}]
        pinned = bool(env.get("ASHEN_PIN_PROVIDER_MODEL", "").strip())
        credentials_present = bool(env.get("OPENAI_API_KEY", "").strip())
        safe_models = {key: env.get(key) for key in (
            "MODEL_NAME", "DEFAULT_MODEL_NAME", "HIGH_PRECISION_MODEL_NAME", "RETRY_ESCALATION_MODEL_NAME", "ENABLE_MODEL_ROUTING")}
        phase1 = {
            "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "worktree_status_game_playtest": subprocess.check_output(
                ["git", "status", "--short", "--", "game", "tools/playtest"], cwd=ROOT, text=True),
            "runner_sha256": sha256_file(ROOT / "tools/playtest/runner.py"),
            "process_launch_uses_base_executable": launch_present,
            "fixture": "frontier-gate-v1",
            "fixture_manifest_sha256": digest(source / "manifest.json"),
            "fixture_matches_pin": digest(source / "manifest.json") == manifest.get("files", {}).get("manifest.json", digest(source / "manifest.json")),
            "scenario_id": "FiveTurnGameplay",
            "scenario_file_ceiling": fixture_ceiling,
            "mission_request_ceiling": MISSION_REQUEST_CEILING,
            "effective_request_ceiling": effective_ceiling,
            "token_limits": {kind: env.get(f"ASHEN_PROVIDER_{kind.upper()}_TOKEN_LIMIT") for kind in ("input", "output", "total")},
            "models": safe_models,
            "credentials_present": credentials_present,
            "live_interpretation_disabled": disabled,
            "pinned_model_override": pinned,
            "opening_renderer_set": "ASHEN_OPENING_RENDERER" in env,
            "sdk_retries_disabled": env.get("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES"),
            "host_retries_disabled": env.get("ASHEN_DISABLE_PROVIDER_RETRIES"),
            "http_timeout_seconds": HTTP_TIMEOUT,
            "player_inputs": [turn["player_input"] for turn in TURNS],
            "pr_play_31_inputs_not_substituted": [
                "I approach the tavern runner and ask what they're offering.",
                "What sort of rumors have you heard?",
                "I head northwest of the crates to investigate the muddy footprints.",
                "I go to Follow the missing patrol rumor.",
                "I examine the footprints.",
            ],
            "user_campaign": str(player),
            "isolated_run": str(run),
        }
        manifest_pin = "9c390c78f3fcf7507793e1037eb0add59e5e373050d1996f29f0c26f3b7bf0ea"
        phase1["fixture_manifest_matches_pinned_constant"] = phase1["fixture_manifest_sha256"] == manifest_pin
        dump(OUT / "phase1_baseline.json", phase1, hidden)
        dump(OUT / "user_campaign_before.json", {"file_count": user_before.get("file_count"), "path": user_before.get("path")}, hidden)
        result["phase1"] = phase1
        if not launch_present or not credentials_present or disabled or pinned or effective_ceiling <= 0:
            result["stop_reason"] = "infrastructure_or_environment"
            result["environment_blockers"] = {
                "launch_present": launch_present,
                "credentials_present": credentials_present,
                "disabled_flags": disabled,
                "pinned_model_override": pinned,
                "effective_request_ceiling": effective_ceiling,
            }
            return
        run.mkdir(parents=True, exist_ok=False)
        for name in ("configuration", "diagnostics", "baseline", "after", "opening", "reports", "turns"):
            (run / name).mkdir()
        prepare_isolated_store(run / "data", scenario_id="FiveTurnGameplay", repo=ROOT, player_campaign_dir=player)
        env["ASHEN_OPENING_RESPONSE_CAPTURE"] = "1"
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        dump(run / "configuration" / "scenario.json", scenario, hidden)
        dump(run / "configuration" / "run.json", {
            "scenario_id": "FiveTurnGameplay", "mode": "Live", "fixture_response": "success",
            "port": 0, "player_data": str(player), "capture_response": True,
        }, hidden)
        dump(OUT / "safe_configuration.json", {
            "provider": "configured OpenAI client",
            "models": safe_models,
            "credentials_present": True,
            "request_ceiling": effective_ceiling,
            "token_limits": phase1["token_limits"],
            "sdk_retries": 0,
            "host_retries": 0,
            "opening_renderer_override": False,
            "opening_response_capture": True,
        }, hidden)
        process = runner.start_worker(run, env)
        logger = threading.Thread(
            target=runner.bounded_log,
            args=(process.stdout, run / "diagnostics" / "application.log", secrets_from(env)),
            daemon=True,
        )
        logger.start()
        ready, base = runner.wait_for_http_ready(process, run, 30)
        owned = ownership(process)
        owned["ready_pid"] = ready.get("pid")
        owned["ready_model"] = ready.get("model")
        owned["isolation_verified"] = ready.get("isolation_verified")
        owned["sdk_retries"] = ready.get("sdk_retries")
        owned["host_retries"] = ready.get("host_retries")
        gates = {
            "ready_pid_matches_popen": ready.get("pid") == process.pid,
            "parent_is_controller": owned["parent_pid"] == os.getpid(),
            "executable_is_base": same_path(owned.get("worker_executable"), owned.get("base_executable")),
            "no_interpreter_child": not owned["interpreter_children"],
            "isolation_verified": ready.get("isolation_verified") is True,
            "retries_disabled": ready.get("sdk_retries") == 0 and ready.get("host_retries") == 0,
            "diagnostics_enabled": ready.get("diagnostics_enabled") is True,
        }
        dump(OUT / "process_ownership.json", {"ownership": owned, "gates": gates, "ready_model": ready.get("model")}, hidden)
        if not all(gates.values()):
            result["stop_reason"] = "process_ownership_or_isolation_failure"
            result["ownership_gates"] = gates
            return
        result["ready_model"] = ready.get("model")
        result["base_url"] = base

        def call(method, path, body=None, timeout=HTTP_TIMEOUT):
            start = time.monotonic()
            status, response = runner.request(base, method, path, timeout, body)
            return {
                "method": method,
                "path": path,
                "http_status": status,
                "api_latency_seconds": round(time.monotonic() - start, 3),
                "response": response,
            }

        def capture(label):
            folder = run / label
            folder.mkdir(parents=True, exist_ok=True)
            row = call("GET", "/api/state?ui_mode=player", timeout=30)
            dump(folder / "public_state.json", row, hidden)
            docs = runner.snapshot_files(run, label)
            return docs, compact_state(docs), row

        initial_docs, initial_state, _public = capture("initial")
        usage = budget(run)
        result["initial_state"] = initial_state
        result["provider_requests_at_initial"] = usage.get("dispatched_requests")
        if usage.get("dispatched_requests") not in (0, None) or initial_state.get("campaign_started") is True or initial_state.get("turn_counter") not in (0, None):
            result["stop_reason"] = "unexpected_initial_state"
            result["initial_usage"] = {key: usage.get(key) for key in ("dispatched_requests", "input_tokens", "output_tokens", "total_tokens", "stopped", "stop_reason")}
            return
        new_row = call("POST", "/api/new_campaign", {"ui_mode": "player"}, timeout=30)
        dump(run / "reports" / "new_campaign.json", {k: v for k, v in new_row.items() if k != "response"} | {"response": shrink(new_row["response"])}, hidden)
        if new_row["http_status"] != 200 or not (isinstance(new_row["response"], dict) and new_row["response"].get("ok") is True):
            result["stop_reason"] = "initialization_failed"
            result["new_campaign"] = {k: v for k, v in new_row.items() if k != "response"}
            result["new_campaign"]["player_text"] = player_text(new_row["response"])
            return
        before_open_docs, before_open_state, _ = capture("baseline")
        offset = len(read_events(run))
        opening = call("POST", "/api/start_campaign", {"ui_mode": "player"})
        after_open_docs, after_open_state, _ = capture("opening")
        opening_events = read_events(run)[offset:]
        opening_record = {
            "http_status": opening["http_status"],
            "api_latency_seconds": opening["api_latency_seconds"],
            "player_facing_text": player_text(opening["response"]),
            "engine": engine_view(opening["response"]),
            "provider": provider_slice(opening_events),
            "state_before": before_open_state,
            "state_after": after_open_state,
            "changed_documents": changed_documents(before_open_docs, after_open_docs),
            "usage_after": {key: budget(run).get(key) for key in ("dispatched_requests", "input_tokens", "output_tokens", "total_tokens", "stopped", "stop_reason")},
        }
        dump(run / "opening" / "api_response.json", opening["response"], hidden)
        dump(run / "opening" / "record.json", opening_record, hidden)
        result["opening"] = opening_record
        if opening["http_status"] != 200 or after_open_state.get("campaign_started") is not True:
            result["stop_reason"] = "initialization_failed"
            return
        usage = budget(run)
        if usage.get("stopped") or int(usage.get("dispatched_requests") or 0) >= effective_ceiling:
            result["stop_reason"] = "provider_budget_exhausted_during_initialization"
            return
        for turn in TURNS:
            usage = budget(run)
            remaining = effective_ceiling - int(usage.get("dispatched_requests") or 0)
            if usage.get("stopped") or remaining < 1 or process.poll() is not None:
                result["turns"].append({
                    "step_id": turn["step_id"],
                    "player_input": turn["player_input"],
                    "classification": "BLOCKED",
                    "blocked_reason": "provider budget exhausted" if remaining < 1 or usage.get("stopped") else "worker exited",
                    "usage": {key: usage.get(key) for key in ("dispatched_requests", "stopped", "stop_reason")},
                })
                result["stop_reason"] = result["stop_reason"] or "provider_budget_exhausted"
                for later in TURNS[TURNS.index(turn) + 1:]:
                    result["turns"].append({
                        "step_id": later["step_id"],
                        "player_input": later["player_input"],
                        "classification": "BLOCKED",
                        "blocked_reason": result["stop_reason"],
                    })
                break
            label = f"turns/{turn['step_id']}"
            before_docs, before_state, _ = capture(f"{label}/before")
            event_offset = len(read_events(run))
            try:
                row = call("POST", "/api/chat", {"text": turn["player_input"], "ui_mode": "player"})
            except Exception as exc:
                failure = {
                    "step_id": turn["step_id"],
                    "player_input": turn["player_input"],
                    "error_type": type(exc).__name__,
                    "error": redact(str(exc)[:500], hidden),
                    "state_before": before_state,
                    "classification": "FAIL",
                    "provider_after": provider_slice(read_events(run)[event_offset:]),
                    "usage_after": {key: budget(run).get(key) for key in ("dispatched_requests", "input_tokens", "output_tokens", "total_tokens", "stopped", "stop_reason", "pending_requests")},
                }
                dump(run / label / "failure.json", failure, hidden)
                result["turns"].append(failure)
                pending = failure["usage_after"].get("pending_requests")
                if process.poll() is not None or pending:
                    result["stop_reason"] = "unrecoverable_turn_failure"
                    for later in TURNS[TURNS.index(turn) + 1:]:
                        result["turns"].append({
                            "step_id": later["step_id"],
                            "player_input": later["player_input"],
                            "classification": "BLOCKED",
                            "blocked_reason": result["stop_reason"],
                        })
                    break
                continue
            dump(run / label / "api_response.json", row["response"], hidden)
            try:
                after_docs, after_state, _ = capture(f"{label}/after")
            except Exception as exc:
                after_docs, after_state = {}, {"snapshot_error": type(exc).__name__, "detail": redact(str(exc)[:400], hidden)}
            events = read_events(run)[event_offset:]
            record = {
                "step_id": turn["step_id"],
                "intent": turn["intent"],
                "player_input": turn["player_input"],
                "http_status": row["http_status"],
                "api_latency_seconds": row["api_latency_seconds"],
                "player_facing_text": player_text(row["response"]),
                "engine": engine_view(row["response"]),
                "provider": provider_slice(events),
                "state_before": before_state,
                "state_after": after_state,
                "changed_documents": changed_documents(before_docs, after_docs),
                "usage_after": {key: budget(run).get(key) for key in ("dispatched_requests", "input_tokens", "output_tokens", "total_tokens", "stopped", "stop_reason", "pending_requests")},
            }
            dump(run / label / "record.json", record, hidden)
            result["turns"].append(record)
            dump(OUT / "live_result.json", result, hidden)
            if process.poll() is not None:
                result["stop_reason"] = "worker_exited"
                break
        else:
            result["stop_reason"] = result["stop_reason"] or "five_turns_submitted"
        capture("after")
    except BaseException as exc:
        result["stop_reason"] = result.get("stop_reason") or "environment_or_controller_failure"
        result["error_type"] = type(exc).__name__
        result["error_detail"] = redact(str(exc)[:800], hidden)
        result["traceback"] = redact(traceback.format_exc()[-2000:], hidden)
    finally:
        result["cleanup"] = runner.stop_owned(process, 5)
        if logger is not None:
            logger.join(timeout=3)
        result["duration_seconds"] = round(time.monotonic() - started, 3)
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        usage_path = run / "diagnostics" / "budget_snapshot.json"
        if usage_path.exists():
            usage = json.loads(usage_path.read_text(encoding="utf-8"))
            result["provider_usage"] = {key: usage.get(key) for key in (
                "dispatched_requests", "input_tokens", "output_tokens", "total_tokens", "stopped", "stop_reason", "pending_requests")}
        result["events"] = provider_slice(read_events(run)) if run.exists() else []
        user_after = campaign_fingerprint(player)
        result["user_campaign_unchanged"] = user_before.get("files") == user_after.get("files")
        hashes_after = source_hashes()
        result["gameplay_sources_unchanged"] = hashes_before == hashes_after
        result["source_drift"] = sorted(set(hashes_before) ^ set(hashes_after) | {key for key in hashes_before if hashes_before.get(key) != hashes_after.get(key)})
        dump(OUT / "live_result.json", result, hidden)
        dump(OUT / "user_campaign_after.json", {"file_count": user_after.get("file_count"), "unchanged": result["user_campaign_unchanged"]}, hidden)
        print(json.dumps({
            "stop_reason": result.get("stop_reason"),
            "turns": len(result.get("turns") or []),
            "provider": result.get("provider_usage"),
            "duration_seconds": result.get("duration_seconds"),
            "user_campaign_unchanged": result.get("user_campaign_unchanged"),
            "sources_unchanged": result.get("gameplay_sources_unchanged"),
            "run": stamp,
        }))


if __name__ == "__main__":
    main()
