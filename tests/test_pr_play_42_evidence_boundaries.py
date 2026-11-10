"""PR-PLAY-42: structured public facts stay separate, and addressee gates follow the action.

The saved PR-PLAY-41 opening is replayed offline. Interpretation is stubbed from
captured records. Social and exploration resolvers are the production functions.
"""
from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from game import api, storage
from game.conversational_orchestration import (
    authored_travel_admission,
    decision_from_interpretation_record,
)
from game.defaults import default_campaign, default_character, default_combat, default_conditions, default_session
from game.incidental_entity import public_evidence_units
from game.ordinary_semantic_ownership import (
    _public_npc_candidates,
    _visible_npcs,
    assess_addressee_grounding,
)
from game.player_interpretation_bridge import normalized_action_from_interpretation
from game.storage import build_effective_scene
from tests.helpers.turn_pipeline_http_fixtures import _patch_storage

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts" / "atgb" / "pr_play_41" / "live" / "20261102T110016Z-47c71d381798"
POST_OPENING = RUN / "turns" / "T1" / "before" / "persistent"
RUMOR = "Have you heard any interesting rumors lately?"
NOTICE = "I examine the notice board."
PATROL = "I want to follow the trail connected to the missing patrol."
AVAILABLE = "What is available here?"
FOOTPRINTS = "I examine the footprints."
SUMMARY = "Go to Follow the missing patrol rumor."


def _unwrap(document):
    if isinstance(document, dict) and isinstance(document.get("payload"), dict):
        return document["payload"]
    return document


def _load_saved(folder: Path):
    scene = json.loads((folder / "scenes" / "frontier_gate.json").read_text(encoding="utf-8"))
    world = _unwrap(json.loads((folder / "world.json").read_text(encoding="utf-8")))
    session = _unwrap(json.loads((folder / "session.json").read_text(encoding="utf-8")))
    overlay = (session.get("runtime_scene_overlays") or {}).get("frontier_gate") or {}
    return build_effective_scene(scene, overlay), world, session


def _turn(step: str) -> dict:
    return json.loads((RUN / "turns" / step / "record.json").read_text(encoding="utf-8"))


def _captured(step: str) -> dict:
    return copy.deepcopy(_turn(step)["engine"]["live_interpretation"]["record"])


def _action(operation: str, target: str, text: str, *, recipient: str, purpose: str) -> dict:
    return {
        "communication_mode": "IN_WORLD_ACTION",
        "interpretation_status": "INTERPRETED",
        "player_intent": {"summary": text},
        "action_components": [{
            "order": 1,
            "description": text,
            "target_ref": target,
            "operation_class": operation,
        }],
        "references": {"permitted_entity_ids": [target] if target else [], "unresolved_references": []},
        "clarification_question": "",
        "communication": {"recipient": recipient, "purpose": purpose, "evidence_refs": []},
        "public_evidence": {},
    }


def _candidate_ids(text, scene, world):
    kind, chosen = _public_npc_candidates(text, _visible_npcs(scene, world), scene)
    return kind, sorted(str(row.get("id") or "") for row in chosen)


def test_saved_opening_facts_remain_separate_units():
    scene, _world, session = _load_saved(POST_OPENING)
    overlay = session["runtime_scene_overlays"]["frontier_gate"]["visible_facts_add"]
    assert len(overlay) == 7
    assert all(not str(fact).rstrip().endswith((".", "!", "?")) for fact in overlay)
    units = public_evidence_units(scene)
    for fact in overlay:
        assert fact in units
    joined = " ".join(overlay)
    assert joined not in units


