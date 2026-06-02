"""Branch-local contract ↔ classifier alignment checks (Cycle T2).

Centralizes taxonomy sync assertions so contract constant changes and classifier
rule tables stay aligned without scattering duplicate checks across test files.
"""
from __future__ import annotations

from typing import Any, Mapping, NotRequired, Sequence, get_origin, get_type_hints

from game.final_emission_meta import (
    SEALED_FALLBACK_OWNER_SEALED_GATE,
)
from tests.failure_classification_contract import (
    ALLOWED_CLASSIFICATION_ROW_FIELDS,
    ALLOWED_FAILURE_CATEGORIES,
    ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS,
    ALLOWED_PRIMARY_OWNERS,
    ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS,
    ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS,
    ALLOWED_SECONDARY_OWNERS,
    ALLOWED_SOURCE_FAMILY_TAGS,
    ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS,
    CLASSIFIER_EVIDENCE_EXTENSION_FIELDS,
    CLASSIFIER_EVIDENCE_FIELDS,
    LEGACY_RESPONSE_TYPE_REPAIR_KINDS,
    MAJOR_OWNER_INVESTIGATION_TARGETS,
    OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS,
    PROTECTED_CLASSIFIER_EVIDENCE_FIELDS,
    REQUIRED_CLASSIFICATION_FIELDS,
)
from tests.helpers.failure_classifier import (
    CATEGORY_RULES,
    FailureClassification,
    INVESTIGATION_TARGETS,
    PRIMARY_OWNER_RULES,
    SECONDARY_OWNER_RULES,
    validate_failure_classification_row,
)
from tests.helpers.golden_replay_projection import (
    protected_observation_drift_bucket,
    protected_observation_field_paths,
    protected_observation_field_registry,
)
from tests.helpers.opening_fallback_evidence import (
    OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
    fail_closed_opening_observed_fields,
    successful_opening_observed_fields,
)


def observed_failure_row(**overrides: Any) -> dict[str, Any]:
    """Return a classifier-shaped synthetic observed replay row."""
    row: dict[str, Any] = {
        "scenario_id": "probe",
        "turn_index": 0,
        "final_text": "The runner answers.",
        "final_text_hash": "hash123",
        "route_kind": "dialogue",
        "selected_speaker_id": "runner",
        "final_emitted_source": "generated_candidate",
        "fallback_family": None,
        "fallback_temporal_frame": None,
        "opening_fallback_owner_bucket": None,
        "sealed_fallback_owner_bucket": None,
        "visibility_fallback_owner_bucket": None,
        "visibility_replacement_applied": None,
        "visibility_fallback_pool": None,
        "visibility_fallback_kind": None,
        "response_type_required": "dialogue_response",
        "response_type_repair_used": False,
        "response_type_repair_kind": None,
        "post_gate_mutation_detected": False,
        "strict_social_active": False,
        "speaker_contract_enforcement_reason": None,
        "fallback_behavior_repaired": False,
        "fallback_behavior_repair_kind": None,
        "sanitizer_mode": None,
        "sanitizer_event_count": None,
        "sanitizer_changed_count": None,
        "sanitizer_rewrite_used": None,
        "unavailable": [],
        "trace": {
            "canonical_entry": {"target_actor_id": "runner"},
            "social_contract_trace": {"route_selected": "dialogue"},
        },
    }
    row.update(overrides)
    return row


def observed_opening_fallback_row(*, owner_bucket: bool = False, **overrides: Any) -> dict[str, Any]:
    """Return observed-row evidence for canonical successful opening fallback."""
    return observed_failure_row(**successful_opening_observed_fields(include_owner_bucket=owner_bucket, **overrides))


def observed_fail_closed_opening_fallback_row(*, owner_bucket: bool = False, **overrides: Any) -> dict[str, Any]:
    """Return observed-row evidence for sealed/fail-closed opening fallback."""
    return observed_failure_row(**fail_closed_opening_observed_fields(include_owner_bucket=owner_bucket, **overrides))


