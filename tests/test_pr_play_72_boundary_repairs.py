"""Separate development cases for defects outside the frozen holdout."""
import copy

import pytest
from game import api, storage
from game.player_initiative import decide
from game.ordinary_semantic_ownership import assess_addressee_grounding
from tests.test_pr_play_72_initiative import campaigns, restore, authority, offline_turns


@pytest.mark.parametrize("text", ["I want to report a programming bug.", "Survey the distant galaxy.", "Please report my inventory."])
def test_unknown_choice_subject_never_commits(campaigns, text):
    restore(campaigns, "survey")
    state = authority(); world = copy.deepcopy(state["world"])
    for key in ("patrol_survey", "patrol_report", "patrol_survey_recorded", "patrol_guards_warned"):
        world["world_state"]["flags"].pop(key, None)
    decision = decide(text, scene=api.load_active_scene(), world=world, session=state["session"])
    assert decision is not None and not decision.requires_authoritative_execution
    assert authority() == state


@pytest.mark.parametrize("name,target", [("Gate Serjeant", "gate_serjeant"), ("Gate Guard", "gate_guard")])
def test_exact_public_name_precedes_shared_gate_word(campaigns, name, target):
    restore(campaigns, "report"); state = authority()
    grounded = assess_addressee_grounding("I ask the " + name + " about the patrol route.", scene=api.load_active_scene(), world=state["world"], session=state["session"], proposed_target_id="invented")
    assert grounded["operation_eligibility"] == "executable" and grounded["target_id"] == target


def test_plural_watch_stays_ambiguous(campaigns):
    restore(campaigns, "report"); state = authority()
    grounded = assess_addressee_grounding("I ask the guards about the patrol.", scene=api.load_active_scene(), world=state["world"], session=state["session"], proposed_target_id="gate_guard")
    assert grounded["operation_eligibility"] != "executable"
