"""Regression suite for ``response_policy.response_delta`` (Block 2) in ``final_emission_gate``.

Tests the implemented skip logic, ``validate_response_delta``, minimal repair modes, and
``apply_final_emission_gate`` integration. Direct response-policy accessor and bundle
materialization ownership lives in ``tests/test_response_policy_contracts.py``; this file
keeps downstream gate application and regression coverage aligned to current code rather
than prompt-context derivation.
"""
from __future__ import annotations

from game.final_emission_meta import read_final_emission_meta_dict

import importlib

import pytest

from game.final_emission_gate import (
    _apply_response_delta_layer,
    _skip_answer_completeness_layer,
    _skip_response_delta_layer,
    _strict_social_answer_pressure_rd_contract_active,
    apply_final_emission_gate,
    inspect_response_delta_failure,
    validate_response_delta,
)

_prompt_context = importlib.import_module("game.prompt_context")
ANSWER_COMPLETENESS_PARTIAL_REASONS = _prompt_context.ANSWER_COMPLETENESS_PARTIAL_REASONS
build_answer_completeness_contract = _prompt_context.build_answer_completeness_contract

pytestmark = pytest.mark.unit

# --- Shared fixtures / helpers -------------------------------------------------


def _obligations_explore_no_npc() -> dict:
    return {
        "suppress_non_social_emitters": False,
        "should_answer_active_npc": False,
        "active_npc_reply_expected": False,
        "active_npc_reply_kind": None,
    }


def _response_type_debug(
    *,
    candidate_ok: bool | None = True,
    repair_kind: str | None = None,
) -> dict:
    return {
        "response_type_required": None,
        "response_type_contract_source": None,
        "response_type_candidate_ok": candidate_ok,
        "response_type_repair_used": repair_kind is not None,
        "response_type_repair_kind": repair_kind,
        "response_type_rejection_reasons": [],
        "non_hostile_escalation_blocked": False,
    }


def _ac_meta(*, failed: bool = False) -> dict:
    return {"answer_completeness_failed": failed}


def _base_rd_contract(
    *,
    allowed_delta_kinds: list[str] | None = None,
    **extra: object,
) -> dict:
    """Hand-built Block 2 contract; ``allowed_delta_kinds`` pins which detectors may fire."""
    c: dict = {
        "enabled": True,
        "delta_required": True,
        "previous_answer_snippet": (
            "The watch keeps a lane open on the east road past the old mill checkpoint."
        ),
        "allowed_delta_kinds": allowed_delta_kinds
        or ["new_information", "refinement", "consequence", "clarified_uncertainty"],
        "delta_must_come_early": False,
        "allow_short_bridge_before_delta": False,
        "expected_delta_shape": "direct_delta",
        "trace": {"trigger_source": "test"},
    }
    for k, v in extra.items():
        c[k] = v
    return c


def _gm_with_delta(text: str, rd: dict | None, ac: dict | None = None) -> dict:
    pol: dict = {}
    if rd is not None:
        pol["response_delta"] = rd
    if ac is not None:
        pol["answer_completeness"] = ac
    return {"player_facing_text": text, "tags": [], "response_policy": pol}


def _apply_rd(
    text: str,
    rd_contract: dict,
    *,
    response_type_debug: dict | None = None,
    ac_meta: dict | None = None,
    strict_social_path: bool = False,
    strict_social_details: dict | None = None,
) -> tuple[str, dict, list]:
    return _apply_response_delta_layer(
        text,
        gm_output=_gm_with_delta(text, rd_contract),
        strict_social_details=strict_social_details,
        response_type_debug=response_type_debug or _response_type_debug(),
        answer_completeness_meta=ac_meta or _ac_meta(),
        strict_social_path=strict_social_path,
    )


# =============================================================================
# 1. Skip-path tests
# =============================================================================


def test_response_delta_skips_without_contract():
    raw = "East road past the mill, with the watch in sight lines."
    out, meta, extra = _apply_response_delta_layer(
        raw,
        gm_output={"player_facing_text": raw, "tags": [], "response_policy": {}},
        strict_social_details=None,
        response_type_debug=_response_type_debug(),
        answer_completeness_meta=_ac_meta(),
        strict_social_path=False,
    )
    assert out == raw
    assert meta["response_delta_checked"] is False
    assert meta["response_delta_skip_reason"] == "no_response_delta_contract"
    assert extra == []


