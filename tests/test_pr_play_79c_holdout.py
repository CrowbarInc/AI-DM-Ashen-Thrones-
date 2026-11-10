"""One frozen developer-authored holdout for PR-PLAY-79C. Not external validation.

The fixture is hashed below and is not edited after a failure.
"""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from game.authored_consequences import ENROLLMENT
from game.bounded_improvisation import LEDGER_KEY
from game.integrated_play import validate_narration
from game.physical_adjudication import commit_physical, plan_physical
from game.player_initiative import decide
from game.publication_contract import narration_skip
from tests.test_pr_play_76_physical import add, door, enable, stage
from tests.test_pr_play_78_integrated import play
from tests.test_pr_play_79a_continuity import gate

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "pr_play_79c_holdout.json"
HOLDOUT_HASH = "3fce8565e2287a35e225bb0761a4470f6a03462b2de271b8ac3cb6e831216dae"
RESULTS = Path(__file__).resolve().parents[1] / "artifacts" / "pr_play_79c" / "holdout_results.json"


def _play(session, scene, world, text):
    _plan, result, said, changed = play(text, session, scene, world)
    return said, result, changed


def _yard(setup):
    session, scene, _world = stage()
    scene["scene"]["interactables"].append(
        {"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]}
    )
    if setup == "door":
        add(session, ident="door", label="wooden door", aliases=["door"], **door())
    elif setup == "stuck":
        add(session, ident="door", label="stuck door", aliases=["door"], **door(), skill_check={"skill_id": "athletics", "dc": 30})
    elif setup == "beside":
        add(session, ident="bench", label="wooden bench", aliases=["bench"], use="seat")
        text = "I approach the bench."
        plan = plan_physical(text, session=session, scene=scene, world={"npcs": []})
        commit_physical(
            scene, session, {"npcs": []}, {"id": plan["id"], "target_id": plan["id"]},
            prompt=text, action_id=plan["id"], label="t",
        )
    elif setup == "crates":
        add(session, ident="a", label="oak crate", aliases=["crate"], mobility="movable", weight="light")
        add(session, ident="b", label="pine crate", aliases=["crate"], mobility="movable", weight="light")
    elif setup == "tracks":
        scene["scene"]["visible_facts"] = ["Faint tracks mark the mud beside the milestone."]
    return session, scene


def _action(case):
    session, scene = _yard(case["setup"])
    world = {"npcs": [], "world_state": {"flags": {}}}
    plan = plan_physical(case["text"], session=session, scene=scene, world=world)
    said = ""
    changed = False
    if plan and plan.get("mode") == "interact":
        result = commit_physical(
            scene, session, world, {"id": plan["id"], "target_id": plan["id"]},
            prompt=case["text"], action_id=plan["id"], label="t",
        )
        said = result["metadata"]["engine_publication"]
        changed = bool(result["state_changes"]["mutation"])
    elif plan:
        said = plan.get("message") or ""
    else:
        said, _result, changed = _play(session, scene, world, case["text"])
    low = (said or "").casefold()
    present = case["present"]
    ok = (not present or present in low) and case["absent"] not in low and changed is case["mutation"]
    return ok, said[:180]


def _run(case):
    lane = case["lane"]
    if lane == "dialogue":
        session, scene, world = gate()
        said = ""
        for text in case["turns"]:
            said, _result, _changed = _play(session, scene, world, text)
        low = said.casefold()
        ok = case["present"] in low and case["absent"] not in low and "says" in low
        return ok, said[:180]
    if lane == "environment":
        session, scene, world = gate()
        for text in case["turns"][:-1]:
            _play(session, scene, world, text)
        decision = decide(case["turns"][-1], scene=scene, world=world, session=session)
        said = decision.player_facing_text or ""
        low = said.casefold()
        ok = case["present"] in low and case["absent"] not in low
        return ok, said[:180]
    if lane == "action":
        return _action(case)
    if lane == "narration":
        verdict = validate_narration(case["candidate"], case["facts"], session={"clue_knowledge": {}})
        return verdict["adopt"] is case["adopt"], str(verdict["reasons"])
    if lane == "contract":
        meta = {"publication_contract": case["contract"]}
        if case["text"]:
            meta["engine_publication"] = case["text"]
        skipped = narration_skip({"kind": "interact", "metadata": meta}, scene={}, session={})
        if case["text"] is None:
            return skipped is None, str(skipped)
        return skipped == (case["text"], case["reason"]), str(skipped)
    if lane == "save":
        session, scene, world = gate()
        _play(session, scene, world, "Hello, Gate Guard.")
        _play(session, scene, world, case["first"])
        source = copy.deepcopy(session["conversational_context"]["active_interlocutor"])
        restored = copy.deepcopy(session)
        said, _result, _changed = _play(restored, scene, world, case["resume"])
        low = said.casefold()
        ok = case["present"] in low and case["absent"] not in low
        ok = ok and session["conversational_context"]["active_interlocutor"] == source
        return ok, said[:180]
    if lane == "isolation":
        return _isolation(case["kind"])
    return False, "unknown lane"


def _isolation(kind):
    session, scene, world = gate()
    if kind == "campaign":
        _play(session, scene, world, "Hello, Gate Guard.")
        other = {
            "campaign_run_id": "beta", "active_scene_id": "frontier_gate", "turn_counter": 2,
            ENROLLMENT: "beta", LEDGER_KEY: {"entries": [], "physical_state": {}, "investigation_notes": []},
        }
        said, _result, _changed = _play(other, scene, world, "Who are you?")
        ok = "i am gate guard" not in said.casefold()
        ok = ok and session["conversational_context"]["active_interlocutor"]["npc_id"] == "gate_guard"
        return ok, said[:180]
    if kind == "scene":
        _play(session, scene, world, "Hello, Gate Guard.")
        session["active_scene_id"] = "old_milestone"
        later = {"scene": {"id": "old_milestone", "visible_facts": ["A stone milestone leans beside the road."], "interactables": [], "addressables": []}}
        said, _result, _changed = _play(session, later, world, "What about the patrol again?")
        return session[LEDGER_KEY].get("npc_focus") is None and "gate guard says" not in said.casefold(), said[:180]
    if kind == "sentinel":
        scene["scene"]["hidden_facts"].append("SENTINEL_HIDDEN_PAYROLL")
        said, _result, _changed = _play(session, scene, world, "Hello, Gate Guard.")
        return "sentinel" not in said.casefold() and "says" in said.casefold(), said[:180]
    if kind == "focus":
        _play(session, scene, world, "Hello, Gate Guard.")
        return session[LEDGER_KEY].get("npc_focus") == "gate_guard", str(session[LEDGER_KEY].get("npc_focus"))
    if kind == "goodbye":
        _play(session, scene, world, "Hello, Gate Guard.")
        said, _result, _changed = _play(session, scene, world, "Goodbye.")
        status = session["conversational_context"]["active_interlocutor"]["status"]
        return status == "ended" and "goodbye" in said.casefold(), said[:180]
    if kind == "position":
        yard, place = _yard("milestone")
        text = "I approach the milestone."
        plan = plan_physical(text, session=yard, scene=place, world={"npcs": []})
        result = commit_physical(place, yard, {"npcs": []}, {"id": plan["id"], "target_id": plan["id"]}, prompt=text, action_id=plan["id"], label="t")
        ok = yard[LEDGER_KEY]["position"]["kind"] == "beside" and result["state_changes"]["mutation"] is True
        return ok, result["metadata"]["engine_publication"]
    if kind == "door":
        yard, place = _yard("door")
        text = "I open the door."
        plan = plan_physical(text, session=yard, scene=place, world={"npcs": []})
        result = commit_physical(place, yard, {"npcs": []}, {"id": plan["id"], "target_id": plan["id"]}, prompt=text, action_id=plan["id"], label="t")
        said = result["metadata"]["engine_publication"]
        return "you open" in said.casefold() and result["state_changes"]["mutation"] is True, said[:180]
    if kind == "noop":
        yard, place = _yard("milestone")
        text = "I step back from the milestone."
        plan = plan_physical(text, session=yard, scene=place, world={"npcs": []})
        result = commit_physical(place, yard, {"npcs": []}, {"id": plan["id"], "target_id": plan["id"]}, prompt=text, action_id=plan["id"], label="t")
        said = result["metadata"]["engine_publication"]
        ok = "unchanged" in said.casefold() and result["state_changes"]["mutation"] is False
        ok = ok and "not up against" not in said.casefold()
        return ok, said[:180]
    if kind == "speech":
        said, result, _changed = _play(session, scene, world, "Hello, Gate Guard.")
        trace = session["last_publication"]
        ok = "says" in said.casefold() and trace["dialogue_published"] and trace["narration_requested"] is False
        ok = ok and result["metadata"]["skip_primary_narration"] is True
        return ok, said[:180]
    if kind == "contract":
        said, result, _changed = _play(session, scene, world, "Hello, Gate Guard.")
        ok = result["metadata"]["publication_contract"] == "FINAL_ENGINE_RESPONSE"
        ok = ok and result["metadata"]["engine_publication"] == said
        return ok, said[:180]
    return False, kind


@pytest.fixture(autouse=True)
def _flags(monkeypatch):
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION", "1")
    monkeypatch.setenv("ASHEN_BOUNDED_SPEECH", "1")


def test_frozen_holdout_runs_once():
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == HOLDOUT_HASH
    document = json.loads(raw)
    assert document["external_validation"] is False
    results = []
    for case in document["cases"]:
        ok, detail = _run(case)
        results.append({"id": case["id"], "ok": ok, "detail": detail, "group": case.get("group")})
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps({"passed": sum(item["ok"] for item in results), "results": results}, indent=2), encoding="utf-8")
    failed = [item["id"] for item in results if not item["ok"]]
    assert not failed
