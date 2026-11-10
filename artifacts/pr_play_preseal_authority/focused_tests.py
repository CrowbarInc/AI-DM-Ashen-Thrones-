"""Provider-free tests of closed inspection preparation and its precedence."""
import copy

import pytest

from game import immutable_valid_response as ivr
from game import storage
from game.perception_grounding import apply_perception_non_invention_to_gm
from game.referenced_surface import metadata_from_classification
from tests.test_referenced_surface_grounding_inspection_resolution import (
    _mill_scene, _mill_world, _seed_scene_runtime, _chat, _facing,
)


def closed(authority="unsupported", **updates):
    resolution = {"kind": "investigate", "success": True, "state_changes": {},
                  "metadata": metadata_from_classification({"authority": authority})}
    resolution.update(updates)
    return resolution


def run(text, resolution, **kwargs):
    return ivr.run_preserve_if_valid(
        {"player_facing_text": text, "metadata": {}}, resolution=resolution,
        player_text="I inspect it.", scene=_mill_scene(), regenerate=None, **kwargs)


@pytest.mark.parametrize("authority,bad", [
    ("authored_hidden", "You pry up the hopper and pocket the brass token."),
    ("authored_abstract_reference", "The ledger lists eight named crews bound for Glassport."),
    ("unsupported", "The kiln schedule names four new overseers."),
])
def test_closed_candidates_are_prepared_validated_and_sealed(authority, bad):
    resolution = closed(authority)
    state = {"inventory": [], "active_scene_id": "mill_loft"}
    before = copy.deepcopy((state, resolution))
    gm = run(bad, resolution, session=state)
    assert (state, resolution) == before
    line = gm["player_facing_text"]
    assert line != bad
    assert not any(term in line.lower() for term in ("token", "sealed under", "pocket", "glassport", "eight", "overseers"))
    record = ivr.accepted_record(gm)
    assert record["immutable"] and record["hard_validation"]["hard_valid"]
    assert record["text"] == line and ivr.verify_delivery_record(record)
    note = gm["metadata"]["closed_surface_preparation"]
    assert note["original_candidate"] == bad
    assert note["classification"]["authority"] == authority
    assert note["eligible"] and note["applied"]
    assert note["prepared_candidate"] == line
    assert note["hard_validation"]["hard_valid"]
    assert note["published_text"] == line
    apply_perception_non_invention_to_gm(gm, resolution=resolution, scene=_mill_scene())
    assert gm["player_facing_text"] == line
    assert ivr.accepted_record(gm) == record


@pytest.mark.parametrize("player_request,bad,authority", [
    ("I inspect the brass token.", "You pry up the hopper and pocket the brass token.", "authored_hidden"),
    ("I inspect the shipping ledger.", "The ledger lists eight named crews bound for Glassport.", "authored_abstract_reference"),
    ("I inspect the glass kiln schedule.", "The kiln schedule names four new overseers.", "unsupported"),
])
def test_http_publication_matches_prepared_authority(tmp_path, monkeypatch, player_request, bad, authority):
    _seed_scene_runtime(tmp_path, monkeypatch, _mill_scene(), world=_mill_world())
    before_character = copy.deepcopy(storage.load_character())
    before_world = copy.deepcopy(storage.load_world())
    data = _chat(monkeypatch, player_request, bad)
    line = _facing(data)
    assert line and line != bad
    assert not any(term in line.lower() for term in ("token", "sealed under", "pocket", "glassport", "eight", "overseers"))
    assert storage.load_character() == before_character
    assert storage.load_world() == before_world
    session = storage.load_session()
    assert session["active_scene_id"] == "mill_loft"
    assert session["last_publication"]["visible"] == line
    log = storage.load_log()[-1]
    resolution = log["resolution"]
    assert resolution["metadata"]["referenced_surface_authority"] == authority
    assert resolution["state_changes"] == {}
    assert not resolution.get("clue_text") and not resolution.get("resolved_transition")
    runtime = session.get("scene_runtime", {}).get("mill_loft", {})
    assert not runtime.get("revealed_hidden_facts")
    # Player DTO carries no internal candidate rejection/hidden-target diagnostics.
    assert "closed_surface_preparation" not in str(data["gm_output"])


