"""PR-AY: local-presence questions use observe, not earshot catalog ignorance.

Synthetic kiln / quay / cedar fixtures. Frontier Gate is calibration residue only.
"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from game import storage
from game.adjudication import classify_adjudication_query, resolve_adjudication_query
from game.api import app
from game.clues import add_clue_to_knowledge
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
from game.interaction_context import (
    _looks_like_local_observation_question,
    should_emit_observe_for_local_observation_parse,
)
from game.intent_parser import looks_like_local_physical_movement, parse_freeform_to_action
from game.perception_grounding import (
    classify_perception_invention,
    observation_recent_use_should_record,
)
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

LANTERN = "A cracked lantern hangs above the kiln door."
ASH = "Cold ash sits unused in the grate."
KILN_CLUE = "Soot handprints mark the kiln brick behind the grate."
KILN_STOCK = f"As you watch the scene, {LANTERN} {ASH}"
RINGS = "Copper mooring rings stud the quay stones."
LEDGER = "A tide ledger flutters on a rusted nail."
QUAY_STOCK = f"As you watch the scene, {RINGS} {LEDGER}"
HIDDEN_STREAM = "A hidden stream rushes through a tunnel beneath the wall."
CEDAR_PILING = "Cedar pilings stand in slack brown water."
CEDAR_HAWSER = "A coiled hemp hawser rests on the lowest plank."
INVENTED_NEARBY = "A marble fountain and a tavern sign stand nearby."

LOCAL_PRESENCE = (
    "What's nearby?",
    "What's around here?",
    "What is around me?",
    "What can I see nearby?",
    "What is close by?",
    "What's in this area?",
    "What's in my immediate surroundings?",
)

GENERIC_ENGINE_FILES = (
    Path("game/interaction_context.py"),
    Path("game/adjudication.py"),
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
    hidden_facts=[HIDDEN_STREAM],
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
    addressables=[],
    exits=[{"label": "To the brass quay", "target_scene_id": "brass_quay"}],
)
QUAY = _envelope(
    "brass_quay",
    location="Brass Quay",
    summary="A deserted quay leans over black water.",
    visible_facts=[RINGS, LEDGER],
    hidden_facts=[],
    discoverable_clues=[],
    interactables=[
        {
            "id": "tide_ledger",
            "label": "Tide ledger",
            "aliases": ["ledger", "nail"],
            "type": "investigate",
            "description": LEDGER,
        }
    ],
    addressables=[],
    exits=[{"label": "To the ember kiln", "target_scene_id": "ember_kiln"}],
)
CEDAR = _envelope(
    "cedar_wharf",
    location="Cedar Wharf",
    summary="Cedar pilings stand in slack brown water.",
    visible_facts=[CEDAR_PILING, CEDAR_HAWSER],
    hidden_facts=[],
    discoverable_clues=[],
    interactables=[],
    addressables=[],
    exits=[],
)
BARREN = _envelope(
    "barren_alcove",
    location="Barren Alcove",
    summary="An empty brick alcove holds no furnishings.",
    visible_facts=[],
    hidden_facts=[],
    discoverable_clues=[],
    interactables=[],
    addressables=[],
    exits=[],
)


def _seed(tmp_path, monkeypatch, first: dict, second: dict | None = None) -> None:
    _patch_storage(tmp_path, monkeypatch)
    first_id = first["scene"]["id"]
    storage._save_json(storage.scene_path(first_id), first)
    if second is not None:
        storage._save_json(storage.scene_path(second["scene"]["id"]), second)
    for extra_id in ("frontier_gate", "market_quarter", "old_milestone"):
        if extra_id not in {first_id, (second or {}).get("scene", {}).get("id")}:
            storage._save_json(storage.scene_path(extra_id), default_scene(extra_id))
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = first_id
    session["visited_scene_ids"] = [first_id]
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


def _parse_observe(text: str, envelope: dict = KILN) -> dict:
    session = default_session()
    session["active_scene_id"] = envelope["scene"]["id"]
    parsed = parse_freeform_to_action(
        text, envelope, session=session, world=default_world()
    )
    assert parsed is not None
    assert parsed.get("type") == "observe"
    assert (parsed.get("metadata") or {}).get("parser_lane") == "local_observation_question"
    return parsed


def test_whats_nearby_is_local_observation_not_adjudication():
    assert _looks_like_local_observation_question("What's nearby?")
    assert should_emit_observe_for_local_observation_parse("What's nearby?", KILN)
    assert classify_adjudication_query("What's nearby?", session={}, world={}, scene=KILN) is None
    assert resolve_adjudication_query(
        "What's nearby?",
        scene=KILN,
        session=default_session(),
        world=default_world(),
        character=default_character(),
    ) is None
    _parse_observe("What's nearby?")


def test_local_presence_paraphrases_reach_observe_owner():
    for text in LOCAL_PRESENCE:
        assert _looks_like_local_observation_question(text), text
        _parse_observe(text)
        assert classify_adjudication_query(text, session={}, world={}, scene=KILN) is None, text


def test_novel_local_presence_paraphrase_reaches_observe():
    text = "What is present in the immediate vicinity?"
    assert _looks_like_local_observation_question(text)
    _parse_observe(text)


def test_http_whats_nearby_surfaces_current_scene_not_catalog(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, QUAY)
    data = _chat(monkeypatch, "What's nearby?", "I don't know what's nearby.")
    facing = _facing(data)
    assert _kind(data) == "observe"
    assert "no nearby npc presence" not in facing.lower()
    assert _has(facing, "lantern", "ash", "kiln") or facing == observe_nothing_new_fallback_line()


def test_http_nearby_does_not_leak_prior_scene_geography(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, QUAY)
    _chat(monkeypatch, "I'll head to the brass quay.", "You reach the deserted quay.")
    data = _chat(
        monkeypatch,
        "What's nearby?",
        "The cracked lantern still hangs above the kiln door beside the mooring rings.",
    )
    facing = _facing(data)
    assert _kind(data) == "observe"
    assert not _has(facing, "cracked lantern", "kiln door")
    assert "lantern hangs above the kiln" not in facing.lower()
    assert _has(facing, "mooring", "ledger", "quay") or facing == observe_nothing_new_fallback_line()


def test_http_offscene_clue_stays_historical_on_nearby(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, QUAY)
    first = _chat(monkeypatch, "I inspect the kiln grate.", f"You read the grate. {KILN_CLUE}")
    assert _kind(first) in {"discover_clue", "investigate"}
    _chat(monkeypatch, "I'll head to the brass quay.", "You reach the deserted quay.")
    facing = _facing(
        _chat(monkeypatch, "What's nearby?", f"Soot handprints still mark the kiln brick beside {RINGS}")
    )
    assert "soot handprints" not in facing.lower()
    assert "kiln brick" not in facing.lower()


def test_http_nearby_does_not_invent_absent_object(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN)
    facing = _facing(_chat(monkeypatch, "What's nearby?", INVENTED_NEARBY))
    assert "marble fountain" not in facing.lower()
    assert "tavern sign" not in facing.lower()


def test_http_barren_scene_nearby_does_not_invent(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, BARREN)
    data = _chat(monkeypatch, "What's nearby?", "I don't know what's nearby.")
    facing = _facing(data)
    assert _kind(data) == "observe"
    assert "marble fountain" not in facing.lower()
    assert "tavern" not in facing.lower()
    assert "no nearby npc presence" not in facing.lower()


def test_unknown_non_local_question_stays_grounded_ignorance(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN)
    data = _chat(monkeypatch, "How far away is the missing patrol?", "The patrol is forty yards west.")
    assert _kind(data) == "adjudication_query"
    facing = _facing(data)
    assert "forty yards" not in facing.lower()
    assert _has(facing, "concrete", "target", "distance", "established")


def test_rules_and_earshot_remain_adjudication():
    session = default_session()
    world = default_world()
    assert classify_adjudication_query(
        "Do I need to roll Perception?", session=session, world=world, scene=KILN
    ) == "roll_requirement_query"
    assert classify_adjudication_query(
        "Is anyone else in earshot?", session=session, world=world, scene=KILN
    ) == "perception_query"
    assert classify_adjudication_query(
        "Who is nearby?", session=session, world=world, scene=KILN
    ) == "perception_query"
    assert classify_adjudication_query(
        "What actions are available?", session=session, world=world, scene=KILN
    ) == "state_query"
    assert classify_adjudication_query(
        "Can I sneak past without being seen?", session=session, world=world, scene=KILN
    ) == "action_feasibility_query"


def test_targeted_inspect_and_travel_keep_existing_owners():
    session = default_session()
    session["active_scene_id"] = "ember_kiln"
    inspect = parse_freeform_to_action(
        "I inspect the kiln grate.", KILN, session=session, world=default_world()
    )
    assert inspect is not None
    assert inspect.get("type") == "investigate"
    travel = parse_freeform_to_action(
        "I'll head to the brass quay.", KILN, session=session, world=default_world()
    )
    assert travel is not None
    assert travel.get("type") == "scene_transition"
    walk = "I walk a few steps along the wall."
    assert looks_like_local_physical_movement(walk) is True
    parsed_walk = parse_freeform_to_action(walk, KILN, session=session, world=default_world())
    assert parsed_walk is not None
    assert parsed_walk.get("type") == "custom"
    assert not parsed_walk.get("target_scene_id")


def test_named_place_nearby_is_not_untargeted_local_observation():
    assert not _looks_like_local_observation_question("What's around the brass quay?")
    assert not _looks_like_local_observation_question("What's nearby the ember kiln?")


def test_http_immediate_nearby_after_observe_is_nothing_new(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN)
    _chat(monkeypatch, "I look around.", KILN_STOCK)
    later = _facing(_chat(monkeypatch, "What's nearby?", KILN_STOCK))
    assert later == observe_nothing_new_fallback_line()


def test_nearby_question_is_stamp_eligible_untargeted_observe():
    assert observation_recent_use_should_record(
        resolution={"kind": "observe"},
        player_text="What's nearby?",
        scene=KILN,
    )
    assert observation_recent_use_should_record(
        resolution={"kind": "observe"},
        player_text="I look around.",
        scene=KILN,
    )


def test_http_cedar_generalization_nearby(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, CEDAR)
    data = _chat(monkeypatch, "What's nearby?", INVENTED_NEARBY)
    facing = _facing(data)
    assert _kind(data) == "observe"
    assert "tavern" not in facing.lower()
    assert "marble fountain" not in facing.lower()
    assert _has(facing, "piling", "hawser", "cedar") or facing == observe_nothing_new_fallback_line()


def test_hidden_fact_still_fail_closed_on_nearby(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN)
    facing = _facing(_chat(monkeypatch, "What's nearby?", f"You notice {HIDDEN_STREAM}"))
    assert "hidden stream" not in facing.lower()


def test_offscene_clue_classifier_still_rejects_present_here_geography():
    session = default_session()
    session["active_scene_id"] = "brass_quay"
    session["visited_scene_ids"] = ["ember_kiln", "brass_quay"]
    add_clue_to_knowledge(
        session,
        "soot_prints",
        "discovered",
        clue_text=KILN_CLUE,
        source_scene="ember_kiln",
    )
    evidence = {
        "kind": "observe",
        "authorized_blob": f"{RINGS} {LEDGER}".lower(),
        "offscene_geography_texts": [LANTERN, ASH, KILN_CLUE],
        "hidden_fact_texts": [],
        "undiscovered_clue_texts": [],
        "interlocutor_id": "",
    }
    verdict = classify_perception_invention(
        f"{LANTERN} {RINGS}", evidence, resolution={"kind": "observe"}
    )
    assert verdict["unsupported"] is True
    assert "prior_scene_geography" in verdict["flags"]


def test_generic_engine_has_no_frontier_gate_special_case():
    text = "".join(path.read_text(encoding="utf-8") for path in GENERIC_ENGINE_FILES)
    lowered = text.lower()
    assert "threadbare watchers" not in lowered
    assert "frontier_gate" not in lowered
    assert "muddy gate line" not in lowered
    assert "gate serjeant" not in lowered
    assert "what's nearby?" not in lowered
