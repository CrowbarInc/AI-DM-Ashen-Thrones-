"""Regression tests for Block 2 speaker_selection_contract enforcement (shipped API).

Owner tests for ``game.speaker_contract_enforcement`` including ``enforce_emitted_speaker_with_contract``.
Gate skip-path and layer-order pins remain in ``tests/test_final_emission_gate.py`` (BH-4)."""
from __future__ import annotations

from copy import deepcopy

import pytest

import game.dialogue_social_plan as dialogue_social_plan
import game.final_emission_strict_social_stack as strict_social_stack
import game.final_emission_referential_clarity as referential_clarity
import game.final_emission_visibility_fallback as visibility_fallback
import game.speaker_contract_enforcement as sce
from game.emitted_speaker_signature import detect_emitted_speaker_signature
from tests.helpers.gate_orchestration_smoke import apply_final_emission_gate_consumer
from tests.helpers.response_type_smoke import response_type_contract
from tests.helpers.strict_social_harness import (
    run_strict_social_motive_overclaim_gate_case,
    runner_strict_bundle,
)
from game.speaker_contract_enforcement import (
    SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES,
    _sync_eff_social_to_resolution,
    enforce_emitted_speaker_with_contract,
    get_speaker_selection_contract,
    validate_emitted_speaker_against_contract,
)
from game.social import SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS

pytestmark = pytest.mark.unit


def _apply_gate(*args, **kwargs):
    out, _ = apply_final_emission_gate_consumer(*args, **kwargs)
    return out


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


# ---------------------------------------------------------------------------
# BH-4: extracted from tests/test_final_emission_gate.py
# ---------------------------------------------------------------------------

def test_block_b_speaker_local_rebind_is_metadata_visible_and_sync_traceable():
    session, world, sid, resolution = runner_strict_bundle()
    eff_resolution = deepcopy(resolution)
    eff_resolution["social"]["npc_id"] = "runner"
    eff_resolution["social"]["npc_name"] = "Tavern Runner"
    gm = {"metadata": {}}

    contract = {
        "primary_speaker_id": "runner",
        "primary_speaker_name": "Tavern Runner",
        "allowed_speaker_ids": ["runner"],
        "continuity_locked": True,
        "speaker_switch_allowed": False,
        "generic_fallback_forbidden": False,
        "offscene_speakers_forbidden": True,
        "debug": {"contract_missing": False},
    }

    def fake_contract(*args, **kwargs):
        return dict(contract)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(sce, "get_speaker_selection_contract", fake_contract)
        repaired, payload = enforce_emitted_speaker_with_contract(
            'Ragged stranger says, "East lanes."',
            gm_output=gm,
            resolution=resolution,
            eff_resolution=eff_resolution,
            world=world,
            scene_id=sid,
        )

    assert repaired == 'Tavern Runner says, "East lanes."'
    assert payload["final_reason_code"] == "continuity_locked_speaker_repair"
    assert payload["repair"]["local_rebind_applied"] is True

    _sync_eff_social_to_resolution(eff_resolution, resolution)
    assert resolution["social"]["npc_id"] == "runner"
    assert resolution["social"]["npc_name"] == "Tavern Runner"

    em = (gm.get("metadata") or {}).get("emission_debug") or {}
    assert em["speaker_contract_enforcement"] is payload
    assert em["speaker_contract_enforcement"]["repair"]["local_rebind_applied"] is True


