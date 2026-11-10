"""Pre-fix traces for admission ceilings and accounting unavailability."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DATA = OUT / "reproduction_interpretation"
sys.path.insert(0, str(ROOT))
os.environ["ASHEN_TEST_EVIDENCE_DIR"] = str(OUT)
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ.pop("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", None)
os.environ.pop("ASHEN_DISABLE_LIVE_INTERPRETATION", None)
os.environ.pop("ASHEN_DISABLE_PROVIDER_CALLS", None)

from tests.helpers.storage_isolation import install

install(DATA)
os.environ["ASHEN_PROVIDER_REQUEST_LIMIT"] = "4"
os.environ["ASHEN_PROVIDER_INPUT_TOKEN_LIMIT"] = "1"
os.environ["ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT"] = "2000"
os.environ["ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT"] = "10000"
os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(DATA / "provider_usage.jsonl")
os.environ["ASHEN_PUBLICATION_TRACE_PATH"] = str(OUT / "reproduction_interpretation_events.jsonl")

from fastapi.testclient import TestClient

from game import provider_budget as budget
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

PRIOR = 'Gate Guard says, "The notice board mentions a missing patrol."'


def seed() -> None:
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    session["campaign_started"] = True
    session["turn_counter"] = 4
    session["campaign_run_id"] = "repro-79df3-b"
    session["last_publication"] = {
        "owner": "integrated_play.commit_integrated",
        "contract": "FINAL_ENGINE_RESPONSE",
        "final": True,
        "visible": PRIOR,
        "dialogue_accepted": True,
        "turn": 4,
        "campaign_run_id": "repro-79df3-b",
    }
    storage.save_session(session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def capture(client, label: str) -> dict:
    before = storage.load_session()
    usage = budget.snapshot()
    response = client.post(
        "/api/chat?ui_mode=player",
        json={"text": "Good day, Gate Guard.", "client_request_id": label},
    )
    after = storage.load_session()
    path = OUT / "reproduction_interpretation_events.jsonl"
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.exists() else []
    body = response.json()
    return {
        "label": label,
        "status": response.status_code,
        "visible": (body.get("gm_output") or {}).get("player_facing_text"),
        "requests_before": usage.get("requests"),
        "requests_after": budget.snapshot().get("requests"),
        "tokens_after": budget.snapshot().get("total_tokens"),
        "pointer_unchanged": (after.get("last_publication") or {}).get("visible") == (before.get("last_publication") or {}).get("visible"),
        "turn_unchanged": after.get("turn_counter") == before.get("turn_counter"),
        "events": len(events),
        "last_validation": (events[-1] or {}).get("validation_outcome") if events else None,
        "last_category": (events[-1] or {}).get("response_category") if events else None,
        "last_owner": (events[-1] or {}).get("publication_owner") if events else None,
    }


def reset_accounting(path: Path) -> None:
    budget._REQUESTS = 0
    budget._STOPPED = False
    budget._STOP_REASON = ""
    budget._INITIALIZED = False
    budget._INPUT = 0
    budget._OUTPUT = 0
    budget._RESERVED_INPUT = 0
    budget._RESERVED_OUTPUT = 0
    budget._LEDGER_PATH = None
    budget._EVENTS.clear()
    budget._ATTEMPTS.clear()
    budget._RECORDS.clear()
    os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(path)


def main() -> None:
    seed()
    rows = []
    with TestClient(app) as client:
        rows.append(capture(client, "input-token-ceiling"))
        reset_accounting(DATA / "blocked_ledger")
        (DATA / "blocked_ledger").mkdir()
        os.environ["ASHEN_PROVIDER_INPUT_TOKEN_LIMIT"] = "8000"
        rows.append(capture(client, "accounting-unavailable"))
    (OUT / "reproduction_interpretation.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
