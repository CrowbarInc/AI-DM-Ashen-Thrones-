"""PR-BA: nearby place-existence is world/adjudication knowledge, not earshot.

Synthetic kiln / loft / cellar fixtures. Frontier Gate is calibration residue only.
"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from game import storage
from game.adjudication import classify_adjudication_query, resolve_adjudication_query
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
from game.intent_parser import parse_freeform_to_action
from game.interaction_context import (
    _looks_like_local_observation_question,
    _looks_like_place_existence_question,
    extract_place_existence_subject,
    find_addressed_npc_id_for_turn,
    resolve_directed_social_entry,
    should_emit_observe_for_local_observation_parse,
)
from game.interaction_routing import choose_interaction_route, is_directed_dialogue
from game.gm import question_resolution_rule_check
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

LANTERN = "A cracked lantern hangs above the kiln door."
ASH = "Cold ash sits unused in the grate."
KILN_SUMMARY = "A cold kiln stands in a brick alcove."
DRYING_RACKS = "Drying racks stand under a cracked skylight."
BRINE_CASKS = "Brine casks line the south wall."
INVENTED_TAVERN = (
    "A marble tavern stands forty yards west, opens at dusk, and sells stew for two silver."
)
NOVEL_PLACE_Q = "Is there a charcoal lodge nearby?"
NPC_CATALOG = "no nearby npc presence"
SOCIAL_IGNORANCE = (
    "do not know enough to answer",
    "you're asking for a line i don't own",
    "the guard says",
)

GENERIC_ENGINE_FILES = (
    Path("game/interaction_context.py"),
    Path("game/adjudication.py"),
    Path("game/intent_parser.py"),
    Path("game/scene_destination_binding.py"),
    Path("game/interaction_routing.py"),
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
    summary=KILN_SUMMARY,
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
KILN_EMPTY = _envelope(
    "ember_kiln",
    location="Ember Kiln Alcove",
    summary=KILN_SUMMARY,
    visible_facts=[LANTERN, ASH],
    addressables=[],
    exits=[{"label": "To the brass quay", "target_scene_id": "brass_quay"}],
)
LOFT = _envelope(
    "salt_loft",
    location="Salt Loft",
    summary="Racks of drying salt crust the loft boards.",
    visible_facts=[DRYING_RACKS],
    addressables=[],
    interactables=[
        {
            "id": "drying_racks",
            "label": "Drying racks",
            "aliases": ["racks"],
            "type": "investigate",
        }
    ],
    exits=[{"label": "Down to the brine cellar", "target_scene_id": "brine_cellar"}],
)
CELLAR = _envelope(
    "brine_cellar",
    location="Brine Cellar",
    summary="A damp cellar holds casks of brine.",
    visible_facts=[BRINE_CASKS],
    addressables=[],
    exits=[{"label": "Up to the salt loft", "target_scene_id": "salt_loft"}],
)
TAVERN = _envelope(
    "rain_barrel_tavern",
    location="Rain Barrel Tavern",
    summary="A crowded tavern hums around a runner.",
    visible_facts=["A soot-dark taproom holds a rain barrel."],
    addressables=[],
    exits=[],
)
CEDAR = _envelope(
    "cedar_wharf",
    location="Cedar Wharf",
    summary="Cedar pilings stand in slack brown water.",
    visible_facts=["Cedar pilings stand in slack brown water."],
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
            "topics": [{"id": "mash_exists", "text": "The mash kettle is cold tonight."}],
        }
    ]
    return world


def _empty_world() -> dict:
    world = default_world()
    world["npcs"] = []
    return world


def _session(scene_id: str, visited: list[str] | None = None) -> dict:
    session = default_session()
    session["active_scene_id"] = scene_id
    session["visited_scene_ids"] = list(visited or [scene_id])
    return session


def _seed(tmp_path, monkeypatch, first: dict, *more: dict, world: dict | None = None) -> None:
    _patch_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path(first["scene"]["id"]), first)
    seen = {first["scene"]["id"]}
    for extra in more:
        storage._save_json(storage.scene_path(extra["scene"]["id"]), extra)
        seen.add(extra["scene"]["id"])
    for extra_id in ("frontier_gate", "market_quarter", "old_milestone"):
        if extra_id not in seen:
            storage._save_json(storage.scene_path(extra_id), default_scene(extra_id))
    storage._save_json(storage.WORLD_PATH, world if world is not None else _empty_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = _session(first["scene"]["id"])
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


def _adj(text: str, scene: dict, world: dict | None = None, session: dict | None = None) -> dict | None:
    sess = session if session is not None else _session(scene["scene"]["id"])
    w = world if world is not None else _empty_world()
    return resolve_adjudication_query(
        text,
        scene=scene,
        session=sess,
        world=w,
        character=default_character(),
    )


def test_tavern_nearby_is_place_existence_not_earshot():
    assert not _looks_like_local_observation_question("Is there a tavern nearby?")
    assert _looks_like_place_existence_question("Is there a tavern nearby?")
    assert extract_place_existence_subject("Is there a tavern nearby?") == "a tavern"
    assert classify_adjudication_query(
        "Is there a tavern nearby?", session={}, world={}, scene=KILN_EMPTY
    ) == "perception_query"
    out = _adj("Is there a tavern nearby?", KILN_EMPTY)
    assert out is not None
    assert out.get("answer_type") == "place_existence_unknown"
    assert NPC_CATALOG not in str(out.get("player_facing_text") or "").lower()
    assert _has(out.get("player_facing_text") or "", "no nearby tavern", "currently established")


def test_novel_place_existence_paraphrases_share_owner():
    for text, subject in (
        ("Is there an inn around here?", "an inn"),
        ("Are there stables close by?", "stables"),
        ("Is there a market in this area?", "a market"),
        (NOVEL_PLACE_Q, "a charcoal lodge"),
    ):
        assert _looks_like_place_existence_question(text), text
        assert extract_place_existence_subject(text) == subject, text
        assert classify_adjudication_query(
            text, session={}, world={}, scene=KILN_EMPTY
        ) == "perception_query", text
        out = _adj(text, KILN_EMPTY)
        assert out is not None, text
        assert out.get("answer_type") == "place_existence_unknown", text
        assert NPC_CATALOG not in str(out.get("player_facing_text") or "").lower(), text


def test_whats_nearby_remains_observe():
    assert _looks_like_local_observation_question("What's nearby?")
    assert should_emit_observe_for_local_observation_parse("What's nearby?", KILN)
    assert classify_adjudication_query(
        "What's nearby?", session={}, world={}, scene=KILN
    ) is None
    parsed = parse_freeform_to_action(
        "What's nearby?", KILN, session=_session("ember_kiln"), world=_kiln_world()
    )
    assert parsed is not None
    assert parsed.get("type") == "observe"


def test_who_and_anyone_nearby_remain_person_presence():
    session = _session("ember_kiln")
    world = _empty_world()
    for text in ("Who is nearby?", "Is anyone nearby?"):
        assert not _looks_like_place_existence_question(text), text
        assert classify_adjudication_query(
            text, session=session, world=world, scene=KILN_EMPTY
        ) == "perception_query", text
        out = _adj(text, KILN_EMPTY, world=world, session=session)
        assert out is not None, text
        assert NPC_CATALOG in str(out.get("player_facing_text") or "").lower(), text


def test_earshot_still_lists_present_npc():
    session = _session("ember_kiln")
    world = _kiln_world()
    assert classify_adjudication_query(
        "Is anyone else in earshot?", session=session, world=world, scene=KILN
    ) == "perception_query"
    out = _adj("Is anyone else in earshot?", KILN, world=world, session=session)
    assert out is not None
    assert "night porter" in str(out.get("player_facing_text") or "").lower()


def test_rules_and_feasibility_remain_adjudication():
    session = _session("ember_kiln")
    world = _empty_world()
    assert classify_adjudication_query(
        "Do I need to roll Perception?", session=session, world=world, scene=KILN_EMPTY
    ) == "roll_requirement_query"
    assert classify_adjudication_query(
        "Can I sneak past without being seen?", session=session, world=world, scene=KILN_EMPTY
    ) == "action_feasibility_query"
    assert classify_adjudication_query(
        "Can I reach the tavern before dark?", session=session, world=world, scene=KILN_EMPTY
    ) == "action_feasibility_query"


def test_distance_question_is_not_local_observation():
    text = "How far is the tavern?"
    assert not _looks_like_local_observation_question(text)
    assert not _looks_like_place_existence_question(text)
    assert classify_adjudication_query(
        text, session={}, world={}, scene=KILN_EMPTY
    ) == "perception_query"
    parsed = parse_freeform_to_action(
        text, KILN_EMPTY, session=_session("ember_kiln"), world=_empty_world()
    )
    assert parsed is None or parsed.get("type") != "observe"
    out = _adj(text, KILN_EMPTY)
    assert out is not None
    assert "forty" not in str(out.get("player_facing_text") or "").lower()
    assert not _has(out.get("player_facing_text") or "", "establishes")


def test_current_scene_place_can_be_established():
    out = _adj("Is there a salt loft nearby?", LOFT)
    assert out is not None
    assert out.get("answer_type") == "place_existence"
    facing = str(out.get("player_facing_text") or "")
    assert "salt loft" in facing.lower()
    assert "there is" in facing.lower()
    assert NPC_CATALOG not in facing.lower()


def test_authored_exit_is_known_nearby_destination_not_travel():
    text = "Is there a salt loft nearby?"
    parsed = parse_freeform_to_action(
        text, CELLAR, session=_session("brine_cellar"), world=_empty_world()
    )
    assert parsed is None or parsed.get("type") != "scene_transition"
    out = _adj(text, CELLAR)
    assert out is not None
    assert out.get("answer_type") == "place_existence"
    facing = str(out.get("player_facing_text") or "")
    assert "salt loft" in facing.lower()
    assert "destination" in facing.lower()
    assert NPC_CATALOG not in facing.lower()


def test_place_known_elsewhere_is_not_asserted_nearby():
    session = _session("ember_kiln", ["rain_barrel_tavern", "ember_kiln"])
    out = _adj("Is there a tavern nearby?", KILN_EMPTY, session=session)
    assert out is not None
    assert out.get("answer_type") == "place_existence_unknown"
    facing = str(out.get("player_facing_text") or "").lower()
    assert "rain barrel" not in facing
    assert "destination" not in facing
    assert _has(facing, "no nearby tavern", "currently established")


def test_unknown_place_fails_closed_without_invention():
    out = _adj(NOVEL_PLACE_Q, KILN_EMPTY)
    assert out is not None
    facing = str(out.get("player_facing_text") or "")
    assert _has(facing, "no nearby charcoal lodge", "currently established")
    assert not _has(facing, "forty", "west", "silver", "dusk", "marble")


def test_directed_place_question_keeps_social_ownership():
    session = _session("ember_kiln")
    world = _kiln_world()
    text = "Night Porter, is there a tavern nearby?"
    assert find_addressed_npc_id_for_turn(text, session, world, KILN) == "night_porter"
    entry = resolve_directed_social_entry(
        session=session, scene=KILN, world=world, segmented_turn=None, raw_text=text
    )
    assert entry.get("should_route_social") is True
    assert entry.get("target_actor_id") == "night_porter"
    assert classify_adjudication_query(
        text, session=session, world=world, scene=KILN
    ) is None


def test_sole_npc_does_not_steal_undirected_place_existence():
    session = _session("ember_kiln")
    world = _kiln_world()
    text = "Is there a tavern nearby?"
    assert find_addressed_npc_id_for_turn(text, session, world, KILN) is None
    assert is_directed_dialogue(text, scene=KILN, session=session, world=world) is False
    assert choose_interaction_route(text, scene=KILN, session=session, world=world) != "dialogue"
    entry = resolve_directed_social_entry(
        session=session, scene=KILN, world=world, segmented_turn=None, raw_text=text
    )
    assert entry.get("should_route_social") is False
    assert classify_adjudication_query(
        text, session=session, world=world, scene=KILN
    ) == "perception_query"
    out = _adj(text, KILN, world=world, session=session)
    assert out is not None
    assert out.get("answer_type") == "place_existence_unknown"
    assert find_addressed_npc_id_for_turn(
        "Where did the missing patrol go?", session, world, KILN
    ) == "night_porter"


def test_http_tavern_nearby_is_not_npc_catalog(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN_EMPTY)
    data = _chat(monkeypatch, "Is there a tavern nearby?", INVENTED_TAVERN)
    assert _kind(data) == "adjudication_query"
    facing = _facing(data)
    assert NPC_CATALOG not in facing.lower()
    assert _has(facing, "no nearby tavern", "currently established")
    assert "tavern" in facing.lower()
    assert not _has(facing, "forty", "west", "two silver", "dusk")


def test_http_novel_paraphrase_and_loft_presence(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, LOFT, CELLAR)
    unknown = _chat(monkeypatch, NOVEL_PLACE_Q, INVENTED_TAVERN)
    assert _kind(unknown) == "adjudication_query"
    assert _has(_facing(unknown), "no nearby charcoal lodge", "currently established")
    assert NPC_CATALOG not in _facing(unknown).lower()
    present = _chat(monkeypatch, "Is there a salt loft nearby?", INVENTED_TAVERN)
    assert _kind(present) == "adjudication_query"
    assert "salt loft" in _facing(present).lower()
    assert "there is" in _facing(present).lower()


def test_http_exit_destination_and_elsewhere_not_nearby(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, CELLAR, LOFT, TAVERN)
    dest = _chat(monkeypatch, "Is there a salt loft nearby?", INVENTED_TAVERN)
    assert _kind(dest) == "adjudication_query"
    assert "destination" in _facing(dest).lower()
    session = storage.load_session()
    session["active_scene_id"] = "ember_kiln"
    session["visited_scene_ids"] = ["rain_barrel_tavern", "brine_cellar", "ember_kiln"]
    storage.save_session(session)
    storage._save_json(storage.scene_path("ember_kiln"), KILN_EMPTY)
    elsewhere = _chat(monkeypatch, "Is there a tavern nearby?", INVENTED_TAVERN)
    facing = _facing(elsewhere).lower()
    assert _has(facing, "no nearby tavern", "currently established")
    assert "rain barrel" not in facing
    assert "destination" not in facing


def test_http_whats_nearby_and_who_nearby_keep_owners(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, world=_kiln_world())
    observe = _chat(monkeypatch, "What's nearby?", "I don't know what's nearby.")
    assert _kind(observe) == "observe"
    assert NPC_CATALOG not in _facing(observe).lower()
    who = _chat(monkeypatch, "Who is nearby?", INVENTED_TAVERN)
    assert _kind(who) in {"adjudication_query", "question"}
    assert "forty yards" not in _facing(who).lower()


def test_http_directed_place_question_is_not_earshot_catalog(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, world=_kiln_world())
    data = _chat(monkeypatch, "Night Porter, is there a tavern nearby?", INVENTED_TAVERN)
    assert _kind(data) != "observe"
    facing = _facing(data).lower()
    assert NPC_CATALOG not in facing
    if _kind(data) == "adjudication_query":
        assert _has(facing, "no nearby tavern", "currently established")
    else:
        assert not _has(facing, "forty yards", "two silver")


def test_http_sole_npc_undirected_place_stays_world_knowledge(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, world=_kiln_world())
    data = _chat(monkeypatch, "Is there a tavern nearby?", INVENTED_TAVERN)
    assert _kind(data) == "adjudication_query"
    facing = _facing(data).lower()
    assert NPC_CATALOG not in facing
    assert _has(facing, "no nearby tavern", "currently established")
    assert not any(needle in facing for needle in SOCIAL_IGNORANCE)


def test_http_cedar_generalization_unknown_place(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, CEDAR)
    data = _chat(monkeypatch, "Are there drying racks close by?", INVENTED_TAVERN)
    assert _kind(data) == "adjudication_query"
    facing = _facing(data).lower()
    assert NPC_CATALOG not in facing
    assert _has(facing, "no nearby drying racks", "currently established")


def test_visible_fact_can_establish_current_place():
    out = _adj("Are there drying racks close by?", LOFT)
    assert out is not None
    assert out.get("answer_type") == "place_existence"
    assert "drying racks" in str(out.get("player_facing_text") or "").lower()


def test_pray_local_observation_and_praz_observe_bind_remain():
    session = _session("ember_kiln")
    world = _kiln_world()
    assert find_addressed_npc_id_for_turn("What's nearby?", session, world, KILN) is None
    parsed = parse_freeform_to_action(
        "What's nearby?", KILN, session=session, world=world
    )
    assert parsed is not None and parsed.get("type") == "observe"
    assert classify_adjudication_query(
        "What's nearby?", session=session, world=world, scene=KILN
    ) is None


def test_question_rule_does_not_rewrite_resolved_place_existence():
    check = question_resolution_rule_check(
        player_text="Is there a tavern nearby?",
        gm_reply_text="No nearby tavern is currently established in this scene.",
        resolution={"kind": "adjudication_query"},
    )
    assert check.get("applies") is False
    observe = question_resolution_rule_check(
        player_text="What's nearby?",
        gm_reply_text="A cracked lantern hangs above the kiln door.",
        resolution={"kind": "observe"},
    )
    assert observe.get("applies") is False


def test_generic_engine_files_have_no_frontier_or_phrase_special_case():
    lowered = "\n".join(path.read_text(encoding="utf-8").lower() for path in GENERIC_ENGINE_FILES)
    assert "frontier_gate" not in lowered
    assert 'is there a tavern nearby?' not in lowered
    assert "charcoal lodge" not in lowered