def test_response_delta_skips_when_disabled():
    c = {**_base_rd_contract(), "enabled": False}
    raw = "Precisely east past the mill and the bonded warehouse."
    out, meta, extra = _apply_rd(raw, c)
    assert out == raw
    assert meta["response_delta_checked"] is False
    assert meta["response_delta_skip_reason"] == "response_delta_disabled"


def test_response_delta_skips_when_delta_not_required():
    c = {**_base_rd_contract(), "delta_required": False}
    raw = "East road, specifically past the customs ditch."
    out, meta, extra = _apply_rd(raw, c)
    assert out == raw
    assert meta["response_delta_skip_reason"] == "delta_not_required"


def test_response_delta_skips_when_previous_snippet_unavailable():
    c = {**_base_rd_contract(), "previous_answer_snippet": "Short."}
    raw = "East road past the mill."
    out, meta, extra = _apply_rd(raw, c)
    assert meta["response_delta_skip_reason"] == "previous_answer_snippet_unavailable"


def test_response_delta_skips_when_allowed_delta_kinds_empty():
    c = {**_base_rd_contract(), "allowed_delta_kinds": []}
    raw = "East road past the mill."
    out, meta, extra = _apply_rd(raw, c)
    assert meta["response_delta_skip_reason"] == "allowed_delta_kinds_empty"


def test_response_delta_skips_when_emitted_text_empty():
    c = _base_rd_contract()
    out, meta, extra = _apply_rd("", c)
    assert out == ""
    assert meta["response_delta_skip_reason"] == "empty_emitted_text"


def test_response_delta_skips_when_response_type_candidate_ok_false():
    c = _base_rd_contract()
    raw = "East road, precisely past the mill."
    out, meta, extra = _apply_rd(
        raw,
        c,
        response_type_debug=_response_type_debug(candidate_ok=False),
    )
    assert out == raw
    assert meta["response_delta_skip_reason"] == "response_type_contract_failed"


def test_response_delta_skips_when_answer_completeness_failed():
    c = _base_rd_contract()
    raw = "East road past the mill."
    out, meta, extra = _apply_rd(raw, c, ac_meta=_ac_meta(failed=True))
    assert out == raw
    assert meta["response_delta_skip_reason"] == "answer_completeness_failed"


def test_response_delta_skips_strict_social_used_internal_fallback():
    c = _base_rd_contract()
    raw = "East road past the mill."
    out, meta, extra = _apply_rd(
        raw,
        c,
        strict_social_details={"used_internal_fallback": True},
    )
    assert out == raw
    assert meta["response_delta_skip_reason"] == "strict_social_authoritative_internal_fallback"
    assert meta["response_delta_failed"] is False


def test_response_delta_skips_strict_social_dialogue_repair_ownership():
    c = _base_rd_contract()
    raw = "East road past the mill."
    out, meta, extra = _apply_rd(
        raw,
        c,
        response_type_debug=_response_type_debug(repair_kind="strict_social_dialogue_repair"),
        strict_social_details={"ownership": "strict_social_terminal"},
    )
    assert meta["response_delta_skip_reason"] == "strict_social_ownership_terminal_repair"


def test_response_delta_skips_strict_social_bridge_source_ownership():
    c = _base_rd_contract()
    raw = "East road past the mill."
    out, meta, extra = _apply_rd(
        raw,
        c,
        strict_social_details={"final_emitted_source": "neutral_reply_speaker_grounding_bridge"},
    )
    assert meta["response_delta_skip_reason"] == "strict_social_structured_or_bridge_source"


def test_response_delta_skips_strict_social_structured_fact_source():
    c = _base_rd_contract()
    raw = "East road past the mill."
    out, meta, extra = _apply_rd(
        raw,
        c,
        strict_social_details={"final_emitted_source": "structured_fact_candidate_emission"},
    )
    assert meta["response_delta_skip_reason"] == "strict_social_structured_or_bridge_source"