def observed_legacy_opening_fallback_row(**overrides: Any) -> dict[str, Any]:
    """Return observed-row evidence for legacy compatibility-local opening fallback."""
    fields = {
        "final_emitted_source": "opening_deterministic_fallback",
        "response_type_repair_kind": "opening_deterministic_fallback",
        "opening_recovered_via_fallback": True,
        "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
        "fallback_family": "scene_opening",
    }
    fields.update(overrides)
    return observed_failure_row(**fields)


def observed_global_replacement_row(**overrides: Any) -> dict[str, Any]:
    """Return observed-row evidence for global/gate terminal replacement."""
    fields = {
        "final_emitted_source": "global_scene_fallback",
        "fallback_family": "gate_terminal_repair",
    }
    fields.update(overrides)
    return observed_failure_row(**fields)


def observed_social_fallback_row(**overrides: Any) -> dict[str, Any]:
    """Return observed-row evidence for strict-social fallback replacement probes."""
    fields = {
        "strict_social_active": True,
        "final_emitted_source": "strict_social_visibility_minimal",
    }
    fields.update(overrides)
    return observed_failure_row(**fields)


def observed_sealed_replacement_row(**overrides: Any) -> dict[str, Any]:
    """Return observed-row evidence for sealed/global replacement owner-bucket checks."""
    fields = {"sealed_fallback_owner_bucket": SEALED_FALLBACK_OWNER_SEALED_GATE}
    fields.update(overrides)
    return observed_global_replacement_row(**fields)


def observed_visibility_replacement_row(**overrides: Any) -> dict[str, Any]:
    """Return observed-row evidence for visibility replacement owner-bucket checks."""
    fields = {
        "final_emitted_source": "global_scene_fallback",
        "visibility_fallback_owner_bucket": "sealed-gate",
        "visibility_replacement_applied": True,
        "visibility_fallback_pool": "global_scene_narrative",
        "visibility_fallback_kind": "narrative_safe_fallback",
    }
    fields.update(overrides)
    return observed_failure_row(**fields)


def observed_sanitizer_row(**overrides: Any) -> dict[str, Any]:
    """Return observed-row evidence for sanitizer-classified failure probes."""
    fields = {
        "sanitizer_mode": "strip_only",
        "sanitizer_event_count": 2,
        "sanitizer_changed_count": 1,
        "sanitizer_rewrite_used": True,
    }
    fields.update(overrides)
    return observed_failure_row(**fields)


def observed_sanitizer_empty_fallback_row(**overrides: Any) -> dict[str, Any]:
    """Return observed-row evidence for sanitizer empty-fallback ownership probes."""
    fields = {
        "sanitizer_mode": "strip_only",
        "sanitizer_empty_fallback_used": True,
        "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
        "sanitizer_empty_fallback_owner": "output_sanitizer",
        "upstream_prepared_emission_used": False,
        "upstream_prepared_emission_valid": False,
    }
    fields.update(overrides)
    return observed_failure_row(**fields)


def known_failure_categories() -> tuple[str, ...]:
    """Return contract-locked failure categories in stable order."""
    return tuple(sorted(ALLOWED_FAILURE_CATEGORIES))


def known_owner_buckets() -> dict[str, tuple[str, ...]]:
    """Return contract-locked fallback owner bucket taxonomies."""
    return {
        "opening": tuple(sorted(ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS)),
        "sealed": tuple(sorted(ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS)),
        "visibility": tuple(sorted(ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS)),
    }


def expected_investigation_targets() -> dict[str, str]:
    """Derive classifier investigation targets from the public contract."""
    return {
        category: target
        for category, target in MAJOR_OWNER_INVESTIGATION_TARGETS.items()
        if category != "replay"
    } | {"replay_drift": MAJOR_OWNER_INVESTIGATION_TARGETS["replay"]}


