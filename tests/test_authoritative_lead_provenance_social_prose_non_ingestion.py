"""PR-AJ: narration communicates authority; it does not mint it.

Synthetic fixtures use Salt Harbor / kelp-shed vocabulary. Frontier Gate
cases are calibration regression only.
"""

from __future__ import annotations

import inspect

from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.clues import _social_resolution_carries_information, get_all_known_clue_ids
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)
from game.intent_parser import _actionable_pending_with_registry_rows
from game.interaction_context import inspect as inspect_interaction_context
from game.interaction_context import rebuild_active_scene_entities
from game.leads import SESSION_LEAD_REGISTRY_KEY, ensure_lead_registry, get_lead
from game.narration_state_consistency import reconcile_final_text_with_structured_state
from game.storage import get_scene_runtime, load_session
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

CALIBRATION_ENGINE_TERMS = (
    "guard_captain",
    "Captain Thoran",
    "frontier_gate",
    "Cinderwatch",
    "old_milestone",
    "patrol",
    "watch_command",
    "were_maintaining_a_strict",
    "narration_ctx_frontier_gate_were_maintaining_a_strict",
)
TIDE_FACT = "Tide marks are painted at the second piling."
KELP_FACT = "The kelp shed key hangs on the inner hook."
KELP_LEAD_ID = "kelp_shed_key"
SUGGESTIVE_PROSE = (
    'Harbor Clerk leans on the desk. "The western trestle is closed to carts '
    'after dusk, and anyone serious should start at the coal loft before the tide turns."'
)
SUGGESTIVE_PARAPHRASE = (
    'Harbor Clerk shakes their head. "You will not get a cart across the western '
    'trestle after dusk. Serious folk begin at the coal loft while the water is still slack."'
)
LEAD_PROSE_A = (
    'Harbor Clerk taps the hook rail. "The kelp shed key hangs on the inner hook."'
)
LEAD_PROSE_B = (
    "You will not find that key on the open counter. It stays on the inner hook "
    "inside the kelp shed."
)
MENTION_PROSE = (
    "Harbor Clerk nods at the rail. \"Same as before: the kelp shed key still "
    "hangs on the inner hook if you mean to use it.\""
)


def _harbor_scene() -> dict:
    return {
        "scene": {
            "id": "salt_harbor",
            "location": "Salt Harbor",
            "summary": "A quiet slip, a clerk desk, and a walk toward the kelp shed.",
            "visible_facts": [
                "A clerk desk faces the inner slip.",
                "An inner walk runs toward a locked kelp shed.",
            ],
            "hidden_facts": ["A brass token is sealed under the quay stones."],
            "discoverable_clues": [],
            "addressables": [
                {
                    "id": "harbor_clerk",
                    "name": "Harbor Clerk",
                    "scene_id": "salt_harbor",
                    "kind": "npc",
                    "addressable": True,
                    "address_roles": ["clerk"],
                    "aliases": [],
                },
                {
                    "id": "net_mender",
                    "name": "Net Mender",
                    "scene_id": "salt_harbor",
                    "kind": "npc",
                    "addressable": True,
                    "address_roles": ["mender"],
                    "aliases": [],
                },
            ],
            "interactables": [],
            "exits": [
                {
                    "label": "Take the inner walk to the kelp shed",
                    "target_scene_id": "kelp_shed",
                }
            ],
            "enemies": [],
            "actions": [],
        }
    }


def _kelp_scene() -> dict:
    return {
        "scene": {
            "id": "kelp_shed",
            "location": "Kelp Shed",
            "summary": "A locked shed above the inner slip.",
            "visible_facts": ["Hooks line the inner wall."],
            "addressables": [],
            "interactables": [],
            "exits": [
                {
                    "label": "Return along the inner walk to the harbor",
                    "target_scene_id": "salt_harbor",
                }
            ],
            "enemies": [],
            "actions": [],
        }
    }


def _info_world() -> dict:
    return {
        "npcs": [
            {
                "id": "harbor_clerk",
                "name": "Harbor Clerk",
                "location": "salt_harbor",
                "topics": [{"id": "tide_marks", "text": TIDE_FACT}],
            },
            {
                "id": "net_mender",
                "name": "Net Mender",
                "location": "salt_harbor",
                "topics": [{"id": "net_repairs", "text": "Nets dry on the south racks until noon."}],
            },
        ]
    }


def _silent_world() -> dict:
    return {
        "npcs": [
            {
                "id": "harbor_clerk",
                "name": "Harbor Clerk",
                "location": "salt_harbor",
                "topics": [],
            }
        ]
    }


