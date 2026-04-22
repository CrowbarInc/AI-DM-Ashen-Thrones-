"""Unit tests for N1 scenario-spine contracts and harness (test-only infrastructure)."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from tests.helpers.n1_scenario_spine_contract import (
    N1BranchDefinition,
    N1BranchPointDefinition,
    N1DeterministicRunConfig,
    N1PerTurnContinuityObservation,
    N1RevisitExpectation,
    N1SessionHealthSummary,
)
from tests.helpers.n1_scenario_spine_harness import (
    build_n1_scenario_spine_definition,
    collect_n1_per_turn_continuity_observations,
    compare_n1_branch_session_health_summaries,
    compute_n1_session_health_summary,
    deterministic_json_dumps,
    dump_n1_scenario_spine_to_json,
    emit_n1_session_health_artifact_dict,
    execute_n1_spine_branch_with_shared_prefix,
    load_n1_scenario_spine_from_json,
    n1_scenario_spine_to_jsonable,
    stable_n1_run_id,
)
from tests.helpers.n1_scenarios import n1_registered_scenarios, validate_n1_registered_scenario_bundle
from tests.helpers.synthetic_profiles import default_placeholder_profile
from tests.helpers.synthetic_types import SyntheticDecision, SyntheticProfile, SyntheticRunResult


def _minimal_run_result(*, turn_views: tuple[dict, ...]) -> SyntheticRunResult:
    profile = SyntheticProfile(profile_id="unit")
    decisions = tuple(SyntheticDecision(player_text=str(v.get("player_text") or "")) for v in turn_views)
    return SyntheticRunResult(
        profiles=(profile,),
        decisions=decisions,
        snapshots=tuple({} for _ in turn_views),
        ok=True,
        profile_name="unit",
        seed=0,
        stop_reason="max_turns_reached",
        turn_views=turn_views,
    )


def test_stable_n1_run_id_is_deterministic_and_order_independent_in_payload() -> None:
    cfg = N1DeterministicRunConfig(
        seed=7,
        use_fake_gm=True,
        max_turns=3,
        profile_id="p",
        extra_scene_ids=("b", "a"),
    )
    rid = stable_n1_run_id(
        scenario_spine_id="spine_x",
        branch_id="branch_a",
        deterministic_config=cfg,
        player_texts=("hello", "world"),
    )
    rid_again = stable_n1_run_id(
        scenario_spine_id="spine_x",
        branch_id="branch_a",
        deterministic_config=cfg,
        player_texts=("hello", "world"),
    )
    assert rid == rid_again
    # extra_scene_ids normalized to sorted list inside fingerprint dict — stable across tuple order
    cfg_perm = N1DeterministicRunConfig(
        seed=7,
        use_fake_gm=True,
        max_turns=3,
        profile_id="p",
        extra_scene_ids=("a", "b"),
    )
    assert rid == stable_n1_run_id(
        scenario_spine_id="spine_x",
        branch_id="branch_a",
        deterministic_config=cfg_perm,
        player_texts=("hello", "world"),
    )


def test_emit_n1_session_health_reason_codes_sorted_and_json_stable() -> None:
    spine = build_n1_scenario_spine_definition(
        scenario_spine_id="s",
        narrative_anchor_ids=("zeta", "alpha"),
    )
    branch = N1BranchDefinition(branch_id="b1", branch_point_id="bp")
    cfg = N1DeterministicRunConfig(seed=1, use_fake_gm=True, max_turns=1, profile_id="p")
    views = (
        {
            "turn_index": 0,
            "player_text": "x",
            "gm_text": "alpha and zeta mentioned here",
            "scene_id": None,
            "raw_snapshot": {},
        },
    )
    run = _minimal_run_result(turn_views=views)
    summary = compute_n1_session_health_summary(
        spine=spine,
        branch=branch,
        run_result=run,
        deterministic_config=cfg,
    )
    codes = list(summary.reason_codes)
    assert codes == sorted(codes)
    art = emit_n1_session_health_artifact_dict(summary)
    dumped_a = deterministic_json_dumps(art)
    dumped_b = deterministic_json_dumps(art)
    assert dumped_a == dumped_b
    parsed = json.loads(dumped_a)
    assert parsed["reason_codes"] == sorted(parsed["reason_codes"])


def test_progression_chain_ordering_and_reason_codes() -> None:
    spine = build_n1_scenario_spine_definition(
        scenario_spine_id="spine_prog",
        progression_chain_step_ids=("step_b", "step_a"),
    )
    branch = N1BranchDefinition(branch_id="main", branch_point_id="bp")
    cfg = N1DeterministicRunConfig(seed=0, use_fake_gm=True, max_turns=2, profile_id="p")
    views = (
        {"turn_index": 0, "player_text": "p0", "gm_text": "step_a appears first", "raw_snapshot": {}},
        {"turn_index": 1, "player_text": "p1", "gm_text": "step_b appears after", "raw_snapshot": {}},
    )
    run = _minimal_run_result(turn_views=views)
    summary = compute_n1_session_health_summary(spine=spine, branch=branch, run_result=run, deterministic_config=cfg)
    assert summary.progression_chain_integrity_ok is False
    assert "N1_PROGRESSION_CHAIN_BROKEN" in summary.reason_codes


def test_forgotten_anchor_flag() -> None:
    spine = build_n1_scenario_spine_definition(scenario_spine_id="s", narrative_anchor_ids=("ledger",))
    branch = N1BranchDefinition(branch_id="b", branch_point_id="bp")
    cfg = N1DeterministicRunConfig(seed=0, use_fake_gm=True, max_turns=4, profile_id="p")
    views = []
    for i in range(4):
        gm = "ledger clue" if i == 0 else "no anchor here"
        views.append({"turn_index": i, "player_text": f"t{i}", "gm_text": gm, "raw_snapshot": {}})
    run = _minimal_run_result(turn_views=tuple(views))
    summary = compute_n1_session_health_summary(spine=spine, branch=branch, run_result=run, deterministic_config=cfg)
    assert summary.forgotten_anchor_flags.get("ledger") is True
    assert any(c.startswith("N1_FORGOTTEN_ANCHOR:") for c in summary.reason_codes)


def test_spine_json_roundtrip(tmp_path: Path) -> None:
    spine = build_n1_scenario_spine_definition(
        scenario_spine_id="roundtrip",
        narrative_anchor_ids=("a", "b"),
        progression_chain_step_ids=("p1",),
        revisit_expectations=(
            N1RevisitExpectation(
                revisit_node_id="gate",
                consistency_token="seal",
                trigger_player_substrings=("return to the gate",),
            ),
        ),
        metadata={"tier": "smoke"},
    )
    path = tmp_path / "spine.json"
    dump_n1_scenario_spine_to_json(spine, path)
    loaded = load_n1_scenario_spine_from_json(path)
    assert loaded.scenario_spine_id == spine.scenario_spine_id
    assert loaded.narrative_anchor_ids == spine.narrative_anchor_ids
    assert loaded.progression_chain_step_ids == spine.progression_chain_step_ids
    assert [r.revisit_node_id for r in loaded.revisit_expectations] == ["gate"]


def test_n1_scenario_spine_to_jsonable_sorts_revisit_nodes() -> None:
    spine = build_n1_scenario_spine_definition(
        scenario_spine_id="s",
        revisit_expectations=(
            N1RevisitExpectation("z_node", "tok", ("a",)),
            N1RevisitExpectation("a_node", "tok2", ("b",)),
        ),
    )
    payload = n1_scenario_spine_to_jsonable(spine)
    nodes = [r["revisit_node_id"] for r in payload["revisit_expectations"]]
    assert nodes == sorted(nodes)


def test_shared_prefix_branch_execution_and_comparison() -> None:
    spine = build_n1_scenario_spine_definition(scenario_spine_id="branchy")
    bp = N1BranchPointDefinition(branch_point_id="bp1", shared_prefix_turn_count=2, description="fork")
    profile = default_placeholder_profile()
    cfg = N1DeterministicRunConfig(seed=42, use_fake_gm=True, max_turns=10, profile_id=profile.profile_id)
    prefix = ("hello there", "what is this place?")
    b_left = N1BranchDefinition(branch_id="left", branch_point_id="bp1", suffix_player_texts=("I investigate quietly.",))
    b_right = N1BranchDefinition(branch_id="right", branch_point_id="bp1", suffix_player_texts=("I greet the nearest NPC.",))

    run_left = execute_n1_spine_branch_with_shared_prefix(
        spine=spine,
        branch_point=bp,
        branch=b_left,
        profile=profile,
        deterministic_config=cfg,
        shared_prefix_player_texts=prefix,
    )
    run_right = execute_n1_spine_branch_with_shared_prefix(
        spine=spine,
        branch_point=bp,
        branch=b_right,
        profile=profile,
        deterministic_config=cfg,
        shared_prefix_player_texts=prefix,
    )

    sum_left = compute_n1_session_health_summary(
        spine=spine,
        branch=b_left,
        run_result=run_left,
        deterministic_config=cfg,
    )
    sum_right = compute_n1_session_health_summary(
        spine=spine,
        branch=b_right,
        run_result=run_right,
        deterministic_config=cfg,
    )
    assert sum_left.branch_id != sum_right.branch_id
    assert stable_n1_run_id(
        scenario_spine_id=spine.scenario_spine_id,
        branch_id=b_left.branch_id,
        deterministic_config=cfg,
        player_texts=tuple(str(v.get("player_text") or "") for v in run_left.turn_views),
    ) != stable_n1_run_id(
        scenario_spine_id=spine.scenario_spine_id,
        branch_id=b_right.branch_id,
        deterministic_config=cfg,
        player_texts=tuple(str(v.get("player_text") or "") for v in run_right.turn_views),
    )

    texts_left = tuple(str(v.get("player_text") or "") for v in run_left.turn_views)
    texts_right = tuple(str(v.get("player_text") or "") for v in run_right.turn_views)
    cmp = compare_n1_branch_session_health_summaries(
        scenario_spine_id=spine.scenario_spine_id,
        branch_point=bp,
        summaries=(sum_left, sum_right),
        branch_full_player_texts={"left": texts_left, "right": texts_right},
    )
    assert cmp.compared_branch_ids == ("left", "right")
    assert cmp.per_branch_suffix_fingerprint["left"] != cmp.per_branch_suffix_fingerprint["right"]


def test_compare_requires_matching_prefix() -> None:
    spine = build_n1_scenario_spine_definition(scenario_spine_id="s")
    bp = N1BranchPointDefinition(branch_point_id="bp", shared_prefix_turn_count=1, description="")
    cfg = N1DeterministicRunConfig(seed=1, use_fake_gm=True, max_turns=2, profile_id="p")
    obs = (
        N1PerTurnContinuityObservation(
            0,
            None,
            "a",
            "b",
            {},
            {},
            -1,
            {},
        ),
    )
    s1 = N1SessionHealthSummary(
        run_id="r1",
        scenario_spine_id="s",
        branch_id="b1",
        deterministic_config=cfg,
        turn_count=2,
        per_turn_observations=obs * 2,
        continuity_verdict_ok=True,
        continuity_verdict_notes="",
        drift_flags={},
        forgotten_anchor_flags={},
        progression_chain_integrity_ok=True,
        progression_chain_integrity_flags={},
        revisit_consistency_ok=True,
        revisit_consistency_flags={},
        aggregate_issue_counts={},
        final_session_verdict="pass",
        reason_codes=(),
    )
    s2 = N1SessionHealthSummary(
        run_id="r2",
        scenario_spine_id="s",
        branch_id="b2",
        deterministic_config=cfg,
        turn_count=2,
        per_turn_observations=obs * 2,
        continuity_verdict_ok=True,
        continuity_verdict_notes="",
        drift_flags={},
        forgotten_anchor_flags={},
        progression_chain_integrity_ok=True,
        progression_chain_integrity_flags={},
        revisit_consistency_ok=True,
        revisit_consistency_flags={},
        aggregate_issue_counts={},
        final_session_verdict="pass",
        reason_codes=(),
    )
    with pytest.raises(ValueError, match="shared prefix"):
        compare_n1_branch_session_health_summaries(
            scenario_spine_id="s",
            branch_point=bp,
            summaries=(s1, s2),
            branch_full_player_texts={"b1": ("a", "x"), "b2": ("b", "y")},
        )


def test_collect_observations_scene_and_fingerprints_are_order_only() -> None:
    spine = build_n1_scenario_spine_definition(scenario_spine_id="s", narrative_anchor_ids=("needle",))
    views = (
        {
            "turn_index": 1,
            "player_text": "needle?",
            "gm_text": "the needle rests on the table",
            "raw_snapshot": {"scene_id": "room_a"},
        },
    )
    run = _minimal_run_result(turn_views=views)
    obs = collect_n1_per_turn_continuity_observations(spine=spine, run_result=run)
    assert len(obs) == 1
    assert obs[0].scene_id == "room_a"
    assert obs[0].anchor_hits["needle"] is True


def test_n1_registered_scenarios_sorted_unique_ids() -> None:
    specs = n1_registered_scenarios()
    ids = [s.scenario_id for s in specs]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))


def test_validate_n1_registered_scenario_bundle_rejects_duplicate_scenario_ids() -> None:
    specs = n1_registered_scenarios()
    impostor = replace(specs[0], scenario_id=specs[1].scenario_id)
    bad = (specs[1], impostor)
    with pytest.raises(ValueError, match="duplicate N1 scenario_id"):
        validate_n1_registered_scenario_bundle(bad)
