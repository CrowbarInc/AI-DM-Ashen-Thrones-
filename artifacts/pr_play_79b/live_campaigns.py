"""Live HTTP acceptance for PR-PLAY-79B. Isolated storage. No authored-action buttons.

Player lines are a developer acceptance script, not an unguided person.
One campaign carries conversation and narration so a second opening is not spent.
Stops when the cycle budget is reached. Does not retry by looping turns.
"""
import copy
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(ROOT))
from tests.helpers.storage_isolation import install

install(OUT / "live_data")
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
for key in (
    "ASHEN_DISABLE_PROVIDER_CALLS",
    "ASHEN_DISABLE_LIVE_INTERPRETATION",
    "ASHEN_DISABLE_EXPRESSION_GENERATION",
):
    os.environ.pop(key, None)
for key in (
    "ASHEN_EXPERIMENTAL_BRANCHING",
    "ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS",
    "ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE",
    "ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION",
    "ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION",
    "ASHEN_EXPERIMENTAL_DYNAMIC_NPCS",
    "ASHEN_BOUNDED_SPEECH",
    "ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION",
):
    os.environ[key] = "1"

from fastapi.testclient import TestClient
from game import api, storage

api.log_upstream_api_preflight_at_startup = lambda: None
from tests.test_pr_play_71_lifecycle import create, flags, safe, start

BUDGET_REQUESTS = 25
BUDGET_TOKENS = 50000


def _rows():
    path = Path(os.environ["ASHEN_PROVIDER_USAGE_PATH"])
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _spent(rows):
    completed = [row for row in rows if row.get("event") == "completed" and row.get("sent")]
    tokens = sum(int(row.get("total_tokens") or 0) for row in completed)
    incoming = sum(int(row.get("input_tokens") or 0) for row in completed)
    outgoing = sum(int(row.get("output_tokens") or 0) for row in completed)
    return {"requests": len(completed), "tokens": tokens, "input_tokens": incoming, "output_tokens": outgoing}


def _turn(client, text, provenance):
    before_rows = _rows()
    before_session = storage.load_session()
    before = {
        "scene": before_session.get("active_scene_id"),
        "flags": copy.deepcopy(flags()),
        "focus": (before_session.get("bounded_improvisation") or {}).get("npc_focus"),
    }
    clock = time.perf_counter()
    payload = safe(client.post("/api/chat", json={"text": text}))
    elapsed = round((time.perf_counter() - clock) * 1000, 1)
    current = storage.load_session()
    said = payload["gm_output"]["player_facing_text"]
    audit = current.get("last_background_expression") if isinstance(current.get("last_background_expression"), dict) else {}
    narration = current.get("last_narration") if isinstance(current.get("last_narration"), dict) else {}
    attempt = audit.get("attempt") if isinstance(audit.get("attempt"), dict) else {}
    low = said.casefold()
    return {
        "input": text,
        "provenance": provenance,
        "elapsed_ms": elapsed,
        "before": before,
        "after": {
            "scene": current.get("active_scene_id"),
            "flags": copy.deepcopy(flags()),
            "focus": (current.get("bounded_improvisation") or {}).get("npc_focus"),
            "interlocutor": (current.get("conversational_context") or {}).get("active_interlocutor"),
        },
        "player_facing_text": said,
        "dialogue_adopted": bool(audit.get("adopted")),
        "dialogue_published": bool(audit.get("adopted")) and bool(attempt.get("text")) and str(attempt.get("text")).casefold() in low,
        "dialogue_text": attempt.get("text") if audit.get("adopted") else "",
        "dialogue_reasons": (audit.get("validation") or {}).get("reasons") if isinstance(audit.get("validation"), dict) else audit.get("reason"),
        "narration_adopted": bool(narration.get("adopted")),
        "narration_published": bool(narration.get("adopted")) and str(narration.get("candidate") or "").casefold() in low,
        "narration_text": narration.get("candidate") if narration.get("adopted") else "",
        "narration_reasons": narration.get("reasons"),
        "clarification": "which person" in low or "which available" in low,
        "authored_interception": "not available here yet" in low or "nothing was attempted" in low,
        "new_provider_calls": [
            row for row in _rows()[len(before_rows):]
            if row.get("event") == "completed" and row.get("sent")
        ],
        "usage": _spent(_rows()),
    }


