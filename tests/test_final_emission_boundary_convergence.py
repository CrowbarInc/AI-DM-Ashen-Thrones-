"""Objective C2 — final emission boundary convergence + ownership lock-in (Block D2).

Invariant tests prefer **behavior and metadata** (repair kinds, FEM flags, stable markers)
over brittle snapshots of private helper names. See ``docs/final_emission_ownership_convergence.md``.
"""
from __future__ import annotations

import json

import pytest

import game.final_emission_gate as feg
from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import read_final_emission_meta_dict
from game.final_emission_repairs import (
    _apply_answer_completeness_layer,
    _apply_response_delta_layer,
    repair_fallback_behavior,
)
from game.final_emission_text import _normalize_text
from game.output_sanitizer import (
    SANITIZER_BOUNDARY_LEGACY_SENTENCE_REWRITE,
    sanitize_player_facing_output,
)
from game.social_exchange_emission import strict_social_ownership_terminal_fallback
from game.upstream_response_repairs import UPSTREAM_PREPARED_EMISSION_KEY
from tests.test_final_emission_gate import _runner_strict_bundle

pytestmark = pytest.mark.unit


@pytest.fixture
def _noop_visibility(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)


def _rtc(required: str) -> dict:
    return {"required_response_type": required, "action_must_preserve_agency": required == "action_outcome"}


def test_answer_completeness_layer_does_not_reorder_on_failure():
    gm = {
        "response_policy": {
            "answer_completeness": {
                "enabled": True,
                "answer_required": True,
                "expected_answer_shape": "direct",
                "expected_voice": "npc",
                "concrete_payload_any_of": ["name"],
                "allowed_partial_reasons": ["uncertainty"],
            }
        }
    }
    text = "I cannot say for certain. The captain is Jonas Hale."
    out, meta, extra = _apply_answer_completeness_layer(
        text,
        gm_output=gm,
        resolution={"social": {"npc_name": "Guard"}},
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        strict_social_path=False,
    )
    assert out == text
    assert meta.get("answer_completeness_boundary_semantic_repair_disabled") is True
    assert meta.get("answer_completeness_repaired") is False
    if meta.get("answer_completeness_failed"):
        assert "answer_completeness_unsatisfied_at_boundary_no_reorder" in extra


def test_response_delta_layer_does_not_reorder_on_failure():
    gm = {
        "response_policy": {
            "response_delta": {
                "enabled": True,
                "delta_required": True,
                "allowed_delta_kinds": ["new_fact"],
                "previous_answer_snippet": "We spoke of the east gate and the watch roster.",
            }
        }
    }
    text = "We spoke of the east gate and the watch roster. Nothing new on the harbor clerk."
    ac_meta = {"answer_completeness_failed": False}
    out, meta, extra = _apply_response_delta_layer(
        text,
        gm_output=gm,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        answer_completeness_meta=ac_meta,
        strict_social_path=False,
    )
    assert out == text
    assert meta.get("response_delta_boundary_semantic_repair_disabled") is True
    assert meta.get("response_delta_repaired") is False
    if meta.get("response_delta_failed"):
        assert "response_delta_unsatisfied_at_boundary_no_reorder" in extra


def test_repair_fallback_behavior_strip_only_no_template_synthesis():
    ctr = {
        "enabled": True,
        "uncertainty_active": True,
        "uncertainty_mode": "npc_ignorance",
        "uncertainty_sources": ["unknown_identity"],
        "allowed_behaviors": {"provide_partial_information": True, "ask_clarifying_question": True},
        "prefer_partial_over_question": True,
        "require_partial_to_state_known_edge": True,
        "require_partial_to_state_unknown_edge": True,
        "max_clarifying_questions": 1,
        "disallowed_behaviors": {},
    }
    validation = {
        "checked": True,
        "passed": False,
        "uncertainty_active": True,
        "failure_reasons": ["missing_allowed_fallback_shape"],
        "meta_fallback_voice_detected": False,
        "fabricated_authority_detected": False,
        "invented_certainty_detected": False,
    }
    repaired, meta, _ = repair_fallback_behavior("", ctr, validation, resolution=None)
    assert meta.get("fallback_behavior_boundary_semantic_synthesis_skipped") is True
    assert repaired == ""


def test_sanitizer_defaults_to_strip_only_drops_scaffold():
    text = "I need a more concrete action or target to resolve that procedurally."
    ctx: dict = {}
    out = sanitize_player_facing_output(text, ctx)
    assert out == ""
    events = [e.get("event") for e in (ctx.get("sanitizer_debug") or []) if isinstance(e, dict)]
    assert "strip_only_dropped_rewrite_candidate" in events


def test_legacy_rewrite_opt_in_still_rewrites_procedural():
    text = "I need a more concrete action or target to resolve that procedurally."
    out = sanitize_player_facing_output(
        text, {"sanitizer_boundary_mode": SANITIZER_BOUNDARY_LEGACY_SENTENCE_REWRITE}
    )
    low = out.lower()
    assert "resolve that procedurally" not in low


# --- Block D2: scenario-shaped ownership locks (gate + strip-only sanitizer) --------------------


