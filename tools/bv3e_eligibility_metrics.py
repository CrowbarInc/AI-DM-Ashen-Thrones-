#!/usr/bin/env python3
"""BV3E — eligibility expansion metrics (baseline vs post-expansion)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.final_emission_referential_clarity import (  # noqa: E402
    _violations_eligible_for_non_strict_local_pronoun_repair,
    _violations_eligible_for_non_strict_local_repair,
)
from tools.bv3a_referential_clarity_metrics import build_metrics as build_bv3a_metrics  # noqa: E402
from tools.bv3d_eligibility_report import build_report as build_eligibility_report  # noqa: E402
from tools.bv3d_measurement_scope import scan_measurement_fem_turns  # noqa: E402

METRICS_PATH = ROOT / "artifacts" / "bv3e_eligibility_metrics.json"
BASELINE_PATH = ROOT / "artifacts" / "bv3d_eligibility_report.json"
SIMULATION_PATH = ROOT / "artifacts" / "bv3e_shape_simulation.json"


def _violations_from_fem(fem: dict) -> list[dict]:
    sample = fem.get("referential_clarity_violation_sample") or []
    return [v for v in sample if isinstance(v, dict)]


def build_metrics() -> dict:
    baseline_report = {}
    if BASELINE_PATH.is_file():
        baseline_report = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    simulation = {}
    if SIMULATION_PATH.is_file():
        simulation = json.loads(SIMULATION_PATH.read_text(encoding="utf-8"))
    sim_summary = simulation.get("summary") or {}

    turns, _count, _hits = scan_measurement_fem_turns()
    observe = [t for t in turns if t.get("route_kind") == "observe"]
    bv3a_metrics = build_bv3a_metrics()
    eligibility = build_eligibility_report()

    bv3a_eligible = 0
    bv3e_eligible = 0
    newly_eligible = 0
    bv3e_applied = 0
    bv3e_repair_success = 0

    for turn in observe:
        fem = turn["meta"]["final_emission_meta"]
        violations = _violations_from_fem(fem)
        session = turn.get("session") if isinstance(turn.get("session"), dict) else None
        scene = turn.get("scene") if isinstance(turn.get("scene"), dict) else None
        world = turn.get("world") if isinstance(turn.get("world"), dict) else None
        a_ok = _violations_eligible_for_non_strict_local_pronoun_repair(violations)
        e_ok = _violations_eligible_for_non_strict_local_repair(
            violations, session=session, scene=scene, world=world
        )
        if a_ok:
            bv3a_eligible += 1
        if e_ok:
            bv3e_eligible += 1
        if e_ok and not a_ok:
            newly_eligible += 1
        if fem.get("referential_clarity_bv3e_repair_mode"):
            bv3e_applied += 1
        if fem.get("referential_clarity_upstream_repair_applied") is True and fem.get(
            "referential_clarity_bv3e_repair_mode"
        ):
            bv3e_repair_success += 1

    baseline_summary = baseline_report.get("summary") or {}
    current_summary = eligibility.get("summary") or {}

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "measurement_scope": "BV3D filtered (see docs/audits/BV3D_measurement_scope.md)",
        "baseline_bv3d": {
            "eligible_observe_turn_count": baseline_summary.get("contract_eligible_shape_count"),
            "upstream_repair_eligible_count": baseline_summary.get("upstream_repair_eligible_count"),
            "upstream_repair_applied_count": baseline_summary.get("upstream_repair_applied_count"),
            "referential_clarity_hard_replacement_count": (
                (bv3a_metrics.get("baseline") or {}).get("referential_clarity_hard_replacement_count")
            ),
            "observe_route_rate": (bv3a_metrics.get("baseline") or {}).get("observe_route_rate"),
            "source": "artifacts/bv3d_eligibility_report.json (pre-BV3E snapshot)",
        },
        "post_expansion": {
            "eligible_observe_turn_count": current_summary.get("contract_eligible_shape_count"),
            "bv3a_eligible_count": bv3a_eligible,
            "bv3e_eligible_count": bv3e_eligible,
            "newly_eligible_turn_count": newly_eligible,
            "simulated_bv3e_eligible_count": sim_summary.get("bv3e_eligible_count"),
            "simulated_newly_eligible_turn_count": sim_summary.get("newly_eligible_turn_count"),
            "simulated_upstream_applied_count": sim_summary.get("simulated_upstream_applied_count"),
            "upstream_repair_eligible_count": current_summary.get("upstream_repair_eligible_count"),
            "upstream_repair_applied_count": current_summary.get("upstream_repair_applied_count"),
            "bv3e_repair_applied_count": bv3e_applied,
            "bv3e_repair_success_count": bv3e_repair_success,
            "referential_clarity_hard_replacement_count": (
                (bv3a_metrics.get("current") or {}).get("referential_clarity_hard_replacement_count")
            ),
            "observe_route_rate": (bv3a_metrics.get("current") or {}).get("observe_route_rate"),
            "repair_success_rate_on_observe": (
                (bv3a_metrics.get("observe_instrumentation") or {}).get("repair_success_rate_on_observe")
            ),
            "simulation_source": str(SIMULATION_PATH.relative_to(ROOT)).replace("\\", "/"),
        },
        "delta": {
            "newly_eligible_turn_count_frozen_fem": newly_eligible,
            "newly_eligible_turn_count_simulated": sim_summary.get("newly_eligible_turn_count"),
            "simulated_hard_replacement_avoidance": sim_summary.get("simulated_upstream_applied_count"),
            "eligible_observe_turn_count_delta_frozen_fem": (
                (current_summary.get("upstream_repair_eligible_count") or 0)
                - (baseline_summary.get("upstream_repair_eligible_count") or 0)
            ),
            "referential_clarity_hard_replacement_delta_frozen_fem": bv3a_metrics.get("delta_vs_baseline", {}).get(
                "referential_clarity_hard_replacement_delta"
            ),
            "observe_route_rate_pp_frozen_fem": bv3a_metrics.get("delta_vs_baseline", {}).get("observe_route_rate_pp"),
            "projected_hard_replacement_delta_after_replay_refresh": (
                -int(sim_summary.get("simulated_upstream_applied_count") or 0)
                if sim_summary.get("simulated_upstream_applied_count") is not None
                else None
            ),
        },
    }


def main() -> int:
    metrics = build_metrics()
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
