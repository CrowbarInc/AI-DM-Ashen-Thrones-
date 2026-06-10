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
    classify_replay_failure,
    validate_failure_classification_row,
)
from tests.helpers.golden_replay_projection import (
    protected_classifier_evidence_excluded_paths,
    protected_classifier_evidence_field_paths,
    protected_observation_drift_bucket,
    protected_observation_field_paths,
    protected_observation_field_registry,
    project_turn_observation,
)
from tests.helpers.opening_fallback_evidence import (
    OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
    fail_closed_opening_observed_fields,
    successful_opening_observed_fields,
)
from tests.helpers.replay_observed_row_fixtures import observed_failure_row


def observed_opening_fallback_row(*, owner_bucket: bool = False, **overrides: Any) -> dict[str, Any]:
    """Return observed-row evidence for canonical successful opening fallback."""
    return observed_failure_row(**successful_opening_observed_fields(include_owner_bucket=owner_bucket, **overrides))


def observed_fail_closed_opening_fallback_row(*, owner_bucket: bool = False, **overrides: Any) -> dict[str, Any]:
    """Return observed-row evidence for sealed/fail-closed opening fallback."""
    return observed_failure_row(**fail_closed_opening_observed_fields(include_owner_bucket=owner_bucket, **overrides))


def observed_legacy_opening_fallback_row(**overrides: Any) -> dict[str, Any]:
    """Return observed-row evidence for legacy compatibility-local opening fallback."""
    return observed_failure_row(
        **successful_opening_observed_fields(
            opening_fallback_authorship_source=OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
            **overrides,
        )
    )


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


def replay_drift_row(
    field_path: str,
    *,
    expected: Any,
    actual: Any,
    reason: str = "exact value mismatch",
    drift_bucket: str = "structural_drift",
) -> dict[str, Any]:
    """Build one replay drift row dict for classifier/dashboard probes."""
    return {
        "field_path": field_path,
        "expected": expected,
        "actual": actual,
        "reason": reason,
        "drift_bucket": drift_bucket,
    }


def speaker_mismatch_drift_row(*, expected: str = "runner", actual: str = "guard") -> dict[str, Any]:
    """Shared selected-speaker mismatch drift row for dashboard/classifier probes."""
    return replay_drift_row("selected_speaker_id", expected=expected, actual=actual)


def global_fallback_source_drift_row(
    *,
    expected: Any = "generated_candidate",
    actual: Any = "global_scene_fallback",
    reason: str = "exact value mismatch",
) -> dict[str, Any]:
    """Shared final-emitted-source fallback drift row for dashboard/classifier probes."""
    return replay_drift_row("final_emitted_source", expected=expected, actual=actual, reason=reason)


def forbidden_global_fallback_source_drift_row() -> dict[str, Any]:
    """Shared forbidden global-scene-fallback drift row for classifier routing probes."""
    return global_fallback_source_drift_row(
        expected="anything except 'global_scene_fallback'",
        reason="forbidden value observed",
    )


def scaffold_leakage_drift_row(*, reason: str = "scaffold leakage mismatch") -> dict[str, Any]:
    """Shared scaffold-leakage drift row for dashboard/classifier probes."""
    return replay_drift_row(
        "scaffold_leakage",
        expected=False,
        actual=True,
        reason=reason,
        drift_bucket="semantic_drift",
    )


def response_type_repair_drift_row(*, reason: str = "exact value mismatch") -> dict[str, Any]:
    """Shared response-type repair drift row for dashboard/classifier probes."""
    return replay_drift_row("response_type_repair_used", expected=False, actual=True, reason=reason)


def projection_unavailable_drift_row(
    field_path: str,
    *,
    expected: Any,
    actual: Any = None,
    reason: str = "unexpected unavailable field",
) -> dict[str, Any]:
    """Shared projection-unavailable drift row for dashboard/classifier probes."""
    return replay_drift_row(field_path, expected=expected, actual=actual, reason=reason)


def post_gate_mutation_drift_row() -> dict[str, Any]:
    """Shared post-gate mutation drift row for dashboard/classifier probes."""
    return replay_drift_row("post_gate_mutation_detected", expected=False, actual=True)


def opening_recovered_drift_row() -> dict[str, Any]:
    """Shared opening-recovered drift row for opening fallback classifier probes."""
    return replay_drift_row("opening_recovered_via_fallback", expected=False, actual=True)


