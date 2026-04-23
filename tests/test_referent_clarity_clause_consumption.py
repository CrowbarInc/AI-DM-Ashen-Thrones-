"""N5 Block C: read-side use of ``clause_referent_plan`` (validators/repairs) and ``referent_clause_prompt_hints`` (prompt)."""

from __future__ import annotations

import copy

import pytest

from game.final_emission_repairs import _apply_referent_clarity_emission_layer
from game.final_emission_validators import validate_referent_clarity
from game.prompt_context import _project_clause_referent_prompt_hints
from tests.helpers.objective7_referent_fixtures import minimal_full_referent_artifact, referent_compact_mirror

pytestmark = pytest.mark.unit


def _two_npc_gate_fixture_core() -> dict:
    """Shared visibility + label rows for multi-NPC clause tests."""
    return {
        "continuity_subject": {"entity_id": "npc_runner", "display_name": "Runner", "source": "test"},
        "safe_explicit_fallback_labels": [
            {"entity_id": "npc_gate", "safe_explicit_label": "Gate sergeant"},
            {"entity_id": "npc_runner", "safe_explicit_label": "Runner"},
        ],
        "allowed_named_references": [
            {"entity_id": "npc_gate", "display_name": "Gate sergeant"},
            {"entity_id": "npc_runner", "display_name": "Runner"},
        ],
        "active_entities": [
            {"entity_id": "npc_gate", "display_name": "Gate sergeant", "entity_kind": "npc", "roles": []},
            {"entity_id": "npc_runner", "display_name": "Runner", "entity_kind": "npc", "roles": []},
        ],
        "active_entity_order": ["npc_gate", "npc_runner"],
    }


def _clause_row_single_label_speaker() -> dict:
    return {
        "clause_id": "n5:speaker_subject:0",
        "clause_kind": "speaker_subject",
        "subject_candidate_ids": ["npc_gate"],
        "object_candidate_ids": [],
        "preferred_subject_id": "npc_gate",
        "preferred_object_id": None,
        "allowed_explicit_labels": ["Gate sergeant"],
        "risky_pronoun_buckets": ["he_him"],
        "target_switch_sensitive": False,
        "ambiguity_class": "ambiguous_plural",
    }


def test_clause_plan_authorized_single_label_allows_bounded_repair_when_artifact_ambiguous() -> None:
    """Two global safe rows (no deterministic artifact label) + one tight clause row with one label."""
    art = minimal_full_referent_artifact(
        single_unambiguous_entity=None,
        referential_ambiguity_class="ambiguous_plural",
        **_two_npc_gate_fixture_core(),
        clause_referent_plan=[_clause_row_single_label_speaker()],
    )
    gm = {"prompt_context": {"referent_tracking": art}}
    text, dbg, _ = _apply_referent_clarity_emission_layer("They wait.", gm_output=gm)
    assert text.startswith("Gate sergeant")
    assert dbg["referent_repair_applied"] is True
    assert dbg.get("referent_repair_label_source") == "clause_referent_plan"


def test_clause_plan_risky_row_without_authorized_label_skips_repair() -> None:
    art = minimal_full_referent_artifact(
        single_unambiguous_entity=None,
        referential_ambiguity_class="ambiguous_plural",
        **_two_npc_gate_fixture_core(),
        clause_referent_plan=[
            {
                **_clause_row_single_label_speaker(),
                "allowed_explicit_labels": [],
            }
        ],
    )
    gm = {"prompt_context": {"referent_tracking": art}}
    text, dbg, _ = _apply_referent_clarity_emission_layer("They disagree.", gm_output=gm)
    assert text == "They disagree."
    assert dbg["referent_repair_applied"] is False


