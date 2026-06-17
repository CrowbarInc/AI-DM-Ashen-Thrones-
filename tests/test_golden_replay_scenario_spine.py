"""Golden replay scenario-spine smoke coverage.

This file owns golden replay scenario-spine smoke coverage.
Scenario schema/evaluator legality remains with scenario-spine owner suites.
Golden replay orchestration remains in tests/helpers/golden_replay.py.
"""

from __future__ import annotations

from game.scenario_spine import (
    ScenarioBranch,
    ScenarioSpine,
    ScenarioTurn,
    scenario_spine_to_dict,
    validate_scenario_spine_definition,
)
from game.scenario_spine_eval import minimal_complete_transcript_turn_meta
from tests.helpers.golden_replay import (
    assert_golden_turn_observation,
    format_golden_replay_debug,
    protected_structural_expectation,
    run_golden_replay,
)
from tests.helpers.golden_replay_fixtures import (
    gm_response,
    golden_replay_chat_stubs,
    seed_spine_three_branch_world,
)


def test_golden_replay_scenario_spine_three_branch_structural_smoke(tmp_path, monkeypatch):
    spine = ScenarioSpine(
        spine_id="golden_smoke_frontier_gate",
        title="Golden smoke three branch spine",
        smoke_only=True,
        fixed_start_state={"scene_id": "scene_investigate"},
        branches=(
            ScenarioBranch(
                branch_id="branch_runner_question",
                label="Ask the runner",
                turns=(ScenarioTurn(turn_id="runner_ask", player_prompt="Runner, who attacked the patrol?"),),
            ),
            ScenarioBranch(
                branch_id="branch_guard_question",
                label="Ask the guard",
                turns=(ScenarioTurn(turn_id="guard_ask", player_prompt="Guard, what did you see?"),),
            ),
            ScenarioBranch(
                branch_id="branch_notice_check",
                label="Check the notice",
                turns=(
                    ScenarioTurn(
                        turn_id="notice_check",
                        player_prompt="I examine the notice board; does it show where the missing patrol went?",
                    ),
                ),
            ),
        ),
    )
    assert validate_scenario_spine_definition(spine) == []
    spine_dict = scenario_spine_to_dict(spine)

    def _fake_call_gpt(_messages):
        return gm_response('Tavern Runner says, "The east road keeps the best clue."')

    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=_fake_call_gpt,
        suppress_exploration=False,
        suppress_intent=False,
    )

    branch_rows: list[dict] = []
    for branch in spine.branches:
        result = run_golden_replay(
            scenario_id=f"scenario_spine_three_branch::{branch.branch_id}",
            turns=[turn.player_prompt for turn in branch.turns],
            tmp_path=tmp_path / branch.branch_id,
            monkeypatch=monkeypatch,
            setup_fn=seed_spine_three_branch_world,
        )
        assert result["turn_count"] == len(branch.turns)
        for i, turn in enumerate(result["turns"]):
            meta = minimal_complete_transcript_turn_meta(
                spine_id=spine.spine_id,
                branch_id=branch.branch_id,
                turn_id=branch.turns[i].turn_id,
                turn_index=i,
                smoke=True,
                max_turns=len(branch.turns),
            )
            assert meta["scenario_spine"]["branch_id"] == branch.branch_id
            assert_golden_turn_observation(
                turn,
                {
                    **protected_structural_expectation(
                        require_present=("final_text",),
                        allow_unavailable=(
                            "fallback_family",
                            "selected_speaker_id",
                            "final_emitted_source",
                            "trace.canonical_entry",
                            "trace.social_contract_trace",
                        ),
                        no_scaffold=False,
                    ),
                    "scaffold_leakage": False,
                },
                debug_context=format_golden_replay_debug(result),
            )
        last = result["turns"][-1]
        branch_rows.append(
            {
                "branch_id": branch.branch_id,
                "turn_count": result["turn_count"],
                "route_kind": last.get("route_kind"),
                "selected_speaker_id": last.get("selected_speaker_id"),
                "final_emitted_source": last.get("final_emitted_source"),
                "fallback_family": last.get("fallback_family"),
            }
        )

    assert [row["branch_id"] for row in branch_rows] == [branch.branch_id for branch in spine.branches]
    assert {row["turn_count"] for row in branch_rows} == {1}
    assert len({(row["route_kind"], row["selected_speaker_id"]) for row in branch_rows}) >= 2
    assert [b["branch_id"] for b in spine_dict["branches"]] == sorted(row["branch_id"] for row in branch_rows)
