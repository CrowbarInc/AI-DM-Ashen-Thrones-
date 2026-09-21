from __future__ import annotations

from typing import Any

import pytest

from game.playability_eval import evaluate_playability
from tests.helpers.reactive_player import (
    ReactivePlayerConfig,
    ReactivePlayerState,
    ReactiveScenario,
    decide_reactive_action,
)
from tools.run_reactive_player_validation import campaign_summary, run_reactive_scenario


SCENARIO = ReactiveScenario(
    scenario_id="test_watch",
    objective="Identify the watch commander.",
    initial_action="Who commands the watch here?",
    narrower_follow_up="Who specifically commands the watch?",
    rephrased_follow_up="Name the watch commander or give the rank.",
    contradiction_probe="You named two officers. Which one commands?",
    established_fact_probe="You established that Captain Vara is present. Does she command?",
    knowledge_boundary_probe="Would this witness actually know the roster?",
    return_to_topic_probe="Return to the unresolved command question.",
    degradation_probe="Again, plainly: who commands the watch?",
    max_turns=5,
    max_attempts_per_intent=2,
)


def _evaluation(player: str, gm: str) -> dict[str, Any]:
    return evaluate_playability({"player_prompt": player, "gm_text": gm})


def _config(strategy: str = "reactive", seed: int = 17) -> ReactivePlayerConfig:
    return ReactivePlayerConfig(strategy, seed, 5, 2)


def test_reactive_follow_up_selected_after_non_answer() -> None:
    state = ReactivePlayerState(current_intent=SCENARIO.objective)
    ev = _evaluation(SCENARIO.initial_action, "Rain beads on the gate while guards cross the yard.")

    decision = decide_reactive_action(
        scenario=SCENARIO,
        config=_config(),
        state=state,
        turn_index=1,
        prior_gm_text="Rain beads on the gate while guards cross the yard.",
        prior_evaluation=ev,
    )

    assert decision.player_text == SCENARIO.narrower_follow_up
    assert decision.rationale == "incomplete_or_vague_answer:demand_specificity"


def test_bounded_persistence_stops_after_attempt_limit() -> None:
    state = ReactivePlayerState(current_intent=SCENARIO.objective, attempts_on_intent=2)
    ev = _evaluation(SCENARIO.initial_action, "Rain beads on the gate while guards cross the yard.")

    decision = decide_reactive_action(
        scenario=SCENARIO,
        config=_config(),
        state=state,
        turn_index=3,
        prior_gm_text="Rain beads on the gate while guards cross the yard.",
        prior_evaluation=ev,
    )

    assert decision.stop_requested is True
    assert decision.stop_reason == "max_intent_attempts"


@pytest.mark.parametrize(
    "gm",
    (
        "Tavern Runner says, 'I don't know who commands them. Ask the gate serjeant.'",
        'Tavern Runner says, "No. I cannot answer that from what I know."',
        "Tavern Runner refuses to name the officer and turns back to the stewpot.",
        "Tavern Runner says, 'I don't know; the roster changed after dusk.'",
    ),
)
def test_legitimate_boundary_is_accepted(gm: str) -> None:
    state = ReactivePlayerState(current_intent=SCENARIO.objective)
    ev = _evaluation(SCENARIO.initial_action, gm)
    decision = decide_reactive_action(
        scenario=SCENARIO,
        config=_config("adversarial"),
        state=state,
        turn_index=1,
        prior_gm_text=gm,
        prior_evaluation=ev,
    )

    assert decision.stop_requested is True
    assert decision.stop_reason == "legitimate_boundary"


def test_legitimate_refusal_is_accepted_even_when_evaluator_flags_it() -> None:
    gm = 'Tavern Runner grimaces. "Not something I can say here."'
    ev = _evaluation(SCENARIO.initial_action, gm)
    assert ev["semantic_result"] == "FAIL"

    decision = decide_reactive_action(
        scenario=SCENARIO,
        config=_config("adversarial"),
        state=ReactivePlayerState(current_intent=SCENARIO.objective),
        turn_index=1,
        prior_gm_text=gm,
        prior_evaluation=ev,
    )

    assert decision.stop_requested is True
    assert decision.stop_reason == "legitimate_boundary"


def test_semantic_pass_without_scenario_evidence_still_gets_follow_up() -> None:
    observation = ReactiveScenario(
        scenario_id="notice",
        objective="Read the notice.",
        initial_action="I inspect the notice closely and read what is posted.",
        narrower_follow_up="What does the notice say?",
        rephrased_follow_up="Read the written notice.",
        observation_follow_up="I persist in reading the notice itself.",
        acceptance_markers=("curfew", "tax", "warning"),
    )
    gm = (
        "A gate serjeant manages the crowd and keeps one eye on the roster board while threadbare "
        "watchers and refugees cluster along the muddy gate line. Guard Captain watches with hard, "
        "tired discipline, while Tavern Runner trades hot stew and rumors near the rain barrel."
    )
    ev = _evaluation(observation.initial_action, gm)
    assert ev["semantic_result"] == "PASS"

    decision = decide_reactive_action(
        scenario=observation,
        config=_config(),
        state=ReactivePlayerState(current_intent=observation.objective),
        turn_index=1,
        prior_gm_text=gm,
        prior_evaluation=ev,
    )

    assert decision.player_text == observation.observation_follow_up
    assert decision.rationale == "observation_not_fulfilled:persist"