def test_saved_opening_grounds_the_rumor_and_does_not_bind_the_notice_or_the_road():
    scene, world, session = _load_saved(POST_OPENING)
    rumor = assess_addressee_grounding(
        RUMOR, scene=scene, world=world, session=session, proposed_target_id="tavern_runner",
    )
    notice = decision_from_interpretation_record(
        _captured("T3"), player_text=NOTICE, scene=scene, world=world, session=session,
    )
    travel = authored_travel_admission(PATROL, scene=scene, world=world, session=session)
    road = assess_addressee_grounding(
        PATROL, scene=scene, world=world, session=session,
        proposed_target_id="leave_for_follow_the_missing_patrol_rumor",
    )
    assert rumor["operation_eligibility"] == "executable"
    assert rumor["target_id"] == "tavern_runner"
    assert notice.category.value == "EXECUTE"
    assert notice.proposed_operation == "INSPECT"
    assert notice.proposed_target == "notice_board"
    assert "which person" not in notice.player_facing_text.casefold()
    assert travel is not None and travel.category.value == "EXECUTE"
    assert travel.proposed_target == "leave_for_follow_the_missing_patrol_rumor"
    assert road["operation_eligibility"] != "requires_clarification"
    summary = assess_addressee_grounding(SUMMARY, scene=scene, world=world, session=session)
    assert summary["target_id"] == "tavern_runner"
    assert addressee_skipped_for_move(summary)


def addressee_skipped_for_move(summary_grounding):
    """The route summary can name the runner. That must not become the move."""
    from game.ordinary_semantic_ownership import addressee_authority_applies

    assert summary_grounding["operation_eligibility"] == "executable"
    return not addressee_authority_applies(operation="MOVE", player_text=PATROL)


def test_punctuation_order_and_duplicates_do_not_change_the_target():
    base = [
        "Mira the merchant sells spices from a blue stall",
        "Holt the blacksmith repairs weapons beside the forge",
    ]
    variants = [
        base,
        ["Mira the merchant sells spices from a blue stall.", base[1]],
        ["Mira the merchant sells spices from a blue stall!", base[1]],
        [base[1], base[0]],
        [base[0], base[0], base[1]],
        [base[1] + ".", base[0] + "."],
    ]
    outcomes = [_spice_target(facts) for facts in variants]
    assert outcomes == ["mira_merchant"] * len(variants)


def _people():
    return {
        "npcs": [
            {"id": "mira_merchant", "name": "Mira", "location": "salt_market", "aliases": ["merchant"], "description": ""},
            {"id": "holt_smith", "name": "Holt", "location": "salt_market", "aliases": ["blacksmith"], "description": ""},
            {"id": "sera_guard", "name": "Sera", "location": "salt_market", "aliases": ["guard"], "description": ""},
            {"id": "nell_page", "name": "Nell", "location": "salt_market", "aliases": ["servant"], "description": ""},
        ]
    }


def _market(facts):
    return {
        "scene": {
            "id": "salt_market",
            "location": "Salt Market",
            "summary": "Stalls crowd a muddy square.",
            "visible_facts": list(facts),
            "exits": [{"label": "North lane", "target_scene_id": "cooper_yard"}],
            "interactables": [{
                "id": "market_notice",
                "label": "Market notice",
                "aliases": ["notice", "posted notice"],
                "type": "investigate",
                "reveals_clue": "spice_tax",
            }],
            "discoverable_clues": [{"id": "spice_tax", "text": "The posted notice names a new spice tax."}],
        }
    }


def _spice_target(facts):
    scene, world = _market(facts), _people()
    grounding = assess_addressee_grounding(
        "What spices are for sale?", scene=scene, world=world, session={},
    )
    return grounding.get("target_id")


