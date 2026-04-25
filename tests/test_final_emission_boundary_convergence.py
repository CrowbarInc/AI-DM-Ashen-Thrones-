"""Objective C2 — final emission boundary convergence + ownership lock-in (Block D2).

Invariant tests prefer **behavior and metadata** (repair kinds, FEM flags, stable markers)
over brittle snapshots of private helper names. See ``docs/final_emission_ownership_convergence.md``.
"""
from __future__ import annotations

import json

import pytest

import game.final_emission_gate as feg
from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import default_response_type_debug, read_final_emission_meta_dict
from game.final_emission_validators import _default_response_type_debug as _validators_default_response_type_debug
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
from game.social_exchange_emission import minimal_social_emergency_fallback_line, strict_social_ownership_terminal_fallback
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
            "prepared_action_fallback_text": "You act, and your position changes with that movement.",
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
    assert meta.get("upstream_prepared_emission_used") is True
    assert meta.get("upstream_prepared_emission_valid") is True
    assert meta.get("upstream_prepared_emission_source") == "upstream_prepared_emission.prepared_answer_fallback_text"
    assert meta.get("final_emission_boundary_repair_used") is False
    assert meta.get("final_emission_boundary_semantic_repair_disabled") is True


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
    assert meta.get("upstream_prepared_emission_used") is True
    assert meta.get("upstream_prepared_emission_valid") is True
    assert meta.get("upstream_prepared_emission_source") == "upstream_prepared_emission.prepared_action_fallback_text"
    assert meta.get("final_emission_boundary_repair_used") is False
    assert meta.get("final_emission_boundary_semantic_repair_disabled") is True


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
    assert dbg.get("upstream_prepared_emission_used") is False
    assert dbg.get("upstream_prepared_emission_valid") is False
    assert dbg.get("upstream_prepared_emission_source") == "absent"
    assert dbg.get("final_emission_boundary_repair_used") is False
    assert dbg.get("final_emission_boundary_semantic_repair_disabled") is True


def test_gate_preserves_duplicate_speaker_subject_lines_no_quote_merge_for_cadence(_noop_visibility):
    """Same speaker twice must not be collapsed into one quoted span for cadence (no multi-speaker merge)."""
    twin = (
        'Rook: "First watch ends soon."\n'
        'Rook: "Second watch picks up the lane."'
    )
    gm = {
        "player_facing_text": twin,
        "tags": [],
        "response_policy": {"response_type_contract": _rtc("dialogue")},
    }
    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "question", "prompt": "What does Rook say?"},
        session=None,
        scene_id="wall",
        world={},
    )
    txt = str(out.get("player_facing_text") or "")
    assert txt.count("Rook:") == 2
    assert "First watch" in txt and "Second watch" in txt
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("social_response_structure_repair_applied") is not True


def test_enforce_response_type_upstream_attribution_override():
    text, dbg = feg._enforce_response_type_contract(
        "Fog.",
        gm_output={
            "response_policy": {"response_type_contract": _rtc("answer")},
            "upstream_prepared_emission": {
                "prepared_answer_fallback_text": "ZETA none east pier yet.",
                "upstream_prepared_emission_attribution": "test_harness",
            },
        },
        resolution={"kind": "observe", "prompt": "What do I see?"},
        session={},
        scene_id="yard",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )
    assert dbg.get("upstream_prepared_emission_used") is True
    assert dbg.get("upstream_prepared_emission_source") == "test_harness"


def test_response_type_debug_default_keys_match_meta_validators_modules():
    """RTD1 / FEM upstream-prepared fields stay aligned across meta, validators, and gate merge."""
    c = {"required_response_type": "answer", "action_must_preserve_agency": False}
    keys_meta = frozenset(default_response_type_debug(c, "unit").keys())
    keys_val = frozenset(_validators_default_response_type_debug(c, "unit").keys())
    assert keys_meta == keys_val
    required = frozenset(
        {
            "upstream_prepared_emission_used",
            "upstream_prepared_emission_valid",
            "upstream_prepared_emission_source",
            "upstream_prepared_emission_reject_reason",
            "final_emission_boundary_repair_used",
            "final_emission_boundary_semantic_repair_disabled",
            "response_type_upstream_prepared_absent",
        }
    )
    assert required <= keys_meta


