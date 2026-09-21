"""PR-AO: investigation may discover authored evidence; it may not author it.

Synthetic fixtures use amber-quay / cooper-bench vocabulary. Frontier Gate /
missing-patrol cases are calibration regression only.
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
from game.exploration import process_investigation_discovery, resolve_exploration_action
from game.intent_parser import parse_freeform_to_action
from game.leads import SESSION_LEAD_REGISTRY_KEY
from game.referenced_surface import (
    AUTHORITY_AUTHORED_INTERACTABLE,
    AUTHORITY_AUTHORED_VISIBLE_FEATURE,
    AUTHORITY_UNTARGETED,
    classify_referenced_surface,
    extract_inspection_target,
    metadata_from_classification,
)
from game.scene_actions import normalize_scene_action
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

CALIBRATION_ENGINE_TERMS = (
    "frontier_gate",
    "gate_line",
    "missing_patrol",
    "tavern_runner",
    "notice_board",
    "personnel",
    "exact_timing",
    "guard_captain",
    "Captain Thoran",
    "Cinderwatch",
    "old_milestone",
    "stew",
)
GENERIC_ENGINE_FILES = (
    Path("game/exploration.py"),
    Path("game/intent_parser.py"),
    Path("game/referenced_surface.py"),
    Path("game/perception_grounding.py"),
)
BOOTPRINTS = "Muddy bootprints sit beneath the south window."
WAX_STAIN = "A cooled wax stain marks the left desk corner."
ROWAN_FALSE = "proof that Rowan poisoned the well"
T15_TEXT = "I thank the runner and look toward the gate line again."
SUSPICIOUS_TITLE = "Details on the exact timing and personnel of the missing patrol assignment."
SUSPICIOUS_SLUG = "details_on_the_exact_timing_and_personnel_of_the_missing_patrol_assignment"


def _quay_scene(**extra) -> dict:
    scene = {
        "scene": {
            "id": "amber_quay",
            "location": "Amber Quay",
            "summary": "A wet quay, a cooper's bench, and a tide bell.",
            "visible_facts": [
                "A cooper's bench stands under the tide bell.",
                "Tar buckets lean along the quay stones.",
            ],
            "hidden_facts": [],
            "discoverable_clues": [],
            "interactables": [
                {
                    "id": "coopers_bench",
                    "label": "Cooper's bench",
                    "aliases": ["bench", "desk", "cooper bench"],
                    "type": "investigate",
                }
            ],
            "addressables": [
                {
                    "id": "bell_warden",
                    "name": "Bell Warden",
                    "scene_id": "amber_quay",
                    "kind": "npc",
                    "addressable": True,
                    "address_roles": ["warden"],
                    "aliases": [],
                }
            ],
            "exits": [],
        }
    }
    scene["scene"].update(extra)
    return scene


def _quay_world(*, warden_topics=None, extra_npcs=None) -> dict:
    world = default_world()
    npcs = [
        {
            "id": "bell_warden",
            "name": "Bell Warden",
            "location": "amber_quay",
            "topics": list(warden_topics or []),
        }
    ]
    if extra_npcs:
        npcs.extend(list(extra_npcs))
    world["npcs"] = npcs
    world_state = world.setdefault("world_state", {})
    if isinstance(world_state, dict):
        world_state["mara_owns_missing_key"] = True
    return world


def _seed(tmp_path, monkeypatch, scene: dict, *, world: dict | None = None):
    _patch_storage(tmp_path, monkeypatch)
    sid = scene["scene"]["id"]
    storage._save_json(storage.scene_path(sid), scene)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    storage._save_json(storage.WORLD_PATH, world or _quay_world())
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
    reg = sess.get(SESSION_LEAD_REGISTRY_KEY) or {}
    return {str(k) for k in reg.keys()} if isinstance(reg, dict) else set()


def _lead_titles(session: dict | None = None) -> list[str]:
    sess = session if isinstance(session, dict) else storage.load_session()
    reg = sess.get(SESSION_LEAD_REGISTRY_KEY) or {}
    if not isinstance(reg, dict):
        return []
    titles = []
    for row in reg.values():
        if isinstance(row, dict):
            titles.append(str(row.get("title") or ""))
    return titles


def _discovered_texts(session: dict, scene_id: str) -> list[str]:
    runtime = (session.get("scene_runtime") or {}).get(scene_id) or {}
    return [str(x) for x in (runtime.get("discovered_clues") or []) if isinstance(x, str)]


def _resolve(scene: dict, text: str, session: dict | None = None):
    parsed = parse_freeform_to_action(text, scene)
    action = normalize_scene_action(parsed)
    return resolve_exploration_action(
        scene,
        session if isinstance(session, dict) else {},
        {},
        action,
        raw_player_text=text,
    )


def test_look_toward_extracts_visible_feature_not_untargeted():
    scene = _quay_scene()
    text = "I thank the warden and look toward the cooper's bench again."
    classified = classify_referenced_surface(text, scene)
    assert classified["authority"] in {
        AUTHORITY_AUTHORED_VISIBLE_FEATURE,
        AUTHORITY_AUTHORED_INTERACTABLE,
    }
    assert classified["authority"] != AUTHORITY_UNTARGETED
    parsed = parse_freeform_to_action(text, scene)
    assert str(parsed.get("type") or "") == "investigate"
    meta = parsed.get("metadata") if isinstance(parsed.get("metadata"), dict) else {}
    assert meta.get("skip_unrelated_clue_discovery") is True
    res = _resolve(scene, text)
    assert res["kind"] == "investigate"
    assert res.get("clue_id") is None
    assert (res.get("metadata") or {}).get("skip_unrelated_clue_discovery") is True


def test_content_question_extracts_written_surface_not_untargeted():
    scene = _quay_scene(
        discoverable_clues=[{"id": "bench_wax", "text": WAX_STAIN}],
        interactables=[
            {
                "id": "coopers_bench",
                "label": "Cooper's bench",
                "aliases": ["bench", "slate", "bench slate"],
                "type": "investigate",
                "reveals_clue": "bench_wax",
            }
        ],
    )
    text = "What is posted on the bench slate?"
    assert extract_inspection_target(text) == "bench slate"
    classified = classify_referenced_surface(text, scene)
    assert classified["authority"] == AUTHORITY_AUTHORED_INTERACTABLE
    assert classified["authority"] != AUTHORITY_UNTARGETED
    res = _resolve(scene, text)
    assert res["kind"] == "discover_clue"
    assert res.get("clue_id") == "bench_wax"


def test_untargeted_investigate_skips_scene_clue_conveyor():
    scene = _quay_scene(discoverable_clues=[{"id": "window_prints", "text": BOOTPRINTS}])
    classified = classify_referenced_surface("I look.", scene)
    assert classified["authority"] == AUTHORITY_UNTARGETED
    assert metadata_from_classification(classified)["skip_unrelated_clue_discovery"] is True
    res = _resolve(scene, "I look.")
    assert res["kind"] == "investigate"
    assert (res.get("metadata") or {}).get("skip_unrelated_clue_discovery") is True
    assert res.get("clue_id") is None


def test_general_written_surface_question_discovers_authored_clue(tmp_path, monkeypatch):
    scene = _quay_scene(
        discoverable_clues=[{"id": "bench_wax", "text": WAX_STAIN}],
        interactables=[
            {
                "id": "coopers_bench",
                "label": "Cooper's bench",
                "aliases": ["bench", "slate", "bench slate"],
                "type": "investigate",
                "reveals_clue": "bench_wax",
            }
        ],
    )
    _seed(tmp_path, monkeypatch, scene)
    data = _chat(monkeypatch, "What is posted on the bench slate?", "A silver locket names the night buyer.")
    session = data.get("session") or {}
    assert (data.get("resolution") or {}).get("kind") == "discover_clue"
    assert "bench_wax" in _lead_ids(session)
    assert "silver locket" not in _facing(data).lower()


def test_general_visible_evidence_may_be_reported(tmp_path, monkeypatch):
    scene = _quay_scene()
    _seed(tmp_path, monkeypatch, scene)
    data = _chat(monkeypatch, "I examine the cooper's bench.", "A silver locket names the night buyer.")
    text = _facing(data).lower()
    assert "cooper" in text or "bench" in text
    assert "silver locket" not in text
    assert "night buyer" not in text


def test_general_hidden_discoverable_evidence_can_land(tmp_path, monkeypatch):
    scene = _quay_scene(
        discoverable_clues=[{"id": "window_prints", "text": BOOTPRINTS}],
        interactables=[
            {
                "id": "south_window",
                "label": "South window",
                "aliases": ["window", "floor", "tracks"],
                "type": "investigate",
                "reveals_clue": "window_prints",
            }
        ],
    )
    _seed(tmp_path, monkeypatch, scene)
    data = _chat(monkeypatch, "I search for tracks.", "You invent a signed confession.")
    session = data.get("session") or {}
    assert (data.get("resolution") or {}).get("kind") == "discover_clue"
    assert "window_prints" in _lead_ids(session)
    assert any(BOOTPRINTS.lower() in t.lower() for t in _lead_titles(session))
    assert BOOTPRINTS in _discovered_texts(session, "amber_quay")


def test_general_valid_target_no_evidence_is_grounded_absence(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _quay_scene())
    before = _lead_ids()
    data = _chat(monkeypatch, "I investigate the cooper's bench.", SUSPICIOUS_TITLE)
    session = data.get("session") or {}
    assert _lead_ids(session) == before
    assert SUSPICIOUS_SLUG not in _lead_ids(session)
    assert not any("timing" in t.lower() and "personnel" in t.lower() for t in _lead_titles(session))
    assert SUSPICIOUS_TITLE.lower() not in _facing(data).lower()


def test_general_requested_identity_absent_does_not_mint_person(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _quay_scene())
    data = _chat(
        monkeypatch,
        "I inspect the bench to see who used it last.",
        "The last user was Cooper Hale, who left at dusk.",
    )
    session = data.get("session") or {}
    blob = (_facing(data) + " " + json.dumps(_lead_titles(session))).lower()
    assert "cooper hale" not in blob
    assert "last user" not in json.dumps(session.get(SESSION_LEAD_REGISTRY_KEY) or {}).lower()
    assert not any("identity" in t.lower() or "last user" in t.lower() for t in _lead_titles(session))


def test_general_requested_time_absent_does_not_mint_timing(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _quay_scene())
    data = _chat(
        monkeypatch,
        "I inspect this to determine exactly when it happened.",
        "The bench was used at three bells exactly.",
    )
    session = data.get("session") or {}
    assert not any("three bells" in t.lower() or "exact" in t.lower() for t in _lead_titles(session))
    assert "three bells" not in json.dumps(session.get("clue_knowledge") or {}).lower()


def test_general_related_evidence_is_not_requested_property(tmp_path, monkeypatch):
    scene = _quay_scene(
        discoverable_clues=[{"id": "bench_wax", "text": WAX_STAIN}],
        interactables=[
            {
                "id": "coopers_bench",
                "label": "Cooper's bench",
                "aliases": ["bench", "desk"],
                "type": "investigate",
                "reveals_clue": "bench_wax",
            }
        ],
    )
    _seed(tmp_path, monkeypatch, scene)
    data = _chat(monkeypatch, "I inspect the desk to learn who used it last.", "The wax stain proves Mira used it.")
    session = data.get("session") or {}
    titles = " ".join(_lead_titles(session)).lower()
    assert "wax stain" in titles or WAX_STAIN.lower() in " ".join(_discovered_texts(session, "amber_quay")).lower()
    assert "mira" not in titles
    assert "who used" not in titles


def test_general_world_true_fact_does_not_leak_locally(tmp_path, monkeypatch):
    world = _quay_world()
    world["world_state"]["mara_owns_missing_key"] = True
    _seed(tmp_path, monkeypatch, _quay_scene(), world=world)
    data = _chat(
        monkeypatch,
        "I search the room for evidence Mara took the key.",
        "You find Mara's mark on the hidden key.",
    )
    session = data.get("session") or {}
    blob = json.dumps(session.get(SESSION_LEAD_REGISTRY_KEY) or {}).lower()
    assert "mara" not in blob
    assert "missing key" not in blob
    assert "mara" not in _facing(data).lower() or "no" in _facing(data).lower()


def test_general_false_player_hypothesis_is_not_adopted(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _quay_scene())
    data = _chat(
        monkeypatch,
        "I search the room for proof that Rowan poisoned the well.",
        "You find proof that Rowan poisoned the well.",
    )
    session = data.get("session") or {}
    blob = json.dumps(session.get(SESSION_LEAD_REGISTRY_KEY) or {}).lower()
    assert "rowan" not in blob
    assert "poison" not in blob
    data2 = _chat(monkeypatch, "I look for signs that Rowan was here.", "Rowan's bootprints cross the quay.")
    session2 = data2.get("session") or {}
    blob2 = json.dumps(session2.get(SESSION_LEAD_REGISTRY_KEY) or {}).lower()
    assert "rowan" not in blob2


def test_general_recent_conversation_does_not_become_evidence(tmp_path, monkeypatch):
    world = _quay_world(warden_topics=[{"id": "bell_time", "text": "The tide bell is rung at first light."}])
    _seed(tmp_path, monkeypatch, _quay_scene(), world=world)
    _chat(
        monkeypatch,
        "I ask the bell warden who last oiled the hinge.",
        'Bell Warden says, "No. I cannot answer that from what I know."',
    )
    data = _chat(monkeypatch, "I inspect the cooper's bench.", "The hinge-oiler was Joss.")
    session = data.get("session") or {}
    blob = json.dumps(session.get(SESSION_LEAD_REGISTRY_KEY) or {}).lower()
    assert "joss" not in blob
    assert "hinge" not in blob


def test_general_authorized_clue_consequence_still_fires(tmp_path, monkeypatch):
    scene = _quay_scene(
        discoverable_clues=[
            {
                "id": "chit_lead",
                "text": "A mill-chit is wedged under the bench lip.",
                "leads_to_scene": "frontier_gate",
            }
        ],
        interactables=[
            {
                "id": "coopers_bench",
                "label": "Cooper's bench",
                "aliases": ["bench"],
                "type": "investigate",
                "reveals_clue": "chit_lead",
            }
        ],
    )
    _seed(tmp_path, monkeypatch, scene)
    data = _chat(monkeypatch, "I examine the bench.", "Nothing useful.")
    session = data.get("session") or {}
    assert "chit_lead" in _lead_ids(session)
    assert (data.get("resolution") or {}).get("kind") == "discover_clue"


def test_general_unsourced_text_cannot_mint_clue(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _quay_scene())
    data = _chat(monkeypatch, "I investigate the cooper's bench.", SUSPICIOUS_TITLE)
    session = data.get("session") or {}
    assert SUSPICIOUS_SLUG not in _lead_ids(session)
    assert SUSPICIOUS_TITLE not in _lead_titles(session)
    assert SUSPICIOUS_TITLE not in _discovered_texts(session, "amber_quay")


def test_general_observe_empty_target_does_not_invent(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _quay_scene())
    data = _chat(monkeypatch, "I look toward the doorway.", "A sealed dossier names the duke's killer.")
    session = data.get("session") or {}
    assert "dossier" not in json.dumps(session.get(SESSION_LEAD_REGISTRY_KEY) or {}).lower()
    assert "duke" not in _facing(data).lower()


def test_general_investigate_empty_target_does_not_invent(tmp_path, monkeypatch):
    scene = _quay_scene(
        visible_facts=["A salt-stained doorway opens onto the quay."],
    )
    _seed(tmp_path, monkeypatch, scene)
    data = _chat(monkeypatch, "I investigate the doorway.", "You find a roster of exact watch times.")
    session = data.get("session") or {}
    assert not any("watch times" in t.lower() or "roster" in t.lower() for t in _lead_titles(session))


def test_general_player_specified_relation_does_not_become_schema(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _quay_scene())
    data = _chat(monkeypatch, "I inspect this for signs of who opened it.", "The opener was Mira.")
    session = data.get("session") or {}
    assert not any("opener" in t.lower() or "mira" in t.lower() for t in _lead_titles(session))


def test_general_authorized_different_evidence_is_not_rewritten(tmp_path, monkeypatch):
    scene = _quay_scene(
        discoverable_clues=[{"id": "bench_wax", "text": WAX_STAIN}],
        interactables=[
            {
                "id": "coopers_bench",
                "label": "Cooper's bench",
                "aliases": ["bench"],
                "type": "investigate",
                "reveals_clue": "bench_wax",
            }
        ],
    )
    _seed(tmp_path, monkeypatch, scene)
    data = _chat(monkeypatch, "I search the bench for Identity X.", "The wax stain is Mira's seal.")
    session = data.get("session") or {}
    titles = " ".join(_lead_titles(session)).lower()
    assert "wax" in titles
    assert "identity x" not in titles
    assert "mira" not in titles


def test_general_repeated_empty_investigation_does_not_accumulate(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _quay_scene())
    first = _chat(monkeypatch, "I investigate the cooper's bench.", "First invented timing clue.")
    second = _chat(monkeypatch, "I investigate the cooper's bench again.", "Second invented personnel clue.")
    session = second.get("session") or {}
    assert _lead_ids(first.get("session") or {}) == _lead_ids(session)
    assert not any("timing" in t.lower() or "personnel" in t.lower() for t in _lead_titles(session))


def test_general_rediscovery_does_not_duplicate_clue(tmp_path, monkeypatch):
    scene = _quay_scene(
        discoverable_clues=[{"id": "window_prints", "text": BOOTPRINTS}],
        interactables=[
            {
                "id": "south_window",
                "label": "South window",
                "aliases": ["window", "tracks"],
                "type": "investigate",
                "reveals_clue": "window_prints",
            }
        ],
    )
    _seed(tmp_path, monkeypatch, scene)
    first = _chat(monkeypatch, "I search for tracks.", "Narration.")
    second = _chat(monkeypatch, "I search for tracks again.", "Another narration.")
    session = second.get("session") or {}
    ids = [i for i in _lead_ids(session) if i == "window_prints"]
    assert ids == ["window_prints"]
    assert (second.get("resolution") or {}).get("kind") in {"already_searched", "discover_clue", "investigate"}


def test_canon_filter_excludes_overlay_injected_clue(tmp_path, monkeypatch):
    scene = _quay_scene()
    _seed(tmp_path, monkeypatch, scene)
    session = storage.load_session()
    overlay = storage.get_runtime_scene_overlay(session, "amber_quay")
    overlay.setdefault("mutations", {})["discoverable_clues_add"] = [SUSPICIOUS_TITLE]
    storage.save_session(session)
    effective = storage.get_effective_scene(session, "amber_quay")
    assert any(
        str(row) == SUSPICIOUS_TITLE or (isinstance(row, dict) and row.get("text") == SUSPICIOUS_TITLE)
        for row in (effective.get("scene") or {}).get("discoverable_clues") or []
    )
    canon = storage.load_scene("amber_quay")
    discovery_scene = {
        **effective,
        "scene": {
            **(effective.get("scene") or {}),
            "discoverable_clues": list((canon.get("scene") or {}).get("discoverable_clues") or []),
        },
    }
    revealed = process_investigation_discovery(discovery_scene, session)
    assert not any(
        (rec.get("text") if isinstance(rec, dict) else str(rec)) == SUSPICIOUS_TITLE
        for rec in revealed
    )


def test_overlay_injected_clue_is_not_authoritative_discovery(tmp_path, monkeypatch):
    scene = _quay_scene(discoverable_clues=[{"id": "window_prints", "text": BOOTPRINTS}])
    _seed(tmp_path, monkeypatch, scene)
    session = storage.load_session()
    overlay = storage.get_runtime_scene_overlay(session, "amber_quay")
    mutations = overlay.setdefault("mutations", {})
    mutations["discoverable_clues_add"] = [SUSPICIOUS_TITLE]
    storage.save_session(session)
    data = _chat(monkeypatch, "I investigate.", SUSPICIOUS_TITLE)
    after = data.get("session") or {}
    assert SUSPICIOUS_SLUG not in _lead_ids(after)
    assert SUSPICIOUS_TITLE not in _lead_titles(after)


def test_direct_helper_still_reveals_authored_next_clue():
    scene = _quay_scene(discoverable_clues=[{"id": "window_prints", "text": BOOTPRINTS}])
    session: dict = {}
    revealed = process_investigation_discovery(scene, session)
    assert len(revealed) == 1
    assert revealed[0]["text"] == BOOTPRINTS


def test_frontier_gate_t15_look_toward_does_not_mint_personnel_timing(tmp_path, monkeypatch):
    scene = json.loads(Path("data/scenes/frontier_gate.json").read_text(encoding="utf-8"))
    _seed(tmp_path, monkeypatch, scene, world=default_world())
    session = storage.load_session()
    process_investigation_discovery(scene, session)
    storage.save_session(session)
    before = _lead_ids(session)
    data = _chat(monkeypatch, T15_TEXT, SUSPICIOUS_TITLE)
    after = data.get("session") or {}
    assert SUSPICIOUS_SLUG not in _lead_ids(after)
    assert SUSPICIOUS_TITLE not in _lead_titles(after)
    assert _lead_ids(after) <= before | {"notice_patrol_route"}
    facing = _facing(data).lower()
    assert "exact timing" not in facing
    assert "personnel" not in facing
    res = data.get("resolution") or {}
    assert res.get("kind") in {"investigate", "observe"}
    assert res.get("clue_id") in {None, ""}


def test_anti_overfitting_generic_helpers_have_no_calibration_special_case():
    for path in GENERIC_ENGINE_FILES:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for term in CALIBRATION_ENGINE_TERMS:
            needle = term.lower()
            assert needle not in lowered, f"{path} newly mentions {term}"
