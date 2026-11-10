"""PR-PLAY-76 physical adjudication. Deferred take/drop/inventory are refusals, not passes."""
import copy
import json

import pytest
from fastapi.testclient import TestClient

from game import api, storage
from game.authored_consequences import ENROLLMENT, GATE as BRANCH, NEW_CAMPAIGNS
from game.bounded_improvisation import LEDGER_KEY, WORLD_FACT_GATE, controlled_request
from game.physical_adjudication import (
    commit_physical, interpret_with_provider, plan_physical, validate_provider_interpretation,
)
from game.player_initiative import GATE as INITIATIVE
from tests.test_pr_play_71_lifecycle import choose, configure, create, reach, safe, start

PHYSICAL = "ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION"


def world():
    return {"npcs": [], "world_state": {"flags": {"patrol_survey": True}}}


def stage(scene_id="yard", fact="A weathered stone marker stands in the yard."):
    session = {"campaign_run_id": "alpha", "active_scene_id": scene_id, "turn_counter": 3,
               ENROLLMENT: "alpha", LEDGER_KEY: {"entries": [], "physical_consequences": [], "physical_state": {}}}
    scene = {"scene": {"id": scene_id, "visible_facts": [fact], "interactables": [], "hidden_facts": ["SENTINEL_HIDDEN_FACT"]}}
    return session, scene, world()


def enable(monkeypatch):
    monkeypatch.setenv(PHYSICAL, "1")
    monkeypatch.setenv(WORLD_FACT_GATE, "1")
    monkeypatch.setenv(INITIATIVE, "1")
    monkeypatch.setenv(BRANCH, "1")
    monkeypatch.setenv(NEW_CAMPAIGNS, "1")


def add(session, *, ident, label, aliases=(), scene_id="yard", **props):
    entry = {"id": ident, "campaign_id": session["campaign_run_id"], "scene_id": scene_id, "family": "object",
             "entity_type": "object", "label": label, "aliases": list(aliases), "content": label,
             "properties": props, "visibility": "public", "status": "accepted", "authority": "controlled_world_fact",
             "scope": "scene"}
    session[LEDGER_KEY]["entries"].append(entry)
    return entry


def act(text, session, scene, packed=None, character=None):
    packed = packed if packed is not None else world()
    before = copy.deepcopy((session, scene, packed))
    plan = plan_physical(text, session=session, scene=scene, world=packed)
    result = None
    if plan and plan["mode"] == "interact":
        result = commit_physical(scene, session, packed, {"id": plan["id"], "target_id": plan["id"]},
                                 prompt=text, action_id=plan["id"], label="physical", character=character or {})
    return plan, result, before


def said(plan, result):
    if result:
        return result["metadata"]["engine_publication"]
    return plan["message"] if plan else ""


def door(**extra):
    props = {"openable": True, "locked": False, "open": False, "accessible": True, "visible": True}
    props.update(extra)
    return props


@pytest.fixture
def ready(monkeypatch):
    enable(monkeypatch)
    return stage()


def test_flag_off_does_not_adjudicate(monkeypatch):
    session, scene, packed = stage()
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    before = copy.deepcopy(session)
    assert plan_physical("I open the door.", session=session, scene=scene, world=packed) is None
    assert session == before


@pytest.mark.parametrize("text,category,operation", [
    ("I sit on the bench.", "A", "sit"),
    ("I stand up.", "A", "stand"),
    ("I open the door.", "A", "open"),
    ("I close the door.", "A", "close"),
    ("I push the crate aside.", "A", "move"),
    ("I lift the crate.", "A", "lift"),
    ("I approach the bench.", "A", "approach"),
])
def test_routine_classification(ready, text, category, operation):
    session, scene, packed = ready
    add(session, ident="bench", label="wooden bench", aliases=["bench", "seat"], use="seat")
    add(session, ident="door", label="wooden door", aliases=["door"], **door(open=True if "close" in text else False))
    add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light", position="by the wall")
    plan, result, _ = act(text, session, scene, packed)
    assert plan["category"] == category and plan["operation"] in {operation, "push", "move"}
    assert result["success"] is True
    assert result["metadata"]["physical_adjudication"]["invented_dc"] is False


