"""Short golden replay structural invariant integration coverage.

This file owns short golden replay structural invariant integration coverage.
Replay orchestration helpers remain in tests/helpers/golden_replay.py.
Gate/fallback/sanitizer legality remains with owner suites.
"""

from __future__ import annotations

import pytest

from tests.helpers.golden_replay import (
    assert_protected_golden_turn_observation,
    format_golden_replay_debug,
    protected_social_speaker_observation_expectation,
    protected_structural_expectation,
    run_golden_replay,
)
from tests.helpers.golden_replay_fixtures import (
    gm_response,
    golden_replay_chat_stubs,
    seed_investigator_runner_world,
    seed_runner_continuity_world,
    seed_runner_guard_world,
    seed_scene_object_investigation_world,
    seed_tavern_patrol_lead_world,
)

pytestmark = pytest.mark.golden_replay


def test_golden_replay_directed_npc_question_structural_invariants(tmp_path, monkeypatch):
    captured_prompts: list[list[dict]] = []

    def _fake_call_gpt(messages):
        captured_prompts.append(messages)
        return gm_response('Tavern Runner grimaces. "I heard east-road talk, but no names."')

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="directed_npc_question",
        turns=["Runner, who attacked the patrol?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_investigator_runner_world,
    )

    assert captured_prompts
    assert result["turn_count"] == 1
    turn = result["turns"][0]
    assert turn.get("selected_speaker_id") == "runner"
    assert_protected_golden_turn_observation(
        turn,
        protected_social_speaker_observation_expectation("runner"),
        scenario_id="directed_npc_question",
        debug_context=format_golden_replay_debug(result),
    )


def test_golden_replay_vocative_override_after_prior_continuity_structural_invariants(tmp_path, monkeypatch):
    responses = iter(
        [
            gm_response('Tavern Runner says, "I saw the patrol turn toward the east lanes."'),
            gm_response('Gate Guard says, "I saw fresh mud by the north arch."'),
        ]
    )

    def _fake_call_gpt(_messages):
        return next(responses)

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="vocative_override_after_prior_continuity",
        turns=[
            "Runner, where did the patrol go?",
            "Guard, what did you see?",
        ],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_runner_guard_world,
    )

    assert result["turn_count"] == 2
    turn = result["turns"][1]
    debug_context = format_golden_replay_debug(result)
    assert turn.get("selected_speaker_id") == "guard"
    assert_protected_golden_turn_observation(
        turn,
        protected_social_speaker_observation_expectation("guard"),
        scenario_id="vocative_override_after_prior_continuity",
        debug_context=debug_context,
    )


def test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants(tmp_path, monkeypatch):
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=lambda _messages: gm_response('Merchant says, "I know nothing about that."'),
    )

    result = run_golden_replay(
        scenario_id="wrong_speaker_strict_social_emission",
        turns=["Who attacked the patrol?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_runner_continuity_world,
    )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    debug_context = format_golden_replay_debug(result)
    assert turn.get("selected_speaker_id") == "runner"
    assert_protected_golden_turn_observation(
        turn,
        protected_social_speaker_observation_expectation("runner"),
        scenario_id="wrong_speaker_strict_social_emission",
        debug_context=debug_context,
    )


def test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants(tmp_path, monkeypatch):
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=lambda _messages: gm_response("The scene pauses without offering anything concrete."),
        suppress_exploration=False,
        suppress_intent=False,
    )

    result = run_golden_replay(
        scenario_id="thin_answer_action_outcome_final_emission",
        turns=["I examine the notice board; does it show where the missing patrol went?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_scene_object_investigation_world,
    )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    low = str(turn.get("final_text") or "").lower()
    debug_context = format_golden_replay_debug(result)
    assert_protected_golden_turn_observation(
        turn,
        protected_structural_expectation(
            require_present=("final_text", "final_emitted_source"),
            allow_unavailable=(
                "fallback_family",
                "selected_speaker_id",
                "trace.canonical_entry",
                "trace.social_contract_trace",
            ),
            equals={
                "response_type_required": "action_outcome",
                "response_type_repair_used": True,
            },
            disallow_global_scene_fallback=True,
            no_scaffold=False,
        ),
        scenario_id="thin_answer_action_outcome_final_emission",
        debug_context=debug_context,
    )
    assert "patrol" in low or "east ridge" in low or "notice" in low, debug_context


def test_golden_replay_sanitizer_scaffold_leakage_structural_invariants(tmp_path, monkeypatch):
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=lambda _messages: gm_response(
            "Planner: route via router. Validator: unresolved scaffold."
        ),
    )

    result = run_golden_replay(
        scenario_id="sanitizer_scaffold_leakage",
        turns=["Where should I start?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_scene_object_investigation_world,
    )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    assert "scaffold_leakage" in turn
    assert_protected_golden_turn_observation(
        turn,
        protected_structural_expectation(
            require_present=("final_text", "scaffold_leakage"),
            allow_unavailable=(
                "fallback_family",
                "final_emitted_source",
                "selected_speaker_id",
                "trace.canonical_entry",
                "trace.social_contract_trace",
            ),
            equals={"scaffold_leakage": False},
            no_scaffold=False,
        ),
        scenario_id="sanitizer_scaffold_leakage",
        debug_context=format_golden_replay_debug(result),
    )


def test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants(tmp_path, monkeypatch):
    responses = iter(
        [
            gm_response(
                'Tavern Runner says, "The patrol never came back from the old milestone beyond the east road."'
            ),
            gm_response('Tavern Runner says, "Last reliable sign was the old milestone."'),
        ]
    )

    def _fake_call_gpt(_messages):
        return next(responses)

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="lead_followup_with_dialogue_lock",
        turns=[
            "Tavern Runner, what happened to the patrol?",
            "Runner, where were they last seen?",
        ],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_tavern_patrol_lead_world,
    )

    assert result["turn_count"] == 2
    turn = result["turns"][1]
    debug_context = format_golden_replay_debug(result)
    assert turn.get("selected_speaker_id") == "tavern_runner"
    assert_protected_golden_turn_observation(
        turn,
        protected_social_speaker_observation_expectation("tavern_runner"),
        scenario_id="lead_followup_with_dialogue_lock",
        debug_context=debug_context,
    )
