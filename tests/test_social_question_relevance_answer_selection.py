"""PR-AL: speaker authorization and question relevance are distinct predicates.

Synthetic fixtures use brine-yard vocabulary. Frontier Gate / stew cases are
calibration regression only.
"""

from __future__ import annotations

import inspect
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
from game.interaction_context import inspect as inspect_interaction_context
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.leads import SESSION_LEAD_REGISTRY_KEY
from game.social import (
    _next_topic_to_reveal,
    _question_subject_tokens,
    apply_authored_knowledge_realization_to_gm,
    authored_topic_relevant_to_question,
    realize_authored_knowledge_answer,
    resolve_social_action,
)
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

CALIBRATION_ENGINE_TERMS = (
    "stew",
    "tavern",
    "runner",
    "muddy_footprints_northwest",
    "minlead_exit_frontier_gate_old_milestone",
    "guard_captain",
    "Captain Thoran",
    "frontier_gate",
    "Cinderwatch",
    "patrol",
    "old_milestone",
)
KILN_FACT = "Kiln three is banked from dusk until the morning bell."
CHIT_FACT = "The barge clerk hides a copper chit under the weigh-stone."
SALT_FACT = "Rakers scrape the north pans after the second horn."
HIDDEN_FACT = "A sealed ledger names the night buyer."
PATROL_RUMOR = "The runner heard the patrol vanished near muddy footprints northwest of the crates."
STEW_RELATED = "Hot stew and rumors for coin."
CHIT_LEAD_ID = "barge_chit_lead"


def _brine_scene() -> dict:
    return {
        "scene": {
            "id": "brine_yard",
            "location": "Brine Yard",
            "summary": "A salt kiln, a weigh-stone, and north pans.",
            "visible_facts": [
                "Kiln three smokes under a tarred hood.",
                "A weigh-stone sits by the barge slip.",
            ],
            "hidden_facts": [HIDDEN_FACT],
            "discoverable_clues": [{"id": CHIT_LEAD_ID, "text": CHIT_FACT}],
            "addressables": [
                {
                    "id": "kiln_tender",
                    "name": "Kiln Tender",
                    "scene_id": "brine_yard",
                    "kind": "npc",
                    "addressable": True,
                    "address_roles": ["tender"],
                    "aliases": ["fire warden"],
                },
                {
                    "id": "salt_raker",
                    "name": "Salt Raker",
                    "scene_id": "brine_yard",
                    "kind": "npc",
                    "addressable": True,
                    "address_roles": ["raker"],
                    "aliases": [],
                },
            ],
            "interactables": [],
            "exits": [{"label": "Follow the weigh-stone chit", "target_scene_id": "weigh_dock"}],
            "enemies": [],
            "actions": [],
        }
    }


def _brine_world() -> dict:
    return {
        "npcs": [
            {
                "id": "kiln_tender",
                "name": "Kiln Tender",
                "location": "brine_yard",
                "aliases": ["fire warden"],
                "topics": [
                    {"id": "kiln_bank", "text": KILN_FACT},
                    {
                        "id": "barge_chit",
                        "text": CHIT_FACT,
                        "clue_id": CHIT_LEAD_ID,
                        "leads_to_scene": "weigh_dock",
                    },
                ],
            },
            {
                "id": "salt_raker",
                "name": "Salt Raker",
                "location": "brine_yard",
                "topics": [{"id": "pan_schedule", "text": SALT_FACT}],
            },
        ]
    }


def _session_for(world: dict, scene_id: str, scene: dict | None = None) -> dict:
    session = default_session()
    session["active_scene_id"] = scene_id
    rebuild_active_scene_entities(session, world, scene_id, scene_envelope=scene)
    return session


