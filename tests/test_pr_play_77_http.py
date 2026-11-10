"""Two normal HTTP campaigns for bounded multi-step play. No developer seeding."""
import json
import os
import time
from pathlib import Path

from fastapi.testclient import TestClient

from game import api, storage
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
            })
    return {
        "scene": session.get("active_scene_id"),
        "turn": session.get("turn_counter"),
        "posture": ledger.get("posture"),
        "position": ledger.get("position"),
        "plans": [
            {"statuses": plan.get("statuses"), "automatic_resume": plan.get("automatic_resume")}
            for plan in (ledger.get("physical_plans") or [])
            if isinstance(plan, dict)
        ],
        "consequences": consequences,
        "flags": (storage.load_world().get("world_state") or {}).get("flags"),
    }


def _turn(client, text, rows):
    before = _slice()
    started = time.perf_counter()
    out = safe(client.post("/api/chat", json={"text": text}))
    facing = out["gm_output"]["player_facing_text"]
    resolution = out.get("resolution") if isinstance(out.get("resolution"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    rows.append({
        "input": text,
        "player_facing_text": facing,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "physical": meta.get("physical_adjudication"),
        "before": before,
        "after": _slice(),
        "sentinel": "SENTINEL" in json.dumps(out),
    })
    assert "SENTINEL" not in json.dumps(out)
    return facing


def test_http_multistep_campaigns(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch)
    enable(monkeypatch)
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_BRANCHING_SESSION", raising=False)
    campaigns = []
    with TestClient(api.app) as client:
        for name, branch, steps in (
            ("A", "survey", None),
            ("B", "report", None),
        ):
            create(client)
            start(client)
            reach(client)
            choose(client, branch)
            rows = []
            if branch == "survey":
                facing = _turn(client, "Is there a small loose stone I could shift aside?", rows)
                assert "has not been moved" in facing
                facing = _turn(client, "I push the loose stone aside and look where it was.", rows)
                assert "aside" in facing.casefold()
                assert _slice()["consequences"]
                facing = _turn(client, "I push the loose stone farther, climb the milestone, and look down the road.", rows)
                low = facing.casefold()
                assert "farther" in low and "no climbing check" in low and "not attempted" in low
                assert "hidden" not in low
                assert (_slice()["position"] or {}).get("kind") != "elevated"
                snap = safe(client.post("/api/snapshots", json={"label": "partial"}))["snapshot"]["id"]
                moved = [item for item in _slice()["consequences"] if item["action"] in {"push", "move"}]
                create(client)
                safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
                facing = _turn(client, "Where is the loose stone?", rows)
                assert "farther" in facing.casefold()
                facing = _turn(client, "continue", rows)
                assert "resumes" in facing.casefold()
                assert [item["id"] for item in _slice()["consequences"] if item["action"] in {"push", "move"}] == [item["id"] for item in moved]
            else:
                before_flags = _slice()["flags"]
                facing = _turn(client, "If I am beside the notice board, step back from it.", rows)
                assert "skipped" in facing.casefold() or "not met" in facing.casefold()
                assert _slice()["position"] in (None, {})
                facing = _turn(client, "I stand up and approach the notice board.", rows)
                assert "beside" in facing.casefold()
                clues_before = storage.load_session().get("discovered_clues")
                position_before = _slice()["position"]
                facing = _turn(client, "Is the notice board here, and what is on the hidden side?", rows)
                assert "you approach" not in facing.casefold()
                assert "hidden side" not in facing.casefold() or "nothing" in facing.casefold()
                assert storage.load_session().get("discovered_clues") == clues_before
                assert _slice()["position"] == position_before
                assert _slice()["flags"] == before_flags
                snap = safe(client.post("/api/snapshots", json={"label": "beside"}))["snapshot"]["id"]
                create(client)
                safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
                facing = _turn(client, "Am I beside the notice board?", rows)
                assert "beside" in facing.casefold()
                facing = _turn(client, "If I am beside the notice board, step back from it.", rows)
                assert "step back" in facing.casefold()
            campaigns.append({"name": name, "branch": branch, "turns": rows, "final": _slice()})
    evidence = os.environ.get("ASHEN_TEST_EVIDENCE_DIR")
    if evidence:
        Path(evidence, "http_campaigns.json").write_text(json.dumps(campaigns, indent=2), encoding="utf-8")
    latencies = [turn["elapsed_ms"] for campaign in campaigns for turn in campaign["turns"]]
    assert campaigns[0]["final"]["position"] is None or campaigns[0]["final"]["position"].get("kind") != "elevated"
    assert latencies and max(latencies) < 15000
