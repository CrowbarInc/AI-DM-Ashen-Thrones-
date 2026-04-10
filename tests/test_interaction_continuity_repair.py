"""Interaction continuity repair + gate enforcement (Objective #14 Block #3)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from game.final_emission_gate import (
    _apply_interaction_continuity_emission_step,
    apply_final_emission_gate,
)
from game.interaction_continuity import repair_interaction_continuity, validate_interaction_continuity

pytestmark = pytest.mark.unit


def _strong_contract(*, anchor: str = "npc_melka") -> dict:
    return {
        "enabled": True,
        "continuity_strength": "strong",
        "anchored_interlocutor_id": anchor,
        "preserve_conversational_thread": True,
        "speaker_selection_contract": None,
    }


def _soft_contract() -> dict:
    return {
        "enabled": True,
        "continuity_strength": "soft",
        "anchored_interlocutor_id": "",
        "preserve_conversational_thread": True,
        "speaker_selection_contract": None,
    }


def test_repair_strips_crowd_interruption_after_labeled_anchor():
    c = _strong_contract()
    # Avoid phrases that count as explicit handoff cues (e.g. "someone behind you").
    text = 'Guard: "Stay where you are."\nA sharp yell from the alley: "Run!"'
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert v["ok"] is False
    r = repair_interaction_continuity(text, validation=v, interaction_continuity_contract=c)
    assert r["applied"] is True
    assert r["repair_type"] == "strip_uncued_interruption"
    assert "alley" not in r["repaired_text"]
    assert "Guard:" in r["repaired_text"]


def test_repair_narration_to_dialogue_strong_short_line():
    c = _strong_contract()
    text = "You can't go there."
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert "dialogue_absent_under_continuity" in v["violations"]
    r = repair_interaction_continuity(text, validation=v, interaction_continuity_contract=c)
    assert r["applied"] is True
    assert r["repair_type"] == "narration_to_dialogue"
    assert "says" in r["repaired_text"].lower()
    assert '"' in r["repaired_text"] or "\u201c" in r["repaired_text"]


def test_gate_strong_narration_repaired_no_fallback():
    ic = _strong_contract()
    gm = {
        "player_facing_text": "You can't go there.",
        "tags": [],
        "metadata": {},
        "response_policy": {"interaction_continuity": ic},
    }
    resolution = {"metadata": {"emission_debug": {}, "player_input": "Can I pass?"}}
    with patch("game.final_emission_gate._apply_visibility_enforcement", lambda out, **kwargs: out):
        out = apply_final_emission_gate(
            gm,
            resolution=resolution,
            session=None,
            scene_id="test_scene",
            scene={},
            world={},
        )
    em = out["metadata"]["emission_debug"]
    assert em.get("interaction_continuity_repair", {}).get("applied") is True
    assert em["interaction_continuity_repair"]["repair_type"] == "narration_to_dialogue"
    assert em.get("interaction_continuity_enforced") is not True
    icv = em.get("interaction_continuity_validation") or {}
    assert icv.get("ok") is True
    assert "says" in (out.get("player_facing_text") or "").lower()


def test_gate_strong_complex_failure_triggers_fallback_and_enforced_flag():
    ic = _strong_contract()
    long_narration = (
        "The regional economy depends on tolls, wayposts, and seasonal trade convoys moving "
        "between jurisdictions, a fact recorded in dry ledgers that never mention your question."
    )
    gm = {
        "player_facing_text": long_narration,
        "tags": [],
        "metadata": {},
        "response_policy": {"interaction_continuity": ic},
    }
    resolution = {"metadata": {"emission_debug": {}, "player_input": "What do you know?"}}
    out = apply_final_emission_gate(
        gm,
        resolution=resolution,
        session=None,
        scene_id="test_scene",
        scene={},
        world={},
    )
    em = out["metadata"]["emission_debug"]
    assert em.get("interaction_continuity_repair") is None or em.get("interaction_continuity_repair", {}).get(
        "applied"
    ) is not True
    assert em.get("interaction_continuity_enforced") is True
    assert "final_emission_gate_replaced" in out.get("tags", [])


def test_soft_continuity_does_not_trigger_fallback_for_violation():
    ic = _soft_contract()
    text = (
        "The regional economy depends on tolls, wayposts, and seasonal trade convoys moving "
        "between jurisdictions, a fact recorded in dry ledgers that never mention your question."
    )
    gm = {
        "player_facing_text": text,
        "tags": [],
        "metadata": {},
        "response_policy": {
            "interaction_continuity": ic,
            "response_type_contract": {"required_response_type": "dialogue"},
        },
    }
    resolution = {"metadata": {"emission_debug": {}, "player_input": "What news?"}}
    out = apply_final_emission_gate(
        gm,
        resolution=resolution,
        session=None,
        scene_id="test_scene",
        scene={},
        world={},
    )
    em = out["metadata"]["emission_debug"]
    icv = em.get("interaction_continuity_validation") or {}
    assert icv.get("ok") is False
    assert em.get("interaction_continuity_enforced") is not True


def test_repair_metadata_includes_violations_applied_and_type():
    c = _strong_contract()
    text = 'Guard: "Halt."\nMerchant: "Wait—he is with me."'
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    r = repair_interaction_continuity(text, validation=v, interaction_continuity_contract=c)
    assert r["applied"] is True
    assert r["repair_type"] == "strip_uncued_interruption"
    out = {
        "player_facing_text": text,
        "metadata": {},
        "response_policy": {"interaction_continuity": c},
    }
    resolution = {"metadata": {"emission_debug": {}}}
    _apply_interaction_continuity_emission_step(
        out,
        text=text,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
        validate_only=False,
        strict_social_path=False,
    )
    em = out["metadata"]["emission_debug"]
    rep = em.get("interaction_continuity_repair") or {}
    assert rep.get("applied") is True
    assert rep.get("repair_type") == "strip_uncued_interruption"
    assert isinstance(rep.get("violations"), list)
    assert rep["violations"]
    assert isinstance(rep.get("strategy_notes"), list)
    assert rep["strategy_notes"]


def test_gate_ordering_response_type_then_continuity_then_fallback():
    import game.final_emission_gate as feg

    calls: list[str] = []
    _real_rtc = feg._enforce_response_type_contract
    _real_repair = feg.repair_interaction_continuity
    _real_fb = feg._global_narrative_fallback_stock_line

    def rtc_wrapper(*a, **kw):
        calls.append("response_type")
        return _real_rtc(*a, **kw)

    def repair_wrapper(*a, **kw):
        calls.append("continuity_repair")
        return _real_repair(*a, **kw)

    def fb_wrapper(*a, **kw):
        calls.append("fallback")
        return _real_fb(*a, **kw)

    ic = _strong_contract()
    long_narration = (
        "The regional economy depends on tolls, wayposts, and seasonal trade convoys moving "
        "between jurisdictions, a fact recorded in dry ledgers that never mention your question."
    )
    gm = {
        "player_facing_text": long_narration,
        "tags": [],
        "metadata": {},
        "response_policy": {"interaction_continuity": ic},
    }
    resolution = {"metadata": {"emission_debug": {}, "player_input": "What?"}}
    with (
        patch.object(feg, "_enforce_response_type_contract", side_effect=rtc_wrapper),
        patch.object(feg, "repair_interaction_continuity", side_effect=repair_wrapper),
        patch.object(feg, "_global_narrative_fallback_stock_line", side_effect=fb_wrapper),
    ):
        apply_final_emission_gate(
            gm,
            resolution=resolution,
            session=None,
            scene_id="test_scene",
            scene={},
            world={},
        )
    rt_i = calls.index("response_type")
    cr_i = calls.index("continuity_repair")
    fb_i = calls.index("fallback")
    assert rt_i < cr_i < fb_i
