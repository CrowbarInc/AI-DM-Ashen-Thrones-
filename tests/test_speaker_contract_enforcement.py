"""Regression tests for Block 2 speaker_selection_contract enforcement (shipped API)."""
from __future__ import annotations

from copy import deepcopy

import pytest

from game.final_emission_gate import (
    SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES,
    _sync_eff_social_to_resolution,
    detect_emitted_speaker_signature,
    enforce_emitted_speaker_with_contract,
    get_speaker_selection_contract,
    validate_emitted_speaker_against_contract,
)
from game.social import SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS

pytestmark = pytest.mark.unit


def _base_contract(**overrides):
    c = {
        "primary_speaker_id": "runner",
        "primary_speaker_name": "Tavern Runner",
        "allowed_speaker_ids": ["runner"],
        "continuity_locked": True,
        "continuity_lock_reason": "test",
        "speaker_switch_allowed": True,
        "speaker_switch_reason": "test",
        "interruption_allowed": True,
        "interruption_requires_scene_event": False,
        "generic_fallback_forbidden": True,
        "forbidden_fallback_labels": list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS),
        "offscene_speakers_forbidden": True,
        "debug": {"contract_missing": False},
    }
    c.update(overrides)
    return c


# --- 1) Contract retrieval ---


def test_get_speaker_selection_contract_prefers_top_level_metadata_emission_debug():
    c = _base_contract()
    md = {"emission_debug": {"speaker_selection_contract": c}}
    res = {"metadata": {"emission_debug": {"speaker_selection_contract": {"primary_speaker_id": "wrong"}}}}
    got = get_speaker_selection_contract(res, metadata=md, trace=None)
    assert got["primary_speaker_id"] == "runner"


def test_get_speaker_selection_contract_falls_back_to_resolution_metadata_emission_debug():
    c = _base_contract()
    res = {"metadata": {"emission_debug": {"speaker_selection_contract": c}}}
    got = get_speaker_selection_contract(res, metadata=None, trace=None)
    assert got["primary_speaker_id"] == "runner"


def test_get_speaker_selection_contract_trace_speaker_selection_contract():
    c = _base_contract()
    trace = {"speaker_selection_contract": c}
    got = get_speaker_selection_contract(None, metadata=None, trace=trace)
    assert got["primary_speaker_id"] == "runner"


def test_get_speaker_selection_contract_trace_emission_debug():
    c = _base_contract()
    trace = {"emission_debug": {"speaker_selection_contract": c}}
    got = get_speaker_selection_contract(None, metadata=None, trace=trace)
    assert got["primary_speaker_id"] == "runner"


def test_get_speaker_selection_contract_empty_fallback_has_contract_missing():
    got = get_speaker_selection_contract(None, metadata=None, trace=None)
    assert got["debug"].get("contract_missing") is True
    assert got["allowed_speaker_ids"] == []


def test_validate_skips_enforcement_when_contract_missing_no_invented_tightening():
    empty = get_speaker_selection_contract(None, None, None)
    v = validate_emitted_speaker_against_contract(
        'Ragged stranger says, "Secrets."',
        empty,
        resolution=None,
    )
    assert v["ok"] is True
    assert v["reason_code"] == "speaker_contract_match"
    assert v["details"].get("skipped") == "no_contract"
    assert v["repair_mode"] == "none"


# --- 2) Signature detection ---


def test_detect_explicit_opening_attribution_high_confidence():
    sig = detect_emitted_speaker_signature(
        'Tavern Runner says, "East road."',
        resolution=None,
    )
    assert sig["speaker_label"] == "Tavern Runner"
    assert sig["is_explicitly_attributed"] is True
    assert sig["confidence"] == "high"


def test_detect_generic_fallback_label_flagged():
    sig = detect_emitted_speaker_signature(
        'Ragged stranger says, "Who sent you?"',
        resolution=None,
    )
    assert sig["is_generic_fallback_label"] is True


def test_detect_interruption_cue_and_framing():
    t = "Tavern Runner starts to answer, then glances past you as shouting breaks out in the crowd."
    sig = detect_emitted_speaker_signature(t, resolution=None)
    assert sig["has_interruption_framing"] is True


def test_detect_explicit_vs_weak_attribution_confidence():
    sig_weak = detect_emitted_speaker_signature("Someone says your name.", resolution=None)
    assert sig_weak["confidence"] in ("medium", "low")
    sig_hi = detect_emitted_speaker_signature('The captain says, "Hold."', resolution=None)
    assert sig_hi["confidence"] == "high"