def route_mismatch_drift_row(*, expected: str, actual: str) -> dict[str, Any]:
    """Shared route-kind mismatch drift row for dashboard/classifier probes."""
    return replay_drift_row("route_kind", expected=expected, actual=actual)


def semantic_text_fragment_drift_row(*, expected: str, actual: str) -> dict[str, Any]:
    """Shared final-text semantic fragment drift row for dashboard/classifier probes."""
    return replay_drift_row(
        "final_text",
        expected=expected,
        actual=actual,
        reason="required text fragment missing",
        drift_bucket="semantic_drift",
    )


def exact_value_drift_row(
    field_path: str,
    *,
    expected: Any,
    actual: Any,
    reason: str = "exact value mismatch",
    drift_bucket: str = "structural_drift",
) -> dict[str, Any]:
    """Shared exact-value drift row for dashboard/classifier probes."""
    return replay_drift_row(
        field_path,
        expected=expected,
        actual=actual,
        reason=reason,
        drift_bucket=drift_bucket,
    )


def classify_replay_probe_row(
    *,
    observed_turn: Mapping[str, Any],
    drift_row: Mapping[str, Any],
    scenario_id: str,
    turn_index: int = 0,
) -> FailureClassification:
    """Classify one replay probe turn into a single dashboard row."""
    rows = classify_replay_failure(
        scenario_id=scenario_id,
        turn_index=turn_index,
        observed_turn=observed_turn,
        drift_rows=[drift_row],
    )
    if not rows:
        raise AssertionError("classify_replay_probe_row expected one classified row")
    return rows[0]


def known_failure_categories() -> tuple[str, ...]:
    """Return contract-locked failure categories in stable order."""
    return tuple(sorted(ALLOWED_FAILURE_CATEGORIES))


def classifier_evidence_field_paths() -> frozenset[str]:
    """Return the contract-locked classifier evidence field paths."""
    return frozenset(CLASSIFIER_EVIDENCE_FIELDS)


def protected_replay_observation_field_paths() -> tuple[str, ...]:
    """Return protected golden replay observation field paths via the sync facade."""
    return protected_observation_field_paths()


def protected_replay_classifier_evidence_field_paths() -> frozenset[str]:
    """Return protected classifier evidence paths derived from protected replay projection."""
    return protected_classifier_evidence_field_paths()


def project_replay_turn_observation(turn_payload: Mapping[str, Any]) -> dict[str, Any]:
    """Project a replay-shaped turn payload through the acceptance projection adapter."""
    return project_turn_observation(turn_payload)


def failure_dashboard_evidence_manifest() -> tuple[tuple[str, str], ...]:
    """Return the contract-owned dashboard Evidence-column manifest."""
    from tests.failure_classification_contract import FAILURE_DASHBOARD_EVIDENCE_MANIFEST

    return FAILURE_DASHBOARD_EVIDENCE_MANIFEST


def failure_dashboard_evidence_row_keys() -> tuple[str, ...]:
    """Return dashboard Evidence-column row keys in contract order."""
    from tests.failure_classification_contract import FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS

    return FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS


def failure_dashboard_evidence_labels() -> tuple[str, ...]:
    """Return dashboard Evidence-column labels in contract order."""
    from tests.failure_classification_contract import FAILURE_DASHBOARD_EVIDENCE_LABELS

    return FAILURE_DASHBOARD_EVIDENCE_LABELS


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
        "protected_classifier_evidence_count": len(protected_replay_classifier_evidence_field_paths()),
        "protected_classifier_evidence_excluded_count": len(protected_classifier_evidence_excluded_paths()),
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


_EXPECTED_FAILURE_DASHBOARD_EVIDENCE_COUNT = 29