def _campaign(client, name, lines):
    create(client)
    clock = time.perf_counter()
    opening = start(client)
    opening_ms = round((time.perf_counter() - clock) * 1000, 1)
    transcript = [{
        "input": "[start_campaign]",
        "provenance": "campaign start, not a gameplay utterance",
        "elapsed_ms": opening_ms,
        "player_facing_text": opening["gm_output"]["player_facing_text"],
        "after": {"scene": storage.load_session().get("active_scene_id")},
        "usage": _spent(_rows()),
    }]
    stopped = None
    for text in lines:
        spent = _spent(_rows())
        if spent["requests"] >= BUDGET_REQUESTS or spent["tokens"] >= BUDGET_TOKENS:
            stopped = "budget"
            break
        transcript.append(_turn(client, text, "developer acceptance script"))
        (OUT / "live_partial.json").write_text(json.dumps({"campaign": name, "transcript": transcript, "usage": _spent(_rows())}, indent=2), encoding="utf-8")
    snap = safe(client.post("/api/snapshots", json={"label": name}))["snapshot"]["id"]
    saved = storage.load_session()
    saved_view = {
        "campaign_run_id": saved.get("campaign_run_id"),
        "scene": saved.get("active_scene_id"),
        "focus": (saved.get("bounded_improvisation") or {}).get("npc_focus"),
        "interlocutor": (saved.get("conversational_context") or {}).get("active_interlocutor"),
        "flags": copy.deepcopy(flags()),
    }
    create(client)
    safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
    restored = storage.load_session()
    resume = {
        "scene": restored.get("active_scene_id") == saved_view["scene"],
        "campaign": restored.get("campaign_run_id") == saved_view["campaign_run_id"],
        "focus": (restored.get("bounded_improvisation") or {}).get("npc_focus") == saved_view["focus"],
        "interlocutor": (restored.get("conversational_context") or {}).get("active_interlocutor") == saved_view["interlocutor"],
        "flags": flags() == saved_view["flags"],
    }
    if stopped is None and _spent(_rows())["tokens"] < BUDGET_TOKENS and _spent(_rows())["requests"] < BUDGET_REQUESTS:
        transcript.append(_turn(client, lines[-1], "resume continuation"))
    return {"opening_ms": opening_ms, "stopped": stopped, "resume": resume, "saved": saved_view, "transcript": transcript}


def main():
    # One campaign. A second opening would spend the token budget before narration.
    lines = [
        "Hello, Gate Guard.",
        "Who are you?",
        "What do you know about the missing patrol?",
        "When did you last hear about them?",
        "Do you think something happened?",
        "What is this place like?",
        "What about the patrol again?",
        "I look at the notice board.",
        "What do you know about the missing patrol?",
        "I examine the notice board.",
        "I follow the missing patrol rumor.",
        "I examine the weathered milestone.",
        "I look at the mud prints.",
        "Look around.",
        "I step back from the milestone.",
        "I look around the milestone.",
    ]
    report = {"budget": {"requests": BUDGET_REQUESTS, "tokens": BUDGET_TOKENS}, "separate_second_campaign": False}
    with TestClient(api.app) as client:
        report["integrated"] = _campaign(client, "integrated", lines)
    rows = _rows()
    completed = [row for row in rows if row.get("event") == "completed" and row.get("sent")]
    samples = [
        turn["elapsed_ms"]
        for turn in report["integrated"]["transcript"]
        if turn.get("provenance") == "developer acceptance script"
    ]
    ordered = sorted(samples) or [0]
    def pct(p):
        return ordered[min(len(ordered) - 1, max(0, int(round((p / 100) * (len(ordered) - 1)))))]
    published_dialogue = [turn for turn in report["integrated"]["transcript"] if turn.get("dialogue_published")]
    published_narration = [turn for turn in report["integrated"]["transcript"] if turn.get("narration_published")]
    primary = [row for row in completed if row.get("purpose") == "primary_turn"]
    report["usage"] = _spent(rows)
    report["completed_rows"] = len(completed)
    report["published_live_dialogue"] = len(published_dialogue)
    report["published_live_narration"] = len(published_narration)
    report["primary_turn_requests"] = len(primary)
    report["primary_turn_tokens"] = sum(int(row.get("total_tokens") or 0) for row in primary)
    report["clarifications"] = sum(1 for turn in report["integrated"]["transcript"] if turn.get("clarification"))
    report["authored_interceptions"] = sum(1 for turn in report["integrated"]["transcript"] if turn.get("authored_interception"))
    report["latency_ms"] = {
        "mean": round(sum(samples) / len(samples), 1) if samples else None,
        "median": ordered[len(ordered) // 2],
        "p95": pct(95),
        "max": max(samples) if samples else None,
        "n": len(samples),
    }
    report["provider_rows"] = rows
    (OUT / "live_http.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "usage": report["usage"],
        "dialogue": report["published_live_dialogue"],
        "narration": report["published_live_narration"],
        "clarifications": report["clarifications"],
        "interceptions": report["authored_interceptions"],
        "primary_turns": report["primary_turn_requests"],
        "primary_tokens": report["primary_turn_tokens"],
        "resume": report["integrated"]["resume"],
        "latency_ms": report["latency_ms"],
        "stopped": report["integrated"]["stopped"],
    }, indent=2))


if __name__ == "__main__":
    main()
