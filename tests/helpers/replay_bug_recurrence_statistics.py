"""Program effectiveness, maturity, roadmap, completion, and graduation analytics.

**Owns (CG-4):** maturity level bands, program-effectiveness policy constants,
roadmap/completion assessments, graduation audit builders, trajectory snapshot
schema, and cross-taxonomy alignment maps (``RECURRENCE_FORECAST_LIFECYCLE_ALIGNMENT``).

**Consumes:** trend/forecast/lifecycle/governance classifiers from
``replay_bug_recurrence_history``; events aggregation via compatibility re-exports.

**Does not own:** trend/forecast/governance/lifecycle allowed-values, confidence
calibration, graduation threshold validation statuses, or outcome signal vocabulary.

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
from tests.helpers.replay_bug_recurrence_history import _regression_rate_value

RECURRENCE_PROGRAM_EFFECTIVENESS_MIN_OBSERVATIONS = RECURRENCE_FORECAST_CONFIDENCE_OBSERVATIONS
RECURRENCE_PROGRAM_EFFECTIVENESS_MIN_KEYS = 3
RECURRENCE_FORECAST_LIFECYCLE_ALIGNMENT: dict[str, frozenset[str]] = {
    RECURRENCE_FORECAST_WATCH: frozenset({RECURRENCE_LIFECYCLE_EMERGING}),
    RECURRENCE_FORECAST_ELEVATED: frozenset(
        {RECURRENCE_LIFECYCLE_RECURRING, RECURRENCE_LIFECYCLE_PERSISTENT}
    ),
    RECURRENCE_FORECAST_CONCENTRATED: frozenset(
        {RECURRENCE_LIFECYCLE_PERSISTENT, RECURRENCE_LIFECYCLE_RECURRING}
    ),
    RECURRENCE_FORECAST_STABLE: frozenset(
        {RECURRENCE_LIFECYCLE_DORMANT, RECURRENCE_LIFECYCLE_RETIRED}
    ),
}
RECURRENCE_GOVERNANCE_CONVERSION_DEFINITION = (
    "Advisory conversion rates from current governance funnel snapshot: "
    "watchlist_conversion_rate is investigate_keys / max(watch_keys, 1); "
    "investigate_conversion_rate is prioritize_keys / max(investigate_keys, 1); "
    "prioritize_conversion_rate is remediation_ready_keys / max(prioritize_keys, 1), "
    "where remediation_ready_keys have reduction_potential >= investigate threshold; "
    "retirement_conversion_rate is retirement_outcome_keys / max(total_governed_keys, 1)."
)
RECURRENCE_REMEDIATION_EFFECTIVENESS_DEFINITION = (
    "Advisory remediation effectiveness: targeted_keys from remediation summary; "
    "improved_keys are targeted keys in dormant or retired lifecycle stages; "
    "unresolved_keys are targeted keys still active; recurrence_reduction_rate is "
    "resolved_or_retired_keys / max(historically_targeted_keys, 1). Without longitudinal "
    "remediation history, historically_targeted_keys defaults to current targeted_keys."
)
RECURRENCE_FORECAST_EFFECTIVENESS_DEFINITION = (
    "Advisory forecast effectiveness: forecast_accuracy is the share of key forecasts whose "
    "lifecycle_stage aligns with the forecast_classification alignment map; "
    "predicted_recurrences counts watch/elevated/concentrated forecasts; "
    "realized_recurrences counts aligned lifecycle outcomes. Low observation volume yields "
    "low effectiveness_confidence without fabricating accuracy."
)
RECURRENCE_PORTFOLIO_TRAJECTORY_DEFINITION = (
    "Portfolio trajectory compares current portfolio, governance, lifecycle, and stability "
    "metrics against a stored baseline snapshot when available; otherwise reports baseline "
    "values with trajectory_available=false and zero change metrics."
)
RECURRENCE_STABILITY_TRAJECTORY_DEFINITION = (
    "Stability trajectory reports current stability_score and regression_recurrence_rate "
    "against baseline values; change metrics are zero when no prior baseline snapshot exists."
)
RECURRENCE_TRAJECTORY_SCHEMA_VERSION = 1
RECURRENCE_TRAJECTORY_HISTORY_DEFINITION = (
    "Append-only protected replay recurrence trajectory snapshots. Snapshot #1 is the "
    "longitudinal baseline; trajectory_available becomes true once two or more snapshots exist."
)
RECURRENCE_TRAJECTORY_SUMMARY_DEFINITION = (
    "Trajectory summary compares the current snapshot against the baseline snapshot. "
    "With one snapshot only, trajectory_available=false and change metrics remain zero."
)
RECURRENCE_TRAJECTORY_ACTIVATION_MIN_SNAPSHOTS = 2
RECURRENCE_TRAJECTORY_BASELINE_MESSAGE = (
    "Trajectory baseline established. Additional snapshots required for change detection."
)


def empty_recurrence_trajectory_history() -> dict[str, Any]:
    return {
        "schema_version": RECURRENCE_TRAJECTORY_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "definition": RECURRENCE_TRAJECTORY_HISTORY_DEFINITION,
        "snapshots": [],
    }


def load_recurrence_trajectory_history(path: Path | str | None = None) -> dict[str, Any]:
    """Load append-only recurrence trajectory history from disk."""
    history_path = Path(path or RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH)
    if not history_path.is_file():
        return empty_recurrence_trajectory_history()
    raw = json.loads(history_path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping) or not isinstance(raw.get("snapshots"), list):
        raise ValueError("trajectory history must be a JSON object with a snapshots list")
    if raw.get("schema_version") != RECURRENCE_TRAJECTORY_SCHEMA_VERSION:
        raise ValueError(f"unsupported trajectory history schema_version: {raw.get('schema_version')!r}")
    return {
        "schema_version": RECURRENCE_TRAJECTORY_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "definition": RECURRENCE_TRAJECTORY_HISTORY_DEFINITION,
        "snapshots": [dict(item) for item in raw["snapshots"] if isinstance(item, Mapping)],
    }


def write_recurrence_trajectory_history(
    history: Mapping[str, Any],
    path: Path | str | None = None,
) -> Path:
    """Write recurrence trajectory history JSON."""
    history_path = Path(path or RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(dict(history), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return history_path


def _trajectory_float(value: Any) -> float:
    try:
        return round(float(value or 0.0), 4)
    except (TypeError, ValueError):
        return 0.0


def _trajectory_snapshot_fingerprint(snapshot: Mapping[str, Any]) -> tuple[Any, ...]:
    source = snapshot if isinstance(snapshot, Mapping) else {}
    return (
        int(source.get("protected_observation_count") or 0),
        int(source.get("unique_recurrence_keys") or 0),
        _trajectory_float(source.get("regression_recurrence_rate")),
        _trajectory_float(source.get("governance_health_score")),
        _trajectory_float(source.get("lifecycle_health_score")),
        _trajectory_float(source.get("portfolio_risk_score")),
        _trajectory_float(source.get("operational_readiness_score")),
        _trajectory_float(source.get("effectiveness_score")),
        _trajectory_float(source.get("maturity_score")),
        _trajectory_float(source.get("stability_score")),
        _trajectory_float(source.get("program_effectiveness_score")),
    )


def build_recurrence_trajectory_snapshot(
    *,
    timestamp: str,
    artifact_source: str,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_portfolio_summary: Mapping[str, Any] | None = None,
    recurrence_forecast_summary: Mapping[str, Any] | None = None,
    recurrence_governance_summary: Mapping[str, Any] | None = None,
    recurrence_lifecycle_summary: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness_summary: Mapping[str, Any] | None = None,
    recurrence_maturity_summary: Mapping[str, Any] | None = None,
    snapshot_index: int | None = None,
) -> dict[str, Any]:
    """Build one protected replay recurrence trajectory snapshot."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    portfolio_summary = recurrence_portfolio_summary if isinstance(recurrence_portfolio_summary, Mapping) else {}
    forecast_summary = recurrence_forecast_summary if isinstance(recurrence_forecast_summary, Mapping) else {}
    governance_summary = recurrence_governance_summary if isinstance(recurrence_governance_summary, Mapping) else {}
    lifecycle_summary = recurrence_lifecycle_summary if isinstance(recurrence_lifecycle_summary, Mapping) else {}
    program_summary = (
        recurrence_program_effectiveness_summary
        if isinstance(recurrence_program_effectiveness_summary, Mapping)
        else {}
    )
    maturity_summary = recurrence_maturity_summary if isinstance(recurrence_maturity_summary, Mapping) else {}
    protected_observation_count = int(
        portfolio_summary.get("total_observations")
        or history.get("total_rows")
        or 0
    )
    unique_recurrence_keys = int(history.get("unique_recurrence_count") or portfolio_summary.get("total_keys") or 0)
    return {
        "snapshot_index": int(snapshot_index or 0),
        "timestamp": str(timestamp or "").strip(),
        "artifact_source": str(artifact_source or "").strip(),
        "protected_observation_count": protected_observation_count,
        "unique_recurrence_keys": unique_recurrence_keys,
        "regression_recurrence_rate": _regression_rate_value(history.get("regression_recurrence_rate")),
        "governance_health_score": _trajectory_float(
            governance_summary.get("governance_health_score")
        ),
        "lifecycle_health_score": _trajectory_float(
            lifecycle_summary.get("lifecycle_health_score")
        ),
        "portfolio_risk_score": _trajectory_float(portfolio_summary.get("portfolio_risk_score")),
        "operational_readiness_score": _trajectory_float(
            maturity_summary.get("operational_readiness_score")
        ),
        "effectiveness_score": _trajectory_float(program_summary.get("effectiveness_confidence")),
        "maturity_score": _trajectory_float(maturity_summary.get("overall_maturity_score")),
        "stability_score": _trajectory_float(forecast_summary.get("stability_score")),
        "program_effectiveness_score": _trajectory_float(
            program_summary.get("program_effectiveness_score")
        ),
    }


def append_recurrence_trajectory_history(
    history: Mapping[str, Any] | None,
    snapshot: Mapping[str, Any],
    *,
    temporal_capture: bool = False,
) -> dict[str, Any]:
    """Return trajectory history with one deduped snapshot appended."""
    base = history if isinstance(history, Mapping) else empty_recurrence_trajectory_history()
    snapshots = [
        dict(item) for item in (base.get("snapshots") or ()) if isinstance(item, Mapping)
    ]
    candidate = dict(snapshot)
    if snapshots and _trajectory_snapshot_fingerprint(snapshots[-1]) == _trajectory_snapshot_fingerprint(candidate):
        same_timestamp = str(snapshots[-1].get("timestamp") or "") == str(candidate.get("timestamp") or "")
        if not temporal_capture or same_timestamp:
            return {
                "schema_version": RECURRENCE_TRAJECTORY_SCHEMA_VERSION,
                "report_only": RECURRENCE_REPORT_ONLY,
                "advisory_only": RECURRENCE_ADVISORY_ONLY,
                "protected_replay_only": True,
                "definition": RECURRENCE_TRAJECTORY_HISTORY_DEFINITION,
                "snapshots": snapshots,
            }
    candidate["snapshot_index"] = len(snapshots) + 1
    return {
        "schema_version": RECURRENCE_TRAJECTORY_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "definition": RECURRENCE_TRAJECTORY_HISTORY_DEFINITION,
        "snapshots": snapshots + [candidate],
    }


def prior_program_effectiveness_from_trajectory_snapshot(
    snapshot: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Convert one trajectory snapshot into prior program-effectiveness inputs."""
    source = snapshot if isinstance(snapshot, Mapping) else {}
    return {
        "program_effectiveness_summary": {
            "program_effectiveness_score": source.get("program_effectiveness_score"),
            "effectiveness_confidence": source.get("effectiveness_score"),
        },
        "portfolio_trajectory_summary": {
            "portfolio_risk_current": source.get("portfolio_risk_score"),
            "governance_health_current": source.get("governance_health_score"),
            "lifecycle_health_current": source.get("lifecycle_health_score"),
        },
        "stability_trajectory_summary": {
            "stability_score_current": source.get("stability_score"),
            "recurrence_rate_current": source.get("regression_recurrence_rate"),
        },
    }


def _trajectory_direction(change: float, *, higher_is_better: bool = True) -> str:
    if abs(float(change or 0.0)) <= 0.0001:
        return "stable"
    if higher_is_better:
        return "improving" if change > 0 else "regressing"
    return "improving" if change < 0 else "regressing"


def _trajectory_percent_change(baseline: float, current: float) -> float:
    baseline_value = float(baseline or 0.0)
    current_value = float(current or 0.0)
    if abs(baseline_value) <= 0.0001:
        return 0.0 if abs(current_value) <= 0.0001 else round(current_value * 100.0, 2)
    return round(((current_value - baseline_value) / baseline_value) * 100.0, 2)


def _trajectory_metric_change(
    *,
    baseline: Mapping[str, Any],
    current: Mapping[str, Any],
    field: str,
    higher_is_better: bool = True,
) -> dict[str, Any]:
    baseline_value = _trajectory_float(baseline.get(field))
    current_value = _trajectory_float(current.get(field))
    absolute_change = round(current_value - baseline_value, 4)
    return {
        "baseline": baseline_value,
        "current": current_value,
        "absolute_change": absolute_change,
        "percent_change": _trajectory_percent_change(baseline_value, current_value),
        "direction": _trajectory_direction(absolute_change, higher_is_better=higher_is_better),
    }


def summarize_recurrence_trajectory(
    history: Mapping[str, Any] | None,
    *,
    current_snapshot: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence trajectory from stored snapshots."""
    source = history if isinstance(history, Mapping) else empty_recurrence_trajectory_history()
    snapshots = [dict(item) for item in (source.get("snapshots") or ()) if isinstance(item, Mapping)]
    if current_snapshot and isinstance(current_snapshot, Mapping):
        projected = append_recurrence_trajectory_history(source, current_snapshot)
        snapshots = [dict(item) for item in (projected.get("snapshots") or ()) if isinstance(item, Mapping)]
    snapshot_count = len(snapshots)
    trajectory_available = snapshot_count >= RECURRENCE_TRAJECTORY_ACTIVATION_MIN_SNAPSHOTS
    baseline_snapshot = dict(snapshots[0]) if snapshots else {}
    latest_snapshot = dict(snapshots[-1]) if snapshots else dict(current_snapshot or {})
    if not latest_snapshot and isinstance(current_snapshot, Mapping):
        latest_snapshot = dict(current_snapshot)

    portfolio_risk = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="portfolio_risk_score",
        higher_is_better=False,
    )
    governance_health = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="governance_health_score",
    )
    lifecycle_health = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="lifecycle_health_score",
    )
    operational_readiness = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="operational_readiness_score",
    )
    effectiveness = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="effectiveness_score",
    )
    maturity = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="maturity_score",
    )
    stability = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="stability_score",
    )
    program_effectiveness = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="program_effectiveness_score",
    )
    regression_rate = _trajectory_metric_change(
        baseline=baseline_snapshot,
        current=latest_snapshot,
        field="regression_recurrence_rate",
        higher_is_better=False,
    )

    if not trajectory_available:
        portfolio_risk["absolute_change"] = 0.0
        portfolio_risk["percent_change"] = 0.0
        portfolio_risk["direction"] = "stable"
        governance_health["absolute_change"] = 0.0
        governance_health["percent_change"] = 0.0
        governance_health["direction"] = "stable"
        lifecycle_health["absolute_change"] = 0.0
        lifecycle_health["percent_change"] = 0.0
        lifecycle_health["direction"] = "stable"
        operational_readiness["absolute_change"] = 0.0
        operational_readiness["percent_change"] = 0.0
        operational_readiness["direction"] = "stable"
        effectiveness["absolute_change"] = 0.0
        effectiveness["percent_change"] = 0.0
        effectiveness["direction"] = "stable"
        maturity["absolute_change"] = 0.0
        maturity["percent_change"] = 0.0
        maturity["direction"] = "stable"
        stability["absolute_change"] = 0.0
        stability["percent_change"] = 0.0
        stability["direction"] = "stable"
        program_effectiveness["absolute_change"] = 0.0
        program_effectiveness["percent_change"] = 0.0
        program_effectiveness["direction"] = "stable"
        regression_rate["absolute_change"] = 0.0
        regression_rate["percent_change"] = 0.0
        regression_rate["direction"] = "stable"

    return {
        "schema_version": RECURRENCE_TRAJECTORY_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "definition": RECURRENCE_TRAJECTORY_SUMMARY_DEFINITION,
        "trajectory_available": trajectory_available,
        "baseline_only": not trajectory_available,
        "snapshot_count": snapshot_count,
        "baseline_snapshot": baseline_snapshot,
        "current_snapshot": latest_snapshot,
        "portfolio_risk_change": portfolio_risk["absolute_change"],
        "governance_health_change": governance_health["absolute_change"],
        "lifecycle_health_change": lifecycle_health["absolute_change"],
        "operational_readiness_change": operational_readiness["absolute_change"],
        "effectiveness_change": effectiveness["absolute_change"],
        "maturity_change": maturity["absolute_change"],
        "portfolio_trajectory": portfolio_risk,
        "governance_trajectory": governance_health,
        "lifecycle_trajectory": lifecycle_health,
        "operational_readiness_trajectory": operational_readiness,
        "effectiveness_trajectory": effectiveness,
        "maturity_trajectory": maturity,
        "stability_trajectory": stability,
        "program_effectiveness_trajectory": program_effectiveness,
        "regression_rate_trajectory": regression_rate,
        "message": (
            RECURRENCE_TRAJECTORY_BASELINE_MESSAGE
            if snapshot_count <= 1
            else "Trajectory change detection active across baseline and current snapshots."
        ),
    }


def apply_recurrence_trajectory_to_analytics(
    *,
    timestamp: str,
    artifact_source: str,
    recurrence_history: Mapping[str, Any],
    recurrence_timeline: Sequence[Mapping[str, Any]] | None,
    recurrence_trends: Mapping[str, Any] | None,
    recurrence_forecast: Mapping[str, Any],
    recurrence_portfolio: Mapping[str, Any],
    recurrence_remediation_targets: Mapping[str, Any],
    recurrence_roi: Mapping[str, Any],
    recurrence_governance: Mapping[str, Any],
    recurrence_lifecycle: Mapping[str, Any],
    recurrence_program_effectiveness: Mapping[str, Any],
    recurrence_maturity: Mapping[str, Any],
    recurrence_roadmap: Mapping[str, Any],
    recurrence_completion: Mapping[str, Any],
    recurrence_graduation_audit: Mapping[str, Any],
    trajectory_history_path: Path | str | None = None,
    temporal_capture: bool = False,
) -> dict[str, Any]:
    """Append trajectory snapshots and rebuild analytics when trajectory activates."""
    current_snapshot = build_recurrence_trajectory_snapshot(
        timestamp=timestamp,
        artifact_source=artifact_source,
        recurrence_history=recurrence_history,
        recurrence_portfolio_summary=recurrence_portfolio.get("portfolio_summary")
        if isinstance(recurrence_portfolio.get("portfolio_summary"), Mapping)
        else None,
        recurrence_forecast_summary=recurrence_forecast.get("forecast_summary")
        if isinstance(recurrence_forecast.get("forecast_summary"), Mapping)
        else None,
        recurrence_governance_summary=recurrence_governance.get("governance_summary")
        if isinstance(recurrence_governance.get("governance_summary"), Mapping)
        else None,
        recurrence_lifecycle_summary=recurrence_lifecycle.get("lifecycle_summary")
        if isinstance(recurrence_lifecycle.get("lifecycle_summary"), Mapping)
        else None,
        recurrence_program_effectiveness_summary=recurrence_program_effectiveness.get(
            "program_effectiveness_summary"
        )
        if isinstance(recurrence_program_effectiveness.get("program_effectiveness_summary"), Mapping)
        else None,
        recurrence_maturity_summary=recurrence_maturity.get("recurrence_maturity_summary")
        if isinstance(recurrence_maturity.get("recurrence_maturity_summary"), Mapping)
        else None,
    )
    loaded_history = load_recurrence_trajectory_history(trajectory_history_path)

    artifact_source_normalized = str(artifact_source or "").replace("\\", "/").lower()
    committed_history = (
        Path(trajectory_history_path or RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH).resolve()
        == RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH.resolve()
    )
    if committed_history and not artifact_source_normalized.startswith(
        GOLDEN_REPLAY_ARTIFACT_SOURCE_PREFIX.lower()
    ):
        projected_history = loaded_history
    else:
        projected_history = append_recurrence_trajectory_history(
            loaded_history,
            current_snapshot,
            temporal_capture=temporal_capture,
        )
    trajectory_summary = summarize_recurrence_trajectory(projected_history)
    trajectory_available = bool(trajectory_summary.get("trajectory_available"))

    program_effectiveness = recurrence_program_effectiveness
    maturity = recurrence_maturity
    roadmap = recurrence_roadmap
    completion = recurrence_completion
    graduation_audit = recurrence_graduation_audit

    if trajectory_available:
        prior = prior_program_effectiveness_from_trajectory_snapshot(
            trajectory_summary.get("baseline_snapshot")
        )
        program_effectiveness = build_recurrence_program_effectiveness(
            recurrence_governance=recurrence_governance,
            recurrence_remediation_summary=recurrence_remediation_targets.get("remediation_summary")
            if isinstance(recurrence_remediation_targets.get("remediation_summary"), Mapping)
            else None,
            recurrence_roi_summary=recurrence_roi.get("roi_summary")
            if isinstance(recurrence_roi.get("roi_summary"), Mapping)
            else None,
            recurrence_lifecycle_summary=recurrence_lifecycle.get("lifecycle_summary")
            if isinstance(recurrence_lifecycle.get("lifecycle_summary"), Mapping)
            else None,
            recurrence_portfolio_summary=recurrence_portfolio.get("portfolio_summary")
            if isinstance(recurrence_portfolio.get("portfolio_summary"), Mapping)
            else None,
            recurrence_forecast=recurrence_forecast,
            recurrence_history=recurrence_history,
            recurrence_lifecycle=recurrence_lifecycle,
            recurrence_remediation_targets=recurrence_remediation_targets,
            prior_program_effectiveness=prior,
            trajectory_available=True,
        )
        maturity = build_recurrence_maturity_assessment(
            recurrence_history=recurrence_history,
            recurrence_trends=recurrence_trends,
            recurrence_forecast=recurrence_forecast,
            recurrence_portfolio=recurrence_portfolio,
            recurrence_remediation=recurrence_remediation_targets,
            recurrence_roi=recurrence_roi,
            recurrence_governance=recurrence_governance,
            recurrence_lifecycle=recurrence_lifecycle,
            recurrence_program_effectiveness=program_effectiveness,
        )
        roadmap = build_recurrence_strategic_roadmap(
            recurrence_maturity_summary=maturity["recurrence_maturity_summary"],
            recurrence_maturity_gap_analysis=maturity["maturity_gap_analysis"],
            recurrence_program_effectiveness_summary=program_effectiveness["program_effectiveness_summary"],
            recurrence_portfolio_summary=recurrence_portfolio.get("portfolio_summary")
            if isinstance(recurrence_portfolio.get("portfolio_summary"), Mapping)
            else None,
            recurrence_forecast_summary=recurrence_forecast.get("forecast_summary")
            if isinstance(recurrence_forecast.get("forecast_summary"), Mapping)
            else None,
            recurrence_lifecycle_summary=recurrence_lifecycle.get("lifecycle_summary")
            if isinstance(recurrence_lifecycle.get("lifecycle_summary"), Mapping)
            else None,
            recurrence_remediation_effectiveness_summary=program_effectiveness[
                "remediation_effectiveness_summary"
            ],
            portfolio_trajectory_summary=program_effectiveness["portfolio_trajectory_summary"],
            total_observations=int(recurrence_history.get("total_rows") or 0),
            total_keys=int(recurrence_history.get("unique_recurrence_count") or 0),
        )
        completion = build_recurrence_completion_assessment(
            recurrence_maturity_summary=maturity["recurrence_maturity_summary"],
            recurrence_program_effectiveness_summary=program_effectiveness["program_effectiveness_summary"],
            recurrence_target_state=roadmap["recurrence_target_state"],
            recurrence_roadmap_summary=roadmap["recurrence_roadmap_summary"],
            recurrence_history={
                **recurrence_history,
                "recurrence_timeline": list(recurrence_timeline or ()),
                "recurrence_trends": recurrence_trends or {},
                "recurrence_forecast": recurrence_forecast,
                "recurrence_portfolio": recurrence_portfolio,
                "recurrence_portfolio_summary": recurrence_portfolio.get("portfolio_summary"),
                "recurrence_governance": recurrence_governance,
                "recurrence_governance_summary": recurrence_governance.get("governance_summary"),
                "recurrence_retirement_summary": recurrence_governance.get("retirement_summary"),
                "recurrence_lifecycle": recurrence_lifecycle,
                "recurrence_lifecycle_summary": recurrence_lifecycle.get("lifecycle_summary"),
                "recurrence_transition_summary": recurrence_lifecycle.get("transition_summary"),
                "recurrence_age_distribution": recurrence_lifecycle.get("age_distribution"),
                "recurrence_closure_effectiveness": recurrence_lifecycle.get("closure_effectiveness"),
                "recurrence_remediation_targets": recurrence_remediation_targets,
                "recurrence_remediation_summary": recurrence_remediation_targets.get("remediation_summary"),
                "recurrence_roi": recurrence_roi,
                "recurrence_roi_summary": recurrence_roi.get("roi_summary"),
            },
            recurrence_governance_summary=recurrence_governance.get("governance_summary")
            if isinstance(recurrence_governance.get("governance_summary"), Mapping)
            else None,
            recurrence_forecast_summary=recurrence_forecast.get("forecast_summary")
            if isinstance(recurrence_forecast.get("forecast_summary"), Mapping)
            else None,
            forecast_effectiveness_summary=program_effectiveness["forecast_effectiveness_summary"],
            remediation_effectiveness_summary=program_effectiveness["remediation_effectiveness_summary"],
            recurrence_lifecycle_summary=recurrence_lifecycle.get("lifecycle_summary")
            if isinstance(recurrence_lifecycle.get("lifecycle_summary"), Mapping)
            else None,
            recurrence_roi_summary=recurrence_roi.get("roi_summary")
            if isinstance(recurrence_roi.get("roi_summary"), Mapping)
            else None,
            portfolio_trajectory_summary=program_effectiveness["portfolio_trajectory_summary"],
        )
        graduation_audit = build_recurrence_graduation_audit(
            recurrence_history={
                **recurrence_history,
                "recurrence_timeline": list(recurrence_timeline or ()),
                "recurrence_trends": recurrence_trends or {},
                "recurrence_forecast": recurrence_forecast,
                "recurrence_portfolio": recurrence_portfolio,
                "recurrence_portfolio_summary": recurrence_portfolio.get("portfolio_summary"),
                "recurrence_governance": recurrence_governance,
                "recurrence_governance_summary": recurrence_governance.get("governance_summary"),
                "recurrence_lifecycle": recurrence_lifecycle,
                "recurrence_lifecycle_summary": recurrence_lifecycle.get("lifecycle_summary"),
                "recurrence_program_effectiveness": program_effectiveness,
                "recurrence_program_effectiveness_summary": program_effectiveness[
                    "program_effectiveness_summary"
                ],
                "recurrence_maturity": maturity,
                "recurrence_maturity_summary": maturity["recurrence_maturity_summary"],
                "recurrence_roadmap": roadmap,
                "recurrence_roadmap_summary": roadmap["recurrence_roadmap_summary"],
                "recurrence_completion": completion,
                "recurrence_completion_summary": completion["recurrence_completion_summary"],
                "portfolio_trajectory_summary": program_effectiveness["portfolio_trajectory_summary"],
                "stability_trajectory_summary": program_effectiveness["stability_trajectory_summary"],
                "recurrence_trajectory_summary": trajectory_summary,
            },
            recurrence_trends=recurrence_trends,
            recurrence_forecast=recurrence_forecast,
            recurrence_portfolio=recurrence_portfolio,
            recurrence_remediation=recurrence_remediation_targets,
            recurrence_roi=recurrence_roi,
            recurrence_governance=recurrence_governance,
            recurrence_lifecycle=recurrence_lifecycle,
            recurrence_program_effectiveness=program_effectiveness,
            recurrence_maturity=maturity,
            recurrence_roadmap=roadmap,
            recurrence_completion=completion,
        )
        trajectory_summary = summarize_recurrence_trajectory(projected_history)

    write_recurrence_trajectory_history(projected_history, trajectory_history_path)
    return {
        "recurrence_trajectory_history": projected_history,
        "recurrence_trajectory_summary": trajectory_summary,
        "recurrence_program_effectiveness": program_effectiveness,
        "recurrence_maturity": maturity,
        "recurrence_roadmap": roadmap,
        "recurrence_completion": completion,
        "recurrence_graduation_audit": graduation_audit,
    }


