"""Recurrence report rendering and artifact orchestration for replay diagnostics.

Consumes recurrence analytics from replay_bug_recurrence.py and paths from
failure_dashboard_paths.py. Does not own session buffers or generic dashboard rendering.
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.helpers.failure_dashboard_paths import (
    BUG_RECURRENCE_HISTORY_JSON_PATH,
    BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    PROTECTED_REPLAY_FAILURE_REPORT_PATH,
    bug_recurrence_event_log_path as _bug_recurrence_event_log_path,
    bug_recurrence_session_diagnostic_event_log_path as _bug_recurrence_session_diagnostic_event_log_path,
    bug_recurrence_trajectory_history_path as _bug_recurrence_trajectory_history_path,
)
from tests.helpers.replay_bug_recurrence import (
    PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
    RECURRENCE_CONFIDENCE_CALIBRATION_DOC_PATH,
    RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH,
    RECURRENCE_GRADUATION_AUDIT_DOC_PATH,
    RECURRENCE_OUTCOME_VALIDATION_DOC_PATH,
    RECURRENCE_TRAJECTORY_BASELINE_MESSAGE,
    aggregate_protected_recurrence_history_from_event_log,
    append_recurrence_events_to_persistence_lanes,
    apply_recurrence_trajectory_to_analytics,
    build_recurrence_completion_assessment,
    build_recurrence_confidence_audit,
    build_recurrence_final_graduation_decision,
    build_recurrence_forecast,
    build_recurrence_governance,
    build_recurrence_graduation_audit,
    build_recurrence_lifecycle,
    build_recurrence_maturity_assessment,
    build_recurrence_outcome_validation,
    build_recurrence_portfolio,
    build_recurrence_program_effectiveness,
    build_recurrence_remediation_targets,
    build_recurrence_roi_analysis,
    build_recurrence_strategic_roadmap,
    build_recurrence_timeline,
    build_recurrence_trend_summary,
    calculate_regression_recurrence_rate,
    load_recurrence_event_log,
    normalize_recurrence_event_metadata,
    render_recurrence_confidence_calibration_report_markdown,
    render_recurrence_final_graduation_decision_report_markdown,
    render_recurrence_graduation_audit_report_markdown,
    render_recurrence_outcome_validation_report_markdown,
    write_recurrence_event_log,
)
from tests.helpers.replay_drift_reports import aggregate_recurrence_history, build_recurrence_summary


def _cell(value: Any) -> str:
    if value is None or value == "":
        text = "none"
    elif isinstance(value, (list, tuple, set, frozenset)):
        text = ", ".join(str(item) for item in value if str(item).strip()) or "none"
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def _regression_recurrence_rate_markdown_lines(metric: Mapping[str, Any]) -> list[str]:
    numerator = int(metric.get("numerator") or 0)
    denominator = int(metric.get("denominator") or 0)
    rate = float(metric.get("rate") or 0.0)
    pct_text = f"{rate * 100.0:.1f}%" if denominator else "0.0%"
    return [
        "## Regression Recurrence Rate",
        "",
        (
            f"Regression Recurrence Rate: {pct_text} ({numerator} / {denominator} "
            "recurrence keys active by repeated observation). "
            "This is advisory/report-only and does not gate protected replay."
        ),
        "",
        f"- Definition: {metric.get('definition')}",
        f"- Interpretation: {metric.get('interpretation')}",
        f"- Report only: `{str(bool(metric.get('report_only', True))).lower()}`",
        f"- Advisory only: `{str(bool(metric.get('advisory_only', True))).lower()}`",
        "",
    ]


def _recurrence_trends_markdown_lines(
    trends: Mapping[str, Any] | None,
    *,
    timeline: Sequence[Mapping[str, Any]] | None = None,
) -> list[str]:
    """Render protected replay recurrence trend section for history markdown."""
    payload = trends if isinstance(trends, Mapping) else {}
    total_keys = int(payload.get("total_keys") or 0)
    growth_rate = float(payload.get("growth_rate") or 0.0)
    regression = payload.get("regression_recurrence_rate")
    if not isinstance(regression, Mapping):
        regression = {}
    regression_numerator = int(regression.get("numerator") or 0)
    regression_denominator = int(regression.get("denominator") or 0)
    regression_rate = float(regression.get("rate") or 0.0)
    regression_pct = (
        f"{regression_rate * 100.0:.1f}%"
        if regression_denominator
        else "0.0%"
    )
    lines = [
        "## Recurrence Trends",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Total protected recurrence keys: `{total_keys}`",
        f"- Emerging keys: `{int(payload.get('emerging_keys') or 0)}`",
        f"- Recurring keys: `{int(payload.get('recurring_keys') or 0)}`",
        f"- Persistent keys: `{int(payload.get('persistent_keys') or 0)}`",
        f"- Dormant keys: `{int(payload.get('dormant_keys') or 0)}`",
        (
            f"- Growth rate: `{growth_rate * 100.0:.1f}%` "
            f"({int(payload.get('emerging_keys') or 0)} / {total_keys or 0} keys emerging)"
        ),
        (
            f"- Regression recurrence rate: `{regression_pct}` "
            f"({regression_numerator} / {regression_denominator})"
        ),
        "",
    ]
    top_recurring = payload.get("top_recurring_keys")
    if isinstance(top_recurring, list) and top_recurring:
        lines.extend(["### Top Recurring Keys", ""])
        for row in top_recurring[:5]:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "- "
                + f"`{_cell(row.get('recurrence_key'))}` "
                + f"(count `{_cell(row.get('occurrence_count'))}`, "
                + f"class `{_cell(row.get('trend_classification'))}`)"
            )
        lines.append("")
    else:
        lines.extend(["### Top Recurring Keys", "", "No recurring protected keys yet.", ""])

    newest = payload.get("newest_recurrence_keys")
    if isinstance(newest, list) and newest:
        lines.extend(["### Newest Recurrence Keys", ""])
        for row in newest[:5]:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "- "
                + f"`{_cell(row.get('recurrence_key'))}` "
                + f"(first seen `{_cell(row.get('first_seen'))}`, "
                + f"class `{_cell(row.get('trend_classification'))}`)"
            )
        lines.append("")
    elif isinstance(timeline, Sequence) and timeline:
        lines.extend(["### Newest Recurrence Keys", ""])
        for row in list(timeline)[-5:][::-1]:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "- "
                + f"`{_cell(row.get('recurrence_key'))}` "
                + f"(first seen `{_cell(row.get('first_seen'))}`, "
                + f"class `{_cell(row.get('trend_classification'))}`)"
            )
        lines.append("")
    else:
        lines.extend(["### Newest Recurrence Keys", "", "No protected recurrence keys recorded.", ""])
    return lines


def _recurrence_forecast_markdown_lines(forecast: Mapping[str, Any] | None) -> list[str]:
    """Render protected replay recurrence forecast section for history markdown."""
    payload = forecast if isinstance(forecast, Mapping) else {}
    summary = payload.get("forecast_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    risk = payload.get("risk_concentration")
    if not isinstance(risk, Mapping):
        risk = {}
    confidence = float(summary.get("forecast_confidence") or 0.0)
    confidence_label = "low" if confidence < 0.5 else "moderate" if confidence < 0.8 else "high"
    lines = [
        "## Recurrence Forecast",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Forecast confidence: `{confidence_label}` (`{confidence:.2f}`)",
        f"- Stable keys: `{int(summary.get('stable_keys') or 0)}`",
        f"- Watch keys: `{int(summary.get('watch_keys') or 0)}`",
        f"- Elevated keys: `{int(summary.get('elevated_keys') or 0)}`",
        f"- Concentrated keys: `{int(summary.get('concentrated_keys') or 0)}`",
        f"- Forecast risk score: `{float(summary.get('forecast_risk_score') or 0.0):.1f}` / 100",
        f"- Stability score: `{float(summary.get('stability_score') or 0.0):.1f}` / 100",
        "",
        "### Concentration Metrics",
        "",
        f"- Top key share: `{float(risk.get('top_key_share') or 0.0) * 100.0:.1f}%`",
        f"- Top three key share: `{float(risk.get('top_three_key_share') or 0.0) * 100.0:.1f}%`",
        f"- Concentration ratio (HHI): `{float(risk.get('concentration_ratio') or 0.0):.4f}`",
        f"- Dominant recurrence key: `{_cell(risk.get('dominant_recurrence_key'))}`",
        "",
    ]
    key_forecasts = payload.get("key_forecasts")
    if isinstance(key_forecasts, list) and key_forecasts:
        lines.extend(["### Key Forecasts", ""])
        for row in key_forecasts[:5]:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "- "
                + f"`{_cell(row.get('recurrence_key'))}` "
                + f"(forecast `{_cell(row.get('forecast_classification'))}`, "
                + f"trend `{_cell(row.get('trend_classification'))}`, "
                + f"share `{float(row.get('observation_share') or 0.0) * 100.0:.1f}%`)"
            )
        lines.append("")
    else:
        lines.extend(["### Key Forecasts", "", "No protected recurrence keys to forecast.", ""])
    return lines


def _portfolio_bucket_markdown_lines(
    heading: str,
    rows: Sequence[Mapping[str, Any]] | None,
    *,
    label_field: str,
    extra_fields: Sequence[tuple[str, str]] = (),
) -> list[str]:
    """Render ranked portfolio bucket lines for one dimension."""
    lines = [heading, ""]
    if not rows:
        lines.extend(["No protected recurrence observations recorded.", ""])
        return lines
    for row in rows[:5]:
        if not isinstance(row, Mapping):
            continue
        parts = [
            f"`{_cell(row.get(label_field))}`",
            f"keys `{_cell(row.get('recurrence_keys'))}`",
            f"obs `{_cell(row.get('observations'))}`",
            f"share `{float(row.get('risk_share') or 0.0) * 100.0:.1f}%`",
        ]
        for extra_label, extra_field in extra_fields:
            parts.append(f"{extra_label} `{_cell(row.get(extra_field))}`")
        lines.append("- " + ", ".join(parts))
    lines.append("")
    return lines


def _recurrence_portfolio_markdown_lines(
    portfolio: Mapping[str, Any] | None,
    *,
    portfolio_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence portfolio section for history markdown."""
    payload = portfolio if isinstance(portfolio, Mapping) else {}
    summary = portfolio_summary if isinstance(portfolio_summary, Mapping) else payload.get("portfolio_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    largest = summary.get("largest_risk_bucket")
    if not isinstance(largest, Mapping):
        largest = {}
    lines = [
        "## Recurrence Portfolio",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Portfolio risk score: `{float(summary.get('portfolio_risk_score') or 0.0):.1f}` / 100",
        (
            "- Largest risk bucket: "
            f"`{_cell(largest.get('dimension'))}` / `{_cell(largest.get('label'))}` "
            f"(HHI `{float(largest.get('concentration_ratio') or 0.0):.4f}`)"
        ),
        f"- Forecast confidence: `{float(summary.get('forecast_confidence') or 0.0):.2f}`",
        "",
        "### Portfolio Metrics",
        "",
        f"- Owner concentration ratio: `{float(summary.get('owner_concentration_ratio') or 0.0):.4f}`",
        f"- Category concentration ratio: `{float(summary.get('category_concentration_ratio') or 0.0):.4f}`",
        f"- Field path concentration ratio: `{float(summary.get('field_path_concentration_ratio') or 0.0):.4f}`",
        f"- Scenario concentration ratio: `{float(summary.get('scenario_concentration_ratio') or 0.0):.4f}`",
        "",
    ]
    lines.extend(
        _portfolio_bucket_markdown_lines(
            "### Top Owners",
            payload.get("owners") if isinstance(payload.get("owners"), list) else None,
            label_field="owner",
            extra_fields=(("recurring", "recurring_keys"), ("elevated", "elevated_keys")),
        )
    )
    lines.extend(
        _portfolio_bucket_markdown_lines(
            "### Top Categories",
            payload.get("categories") if isinstance(payload.get("categories"), list) else None,
            label_field="category",
        )
    )
    lines.extend(
        _portfolio_bucket_markdown_lines(
            "### Top Field Paths",
            payload.get("field_paths") if isinstance(payload.get("field_paths"), list) else None,
            label_field="field_path",
        )
    )
    lines.extend(
        _portfolio_bucket_markdown_lines(
            "### Top Scenarios",
            payload.get("scenarios") if isinstance(payload.get("scenarios"), list) else None,
            label_field="scenario_id",
        )
    )
    return lines


def _remediation_bucket_markdown_lines(
    heading: str,
    rows: Sequence[Mapping[str, Any]] | None,
    *,
    label_field: str,
    extra_fields: Sequence[tuple[str, str]] = (),
) -> list[str]:
    lines = [heading, ""]
    if not rows:
        lines.extend(["No remediation targets recorded.", ""])
        return lines
    for row in rows[:5]:
        if not isinstance(row, Mapping):
            continue
        parts = [
            f"`{_cell(row.get(label_field))}`",
            f"priority `{_cell(row.get('remediation_priority'))}`",
            f"reduction `{float(row.get('reduction_potential') or 0.0):.1f}`",
            f"share `{float(row.get('risk_share') or 0.0) * 100.0:.1f}%`",
        ]
        for extra_label, extra_field in extra_fields:
            parts.append(f"{extra_label} `{_cell(row.get(extra_field))}`")
        lines.append("- " + ", ".join(parts))
    lines.append("")
    return lines


def _recurrence_remediation_markdown_lines(
    targets: Mapping[str, Any] | None,
    *,
    remediation_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence remediation section for history markdown."""
    payload = targets if isinstance(targets, Mapping) else {}
    summary = remediation_summary if isinstance(remediation_summary, Mapping) else payload.get("remediation_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    highest = summary.get("highest_leverage_target")
    if not isinstance(highest, Mapping):
        highest = {}
    lines = [
        "## Recurrence Remediation Targets",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        (
            "- Highest leverage target: "
            f"`{_cell(highest.get('dimension') or summary.get('highest_leverage_key'))}` / "
            f"`{_cell(highest.get('label') or summary.get('highest_leverage_key'))}` "
            f"(priority `{_cell(highest.get('remediation_priority'))}`)"
        ),
        f"- Estimated portfolio reduction: `{float(summary.get('estimated_portfolio_reduction') or 0.0):.1f}`",
        f"- Remediation confidence: `{float(summary.get('remediation_confidence') or 0.0):.2f}`",
        "",
    ]
    lines.extend(
        _remediation_bucket_markdown_lines(
            "### Top Keys",
            payload.get("keys") if isinstance(payload.get("keys"), list) else None,
            label_field="recurrence_key",
            extra_fields=(("trend", "trend_classification"), ("forecast", "forecast_classification")),
        )
    )
    lines.extend(
        _remediation_bucket_markdown_lines(
            "### Top Owners",
            payload.get("owners") if isinstance(payload.get("owners"), list) else None,
            label_field="owner",
            extra_fields=(("keys", "recurrence_keys"),),
        )
    )
    lines.extend(
        _remediation_bucket_markdown_lines(
            "### Top Field Paths",
            payload.get("field_paths") if isinstance(payload.get("field_paths"), list) else None,
            label_field="field_path",
        )
    )
    lines.extend(
        _remediation_bucket_markdown_lines(
            "### Top Scenarios",
            payload.get("scenarios") if isinstance(payload.get("scenarios"), list) else None,
            label_field="scenario_id",
        )
    )
    return lines


def _roi_bucket_markdown_lines(
    heading: str,
    rows: Sequence[Mapping[str, Any]] | None,
    *,
    label_field: str,
) -> list[str]:
    lines = [heading, ""]
    if not rows:
        lines.extend(["No ROI targets recorded.", ""])
        return lines
    for row in rows[:5]:
        if not isinstance(row, Mapping):
            continue
        parts = [
            f"rank `{int(row.get('roi_rank') or 0)}`",
            f"`{_cell(row.get(label_field))}`",
            f"ROI `{float(row.get('roi_score') or 0.0):.1f}`",
            f"cost `{_cell(row.get('cost_classification'))}`",
            f"benefit `{float(row.get('expected_benefit') or 0.0):.1f}`",
        ]
        lines.append("- " + ", ".join(parts))
    lines.append("")
    return lines


def _recurrence_roi_markdown_lines(
    analysis: Mapping[str, Any] | None,
    *,
    roi_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence ROI section for history markdown."""
    payload = analysis if isinstance(analysis, Mapping) else {}
    summary = roi_summary if isinstance(roi_summary, Mapping) else payload.get("roi_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    highest = summary.get("highest_roi_target")
    if not isinstance(highest, Mapping):
        highest = {}
    lines = [
        "## Recurrence ROI",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        (
            "- Highest ROI target: "
            f"`{_cell(highest.get('dimension') or 'key')}` / "
            f"`{_cell(highest.get('label'))}` "
            f"(ROI `{float(highest.get('roi_score') or summary.get('portfolio_roi_score') or 0.0):.1f}`, "
            f"cost `{_cell(highest.get('cost_classification'))}`)"
        ),
        f"- Portfolio ROI score: `{float(summary.get('portfolio_roi_score') or 0.0):.1f}`",
        f"- Projected stability gain: `{float(summary.get('projected_stability_gain') or 0.0):.1f}`",
        f"- Projected risk reduction: `{float(summary.get('projected_risk_reduction') or 0.0):.1f}`",
        f"- ROI confidence: `{float(summary.get('roi_confidence') or 0.0):.2f}`",
        "",
    ]
    lines.extend(
        _roi_bucket_markdown_lines(
            "### Top ROI Targets",
            payload.get("keys") if isinstance(payload.get("keys"), list) else None,
            label_field="recurrence_key",
        )
    )
    lines.extend(
        _roi_bucket_markdown_lines(
            "### Top ROI Owners",
            payload.get("owners") if isinstance(payload.get("owners"), list) else None,
            label_field="owner",
        )
    )
    lines.extend(
        _roi_bucket_markdown_lines(
            "### Top ROI Field Paths",
            payload.get("field_paths") if isinstance(payload.get("field_paths"), list) else None,
            label_field="field_path",
        )
    )
    lines.extend(
        _roi_bucket_markdown_lines(
            "### Top ROI Scenarios",
            payload.get("scenarios") if isinstance(payload.get("scenarios"), list) else None,
            label_field="scenario_id",
        )
    )
    return lines


def _governance_watchlist_markdown_lines(
    heading: str,
    rows: Sequence[Mapping[str, Any]] | None,
) -> list[str]:
    lines = [heading, ""]
    if not rows:
        lines.extend(["No watchlist entries recorded.", ""])
        return lines
    for row in rows[:5]:
        if not isinstance(row, Mapping):
            continue
        parts = [
            f"`{_cell(row.get('recurrence_key'))}`",
            f"status `{_cell(row.get('governance_status'))}`",
            f"action `{_cell(row.get('recommended_action'))}`",
            f"ROI `{float(row.get('roi_score') or 0.0):.1f}`",
            f"trend `{_cell(row.get('trend_classification'))}`",
            f"forecast `{_cell(row.get('forecast_classification'))}`",
        ]
        lines.append("- " + ", ".join(parts))
    lines.append("")
    return lines


def _recurrence_governance_markdown_lines(
    governance: Mapping[str, Any] | None,
    *,
    governance_summary: Mapping[str, Any] | None = None,
    watchlist: Sequence[Mapping[str, Any]] | None = None,
    retirement_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence governance section for history markdown."""
    payload = governance if isinstance(governance, Mapping) else {}
    summary = governance_summary if isinstance(governance_summary, Mapping) else payload.get("governance_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    entries = watchlist if watchlist is not None else payload.get("watchlist")
    if not isinstance(entries, list):
        entries = []
    retirement = retirement_summary if isinstance(retirement_summary, Mapping) else payload.get("retirement_summary")
    if not isinstance(retirement, Mapping):
        retirement = {}
    owners = payload.get("owners") if isinstance(payload.get("owners"), list) else []
    prioritized = [
        row for row in entries if isinstance(row, Mapping) and row.get("governance_status") == "prioritize"
    ]
    retire_candidates = [
        row
        for row in entries
        if isinstance(row, Mapping) and row.get("governance_status") == "retire_candidate"
    ]
    lines = [
        "## Recurrence Governance",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Governance health score: `{float(summary.get('governance_health_score') or 0.0):.1f}`",
        f"- Governance confidence: `{float(summary.get('governance_confidence') or 0.0):.2f}`",
        f"- Watchlist size: `{int(summary.get('watchlist_size') or 0)}`",
        f"- Prioritized targets: `{int(summary.get('prioritized_targets') or 0)}`",
        f"- Retirement opportunities: `{int(summary.get('retirement_opportunities') or retirement.get('retirement_opportunities') or 0)}`",
        "",
    ]
    lines.extend(_governance_watchlist_markdown_lines("### Watchlist", entries))
    lines.extend(_governance_watchlist_markdown_lines("### Prioritized Targets", prioritized))
    lines.extend(_governance_watchlist_markdown_lines("### Retire Candidates", retire_candidates))
    lines.extend(["### Owner Accountability", ""])
    if not owners:
        lines.extend(["No owner governance metrics recorded.", ""])
    else:
        for row in owners[:5]:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "- "
                + ", ".join(
                    [
                        f"`{_cell(row.get('owner'))}`",
                        f"governed `{int(row.get('governed_keys') or 0)}`",
                        f"watch `{int(row.get('watch_keys') or 0)}`",
                        f"prioritized `{int(row.get('prioritized_keys') or 0)}`",
                        f"retire `{int(row.get('retire_candidates') or 0)}`",
                    ]
                )
            )
        load_owner = summary.get("highest_governance_load_owner") or payload.get("highest_governance_load_owner")
        if load_owner:
            lines.append(f"- Highest governance load owner: `{_cell(load_owner)}`")
        lines.append("")
    return lines


def _recurrence_lifecycle_markdown_lines(
    lifecycle: Mapping[str, Any] | None,
    *,
    lifecycle_summary: Mapping[str, Any] | None = None,
    age_distribution: Mapping[str, Any] | None = None,
    transition_summary: Mapping[str, Any] | None = None,
    closure_effectiveness: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence lifecycle section for history markdown."""
    payload = lifecycle if isinstance(lifecycle, Mapping) else {}
    summary = lifecycle_summary if isinstance(lifecycle_summary, Mapping) else payload.get("lifecycle_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    ages = age_distribution if isinstance(age_distribution, Mapping) else payload.get("age_distribution")
    if not isinstance(ages, Mapping):
        ages = {}
    transitions = transition_summary if isinstance(transition_summary, Mapping) else payload.get("transition_summary")
    if not isinstance(transitions, Mapping):
        transitions = {}
    closure = closure_effectiveness if isinstance(closure_effectiveness, Mapping) else payload.get("closure_effectiveness")
    if not isinstance(closure, Mapping):
        closure = {}
    distribution = payload.get("lifecycle_distribution")
    if not isinstance(distribution, Mapping):
        distribution = {}

    lines = [
        "## Recurrence Lifecycle",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Lifecycle health score: `{float(summary.get('lifecycle_health_score') or 0.0):.1f}`",
        f"- Closure rate: `{float(summary.get('closure_rate') or 0.0) * 100.0:.1f}%`",
        f"- Average age (days): `{float(summary.get('average_age_days') or 0.0):.1f}`",
        f"- Advancement rate: `{float(summary.get('advancement_rate') or 0.0):.2f}`",
        "",
        "### Lifecycle Distribution",
        "",
    ]
    if not distribution:
        lines.extend(["No lifecycle distribution recorded.", ""])
    else:
        for stage, count in sorted(distribution.items()):
            lines.append(f"- `{_cell(stage)}`: `{int(count or 0)}`")
        lines.append("")

    lines.extend(
        [
            "### Age Distribution",
            "",
            f"- Youngest key: `{_cell(ages.get('youngest_key'))}`",
            f"- Oldest key: `{_cell(ages.get('oldest_key'))}`",
            f"- Average age (days): `{float(ages.get('average_age_days') or 0.0):.1f}`",
            f"- Median age (days): `{float(ages.get('median_age_days') or 0.0):.1f}`",
            "",
            "### Transition Summary",
            "",
            f"- Transition count: `{int(transitions.get('transition_count') or 0)}`",
            f"- Advancing transitions: `{int(transitions.get('advancing_transitions') or 0)}`",
            f"- Retiring transitions: `{int(transitions.get('retiring_transitions') or 0)}`",
            f"- Stalled keys: `{int(transitions.get('stalled_key_count') or 0)}`",
            "",
            "### Closure Effectiveness",
            "",
            f"- Active keys: `{int(closure.get('active_keys') or 0)}`",
            f"- Dormant keys: `{int(closure.get('dormant_keys') or 0)}`",
            f"- Retired keys: `{int(closure.get('retired_keys') or 0)}`",
            f"- Closure rate: `{float(closure.get('closure_rate') or 0.0) * 100.0:.1f}%`",
            "",
        ]
    )
    return lines


def _recurrence_trajectory_markdown_lines(
    trajectory_history: Mapping[str, Any] | None,
    *,
    trajectory_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence trajectory section."""
    history = trajectory_history if isinstance(trajectory_history, Mapping) else {}
    summary = trajectory_summary if isinstance(trajectory_summary, Mapping) else {}
    baseline = summary.get("baseline_snapshot")
    current = summary.get("current_snapshot")
    if not isinstance(baseline, Mapping):
        baseline = {}
    if not isinstance(current, Mapping):
        current = {}
    lines = [
        "## Recurrence Trajectory",
        "",
        f"- Trajectory available: `{str(bool(summary.get('trajectory_available', False))).lower()}`",
        f"- Snapshot count: `{int(summary.get('snapshot_count') or len(history.get('snapshots') or []))}`",
        "",
        "### Current Snapshot",
        "",
        f"- Timestamp: `{_cell(current.get('timestamp'))}`",
        f"- Protected observations: `{int(current.get('protected_observation_count') or 0)}`",
        f"- Unique recurrence keys: `{int(current.get('unique_recurrence_keys') or 0)}`",
        f"- Portfolio risk score: `{float(current.get('portfolio_risk_score') or 0.0):.1f}`",
        f"- Governance health score: `{float(current.get('governance_health_score') or 0.0):.1f}`",
        f"- Operational readiness score: `{float(current.get('operational_readiness_score') or 0.0):.1f}`",
        f"- Effectiveness confidence: `{float(current.get('effectiveness_score') or 0.0):.2f}`",
        f"- Maturity score: `{float(current.get('maturity_score') or 0.0):.1f}`",
        "",
        "### Baseline Snapshot",
        "",
        f"- Timestamp: `{_cell(baseline.get('timestamp'))}`",
        f"- Protected observations: `{int(baseline.get('protected_observation_count') or 0)}`",
        f"- Unique recurrence keys: `{int(baseline.get('unique_recurrence_keys') or 0)}`",
        f"- Portfolio risk score: `{float(baseline.get('portfolio_risk_score') or 0.0):.1f}`",
        f"- Governance health score: `{float(baseline.get('governance_health_score') or 0.0):.1f}`",
        f"- Operational readiness score: `{float(baseline.get('operational_readiness_score') or 0.0):.1f}`",
        f"- Effectiveness confidence: `{float(baseline.get('effectiveness_score') or 0.0):.2f}`",
        f"- Maturity score: `{float(baseline.get('maturity_score') or 0.0):.1f}`",
        "",
        "### Trajectory Availability",
        "",
    ]
    message = str(summary.get("message") or "").strip()
    if message:
        lines.append(message)
    else:
        lines.append(RECURRENCE_TRAJECTORY_BASELINE_MESSAGE)
    lines.append("")
    if bool(summary.get("trajectory_available")):
        lines.extend(
            [
                "### Trajectory Changes",
                "",
                f"- Portfolio risk change: `{float(summary.get('portfolio_risk_change') or 0.0):+.1f}`",
                f"- Governance health change: `{float(summary.get('governance_health_change') or 0.0):+.1f}`",
                f"- Lifecycle health change: `{float(summary.get('lifecycle_health_change') or 0.0):+.1f}`",
                f"- Operational readiness change: `{float(summary.get('operational_readiness_change') or 0.0):+.1f}`",
                f"- Effectiveness change: `{float(summary.get('effectiveness_change') or 0.0):+.2f}`",
                f"- Maturity change: `{float(summary.get('maturity_change') or 0.0):+.1f}`",
                "",
            ]
        )
    return lines


def _recurrence_program_effectiveness_markdown_lines(
    effectiveness: Mapping[str, Any] | None,
    *,
    program_summary: Mapping[str, Any] | None = None,
    governance_effectiveness: Mapping[str, Any] | None = None,
    remediation_effectiveness: Mapping[str, Any] | None = None,
    forecast_effectiveness: Mapping[str, Any] | None = None,
    portfolio_trajectory: Mapping[str, Any] | None = None,
    stability_trajectory: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence program effectiveness section."""
    payload = effectiveness if isinstance(effectiveness, Mapping) else {}
    summary = program_summary if isinstance(program_summary, Mapping) else payload.get("program_effectiveness_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    governance = (
        governance_effectiveness
        if isinstance(governance_effectiveness, Mapping)
        else payload.get("governance_effectiveness_summary")
    )
    if not isinstance(governance, Mapping):
        governance = {}
    remediation = (
        remediation_effectiveness
        if isinstance(remediation_effectiveness, Mapping)
        else payload.get("remediation_effectiveness_summary")
    )
    if not isinstance(remediation, Mapping):
        remediation = {}
    forecast = (
        forecast_effectiveness
        if isinstance(forecast_effectiveness, Mapping)
        else payload.get("forecast_effectiveness_summary")
    )
    if not isinstance(forecast, Mapping):
        forecast = {}
    portfolio = (
        portfolio_trajectory
        if isinstance(portfolio_trajectory, Mapping)
        else payload.get("portfolio_trajectory_summary")
    )
    if not isinstance(portfolio, Mapping):
        portfolio = {}
    stability = (
        stability_trajectory
        if isinstance(stability_trajectory, Mapping)
        else payload.get("stability_trajectory_summary")
    )
    if not isinstance(stability, Mapping):
        stability = {}

    lines = [
        "## Recurrence Program Effectiveness",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Program effectiveness score: `{float(summary.get('program_effectiveness_score') or 0.0):.1f}`",
        f"- Effectiveness confidence: `{float(summary.get('effectiveness_confidence') or 0.0):.2f}`",
        f"- Recurrence reduction rate: `{float(summary.get('recurrence_reduction_rate') or 0.0) * 100.0:.1f}%`",
        f"- Forecast accuracy: `{float(summary.get('forecast_accuracy') or 0.0) * 100.0:.1f}%`",
        f"- Stability change: `{float(summary.get('stability_change') or 0.0):+.1f}`",
        "",
        "### Governance Effectiveness",
        "",
        f"- Watchlist conversion rate: `{float(governance.get('watchlist_conversion_rate') or 0.0) * 100.0:.1f}%`",
        f"- Investigate conversion rate: `{float(governance.get('investigate_conversion_rate') or 0.0) * 100.0:.1f}%`",
        f"- Prioritize conversion rate: `{float(governance.get('prioritize_conversion_rate') or 0.0) * 100.0:.1f}%`",
        f"- Retirement conversion rate: `{float(governance.get('retirement_conversion_rate') or 0.0) * 100.0:.1f}%`",
        f"- Governance effectiveness: `{float(governance.get('governance_effectiveness') or 0.0):.2f}`",
        "",
        "### Remediation Effectiveness",
        "",
        f"- Targeted keys: `{int(remediation.get('targeted_keys') or 0)}`",
        f"- Improved keys: `{int(remediation.get('improved_keys') or 0)}`",
        f"- Unresolved keys: `{int(remediation.get('unresolved_keys') or 0)}`",
        f"- Recurrence reduction rate: `{float(remediation.get('recurrence_reduction_rate') or 0.0) * 100.0:.1f}%`",
        "",
        "### Forecast Effectiveness",
        "",
        f"- Forecast accuracy: `{float(forecast.get('forecast_accuracy') or 0.0) * 100.0:.1f}%`",
        f"- Forecast confidence: `{float(forecast.get('forecast_confidence') or 0.0):.2f}`",
        f"- Predicted recurrences: `{int(forecast.get('predicted_recurrences') or 0)}`",
        f"- Realized recurrences: `{int(forecast.get('realized_recurrences') or 0)}`",
        f"- Low confidence: `{str(bool(forecast.get('low_confidence', False))).lower()}`",
        "",
        "### Portfolio Trajectory",
        "",
        f"- Trajectory available: `{str(bool(portfolio.get('trajectory_available', False))).lower()}`",
        f"- Portfolio risk change: `{float(portfolio.get('portfolio_risk_change') or 0.0):+.1f}`",
        f"- Concentration change: `{float(portfolio.get('concentration_change') or 0.0):+.4f}`",
        f"- Governance health change: `{float(portfolio.get('governance_health_change') or 0.0):+.1f}`",
        f"- Lifecycle health change: `{float(portfolio.get('lifecycle_health_change') or 0.0):+.1f}`",
        "",
        "### Stability Trajectory",
        "",
        f"- Trajectory available: `{str(bool(stability.get('trajectory_available', False))).lower()}`",
        f"- Stability score current: `{float(stability.get('stability_score_current') or 0.0):.1f}`",
        f"- Stability change: `{float(stability.get('stability_change') or 0.0):+.1f}`",
        f"- Recurrence rate change: `{float(stability.get('recurrence_rate_change') or 0.0):+.4f}`",
        "",
    ]
    return lines


def _recurrence_maturity_markdown_lines(
    maturity: Mapping[str, Any] | None,
    *,
    maturity_summary: Mapping[str, Any] | None = None,
    maturity_gap_analysis: Sequence[Mapping[str, Any]] | None = None,
) -> list[str]:
    """Render protected replay recurrence maturity assessment section."""
    payload = maturity if isinstance(maturity, Mapping) else {}
    summary = maturity_summary if isinstance(maturity_summary, Mapping) else payload.get("recurrence_maturity_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    gaps = [
        dict(row)
        for row in (maturity_gap_analysis or payload.get("maturity_gap_analysis") or ())
        if isinstance(row, Mapping)
    ]

    dimension_fields = (
        ("observability", "observability_maturity", summary.get("observability_score")),
        ("governance", "governance_maturity", summary.get("governance_score")),
        ("forecasting", "forecasting_maturity", summary.get("forecasting_score")),
        ("remediation", "remediation_maturity", summary.get("remediation_score")),
        ("lifecycle", "lifecycle_maturity", summary.get("lifecycle_score")),
        ("operational_readiness", "operational_readiness", summary.get("operational_readiness_score")),
    )

    lines = [
        "## Recurrence Maturity Assessment",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Overall maturity score: `{float(summary.get('overall_maturity_score') or 0.0):.1f}`",
        f"- Overall maturity level: `{str(summary.get('overall_maturity_level') or 'initial').replace('_', ' ').title()}`",
        f"- Highest dimension: `{summary.get('highest_dimension') or 'none'}`",
        f"- Lowest dimension: `{summary.get('lowest_dimension') or 'none'}`",
        "",
        "### Dimension Scores",
        "",
    ]
    for label, field_name, fallback_score in dimension_fields:
        dimension = payload.get(field_name)
        score = float(fallback_score or 0.0)
        if isinstance(dimension, Mapping):
            score = float(dimension.get("maturity_score") or score)
        lines.append(f"- {label.replace('_', ' ').title()}: `{score:.1f}`")

    lines.extend(["", "### Dimension Levels", ""])
    for label, field_name, _ in dimension_fields:
        dimension = payload.get(field_name)
        level = "initial"
        if isinstance(dimension, Mapping):
            level = str(dimension.get("maturity_level") or level)
        lines.append(f"- {label.replace('_', ' ').title()}: `{level.replace('_', ' ').title()}`")

    lines.extend(["", "### Capability Gaps", ""])
    if gaps:
        for row in gaps:
            lines.append(
                f"- {str(row.get('dimension') or 'unknown').replace('_', ' ').title()}: "
                f"current `{float(row.get('current_score') or 0.0):.1f}`, "
                f"target `{float(row.get('target_score') or 80.0):.1f}`, "
                f"gap `{float(row.get('gap') or 0.0):.1f}`"
            )
    else:
        lines.append("- No capability gaps recorded.")

    lines.extend(["", "### Improvement Priorities", ""])
    if gaps:
        for row in gaps:
            lines.append(
                f"- {str(row.get('dimension') or 'unknown').replace('_', ' ').title()}: "
                f"`{str(row.get('improvement_priority') or 'low')}`"
            )
    else:
        lines.append("- No improvement priorities recorded.")

    lines.append("")
    return lines


def _recurrence_roadmap_markdown_lines(
    roadmap: Mapping[str, Any] | None,
    *,
    roadmap_summary: Mapping[str, Any] | None = None,
    target_state: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence strategic roadmap section."""
    payload = roadmap if isinstance(roadmap, Mapping) else {}
    summary = roadmap_summary if isinstance(roadmap_summary, Mapping) else payload.get("recurrence_roadmap_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    target = target_state if isinstance(target_state, Mapping) else payload.get("recurrence_target_state")
    if not isinstance(target, Mapping):
        target = {}
    initiatives = [row for row in (payload.get("initiatives") or ()) if isinstance(row, Mapping)]
    sequence = [row for row in (payload.get("roadmap_sequence") or ()) if isinstance(row, Mapping)]

    lines = [
        "## Recurrence Strategic Roadmap",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Highest ROI initiative: `{summary.get('highest_roi_initiative') or 'data_volume_expansion'}`",
        f"- Largest gap dimension: `{summary.get('highest_gap_dimension') or 'operational_readiness'}`",
        f"- Estimated remaining initiatives: `{int(summary.get('estimated_initiatives_remaining') or 0)}`",
        f"- Target maturity state: `{str(target.get('target_maturity_level') or 'optimized').replace('_', ' ').title()}`",
        f"- Roadmap priority: `{summary.get('roadmap_priority_guidance') or 'Collect more protected replay observations before optimizing models.'}`",
        "",
        "### Priority Initiatives",
        "",
    ]
    for row in initiatives[:6]:
        lines.append(
            f"- {str(row.get('initiative_label') or row.get('initiative_id'))}: "
            f"ROI `{float(row.get('maturity_roi') or 0.0):.1f}`, "
            f"priority `{float(row.get('investment_priority_score') or 0.0):.1f}`, "
            f"complexity `{float(row.get('implementation_complexity') or 0.0):.1f}`"
        )

    lines.extend(["", "### Expected Maturity Lift", ""])
    for row in initiatives[:6]:
        projected = row.get("projected_maturity_after_completion")
        if not isinstance(projected, Mapping):
            projected = {}
        lines.append(
            f"- {str(row.get('initiative_label') or row.get('initiative_id'))}: "
            f"projected overall `{float(projected.get('overall_maturity_score') or 0.0):.1f}` "
            f"(`{str(projected.get('overall_maturity_level') or 'initial').replace('_', ' ').title()}`)"
        )

    lines.extend(["", "### Dependency Sequence", ""])
    if sequence:
        for row in sequence:
            deps = ", ".join(str(dep) for dep in (row.get("dependencies") or ()))
            dep_text = deps if deps else "none"
            lines.append(
                f"- Step `{int(row.get('sequence_step') or 0)}`: "
                f"`{row.get('initiative_id')}` "
                f"(dependencies: {dep_text}, completed: `{str(bool(row.get('completed'))).lower()}`)"
            )
    else:
        lines.append("- No roadmap sequence recorded.")

    lines.extend(["", "### Target State", ""])
    criteria = target.get("completion_criteria")
    if isinstance(criteria, Mapping):
        for name, met in criteria.items():
            lines.append(f"- {str(name).replace('_', ' ').title()}: `{str(bool(met)).lower()}`")
    else:
        lines.append("- Target state criteria not defined.")

    lines.append("")
    return lines


def _recurrence_completion_markdown_lines(
    completion: Mapping[str, Any] | None,
    *,
    completion_summary: Mapping[str, Any] | None = None,
    completion_gap_analysis: Sequence[Mapping[str, Any]] | None = None,
) -> list[str]:
    """Render protected replay recurrence program completion section."""
    payload = completion if isinstance(completion, Mapping) else {}
    summary = (
        completion_summary
        if isinstance(completion_summary, Mapping)
        else payload.get("recurrence_completion_summary")
    )
    if not isinstance(summary, Mapping):
        summary = {}
    gaps = [
        dict(row)
        for row in (completion_gap_analysis or payload.get("completion_gap_analysis") or ())
        if isinstance(row, Mapping)
    ]
    dimension_fields = (
        ("observability", "observability_completion"),
        ("governance", "governance_completion"),
        ("forecasting", "forecasting_completion"),
        ("remediation", "remediation_completion"),
        ("lifecycle", "lifecycle_completion"),
        ("operational_readiness", "operational_readiness_completion"),
    )

    lines = [
        "## Recurrence Program Completion",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Overall completion score: `{float(summary.get('overall_completion_score') or 0.0):.1f}`",
        f"- Completed dimensions: `{len(summary.get('completed_dimensions') or [])}`",
        f"- Remaining dimensions: `{len(summary.get('remaining_dimensions') or [])}`",
        f"- Estimated completion distance: `{float(summary.get('estimated_completion_distance') or 0.0):.1f}`",
        f"- Graduation achieved: `{str(bool(summary.get('program_graduated'))).lower()}`",
        "",
        "### Dimension Completion Status",
        "",
    ]
    for label, field_name in dimension_fields:
        dimension = payload.get(field_name)
        if not isinstance(dimension, Mapping):
            dimension = {}
        status = "complete" if dimension.get("completion_met") else "incomplete"
        score = float(dimension.get("completion_score") or 0.0)
        lines.append(
            f"- {label.replace('_', ' ').title()}: `{status}` (score `{score:.1f}`)"
        )

    lines.extend(["", "### Remaining Requirements", ""])
    remaining = summary.get("remaining_requirements")
    if isinstance(remaining, list) and remaining:
        for requirement in remaining:
            lines.append(f"- `{requirement}`")
    else:
        lines.append("- No remaining requirements.")

    lines.extend(["", "### Completion Gaps", ""])
    if gaps:
        for row in gaps[:12]:
            lines.append(
                f"- {str(row.get('dimension') or 'unknown').replace('_', ' ').title()} / "
                f"`{row.get('requirement')}`: current `{row.get('current_value')}`, "
                f"target `{row.get('target_value')}`, gap `{float(row.get('gap') or 0.0):.2f}`, "
                f"roadmap `{row.get('roadmap_dependency')}`"
            )
    else:
        lines.append("- No completion gaps recorded.")

    lines.extend(["", "### Graduation Status", ""])
    lines.append(
        f"- Program graduated: `{str(bool(summary.get('program_graduated'))).lower()}`"
    )
    lines.append(
        f"- Completion criteria met: `{str(bool(summary.get('completion_criteria_met'))).lower()}`"
    )
    lines.append("")
    return lines


def _recurrence_graduation_audit_markdown_lines(
    audit: Mapping[str, Any] | None,
    *,
    audit_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence graduation audit section."""
    payload = audit if isinstance(audit, Mapping) else {}
    summary = audit_summary if isinstance(audit_summary, Mapping) else payload.get("recurrence_graduation_audit_summary")
    if not isinstance(summary, Mapping):
        summary = {}
    blind_spots = [row for row in (payload.get("blind_spots") or ()) if isinstance(row, Mapping)]
    redundancies = [row for row in (payload.get("redundancies") or ()) if isinstance(row, Mapping)]
    capabilities = [row for row in (payload.get("capability_coverage") or ()) if isinstance(row, Mapping)]

    lines = [
        "## Recurrence Graduation Audit",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Graduation readiness score: `{float(summary.get('graduation_readiness_score') or 0.0):.1f}`",
        f"- Readiness level: `{summary.get('readiness_label') or 'unknown'}`",
        f"- Critical blind spots: `{int(summary.get('critical_blind_spots') or 0)}`",
        f"- Critical redundancies: `{int(summary.get('critical_redundancies') or 0)}`",
        f"- Recommended next action: {summary.get('recommended_next_action') or 'none recorded'}",
        "",
        "### Capability Coverage",
        "",
    ]
    for row in capabilities:
        lines.append(
            f"- {row.get('capability_label')}: implemented `{str(bool(row.get('implemented'))).lower()}`, "
            f"validated `{str(bool(row.get('validated'))).lower()}`, operational `{str(bool(row.get('operational'))).lower()}`, "
            f"confidence `{float(row.get('confidence') or 0.0):.2f}`"
        )
    lines.extend(["", "### Blind Spots", ""])
    if blind_spots:
        for row in blind_spots:
            lines.append(
                f"- `{row.get('blind_spot_id')}` ({row.get('severity')}): {row.get('description')}"
            )
    else:
        lines.append("- No blind spots identified.")
    lines.extend(["", "### Redundancies", ""])
    if redundancies:
        for row in redundancies:
            lines.append(
                f"- `{row.get('redundancy_id')}` ({row.get('severity')}): {row.get('consolidation_recommendation')}"
            )
    else:
        lines.append("- No redundancies identified.")
    lines.extend(["", "### Graduation Readiness", ""])
    readiness = payload.get("graduation_readiness")
    if isinstance(readiness, Mapping):
        lines.append(f"- Operational capability ratio: `{float(readiness.get('operational_capability_ratio') or 0.0):.2f}`")
        lines.append(f"- Validated capability ratio: `{float(readiness.get('validated_capability_ratio') or 0.0):.2f}`")
        lines.append(f"- Average capability confidence: `{float(readiness.get('average_capability_confidence') or 0.0):.2f}`")
    lines.append(f"- Program graduated: `{str(bool(summary.get('program_graduated'))).lower()}`")
    lines.append("")
    return lines


def _recurrence_confidence_calibration_markdown_lines(
    audit: Mapping[str, Any] | None,
    *,
    calibration_summary: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render protected replay recurrence confidence calibration audit section."""
    payload = audit if isinstance(audit, Mapping) else {}
    summary = calibration_summary if isinstance(calibration_summary, Mapping) else payload.get(
        "recurrence_confidence_calibration_summary"
    )
    if not isinstance(summary, Mapping):
        summary = {}
    forecast = payload.get("forecast_confidence_audit")
    if not isinstance(forecast, Mapping):
        forecast = {}
    governance = payload.get("governance_confidence_audit")
    if not isinstance(governance, Mapping):
        governance = {}
    effectiveness = payload.get("effectiveness_confidence_audit")
    if not isinstance(effectiveness, Mapping):
        effectiveness = {}
    threshold_rows = [
        row for row in (payload.get("graduation_threshold_validation") or ()) if isinstance(row, Mapping)
    ]

    lines = [
        "## Confidence Calibration Audit",
        "",
        f"- Protected replay only: `{str(bool(payload.get('protected_replay_only', True))).lower()}`",
        f"- Calibration score: `{float(summary.get('confidence_calibration_score') or 0.0):.1f}`",
        f"- Interpretation: `{summary.get('interpretation_label') or 'unknown'}`",
        f"- Largest calibration gap: `{float(summary.get('largest_calibration_gap') or 0.0):.2f}`",
        f"- Graduation confidence ready: `{str(bool(summary.get('graduation_confidence_ready'))).lower()}`",
        "",
        "### Forecast Calibration",
        "",
        f"- Reported confidence: `{float(forecast.get('reported_confidence') or 0.0):.2f}`",
        f"- Evidence strength: `{float(forecast.get('evidence_strength') or 0.0):.2f}`",
        f"- Calibration gap: `{float(forecast.get('calibration_gap') or 0.0):.2f}`",
        f"- Status: `{forecast.get('confidence_status') or 'unknown'}`",
        "",
        "### Governance Calibration",
        "",
        f"- Reported confidence: `{float(governance.get('reported_confidence') or 0.0):.2f}`",
        f"- Evidence strength: `{float(governance.get('evidence_strength') or 0.0):.2f}`",
        f"- Calibration gap: `{float(governance.get('calibration_gap') or 0.0):.2f}`",
        f"- Status: `{governance.get('confidence_status') or 'unknown'}`",
        "",
        "### Effectiveness Calibration",
        "",
        f"- Reported confidence: `{float(effectiveness.get('reported_confidence') or 0.0):.2f}`",
        f"- Evidence strength: `{float(effectiveness.get('evidence_strength') or 0.0):.2f}`",
        f"- Calibration gap: `{float(effectiveness.get('calibration_gap') or 0.0):.2f}`",
        f"- Status: `{effectiveness.get('confidence_status') or 'unknown'}`",
        "",
        "### Graduation Threshold Validation",
        "",
    ]
    if threshold_rows:
        for row in threshold_rows:
            lines.append(
                f"- `{row.get('threshold')}`: current `{row.get('current_value')}`, "
                f"target `{row.get('target_value')}`, status `{row.get('validation_status')}`"
            )
    else:
        lines.append("- No graduation threshold validation recorded.")
    lines.append("")
    return lines


def render_bug_recurrence_history_markdown(
    history: Mapping[str, Any] | None,
    *,
    generated_at: str | None = None,
    command_used: str | None = None,
) -> str:
    """Render report-only bug-class recurrence history markdown."""
    payload = history if isinstance(history, Mapping) else aggregate_recurrence_history([])
    generated_at_s = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    command_s = command_used if command_used is not None else " ".join(sys.argv)
    summary_rows = build_recurrence_summary(payload)
    report_only = str(bool(payload.get("report_only", True))).lower()
    advisory_only = str(bool(payload.get("advisory_only", True))).lower()
    metric = payload.get("regression_recurrence_rate")
    if not isinstance(metric, Mapping):
        metric = calculate_regression_recurrence_rate(payload)
    lines = [
        "# Bug-Class Recurrence History",
        "",
        f"- Generated at: `{generated_at_s}`",
        f"- Command: `{command_s or 'unavailable'}`",
        f"- Report only: `{report_only}`",
        f"- Advisory only: `{advisory_only}`",
        f"- Total recurrence keys: `{int(payload.get('unique_recurrence_count') or 0)}`",
        f"- Total recurrence events: `{int(payload.get('total_rows') or 0)}`",
        "",
    ]
    lines.extend(_regression_recurrence_rate_markdown_lines(metric))
    trends = payload.get("recurrence_trends")
    timeline = payload.get("recurrence_timeline")
    if isinstance(trends, Mapping):
        lines.extend(
            _recurrence_trends_markdown_lines(
                trends,
                timeline=timeline if isinstance(timeline, list) else None,
            )
        )
    forecast = payload.get("recurrence_forecast")
    if isinstance(forecast, Mapping):
        lines.extend(_recurrence_forecast_markdown_lines(forecast))
    portfolio = payload.get("recurrence_portfolio")
    portfolio_summary = payload.get("recurrence_portfolio_summary")
    if isinstance(portfolio, Mapping):
        lines.extend(
            _recurrence_portfolio_markdown_lines(
                portfolio,
                portfolio_summary=portfolio_summary if isinstance(portfolio_summary, Mapping) else None,
            )
        )
    remediation = payload.get("recurrence_remediation_targets")
    remediation_summary = payload.get("recurrence_remediation_summary")
    if isinstance(remediation, Mapping):
        lines.extend(
            _recurrence_remediation_markdown_lines(
                remediation,
                remediation_summary=remediation_summary if isinstance(remediation_summary, Mapping) else None,
            )
        )
    roi = payload.get("recurrence_roi")
    roi_summary = payload.get("recurrence_roi_summary")
    if isinstance(roi, Mapping):
        lines.extend(
            _recurrence_roi_markdown_lines(
                roi,
                roi_summary=roi_summary if isinstance(roi_summary, Mapping) else None,
            )
        )
    governance = payload.get("recurrence_governance")
    governance_summary = payload.get("recurrence_governance_summary")
    watchlist = payload.get("recurrence_watchlist")
    retirement_summary = payload.get("recurrence_retirement_summary")
    if isinstance(governance, Mapping):
        lines.extend(
            _recurrence_governance_markdown_lines(
                governance,
                governance_summary=governance_summary if isinstance(governance_summary, Mapping) else None,
                watchlist=watchlist if isinstance(watchlist, list) else None,
                retirement_summary=retirement_summary if isinstance(retirement_summary, Mapping) else None,
            )
        )
    lifecycle = payload.get("recurrence_lifecycle")
    lifecycle_summary = payload.get("recurrence_lifecycle_summary")
    if isinstance(lifecycle, Mapping):
        lines.extend(
            _recurrence_lifecycle_markdown_lines(
                lifecycle,
                lifecycle_summary=lifecycle_summary if isinstance(lifecycle_summary, Mapping) else None,
                age_distribution=payload.get("recurrence_age_distribution")
                if isinstance(payload.get("recurrence_age_distribution"), Mapping)
                else None,
                transition_summary=payload.get("recurrence_transition_summary")
                if isinstance(payload.get("recurrence_transition_summary"), Mapping)
                else None,
                closure_effectiveness=payload.get("recurrence_closure_effectiveness")
                if isinstance(payload.get("recurrence_closure_effectiveness"), Mapping)
                else None,
            )
        )
    effectiveness = payload.get("recurrence_program_effectiveness")
    if isinstance(effectiveness, Mapping):
        lines.extend(
            _recurrence_program_effectiveness_markdown_lines(
                effectiveness,
                program_summary=payload.get("recurrence_program_effectiveness_summary")
                if isinstance(payload.get("recurrence_program_effectiveness_summary"), Mapping)
                else None,
                governance_effectiveness=payload.get("governance_effectiveness_summary")
                if isinstance(payload.get("governance_effectiveness_summary"), Mapping)
                else None,
                remediation_effectiveness=payload.get("remediation_effectiveness_summary")
                if isinstance(payload.get("remediation_effectiveness_summary"), Mapping)
                else None,
                forecast_effectiveness=payload.get("forecast_effectiveness_summary")
                if isinstance(payload.get("forecast_effectiveness_summary"), Mapping)
                else None,
                portfolio_trajectory=payload.get("portfolio_trajectory_summary")
                if isinstance(payload.get("portfolio_trajectory_summary"), Mapping)
                else None,
                stability_trajectory=payload.get("stability_trajectory_summary")
                if isinstance(payload.get("stability_trajectory_summary"), Mapping)
                else None,
            )
        )
    maturity = payload.get("recurrence_maturity")
    if isinstance(maturity, Mapping):
        lines.extend(
            _recurrence_maturity_markdown_lines(
                maturity,
                maturity_summary=payload.get("recurrence_maturity_summary")
                if isinstance(payload.get("recurrence_maturity_summary"), Mapping)
                else None,
                maturity_gap_analysis=payload.get("recurrence_maturity_gap_analysis")
                if isinstance(payload.get("recurrence_maturity_gap_analysis"), list)
                else None,
            )
        )
    roadmap = payload.get("recurrence_roadmap")
    if isinstance(roadmap, Mapping):
        lines.extend(
            _recurrence_roadmap_markdown_lines(
                roadmap,
                roadmap_summary=payload.get("recurrence_roadmap_summary")
                if isinstance(payload.get("recurrence_roadmap_summary"), Mapping)
                else None,
                target_state=payload.get("recurrence_target_state")
                if isinstance(payload.get("recurrence_target_state"), Mapping)
                else None,
            )
        )
    completion = payload.get("recurrence_completion")
    if isinstance(completion, Mapping):
        lines.extend(
            _recurrence_completion_markdown_lines(
                completion,
                completion_summary=payload.get("recurrence_completion_summary")
                if isinstance(payload.get("recurrence_completion_summary"), Mapping)
                else None,
                completion_gap_analysis=payload.get("recurrence_completion_gap_analysis")
                if isinstance(payload.get("recurrence_completion_gap_analysis"), list)
                else None,
            )
        )
    graduation_audit = payload.get("recurrence_graduation_audit")
    if isinstance(graduation_audit, Mapping):
        lines.extend(
            _recurrence_graduation_audit_markdown_lines(
                graduation_audit,
                audit_summary=payload.get("recurrence_graduation_audit_summary")
                if isinstance(payload.get("recurrence_graduation_audit_summary"), Mapping)
                else None,
            )
        )
    trajectory_history = payload.get("recurrence_trajectory_history")
    trajectory_summary = payload.get("recurrence_trajectory_summary")
    if isinstance(trajectory_history, Mapping) or isinstance(trajectory_summary, Mapping):
        lines.extend(
            _recurrence_trajectory_markdown_lines(
                trajectory_history if isinstance(trajectory_history, Mapping) else None,
                trajectory_summary=trajectory_summary if isinstance(trajectory_summary, Mapping) else None,
            )
        )
    confidence_audit = payload.get("recurrence_confidence_audit")
    if isinstance(confidence_audit, Mapping):
        lines.extend(
            _recurrence_confidence_calibration_markdown_lines(
                confidence_audit,
                calibration_summary=payload.get("recurrence_confidence_calibration_summary")
                if isinstance(payload.get("recurrence_confidence_calibration_summary"), Mapping)
                else None,
            )
        )
    if not summary_rows:
        lines.extend(["No recurrence history recorded.", ""])
        return "\n".join(lines)

    lines.extend(
        [
            "| Key | Count | Owner | Status | Categories | Field Paths | Affected Scenarios | Investigate First |",
            "|---|---:|---|---|---|---|---|---|",
        ]
    )
    for row in summary_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(row.get("recurrence_key")),
                    _cell(row.get("occurrence_count")),
                    _cell(row.get("owner")),
                    _cell(row.get("status")),
                    _cell(row.get("categories")),
                    _cell(row.get("field_paths")),
                    _cell(row.get("affected_scenarios")),
                    _cell(row.get("latest_investigate_first")),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def protected_replay_recurrence_event_metadata(
    *,
    command_used: str | None = None,
    generated_at: str | None = None,
    artifact_source: Path | str | None = None,
    persistence_intent: str | None = None,
) -> dict[str, Any]:
    """Build recurrence metadata for protected replay failure report writes."""
    artifact = str(artifact_source).strip() if artifact_source is not None else ""
    return normalize_recurrence_event_metadata(
        {
            "event_source": PROTECTED_REPLAY_FAILURE_EVENT_SOURCE,
            "recorded_at": generated_at,
            "command": command_used,
            "run_id": generated_at,
            "artifact_source": artifact or str(PROTECTED_REPLAY_FAILURE_REPORT_PATH),
            "persistence_intent": persistence_intent,
        }
    )


def write_bug_recurrence_history_artifacts(
    rows: Sequence[Mapping[str, Any]] | None = None,
    *,
    json_path: Path | str = BUG_RECURRENCE_HISTORY_JSON_PATH,
    markdown_path: Path | str = BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    event_log_path: Path | str | None = None,
    session_diagnostic_event_log_path: Path | str | None = None,
    command_used: str | None = None,
    generated_at: str | None = None,
    recurrence_event_metadata: Mapping[str, Any] | None = None,
    event_source: str | None = None,
    recorded_at: str | None = None,
    persistence_report: dict[str, Any] | None = None,
    temporal_trajectory_capture: bool = False,
) -> tuple[Path, Path]:
    """Write report-only bug-class recurrence JSON and markdown artifacts."""
    json_out = Path(json_path)
    markdown_out = Path(markdown_path)
    log_out = Path(event_log_path) if event_log_path is not None else _bug_recurrence_event_log_path(json_out)
    session_log_out = (
        Path(session_diagnostic_event_log_path)
        if session_diagnostic_event_log_path is not None
        else _bug_recurrence_session_diagnostic_event_log_path(json_out)
    )
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)

    protected_log = load_recurrence_event_log(log_out)
    session_diagnostic_log = load_recurrence_event_log(session_log_out)
    if rows:
        merge_kwargs: dict[str, Any] = {
            "event_source": event_source,
            "recorded_at": recorded_at or generated_at,
        }
        if not (isinstance(recurrence_event_metadata, Mapping) and recurrence_event_metadata.get("command")):
            merge_kwargs["command"] = command_used
        metadata = normalize_recurrence_event_metadata(
            recurrence_event_metadata,
            **merge_kwargs,
        )
        lane_result = append_recurrence_events_to_persistence_lanes(
            protected_log,
            session_diagnostic_log,
            rows,
            event_metadata=metadata,
        )
        protected_log = lane_result["protected_log"]
        session_diagnostic_log = lane_result["session_diagnostic_log"]
        write_recurrence_event_log(log_out, protected_log)
        write_recurrence_event_log(session_log_out, session_diagnostic_log)
        if persistence_report is not None:
            persistence_report.clear()
            persistence_report.update(lane_result)

    recurrence_history = aggregate_protected_recurrence_history_from_event_log(protected_log)
    recurrence_timeline = build_recurrence_timeline(protected_log)
    recurrence_trends = build_recurrence_trend_summary(protected_log)
    recurrence_forecast = build_recurrence_forecast(
        recurrence_timeline=recurrence_timeline,
        recurrence_trends=recurrence_trends,
        regression_recurrence_rate=recurrence_history.get("regression_recurrence_rate"),
    )
    recurrence_portfolio = build_recurrence_portfolio(
        recurrence_timeline=recurrence_timeline,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        event_log=protected_log,
    )
    recurrence_remediation_targets = build_recurrence_remediation_targets(
        recurrence_portfolio=recurrence_portfolio,
        recurrence_forecast=recurrence_forecast,
        recurrence_trends=recurrence_trends,
        recurrence_history=recurrence_history,
        recurrence_timeline=recurrence_timeline,
        event_log=protected_log,
    )
    recurrence_roi = build_recurrence_roi_analysis(
        recurrence_remediation_targets=recurrence_remediation_targets,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_history=recurrence_history,
    )
    recurrence_governance = build_recurrence_governance(
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_remediation_targets=recurrence_remediation_targets,
        recurrence_roi=recurrence_roi,
        recurrence_history=recurrence_history,
        recurrence_timeline=recurrence_timeline,
    )
    recurrence_lifecycle = build_recurrence_lifecycle(
        recurrence_timeline=recurrence_timeline,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_governance=recurrence_governance,
        recurrence_history=recurrence_history,
    )
    recurrence_program_effectiveness = build_recurrence_program_effectiveness(
        recurrence_governance=recurrence_governance,
        recurrence_remediation_summary=recurrence_remediation_targets["remediation_summary"],
        recurrence_roi_summary=recurrence_roi["roi_summary"],
        recurrence_lifecycle_summary=recurrence_lifecycle["lifecycle_summary"],
        recurrence_portfolio_summary=recurrence_portfolio["portfolio_summary"],
        recurrence_forecast=recurrence_forecast,
        recurrence_history=recurrence_history,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_remediation_targets=recurrence_remediation_targets,
    )
    recurrence_maturity = build_recurrence_maturity_assessment(
        recurrence_history=recurrence_history,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_remediation=recurrence_remediation_targets,
        recurrence_roi=recurrence_roi,
        recurrence_governance=recurrence_governance,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
    )
    recurrence_roadmap = build_recurrence_strategic_roadmap(
        recurrence_maturity_summary=recurrence_maturity["recurrence_maturity_summary"],
        recurrence_maturity_gap_analysis=recurrence_maturity["maturity_gap_analysis"],
        recurrence_program_effectiveness_summary=recurrence_program_effectiveness[
            "program_effectiveness_summary"
        ],
        recurrence_portfolio_summary=recurrence_portfolio["portfolio_summary"],
        recurrence_forecast_summary=recurrence_forecast["forecast_summary"],
        recurrence_lifecycle_summary=recurrence_lifecycle["lifecycle_summary"],
        recurrence_remediation_effectiveness_summary=recurrence_program_effectiveness[
            "remediation_effectiveness_summary"
        ],
        portfolio_trajectory_summary=recurrence_program_effectiveness["portfolio_trajectory_summary"],
        total_observations=int(recurrence_history.get("total_rows") or 0),
        total_keys=int(recurrence_history.get("unique_recurrence_count") or 0),
    )
    recurrence_completion = build_recurrence_completion_assessment(
        recurrence_maturity_summary=recurrence_maturity["recurrence_maturity_summary"],
        recurrence_program_effectiveness_summary=recurrence_program_effectiveness[
            "program_effectiveness_summary"
        ],
        recurrence_target_state=recurrence_roadmap["recurrence_target_state"],
        recurrence_roadmap_summary=recurrence_roadmap["recurrence_roadmap_summary"],
        recurrence_history={
            **recurrence_history,
            "recurrence_timeline": recurrence_timeline,
            "recurrence_trends": recurrence_trends,
            "recurrence_forecast": recurrence_forecast,
            "recurrence_portfolio": recurrence_portfolio,
            "recurrence_portfolio_summary": recurrence_portfolio["portfolio_summary"],
            "recurrence_governance": recurrence_governance,
            "recurrence_governance_summary": recurrence_governance["governance_summary"],
            "recurrence_retirement_summary": recurrence_governance["retirement_summary"],
            "recurrence_lifecycle": recurrence_lifecycle,
            "recurrence_lifecycle_summary": recurrence_lifecycle["lifecycle_summary"],
            "recurrence_transition_summary": recurrence_lifecycle["transition_summary"],
            "recurrence_age_distribution": recurrence_lifecycle["age_distribution"],
            "recurrence_closure_effectiveness": recurrence_lifecycle["closure_effectiveness"],
            "recurrence_remediation_targets": recurrence_remediation_targets,
            "recurrence_remediation_summary": recurrence_remediation_targets["remediation_summary"],
            "recurrence_roi": recurrence_roi,
            "recurrence_roi_summary": recurrence_roi["roi_summary"],
        },
        recurrence_governance_summary=recurrence_governance["governance_summary"],
        recurrence_forecast_summary=recurrence_forecast["forecast_summary"],
        forecast_effectiveness_summary=recurrence_program_effectiveness[
            "forecast_effectiveness_summary"
        ],
        remediation_effectiveness_summary=recurrence_program_effectiveness[
            "remediation_effectiveness_summary"
        ],
        recurrence_lifecycle_summary=recurrence_lifecycle["lifecycle_summary"],
        recurrence_roi_summary=recurrence_roi["roi_summary"],
        portfolio_trajectory_summary=recurrence_program_effectiveness["portfolio_trajectory_summary"],
    )
    enriched_history = {
        **recurrence_history,
        "recurrence_timeline": recurrence_timeline,
        "recurrence_trends": recurrence_trends,
        "recurrence_forecast": recurrence_forecast,
        "recurrence_portfolio": recurrence_portfolio,
        "recurrence_portfolio_summary": recurrence_portfolio["portfolio_summary"],
        "recurrence_governance": recurrence_governance,
        "recurrence_governance_summary": recurrence_governance["governance_summary"],
        "recurrence_retirement_summary": recurrence_governance["retirement_summary"],
        "recurrence_lifecycle": recurrence_lifecycle,
        "recurrence_lifecycle_summary": recurrence_lifecycle["lifecycle_summary"],
        "recurrence_transition_summary": recurrence_lifecycle["transition_summary"],
        "recurrence_age_distribution": recurrence_lifecycle["age_distribution"],
        "recurrence_closure_effectiveness": recurrence_lifecycle["closure_effectiveness"],
        "recurrence_remediation_targets": recurrence_remediation_targets,
        "recurrence_remediation_summary": recurrence_remediation_targets["remediation_summary"],
        "recurrence_roi": recurrence_roi,
        "recurrence_roi_summary": recurrence_roi["roi_summary"],
        "recurrence_maturity": recurrence_maturity,
        "recurrence_maturity_summary": recurrence_maturity["recurrence_maturity_summary"],
        "recurrence_roadmap": recurrence_roadmap,
        "recurrence_roadmap_summary": recurrence_roadmap["recurrence_roadmap_summary"],
        "recurrence_target_state": recurrence_roadmap["recurrence_target_state"],
        "recurrence_completion": recurrence_completion,
        "recurrence_completion_summary": recurrence_completion["recurrence_completion_summary"],
    }
    recurrence_graduation_audit = build_recurrence_graduation_audit(
        recurrence_history=enriched_history,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_remediation=recurrence_remediation_targets,
        recurrence_roi=recurrence_roi,
        recurrence_governance=recurrence_governance,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_maturity=recurrence_maturity,
        recurrence_roadmap=recurrence_roadmap,
        recurrence_completion=recurrence_completion,
    )
    trajectory_result = apply_recurrence_trajectory_to_analytics(
        timestamp=generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        artifact_source=str(json_out),
        recurrence_history=recurrence_history,
        recurrence_timeline=recurrence_timeline,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_remediation_targets=recurrence_remediation_targets,
        recurrence_roi=recurrence_roi,
        recurrence_governance=recurrence_governance,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_maturity=recurrence_maturity,
        recurrence_roadmap=recurrence_roadmap,
        recurrence_completion=recurrence_completion,
        recurrence_graduation_audit=recurrence_graduation_audit,
        trajectory_history_path=_bug_recurrence_trajectory_history_path(json_out),
        temporal_capture=temporal_trajectory_capture,
    )
    recurrence_program_effectiveness = trajectory_result["recurrence_program_effectiveness"]
    recurrence_maturity = trajectory_result["recurrence_maturity"]
    recurrence_roadmap = trajectory_result["recurrence_roadmap"]
    recurrence_completion = trajectory_result["recurrence_completion"]
    recurrence_graduation_audit = trajectory_result["recurrence_graduation_audit"]
    recurrence_trajectory_history = trajectory_result["recurrence_trajectory_history"]
    recurrence_trajectory_summary = trajectory_result["recurrence_trajectory_summary"]
    enriched_history_for_confidence = {
        **recurrence_history,
        "recurrence_timeline": recurrence_timeline,
        "recurrence_trends": recurrence_trends,
        "recurrence_forecast": recurrence_forecast,
        "recurrence_portfolio": recurrence_portfolio,
        "recurrence_portfolio_summary": recurrence_portfolio["portfolio_summary"],
        "recurrence_governance": recurrence_governance,
        "recurrence_governance_summary": recurrence_governance["governance_summary"],
        "recurrence_lifecycle": recurrence_lifecycle,
        "recurrence_lifecycle_summary": recurrence_lifecycle["lifecycle_summary"],
        "recurrence_program_effectiveness": recurrence_program_effectiveness,
        "recurrence_program_effectiveness_summary": recurrence_program_effectiveness[
            "program_effectiveness_summary"
        ],
        "recurrence_maturity": recurrence_maturity,
        "recurrence_maturity_summary": recurrence_maturity["recurrence_maturity_summary"],
        "recurrence_completion": recurrence_completion,
        "recurrence_completion_summary": recurrence_completion["recurrence_completion_summary"],
        "recurrence_trajectory_summary": recurrence_trajectory_summary,
    }
    recurrence_confidence_audit = build_recurrence_confidence_audit(
        recurrence_forecast=recurrence_forecast,
        recurrence_governance=recurrence_governance,
        recurrence_program_effectiveness=recurrence_program_effectiveness,
        recurrence_maturity=recurrence_maturity,
        recurrence_completion=recurrence_completion,
        recurrence_trajectory_summary=recurrence_trajectory_summary,
        recurrence_history=enriched_history_for_confidence,
        recurrence_lifecycle=recurrence_lifecycle,
        recurrence_portfolio_summary=recurrence_portfolio["portfolio_summary"],
    )
    recurrence_outcome_validation = None
    if bool(recurrence_trajectory_summary.get("trajectory_available")):
        recurrence_outcome_validation = build_recurrence_outcome_validation(
            recurrence_history=enriched_history_for_confidence,
            recurrence_lifecycle=recurrence_lifecycle,
            recurrence_remediation_targets=recurrence_remediation_targets,
            recurrence_program_effectiveness=recurrence_program_effectiveness,
            recurrence_trajectory_summary=recurrence_trajectory_summary,
            recurrence_forecast=recurrence_forecast,
            recurrence_governance=recurrence_governance,
            recurrence_maturity=recurrence_maturity,
            recurrence_completion=recurrence_completion,
            recurrence_graduation_audit=recurrence_graduation_audit,
            event_log=protected_log,
            as_of=generated_at,
        )
        recurrence_confidence_audit = recurrence_outcome_validation["recurrence_confidence_audit"]
    recurrence_final_graduation_decision = build_recurrence_final_graduation_decision(
        recurrence_trajectory_summary=recurrence_trajectory_summary,
        recurrence_trajectory_history=recurrence_trajectory_history,
        recurrence_confidence_audit=recurrence_confidence_audit,
        recurrence_graduation_audit=recurrence_graduation_audit,
        recurrence_completion=recurrence_completion,
        recurrence_maturity=recurrence_maturity,
    )
    payload = {
        **recurrence_history,
        "summary": build_recurrence_summary(recurrence_history),
        "recurrence_timeline": recurrence_timeline,
        "recurrence_trends": recurrence_trends,
        "recurrence_forecast": recurrence_forecast,
        "recurrence_portfolio": recurrence_portfolio,
        "recurrence_portfolio_summary": recurrence_portfolio["portfolio_summary"],
        "recurrence_remediation_targets": recurrence_remediation_targets,
        "recurrence_remediation_summary": recurrence_remediation_targets["remediation_summary"],
        "recurrence_roi": recurrence_roi,
        "recurrence_roi_summary": recurrence_roi["roi_summary"],
        "recurrence_governance": recurrence_governance,
        "recurrence_watchlist": recurrence_governance["watchlist"],
        "recurrence_governance_summary": recurrence_governance["governance_summary"],
        "recurrence_retirement_summary": recurrence_governance["retirement_summary"],
        "recurrence_lifecycle": recurrence_lifecycle,
        "recurrence_lifecycle_summary": recurrence_lifecycle["lifecycle_summary"],
        "recurrence_age_distribution": recurrence_lifecycle["age_distribution"],
        "recurrence_transition_summary": recurrence_lifecycle["transition_summary"],
        "recurrence_closure_effectiveness": recurrence_lifecycle["closure_effectiveness"],
        "recurrence_program_effectiveness": recurrence_program_effectiveness,
        "recurrence_program_effectiveness_summary": recurrence_program_effectiveness[
            "program_effectiveness_summary"
        ],
        "governance_effectiveness_summary": recurrence_program_effectiveness[
            "governance_effectiveness_summary"
        ],
        "remediation_effectiveness_summary": recurrence_program_effectiveness[
            "remediation_effectiveness_summary"
        ],
        "forecast_effectiveness_summary": recurrence_program_effectiveness[
            "forecast_effectiveness_summary"
        ],
        "portfolio_trajectory_summary": recurrence_program_effectiveness["portfolio_trajectory_summary"],
        "stability_trajectory_summary": recurrence_program_effectiveness["stability_trajectory_summary"],
        "recurrence_maturity": recurrence_maturity,
        "recurrence_maturity_summary": recurrence_maturity["recurrence_maturity_summary"],
        "recurrence_maturity_gap_analysis": recurrence_maturity["maturity_gap_analysis"],
        "recurrence_roadmap": recurrence_roadmap,
        "recurrence_roadmap_summary": recurrence_roadmap["recurrence_roadmap_summary"],
        "recurrence_target_state": recurrence_roadmap["recurrence_target_state"],
        "recurrence_completion": recurrence_completion,
        "recurrence_completion_summary": recurrence_completion["recurrence_completion_summary"],
        "recurrence_completion_gap_analysis": recurrence_completion["completion_gap_analysis"],
        "recurrence_graduation_audit": recurrence_graduation_audit,
        "recurrence_graduation_audit_summary": recurrence_graduation_audit[
            "recurrence_graduation_audit_summary"
        ],
        "recurrence_trajectory_history": recurrence_trajectory_history,
        "recurrence_trajectory_summary": recurrence_trajectory_summary,
        "recurrence_confidence_audit": recurrence_confidence_audit,
        "recurrence_confidence_calibration_summary": recurrence_confidence_audit[
            "recurrence_confidence_calibration_summary"
        ],
        "recurrence_final_graduation_decision": recurrence_final_graduation_decision,
    }
    if isinstance(recurrence_outcome_validation, Mapping):
        payload["recurrence_outcome_validation"] = recurrence_outcome_validation
        payload["outcome_validation_summary"] = recurrence_outcome_validation["outcome_validation_summary"]
    json_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(
        render_bug_recurrence_history_markdown(
            payload,
            generated_at=generated_at,
            command_used=command_used,
        ),
        encoding="utf-8",
    )
    if json_out.name == BUG_RECURRENCE_HISTORY_JSON_PATH.name:
        audit_doc_path = RECURRENCE_GRADUATION_AUDIT_DOC_PATH
        audit_doc_path.parent.mkdir(parents=True, exist_ok=True)
        audit_doc_path.write_text(
            render_recurrence_graduation_audit_report_markdown(
                recurrence_graduation_audit,
                generated_at=generated_at,
            ),
            encoding="utf-8",
        )
        if not bool(recurrence_trajectory_summary.get("trajectory_available")):
            calibration_doc_path = RECURRENCE_CONFIDENCE_CALIBRATION_DOC_PATH
            calibration_doc_path.parent.mkdir(parents=True, exist_ok=True)
            calibration_doc_path.write_text(
                render_recurrence_confidence_calibration_report_markdown(
                    recurrence_confidence_audit,
                    generated_at=generated_at,
                ),
                encoding="utf-8",
            )
        final_decision_doc_path = RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH
        final_decision_doc_path.parent.mkdir(parents=True, exist_ok=True)
        final_decision_doc_path.write_text(
            render_recurrence_final_graduation_decision_report_markdown(
                recurrence_final_graduation_decision,
                generated_at=generated_at,
            ),
            encoding="utf-8",
        )
        if isinstance(recurrence_outcome_validation, Mapping):
            outcome_doc_path = RECURRENCE_OUTCOME_VALIDATION_DOC_PATH
            outcome_doc_path.parent.mkdir(parents=True, exist_ok=True)
            outcome_doc_path.write_text(
                render_recurrence_outcome_validation_report_markdown(
                    recurrence_outcome_validation,
                    generated_at=generated_at,
                ),
                encoding="utf-8",
            )
    return json_out, markdown_out
