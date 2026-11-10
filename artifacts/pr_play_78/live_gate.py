"""A few live narration and dialogue turns at the gate. Isolated data."""
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
DATA = OUT / "live_data"
if DATA.exists():
    shutil.rmtree(DATA)
DATA.mkdir()
os.environ["ASHEN_DATA_DIR"] = str(DATA)
os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(DATA / "provider_usage.jsonl")
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "0"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "0"
os.environ["ASHEN_BOUNDED_SPEECH"] = "1"
os.environ["ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION"] = "1"
os.environ["ASHEN_EXPERIMENTAL_BRANCHING"] = "1"
os.environ["ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS"] = "1"
os.environ["ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE"] = "1"
os.environ["ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION"] = "1"
os.environ["ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION"] = "1"
os.environ["ASHEN_EXPERIMENTAL_DYNAMIC_NPCS"] = "1"

import copy
from fastapi.testclient import TestClient
from game import api, storage
from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE

api.call_gpt = lambda *a, **k: copy.deepcopy(RICH_OPENING_GPT_RESPONSE)
api.log_upstream_api_preflight_at_startup = lambda: None
for name in ("campaign.json", "character.json", "world.json", "conditions.json"):
    shutil.copy2(ROOT / "data" / name, storage.DATA_DIR / name)
(storage.DATA_DIR / "scenes").mkdir(parents=True, exist_ok=True)
for path in (ROOT / "data" / "scenes").glob("*.json"):
    shutil.copy2(path, storage.SCENES_DIR / path.name)

TURNS = [
    "I look around.",
    "I stand up.",
    "Approach the guard and greet him.",
    "Ask the guard about the warning.",
    "Who are you?",
    "Thank the guard.",
]


def main():
    rows = []
    with TestClient(api.app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        assert client.post("/api/start_campaign").status_code == 200
        for index, text in enumerate(TURNS):
            clock = time.perf_counter()
            response = client.post("/api/chat", json={"text": text, "client_request_id": f"live-{index}"})
            elapsed = round((time.perf_counter() - clock) * 1000, 1)
            payload = response.json()
            facing = payload.get("gm_output", {}).get("player_facing_text", "")
            session = storage.load_session()
            speech = session.get("last_background_expression") if isinstance(session.get("last_background_expression"), dict) else {}
            narration = session.get("last_narration") if isinstance(session.get("last_narration"), dict) else {}
            rows.append({
                "input": text,
                "player_facing_text": facing,
                "elapsed_ms": elapsed,
                "speech_adopted": bool(speech.get("adopted")),
                "speech_reasons": (speech.get("validation") or {}).get("reasons") if isinstance(speech.get("validation"), dict) else speech.get("reason"),
                "narration_adopted": bool(narration.get("adopted")),
                "narration_reasons": narration.get("reasons"),
                "status": response.status_code,
            })
    usage = DATA / "provider_usage.jsonl"
    tokens = 0
    requests = 0
    if usage.exists():
        for line in usage.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            requests += 1
            tokens += int(row.get("total_tokens") or 0)
    summary = {
        "turns": rows,
        "accepted_dialogue": sum(1 for row in rows if row["speech_adopted"]),
        "accepted_narration": sum(1 for row in rows if row["narration_adopted"]),
        "provider_lines": requests,
        "provider_tokens": tokens,
    }
    (OUT / "live_gate.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("accepted_dialogue", "accepted_narration", "provider_lines", "provider_tokens")}))
    for row in rows:
        print(row["input"], row["elapsed_ms"], "speech", row["speech_adopted"], "narr", row["narration_adopted"])
        print(" ", row["player_facing_text"][:220])


if __name__ == "__main__":
    main()
