"""Replay stored PR-DL interpretations under the refined selective policy.

No provider client is constructed. The source JSON is read and left unchanged.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from experiments.pr_dl.policies import summarize_policy
from experiments.pr_dm.authority import evaluate_authority
from experiments.pr_dm.completeness import refined_checks, refined_route
from experiments.pr_dm.fallback import decide_consumption

ROOT = Path(__file__).resolve().parents[2]
STORED_RESULTS = ROOT / "artifacts" / "pr_dl_interpretation_comparison" / "raw_results.json"
BASELINE_FULL = {"A": 11, "B": 16, "C": 17}
ORDINARY = (
    "S1",
    "control_movement",
    "control_combat",
    "control_observation",
    "control_authored_fact",
    "control_followup",
    "var_compound_control",
    "var_pronoun_control",
    "var_negated_control",
)
RECOVERED_TARGETS = ("var_compound_subtle", "var_quote_control")


class ReplayStop(RuntimeError):
    """Raised when stored evidence cannot support an offline replay."""


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_stored(path: Path | None = None) -> dict[str, Any]:
    source = path or STORED_RESULTS
    if not source.is_file():
        raise ReplayStop(f"stored PR-DL results are missing: {source}")
    payload = json.loads(source.read_text(encoding="utf-8"))
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != 21:
        raise ReplayStop("stored results do not contain the original 21 scenarios")
    return payload


def _policy_row(row: Mapping[str, Any]) -> dict[str, Any]:
    scores = row.get("scores") if isinstance(row.get("scores"), Mapping) else {}
    adapter = row.get("live_adapter") if isinstance(row.get("live_adapter"), Mapping) else {}
    return {
        "scenario_id": row["scenario_id"],
        "B_requested": bool(row.get("B_requested")),
        "deterministic_gameplay": row.get("deterministic_gameplay"),
        "live_accepted": bool(adapter.get("accepted")),
        "live_gameplay": scores.get("gameplay_usefulness"),
        "live_authority": scores.get("authority_compliance"),
        "live_clarification_useful": scores.get("clarification_usefulness"),
        "live_asserted_outcome": scores.get("asserted_outcome"),
        "usage": row.get("usage") or {},
    }


def _assert_baseline(stored: Mapping[str, Any], recomputed: Mapping[str, Mapping[str, Any]]) -> None:
    published = stored.get("policies") if isinstance(stored.get("policies"), Mapping) else {}
    for policy, expected in BASELINE_FULL.items():
        fresh = recomputed[policy]
        if fresh["correct_count"] != expected:
            raise ReplayStop(f"recomputed policy {policy} handled {fresh['correct_count']}, baseline is {expected}")
        published_ids = list((published.get(policy) or {}).get("correctly_handled") or [])
        if published_ids != list(fresh["correctly_handled"]):
            raise ReplayStop(f"recomputed policy {policy} labels differ from the stored PR-DL labels")


def _usage(rows: list[Mapping[str, Any]], selector) -> dict[str, int]:
    chosen = [row for row in rows if selector(row) and row.get("usage")]
    return {
        "provider_requests": len(chosen),
        "actual_input_tokens": sum(int(row["usage"]["input_tokens"]) for row in chosen),
        "actual_output_tokens": sum(int(row["usage"]["output_tokens"]) for row in chosen),
        "actual_total_tokens": sum(int(row["usage"]["total_tokens"]) for row in chosen),
    }


def _working_row(row: Mapping[str, Any]) -> dict[str, Any]:
    scores = row.get("scores") if isinstance(row.get("scores"), Mapping) else {}
    adapter = row.get("live_adapter") if isinstance(row.get("live_adapter"), Mapping) else {}
    public = row.get("public_context") if isinstance(row.get("public_context"), Mapping) else {}
    return {
        "scenario_id": row["scenario_id"],
        "utterance": row.get("utterance") or "",
        "selected_resolver": row.get("selected_resolver"),
        "B_requested": bool(row.get("B_requested")),
        "deterministic_gameplay": row.get("deterministic_gameplay"),
        "independent_checks": dict(row.get("independent_checks") or {}),
        "existing_signals": dict(row.get("existing_signals") or {}),
        "live_payload": row.get("live_payload"),
        "live_adapter": adapter,
        "live_gameplay": scores.get("gameplay_usefulness"),
        "live_authority": scores.get("authority_compliance"),
        "public_context": public,
        "usage": row.get("usage") or {},
        "scores": dict(scores),
    }


def replay_stored(path: Path | None = None) -> dict[str, Any]:
    source = path or STORED_RESULTS
    digest_before = file_sha256(source)
    stored = load_stored(source)
    if file_sha256(source) != digest_before:
        raise ReplayStop("reading stored results changed the file")
    policy_rows = [_policy_row(row) for row in stored["rows"]]
    policies = {name: summarize_policy(policy_rows, name) for name in ("A", "B", "C")}
    _assert_baseline(stored, policies)

    evaluated: list[dict[str, Any]] = []
    for source_row in stored["rows"]:
        row = _working_row(source_row)
        public = row["public_context"]
        guard = evaluate_authority(
            row["live_payload"] if isinstance(row["live_payload"], Mapping) else None,
            permitted_entities=public.get("permitted_entities"),
            visible_context=public.get("visible_context"),
        )
        checks = refined_checks(
            str(row["utterance"]),
            str(row["selected_resolver"] or ""),
            independent=row["independent_checks"],
        )
        routed = bool(row["B_requested"] or refined_route(checks))
        decision = decide_consumption(row, guard, routed=routed)
        offered = decide_consumption(row, guard, routed=True)
        evaluated.append(
            {
                **{key: row[key] for key in ("scenario_id", "utterance", "selected_resolver", "B_requested", "deterministic_gameplay", "live_gameplay", "usage")},
                "live_accepted": bool(row["live_adapter"].get("accepted")),
                "new_checks": checks,
                "refined_routed": routed,
                "guard": guard,
                "decision": decision,
                "if_offered": offered,
            }
        )

    by_id = {row["scenario_id"]: row for row in evaluated}
    full = [row["scenario_id"] for row in evaluated if row["decision"]["selected_gameplay"] == "PASS"]
    partial = [row["scenario_id"] for row in evaluated if row["decision"]["selected_gameplay"] == "PARTIAL"]
    recovered = [
        sid
        for sid in RECOVERED_TARGETS
        if by_id[sid]["refined_routed"] and by_id[sid]["decision"]["interpretation_usefulness"] == "successful_interpretation"
    ]
    new_escalations = [
        row["scenario_id"]
        for row in evaluated
        if row["refined_routed"] and not row["B_requested"] and row["deterministic_gameplay"] == "PASS"
    ]
    ordinary_degraded = [
        sid
        for sid in ORDINARY
        if by_id[sid]["decision"]["selected_gameplay"] != "PASS"
    ]
    committed = [
        row["scenario_id"]
        for row in evaluated
        if row["decision"]["consumed_ai"] and not row["guard"]["accepted"]
    ]
    executed = [row["scenario_id"] for row in evaluated if row["decision"]["executed"] or row["decision"]["mutated_state"]]
    suppressed = [
        row["scenario_id"]
        for row in evaluated
        if row["deterministic_gameplay"] == "PASS" and row["decision"]["selected_gameplay"] != "PASS"
    ]
    usage_d = _usage(evaluated, lambda row: row["refined_routed"])
    return {
        "source": str(source),
        "source_sha256": digest_before,
        "live_provider_calls": 0,
        "provider_models": list(stored.get("provider_models") or []),
        "baseline": {name: policies[name]["correct_count"] for name in ("A", "B", "C")},
        "policies": policies,
        "stored_usage": stored.get("usage"),
        "rows": evaluated,
        "refined": {
            "fully_handled": full,
            "partially_handled": partial,
            "full_count": len(full),
            "partial_count": len(partial),
            "recovered_misses": recovered,
            "new_false_escalations": new_escalations,
            "ordinary_degraded": ordinary_degraded,
            "committed_authority_violations": committed,
            "executed_or_mutated": executed,
            "suppressed_valid_deterministic": suppressed,
            "rejected": [row["scenario_id"] for row in evaluated if row["refined_routed"] and not row["decision"]["consumed_ai"]],
            "clarifications": [row["scenario_id"] for row in evaluated if row["decision"]["clarification"]],
            "unsupported": [row["scenario_id"] for row in evaluated if row["decision"]["unsupported"]],
            "abstentions": [row["scenario_id"] for row in evaluated if row["decision"]["abstained"]],
            "fallbacks": [row["scenario_id"] for row in evaluated if row["decision"]["disposition"] == "preserve_deterministic"],
            "consumed": [row["scenario_id"] for row in evaluated if row["decision"]["consumed_ai"]],
            "missed": [
                row["scenario_id"]
                for row in evaluated
                if row["decision"]["interpretation_usefulness"] == "missed_complication"
            ],
        },
        "usage": {
            "A": _usage(evaluated, lambda row: False),
            "B": _usage(evaluated, lambda row: row["B_requested"]),
            "C": _usage(evaluated, lambda row: True),
            "D": usage_d,
        },
    }