def test_block_b_strict_social_pronoun_substitution_records_explicit_metadata(monkeypatch):
    out = {
        "player_facing_text": 'She says, "East gate is watched."',
        "tags": [],
        "_final_emission_meta": {"response_type_required": "dialogue"},
    }
    eff_resolution = {
        "kind": "question",
        "social": {"npc_id": "runner", "npc_name": "Tavern Runner"},
    }

    calls = {"ref": 0}

    def fake_ref(text, **kwargs):
        calls["ref"] += 1
        if calls["ref"] == 1:
            return {
                "ok": False,
                "violations": [
                    {
                        "kind": "ambiguous_entity_reference",
                        "token": "She",
                        "candidate_entity_ids": ["runner"],
                        "sentence_text": text,
                    }
                ],
                "checked_entities": ["runner"],
            }
        return {"ok": True, "violations": [], "checked_entities": ["runner"]}

    monkeypatch.setattr(referential_clarity, "validate_player_facing_referential_clarity", fake_ref)
    monkeypatch.setattr(visibility_fallback, "validate_player_facing_referential_clarity", fake_ref)
    monkeypatch.setattr(referential_clarity, "validate_player_facing_first_mentions", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(referential_clarity, "validate_player_facing_visibility", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(referential_clarity, "_active_interlocutor_visible_person_like", lambda *a, **k: True)

    result = visibility_fallback.apply_referential_clarity_enforcement(
        out,
        session={},
        scene={},
        world={},
        scene_id="scene_investigate",
        eff_resolution=eff_resolution,
        active_interlocutor="runner",
        strict_social_active=True,
        strict_social_suppressed_non_social_turn=False,
    )

    meta = result["_final_emission_meta"]
    assert result["player_facing_text"].startswith("The Tavern Runner says")
    assert meta["referential_clarity_local_substitution_attempted"] is True
    assert meta["referential_clarity_local_substitution_applied"] is True
    assert meta["referential_clarity_local_substitution_token"] == "She"
    assert meta["referential_clarity_local_substitution_replacement"] == "The Tavern Runner"
    assert "referential_clarity_local_substitution" in result["tags"]


# === BLOCK E — Strict-social referential substitution (gate routing/fencing only) ===
# Semantic legality: game/narration_visibility.py and tests/test_final_emission_visibility.py.

_BLOCK_E_REFCLARITY_FAIL_VIOLATION = {
    "kind": "ambiguous_entity_reference",
    "token": "She",
    "candidate_entity_ids": ["runner"],
    "sentence_text": 'She says, "East gate is watched."',
}


def _block_e_failing_referential_validation(text: str, **_kwargs):
    return {
        "ok": False,
        "violations": [dict(_BLOCK_E_REFCLARITY_FAIL_VIOLATION, sentence_text=text)],
        "checked_entities": ["runner"],
    }


def _block_e_benign_fallback_selection(*_args, **_kwargs) -> visibility_fallback.VisibilitySelectedFallback:
    return visibility_fallback.VisibilitySelectedFallback(
        text="Block E sealed fallback line.",
        fallback_pool="block_e_test_pool",
        fallback_kind="block_e_test_kind",
        final_emitted_source="block_e_test_source",
        fallback_strategy="standard_safe_fallback",
        fallback_candidate_source="block_e_test_candidate_source",
        composition_meta=visibility_fallback.first_mention_composition_meta(),
    )


def _block_e_seed_strict_social_dialogue_out() -> dict:
    return {
        "player_facing_text": 'She says, "East gate is watched."',
        "tags": [],
        "_final_emission_meta": {"response_type_required": "dialogue"},
    }


def _block_e_eff_resolution() -> dict:
    return {
        "kind": "question",
        "social": {"npc_id": "runner", "npc_name": "Tavern Runner"},
    }


def test_block_e_strict_social_referential_substitution_skipped_on_non_strict_path(monkeypatch):
    """Block E: non-strict callers must not reach the substitution helper, even when validation fails."""
    out = _block_e_seed_strict_social_dialogue_out()
    monkeypatch.setattr(
        referential_clarity, "validate_player_facing_referential_clarity", _block_e_failing_referential_validation
    )
    monkeypatch.setattr(
        visibility_fallback, "validate_player_facing_referential_clarity", _block_e_failing_referential_validation
    )
    monkeypatch.setattr(visibility_fallback, "standard_visibility_safe_fallback", _block_e_benign_fallback_selection)

    def boom(*_a, **_k):
        raise AssertionError(
            "_try_strict_social_local_pronoun_substitution_repair must not run on non-strict-social paths"
        )

    monkeypatch.setattr(referential_clarity, "_try_strict_social_local_pronoun_substitution_repair", boom)

    result = visibility_fallback.apply_referential_clarity_enforcement(
        out,
        session={},
        scene={},
        world={},
        scene_id="scene_investigate",
        eff_resolution=_block_e_eff_resolution(),
        active_interlocutor="runner",
        strict_social_active=False,
        strict_social_suppressed_non_social_turn=False,
    )
    meta = result["_final_emission_meta"]
    assert meta["referential_clarity_local_substitution_attempted"] is False
    assert meta["referential_clarity_local_substitution_applied"] is False
    assert meta["referential_clarity_local_substitution_token"] is None
    assert meta["referential_clarity_local_substitution_replacement"] is None
    assert meta["referential_clarity_fallback_avoided"] is False
    assert meta["referential_clarity_replacement_applied"] is True
    assert "referential_clarity_local_substitution" not in (result.get("tags") or [])
    assert "referential_clarity_enforcement_replaced" in (result.get("tags") or [])


def test_block_e_strict_social_referential_substitution_skipped_on_non_dialogue_response_type(monkeypatch):
    """Block E: even strict-social, a non-dialogue response_type_required must not reach the helper."""
    out = _block_e_seed_strict_social_dialogue_out()
    out["_final_emission_meta"]["response_type_required"] = "action_outcome"
    monkeypatch.setattr(
        referential_clarity, "validate_player_facing_referential_clarity", _block_e_failing_referential_validation
    )
    monkeypatch.setattr(
        visibility_fallback, "validate_player_facing_referential_clarity", _block_e_failing_referential_validation
    )
    monkeypatch.setattr(visibility_fallback, "standard_visibility_safe_fallback", _block_e_benign_fallback_selection)

    def boom(*_a, **_k):
        raise AssertionError(
            "_try_strict_social_local_pronoun_substitution_repair must not run when response_type != dialogue"
        )

    monkeypatch.setattr(referential_clarity, "_try_strict_social_local_pronoun_substitution_repair", boom)

    result = visibility_fallback.apply_referential_clarity_enforcement(
        out,
        session={},
        scene={},
        world={},
        scene_id="scene_investigate",
        eff_resolution=_block_e_eff_resolution(),
        active_interlocutor="runner",
        strict_social_active=True,
        strict_social_suppressed_non_social_turn=False,
    )
    meta = result["_final_emission_meta"]
    assert meta["referential_clarity_local_substitution_attempted"] is False
    assert meta["referential_clarity_local_substitution_applied"] is False
    assert meta["referential_clarity_replacement_applied"] is True


def test_block_e_strict_social_referential_substitution_skipped_when_suppressed_non_social_turn(monkeypatch):
    """Block E: strict-social-suppressed-non-social-turn blocks substitution; sealed fallback runs instead."""
    out = _block_e_seed_strict_social_dialogue_out()
    monkeypatch.setattr(
        referential_clarity, "validate_player_facing_referential_clarity", _block_e_failing_referential_validation
    )
    monkeypatch.setattr(
        visibility_fallback, "validate_player_facing_referential_clarity", _block_e_failing_referential_validation
    )
    monkeypatch.setattr(visibility_fallback, "standard_visibility_safe_fallback", _block_e_benign_fallback_selection)

    def boom(*_a, **_k):
        raise AssertionError(
            "_try_strict_social_local_pronoun_substitution_repair must not run when "
            "strict_social_suppressed_non_social_turn=True"
        )

    monkeypatch.setattr(referential_clarity, "_try_strict_social_local_pronoun_substitution_repair", boom)

    result = visibility_fallback.apply_referential_clarity_enforcement(
        out,
        session={},
        scene={},
        world={},
        scene_id="scene_investigate",
        eff_resolution=_block_e_eff_resolution(),
        active_interlocutor="runner",
        strict_social_active=True,
        strict_social_suppressed_non_social_turn=True,
    )
    meta = result["_final_emission_meta"]
    assert meta["referential_clarity_local_substitution_attempted"] is False
    assert meta["referential_clarity_local_substitution_applied"] is False
    assert meta["referential_clarity_replacement_applied"] is True


def test_block_e_strict_social_referential_substitution_post_validation_rejection_records_failure_reason(monkeypatch):
    """Block E: helper attempts substitution but post-validation fails; metadata records attempted-but-not-applied."""
    out = _block_e_seed_strict_social_dialogue_out()

    calls = {"ref": 0}

    def fake_ref(text, **_kwargs):
        calls["ref"] += 1
        return {
            "ok": False,
            "violations": [dict(_BLOCK_E_REFCLARITY_FAIL_VIOLATION, sentence_text=text)],
            "checked_entities": ["runner"],
        }

    monkeypatch.setattr(referential_clarity, "validate_player_facing_referential_clarity", fake_ref)
    monkeypatch.setattr(visibility_fallback, "validate_player_facing_referential_clarity", fake_ref)
    monkeypatch.setattr(referential_clarity, "validate_player_facing_first_mentions", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(referential_clarity, "validate_player_facing_visibility", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(referential_clarity, "_active_interlocutor_visible_person_like", lambda *a, **k: True)
    monkeypatch.setattr(visibility_fallback, "standard_visibility_safe_fallback", _block_e_benign_fallback_selection)

    result = visibility_fallback.apply_referential_clarity_enforcement(
        out,
        session={},
        scene={},
        world={},
        scene_id="scene_investigate",
        eff_resolution=_block_e_eff_resolution(),
        active_interlocutor="runner",
        strict_social_active=True,
        strict_social_suppressed_non_social_turn=False,
    )
    meta = result["_final_emission_meta"]
    assert meta["referential_clarity_local_substitution_attempted"] is True
    assert meta["referential_clarity_local_substitution_applied"] is False
    assert meta["referential_clarity_fallback_after_failed_local_repair"] is True
    assert meta["referential_clarity_replacement_applied"] is True
    assert calls["ref"] >= 2


def test_block_f_canonical_rewrite_and_narrator_neutral_repair_metadata_visible(monkeypatch):
    """Block F: canonical rewrite and narrator-neutral branches record repair flags on enforcement payload."""
    from copy import deepcopy

    from game.social import SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS

    def _contract_canonical(**overrides):
        c = {
            "primary_speaker_id": "runner",
            "primary_speaker_name": "Tavern Runner",
            "allowed_speaker_ids": ["runner"],
            "continuity_locked": True,
            "speaker_switch_allowed": True,
            "interruption_allowed": True,
            "interruption_requires_scene_event": False,
            "generic_fallback_forbidden": True,
            "forbidden_fallback_labels": list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS),
            "offscene_speakers_forbidden": True,
            "debug": {"contract_missing": False},
        }
        c.update(overrides)
        return c

    session, world, sid, resolution = runner_strict_bundle()

    c_cr = _contract_canonical()
    eff_cr = {
        "kind": "question",
        "social": {"npc_id": "runner", "npc_name": "Tavern Runner", "social_intent_class": "social_exchange"},
        "metadata": {"emission_debug": {"speaker_selection_contract": c_cr}},
    }
    gm_cr = {"metadata": deepcopy(eff_cr["metadata"]), "trace": {}}
    monkeypatch.setattr(sce, "get_speaker_selection_contract", lambda *a, **kw: dict(c_cr))
    out_cr, payload_cr = enforce_emitted_speaker_with_contract(
        "Merchant mutters under his breath without giving a straight answer.",
        gm_output=gm_cr,
        resolution=eff_cr,
        eff_resolution=eff_cr,
        world={},
        scene_id=sid,
    )
    assert "Merchant" not in out_cr
    assert payload_cr["final_reason_code"] == "canonical_speaker_rewrite"
    assert (payload_cr.get("repair") or {}).get("canonical_rewrite_applied") is True

    c_nn = _contract_canonical(
        allowed_speaker_ids=[],
        primary_speaker_id=None,
        primary_speaker_name=None,
        generic_fallback_forbidden=True,
    )
    eff_nn = {
        "kind": "question",
        "social": {"npc_id": "runner", "npc_name": "Tavern Runner", "social_intent_class": "social_exchange"},
        "metadata": {"emission_debug": {"speaker_selection_contract": c_nn}},
    }
    gm_nn = {"metadata": deepcopy(eff_nn["metadata"]), "trace": {}}
    monkeypatch.setattr(sce, "get_speaker_selection_contract", lambda *a, **kw: dict(c_nn))
    out_nn, payload_nn = enforce_emitted_speaker_with_contract(
        'Someone says, "Hello."',
        gm_output=gm_nn,
        resolution=eff_nn,
        eff_resolution=eff_nn,
        world={},
        scene_id=sid,
    )
    assert eff_nn["social"].get("reply_speaker_grounding_neutral_bridge") is True
    assert (payload_nn.get("repair") or {}).get("narrator_neutral_applied") is True
    assert payload_nn["final_reason_code"] == "narrator_neutral_no_allowed_speaker"
    assert len(out_nn or "") > 0


def test_strict_social_gate_repairs_motive_overclaim_and_keeps_speaker(monkeypatch):
    """Strict-social: NA is validate-only; motive overclaim remains visible in meta, not silently rewritten."""
    run_strict_social_motive_overclaim_gate_case(monkeypatch)


def _monoblob_dialogue_quote() -> str:
    core = " ".join(f"w{i}" for i in range(110))
    return f'Tavern Runner says "{core}."'


def _secondary_social_response_structure_contract(
    required_response_type: str,
    **overrides,
):
    # Downstream gate tests consume the shipped shape without re-importing the prompt owner helper.
    contract = {
        "enabled": required_response_type == "dialogue",
        "applies_to_response_type": "dialogue",
        "require_spoken_dialogue_shape": required_response_type == "dialogue",
        "discourage_expository_monologue": required_response_type == "dialogue",
        "require_natural_cadence": required_response_type == "dialogue",
        "allow_brief_action_beats": True,
        "allow_brief_refusal_or_uncertainty": True,
        "max_contiguous_expository_lines": 2 if required_response_type == "dialogue" else None,
        "max_dialogue_paragraphs_before_break": 2 if required_response_type == "dialogue" else None,
        "prefer_single_speaker_turn": required_response_type == "dialogue",
        "forbid_bulleted_or_list_like_dialogue": required_response_type == "dialogue",
        "required_response_type": required_response_type,
        "debug_reason": (
            "response_type_contract_requires_dialogue"
            if required_response_type == "dialogue"
            else f"response_type_not_dialogue:{required_response_type}"
        ),
        "debug_inputs": {},
    }
    contract.update(overrides)
    return contract


def _dialogue_response_policy_with_social_structure(**srs_overrides):
    rtc = response_type_contract("dialogue")
    srs = _secondary_social_response_structure_contract("dialogue")
    srs.update(srs_overrides)
    return {"response_type_contract": rtc, "social_response_structure": srs}


def test_bare_speech_attribution_shell_line_heuristic() -> None:
    assert dialogue_social_plan.is_bare_speech_attribution_shell_line("Tavern Runner says") is True
    assert dialogue_social_plan.is_bare_speech_attribution_shell_line("  Runner replies  ") is True
    assert dialogue_social_plan.is_bare_speech_attribution_shell_line("") is True
    assert dialogue_social_plan.is_bare_speech_attribution_shell_line('Runner mutters, "East."') is False
    assert dialogue_social_plan.is_bare_speech_attribution_shell_line("Rain falls hard on the square.") is False


def test_subtractive_dialogue_strip_on_long_monoblob_yields_shell_not_playable_narration() -> None:
    stripped = dialogue_social_plan.strip_dialogue_from_text(_monoblob_dialogue_quote())
    assert '"' not in stripped
    assert dialogue_social_plan.is_bare_speech_attribution_shell_line(stripped)


def test_strict_social_long_quoted_line_retains_speaker_and_dialogue_payload(monkeypatch) -> None:
    """Invalid dialogue plan must not truncate strict-social output to a bare '… says' tail."""
    session, world, sid, resolution = runner_strict_bundle()
    stub_details = {
        "used_internal_fallback": False,
        "final_emitted_source": "test_stub",
        "rejection_reasons": [],
        "deterministic_attempted": False,
        "deterministic_passed": False,
        "fallback_pool": "none",
        "fallback_kind": "none",
        "route_illegal_intercepted": False,
    }
    bad = _monoblob_dialogue_quote()

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        return bad, dict(stub_details)

    monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response", fake_build)
    monkeypatch.setattr(visibility_fallback, "apply_visibility_enforcement", lambda out, **kwargs: out)
    pol = _dialogue_response_policy_with_social_structure()
    out = _apply_gate(
        {"player_facing_text": bad, "tags": [], "response_policy": pol},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    txt = str(out.get("player_facing_text") or "")
    low = txt.lower()
    assert "tavern runner" in low
    assert '"' in txt
    assert "w0" in low and "w109" in low
    banned = (
        "that is all i can give you",
        "from here, no",
        "no certain answer",
        "truth is still buried",
        "nothing in the scene",
        "scene holds",
        "hard to say",
        "i can only point you",
        "best lead",
    )
    for phrase in banned:
        assert phrase not in low, phrase
