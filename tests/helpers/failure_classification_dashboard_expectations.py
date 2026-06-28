"""Expected dashboard rows and presentation-structure helpers (CG-2/CG-3).

**Authority:** owns expected presentation structures only; does not define taxonomy.
Registry: ``docs/audits/CG_failure_classification_authority_registry.md``

CG-3 case groups (36 controlled dashboard probes total):

**A — classifier behavior probes** (36): ``CONTROLLED_FAILURE_PROBE_CASES`` /
``split_owner_matrix_controlled_failure_cases``. Routing fields
(``category``, ``primary_owner``, ``secondary_owner``, ``severity``,
``investigate_first``) are **derived** from ``classify_replay_probe_row``;
split-owner owner literals are validated via ``assert_split_owner_matrix_*``
against matrix rows, not duplicated literals.

**B — dashboard presentation goldens**: ``CONTROLLED_PROBE_EVIDENCE_CELLS`` /
``CONTROLLED_FAILURE_DASHBOARD_REPORT_FRAGMENTS`` (family-grouped in this module,
CO11); consumed by ``tests/test_failure_dashboard_controlled_failures.py``;
report section/shape tests in ``tests/test_failure_dashboard_report.py``. These
lock evidence cell formatting, labels, ordering, and markdown report shape.

**C — compatibility probes**: ``SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES`` (BU19
empty guard), module export parity tests, ``record_selected_speaker_protected_failure``
bridge fixture, ``expected_failure_classification_row_fields`` contract re-export.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from tests.helpers.failure_classifier import validate_failure_classification_row
from tests.helpers.failure_classification_alignment import failure_classification_row_contract_fields
from tests.helpers.failure_classification_builders import classify_replay_probe_row
from tests.helpers.opening_fallback_evidence import legacy_compatibility_local_opening_authorship_source
from tests.helpers.failure_classification_split_owner import (
    SPLIT_OWNER_ACCEPTANCE_MATRIX,
    SplitOwnerAcceptanceRow,
    split_owner_matrix_classifier_drift_row,
    split_owner_matrix_legacy,
    split_owner_observed_row_from_matrix_row,
)

# Classifier routing fields derived for behavior probes (Group A).
CLASSIFIER_ROUTING_FIELD_KEYS: tuple[str, ...] = (
    "category",
    "primary_owner",
    "secondary_owner",
    "severity",
    "investigate_first",
)

ControlledFailureProbeCase = tuple[str, dict[str, Any], dict[str, Any]]
ControlledFailureCase = tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]


def derive_classifier_routing_expected(
    case_id: str,
    observed: Mapping[str, Any],
    drift_row: Mapping[str, Any],
    *,
    turn_index: int = 0,
) -> dict[str, Any]:
    """Derive classifier routing fields for a controlled dashboard behavior probe."""
    row = classify_replay_probe_row(
        scenario_id=case_id,
        turn_index=turn_index,
        observed_turn={**observed, "scenario_id": case_id},
        drift_row=drift_row,
    )
    return {key: row[key] for key in CLASSIFIER_ROUTING_FIELD_KEYS if key in row}


def controlled_failure_probe_case(
    case_id: str,
    observed: Mapping[str, Any],
    drift_row: Mapping[str, Any],
) -> ControlledFailureCase:
    """Build one controlled-failure 4-tuple with derived classifier routing expected."""
    return (
        case_id,
        dict(observed),
        dict(drift_row),
        derive_classifier_routing_expected(case_id, observed, drift_row),
    )


def assert_classifier_routing_parity(
    dashboard_row: Mapping[str, Any],
    classifier_row: Mapping[str, Any],
) -> None:
    """Assert dashboard and classifier paths agree on routing fields."""
    for key in CLASSIFIER_ROUTING_FIELD_KEYS:
        assert dashboard_row.get(key) == classifier_row.get(key), (
            f"{key}: dashboard={dashboard_row.get(key)!r} classifier={classifier_row.get(key)!r}"
        )


def split_owner_matrix_dashboard_expected_dict(row: SplitOwnerAcceptanceRow) -> dict[str, Any]:
    """Compatibility wrapper: derive routing expected for a split-owner matrix probe."""
    case_id = row.dashboard_case_id or f"{row.matrix_id}_split_owner"
    observed = split_owner_observed_row_from_matrix_row(row, profile="dashboard_probe")
    drift_row = split_owner_matrix_classifier_drift_row(row)
    return derive_classifier_routing_expected(case_id, observed, drift_row)


def split_owner_matrix_controlled_failure_cases() -> tuple[ControlledFailureCase, ...]:
    """Build dashboard controlled probes for matrix rows with dashboard_case_id."""
    cases: list[ControlledFailureCase] = []
    for row in SPLIT_OWNER_ACCEPTANCE_MATRIX:
        if row.dashboard_case_id is None:
            continue
        cases.append(
            controlled_failure_probe_case(
                row.dashboard_case_id,
                split_owner_observed_row_from_matrix_row(row, profile="dashboard_probe"),
                split_owner_matrix_classifier_drift_row(row),
            )
        )
    return tuple(cases)


def assert_split_owner_matrix_dashboard_expected(
    row: SplitOwnerAcceptanceRow,
    classified: Mapping[str, Any],
) -> None:
    """Assert classified dashboard row matches matrix owner literals."""
    if row.event_kind == "mutation":
        assert classified.get(row.owner_bucket_field) == row.owner_bucket
        if row.repair_kind is not None:
            assert classified.get("repair_kind") == row.repair_kind
        return
    if row.fallback_selection_owner is not None:
        assert classified.get("fallback_selection_owner") == row.fallback_selection_owner
    if row.fallback_content_owner is not None:
        assert classified.get("fallback_content_owner") == row.fallback_content_owner
    if row.owner_bucket_field is not None:
        assert classified.get(row.owner_bucket_field) == row.owner_bucket
    if row.repair_kind is not None:
        assert classified.get("repair_kind") == row.repair_kind


# BU19: empty — every non-legacy row uses "{matrix_id}_split_owner".
SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES: dict[str, tuple[str, str]] = {}


def split_owner_dashboard_case_id_default(matrix_id: str) -> str:
    """Return the canonical dashboard probe id for a matrix row."""
    return f"{matrix_id}_split_owner"


def split_owner_expected_dashboard_case_id(row: SplitOwnerAcceptanceRow) -> str | None:
    """Return the expected dashboard probe id for a matrix row (None when legacy/excluded)."""
    if split_owner_matrix_legacy(row):
        return None
    return split_owner_dashboard_case_id_default(row.matrix_id)


def split_owner_matrix_dashboard_case_id_misalignments() -> list[str]:
    """Return dashboard_case_id drift messages; empty when ids match {matrix_id}_split_owner."""
    misalignments: list[str] = []
    for row in SPLIT_OWNER_ACCEPTANCE_MATRIX:
        expected = split_owner_expected_dashboard_case_id(row)
        if expected is None:
            if row.dashboard_case_id is not None:
                misalignments.append(
                    f"{row.matrix_id!r} is legacy/excluded but dashboard_case_id={row.dashboard_case_id!r}"
                )
            continue
        if row.dashboard_case_id != expected:
            misalignments.append(
                f"{row.matrix_id!r} dashboard_case_id={row.dashboard_case_id!r} "
                f"expected {expected!r}"
            )
    return misalignments


def assert_split_owner_matrix_dashboard_case_id_parity() -> None:
    """Assert every dashboard-covered matrix row uses {matrix_id}_split_owner."""
    misalignments = split_owner_matrix_dashboard_case_id_misalignments()
    if misalignments:
        joined = "\n".join(f"- {item}" for item in misalignments)
        raise AssertionError(f"split-owner dashboard case id parity drift:\n{joined}")


def split_owner_sealed_matrix_rows_requiring_dashboard_probe() -> tuple[SplitOwnerAcceptanceRow, ...]:
    """Return sealed-family matrix rows that must have dashboard controlled probes (BU17)."""
    return tuple(
        row
        for row in SPLIT_OWNER_ACCEPTANCE_MATRIX
        if row.family == "sealed" and not split_owner_matrix_legacy(row)
    )


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


def assert_classification_owner_mapping(
    row: Mapping[str, Any],
    *,
    category: str | None = None,
    primary_owner: str | None = None,
    secondary_owner: str | None = None,
    severity: str | None = None,
    investigate_first: str | None = None,
) -> None:
    """Assert canonical classifier routing fields on one classification row."""
    expectations = {
        "category": category,
        "primary_owner": primary_owner,
        "secondary_owner": secondary_owner,
        "severity": severity,
        "investigate_first": investigate_first,
    }
    for key, expected in expectations.items():
        if expected is not None:
            assert row.get(key) == expected, (
                f"{key}: expected {expected!r}, got {row.get(key)!r}"
            )


def assert_failure_classification_row(row: Mapping[str, Any], **expected_fields: Any) -> None:
    """Assert arbitrary classifier/dashboard row fields match expected values."""
    for key, expected in expected_fields.items():
        assert row.get(key) == expected, (
            f"{key}: expected {expected!r}, got {row.get(key)!r}"
        )


def assert_split_owner_classification(
    row: Mapping[str, Any],
    *,
    category: str | None = None,
    primary_owner: str | None = None,
    secondary_owner: str | None = None,
    severity: str | None = None,
    investigate_first: str | None = None,
    source_family: str | None = None,
    emission_sublayer: str | None = None,
    **extra_fields: Any,
) -> None:
    """Assert split-owner classifier routing plus common owner-family projection fields."""
    assert_classification_owner_mapping(
        row,
        category=category,
        primary_owner=primary_owner,
        secondary_owner=secondary_owner,
        severity=severity,
        investigate_first=investigate_first,
    )
    for key, expected in (
        ("source_family", source_family),
        ("emission_sublayer", emission_sublayer),
    ):
        if expected is not None:
            assert row.get(key) == expected, (
                f"{key}: expected {expected!r}, got {row.get(key)!r}"
            )
    if extra_fields:
        assert_failure_classification_row(row, **extra_fields)


def assert_classifier_dashboard_projection_parity(
    dashboard_row: Mapping[str, Any],
    classifier_row: Mapping[str, Any],
) -> None:
    """Assert dashboard build and direct classifier paths agree on routing fields."""
    assert_classifier_routing_parity(dashboard_row, classifier_row)


# Dashboard evidence column presentation helpers (CO5) ------------------------


def _assert_evidence_in_report(report: str, needle: str, *, present: bool = True) -> None:
    if present:
        assert needle in report, f"expected evidence cell {needle!r} in report"
    else:
        assert needle not in report, f"expected evidence cell {needle!r} absent from report"


def assert_dashboard_evidence_contains(report: str, *needles: str) -> None:
    """Assert dashboard evidence column fragments appear in the rendered report."""
    for needle in needles:
        _assert_evidence_in_report(report, needle, present=True)


def assert_dashboard_evidence_cell(report: str, cell: str, *, present: bool = True) -> None:
    """Assert one compact evidence cell token is present or absent in the report."""
    _assert_evidence_in_report(report, cell, present=present)


def assert_dashboard_evidence_column_present(report: str) -> None:
    """Assert the dashboard markdown includes the Evidence column header."""
    assert_dashboard_evidence_cell(report, "Evidence")


def assert_compact_evidence_field(
    report: str,
    field: str,
    value: str | bool | int,
) -> None:
    """Assert one ``field=value`` token in the dashboard evidence column."""
    if isinstance(value, bool):
        rendered = "True" if value else "False"
    else:
        rendered = str(value)
    assert_dashboard_evidence_cell(report, f"{field}={rendered}")


def assert_prepared_emission_evidence(
    report: str,
    *,
    status: str,
    valid: bool | None = None,
    source: str | None = None,
    reject_reason: str | None = None,
) -> None:
    """Assert ``prepared_emission=`` evidence tokens in the dashboard evidence column."""
    if status == "rejected":
        assert reject_reason is not None, "reject_reason required when status='rejected'"
        assert_dashboard_evidence_cell(
            report,
            f"prepared_emission=rejected reason={reject_reason}",
        )
        return
    if status == "used":
        parts = ["prepared_emission=used"]
        if valid is not None:
            parts.append(f"valid={valid}")
        if source is not None:
            parts.append(f"source={source}")
        assert_dashboard_evidence_cell(report, " ".join(parts))
        return
    raise ValueError(f"unsupported prepared_emission status: {status!r}")


def assert_sanitizer_lineage_evidence(
    report: str,
    *,
    mode: str | None = None,
    changed: int | None = None,
    dropped: int | None = None,
    empty: bool | None = None,
    legacy: str | bool | None = None,
) -> None:
    """Assert ``sanitizer_lineage_*`` evidence tokens in the dashboard evidence column."""
    if mode is not None:
        assert_compact_evidence_field(report, "sanitizer_lineage_mode", mode)
    if changed is not None:
        assert_compact_evidence_field(report, "sanitizer_lineage_changed", changed)
    if dropped is not None:
        assert_compact_evidence_field(report, "sanitizer_lineage_dropped", dropped)
    if empty is not None:
        assert_compact_evidence_field(report, "sanitizer_lineage_empty", empty)
    if legacy is not None:
        assert_compact_evidence_field(report, "sanitizer_lineage_legacy", legacy)


def assert_sanitizer_empty_fallback_evidence(
    report: str,
    *,
    source: str,
    owner: str,
    prepared_emission_used_absent: bool = True,
) -> None:
    """Assert sanitizer-empty fallback evidence is distinct from prepared-emission used."""
    assert_compact_evidence_field(report, "sanitizer_empty", True)
    assert_compact_evidence_field(report, "sanitizer_empty_source", source)
    assert_compact_evidence_field(report, "sanitizer_empty_owner", owner)
    if prepared_emission_used_absent:
        assert_dashboard_evidence_cell(report, "prepared_emission=used", present=False)


def assert_strict_social_sanitizer_evidence(
    report: str,
    *,
    selection_owner: str,
    prose_owner: str,
    source: str,
) -> None:
    """Assert strict-social sanitizer split-owner evidence tokens."""
    assert_compact_evidence_field(report, "strict_social_selection_owner", selection_owner)
    assert_compact_evidence_field(report, "strict_social_prose_owner", prose_owner)
    assert_compact_evidence_field(report, "strict_social_source", source)


def assert_fallback_authorship_evidence(
    report: str,
    *,
    selection_owner: str | None = None,
    content_owner: str | None = None,
    repair: str | None = None,
    opening_owner: str | None = None,
    visibility_owner: str | None = None,
    sealed_owner: str | None = None,
) -> None:
    """Assert fallback split-owner and bucket evidence summaries in the evidence column."""
    if selection_owner is not None:
        assert_compact_evidence_field(report, "fallback_selection_owner", selection_owner)
    if content_owner is not None:
        assert_compact_evidence_field(report, "fallback_content_owner", content_owner)
    if repair is not None:
        assert_compact_evidence_field(report, "repair", repair)
    if opening_owner is not None:
        assert_compact_evidence_field(report, "opening_owner", opening_owner)
    if visibility_owner is not None:
        assert_compact_evidence_field(report, "visibility_owner", visibility_owner)
    if sealed_owner is not None:
        assert_compact_evidence_field(report, "sealed_owner", sealed_owner)


# Runtime lineage summary presentation helpers (CO6) --------------------------


_RUNTIME_LINEAGE_SUMMARY_HEADER = "## Runtime Lineage Summary"


def _runtime_lineage_frequency_row(label: str, count: int) -> str:
    return f"`{label}` ({count})"


def assert_runtime_lineage_frequency_row(report: str, label: str, count: int) -> None:
    """Assert one ``label (count)`` frequency row in the runtime lineage summary section."""
    needle = _runtime_lineage_frequency_row(label, count)
    assert needle in report, f"expected lineage frequency row {needle!r} in report"


def assert_runtime_lineage_source_counts(
    report: str,
    counts: Mapping[str, int],
) -> None:
    """Assert multiple backtick-wrapped lineage source/bucket frequency rows."""
    for label, count in counts.items():
        assert_runtime_lineage_frequency_row(report, label, count)


def assert_runtime_lineage_summary_contains(
    report: str,
    *,
    total_events: int | None = None,
    fallback_selected: int | None = None,
    frequency_rows: Mapping[str, int] | None = None,
    needles: Sequence[str] = (),
) -> None:
    """Assert runtime lineage summary section headers and optional count rows."""
    assert _RUNTIME_LINEAGE_SUMMARY_HEADER in report, (
        "expected runtime lineage summary section in report"
    )
    if total_events is not None:
        assert f"**Total lineage events:** {total_events}" in report, (
            f"expected total lineage events {total_events} in report"
        )
    if fallback_selected is not None:
        assert f"**Fallback selected:** {fallback_selected}" in report, (
            f"expected fallback selected count {fallback_selected} in report"
        )
    if frequency_rows:
        assert_runtime_lineage_source_counts(report, frequency_rows)
    for needle in needles:
        assert needle in report, f"expected {needle!r} in runtime lineage summary report"


def assert_runtime_lineage_summary_absent(report: str) -> None:
    """Assert the runtime lineage summary section is not rendered."""
    assert _RUNTIME_LINEAGE_SUMMARY_HEADER not in report, (
        "expected runtime lineage summary section absent from report"
    )


# Lineage aggregation parity helpers (CO7) ------------------------------------
# Dict-level aggregation checks only; report markdown rendering stays in CO6.


def assert_lineage_summary_counts(
    summary: Mapping[str, Any],
    *,
    total_events: int,
) -> None:
    """Assert ``total_events`` on a runtime lineage aggregation summary dict."""
    actual = summary.get("total_events")
    assert actual == total_events, (
        f"total_events: expected {total_events!r}, got {actual!r}"
    )


def assert_lineage_frequency_counts(
    summary: Mapping[str, Any],
    bucket: str,
    expected: Mapping[str, int],
) -> None:
    """Assert one lineage frequency bucket matches expected key/count mapping."""
    actual = summary.get(bucket)
    assert actual == expected, (
        f"{bucket}: expected {expected!r}, got {actual!r}"
    )


def assert_lineage_frequency_absent(
    summary: Mapping[str, Any],
    bucket: str,
    key: str,
) -> None:
    """Assert a lineage frequency bucket has no count for ``key``."""
    frequencies = summary.get(bucket) if isinstance(summary.get(bucket), Mapping) else {}
    actual = frequencies.get(key, 0) if isinstance(frequencies, Mapping) else 0
    assert actual == 0, f"{bucket}[{key!r}]: expected absent, got {actual!r}"


def assert_lineage_frequency_at_least(
    summary: Mapping[str, Any],
    bucket: str,
    key: str,
    *,
    minimum: int = 1,
) -> None:
    """Assert a lineage frequency bucket includes at least ``minimum`` for ``key``."""
    frequencies = summary.get(bucket) if isinstance(summary.get(bucket), Mapping) else {}
    actual = frequencies.get(str(key), 0) if isinstance(frequencies, Mapping) else 0
    assert actual >= minimum, (
        f"{bucket}[{key!r}]: expected >={minimum}, got {actual!r}"
    )


def assert_lineage_aggregation_parity(
    summary: Mapping[str, Any],
    *,
    total_events: int | None = None,
    fallback_frequency: Mapping[str, int] | None = None,
    fallback_authorship_frequency: Mapping[str, int] | None = None,
    fallback_owner_bucket_frequency: Mapping[str, int] | None = None,
    fallback_selection_owner_frequency: Mapping[str, int] | None = None,
    fallback_content_owner_frequency: Mapping[str, int] | None = None,
    speaker_repair_frequency: Mapping[str, int] | None = None,
    mutation_kind_frequency: Mapping[str, int] | None = None,
    gate_path_frequency: Mapping[str, int] | None = None,
    by_event_kind: Mapping[str, int] | None = None,
    first_recurring_count: int | None = None,
    recurring_event_index: int = 0,
) -> None:
    """Assert runtime lineage summary dict matches expected aggregation buckets."""
    if total_events is not None:
        assert_lineage_summary_counts(summary, total_events=total_events)
    bucket_expectations = (
        ("fallback_frequency", fallback_frequency),
        ("fallback_authorship_frequency", fallback_authorship_frequency),
        ("fallback_owner_bucket_frequency", fallback_owner_bucket_frequency),
        ("fallback_selection_owner_frequency", fallback_selection_owner_frequency),
        ("fallback_content_owner_frequency", fallback_content_owner_frequency),
        ("speaker_repair_frequency", speaker_repair_frequency),
        ("mutation_kind_frequency", mutation_kind_frequency),
        ("gate_path_frequency", gate_path_frequency),
        ("by_event_kind", by_event_kind),
    )
    for bucket_name, expected in bucket_expectations:
        if expected is not None:
            assert_lineage_frequency_counts(summary, bucket_name, expected)
    if first_recurring_count is not None:
        recurring = summary.get("recurring_events")
        assert isinstance(recurring, list) and len(recurring) > recurring_event_index, (
            f"recurring_events[{recurring_event_index}] missing from summary"
        )
        item = recurring[recurring_event_index]
        assert isinstance(item, Mapping), (
            f"recurring_events[{recurring_event_index}] is not a mapping"
        )
        actual = item.get("count")
        assert actual == first_recurring_count, (
            f"recurring_events[{recurring_event_index}].count: "
            f"expected {first_recurring_count!r}, got {actual!r}"
        )


def assert_lineage_matrix_row_aggregated(
    summary: Mapping[str, Any],
    *,
    event_kind: str,
    fallback_kind: str | None = None,
    fallback_selection_owner: str | None = None,
    fallback_content_owner: str | None = None,
) -> None:
    """Assert one split-owner matrix row contributes to lineage aggregation buckets."""
    if event_kind == "mutation":
        assert_lineage_frequency_at_least(summary, "by_event_kind", "mutation")
        return
    assert_lineage_frequency_at_least(summary, "fallback_frequency", fallback_kind or "")
    assert_lineage_frequency_at_least(
        summary,
        "fallback_selection_owner_frequency",
        fallback_selection_owner or "",
    )
    assert_lineage_frequency_at_least(
        summary,
        "fallback_content_owner_frequency",
        fallback_content_owner or "",
    )


# Contract/registry summary helpers (CO8) ---------------------------------------
# Taxonomy and protected-field registry parity; separate from CO4–CO7 helpers.
# CO12 reuses ``assert_failure_dashboard_row_shape`` and ``assert_classification_contract_summary``
# from contract tests without hiding schema ownership behind broad helpers.
# CO13 reuses the same row-shape and classification helpers in classifier parity tests.


_OWNER_BUCKET_SUMMARY_KEYS: tuple[tuple[str, str], ...] = (
    ("opening", "opening_owner_bucket_count"),
    ("sealed", "sealed_owner_bucket_count"),
    ("visibility", "visibility_owner_bucket_count"),
)


def assert_classification_contract_summary(
    summary: Mapping[str, Any],
    *,
    categories: Sequence[str] | None = None,
    owner_buckets: Mapping[str, Sequence[str]] | None = None,
) -> None:
    """Assert contract summary counts align with known taxonomy surfaces."""
    if categories is not None:
        expected = len(categories)
        actual = summary.get("failure_category_count")
        assert actual == expected, (
            f"failure_category_count: expected {expected!r}, got {actual!r}"
        )
    if owner_buckets is not None:
        for bucket_key, summary_key in _OWNER_BUCKET_SUMMARY_KEYS:
            expected = len(owner_buckets[bucket_key])
            actual = summary.get(summary_key)
            assert actual == expected, (
                f"{summary_key}: expected {expected!r}, got {actual!r}"
            )


def assert_classification_contract_categories_contain(
    categories: Sequence[str],
    *members: str,
) -> None:
    """Assert known failure categories include expected membership tokens."""
    for member in members:
        assert member in categories, f"expected category {member!r} in taxonomy"


def assert_owner_buckets_contain(
    buckets: Mapping[str, Sequence[str]],
    *,
    opening: Sequence[str] = (),
    sealed: Sequence[str] = (),
    visibility: Sequence[str] = (),
) -> None:
    """Assert owner-bucket registries include expected bucket literals."""
    for bucket_name, members in (
        ("opening", opening),
        ("sealed", sealed),
        ("visibility", visibility),
    ):
        if not members:
            continue
        values = buckets.get(bucket_name, ())
        for member in members:
            assert member in values, (
                f"expected {bucket_name} bucket {member!r} in owner registry"
            )


def assert_registry_summary_counts(registry_summary: Mapping[str, Any]) -> None:
    """Assert protected observation registry summary count invariants."""
    protected = registry_summary.get("protected_field_count")
    structural = registry_summary.get("structural_field_count")
    semantic = registry_summary.get("semantic_field_count")
    assert protected == structural + semantic, (
        "protected_field_count must equal structural_field_count + semantic_field_count: "
        f"protected={protected!r} structural={structural!r} semantic={semantic!r}"
    )
    assert registry_summary.get("paths_unique") is True, "expected paths_unique=True"
    assert registry_summary.get("paths_sorted") is True, "expected paths_sorted=True"


def assert_registry_summary_contains(
    registry_summary: Mapping[str, Any],
    **expected_fields: Any,
) -> None:
    """Assert protected observation registry summary field values."""
    for key, expected in expected_fields.items():
        actual = registry_summary.get(key)
        assert actual == expected, (
            f"{key}: expected {expected!r}, got {actual!r}"
        )


def assert_registry_contract_fields(
    summary: Mapping[str, Any],
    row_fields: Mapping[str, Sequence[str]],
    *,
    required_contains: Sequence[str] = (),
    optional_evidence_contains: Sequence[str] = (),
) -> None:
    """Assert classification row-field contract aligns with contract summary counts."""
    required = row_fields.get("required", ())
    optional_evidence = row_fields.get("optional_evidence", ())
    expected_required_count = summary.get("required_field_count")
    assert len(required) == expected_required_count, (
        f"required field count: expected {expected_required_count!r}, got {len(required)!r}"
    )
    for field in required_contains:
        assert field in required, f"expected required field {field!r} in contract"
    for field in optional_evidence_contains:
        assert field in optional_evidence, (
            f"expected optional evidence field {field!r} in contract"
        )


# Controlled-failure presentation helpers (CO10) ------------------------------
# Group B/C dashboard probe presentation; separate from CO4–CO9 helpers.


def assert_controlled_failure_probe_row(
    dashboard_row: Mapping[str, Any],
    classifier_row: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> None:
    """Assert controlled probe dashboard/classifier parity and routing expected fields."""
    assert_classifier_dashboard_projection_parity(dashboard_row, classifier_row)
    assert_failure_classification_row(dashboard_row, **expected)


def assert_controlled_failure_probe_coverage(
    cases: Sequence[ControlledFailureCase],
    *,
    categories: Sequence[str] | None = None,
    owner_buckets: Mapping[str, Sequence[str]] | None = None,
    protected_field_paths: Sequence[str] | None = None,
    extension_field_paths: frozenset[str] | None = None,
) -> None:
    """Assert controlled probes use sync taxonomy categories, buckets, and field paths."""
    category_set = set(categories) if categories is not None else None
    protected_set = set(protected_field_paths) if protected_field_paths is not None else None
    for case_id, observed, drift_row, expected in cases:
        if category_set is not None:
            category = expected.get("category")
            assert category in category_set, (
                f"{case_id}: expected category {category!r} in sync taxonomy"
            )
        if owner_buckets is not None:
            opening_bucket = expected.get("opening_fallback_owner_bucket") or observed.get(
                "opening_fallback_owner_bucket"
            )
            if opening_bucket is not None:
                assert opening_bucket in owner_buckets["opening"], (
                    f"{case_id}: expected opening bucket {opening_bucket!r} in sync taxonomy"
                )
            sealed_bucket = expected.get("sealed_fallback_owner_bucket") or observed.get(
                "sealed_fallback_owner_bucket"
            )
            if sealed_bucket is not None:
                assert sealed_bucket in owner_buckets["sealed"], (
                    f"{case_id}: expected sealed bucket {sealed_bucket!r} in sync taxonomy"
                )
            visibility_bucket = expected.get("visibility_fallback_owner_bucket") or observed.get(
                "visibility_fallback_owner_bucket"
            )
            if visibility_bucket is not None:
                assert visibility_bucket in owner_buckets["visibility"], (
                    f"{case_id}: expected visibility bucket {visibility_bucket!r} in sync taxonomy"
                )
        if protected_set is not None:
            field_path = str(drift_row["field_path"])
            allowed_extensions = extension_field_paths or frozenset()
            assert field_path in protected_set or field_path in allowed_extensions, (
                f"{case_id}: drift field_path {field_path!r} not on projection surface"
            )


def assert_controlled_failure_evidence_cell(
    row: Mapping[str, Any],
    expected: str,
    *,
    render_cell: Callable[[Mapping[str, Any]], str],
) -> None:
    """Assert one controlled probe evidence cell matches its presentation golden."""
    actual = render_cell(row)
    assert actual == expected, (
        f"controlled probe evidence cell: expected {expected!r}, got {actual!r}"
    )


def assert_controlled_failure_dashboard_entry(
    report: str,
    *fragments: str,
) -> None:
    """Assert controlled-failure dashboard markdown includes evidence column fragments."""
    assert_dashboard_evidence_column_present(report)
    assert_dashboard_evidence_contains(report, *fragments)


# Group B presentation goldens (CO11) -------------------------------------------
# Intentional literal locks grouped by presentation family. Families make shared
# vocabulary obvious; merged tables preserve exact per-probe strings for parametrized
# tests. Repeated tokens across families (e.g. visibility_pool=...) are deliberate
# cross-probe presentation anchors, not accidental duplication.


# --- Evidence cell goldens (per-probe compact Evidence column strings) ---------

CONTROLLED_SPEAKER_EVIDENCE_CELLS: dict[str, str] = {
    # Speaker contract probes: empty evidence when mismatch is routing-only.
    "wrong_speaker": "none",
}

CONTROLLED_FALLBACK_TERMINAL_EVIDENCE_CELLS: dict[str, str] = {
    "forced_fallback_source": "sublayer=terminal_fallback; mutation=terminal_fallback",
}

CONTROLLED_OPENING_FALLBACK_EVIDENCE_CELLS: dict[str, str] = {
    # Opening-family probes share sublayer=opening_fallback vocabulary; literals differ by symptom.
    "opening_fallback_owner_bucket": (
        "sublayer=opening_fallback; repair=opening_deterministic_fallback; "
        "opening_authorship=upstream_prepared_opening_fallback; opening_owner=upstream-prepared; "
        "mutation=opening_fallback"
    ),
    "scene_opening_split_owner": (
        "sublayer=opening_fallback; repair=opening_deterministic_fallback; "
        "opening_authorship=upstream_prepared_opening_fallback; opening_owner=upstream-prepared; "
        "fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.opening_deterministic_fallback; mutation=opening_fallback"
    ),
    "opening_failed_closed_split_owner": (
        "sublayer=opening_fallback; repair=opening_deterministic_fallback_failed_closed; "
        "opening_owner=sealed-gate; fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.final_emission_gate; mutation=opening_fallback"
    ),
    "opening_fallback_authorship_source": (
        "sublayer=opening_fallback; "
        f"opening_authorship={legacy_compatibility_local_opening_authorship_source()}; "
        "opening_owner=unknown-ambiguous; mutation=opening_fallback"
    ),
    "opening_fallback_basis": (
        "sublayer=opening_fallback; opening_owner=unknown-ambiguous; mutation=opening_fallback"
    ),
    "opening_fallback_projection_missing": (
        "opening_owner=unknown-ambiguous; missing=projection_missing_raw_present"
    ),
}

CONTROLLED_SEALED_VISIBILITY_BUCKET_EVIDENCE_CELLS: dict[str, str] = {
    "sealed_fallback_owner_bucket": (
        "sublayer=terminal_fallback; sealed_owner=sealed-gate; mutation=terminal_fallback"
    ),
    "visibility_fallback_owner_bucket": (
        "sublayer=terminal_fallback; visibility_owner=sealed-gate; visibility_replaced=True; "
        "visibility_pool=global_scene_narrative; visibility_kind=narrative_safe_fallback; mutation=terminal_fallback"
    ),
}

CONTROLLED_VISIBILITY_SPLIT_OWNER_EVIDENCE_CELLS: dict[str, str] = {
    # Visibility enforcement probes repeat pool/kind tokens to lock shared replacement meta.
    "visibility_enforcement_split_owner": (
        "sublayer=terminal_fallback; repair=visibility_enforcement; "
        "fallback_selection_owner=game.final_emission_visibility_fallback; "
        "fallback_content_owner=game.final_emission_sealed_fallback; "
        "visibility_owner=sealed-gate; visibility_replaced=True; "
        "visibility_pool=global_scene_narrative; visibility_kind=narrative_safe_fallback; mutation=terminal_fallback"
    ),
    "first_mention_enforcement_split_owner": (
        "sublayer=terminal_fallback; repair=first_mention_enforcement; "
        "fallback_selection_owner=game.final_emission_visibility_fallback; "
        "fallback_content_owner=game.final_emission_sealed_fallback; "
        "visibility_owner=sealed-gate; visibility_replaced=False; "
        "visibility_pool=global_scene_narrative; visibility_kind=narrative_safe_fallback; mutation=terminal_fallback"
    ),
    "referential_clarity_enforcement_split_owner": (
        "sublayer=terminal_fallback; repair=referential_clarity_enforcement; "
        "fallback_selection_owner=game.final_emission_visibility_fallback; "
        "fallback_content_owner=game.social_exchange_emission; "
        "visibility_owner=strict-social-visibility; visibility_replaced=False; "
        "visibility_pool=global_scene_narrative; visibility_kind=narrative_safe_fallback; mutation=terminal_fallback"
    ),
    "referential_local_substitution_split_owner": (
        "repair=referential_clarity_local_substitution; visibility_owner=strict-social-visibility; "
        "mutation=referential_clarity_local_substitution_mutation"
    ),
}

CONTROLLED_SANITIZER_SPLIT_OWNER_EVIDENCE_CELLS: dict[str, str] = {
    "sanitizer_strict_social_split_owner": (
        "sublayer=strict_social_replacement; repair=strict_social_repair; "
        "fallback_selection_owner=game.output_sanitizer; fallback_content_owner=game.social_exchange_emission; "
        "mutation=strict_social_replacement; strict_social_fallback=True; "
        "strict_social_selection_owner=game.output_sanitizer; strict_social_prose_owner=game.social_exchange_emission; "
        "strict_social_source=social_fallback_line_for_sanitizer.empty_output"
    ),
    "sanitizer_empty_output_split_owner": (
        "sublayer=sanitizer; repair=sanitizer_empty_output; "
        "fallback_selection_owner=game.output_sanitizer; fallback_content_owner=game.output_sanitizer; "
        "mutation=sanitizer; sanitizer_empty=True; "
        "sanitizer_empty_source=upstream_prepared_emission.prepared_sanitizer_empty_fallback_text; "
        "sanitizer_empty_owner=game.output_sanitizer; sanitizer_lineage_mode=strip_only; sanitizer_lineage_empty=True"
    ),
}

CONTROLLED_UPSTREAM_FAST_SPLIT_OWNER_EVIDENCE_CELLS: dict[str, str] = {
    "upstream_fast_fallback_split_owner": (
        "fallback_selection_owner=game.api; fallback_content_owner=game.gm_retry"
    ),
}

CONTROLLED_SEALED_SPLIT_OWNER_EVIDENCE_CELLS: dict[str, str] = {
    "sealed_global_scene_split_owner": (
        "sublayer=terminal_fallback; "
        "fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.final_emission_sealed_fallback; "
        "sealed_owner=sealed-gate; mutation=terminal_fallback"
    ),
    "sealed_social_interlocutor_split_owner": (
        "sublayer=fallback_behavior; "
        "fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.social_exchange_emission; "
        "sealed_owner=strict-social-sealed; mutation=fallback_behavior"
    ),
    "sealed_passive_scene_pressure_split_owner": (
        "sublayer=fallback_behavior; "
        "fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.final_emission_sealed_fallback; "
        "sealed_owner=sealed-gate; mutation=fallback_behavior"
    ),
    "sealed_npc_pursuit_neutral_split_owner": (
        "sublayer=fallback_behavior; "
        "fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.final_emission_sealed_fallback; "
        "sealed_owner=sealed-gate; mutation=fallback_behavior"
    ),
    "sealed_anti_reset_continuation_split_owner": (
        "sublayer=fallback_behavior; "
        "fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.final_emission_sealed_fallback; "
        "sealed_owner=sealed-gate; mutation=fallback_behavior"
    ),
    "sealed_unknown_replacement_split_owner": (
        "sublayer=terminal_fallback; "
        "fallback_selection_owner=game.final_emission_gate; "
        "fallback_content_owner=game.final_emission_gate; "
        "sealed_owner=unknown-none; mutation=terminal_fallback"
    ),
}

CONTROLLED_SANITIZER_LINEAGE_EVIDENCE_CELLS: dict[str, str] = {
    "sanitizer_leakage": (
        "sublayer=sanitizer; mutation=sanitizer; sanitizer_mode=strip_only; sanitizer_events=1; "
        "sanitizer_changed=0; sanitizer_lineage_mode=strip_only; sanitizer_lineage_changed=1; "
        "sanitizer_lineage_dropped=1; sanitizer_lineage_empty=False; sanitizer_lineage_legacy=False"
    ),
    "sanitizer_empty_fallback": (
        "sublayer=sanitizer; lineage=pre_gate_sanitizer>sanitizer_empty_fallback>finalize_packaging; "
        "mutation=sanitizer; sanitizer_mode=strip_only; sanitizer_empty=True; "
        "sanitizer_empty_source=upstream_prepared_emission.prepared_sanitizer_empty_fallback_text; "
        "sanitizer_empty_owner=game.output_sanitizer; sanitizer_lineage_mode=strip_only; sanitizer_lineage_changed=1; "
        "sanitizer_lineage_dropped=1; sanitizer_lineage_empty=True; sanitizer_lineage_legacy=False"
    ),
    "strict_social_sanitizer_fallback": (
        "sublayer=strict_social_replacement; mutation=strict_social_replacement; strict_social_fallback=True; "
        "strict_social_selection_owner=game.output_sanitizer; strict_social_prose_owner=game.social_exchange_emission; "
        "strict_social_source=social_fallback_line_for_sanitizer.empty_output"
    ),
    "legacy_sanitizer_rewrite_diagnostic": (
        "sublayer=sanitizer; mutation=sanitizer; sanitizer_lineage_mode=legacy_sentence_rewrite; "
        "sanitizer_lineage_changed=1; sanitizer_lineage_dropped=0; sanitizer_lineage_empty=False; "
        "sanitizer_lineage_legacy=legacy_diagnostic"
    ),
}

CONTROLLED_PREPARED_EMISSION_EVIDENCE_CELLS: dict[str, str] = {
    "response_type_repair_unexpected": (
        "prepared_emission=used valid=True source=prepared_action_fallback_text; sublayer=upstream_prepared_emission; "
        "repair=action_outcome_upstream_prepared_repair; lineage=response_type_repair>prepared_emission_selection>finalize_packaging; "
        "mutation=upstream_prepared_emission"
    ),
    "prepared_emission_rejected": (
        "prepared_emission=rejected reason=missing_answer_specificity; sublayer=upstream_prepared_emission; "
        "repair=answer_upstream_prepared_repair; mutation=upstream_prepared_emission"
    ),
}

CONTROLLED_PROJECTION_MISSING_EVIDENCE_CELLS: dict[str, str] = {
    "missing_route_metadata_raw_absent": "missing=runtime_missing_raw_absent",
    "missing_route_metadata_raw_present": "missing=projection_missing_raw_present",
}

CONTROLLED_SEMANTIC_EVIDENCE_CELLS: dict[str, str] = {
    "semantic_mutation": "none",
}

CONTROLLED_POST_GATE_MUTATION_EVIDENCE_CELLS: dict[str, str] = {
    "post_gate_unknown_mutation": (
        "sublayer=emission.post_gate_mutation_unknown; mutation=emission.post_gate_mutation_unknown"
    ),
    "post_gate_route_illegal_strip_reduced": (
        "sublayer=final_emission.finalize_route_illegal_strip; lineage=finalize_route_illegal_strip>finalize_packaging; "
        "mutation=final_emission.finalize_route_illegal_strip"
    ),
    "post_gate_sanitizer_empty_reduced": (
        "sublayer=sanitizer.empty_fallback; lineage=pre_gate_sanitizer>sanitizer_empty_fallback>finalize_packaging; "
        "mutation=sanitizer.empty_fallback"
    ),
    "post_gate_response_type_reduced": (
        "sublayer=response_type; lineage=response_type_repair>finalize_packaging; mutation=response_type"
    ),
}

CONTROLLED_PROBE_EVIDENCE_CELLS: dict[str, str] = {
    **CONTROLLED_SPEAKER_EVIDENCE_CELLS,
    **CONTROLLED_FALLBACK_TERMINAL_EVIDENCE_CELLS,
    **CONTROLLED_OPENING_FALLBACK_EVIDENCE_CELLS,
    **CONTROLLED_SEALED_VISIBILITY_BUCKET_EVIDENCE_CELLS,
    **CONTROLLED_VISIBILITY_SPLIT_OWNER_EVIDENCE_CELLS,
    **CONTROLLED_SANITIZER_SPLIT_OWNER_EVIDENCE_CELLS,
    **CONTROLLED_UPSTREAM_FAST_SPLIT_OWNER_EVIDENCE_CELLS,
    **CONTROLLED_SEALED_SPLIT_OWNER_EVIDENCE_CELLS,
    **CONTROLLED_SANITIZER_LINEAGE_EVIDENCE_CELLS,
    **CONTROLLED_PREPARED_EMISSION_EVIDENCE_CELLS,
    **CONTROLLED_PROJECTION_MISSING_EVIDENCE_CELLS,
    **CONTROLLED_SEMANTIC_EVIDENCE_CELLS,
    **CONTROLLED_POST_GATE_MUTATION_EVIDENCE_CELLS,
}


# --- Dashboard markdown report fragments (cross-probe rendered anchors) --------

CONTROLLED_SPEAKER_DASHBOARD_FRAGMENTS: tuple[str, ...] = (
    "wrong_speaker",
    "speaker_mismatch",
)

CONTROLLED_FALLBACK_SOURCE_DASHBOARD_FRAGMENTS: tuple[str, ...] = (
    "forced_fallback_source",
    "fallback_source_mismatch",
)

CONTROLLED_OPENING_FALLBACK_DASHBOARD_FRAGMENTS: tuple[str, ...] = (
    "opening_fallback_owner_bucket",
    "opening_owner=upstream-prepared",
    "scene_opening_split_owner",
    "fallback_content_owner=game.opening_deterministic_fallback",
    "opening_authorship=upstream_prepared_opening_fallback",
    "opening_fallback_authorship_source",
    "opening_final_fallback_basis",
    "opening_fallback_projection_missing",
)

CONTROLLED_INVESTIGATE_FIRST_DASHBOARD_FRAGMENTS: tuple[str, ...] = (
    # investigate_first routing targets must appear in the rendered dashboard row.
    "game/final_emission_meta.py",
    "game/upstream_response_repairs.py",
    "game/opening_deterministic_fallback.py",
    "tests/helpers/golden_replay.py",
)

CONTROLLED_SEALED_VISIBILITY_DASHBOARD_FRAGMENTS: tuple[str, ...] = (
    "sealed_fallback_owner_bucket",
    "sealed_owner=sealed-gate",
    "visibility_fallback_owner_bucket",
    "visibility_owner=sealed-gate",
    "visibility_replaced=True",
    "visibility_pool=global_scene_narrative",
    "visibility_kind=narrative_safe_fallback",
    "sealed_owner=strict-social-sealed",
    "sealed_owner=unknown-none",
)

CONTROLLED_SPLIT_OWNER_DASHBOARD_FRAGMENTS: tuple[str, ...] = (
    "fallback_selection_owner=game.final_emission_visibility_fallback",
    "fallback_content_owner=game.final_emission_sealed_fallback",
    "fallback_selection_owner=game.output_sanitizer",
    "fallback_content_owner=game.social_exchange_emission",
    "fallback_selection_owner=game.api",
    "fallback_content_owner=game.gm_retry",
    "sealed_global_scene_split_owner",
    "sealed_social_interlocutor_split_owner",
    "sealed_passive_scene_pressure_split_owner",
    "sealed_unknown_replacement_split_owner",
    "fallback_selection_owner=game.final_emission_gate",
    "fallback_content_owner=game.final_emission_sealed_fallback",
)

CONTROLLED_PREPARED_EMISSION_DASHBOARD_FRAGMENTS: tuple[str, ...] = (
    "prepared_emission=used valid=True source=prepared_action_fallback_text",
    "lineage=response_type_repair>prepared_emission_selection>finalize_packaging",
    "prepared_emission=rejected reason=missing_answer_specificity",
)

CONTROLLED_SANITIZER_LINEAGE_DASHBOARD_FRAGMENTS: tuple[str, ...] = (
    "sanitizer_empty_owner=game.output_sanitizer",
    "sanitizer_lineage_changed=1",
    "sanitizer_lineage_dropped=1",
    "sanitizer_lineage_empty=True",
    "sanitizer_lineage_legacy=legacy_diagnostic",
)

CONTROLLED_STRICT_SOCIAL_DASHBOARD_FRAGMENTS: tuple[str, ...] = (
    "strict_social_selection_owner=game.output_sanitizer",
    "strict_social_prose_owner=game.social_exchange_emission",
    "strict_social_source=social_fallback_line_for_sanitizer.empty_output",
)

CONTROLLED_PROJECTION_MISSING_DASHBOARD_FRAGMENTS: tuple[str, ...] = (
    "missing=runtime_missing_raw_absent",
    "missing=projection_missing_raw_present",
)

CONTROLLED_POST_GATE_DASHBOARD_FRAGMENTS: tuple[str, ...] = (
    "sublayer=emission.post_gate_mutation_unknown",
    "lineage=finalize_route_illegal_strip>finalize_packaging",
    "mutation=final_emission.finalize_route_illegal_strip",
    "lineage=pre_gate_sanitizer>sanitizer_empty_fallback>finalize_packaging",
    "mutation=sanitizer.empty_fallback",
    "lineage=response_type_repair>finalize_packaging",
    "mutation=response_type",
)

CONTROLLED_DASHBOARD_STRUCTURE_FRAGMENTS: tuple[str, ...] = (
    # Column/field anchors proving triage table shape survived rendering.
    "route_kind",
)

CONTROLLED_FAILURE_DASHBOARD_REPORT_FRAGMENTS: tuple[str, ...] = (
    *CONTROLLED_SPEAKER_DASHBOARD_FRAGMENTS,
    *CONTROLLED_FALLBACK_SOURCE_DASHBOARD_FRAGMENTS,
    *CONTROLLED_OPENING_FALLBACK_DASHBOARD_FRAGMENTS,
    *CONTROLLED_INVESTIGATE_FIRST_DASHBOARD_FRAGMENTS,
    *CONTROLLED_SEALED_VISIBILITY_DASHBOARD_FRAGMENTS,
    *CONTROLLED_SPLIT_OWNER_DASHBOARD_FRAGMENTS,
    *CONTROLLED_PREPARED_EMISSION_DASHBOARD_FRAGMENTS,
    *CONTROLLED_SANITIZER_LINEAGE_DASHBOARD_FRAGMENTS,
    *CONTROLLED_STRICT_SOCIAL_DASHBOARD_FRAGMENTS,
    *CONTROLLED_PROJECTION_MISSING_DASHBOARD_FRAGMENTS,
    *CONTROLLED_POST_GATE_DASHBOARD_FRAGMENTS,
    *CONTROLLED_DASHBOARD_STRUCTURE_FRAGMENTS,
)
