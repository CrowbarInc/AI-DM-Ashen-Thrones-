#!/usr/bin/env python3
"""Manual synthetic-session CLI for exploratory harness runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.synthetic_profiles import (  # noqa: E402
    default_placeholder_profile,
    profile_adversarial_rules_poker,
    profile_arcane_examiner,
    profile_bold_opportunist,
    profile_cautious_investigator,
    profile_social_prober,
)
from tests.helpers.synthetic_runner import run_synthetic_session  # noqa: E402
from tests.helpers.synthetic_scoring import summarize_synthetic_run  # noqa: E402
from tests.helpers.synthetic_types import SyntheticProfile, SyntheticRunResult  # noqa: E402

ProfileFactory = Callable[[], SyntheticProfile]

PROFILE_FACTORIES: dict[str, ProfileFactory] = {
    "placeholder": default_placeholder_profile,
    "cautious_investigator": profile_cautious_investigator,
    "social_prober": profile_social_prober,
    "arcane_examiner": profile_arcane_examiner,
    "bold_opportunist": profile_bold_opportunist,
    "adversarial_rules_poker": profile_adversarial_rules_poker,
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a manual synthetic harness session (fake-GM by default).",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_FACTORIES.keys()),
        default="placeholder",
        help="Synthetic profile id.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Deterministic seed for synthetic policy decisions.",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=5,
        help="Maximum turns to run before stop conditions.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--fake-gm",
        action="store_true",
        help="Use deterministic fake GM responder (default behavior).",
    )
    mode.add_argument(
        "--real-gm",
        action="store_true",
        help="Opt into real transcript/game GM path.",
    )
    return parser


def _compact_line(text: object) -> str:
    value = str(text or "").strip()
    return " ".join(value.split()) or "-"


def _extract_player_facing(turn_view: dict[str, object]) -> str:
    snapshot = turn_view.get("raw_snapshot")
    if isinstance(snapshot, dict):
        response = snapshot.get("response")
        if isinstance(response, dict):
            return _compact_line(response.get("player_facing_text"))
    return _compact_line(turn_view.get("gm_text"))


def _print_result(result: SyntheticRunResult) -> None:
    print(f"profile_name: {result.profile_name}")
    print(f"seed: {result.seed}")
    print(f"stop_reason: {result.stop_reason}")
    print("")

    for idx, turn_view in enumerate(result.turn_views, start=1):
        player_text = _compact_line(turn_view.get("player_text"))
        rationale = _compact_line(turn_view.get("decision_rationale"))
        gm_text = _compact_line(turn_view.get("gm_text"))
        player_facing = _extract_player_facing(turn_view)
        print(f"[turn {idx}] player: {player_text}")
        print(f"          rationale: {rationale}")
        print(f"          gm: {gm_text}")
        print(f"          player_facing: {player_facing}")

    summary = summarize_synthetic_run(result)
    print("")
    print("run_summary:")
    print(json.dumps(summary, indent=2, sort_keys=True))


def main() -> int:
    args = _build_parser().parse_args()
    profile = PROFILE_FACTORIES[args.profile]()
    use_fake_gm = not args.real_gm
    if args.fake_gm:
        use_fake_gm = True

    result = run_synthetic_session(
        profile=profile,
        seed=args.seed,
        max_turns=args.max_turns,
        use_fake_gm=use_fake_gm,
    )
    _print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
