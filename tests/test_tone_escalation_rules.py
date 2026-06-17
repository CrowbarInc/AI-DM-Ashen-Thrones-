"""Regression tests for tone escalation contract, validator, final gate, and pregate audit."""
from __future__ import annotations

import pytest

import game.final_emission_non_strict_stack as non_strict_stack
import game.final_emission_terminal_pipeline as terminal_pipeline
from game.final_emission_meta import default_response_type_debug
from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import read_final_emission_meta_dict
from game.final_emission_tone_escalation import (
    apply_tone_escalation_layer,
    flag_non_hostile_escalation_from_writer_pregate,
)
from game.tone_escalation import build_tone_escalation_contract, validate_tone_escalation
from tests.helpers.emission_smoke_assertions import apply_final_emission_gate_consumer, response_type_contract

pytestmark = pytest.mark.unit


def _shipped_tone_contract(**overrides: object) -> dict:
    """Minimal contract shape accepted as shipped by the final gate (includes debug_inputs)."""
    base: dict = {
        "enabled": True,
        "scene_id": "test_scene",
        "active_speaker_id": None,
        "base_tone": "neutral",
        "max_allowed_tone": "guarded",
        "allow_guarded_refusal": True,
        "allow_verbal_pressure": False,
        "allow_explicit_threat": False,
        "allow_physical_hostility": False,
        "allow_combat_initiation": False,
        "justification_flags": {},
        "justification_reasons": [],
        "preferred_deescalations": [],
        "debug_reason": "test",
        "debug_inputs": {"scene_id": "test_scene"},
        "debug_flags": {},
    }
    base.update(overrides)  # type: ignore[arg-type]
    return base


def test_neutral_contract_blocks_explicit_threat_in_narration() -> None:
    ctr = _shipped_tone_contract()
    v = validate_tone_escalation("The guard leans in. One more word and you will regret it.", contract=ctr)
    assert v["checked"] is True
    assert v["ok"] is False
    assert "explicit_threat_not_allowed" in v["failure_reasons"]


def test_neutral_contract_blocks_physical_hostility() -> None:
    ctr = _shipped_tone_contract(allow_verbal_pressure=True, max_allowed_tone="tense")
    v = validate_tone_escalation("He shoves you against the wall.", contract=ctr)
    assert v["checked"] is True
    assert v["ok"] is False
    assert "physical_hostility_not_allowed" in v["failure_reasons"]


def test_guarded_tension_refusal_passes_neutral_ceiling() -> None:
    ctr = _shipped_tone_contract()
    v = validate_tone_escalation(
        'The clerk refuses. "Not here. Not for you."',
        contract=ctr,
    )
    assert v["checked"] is True
    assert v["ok"] is True


def test_verbal_pressure_passes_when_allowed() -> None:
    ctr = _shipped_tone_contract(
        max_allowed_tone="tense",
        allow_verbal_pressure=True,
    )
    v = validate_tone_escalation("She gives you a cold stare. Drop it.", contract=ctr)
    assert v["checked"] is True
    assert v["ok"] is True


def test_explicit_threat_passes_when_contract_allows() -> None:
    ctr = _shipped_tone_contract(
        max_allowed_tone="threatening",
        allow_verbal_pressure=True,
        allow_explicit_threat=True,
    )
    v = validate_tone_escalation("Try that again and you will be sorry.", contract=ctr)
    assert v["checked"] is True
    assert v["ok"] is True


def test_topic_pressure_contract_alone_does_not_unlock_threat_without_flags() -> None:
    """Persistence / risky resolution kind must not widen the ceiling without justification flags."""
    resolution = {"kind": "social_probe", "prompt": "Tell me now."}
    ctr = build_tone_escalation_contract(
        session={"topic_pressure": {"count": 9}},
        world={},
        scene_id="tavern",
        resolution=resolution,
        speaker_selection_contract=None,
        scene_state_anchor_contract=None,
        narration_visibility={"visible_entity_roles": {}, "visible_fact_strings": []},
        recent_log=(),
    )
    assert ctr.get("enabled") is True
    assert ctr.get("allow_explicit_threat") is False


