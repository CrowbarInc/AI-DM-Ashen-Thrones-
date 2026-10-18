"""Interaction completion, discourse precedence, and structural degradation.

The ten independent-smoke turns are replayed from the recorded player lines
and the candidates generation and emission actually produced. Variants change
names, wording, and prior discourse. No paid inference.
"""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from game.api import app
from game.discourse_state import DISCOURSE_FOCUS_KEY, commit_discourse_focus
from game.interaction_completion import (
    attribution_shell,
    explicit_discourse_binding,
    nonverbal_resolution,
    player_utterance_embedded,
    structural_assessment,
)
from game.live_resolution import obligation_preserving_fallback_line
from game.resolution_contract import (
    assess_contract_satisfaction,
    candidate_may_replace,
    construct_resolution_contract,
    detect_semantic_degradation,
    enforce_emitted_contract_monotonicity,
    remember_satisfied_candidate,
)
from game import storage
from game.defaults import default_campaign, default_character, default_combat, default_conditions, default_session, default_world
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage


RUNNER = {
    "type": "interlocutor",
    "id": "tavern_runner",
    "label": "Tavern Runner",
    "aliases": ["runner", "stew seller"],
    "source": "scene",
}
CAPTAIN = {
    "type": "interlocutor",
    "id": "guard_captain",
    "label": "Guard Captain",
    "aliases": ["captain", "guard"],
    "source": "scene",
}
CLERK = {
    "type": "interlocutor",
    "id": "yard_clerk",
    "label": "Yard Clerk",
    "aliases": ["clerk"],
    "source": "scene",
}
MERCHANT = {
    "type": "interlocutor",
    "id": "cloth_merchant",
    "label": "Cloth Merchant",
    "aliases": ["merchant"],
    "source": "scene",
}
WATCHER = {
    "type": "interlocutor",
    "id": "threadbare_watcher",
    "label": "Threadbare watcher",
    "aliases": ["watcher", "threadbare"],
    "source": "scene",
}
NOTICE = {
    "type": "object",
    "id": "notice_board",
    "label": "Notice board",
    "aliases": ["notice", "board", "curfew notice"],
    "source": "scene",
}
DOOR = {
    "type": "object",
    "id": "side_door",
    "label": "Side door",
    "aliases": ["door"],
    "source": "scene",
}
CATALOG = [RUNNER, CAPTAIN, CLERK, MERCHANT, WATCHER, NOTICE, DOOR]

TURN1 = "I shoulder through the crowd toward the tavern runner and ask what the stew costs, and whether there is somewhere dry to eat it."
TURN1_ANSWER = (
    '"I can\'t say for sure right now. Prices shift quick. As for a dry spot, '
    'best you check with the serjeant near the roster board."'
)
TURN1_SHELL = "Tavern Runner says with a tight shrug, voice low and hurried,"
TURN2 = "I lean closer so I can hear him over the rain. How much for a bowl, and where can I eat it out of this weather?"
TURN2_ANSWER = 'Tavern Runner says, "Prices shift with the rumors, and dry spots are scarce unless you know the right people."'
TURN3 = "I keep my voice down. A number, then. What are you charging for one bowl right now, and who are these right people?"
TURN3_ANSWER = '"I can\'t give you a solid number right now, and I will not name those people in this crowd."'
TURN3_LEAK = (
    'Tavern Runner says, "I couldn\'t tell you I keep my voice down. A number, then. '
    'What are you charging for one bowl right n; you will need another source."'
)
TURN4 = "I leave the runner and step up to the nearest guard holding the line. I ask, calmly, what a traveler has to do to pass this gate."
TURN4_ANSWER = '"You need a reason the watch will accept, or you wait with the line."'
TURN4_SHELL = "The tavern runner replies, voice low and wary, eyes flicking to the guards holding the line."
TURN5 = "I ignore the stew seller. I face the guard holding the line and say it again: I am not asking him. What do I need to show or pay to pass this gate?"
TURN5_SHELL = "Tavern Runner says, voice low and careful. The runner glances past you toward the stern figure managing the crowd, adding,"
TURN6 = "I follow his glance to the stern figure managing the crowd. I walk over and ask that person, directly, what it takes for a traveler to get through this gate."
TURN6_ANSWER = (
    'You approach the stern figure managing the crowd, a guard captain. '
    '"These days it takes more than coin. You need a reason the watch will accept."'
)
TURN7 = "I nod. I do not have local allies to name. What is the proper toll today, and if I pay it, will you let me through?"
TURN7_FIND = (
    "No one steps forward to answer. If you want the toll, you might need to find the guard captain managing the crowd."
)
TURN8 = "Captain, I am standing in front of you. Either name today's toll, or tell me you will not let me through."
TURN8_ANSWER = '"I cannot name a fixed toll today. If that is unacceptable, then you will not be allowed through."'
TURN9 = "He is done with me. I step back from the captain and read the notice board, starting with the curfew, so I know whether I can even wait out here."
TURN9_CLUE = "The missing patrol was last seen taking the northwest mud track past the crates."
TURN9_STALL = "On closer inspection, the notice board lists taxes, curfew rules, and a warning about a missing patrol. Closer looking yields nothing further."
TURN10 = "The board will not give me the rule. I leave it and walk over to the threadbare figure who has been standing still. I ask, quietly, whether they are waiting to get in or watching for someone."
TURN10_ANSWER = '"I am watching for a particular face. I will not say more than that."'
TURN10_SCENE = "As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line."


