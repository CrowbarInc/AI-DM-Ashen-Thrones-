"""In-process timing for one grounded marking. No live provider calls."""
import hashlib
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
for key in (
    "ASHEN_DISABLE_PROVIDER_CALLS",
    "ASHEN_DISABLE_LIVE_INTERPRETATION",
    "ASHEN_DISABLE_EXPRESSION_GENERATION",
    "ASHEN_DISABLE_PROVIDER_RETRIES",
    "ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT",
):
    os.environ[key] = "1"
for key in (
    "OPENAI_API_KEY",
    "ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION",
    "ASHEN_EXPERIMENTAL_DYNAMIC_NPCS",
    "ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE",
    "ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION",
):
    os.environ.pop(key, None)
blocks = []


def guard(event, args):
    if event in ("socket.connect", "socket.getaddrinfo"):
        dest = args[1] if event == "socket.connect" else args[0]
        host = dest[0] if isinstance(dest, tuple) else dest
        if host not in ("127.0.0.1", "::1", "localhost"):
            blocks.append(str(dest))
            raise RuntimeError("Live networking forbidden")


sys.addaudithook(guard)
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from game import storage
from game.api import app
from game.marking_action import (
    _resolve_content,
    _resolve_medium,
    _resolve_target,
    recognize_marking,
    resolve_marking,
)
from tests.helpers.storage_isolation import install
from tests.test_grounded_marking_action import ACTION, _equip

install(ROOT / "development/tmp/marking_action_performance")
from tests.pr_play_79df3_harness import seed_gate

seed_gate(ROOT / "development/tmp/marking_action_performance", MonkeyPatch())
_equip()
character = storage.load_character()
session = storage.load_session()
before = storage.CHARACTER_PATH.stat().st_size
proposal = recognize_marking(ACTION)


def bench(fn, rounds=200):
    start = time.perf_counter()
    for _ in range(rounds):
        fn()
    return (time.perf_counter() - start) / rounds


stages = {
    "intent_classification_s": bench(lambda: recognize_marking(ACTION)),
    "object_resolution_s": bench(lambda: _resolve_target(proposal["target_phrase"], character, session)),
    "medium_resolution_s": bench(lambda: _resolve_medium(proposal["medium_phrase"], character)),
    "content_resolution_s": bench(lambda: _resolve_content(proposal["content_phrase"], session)),
    "prerequisite_and_resolution_s": bench(lambda: resolve_marking(proposal, character, session), 50),
}
http_started = time.perf_counter()
with TestClient(app) as client:
    response = client.post(
        "/api/chat?ui_mode=player",
        json={"text": ACTION, "client_request_id": "perf-mark-1"},
    )
http_s = time.perf_counter() - http_started
reload_started = time.perf_counter()
reloaded = storage.load_character()
reload_s = time.perf_counter() - reload_started
after = storage.CHARACTER_PATH.stat().st_size
marks = [
    mark.get("content")
    for row in reloaded.get("inventory") or []
    if isinstance(row, dict)
    for mark in row.get("markings") or []
]
text = (response.json().get("gm_output") or {}).get("player_facing_text") or ""
safe = ROOT / "development/tmp/marking_action_performance/performance.json"
import json
safe.write_text(json.dumps({
    "rounds_pure": 200,
    "rounds_resolution": 50,
    "stages_s": stages,
    "http_commit_and_publication_s": http_s,
    "save_reload_s": reload_s,
    "character_bytes_before": before,
    "character_bytes_after": after,
    "byte_growth": after - before,
    "mark_count": len(marks),
    "mark_content_sha256": hashlib.sha256("|".join(marks).encode()).hexdigest(),
    "published_success": "The marking is on it now." in text,
    "live_provider_calls": 0,
    "network_blocks": blocks,
    "provider_retries": 0,
    "token_consumption": 0,
}, indent=2), encoding="utf-8")
print("PERF_OK", round(http_s, 4), "growth", after - before, "marks", len(marks))