def test_gate_thin_answer_uses_upstream_prepared_marker_not_boundary_synthesis(_noop_visibility):
    """Answer contract repair consumes ``prepared_answer_fallback_text``; gate does not mint a new line."""
    marker = "ZETA none east pier yet."
    gm = {
        "player_facing_text": "Fog.",
        "tags": [],
        "response_policy": {"response_type_contract": _rtc("answer")},
        UPSTREAM_PREPARED_EMISSION_KEY: {
            "prepared_answer_fallback_text": marker,
            "prepared_action_fallback_text": "You act, and the scene shifts.",
        },
    }
    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "observe", "prompt": "What do I see?"},
        session={},
        scene_id="yard",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert _normalize_text(out.get("player_facing_text") or "") == _normalize_text(marker)
    assert meta.get("response_type_repair_kind") == "answer_upstream_prepared_repair"
    assert meta.get("response_type_upstream_prepared_absent") is not True


def test_gate_thin_action_outcome_uses_upstream_prepared_marker_not_boundary_synthesis(_noop_visibility):
    marker = "You pry the chest lid, and the attempt produces an immediate result."
    gm = {
        "player_facing_text": "The room is quiet.",
        "tags": [],
        "response_policy": {"response_type_contract": _rtc("action_outcome")},
        UPSTREAM_PREPARED_EMISSION_KEY: {
            "prepared_answer_fallback_text": "none east.",
            "prepared_action_fallback_text": marker,
        },
    }
    session = {"last_player_action_text": "Pry the chest lid"}
    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "investigate", "prompt": "Pry the chest lid"},
        session=session,
        scene_id="cellar",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert _normalize_text(out.get("player_facing_text") or "") == _normalize_text(marker)
    assert meta.get("response_type_repair_kind") == "action_outcome_upstream_prepared_repair"


def test_enforce_response_type_marks_upstream_absent_without_inventing_answer_line():
    """When prepared answer text is missing, debug records absence; candidate text is not silently 'completed'."""
    text, dbg = feg._enforce_response_type_contract(
        "Only mist between the torches.",
        gm_output={
            "response_policy": {"response_type_contract": _rtc("answer")},
            "upstream_prepared_emission": {},
        },
        resolution={"kind": "observe", "prompt": "What do I see?"},
        session={},
        scene_id="yard",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )
    assert dbg.get("response_type_upstream_prepared_absent") is True
    assert dbg.get("response_type_candidate_ok") is False
    assert text == "Only mist between the torches."
    assert "No direct answer is established" not in text


def test_gate_strict_social_dialogue_repair_is_terminal_social_owned_fallback(monkeypatch, _noop_visibility):
    """Thin non-dialogue strict-social candidate is repaired via ``strict_social_ownership_terminal_fallback``, not gate prose."""
    session, world, sid, resolution = _runner_strict_bundle()
    expected = strict_social_ownership_terminal_fallback(resolution)

    def fake_build(candidate_text, *, resolution, tags=None, session=None, scene_id="", world=None):
        return "Wind lifts grit along the cobbles.", {
            "used_internal_fallback": False,
            "final_emitted_source": "test_stub",
            "rejection_reasons": [],
            "deterministic_attempted": False,
            "deterministic_passed": False,
            "fallback_pool": "none",
            "fallback_kind": "none",
            "route_illegal_intercepted": False,
        }

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)
    out = apply_final_emission_gate(
        {
            "player_facing_text": "placeholder",
            "tags": [],
            "response_policy": {"response_type_contract": _rtc("dialogue")},
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("response_type_repair_kind") == "strict_social_dialogue_repair"
    assert _normalize_text(out.get("player_facing_text") or "") == _normalize_text(expected)


def test_route_illegal_visibility_stock_strip_is_packaging_only_preserves_lead():
    """Trailing global-visibility placeholder sentences drop without reordering earlier substance."""
    raw = (
        "Lead sentence alpha. Second sentence beta. For a breath, the scene stays still."
    )
    stripped = feg._strip_appended_route_illegal_contamination_sentences(raw)
    assert stripped.startswith("Lead sentence alpha.")
    assert "beta" in stripped
    assert "scene stays still" not in stripped.lower()
    assert stripped.index("alpha") < stripped.index("beta")


def test_strip_only_sanitizer_extracts_player_text_without_scaffold_rewrite():
    """Serialized payload recovery is packaging (field extraction), not diegetic invention."""
    inner = "Brass hinges gleam in lantern light."
    payload = json.dumps({"player_facing_text": inner, "turn_index": 3, "debug_notes": "x"})
    ctx: dict = {"sanitizer_boundary_mode": "strip_only"}
    out = sanitize_player_facing_output(payload, ctx)
    assert inner in out
    assert "turn_index" not in out
    assert "debug_notes" not in out


def test_strip_only_sanitizer_strips_internal_prefix_without_template_substitution():
    ctx: dict = {"sanitizer_boundary_mode": "strip_only"}
    raw = "validator: The wooden door stands closed in draft and dust."
    out = sanitize_player_facing_output(raw, ctx)
    low = out.lower()
    assert "validator:" not in low
    assert "wooden door" in low


def test_gate_clean_neutral_narration_near_no_op_pass_through(_noop_visibility):
    src = "Rain hammers the slate roof; torchlight shivers in the gutter below."
    out = apply_final_emission_gate(
        {
            "player_facing_text": src,
            "tags": [],
            "response_policy": {"response_type_contract": _rtc("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I look around the street."},
        session={},
        scene_id="market_lane",
        world={},
    )
    assert _normalize_text(out.get("player_facing_text") or "") == _normalize_text(src)
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("response_type_repair_used") is False