def failure_classification_row_contract_fields() -> dict[str, frozenset[str]]:
    """Return contract-locked classifier row field sets for sync and validation."""
    return {
        "required": REQUIRED_CLASSIFICATION_FIELDS,
        "optional_evidence": OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS,
        "allowed": ALLOWED_CLASSIFICATION_ROW_FIELDS,
    }


def failure_classification_typeddict_field_sets() -> tuple[frozenset[str], frozenset[str]]:
    """Return (required, optional) field names from ``FailureClassification`` annotations."""
    required: set[str] = set()
    optional: set[str] = set()
    for name, hint in get_type_hints(FailureClassification, include_extras=True).items():
        if get_origin(hint) is NotRequired:
            optional.add(name)
        else:
            required.add(name)
    return frozenset(required), frozenset(optional)


def failure_classification_row_contract_misalignments() -> list[str]:
    """Return row-contract drift messages; empty when TypedDict matches contract."""
    misalignments: list[str] = []
    contract = failure_classification_row_contract_fields()
    typed_required, typed_optional = failure_classification_typeddict_field_sets()
    allowed_typeddict = typed_required | typed_optional

    if contract["required"] != typed_required:
        misalignments.append(
            "FailureClassification required TypedDict fields must match REQUIRED_CLASSIFICATION_FIELDS; "
            f"missing_from_typeddict={sorted(contract['required'] - typed_required)!r} "
            f"extra_in_typeddict={sorted(typed_required - contract['required'])!r}"
        )
    if contract["optional_evidence"] != typed_optional:
        misalignments.append(
            "FailureClassification NotRequired TypedDict fields must match OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS; "
            f"missing_from_typeddict={sorted(contract['optional_evidence'] - typed_optional)!r} "
            f"extra_in_typeddict={sorted(typed_optional - contract['optional_evidence'])!r}"
        )
    if allowed_typeddict != contract["allowed"]:
        misalignments.append(
            "FailureClassification.__annotations__ must cover required ∪ optional contract fields; "
            f"missing_from_typeddict={sorted(contract['allowed'] - allowed_typeddict)!r} "
            f"extra_in_typeddict={sorted(allowed_typeddict - contract['allowed'])!r}"
        )

    return misalignments


def assert_failure_classification_row_contract_locked() -> None:
    """Assert FailureClassification TypedDict mirrors the public row contract."""
    misalignments = failure_classification_row_contract_misalignments()
    if misalignments:
        joined = "\n".join(f"- {item}" for item in misalignments)
        raise AssertionError(f"failure classification row contract misalignment:\n{joined}")


def classification_contract_summary() -> dict[str, Any]:
    """Compact summary of contract/classifier taxonomy surfaces."""
    buckets = known_owner_buckets()
    rule_categories = {rule[2] for rule in CATEGORY_RULES}
    return {
        "failure_category_count": len(ALLOWED_FAILURE_CATEGORIES),
        "primary_owner_count": len(ALLOWED_PRIMARY_OWNERS),
        "category_rule_count": len(CATEGORY_RULES),
        "category_rule_categories": len(rule_categories),
        "investigation_target_count": len(INVESTIGATION_TARGETS),
        "required_field_count": len(REQUIRED_CLASSIFICATION_FIELDS),
        "opening_owner_bucket_count": len(buckets["opening"]),
        "sealed_owner_bucket_count": len(buckets["sealed"]),
        "visibility_owner_bucket_count": len(buckets["visibility"]),
        "runtime_response_type_repair_kind_count": len(ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS),
        "legacy_response_type_repair_kind_count": len(LEGACY_RESPONSE_TYPE_REPAIR_KINDS),
    }


def expected_failure_classification_row_fields() -> dict[str, tuple[str, ...]]:
    """Return contract-locked required and optional evidence field names for dashboard rows."""
    fields = failure_classification_row_contract_fields()
    return {
        "required": tuple(sorted(fields["required"])),
        "optional_evidence": tuple(sorted(fields["optional_evidence"])),
        "allowed": tuple(sorted(fields["allowed"])),
    }


