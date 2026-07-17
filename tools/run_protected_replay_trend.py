#!/usr/bin/env python3
"""Run protected replay trend windows and emit Golden Transcript Drift artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.golden_replay_trend import (  # noqa: E402
    BZ_REPLAY_KEY_MOVEMENT_FILENAME,
    GUARDRAIL_STATUS_WARN,
    load_guardrail_thresholds,
    protected_replay_corpus_scenario_ids,
    run_protected_replay_trend_window,
)
from tests.helpers.protected_replay_trend_movement import (  # noqa: E402
    BZ_RECURRENCE_MOVEMENT_FILENAME,
)

DEFAULT_OUT_DIR = ROOT / "artifacts" / "golden_replay" / "trend_window"
DEFAULT_BW_BASELINE_DIR = ROOT / "artifacts" / "golden_replay" / "trend_window"
DEFAULT_RECURRENCE_HISTORY = ROOT / "artifacts" / "golden_replay" / "bug_recurrence_history.json"
DEFAULT_RECURRENCE_EVENT_LOG = ROOT / "artifacts" / "golden_replay" / "bug_recurrence_event_log.json"
BZ_TREND_WINDOW_DIRNAME = "trend_window_2"


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
        "--compact",
        action="store_true",
        help="Emit compact_golden_drift_summary.json for the six protected replay cases.",
    )
    parser.add_argument(
        "--thresholds",
        type=Path,
        default=None,
        help="Optional JSON file overriding report-only guardrail thresholds.",
    )
    parser.add_argument(
        "--bz-replay-key-baseline-run",
        type=Path,
        default=None,
        help=(
            "Optional baseline run envelope for BZ replay-key movement "
            f"(default for {BZ_TREND_WINDOW_DIRNAME}: "
            f"{DEFAULT_BW_BASELINE_DIR / 'runs' / 'run-000.json'})."
        ),
    )
    parser.add_argument(
        "--bz-recurrence-baseline",
        type=Path,
        default=None,
        help=(
            "Optional explicit recurrence history snapshot for BZ recurrence movement. "
            "When omitted for trend_window_2, baseline_establishment mode is used."
        ),
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

    out_dir = args.out_dir.resolve()
    bz_baseline_run = args.bz_replay_key_baseline_run
    bz_corpus_baseline_ids: list[str] | None = None
    write_bz_recurrence = out_dir.name == BZ_TREND_WINDOW_DIRNAME
    bz_recurrence_baseline = args.bz_recurrence_baseline.resolve() if args.bz_recurrence_baseline else None
    bz_recurrence_current = DEFAULT_RECURRENCE_HISTORY if write_bz_recurrence else None
    bz_recurrence_event_log = DEFAULT_RECURRENCE_EVENT_LOG if write_bz_recurrence else None
    if bz_baseline_run is None and out_dir.name == BZ_TREND_WINDOW_DIRNAME:
        bz_baseline_run = DEFAULT_BW_BASELINE_DIR / "runs" / "run-000.json"
        bw_manifest = DEFAULT_BW_BASELINE_DIR / "manifest.json"
        if bw_manifest.is_file():
            try:
                manifest_payload = json.loads(bw_manifest.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                manifest_payload = {}
            corpus_ids = manifest_payload.get("corpus_scenario_ids")
            if isinstance(corpus_ids, list):
                bz_corpus_baseline_ids = [str(item) for item in corpus_ids]
        if bz_corpus_baseline_ids is None:
            bz_corpus_baseline_ids = list(protected_replay_corpus_scenario_ids())

    report = run_protected_replay_trend_window(
        runs=args.runs,
        out_dir=out_dir,
        compact=args.compact,
        append_history=args.append_history,
        thresholds=thresholds,
        bz_replay_key_baseline_run=bz_baseline_run.resolve() if bz_baseline_run else None,
        bz_corpus_baseline_scenario_ids=bz_corpus_baseline_ids,
        bz_recurrence_baseline=bz_recurrence_baseline,
        bz_recurrence_current=bz_recurrence_current,
        bz_recurrence_event_log=bz_recurrence_event_log,
        write_bz_recurrence_movement=write_bz_recurrence,
    )
    guardrail = report.get("guardrail") if isinstance(report.get("guardrail"), dict) else {}
    message = (
        f"Wrote protected replay trend artifacts to {out_dir} "
        f"(golden_transcript_drift_count={report.get('golden_transcript_drift_count')}, "
        f"guardrail={guardrail.get('status')})"
    )
    if args.append_history:
        message += " and appended golden_transcript_drift_history"
    if args.compact:
        message += "; wrote compact_golden_drift_summary.json"
    if bz_baseline_run is not None:
        bz_report = report.get("bz_replay_key_movement")
        if isinstance(bz_report, Mapping):
            summary = bz_report.get("summary")
            if isinstance(summary, Mapping):
                message += (
                    f"; wrote {BZ_REPLAY_KEY_MOVEMENT_FILENAME} "
                    f"(new={summary.get('new_key_count')}, "
                    f"retired={summary.get('retired_key_count')}, "
                    f"unchanged={summary.get('unchanged_key_count')})"
                )
            else:
                message += f"; wrote {BZ_REPLAY_KEY_MOVEMENT_FILENAME}"
        else:
            message += f"; wrote {BZ_REPLAY_KEY_MOVEMENT_FILENAME}"
    if write_bz_recurrence:
        bz_recurrence_report = report.get("bz_recurrence_movement")
        if isinstance(bz_recurrence_report, Mapping):
            message += (
                f"; wrote {BZ_RECURRENCE_MOVEMENT_FILENAME} "
                f"(mode={bz_recurrence_report.get('comparison_mode')})"
            )
        else:
            message += f"; wrote {BZ_RECURRENCE_MOVEMENT_FILENAME}"
    print(message)
    if guardrail.get("status") == GUARDRAIL_STATUS_WARN:
        print("Guardrail WARN (report-only; exit code remains 0).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
