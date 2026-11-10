"""One frozen developer-authored holdout for PR-PLAY-79A. Not external validation.

Do not edit the fixture to chase a failure. Repair product code from development tests.
"""
import copy
import hashlib
import json
from pathlib import Path

from game import storage
from game.authored_consequences import ENROLLMENT
from game.bounded_improvisation import LEDGER_KEY
from game.expressive_dialogue import build_expression_contract, build_expression_prompt
from game.integrated_play import validate_narration
from game.player_initiative import decide
from tests.test_pr_play_76_physical import enable
from tests.test_pr_play_78_integrated import play
from tests.test_pr_play_79a_continuity import gate

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "pr_play_79a_holdout.json"
HOLDOUT_HASH = "a9d564aa0f0ca97934e5f5b5b8a401640b0a0f14461cfe1bbb3cc4bd29062ee4"


def _say(session, scene, world, text):
    _plan, _result, spoken, _changed = play(text, session, scene, world)
    return spoken


def _talk(case):
    session, scene, world = gate()
    spoken = ""
    for text in case["turns"]:
        spoken = _say(session, scene, world, text)
    low = spoken.casefold()
    focus = session[LEDGER_KEY].get("npc_focus")
    status = ((session.get("conversational_context") or {}).get("active_interlocutor") or {}).get("status")
    expected = case["focus"]
    if expected == "ended":
        focus_ok = status == "ended" and focus is None
    elif expected is None:
        focus_ok = focus in {None, ""}
    else:
        focus_ok = focus == expected
    return case["present"] in low and case["absent"] not in low and focus_ok, spoken[:180]


def _invalidate(case):
    session, scene, world = gate()
    kind = case["kind"]
    if kind != "unfocused":
        _say(session, scene, world, "Hello, Gate Guard.")
    if kind == "leave":
        session["active_scene_id"] = "old_milestone"
        later = {"scene": {"id": "old_milestone", "visible_facts": ["A stone milestone leans beside the road."], "interactables": [], "addressables": []}}
        spoken = _say(session, later, world, "Who are you?")
        return "gate guard says" not in spoken.casefold() and session[LEDGER_KEY].get("npc_focus") is None, spoken[:180]
    if kind == "other-scene":
        session["active_scene_id"] = "cinderwatch"
        later = {"scene": {"id": "cinderwatch", "visible_facts": ["The yard is quiet."], "interactables": [], "addressables": []}}
        spoken = _say(session, later, world, "When did you last hear about them?")
        return "gate guard says" not in spoken.casefold(), spoken[:180]
    if kind == "campaign":
        other = copy.deepcopy(session)
        other["campaign_run_id"] = "beta"
        other[ENROLLMENT] = "beta"
        spoken = _say(other, scene, world, "Who are you?")
        return "gate guard says" not in spoken.casefold(), spoken[:180]
    if kind == "foreign-copy":
        other = copy.deepcopy(session)
        other["campaign_run_id"] = "beta"
        other[ENROLLMENT] = "beta"
        spoken = _say(other, scene, world, "What do you know about the missing patrol?")
        original = session[LEDGER_KEY].get("npc_focus") == "gate_guard"
        return original and "gate guard says" not in spoken.casefold(), spoken[:180]
    if kind == "goodbye":
        _say(session, scene, world, "Goodbye.")
        spoken = _say(session, scene, world, "Who are you?")
        return "gate guard says" not in spoken.casefold(), spoken[:180]
    if kind == "norevive":
        _say(session, scene, world, "Goodbye.")
        spoken = _say(session, scene, world, "What do you know about them?")
        return "gate guard says" not in spoken.casefold(), spoken[:180]
    if kind == "end":
        _say(session, scene, world, "I end the conversation.")
        status = session["conversational_context"]["active_interlocutor"]["status"]
        return status == "ended" and session[LEDGER_KEY].get("npc_focus") is None, status
    if kind == "depart":
        for npc in world["npcs"]:
            if npc["id"] == "gate_guard":
                npc["location"] = "old_milestone"
        addressed = session[LEDGER_KEY].get("addressed_npcs") or {}
        if "gate_guard" in addressed:
            addressed["gate_guard"]["location"] = "old_milestone"
            addressed["gate_guard"]["scene_id"] = "old_milestone"
        spoken = _say(session, scene, world, "Who are you?")
        return "gate guard says" not in spoken.casefold() and session[LEDGER_KEY].get("npc_focus") is None, spoken[:180]
    if kind == "switch":
        spoken = _say(session, scene, world, "Hello, Gate Serjeant.")
        return session[LEDGER_KEY].get("npc_focus") == "gate_serjeant" and "gate serjeant" in spoken.casefold(), spoken[:180]
    if kind == "unfocused":
        spoken = _say(session, scene, world, "Who are you?")
        return "says" not in spoken.casefold(), spoken[:180]
    return False, kind


