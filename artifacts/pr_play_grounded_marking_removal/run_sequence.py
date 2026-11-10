"""Provider-free twelve-turn HTTP run compared with the immediate predecessor."""
import ast
import copy
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
from game.marking_action import recognize_marking, resolve_marking
from game.marking_removal import recognize_removal
from game.provider_budget import snapshot as provider_snapshot
from tests.helpers.storage_isolation import install
from tests.pr_play_79df3_harness import seed_gate

DATA = ROOT / "development/tmp/marking_removal_sequence"
install(DATA)
seed_gate(DATA, MonkeyPatch())
source = (ROOT / "artifacts/pr_play_t05_composition/run_sequence.py").read_text(encoding="utf-8")
turns = ast.literal_eval(source.split("TURNS = ", 1)[1].split("\n]\n", 1)[0] + "\n]")
prior = json.loads(
    (ROOT / "artifacts/pr_play_player_marking_observation/twelve_turn_after.json").read_text(encoding="utf-8")
)
prior_by_id = {row["id"]: row for row in prior["turns"]}
providers = len(provider_snapshot()["records"])


def snap():
    return copy.deepcopy({
        "character": storage.load_character(),
        "scene_id": storage.load_session().get("active_scene_id"),
    })


rows = []
started = time.perf_counter()
with TestClient(app) as client:
    for turn in turns:
        before = snap()
        response = client.post("/api/chat?ui_mode=player", json={"text": turn["text"], "client_request_id": turn["id"]})
        body = response.json()
        log = storage.load_log()[-1]
        visible = (body.get("gm_output") or {}).get("player_facing_text")
        previous = prior_by_id.get(turn["id"], {})
        rows.append({
            "id": turn["id"],
            "request": turn["text"],
            "status": response.status_code,
            "visible": visible,
            "predecessor_visible": previous.get("visible"),
            "visible_unchanged": visible == previous.get("visible"),
            "scene": storage.load_session().get("active_scene_id"),
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
elapsed = time.perf_counter() - started
sample = recognize_marking(turns[5]["text"])
resolved = resolve_marking(sample, storage.load_character(), storage.load_session()) if sample else None
payload = {
    "turns": rows,
    "elapsed_s": elapsed,
    "network_blocks": blocks,
    "live_provider_calls": len(provider_snapshot()["records"]) - providers,
    "t06_recognized_as_removal": recognize_removal(turns[5]["text"]) is not None,
    "t06_resolution_missing": None if not resolved else resolved.get("missing"),
    "t06_visible": rows[5]["visible"],
    "unchanged_ids": [row["id"] for row in rows if row["visible_unchanged"]],
    "changed_ids": [row["id"] for row in rows if not row["visible_unchanged"]],
}
(OUT / "twelve_turn_after.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("ELAPSED", round(elapsed, 3), "CHANGED", payload["changed_ids"], "PROVIDERS", payload["live_provider_calls"], "REMOVAL", payload["t06_recognized_as_removal"])
