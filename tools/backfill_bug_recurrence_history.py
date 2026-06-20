#!/usr/bin/env python3
"""Backfill bug-class recurrence history from a protected replay failure report.

Reporting-only. Parses committed failure-report markdown, appends deduped events
to the recurrence event log, and regenerates recurrence history artifacts.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.failure_dashboard_report import (  # noqa: E402
    BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_HISTORY_JSON_PATH,
    BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    PROTECTED_REPLAY_FAILURE_REPORT_PATH,
    protected_replay_recurrence_event_metadata,
    write_bug_recurrence_history_artifacts,
)
from tests.helpers.replay_bug_recurrence import (  # noqa: E402
    BACKFILL_PROTECTED_REPLAY_PERSISTENCE_INTENT,
    existing_backfill_dedupe_keys,
    load_recurrence_event_log,
    recurrence_backfill_dedupe_key,
)
from tests.helpers.replay_drift_taxonomy import classify_owner_drift_bucket  # noqa: E402

FAILURE_TABLE_HEADING = "## Failure Table"
_MISSING_CELL_VALUES = frozenset({"", "none", "unknown", "unavailable", "n/a"})


def _artifact_source_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _unwrap_backticks(value: str) -> str:
    return value.strip().strip("`")


def _clean_cell(value: Any) -> str:
    text = _unwrap_backticks(str(value or ""))
    return "" if text.lower() in _MISSING_CELL_VALUES else text


def _field_path_from_invariant(failed_invariant: str) -> str | None:
    text = _clean_cell(failed_invariant)
    if not text:
        return None
    if ": " in text:
        return text.split(": ", 1)[0].strip() or None
    return text


def parse_run_summary(markdown: str) -> dict[str, str]:
    """Extract command and generated-at metadata from the report header."""
    summary = {"command": "", "generated_at": ""}
    for line in markdown.splitlines():
        if line.startswith("- Command:"):
            summary["command"] = _unwrap_backticks(line.split(":", 1)[1])
        elif line.startswith("- Generated at:"):
            summary["generated_at"] = _unwrap_backticks(line.split(":", 1)[1])
    return summary


def _failure_table_lines(markdown: str) -> tuple[list[str], list[str]] | None:
    lines = markdown.splitlines()
    section_start = next((index for index, line in enumerate(lines) if line.strip() == FAILURE_TABLE_HEADING), None)
    if section_start is None:
        return None

    header_index = next(
        (
            index
            for index in range(section_start + 1, len(lines))
            if lines[index].startswith("| Scenario |")
        ),
        None,
    )
    if header_index is None:
        return None

    headers = [header.strip() for header in lines[header_index].strip("|").split("|")]
    data_lines: list[str] = []
    for line in lines[header_index + 2 :]:
        if not line.startswith("|"):
            break
        if line.startswith("|---"):
            continue
        data_lines.append(line)
    return headers, data_lines


def _row_from_table(headers: Sequence[str], line: str) -> dict[str, str]:
    cells = [cell.strip() for cell in line.strip("|").split("|")]
    if len(cells) < len(headers):
        cells.extend([""] * (len(headers) - len(cells)))
    return {header: cells[index] for index, header in enumerate(headers)}


def classification_row_from_failure_table_row(
    table_row: Mapping[str, str],
    *,
    warnings: list[str] | None = None,
) -> dict[str, Any] | None:
    """Convert one Failure Table row into a recurrence classification row."""
    scenario_id = _clean_cell(table_row.get("Scenario"))
    category = _clean_cell(table_row.get("Category"))
    investigate_first = _clean_cell(table_row.get("Investigate First"))
    field_path = _field_path_from_invariant(str(table_row.get("Failed Invariant") or ""))
    turn_text = _clean_cell(table_row.get("Turn"))
    turn_index = int(turn_text) if turn_text.isdigit() else None

    missing = [
        label
        for label, value in (
            ("scenario_id", scenario_id),
            ("category", category),
            ("field_path", field_path),
            ("investigate_first", investigate_first),
        )
        if not value
    ]
    if missing:
        if warnings is not None:
            warnings.append(
                f"skipped failure-table row for scenario {scenario_id or '<unknown>'}: missing {', '.join(missing)}"
            )
        return None

    drift_type = _clean_cell(table_row.get("Drift Type")) or "unknown"
    owner_drift_bucket = _clean_cell(table_row.get("Owner Drift Bucket"))
    if not owner_drift_bucket:
        owner_drift_bucket = classify_owner_drift_bucket(
            field_path=field_path,
            category=category,
            measurement_drift_bucket=drift_type,
            replay_tags=[drift_type] if drift_type else None,
        )

    row: dict[str, Any] = {
        "scenario_id": scenario_id,
        "turn_index": turn_index,
        "category": category,
        "primary_owner": _clean_cell(table_row.get("Primary Owner")) or None,
        "owner_drift_bucket": owner_drift_bucket,
        "field_path": field_path,
        "investigate_first": investigate_first,
    }
    test_node_id = _clean_cell(table_row.get("Test Node"))
    if test_node_id:
        row["test_node_id"] = test_node_id
    return row


def parse_failure_report_classification_rows(
    markdown: str,
    *,
    warnings: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Parse recurrence classification rows from a protected failure report."""
    parsed_table = _failure_table_lines(markdown)
    if parsed_table is None:
        return []
    headers, data_lines = parsed_table
    rows: list[dict[str, Any]] = []
    for line in data_lines:
        table_row = _row_from_table(headers, line)
        classification_row = classification_row_from_failure_table_row(table_row, warnings=warnings)
        if classification_row is not None:
            rows.append(classification_row)
    return rows


