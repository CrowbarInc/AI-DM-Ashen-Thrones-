"""PR-BB: first-person can+known-perception-verb family, not passive residue.

The existing local-observation classifier already treated perceive/observe as
observation verbs on the do/does branch. The can branch omitted them. This file
locks that composition and preserves the accepted passive miss.
"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from game import storage
from game.adjudication import classify_adjudication_query
from game.api import app
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)
from game.diegetic_fallback_narration import observe_nothing_new_fallback_line
from game.gm import question_resolution_rule_check
from game.intent_parser import parse_freeform_to_action
from game.interaction_context import (
    _looks_like_local_observation_question,
    find_addressed_npc_id_for_turn,
    should_emit_observe_for_local_observation_parse,
)
from game.interaction_routing import choose_interaction_route, is_directed_dialogue
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

LANTERN = "A cracked lantern hangs above the kiln door."
ASH = "Cold ash sits unused in the grate."
CEDAR_PILING = "Cedar pilings stand in slack brown water."
KNOWN_PASSIVE_MISS = "What can be perceived from where I stand?"
CAN_PERCEPTION_FAMILY = (
    "What can I perceive?",
    "What can I perceive around me?",
    "What can I perceive from here?",
    "What can I observe?",
    "What can we perceive from here?",
)
GENERIC_ENGINE_FILES = (
    Path("game/interaction_context.py"),
    Path("game/intent_parser.py"),
)


def _envelope(scene_id: str, **extra) -> dict:
    scene = default_scene(scene_id)
    inner = scene["scene"]
    inner["id"] = scene_id
    inner["location"] = extra.pop("location", scene_id.replace("_", " ").title())
    inner.update(extra)
    return scene


KILN = _envelope(
    "ember_kiln",
    location="Ember Kiln Alcove",
    summary="A cold kiln stands in a brick alcove.",
    visible_facts=[LANTERN, ASH],
    addressables=[
        {
            "id": "night_porter",
            "name": "Night Porter",
            "scene_id": "ember_kiln",
            "kind": "npc",
            "addressable": True,
            "aliases": ["porter"],
        }
    ],
    exits=[{"label": "To the brass quay", "target_scene_id": "brass_quay"}],
)
CEDAR = _envelope(
    "cedar_wharf",
    location="Cedar Wharf",
    summary="Cedar pilings stand in slack brown water.",
    visible_facts=[CEDAR_PILING],
    addressables=[],
    exits=[],
)


def _kiln_world() -> dict:
    world = default_world()
    world["npcs"] = [
        {
            "id": "night_porter",
            "name": "Night Porter",
            "location": "ember_kiln",
            "aliases": ["porter"],
        }
    ]
    return world


def _session(scene_id: str = "ember_kiln") -> dict:
    session = default_session()
    session["active_scene_id"] = scene_id
    session["visited_scene_ids"] = [scene_id]
    return session


def _parse(text: str, envelope: dict = KILN, world: dict | None = None):
    return parse_freeform_to_action(
        text,
        envelope,
        session=_session(envelope["scene"]["id"]),
        world=world if world is not None else _kiln_world(),
    )


def _assert_observe(text: str, envelope: dict = KILN) -> None:
    assert _looks_like_local_observation_question(text), text
    assert should_emit_observe_for_local_observation_parse(text, envelope), text
    parsed = _parse(text, envelope)
    assert parsed is not None, text
    assert parsed.get("type") == "observe", text
    assert (parsed.get("metadata") or {}).get("parser_lane") == "local_observation_question", text
    assert classify_adjudication_query(
        text, session=_session(envelope["scene"]["id"]), world=_kiln_world(), scene=envelope
    ) is None, text


def _seed(tmp_path, monkeypatch, scene: dict) -> None:
    _patch_storage(tmp_path, monkeypatch)
    scene_id = scene["scene"]["id"]
    storage._save_json(storage.scene_path(scene_id), scene)
    for extra_id in ("frontier_gate", "market_quarter", "old_milestone"):
        if extra_id != scene_id:
            storage._save_json(storage.scene_path(extra_id), default_scene(extra_id))
    storage._save_json(storage.WORLD_PATH, _kiln_world() if scene_id == "ember_kiln" else default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = _session(scene_id)
    session["turn_counter"] = 2
    storage.save_session(session)
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _chat(monkeypatch, text: str, gm_text: str) -> dict:
    monkeypatch.setattr("game.api.call_gpt", lambda _messages: _gm_response(gm_text))
    client = TestClient(app)
    resp = client.post("/api/chat", json={"text": text})
    assert resp.status_code == 200
    return resp.json()


def _facing(data: dict) -> str:
    return str((data.get("gm_output") or {}).get("player_facing_text") or "")


def _kind(data: dict) -> str:
    return str((data.get("resolution") or {}).get("kind") or "")


def test_ordinary_imperative_look_around_is_existing_observe():
    parsed = _parse("I look around.")
    assert parsed is not None
    assert parsed.get("type") == "observe"


def test_ordinary_question_form_observation_remains_observe():
    for text in ("What do I see?", "What can I see?", "What's around me?", "What's nearby?"):
        _assert_observe(text)


def test_do_perceive_already_reached_observe():
    _assert_observe("What do I perceive?")


def test_can_plus_known_perception_verb_family_reaches_observe():
    for text in CAN_PERCEPTION_FAMILY:
        _assert_observe(text)


def test_novel_can_observe_around_me_reaches_observe():
    _assert_observe("What can I observe around me?")


def test_known_passive_standpoint_sentence_remains_unsupported():
    text = KNOWN_PASSIVE_MISS
    assert not _looks_like_local_observation_question(text)
    parsed = _parse(text)
    assert parsed is None or parsed.get("type") != "observe"


def test_player_current_viewpoint_can_perceive_does_not_bind_sole_npc():
    session = _session()
    world = _kiln_world()
    text = "What can I perceive from here?"
    assert find_addressed_npc_id_for_turn(text, session, world, KILN) is None
    assert is_directed_dialogue(text, scene=KILN, session=session, world=world) is False
    assert choose_interaction_route(text, scene=KILN, session=session, world=world) != "dialogue"


def test_npc_perception_contrast_stays_outside_local_observation():
    assert not _looks_like_local_observation_question("What does the guard perceive?")
    assert not _looks_like_local_observation_question("What does the guard see?")
    assert not _looks_like_local_observation_question("Who can see me?")
    assert not _looks_like_local_observation_question("Can the guard see me?")


def test_listen_and_feasibility_contrasts_are_not_local_observation():
    assert not _looks_like_local_observation_question("Can I hear anything?")
    assert not _looks_like_local_observation_question("Can I get there before dark?")
    assert classify_adjudication_query(
        "Can I get there before dark?",
        session=_session(),
        world=_kiln_world(),
        scene=KILN,
    ) == "action_feasibility_query"


def test_person_presence_and_place_existence_contrasts_remain():
    assert not _looks_like_local_observation_question("Who is nearby?")
    assert not _looks_like_local_observation_question("Is anyone nearby?")
    assert not _looks_like_local_observation_question("Is there a tavern nearby?")
    tavern = classify_adjudication_query(
        "Is there a tavern nearby?",
        session=_session(),
        world=_kiln_world(),
        scene=KILN,
    )
    assert tavern == "perception_query"
    who = classify_adjudication_query(
        "Who is nearby?",
        session=_session(),
        world=default_world(),
        scene=_envelope("ember_kiln", location="Ember Kiln Alcove", addressables=[], exits=[]),
    )
    assert who == "perception_query"
    distance = classify_adjudication_query(
        "How far away is the quay?",
        session=_session(),
        world=default_world(),
        scene=_envelope("ember_kiln", location="Ember Kiln Alcove", addressables=[], exits=[]),
    )
    assert distance == "perception_query"


def test_question_rule_does_not_rewrite_executed_can_perceive_observe():
    check = question_resolution_rule_check(
        player_text="What can I perceive?",
        gm_reply_text=LANTERN,
        resolution={"kind": "observe", "metadata": {"parser_lane": "local_observation_question"}},
    )
    assert check.get("applies") is False


def test_http_can_perceive_is_observe_not_feasibility_or_social(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN)
    data = _chat(monkeypatch, "What can I perceive?", "I need a more concrete action or target.")
    facing = _facing(data).lower()
    assert _kind(data) == "observe"
    assert "more concrete action" not in facing
    assert "no nearby npc presence" not in facing
    assert "lantern" in facing or "ash" in facing or "kiln" in facing or facing == observe_nothing_new_fallback_line().lower()


def test_http_can_observe_generalizes_off_frontier_wording(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, CEDAR)
    data = _chat(monkeypatch, "What can I observe around me?", "A marble tavern stands nearby.")
    facing = _facing(data).lower()
    assert _kind(data) == "observe"
    assert "more concrete action" not in facing
    assert (
        "piling" in facing
        or "cedar" in facing
        or facing == observe_nothing_new_fallback_line().lower()
    )


def test_generic_engine_files_have_no_phrase_special_case():
    lowered = "\n".join(path.read_text(encoding="utf-8").lower() for path in GENERIC_ENGINE_FILES)
    assert "frontier_gate" not in lowered
    assert "what can be perceived from where i stand" not in lowered
    assert "what can i perceive from here" not in lowered
