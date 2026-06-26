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

**B — dashboard presentation goldens**: ``_CONTROLLED_PROBE_EVIDENCE_CELLS`` and
``test_controlled_failure_probe_dashboard_contains_triage_columns`` in
``tests/test_failure_dashboard_controlled_failures.py``; report section/shape
tests in ``tests/test_failure_dashboard_report.py``. These lock evidence cell
formatting, labels, ordering, and markdown report shape.

**C — compatibility probes**: ``SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES`` (BU19
empty guard), module export parity tests, ``record_selected_speaker_protected_failure``
bridge fixture, ``expected_failure_classification_row_fields`` contract re-export.
"""
from __future__ import annotations

from typing import Any, Mapping

from tests.helpers.failure_classifier import validate_failure_classification_row
from tests.helpers.failure_classification_alignment import failure_classification_row_contract_fields
from tests.helpers.failure_classification_builders import classify_replay_probe_row
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