def filter_rows_for_backfill(
    rows: Sequence[Mapping[str, Any]],
    event_log: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split parsed rows into appendable rows and already-present duplicates."""
    existing_keys = existing_backfill_dedupe_keys(event_log)
    appendable: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        dedupe_key = recurrence_backfill_dedupe_key(row, metadata)
        if dedupe_key and dedupe_key in existing_keys:
            skipped.append(dict(row))
            continue
        appendable.append(dict(row))
        if dedupe_key:
            existing_keys.add(dedupe_key)
    return appendable, skipped


def backfill_bug_recurrence_history(
    *,
    failure_report_path: Path | str,
    event_log_path: Path | str = BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    history_json_path: Path | str = BUG_RECURRENCE_HISTORY_JSON_PATH,
    history_md_path: Path | str = BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    dry_run: bool = False,
    check: bool = False,
) -> dict[str, Any]:
    """Parse a failure report and append deduped recurrence events."""
    report_path = Path(failure_report_path)
    if not report_path.is_file():
        raise FileNotFoundError(f"failure report not found: {report_path}")

    markdown = report_path.read_text(encoding="utf-8")
    warnings: list[str] = []
    summary = parse_run_summary(markdown)
    parsed_rows = parse_failure_report_classification_rows(markdown, warnings=warnings)
    artifact_source = _artifact_source_path(report_path)
    metadata = protected_replay_recurrence_event_metadata(
        command_used=summary.get("command") or None,
        generated_at=summary.get("generated_at") or None,
        artifact_source=artifact_source,
        persistence_intent=BACKFILL_PROTECTED_REPLAY_PERSISTENCE_INTENT,
    )

    event_log = load_recurrence_event_log(event_log_path)
    appendable_rows, skipped_rows = filter_rows_for_backfill(parsed_rows, event_log, metadata)

    result: dict[str, Any] = {
        "failure_report_path": str(report_path),
        "parsed_row_count": len(parsed_rows),
        "append_count": len(appendable_rows),
        "skipped_duplicate_count": len(skipped_rows),
        "warnings": warnings,
        "dry_run": dry_run,
        "check": check,
        "generated_at": summary.get("generated_at") or "",
        "command": summary.get("command") or "",
    }

    if check:
        result["check_passed"] = not appendable_rows
        if appendable_rows:
            raise SystemExit(
                f"Backfill check failed: {len(appendable_rows)} parseable recurrence row(s) missing from event log"
            )
        return result

    if dry_run:
        result["would_append"] = appendable_rows
        return result

    write_bug_recurrence_history_artifacts(
        appendable_rows,
        json_path=history_json_path,
        markdown_path=history_md_path,
        event_log_path=event_log_path,
        command_used=summary.get("command")
        or f"tools/backfill_bug_recurrence_history.py --failure-report {artifact_source}",
        generated_at=summary.get("generated_at") or None,
        recurrence_event_metadata=metadata,
    )
    updated_log = load_recurrence_event_log(event_log_path)
    result["event_log_count"] = len(updated_log.get("events") or [])
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--failure-report",
        type=Path,
        default=PROTECTED_REPLAY_FAILURE_REPORT_PATH,
        help="Protected replay failure report markdown to parse.",
    )
    parser.add_argument(
        "--history-json",
        type=Path,
        default=BUG_RECURRENCE_HISTORY_JSON_PATH,
        help="Bug recurrence history JSON output path.",
    )
    parser.add_argument(
        "--history-md",
        type=Path,
        default=BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
        help="Bug recurrence history markdown output path.",
    )
    parser.add_argument(
        "--event-log",
        type=Path,
        default=BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
        help="Bug recurrence append-only event log path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print parsed rows and append plan without writing artifacts.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if parseable report rows are missing from the event log.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = backfill_bug_recurrence_history(
            failure_report_path=args.failure_report,
            event_log_path=args.event_log,
            history_json_path=args.history_json,
            history_md_path=args.history_md,
            dry_run=args.dry_run,
            check=args.check,
        )
    except (OSError, UnicodeError, ValueError, FileNotFoundError) as exc:
        print(f"Bug recurrence backfill failed: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"Parsed rows: {result['parsed_row_count']}")
        print(f"Would append: {result['append_count']}")
        print(f"Would skip duplicates: {result['skipped_duplicate_count']}")
        for warning in result.get("warnings", []):
            print(f"warning: {warning}", file=sys.stderr)
        return 0

    if args.check:
        print("Backfill check passed.")
        return 0

    print(f"Parsed rows: {result['parsed_row_count']}")
    print(f"Appended events: {result['append_count']}")
    print(f"Skipped duplicates: {result['skipped_duplicate_count']}")
    print(f"Event log events: {result.get('event_log_count', 0)}")
    for warning in result.get("warnings", []):
        print(f"warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
