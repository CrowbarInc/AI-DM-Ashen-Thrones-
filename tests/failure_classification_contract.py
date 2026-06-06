"""Canonical replay failure classification contract.

This module is the public taxonomy lock for the replay-side failure dashboard.
Classifier rules may evolve, but new categories, owners, severities, tags, or
row fields should be added here deliberately with tests.

Alignment with classifier rule tables is enforced by
``tests.helpers.failure_classification_sync``.
"""
from __future__ import annotations

from game.final_emission_meta import (
    OPENING_FALLBACK_OWNER_BUCKETS,
    SEALED_FALLBACK_OWNER_BUCKETS,
    VISIBILITY_FALLBACK_OWNER_BUCKETS,
)
from tests.helpers.golden_replay_projection import protected_classifier_evidence_field_paths
from tests.helpers.replay_drift_taxonomy import ALLOWED_OWNER_DRIFT_BUCKETS

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

# Single source: runtime/read-side bucket registry in ``game.final_emission_meta``.
ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS: frozenset[str] = OPENING_FALLBACK_OWNER_BUCKETS
ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS: frozenset[str] = SEALED_FALLBACK_OWNER_BUCKETS
ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS: frozenset[str] = VISIBILITY_FALLBACK_OWNER_BUCKETS
ALLOWED_FALLBACK_SELECTION_OWNERS: frozenset[str] = frozenset(
    {
        "game.final_emission_gate",
    }
)
ALLOWED_FALLBACK_CONTENT_OWNERS: frozenset[str] = frozenset(
    {
        "game.final_emission_gate",
        "game.opening_deterministic_fallback",
        "game.social_exchange_emission",
    }
)

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

# Cycle AK2 / AO2 — protected overlap derived from golden replay observation registry.
# ``CLASSIFIER_EVIDENCE_FIELDS`` must stay equal to ``OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS``.
PROTECTED_CLASSIFIER_EVIDENCE_FIELDS: frozenset[str] = protected_classifier_evidence_field_paths()

CLASSIFIER_EVIDENCE_EXTENSION_FIELDS: frozenset[str] = frozenset(
    {
        "canonical_target_actor_id",
        "emission_sublayer",
        "fallback_content_owner",
        "fallback_selection_owner",
        "final_text_hash",
        "missing_source_kind",
        "mutation_source",
        "owner_drift_bucket",
        "post_gate_mutation_detected",
        "prepared_emission_owner",
        "repair_kind",
        "sanitizer_changed_count",
        "sanitizer_event_count",
        "sanitizer_mode",
        "sanitizer_rewrite_used",
        "secondary_owner",
    }
)

