"""Analyzer-driven N1 regression tests (scenario spines + longitudinal continuity)."""

from __future__ import annotations

import json

import pytest

from tests.helpers.n1_continuity_analysis import (
    N1ContinuityIssue,
    N1LongitudinalContinuityReport,
    analyze_n1_branch_longitudinal_continuity,
    deterministic_continuity_report_json,
)
from tests.helpers.n1_scenario_spine_contract import (
    N1BranchDefinition,
    N1_REASON_BRANCH_DIVERGENT_FINAL_SCENE_ID,
    N1_REASON_BRANCH_SHARED_FACT_VIOLATION,
    N1_REASON_FORGOTTEN_ANCHOR,
    N1_REASON_NARRATIVE_GROUNDING_DEGRADED,
    N1_REASON_PROGRESSION_CHAIN_BROKEN,
    N1_REASON_REFERENT_INCONSISTENT,
    N1_REASON_REVISIT_SCENE_UNSTABLE,
)
from tests.helpers.n1_scenario_spine_harness import compare_n1_branch_session_health_summaries
from tests.helpers.n1_scenarios import (
    N1_ANCHOR_PERSISTENCE_LINES,
    N1_BRANCH_LEFT,
    N1_BRANCH_POINT_MAIN,
    N1_BRANCH_PREFIX_LINES,
    N1_BRANCH_RIGHT,
    N1_LINEAR_BRANCH_POINT,
    N1_PROGRESSION_LINES,
    N1_REVISIT_LINES,
    N1_SPINE_ANCHOR_PERSISTENCE,
    N1_SPINE_BRANCH,
    N1_SPINE_PROGRESSION,
    N1_SPINE_REVISIT,
    n1_default_fixture_deterministic_config,
    n1_fixture_fake_gm_responder,
    n1_player_texts_from_run,
    run_n1_scenario_and_analyze,
)
from tests.helpers.synthetic_profiles import default_placeholder_profile


def _issue_sort_key(issue: N1ContinuityIssue) -> tuple[str, str, str, int, int]:
    fs = issue.first_seen_turn if issue.first_seen_turn is not None else -1
    ls = issue.last_seen_turn if issue.last_seen_turn is not None else -1
    return (issue.severity, issue.category, issue.reason_code, fs, ls)


def _assert_longitudinal_report_structure(report: N1LongitudinalContinuityReport) -> None:
    merged = list(report.merged_reason_codes)
    assert merged == sorted(merged)
    assert report.issues == tuple(sorted(report.issues, key=_issue_sort_key))
    assert list(report.aggregate_issue_counters.keys()) == sorted(report.aggregate_issue_counters.keys())
    assert list(report.severity_counters.keys()) == sorted(report.severity_counters.keys())
    hard = report.severity_counters.get("hard", 0)
    soft = report.severity_counters.get("soft", 0)
    info = report.severity_counters.get("info", 0)
    assert hard + soft + info == len(report.issues)
    dumped_a = deterministic_continuity_report_json(report)
    dumped_b = deterministic_continuity_report_json(report)
    assert dumped_a == dumped_b
    parsed = json.loads(dumped_a)
    assert parsed["merged_reason_codes"] == sorted(parsed["merged_reason_codes"])


def _assert_no_forbidden_prefixes(merged: tuple[str, ...], forbidden_prefixes: tuple[str, ...]) -> None:
    for code in merged:
        assert not any(code.startswith(prefix) for prefix in forbidden_prefixes)


@pytest.fixture
def n1_profile() -> object:
    return default_placeholder_profile()


@pytest.fixture
def n1_cfg(n1_profile: object) -> object:
    return n1_default_fixture_deterministic_config(n1_profile)


