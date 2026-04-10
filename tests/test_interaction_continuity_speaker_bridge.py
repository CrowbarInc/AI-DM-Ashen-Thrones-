"""Speaker-binding → interaction continuity bridge (Objective #14 hardening)."""
from __future__ import annotations

import pytest

from game.final_emission_gate import (
    _apply_interaction_continuity_emission_step,
    _interaction_continuity_should_fail_from_speaker_binding,
    _looks_like_malformed_explicit_speaker_attribution,
)
from game.interaction_continuity import repair_interaction_continuity, validate_interaction_continuity

pytestmark = pytest.mark.unit

_LIVE_MALFORMED = 'South road." Tavern Runner nods once. "Old Millstone.'


def _ssc_locked_tavern_runner() -> dict:
    return {
        "continuity_locked": True,
        "primary_speaker_id": "tavern_runner",
        "primary_speaker_name": "Tavern Runner",
        "allowed_speaker_ids": ["tavern_runner"],
        "speaker_switch_allowed": False,
    }


def _strong_ic_with_ssc() -> dict:
    return {
        "enabled": True,
        "continuity_strength": "strong",
        "anchored_interlocutor_id": "tavern_runner",
        "preserve_conversational_thread": True,
        "speaker_selection_contract": _ssc_locked_tavern_runner(),
    }


def _enforcement_speaker_ok() -> dict:
    return {
        "validation": {
            "ok": True,
            "reason_code": "speaker_contract_match",
            "canonical_speaker_name": "Tavern Runner",
            "details": {"signature": {"speaker_label": "Tavern Runner", "is_explicitly_attributed": True}},
        },
    }


def _enforcement_binding_mismatch_malformed() -> dict:
    return {
        "validation": {
            "ok": False,
            "reason_code": "speaker_binding_mismatch",
            "canonical_speaker_name": "Tavern Runner",
            "details": {
                "signature": {
                    "speaker_label": 'South road." Tavern Runner',
                    "speaker_name": 'South road." Tavern Runner',
                    "is_explicitly_attributed": True,
                }
            },
        },
        "post_validation": {
            "ok": False,
            "reason_code": "speaker_binding_mismatch",
            "canonical_speaker_name": "Tavern Runner",
            "details": {
                "signature": {
                    "speaker_label": 'South road." Tavern Runner',
                    "speaker_name": 'South road." Tavern Runner',
                    "is_explicitly_attributed": True,
                }
            },
        },
    }


def test_A_bridge_adds_synthetic_violation_strong_continuity():
    ic = _strong_ic_with_ssc()
    base = validate_interaction_continuity(_LIVE_MALFORMED, interaction_continuity_contract=ic)
    assert base["ok"] is True

    br = _interaction_continuity_should_fail_from_speaker_binding(
        interaction_continuity_contract=ic,
        interaction_continuity_validation=base,
        speaker_contract_enforcement=_enforcement_binding_mismatch_malformed(),
        text=_LIVE_MALFORMED,
    )
    assert br["should_fail"] is True
    assert br["synthetic_violation"] == "malformed_speaker_attribution_under_continuity"
    assert br["debug"].get("malformed_attribution_detected") is True


def test_B_safe_salvage_repair_canonical_speaker():
    ic = _strong_ic_with_ssc()
    v = validate_interaction_continuity(_LIVE_MALFORMED, interaction_continuity_contract=ic)
    assert v["ok"] is True
    v["ok"] = False
    v["violations"] = list(v["violations"]) + ["malformed_speaker_attribution_under_continuity"]
    v.setdefault("debug", {})["speaker_binding_reason_code"] = "speaker_binding_mismatch"

    r = repair_interaction_continuity(_LIVE_MALFORMED, validation=v, interaction_continuity_contract=ic)
    assert r["applied"] is True
    assert r["repair_type"] == "repair_malformed_speaker_attribution"
    assert "Tavern Runner" in r["repaired_text"]
    assert "Old Millstone" in r["repaired_text"]
    assert "South road" in r["repaired_text"]
    assert "malformed explicit attribution salvaged" in " ".join(r["strategy_notes"]).lower()