def test_enforce_response_type_rejects_malformed_upstream_answer_without_boundary_synthesis():
    """Non-empty prepared text that fails the answer contract is not adopted; gate does not mint a substitute."""
    text, dbg = feg._enforce_response_type_contract(
        "Only mist between the torches.",
        gm_output={
            "response_policy": {"response_type_contract": _rtc("answer")},
            "upstream_prepared_emission": {"prepared_answer_fallback_text": "Why ask that?"},
        },
        resolution={"kind": "observe", "prompt": "What do I see?"},
        session={},
        scene_id="yard",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )
    assert dbg.get("response_type_candidate_ok") is False
    assert text == "Only mist between the torches."
    assert dbg.get("upstream_prepared_emission_used") is False
    assert dbg.get("upstream_prepared_emission_valid") is False
    assert dbg.get("upstream_prepared_emission_reject_reason") == "answer_is_another_question"
    assert dbg.get("response_type_upstream_prepared_absent") is not True


def test_enforce_response_type_rejects_malformed_upstream_action_without_boundary_synthesis():
    """Quoted NPC-only prepared action text fails action_outcome contract; gate keeps candidate text."""
    text, dbg = feg._enforce_response_type_contract(
        "You pry the chest lid, but nothing gives yet.",
        gm_output={
            "response_policy": {"response_type_contract": _rtc("action_outcome")},
            "upstream_prepared_emission": {"prepared_action_fallback_text": 'She says, "All quiet."'},
        },
        resolution={"kind": "investigate", "prompt": "Pry the chest lid"},
        session={"last_player_action_text": "Pry the chest lid"},
        scene_id="cellar",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )
    assert dbg.get("response_type_candidate_ok") is False
    assert text == "You pry the chest lid, but nothing gives yet."
    assert dbg.get("upstream_prepared_emission_used") is False
    assert dbg.get("upstream_prepared_emission_valid") is False
    assert dbg.get("upstream_prepared_emission_reject_reason") == "action_outcome_replaced_by_dialogue"
    assert dbg.get("response_type_upstream_prepared_absent") is not True


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


def test_gate_valid_answer_passes_unchanged_modulo_packaging_normalization(_noop_visibility):
    """Contract-satisfying answer text is not rewritten for completeness; only normalization may apply."""
    raw = "  The   east   gate   is   barred.  "
    gm = {
        "player_facing_text": raw,
        "tags": [],
        "response_policy": {"response_type_contract": _rtc("answer")},
    }
    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "observe", "prompt": "What blocks the road?"},
        session={},
        scene_id="road",
        world={},
    )
    assert _normalize_text(out.get("player_facing_text") or "") == _normalize_text(
        "The east gate is barred."
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("response_type_candidate_ok") is True
    assert meta.get("upstream_prepared_emission_used") is not True
    assert meta.get("final_emission_boundary_semantic_repair_disabled") is True


def test_enforce_dialogue_contract_minimal_repair_delegates_to_social_module_not_gate_composition():
    """Thin non-dialogue text is repaired via ``minimal_social_emergency_fallback_line`` (social module), not gate prose."""
    resolution = {
        "kind": "question",
        "prompt": "What does Rook say?",
        "social": {"npc_id": "rook", "npc_name": "Rook", "social_intent_class": "social_exchange"},
    }
    expected = minimal_social_emergency_fallback_line(resolution)
    text, dbg = feg._enforce_response_type_contract(
        "The sky is grey and still.",
        gm_output={
            "response_policy": {"response_type_contract": _rtc("dialogue")},
        },
        resolution=resolution,
        session=None,
        scene_id="wall",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )
    assert _normalize_text(text) == _normalize_text(expected)
    assert dbg.get("response_type_repair_kind") == "dialogue_minimal_repair"
    assert dbg.get("response_type_repair_used") is True
    assert dbg.get("final_emission_boundary_semantic_repair_disabled") is True


def test_gate_upstream_bundle_origin_preserved_separate_from_fem_source_attribution(_noop_visibility):
    """``upstream_prepared_bundle_origin`` stays on the payload; FEM ``upstream_prepared_emission_source`` uses attribution."""
    bundle_tag = "fixture.test_bundle_origin_lock"
    marker_answer = "The east gate is barred and manned."
    marker_action = "You pry the chest lid, and the attempt produces an immediate result."
    gm = {
        "player_facing_text": "Fog.",
        "tags": [],
        "response_policy": {"response_type_contract": _rtc("answer")},
        UPSTREAM_PREPARED_EMISSION_KEY: {
            "prepared_answer_fallback_text": marker_answer,
            "prepared_action_fallback_text": marker_action,
            "upstream_prepared_emission_attribution": "harness.attrib_only",
            "upstream_prepared_bundle_origin": bundle_tag,
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
    assert meta.get("upstream_prepared_emission_source") == "harness.attrib_only"
    up = out.get(UPSTREAM_PREPARED_EMISSION_KEY)
    assert isinstance(up, dict)
    assert up.get("upstream_prepared_bundle_origin") == bundle_tag
    assert "upstream_prepared_bundle_origin" not in meta


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