@pytest.mark.parametrize("text,category", [
    ("I lift the boulder.", "B"),
    ("I climb the pillar.", "D"),
    ("I break the door.", "C"),
    ("I push the pillar.", "E"),
    ("I open the hatch.", "E"),
    ("I push it.", "F"),
])
def test_nonroutine_classification(ready, text, category):
    session, scene, packed = ready
    add(session, ident="boulder", label="boulder", aliases=["boulder"], mobility="movable", weight="heavy")
    add(session, ident="pillar", label="stone pillar", aliases=["pillar"], mobility="immovable", weight="immovable")
    add(session, ident="door", label="guarded door", aliases=["door"], **door(consequential=True))
    add(session, ident="a", label="left crate", aliases=["crate"], mobility="movable", weight="light")
    add(session, ident="b", label="right crate", aliases=["crate"], mobility="movable", weight="light")
    plan, result, before = act(text, session, scene, packed)
    assert plan["category"] == category
    assert result is None
    assert session[LEDGER_KEY]["physical_consequences"] == before[0][LEDGER_KEY]["physical_consequences"]


@pytest.mark.parametrize("props,text,fragment", [
    ({"accessible": False, "use": "seat"}, "I sit on the bench.", "not accessible"),
    ({"visible": False, "use": "seat"}, "I sit on the bench.", "not accessible"),
    ({"mobility": "immovable"}, "I push the crate.", "cannot be moved"),
    ({"openable": True}, "I open the door.", "not established"),
    ({"openable": True, "locked": True, "open": False}, "I open the door.", "locked"),
    ({"openable": True, "locked": False, "open": False, "obstructed": True}, "I open the door.", "obstructed"),
    ({"consequential": True, "openable": True, "locked": False, "open": False}, "I open the door.", "important state"),
    ({"ownership": "guarded", "mobility": "movable", "weight": "light"}, "I push the crate aside.", "important state"),
    ({"portable": True, "mobility": "movable", "weight": "light"}, "I pick up the cup.", "inventory"),
])
def test_property_gates(ready, props, text, fragment):
    session, scene, packed = ready
    label = "wooden bench" if "sit" in text else "oak crate" if "crate" in text or "cup" in text else "wooden door"
    aliases = ["bench", "seat"] if "sit" in text else ["crate", "cup"] if "crate" in text or "cup" in text else ["door"]
    add(session, ident="obj", label=label, aliases=aliases, **props)
    before = copy.deepcopy(session)
    plan, result, _ = act(text, session, scene, packed)
    assert fragment in said(plan, result).casefold()
    assert result is None
    assert session[LEDGER_KEY]["entries"] == before[LEDGER_KEY]["entries"]


def test_names_do_not_imply_properties(ready):
    session, scene, packed = ready
    add(session, ident="crate", label="crate", aliases=["crate"])
    add(session, ident="door", label="door", aliases=["door"])
    add(session, ident="stone", label="stone", aliases=["stone"])
    for text in ("I push the crate aside.", "I open the door.", "I lift the stone."):
        plan, result, _ = act(text, session, scene, packed)
        assert plan["category"] == "D" and result is None
        assert "not established" in said(plan, result) or "whether" in said(plan, result).casefold()


def test_sit_stand_and_any_suitable_seat(ready):
    session, scene, packed = ready
    add(session, ident="bench", label="wooden bench", aliases=["bench", "seat"], use="seat")
    plan, result, _ = act("Please take a seat on the bench.", session, scene, packed)
    assert "You sit on the wooden bench." in said(plan, result)
    assert session[LEDGER_KEY]["posture"]["kind"] == "sitting"
    plan, result, _ = act("I sit on the bench.", session, scene, packed)
    assert len(session[LEDGER_KEY]["physical_consequences"]) == 1
    plan, result, _ = act("I stand up.", session, scene, packed)
    assert session[LEDGER_KEY]["posture"]["kind"] == "standing"
    assert "standing" in {item["result"]["posture"] for item in session[LEDGER_KEY]["physical_consequences"]}


