"""Run the Ashen Thrones Gameplay Benchmark harness.

The default mode is provider-disabled and simulated. It checks the benchmark
machinery. It does not measure conversational performance, and it does not
call a model.

A future live checkpoint must pass --mode live-provider, an explicit call
ceiling, an explicit time ceiling, and --confirm-live-provider. This command
does not choose a dollar budget.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.atgb.budget import Budget, BudgetError
from tools.atgb.driver import MODES, LiveRunRefused, RunConfig, run_benchmark
from tools.atgb.fixtures import PARTITIONS, load_corpus


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="Print scenario ids, partitions, and turn counts.")
    parser.add_argument("--mode", choices=MODES, default="provider_disabled_simulated")
    parser.add_argument("--scenario", action="append", dest="scenarios", help="Scenario id to run. Repeatable.")
    parser.add_argument("--partition", action="append", dest="partitions", choices=PARTITIONS)
    parser.add_argument("--output", type=Path, help="Directory for result.json, report.md, and the worksheet.")
    parser.add_argument("--trial", type=int, default=1)
    parser.add_argument("--max-provider-calls", type=int)
    parser.add_argument("--max-tokens", type=int)
    parser.add_argument("--max-estimated-cost", type=float)
    parser.add_argument("--max-elapsed-seconds", type=float)
    parser.add_argument("--price-per-million-input-tokens", type=float)
    parser.add_argument("--price-per-million-output-tokens", type=float)
    parser.add_argument("--confirm-live-provider", action="store_true")
    parser.add_argument("--keep-stores", action="store_true")
    parser.add_argument("--preflight-only", action="store_true", help="Reset and inspect starting state with providers disabled; submit no chat turns.")
    parser.add_argument("--scores", type=Path, help="Optional human score JSON to merge. It does not create a gameplay claim by itself.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.preflight_only and args.mode != "provider_disabled_host":
        print("--preflight-only requires --mode provider_disabled_host", file=sys.stderr)
        return 2
    if args.list:
        loaded = load_corpus(ROOT)
        for scenario in loaded["scenarios"]:
            print(f"{scenario['scenario_id']}\t{scenario['partition']}\t{len(scenario['turns'])}\t{scenario['title']}")
        return 0
    scores = None
    if args.scores is not None:
        scores = json.loads(args.scores.read_text(encoding="utf-8"))
    config = RunConfig(
        mode=args.mode,
        output_dir=args.output,
        partitions=tuple(args.partitions) if args.partitions else None,
        scenario_ids=tuple(args.scenarios) if args.scenarios else None,
        trial_number=args.trial,
        confirm_live_provider=args.confirm_live_provider,
        keep_stores=args.keep_stores,
        preflight_only=args.preflight_only,
        budget=Budget(
            max_provider_calls=args.max_provider_calls,
            max_tokens=args.max_tokens,
            max_estimated_cost=args.max_estimated_cost,
            max_elapsed_seconds=args.max_elapsed_seconds,
            price_per_million_input_tokens=args.price_per_million_input_tokens,
            price_per_million_output_tokens=args.price_per_million_output_tokens,
        ),
        scores=scores,
    )
    try:
        result = run_benchmark(config, root=ROOT)
    except (BudgetError, LiveRunRefused, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(
        f"{result['evidence_distinction']} turns={len(result['turns'])} "
        f"gameplay_performance_claim={str(result['gameplay_performance_claim']).lower()}"
    )
    if result.get("stop_reason"):
        print(f"stopped: {result['stop_reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
