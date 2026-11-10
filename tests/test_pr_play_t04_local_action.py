"""Low-stakes local approach and contact stay transient and authoritative."""
from __future__ import annotations

import copy
import json

from game import immutable_valid_response as ivr
from game import storage
from game.local_interaction import resolve_transient_local_action
from tests.test_pr_play_post_npc_handoff import CLUE, _say, client

COMPOUND = "I walk over to the notice board and put a hand on the frame."
MILESTONE_CLUE = "Faint overlapping prints"


def _scene():
    return storage.load_active_scene()


def _outcome(text, scene=None, world=None, session=None):
    return resolve_transient_local_action(
        text,
        scene=scene if scene is not None else _scene(),
        world=world if world is not None else storage.load_world(),
        session=session if session is not None else storage.load_session(),
    )


def _save_scene(scene):
    payload = copy.deepcopy(scene)
    payload.pop("_is_canon", None)
    storage.save_scene(payload)


def test_a_original_t04_http_completes_without_mutation(client):
    before_character = json.dumps(storage.load_character(), sort_keys=True)
    before_world = json.dumps(storage.load_world(), sort_keys=True)
    before = _say(client, "You mentioned the patrol. What have you heard?")
    result = _say(client, COMPOUND)
    log = storage.load_log()[-1]
    resolution = log["resolution"]
    outcome = resolution["metadata"]["transient_local_action"]
    gm = log["gm_output"]
    record = ivr.accepted_record(gm)
    assert "notice board" in result["visible"].lower()
    assert "frame" in result["visible"].lower()
    assert "not a supported action" not in result["visible"].lower()
    assert CLUE not in result["visible"]
    assert result["scene"] == "frontier_gate"
    assert "notice_patrol_route" not in result["clues"]
    assert resolution["success"] is True
    assert resolution["resolved_transition"] is False
    assert resolution["metadata"]["action_owner"] == "local_interaction"
    assert outcome["target_id"] == "notice_board"
    assert outcome["completion"]["local_movement"] == "completed"
    assert outcome["completion"]["physical_contact"] == "completed"
    assert outcome["scene_transition"] is False
    assert outcome["persistent_state_changed"] is False
    assert outcome["narration_authorized"] is True
    assert outcome["authority_basis"]["visibility"] is True
    assert outcome["authority_basis"]["inspectability"] is True
    assert record["hard_validation"]["hard_valid"] and record["immutable"]
    assert ivr.verify_delivery_record(record)
    assert record["text"] == gm["player_facing_text"] == result["visible"] == result["publication"]
    assert json.dumps(storage.load_character(), sort_keys=True) == before_character
    assert storage.load_session()["active_scene_id"] == before["scene"]
    world = json.loads(json.dumps(storage.load_world(), sort_keys=True))
    prior = json.loads(before_world)
    assert world.get("inventory", prior.get("inventory")) == prior.get("inventory")


def test_b_and_c_and_d_other_fixture_approach_and_contact(client):
    moved = _say(client, "I follow the missing patrol rumor toward the northwest track.")
    assert moved["scene"] == "old_milestone"
    approach = _say(client, "I walk over to the weathered milestone.")
    assert "weathered milestone" in approach["visible"].lower()
    assert "rest a hand" not in approach["visible"].lower()
    assert approach["scene"] == "old_milestone"
    assert MILESTONE_CLUE not in approach["visible"]
    contact = _say(client, "I put a hand on the weathered milestone.")
    assert "rest a hand" in contact["visible"].lower()
    assert "walk over" not in contact["visible"].lower()
    assert contact["scene"] == "old_milestone"
    assert MILESTONE_CLUE not in contact["visible"]
    touched = _say(client, "I touch the weathered milestone.")
    assert "walk over" not in touched["visible"].lower()
    assert touched["scene"] == "old_milestone"


def test_e_compound_outcome_authorizes_both_parts(client):
    outcome = _outcome(COMPOUND)
    assert outcome["status"] == "completed"
    assert outcome["categories"] == ["local_movement", "physical_contact"]
    visible = _say(client, COMPOUND)["visible"].lower()
    assert "walk over" in visible and "frame" in visible


