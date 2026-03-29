"""Smoke test for ``tests.helpers.transcript_runner``."""
from __future__ import annotations

import pytest

from game.gm import _is_placeholder_only_player_facing_text

from tests.helpers.transcript_runner import (
    compact_snapshot_summary,
    run_transcript,
)

pytestmark = [pytest.mark.transcript, pytest.mark.unit]


def _fake_gpt_response():
    return {
        "player_facing_text": "The frontier gate stands before you.",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }


def test_transcript_runner_smoke_single_begin_turn(tmp_path, monkeypatch):
    monkeypatch.setattr("game.api.call_gpt", lambda _messages: _fake_gpt_response())

    snaps = run_transcript(tmp_path, monkeypatch, ["Begin."])

    assert len(snaps) == 1
    assert snaps[0]["turn_index"] == 0
    assert snaps[0]["player_text"] == "Begin."
    gm_text = (snaps[0].get("gm_text") or "").strip()
    assert gm_text
    assert not _is_placeholder_only_player_facing_text(gm_text)
    low = gm_text.lower()
    assert "frontier" in low or "gate" in low
    assert snaps[0].get("scene_id") == "frontier_gate"

    summary = compact_snapshot_summary(snaps[0])
    assert "frontier_gate" in summary
    assert "Begin." in summary or "t0" in summary
