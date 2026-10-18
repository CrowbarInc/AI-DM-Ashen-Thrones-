"""Run the PR-DL comparison. Live calls require --execute-live."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.pr_dl.budget import Budget  # noqa: E402
from experiments.pr_dl.runner import OUT, STAGE_1, IsolationStop, assemble, prepare_matrix, run_live, stage1_unusable  # noqa: E402


def _git(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return (completed.stdout or completed.stderr or "").strip()


def _provider_configuration() -> dict[str, object]:
    from game.config import (
        DEFAULT_MODEL_NAME,
        ENABLE_MODEL_ROUTING,
        HIGH_PRECISION_MODEL_NAME,
        MODEL_NAME,
        RETRY_ESCALATION_MODEL_NAME,
    )

    return {
        "DEFAULT_MODEL_NAME": DEFAULT_MODEL_NAME,
        "MODEL_NAME": MODEL_NAME,
        "HIGH_PRECISION_MODEL_NAME": HIGH_PRECISION_MODEL_NAME,
        "RETRY_ESCALATION_MODEL_NAME": RETRY_ESCALATION_MODEL_NAME,
        "ENABLE_MODEL_ROUTING": ENABLE_MODEL_ROUTING,
        "ASHEN_DISABLE_LIVE_INTERPRETATION": os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION"),
        "openai_api_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "temperature": 0,
        "max_output_tokens": 400,
        "endpoint": "responses.create",
        "planner_schema_reused": False,
        "planner_schema_reason": "PR-DH Candidate B schema includes proposed_resolver, advance_time, and expects_mutation.",
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute-live", action="store_true")
    parser.add_argument("--stage", choices=("1", "2", "all"), default="1")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    phase0 = {
        "head": _git(["rev-parse", "HEAD"]),
        "status_short": _git(["status", "--short"]),
        "provider_configuration": _provider_configuration(),
    }
    _write_json(OUT / "phase0_snapshot.json", phase0)
    try:
        prepared = prepare_matrix()
    except IsolationStop as exc:
        _write_json(OUT / "isolation_stop.json", {"stopped": str(exc), "phase0": phase0})
        print(f"STOP BEFORE LIVE CALLS: {exc}")
        return 2
    prepared_public = {
        "metrics": prepared["metrics"],
        "isolation": prepared["isolation"],
        "evidence": prepared["evidence"],
        "live_provider_calls_during_preparation": prepared["live_provider_calls_during_preparation"],
        "estimates": [
            {"scenario_id": row["scenario_id"], "estimated_input_tokens": row["estimated_input_tokens"]}
            for row in prepared["rows"]
        ],
    }
    _write_json(OUT / "preparation.json", prepared_public)
    (OUT / "PR-DL_evidence_corrections.md").write_text(
        __import__("experiments.pr_dl.evidence", fromlist=["render_evidence"]).render_evidence(prepared["evidence"]).rstrip() + "\n",
        encoding="utf-8",
    )
    estimate_sum = sum(row["estimated_input_tokens"] for row in prepared["rows"])
    print(f"preparation ok; conservative input estimate sum={estimate_sum}")
    print("matrix", json.dumps(prepared["metrics"]))
    if not args.execute_live:
        print("live calls not requested")
        return 0
    order = list(STAGE_1)
    if args.stage in {"2", "all"}:
        order.extend(row["scenario_id"] for row in prepared["rows"] if row["scenario_id"] not in STAGE_1)
    if args.stage == "2":
        order = [row["scenario_id"] for row in prepared["rows"] if row["scenario_id"] not in STAGE_1]
        checkpoint_path = OUT / "checkpoint.json"
        if not checkpoint_path.exists():
            print("STOP: stage 2 requires stage 1 checkpoint")
            return 2
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("stage1_all_unusable") or checkpoint.get("stopped"):
            print("STOP: stage 1 did not clear live continuation")
            return 2
        budget = Budget(
            requests=int(checkpoint["budget"]["requests"]),
            input_tokens=int(checkpoint["budget"]["input_tokens"]),
            output_tokens=int(checkpoint["budget"]["output_tokens"]),
            records=list(checkpoint["budget"]["records"]),
        )
        prior = checkpoint["results"]
    else:
        budget = Budget()
        prior = {}
        if args.stage == "1":
            order = list(STAGE_1)
    live = run_live(prepared, scenario_ids=order, budget=budget)
    results = {**prior, **live["results"]}
    checkpoint = {
        "results": results,
        "budget": {
            "requests": live["budget"].requests,
            "input_tokens": live["budget"].input_tokens,
            "output_tokens": live["budget"].output_tokens,
            "total_tokens": live["budget"].total_tokens,
            "records": live["budget"].records,
        },
        "stopped": live["stopped"],
        "stage1_all_unusable": stage1_unusable(results),
        "configured_model": live.get("configured_model") or phase0["provider_configuration"]["DEFAULT_MODEL_NAME"],
        "save_guard_verified": live["save_guard_verified"],
        "provider_tripwire_hits": live["provider_tripwire_hits"],
    }
    _write_json(OUT / "checkpoint.json", checkpoint)
    print(
        json.dumps(
            {
                "stopped": checkpoint["stopped"],
                "requests": checkpoint["budget"]["requests"],
                "input_tokens": checkpoint["budget"]["input_tokens"],
                "output_tokens": checkpoint["budget"]["output_tokens"],
                "stage1_all_unusable": checkpoint["stage1_all_unusable"],
                "scenarios": sorted(results),
            }
        )
    )
    if checkpoint["stopped"] or (args.stage == "1" and checkpoint["stage1_all_unusable"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