def _lead_world() -> dict:
    return {
        "npcs": [
            {
                "id": "harbor_clerk",
                "name": "Harbor Clerk",
                "location": "salt_harbor",
                "topics": [
                    {
                        "id": "kelp_key",
                        "text": KELP_FACT,
                        "clue_id": KELP_LEAD_ID,
                        "leads_to_scene": "kelp_shed",
                    }
                ],
            }
        ]
    }


def _empty_question_resolution(*, npc_id: str = "harbor_clerk", npc_name: str = "Harbor Clerk") -> dict:
    return {
        "kind": "question",
        "action_id": "q",
        "label": "Ask",
        "prompt": "Ask",
        "success": None,
        "clue_id": None,
        "discovered_clues": [],
        "hint": "Player spoke with the clerk. No new information was revealed. Narrate refusal.",
        "social": {
            "npc_id": npc_id,
            "npc_name": npc_name,
            "target_resolved": True,
            "topic_revealed": None,
            "social_intent_class": "social_exchange",
        },
        "requires_check": False,
    }


def _lead_ids(session: dict) -> list[str]:
    ensure_lead_registry(session)
    reg = session.get(SESSION_LEAD_REGISTRY_KEY) or {}
    return [str(k) for k in reg.keys()] if isinstance(reg, dict) else []


def _narration_ctx_ids(session: dict) -> list[str]:
    found: list[str] = []
    for item in _lead_ids(session):
        if "narration_ctx" in item:
            found.append(item)
    for item in get_all_known_clue_ids(session):
        if "narration_ctx" in str(item) and str(item) not in found:
            found.append(str(item))
    return found


def _pending(session: dict, scene_id: str) -> list[dict]:
    rt = get_scene_runtime(session, scene_id)
    return [p for p in (rt.get("pending_leads") or []) if isinstance(p, dict)]


def _seed_harbor_http(tmp_path, monkeypatch, *, world: dict | None = None) -> str:
    _patch_storage(tmp_path, monkeypatch)
    harbor = _harbor_scene()
    kelp = _kelp_scene()
    storage._save_json(storage.scene_path("salt_harbor"), harbor)
    storage._save_json(storage.scene_path("kelp_shed"), kelp)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    w = default_world()
    w["npcs"] = (world or _info_world())["npcs"]
    storage._save_json(storage.WORLD_PATH, w)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = "salt_harbor"
    session["visited_scene_ids"] = ["salt_harbor"]
    rebuild_active_scene_entities(session, w, "salt_harbor", scene_envelope=harbor)
    storage.save_session(session)
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    return "salt_harbor"


def _chat(monkeypatch, text: str, gm_text: str) -> dict:
    monkeypatch.setattr("game.api.call_gpt", lambda _messages: _gm_response(gm_text))
    client = TestClient(app)
    resp = client.post("/api/chat", json={"text": text})
    assert resp.status_code == 200
    return resp.json()


def _facing(data: dict) -> str:
    return str((data.get("gm_output") or {}).get("player_facing_text") or "")


def _session(data: dict) -> dict:
    sess = data.get("session")
    return sess if isinstance(sess, dict) else {}


def test_reconcile_informational_prose_does_not_mint_narration_ctx():
    session: dict = {}
    world = default_world()
    scene = _harbor_scene()
    res = _empty_question_resolution()
    gm = {"player_facing_text": SUGGESTIVE_PROSE, "tags": []}
    meta = reconcile_final_text_with_structured_state(
        session=session, scene=scene, world=world, resolution=res, gm_output=gm
    )
    assert meta["narration_state_mismatch_detected"] is True
    assert meta["mismatch_repair_applied"] == "fail_closed_no_authoritative_provenance"
    assert meta.get("prose_derived_authority_suppressed") is True
    assert not _social_resolution_carries_information(res)
    assert _narration_ctx_ids(session) == []
    assert not get_all_known_clue_ids(session)
    assert _pending(session, "salt_harbor") == []


def test_reconcile_paraphrase_invariance_without_structured_lead():
    outcomes = []
    for prose in (SUGGESTIVE_PROSE, SUGGESTIVE_PARAPHRASE):
        session: dict = {}
        res = _empty_question_resolution()
        reconcile_final_text_with_structured_state(
            session=session,
            scene=_harbor_scene(),
            world=default_world(),
            resolution=res,
            gm_output={"player_facing_text": prose, "tags": []},
        )
        outcomes.append(
            (
                _social_resolution_carries_information(res),
                tuple(sorted(_lead_ids(session))),
                tuple(sorted(get_all_known_clue_ids(session))),
                res.get("clue_id"),
            )
        )
    assert outcomes[0] == outcomes[1]
    assert outcomes[0][0] is False


