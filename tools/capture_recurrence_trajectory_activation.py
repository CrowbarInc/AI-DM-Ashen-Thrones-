#!/usr/bin/env python3
"""Capture protected replay recurrence trajectory snapshot #2 and run final graduation audit.

Reporting-only. Regenerates recurrence history artifacts, appends a temporal follow-up
snapshot when metrics are unchanged from baseline, activates trajectory analytics, and
writes the BQ-C4 final graduation decision report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.failure_dashboard_paths import (  # noqa: E402
    BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_HISTORY_JSON_PATH,
    BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH,
)
from tests.helpers.failure_dashboard_report import write_bug_recurrence_history_artifacts  # noqa: E402
from tests.helpers.replay_bug_recurrence_serialization import (  # noqa: E402
    RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH,
)


def capture_recurrence_trajectory_activation(
    *,
    event_log_path: Path | str = BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    history_json_path: Path | str = BUG_RECURRENCE_HISTORY_JSON_PATH,
    history_md_path: Path | str = BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    trajectory_history_path: Path | str = RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH,
    generated_at: str | None = None,
) -> dict[str, object]:
    """Regenerate recurrence history, capture snapshot #2, and run final graduation audit."""
    write_bug_recurrence_history_artifacts(
        [],
        json_path=history_json_path,
        markdown_path=history_md_path,
        event_log_path=event_log_path,
        command_used="python tools/capture_recurrence_trajectory_activation.py",
        generated_at=generated_at,
        temporal_trajectory_capture=True,
    )
    history = json.loads(Path(history_json_path).read_text(encoding="utf-8"))
    trajectory_summary = history.get("recurrence_trajectory_summary") or {}
    calibration = history.get("recurrence_confidence_calibration_summary") or {}
    decision = history.get("recurrence_final_graduation_decision") or {}
    return {
        "history_json_path": str(history_json_path),
        "trajectory_history_path": str(trajectory_history_path),
        "final_decision_path": str(RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH),
        "snapshot_count": int(trajectory_summary.get("snapshot_count") or 0),
        "trajectory_available": bool(trajectory_summary.get("trajectory_available")),
        "calibration_score": float(calibration.get("confidence_calibration_score") or 0.0),
        "largest_calibration_gap": float(calibration.get("largest_calibration_gap") or 0.0),
        "graduation_confidence_ready": bool(calibration.get("graduation_confidence_ready")),
        "final_recommendation": decision.get("final_recommendation"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generated-at",
        default="2026-06-20T20:00:00Z",
        help="Timestamp recorded on snapshot #2.",
    )
    args = parser.parse_args(argv)
    result = capture_recurrence_trajectory_activation(generated_at=args.generated_at)
    print(
        "Recurrence trajectory activation captured: "
        f"snapshot_count={result['snapshot_count']}, "
        f"trajectory_available={result['trajectory_available']}, "
        f"calibration_score={result['calibration_score']}, "
        f"final_recommendation={result['final_recommendation']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
