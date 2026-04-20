"""Downstream fallback-consumer coverage.

This suite validates how repaired outputs are consumed by fallback,
gate, and retry systems.

It does NOT own repair semantics. All repair derivation, helper logic,
and materialization behavior are owned by:

```
tests/test_final_emission_repairs.py
```

"""
from __future__ import annotations

from game.final_emission_meta import read_final_emission_meta_dict

import pytest

from game.final_emission_gate import apply_final_emission_gate
from game.gm import apply_response_policy_enforcement
from game.gm_retry import build_retry_prompt_for_failure


pytestmark = pytest.mark.unit


def _consumer_fallback_contract(**overrides: object) -> dict:
    contract = {
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
        "forbidden_hedge_forms": [
            "I lack enough information to answer confidently.",
            "The system cannot confirm that.",
            "Canon proves it.",
            "As an AI, I don't know.",
            "There is insufficient context available.",
        ],
        "allowed_authority_bases": [
            "direct_observation",
            "established_report",
            "rumor_marked_as_rumor",
            "visible_evidence",
        ],
        "forbidden_authority_bases": [
            "unsupported_named_culprit",
            "unsupported_exact_location",
            "unsupported_motive_as_fact",
            "unsupported_procedural_certainty",
            "system_or_canon_claims",
        ],
        "debug": {},
    }
    contract.update(overrides)
    return contract


def _response_type_contract(required: str = "answer") -> dict:
    return {
        "required_response_type": required,
        "action_must_preserve_agency": required == "action_outcome",
    }


def _answer_contract(**overrides: object) -> dict:
    contract = {
        "enabled": True,
        "answer_required": True,
        "answer_must_come_first": False,
        "player_direct_question": True,
        "expected_voice": "narrator",
        "expected_answer_shape": "bounded_partial",
        "allowed_partial_reasons": ["uncertainty", "lack_of_knowledge", "gated_information"],
        "forbid_deflection": True,
        "forbid_generic_nonanswer": True,
        "require_concrete_payload": True,
        "concrete_payload_any_of": ["place", "name", "next_lead"],
        "trace": {},
    }
    contract.update(overrides)
    return contract


def test_downstream_retry_observes_shipped_fallback_contract_and_final_emission_meta() -> None:
    contract = _consumer_fallback_contract()
    gm = apply_response_policy_enforcement(
        {"player_facing_text": "The line inches forward."},
        response_policy={"fallback_behavior": contract},
        player_text="Who did it?",
        scene_envelope={"scene": {"id": "frontier_gate"}},
        session={},
        world={},
        resolution={"kind": "adjudication_query", "prompt": "Who did it?"},
    )

    emitted_contract = ((gm.get("metadata") or {}).get("emission_debug") or {}).get("fallback_behavior_contract") or {}
    assert emitted_contract.get("enabled") is True
    assert emitted_contract.get("uncertainty_active") is True
    assert emitted_contract.get("prefer_partial_over_question") is True

    retry_debug: dict = {}
    gm_with_meta = dict(gm)
    gm_with_meta["_final_emission_meta"] = {
        "fallback_behavior_checked": True,
        "fallback_behavior_failed": True,
        "fallback_behavior_repaired": True,
        "fallback_behavior_skip_reason": None,
        "fallback_behavior_failure_reasons": ["missing_allowed_fallback_shape"],
    }
    build_retry_prompt_for_failure(
        {"failure_class": "scene_stall", "reasons": ["test"]},
        response_policy=gm.get("response_policy"),
        gm_output=gm_with_meta,
        retry_debug_sink=retry_debug,
        player_text="Who did it?",
    )

    assert retry_debug.get("retry_fallback_behavior_contract_present") is True
    assert retry_debug.get("retry_fallback_behavior_uncertainty_active") is True
    assert retry_debug.get("retry_fallback_behavior_checked") is True
    assert retry_debug.get("retry_fallback_behavior_repaired") is True
    assert retry_debug.get("retry_fallback_behavior_failure_reasons") == [
        "missing_allowed_fallback_shape"
    ]


def test_retry_consumer_prefers_upstream_fallback_meta_over_nested_debug_noise() -> None:
    retry_debug: dict = {}
    build_retry_prompt_for_failure(
        {"failure_class": "scene_stall", "reasons": ["test"]},
        response_policy={"fallback_behavior": _consumer_fallback_contract()},
        gm_output={
            "response_policy": {"fallback_behavior": _consumer_fallback_contract(uncertainty_active=False)},
            "_final_emission_meta": {
                "fallback_behavior_checked": False,
                "fallback_behavior_failed": True,
                "fallback_behavior_repaired": False,
                "fallback_behavior_skip_reason": "upstream_skip",
                "fallback_behavior_failure_reasons": ["residual_shape_gap"],
            },
            "metadata": {
                "emission_debug": {
                    "fallback_behavior": {
                        "validation": {"checked": True, "passed": True},
                        "skip_reason": "conflicting_nested_value",
                    }
                }
            },
        },
        retry_debug_sink=retry_debug,
        player_text="No. Exactly who?",
    )

    assert retry_debug.get("retry_fallback_behavior_contract_present") is True
    assert retry_debug.get("retry_fallback_behavior_uncertainty_active") is True
    assert retry_debug.get("retry_fallback_behavior_checked") is False
    assert retry_debug.get("retry_fallback_behavior_failed") is True
    assert retry_debug.get("retry_fallback_behavior_repaired") is False
    assert retry_debug.get("retry_fallback_behavior_skip_reason") == "upstream_skip"
    assert retry_debug.get("retry_fallback_behavior_failure_reasons") == ["residual_shape_gap"]


def test_downstream_gate_observes_answer_contract_meta_when_output_exhibits_smoothed_fallback_shape() -> None:
    out = apply_final_emission_gate(
        {
            "player_facing_text": (
                "No names yet. Check the ward clerk at the east gate office. "
                "I don't have enough information to answer confidently."
            ),
            "tags": [],
            "response_policy": {
                "response_type_contract": _response_type_contract("answer"),
                "answer_completeness": _answer_contract(),
                "fallback_behavior": _consumer_fallback_contract(),
            },
        },
        resolution={"kind": "adjudication_query", "prompt": "No. Exactly who?"},
        session={},
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("response_type_required") == "answer"
    assert meta.get("response_type_candidate_ok") is True
    assert meta.get("answer_completeness_checked") is True
    assert meta.get("answer_completeness_failed") is False
    assert meta.get("fallback_behavior_repaired") is True
    assert "enough information" not in str(out.get("player_facing_text") or "").lower()