def test_ordinary_prose_role_words_not_attribution_without_shape():
    """Generic role words alone do not produce explicit speaker attribution."""
    sig = detect_emitted_speaker_signature(
        "The guard watches the gate while merchants argue about tolls.",
        resolution=None,
    )
    assert sig["speaker_label"] is None
    assert sig["is_explicitly_attributed"] is False


# --- 3) Contract-first validation ---


def test_validation_continuity_locked_wrong_explicit_speaker_fails():
    c = _base_contract()
    v = validate_emitted_speaker_against_contract(
        'Merchant says, "No names."',
        c,
        resolution={"social": {"npc_id": "runner", "npc_name": "Tavern Runner"}},
    )
    assert v["ok"] is False
    assert v["reason_code"] == "speaker_binding_mismatch"
    assert v["repair_mode"] == "local_rebind"


def test_validation_forbidden_generic_fallback_speaker_fails():
    c = _base_contract()
    v = validate_emitted_speaker_against_contract(
        'Ragged stranger mutters, "Maybe."',
        c,
        resolution={"social": {"npc_id": "runner", "npc_name": "Tavern Runner"}},
    )
    assert v["ok"] is False
    assert v["reason_code"] == "forbidden_generic_fallback_speaker"


def test_validation_new_speaker_outside_allowed_fails():
    c = _base_contract(continuity_locked=False, speaker_switch_allowed=False)
    v = validate_emitted_speaker_against_contract(
        'The clerk says, "Try the ward office."',
        c,
        resolution={"social": {"npc_id": "runner", "npc_name": "Tavern Runner"}},
    )
    assert v["ok"] is False
    assert v["reason_code"] == "unjustified_speaker_switch"


def test_validation_no_allowed_speaker_invents_dialogue_fails():
    c = _base_contract(allowed_speaker_ids=[], primary_speaker_id=None, primary_speaker_name=None)
    c["debug"] = {"contract_missing": False}
    c["generic_fallback_forbidden"] = True
    # Use a non-forbidden invented speaker so rule (e) fires before generic-fallback overlap on "someone".
    v = validate_emitted_speaker_against_contract(
        'A ward clerk says, "Hello."',
        c,
        resolution={"social": {}},
    )
    assert v["ok"] is False
    assert v["reason_code"] == "narrator_neutral_no_allowed_speaker"
    assert v["repair_mode"] == "narrator_neutral"


def test_validation_interruption_allowed_with_framing():
    c = _base_contract(interruption_requires_scene_event=False)
    t = "Tavern Runner starts to answer, then shouting breaks out in the crowd."
    v = validate_emitted_speaker_against_contract(
        t,
        c,
        resolution={"social": {"npc_id": "runner", "npc_name": "Tavern Runner"}},
    )
    assert v["ok"] is True
    assert v["reason_code"] == "interruption_justified_switch"


def test_validation_interruption_denied_when_not_permitted():
    c = _base_contract(interruption_allowed=False)
    t = "Tavern Runner starts to answer, then shouting breaks out in the crowd."
    v = validate_emitted_speaker_against_contract(
        t,
        c,
        resolution={"social": {"npc_id": "runner", "npc_name": "Tavern Runner"}},
    )
    assert v["ok"] is False
    assert v["reason_code"] == "interruption_without_contract_support"


def test_validation_interruption_denied_when_speaker_switch_disallowed():
    """Interruption cue + continuity-locked contract with speaker_switch_allowed False => not_permitted rule."""
    c = _base_contract(speaker_switch_allowed=False)
    t = "Tavern Runner starts to answer, then shouting breaks out in the crowd."
    v = validate_emitted_speaker_against_contract(
        t,
        c,
        resolution={"social": {"npc_id": "runner", "npc_name": "Tavern Runner"}},
    )
    assert v["ok"] is False
    assert v["reason_code"] == "interruption_without_contract_support"
    assert v["details"].get("rule") == "interruption_not_permitted"


def test_validation_interruption_requires_scene_event_enforced_shape():
    c = _base_contract(interruption_requires_scene_event=True)
    # No explicit scene-event framing, but quoted speech forces the mixed-blob guard branch.
    t = 'Tavern Runner says, "Wait." Then shouting breaks out.'
    v = validate_emitted_speaker_against_contract(
        t,
        c,
        resolution={"social": {"npc_id": "runner", "npc_name": "Tavern Runner"}},
    )
    assert v["ok"] is False
    assert v["details"].get("rule") == "interruption_requires_scene_event"


def test_validation_pure_narrative_interruption_passes_without_quotes():
    c = _base_contract(interruption_requires_scene_event=True)
    t = "Shouting breaks out in the square as the crowd surges."
    v = validate_emitted_speaker_against_contract(
        t,
        c,
        resolution={"social": {"npc_id": "runner", "npc_name": "Tavern Runner"}},
    )
    assert v["ok"] is True
    assert v["reason_code"] == "interruption_justified_switch"


