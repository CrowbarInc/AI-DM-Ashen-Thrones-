"""PR-AU: grounded social absence must survive live-model realization.

Synthetic fixtures use kiln-yard / night-porter vocabulary. Frontier Gate /
stew / patrol strings are calibration residue only.
"""
from __future__ import annotations

import re
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
from game.interaction_context import rebuild_active_scene_entities
from game.social import (
    apply_authored_knowledge_realization_to_gm,
    player_facing_invents_unauthored_social_fact,
    realize_authored_knowledge_answer,
    resolve_social_action,
    select_best_social_answer_candidate,
)
from game.social_exchange_fallback_catalog import strict_social_ownership_terminal_fallback
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

CALIBRATION_ENGINE_TERMS = (
    "stew",
    "tavern_runner",
    "notice_board",
    "frontier_gate",
    "missing_patrol",
    "Cinderwatch",
    "Captain Thoran",
    "guard_captain",
    "old_milestone",
    "roster_board",
)
GENERIC_ENGINE_FILES = (
    Path("game/social.py"),
    Path("game/social_exchange_fallback_catalog.py"),
    Path("game/upstream_response_repairs.py"),
)
INTERNAL_TERMS = (
    "authored answer",
    "not in state",
    "dimension is unsupported",
    "eligible topic candidate",
    "clue_knowledge",
    "topic_revealed",
    "grounded absence",
    "answer sufficiency",
)
MASH_EXISTS = "A kettle of mash sits on the porter's brazier."
LEDGER_OWNER = "Clerk Harun at the tally desk keeps the firing ledgers."
INVENTED_PRICE = 'Night Porter says, "Two coppers a ladle, and the kettle is still hot."'
INVENTED_TIME = 'Night Porter mutters, "Word is, they were due to leave sometime before dawn."'
INVENTED_COUNT = 'Night Porter says, "Seven dozen, stacked against the north wall."'
INVENTED_IDENTITY = 'Night Porter says, "Mira from the dock office checked it after the second bell."'
INVENTED_REDIRECT = 'Night Porter says, "Speak to the ward clerk by the main gate if that still matters."'
NATURAL_ABSENCE = 'Night Porter shakes their head. "I couldn\'t tell you."'
NOVEL_INVENTION = 'Night Porter says, "The chimney flue was recaulked by three hired tilers at dusk."'


def _kiln_scene() -> dict:
    return {
        "scene": {
            "id": "kiln_yard",
            "location": "Kiln Yard",
            "summary": "A brick kiln, a tally slate, and a night porter.",
            "visible_facts": [
                "A brick kiln smokes under a tin roof.",
                "A tally slate hangs by the kiln door.",
                MASH_EXISTS,
            ],
            "hidden_facts": [],
            "discoverable_clues": [],
            "addressables": [
                {
                    "id": "night_porter",
                    "name": "Night Porter",
                    "scene_id": "kiln_yard",
                    "kind": "npc",
                    "addressable": True,
                    "address_roles": ["porter"],
                    "aliases": ["porter"],
                },
                {
                    "id": "kiln_clerk",
                    "name": "Kiln Clerk",
                    "scene_id": "kiln_yard",
                    "kind": "npc",
                    "addressable": True,
                    "aliases": ["clerk"],
                },
            ],
            "interactables": [
                {
                    "id": "tally_slate",
                    "label": "Tally slate",
                    "aliases": ["slate", "board"],
                    "type": "investigate",
                }
            ],
            "exits": [],
            "enemies": [],
            "actions": [],
        }
    }


def _kiln_world(*, porter_topics: list[dict] | None = None) -> dict:
    return {
        "npcs": [
            {
                "id": "night_porter",
                "name": "Night Porter",
                "location": "kiln_yard",
                "aliases": ["porter"],
                "topics": porter_topics
                if porter_topics is not None
                else [{"id": "mash_exists", "text": MASH_EXISTS}],
            },
            {
                "id": "kiln_clerk",
                "name": "Kiln Clerk",
                "location": "kiln_yard",
                "topics": [{"id": "ledger_owner", "text": LEDGER_OWNER}],
            },
        ]
    }


def _session_for(world: dict, scene: dict) -> dict:
    session = default_session()
    session["active_scene_id"] = scene["scene"]["id"]
    rebuild_active_scene_entities(session, world, scene["scene"]["id"], scene_envelope=scene)
    return session


def _ask(world: dict, session: dict, npc_id: str, player_text: str, scene: dict) -> dict:
    return resolve_social_action(
        scene,
        session,
        world,
        {
            "id": "question",
            "label": player_text,
            "type": "question",
            "prompt": player_text,
            "target_id": npc_id,
        },
        raw_player_text=player_text,
        character=default_character(),
        turn_counter=int(session.get("turn_counter") or 1),
    )


