"""Shared shipped ``fallback_behavior`` / ``answer_completeness`` contract builders (Cycle AS5).

Support residue for gate, downstream consumer, and transcript suites. Predicate
semantics stay owned by ``tests/test_fallback_behavior_validator.py`` and
``tests/test_final_emission_repairs.py``; these helpers only pin stable contract
dict shapes for orchestration and wiring tests.

``assert_retry_debug_fallback_contract`` (Cycle BE Block 2) centralizes
``build_retry_prompt_for_failure`` retry_debug sink assertions for downstream
fallback-consumer tests.

CO19 gate-integration helpers (``fallback_gate_emission_debug``, ``assert_fallback_gate_metadata``,
``assert_fallback_gate_propagation``, ``assert_fallback_gate_repair_evidence``) absorb repeated
``apply_final_emission_gate`` FEM/debug propagation locks from ``tests/test_fallback_behavior_gate.py``
separately from validator predicate helpers and opening/visibility ownership helpers.

Import from here — not from ``tests/test_fallback_behavior_gate.py`` or other test modules.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from tests.helpers.opening_fallback_evidence import assert_final_emission_meta_contains
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output


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


def fallback_gate_emission_debug(out: Mapping[str, Any]) -> dict[str, Any]:
    """Return ``metadata.emission_debug.fallback_behavior`` slice from gate output."""
    metadata = out.get("metadata") if isinstance(out.get("metadata"), Mapping) else {}
    emission_debug = metadata.get("emission_debug") if isinstance(metadata.get("emission_debug"), Mapping) else {}
    fb = emission_debug.get("fallback_behavior")
    return dict(fb) if isinstance(fb, Mapping) else {}


def assert_fallback_gate_metadata(
    meta: Mapping[str, Any] | None,
    *,
    checked: bool | None = None,
    repaired: bool | None = None,
    uncertainty_active: bool | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Assert FEM fallback-behavior propagation stamps (gate integration, not validator predicates)."""
    fem = dict(meta) if isinstance(meta, Mapping) else {}
    if checked is not None:
        assert fem.get("fallback_behavior_checked") is checked
    if repaired is not None:
        assert fem.get("fallback_behavior_repaired") is repaired
    if uncertainty_active is not None:
        assert fem.get("fallback_behavior_uncertainty_active") is uncertainty_active
    if extra:
        assert_final_emission_meta_contains(fem, **extra)
    return fem


def assert_fallback_gate_propagation(
    out: Mapping[str, Any],
    *,
    validation_checked: bool | None = None,
    checked: bool | None = None,
    repaired: bool | None = None,
    uncertainty_active: bool | None = None,
    repair_mode_matches_fem: bool = False,
    **extra_fem: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Assert gate output propagated FEM fallback metadata and optional emission_debug validation."""
    meta = final_emission_meta_from_output(out) or {}
    emission_debug = fallback_gate_emission_debug(out)
    assert_fallback_gate_metadata(
        meta,
        checked=checked,
        repaired=repaired,
        uncertainty_active=uncertainty_active,
        **extra_fem,
    )
    if validation_checked is not None:
        assert (emission_debug.get("validation") or {}).get("checked") is validation_checked
    if repair_mode_matches_fem:
        assert emission_debug.get("repair_mode") == meta.get("fallback_behavior_repair_mode")
    return meta, emission_debug


def assert_fallback_gate_repair_evidence(
    out: Mapping[str, Any],
    *,
    forbidden_phrases: Sequence[str] = (),
    required_phrases: Sequence[str] = (),
    require_non_empty: bool = False,
) -> str:
    """Assert gate repair rewrote player-facing text away from meta-voice leaks."""
    text = str(out.get("player_facing_text") or "")
    low = text.lower()
    for phrase in forbidden_phrases:
        assert phrase.lower() not in low, (
            f"expected forbidden phrase absent from player-facing text: {phrase!r}"
        )
    for phrase in required_phrases:
        assert phrase.lower() in low, (
            f"expected required phrase in player-facing text: {phrase!r}"
        )
    if require_non_empty:
        assert text.strip(), "expected non-empty repaired player-facing text"
    return text
