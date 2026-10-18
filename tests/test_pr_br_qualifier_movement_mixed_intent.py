"""PR-BR targeted repair: qualifier safety, movement decisions, mixed obligations.

Deterministic only. No gameplay or model calls.
"""
from __future__ import annotations

from game.gm_resolution_decision import (
    DECISION_METADATA_KEY,
    OUTCOME_MUTATION,
    OUTCOME_UNRESOLVED,
    audit_narration_against_decision,
    narration_acknowledges_supporting,
    reconcile_movement_decision,
    sentences_without_decision_violations,
)
from game.live_resolution import attach_interaction_obligation
from game.player_commitment import commitment_status, executable_obligations


def _scene(*facts: object, scene_id: str = "mill_race", exits: list | None = None) -> dict:
    return {
        "scene": {
            "id": scene_id,
            "visible_facts": list(facts),
            "summary": scene_id.replace("_", " "),
            "exits": list(exits or []),
        }
    }


def _attach(player: str, scene: dict, *, resolution: dict | None = None) -> dict:
    resolution = resolution or {}
    attach_interaction_obligation(
        resolution,
        player_text=player,
        session={"active_scene_id": scene["scene"]["id"], "turn_counter": 1},
        scene_id=scene["scene"]["id"],
        scene=scene,
        world={"npcs": []},
    )
    return resolution


def _audit(text: str, resolution: dict, scene: dict) -> dict:
    corpus = "\n".join(str(item) for item in scene["scene"].get("visible_facts") or [])
    return audit_narration_against_decision(
        text,
        decision=resolution["metadata"][DECISION_METADATA_KEY],
        authored_corpus=corpus,
    )


def _codes(audit: dict) -> set[str]:
    return {code for row in audit["violations"] for code in row.get("reason_codes") or []}


SLUICE = _scene(
    {
        "text": "The oak sluice gate beside the mill race is jammed halfway open.",
        "semantic_identity": {
            "kind": "world_fact",
            "subject": "sluice_gate",
            "subject_aliases": ["sluice gate", "oak sluice", "gate", "sluice"],
            "relation": "condition",
            "value": "jammed",
            "value_aliases": ["jammed", "halfway open"],
            "polarity": "positive",
        },
    }
)


def test_unknown_cause_actor_and_time_are_not_event_sites():
    player = "What happened to the sluice gate?"
    resolution = _attach(player, SLUICE)
    decision = resolution["metadata"][DECISION_METADATA_KEY]
    assert "cause" in decision["unresolved_qualifiers"]
    unknown = "What caused it to jam, when it happened, and who might be responsible remain unseen here."
    audit = _audit(unknown, resolution, SLUICE)
    assert "unauthorized_qualifier:location" not in _codes(audit)
    assert audit["hard_valid"] is True
    actor = "Who forced the sluice remains unknown."
    assert _audit(actor, resolution, SLUICE)["hard_valid"] is True
    timing = "When it happened remains unknown from what we can see here."
    timing_audit = _audit(timing, resolution, SLUICE)
    assert "unauthorized_qualifier:location" not in _codes(timing_audit)
    assert timing_audit["hard_valid"] is True


def test_it_happened_here_is_still_an_event_site():
    resolution = _attach("What happened to the sluice gate?", SLUICE)
    audit = _audit("It happened here.", resolution, SLUICE)
    assert "unauthorized_qualifier:location" in _codes(audit)
    asked = _audit("It happened here?", resolution, SLUICE)
    assert "unauthorized_qualifier:location" in _codes(asked)


def test_preservation_keeps_authorized_uncertainty_and_drops_narrator_lead():
    resolution = _attach("What happened to the sluice gate?", SLUICE)
    text = (
        "The oak sluice gate beside the mill race is jammed halfway open. "
        "What caused it to jam, when it happened, and who might be responsible remain unseen here. "
        "To uncover more, you might compare this disruption with changes around the missing patrol's notice."
    )
    audit = _audit(text, resolution, SLUICE)
    assert "unauthorized_qualifier:location" not in _codes(audit)
    assert "unsupported_narrator_lead" in _codes(audit)
    kept = sentences_without_decision_violations(text, audit)
    assert "remain unseen here" in kept
    assert "missing patrol" not in kept