def _ask(world: dict, session: dict, npc_id: str, player_text: str, scene: dict | None = None) -> dict:
    envelope = scene or _brine_scene()
    sid = str((envelope.get("scene") or {}).get("id") or "brine_yard")
    action = {
        "id": "question",
        "label": player_text,
        "type": "question",
        "prompt": player_text,
        "target_id": npc_id,
    }
    return resolve_social_action(
        envelope,
        session,
        world,
        action,
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


def _realize(world: dict, session: dict, player_text: str, npc_id: str | None, scene: dict | None = None):
    name = None
    if npc_id:
        row = next((n for n in world.get("npcs") or [] if n.get("id") == npc_id), None)
        name = str((row or {}).get("name") or "").strip() or None
    social = {"social_intent_class": "social_exchange", "target_resolved": bool(npc_id)}
    if npc_id:
        social["npc_id"] = npc_id
        social["npc_name"] = name or npc_id.replace("_", " ").title()
    return realize_authored_knowledge_answer(
        session=session,
        scene_id=str(((scene or _brine_scene()).get("scene") or {}).get("id") or "brine_yard"),
        player_text=player_text,
        resolution={"kind": "question", "social": social},
        world=world,
        scene=scene or _brine_scene(),
    )


def _seed_brine_http(tmp_path, monkeypatch, *, world: dict | None = None, scene: dict | None = None):
    _patch_storage(tmp_path, monkeypatch)
    envelope = scene or _brine_scene()
    sid = envelope["scene"]["id"]
    storage._save_json(storage.scene_path(sid), envelope)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    w = default_world()
    w["npcs"] = (world or _brine_world())["npcs"]
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


def _lead_ids(session: dict) -> set[str]:
    reg = session.get(SESSION_LEAD_REGISTRY_KEY) or {}
    return {str(k) for k in reg.keys()} if isinstance(reg, dict) else set()


def test_general_ask_about_a_does_not_emit_b():
    world = _brine_world()
    session = _session_for(world, "brine_yard", _brine_scene())
    res = _ask(world, session, "kiln_tender", "When is kiln three banked?")
    assert _topic_id(res) == "kiln_bank"
    assert "morning bell" in _topic_text(res).lower()
    assert "copper chit" not in _topic_text(res).lower()
    assert res.get("clue_id") not in {CHIT_LEAD_ID, "barge_chit"}
    assert CHIT_FACT not in (res.get("discovered_clues") or [])


def test_general_ask_about_b_does_not_emit_a():
    world = _brine_world()
    session = _session_for(world, "brine_yard", _brine_scene())
    res = _ask(world, session, "kiln_tender", "Where does the barge clerk hide the copper chit?")
    assert _topic_id(res) == "barge_chit"
    assert "weigh-stone" in _topic_text(res).lower()
    assert "kiln three" not in _topic_text(res).lower()


def test_general_unsupported_question_does_not_substitute_or_invent():
    world = _brine_world()
    session = _session_for(world, "brine_yard", _brine_scene())
    res = _ask(world, session, "kiln_tender", "How much does a sack of kiln ash cost?")
    assert _topic_id(res) == ""
    assert res.get("clue_id") is None
    assert res.get("discovered_clues") == []
    text = _topic_text(res).lower()
    assert "copper chit" not in text
    assert "morning bell" not in text
    realized = _realize(world, session, "How much does a sack of kiln ash cost?", "kiln_tender")
    blob = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "copper chit" not in blob
    assert "twelve" not in blob
    assert "silver" not in blob
    assert HIDDEN_FACT.lower() not in blob


def test_general_relevant_but_unauthorized_does_not_leak():
    world = _brine_world()
    session = _session_for(world, "brine_yard", _brine_scene())
    set_social_target(session, "kiln_tender")
    res = _ask(world, session, "kiln_tender", "When do the rakers scrape the north pans?")
    assert SALT_FACT not in _topic_text(res)
    assert _topic_id(res) != "pan_schedule"
    realized = _realize(world, session, "When do the rakers scrape the north pans?", "kiln_tender")
    blob = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "north pans" not in blob
    assert "second horn" not in blob


def test_general_plain_relevant_answer_beats_unrelated_hook():
    world = _brine_world()
    session = _session_for(world, "brine_yard", _brine_scene())
    res = _ask(world, session, "kiln_tender", "When is kiln three banked?")
    assert _topic_id(res) == "kiln_bank"
    assert res.get("clue_id") != CHIT_LEAD_ID
    assert CHIT_FACT not in (res.get("discovered_clues") or [])


def test_general_relevant_authorized_hook_still_fires():
    world = _brine_world()
    session = _session_for(world, "brine_yard", _brine_scene())
    res = _ask(world, session, "kiln_tender", "Where does the barge clerk hide the copper chit?")
    assert _topic_id(res) == "barge_chit"
    assert res.get("clue_id") == CHIT_LEAD_ID
    assert CHIT_FACT in (res.get("discovered_clues") or [])


def test_general_natural_paraphrase_keeps_relevant_topic():
    world = _brine_world()
    session = _session_for(world, "brine_yard", _brine_scene())
    res = _ask(world, session, "kiln_tender", "What hour do you bank that third kiln?")
    assert _topic_id(res) == "kiln_bank"
    assert "copper chit" not in _topic_text(res).lower()


def test_general_first_ask_without_warmup():
    world = _brine_world()
    session = _session_for(world, "brine_yard", _brine_scene())
    set_social_target(session, "kiln_tender")
    res = _ask(world, session, "kiln_tender", "When is kiln three banked?")
    assert _topic_id(res) == "kiln_bank"
    realized = _realize(world, session, "When is kiln three banked?", "kiln_tender")
    assert "morning bell" in str((realized or {}).get("fact_text") or (realized or {}).get("text") or "").lower()


def test_general_followup_context_does_not_hijack_with_unrelated_hook():
    world = _brine_world()
    session = _session_for(world, "brine_yard", _brine_scene())
    first = _ask(world, session, "kiln_tender", "When is kiln three banked?")
    assert _topic_id(first) == "kiln_bank"
    follow = _ask(world, session, "kiln_tender", "What do you mean?")
    assert _topic_id(follow) != "barge_chit"
    assert CHIT_FACT not in (follow.get("discovered_clues") or [])
    assert follow.get("clue_id") != CHIT_LEAD_ID


def test_general_explicit_subject_change_can_move_to_other_owned_topic():
    world = _brine_world()
    session = _session_for(world, "brine_yard", _brine_scene())
    first = _ask(world, session, "kiln_tender", "When is kiln three banked?")
    assert _topic_id(first) == "kiln_bank"
    second = _ask(world, session, "kiln_tender", "Where does the barge clerk hide the copper chit?")
    assert _topic_id(second) == "barge_chit"


def test_general_rejected_candidate_leaves_no_consequence():
    world = _brine_world()
    session = _session_for(world, "brine_yard", _brine_scene())
    res = _ask(world, session, "kiln_tender", "When is kiln three banked?")
    assert res.get("clue_id") != CHIT_LEAD_ID
    runtime = session.get("npc_runtime") or {}
    revealed = ((runtime.get("kiln_tender") or {}).get("revealed_topics") or [])
    assert "barge_chit" not in revealed
    assert "kiln_bank" in revealed


def test_general_answer_selection_does_not_create_knowledge():
    world = _brine_world()
    session = _session_for(world, "brine_yard", _brine_scene())
    before = [dict(row) for row in world["npcs"]]
    _ask(world, session, "kiln_tender", "When do the rakers scrape the north pans?")
    after_topics = world["npcs"][0].get("topics") or []
    assert [row.get("id") for row in after_topics] == [row.get("id") for row in (before[0].get("topics") or [])]
    realized = _realize(world, session, "When do the rakers scrape the north pans?", "kiln_tender")
    assert realized is None or SALT_FACT.lower() not in str(realized.get("fact_text") or "").lower()


def test_general_http_ask_a_not_b(tmp_path, monkeypatch):
    _seed_brine_http(tmp_path, monkeypatch)
    data = _chat(
        monkeypatch,
        'I turn to the Kiln Tender. "When is kiln three banked?"',
        'Kiln Tender mutters, "Word is, the barge clerk hides a copper chit under the weigh-stone."',
    )
    text = _facing(data).lower()
    assert "morning bell" in text or "kiln three" in text
    assert "copper chit" not in text
    assert CHIT_LEAD_ID not in _lead_ids(data.get("session") or {})
    assert inspect_interaction_context(data.get("session") or {}).get("active_interaction_target_id") == "kiln_tender"


def test_general_http_relevant_hook_still_lands(tmp_path, monkeypatch):
    _seed_brine_http(tmp_path, monkeypatch)
    data = _chat(
        monkeypatch,
        'I turn to the Kiln Tender. "Where does the barge clerk hide the copper chit?"',
        'Kiln Tender shakes their head. "I don\'t know."',
    )
    text = _facing(data).lower()
    assert "weigh-stone" in text or "copper chit" in text
    assert "i don't know" not in text
    assert CHIT_LEAD_ID in _lead_ids(data.get("session") or {})


def test_general_http_unauthorized_no_leak(tmp_path, monkeypatch):
    _seed_brine_http(tmp_path, monkeypatch)
    data = _chat(
        monkeypatch,
        'I turn to the Kiln Tender. "When do the rakers scrape the north pans?"',
        'Kiln Tender mutters, "Word is, rakers scrape the north pans after the second horn."',
    )
    text = _facing(data).lower()
    assert "second horn" not in text
    assert inspect_interaction_context(data.get("session") or {}).get("active_interaction_target_id") == "kiln_tender"


def test_general_http_first_ask(tmp_path, monkeypatch):
    _seed_brine_http(tmp_path, monkeypatch)
    data = _chat(
        monkeypatch,
        'I turn to the Kiln Tender. "When is kiln three banked?"',
        'Kiln Tender shakes their head. "I don\'t know."',
    )
    text = _facing(data).lower()
    assert "i don't know" not in text
    assert "morning bell" in text or "kiln three" in text


def test_generic_ask_without_subject_can_still_reveal_first_topic():
    world = _brine_world()
    session = _session_for(world, "brine_yard", _brine_scene())
    res = _ask(world, session, "kiln_tender", "Ask the Kiln Tender")
    assert _topic_id(res) == "kiln_bank"


def test_speaker_identity_tokens_do_not_make_unrelated_topic_relevant():
    npc = {
        "id": "kiln_tender",
        "name": "Kiln Tender",
        "aliases": ["fire warden"],
        "topics": [{"id": "barge_chit", "text": CHIT_FACT, "clue_id": CHIT_LEAD_ID}],
    }
    assert (
        authored_topic_relevant_to_question(
            "I step over to the kiln tender and ask what the kiln ash costs.",
            npc["topics"][0],
            npc=npc,
        )
        is False
    )
    subject = _question_subject_tokens(
        "I step over to the kiln tender and ask what the kiln ash costs.",
        {"kiln", "tender"},
    )
    assert "costs" in subject or "cost" in subject
    assert "tender" not in subject
    assert "kiln" not in subject


def test_calibration_stew_question_does_not_select_patrol_rumor():
    world = default_world()
    world["npcs"] = [
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "aliases": ["runner", "tavern runner"],
            "topics": [
                {
                    "id": "patrol_rumor",
                    "text": PATROL_RUMOR,
                    "clue_id": "muddy_footprints_northwest",
                }
            ],
        }
    ]
    scene = default_scene("frontier_gate")
    session = _session_for(world, "frontier_gate", scene)
    player = "I step over to the tavern runner and ask what the stew costs."
    res = resolve_social_action(
        scene,
        session,
        world,
        {
            "id": "question_stew",
            "label": player,
            "type": "question",
            "prompt": player,
            "target_id": "tavern_runner",
        },
        raw_player_text=player,
        character=default_character(),
        turn_counter=1,
    )
    assert _topic_id(res) != "patrol_rumor"
    assert res.get("clue_id") != "muddy_footprints_northwest"
    assert PATROL_RUMOR not in (res.get("discovered_clues") or [])
    realized = realize_authored_knowledge_answer(
        session=session,
        scene_id="frontier_gate",
        player_text=player,
        resolution=res,
        world=world,
        scene=scene,
    )
    blob = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "muddy footprints" not in blob
    assert "patrol vanished" not in blob


