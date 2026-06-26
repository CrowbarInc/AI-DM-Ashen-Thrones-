"""Confidence calibration, outcome validation, and markdown report rendering.

**Owns (CG-4):** confidence calibration status, graduation threshold validation
status, blind-spot status change, outcome signal/rejection vocabularies, final
graduation recommendation, and recurrence markdown/JSON report serialization.

**Consumes/displays:** trend, forecast, governance, lifecycle, maturity, and
remediation payloads from history/statistics — does not own those classifiers.

**Does not own:** any recurrence classifier thresholds or recurrence:v1 identity.

Registry: ``docs/audits/CG_recurrence_taxonomy_registry.md``
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.helpers.failure_dashboard_paths import RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH
from tests.helpers.replay_drift_taxonomy import ALLOWED_OWNER_DRIFT_BUCKETS

from tests.helpers.replay_bug_recurrence_events import *  # noqa: F403
from tests.helpers.replay_bug_recurrence_history import *  # noqa: F403
from tests.helpers.replay_bug_recurrence_statistics import *  # noqa: F403
from tests.helpers.replay_bug_recurrence_history import _parse_iso_timestamp
from tests.helpers.replay_bug_recurrence_statistics import (
    _clamp_maturity_score,
    _maturity_volume_factor,
)

RECURRENCE_CONFIDENCE_CALIBRATION_TOLERANCE = 0.10
RECURRENCE_CONFIDENCE_CALIBRATION_DOC_PATH = Path("docs/audits/BQC3_confidence_calibration_audit.md")
RECURRENCE_CONFIDENCE_STATUS_UNDERCONFIDENT = "underconfident"
RECURRENCE_CONFIDENCE_STATUS_CALIBRATED = "calibrated"
RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT = "overconfident"
RECURRENCE_CONFIDENCE_STATUSES: frozenset[str] = frozenset(
    {
        RECURRENCE_CONFIDENCE_STATUS_UNDERCONFIDENT,
        RECURRENCE_CONFIDENCE_STATUS_CALIBRATED,
        RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT,
    }
)
RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED = "supported"
RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC = "optimistic"
RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED = "unsupported"
RECURRENCE_GRADUATION_THRESHOLD_STATUSES: frozenset[str] = frozenset(
    {
        RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED,
        RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC,
        RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED,
    }
)
RECURRENCE_BLIND_SPOT_REDUCED = "reduced"
RECURRENCE_BLIND_SPOT_PARTIALLY_REDUCED = "partially_reduced"
RECURRENCE_BLIND_SPOT_UNCHANGED = "unchanged"
RECURRENCE_BLIND_SPOT_ESCALATED = "escalated"
RECURRENCE_CONFIDENCE_CALIBRATION_DEFINITION = (
    "Advisory confidence calibration compares reported confidence metrics against evidence "
    "strength derived from protected replay observation volume, key coverage, trajectory "
    "availability, forecast accuracy, governance posture, and lifecycle/remediation outcomes. "
    "calibration_gap = reported_confidence - evidence_strength. Positive gaps indicate "
    "overconfidence; negative gaps indicate underconfidence; gaps within tolerance indicate calibration."
)
RECURRENCE_CONFIDENCE_CALIBRATION_SCORE_DEFINITION = (
    "Advisory 0-100 calibration score: 100 * (1 - average(abs(calibration_gap))) minus 5 points "
    "per component with overconfident status and gap > 0.20. Interpretation: 90-100 well calibrated; "
    "70-89 acceptable; 50-69 needs monitoring; <50 significant calibration risk."
)
RECURRENCE_FORECAST_EVIDENCE_DEFINITION = (
    "Weighted blend: 30% observation volume factor min(1, observations/5), 20% key coverage "
    "factor min(1, keys/3), 25% trajectory factor (1.0 when trajectory_available else 0.4), "
    "25% accuracy evidence forecast_accuracy * observation volume factor."
)
RECURRENCE_GOVERNANCE_EVIDENCE_DEFINITION = (
    "Weighted blend: 30% observation volume factor, 25% watchlist coverage "
    "watchlist_size/max(keys,1), 20% owner dispersion 1 - owner_concentration_ratio, "
    "25% governance_health_score/100."
)
RECURRENCE_EFFECTIVENESS_EVIDENCE_DEFINITION = (
    "Weighted blend: 25% trajectory factor (1.0 when trajectory_available else 0.4), "
    "25% remediation effectiveness, 25% closure_rate, 25% lifecycle_health_score/100."
)
BQ16_CALIBRATION_BLIND_SPOT_IDS: tuple[str, ...] = (
    "recurrence_data_quality",
    "recurrence_trajectory_history",
    "recurrence_model_calibration",
    "recurrence_ownership_drift",
    "recurrence_confidence_decay",
    "recurrence_auditability",
)
BQ16_CALIBRATION_BLIND_SPOT_SEVERITIES: dict[str, str] = {
    "recurrence_data_quality": "critical",
    "recurrence_trajectory_history": "critical",
    "recurrence_model_calibration": "high",
    "recurrence_ownership_drift": "medium",
    "recurrence_confidence_decay": "medium",
    "recurrence_auditability": "low",
}


def _confidence_calibration_status(
    reported_confidence: float,
    evidence_strength: float,
    *,
    tolerance: float = RECURRENCE_CONFIDENCE_CALIBRATION_TOLERANCE,
) -> str:
    gap = float(reported_confidence or 0.0) - float(evidence_strength or 0.0)
    if gap > tolerance:
        return RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT
    if gap < -tolerance:
        return RECURRENCE_CONFIDENCE_STATUS_UNDERCONFIDENT
    return RECURRENCE_CONFIDENCE_STATUS_CALIBRATED


def _forecast_evidence_strength(
    *,
    total_observations: int,
    total_keys: int,
    forecast_accuracy: float,
    trajectory_available: bool,
) -> float:
    observations = max(int(total_observations or 0), 0)
    keys = max(int(total_keys or 0), 0)
    observation_factor = min(1.0, observations / float(RECURRENCE_FORECAST_CONFIDENCE_OBSERVATIONS))
    key_factor = min(1.0, keys / float(RECURRENCE_PROGRAM_EFFECTIVENESS_MIN_KEYS))
    trajectory_factor = 1.0 if trajectory_available else 0.4
    accuracy = max(min(float(forecast_accuracy or 0.0), 1.0), 0.0)
    accuracy_evidence = accuracy * observation_factor
    return round(
        min(
            1.0,
            0.30 * observation_factor
            + 0.20 * key_factor
            + 0.25 * trajectory_factor
            + 0.25 * accuracy_evidence,
        ),
        2,
    )


def _governance_evidence_strength(
    *,
    total_observations: int,
    total_keys: int,
    watchlist_size: int,
    owner_concentration_ratio: float,
    governance_health_score: float,
) -> float:
    observations = max(int(total_observations or 0), 0)
    keys = max(int(total_keys or 0), 1)
    watchlist = max(int(watchlist_size or 0), 0)
    observation_factor = min(1.0, observations / float(RECURRENCE_FORECAST_CONFIDENCE_OBSERVATIONS))
    watchlist_coverage = min(1.0, watchlist / float(keys))
    owner_dispersion = 1.0 - max(min(float(owner_concentration_ratio or 0.0), 1.0), 0.0)
    governance_health_factor = max(min(float(governance_health_score or 0.0), 100.0), 0.0) / 100.0
    return round(
        min(
            1.0,
            0.30 * observation_factor
            + 0.25 * watchlist_coverage
            + 0.20 * owner_dispersion
            + 0.25 * governance_health_factor,
        ),
        2,
    )


def _effectiveness_evidence_strength(
    *,
    trajectory_available: bool,
    remediation_effectiveness: float,
    closure_rate: float,
    lifecycle_health_score: float,
) -> float:
    trajectory_factor = 1.0 if trajectory_available else 0.4
    remediation = max(min(float(remediation_effectiveness or 0.0), 1.0), 0.0)
    closure = max(min(float(closure_rate or 0.0), 1.0), 0.0)
    lifecycle_health_factor = max(min(float(lifecycle_health_score or 0.0), 100.0), 0.0) / 100.0
    return round(
        min(
            1.0,
            0.25 * trajectory_factor
            + 0.25 * remediation
            + 0.25 * closure
            + 0.25 * lifecycle_health_factor,
        ),
        2,
    )


def _audit_forecast_confidence(
    *,
    recurrence_forecast: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    recurrence_trajectory_summary: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    forecast_effectiveness = effectiveness.get("forecast_effectiveness_summary")
    if not isinstance(forecast_effectiveness, Mapping):
        forecast_effectiveness = {}
    trajectory_available = bool(
        trajectory.get("trajectory_available")
        or (effectiveness.get("portfolio_trajectory_summary") or {}).get("trajectory_available")
    )
    reported_confidence = float(forecast_summary.get("forecast_confidence") or 0.0)
    forecast_accuracy = float(forecast_effectiveness.get("forecast_accuracy") or 0.0)
    evidence_strength = _forecast_evidence_strength(
        total_observations=total_observations,
        total_keys=total_keys,
        forecast_accuracy=forecast_accuracy,
        trajectory_available=trajectory_available,
    )
    calibration_gap = round(reported_confidence - evidence_strength, 2)
    return {
        "reported_confidence": reported_confidence,
        "evidence_strength": evidence_strength,
        "calibration_gap": calibration_gap,
        "confidence_status": _confidence_calibration_status(reported_confidence, evidence_strength),
        "forecast_accuracy": forecast_accuracy,
        "total_observations": total_observations,
        "total_keys": total_keys,
        "trajectory_available": trajectory_available,
        "evidence_definition": RECURRENCE_FORECAST_EVIDENCE_DEFINITION,
    }


def _audit_governance_confidence(
    *,
    recurrence_governance: Mapping[str, Any] | None,
    recurrence_portfolio_summary: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    portfolio_summary = recurrence_portfolio_summary if isinstance(recurrence_portfolio_summary, Mapping) else {}
    governance_summary = governance.get("governance_summary")
    if not isinstance(governance_summary, Mapping):
        governance_summary = {}
    watchlist = [row for row in (governance.get("watchlist") or ()) if isinstance(row, Mapping)]
    owners = [row for row in (governance.get("owners") or ()) if isinstance(row, Mapping)]
    owner_concentration = float(portfolio_summary.get("owner_concentration_ratio") or 0.0)
    if owners:
        owner_loads = [int(row.get("watchlist_entries") or row.get("governance_load") or 0) for row in owners]
        total_load = sum(owner_loads) or 1
        owner_concentration = max(owner_concentration, max(owner_loads) / float(total_load))
    reported_confidence = float(
        governance_summary.get("governance_confidence") or governance.get("governance_confidence") or 0.0
    )
    governance_health_score = float(
        governance_summary.get("governance_health_score") or governance.get("governance_health_score") or 0.0
    )
    evidence_strength = _governance_evidence_strength(
        total_observations=total_observations,
        total_keys=total_keys,
        watchlist_size=len(watchlist),
        owner_concentration_ratio=owner_concentration,
        governance_health_score=governance_health_score,
    )
    calibration_gap = round(reported_confidence - evidence_strength, 2)
    return {
        "reported_confidence": reported_confidence,
        "evidence_strength": evidence_strength,
        "calibration_gap": calibration_gap,
        "confidence_status": _confidence_calibration_status(reported_confidence, evidence_strength),
        "watchlist_size": len(watchlist),
        "total_observations": total_observations,
        "owner_count": len(owners),
        "owner_concentration_ratio": round(owner_concentration, 4),
        "governance_health_score": governance_health_score,
        "evidence_definition": RECURRENCE_GOVERNANCE_EVIDENCE_DEFINITION,
    }


def _audit_effectiveness_confidence(
    *,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    recurrence_lifecycle: Mapping[str, Any] | None,
    recurrence_trajectory_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    lifecycle = recurrence_lifecycle if isinstance(recurrence_lifecycle, Mapping) else {}
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    program_summary = effectiveness.get("program_effectiveness_summary")
    if not isinstance(program_summary, Mapping):
        program_summary = {}
    lifecycle_summary = lifecycle.get("lifecycle_summary")
    if not isinstance(lifecycle_summary, Mapping):
        lifecycle_summary = {}
    remediation = effectiveness.get("remediation_effectiveness_summary")
    if not isinstance(remediation, Mapping):
        remediation = {}
    closure = lifecycle.get("closure_effectiveness")
    if not isinstance(closure, Mapping):
        closure = {}
    trajectory_available = bool(
        trajectory.get("trajectory_available")
        or (effectiveness.get("portfolio_trajectory_summary") or {}).get("trajectory_available")
    )
    reported_confidence = float(program_summary.get("effectiveness_confidence") or 0.0)
    remediation_effectiveness = float(
        remediation.get("remediation_effectiveness") or program_summary.get("remediation_effectiveness") or 0.0
    )
    closure_rate = float(closure.get("closure_rate") or lifecycle_summary.get("closure_rate") or 0.0)
    lifecycle_health_score = float(
        lifecycle_summary.get("lifecycle_health_score") or lifecycle.get("lifecycle_health_score") or 0.0
    )
    evidence_strength = _effectiveness_evidence_strength(
        trajectory_available=trajectory_available,
        remediation_effectiveness=remediation_effectiveness,
        closure_rate=closure_rate,
        lifecycle_health_score=lifecycle_health_score,
    )
    calibration_gap = round(reported_confidence - evidence_strength, 2)
    return {
        "reported_confidence": reported_confidence,
        "evidence_strength": evidence_strength,
        "calibration_gap": calibration_gap,
        "confidence_status": _confidence_calibration_status(reported_confidence, evidence_strength),
        "trajectory_available": trajectory_available,
        "remediation_effectiveness": remediation_effectiveness,
        "closure_rate": closure_rate,
        "lifecycle_health_score": lifecycle_health_score,
        "evidence_definition": RECURRENCE_EFFECTIVENESS_EVIDENCE_DEFINITION,
    }


def _validate_graduation_confidence_thresholds(
    *,
    forecast_audit: Mapping[str, Any],
    governance_audit: Mapping[str, Any],
    effectiveness_audit: Mapping[str, Any],
    recurrence_maturity: Mapping[str, Any] | None,
    recurrence_completion: Mapping[str, Any] | None,
    recurrence_trajectory_summary: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    maturity = recurrence_maturity if isinstance(recurrence_maturity, Mapping) else {}
    completion = recurrence_completion if isinstance(recurrence_completion, Mapping) else {}
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    maturity_summary = maturity.get("recurrence_maturity_summary")
    if not isinstance(maturity_summary, Mapping):
        maturity_summary = {}
    completion_summary = completion.get("recurrence_completion_summary")
    if not isinstance(completion_summary, Mapping):
        completion_summary = {}

    forecast_confidence = float(forecast_audit.get("reported_confidence") or 0.0)
    effectiveness_confidence = float(effectiveness_audit.get("reported_confidence") or 0.0)
    operational_readiness = float(maturity_summary.get("operational_readiness_score") or 0.0)
    trajectory_available = bool(forecast_audit.get("trajectory_available"))
    snapshot_count = int(trajectory.get("snapshot_count") or 0)

    rows: list[dict[str, Any]] = []

    if forecast_confidence >= RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET:
        if str(forecast_audit.get("confidence_status")) == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT:
            forecast_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
            forecast_rationale = (
                "Forecast confidence meets graduation threshold but exceeds evidence strength; "
                "treat as structurally met, not empirically validated."
            )
        elif float(forecast_audit.get("evidence_strength") or 0.0) >= RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET:
            forecast_status = RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED
            forecast_rationale = "Forecast confidence and evidence strength both meet graduation threshold."
        else:
            forecast_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
            forecast_rationale = (
                "Forecast confidence meets threshold via observation volume, but supporting evidence "
                "remains below target."
            )
    else:
        forecast_status = RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED
        forecast_rationale = "Forecast confidence remains below graduation threshold."

    rows.append(
        {
            "threshold": "forecast_confidence",
            "current_value": forecast_confidence,
            "target_value": RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET,
            "validation_status": forecast_status,
            "rationale": forecast_rationale,
        }
    )

    if effectiveness_confidence >= RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET:
        if str(effectiveness_audit.get("confidence_status")) == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT:
            effectiveness_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
            effectiveness_rationale = (
                "Effectiveness confidence meets threshold but substantially exceeds remediation, "
                "closure, and trajectory evidence."
            )
        elif float(effectiveness_audit.get("evidence_strength") or 0.0) >= RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET:
            effectiveness_status = RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED
            effectiveness_rationale = "Effectiveness confidence and evidence strength both meet graduation threshold."
        else:
            effectiveness_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
            effectiveness_rationale = (
                "Effectiveness confidence meets threshold structurally but outcome evidence remains thin."
            )
    else:
        effectiveness_status = RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED
        effectiveness_rationale = "Effectiveness confidence remains below graduation threshold."

    rows.append(
        {
            "threshold": "effectiveness_confidence",
            "current_value": effectiveness_confidence,
            "target_value": RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET,
            "validation_status": effectiveness_status,
            "rationale": effectiveness_rationale,
        }
    )

    if operational_readiness >= RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET:
        if float(maturity_summary.get("overall_maturity_score") or 0.0) < RECURRENCE_COMPLETION_OVERALL_MATURITY_TARGET:
            readiness_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
            readiness_rationale = (
                "Operational readiness meets target while overall maturity remains below program target."
            )
        else:
            readiness_status = RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED
            readiness_rationale = "Operational readiness and maturity posture support graduation threshold."
    elif operational_readiness >= RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET - 5.0:
        readiness_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
        readiness_rationale = (
            f"Operational readiness is within 5 points of target ({operational_readiness:.1f} vs "
            f"{RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET:.1f})."
        )
    else:
        readiness_status = RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED
        readiness_rationale = "Operational readiness remains materially below graduation threshold."

    rows.append(
        {
            "threshold": "operational_readiness",
            "current_value": operational_readiness,
            "target_value": RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET,
            "validation_status": readiness_status,
            "rationale": readiness_rationale,
        }
    )

    if trajectory_available:
        trajectory_status = RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED
        trajectory_rationale = "Longitudinal trajectory comparison is active across two or more snapshots."
    elif snapshot_count >= 1:
        trajectory_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
        trajectory_rationale = (
            "Trajectory baseline exists but trajectory_available remains false until snapshot #2 is captured."
        )
    else:
        trajectory_status = RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED
        trajectory_rationale = "No trajectory baseline exists for protected replay recurrence analytics."

    rows.append(
        {
            "threshold": "trajectory_available",
            "current_value": trajectory_available,
            "target_value": True,
            "validation_status": trajectory_status,
            "rationale": trajectory_rationale,
        }
    )

    governance_confidence = float(governance_audit.get("reported_confidence") or 0.0)
    if governance_confidence >= RECURRENCE_COMPLETION_GOVERNANCE_CONFIDENCE_TARGET:
        if str(governance_audit.get("confidence_status")) == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT:
            governance_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
            governance_rationale = (
                "Governance confidence meets threshold but exceeds governance health and funnel evidence."
            )
        elif float(governance_audit.get("evidence_strength") or 0.0) >= RECURRENCE_COMPLETION_GOVERNANCE_CONFIDENCE_TARGET:
            governance_status = RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED
            governance_rationale = "Governance confidence and evidence strength both meet graduation threshold."
        else:
            governance_status = RECURRENCE_GRADUATION_THRESHOLD_OPTIMISTIC
            governance_rationale = "Governance confidence meets threshold structurally but health score remains moderate."
    else:
        governance_status = RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED
        governance_rationale = "Governance confidence remains below graduation threshold."

    rows.append(
        {
            "threshold": "governance_confidence",
            "current_value": governance_confidence,
            "target_value": RECURRENCE_COMPLETION_GOVERNANCE_CONFIDENCE_TARGET,
            "validation_status": governance_status,
            "rationale": governance_rationale,
        }
    )

    if bool(completion_summary.get("program_graduated")):
        rows.append(
            {
                "threshold": "program_graduated",
                "current_value": True,
                "target_value": True,
                "validation_status": RECURRENCE_GRADUATION_THRESHOLD_SUPPORTED,
                "rationale": "Completion assessment marks program as graduated.",
            }
        )

    return rows


def _reassess_calibration_blind_spots(
    *,
    total_observations: int,
    total_keys: int,
    forecast_audit: Mapping[str, Any],
    effectiveness_audit: Mapping[str, Any],
    recurrence_trajectory_summary: Mapping[str, Any] | None,
    recurrence_history: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    volume_factor = _maturity_volume_factor(total_observations=total_observations, total_keys=total_keys)
    trajectory_available = bool(trajectory.get("trajectory_available"))
    snapshot_count = int(trajectory.get("snapshot_count") or 0)
    has_trajectory_infrastructure = snapshot_count >= 1 or bool(history.get("recurrence_trajectory_history"))

    reassessments: list[dict[str, Any]] = []

    data_quality_status = (
        RECURRENCE_BLIND_SPOT_REDUCED
        if volume_factor >= 0.5
        else RECURRENCE_BLIND_SPOT_UNCHANGED
    )
    reassessments.append(
        {
            "blind_spot_id": "recurrence_data_quality",
            "bq16_severity": BQ16_CALIBRATION_BLIND_SPOT_SEVERITIES["recurrence_data_quality"],
            "status_change": data_quality_status,
            "current_severity": "medium" if data_quality_status == RECURRENCE_BLIND_SPOT_REDUCED else "critical",
            "rationale": (
                "Protected replay observation and key volume now meet maturity confidence thresholds."
                if data_quality_status == RECURRENCE_BLIND_SPOT_REDUCED
                else "Protected replay volume remains below maturity confidence thresholds."
            ),
            "blockers_remaining": [] if data_quality_status == RECURRENCE_BLIND_SPOT_REDUCED else [
                "Continue protected replay observation collection."
            ],
        }
    )

    if trajectory_available:
        trajectory_status = RECURRENCE_BLIND_SPOT_REDUCED
        trajectory_rationale = "Longitudinal trajectory comparison is active."
        trajectory_severity = "low"
        trajectory_blockers: list[str] = []
    elif has_trajectory_infrastructure:
        trajectory_status = RECURRENCE_BLIND_SPOT_PARTIALLY_REDUCED
        trajectory_rationale = (
            "Trajectory infrastructure and baseline snapshot exist; trajectory_available remains false "
            "until snapshot #2."
        )
        trajectory_severity = "high"
        trajectory_blockers = ["Capture snapshot #2 to activate trajectory comparisons."]
    else:
        trajectory_status = RECURRENCE_BLIND_SPOT_UNCHANGED
        trajectory_rationale = "No longitudinal trajectory baseline exists."
        trajectory_severity = "critical"
        trajectory_blockers = ["Establish trajectory baseline snapshots."]

    reassessments.append(
        {
            "blind_spot_id": "recurrence_trajectory_history",
            "bq16_severity": BQ16_CALIBRATION_BLIND_SPOT_SEVERITIES["recurrence_trajectory_history"],
            "status_change": trajectory_status,
            "current_severity": trajectory_severity,
            "rationale": trajectory_rationale,
            "blockers_remaining": trajectory_blockers,
        }
    )

    forecast_status = str(forecast_audit.get("confidence_status") or "")
    forecast_gap = float(forecast_audit.get("calibration_gap") or 0.0)
    if forecast_status == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT and forecast_gap > 0.15:
        calibration_status = RECURRENCE_BLIND_SPOT_ESCALATED
        calibration_rationale = (
            "Forecast confidence exceeds evidence strength despite high reported accuracy; "
            "calibration audit flags overconfidence risk."
        )
        calibration_severity = "critical"
        calibration_blockers = ["Recalibrate forecast confidence or expand validation volume before graduation."]
    elif forecast_status == RECURRENCE_CONFIDENCE_STATUS_CALIBRATED:
        calibration_status = RECURRENCE_BLIND_SPOT_REDUCED
        calibration_rationale = "Forecast confidence aligns with evidence strength."
        calibration_severity = "low"
        calibration_blockers = []
    else:
        calibration_status = RECURRENCE_BLIND_SPOT_PARTIALLY_REDUCED
        calibration_rationale = (
            "Volume thresholds met, but forecast confidence calibration still warrants monitoring."
        )
        calibration_severity = "medium"
        calibration_blockers = ["Monitor forecast accuracy as observation volume grows."]

    reassessments.append(
        {
            "blind_spot_id": "recurrence_model_calibration",
            "bq16_severity": BQ16_CALIBRATION_BLIND_SPOT_SEVERITIES["recurrence_model_calibration"],
            "status_change": calibration_status,
            "current_severity": calibration_severity,
            "rationale": calibration_rationale,
            "blockers_remaining": calibration_blockers,
        }
    )

    reassessments.append(
        {
            "blind_spot_id": "recurrence_ownership_drift",
            "bq16_severity": BQ16_CALIBRATION_BLIND_SPOT_SEVERITIES["recurrence_ownership_drift"],
            "status_change": RECURRENCE_BLIND_SPOT_UNCHANGED,
            "current_severity": "medium",
            "rationale": "Recurrence ownership drift is still not tracked as a dedicated longitudinal signal.",
            "blockers_remaining": ["Monitor owner_drift_bucket transitions separately from recurrence lifecycle."],
        }
    )

    reassessments.append(
        {
            "blind_spot_id": "recurrence_confidence_decay",
            "bq16_severity": BQ16_CALIBRATION_BLIND_SPOT_SEVERITIES["recurrence_confidence_decay"],
            "status_change": RECURRENCE_BLIND_SPOT_UNCHANGED,
            "current_severity": "medium",
            "rationale": "Confidence scores still do not decay with stale observations or aging keys.",
            "blockers_remaining": ["Consider temporal decay modeling if history spans long idle periods."],
        }
    )

    auditability_status = (
        RECURRENCE_BLIND_SPOT_PARTIALLY_REDUCED
        if has_trajectory_infrastructure
        else RECURRENCE_BLIND_SPOT_UNCHANGED
    )
    reassessments.append(
        {
            "blind_spot_id": "recurrence_auditability",
            "bq16_severity": BQ16_CALIBRATION_BLIND_SPOT_SEVERITIES["recurrence_auditability"],
            "status_change": auditability_status,
            "current_severity": "low" if auditability_status == RECURRENCE_BLIND_SPOT_PARTIALLY_REDUCED else "low",
            "rationale": (
                "Trajectory history artifacts provide versioned snapshots, but no immutable audit chain exists."
                if auditability_status == RECURRENCE_BLIND_SPOT_PARTIALLY_REDUCED
                else "No immutable audit chain links recurrence analytics revisions over time."
            ),
            "blockers_remaining": (
                ["Retain versioned history artifacts for audit replay if formal compliance is required."]
            ),
        }
    )

    if str(effectiveness_audit.get("confidence_status")) == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT:
        reassessments.append(
            {
                "blind_spot_id": "recurrence_effectiveness_overconfidence",
                "bq16_severity": "high",
                "status_change": RECURRENCE_BLIND_SPOT_ESCALATED,
                "current_severity": "high",
                "rationale": (
                    "Effectiveness confidence substantially exceeds remediation, closure, and trajectory evidence."
                ),
                "blockers_remaining": [
                    "Do not treat effectiveness confidence as graduation-ready without outcome validation."
                ],
            }
        )

    return reassessments


def calculate_confidence_calibration_score(
    *,
    forecast_confidence_audit: Mapping[str, Any] | None,
    governance_confidence_audit: Mapping[str, Any] | None,
    effectiveness_confidence_audit: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Calculate protected replay recurrence confidence calibration score."""
    audits = [
        forecast_confidence_audit if isinstance(forecast_confidence_audit, Mapping) else {},
        governance_confidence_audit if isinstance(governance_confidence_audit, Mapping) else {},
        effectiveness_confidence_audit if isinstance(effectiveness_confidence_audit, Mapping) else {},
    ]
    gaps = [abs(float(row.get("calibration_gap") or 0.0)) for row in audits]
    largest_gap = max(gaps) if gaps else 0.0
    average_gap = sum(gaps) / float(len(gaps)) if gaps else 0.0
    severe_overconfidence = sum(
        1
        for row in audits
        if str(row.get("confidence_status")) == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT
        and float(row.get("calibration_gap") or 0.0) > 0.20
    )
    raw_score = 100.0 * (1.0 - average_gap) - severe_overconfidence * 5.0
    confidence_calibration_score = round(_clamp_maturity_score(raw_score), 1)
    if confidence_calibration_score >= 90.0:
        interpretation = "well_calibrated"
        interpretation_label = "Well calibrated"
    elif confidence_calibration_score >= 70.0:
        interpretation = "acceptable"
        interpretation_label = "Acceptable"
    elif confidence_calibration_score >= 50.0:
        interpretation = "needs_monitoring"
        interpretation_label = "Needs monitoring"
    else:
        interpretation = "significant_calibration_risk"
        interpretation_label = "Significant calibration risk"

    forecast_status = str(audits[0].get("confidence_status") or RECURRENCE_CONFIDENCE_STATUS_CALIBRATED)
    governance_status = str(audits[1].get("confidence_status") or RECURRENCE_CONFIDENCE_STATUS_CALIBRATED)
    effectiveness_status = str(audits[2].get("confidence_status") or RECURRENCE_CONFIDENCE_STATUS_CALIBRATED)
    graduation_confidence_ready = (
        confidence_calibration_score >= 70.0
        and largest_gap <= 0.20
        and severe_overconfidence == 0
        and forecast_status != RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT
        and governance_status != RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT
        and effectiveness_status != RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT
    )

    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "protected_replay_only": True,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "forecast_status": forecast_status,
        "governance_status": governance_status,
        "effectiveness_status": effectiveness_status,
        "confidence_calibration_score": confidence_calibration_score,
        "interpretation": interpretation,
        "interpretation_label": interpretation_label,
        "largest_calibration_gap": round(largest_gap, 2),
        "average_calibration_gap": round(average_gap, 2),
        "severe_overconfidence_count": severe_overconfidence,
        "graduation_confidence_ready": graduation_confidence_ready,
        "score_definition": RECURRENCE_CONFIDENCE_CALIBRATION_SCORE_DEFINITION,
    }