def test_final_gate_downgrades_unsupported_threat() -> None:
    ctr = _shipped_tone_contract()
    gm = {
        "player_facing_text": "Without warning he says you will regret crossing him.",
        "tags": [],
        "response_policy": {"tone_escalation": ctr},
    }
    out, meta = apply_final_emission_gate_consumer(
        gm,
        resolution={"kind": "observe", "prompt": "I watch the crowd."},
        session={},
        scene_id="market",
        world={},
    )
    text = str(out.get("player_facing_text") or "").lower()
    assert meta.get("tone_escalation_repaired") is True or "regret" not in text


def test_final_gate_downgrades_unsupported_physical() -> None:
    ctr = _shipped_tone_contract(allow_verbal_pressure=True, max_allowed_tone="tense")
    gm = {
        "player_facing_text": "She grabs your collar and shoves you backward.",
        "tags": [],
        "response_policy": {"tone_escalation": ctr},
    }
    out, meta = apply_final_emission_gate_consumer(
        gm,
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="lane",
        world={},
    )
    text = str(out.get("player_facing_text") or "").lower()
    assert "shoves" not in text or meta.get("tone_escalation_repaired") is True


def test_final_gate_repairs_forced_drama_to_grounded_friction() -> None:
    ctr = _shipped_tone_contract()
    gm = {
        "player_facing_text": "Out of nowhere, chaos erupts through the hall.",
        "tags": [],
        "response_policy": {"tone_escalation": ctr},
    }
    out, meta = apply_final_emission_gate_consumer(
        gm,
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="hall",
        world={},
    )
    text = str(out.get("player_facing_text") or "").lower()
    assert "chaos erupts" not in text
    assert meta.get("tone_escalation_violation_before_repair") is True


def test_tone_layer_preserves_justified_explicit_threat() -> None:
    """Narrow slice: when the shipped contract allows threats, validator passes without repair."""
    ctr = _shipped_tone_contract(
        max_allowed_tone="threatening",
        allow_verbal_pressure=True,
        allow_explicit_threat=True,
    )
    original = "The sergeant leans in. One more step and you will be sorry."
    text, meta, reasons = apply_tone_escalation_layer(
        original,
        gm_output={"response_policy": {"tone_escalation": ctr}},
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="gate",
        response_type_debug=default_response_type_debug(None, None),
    )
    assert not reasons
    assert meta.get("tone_escalation_repaired") is not True
    assert meta.get("tone_escalation_ok") is True
    assert "sorry" in text.lower()


def test_pregate_audit_flags_writer_overshoot() -> None:
    """Legacy audit: overshoot vs strict fallback contract sets non_hostile_escalation_blocked."""
    dbg = default_response_type_debug(None, None)
    flag_non_hostile_escalation_from_writer_pregate(
        "He says you will regret this.",
        gm_output={},
        resolution={"kind": "observe", "prompt": "I watch."},
        session={},
        response_type_debug=dbg,
    )
    assert dbg.get("non_hostile_escalation_blocked") is True


def test_apply_final_emission_gate_runs_tone_escalation_before_narrative_authority(monkeypatch: pytest.MonkeyPatch) -> None:
    order: list[str] = []
    orig_te = non_strict_stack.apply_tone_escalation_layer
    orig_na = non_strict_stack.apply_narrative_authority_layer

    def te(*args, **kwargs):
        order.append("tone")
        return orig_te(*args, **kwargs)

    def na(*args, **kwargs):
        order.append("narrative_authority")
        return orig_na(*args, **kwargs)

    monkeypatch.setattr(non_strict_stack, "apply_tone_escalation_layer", te)
    monkeypatch.setattr(non_strict_stack, "apply_narrative_authority_layer", na)

    ctr = _shipped_tone_contract()
    apply_final_emission_gate(
        {
            "player_facing_text": "Rain drums on the roof.",
            "tags": [],
            "response_policy": {"tone_escalation": ctr},
        },
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="hut",
        world={},
    )
    assert order.index("tone") < order.index("narrative_authority")


