"""Deterministic synthetic smoke tests built on run_synthetic_session."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
import re

import pytest

from tests.helpers.synthetic_profiles import (
    profile_bold_opportunist,
    profile_cautious_investigator,
    profile_social_prober,
)
from tests.helpers.synthetic_runner import run_synthetic_session
from tests.helpers.synthetic_scenarios import (
    SyntheticScenario,
    advancement_signal_opening,
    alternate_resolution_followup_opening,
    authority_switch_followup_opening,
    clue_followup_opening,
    conditional_affordance_opening,
    default_opening,
    directed_social_opening,
    emergent_npc_opening,
    friction_opening,
    investigation_opening,
    lead_commitment_followthrough_opening,
    magic_anomaly_opening,
    npc_payoff_or_fallback_opening,
    obsolete_lead_pressure_opening,
    retry_pressure_opening,
    scene_transition_followup_opening,
    social_opening,
    social_redirect_followup_opening,
    speaker_grounding_followup_opening,
    who_next_where_followup_opening,
)
from tests.helpers.synthetic_scoring import detect_soft_lock, summarize_synthetic_run
from tests.helpers.synthetic_types import SyntheticRunResult

pytestmark = [pytest.mark.synthetic, pytest.mark.slow]

# Template slugs are stable harness signals from :func:`decide_placeholder` (``profile_id:slug`` rationales).

_SOCIAL_OR_QUESTION_SLUGS = frozenset(
    {"social_direct", "social_probe", "negotiate_trade", "hypothetical_question"},
)
_SOCIAL_CORE_SLUGS = frozenset({"social_direct", "social_probe", "negotiate_trade"})
# Social questioning plus persistence/circle-back (authority/speaker continuity pressure).
_SOCIAL_CONTINUITY_SLUGS = frozenset(
    {
        "social_direct",
        "social_probe",
        "negotiate_trade",
        "hypothetical_question",
        "persistence_followup",
    },
)
_ARCANE_PROBE_SLUGS = frozenset({"arcane_sense"})
_INVESTIGATIVE_SLUGS = frozenset(
    {"cautious_survey", "investigate_inconsistency", "persistence_followup"},
)
_RULES_FRICTION_SLUGS = frozenset({"rules_clarify", "edge_case_press"})
_CAUTIOUS_LEANING_SLUGS = frozenset(
    {"cautious_survey", "investigate_inconsistency", "persistence_followup"},
)
_BOLD_LEANING_SLUGS = frozenset({"bold_push", "negotiate_trade", "hang_back", "hypothetical_question"})
# Forward motion after lead pivots / alternate routes (excludes passive stall signals only).
_LEAD_FORWARD_ACTION_SLUGS = frozenset(
    {
        "cautious_survey",
        "investigate_inconsistency",
        "bold_push",
        "social_direct",
        "social_probe",
        "arcane_sense",
        "rules_clarify",
        "edge_case_press",
        "hypothetical_question",
        "persistence_followup",
        "negotiate_trade",
    },
)
# Post-setup exploration: investigation, survey, magic read, or decisive push (category-level).
_EXPLORATION_ACTION_INVESTIGATION_FORWARD_SLUGS = frozenset(
    {
        "cautious_survey",
        "investigate_inconsistency",
        "bold_push",
        "persistence_followup",
        "arcane_sense",
    },
)
# After an if/then affordance seed, expect branch follow-through (social/trade/persistence).
_CONDITIONAL_AFFORDANCE_PICKUP_SLUGS = _SOCIAL_OR_QUESTION_SLUGS | frozenset({"persistence_followup"})

_TRANSCRIPT_SOFT_DEFAULT_SLUGS = _CAUTIOUS_LEANING_SLUGS
_TRANSCRIPT_SOFT_SOCIAL_SLUGS = _SOCIAL_OR_QUESTION_SLUGS

_KNOWN_STOP_REASONS = {
    "max_turns_reached",
    "stall_repeat_threshold",
    "policy_stop",
    "external_stop",
}

_FOLLOWUP_INTERNAL_LEAK_PATTERNS = (
    r"\brouter\b",
    r"\bplanner\b",
    r"\bvalidator\b",
    r"\bdecision_rationale\b",
    r"\bpolicy\b",
    r"\bsystem prompt\b",
    r"\bdebug_notes?\b",
    r"\bchain[- ]of[- ]thought\b",
)
_FOLLOWUP_SCAFFOLD_LEAK_PATTERNS = (
    r"\bstate exactly what you do\b",
    r"\bstate the specific action\b",
    r"\bresolve that procedurally\b",
    r"\bcannot determine roll requirements\b",
    r"\bbased on (?:what'?s|what is) established\b",
    r"\bas an ai\b",
    r"\bi can't answer\b",
    r"\bi cannot answer\b",
)
_FOLLOWUP_VAGUE_FILLER_PATTERNS = (
    r"\bfor a breath\b",
    r"\bthe scene holds\b",
    r"\bvoices shift around you\b",
    r"\bthese are dangerous times\b",
    r"\btrust is hard to come by\b",
)
_FOLLOWUP_GROUNDED_MARKERS = (
    r"\bscene\b",
    r"\bclue\b",
    r"\bnpc\b",
    r"\bguard\b",
    r"\bwatch\b",
    r"\bpatrol\b",
    r"\bgate\b",
    r"\bcrowd\b",
    r"\bpassage\b",
    r"\bname\b",
    r"\btrail\b",
    r"\bledger\b",
    r"\bsergeant\b",
    r"\bmagistrate\b",
    r"\"",
)


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


def _policy_template_slugs_from_turn_index(
    run_result: SyntheticRunResult,
    *,
    start_turn_index: int,
) -> tuple[str, ...]:
    """Slugs from policy turns at or after ``start_turn_index`` (skips ``provided``)."""
    slugs: list[str] = []
    for view in run_result.turn_views:
        turn_idx = int(view.get("turn_index", 0))
        if turn_idx < start_turn_index:
            continue
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


def _followup_quality_failure_message(
    scenario: SyntheticScenario,
    run_result: SyntheticRunResult,
    *,
    offending_turn_index: int,
    detail: str,
) -> str:
    profile_id = scenario.profile_factory().profile_id
    return (
        f"{detail} | scenario_id={scenario.scenario_id!r} profile_id={profile_id!r} "
        f"seed={run_result.seed} offending_turn_index={offending_turn_index} | "
        f"{summarize_synthetic_run(run_result)}"
    )


def _progression_failure_message(
    scenario: SyntheticScenario,
    run_result: SyntheticRunResult,
    *,
    progression_turn_index: int,
    detail: str,
    bug_class: str | None = None,
) -> str:
    profile_id = scenario.profile_factory().profile_id
    effective_bug_class = bug_class or scenario.regression_risk_class or "unspecified"
    return (
        f"{detail} | bug_class={effective_bug_class!r} "
        f"scenario_id={scenario.scenario_id!r} profile_id={profile_id!r} "
        f"seed={run_result.seed} progression_turn_index={progression_turn_index} | "
        f"{summarize_synthetic_run(run_result)}"
    )


def _extract_player_facing_text(turn_view: dict[str, object]) -> str:
    gm_text = str(turn_view.get("gm_text", "") or "").strip()
    if gm_text:
        return gm_text
    raw = turn_view.get("raw_snapshot")
    if isinstance(raw, dict):
        response = raw.get("response")
        if isinstance(response, dict):
            text = str(response.get("player_facing_text", "") or "").strip()
            if text:
                return text
    return ""


def _normalize_prose_for_repeat_detection(text: str) -> str:
    low = re.sub(r"\s+", " ", text.lower()).strip()
    return re.sub(r"[^\w\s]", "", low).strip()


def _assert_followup_player_facing_quality(
    run_result: SyntheticRunResult,
    scenario: SyntheticScenario,
    *,
    start_turn_index: int = 1,
) -> None:
    # Fake-GM emits minimal deterministic responses.
    # These checks intentionally allow short-form outputs while still guarding:
    # - repetition collapse
    # - internal leakage
    # - filler degradation patterns
    followups = [
        view
        for view in run_result.turn_views
        if int(view.get("turn_index", -1)) >= start_turn_index
    ]
    assert followups, _followup_quality_failure_message(
        scenario,
        run_result,
        offending_turn_index=start_turn_index,
        detail=f"expected at least one follow-up turn at turn_index>={start_turn_index}",
    )

    normalized_followups: list[str] = []
    filler_counts: dict[str, int] = {}
    repeated_streak = 1
    prev_norm = ""
    prev_player = ""
    for view in followups:
        turn_index = int(view.get("turn_index", -1))
        gm_text = _extract_player_facing_text(view)
        low = gm_text.lower()
        player_text = str(view.get("player_text", "") or "").strip()

        assert gm_text, _followup_quality_failure_message(
            scenario,
            run_result,
            offending_turn_index=turn_index,
            detail="empty player-facing follow-up text",
        )
        # Short outputs are acceptable in fake-GM mode, but they must still be valid prose-ish text.
        assert re.search(r"[a-z0-9]", low), _followup_quality_failure_message(
            scenario,
            run_result,
            offending_turn_index=turn_index,
            detail=f"follow-up response is not syntactically valid text: {gm_text!r}",
        )

        for pattern in _FOLLOWUP_INTERNAL_LEAK_PATTERNS:
            assert not re.search(pattern, low), _followup_quality_failure_message(
                scenario,
                run_result,
                offending_turn_index=turn_index,
                detail=f"internal role leakage in player-facing text: pattern={pattern!r}",
            )
        for pattern in _FOLLOWUP_SCAFFOLD_LEAK_PATTERNS:
            assert not re.search(pattern, low), _followup_quality_failure_message(
                scenario,
                run_result,
                offending_turn_index=turn_index,
                detail=f"scaffold/instruction leakage in player-facing text: pattern={pattern!r}",
            )
        filler_hits = tuple(pattern for pattern in _FOLLOWUP_VAGUE_FILLER_PATTERNS if re.search(pattern, low))
        # Pure filler should fail immediately; incidental phrasing is tolerated unless it repeats.
        if filler_hits and len(gm_text.split()) <= 8:
            assert False, _followup_quality_failure_message(
                scenario,
                run_result,
                offending_turn_index=turn_index,
                detail=f"follow-up response appears to be pure filler: {gm_text!r}",
            )
        for pattern in filler_hits:
            filler_counts[pattern] = filler_counts.get(pattern, 0) + 1
            assert filler_counts[pattern] <= 1, _followup_quality_failure_message(
                scenario,
                run_result,
                offending_turn_index=turn_index,
                detail=f"repeated filler phrase detected under follow-up pressure: pattern={pattern!r}",
            )

        current_norm = _normalize_prose_for_repeat_detection(gm_text)
        if current_norm:
            normalized_followups.append(current_norm)
        if current_norm and current_norm == prev_norm:
            repeated_streak += 1
        else:
            repeated_streak = 1
        assert repeated_streak <= 2, _followup_quality_failure_message(
            scenario,
            run_result,
            offending_turn_index=turn_index,
            detail="follow-up prose collapsed into repeated normalized output across turns",
        )

        if prev_norm and current_norm == prev_norm and player_text and prev_player and player_text != prev_player:
            assert False, _followup_quality_failure_message(
                scenario,
                run_result,
                offending_turn_index=turn_index,
                detail=(
                    "follow-up response is not contextually coherent with prior turn: "
                    "identical output despite changed player input"
                ),
            )
        prev_norm = current_norm
        prev_player = player_text

    if normalized_followups and len(set(normalized_followups)) == 1 and len(normalized_followups) >= 2:
        last_turn_index = int(followups[-1].get("turn_index", start_turn_index))
        assert False, _followup_quality_failure_message(
            scenario,
            run_result,
            offending_turn_index=last_turn_index,
            detail="follow-up prose collapsed into a single repeated normalized output across turns",
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


def _assert_slug_bucket_hit_from_turn(
    run_result: SyntheticRunResult,
    scenario: SyntheticScenario,
    bucket: frozenset[str],
    *,
    start_turn_index: int,
    label: str,
    bug_class: str | None = None,
) -> None:
    slugs = frozenset(
        _policy_template_slugs_from_turn_index(run_result, start_turn_index=start_turn_index),
    )
    detail = (
        f"missing {label} for policy turns at turn_index>={start_turn_index}; "
        f"expected_any_of={sorted(bucket)!r} got_slugs={sorted(slugs)!r}"
    )
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


def _distinct_policy_slug_count_from_turn(
    run_result: SyntheticRunResult,
    *,
    start_turn_index: int,
) -> int:
    """Count distinct template slugs on policy turns from ``start_turn_index`` onward."""
    return len(
        frozenset(
            _policy_template_slugs_from_turn_index(
                run_result,
                start_turn_index=start_turn_index,
            ),
        ),
    )


def _assert_seeded_opener_then_slug_bucket_from_turn(
    run_result: SyntheticRunResult,
    scenario: SyntheticScenario,
    bucket: frozenset[str],
    *,
    start_turn_index: int = 1,
    label: str,
    bug_class: str | None = None,
) -> None:
    """Rich-path helper: explicit seeded opener + policy slug bucket from later turns."""
    _assert_seeded_first_turn_used(run_result, scenario, bug_class=bug_class)
    _assert_slug_bucket_hit_from_turn(
        run_result,
        scenario,
        bucket,
        start_turn_index=start_turn_index,
        label=label,
        bug_class=bug_class,
    )


def _policy_turn_views_from(
    run_result: SyntheticRunResult,
    *,
    start_turn_index: int,
) -> list[dict[str, object]]:
    """Policy (non-``provided``) turn views at or after ``start_turn_index``, sorted by turn."""
    views = [
        v
        for v in run_result.turn_views
        if int(v.get("turn_index", -1)) >= start_turn_index
        and str(v.get("decision_rationale", "")).strip() != "provided"
    ]
    return sorted(views, key=lambda v: int(v.get("turn_index", 0)))


def _assert_no_progression_stall_repeated_player_intent(
    run_result: SyntheticRunResult,
    scenario: SyntheticScenario,
    *,
    start_turn_index: int = 1,
    bug_class: str | None = None,
) -> None:
    """Fail when consecutive policy turns repeat the same normalized player intent (stall signal)."""
    views = _policy_turn_views_from(run_result, start_turn_index=start_turn_index)
    prev_fp: str | None = None
    prev_turn = start_turn_index
    for view in views:
        turn_index = int(view.get("turn_index", -1))
        player_text = str(view.get("player_text", "") or "").strip()
        fp = _normalize_prose_for_repeat_detection(player_text)
        if fp and prev_fp is not None and fp == prev_fp:
            assert False, _progression_failure_message(
                scenario,
                run_result,
                progression_turn_index=turn_index,
                detail=(
                    "progression stall: repeated player intent fingerprint on consecutive policy turns "
                    f"(matches turn_index={prev_turn})"
                ),
                bug_class=bug_class,
            )
        if fp:
            prev_fp = fp
            prev_turn = turn_index


def _assert_forward_slug_within_turns_after_opener(
    run_result: SyntheticRunResult,
    scenario: SyntheticScenario,
    forward_bucket: frozenset[str],
    *,
    within_turn_index_inclusive: int,
    label: str,
    bug_class: str | None = None,
) -> None:
    """At least one policy slug from ``forward_bucket`` on some turn in ``1..N`` (inclusive)."""
    for view in run_result.turn_views:
        turn_index = int(view.get("turn_index", -1))
        if turn_index < 1 or turn_index > within_turn_index_inclusive:
            continue
        rationale = str(view.get("decision_rationale", "")).strip()
        if rationale == "provided" or ":" not in rationale:
            continue
        slug = rationale.split(":", 1)[1].strip()
        if slug in forward_bucket:
            return
    max_turn = max((int(v.get("turn_index", 0)) for v in run_result.turn_views), default=0)
    fail_turn = min(within_turn_index_inclusive, max_turn)
    assert False, _progression_failure_message(
        scenario,
        run_result,
        progression_turn_index=fail_turn,
        detail=(
            f"no forward-moving template slug within turns 1..{within_turn_index_inclusive} ({label}); "
            f"expected_any_of={sorted(forward_bucket)!r}"
        ),
        bug_class=bug_class,
    )


def _assert_distinct_policy_player_intent_after_opener(
    run_result: SyntheticRunResult,
    scenario: SyntheticScenario,
    *,
    min_distinct: int,
    start_turn_index: int = 1,
    bug_class: str | None = None,
) -> None:
    """Policy player lines after setup should not collapse to a single repeated intent category."""
    views = _policy_turn_views_from(run_result, start_turn_index=start_turn_index)
    fingerprints = [
        _normalize_prose_for_repeat_detection(str(v.get("player_text", "") or "").strip())
        for v in views
    ]
    distinct = len({f for f in fingerprints if f})
    last_turn = int(views[-1].get("turn_index", start_turn_index)) if views else start_turn_index
    assert distinct >= min_distinct, _progression_failure_message(
        scenario,
        run_result,
        progression_turn_index=last_turn,
        detail=(
            f"player policy intents did not diversify enough for progression "
            f"(distinct_normalized={distinct}, min_required={min_distinct})"
        ),
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
        pytest.param(social_redirect_followup_opening, id="social-redirect-followup-opening"),
        pytest.param(who_next_where_followup_opening, id="who-next-where-followup-opening"),
        pytest.param(authority_switch_followup_opening, id="authority-switch-followup-opening"),
        pytest.param(speaker_grounding_followup_opening, id="speaker-grounding-followup-opening"),
        pytest.param(lead_commitment_followthrough_opening, id="lead-commitment-followthrough-opening"),
        pytest.param(npc_payoff_or_fallback_opening, id="npc-payoff-or-fallback-opening"),
        pytest.param(obsolete_lead_pressure_opening, id="obsolete-lead-pressure-opening"),
        pytest.param(alternate_resolution_followup_opening, id="alternate-resolution-followup-opening"),
        pytest.param(advancement_signal_opening, id="advancement-signal-opening"),
        pytest.param(conditional_affordance_opening, id="conditional-affordance-opening"),
        pytest.param(scene_transition_followup_opening, id="scene-transition-followup-opening"),
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


def test_fake_gm_profile_expectation_social_redirect_followup_stays_social() -> None:
    scenario = replace(social_redirect_followup_opening(), seed=1181)
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario)
    _assert_slug_bucket_hit_from_turn(
        run_result,
        scenario,
        _SOCIAL_OR_QUESTION_SLUGS,
        start_turn_index=1,
        label="post-redirect social/question follow-up template slug",
    )


def test_fake_gm_profile_expectation_who_next_where_followup_stays_target_social() -> None:
    scenario = replace(who_next_where_followup_opening(), seed=1182)
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario)
    _assert_slug_bucket_hit_from_turn(
        run_result,
        scenario,
        _SOCIAL_OR_QUESTION_SLUGS,
        start_turn_index=1,
        label="post who/where opener social/question follow-up slug",
    )


def test_fake_gm_profile_expectation_authority_switch_retains_social_continuity() -> None:
    scenario = replace(authority_switch_followup_opening(), seed=1183)
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario)
    _assert_slug_bucket_hit_from_turn(
        run_result,
        scenario,
        _SOCIAL_CONTINUITY_SLUGS,
        start_turn_index=1,
        label="post authority-switch social or persistence continuity slug",
    )


def test_fake_gm_profile_expectation_speaker_grounding_retains_social_continuity() -> None:
    scenario = replace(speaker_grounding_followup_opening(), seed=1184)
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario)
    _assert_slug_bucket_hit_from_turn(
        run_result,
        scenario,
        _SOCIAL_CONTINUITY_SLUGS,
        start_turn_index=1,
        label="post speaker-grounding social or persistence continuity slug",
    )


def test_fake_gm_profile_expectation_lead_commitment_followthrough_opening() -> None:
    scenario = lead_commitment_followthrough_opening()
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_opener_then_slug_bucket_from_turn(
        run_result,
        scenario,
        _INVESTIGATIVE_SLUGS,
        label="post-opener investigative follow-through after lead commitment seed",
    )


def test_fake_gm_profile_expectation_npc_payoff_or_fallback_opening() -> None:
    scenario = npc_payoff_or_fallback_opening()
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_opener_then_slug_bucket_from_turn(
        run_result,
        scenario,
        _SOCIAL_OR_QUESTION_SLUGS,
        start_turn_index=1,
        label="post-opener social/question pressure after NPC payoff/fallback seed",
    )
    distinct = _distinct_policy_slug_count_from_turn(run_result, start_turn_index=1)
    assert distinct >= 2, _fake_gm_profile_expectation_message(
        scenario,
        run_result,
        detail=f"expected>=2 distinct policy slugs after opener (avoid single-template collapse); "
        f"distinct_from_turn_1={distinct}",
    )


def test_fake_gm_profile_expectation_obsolete_lead_pressure_opening() -> None:
    scenario = obsolete_lead_pressure_opening()
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_opener_then_slug_bucket_from_turn(
        run_result,
        scenario,
        _LEAD_FORWARD_ACTION_SLUGS,
        start_turn_index=1,
        label="post-opener forward action after obsolete-lead pivot seed",
    )


def test_fake_gm_profile_expectation_alternate_resolution_followup_opening() -> None:
    scenario = alternate_resolution_followup_opening()
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_opener_then_slug_bucket_from_turn(
        run_result,
        scenario,
        _LEAD_FORWARD_ACTION_SLUGS,
        start_turn_index=1,
        label="post-opener forward action after alternate-resolution seed",
    )


def test_fake_gm_progression_advancement_signal_opening() -> None:
    scenario = advancement_signal_opening()
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_opener_then_slug_bucket_from_turn(
        run_result,
        scenario,
        _EXPLORATION_ACTION_INVESTIGATION_FORWARD_SLUGS,
        start_turn_index=1,
        label="post-opener investigation/action-forward slug after advancement signal seed",
    )
    _assert_forward_slug_within_turns_after_opener(
        run_result,
        scenario,
        _EXPLORATION_ACTION_INVESTIGATION_FORWARD_SLUGS,
        within_turn_index_inclusive=2,
        label="early-turn investigation/action-forward slug",
    )
    _assert_no_progression_stall_repeated_player_intent(run_result, scenario, start_turn_index=1)
    _assert_distinct_policy_player_intent_after_opener(
        run_result,
        scenario,
        min_distinct=2,
        start_turn_index=1,
    )


def test_fake_gm_progression_conditional_affordance_opening() -> None:
    scenario = conditional_affordance_opening()
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_opener_then_slug_bucket_from_turn(
        run_result,
        scenario,
        _CONDITIONAL_AFFORDANCE_PICKUP_SLUGS,
        start_turn_index=1,
        label="post-opener affordance follow-through slug (social/trade/persistence)",
    )
    _assert_forward_slug_within_turns_after_opener(
        run_result,
        scenario,
        _CONDITIONAL_AFFORDANCE_PICKUP_SLUGS,
        within_turn_index_inclusive=2,
        label="early-turn affordance pickup slug",
    )
    _assert_no_progression_stall_repeated_player_intent(run_result, scenario, start_turn_index=1)
    _assert_distinct_policy_player_intent_after_opener(
        run_result,
        scenario,
        min_distinct=2,
        start_turn_index=1,
    )


def test_fake_gm_progression_scene_transition_followup_opening() -> None:
    scenario = scene_transition_followup_opening()
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_opener_then_slug_bucket_from_turn(
        run_result,
        scenario,
        _EXPLORATION_ACTION_INVESTIGATION_FORWARD_SLUGS,
        start_turn_index=1,
        label="post-opener survey/investigate/push after scene transition seed",
    )
    _assert_forward_slug_within_turns_after_opener(
        run_result,
        scenario,
        _EXPLORATION_ACTION_INVESTIGATION_FORWARD_SLUGS,
        within_turn_index_inclusive=2,
        label="early-turn forward exploration slug after transition",
    )
    _assert_no_progression_stall_repeated_player_intent(run_result, scenario, start_turn_index=1)
    _assert_distinct_policy_player_intent_after_opener(
        run_result,
        scenario,
        min_distinct=2,
        start_turn_index=1,
    )


@pytest.mark.parametrize(
    "scenario_factory,seed",
    (
        pytest.param(social_redirect_followup_opening, 2181, id="social-redirect-followup-opening"),
        pytest.param(authority_switch_followup_opening, 2183, id="authority-switch-followup-opening"),
        pytest.param(speaker_grounding_followup_opening, 2184, id="speaker-grounding-followup-opening"),
        pytest.param(lead_commitment_followthrough_opening, 2171, id="lead-commitment-followthrough-opening"),
        pytest.param(npc_payoff_or_fallback_opening, 2172, id="npc-payoff-or-fallback-opening"),
    ),
)
def test_fake_gm_followup_output_quality_pressure_checks(
    scenario_factory: Callable[[], SyntheticScenario],
    seed: int,
) -> None:
    scenario = replace(scenario_factory(), seed=seed)
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario)
    _assert_followup_player_facing_quality(run_result, scenario, start_turn_index=1)


def test_fake_gm_contrast_social_redirect_social_prober_vs_cautious_investigator_diverge() -> None:
    seed = 12001
    social_scenario = replace(social_redirect_followup_opening(), seed=seed)
    cautious_scenario = replace(
        social_redirect_followup_opening(),
        seed=seed,
        profile_factory=profile_cautious_investigator,
    )
    social_run = run_synthetic_session(**social_scenario.run_kwargs(use_fake_gm=True))
    cautious_run = run_synthetic_session(**cautious_scenario.run_kwargs(use_fake_gm=True))

    for run_result, scenario in (
        (social_run, social_scenario),
        (cautious_run, cautious_scenario),
    ):
        _assert_compact_smoke_invariants(run_result)
        _assert_seeded_first_turn_used(run_result, scenario)

    social_slugs = _policy_template_slugs(social_run)
    cautious_slugs = _policy_template_slugs(cautious_run)
    assert social_slugs != cautious_slugs, _fake_gm_profile_expectation_message(
        cautious_scenario,
        cautious_run,
        detail=f"expected differing slug sequences on same redirect seed; social={social_slugs!r} "
        f"cautious={cautious_slugs!r}",
        bug_class="social_redirect_profile_contrast",
    )

    _assert_slug_bucket_hit_from_turn(
        social_run,
        social_scenario,
        _SOCIAL_OR_QUESTION_SLUGS,
        start_turn_index=1,
        label="social prober post-redirect follow-up slug",
        bug_class="social_redirect_profile_contrast",
    )
    cautious_follow = frozenset(
        _policy_template_slugs_from_turn_index(cautious_run, start_turn_index=1),
    )
    assert cautious_follow & _CAUTIOUS_LEANING_SLUGS, _fake_gm_profile_expectation_message(
        cautious_scenario,
        cautious_run,
        detail=(
            f"expected cautious-leaning follow-up after redirect; "
            f"expected_any_of={sorted(_CAUTIOUS_LEANING_SLUGS)!r} got_slugs={sorted(cautious_follow)!r}"
        ),
        bug_class="social_redirect_profile_contrast",
    )


def test_fake_gm_contrast_directed_social_vs_authority_switch_opening_diverge() -> None:
    # Same profile + nearby seeds can yield identical policy slug streams once the first policy
    # pick matches; offset authority seed so we still compare two distinct social openers while
    # observing divergent follow-up slugs.
    directed_seed = 13000
    authority_seed = 13063
    directed = replace(directed_social_opening(), seed=directed_seed)
    authority = replace(authority_switch_followup_opening(), seed=authority_seed)
    directed_run = run_synthetic_session(**directed.run_kwargs(use_fake_gm=True))
    authority_run = run_synthetic_session(**authority.run_kwargs(use_fake_gm=True))

    for run_result, scenario in ((directed_run, directed), (authority_run, authority)):
        _assert_compact_smoke_invariants(run_result)
        _assert_seeded_first_turn_used(run_result, scenario)
        _assert_slug_bucket_hit_from_turn(
            run_result,
            scenario,
            _SOCIAL_OR_QUESTION_SLUGS,
            start_turn_index=1,
            label="social follow-up after seeded opener",
            bug_class="directed_vs_authority_switch_contrast",
        )

    assert _policy_template_slugs(directed_run) != _policy_template_slugs(authority_run), (
        _fake_gm_profile_expectation_message(
            authority,
            authority_run,
            detail=(
                "expected differing full-run slug sequences for directed-social vs authority-switch "
                f"openers; directed={_policy_template_slugs(directed_run)!r} "
                f"authority={_policy_template_slugs(authority_run)!r}"
            ),
            bug_class="directed_vs_authority_switch_contrast",
        )
    )


def test_fake_gm_contrast_obsolete_lead_cautious_investigator_vs_bold_opportunist() -> None:
    seed = 6022
    cautious_scenario = replace(obsolete_lead_pressure_opening(), seed=seed)
    bold_scenario = replace(
        obsolete_lead_pressure_opening(),
        seed=seed,
        profile_factory=profile_bold_opportunist,
    )
    cautious_run = run_synthetic_session(**cautious_scenario.run_kwargs(use_fake_gm=True))
    bold_run = run_synthetic_session(**bold_scenario.run_kwargs(use_fake_gm=True))

    for run_result, scenario in (
        (cautious_run, cautious_scenario),
        (bold_run, bold_scenario),
    ):
        _assert_compact_smoke_invariants(run_result)
        _assert_seeded_first_turn_used(run_result, scenario, bug_class="lead_obsolete_profile_contrast")

    cautious_slugs = _policy_template_slugs(cautious_run)
    bold_slugs = _policy_template_slugs(bold_run)
    assert cautious_slugs != bold_slugs, _fake_gm_profile_expectation_message(
        bold_scenario,
        bold_run,
        detail=f"expected differing slug sequences on same obsolete-lead seed; "
        f"cautious={cautious_slugs!r} bold={bold_slugs!r}",
        bug_class="lead_obsolete_profile_contrast",
    )

    cautious_follow = frozenset(
        _policy_template_slugs_from_turn_index(cautious_run, start_turn_index=1),
    )
    bold_follow = frozenset(_policy_template_slugs_from_turn_index(bold_run, start_turn_index=1))
    assert cautious_follow & _CAUTIOUS_LEANING_SLUGS, _fake_gm_profile_expectation_message(
        cautious_scenario,
        cautious_run,
        detail=(
            f"expected cautious-leaning post-opener slugs; "
            f"expected_any_of={sorted(_CAUTIOUS_LEANING_SLUGS)!r} got_slugs={sorted(cautious_follow)!r}"
        ),
        bug_class="lead_obsolete_profile_contrast",
    )
    assert bold_follow & _BOLD_LEANING_SLUGS, _fake_gm_profile_expectation_message(
        bold_scenario,
        bold_run,
        detail=(
            f"expected bold-leaning post-opener slugs; "
            f"expected_any_of={sorted(_BOLD_LEANING_SLUGS)!r} got_slugs={sorted(bold_follow)!r}"
        ),
        bug_class="lead_obsolete_profile_contrast",
    )


def test_fake_gm_contrast_npc_payoff_cautious_investigator_vs_social_prober() -> None:
    seed = 6021
    social_scenario = replace(npc_payoff_or_fallback_opening(), seed=seed)
    cautious_scenario = replace(
        npc_payoff_or_fallback_opening(),
        seed=seed,
        profile_factory=profile_cautious_investigator,
    )
    social_run = run_synthetic_session(**social_scenario.run_kwargs(use_fake_gm=True))
    cautious_run = run_synthetic_session(**cautious_scenario.run_kwargs(use_fake_gm=True))

    for run_result, scenario in (
        (social_run, social_scenario),
        (cautious_run, cautious_scenario),
    ):
        _assert_compact_smoke_invariants(run_result)
        _assert_seeded_first_turn_used(run_result, scenario, bug_class="lead_npc_payoff_profile_contrast")

    social_slugs = _policy_template_slugs(social_run)
    cautious_slugs = _policy_template_slugs(cautious_run)
    assert social_slugs != cautious_slugs, _fake_gm_profile_expectation_message(
        cautious_scenario,
        cautious_run,
        detail=f"expected differing slug sequences on same NPC payoff seed; "
        f"social={social_slugs!r} cautious={cautious_slugs!r}",
        bug_class="lead_npc_payoff_profile_contrast",
    )

    _assert_slug_bucket_hit_from_turn(
        social_run,
        social_scenario,
        _SOCIAL_OR_QUESTION_SLUGS,
        start_turn_index=1,
        label="social prober post-opener social/question slug",
        bug_class="lead_npc_payoff_profile_contrast",
    )
    cautious_follow = frozenset(
        _policy_template_slugs_from_turn_index(cautious_run, start_turn_index=1),
    )
    assert cautious_follow & _CAUTIOUS_LEANING_SLUGS, _fake_gm_profile_expectation_message(
        cautious_scenario,
        cautious_run,
        detail=(
            f"expected cautious-leaning post-opener slugs on NPC-mediated lead; "
            f"expected_any_of={sorted(_CAUTIOUS_LEANING_SLUGS)!r} got_slugs={sorted(cautious_follow)!r}"
        ),
        bug_class="lead_npc_payoff_profile_contrast",
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


def test_fake_gm_regression_social_destination_redirect_followup_guard() -> None:
    scenario = replace(social_redirect_followup_opening(), seed=1961)
    bug_class = "social_destination_redirect_followup"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario, bug_class=bug_class)
    _assert_slug_bucket_hit_from_turn(
        run_result,
        scenario,
        _SOCIAL_OR_QUESTION_SLUGS,
        start_turn_index=1,
        label="redirect follow-up stays socially grounded",
        bug_class=bug_class,
    )


def test_fake_gm_regression_social_target_location_followup_guard() -> None:
    scenario = replace(who_next_where_followup_opening(), seed=1962)
    bug_class = "social_target_location_followup"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario, bug_class=bug_class)
    _assert_slug_bucket_hit_from_turn(
        run_result,
        scenario,
        _SOCIAL_OR_QUESTION_SLUGS,
        start_turn_index=1,
        label="who/where opener keeps target-aware social follow-up",
        bug_class=bug_class,
    )


def test_fake_gm_regression_social_authority_switch_continuity_guard() -> None:
    scenario = replace(authority_switch_followup_opening(), seed=1963)
    bug_class = "social_authority_switch_continuity"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario, bug_class=bug_class)
    _assert_slug_bucket_hit_from_turn(
        run_result,
        scenario,
        _SOCIAL_CONTINUITY_SLUGS,
        start_turn_index=1,
        label="authority switch retains social/persistence continuity",
        bug_class=bug_class,
    )


def test_fake_gm_regression_social_speaker_grounding_followup_guard() -> None:
    scenario = replace(speaker_grounding_followup_opening(), seed=1964)
    bug_class = "social_speaker_grounding_followup"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_first_turn_used(run_result, scenario, bug_class=bug_class)
    _assert_slug_bucket_hit_from_turn(
        run_result,
        scenario,
        _SOCIAL_CONTINUITY_SLUGS,
        start_turn_index=1,
        label="speaker grounding retains social/persistence continuity",
        bug_class=bug_class,
    )


def test_fake_gm_regression_lead_commitment_followthrough_stall_guard() -> None:
    scenario = replace(lead_commitment_followthrough_opening(), seed=1971)
    bug_class = "lead_commitment_followthrough_stall"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_opener_then_slug_bucket_from_turn(
        run_result,
        scenario,
        _INVESTIGATIVE_SLUGS,
        label="lead commitment retains investigative follow-through",
        bug_class=bug_class,
    )


def test_fake_gm_regression_lead_npc_payoff_or_fallback_continuity_guard() -> None:
    scenario = replace(npc_payoff_or_fallback_opening(), seed=1972)
    bug_class = "lead_npc_payoff_or_fallback_continuity"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_opener_then_slug_bucket_from_turn(
        run_result,
        scenario,
        _SOCIAL_OR_QUESTION_SLUGS,
        label="NPC payoff/fallback fork keeps social/question follow-up",
        bug_class=bug_class,
    )
    distinct = _distinct_policy_slug_count_from_turn(run_result, start_turn_index=1)
    assert distinct >= 2, _fake_gm_profile_expectation_message(
        scenario,
        run_result,
        detail=f"expected>=2 distinct post-opener slugs; distinct_from_turn_1={distinct}",
        bug_class=bug_class,
    )


def test_fake_gm_regression_lead_obsolescence_pivot_pressure_guard() -> None:
    scenario = replace(obsolete_lead_pressure_opening(), seed=1973)
    bug_class = "lead_obsolescence_pivot_pressure"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_opener_then_slug_bucket_from_turn(
        run_result,
        scenario,
        _LEAD_FORWARD_ACTION_SLUGS,
        label="obsolete-lead pivot keeps forward template pressure",
        bug_class=bug_class,
    )


def test_fake_gm_regression_lead_alternate_route_continuity_guard() -> None:
    scenario = replace(alternate_resolution_followup_opening(), seed=1974)
    bug_class = "lead_alternate_route_continuity"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_opener_then_slug_bucket_from_turn(
        run_result,
        scenario,
        _LEAD_FORWARD_ACTION_SLUGS,
        label="alternate route retains forward template pressure",
        bug_class=bug_class,
    )


def test_fake_gm_regression_exploration_advancement_signal_stall_guard() -> None:
    scenario = replace(advancement_signal_opening(), seed=1981)
    bug_class = "exploration_advancement_signal_stall"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_opener_then_slug_bucket_from_turn(
        run_result,
        scenario,
        _EXPLORATION_ACTION_INVESTIGATION_FORWARD_SLUGS,
        start_turn_index=1,
        label="advancement signal retains investigation/action-forward pressure",
        bug_class=bug_class,
    )
    _assert_forward_slug_within_turns_after_opener(
        run_result,
        scenario,
        _EXPLORATION_ACTION_INVESTIGATION_FORWARD_SLUGS,
        within_turn_index_inclusive=2,
        label="early investigation/action-forward slug",
        bug_class=bug_class,
    )
    _assert_no_progression_stall_repeated_player_intent(
        run_result,
        scenario,
        start_turn_index=1,
        bug_class=bug_class,
    )


def test_fake_gm_regression_exploration_conditional_affordance_drop_guard() -> None:
    scenario = replace(conditional_affordance_opening(), seed=1982)
    bug_class = "exploration_conditional_affordance_drop"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_opener_then_slug_bucket_from_turn(
        run_result,
        scenario,
        _CONDITIONAL_AFFORDANCE_PICKUP_SLUGS,
        start_turn_index=1,
        label="conditional affordance seed keeps branch follow-through slugs",
        bug_class=bug_class,
    )
    _assert_forward_slug_within_turns_after_opener(
        run_result,
        scenario,
        _CONDITIONAL_AFFORDANCE_PICKUP_SLUGS,
        within_turn_index_inclusive=2,
        label="early affordance pickup slug",
        bug_class=bug_class,
    )


def test_fake_gm_regression_exploration_scene_transition_followup_stall_guard() -> None:
    scenario = replace(scene_transition_followup_opening(), seed=1983)
    bug_class = "exploration_scene_transition_followup_stall"
    run_result = run_synthetic_session(**scenario.run_kwargs(use_fake_gm=True))
    _assert_compact_smoke_invariants(run_result)
    _assert_seeded_opener_then_slug_bucket_from_turn(
        run_result,
        scenario,
        _EXPLORATION_ACTION_INVESTIGATION_FORWARD_SLUGS,
        start_turn_index=1,
        label="scene transition retains forward exploration slugs",
        bug_class=bug_class,
    )
    _assert_forward_slug_within_turns_after_opener(
        run_result,
        scenario,
        _EXPLORATION_ACTION_INVESTIGATION_FORWARD_SLUGS,
        within_turn_index_inclusive=2,
        label="early forward exploration after transition",
        bug_class=bug_class,
    )
    _assert_no_progression_stall_repeated_player_intent(
        run_result,
        scenario,
        start_turn_index=1,
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


@pytest.mark.synthetic
@pytest.mark.slow
@pytest.mark.transcript
def test_synthetic_transcript_probe_who_next_where_opener_runs_sanely():
    """Single soft structural check: who/where social seed still yields a social-leaning policy slug."""
    max_turns = 2
    scenario, run_result = _run_transcript_probe(
        who_next_where_followup_opening(),
        max_turns=max_turns,
        seed=636,
    )
    bug_class = "social_target_location_followup"
    _assert_transcript_soft_policy_signal(
        scenario=scenario,
        run_result=run_result,
        slug_bucket=_TRANSCRIPT_SOFT_SOCIAL_SLUGS,
        signal_label="who/where seeded social follow-up slug",
        bug_class=bug_class,
    )


@pytest.mark.synthetic
@pytest.mark.slow
@pytest.mark.transcript
def test_synthetic_transcript_probe_lead_commitment_followthrough_runs_sanely() -> None:
    """Soft structural check: committed lead seed still yields cautious/investigative policy signal."""
    max_turns = 2
    scenario, run_result = _run_transcript_probe(
        lead_commitment_followthrough_opening(),
        max_turns=max_turns,
        seed=646,
    )
    bug_class = "lead_commitment_followthrough_stall"
    _assert_transcript_soft_policy_signal(
        scenario=scenario,
        run_result=run_result,
        slug_bucket=_TRANSCRIPT_SOFT_DEFAULT_SLUGS,
        signal_label="lead-commitment seeded investigative follow-up slug",
        bug_class=bug_class,
    )


@pytest.mark.synthetic
@pytest.mark.slow
@pytest.mark.transcript
def test_synthetic_transcript_probe_scene_transition_followup_runs_sanely() -> None:
    """Structural check only: spatial transition seed still yields exploration-forward policy slugs."""
    max_turns = 2
    scenario, run_result = _run_transcript_probe(
        scene_transition_followup_opening(),
        max_turns=max_turns,
        seed=656,
    )
    bug_class = "exploration_scene_transition_followup_stall"
    _assert_transcript_soft_policy_signal(
        scenario=scenario,
        run_result=run_result,
        slug_bucket=_EXPLORATION_ACTION_INVESTIGATION_FORWARD_SLUGS,
        signal_label="scene-transition seeded exploration-forward slug",
        bug_class=bug_class,
    )
