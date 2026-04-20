"""Top-level prompt-lane separation via ``game.state_channels`` at ``build_narration_context`` return."""

from __future__ import annotations

import pytest

from game.prompt_context import build_narration_context
from game.state_channels import (
    ChannelSeparationError,
    assert_no_debug_keys_in_prompt_payload,
    is_author_key,
    is_debug_key,
    project_public_payload,
)
from tests.test_prompt_context import _narration_minimal_kwargs

pytestmark = pytest.mark.unit


def test_shipped_narration_context_has_no_top_level_debug_or_prompt_debug() -> None:
    ctx = build_narration_context(**_narration_minimal_kwargs())
    assert "prompt_debug" not in ctx
    assert_no_debug_keys_in_prompt_payload(ctx)
    for k in ctx:
        assert not is_debug_key(k), k
        assert not is_author_key(k), k


def test_shipped_narration_context_retains_core_public_contract_keys() -> None:
    ctx = build_narration_context(**_narration_minimal_kwargs())
    for key in (
        "instructions",
        "response_policy",
        "narration_visibility",
        "player_input",
        "scene",
        "turn_summary",
    ):
        assert key in ctx


def test_include_non_public_prompt_keys_restores_prompt_debug_top_level() -> None:
    ctx = build_narration_context(**_narration_minimal_kwargs(include_non_public_prompt_keys=True))
    pd = ctx.get("prompt_debug")
    assert isinstance(pd, dict) and pd


def test_player_facing_narration_purity_contract_in_shipped_payload_has_no_debug_fields() -> None:
    ctx = build_narration_context(**_narration_minimal_kwargs())
    c = ctx.get("player_facing_narration_purity_contract")
    assert isinstance(c, dict)
    for forbidden in ("debug_inputs", "debug_reason"):
        assert forbidden not in c


def test_projection_strips_classified_top_level_keys() -> None:
    raw = {
        "instructions": [],
        "response_policy": {"x": 1},
        "_final_emission_meta": {},
        "stage_diff_telemetry": {},
        "dead_turn": False,
        "reason_codes": [],
        "debug_x": 1,
        "foo_trace": [],
        "telemetry_bar": {},
        "author_notes": {},
        "planner_graph": {},
        "scene_internal": 1,
        "role_planner": 2,
        "public_stays": True,
    }
    with pytest.raises(ChannelSeparationError):
        assert_no_debug_keys_in_prompt_payload(raw)
    out = project_public_payload(raw)
    assert set(out.keys()) == {"instructions", "response_policy", "public_stays"}
    assert_no_debug_keys_in_prompt_payload(out)
    for k in out:
        assert not is_debug_key(k), k
        assert not is_author_key(k), k