def failure_dashboard_row_shape_errors(row: Mapping[str, Any]) -> list[str]:
    """Return row-shape validation errors; empty when the row matches the contract."""
    return validate_failure_classification_row(row)


def assert_failure_dashboard_row_shape(row: Mapping[str, Any]) -> None:
    """Assert one classifier/dashboard row satisfies the shared row-shape contract."""
    errors = failure_dashboard_row_shape_errors(row)
    if errors:
        joined = "; ".join(errors)
        raise AssertionError(f"invalid failure dashboard row shape: {joined}")


def protected_observation_registry_summary() -> dict[str, Any]:
    """Compact summary of the protected golden replay observation field registry."""
    registry = protected_observation_field_registry()
    paths = protected_observation_field_paths()
    structural_paths = tuple(
        field.path for field in registry if field.drift_bucket == "structural_drift"
    )
    semantic_paths = tuple(
        field.path for field in registry if field.drift_bucket == "semantic_drift"
    )
    return {
        "protected_field_count": len(registry),
        "structural_field_count": len(structural_paths),
        "semantic_field_count": len(semantic_paths),
        "paths_unique": len(set(paths)) == len(paths),
        "paths_sorted": list(paths) == sorted(paths),
        "fallback_family_bucket": protected_observation_drift_bucket("fallback_family"),
        "scaffold_leakage_bucket": protected_observation_drift_bucket("scaffold_leakage"),
    }


def contract_classifier_misalignments(
    *,
    category_rules: Sequence[tuple[str, tuple[str, ...], str, str]] | None = None,
    primary_owner_rules: Mapping[str, str] | None = None,
    secondary_owner_rules: Mapping[str, str | None] | None = None,
    investigation_targets: Mapping[str, str] | None = None,
) -> list[str]:
    """Return human-readable misalignment messages; empty when aligned."""
    rules = list(category_rules if category_rules is not None else CATEGORY_RULES)
    primary = dict(primary_owner_rules if primary_owner_rules is not None else PRIMARY_OWNER_RULES)
    secondary = dict(secondary_owner_rules if secondary_owner_rules is not None else SECONDARY_OWNER_RULES)
    targets = dict(investigation_targets if investigation_targets is not None else INVESTIGATION_TARGETS)
    expected_targets = expected_investigation_targets()

    misalignments: list[str] = []

    if targets != expected_targets:
        missing = sorted(set(expected_targets) - set(targets))
        extra = sorted(set(targets) - set(expected_targets))
        changed = sorted(
            key
            for key in set(expected_targets) & set(targets)
            if expected_targets[key] != targets[key]
        )
        if missing:
            misalignments.append(f"investigation_targets missing keys: {missing!r}")
        if extra:
            misalignments.append(f"investigation_targets unexpected keys: {extra!r}")
        for key in changed:
            misalignments.append(
                "investigation_targets drift for "
                f"{key!r}: expected {expected_targets[key]!r}, got {targets[key]!r}"
            )

    for rule_name, _needles, category, source_family in rules:
        if category not in ALLOWED_FAILURE_CATEGORIES:
            misalignments.append(
                f"CATEGORY_RULES[{rule_name!r}] category {category!r} not in ALLOWED_FAILURE_CATEGORIES"
            )
        if source_family not in ALLOWED_SOURCE_FAMILY_TAGS:
            misalignments.append(
                f"CATEGORY_RULES[{rule_name!r}] source_family {source_family!r} not in ALLOWED_SOURCE_FAMILY_TAGS"
            )

    for category, owner in primary.items():
        if owner not in ALLOWED_PRIMARY_OWNERS:
            misalignments.append(
                f"PRIMARY_OWNER_RULES[{category!r}] owner {owner!r} not in ALLOWED_PRIMARY_OWNERS"
            )
        if category not in ALLOWED_PRIMARY_OWNERS and category not in ALLOWED_FAILURE_CATEGORIES:
            misalignments.append(
                f"PRIMARY_OWNER_RULES key {category!r} is neither a contract category nor primary owner"
            )

    for category in ALLOWED_FAILURE_CATEGORIES:
        if category not in primary:
            misalignments.append(f"missing PRIMARY_OWNER_RULES entry for category {category!r}")

    for category, owner in secondary.items():
        if owner is not None and owner not in ALLOWED_SECONDARY_OWNERS:
            misalignments.append(
                f"SECONDARY_OWNER_RULES[{category!r}] owner {owner!r} not in ALLOWED_SECONDARY_OWNERS"
            )
        if category not in ALLOWED_FAILURE_CATEGORIES and category not in ALLOWED_PRIMARY_OWNERS:
            misalignments.append(
                f"SECONDARY_OWNER_RULES key {category!r} is neither a contract category nor primary owner"
            )

    rule_categories = {rule[2] for rule in rules}
    for category in sorted(rule_categories):
        if category not in targets:
            misalignments.append(f"missing investigation target for CATEGORY_RULES category {category!r}")

    runtime_kinds = {
        "answer_upstream_prepared_repair",
        "action_outcome_upstream_prepared_repair",
        "strict_social_dialogue_repair",
        "dialogue_minimal_repair",
    }
    if not runtime_kinds <= ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS:
        missing = sorted(runtime_kinds - ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS)
        misalignments.append(f"ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS missing {missing!r}")
    if "thin_answer" not in LEGACY_RESPONSE_TYPE_REPAIR_KINDS:
        misalignments.append("LEGACY_RESPONSE_TYPE_REPAIR_KINDS must include 'thin_answer'")
    if "thin_answer" in ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS:
        misalignments.append("ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS must not include legacy 'thin_answer'")

    if "upstream_prepared_emission" not in ALLOWED_PRIMARY_OWNERS:
        misalignments.append("ALLOWED_PRIMARY_OWNERS must include 'upstream_prepared_emission'")
    if "upstream_prepared_emission" not in ALLOWED_SOURCE_FAMILY_TAGS:
        misalignments.append("ALLOWED_SOURCE_FAMILY_TAGS must include 'upstream_prepared_emission'")

    return misalignments


