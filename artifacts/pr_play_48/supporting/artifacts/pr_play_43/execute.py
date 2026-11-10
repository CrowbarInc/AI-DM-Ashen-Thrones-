"""PR-PLAY-43 observational live gameplay controller.

Uses the existing isolated-store harness and production worker. Does not change
gameplay, prompts, provider routing, semantic validation, opening recovery,
action admission, grounding, or fixtures. Does not retry a turn or restart a
campaign.

The five player lines are unchanged. Turn 5 is not submitted unless turn 4
leaves the authoritative scene at old_milestone. A gameplay turn starts only
when two provider requests remain. After a successful opening, a separate
process reads the copied scene and calls production grounding functions.
That process does not submit a turn or call the provider.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import hashlib
import json
import os
import subprocess

os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
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
EXPERIMENT = "PR-PLAY-43"
TURNS = (
    {"step_id": "T1", "player_input": "What is available here?",
     "intent": "public scene information"},
    {"step_id": "T2", "player_input": "Have you heard any interesting rumors lately?",
     "intent": "npc rumor interaction"},
    {"step_id": "T3", "player_input": "I examine the notice board.",
     "intent": "notice board investigation"},
    {"step_id": "T4", "player_input": "I want to follow the trail connected to the missing patrol.",
     "intent": "authored travel"},
    {"step_id": "T5", "player_input": "I examine the footprints.",
     "intent": "footprint investigation"},
)
INTERPRETER_IMAGES = {"python.exe", "pythonw.exe", "py.exe"}
K = ctypes.WinDLL("kernel32", use_last_error=True)
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
USAGE_KEYS = (
    "dispatched_requests", "input_tokens", "output_tokens", "total_tokens",
    "stopped", "stop_reason", "pending_requests",
)


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
        view["fingerprint_sha256"] = hashlib.sha256(b"").hexdigest()
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
    raw = json.dumps(files, sort_keys=True, separators=(",", ":"))
    view["fingerprint_sha256"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return view


def fingerprint_public(view):
    return {
        "path": view.get("path"),
        "exists": view.get("exists"),
        "file_count": view.get("file_count"),
        "fingerprint_sha256": view.get("fingerprint_sha256"),
    }


def can_start_interaction(usage, request_limit):
    """Same reserve as tools.playtest.gameplay.can_start_interaction."""
    return (not usage.get("stopped")
            and request_limit - int(usage.get("dispatched_requests") or 0) >= 2)


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
            states[key] = item.get("state") or item.get("lifecycle") or item.get("status")
        else:
            states[key] = item
    return states


def scene_body(document):
    body = unwrap(document)
    scene = body.get("scene") if isinstance(body.get("scene"), dict) else body
    return scene if isinstance(scene, dict) else {}


def catalog(docs):
    world = unwrap(docs.get("world.json"))
    npcs = []
    for npc in world.get("npcs") or []:
        if isinstance(npc, dict):
            npcs.append({
                "id": npc.get("id"),
                "name": npc.get("name"),
                "location": npc.get("location"),
                "topic_ids": [
                    topic.get("id") for topic in (npc.get("topics") or [])
                    if isinstance(topic, dict)
                ],
            })
    factions = []
    for faction in world.get("factions") or []:
        if isinstance(faction, dict):
            factions.append({
                "id": faction.get("id"),
                "pressure": faction.get("pressure"),
                "influence": faction.get("influence"),
                "agenda_progress": faction.get("agenda_progress"),
            })
    scenes = {}
    for name, document in docs.items():
        if not str(name).startswith("scenes/") or not str(name).endswith(".json"):
            continue
        scene = scene_body(document)
        scenes[scene.get("id") or name] = {
            "exit_labels": [
                {
                    "id": row.get("id"),
                    "label": row.get("label"),
                    "target_scene_id": row.get("target_scene_id"),
                }
                for row in (scene.get("exits") or []) if isinstance(row, dict)
            ],
            "interactable_ids": [
                row.get("id") for row in (scene.get("interactables") or [])
                if isinstance(row, dict)
            ],
            "addressable_ids": [
                row.get("id") for row in (scene.get("addressables") or [])
                if isinstance(row, dict)
            ],
        }
    return {
        "npc_ids": [row["id"] for row in npcs],
        "npcs": npcs,
        "factions": factions,
        "world_event_log_len": len(world.get("event_log") or []),
        "scenes": scenes,
    }


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
    clocks = session.get("clocks") if isinstance(session.get("clocks"), dict) else None
    active_quests = session.get("quests") or session.get("active_quests") or campaign.get("quests")
    return {
        "campaign_title": campaign.get("title"),
        "campaign_run_id": session.get("campaign_run_id"),
        "session_id": session.get("session_id"),
        "campaign_started": session.get("campaign_started"),
        "active_scene_id": session.get("active_scene_id"),
        "visited_scene_ids": session.get("visited_scene_ids"),
        "current_date": session.get("current_date"),
        "clocks": clocks,
        "turn_counter": session.get("turn_counter"),
        "chat_history_len": len(session.get("chat_history") or []),
        "log_entries": len(docs.get("session_log.jsonl") or []),
        "discovered_clues_by_scene": discovered,
        "clue_knowledge": clue_states(session.get("clue_knowledge")),
        "known_clue_ids": sorted((session.get("known_clues") or [])) if isinstance(session.get("known_clues"), list) else session.get("known_clues"),
        "deferred_intentions": session.get("deferred_intentions"),
        "deferred_steps": session.get("deferred_steps"),
        "time_pressure": clocks.get("time_pressure") if isinstance(clocks, dict) else session.get("time_pressure"),
        "active_quests": active_quests,
        "character": {
            "id": character.get("id"),
            "name": character.get("name"),
            "hp_current": hp.get("current"),
            "hp_max": hp.get("max"),
            "gold": character.get("gold"),
            "resources": character.get("resources"),
            "inventory_count": len(inventory) if isinstance(inventory, list) else None,
            "inventory_ids": [
                (item.get("id") or item.get("name")) if isinstance(item, dict) else item
                for item in (inventory[:30] if isinstance(inventory, list) else [])
            ],
        },
        "world_clue_ids": sorted((world.get("clues") or {}).keys()) if isinstance(world.get("clues"), dict) else None,
        "authority_catalog": catalog(docs),
        "documents_present": present,
        "observability_gaps": [
            name for name, value in (
                ("campaign_run_id", session.get("campaign_run_id")),
                ("session_id", session.get("session_id")),
                ("active_scene_id", session.get("active_scene_id")),
                ("current_date", session.get("current_date")),
                ("clocks", clocks),
                ("turn_counter", session.get("turn_counter")),
                ("active_quests", active_quests),
                ("known_clues", session.get("known_clues")),
                ("character_resources", character.get("resources")),
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


def clip(value, depth=0):
    if isinstance(value, str):
        return value if len(value) <= 4000 else value[:4000] + f"...[{len(value)} chars]"
    if isinstance(value, list):
        items = [clip(item, depth + 1) for item in value[:24]]
        if len(value) > 24:
            items.append(f"...[{len(value)} items]")
        return items
    if isinstance(value, dict):
        if depth >= 6:
            return {"keys": sorted(value)[:40], "truncated": True}
        kept = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 60:
                kept["truncated_keys"] = len(value) - 60
                break
            kept[str(key)] = clip(item, depth + 1)
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
    hard = accepted.get("hard_validation") if isinstance(accepted.get("hard_validation"), dict) else {}
    return {
        "ok": body.get("ok"),
        "status": body.get("status"),
        "error": body.get("error"),
        "resolution_keys": sorted(resolution),
        "action_type": resolution.get("action_type") or resolution.get("type"),
        "intent": resolution.get("intent") or resolution.get("player_intent"),
        "kind": resolution.get("kind"),
        "action_id": resolution.get("action_id"),
        "success": resolution.get("success"),
        "resolved_transition": resolution.get("resolved_transition"),
        "target_scene_id": resolution.get("target_scene_id"),
        "originating_scene_id": resolution.get("originating_scene_id"),
        "prompt": resolution.get("prompt"),
        "discovered_clues": clip(resolution.get("discovered_clues")),
        "state_changes": clip(resolution.get("state_changes")),
        "noncombat_resolution": clip(resolution.get("noncombat_resolution")),
        "authoritative_mutation": metadata.get("authoritative_mutation"),
        "processing_outcome": metadata.get("processing_outcome"),
        "resolver_invoked": metadata.get("resolver_invoked"),
        "narration_invoked": metadata.get("narration_invoked"),
        "gameplay_parser_invoked": metadata.get("gameplay_parser_invoked"),
        "provider_calls": clip(metadata.get("provider_calls")),
        "resolution_metadata_keys": sorted(metadata),
        "conversational_decision": clip(metadata.get("conversational_decision")),
        "stored_interpretation_bridge": clip(metadata.get("stored_interpretation_bridge")),
        "live_interpretation": clip(live) if live else None,
        "tags": gm.get("tags"),
        "provenance": accepted.get("provenance"),
        "hard_valid": hard.get("hard_valid", accepted.get("hard_valid")),
        "expression_decision": (gm_meta.get("expression_generation") or {}).get("decision")
        if isinstance(gm_meta.get("expression_generation"), dict) else None,
        "gm_metadata_keys": sorted(gm_meta)[:40],
        "missing_observability": [
            name for name, present in (
                ("resolution", bool(resolution)),
                ("recognized_intent", bool(resolution.get("intent") or resolution.get("player_intent") or live or metadata.get("conversational_decision"))),
                ("selected_action", bool(resolution.get("action_type") or resolution.get("type") or resolution.get("kind") or resolution.get("noncombat_resolution"))),
                ("validation", "accepted_response" in gm_meta or "hard_validation" in gm_meta),
            ) if not present
        ],
    }


DIAGNOSTIC_STAGES = {
    "provider_response", "opening_semantics", "opening_validation", "opening_outcome",
    "opening_response_capture", "opening_admission",
}


def provider_slice(events):
    rows = []
    for event in events:
        stage = event.get("stage")
        if event.get("event") not in {"dispatch_attempted", "completed", "rejected", "admitted", "generation_diagnostic"} and stage not in DIAGNOSTIC_STAGES:
            continue
        if event.get("event") == "initialized":
            continue
        if event.get("event") == "generation_diagnostic" and stage not in DIAGNOSTIC_STAGES:
            continue
        rows.append({
            "event": event.get("event"),
            "stage": stage,
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
            "semantic_classification": event.get("semantic_classification"),
            "semantic_reasons": event.get("semantic_reasons"),
            "classification_reason": event.get("classification_reason"),
            "opening_accepted": event.get("opening_accepted"),
            "gameplay_committed": event.get("gameplay_committed"),
            "recovery_classification": event.get("recovery_classification"),
            "rejection_reason": event.get("rejection_reason"),
            "final_validation_passed": event.get("final_validation_passed"),
            "structured_validation_result": event.get("structured_validation_result"),
            "narration_length": event.get("narration_length"),
            "declaration_count": event.get("declaration_count"),
            "logical_operation": event.get("logical_operation"),
            "opening_recovery": event.get("opening_recovery"),
            "sequence": event.get("sequence"),
            "budget_remaining": event.get("budget_remaining"),
            "fallback": event.get("fallback"),
            "retry_count": event.get("retry_count"),
        })
    return rows


def latest_opening_recovery(events):
    found = None
    for event in events:
        recovery = event.get("opening_recovery")
        if isinstance(recovery, dict):
            found = recovery
    return found


def persisted_engine(docs):
    rows = docs.get("session_log.jsonl") or []
    if not rows or not isinstance(rows[-1], dict):
        return None
    last = rows[-1]
    resolution = last.get("resolution") if isinstance(last.get("resolution"), dict) else {}
    meta = last.get("log_meta") if isinstance(last.get("log_meta"), dict) else {}
    res_meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    gm = last.get("gm_output") if isinstance(last.get("gm_output"), dict) else {}
    gm_meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    accepted = gm_meta.get("accepted_response") if isinstance(gm_meta.get("accepted_response"), dict) else {}
    hard = accepted.get("hard_validation") if isinstance(accepted.get("hard_validation"), dict) else {}
    return {
        "log_index": len(rows) - 1,
        "player_input": last.get("player_input"),
        "player_facing_text": gm.get("player_facing_text"),
        "intent_classification": clip(meta.get("intent_classification")),
        "resolution_kind": resolution.get("kind"),
        "action_id": resolution.get("action_id"),
        "action_type": resolution.get("action_type") or resolution.get("type"),
        "success": resolution.get("success"),
        "resolved_transition": resolution.get("resolved_transition"),
        "target_scene_id": resolution.get("target_scene_id"),
        "originating_scene_id": resolution.get("originating_scene_id"),
        "prompt": resolution.get("prompt"),
        "discovered_clues": clip(resolution.get("discovered_clues")),
        "state_changes": clip(resolution.get("state_changes")),
        "clocks_changed": meta.get("clocks_changed"),
        "discovered_clues_added": meta.get("discovered_clues_added"),
        "approved_state_updates": clip(meta.get("approved_state_updates")),
        "rejected_state_updates": clip(meta.get("rejected_state_updates")),
        "log_meta_keys": sorted(meta),
        "resolution_metadata_keys": sorted(res_meta),
        "processing_outcome": res_meta.get("processing_outcome"),
        "resolver_invoked": res_meta.get("resolver_invoked"),
        "narration_invoked": res_meta.get("narration_invoked"),
        "gameplay_parser_invoked": res_meta.get("gameplay_parser_invoked"),
        "conversational_decision": clip(res_meta.get("conversational_decision")),
        "stored_interpretation_bridge": clip(res_meta.get("stored_interpretation_bridge")),
        "opening_recovery_debug": gm_meta.get("opening_recovery_debug"),
        "provenance": accepted.get("provenance"),
        "hard_valid": hard.get("hard_valid", accepted.get("hard_valid")),
        "response_type_contract": clip(meta.get("response_type_contract")),
    }


def compact_delta(before, after):
    if not isinstance(before, dict) or not isinstance(after, dict):
        return None
    delta = {}
    for key in sorted(set(before) | set(after)):
        if before.get(key) != after.get(key):
            delta[key] = {"before": before.get(key), "after": after.get(key)}
    return delta


def classify_opening_source(http_status, recovery, state_after):
    started = isinstance(state_after, dict) and state_after.get("campaign_started") is True
    if not started or http_status != 200:
        return "C_initialization_failure"
    source = (recovery or {}).get("opening_source") if isinstance(recovery, dict) else None
    if source == "deterministic_fallback" and (recovery or {}).get("fallback_succeeded"):
        return "B_deterministic_recovery"
    if source in {None, "ai_accepted"} or (isinstance(recovery, dict) and recovery.get("recovery_eligibility") == "ai_accepted"):
        return "A_ai_accepted"
    return "unclassified"


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


def usage_view(usage):
    return {key: usage.get(key) for key in USAGE_KEYS}


def tree_fingerprint(path):
    resolved = Path(path)
    rows = {}
    if not resolved.exists():
        return rows
    for file in resolved.rglob("*"):
        if not file.is_file() or "__pycache__" in file.parts:
            continue
        rows[file.relative_to(resolved).as_posix()] = {
            "bytes": file.stat().st_size,
            "sha256": sha256_file(file),
        }
    return rows


def run_grounding_audit(run, hidden):
    """Observe the copied opening. Do not write the live store or call the provider."""
    snapshot = run / "opening" / "persistent"
    scratch = run / "audit_bind"
    scratch.mkdir(parents=True, exist_ok=False)
    before_live = tree_fingerprint(run / "data")
    before_snapshot = tree_fingerprint(snapshot)
    usage_path = run / "diagnostics" / "provider_usage.jsonl"
    usage_before = usage_path.read_bytes() if usage_path.exists() else b""
    destination = run / "opening" / "grounding_audit.json"
    env = os.environ.copy()
    env["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
    env["ASHEN_DATA_DIR"] = str(scratch)
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    executable = getattr(sys, "_base_executable", None) or sys.executable
    try:
        completed = subprocess.run(
            [executable, "-u", str(OUT / "grounding_audit.py"), str(snapshot), str(destination)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        spawned = True
        error = None
    except Exception as exc:
        completed = None
        spawned = False
        error = {"error_type": type(exc).__name__, "error": redact(str(exc)[:500], hidden)}
    after_live = tree_fingerprint(run / "data")
    after_snapshot = tree_fingerprint(snapshot)
    usage_after = usage_path.read_bytes() if usage_path.exists() else b""
    scratch_files = sorted(tree_fingerprint(scratch))
    audit = {}
    if destination.exists():
        audit = json.loads(destination.read_text(encoding="utf-8"))
    else:
        audit = {
            "decision": "INCONCLUSIVE",
            "reasons": ["probe_produced_no_report"],
        }
    if not spawned:
        audit["decision"] = "INCONCLUSIVE"
        audit["spawn_error"] = error
    elif completed.returncode not in {0, 2, 3}:
        audit["decision"] = "INCONCLUSIVE"
        audit.setdefault("reasons", []).append("probe_process_failed")
    audit["probe_exit_code"] = None if completed is None else completed.returncode
    audit["probe_stdout_excerpt"] = "" if completed is None else redact(completed.stdout[-1000:], hidden)
    audit["probe_stderr_excerpt"] = "" if completed is None else redact(completed.stderr[-1500:], hidden)
    audit["live_store_unchanged_during_probe"] = before_live == after_live
    audit["snapshot_unchanged_during_probe"] = before_snapshot == after_snapshot
    audit["provider_usage_unchanged_during_probe"] = usage_before == usage_after
    audit["scratch_files_after_probe"] = scratch_files
    if audit.get("provider_invoked_by_probe") or not audit["provider_usage_unchanged_during_probe"]:
        audit["decision"] = "INCONCLUSIVE"
        audit.setdefault("reasons", []).append("probe_or_worker_emitted_provider_activity")
    if not audit["live_store_unchanged_during_probe"] or not audit["snapshot_unchanged_during_probe"]:
        audit["decision"] = "INCONCLUSIVE"
        audit.setdefault("reasons", []).append("probe_mutated_campaign_state")
    dump(destination, audit, hidden)
    return audit


def block_remaining(result, start_at, reason):
    for later in TURNS[start_at:]:
        result["turns"].append({
            "step_id": later["step_id"],
            "player_input": later["player_input"],
            "classification": "BLOCKED",
            "blocked_reason": reason,
        })


def main():
    hidden = secrets_from({**os.environ})
    from dotenv import dotenv_values
    file_env = {key: value for key, value in dotenv_values(ROOT / ".env").items() if value is not None}
    hidden = secrets_from({**file_env, **os.environ})
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12]
    run = ROOT / "artifacts" / "atgb" / "pr_play_43" / "live" / stamp
    result = {
        "experiment": EXPERIMENT,
        "experiment_id": "pr_play_43",
        "run_id": stamp,
        "run_path": str(run),
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "turns": [],
        "opening": None,
        "stop_reason": None,
        "provider_requests_before_gameplay": None,
        "health_probe_issued_by_controller": False,
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
        decision_text = (ROOT / "game" / "gm_resolution_decision.py").read_text(encoding="utf-8")
        api_text = (ROOT / "game" / "api.py").read_text(encoding="utf-8")
        readiness_text = (ROOT / "tests" / "test_pr_play_34_readiness_diagnostics.py").read_text(encoding="utf-8")
        ownership_text = (ROOT / "game" / "ordinary_semantic_ownership.py").read_text(encoding="utf-8")
        orchestration_text = (ROOT / "game" / "conversational_orchestration.py").read_text(encoding="utf-8")
        intent_text = (ROOT / "game" / "intent_parser.py").read_text(encoding="utf-8")
        incidental_text = (ROOT / "game" / "incidental_entity.py").read_text(encoding="utf-8")
        recovery_path = ROOT / "game" / "opening_initialization_recovery.py"
        launch_present = (
            "def start_worker" in runner_text
            and "_base_executable" in runner_text
            and "Harness base interpreter unavailable" in runner_text
        )
        preserved = {
            "pr_play_33_process_launch": launch_present,
            "pr_play_34_readiness_non_interpreter_child": "test_non_interpreter_child_is_visible_but_not_an_ownership_failure" in readiness_text,
            "pr_play_36_realization_texture": "_REALIZATION_TEXTURE_TOKENS" in decision_text and '"nearby"' in decision_text and '"tightly"' in decision_text,
            "pr_play_37_opening_recovery": recovery_path.is_file() and "apply_opening_initialization_recovery" in api_text,
            "pr_play_39_npc_grounding": "def assess_addressee_grounding(" in ownership_text,
            "pr_play_39_authored_travel_admission": "def authored_travel_admission(" in orchestration_text,
            "pr_play_40_pursuit_departure_recognition": (
                "def looks_like_explicit_leave_or_pursuit_intent(" in intent_text
                and "def _match_follow_pursuit_exit(" in intent_text
                and "looks_like_explicit_leave_or_pursuit_intent" in orchestration_text
                and "_authored_pursuit_row" in orchestration_text
            ),
            "pr_play_42_public_evidence_units": "def public_evidence_units(" in incidental_text,
            "pr_play_42_addressee_authority": "def addressee_authority_applies(" in ownership_text,
            "pr_play_42_communication_uses_authority": "addressee_authority_applies" in orchestration_text,
            "pr_play_42_pretick_uses_authority": "addressee_authority_applies" in api_text,
            "pr_play_42_npc_blob_uses_units": "public_evidence_units" in ownership_text,
        }
        env = runner.child_environment(run, scenario, "Live", "success")
        effective_ceiling = int(env["ASHEN_PROVIDER_REQUEST_LIMIT"])
        if effective_ceiling > MISSION_REQUEST_CEILING:
            raise RuntimeError("Request ceiling exceeded the mission limit")
        disabled = [key for key in ("ASHEN_DISABLE_LIVE_INTERPRETATION", "ASHEN_DISABLE_EXPRESSION_GENERATION", "ASHEN_DISABLE_PROVIDER_CALLS")
                    if env.get(key, "").lower() in {"1", "true", "yes", "on"}]
        pinned = bool(env.get("ASHEN_PIN_PROVIDER_MODEL", "").strip())
        credentials_present = bool(env.get("OPENAI_API_KEY", "").strip())
        preflight_skipped = env.get("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT") == "1"
        safe_models = {key: env.get(key) for key in (
            "MODEL_NAME", "DEFAULT_MODEL_NAME", "HIGH_PRECISION_MODEL_NAME", "RETRY_ESCALATION_MODEL_NAME", "ENABLE_MODEL_ROUTING")}
        phase1 = {
            "experiment": EXPERIMENT,
            "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "worktree_status_game_playtest_atgb": subprocess.check_output(
                ["git", "status", "--short", "--", "game", "tools/playtest", "tools/atgb"], cwd=ROOT, text=True),
            "runner_sha256": sha256_file(ROOT / "tools/playtest/runner.py"),
            "process_launch_uses_base_executable": launch_present,
            "preserved_corrections": preserved,
            "fixture": "frontier-gate-v1",
            "fixture_manifest_sha256": digest(source / "manifest.json"),
            "scenario_id": "FiveTurnGameplay",
            "scenario_file_ceiling": fixture_ceiling,
            "mission_request_ceiling": MISSION_REQUEST_CEILING,
            "effective_request_ceiling": effective_ceiling,
            "turn_start_reserve": "interpretation plus optional narration; remaining requests must be at least 2",
            "token_limits": {kind: env.get(f"ASHEN_PROVIDER_{kind.upper()}_TOKEN_LIMIT") for kind in ("input", "output", "total")},
            "models": safe_models,
            "credentials_present": credentials_present,
            "live_interpretation_disabled": disabled,
            "pinned_model_override": pinned,
            "opening_renderer_set": "ASHEN_OPENING_RENDERER" in env,
            "sdk_retries_disabled": env.get("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES"),
            "host_retries_disabled": env.get("ASHEN_DISABLE_PROVIDER_RETRIES"),
            "upstream_preflight_skipped": preflight_skipped,
            "health_probe_issued_by_controller": False,
            "http_timeout_seconds": HTTP_TIMEOUT,
            "player_inputs": [turn["player_input"] for turn in TURNS],
            "turn5_stop": "submit only when the post-turn-4 authoritative scene is old_milestone",
            "user_campaign": str(player),
            "isolated_run": str(run),
            "user_campaign_fingerprint": fingerprint_public(user_before),
        }
        manifest_pin = "9c390c78f3fcf7507793e1037eb0add59e5e373050d1996f29f0c26f3b7bf0ea"
        phase1["fixture_manifest_matches_pinned_constant"] = phase1["fixture_manifest_sha256"] == manifest_pin
        dump(OUT / "phase1_baseline.json", phase1, hidden)
        dump(OUT / "user_campaign_before.json", fingerprint_public(user_before), hidden)
        result["phase1"] = phase1
        if not all(preserved.values()):
            result["stop_reason"] = "baseline_corrections_absent"
            result["environment_blockers"] = {"preserved_corrections": preserved}
            return
        isolated_is_user = same_path(run / "data", player) or same_path(run / "data", ROOT / "data")
        if (not launch_present or not credentials_present or disabled or pinned
                or effective_ceiling <= 0 or not preflight_skipped or isolated_is_user
                or not phase1["fixture_manifest_matches_pinned_constant"]):
            result["stop_reason"] = "infrastructure_or_environment"
            result["environment_blockers"] = {
                "launch_present": launch_present,
                "credentials_present": credentials_present,
                "disabled_flags": disabled,
                "pinned_model_override": pinned,
                "effective_request_ceiling": effective_ceiling,
                "upstream_preflight_skipped": preflight_skipped,
                "isolated_store_is_user_campaign": isolated_is_user,
                "fixture_manifest_matches_pin": phase1["fixture_manifest_matches_pinned_constant"],
            }
            return
        run.mkdir(parents=True, exist_ok=False)
        for name in ("configuration", "diagnostics", "baseline", "after", "opening", "reports", "turns"):
            (run / name).mkdir()
        prepare_isolated_store(run / "data", scenario_id="FiveTurnGameplay", repo=ROOT, player_campaign_dir=player)
        if same_path(run / "data", player):
            raise RuntimeError("isolated store resolved to the user campaign")
        env["ASHEN_OPENING_RESPONSE_CAPTURE"] = "1"
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        dump(run / "configuration" / "scenario.json", scenario, hidden)
        dump(run / "configuration" / "run.json", {
            "experiment": EXPERIMENT,
            "scenario_id": "FiveTurnGameplay", "mode": "Live", "fixture_response": "success",
            "port": 0, "player_data": str(player), "capture_response": True,
            "player_inputs": [turn["player_input"] for turn in TURNS],
        }, hidden)
        dump(OUT / "safe_configuration.json", {
            "provider": "configured OpenAI client",
            "models": safe_models,
            "credentials_present": True,
            "request_ceiling": effective_ceiling,
            "token_limits": phase1["token_limits"],
            "sdk_retries": 0,
            "host_retries": 0,
            "upstream_preflight_skipped": True,
            "opening_renderer_override": False,
            "opening_response_capture": True,
            "turn_start_reserve": 2,
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
        owned["configured_data_dir"] = ready.get("data_dir")
        owned["isolation_verified"] = ready.get("isolation_verified")
        owned["sdk_retries"] = ready.get("sdk_retries")
        owned["host_retries"] = ready.get("host_retries")
        owned["user_campaign_dir"] = str(player)
        owned["isolated_data_dir"] = str((run / "data").resolve())
        gates = {
            "ready_pid_matches_popen": ready.get("pid") == process.pid,
            "parent_is_controller": owned["parent_pid"] == os.getpid(),
            "executable_is_base": same_path(owned.get("worker_executable"), owned.get("base_executable")),
            "no_interpreter_child": not owned["interpreter_children"],
            "isolation_verified": ready.get("isolation_verified") is True,
            "isolated_dir_is_not_user_campaign": not same_path(ready.get("data_dir"), player),
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
            result["initial_usage"] = usage_view(usage)
            return
        new_row = call("POST", "/api/new_campaign", {"ui_mode": "player"}, timeout=30)
        dump(run / "reports" / "new_campaign.json", {k: v for k, v in new_row.items() if k != "response"} | {"response": clip(new_row["response"])}, hidden)
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
        http_body = opening["response"] if isinstance(opening["response"], dict) else {}
        http_gm = http_body.get("gm_output") if isinstance(http_body.get("gm_output"), dict) else {}
        http_meta = http_gm.get("metadata") if isinstance(http_gm.get("metadata"), dict) else {}
        recovery = latest_opening_recovery(opening_events)
        persisted = persisted_engine(after_open_docs)
        if isinstance(persisted, dict) and isinstance(persisted.get("opening_recovery_debug"), dict):
            recovery = persisted["opening_recovery_debug"]
        if isinstance(http_meta.get("opening_recovery_debug"), dict):
            recovery = http_meta["opening_recovery_debug"]
        opening_record = {
            "http_status": opening["http_status"],
            "api_latency_seconds": opening["api_latency_seconds"],
            "player_facing_text": player_text(opening["response"]),
            "opening_failure_reason": http_body.get("opening_failure_reason"),
            "opening_recovery_class": http_body.get("opening_recovery_class"),
            "opening_recovery_error": http_body.get("opening_recovery_error"),
            "opening_recovery": recovery,
            "opening_source_classification": classify_opening_source(opening["http_status"], recovery, after_open_state),
            "engine": engine_view(opening["response"]),
            "persisted_engine": persisted,
            "provider": provider_slice(opening_events),
            "provider_completed_count": sum(1 for event in opening_events if event.get("event") == "completed"),
            "state_before": before_open_state,
            "state_after": after_open_state,
            "state_delta": compact_delta(before_open_state, after_open_state),
            "changed_documents": changed_documents(before_open_docs, after_open_docs),
            "usage_after": usage_view(budget(run)),
        }
        dump(run / "opening" / "api_response.json", opening["response"], hidden)
        dump(run / "opening" / "record.json", opening_record, hidden)
        result["opening"] = opening_record
        if opening["http_status"] != 200 or after_open_state.get("campaign_started") is not True:
            result["stop_reason"] = "initialization_failed"
            return
        audit = run_grounding_audit(run, hidden)
        result["grounding_audit"] = {
            "decision": audit.get("decision"),
            "reasons": audit.get("reasons"),
            "known_pr_play_41_defect_reproduced": audit.get("known_pr_play_41_defect_reproduced"),
            "active_scene_id": audit.get("active_scene_id"),
            "rumor_probe": audit.get("rumor_probe"),
            "inspection_probe": audit.get("inspection_probe"),
            "movement_probe": audit.get("movement_probe"),
            "fact_leakage": audit.get("fact_leakage"),
            "ai_added_public_facts": audit.get("ai_added_public_facts"),
            "live_store_unchanged_during_probe": audit.get("live_store_unchanged_during_probe"),
            "snapshot_unchanged_during_probe": audit.get("snapshot_unchanged_during_probe"),
            "provider_usage_unchanged_during_probe": audit.get("provider_usage_unchanged_during_probe"),
            "provider_invoked_by_probe": audit.get("provider_invoked_by_probe"),
            "game_api_imported": audit.get("game_api_imported"),
        }
        dump(OUT / "grounding_audit.json", audit, hidden)
        if audit.get("decision") != "PASS":
            result["stop_reason"] = "post_opening_grounding_audit_" + str(audit.get("decision") or "INCONCLUSIVE").lower()
            block_remaining(result, 0, result["stop_reason"])
            return
        usage = budget(run)
        if usage.get("stopped") or int(usage.get("dispatched_requests") or 0) >= effective_ceiling:
            result["stop_reason"] = "provider_budget_exhausted_during_initialization"
            block_remaining(result, 0, result["stop_reason"])
            return
        result["provider_requests_before_gameplay"] = usage.get("dispatched_requests")
        for index, turn in enumerate(TURNS):
            if turn["step_id"] == "T5":
                prior = next((row for row in reversed(result["turns"]) if row.get("step_id") == "T4"), None)
                scene = ((prior or {}).get("state_after") or {}).get("active_scene_id")
                attempted = bool(prior) and prior.get("http_status") is not None
                if not attempted or scene != "old_milestone":
                    result["turns"].append({
                        "step_id": "T5",
                        "player_input": turn["player_input"],
                        "classification": "BLOCKED",
                        "blocked_reason": "BLOCKED BY PRIOR TURN",
                        "prior_turn_attempted": attempted,
                        "observed_scene_after_turn_4": scene,
                        "submitted": False,
                    })
                    result["stop_reason"] = "turn5_blocked_scene_not_old_milestone"
                    break
            usage = budget(run)
            remaining = effective_ceiling - int(usage.get("dispatched_requests") or 0)
            if not can_start_interaction(usage, effective_ceiling) or process.poll() is not None:
                reason = "provider budget cannot safely support the next action" if process.poll() is None else "worker exited"
                result["turns"].append({
                    "step_id": turn["step_id"],
                    "player_input": turn["player_input"],
                    "classification": "BLOCKED",
                    "blocked_reason": reason,
                    "submitted": False,
                    "requests_remaining": remaining,
                    "usage": usage_view(usage),
                })
                result["stop_reason"] = result["stop_reason"] or (
                    "provider_budget_cannot_safely_support_next_action" if process.poll() is None else "worker_exited"
                )
                block_remaining(result, index + 1, result["stop_reason"])
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
                    "current_scene_before": before_state.get("active_scene_id"),
                    "error_type": type(exc).__name__,
                    "error": redact(str(exc)[:500], hidden),
                    "state_before": before_state,
                    "classification": "FAIL",
                    "submitted": True,
                    "retried": False,
                    "provider_after": provider_slice(read_events(run)[event_offset:]),
                    "usage_after": usage_view(budget(run)),
                }
                dump(run / label / "failure.json", failure, hidden)
                result["turns"].append(failure)
                pending = failure["usage_after"].get("pending_requests")
                if process.poll() is not None or pending:
                    result["stop_reason"] = "unrecoverable_turn_failure"
                    block_remaining(result, index + 1, result["stop_reason"])
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
                "submitted": True,
                "retried": False,
                "current_scene_before": before_state.get("active_scene_id"),
                "http_status": row["http_status"],
                "api_latency_seconds": row["api_latency_seconds"],
                "player_facing_text": player_text(row["response"]),
                "engine": engine_view(row["response"]),
                "persisted_engine": persisted_engine(after_docs),
                "provider": provider_slice(events),
                "provider_completed_count": sum(1 for event in events if event.get("event") == "completed"),
                "state_before": before_state,
                "state_after": after_state,
                "state_delta": compact_delta(before_state, after_state),
                "changed_documents": changed_documents(before_docs, after_docs),
                "usage_after": usage_view(budget(run)),
            }
            dump(run / label / "record.json", record, hidden)
            result["turns"].append(record)
            dump(OUT / "live_result.json", result, hidden)
            if process.poll() is not None:
                result["stop_reason"] = "worker_exited"
                block_remaining(result, index + 1, result["stop_reason"])
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
            result["provider_usage"] = usage_view(usage)
        result["events"] = provider_slice(read_events(run)) if run.exists() else []
        user_after = campaign_fingerprint(player)
        result["user_campaign_unchanged"] = user_before.get("files") == user_after.get("files")
        result["user_campaign_after"] = fingerprint_public(user_after)
        hashes_after = source_hashes()
        result["gameplay_sources_unchanged"] = hashes_before == hashes_after
        result["source_drift"] = sorted(set(hashes_before) ^ set(hashes_after) | {key for key in hashes_before if hashes_before.get(key) != hashes_after.get(key)})
        dump(OUT / "live_result.json", result, hidden)
        dump(OUT / "user_campaign_after.json", fingerprint_public(user_after) | {"unchanged": result["user_campaign_unchanged"]}, hidden)
        print(json.dumps({
            "stop_reason": result.get("stop_reason"),
            "opening": (result.get("opening") or {}).get("opening_source_classification"),
            "grounding_audit": (result.get("grounding_audit") or {}).get("decision"),
            "turns": [
                {
                    "step": row.get("step_id"),
                    "http": row.get("http_status"),
                    "scene_after": (row.get("state_after") or {}).get("active_scene_id"),
                    "blocked": row.get("blocked_reason"),
                    "provider_completed": row.get("provider_completed_count"),
                }
                for row in result.get("turns") or []
            ],
            "provider": result.get("provider_usage"),
            "duration_seconds": result.get("duration_seconds"),
            "user_campaign_unchanged": result.get("user_campaign_unchanged"),
            "sources_unchanged": result.get("gameplay_sources_unchanged"),
            "run": stamp,
        }))


if __name__ == "__main__":
    main()
