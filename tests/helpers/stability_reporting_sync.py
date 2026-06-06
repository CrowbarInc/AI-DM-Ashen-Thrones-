"""Stability reporting contract ↔ projection alignment checks (Cycle AT6).

Centralizes structural validation and registry drift assertions for AT1–AT5
reporting surfaces without semantic scoring or acceptance logic.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from tests.stability_reporting_contract import (
    ALLOWED_LONG_SESSION_STABILITY_SCORECARD_FIELDS,
    ALLOWED_STABILITY_HOTSPOT_PRIORITIES,
    ALLOWED_STABILITY_HOTSPOT_ROW_FIELDS,
    ALLOWED_STABILITY_OWNERSHIP_CLASSIFICATION_FIELDS,
    ALLOWED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS,
    ALLOWED_STABILITY_STATUS_VALUES,
    ALLOWED_STABILITY_TREND_LABELS,
    ALLOWED_STABILITY_TREND_ROW_FIELDS,
    REQUIRED_DEGRADATION_FIELDS,
    REQUIRED_FALLBACK_STABILITY_FIELDS,
    REQUIRED_LINEAGE_STABILITY_FIELDS,
    REQUIRED_LONG_SESSION_STABILITY_SCORECARD_FIELDS,
    REQUIRED_OPERATIONAL_SUMMARY_FIELDS,
    REQUIRED_ROUTE_STABILITY_FIELDS,
    REQUIRED_SCORECARD_OWNER_DRIFT_CLASSIFICATION_FIELDS,
    REQUIRED_SPEAKER_STABILITY_FIELDS,
    REQUIRED_STABILITY_AGGREGATION_FIELDS,
    REQUIRED_STABILITY_HISTORY_FIELDS,
    REQUIRED_STABILITY_HOTSPOT_BUCKET_RANKING_FIELDS,
    REQUIRED_STABILITY_HOTSPOT_PAYLOAD_FIELDS,
    REQUIRED_STABILITY_HOTSPOT_ROW_FIELDS,
    REQUIRED_STABILITY_OWNERSHIP_CLASSIFICATION_FIELDS,
    REQUIRED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS,
    REQUIRED_STABILITY_TREND_ROW_FIELDS,
    REQUIRED_STABILITY_TREND_SUMMARY_FIELDS,
    STABILITY_REPORTING_OWNERSHIP,
    stability_reporting_field_registries,
    stability_reporting_governance_manifest,
)


def _unknown_keys(row: Mapping[str, Any], allowed: frozenset[str]) -> list[str]:
    return sorted(key for key in row if key not in allowed)


def _missing_keys(row: Mapping[str, Any], required: frozenset[str]) -> list[str]:
    return sorted(key for key in required if key not in row)


def validate_stability_scorecard(scorecard: Mapping[str, Any] | None) -> list[str]:
    """Return structural validation errors for one long-session stability scorecard."""
    if not isinstance(scorecard, Mapping):
        return ["scorecard must be a mapping"]
    errors: list[str] = []
    errors.extend(f"missing scorecard field: {key}" for key in _missing_keys(scorecard, REQUIRED_LONG_SESSION_STABILITY_SCORECARD_FIELDS))
    errors.extend(f"unknown scorecard field: {key}" for key in _unknown_keys(scorecard, ALLOWED_LONG_SESSION_STABILITY_SCORECARD_FIELDS))

    nested_checks = (
        ("route_stability", REQUIRED_ROUTE_STABILITY_FIELDS),
        ("speaker_stability", REQUIRED_SPEAKER_STABILITY_FIELDS),
        ("fallback_stability", REQUIRED_FALLBACK_STABILITY_FIELDS),
        ("lineage_stability", REQUIRED_LINEAGE_STABILITY_FIELDS),
        ("degradation", REQUIRED_DEGRADATION_FIELDS),
        ("operational_summary", REQUIRED_OPERATIONAL_SUMMARY_FIELDS),
    )
    for section, required in nested_checks:
        payload = scorecard.get(section)
        if not isinstance(payload, Mapping):
            errors.append(f"missing or invalid scorecard section: {section}")
            continue
        errors.extend(
            f"missing {section} field: {key}" for key in _missing_keys(payload, required)
        )

    operational = scorecard.get("operational_summary")
    if isinstance(operational, Mapping):
        status = str(operational.get("stability_status") or "")
        if status and status not in ALLOWED_STABILITY_STATUS_VALUES:
            errors.append(f"unknown stability_status: {status}")

    classifications = scorecard.get("owner_drift_classifications")
    if classifications is None:
        errors.append("missing scorecard field: owner_drift_classifications")
    elif not isinstance(classifications, list):
        errors.append("owner_drift_classifications must be a list")
    else:
        for index, row in enumerate(classifications):
            errors.extend(
                f"owner_drift_classifications[{index}]: {message}"
                for message in validate_scorecard_owner_drift_classification_row(row)
            )

    bucket_counts = scorecard.get("owner_drift_bucket_counts")
    if bucket_counts is None:
        errors.append("missing scorecard field: owner_drift_bucket_counts")
    elif not isinstance(bucket_counts, Mapping):
        errors.append("owner_drift_bucket_counts must be a mapping")

    return errors


def validate_scorecard_owner_drift_classification_row(row: Mapping[str, Any] | None) -> list[str]:
    """Return structural validation errors for one embedded scorecard classification row."""
    if not isinstance(row, Mapping):
        return ["scorecard classification row must be a mapping"]
    errors: list[str] = []
    errors.extend(
        f"missing scorecard classification field: {key}"
        for key in _missing_keys(row, REQUIRED_SCORECARD_OWNER_DRIFT_CLASSIFICATION_FIELDS)
    )
    errors.extend(
        f"unknown scorecard classification field: {key}"
        for key in _unknown_keys(row, REQUIRED_SCORECARD_OWNER_DRIFT_CLASSIFICATION_FIELDS)
    )
    return errors


def validate_stability_ownership_classification_row(row: Mapping[str, Any] | None) -> list[str]:
    """Return structural validation errors for one stability ownership classification row."""
    if not isinstance(row, Mapping):
        return ["classification row must be a mapping"]
    errors: list[str] = []
    errors.extend(
        f"missing classification field: {key}"
        for key in _missing_keys(row, REQUIRED_STABILITY_OWNERSHIP_CLASSIFICATION_FIELDS)
    )
    errors.extend(
        f"unknown classification field: {key}"
        for key in _unknown_keys(row, ALLOWED_STABILITY_OWNERSHIP_CLASSIFICATION_FIELDS)
    )
    return errors


def validate_stability_trend_row(row: Mapping[str, Any] | None) -> list[str]:
    """Return structural validation errors for one stability trend row."""
    if not isinstance(row, Mapping):
        return ["trend row must be a mapping"]
    errors: list[str] = []
    errors.extend(f"missing trend field: {key}" for key in _missing_keys(row, REQUIRED_STABILITY_TREND_ROW_FIELDS))
    errors.extend(f"unknown trend field: {key}" for key in _unknown_keys(row, ALLOWED_STABILITY_TREND_ROW_FIELDS))
    trend = str(row.get("trend") or "")
    if trend and trend not in ALLOWED_STABILITY_TREND_LABELS:
        errors.append(f"unknown trend label: {trend}")
    return errors


def validate_stability_hotspot_row(row: Mapping[str, Any] | None) -> list[str]:
    """Return structural validation errors for one stability hotspot row."""
    if not isinstance(row, Mapping):
        return ["hotspot row must be a mapping"]
    errors: list[str] = []
    errors.extend(
        f"missing hotspot field: {key}" for key in _missing_keys(row, REQUIRED_STABILITY_HOTSPOT_ROW_FIELDS)
    )
    errors.extend(
        f"unknown hotspot field: {key}" for key in _unknown_keys(row, ALLOWED_STABILITY_HOTSPOT_ROW_FIELDS)
    )
    priority = str(row.get("priority") or "")
    if priority and priority not in ALLOWED_STABILITY_HOTSPOT_PRIORITIES:
        errors.append(f"unknown hotspot priority: {priority}")
    trend = str(row.get("trend") or "")
    if trend and trend not in ALLOWED_STABILITY_TREND_LABELS:
        errors.append(f"unknown hotspot trend label: {trend}")
    return errors


def validate_stability_hotspots_payload(payload: Mapping[str, Any] | None) -> list[str]:
    """Return structural validation errors for a stability hotspots aggregate payload."""
    if not isinstance(payload, Mapping):
        return ["hotspots payload must be a mapping"]
    errors: list[str] = []
    errors.extend(
        f"missing hotspots field: {key}" for key in _missing_keys(payload, REQUIRED_STABILITY_HOTSPOT_PAYLOAD_FIELDS)
    )
    for key in ("bucket_rankings", "signal_rankings", "scenario_rankings", "hotspot_rows"):
        value = payload.get(key)
        if value is None:
            continue
        if not isinstance(value, list):
            errors.append(f"{key} must be a list")
    for index, row in enumerate(payload.get("bucket_rankings") or ()):
        if not isinstance(row, Mapping):
            errors.append(f"bucket_rankings[{index}] must be a mapping")
            continue
        errors.extend(
            f"bucket_rankings[{index}]: missing {field}"
            for field in _missing_keys(row, REQUIRED_STABILITY_HOTSPOT_BUCKET_RANKING_FIELDS)
        )
    for index, row in enumerate(payload.get("hotspot_rows") or ()):
        errors.extend(
            f"hotspot_rows[{index}]: {message}" for message in validate_stability_hotspot_row(row)
        )
    return errors


def validate_stability_ownership_payload(payload: Mapping[str, Any] | None) -> list[str]:
    """Return structural validation errors for a stability ownership risk payload."""
    if not isinstance(payload, Mapping):
        return ["stability ownership payload must be a mapping"]
    errors: list[str] = []
    errors.extend(
        f"missing stability ownership field: {key}"
        for key in _missing_keys(payload, REQUIRED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS)
    )
    errors.extend(
        f"unknown stability ownership field: {key}"
        for key in _unknown_keys(payload, ALLOWED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS)
    )

    aggregation = payload.get("aggregation")
    if isinstance(aggregation, Mapping):
        errors.extend(
            f"missing aggregation field: {key}"
            for key in _missing_keys(aggregation, REQUIRED_STABILITY_AGGREGATION_FIELDS)
        )
        for index, row in enumerate(aggregation.get("classification_rows") or ()):
            errors.extend(
                f"aggregation.classification_rows[{index}]: {message}"
                for message in validate_stability_ownership_classification_row(row)
            )
    else:
        errors.append("missing or invalid aggregation section")

    history = payload.get("history")
    if isinstance(history, Mapping):
        errors.extend(
            f"missing history field: {key}" for key in _missing_keys(history, REQUIRED_STABILITY_HISTORY_FIELDS)
        )
        trend_summary = history.get("trend_summary")
        if isinstance(trend_summary, Mapping):
            errors.extend(
                f"missing trend_summary field: {key}"
                for key in _missing_keys(trend_summary, REQUIRED_STABILITY_TREND_SUMMARY_FIELDS)
            )
        else:
            errors.append("missing or invalid history.trend_summary section")
    else:
        errors.append("missing or invalid history section")

    for index, row in enumerate(payload.get("stability_trend_rows") or ()):
        errors.extend(
            f"stability_trend_rows[{index}]: {message}" for message in validate_stability_trend_row(row)
        )

    hotspots = payload.get("stability_hotspots")
    if isinstance(hotspots, Mapping):
        errors.extend(validate_stability_hotspots_payload(hotspots))
    else:
        errors.append("missing or invalid stability_hotspots section")

    return errors


def _registry_drift_messages(
    *,
    label: str,
    observed_keys: frozenset[str],
    required: frozenset[str],
    allowed: frozenset[str],
) -> list[str]:
    messages: list[str] = []
    missing = sorted(required - observed_keys)
    if missing:
        messages.append(f"{label} missing required fields: {missing!r}")
    unknown = sorted(observed_keys - allowed)
    if unknown:
        messages.append(f"{label} has unknown fields: {unknown!r}")
    return messages


def stability_scorecard_contract_misalignments(scorecard: Mapping[str, Any]) -> list[str]:
    """Return scorecard shape drift messages against the public contract."""
    return _registry_drift_messages(
        label="long_session_stability_scorecard",
        observed_keys=frozenset(scorecard),
        required=REQUIRED_LONG_SESSION_STABILITY_SCORECARD_FIELDS,
        allowed=ALLOWED_LONG_SESSION_STABILITY_SCORECARD_FIELDS,
    )


def stability_trend_row_contract_misalignments(row: Mapping[str, Any]) -> list[str]:
    """Return trend-row shape drift messages against the public contract."""
    return _registry_drift_messages(
        label="stability_trend_row",
        observed_keys=frozenset(row),
        required=REQUIRED_STABILITY_TREND_ROW_FIELDS,
        allowed=ALLOWED_STABILITY_TREND_ROW_FIELDS,
    )


def stability_hotspot_row_contract_misalignments(row: Mapping[str, Any]) -> list[str]:
    """Return hotspot-row shape drift messages against the public contract."""
    return _registry_drift_messages(
        label="stability_hotspot_row",
        observed_keys=frozenset(row),
        required=REQUIRED_STABILITY_HOTSPOT_ROW_FIELDS,
        allowed=ALLOWED_STABILITY_HOTSPOT_ROW_FIELDS,
    )


def stability_ownership_payload_contract_misalignments(payload: Mapping[str, Any]) -> list[str]:
    """Return ownership-payload shape drift messages against the public contract."""
    return _registry_drift_messages(
        label="stability_ownership_payload",
        observed_keys=frozenset(payload),
        required=REQUIRED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS,
        allowed=ALLOWED_STABILITY_OWNERSHIP_PAYLOAD_FIELDS,
    )


def assert_stability_scorecard_contract_locked(scorecard: Mapping[str, Any]) -> None:
    misalignments = stability_scorecard_contract_misalignments(scorecard)
    errors = validate_stability_scorecard(scorecard)
    if misalignments or errors:
        joined = "\n".join(f"- {item}" for item in misalignments + errors)
        raise AssertionError(f"stability scorecard contract misalignment:\n{joined}")


def assert_stability_trend_contract_locked(rows: Sequence[Mapping[str, Any]]) -> None:
    misalignments: list[str] = []
    for index, row in enumerate(rows):
        misalignments.extend(
            f"row[{index}]: {message}" for message in stability_trend_row_contract_misalignments(row)
        )
        misalignments.extend(f"row[{index}]: {message}" for message in validate_stability_trend_row(row))
    if misalignments:
        joined = "\n".join(f"- {item}" for item in misalignments)
        raise AssertionError(f"stability trend contract misalignment:\n{joined}")


def assert_stability_hotspot_contract_locked(hotspots: Mapping[str, Any]) -> None:
    misalignments: list[str] = []
    for index, row in enumerate(hotspots.get("hotspot_rows") or ()):
        if isinstance(row, Mapping):
            misalignments.extend(
                f"hotspot_rows[{index}]: {message}"
                for message in stability_hotspot_row_contract_misalignments(row)
            )
    misalignments.extend(validate_stability_hotspots_payload(hotspots))
    if misalignments:
        joined = "\n".join(f"- {item}" for item in misalignments)
        raise AssertionError(f"stability hotspot contract misalignment:\n{joined}")


def assert_stability_ownership_contract_locked(payload: Mapping[str, Any]) -> None:
    misalignments = stability_ownership_payload_contract_misalignments(payload)
    errors = validate_stability_ownership_payload(payload)
    if misalignments or errors:
        joined = "\n".join(f"- {item}" for item in misalignments + errors)
        raise AssertionError(f"stability ownership contract misalignment:\n{joined}")


def assert_stability_reporting_boundary_documented() -> None:
    manifest = stability_reporting_governance_manifest()
    if manifest.get("advisory_only") is not True:
        raise AssertionError("stability reporting must remain advisory_only")
    if manifest.get("report_only") is not True:
        raise AssertionError("stability reporting must remain report_only")
    if manifest.get("gameplay_ownership") is not False:
        raise AssertionError("stability reporting must not claim gameplay ownership")
    if manifest.get("acceptance_ownership") is not False:
        raise AssertionError("stability reporting must not claim acceptance ownership")
    if manifest.get("acceptance_threshold_ownership") is not False:
        raise AssertionError("stability reporting must not claim acceptance-threshold ownership")
    if set(STABILITY_REPORTING_OWNERSHIP) != {"golden_replay", "taxonomy", "risk_reporting", "dashboard_reporting", "contract"}:
        raise AssertionError("stability reporting ownership boundaries changed unexpectedly")
    if stability_reporting_field_registries().keys() != {
        "long_session_stability_scorecard",
        "scorecard_owner_drift_classification",
        "stability_ownership_classification",
        "stability_trend_row",
        "stability_hotspot_row",
        "stability_ownership_payload",
    }:
        raise AssertionError("stability reporting field registries changed unexpectedly")