def test_marketplace_ask_inspect_travel_ambiguity_and_unknown():
    facts = [
        "Mira the merchant sells spices from a blue stall",
        "Holt the blacksmith repairs weapons beside the forge",
        "Sera the guard watches the square",
        "the market notice lists today's spice prices",
    ]
    scene, world = _market(facts), _people()
    before = copy.deepcopy(world)
    spices = assess_addressee_grounding("What spices are for sale?", scene=scene, world=world, session={})
    notice = decision_from_interpretation_record(
        _action("INSPECT", "market_notice", "I examine the market notice.", recipient="CHARACTER", purpose="ACTION"),
        player_text="I examine the market notice.", scene=scene, world=world, session={},
    )
    travel = authored_travel_admission("I take the north lane.", scene=scene, world=world, session={})
    ambiguous = assess_addressee_grounding(
        "Can you tell me what happened?", scene=scene, world=world, session={}, proposed_target_id="mira_merchant",
    )
    unknown = assess_addressee_grounding(
        "I ask Duke Halvern about the spices.", scene=scene, world=world, session={}, proposed_target_id="duke_halvern",
    )
    assert spices["target_id"] == "mira_merchant"
    assert spices["operation_eligibility"] == "executable"
    assert notice.category.value == "EXECUTE"
    assert notice.proposed_operation == "INSPECT"
    assert notice.proposed_target == "market_notice"
    assert travel is not None and travel.category.value == "EXECUTE"
    assert travel.proposed_target == "leave_for_north_lane"
    assert ambiguous["operation_eligibility"] == "requires_clarification"
    assert ambiguous["target_id"] is None
    assert unknown["operation_eligibility"] != "executable"
    assert all(npc["id"] != "duke_halvern" for npc in world["npcs"])
    assert world == before


def test_one_fact_can_name_two_people_without_absorbing_its_neighbors():
    scene = _market([
        "Bram the merchant argues with Lira the guard about missing supplies",
        "Odell the baker sells bread at the end of the row",
        "the posted slate lists bread prices",
    ])
    world = {
        "npcs": [
            {"id": "bram", "name": "Bram", "location": "salt_market", "aliases": ["merchant"], "description": ""},
            {"id": "lira", "name": "Lira", "location": "salt_market", "aliases": ["guard"], "description": ""},
            {"id": "odell", "name": "Odell", "location": "salt_market", "aliases": ["baker"], "description": ""},
        ]
    }
    shared = assess_addressee_grounding("What about the missing supplies?", scene=scene, world=world, session={})
    bread = assess_addressee_grounding("Who sells bread?", scene=scene, world=world, session={})
    slate = decision_from_interpretation_record(
        _action("INSPECT", "market_notice", "I examine the posted slate.", recipient="CHARACTER", purpose="ACTION"),
        player_text="I examine the posted slate.", scene=scene, world=world, session={},
    )
    assert shared["operation_eligibility"] == "requires_clarification"
    assert {choice["entity_id"] for choice in shared["choices"]} == {"bram", "lira"}
    assert bread["target_id"] == "odell"
    assert slate.category.value == "EXECUTE"
    assert slate.proposed_operation == "INSPECT"


def test_shared_object_words_do_not_turn_inspection_into_a_person_question():
    scene = _market([
        "Bram the merchant and Lira the guard argue beside the posted slate about missing supplies",
        "Odell the baker sells bread at the end of the row",
    ])
    world = {
        "npcs": [
            {"id": "bram", "name": "Bram", "location": "salt_market", "aliases": ["merchant"], "description": ""},
            {"id": "lira", "name": "Lira", "location": "salt_market", "aliases": ["guard"], "description": ""},
            {"id": "odell", "name": "Odell", "location": "salt_market", "aliases": ["baker"], "description": ""},
        ]
    }
    kind, ids = _candidate_ids("I examine the posted slate.", scene, world)
    decision = decision_from_interpretation_record(
        _action("INSPECT", "market_notice", "I examine the posted slate.", recipient="CHARACTER", purpose="ACTION"),
        player_text="I examine the posted slate.", scene=scene, world=world, session={},
    )
    assert kind == "ambiguous"
    assert set(ids) == {"bram", "lira"}
    assert decision.category.value == "EXECUTE"
    assert decision.proposed_operation == "INSPECT"
    assert decision.proposed_target == "market_notice"


