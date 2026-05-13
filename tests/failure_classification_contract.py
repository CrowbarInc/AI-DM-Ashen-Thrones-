"""Canonical replay failure classification contract.

This module is the public taxonomy lock for the replay-side failure dashboard.
Classifier rules may evolve, but new categories, owners, severities, tags, or
row fields should be added here deliberately with tests.
"""
from __future__ import annotations

from game.final_emission_meta import OPENING_FALLBACK_OWNER_BUCKETS

ALLOWED_FAILURE_CATEGORIES: frozenset[str] = frozenset(
    {
        "route",
        "speaker",
        "fallback",
        "emission",
        "semantic_mutation",
        "replay_drift",
        "projection",
        "validator",
        "evaluator",
        "continuity",
        "normalization",
        "sanitizer",
    }
)

ALLOWED_PRIMARY_OWNERS: frozenset[str] = frozenset(
    {
        "route",
        "speaker",
        "fallback",
        "emission",
        "semantic_mutation",
        "replay",
        "projection",
        "validator",
        "evaluator",
        "continuity",
        "normalization",
        "sanitizer",
        "upstream_prepared_emission",
    }
)

ALLOWED_SECONDARY_OWNERS: frozenset[str] = ALLOWED_PRIMARY_OWNERS | frozenset({"planner"})
ALLOWED_FAILURE_OWNERS: frozenset[str] = ALLOWED_PRIMARY_OWNERS | ALLOWED_SECONDARY_OWNERS

ALLOWED_FAILURE_SEVERITIES: frozenset[str] = frozenset({"critical", "high", "medium", "low"})

ALLOWED_REPLAY_TAGS: frozenset[str] = frozenset(
    {
        "exact_drift",
        "structural_drift",
        "semantic_drift",
        "missing_observation",
        "dotted_path_mismatch",
        "route_mismatch",
        "missing_route_metadata",
        "speaker_mismatch",
        "fallback_source_mismatch",
        "fallback_family_mismatch",
        "response_type_repair_mismatch",
        "scaffold_leakage",
        "post_gate_mutation",
        "continuity_break",
        "semantic_mutation",
        "evaluator_failure",
        "evaluator_warning",
    }
)

EXPERIMENTAL_REPLAY_TAG_PREFIX = "experimental:"

ALLOWED_SOURCE_FAMILY_TAGS: frozenset[str] = frozenset(
    {
        "api_route",
        "interaction_context",
        "speaker_contract",
        "dialogue_social_plan",
        "interaction_continuity",
        "final_emission_gate",
        "final_emission_meta",
        "response_type",
        "fallback_behavior",
        "strict_social_emission",
        "opening_fallback",
        "upstream_prepared_emission",
        "output_sanitizer",
        "stage_diff",
        "schema_contracts",
        "state_authority",
        "scenario_spine_eval",
        "playability_eval",
        "narrative_authenticity_eval",
        "behavioral_eval",
        "golden_replay_projection",
    }
)

ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS: frozenset[str] = OPENING_FALLBACK_OWNER_BUCKETS

ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS: frozenset[str] = frozenset(
    {
        "answer_upstream_prepared_repair",
        "action_outcome_upstream_prepared_repair",
        "strict_social_dialogue_repair",
        "dialogue_minimal_repair",
    }
)

LEGACY_RESPONSE_TYPE_REPAIR_KINDS: frozenset[str] = frozenset({"thin_answer"})

REQUIRED_CLASSIFICATION_FIELDS: frozenset[str] = frozenset(
    {
        "scenario_id",
        "turn_index",
        "category",
        "severity",
        "primary_owner",
        "source_family",
        "replay_tags",
        "field_path",
        "expected",
        "actual",
        "reason",
        "unavailable_fields",
        "raw_signal_refs",
        "classification_confidence",
        "investigate_first",
    }
)

OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS: frozenset[str] = frozenset(
    {
        "secondary_owner",
        "final_text_hash",
        "route_kind",
        "selected_speaker_id",
        "canonical_target_actor_id",
        "final_emitted_source",
        "final_emission_mutation_lineage",
        "fallback_family",
        "fallback_temporal_frame",
        "opening_fallback_owner_bucket",
        "upstream_prepared_emission_used",
        "upstream_prepared_emission_valid",
        "upstream_prepared_emission_source",
        "upstream_prepared_emission_reject_reason",
        "prepared_emission_owner",
        "response_type_required",
        "response_type_repair_used",
        "response_type_repair_kind",
        "post_gate_mutation_detected",
        "emission_sublayer",
        "repair_kind",
        "mutation_source",
        "missing_source_kind",
        "sanitizer_mode",
        "sanitizer_event_count",
        "sanitizer_changed_count",
        "sanitizer_rewrite_used",
        "sanitizer_empty_fallback_used",
        "sanitizer_empty_fallback_source",
        "sanitizer_empty_fallback_owner",
        "sanitizer_lineage_mode",
        "sanitizer_lineage_changed_count",
        "sanitizer_lineage_dropped_count",
        "sanitizer_lineage_empty_fallback_used",
        "sanitizer_lineage_legacy_rewrite_active",
        "sanitizer_strict_social_fallback_used",
        "sanitizer_strict_social_selection_owner",
        "sanitizer_strict_social_prose_owner",
        "sanitizer_strict_social_source",
    }
)

ALLOWED_MISSING_SOURCE_KINDS: frozenset[str] = frozenset(
    {
        "projection_missing_raw_present",
        "runtime_missing_raw_absent",
        "normalized_view_missing_raw_present",
        "unknown_missing_source",
    }
)

ALLOWED_EMISSION_SUBLAYERS: frozenset[str] = frozenset(
    {
        "response_type",
        "fallback_behavior",
        "strict_social_replacement",
        "speaker_contract_enforcement",
        "interaction_continuity",
        "sanitizer",
        "sanitizer.empty_fallback",
        "opening_fallback",
        "upstream_prepared_emission",
        "sealed_gate",
        "final_emission.finalize_packaging",
        "final_emission.finalize_route_illegal_strip",
        "terminal_fallback",
        "emission.post_gate_mutation_unknown",
    }
)

MAJOR_OWNER_INVESTIGATION_TARGETS: dict[str, str] = {
    "route": "game/interaction_context.py",
    "speaker": "game/speaker_contract_enforcement.py",
    "fallback": "game/final_emission_gate.py",
    "emission": "game/final_emission_gate.py",
    "semantic_mutation": "game/stage_diff_telemetry.py",
    "replay": "tests/helpers/golden_replay.py",
    "projection": "tests/helpers/golden_replay.py",
    "validator": "game/final_emission_validators.py",
    "evaluator": "game/scenario_spine_eval.py",
    "continuity": "game/interaction_context.py",
    "normalization": "game/final_emission_meta.py",
    "sanitizer": "game/output_sanitizer.py",
    "upstream_prepared_emission": "game/final_emission_gate.py",
}