def test_stone_seat_wording_is_not_required(ready):
    session, scene, packed = ready
    add(session, ident="stool", label="low stool", aliases=["stool"], use="seat", material="wood")
    plan, result, _ = act("I rest on the stool.", session, scene, packed)
    assert result["success"] and "stool" in said(plan, result)
    assert "stone seat" not in said(plan, result)


def test_open_close_persists_and_answers_from_state(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    act("I open the door.", session, scene, packed)
    plan, result, _ = act("Is the door still open?", session, scene, packed)
    assert result is None and "is open" in said(plan, None)
    act("I close it.", session, scene, packed)
    assert session[LEDGER_KEY]["entries"][0]["properties"]["open"] is False
    plan, _, _ = act("Is the door open?", session, scene, packed)
    assert "closed" in said(plan, None)
    before = copy.deepcopy(session[LEDGER_KEY]["entries"][0]["properties"])
    act("Is the door open?", session, scene, packed)
    assert session[LEDGER_KEY]["entries"][0]["properties"] == before


def test_move_clears_only_established_obstruction(ready):
    session, scene, packed = ready
    add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light",
        position="blocking the doorway", obstructs="doorway")
    plan, _, _ = act("Is the doorway clear?", session, scene, packed)
    assert "not clear" in said(plan, None)
    act("I push the crate away from the doorway.", session, scene, packed)
    assert session[LEDGER_KEY]["entries"][0]["properties"]["position"] == "aside from the doorway"
    assert "obstructs" not in session[LEDGER_KEY]["entries"][0]["properties"]
    plan, _, _ = act("Is the doorway clear?", session, scene, packed)
    assert said(plan, None) == "The doorway is clear."
    add(session, ident="box", label="pine box", aliases=["box"], mobility="movable", weight="light", position="by the wall")
    before = copy.deepcopy(session)
    plan, result, _ = act("I push the box away from the doorway.", session, scene, packed)
    assert result is None and "No doorway" in said(plan, None)
    assert session[LEDGER_KEY]["entries"][1]["properties"]["position"] == "by the wall"


def test_farther_and_pronoun_keep_identity(ready):
    session, scene, packed = ready
    add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light", position="by the wall")
    act("I shove the crate aside.", session, scene, packed)
    ident = session[LEDGER_KEY]["entries"][0]["id"]
    act("Push it farther.", session, scene, packed)
    assert session[LEDGER_KEY]["entries"][0]["id"] == ident
    assert session[LEDGER_KEY]["entries"][0]["properties"]["position"].startswith("farther")
    act("Push it farther.", session, scene, packed)
    assert sum(item["action"] == "push" for item in session[LEDGER_KEY]["physical_consequences"]) == 2


def test_invalid_destination_and_barrier(ready):
    session, scene, packed = ready
    add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light", position="by the wall")
    before = copy.deepcopy(session[LEDGER_KEY]["entries"][0]["properties"])
    plan, result, _ = act("I push the crate through the wall.", session, scene, packed)
    assert result is None and session[LEDGER_KEY]["entries"][0]["properties"] == before
    plan, result, _ = act("I teleport through the wall.", session, scene, packed)
    assert plan["category"] == "E" and result is None


def test_heavy_missing_mechanic_does_not_invent_dc(ready):
    session, scene, packed = ready
    add(session, ident="boulder", label="boulder", aliases=["boulder"], mobility="movable", weight="heavy")
    plan, result, _ = act("I lift the boulder.", session, scene, packed)
    assert plan["category"] == "B" and plan["mechanic"] == "strength" and result is None
    assert "no strength check" in said(plan, None).casefold()
    assert "dc" not in said(plan, None).casefold()


