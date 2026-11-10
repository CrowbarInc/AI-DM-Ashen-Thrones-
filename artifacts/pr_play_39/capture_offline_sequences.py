"""Offline PR-PLAY-39 sequence capture. No provider calls."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ.setdefault("ASHEN_DISABLE_PROVIDER_CALLS", "1")

import pytest

from tests.test_pr_play_39_action_admission import (
    FOOTPRINTS,
    PATROL,
    RUMOR,
    _ask,
    _install_frontier,
    _post,
    _quiet_models,
    _record,
    _turn,
)
from game import storage
from game.api import app
from fastapi.testclient import TestClient

OUT = Path(__file__).resolve().parent / "offline_sequences.json"


def _snap(session):
    return {
        "active_scene_id": session.get("active_scene_id"),
        "visited_scene_ids": list(session.get("visited_scene_ids") or []),
        "turn_counter": session.get("turn_counter"),
        "time_pressure": (session.get("clocks") or {}).get("time_pressure"),
    }


def _run(interpretations, texts):
    monkeypatch = pytest.MonkeyPatch()
    tmp = Path(tempfile.mkdtemp(prefix="play39-"))
    _install_frontier(tmp, monkeypatch)
    calls = _quiet_models(monkeypatch, interpretations)
    before = _snap(storage.load_session())
    rows = []
    with TestClient(app) as client:
        for text in texts:
            body = _post(client, text)
            rows.append({
                "player_text": text,
                "player_facing_text": body["gm_output"]["player_facing_text"],
                "resolution_kind": (body.get("resolution") or {}).get("kind"),
                "resolved_transition": (body.get("resolution") or {}).get("resolved_transition"),
                "target_scene_id": (body.get("resolution") or {}).get("target_scene_id"),
            })
    after = _snap(storage.load_session())
    monkeypatch.undo()
    return {"before": before, "after": after, "calls": calls, "turns": rows}


def main():
    unknown = "I ask Captain Voss what he knows about the gate."
    observatory = "I want to follow the trail to the glass observatory."
    payload = {
        "rumor": _run(
            {RUMOR: {"status": "accepted", "reason": "captured_record", "record": _record("T2"), "provider_requests": []}},
            [RUMOR],
        ),
        "patrol": _run(
            {PATROL: {"status": "blocked", "reason": "clarification_required", "record": _record("T4"),
                      "player_facing_text": _turn("T4")["player_facing_text"], "provider_requests": []}},
            [PATROL],
        ),
        "unsupported": _run(
            {
                unknown: {"status": "accepted", "reason": "captured_style", "record": _ask("captain_voss", unknown), "provider_requests": []},
                FOOTPRINTS: {"status": "blocked", "reason": "clarification_required", "record": _record("T3"),
                             "player_facing_text": _turn("T3")["player_facing_text"], "provider_requests": []},
            },
            [unknown, observatory, FOOTPRINTS],
        ),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
