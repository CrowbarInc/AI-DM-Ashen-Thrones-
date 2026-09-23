"""PR-BD: interactable references resolve through authored names/aliases and
ordinary plural stemming, not synonym invention.

Silent-e plurals (notices/stones/slates/chutes) must match the singular
authored surface. Loose leading-modifier paraphrases may remain unbound.
Mentioned nouns and off-scene objects must not become local interactables.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from game import storage
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
from game.exploration import resolve_exploration_action
from game.intent_parser import parse_freeform_to_action
from game.referenced_surface import (
    AUTHORITY_AUTHORED_HIDDEN,
    AUTHORITY_AUTHORED_INTERACTABLE,
    AUTHORITY_AUTHORED_VISIBLE_FEATURE,
    AUTHORITY_UNSUPPORTED,
    _stem_token,
    classify_referenced_surface,
)
from game.scene_actions import normalize_scene_action
from game.social import parse_social_intent
from game.storage import get_scene_runtime
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

TARIFF_FACT = "Dock fees rise after the second horn."
NOTICE_FACT = "The missing patrol was last seen taking the northwest mud track past the crates."
PRINT_FACT = (
    "Faint overlapping prints mark the mud around the old milestone, "
    "but their number, origin, and direction stay unclear."
)
GENERIC_ENGINE_FILES = (
    Path("game/referenced_surface.py"),
    Path("game/intent_parser.py"),
    Path("game/exploration.py"),
)


def _mill_scene() -> dict:
    return {
        "scene": {
            "id": "mill_loft",
            "location": "Mill Loft",
            "summary": "A dry loft, a grain hopper, and a tariff slate.",
            "visible_facts": [
                "A soot-stained skylight leaks pale noon light onto the loft floor.",
                "Sacks of cracked maize lean against the hopper braces.",
                "A tariff slate hangs from a nail by the loft stair.",
            ],
            "hidden_facts": ["A brass token is sealed under the grain hopper."],
            "discoverable_clues": [{"id": "tariff_slate_fees", "text": TARIFF_FACT}],
            "interactables": [
                {
                    "id": "grain_hopper",
                    "label": "Grain hopper",
                    "aliases": ["hopper", "feed chute"],
                    "type": "investigate",
                },
                {
                    "id": "tariff_slate",
                    "label": "Tariff slate",
                    "aliases": ["slate", "fee slate"],
                    "type": "read",
                    "reveals_clue": "tariff_slate_fees",
                },
            ],
            "exits": [{"label": "Climb down to the quay", "target_scene_id": "cedar_wharf"}],
            "enemies": [],
            "actions": [],
        }
    }


def _frontier() -> dict:
    return json.loads(Path("data/scenes/frontier_gate.json").read_text(encoding="utf-8"))


def _milestone() -> dict:
    return json.loads(Path("data/scenes/old_milestone.json").read_text(encoding="utf-8"))


def _seed(tmp_path, monkeypatch, envelope: dict):
    _patch_storage(tmp_path, monkeypatch)
    sid = envelope["scene"]["id"]
    storage._save_json(storage.scene_path(sid), envelope)
    for extra_id in ("frontier_gate", "market_quarter", "old_milestone", "cedar_wharf"):
        if extra_id == sid:
            continue
        extra = default_scene(extra_id)
        if extra_id == "old_milestone":
            extra = _milestone()
        storage._save_json(storage.scene_path(extra_id), extra)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = sid
    session["visited_scene_ids"] = [sid]
    storage.save_session(session)
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    return sid


def _chat(monkeypatch, text: str, gm_text: str):
    monkeypatch.setattr("game.api.call_gpt", lambda _messages: _gm_response(gm_text))
    client = TestClient(app)
    resp = client.post("/api/chat", json={"text": text})
    assert resp.status_code == 200
    return resp.json()


def _facing(data: dict) -> str:
    return str((data.get("gm_output") or {}).get("player_facing_text") or "")


def _bind(text: str, scene: dict) -> dict:
    return classify_referenced_surface(text, scene)


def test_stem_collapses_silent_e_plurals_without_overcutting_true_es():
    assert _stem_token("notices") == "notice"
    assert _stem_token("stones") == "stone"
    assert _stem_token("slates") == "slate"
    assert _stem_token("chutes") == "chute"
    assert _stem_token("crates") == "crate"
    assert _stem_token("boards") == "board"
    assert _stem_token("maps") == "map"
    assert _stem_token("boxes") == "box"
    assert _stem_token("watches") == "watch"
    assert _stem_token("dishes") == "dish"
    assert _stem_token("classes") == "class"
    assert _stem_token("taxes") == "tax"


def test_canonical_and_ordinary_notice_board_references_bind():
    scene = _frontier()
    for text in (
        "I read the notice board.",
        "I look at the board.",
        "I read the notice.",
        "I read the notices.",
        "I read the curfew notice.",
    ):
        classified = _bind(text, scene)
        parsed = parse_freeform_to_action(text, scene)
        assert classified["authority"] == AUTHORITY_AUTHORED_INTERACTABLE, text
        assert classified["interactable_id"] == "notice_board", text
        assert parsed is not None
        assert parsed.get("type") == "investigate"
        assert parsed.get("target_id") == "notice_board"


def test_posted_notices_stays_unbound_loose_paraphrase():
    classified = _bind("I read the posted notices.", _frontier())
    assert classified["interactable_id"] == ""
    assert classified["authority"] in {
        AUTHORITY_AUTHORED_VISIBLE_FEATURE,
        AUTHORITY_UNSUPPORTED,
    }
    parsed = parse_freeform_to_action("I read the posted notices.", _frontier())
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert parsed.get("target_id") != "notice_board"


def test_leading_modifier_paraphrases_do_not_invent_or_bind():
    frontier = _frontier()
    mill = _mill_scene()
    milestone = _milestone()
    assert _bind("I inspect the wooden board.", frontier)["authority"] == AUTHORITY_UNSUPPORTED
    assert _bind("I read the public notices.", frontier)["interactable_id"] == ""
    assert _bind("I inspect the wooden hopper.", mill)["authority"] == AUTHORITY_UNSUPPORTED
    assert _bind("I examine the muddy milestone.", milestone)["authority"] == AUTHORITY_UNSUPPORTED


def test_silent_e_plurals_bind_unrelated_authored_interactables():
    mill = _mill_scene()
    milestone = _milestone()
    slates = _bind("I read the slates.", mill)
    chutes = _bind("I examine the chutes.", mill)
    stones = _bind("I look at the stones.", milestone)
    assert slates["authority"] == AUTHORITY_AUTHORED_INTERACTABLE
    assert slates["interactable_id"] == "tariff_slate"
    assert chutes["authority"] == AUTHORITY_AUTHORED_INTERACTABLE
    assert chutes["interactable_id"] == "grain_hopper"
    assert stones["authority"] == AUTHORITY_AUTHORED_INTERACTABLE
    assert stones["interactable_id"] == "milestone"
    for text, scene, expected in (
        ("I read the slates.", mill, "tariff_slate"),
        ("I examine the chutes.", mill, "grain_hopper"),
        ("I look at the stones.", milestone, "milestone"),
        ("I inspect the grain hopper.", mill, "grain_hopper"),
        ("I read the tariff slate.", mill, "tariff_slate"),
        ("I examine the weathered milestone.", milestone, "milestone"),
        ("I look at the footprints.", milestone, "prints"),
    ):
        parsed = parse_freeform_to_action(text, scene)
        assert parsed is not None, text
        assert parsed.get("type") == "investigate", text
        assert parsed.get("target_id") == expected, text


def test_incidental_and_unauthored_nouns_are_not_interactables():
    frontier = _frontier()
    mill = _mill_scene()
    for text, scene, allowed in (
        ("I inspect the rain.", frontier, {AUTHORITY_AUTHORED_VISIBLE_FEATURE}),
        ("I examine the banners.", frontier, {AUTHORITY_AUTHORED_VISIBLE_FEATURE}),
        ("I inspect the stew.", frontier, {AUTHORITY_AUTHORED_VISIBLE_FEATURE}),
        ("I inspect the crates.", frontier, {AUTHORITY_UNSUPPORTED}),
        ("I inspect the brass orrery.", frontier, {AUTHORITY_UNSUPPORTED}),
        ("I inspect the maize.", mill, {AUTHORITY_AUTHORED_VISIBLE_FEATURE}),
        ("I inspect the nail.", mill, {AUTHORITY_AUTHORED_VISIBLE_FEATURE}),
        ("I inspect the glass kiln.", mill, {AUTHORITY_UNSUPPORTED}),
        ("I inspect the brass token.", mill, {AUTHORITY_AUTHORED_HIDDEN}),
    ):
        classified = _bind(text, scene)
        assert classified["authority"] in allowed, text
        assert classified["interactable_id"] == ""


def test_offscene_interactables_do_not_resolve_locally():
    frontier = _frontier()
    mill = _mill_scene()
    milestone = _milestone()
    assert _bind("I examine the weathered milestone.", frontier)["authority"] == AUTHORITY_UNSUPPORTED
    assert _bind("I read the notice board.", mill)["authority"] == AUTHORITY_UNSUPPORTED
    assert _bind("I read the notice board.", milestone)["authority"] == AUTHORITY_UNSUPPORTED
    assert _bind("I read the posted notices.", milestone)["authority"] == AUTHORITY_UNSUPPORTED
    assert _bind("I look at the hopper.", frontier)["interactable_id"] == ""


def test_roster_board_remains_visible_not_notice_board():
    classified = _bind(
        "If the watch already has a commander on this, I'll check the roster board the serjeant is watching.",
        _frontier(),
    )
    assert classified["authority"] == AUTHORITY_AUTHORED_VISIBLE_FEATURE
    assert classified["interactable_id"] == ""
    assert "roster board" in classified["visible_fact"].lower()


def test_http_plural_notice_reads_authored_clue(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _frontier())
    data = _chat(monkeypatch, "I read the notices.", "As you watch the scene, rain needles the gate.")
    text = _facing(data).lower()
    res = data.get("resolution") or {}
    assert res.get("kind") in {"investigate", "discover_clue"}
    assert res.get("clue_id") == "notice_patrol_route" or "northwest" in text
    assert "northwest" in text
    assert "as you watch the scene" not in text


def test_http_plural_slate_reads_authored_clue(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _mill_scene())
    data = _chat(monkeypatch, "I read the slates.", "As you watch the scene, maize dust hangs in the loft.")
    text = _facing(data).lower()
    res = data.get("resolution") or {}
    assert res.get("kind") in {"investigate", "discover_clue"}
    assert res.get("clue_id") == "tariff_slate_fees" or "dock fees" in text
    assert "dock fees" in text


def test_already_searched_plural_notice_keeps_authored_sentence(tmp_path, monkeypatch):
    scene = _frontier()
    session: dict = {}
    rt = get_scene_runtime(session, "frontier_gate")
    rt["resolved_interactables"] = ["notice_board"]
    rt["searched_targets"] = ["notice_board"]
    parsed = parse_freeform_to_action("I read the notices.", scene)
    action = normalize_scene_action(parsed)
    res = resolve_exploration_action(
        scene,
        session,
        {},
        action,
        raw_player_text="I read the notices.",
        list_scene_ids=lambda: ["frontier_gate"],
    )
    assert res["kind"] == "already_searched"
    assert res.get("interactable_id") == "notice_board"


def test_destination_and_social_routing_still_own_their_phrases():
    frontier = _frontier()
    travel = parse_freeform_to_action("Follow the missing patrol rumor.", frontier)
    assert travel is not None
    assert travel.get("type") == "scene_transition"
    assert (travel.get("target_scene_id") or travel.get("targetSceneId")) == "old_milestone"
    world = default_world()
    world["npcs"] = [
        {
            "id": "guard_captain",
            "name": "Guard Captain",
            "location": "frontier_gate",
        }
    ]
    social = parse_social_intent(
        "I ask the guard captain about the missing patrol.",
        frontier,
        world,
    )
    assert social is not None
    assert social.get("type") == "question"
    assert "notice_board" not in str(social.get("target_id") or "")
    inspect = parse_freeform_to_action("I ask the guard captain about the missing patrol.", frontier)
    assert inspect is None or inspect.get("target_id") != "notice_board"


def test_generic_engine_has_no_posted_notices_special_case():
    for rel in GENERIC_ENGINE_FILES:
        lowered = rel.read_text(encoding="utf-8").lower()
        assert "posted notices" not in lowered
        assert "posted_notices" not in lowered
        assert "frontier_gate" not in lowered
        assert "notice_board" not in lowered