def _apply(player_text: str, invented: str, *, topics: list[dict] | None = None) -> tuple[dict, dict, dict]:
    scene = _kiln_scene()
    world = _kiln_world(porter_topics=topics)
    session = _session_for(world, scene)
    resolution = _ask(world, session, "night_porter", player_text, scene)
    gm = apply_authored_knowledge_realization_to_gm(
        {"player_facing_text": invented, "tags": []},
        player_text=player_text,
        resolution=resolution,
        session=session,
        world=world,
        scene=scene,
        scene_id="kiln_yard",
    )
    return gm, resolution, session


def _seed_kiln_http(tmp_path, monkeypatch, *, world: dict | None = None, scene: dict | None = None):
    _patch_storage(tmp_path, monkeypatch)
    envelope = scene or _kiln_scene()
    sid = envelope["scene"]["id"]
    storage._save_json(storage.scene_path(sid), envelope)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    w = default_world()
    w["npcs"] = (world or _kiln_world())["npcs"]
    storage._save_json(storage.WORLD_PATH, w)
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


def _assert_natural_absence(text: str) -> str:
    raw = str(text or "").strip()
    assert raw
    low = raw.lower()
    for term in INTERNAL_TERMS:
        assert term not in low
    assert not raw.endswith("…")
    assert raw[-1] in '.!?"”\''
    return raw


def test_engine_has_grounded_absence_before_realization():
    scene = _kiln_scene()
    world = _kiln_world()
    session = _session_for(world, scene)
    player_text = "I ask the night porter how much the mash costs."
    resolution = _ask(world, session, "night_porter", player_text, scene)
    soc = resolution.get("social") or {}
    assert resolution.get("kind") == "question"
    assert soc.get("topic_revealed") is None
    assert soc.get("reply_kind") == "refusal"
    assert realize_authored_knowledge_answer(
        session=session,
        scene_id="kiln_yard",
        player_text=player_text,
        resolution=resolution,
        world=world,
        scene=scene,
    ) is None
    cand = select_best_social_answer_candidate(
        session=session,
        scene_id="kiln_yard",
        npc_id="night_porter",
        topic_key=None,
        player_text=player_text,
        resolution=resolution,
        world=world,
        scene=scene,
    )
    assert cand.get("answer_kind") == "refusal"
    hint = str(resolution.get("hint") or "").lower()
    assert "no new information was revealed" in hint
    assert "without inventing" in hint
    assert "answer, refusal, evasion" not in hint


def test_unauthored_price_cannot_become_invented_price():
    gm, resolution, _session = _apply(
        "I ask the night porter how much the mash costs.",
        INVENTED_PRICE,
    )
    text = str(gm.get("player_facing_text") or "")
    _assert_natural_absence(text)
    assert "two coppers" not in text.lower()
    assert "copper" not in text.lower()
    assert text != INVENTED_PRICE
    assert "grounded_social_absence_realization" in (gm.get("tags") or [])
    catalog = strict_social_ownership_terminal_fallback(resolution)
    assert text == catalog


def test_unauthored_time_cannot_become_invented_time():
    gm, _resolution, _session = _apply(
        "I ask the night porter when the kiln crew actually left.",
        INVENTED_TIME,
    )
    text = str(gm.get("player_facing_text") or "").lower()
    _assert_natural_absence(gm.get("player_facing_text") or "")
    assert "before dawn" not in text
    assert "dawn" not in text


def test_unauthored_count_cannot_become_invented_count():
    gm, _resolution, _session = _apply(
        "I ask the night porter how many bricks are left in that stack.",
        INVENTED_COUNT,
    )
    text = str(gm.get("player_facing_text") or "").lower()
    _assert_natural_absence(gm.get("player_facing_text") or "")
    assert "seven dozen" not in text
    assert not re.search(r"\b\d+\b", text)


def test_unauthored_identity_cannot_become_invented_person():
    gm, _resolution, _session = _apply(
        "I ask the night porter who last read that tally slate.",
        INVENTED_IDENTITY,
    )
    text = str(gm.get("player_facing_text") or "")
    _assert_natural_absence(text)
    assert "mira" not in text.lower()
    assert "dock office" not in text.lower()
    assert "second bell" not in text.lower()


def test_unauthored_redirect_cannot_become_invented_redirect():
    gm, _resolution, _session = _apply(
        "I ask the night porter who keeps the firing ledgers.",
        INVENTED_REDIRECT,
    )
    text = str(gm.get("player_facing_text") or "").lower()
    _assert_natural_absence(gm.get("player_facing_text") or "")
    assert "ward clerk" not in text
    assert "main gate" not in text
    assert "speak to" not in text


