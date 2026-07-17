"""Owner-oriented replay drift bucket taxonomy (Cycle AR).

**Authority (CG-1):** owner-drift bucket vocabulary (``ALLOWED_OWNER_DRIFT_BUCKETS``)
and ``classify_owner_drift_bucket`` mapping logic. First component of
``recurrence:v1`` keys.

**Consumes:** classifier rows for drift reporting; does not own failure
categories or investigation-target defaults (those mirror contract/classifier).

Registry: ``docs/audits/CG_failure_classification_authority_registry.md``
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

ALLOWED_OWNER_DRIFT_BUCKETS: frozenset[str] = frozenset(
    {
        "route_drift",
        "speaker_drift",
        "fallback_drift",
        "ownership_drift",
        "emission_drift",
        "semantic_drift",
        "lineage_drift",
        "projection_drift",
        "replay_drift_unclassified",
    }
)

ROUTE_DRIFT_FIELD_PATH = "route_kind"
ROUTE_DRIFT_OWNER_BUCKET = "route_drift"
ROUTE_DRIFT_INVESTIGATION_TARGET = "game/interaction_context.py"
ROUTE_DRIFT_CATEGORY = "route"
SPEAKER_DRIFT_FIELD_PATH = "selected_speaker_id"
SPEAKER_DRIFT_OWNER_BUCKET = "speaker_drift"
SPEAKER_DRIFT_INVESTIGATION_TARGET = "game/speaker_contract_enforcement.py"
SPEAKER_DRIFT_CATEGORY = "speaker"
FALLBACK_DRIFT_FIELD_PATH = "fallback_family"
FALLBACK_DRIFT_OWNER_BUCKET = "fallback_drift"
FALLBACK_DRIFT_INVESTIGATION_TARGET = "game/final_emission_gate.py"
FALLBACK_DRIFT_CATEGORY = "fallback"
REPLAY_UNCLASSIFIED_FIELD_PATH = "final_text_hash"
REPLAY_UNCLASSIFIED_OWNER_BUCKET = "replay_drift_unclassified"
REPLAY_UNCLASSIFIED_INVESTIGATION_TARGET = "tests/helpers/golden_replay.py"
REPLAY_UNCLASSIFIED_CATEGORY = "evaluator"

_ROUTE_NEEDLES: tuple[str, ...] = (
    "route_kind",
    "resolution_kind",
    "trace.social_contract_trace.route_selected",
    "trace.canonical_entry",
)
_CONTINUITY_NEEDLES: tuple[str, ...] = (
    "continuity",
    "active_interaction",
    "current_interlocutor",
    "dialogue_lock",
)
_SPEAKER_NEEDLES: tuple[str, ...] = (
    "selected_speaker_id",
    "reply_owner",
    "visible_grounded_speaker",
    "speaker",
)
_OWNERSHIP_NEEDLES: tuple[str, ...] = (
    "opening_fallback_owner_bucket",
    "opening_fallback_authorship_source",
    "sealed_fallback_owner_bucket",
    "visibility_fallback_owner_bucket",
    "visibility_fallback_pool",
    "visibility_fallback_kind",
    "visibility_replacement_applied",
)
_FALLBACK_NEEDLES: tuple[str, ...] = (
    "fallback_family",
    "fallback_temporal_frame",
    "final_emitted_source",
    "opening_recovered_via_fallback",
)
_EMISSION_NEEDLES: tuple[str, ...] = (
    "upstream_prepared_emission",
    "prepared_emission_owner",
    "response_type_repair",
    "response_type_required",
    "response_type_candidate",
    "stage_diff",
    "post_gate_mutation",
    "final_emission_mutation_lineage",
    "validator",
)


def route_drift_classification_kwargs(
    *,
    investigate_first: str = ROUTE_DRIFT_INVESTIGATION_TARGET,
    category: str = ROUTE_DRIFT_CATEGORY,
) -> dict[str, str]:
    """Return canonical route-drift classification fixture kwargs for reporting consumers."""
    return {
        "field_path": ROUTE_DRIFT_FIELD_PATH,
        "owner_drift_bucket": ROUTE_DRIFT_OWNER_BUCKET,
        "investigate_first": investigate_first,
        "category": category,
    }


def speaker_drift_classification_kwargs(
    *,
    investigate_first: str = SPEAKER_DRIFT_INVESTIGATION_TARGET,
    category: str = SPEAKER_DRIFT_CATEGORY,
) -> dict[str, str]:
    """Return canonical speaker-drift classification fixture kwargs for reporting consumers."""
    return {
        "field_path": SPEAKER_DRIFT_FIELD_PATH,
        "owner_drift_bucket": SPEAKER_DRIFT_OWNER_BUCKET,
        "investigate_first": investigate_first,
        "category": category,
    }


def fallback_drift_classification_kwargs(
    *,
    investigate_first: str = FALLBACK_DRIFT_INVESTIGATION_TARGET,
    category: str = FALLBACK_DRIFT_CATEGORY,
) -> dict[str, str]:
    """Return canonical fallback-drift classification fixture kwargs for reporting consumers."""
    return {
        "field_path": FALLBACK_DRIFT_FIELD_PATH,
        "owner_drift_bucket": FALLBACK_DRIFT_OWNER_BUCKET,
        "investigate_first": investigate_first,
        "category": category,
    }


def replay_unclassified_classification_kwargs(
    *,
    investigate_first: str = REPLAY_UNCLASSIFIED_INVESTIGATION_TARGET,
    category: str = REPLAY_UNCLASSIFIED_CATEGORY,
) -> dict[str, str]:
    """Return canonical replay-unclassified classification fixture kwargs for reporting consumers."""
    return {
        "field_path": REPLAY_UNCLASSIFIED_FIELD_PATH,
        "owner_drift_bucket": REPLAY_UNCLASSIFIED_OWNER_BUCKET,
        "investigate_first": investigate_first,
        "category": category,
    }


def owner_drift_classification_fixture(
    *,
    field_path: str,
    owner_drift_bucket: str,
    investigate_first: str,
    category: str,
    severity: str = "high",
    scenario_id: str = "owner_drift_probe",
    turn_index: int = 0,
) -> dict[str, Any]:
    """Build one classifier-shaped owner-drift row for drift report tests."""
    from tests.helpers.failure_classifier import classify_replay_failure
    from tests.helpers.replay_observed_row_fixtures import observed_failure_row

    rows = classify_replay_failure(
        scenario_id=scenario_id,
        turn_index=turn_index,
        observed_turn=observed_failure_row(),
        drift_rows=[
            {
                "field_path": field_path,
                "expected": "a",
                "actual": "b",
                "reason": "probe",
                "drift_bucket": "structural_drift",
                "replay_tags": ["structural_drift"],
            }
        ],
    )
    row = dict(rows[0])
    row["owner_drift_bucket"] = owner_drift_bucket
    row["investigate_first"] = investigate_first
    row["category"] = category
    row["severity"] = severity
    return row


def route_drift_scorecard_fixture(
    *,
    scenario_id: str = "route_drift_fixture",
    turn_index: int = 0,
) -> dict[str, Any]:
    """Return a minimal scorecard carrying a route owner-drift row for reporting consumers."""
    return {
        "scenario_id": scenario_id,
        "comparison_available": True,
        "report_only": True,
        "owner_drift_classifications": [
            {
                "turn_index": turn_index,
                "owner_drift_bucket": ROUTE_DRIFT_OWNER_BUCKET,
                "delta_key": "route",
            }
        ],
    }


def speaker_drift_scorecard_fixture(
    *,
    scenario_id: str = "speaker_drift_fixture",
    turn_index: int = 0,
) -> dict[str, Any]:
    """Return a minimal scorecard carrying a speaker owner-drift row for reporting consumers."""
    return {
        "scenario_id": scenario_id,
        "comparison_available": True,
        "report_only": True,
        "owner_drift_classifications": [
            {
                "turn_index": turn_index,
                "owner_drift_bucket": SPEAKER_DRIFT_OWNER_BUCKET,
                "delta_key": "speaker",
            }
        ],
    }


def speaker_route_scorecard_history(
    *,
    scenario_prefix: str = "owner_drift",
    duplicate_speaker: bool = False,
) -> list[dict[str, Any]]:
    """Return a reusable speaker-then-route scorecard history for trend/risk tests."""
    history = [speaker_drift_scorecard_fixture(scenario_id=f"{scenario_prefix}_speaker_scorecard")]
    if duplicate_speaker:
        history.append(speaker_drift_scorecard_fixture(scenario_id=f"{scenario_prefix}_speaker_scorecard"))
    history.append(route_drift_scorecard_fixture(scenario_id=f"{scenario_prefix}_route_scorecard"))
    return history


def stable_long_session_scorecard_fixture(scenario_id: str) -> dict[str, Any]:
    """Return a long-session stability scorecard with no owner drift rows."""
    from tests.helpers.golden_replay_api import build_long_session_stability_scorecard

    return build_long_session_stability_scorecard(
        scenario_id=scenario_id,
        observations=[
            {"turn_index": 0, "route_kind": "dialogue", "selected_speaker_id": "runner"},
            {"turn_index": 1, "route_kind": "dialogue", "selected_speaker_id": "runner"},
        ],
    )


def route_drift_long_session_scorecard_fixture(scenario_id: str) -> dict[str, Any]:
    """Return a long-session stability scorecard containing route drift."""
    from tests.helpers.golden_replay_api import build_long_session_stability_scorecard

    return build_long_session_stability_scorecard(
        scenario_id=scenario_id,
        observations=[
            {"turn_index": 0, "route_kind": "dialogue", "selected_speaker_id": "runner"},
            {"turn_index": 1, "route_kind": "social", "selected_speaker_id": "runner"},
        ],
    )


def fallback_drift_long_session_scorecard_fixture(scenario_id: str) -> dict[str, Any]:
    """Return a long-session stability scorecard containing fallback drift."""
    from tests.helpers.golden_replay_api import build_long_session_stability_scorecard

    return build_long_session_stability_scorecard(
        scenario_id=scenario_id,
        observations=[
            {
                "turn_index": 0,
                "route_kind": "action",
                "fallback_family": "gate_terminal_repair",
                "runtime_lineage_events": [{"event_kind": "fallback_selected"}],
            }
        ],
    )


def _field_matches(field_path: str, needles: tuple[str, ...]) -> bool:
    field_l = field_path.lower()
    return any(needle.lower() in field_l for needle in needles)


def _tag_set(replay_tags: Sequence[str] | None) -> set[str]:
    if not replay_tags:
        return set()
    return {str(tag) for tag in replay_tags if str(tag).strip()}


def classify_owner_drift_bucket(
    *,
    field_path: str,
    category: str,
    measurement_drift_bucket: str,
    replay_tags: Sequence[str] | None,
) -> str:
    """Map one single-run drift row to an owner drift bucket (AR1 priority order)."""
    path = str(field_path or "")
    cat = str(category or "")
    measurement = str(measurement_drift_bucket or "")
    tags = _tag_set(replay_tags)

    if cat == "speaker" or _field_matches(path, _SPEAKER_NEEDLES):
        return "speaker_drift"

    if (
        cat == "route"
        or cat == "continuity"
        or _field_matches(path, _ROUTE_NEEDLES)
        or _field_matches(path, _CONTINUITY_NEEDLES)
    ):
        return "route_drift"

    if _field_matches(path, _OWNERSHIP_NEEDLES):
        return "ownership_drift"

    if cat == "fallback" or _field_matches(path, _FALLBACK_NEEDLES):
        return "fallback_drift"

    if cat in {"emission", "validator", "upstream_prepared_emission"} or _field_matches(path, _EMISSION_NEEDLES):
        return "emission_drift"

    if (
        path == "scaffold_leakage"
        or path.startswith("semantic.")
        or cat in {"sanitizer", "semantic_mutation"}
        or measurement == "semantic_drift"
    ):
        return "semantic_drift"

    if cat in {"projection", "normalization"} or "missing_observation" in tags:
        return "projection_drift"

    if measurement == "exact_drift" or cat in {"replay_drift", "evaluator"}:
        return "replay_drift_unclassified"

    return "replay_drift_unclassified"


def classify_rerun_delta_owner_drift_bucket(
    delta_key: str,
    delta_payload: Mapping[str, Any] | None,
) -> str:
    """Map one rerun per-turn delta key to an owner drift bucket (AR1 priority order)."""
    key = str(delta_key or "")
    payload = delta_payload if isinstance(delta_payload, Mapping) else {}

    if key == "runtime_lineage":
        return "lineage_drift"
    if key == "speaker":
        return "speaker_drift"
    if key == "route":
        return "route_drift"
    if key == "fallback":
        previous_family = payload.get("previous_family")
        current_family = payload.get("current_family")
        if previous_family == current_family:
            return "ownership_drift"
        return "fallback_drift"
    if key == "response_delta":
        return "emission_drift"
    if key == "scaffold":
        return "semantic_drift"
    if key == "text_fingerprint":
        return "replay_drift_unclassified"

    return "replay_drift_unclassified"


def owner_drift_classifications_from_per_turn_deltas(
    per_turn_deltas: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build scorecard owner drift classification rows from rerun per-turn deltas."""
    rows: list[dict[str, Any]] = []
    for turn_row in per_turn_deltas:
        if not isinstance(turn_row, Mapping):
            continue
        deltas = turn_row.get("deltas")
        if not isinstance(deltas, Mapping):
            continue
        turn_index = turn_row.get("turn_index")
        for delta_key, payload in deltas.items():
            rows.append(
                {
                    "turn_index": turn_index,
                    "owner_drift_bucket": classify_rerun_delta_owner_drift_bucket(
                        str(delta_key),
                        payload if isinstance(payload, Mapping) else {},
                    ),
                    "delta_key": str(delta_key),
                }
            )
    return rows