def build_recurrence_confidence_audit(
    *,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
    recurrence_maturity: Mapping[str, Any] | None = None,
    recurrence_completion: Mapping[str, Any] | None = None,
    recurrence_trajectory_summary: Mapping[str, Any] | None = None,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_portfolio_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence confidence calibration audit."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    portfolio_summary = recurrence_portfolio_summary if isinstance(recurrence_portfolio_summary, Mapping) else {}
    if not portfolio_summary and isinstance(history.get("recurrence_portfolio_summary"), Mapping):
        portfolio_summary = history["recurrence_portfolio_summary"]
    total_observations = int(
        history.get("total_rows") or portfolio_summary.get("total_observations") or 0
    )
    total_keys = int(
        history.get("unique_recurrence_count") or portfolio_summary.get("total_keys") or 0
    )

    forecast_confidence_audit = _audit_forecast_confidence(
        recurrence_forecast=recurrence_forecast,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
        total_observations=total_observations,
        total_keys=total_keys,
    )
    governance_confidence_audit = _audit_governance_confidence(
        recurrence_governance=recurrence_governance,
        recurrence_portfolio_summary=portfolio_summary,
        total_observations=total_observations,
        total_keys=total_keys,
    )
    lifecycle = recurrence_lifecycle if isinstance(recurrence_lifecycle, Mapping) else {}
    if not lifecycle and isinstance(history.get("recurrence_lifecycle"), Mapping):
        lifecycle = history["recurrence_lifecycle"]
    effectiveness_confidence_audit = _audit_effectiveness_confidence(
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_lifecycle=lifecycle,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
    )
    graduation_threshold_validation = _validate_graduation_confidence_thresholds(
        forecast_audit=forecast_confidence_audit,
        governance_audit=governance_confidence_audit,
        effectiveness_audit=effectiveness_confidence_audit,
        recurrence_maturity=recurrence_maturity,
        recurrence_completion=recurrence_completion,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
    )
    blind_spot_reassessment = _reassess_calibration_blind_spots(
        total_observations=total_observations,
        total_keys=total_keys,
        forecast_audit=forecast_confidence_audit,
        effectiveness_audit=effectiveness_confidence_audit,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
        recurrence_history=history,
    )
    confidence_calibration_summary = calculate_confidence_calibration_score(
        forecast_confidence_audit=forecast_confidence_audit,
        governance_confidence_audit=governance_confidence_audit,
        effectiveness_confidence_audit=effectiveness_confidence_audit,
    )
    recommended_actions = _confidence_calibration_recommended_actions(
        confidence_calibration_summary=confidence_calibration_summary,
        graduation_threshold_validation=graduation_threshold_validation,
        blind_spot_reassessment=blind_spot_reassessment,
        forecast_audit=forecast_confidence_audit,
        effectiveness_audit=effectiveness_confidence_audit,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
    )
    audit_without_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "calibration_definition": RECURRENCE_CONFIDENCE_CALIBRATION_DEFINITION,
        "forecast_confidence_audit": forecast_confidence_audit,
        "governance_confidence_audit": governance_confidence_audit,
        "effectiveness_confidence_audit": effectiveness_confidence_audit,
        "graduation_threshold_validation": graduation_threshold_validation,
        "blind_spot_reassessment": blind_spot_reassessment,
        "recommended_actions": recommended_actions,
    }
    recurrence_confidence_calibration_summary = summarize_recurrence_confidence_calibration(
        audit_without_summary,
        confidence_calibration_summary=confidence_calibration_summary,
    )
    return {
        **audit_without_summary,
        "recurrence_confidence_calibration_summary": recurrence_confidence_calibration_summary,
    }


