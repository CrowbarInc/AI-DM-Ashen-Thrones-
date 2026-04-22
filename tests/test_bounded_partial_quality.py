"""Bounded-partial **validator** coverage under unresolved-question pressure.

Objective C2 Block C: ``repair_fallback_behavior`` is strip-only at the boundary; synthesis
that made thin lines pass ``validate_fallback_behavior`` lives upstream. These tests assert
validator signals and strip-only non-authorship where still applicable.
"""
from __future__ import annotations

import pytest

from game.final_emission_repairs import repair_fallback_behavior
from game.final_emission_validators import validate_fallback_behavior


pytestmark = pytest.mark.unit


def _contract(**overrides: object) -> dict:
    base = {
        "enabled": True,
        "uncertainty_active": True,
        "uncertainty_sources": ["unknown_identity"],
        "uncertainty_mode": "scene_ambiguity",
        "allowed_behaviors": {
            "ask_clarifying_question": True,
            "hedge_appropriately": True,
            "provide_partial_information": True,
        },
        "disallowed_behaviors": {
            "invented_certainty": True,
            "fabricated_authority": True,
            "meta_system_explanations": True,
        },
        "diegetic_only": True,
        "max_clarifying_questions": 1,
        "prefer_partial_over_question": True,
        "require_partial_to_state_known_edge": True,
        "require_partial_to_state_unknown_edge": True,
        "require_partial_to_offer_next_lead": True,
        "allowed_hedge_forms": [
            "I can't swear to it, but",
            "From what I saw,",
            "As far as rumor goes,",
            "Looks like",
            "Hard to tell, but",
        ],
        "forbidden_hedge_forms": [],
        "allowed_authority_bases": ["visible_evidence", "rumor_marked_as_rumor"],
        "forbidden_authority_bases": [],
        "debug": {},
    }
    base.update(overrides)
    return base


def test_unresolved_identity_quality_accepts_unknown_and_next_lead_consumer_shape() -> None:
    ctr = _contract()
    resolution = {"kind": "question", "prompt": "Who was the buyer, exactly?"}
    raw = "No name comes clear from what shows."
    v0 = validate_fallback_behavior(raw, ctr, resolution=resolution)
    assert v0.get("passed") is False
    repaired, meta, _ = repair_fallback_behavior(raw, ctr, v0, resolution=resolution)
    v1 = validate_fallback_behavior(repaired, ctr, resolution=resolution)
    assert repaired == raw
    assert v1.get("passed") is False
    assert meta.get("fallback_behavior_partial_used") is False
    assert meta.get("fallback_behavior_boundary_semantic_synthesis_skipped") is True


def test_thin_generic_identity_line_triggers_substance_failure() -> None:
    ctr = _contract()
    out = validate_fallback_behavior("No name comes clear from what shows.", ctr)
    assert out.get("passed") is False
    assert "bounded_partial_insufficient_substance" in (out.get("failure_reasons") or [])


def test_synthesis_from_thin_line_does_not_introduce_new_named_culprits() -> None:
    """Strip-only repair must not mint new named culprits."""
    ctr = _contract()
    resolution = {"kind": "adjudication_query", "prompt": "Who signed the order?"}
    raw = "No name comes clear from what shows."
    v0 = validate_fallback_behavior(raw, ctr, resolution=resolution)
    repaired, _, _ = repair_fallback_behavior(raw, ctr, v0, resolution=resolution)
    low = repaired.lower()
    assert repaired == raw
    assert "verrick" not in low
    assert "culprit was" not in low


@pytest.mark.skip(reason="C2 Block C: NPC-vocative bounded-partial synthesis moved upstream from final emission")
def test_recovered_vocative_uses_npc_specific_known_edge_not_generic_crowd_noise() -> None:
    ctr = _contract()
    resolution = {
        "kind": "question",
        "prompt": "Who was the buyer?",
        "social": {
            "npc_id": "runner_01",
            "npc_name": "Mara",
            "social_intent_class": "social_exchange",
        },
    }
    raw = "No name comes clear from what shows."
    v0 = validate_fallback_behavior(raw, ctr, resolution=resolution)
    repaired, _, _ = repair_fallback_behavior(raw, ctr, v0, resolution=resolution)
    low = repaired.lower()
    assert "mara" in low
    assert "noise along the road stays loud" not in low
