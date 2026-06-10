"""Shared replay drift row normalization utilities.

Test/report helper only. Keeps row filtering and scorecard expansion consistent
across hotspot, trend, and risk diagnostics without changing scoring rules.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

RERUN_DELTA_KEY_FIELD_PATHS: dict[str, str] = {
    "speaker": "selected_speaker_id",
    "route": "route_kind",
    "fallback": "fallback_family",
    "scaffold": "scaffold_leakage",
    "text_fingerprint": "final_text",
    "response_delta": "response_delta",
    "runtime_lineage": "runtime_lineage",
}


def valid_classification_rows(
    classifications: Sequence[Mapping[str, Any]] | None,
) -> list[Mapping[str, Any]]:
    """Return mapping rows with non-empty ``field_path``."""
    if not classifications:
        return []
    rows: list[Mapping[str, Any]] = []
    for row in classifications:
        if not isinstance(row, Mapping):
            continue
        field_path = str(row.get("field_path") or "").strip()
        if not field_path:
            continue
        rows.append(row)
    return rows


def classification_rows_from_scorecards(
    scorecards: Sequence[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Expand rerun scorecard owner drift rows into pseudo-classification rows."""
    if not scorecards:
        return []
    rows: list[dict[str, Any]] = []
    for scorecard in scorecards:
        if not isinstance(scorecard, Mapping) or scorecard.get("comparison_available") is False:
            continue
        owner_rows = scorecard.get("owner_drift_classifications")
        if not isinstance(owner_rows, list):
            continue
        for row in owner_rows:
            if not isinstance(row, Mapping):
                continue
            delta_key = str(row.get("delta_key") or "").strip()
            field_path = RERUN_DELTA_KEY_FIELD_PATHS.get(delta_key, delta_key or "unknown")
            rows.append(
                {
                    "field_path": field_path,
                    "owner_drift_bucket": row.get("owner_drift_bucket"),
                    "category": None,
                    "investigate_first": None,
                    "turn_index": row.get("turn_index"),
                    "source": "rerun_scorecard",
                }
            )
    return rows


def classification_rows_for_analysis(
    classifications: Sequence[Mapping[str, Any]] | None,
    *,
    scorecard_history: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return raw classification mappings plus expanded scorecard classifications."""
    rows: list[dict[str, Any]] = []
    if classifications:
        rows.extend(dict(row) for row in classifications if isinstance(row, Mapping))
    if scorecard_history:
        rows.extend(classification_rows_from_scorecards(scorecard_history))
    return rows
