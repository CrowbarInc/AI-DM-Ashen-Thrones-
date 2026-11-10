"""AT-OPT-06 same-scene transition regression.

Calls production ``_derive_transition_node`` and ``build_narrative_plan``.
No provider.
"""

from __future__ import annotations

import copy

from game import ctir
from game.narrative_planning import _derive_transition_node, build_narrative_plan


def _ctir(
    *,
    scene_id: str = "frontier_gate",
    player: str = "I examine the notice board.",
    resolution: dict | None = None,
    state_mutations: dict | None = None,
) -> dict:
    return ctir.build_ctir(
        turn_id="at-opt-06",
        scene_id=scene_id,
        player_input=player,
        builder_source="tests.at_opt_06.transition",
        resolution=resolution,
        state_mutations=state_mutations,
    )


def _derive(body: dict, public: dict | None = None) -> tuple[dict, dict]:
    node, _codes = _derive_transition_node(body, public_scene_slice=public)
    plan = build_narrative_plan(ctir=body, public_scene_slice=public)
    plan_node = plan["transition_node"]
    assert plan_node["transition_required"] is node["transition_required"]
    assert plan_node["transition_type"] == node["transition_type"]
    return node, plan


def _same_stamp(player: str = "I examine the notice board.") -> dict:
    body = _ctir(player=player)
    body["state_mutations"] = {
        "scene": {"scene_id": "frontier_gate"},
        "session": {},
        "combat": {},
        "clues_leads": {},
    }
    return body


def test_same_scene_id_is_not_a_location_change() -> None:
    node, plan = _derive(_same_stamp())
    assert node["transition_required"] is False
    assert node["transition_type"] == "none"
    assert node["before_anchor"] is None
    assert node["after_anchor"] is None
    assert not any("state_mutations.scene" in field for field in node["source_fields"])
    assert plan["transition_node"]["transition_required"] is False


def test_canonical_scene_id_whitespace_still_matches() -> None:
    body = _ctir(scene_id="frontier_gate")
    body["state_mutations"] = {"scene": {"scene_id": "  frontier_gate  "}, "session": {}, "combat": {}, "clues_leads": {}}
    node, _plan = _derive(body)
    assert node["transition_required"] is False
    assert node["transition_type"] == "none"


def test_different_scene_id_remains_a_location_change() -> None:
    body = _ctir()
    body["state_mutations"] = {"scene": {"scene_id": "old_milestone"}, "session": {}, "combat": {}, "clues_leads": {}}
    node, _plan = _derive(body)
    assert node["transition_required"] is True
    assert node["transition_type"] == "location_change"
    assert node["before_anchor"]["scene_id"] == "frontier_gate"
    assert node["after_anchor"]["scene_id"] == "old_milestone"


def test_explicit_scene_activation_remains_required() -> None:
    body = _ctir()
    body["state_mutations"] = {"scene": {"activate_scene_id": "old_milestone"}, "session": {}, "combat": {}, "clues_leads": {}}
    node, _plan = _derive(body)
    assert node["transition_required"] is True
    assert node["after_anchor"]["scene_id"] == "old_milestone"
    assert any("state_mutations.scene" in field for field in node["source_fields"])


def test_same_scene_activation_does_not_cancel_the_activation_signal() -> None:
    body = _ctir()
    body["state_mutations"] = {
        "scene": {"scene_id": "frontier_gate", "activate_scene_id": "frontier_gate"},
        "session": {},
        "combat": {},
        "clues_leads": {},
    }
    node, _plan = _derive(body)
    assert node["transition_required"] is True
    assert node["transition_type"] != "none"


def test_resolved_transition_remains_required_on_the_same_scene_stamp() -> None:
    body = _same_stamp()
    body["resolution"] = {"kind": "scene_transition", "resolved_transition": True, "target_scene_id": "old_milestone"}
    node, plan = _derive(body)
    assert node["transition_required"] is True
    assert node["transition_type"] != "none"
    assert node["after_anchor"]["scene_id"] == "old_milestone"
    assert plan["narrative_mode"] == "transition"