CLASSIFIER_EVIDENCE_FIELDS: frozenset[str] = (
    PROTECTED_CLASSIFIER_EVIDENCE_FIELDS | CLASSIFIER_EVIDENCE_EXTENSION_FIELDS
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
        "opening_fallback_authorship_source",
        "opening_fallback_owner_bucket",
        "fallback_selection_owner",
        "fallback_content_owner",
        "sealed_fallback_owner_bucket",
        "visibility_fallback_owner_bucket",
        "visibility_replacement_applied",
        "visibility_fallback_pool",
        "visibility_fallback_kind",
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
        "owner_drift_bucket",
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

if CLASSIFIER_EVIDENCE_FIELDS != OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS:
    _manifest_only = sorted(CLASSIFIER_EVIDENCE_FIELDS - OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS)
    _contract_only = sorted(OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS - CLASSIFIER_EVIDENCE_FIELDS)
    raise AssertionError(
        "CLASSIFIER_EVIDENCE_FIELDS must equal OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS; "
        f"manifest_only={_manifest_only!r} contract_only={_contract_only!r}"
    )

if not PROTECTED_CLASSIFIER_EVIDENCE_FIELDS <= OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS:
    _protected_only = sorted(PROTECTED_CLASSIFIER_EVIDENCE_FIELDS - OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS)
    raise AssertionError(
        "derived PROTECTED_CLASSIFIER_EVIDENCE_FIELDS must be subset of OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS; "
        f"protected_only={_protected_only!r}"
    )

if PROTECTED_CLASSIFIER_EVIDENCE_FIELDS & CLASSIFIER_EVIDENCE_EXTENSION_FIELDS:
    _overlap = sorted(PROTECTED_CLASSIFIER_EVIDENCE_FIELDS & CLASSIFIER_EVIDENCE_EXTENSION_FIELDS)
    raise AssertionError(
        "derived protected overlap and classifier extension fields must be disjoint; "
        f"overlap={_overlap!r}"
    )

# Cycle AK3 / AO3 — dashboard Evidence column manifest (label, classifier row key).
# Row keys are a curated subset of ``CLASSIFIER_EVIDENCE_FIELDS`` surfaced in markdown.
_EXPECTED_FAILURE_DASHBOARD_EVIDENCE_COUNT = 29

FAILURE_DASHBOARD_EVIDENCE_MANIFEST: tuple[tuple[str, str], ...] = (
    ("sublayer", "emission_sublayer"),
    ("repair", "repair_kind"),
    ("lineage", "final_emission_mutation_lineage"),
    ("opening_authorship", "opening_fallback_authorship_source"),
    ("opening_owner", "opening_fallback_owner_bucket"),
    ("fallback_selection_owner", "fallback_selection_owner"),
    ("fallback_content_owner", "fallback_content_owner"),
    ("sealed_owner", "sealed_fallback_owner_bucket"),
    ("visibility_owner", "visibility_fallback_owner_bucket"),
    ("visibility_replaced", "visibility_replacement_applied"),
    ("visibility_pool", "visibility_fallback_pool"),
    ("visibility_kind", "visibility_fallback_kind"),
    ("mutation", "mutation_source"),
    ("missing", "missing_source_kind"),
    ("sanitizer_mode", "sanitizer_mode"),
    ("sanitizer_events", "sanitizer_event_count"),
    ("sanitizer_changed", "sanitizer_changed_count"),
    ("sanitizer_empty", "sanitizer_empty_fallback_used"),
    ("sanitizer_empty_source", "sanitizer_empty_fallback_source"),
    ("sanitizer_empty_owner", "sanitizer_empty_fallback_owner"),
    ("sanitizer_lineage_mode", "sanitizer_lineage_mode"),
    ("sanitizer_lineage_changed", "sanitizer_lineage_changed_count"),
    ("sanitizer_lineage_dropped", "sanitizer_lineage_dropped_count"),
    ("sanitizer_lineage_empty", "sanitizer_lineage_empty_fallback_used"),
    ("sanitizer_lineage_legacy", "sanitizer_lineage_legacy_rewrite_active"),
    ("strict_social_fallback", "sanitizer_strict_social_fallback_used"),
    ("strict_social_selection_owner", "sanitizer_strict_social_selection_owner"),
    ("strict_social_prose_owner", "sanitizer_strict_social_prose_owner"),
    ("strict_social_source", "sanitizer_strict_social_source"),
)

FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS: tuple[str, ...] = tuple(
    row_key for _label, row_key in FAILURE_DASHBOARD_EVIDENCE_MANIFEST
)

FAILURE_DASHBOARD_EVIDENCE_LABELS: tuple[str, ...] = tuple(
    label for label, _row_key in FAILURE_DASHBOARD_EVIDENCE_MANIFEST
)


def failure_dashboard_evidence_manifest() -> tuple[tuple[str, str], ...]:
    """Return the canonical dashboard Evidence-column manifest (AO3)."""
    return FAILURE_DASHBOARD_EVIDENCE_MANIFEST


def _validate_failure_dashboard_evidence_manifest() -> None:
    row_keys = FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS
    if len(row_keys) != len(set(row_keys)):
        duplicates = sorted({key for key in row_keys if row_keys.count(key) > 1})
        raise AssertionError(f"FAILURE_DASHBOARD_EVIDENCE_MANIFEST has duplicate row keys: {duplicates!r}")
    if len(row_keys) != _EXPECTED_FAILURE_DASHBOARD_EVIDENCE_COUNT:
        raise AssertionError(
            f"FAILURE_DASHBOARD_EVIDENCE_MANIFEST must contain {_EXPECTED_FAILURE_DASHBOARD_EVIDENCE_COUNT} "
            f"row keys, got {len(row_keys)}"
        )
    dashboard_only = set(row_keys) - CLASSIFIER_EVIDENCE_FIELDS
    if dashboard_only:
        raise AssertionError(
            "dashboard evidence row keys must be subset of CLASSIFIER_EVIDENCE_FIELDS; "
            f"unexpected={sorted(dashboard_only)!r}"
        )
    if FAILURE_DASHBOARD_EVIDENCE_LABELS != tuple(label for label, _row_key in FAILURE_DASHBOARD_EVIDENCE_MANIFEST):
        raise AssertionError("FAILURE_DASHBOARD_EVIDENCE_LABELS must match manifest label order")


_validate_failure_dashboard_evidence_manifest()

# Cycle AK4 — full classifier/dashboard row field allowlist (required ∪ optional evidence).
ALLOWED_CLASSIFICATION_ROW_FIELDS: frozenset[str] = (
    REQUIRED_CLASSIFICATION_FIELDS | OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS
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
