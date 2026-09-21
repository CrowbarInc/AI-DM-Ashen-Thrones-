"""PR-AR: perception narration may realize the world, not author it.

Synthetic fixtures use kiln / quay / orchard vocabulary. Frontier Gate T16
is calibration regression only.
"""
from __future__ import annotations

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
from game.diegetic_fallback_narration import render_observe_perception_fallback_line
from game.exploration import resolve_exploration_action
from game.human_adjacent_focus import resolve_implicit_human_adjacent_focus
from game.intent_parser import parse_freeform_to_action
from game.interaction_context import inspect as inspect_interaction_context
from game.leads import SESSION_LEAD_REGISTRY_KEY
from game.perception_grounding import (
    apply_perception_non_invention_to_gm,
    build_perception_evidence_surface,
    classify_perception_invention,
)
from game.scene_actions import normalize_scene_action
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

CALIBRATION_ENGINE_TERMS = (
    "frontier_gate",
    "muddy_gate_line",
    "gate_line",
    "missing_patrol",
    "tavern_runner",
    "notice_board",
    "Cinderwatch",
    "Captain Thoran",
    "guard_captain",
    "old_milestone",
    "stew",
)
GENERIC_ENGINE_FILES = (
    Path("game/perception_grounding.py"),
    Path("game/human_adjacent_focus.py"),
    Path("game/diegetic_fallback_narration.py"),
)
T16_TEXT = "I walk a few steps along the muddy gate line and listen"
T16_INVENTION = (
    "You pace alongside the muddy line, tuning your ears to the murmurs and muted "
    "complaints. Soft, anxious whispers drift—talk of the missing patrol."
)
WATER_FACT = "Water can be heard behind the kiln wall."
FOOTSTEP_FACT = "Footsteps tap along the quay boards."
BELL_FACT = "A harbor bell tolls once from the cut."
SPEECH_FACT = "A dock clerk calls the next berth number."
BLOOD_FACT = "A streak of blood marks the flagstones by the kiln."


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
    visible_facts=[
        "A cold kiln stands in a brick alcove.",
        "Ash sits unused in the grate.",
    ],
    hidden_facts=["A hidden stream rushes through a tunnel beneath the wall."],
    discoverable_clues=[],
    interactables=[
        {
            "id": "kiln_door",
            "label": "Kiln door",
            "aliases": ["door", "alcove door"],
            "type": "investigate",
        }
    ],
    addressables=[],
    exits=[],
)
KILN_WATER = _envelope(
    "ember_kiln",
    location="Ember Kiln Alcove",
    summary="A cold kiln stands in a brick alcove.",
    visible_facts=[
        "A cold kiln stands in a brick alcove.",
        WATER_FACT,
    ],
    hidden_facts=["A hidden stream rushes through a tunnel beneath the wall."],
    discoverable_clues=[],
    addressables=[],
    exits=[],
)
QUAY = _envelope(
    "brass_quay",
    location="Brass Quay",
    summary="A deserted quay leans over black water.",
    visible_facts=[
        "A deserted quay leans over black water.",
        "Lantern hooks hang empty along the rail.",
    ],
    hidden_facts=[],
    discoverable_clues=[],
    addressables=[
        {
            "id": "quay_clerk",
            "name": "Quay Clerk",
            "scene_id": "brass_quay",
            "kind": "npc",
            "addressable": True,
        }
    ],
    exits=[],
)
QUAY_SPEECH = _envelope(
    "brass_quay",
    location="Brass Quay",
    summary="A clerk works the deserted quay.",
    visible_facts=[
        "A deserted quay leans over black water.",
        SPEECH_FACT,
    ],
    addressables=[
        {
            "id": "quay_clerk",
            "name": "Quay Clerk",
            "scene_id": "brass_quay",
            "kind": "npc",
            "addressable": True,
        }
    ],
    exits=[],
)
QUAY_FOOTSTEPS = _envelope(
    "brass_quay",
    location="Brass Quay",
    visible_facts=["A deserted quay leans over black water.", FOOTSTEP_FACT],
    addressables=[],
    exits=[],
)
QUAY_BELL = _envelope(
    "brass_quay",
    location="Brass Quay",
    visible_facts=["A deserted quay leans over black water.", BELL_FACT],
    addressables=[],
    exits=[],
)
KILN_BLOOD = _envelope(
    "ember_kiln",
    location="Ember Kiln Alcove",
    visible_facts=["A cold kiln stands in a brick alcove.", BLOOD_FACT],
    addressables=[],
    exits=[],
)


