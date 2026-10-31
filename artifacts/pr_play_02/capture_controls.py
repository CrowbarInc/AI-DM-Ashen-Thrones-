"""Reproducible offline evidence; every SDK client is replaced before use."""
from pathlib import Path
import os
import sys
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace as NS
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
os.environ.update(ASHEN_PLAYTEST_DISABLE_SDK_RETRIES="1", ASHEN_DISABLE_PROVIDER_RETRIES="1",
                  ASHEN_PROVIDER_REQUEST_LIMIT="6", ASHEN_PROVIDER_INPUT_TOKEN_LIMIT="200000",
                  ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT="20000", ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT="220000",
                  ASHEN_PROVIDER_USAGE_PATH=str(OUT / "mock_concurrent_ledger.jsonl"))
from game import provider_budget as budget, live_chat_interpretation as live, gm

constructors, calls = [], []
def create(**kwargs):
    calls.append(kwargs["model"])
    return NS(id=None, model=kwargs["model"], output_text="{}",
              usage=NS(input_tokens=10, output_tokens=2, total_tokens=12))
def constructor(**kwargs):
    constructors.append({k: v for k, v in kwargs.items() if k in {"timeout", "max_retries"}})
    return NS(responses=NS(create=create))
barrier = threading.Barrier(16)
def invoke(i):
    barrier.wait()
    if i % 2:
        live.request_interpretation([], estimated_input=10)
    else:
        gm.call_gpt([], purpose="narration")
with patch("openai.OpenAI", constructor), patch("game.config.get_openai_api_key", return_value="stub-only"):
    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(invoke, range(16)))
snapshot = budget.snapshot()
assert len(calls) == snapshot["requests"] == snapshot["dispatched_requests"] == 6
assert len([e for e in snapshot["events"] if e["event"] == "rejected"]) == 10
(OUT / "mock_concurrent_snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
(OUT / "constructor_evidence.json").write_text(json.dumps({"constructors": constructors,
    "mock_dispatch_count": len(calls), "live_requests": 0, "note": "SDK constructors replaced; no network transport"}, indent=2), encoding="utf-8")
print("six mock dispatches, ten pre-dispatch rejections; zero live requests")
