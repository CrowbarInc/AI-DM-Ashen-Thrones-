"""Normal UI host for PR-PLAY-71V. Isolated data copy. Provider dispatch disabled."""
import copy
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
DATA = OUT / os.environ.get("ASHEN_71V_DATA_NAME", "normal_data")
NETWORK = OUT / os.environ.get("ASHEN_71V_NETWORK_LOG", "browser_network.jsonl")
if not DATA.exists():
    DATA.mkdir()
    for name in ("campaign.json", "character.json", "world.json", "conditions.json"):
        shutil.copy2(ROOT / "data" / name, DATA / name)
    shutil.copytree(ROOT / "data" / "scenes", DATA / "scenes")
os.environ["ASHEN_DATA_DIR"] = str(DATA)
os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(OUT / "provider_usage.jsonl")
os.environ["ASHEN_EXPERIMENTAL_BRANCHING"] = "1"
os.environ["ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ["ASHEN_PLAYTEST_DISABLE_SDK_RETRIES"] = "1"
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
from game import api, storage
from starlette.responses import Response
from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE
import uvicorn

api.call_gpt = lambda *args, **kwargs: copy.deepcopy(RICH_OPENING_GPT_RESPONSE)
api.log_upstream_api_preflight_at_startup = lambda: None


def snapshot():
    return {name: getattr(storage, "load_" + name)() for name in ("session", "world", "character", "combat")}


@api.app.middleware("http")
async def capture(request, call_next):
    start = time.perf_counter()
    raw = await request.body()
    before = snapshot() if request.url.path.startswith("/api/") else None
    response = await call_next(request)
    body = b"".join([chunk async for chunk in response.body_iterator])
    if before is not None:
        row = {
            "path": request.url.path,
            "method": request.method,
            "request": raw.decode(errors="replace"),
            "status": response.status_code,
            "body": body.decode(errors="replace"),
            "server_ms": round((time.perf_counter() - start) * 1000, 1),
        }
        with NETWORK.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return Response(body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)


if __name__ == "__main__":
    uvicorn.run(api.app, host="127.0.0.1", port=8072, log_level="info")
