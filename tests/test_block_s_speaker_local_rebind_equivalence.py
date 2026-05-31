"""Block S — local_rebind relocation equivalence harness (ordering + fixtures, no upstream move)."""
from __future__ import annotations

import copy

import pytest

import game.final_emission_gate as feg
from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import read_final_emission_meta_dict
from tests.helpers.speaker_gate_order import (
    assert_phase_subsequence,
    normalized_player_text_equal,
)
from tests.helpers.final_emission_gate_fixtures import runner_strict_bundle

pytestmark = pytest.mark.unit

# Strict-social trunk milestones (must stay aligned with apply_final_emission_gate ordering).
PHASE_BUILD_SOCIAL = "build_final_strict_social_response"
PHASE_RESPONSE_TYPE = "_enforce_response_type_contract"
PHASE_NARRATIVE_AUTHENTICITY = "_apply_narrative_authenticity_layer"
PHASE_TONE_ESCALATION = "_apply_tone_escalation_layer"
PHASE_NARRATIVE_AUTHORITY = "_apply_narrative_authority_layer"
PHASE_SPEAKER = "enforce_emitted_speaker_with_contract"
PHASE_ANTI_RAILROADING = "_apply_anti_railroading_layer"
PHASE_SCENE_STATE_ANCHOR = "_apply_scene_state_anchor_layer"

_CHAIN_SOCIAL_TO_POST_SPEAKER = (
    PHASE_BUILD_SOCIAL,
    PHASE_RESPONSE_TYPE,
    PHASE_NARRATIVE_AUTHENTICITY,
    PHASE_TONE_ESCALATION,
    PHASE_NARRATIVE_AUTHORITY,
    PHASE_SPEAKER,
    PHASE_ANTI_RAILROADING,
    PHASE_SCENE_STATE_ANCHOR,
)


def _locked_runner_contract() -> dict:
    """Continuity-locked contract matching `runner_strict_bundle` NPC id `runner`."""
    return {
        "primary_speaker_id": "runner",
        "primary_speaker_name": "Tavern Runner",
        "allowed_speaker_ids": ["runner"],
        "continuity_locked": True,
        "speaker_switch_allowed": False,
        "speaker_switch_reason": "block_s",
        "generic_fallback_forbidden": False,
        "offscene_speakers_forbidden": True,
        "interruption_allowed": True,
        "interruption_requires_scene_event": False,
        "debug": {"contract_missing": False},
    }


def _stub_strict_social_details() -> dict:
    return {
        "used_internal_fallback": False,
        "final_emitted_source": "block_s_stub",
        "rejection_reasons": [],
        "deterministic_attempted": False,
        "deterministic_passed": False,
        "fallback_pool": "none",
        "fallback_kind": "none",
        "route_illegal_intercepted": False,
    }


def _wrap(orig, order: list[str], phase: str):
    def tracked(*args, **kwargs):
        order.append(phase)
        return orig(*args, **kwargs)

    return tracked


def test_block_s_strict_social_phase_order_wrapped_build(monkeypatch):
    """Same chain when social build is wrapped (avoid overwriting tracked build)."""
    session, world, sid, resolution = runner_strict_bundle()
    order: list[str] = []

    orig_rt = feg._enforce_response_type_contract
    orig_nat = feg._apply_narrative_authenticity_layer
    orig_te = feg._apply_tone_escalation_layer
    orig_na = feg._apply_narrative_authority_layer
    orig_sp = feg.enforce_emitted_speaker_with_contract
    orig_ar = feg._apply_anti_railroading_layer
    orig_ssa = feg._apply_scene_state_anchor_layer

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        order.append(PHASE_BUILD_SOCIAL)
        return 'Tavern Runner says, "Order chain."', _stub_strict_social_details()

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)
    monkeypatch.setattr(feg, "_enforce_response_type_contract", _wrap(orig_rt, order, PHASE_RESPONSE_TYPE))
    monkeypatch.setattr(
        feg, "_apply_narrative_authenticity_layer", _wrap(orig_nat, order, PHASE_NARRATIVE_AUTHENTICITY)
    )
    monkeypatch.setattr(feg, "_apply_tone_escalation_layer", _wrap(orig_te, order, PHASE_TONE_ESCALATION))
    monkeypatch.setattr(
        feg, "_apply_narrative_authority_layer", _wrap(orig_na, order, PHASE_NARRATIVE_AUTHORITY)
    )
    monkeypatch.setattr(feg, "enforce_emitted_speaker_with_contract", _wrap(orig_sp, order, PHASE_SPEAKER))
    monkeypatch.setattr(feg, "_apply_anti_railroading_layer", _wrap(orig_ar, order, PHASE_ANTI_RAILROADING))
    monkeypatch.setattr(feg, "_apply_scene_state_anchor_layer", _wrap(orig_ssa, order, PHASE_SCENE_STATE_ANCHOR))

    apply_final_emission_gate(
        {'player_facing_text': 'Tavern Runner says, "Order chain."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    assert_phase_subsequence(order, _CHAIN_SOCIAL_TO_POST_SPEAKER)


def test_block_s_local_rebind_full_gate_metadata_not_canonical_or_neutral(monkeypatch):
    """Wrong opening label + continuity lock → local_rebind; no canonical_rewrite / narrator_neutral flags."""
    session, world, sid, resolution = runner_strict_bundle()
    c = _locked_runner_contract()
    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: dict(c))

    line = 'Ragged stranger says, "No names, only rumors."'

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        return line, _stub_strict_social_details()

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    out = apply_final_emission_gate(
        {"player_facing_text": line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    text = (out.get("player_facing_text") or "").strip()

    em = (out.get("metadata") or {}).get("emission_debug") or {}
    sp = em.get("speaker_contract_enforcement") or {}
    repair = sp.get("repair") or {}
    assert repair.get("local_rebind_applied") is True
    assert repair.get("canonical_rewrite_applied") is not True
    assert repair.get("narrator_neutral_applied") is not True
    assert (read_final_emission_meta_dict(out) or {}).get("speaker_contract_enforcement_reason") == "continuity_locked_speaker_repair"
    # Opening attribution repair ran (labels canonicalized); downstream Gate layers may still reshape
    # quoted payloads for unrelated boundary reasons — metadata proves the local_rebind branch, not final prose.
    assert "Tavern Runner" in text


def test_block_s_comparison_helper_self_consistent_with_direct_string():
    assert normalized_player_text_equal("  A  \n", "A")
    assert not normalized_player_text_equal("A", "B")


def test_block_s_local_rebind_gate_entry_preserves_full_line_same_as_block_b_direct(monkeypatch):
    """Speaker boundary only: canonical opening label + quoted span unchanged (matches Block B direct test)."""
    session, world, sid, resolution = runner_strict_bundle()
    eff_resolution = copy.deepcopy(resolution)
    eff_resolution["social"]["npc_id"] = "runner"
    eff_resolution["social"]["npc_name"] = "Tavern Runner"
    gm: dict = {"metadata": {}}
    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: dict(_locked_runner_contract()))

    repaired, payload = feg.enforce_emitted_speaker_with_contract(
        'Ragged stranger says, "No names, only rumors."',
        gm_output=gm,
        resolution=resolution,
        eff_resolution=eff_resolution,
        world=world,
        scene_id=sid,
    )
    assert normalized_player_text_equal(repaired, 'Tavern Runner says, "No names, only rumors."')
    assert payload["repair"]["local_rebind_applied"] is True
    assert payload["repair"].get("canonical_rewrite_applied") is not True
    assert payload["repair"].get("narrator_neutral_applied") is not True