def test_adversarial_probe_is_seed_reproducible() -> None:
    ev = _evaluation(SCENARIO.initial_action, "Captain Vara commands the watch at this gate.")
    assert ev["semantic_result"] == "PASS"

    def choose() -> tuple[str, str]:
        state = ReactivePlayerState(current_intent=SCENARIO.objective)
        decision = decide_reactive_action(
            scenario=SCENARIO,
            config=_config("adversarial", 919),
            state=state,
            turn_index=1,
            prior_gm_text="Captain Vara commands the watch at this gate.",
            prior_evaluation=ev,
        )
        return decision.player_text, decision.rationale

    assert choose() == choose()
    assert choose()[1].startswith("adversarial_probe:")


def test_unresolved_objective_rephrases_then_stops() -> None:
    responses = iter(
        [
            "Rain beads on the gate while guards cross the yard.",
            "The gate is crowded and the roster board hangs under the eaves.",
            "Refugees wait while a runner ladles stew.",
        ]
    )

    def chat(_: str) -> dict[str, Any]:
        return {"ok": True, "gm_output": {"player_facing_text": next(responses)}, "resolution": {"kind": "social"}}

    run = run_reactive_scenario(SCENARIO, strategy="reactive", seed=12, chat_call=chat, apply_reset=False)

    assert [turn["selected_player_action"] for turn in run["turns"]] == [
        SCENARIO.initial_action,
        SCENARIO.narrower_follow_up,
        SCENARIO.rephrased_follow_up,
    ]
    assert run["termination_reason"] == "max_intent_attempts"
    assert run["unresolved_intents"] == [SCENARIO.objective]


def test_invalid_run_terminates_and_remains_distinct() -> None:
    invalid = {
        "semantic_result": "INVALID_RUN",
        "mandatory_gates": {
            "malformed_output": {"status": "PASS"},
            "player_intent_addressed": {"status": "PASS"},
        },
    }
    decision = decide_reactive_action(
        scenario=SCENARIO,
        config=_config(),
        state=ReactivePlayerState(current_intent=SCENARIO.objective),
        turn_index=1,
        prior_gm_text="A response that must not be treated as gameplay evidence.",
        prior_evaluation=invalid,
    )
    assert decision.stop_reason == "invalid_run"
    assert decision.stop_requested is True


def test_run_and_campaign_artifact_schema_trace_failures() -> None:
    def chat(_: str) -> dict[str, Any]:
        return {
            "ok": True,
            "gm_output": {"player_facing_text": "Rain beads on the gate while guards cross the yard."},
            "resolution": {"kind": "social"},
        }

    run = run_reactive_scenario(SCENARIO, strategy="reactive", seed=22, chat_call=chat, apply_reset=False)
    summary = campaign_summary([run])

    assert run["artifact_version"] == 1
    assert run["termination_reason"] == "max_intent_attempts"
    assert run["turns"][0]["selection_reason"].startswith("initial_objective:")
    assert run["turns"][0]["semantic_result"] == "FAIL"
    assert run["turns"][0]["mandatory_gates"]["player_intent_addressed"]["status"] == "FAIL"
    assert summary["total_runs"] == 1
    assert summary["total_turns"] == 3
    assert summary["semantic_result_counts"]["FAIL"] == 3
    assert summary["mandatory_gate_failure_counts"]["player_intent_addressed"] == 3
    assert summary["failure_references"][0]["turn_index"] == 0


def test_adversarial_sequence_preserves_probe_rationale() -> None:
    responses = iter(
        [
            "Captain Vara commands the watch at this gate.",
            "Captain Vara commands the watch; the serjeant only directs the queue.",
            "Captain Vara commands the watch, according to the posted roster.",
            "Captain Vara commands the watch; the witness knows only the posted roster.",
            "Captain Vara commands the watch at this gate.",
        ]
    )

    def chat(_: str) -> dict[str, Any]:
        return {"ok": True, "gm_output": {"player_facing_text": next(responses)}, "resolution": {"kind": "social"}}

    first = run_reactive_scenario(SCENARIO, strategy="adversarial", seed=77, chat_call=chat, apply_reset=False)
    assert first["turn_count"] == 5
    assert first["turns"][0]["semantic_result"] == "PASS"
    assert first["turns"][1]["selection_reason"].startswith("adversarial_probe:")
    assert all(turn["selection_reason"] for turn in first["turns"])