def _focus(**slots):
    focus = {
        "scene_id": "frontier_gate",
        "active_interlocutor": None,
        "active_claim": None,
        "active_actionable_lead": None,
        "active_inspected": None,
        "last_attempted_action": None,
    }
    focus.update(slots)
    return {"active_scene_id": "frontier_gate", "turn_counter": 4, DISCOURSE_FOCUS_KEY: focus}


def _runner_focus():
    return _focus(
        active_interlocutor={"id": "tavern_runner", "label": "Tavern Runner", "kind": "interlocutor", "turn_index": 2}
    )


def _captain_focus():
    return _focus(
        active_interlocutor={"id": "guard_captain", "label": "Guard Captain", "kind": "interlocutor", "turn_index": 6},
        active_inspected={"id": "notice_board", "label": "Notice board", "kind": "object", "turn_index": 9},
    )


def _contract(text, session=None, referents=None):
    return construct_resolution_contract(
        player_text=text,
        session=session if session is not None else _focus(),
        scene_id="frontier_gate",
        canonical_referents=CATALOG if referents is None else referents,
    )


def _resolution(contract, *, speaker_id="", speaker_name=""):
    social = {}
    if speaker_id:
        social = {"npc_id": speaker_id, "npc_name": speaker_name or speaker_id}
    return {
        "kind": "question",
        "prompt": contract.raw_input,
        "social": social,
        "metadata": {"resolution_contract": contract.as_dict()},
    }


def _keep(better, worse, contract, speaker_id="", speaker_name=""):
    resolution = _resolution(contract, speaker_id=speaker_id, speaker_name=speaker_name)
    allowed, reason = candidate_may_replace(better, worse, resolution)
    assert allowed is False, reason
    gm = {"player_facing_text": better, "metadata": {}}
    remember_satisfied_candidate(gm, better, resolution)
    gm["player_facing_text"] = worse
    enforce_emitted_contract_monotonicity(gm, resolution)
    report = detect_semantic_degradation(better, worse, resolution)
    return gm["player_facing_text"], report


def test_attribution_shells_and_nonverbal_resolution_are_structural():
    assert attribution_shell("The sentry says,")
    assert attribution_shell("She replies cautiously,")
    assert attribution_shell("The merchant answers with a shrug,")
    assert attribution_shell(TURN1_SHELL)
    assert attribution_shell(TURN4_SHELL)
    assert not attribution_shell(TURN1_ANSWER)
    assert not attribution_shell(TURN8_ANSWER)
    assert nonverbal_resolution("He shakes his head and bars the doorway.")
    assert not nonverbal_resolution("The guard looks nervous and shifts his weight.")
    assert structural_assessment("He shakes his head and bars the doorway.", {"operation": "ask", "contract_id": "x"})["valid"]


def test_player_utterance_is_not_a_fallback_subject():
    assert player_utterance_embedded(TURN3_LEAK, TURN3)
    contract = _contract(TURN3, _runner_focus())
    resolution = _resolution(contract, speaker_id="tavern_runner", speaker_name="Tavern Runner")
    line = obligation_preserving_fallback_line(resolution)
    assert "keep my voice down" not in line.lower()
    assert "what are you charging" not in line.lower()
    assert player_utterance_embedded(line, TURN3) is False


def test_explicit_switch_variants_and_pronoun_follow_up():
    merchant = _focus(active_interlocutor={"id": "cloth_merchant", "label": "Cloth Merchant", "kind": "interlocutor"})
    stop = _contract("I stop talking to the merchant and ask the guard what the watch requires.", merchant)
    assert stop.interlocutor_id == "guard_captain"
    assert stop.operation == "ask"
    clerk = _contract("Not her. I mean the clerk.", merchant)
    assert clerk.interlocutor_id == "yard_clerk"
    leave = _contract("I leave him there and approach the woman by the door.", _runner_focus())
    assert leave.interlocutor_id != "tavern_runner"
    asking = _contract("I'm asking the captain, not the runner.", _runner_focus())
    assert asking.interlocutor_id == "guard_captain"
    follow = _contract("What does he mean by that?", _captain_focus())
    assert follow.interlocutor_id == "guard_captain"