def test_npc_rumor_with_a_source_stays_a_claim():
    resolution = _attach("What happened to the sluice gate?", SLUICE)
    rumor = 'Mirelle says, "Travelers speak of a missing patrol that left a notice."'
    audit = _audit(rumor, resolution, SLUICE)
    assert audit["hard_valid"] is True
    assert audit["proposed_facts"][0]["provenance"] == "npc_claim"
    grounded = _audit("You might look again at the jammed sluice gate.", resolution, SLUICE)
    assert "unsupported_narrator_lead" not in _codes(grounded)
    question = (
        '"Could you clarify what you mean by \'that\' exactly? Are you asking about the new curfew, '
        'the missing patrol, or something else posted on the notice board?" the gate guard asks.'
    )
    asked = _audit(question, resolution, SLUICE)
    assert asked["hard_valid"] is True
    assert "notice_roster_history" not in _codes(asked)


def test_successful_transition_authorizes_destination_and_rejects_departure_exit():
    departure = _scene(
        "Coils of new rope line the covered walk.",
        "A stair at the far end climbs to the sail loft.",
        scene_id="rope_walk",
        exits=[{"label": "Stair to the sail loft", "target_scene_id": "sail_loft"}],
    )
    destination = _scene(
        "Cut canvas hangs from the pegs.",
        scene_id="sail_loft",
        exits=[{"label": "Hatch onto the roof", "target_scene_id": "roof"}],
    )
    resolution = _attach("I go to the sail loft.", departure)
    resolution["kind"] = "scene_transition"
    resolution["resolved_transition"] = True
    resolution["target_scene_id"] = "sail_loft"
    resolution["originating_scene_id"] = "rope_walk"
    reconcile_movement_decision(
        resolution,
        departure_scene=departure,
        destination_scene=destination,
        world={"npcs": []},
    )
    decision = resolution["metadata"][DECISION_METADATA_KEY]
    assert decision["outcome_classification"] == OUTCOME_MUTATION
    mutation = next(row for row in decision["permitted_state_mutations"] if row["type"] == "location")
    assert mutation["source_scene_id"] == "rope_walk"
    assert mutation["target_scene_id"] == "sail_loft"
    roles = {
        row["text"]: (row.get("semantic_identity") or {}).get("scene_role")
        for row in decision["proposed_facts"]
    }
    assert roles["A stair at the far end climbs to the sail loft."] == "departure_exit"
    assert roles["Cut canvas hangs from the pegs."] == "destination_fact"
    assert roles["Hatch onto the roof"] == "destination_exit"
    arrival = _audit("You step into the sail loft. Cut canvas hangs from the pegs.", resolution, destination)
    assert arrival["hard_valid"] is True
    onward = _audit("At the far end, a sturdy stair leads upward, beckoning further exploration.", resolution, destination)
    assert "departure_exit_reused_as_destination_exit" in _codes(onward)
    invented = _audit("A hidden stair leads upward to the vault.", resolution, destination)
    assert invented["hard_valid"] is False


def test_unresolved_and_failed_movement_do_not_authorize_arrival():
    scene = _scene("The yard is empty.", scene_id="yard", exits=[])
    unresolved = _attach("I head toward the unnamed place.", scene)
    unresolved["kind"] = "travel"
    unresolved["resolved_transition"] = False
    unresolved["target_scene_id"] = None
    reconcile_movement_decision(unresolved, departure_scene=scene, destination_scene=scene)
    decision = unresolved["metadata"][DECISION_METADATA_KEY]
    assert decision["outcome_classification"] == OUTCOME_UNRESOLVED
    assert not any(row.get("type") == "location" for row in decision["permitted_state_mutations"])
    failed = _attach("I go to the blocked arch.", scene)
    failed["kind"] = "scene_transition"
    failed["resolved_transition"] = False
    failed["success"] = False
    failed["target_scene_id"] = None
    reconcile_movement_decision(failed, departure_scene=scene, destination_scene=scene)
    failed_decision = failed["metadata"][DECISION_METADATA_KEY]
    assert not any(row.get("type") == "location" for row in failed_decision["permitted_state_mutations"])
    assert any("did not resolve" in item for item in failed_decision["narration_constraints"])


