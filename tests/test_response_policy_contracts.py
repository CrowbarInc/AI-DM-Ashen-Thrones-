"""Practical primary direct-owner suite for ``game.response_policy_contracts``.

This file owns direct read-side response-policy accessors, canonical bundle
materialization semantics, and response-type enforcement / upstream-prepared
emission selection behavior at the gate seam.

Downstream fallback, validator, emission, gate-order, and interaction-continuity
tests may still consume these contracts, but they should remain secondary coverage
rather than the semantic authority for the seam.
"""
from __future__ import annotations

import pytest

from game.realization_authority import FALLBACK_FAMILIES
from game.realization_provenance import (
    GATE_TERMINAL_REPAIR,
    REALIZATION_FALLBACK_FAMILY_FIELD,
    UPSTREAM_PREPARED_EMISSION,
)
from game.response_policy_contracts import (
    materialize_response_policy_bundle,
    resolve_answer_completeness_contract,
    resolve_conversational_memory_window_contract,
    resolve_fallback_behavior_contract,
    resolve_interaction_continuity_contract,
    resolve_response_delta_contract,
    resolve_social_response_structure_contract,
    response_type_contract_requires_dialogue,
)
from game.upstream_response_repairs import UPSTREAM_PREPARED_EMISSION_KEY
from tests.helpers.emission_smoke_assertions import (
    apply_final_emission_gate_consumer,
    enforce_response_type_contract_layer,
    final_emission_meta_from_output,
    response_type_contract,
)


def _apply_gate(*args, **kwargs):
    out, _ = apply_final_emission_gate_consumer(*args, **kwargs)
    return out

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


def test_interaction_continuity_accessor_reads_shipped_response_policy_contract() -> None:
    ic = {
        "enabled": True,
        "continuity_strength": "strong",
        "anchored_interlocutor_id": "npc_melka",
    }
    gm = {"response_policy": {"interaction_continuity": ic}}

    resolved, src = resolve_interaction_continuity_contract(
        gm,
        resolution=None,
        session=None,
    )

    assert src == "response_policy"
    assert resolved == ic


def test_conversational_memory_window_accessor_reads_shipped_response_policy_contract() -> None:
    cmw = {
        "enabled": True,
        "window_version": "v1",
    }
    gm = {"response_policy": {"conversational_memory_window": cmw}}

    resolved, src = resolve_conversational_memory_window_contract(
        gm,
        resolution=None,
        session=None,
    )

    assert src == "response_policy"
    assert resolved == cmw


# --- Response-type enforcement / upstream-prepared emission ownership ---


def _assert_known_realization_family(value: str) -> None:
    assert value in FALLBACK_FAMILIES


def test_enforce_response_type_contract_marks_upstream_absent_for_answer_without_prepared_text():
    text, dbg = enforce_response_type_contract_layer(
        "Only mist between the torches.",
        gm_output={
            "response_policy": {"response_type_contract": response_type_contract("answer")},
            "upstream_prepared_emission": {},
        },
        resolution={"kind": "observe", "prompt": "What do I see?"},
        session={},
        scene_id="yard",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )
    assert dbg.get("response_type_upstream_prepared_absent") is True
    assert dbg.get("response_type_candidate_ok") is False
    assert text == "Only mist between the torches."


def test_final_gate_upstream_prepared_emission_branch_records_upstream_family() -> None:
    out = _apply_gate(
        {
            "player_facing_text": "Mist gathers without answering.",
            "tags": [],
            "response_policy": {"response_type_contract": response_type_contract("answer")},
            UPSTREAM_PREPARED_EMISSION_KEY: {
                "prepared_answer_fallback_text": "Yes. The east gate is open until dusk.",
                "upstream_prepared_emission_attribution": "unit_upstream_answer",
            },
        },
        resolution={"kind": "question", "prompt": "Is the east gate open?"},
        session={},
        scene_id="yard",
        world={},
    )

    fem = final_emission_meta_from_output(out) or {}
    assert out["player_facing_text"] == "Yes. The east gate is open until dusk."
    assert fem["final_route"] == "accept_candidate"
    assert fem["final_emitted_source"] == "answer_upstream_prepared_repair"
    assert fem["response_type_repair_kind"] == "answer_upstream_prepared_repair"
    assert fem["upstream_prepared_emission_used"] is True
    assert fem["upstream_prepared_emission_valid"] is True
    assert fem["upstream_prepared_emission_source"] == "unit_upstream_answer"
    lineage = fem.get("final_emission_mutation_lineage")
    assert "response_type_repair" in lineage
    assert "prepared_emission_selection" in lineage
    assert "finalize_packaging" in lineage
    family = fem[REALIZATION_FALLBACK_FAMILY_FIELD]
    _assert_known_realization_family(family)
    assert family == UPSTREAM_PREPARED_EMISSION
    assert family != GATE_TERMINAL_REPAIR


@pytest.mark.parametrize(
    ("required", "prepared_field", "invalid_prepared", "repair_kind"),
    [
        ("answer", "prepared_answer_fallback_text", "Mist gathers without answering.", "answer_upstream_prepared_repair"),
        (
            "action_outcome",
            "prepared_action_fallback_text",
            "You consider the lock.",
            "action_outcome_upstream_prepared_repair",
        ),
    ],
)
def test_enforce_response_type_contract_rejects_malformed_prepared_answer_action_without_synthesis(
    required: str,
    prepared_field: str,
    invalid_prepared: str,
    repair_kind: str,
) -> None:
    candidate = "Only mist between the torches."

    text, dbg = enforce_response_type_contract_layer(
        candidate,
        gm_output={
            "response_policy": {"response_type_contract": response_type_contract(required)},
            UPSTREAM_PREPARED_EMISSION_KEY: {
                prepared_field: invalid_prepared,
                "upstream_prepared_emission_attribution": f"unit_invalid_{required}",
            },
        },
        resolution={"kind": "investigate", "prompt": "Can I force the lock?"},
        session={},
        scene_id="yard",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert text == candidate
    assert text != invalid_prepared
    assert dbg.get("response_type_candidate_ok") is False
    assert dbg.get("response_type_repair_kind") == repair_kind
    assert dbg.get("upstream_prepared_emission_used") is False
    assert dbg.get("upstream_prepared_emission_valid") is False
    assert dbg.get("upstream_prepared_emission_source") == f"unit_invalid_{required}"
    assert dbg.get("upstream_prepared_emission_reject_reason")


@pytest.mark.parametrize(
    ("required", "prompt"),
    [
        ("answer", "What do I see?"),
        ("action_outcome", "I force the lock."),
    ],
)
def test_enforce_response_type_contract_absent_prepared_answer_action_keeps_candidate_without_synthesis(
    required: str,
    prompt: str,
) -> None:
    candidate = "Only mist between the torches."

    text, dbg = enforce_response_type_contract_layer(
        candidate,
        gm_output={
            "response_policy": {"response_type_contract": response_type_contract(required)},
            UPSTREAM_PREPARED_EMISSION_KEY: {},
        },
        resolution={"kind": "investigate", "prompt": prompt},
        session={},
        scene_id="yard",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert text == candidate
    assert dbg.get("response_type_upstream_prepared_absent") is True
    assert dbg.get("response_type_candidate_ok") is False
    assert dbg.get("response_type_repair_used") is False
    assert dbg.get("response_type_repair_kind") is None
    assert dbg.get("upstream_prepared_emission_source") == "absent"
