"""Two normal HTTP campaigns for integrated play. Deterministic host wording."""
import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

from game import storage
from game.bounded_improvisation import LEDGER_KEY
from tests.test_pr_play_71_lifecycle import choose, configure, create, reach, safe, start
from tests.test_pr_play_76_physical import enable


def _facing(payload):
    return payload["gm_output"]["player_facing_text"]


def _turn(client, text, rows, allow_discovery=False):
    started = time.perf_counter()
    out = safe(client.post("/api/chat", json={"text": text, "client_request_id": f"http-{len(rows)}-{text[:12]}"}))
    facing = _facing(out)
    rows.append({
        "input": text,
        "player_facing_text": facing,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "sentinel": "SENTINEL" in json.dumps(out),
    })
    assert "SENTINEL" not in json.dumps(out)
    if not allow_discovery:
        assert "northwest mud" not in facing.casefold()
    return facing


def test_http_integrated_campaigns(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch)
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_BRANCHING_SESSION", raising=False)
    campaigns = []
    with TestClient(api_client_app()) as client:
        create(client)
        start(client)
        rows = []
        opening = _turn(client, "I look around.", rows)
        assert opening
        notice = _turn(client, "I examine the notice board and ask the guard about the warning.", rows, allow_discovery=True)
        assert "northwest mud" in notice.casefold()
        assert "patrol" in notice.casefold() or "guard" in notice.casefold()
        greet = _turn(client, "Approach the guard and greet him.", rows)
        assert "guard" in greet.casefold()
        follow = _turn(client, "Ask the guard whether anyone has passed through recently.", rows)
        assert "northwest" not in follow.casefold()
        unexpected = _turn(client, "I wait and watch the road.", rows)
        assert "nothing new" in unexpected.casefold() or "watch" in unexpected.casefold()
        unsupported = _turn(client, "I climb the gate wall.", rows)
        assert "not" in unsupported.casefold()
        snap = safe(client.post("/api/snapshots", json={"label": "integrated-a"}))["snapshot"]["id"]
        create(client)
        safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
        resumed = _turn(client, "Ask the guard what concerns him.", rows)
        assert "guard" in resumed.casefold() or "do not know" in resumed.casefold() or "concern" in resumed.casefold()
        campaigns.append({"name": "A", "turns": rows, "snapshot": snap})

        create(client)
        start(client)
        reach(client)
        choose(client, "report")
        rows = []
        branch = _turn(client, "I look around the milestone.", rows)
        assert branch
        mixed = _turn(client, "I look for signs of a struggle.", rows)
        assert "no signs" in mixed.casefold() or "not established" in mixed.casefold() or "nothing" in mixed.casefold()
        watch = _turn(client, "I offer to help search.", rows)
        assert "no search party" in watch.casefold() or "help" in watch.casefold()
        question = _turn(client, "Am I standing?", rows)
        assert "standing" in question.casefold() or "seated" in question.casefold()
        snap = safe(client.post("/api/snapshots", json={"label": "integrated-b"}))["snapshot"]["id"]
        before = storage.load_session().get("active_scene_id")
        create(client)
        safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
        assert storage.load_session().get("active_scene_id") == before
        continued = _turn(client, "I wait and watch the road.", rows)
        assert "nothing new" in continued.casefold() or "watch" in continued.casefold()
        campaigns.append({"name": "B", "turns": rows, "snapshot": snap, "scene": before})
    out = Path("artifacts/pr_play_78")
    # Evidence is written by the caller. Keep the assertion local.
    assert all(item["turns"] for item in campaigns)
    assert "SENTINEL" not in json.dumps(campaigns)


def api_client_app():
    from game import api
    return api.app