RECURRENCE_PROGRAM_EFFECTIVENESS_SCORE_DEFINITION = (
    "Advisory 0-100 score: 100 * clamp01(0.20*closure_rate + 0.20*(forecast_accuracy*forecast_confidence) "
    "+ 0.20*(stability_score/100) + 0.15*(1-regression_rate) + 0.15*(governance_health_score/100) "
    "+ 0.10*(lifecycle_health_score/100)) * (1 - 0.30*watchlist_pressure), where watchlist_pressure is "
    "watchlist_size/max(total_keys,1). Higher scores indicate improving program outcomes."
)
RECURRENCE_EFFECTIVENESS_CONFIDENCE_DEFINITION = (
    "Weighted blend of forecast_confidence (35%), governance_confidence (35%), and "
    "observation/key volume factor min(1, observations/5)*min(1, keys/3) scaled by 0.4 when "
    "trajectory history is unavailable (30%)."
)


def _effectiveness_confidence(
    *,
    total_observations: int,
    total_keys: int,
    forecast_confidence: float,
    governance_confidence: float,
    trajectory_available: bool,
) -> float:
    observations = max(int(total_observations or 0), 0)
    keys = max(int(total_keys or 0), 0)
    volume_factor = min(1.0, observations / float(RECURRENCE_PROGRAM_EFFECTIVENESS_MIN_OBSERVATIONS))
    volume_factor *= min(1.0, keys / float(RECURRENCE_PROGRAM_EFFECTIVENESS_MIN_KEYS))
    if not trajectory_available:
        volume_factor *= 0.4
    return round(
        0.35 * float(forecast_confidence or 0.0)
        + 0.35 * float(governance_confidence or 0.0)
        + 0.30 * volume_factor,
        2,
    )


def _forecast_lifecycle_aligned(forecast_classification: str, lifecycle_stage: str) -> bool:
    forecast = str(forecast_classification or "").strip()
    stage = str(lifecycle_stage or "").strip()
    allowed = RECURRENCE_FORECAST_LIFECYCLE_ALIGNMENT.get(forecast)
    return stage in allowed if allowed else False


def _governance_status_counts_from_watchlist(
    watchlist: Sequence[Mapping[str, Any]] | None,
) -> dict[str, int]:
    counts = {status: 0 for status in sorted(RECURRENCE_GOVERNANCE_STATUSES)}
    for entry in watchlist or ():
        if not isinstance(entry, Mapping):
            continue
        status = str(entry.get("governance_status") or RECURRENCE_GOVERNANCE_OBSERVE).strip()
        if status in counts:
            counts[status] += 1
    return counts


def calculate_recurrence_effectiveness_metrics(
    *,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_remediation_summary: Mapping[str, Any] | None = None,
    recurrence_roi_summary: Mapping[str, Any] | None = None,
    recurrence_lifecycle_summary: Mapping[str, Any] | None = None,
    recurrence_portfolio_summary: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_remediation_targets: Mapping[str, Any] | None = None,
    recurrence_governance_summary: Mapping[str, Any] | None = None,
    prior_program_effectiveness: Mapping[str, Any] | None = None,
    trajectory_available: bool | None = None,
) -> dict[str, Any]:
    """Calculate protected replay recurrence program effectiveness metrics."""
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    remediation_summary = (
        recurrence_remediation_summary if isinstance(recurrence_remediation_summary, Mapping) else {}
    )
    roi_summary = recurrence_roi_summary if isinstance(recurrence_roi_summary, Mapping) else {}
    lifecycle_summary = recurrence_lifecycle_summary if isinstance(recurrence_lifecycle_summary, Mapping) else {}
    portfolio_summary = recurrence_portfolio_summary if isinstance(recurrence_portfolio_summary, Mapping) else {}
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    lifecycle = recurrence_lifecycle if isinstance(recurrence_lifecycle, Mapping) else {}
    targets = recurrence_remediation_targets if isinstance(recurrence_remediation_targets, Mapping) else {}
    governance_summary = (
        recurrence_governance_summary if isinstance(recurrence_governance_summary, Mapping) else {}
    )
    prior = prior_program_effectiveness if isinstance(prior_program_effectiveness, Mapping) else {}

    watchlist = [
        dict(row) for row in (governance.get("watchlist") or ()) if isinstance(row, Mapping)
    ]
    lifecycle_keys = [
        dict(row) for row in (lifecycle.get("keys") or ()) if isinstance(row, Mapping)
    ]
    if not lifecycle_keys and isinstance(history.get("recurrence_lifecycle"), Mapping):
        lifecycle_keys = [
            dict(row)
            for row in (history["recurrence_lifecycle"].get("keys") or ())
            if isinstance(row, Mapping)
        ]
    lifecycle_by_key = {
        str(row.get("recurrence_key") or ""): row for row in lifecycle_keys if str(row.get("recurrence_key") or "")
    }
    remediation_by_key = {
        str(row.get("recurrence_key") or ""): dict(row)
        for row in (targets.get("keys") or ())
        if isinstance(row, Mapping) and str(row.get("recurrence_key") or "").strip()
    }

    total_keys = int(
        lifecycle_summary.get("active_keys", 0)
        + lifecycle_summary.get("dormant_keys", 0)
        + lifecycle_summary.get("retired_keys", 0)
        or history.get("unique_recurrence_count")
        or len(lifecycle_keys)
        or 0
    )
    total_observations = int(history.get("total_rows") or targets.get("total_observations") or 0)
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    forecast_confidence = float(
        forecast_summary.get("forecast_confidence") or portfolio_summary.get("forecast_confidence") or 0.0
    )
    governance_confidence = float(
        governance_summary.get("governance_confidence") or governance.get("governance_confidence") or 0.0
    )
    stability_score_current = float(forecast_summary.get("stability_score") or 100.0)
    regression_rate_current = _regression_rate_value(history.get("regression_recurrence_rate"))
    portfolio_risk_current = float(portfolio_summary.get("portfolio_risk_score") or 0.0)
    concentration_current = max(
        float(portfolio_summary.get("owner_concentration_ratio") or 0.0),
        float(portfolio_summary.get("category_concentration_ratio") or 0.0),
        float(portfolio_summary.get("field_path_concentration_ratio") or 0.0),
        float(portfolio_summary.get("scenario_concentration_ratio") or 0.0),
    )
    governance_health_current = float(
        governance_summary.get("governance_health_score") or governance.get("governance_health_score") or 0.0
    )
    lifecycle_health_current = float(
        lifecycle_summary.get("lifecycle_health_score") or lifecycle.get("lifecycle_health_score") or 0.0
    )
    closure_rate = float(lifecycle_summary.get("closure_rate") or 0.0)
    watchlist_size = int(governance_summary.get("watchlist_size") or len(watchlist) or 0)

    prior_summary = prior.get("program_effectiveness_summary")
    if not isinstance(prior_summary, Mapping):
        prior_summary = prior.get("recurrence_program_effectiveness_summary")
    if not isinstance(prior_summary, Mapping):
        prior_summary = {}
    prior_portfolio = prior.get("portfolio_trajectory_summary")
    if not isinstance(prior_portfolio, Mapping):
        prior_portfolio = {}
    prior_stability = prior.get("stability_trajectory_summary")
    if not isinstance(prior_stability, Mapping):
        prior_stability = {}
    if trajectory_available is None:
        trajectory_available = bool(prior_summary)
    trajectory_available = bool(trajectory_available)

    status_counts = _governance_status_counts_from_watchlist(watchlist)
    watch_keys = int(status_counts.get(RECURRENCE_GOVERNANCE_WATCH) or 0)
    investigate_keys = int(status_counts.get(RECURRENCE_GOVERNANCE_INVESTIGATE) or 0)
    prioritize_keys = int(status_counts.get(RECURRENCE_GOVERNANCE_PRIORITIZE) or 0)
    retire_candidates = int(status_counts.get(RECURRENCE_GOVERNANCE_RETIRE_CANDIDATE) or 0)
    retirement_outcome_keys = retire_candidates + int(lifecycle_summary.get("retired_keys") or 0) + int(
        lifecycle_summary.get("dormant_keys") or 0
    )
    remediation_ready_keys = sum(
        1
        for row in watchlist
        if str(row.get("governance_status") or "") == RECURRENCE_GOVERNANCE_PRIORITIZE
        and float(remediation_by_key.get(str(row.get("recurrence_key") or ""), {}).get("reduction_potential") or 0.0)
        >= RECURRENCE_GOVERNANCE_INVESTIGATE_THRESHOLD
    )
    total_governed_keys = max(len(watchlist), 1)
    watchlist_conversion_rate = round(investigate_keys / float(max(watch_keys, 1)), 4)
    investigate_conversion_rate = round(prioritize_keys / float(max(investigate_keys, 1)), 4)
    prioritize_conversion_rate = round(remediation_ready_keys / float(max(prioritize_keys, 1)), 4)
    retirement_conversion_rate = round(retirement_outcome_keys / float(total_governed_keys), 4)
    governance_effectiveness = round(
        (
            watchlist_conversion_rate
            + investigate_conversion_rate
            + prioritize_conversion_rate
            + retirement_conversion_rate
        )
        / 4.0,
        4,
    )

    targeted_keys = int(targets.get("total_keys") or len(remediation_by_key) or 0)
    if targeted_keys <= 0 and remediation_summary.get("highest_leverage_key"):
        targeted_keys = 1
    improved_keys = 0
    unresolved_keys = 0
    resolved_or_retired_keys = 0
    for key, remediation_row in remediation_by_key.items():
        lifecycle_row = lifecycle_by_key.get(key, {})
        stage = str(lifecycle_row.get("lifecycle_stage") or "")
        if stage in {RECURRENCE_LIFECYCLE_DORMANT, RECURRENCE_LIFECYCLE_RETIRED}:
            improved_keys += 1
            resolved_or_retired_keys += 1
        else:
            unresolved_keys += 1
    historically_targeted_keys = max(targeted_keys, 1)
    recurrence_reduction_rate = round(resolved_or_retired_keys / float(historically_targeted_keys), 4)
    remediation_effectiveness = round(
        (recurrence_reduction_rate + (1.0 - unresolved_keys / float(max(targeted_keys, 1)))) / 2.0,
        4,
    )

    forecast_rows = [
        dict(row) for row in (forecast.get("key_forecasts") or ()) if isinstance(row, Mapping)
    ]
    predicted_recurrences = 0
    realized_recurrences = 0
    aligned_forecasts = 0
    for row in forecast_rows:
        key = str(row.get("recurrence_key") or "")
        forecast_classification = str(row.get("forecast_classification") or "")
        lifecycle_stage = str(lifecycle_by_key.get(key, {}).get("lifecycle_stage") or "")
        if forecast_classification in {
            RECURRENCE_FORECAST_WATCH,
            RECURRENCE_FORECAST_ELEVATED,
            RECURRENCE_FORECAST_CONCENTRATED,
        }:
            predicted_recurrences += 1
        if _forecast_lifecycle_aligned(forecast_classification, lifecycle_stage):
            aligned_forecasts += 1
            realized_recurrences += 1
    forecast_key_count = max(len(forecast_rows), 1)
    forecast_accuracy = round(aligned_forecasts / float(forecast_key_count), 4)
    forecast_effectiveness = round(forecast_accuracy * forecast_confidence, 4)

    portfolio_risk_baseline = float(
        prior_portfolio.get("portfolio_risk_current") or portfolio_risk_current
    )
    concentration_baseline = float(
        prior_portfolio.get("concentration_current") or concentration_current
    )
    governance_health_baseline = float(
        prior_portfolio.get("governance_health_current") or governance_health_current
    )
    lifecycle_health_baseline = float(
        prior_portfolio.get("lifecycle_health_current") or lifecycle_health_current
    )

    if trajectory_available:
        stability_score_baseline = float(
            prior_stability.get("stability_score_current") or stability_score_current
        )
        regression_rate_baseline = float(
            prior_stability.get("recurrence_rate_current")
            if prior_stability.get("recurrence_rate_current") is not None
            else regression_rate_current
        )
        stability_change = round(stability_score_current - stability_score_baseline, 4)
        recurrence_rate_change = round(regression_rate_current - regression_rate_baseline, 4)
        portfolio_risk_change = round(portfolio_risk_current - portfolio_risk_baseline, 4)
        concentration_change = round(concentration_current - concentration_baseline, 4)
        governance_health_change = round(governance_health_current - governance_health_baseline, 4)
        lifecycle_health_change = round(lifecycle_health_current - lifecycle_health_baseline, 4)
    else:
        stability_score_baseline = stability_score_current
        regression_rate_baseline = regression_rate_current
        portfolio_risk_baseline = portfolio_risk_current
        concentration_baseline = concentration_current
        governance_health_baseline = governance_health_current
        lifecycle_health_baseline = lifecycle_health_current
        stability_change = 0.0
        recurrence_rate_change = 0.0
        portfolio_risk_change = 0.0
        concentration_change = 0.0
        governance_health_change = 0.0
        lifecycle_health_change = 0.0

    watchlist_pressure = min(1.0, watchlist_size / float(max(total_keys, 1)))
    if total_keys <= 0:
        program_effectiveness_score = 0.0
    else:
        blended = (
            0.20 * closure_rate
            + 0.20 * forecast_effectiveness
            + 0.20 * (stability_score_current / 100.0)
            + 0.15 * (1.0 - regression_rate_current)
            + 0.15 * (governance_health_current / 100.0)
            + 0.10 * (lifecycle_health_current / 100.0)
        )
        program_effectiveness_score = round(
            max(0.0, min(100.0, 100.0 * blended * (1.0 - 0.30 * watchlist_pressure))),
            1,
        )
    effectiveness_confidence = _effectiveness_confidence(
        total_observations=total_observations,
        total_keys=total_keys,
        forecast_confidence=forecast_confidence,
        governance_confidence=governance_confidence,
        trajectory_available=trajectory_available,
    )

    return {
        "total_keys": total_keys,
        "total_observations": total_observations,
        "trajectory_available": trajectory_available,
        "baseline_only": not trajectory_available,
        "governance_effectiveness": governance_effectiveness,
        "watchlist_conversion_rate": watchlist_conversion_rate,
        "investigate_conversion_rate": investigate_conversion_rate,
        "prioritize_conversion_rate": prioritize_conversion_rate,
        "retirement_conversion_rate": retirement_conversion_rate,
        "targeted_keys": targeted_keys,
        "improved_keys": improved_keys,
        "unresolved_keys": unresolved_keys,
        "recurrence_reduction_rate": recurrence_reduction_rate,
        "remediation_effectiveness": remediation_effectiveness,
        "forecast_accuracy": forecast_accuracy,
        "forecast_confidence": forecast_confidence,
        "predicted_recurrences": predicted_recurrences,
        "realized_recurrences": realized_recurrences,
        "forecast_effectiveness": forecast_effectiveness,
        "portfolio_risk_current": portfolio_risk_current,
        "portfolio_risk_baseline": portfolio_risk_baseline,
        "portfolio_risk_change": portfolio_risk_change,
        "concentration_current": concentration_current,
        "concentration_baseline": concentration_baseline,
        "concentration_change": concentration_change,
        "stability_score_current": stability_score_current,
        "stability_score_baseline": stability_score_baseline,
        "stability_change": stability_change,
        "recurrence_rate_current": regression_rate_current,
        "recurrence_rate_baseline": regression_rate_baseline,
        "recurrence_rate_change": recurrence_rate_change,
        "governance_health_current": governance_health_current,
        "governance_health_baseline": governance_health_baseline,
        "governance_health_change": governance_health_change,
        "lifecycle_health_current": lifecycle_health_current,
        "lifecycle_health_baseline": lifecycle_health_baseline,
        "lifecycle_health_change": lifecycle_health_change,
        "program_effectiveness_score": program_effectiveness_score,
        "effectiveness_confidence": effectiveness_confidence,
        "closure_rate": closure_rate,
        "watchlist_pressure": watchlist_pressure,
    }


