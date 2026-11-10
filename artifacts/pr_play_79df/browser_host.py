"""Isolated final-source browser host. Copies the initialized campaign; new ledger."""
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
SOURCE = ROOT / "artifacts" / "pr_play_79d" / "browser_data"
DATA = OUT / "browser_data"
if not DATA.exists():
    shutil.copytree(
        SOURCE, DATA,
        ignore=shutil.ignore_patterns("provider_usage.jsonl", "publication_events.jsonl"),
    )
    manifest = [
        {"path": str(p.relative_to(SOURCE)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in sorted(SOURCE.rglob("*"))
        if p.is_file() and p.name not in {"provider_usage.jsonl", "publication_events.jsonl"}
    ]
    (OUT / "browser_fixture.json").write_text(json.dumps({
        "source": str(SOURCE),
        "files": manifest,
        "provenance": "79D initialized continuation copied for 79D-F; not a fresh opening",
        "execution_ledger": "fresh; admission controls unchanged",
    }, indent=2), encoding="utf-8")

from tests.helpers.storage_isolation import install

install(DATA)
os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(OUT / "browser_provider_usage.jsonl")
os.environ["ASHEN_PUBLICATION_TRACE_PATH"] = str(OUT / "browser_publication.jsonl")
os.environ["ASHEN_PROVIDER_REQUEST_LIMIT"] = "5"
os.environ["ASHEN_PROVIDER_INPUT_TOKEN_LIMIT"] = "4000"
os.environ["ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT"] = "1000"
os.environ["ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT"] = "5000"
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
for key in ("ASHEN_DISABLE_PROVIDER_CALLS", "ASHEN_DISABLE_LIVE_INTERPRETATION", "ASHEN_DISABLE_EXPRESSION_GENERATION"):
    os.environ.pop(key, None)
for suffix in (
    "BRANCHING", "BRANCHING_NEW_CAMPAIGNS", "PLAYER_INITIATIVE", "WORLD_IMPROVISATION",
    "PHYSICAL_ADJUDICATION", "DYNAMIC_NPCS", "INTEGRATED_NARRATION",
):
    os.environ["ASHEN_EXPERIMENTAL_" + suffix] = "1"
os.environ["ASHEN_BOUNDED_SPEECH"] = "1"

from game import api, storage
from game.config import DEFAULT_MODEL_NAME
from starlette.responses import Response

SOURCES = [
    "game/bounded_improvisation.py", "game/publication_contract.py", "game/integrated_play.py",
    "game/physical_adjudication.py", "game/player_http_boundary.py", "game/exploration.py",
    "game/api.py", "static/app.js", "static/index.html",
]
(OUT / "server_identity.json").write_text(json.dumps({
    "pid": os.getpid(),
    "python": sys.version,
    "port": 8111,
    "model": DEFAULT_MODEL_NAME,
    "api_key_present": bool(os.environ.get("OPENAI_API_KEY")),
    "provider_limits": {"requests": 5, "input": 4000, "output": 1000, "total": 5000},
    "retries_disabled": True,
    "sources": [{"path": rel, "sha256": hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()} for rel in SOURCES],
}, indent=2), encoding="utf-8")


def _ledger_rows():
    path = OUT / "browser_provider_usage.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@api.app.middleware("http")
async def evidence(request, call_next):
    started = time.perf_counter()
    wall_start = time.time()
    raw = await request.body()
    before = storage.load_session() if request.url.path in {"/api/chat", "/api/snapshots/load"} else None
    ledger_before = len(_ledger_rows())
    response = await call_next(request)
    body = b"".join([chunk async for chunk in response.body_iterator])
    wall_end = time.time()
    new_rows = _ledger_rows()[ledger_before:]
    row = {
        "path": request.url.path,
        "method": request.method,
        "request": raw.decode("utf-8", errors="replace"),
        "status": response.status_code,
        "t2_wall": wall_start,
        "t5_wall": wall_end,
        "server_monotonic_ms": round((time.perf_counter() - started) * 1000, 2),
        "provider_rows": [
            {key: item.get(key) for key in (
                "event", "attempt_id", "purpose", "owner", "sent", "input_tokens",
                "output_tokens", "total_tokens", "latency_ms", "model", "retry_attempt", "accepted",
            )}
            for item in new_rows
        ],
        "response": json.loads(body) if "application/json" in response.headers.get("content-type", "") else None,
        "before": before,
        "after": storage.load_session() if before else None,
    }
    if row["response"] is not None:
        with (OUT / "browser_network.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return Response(body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)


if __name__ == "__main__":
    import uvicorn
    (OUT / "browser_host.pid").write_text(str(os.getpid()), encoding="utf-8")
    uvicorn.run(api.app, host="127.0.0.1", port=8111, log_level="warning")
