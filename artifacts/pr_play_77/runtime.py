"""Isolated host for PR-PLAY-76 browser campaigns. Deterministic opening, physical adjudication on."""
import contextvars
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
from tests.helpers.storage_isolation import install

install(OUT / "browser_data")
for key in (
    "ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "ASHEN_DISABLE_PROVIDER_CALLS",
    "ASHEN_DISABLE_LIVE_INTERPRETATION", "ASHEN_DISABLE_EXPRESSION_GENERATION",
    "ASHEN_DISABLE_PROVIDER_RETRIES", "ASHEN_EXPERIMENTAL_BRANCHING",
    "ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS", "ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE",
    "ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION", "ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION",
):
    os.environ[key] = "1"
os.environ["ASHEN_GP_PROVIDER_INTERPRETATION"] = "0"
os.environ["ASHEN_PHYSICAL_PROVIDER"] = "0"
from game import api, storage
from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE

api.call_gpt = lambda *a, **k: copy.deepcopy(RICH_OPENING_GPT_RESPONSE)
api.log_upstream_api_preflight_at_startup = lambda: None
STAGES = contextvars.ContextVar("pr76_stages", default=None)


def snapshot():
    return {name: getattr(storage, "load_" + name)() for name in ("session", "world", "character", "combat")}


def instrument(owner, name, stage):
    original = getattr(owner, name)

    def wrapped(*args, **kwargs):
        started = time.perf_counter()
        result = original(*args, **kwargs)
        trace = STAGES.get()
        if trace is not None:
            trace.setdefault(stage, []).append(round((time.perf_counter() - started) * 1000, 3))
        return result

    setattr(owner, name, wrapped)


instrument(api, "deterministic_conversational_decision", "interpretation_ms")
instrument(storage, "_atomic_write_bytes", "atomic_write_ms")
HOST_SOURCE = {
    name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    for name in ("game/api.py", "game/bounded_improvisation.py", "game/physical_adjudication.py")
}
from starlette.responses import Response


@api.app.middleware("http")
async def capture(request, call_next):
    trace = {}
    token = STAGES.set(trace)
    start = time.perf_counter()
    raw = await request.body()
    before = snapshot() if request.url.path.startswith("/api/") else None
    try:
        response = await call_next(request)
        body = b"".join([chunk async for chunk in response.body_iterator])
        if before is not None:
            text = body.decode(errors="replace")
            row = {
                "path": request.url.path, "method": request.method,
                "request": raw.decode(errors="replace")[:2000],
                "status": response.status_code,
                "player_facing": _facing(text),
                "server_ms": round((time.perf_counter() - start) * 1000, 3),
                "stages": trace,
                "host_source": HOST_SOURCE,
            }
            with (OUT / "browser_network.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row) + "\n")
        return Response(body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
    finally:
        STAGES.reset(token)


def _facing(text):
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return ""
    output = payload.get("gm_output") if isinstance(payload, dict) else None
    if isinstance(output, dict):
        return output.get("player_facing_text") or ""
    return ""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api.app, host="127.0.0.1", port=8091, log_level="warning")