def test_n1_anchor_persistence_fixture_analyzer_clean(n1_profile: object, n1_cfg: object) -> None:
    bp = N1_LINEAR_BRANCH_POINT
    branch = N1BranchDefinition(
        branch_id="n1_main",
        branch_point_id=bp.branch_point_id,
        suffix_player_texts=N1_ANCHOR_PERSISTENCE_LINES,
    )
    responder = n1_fixture_fake_gm_responder()
    analyzed = run_n1_scenario_and_analyze(
        spine=N1_SPINE_ANCHOR_PERSISTENCE,
        branch_point=bp,
        branch=branch,
        profile=n1_profile,
        deterministic_config=n1_cfg,
        shared_prefix_player_texts=(),
        fake_gm_responder=responder,
    )
    assert analyzed.summary.final_session_verdict == "pass"
    assert analyzed.summary.reason_codes == tuple(sorted(analyzed.summary.reason_codes))
    report = analyzed.longitudinal_report
    _assert_longitudinal_report_structure(report)
    assert report.severity_counters == {"hard": 0, "info": 0, "soft": 0}
    assert report.aggregate_issue_counters == {}
    _assert_no_forbidden_prefixes(
        report.merged_reason_codes,
        (
            f"{N1_REASON_REFERENT_INCONSISTENT}:",
            f"{N1_REASON_REVISIT_SCENE_UNSTABLE}:",
            N1_REASON_PROGRESSION_CHAIN_BROKEN,
            N1_REASON_NARRATIVE_GROUNDING_DEGRADED,
            f"{N1_REASON_FORGOTTEN_ANCHOR}:",
            f"{N1_REASON_BRANCH_SHARED_FACT_VIOLATION}:",
        ),
    )


def test_n1_revisit_fixture_analyzer_clean(n1_profile: object, n1_cfg: object) -> None:
    bp = N1_LINEAR_BRANCH_POINT
    branch = N1BranchDefinition(
        branch_id="n1_main",
        branch_point_id=bp.branch_point_id,
        suffix_player_texts=N1_REVISIT_LINES,
    )
    analyzed = run_n1_scenario_and_analyze(
        spine=N1_SPINE_REVISIT,
        branch_point=bp,
        branch=branch,
        profile=n1_profile,
        deterministic_config=n1_cfg,
        shared_prefix_player_texts=(),
        fake_gm_responder=n1_fixture_fake_gm_responder(),
    )
    assert analyzed.summary.revisit_consistency_ok is True
    assert analyzed.summary.final_session_verdict == "pass"
    assert analyzed.summary.reason_codes == tuple(sorted(analyzed.summary.reason_codes))
    report = analyzed.longitudinal_report
    _assert_longitudinal_report_structure(report)
    assert report.severity_counters == {"hard": 0, "info": 0, "soft": 0}
    _assert_no_forbidden_prefixes(
        report.merged_reason_codes,
        (
            f"{N1_REASON_REFERENT_INCONSISTENT}:",
            f"{N1_REASON_REVISIT_SCENE_UNSTABLE}:",
            N1_REASON_PROGRESSION_CHAIN_BROKEN,
            N1_REASON_NARRATIVE_GROUNDING_DEGRADED,
        ),
    )


def test_n1_progression_chain_fixture_analyzer_clean(n1_profile: object, n1_cfg: object) -> None:
    bp = N1_LINEAR_BRANCH_POINT
    branch = N1BranchDefinition(
        branch_id="n1_main",
        branch_point_id=bp.branch_point_id,
        suffix_player_texts=N1_PROGRESSION_LINES,
    )
    analyzed = run_n1_scenario_and_analyze(
        spine=N1_SPINE_PROGRESSION,
        branch_point=bp,
        branch=branch,
        profile=n1_profile,
        deterministic_config=n1_cfg,
        shared_prefix_player_texts=(),
        fake_gm_responder=n1_fixture_fake_gm_responder(),
    )
    assert analyzed.summary.progression_chain_integrity_ok is True
    assert analyzed.summary.final_session_verdict == "pass"
    assert analyzed.summary.reason_codes == tuple(sorted(analyzed.summary.reason_codes))
    report = analyzed.longitudinal_report
    _assert_longitudinal_report_structure(report)
    assert report.severity_counters == {"hard": 0, "info": 0, "soft": 0}
    _assert_no_forbidden_prefixes(
        report.merged_reason_codes,
        (
            f"{N1_REASON_REFERENT_INCONSISTENT}:",
            f"{N1_REASON_REVISIT_SCENE_UNSTABLE}:",
            N1_REASON_PROGRESSION_CHAIN_BROKEN,
            N1_REASON_NARRATIVE_GROUNDING_DEGRADED,
        ),
    )


