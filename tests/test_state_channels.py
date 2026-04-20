"""Tests for ``game.state_channels`` — channel projection and assertion helpers."""

from __future__ import annotations

import pytest

from game.state_channels import (
    ChannelSeparationError,
    assert_no_author_keys_in_player_output,
    assert_no_debug_keys_in_prompt_payload,
    project_author_payload,
    project_debug_payload,
    project_public_payload,
    strip_non_public_payload,
)


def test_project_mixed_payloads_per_channel() -> None:
    payload = {
        "player_facing_text": "Hello",
        "scene_id": "gate",
        "lint_trace": {"x": 1},
        "internal_plan": {"steps": []},
        "author_notes": "do not show",
        "narrative_authenticity_eval": {"verdict": "ok"},
    }
    pub = project_public_payload(payload)
    dbg = project_debug_payload(payload)
    auth = project_author_payload(payload)

    assert pub == {"player_facing_text": "Hello", "scene_id": "gate"}
    assert dbg == {"lint_trace": {"x": 1}, "narrative_authenticity_eval": {"verdict": "ok"}}
    assert auth == {"internal_plan": {"steps": []}, "author_notes": "do not show"}


def test_final_emission_meta_is_debug() -> None:
    p = {"_final_emission_meta": {"dead_turn": {}}, "ok": True}
    assert project_debug_payload(p) == {"_final_emission_meta": {"dead_turn": {}}}
    assert project_public_payload(p) == {"ok": True}


def test_debug_trace_telemetry_suffixes_stripped_from_public() -> None:
    payload = {
        "visible": 1,
        "stage_diff_telemetry": {},
        "gm_debug": {},
        "tail_trace": [],
        "pack_telemetry": {},
    }
    pub = project_public_payload(payload)
    assert pub == {"visible": 1}
    assert strip_non_public_payload(payload) == pub


def test_author_internal_keys_stripped_from_public() -> None:
    payload = {
        "published": "yes",
        "planner_graph": {},
        "draft_author": "secret",
        "internal_state": {},
    }
    pub = project_public_payload(payload)
    assert pub == {"published": "yes"}


def test_assert_no_debug_keys_in_prompt_payload_raises() -> None:
    with pytest.raises(ChannelSeparationError) as ei:
        assert_no_debug_keys_in_prompt_payload({"narration": "x", "foo_debug": {}})
    assert "foo_debug" in str(ei.value)


def test_assert_no_author_keys_in_player_output_raises() -> None:
    with pytest.raises(ChannelSeparationError) as ei:
        assert_no_author_keys_in_player_output({"text": "x", "internal_foo": 1})
    assert "internal_foo" in str(ei.value)


def test_assert_helpers_pass_on_clean_or_empty_payload() -> None:
    assert_no_debug_keys_in_prompt_payload(None)
    assert_no_debug_keys_in_prompt_payload({})
    assert_no_author_keys_in_player_output(None)
    assert_no_author_keys_in_player_output({"player_facing_text": "ok"})