def test_response_delta_does_not_skip_bridge_when_strict_social_answer_pressure_contract():
    """Block 2: bridge/structured ownership skip is bypassed when RD is activated for answer-pressure."""
    c = {
        **_base_rd_contract(),
        "trigger_source": "strict_social_answer_pressure",
        "trace": {"trigger_source": "strict_social_answer_pressure"},
    }
    raw = "East road past the mill."
    gm = _gm_with_delta(raw, c)
    skip = _skip_response_delta_layer(
        contract=c,
        emitted_text=raw,
        strict_social_details={"final_emitted_source": "neutral_reply_speaker_grounding_bridge"},
        response_type_debug=_response_type_debug(),
        answer_completeness_meta=_ac_meta(),
        gm_output=gm,
    )
    assert skip is None


def test_answer_completeness_does_not_skip_bridge_when_strict_social_answer_pressure_contract():
    ac = {
        "enabled": True,
        "answer_required": True,
        "answer_must_come_first": True,
        "expected_voice": "npc",
        "expected_answer_shape": "direct",
        "allowed_partial_reasons": list(ANSWER_COMPLETENESS_PARTIAL_REASONS),
        "forbid_deflection": True,
        "forbid_generic_nonanswer": True,
        "require_concrete_payload": True,
        "concrete_payload_any_of": ["place", "fact"],
        "trace": {"strict_social_answer_seek_override": True},
    }
    gm = {"player_facing_text": "Line.", "tags": [], "response_policy": {"answer_completeness": ac}}
    skip = _skip_answer_completeness_layer(
        strict_social_details={"final_emitted_source": "structured_fact_candidate_emission"},
        response_type_debug=_response_type_debug(),
        gm_output=gm,
    )
    assert skip is None


def test_strict_social_answer_pressure_rd_contract_active_from_trace_only():
    """Block 1/2: root ``trigger_source`` may be shadowed; trace still activates answer-pressure RD."""
    gm = {
        "player_facing_text": "stub",
        "tags": [],
        "response_policy": {
            "response_delta": {
                "enabled": True,
                "delta_required": True,
                "trigger_source": "follow_up_pressure",
                "trace": {"trigger_source": "strict_social_answer_pressure"},
            }
        },
    }
    assert _strict_social_answer_pressure_rd_contract_active(gm) is True


# =============================================================================
# 2. Validator pass tests
# =============================================================================


def test_validate_response_delta_accepts_refinement_with_high_overlap():
    # Priority order lists ``new_information`` first; restrict kinds so refinement wins.
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    prior = "East road past the mill checkpoint."
    emitted = "East road, precisely past the old mill and toward the customs ditch."
    c["previous_answer_snippet"] = prior
    r = validate_response_delta(emitted, c)
    assert r["checked"] is True
    assert r["passed"] is True
    assert r["delta_kind_detected"] == "refinement"
    assert r["echo_overlap_ratio"] is not None
    assert r["echo_overlap_ratio"] >= 0.4


def test_validate_response_delta_accepts_new_information_despite_overlap():
    c = _base_rd_contract(allowed_delta_kinds=["new_information"])
    c["previous_answer_snippet"] = "He works the quay near the riverfront market district."
    emitted = "He works the quay, in the bonded warehouse by the south crane."
    r = validate_response_delta(emitted, c)
    assert r["passed"] is True
    assert r["delta_kind_detected"] == "new_information"


def test_validate_response_delta_accepts_consequence():
    c = _base_rd_contract(allowed_delta_kinds=["consequence"])
    c["previous_answer_snippet"] = "The watch is on the east road near the mill."
    emitted = (
        "The watch is on the east road; therefore they will spot you before the mill if you go now."
    )
    r = validate_response_delta(emitted, c)
    assert r["passed"] is True
    assert r["delta_kind_detected"] == "consequence"