def test_mixed_intent_keeps_speech_off_object_and_route_resolution():
    facts = [
        "Mira the merchant sells spices from a blue stall",
        "Sera the guard watches the square",
        "Nell the servant waits by the stall",
    ]
    scene, world = _market(facts), _people()
    ask = decision_from_interpretation_record(
        _action("INSPECT", "missing_wagon", "Ask the guard to inspect the wagon.", recipient="CHARACTER", purpose="ACTION"),
        player_text="Ask the guard to inspect the wagon.", scene=scene, world=world, session={},
    )
    tell = decision_from_interpretation_record(
        _action("MOVE", "leave_for_north_lane", "Tell the servant I'm leaving.", recipient="CHARACTER", purpose="ACTION"),
        player_text="Tell the servant I'm leaving.", scene=scene, world=world, session={},
    )
    follow = authored_travel_admission("Follow the merchant.", scene=scene, world=world, session={})
    wagon_record = _action("INSPECT", "missing_wagon", "Inspect the wagon.", recipient="CHARACTER", purpose="ACTION")
    missing = decision_from_interpretation_record(
        wagon_record, player_text="Inspect the wagon.", scene=scene, world=world, session={},
    )
    _action_out, wagon_meta = normalized_action_from_interpretation(
        missing.proposed_record or wagon_record,
        scene=scene, world=world, player_text="Inspect the wagon.", session={},
        known_scene_ids=lambda: ["salt_market", "cooper_yard"],
    )
    leave = authored_travel_admission("I leave through the north lane.", scene=scene, world=world, session={})
    assert ask.category.value == "EXECUTE"
    assert ask.proposed_operation == "ASK"
    assert ask.proposed_target == "sera_guard"
    assert tell.category.value == "EXECUTE"
    assert tell.proposed_operation == "ASK"
    assert tell.proposed_target == "nell_page"
    assert follow is None or follow.proposed_target != "leave_for_north_lane"
    assert wagon_meta.get("accepted") is not True
    assert _action_out is None
    assert "wagon" not in json.dumps(world)
    assert leave is not None and leave.category.value == "EXECUTE"
    assert leave.proposed_target == "leave_for_north_lane"


