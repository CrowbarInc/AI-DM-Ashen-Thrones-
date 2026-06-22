#!/usr/bin/env python3
"""Run protected replay trend windows and emit Golden Transcript Drift artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.golden_replay_trend import (  # noqa: E402
    GUARDRAIL_STATUS_WARN,
    load_guardrail_thresholds,
    run_protected_replay_trend_window,
)

DEFAULT_OUT_DIR = ROOT / "artifacts" / "golden_replay" / "trend_window"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, required=True, help="Number of isolated replay runs.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"Artifact output directory (default: {DEFAULT_OUT_DIR})",
    )
    parser.add_argument(
        "--append-history",
        action="store_true",
        help="Append the latest window aggregate to golden_transcript_drift_history.jsonl.",
    )
    parser.add_argument(
        "--thresholds",
        type=Path,
        default=None,
        help="Optional JSON file overriding report-only guardrail thresholds.",
    )
    args = parser.parse_args(argv)

    if args.runs < 1:
        print("--runs must be >= 1", file=sys.stderr)
        return 2

    try:
        thresholds = load_guardrail_thresholds(args.thresholds) if args.thresholds else None
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    report = run_protected_replay_trend_window(
        runs=args.runs,
        out_dir=args.out_dir.resolve(),
        append_history=args.append_history,
        thresholds=thresholds,
    )
    guardrail = report.get("guardrail") if isinstance(report.get("guardrail"), dict) else {}
    message = (
        f"Wrote protected replay trend artifacts to {args.out_dir.resolve()} "
        f"(golden_transcript_drift_count={report.get('golden_transcript_drift_count')}, "
        f"guardrail={guardrail.get('status')})"
    )
    if args.append_history:
        message += " and appended golden_transcript_drift_history"
    print(message)
    if guardrail.get("status") == GUARDRAIL_STATUS_WARN:
        print("Guardrail WARN (report-only; exit code remains 0).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
