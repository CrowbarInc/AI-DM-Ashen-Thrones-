"""PR-AX: post-transition observation must use current-scene geography.

Synthetic kiln / quay fixtures. Frontier Gate is calibration residue only.
"""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.clues import add_clue_to_knowledge, get_known_clues_with_presentation
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
from game.intent_parser import looks_like_local_physical_movement, parse_freeform_to_action
from game.perception_grounding import (
    apply_perception_non_invention_to_gm,
    build_perception_evidence_surface,
    classify_perception_invention,
    collect_recent_player_facing_narration,
)
from game.storage import get_scene_runtime
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

LANTERN = "A cracked lantern hangs above the kiln door."
ASH = "Cold ash sits unused in the grate."
KILN_CLUE = "Soot handprints mark the kiln brick behind the grate."
KILN_STOCK = f"As you watch the scene, {LANTERN} {ASH}"
RINGS = "Copper mooring rings stud the quay stones."
LEDGER = "A tide ledger flutters on a rusted nail."
QUAY_CLUE = "The tide ledger names a missing berth at dawn."
QUAY_STOCK = f"As you watch the scene, {RINGS} {LEDGER}"
KILN_AT_QUAY = (
    "A cracked lantern hangs above the kiln door while copper mooring rings "
    "stud the quay stones and a tide ledger flutters on a rusted nail."
)
QUAY_AT_KILN = (
    "Copper mooring rings stud the quay stones beside the kiln while a cracked "
    "lantern hangs above the kiln door."
)
HIDDEN_STREAM = "A hidden stream rushes through a tunnel beneath the wall."

GENERIC_ENGINE_FILES = (
    Path("game/perception_grounding.py"),
    Path("game/diegetic_fallback_narration.py"),
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
    discoverable_clues=[{"id": "tide_berth", "text": QUAY_CLUE}],
    interactables=[
        {
            "id": "tide_ledger",
            "label": "Tide ledger",
            "aliases": ["ledger", "nail"],
            "type": "investigate",
            "reveals_clue": "tide_berth",
            "description": QUAY_CLUE,
        }
    ],
    addressables=[],
    exits=[{"label": "To the ember kiln", "target_scene_id": "ember_kiln"}],
)
CEDAR = _envelope(
    "cedar_wharf",
    location="Cedar Wharf",
    summary="Cedar pilings stand in slack brown water.",
    visible_facts=[
        "Cedar pilings stand in slack brown water.",
        "A coiled hemp hawser rests on the lowest plank.",
    ],
    hidden_facts=[],
    discoverable_clues=[],
    interactables=[],
    addressables=[],
    exits=[{"label": "To the tin loft", "target_scene_id": "tin_loft"}],
)
LOFT = _envelope(
    "tin_loft",
    location="Tin Loft",
    summary="A tin-roofed loft holds stacked dye crates.",
    visible_facts=[
        "Stacked dye crates lean under a tin roof.",
        "A brass scale sits on a counting stool.",
    ],
    hidden_facts=[],
    discoverable_clues=[],
    interactables=[],
    addressables=[],
    exits=[{"label": "To the cedar wharf", "target_scene_id": "cedar_wharf"}],
)


def _seed_pair(tmp_path, monkeypatch, first: dict, second: dict) -> str:
    _patch_storage(tmp_path, monkeypatch)
    first_id = first["scene"]["id"]
    second_id = second["scene"]["id"]
    storage._save_json(storage.scene_path(first_id), first)
    storage._save_json(storage.scene_path(second_id), second)
    for extra_id in ("frontier_gate", "market_quarter", "old_milestone"):
        if extra_id not in {first_id, second_id}:
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
    return first_id


def _chat(monkeypatch, text: str, gm_text: str) -> dict:
    monkeypatch.setattr("game.api.call_gpt", lambda _messages: _gm_response(gm_text))
    client = TestClient(app)
    resp = client.post("/api/chat", json={"text": text})
    assert resp.status_code == 200
    return resp.json()


def _facing(data: dict) -> str:
    return str((data.get("gm_output") or {}).get("player_facing_text") or "")


def _active_scene(data: dict) -> str:
    scene = data.get("scene") if isinstance(data.get("scene"), dict) else {}
    inner = scene.get("scene") if isinstance(scene.get("scene"), dict) else scene
    sid = str((inner or {}).get("id") or "").strip()
    if sid:
        return sid
    return str((data.get("session") or {}).get("active_scene_id") or "").strip()


def _has(text: str, *needles: str) -> bool:
    low = str(text or "").lower()
    return any(needle.lower() in low for needle in needles)


def test_scene_a_observation_uses_scene_a_geography(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, KILN, QUAY)
    facing = _facing(_chat(monkeypatch, "I look around.", KILN_STOCK))
    assert _has(facing, "lantern", "ash")
    assert not _has(facing, "mooring", "tide ledger")


