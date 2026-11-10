"""Live HTTP acceptance for PR-PLAY-79C. Isolated storage. No authored-action buttons.

One opening is kept as an initialized seed for the browser. Later turns are not
a second opening. Player lines are a developer acceptance script.
"""
import copy
import hashlib
import json
import os
import shutil
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


def _fold(value):
    return (
        str(value or "")
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .casefold()
    )


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
    retries = sum(1 for row in completed if int(row.get("retry_attempt") or 0) > 0)
    return {
        "requests": len(completed),
        "tokens": tokens,
        "input_tokens": incoming,
        "output_tokens": outgoing,
        "retries": retries,
    }


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
    publication = current.get("last_publication") if isinstance(current.get("last_publication"), dict) else {}
    attempt = audit.get("attempt") if isinstance(audit.get("attempt"), dict) else {}
    speech = str(attempt.get("text") or "")
    low = _fold(said)
    new_rows = [row for row in _rows()[len(before_rows):] if row.get("event") == "completed" and row.get("sent")]
    adopted = bool(audit.get("adopted"))
    published = adopted and bool(speech) and _fold(speech) in low
    narration_adopted = bool(narration.get("adopted")) and narration.get("requested") is not False
    narration_text = str(narration.get("candidate") or "")
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
            "publication": publication,
        },
        "player_facing_text": said,
        "dialogue_adopted": adopted,
        "dialogue_published": published,
        "dialogue_replaced": adopted and not published,
        "dialogue_text": speech if adopted else "",
        "dialogue_reasons": (audit.get("validation") or {}).get("reasons") if isinstance(audit.get("validation"), dict) else audit.get("reason"),
        "narration_adopted": narration_adopted,
        "narration_published": narration_adopted and bool(narration_text) and _fold(narration_text) in low,
        "narration_text": narration_text if narration_adopted else "",
        "narration_reasons": narration.get("reasons"),
        "clarification": "which person" in low or "which available" in low or "which do you mean" in low,
        "authored_interception": "not available here yet" in low or "nothing was attempted" in low,
        "primary_narration": any(row.get("purpose") == "primary_turn" for row in new_rows),
        "new_provider_calls": new_rows,
        "usage": _spent(_rows()),
    }


def _copy_seed():
    seed = OUT / "initialized_seed"
    if seed.exists():
        shutil.rmtree(seed)
    shutil.copytree(OUT / "live_data", seed)
    digest = hashlib.sha256()
    for path in sorted(seed.rglob("*")):
        if path.is_file():
            digest.update(path.name.encode())
            digest.update(path.read_bytes())
    return {"path": str(seed), "sha256": digest.hexdigest(), "provenance": "restored initialized campaign, not a new opening"}