def _seed(tmp_path, monkeypatch, envelope: dict, *, world_npcs: list | None = None):
    _patch_storage(tmp_path, monkeypatch)
    sid = envelope["scene"]["id"]
    storage._save_json(storage.scene_path(sid), envelope)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    storage._save_json(storage.scene_path("market_quarter"), default_scene("market_quarter"))
    storage._save_json(storage.scene_path("old_milestone"), default_scene("old_milestone"))
    world = default_world()
    if world_npcs is not None:
        world["npcs"] = world_npcs
    storage._save_json(storage.WORLD_PATH, world)
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


def _lead_ids(session: dict | None = None) -> set[str]:
    sess = session if isinstance(session, dict) else storage.load_session()
    registry = sess.get(SESSION_LEAD_REGISTRY_KEY) or {}
    if isinstance(registry, dict):
        return {str(key) for key in registry.keys()}
    return set()


def _npc_ids() -> set[str]:
    world = storage.load_world()
    rows = world.get("npcs") or []
    if isinstance(rows, dict):
        rows = list(rows.values())
    return {str(row["id"]) for row in rows if isinstance(row, dict) and row.get("id")}


def _evidence(scene: dict, *, kind: str = "observe", session=None, world=None):
    return build_perception_evidence_surface(
        scene=scene,
        session=session if session is not None else default_session(),
        world=world if world is not None else {"npcs": []},
        resolution={"kind": kind},
    )


def _resolve(scene: dict, text: str):
    parsed = parse_freeform_to_action(text, scene)
    action = normalize_scene_action(parsed)
    res = resolve_exploration_action(
        scene,
        {},
        {},
        action,
        raw_player_text=text,
        list_scene_ids=lambda: [scene["scene"]["id"]],
    )
    return parsed, res