def test_after_a_to_b_observe_does_not_emit_a_geography(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, KILN, QUAY)
    _chat(monkeypatch, "I look around.", KILN_STOCK)
    travel = _chat(monkeypatch, "I'll head to the brass quay.", "You reach the deserted quay.")
    assert _active_scene(travel) == "brass_quay"
    facing = _facing(_chat(monkeypatch, "I look around.", KILN_AT_QUAY))
    assert not _has(facing, "cracked lantern", "kiln door")
    assert "lantern hangs above the kiln" not in facing.lower()


def test_after_a_to_b_authored_b_geography_remains(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, KILN, QUAY)
    _chat(monkeypatch, "I'll head to the brass quay.", "You reach the deserted quay.")
    facing = _facing(_chat(monkeypatch, "I look around.", QUAY_STOCK))
    assert _has(facing, "mooring", "ledger") or _has(facing, "quay", "nail")


def test_after_a_to_b_to_a_legitimate_a_geography_can_surface(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, KILN, QUAY)
    _chat(monkeypatch, "I'll head to the brass quay.", "You reach the deserted quay.")
    _chat(monkeypatch, "I'll head back to the ember kiln.", "You return to the kiln alcove.")
    facing = _facing(_chat(monkeypatch, "I look around.", KILN_STOCK))
    assert _has(facing, "lantern", "ash")
    assert not _has(facing, "mooring rings", "tide ledger")


def test_prior_perception_snapshot_cannot_override_current_scene(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, KILN, QUAY)
    _chat(monkeypatch, "I look around.", KILN_STOCK)
    _chat(monkeypatch, "I'll head to the brass quay.", "You reach the deserted quay.")
    session = storage.load_session()
    kiln_recent = collect_recent_player_facing_narration(session=session, scene_id="ember_kiln")
    quay_recent = collect_recent_player_facing_narration(session=session, scene_id="brass_quay")
    assert _has(kiln_recent, "lantern")
    assert quay_recent == ""
    replaced = apply_perception_non_invention_to_gm(
        {"player_facing_text": KILN_AT_QUAY, "tags": []},
        resolution={"kind": "observe"},
        session=session,
        world=storage.load_world(),
        scene=storage.load_scene("brass_quay"),
        player_text="I look around.",
    )
    facing = str((replaced or {}).get("player_facing_text") or "")
    assert "lantern hangs above the kiln" not in facing.lower()
    assert _has(facing, "mooring", "ledger") or facing == observe_nothing_new_fallback_line()
    assert (replaced or {}).get("metadata", {}).get("perception_non_invention", {}).get("applied")


def test_history_is_not_globally_erased_on_transition(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, KILN, QUAY)
    _chat(monkeypatch, "I look around.", KILN_STOCK)
    _chat(monkeypatch, "I inspect the kiln grate.", f"You read the grate. {KILN_CLUE}")
    _chat(monkeypatch, "I'll head to the brass quay.", "You reach the deserted quay.")
    session = storage.load_session()
    assert session.get("active_scene_id") == "brass_quay"
    kiln_rt = get_scene_runtime(session, "ember_kiln")
    assert _has(str(kiln_rt.get("last_perception_narration") or ""), "lantern")
    known = get_known_clues_with_presentation(session)
    assert any(row.get("id") == "soot_prints" for row in known)
    assert any(row.get("source_scene") == "ember_kiln" for row in known)
    evidence = build_perception_evidence_surface(
        scene=storage.load_scene("brass_quay"),
        session=session,
        world=storage.load_world(),
        resolution={"kind": "observe"},
    )
    assert any("soot handprints" in str(text).lower() for text in evidence.get("offscene_geography_texts") or [])
    assert not any("soot handprints" in str(text).lower() for text in evidence.get("discovered_clue_texts") or [])


def test_pras_untargeted_repeat_still_nothing_new(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, KILN, QUAY)
    first = _facing(_chat(monkeypatch, "I look around.", KILN_STOCK))
    assert _has(first, "lantern", "ash")
    again = _facing(_chat(monkeypatch, "I look around again.", KILN_STOCK))
    assert again == observe_nothing_new_fallback_line()


def test_praw_intervening_inspect_does_not_restack(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, KILN, QUAY)
    _chat(monkeypatch, "I look around.", KILN_STOCK)
    _chat(monkeypatch, "I inspect the kiln grate.", f"You read the grate. {KILN_CLUE}")
    later = _facing(_chat(monkeypatch, "I look around.", KILN_STOCK))
    assert later == observe_nothing_new_fallback_line()


def test_targeted_current_scene_fact_may_repeat(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, KILN, QUAY)
    _chat(monkeypatch, "I look around.", KILN_STOCK)
    _chat(monkeypatch, "I'll head to the brass quay.", "You reach the deserted quay.")
    _chat(monkeypatch, "I look around.", QUAY_STOCK)
    targeted = _facing(
        _chat(monkeypatch, "I look at the tide ledger.", f"You notice {LEDGER}")
    )
    assert _has(targeted, "ledger")