def test_general_http_informational_social_prose_mints_no_lead(tmp_path, monkeypatch):
    _seed_harbor_http(tmp_path, monkeypatch, world=_silent_world())
    data = _chat(
        monkeypatch,
        'I turn to the Harbor Clerk. "How do you mark the tide here?"',
        SUGGESTIVE_PROSE,
    )
    sess = _session(data)
    assert "trestle" in _facing(data).lower() or "coal loft" in _facing(data).lower()
    assert _narration_ctx_ids(sess) == []
    assert not any(str(cid).startswith("narration_ctx_") for cid in get_all_known_clue_ids(sess))
    assert _pending(sess, "salt_harbor") == []
    assert _actionable_pending_with_registry_rows(sess, "salt_harbor") == []


def test_general_http_paraphrased_information_same_authority(tmp_path, monkeypatch):
    snapshots = []
    for prose in (SUGGESTIVE_PROSE, SUGGESTIVE_PARAPHRASE):
        _seed_harbor_http(tmp_path, monkeypatch, world=_silent_world())
        data = _chat(
            monkeypatch,
            'I turn to the Harbor Clerk. "How do you mark the tide here?"',
            prose,
        )
        sess = _session(data)
        snapshots.append(
            (
                tuple(sorted(_lead_ids(sess))),
                tuple(sorted(get_all_known_clue_ids(sess))),
                tuple(
                    (
                        p.get("authoritative_lead_id"),
                        p.get("leads_to_scene"),
                        p.get("leads_to_npc"),
                    )
                    for p in _pending(sess, "salt_harbor")
                ),
            )
        )
    assert snapshots[0] == snapshots[1]
    assert snapshots[0][0] == ()
    assert snapshots[0][2] == ()


def test_general_http_structured_lead_survives_wording(tmp_path, monkeypatch):
    _seed_harbor_http(tmp_path, monkeypatch, world=_lead_world())
    data = _chat(
        monkeypatch,
        'I turn to the Harbor Clerk. "Where is the kelp shed key kept?"',
        LEAD_PROSE_A,
    )
    sess = _session(data)
    assert "inner hook" in _facing(data).lower()
    assert get_lead(sess, KELP_LEAD_ID) is not None
    assert KELP_LEAD_ID in get_all_known_clue_ids(sess)
    assert _narration_ctx_ids(sess) == []
    pending = _pending(sess, "salt_harbor")
    assert any(p.get("authoritative_lead_id") == KELP_LEAD_ID for p in pending)
    assert any(p.get("leads_to_scene") == "kelp_shed" for p in pending)


def test_general_http_structured_lead_paraphrase_no_duplicate(tmp_path, monkeypatch):
    ids = []
    for prose in (LEAD_PROSE_A, LEAD_PROSE_B):
        _seed_harbor_http(tmp_path, monkeypatch, world=_lead_world())
        data = _chat(
            monkeypatch,
            'I turn to the Harbor Clerk. "Where is the kelp shed key kept?"',
            prose,
        )
        sess = _session(data)
        ids.append(tuple(sorted(_lead_ids(sess))))
        assert get_lead(sess, KELP_LEAD_ID) is not None
        assert _narration_ctx_ids(sess) == []
        assert sum(1 for lid in _lead_ids(sess) if lid == KELP_LEAD_ID) == 1
    assert ids[0] == ids[1]


def test_general_http_existing_lead_mention_does_not_duplicate(tmp_path, monkeypatch):
    _seed_harbor_http(tmp_path, monkeypatch, world=_lead_world())
    first = _chat(
        monkeypatch,
        'I turn to the Harbor Clerk. "Where is the kelp shed key kept?"',
        LEAD_PROSE_A,
    )
    before = tuple(sorted(_lead_ids(_session(first))))
    assert KELP_LEAD_ID in before
    second = _chat(
        monkeypatch,
        'I stay with the Harbor Clerk. "You mentioned that key again?"',
        MENTION_PROSE,
    )
    after = _session(second)
    assert tuple(sorted(_lead_ids(after))) == before
    assert _narration_ctx_ids(after) == []
    assert sum(1 for lid in _lead_ids(after) if lid == KELP_LEAD_ID) == 1


def test_general_http_suggestive_prose_is_not_pursuit_surface(tmp_path, monkeypatch):
    _seed_harbor_http(tmp_path, monkeypatch, world=_silent_world())
    first = _chat(
        monkeypatch,
        'I turn to the Harbor Clerk. "Any advice before I move?"',
        SUGGESTIVE_PROSE,
    )
    sess = _session(first)
    assert _narration_ctx_ids(sess) == []
    assert _actionable_pending_with_registry_rows(sess, "salt_harbor") == []
    second = _chat(
        monkeypatch,
        "I'll go check that western trestle the clerk just mentioned.",
        "You remain at the clerk desk; no trestle path opens from here.",
    )
    after = _session(second)
    assert _narration_ctx_ids(after) == []
    assert _actionable_pending_with_registry_rows(after, "salt_harbor") == []
    res = second.get("resolution") if isinstance(second.get("resolution"), dict) else {}
    assert str(res.get("target_scene_id") or "").strip() in {"", "salt_harbor"}
    assert res.get("resolved_transition") is not True


