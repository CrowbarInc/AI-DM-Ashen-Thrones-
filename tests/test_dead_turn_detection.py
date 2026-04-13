"""Unit and light integration tests for deterministic dead-turn classification."""
from __future__ import annotations

import pytest

from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import classify_dead_turn, read_dead_turn_from_gm_output

pytestmark = pytest.mark.unit


def _dead(payload: dict) -> dict:
    return classify_dead_turn(payload)


def test_insufficient_quota_retry_exhausted_forced_fallback_is_dead() -> None:
    gm = {
        "player_facing_text": "The moment holds; choose your next step.",
        "metadata": {
            "upstream_api_error": {
                "failure_class": "insufficient_quota",
                "retryable": False,
                "error_code": "insufficient_quota",
            },
            "latency_mode": "fast_fallback",
        },
        "accepted_via": "forced_fallback",
        "final_route": "forced_retry_fallback",
        "retry_exhausted": True,
        "targeted_retry_terminal": True,
        "tags": ["forced_retry_fallback", "upstream_api_fast_fallback", "retry_escape_hatch", "retry_exhausted"],
    }
    d = _dead(gm)
    assert d["is_dead_turn"] is True
    assert d["validation_playable"] is False
    assert d["manual_test_valid"] is False
    assert d["dead_turn_class"] == "retry_terminal_fallback"
    assert "upstream_api_error" in d["dead_turn_reason_codes"]
    assert "fast_fallback_lane" in d["dead_turn_reason_codes"]


def test_nonretryable_upstream_forced_fallback_is_dead() -> None:
    gm = {
        "player_facing_text": "A neutral beat passes.",
        "metadata": {
            "upstream_api_error": {
                "failure_class": "invalid_api_key",
                "retryable": False,
            },
            "latency_mode": "fast_fallback",
        },
        "accepted_via": "forced_fallback",
        "final_route": "forced_retry_fallback",
        "retry_exhausted": True,
        "targeted_retry_terminal": True,
        "tags": ["upstream_api_fast_fallback", "forced_retry_fallback", "retry_escape_hatch"],
    }
    d = _dead(gm)
    assert d["is_dead_turn"] is True
    assert d["dead_turn_class"] == "retry_terminal_fallback"


def test_ordinary_candidate_through_gate_is_not_dead() -> None:
    out = apply_final_emission_gate(
        {"player_facing_text": "Rain drums on the slate roof.", "tags": []},
        resolution={"kind": "observe", "prompt": "I listen to the rain."},
        session={},
        scene_id="scene_investigate",
        world={},
    )
    dt = (out.get("_final_emission_meta") or {}).get("dead_turn") or {}
    assert dt.get("is_dead_turn") is False
    assert dt.get("dead_turn_class") == "none"
    assert dt.get("validation_playable") is True


def test_bounded_partial_meta_without_upstream_is_not_dead() -> None:
    gm = {
        "player_facing_text": "You get a partial read: the trail forks east and west.",
        "tags": [],
        "_final_emission_meta": {
            "answer_completeness_checked": True,
            "answer_completeness_passed": False,
            "answer_completeness_failure_reasons": ["bounded_partial_answer"],
        },
    }
    d = _dead(gm)
    assert d["is_dead_turn"] is False


def test_social_resolution_repair_terminal_without_infra_signals_not_dead() -> None:
    gm = {
        "player_facing_text": "They answer cautiously, eyes on the door.",
        "accepted_via": "social_resolution_repair",
        "retry_exhausted": True,
        "targeted_retry_terminal": True,
        "final_route": "social_fallback_minimal",
        "metadata": {
            "upstream_api_error": {
                "failure_class": "insufficient_quota",
                "retryable": False,
            },
        },
        "tags": ["social_empty_resolution_repair", "retry_exhausted"],
    }
    d = _dead(gm)
    assert d["is_dead_turn"] is False


def test_forced_retry_tags_alone_without_upstream_metadata_not_dead() -> None:
    gm = {
        "player_facing_text": "The gate sergeant waves you through with a tired nod.",
        "accepted_via": "forced_fallback",
        "final_route": "forced_retry_fallback",
        "retry_exhausted": True,
        "targeted_retry_terminal": True,
        "tags": ["forced_retry_fallback", "retry_escape_hatch", "retry_exhausted"],
    }
    d = _dead(gm)
    assert d["is_dead_turn"] is False


def test_synthetic_budget_upstream_error_tags_dead() -> None:
    gm = {
        "player_facing_text": "The game master is temporarily unavailable. Please try again.",
        "tags": ["error", "gpt_api_error:manual_play_gpt_budget_exceeded", "gpt_api_error_nonretryable"],
        "metadata": {
            "upstream_api_error": {
                "failure_class": "manual_play_gpt_budget_exceeded",
                "retryable": False,
                "error_code": "manual_play_gpt_budget_exceeded",
            },
        },
    }
    d = _dead(gm)
    assert d["is_dead_turn"] is True
    assert d["dead_turn_class"] == "upstream_api_failure"


def test_forced_fallback_with_upstream_but_without_retry_terminal_class_forced_nonplayable() -> None:
    gm = {
        "player_facing_text": "A procedural stand-in line.",
        "metadata": {
            "upstream_api_error": {"failure_class": "insufficient_quota", "retryable": False},
            "latency_mode": "fast_fallback",
        },
        "accepted_via": "forced_fallback",
        "final_route": "forced_retry_fallback",
        "retry_exhausted": False,
        "targeted_retry_terminal": False,
        "tags": ["upstream_api_fast_fallback"],
    }
    d = _dead(gm)
    assert d["is_dead_turn"] is True
    assert d["dead_turn_class"] == "forced_fallback_nonplayable"


def test_opening_style_fast_fallback_tags_without_upstream_not_dead() -> None:
    gm = {
        "player_facing_text": "At Frontier Gate, rain darkens the flagstones.",
        "tags": ["forced_retry_fallback", "upstream_api_fast_fallback"],
    }
    assert _dead(gm)["is_dead_turn"] is False


def test_malformed_emergency_output_flag_is_dead() -> None:
    gm = {
        "player_facing_text": "x",
        "metadata": {"malformed_emergency_output": True},
    }
    d = _dead(gm)
    assert d["is_dead_turn"] is True
    assert d["dead_turn_class"] == "malformed_emergency_output"


def test_read_dead_turn_from_gm_output_is_read_only_from_fem() -> None:
    gm = {
        "metadata": {"upstream_api_error": {"failure_class": "timeout"}},
        "tags": ["upstream_api_fast_fallback"],
        "player_facing_text": "Would be dead if classified, but FEM snapshot wins.",
        "_final_emission_meta": {
            "dead_turn": {
                "is_dead_turn": False,
                "dead_turn_class": "none",
                "dead_turn_reason_codes": [],
                "validation_playable": True,
                "manual_test_valid": True,
            }
        },
    }
    snap = read_dead_turn_from_gm_output(gm)
    assert snap["is_dead_turn"] is False
    assert snap["validation_playable"] is True
