"""Longitudinal continuity analyzer tests (N1 test tooling)."""

from __future__ import annotations

from tests.helpers.n1_continuity_analysis import (
    analyze_n1_branch_longitudinal_continuity,
    analyze_n1_longitudinal_continuity,
    deterministic_continuity_report_json,
)
from tests.helpers.n1_scenario_spine_contract import (
    N1BranchComparisonSummary,
    N1BranchDefinition,
    N1BranchPointDefinition,
    N1DeterministicRunConfig,
    N1PerTurnContinuityObservation,
    N1RevisitExpectation,
    N1SessionHealthSummary,
    N1_REASON_BRANCH_DIVERGENT_FINAL_SCENE_ID,
    N1_REASON_BRANCH_SHARED_FACT_VIOLATION,
    N1_REASON_FORGOTTEN_ANCHOR,
    N1_REASON_PROGRESSION_CHAIN_BROKEN,
    N1_REASON_REFERENT_INCONSISTENT,
    N1_REASON_REVISIT_INCONSISTENT,
    N1_REASON_REVISIT_SCENE_UNSTABLE,
)
from tests.helpers.n1_scenario_spine_harness import (
    build_n1_scenario_spine_definition,
    collect_n1_per_turn_continuity_observations,
    compare_n1_branch_session_health_summaries,
    compute_n1_session_health_summary,
    execute_n1_spine_branch_with_shared_prefix,
    stable_n1_run_id,
)
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


def test_merged_reason_codes_lexically_sorted() -> None:
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
        spine=spine, branch=branch, run_result=run, deterministic_config=cfg
    )
    report = analyze_n1_longitudinal_continuity(spine=spine, summary=summary)
    codes = list(report.merged_reason_codes)
    assert codes == sorted(codes)


def test_forgotten_anchor_multi_turn_turn_metadata() -> None:
    spine = build_n1_scenario_spine_definition(scenario_spine_id="s", narrative_anchor_ids=("ledger",))
    branch = N1BranchDefinition(branch_id="b", branch_point_id="bp")
    cfg = N1DeterministicRunConfig(seed=0, use_fake_gm=True, max_turns=4, profile_id="p")
    views = []
    for i in range(4):
        gm = "ledger clue" if i == 0 else "no anchor here"
        views.append({"turn_index": i, "player_text": f"t{i}", "gm_text": gm, "raw_snapshot": {}})
    run = _minimal_run_result(turn_views=tuple(views))
    summary = compute_n1_session_health_summary(spine=spine, branch=branch, run_result=run, deterministic_config=cfg)
    report = analyze_n1_longitudinal_continuity(spine=spine, summary=summary)
    forgotten = [i for i in report.issues if i.reason_code.startswith(N1_REASON_FORGOTTEN_ANCHOR)]
    assert len(forgotten) == 1
    assert forgotten[0].first_seen_turn == 0
    assert forgotten[0].last_seen_turn == 0
    assert forgotten[0].severity == "hard"


def test_revisit_inconsistency_and_scene_unstable() -> None:
    spine = build_n1_scenario_spine_definition(
        scenario_spine_id="s",
        revisit_expectations=(
            N1RevisitExpectation(
                revisit_node_id="gate",
                consistency_token="seal",
                trigger_player_substrings=("return to the gate",),
            ),
        ),
    )
    branch = N1BranchDefinition(branch_id="b", branch_point_id="bp")
    cfg = N1DeterministicRunConfig(seed=0, use_fake_gm=True, max_turns=3, profile_id="p")
    views = (
        {
            "turn_index": 0,
            "player_text": "return to the gate",
            "gm_text": "seal intact on return",
            "raw_snapshot": {"scene_id": "court_a"},
        },
        {
            "turn_index": 1,
            "player_text": "look around",
            "gm_text": "dust",
            "raw_snapshot": {"scene_id": "court_a"},
        },
        {
            "turn_index": 2,
            "player_text": "return to the gate",
            "gm_text": "wrong lore no token",
            "raw_snapshot": {"scene_id": "court_b"},
        },
    )
    run = _minimal_run_result(turn_views=views)
    summary = compute_n1_session_health_summary(spine=spine, branch=branch, run_result=run, deterministic_config=cfg)
    texts = {int(v["turn_index"]): str(v["player_text"]) for v in views}
    report = analyze_n1_longitudinal_continuity(spine=spine, summary=summary, player_texts_by_turn=texts)
    codes = report.merged_reason_codes
    assert any(c.startswith(N1_REASON_REVISIT_INCONSISTENT) for c in codes)
    assert any(c.startswith(N1_REASON_REVISIT_SCENE_UNSTABLE) for c in codes)


