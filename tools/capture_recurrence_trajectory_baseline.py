#!/usr/bin/env python3
"""Capture or refresh protected replay recurrence trajectory baseline snapshots.

Reporting-only. Regenerates recurrence history artifacts and appends a deduped
trajectory snapshot to recurrence_trajectory_history.json.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.failure_dashboard_report import (  # noqa: E402
    BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_HISTORY_JSON_PATH,
    BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH,
    write_bug_recurrence_history_artifacts,
)


def capture_recurrence_trajectory_baseline(
    *,
    event_log_path: Path | str = BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    history_json_path: Path | str = BUG_RECURRENCE_HISTORY_JSON_PATH,
    history_md_path: Path | str = BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    trajectory_history_path: Path | str = RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH,
    generated_at: str | None = None,
) -> dict[str, object]:
    """Regenerate recurrence history and capture a trajectory snapshot."""
    write_bug_recurrence_history_artifacts(
        [],
        json_path=history_json_path,
        markdown_path=history_md_path,
        event_log_path=event_log_path,
        command_used="python tools/capture_recurrence_trajectory_baseline.py",
        generated_at=generated_at,
    )
    history = __import__("json").loads(Path(history_json_path).read_text(encoding="utf-8"))
    summary = history.get("recurrence_trajectory_summary") or {}
    return {
        "history_json_path": str(history_json_path),
        "trajectory_history_path": str(trajectory_history_path),
        "snapshot_count": int(summary.get("snapshot_count") or 0),
        "trajectory_available": bool(summary.get("trajectory_available")),
        "baseline_snapshot": summary.get("baseline_snapshot") or {},
        "current_snapshot": summary.get("current_snapshot") or {},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generated-at",
        default="2026-06-20T12:00:00Z",
        help="Timestamp recorded on the captured snapshot.",
    )
    args = parser.parse_args(argv)
    result = capture_recurrence_trajectory_baseline(generated_at=args.generated_at)
    print(
        "Recurrence trajectory baseline captured: "
        f"snapshot_count={result['snapshot_count']}, "
        f"trajectory_available={result['trajectory_available']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