def test_f_ambiguous_target_is_not_contacted(client):
    scene = _scene()
    scene["scene"]["interactables"].append({
        "id": "roster_board",
        "label": "Roster board",
        "aliases": ["board"],
        "type": "investigate",
    })
    _save_scene(scene)
    outcome = _outcome("I touch the board.")
    assert outcome["status"] == "refused"
    assert outcome["reason"] == "ambiguous_local_object"
    visible = _say(client, "I touch the board.")["visible"].lower()
    assert "rest a hand" not in visible
    assert "nothing has been attempted" in visible


def test_g_inaccessible_target_is_not_touched(client):
    scene = _scene()
    board = next(item for item in scene["scene"]["interactables"] if item["id"] == "notice_board")
    board["accessible"] = False
    _save_scene(scene)
    outcome = _outcome("I put a hand on the notice board.")
    assert outcome["status"] == "refused"
    assert outcome["reason"] == "inaccessible_local_object"
    visible = _say(client, "I walk over to the notice board.")["visible"].lower()
    assert "not accessible" in visible
    assert "walk over to the notice board." not in visible or "have not approached" in visible


def test_h_hidden_target_is_not_revealed(client):
    scene = _scene()
    scene["scene"]["interactables"].append({
        "id": "sealed_cache",
        "label": "Sealed cache",
        "aliases": ["cache"],
        "hidden": True,
        "type": "investigate",
    })
    scene["scene"]["hidden_facts"] = list(scene["scene"].get("hidden_facts") or []) + [
        "A sealed cache waits under the boards."
    ]
    _save_scene(scene)
    outcome = _outcome("I touch the sealed cache.")
    assert outcome["status"] == "refused"
    assert outcome["target_id"] is None
    visible = _say(client, "I touch the sealed cache.")["visible"]
    assert "sealed cache" not in visible.lower()
    assert "rest a hand" not in visible.lower()
    assert "nothing here matches" in visible.lower()


def test_i_consequential_manipulation_is_not_downgraded(client):
    before = json.dumps(storage.load_character(), sort_keys=True)
    taken = _say(client, "I take the notice board.")
    assert "rest a hand" not in taken["visible"].lower()
    assert "walk over to the notice board and rest" not in taken["visible"].lower()
    copying = _say(client, "I try to copy the patrol warning onto my sleeve with a bit of mud so I won't forget the wording.")
    assert "nothing was written" in copying["visible"].lower()
    assert "no established object matches" in copying["visible"].lower()
    assert json.dumps(storage.load_character(), sort_keys=True) == before
    opened = _outcome("I open the notice board.")
    assert opened is None or opened.get("status") != "completed"


def test_j_genuine_travel_still_changes_scene(client):
    moved = _say(client, "I follow the missing patrol rumor toward the northwest track.")
    assert moved["scene"] == "old_milestone"
    assert "Old Milestone" in moved["visible"]


def test_k_authorized_clue_survives_local_contact(client):
    _say(client, COMPOUND)
    reading = _say(client, "Read me the missing-patrol notice, not the tax lines.")
    assert CLUE in reading["visible"]
    assert "impatient with anyone who reads too long" not in reading["visible"]
    assert "notice_patrol_route" in reading["clues"]
    assert reading["scene"] == "frontier_gate"


def test_l_npc_dialogue_is_not_fixture_contact(client):
    asked = _say(client, "You mentioned the patrol. What have you heard?")
    assert "Guard Captain" in asked["visible"] or "patrol went missing" in asked["visible"]
    assert "rest a hand" not in asked["visible"].lower()
    walked = _say(client, "I walk over to the guard captain and ask what he heard.")
    assert "rest a hand" not in walked["visible"].lower()


def test_m_and_n_acceptance_and_state(client):
    before_character = storage.load_character()
    before_scene = storage.load_session()["active_scene_id"]
    result = _say(client, "I touch the notice board.")
    log = storage.load_log()[-1]
    record = ivr.accepted_record(log["gm_output"])
    assert record["immutable"] and record["hard_validation"]["hard_valid"]
    assert record["text"] == result["visible"]
    assert storage.load_character() == before_character
    assert storage.load_session()["active_scene_id"] == before_scene
    assert log["resolution"]["resolved_transition"] is False
    assert log["resolution"]["state_changes"] == {}
    assert "notice_patrol_route" not in result["clues"]


def test_o_unsupported_gesture_is_not_completed(client):
    visible = _say(client, "I lick the notice board.")["visible"].lower()
    assert "rest a hand" not in visible
    assert "walk over to the notice board" not in visible
    assert _outcome("I lick the notice board.") is None
