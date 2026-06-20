#!/usr/bin/env python3
"""Expand protected replay recurrence observations from the curated corpus.

Reporting-only. Appends deduped protected replay failure events and regenerates
recurrence history artifacts until observation volume targets are met.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.failure_dashboard_report import (  # noqa: E402
    BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_HISTORY_JSON_PATH,
    BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
)
from tests.helpers.protected_replay_observation_corpus import (  # noqa: E402
    PROTECTED_REPLAY_OBSERVATION_CORPUS_REPORT_PATH,
    PROTECTED_REPLAY_OBSERVATION_EXPANSION_COMMAND,
    PROTECTED_REPLAY_OBSERVATION_EXPANSION_GENERATED_AT,
    render_protected_replay_observation_corpus_report,
)
from tests.helpers.replay_bug_recurrence import (  # noqa: E402
    RECURRENCE_MATURITY_MIN_KEYS,
    RECURRENCE_MATURITY_MIN_OBSERVATIONS,
    aggregate_protected_recurrence_history_from_event_log,
    load_recurrence_event_log,
)

from tools.backfill_bug_recurrence_history import backfill_bug_recurrence_history  # noqa: E402


def _confidence_metrics(history: dict[str, Any]) -> dict[str, float]:
    forecast = history.get("recurrence_forecast") or {}
    forecast_summary = forecast.get("forecast_summary") if isinstance(forecast, dict) else {}
    governance_summary = history.get("recurrence_governance_summary") or {}
    program_summary = history.get("recurrence_program_effectiveness_summary") or {}
    maturity_summary = history.get("recurrence_maturity_summary") or {}
    return {
        "forecast_confidence": float((forecast_summary or {}).get("forecast_confidence") or 0.0),
        "governance_confidence": float(governance_summary.get("governance_confidence") or 0.0),
        "effectiveness_confidence": float(program_summary.get("effectiveness_confidence") or 0.0),
        "operational_readiness_score": float(maturity_summary.get("operational_readiness_score") or 0.0),
    }


def _volume_status(*, total_observations: int, total_keys: int) -> dict[str, Any]:
    observations_met = total_observations >= RECURRENCE_MATURITY_MIN_OBSERVATIONS
    keys_met = total_keys >= RECURRENCE_MATURITY_MIN_KEYS
    return {
        "total_observations": total_observations,
        "total_keys": total_keys,
        "observations_target_met": observations_met,
        "keys_target_met": keys_met,
        "data_volume_target_met": observations_met and keys_met,
        "observations_target": RECURRENCE_MATURITY_MIN_OBSERVATIONS,
        "keys_target": RECURRENCE_MATURITY_MIN_KEYS,
    }


def ensure_observation_corpus_report(
    *,
    report_path: Path | str = PROTECTED_REPLAY_OBSERVATION_CORPUS_REPORT_PATH,
    command: str = PROTECTED_REPLAY_OBSERVATION_EXPANSION_COMMAND,
    generated_at: str = PROTECTED_REPLAY_OBSERVATION_EXPANSION_GENERATED_AT,
) -> Path:
    """Write the curated observation corpus report when absent or when forced."""
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_protected_replay_observation_corpus_report(command=command, generated_at=generated_at),
        encoding="utf-8",
    )
    return path


def expand_protected_replay_observations(
    *,
    corpus_report_path: Path | str = PROTECTED_REPLAY_OBSERVATION_CORPUS_REPORT_PATH,
    event_log_path: Path | str = BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    history_json_path: Path | str = BUG_RECURRENCE_HISTORY_JSON_PATH,
    history_md_path: Path | str = BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    refresh_corpus: bool = False,
    dry_run: bool = False,
    check: bool = False,
) -> dict[str, Any]:
    """Append curated protected replay observations and regenerate history artifacts."""
    report_path = Path(corpus_report_path)
    if refresh_corpus or not report_path.is_file():
        ensure_observation_corpus_report(report_path=report_path)

    backfill_result = backfill_bug_recurrence_history(
        failure_report_path=report_path,
        event_log_path=event_log_path,
        history_json_path=history_json_path,
        history_md_path=history_md_path,
        dry_run=dry_run,
        check=check,
    )

    if dry_run or check:
        return backfill_result

    protected_log = load_recurrence_event_log(event_log_path)
    history = aggregate_protected_recurrence_history_from_event_log(protected_log)
    if history_json_path:
        persisted = json.loads(Path(history_json_path).read_text(encoding="utf-8"))
    else:
        persisted = history

    portfolio_summary = persisted.get("recurrence_portfolio_summary")
    if not isinstance(portfolio_summary, dict):
        portfolio_summary = {}
    total_observations = int(
        portfolio_summary.get("total_observations")
        or persisted.get("total_rows")
        or len(protected_log.get("events") or [])
    )
    total_keys = int(persisted.get("unique_recurrence_count") or history.get("unique_recurrence_count") or 0)
    volume = _volume_status(total_observations=total_observations, total_keys=total_keys)
    confidence = _confidence_metrics(persisted)

    return {
        **backfill_result,
        **volume,
        **confidence,
        "unique_recurrence_count": total_keys,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus-report",
        type=Path,
        default=Path(PROTECTED_REPLAY_OBSERVATION_CORPUS_REPORT_PATH),
        help="Curated protected replay observation corpus markdown path.",
    )
    parser.add_argument(
        "--event-log",
        type=Path,
        default=BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
        help="Bug recurrence append-only event log path.",
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
        "--refresh-corpus",
        action="store_true",
        help="Regenerate the curated corpus report before backfill.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print append plan without writing artifacts.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if parseable corpus rows are missing from the event log.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = expand_protected_replay_observations(
            corpus_report_path=args.corpus_report,
            event_log_path=args.event_log,
            history_json_path=args.history_json,
            history_md_path=args.history_md,
            refresh_corpus=args.refresh_corpus,
            dry_run=args.dry_run,
            check=args.check,
        )
    except SystemExit:
        return 1

    if args.dry_run:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.check:
        print("Protected replay observation expansion check passed.")
        return 0

    print(
        "Protected replay observation expansion complete: "
        f"{result.get('total_observations')} observations, "
        f"{result.get('unique_recurrence_count')} keys, "
        f"forecast_confidence={result.get('forecast_confidence')}, "
        f"governance_confidence={result.get('governance_confidence')}, "
        f"effectiveness_confidence={result.get('effectiveness_confidence')}, "
        f"operational_readiness_score={result.get('operational_readiness_score')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
