"""Validator-side downstream coverage for ``validate_social_response_structure``.

Direct shipped-contract ownership for social-response-structure and other response-policy
accessors lives in ``tests/test_response_policy_contracts.py``. This file only verifies
validator application behavior once those already-owned contracts have been supplied.
"""
from __future__ import annotations

import pytest

from game.final_emission_repairs import _apply_referent_clarity_emission_layer
from game.final_emission_validators import validate_referent_clarity, validate_social_response_structure
from tests.helpers.objective7_referent_fixtures import (
    minimal_full_referent_artifact,
    referent_compact_mirror,
)

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


def test_validate_referent_clarity_full_artifact_detects_lead_pronoun():
    art = minimal_full_referent_artifact(
        referential_ambiguity_class="ambiguous_plural",
        single_unambiguous_entity=None,
        ambiguity_risk=70,
        safe_explicit_fallback_labels=[
            {"entity_id": "npc_gate", "safe_explicit_label": "Gate sergeant"},
            {"entity_id": "npc_runner", "safe_explicit_label": "Runner"},
        ],
        allowed_named_references=[
            {"entity_id": "npc_gate", "display_name": "Gate sergeant"},
            {"entity_id": "npc_runner", "display_name": "Runner"},
        ],
    )
    r = validate_referent_clarity("They wait by the gate.", referent_tracking=art, referent_tracking_compact=None)
    assert r["referent_validation_ran"] is True
    assert r["referent_validation_input_source"] == "full_artifact"
    assert "ambiguous_pronoun_environment" in r["referent_violation_categories"]
    assert "pronoun_before_anchor" in r["referent_violation_categories"]


def test_validate_referent_clarity_prefers_full_artifact_when_compact_diverges():
    full = minimal_full_referent_artifact(referential_ambiguity_class="none", ambiguity_risk=5)
    compact = referent_compact_mirror(referential_ambiguity_class="ambiguous_plural", ambiguity_risk=92)
    r = validate_referent_clarity("They halt.", referent_tracking=full, referent_tracking_compact=compact)
    assert r["referent_validation_input_source"] == "full_artifact"
    assert "explicit_subject_substitution_eligible" in r["referent_violation_categories"]


def test_validate_referent_clarity_compact_only_records_observability_without_categories():
    compact = referent_compact_mirror(referential_ambiguity_class="ambiguous_singular", ambiguity_risk=80)
    r = validate_referent_clarity("They wait.", referent_tracking=None, referent_tracking_compact=compact)
    assert r["referent_validation_input_source"] == "packet_compact"
    assert r["referent_violation_categories"] == []
    assert r["unresolved_referent_ambiguity"] is True


def test_apply_referent_clarity_replaces_pronoun_with_single_unambiguous_label():
    art = minimal_full_referent_artifact()
    gm = {"prompt_context": {"referent_tracking": art}, "_gate_turn_packet_cache": {}}
    text, dbg, _ = _apply_referent_clarity_emission_layer("They wait.", gm_output=gm)
    assert "Gate sergeant" in text
    assert dbg["referent_repair_applied"] is True
    assert dbg["referent_repair_strategy"] == "replace_first_risky_pronoun_with_explicit_label"
    assert dbg["referent_validation_input_source"] == "full_artifact"


def test_apply_referent_clarity_safe_fallback_single_row():
    art = minimal_full_referent_artifact(
        single_unambiguous_entity=None,
        referential_ambiguity_class="ambiguous_plural",
        safe_explicit_fallback_labels=[{"entity_id": "npc_gate", "safe_explicit_label": "Watch sergeant"}],
        allowed_named_references=[{"entity_id": "npc_gate", "display_name": "Watch sergeant"}],
    )
    gm = {"prompt_context": {"referent_tracking": art}}
    text, dbg, _ = _apply_referent_clarity_emission_layer("They nod.", gm_output=gm)
    assert text.startswith("Watch sergeant")
    assert dbg["referent_repair_applied"] is True


def test_apply_referent_clarity_skips_ambiguous_without_safe_label():
    art = minimal_full_referent_artifact(
        single_unambiguous_entity=None,
        referential_ambiguity_class="ambiguous_plural",
        active_interaction_target=None,
        continuity_subject=None,
        interaction_target_continuity={
            "prior_target_id": None,
            "current_target_id": None,
            "signal_target_id": None,
            "target_visible": False,
            "drift_detected": False,
            "signal_sources": [],
        },
        safe_explicit_fallback_labels=[
            {"entity_id": "a", "safe_explicit_label": "One"},
            {"entity_id": "b", "safe_explicit_label": "Two"},
        ],
        allowed_named_references=[
            {"entity_id": "a", "display_name": "One"},
            {"entity_id": "b", "display_name": "Two"},
        ],
    )
    gm = {"prompt_context": {"referent_tracking": art}}
    text, dbg, _ = _apply_referent_clarity_emission_layer("They disagree.", gm_output=gm)
    assert text == "They disagree."
    assert dbg["referent_repair_applied"] is False
    assert dbg.get("referent_repair_skipped_reason") == "no_safe_deterministic_repair"


def test_apply_referent_clarity_never_inserts_forbidden_name():
    art = minimal_full_referent_artifact(
        forbidden_or_unresolved_patterns=[
            {"kind": "memory_entity_not_visible", "entity_id": "npc_hidden", "detail": "x"}
        ],
        active_entities=[{"entity_id": "npc_hidden", "display_name": "Morwen"}],
    )
    gm = {"prompt_context": {"referent_tracking": art}}
    text, dbg, _ = _apply_referent_clarity_emission_layer("Morwen waits in shadow.", gm_output=gm)
    assert "Morwen waits" in text
    assert dbg["referent_repair_applied"] is False