def test_general_http_authorized_pursuit_surface_sees_structured_lead(tmp_path, monkeypatch):
    _seed_harbor_http(tmp_path, monkeypatch, world=_lead_world())
    first = _chat(
        monkeypatch,
        'I turn to the Harbor Clerk. "Where is the kelp shed key kept?"',
        LEAD_PROSE_A,
    )
    sess = _session(first)
    rows = _actionable_pending_with_registry_rows(sess, "salt_harbor")
    assert any(str(p.get("authoritative_lead_id") or "") == KELP_LEAD_ID for p in rows)
    assert get_lead(sess, KELP_LEAD_ID) is not None


def test_general_http_provenance_survives_persistence(tmp_path, monkeypatch):
    _seed_harbor_http(tmp_path, monkeypatch, world=_lead_world())
    _chat(
        monkeypatch,
        'I turn to the Harbor Clerk. "Where is the kelp shed key kept?"',
        LEAD_PROSE_A,
    )
    loaded = load_session()
    assert get_lead(loaded, KELP_LEAD_ID) is not None
    assert _narration_ctx_ids(loaded) == []
    row = get_lead(loaded, KELP_LEAD_ID) or {}
    assert str(row.get("discovery_source") or "")
    _seed_harbor_http(tmp_path, monkeypatch, world=_silent_world())
    _chat(
        monkeypatch,
        'I turn to the Harbor Clerk. "Any advice before I move?"',
        SUGGESTIVE_PROSE,
    )
    reloaded = load_session()
    assert _narration_ctx_ids(reloaded) == []
    assert get_lead(reloaded, KELP_LEAD_ID) is None


def test_general_http_model_wording_does_not_change_mechanics(tmp_path, monkeypatch):
    variants = (
        'Harbor Clerk shrugs. "Tide marks are painted at the second piling."',
        "The second piling still carries the painted tide marks, nothing more.",
        "If you want the marks, look at the second piling. That is all the clerk will give.",
    )
    snapshots = []
    for prose in variants:
        _seed_harbor_http(tmp_path, monkeypatch, world=_info_world())
        data = _chat(
            monkeypatch,
            'I turn to the Harbor Clerk. "How do you mark the tide here?"',
            prose,
        )
        sess = _session(data)
        snapshots.append(
            (
                tuple(sorted(lid for lid in _lead_ids(sess) if "narration_ctx" in lid)),
                tuple(
                    (
                        p.get("authoritative_lead_id"),
                        p.get("leads_to_scene"),
                    )
                    for p in _pending(sess, "salt_harbor")
                    if p.get("leads_to_scene") or p.get("leads_to_npc")
                ),
            )
        )
    assert len(set(snapshots)) == 1
    assert snapshots[0][0] == ()


def test_calibration_http_captain_answer_does_not_mint_narration_ctx(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    storage._save_json(storage.scene_path("old_milestone"), default_scene("old_milestone"))
    world = default_world()
    world["npcs"] = [
        {
            "id": "gate_guard",
            "name": "Gate Guard",
            "location": "frontier_gate",
            "aliases": ["guard", "watch", "watch guard"],
            "topics": [
                {
                    "id": "watch_command",
                    "text": "Captain Thoran commands the gate watch tonight.",
                    "clue_id": "captain_thoran_watch",
                }
            ],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    storage.save_session(session)
    data = _chat(
        monkeypatch,
        'I turn to the Guard Captain. "Who commands the watch here?"',
        (
            '"We\'re maintaining a strict watch along the northwest mud track, '
            'where the patrol was last seen," says the guard captain.'
        ),
    )
    sess = _session(data)
    text = _facing(data)
    low = text.lower()
    assert "i don't know" not in low
    assert "thoran" in low or "maintaining a strict" in low or "watch" in low
    assert inspect_interaction_context(sess).get("active_interaction_target_id") == "guard_captain"
    assert "narration_ctx_frontier_gate_were_maintaining_a_strict" not in _lead_ids(sess)
    assert _narration_ctx_ids(sess) == []


def test_generic_reconcile_has_no_calibration_special_case():
    src = inspect.getsource(reconcile_final_text_with_structured_state)
    marker = "fail_closed_no_authoritative_provenance"
    assert marker in src
    else_block = src.split("fail_closed_no_authoritative_provenance", 1)[-1]
    for term in CALIBRATION_ENGINE_TERMS:
        assert term not in else_block
