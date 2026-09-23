"""PR-AZ: resolved question-form observe must not retry as social ignorance.

Synthetic kiln fixtures. Frontier Gate is calibration residue only.
"""
from __future__ import annotations

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
from game.gm_retry import detect_retry_failures
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
KILN_CLUE = "Soot handprints mark the kiln brick behind the grate."
KILN_STOCK = f"As you watch the scene, {LANTERN} {ASH}"
KILN_SUMMARY = "In Ember Kiln Alcove, a cold kiln stands in a brick alcove."
NOVEL_Q = "What is visible in this area?"
SOCIAL_IGNORANCE_NEEDLES = (
    "do not know enough to answer",
    "you're asking for a line i don't own",
    "i don't know.",
    "the guard says",
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
    hidden_facts=["A hidden stream rushes through a tunnel beneath the wall."],
    discoverable_clues=[{"id": "soot_prints", "text": KILN_CLUE}],
    interactables=[
        {
            "id": "kiln_grate",
            "label": "Kiln grate",
            "aliases": ["grate", "ash"],
            "type": "investigate",
            "reveals_clue": "soot_prints",
            "description": KILN_CLUE,
        }
    ],
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
            "topics": [{"id": "mash_exists", "text": "The mash kettle is cold tonight."}],
        }
    ]
    return world


def _seed(tmp_path, monkeypatch) -> None:
    _patch_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("ember_kiln"), KILN)
    for extra_id in ("frontier_gate", "market_quarter", "old_milestone"):
        storage._save_json(storage.scene_path(extra_id), default_scene(extra_id))
    storage._save_json(storage.WORLD_PATH, _kiln_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = "ember_kiln"
    session["visited_scene_ids"] = ["ember_kiln"]
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


def _has(text: str, *needles: str) -> bool:
    low = str(text or "").lower()
    return any(needle.lower() in low for needle in needles)


def _social_ignorance(text: str) -> bool:
    low = str(text or "").lower()
    return any(needle in low for needle in SOCIAL_IGNORANCE_NEEDLES)


def _observe_res(player_text: str) -> dict:
    return {
        "kind": "observe",
        "prompt": player_text,
        "metadata": {"parser_lane": "local_observation_question"},
    }


def test_pray_local_presence_classification_remains_observe():
    for text in ("What's nearby?", NOVEL_Q, "What can I see nearby?"):
        assert _looks_like_local_observation_question(text), text
        assert should_emit_observe_for_local_observation_parse(text, KILN), text
        session = default_session()
        session["active_scene_id"] = "ember_kiln"
        parsed = parse_freeform_to_action(text, KILN, session=session, world=_kiln_world())
        assert parsed is not None
        assert parsed.get("type") == "observe"


def test_sole_npc_does_not_address_untargeted_local_observation():
    session = default_session()
    session["active_scene_id"] = "ember_kiln"
    world = _kiln_world()
    assert find_addressed_npc_id_for_turn("What's nearby?", session, world, KILN) is None
    assert find_addressed_npc_id_for_turn(NOVEL_Q, session, world, KILN) is None
    assert (
        find_addressed_npc_id_for_turn("Where did the missing patrol go?", session, world, KILN)
        == "night_porter"
    )


def test_interrogative_form_alone_does_not_make_local_observation_directed_dialogue():
    session = default_session()
    session["active_scene_id"] = "ember_kiln"
    world = _kiln_world()
    for text in ("What's nearby?", NOVEL_Q):
        assert (
            is_directed_dialogue(text, scene=KILN, session=session, world=world) is False
        ), text
        assert (
            choose_interaction_route(text, scene=KILN, session=session, world=world)
            != "dialogue"
        ), text


def test_question_rule_does_not_apply_after_resolved_observe():
    for text, reply in (
        ("What's nearby?", KILN_SUMMARY),
        ("What's nearby?", observe_nothing_new_fallback_line()),
        (NOVEL_Q, KILN_STOCK),
    ):
        chk = question_resolution_rule_check(
            player_text=text,
            gm_reply_text=reply,
            resolution=_observe_res(text),
        )
        assert chk["applies"] is False
        assert chk["ok"] is True
        assert chk["reasons"] == []


def test_genuine_unresolved_question_still_uses_question_rule():
    chk = question_resolution_rule_check(
        player_text="Where did the missing patrol go?",
        gm_reply_text=KILN_SUMMARY,
        resolution={
            "kind": "question",
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": "night_porter",
                "npc_name": "Night Porter",
                "npc_reply_expected": True,
            },
        },
    )
    assert chk["applies"] is True
    assert chk["ok"] is False


