"""Recurrence unit-test assertion helpers (CO22).

Payload parity and report-section checks shared by replay recurrence tests.
Dashboard integration helpers remain in ``failure_dashboard_report``.
"""
from __future__ import annotations

from typing import Any, Mapping

from tests.helpers.failure_dashboard_report import assert_recurrence_payload_status

CONFIDENCE_AUDIT_DIMENSION_KEYS = (
    "forecast_confidence_audit",
    "governance_confidence_audit",
    "effectiveness_confidence_audit",
)


def assert_recurrence_summarizer_parity(
    summary: Mapping[str, Any],
    artifact: Mapping[str, Any],
    summary_key: str,
    *,
    expected_fields: tuple[str, ...] | None = None,
) -> None:
    """Assert summarize_* output matches the embedded summary on a build artifact."""
    embedded = artifact[summary_key]
    if expected_fields is None:
        assert summary == embedded
        return
    for field in expected_fields:
        assert summary[field] == embedded[field]


def assert_recurrence_report_markdown_sections(markdown: str, *headings: str) -> None:
    """Assert recurrence markdown report contains each required section heading."""
    for heading in headings:
        assert heading in markdown


def assert_recurrence_core_regression_rate(
    metric: Mapping[str, Any],
    *,
    numerator: int | None = None,
    denominator: int | None = None,
    rate: float | None = None,
    metric_name: str | None = None,
    report_only: bool | None = None,
    advisory_only: bool | None = None,
) -> None:
    """Assert core ``regression_recurrence_rate`` metric fields on aggregated history."""
    if metric_name is not None:
        assert metric.get("metric") == metric_name
    if numerator is not None:
        assert metric.get("numerator") == numerator
    if denominator is not None:
        assert metric.get("denominator") == denominator
    if rate is not None:
        assert metric.get("rate") == rate
    if report_only is not None:
        assert metric.get("report_only") is report_only
    if advisory_only is not None:
        assert metric.get("advisory_only") is advisory_only


def assert_recurrence_aggregated_summary_status(
    history: Mapping[str, Any],
    *,
    index: int = 0,
    occurrence_count: int | None = None,
    status: str | None = None,
) -> None:
    """Assert build_recurrence_summary entry fields via dashboard status helper."""
    from tests.helpers.replay_bug_recurrence import build_recurrence_summary

    assert_recurrence_payload_status(
        {"summary": build_recurrence_summary(history)},
        index=index,
        occurrence_count=occurrence_count,
        status=status,
    )


def assert_recurrence_confidence_dimension(
    audit: Mapping[str, Any],
    dimension_key: str,
    *,
    confidence_status: str | None = None,
    calibration_gap: float | None = None,
) -> None:
    """Assert one confidence calibration dimension audit row."""
    dimension = audit[dimension_key]
    assert isinstance(dimension, Mapping), f"audit[{dimension_key!r}] must be a mapping"
    if confidence_status is not None:
        assert dimension.get("confidence_status") == confidence_status
    if calibration_gap is not None:
        assert dimension.get("calibration_gap") == calibration_gap


def assert_recurrence_confidence_status(
    audit: Mapping[str, Any],
    expected_status: str,
    *,
    dimensions: tuple[str, ...] = CONFIDENCE_AUDIT_DIMENSION_KEYS,
) -> None:
    """Assert the same calibration classification across confidence audit dimensions."""
    for dimension_key in dimensions:
        assert_recurrence_confidence_dimension(
            audit,
            dimension_key,
            confidence_status=expected_status,
        )


def assert_recurrence_empty_collection(
    payload: Mapping[str, Any],
    collection_key: str = "keys",
) -> None:
    """Assert an analytics payload exposes an empty keyed collection."""
    assert payload.get(collection_key) == []


def assert_recurrence_zero_payload(
    payload: Mapping[str, Any],
    **expected_fields: Any,
) -> None:
    """Assert exact zero-state or default field values on a summary or metric mapping."""
    for key, expected in expected_fields.items():
        assert payload.get(key) == expected, (
            f"payload[{key!r}]: expected {expected!r}, got {payload.get(key)!r}"
        )


def assert_recurrence_empty_summary(
    artifact: Mapping[str, Any],
    summary_key: str,
    **expected_fields: Any,
) -> None:
    """Assert zero-state summary fields on a builder artifact."""
    summary = artifact[summary_key]
    assert isinstance(summary, Mapping), f"artifact[{summary_key!r}] must be a mapping"
    assert_recurrence_zero_payload(summary, **expected_fields)