def summarize_recurrence_program_effectiveness(
    effectiveness: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence program effectiveness."""
    source = effectiveness if isinstance(effectiveness, Mapping) else {}
    program_summary = source.get("program_effectiveness_summary")
    if isinstance(program_summary, Mapping):
        return dict(program_summary)
    metrics = source.get("effectiveness_metrics")
    if not isinstance(metrics, Mapping):
        metrics = calculate_recurrence_effectiveness_metrics()
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "program_effectiveness_score": float(metrics.get("program_effectiveness_score") or 0.0),
        "governance_effectiveness": float(metrics.get("governance_effectiveness") or 0.0),
        "remediation_effectiveness": float(metrics.get("remediation_effectiveness") or 0.0),
        "forecast_effectiveness": float(metrics.get("forecast_effectiveness") or 0.0),
        "stability_trajectory": {
            "stability_score_current": float(metrics.get("stability_score_current") or 0.0),
            "stability_change": float(metrics.get("stability_change") or 0.0),
            "recurrence_rate_change": float(metrics.get("recurrence_rate_change") or 0.0),
            "trajectory_available": bool(metrics.get("trajectory_available")),
        },
        "effectiveness_confidence": float(metrics.get("effectiveness_confidence") or 0.0),
        "recurrence_reduction_rate": float(metrics.get("recurrence_reduction_rate") or 0.0),
        "forecast_accuracy": float(metrics.get("forecast_accuracy") or 0.0),
        "stability_change": float(metrics.get("stability_change") or 0.0),
        "program_effectiveness_score_definition": RECURRENCE_PROGRAM_EFFECTIVENESS_SCORE_DEFINITION,
        "effectiveness_confidence_definition": RECURRENCE_EFFECTIVENESS_CONFIDENCE_DEFINITION,
    }


def build_recurrence_program_effectiveness(
    *,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_remediation_summary: Mapping[str, Any] | None = None,
    recurrence_roi_summary: Mapping[str, Any] | None = None,
    recurrence_lifecycle_summary: Mapping[str, Any] | None = None,
    recurrence_portfolio_summary: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_remediation_targets: Mapping[str, Any] | None = None,
    prior_program_effectiveness: Mapping[str, Any] | None = None,
    trajectory_available: bool | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence program effectiveness analytics."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    governance_summary = history.get("recurrence_governance_summary")
    if not isinstance(governance_summary, Mapping):
        governance_summary = governance.get("governance_summary")
    if not isinstance(governance_summary, Mapping):
        governance_summary = {}

    prior = prior_program_effectiveness
    if prior is None and isinstance(history.get("recurrence_program_effectiveness"), Mapping):
        prior = history["recurrence_program_effectiveness"]

    metrics = calculate_recurrence_effectiveness_metrics(
        recurrence_governance=governance,
        recurrence_remediation_summary=recurrence_remediation_summary,
        recurrence_roi_summary=recurrence_roi_summary,
        recurrence_lifecycle_summary=recurrence_lifecycle_summary,
        recurrence_portfolio_summary=recurrence_portfolio_summary,
        recurrence_forecast=recurrence_forecast,
        recurrence_history=history,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_remediation_targets=recurrence_remediation_targets,
        recurrence_governance_summary=governance_summary,
        prior_program_effectiveness=prior,
        trajectory_available=trajectory_available,
    )

    governance_effectiveness_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "watchlist_conversion_rate": metrics["watchlist_conversion_rate"],
        "investigate_conversion_rate": metrics["investigate_conversion_rate"],
        "prioritize_conversion_rate": metrics["prioritize_conversion_rate"],
        "retirement_conversion_rate": metrics["retirement_conversion_rate"],
        "governance_effectiveness": metrics["governance_effectiveness"],
        "conversion_definition": RECURRENCE_GOVERNANCE_CONVERSION_DEFINITION,
        "confidence_adjusted": not bool(metrics["trajectory_available"]),
    }
    remediation_effectiveness_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "targeted_keys": metrics["targeted_keys"],
        "improved_keys": metrics["improved_keys"],
        "unresolved_keys": metrics["unresolved_keys"],
        "recurrence_reduction_rate": metrics["recurrence_reduction_rate"],
        "remediation_effectiveness": metrics["remediation_effectiveness"],
        "effectiveness_definition": RECURRENCE_REMEDIATION_EFFECTIVENESS_DEFINITION,
    }
    forecast_effectiveness_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "forecast_accuracy": metrics["forecast_accuracy"],
        "forecast_confidence": metrics["forecast_confidence"],
        "predicted_recurrences": metrics["predicted_recurrences"],
        "realized_recurrences": metrics["realized_recurrences"],
        "forecast_effectiveness": metrics["forecast_effectiveness"],
        "low_confidence": metrics["effectiveness_confidence"] < 0.25,
        "effectiveness_definition": RECURRENCE_FORECAST_EFFECTIVENESS_DEFINITION,
    }
    portfolio_trajectory_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "trajectory_available": metrics["trajectory_available"],
        "baseline_only": metrics["baseline_only"],
        "portfolio_risk_current": metrics["portfolio_risk_current"],
        "portfolio_risk_baseline": metrics["portfolio_risk_baseline"],
        "portfolio_risk_change": metrics["portfolio_risk_change"],
        "concentration_current": metrics["concentration_current"],
        "concentration_baseline": metrics["concentration_baseline"],
        "concentration_change": metrics["concentration_change"],
        "governance_health_current": metrics["governance_health_current"],
        "governance_health_baseline": metrics["governance_health_baseline"],
        "governance_health_change": metrics["governance_health_change"],
        "lifecycle_health_current": metrics["lifecycle_health_current"],
        "lifecycle_health_baseline": metrics["lifecycle_health_baseline"],
        "lifecycle_health_change": metrics["lifecycle_health_change"],
        "trajectory_definition": RECURRENCE_PORTFOLIO_TRAJECTORY_DEFINITION,
    }
    stability_trajectory_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "trajectory_available": metrics["trajectory_available"],
        "baseline_only": metrics["baseline_only"],
        "stability_score_current": metrics["stability_score_current"],
        "stability_score_baseline": metrics["stability_score_baseline"],
        "stability_change": metrics["stability_change"],
        "recurrence_rate_current": metrics["recurrence_rate_current"],
        "recurrence_rate_baseline": metrics["recurrence_rate_baseline"],
        "recurrence_rate_change": metrics["recurrence_rate_change"],
        "trajectory_definition": RECURRENCE_STABILITY_TRAJECTORY_DEFINITION,
    }
    program_effectiveness_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "program_effectiveness_score": metrics["program_effectiveness_score"],
        "governance_effectiveness": metrics["governance_effectiveness"],
        "remediation_effectiveness": metrics["remediation_effectiveness"],
        "forecast_effectiveness": metrics["forecast_effectiveness"],
        "stability_trajectory": {
            "stability_score_current": metrics["stability_score_current"],
            "stability_change": metrics["stability_change"],
            "recurrence_rate_change": metrics["recurrence_rate_change"],
            "trajectory_available": metrics["trajectory_available"],
        },
        "effectiveness_confidence": metrics["effectiveness_confidence"],
        "recurrence_reduction_rate": metrics["recurrence_reduction_rate"],
        "forecast_accuracy": metrics["forecast_accuracy"],
        "stability_change": metrics["stability_change"],
        "program_effectiveness_score_definition": RECURRENCE_PROGRAM_EFFECTIVENESS_SCORE_DEFINITION,
        "effectiveness_confidence_definition": RECURRENCE_EFFECTIVENESS_CONFIDENCE_DEFINITION,
    }

    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "effectiveness_metrics": metrics,
        "governance_effectiveness_summary": governance_effectiveness_summary,
        "remediation_effectiveness_summary": remediation_effectiveness_summary,
        "forecast_effectiveness_summary": forecast_effectiveness_summary,
        "portfolio_trajectory_summary": portfolio_trajectory_summary,
        "stability_trajectory_summary": stability_trajectory_summary,
        "program_effectiveness_summary": program_effectiveness_summary,
    }


def enrich_recurrence_history_with_program_effectiveness(
    history: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a history payload with additive protected replay program effectiveness fields."""
    payload = dict(history)
    effectiveness = build_recurrence_program_effectiveness(
        recurrence_governance=payload.get("recurrence_governance")
        if isinstance(payload.get("recurrence_governance"), Mapping)
        else None,
        recurrence_remediation_summary=payload.get("recurrence_remediation_summary")
        if isinstance(payload.get("recurrence_remediation_summary"), Mapping)
        else None,
        recurrence_roi_summary=payload.get("recurrence_roi_summary")
        if isinstance(payload.get("recurrence_roi_summary"), Mapping)
        else None,
        recurrence_lifecycle_summary=payload.get("recurrence_lifecycle_summary")
        if isinstance(payload.get("recurrence_lifecycle_summary"), Mapping)
        else None,
        recurrence_portfolio_summary=payload.get("recurrence_portfolio_summary")
        if isinstance(payload.get("recurrence_portfolio_summary"), Mapping)
        else None,
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        recurrence_history=payload,
        recurrence_lifecycle=payload.get("recurrence_lifecycle")
        if isinstance(payload.get("recurrence_lifecycle"), Mapping)
        else None,
        recurrence_remediation_targets=payload.get("recurrence_remediation_targets")
        if isinstance(payload.get("recurrence_remediation_targets"), Mapping)
        else None,
    )
    payload["recurrence_program_effectiveness"] = effectiveness
    payload["recurrence_program_effectiveness_summary"] = effectiveness["program_effectiveness_summary"]
    payload["governance_effectiveness_summary"] = effectiveness["governance_effectiveness_summary"]
    payload["remediation_effectiveness_summary"] = effectiveness["remediation_effectiveness_summary"]
    payload["forecast_effectiveness_summary"] = effectiveness["forecast_effectiveness_summary"]
    payload["portfolio_trajectory_summary"] = effectiveness["portfolio_trajectory_summary"]
    payload["stability_trajectory_summary"] = effectiveness["stability_trajectory_summary"]
    return payload


RECURRENCE_MATURITY_TARGET_SCORE = 80.0
RECURRENCE_MATURITY_LEVEL_INITIAL = "initial"
RECURRENCE_MATURITY_LEVEL_DEVELOPING = "developing"
RECURRENCE_MATURITY_LEVEL_MANAGED = "managed"
RECURRENCE_MATURITY_LEVEL_MEASURED = "measured"
RECURRENCE_MATURITY_LEVEL_OPTIMIZED = "optimized"
RECURRENCE_MATURITY_LEVEL_THRESHOLDS: tuple[tuple[str, int, int], ...] = (
    (RECURRENCE_MATURITY_LEVEL_INITIAL, 0, 19),
    (RECURRENCE_MATURITY_LEVEL_DEVELOPING, 20, 39),
    (RECURRENCE_MATURITY_LEVEL_MANAGED, 40, 59),
    (RECURRENCE_MATURITY_LEVEL_MEASURED, 60, 79),
    (RECURRENCE_MATURITY_LEVEL_OPTIMIZED, 80, 100),
)
RECURRENCE_MATURITY_LEVEL_DEFINITION = (
    "Maturity levels map 0-100 scores to capability stages: "
    "0-19 Initial, 20-39 Developing, 40-59 Managed, 60-79 Measured, 80-100 Optimized."
)
RECURRENCE_MATURITY_DIMENSION_WEIGHTS: dict[str, float] = {
    "observability": 0.20,
    "governance": 0.15,
    "forecasting": 0.15,
    "remediation": 0.15,
    "lifecycle": 0.15,
    "operational_readiness": 0.20,
}
RECURRENCE_MATURITY_OVERALL_SCORE_DEFINITION = (
    "Advisory 0-100 weighted maturity score: "
    "20% observability + 15% governance + 15% forecasting + 15% remediation "
    "+ 15% lifecycle + 20% operational_readiness. Higher scores indicate a more "
    "mature recurrence capability independent of program outcome effectiveness."
)
RECURRENCE_MATURITY_GAP_PRIORITY_DEFINITION = (
    "Improvement priority from current_score and gap to target (80): "
    "critical when current_score < 20 or gap >= 40; high when current_score < 40 or gap >= 25; "
    "medium when gap >= 15; otherwise low."
)
RECURRENCE_MATURITY_MIN_OBSERVATIONS = RECURRENCE_PROGRAM_EFFECTIVENESS_MIN_OBSERVATIONS
RECURRENCE_MATURITY_MIN_KEYS = RECURRENCE_PROGRAM_EFFECTIVENESS_MIN_KEYS


def _clamp_maturity_score(value: float) -> float:
    return round(max(0.0, min(100.0, float(value or 0.0))), 1)


def _maturity_volume_factor(*, total_observations: int, total_keys: int) -> float:
    observations = max(int(total_observations or 0), 0)
    keys = max(int(total_keys or 0), 0)
    return min(1.0, observations / float(RECURRENCE_MATURITY_MIN_OBSERVATIONS)) * min(
        1.0, keys / float(RECURRENCE_MATURITY_MIN_KEYS)
    )


def _recurrence_maturity_level(score: float) -> str:
    bounded = round(max(0.0, min(100.0, float(score or 0.0))))
    for level, lower, upper in RECURRENCE_MATURITY_LEVEL_THRESHOLDS:
        if lower <= bounded <= upper:
            return level
    return RECURRENCE_MATURITY_LEVEL_OPTIMIZED


def _recurrence_maturity_level_label(level: str) -> str:
    return str(level or RECURRENCE_MATURITY_LEVEL_INITIAL).replace("_", " ").title()


def _maturity_dimension_result(*, score: float, confidence: float, rationale: str) -> dict[str, Any]:
    bounded_score = _clamp_maturity_score(score)
    return {
        "maturity_score": bounded_score,
        "maturity_level": _recurrence_maturity_level(bounded_score),
        "confidence": round(max(0.0, min(1.0, float(confidence or 0.0))), 2),
        "rationale": rationale,
    }


def _maturity_improvement_priority(*, current_score: float, gap: float) -> str:
    score = float(current_score or 0.0)
    gap_value = float(gap or 0.0)
    if score < 20.0 or gap_value >= 40.0:
        return "critical"
    if score < 40.0 or gap_value >= 25.0:
        return "high"
    if gap_value >= 15.0:
        return "medium"
    return "low"


def _score_observability_maturity(
    *,
    recurrence_history: Mapping[str, Any],
    recurrence_trends: Mapping[str, Any] | None,
    recurrence_forecast: Mapping[str, Any] | None,
    recurrence_portfolio: Mapping[str, Any] | None,
    recurrence_governance: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    trends = recurrence_trends if isinstance(recurrence_trends, Mapping) else {}
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    portfolio = recurrence_portfolio if isinstance(recurrence_portfolio, Mapping) else {}
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    portfolio_trajectory = effectiveness.get("portfolio_trajectory_summary")
    if not isinstance(portfolio_trajectory, Mapping):
        portfolio_trajectory = {}

    signals = {
        "recurrence_history": bool(history.get("unique_recurrence_count") or history.get("summary")),
        "trend_analytics": bool(trends) and (
            trends.get("total_keys") is not None
            or trends.get("growth_rate") is not None
            or trends.get("top_recurring_keys") is not None
        ),
        "forecasting": bool(forecast.get("key_forecasts") or forecast.get("forecast_summary")),
        "portfolio_analytics": bool(
            portfolio.get("portfolio_summary") or history.get("recurrence_portfolio_summary")
        ),
        "governance_signals": bool(governance.get("watchlist") or governance.get("governance_summary")),
        "longitudinal_measurements": bool(
            portfolio_trajectory.get("trajectory_available")
            or total_observations >= 2
            or (
                isinstance(history.get("recurrence_timeline"), list)
                and bool(history.get("recurrence_timeline"))
            )
        ),
    }
    presence_ratio = sum(1 for present in signals.values() if present) / float(len(signals))
    presence_score = presence_ratio * 70.0
    completeness_bonus = 0.0
    if history.get("recurrence_timeline"):
        completeness_bonus += 3.0
    if history.get("recurrence_roi") or history.get("recurrence_roi_summary"):
        completeness_bonus += 3.0
    if history.get("recurrence_remediation_targets") or history.get("recurrence_remediation_summary"):
        completeness_bonus += 4.0
    volume_quality = _maturity_volume_factor(
        total_observations=total_observations,
        total_keys=total_keys,
    ) * 20.0
    score = presence_score + completeness_bonus + volume_quality
    confidence = round(0.35 + 0.45 * presence_ratio + 0.20 * _maturity_volume_factor(
        total_observations=total_observations,
        total_keys=total_keys,
    ), 2)
    present_labels = [name for name, present in signals.items() if present]
    missing_labels = [name for name, present in signals.items() if not present]
    rationale = (
        f"Observability reflects analytics coverage ({len(present_labels)}/{len(signals)} signals present: "
        f"{', '.join(present_labels) or 'none'}). "
    )
    if missing_labels:
        rationale += f"Missing: {', '.join(missing_labels)}. "
    rationale += (
        f"Volume quality factor {_maturity_volume_factor(total_observations=total_observations, total_keys=total_keys):.2f} "
        f"from {total_observations} observations across {total_keys} keys."
    )
    return _maturity_dimension_result(score=score, confidence=confidence, rationale=rationale)


def _score_governance_maturity(
    *,
    recurrence_governance: Mapping[str, Any] | None,
    recurrence_history: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    governance_summary = governance.get("governance_summary")
    if not isinstance(governance_summary, Mapping):
        governance_summary = history.get("recurrence_governance_summary")
    if not isinstance(governance_summary, Mapping):
        governance_summary = {}
    watchlist = [row for row in (governance.get("watchlist") or ()) if isinstance(row, Mapping)]
    owners = [row for row in (governance.get("owners") or ()) if isinstance(row, Mapping)]
    retirement_summary = governance.get("retirement_summary")
    if not isinstance(retirement_summary, Mapping):
        retirement_summary = history.get("recurrence_retirement_summary")
    accountability = bool(watchlist) and all(
        str(row.get("governance_status") or "").strip() for row in watchlist
    )
    structure_signals = [
        bool(watchlist),
        bool(owners),
        bool(retirement_summary),
        accountability,
        bool(governance_summary.get("governance_health_score") is not None),
    ]
    structure_score = (sum(structure_signals) / float(len(structure_signals))) * 30.0
    governance_health = float(
        governance_summary.get("governance_health_score") or governance.get("governance_health_score") or 0.0
    )
    governance_confidence = float(
        governance_summary.get("governance_confidence") or governance.get("governance_confidence") or 0.0
    )
    health_score = governance_health * 0.25
    confidence_score = governance_confidence * 20.0
    score = structure_score + health_score + confidence_score
    confidence = round(0.40 * governance_confidence + 0.35 * (sum(structure_signals) / len(structure_signals)) + 0.25 * _maturity_volume_factor(
        total_observations=total_observations,
        total_keys=total_keys,
    ), 2)
    rationale = (
        f"Governance maturity from watchlist/ownership/retirement structures "
        f"({sum(structure_signals)}/{len(structure_signals)} present), "
        f"governance_health_score {governance_health:.1f}, "
        f"and governance_confidence {governance_confidence:.2f}."
    )
    return _maturity_dimension_result(score=score, confidence=confidence, rationale=rationale)


def _score_forecasting_maturity(
    *,
    recurrence_forecast: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    metrics = effectiveness.get("effectiveness_metrics")
    if not isinstance(metrics, Mapping):
        metrics = {}
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    key_forecasts = [row for row in (forecast.get("key_forecasts") or ()) if isinstance(row, Mapping)]
    forecast_confidence = float(
        forecast_summary.get("forecast_confidence") or metrics.get("forecast_confidence") or 0.0
    )
    forecast_accuracy = float(metrics.get("forecast_accuracy") or 0.0)
    availability_score = 20.0 if key_forecasts else 0.0
    confidence_score = forecast_confidence * 35.0
    validation_score = 15.0 if key_forecasts else 0.0
    accuracy_score = forecast_accuracy * forecast_confidence * 40.0
    raw_score = availability_score + confidence_score + validation_score + accuracy_score
    volume_scale = max(0.45, _maturity_volume_factor(total_observations=total_observations, total_keys=total_keys))
    score = raw_score * volume_scale
    confidence = round(0.50 * forecast_confidence + 0.30 * (1.0 if key_forecasts else 0.0) + 0.20 * volume_scale, 2)
    rationale = (
        f"Forecasting maturity from model availability ({len(key_forecasts)} key forecasts), "
        f"forecast_confidence {forecast_confidence:.2f}, "
        f"confidence-weighted accuracy {forecast_accuracy * forecast_confidence:.2f}, "
        f"scaled by volume factor {volume_scale:.2f}."
    )
    return _maturity_dimension_result(score=score, confidence=confidence, rationale=rationale)


def _score_remediation_maturity(
    *,
    recurrence_remediation: Mapping[str, Any] | None,
    recurrence_roi: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    remediation = recurrence_remediation if isinstance(recurrence_remediation, Mapping) else {}
    roi = recurrence_roi if isinstance(recurrence_roi, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    metrics = effectiveness.get("effectiveness_metrics")
    if not isinstance(metrics, Mapping):
        metrics = {}
    remediation_summary = remediation.get("remediation_summary")
    if not isinstance(remediation_summary, Mapping):
        remediation_summary = {}
    roi_summary = roi.get("roi_summary")
    if not isinstance(roi_summary, Mapping):
        roi_summary = {}
    remediation_keys = [row for row in (remediation.get("keys") or ()) if isinstance(row, Mapping)]
    targeting_score = 20.0 if remediation_keys else (10.0 if remediation_summary else 0.0)
    roi_score = 20.0 if roi_summary else 0.0
    reduction_rate = float(metrics.get("recurrence_reduction_rate") or 0.0)
    remediation_effectiveness = float(metrics.get("remediation_effectiveness") or 0.0)
    remediation_confidence = float(remediation_summary.get("remediation_confidence") or 0.0)
    outcome_score = reduction_rate * 25.0 + remediation_effectiveness * 25.0
    structure_score = targeting_score + roi_score
    volume_scale = 0.55 + 0.45 * _maturity_volume_factor(
        total_observations=total_observations,
        total_keys=total_keys,
    )
    score = (structure_score + outcome_score) * volume_scale + remediation_confidence * 15.0
    confidence = round(
        0.35 * remediation_confidence
        + 0.35 * (1.0 if remediation_keys else 0.5 if remediation_summary else 0.0)
        + 0.30 * _maturity_volume_factor(total_observations=total_observations, total_keys=total_keys),
        2,
    )
    rationale = (
        f"Remediation maturity from targeting/ROI structures "
        f"({'present' if structure_score >= 30 else 'partial' if structure_score else 'absent'}), "
        f"recurrence_reduction_rate {reduction_rate:.2f}, remediation_effectiveness "
        f"{remediation_effectiveness:.2f}, remediation_confidence {remediation_confidence:.2f}."
    )
    return _maturity_dimension_result(score=score, confidence=confidence, rationale=rationale)


def _score_lifecycle_maturity(
    *,
    recurrence_lifecycle: Mapping[str, Any] | None,
    recurrence_history: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    lifecycle = recurrence_lifecycle if isinstance(recurrence_lifecycle, Mapping) else {}
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    lifecycle_summary = lifecycle.get("lifecycle_summary")
    if not isinstance(lifecycle_summary, Mapping):
        lifecycle_summary = history.get("recurrence_lifecycle_summary")
    if not isinstance(lifecycle_summary, Mapping):
        lifecycle_summary = {}
    lifecycle_keys = [row for row in (lifecycle.get("keys") or ()) if isinstance(row, Mapping)]
    transition_summary = lifecycle.get("transition_summary")
    if not isinstance(transition_summary, Mapping):
        transition_summary = history.get("recurrence_transition_summary")
    age_distribution = lifecycle.get("age_distribution")
    if not isinstance(age_distribution, Mapping):
        age_distribution = history.get("recurrence_age_distribution")
    lifecycle_health = float(
        lifecycle_summary.get("lifecycle_health_score") or lifecycle.get("lifecycle_health_score") or 0.0
    )
    tracking_score = 15.0 if lifecycle_keys else 0.0
    transition_score = 10.0 if isinstance(transition_summary, Mapping) else 0.0
    age_score = 10.0 if isinstance(age_distribution, Mapping) else 0.0
    health_score = lifecycle_health * 0.25
    score = tracking_score + transition_score + age_score + health_score
    confidence = round(
        0.40 * (1.0 if lifecycle_keys else 0.0)
        + 0.30 * (1.0 if isinstance(transition_summary, Mapping) else 0.0)
        + 0.30 * _maturity_volume_factor(total_observations=total_observations, total_keys=total_keys),
        2,
    )
    rationale = (
        f"Lifecycle maturity from lifecycle tracking ({len(lifecycle_keys)} keys), "
        f"transition_summary {'present' if isinstance(transition_summary, Mapping) else 'absent'}, "
        f"age_distribution {'present' if isinstance(age_distribution, Mapping) else 'absent'}, "
        f"and lifecycle_health_score {lifecycle_health:.1f}."
    )
    return _maturity_dimension_result(score=score, confidence=confidence, rationale=rationale)


def _score_operational_readiness_maturity(
    *,
    recurrence_governance: Mapping[str, Any] | None,
    recurrence_forecast: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    total_observations: int,
    total_keys: int,
) -> dict[str, Any]:
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    program_summary = effectiveness.get("program_effectiveness_summary")
    if not isinstance(program_summary, Mapping):
        program_summary = {}
    portfolio_trajectory = effectiveness.get("portfolio_trajectory_summary")
    if not isinstance(portfolio_trajectory, Mapping):
        portfolio_trajectory = {}
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    governance_summary = governance.get("governance_summary")
    if not isinstance(governance_summary, Mapping):
        governance_summary = {}
    governance_confidence = float(
        governance_summary.get("governance_confidence") or governance.get("governance_confidence") or 0.0
    )
    effectiveness_confidence = float(program_summary.get("effectiveness_confidence") or 0.0)
    forecast_confidence = float(forecast_summary.get("forecast_confidence") or 0.0)
    trajectory_available = bool(portfolio_trajectory.get("trajectory_available"))
    volume_factor = _maturity_volume_factor(total_observations=total_observations, total_keys=total_keys)
    score = (
        governance_confidence * 20.0
        + effectiveness_confidence * 20.0
        + forecast_confidence * 20.0
        + (20.0 if trajectory_available else 0.0)
        + volume_factor * 20.0
    )
    confidence = round(
        0.30 * governance_confidence
        + 0.30 * effectiveness_confidence
        + 0.20 * forecast_confidence
        + 0.20 * volume_factor,
        2,
    )
    rationale = (
        f"Operational readiness from governance_confidence {governance_confidence:.2f}, "
        f"effectiveness_confidence {effectiveness_confidence:.2f}, "
        f"forecast_confidence {forecast_confidence:.2f}, "
        f"trajectory_available {str(trajectory_available).lower()}, "
        f"and data sufficiency factor {volume_factor:.2f}."
    )
    return _maturity_dimension_result(score=score, confidence=confidence, rationale=rationale)


def calculate_recurrence_maturity_score(
    *,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_trends: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_portfolio: Mapping[str, Any] | None = None,
    recurrence_remediation: Mapping[str, Any] | None = None,
    recurrence_roi: Mapping[str, Any] | None = None,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate protected replay recurrence maturity dimension scores."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    trends = recurrence_trends if isinstance(recurrence_trends, Mapping) else {}
    if not trends and isinstance(history.get("recurrence_trends"), Mapping):
        trends = history["recurrence_trends"]
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    if not forecast and isinstance(history.get("recurrence_forecast"), Mapping):
        forecast = history["recurrence_forecast"]
    portfolio = recurrence_portfolio if isinstance(recurrence_portfolio, Mapping) else {}
    if not portfolio and isinstance(history.get("recurrence_portfolio"), Mapping):
        portfolio = history["recurrence_portfolio"]
    remediation = recurrence_remediation if isinstance(recurrence_remediation, Mapping) else {}
    if not remediation and isinstance(history.get("recurrence_remediation_targets"), Mapping):
        remediation = history["recurrence_remediation_targets"]
    roi = recurrence_roi if isinstance(recurrence_roi, Mapping) else {}
    if not roi and isinstance(history.get("recurrence_roi"), Mapping):
        roi = history["recurrence_roi"]
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    if not governance and isinstance(history.get("recurrence_governance"), Mapping):
        governance = history["recurrence_governance"]
    lifecycle = recurrence_lifecycle if isinstance(recurrence_lifecycle, Mapping) else {}
    if not lifecycle and isinstance(history.get("recurrence_lifecycle"), Mapping):
        lifecycle = history["recurrence_lifecycle"]
    program_effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    if not program_effectiveness and isinstance(history.get("recurrence_program_effectiveness"), Mapping):
        program_effectiveness = history["recurrence_program_effectiveness"]

    total_keys = int(
        history.get("unique_recurrence_count")
        or (lifecycle.get("lifecycle_summary") or {}).get("active_keys")
        or len(lifecycle.get("keys") or ())
        or 0
    )
    total_observations = int(history.get("total_rows") or remediation.get("total_observations") or 0)

    observability = _score_observability_maturity(
        recurrence_history=history,
        recurrence_trends=trends,
        recurrence_forecast=forecast,
        recurrence_portfolio=portfolio,
        recurrence_governance=governance,
        recurrence_program_effectiveness=program_effectiveness,
        total_observations=total_observations,
        total_keys=total_keys,
    )
    governance_maturity = _score_governance_maturity(
        recurrence_governance=governance,
        recurrence_history=history,
        total_observations=total_observations,
        total_keys=total_keys,
    )
    forecasting = _score_forecasting_maturity(
        recurrence_forecast=forecast,
        recurrence_program_effectiveness=program_effectiveness,
        total_observations=total_observations,
        total_keys=total_keys,
    )
    remediation_maturity = _score_remediation_maturity(
        recurrence_remediation=remediation,
        recurrence_roi=roi,
        recurrence_program_effectiveness=program_effectiveness,
        total_observations=total_observations,
        total_keys=total_keys,
    )
    lifecycle_maturity = _score_lifecycle_maturity(
        recurrence_lifecycle=lifecycle,
        recurrence_history=history,
        total_observations=total_observations,
        total_keys=total_keys,
    )
    operational_readiness = _score_operational_readiness_maturity(
        recurrence_governance=governance,
        recurrence_forecast=forecast,
        recurrence_program_effectiveness=program_effectiveness,
        total_observations=total_observations,
        total_keys=total_keys,
    )

    dimension_scores = {
        "observability": observability["maturity_score"],
        "governance": governance_maturity["maturity_score"],
        "forecasting": forecasting["maturity_score"],
        "remediation": remediation_maturity["maturity_score"],
        "lifecycle": lifecycle_maturity["maturity_score"],
        "operational_readiness": operational_readiness["maturity_score"],
    }
    overall_maturity_score = round(
        sum(
            float(dimension_scores[name]) * RECURRENCE_MATURITY_DIMENSION_WEIGHTS[name]
            for name in RECURRENCE_MATURITY_DIMENSION_WEIGHTS
        ),
        1,
    )

    return {
        "total_keys": total_keys,
        "total_observations": total_observations,
        "dimension_scores": dimension_scores,
        "overall_maturity_score": _clamp_maturity_score(overall_maturity_score),
        "observability_maturity": observability,
        "governance_maturity": governance_maturity,
        "forecasting_maturity": forecasting,
        "remediation_maturity": remediation_maturity,
        "lifecycle_maturity": lifecycle_maturity,
        "operational_readiness": operational_readiness,
    }


def _build_maturity_gap_analysis(dimension_scores: Mapping[str, float]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for dimension, current_score in dimension_scores.items():
        current = float(current_score or 0.0)
        target = RECURRENCE_MATURITY_TARGET_SCORE
        gap = round(max(0.0, target - current), 1)
        gaps.append(
            {
                "dimension": dimension,
                "current_score": round(current, 1),
                "target_score": target,
                "gap": gap,
                "improvement_priority": _maturity_improvement_priority(
                    current_score=current,
                    gap=gap,
                ),
            }
        )
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    gaps.sort(key=lambda row: (priority_order.get(str(row["improvement_priority"]), 9), -float(row["gap"])))
    return gaps


def summarize_recurrence_maturity(
    maturity: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence maturity scores."""
    source = maturity if isinstance(maturity, Mapping) else {}
    summary = source.get("recurrence_maturity_summary")
    if isinstance(summary, Mapping):
        return dict(summary)
    maturity_scores = source.get("maturity_scores")
    if not isinstance(maturity_scores, Mapping):
        maturity_scores = calculate_recurrence_maturity_score()
    dimension_scores = maturity_scores.get("dimension_scores")
    if not isinstance(dimension_scores, Mapping):
        dimension_scores = {}
    overall_score = float(
        maturity_scores.get("overall_maturity_score")
        or source.get("overall_maturity_score")
        or 0.0
    )
    if not dimension_scores:
        dimension_scores = {
            "observability": 0.0,
            "governance": 0.0,
            "forecasting": 0.0,
            "remediation": 0.0,
            "lifecycle": 0.0,
            "operational_readiness": 0.0,
        }
    highest_dimension = max(dimension_scores, key=lambda name: float(dimension_scores[name] or 0.0))
    lowest_dimension = min(dimension_scores, key=lambda name: float(dimension_scores[name] or 0.0))
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "overall_maturity_score": _clamp_maturity_score(overall_score),
        "overall_maturity_level": _recurrence_maturity_level(overall_score),
        "observability_score": float(dimension_scores.get("observability") or 0.0),
        "governance_score": float(dimension_scores.get("governance") or 0.0),
        "forecasting_score": float(dimension_scores.get("forecasting") or 0.0),
        "remediation_score": float(dimension_scores.get("remediation") or 0.0),
        "lifecycle_score": float(dimension_scores.get("lifecycle") or 0.0),
        "operational_readiness_score": float(dimension_scores.get("operational_readiness") or 0.0),
        "highest_dimension": highest_dimension,
        "lowest_dimension": lowest_dimension,
        "maturity_level_definition": RECURRENCE_MATURITY_LEVEL_DEFINITION,
        "overall_maturity_score_definition": RECURRENCE_MATURITY_OVERALL_SCORE_DEFINITION,
    }


def build_recurrence_maturity_assessment(
    *,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_trends: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_portfolio: Mapping[str, Any] | None = None,
    recurrence_remediation: Mapping[str, Any] | None = None,
    recurrence_roi: Mapping[str, Any] | None = None,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence maturity assessment analytics."""
    maturity_scores = calculate_recurrence_maturity_score(
        recurrence_history=recurrence_history,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_remediation=recurrence_remediation,
        recurrence_roi=recurrence_roi,
        recurrence_governance=recurrence_governance,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
    )
    gap_analysis = _build_maturity_gap_analysis(maturity_scores["dimension_scores"])
    maturity_without_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "maturity_scores": maturity_scores,
        "observability_maturity": maturity_scores["observability_maturity"],
        "governance_maturity": maturity_scores["governance_maturity"],
        "forecasting_maturity": maturity_scores["forecasting_maturity"],
        "remediation_maturity": maturity_scores["remediation_maturity"],
        "lifecycle_maturity": maturity_scores["lifecycle_maturity"],
        "operational_readiness": maturity_scores["operational_readiness"],
        "maturity_gap_analysis": gap_analysis,
        "maturity_level_definition": RECURRENCE_MATURITY_LEVEL_DEFINITION,
        "overall_maturity_score_definition": RECURRENCE_MATURITY_OVERALL_SCORE_DEFINITION,
        "maturity_gap_priority_definition": RECURRENCE_MATURITY_GAP_PRIORITY_DEFINITION,
        "dimension_weights": dict(RECURRENCE_MATURITY_DIMENSION_WEIGHTS),
    }
    recurrence_maturity_summary = summarize_recurrence_maturity(maturity_without_summary)
    return {
        **maturity_without_summary,
        "recurrence_maturity_summary": recurrence_maturity_summary,
    }


def enrich_recurrence_history_with_maturity(
    history: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a history payload with additive protected replay maturity fields."""
    payload = dict(history)
    maturity = build_recurrence_maturity_assessment(
        recurrence_history=payload,
        recurrence_trends=payload.get("recurrence_trends")
        if isinstance(payload.get("recurrence_trends"), Mapping)
        else None,
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        recurrence_portfolio=payload.get("recurrence_portfolio")
        if isinstance(payload.get("recurrence_portfolio"), Mapping)
        else None,
        recurrence_remediation=payload.get("recurrence_remediation_targets")
        if isinstance(payload.get("recurrence_remediation_targets"), Mapping)
        else None,
        recurrence_roi=payload.get("recurrence_roi")
        if isinstance(payload.get("recurrence_roi"), Mapping)
        else None,
        recurrence_governance=payload.get("recurrence_governance")
        if isinstance(payload.get("recurrence_governance"), Mapping)
        else None,
        recurrence_lifecycle=payload.get("recurrence_lifecycle")
        if isinstance(payload.get("recurrence_lifecycle"), Mapping)
        else None,
        recurrence_program_effectiveness=payload.get("recurrence_program_effectiveness")
        if isinstance(payload.get("recurrence_program_effectiveness"), Mapping)
        else None,
    )
    payload["recurrence_maturity"] = maturity
    payload["recurrence_maturity_summary"] = maturity["recurrence_maturity_summary"]
    payload["recurrence_maturity_gap_analysis"] = maturity["maturity_gap_analysis"]
    return payload


RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME = "data_volume_expansion"
RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY = "trajectory_establishment"
RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION = "forecast_validation"
RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE = "lifecycle_closure_tracking"
RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK = "remediation_feedback_loop"
RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION = "operationalization"
RECURRENCE_ROADMAP_INITIATIVES: tuple[str, ...] = (
    RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY,
    RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION,
    RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE,
    RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK,
    RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION,
)
RECURRENCE_ROADMAP_DEFAULT_SEQUENCE: tuple[str, ...] = RECURRENCE_ROADMAP_INITIATIVES
RECURRENCE_ROADMAP_INITIATIVE_LABELS: dict[str, str] = {
    RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME: "Data Volume Expansion",
    RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY: "Trajectory Establishment",
    RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION: "Forecast Validation",
    RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE: "Lifecycle Closure Tracking",
    RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK: "Remediation Feedback Loop",
    RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION: "Operationalization",
}
RECURRENCE_ROADMAP_INITIATIVE_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME: (),
    RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY: (RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,),
    RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION: (
        RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
        RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY,
    ),
    RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE: (RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY,),
    RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK: (
        RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION,
        RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE,
    ),
    RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION: (
        RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK,
    ),
}
RECURRENCE_ROADMAP_INITIATIVE_BASE_COMPLEXITY: dict[str, float] = {
    RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME: 12.0,
    RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY: 22.0,
    RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION: 28.0,
    RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE: 24.0,
    RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK: 32.0,
    RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION: 35.0,
}
RECURRENCE_ROADMAP_INITIATIVE_DIMENSION_DELTAS: dict[str, dict[str, float]] = {
    RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME: {
        "observability": 8.0,
        "governance": 12.0,
        "forecasting": 18.0,
        "remediation": 15.0,
        "lifecycle": 8.0,
        "operational_readiness": 28.0,
    },
    RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY: {
        "observability": 5.0,
        "governance": 6.0,
        "forecasting": 8.0,
        "remediation": 4.0,
        "lifecycle": 6.0,
        "operational_readiness": 20.0,
    },
    RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION: {
        "observability": 2.0,
        "governance": 4.0,
        "forecasting": 25.0,
        "remediation": 6.0,
        "lifecycle": 4.0,
        "operational_readiness": 8.0,
    },
    RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE: {
        "observability": 2.0,
        "governance": 5.0,
        "forecasting": 4.0,
        "remediation": 6.0,
        "lifecycle": 25.0,
        "operational_readiness": 6.0,
    },
    RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK: {
        "observability": 2.0,
        "governance": 6.0,
        "forecasting": 5.0,
        "remediation": 30.0,
        "lifecycle": 8.0,
        "operational_readiness": 10.0,
    },
    RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION: {
        "observability": 4.0,
        "governance": 8.0,
        "forecasting": 6.0,
        "remediation": 8.0,
        "lifecycle": 6.0,
        "operational_readiness": 20.0,
    },
}
RECURRENCE_ROADMAP_MATURITY_ROI_DEFINITION = (
    "Advisory 0-100 maturity ROI: 100 * (expected_maturity_gain / implementation_complexity) "
    "/ max_initiative_raw_roi, where expected_maturity_gain is the weighted sum of projected "
    "dimension deltas using recurrence maturity dimension weights and implementation_complexity "
    "is base complexity plus 5 per dependency. Higher values indicate better maturity return "
    "per unit implementation effort."
)
RECURRENCE_ROADMAP_INVESTMENT_PRIORITY_DEFINITION = (
    "Advisory 0-100 investment priority blends maturity ROI (45%), gap alignment (35%), "
    "and readiness impact (20%). Gap alignment weights initiative dimension deltas against "
    "current maturity gap analysis; readiness impact favors initiatives that unlock "
    "downstream dependencies when volume or trajectory prerequisites are unmet."
)
RECURRENCE_ROADMAP_TARGET_STATE_DEFINITION = (
    "Optimized recurrence target state requires all maturity dimensions >= 80, "
    "operational_readiness >= 80, forecast_confidence >= 0.75, effectiveness_confidence >= 0.75, "
    "trajectory_available=true, measurable closure effectiveness, and measurable remediation "
    "effectiveness. Completion criteria are explicit boolean checks against these thresholds."
)
RECURRENCE_ROADMAP_TARGET_FORECAST_CONFIDENCE = 0.75
RECURRENCE_ROADMAP_TARGET_EFFECTIVENESS_CONFIDENCE = 0.75
RECURRENCE_ROADMAP_LOW_VOLUME_GUIDANCE = (
    "Collect more protected replay observations before optimizing models."
)


def _roadmap_dimension_scores_from_summary(
    maturity_summary: Mapping[str, Any] | None,
) -> dict[str, float]:
    summary = maturity_summary if isinstance(maturity_summary, Mapping) else {}
    return {
        "observability": float(summary.get("observability_score") or 0.0),
        "governance": float(summary.get("governance_score") or 0.0),
        "forecasting": float(summary.get("forecasting_score") or 0.0),
        "remediation": float(summary.get("remediation_score") or 0.0),
        "lifecycle": float(summary.get("lifecycle_score") or 0.0),
        "operational_readiness": float(summary.get("operational_readiness_score") or 0.0),
    }


def _roadmap_weighted_overall_maturity(dimension_scores: Mapping[str, float]) -> float:
    return round(
        sum(
            float(dimension_scores.get(name) or 0.0) * RECURRENCE_MATURITY_DIMENSION_WEIGHTS[name]
            for name in RECURRENCE_MATURITY_DIMENSION_WEIGHTS
        ),
        1,
    )


def _roadmap_projected_dimension_scores(
    current_scores: Mapping[str, float],
    deltas: Mapping[str, float],
) -> dict[str, float]:
    projected: dict[str, float] = {}
    for dimension in RECURRENCE_MATURITY_DIMENSION_WEIGHTS:
        projected[dimension] = _clamp_maturity_score(
            float(current_scores.get(dimension) or 0.0) + float(deltas.get(dimension) or 0.0)
        )
    return projected


def _roadmap_expected_maturity_gain(dimension_deltas: Mapping[str, float]) -> float:
    return round(
        sum(
            float(dimension_deltas.get(name) or 0.0) * RECURRENCE_MATURITY_DIMENSION_WEIGHTS[name]
            for name in RECURRENCE_MATURITY_DIMENSION_WEIGHTS
        ),
        2,
    )


def _roadmap_implementation_complexity(initiative_id: str) -> float:
    dependencies = RECURRENCE_ROADMAP_INITIATIVE_DEPENDENCIES.get(initiative_id, ())
    base = float(RECURRENCE_ROADMAP_INITIATIVE_BASE_COMPLEXITY.get(initiative_id) or 20.0)
    return round(base + 5.0 * len(dependencies), 1)


def _roadmap_gap_by_dimension(
    gap_analysis: Sequence[Mapping[str, Any]] | None,
) -> dict[str, float]:
    gaps: dict[str, float] = {}
    for row in gap_analysis or ():
        if not isinstance(row, Mapping):
            continue
        dimension = str(row.get("dimension") or "").strip()
        if dimension:
            gaps[dimension] = float(row.get("gap") or 0.0)
    return gaps


def _roadmap_volume_deficiency(
    *,
    total_observations: int,
    total_keys: int,
) -> float:
    volume_factor = _maturity_volume_factor(
        total_observations=total_observations,
        total_keys=total_keys,
    )
    return round(max(0.0, 1.0 - volume_factor), 2)


def _roadmap_initiative_completion_status(
    initiative_id: str,
    *,
    total_observations: int,
    total_keys: int,
    trajectory_available: bool,
    forecast_confidence: float,
    effectiveness_confidence: float,
    operational_readiness_score: float,
    lifecycle_score: float,
    remediation_score: float,
    closure_measurable: bool,
    remediation_measurable: bool,
) -> bool:
    if initiative_id == RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME:
        return (
            total_observations >= RECURRENCE_MATURITY_MIN_OBSERVATIONS
            and total_keys >= RECURRENCE_MATURITY_MIN_KEYS
        )
    if initiative_id == RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY:
        return trajectory_available
    if initiative_id == RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION:
        return forecast_confidence >= RECURRENCE_ROADMAP_TARGET_FORECAST_CONFIDENCE
    if initiative_id == RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE:
        return lifecycle_score >= RECURRENCE_MATURITY_TARGET_SCORE and closure_measurable
    if initiative_id == RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK:
        return remediation_score >= RECURRENCE_MATURITY_TARGET_SCORE and remediation_measurable
    if initiative_id == RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION:
        return operational_readiness_score >= RECURRENCE_MATURITY_TARGET_SCORE
    return False


def calculate_maturity_investment_priority(
    *,
    initiative_id: str,
    recurrence_maturity_summary: Mapping[str, Any] | None = None,
    recurrence_maturity_gap_analysis: Sequence[Mapping[str, Any]] | None = None,
    recurrence_program_effectiveness_summary: Mapping[str, Any] | None = None,
    recurrence_portfolio_summary: Mapping[str, Any] | None = None,
    recurrence_forecast_summary: Mapping[str, Any] | None = None,
    recurrence_lifecycle_summary: Mapping[str, Any] | None = None,
    maturity_roi: float | None = None,
    dependency_count: int | None = None,
) -> dict[str, Any]:
    """Calculate protected replay maturity investment priority for one initiative."""
    initiative = str(initiative_id or "").strip()
    summary = recurrence_maturity_summary if isinstance(recurrence_maturity_summary, Mapping) else {}
    gaps = _roadmap_gap_by_dimension(recurrence_maturity_gap_analysis)
    program_summary = (
        recurrence_program_effectiveness_summary
        if isinstance(recurrence_program_effectiveness_summary, Mapping)
        else {}
    )
    portfolio_summary = recurrence_portfolio_summary if isinstance(recurrence_portfolio_summary, Mapping) else {}
    forecast_summary = recurrence_forecast_summary if isinstance(recurrence_forecast_summary, Mapping) else {}
    lifecycle_summary = recurrence_lifecycle_summary if isinstance(recurrence_lifecycle_summary, Mapping) else {}

    dimension_deltas = RECURRENCE_ROADMAP_INITIATIVE_DIMENSION_DELTAS.get(initiative, {})
    gap_alignment = 0.0
    if gaps and dimension_deltas:
        alignment_total = 0.0
        weight_total = 0.0
        for dimension, delta in dimension_deltas.items():
            gap = float(gaps.get(dimension) or 0.0)
            weight = RECURRENCE_MATURITY_DIMENSION_WEIGHTS.get(dimension, 0.0)
            alignment_total += min(gap, float(delta)) * weight
            weight_total += gap * weight
        gap_alignment = alignment_total / weight_total if weight_total > 0 else 0.0
    volume_deficiency = _roadmap_volume_deficiency(
        total_observations=int(program_summary.get("total_observations") or portfolio_summary.get("total_observations") or 0),
        total_keys=int(summary.get("unique_recurrence_count") or portfolio_summary.get("total_keys") or 0),
    )
    readiness_impact = 0.0
    if initiative == RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME:
        readiness_impact = volume_deficiency
    elif initiative == RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY:
        readiness_impact = 0.7 if volume_deficiency < 0.5 else 0.3
    elif initiative == RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION:
        readiness_impact = float(summary.get("operational_readiness_score") or 0.0) / 100.0
    else:
        readiness_impact = min(
            1.0,
            float(forecast_summary.get("forecast_confidence") or 0.0)
            + float(lifecycle_summary.get("closure_rate") or 0.0),
        ) / 2.0
    roi_component = float(maturity_roi or 0.0) / 100.0
    investment_priority_score = round(
        100.0 * (0.45 * roi_component + 0.35 * gap_alignment + 0.20 * readiness_impact),
        1,
    )
    return {
        "initiative_id": initiative,
        "initiative_label": RECURRENCE_ROADMAP_INITIATIVE_LABELS.get(initiative, initiative),
        "investment_priority_score": investment_priority_score,
        "gap_alignment": round(gap_alignment, 2),
        "readiness_impact": round(readiness_impact, 2),
        "maturity_roi": round(float(maturity_roi or 0.0), 1),
        "dependency_count": int(dependency_count or len(RECURRENCE_ROADMAP_INITIATIVE_DEPENDENCIES.get(initiative, ()))),
        "investment_priority_definition": RECURRENCE_ROADMAP_INVESTMENT_PRIORITY_DEFINITION,
    }


def _build_recurrence_target_state(
    *,
    maturity_summary: Mapping[str, Any] | None,
    program_summary: Mapping[str, Any] | None,
    forecast_summary: Mapping[str, Any] | None,
    lifecycle_summary: Mapping[str, Any] | None,
    remediation_summary: Mapping[str, Any] | None,
    portfolio_trajectory: Mapping[str, Any] | None,
) -> dict[str, Any]:
    summary = maturity_summary if isinstance(maturity_summary, Mapping) else {}
    program = program_summary if isinstance(program_summary, Mapping) else {}
    forecast = forecast_summary if isinstance(forecast_summary, Mapping) else {}
    lifecycle = lifecycle_summary if isinstance(lifecycle_summary, Mapping) else {}
    remediation = remediation_summary if isinstance(remediation_summary, Mapping) else {}
    trajectory = portfolio_trajectory if isinstance(portfolio_trajectory, Mapping) else {}
    dimension_scores = _roadmap_dimension_scores_from_summary(summary)
    forecast_confidence = float(forecast.get("forecast_confidence") or 0.0)
    effectiveness_confidence = float(program.get("effectiveness_confidence") or 0.0)
    closure_measurable = "closure_rate" in lifecycle or bool(lifecycle.get("closure_rate_definition"))
    remediation_measurable = remediation.get("remediation_effectiveness") is not None or bool(
        remediation.get("effectiveness_definition")
    )
    completion_criteria = {
        "all_dimensions_optimized": all(
            float(dimension_scores.get(name) or 0.0) >= RECURRENCE_MATURITY_TARGET_SCORE
            for name in RECURRENCE_MATURITY_DIMENSION_WEIGHTS
        ),
        "operational_readiness_optimized": float(summary.get("operational_readiness_score") or 0.0)
        >= RECURRENCE_MATURITY_TARGET_SCORE,
        "forecast_confidence_target_met": forecast_confidence >= RECURRENCE_ROADMAP_TARGET_FORECAST_CONFIDENCE,
        "effectiveness_confidence_target_met": effectiveness_confidence
        >= RECURRENCE_ROADMAP_TARGET_EFFECTIVENESS_CONFIDENCE,
        "trajectory_available": bool(trajectory.get("trajectory_available")),
        "closure_effectiveness_measurable": closure_measurable,
        "remediation_effectiveness_measurable": remediation_measurable,
    }
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "target_maturity_level": RECURRENCE_MATURITY_LEVEL_OPTIMIZED,
        "dimension_targets": {
            name: RECURRENCE_MATURITY_TARGET_SCORE for name in RECURRENCE_MATURITY_DIMENSION_WEIGHTS
        },
        "forecast_confidence_target": RECURRENCE_ROADMAP_TARGET_FORECAST_CONFIDENCE,
        "effectiveness_confidence_target": RECURRENCE_ROADMAP_TARGET_EFFECTIVENESS_CONFIDENCE,
        "trajectory_required": True,
        "closure_effectiveness_measurable": True,
        "remediation_effectiveness_measurable": True,
        "completion_criteria": completion_criteria,
        "completion_criteria_met": all(completion_criteria.values()),
        "completion_criteria_definition": RECURRENCE_ROADMAP_TARGET_STATE_DEFINITION,
    }


def _build_roadmap_sequence(
    initiatives: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {
        str(row.get("initiative_id") or ""): row for row in initiatives if isinstance(row, Mapping)
    }
    sequence: list[dict[str, Any]] = []
    for step, initiative_id in enumerate(RECURRENCE_ROADMAP_DEFAULT_SEQUENCE, start=1):
        row = dict(by_id.get(initiative_id) or {})
        if not row:
            continue
        sequence.append(
            {
                "sequence_step": step,
                "initiative_id": initiative_id,
                "initiative_label": RECURRENCE_ROADMAP_INITIATIVE_LABELS.get(initiative_id, initiative_id),
                "dependency_count": int(row.get("dependency_count") or 0),
                "dependencies": list(RECURRENCE_ROADMAP_INITIATIVE_DEPENDENCIES.get(initiative_id, ())),
                "completed": bool(row.get("completed")),
                "investment_priority_score": float(row.get("investment_priority_score") or 0.0),
                "maturity_roi": float(row.get("maturity_roi") or 0.0),
            }
        )
    return sequence


def build_recurrence_strategic_roadmap(
    *,
    recurrence_maturity_summary: Mapping[str, Any] | None = None,
    recurrence_maturity_gap_analysis: Sequence[Mapping[str, Any]] | None = None,
    recurrence_program_effectiveness_summary: Mapping[str, Any] | None = None,
    recurrence_portfolio_summary: Mapping[str, Any] | None = None,
    recurrence_forecast_summary: Mapping[str, Any] | None = None,
    recurrence_lifecycle_summary: Mapping[str, Any] | None = None,
    recurrence_remediation_effectiveness_summary: Mapping[str, Any] | None = None,
    portfolio_trajectory_summary: Mapping[str, Any] | None = None,
    total_observations: int | None = None,
    total_keys: int | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence strategic roadmap analytics."""
    maturity_summary = recurrence_maturity_summary if isinstance(recurrence_maturity_summary, Mapping) else {}
    gap_analysis = [
        dict(row) for row in (recurrence_maturity_gap_analysis or ()) if isinstance(row, Mapping)
    ]
    program_summary = (
        recurrence_program_effectiveness_summary
        if isinstance(recurrence_program_effectiveness_summary, Mapping)
        else {}
    )
    portfolio_summary = recurrence_portfolio_summary if isinstance(recurrence_portfolio_summary, Mapping) else {}
    forecast_summary = recurrence_forecast_summary if isinstance(recurrence_forecast_summary, Mapping) else {}
    lifecycle_summary = recurrence_lifecycle_summary if isinstance(recurrence_lifecycle_summary, Mapping) else {}
    remediation_summary = (
        recurrence_remediation_effectiveness_summary
        if isinstance(recurrence_remediation_effectiveness_summary, Mapping)
        else {}
    )
    portfolio_trajectory = portfolio_trajectory_summary if isinstance(portfolio_trajectory_summary, Mapping) else {}

    current_scores = _roadmap_dimension_scores_from_summary(maturity_summary)
    current_overall = _roadmap_weighted_overall_maturity(current_scores)
    observations = int(
        total_observations
        or program_summary.get("total_observations")
        or portfolio_summary.get("total_observations")
        or 0
    )
    keys = int(total_keys or maturity_summary.get("unique_recurrence_count") or portfolio_summary.get("total_keys") or 0)
    trajectory_available = bool(portfolio_trajectory.get("trajectory_available"))
    forecast_confidence = float(
        forecast_summary.get("forecast_confidence") or portfolio_summary.get("forecast_confidence") or 0.0
    )
    effectiveness_confidence = float(program_summary.get("effectiveness_confidence") or 0.0)
    volume_deficiency = _roadmap_volume_deficiency(total_observations=observations, total_keys=keys)

    initiative_rows: list[dict[str, Any]] = []
    raw_rois: dict[str, float] = {}
    for initiative_id in RECURRENCE_ROADMAP_INITIATIVES:
        base_deltas = dict(RECURRENCE_ROADMAP_INITIATIVE_DIMENSION_DELTAS.get(initiative_id, {}))
        if initiative_id == RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME:
            scale = 0.75 + 0.25 * volume_deficiency
            dimension_deltas = {
                dimension: round(float(delta) * scale, 1)
                for dimension, delta in base_deltas.items()
            }
        else:
            dimension_deltas = {dimension: round(float(delta), 1) for dimension, delta in base_deltas.items()}
        expected_gain = _roadmap_expected_maturity_gain(dimension_deltas)
        complexity = _roadmap_implementation_complexity(initiative_id)
        raw_rois[initiative_id] = expected_gain / max(complexity, 1.0)
        projected_scores = _roadmap_projected_dimension_scores(current_scores, dimension_deltas)
        maturity_impact = round(expected_gain, 2)
        readiness_impact = round(
            float(dimension_deltas.get("operational_readiness") or 0.0) / 100.0,
            2,
        )
        dependency_count = len(RECURRENCE_ROADMAP_INITIATIVE_DEPENDENCIES.get(initiative_id, ()))
        completed = _roadmap_initiative_completion_status(
            initiative_id,
            total_observations=observations,
            total_keys=keys,
            trajectory_available=trajectory_available,
            forecast_confidence=forecast_confidence,
            effectiveness_confidence=effectiveness_confidence,
            operational_readiness_score=float(current_scores.get("operational_readiness") or 0.0),
            lifecycle_score=float(current_scores.get("lifecycle") or 0.0),
            remediation_score=float(current_scores.get("remediation") or 0.0),
            closure_measurable="closure_rate" in lifecycle_summary
            or bool(lifecycle_summary.get("closure_rate_definition")),
            remediation_measurable=remediation_summary.get("remediation_effectiveness") is not None
            or bool(remediation_summary.get("effectiveness_definition")),
        )
        initiative_rows.append(
            {
                "initiative_id": initiative_id,
                "initiative_label": RECURRENCE_ROADMAP_INITIATIVE_LABELS.get(initiative_id, initiative_id),
                "initiative_score": round(expected_gain + readiness_impact * 10.0, 1),
                "maturity_impact": maturity_impact,
                "readiness_impact": readiness_impact,
                "implementation_complexity": complexity,
                "dependency_count": dependency_count,
                "dependencies": list(RECURRENCE_ROADMAP_INITIATIVE_DEPENDENCIES.get(initiative_id, ())),
                "expected_maturity_gain": maturity_impact,
                "dimension_deltas": dimension_deltas,
                "projected_maturity_after_completion": {
                    "overall_maturity_score": _roadmap_weighted_overall_maturity(projected_scores),
                    "overall_maturity_level": _recurrence_maturity_level(
                        _roadmap_weighted_overall_maturity(projected_scores)
                    ),
                    "dimension_scores": projected_scores,
                },
                "completed": completed,
            }
        )

    max_raw_roi = max(raw_rois.values()) if raw_rois else 1.0
    for row in initiative_rows:
        initiative_id = str(row["initiative_id"])
        raw_roi = raw_rois.get(initiative_id, 0.0)
        row["maturity_roi"] = round(100.0 * raw_roi / max(max_raw_roi, 0.001), 1)
        priority = calculate_maturity_investment_priority(
            initiative_id=initiative_id,
            recurrence_maturity_summary=maturity_summary,
            recurrence_maturity_gap_analysis=gap_analysis,
            recurrence_program_effectiveness_summary=program_summary,
            recurrence_portfolio_summary=portfolio_summary,
            recurrence_forecast_summary=forecast_summary,
            recurrence_lifecycle_summary=lifecycle_summary,
            maturity_roi=row["maturity_roi"],
            dependency_count=row["dependency_count"],
        )
        row["investment_priority_score"] = priority["investment_priority_score"]
        row["gap_alignment"] = priority["gap_alignment"]

    initiative_rows.sort(
        key=lambda row: (
            -float(row.get("maturity_roi") or 0.0),
            -float(row.get("investment_priority_score") or 0.0),
        )
    )
    roadmap_sequence = _build_roadmap_sequence(initiative_rows)
    recurrence_target_state = _build_recurrence_target_state(
        maturity_summary=maturity_summary,
        program_summary=program_summary,
        forecast_summary=forecast_summary,
        lifecycle_summary=lifecycle_summary,
        remediation_summary=remediation_summary,
        portfolio_trajectory=portfolio_trajectory,
    )
    remaining_initiatives = [row for row in initiative_rows if not row.get("completed")]
    next_initiative = next(
        (row for row in roadmap_sequence if not row.get("completed")),
        roadmap_sequence[0] if roadmap_sequence else {},
    )
    next_initiative_id = str(next_initiative.get("initiative_id") or RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME)
    next_initiative_row = next(
        (row for row in initiative_rows if row["initiative_id"] == next_initiative_id),
        initiative_rows[0] if initiative_rows else {},
    )
    highest_roi_initiative = max(
        initiative_rows,
        key=lambda row: float(row.get("maturity_roi") or 0.0),
    )
    highest_gap_dimension = str(maturity_summary.get("lowest_dimension") or "operational_readiness")
    if gap_analysis:
        highest_gap_dimension = str(
            max(gap_analysis, key=lambda row: float(row.get("gap") or 0.0)).get("dimension")
            or highest_gap_dimension
        )
    projected_next = next_initiative_row.get("projected_maturity_after_completion") or {}
    roadmap_without_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "current_maturity_score": current_overall,
        "current_maturity_level": _recurrence_maturity_level(current_overall),
        "initiatives": initiative_rows,
        "roadmap_sequence": roadmap_sequence,
        "recurrence_target_state": recurrence_target_state,
        "highest_roi_initiative": highest_roi_initiative.get("initiative_id"),
        "highest_gap_dimension": highest_gap_dimension,
        "next_recommended_initiative": next_initiative_id,
        "roadmap_priority_guidance": (
            RECURRENCE_ROADMAP_LOW_VOLUME_GUIDANCE
            if volume_deficiency >= 0.5
            else "Execute roadmap sequence in dependency order to reach optimized maturity."
        ),
        "maturity_roi_definition": RECURRENCE_ROADMAP_MATURITY_ROI_DEFINITION,
        "investment_priority_definition": RECURRENCE_ROADMAP_INVESTMENT_PRIORITY_DEFINITION,
        "target_state_definition": RECURRENCE_ROADMAP_TARGET_STATE_DEFINITION,
    }
    recurrence_roadmap_summary = summarize_recurrence_roadmap(roadmap_without_summary)
    recurrence_roadmap_summary["estimated_initiatives_remaining"] = len(remaining_initiatives)
    return {
        **roadmap_without_summary,
        "recurrence_roadmap_summary": recurrence_roadmap_summary,
    }


def summarize_recurrence_roadmap(
    roadmap: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence strategic roadmap."""
    source = roadmap if isinstance(roadmap, Mapping) else {}
    summary = source.get("recurrence_roadmap_summary")
    if isinstance(summary, Mapping):
        return dict(summary)
    initiatives = [row for row in (source.get("initiatives") or ()) if isinstance(row, Mapping)]
    remaining = [row for row in initiatives if not row.get("completed")]
    next_initiative = str(
        source.get("next_recommended_initiative")
        or (remaining[0].get("initiative_id") if remaining else RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME)
    )
    next_row = next((row for row in initiatives if row.get("initiative_id") == next_initiative), {})
    projected = next_row.get("projected_maturity_after_completion") or {}
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "highest_roi_initiative": source.get("highest_roi_initiative")
        or RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
        "highest_gap_dimension": source.get("highest_gap_dimension") or "operational_readiness",
        "projected_next_maturity_level": projected.get("overall_maturity_level")
        or _recurrence_maturity_level(float(source.get("current_maturity_score") or 0.0)),
        "projected_next_maturity_score": float(projected.get("overall_maturity_score") or 0.0),
        "estimated_initiatives_remaining": len(remaining),
        "next_recommended_initiative": next_initiative,
        "roadmap_priority_guidance": source.get("roadmap_priority_guidance")
        or RECURRENCE_ROADMAP_LOW_VOLUME_GUIDANCE,
        "target_state_defined": bool(source.get("recurrence_target_state")),
    }


def enrich_recurrence_history_with_roadmap(
    history: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a history payload with additive protected replay roadmap fields."""
    payload = dict(history)
    maturity_summary = payload.get("recurrence_maturity_summary")
    if not isinstance(maturity_summary, Mapping):
        maturity_summary = {}
    program_summary = payload.get("recurrence_program_effectiveness_summary")
    if not isinstance(program_summary, Mapping):
        program_summary = {}
    portfolio_summary = payload.get("recurrence_portfolio_summary")
    if not isinstance(portfolio_summary, Mapping):
        portfolio_summary = {}
    forecast = payload.get("recurrence_forecast")
    forecast_summary = forecast.get("forecast_summary") if isinstance(forecast, Mapping) else None
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    lifecycle_summary = payload.get("recurrence_lifecycle_summary")
    if not isinstance(lifecycle_summary, Mapping):
        lifecycle_summary = {}
    remediation_summary = payload.get("remediation_effectiveness_summary")
    if not isinstance(remediation_summary, Mapping):
        remediation_summary = {}
    portfolio_trajectory = payload.get("portfolio_trajectory_summary")
    if not isinstance(portfolio_trajectory, Mapping):
        portfolio_trajectory = {}
    roadmap = build_recurrence_strategic_roadmap(
        recurrence_maturity_summary=maturity_summary,
        recurrence_maturity_gap_analysis=payload.get("recurrence_maturity_gap_analysis")
        if isinstance(payload.get("recurrence_maturity_gap_analysis"), list)
        else None,
        recurrence_program_effectiveness_summary=program_summary,
        recurrence_portfolio_summary=portfolio_summary,
        recurrence_forecast_summary=forecast_summary,
        recurrence_lifecycle_summary=lifecycle_summary,
        recurrence_remediation_effectiveness_summary=remediation_summary,
        portfolio_trajectory_summary=portfolio_trajectory,
        total_observations=int(payload.get("total_rows") or 0),
        total_keys=int(payload.get("unique_recurrence_count") or 0),
    )
    payload["recurrence_roadmap"] = roadmap
    payload["recurrence_roadmap_summary"] = roadmap["recurrence_roadmap_summary"]
    payload["recurrence_target_state"] = roadmap["recurrence_target_state"]
    return payload


RECURRENCE_COMPLETION_GOVERNANCE_HEALTH_TARGET = RECURRENCE_MATURITY_TARGET_SCORE
RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET = RECURRENCE_MATURITY_TARGET_SCORE
RECURRENCE_COMPLETION_OVERALL_MATURITY_TARGET = RECURRENCE_MATURITY_TARGET_SCORE
RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET = RECURRENCE_ROADMAP_TARGET_FORECAST_CONFIDENCE
RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET = RECURRENCE_ROADMAP_TARGET_EFFECTIVENESS_CONFIDENCE
RECURRENCE_COMPLETION_GOVERNANCE_CONFIDENCE_TARGET = RECURRENCE_ROADMAP_TARGET_EFFECTIVENESS_CONFIDENCE
RECURRENCE_COMPLETION_GRADUATION_DEFINITION = (
    "Program graduated when all six capability dimensions report completion_met=true, "
    "overall_maturity_score >= 80, operational_readiness_score >= 80, "
    "forecast_confidence >= 0.75, and effectiveness_confidence >= 0.75."
)
RECURRENCE_COMPLETION_SCORE_DEFINITION = (
    "Advisory 0-100 overall completion score: weighted average of dimension completion scores "
    "using recurrence maturity dimension weights. Each dimension completion_score is "
    "100 * met_requirements / total_requirements."
)
RECURRENCE_COMPLETION_DISTANCE_DEFINITION = (
    "Estimated completion distance is 100 - overall_completion_score; lower values indicate "
    "closer proximity to program graduation."
)
RECURRENCE_COMPLETION_REQUIREMENT_ROADMAP: dict[str, str] = {
    "recurrence_history_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "trend_analytics_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "forecasting_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "portfolio_analytics_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "governance_analytics_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "lifecycle_analytics_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "governance_health_target_met": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "watchlist_operational": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "ownership_accountability_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "retirement_tracking_present": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "forecast_confidence_target_met": RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION,
    "forecast_effectiveness_measurable": RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION,
    "trajectory_available": RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY,
    "forecast_validation_available": RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION,
    "remediation_targeting_available": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "roi_analytics_available": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "recurrence_reduction_measurable": RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK,
    "remediation_effectiveness_measurable": RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK,
    "lifecycle_tracking_available": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "transition_tracking_available": RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE,
    "closure_effectiveness_measurable": RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE,
    "age_distribution_available": RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE,
    "operational_readiness_target_met": RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION,
    "effectiveness_confidence_target_met": RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION,
    "governance_confidence_target_met": RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
    "overall_maturity_target_met": RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION,
}


def _completion_dimension_result(
    *,
    requirements: Sequence[tuple[str, bool, Any, Any]],
) -> dict[str, Any]:
    unmet: list[str] = []
    met_count = 0
    requirement_rows: list[dict[str, Any]] = []
    for requirement_id, met, current_value, target_value in requirements:
        requirement_rows.append(
            {
                "requirement": requirement_id,
                "met": bool(met),
                "current_value": current_value,
                "target_value": target_value,
            }
        )
        if met:
            met_count += 1
        else:
            unmet.append(requirement_id)
    total = max(len(requirements), 1)
    completion_score = round(100.0 * met_count / float(total), 1)
    return {
        "completion_met": met_count == len(requirements) and len(requirements) > 0,
        "completion_score": completion_score,
        "unmet_requirements": unmet,
        "requirements": requirement_rows,
    }


def _completion_numeric_gap(current: float, target: float) -> float:
    return round(max(0.0, float(target) - float(current)), 2)


def _assess_observability_completion(
    *,
    recurrence_history: Mapping[str, Any] | None,
) -> dict[str, Any]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    checks = [
        (
            "recurrence_history_present",
            bool(history.get("unique_recurrence_count") or history.get("summary")),
            bool(history.get("unique_recurrence_count") or history.get("summary")),
            True,
        ),
        (
            "trend_analytics_present",
            isinstance(history.get("recurrence_trends"), Mapping),
            isinstance(history.get("recurrence_trends"), Mapping),
            True,
        ),
        (
            "forecasting_present",
            isinstance(history.get("recurrence_forecast"), Mapping),
            isinstance(history.get("recurrence_forecast"), Mapping),
            True,
        ),
        (
            "portfolio_analytics_present",
            isinstance(history.get("recurrence_portfolio"), Mapping)
            or isinstance(history.get("recurrence_portfolio_summary"), Mapping),
            isinstance(history.get("recurrence_portfolio"), Mapping)
            or isinstance(history.get("recurrence_portfolio_summary"), Mapping),
            True,
        ),
        (
            "governance_analytics_present",
            isinstance(history.get("recurrence_governance"), Mapping)
            or isinstance(history.get("recurrence_governance_summary"), Mapping),
            isinstance(history.get("recurrence_governance"), Mapping)
            or isinstance(history.get("recurrence_governance_summary"), Mapping),
            True,
        ),
        (
            "lifecycle_analytics_present",
            isinstance(history.get("recurrence_lifecycle"), Mapping)
            or isinstance(history.get("recurrence_lifecycle_summary"), Mapping),
            isinstance(history.get("recurrence_lifecycle"), Mapping)
            or isinstance(history.get("recurrence_lifecycle_summary"), Mapping),
            True,
        ),
    ]
    return _completion_dimension_result(requirements=checks)


def _assess_governance_completion(
    *,
    recurrence_history: Mapping[str, Any] | None,
    recurrence_governance_summary: Mapping[str, Any] | None,
    maturity_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    governance_summary = (
        recurrence_governance_summary if isinstance(recurrence_governance_summary, Mapping) else {}
    )
    if not governance_summary and isinstance(history.get("recurrence_governance_summary"), Mapping):
        governance_summary = history["recurrence_governance_summary"]
    governance = history.get("recurrence_governance")
    if not isinstance(governance, Mapping):
        governance = {}
    governance_health = float(
        governance_summary.get("governance_health_score")
        or governance.get("governance_health_score")
        or (maturity_summary.get("governance_score") if isinstance(maturity_summary, Mapping) else None)
        or 0.0
    )
    watchlist = governance.get("watchlist") if isinstance(governance.get("watchlist"), list) else []
    watchlist_operational = bool(watchlist) or int(governance_summary.get("watchlist_size") or 0) > 0
    owners = governance.get("owners") if isinstance(governance.get("owners"), list) else []
    ownership_present = bool(owners)
    retirement_present = isinstance(governance.get("retirement_summary"), Mapping) or isinstance(
        history.get("recurrence_retirement_summary"), Mapping
    )
    checks = [
        (
            "governance_health_target_met",
            governance_health >= RECURRENCE_COMPLETION_GOVERNANCE_HEALTH_TARGET,
            round(governance_health, 1),
            RECURRENCE_COMPLETION_GOVERNANCE_HEALTH_TARGET,
        ),
        ("watchlist_operational", watchlist_operational, watchlist_operational, True),
        ("ownership_accountability_present", ownership_present, ownership_present, True),
        ("retirement_tracking_present", retirement_present, retirement_present, True),
    ]
    return _completion_dimension_result(requirements=checks)


def _assess_forecasting_completion(
    *,
    recurrence_forecast_summary: Mapping[str, Any] | None,
    forecast_effectiveness_summary: Mapping[str, Any] | None,
    portfolio_trajectory_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    forecast_summary = recurrence_forecast_summary if isinstance(recurrence_forecast_summary, Mapping) else {}
    forecast_effectiveness = (
        forecast_effectiveness_summary if isinstance(forecast_effectiveness_summary, Mapping) else {}
    )
    trajectory = portfolio_trajectory_summary if isinstance(portfolio_trajectory_summary, Mapping) else {}
    forecast_confidence = float(forecast_summary.get("forecast_confidence") or 0.0)
    forecast_measurable = forecast_effectiveness.get("forecast_accuracy") is not None or bool(
        forecast_effectiveness.get("effectiveness_definition")
    )
    trajectory_available = bool(trajectory.get("trajectory_available"))
    validation_available = bool(forecast_effectiveness.get("predicted_recurrences") is not None) or bool(
        forecast_summary.get("watch_keys") is not None
    )
    checks = [
        (
            "forecast_confidence_target_met",
            forecast_confidence >= RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET,
            round(forecast_confidence, 2),
            RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET,
        ),
        ("forecast_effectiveness_measurable", forecast_measurable, forecast_measurable, True),
        ("trajectory_available", trajectory_available, trajectory_available, True),
        ("forecast_validation_available", validation_available, validation_available, True),
    ]
    return _completion_dimension_result(requirements=checks)


def _assess_remediation_completion(
    *,
    recurrence_history: Mapping[str, Any] | None,
    remediation_effectiveness_summary: Mapping[str, Any] | None,
    recurrence_roi_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    remediation = (
        remediation_effectiveness_summary if isinstance(remediation_effectiveness_summary, Mapping) else {}
    )
    roi_summary = recurrence_roi_summary if isinstance(recurrence_roi_summary, Mapping) else {}
    if not roi_summary and isinstance(history.get("recurrence_roi_summary"), Mapping):
        roi_summary = history["recurrence_roi_summary"]
    remediation_targets = history.get("recurrence_remediation_targets")
    targeting_available = isinstance(remediation_targets, Mapping) and bool(
        remediation_targets.get("keys") or remediation_targets.get("remediation_summary")
    )
    roi_available = bool(roi_summary) or isinstance(history.get("recurrence_roi"), Mapping)
    reduction_measurable = remediation.get("recurrence_reduction_rate") is not None
    effectiveness_measurable = remediation.get("remediation_effectiveness") is not None or bool(
        remediation.get("effectiveness_definition")
    )
    checks = [
        ("remediation_targeting_available", targeting_available, targeting_available, True),
        ("roi_analytics_available", roi_available, roi_available, True),
        ("recurrence_reduction_measurable", reduction_measurable, reduction_measurable, True),
        ("remediation_effectiveness_measurable", effectiveness_measurable, effectiveness_measurable, True),
    ]
    return _completion_dimension_result(requirements=checks)


def _assess_lifecycle_completion(
    *,
    recurrence_history: Mapping[str, Any] | None,
    recurrence_lifecycle_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    lifecycle_summary = recurrence_lifecycle_summary if isinstance(recurrence_lifecycle_summary, Mapping) else {}
    lifecycle = history.get("recurrence_lifecycle")
    if not isinstance(lifecycle, Mapping):
        lifecycle = {}
    tracking_available = bool(lifecycle.get("keys")) or bool(lifecycle_summary)
    transition_available = isinstance(lifecycle.get("transition_summary"), Mapping) or isinstance(
        history.get("recurrence_transition_summary"), Mapping
    )
    closure_measurable = "closure_rate" in lifecycle_summary or isinstance(
        history.get("recurrence_closure_effectiveness"), Mapping
    )
    age_available = isinstance(lifecycle.get("age_distribution"), Mapping) or isinstance(
        history.get("recurrence_age_distribution"), Mapping
    )
    checks = [
        ("lifecycle_tracking_available", tracking_available, tracking_available, True),
        ("transition_tracking_available", transition_available, transition_available, True),
        ("closure_effectiveness_measurable", closure_measurable, closure_measurable, True),
        ("age_distribution_available", age_available, age_available, True),
    ]
    return _completion_dimension_result(requirements=checks)


def _assess_operational_readiness_completion(
    *,
    maturity_summary: Mapping[str, Any] | None,
    program_summary: Mapping[str, Any] | None,
    governance_summary: Mapping[str, Any] | None,
    portfolio_trajectory_summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    summary = maturity_summary if isinstance(maturity_summary, Mapping) else {}
    program = program_summary if isinstance(program_summary, Mapping) else {}
    governance = governance_summary if isinstance(governance_summary, Mapping) else {}
    trajectory = portfolio_trajectory_summary if isinstance(portfolio_trajectory_summary, Mapping) else {}
    operational_readiness = float(summary.get("operational_readiness_score") or 0.0)
    effectiveness_confidence = float(program.get("effectiveness_confidence") or 0.0)
    governance_confidence = float(governance.get("governance_confidence") or 0.0)
    trajectory_available = bool(trajectory.get("trajectory_available"))
    checks = [
        (
            "operational_readiness_target_met",
            operational_readiness >= RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET,
            round(operational_readiness, 1),
            RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET,
        ),
        (
            "effectiveness_confidence_target_met",
            effectiveness_confidence >= RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET,
            round(effectiveness_confidence, 2),
            RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET,
        ),
        (
            "governance_confidence_target_met",
            governance_confidence >= RECURRENCE_COMPLETION_GOVERNANCE_CONFIDENCE_TARGET,
            round(governance_confidence, 2),
            RECURRENCE_COMPLETION_GOVERNANCE_CONFIDENCE_TARGET,
        ),
        ("trajectory_available", trajectory_available, trajectory_available, True),
    ]
    return _completion_dimension_result(requirements=checks)


def calculate_recurrence_completion_score(
    *,
    observability_completion: Mapping[str, Any] | None = None,
    governance_completion: Mapping[str, Any] | None = None,
    forecasting_completion: Mapping[str, Any] | None = None,
    remediation_completion: Mapping[str, Any] | None = None,
    lifecycle_completion: Mapping[str, Any] | None = None,
    operational_readiness_completion: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Calculate protected replay recurrence program completion scores."""
    dimensions = {
        "observability": observability_completion if isinstance(observability_completion, Mapping) else {},
        "governance": governance_completion if isinstance(governance_completion, Mapping) else {},
        "forecasting": forecasting_completion if isinstance(forecasting_completion, Mapping) else {},
        "remediation": remediation_completion if isinstance(remediation_completion, Mapping) else {},
        "lifecycle": lifecycle_completion if isinstance(lifecycle_completion, Mapping) else {},
        "operational_readiness": operational_readiness_completion
        if isinstance(operational_readiness_completion, Mapping)
        else {},
    }
    dimension_scores = {
        name: float(row.get("completion_score") or 0.0) for name, row in dimensions.items()
    }
    overall_completion_score = round(
        sum(
            dimension_scores[name] * RECURRENCE_MATURITY_DIMENSION_WEIGHTS[name]
            for name in RECURRENCE_MATURITY_DIMENSION_WEIGHTS
        ),
        1,
    )
    completed_dimensions = [name for name, row in dimensions.items() if row.get("completion_met")]
    remaining_dimensions = [name for name, row in dimensions.items() if not row.get("completion_met")]
    return {
        "dimension_scores": dimension_scores,
        "overall_completion_score": overall_completion_score,
        "completed_dimensions": completed_dimensions,
        "remaining_dimensions": remaining_dimensions,
        "dimensions": dimensions,
    }


def _build_completion_gap_analysis(
    dimensions: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for dimension, row in dimensions.items():
        if not isinstance(row, Mapping):
            continue
        for requirement in row.get("requirements") or ():
            if not isinstance(requirement, Mapping) or requirement.get("met"):
                continue
            requirement_id = str(requirement.get("requirement") or "")
            current_value = requirement.get("current_value")
            target_value = requirement.get("target_value")
            if isinstance(current_value, (int, float)) and isinstance(target_value, (int, float)):
                gap = _completion_numeric_gap(float(current_value), float(target_value))
            elif current_value == target_value:
                gap = 0.0
            else:
                gap = 1.0
            gaps.append(
                {
                    "dimension": dimension,
                    "requirement": requirement_id,
                    "current_value": current_value,
                    "target_value": target_value,
                    "gap": gap,
                    "roadmap_dependency": RECURRENCE_COMPLETION_REQUIREMENT_ROADMAP.get(
                        requirement_id,
                        RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION,
                    ),
                }
            )
    gaps.sort(key=lambda row: (-float(row.get("gap") or 0.0), str(row.get("dimension") or "")))
    return gaps


def _program_graduation_met(
    *,
    dimensions: Mapping[str, Mapping[str, Any]],
    maturity_summary: Mapping[str, Any] | None,
    program_summary: Mapping[str, Any] | None,
    forecast_summary: Mapping[str, Any] | None,
) -> bool:
    summary = maturity_summary if isinstance(maturity_summary, Mapping) else {}
    program = program_summary if isinstance(program_summary, Mapping) else {}
    forecast = forecast_summary if isinstance(forecast_summary, Mapping) else {}
    all_dimensions_complete = all(
        isinstance(row, Mapping) and row.get("completion_met") for row in dimensions.values()
    )
    return bool(
        all_dimensions_complete
        and float(summary.get("overall_maturity_score") or 0.0)
        >= RECURRENCE_COMPLETION_OVERALL_MATURITY_TARGET
        and float(summary.get("operational_readiness_score") or 0.0)
        >= RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET
        and float(forecast.get("forecast_confidence") or 0.0) >= RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET
        and float(program.get("effectiveness_confidence") or 0.0)
        >= RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET
    )


def summarize_recurrence_completion(
    completion: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence program completion."""
    source = completion if isinstance(completion, Mapping) else {}
    summary = source.get("recurrence_completion_summary")
    if isinstance(summary, Mapping):
        return dict(summary)
    scores = source.get("completion_scores")
    if not isinstance(scores, Mapping):
        scores = calculate_recurrence_completion_score()
    remaining_requirements: list[str] = []
    for dimension, row in (scores.get("dimensions") or {}).items():
        if isinstance(row, Mapping):
            remaining_requirements.extend(list(row.get("unmet_requirements") or ()))
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "overall_completion_score": float(scores.get("overall_completion_score") or 0.0),
        "completion_criteria_met": bool(source.get("program_graduated")),
        "program_graduated": bool(source.get("program_graduated")),
        "completed_dimensions": list(scores.get("completed_dimensions") or ()),
        "remaining_dimensions": list(scores.get("remaining_dimensions") or ()),
        "remaining_requirements": remaining_requirements,
        "estimated_completion_distance": round(
            100.0 - float(scores.get("overall_completion_score") or 0.0),
            1,
        ),
        "graduation_definition": RECURRENCE_COMPLETION_GRADUATION_DEFINITION,
        "completion_score_definition": RECURRENCE_COMPLETION_SCORE_DEFINITION,
        "completion_distance_definition": RECURRENCE_COMPLETION_DISTANCE_DEFINITION,
    }


def build_recurrence_completion_assessment(
    *,
    recurrence_maturity_summary: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness_summary: Mapping[str, Any] | None = None,
    recurrence_target_state: Mapping[str, Any] | None = None,
    recurrence_roadmap_summary: Mapping[str, Any] | None = None,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_governance_summary: Mapping[str, Any] | None = None,
    recurrence_forecast_summary: Mapping[str, Any] | None = None,
    forecast_effectiveness_summary: Mapping[str, Any] | None = None,
    remediation_effectiveness_summary: Mapping[str, Any] | None = None,
    recurrence_lifecycle_summary: Mapping[str, Any] | None = None,
    recurrence_roi_summary: Mapping[str, Any] | None = None,
    portfolio_trajectory_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence program completion assessment."""
    maturity_summary = recurrence_maturity_summary if isinstance(recurrence_maturity_summary, Mapping) else {}
    program_summary = (
        recurrence_program_effectiveness_summary
        if isinstance(recurrence_program_effectiveness_summary, Mapping)
        else {}
    )
    target_state = recurrence_target_state if isinstance(recurrence_target_state, Mapping) else {}
    roadmap_summary = recurrence_roadmap_summary if isinstance(recurrence_roadmap_summary, Mapping) else {}
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    governance_summary = (
        recurrence_governance_summary if isinstance(recurrence_governance_summary, Mapping) else {}
    )
    forecast_summary = recurrence_forecast_summary if isinstance(recurrence_forecast_summary, Mapping) else {}
    forecast_effectiveness = (
        forecast_effectiveness_summary if isinstance(forecast_effectiveness_summary, Mapping) else {}
    )
    remediation_summary = (
        remediation_effectiveness_summary if isinstance(remediation_effectiveness_summary, Mapping) else {}
    )
    lifecycle_summary = recurrence_lifecycle_summary if isinstance(recurrence_lifecycle_summary, Mapping) else {}
    roi_summary = recurrence_roi_summary if isinstance(recurrence_roi_summary, Mapping) else {}
    portfolio_trajectory = portfolio_trajectory_summary if isinstance(portfolio_trajectory_summary, Mapping) else {}

    observability_completion = _assess_observability_completion(recurrence_history=history)
    governance_completion = _assess_governance_completion(
        recurrence_history=history,
        recurrence_governance_summary=governance_summary,
        maturity_summary=maturity_summary,
    )
    forecasting_completion = _assess_forecasting_completion(
        recurrence_forecast_summary=forecast_summary,
        forecast_effectiveness_summary=forecast_effectiveness,
        portfolio_trajectory_summary=portfolio_trajectory,
    )
    remediation_completion = _assess_remediation_completion(
        recurrence_history=history,
        remediation_effectiveness_summary=remediation_summary,
        recurrence_roi_summary=roi_summary,
    )
    lifecycle_completion = _assess_lifecycle_completion(
        recurrence_history=history,
        recurrence_lifecycle_summary=lifecycle_summary,
    )
    operational_readiness_completion = _assess_operational_readiness_completion(
        maturity_summary=maturity_summary,
        program_summary=program_summary,
        governance_summary=governance_summary,
        portfolio_trajectory_summary=portfolio_trajectory,
    )
    completion_scores = calculate_recurrence_completion_score(
        observability_completion=observability_completion,
        governance_completion=governance_completion,
        forecasting_completion=forecasting_completion,
        remediation_completion=remediation_completion,
        lifecycle_completion=lifecycle_completion,
        operational_readiness_completion=operational_readiness_completion,
    )
    dimensions = completion_scores["dimensions"]
    completion_gap_analysis = _build_completion_gap_analysis(dimensions)
    program_graduated = _program_graduation_met(
        dimensions=dimensions,
        maturity_summary=maturity_summary,
        program_summary=program_summary,
        forecast_summary=forecast_summary,
    )
    completion_without_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "completion_scores": completion_scores,
        "observability_completion": observability_completion,
        "governance_completion": governance_completion,
        "forecasting_completion": forecasting_completion,
        "remediation_completion": remediation_completion,
        "lifecycle_completion": lifecycle_completion,
        "operational_readiness_completion": operational_readiness_completion,
        "completion_gap_analysis": completion_gap_analysis,
        "program_graduated": program_graduated,
        "graduation_definition": RECURRENCE_COMPLETION_GRADUATION_DEFINITION,
        "completion_score_definition": RECURRENCE_COMPLETION_SCORE_DEFINITION,
        "completion_distance_definition": RECURRENCE_COMPLETION_DISTANCE_DEFINITION,
        "target_state_reference": target_state,
        "roadmap_reference": roadmap_summary,
    }
    recurrence_completion_summary = summarize_recurrence_completion(completion_without_summary)
    return {
        **completion_without_summary,
        "recurrence_completion_summary": recurrence_completion_summary,
    }


def enrich_recurrence_history_with_completion(
    history: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a history payload with additive protected replay completion fields."""
    payload = dict(history)
    forecast = payload.get("recurrence_forecast")
    forecast_summary = forecast.get("forecast_summary") if isinstance(forecast, Mapping) else None
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    completion = build_recurrence_completion_assessment(
        recurrence_maturity_summary=payload.get("recurrence_maturity_summary")
        if isinstance(payload.get("recurrence_maturity_summary"), Mapping)
        else None,
        recurrence_program_effectiveness_summary=payload.get("recurrence_program_effectiveness_summary")
        if isinstance(payload.get("recurrence_program_effectiveness_summary"), Mapping)
        else None,
        recurrence_target_state=payload.get("recurrence_target_state")
        if isinstance(payload.get("recurrence_target_state"), Mapping)
        else None,
        recurrence_roadmap_summary=payload.get("recurrence_roadmap_summary")
        if isinstance(payload.get("recurrence_roadmap_summary"), Mapping)
        else None,
        recurrence_history=payload,
        recurrence_governance_summary=payload.get("recurrence_governance_summary")
        if isinstance(payload.get("recurrence_governance_summary"), Mapping)
        else None,
        recurrence_forecast_summary=forecast_summary,
        forecast_effectiveness_summary=payload.get("forecast_effectiveness_summary")
        if isinstance(payload.get("forecast_effectiveness_summary"), Mapping)
        else None,
        remediation_effectiveness_summary=payload.get("remediation_effectiveness_summary")
        if isinstance(payload.get("remediation_effectiveness_summary"), Mapping)
        else None,
        recurrence_lifecycle_summary=payload.get("recurrence_lifecycle_summary")
        if isinstance(payload.get("recurrence_lifecycle_summary"), Mapping)
        else None,
        recurrence_roi_summary=payload.get("recurrence_roi_summary")
        if isinstance(payload.get("recurrence_roi_summary"), Mapping)
        else None,
        portfolio_trajectory_summary=payload.get("portfolio_trajectory_summary")
        if isinstance(payload.get("portfolio_trajectory_summary"), Mapping)
        else None,
    )
    payload["recurrence_completion"] = completion
    payload["recurrence_completion_summary"] = completion["recurrence_completion_summary"]
    payload["recurrence_completion_gap_analysis"] = completion["completion_gap_analysis"]
    return payload


RECURRENCE_GRADUATION_AUDIT_CAPABILITY_HISTORICAL_PERSISTENCE = "historical_persistence"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_TREND_ANALYTICS = "trend_analytics"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_FORECASTING = "forecasting"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_PORTFOLIO_ANALYTICS = "portfolio_analytics"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_REMEDIATION_TARGETING = "remediation_targeting"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_ROI_ANALYTICS = "roi_analytics"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_GOVERNANCE = "governance"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_LIFECYCLE_MANAGEMENT = "lifecycle_management"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_EFFECTIVENESS_MEASUREMENT = "effectiveness_measurement"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_MATURITY_ASSESSMENT = "maturity_assessment"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_STRATEGIC_ROADMAP = "strategic_roadmap"
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_COMPLETION_TRACKING = "completion_tracking"
RECURRENCE_GRADUATION_AUDIT_CAPABILITIES: tuple[str, ...] = (
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_HISTORICAL_PERSISTENCE,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_TREND_ANALYTICS,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_FORECASTING,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_PORTFOLIO_ANALYTICS,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_REMEDIATION_TARGETING,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_ROI_ANALYTICS,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_GOVERNANCE,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_LIFECYCLE_MANAGEMENT,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_EFFECTIVENESS_MEASUREMENT,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_MATURITY_ASSESSMENT,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_STRATEGIC_ROADMAP,
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_COMPLETION_TRACKING,
)
RECURRENCE_GRADUATION_AUDIT_CAPABILITY_LABELS: dict[str, str] = {
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_HISTORICAL_PERSISTENCE: "Historical Persistence",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_TREND_ANALYTICS: "Trend Analytics",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_FORECASTING: "Forecasting",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_PORTFOLIO_ANALYTICS: "Portfolio Analytics",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_REMEDIATION_TARGETING: "Remediation Targeting",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_ROI_ANALYTICS: "ROI Analytics",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_GOVERNANCE: "Governance",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_LIFECYCLE_MANAGEMENT: "Lifecycle Management",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_EFFECTIVENESS_MEASUREMENT: "Effectiveness Measurement",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_MATURITY_ASSESSMENT: "Maturity Assessment",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_STRATEGIC_ROADMAP: "Strategic Roadmap",
    RECURRENCE_GRADUATION_AUDIT_CAPABILITY_COMPLETION_TRACKING: "Completion Tracking",
}
RECURRENCE_GRADUATION_AUDIT_OPERATIONAL_CONFIDENCE_THRESHOLD = 0.15
RECURRENCE_GRADUATION_AUDIT_READINESS_DEFINITION = (
    "Advisory 0-100 graduation readiness score: 45% overall_completion_score + "
    "30% operational_capability_ratio*100 + 15% validated_capability_ratio*100 + "
    "10% average_capability_confidence*100 - 8 per critical blind spot - 3 per critical "
    "redundancy. Interpretation: 90-100 ready; 70-89 minor gaps; 50-69 moderate gaps; "
    "<50 major gaps."
)
RECURRENCE_GRADUATION_AUDIT_DOC_PATH = Path("docs/audits/BQ16_recurrence_graduation_audit.md")
RECURRENCE_GRADUATION_AUDIT_GOVERNANCE_RUNBOOK_PATH = (
    "docs/runbooks/protected_replay_observation_collection.md"
)


def _completion_criterion_current(
    audit: Mapping[str, Any],
    requirement: str,
    *,
    default: str = "unknown",
) -> str:
    """Return the current value string for one completion criterion row."""
    for row in audit.get("completion_criteria_validation") or ():
        if isinstance(row, Mapping) and row.get("requirement") == requirement:
            return str(row.get("current_value") if row.get("current_value") is not None else default)
    return default


def _critical_blind_spot_count(audit: Mapping[str, Any]) -> int:
    return sum(
        1
        for row in audit.get("blind_spots") or ()
        if isinstance(row, Mapping) and str(row.get("severity") or "").lower() == "critical"
    )


def _critical_blind_spot_ids(audit: Mapping[str, Any]) -> list[str]:
    return [
        str(row.get("blind_spot_id") or "")
        for row in audit.get("blind_spots") or ()
        if isinstance(row, Mapping) and str(row.get("severity") or "").lower() == "critical"
    ]


def render_recurrence_graduation_audit_governance_preamble_markdown(
    audit: Mapping[str, Any] | None,
    *,
    summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render stable CO99/CO100 governance preamble lines for BQ16 audit markdown."""
    payload = audit if isinstance(audit, Mapping) else {}
    active_summary = summary if isinstance(summary, Mapping) else {}
    if not active_summary:
        nested = payload.get("recurrence_graduation_audit_summary")
        active_summary = nested if isinstance(nested, Mapping) else summarize_recurrence_graduation_audit(payload)
    readiness = payload.get("graduation_readiness")
    if not isinstance(readiness, Mapping):
        readiness = {}
    program_graduated = bool(active_summary.get("program_graduated"))
    graduation_status = "**Graduated**" if program_graduated else "**Active — not graduated**"
    critical_ids = _critical_blind_spot_ids(payload)
    critical_blind_spots = _critical_blind_spot_count(payload)
    protected_observations = int(
        payload.get("protected_observation_count") or payload.get("total_rows") or 0
    )
    unique_recurrence_keys = int(
        payload.get("unique_recurrence_keys") or payload.get("unique_recurrence_count") or 0
    )
    trajectory_available = _completion_criterion_current(payload, "trajectory_available", default="False")
    readiness_score = float(active_summary.get("graduation_readiness_score") or 0.0)
    operational_readiness = float(
        readiness.get("operational_readiness_score")
        or _completion_criterion_current(payload, "operational_readiness_target_met", default="0.0")
    )
    overall_maturity = float(
        readiness.get("overall_maturity_score")
        or _completion_criterion_current(payload, "overall_maturity_target_met", default="0.0")
    )
    forecast_confidence = _completion_criterion_current(payload, "forecast_confidence_target_met", default="0.0")
    effectiveness_confidence = _completion_criterion_current(
        payload, "effectiveness_confidence_target_met", default="0.0"
    )
    governance_confidence = _completion_criterion_current(
        payload, "governance_confidence_target_met", default="0.0"
    )
    governance_health = _completion_criterion_current(payload, "governance_health_target_met", default="0.0")
    blind_spot_summary = ", ".join(critical_ids) if critical_ids else "none"
    volume_status = (
        "Sufficient for maturity confidence (`volume_factor` ≥ 0.5 per serialization policy)"
        if protected_observations >= RECURRENCE_MATURITY_MIN_OBSERVATIONS
        and unique_recurrence_keys >= RECURRENCE_MATURITY_MIN_KEYS
        else "Low volume (`recurrence_data_quality` critical)"
    )
    trajectory_status = (
        f"≥ 2 snapshots (`trajectory_available: {str(trajectory_available).lower()}`)"
        if str(trajectory_available).lower() == "true"
        else "`1` (`trajectory_available: false`)"
    )
    recommendation_note = (
        "**Graduated**"
        if program_graduated
        else "**C — Recurrence program remains operationally immature** (`recurrence_program_remains_operationally_immature`)"
        if readiness_score < 90.0
        else "**B — One final targeted validation cycle required** (confidence/outcome evidence pending)"
    )
    return [
        "## Governance context (CO99)",
        "",
        "| Program | Status | Governing document |",
        "|---|---|---|",
        "| **Failure-classification taxonomy (CG-1)** | **Closed** | "
        "[`CG_failure_classification_authority_registry.md`](CG_failure_classification_authority_registry.md) (CO98) |",
        "| **Attribution maturity (CO96)** | **Closed** | "
        "[`CO96_attribution_program_closeout.md`](CO96_attribution_program_closeout.md) |",
        "| **Recurrence taxonomy (CG-4)** | **Closed** — vocabulary documented | "
        "[`CG_recurrence_taxonomy_registry.md`](CG_recurrence_taxonomy_registry.md) |",
        f"| **Recurrence operational graduation** | {graduation_status} | "
        "This document + [`BQC4_final_graduation_decision.md`](BQC4_final_graduation_decision.md) |",
        "",
        "**Operational graduation authority:** Graduation audit builder — "
        "`tests/helpers/replay_bug_recurrence_statistics.py` (`RECURRENCE_GRADUATION_AUDIT_DOC_PATH`). "
        "Final recommendation — `tests/helpers/replay_bug_recurrence_serialization.py` "
        "(`RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH`).",
        "",
        "**Scope:** Recurrence **operational** graduation only. Remaining work requires "
        "**protected replay observation volume and trajectory evidence** — not additional classifier "
        "taxonomy (CG closed) or attribution completeness (CO96 closed).",
        "",
        "### Operational graduation baseline (CO99)",
        "",
        "Evidence required before formal graduation (aligned with BQ-C4 blockers and "
        "`RECURRENCE_FINAL_GRADUATION_DECISION_DEFINITION`):",
        "",
        "| Requirement | Current (BQ-C4) | Target | Category |",
        "|---|---|---|---|",
        f"| Protected replay observations | {volume_status} | "
        "Sufficient for maturity confidence (`volume_factor` ≥ 0.5 per serialization policy) | "
        "**Observation volume** |",
        "| Unique recurrence keys | "
        f"{unique_recurrence_keys} keys | "
        "Coverage supporting forecast/governance validation | **Observation volume** |",
        f"| Trajectory snapshots | {trajectory_status} | ≥ 2 snapshots for change detection | **Trajectory** |",
        f"| Graduation readiness score | `{readiness_score:.1f}` | ≥ `90.0` | **Graduation gate** |",
        "| Calibration score | See BQC4 | ≥ `70.0` | **Confidence** |",
        "| Largest calibration gap | See BQC4 | ≤ `0.20` | **Confidence** |",
        "| `graduation_confidence_ready` | See BQC4 | `true` | **Confidence** |",
        f"| Forecast confidence | `{forecast_confidence}` | ≥ `0.75` | **Operational readiness** |",
        f"| Effectiveness confidence | `{effectiveness_confidence}` | ≥ `0.75` | **Operational readiness** |",
        f"| Governance confidence | `{governance_confidence}` | ≥ `0.75` | **Operational readiness** |",
        f"| Operational readiness score | `{operational_readiness:.1f}` | ≥ `80.0` | **Operational readiness** |",
        f"| Overall maturity score | `{overall_maturity:.1f}` | ≥ `80.0` | **Program maturity** |",
        f"| Critical blind spots | `{critical_blind_spots}` ({blind_spot_summary}) | `0` | "
        "**Architectural constraint** |",
        f"| Program graduated | `{str(program_graduated).lower()}` | `true` | **Verdict** |",
        "",
        "**Stability / regression posture:** Trajectory tracks `stability_score` and "
        "`regression_recurrence_rate` for longitudinal comparison. Graduation is **not** blocked by a "
        "single regression-rate tolerance constant; insufficient protected-replay volume prevents "
        "meaningful stability and effectiveness validation (see Effectiveness Validation below).",
        "",
        f"**Graduation recommendation (BQ-C4):** {recommendation_note}.",
        "",
        "**Remaining operational evidence needed:**",
        "",
        "1. Additional **protected replay failure observations** committed to the protected event log "
        "(`event_source=protected_replay_failure`).",
        "2. **Trajectory baseline** with multiple snapshots (`bug_recurrence_trajectory_history.json`) "
        f"so `trajectory_available={str(trajectory_available).lower()}`.",
        "3. **Validated effectiveness outcomes** (retired keys, measurable recurrence reduction, confirmed "
        "remediation impact) — see Effectiveness Validation below.",
        "4. Resolution of **critical blind spots** before `graduation_confidence_ready` can become true.",
        "",
        "---",
        "",
    ]


def render_recurrence_graduation_audit_governance_cross_references_markdown() -> list[str]:
    """Render stable CO99/CO100 cross-reference footer for BQ16 audit markdown."""
    return [
        "---",
        "",
        "## Cross-references (CO99)",
        "",
        "- Final graduation verdict: [`BQC4_final_graduation_decision.md`](BQC4_final_graduation_decision.md)",
        "- Recurrence taxonomy authority: [`CG_recurrence_taxonomy_registry.md`](CG_recurrence_taxonomy_registry.md)",
        "- Closed programs: [`CO96_attribution_program_closeout.md`](CO96_attribution_program_closeout.md), "
        "[`CG_failure_classification_authority_registry.md`](CG_failure_classification_authority_registry.md) (CO98)",
        f"- Protected replay observation collection (CO100): [`{RECURRENCE_GRADUATION_AUDIT_GOVERNANCE_RUNBOOK_PATH}`]"
        f"({RECURRENCE_GRADUATION_AUDIT_GOVERNANCE_RUNBOOK_PATH})",
        "",
    ]


def _audit_capability_row(
    *,
    capability_id: str,
    implemented: bool,
    validated: bool,
    operational: bool,
    confidence: float,
    remaining_concerns: Sequence[str],
) -> dict[str, Any]:
    return {
        "capability_id": capability_id,
        "capability_label": RECURRENCE_GRADUATION_AUDIT_CAPABILITY_LABELS.get(capability_id, capability_id),
        "implemented": bool(implemented),
        "validated": bool(validated),
        "operational": bool(operational),
        "confidence": round(max(0.0, min(1.0, float(confidence or 0.0))), 2),
        "remaining_concerns": list(remaining_concerns),
    }


def validate_recurrence_program_capabilities(
    *,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_trends: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_portfolio: Mapping[str, Any] | None = None,
    recurrence_remediation: Mapping[str, Any] | None = None,
    recurrence_roi: Mapping[str, Any] | None = None,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
    recurrence_maturity: Mapping[str, Any] | None = None,
    recurrence_roadmap: Mapping[str, Any] | None = None,
    recurrence_completion: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Validate protected replay recurrence program capability coverage."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    trends = recurrence_trends if isinstance(recurrence_trends, Mapping) else {}
    if not trends and isinstance(history.get("recurrence_trends"), Mapping):
        trends = history["recurrence_trends"]
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    if not forecast and isinstance(history.get("recurrence_forecast"), Mapping):
        forecast = history["recurrence_forecast"]
    portfolio = recurrence_portfolio if isinstance(recurrence_portfolio, Mapping) else {}
    if not portfolio and isinstance(history.get("recurrence_portfolio"), Mapping):
        portfolio = history["recurrence_portfolio"]
    remediation = recurrence_remediation if isinstance(recurrence_remediation, Mapping) else {}
    if not remediation and isinstance(history.get("recurrence_remediation_targets"), Mapping):
        remediation = history["recurrence_remediation_targets"]
    roi = recurrence_roi if isinstance(recurrence_roi, Mapping) else {}
    if not roi and isinstance(history.get("recurrence_roi"), Mapping):
        roi = history["recurrence_roi"]
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}
    if not governance and isinstance(history.get("recurrence_governance"), Mapping):
        governance = history["recurrence_governance"]
    lifecycle = recurrence_lifecycle if isinstance(recurrence_lifecycle, Mapping) else {}
    if not lifecycle and isinstance(history.get("recurrence_lifecycle"), Mapping):
        lifecycle = history["recurrence_lifecycle"]
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    maturity = recurrence_maturity if isinstance(recurrence_maturity, Mapping) else {}
    roadmap = recurrence_roadmap if isinstance(recurrence_roadmap, Mapping) else {}
    completion = recurrence_completion if isinstance(recurrence_completion, Mapping) else {}

    observations = int(history.get("total_rows") or portfolio.get("total_observations") or 0)
    keys = int(history.get("unique_recurrence_count") or portfolio.get("total_keys") or 0)
    volume_factor = _maturity_volume_factor(total_observations=observations, total_keys=keys)
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    forecast_confidence = float(forecast_summary.get("forecast_confidence") or 0.0)
    program_summary = effectiveness.get("program_effectiveness_summary")
    if not isinstance(program_summary, Mapping):
        program_summary = {}
    effectiveness_confidence = float(program_summary.get("effectiveness_confidence") or 0.0)

    def _operational(validated_flag: bool, confidence: float) -> bool:
        return validated_flag and confidence >= RECURRENCE_GRADUATION_AUDIT_OPERATIONAL_CONFIDENCE_THRESHOLD

    rows: list[dict[str, Any]] = []

    history_impl = bool(history.get("unique_recurrence_count") is not None or history.get("summary"))
    history_valid = int(history.get("unique_recurrence_count") or 0) > 0 and observations > 0
    history_conf = volume_factor
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_HISTORICAL_PERSISTENCE,
            implemented=history_impl,
            validated=history_valid,
            operational=_operational(history_valid, history_conf),
            confidence=history_conf,
            remaining_concerns=(
                ["Protected replay observation volume remains below confidence threshold."]
                if volume_factor < 0.5
                else []
            ),
        )
    )

    trends_impl = bool(trends)
    trends_valid = trends.get("total_keys") is not None and int(trends.get("total_keys") or 0) >= 0
    trends_conf = min(1.0, volume_factor + 0.1) if trends_valid else 0.0
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_TREND_ANALYTICS,
            implemented=trends_impl,
            validated=trends_valid and observations > 0,
            operational=_operational(trends_valid and observations > 0, trends_conf),
            confidence=trends_conf,
            remaining_concerns=(
                ["Trend classifications rely on sparse protected history."]
                if observations < RECURRENCE_MATURITY_MIN_OBSERVATIONS
                else []
            ),
        )
    )

    forecast_impl = bool(forecast.get("key_forecasts") or forecast_summary)
    forecast_valid = bool(forecast.get("key_forecasts")) and keys > 0
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_FORECASTING,
            implemented=forecast_impl,
            validated=forecast_valid,
            operational=_operational(forecast_valid, forecast_confidence),
            confidence=forecast_confidence,
            remaining_concerns=(
                ["Forecast confidence remains below operational threshold."]
                if forecast_confidence < RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET
                else []
            ),
        )
    )

    portfolio_impl = bool(portfolio.get("portfolio_summary") or history.get("recurrence_portfolio_summary"))
    portfolio_valid = portfolio_impl and observations > 0
    portfolio_conf = min(1.0, volume_factor + forecast_confidence * 0.3)
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_PORTFOLIO_ANALYTICS,
            implemented=portfolio_impl,
            validated=portfolio_valid,
            operational=_operational(portfolio_valid, portfolio_conf),
            confidence=portfolio_conf,
            remaining_concerns=[],
        )
    )

    remediation_impl = bool(remediation.get("keys") or remediation.get("remediation_summary"))
    remediation_valid = remediation_impl and keys > 0
    remediation_conf = min(1.0, volume_factor * 0.8 + 0.1)
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_REMEDIATION_TARGETING,
            implemented=remediation_impl,
            validated=remediation_valid,
            operational=_operational(remediation_valid, remediation_conf),
            confidence=remediation_conf,
            remaining_concerns=(
                ["Remediation confidence remains low at current observation volume."]
                if remediation_conf < RECURRENCE_GRADUATION_AUDIT_OPERATIONAL_CONFIDENCE_THRESHOLD
                else []
            ),
        )
    )

    roi_impl = bool(roi.get("roi_summary") or history.get("recurrence_roi_summary"))
    roi_valid = roi_impl and keys > 0
    roi_conf = min(1.0, volume_factor * 0.7 + 0.15)
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_ROI_ANALYTICS,
            implemented=roi_impl,
            validated=roi_valid,
            operational=_operational(roi_valid, roi_conf),
            confidence=roi_conf,
            remaining_concerns=[],
        )
    )

    governance_impl = bool(governance.get("watchlist") or governance.get("governance_summary"))
    governance_valid = governance_impl and bool(governance.get("watchlist"))
    governance_conf = float(
        (governance.get("governance_summary") or {}).get("governance_confidence")
        or governance.get("governance_confidence")
        or 0.0
    )
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_GOVERNANCE,
            implemented=governance_impl,
            validated=governance_valid,
            operational=_operational(governance_valid, governance_conf),
            confidence=governance_conf,
            remaining_concerns=(
                ["Governance health remains below completion target."]
                if float((governance.get("governance_summary") or {}).get("governance_health_score") or 0.0)
                < RECURRENCE_COMPLETION_GOVERNANCE_HEALTH_TARGET
                else []
            ),
        )
    )

    lifecycle_impl = bool(lifecycle.get("keys") or lifecycle.get("lifecycle_summary"))
    lifecycle_valid = lifecycle_impl and keys > 0
    lifecycle_conf = min(1.0, volume_factor + 0.2)
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_LIFECYCLE_MANAGEMENT,
            implemented=lifecycle_impl,
            validated=lifecycle_valid,
            operational=_operational(lifecycle_valid, lifecycle_conf),
            confidence=lifecycle_conf,
            remaining_concerns=[],
        )
    )

    effectiveness_impl = bool(effectiveness.get("program_effectiveness_summary"))
    effectiveness_valid = effectiveness_impl and keys > 0
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_EFFECTIVENESS_MEASUREMENT,
            implemented=effectiveness_impl,
            validated=effectiveness_valid,
            operational=_operational(effectiveness_valid, effectiveness_confidence),
            confidence=effectiveness_confidence,
            remaining_concerns=(
                ["Effectiveness confidence remains below graduation threshold."]
                if effectiveness_confidence < RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET
                else []
            ),
        )
    )

    maturity_impl = bool(maturity.get("recurrence_maturity_summary"))
    maturity_valid = maturity_impl and float(
        (maturity.get("recurrence_maturity_summary") or {}).get("overall_maturity_score") or 0.0
    ) > 0.0
    maturity_conf = float(
        (maturity.get("recurrence_maturity_summary") or {}).get("overall_maturity_score") or 0.0
    ) / 100.0
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_MATURITY_ASSESSMENT,
            implemented=maturity_impl,
            validated=maturity_valid,
            operational=_operational(maturity_valid, maturity_conf),
            confidence=maturity_conf,
            remaining_concerns=[],
        )
    )

    roadmap_impl = bool(roadmap.get("recurrence_roadmap_summary") or roadmap.get("initiatives"))
    roadmap_valid = roadmap_impl and bool(roadmap.get("roadmap_sequence"))
    roadmap_conf = 0.8 if roadmap_valid else 0.0
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_STRATEGIC_ROADMAP,
            implemented=roadmap_impl,
            validated=roadmap_valid,
            operational=roadmap_valid,
            confidence=roadmap_conf,
            remaining_concerns=[],
        )
    )

    completion_impl = bool(completion.get("recurrence_completion_summary"))
    completion_valid = completion_impl and float(
        (completion.get("recurrence_completion_summary") or {}).get("overall_completion_score") or 0.0
    ) >= 0.0
    completion_conf = float(
        (completion.get("recurrence_completion_summary") or {}).get("overall_completion_score") or 0.0
    ) / 100.0
    rows.append(
        _audit_capability_row(
            capability_id=RECURRENCE_GRADUATION_AUDIT_CAPABILITY_COMPLETION_TRACKING,
            implemented=completion_impl,
            validated=completion_valid,
            operational=_operational(completion_valid, completion_conf),
            confidence=completion_conf,
            remaining_concerns=(
                ["Program graduation criteria not yet met."]
                if not (completion.get("recurrence_completion_summary") or {}).get("program_graduated")
                else []
            ),
        )
    )
    return rows


def _audit_completion_criteria_validation(
    *,
    recurrence_completion: Mapping[str, Any] | None,
    recurrence_maturity: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    recurrence_forecast: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    completion = recurrence_completion if isinstance(recurrence_completion, Mapping) else {}
    maturity_summary = {}
    if isinstance(recurrence_maturity, Mapping):
        maturity_summary = recurrence_maturity.get("recurrence_maturity_summary") or {}
    if not isinstance(maturity_summary, Mapping):
        maturity_summary = {}
    program_summary = {}
    if isinstance(recurrence_program_effectiveness, Mapping):
        program_summary = recurrence_program_effectiveness.get("program_effectiveness_summary") or {}
    if not isinstance(program_summary, Mapping):
        program_summary = {}
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}

    rows: list[dict[str, Any]] = []
    dimension_completion = {
        "observability": completion.get("observability_completion"),
        "governance": completion.get("governance_completion"),
        "forecasting": completion.get("forecasting_completion"),
        "remediation": completion.get("remediation_completion"),
        "lifecycle": completion.get("lifecycle_completion"),
        "operational_readiness": completion.get("operational_readiness_completion"),
    }
    for dimension, payload in dimension_completion.items():
        if not isinstance(payload, Mapping):
            continue
        for requirement in payload.get("requirements") or ():
            if not isinstance(requirement, Mapping):
                continue
            rows.append(
                {
                    "requirement": str(requirement.get("requirement") or ""),
                    "dimension": dimension,
                    "current_value": requirement.get("current_value"),
                    "target_value": requirement.get("target_value"),
                    "status": "met" if requirement.get("met") else "unmet",
                    "confidence": 0.9 if requirement.get("met") else 0.4,
                    "threshold_appropriate": True,
                }
            )
    rows.extend(
        [
            {
                "requirement": "overall_maturity_target_met",
                "dimension": "program",
                "current_value": float(maturity_summary.get("overall_maturity_score") or 0.0),
                "target_value": RECURRENCE_COMPLETION_OVERALL_MATURITY_TARGET,
                "status": "met"
                if float(maturity_summary.get("overall_maturity_score") or 0.0)
                >= RECURRENCE_COMPLETION_OVERALL_MATURITY_TARGET
                else "unmet",
                "confidence": 0.85,
                "threshold_appropriate": True,
            },
            {
                "requirement": "forecast_confidence_graduation",
                "dimension": "program",
                "current_value": float(forecast_summary.get("forecast_confidence") or 0.0),
                "target_value": RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET,
                "status": "met"
                if float(forecast_summary.get("forecast_confidence") or 0.0)
                >= RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET
                else "unmet",
                "confidence": float(forecast_summary.get("forecast_confidence") or 0.0),
                "threshold_appropriate": True,
            },
            {
                "requirement": "effectiveness_confidence_graduation",
                "dimension": "program",
                "current_value": float(program_summary.get("effectiveness_confidence") or 0.0),
                "target_value": RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET,
                "status": "met"
                if float(program_summary.get("effectiveness_confidence") or 0.0)
                >= RECURRENCE_COMPLETION_EFFECTIVENESS_CONFIDENCE_TARGET
                else "unmet",
                "confidence": float(program_summary.get("effectiveness_confidence") or 0.0),
                "threshold_appropriate": True,
            },
        ]
    )
    return rows


def _audit_roadmap_assumption_validation(
    *,
    recurrence_roadmap: Mapping[str, Any] | None,
    recurrence_history: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    roadmap = recurrence_roadmap if isinstance(recurrence_roadmap, Mapping) else {}
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    observations = int(history.get("total_rows") or 0)
    keys = int(history.get("unique_recurrence_count") or 0)
    volume_factor = _maturity_volume_factor(total_observations=observations, total_keys=keys)
    trajectory = effectiveness.get("portfolio_trajectory_summary")
    if not isinstance(trajectory, Mapping):
        trajectory = {}
    trajectory_available = bool(trajectory.get("trajectory_available"))

    assumptions: list[tuple[str, str, str]] = []
    if volume_factor < 0.5:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
                "still_valid",
                "Low protected replay volume confirms data expansion remains highest ROI.",
            )
        )
    else:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_DATA_VOLUME,
                "partially_valid",
                "Volume threshold partially met; continued expansion still improves confidence.",
            )
        )
    if not trajectory_available:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY,
                "still_valid",
                "Trajectory unavailable; baseline-only posture validates trajectory-first sequencing.",
            )
        )
    else:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_TRAJECTORY,
                "partially_valid",
                "Trajectory exists but downstream forecasting and readiness remain incomplete.",
            )
        )
    forecast_summary = (history.get("recurrence_forecast") or {}).get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    if float(forecast_summary.get("forecast_confidence") or 0.0) < RECURRENCE_COMPLETION_FORECAST_CONFIDENCE_TARGET:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION,
                "still_valid",
                "Forecast confidence below target; validation initiative remains appropriate.",
            )
        )
    else:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_FORECAST_VALIDATION,
                "partially_valid",
                "Forecast confidence met structurally but effectiveness evidence remains thin.",
            )
        )
    lifecycle_summary = history.get("recurrence_lifecycle_summary")
    if not isinstance(lifecycle_summary, Mapping):
        lifecycle_summary = {}
    if float(lifecycle_summary.get("closure_rate") or 0.0) <= 0.0:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE,
                "still_valid",
                "No closure outcomes observed; lifecycle closure tracking remains necessary.",
            )
        )
    else:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_LIFECYCLE_CLOSURE,
                "partially_valid",
                "Closure signal exists but longitudinal closure effectiveness remains limited.",
            )
        )
    remediation_summary = effectiveness.get("remediation_effectiveness_summary")
    if not isinstance(remediation_summary, Mapping):
        remediation_summary = {}
    if float(remediation_summary.get("recurrence_reduction_rate") or 0.0) <= 0.0:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK,
                "still_valid",
                "Zero recurrence reduction rate; remediation feedback loop not yet evidenced.",
            )
        )
    else:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_REMEDIATION_FEEDBACK,
                "partially_valid",
                "Reduction signal present but sample size may be insufficient.",
            )
        )
    maturity_summary = (history.get("recurrence_maturity_summary") or {}) if isinstance(history, Mapping) else {}
    if not isinstance(maturity_summary, Mapping):
        maturity_summary = {}
    if float(maturity_summary.get("operational_readiness_score") or 0.0) < RECURRENCE_COMPLETION_OPERATIONAL_READINESS_TARGET:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION,
                "still_valid",
                "Operational readiness below target; final operationalization stage remains required.",
            )
        )
    else:
        assumptions.append(
            (
                RECURRENCE_ROADMAP_INITIATIVE_OPERATIONALIZATION,
                "partially_valid",
                "Operational readiness improved but graduation thresholds not fully met.",
            )
        )

    return [
        {
            "initiative_id": initiative_id,
            "initiative_label": RECURRENCE_ROADMAP_INITIATIVE_LABELS.get(initiative_id, initiative_id),
            "validation_status": status,
            "rationale": rationale,
        }
        for initiative_id, status, rationale in assumptions
    ]


def _audit_effectiveness_assumption_validation(
    *,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    forecast = effectiveness.get("forecast_effectiveness_summary")
    if not isinstance(forecast, Mapping):
        forecast = {}
    governance = effectiveness.get("governance_effectiveness_summary")
    if not isinstance(governance, Mapping):
        governance = {}
    remediation = effectiveness.get("remediation_effectiveness_summary")
    if not isinstance(remediation, Mapping):
        remediation = {}
    metrics = effectiveness.get("effectiveness_metrics")
    if not isinstance(metrics, Mapping):
        metrics = {}

    rows: list[dict[str, Any]] = []
    forecast_accuracy = float(forecast.get("forecast_accuracy") or metrics.get("forecast_accuracy") or 0.0)
    forecast_confidence = float(forecast.get("forecast_confidence") or metrics.get("forecast_confidence") or 0.0)
    if forecast_accuracy >= 0.99 and forecast_confidence < 0.25:
        evidence = "potentially_misleading"
        rationale = "Perfect accuracy with very low confidence suggests insufficient validation volume."
    elif forecast_confidence >= 0.25:
        evidence = "supported_by_evidence"
        rationale = "Forecast effectiveness metrics available with non-trivial confidence."
    else:
        evidence = "insufficient_evidence"
        rationale = "Forecast effectiveness measurable but confidence remains low."
    rows.append(
        {
            "metric": "forecast_accuracy",
            "current_value": forecast_accuracy,
            "evidence_status": evidence,
            "rationale": rationale,
        }
    )

    governance_effectiveness = float(
        governance.get("governance_effectiveness") or metrics.get("governance_effectiveness") or 0.0
    )
    rows.append(
        {
            "metric": "governance_effectiveness",
            "current_value": governance_effectiveness,
            "evidence_status": "insufficient_evidence"
            if governance_effectiveness <= 0.0
            else "supported_by_evidence",
            "rationale": "Zero conversion rates indicate governance funnel not yet exercised by history volume.",
        }
    )

    remediation_effectiveness = float(
        remediation.get("remediation_effectiveness") or metrics.get("remediation_effectiveness") or 0.0
    )
    rows.append(
        {
            "metric": "remediation_effectiveness",
            "current_value": remediation_effectiveness,
            "evidence_status": "insufficient_evidence"
            if remediation_effectiveness <= 0.0
            else "supported_by_evidence",
            "rationale": "No resolved remediation outcomes observed in protected replay history.",
        }
    )

    closure_rate = float(metrics.get("closure_rate") or 0.0)
    rows.append(
        {
            "metric": "lifecycle_closure_effectiveness",
            "current_value": closure_rate,
            "evidence_status": "insufficient_evidence"
            if closure_rate <= 0.0
            else "supported_by_evidence",
            "rationale": "Lifecycle closure rate requires retired or dormant keys to validate effectiveness.",
        }
    )
    return rows


def _audit_blind_spot_analysis(
    *,
    recurrence_history: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    recurrence_forecast: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    observations = int(history.get("total_rows") or 0)
    keys = int(history.get("unique_recurrence_count") or 0)
    volume_factor = _maturity_volume_factor(total_observations=observations, total_keys=keys)
    trajectory = effectiveness.get("portfolio_trajectory_summary")
    if not isinstance(trajectory, Mapping):
        trajectory = {}
    forecast_summary = forecast.get("forecast_summary")
    if not isinstance(forecast_summary, Mapping):
        forecast_summary = {}
    metrics = effectiveness.get("effectiveness_metrics")
    if not isinstance(metrics, Mapping):
        metrics = {}

    blind_spots: list[dict[str, Any]] = []
    if volume_factor < 0.5:
        blind_spots.append(
            {
                "blind_spot_id": "recurrence_data_quality",
                "severity": "critical",
                "description": "Protected replay observation and key volume remain below maturity confidence thresholds.",
                "recommendation": "Continue data volume expansion before trusting downstream scores.",
            }
        )
    if not bool(trajectory.get("trajectory_available")):
        blind_spots.append(
            {
                "blind_spot_id": "recurrence_trajectory_history",
                "severity": "critical",
                "description": "No longitudinal trajectory baseline exists for portfolio and readiness comparisons.",
                "recommendation": "Establish trajectory snapshots after sufficient protected replay history.",
            }
        )
    blind_spots.append(
        {
            "blind_spot_id": "recurrence_confidence_decay",
            "severity": "medium",
            "description": "Confidence scores do not decay with stale observations or aging keys.",
            "recommendation": "Consider temporal decay modeling in a future cycle if history spans long idle periods.",
        }
    )
    if not history.get("persistence_population"):
        blind_spots.append(
            {
                "blind_spot_id": "recurrence_artifact_integrity",
                "severity": "medium",
                "description": "Artifact provenance is not continuously re-audited during graduation assessment.",
                "recommendation": "Run periodic provenance audits on protected recurrence event logs.",
            }
        )
    blind_spots.append(
        {
            "blind_spot_id": "recurrence_auditability",
            "severity": "low",
            "description": "No immutable audit chain links recurrence analytics revisions over time.",
            "recommendation": "Retain versioned history artifacts for audit replay if formal compliance is required.",
        }
    )
    if float(forecast_summary.get("forecast_confidence") or 0.0) < 0.25 and float(
        metrics.get("forecast_accuracy") or 0.0
    ) >= 0.99:
        blind_spots.append(
            {
                "blind_spot_id": "recurrence_model_calibration",
                "severity": "high",
                "description": "High forecast accuracy coexists with low forecast confidence, risking over-interpretation.",
                "recommendation": "Treat forecast accuracy as advisory until confidence crosses graduation threshold.",
            }
        )
    blind_spots.append(
        {
            "blind_spot_id": "recurrence_ownership_drift",
            "severity": "medium",
            "description": "Recurrence ownership drift across runs is not tracked as a dedicated longitudinal signal.",
            "recommendation": "Monitor owner_drift_bucket transitions separately from recurrence key lifecycle.",
        }
    )
    return blind_spots


def _audit_redundancy_analysis(
    *,
    recurrence_maturity: Mapping[str, Any] | None,
    recurrence_completion: Mapping[str, Any] | None,
    recurrence_program_effectiveness: Mapping[str, Any] | None,
    recurrence_forecast: Mapping[str, Any] | None,
    recurrence_portfolio: Mapping[str, Any] | None,
    recurrence_governance: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    maturity = recurrence_maturity if isinstance(recurrence_maturity, Mapping) else {}
    completion = recurrence_completion if isinstance(recurrence_completion, Mapping) else {}
    effectiveness = (
        recurrence_program_effectiveness if isinstance(recurrence_program_effectiveness, Mapping) else {}
    )
    forecast = recurrence_forecast if isinstance(recurrence_forecast, Mapping) else {}
    portfolio = recurrence_portfolio if isinstance(recurrence_portfolio, Mapping) else {}
    governance = recurrence_governance if isinstance(recurrence_governance, Mapping) else {}

    redundancies: list[dict[str, Any]] = []
    maturity_summary = maturity.get("recurrence_maturity_summary")
    completion_summary = completion.get("recurrence_completion_summary")
    if isinstance(maturity_summary, Mapping) and isinstance(completion_summary, Mapping):
        redundancies.append(
            {
                "redundancy_id": "maturity_vs_completion_dimensions",
                "severity": "medium",
                "overlapping_signals": ["observability", "governance", "forecasting", "remediation", "lifecycle"],
                "consolidation_recommendation": (
                    "Use maturity scores for capability posture and completion scores for graduation gates; "
                    "avoid treating both as independent KPIs in operator dashboards."
                ),
            }
        )
    program_summary = effectiveness.get("program_effectiveness_summary")
    if isinstance(program_summary, Mapping) and isinstance(maturity_summary, Mapping):
        redundancies.append(
            {
                "redundancy_id": "program_effectiveness_vs_overall_maturity",
                "severity": "medium",
                "overlapping_signals": ["program_effectiveness_score", "overall_maturity_score"],
                "consolidation_recommendation": (
                    "Program effectiveness measures outcomes; maturity measures capability. "
                    "Report both but do not average them into a single headline metric."
                ),
            }
        )
    governance_summary = governance.get("governance_summary")
    governance_effectiveness = effectiveness.get("governance_effectiveness_summary")
    if isinstance(governance_summary, Mapping) and isinstance(governance_effectiveness, Mapping):
        redundancies.append(
            {
                "redundancy_id": "governance_health_vs_governance_effectiveness",
                "severity": "high",
                "overlapping_signals": ["governance_health_score", "governance_effectiveness"],
                "consolidation_recommendation": (
                    "Health score reflects posture; effectiveness reflects funnel conversion. "
                    "Keep both, but label clearly to prevent duplicate escalation triggers."
                ),
            }
        )
    forecast_summary = forecast.get("forecast_summary")
    portfolio_summary = portfolio.get("portfolio_summary")
    if isinstance(forecast_summary, Mapping) and isinstance(portfolio_summary, Mapping):
        redundancies.append(
            {
                "redundancy_id": "forecast_risk_vs_portfolio_risk",
                "severity": "medium",
                "overlapping_signals": ["forecast_risk_score", "portfolio_risk_score"],
                "consolidation_recommendation": (
                    "Portfolio risk already blends forecast risk; prefer portfolio_risk_score for prioritization "
                    "summaries unless forecast-specific drill-down is required."
                ),
            }
        )
    if isinstance(program_summary, Mapping):
        redundancies.append(
            {
                "redundancy_id": "multiple_confidence_metrics",
                "severity": "low",
                "overlapping_signals": [
                    "forecast_confidence",
                    "governance_confidence",
                    "effectiveness_confidence",
                    "remediation_confidence",
                ],
                "consolidation_recommendation": (
                    "Expose a single operator-facing readiness confidence only when all component "
                    "confidences exceed graduation thresholds."
                ),
            }
        )
    return redundancies


def calculate_recurrence_graduation_readiness_score(
    *,
    capability_coverage: Sequence[Mapping[str, Any]] | None,
    blind_spots: Sequence[Mapping[str, Any]] | None,
    redundancies: Sequence[Mapping[str, Any]] | None,
    overall_completion_score: float,
) -> dict[str, Any]:
    """Calculate protected replay recurrence graduation readiness score."""
    capabilities = [row for row in (capability_coverage or ()) if isinstance(row, Mapping)]
    total = max(len(capabilities), 1)
    operational_count = sum(1 for row in capabilities if row.get("operational"))
    validated_count = sum(1 for row in capabilities if row.get("validated"))
    avg_confidence = (
        sum(float(row.get("confidence") or 0.0) for row in capabilities) / float(total) if capabilities else 0.0
    )
    critical_blind_spots = sum(
        1 for row in (blind_spots or ()) if isinstance(row, Mapping) and row.get("severity") == "critical"
    )
    critical_redundancies = sum(
        1 for row in (redundancies or ()) if isinstance(row, Mapping) and row.get("severity") in {"high", "critical"}
    )
    raw_score = (
        0.45 * float(overall_completion_score or 0.0)
        + 0.30 * (operational_count / float(total) * 100.0)
        + 0.15 * (validated_count / float(total) * 100.0)
        + 0.10 * (avg_confidence * 100.0)
        - critical_blind_spots * 8.0
        - critical_redundancies * 3.0
    )
    graduation_readiness_score = _clamp_maturity_score(raw_score)
    if graduation_readiness_score >= 90.0:
        readiness_level = "ready_for_graduation"
        readiness_label = "Ready for graduation"
    elif graduation_readiness_score >= 70.0:
        readiness_level = "minor_gaps_remain"
        readiness_label = "Minor gaps remain"
    elif graduation_readiness_score >= 50.0:
        readiness_level = "moderate_gaps_remain"
        readiness_label = "Moderate gaps remain"
    else:
        readiness_level = "major_gaps_remain"
        readiness_label = "Major capability gaps remain"
    return {
        "graduation_readiness_score": graduation_readiness_score,
        "readiness_level": readiness_level,
        "readiness_label": readiness_label,
        "operational_capability_ratio": round(operational_count / float(total), 2),
        "validated_capability_ratio": round(validated_count / float(total), 2),
        "average_capability_confidence": round(avg_confidence, 2),
        "critical_blind_spots": critical_blind_spots,
        "critical_redundancies": critical_redundancies,
        "readiness_definition": RECURRENCE_GRADUATION_AUDIT_READINESS_DEFINITION,
    }


def summarize_recurrence_graduation_audit(
    audit: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Summarize protected replay recurrence graduation audit."""
    source = audit if isinstance(audit, Mapping) else {}
    summary = source.get("recurrence_graduation_audit_summary")
    if isinstance(summary, Mapping):
        return dict(summary)
    capabilities = [row for row in (source.get("capability_coverage") or ()) if isinstance(row, Mapping)]
    blind_spots = [row for row in (source.get("blind_spots") or ()) if isinstance(row, Mapping)]
    redundancies = [row for row in (source.get("redundancies") or ()) if isinstance(row, Mapping)]
    readiness = source.get("graduation_readiness")
    if not isinstance(readiness, Mapping):
        readiness = {}
    completion_summary = source.get("completion_reference")
    if not isinstance(completion_summary, Mapping):
        completion_summary = {}
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "capabilities_complete": sum(1 for row in capabilities if row.get("implemented") and row.get("operational")),
        "validated_capabilities": sum(1 for row in capabilities if row.get("validated")),
        "critical_blind_spots": int(readiness.get("critical_blind_spots") or 0),
        "critical_redundancies": int(readiness.get("critical_redundancies") or 0),
        "graduation_readiness_score": float(readiness.get("graduation_readiness_score") or 0.0),
        "readiness_level": readiness.get("readiness_level") or "major_gaps_remain",
        "readiness_label": readiness.get("readiness_label") or "Major capability gaps remain",
        "program_graduated": bool(completion_summary.get("program_graduated")),
        "recommended_next_action": source.get("recommended_next_action")
        or "Expand protected replay observation volume before graduation.",
        "readiness_definition": RECURRENCE_GRADUATION_AUDIT_READINESS_DEFINITION,
    }


def build_recurrence_graduation_audit(
    *,
    recurrence_history: Mapping[str, Any] | None = None,
    recurrence_trends: Mapping[str, Any] | None = None,
    recurrence_forecast: Mapping[str, Any] | None = None,
    recurrence_portfolio: Mapping[str, Any] | None = None,
    recurrence_remediation: Mapping[str, Any] | None = None,
    recurrence_roi: Mapping[str, Any] | None = None,
    recurrence_governance: Mapping[str, Any] | None = None,
    recurrence_lifecycle: Mapping[str, Any] | None = None,
    recurrence_program_effectiveness: Mapping[str, Any] | None = None,
    recurrence_maturity: Mapping[str, Any] | None = None,
    recurrence_roadmap: Mapping[str, Any] | None = None,
    recurrence_completion: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build protected replay recurrence graduation audit analytics."""
    history = recurrence_history if isinstance(recurrence_history, Mapping) else {}
    capability_coverage = validate_recurrence_program_capabilities(
        recurrence_history=history,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_remediation=recurrence_remediation,
        recurrence_roi=recurrence_roi,
        recurrence_governance=recurrence_governance,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_maturity=recurrence_maturity,
        recurrence_roadmap=recurrence_roadmap,
        recurrence_completion=recurrence_completion,
    )
    completion_criteria_validation = _audit_completion_criteria_validation(
        recurrence_completion=recurrence_completion,
        recurrence_maturity=recurrence_maturity,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_forecast=recurrence_forecast if isinstance(recurrence_forecast, Mapping) else history.get("recurrence_forecast"),
    )
    roadmap_validation = _audit_roadmap_assumption_validation(
        recurrence_roadmap=recurrence_roadmap,
        recurrence_history=history,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
    )
    effectiveness_validation = _audit_effectiveness_assumption_validation(
        recurrence_program_effectiveness=recurrence_program_effectiveness,
    )
    blind_spots = _audit_blind_spot_analysis(
        recurrence_history=history,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_forecast=recurrence_forecast if isinstance(recurrence_forecast, Mapping) else history.get("recurrence_forecast"),
    )
    redundancies = _audit_redundancy_analysis(
        recurrence_maturity=recurrence_maturity,
        recurrence_completion=recurrence_completion,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_forecast=recurrence_forecast if isinstance(recurrence_forecast, Mapping) else history.get("recurrence_forecast"),
        recurrence_portfolio=recurrence_portfolio if isinstance(recurrence_portfolio, Mapping) else history.get("recurrence_portfolio"),
        recurrence_governance=recurrence_governance if isinstance(recurrence_governance, Mapping) else history.get("recurrence_governance"),
    )
    completion_summary = {}
    if isinstance(recurrence_completion, Mapping):
        completion_summary = recurrence_completion.get("recurrence_completion_summary") or {}
    if not isinstance(completion_summary, Mapping):
        completion_summary = {}
    overall_completion_score = float(completion_summary.get("overall_completion_score") or 0.0)
    graduation_readiness = calculate_recurrence_graduation_readiness_score(
        capability_coverage=capability_coverage,
        blind_spots=blind_spots,
        redundancies=redundancies,
        overall_completion_score=overall_completion_score,
    )
    roadmap_summary = {}
    if isinstance(recurrence_roadmap, Mapping):
        roadmap_summary = recurrence_roadmap.get("recurrence_roadmap_summary") or {}
    if not isinstance(roadmap_summary, Mapping):
        roadmap_summary = {}
    recommended_next_action = str(
        roadmap_summary.get("roadmap_priority_guidance")
        or "Expand protected replay observation volume and establish trajectory baseline before graduation."
    )
    audit_without_summary = {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "protected_replay_only": True,
        "protected_observation_count": int(history.get("total_rows") or 0),
        "unique_recurrence_keys": int(history.get("unique_recurrence_count") or 0),
        "capability_coverage": capability_coverage,
        "completion_criteria_validation": completion_criteria_validation,
        "roadmap_validation": roadmap_validation,
        "effectiveness_validation": effectiveness_validation,
        "blind_spots": blind_spots,
        "redundancies": redundancies,
        "graduation_readiness": graduation_readiness,
        "completion_reference": completion_summary,
        "recommended_next_action": recommended_next_action,
        "readiness_definition": RECURRENCE_GRADUATION_AUDIT_READINESS_DEFINITION,
    }
    recurrence_graduation_audit_summary = summarize_recurrence_graduation_audit(audit_without_summary)
    return {
        **audit_without_summary,
        "recurrence_graduation_audit_summary": recurrence_graduation_audit_summary,
    }


def render_recurrence_graduation_audit_report_markdown(
    audit: Mapping[str, Any] | None,
    *,
    generated_at: str | None = None,
) -> str:
    """Render the standalone BQ16 recurrence graduation audit report."""
    payload = audit if isinstance(audit, Mapping) else {}
    summary = payload.get("recurrence_graduation_audit_summary")
    if not isinstance(summary, Mapping):
        summary = summarize_recurrence_graduation_audit(payload)
    readiness = payload.get("graduation_readiness")
    if not isinstance(readiness, Mapping):
        readiness = {}
    generated_at_s = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    lines = [
        "# BQ16 Recurrence Graduation Audit",
        "",
        f"**Date:** {generated_at_s}",
        f"**Protected replay only:** true",
        "",
        *render_recurrence_graduation_audit_governance_preamble_markdown(payload, summary=summary),
        "## Graduation Readiness",
        "",
        f"- Graduation readiness score: `{float(summary.get('graduation_readiness_score') or 0.0):.1f}`",
        f"- Readiness level: `{summary.get('readiness_label') or 'unknown'}`",
        f"- Program graduated: `{str(bool(summary.get('program_graduated'))).lower()}`",
        f"- Recommended next action: {summary.get('recommended_next_action') or 'none recorded'}",
        "",
        "# Capability Coverage",
        "",
        "| Capability | Implemented | Validated | Operational | Confidence |",
        "|---|---|---|---|---:|",
    ]
    for row in payload.get("capability_coverage") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"| {row.get('capability_label')} | `{str(bool(row.get('implemented'))).lower()}` | "
            f"`{str(bool(row.get('validated'))).lower()}` | `{str(bool(row.get('operational'))).lower()}` | "
            f"`{float(row.get('confidence') or 0.0):.2f}` |"
        )
    lines.extend(["", "# Completion Criteria Validation", ""])
    for row in payload.get("completion_criteria_validation") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- `{row.get('requirement')}` ({row.get('dimension')}): "
            f"current `{row.get('current_value')}`, target `{row.get('target_value')}`, "
            f"status `{row.get('status')}`"
        )
    lines.extend(["", "# Roadmap Validation", ""])
    for row in payload.get("roadmap_validation") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- {row.get('initiative_label')}: `{row.get('validation_status')}` — {row.get('rationale')}"
        )
    lines.extend(["", "# Effectiveness Validation", ""])
    for row in payload.get("effectiveness_validation") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- {row.get('metric')}: `{row.get('evidence_status')}` — {row.get('rationale')}"
        )
    lines.extend(["", "# Blind Spots", ""])
    for row in payload.get("blind_spots") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- **{row.get('blind_spot_id')}** ({row.get('severity')}): {row.get('description')}"
        )
    lines.extend(["", "# Redundancies", ""])
    for row in payload.get("redundancies") or ():
        if not isinstance(row, Mapping):
            continue
        lines.append(
            f"- **{row.get('redundancy_id')}** ({row.get('severity')}): {row.get('consolidation_recommendation')}"
        )
    lines.extend(
        [
            "",
            "# Recommended Actions",
            "",
            f"1. {summary.get('recommended_next_action') or 'Continue protected replay observation collection.'}",
            "2. Establish trajectory baseline before treating forecasting and operational readiness as graduation-ready.",
            "3. Keep maturity, effectiveness, and completion scores distinct in operator reporting to avoid redundant escalation.",
            "",
        ]
    )
    lines.extend(render_recurrence_graduation_audit_governance_cross_references_markdown())
    return "\n".join(lines)


def enrich_recurrence_history_with_graduation_audit(
    history: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a history payload with additive protected replay graduation audit fields."""
    payload = dict(history)
    audit = build_recurrence_graduation_audit(
        recurrence_history=payload,
        recurrence_trends=payload.get("recurrence_trends")
        if isinstance(payload.get("recurrence_trends"), Mapping)
        else None,
        recurrence_forecast=payload.get("recurrence_forecast")
        if isinstance(payload.get("recurrence_forecast"), Mapping)
        else None,
        recurrence_portfolio=payload.get("recurrence_portfolio")
        if isinstance(payload.get("recurrence_portfolio"), Mapping)
        else None,
        recurrence_remediation=payload.get("recurrence_remediation_targets")
        if isinstance(payload.get("recurrence_remediation_targets"), Mapping)
        else None,
        recurrence_roi=payload.get("recurrence_roi")
        if isinstance(payload.get("recurrence_roi"), Mapping)
        else None,
        recurrence_governance=payload.get("recurrence_governance")
        if isinstance(payload.get("recurrence_governance"), Mapping)
        else None,
        recurrence_lifecycle=payload.get("recurrence_lifecycle")
        if isinstance(payload.get("recurrence_lifecycle"), Mapping)
        else None,
        recurrence_program_effectiveness=payload.get("recurrence_program_effectiveness")
        if isinstance(payload.get("recurrence_program_effectiveness"), Mapping)
        else None,
        recurrence_maturity=payload.get("recurrence_maturity")
        if isinstance(payload.get("recurrence_maturity"), Mapping)
        else None,
        recurrence_roadmap=payload.get("recurrence_roadmap")
        if isinstance(payload.get("recurrence_roadmap"), Mapping)
        else None,
        recurrence_completion=payload.get("recurrence_completion")
        if isinstance(payload.get("recurrence_completion"), Mapping)
        else None,
    )
    payload["recurrence_graduation_audit"] = audit
    payload["recurrence_graduation_audit_summary"] = audit["recurrence_graduation_audit_summary"]
    return payload