def test_detect_retry_does_not_flag_resolved_observe_as_unresolved():
    session = default_session()
    session["active_scene_id"] = "ember_kiln"
    failures = detect_retry_failures(
        player_text="What's nearby?",
        gm_reply={"player_facing_text": KILN_SUMMARY, "tags": []},
        scene_envelope=KILN,
        session=session,
        world=_kiln_world(),
        resolution=_observe_res("What's nearby?"),
    )
    assert not any(str(f.get("failure_class") or "") == "unresolved_question" for f in failures)


def test_http_first_turn_question_form_observe_stays_observe(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    data = _chat(monkeypatch, "What's nearby?", "I don't know what's nearby.")
    facing = _facing(data)
    assert _kind(data) == "observe"
    assert not _social_ignorance(facing)
    assert _has(facing, "lantern", "ash", "kiln") or facing == observe_nothing_new_fallback_line()


def test_http_later_turn_question_form_observe_stays_observe(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    first = _chat(monkeypatch, "I look around.", KILN_STOCK)
    assert _kind(first) == "observe"
    _chat(monkeypatch, "I wait a moment.", "The kiln stays cold.")
    later = _chat(monkeypatch, "What's nearby?", "I don't know what's nearby.")
    facing = _facing(later)
    assert _kind(later) == "observe"
    assert not _social_ignorance(facing)
    assert facing == observe_nothing_new_fallback_line() or _has(facing, "lantern", "ash", "kiln")


def test_http_question_form_observe_after_social_is_not_social_ignorance(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    social = _chat(
        monkeypatch,
        "I ask the night porter whether the mash is still hot.",
        'Night Porter says, "The mash kettle is cold tonight."',
    )
    assert _kind(social) == "question"
    later = _chat(monkeypatch, "What's nearby?", "I don't know what's nearby.")
    facing = _facing(later)
    assert _kind(later) == "observe"
    assert not _social_ignorance(facing)
    assert facing == observe_nothing_new_fallback_line() or _has(facing, "lantern", "ash", "kiln")


def test_http_question_form_observe_after_investigation_stays_observe(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    inspected = _chat(monkeypatch, "I inspect the kiln grate.", f"You inspect the grate. {KILN_CLUE}")
    assert _kind(inspected) in {"discover_clue", "investigate"}
    later = _chat(monkeypatch, "What's nearby?", "I don't know what's nearby.")
    facing = _facing(later)
    assert _kind(later) == "observe"
    assert not _social_ignorance(facing)


def test_http_question_form_after_prior_observe_remains_owned(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    _chat(monkeypatch, "I look around.", KILN_STOCK)
    later = _chat(monkeypatch, NOVEL_Q, KILN_STOCK)
    facing = _facing(later)
    assert _kind(later) == "observe"
    assert not _social_ignorance(facing)
    assert facing == observe_nothing_new_fallback_line() or _has(facing, "lantern", "ash", "kiln")


def test_http_stock_bearing_question_form_observe_can_surface_scene(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    data = _chat(monkeypatch, NOVEL_Q, "I don't know what is visible.")
    facing = _facing(data)
    assert _kind(data) == "observe"
    assert not _social_ignorance(facing)
    assert _has(facing, "lantern", "ash", "kiln") or facing == observe_nothing_new_fallback_line()


def test_http_genuine_unresolved_question_still_uses_retry_path(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    _chat(monkeypatch, "I look around.", KILN_STOCK)
    later = _chat(monkeypatch, "Where did the missing patrol go?", "I have no idea where they went.")
    assert _kind(later) == "question"
    tags = [str(t) for t in ((later.get("gm_output") or {}).get("tags") or [])]
    joined = " ".join(tags).lower()
    assert "question_retry_fallback" in joined or "social_exchange" in joined or _social_ignorance(
        _facing(later)
    )


def test_adjudication_questions_remain_adjudication():
    session = default_session()
    world = default_world()
    bare = _envelope(
        "ember_kiln",
        location="Ember Kiln Alcove",
        visible_facts=[LANTERN],
        addressables=[],
    )
    assert classify_adjudication_query(
        "Who is nearby?", session=session, world=world, scene=bare
    ) == "perception_query"
    assert classify_adjudication_query(
        "Is anyone else in earshot?", session=session, world=world, scene=bare
    ) == "perception_query"
    assert classify_adjudication_query(
        "Do I need to roll Perception?", session=session, world=world, scene=bare
    ) == "roll_requirement_query"