def test_calibration_related_stew_topic_answers_without_inventing_a_price():
    world = default_world()
    world["npcs"] = [
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "topics": [{"id": "stew", "text": STEW_RELATED}],
        }
    ]
    scene = default_scene("frontier_gate")
    session = _session_for(world, "frontier_gate", scene)
    cost_ask = "What does the stew cost?"
    cost_res = resolve_social_action(
        scene,
        session,
        world,
        {
            "id": "question_stew",
            "label": cost_ask,
            "type": "question",
            "prompt": cost_ask,
            "target_id": "tavern_runner",
        },
        raw_player_text=cost_ask,
        character=default_character(),
        turn_counter=1,
    )
    assert _topic_id(cost_res) != "stew"
    assert "copper" not in _topic_text(cost_res).lower()
    assert "silver" not in _topic_text(cost_res).lower()
    about_ask = "Tell me about the stew."
    about_res = resolve_social_action(
        scene,
        session,
        world,
        {
            "id": "question_stew_about",
            "label": about_ask,
            "type": "question",
            "prompt": about_ask,
            "target_id": "tavern_runner",
        },
        raw_player_text=about_ask,
        character=default_character(),
        turn_counter=2,
    )
    assert _topic_id(about_res) == "stew"
    assert "hot stew" in _topic_text(about_res).lower()
    assert "copper coins" not in _topic_text(about_res).lower()
    assert "silver" not in _topic_text(about_res).lower()