def _route(case):
    session, scene, world = gate()
    _say(session, scene, world, "Hello, Gate Guard.")
    text = case["text"]
    if text in {"What does the notice board say?", "Where am I?", "What do I know about the patrol?"}:
        decision = decide(text, scene=scene, world=world, session=session)
        spoken = decision.player_facing_text or ""
    else:
        spoken = _say(session, scene, world, text)
    low = spoken.casefold()
    return case["present"] in low and case["absent"] not in low, spoken[:180]


def _prompt(case):
    contract = build_expression_contract(
        player_text=case["question"],
        speaker_name="Gate Guard",
        speaker_id="gate_guard",
        fallback_line="The notice board lists a warning about a missing patrol.",
        fallback_source="background.authorized_identity_or_public",
        forced_operation="bounded_social_line",
        extra_facts=["The notice board lists a warning about a missing patrol."],
    )
    prompt = build_expression_prompt(contract)
    blob = prompt["system"] + prompt["user"]
    ok = case["question"] in blob and "northwest" not in blob.casefold() and len(blob) < 2500
    return ok, str(len(blob))


def _save(case):
    session, scene, world = gate()
    _say(session, scene, world, "Hello, Gate Guard.")
    _say(session, scene, world, case["text"])
    expected = session[LEDGER_KEY].get("npc_focus")
    slot = copy.deepcopy(session["conversational_context"]["active_interlocutor"])
    storage.save_session(session)
    session[LEDGER_KEY]["npc_focus"] = "tampered"
    restored = storage.load_session()
    again = _say(restored, scene, world, "Who are you?")
    ok = (
        restored[LEDGER_KEY].get("npc_focus") == expected
        and restored["conversational_context"]["active_interlocutor"]["npc_id"] == slot["npc_id"]
        and "northwest" not in again.casefold()
    )
    return ok, again[:180]


def test_pr_play_79a_holdout_is_frozen(monkeypatch):
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    raw = FIXTURE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == HOLDOUT_HASH
    payload = json.loads(raw)
    assert payload["external_validation"] is False
    cases = payload["cases"]
    assert 100 <= len(cases) <= 120
    assert sum(1 for case in cases if case.get("multi_turn")) >= 20
    assert sum(1 for case in cases if case["lane"] == "save") >= 15
    assert sum(1 for case in cases if case.get("paraphrase")) >= 15
    assert sum(1 for case in cases if case.get("rejection")) >= 15
    assert sum(1 for case in cases if case["lane"] == "invalidate") >= 10
    assert sum(1 for case in cases if case.get("efficiency")) >= 10
    results = []
    for index, case in enumerate(cases, start=1):
        lane = case["lane"]
        if lane == "talk":
            ok, detail = _talk(case)
        elif lane == "invalidate":
            ok, detail = _invalidate(case)
        elif lane == "narration":
            verdict = validate_narration(case["candidate"], case["facts"], session={"clue_knowledge": {}})
            ok = verdict["adopt"] is case["adopt"]
            detail = verdict["reasons"]
        elif lane == "prompt":
            ok, detail = _prompt(case)
        elif lane == "save":
            ok, detail = _save(case)
        elif lane == "route":
            ok, detail = _route(case)
        else:
            ok, detail = False, "unknown lane"
        results.append({"id": f"H{index:03d}", "lane": lane, "ok": ok, "detail": detail})
    failed = [row for row in results if not row["ok"]]
    assert not failed
    assert all(row["ok"] for row in results)