def _campaign(client, name, lines):
    create(client)
    clock = time.perf_counter()
    opening = start(client)
    opening_ms = round((time.perf_counter() - clock) * 1000, 1)
    seed = _copy_seed()
    transcript = [{
        "input": "[start_campaign]",
        "provenance": "fresh campaign opening",
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
        (OUT / "live_partial.json").write_text(
            json.dumps({"campaign": name, "transcript": transcript, "usage": _spent(_rows())}, indent=2),
            encoding="utf-8",
        )
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
        transcript.append(_turn(client, "I look around the milestone.", "resume continuation"))
    return {
        "opening_ms": opening_ms,
        "stopped": stopped,
        "resume": resume,
        "saved": saved_view,
        "seed": seed,
        "transcript": transcript,
    }


def _streak(transcript):
    best = current = 0
    for turn in transcript:
        if turn.get("dialogue_published"):
            current += 1
            best = max(best, current)
        elif turn.get("provenance") == "developer acceptance script":
            current = 0
    return best


def main():
    lines = [
        "Hello, Gate Guard.",
        "Who are you?",
        "What do you know about the missing patrol?",
        "When did you last hear about them?",
        "Do you think something happened?",
        "What is this place like?",
        "What about the patrol again?",
        "You mentioned the patrol earlier. What else?",
        "I look around.",
        "I approach the notice board.",
        "I step back from the notice board.",
        "I examine the notice board.",
        "I follow the missing patrol rumor.",
        "I examine the weathered milestone.",
        "I look at the mud prints.",
        "Look around.",
        "I step back from the milestone.",
    ]
    report = {
        "budget": {"requests": BUDGET_REQUESTS, "tokens": BUDGET_TOKENS},
        "separate_second_campaign": False,
        "opening_reuse": "initialized seed copied after the single opening",
    }
    with TestClient(api.app) as client:
        report["integrated"] = _campaign(client, "integrated", lines)
    rows = _rows()
    completed = [row for row in rows if row.get("event") == "completed" and row.get("sent")]
    turns = [turn for turn in report["integrated"]["transcript"] if turn.get("provenance") == "developer acceptance script"]
    samples = [turn["elapsed_ms"] for turn in turns]
    ordered = sorted(samples) or [0]

    def pct(p):
        return ordered[min(len(ordered) - 1, max(0, int(round((p / 100) * (len(ordered) - 1)))))]

    published_dialogue = [turn for turn in turns if turn.get("dialogue_published")]
    published_narration = [turn for turn in report["integrated"]["transcript"] if turn.get("narration_published")]
    primary = [row for row in completed if row.get("purpose") == "primary_turn"]
    report["usage"] = _spent(rows)
    report["completed_rows"] = len(completed)
    report["accepted_live_dialogue"] = sum(1 for turn in turns if turn.get("dialogue_adopted"))
    report["published_live_dialogue"] = len(published_dialogue)
    report["visible_live_dialogue"] = len(published_dialogue)
    report["dialogue_replacements"] = sum(1 for turn in turns if turn.get("dialogue_replaced"))
    report["consecutive_published_dialogue"] = _streak(report["integrated"]["transcript"])
    report["accepted_live_narration"] = sum(1 for turn in report["integrated"]["transcript"] if turn.get("narration_adopted"))
    report["published_live_narration"] = len(published_narration)
    report["primary_turn_requests"] = len(primary)
    report["primary_turn_tokens"] = sum(int(row.get("total_tokens") or 0) for row in primary)
    report["redundant_primary_after_opening"] = max(0, len(primary) - 1)
    report["clarifications"] = sum(1 for turn in turns if turn.get("clarification"))
    report["authored_interceptions"] = sum(1 for turn in turns if turn.get("authored_interception"))
    gameplay_tokens = report["usage"]["tokens"] - int(primary[0].get("total_tokens") or 0) if primary else report["usage"]["tokens"]
    report["latency_ms"] = {
        "mean": round(sum(samples) / len(samples), 1) if samples else None,
        "median": ordered[len(ordered) // 2],
        "p95": pct(95),
        "max": max(samples) if samples else None,
        "n": len(samples),
        "opening": report["integrated"]["opening_ms"],
    }
    report["tokens_per_published_live_response"] = (
        round(gameplay_tokens / max(1, len(published_dialogue) + len(published_narration)), 1)
    )
    report["provider_rows"] = rows
    (OUT / "live_http.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "usage": report["usage"],
        "accepted_dialogue": report["accepted_live_dialogue"],
        "published_dialogue": report["published_live_dialogue"],
        "replacements": report["dialogue_replacements"],
        "streak": report["consecutive_published_dialogue"],
        "narration": report["published_live_narration"],
        "primary_turns": report["primary_turn_requests"],
        "redundant_primary": report["redundant_primary_after_opening"],
        "clarifications": report["clarifications"],
        "interceptions": report["authored_interceptions"],
        "resume": report["integrated"]["resume"],
        "latency_ms": report["latency_ms"],
        "stopped": report["integrated"]["stopped"],
    }, indent=2))


if __name__ == "__main__":
    main()
