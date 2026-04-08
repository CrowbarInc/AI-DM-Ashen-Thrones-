"""Retry prompt alignment with anti-railroading policy (prompt_context + final_emission_gate)."""
from __future__ import annotations

import pytest

from game.anti_railroading import build_anti_railroading_contract, validate_anti_railroading
from game.final_emission_gate import apply_final_emission_gate
from game.gm import build_retry_prompt_for_failure

pytestmark = pytest.mark.unit


def _minimal_ar_contract(**overrides: object) -> dict:
    c = build_anti_railroading_contract(resolution=None, player_text="Test.")
    assert isinstance(c, dict)
    return {**c, **overrides}  # type: ignore[misc]


def test_retry_prompt_always_includes_agency_and_forbidden_patterns() -> None:
    p = build_retry_prompt_for_failure(
        {"failure_class": "scene_stall"},
        response_policy=None,
        gm_output=None,
    ).lower()
    assert "retry agency (anti-railroading)" in p
    assert "without choosing for the player" in p
    assert "auto-travel" in p
    assert "the story wants" in p


def test_retry_prompt_includes_contract_tail_when_flags_present() -> None:
    arc = _minimal_ar_contract(
        allow_directional_language_from_resolved_transition=True,
        allow_exclusivity_from_authoritative_resolution=True,
        allow_commitment_language_when_player_explicitly_committed=True,
        surfaced_lead_ids=["lead_a", "lead_b"],
    )
    gm = {"anti_railroading_contract": arc}
    p = build_retry_prompt_for_failure(
        {"failure_class": "followup_soft_repetition", "followup_context": {}},
        response_policy=None,
        gm_output=gm,
    ).lower()
    assert "contract tail:" in p
    assert "resolved transition" in p or "authoritative state" in p
    assert "multiple leads are in play" in p


def test_scene_stall_retry_stresses_openings_not_pc_commitment() -> None:
    p = build_retry_prompt_for_failure(
        {"failure_class": "scene_stall"},
        response_policy=None,
        gm_output=None,
    ).lower()
    assert "scene stall" in p or "low progress" in p
    assert "without choosing for the player" in p
    assert "auto-commit" in p or "auto-commitment" in p


def test_topic_pressure_retry_rejects_forced_pathing_despite_urgency() -> None:
    p = build_retry_prompt_for_failure(
        {
            "failure_class": "topic_pressure_escalation",
            "topic_context": {"topic_key": "t", "repeat_count": 2},
        },
        response_policy=None,
        gm_output=None,
    ).lower()
    assert "urgency sharpens salience" in p
    assert "forced pathing" in p
    assert "do not narrate the pc's move" in p or "pc's move" in p


def test_exemplar_retry_style_passes_validator_and_gate_without_ar_repair() -> None:
    """Integration-style: prose shaped like an ideal retry should pass anti-RR on first pass."""
    arc = _minimal_ar_contract()
    samples = [
        (
            "The clerk's stamp comes down; the queue compresses—east weigh-house before sundown is one handle, "
            "the night ward another, and a third faction watcher tracks who chooses which line."
        ),
        (
            "Marta refuses the ledger outright, but her eyes flick toward the chapel steps and the river stairs—"
            "two different openings, each with its own cost if you press."
        ),
        (
            "The eastern gate is sealed by decree; the river post and the old break in the wall remain contested, "
            "and the watch sergeant is already counting heartbeats."
        ),
    ]
    for text in samples:
        v = validate_anti_railroading(text, arc)
        assert v.get("passed") is True, (text, v)
        out = apply_final_emission_gate(
            {"player_facing_text": text, "tags": ["scene_momentum:new_information"], "anti_railroading_contract": arc},
            resolution={"kind": "question", "prompt": "Where?", "social": {"social_intent_class": "social_exchange"}},
            session={},
            scene_id="gate",
            world={},
        )
        meta = out.get("_final_emission_meta") or {}
        assert meta.get("anti_railroading_repaired") is not True
        assert meta.get("anti_railroading_ok") is not False


def test_retry_prompt_respects_response_policy_anti_railroading_field() -> None:
    arc = _minimal_ar_contract(surfaced_lead_ids=["x", "y", "z"])
    pol = {"anti_railroading": arc}
    p = build_retry_prompt_for_failure({"failure_class": "npc_contract_failure", "missing": []}, response_policy=pol, gm_output=None).lower()
    assert "multiple leads are in play" in p
