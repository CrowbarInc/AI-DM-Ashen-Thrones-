"""Report-facing replay drift analytics facade.

This module intentionally re-exports only the drift analytics helpers consumed
by dashboard/report writers. Analytics logic remains in the narrower owner
modules.
"""
from __future__ import annotations

from tests.helpers.replay_bug_recurrence import (
    aggregate_recurrence_history,
    build_recurrence_summary,
    recurrence_rows,
)
from tests.helpers.replay_drift_hotspots import (
    build_hotspot_rankings,
    render_owner_drift_hotspot_report,
)
from tests.helpers.replay_drift_longitudinal import (
    aggregate_owner_drift_history,
    build_owner_drift_trend_summary,
    render_owner_drift_longitudinal_report,
)
from tests.helpers.replay_drift_risk import (
    build_risk_payload,
    render_owner_drift_risk_report,
)
from tests.helpers.replay_drift_rows import (
    classification_rows_for_analysis,
    classification_rows_from_scorecards,
)
from tests.helpers.replay_drift_taxonomy import (
    build_long_session_stability_history,
    build_stability_hotspots,
    render_stability_hotspots_markdown_lines,
    render_stability_trends_markdown_lines,
    stability_classification_rows_from_scorecard,
    summarize_owner_drift_buckets,
)
from tests.helpers.replay_drift_trends import (
    build_trend_payload,
    enrich_hotspots_with_field_trends,
    render_owner_drift_trend_report,
)

__all__ = (
    "aggregate_owner_drift_history",
    "aggregate_recurrence_history",
    "build_hotspot_rankings",
    "build_long_session_stability_history",
    "build_owner_drift_trend_summary",
    "build_recurrence_summary",
    "build_risk_payload",
    "build_stability_hotspots",
    "build_trend_payload",
    "classification_rows_for_analysis",
    "classification_rows_from_scorecards",
    "enrich_hotspots_with_field_trends",
    "recurrence_rows",
    "render_owner_drift_hotspot_report",
    "render_owner_drift_longitudinal_report",
    "render_owner_drift_risk_report",
    "render_owner_drift_trend_report",
    "render_stability_hotspots_markdown_lines",
    "render_stability_trends_markdown_lines",
    "stability_classification_rows_from_scorecard",
    "summarize_owner_drift_buckets",
)