def test_resolved_transition_without_a_new_target_is_not_cleared_by_scene_equality() -> None:
    body = _same_stamp()
    body["resolution"] = {"kind": "scene_transition", "resolved_transition": True}
    node, _plan = _derive(body)
    assert node["transition_required"] is True
    assert "resolution.resolved_transition" in node["source_fields"]


def test_arrival_at_another_scene_remains_required() -> None:
    body = _same_stamp()
    body["resolution"] = {
        "kind": "travel",
        "target_scene_id": "old_milestone",
        "state_changes": {"arrived_at_scene": True},
    }
    node, plan = _derive(body)
    assert node["transition_required"] is True
    assert node["after_anchor"]["scene_id"] == "old_milestone"
    assert plan["narrative_mode"] == "transition"


def test_time_skip_remains_required_with_a_same_scene_stamp() -> None:
    body = _same_stamp()
    body["resolution"] = {
        "kind": "custom",
        "metadata": {
            "transition_type": "time_skip",
            "time_anchor_before": "day:3:night",
            "time_anchor_after": "day:4:dawn",
        },
    }
    node, _plan = _derive(body)
    assert node["transition_required"] is True
    assert node["transition_type"] == "time_skip"
    assert node["before_anchor"]["time_anchor"] == "day:3:night"
    assert node["after_anchor"]["time_anchor"] == "day:4:dawn"


def test_same_scene_ordinary_actions_do_not_require_advancement() -> None:
    for player in (
        "I push the nearest crate.",
        "Hello, Gate Guard.",
        "I look closely at the notice board.",
    ):
        node, _plan = _derive(_same_stamp(player))
        assert node["transition_required"] is False
        assert node["transition_type"] == "none"
        assert node["before_anchor"] is None


def test_missing_current_scene_id_keeps_the_prior_stamp_signal() -> None:
    body = _ctir(scene_id="frontier_gate")
    body["scene_id"] = ""
    body["state_mutations"] = {"scene": {"scene_id": "frontier_gate"}, "session": {}, "combat": {}, "clues_leads": {}}
    node, _codes = _derive_transition_node(body, public_scene_slice=None)
    assert node["transition_required"] is True
    assert node["transition_type"] == "location_change"


def test_missing_destination_scene_id_does_not_invent_a_change() -> None:
    body = _ctir()
    body["state_mutations"] = {"scene": {}, "session": {}, "combat": {}, "clues_leads": {}}
    node, _plan = _derive(body)
    assert node["transition_required"] is False
    assert node["transition_type"] == "none"


def test_both_scene_ids_missing_does_not_invent_a_location_change() -> None:
    body = _ctir(scene_id="frontier_gate")
    body["scene_id"] = ""
    body["state_mutations"] = {"scene": {}, "session": {}, "combat": {}, "clues_leads": {}}
    node, _codes = _derive_transition_node(body, public_scene_slice=None)
    assert node["transition_required"] is False
    assert node["transition_type"] == "none"
    assert node["before_anchor"] is None
    assert node["after_anchor"] is None


def test_same_scene_state_change_flag_stays_required() -> None:
    body = _same_stamp()
    body["resolution"] = {"kind": "custom", "state_changes": {"scene_transition_occurred": True}}
    node, _plan = _derive(body)
    assert node["transition_required"] is True
    assert "resolution.state_changes.scene_transition_occurred" in node["source_fields"]


def test_repeated_derivation_is_stable_and_does_not_mutate_inputs() -> None:
    body = _same_stamp("I look around the milestone.")
    public = {"scene_id": "frontier_gate", "location_tokens": ["Frontier Gate"]}
    body_before = copy.deepcopy(body)
    public_before = copy.deepcopy(public)
    first, _codes = _derive_transition_node(body, public_scene_slice=public)
    second, _codes = _derive_transition_node(body, public_scene_slice=public)
    assert first == second
    assert body == body_before
    assert public == public_before
    plan_a = build_narrative_plan(ctir=body, public_scene_slice=public)
    plan_b = build_narrative_plan(ctir=body, public_scene_slice=public)
    assert plan_a["transition_node"] == plan_b["transition_node"]
    assert body == body_before
    assert public == public_before