def test_validate_response_delta_accepts_clarified_uncertainty():
    c = _base_rd_contract(allowed_delta_kinds=["clarified_uncertainty"])
    c["previous_answer_snippet"] = "I do not know his name from the muster roll alone."
    emitted = (
        "I do not know his name, but he might be the clerk I saw near the south quay."
    )
    r = validate_response_delta(emitted, c)
    assert r["passed"] is True
    assert r["delta_kind_detected"] == "clarified_uncertainty"


def test_validate_response_delta_accepts_high_overlap_when_kind_detected():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["previous_answer_snippet"] = (
        "The watch keeps a lane open on the east road past the old mill checkpoint."
    )
    emitted = (
        "The watch keeps a lane open on the east road past the old mill checkpoint, "
        "rather than the western timber trace."
    )
    r = validate_response_delta(emitted, c)
    assert r["checked"] is True
    assert r["passed"] is True
    assert r["delta_kind_detected"] == "refinement"
    assert r["echo_overlap_ratio"] is not None
    assert r["echo_overlap_ratio"] >= 0.68


def test_validate_response_delta_gate_level_passes_clean_refinement():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["previous_answer_snippet"] = "East road past the mill checkpoint."
    text = "East road, precisely past the customs ditch and the bonded yard."
    out, meta, extra = _apply_rd(text, c)
    assert out == text
    assert meta["response_delta_checked"] is True
    assert meta["response_delta_failed"] is False
    assert meta["response_delta_kind_detected"] == "refinement"
    assert extra == []


# =============================================================================
# 3. Validator fail tests
# =============================================================================


def test_validate_response_delta_rejects_pure_paraphrase():
    # Exclude ``new_information`` so token novelty cannot mask a pure paraphrase failure.
    c = _base_rd_contract(allowed_delta_kinds=["refinement", "consequence", "clarified_uncertainty"])
    c["previous_answer_snippet"] = (
        "The eastern patrol uses the old mill road as its primary route nightly."
    )
    emitted = (
        "The eastern patrol route uses the old mill road as its primary path each night."
    )
    r = validate_response_delta(emitted, c)
    assert r["checked"] is True
    assert r["passed"] is False
    assert "no_delta_detected" in r["failure_reasons"]


def test_validate_response_delta_rejects_opening_semantic_restatement():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["previous_answer_snippet"] = "The watch patrols the east road checkpoint nightly."
    emitted = (
        "The watch patrols the east road checkpoint nightly. "
        "Specifically they rotate shifts at midnight by the mill."
    )
    r = validate_response_delta(emitted, c)
    assert r["passed"] is False
    assert "opening_semantic_restatement" in r["failure_reasons"]
    assert r["delta_kind_detected"] == "refinement"


def test_validate_response_delta_rejects_full_response_semantic_restatement():
    c = _base_rd_contract(allowed_delta_kinds=["refinement", "consequence", "clarified_uncertainty"])
    prior = "The watch keeps a lane open on the east road past the old mill checkpoint."
    c["previous_answer_snippet"] = prior
    emitted = prior + " " + prior.replace("checkpoint", "checkpoint tonight")
    r = validate_response_delta(emitted, c)
    assert r["passed"] is False
    assert "full_response_semantic_restatement" in r["failure_reasons"]


def test_validate_response_delta_rejects_repackaged_nonanswer():
    c = _base_rd_contract()
    c["previous_answer_snippet"] = (
        "The watch keeps a lane open on the east road past the old mill checkpoint."
    )
    emitted = "Maybe the watch keeps a lane open on the east road past the old mill checkpoint."
    r = validate_response_delta(emitted, c)
    assert r["passed"] is False
    assert "repackaged_nonanswer" in r["failure_reasons"]


def test_validate_response_delta_rejects_repeated_partial_without_new_boundary():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["expected_delta_shape"] = "bounded_partial_with_delta"
    c["previous_answer_snippet"] = (
        "I am not sure which sergeant signed the roster; the ledger is unclear about names here."
    )
    emitted = (
        "I am not sure which sergeant signed the roster; the ledger is unclear about names here "
        "under the captain orders."
    )
    r = validate_response_delta(emitted, c)
    assert r["passed"] is False
    assert "repeated_partial_without_new_boundary" in r["failure_reasons"]