def test_C_unrecoverable_no_repair_strong_enforcement_via_gate():
    ic = _strong_ic_with_ssc()
    unrecoverable = 'South road." Stranger waits. "Old Millstone.'
    v_min = {
        "ok": False,
        "enabled": True,
        "continuity_strength": "strong",
        "violations": ["malformed_speaker_attribution_under_continuity"],
        "warnings": [],
        "facts": {},
        "debug": {"speaker_binding_reason_code": "speaker_binding_mismatch"},
    }
    r = repair_interaction_continuity(unrecoverable, validation=v_min, interaction_continuity_contract=ic)
    assert r["applied"] is False

    out = {
        "player_facing_text": unrecoverable,
        "metadata": {"emission_debug": {"speaker_contract_enforcement": _enforcement_binding_mismatch_malformed()}},
        "response_policy": {"interaction_continuity": ic},
    }
    resolution = {"metadata": {"emission_debug": {}}}
    _apply_interaction_continuity_emission_step(
        out,
        text=unrecoverable,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
        validate_only=False,
        strict_social_path=False,
    )
    em = out["metadata"]["emission_debug"]
    assert em.get("interaction_continuity_enforced") is True
    assert em.get("interaction_continuity_repair", {}).get("applied") is not True


def test_D_clean_dialogue_no_bridge():
    ic = _strong_ic_with_ssc()
    clean = '"The south road is clear," Tavern Runner says.'
    assert (
        _interaction_continuity_should_fail_from_speaker_binding(
            interaction_continuity_contract=ic,
            interaction_continuity_validation=validate_interaction_continuity(clean, interaction_continuity_contract=ic),
            speaker_contract_enforcement=_enforcement_speaker_ok(),
            text=clean,
        )["should_fail"]
        is False
    )


def test_E_soft_continuity_bridge_inert():
    ic = {
        "enabled": True,
        "continuity_strength": "soft",
        "anchored_interlocutor_id": "",
        "speaker_selection_contract": _ssc_locked_tavern_runner(),
    }
    br = _interaction_continuity_should_fail_from_speaker_binding(
        interaction_continuity_contract=ic,
        interaction_continuity_validation=validate_interaction_continuity(_LIVE_MALFORMED, interaction_continuity_contract=ic),
        speaker_contract_enforcement=_enforcement_binding_mismatch_malformed(),
        text=_LIVE_MALFORMED,
    )
    assert br["should_fail"] is False


def test_F_regression_live_malformed_family_not_accepted_without_repair_or_enforcement():
    ic = _strong_ic_with_ssc()
    v_plain = validate_interaction_continuity(_LIVE_MALFORMED, interaction_continuity_contract=ic)
    assert v_plain["ok"] is True

    out = {
        "player_facing_text": _LIVE_MALFORMED,
        "metadata": {"emission_debug": {"speaker_contract_enforcement": _enforcement_binding_mismatch_malformed()}},
        "response_policy": {"interaction_continuity": ic},
    }
    resolution = {"metadata": {"emission_debug": {}}}
    _apply_interaction_continuity_emission_step(
        out,
        text=_LIVE_MALFORMED,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
        validate_only=False,
        strict_social_path=False,
    )
    em = out["metadata"]["emission_debug"]
    icv = em.get("interaction_continuity_validation") or {}
    assert icv.get("ok") is True
    rep = em.get("interaction_continuity_repair") or {}
    assert rep.get("applied") is True
    assert rep.get("repair_type") == "repair_malformed_speaker_attribution"
    assert "malformed_speaker_attribution_under_continuity" in (rep.get("violations") or [])
    assert em.get("interaction_continuity_enforced") is not True
    assert em.get("interaction_continuity_speaker_binding_bridge", {}).get("applied") is True


def test_malformed_heuristic_detects_live_shape():
    assert _looks_like_malformed_explicit_speaker_attribution(
        _LIVE_MALFORMED,
        _enforcement_binding_mismatch_malformed(),
    )


def test_bridge_metadata_recorded_when_firing():
    ic = _strong_ic_with_ssc()
    out = {
        "player_facing_text": _LIVE_MALFORMED,
        "metadata": {"emission_debug": {"speaker_contract_enforcement": _enforcement_binding_mismatch_malformed()}},
        "response_policy": {"interaction_continuity": ic},
    }
    resolution = {"metadata": {"emission_debug": {}}}
    _apply_interaction_continuity_emission_step(
        out,
        text=_LIVE_MALFORMED,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
        validate_only=False,
        strict_social_path=False,
    )
    bridge = (out["metadata"].get("emission_debug") or {}).get("interaction_continuity_speaker_binding_bridge")
    assert isinstance(bridge, dict)
    assert bridge.get("applied") is True
    assert bridge.get("synthetic_violation") == "malformed_speaker_attribution_under_continuity"
    assert bridge.get("malformed_attribution_detected") is True