def dashboard_evidence_manifest_misalignments() -> list[str]:
    """Return dashboard evidence manifest drift messages; empty when AK3/AO3-locked."""
    from tests.failure_classification_contract import (
        FAILURE_DASHBOARD_EVIDENCE_LABELS as contract_labels,
        FAILURE_DASHBOARD_EVIDENCE_MANIFEST as contract_manifest,
        FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS as contract_row_keys,
        failure_dashboard_evidence_manifest,
    )
    from tests.helpers.failure_dashboard_report import (
        FAILURE_DASHBOARD_EVIDENCE_LABELS as dashboard_labels,
        FAILURE_DASHBOARD_EVIDENCE_MANIFEST as dashboard_manifest,
        FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS as dashboard_row_keys,
    )

    misalignments: list[str] = []

    if failure_dashboard_evidence_manifest() != contract_manifest:
        misalignments.append("failure_dashboard_evidence_manifest() must return FAILURE_DASHBOARD_EVIDENCE_MANIFEST")

    if dashboard_manifest != contract_manifest:
        misalignments.append(
            "failure_dashboard_report must re-export contract FAILURE_DASHBOARD_EVIDENCE_MANIFEST unchanged"
        )
    if dashboard_row_keys != contract_row_keys:
        misalignments.append(
            "failure_dashboard_report must re-export contract FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS unchanged"
        )
    if dashboard_labels != contract_labels:
        misalignments.append(
            "failure_dashboard_report must re-export contract FAILURE_DASHBOARD_EVIDENCE_LABELS unchanged"
        )

    manifest_keys = tuple(row_key for _label, row_key in contract_manifest)
    if manifest_keys != contract_row_keys:
        misalignments.append("FAILURE_DASHBOARD_EVIDENCE_ROW_KEYS must match manifest row keys")

    if len(contract_row_keys) != _EXPECTED_FAILURE_DASHBOARD_EVIDENCE_COUNT:
        misalignments.append(
            f"dashboard evidence manifest must contain {_EXPECTED_FAILURE_DASHBOARD_EVIDENCE_COUNT} row keys, "
            f"got {len(contract_row_keys)}"
        )

    dashboard_only = sorted(set(contract_row_keys) - CLASSIFIER_EVIDENCE_FIELDS)
    if dashboard_only:
        misalignments.append(f"dashboard evidence keys outside classifier evidence: {dashboard_only!r}")

    return misalignments


def classifier_evidence_manifest_misalignments() -> list[str]:
    """Return manifest drift messages; empty when AK2/AO2 evidence sets are locked."""
    misalignments: list[str] = []

    if CLASSIFIER_EVIDENCE_FIELDS != OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS:
        misalignments.append(
            "CLASSIFIER_EVIDENCE_FIELDS must equal OPTIONAL_CLASSIFICATION_EVIDENCE_FIELDS"
        )

    derived_protected_overlap = protected_classifier_evidence_field_paths()
    if PROTECTED_CLASSIFIER_EVIDENCE_FIELDS != derived_protected_overlap:
        misalignments.append(
            "PROTECTED_CLASSIFIER_EVIDENCE_FIELDS must equal protected_classifier_evidence_field_paths(); "
            f"contract_only={sorted(PROTECTED_CLASSIFIER_EVIDENCE_FIELDS - derived_protected_overlap)!r} "
            f"derived_only={sorted(derived_protected_overlap - PROTECTED_CLASSIFIER_EVIDENCE_FIELDS)!r}"
        )

    if len(PROTECTED_CLASSIFIER_EVIDENCE_FIELDS) != 32:
        misalignments.append(
            f"PROTECTED_CLASSIFIER_EVIDENCE_FIELDS must contain 32 fields, got {len(PROTECTED_CLASSIFIER_EVIDENCE_FIELDS)}"
        )
    if len(CLASSIFIER_EVIDENCE_EXTENSION_FIELDS) != 16:
        misalignments.append(
            f"CLASSIFIER_EVIDENCE_EXTENSION_FIELDS must contain 16 fields, got {len(CLASSIFIER_EVIDENCE_EXTENSION_FIELDS)}"
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

    excluded_only = protected_classifier_evidence_excluded_paths() - protected_flat_paths
    if excluded_only:
        misalignments.append(
            "protected classifier evidence exclusions must be flat protected paths; "
            f"invalid_exclusions={sorted(excluded_only)!r}"
        )
    ineligible_flat = protected_flat_paths - derived_protected_overlap
    if ineligible_flat != protected_classifier_evidence_excluded_paths():
        misalignments.append(
            "protected classifier evidence exclusions must equal flat protected paths not in overlap; "
            f"expected_excluded={sorted(protected_classifier_evidence_excluded_paths())!r} "
            f"actual_ineligible={sorted(ineligible_flat)!r}"
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
