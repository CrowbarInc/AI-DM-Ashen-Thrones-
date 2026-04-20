"""Retry prompt alignment with tone escalation policy (no invalid hostility before final gate)."""
from __future__ import annotations

from game.final_emission_meta import read_final_emission_meta_dict

import pytest

from game.final_emission_gate import apply_final_emission_gate
from game.gm import _retry_allows_hostile_escalation, build_retry_prompt_for_failure
from game.tone_escalation import validate_tone_escalation

pytestmark = pytest.mark.unit


def _shipped_tone_policy(**overrides: object) -> dict:
    return {
        "enabled": True,
        "scene_id": "t",
        "base_tone": "neutral",
        "max_allowed_tone": "guarded",
        "allow_guarded_refusal": True,
        "allow_verbal_pressure": False,
        "allow_explicit_threat": False,
        "allow_physical_hostility": False,
        "allow_combat_initiation": False,
        "justification_flags": {},
        "justification_reasons": [],
        "debug_inputs": {"scene_id": "t"},
        "debug_flags": {},
        **overrides,  # type: ignore[arg-type]
    }


def _guarded_ceiling_contract() -> dict:
    return {
        "enabled": True,
        "base_tone": "neutral",
        "max_allowed_tone": "guarded",
        "allow_guarded_refusal": True,
        "allow_verbal_pressure": False,
        "allow_explicit_threat": False,
        "allow_physical_hostility": False,
        "allow_combat_initiation": False,
        "justification_flags": {},
        "justification_reasons": [],
    }


def test_retry_allows_hostile_false_without_policy() -> None:
    assert _retry_allows_hostile_escalation(None, response_policy=None) is False
    assert _retry_allows_hostile_escalation({}, response_policy={}) is False


def test_retry_allows_hostile_true_when_policy_allows_threat() -> None:
    pol = {"tone_escalation": _shipped_tone_policy(allow_explicit_threat=True, max_allowed_tone="threatening")}
    assert _retry_allows_hostile_escalation(None, response_policy=pol) is True


def test_topic_pressure_retry_prompt_bans_hostility_without_policy() -> None:
    failure = {
        "failure_class": "topic_pressure_escalation",
        "topic_context": {"topic_key": "patrol", "previous_answer_snippet": "Hard to say.", "repeat_count": 3},
    }
    prompt = build_retry_prompt_for_failure(failure, response_policy=None, gm_output=None).lower()
    assert "emerging threat" not in prompt
    assert "new npc interruption" not in prompt
    assert "topic pressure alone" in prompt or "without threats" in prompt
    assert "scene momentum" in prompt


def test_topic_pressure_retry_allows_grounded_hostility_when_policy_permits() -> None:
    pol = {"tone_escalation": _shipped_tone_policy(allow_explicit_threat=True, max_allowed_tone="threatening")}
    failure = {
        "failure_class": "topic_pressure_escalation",
        "topic_context": {"topic_key": "patrol", "repeat_count": 2},
    }
    prompt = build_retry_prompt_for_failure(failure, response_policy=pol, gm_output=None).lower()
    assert "calibrated confrontation" in prompt or "physical hostility" in prompt
    assert "do not invent random aggression" in prompt


def test_scene_stall_retry_includes_nonviolence_guard_without_policy() -> None:
    prompt = build_retry_prompt_for_failure(
        {"failure_class": "scene_stall"},
        response_policy=None,
        gm_output=None,
    ).lower()
    assert "do not introduce threats" in prompt or "violence" in prompt


def test_followup_repetition_retry_warns_against_hostility_without_policy() -> None:
    failure = {
        "failure_class": "followup_soft_repetition",
        "followup_context": {"previous_player_input": "Who?", "previous_answer_snippet": "Maybe.", "topic_tokens": ["x"]},
    }
    prompt = build_retry_prompt_for_failure(failure, response_policy=None, gm_output=None).lower()
    assert "topic pressure alone" in prompt or "weapons" in prompt


def test_exemplar_non_hostile_escalation_passes_validator() -> None:
    """Concrete menu the retry text steers toward should satisfy a guarded ceiling."""
    ctr = _guarded_ceiling_contract()
    samples = [
        (
            "The clerk names the east weigh-house; the ledger line closes at sundown—if you want a witness, "
            "the factor there saw the wagon turn north."
        ),
        "Marta refuses the name outright, but her eyes flick toward the chapel steps—someone there trades in rumors.",
        "Footsteps hurry on the stair; the moment is about to be decided for you if you do not pick a door.",
    ]
    for s in samples:
        v = validate_tone_escalation(s, contract=ctr)
        assert v.get("ok") is True, (s, v)


def test_retry_exemplar_passes_final_gate_minimal() -> None:
    ctr = _shipped_tone_policy()
    text = (
        "Lantern light catches dust on the clerk's fingers; he slides a folded route toward you—"
        "the night gate, not the day ward—and the queue behind you tightens."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "response_policy": {"tone_escalation": ctr}},
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="office",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("tone_escalation_repaired") is not True
    assert meta.get("tone_escalation_ok") is not False


def test_transcript_guarded_pressures_stay_below_threat_ceiling() -> None:
    """Simulate repeated player pressure: scrutiny and consequences, no jump to threat under guarded contract."""
    ctr = _guarded_ceiling_contract()
    beats = [
        'The guard says, "That is enough."',
        "His hand rests on the stamp-ribbon, not the blade—policy, not bravado.",
        "If you keep asking here, the watch sergeant hears about it before you get a straight answer.",
    ]
    for line in beats:
        v = validate_tone_escalation(line, contract=ctr)
        assert v.get("ok") is True, v
        assert v.get("detected_assertion_flags", {}).get("explicit_threat") is not True