def test_progression_chain_break_in_report() -> None:
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
    report = analyze_n1_longitudinal_continuity(spine=spine, summary=summary)
    assert N1_REASON_PROGRESSION_CHAIN_BROKEN in report.merged_reason_codes
    prog_issues = [i for i in report.issues if i.reason_code == N1_REASON_PROGRESSION_CHAIN_BROKEN]
    assert prog_issues and prog_issues[0].severity == "hard"
    assert prog_issues[0].first_seen_turn == 0
    assert prog_issues[0].last_seen_turn == 1


def test_branch_divergence_allowed_shared_fact_violation_hard() -> None:
    spine = build_n1_scenario_spine_definition(scenario_spine_id="branchy", narrative_anchor_ids=("ledger",))
    bp = N1BranchPointDefinition(branch_point_id="bp1", shared_prefix_turn_count=1, description="fork")
    cfg = N1DeterministicRunConfig(seed=1, use_fake_gm=True, max_turns=4, profile_id="p")

    def _obs(*, anchor0: bool, forgotten: bool) -> tuple[N1PerTurnContinuityObservation, ...]:
        # 4 turns; prefix turn 0 establishes anchor when anchor0; tail without anchor if forgotten
        rows: list[N1PerTurnContinuityObservation] = []
        for t in range(4):
            hit = anchor0 if t == 0 else (not forgotten or t < 2)
            if forgotten and t >= 2:
                hit = False
            rows.append(
                N1PerTurnContinuityObservation(
                    turn_index=t,
                    scene_id="room",
                    gm_text_fingerprint=f"fp{t}",
                    player_text_fingerprint=f"pp{t}",
                    anchor_hits={"ledger": hit},
                    progression_hits={},
                    progression_chain_index_ceiling=-1,
                    revisit_hits={},
                )
            )
        return tuple(rows)

    sum_ok = N1SessionHealthSummary(
        run_id="r_ok",
        scenario_spine_id=spine.scenario_spine_id,
        branch_id="left",
        deterministic_config=cfg,
        turn_count=4,
        per_turn_observations=_obs(anchor0=True, forgotten=False),
        continuity_verdict_ok=True,
        continuity_verdict_notes="",
        drift_flags={"gm_text_empty_turns": False, "player_text_empty_turns": False},
        forgotten_anchor_flags={"ledger": False},
        progression_chain_integrity_ok=True,
        progression_chain_integrity_flags={},
        revisit_consistency_ok=True,
        revisit_consistency_flags={},
        aggregate_issue_counts={},
        final_session_verdict="pass",
        reason_codes=(),
    )
    sum_bad = N1SessionHealthSummary(
        run_id="r_bad",
        scenario_spine_id=spine.scenario_spine_id,
        branch_id="right",
        deterministic_config=cfg,
        turn_count=4,
        per_turn_observations=_obs(anchor0=True, forgotten=True),
        continuity_verdict_ok=True,
        continuity_verdict_notes="",
        drift_flags={"gm_text_empty_turns": False, "player_text_empty_turns": False},
        forgotten_anchor_flags={"ledger": True},
        progression_chain_integrity_ok=True,
        progression_chain_integrity_flags={},
        revisit_consistency_ok=True,
        revisit_consistency_flags={},
        aggregate_issue_counts={},
        final_session_verdict="fail",
        reason_codes=(f"{N1_REASON_FORGOTTEN_ANCHOR}:ledger",),
    )
    cmp = N1BranchComparisonSummary(
        scenario_spine_id=spine.scenario_spine_id,
        branch_point_id=bp.branch_point_id,
        compared_branch_ids=("left", "right"),
        shared_prefix_turn_count=1,
        shared_prefix_fingerprint="x",
        per_branch_suffix_fingerprint={"left": "a", "right": "b"},
        per_branch_final_scene_id={"left": "hall", "right": "yard"},
        divergence_detected=True,
        reason_codes=(N1_REASON_BRANCH_DIVERGENT_FINAL_SCENE_ID,),
    )
    branch_issues = analyze_n1_branch_longitudinal_continuity(
        spine=spine, branch_point=bp, summaries=(sum_ok, sum_bad), comparison=cmp
    )
    assert any(i.reason_code.startswith(N1_REASON_BRANCH_SHARED_FACT_VIOLATION) for i in branch_issues)
    info = [i for i in branch_issues if i.severity == "info"]
    assert any(i.reason_code == N1_REASON_BRANCH_DIVERGENT_FINAL_SCENE_ID for i in info)


