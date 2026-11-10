"""In-process timing for one observation. No live provider calls."""
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
from game.marking_action import recognize_marking
from game.marking_observation import project_observation, recognize_observation, resolve_observation
from game.provider_budget import snapshot as provider_snapshot
from tests.helpers.storage_isolation import install
from tests.pr_play_79df3_harness import seed_gate
from tests.test_grounded_marking_action import ACTION, _equip

DATA = ROOT / "development/tmp/player_observation_performance"
install(DATA)
seed_gate(DATA, MonkeyPatch())
_equip()
providers = len(provider_snapshot()["records"])
with TestClient(app) as client:
    marked = client.post("/api/chat?ui_mode=player", json={"text": ACTION, "client_request_id": "perf-mark"})
character = storage.load_character()
session = storage.load_session()
scene = storage.load_active_scene()
utterance = "I examine the writing on my sleeve."
proposal = recognize_observation(utterance)
resolved = resolve_observation(proposal, character, session, scene)
before = storage.CHARACTER_PATH.stat().st_size


def bench(fn, rounds=200):
    start = time.perf_counter()
    for _ in range(rounds):
        fn()
    return (time.perf_counter() - start) / rounds


stages = {
    "observation_intent_s": bench(lambda: recognize_observation(utterance)),
    "target_resolution_s": bench(lambda: resolve_observation(proposal, character, session, scene)),
    "disclosure_projection_s": bench(lambda: project_observation(character, session, resolved), 50),
    "marking_intent_s": bench(lambda: recognize_marking(ACTION)),
}
http_started = time.perf_counter()
with TestClient(app) as client:
    response = client.post(
        "/api/chat?ui_mode=player",
        json={"text": utterance, "client_request_id": "perf-observe"},
    )
http_s = time.perf_counter() - http_started
after = storage.CHARACTER_PATH.stat().st_size
text = (response.json().get("gm_output") or {}).get("player_facing_text") or ""
mark_text = (marked.json().get("gm_output") or {}).get("player_facing_text") or ""
payload = {
    "rounds_pure": 200,
    "rounds_projection": 50,
    "stages_s": stages,
    "http_observation_s": http_s,
    "marking_response_bytes": len(mark_text.encode("utf-8")),
    "observation_response_bytes": len(text.encode("utf-8")),
    "character_bytes_before_observation": before,
    "character_bytes_after_observation": after,
    "character_unchanged": before == after,
    "published_observation": text,
    "live_provider_calls": len(provider_snapshot()["records"]) - providers,
    "network_blocks": blocks,
    "provider_retries": 0,
    "token_consumption": 0,
    "additional_model_pass": False,
}
(OUT / "performance.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("PERF_OK", round(http_s, 4), "unchanged", before == after, "providers", payload["live_provider_calls"])