def summarize_owner_drift_buckets(
    classifications: Sequence[Mapping[str, Any]] | None,
) -> dict[str, int]:
    """Count owner drift bucket occurrences from classification rows."""
    counts = {bucket: 0 for bucket in sorted(ALLOWED_OWNER_DRIFT_BUCKETS)}
    if not classifications:
        return counts
    for row in classifications:
        if not isinstance(row, Mapping):
            continue
        bucket = str(row.get("owner_drift_bucket") or "").strip()
        if bucket in ALLOWED_OWNER_DRIFT_BUCKETS:
            counts[bucket] += 1
    return counts


def _long_session_stability_classification_row(
    *,
    signal: str,
    owner_drift_bucket: str,
    severity_hint: str,
    reason: str,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    bucket = (
        owner_drift_bucket
        if owner_drift_bucket in ALLOWED_OWNER_DRIFT_BUCKETS
        else "replay_drift_unclassified"
    )
    return {
        "signal": signal,
        "owner_drift_bucket": bucket,
        "severity_hint": severity_hint,
        "reason": reason,
        "evidence": dict(evidence),
    }


def _degradation_reason_owner_bucket(reason_code: str) -> str:
    code = str(reason_code or "").strip().lower()
    if not code:
        return "replay_drift_unclassified"
    semantic_markers = (
        "rising_generic_filler",
        "late_session_reset",
        "referent_loss",
        "continuity_anchor",
        "debug_leak",
        "progressive_degradation",
    )
    if any(marker in code for marker in semantic_markers):
        return "semantic_drift"
    return "replay_drift_unclassified"


def _recurrence_owner_bucket(recurrence_key: str) -> str:
    key = str(recurrence_key or "").strip().lower()
    if "fallback_selected" in key or key.startswith("fallback"):
        return "fallback_drift"
    return "lineage_drift"


def owner_drift_buckets_from_long_session_stability_scorecard(
    scorecard: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Map long-session stability scorecard signals to Cycle AR owner drift buckets."""
    if not isinstance(scorecard, Mapping):
        return []

    route = scorecard.get("route_stability") if isinstance(scorecard.get("route_stability"), Mapping) else {}
    speaker = scorecard.get("speaker_stability") if isinstance(scorecard.get("speaker_stability"), Mapping) else {}
    fallback = scorecard.get("fallback_stability") if isinstance(scorecard.get("fallback_stability"), Mapping) else {}
    lineage = scorecard.get("lineage_stability") if isinstance(scorecard.get("lineage_stability"), Mapping) else {}
    degradation = scorecard.get("degradation") if isinstance(scorecard.get("degradation"), Mapping) else {}

    route_change_count = int(route.get("route_change_count") or 0)
    route_frequency = dict(route.get("route_frequency") or {}) if isinstance(route.get("route_frequency"), Mapping) else {}
    speaker_change_count = int(speaker.get("speaker_change_count") or 0)
    speaker_missing_count = int(speaker.get("speaker_missing_count") or 0)
    speaker_frequency = (
        dict(speaker.get("speaker_frequency") or {})
        if isinstance(speaker.get("speaker_frequency"), Mapping)
        else {}
    )
    fallback_count = int(fallback.get("fallback_count") or 0)
    max_fallback_streak = int(fallback.get("max_fallback_streak") or 0)
    late_window_fallback_count = int(fallback.get("late_window_fallback_count") or 0)
    escalation_warnings_raw = fallback.get("escalation_warnings")
    escalation_warnings = (
        [str(item) for item in escalation_warnings_raw if str(item).strip()]
        if isinstance(escalation_warnings_raw, list)
        else []
    )
    fallback_family_frequency = (
        dict(fallback.get("fallback_family_frequency") or {})
        if isinstance(fallback.get("fallback_family_frequency"), Mapping)
        else {}
    )
    recurring_events = lineage.get("recurring_events")
    event_counts = dict(lineage.get("event_counts") or {}) if isinstance(lineage.get("event_counts"), Mapping) else {}
    progressive_degradation_detected = bool(degradation.get("progressive_degradation_detected"))
    reason_codes_raw = degradation.get("reason_codes")
    reason_codes = (
        [str(code) for code in reason_codes_raw if str(code).strip()]
        if isinstance(reason_codes_raw, list)
        else []
    )

    rows: list[dict[str, Any]] = []

    if route_change_count > 0 or len(route_frequency) > 1:
        rows.append(
            _long_session_stability_classification_row(
                signal="route_change",
                owner_drift_bucket="route_drift",
                severity_hint="medium" if route_change_count > 2 else "low",
                reason=f"route instability observed across {route_change_count} change(s)",
                evidence={
                    "route_change_count": route_change_count,
                    "route_frequency": route_frequency,
                },
            )
        )

    if speaker_change_count > 0:
        rows.append(
            _long_session_stability_classification_row(
                signal="speaker_change",
                owner_drift_bucket="speaker_drift",
                severity_hint="medium" if speaker_change_count > 2 else "low",
                reason=f"speaker changed {speaker_change_count} time(s) across the session",
                evidence={
                    "speaker_change_count": speaker_change_count,
                    "speaker_frequency": speaker_frequency,
                },
            )
        )
    if speaker_missing_count > 0:
        rows.append(
            _long_session_stability_classification_row(
                signal="speaker_missing",
                owner_drift_bucket="speaker_drift",
                severity_hint="medium" if speaker_missing_count > 2 else "low",
                reason=f"speaker missing on {speaker_missing_count} turn(s)",
                evidence={"speaker_missing_count": speaker_missing_count},
            )
        )

    if fallback_count > 0:
        rows.append(
            _long_session_stability_classification_row(
                signal="fallback_count",
                owner_drift_bucket="fallback_drift",
                severity_hint="medium" if fallback_count > 2 else "low",
                reason=f"fallback selected on {fallback_count} turn(s)",
                evidence={
                    "fallback_count": fallback_count,
                    "fallback_family_frequency": fallback_family_frequency,
                },
            )
        )
    if max_fallback_streak > 1:
        rows.append(
            _long_session_stability_classification_row(
                signal="fallback_streak",
                owner_drift_bucket="fallback_drift",
                severity_hint="high" if max_fallback_streak > 2 else "medium",
                reason=f"fallback streak reached {max_fallback_streak} consecutive turn(s)",
                evidence={"max_fallback_streak": max_fallback_streak},
            )
        )
    if late_window_fallback_count > 0:
        rows.append(
            _long_session_stability_classification_row(
                signal="late_window_fallback",
                owner_drift_bucket="fallback_drift",
                severity_hint="medium",
                reason=f"late-window fallback count is {late_window_fallback_count}",
                evidence={"late_window_fallback_count": late_window_fallback_count},
            )
        )
    for warning in sorted(set(escalation_warnings)):
        rows.append(
            _long_session_stability_classification_row(
                signal="fallback_escalation_warning",
                owner_drift_bucket="fallback_drift",
                severity_hint="high" if warning.endswith("_loop") or "spike" in warning else "medium",
                reason=f"fallback escalation warning: {warning}",
                evidence={"escalation_warning": warning},
            )
        )

    seen_recurrence_keys: set[str] = set()
    if isinstance(recurring_events, list):
        for event in recurring_events:
            if not isinstance(event, Mapping):
                continue
            count = int(event.get("count") or 0)
            if count < 2:
                continue
            recurrence_key = str(event.get("recurrence_key") or "").strip()
            if not recurrence_key or recurrence_key in seen_recurrence_keys:
                continue
            seen_recurrence_keys.add(recurrence_key)
            rows.append(
                _long_session_stability_classification_row(
                    signal="lineage_recurrence",
                    owner_drift_bucket=_recurrence_owner_bucket(recurrence_key),
                    severity_hint="high" if count > 5 else "medium",
                    reason=f"recurring lineage pattern `{recurrence_key}` observed {count} time(s)",
                    evidence={"recurrence_key": recurrence_key, "count": count},
                )
            )
    fallback_selected_count = int(event_counts.get("fallback_selected") or 0)
    if fallback_selected_count >= 2 and not any(
        row.get("signal") == "lineage_recurrence"
        and isinstance(row.get("evidence"), Mapping)
        and "fallback_selected" in str(row["evidence"].get("recurrence_key") or "")
        for row in rows
    ):
        rows.append(
            _long_session_stability_classification_row(
                signal="lineage_fallback_recurrence",
                owner_drift_bucket="fallback_drift",
                severity_hint="medium",
                reason=f"fallback_selected lineage events recurred {fallback_selected_count} time(s)",
                evidence={"event_kind": "fallback_selected", "count": fallback_selected_count},
            )
        )

    if progressive_degradation_detected:
        rows.append(
            _long_session_stability_classification_row(
                signal="progressive_degradation",
                owner_drift_bucket="semantic_drift",
                severity_hint="high",
                reason="progressive session degradation detected",
                evidence={
                    "progressive_degradation_detected": True,
                    "reason_codes": reason_codes,
                    "classification": degradation.get("classification"),
                },
            )
        )
    for reason_code in sorted(set(reason_codes)):
        rows.append(
            _long_session_stability_classification_row(
                signal="degradation_reason",
                owner_drift_bucket=_degradation_reason_owner_bucket(reason_code),
                severity_hint="high" if progressive_degradation_detected else "medium",
                reason=f"degradation reason code: {reason_code}",
                evidence={"reason_code": reason_code},
            )
        )

    rows.sort(key=lambda row: (str(row.get("signal") or ""), str(row.get("owner_drift_bucket") or ""), str(row.get("reason") or "")))
    return rows


def _scorecard_stability_status(scorecard: Mapping[str, Any]) -> str:
    operational = scorecard.get("operational_summary") if isinstance(scorecard.get("operational_summary"), Mapping) else {}
    status = str(operational.get("stability_status") or "").strip()
    return status or "unknown"


def stability_classification_rows_from_scorecard(
    scorecard: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Project long-session scorecard owner drift rows into stability ownership rows."""
    if not isinstance(scorecard, Mapping):
        return []
    scenario_id = str(scorecard.get("scenario_id") or "")
    stability_status = _scorecard_stability_status(scorecard)
    source = scorecard.get("owner_drift_classifications")
    if not isinstance(source, list):
        return []

    rows: list[dict[str, Any]] = []
    for item in source:
        if not isinstance(item, Mapping):
            continue
        evidence = item.get("evidence")
        rows.append(
            {
                "scenario_id": scenario_id,
                "signal": str(item.get("signal") or ""),
                "owner_drift_bucket": str(item.get("owner_drift_bucket") or ""),
                "severity_hint": str(item.get("severity_hint") or ""),
                "stability_status": stability_status,
                "reason": str(item.get("reason") or ""),
                "evidence": dict(evidence) if isinstance(evidence, Mapping) else {},
            }
        )
    rows.sort(
        key=lambda row: (
            str(row.get("scenario_id") or ""),
            str(row.get("signal") or ""),
            str(row.get("owner_drift_bucket") or ""),
            str(row.get("reason") or ""),
        )
    )
    return rows


def aggregate_long_session_stability_classifications(
    scorecards: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    """Aggregate stability ownership rows across long-session scorecards."""
    valid = [scorecard for scorecard in (scorecards or []) if isinstance(scorecard, Mapping)]
    bucket_frequencies: dict[str, int] = {bucket: 0 for bucket in sorted(ALLOWED_OWNER_DRIFT_BUCKETS)}
    scenario_frequencies: dict[str, int] = {}
    stability_status_counts: dict[str, int] = {}
    classification_rows: list[dict[str, Any]] = []

    for scorecard in valid:
        scenario_id = str(scorecard.get("scenario_id") or "unknown")
        stability_status = _scorecard_stability_status(scorecard)
        stability_status_counts[stability_status] = stability_status_counts.get(stability_status, 0) + 1
        projected_rows = stability_classification_rows_from_scorecard(scorecard)
        if projected_rows:
            scenario_frequencies[scenario_id] = scenario_frequencies.get(scenario_id, 0) + len(projected_rows)
        for row in projected_rows:
            classification_rows.append(row)
            bucket = str(row.get("owner_drift_bucket") or "").strip()
            if bucket in ALLOWED_OWNER_DRIFT_BUCKETS:
                bucket_frequencies[bucket] += 1

    return {
        "total_scorecards": len(valid),
        "bucket_frequencies": dict(sorted(bucket_frequencies.items())),
        "scenario_frequencies": dict(sorted(scenario_frequencies.items())),
        "stability_status_counts": dict(sorted(stability_status_counts.items())),
        "classification_rows": classification_rows,
    }


STABILITY_TREND_BUCKETS: tuple[str, ...] = (
    "route_drift",
    "speaker_drift",
    "fallback_drift",
    "semantic_drift",
)
STABILITY_TREND_STATUSES: tuple[str, ...] = ("degraded", "watch", "stable")
StabilityTrendLabel = str


def _valid_stability_scorecards(scorecards: Sequence[Mapping[str, Any]] | None) -> list[Mapping[str, Any]]:
    if not scorecards:
        return []
    return [scorecard for scorecard in scorecards if isinstance(scorecard, Mapping)]


def _bucket_counts_for_stability_scorecard(scorecard: Mapping[str, Any]) -> dict[str, int]:
    raw_counts = scorecard.get("owner_drift_bucket_counts")
    if isinstance(raw_counts, Mapping):
        return {bucket: int(raw_counts.get(bucket) or 0) for bucket in STABILITY_TREND_BUCKETS}
    source = scorecard.get("owner_drift_classifications")
    rows = [row for row in source if isinstance(row, Mapping)] if isinstance(source, list) else []
    summarized = summarize_owner_drift_buckets(rows)
    return {bucket: int(summarized.get(bucket) or 0) for bucket in STABILITY_TREND_BUCKETS}


def _signal_counts_for_stability_scorecard(scorecard: Mapping[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in stability_classification_rows_from_scorecard(scorecard):
        signal = str(row.get("signal") or "").strip()
        if not signal:
            continue
        counts[signal] = counts.get(signal, 0) + 1
    return dict(sorted(counts.items()))


def _classify_stability_count_trend(delta: int, *, has_previous: bool) -> StabilityTrendLabel:
    if not has_previous:
        return "insufficient_data"
    if delta > 0:
        return "worsening"
    if delta < 0:
        return "improving"
    return "stable"


def _status_severity_rank(status: str) -> int:
    return {"stable": 0, "watch": 1, "degraded": 2}.get(str(status or "").strip(), 3)


def _classify_stability_status_trend(current_status: str, previous_status: str, *, has_previous: bool) -> StabilityTrendLabel:
    if not has_previous:
        return "insufficient_data"
    current_rank = _status_severity_rank(current_status)
    previous_rank = _status_severity_rank(previous_status)
    if current_rank > previous_rank:
        return "worsening"
    if current_rank < previous_rank:
        return "improving"
    return "stable"


def build_long_session_stability_history(
    scorecards: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    """Build longitudinal stability history across ordered long-session scorecards."""
    valid = _valid_stability_scorecards(scorecards)
    bucket_history: list[dict[str, Any]] = []
    status_history: list[dict[str, Any]] = []
    signal_history: list[dict[str, Any]] = []

    for index, scorecard in enumerate(valid):
        scenario_id = str(scorecard.get("scenario_id") or f"scorecard_{index:02d}")
        bucket_history.append(
            {
                "index": index,
                "scenario_id": scenario_id,
                "bucket_counts": _bucket_counts_for_stability_scorecard(scorecard),
            }
        )
        status_history.append(
            {
                "index": index,
                "scenario_id": scenario_id,
                "stability_status": _scorecard_stability_status(scorecard),
            }
        )
        signal_history.append(
            {
                "index": index,
                "scenario_id": scenario_id,
                "signal_counts": _signal_counts_for_stability_scorecard(scorecard),
            }
        )

    has_comparison = len(valid) >= 2
    current_buckets = _bucket_counts_for_stability_scorecard(valid[-1]) if valid else {bucket: 0 for bucket in STABILITY_TREND_BUCKETS}
    previous_buckets = (
        _bucket_counts_for_stability_scorecard(valid[-2])
        if len(valid) >= 2
        else {bucket: 0 for bucket in STABILITY_TREND_BUCKETS}
    )
    current_status = _scorecard_stability_status(valid[-1]) if valid else "unknown"
    previous_status = _scorecard_stability_status(valid[-2]) if len(valid) >= 2 else "unknown"

    bucket_trends: dict[str, dict[str, Any]] = {}
    for bucket in STABILITY_TREND_BUCKETS:
        current = int(current_buckets.get(bucket) or 0)
        previous = int(previous_buckets.get(bucket) or 0) if has_comparison else 0
        delta = current - previous if has_comparison else 0
        bucket_trends[bucket] = {
            "current": current,
            "previous": previous,
            "delta": delta,
            "trend": _classify_stability_count_trend(delta, has_previous=has_comparison),
        }

    status_trends: dict[str, dict[str, Any]] = {}
    for status in STABILITY_TREND_STATUSES:
        current = 1 if current_status == status else 0
        previous = 1 if previous_status == status else 0
        delta = current - previous if has_comparison else 0
        status_trends[status] = {
            "current": current,
            "previous": previous,
            "delta": delta,
            "trend": _classify_stability_count_trend(delta, has_previous=has_comparison),
        }

    return {
        "sample_count": len(valid),
        "bucket_history": bucket_history,
        "status_history": status_history,
        "signal_history": signal_history,
        "trend_summary": {
            "comparison_available": has_comparison,
            "bucket_trends": bucket_trends,
            "status_trends": status_trends,
            "overall_stability_trend": _classify_stability_status_trend(
                current_status,
                previous_status,
                has_previous=has_comparison,
            ),
            "current_stability_status": current_status,
            "previous_stability_status": previous_status if has_comparison else None,
        },
    }


def stability_trend_rows_from_history(history: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Project stability history trend summary into operator-facing trend rows."""
    if not isinstance(history, Mapping):
        return []
    trend_summary = history.get("trend_summary") if isinstance(history.get("trend_summary"), Mapping) else {}
    bucket_trends = trend_summary.get("bucket_trends") if isinstance(trend_summary.get("bucket_trends"), Mapping) else {}

    rows: list[dict[str, Any]] = []
    for bucket in STABILITY_TREND_BUCKETS:
        trend = bucket_trends.get(bucket) if isinstance(bucket_trends.get(bucket), Mapping) else {}
        rows.append(
            {
                "owner_drift_bucket": bucket,
                "current_count": int(trend.get("current") or 0),
                "previous_count": int(trend.get("previous") or 0),
                "delta": int(trend.get("delta") or 0),
                "trend": str(trend.get("trend") or "insufficient_data"),
            }
        )

    status_trends = trend_summary.get("status_trends") if isinstance(trend_summary.get("status_trends"), Mapping) else {}
    for status in STABILITY_TREND_STATUSES:
        trend = status_trends.get(status) if isinstance(status_trends.get(status), Mapping) else {}
        rows.append(
            {
                "owner_drift_bucket": f"stability_status:{status}",
                "current_count": int(trend.get("current") or 0),
                "previous_count": int(trend.get("previous") or 0),
                "delta": int(trend.get("delta") or 0),
                "trend": str(trend.get("trend") or "insufficient_data"),
            }
        )

    overall = str(trend_summary.get("overall_stability_trend") or "insufficient_data")
    rows.append(
        {
            "owner_drift_bucket": "overall_stability",
            "current_count": 1 if trend_summary.get("comparison_available") else 0,
            "previous_count": 1 if trend_summary.get("comparison_available") else 0,
            "delta": 0,
            "trend": overall,
        }
    )
    return rows


def render_stability_trends_markdown_lines(
    *,
    history: Mapping[str, Any] | None = None,
    trend_rows: Sequence[Mapping[str, Any]] | None = None,
) -> list[str]:
    """Render longitudinal stability trend rows for markdown surfaces."""
    lines = ["## Stability Trends", ""]
    resolved_history = history if isinstance(history, Mapping) else {}
    sample_count = int(resolved_history.get("sample_count") or 0)
    trend_summary = (
        resolved_history.get("trend_summary")
        if isinstance(resolved_history.get("trend_summary"), Mapping)
        else {}
    )
    if sample_count < 2 or not trend_summary.get("comparison_available"):
        lines.extend(["Not enough stability history.", ""])
        return lines

    rows = list(trend_rows or stability_trend_rows_from_history(resolved_history))
    if not rows:
        lines.extend(["Not enough stability history.", ""])
        return lines

    lines.extend(
        [
            "| Bucket | Current | Previous | Delta | Trend |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        delta = int(row.get("delta") or 0)
        delta_s = f"+{delta}" if delta > 0 else str(delta)
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.get('owner_drift_bucket')}`",
                    f"`{int(row.get('current_count') or 0)}`",
                    f"`{int(row.get('previous_count') or 0)}`",
                    f"`{delta_s}`",
                    f"`{row.get('trend')}`",
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


STABILITY_HOTSPOT_BUCKETS: tuple[str, ...] = (
    "route_drift",
    "speaker_drift",
    "fallback_drift",
    "semantic_drift",
    "replay_drift_unclassified",
)


def _stability_hotspot_rank_key(row: Mapping[str, Any]) -> tuple[int, int, int, str]:
    return (
        -int(row.get("occurrence_count") or 0),
        -int(row.get("worsening_count") or 0),
        -int(row.get("degraded_count") or 0),
        str(row.get("owner_drift_bucket") or row.get("name") or ""),
    )


def _rank_stability_hotspot_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(entries, key=_stability_hotspot_rank_key)
    for index, row in enumerate(ordered, start=1):
        row["rank"] = index
    return ordered


def _stability_hotspot_worsening_counts(scorecards: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {bucket: 0 for bucket in STABILITY_HOTSPOT_BUCKETS}
    if len(scorecards) < 2:
        return counts
    for index in range(1, len(scorecards)):
        previous = _bucket_counts_for_stability_scorecard(scorecards[index - 1])
        current = _bucket_counts_for_stability_scorecard(scorecards[index])
        for bucket in STABILITY_HOTSPOT_BUCKETS:
            if int(current.get(bucket) or 0) > int(previous.get(bucket) or 0):
                counts[bucket] += 1
    return counts


def _stability_hotspot_degraded_counts(scorecards: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {bucket: 0 for bucket in STABILITY_HOTSPOT_BUCKETS}
    for scorecard in scorecards:
        if _scorecard_stability_status(scorecard) != "degraded":
            continue
        bucket_counts = _bucket_counts_for_stability_scorecard(scorecard)
        for bucket in STABILITY_HOTSPOT_BUCKETS:
            if int(bucket_counts.get(bucket) or 0) > 0:
                counts[bucket] += 1
    return counts


def _stability_hotspot_signal_worsening_counts(scorecards: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    if len(scorecards) < 2:
        return counts
    for index in range(1, len(scorecards)):
        previous = _signal_counts_for_stability_scorecard(scorecards[index - 1])
        current = _signal_counts_for_stability_scorecard(scorecards[index])
        for signal in sorted(set(previous) | set(current)):
            if int(current.get(signal) or 0) > int(previous.get(signal) or 0):
                counts[signal] = counts.get(signal, 0) + 1
    return counts


def _stability_hotspot_signal_degraded_counts(scorecards: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for scorecard in scorecards:
        if _scorecard_stability_status(scorecard) != "degraded":
            continue
        for signal, count in _signal_counts_for_stability_scorecard(scorecard).items():
            if int(count) > 0:
                counts[signal] = counts.get(signal, 0) + 1
    return counts


def _stability_hotspot_priority(
    *,
    occurrence_count: int,
    worsening_count: int,
    degraded_count: int,
) -> str:
    if occurrence_count <= 0:
        return "normal"
    if occurrence_count >= 3 and (worsening_count >= 1 or degraded_count >= 1):
        return "critical"
    if occurrence_count >= 2 and worsening_count >= 1:
        return "critical"
    if degraded_count >= 2:
        return "critical"
    if occurrence_count >= 2 or worsening_count >= 1 or degraded_count >= 1:
        return "elevated"
    return "normal"


def stability_hotspot_rows(
    bucket_rankings: Sequence[Mapping[str, Any]] | None,
    *,
    history: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Project ranked bucket hotspots into operator-facing hotspot rows."""
    trend_by_bucket: dict[str, str] = {}
    if isinstance(history, Mapping):
        trend_summary = (
            history.get("trend_summary")
            if isinstance(history.get("trend_summary"), Mapping)
            else {}
        )
        bucket_trends = (
            trend_summary.get("bucket_trends")
            if isinstance(trend_summary.get("bucket_trends"), Mapping)
            else {}
        )
        for bucket in STABILITY_HOTSPOT_BUCKETS:
            trend = bucket_trends.get(bucket) if isinstance(bucket_trends.get(bucket), Mapping) else {}
            trend_by_bucket[bucket] = str(trend.get("trend") or "insufficient_data")

    rows: list[dict[str, Any]] = []
    for entry in bucket_rankings or ():
        if not isinstance(entry, Mapping):
            continue
        bucket = str(entry.get("owner_drift_bucket") or "").strip()
        occurrence_count = int(entry.get("occurrence_count") or 0)
        if not bucket or occurrence_count <= 0:
            continue
        worsening_count = int(entry.get("worsening_count") or 0)
        degraded_count = int(entry.get("degraded_count") or 0)
        rows.append(
            {
                "rank": int(entry.get("rank") or 0),
                "owner_drift_bucket": bucket,
                "occurrence_count": occurrence_count,
                "scenario_count": int(entry.get("affected_scenarios") or 0),
                "worsening_count": worsening_count,
                "degraded_count": degraded_count,
                "trend": trend_by_bucket.get(bucket, "insufficient_data"),
                "priority": _stability_hotspot_priority(
                    occurrence_count=occurrence_count,
                    worsening_count=worsening_count,
                    degraded_count=degraded_count,
                ),
            }
        )
    return sorted(rows, key=lambda row: int(row.get("rank") or 0))


def build_stability_hotspots(
    scorecards: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    """Aggregate stability hotspot rankings across long-session scorecard history."""
    valid = _valid_stability_scorecards(scorecards)
    bucket_occurrence = {bucket: 0 for bucket in STABILITY_HOTSPOT_BUCKETS}
    bucket_scorecards: dict[str, set[int]] = {bucket: set() for bucket in STABILITY_HOTSPOT_BUCKETS}
    bucket_scenarios: dict[str, set[str]] = {bucket: set() for bucket in STABILITY_HOTSPOT_BUCKETS}

    signal_occurrence: dict[str, int] = {}
    signal_scorecards: dict[str, set[int]] = {}
    signal_scenarios: dict[str, set[str]] = {}

    scenario_occurrence: dict[str, int] = {}
    scenario_scorecards: dict[str, set[int]] = {}

    for index, scorecard in enumerate(valid):
        scenario_id = str(scorecard.get("scenario_id") or f"scorecard_{index:02d}")
        projected_rows = stability_classification_rows_from_scorecard(scorecard)
        if projected_rows:
            scenario_occurrence[scenario_id] = scenario_occurrence.get(scenario_id, 0) + len(projected_rows)
            scenario_scorecards.setdefault(scenario_id, set()).add(index)

        for row in projected_rows:
            bucket = str(row.get("owner_drift_bucket") or "").strip()
            signal = str(row.get("signal") or "").strip()
            if bucket in STABILITY_HOTSPOT_BUCKETS:
                bucket_occurrence[bucket] += 1
                bucket_scorecards[bucket].add(index)
                bucket_scenarios[bucket].add(scenario_id)
            if signal:
                signal_occurrence[signal] = signal_occurrence.get(signal, 0) + 1
                signal_scorecards.setdefault(signal, set()).add(index)
                signal_scenarios.setdefault(signal, set()).add(scenario_id)

    bucket_worsening = _stability_hotspot_worsening_counts(valid)
    bucket_degraded = _stability_hotspot_degraded_counts(valid)
    signal_worsening = _stability_hotspot_signal_worsening_counts(valid)
    signal_degraded = _stability_hotspot_signal_degraded_counts(valid)

    bucket_rankings = _rank_stability_hotspot_entries(
        [
            {
                "owner_drift_bucket": bucket,
                "occurrence_count": bucket_occurrence[bucket],
                "affected_scorecards": len(bucket_scorecards[bucket]),
                "affected_scenarios": len(bucket_scenarios[bucket]),
                "worsening_count": bucket_worsening.get(bucket, 0),
                "degraded_count": bucket_degraded.get(bucket, 0),
            }
            for bucket in STABILITY_HOTSPOT_BUCKETS
            if bucket_occurrence[bucket] > 0
        ]
    )

    signal_rankings = _rank_stability_hotspot_entries(
        [
            {
                "name": signal,
                "occurrence_count": count,
                "affected_scorecards": len(signal_scorecards.get(signal, set())),
                "affected_scenarios": len(signal_scenarios.get(signal, set())),
                "worsening_count": signal_worsening.get(signal, 0),
                "degraded_count": signal_degraded.get(signal, 0),
            }
            for signal, count in sorted(signal_occurrence.items())
            if count > 0
        ]
    )

    scenario_rankings = _rank_stability_hotspot_entries(
        [
            {
                "name": scenario_id,
                "occurrence_count": count,
                "affected_scorecards": len(scenario_scorecards.get(scenario_id, set())),
                "affected_scenarios": 1,
                "worsening_count": 0,
                "degraded_count": (
                    1
                    if any(
                        _scorecard_stability_status(valid[index]) == "degraded"
                        for index in scenario_scorecards.get(scenario_id, set())
                    )
                    else 0
                ),
            }
            for scenario_id, count in sorted(scenario_occurrence.items())
            if count > 0
        ]
    )

    history = build_long_session_stability_history(valid)
    return {
        "bucket_rankings": bucket_rankings,
        "signal_rankings": signal_rankings,
        "scenario_rankings": scenario_rankings,
        "hotspot_rows": stability_hotspot_rows(bucket_rankings, history=history),
    }


def render_stability_hotspots_markdown_lines(
    hotspot_rows: Sequence[Mapping[str, Any]] | None,
) -> list[str]:
    """Render stability hotspot rows for markdown surfaces."""
    lines = ["## Stability Hotspots", ""]
    rows = [row for row in (hotspot_rows or ()) if isinstance(row, Mapping)]
    if not rows:
        lines.extend(["No stability hotspots identified.", ""])
        return lines

    lines.extend(
        [
            "| Rank | Bucket | Occurrences | Scenarios | Trend | Priority |",
            "|---:|---|---:|---:|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row.get("rank") or 0)),
                    f"`{row.get('owner_drift_bucket')}`",
                    f"`{int(row.get('occurrence_count') or 0)}`",
                    f"`{int(row.get('scenario_count') or 0)}`",
                    f"`{row.get('trend')}`",
                    f"`{row.get('priority')}`",
                ]
            )
            + " |"
        )
    lines.append("")
    return lines