def test_target_switch_sensitive_clause_without_explicit_triggers_category() -> None:
    art = minimal_full_referent_artifact(
        single_unambiguous_entity=None,
        referential_ambiguity_class="ambiguous_plural",
        interaction_target_continuity={
            "prior_target_id": "npc_runner",
            "current_target_id": "npc_gate",
            "signal_target_id": "npc_runner",
            "target_visible": True,
            "drift_detected": True,
            "signal_sources": ["session_interaction.active_interaction_target_id"],
        },
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
        clause_referent_plan=[
            {
                "clause_id": "n5:interaction_target:0",
                "clause_kind": "interaction_target",
                "subject_candidate_ids": ["npc_gate"],
                "object_candidate_ids": ["npc_gate"],
                "preferred_subject_id": "npc_gate",
                "preferred_object_id": "npc_gate",
                "allowed_explicit_labels": [],
                "risky_pronoun_buckets": ["they_them"],
                "target_switch_sensitive": True,
                "ambiguity_class": "ambiguous_singular",
            }
        ],
    )
    r = validate_referent_clarity("He waits.", referent_tracking=art, referent_tracking_compact=None)
    assert "clause_target_switch_sensitive_without_authorized_explicit" in r["referent_violation_categories"]


def test_compact_only_path_no_repair_even_with_clause_plan_on_missing_full() -> None:
    gm = {
        "prompt_context": {},
        "_gate_turn_packet_cache": {
            "referent_tracking_compact": referent_compact_mirror(
                referential_ambiguity_class="ambiguous_singular",
                ambiguity_risk=80,
            )
        },
    }
    text, dbg, _ = _apply_referent_clarity_emission_layer("They wait.", gm_output=gm)
    assert text == "They wait."
    assert dbg["referent_validation_input_source"] == "packet_compact"
    assert dbg.get("referent_repair_skipped_reason") == "limited_input_no_full_artifact"


def test_no_full_artifact_safe_skip_validate() -> None:
    r = validate_referent_clarity("They wait.", referent_tracking=None, referent_tracking_compact=None)
    assert r["referent_validation_input_source"] == "missing"
    assert r["referent_validation_ran"] is False


def test_validate_repair_and_prompt_projection_do_not_mutate_referent_artifact() -> None:
    """Clause-driven paths are read-side over the full artifact (no in-place edits)."""
    art = minimal_full_referent_artifact(
        single_unambiguous_entity=None,
        referential_ambiguity_class="ambiguous_plural",
        **_two_npc_gate_fixture_core(),
        clause_referent_plan=[_clause_row_single_label_speaker()],
    )
    frozen = copy.deepcopy(art)
    validate_referent_clarity("They wait.", referent_tracking=art, referent_tracking_compact=None)
    assert art == frozen
    _project_clause_referent_prompt_hints(art)
    assert art == frozen
    gm = {"prompt_context": {"referent_tracking": art}}
    _apply_referent_clarity_emission_layer("They wait.", gm_output=gm)
    assert art == frozen


def test_prompt_projection_is_compact_and_json_safe() -> None:
    art = minimal_full_referent_artifact(
        clause_referent_plan=[
            _clause_row_single_label_speaker(),
            {
                "clause_id": "n5:interaction_target:0",
                "clause_kind": "interaction_target",
                "subject_candidate_ids": ["npc_gate"],
                "object_candidate_ids": ["npc_gate"],
                "preferred_subject_id": "npc_gate",
                "preferred_object_id": "npc_gate",
                "allowed_explicit_labels": ["Gate sergeant"],
                "risky_pronoun_buckets": ["they_them"],
                "target_switch_sensitive": True,
                "ambiguity_class": "ambiguous_singular",
            },
        ],
    )
    hints = _project_clause_referent_prompt_hints(art)
    assert hints is not None
    assert len(hints) <= 4
    for row in hints:
        assert set(row.keys()) <= {
            "clause_id",
            "clause_kind",
            "ambiguity_class",
            "target_switch_sensitive",
            "explicit_anchor_preferred",
            "risky_pronoun_buckets",
            "allowed_explicit_labels",
        }
        assert "narration" not in str(row).lower()
