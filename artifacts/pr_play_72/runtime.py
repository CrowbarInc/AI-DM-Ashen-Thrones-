"""Isolated normal application host and diagnostic wrappers; offline provider fixture."""
import contextvars
import copy
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
from tests.helpers.storage_isolation import install

DATA = install(OUT / os.environ.get("PR72_STORAGE", "http_data"))
for key in ("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "ASHEN_DISABLE_PROVIDER_CALLS",
            "ASHEN_DISABLE_LIVE_INTERPRETATION", "ASHEN_DISABLE_EXPRESSION_GENERATION",
            "ASHEN_DISABLE_PROVIDER_RETRIES", "ASHEN_EXPERIMENTAL_BRANCHING",
            "ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS", "ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE"):
    os.environ[key] = "1"
from game import api, storage
from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE

api.call_gpt = lambda *a, **k: copy.deepcopy(RICH_OPENING_GPT_RESPONSE)
api.log_upstream_api_preflight_at_startup = lambda: None

STAGES = contextvars.ContextVar("pr72_stages", default=None)


def snapshot():
    return {name: getattr(storage, "load_" + name)() for name in ("session", "world", "character", "combat")}


def instrument(owner, name, stage, decision=False):
    original = getattr(owner, name)
    def wrapped(*a, **kw):
        started = time.perf_counter()
        result = original(*a, **kw)
        trace = STAGES.get()
        if trace is not None:
            trace.setdefault(stage, []).append(round((time.perf_counter() - started) * 1000, 3))
            if decision and result is not None:
                trace["interpretation"] = result.to_public_dict()
        return result
    setattr(owner, name, wrapped)


instrument(api, "deterministic_conversational_decision", "interpretation_ms", True)
instrument(api, "_resolve_engine_noncombat_seam", "resolver_ms")
instrument(storage, "_atomic_write_bytes", "atomic_write_ms")
instrument(api, "_finalize_investigation_publication", "publication_ms")


from starlette.responses import Response
@api.app.middleware("http")
async def capture(request, call_next):
    trace = {}; token = STAGES.set(trace)
    start = time.perf_counter(); raw = await request.body()
    before = snapshot() if request.url.path.startswith("/api/") else None
    try:
        response = await call_next(request)
        body = b"".join([chunk async for chunk in response.body_iterator])
        if before is not None:
            row = dict(path=request.url.path, method=request.method, request=raw.decode(errors="replace"),
                       status=response.status_code, response=body.decode(errors="replace"),
                       server_ms=round((time.perf_counter()-start)*1000, 3),
                       stages=trace, authority_before=before, authority_after=snapshot())
            with (OUT / os.environ.get("PR72_NETWORK", "http_network.jsonl")).open("a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
        return Response(body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
    finally:
        STAGES.reset(token)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api.app, host="127.0.0.1", port=8073, log_level="warning")