def test_selected_notice_clue_takes_precedence_over_stale_closed_classification():
    clue = "The missing patrol was last seen on the northwest mud track."
    resolution = closed("authored_hidden", clue_text=clue)
    gm = run(clue, resolution)
    assert gm["player_facing_text"] == clue
    assert not gm["metadata"]["closed_surface_preparation"]["eligible"]
    assert ivr.accepted_record(gm)["hard_validation"]["hard_valid"]


def test_resolved_acquisition_remains_narratable():
    resolution = closed("authored_hidden", state_changes={"items_added": ["silver key"]})
    text = "A silver key now rests among your possessions."
    gm = run(text, resolution)
    assert gm["player_facing_text"] == text
    assert ivr.accepted_record(gm)["hard_validation"]["hard_valid"]
    assert not gm["metadata"]["closed_surface_preparation"]["eligible"]


def test_resolved_physical_outcome_takes_precedence():
    resolution = closed(state_changes={"physical_operation": "open", "mutation": True})
    resolution["metadata"]["physical_adjudication"] = {"operation": "open", "target_id": "shutter", "mutation": True}
    text = "You open the wooden shutter."
    gm = run(text, resolution)
    assert gm["player_facing_text"] == text
    assert not gm["metadata"]["closed_surface_preparation"]["eligible"]


def test_genuine_travel_remains_narratable():
    resolution = closed(kind="travel", resolved_transition=True, target_scene_id="old_milestone")
    text = "You arrive at the old milestone."
    gm = run(text, resolution)
    assert gm["player_facing_text"] == text
    assert not gm["metadata"].get("closed_surface_preparation", {}).get("applied")


@pytest.mark.parametrize("text", [
    'The clerk says, "I prefer the morning shift."',
    'The clerk says, "I am not sure."',
    'The clerk asks, "Which record do you mean?"',
])
def test_ordinary_npc_speech_is_unchanged(text):
    gm = run(text, closed(kind="social"))
    assert gm["player_facing_text"] == text
    assert not gm["metadata"].get("closed_surface_preparation", {}).get("applied")


def test_sensory_improvisation_outside_closed_path_is_unchanged():
    text = "Rain taps the shutters."
    gm = run(text, {"kind": "observe", "success": True})
    assert gm["player_facing_text"] == text
    assert not gm["metadata"].get("closed_surface_preparation", {}).get("applied")


def test_no_classification_is_not_inferred_from_candidate_words():
    text = "The ledger lists eight named crews bound for Glassport."
    gm = run(text, {"kind": "investigate", "success": True})
    assert gm["player_facing_text"] == text
    assert not gm["metadata"].get("closed_surface_preparation", {}).get("applied")


def test_preparation_is_validated_before_replacement_and_never_retries(monkeypatch):
    calls = []
    real_check = ivr.validate_generated_response
    def fail_prepared(text, **kwargs):
        calls.append(text)
        checked = real_check(text, **kwargs)
        if "Nothing here matches" in text:
            return {**checked, "hard_valid": False, "reasons": ["injected_validation_failure"]}
        return checked
    monkeypatch.setattr(ivr, "validate_generated_response", fail_prepared)
    retries = []
    bad = "The kiln schedule names four new overseers."
    gm = ivr.run_preserve_if_valid({"player_facing_text": bad, "metadata": {}},
        resolution=closed(), player_text="I inspect it.", scene=_mill_scene(),
        regenerate=lambda _: retries.append(True))
    assert calls and retries == []
    assert "overseers" not in gm["player_facing_text"]
    assert gm["player_facing_text"] == ivr.TERMINAL_FALLBACK
    assert not ivr.effects_allowed(gm)
    assert not gm["metadata"]["closed_surface_preparation"]["applied"]


def test_already_accepted_text_is_never_reprepared():
    gm = run("Rain taps the shutters.", {"kind": "observe", "success": True})
    before = copy.deepcopy(gm)
    assert ivr.run_preserve_if_valid(gm, resolution=closed(), player_text="I inspect it.", regenerate=None) == before

