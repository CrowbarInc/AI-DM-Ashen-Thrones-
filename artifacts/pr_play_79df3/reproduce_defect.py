"""Reproduce the PR-PLAY-79D-F2 operational-refusal publication mismatch.

Runs before the classification repair. Uses the real HTTP boundary and a
fresh provider ledger. Does not write repository data/.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DATA = OUT / "reproduction_data"
sys.path.insert(0, str(ROOT))
os.environ["ASHEN_TEST_EVIDENCE_DIR"] = str(OUT)
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ["ASHEN_PLAYTEST_DISABLE_SDK_RETRIES"] = "1"
os.environ.pop("ASHEN_DISABLE_LIVE_INTERPRETATION", None)
os.environ.pop("ASHEN_DISABLE_PROVIDER_CALLS", None)

from tests.helpers.storage_isolation import install

install(DATA)
os.environ["ASHEN_PROVIDER_REQUEST_LIMIT"] = "0"
os.environ["ASHEN_PROVIDER_INPUT_TOKEN_LIMIT"] = "8000"
os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(DATA / "provider_usage.jsonl")
os.environ["ASHEN_PUBLICATION_TRACE_PATH"] = str(OUT / "reproduction_events.jsonl")

from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_session,
    default_world,
)
from game.provider_budget import snapshot

PRIOR = 'Gate Guard says, "The notice board mentions a missing patrol."'
PHRASES = (
    "Good day, Gate Guard.",
    "I would like a word with the gate guard about the weather.",
    "Blargh the seventh bell.",
)


def seed() -> None:
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    session["campaign_started"] = True
    session["turn_counter"] = 4
    session["campaign_run_id"] = session.get("campaign_run_id") or "repro-79df3"
    session["last_publication"] = {
        "owner": "integrated_play.commit_integrated",
        "contract": "FINAL_ENGINE_RESPONSE",
        "final": True,
        "dialogue_accepted": True,
        "dialogue_published": True,
        "visible": PRIOR,
        "turn": 4,
        "campaign_run_id": session["campaign_run_id"],
    }
    storage.save_session(session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def main() -> None:
    seed()
    before = storage.load_session()
    world_before = json.dumps(storage.load_world(), sort_keys=True)
    client = TestClient(app)
    rows = []
    with client:
        for phrase in PHRASES:
            usage = snapshot()
            response = client.post("/api/chat?ui_mode=player", json={"text": phrase, "client_request_id": phrase})
            after = storage.load_session()
            body = response.json()
            text = ((body.get("gm_output") or {}).get("player_facing_text"))
            events = []
            path = OUT / "reproduction_events.jsonl"
            if path.exists():
                events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            rows.append({
                "input": phrase,
                "status": response.status_code,
                "visible": text,
                "requests_before": usage.get("requests"),
                "requests_after": snapshot().get("requests"),
                "tokens_after": snapshot().get("total_tokens"),
                "turn_before": before.get("turn_counter"),
                "turn_after": after.get("turn_counter"),
                "pointer_before": (before.get("last_publication") or {}).get("visible"),
                "pointer_after": (after.get("last_publication") or {}).get("visible"),
                "publication_events": len(events),
                "last_event": events[-1] if events else None,
                "world_unchanged": json.dumps(storage.load_world(), sort_keys=True) == world_before,
                "log_count": len(storage.load_log()),
            })
            if text and "no gameplay action was taken" in text:
                break
            before = after
    (OUT / "reproduction_trace.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2)[:4000])


if __name__ == "__main__":
    main()