def test_calibration_relevant_patrol_question_still_fires_runner_hook():
    world = default_world()
    world["npcs"] = [
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "topics": [
                {
                    "id": "patrol_rumor",
                    "text": PATROL_RUMOR,
                    "clue_id": "muddy_footprints_northwest",
                }
            ],
        }
    ]
    scene = default_scene("frontier_gate")
    session = _session_for(world, "frontier_gate", scene)
    player = "I ask the tavern runner about the missing patrol."
    res = resolve_social_action(
        scene,
        session,
        world,
        {
            "id": "question_patrol",
            "label": player,
            "type": "question",
            "prompt": player,
            "target_id": "tavern_runner",
        },
        raw_player_text=player,
        character=default_character(),
        turn_counter=1,
    )
    assert _topic_id(res) == "patrol_rumor"
    assert res.get("clue_id") == "muddy_footprints_northwest"


def test_calibration_http_stew_question_does_not_mint_patrol_lead(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    scene = default_scene("frontier_gate")
    storage._save_json(storage.scene_path("frontier_gate"), scene)
    world = default_world()
    world["npcs"] = [
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "aliases": ["runner", "tavern runner"],
            "topics": [
                {
                    "id": "patrol_rumor",
                    "text": PATROL_RUMOR,
                    "clue_id": "muddy_footprints_northwest",
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
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    data = _chat(
        monkeypatch,
        "I step over to the tavern runner and ask what the stew costs.",
        'Tavern Runner shakes their head. "I don\'t know."',
    )
    text = _facing(data).lower()
    assert "muddy footprints" not in text
    assert "patrol vanished" not in text
    assert "copper coins" not in text
    leads = _lead_ids(data.get("session") or {})
    assert "muddy_footprints_northwest" not in leads
    assert "minlead_exit_frontier_gate_old_milestone" not in leads
    assert ((data.get("resolution") or {}).get("social") or {}).get("topic_revealed") in (None, {})


def test_anti_overfitting_generic_helpers_have_no_calibration_special_case():
    for fn in (
        authored_topic_relevant_to_question,
        _question_subject_tokens,
        _next_topic_to_reveal,
    ):
        src = inspect.getsource(fn)
        for term in CALIBRATION_ENGINE_TERMS:
            assert term not in src, f"{fn.__name__} contains calibration term {term!r}"
    social = Path("game/social.py").read_text(encoding="utf-8")
    start = social.find("def authored_topic_relevant_to_question")
    end = social.find("def npc_social_knowledge_exhausted")
    slice_src = social[start:end]
    for term in CALIBRATION_ENGINE_TERMS:
        assert term not in slice_src, f"relevance helpers contain calibration term {term!r}"


def test_ignorance_line_is_not_replaced_by_unrelated_owned_topic():
    world = _brine_world()
    session = _session_for(world, "brine_yard", _brine_scene())
    gm = apply_authored_knowledge_realization_to_gm(
        {"player_facing_text": 'Kiln Tender shakes their head. "I don\'t know."', "tags": []},
        player_text="How much does a sack of kiln ash cost?",
        resolution={
            "kind": "question",
            "social": {
                "npc_id": "kiln_tender",
                "npc_name": "Kiln Tender",
                "topic_revealed": None,
            },
        },
        session=session,
        world=world,
        scene=_brine_scene(),
        scene_id="brine_yard",
    )
    text = str(gm.get("player_facing_text") or "").lower()
    assert "copper chit" not in text
    assert "morning bell" not in text
