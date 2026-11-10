"""Isolated browser host for PR-PLAY-79D-F3. No campaign opening and no live provider."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DATA = OUT / "browser_data"
sys.path.insert(0, str(ROOT))
os.environ["ASHEN_TEST_EVIDENCE_DIR"] = str(OUT)
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_PROVIDER_REQUEST_LIMIT"] = "4"
os.environ["ASHEN_PROVIDER_INPUT_TOKEN_LIMIT"] = "50"
os.environ["ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT"] = "50"
os.environ["ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT"] = "80"
os.environ.pop("ASHEN_DISABLE_PROVIDER_CALLS", None)
os.environ.pop("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", None)

from tests.helpers.storage_isolation import install

install(DATA)
os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(OUT / "browser_provider_usage.jsonl")
os.environ["ASHEN_PUBLICATION_TRACE_PATH"] = str(OUT / "browser_publication.jsonl")

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

session = default_session()
session["active_scene_id"] = "frontier_gate"
session["visited_scene_ids"] = ["frontier_gate"]
session["campaign_started"] = True
session["turn_counter"] = 4
session["campaign_run_id"] = "browser-79df3"
session["last_publication"] = {
    "owner": "completed_runtime_response",
    "contract": "FINAL_ENGINE_RESPONSE",
    "final": True,
    "visible": "The gate is quiet.",
    "turn": 4,
    "campaign_run_id": "browser-79df3",
    "dialogue_accepted": False,
}
storage.save_session(session)
storage._save_json(storage.WORLD_PATH, default_world())
storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
storage._save_json(storage.CHARACTER_PATH, default_character())
storage._save_json(storage.COMBAT_PATH, default_combat())
storage._save_json(storage.CONDITIONS_PATH, default_conditions())
storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

SOURCES = ["game/api.py", "game/publication_contract.py", "game/live_chat_interpretation.py", "game/player_http_boundary.py", "static/app.js"]
(OUT / "server_identity.json").write_text(json.dumps({
    "pid": os.getpid(),
    "port": 8114,
    "provider": "simulated-admission-only",
    "live_calls": 0,
    "interpretation": "disabled-until-controlled-refusal",
    "sources": [{"path": rel, "sha256": hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()} for rel in SOURCES],
}, indent=2), encoding="utf-8")


@app.post("/__cycle_control")
def cycle_control(payload: dict):
    """Test-host switch. Not a product route."""
    if payload.get("interpretation") == "on":
        os.environ.pop("ASHEN_DISABLE_LIVE_INTERPRETATION", None)
    else:
        os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
    if "request_limit" in payload:
        os.environ["ASHEN_PROVIDER_REQUEST_LIMIT"] = str(payload["request_limit"])
    return {
        "ok": True,
        "interpretation_disabled": os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION", ""),
        "request_limit": os.environ.get("ASHEN_PROVIDER_REQUEST_LIMIT"),
    }


@app.middleware("http")
async def evidence(request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    if request.url.path.startswith("/api/chat"):
        body = b"".join([chunk async for chunk in response.body_iterator])
        from starlette.responses import Response
        record = {
            "path": request.url.path,
            "status": response.status_code,
            "server_ms": round((time.perf_counter() - started) * 1000, 2),
            "body": json.loads(body) if body else None,
            "pointer": (storage.load_session().get("last_publication") or {}).get("visible"),
            "turn": storage.load_session().get("turn_counter"),
        }
        with (OUT / "browser_network.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return Response(body, status_code=response.status_code, media_type="application/json")
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8114, log_level="warning")