def test_apply_referent_clarity_active_target_pinned_prefers_continuity_label():
    art = minimal_full_referent_artifact(
        single_unambiguous_entity=None,
        referential_ambiguity_class="ambiguous_plural",
        safe_explicit_fallback_labels=[
            {"entity_id": "npc_gate", "safe_explicit_label": "Gate sergeant"},
            {"entity_id": "npc_runner", "safe_explicit_label": "Runner"},
        ],
        allowed_named_references=[
            {"entity_id": "npc_gate", "display_name": "Gate sergeant"},
            {"entity_id": "npc_runner", "display_name": "Runner"},
        ],
        continuity_subject={"entity_id": "npc_gate", "display_name": "Gate sergeant", "source": "t"},
    )
    gm = {"prompt_context": {"referent_tracking": art}}
    text, dbg, _ = _apply_referent_clarity_emission_layer("He waits.", gm_output=gm)
    assert text.startswith("Gate sergeant")
    assert dbg["referent_repair_applied"] is True
    assert dbg.get("referent_repair_label_source") == "active_interaction_target_pinned"


def test_apply_referent_clarity_compact_only_abstains_repair():
    gm = {
        "prompt_context": {},
        "_gate_turn_packet_cache": {
            "referent_tracking_compact": referent_compact_mirror(
                active_interaction_target="x",
                referential_ambiguity_class="ambiguous_singular",
                ambiguity_risk=80,
            )
        },
    }
    text, dbg, _ = _apply_referent_clarity_emission_layer("They wait.", gm_output=gm)
    assert text == "They wait."
    assert dbg["referent_validation_input_source"] == "packet_compact"
    assert dbg["referent_repair_skipped_reason"] == "limited_input_no_full_artifact"


def test_apply_referent_clarity_missing_inputs_noop():
    gm: dict = {"prompt_context": {}}
    text, dbg, _ = _apply_referent_clarity_emission_layer("They wait.", gm_output=gm)
    assert text == "They wait."
    assert dbg["referent_validation_input_source"] == "missing"
    assert dbg["referent_repair_skipped_reason"] == "no_referent_inputs"


def test_apply_referent_clarity_replaces_at_most_one_pronoun_token():
    art = minimal_full_referent_artifact()
    gm = {"prompt_context": {"referent_tracking": art}}
    text, dbg, _ = _apply_referent_clarity_emission_layer("They wait and they leave.", gm_output=gm)
    assert dbg["referent_repair_applied"] is True
    assert text.lower().count("they") == 1
    assert text.count("Gate sergeant") == 1


def test_apply_referent_clarity_abstains_when_disallowed_named_reference_present():
    art = minimal_full_referent_artifact(
        forbidden_or_unresolved_patterns=[
            {"kind": "memory_entity_not_visible", "entity_id": "npc_hidden", "detail": "x"}
        ],
        active_entities=[{"entity_id": "npc_hidden", "display_name": "Morwen", "entity_kind": "npc", "roles": []}],
    )
    gm = {"prompt_context": {"referent_tracking": art}}
    text, dbg, _ = _apply_referent_clarity_emission_layer("They wait. Morwen waits in shadow.", gm_output=gm)
    assert text == "They wait. Morwen waits in shadow."
    assert dbg["referent_repair_applied"] is False


def test_apply_referent_clarity_abstains_on_unsupported_target_switch_category():
    # Drift + single-unambiguous entity that does not match active_interaction_target →
    # ``unsupported_target_switch``; repair must abstain (no semantic target resolution).
    art = minimal_full_referent_artifact(
        single_unambiguous_entity={"entity_id": "npc_runner", "label": "Runner"},
        active_interaction_target="npc_gate",
        referential_ambiguity_class="ambiguous_plural",
        safe_explicit_fallback_labels=[
            {"entity_id": "npc_gate", "safe_explicit_label": "Gate sergeant"},
            {"entity_id": "npc_runner", "safe_explicit_label": "Runner"},
        ],
        allowed_named_references=[
            {"entity_id": "npc_gate", "display_name": "Gate sergeant"},
            {"entity_id": "npc_runner", "display_name": "Runner"},
        ],
        active_entities=[
            {"entity_id": "npc_gate", "display_name": "Gate sergeant", "entity_kind": "npc", "roles": []},
            {"entity_id": "npc_runner", "display_name": "Runner", "entity_kind": "npc", "roles": []},
        ],
        active_entity_order=["npc_gate", "npc_runner"],
        continuity_subject={"entity_id": "npc_gate", "display_name": "Gate sergeant", "source": "t"},
        interaction_target_continuity={
            "prior_target_id": "npc_runner",
            "current_target_id": "npc_gate",
            "signal_target_id": "npc_runner",
            "target_visible": True,
            "drift_detected": True,
            "signal_sources": ["session_interaction.active_interaction_target_id"],
        },
    )
    gm = {"prompt_context": {"referent_tracking": art}}
    text, dbg, _ = _apply_referent_clarity_emission_layer("They disagree.", gm_output=gm)
    assert text == "They disagree."
    assert dbg["referent_repair_applied"] is False
    assert "unsupported_target_switch" in dbg.get("referent_violation_categories", [])