_EXPECTED_FAILURE_DASHBOARD_EVIDENCE_LABELS: tuple[str, ...] = (
    "sublayer",
    "repair",
    "lineage",
    "opening_authorship",
    "opening_owner",
    "fallback_selection_owner",
    "fallback_content_owner",
    "sealed_owner",
    "visibility_owner",
    "visibility_replaced",
    "visibility_pool",
    "visibility_kind",
    "mutation",
    "missing",
    "sanitizer_mode",
    "sanitizer_events",
    "sanitizer_changed",
    "sanitizer_empty",
    "sanitizer_empty_source",
    "sanitizer_empty_owner",
    "sanitizer_lineage_mode",
    "sanitizer_lineage_changed",
    "sanitizer_lineage_dropped",
    "sanitizer_lineage_empty",
    "sanitizer_lineage_legacy",
    "strict_social_fallback",
    "strict_social_selection_owner",
    "strict_social_prose_owner",
    "strict_social_source",
)


def dashboard_evidence_manifest_misalignments() -> list[str]:
    """Return dashboard evidence manifest drift messages; empty when AK3-locked."""
    from tests.helpers.failure_dashboard_report import (
        FAILURE_DASHBOARD_EVIDENCE_LABELS,
        FAILURE_DASHBOARD_EVIDENCE_MANIFEST,
        FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS,
    )

    misalignments: list[str] = []

    if FAILURE_DASHBOARD_EVIDENCE_LABELS != _EXPECTED_FAILURE_DASHBOARD_EVIDENCE_LABELS:
        misalignments.append(
            "FAILURE_DASHBOARD_EVIDENCE_LABELS drifted from locked dashboard label order"
        )

    manifest_keys = tuple(row_key for _label, row_key in FAILURE_DASHBOARD_EVIDENCE_MANIFEST)
    if manifest_keys != FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS:
        misalignments.append("FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS must match manifest row keys")

    dashboard_only = sorted(set(FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS) - CLASSIFIER_EVIDENCE_FIELDS)
    if dashboard_only:
        misalignments.append(f"dashboard evidence keys outside classifier evidence: {dashboard_only!r}")

    return misalignments


