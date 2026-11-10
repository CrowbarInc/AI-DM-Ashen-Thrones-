"""Selected disclosures must not acquire synthetic scene-momentum filler."""
import copy

import pytest

from game import immutable_valid_response as ivr, storage
from game.response_policy_enforcement import enforce_scene_momentum, apply_response_policy_enforcement
from tests.test_pr_play_post_npc_handoff import client, _say

CLUE = "The missing patrol was last seen taking the northwest mud track past the crates."
SCENE = {"scene": {"id": "frontier_gate", "location": "Cinderwatch Gate District",
                   "visible_facts": ["The notice board lists taxes and a missing patrol warning."]}}


@pytest.fixture
def momentum(monkeypatch):
    calls = []
    monkeypatch.setattr("game.gm._scene_momentum_due", lambda *args: True)
    def stock(*args, **kwargs):
        calls.append((args, kwargs))
        return "A passerby demands room at the board."
    monkeypatch.setattr("game.diegetic_fallback_narration.render_scene_momentum_diegetic_append", stock)
    return calls


def compose(text, resolution, tags=None):
    gm = {"player_facing_text": text, "tags": tags or [], "metadata": {}}
    before = copy.deepcopy((gm, resolution))
    result = enforce_scene_momentum(gm, session={}, scene_envelope=SCENE, resolution=resolution)
    assert (gm, resolution) == before
    return result


@pytest.mark.parametrize("kind", ["discover_clue", "investigate", "observe"])
def test_selected_information_excludes_stock_component(momentum, kind):
    result = compose(CLUE, {"kind": kind, "success": True, "clue_text": CLUE})
    assert result["player_facing_text"] == CLUE
    assert not momentum
    assert not any(tag.startswith("scene_momentum:") for tag in result["tags"])
    assert result["metadata"]["emission_debug"]["scene_momentum_composition"]["appended"] is False


@pytest.mark.parametrize("text", [
    "Rain beads along the notice's lower edge. " + CLUE,
    "The notice puts the route plainly: the patrol took the northwest mud track past the crates. The ink is still legible.",
    CLUE + ' The guard beside the board says, "Read that line carefully."',
])
def test_existing_contextual_elaboration_is_kept(momentum, text):
    assert compose(text, {"kind": "discover_clue", "success": True, "clue_text": CLUE})["player_facing_text"] == text
    assert not momentum


def test_multiple_authorized_facts_and_resolved_event_are_kept(momentum):
    second = "The patrol left before sunrise."
    text = CLUE + " " + second + " You unfold the posted sheet."
    resolution = {"kind": "investigate", "success": True, "clue_text": CLUE,
                  "discovered_clues": [CLUE, second],
                  "state_changes": {"physical_operation": "unfold", "mutation": True}}
    assert compose(text, resolution)["player_facing_text"] == text
    assert not momentum


@pytest.mark.parametrize("resolution,text", [
    ({"kind": "social", "success": True}, 'The guard says, "Rain again."'),
    ({"kind": "travel", "success": True, "resolved_transition": True, "target_scene_id": "old_milestone"}, "You arrive at Old Milestone."),
    ({"kind": "physical", "success": True, "state_changes": {"physical_operation": "open"}}, "You open the shutter."),
    ({"kind": "investigate", "success": False, "clue_text": CLUE}, "The page cannot be read."),
    ({"kind": "investigate", "success": True, "state_changes": {"already_searched": True}, "clue_text": CLUE}, "You examine the notice again."),
    ({"kind": "observe", "success": True}, "Rain taps the frame."),
])
def test_other_routes_retain_existing_composition(momentum, resolution, text):
    result = compose(text, resolution)
    assert momentum
    assert text in result["player_facing_text"]
    assert "scene_momentum_composition" not in result["metadata"].get("emission_debug", {})


def test_authorized_momentum_already_in_candidate_is_kept(momentum):
    text = CLUE + " The guard points to the route."
    assert compose(text, {"kind": "discover_clue", "success": True, "clue_text": CLUE},
                   ["scene_momentum:consequence_or_opportunity"])["player_facing_text"] == text
    assert not momentum


def test_original_t05_http_acceptance_and_publication(client, monkeypatch):
    accepted = []
    original = ivr.seal_accepted_response
    def seal(*args, **kwargs):
        result = original(*args, **kwargs)
        accepted.append(copy.deepcopy(result))
        return result
    monkeypatch.setattr(ivr, "seal_accepted_response", seal)
    for text in [
        "I stop under the gate and look around. What is actually in front of me?",
        "Gate Guard, do you have a moment?",
        "You mentioned the patrol. What have you heard?",
        "I walk over to the notice board and put a hand on the frame.",
    ]:
        _say(client, text)
    before = copy.deepcopy(storage.load_character())
    scene = storage.load_session()["active_scene_id"]
    accepted.clear()
    reading = _say(client, "Read me the missing-patrol notice, not the tax lines.")
    assert CLUE in reading["visible"]
    assert "notice_patrol_route" in reading["clues"]
    assert reading["scene"] == scene
    assert storage.load_character() == before
    assert accepted
    gm = accepted[-1]
    record = ivr.accepted_record(gm)
    assert record["hard_validation"]["hard_valid"] and record["immutable"]
    assert ivr.verify_delivery_record(record)
    assert record["text"] == gm["player_facing_text"] == reading["visible"] == reading["publication"]
    assert gm["metadata"]["emission_debug"]["scene_momentum_composition"]["appended"] is False
    assert not any(tag.startswith("scene_momentum:") for tag in gm.get("tags", []))
    original_text = gm["player_facing_text"]
    result = apply_response_policy_enforcement(gm, response_policy={"prefer_scene_momentum": True},
        player_text="Read me the missing-patrol notice, not the tax lines.", scene_envelope=SCENE,
        session={}, world={}, resolution={"kind": "discover_clue", "success": True, "clue_text": CLUE})
    assert result["player_facing_text"] == original_text
    assert ivr.verify_delivery_record(ivr.accepted_record(result))
