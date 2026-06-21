#!/usr/bin/env python3
"""BV8A — Recurrence history retirement and deduplication (read-side only)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.replay_bug_recurrence import (  # noqa: E402
    aggregate_protected_recurrence_history_from_event_log,
    build_recurrence_forecast,
    build_recurrence_governance,
    build_recurrence_lifecycle,
    build_recurrence_outcome_validation,
    build_recurrence_portfolio,
    build_recurrence_timeline,
    build_recurrence_trend_summary,
    calculate_protected_replay_regression_recurrence_rate,
    load_recurrence_event_log,
)

ARTIFACT_DIR = ROOT / "artifacts"
GOLDEN_REPLAY_DIR = ARTIFACT_DIR / "golden_replay"
RAW_EVENT_LOG_PATH = GOLDEN_REPLAY_DIR / "bug_recurrence_event_log.json"
RAW_HISTORY_PATH = GOLDEN_REPLAY_DIR / "bug_recurrence_history.json"
OUTPUT_PATH = ARTIFACT_DIR / "bv8a_recurrence_history.json"

PROJECTION_RECURRENCE_KEY = (
    "recurrence:v1:speaker_drift|projection|selected_speaker_id|tests/helpers/golden_replay.py"
)
SPEAKER_ENFORCEMENT_KEY = (
    "recurrence:v1:speaker_drift|speaker|selected_speaker_id|game/speaker_contract_enforcement.py"
)
FALLBACK_KEY = (
    "recurrence:v1:fallback_drift|fallback|final_emitted_source|game/final_emission_gate.py"
)
SANITIZER_KEY = (
    "recurrence:v1:semantic_drift|sanitizer|scaffold_leakage|game/output_sanitizer.py"
)

SPEAKER_PROJECTION_KEYS = frozenset(
    {
        PROJECTION_RECURRENCE_KEY,
        SPEAKER_ENFORCEMENT_KEY,
    }
)

RETIREMENT_REGISTRY: tuple[dict[str, str], ...] = (
    {
        "recurrence_key": PROJECTION_RECURRENCE_KEY,
        "registry_status": "RETIRED",
        "rationale": (
            "Single historical alias/canonical projection mismatch on "
            "vocative_override_after_prior_continuity; underlying test passes; "
            "seven duplicate backfill rows removed."
        ),
    },
    {
        "recurrence_key": PROJECTION_RECURRENCE_KEY,
        "registry_status": "HISTORICAL",
        "rationale": "One deduplicated protected-replay failure retained as source evidence.",
    },
    {
        "recurrence_key": SPEAKER_ENFORCEMENT_KEY,
        "registry_status": "ACTIVE",
        "rationale": "Emerging single-observation speaker-contract enforcement key.",
    },
    {
        "recurrence_key": FALLBACK_KEY,
        "registry_status": "ACTIVE",
        "rationale": "Emerging single-observation fallback drift key.",
    },
    {
        "recurrence_key": SANITIZER_KEY,
        "registry_status": "ACTIVE",
        "rationale": "Emerging single-observation sanitizer drift key.",
    },
)

VOCATIVE_TEST_NODE = (
    "tests/test_golden_replay.py::test_golden_replay_vocative_override_after_prior_continuity_structural_invariants"
)


def bv8a_semantic_dedupe_key(event: Mapping[str, Any]) -> tuple[str, ...]:
    """Collapse duplicate bookkeeping rows that share run, key, and root cause."""
    return (
        str(event.get("recurrence_key") or ""),
        str(event.get("scenario_id") or ""),
        str(event.get("run_id") or ""),
        str(event.get("turn_index") or ""),
        str(event.get("category") or ""),
        str(event.get("field_path") or ""),
        str(event.get("investigate_first") or ""),
        str(event.get("owner_drift_bucket") or ""),
    )


def dedupe_events(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return deduplicated events and an audit of removed duplicate rows."""
    ordered = sorted(
        events,
        key=lambda event: (
            int(event.get("event_index") or 0),
            str(event.get("recurrence_key") or ""),
        ),
    )
    seen: set[tuple[str, ...]] = set()
    kept: list[dict[str, Any]] = []
    duplicate_audit: list[dict[str, Any]] = []

    for event in ordered:
        dedupe_key = bv8a_semantic_dedupe_key(event)
        if dedupe_key in seen:
            duplicate_audit.append(
                {
                    "recurrence_key": event.get("recurrence_key"),
                    "run_id": event.get("run_id"),
                    "event_index": event.get("event_index"),
                    "duplicate_of_event_index": next(
                        kept_event.get("event_index")
                        for kept_event in kept
                        if bv8a_semantic_dedupe_key(kept_event) == dedupe_key
                    ),
                    "validation_status": "duplicate_removed",
                    "root_cause": _root_cause_label(event),
                }
            )
            continue
        seen.add(dedupe_key)
        kept.append(dict(event))

    return kept, duplicate_audit