def test_configured_check_failure_and_success(ready):
    session, scene, packed = ready
    add(session, ident="stuck", label="stuck door", aliases=["door"], **door(), skill_check={"skill_id": "athletics", "dc": 30})
    plan, result, _ = act("I open the door.", session, scene, packed)
    assert result["success"] is False and result["skill_check"]["difficulty"] == 30
    assert session[LEDGER_KEY]["entries"][0]["properties"]["open"] is False
    add(session, ident="easy", label="loose shutter", aliases=["shutter"], **door(), skill_check={"skill_id": "athletics", "dc": 1})
    plan, result, _ = act("I open the shutter.", session, scene, packed)
    assert result["success"] is True and result["skill_check"]["difficulty"] == 1
    assert session[LEDGER_KEY]["entries"][1]["properties"]["open"] is True


def test_climb_without_dc_and_with_authored_dc(ready):
    session, scene, packed = ready
    scene["scene"]["interactables"].append({"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]})
    plan, result, _ = act("I climb the weathered milestone to get a better view.", session, scene, packed)
    assert "no climbing check is configured" in said(plan, result)
    assert session.get("scene_state") is None and result is None
    add(session, ident="wall", label="practice wall", aliases=["wall"], skill_check={"skill_id": "climb", "dc": 1})
    plan, result, _ = act("I climb the practice wall.", session, scene, packed)
    assert result["success"] and result["skill_check"]["difficulty"] == 1
    assert session[LEDGER_KEY]["position"]["kind"] == "elevated"
    assert "No additional view" in said(plan, result)


def test_take_drop_place_are_deferred(ready):
    session, scene, packed = ready
    character = {"inventory": [{"id": "spellbook", "name": "Spellbook"}]}
    add(session, ident="cup", label="wooden cup", aliases=["cup"], portable=True, mobility="movable", weight="light")
    before = copy.deepcopy(character)
    for text in ("I pick up the cup.", "I drop the cup.", "I place the cup on the ground."):
        plan, result, _ = act(text, session, scene, packed, character)
        assert plan["deferred"] is True and result is None
    assert character == before


def test_lift_then_place_is_not_inventory(ready):
    session, scene, packed = ready
    character = {"inventory": [{"id": "spellbook"}]}
    add(session, ident="cup", label="wooden cup", aliases=["cup"], mobility="movable", weight="light", position="on the table")
    act("I lift the cup.", session, scene, packed, character)
    assert session[LEDGER_KEY]["entries"][0]["properties"]["position"] == "raised in place"
    act("I place the cup aside.", session, scene, packed, character)
    assert session[LEDGER_KEY]["entries"][0]["properties"]["position"] == "aside from where it was"
    assert character["inventory"] == [{"id": "spellbook"}]


@pytest.mark.parametrize("text", [
    "Is the door open?", "Can I move the crate?", "Is there a seat here?", "Am I sitting?",
])
def test_questions_do_not_mutate(ready, text):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light")
    add(session, ident="bench", label="wooden bench", aliases=["bench", "seat"], use="seat", content="A bench is here.")
    session[LEDGER_KEY]["entries"][-1]["content"] = "A bench is here."
    before = copy.deepcopy(session)
    plan, result, _ = act(text, session, scene, packed)
    assert result is None and session == before


def test_compound_open_then_look_and_partial_stop(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    add(session, ident="bench", label="wooden bench", aliases=["bench"], use="seat")
    plan, result, _ = act("I open the door and look inside.", session, scene, packed)
    assert session[LEDGER_KEY]["entries"][0]["properties"]["open"] is True
    assert "No room" in said(plan, result) or "Nothing concealed" in said(plan, result)
    before = copy.deepcopy(session[LEDGER_KEY].get("posture"))
    plan, result, _ = act("I open the hatch and sit on the bench.", session, scene, packed)
    assert result is None and session[LEDGER_KEY].get("posture") == before
    assert "not attempted" in said(plan, None).casefold()


def test_compound_move_then_doorway(ready):
    session, scene, packed = ready
    add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light",
        position="blocking the doorway", obstructs="doorway")
    plan, result, _ = act("I push the crate away from the doorway and check the doorway.", session, scene, packed)
    assert "aside from the doorway" in said(plan, result)
    assert "clear" in said(plan, result)


def test_hidden_target_is_not_revealed(ready):
    session, scene, packed = ready
    scene["scene"]["interactables"].append({"id": "cache", "label": "hidden chest", "hidden": True,
                                            "aliases": ["chest"], "affordances": {"openable": True, "locked": False, "open": False}})
    plan, result, _ = act("I open the hidden chest.", session, scene, packed)
    assert "SENTINEL" not in said(plan, result)
    assert result is None and "not established" in said(plan, result).casefold()


def test_ambiguous_and_unknown(ready):
    session, scene, packed = ready
    add(session, ident="a", label="oak crate", aliases=["crate"], mobility="movable", weight="light")
    add(session, ident="b", label="pine crate", aliases=["crate"], mobility="movable", weight="light")
    before = copy.deepcopy(session)
    plan, result, _ = act("Push the crate.", session, scene, packed)
    assert plan["mode"] == "clarify" and result is None and session == before
    plan, result, _ = act("I open the cellar door.", session, scene, packed)
    assert plan["category"] == "E" and result is None


def test_cross_scene_and_campaign(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], scene_id="other", **door())
    plan, result, _ = act("I open the door.", session, scene, packed)
    assert result is None
    add(session, ident="here", label="wooden door", aliases=["door"], **door())
    session["campaign_run_id"] = "beta"
    session[ENROLLMENT] = "beta"
    plan, result, _ = act("I open the door.", session, scene, packed)
    assert result is None


def test_save_resume_roundtrip(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    act("I open the door.", session, scene, packed)
    act("I sit on the bench.", session, scene, packed) if False else None
    add(session, ident="bench", label="wooden bench", aliases=["bench"], use="seat")
    act("I sit on the bench.", session, scene, packed)
    storage.save_session(session)
    restored = storage.load_session()
    assert restored[LEDGER_KEY]["entries"][0]["properties"]["open"] is True
    assert restored[LEDGER_KEY]["posture"]["kind"] == "sitting"
    plan, _, _ = act("Is the door still open?", restored, scene, packed)
    assert "open" in said(plan, None)
    act("I close the door.", restored, scene, packed)
    assert restored[LEDGER_KEY]["entries"][0]["properties"]["open"] is False


def test_provider_validation_does_not_commit(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    before = copy.deepcopy(session)
    assert validate_provider_interpretation({"operation": "open", "success": True}, session=session, scene=scene, world=packed)["reason"] == "invented_outcome_or_hidden_field"
    assert validate_provider_interpretation({"operation": "open", "target_ref": "invented"}, session=session, scene=scene, world=packed)["reason"] == "invented_target"
    assert validate_provider_interpretation({"operation": "open", "target_ref": "SENTINEL_HIDDEN"}, session=session, scene=scene, world=packed)["accepted"] is False
    calls = []
    outcome = interpret_with_provider("I wiggle the fitting.", session=session, scene=scene, world=packed, invoke=lambda text: calls.append(text) or {"operation": "open", "target_ref": "door"})
    assert outcome["committed"] is False and session == before
    assert interpret_with_provider("I open the door.", session=session, scene=scene, world=packed, invoke=lambda text: (_ for _ in ()).throw(TimeoutError()))["reason"]
    timeout = interpret_with_provider("Which one?", session=session, scene=scene, world=packed, invoke=lambda text: (_ for _ in ()).throw(TimeoutError()))
    assert timeout["accepted"] is False and timeout["retries"] == 0 and session == before


def test_provider_ambiguous_candidate_and_disagreement(ready):
    session, scene, packed = ready
    add(session, ident="a", label="oak crate", aliases=["crate"], mobility="movable", weight="light")
    add(session, ident="b", label="pine crate", aliases=["crate"], mobility="movable", weight="light")
    before = copy.deepcopy(session)
    accepted = interpret_with_provider("Push the crate.", session=session, scene=scene, world=packed,
                                      invoke=lambda text: {"operation": "push", "target_ref": "a"})
    rejected = interpret_with_provider("Push the crate.", session=session, scene=scene, world=packed,
                                      invoke=lambda text: {"operation": "open", "target_ref": "a"})
    malformed = interpret_with_provider("Push the crate.", session=session, scene=scene, world=packed, invoke=lambda text: None)
    assert accepted["accepted"] and rejected["accepted"] is False and malformed["accepted"] is False
    assert session == before


def test_loose_stone_requires_support_and_does_not_move(ready):
    session, scene, packed = ready
    scene["scene"]["visible_facts"] = ["A painted picture of a stone hangs here."]
    plan, result, _ = act("Is there a small loose stone I could shift aside?", session, scene, packed)
    assert result is None and "Nothing has been added" in said(plan, None)
    scene["scene"]["visible_facts"] = ["A weathered stone marker stands in the yard."]
    plan, result, _ = act("Is there a small loose stone I could shift aside?", session, scene, packed)
    assert result["success"] and "has not been moved" in said(plan, result)
    assert session[LEDGER_KEY]["entries"][0]["properties"]["mobility"] == "movable"
    plan, result, _ = act("Is there a small loose stone I could shift aside?", session, scene, packed)
    assert result is None and len(session[LEDGER_KEY]["entries"]) == 1


def test_authored_notice_is_not_opened_by_name(ready):
    session, scene, packed = ready
    scene["scene"]["interactables"].append({"id": "notice_board", "label": "Notice board", "aliases": ["notice board", "board"]})
    plan, result, _ = act("I open the notice board.", session, scene, packed)
    assert result is None and "not established as something you can open" in said(plan, None)
    plan, result, _ = act("I approach the notice board.", session, scene, packed)
    assert result["success"] and session[LEDGER_KEY]["position"]["target_id"] == "notice_board"


def test_consequence_fields_and_no_duplicate(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    act("I open the door.", session, scene, packed)
    item = session[LEDGER_KEY]["physical_consequences"][0]
    assert {"id", "target_id", "action", "prior", "result", "campaign_id", "scene_id", "turn", "provenance"} <= set(item)
    assert item["provenance"] == "physical_adjudication" and item["target_id"] == "door"
    act("The door is already open, I open the door.", session, scene, packed)
    assert len(session[LEDGER_KEY]["physical_consequences"]) == 1


def test_read_only_possibility(ready):
    session, scene, packed = ready
    add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light")
    before = copy.deepcopy(session)
    plan, result, _ = act("Can I move the crate?", session, scene, packed)
    assert result is None and "Nothing has been moved" in said(plan, None) and session == before


def test_existing_seat_path_without_physical_flag(monkeypatch):
    session, scene, packed = stage()
    monkeypatch.setenv(WORLD_FACT_GATE, "1")
    monkeypatch.setenv(INITIATIVE, "1")
    monkeypatch.setenv(BRANCH, "1")
    monkeypatch.setenv(NEW_CAMPAIGNS, "1")
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    add(session, ident="seat", label="ordinary stone seat", aliases=["seat"], use="seat", material="stone")
    plan = controlled_request("I sit on the stone seat.", session=session, scene=scene, world=packed)
    assert plan["routine"] == "sit" and plan.get("physical") is not True


@pytest.mark.parametrize("branch", ["survey", "report"])
def test_http_campaign_actions(tmp_path, monkeypatch, branch):
    configure(tmp_path, monkeypatch)
    enable(monkeypatch)
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_BRANCHING_SESSION", raising=False)
    with TestClient(api.app) as client:
        create(client)
        start(client)
        reach(client)
        choose(client, branch)
        if branch == "survey":
            out = safe(client.post("/api/chat", json={"text": "Is there a small loose stone I could shift aside?"}))
            assert "has not been moved" in out["gm_output"]["player_facing_text"]
            out = safe(client.post("/api/chat", json={"text": "I push the loose stone aside."}))
            assert "aside from the stonework" in out["gm_output"]["player_facing_text"]
            out = safe(client.post("/api/chat", json={"text": "Is the loose stone still beside the stonework?"}))
            assert "aside from the stonework" in out["gm_output"]["player_facing_text"]
            assert "SENTINEL" not in json.dumps(out)
            flags = storage.load_world()["world_state"]["flags"]
            out = safe(client.post("/api/chat", json={"text": "I push it farther."}))
            assert storage.load_world()["world_state"]["flags"] == flags
            snap = safe(client.post("/api/snapshots", json={"label": "stone"}))["snapshot"]["id"]
            create(client)
            assert storage.load_session().get(LEDGER_KEY, {}).get("entries", []) == []
            safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
            out = safe(client.post("/api/chat", json={"text": "Where is the loose stone?"}))
            assert "farther" in out["gm_output"]["player_facing_text"]
            safe(client.post("/api/chat", json={"text": "Is there anything nearby I could sit on?"}))
            out = safe(client.post("/api/chat", json={"text": "I sit on the stone seat."}))
            assert "You sit" in out["gm_output"]["player_facing_text"]
            assert storage.load_session()[LEDGER_KEY]["posture"]["kind"] == "sitting"
        else:
            out = safe(client.post("/api/chat", json={"text": "I approach the notice board."}))
            assert "beside the Notice board" in out["gm_output"]["player_facing_text"]
            before = copy.deepcopy(storage.load_session().get("scene_state"))
            out = safe(client.post("/api/chat", json={"text": "I climb onto the broken stonework to get a better view of the road."}))
            text = out["gm_output"]["player_facing_text"]
            assert "not established" in text or "no climbing check" in text
            assert storage.load_session().get("scene_state") == before
            out = safe(client.post("/api/chat", json={"text": "Am I beside the notice board?"}))
            assert "beside the Notice board" in out["gm_output"]["player_facing_text"]
            assert storage.load_session()[LEDGER_KEY]["position"]["kind"] == "beside"
            snap = safe(client.post("/api/snapshots", json={"label": "approach"}))["snapshot"]["id"]
            create(client)
            safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
            out = safe(client.post("/api/chat", json={"text": "Am I beside the notice board?"}))
            assert "beside the Notice board" in out["gm_output"]["player_facing_text"]
            out = safe(client.post("/api/chat", json={"text": "I step back from the notice board."}))
            assert storage.load_session()[LEDGER_KEY]["position"]["kind"] == "back"


def test_failed_session_write_rolls_back(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch)
    enable(monkeypatch)
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_BRANCHING_SESSION", raising=False)
    with TestClient(api.app, raise_server_exceptions=False) as client:
        create(client)
        start(client)
        reach(client)
        safe(client.post("/api/chat", json={"text": "Is there a small loose stone I could shift aside?"}))
        paths = [storage.SESSION_PATH, storage.WORLD_PATH, storage.COMBAT_PATH, storage.SESSION_LOG_PATH]
        before = {path: path.read_bytes() for path in paths}
        original = storage._atomic_write_bytes
        def fail(path, content):
            if path == storage.SESSION_PATH and content != before[path]:
                raise PermissionError("injected physical commit fault")
            return original(path, content)
        monkeypatch.setattr(storage, "_atomic_write_bytes", fail)
        response = client.post("/api/chat", json={"text": "I push the loose stone aside."})
        assert response.status_code == 500
        assert "aside from the stonework" not in response.text
        assert all(path.read_bytes() == payload for path, payload in before.items())