# --- 4–6) Repair ladder ---


def test_enforce_local_rebind_rewrites_opening_and_syncs_social():
    c = _base_contract()
    eff = {
        "kind": "question",
        "social": {"npc_id": "runner", "npc_name": "Tavern Runner", "social_intent_class": "social_exchange"},
        "metadata": {"emission_debug": {"speaker_selection_contract": c}},
    }
    gm = {"metadata": deepcopy(eff["metadata"]), "trace": {}}
    text_in = 'Merchant says, "I know nothing."'
    out_text, payload = enforce_emitted_speaker_with_contract(
        text_in,
        gm_output=gm,
        resolution=eff,
        eff_resolution=eff,
        world={},
        scene_id="scene_x",
    )
    assert "Merchant" not in out_text
    assert "Tavern Runner" in out_text
    assert '"I know nothing."' in out_text
    assert eff["social"]["npc_id"] == "runner"
    assert eff["social"]["npc_name"] == "Tavern Runner"
    assert payload["final_reason_code"] == "continuity_locked_speaker_repair"


def test_enforce_canonical_rewrite_when_local_rebind_unsafe():
    c = _base_contract()
    eff = {
        "kind": "question",
        "social": {"npc_id": "runner", "npc_name": "Tavern Runner", "social_intent_class": "social_exchange"},
        "metadata": {"emission_debug": {"speaker_selection_contract": c}},
    }
    gm = {"metadata": deepcopy(eff["metadata"]), "trace": {}}
    # Wrong explicit speaker, no quoted salvage — canonical_rewrite path from validation.
    text_in = "Merchant mutters under his breath without giving a straight answer."
    out_text, payload = enforce_emitted_speaker_with_contract(
        text_in,
        gm_output=gm,
        resolution=eff,
        eff_resolution=eff,
        world={},
        scene_id="scene_x",
    )
    assert "Merchant" not in out_text
    assert "Tavern Runner" in out_text
    assert payload["final_reason_code"] == "canonical_speaker_rewrite"
    repair = payload.get("repair") or {}
    assert repair.get("canonical_rewrite_applied") is True


def test_enforce_narrator_neutral_clears_npc_and_sets_bridge_marker():
    c = _base_contract(allowed_speaker_ids=[], primary_speaker_id=None, primary_speaker_name=None)
    c["debug"] = {"contract_missing": False}
    eff = {
        "kind": "question",
        "social": {"npc_id": "runner", "npc_name": "Tavern Runner", "social_intent_class": "social_exchange"},
        "metadata": {"emission_debug": {"speaker_selection_contract": c}},
    }
    gm = {"metadata": deepcopy(eff["metadata"]), "trace": {}}
    out_text, payload = enforce_emitted_speaker_with_contract(
        'Someone says, "Hello."',
        gm_output=gm,
        resolution=eff,
        eff_resolution=eff,
        world={},
        scene_id="scene_x",
    )
    assert eff["social"].get("reply_speaker_grounding_neutral_bridge") is True
    assert eff["social"].get("npc_id") is None
    assert eff["social"].get("npc_name") is None
    assert "murmur" in out_text.lower() or "noise" in out_text.lower() or "moment" in out_text.lower()
    assert payload["final_reason_code"] == "narrator_neutral_no_allowed_speaker"


def test_sync_eff_social_to_resolution_copies_bridge_and_canonical_fields():
    eff = {
        "social": {
            "npc_id": "runner",
            "npc_name": "Tavern Runner",
            "reply_speaker_grounding_neutral_bridge": True,
        }
    }
    res = {"social": {"npc_id": "runner", "npc_name": "Tavern Runner"}}
    _sync_eff_social_to_resolution(eff, res)
    assert res["social"].get("reply_speaker_grounding_neutral_bridge") is True
    assert res["social"].get("npc_id") is None

    eff2 = {"social": {"npc_id": "guard", "npc_name": "The Guard"}}
    res2 = {"social": {"npc_id": "runner", "npc_name": "Tavern Runner"}}
    _sync_eff_social_to_resolution(eff2, res2)
    assert res2["social"]["npc_id"] == "guard"
    assert res2["social"]["npc_name"] == "The Guard"


def test_reason_codes_tuple_is_stable_export():
    assert "speaker_contract_match" in SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES
    assert "continuity_locked_speaker_repair" in SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES
    assert "canonical_speaker_rewrite" in SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES
    assert "narrator_neutral_no_allowed_speaker" in SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES
