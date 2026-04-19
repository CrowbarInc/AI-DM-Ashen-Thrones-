"""Regression: turn_packet stays separate from CTIR (no embedded meaning tree)."""

from __future__ import annotations

import json

import pytest

from game import ctir
from game.prompt_context import build_response_policy
from game.turn_packet import TURN_PACKET_METADATA_KEY, build_turn_packet

pytestmark = pytest.mark.unit

# CTIR root sections — must not appear as turn_packet top-level contract mirrors.
_CTIR_ROOT_KEYS = frozenset(
    {
        "intent",
        "state_mutations",
        "interaction",
        "world",
        "narrative_anchors",
        "provenance",
        "player_input",
    }
)


def test_turn_packet_is_not_ctir_shape() -> None:
    rp = build_response_policy()
    packet = build_turn_packet(
        response_policy=rp,
        scene_id="s1",
        player_text="Hello",
        resolution={"kind": "question"},
        interaction_continuity={"interaction_mode": "social", "active_interaction_target_id": "npc_a"},
        narration_obligations={"suppress_non_social_emitters": False},
        turn_id=9,
    )
    assert not ctir.looks_like_ctir(packet)
    top = frozenset(packet.keys())
    assert not (_CTIR_ROOT_KEYS <= top)
    dumped = json.dumps(packet, sort_keys=True)
    assert "state_mutations" not in dumped
    assert TURN_PACKET_METADATA_KEY not in packet  # attachment key lives on gm metadata, not inside packet


def test_turn_packet_versioned_contracts_not_ctir_provenance() -> None:
    packet = build_turn_packet(
        response_policy={},
        scene_id=None,
        player_text="x",
        resolution=None,
    )
    assert packet.get("version") == 1
    prov = packet.get("contracts")
    assert isinstance(prov, dict)
    assert "builder_source" not in packet