def _install_opening(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    dest = tmp_path / "data"
    shutil.rmtree(dest)
    shutil.copytree(POST_OPENING, dest)


def _quiet(monkeypatch, interpretations):
    calls = {"interpretation": [], "narration": [], "social": [], "exploration": []}

    def interpret(**kwargs):
        text = kwargs.get("player_text") or ""
        calls["interpretation"].append(text)
        for key, outcome in interpretations.items():
            if key in text:
                return outcome
        return {"status": "blocked", "reason": "stub_unmatched", "record": None, "provider_requests": []}

    def narrate(*_args, **_kwargs):
        calls["narration"].append(True)
        return {
            "player_facing_text": "Invented narration.",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": "moon_gate",
            "new_scene_draft": {"id": "moon_gate", "summary": "Invented."},
            "world_updates": {"npcs": [{"id": "invented_guide", "name": "Invented Guide"}]},
        }

    import game.exploration as exploration_mod
    import game.social as social_mod

    social = social_mod.resolve_social_action
    exploration = exploration_mod.resolve_exploration_action

    def social_spy(*args, **kwargs):
        calls["social"].append(True)
        return social(*args, **kwargs)

    def exploration_spy(*args, **kwargs):
        calls["exploration"].append(True)
        return exploration(*args, **kwargs)

    monkeypatch.setenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    monkeypatch.setattr(api, "interpret_production_turn", interpret)
    monkeypatch.setattr(api, "call_gpt", narrate)
    monkeypatch.setattr(social_mod, "resolve_social_action", social_spy)
    monkeypatch.setattr(exploration_mod, "resolve_exploration_action", exploration_spy)
    return calls


def _post(client, text):
    response = client.post("/api/chat?ui_mode=player", json={"text": text})
    assert response.status_code == 200, response.text
    return response.json()


def _facing(body) -> str:
    return str((body.get("gm_output") or {}).get("player_facing_text") or "")


def _ids(world):
    return sorted(str(npc.get("id") or "") for npc in world.get("npcs") or [] if isinstance(npc, dict))


def test_rumor_reaches_the_social_resolver_on_the_saved_opening(tmp_path, monkeypatch):
    _install_opening(tmp_path, monkeypatch)
    calls = _quiet(monkeypatch, {RUMOR: {"status": "accepted", "record": _captured("T2"), "provider_requests": []}})
    before = storage.load_session()
    npc_ids = _ids(storage.load_world())
    with TestClient(api.app) as client:
        body = _post(client, RUMOR)
    after = storage.load_session()
    text = _facing(body)
    assert calls["social"] == [True]
    assert calls["exploration"] == []
    assert "which person" not in text.casefold()
    assert "patrol" in text.casefold() or "footprint" in text.casefold()
    assert after["active_scene_id"] == "frontier_gate"
    assert after["turn_counter"] == before["turn_counter"] + 1
    log = storage.load_log()[-1]
    assert log["resolution"]["social"]["npc_id"] == "tavern_runner"
    assert log["resolution"]["social"]["topic_revealed"]["id"] == "patrol_rumor"
    assert _ids(storage.load_world()) == npc_ids


def test_notice_board_reaches_the_exploration_resolver_on_the_saved_opening(tmp_path, monkeypatch):
    _install_opening(tmp_path, monkeypatch)
    calls = _quiet(monkeypatch, {NOTICE: {"status": "accepted", "record": _captured("T3"), "provider_requests": []}})
    before = storage.load_session()
    with TestClient(api.app) as client:
        body = _post(client, NOTICE)
    after = storage.load_session()
    text = _facing(body)
    assert calls["exploration"] == [True]
    assert calls["social"] == []
    assert "which person" not in text.casefold()
    assert after["active_scene_id"] == "frontier_gate"
    assert after["turn_counter"] == before["turn_counter"] + 1
    log = storage.load_log()[-1]
    resolution = log["resolution"]
    assert resolution.get("action_id") == "notice_board" or "notice" in json.dumps(resolution).casefold()
    blob = json.dumps(resolution)
    if resolution.get("success") is True:
        assert "notice_patrol_route" in blob
    assert "invented_guide" not in json.dumps(storage.load_world())


def test_patrol_travel_reaches_old_milestone_on_the_saved_opening(tmp_path, monkeypatch):
    _install_opening(tmp_path, monkeypatch)
    calls = _quiet(monkeypatch, {})
    before = storage.load_session()
    with TestClient(api.app) as client:
        body = _post(client, PATROL)
    after = storage.load_session()
    text = _facing(body)
    assert calls["interpretation"] == []
    assert calls["exploration"] == [True]
    assert calls["social"] == []
    assert "which person" not in text.casefold()
    assert after["active_scene_id"] == "old_milestone"
    assert "old_milestone" in after["visited_scene_ids"]
    assert after["clocks"]["time_pressure"] == before["clocks"]["time_pressure"] + 1
    assert after["turn_counter"] == before["turn_counter"] + 1
    assert body["resolution"] == {}
    assert storage.load_log()[-1]["resolution"]["resolved_transition"] is True
    assert storage.load_log()[-1]["resolution"]["target_scene_id"] == "old_milestone"
    assert storage.load_log()[-1]["player_input"] == PATROL
    assert "moon_gate" not in json.dumps(storage.load_world())


def test_five_turn_sequence_on_the_saved_opening(tmp_path, monkeypatch):
    _install_opening(tmp_path, monkeypatch)
    calls = _quiet(monkeypatch, {
        AVAILABLE: {"status": "accepted", "record": _captured("T1"), "provider_requests": []},
        RUMOR: {"status": "accepted", "record": _captured("T2"), "provider_requests": []},
        NOTICE: {"status": "accepted", "record": _captured("T3"), "provider_requests": []},
        FOOTPRINTS: {
            "status": "accepted",
            "record": _action("INSPECT", "prints", FOOTPRINTS, recipient="CHARACTER", purpose="ACTION"),
            "provider_requests": [],
        },
    })
    start = storage.load_session()
    npc_ids = _ids(storage.load_world())
    with TestClient(api.app) as client:
        briefing = _post(client, AVAILABLE)
        rumor = _post(client, RUMOR)
        notice = _post(client, NOTICE)
        travel = _post(client, PATROL)
        assert storage.load_session()["active_scene_id"] == "old_milestone"
        prints = _post(client, FOOTPRINTS)
    final = storage.load_session()
    for body in (rumor, notice, travel, prints):
        assert "which person" not in _facing(body).casefold()
    assert "notice" in _facing(briefing).casefold() or "cinderwatch" in _facing(briefing).casefold()
    assert calls["social"] == [True]
    assert calls["exploration"] == [True, True, True]
    assert final["active_scene_id"] == "old_milestone"
    assert final["visited_scene_ids"][:2] == ["frontier_gate", "old_milestone"] or "old_milestone" in final["visited_scene_ids"]
    assert final["turn_counter"] == start["turn_counter"] + 4
    assert final["clocks"]["time_pressure"] == start["clocks"]["time_pressure"] + 4
    assert _ids(storage.load_world()) == npc_ids
    rumor_log = next(row for row in storage.load_log() if row.get("player_input") == RUMOR)
    assert rumor_log["resolution"]["social"]["topic_revealed"]["id"] == "patrol_rumor"
    assert travel["resolution"] == {}
    travel_log = next(row for row in storage.load_log() if row.get("player_input") == PATROL)
    assert travel_log["resolution"]["target_scene_id"] == "old_milestone"
    print_log = storage.load_log()[-1]
    assert print_log["player_input"] == FOOTPRINTS
    assert print_log["resolution"].get("action_id") in {"prints", "notice_board"} or "print" in json.dumps(print_log["resolution"]).casefold()
    assert "invented_guide" not in json.dumps(storage.load_world())


def test_marketplace_actions_resolve_without_inventing_people(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    facts = [
        "Mira the merchant sells spices and trades rumors from a blue stall",
        "Holt the blacksmith repairs weapons beside the forge",
        "Sera the guard watches the square",
        "the market notice lists today's spice prices",
    ]
    scene = _market(facts)
    for sid, location in (("frontier_gate", "Gate"), ("market_quarter", "Market Quarter")):
        storage._save_json(storage.scene_path(sid), {
            "scene": {
                "id": sid,
                "location": location,
                "summary": "Unused in this isolated scene.",
                "visible_facts": [],
                "exits": [],
                "interactables": [],
            },
        })
    storage._save_json(storage.scene_path("salt_market"), scene)
    storage._save_json(storage.scene_path("cooper_yard"), {
        "scene": {
            "id": "cooper_yard",
            "location": "Cooper Yard",
            "summary": "A quiet cooper's yard.",
            "visible_facts": [],
            "exits": [],
            "interactables": [],
        },
    })
    world = _people()
    world["world_state"] = {"flags": {}, "counters": {}, "clocks": {}}
    world["npcs"][0]["topics"] = [{
        "id": "spice_prices",
        "discovery_categories": ["rumor"],
        "text": "Mira heard the pepper costs two silver this week.",
    }]
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = "salt_market"
    session["visited_scene_ids"] = ["salt_market"]
    session["campaign_started"] = True
    session["turn_counter"] = 1
    storage.save_session(session)
    ask = "Have you heard any interesting rumors lately?"
    inspect = "I examine the market notice."
    travel = "I take the north lane."
    calls = _quiet(monkeypatch, {
        ask: {"status": "accepted", "record": _action("ASK", "mira_merchant", ask, recipient="NPC", purpose="QUESTION"), "provider_requests": []},
        inspect: {"status": "accepted", "record": _action("INSPECT", "market_notice", inspect, recipient="CHARACTER", purpose="ACTION"), "provider_requests": []},
    })
    with TestClient(api.app) as client:
        asked = _post(client, ask)
        inspected = _post(client, inspect)
        moved = _post(client, travel)
    assert calls["social"] == [True]
    assert calls["exploration"] == [True, True]
    assert "which person" not in _facing(inspected).casefold()
    assert "which person" not in _facing(moved).casefold()
    assert storage.load_session()["active_scene_id"] == "cooper_yard"
    assert "which person" not in _facing(asked).casefold()
    asked_log = next(row for row in storage.load_log() if row.get("player_input") == ask)
    assert asked_log["resolution"]["social"]["npc_id"] == "mira_merchant"
    assert asked_log["resolution"]["social"]["topic_revealed"]["id"] == "spice_prices"
    assert "pepper" in _facing(asked).casefold()
    assert all(npc.get("id") != "duke_halvern" for npc in storage.load_world().get("npcs") or [])
