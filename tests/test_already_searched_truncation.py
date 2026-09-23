"""PR-AT: already_searched must realize a complete owned sentence.

Synthetic fixtures use mill-loft / kiln vocabulary. Frontier Gate strings
are calibration residue only.
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
from game.exploration import resolve_exploration_action
from game.intent_parser import parse_freeform_to_action
from game.leads import SESSION_LEAD_REGISTRY_KEY
from game.perception_grounding import (
    ALREADY_SEARCHED_NOTHING_NEW_LINE,
    apply_perception_non_invention_to_gm,
    render_grounded_perception_line,
)
from game.referenced_surface import (
    classification_from_resolution,
    classify_referenced_surface,
    metadata_from_classification,
    render_referenced_surface_inspection_line,
)
from game.scene_actions import normalize_scene_action
from game.storage import get_scene_runtime
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

SLATE = "Dock fees rise after the second horn."
SKYLIGHT = "A soot-stained skylight leaks pale noon light onto the loft floor."
T19_LIKE = (
    "The slate's weathered planks bear the official lists: new taxes levied on "
    "inbound goods, curfew rules tightening after dusk, and an urgent warning "
    "about a patrol that has gone missing. The posted notice specifies that the "
    "missing patrol was last seen taking the northwest…"
)
T13_LIKE = (
    "The slate remains unchanged, its posting firmly listing the current taxes, "
    "curfew regulations, and the warning about the missing patrol scheduled "
    "along the northwest mud track past the crates. The gate serjeant nearby "
    "continues his steady watch over the roster board, with…"
)


def _mill_scene() -> dict:
    return {
        "scene": {
            "id": "mill_loft",
            "location": "Mill Loft",
            "summary": "A dry loft, a grain hopper, and a tariff slate.",
            "visible_facts": [SKYLIGHT, "Sacks of cracked maize lean against the hopper braces."],
            "discoverable_clues": [{"id": "tariff_slate_fees", "text": SLATE}],
            "interactables": [
                {
                    "id": "tariff_slate",
                    "label": "Tariff slate",
                    "aliases": ["slate", "fee slate"],
                    "type": "investigate",
                    "reveals_clue": "tariff_slate_fees",
                }
            ],
            "addressables": [],
            "exits": [],
            "enemies": [],
            "actions": [],
        }
    }


def _complete(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw or raw.endswith("…") or raw.endswith("..."):
        return False
    if raw.lower().endswith((" with", " northwest")):
        return False
    return raw[-1] in '.!?"'


def _seed(tmp_path, monkeypatch, envelope: dict):
    _patch_storage(tmp_path, monkeypatch)
    sid = envelope["scene"]["id"]
    storage._save_json(storage.scene_path(sid), envelope)
    for extra_id in ("frontier_gate", "market_quarter", "old_milestone"):
        if extra_id != sid:
            storage._save_json(storage.scene_path(extra_id), default_scene(extra_id))
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


def _lead_ids(session: dict | None = None) -> list[str]:
    sess = session if isinstance(session, dict) else storage.load_session()
    registry = sess.get(SESSION_LEAD_REGISTRY_KEY) or {}
    if isinstance(registry, dict):
        return sorted(str(key) for key in registry.keys())
    return []


def _resolve_already_searched(scene: dict, player_text: str = "I look at the tariff slate."):
    session: dict = {}
    rt = get_scene_runtime(session, scene["scene"]["id"])
    rt["resolved_interactables"] = ["tariff_slate"]
    rt["searched_targets"] = ["tariff_slate"]
    parsed = parse_freeform_to_action(player_text, scene)
    action = normalize_scene_action(parsed)
    return resolve_exploration_action(
        scene,
        session,
        {},
        action,
        raw_player_text=player_text,
        list_scene_ids=lambda: [scene["scene"]["id"]],
    ), session


def test_metadata_keeps_authored_inspectable_text():
    scene = _mill_scene()
    classified = classify_referenced_surface("I look at the tariff slate.", scene)
    meta = metadata_from_classification(classified)
    assert classified["inspectable_text"] == SLATE
    assert meta["referenced_surface_inspectable_text"] == SLATE


def test_already_searched_resolution_is_not_a_new_discovery():
    res, _session = _resolve_already_searched(_mill_scene())
    assert res["kind"] == "already_searched"
    assert res.get("clue_id") is None
    assert res.get("clue_text") is None
    assert res.get("discovered_clues") == []
    assert (res.get("state_changes") or {}).get("already_searched") is True
    reconstructed = classification_from_resolution(res)
    assert reconstructed.get("inspectable_text") == SLATE


def test_owned_already_searched_line_is_complete_and_authored():
    res, _session = _resolve_already_searched(_mill_scene())
    line = render_grounded_perception_line(
        _mill_scene(),
        player_text="I look at the tariff slate.",
        resolution=res,
    )
    assert line == render_referenced_surface_inspection_line(
        classification_from_resolution(res), _mill_scene()
    )
    assert SLATE.rstrip(".") in line
    assert _complete(line)
    assert not line.endswith("…")
    assert "inbound goods" not in line.lower()
    assert "northwest" not in line.lower()


def test_apply_replaces_truncated_already_searched_model_text():
    res, session = _resolve_already_searched(_mill_scene())
    for fragment in (T19_LIKE, T13_LIKE):
        gm = {"player_facing_text": fragment, "tags": [], "metadata": {}}
        out = apply_perception_non_invention_to_gm(
            gm,
            resolution=res,
            session=session,
            world={},
            scene=_mill_scene(),
            player_text="I look at the tariff slate.",
        )
        text = str(out["player_facing_text"])
        assert text != fragment
        assert _complete(text)
        assert SLATE.rstrip(".") in text
        assert not text.endswith("…")
        assert not text.lower().endswith("with")
        assert "inbound goods" not in text.lower()
        assert "gate serjeant" not in text.lower()


def test_generic_already_searched_is_complete_without_invention():
    line = render_grounded_perception_line(
        _mill_scene(),
        player_text="I search again.",
        resolution={"kind": "already_searched", "metadata": {}},
    )
    assert line
    assert _complete(line)
    assert not line.endswith("…")
    assert "inbound" not in line.lower()
    assert "northwest" not in line.lower()
    assert "dusk" not in line.lower()
    assert ALREADY_SEARCHED_NOTHING_NEW_LINE in line or "nothing" in line.lower()


def test_http_reread_is_complete_and_does_not_mint_a_new_clue(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _mill_scene())
    first = _chat(monkeypatch, "I read the tariff slate.", "Invented inbound-goods schedule at dusk.")
    first_text = _facing(first)
    assert (first.get("resolution") or {}).get("kind") == "discover_clue"
    assert "dock fees" in first_text.lower()
    first_leads = _lead_ids(first.get("session"))
    assert "tariff_slate_fees" in first_leads

    second = _chat(monkeypatch, "I look at the tariff slate.", T19_LIKE)
    second_text = _facing(second)
    res = second.get("resolution") or {}
    assert res.get("kind") == "already_searched"
    assert _complete(second_text)
    assert "dock fees" in second_text.lower()
    assert "inbound goods" not in second_text.lower()
    assert "northwest" not in second_text.lower()
    assert not second_text.endswith("…")
    assert _lead_ids(second.get("session")) == first_leads
    assert res.get("clue_id") is None
    assert res.get("discovered_clues") in (None, [])


def test_http_first_authored_read_still_available(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _mill_scene())
    data = _chat(monkeypatch, "I read the tariff slate.", "As you watch the scene, maize sacks shift.")
    text = _facing(data)
    assert (data.get("resolution") or {}).get("kind") == "discover_clue"
    assert "dock fees" in text.lower()
    assert "as you watch the scene" not in text.lower()
    assert _complete(text)


def test_generic_engine_has_no_frontier_gate_special_case():
    for rel in (
        "game/referenced_surface.py",
        "game/perception_grounding.py",
        "game/exploration.py",
        "game/gm_retry.py",
    ):
        lowered = Path(rel).read_text(encoding="utf-8").lower()
        assert "threadbare watchers" not in lowered
        assert "frontier_gate" not in lowered
        assert "northwest…" not in lowered
        assert "notice board" not in lowered


def test_calibration_t13_t19_fragments_are_replaced_on_frontier_gate():
    """Calibration repro only. Production code must not special-case these strings."""
    scene = storage.load_scene("frontier_gate")
    session: dict = {}
    rt = get_scene_runtime(session, "frontier_gate")
    rt["resolved_interactables"] = ["notice_board"]
    rt["searched_targets"] = ["notice_board"]
    parsed = parse_freeform_to_action("I look at the notice board.", scene)
    action = normalize_scene_action(parsed)
    res = resolve_exploration_action(
        scene,
        session,
        {},
        action,
        raw_player_text="I look at the notice board.",
        list_scene_ids=lambda: ["frontier_gate"],
    )
    assert res["kind"] == "already_searched"
    t19 = (
        "The notice board's weathered planks bear the official lists: new taxes "
        "levied on inbound goods, curfew rules tightening after dusk, and an "
        "urgent warning about a patrol that has gone missing. The posted notice "
        "specifies that the missing patrol was last seen taking the northwest…"
    )
    t13 = (
        "The notice board remains unchanged, its posting firmly listing the "
        "current taxes, curfew regulations, and the warning about the missing "
        "patrol scheduled along the northwest mud track past the crates. The "
        "gate serjeant nearby continues his steady watch over the roster board, "
        "with…"
    )
    authored = "The missing patrol was last seen taking the northwest mud track past the crates."
    for fragment in (t19, t13):
        out = apply_perception_non_invention_to_gm(
            {"player_facing_text": fragment, "tags": [], "metadata": {}},
            resolution=res,
            session=session,
            world={},
            scene=scene,
            player_text="I look at the notice board.",
        )
        text = str(out["player_facing_text"])
        assert text != fragment
        assert _complete(text)
        assert authored in text
        assert not text.endswith("…")
        assert "inbound goods" not in text.lower()