def classifier_evidence_manifest_misalignments() -> list[str]:
    """Return manifest drift messages; empty when AK2 evidence sets are locked."""
    misalignments: list[str] = []

    if CLASSIFIER_EVIDENCE_FIELDS != OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS:
        misalignments.append(
            "CLASSIFIER_EVIDENCE_FIELDS must equal OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS"
        )

    if len(PROTECTED_CLASSIFIER_EVIDENCE_FIELDS) != 32:
        misalignments.append(
            f"PROTECTED_CLASSIFIER_EVIDENCE_FIELDS must contain 32 fields, got {len(PROTECTED_CLASSIFIER_EVIDENCE_FIELDS)}"
        )
    if len(CLASSIFIER_EVIDENCE_EXTENSION_FIELDS) != 15:
        misalignments.append(
            f"CLASSIFIER_EVIDENCE_EXTENSION_FIELDS must contain 15 fields, got {len(CLASSIFIER_EVIDENCE_EXTENSION_FIELDS)}"
        )

    overlap = PROTECTED_CLASSIFIER_EVIDENCE_FIELDS & CLASSIFIER_EVIDENCE_EXTENSION_FIELDS
    if overlap:
        misalignments.append(f"protected overlap and extension sets must be disjoint; overlap={sorted(overlap)!r}")

    if PROTECTED_CLASSIFIER_EVIDENCE_FIELDS | CLASSIFIER_EVIDENCE_EXTENSION_FIELDS != CLASSIFIER_EVIDENCE_FIELDS:
        misalignments.append("CLASSIFIER_EVIDENCE_FIELDS must equal protected overlap | extension")

    protected_flat_paths = {path for path in protected_observation_field_paths() if "." not in path}
    expected_protected_overlap = protected_flat_paths & CLASSIFIER_EVIDENCE_FIELDS
    if PROTECTED_CLASSIFIER_EVIDENCE_FIELDS != expected_protected_overlap:
        misalignments.append(
            "PROTECTED_CLASSIFIER_EVIDENCE_FIELDS must equal flat protected paths ∩ classifier evidence; "
            f"manifest_only={sorted(PROTECTED_CLASSIFIER_EVIDENCE_FIELDS - expected_protected_overlap)!r} "
            f"expected_only={sorted(expected_protected_overlap - PROTECTED_CLASSIFIER_EVIDENCE_FIELDS)!r}"
        )

    misalignments.extend(dashboard_evidence_manifest_misalignments())
    misalignments.extend(failure_classification_row_contract_misalignments())

    return misalignments


def assert_classifier_evidence_manifest_locked() -> None:
    """Assert AK2 classifier evidence manifest matches contract and dashboard surfaces."""
    misalignments = classifier_evidence_manifest_misalignments()
    if misalignments:
        joined = "\n".join(f"- {item}" for item in misalignments)
        raise AssertionError(f"classifier evidence manifest misalignment:\n{joined}")
    assert_failure_classification_row_contract_locked()


def assert_contract_classifier_alignment() -> None:
    """Assert classifier rule tables remain aligned with contract constants."""
    misalignments = contract_classifier_misalignments()
    if misalignments:
        joined = "\n".join(f"- {item}" for item in misalignments)
        raise AssertionError(f"failure classification contract/classifier misalignment:\n{joined}")
    assert_classifier_evidence_manifest_locked()
