#!/usr/bin/env python3
"""BV3A — referential clarity repair instrumentation and incidence measurement."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.bv3d_measurement_scope import MEASUREMENT_ROOTS, scan_measurement_fem_turns  # noqa: E402
from tools.fallback_incidence_report import build_fallback_incidence_report  # noqa: E402

METRICS_PATH = ROOT / "artifacts" / "bv3a_referential_clarity_metrics.json"
BV1B_BASELINE_PATH = ROOT / "artifacts" / "golden_replay" / "bv1b_fallback_incidence_report.baseline.json"


def scan_canonical_fem_turns() -> list[dict]:
    turns, _count, _hits = scan_measurement_fem_turns()
    return turns


def _instrumentation_from_fem(fem: dict) -> dict[str, int | bool | None]:
    return {
        "upstream_repair_attempted": fem.get("referential_clarity_upstream_repair_attempted"),
        "upstream_repair_applied": fem.get("referential_clarity_upstream_repair_applied"),
        "upstream_repair_eligible": fem.get("referential_clarity_upstream_repair_eligible"),
        "local_substitution_applied": fem.get("referential_clarity_local_substitution_applied"),
        "replacement_applied": fem.get("referential_clarity_replacement_applied"),
        "unrepaired_violation_count": fem.get("referential_clarity_unrepaired_violation_count"),
    }


def build_metrics() -> dict:
    baseline = {}
    if BV1B_BASELINE_PATH.is_file():
        baseline = json.loads(BV1B_BASELINE_PATH.read_text(encoding="utf-8"))

    turns = scan_canonical_fem_turns()
    report = build_fallback_incidence_report(turns)

    observe_turns = [t for t in turns if t.get("route_kind") == "observe"]
    observe_fem = [t["meta"]["final_emission_meta"] for t in observe_turns]

    upstream_applied = sum(
        1 for fem in observe_fem if fem.get("referential_clarity_upstream_repair_applied") is True
    )
    local_applied = sum(
        1 for fem in observe_fem if fem.get("referential_clarity_local_substitution_applied") is True
    )
    ref_replaced = sum(1 for fem in observe_fem if fem.get("referential_clarity_replacement_applied") is True)
    ambiguous_turns = sum(
        1
        for fem in observe_fem
        if isinstance(fem.get("referential_clarity_violation_kinds"), list)
        and "ambiguous_entity_reference" in fem["referential_clarity_violation_kinds"]
    )

    lineage_kind = Counter(
        event.get("fallback_kind")
        for turn in turns
        for event in turn["meta"].get("runtime_lineage_events") or []
        if isinstance(event, dict) and event.get("event_kind") == "fallback_selected"
    )

    baseline_rate = baseline.get("fallback_trigger_rate")
    baseline_observe = (baseline.get("route_fallback_trigger_rate") or {}).get("observe")
    baseline_ref_kind = ((baseline.get("frequency") or {}).get("fallback_kind") or {}).get(
        "referential_clarity_hard_replacement"
    )

    current_ref_kind = lineage_kind.get("referential_clarity_hard_replacement", 0)

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "measurement_scope": {
            "policy": "BV3D",
            "roots": [str(p.relative_to(ROOT)).replace("\\", "/") for p in MEASUREMENT_ROOTS],
            "doc": "docs/audits/BV3D_measurement_scope.md",
        },
        "baseline": {
            "observe_route_rate": baseline_observe,
            "fallback_incidence": baseline_rate,
            "referential_clarity_hard_replacement_count": baseline_ref_kind,
            "source": str(BV1B_BASELINE_PATH.relative_to(ROOT)).replace("\\", "/"),
        },
        "current": {
            "eligible_turn_count": report["eligible_turn_count"],
            "fallback_trigger_rate": report["fallback_trigger_rate"],
            "observe_route_rate": report["route_fallback_trigger_rate"].get("observe"),
            "referential_clarity_hard_replacement_count": current_ref_kind,
            "fallback_kind_counts": dict(lineage_kind),
        },
        "delta_vs_baseline": {
            "observe_route_rate_pp": (
                None
                if baseline_observe is None
                else round((report["route_fallback_trigger_rate"].get("observe") or 0) - baseline_observe, 4)
            ),
            "fallback_incidence_pp": (
                None
                if baseline_rate is None
                else round(report["fallback_trigger_rate"] - baseline_rate, 4)
            ),
            "referential_clarity_hard_replacement_delta": (
                None if baseline_ref_kind is None else current_ref_kind - int(baseline_ref_kind)
            ),
        },
        "observe_instrumentation": {
            "observe_turn_count": len(observe_turns),
            "ambiguous_entity_reference_turns": ambiguous_turns,
            "upstream_repair_applied_count": upstream_applied,
            "local_substitution_applied_count": local_applied,
            "referential_clarity_replacement_applied_count": ref_replaced,
            "repair_success_rate_on_observe": (
                round(local_applied / ambiguous_turns, 4) if ambiguous_turns else None
            ),
            "unrepaired_violation_turns": sum(
                1
                for fem in observe_fem
                if int(fem.get("referential_clarity_unrepaired_violation_count") or 0) > 0
            ),
        },
        "projected_after_bv3a": {
            "description": "Synthetic gate simulation + corpus shape analysis; historical FEM frozen until replay refresh",
            "eligible_shape_turns_ambiguous_speaker": 35,
            "simulation": {
                "dialogue_he_with_interlocutor_avoids_fallback": True,
                "dialogue_he_multi_person_no_grounding_still_replaces": True,
            },
            "conservative_referential_clarity_hard_replacement_delta": "-8 to -15 events when observe turns carry social/interlocutor grounding",
            "conservative_observe_route_rate_target": "0.70-0.80",
            "conservative_fallback_incidence_target": "0.58-0.62",
            "replay_refresh_required": True,
        },
        "note": (
            "BV3D measurement scope: excludes pre-refresh archives, run_debug.json, nested debug FEM, "
            "and derived golden_replay reports. Includes bv3d_measurement positive-control fixtures."
        ),
    }


def main() -> None:
    metrics = build_metrics()
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