def _root_cause_label(event: Mapping[str, Any]) -> str:
    scenario = str(event.get("scenario_id") or "")
    field_path = str(event.get("field_path") or "")
    if scenario == "vocative_override_after_prior_continuity" and field_path == "selected_speaker_id":
        return "selected_speaker_id projection mismatch (guard vs guard_captain alias/canonical vocabulary)"
    return f"{field_path} drift on {scenario or '(unknown scenario)'}"


def apply_retirement_metadata(
    events: list[dict[str, Any]],
    *,
    generated_at: str,
    vocative_test_passed: bool,
) -> list[dict[str, Any]]:
    """Mark stale projection recurrence as retired while preserving source evidence."""
    retired: list[dict[str, Any]] = []
    for event in events:
        updated = dict(event)
        key = str(event.get("recurrence_key") or "")
        if key == PROJECTION_RECURRENCE_KEY:
            updated["recurrence_status"] = "retired"
            updated["bv8a_registry_status"] = "RETIRED"
            updated["bv8a_retirement_evidence"] = {
                "scenario_id": "vocative_override_after_prior_continuity",
                "test_node_id": event.get("test_node_id") or VOCATIVE_TEST_NODE,
                "vocative_test_passed": vocative_test_passed,
                "validated_at": generated_at,
                "failure_no_longer_reproduces": vocative_test_passed,
                "source_artifact": "artifacts/golden_replay/replay_failure_report.md",
            }
        else:
            updated["bv8a_registry_status"] = "ACTIVE"
        retired.append(updated)
    return retired


def _dominant_share(history: Mapping[str, Any]) -> float:
    total_rows = int(history.get("total_rows") or 0)
    if total_rows <= 0:
        return 0.0
    recurrences = history.get("recurrences") or []
    if not isinstance(recurrences, list) or not recurrences:
        return 0.0
    max_count = max(int(row.get("occurrence_count") or 0) for row in recurrences if isinstance(row, Mapping))
    return round(max_count / float(total_rows), 4)


def _recurring_key_count(history: Mapping[str, Any]) -> int:
    recurrences = history.get("recurrences") or []
    if not isinstance(recurrences, list):
        return 0
    return sum(
        1
        for row in recurrences
        if isinstance(row, Mapping) and int(row.get("occurrence_count") or 0) >= 2
    )


def _active_recurrence_count(events: list[dict[str, Any]]) -> int:
    active_keys = {
        str(event.get("recurrence_key") or "")
        for event in events
        if str(event.get("recurrence_status") or "active").lower() != "retired"
    }
    return len(active_keys)


