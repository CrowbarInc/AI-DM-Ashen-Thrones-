"""PR-AP: grounded absence must realize as complete player-facing language.

Synthetic fixtures use cedar-wharf / coil-warden vocabulary. Frontier Gate /
stew / last-checker cases are calibration regression only.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

from fastapi.testclient import TestClient

from game import storage
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)
from game.final_emission_repairs import repair_fallback_behavior
from game.final_emission_validators import (
    _contains_fabricated_authority,
    validate_fallback_behavior,
)
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.leads import SESSION_LEAD_REGISTRY_KEY
from game.playability_eval import _MALFORMED_REFUSAL_FRAGMENT_RE
from game.social import (
    authored_answer_sufficient_for_question,
    authored_topic_relevant_to_question,
    classify_social_question_dimension,
    realize_authored_knowledge_answer,
    resolve_social_action,
)
from game.social_exchange_fallback_catalog import strict_social_ownership_terminal_fallback
from game.api import app
from tests.helpers.fallback_behavior_fixtures import fallback_contract
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
    Path("game/final_emission_validators.py"),
    Path("game/final_emission_repairs.py"),
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
COIL_EXIST = "Tarred coils sit under the shed eaves."
COIL_COUNT = "Nine tarred coils sit under the shed eaves."
LEDGER_HOURS = "The lamp clerk posts the night hours on the pier slate."
HIDDEN_BUYER = "A sealed chit names the night buyer."
SKIFF_LEFT = "The grain skiff departed."
GATE_BARRED = "The pier gate is barred."
BROTH_EXISTS = "A kettle of broth sits on the brazier."
CRATE_EXISTS = "A sealed crate sits by the bollard."
BELL_REPAIRED = "The pier bell was recaulked."
MALFORMED_FRAGMENT = "from what."


def _wharf_scene() -> dict:
    return {
        "scene": {
            "id": "cedar_wharf",
            "location": "Cedar Wharf",
            "summary": "A coil shed, a pier slate, and a barred gate.",
            "visible_facts": [
                COIL_EXIST,
                SKIFF_LEFT,
                GATE_BARRED,
                BROTH_EXISTS,
                CRATE_EXISTS,
                BELL_REPAIRED,
            ],
            "hidden_facts": [HIDDEN_BUYER],
            "discoverable_clues": [],
            "addressables": [
                {
                    "id": "coil_warden",
                    "name": "Coil Warden",
                    "scene_id": "cedar_wharf",
                    "kind": "npc",
                    "addressable": True,
                    "address_roles": ["warden"],
                    "aliases": ["coil keeper"],
                },
                {
                    "id": "lamp_clerk",
                    "name": "Lamp Clerk",
                    "scene_id": "cedar_wharf",
                    "kind": "npc",
                    "addressable": True,
                    "address_roles": ["clerk"],
                    "aliases": [],
                },
            ],
            "interactables": [],
            "exits": [],
            "enemies": [],
            "actions": [],
        }
    }


def _wharf_world(*, warden_topics: list[dict] | None = None, clerk_topics: list[dict] | None = None) -> dict:
    return {
        "npcs": [
            {
                "id": "coil_warden",
                "name": "Coil Warden",
                "location": "cedar_wharf",
                "aliases": ["coil keeper"],
                "topics": warden_topics
                if warden_topics is not None
                else [{"id": "coil_exist", "text": COIL_EXIST}],
            },
            {
                "id": "lamp_clerk",
                "name": "Lamp Clerk",
                "location": "cedar_wharf",
                "topics": clerk_topics
                if clerk_topics is not None
                else [
                    {"id": "ledger_hours", "text": LEDGER_HOURS},
                    {"id": "night_buyer", "text": HIDDEN_BUYER},
                ],
            },
        ]
    }


def _session_for(world: dict, scene_id: str, scene: dict | None = None) -> dict:
    session = default_session()
    session["active_scene_id"] = scene_id
    rebuild_active_scene_entities(session, world, scene_id, scene_envelope=scene)
    return session


def _ask(world: dict, session: dict, npc_id: str, player_text: str, scene: dict | None = None) -> dict:
    envelope = scene or _wharf_scene()
    return resolve_social_action(
        envelope,
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


def _topic_id(resolution: dict) -> str:
    rec = ((resolution.get("social") or {}).get("topic_revealed") or {}) if isinstance(resolution, dict) else {}
    return str(rec.get("id") or "").strip()


def _topic_text(resolution: dict) -> str:
    rec = ((resolution.get("social") or {}).get("topic_revealed") or {}) if isinstance(resolution, dict) else {}
    return str(rec.get("text") or rec.get("clue_text") or "").strip()


def _seed_wharf_http(tmp_path, monkeypatch, *, world: dict | None = None, scene: dict | None = None):
    _patch_storage(tmp_path, monkeypatch)
    envelope = scene or _wharf_scene()
    sid = envelope["scene"]["id"]
    storage._save_json(storage.scene_path(sid), envelope)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    w = default_world()
    w["npcs"] = (world or _wharf_world())["npcs"]
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


def _assert_complete_refusal(text: str) -> str:
    raw = str(text or "").strip()
    assert raw
    low = raw.lower()
    assert not _MALFORMED_REFUSAL_FRAGMENT_RE.search(raw)
    assert MALFORMED_FRAGMENT not in low
    assert not re.search(r"\b(?:from|according to|based on)\s*[.\"']?\s*$", raw, re.I)
    assert not re.search(r"\s{2,}", raw)
    assert raw.count('"') % 2 == 0
    for term in INTERNAL_TERMS:
        assert term not in low
    return low


def _assert_no_invention(text: str, *banned: str) -> None:
    low = str(text or "").lower()
    for item in banned:
        assert item.lower() not in low


def test_repro_catalog_line_is_complete_before_downstream_strip():
    resolution = {"social": {"npc_id": "coil_warden", "npc_name": "Coil Warden"}}
    catalog = strict_social_ownership_terminal_fallback(resolution)
    assert "from what I know" in catalog
    assert not _MALFORMED_REFUSAL_FRAGMENT_RE.search(catalog)
    assert _contains_fabricated_authority(catalog) is False


def test_repro_old_strip_path_composed_malformed_from_what():
    raw = 'Coil Warden says, "No. I cannot answer that from what I know."'
    composed = re.sub(r"\bi know\b", "", raw, flags=re.I)
    composed = re.sub(r"\s+", " ", composed)
    composed = re.sub(r"\s+([.!?])", r"\1", composed)
    assert _MALFORMED_REFUSAL_FRAGMENT_RE.search(composed)
    assert "from what." in composed.lower()


def test_repair_keeps_catalog_knowledge_limit_refusal():
    raw = 'Coil Warden says, "No. I cannot answer that from what I know."'
    validation = validate_fallback_behavior(raw, fallback_contract(uncertainty_sources=["unknown_quantity"]))
    repaired, meta, _ = repair_fallback_behavior(raw, fallback_contract(), validation)
    _assert_complete_refusal(repaired)
    assert "from what i know" in repaired.lower()
    assert "remove_fabricated_authority" not in str(meta.get("fallback_behavior_repair_mode") or "")


def test_general_person_absence_is_grammatical(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch, world=_wharf_world(warden_topics=[{"id": "bell_event", "text": BELL_REPAIRED}]))
    q = "I ask the coil warden who recaulked the pier bell."
    data = _chat(monkeypatch, q, 'Coil Warden says, "No. I cannot answer that from what I know."')
    text = _facing(data)
    _assert_complete_refusal(text)
    _assert_no_invention(text, "joss", "mara", "neris", "rowen")
    assert _topic_id(data.get("resolution") or {}) == ""


def test_general_time_absence_is_grammatical(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch, world=_wharf_world(warden_topics=[{"id": "skiff_left", "text": SKIFF_LEFT}]))
    data = _chat(
        monkeypatch,
        "I ask the coil warden when the grain skiff left.",
        'Coil Warden says, "No. I cannot answer that from what I know."',
    )
    text = _facing(data)
    _assert_complete_refusal(text)
    _assert_no_invention(text, "dawn", "yesterday", "third bell", "noon")


def test_general_location_absence_is_grammatical(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch, world=_wharf_world(warden_topics=[{"id": "skiff_left", "text": SKIFF_LEFT}]))
    data = _chat(
        monkeypatch,
        "I ask the coil warden where the grain skiff went.",
        'Coil Warden says, "No. I cannot answer that from what I know."',
    )
    text = _facing(data)
    _assert_complete_refusal(text)
    _assert_no_invention(text, "river crossing", "east dock", "north road")


def test_general_cause_absence_is_grammatical(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch, world=_wharf_world(warden_topics=[{"id": "gate_barred", "text": GATE_BARRED}]))
    data = _chat(
        monkeypatch,
        "I ask the coil warden why the pier gate is barred.",
        'Coil Warden says, "No. I cannot answer that from what I know."',
    )
    text = _facing(data)
    _assert_complete_refusal(text)
    _assert_no_invention(text, "because", "storm", "curfew", "tax")


def test_general_quantity_absence_is_grammatical(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch)
    data = _chat(
        monkeypatch,
        "I ask the coil warden how many tarred coils sit under the shed eaves.",
        'Coil Warden says, "No. I cannot answer that from what I know."',
    )
    text = _facing(data)
    _assert_complete_refusal(text)
    _assert_no_invention(text, "nine", "dozen", "twelve")
    assert _topic_id(data.get("resolution") or {}) == ""


def test_general_value_absence_is_grammatical_without_economy(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch, world=_wharf_world(warden_topics=[{"id": "broth", "text": BROTH_EXISTS}]))
    data = _chat(
        monkeypatch,
        "I ask the coil warden how much the broth costs.",
        'Coil Warden says, "No. I cannot answer that from what I know."',
    )
    text = _facing(data)
    _assert_complete_refusal(text)
    _assert_no_invention(text, "copper", "silver", "price", "coin")


def test_general_content_absence_is_grammatical(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch, world=_wharf_world(warden_topics=[{"id": "crate", "text": CRATE_EXISTS}]))
    data = _chat(
        monkeypatch,
        "I ask the coil warden what is inside the sealed crate.",
        'Coil Warden says, "No. I cannot answer that from what I know."',
    )
    text = _facing(data)
    _assert_complete_refusal(text)
    _assert_no_invention(text, "chit", "ledger", "buyer")


def test_general_insufficient_related_fact_stays_rejected():
    world = _wharf_world(warden_topics=[{"id": "coil_exist", "text": COIL_EXIST}])
    session = _session_for(world, "cedar_wharf", _wharf_scene())
    q = "How many tarred coils sit under the shed eaves?"
    assert authored_topic_relevant_to_question(q, {"id": "coil_exist", "text": COIL_EXIST})
    assert not authored_answer_sufficient_for_question(q, {"id": "coil_exist", "text": COIL_EXIST})
    res = _ask(world, session, "coil_warden", q)
    assert _topic_id(res) == ""
    assert "nine" not in _topic_text(res).lower()


def test_general_unrelated_owned_topic_stays_rejected():
    world = _wharf_world()
    session = _session_for(world, "cedar_wharf", _wharf_scene())
    q = "When does the lamp clerk post the night hours?"
    res = _ask(world, session, "coil_warden", q)
    assert _topic_id(res) != "ledger_hours"
    assert "pier slate" not in _topic_text(res).lower()


def test_general_unauthorized_exact_answer_does_not_leak():
    world = _wharf_world(
        warden_topics=[{"id": "coil_exist", "text": COIL_EXIST}],
        clerk_topics=[{"id": "night_buyer", "text": HIDDEN_BUYER}],
    )
    session = _session_for(world, "cedar_wharf", _wharf_scene())
    set_social_target(session, "coil_warden")
    q = "Who does the sealed chit name?"
    res = _ask(world, session, "coil_warden", q)
    assert HIDDEN_BUYER not in _topic_text(res)
    realized = realize_authored_knowledge_answer(
        session=session,
        scene_id="cedar_wharf",
        player_text=q,
        resolution={"kind": "question", "social": {"npc_id": "coil_warden", "npc_name": "Coil Warden"}},
        world=world,
        scene=_wharf_scene(),
    )
    blob = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "night buyer" not in blob
    assert "sealed chit" not in blob or "cannot" in blob or "don't know" in blob or blob == ""


def test_optional_knowledge_limit_present_is_complete():
    raw = 'Coil Warden says, "No. I cannot answer that from what I know."'
    validation = validate_fallback_behavior(raw, fallback_contract())
    repaired, _, _ = repair_fallback_behavior(raw, fallback_contract(), validation)
    _assert_complete_refusal(repaired)
    assert "from what i know" in repaired.lower()


def test_optional_connector_absent_stays_complete():
    raw = 'Coil Warden says, "I cannot answer that."'
    validation = validate_fallback_behavior(raw, fallback_contract())
    repaired, _, _ = repair_fallback_behavior(raw, fallback_contract(), validation)
    _assert_complete_refusal(repaired)
    assert "from" not in repaired.lower()


def test_optional_connector_filtered_does_not_dangle():
    from game.final_emission_repairs import _drop_dangling_optional_connectors

    leftover = _drop_dangling_optional_connectors(
        'Coil Warden says, "No. I cannot answer that from what."'
    )
    _assert_complete_refusal(leftover)
    assert "from what" not in leftover.lower()


def test_empty_optional_value_does_not_malform():
    from game.final_emission_repairs import _drop_dangling_optional_connectors

    leftover = _drop_dangling_optional_connectors('Coil Warden says, "I cannot answer that from ."')
    _assert_complete_refusal(leftover)


def test_repeated_refusals_do_not_accumulate(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch)
    first = _chat(
        monkeypatch,
        "I ask the coil warden who recaulked the pier bell.",
        'Coil Warden says, "No. I cannot answer that from what I know."',
    )
    second = _chat(
        monkeypatch,
        "I ask the coil warden how much the broth costs.",
        'Coil Warden says, "No. I cannot answer that from what I know."',
    )
    t1 = _facing(first)
    t2 = _facing(second)
    _assert_complete_refusal(t1)
    _assert_complete_refusal(t2)
    assert t1.lower().count("cannot answer") <= 1
    assert t2.lower().count("cannot answer") <= 1


def test_refusal_then_answerable_question(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch)
    _chat(
        monkeypatch,
        "I ask the coil warden how much the broth costs.",
        'Coil Warden says, "No. I cannot answer that from what I know."',
    )
    data = _chat(
        monkeypatch,
        "I ask the coil warden what sits under the shed eaves.",
        'Coil Warden mutters, "Word is, tarred coils sit under the shed eaves."',
    )
    text = _facing(data).lower()
    assert "tarred coils" in text
    assert MALFORMED_FRAGMENT not in text


def test_answerable_then_refusal(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch)
    first = _chat(
        monkeypatch,
        "I ask the coil warden what sits under the shed eaves.",
        'Coil Warden mutters, "Word is, tarred coils sit under the shed eaves."',
    )
    assert "tarred coils" in _facing(first).lower()
    second = _chat(
        monkeypatch,
        "I ask the coil warden how much the broth costs.",
        'Coil Warden says, "No. I cannot answer that from what I know."',
    )
    text = _facing(second)
    _assert_complete_refusal(text)
    _assert_no_invention(text, "tarred coils")


def test_refusal_has_no_internal_terminology():
    raw = 'Coil Warden says, "No. I cannot answer that from what I know."'
    validation = validate_fallback_behavior(raw, fallback_contract())
    repaired, _, _ = repair_fallback_behavior(raw, fallback_contract(), validation)
    _assert_complete_refusal(repaired)


def test_refusal_does_not_invent_filler_source():
    raw = 'Coil Warden says, "I cannot answer that."'
    validation = validate_fallback_behavior(raw, fallback_contract())
    repaired, _, _ = repair_fallback_behavior(raw, fallback_contract(), validation)
    low = _assert_complete_refusal(repaired)
    assert "from the notices" not in low
    assert "from what i've heard" not in low
    assert "from the patrol" not in low


def test_dimension_matrix_classifies_absence_without_changing_semantics():
    assert classify_social_question_dimension("Who recaulked the pier bell?") == "identity"
    assert classify_social_question_dimension("When did the grain skiff leave?") == "time"
    assert classify_social_question_dimension("Where did the grain skiff go?") == "location"
    assert classify_social_question_dimension("Why is the pier gate barred?") == "cause"
    assert classify_social_question_dimension("How many tarred coils sit under the shed?") == "quantity"
    assert classify_social_question_dimension("How much does the broth cost?") == "quantity"


def test_distinct_refusal_semantics_are_not_flattened():
    resolution = {"social": {"npc_id": "coil_warden", "npc_name": "Coil Warden"}}
    catalog = strict_social_ownership_terminal_fallback(resolution)
    assert catalog != 'Coil Warden shakes their head. "I don\'t know."' or "from what I know" in catalog
    pool = {
        'Coil Warden shakes their head. "I don\'t know."',
        'Coil Warden says, "I do not know enough to answer that."',
        'Coil Warden says, "No. I cannot answer that from what I know."',
    }
    assert catalog in pool


def test_anti_overfitting_generic_files_have_no_calibration_special_case():
    for path in GENERIC_ENGINE_FILES:
        src = path.read_text(encoding="utf-8")
        for term in CALIBRATION_ENGINE_TERMS:
            assert term not in src, f"{path} contains calibration term {term!r}"
    for fn in (
        _contains_fabricated_authority,
        validate_fallback_behavior,
        repair_fallback_behavior,
    ):
        src = inspect.getsource(fn)
        for term in CALIBRATION_ENGINE_TERMS:
            assert term not in src, f"{fn.__name__} contains calibration term {term!r}"


def test_implementation_is_not_exact_string_replacement():
    src = Path("game/final_emission_validators.py").read_text(encoding="utf-8")
    assert "I cannot answer that from what." not in src
    repair_src = Path("game/final_emission_repairs.py").read_text(encoding="utf-8")
    assert "I cannot answer that from what." not in repair_src
    assert "_drop_dangling_optional_connectors" in repair_src