def test_validate_response_delta_rejects_caveat_shuffle_only():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["expected_delta_shape"] = "bounded_partial_with_delta"
    c["previous_answer_snippet"] = (
        "I do not know the name; I was not on duty when the ledger was signed."
    )
    emitted = (
        "I was not on duty when the ledger was signed; I do not know the name from the roster."
    )
    r = validate_response_delta(emitted, c)
    assert r["passed"] is False
    insp = inspect_response_delta_failure(r)
    assert insp["failed"] is True
    assert r["failure_reasons"]


def test_validate_response_delta_failure_populates_echo_and_restatement_flags():
    c = _base_rd_contract()
    c["previous_answer_snippet"] = "The watch patrols the east road checkpoint nightly."
    emitted = "The watch patrols the east road checkpoint each night without change."
    r = validate_response_delta(emitted, c)
    assert r["echo_overlap_ratio"] is not None
    assert r["direct_restatement_detected"] in (True, False)


# =============================================================================
# 4. Early-delta tests
# =============================================================================


def test_response_delta_requires_early_delta_when_configured():
    c = _base_rd_contract()
    c["delta_must_come_early"] = True
    c["allow_short_bridge_before_delta"] = False
    c["previous_answer_snippet"] = "The watch keeps a lane open on the east road past the mill."
    emitted = (
        "The watch keeps a lane open on the east road past the mill. "
        "Rain slicks the stones. "
        "Specifically the bonded warehouse sits past the ditch."
    )
    r = validate_response_delta(emitted, c)
    assert r["passed"] is False
    assert "follow_up_answer_without_refinement" in r["failure_reasons"]


def test_response_delta_allows_short_bridge_then_delta_in_second_sentence():
    # First sentence must not alone trigger ``opening_semantic_restatement`` vs prior (low overlap).
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["delta_must_come_early"] = True
    c["allow_short_bridge_before_delta"] = True
    c["previous_answer_snippet"] = "The watch keeps a lane open on the east road past the mill."
    emitted = (
        "Rain slicks the cobbles along the verge. "
        "Specifically the bonded warehouse sits past the customs ditch."
    )
    r = validate_response_delta(emitted, c)
    assert r["passed"] is True
    assert r["early_delta_found"] is True


def test_response_delta_early_delta_in_first_sentence_passes():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["delta_must_come_early"] = True
    c["previous_answer_snippet"] = "The watch keeps a lane open on the east road past the mill."
    emitted = "Specifically the bonded warehouse sits just past the customs ditch on that lane."
    r = validate_response_delta(emitted, c)
    assert r["passed"] is True
    assert r["early_delta_found"] is True


def test_response_delta_allows_late_delta_when_early_not_required():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["delta_must_come_early"] = False
    c["previous_answer_snippet"] = "The watch keeps a lane open on the east road past the mill."
    emitted = (
        "Rain slicks the cobbles along the verge. "
        "The watch keeps a lane open on the east road past the mill. "
        "Specifically the bonded warehouse sits past the customs ditch."
    )
    r = validate_response_delta(emitted, c)
    assert r["passed"] is True


# =============================================================================
# 5. Minimal repair tests
# =============================================================================
# ``_repair_response_delta_minimal`` tries ``frontload_delta_sentence`` before
# ``trim_echo_opening`` / ``prioritize_refinement_before_caveat`` / ``drop_duplicate_partial_prefix`` /
# ``compress_echo_plus_delta``. Most two-sentence fixes surface as frontload in practice.


def test_response_delta_frontloads_existing_delta_sentence():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["previous_answer_snippet"] = "The watch keeps a lane open on the east road past the mill."
    raw = (
        "The watch keeps a lane open on the east road past the mill. "
        "Specifically the bonded warehouse sits past the customs ditch."
    )
    out, meta, extra = _apply_rd(raw, c)
    assert meta["response_delta_repaired"] is True
    assert meta["response_delta_repair_mode"] == "frontload_delta_sentence"
    assert out.startswith("Specifically the bonded warehouse")
    assert meta["response_delta_failed"] is False
    assert extra == []