def test_compound_actions_keep_the_terminal_operation():
    ask = _contract("I walk over to the woman and ask where the road leads.", _runner_focus())
    assert ask.operation == "ask"
    assert ask.interlocutor_id != "tavern_runner"
    read = _contract("I step beside the notice and read it.", _captain_focus())
    assert read.operation == "inspect"
    assert "notice" in str(read.target_ref.id_or_text or "").lower()
    listen = _contract("I move closer and listen at the door.")
    assert listen.operation == "perceive"
    hand = _contract("I approach the clerk and hand him the paper.", _runner_focus())
    assert hand.operation == "act"
    assert hand.interlocutor_id == "yard_clerk"


def test_current_interlocutor_is_not_someone_to_go_find():
    contract = _contract(TURN7, _captain_focus())
    assert contract.interlocutor_id == "guard_captain"
    assessment = assess_contract_satisfaction(TURN7_FIND, contract.as_dict())
    assert "discourse_state_contradiction" in assessment["reasons"]
    kept, report = _keep(TURN8_ANSWER, TURN7_FIND, contract, "guard_captain", "Guard Captain")
    assert "find the guard captain" not in kept.lower()
    assert report["degraded"] is True


def test_smoke_turn_replays_and_structural_degradation():
    turn1 = _contract(TURN1)
    assert turn1.operation == "ask"
    assert turn1.interlocutor_id == "tavern_runner"
    kept, report = _keep(TURN1_ANSWER, TURN1_SHELL, turn1, "tavern_runner", "Tavern Runner")
    assert "can't say" in kept.lower() or "cannot" in kept.lower() or "serjeant" in kept.lower()
    assert report["degraded"] is True
    assert "social_payload_loss" in report["reasons"] or "interaction_completion_loss" in report["reasons"]

    turn2 = _contract(TURN2, _runner_focus())
    assert turn2.interlocutor_id == "tavern_runner"
    assert turn2.operation == "ask"
    report2 = detect_semantic_degradation(TURN2_ANSWER, TURN2_ANSWER, _resolution(turn2))
    assert report2["degraded"] is False
    assert structural_assessment(TURN2_ANSWER, turn2.as_dict())["valid"] is True
    assert attribution_shell(TURN2_ANSWER) is False

    turn3 = _contract(TURN3, _runner_focus())
    kept3, report3 = _keep(TURN3_ANSWER, TURN3_LEAK, turn3, "tavern_runner", "Tavern Runner")
    assert "solid number" in kept3.lower() or "will not name" in kept3.lower()
    assert report3["degraded"] is True
    assert "player_text_leakage" in report3["reasons"]

    turn4 = _contract(TURN4, _runner_focus())
    assert turn4.interlocutor_id != "tavern_runner"
    assert turn4.operation == "ask"
    kept4, report4 = _keep(TURN4_ANSWER, TURN4_SHELL, turn4, "guard_captain", "Guard Captain")
    assert "reason the watch" in kept4.lower()
    assert report4["degraded"] is True

    turn5 = _contract(TURN5, _runner_focus())
    assert turn5.interlocutor_id != "tavern_runner"
    shell = assess_contract_satisfaction(TURN5_SHELL, turn5.as_dict())
    assert shell["status"] != "satisfied"

    turn6 = _contract(TURN6, _runner_focus())
    assert turn6.interlocutor_id != "tavern_runner"
    assert turn6.operation == "ask"
    assert structural_assessment(TURN6_ANSWER, turn6.as_dict())["valid"] is True

    turn8 = _contract(TURN8, _captain_focus())
    assert turn8.interlocutor_id == "guard_captain"
    assert assess_contract_satisfaction(TURN8_ANSWER, turn8.as_dict())["status"] in {"satisfied", "legitimate_nonresolution"}

    turn9 = _contract(TURN9, _captain_focus())
    assert turn9.operation == "inspect"
    assert "notice" in str(turn9.target_ref.id_or_text or "").lower()
    assert turn9.interlocutor_id != "guard_captain"
    assert candidate_may_replace(TURN9_CLUE, "Closer looking yields nothing further.", _resolution(turn9))[0] is False
    detail = detect_semantic_degradation(TURN9_CLUE, TURN9_STALL, _resolution(turn9))
    assert detail["degraded"] is True
    assert "inspection_detail_loss" in detail["reasons"]

    turn10 = _contract(TURN10, _captain_focus())
    assert turn10.operation == "ask"
    assert turn10.interlocutor_id == "threadbare_watcher"
    kept10, report10 = _keep(TURN10_ANSWER, TURN10_SCENE, turn10, "threadbare_watcher", "Threadbare watcher")
    assert "particular face" in kept10.lower()
    assert report10["degraded"] is True
    assert "operation_loss" in report10["reasons"] or "passive_observation_collapse" in report10["reasons"] or "interaction_completion_loss" in report10["reasons"]