def _confidence_calibration_recommended_actions(
    *,
    confidence_calibration_summary: Mapping[str, Any],
    graduation_threshold_validation: Sequence[Mapping[str, Any]] | None,
    blind_spot_reassessment: Sequence[Mapping[str, Any]] | None,
    forecast_audit: Mapping[str, Any],
    effectiveness_audit: Mapping[str, Any],
    recurrence_trajectory_summary: Mapping[str, Any] | None,
) -> list[str]:
    actions: list[str] = []
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    if not bool(trajectory.get("trajectory_available")):
        actions.append("Capture snapshot #2 to activate trajectory_available before final graduation audit.")
    if str(forecast_audit.get("confidence_status")) == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT:
        actions.append(
            "Treat forecast confidence as volume-saturated; prioritize forecast validation over threshold celebration."
        )
    if str(effectiveness_audit.get("confidence_status")) == RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT:
        actions.append(
            "Do not treat effectiveness confidence as graduation-ready until remediation and closure evidence exists."
        )
    unsupported = [
        row
        for row in (graduation_threshold_validation or ())
        if isinstance(row, Mapping)
        and row.get("validation_status") == RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED
    ]
    if unsupported:
        actions.append(
            "Resolve unsupported graduation thresholds before closing the BQ recurrence program."
        )
    for row in blind_spot_reassessment or ():
        if not isinstance(row, Mapping):
            continue
        if row.get("status_change") in {RECURRENCE_BLIND_SPOT_UNCHANGED, RECURRENCE_BLIND_SPOT_ESCALATED}:
            blockers = row.get("blockers_remaining")
            if isinstance(blockers, list):
                actions.extend(str(item) for item in blockers if str(item).strip())
    if not actions:
        if bool(confidence_calibration_summary.get("graduation_confidence_ready")):
            actions.append(
                "Confidence metrics appear calibration-ready; proceed to snapshot #2 and final graduation audit."
            )
        else:
            actions.append("Continue monitoring confidence calibration until graduation_confidence_ready is true.")
    deduped: list[str] = []
    seen: set[str] = set()
    for action in actions:
        normalized = str(action).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped[:8]