def test_response_delta_trim_echo_opening():
    """Echo-first layout plus later substantive line: Block 2 resolves via ``frontload_delta_sentence`` first."""
    c = _base_rd_contract(allowed_delta_kinds=["new_information"])
    c["previous_answer_snippet"] = "The watch keeps a lane open on the east road past the mill."
    c["delta_must_come_early"] = False
    raw = (
        "The watch keeps a lane open on the east road past the mill. "
        "Twelve guards hold the bonded warehouse past the customs ditch tonight."
    )
    out, meta, extra = _apply_rd(raw, c)
    assert meta["response_delta_repair_mode"] == "frontload_delta_sentence"
    assert "Twelve guards hold" in out
    assert out.lower().startswith("twelve guards")


def test_response_delta_prioritize_refinement_before_caveat():
    """Caveat-first layout can violate early-delta; repair front-loads the refinement (step 3 mirrors this swap)."""
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["previous_answer_snippet"] = "He works the quay near the riverfront market district."
    c["delta_must_come_early"] = True
    c["allow_short_bridge_before_delta"] = False
    raw = (
        "I do not know his name from the ledger. "
        "Specifically he works the bonded warehouse by the south crane."
    )
    out, meta, extra = _apply_rd(raw, c)
    assert meta["response_delta_repair_mode"] == "frontload_delta_sentence"
    assert out.lower().index("specifically") < out.lower().index("do not know")


def test_response_delta_drop_duplicate_partial_prefix():
    c = _base_rd_contract(allowed_delta_kinds=["new_information"])
    c["previous_answer_snippet"] = "I do not know the sergeant name from the muster roll."
    raw = (
        "I do not know the sergeant name from the muster roll. "
        "I do not know the sergeant name from the roster lines either, "
        "but the quartermaster calls him Brick."
    )
    out, meta, extra = _apply_rd(raw, c)
    assert meta["response_delta_repair_mode"] == "frontload_delta_sentence"
    assert "Brick" in out


def test_response_delta_compress_echo_plus_delta():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["previous_answer_snippet"] = "He works the quay near the riverfront market district."
    raw = (
        "He works the quay near the riverfront market district. "
        "Specifically the bonded warehouse by the south crane handles the cargo."
    )
    out, meta, extra = _apply_rd(raw, c)
    assert meta["response_delta_repair_mode"] == "frontload_delta_sentence"
    assert "bonded warehouse" in out.lower()


def test_response_delta_no_fabricated_repair_when_no_valid_later_delta():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["previous_answer_snippet"] = (
        "The watch keeps a lane open on the east road past the old mill checkpoint."
    )
    raw = (
        "The watch keeps a lane open on the east road past the old mill checkpoint. "
        "Rain slicks the cobbles. "
        "Fog drifts over the riverfront."
    )
    out, meta, extra = _apply_rd(raw, c)
    assert out == raw
    assert meta["response_delta_repaired"] is False
    assert meta["response_delta_failed"] is True
    assert extra == ["response_delta_unsatisfied_after_repair"]


# =============================================================================
# 6. Integration / compatibility tests
# =============================================================================


def test_response_delta_runs_after_answer_completeness_non_social():
    """Delta layer consults ``answer_completeness_failed``; terminal AC failure skips response-delta."""
    ac_contract = build_answer_completeness_contract(
        player_input="Where did they go?",
        narration_obligations=_obligations_explore_no_npc(),
        resolution={"kind": "adjudication_query", "prompt": "Where did they go?"},
        session_view={},
        uncertainty_hint=None,
    )
    rd = _base_rd_contract()
    rd["previous_answer_snippet"] = "They went east past the mill toward the treeline."
    raw = "Maybe people talk about routes, but hard to say from here."
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "response_policy": {"answer_completeness": ac_contract, "response_delta": rd}},
        resolution={"kind": "adjudication_query", "prompt": "Where did they go?"},
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("answer_completeness_failed") is True
    assert meta.get("response_delta_skip_reason") == "answer_completeness_failed"


