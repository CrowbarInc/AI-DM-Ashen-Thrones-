"""Practical primary direct-owner suite for ``game.response_policy_contracts``.

This file owns direct read-side response-policy accessors and canonical bundle
materialization semantics. Downstream fallback, validator, emission, and gate
tests may still consume these contracts, but they should remain secondary
coverage rather than the semantic authority for the seam.
"""
from __future__ import annotations

import pytest

from game.response_policy_contracts import (
    materialize_response_policy_bundle,
    resolve_answer_completeness_contract,
    resolve_fallback_behavior_contract,
    resolve_response_delta_contract,
    resolve_social_response_structure_contract,
    response_type_contract_requires_dialogue,
)

pytestmark = pytest.mark.unit


def test_response_policy_accessors_read_canonical_bundle_children() -> None:
    pol = {
        "answer_completeness": {"enabled": True, "answer_required": True},
        "response_delta": {"enabled": True, "delta_required": True},
        "fallback_behavior": {"enabled": True, "uncertainty_active": True},
        "social_response_structure": {
            "enabled": True,
            "applies_to_response_type": "dialogue",
        },
    }
    gm = {"response_policy": pol}

    assert resolve_answer_completeness_contract(gm) is pol["answer_completeness"]
    assert resolve_response_delta_contract(gm) is pol["response_delta"]
    assert resolve_fallback_behavior_contract(gm) is pol["fallback_behavior"]
    assert resolve_social_response_structure_contract(gm) is pol["social_response_structure"]


def test_fallback_behavior_accessor_keeps_top_level_compatibility_residue() -> None:
    fb = {"enabled": True, "uncertainty_active": False}
    assert resolve_fallback_behavior_contract({"fallback_behavior": fb}) is fb


def test_social_response_structure_accessor_keeps_top_level_compatibility_residue() -> None:
    srs = {"enabled": False, "applies_to_response_type": "dialogue"}
    assert resolve_social_response_structure_contract({"social_response_structure_contract": srs}) is srs


def test_materialize_response_policy_bundle_merges_session_residue_when_gm_lacks_policy() -> None:
    pol = {"context_separation": {"enabled": True, "focus_mode": "local"}}
    out = materialize_response_policy_bundle(
        {"player_facing_text": "Rain threads along the slate.", "tags": []},
        {"last_turn_response_policy": pol},
    )
    assert out["response_policy"] is pol


def test_materialize_response_policy_bundle_preserves_existing_gm_policy() -> None:
    shipped = {"context_separation": {"enabled": True, "focus_mode": "local"}}
    session_pol = {"context_separation": {"enabled": True, "focus_mode": "ambient"}}
    out = materialize_response_policy_bundle(
        {"player_facing_text": "Rain threads along the slate.", "response_policy": shipped},
        {"last_turn_response_policy": session_pol},
    )
    assert out["response_policy"] is shipped


def test_response_type_contract_requires_dialogue_reads_canonical_contract() -> None:
    gm = {
        "response_policy": {
            "response_type_contract": {
                "required_response_type": "dialogue",
            }
        }
    }
    assert response_type_contract_requires_dialogue(gm, resolution=None, session=None) is True
    assert response_type_contract_requires_dialogue({}, resolution=None, session=None) is False
