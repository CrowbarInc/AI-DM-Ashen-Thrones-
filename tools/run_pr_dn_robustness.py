"""Run PR-DN bounded live interpretation robustness experiment."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.pr_dn.runner import (  # noqa: E402
    OUT,
    STAGE_1,
    Budget,
    BudgetStop,
    _git,
    _save_fingerprints,
    choose_decision,
    prepare,
    provider_configuration,
    run_live,
    run_regressions,
    stage1_unusable,
    write_artifacts,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--stage", choices=("1", "2", "all"), default="all")
    parser.add_argument("--skip-regressions", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    phase0 = {
        "head": _git(["rev-parse", "HEAD"]),
        "status_short": _git(["status", "--short"]),
        "provider_configuration": provider_configuration(),
        "production_save_fingerprints_before": _save_fingerprints(),
    }
    _write_json(OUT / "phase0_snapshot.json", phase0)
    prepared = prepare()
    _write_json(OUT / "preparation.json", {k: v for k, v in prepared.items() if k != "rows"})
    live: dict = {"results": {}, "budget": Budget(), "stopped": None}
    if args.execute_live:
        order = list(STAGE_1)
        if args.stage in {"2", "all"}:
            order.extend(row["scenario_id"] for row in prepared["rows"] if row["scenario_id"] not in STAGE_1)
        if args.stage == "2":
            order = [row["scenario_id"] for row in prepared["rows"] if row["scenario_id"] not in STAGE_1]
        try:
            live = run_live(prepared, order)
        except BudgetStop as exc:
            live["stopped"] = str(exc)
            print(f"STOP: {exc}")
        if args.stage == "1" and stage1_unusable(live.get("results", {})):
            live["stopped"] = "stage 1 had three or more unusable outputs"
    else:
        print("Preparation complete; live calls not requested.")
    phase0["production_save_fingerprints_after"] = _save_fingerprints()
    regression = "Regressions not run."
    if not args.skip_regressions:
        regression = run_regressions()
    budget = {
        "requests": getattr(live.get("budget"), "requests", 0),
        "input_tokens": getattr(live.get("budget"), "input_tokens", 0),
        "output_tokens": getattr(live.get("budget"), "output_tokens", 0),
        "total_tokens": getattr(live.get("budget"), "total_tokens", 0),
    }
    rows = []
    from experiments.pr_dn.runner import assemble

    rows = assemble(prepared, live)
    decision = choose_decision(rows, {**budget, "records": getattr(live.get("budget"), "records", [])}, live.get("stopped"))
    write_artifacts(prepared, live, phase0, regression, decision)
    print(json.dumps({"decision": decision, "requests": budget["requests"], "input_tokens": budget["input_tokens"], "output_tokens": budget["output_tokens"], "total_tokens": budget["total_tokens"], "out": str(OUT), "zip": str(ROOT / "handoff" / "CURRENT_REVIEW.zip")}, indent=2))
    return 2 if live.get("stopped") else 0


if __name__ == "__main__":
    raise SystemExit(main())