def test_new_current_scene_fact_may_surface(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, KILN, QUAY)
    _chat(monkeypatch, "I'll head to the brass quay.", "You reach the deserted quay.")
    _chat(monkeypatch, "I look around.", QUAY_STOCK)
    scene = storage.load_scene("brass_quay")
    scene["scene"]["visible_facts"] = [RINGS, LEDGER, "A wet boot print darkens the lowest ring."]
    storage._save_json(storage.scene_path("brass_quay"), scene)
    later = _facing(
        _chat(monkeypatch, "I look around.", "A wet boot print darkens the lowest ring.")
    )
    assert _has(later, "boot print")
    assert later != observe_nothing_new_fallback_line()


def test_return_nothing_new_remains_valid(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, KILN, QUAY)
    _chat(monkeypatch, "I look around.", KILN_STOCK)
    _chat(monkeypatch, "I'll head to the brass quay.", "You reach the deserted quay.")
    _chat(monkeypatch, "I look around.", QUAY_STOCK)
    _chat(monkeypatch, "I'll head back to the ember kiln.", "You return to the kiln alcove.")
    later = _facing(_chat(monkeypatch, "I look around.", KILN_STOCK))
    assert later == observe_nothing_new_fallback_line()


def test_prar_hidden_fact_still_fail_closed(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, KILN, QUAY)
    facing = _facing(
        _chat(monkeypatch, "I look around.", f"You notice {HIDDEN_STREAM}")
    )
    assert "hidden stream" not in facing.lower()


def test_praq_local_walk_is_not_scene_travel():
    text = "I walk a few steps along the wall."
    parsed = parse_freeform_to_action(text, KILN)
    assert looks_like_local_physical_movement(text) is True
    assert parsed["type"] == "custom"
    assert not parsed.get("target_scene_id")


def test_prat_already_searched_keeps_authored_sentence(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, KILN, QUAY)
    first = _chat(monkeypatch, "I inspect the kiln grate.", f"You read the grate. {KILN_CLUE}")
    assert (first.get("resolution") or {}).get("kind") in {"discover_clue", "investigate"}
    second = _chat(monkeypatch, "I inspect the kiln grate again.", "Closer looking yields nothing further.")
    kind = (second.get("resolution") or {}).get("kind")
    facing = _facing(second)
    assert kind == "already_searched"
    assert facing[-1] in '.!?"'
    assert not facing.endswith("…")


def test_cedar_wharf_generalization_not_frontier_gate(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, CEDAR, LOFT)
    _chat(monkeypatch, "I look around.", "Cedar pilings stand in slack brown water.")
    _chat(monkeypatch, "I'll head to the tin loft.", "You climb into the tin loft.")
    bleed = (
        "Cedar pilings stand in slack brown water beneath stacked dye crates "
        "leaning under a tin roof."
    )
    facing = _facing(_chat(monkeypatch, "I look around.", bleed))
    assert "cedar pilings" not in facing.lower()
    assert _has(facing, "dye", "scale", "tin") or facing == observe_nothing_new_fallback_line()


def test_offscene_clue_does_not_license_current_geography():
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
        KILN_AT_QUAY, evidence, resolution={"kind": "observe"}
    )
    assert verdict["unsupported"] is True
    assert "prior_scene_geography" in verdict["flags"]


def test_return_to_scene_does_not_flag_its_own_geography():
    evidence = {
        "kind": "observe",
        "authorized_blob": f"{LANTERN} {ASH}".lower(),
        "offscene_geography_texts": [RINGS, LEDGER],
        "hidden_fact_texts": [],
        "undiscovered_clue_texts": [],
        "interlocutor_id": "",
    }
    verdict = classify_perception_invention(
        KILN_STOCK, evidence, resolution={"kind": "observe"}
    )
    assert verdict["unsupported"] is False
    assert "prior_scene_geography" not in verdict["flags"]


def test_whats_nearby_after_travel_does_not_emit_prior_scene_geography(tmp_path, monkeypatch):
    _seed_pair(tmp_path, monkeypatch, KILN, QUAY)
    _chat(monkeypatch, "I'll head to the brass quay.", "You reach the deserted quay.")
    data = _chat(
        monkeypatch,
        "What's nearby?",
        "The cracked lantern still hangs above the kiln door beside the quay.",
    )
    facing = _facing(data)
    assert (data.get("resolution") or {}).get("kind") == "observe"
    assert not _has(facing, "cracked lantern", "kiln door")
    assert "lantern hangs above the kiln" not in facing.lower()


def test_generic_engine_has_no_frontier_gate_special_case():
    text = "".join(path.read_text(encoding="utf-8") for path in GENERIC_ENGINE_FILES)
    lowered = text.lower()
    assert "threadbare watchers" not in lowered
    assert "frontier_gate" not in lowered
    assert "muddy gate line" not in lowered
    assert "gate serjeant" not in lowered
    assert "old_milestone" not in lowered
    helper = Path("game/perception_grounding.py").read_text(encoding="utf-8")
    assert "prior_scene_geography" in helper
    assert "offscene_geography_texts" in helper
