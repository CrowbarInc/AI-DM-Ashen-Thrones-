"""Direct-owner tests for :mod:`game.upstream_response_repairs` (C2 Block B)."""

from __future__ import annotations

import pytest

from game.upstream_response_repairs import (
    UPSTREAM_PREPARED_EMISSION_KEY,
    build_minimal_action_outcome_contract_repair_text,
    build_upstream_prepared_emission_payload,
    merge_upstream_prepared_emission_into_gm_output,
)

pytestmark = pytest.mark.unit


def test_build_upstream_payload_includes_answer_action_and_sanitizer_stock() -> None:
    resolution = {
        "kind": "observe",
        "prompt": "I look around.",
        "adjudication": {"answer_type": "needs_concrete_action"},
    }
    session = {"active_scene_id": "tavern"}
    world: dict = {}
    p = build_upstream_prepared_emission_payload(resolution=resolution, session=session, world=world, scene_id="tavern")
    assert "prepared_answer_fallback_text" in p
    assert "prepared_action_fallback_text" in p
    assert p["prepared_sanitizer_empty_fallback_text"]
    assert p.get("upstream_prepared_bundle_origin") == "upstream_response_repairs.build_upstream_prepared_emission_payload"
    assert "concrete" in (p["prepared_answer_fallback_text"] or "").lower()
    line = build_minimal_action_outcome_contract_repair_text(player_input="I open the door", resolution=resolution)
    assert line.lower().startswith("you")


def test_merge_respects_nonempty_caller_override() -> None:
    gm: dict = {
        UPSTREAM_PREPARED_EMISSION_KEY: {"prepared_answer_fallback_text": "OVERRIDE_ANSWER."},
    }
    merge_upstream_prepared_emission_into_gm_output(
        gm,
        resolution={"kind": "observe", "prompt": "x"},
        session={},
        world=None,
        scene_id="s",
    )
    assert gm[UPSTREAM_PREPARED_EMISSION_KEY]["prepared_answer_fallback_text"] == "OVERRIDE_ANSWER."
    assert gm[UPSTREAM_PREPARED_EMISSION_KEY]["prepared_action_fallback_text"]


def test_merge_fills_missing_key_from_fresh() -> None:
    gm = {UPSTREAM_PREPARED_EMISSION_KEY: {}}
    merge_upstream_prepared_emission_into_gm_output(
        gm,
        resolution={"kind": "travel", "prompt": "I go north", "resolved_transition": True},
        session={},
        world=None,
        scene_id="road",
    )
    assert isinstance(gm[UPSTREAM_PREPARED_EMISSION_KEY].get("prepared_action_fallback_text"), str)