def _complete(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw or raw.endswith("…") or raw.endswith("..."):
        return False
    return raw[-1] in ".!?\""


def test_empty_listen_is_grounded_absence():
    parsed, res = _resolve(KILN, "I listen.")
    assert parsed["type"] == "observe"
    line = render_observe_perception_fallback_line(
        KILN, seed_key="prar|empty", player_text="I listen.", resolution=res
    )
    assert line and _complete(line)
    low = line.lower()
    assert "whisper" not in low
    assert "footstep" not in low
    assert "complaint" not in low


def test_authorized_water_sound_may_be_realized():
    _parsed, res = _resolve(KILN_WATER, "I listen.")
    line = render_observe_perception_fallback_line(
        KILN_WATER, seed_key="prar|water", player_text="I listen.", resolution=res
    )
    assert line
    assert "water" in line.lower() or "heard" in line.lower()
    assert "whisper" not in line.lower()
    assert "tunnel" not in line.lower()


def test_unsupported_footsteps_fail_closed():
    verdict = classify_perception_invention(
        "Boots scrape behind the kiln wall.",
        _evidence(KILN),
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is True
    assert any(flag.startswith("perceptible_event:") for flag in verdict["flags"])


def test_authorized_footsteps_survive():
    verdict = classify_perception_invention(
        "You hear footsteps tap along the quay boards.",
        _evidence(QUAY_FOOTSTEPS),
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is False


def test_unsupported_mutter_fails_closed_on_observe():
    verdict = classify_perception_invention(
        'A kiln warden mutters, "The grate stays sealed after dark."',
        _evidence(KILN),
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is True
    assert any("mutter" in flag for flag in verdict["flags"])


def test_unsupported_whisper_fails_closed_even_with_npc_present():
    world = {"npcs": [{"id": "quay_clerk", "name": "Quay Clerk", "location": "brass_quay"}]}
    verdict = classify_perception_invention(
        "The quay clerk whispers about a sealed hold.",
        _evidence(QUAY, world=world),
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is True
    assert any("whisper" in flag or "spoken_content" in flag for flag in verdict["flags"])


def test_authorized_speech_survives():
    world = {"npcs": [{"id": "quay_clerk", "name": "Quay Clerk", "location": "brass_quay"}]}
    verdict = classify_perception_invention(
        "A dock clerk calls the next berth number over the water.",
        _evidence(QUAY_SPEECH, world=world),
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is False


def test_npc_presence_is_not_speaking_group():
    bundle = resolve_implicit_human_adjacent_focus(
        player_text="I listen.",
        session={},
        world={"npcs": [{"id": "quay_clerk", "name": "Quay Clerk", "location": "brass_quay"}]},
        scene_envelope=QUAY,
        intent_family="listen",
    )
    assert bundle["implicit_focus_resolution"] != "speaking_group"


def test_player_seeks_whisper_does_not_create_one(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, world_npcs=[])
    data = _chat(monkeypatch, "I listen for whispers.", T16_INVENTION)
    text = _facing(data).lower()
    assert (data.get("resolution") or {}).get("kind") == "observe"
    assert "whisper" not in text
    assert "complaint" not in text
    assert _complete(_facing(data))


def test_player_seeks_footsteps_does_not_create_them(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, world_npcs=[])
    data = _chat(monkeypatch, "I listen for footsteps.", "Boots scrape behind the kiln wall.")
    text = _facing(data).lower()
    assert "footstep" not in text
    assert "boots scrape" not in text


def test_unsupported_bell_fails_closed():
    verdict = classify_perception_invention(
        "A harbor bell tolls somewhere above the alcove.",
        _evidence(KILN),
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is True
    assert any("bell" in flag for flag in verdict["flags"])


def test_authorized_bell_survives():
    verdict = classify_perception_invention(
        "A harbor bell tolls once from the cut.",
        _evidence(QUAY_BELL),
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is False


def test_unsupported_visual_blood_fails_closed():
    verdict = classify_perception_invention(
        "A streak of blood marks the flagstones by the kiln.",
        _evidence(KILN),
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is True
    assert any("blood" in flag for flag in verdict["flags"])


def test_authorized_visual_blood_survives():
    verdict = classify_perception_invention(
        "A streak of blood marks the flagstones by the kiln.",
        _evidence(KILN_BLOOD),
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is False


def test_unsupported_smoke_fails_closed():
    verdict = classify_perception_invention(
        "A ribbon of woodsmoke lifts from the cold kiln.",
        _evidence(KILN),
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is True
    assert any("smoke" in flag for flag in verdict["flags"])


def test_unsupported_tracks_fail_closed():
    verdict = classify_perception_invention(
        "Boot prints mark a trail in the dust beside the grate.",
        _evidence(KILN),
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is True
    assert any("tracks" in flag for flag in verdict["flags"])


def test_unsupported_moving_figure_fails_closed():
    verdict = classify_perception_invention(
        "A hooded figure slips from the shadows behind the kiln.",
        _evidence(KILN),
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is True
    assert any("moving_figure" in flag for flag in verdict["flags"])


def test_grounded_paraphrase_of_authorized_sound_survives():
    verdict = classify_perception_invention(
        "You hear water somewhere beyond the wall.",
        _evidence(KILN_WATER),
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is False


def test_unsupported_expansion_of_authorized_sound_fails_closed():
    verdict = classify_perception_invention(
        "A hidden stream rushes through a tunnel beneath the wall.",
        _evidence(KILN_WATER),
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is True
    assert "hidden_fact" in verdict["flags"]


def test_repeated_empty_listen_does_not_escalate():
    first = render_observe_perception_fallback_line(
        KILN,
        seed_key="prar|rep-a",
        player_text="I listen.",
        resolution=_resolve(KILN, "I listen.")[1],
    )
    second = render_observe_perception_fallback_line(
        KILN,
        seed_key="prar|rep-b",
        player_text="I keep listening.",
        resolution=_resolve(KILN, "I keep listening.")[1],
    )
    third = render_observe_perception_fallback_line(
        KILN,
        seed_key="prar|rep-c",
        player_text="I listen again.",
        resolution=_resolve(KILN, "I listen again.")[1],
    )
    for line in (first, second, third):
        assert line and _complete(line)
        low = line.lower()
        assert "whisper" not in low
        assert "new voice" not in low
        assert "someone approaches" not in low


def test_targeted_empty_listen_does_not_invent_sound():
    _parsed, res = _resolve(KILN, "I listen at the door.")
    line = render_observe_perception_fallback_line(
        KILN, seed_key="prar|door", player_text="I listen at the door.", resolution=res
    )
    assert line
    low = line.lower()
    assert "whisper" not in low
    assert "footstep" not in low


def test_recent_prose_does_not_become_perception_authority(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, world_npcs=[])
    first = _chat(monkeypatch, "I look around.", T16_INVENTION)
    assert "whisper" not in _facing(first).lower()
    second = _chat(monkeypatch, "I listen for those whispers.", "The same anxious whispers return.")
    text = _facing(second).lower()
    assert "whisper" not in text
    assert not any("narration_ctx" in item for item in _lead_ids(second.get("session")))


def test_unsupported_speech_mints_no_lead_or_npc(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, world_npcs=[])
    data = _chat(monkeypatch, "I listen.", T16_INVENTION)
    assert "whisper" not in _facing(data).lower()
    assert _lead_ids(data.get("session")) == set()
    assert "stranger" not in _npc_ids()
    assert inspect_interaction_context(data.get("session") or {}).get("active_interaction_target_id") in (None, "")


def test_fallback_does_not_replace_whisper_with_other_event():
    gm = apply_perception_non_invention_to_gm(
        {"player_facing_text": T16_INVENTION, "tags": []},
        resolution={"kind": "observe", "metadata": {"human_adjacent_intent_family": "listen", "human_adjacent_diegetic_null": True, "implicit_focus_resolution": "none"}},
        session=default_session(),
        world={"npcs": []},
        scene=KILN,
        player_text="I listen.",
    )
    text = str((gm or {}).get("player_facing_text") or "").lower()
    assert text
    assert "whisper" not in text
    assert "footstep" not in text
    assert "bell" not in text
    assert "complaint" not in text


def test_cross_modal_authority_uses_category_not_auditory_noun():
    visual = classify_perception_invention(
        "A streak of blood marks the flagstones beside unused ash.",
        _evidence(KILN),
        resolution={"kind": "observe"},
    )
    assert visual["unsupported"] is True
    assert any("blood" in flag for flag in visual["flags"])
    authorized = classify_perception_invention(
        "Ash sits unused in the grate beside the cold kiln.",
        _evidence(KILN),
        resolution={"kind": "observe"},
    )
    assert authorized["unsupported"] is False


def test_t16_remains_typed_observe_and_rejects_invented_speech():
    scene = default_scene("frontier_gate")
    parsed, res = _resolve(scene, T16_TEXT)
    assert parsed["type"] == "observe"
    assert res["kind"] == "observe"
    assert res.get("resolved_transition") is not True
    evidence = _evidence(scene, session=default_session(), world=default_world())
    verdict = classify_perception_invention(T16_INVENTION, evidence, resolution=res)
    assert verdict["unsupported"] is True
    gm = apply_perception_non_invention_to_gm(
        {"player_facing_text": T16_INVENTION, "tags": []},
        resolution=res,
        session=default_session(),
        world=default_world(),
        scene=scene,
        player_text=T16_TEXT,
    )
    text = str((gm or {}).get("player_facing_text") or "").lower()
    assert "whisper" not in text
    assert "complaint" not in text
    assert "talk of the missing" not in text


def test_http_empty_listen_complete_and_grounded(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, world_npcs=[])
    data = _chat(monkeypatch, "I listen.", T16_INVENTION)
    assert (data.get("resolution") or {}).get("kind") == "observe"
    facing = _facing(data)
    assert _complete(facing)
    assert "whisper" not in facing.lower()
    assert data.get("session", {}).get("active_scene_id") == "ember_kiln"


def test_http_authorized_speech_can_survive(tmp_path, monkeypatch):
    _seed(
        tmp_path,
        monkeypatch,
        QUAY_SPEECH,
        world_npcs=[{"id": "quay_clerk", "name": "Quay Clerk", "location": "brass_quay"}],
    )
    data = _chat(monkeypatch, "I listen.", "A dock clerk calls the next berth number over the water.")
    assert (data.get("resolution") or {}).get("kind") == "observe"
    assert "berth" in _facing(data).lower() or "clerk" in _facing(data).lower()
    assert "whisper" not in _facing(data).lower()


def test_anti_overfitting_no_calibration_special_case_or_noun_blacklist():
    for path in GENERIC_ENGINE_FILES:
        text = path.read_text(encoding="utf-8")
        for term in CALIBRATION_ENGINE_TERMS:
            if path.name == "diegetic_fallback_narration.py" and term == "stew":
                continue
            assert term not in text, f"{path} contains calibration term {term!r}"
        assert T16_TEXT not in text
        assert 'if "whisper" in' not in text
        assert "if 'whisper' in" not in text
        assert 'if "complaint" in' not in text
        assert ".replace(\"whisper\"" not in text
        assert ".replace('whisper'" not in text
