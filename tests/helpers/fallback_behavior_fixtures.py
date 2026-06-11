"""Shared shipped ``fallback_behavior`` / ``answer_completeness`` contract builders (Cycle AS5).

Support residue for gate, downstream consumer, and transcript suites. Predicate
semantics stay owned by ``tests/test_fallback_behavior_validator.py`` and
``tests/test_final_emission_repairs.py``; these helpers only pin stable contract
dict shapes for orchestration and wiring tests.

``assert_retry_debug_fallback_contract`` (Cycle BE Block 2) centralizes
``build_retry_prompt_for_failure`` retry_debug sink assertions for downstream
fallback-consumer tests.

Import from here — not from ``tests/test_fallback_behavior_gate.py`` or other test modules.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def fallback_contract(**overrides: object) -> dict:
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


def answer_contract(**overrides: object) -> dict:
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


def assert_retry_debug_fallback_contract(
    retry_debug: Mapping[str, Any],
    *,
    contract_present: bool,
    uncertainty_active: bool,
    checked: bool,
    repaired: bool,
    failure_reasons: Sequence[str],
    failed: bool | None = None,
    skip_reason: str | None = None,
) -> None:
    """Assert ``gm_retry`` fallback contract fields written to a retry_debug sink."""
    bool_expectations: tuple[tuple[str, bool], ...] = (
        ("retry_fallback_behavior_contract_present", contract_present),
        ("retry_fallback_behavior_uncertainty_active", uncertainty_active),
        ("retry_fallback_behavior_checked", checked),
        ("retry_fallback_behavior_repaired", repaired),
    )
    for key, expected in bool_expectations:
        actual = retry_debug.get(key)
        assert actual is expected, (
            f"retry_debug {key!r}: expected {expected!r}, got {actual!r}"
        )
    expected_reasons = list(failure_reasons)
    actual_reasons = retry_debug.get("retry_fallback_behavior_failure_reasons")
    assert actual_reasons == expected_reasons, (
        "retry_debug 'retry_fallback_behavior_failure_reasons': "
        f"expected {expected_reasons!r}, got {actual_reasons!r}"
    )
    if failed is not None:
        actual = retry_debug.get("retry_fallback_behavior_failed")
        assert actual is failed, (
            f"retry_debug 'retry_fallback_behavior_failed': expected {failed!r}, got {actual!r}"
        )
    if skip_reason is not None:
        actual = retry_debug.get("retry_fallback_behavior_skip_reason")
        assert actual == skip_reason, (
            f"retry_debug 'retry_fallback_behavior_skip_reason': "
            f"expected {skip_reason!r}, got {actual!r}"
        )
