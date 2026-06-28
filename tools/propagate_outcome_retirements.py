#!/usr/bin/env python3
"""CO104/CO105 — Propagate audit-backed outcome retirements into protected recurrence history.

Reporting-only. Applies documented engineering retirements from the consolidated retirement
registry to the protected event log, then regenerates recurrence history artifacts.
Does not dedupe or remove observation rows — preserves chronology and replay evidence.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.failure_dashboard_paths import (  # noqa: E402
    BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_HISTORY_JSON_PATH,
    BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
)
from tests.helpers.failure_dashboard_report import write_bug_recurrence_history_artifacts  # noqa: E402
from tests.helpers.replay_bug_recurrence import (  # noqa: E402
    load_recurrence_event_log,
    write_recurrence_event_log,
)
from tools.bv8a_recurrence_history_regeneration import (  # noqa: E402
    PROJECTION_RECURRENCE_KEY,
    RETIREMENT_REGISTRY as BV8A_RETIREMENT_REGISTRY,
)

VOCATIVE_TEST_NODE = (
    "tests/test_golden_replay_structural_invariants.py::"
    "test_golden_replay_vocative_override_after_prior_continuity_structural_invariants"
)

EMISSION_DRIFT_RECURRENCE_KEY = (
    "recurrence:v1:emission_drift|projection|response_type_candidate_ok|tests/helpers/golden_replay.py"
)

BX_SPEAKER_PARITY_EVIDENCE_COMMAND = [sys.executable, "-m", "pytest", "-m", "bx_speaker_parity", "-q", "--tb=short"]

DOCUMENTED_RETIREMENT_REGISTRY: tuple[dict[str, str], ...] = (
    *tuple(entry for entry in BV8A_RETIREMENT_REGISTRY if entry.get("registry_status") == "RETIRED"),
    {
        "recurrence_key": EMISSION_DRIFT_RECURRENCE_KEY,
        "registry_status": "RETIRED",
        "rationale": (
            "Historical BX development response_type_candidate_ok projection mismatches on "
            "bx5 guard-matrix scenarios; BX program closed; all bx_speaker_parity tests pass; "
            "no reproduction since 2026-06-22."
        ),
        "evidence_registry_doc": "docs/audits/BX_emission_retirement_registry.md",
        "evidence_doc": "docs/audits/BX_emission_retirement_evidence.md",
    },
)

EVIDENCE_GATES: dict[str, tuple[str, ...]] = {
    PROJECTION_RECURRENCE_KEY: (VOCATIVE_TEST_NODE,),
    EMISSION_DRIFT_RECURRENCE_KEY: ("pytest -m bx_speaker_parity",),
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _events_for_key(events: list[dict[str, Any]], recurrence_key: str) -> list[dict[str, Any]]:
    return [event for event in events if str(event.get("recurrence_key") or "") == recurrence_key]


def _is_retired(event: Mapping[str, Any]) -> bool:
    return str(event.get("recurrence_status") or "").lower() in {"retired", "deprecated"}


def _run_pytest_node(test_node: str) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_node, "-q", "--tb=short"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _run_bx_speaker_parity_gate() -> bool:
    result = subprocess.run(
        BX_SPEAKER_PARITY_EVIDENCE_COMMAND,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _run_evidence_gate(recurrence_key: str) -> tuple[bool, str | None]:
    if recurrence_key == PROJECTION_RECURRENCE_KEY:
        return _run_pytest_node(VOCATIVE_TEST_NODE), VOCATIVE_TEST_NODE
    if recurrence_key == EMISSION_DRIFT_RECURRENCE_KEY:
        return _run_bx_speaker_parity_gate(), "pytest -m bx_speaker_parity"
    gate = EVIDENCE_GATES.get(recurrence_key)
    if not gate:
        return True, None
    passed = _run_pytest_node(gate[0])
    return passed, gate[0]


def _build_projection_retirement_evidence(
    event: Mapping[str, Any],
    *,
    generated_at: str,
    vocative_test_passed: bool,
) -> dict[str, Any]:
    return {
        "scenario_id": "vocative_override_after_prior_continuity",
        "test_node_id": event.get("test_node_id") or VOCATIVE_TEST_NODE,
        "vocative_test_passed": vocative_test_passed,
        "validated_at": generated_at,
        "failure_no_longer_reproduces": vocative_test_passed,
        "source_artifact": "artifacts/golden_replay/replay_failure_report.md",
    }


def apply_documented_retirements(
    events: list[dict[str, Any]],
    *,
    generated_at: str,
    keys_to_retire: frozenset[str],
    gate_results: Mapping[str, bool],
) -> list[dict[str, Any]]:
    """Mark documented recurrence keys retired while preserving observation rows."""
    retired: list[dict[str, Any]] = []
    vocative_passed = bool(gate_results.get(PROJECTION_RECURRENCE_KEY))
    for event in events:
        updated = dict(event)
        key = str(event.get("recurrence_key") or "")
        if key in keys_to_retire:
            updated["recurrence_status"] = "retired"
        if key == PROJECTION_RECURRENCE_KEY and key in keys_to_retire:
            updated["bv8a_registry_status"] = "RETIRED"
            updated["bv8a_retirement_evidence"] = _build_projection_retirement_evidence(
                event,
                generated_at=generated_at,
                vocative_test_passed=vocative_passed,
            )
        elif "bv8a_registry_status" not in updated and key != PROJECTION_RECURRENCE_KEY:
            updated.setdefault("bv8a_registry_status", "ACTIVE")
        retired.append(updated)
    return retired


def propagate_outcome_retirements(
    *,
    event_log_path: Path | str = BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    history_json_path: Path | str = BUG_RECURRENCE_HISTORY_JSON_PATH,
    history_md_path: Path | str = BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    generated_at: str | None = None,
    dry_run: bool = False,
    check: bool = False,
    skip_history_regeneration: bool = False,
) -> dict[str, Any]:
    """Apply documented retirements to the protected event log and regenerate history."""
    timestamp = generated_at or _utc_now_iso()
    event_log = load_recurrence_event_log(event_log_path)
    events = [dict(event) for event in event_log.get("events") or [] if isinstance(event, Mapping)]

    candidate_results: list[dict[str, Any]] = []
    pending_keys: list[str] = []
    blocked_keys: list[str] = []
    gate_results: dict[str, bool] = {}

    for candidate in DOCUMENTED_RETIREMENT_REGISTRY:
        recurrence_key = str(candidate.get("recurrence_key") or "")
        key_events = _events_for_key(events, recurrence_key)
        already_retired = bool(key_events) and all(_is_retired(event) for event in key_events)
        gate_passed, gate_test = _run_evidence_gate(recurrence_key)
        gate_results[recurrence_key] = gate_passed
        result = {
            "recurrence_key": recurrence_key,
            "registry_status": candidate.get("registry_status"),
            "rationale": candidate.get("rationale"),
            "event_count": len(key_events),
            "already_retired": already_retired,
            "evidence_gate_passed": gate_passed,
            "evidence_gate_test_node": gate_test,
            "evidence_doc": candidate.get("evidence_doc") or candidate.get("evidence_registry_doc"),
        }
        candidate_results.append(result)
        if not key_events:
            continue
        if already_retired:
            continue
        if not gate_passed:
            blocked_keys.append(recurrence_key)
            continue
        pending_keys.append(recurrence_key)

    keys_to_retire = frozenset(
        str(candidate.get("recurrence_key") or "")
        for candidate in DOCUMENTED_RETIREMENT_REGISTRY
        if candidate.get("registry_status") == "RETIRED"
        and gate_results.get(str(candidate.get("recurrence_key") or ""), False)
        and _events_for_key(events, str(candidate.get("recurrence_key") or ""))
    )
    updated_events = apply_documented_retirements(
        events,
        generated_at=timestamp,
        keys_to_retire=keys_to_retire,
        gate_results=gate_results,
    )
    mutated_event_count = sum(
        1
        for before, after in zip(events, updated_events, strict=True)
        if before.get("recurrence_status") != after.get("recurrence_status")
        or before.get("bv8a_retirement_evidence") != after.get("bv8a_retirement_evidence")
    )

    result: dict[str, Any] = {
        "generated_at": timestamp,
        "documented_retirement_candidates": candidate_results,
        "pending_retirement_keys": pending_keys,
        "blocked_retirement_keys": blocked_keys,
        "propagated_retirement_keys": sorted(keys_to_retire),
        "mutated_event_count": mutated_event_count,
        "dry_run": dry_run,
        "check": check,
    }

    if check:
        result["check_passed"] = not pending_keys and not blocked_keys
        if pending_keys:
            raise SystemExit(
                "Retirement propagation check failed: "
                f"{len(pending_keys)} documented retirement key(s) not yet propagated "
                f"({', '.join(pending_keys)})"
            )
        if blocked_keys:
            raise SystemExit(
                "Retirement propagation check failed: evidence gate blocked "
                f"{', '.join(blocked_keys)}"
            )
        return result

    if dry_run:
        would_mutate = sum(
            1
            for event in events
            if str(event.get("recurrence_key") or "") in keys_to_retire and not _is_retired(event)
        )
        result["would_mutate_event_count"] = would_mutate
        return result

    if mutated_event_count:
        updated_log = dict(event_log)
        updated_log["events"] = updated_events
        write_recurrence_event_log(event_log_path, updated_log)

    if not skip_history_regeneration:
        write_bug_recurrence_history_artifacts(
            [],
            json_path=history_json_path,
            markdown_path=history_md_path,
            event_log_path=event_log_path,
            command_used="python tools/propagate_outcome_retirements.py",
            generated_at=timestamp,
        )

    history = json.loads(Path(history_json_path).read_text(encoding="utf-8"))
    outcome_summary = history.get("outcome_validation_summary") or {}
    calibration = history.get("recurrence_confidence_calibration_summary") or {}
    result.update(
        {
            "event_log_count": len(updated_events),
            "validated_outcome_count": int(outcome_summary.get("validated_outcome_count") or 0),
            "retired_keys": int(outcome_summary.get("retired_keys") or 0),
            "active_keys": int(outcome_summary.get("active_keys") or 0),
            "governance_health_score": float(
                (history.get("recurrence_governance") or {}).get("governance_health_score") or 0.0
            ),
            "calibration_score": float(calibration.get("confidence_calibration_score") or 0.0),
            "largest_calibration_gap": float(calibration.get("largest_calibration_gap") or 0.0),
            "graduation_confidence_ready": bool(calibration.get("graduation_confidence_ready")),
            "final_recommendation": (history.get("recurrence_final_graduation_decision") or {}).get(
                "final_recommendation"
            ),
        }
    )
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--event-log",
        type=Path,
        default=BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
        help="Protected recurrence event log path.",
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
        "--generated-at",
        default=None,
        help="Timestamp recorded on retirement evidence (ISO8601).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned retirements without writing artifacts.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if documented retirements are not yet propagated.",
    )
    parser.add_argument(
        "--skip-history-regeneration",
        action="store_true",
        help="Update the event log only; do not regenerate history artifacts.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = propagate_outcome_retirements(
            event_log_path=args.event_log,
            history_json_path=args.history_json,
            history_md_path=args.history_md,
            generated_at=args.generated_at,
            dry_run=args.dry_run,
            check=args.check,
            skip_history_regeneration=args.skip_history_regeneration,
        )
    except (OSError, UnicodeError, ValueError, FileNotFoundError) as exc:
        print(f"Outcome retirement propagation failed: {exc}", file=sys.stderr)
        return 2

    if args.check:
        print("Retirement propagation check passed.")
        return 0

    if args.dry_run:
        print(f"Documented candidates: {len(result['documented_retirement_candidates'])}")
        print(f"Would mutate events: {result.get('would_mutate_event_count', 0)}")
        for candidate in result["documented_retirement_candidates"]:
            print(
                f"  - {candidate['recurrence_key']}: events={candidate['event_count']}, "
                f"already_retired={candidate['already_retired']}, gate={candidate['evidence_gate_passed']}"
            )
        return 0

    print(
        "Outcome retirement propagation complete: "
        f"mutated_events={result['mutated_event_count']}, "
        f"retired_keys={result.get('retired_keys', 0)}, "
        f"validated_outcome_count={result.get('validated_outcome_count', 0)}, "
        f"calibration_score={result.get('calibration_score', 0.0)}, "
        f"graduation_confidence_ready={result.get('graduation_confidence_ready', False)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
