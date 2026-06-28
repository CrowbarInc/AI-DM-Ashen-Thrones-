#!/usr/bin/env python3
"""Regenerate protected replay recurrence history JSON and markdown artifacts.

Reporting-only. Reloads the committed protected and session-diagnostic event logs
without appending rows, then writes only:
  - artifacts/golden_replay/bug_recurrence_history.json
  - artifacts/golden_replay/bug_recurrence_history.md

Uses the canonical ``write_bug_recurrence_history_artifacts`` orchestration via a
temporary output path so supplementary governance markdown is not rewritten.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.failure_dashboard_paths import (  # noqa: E402
    BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_HISTORY_JSON_PATH,
    BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_SESSION_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_SYNTHETIC_TEST_ARTIFACT_EVENT_LOG_JSON_PATH,
)
from tests.helpers.failure_dashboard_recurrence import write_bug_recurrence_history_artifacts  # noqa: E402


def regenerate_bug_recurrence_history(
    *,
    history_json_path: Path | str = BUG_RECURRENCE_HISTORY_JSON_PATH,
    history_md_path: Path | str = BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    event_log_path: Path | str = BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    session_diagnostic_event_log_path: Path | str = BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH,
    session_event_log_path: Path | str = BUG_RECURRENCE_SESSION_EVENT_LOG_JSON_PATH,
    synthetic_test_artifact_event_log_path: Path | str = (
        BUG_RECURRENCE_SYNTHETIC_TEST_ARTIFACT_EVENT_LOG_JSON_PATH
    ),
    generated_at: str | None = None,
    command_used: str | None = None,
) -> tuple[Path, Path]:
    """Regenerate history artifacts without rewriting supplementary governance docs."""
    json_out = Path(history_json_path)
    markdown_out = Path(history_md_path)
    timestamp = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    command = command_used or "python tools/regenerate_bug_recurrence_history.py"

    write_bug_recurrence_history_artifacts(
        [],
        json_path=json_out,
        markdown_path=markdown_out,
        event_log_path=event_log_path,
        session_diagnostic_event_log_path=session_diagnostic_event_log_path,
        session_event_log_path=session_event_log_path,
        synthetic_test_artifact_event_log_path=synthetic_test_artifact_event_log_path,
        command_used=command,
        generated_at=timestamp,
        emit_governance_docs=False,
        emit_trajectory_history=False,
    )

    return json_out, markdown_out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generated-at",
        default=None,
        help="Optional ISO timestamp recorded in regenerated artifact headers.",
    )
    args = parser.parse_args(argv)
    json_out, markdown_out = regenerate_bug_recurrence_history(generated_at=args.generated_at)
    print(f"Regenerated {json_out.as_posix()}")
    print(f"Regenerated {markdown_out.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
