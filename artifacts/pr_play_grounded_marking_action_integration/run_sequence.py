"""Provider-free twelve-turn HTTP run for this cycle."""
import ast
import copy
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
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
from game.marking_action import recognize_marking, resolve_marking
from tests.helpers.storage_isolation import install
from tests.pr_play_79df3_harness import seed_gate

install(ROOT / "development/tmp/marking_action_sequence")
seed_gate(ROOT / "development/tmp/marking_action_sequence", MonkeyPatch())
source = (ROOT / "artifacts/pr_play_t05_composition/run_sequence.py").read_text(encoding="utf-8")
turns = ast.literal_eval(source.split("TURNS = ", 1)[1].split("\n]\n", 1)[0] + "\n]")


def snap():
    return copy.deepcopy({
        "session": storage.load_session(),
        "character": storage.load_character(),
        "scene_id": storage.load_session().get("active_scene_id"),
    })


rows = []
started = time.perf_counter()
with TestClient(app) as client:
    for turn in turns:
        before = snap()
        response = client.post("/api/chat?ui_mode=player", json={"text": turn["text"]})
        body = response.json()
        log = storage.load_log()[-1]
        visible = (body.get("gm_output") or {}).get("player_facing_text")
        rows.append({
            "id": turn["id"],
            "request": turn["text"],
            "status": response.status_code,
            "visible": visible,
            "scene": before["scene_id"] and storage.load_session().get("active_scene_id"),
            "character_changed": before["character"] != storage.load_character(),
            "markings": [
                mark.get("content")
                for row in storage.load_character().get("inventory") or []
                if isinstance(row, dict)
                for mark in row.get("markings") or []
            ],
            "resolution_kind": (log.get("resolution") or {}).get("kind"),
            "reason": (((log.get("resolution") or {}).get("metadata") or {}).get("conversational_decision") or {}).get("reason"),
        })
        print(turn["id"], visible, flush=True)
elapsed = time.perf_counter() - started
character = storage.load_character()
session = storage.load_session()
sample = recognize_marking(turns[5]["text"])
resolved = resolve_marking(sample, character, session) if sample else None
payload = {
    "turns": rows,
    "elapsed_s": elapsed,
    "network_blocks": blocks,
    "live_provider_calls": 0,
    "t06_resolution_missing": None if not resolved else resolved.get("missing"),
    "t06_markings": rows[5]["markings"] if len(rows) > 5 else None,
    "t06_visible": rows[5]["visible"] if len(rows) > 5 else None,
}
safe = ROOT / "development/tmp/marking_action_sequence/twelve_turn_after.json"
safe.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("ELAPSED", round(elapsed, 3), "BLOCKS", blocks)
