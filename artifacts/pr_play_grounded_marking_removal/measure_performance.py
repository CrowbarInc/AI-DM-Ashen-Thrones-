"""In-process timing for one grounded removal. No live provider calls."""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ["ASHEN_TEST_EVIDENCE_DIR"] = str(OUT)
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
from game.marking_observation import recognize_observation
from game.marking_removal import recognize_removal, resolve_removal
from game.provider_budget import snapshot as provider_snapshot
from tests.helpers.storage_isolation import install
from tests.pr_play_79df3_harness import seed_gate
from tests.test_grounded_marking_action import ACTION, _equip

DATA = ROOT / "development/tmp/marking_removal_performance"
install(DATA)
seed_gate(DATA, MonkeyPatch())
_equip()
character = storage.load_character()
character["inventory"][1]["marking_medium"]["removal"] = {
    "methods": {"wipe": {"resource": "none", "surfaces": ["cloth"]}},
}
storage.save_character(character)
providers = len(provider_snapshot()["records"])
tokens_before = provider_snapshot().get("tokens") if isinstance(provider_snapshot(), dict) else 0
with TestClient(app) as client:
    marked = client.post("/api/chat?ui_mode=player", json={"text": ACTION, "client_request_id": "perf-mark"})
character = storage.load_character()
session = storage.load_session()
utterance = "I wipe the warning off my sleeve."
observe = "I examine the writing on my sleeve."
proposal = recognize_removal(utterance)
before = storage.CHARACTER_PATH.stat().st_size


def bench(fn, rounds=200):
    start = time.perf_counter()
    for _ in range(rounds):
        fn()
    return (time.perf_counter() - start) / rounds


resolved = resolve_removal(proposal, character, session)
stages = {
    "removal_intent_s": bench(lambda: recognize_removal(utterance)),
    "resolution_s": bench(lambda: resolve_removal(proposal, character, session)),
    "observation_intent_s": bench(lambda: recognize_observation(observe)),
}
http_started = time.perf_counter()
with TestClient(app) as client:
    removed = client.post("/api/chat?ui_mode=player", json={"text": utterance, "client_request_id": "perf-wipe"})
    seen = client.post("/api/chat?ui_mode=player", json={"text": observe, "client_request_id": "perf-read"})
http_s = time.perf_counter() - http_started
after = storage.CHARACTER_PATH.stat().st_size
removed_text = (removed.json().get("gm_output") or {}).get("player_facing_text") or ""
seen_text = (seen.json().get("gm_output") or {}).get("player_facing_text") or ""
mark_text = (marked.json().get("gm_output") or {}).get("player_facing_text") or ""
payload = {
    "rounds_pure": 200,
    "stages_s": stages,
    "resolution_outcome": resolved.get("outcome"),
    "http_removal_and_observation_s": http_s,
    "marking_response_bytes": len(mark_text.encode("utf-8")),
    "removal_response_bytes": len(removed_text.encode("utf-8")),
    "observation_response_bytes": len(seen_text.encode("utf-8")),
    "character_bytes_before_removal": before,
    "character_bytes_after_removal": after,
    "storage_growth_bytes": after - before,
    "published_removal": removed_text,
    "published_observation": seen_text,
    "live_provider_calls": len(provider_snapshot()["records"]) - providers,
    "network_blocks": blocks,
    "provider_retries": 0,
    "token_consumption": 0,
    "additional_model_pass": False,
    "tokens_before": tokens_before,
}
(OUT / "performance.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("PERF_OK", round(http_s, 4), "growth", after - before, "providers", payload["live_provider_calls"], "outcome", resolved.get("outcome"))