def test_turn7_thanks_is_supporting_and_travel_is_primary():
    line = "I thank Mirelle for the warning, then head for the eastern courtyard."
    record = executable_obligations(line)
    assert record["primary"] == "travel"
    assert record["mutation_owner"] == "travel"
    assert record["sequence"] == ["social", "travel"]
    assert record["supporting"][0]["act"] == "thank"
    scene = _scene(
        "Mirelle warns that the steps are slick.",
        scene_id="cistern",
        exits=[{"label": "Arch to the eastern courtyard", "target_scene_id": "eastern_courtyard"}],
    )
    destination = _scene("The eastern courtyard is open stone.", scene_id="eastern_courtyard")
    resolution = _attach(line, scene)
    contract = resolution["metadata"]["resolution_contract"]
    assert contract["construction"]["executable_obligations"]["primary"] == "travel"
    assert resolution["metadata"]["interaction_obligation"]["executable_obligations"]["supporting"][0]["kind"] == "social"
    resolution["kind"] = "scene_transition"
    resolution["resolved_transition"] = True
    resolution["target_scene_id"] = "eastern_courtyard"
    resolution["originating_scene_id"] = "cistern"
    reconcile_movement_decision(resolution, departure_scene=scene, destination_scene=destination)
    decision = resolution["metadata"][DECISION_METADATA_KEY]
    assert any(row.get("type") == "location" and row.get("target_scene_id") == "eastern_courtyard" for row in decision["permitted_state_mutations"])
    assert narration_acknowledges_supporting("You thank Mirelle and cross into the eastern courtyard.", record)
    omitted = _audit("You cross into the eastern courtyard and look around the open stone.", resolution, destination)
    assert "supporting_obligation_unacknowledged" in _codes(omitted)
    acknowledged = _audit("You thank Mirelle and cross into the eastern courtyard.", resolution, destination)
    assert "supporting_obligation_unacknowledged" not in _codes(acknowledged)


def test_inverse_mixed_intent_keeps_social_primary_and_committed_travel():
    line = "I ask Nessa who owns the warehouse while walking to the gate."
    record = executable_obligations(line)
    assert record["primary"] == "social"
    assert record["mutation_owner"] == "travel"
    assert record["supporting"][0]["kind"] == "travel"
    assert record["sequence"][0] == "social"


def test_modality_contrasts_do_not_execute_uncommitted_travel():
    assert executable_obligations("I ask Nessa whether I should go to the gate.")["mutation_owner"] is None
    assert commitment_status("If Nessa agrees, I'll go to the gate.") == "conditional"
    assert executable_obligations("If Nessa agrees, I'll go to the gate.")["mutation_owner"] is None
    assert commitment_status("I might head to the gate later.") in {"contemplated", "intended_later"}
    assert executable_obligations("I might head to the gate later.")["mutation_owner"] is None
    both = executable_obligations("I thank Nessa and go to the gate.")
    assert both["primary"] == "travel"
    assert both["supporting"][0]["act"] == "thank"
    told = executable_obligations("I tell the guard I'll return, then cross the bridge.")
    assert told["primary"] == "travel"
    assert told["supporting"][0]["act"] == "tell"
    asked = executable_obligations("On my way to the gate, I ask Nessa whether she saw the courier.")
    assert asked["primary"] == "social"
    assert asked["supporting"][0]["kind"] == "travel"
