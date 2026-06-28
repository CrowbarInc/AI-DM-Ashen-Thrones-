#!/usr/bin/env python3
"""Migrate unified bug recurrence event log into protected and session-diagnostic lanes.

Reporting-only. Classifies existing events with BQ3.6 commit-worthiness rules, archives
the original unified log byte-for-byte, splits populations into persistence lanes, and
regenerates protected replay recurrence history artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.failure_dashboard_report import (  # noqa: E402
    BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_HISTORY_JSON_PATH,
    BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_SESSION_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_SYNTHETIC_TEST_ARTIFACT_EVENT_LOG_JSON_PATH,
    write_bug_recurrence_artifact_set,
)
from tests.helpers.replay_bug_recurrence import (  # noqa: E402
    RECURRENCE_ADVISORY_ONLY,
    RECURRENCE_REPORT_ONLY,
    RECURRENCE_SCHEMA_VERSION,
    build_recurrence_key,
    calculate_protected_replay_regression_recurrence_rate,
    calculate_regression_recurrence_rate,
    classify_recurrence_event_commit_worthiness,
)

DEFAULT_MIGRATION_REPORT_PATH = ROOT / "docs" / "audits" / "BQ37_recurrence_history_migration.md"


def legacy_event_log_path(event_log_path: Path | str) -> Path:
    """Return the byte-for-byte archive path for a unified recurrence event log."""
    path = Path(event_log_path)
    return path.with_name(f"{path.stem}.legacy{path.suffix}")


def _event_log_envelope(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "events": [dict(event) for event in events if isinstance(event, Mapping)],
    }


def _unique_recurrence_keys(events: Sequence[Mapping[str, Any]]) -> set[str]:
    keys: set[str] = set()
    for event in events:
        if not isinstance(event, Mapping):
            continue
        key = str(event.get("recurrence_key") or build_recurrence_key(event)).strip()
        if key:
            keys.add(key)
    return keys


def _parse_event_log_bytes(payload: bytes) -> dict[str, Any]:
    raw = json.loads(payload.decode("utf-8"))
    if not isinstance(raw, Mapping) or not isinstance(raw.get("events"), list):
        raise ValueError("event log must be a JSON object with an events list")
    if raw.get("schema_version") != RECURRENCE_SCHEMA_VERSION:
        raise ValueError(f"unsupported event log schema_version: {raw.get('schema_version')!r}")
    return {
        "schema_version": RECURRENCE_SCHEMA_VERSION,
        "report_only": RECURRENCE_REPORT_ONLY,
        "advisory_only": RECURRENCE_ADVISORY_ONLY,
        "events": [dict(item) for item in raw["events"] if isinstance(item, Mapping)],
    }


def _load_source_event_log_bytes(
    event_log_path: Path,
    legacy_path: Path,
) -> tuple[bytes, str]:
    if legacy_path.is_file():
        return legacy_path.read_bytes(), "legacy_archive"
    if not event_log_path.is_file():
        raise FileNotFoundError(f"event log not found: {event_log_path}")
    return event_log_path.read_bytes(), "event_log"


def render_migration_report_markdown(result: Mapping[str, Any]) -> str:
    """Render the BQ3.7 migration audit report."""
    summary = result.get("summary") or {}
    protected = result.get("protected") or {}
    diagnostic = result.get("diagnostic") or {}
    session = result.get("session_diagnostic") or {}
    synthetic = result.get("synthetic_test_artifact") or {}
    verification = result.get("verification") or {}
    protected_metric = protected.get("regression_recurrence_rate") or {}
    lines = [
        "# BQ3.7 Recurrence History Migration",
        "",
        f"**Date:** {result.get('generated_at', '')}",
        f"**Source:** `{result.get('source_label', '')}`",
        "",
        "## Migration Summary",
        "",
        "| Population | Events |",
        "|---|---:|",
        f"| Original unified log | {int(summary.get('original_event_count') or 0)} |",
        f"| Protected replay history | {int(summary.get('protected_event_count') or 0)} |",
        f"| Session diagnostic history | {int(summary.get('session_diagnostic_event_count') or 0)} |",
        f"| Synthetic/test artifact history | {int(summary.get('synthetic_test_artifact_event_count') or 0)} |",
        f"| Legacy diagnostic compatibility output | {int(summary.get('diagnostic_event_count') or 0)} |",
        "",
        "## Protected Population",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Events | {int(protected.get('event_count') or 0)} |",
        f"| Unique Keys | {int(protected.get('unique_recurrence_keys') or 0)} |",
        f"| Numerator | {int(protected_metric.get('numerator') or 0)} |",
        f"| Denominator | {int(protected_metric.get('denominator') or 0)} |",
        f"| Rate | {float(protected_metric.get('rate') or 0.0):.1%} |",
        "",
        "## Session Diagnostic Population",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Events | {int(session.get('event_count') or 0)} |",
        f"| Unique Keys | {int(session.get('unique_recurrence_keys') or 0)} |",
        "",
        "## Synthetic/Test Artifact Population",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Events | {int(synthetic.get('event_count') or 0)} |",
        f"| Unique Keys | {int(synthetic.get('unique_recurrence_keys') or 0)} |",
        "",
        "## Legacy Diagnostic Compatibility Output",
        "",
        "Compatibility-only combined diagnostic output retained for existing consumers:",
        f"`{result.get('session_diagnostic_event_log_path', '')}`",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Events | {int(diagnostic.get('event_count') or 0)} |",
        f"| Unique Keys | {int(diagnostic.get('unique_recurrence_keys') or 0)} |",
        "",
        "## Archived Artifact",
        "",
        "Location:",
        f"`{result.get('legacy_archive_path', '')}`",
        "",
        "## Verification",
        "",
        "Confirm:",
        f"- no events lost: `{str(bool(verification.get('no_events_lost'))).lower()}`",
        f"- counts reconcile: `{str(bool(verification.get('counts_reconcile'))).lower()}`",
        f"- metrics regenerated: `{str(bool(verification.get('metrics_regenerated'))).lower()}`",
        f"- diagnostic keys absent from protected history: `{str(bool(verification.get('diagnostic_keys_absent_from_protected_history'))).lower()}`",
        "",
    ]
    if verification.get("notes"):
        lines.extend(["Notes:", ""])
        for note in verification["notes"]:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines)


def migrate_bug_recurrence_event_log(
    *,
    event_log_path: Path | str = BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    session_diagnostic_event_log_path: Path | str = BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH,
    session_event_log_path: Path | str = BUG_RECURRENCE_SESSION_EVENT_LOG_JSON_PATH,
    synthetic_test_artifact_event_log_path: Path | str = (
        BUG_RECURRENCE_SYNTHETIC_TEST_ARTIFACT_EVENT_LOG_JSON_PATH
    ),
    history_json_path: Path | str = BUG_RECURRENCE_HISTORY_JSON_PATH,
    history_md_path: Path | str = BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    legacy_archive_path: Path | str | None = None,
    report_path: Path | str = DEFAULT_MIGRATION_REPORT_PATH,
    dry_run: bool = False,
    report_only: bool = False,
    emit_recurrence_artifacts: bool = True,
    emit_compatibility_artifacts: bool = True,
    emit_governance_docs: bool = True,
    emit_audit_docs: bool = True,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Split a unified recurrence event log into protected, session, and synthetic lanes."""
    log_path = Path(event_log_path)
    compatibility_session_log_path = Path(session_diagnostic_event_log_path)
    session_log_path = Path(session_event_log_path)
    synthetic_log_path = Path(synthetic_test_artifact_event_log_path)
    history_json = Path(history_json_path)
    history_md = Path(history_md_path)
    legacy_path = Path(legacy_archive_path) if legacy_archive_path is not None else legacy_event_log_path(log_path)
    report_out = Path(report_path)

    source_bytes, source_label = _load_source_event_log_bytes(log_path, legacy_path)
    source_log = _parse_event_log_bytes(source_bytes)
    source_events = list(source_log.get("events") or [])
    classification = classify_recurrence_event_commit_worthiness(source_events)
    protected_events = list(classification["protected_replay_history"])
    session_events = list(classification["session_diagnostic_history"])
    synthetic_events = list(classification["synthetic_test_artifact_history"])
    diagnostic_events = list(classification["diagnostic_history"])

    protected_log = _event_log_envelope(protected_events)
    session_log = _event_log_envelope(session_events)
    synthetic_log = _event_log_envelope(synthetic_events)
    diagnostic_log = {**_event_log_envelope(diagnostic_events), "compatibility_only": True}
    protected_metric = calculate_protected_replay_regression_recurrence_rate(protected_log)
    diagnostic_metric = calculate_regression_recurrence_rate(diagnostic_log)

    original_count = len(source_events)
    protected_count = len(protected_events)
    session_count = len(session_events)
    synthetic_count = len(synthetic_events)
    diagnostic_count = len(diagnostic_events)
    protected_keys = _unique_recurrence_keys(protected_events)
    session_keys = _unique_recurrence_keys(session_events)
    synthetic_keys = _unique_recurrence_keys(synthetic_events)
    diagnostic_keys = _unique_recurrence_keys(diagnostic_events)

    verification_notes: list[str] = []
    counts_reconcile = protected_count + diagnostic_count == original_count
    no_events_lost = counts_reconcile
    if not counts_reconcile:
        verification_notes.append(
            f"protected ({protected_count}) + diagnostic ({diagnostic_count}) != original ({original_count})"
        )

    metrics_regenerated = False
    diagnostic_keys_absent_from_protected_history = protected_keys.isdisjoint(diagnostic_keys)

    generated_timestamp = (
        generated_at
        or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    command_used = (
        "tools/migrate_bug_recurrence_event_log.py "
        f"--event-log {log_path.as_posix()}"
    )
    archive_created = legacy_path.is_file()
    written_paths: dict[str, list[str]] = {
        "recurrence_artifacts": [],
        "compatibility_artifacts": [],
        "governance_reports": [],
        "audit_reports": [],
    }

    if not dry_run and not report_only:
        if emit_compatibility_artifacts and not legacy_path.is_file():
            legacy_path.parent.mkdir(parents=True, exist_ok=True)
            legacy_path.write_bytes(source_bytes)
            archive_created = True
            written_paths["compatibility_artifacts"].append(str(legacy_path.as_posix()))

        phase_written_paths = write_bug_recurrence_artifact_set(
            protected_log=protected_log,
            session_diagnostic_log=session_log,
            synthetic_test_artifact_log=synthetic_log,
            compatibility_diagnostic_log=diagnostic_log,
            event_log_path=log_path,
            session_event_log_path=session_log_path,
            synthetic_test_artifact_event_log_path=synthetic_log_path,
            session_diagnostic_event_log_path=compatibility_session_log_path,
            history_json_path=history_json,
            history_md_path=history_md,
            command_used=command_used,
            generated_at=generated_timestamp,
            emit_recurrence_artifacts=emit_recurrence_artifacts,
            emit_compatibility_artifacts=emit_compatibility_artifacts,
            emit_governance_docs=emit_governance_docs,
            emit_trajectory_history=emit_governance_docs,
        )
        for phase, paths in phase_written_paths.items():
            written_paths.setdefault(phase, []).extend(paths)
        metrics_regenerated = emit_recurrence_artifacts and history_json.is_file() and history_md.is_file()
        if metrics_regenerated:
            reloaded_history = json.loads(history_json.read_text(encoding="utf-8"))
            history_keys = {
                str(entry.get("recurrence_key") or "")
                for entry in reloaded_history.get("recurrences") or []
                if isinstance(entry, Mapping)
            }
            diagnostic_keys_absent_from_protected_history = diagnostic_keys.isdisjoint(history_keys)
    elif report_only:
        metrics_regenerated = False
    else:
        metrics_regenerated = False

    result: dict[str, Any] = {
        "generated_at": generated_timestamp,
        "command_used": command_used,
        "source_label": source_label,
        "legacy_archive_path": str(legacy_path.as_posix()),
        "event_log_path": str(log_path.as_posix()),
        "session_diagnostic_event_log_path": str(compatibility_session_log_path.as_posix()),
        "session_event_log_path": str(session_log_path.as_posix()),
        "synthetic_test_artifact_event_log_path": str(synthetic_log_path.as_posix()),
        "history_json_path": str(history_json.as_posix()),
        "history_md_path": str(history_md.as_posix()),
        "dry_run": dry_run,
        "report_only": report_only,
        "write_phases": {
            "recurrence_artifacts": emit_recurrence_artifacts,
            "compatibility_artifacts": emit_compatibility_artifacts,
            "governance_reports": emit_governance_docs,
            "audit_reports": emit_audit_docs,
        },
        "written_paths": written_paths,
        "archive_created": archive_created,
        "summary": {
            "original_event_count": original_count,
            "protected_event_count": protected_count,
            "session_diagnostic_event_count": session_count,
            "synthetic_test_artifact_event_count": synthetic_count,
            "diagnostic_event_count": diagnostic_count,
        },
        "protected": {
            "event_count": protected_count,
            "unique_recurrence_keys": len(protected_keys),
            "regression_recurrence_rate": protected_metric,
        },
        "session_diagnostic": {
            "event_count": session_count,
            "unique_recurrence_keys": len(session_keys),
        },
        "synthetic_test_artifact": {
            "event_count": synthetic_count,
            "unique_recurrence_keys": len(synthetic_keys),
        },
        "diagnostic": {
            "event_count": diagnostic_count,
            "unique_recurrence_keys": len(diagnostic_keys),
            "regression_recurrence_rate": diagnostic_metric,
            "compatibility_only": True,
        },
        "verification": {
            "no_events_lost": no_events_lost,
            "counts_reconcile": counts_reconcile,
            "metrics_regenerated": metrics_regenerated,
            "diagnostic_keys_absent_from_protected_history": diagnostic_keys_absent_from_protected_history,
            "notes": verification_notes,
        },
        "classifications": classification["classifications"],
    }

    if not dry_run and emit_audit_docs:
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(render_migration_report_markdown(result), encoding="utf-8")
        result["report_path"] = str(report_out.as_posix())
        result["written_paths"]["audit_reports"].append(str(report_out.as_posix()))

    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--event-log",
        type=Path,
        default=BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
        help="Unified recurrence event log to migrate.",
    )
    parser.add_argument(
        "--session-diagnostic-event-log",
        type=Path,
        default=BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH,
        help="Legacy combined diagnostic recurrence event log compatibility output path.",
    )
    parser.add_argument(
        "--session-event-log",
        type=Path,
        default=BUG_RECURRENCE_SESSION_EVENT_LOG_JSON_PATH,
        help="Explicit session diagnostic recurrence event log output path.",
    )
    parser.add_argument(
        "--synthetic-test-artifact-event-log",
        type=Path,
        default=BUG_RECURRENCE_SYNTHETIC_TEST_ARTIFACT_EVENT_LOG_JSON_PATH,
        help="Explicit synthetic/test artifact recurrence event log output path.",
    )
    parser.add_argument(
        "--history-json",
        type=Path,
        default=BUG_RECURRENCE_HISTORY_JSON_PATH,
        help="Protected replay recurrence history JSON output path.",
    )
    parser.add_argument(
        "--history-md",
        type=Path,
        default=BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
        help="Protected replay recurrence history markdown output path.",
    )
    parser.add_argument(
        "--legacy-archive",
        type=Path,
        default=None,
        help="Optional override for the byte-for-byte legacy archive path.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_MIGRATION_REPORT_PATH,
        help="Migration audit report markdown output path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Classify and summarize without writing artifacts.",
    )
    parser.add_argument(
        "--generated-at",
        default=None,
        help="Optional ISO timestamp recorded in regenerated artifact headers.",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write the migration audit report without rewriting lane artifacts.",
    )
    parser.add_argument(
        "--recurrence-artifacts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable or disable protected history plus explicit lane recurrence artifacts.",
    )
    parser.add_argument(
        "--compatibility-artifacts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable or disable legacy archive and compatibility diagnostic output.",
    )
    parser.add_argument(
        "--governance-docs",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable or disable supplementary governance documents and trajectory reports.",
    )
    parser.add_argument(
        "--audit-docs",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable or disable migration audit report output.",
    )
    parser.add_argument(
        "--recurrence-only",
        action="store_true",
        help=(
            "Write only protected history and explicit recurrence lane artifacts; "
            "suppresses compatibility, governance, and audit outputs."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    emit_recurrence_artifacts = bool(args.recurrence_artifacts)
    emit_compatibility_artifacts = bool(args.compatibility_artifacts)
    emit_governance_docs = bool(args.governance_docs)
    emit_audit_docs = bool(args.audit_docs)
    if args.recurrence_only:
        emit_recurrence_artifacts = True
        emit_compatibility_artifacts = False
        emit_governance_docs = False
        emit_audit_docs = False
    try:
        result = migrate_bug_recurrence_event_log(
            event_log_path=args.event_log,
            session_diagnostic_event_log_path=args.session_diagnostic_event_log,
            session_event_log_path=args.session_event_log,
            synthetic_test_artifact_event_log_path=args.synthetic_test_artifact_event_log,
            history_json_path=args.history_json,
            history_md_path=args.history_md,
            legacy_archive_path=args.legacy_archive,
            report_path=args.report,
            dry_run=args.dry_run,
            report_only=args.report_only,
            emit_recurrence_artifacts=emit_recurrence_artifacts,
            emit_compatibility_artifacts=emit_compatibility_artifacts,
            emit_governance_docs=emit_governance_docs,
            emit_audit_docs=emit_audit_docs,
            generated_at=args.generated_at,
        )
    except (OSError, UnicodeError, ValueError, FileNotFoundError) as exc:
        print(f"Bug recurrence migration failed: {exc}", file=sys.stderr)
        return 2

    summary = result["summary"]
    protected_metric = result["protected"]["regression_recurrence_rate"]
    print(f"Source: {result['source_label']}")
    print(f"Original events: {summary['original_event_count']}")
    print(f"Protected events: {summary['protected_event_count']}")
    print(f"Session diagnostic events: {summary['session_diagnostic_event_count']}")
    print(f"Synthetic/test artifact events: {summary['synthetic_test_artifact_event_count']}")
    print(f"Legacy diagnostic compatibility events: {summary['diagnostic_event_count']}")
    print(
        "Protected recurrence rate: "
        f"{protected_metric['numerator']}/{protected_metric['denominator']} "
        f"({protected_metric['rate']:.1%})"
    )
    if args.dry_run:
        print("Dry run: no artifacts written.")
    elif args.report_only:
        if emit_audit_docs:
            print(f"Report only: wrote {result.get('report_path', args.report)}")
        else:
            print("Report only: audit docs disabled; no artifacts written.")
    else:
        if emit_compatibility_artifacts:
            print(f"Legacy archive: {result['legacy_archive_path']}")
        else:
            print("Compatibility artifacts disabled.")
        if emit_audit_docs:
            print(f"Migration report: {result.get('report_path', args.report)}")
        else:
            print("Audit docs disabled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
