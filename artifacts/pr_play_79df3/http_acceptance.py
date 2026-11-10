"""Final-source HTTP acceptance for PR-PLAY-79D-F3. No campaign opening."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DATA = OUT / "http_data"
sys.path.insert(0, str(ROOT))
os.environ["ASHEN_TEST_EVIDENCE_DIR"] = str(OUT)
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ.pop("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", None)
os.environ.pop("ASHEN_DISABLE_PROVIDER_CALLS", None)

from tests.helpers.storage_isolation import install

install(DATA)
os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(DATA / "provider_usage.jsonl")
os.environ["ASHEN_PUBLICATION_TRACE_PATH"] = str(OUT / "http_events.jsonl")
from game.verification_budget import apply_verification_budget

apply_verification_budget()
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

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

PRIOR_TURN = 4


def seed() -> None:
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    session["campaign_started"] = True
    session["turn_counter"] = PRIOR_TURN
    session["campaign_run_id"] = "http-79df3"
    session["last_publication"] = {
        "owner": "completed_runtime_response",
        "contract": "FINAL_ENGINE_RESPONSE",
        "final": True,
        "visible": "The gate is open.",
        "turn": 1,
        "campaign_run_id": "http-79df3",
        "dialogue_accepted": False,
    }
    storage.save_session(session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def events() -> list[dict]:
    path = OUT / "http_events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    seed()
    trace = []
    with TestClient(app) as client:
        played = client.post("/api/chat?ui_mode=player", json={"text": "I examine the notice board.", "client_request_id": "t1"})
        visible = played.json()["gm_output"]["player_facing_text"]
        pointer = storage.load_session()["last_publication"]["visible"]
        world_after_play = json.dumps(storage.load_world(), sort_keys=True)
        turn_after_play = storage.load_session()["turn_counter"]
        trace.append({"step": "gameplay", "status": played.status_code, "visible": visible, "pointer": pointer, "events": len(events()), "requests": budget.snapshot().get("requests")})
        os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "0"
        os.environ.pop("ASHEN_DISABLE_LIVE_INTERPRETATION", None)
        os.environ["ASHEN_PROVIDER_REQUEST_LIMIT"] = "0"
        refused = client.post("/api/chat?ui_mode=player", json={"text": "Good day, Gate Guard.", "client_request_id": "t2"})
        refusal = refused.json()["gm_output"]["player_facing_text"]
        after_refusal = storage.load_session()
        trace.append({
            "step": "admission_refusal",
            "status": refused.status_code,
            "visible": refusal,
            "pointer": after_refusal["last_publication"]["visible"],
            "events": len(events()),
            "turn": after_refusal["turn_counter"],
            "requests": budget.snapshot().get("requests"),
            "tokens": budget.snapshot().get("total_tokens"),
            "world_unchanged": json.dumps(storage.load_world(), sort_keys=True) == world_after_play,
            "log_class": (storage.load_log()[-1].get("log_meta") or {}).get("response_class"),
        })
        created = client.post("/api/snapshots?ui_mode=player", json={"label": "after-refusal"})
        loaded = client.post("/api/snapshots/load?ui_mode=player", json={"snapshot_id": created.json()["snapshot"]["id"]})
        trace.append({"step": "reload", "status": loaded.status_code, "pointer": storage.load_session()["last_publication"]["visible"], "turn": storage.load_session()["turn_counter"]})
        os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
        os.environ["ASHEN_PROVIDER_REQUEST_LIMIT"] = "4"
        continued = client.post("/api/chat?ui_mode=player", json={"text": "I step back from the notice board.", "client_request_id": "t5"})
        continued_text = continued.json()["gm_output"]["player_facing_text"]
        final_pointer = storage.load_session()["last_publication"]["visible"]
        trace.append({
            "step": "continuation",
            "status": continued.status_code,
            "visible": continued_text,
            "pointer": final_pointer,
            "events": len(events()),
            "event_texts": [row.get("final_player_facing_response") for row in events()],
            "requests": budget.snapshot().get("requests"),
        })
    (OUT / "http_acceptance.json").write_text(json.dumps({
        "trace": trace,
        "gameplay_visible": visible,
        "gameplay_is_publication": pointer == visible and "no gameplay action was taken" not in visible,
        "refusal_visible": "no gameplay action was taken" in refusal,
        "refusal_added_no_event": len([row for row in events() if row.get("final_player_facing_response") == refusal]) == 0,
        "pointer_held_through_refusal_and_reload": trace[2]["pointer"] == visible,
        "turn_held": trace[1]["turn"] == turn_after_play,
        # Historical F3 publication check. Do not re-run this script as proof
        # of the current retreat route. AT-OPT-02 owns that regression.
        "continuation_advances": final_pointer == continued_text and final_pointer != visible,
        "requests_sent": budget.snapshot().get("requests"),
    }, indent=2), encoding="utf-8")
    print((OUT / "http_acceptance.json").read_text(encoding="utf-8")[:4000])


if __name__ == "__main__":
    main()
