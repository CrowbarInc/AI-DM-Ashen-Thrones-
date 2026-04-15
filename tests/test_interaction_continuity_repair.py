"""Downstream continuity-repair consumer coverage.

This suite validates how continuity-repair effects appear in emitted outputs
after final-emission gate orchestration.

It does NOT own:

* gate ordering
* continuity emission step semantics
* repair derivation logic

These are owned by:
tests/test_final_emission_gate.py
"""
from __future__ import annotations

import pytest

from game.final_emission_gate import apply_final_emission_gate
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


def test_output_exhibits_stripped_uncued_interruption_with_labeled_anchor():
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


def test_output_exhibits_continuity_repaired_structure_narration_to_dialogue():
    c = _strong_contract()
    text = "You can't go there."
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert "dialogue_absent_under_continuity" in v["violations"]
    r = repair_interaction_continuity(text, validation=v, interaction_continuity_contract=c)
    assert r["applied"] is True
    assert r["repair_type"] == "narration_to_dialogue"
    assert "says" in r["repaired_text"].lower()
    assert '"' in r["repaired_text"] or "\u201c" in r["repaired_text"]


def test_emitted_output_exhibits_continuity_repaired_structure_strong_short_narration():
    ic = _strong_contract()
    gm = {
        "player_facing_text": "You can't go there.",
        "tags": [],
        "metadata": {},
        "response_policy": {"interaction_continuity": ic},
    }
    resolution = {"metadata": {"emission_debug": {}, "player_input": "Can I pass?"}}
    out = apply_final_emission_gate(
        gm,
        resolution=resolution,
        session=None,
        scene_id="test_scene",
        scene={},
        world={},
    )
    em = out["metadata"]["emission_debug"]
    rep = em.get("interaction_continuity_repair") or {}
    assert rep.get("applied") is True
    assert rep.get("repair_type") == "narration_to_dialogue"
    assert "dialogue_absent_under_continuity" in (rep.get("violations") or [])
    assert isinstance(rep.get("strategy_notes"), list) and rep["strategy_notes"]
    assert em.get("interaction_continuity_enforced") is not True


def test_emitted_output_preserves_continuity_constraints_under_strong_complex_narration():
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


def test_emitted_output_preserves_continuity_constraints_soft_strength_on_violation():
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


def test_emitted_output_surfaces_stripped_interruption_repair_metadata():
    c = _strong_contract()
    text = 'Guard: "Halt."\nMerchant: "Wait—he is with me."'
    gm = {
        "player_facing_text": text,
        "metadata": {},
        "response_policy": {"interaction_continuity": c},
    }
    resolution = {"metadata": {"emission_debug": {}}, "player_input": "Who called out?"}
    out = apply_final_emission_gate(
        gm,
        resolution=resolution,
        session=None,
        scene_id="test_scene",
        scene={},
        world={},
    )
    rep = out["metadata"]["emission_debug"].get("interaction_continuity_repair") or {}
    assert rep.get("applied") is True
    assert rep.get("repair_type") == "strip_uncued_interruption"
    assert isinstance(rep.get("violations"), list)
    assert rep["violations"]
    assert isinstance(rep.get("strategy_notes"), list)
    assert rep["strategy_notes"]
    assert out["metadata"]["emission_debug"].get("interaction_continuity_enforced") is not True
