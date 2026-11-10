"""Record the two normal HTTP campaigns with timings and authoritative slices."""
import json
import os
import time
from pathlib import Path

from fastapi.testclient import TestClient

from game import storage
from game.bounded_improvisation import LEDGER_KEY
from tests.test_pr_play_71_lifecycle import choose, configure, create, reach, safe, start
from tests.test_pr_play_76_physical import enable


def _slice():
    session = storage.load_session()
    ledger = session.get(LEDGER_KEY) if isinstance(session.get(LEDGER_KEY), dict) else {}
    consequences = []
    for item in ledger.get("physical_consequences") or []:
        if isinstance(item, dict):
            consequences.append({
                "id": item.get("id"), "target_id": item.get("target_id"), "action": item.get("action"),
                "prior": item.get("prior"), "result": item.get("result"), "scene_id": item.get("scene_id"),
                "turn": item.get("turn"), "provenance": item.get("provenance"),
            })
    return {
        "scene": session.get("active_scene_id"),
        "turn": session.get("turn_counter"),
        "posture": ledger.get("posture"),
        "position": ledger.get("position"),
        "physical_state": ledger.get("physical_state"),
        "consequences": consequences,
        "flags": (storage.load_world().get("world_state") or {}).get("flags"),
    }


def _turn(client, text, rows):
    before = _slice()
    started = time.perf_counter()
    out = safe(client.post("/api/chat", json={"text": text}))
    elapsed = round((time.perf_counter() - started) * 1000, 1)
    facing = out["gm_output"]["player_facing_text"]
    resolution = out.get("resolution") if isinstance(out.get("resolution"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    rows.append({
        "input": text,
        "player_facing_text": facing,
        "elapsed_ms": elapsed,
        "physical": meta.get("physical_adjudication"),
        "before": before,
        "after": _slice(),
        "sentinel": "SENTINEL" in json.dumps(out),
    })
    return facing


def test_http_campaign_traces(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch)
    enable(monkeypatch)
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_BRANCHING_SESSION", raising=False)
    campaigns = []
    with TestClient(api_app()) as client:
        for branch, steps in (
            ("survey", [
                "Is there a small loose stone I could shift aside?",
                "I push the loose stone aside.",
                "Is the loose stone still beside the stonework?",
                "I push it farther.",
                "Where is the loose stone?",
                "Is there anything nearby I could sit on?",
                "I sit on the stone seat.",
            ]),
            ("report", [
                "I approach the notice board.",
                "I climb onto the broken stonework to get a better view of the road.",
                "Am I beside the notice board?",
                "I step back from the notice board.",
            ]),
        ):
            create(client)
            start(client)
            reach(client)
            choose(client, branch)
            rows = []
            texts = [_turn(client, text, rows) for text in steps[:4 if branch == "survey" else 3]]
            if branch == "survey":
                assert "has not been moved" in texts[0]
                assert "aside from the stonework" in texts[1]
                assert "aside from the stonework" in texts[2]
                assert "farther" in texts[3]
            else:
                assert "beside the Notice board" in texts[0]
                assert "not established" in texts[1] or "no climbing check" in texts[1]
                assert "beside the Notice board" in texts[2]
            snap = safe(client.post("/api/snapshots", json={"label": branch}))["snapshot"]["id"]
            create(client)
            safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
            resumed = _turn(client, steps[4] if branch == "survey" else steps[2], rows)
            if branch == "survey":
                assert "farther" in resumed
                _turn(client, steps[5], rows)
                seated = _turn(client, steps[6], rows)
                assert "You sit" in seated
                assert storage.load_session()[LEDGER_KEY]["posture"]["kind"] == "sitting"
            else:
                assert "beside the Notice board" in resumed
                backed = _turn(client, steps[3], rows)
                assert "step back" in backed.casefold() or storage.load_session()[LEDGER_KEY]["position"]["kind"] == "back"
            assert all(row["sentinel"] is False for row in rows)
            campaigns.append({"branch": branch, "snapshot_id": snap, "turns": rows, "result": "PASS"})
    latencies = [row["elapsed_ms"] for campaign in campaigns for row in campaign["turns"]]
    ordered = sorted(latencies)
    mid = ordered[len(ordered) // 2]
    summary = {
        "campaigns": 2,
        "turns": len(latencies),
        "mean_ms": round(sum(latencies) / len(latencies), 1),
        "median_ms": mid,
        "max_ms": max(latencies),
        "provider_requests": 0,
        "results": [item["result"] for item in campaigns],
    }
    payload = {"summary": summary, "campaigns": campaigns}
    evidence = os.environ.get("ASHEN_TEST_EVIDENCE_DIR")
    if evidence:
        destination = Path(evidence)
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "http_campaigns.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    assert summary["results"] == ["PASS", "PASS"]


def api_app():
    from game import api
    return api.app