def test_natural_absence_phrasing_is_kept():
    gm, _resolution, _session = _apply(
        "I ask the night porter how much the mash costs.",
        NATURAL_ABSENCE,
    )
    assert gm.get("player_facing_text") == NATURAL_ABSENCE
    assert "grounded_social_absence_realization" not in (gm.get("tags") or [])


def test_grounded_absence_survives_http_realization(tmp_path, monkeypatch):
    _seed_kiln_http(tmp_path, monkeypatch)
    data = _chat(
        monkeypatch,
        "I ask the night porter how much the mash costs.",
        INVENTED_PRICE,
    )
    text = _facing(data)
    _assert_natural_absence(text)
    assert "two coppers" not in text.lower()
    assert "player_facing_text" in (data.get("gm_output") or {})


def test_authored_knowledge_still_realizes():
    gm, resolution, _session = _apply(
        "I ask the night porter what sits on the brazier.",
        'Night Porter mutters, "Word is, a kettle of mash sits on the porter\'s brazier."',
    )
    soc = resolution.get("social") or {}
    assert isinstance(soc.get("topic_revealed"), dict)
    text = str(gm.get("player_facing_text") or "").lower()
    assert "kettle of mash" in text
    assert "grounded_social_absence_realization" not in (gm.get("tags") or [])


def test_authored_redirect_still_possible():
    gm, resolution, _session = _apply(
        "I ask the night porter who keeps the firing ledgers.",
        'Night Porter mutters, "Word is, Clerk Harun at the tally desk keeps the firing ledgers."',
        topics=[{"id": "ledger_owner", "text": LEDGER_OWNER}],
    )
    soc = resolution.get("social") or {}
    assert isinstance(soc.get("topic_revealed"), dict)
    text = str(gm.get("player_facing_text") or "").lower()
    assert "harun" in text
    assert "tally desk" in text
    assert "ward clerk" not in text


def test_novel_freeform_absence_is_protected():
    gm, _resolution, _session = _apply(
        "I ask the night porter who recaulked the chimney flue, and how many tilers did the job.",
        NOVEL_INVENTION,
    )
    text = str(gm.get("player_facing_text") or "").lower()
    _assert_natural_absence(gm.get("player_facing_text") or "")
    assert "three hired tilers" not in text
    assert "dusk" not in text
    assert "recaulked" not in text


def test_http_novel_freeform_absence_is_protected(tmp_path, monkeypatch):
    _seed_kiln_http(tmp_path, monkeypatch)
    data = _chat(
        monkeypatch,
        "I ask the night porter who recaulked the chimney flue, and how many tilers did the job.",
        NOVEL_INVENTION,
    )
    text = _facing(data)
    _assert_natural_absence(text)
    assert "three hired tilers" not in text.lower()
    assert "dusk" not in text.lower()
    assert "recaulked" not in text.lower()


def test_http_refusal_grammar_still_intact(tmp_path, monkeypatch):
    _seed_kiln_http(tmp_path, monkeypatch)
    data = _chat(
        monkeypatch,
        "I ask the night porter how much the mash costs.",
        'Night Porter says, "No. I cannot answer that from what I know."',
    )
    text = _facing(data)
    _assert_natural_absence(text)
    assert "from what." not in text.lower()
    assert "from what i know" in text.lower() or "don't know" in text.lower() or "do not know" in text.lower()


def test_invention_detector_does_not_flag_catalog_absence():
    catalog = strict_social_ownership_terminal_fallback(
        {
            "social": {
                "npc_id": "night_porter",
                "npc_name": "Night Porter",
            }
        }
    )
    assert not player_facing_invents_unauthored_social_fact(
        catalog,
        speaker_id="night_porter",
        speaker_name="Night Porter",
    )
    assert not player_facing_invents_unauthored_social_fact(
        NATURAL_ABSENCE,
        speaker_id="night_porter",
        speaker_name="Night Porter",
    )
    assert player_facing_invents_unauthored_social_fact(
        INVENTED_PRICE,
        speaker_id="night_porter",
        speaker_name="Night Porter",
    )


def test_no_frontier_gate_special_case_in_touched_engine():
    for path in GENERIC_ENGINE_FILES:
        blob = path.read_text(encoding="utf-8")
        added = blob
        for term in CALIBRATION_ENGINE_TERMS:
            if term == "stew" and path.name == "social_exchange_fallback_catalog.py":
                continue
            if term.lower() in added.lower() and path.name == "social.py":
                # pre-existing social.py may mention calibration terms elsewhere;
                # PR-AU helpers must not introduce them.
                helper = added[added.find("_PRICE_INVENTION_RE"): added.find("def apply_authored_knowledge_realization_to_gm")]
                assert term.lower() not in helper.lower(), f"{term} in PR-AU helper block of {path}"
