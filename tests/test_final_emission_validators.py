"""Validator-side downstream coverage for ``validate_social_response_structure``.

Direct shipped-contract ownership for social-response-structure and other response-policy
accessors lives in ``tests/test_response_policy_contracts.py``. This file only verifies
validator application behavior once those already-owned contracts have been supplied.
"""
from __future__ import annotations

import pytest

from game.final_emission_validators import validate_social_response_structure

pytestmark = pytest.mark.unit


def _base_dialogue_contract(**overrides: object) -> dict:
    c = {
        "enabled": True,
        "applies_to_response_type": "dialogue",
        "require_spoken_dialogue_shape": True,
        "discourage_expository_monologue": True,
        "require_natural_cadence": True,
        "allow_brief_action_beats": True,
        "allow_brief_refusal_or_uncertainty": True,
        "max_contiguous_expository_lines": 2,
        "max_dialogue_paragraphs_before_break": 2,
        "prefer_single_speaker_turn": True,
        "forbid_bulleted_or_list_like_dialogue": True,
        "required_response_type": "dialogue",
    }
    c.update(overrides)
    return c


def test_social_response_structure_disabled_contract_noops():
    contract = _base_dialogue_contract(enabled=False)
    r = validate_social_response_structure("any text", contract)
    assert r["checked"] is False
    assert r["applicable"] is False
    assert r["passed"] is True
    assert r["failure_reasons"] == []


def test_social_response_structure_non_dialogue_contract_noops():
    contract = _base_dialogue_contract(applies_to_response_type="answer")
    r = validate_social_response_structure("- bullet line", contract)
    assert r["applicable"] is False
    assert r["passed"] is True
    assert r["failure_reasons"] == []


def test_empty_emitted_text_fails_when_applicable():
    contract = _base_dialogue_contract()
    r = validate_social_response_structure("", contract)
    assert r["checked"] is True
    assert r["applicable"] is True
    assert r["passed"] is False
    assert "empty_emitted_text" in r["failure_reasons"]


def test_list_like_dialogue_fails_with_expected_reason():
    contract = _base_dialogue_contract()
    text = '- "East gate lies two hundred feet south," he mutters.\n- "Patrols chart that lane nightly."'
    r = validate_social_response_structure(text, contract)
    assert r["applicable"] is True
    assert r["passed"] is False
    assert "list_like_or_bulleted_dialogue" in r["failure_reasons"]


def test_multi_speaker_dialogue_fails_with_expected_reason():
    contract = _base_dialogue_contract()
    text = (
        'Garreth: "The east gate is two hundred feet along the market road."\n'
        'Morwen: "Patrols hold that lane until dusk."'
    )
    r = validate_social_response_structure(text, contract)
    assert r["applicable"] is True
    assert r["passed"] is False
    assert "multi_speaker_turn_formatting" in r["failure_reasons"]


def test_summary_like_nonspoken_dialogue_fails_with_missing_spoken_shape():
    contract = _base_dialogue_contract()
    text = (
        "The checkpoint rumor describes supply movements, watch rotations, and which lanes stay open after curfew; "
        "nothing in it names a single officer responsible for the patrol roster."
    )
    r = validate_social_response_structure(text, contract)
    assert r["applicable"] is True
    assert r["passed"] is False
    assert "missing_spoken_dialogue_shape" in r["failure_reasons"]


def test_conversational_uncertainty_can_still_pass():
    contract = _base_dialogue_contract()
    text = 'The guard shrugs. "I am not sure—maybe the east lane, maybe nothing at all."'
    r = validate_social_response_structure(text, contract)
    assert r["applicable"] is True
    assert r["passed"] is True
    assert r["failure_reasons"] == []