def test_n1_branch_fixture_branch_analyzer_signals(n1_profile: object, n1_cfg: object) -> None:
    responder = n1_fixture_fake_gm_responder()
    left = run_n1_scenario_and_analyze(
        spine=N1_SPINE_BRANCH,
        branch_point=N1_BRANCH_POINT_MAIN,
        branch=N1_BRANCH_LEFT,
        profile=n1_profile,
        deterministic_config=n1_cfg,
        shared_prefix_player_texts=N1_BRANCH_PREFIX_LINES,
        fake_gm_responder=responder,
    )
    right = run_n1_scenario_and_analyze(
        spine=N1_SPINE_BRANCH,
        branch_point=N1_BRANCH_POINT_MAIN,
        branch=N1_BRANCH_RIGHT,
        profile=n1_profile,
        deterministic_config=n1_cfg,
        shared_prefix_player_texts=N1_BRANCH_PREFIX_LINES,
        fake_gm_responder=responder,
    )
    assert left.summary.final_session_verdict == "pass"
    assert right.summary.final_session_verdict == "pass"
    assert left.summary.reason_codes == tuple(sorted(left.summary.reason_codes))
    assert right.summary.reason_codes == tuple(sorted(right.summary.reason_codes))

    for side in (left, right):
        _assert_longitudinal_report_structure(side.longitudinal_report)
        assert side.longitudinal_report.severity_counters == {"hard": 0, "info": 0, "soft": 0}
        _assert_no_forbidden_prefixes(
            side.longitudinal_report.merged_reason_codes,
            (
                f"{N1_REASON_REFERENT_INCONSISTENT}:",
                f"{N1_REASON_REVISIT_SCENE_UNSTABLE}:",
                N1_REASON_PROGRESSION_CHAIN_BROKEN,
                N1_REASON_NARRATIVE_GROUNDING_DEGRADED,
                f"{N1_REASON_BRANCH_SHARED_FACT_VIOLATION}:",
            ),
        )

    comparison = compare_n1_branch_session_health_summaries(
        scenario_spine_id=N1_SPINE_BRANCH.scenario_spine_id,
        branch_point=N1_BRANCH_POINT_MAIN,
        summaries=(left.summary, right.summary),
        branch_full_player_texts={
            left.summary.branch_id: n1_player_texts_from_run(left.run_result),
            right.summary.branch_id: n1_player_texts_from_run(right.run_result),
        },
    )
    assert comparison.divergence_detected is True
    branch_issues = analyze_n1_branch_longitudinal_continuity(
        spine=N1_SPINE_BRANCH,
        branch_point=N1_BRANCH_POINT_MAIN,
        summaries=(left.summary, right.summary),
        comparison=comparison,
    )
    assert branch_issues == tuple(sorted(branch_issues, key=_issue_sort_key))
    codes = [i.reason_code for i in branch_issues]
    assert N1_REASON_BRANCH_DIVERGENT_FINAL_SCENE_ID in codes
    assert not any(c.startswith(f"{N1_REASON_BRANCH_SHARED_FACT_VIOLATION}:") for c in codes)
    assert any(i.reason_code == N1_REASON_BRANCH_DIVERGENT_FINAL_SCENE_ID and i.severity == "info" for i in branch_issues)
