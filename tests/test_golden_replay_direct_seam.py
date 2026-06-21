"""Direct-seam replay observation of gate output.

This file owns direct-seam replay observation of gate output.
Gate legality remains with final-emission owner suites.
Replay projection remains with golden replay helpers.
"""

from __future__ import annotations

from tests.helpers.gate_orchestration_smoke import apply_final_emission_gate_consumer

from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output as read_final_emission_meta_dict
from tests.helpers.golden_replay import (
    assert_protected_golden_turn_observation,
    protected_social_speaker_observation_expectation,
    protected_structural_expectation,
)
from tests.helpers.dialogue_social_plan import (
    attach_dialogue_social_plan_to_resolution,
    make_valid_dialogue_social_plan,
)
from tests.helpers.block_stu_equivalence_fixtures import locked_runner_contract, stub_strict_social_details
from tests.helpers.gate_equivalence_monkeypatch import (
    patch_build_final_strict_social_response,
    patch_get_speaker_selection_contract,
)
from tests.helpers.opening_fallback_evidence import opening_gm_output
from tests.helpers.strict_social_harness import runner_strict_bundle
from tests.helpers.golden_replay_fixtures import observed_turn_from_gate_output


def test_golden_direct_seam_declared_alias_dialogue_plan_structural_invariants(monkeypatch):
    session, world, scene_id, resolution = runner_strict_bundle()
    attach_dialogue_social_plan_to_resolution(
        resolution,
        make_valid_dialogue_social_plan(
            speaker_id="tavern_runner",
            speaker_name="Tavern Runner",
            dialogue_intent="question",
            allowed_pregate_speaker_labels=["Ragged stranger"],
            speaker_alias_resolution_source="manual_bundle_override",
        ),
    )
    patch_get_speaker_selection_contract(monkeypatch, locked_runner_contract())
    pre_gate_line = 'Ragged stranger says, "No names, only rumors."'
    patch_build_final_strict_social_response(
        monkeypatch, line=pre_gate_line, strict_social_details=stub_strict_social_details
    )

    out, _ = apply_final_emission_gate_consumer(
        {"player_facing_text": pre_gate_line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=scene_id,
        world=world,
    )

    final_text = str(out.get("player_facing_text") or "")
    meta = read_final_emission_meta_dict(out) or {}
    turn = observed_turn_from_gate_output(
        scenario_id="declared_alias_dialogue_plan",
        gm_output=out,
        resolution=resolution,
        unavailable=["fallback_family"],
    )

    assert turn.get("selected_speaker_id") == "runner"
    assert_protected_golden_turn_observation(
        turn,
        protected_social_speaker_observation_expectation("runner"),
        scenario_id="declared_alias_dialogue_plan",
        debug_context=f"meta={meta!r}; final_text={final_text!r}",
    )


def test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership():
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out, _ = apply_final_emission_gate_consumer(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    final_text = str(out.get("player_facing_text") or "")
    turn = observed_turn_from_gate_output(
        scenario_id="opening_fallback_path",
        gm_output=out,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        unavailable=[],
    )

    assert_protected_golden_turn_observation(
        turn,
        protected_structural_expectation(
            require_present=("final_text",),
            no_scaffold=False,
        ),
        scenario_id="opening_fallback_path",
        debug_context=f"final_text={final_text!r}",
    )
