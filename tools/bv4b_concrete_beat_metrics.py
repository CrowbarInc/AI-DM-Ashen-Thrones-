#!/usr/bin/env python3
"""BV4B — concrete beat satisfier and PSP incidence metrics."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.final_emission_replay_projection import project_sealed_replacement_subkind_from_fem  # noqa: E402
from tools.bv3a_referential_clarity_metrics import build_metrics as build_bv3a_metrics  # noqa: E402
from tools.bv3d_measurement_scope import scan_measurement_fem_turns  # noqa: E402
from tools.fallback_incidence_report import build_fallback_incidence_report  # noqa: E402

METRICS_PATH = ROOT / "artifacts" / "bv4b_concrete_beat_metrics.json"
BV3F_BASELINE_PATH = ROOT / "artifacts" / "bv3f_reduction_metrics.json"


def build_metrics() -> dict:
    bv3f = {}
    if BV3F_BASELINE_PATH.is_file():
        bv3f = json.loads(BV3F_BASELINE_PATH.read_text(encoding="utf-8"))

    turns, fem_count, _hits = scan_measurement_fem_turns()
    report = build_fallback_incidence_report(turns)
    bv3a = build_bv3a_metrics()

    observe_turns = [t for t in turns if t.get("route_kind") == "observe"]
    observe_fem = [t["meta"]["final_emission_meta"] for t in observe_turns]

    psp_events = 0
    for turn in turns:
        fem = turn["meta"]["final_emission_meta"]
        subkind = project_sealed_replacement_subkind_from_fem(fem)
        if subkind == "sealed_passive_scene_pressure_fallback":
            psp_events += 1
            continue
        for event in turn["meta"].get("runtime_lineage_events") or []:
            if (
                isinstance(event, dict)
                and event.get("event_kind") == "fallback_selected"
                and event.get("fallback_kind") == "sealed_passive_scene_pressure_fallback"
            ):
                psp_events += 1
                break

    satisfier_attempted = sum(
        1 for fem in observe_fem if fem.get("passive_scene_concrete_beat_satisfier_attempted") is True
    )
    satisfier_applied = sum(
        1 for fem in observe_fem if fem.get("passive_scene_concrete_beat_satisfier_applied") is True
    )
    fallback_avoided = sum(
        1 for fem in observe_fem if fem.get("passive_scene_pressure_fallback_avoided") is True
    )
    beat_types = dict(
        Counter(
            str(fem.get("passive_scene_concrete_beat_type"))
            for fem in observe_fem
            if fem.get("passive_scene_concrete_beat_satisfier_applied") is True
            and fem.get("passive_scene_concrete_beat_type")
        )
    )

    baseline_psp = (bv3f.get("actual_post_refresh") or {}).get("fallback_kind_counts", {}).get(
        "sealed_passive_scene_pressure_fallback", 10
    )
    baseline_observe = (bv3f.get("comparison_table") or {}).get("observe_route_rate", {}).get("actual", 0.4783)
    baseline_incidence = (bv3f.get("comparison_table") or {}).get("fallback_incidence", {}).get("actual", 0.1158)

    current_observe_rate = report["route_fallback_trigger_rate"].get("observe")
    current_incidence = report["fallback_trigger_rate"]
    current_psp = (bv3a.get("current") or {}).get("fallback_kind_counts", {}).get(
        "sealed_passive_scene_pressure_fallback", psp_events
    )

    rc_delta = current_psp - baseline_psp
    classification = "NO_MEASURABLE_CHANGE"
    if current_psp <= baseline_psp - 8 and satisfier_applied >= 8:
        classification = "EFFECTIVE_REDUCTION"
    elif current_psp < baseline_psp and satisfier_applied > 0:
        classification = "PARTIAL_REDUCTION"

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "phase": "BV4B",
        "measurement_scope": "BV3D filtered",
        "comparison_table": {
            "sealed_passive_scene_pressure_fallback_count": {
                "bv3f_baseline": baseline_psp,
                "current": current_psp,
                "delta": current_psp - baseline_psp if baseline_psp is not None else None,
            },
            "observe_route_rate": {
                "bv3f_baseline": baseline_observe,
                "current": current_observe_rate,
                "delta": (
                    round(current_observe_rate - baseline_observe, 4)
                    if current_observe_rate is not None and baseline_observe is not None
                    else None
                ),
            },
            "fallback_incidence": {
                "bv3f_baseline": baseline_incidence,
                "current": current_incidence,
                "delta": (
                    round(current_incidence - baseline_incidence, 4)
                    if baseline_incidence is not None
                    else None
                ),
            },
        },
        "satisfier_instrumentation": {
            "observe_turn_count": len(observe_turns),
            "satisfier_attempted_count": satisfier_attempted,
            "satisfier_applied_count": satisfier_applied,
            "fallback_avoided_count": fallback_avoided,
            "beat_type_counts": beat_types,
            "satisfier_success_rate_on_eligible": (
                round(satisfier_applied / satisfier_attempted, 4) if satisfier_attempted else None
            ),
        },
        "classification": classification,
        "baseline_source": str(BV3F_BASELINE_PATH.relative_to(ROOT)).replace("\\", "/"),
    }


def main() -> int:
    metrics = build_metrics()
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
