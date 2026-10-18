"""PR-BR Continuation 19: hard-authority boundary and contract canonicalization.

Deterministic only. No paid model calls.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game.api import app
from game.bounded_improvisation import INCIDENTAL_KIND, NPC_CLAIM_KIND, validate_bounded_improvisation_proposal
from game.defaults import default_campaign, default_character, default_combat, default_conditions, default_session, default_world
from game.discourse_state import DISCOURSE_FOCUS_KEY, note_emitted_npc_claim, read_discourse_focus
from game.immutable_valid_response import (
    PROVENANCE_INITIAL,
    PROVENANCE_REGENERATION,
    commit_text,
    effects_allowed,
    regeneration_feedback,
    run_preserve_if_valid,
    validate_generated_response,
)
from game.interpretation_proposal import span_is_malformed
from game.proposition_authority import (
    CONSEQUENTIAL_KIND,
    price_class,
    unauthorized_authoritative_rules,
)
from game.resolution_contract import construct_resolution_contract
from game import storage
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage

ROOT = Path(__file__).resolve().parents[1]
C18_TURNS = ROOT / "artifacts" / "pr_br_continuation18" / "20261001T225126Z" / "turns.json"

THIRD_BELL = (
    "Travelers can still pass, but only until the watch changes at the third bell. "
    "After that, the gates close until morning."
)
GROUNDED_SCHEDULE = "The city gate closes when the watch changes at the third bell."
RUMOR = "I heard they may close the gate around the third bell tonight."
BOUNDED = (
    "The runner shrugs, tugs a grey cloak against the rain, and nods at a barley-and-onion stew."
)

RUNNER = {"id": "tavern_runner", "type": "interlocutor", "label": "Tavern Runner", "aliases": ["runner", "tavern runner"]}
GUARD = {"id": "gate_guard", "type": "interlocutor", "label": "Gate Guard", "aliases": ["guard", "nearest guard"]}
MERCHANT = {"id": "cloth_merchant", "type": "interlocutor", "label": "Cloth Merchant", "aliases": ["merchant"]}
NOTICE = {"id": "notice_board", "type": "object", "label": "Notice board", "aliases": ["notice"]}
CATALOG = [RUNNER, GUARD, MERCHANT, NOTICE]

LONG_CLAIM = (
    "From what I heard, the ash compact census has slowed things down, making that route a bit of a choke point. "
    "But as for whether the carts are still passing, that is one of those things that changes by the hour around here."
)


def _focus(**slots):
    focus = {
        "scene_id": "frontier_gate",
        "active_interlocutor": {"id": "tavern_runner", "label": "Tavern Runner", "kind": "interlocutor"},
        "active_claim": None,
        "active_actionable_lead": None,
        "active_inspected": None,
        "last_attempted_action": None,
    }
    focus.update(slots)
    return {"active_scene_id": "frontier_gate", "turn_counter": 3, DISCOURSE_FOCUS_KEY: focus}


def _contract(text, session=None, interpreter=None):
    return construct_resolution_contract(
        player_text=text,
        session=session if session is not None else _focus(),
        scene_id="frontier_gate",
        canonical_referents=CATALOG,
        model_interpreter=interpreter,
    )


def _verdict(text, corpus=""):
    return validate_generated_response(text, authored_corpus=corpus, player_text="What is the rule?")


def test_third_bell_ungrounded_schedule_is_hard_invalid_and_retries_once():
    verdict = _verdict(THIRD_BELL)
    assert verdict["hard_valid"] is False
    assert "ungrounded_authoritative_rule" in verdict["reasons"]
    assert any(row["kind"] == CONSEQUENTIAL_KIND and row["family"] == "schedule" for row in verdict["authority"])
    feedback = regeneration_feedback(verdict["reasons"])
    assert "ungrounded authoritative world rule" in feedback.lower()
    assert "third bell" not in feedback.lower()
    assert THIRD_BELL not in feedback

    def _retry(note):
        assert "ungrounded authoritative" in note.lower()
        return {"player_facing_text": "The guard says, \"I cannot name the closing hour from here.\"", "metadata": {}}

    sealed = run_preserve_if_valid(
        {"player_facing_text": THIRD_BELL, "metadata": {}},
        regenerate=_retry,
        resolution={"kind": "question", "metadata": {"resolution_contract": {"operation": "ask", "contract_id": "rc"}}},
        player_text="Can travelers still pass?",
    )
    assert sealed["metadata"]["accepted_response"]["provenance"] == PROVENANCE_REGENERATION
    assert "third bell" not in sealed["player_facing_text"].lower()
    assert effects_allowed({"player_facing_text": THIRD_BELL, "metadata": {"accepted_response": {"provenance": "rejected", "immutable": False, "text": THIRD_BELL}}}) is False


FAITHFUL_THIRD_BELL = "The gate closes when the watch changes at the third bell."


def _schedule_resolution(player: str, *, interlocutor: str | None = "gate_guard") -> dict:
    from game.gm_resolution_decision import attach_gm_resolution_decision

    contract = {
        "contract_id": "c19_third_bell",
        "operation": "ask",
        "raw_input": player,
        "conversational_subject": player,
        "dimensions": ["content"],
    }
    if interlocutor:
        contract["interlocutor_id"] = interlocutor
    resolution = {"kind": "question", "metadata": {"resolution_contract": contract}}
    attach_gm_resolution_decision(
        resolution,
        session={"active_scene_id": "frontier_gate"},
        scene={"scene": {"id": "frontier_gate", "visible_facts": [GROUNDED_SCHEDULE]}},
        world={"npcs": []},
    )
    return resolution


def test_grounded_third_bell_is_authoritative_and_kept():
    """The authored closing rule stays usable. The extra pass/morning claims do not.

    Corpus-only grounding used to keep THIRD_BELL once "third bell" was in the
    schedule corpus. The live decision audits each sentence. Faithful lexical
    paraphrase is accepted. The travelers-pass and until-morning sentences are not.
    """
    from game.gm_resolution_decision import DECISION_METADATA_KEY, audit_narration_against_decision

    player = "I ask the guard what hour the gate closes."
    resolution = _schedule_resolution(player)
    decision = resolution["metadata"][DECISION_METADATA_KEY]
    schedule_rows = [
        row
        for row in decision["proposed_facts"]
        if row.get("text") == GROUNDED_SCHEDULE
    ]
    assert schedule_rows
    assert schedule_rows[0]["authorized"] is True
    assert schedule_rows[0]["semantic_identity"] == {}

    faithful = audit_narration_against_decision(
        FAITHFUL_THIRD_BELL,
        decision=decision,
        authored_corpus=GROUNDED_SCHEDULE,
    )
    assert faithful["hard_valid"] is True

    residual = audit_narration_against_decision(
        THIRD_BELL,
        decision=decision,
        authored_corpus=GROUNDED_SCHEDULE,
    )
    assert residual["hard_valid"] is False
    assert all("proposition_authority" in row["reason_codes"] for row in residual["violations"])

    sealed = run_preserve_if_valid(
        {"player_facing_text": THIRD_BELL, "metadata": {}},
        regenerate=lambda _note: {"player_facing_text": FAITHFUL_THIRD_BELL, "metadata": {}},
        resolution=resolution,
        player_text=player,
        scene={"scene": {"id": "frontier_gate", "visible_facts": [GROUNDED_SCHEDULE]}},
        authored_corpus=GROUNDED_SCHEDULE,
    )
    assert sealed["player_facing_text"] == FAITHFUL_THIRD_BELL
    assert sealed["metadata"]["accepted_response"]["provenance"] == PROVENANCE_REGENERATION

    def _still_residual(_note):
        return {"player_facing_text": THIRD_BELL, "metadata": {}}

    fallback = run_preserve_if_valid(
        {"player_facing_text": THIRD_BELL, "metadata": {}},
        regenerate=_still_residual,
        resolution=resolution,
        player_text=player,
        scene={"scene": {"id": "frontier_gate", "visible_facts": [GROUNDED_SCHEDULE]}},
        authored_corpus=GROUNDED_SCHEDULE,
    )
    assert fallback["player_facing_text"] == GROUNDED_SCHEDULE
    assert "travelers" not in fallback["player_facing_text"].lower()
    assert "morning" not in fallback["player_facing_text"].lower()
    assert fallback["metadata"]["decision_review"]["acceptance"]["why"] == "authorized_observation"


def test_npc_rumor_is_a_claim_and_not_world_truth():
    verdict = _verdict(RUMOR)
    assert verdict["hard_valid"] is True
    assert unauthorized_authoritative_rules(RUMOR) == []
    assert any(row["kind"] == NPC_CLAIM_KIND and row["grounded"] is False for row in verdict["authority"])
    session = _focus()
    scene = {"scene": {"id": "frontier_gate", "visible_facts": ["The notice board lists taxes and curfew rules."]}}
    assert note_emitted_npc_claim(session, emitted_text=f'The runner says, "{RUMOR}"', scene_id="frontier_gate") is True
    claim = read_discourse_focus(session)["active_claim"]
    assert claim["epistemic_status"] in {"hearsay", "rumor", "uncertain"}
    assert "third bell" in claim["label"].lower()
    assert RUMOR.lower() not in " ".join(scene["scene"]["visible_facts"]).lower()
    assert claim.get("kind") == "claim"


def test_bounded_incidental_detail_stays_valid():
    verdict = _verdict(BOUNDED)
    assert verdict["hard_valid"] is True
    assert "ungrounded_authoritative_rule" not in verdict["reasons"]
    decision = validate_bounded_improvisation_proposal(
        {
            "kind": INCIDENTAL_KIND,
            "category": "food_composition",
            "content": "The stew is barley, onion, and pepper.",
            "scope": "scene",
            "consequence_level": "low",
        },
        session={},
        scene={"scene": {"id": "frontier_gate"}},
        world={},
    )
    assert decision.accepted is True


def test_price_temporal_and_access_families_follow_pr_bn():
    assert price_class("A bowl of stew costs two coppers.") == "mundane"
    assert price_class("I hear a street cloak might go for about two silver.") == "mundane"
    assert price_class("The official gate toll is two silver.") == "official"
    assert price_class("The tax is two gold for every wagon.") == "official"
    mundane = validate_bounded_improvisation_proposal(
        {
            "kind": "incidental_fact",
            "category": "mundane_service_detail",
            "content": "A bowl of stew costs two coppers.",
            "scope": "scene",
            "consequence_level": "low",
        },
        session={},
        scene={"scene": {"id": "frontier_gate"}},
        world={},
    )
    assert mundane.accepted is True
    official = validate_bounded_improvisation_proposal(
        {
            "kind": "incidental_fact",
            "category": "mundane_service_detail",
            "content": "The official gate toll is two silver.",
            "scope": "scene",
            "consequence_level": "low",
        },
        session={},
        scene={"scene": {"id": "frontier_gate"}},
        world={},
    )
    assert official.accepted is False
    assert "content:official_levy" in official.reason_codes
    rumor_price = validate_bounded_improvisation_proposal(
        {
            "kind": "npc_claim",
            "category": "rumor",
            "content": "I heard the toll might be two silver.",
            "epistemic_status": "rumor",
            "scope": "scene",
            "consequence_level": "low",
            "speaker_id": "tavern_runner",
        },
        session={},
        scene={"scene": {"id": "frontier_gate"}},
        world={},
    )
    assert rumor_price.accepted is True
    assert rumor_price.entry["truth_status"] == "not_world_truth"

    assert _verdict("The soup will be ready in a few minutes.")["hard_valid"] is True
    assert _verdict("I think they might be back shortly.")["hard_valid"] is True
    assert _verdict(RUMOR)["hard_valid"] is True
    assert _verdict("The city gate closes at the third bell.")["hard_valid"] is False
    assert _verdict("The city gate closes at the third bell.", GROUNDED_SCHEDULE)["hard_valid"] is True

    assert _verdict("You need papers.")["hard_valid"] is False
    assert _verdict("Only guild members may enter.")["hard_valid"] is False
    assert _verdict("Travelers pay two silver.")["hard_valid"] is False
    assert _verdict("The bridge closes after sunset.")["hard_valid"] is False
    assert _verdict("I heard you might need papers.")["hard_valid"] is True
    assert _verdict("Someone said only guild members may enter.")["hard_valid"] is True
    assert _verdict("You need papers.", "Travelers need papers to pass the gate.")["hard_valid"] is True
    negotiated = _verdict("I can do the stew for one copper if you are buying now.")
    assert negotiated["hard_valid"] is True


def test_rejected_rule_does_not_persist_and_accepted_claim_keeps_epistemic_status():
    session = _focus()
    rejected = {"player_facing_text": THIRD_BELL, "metadata": {}}
    sealed = run_preserve_if_valid(
        rejected,
        regenerate=lambda _note: {"player_facing_text": "The guard says, \"I do not know the hour.\"", "metadata": {}},
        resolution={"kind": "question", "metadata": {"resolution_contract": {"operation": "ask"}}},
        player_text="When does the gate close?",
    )
    assert commit_text(sealed)
    assert "third bell" not in commit_text(sealed).lower()
    note_emitted_npc_claim(session, emitted_text=commit_text(sealed), scene_id="frontier_gate")
    claim = read_discourse_focus(session).get("active_claim")
    if isinstance(claim, dict):
        assert "third bell" not in str(claim.get("label") or "").lower()
    accepted = _focus()
    note_emitted_npc_claim(
        accepted,
        emitted_text='The runner says, "I heard they may close the gate around the third bell tonight."',
        scene_id="frontier_gate",
    )
    stored = read_discourse_focus(accepted)["active_claim"]
    assert stored["epistemic_status"] in {"hearsay", "rumor", "uncertain"}
    assert stored["epistemic_status"] != "world_truth"


def test_source_follow_up_binds_the_claim_id_not_the_previous_response():
    session = _focus(
        active_claim={"id": "emitted_85a7ac5156", "label": LONG_CLAIM, "kind": "claim", "turn_index": 1},
    )
    contract = _contract("Who told him that?", session)
    assert contract.operation == "ask"
    assert contract.dimension == "source"
    assert contract.interlocutor_id == "tavern_runner"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.type == "claim"
    assert contract.discourse_ref.id == "emitted_85a7ac5156"
    assert contract.target_ref is not None
    assert contract.target_ref.type == "claim"
    assert contract.target_ref.id_or_text == "emitted_85a7ac5156"
    assert span_is_malformed(contract.target_ref.id_or_text) is False
    assert LONG_CLAIM not in (contract.target_ref.id_or_text or "")
    variants = (
        "Who told you that?",
        "Where did she hear that?",
        "What's your source?",
        "Did the guard tell him that?",
        "Who says?",
    )
    for text in variants:
        follow = _contract(text, session)
        assert follow.dimension == "source", text
        assert follow.discourse_ref is not None and follow.discourse_ref.id == "emitted_85a7ac5156", text
        assert follow.target_ref is not None and follow.target_ref.id_or_text == "emitted_85a7ac5156", text
        assert follow.interlocutor_id == "tavern_runner", text


def test_model_act_on_a_social_question_is_canonicalized_to_ask():
    def _act(_ctx):
        return {
            "status": "proposed",
            "api_calls": 0,
            "proposal": {
                "primary_operation": "act",
                "proposed_target_id": "gate_guard",
                "interlocutor_id": "gate_guard",
                "dimension": "content",
                "dimensions": ["content"],
                "conversational_subject": "whether travelers can pass",
            },
        }

    leave = _contract(
        "I leave the runner and ask the nearest guard whether travelers can still pass before the watch changes.",
        _focus(),
        interpreter=_act,
    )
    assert leave.operation == "ask"
    assert leave.interlocutor_id == "gate_guard"
    samples = (
        "I walk to the guard and ask if the road is open.",
        "I turn to her and ask what happened.",
        "I point at the notice and ask him what it means.",
        "I ask the merchant whether travelers have come through today.",
    )
    for text in samples:
        contract = _contract(text, _focus(), interpreter=_act)
        assert contract.operation == "ask", text


def test_genuine_acts_stay_acts():
    session = _focus()
    for text in (
        "I hand him the papers.",
        "I push the door.",
        "I follow the tracks.",
        "I pay the toll.",
    ):
        contract = _contract(text, session)
        assert contract.operation == "act", text


def test_c18_live_turns_replay_authority_and_contracts():
    turns = json.loads(C18_TURNS.read_text(encoding="utf-8"))
    assert len(turns) == 6
    by_number = {int(row["turn_number"]): row for row in turns}
    third = _verdict(by_number[3]["generation_attempt_1"])
    assert third["hard_valid"] is False
    assert "ungrounded_authoritative_rule" in third["reasons"]
    for number in (1, 2, 5):
        verdict = _verdict(by_number[number]["generation_attempt_1"])
        assert verdict["hard_valid"] is True, (number, verdict["reasons"])
    board = _verdict(by_number[4]["generation_attempt_1"])
    assert board["hard_valid"] is False
    session = _focus(
        active_claim={"id": "emitted_85a7ac5156", "label": LONG_CLAIM, "kind": "claim"},
    )
    follow = _contract(by_number[2]["player_input"], session)
    assert follow.dimension == "source"
    assert follow.target_ref.id_or_text == "emitted_85a7ac5156"
    asked = _contract(by_number[3]["player_input"], _focus(), interpreter=lambda _ctx: {
        "status": "proposed",
        "api_calls": 0,
        "proposal": {
            "primary_operation": "act",
            "proposed_target_id": "gate_guard",
            "interlocutor_id": "gate_guard",
            "dimension": "content",
        },
    })
    assert asked.operation == "ask"


def _seed(tmp_path, monkeypatch):
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
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


def _set_visible_fact(fact: str | None):
    scene = storage.load_scene("frontier_gate")
    facts = scene["scene"]["visible_facts"]
    if fact:
        facts.append(fact)
    storage._save_json(storage.scene_path("frontier_gate"), scene)


@pytest.fixture()
def chat(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    monkeypatch.setattr("game.api.call_gpt", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unpatched")))
    return TestClient(app)


def test_raw_chat_stub_authority_and_contracts(chat, monkeypatch):
    calls = {"n": 0, "misses": []}

    def fake_gpt(messages, **kwargs):
        calls["n"] += 1
        reason = str(kwargs.get("retry_reason") or "")
        user = ""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                user = str(message.get("content") or "")
                break
        if reason == "hard_invalid" or int(kwargs.get("retry_attempt") or 0) >= 1:
            return _gm_response('The guard says, "I cannot give you an hour that is settled here."')
        low = user.lower()
        if "who told you that" in low:
            return _gm_response('The runner says, "I cannot name who told me."')
        if "in the stew" in low:
            return _gm_response(
                '"The stew is barley and onion," the runner says, tugging a grey cloak against the rain.'
            )
        if "push the door" in low:
            return _gm_response("You push the door. It does not open.")
        if "rumor he heard" in low:
            return _gm_response(f'The runner says, "{RUMOR}"')
        if "still pass" in low or "what hour the gate" in low or "road is open" in low:
            return _gm_response(THIRD_BELL)
        calls["misses"].append(user[-240:])
        return _gm_response('The runner says, "I cannot add to what is already settled."')

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)

    blocked = chat.post("/api/chat", json={"text": "I ask the nearest guard whether travelers can still pass."}).json()
    blocked_text = blocked["gm_output"]["player_facing_text"]
    blocked_record = blocked["gm_output"]["metadata"]["accepted_response"]
    assert "third bell" not in blocked_text.lower(), blocked_text
    assert blocked_record["provenance"] in {PROVENANCE_REGENERATION, PROVENANCE_INITIAL}, blocked_text
    assert calls["n"] <= 2

    _set_visible_fact(GROUNDED_SCHEDULE)
    calls["n"] = 0

    def grounded_gpt(messages, **kwargs):
        calls["n"] += 1
        reason = str(kwargs.get("retry_reason") or "")
        if reason == "hard_invalid" or int(kwargs.get("retry_attempt") or 0) >= 1:
            return _gm_response(FAITHFUL_THIRD_BELL)
        return _gm_response(THIRD_BELL)

    monkeypatch.setattr("game.api.call_gpt", grounded_gpt)
    allowed = chat.post("/api/chat", json={"text": "I ask the guard what hour the gate closes."}).json()
    assert allowed["gm_output"]["player_facing_text"] == FAITHFUL_THIRD_BELL
    assert "travelers" not in allowed["gm_output"]["player_facing_text"].lower()
    assert "morning" not in allowed["gm_output"]["player_facing_text"].lower()
    assert allowed["gm_output"]["metadata"]["accepted_response"]["provenance"] == PROVENANCE_REGENERATION
    assert calls["n"] == 2

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)
    rumor = chat.post("/api/chat", json={"text": "I ask the runner what rumor he heard about the gate."}).json()
    rumor_text = rumor["gm_output"]["player_facing_text"]
    # The resolver-selected stew topic is the authorized answer. The unauthored
    # third-bell rumor must not replace it.
    assert "rumor" in rumor_text.lower(), rumor_text
    assert "third bell" not in rumor_text.lower()
    saved = storage.load_session()
    facts = " ".join(storage.load_scene("frontier_gate")["scene"]["visible_facts"]).lower()
    claim = (saved.get(DISCOURSE_FOCUS_KEY) or {}).get("active_claim") or {}
    if isinstance(claim, dict) and claim.get("label"):
        assert claim.get("epistemic_status") != "world_truth"
    assert "around the third bell" not in facts or "closes when the watch changes" in facts

    detail = chat.post("/api/chat", json={"text": "I ask the runner what is in the stew."}).json()
    assert "onion" in detail["gm_output"]["player_facing_text"].lower(), detail["gm_output"]["player_facing_text"]
    assert detail["gm_output"]["metadata"]["accepted_response"]["immutable"] is True

    follow = chat.post("/api/chat", json={"text": "Who told you that?"}).json()
    follow_contract = follow["gm_output"]["metadata"]["accepted_response"]["contract"]
    assert follow_contract["operation"] in {"ask", "unresolved"}
    focus = storage.load_session().get(DISCOURSE_FOCUS_KEY) or {}
    assert focus.get("active_interlocutor")

    approach = chat.post(
        "/api/chat",
        json={"text": "I walk to the guard and ask if the road is open."},
    ).json()
    approach_contract = (approach.get("resolution") or {}).get("metadata", {}).get("resolution_contract") or {}
    if not approach_contract:
        approach_contract = approach["gm_output"]["metadata"]["accepted_response"]["contract"]
    assert approach_contract.get("operation") == "ask"

    act = chat.post("/api/chat", json={"text": "I push the door."}).json()
    live_contract = ((act.get("resolution") or {}).get("metadata") or {}).get("resolution_contract") or {}
    assert live_contract.get("operation") == "act"
