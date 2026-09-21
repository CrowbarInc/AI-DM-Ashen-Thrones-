"""Build read-only evidence for the RC-11 and RC-13 investigation."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import pytest

from game.final_emission_opening_fallback import reassert_scene_opening_accepted_candidate
from game.observability_attribution_read import FINAL_EMISSION_META_KEY
from tests.helpers.golden_replay import (
    evaluate_golden_replay_continuity_drift,
    frontier_gate_branch_replay_fixture,
    run_golden_replay,
    summarize_long_session_replay_observations,
)
from tests.helpers.golden_replay_fixtures import (
    gm_response,
    golden_replay_chat_stubs,
    seed_frontier_gate_world,
)
from tests.helpers.golden_replay_profiles import FRONTIER_GATE_DIRECT_INTRUSION_LINEAGE_PROFILE


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts" / "unresolved_root_cause_investigation"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_rc11_trace() -> dict[str, Any]:
    accepted = "Rain on the gate. Guards watch the choke."
    initial = {
        "player_facing_text": "You stand at the gate.",
        "metadata": {"emission_debug": {}},
        FINAL_EMISSION_META_KEY: {},
    }
    current = copy.deepcopy(initial)
    reassert_scene_opening_accepted_candidate(
        current,
        accepted_scene_opening_text=accepted,
        source="test.reassert_scene_opening_accepted_candidate",
    )
    legacy_contract = copy.deepcopy(current)
    legacy_contract[FINAL_EMISSION_META_KEY].pop("semantic_mutation_write_sites", None)
    differing_paths = [f"{FINAL_EMISSION_META_KEY}.semantic_mutation_write_sites"]
    return {
        "case_id": "RC-11",
        "accepted_candidate": accepted,
        "initial": initial,
        "legacy_inline_result": legacy_contract,
        "current_helper_result": current,
        "player_facing_text_equal": legacy_contract["player_facing_text"] == current["player_facing_text"],
        "candidate_preview_equal": legacy_contract[FINAL_EMISSION_META_KEY]["response_type_candidate_preview"]
        == current[FINAL_EMISSION_META_KEY]["response_type_candidate_preview"],
        "emitted_preview_equal": legacy_contract[FINAL_EMISSION_META_KEY]["response_type_emitted_preview"]
        == current[FINAL_EMISSION_META_KEY]["response_type_emitted_preview"],
        "differing_paths": differing_paths,
        "first_meaningful_divergence": {
            "stage": "accepted-candidate reassertion attribution",
            "path": differing_paths[0],
            "legacy": "absent",
            "current": "one diagnostic_only write-site row",
        },
    }


def _compact_event(event: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "event_kind", "stage", "owner", "mutation_kind", "fallback_kind",
        "gate_path", "repair_kind", "recurrence_key",
    )
    return {key: event[key] for key in keys if event.get(key) is not None}


def build_rc13_trace(tmp_path: Path) -> dict[str, Any]:
    fixture = frontier_gate_branch_replay_fixture("branch_direct_intrusion")
    monkeypatch = pytest.MonkeyPatch()
    call_count = 0

    def fake_call_gpt(_messages: Any) -> dict[str, Any]:
        nonlocal call_count
        call_count += 1
        return gm_response(
            "The direct intrusion stays anchored: the gate serjeant, roster board, cordon pressure, "
            "warehouse latch, muddy crates, and watch whistles remain in view. "
            f"The risky push advances the same forced-access thread at deterministic call {call_count}."
        )

    try:
        golden_replay_chat_stubs(monkeypatch, gpt_callback=fake_call_gpt)
        result = run_golden_replay(
            scenario_id="frontier_gate_direct_intrusion_25_turn_diagnostic",
            turns=fixture["player_prompts"],
            tmp_path=tmp_path,
            monkeypatch=monkeypatch,
            setup_fn=seed_frontier_gate_world,
            starting_scene_id="frontier_gate",
            source_path=fixture["source_path"],
            branch_id=fixture["branch_id"],
            turn_ids=fixture["turn_ids"],
        )
        turns = result["turns"]
        summary = summarize_long_session_replay_observations(turns)
        continuity = evaluate_golden_replay_continuity_drift(
            spine=fixture["spine"], branch_id=fixture["branch_id"], turns=turns,
            turn_ids=fixture["turn_ids"],
        )["evaluation"]
    finally:
        monkeypatch.undo()

    mutation_limit = FRONTIER_GATE_DIRECT_INTRUSION_LINEAGE_PROFILE["event_kind_max"]["mutation"]
    cumulative = Counter()
    compact_turns = []
    first_unprofiled = None
    first_over_limit = None
    modeled = set(FRONTIER_GATE_DIRECT_INTRUSION_LINEAGE_PROFILE["mutation_kind_max"])
    for turn in turns:
        events = [_compact_event(row) for row in turn.get("runtime_lineage_events", []) if isinstance(row, Mapping)]
        mutation_kinds = [row["mutation_kind"] for row in events if row.get("event_kind") == "mutation" and row.get("mutation_kind")]
        cumulative.update(mutation_kinds)
        unprofiled = sorted(set(mutation_kinds) - modeled)
        mutation_total = sum(cumulative.values())
        row = {
            "turn_index": turn.get("turn_index"), "turn_id": turn.get("turn_id"),
            "route_kind": turn.get("route_kind"), "selected_speaker_id": turn.get("selected_speaker_id"),
            "fallback_family": turn.get("fallback_family"), "events": events,
            "mutation_kinds": mutation_kinds, "cumulative_mutation_count": mutation_total,
            "cumulative_mutation_kinds": dict(sorted(cumulative.items())),
        }
        compact_turns.append(row)
        if unprofiled and first_unprofiled is None:
            first_unprofiled = {"turn_index": turn.get("turn_index"), "turn_id": turn.get("turn_id"), "mutation_kinds": unprofiled}
        if mutation_total > mutation_limit and first_over_limit is None:
            first_over_limit = {"turn_index": turn.get("turn_index"), "turn_id": turn.get("turn_id"), "count": mutation_total}

    lineage = summary["lineage_summary"]
    return {
        "case_id": "RC-13", "scenario_id": result["scenario_id"], "turn_count": len(turns),
        "profile_mutation_limit": mutation_limit,
        "observed_event_kind_frequency": lineage["by_event_kind"],
        "observed_mutation_kind_frequency": lineage["mutation_kind_frequency"],
        "first_unprofiled_mutation": first_unprofiled,
        "first_aggregate_limit_exceedance": first_over_limit,
        "session_health": continuity.get("session_health"),
        "degradation": continuity.get("degradation_over_time"),
        "continuity_axes": continuity.get("axes"),
        "summary": {
            key: summary.get(key) for key in (
                "turn_count", "route_change_count", "speaker_change_count", "speaker_missing_count",
                "fallback_turn_count", "fallback_owner_change_count", "mutation_turn_count",
            )
        },
        "turns": compact_turns,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tmp-dir", type=Path, default=ROOT / "codex_rc13_trace_tmp")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.tmp_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.output_dir / "rc11_trace.json", build_rc11_trace())
    _write_json(args.output_dir / "rc13_turn_trace.json", build_rc13_trace(args.tmp_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