def test_ac_repair_precedence_then_delta_on_repaired_text():
    """AC minimal repair runs first; response-delta validates the post-AC string."""
    ac_contract = {
        "enabled": True,
        "answer_required": True,
        "answer_must_come_first": True,
        "player_direct_question": True,
        "expected_voice": "either",
        "expected_answer_shape": "direct",
        "allowed_partial_reasons": list(ANSWER_COMPLETENESS_PARTIAL_REASONS),
        "forbid_deflection": True,
        "forbid_generic_nonanswer": True,
        "require_concrete_payload": True,
        "concrete_payload_any_of": ["place", "direction", "name"],
        "trace": {},
    }
    rd = _base_rd_contract()
    rd["previous_answer_snippet"] = "East road past the mill toward the customs ditch."
    raw = (
        "The square holds for a moment. "
        "East road past the mill toward the customs ditch, specifically past the bonded warehouse."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "response_policy": {"answer_completeness": ac_contract, "response_delta": rd}},
        resolution={"kind": "adjudication_query", "prompt": "Which way?"},
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("answer_completeness_repaired") is True
    assert meta.get("response_delta_checked") is True
    assert meta.get("response_delta_failed") is False


def test_final_emitted_source_reflects_response_delta_repair_mode():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["previous_answer_snippet"] = "The watch keeps a lane open on the east road past the mill."
    raw = (
        "The watch keeps a lane open on the east road past the mill. "
        "Specifically the bonded warehouse sits past the customs ditch."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "response_policy": {"response_delta": c}},
        resolution={"kind": "adjudication_query", "prompt": "Same road detail?"},
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("response_delta_repaired") is True
    assert meta.get("final_emitted_source") == meta.get("response_delta_repair_mode")


def test_response_delta_unrepaired_failure_triggers_gate_replace_reason():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["previous_answer_snippet"] = (
        "The watch keeps a lane open on the east road past the old mill checkpoint."
    )
    raw = (
        "The watch keeps a lane open on the east road past the old mill checkpoint. "
        "Rain slicks the cobbles. "
        "Fog drifts over the riverfront."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "response_policy": {"response_delta": c}},
        resolution={"kind": "adjudication_query", "prompt": "Tell me again?"},
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("final_route") == "replaced"
    sample = meta.get("rejection_reasons_sample") or []
    assert "response_delta_unsatisfied_after_repair" in sample


def test_response_delta_strict_social_owned_path_adds_no_extra_reason():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["previous_answer_snippet"] = (
        "The watch keeps a lane open on the east road past the old mill checkpoint."
    )
    raw = (
        "The watch keeps a lane open on the east road past the old mill checkpoint. "
        "Rain slicks the cobbles."
    )
    out, meta, extra = _apply_rd(raw, c, strict_social_path=True)
    assert meta["response_delta_failed"] is True
    assert extra == []


def test_response_delta_repair_preserves_npc_voice_trim():
    c = _base_rd_contract()
    c["previous_answer_snippet"] = "The watch keeps a lane open on the east road past the mill."
    raw = (
        'The watch keeps a lane open on the east road past the mill. '
        '"Twelve guards tonight," she mutters, "past the bonded warehouse."'
    )
    out, meta, extra = _apply_rd(raw, c)
    if meta.get("response_delta_repaired"):
        assert '"' in out or "mutters" in out.lower()


def test_response_delta_repair_preserves_pronoun_referent_order():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["previous_answer_snippet"] = "He works the quay near the riverfront market district."
    raw = (
        "I do not know his name from the ledger. "
        "Specifically he works the bonded warehouse by the south crane."
    )
    out, meta, extra = _apply_rd(raw, c)
    if meta.get("response_delta_repaired"):
        assert "he" in out.lower()
        assert "specifically" in out.lower()


def test_response_delta_repair_does_not_invent_gated_facts():
    c = _base_rd_contract(allowed_delta_kinds=["refinement"])
    c["previous_answer_snippet"] = "The watch keeps a lane open on the east road past the mill."
    raw = (
        "The watch keeps a lane open on the east road past the mill. "
        "Specifically the bonded warehouse sits past the customs ditch."
    )
    out, meta, extra = _apply_rd(raw, c)
    if meta.get("response_delta_repaired"):
        for token in ("secret", "hidden", "underground"):
            assert token not in out.lower()