# --- Gate-layer tone escalation ownership ---


def _secondary_social_response_structure_contract(
    required_response_type: str,
    **overrides,
):
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


def test_final_emission_gate_marks_non_hostile_escalation_blocked_on_tone_writer_overshoot() -> None:
    """When pre-repair text violates shipped tone policy, legacy meta records the overshoot."""
    ctr = {
        "enabled": True,
        "scene_id": "hall",
        "base_tone": "neutral",
        "max_allowed_tone": "guarded",
        "allow_guarded_refusal": True,
        "allow_verbal_pressure": False,
        "allow_explicit_threat": False,
        "allow_physical_hostility": False,
        "allow_combat_initiation": False,
        "justification_flags": {},
        "justification_reasons": [],
        "debug_inputs": {"scene_id": "hall"},
        "debug_flags": {},
    }
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Out of nowhere, chaos erupts through the hall.",
            "tags": [],
            "response_policy": {"tone_escalation": ctr},
        },
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="hall",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("non_hostile_escalation_blocked") is True
    assert meta.get("tone_escalation_violation_before_repair") is True


def test_gate_context_separation_tone_escalation_with_city_pressure_fails(monkeypatch):
    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "Good morning. A loaf, please."
    cs = build_context_separation_contract(
        player_text=pt,
        resolution={"kind": "barter"},
        tone_escalation_contract={"allow_verbal_pressure": False, "allow_explicit_threat": False},
    )
    text = (
        "The city is on edge tonight, so back off and drop it—this is not the time for questions."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("context_separation_failed") is True
    assert "ambient_pressure_forced_tone_shift" in (meta.get("context_separation_failure_reasons") or [])


def test_social_response_structure_coexists_with_tone_escalation_layer(monkeypatch):
    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", lambda out, **kwargs: out)
    order: list[str] = []
    orig_srs = non_strict_stack._apply_social_response_structure_layer
    orig_te = non_strict_stack.apply_tone_escalation_layer

    def srs(*args, **kwargs):
        order.append("social_response_structure")
        return orig_srs(*args, **kwargs)

    def te(*args, **kwargs):
        order.append("tone_escalation")
        return orig_te(*args, **kwargs)

    monkeypatch.setattr(non_strict_stack, "_apply_social_response_structure_layer", srs)
    monkeypatch.setattr(non_strict_stack, "apply_tone_escalation_layer", te)
    pol = _dialogue_response_policy_with_social_structure()
    out = apply_final_emission_gate(
        {
            "player_facing_text": 'Clerk says "East ledger is closed until dawn."',
            "tags": [],
            "response_policy": pol,
        },
        resolution={"kind": "question", "prompt": "When does the east ledger open?"},
        session=None,
        scene_id="hall",
        world={},
    )
    assert order.index("social_response_structure") < order.index("tone_escalation")
    meta = read_final_emission_meta_dict(out) or {}
    assert "tone_escalation_checked" in meta
    assert meta.get("candidate_validation_passed") is True


def test_bj31_repair_tone_escalation_narrow_softens_explicit_threat() -> None:
    from game.final_emission_tone_escalation import repair_tone_escalation_narrow

    ctr = _shipped_tone_contract()
    validation = validate_tone_escalation(
        "One more word and you will regret it.",
        contract=ctr,
    )
    repaired, mode = repair_tone_escalation_narrow(
        "One more word and you will regret it.",
        contract=ctr,
        validation=validation,
    )
    assert repaired is not None
    assert mode
    assert "regret" not in str(repaired).lower()
