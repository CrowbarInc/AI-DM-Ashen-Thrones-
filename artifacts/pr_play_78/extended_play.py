"""Extended integrated session. The chooser sees only player-facing text and affordance labels."""
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
DATA = OUT / "extended_data"
if DATA.exists():
    shutil.rmtree(DATA)
DATA.mkdir(parents=True)
os.environ["ASHEN_DATA_DIR"] = str(DATA)
os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(DATA / "provider_usage.jsonl")
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "0"
os.environ["ASHEN_EXPERIMENTAL_BRANCHING"] = "1"
os.environ["ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS"] = "1"
os.environ["ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE"] = "1"
os.environ["ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION"] = "1"
os.environ["ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION"] = "1"
os.environ["ASHEN_EXPERIMENTAL_DYNAMIC_NPCS"] = "1"
os.environ["ASHEN_BOUNDED_SPEECH"] = "1"
os.environ["ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION"] = "0"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"

from fastapi.testclient import TestClient

from game import api, storage

for name in ("campaign.json", "character.json", "world.json", "conditions.json"):
    shutil.copy2(ROOT / "data" / name, storage.DATA_DIR / name)
(storage.DATA_DIR / "scenes").mkdir(parents=True, exist_ok=True)
for path in (ROOT / "data" / "scenes").glob("*.json"):
    shutil.copy2(path, storage.SCENES_DIR / path.name)
from tests.test_start_campaign_api import RICH_OPENING_GPT_RESPONSE
import copy

api.call_gpt = lambda *a, **k: copy.deepcopy(RICH_OPENING_GPT_RESPONSE)
api.log_upstream_api_preflight_at_startup = lambda: None

LIVE_CAP = 8
live_used = 0


SEEN = set()


def choose(visible, labels, turn):
    """Pick the next unused action from words the player has actually been shown."""
    text = " ".join(visible).casefold()
    joined = " ".join(labels).casefold()
    ideas = ["I look around."]
    if "notice" in text:
        ideas.append("I examine the notice board.")
    if "mud track" in text or "rumor" in joined or "patrol" in text:
        ideas.append("I follow the missing patrol rumor.")
    if "milestone" in joined or "milestone" in text:
        ideas.append("I examine the weathered milestone.")
    if "survey" in joined:
        ideas.append("I record the survey at the milestone.")
    if "guard" in text or "serjeant" in text:
        ideas += [
            "Approach the guard and greet him.",
            "Ask the guard about the warning.",
            "Does he seem nervous?",
            "Who are you?",
            "Thank the guard and look around.",
        ]
    ideas += [
        "I look for signs of a struggle.",
        "I wait and watch the road.",
        "I offer to help search.",
        "I inspect the tracks more closely.",
        "I climb the nearest wall.",
        "Examine the notice board and ask the guard what concerns him.",
        "Am I standing?",
        "I look around again.",
        "Ask the guard whether anyone passed recently.",
        "I look around the road and ask the guard what he sees.",
    ]
    for idea in ideas:
        if idea not in SEEN:
            SEEN.add(idea)
            return idea, "adaptive"
    return f"I look around the gate again, turn {turn}.", "adaptive"


def labels_from(payload):
    state = payload.get("public_state") or payload.get("session") or {}
    ui = payload.get("ui") or state.get("ui") or {}
    affordances = ui.get("affordances") or []
    names = []
    for item in affordances:
        if isinstance(item, dict):
            names.append(str(item.get("label") or item.get("id") or ""))
    return names


def main():
    global live_used
    rows = []
    visible = []
    latencies = []
    with TestClient(api.app) as client:
        created = client.post("/api/new_campaign")
        assert created.status_code == 200, created.text
        started = client.post("/api/start_campaign")
        assert started.status_code == 200, started.text
        opening = started.json()
        visible.append(opening["gm_output"]["player_facing_text"])
        labels = labels_from(opening)
        for turn in range(34):
            text, provenance = choose(visible, labels, turn)
            dialogue = any(word in text.casefold() for word in ("ask", "greet", "thank", "approach the guard"))
            use_live = dialogue and live_used < LIVE_CAP
            os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "0" if use_live else "1"
            if use_live:
                live_used += 1
            clock = time.perf_counter()
            response = client.post("/api/chat", json={"text": text, "client_request_id": f"ext-{turn}"})
            elapsed = round((time.perf_counter() - clock) * 1000, 1)
            latencies.append(elapsed)
            assert response.status_code == 200, response.text
            payload = response.json()
            facing = payload["gm_output"]["player_facing_text"]
            visible.append(facing)
            labels = labels_from(payload) or labels
            audit = storage.load_session().get("last_background_expression") if use_live else None
            rows.append({
                "turn": turn + 1,
                "input": text,
                "provenance": provenance,
                "live_requested": use_live,
                "player_facing_text": facing,
                "elapsed_ms": elapsed,
                "adopted": bool((audit or {}).get("adopted")) if isinstance(audit, dict) else False,
                "sentinel": "SENTINEL" in json.dumps(payload) or "northwest mud track" in facing.casefold(),
            })
            if turn == 16:
                snap = client.post("/api/snapshots", json={"label": "extended"})
                assert snap.status_code == 200, snap.text
                rows.append({"turn": "save", "input": "save", "provenance": "system", "snapshot": snap.json()["snapshot"]["id"]})
            if turn == 17:
                snap_id = next(item["snapshot"] for item in rows if item.get("snapshot"))
                client.post("/api/new_campaign")
                loaded = client.post("/api/snapshots/load", json={"snapshot_id": snap_id})
                assert loaded.status_code == 200, loaded.text
                rows.append({"turn": "resume", "input": "load", "provenance": "system", "scene": storage.load_session().get("active_scene_id")})
    summary = {
        "turns": [row for row in rows if isinstance(row.get("turn"), int)],
        "meaningful_turns": sum(1 for row in rows if isinstance(row.get("turn"), int)),
        "live_requested": live_used,
        "adopted": sum(1 for row in rows if row.get("adopted")),
        "sentinels": sum(1 for row in rows if row.get("sentinel")),
        "latencies_ms": latencies,
        "mean_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
        "max_ms": max(latencies) if latencies else 0,
        "transcript": rows,
    }
    (OUT / "extended_play.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("meaningful_turns", "live_requested", "adopted", "sentinels", "mean_ms", "max_ms")}))


if __name__ == "__main__":
    main()