def summarize_recurrence_confidence_calibration(
    audit: Mapping[str, Any] | None,
    *,
    confidence_calibration_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence confidence calibration audit."""
    source = audit if isinstance(audit, Mapping) else {}
    summary = confidence_calibration_summary if isinstance(confidence_calibration_summary, Mapping) else {}
    if not summary:
        summary = calculate_confidence_calibration_score(
            forecast_confidence_audit=source.get("forecast_confidence_audit")
            if isinstance(source.get("forecast_confidence_audit"), Mapping)
            else None,
            governance_confidence_audit=source.get("governance_confidence_audit")
            if isinstance(source.get("governance_confidence_audit"), Mapping)
            else None,
            effectiveness_confidence_audit=source.get("effectiveness_confidence_audit")
            if isinstance(source.get("effectiveness_confidence_audit"), Mapping)
            else None,
        )
    return dict(summary)


def render_recurrence_confidence_calibration_report_markdown(
    audit: Mapping[str, Any] | None,
    *,
    generated_at: str | None = None,
) -> str:
    """Render the standalone BQ-C3 confidence calibration audit report."""
    payload = audit if isinstance(audit, Mapping) else {}
    summary = payload.get("recurrence_confidence_calibration_summary")
    if not isinstance(summary, Mapping):
        summary = summarize_recurrence_confidence_calibration(payload)
    forecast = payload.get("forecast_confidence_audit")
    if not isinstance(forecast, Mapping):
        forecast = {}
    governance = payload.get("governance_confidence_audit")
    if not isinstance(governance, Mapping):
        governance = {}
    effectiveness = payload.get("effectiveness_confidence_audit")
    if not isinstance(effectiveness, Mapping):
        effectiveness = {}
    generated_at_s = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines = [
        "# BQ-C3 Confidence Calibration Audit",
        "",
        f"**Date:** {generated_at_s}",
        "**Protected replay only:** true",
        "",
        "## Summary",
        "",
        f"- Calibration score: `{float(summary.get('confidence_calibration_score') or 0.0):.1f}`",
        f"- Interpretation: `{summary.get('interpretation_label') or 'unknown'}`",
        f"- Largest calibration gap: `{float(summary.get('largest_calibration_gap') or 0.0):.2f}`",
        f"- Graduation confidence ready: `{str(bool(summary.get('graduation_confidence_ready'))).lower()}`",
        "",
        "# Forecast Confidence",
        "",
        f"- Reported confidence: `{float(forecast.get('reported_confidence') or 0.0):.2f}`",
        f"- Evidence strength: `{float(forecast.get('evidence_strength') or 0.0):.2f}`",
        f"- Calibration gap: `{float(forecast.get('calibration_gap') or 0.0):.2f}`",
        f"- Status: `{forecast.get('confidence_status')}`",
        f"- Forecast accuracy: `{float(forecast.get('forecast_accuracy') or 0.0):.2f}`",
        f"- Observations: `{int(forecast.get('total_observations') or 0)}`",
        f"- Keys: `{int(forecast.get('total_keys') or 0)}`",
        f"- Trajectory available: `{str(bool(forecast.get('trajectory_available'))).lower()}`",
        "",
        "# Governance Confidence",
        "",
        f"- Reported confidence: `{float(governance.get('reported_confidence') or 0.0):.2f}`",
        f"- Evidence strength: `{float(governance.get('evidence_strength') or 0.0):.2f}`",
        f"- Calibration gap: `{float(governance.get('calibration_gap') or 0.0):.2f}`",
        f"- Status: `{governance.get('confidence_status')}`",
        f"- Watchlist size: `{int(governance.get('watchlist_size') or 0)}`",
        f"- Governance health: `{float(governance.get('governance_health_score') or 0.0):.1f}`",
        "",
        "# Effectiveness Confidence",
        "",
        f"- Reported confidence: `{float(effectiveness.get('reported_confidence') or 0.0):.2f}`",
        f"- Evidence strength: `{float(effectiveness.get('evidence_strength') or 0.0):.2f}`",
        f"- Calibration gap: `{float(effectiveness.get('calibration_gap') or 0.0):.2f}`",
        f"- Status: `{effectiveness.get('confidence_status')}`",
        f"- Trajectory available: `{str(bool(effectiveness.get('trajectory_available'))).lower()}`",
        f"- Remediation effectiveness: `{float(effectiveness.get('remediation_effectiveness') or 0.0):.2f}`",
        f"- Closure rate: `{float(effectiveness.get('closure_rate') or 0.0):.2f}`",
        "",
        "# Graduation Threshold Validation",
        "",
    ]
    for row in payload.get("graduation_threshold_validation") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- `{row.get('threshold')}`: current `{row.get('current_value')}`, target `{row.get('target_value')}`, "
            f"status `{row.get('validation_status')}` — {row.get('rationale')}"
        )
    lines.extend(["", "# Blind Spot Reassessment", ""])
    for row in payload.get("blind_spot_reassessment") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- **{row.get('blind_spot_id')}** (BQ16 `{row.get('bq16_severity')}`, now `{row.get('current_severity')}`): "
            f"`{row.get('status_change')}` — {row.get('rationale')}"
        )
    lines.extend(["", "# Recommended Actions", ""])
    actions = payload.get("recommended_actions") or []
    if actions:
        for index, action in enumerate(actions, start=1):
            lines.append(f"{index}. {action}")
    else:
        lines.append("1. Continue monitoring confidence calibration.")
    lines.append("")
    return "\n".join(lines)


def enrich_recurrence_history_with_confidence_audit(
    history: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a history payload with additive protected replay confidence audit fields."""
    payload = dict(history)
    audit = build_recurrence_confidence_audit(
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        recurrence_governance=payload.get("recurrence_governance")
        if isinstance(payload.get("recurrence_governance"), Mapping)
        else None,
        recurrence_program_effectiveness=payload.get("recurrence_program_effectiveness")
        if isinstance(payload.get("recurrence_program_effectiveness"), Mapping)
        else None,
        recurrence_maturity=payload.get("recurrence_maturity")
        if isinstance(payload.get("recurrence_maturity"), Mapping)
        else None,
        recurrence_completion=payload.get("recurrence_completion")
        if isinstance(payload.get("recurrence_completion"), Mapping)
        else None,
        recurrence_trajectory_summary=payload.get("recurrence_trajectory_summary")
        if isinstance(payload.get("recurrence_trajectory_summary"), Mapping)
        else None,
        recurrence_history=payload,
        recurrence_lifecycle=payload.get("recurrence_lifecycle")
        if isinstance(payload.get("recurrence_lifecycle"), Mapping)
        else None,
        recurrence_portfolio_summary=payload.get("recurrence_portfolio_summary")
        if isinstance(payload.get("recurrence_portfolio_summary"), Mapping)
        else None,
    )
    payload["recurrence_confidence_audit"] = audit
    payload["recurrence_confidence_calibration_summary"] = audit["recurrence_confidence_calibration_summary"]
    return payload


RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH = Path("docs/audits/BQC4_final_graduation_decision.md")
RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_GRADUATE = "graduate_recurrence_program"
RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_VALIDATION_CYCLE = "one_final_targeted_validation_cycle_required"
RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_IMMATURE = "recurrence_program_remains_operationally_immature"
BQC3_CALIBRATION_BASELINE: dict[str, Any] = {
    "confidence_calibration_score": 57.3,
    "largest_calibration_gap": 0.61,
    "graduation_confidence_ready": False,
    "trajectory_available": False,
    "snapshot_count": 1,
}
RECURRENCE_FINAL_GRADUATION_DECISION_DEFINITION = (
    "Advisory final graduation decision compares post-activation calibration, readiness, and blind-spot "
    "posture against BQ-C3 baseline. Formal graduation requires calibration score >= 70, largest gap <= 0.20, "
    "trajectory_available=true, and no critical blind spots."
)


def _collect_remaining_graduation_blockers(
    *,
    recurrence_confidence_audit: Mapping[str, Any] | None,
    recurrence_graduation_audit: Mapping[str, Any] | None,
    recurrence_completion: Mapping[str, Any] | None,
    recurrence_trajectory_summary: Mapping[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    confidence = recurrence_confidence_audit if isinstance(recurrence_confidence_audit, Mapping) else {}
    calibration = confidence.get("recurrence_confidence_calibration_summary")
    if not isinstance(calibration, Mapping):
        calibration = {}
    graduation = recurrence_graduation_audit if isinstance(recurrence_graduation_audit, Mapping) else {}
    completion = recurrence_completion if isinstance(recurrence_completion, Mapping) else {}
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    completion_summary = completion.get("recurrence_completion_summary")
    if not isinstance(completion_summary, Mapping):
        completion_summary = {}

    if not bool(trajectory.get("trajectory_available")):
        blockers.append("trajectory_available remains false")
    if float(calibration.get("confidence_calibration_score") or 0.0) < 70.0:
        blockers.append(
            f"calibration score below target ({float(calibration.get('confidence_calibration_score') or 0.0):.1f} < 70)"
        )
    if float(calibration.get("largest_calibration_gap") or 0.0) > 0.20:
        blockers.append(
            f"largest calibration gap above target ({float(calibration.get('largest_calibration_gap') or 0.0):.2f} > 0.20)"
        )
    if not bool(calibration.get("graduation_confidence_ready")):
        blockers.append("graduation_confidence_ready is false")
    if int(graduation.get("recurrence_graduation_audit_summary", {}).get("critical_blind_spots") or 0) > 0:
        blockers.append("critical blind spots remain in graduation audit")
    for row in confidence.get("blind_spot_reassessment") or ():
        if not isinstance(row, Mapping):
            continue
        if row.get("status_change") in {"unchanged", "escalated"} and row.get("current_severity") == "critical":
            blockers.append(f"critical blind spot unresolved: {row.get('blind_spot_id')}")
    if not bool(completion_summary.get("program_graduated")):
        if completion_summary.get("remaining_dimensions"):
            remaining = completion_summary.get("remaining_dimensions")
            if isinstance(remaining, list) and remaining:
                blockers.append(
                    f"completion dimensions incomplete: {', '.join(str(item) for item in remaining)}"
                )
    readiness = graduation.get("graduation_readiness")
    if isinstance(readiness, Mapping):
        if float(readiness.get("graduation_readiness_score") or 0.0) < 90.0:
            blockers.append(
                f"graduation readiness below formal threshold ({float(readiness.get('graduation_readiness_score') or 0.0):.1f} < 90)"
            )
    for row in confidence.get("graduation_threshold_validation") or ():
        if not isinstance(row, Mapping):
            continue
        if row.get("validation_status") == RECURRENCE_GRADUATION_THRESHOLD_UNSUPPORTED:
            blockers.append(f"unsupported graduation threshold: {row.get('threshold')}")
    deduped: list[str] = []
    seen: set[str] = set()
    for blocker in blockers:
        if blocker not in seen:
            seen.add(blocker)
            deduped.append(blocker)
    return deduped


def _determine_final_graduation_recommendation(
    *,
    calibration_summary: Mapping[str, Any],
    trajectory_summary: Mapping[str, Any],
    graduation_audit_summary: Mapping[str, Any],
    remaining_blockers: Sequence[str],
) -> tuple[str, str]:
    calibration_score = float(calibration_summary.get("confidence_calibration_score") or 0.0)
    largest_gap = float(calibration_summary.get("largest_calibration_gap") or 0.0)
    trajectory_available = bool(trajectory_summary.get("trajectory_available"))
    critical_blind_spots = int(graduation_audit_summary.get("critical_blind_spots") or 0)
    readiness_score = float(graduation_audit_summary.get("graduation_readiness_score") or 0.0)

    formal_ready = (
        calibration_score >= 70.0
        and largest_gap <= 0.20
        and trajectory_available
        and critical_blind_spots == 0
        and bool(calibration_summary.get("graduation_confidence_ready"))
    )
    if formal_ready and readiness_score >= 90.0 and not remaining_blockers:
        return (
            RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_GRADUATE,
            "Formal graduation criteria met: calibration, trajectory, readiness, and blind-spot posture support program closure.",
        )

    if trajectory_available and readiness_score >= 70.0:
        return (
            RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_VALIDATION_CYCLE,
            "Trajectory is active and readiness improved, but confidence or outcome evidence still requires one narrowly scoped validation cycle.",
        )

    return (
        RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_IMMATURE,
        "Recurrence program remains operationally immature relative to graduation confidence and outcome evidence requirements.",
    )


def build_recurrence_final_graduation_decision(
    *,
    recurrence_trajectory_summary: Mapping[str, Any] | None = None,
    recurrence_trajectory_history: Mapping[str, Any] | None = None,
    recurrence_confidence_audit: Mapping[str, Any] | None = None,
    recurrence_graduation_audit: Mapping[str, Any] | None = None,
    recurrence_completion: Mapping[str, Any] | None = None,
    recurrence_maturity: Mapping[str, Any] | None = None,
    bqc3_calibration_baseline: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build protected replay final graduation decision audit (BQ-C4)."""
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    trajectory_history = (
        recurrence_trajectory_history if isinstance(recurrence_trajectory_history, Mapping) else {}
    )
    confidence = recurrence_confidence_audit if isinstance(recurrence_confidence_audit, Mapping) else {}
    graduation = recurrence_graduation_audit if isinstance(recurrence_graduation_audit, Mapping) else {}
    completion = recurrence_completion if isinstance(recurrence_completion, Mapping) else {}
    maturity = recurrence_maturity if isinstance(recurrence_maturity, Mapping) else {}
    baseline = bqc3_calibration_baseline if isinstance(bqc3_calibration_baseline, Mapping) else BQC3_CALIBRATION_BASELINE

    calibration_summary = confidence.get("recurrence_confidence_calibration_summary")
    if not isinstance(calibration_summary, Mapping):
        calibration_summary = summarize_recurrence_confidence_calibration(confidence)
    graduation_summary = graduation.get("recurrence_graduation_audit_summary")
    if not isinstance(graduation_summary, Mapping):
        graduation_summary = summarize_recurrence_graduation_audit(graduation)
    completion_summary = completion.get("recurrence_completion_summary")
    if not isinstance(completion_summary, Mapping):
        completion_summary = {}
    maturity_summary = maturity.get("recurrence_maturity_summary")
    if not isinstance(maturity_summary, Mapping):
        maturity_summary = {}

    calibration_score = float(calibration_summary.get("confidence_calibration_score") or 0.0)
    largest_gap = float(calibration_summary.get("largest_calibration_gap") or 0.0)
    baseline_score = float(baseline.get("confidence_calibration_score") or 0.0)
    baseline_gap = float(baseline.get("largest_calibration_gap") or 0.0)
    remaining_blockers = _collect_remaining_graduation_blockers(
        recurrence_confidence_audit=confidence,
        recurrence_graduation_audit=graduation,
        recurrence_completion=completion,
        recurrence_trajectory_summary=trajectory,
    )
    recommendation, recommendation_rationale = _determine_final_graduation_recommendation(
        calibration_summary=calibration_summary,
        trajectory_summary=trajectory,
        graduation_audit_summary=graduation_summary,
        remaining_blockers=remaining_blockers,
    )

    snapshots = [row for row in (trajectory_history.get("snapshots") or ()) if isinstance(row, Mapping)]
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "decision_definition": RECURRENCE_FINAL_GRADUATION_DECISION_DEFINITION,
        "trajectory_activation": {
            "snapshot_count": int(trajectory.get("snapshot_count") or len(snapshots)),
            "trajectory_available": bool(trajectory.get("trajectory_available")),
            "baseline_only": bool(trajectory.get("baseline_only")),
            "portfolio_risk_change": float(trajectory.get("portfolio_risk_change") or 0.0),
            "governance_health_change": float(trajectory.get("governance_health_change") or 0.0),
            "lifecycle_health_change": float(trajectory.get("lifecycle_health_change") or 0.0),
            "operational_readiness_change": float(trajectory.get("operational_readiness_change") or 0.0),
            "effectiveness_change": float(trajectory.get("effectiveness_change") or 0.0),
            "maturity_change": float(trajectory.get("maturity_change") or 0.0),
            "stability_change": float((trajectory.get("stability_trajectory") or {}).get("absolute_change") or 0.0),
            "message": trajectory.get("message"),
        },
        "confidence_recalculation": {
            "forecast_confidence_audit": confidence.get("forecast_confidence_audit"),
            "governance_confidence_audit": confidence.get("governance_confidence_audit"),
            "effectiveness_confidence_audit": confidence.get("effectiveness_confidence_audit"),
            "recurrence_confidence_calibration_summary": dict(calibration_summary),
        },
        "calibration_comparison": {
            "bqc3_baseline": dict(baseline),
            "bqc4_current": {
                "confidence_calibration_score": calibration_score,
                "largest_calibration_gap": largest_gap,
                "graduation_confidence_ready": bool(calibration_summary.get("graduation_confidence_ready")),
                "trajectory_available": bool(trajectory.get("trajectory_available")),
                "snapshot_count": int(trajectory.get("snapshot_count") or len(snapshots)),
            },
            "calibration_score_delta": round(calibration_score - baseline_score, 1),
            "largest_gap_delta": round(largest_gap - baseline_gap, 2),
            "trajectory_activated": bool(trajectory.get("trajectory_available"))
            and not bool(baseline.get("trajectory_available")),
        },
        "graduation_readiness": {
            "graduation_readiness_score": float(graduation_summary.get("graduation_readiness_score") or 0.0),
            "readiness_level": graduation_summary.get("readiness_level"),
            "readiness_label": graduation_summary.get("readiness_label"),
            "overall_completion_score": float(completion_summary.get("overall_completion_score") or 0.0),
            "overall_maturity_score": float(maturity_summary.get("overall_maturity_score") or 0.0),
            "operational_readiness_score": float(maturity_summary.get("operational_readiness_score") or 0.0),
            "program_graduated": bool(completion_summary.get("program_graduated")),
            "critical_blind_spots": int(graduation_summary.get("critical_blind_spots") or 0),
        },
        "remaining_blockers": remaining_blockers,
        "final_recommendation": recommendation,
        "final_recommendation_rationale": recommendation_rationale,
        "formal_graduation_criteria_met": recommendation == RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_GRADUATE,
    }


def render_recurrence_final_graduation_decision_report_markdown(
    decision: Mapping[str, Any] | None,
    *,
    generated_at: str | None = None,
) -> str:
    """Render the standalone BQ-C4 final graduation decision report."""
    payload = decision if isinstance(decision, Mapping) else {}
    activation = payload.get("trajectory_activation")
    if not isinstance(activation, Mapping):
        activation = {}
    comparison = payload.get("calibration_comparison")
    if not isinstance(comparison, Mapping):
        comparison = {}
    bqc3 = comparison.get("bqc3_baseline")
    if not isinstance(bqc3, Mapping):
        bqc3 = {}
    bqc4 = comparison.get("bqc4_current")
    if not isinstance(bqc4, Mapping):
        bqc4 = {}
    readiness = payload.get("graduation_readiness")
    if not isinstance(readiness, Mapping):
        readiness = {}
    confidence = payload.get("confidence_recalculation")
    if not isinstance(confidence, Mapping):
        confidence = {}
    calibration = confidence.get("recurrence_confidence_calibration_summary")
    if not isinstance(calibration, Mapping):
        calibration = {}
    generated_at_s = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    recommendation = payload.get("final_recommendation")
    if recommendation == RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_GRADUATE:
        recommendation_label = "A. Graduate recurrence program"
    elif recommendation == RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_VALIDATION_CYCLE:
        recommendation_label = "B. One final targeted validation cycle required"
    else:
        recommendation_label = "C. Recurrence program remains operationally immature"

    lines = [
        "# BQ-C4 Final Graduation Decision",
        "",
        f"**Date:** {generated_at_s}",
        "**Protected replay only:** true",
        "",
        "# Trajectory Activation",
        "",
        f"- Snapshot count: `{int(activation.get('snapshot_count') or 0)}`",
        f"- Trajectory available: `{str(bool(activation.get('trajectory_available'))).lower()}`",
        f"- Portfolio risk change: `{float(activation.get('portfolio_risk_change') or 0.0):.4f}`",
        f"- Governance health change: `{float(activation.get('governance_health_change') or 0.0):.4f}`",
        f"- Lifecycle health change: `{float(activation.get('lifecycle_health_change') or 0.0):.4f}`",
        f"- Operational readiness change: `{float(activation.get('operational_readiness_change') or 0.0):.4f}`",
        f"- Effectiveness change: `{float(activation.get('effectiveness_change') or 0.0):.4f}`",
        f"- Maturity change: `{float(activation.get('maturity_change') or 0.0):.4f}`",
        f"- Stability change: `{float(activation.get('stability_change') or 0.0):.4f}`",
        f"- Message: {activation.get('message') or 'none recorded'}",
        "",
        "# Confidence Recalculation",
        "",
        f"- Calibration score: `{float(calibration.get('confidence_calibration_score') or 0.0):.1f}`",
        f"- Largest calibration gap: `{float(calibration.get('largest_calibration_gap') or 0.0):.2f}`",
        f"- Graduation confidence ready: `{str(bool(calibration.get('graduation_confidence_ready'))).lower()}`",
        f"- Forecast status: `{calibration.get('forecast_status')}`",
        f"- Governance status: `{calibration.get('governance_status')}`",
        f"- Effectiveness status: `{calibration.get('effectiveness_status')}`",
        "",
        "# Calibration Comparison",
        "",
        f"- BQ-C3 calibration score: `{float(bqc3.get('confidence_calibration_score') or 0.0):.1f}`",
        f"- BQ-C4 calibration score: `{float(bqc4.get('confidence_calibration_score') or 0.0):.1f}`",
        f"- Score delta: `{float(comparison.get('calibration_score_delta') or 0.0):+.1f}`",
        f"- BQ-C3 largest gap: `{float(bqc3.get('largest_calibration_gap') or 0.0):.2f}`",
        f"- BQ-C4 largest gap: `{float(bqc4.get('largest_calibration_gap') or 0.0):.2f}`",
        f"- Gap delta: `{float(comparison.get('largest_gap_delta') or 0.0):+.2f}`",
        f"- Trajectory activated: `{str(bool(comparison.get('trajectory_activated'))).lower()}`",
        "",
        "# Graduation Readiness",
        "",
        f"- Graduation readiness score: `{float(readiness.get('graduation_readiness_score') or 0.0):.1f}`",
        f"- Readiness level: `{readiness.get('readiness_label') or readiness.get('readiness_level')}`",
        f"- Overall completion score: `{float(readiness.get('overall_completion_score') or 0.0):.1f}`",
        f"- Overall maturity score: `{float(readiness.get('overall_maturity_score') or 0.0):.1f}`",
        f"- Operational readiness score: `{float(readiness.get('operational_readiness_score') or 0.0):.1f}`",
        f"- Program graduated: `{str(bool(readiness.get('program_graduated'))).lower()}`",
        f"- Critical blind spots: `{int(readiness.get('critical_blind_spots') or 0)}`",
        "",
        "# Remaining Blockers",
        "",
    ]
    blockers = payload.get("remaining_blockers") or []
    if blockers:
        for blocker in blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- No remaining blockers recorded.")
    lines.extend(
        [
            "",
            "# Final Recommendation",
            "",
            f"**{recommendation_label}**",
            "",
            str(payload.get("final_recommendation_rationale") or "No rationale recorded."),
            "",
        ]
    )
    return "\n".join(lines)


RECURRENCE_OUTCOME_VALIDATION_DOC_PATH = Path("docs/audits/BQC5_effectiveness_validation.md")
RECURRENCE_OUTCOME_SIGNAL_RETIRED = "retired_recurrence_key"
RECURRENCE_OUTCOME_SIGNAL_DORMANT = "dormant_recurrence_key"
RECURRENCE_OUTCOME_SIGNAL_REDUCTION = "measurable_recurrence_reduction"
RECURRENCE_OUTCOME_SIGNAL_REMEDIATION = "confirmed_remediation_impact"
RECURRENCE_OUTCOME_SIGNALS: frozenset[str] = frozenset(
    {
        RECURRENCE_OUTCOME_SIGNAL_RETIRED,
        RECURRENCE_OUTCOME_SIGNAL_DORMANT,
        RECURRENCE_OUTCOME_SIGNAL_REDUCTION,
        RECURRENCE_OUTCOME_SIGNAL_REMEDIATION,
    }
)
RECURRENCE_OUTCOME_REJECTION_SYNTHETIC = "synthetic_key_rejected"
RECURRENCE_OUTCOME_REJECTION_INFERRED = "inferred_without_evidence"
RECURRENCE_OUTCOME_REJECTION_FORCED = "manually_forced_status_rejected"
RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT = "insufficient_evidence"
RECURRENCE_OUTCOME_VALIDATION_DEFINITION = (
    "Advisory protected replay outcome validation accepts only evidenced lifecycle closures "
    "(retired/dormant keys with event-log or inactivity backing), measurable trajectory "
    "recurrence reduction, or confirmed remediation impact on targeted keys. Synthetic keys, "
    "manually forced statuses, and inferred success without evidence are rejected."
)
RECURRENCE_OUTCOME_EVIDENCE_STRENGTH_DEFINITION = (
    "Outcome-grounded 0-1 effectiveness evidence: 20% trajectory factor + 40% validated outcome "
    "coverage (validated_outcomes / total_keys) + 40% max(validated_closure_rate, "
    "validated_recurrence_reduction_rate, validated_remediation_impact_rate)."
)
BQC4_EFFECTIVENESS_BASELINE: dict[str, Any] = {
    "reported_confidence": 0.82,
    "evidence_strength": 0.18,
    "calibration_gap": 0.64,
    "confidence_calibration_score": 61.3,
    "largest_calibration_gap": 0.64,
    "graduation_confidence_ready": False,
}
BQC5_GRADUATION_RECOMMENDATION_GRADUATE = "graduate_recurrence_program"
BQC5_GRADUATION_RECOMMENDATION_VALIDATION_PERIOD = "one_additional_validation_period_required"
BQC5_GRADUATION_RECOMMENDATION_IMMATURE = "recurrence_program_remains_operationally_immature"


def _days_since_timestamp(value: Any, *, as_of: Any | None = None) -> float:
    last_dt = _parse_iso_timestamp(value)
    as_of_dt = _parse_iso_timestamp(as_of) or datetime.now(UTC)
    if last_dt is None:
        return 0.0
    return max((as_of_dt - last_dt).total_seconds() / 86400.0, 0.0)


def _event_log_rows_for_key(
    event_log: Mapping[str, Any] | None,
    recurrence_key: str,
) -> list[dict[str, Any]]:
    log = event_log if isinstance(event_log, Mapping) else {}
    rows: list[dict[str, Any]] = []
    for event in log.get("events") or ():
        if not isinstance(event, Mapping):
            continue
        if str(event.get("recurrence_key") or "").strip() == str(recurrence_key or "").strip():
            rows.append(dict(event))
    return rows


def _validate_retired_outcome_signal(
    key_row: Mapping[str, Any],
    *,
    event_log: Mapping[str, Any] | None = None,
    as_of: Any | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    key = str(key_row.get("recurrence_key") or "").strip()
    if not key:
        return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT
    if is_synthetic_drift_recurrence_key(key):
        return None, RECURRENCE_OUTCOME_REJECTION_SYNTHETIC
    if str(key_row.get("lifecycle_stage") or "") != RECURRENCE_LIFECYCLE_RETIRED:
        return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT
    events = _event_log_rows_for_key(event_log, key)
    explicit_retired = any(
        str(event.get("recurrence_status") or "").lower() in {"retired", "deprecated"} for event in events
    )
    inactivity_days = _days_since_timestamp(key_row.get("last_seen"), as_of=as_of)
    if explicit_retired:
        return {
            "signal_type": RECURRENCE_OUTCOME_SIGNAL_RETIRED,
            "recurrence_key": key,
            "evidence_source": "event_log_recurrence_status",
            "inactivity_days": round(inactivity_days, 4),
        }, None
    if inactivity_days >= RECURRENCE_LIFECYCLE_RETIREMENT_INACTIVITY_DAYS:
        return {
            "signal_type": RECURRENCE_OUTCOME_SIGNAL_RETIRED,
            "recurrence_key": key,
            "evidence_source": "natural_inactivity_retirement_threshold",
            "inactivity_days": round(inactivity_days, 4),
        }, None
    return None, RECURRENCE_OUTCOME_REJECTION_INFERRED


def _validate_dormant_outcome_signal(
    key_row: Mapping[str, Any],
    *,
    event_log: Mapping[str, Any] | None = None,
    as_of: Any | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    key = str(key_row.get("recurrence_key") or "").strip()
    if not key:
        return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT
    if is_synthetic_drift_recurrence_key(key):
        return None, RECURRENCE_OUTCOME_REJECTION_SYNTHETIC
    if str(key_row.get("lifecycle_stage") or "") != RECURRENCE_LIFECYCLE_DORMANT:
        return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT
    events = _event_log_rows_for_key(event_log, key)
    if any(str(event.get("recurrence_status") or "").lower() in {"retired", "deprecated"} for event in events):
        return None, RECURRENCE_OUTCOME_REJECTION_FORCED
    inactivity_days = _days_since_timestamp(key_row.get("last_seen"), as_of=as_of)
    if inactivity_days < RECURRENCE_TREND_DORMANT_INACTIVITY_DAYS:
        return None, RECURRENCE_OUTCOME_REJECTION_INFERRED
    return {
        "signal_type": RECURRENCE_OUTCOME_SIGNAL_DORMANT,
        "recurrence_key": key,
        "evidence_source": "protected_replay_inactivity_threshold",
        "inactivity_days": round(inactivity_days, 4),
    }, None


def _validate_measurable_recurrence_reduction(
    *,
    recurrence_trajectory_summary: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    if not bool(trajectory.get("trajectory_available")):
        return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT
    regression_trajectory = trajectory.get("regression_rate_trajectory")
    if not isinstance(regression_trajectory, Mapping):
        regression_trajectory = {}
    regression_change = float(regression_trajectory.get("absolute_change") or 0.0)
    if regression_change < -0.0001:
        return {
            "signal_type": RECURRENCE_OUTCOME_SIGNAL_REDUCTION,
            "evidence_source": "trajectory_regression_rate_decrease",
            "absolute_change": round(regression_change, 4),
        }, None
    portfolio_change = float(trajectory.get("portfolio_risk_change") or 0.0)
    if portfolio_change < -0.0001:
        return {
            "signal_type": RECURRENCE_OUTCOME_SIGNAL_REDUCTION,
            "evidence_source": "trajectory_portfolio_risk_decrease",
            "absolute_change": round(portfolio_change, 4),
        }, None
    remediation = effectiveness.get("remediation_effectiveness_summary")
    if isinstance(remediation, Mapping):
        reduction_rate = float(remediation.get("recurrence_reduction_rate") or 0.0)
        improved_keys = int(remediation.get("improved_keys") or 0)
        if reduction_rate > 0.0 and improved_keys > 0:
            return {
                "signal_type": RECURRENCE_OUTCOME_SIGNAL_REDUCTION,
                "evidence_source": "remediation_improved_keys",
                "recurrence_reduction_rate": round(reduction_rate, 4),
                "improved_keys": improved_keys,
            }, None
    return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT


def _validate_remediation_impact_signal(
    key_row: Mapping[str, Any],
    *,
    remediation_by_key: Mapping[str, Mapping[str, Any]],
    validated_closure_keys: set[str],
) -> tuple[dict[str, Any] | None, str | None]:
    key = str(key_row.get("recurrence_key") or "").strip()
    if not key or key not in validated_closure_keys:
        return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT
    remediation = remediation_by_key.get(key)
    if not isinstance(remediation, Mapping):
        return None, RECURRENCE_OUTCOME_REJECTION_INSUFFICIENT
    reduction_potential = float(remediation.get("reduction_potential") or 0.0)
    if reduction_potential <= 0.0:
        return None, RECURRENCE_OUTCOME_REJECTION_INFERRED
    return {
        "signal_type": RECURRENCE_OUTCOME_SIGNAL_REMEDIATION,
        "recurrence_key": key,
        "evidence_source": "targeted_key_with_validated_closure",
        "reduction_potential": round(reduction_potential, 4),
    }, None


def summarize_recurrence_outcomes(
    *,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_remediation_targets: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
    recurrence_trajectory_summary: Mapping[str, Any] | None = None,
    event_log: Mapping[str, Any] | None = None,
    as_of: Any | None = None,
) -> dict[str, Any]:
    """Summarize validated protected replay recurrence outcome evidence."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    lifecycle = recurrence_lifecycle if isinstance(recurrence_lifecycle, Mapping) else {}
    if not lifecycle and isinstance(history.get("recurrence_lifecycle"), Mapping):
        lifecycle = history["recurrence_lifecycle"]
    targets = recurrence_remediation_targets if isinstance(recurrence_remediation_targets, Mapping) else {}
    if not targets and isinstance(history.get("recurrence_remediation_targets"), Mapping):
        targets = history["recurrence_remediation_targets"]
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    if not trajectory and isinstance(history.get("recurrence_trajectory_summary"), Mapping):
        trajectory = history["recurrence_trajectory_summary"]

    lifecycle_keys = [dict(row) for row in (lifecycle.get("keys") or ()) if isinstance(row, Mapping)]
    total_keys = int(lifecycle.get("total_keys") or history.get("unique_recurrence_count") or len(lifecycle_keys))
    remediation_by_key = {
        str(row.get("recurrence_key") or ""): dict(row)
        for row in (targets.get("keys") or ())
        if isinstance(row, Mapping) and str(row.get("recurrence_key") or "").strip()
    }

    validated_outcomes: list[dict[str, Any]] = []
    rejected_signals: list[dict[str, Any]] = []
    validated_closure_keys: set[str] = set()
    retired_keys = 0
    dormant_keys = 0

    for key_row in lifecycle_keys:
        retired_signal, retired_reason = _validate_retired_outcome_signal(
            key_row,
            event_log=event_log,
            as_of=as_of,
        )
        if retired_signal:
            validated_outcomes.append(retired_signal)
            validated_closure_keys.add(str(retired_signal.get("recurrence_key") or ""))
            retired_keys += 1
            continue
        if retired_reason and str(key_row.get("lifecycle_stage") or "") == RECURRENCE_LIFECYCLE_RETIRED:
            rejected_signals.append(
                {
                    "recurrence_key": key_row.get("recurrence_key"),
                    "candidate_signal": RECURRENCE_OUTCOME_SIGNAL_RETIRED,
                    "rejection_reason": retired_reason,
                }
            )

        dormant_signal, dormant_reason = _validate_dormant_outcome_signal(
            key_row,
            event_log=event_log,
            as_of=as_of,
        )
        if dormant_signal:
            validated_outcomes.append(dormant_signal)
            validated_closure_keys.add(str(dormant_signal.get("recurrence_key") or ""))
            dormant_keys += 1
            continue
        if dormant_reason and str(key_row.get("lifecycle_stage") or "") == RECURRENCE_LIFECYCLE_DORMANT:
            rejected_signals.append(
                {
                    "recurrence_key": key_row.get("recurrence_key"),
                    "candidate_signal": RECURRENCE_OUTCOME_SIGNAL_DORMANT,
                    "rejection_reason": dormant_reason,
                }
            )

    reduction_signal, reduction_reason = _validate_measurable_recurrence_reduction(
        recurrence_trajectory_summary=trajectory,
        recurrence_program_effectiveness=effectiveness,
    )
    if reduction_signal:
        validated_outcomes.append(reduction_signal)
    elif reduction_reason:
        rejected_signals.append(
            {
                "candidate_signal": RECURRENCE_OUTCOME_SIGNAL_REDUCTION,
                "rejection_reason": reduction_reason,
            }
        )

    for key_row in lifecycle_keys:
        remediation_signal, remediation_reason = _validate_remediation_impact_signal(
            key_row,
            remediation_by_key=remediation_by_key,
            validated_closure_keys=validated_closure_keys,
        )
        if remediation_signal:
            validated_outcomes.append(remediation_signal)
        elif (
            remediation_reason
            and str(key_row.get("recurrence_key") or "") in remediation_by_key
            and str(key_row.get("lifecycle_stage") or "")
            in {RECURRENCE_LIFECYCLE_DORMANT, RECURRENCE_LIFECYCLE_RETIRED}
        ):
            rejected_signals.append(
                {
                    "recurrence_key": key_row.get("recurrence_key"),
                    "candidate_signal": RECURRENCE_OUTCOME_SIGNAL_REMEDIATION,
                    "rejection_reason": remediation_reason,
                }
            )

    validated_outcome_count = len(validated_outcomes)
    denominator = max(total_keys, 1)
    validated_closure_rate = round((retired_keys + dormant_keys) / float(denominator), 4)
    validated_reduction_rate = 0.0
    validated_remediation_rate = 0.0
    for row in validated_outcomes:
        signal_type = str(row.get("signal_type") or "")
        if signal_type == RECURRENCE_OUTCOME_SIGNAL_REDUCTION:
            validated_reduction_rate = max(
                validated_reduction_rate,
                float(row.get("recurrence_reduction_rate") or abs(float(row.get("absolute_change") or 0.0))),
            )
        if signal_type == RECURRENCE_OUTCOME_SIGNAL_REMEDIATION:
            validated_remediation_rate = max(validated_remediation_rate, 1.0 / float(denominator))

    active_keys = sum(
        1
        for row in lifecycle_keys
        if str(row.get("lifecycle_stage") or "")
        not in {RECURRENCE_LIFECYCLE_DORMANT, RECURRENCE_LIFECYCLE_RETIRED}
    )
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "definition": RECURRENCE_OUTCOME_VALIDATION_DEFINITION,
        "total_keys": total_keys,
        "active_keys": active_keys,
        "retired_keys": retired_keys,
        "dormant_keys": dormant_keys,
        "validated_outcome_count": validated_outcome_count,
        "validated_outcomes": validated_outcomes,
        "rejected_signals": rejected_signals,
        "validated_closure_rate": validated_closure_rate,
        "validated_recurrence_reduction_rate": round(validated_reduction_rate, 4),
        "validated_remediation_impact_rate": round(validated_remediation_rate, 4),
        "has_validated_outcomes": validated_outcome_count > 0,
        "outcome_evidence_strength_definition": RECURRENCE_OUTCOME_EVIDENCE_STRENGTH_DEFINITION,
    }


def calculate_effectiveness_evidence_strength(
    *,
    outcome_validation_summary: Mapping[str, Any] | None,
    trajectory_available: bool,
) -> float:
    """Calculate outcome-grounded protected replay effectiveness evidence strength."""
    summary = outcome_validation_summary if isinstance(outcome_validation_summary, Mapping) else {}
    total_keys = max(int(summary.get("total_keys") or 0), 1)
    validated_count = int(summary.get("validated_outcome_count") or 0)
    outcome_coverage = min(1.0, validated_count / float(total_keys))
    validated_closure_rate = float(summary.get("validated_closure_rate") or 0.0)
    validated_reduction_rate = float(summary.get("validated_recurrence_reduction_rate") or 0.0)
    validated_remediation_rate = float(summary.get("validated_remediation_impact_rate") or 0.0)
    outcome_signal = max(validated_closure_rate, validated_reduction_rate, validated_remediation_rate)
    trajectory_factor = 1.0 if trajectory_available else 0.4
    if not bool(summary.get("has_validated_outcomes")):
        outcome_coverage = 0.0
        outcome_signal = 0.0
    return round(
        min(
            1.0,
            0.20 * trajectory_factor + 0.40 * outcome_coverage + 0.40 * outcome_signal,
        ),
        2,
    )


def _audit_effectiveness_confidence_with_outcomes(
    *,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    recurrence_trajectory_summary: Mapping[str, Any] | None,
    outcome_validation_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    trajectory = recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {}
    program_summary = effectiveness.get("program_effectiveness_summary")
    if not isinstance(program_summary, Mapping):
        program_summary = {}
    trajectory_available = bool(
        trajectory.get("trajectory_available")
        or (effectiveness.get("portfolio_trajectory_summary") or {}).get("trajectory_available")
    )
    reported_confidence = float(program_summary.get("effectiveness_confidence") or 0.0)
    evidence_strength = calculate_effectiveness_evidence_strength(
        outcome_validation_summary=outcome_validation_summary,
        trajectory_available=trajectory_available,
    )
    calibration_gap = round(reported_confidence - evidence_strength, 2)
    outcome_summary = outcome_validation_summary if isinstance(outcome_validation_summary, Mapping) else {}
    confidence_status = _confidence_calibration_status(reported_confidence, evidence_strength)
    return {
        "reported_confidence": reported_confidence,
        "evidence_strength": evidence_strength,
        "calibration_gap": calibration_gap,
        "confidence_status": confidence_status,
        "trajectory_available": trajectory_available,
        "validated_outcome_count": int(outcome_summary.get("validated_outcome_count") or 0),
        "validated_closure_rate": float(outcome_summary.get("validated_closure_rate") or 0.0),
        "validated_recurrence_reduction_rate": float(
            outcome_summary.get("validated_recurrence_reduction_rate") or 0.0
        ),
        "validated_remediation_impact_rate": float(
            outcome_summary.get("validated_remediation_impact_rate") or 0.0
        ),
        "outcome_supported": bool(outcome_summary.get("has_validated_outcomes"))
        and confidence_status != RECURRENCE_CONFIDENCE_STATUS_OVERCONFIDENT
        and evidence_strength >= RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET * 0.5,
        "evidence_definition": RECURRENCE_OUTCOME_EVIDENCE_STRENGTH_DEFINITION,
    }


def _determine_bqc5_graduation_recommendation(
    *,
    calibration_summary: Mapping[str, Any],
    trajectory_summary: Mapping[str, Any],
    effectiveness_audit: Mapping[str, Any],
    graduation_audit_summary: Mapping[str, Any],
    outcome_validation_summary: Mapping[str, Any],
) -> tuple[str, str]:
    calibration_score = float(calibration_summary.get("confidence_calibration_score") or 0.0)
    largest_gap = float(calibration_summary.get("largest_calibration_gap") or 0.0)
    trajectory_available = bool(trajectory_summary.get("trajectory_available"))
    critical_blind_spots = int(graduation_audit_summary.get("critical_blind_spots") or 0)
    outcome_supported = bool(effectiveness_audit.get("outcome_supported"))
    has_outcomes = bool(outcome_validation_summary.get("has_validated_outcomes"))

    formal_ready = (
        calibration_score >= 70.0
        and largest_gap <= 0.20
        and trajectory_available
        and outcome_supported
        and has_outcomes
        and critical_blind_spots == 0
        and bool(calibration_summary.get("graduation_confidence_ready"))
    )
    if formal_ready:
        return (
            BQC5_GRADUATION_RECOMMENDATION_GRADUATE,
            "Outcome evidence validates effectiveness confidence; calibration and readiness criteria support formal program graduation.",
        )
    if trajectory_available and has_outcomes:
        return (
            BQC5_GRADUATION_RECOMMENDATION_VALIDATION_PERIOD,
            "Some outcome evidence exists but calibration or effectiveness support remains insufficient for graduation.",
        )
    if trajectory_available:
        return (
            BQC5_GRADUATION_RECOMMENDATION_VALIDATION_PERIOD,
            "Trajectory is active but no validated outcome evidence exists; one additional validation period is required.",
        )
    return (
        BQC5_GRADUATION_RECOMMENDATION_IMMATURE,
        "Recurrence program lacks trajectory activation and validated outcome evidence required for graduation.",
    )


def build_recurrence_outcome_validation(
    *,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_remediation_targets: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
    recurrence_trajectory_summary: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_maturity: Mapping[str, Any] | None = None,
    recurrence_completion: Mapping[str, Any] | None = None,
    recurrence_graduation_audit: Mapping[str, Any] | None = None,
    event_log: Mapping[str, Any] | None = None,
    as_of: Any | None = None,
    bqc4_effectiveness_baseline: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence outcome validation and recalibrated confidence audit."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    outcome_validation_summary = summarize_recurrence_outcomes(
        recurrence_history=history,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_remediation_targets=recurrence_remediation_targets,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
        event_log=event_log,
        as_of=as_of,
    )
    base_confidence_audit = build_recurrence_confidence_audit(
        recurrence_forecast=recurrence_forecast,
        recurrence_governance=recurrence_governance,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_maturity=recurrence_maturity,
        recurrence_completion=recurrence_completion,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
        recurrence_history=history,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_portfolio_summary=history.get("recurrence_portfolio_summary")
        if isinstance(history.get("recurrence_portfolio_summary"), Mapping)
        else None,
    )
    outcome_effectiveness_audit = _audit_effectiveness_confidence_with_outcomes(
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
        outcome_validation_summary=outcome_validation_summary,
    )
    confidence_audit = dict(base_confidence_audit)
    confidence_audit["effectiveness_confidence_audit"] = outcome_effectiveness_audit
    confidence_audit["outcome_validation_summary"] = outcome_validation_summary
    confidence_audit["recurrence_confidence_calibration_summary"] = calculate_confidence_calibration_score(
        forecast_confidence_audit=confidence_audit.get("forecast_confidence_audit"),
        governance_confidence_audit=confidence_audit.get("governance_confidence_audit"),
        effectiveness_confidence_audit=outcome_effectiveness_audit,
    )
    calibration_summary = confidence_audit["recurrence_confidence_calibration_summary"]
    baseline = bqc4_effectiveness_baseline if isinstance(bqc4_effectiveness_baseline, Mapping) else BQC4_EFFECTIVENESS_BASELINE
    graduation = recurrence_graduation_audit if isinstance(recurrence_graduation_audit, Mapping) else {}
    graduation_summary = graduation.get("recurrence_graduation_audit_summary")
    if not isinstance(graduation_summary, Mapping):
        graduation_summary = summarize_recurrence_graduation_audit(graduation)
    recommendation, recommendation_rationale = _determine_bqc5_graduation_recommendation(
        calibration_summary=calibration_summary,
        trajectory_summary=recurrence_trajectory_summary if isinstance(recurrence_trajectory_summary, Mapping) else {},
        effectiveness_audit=outcome_effectiveness_audit,
        graduation_audit_summary=graduation_summary,
        outcome_validation_summary=outcome_validation_summary,
    )
    missing_outcome_signal = None
    if not bool(outcome_validation_summary.get("has_validated_outcomes")):
        missing_outcome_signal = (
            "At least one validated outcome event is required: retired key, dormant key, "
            "measurable recurrence reduction, or confirmed remediation impact."
        )
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "validation_definition": RECURRENCE_OUTCOME_VALIDATION_DEFINITION,
        "outcome_validation_summary": outcome_validation_summary,
        "effectiveness_confidence_audit": outcome_effectiveness_audit,
        "recurrence_confidence_audit": confidence_audit,
        "recurrence_confidence_calibration_summary": calibration_summary,
        "calibration_comparison": {
            "bqc4_baseline": dict(baseline),
            "bqc5_current": {
                "reported_confidence": float(outcome_effectiveness_audit.get("reported_confidence") or 0.0),
                "evidence_strength": float(outcome_effectiveness_audit.get("evidence_strength") or 0.0),
                "calibration_gap": float(outcome_effectiveness_audit.get("calibration_gap") or 0.0),
                "confidence_calibration_score": float(
                    calibration_summary.get("confidence_calibration_score") or 0.0
                ),
                "largest_calibration_gap": float(calibration_summary.get("largest_calibration_gap") or 0.0),
                "graduation_confidence_ready": bool(calibration_summary.get("graduation_confidence_ready")),
            },
            "effectiveness_evidence_delta": round(
                float(outcome_effectiveness_audit.get("evidence_strength") or 0.0)
                - float(baseline.get("evidence_strength") or 0.0),
                2,
            ),
            "calibration_score_delta": round(
                float(calibration_summary.get("confidence_calibration_score") or 0.0)
                - float(baseline.get("confidence_calibration_score") or 0.0),
                1,
            ),
            "largest_gap_delta": round(
                float(calibration_summary.get("largest_calibration_gap") or 0.0)
                - float(baseline.get("largest_calibration_gap") or 0.0),
                2,
            ),
        },
        "final_graduation_recommendation": recommendation,
        "final_graduation_recommendation_rationale": recommendation_rationale,
        "missing_outcome_signal": missing_outcome_signal,
        "formal_graduation_criteria_met": recommendation == BQC5_GRADUATION_RECOMMENDATION_GRADUATE,
    }


def render_recurrence_outcome_validation_report_markdown(
    validation: Mapping[str, Any] | None,
    *,
    generated_at: str | None = None,
) -> str:
    """Render the standalone BQ-C5 effectiveness outcome validation report."""
    payload = validation if isinstance(validation, Mapping) else {}
    outcomes = payload.get("outcome_validation_summary")
    if not isinstance(outcomes, Mapping):
        outcomes = {}
    effectiveness = payload.get("effectiveness_confidence_audit")
    if not isinstance(effectiveness, Mapping):
        effectiveness = {}
    calibration = payload.get("recurrence_confidence_calibration_summary")
    if not isinstance(calibration, Mapping):
        calibration = {}
    comparison = payload.get("calibration_comparison")
    if not isinstance(comparison, Mapping):
        comparison = {}
    bqc4 = comparison.get("bqc4_baseline")
    if not isinstance(bqc4, Mapping):
        bqc4 = {}
    bqc5 = comparison.get("bqc5_current")
    if not isinstance(bqc5, Mapping):
        bqc5 = {}
    generated_at_s = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    recommendation = payload.get("final_graduation_recommendation")
    if recommendation == BQC5_GRADUATION_RECOMMENDATION_GRADUATE:
        recommendation_label = "A. Graduate recurrence program"
    elif recommendation == BQC5_GRADUATION_RECOMMENDATION_VALIDATION_PERIOD:
        recommendation_label = "B. One additional validation period required"
    else:
        recommendation_label = "C. Recurrence program remains operationally immature"

    lines = [
        "# BQ-C5 Effectiveness Outcome Validation",
        "",
        f"**Date:** {generated_at_s}",
        "**Protected replay only:** true",
        "",
        "# Outcome Evidence",
        "",
        f"- Total keys: `{int(outcomes.get('total_keys') or 0)}`",
        f"- Active keys: `{int(outcomes.get('active_keys') or 0)}`",
        f"- Validated retired keys: `{int(outcomes.get('retired_keys') or 0)}`",
        f"- Validated dormant keys: `{int(outcomes.get('dormant_keys') or 0)}`",
        f"- Validated outcome count: `{int(outcomes.get('validated_outcome_count') or 0)}`",
        f"- Has validated outcomes: `{str(bool(outcomes.get('has_validated_outcomes'))).lower()}`",
        "",
    ]
    validated_rows = outcomes.get("validated_outcomes") or []
    if validated_rows:
        for row in validated_rows:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                f"- `{row.get('signal_type')}`: {row.get('recurrence_key') or row.get('evidence_source')}"
            )
    else:
        lines.append("- No validated outcome signals discovered.")
    rejected_rows = outcomes.get("rejected_signals") or []
    if rejected_rows:
        lines.extend(["", "### Rejected Candidates", ""])
        for row in rejected_rows:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                f"- `{row.get('candidate_signal')}` ({row.get('recurrence_key') or 'portfolio'}): "
                f"{row.get('rejection_reason')}"
            )
    lines.extend(
        [
            "",
            "# Effectiveness Confidence",
            "",
            f"- Reported confidence: `{float(effectiveness.get('reported_confidence') or 0.0):.2f}`",
            f"- Outcome evidence strength: `{float(effectiveness.get('evidence_strength') or 0.0):.2f}`",
            f"- Calibration gap: `{float(effectiveness.get('calibration_gap') or 0.0):.2f}`",
            f"- Status: `{effectiveness.get('confidence_status')}`",
            f"- Outcome supported: `{str(bool(effectiveness.get('outcome_supported'))).lower()}`",
            "",
            "# Calibration Recalculation",
            "",
            f"- Calibration score: `{float(calibration.get('confidence_calibration_score') or 0.0):.1f}`",
            f"- Largest calibration gap: `{float(calibration.get('largest_calibration_gap') or 0.0):.2f}`",
            f"- Graduation confidence ready: `{str(bool(calibration.get('graduation_confidence_ready'))).lower()}`",
            f"- BQ-C4 effectiveness evidence: `{float(bqc4.get('evidence_strength') or 0.0):.2f}`",
            f"- BQ-C5 effectiveness evidence: `{float(bqc5.get('evidence_strength') or 0.0):.2f}`",
            f"- Evidence delta: `{float(comparison.get('effectiveness_evidence_delta') or 0.0):+.2f}`",
            f"- BQ-C4 calibration score: `{float(bqc4.get('confidence_calibration_score') or 0.0):.1f}`",
            f"- BQ-C5 calibration score: `{float(bqc5.get('confidence_calibration_score') or 0.0):.1f}`",
            f"- Calibration score delta: `{float(comparison.get('calibration_score_delta') or 0.0):+.1f}`",
            "",
            "# Graduation Impact",
            "",
            f"- Formal graduation criteria met: `{str(bool(payload.get('formal_graduation_criteria_met'))).lower()}`",
            f"- Missing outcome signal: {payload.get('missing_outcome_signal') or 'none'}",
            "",
            "# Final Recommendation",
            "",
            f"**{recommendation_label}**",
            "",
            str(payload.get("final_graduation_recommendation_rationale") or "No rationale recorded."),
            "",
        ]
    )
    return "\n".join(lines)


def enrich_recurrence_history_with_outcome_validation(
    history: Mapping[str, Any],
    *,
    event_log: Mapping[str, Any] | None = None,
    as_of: Any | None = None,
) -> dict[str, Any]:
    """Return a history payload with additive protected replay outcome validation fields."""
    payload = dict(history)
    validation = build_recurrence_outcome_validation(
        recurrence_history=payload,
        recurrence_lifecycle=payload.get("recurrence_lifecycle")
        if isinstance(payload.get("recurrence_lifecycle"), Mapping)
        else None,
        recurrence_remediation_targets=payload.get("recurrence_remediation_targets")
        if isinstance(payload.get("recurrence_remediation_targets"), Mapping)
        else None,
        recurrence_program_effectiveness=payload.get("recurrence_program_effectiveness")
        if isinstance(payload.get("recurrence_program_effectiveness"), Mapping)
        else None,
        recurrence_trajectory_summary=payload.get("recurrence_trajectory_summary")
        if isinstance(payload.get("recurrence_trajectory_summary"), Mapping)
        else None,
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        recurrence_governance=payload.get("recurrence_governance")
        if isinstance(payload.get("recurrence_governance"), Mapping)
        else None,
        recurrence_maturity=payload.get("recurrence_maturity")
        if isinstance(payload.get("recurrence_maturity"), Mapping)
        else None,
        recurrence_completion=payload.get("recurrence_completion")
        if isinstance(payload.get("recurrence_completion"), Mapping)
        else None,
        recurrence_graduation_audit=payload.get("recurrence_graduation_audit")
        if isinstance(payload.get("recurrence_graduation_audit"), Mapping)
        else None,
        event_log=event_log,
        as_of=as_of,
    )
    payload["recurrence_outcome_validation"] = validation
    payload["outcome_validation_summary"] = validation["outcome_validation_summary"]
    payload["recurrence_confidence_audit"] = validation["recurrence_confidence_audit"]
    payload["recurrence_confidence_calibration_summary"] = validation["recurrence_confidence_calibration_summary"]
    return payload
