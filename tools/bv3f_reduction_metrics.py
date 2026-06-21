#!/usr/bin/env python3
"""BV3F — aggregate reduction metrics: BV3D baseline vs BV3E projection vs post-refresh actual."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

METRICS_PATH = ROOT / "artifacts" / "bv3f_reduction_metrics.json"
PRE_REFRESH_DIR = ROOT / "artifacts" / "bv3f_replay_refresh"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _run_metrics_tools() -> None:
    for script in (
        "bv3a_referential_clarity_metrics.py",
        "bv3d_eligibility_report.py",
        "bv1b_fallback_incidence_validation.py",
        "bv3e_eligibility_metrics.py",
        "bv3e_shape_simulation.py",
    ):
        subprocess.run([sys.executable, str(ROOT / "tools" / script)], cwd=ROOT, check=True)


def _delta(actual: float | int | None, projected: float | int | None) -> float | int | None:
    if actual is None or projected is None:
        return None
    return actual - projected


def build_metrics(*, run_tools: bool = True) -> dict:
    if run_tools:
        _run_metrics_tools()

    pre_bv3d = _load_json(PRE_REFRESH_DIR / "pre_refresh.bv3d_eligibility_report.json")
    pre_bv3e = _load_json(PRE_REFRESH_DIR / "pre_refresh.bv3e_eligibility_metrics.json")
    if not pre_bv3d:
        pre_bv3d = _load_json(ROOT / "artifacts" / "bv3d_eligibility_report.json")

    bv3a = _load_json(ROOT / "artifacts" / "bv3a_referential_clarity_metrics.json")
    bv3d = _load_json(ROOT / "artifacts" / "bv3d_eligibility_report.json")
    bv3e = _load_json(ROOT / "artifacts" / "bv3e_eligibility_metrics.json")
    bv1b = _load_json(ROOT / "artifacts" / "golden_replay" / "bv1b_fallback_incidence_report.json")

    bv3d_summary = (pre_bv3d or bv3d).get("summary") or {}
    bv3d_eligible = bv3d_summary.get("upstream_repair_eligible_count") or bv3d_summary.get("contract_eligible_shape_count")
    bv3d_applied = bv3d_summary.get("upstream_repair_applied_count")

    pre_bv3a = _load_json(PRE_REFRESH_DIR / "pre_refresh.bv3a_referential_clarity_metrics.json")
    bv3d_rc = (
        (pre_bv3a.get("current") or {}).get("referential_clarity_hard_replacement_count")
        if pre_bv3a
        else (bv3a.get("current") or {}).get("referential_clarity_hard_replacement_count")
    )
    bv3d_observe_rate = (
        (pre_bv3a.get("current") or {}).get("observe_route_rate")
        if pre_bv3a
        else (bv3a.get("current") or {}).get("observe_route_rate")
    )
    bv3d_fallback = (
        (pre_bv3a.get("current") or {}).get("fallback_trigger_rate")
        if pre_bv3a
        else (bv3a.get("current") or {}).get("fallback_trigger_rate")
    )

    sim_path = PRE_REFRESH_DIR / "pre_refresh.bv3e_shape_simulation.json"
    if not sim_path.is_file():
        sim_path = ROOT / "artifacts" / "bv3e_shape_simulation.json"
    sim = _load_json(sim_path).get("summary") or {}
    proj_eligible = (bv3d_eligible or 0) + int(sim.get("newly_eligible_turn_count") or 0)
    proj_applied = int(sim.get("simulated_upstream_applied_count") or 0) + int(bv3d_applied or 0)
    proj_rc = (bv3d_rc or 0) - int(sim.get("simulated_upstream_applied_count") or 0)
    proj_observe_rate = None
    if bv3d_observe_rate is not None and sim.get("simulated_upstream_applied_count"):
        observe_turns = (bv3d.get("summary") or {}).get("observe_turn_count") or 23
        avoided = int(sim.get("simulated_upstream_applied_count") or 0)
        proj_observe_rate = round(bv3d_observe_rate - (avoided / observe_turns if observe_turns else 0), 4)

    current_summary = (bv3d.get("summary") or {})
    current_bv3a = bv3a.get("current") or {}
    observe_instr = bv3a.get("observe_instrumentation") or {}
    post_bv3e = (bv3e.get("post_expansion") or {})

    actual_eligible = post_bv3e.get("bv3e_eligible_count") or current_summary.get("upstream_repair_eligible_count")
    actual_applied = post_bv3e.get("bv3e_repair_applied_count") or current_summary.get("upstream_repair_applied_count")
    actual_rc = current_bv3a.get("referential_clarity_hard_replacement_count")
    actual_observe_rate = current_bv3a.get("observe_route_rate")
    actual_fallback = current_bv3a.get("fallback_trigger_rate") or bv1b.get("fallback_trigger_rate")

    repair_success = post_bv3e.get("repair_success_rate_on_observe")
    if post_bv3e.get("bv3e_repair_applied_count"):
        applied = int(post_bv3e.get("bv3e_repair_applied_count") or 0)
        success = int(post_bv3e.get("bv3e_repair_success_count") or 0)
        repair_success = round(success / applied, 4) if applied else repair_success

    rows = {
        "eligible_turns": {
            "bv3d": bv3d_eligible,
            "bv3e_projection": proj_eligible,
            "actual": actual_eligible,
            "delta_actual_vs_projection": _delta(actual_eligible, proj_eligible),
        },
        "repairs_applied": {
            "bv3d": bv3d_applied,
            "bv3e_projection": proj_applied,
            "actual": actual_applied,
            "delta_actual_vs_projection": _delta(actual_applied, proj_applied),
        },
        "repair_success_rate": {
            "bv3d": (pre_bv3e.get("post_expansion") or {}).get("repair_success_rate_on_observe") or 0.0909,
            "bv3e_projection": 1.0,
            "actual": repair_success,
            "delta_actual_vs_projection": _delta(repair_success, 1.0),
        },
        "referential_clarity_hard_replacements": {
            "bv3d": bv3d_rc,
            "bv3e_projection": proj_rc,
            "actual": actual_rc,
            "delta_actual_vs_projection": _delta(actual_rc, proj_rc),
        },
        "observe_route_rate": {
            "bv3d": bv3d_observe_rate,
            "bv3e_projection": proj_observe_rate,
            "actual": actual_observe_rate,
            "delta_actual_vs_projection": _delta(actual_observe_rate, proj_observe_rate),
        },
        "fallback_incidence": {
            "bv3d": bv3d_fallback,
            "bv3e_projection": None,
            "actual": actual_fallback,
            "delta_actual_vs_projection": None,
        },
    }

    rc_delta_actual = _delta(actual_rc, bv3d_rc)
    rc_delta_proj = proj_rc - (bv3d_rc or 0) if proj_rc is not None and bv3d_rc is not None else None

    fallback_kinds = current_bv3a.get("fallback_kind_counts") or {}
    scene_opening = fallback_kinds.get("scene_opening")

    classification = "NO_MEASURABLE_CHANGE"
    if (
        rc_delta_actual is not None
        and rc_delta_actual <= -8
        and actual_applied is not None
        and proj_applied is not None
        and actual_applied >= (proj_applied * 0.8)
    ):
        classification = "EFFECTIVE_REDUCTION"
    elif rc_delta_actual is not None and rc_delta_actual < 0 and (actual_applied or 0) > (bv3d_applied or 0):
        classification = "PARTIAL_REDUCTION"

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "phase": "BV3F",
        "measurement_scope": "BV3D filtered + post-BV3F replay refresh",
        "comparison_table": rows,
        "bv3d_frozen_baseline": {
            "eligible_turns": bv3d_eligible,
            "repairs_applied": bv3d_applied,
            "referential_clarity_hard_replacements": bv3d_rc,
            "observe_route_rate": bv3d_observe_rate,
            "fallback_incidence": bv3d_fallback,
        },
        "bv3e_projection": {
            "eligible_turns": proj_eligible,
            "repairs_applied": proj_applied,
            "referential_clarity_hard_replacements": proj_rc,
            "observe_route_rate": proj_observe_rate,
            "hard_replacement_delta": rc_delta_proj,
            "source": str(sim_path.relative_to(ROOT)).replace("\\", "/"),
        },
        "actual_post_refresh": {
            "eligible_turns": actual_eligible,
            "repairs_applied": actual_applied,
            "bv3e_repair_applied_count": post_bv3e.get("bv3e_repair_applied_count"),
            "referential_clarity_hard_replacements": actual_rc,
            "observe_route_rate": actual_observe_rate,
            "fallback_incidence": actual_fallback,
            "fallback_kind_counts": fallback_kinds,
            "scene_opening_fallback_count": scene_opening,
        },
        "reduction_signals": {
            "referential_clarity_delta_vs_bv3d": rc_delta_actual,
            "repairs_applied_delta_vs_bv3d": _delta(actual_applied, bv3d_applied),
            "eligible_turns_delta_vs_bv3d": _delta(actual_eligible, bv3d_eligible),
            "projection_convergence_rc": _delta(actual_rc, proj_rc),
            "projection_convergence_repairs": _delta(actual_applied, proj_applied),
        },
        "classification": classification,
        "sources": {
            "bv3a": "artifacts/bv3a_referential_clarity_metrics.json",
            "bv3d": "artifacts/bv3d_eligibility_report.json",
            "bv3e": "artifacts/bv3e_eligibility_metrics.json",
            "bv1b": "artifacts/golden_replay/bv1b_fallback_incidence_report.json",
            "pre_refresh": str(PRE_REFRESH_DIR.relative_to(ROOT)).replace("\\", "/"),
        },
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-run", action="store_true", help="Use existing metric artifacts only.")
    args = parser.parse_args()

    metrics = build_metrics(run_tools=not args.skip_run)
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
