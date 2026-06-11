"""Transcript-style regressions for anti-railroading + final gate (quoted dialogue, hard constraints)."""
from __future__ import annotations

import pytest

import game.final_emission_gate as feg

from tests.helpers.emission_smoke_assertions import apply_final_emission_gate_consumer
pytestmark = pytest.mark.unit


def test_quoted_npc_line_does_not_trigger_forced_direction_on_outer_narration(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = (
        "Ash dusts the sill. A dockhand says, \"You head straight to the customs house.\" "
        "You still choose how you answer."
    )
    out, meta = apply_final_emission_gate_consumer(
        {"player_facing_text": raw, "tags": []},
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="dock",
        world={},
    )
    assert meta.get("anti_railroading_repaired") is False
    assert '"' in (out.get("player_facing_text") or "")


def test_hard_constraint_bridge_line_passes_without_repair(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = "The bridge is out. The alley and the roofline are still open."
    out, _ = apply_final_emission_gate_consumer(
        {"player_facing_text": raw, "tags": []},
        resolution={"kind": "observe", "prompt": "I look for routes."},
        session={},
        scene_id="bridge",
        world={},
    )
    assert out.get("player_facing_text") == raw