def test_rejected_interlocutor_is_cleared_and_follow_up_can_inherit():
    session = _runner_focus()
    contract = _contract("I turn away from the runner.", session)
    commit_discourse_focus(session, contract=contract.as_dict(), scene_id="frontier_gate")
    assert session[DISCOURSE_FOCUS_KEY]["active_interlocutor"] is None
    talking = _captain_focus()
    spoken = _contract("I ask the captain whether the gate is open.", talking)
    commit_discourse_focus(talking, contract=spoken.as_dict(), scene_id="frontier_gate")
    assert talking[DISCOURSE_FOCUS_KEY]["active_interlocutor"]["id"] == "guard_captain"
    later = construct_resolution_contract(
        player_text="What does he mean by that?",
        session=talking,
        scene_id="frontier_gate",
        canonical_referents=CATALOG,
    )
    assert later.interlocutor_id == "guard_captain"


def test_binding_does_not_use_the_smoke_sentences_as_its_only_patterns():
    focus = _focus(active_interlocutor={"id": "yard_clerk", "label": "Yard Clerk", "kind": "interlocutor"})
    binding = explicit_discourse_binding(
        "I leave the clerk and speak to the merchant about the cloth.",
        CATALOG,
        focus[DISCOURSE_FOCUS_KEY],
    )
    assert binding["selected_interlocutor_id"] == "cloth_merchant"
    assert binding["suppress_inherited_interlocutor"] is True


def test_raw_chat_stub_covers_completion_switch_and_leakage(tmp_path, monkeypatch):
    _seed_campaign_start_storage(tmp_path, monkeypatch)
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    session["turn_counter"] = 1
    storage.save_session(session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())

    def fake_gpt(messages, **_kwargs):
        user = ""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                user = str(message.get("content") or "")
                break
        try:
            payload = json.loads(user)
            current = str(payload.get("player_input") or payload.get("raw_player_input") or payload.get("raw_input") or "")
        except (TypeError, ValueError, json.JSONDecodeError):
            current = user
        low = f"{current}\n{user}".lower()
        if "proper toll" in low or "find the captain" in low:
            return _gm_response(TURN7_FIND)
        if "threadbare" in low or "watching for someone" in low:
            return _gm_response(TURN10_SCENE)
        if "not the runner" in low or "asking the captain" in low:
            return _gm_response(TURN8_ANSWER)
        if "stew costs" in low or "tavern runner" in low:
            return _gm_response(TURN1_ANSWER + " " + TURN1_SHELL)
        return _gm_response(TURN2_ANSWER)

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)
    client = TestClient(app)
    asked = client.post(
        "/api/chat",
        json={"text": "I shoulder through the crowd toward the tavern runner and ask what the stew costs."},
    ).json()
    visible = asked["gm_output"]["player_facing_text"]
    assert attribution_shell(visible) is False
    assert '"' in visible
    assert not visible.strip().endswith(",")

    switched = client.post(
        "/api/chat",
        json={"text": "I'm asking the captain, not the runner. What does it take to pass?"},
    ).json()
    contract = switched["resolution"]["metadata"]["resolution_contract"]
    assert contract["interlocutor_id"] == "guard_captain", (
        contract.get("operation"),
        contract.get("interlocutor_id"),
        contract.get("referent_provenance"),
        (contract.get("construction") or {}).get("abstention_reason"),
        (contract.get("construction") or {}).get("referent_reason"),
    )
    assert attribution_shell(switched["gm_output"]["player_facing_text"]) is False

    captain_focus_text = client.post(
        "/api/chat",
        json={"text": "What is the proper toll today, and if I pay it, will you let me through?"},
    ).json()
    toll = captain_focus_text["gm_output"]["player_facing_text"].lower()
    assert "find the guard captain" not in toll

    compound = client.post(
        "/api/chat",
        json={"text": "I leave the board and walk over to the threadbare figure. I ask whether they are watching for someone."},
    ).json()
    compound_contract = compound["resolution"]["metadata"]["resolution_contract"]
    assert compound_contract["operation"] == "ask"
    assert compound_contract["interlocutor_id"] == "threadbare_watcher"
    assert "as you watch the scene" not in compound["gm_output"]["player_facing_text"].lower()

    historical = detect_semantic_degradation(TURN1_ANSWER, TURN1_SHELL, asked["resolution"])
    assert historical["degraded"] is True