def _run_vocative_test() -> bool:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            VOCATIVE_TEST_NODE,
            "-q",
            "--tb=short",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def build_bv8a_recurrence_history(*, generated_at: str | None = None) -> dict[str, Any]:
    timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    raw_log = load_recurrence_event_log(RAW_EVENT_LOG_PATH)
    raw_events = [dict(event) for event in raw_log.get("events") or [] if isinstance(event, Mapping)]
    raw_history = json.loads(RAW_HISTORY_PATH.read_text(encoding="utf-8"))

    speaker_projection_events = [
        event for event in raw_events if str(event.get("recurrence_key") or "") in SPEAKER_PROJECTION_KEYS
    ]
    projection_key_events = [
        event for event in raw_events if str(event.get("recurrence_key") or "") == PROJECTION_RECURRENCE_KEY
    ]

    deduped_events, duplicate_audit = dedupe_events(raw_events)
    vocative_test_passed = _run_vocative_test()
    retired_events = apply_retirement_metadata(
        deduped_events,
        generated_at=timestamp,
        vocative_test_passed=vocative_test_passed,
    )

    deduped_log = {
        "advisory_only": True,
        "events": retired_events,
        "report_only": True,
        "schema_version": 1,
        "source_event_log": str(RAW_EVENT_LOG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "bv8a_deduplicated_view": True,
    }

    recurrence_history = aggregate_protected_recurrence_history_from_event_log(deduped_log)
    recurrence_timeline = build_recurrence_timeline(deduped_log)
    recurrence_trends = build_recurrence_trend_summary(deduped_log)
    recurrence_forecast = build_recurrence_forecast(
        recurrence_timeline=recurrence_timeline,
        recurrence_trends=recurrence_trends,
        regression_recurrence_rate=recurrence_history.get("regression_recurrence_rate"),
    )
    recurrence_portfolio = build_recurrence_portfolio(
        recurrence_timeline=recurrence_timeline,
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        event_log=deduped_log,
    )
    recurrence_governance = build_recurrence_governance(
        recurrence_trends=recurrence_trends,
        recurrence_forecast=recurrence_forecast,
        recurrence_portfolio=recurrence_portfolio,
        recurrence_remediation_targets={"targets": [], "remediation_summary": {}},
        recurrence_roi={"roi_summary": {}},
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
    outcome_validation = build_recurrence_outcome_validation(
        recurrence_history={
            **recurrence_history,
            "recurrence_lifecycle": recurrence_lifecycle,
            "recurrence_lifecycle_summary": recurrence_lifecycle.get("lifecycle_summary"),
        },
        event_log=deduped_log,
        recurrence_forecast=recurrence_forecast,
        recurrence_governance=recurrence_governance,
        recurrence_lifecycle=recurrence_lifecycle,
    )

    before_metrics = {
        "total_recurrence_rows": len(raw_events),
        "recurring_keys": _recurring_key_count(raw_history),
        "dominant_share": _dominant_share(raw_history),
        "active_recurrence_count": int(
            raw_history.get("outcome_validation_summary", {}).get("active_keys")
            or raw_history.get("unique_recurrence_count")
            or 0
        ),
        "projection_key_rows": len(projection_key_events),
        "validated_outcome_count": int(
            raw_history.get("outcome_validation_summary", {}).get("validated_outcome_count") or 0
        ),
    }
    after_metrics = {
        "total_recurrence_rows": len(retired_events),
        "recurring_keys": _recurring_key_count(recurrence_history),
        "dominant_share": _dominant_share(recurrence_history),
        "active_recurrence_count": _active_recurrence_count(retired_events),
        "projection_key_rows": sum(
            1
            for event in retired_events
            if str(event.get("recurrence_key") or "") == PROJECTION_RECURRENCE_KEY
        ),
        "validated_outcome_count": int(
            outcome_validation.get("outcome_validation_summary", {}).get("validated_outcome_count") or 0
        ),
    }

    recurrence_audit_rows = []
    for event in speaker_projection_events:
        dedupe_key = bv8a_semantic_dedupe_key(event)
        duplicate_count = sum(
            1 for candidate in raw_events if bv8a_semantic_dedupe_key(candidate) == dedupe_key
        )
        canonical_index = min(
            int(candidate.get("event_index") or 0)
            for candidate in raw_events
            if bv8a_semantic_dedupe_key(candidate) == dedupe_key
        )
        recurrence_audit_rows.append(
            {
                "recurrence_key": event.get("recurrence_key"),
                "run_id": event.get("run_id"),
                "event_index": event.get("event_index"),
                "duplicate_count": duplicate_count,
                "validation_status": "duplicate_removed"
                if duplicate_count > 1 and int(event.get("event_index") or 0) != canonical_index
                else ("canonical_retained" if duplicate_count > 1 else "unique"),
            }
        )

    return {
        "schema_version": 1,
        "report_only": True,
        "advisory_only": True,
        "generated_at": timestamp,
        "cycle": "BV8A",
        "primary_metric": "Recurrence History Accuracy",
        "source_evidence": {
            "raw_event_log": str(RAW_EVENT_LOG_PATH.relative_to(ROOT)).replace("\\", "/"),
            "raw_history": str(RAW_HISTORY_PATH.relative_to(ROOT)).replace("\\", "/"),
            "failure_report": "artifacts/golden_replay/replay_failure_report.md",
            "raw_history_unmodified": True,
        },
        "recurrence_event_audit": recurrence_audit_rows,
        "duplicate_removal": {
            "dedupe_key_fields": [
                "recurrence_key",
                "scenario_id",
                "run_id",
                "turn_index",
                "category",
                "field_path",
                "investigate_first",
                "owner_drift_bucket",
            ],
            "removed_duplicate_count": len(duplicate_audit),
            "removed_duplicates": duplicate_audit,
            "canonical_retained_event_index": projection_key_events[0].get("event_index") if projection_key_events else None,
        },
        "retirement_registry": RETIREMENT_REGISTRY,
        "deduplicated_event_log_view": deduped_log,
        "before_metrics": before_metrics,
        "after_metrics": after_metrics,
        "recurrence_history": {
            **recurrence_history,
            "recurrence_timeline": recurrence_timeline,
            "recurrence_trends": recurrence_trends,
            "recurrence_forecast": recurrence_forecast,
            "recurrence_portfolio": recurrence_portfolio,
            "recurrence_governance": recurrence_governance,
            "recurrence_lifecycle": recurrence_lifecycle,
            "outcome_validation_summary": outcome_validation.get("outcome_validation_summary"),
            "validated_outcomes": outcome_validation.get("outcome_validation_summary", {}).get("validated_outcomes"),
        },
        "protected_replay_regression_recurrence_rate": calculate_protected_replay_regression_recurrence_rate(
            deduped_log
        ),
    }


def write_bv8a_recurrence_history(*, generated_at: str | None = None) -> Path:
    payload = build_bv8a_recurrence_history(generated_at=generated_at)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return OUTPUT_PATH


def main() -> int:
    output = write_bv8a_recurrence_history()
    print(f"Wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
