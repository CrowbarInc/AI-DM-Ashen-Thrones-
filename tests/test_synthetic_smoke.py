"""Deterministic synthetic smoke tests built on run_synthetic_session."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

import pytest

from tests.helpers.synthetic_profiles import profile_bold_opportunist
from tests.helpers.synthetic_runner import run_synthetic_session
from tests.helpers.synthetic_scenarios import (
    SyntheticScenario,
    clue_followup_opening,
    default_opening,
    directed_social_opening,
    emergent_npc_opening,
    friction_opening,
    investigation_opening,
    magic_anomaly_opening,
    retry_pressure_opening,
    social_opening,
)
from tests.helpers.synthetic_scoring import detect_soft_lock, summarize_synthetic_run
from tests.helpers.synthetic_types import SyntheticRunResult

pytestmark = [pytest.mark.synthetic, pytest.mark.slow]

# Template slugs are stable harness signals from :func:`decide_placeholder` (``profile_id:slug`` rationales).

_SOCIAL_OR_QUESTION_SLUGS = frozenset(
    {"social_direct", "social_probe", "negotiate_trade", "hypothetical_question"},
)
_SOCIAL_CORE_SLUGS = frozenset({"social_direct", "social_probe", "negotiate_trade"})
_ARCANE_PROBE_SLUGS = frozenset({"arcane_sense"})
_INVESTIGATIVE_SLUGS = frozenset(
    {"cautious_survey", "investigate_inconsistency", "persistence_followup"},
)
_RULES_FRICTION_SLUGS = frozenset({"rules_clarify", "edge_case_press"})
_CAUTIOUS_LEANING_SLUGS = frozenset(
    {"cautious_survey", "investigate_inconsistency", "persistence_followup"},
)
_BOLD_LEANING_SLUGS = frozenset({"bold_push", "negotiate_trade", "hang_back", "hypothetical_question"})

_TRANSCRIPT_SOFT_DEFAULT_SLUGS = _CAUTIOUS_LEANING_SLUGS
_TRANSCRIPT_SOFT_SOCIAL_SLUGS = _SOCIAL_OR_QUESTION_SLUGS

_KNOWN_STOP_REASONS = {
    "max_turns_reached",
    "stall_repeat_threshold",
    "policy_stop",
    "external_stop",
}


def _assert_compact_smoke_invariants(run_result: SyntheticRunResult) -> None:
    summary = summarize_synthetic_run(run_result)
    assert run_result.stop_reason in _KNOWN_STOP_REASONS, summary
    assert run_result.turn_views, summary
    assert all(str(view.get("player_text", "")).strip() for view in run_result.turn_views), summary
    assert all(str(view.get("gm_text", "")).strip() for view in run_result.turn_views), summary

    soft_lock = detect_soft_lock(run_result, repeat_window=3, low_variation_window=4)
    assert soft_lock["is_soft_lock"] is False, f"{summary} soft_lock={soft_lock}"


def _assert_transcript_probe_invariants(
    run_result: SyntheticRunResult,
    *,
    max_turns: int,
) -> None:
    summary = summarize_synthetic_run(run_result)
    assert run_result.stop_reason in _KNOWN_STOP_REASONS, summary
    assert run_result.turn_views, summary
    assert len(run_result.turn_views) <= max_turns, summary
    assert all(str(view.get("player_text", "")).strip() for view in run_result.turn_views), summary
    assert all(str(view.get("gm_text", "")).strip() for view in run_result.turn_views), summary


def _policy_template_slugs(run_result: SyntheticRunResult) -> tuple[str, ...]:
    """Return policy template slugs from ``profile_id:slug`` rationales (skips ``provided`` turns)."""
    slugs: list[str] = []
    for view in run_result.turn_views:
        rationale = str(view.get("decision_rationale", "")).strip()
        if rationale == "provided":
            continue
        if ":" in rationale:
            _, slug = rationale.split(":", 1)
            slug = slug.strip()
            if slug:
                slugs.append(slug)
    return tuple(slugs)


def _fake_gm_profile_expectation_message(
    scenario: SyntheticScenario,
    run_result: SyntheticRunResult,
    *,
    detail: str,
    bug_class: str | None = None,
) -> str:
    profile_id = scenario.profile_factory().profile_id
    effective_bug_class = bug_class or scenario.regression_risk_class or "unspecified"
    return (
        f"{detail} | bug_class={effective_bug_class!r} "
        f"scenario_id={scenario.scenario_id!r} profile_id={profile_id!r} "
        f"seed={run_result.seed} template_slugs={list(_policy_template_slugs(run_result))!r} | "
        f"{summarize_synthetic_run(run_result)}"
    )


def _assert_slug_bucket_hit(
    run_result: SyntheticRunResult,
    scenario: SyntheticScenario,
    bucket: frozenset[str],
    *,
    label: str,
    bug_class: str | None = None,
) -> None:
    slugs = frozenset(_policy_template_slugs(run_result))
    detail = f"missing {label}; expected_any_of={sorted(bucket)!r} got_slugs={sorted(slugs)!r}"
    assert slugs & bucket, _fake_gm_profile_expectation_message(
        scenario,
        run_result,
        detail=detail,
        bug_class=bug_class,
    )


def _assert_seeded_first_turn_used(
    run_result: SyntheticRunResult,
    scenario: SyntheticScenario,
    *,
    bug_class: str | None = None,
) -> None:
    first_rationale = str(run_result.turn_views[0].get("decision_rationale", "")).strip()
    assert first_rationale == "provided", _fake_gm_profile_expectation_message(
        scenario,
        run_result,
        detail=f"expected fixed first turn to be used; first_rationale={first_rationale!r}",
        bug_class=bug_class,
    )


@pytest.mark.parametrize(
    "scenario_factory",
    (
        pytest.param(default_opening, id="default-opening"),
        pytest.param(social_opening, id="social-opening"),
        pytest.param(friction_opening, id="friction-opening"),
        pytest.param(investigation_opening, id="investigation-opening"),
        pytest.param(magic_anomaly_opening, id="magic-anomaly-opening"),
        pytest.param(directed_social_opening, id="directed-social-opening"),
        pytest.param(emergent_npc_opening, id="emergent-npc-opening"),
        pytest.param(clue_followup_opening, id="clue-followup-opening"),
        pytest.param(retry_pressure_opening, id="retry-pressure-opening"),
    ),
)
def test_synthetic_smoke_run_is_deterministic_and_healthy(
    scenario_factory: Callable[[], SyntheticScenario],
):
    scenario = scenario_factory()
    kwargs = scenario.run_kwargs(use_fake_gm=True)
    result_a = run_synthetic_session(**kwargs)
    result_b = run_synthetic_session(**kwargs)

    assert result_a.stop_reason == result_b.stop_reason, summarize_synthetic_run(result_a)
    assert result_a.turn_views == result_b.turn_views, summarize_synthetic_run(result_a)
    _assert_compact_smoke_invariants(result_a)


def test_synthetic_smoke_profiles_show_variation():
    shared_seed = 404
    scenarios = (
        replace(default_opening(), seed=shared_seed),
        replace(social_opening(), seed=shared_seed),
        replace(friction_opening(), seed=shared_seed),
    )
    runs = tuple(run_synthetic_session(**s.run_kwargs(use_fake_gm=True)) for s in scenarios)

    for run_result in runs:
        _assert_compact_smoke_invariants(run_result)

    first_inputs = [str(run.turn_views[0].get("player_text", "")).strip() for run in runs]
    summaries = " | ".join(summarize_synthetic_run(run) for run in runs)
    assert len(set(first_inputs)) >= 2, summaries


# --- Fake-GM lane: strong deterministic profile expectations (real scenario presets) ---


def test_fake_gm_profile_expectation_social_opening_social_prober():
    scenario = replace(social_opening(), seed=909)
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_slug_bucket_hit(
        run_result,
        scenario,
        _SOCIAL_OR_QUESTION_SLUGS,
        label="social/question-or-trade template slug",
    )


def test_fake_gm_profile_expectation_magic_anomaly_opening_arcane_examiner():
    scenario = replace(magic_anomaly_opening(), seed=919)
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_slug_bucket_hit(
        run_result,
        scenario,
        _ARCANE_PROBE_SLUGS,
        label="arcane probe template slug",
    )
    arcane_hits = sum(
        1
        for view in run_result.turn_views
        if "magic" in str(view.get("player_text", "")).lower()
        or "arcane" in str(view.get("player_text", "")).lower()
        or "dispelled" in str(view.get("player_text", "")).lower()
    )
    assert arcane_hits >= 1, _fake_gm_profile_expectation_message(
        scenario,
        run_result,
        detail="expected>=1 player line broadly themed magic/anomaly in combined turns",
    )


def test_fake_gm_profile_expectation_investigation_opening_cautious_investigator():
    scenario = replace(investigation_opening(), seed=929)
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_slug_bucket_hit(
        run_result,
        scenario,
        _INVESTIGATIVE_SLUGS,
        label="investigative follow-up template slug after fixed opener",
    )


def test_fake_gm_profile_expectation_friction_opening_adversarial_rules_poker():
    scenario = replace(friction_opening(), seed=939)
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_slug_bucket_hit(
        run_result,
        scenario,
        _RULES_FRICTION_SLUGS,
        label="rules/edge-case pressure template slug",
    )


def test_fake_gm_profile_expectation_default_opening_cautious_vs_bold_diverge():
    seed = 777001
    cautious_scenario = replace(default_opening(), seed=seed)
    bold_scenario = replace(default_opening(), seed=seed, profile_factory=profile_bold_opportunist)

    cautious_run = run_synthetic_session(**cautious_scenario.run_kwargs(use_fake_gm=True))
    bold_run = run_synthetic_session(**bold_scenario.run_kwargs(use_fake_gm=True))

    for run_result, scenario in (
        (cautious_run, cautious_scenario),
        (bold_run, bold_scenario),
    ):
        _assert_compact_smoke_invariants(run_result)

    cautious_slugs = _policy_template_slugs(cautious_run)
    bold_slugs = _policy_template_slugs(bold_run)
    cautious_set = frozenset(cautious_slugs)
    bold_set = frozenset(bold_slugs)

    assert cautious_slugs != bold_slugs, _fake_gm_profile_expectation_message(
        bold_scenario,
        bold_run,
        detail=f"expected differing slug sequences; cautious={cautious_slugs!r} bold={bold_slugs!r}",
    )
    assert cautious_set != bold_set, _fake_gm_profile_expectation_message(
        bold_scenario,
        bold_run,
        detail=f"expected differing slug sets; cautious={sorted(cautious_set)!r} bold={sorted(bold_set)!r}",
    )
    assert cautious_set & _CAUTIOUS_LEANING_SLUGS, _fake_gm_profile_expectation_message(
        cautious_scenario,
        cautious_run,
        detail=f"expected cautious-leaning slug; got {cautious_slugs!r}",
    )
    assert bold_set & _BOLD_LEANING_SLUGS, _fake_gm_profile_expectation_message(
        bold_scenario,
        bold_run,
        detail=f"expected bold-leaning slug; got {bold_slugs!r}",
    )


def test_fake_gm_profile_expectation_directed_social_opening_stays_social() -> None:
    scenario = replace(directed_social_opening(), seed=949)
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario)
    _assert_slug_bucket_hit(
        run_result,
        scenario,
        _SOCIAL_OR_QUESTION_SLUGS,
        label="directed social follow-up template slug",
    )


def test_fake_gm_profile_expectation_emergent_npc_opening_prefers_social_core() -> None:
    scenario = replace(emergent_npc_opening(), seed=959)
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_slug_bucket_hit(
        run_result,
        scenario,
        _SOCIAL_CORE_SLUGS,
        label="emergent npc social-core template slug",
    )


def test_fake_gm_profile_expectation_clue_followup_opening_remains_investigative() -> None:
    scenario = replace(clue_followup_opening(), seed=969)
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario)
    _assert_slug_bucket_hit(
        run_result,
        scenario,
        _INVESTIGATIVE_SLUGS,
        label="clue follow-up investigative template slug",
    )


def test_fake_gm_profile_expectation_retry_pressure_opening_hits_rules_friction() -> None:
    scenario = replace(retry_pressure_opening(), seed=979)
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario)
    _assert_slug_bucket_hit(
        run_result,
        scenario,
        _RULES_FRICTION_SLUGS,
        label="retry pressure rules/edge-case template slug",
    )
    policy_turn_texts = [
        str(view.get("player_text", "")).strip().lower()
        for view in run_result.turn_views
        if str(view.get("decision_rationale", "")).strip() != "provided"
    ]
    assert any(
        ("?" in text) or ("clarif" in text) or ("ruling" in text) or ("edge case" in text)
        for text in policy_turn_texts
    ), _fake_gm_profile_expectation_message(
        scenario,
        run_result,
        detail="expected>=1 policy turn broadly framed as clarification/retry pressure",
    )


# --- Regression-mapped fake-GM lane checks (historical project risk classes) ---


def test_fake_gm_regression_directed_social_routing_confusion_guard() -> None:
    # Historical risk mapping: directed social opener previously drifted away from addressed contact.
    scenario = replace(directed_social_opening(), seed=1951)
    bug_class = "directed_social_routing_confusion"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario, bug_class=bug_class)
    _assert_slug_bucket_hit(
        run_result,
        scenario,
        _SOCIAL_CORE_SLUGS,
        label="on-theme social routing follow-up slug",
        bug_class=bug_class,
    )


def test_fake_gm_regression_emergent_npc_addressability_redirect_guard() -> None:
    # Historical risk mapping: unscripted social turns occasionally collapsed into non-addressable redirects.
    scenario = replace(emergent_npc_opening(), seed=1952)
    bug_class = "emergent_npc_addressability_redirect"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_slug_bucket_hit(
        run_result,
        scenario,
        _SOCIAL_CORE_SLUGS,
        label="emergent social-addressability slug",
        bug_class=bug_class,
    )


def test_fake_gm_regression_clue_followup_contradiction_pressure_guard() -> None:
    # Historical risk mapping: clue contradiction prompts could lose investigative pressure too early.
    scenario = replace(clue_followup_opening(), seed=1953)
    bug_class = "lead_followup_contradiction_pressure"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario, bug_class=bug_class)
    _assert_slug_bucket_hit(
        run_result,
        scenario,
        _INVESTIGATIVE_SLUGS,
        label="continued clue-followup investigative slug",
        bug_class=bug_class,
    )


def test_fake_gm_regression_retry_fallback_clarification_pressure_guard() -> None:
    # Historical risk mapping: retry/ruling pressure could fall into degenerate non-clarifying loops.
    scenario = replace(retry_pressure_opening(), seed=1954)
    bug_class = "retry_fallback_clarification_pressure"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario, bug_class=bug_class)
    _assert_slug_bucket_hit(
        run_result,
        scenario,
        _RULES_FRICTION_SLUGS,
        label="retry/clarification pressure slug",
        bug_class=bug_class,
    )
    policy_turn_texts = [
        str(view.get("player_text", "")).strip().lower()
        for view in run_result.turn_views
        if str(view.get("decision_rationale", "")).strip() != "provided"
    ]
    assert any(
        ("?" in text) or ("clarif" in text) or ("ruling" in text) or ("retry" in text)
        for text in policy_turn_texts
    ), _fake_gm_profile_expectation_message(
        scenario,
        run_result,
        detail="expected>=1 policy turn applying clarification/retry pressure",
        bug_class=bug_class,
    )


# --- Transcript lane: lightweight wiring sanity checks (no narrative overfit) ---


def _assert_transcript_soft_policy_signal(
    *,
    scenario: SyntheticScenario,
    run_result: SyntheticRunResult,
    slug_bucket: frozenset[str],
    signal_label: str,
    bug_class: str | None = None,
) -> None:
    slugs = frozenset(_policy_template_slugs(run_result))
    profile_id = scenario.profile_factory().profile_id
    effective_bug_class = bug_class or scenario.regression_risk_class or "unspecified"
    detail = (
        f"transcript soft policy signal missing ({signal_label}); "
        f"expected_any_of={sorted(slug_bucket)!r} got_slugs={sorted(slugs)!r}"
    )
    msg = (
        f"{detail} | bug_class={effective_bug_class!r} "
        f"scenario_id={scenario.scenario_id!r} profile_id={profile_id!r} "
        f"seed={run_result.seed} | {summarize_synthetic_run(run_result)}"
    )
    assert slugs & slug_bucket, msg


def _run_transcript_probe(
    scenario: SyntheticScenario,
    *,
    max_turns: int,
    seed: int,
) -> tuple[SyntheticScenario, SyntheticRunResult]:
    """Run a bounded transcript-backed probe with shared real-path wiring."""
    tuned_scenario = replace(scenario, max_turns=max_turns, seed=seed)
    run_result = run_synthetic_session(**tuned_scenario.run_kwargs(use_fake_gm=False))
    _assert_transcript_probe_invariants(run_result, max_turns=max_turns)
    return tuned_scenario, run_result


# Real-path integration probe: this validates transcript-backed wiring only.
# Behavior can vary across content updates, so assertions must stay structural.
@pytest.mark.synthetic
@pytest.mark.slow
@pytest.mark.transcript
def test_synthetic_transcript_probe_cautious_profile_runs_sanely():
    max_turns = 2
    scenario, run_result = _run_transcript_probe(default_opening(), max_turns=max_turns, seed=515)
    _assert_transcript_soft_policy_signal(
        scenario=scenario,
        run_result=run_result,
        slug_bucket=_TRANSCRIPT_SOFT_DEFAULT_SLUGS,
        signal_label="cautious/investigative template slug",
    )


# Real-path integration probe: this is tolerant by design and accepts early exits.
# Keep this resilient to harmless narrative variation in transcript-backed runs.
@pytest.mark.synthetic
@pytest.mark.slow
@pytest.mark.transcript
def test_synthetic_transcript_probe_social_profile_runs_sanely():
    max_turns = 2
    scenario, run_result = _run_transcript_probe(social_opening(), max_turns=max_turns, seed=616)
    _assert_transcript_soft_policy_signal(
        scenario=scenario,
        run_result=run_result,
        slug_bucket=_TRANSCRIPT_SOFT_SOCIAL_SLUGS,
        signal_label="social/question-or-trade template slug",
    )


# Keep transcript coverage selective: include only stable seeded social direction probe.
@pytest.mark.synthetic
@pytest.mark.slow
@pytest.mark.transcript
def test_synthetic_transcript_probe_directed_social_profile_runs_sanely():
    max_turns = 2
    scenario, run_result = _run_transcript_probe(directed_social_opening(), max_turns=max_turns, seed=626)
    bug_class = "directed_social_routing_confusion"
    _assert_transcript_soft_policy_signal(
        scenario=scenario,
        run_result=run_result,
        slug_bucket=_TRANSCRIPT_SOFT_SOCIAL_SLUGS,
        signal_label="directed social follow-up slug",
        bug_class=bug_class,
    )