def test_deterministic_report_json_repeated() -> None:
    spine = build_n1_scenario_spine_definition(scenario_spine_id="s", narrative_anchor_ids=("zz_n1_ground_marker",))
    branch = N1BranchDefinition(branch_id="b", branch_point_id="bp")
    cfg = N1DeterministicRunConfig(seed=0, use_fake_gm=True, max_turns=6, profile_id="p")
    # First half anchored, second half bare -> grounding degraded heuristic
    views = []
    for i in range(6):
        gm = "zz_n1_ground_marker holds" if i < 3 else "generic ambience only"
        views.append({"turn_index": i, "player_text": f"p{i}", "gm_text": gm, "raw_snapshot": {"scene_id": "s1"}})
    run = _minimal_run_result(turn_views=tuple(views))
    summary = compute_n1_session_health_summary(spine=spine, branch=branch, run_result=run, deterministic_config=cfg)
    r1 = analyze_n1_longitudinal_continuity(spine=spine, summary=summary)
    r2 = analyze_n1_longitudinal_continuity(spine=spine, summary=summary)
    assert deterministic_continuity_report_json(r1) == deterministic_continuity_report_json(r2)


def test_referent_inconsistency_pattern() -> None:
    spine = build_n1_scenario_spine_definition(scenario_spine_id="s", narrative_anchor_ids=("needle",))
    branch = N1BranchDefinition(branch_id="b", branch_point_id="bp")
    cfg = N1DeterministicRunConfig(seed=0, use_fake_gm=True, max_turns=4, profile_id="p")
    views = []
    gms = ("needle here", "no", "still no", "needle again")
    for i in range(4):
        views.append(
            {
                "turn_index": i,
                "player_text": f"p{i}",
                "gm_text": gms[i],
                "raw_snapshot": {"scene_id": "workshop"},
            }
        )
    run = _minimal_run_result(turn_views=tuple(views))
    summary = compute_n1_session_health_summary(spine=spine, branch=branch, run_result=run, deterministic_config=cfg)
    report = analyze_n1_longitudinal_continuity(spine=spine, summary=summary)
    assert any(c.startswith(N1_REASON_REFERENT_INCONSISTENT) for c in report.merged_reason_codes)


def test_foundational_harness_still_importable() -> None:
    """Guard: foundational N1 module remains wired (backward compatibility)."""
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
    assert obs[0].anchor_hits["needle"] is True


def test_integration_branch_compare_with_analyzer() -> None:
    """Synthetic branch runs: comparison + longitudinal report stay deterministic."""
    spine = build_n1_scenario_spine_definition(scenario_spine_id="branchy")
    bp = N1BranchPointDefinition(branch_point_id="bp1", shared_prefix_turn_count=2, description="fork")
    profile = default_placeholder_profile()
    cfg = N1DeterministicRunConfig(seed=42, use_fake_gm=True, max_turns=10, profile_id=profile.profile_id)
    prefix = ("hello there", "what is this place?")
    b_left = N1BranchDefinition(branch_id="left", branch_point_id="bp1", suffix_player_texts=("I investigate quietly.",))
    b_right = N1BranchDefinition(branch_id="right", branch_point_id="bp1", suffix_player_texts=("I greet the nearest NPC.",))

    run_left = execute_n1_spine_branch_with_shared_prefix(
        spine=spine, branch_point=bp, branch=b_left, profile=profile, deterministic_config=cfg, shared_prefix_player_texts=prefix
    )
    run_right = execute_n1_spine_branch_with_shared_prefix(
        spine=spine, branch_point=bp, branch=b_right, profile=profile, deterministic_config=cfg, shared_prefix_player_texts=prefix
    )
    sum_left = compute_n1_session_health_summary(
        spine=spine, branch=b_left, run_result=run_left, deterministic_config=cfg
    )
    sum_right = compute_n1_session_health_summary(
        spine=spine, branch=b_right, run_result=run_right, deterministic_config=cfg
    )
    texts_left = tuple(str(v.get("player_text") or "") for v in run_left.turn_views)
    texts_right = tuple(str(v.get("player_text") or "") for v in run_right.turn_views)
    cmp = compare_n1_branch_session_health_summaries(
        scenario_spine_id=spine.scenario_spine_id,
        branch_point=bp,
        summaries=(sum_left, sum_right),
        branch_full_player_texts={"left": texts_left, "right": texts_right},
    )
    rep_l = analyze_n1_longitudinal_continuity(spine=spine, summary=sum_left)
    rep_r = analyze_n1_longitudinal_continuity(spine=spine, summary=sum_right)
    assert rep_l.run_id == stable_n1_run_id(
        scenario_spine_id=spine.scenario_spine_id,
        branch_id="left",
        deterministic_config=cfg,
        player_texts=texts_left,
    )
    branch_issues = analyze_n1_branch_longitudinal_continuity(
        spine=spine, branch_point=bp, summaries=(sum_left, sum_right), comparison=cmp
    )
    if cmp.divergence_detected:
        assert any(i.reason_code == N1_REASON_BRANCH_DIVERGENT_FINAL_SCENE_ID for i in branch_issues)
    assert deterministic_continuity_report_json(rep_l) == deterministic_continuity_report_json(
        analyze_n1_longitudinal_continuity(spine=spine, summary=sum_left)
    )
