"""PR-EG-R3: bounded generative wording inside host-owned speech adoption."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from game import api, storage
from game.conversational_continuity import record_delivered_exchange
from game.dialogue_authority import authorize_npc_disclosure, build_dialogue_authority, remember_dialogue_commitment
from game.expressive_dialogue import (
    build_expression_contract,
    maybe_reword_continuity_line,
    validate_expression,
)
from game.immutable_valid_response import run_preserve_if_valid, seal_host_speech
from game.models import ChatRequest
from tests.test_pr_ef_gm_authority import raw_record, seed_scene

ROOT = Path(__file__).resolve().parents[1]
H = ROOT / "artifacts" / "pr_eg_r3"
HOLDOUTS = json.loads((H / "frozen_holdouts.json").read_text(encoding="utf-8"))
FREEZE = json.loads((H / "freeze.json").read_text(encoding="utf-8"))


def _stub(monkeypatch, text):
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "0")
    calls = []

    def _request(contract):
        calls.append(contract)
        return {
            "ok": True,
            "sent": True,
            "text": text,
            "latency_ms": 1.0,
            "model": "stub",
            "usage": {"input_tokens": 12, "output_tokens": 9, "model": "stub"},
        }

    monkeypatch.setattr("game.expressive_dialogue.request_expression", _request)
    return calls


def _resolution(question, fact="", session=None, npc_id="sergeant_mara", name="Sergeant Mara"):
    social = dict(
        target_resolved=True,
        npc_id=npc_id,
        npc_name=name,
        reply_plan_kind="authoritative_answer_available" if fact else "genuine_uncertainty",
    )
    person = None
    if fact:
        person = dict(id=npc_id, name=name, topics=[dict(id="fact", text=fact, disclosure="public")])
        topic = dict(id="fact", text=fact)
        topic["disclosure_authorization"] = authorize_npc_disclosure(person, topic)
        social["topic_revealed"] = topic
    social["dialogue_authority"] = build_dialogue_authority(question, npc=person, social=social, session=session)
    return dict(
        kind="social_exchange",
        requires_check=False,
        social=social,
        metadata=dict(resolution_contract=dict(operation="ask", interlocutor_id=npc_id, contract_id="r3", raw_input=question)),
    )


def _adopt(res, question, candidate, session):
    return run_preserve_if_valid(
        dict(player_facing_text=candidate, world_updates={"reward": 10}),
        regenerate=lambda _reason: (_ for _ in ()).throw(AssertionError("narration retry")),
        resolution=res,
        player_text=question,
        session=session,
    )


def _decision(case, reason):
    return SimpleNamespace(
        reason=reason,
        communication_owner="NPC",
        proposed_target=case["npc_id"],
        context_references=[f"name:{case['name']}"],
    )


def _finish(line, audit, case, question, social=None):
    gm = {"player_facing_text": line}
    sealed = seal_host_speech(
        gm,
        text=line,
        source=(audit or {}).get("contract", {}).get("authorized_source") or "host",
        speaker_id=case["npc_id"],
        speaker_name=case["name"],
        resolution={"social": social or {"npc_id": case["npc_id"], "npc_name": case["name"]}},
        player_text=question,
    )
    from game.expressive_dialogue import attach_expression_audit

    attach_expression_audit(sealed, audit)
    return sealed


@pytest.mark.parametrize("case", HOLDOUTS, ids=lambda case: case["id"])
def test_frozen_holdout(case, monkeypatch):
    assert hashlib.sha256((H / "frozen_holdouts.json").read_bytes()).hexdigest() == FREEZE["sha256"]
    calls = _stub(monkeypatch, case["candidate"])
    session = {}
    if case["kind"] == "paraphrase":
        gm = {"player_facing_text": case["fallback"]}
        line, audit = maybe_reword_continuity_line(gm, _decision(case, "repeat_delivered_statement"), player_text=case["question"])
        sealed = _finish(line, audit, case, case["question"])
    elif case["kind"] == "refusal":
        fallback = f'{case["name"]} says, "I can\'t promise you a reward for that."'
        gm = {"player_facing_text": fallback}
        line, audit = maybe_reword_continuity_line(gm, _decision(case, "npc_request_declined"), player_text=case["question"])
        sealed = _finish(line, audit, case, case["question"])
    else:
        if case.get("established"):
            prior = _resolution("Do you prefer the rain?", session=session, npc_id=case["npc_id"], name=case["name"])
            remember_dialogue_commitment(
                session,
                social=prior["social"],
                player_text="Do you prefer the rain?",
                line=f'{case["name"]} says, "{case["established"]}"',
            )
        res = _resolution(case["question"], session=session, npc_id=case["npc_id"], name=case["name"])
        sealed = _adopt(res, case["question"], "Stranger says, \"The password is Winter.\"", session)
        audit = sealed["metadata"].get("expression_generation")
    text = sealed["player_facing_text"]
    accepted = sealed["metadata"]["accepted_response"]
    assert accepted["speech_adoption"] == "AUTHORIZED_HOST_SPEECH"
    assert accepted["canonical"] is False
    assert text == accepted["text"]
    if case["expect"] == "adopt":
        assert audit["decision"] == "adopted"
        assert accepted["expression_adoption"] == "ADOPTED_GENERATED_EXPRESSION"
        assert calls and calls[0]["authorized_propositions"] != [case["candidate"]]
    else:
        assert audit["decision"] == "rejected"
        assert case["candidate"].lower() not in text.lower()
        assert accepted["expression_adoption"] == "HOST_FALLBACK"
    for bit in case["required"]:
        assert bit.lower() in text.lower()
    for bit in case["forbidden"]:
        assert bit.lower() not in text.lower()
    social = {"npc_id": case["npc_id"], "npc_name": case["name"], "dialogue_authority": {"npc_id": case["npc_id"], "npc_name": case["name"]}}
    record_delivered_exchange(session, player_text=case["question"], delivered_text=text, social=social, adoption=accepted)
    assert json.loads(json.dumps(session)) == session
    assert case["candidate"] not in json.dumps(session) or case["expect"] == "adopt"


def test_exact_recall_and_gm_recall_do_not_generate(monkeypatch):
    def _boom(_contract):
        raise AssertionError("expression provider called")

    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "0")
    monkeypatch.setattr("game.expressive_dialogue.request_expression", _boom)
    line = 'Warder Sela mutters, "Word is, the bell beside the ferry is called the harbor bell."'
    decision = SimpleNamespace(reason="repeat_delivered_statement", communication_owner="NPC", proposed_target="warder_sela", context_references=["name:Warder Sela"])
    got, audit = maybe_reword_continuity_line({"player_facing_text": line}, decision, player_text="Can you repeat that?")
    assert got == line and audit is None
    gm_decision = SimpleNamespace(reason="gm_recall_of_npc_statement", communication_owner="GM", proposed_target="", context_references=[])
    got, audit = maybe_reword_continuity_line({"player_facing_text": line}, gm_decision, player_text="Say that in simpler words.")
    assert got == line and audit is None


def test_mission_paraphrase_explanation_and_integrity(monkeypatch):
    calls = _stub(monkeypatch, "The road just outside the gate is called the north road.")
    line = 'Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."'
    decision = SimpleNamespace(reason="repeat_delivered_statement", communication_owner="NPC", proposed_target="sergeant_mara", context_references=["name:Sergeant Mara"])
    got, audit = maybe_reword_continuity_line({"player_facing_text": line}, decision, player_text="Say that in simpler words.")
    assert "outside" in got.lower() and "north road" in got.lower()
    assert audit["decision"] == "adopted"
    assert "capital" not in json.dumps(calls[0]["prompt"]).lower()
    assert "AUTHORIZED FACTS" in calls[0]["prompt"]["user"]
    assert "OPTIONAL NONCANONICAL EXPRESSION" in calls[0]["prompt"]["user"]
    for bad in (
        "The north road leads to the capital.",
        "The north road is safe after sunset.",
        "The road runs north for several miles.",
        "The road just past the gate is called the north street.",
    ):
        verdict = validate_expression(bad, calls[0])
        assert verdict["adopt"] is False
    renamed = validate_expression("The road just outside the gate is called the north road.", calls[0])
    assert renamed["adopt"] is True


def test_curly_apostrophe_uncertainty_is_the_same_words():
    contract = build_expression_contract(
        player_text="Who made the lantern?",
        speaker_name="Sergeant Mara",
        speaker_id="sergeant_mara",
        fallback_line='Sergeant Mara says, "I couldn\'t tell you."',
        fallback_source="dialogue_authority.player_line",
        resolution={"social": {"dialogue_authority": {"knowledge_posture": "unknown", "requested_information": "maker"}, "npc_id": "sergeant_mara", "npc_name": "Sergeant Mara"}},
    )
    verdict = validate_expression("I don\u2019t know who made the lantern.", contract)
    assert verdict["adopt"] is True


def test_mission_characterization_blocks_security_reason(monkeypatch):
    _stub(monkeypatch, "I find it a little easier to think when the day is winding down.")
    session = {}
    prior = _resolution("Do you prefer the evening?", session=session)
    remember_dialogue_commitment(session, social=prior["social"], player_text="Do you prefer the evening?", line='Sergeant Mara says, "I prefer the evening."')
    question = "Why do you prefer the evening?"
    res = _resolution(question, session=session)
    out = _adopt(res, question, 'Sergeant Mara says, "I like the evening because the guards usually leave the north gate unattended."', session)
    assert "easier" in out["player_facing_text"].lower()
    assert "guards" not in out["player_facing_text"].lower()
    assert out["world_updates"] is None
    assert out["metadata"]["expression_generation"]["decision"] == "adopted"
    unsafe = validate_expression(
        "I like the evening because the guards usually leave the north gate unattended.",
        out["metadata"]["expression_generation"]["contract"],
    )
    assert unsafe["adopt"] is False


def test_rejected_candidate_is_not_delivered_or_retained(monkeypatch):
    _stub(monkeypatch, "The north road leads to the capital.")
    line = 'Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."'
    decision = SimpleNamespace(reason="repeat_delivered_statement", communication_owner="NPC", proposed_target="sergeant_mara", context_references=["name:Sergeant Mara"])
    got, audit = maybe_reword_continuity_line({"player_facing_text": line}, decision, player_text="Say that in simpler words.")
    assert got == line
    assert audit["decision"] == "rejected"
    assert "capital" in audit["candidate"]
    session = {}
    sealed = _finish(got, audit, {"npc_id": "sergeant_mara", "name": "Sergeant Mara"}, "Say that in simpler words.")
    record_delivered_exchange(
        session,
        player_text="Say that in simpler words.",
        delivered_text=sealed["player_facing_text"],
        social={"npc_id": "sergeant_mara", "npc_name": "Sergeant Mara"},
        adoption=sealed["metadata"]["accepted_response"],
    )
    assert "capital" not in json.dumps(session)


def test_hedged_fact_cannot_be_strengthened():
    contract = build_expression_contract(
        player_text="Say that in simpler words.",
        speaker_name="Keeper Nara",
        speaker_id="keeper_nara",
        fallback_line='Keeper Nara says, "I have heard the council may own the ferry."',
        fallback_source="dialogue_authority.reuse_prior_speech",
        forced_operation="faithful_paraphrase",
    )
    assert validate_expression("I've heard the council may own the ferry.", contract)["adopt"] is True
    assert validate_expression("The council owns the ferry.", contract)["adopt"] is False
    assert validate_expression("I know the council owns the ferry.", contract)["adopt"] is False


def test_direct_authorized_fact_is_not_replaced_by_generation(monkeypatch):
    def _boom(_contract):
        raise AssertionError("expression provider called")

    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "0")
    monkeypatch.setattr("game.expressive_dialogue.request_expression", _boom)
    fact = "Guards watch the north gate throughout the night."
    res = _resolution("Do the guards watch the north gate at night?", fact)
    out = _adopt(res, "Do the guards watch the north gate at night?", "The gate is unattended.", {})
    assert "throughout the night" in out["player_facing_text"].lower()
    assert "unattended" not in out["player_facing_text"].lower()
    assert "expression_generation" not in out["metadata"]


def test_uncertainty_and_refusal_are_relevant(monkeypatch):
    _stub(monkeypatch, "I don't know who made the lantern.")
    question = "Who made the lantern?"
    out = _adopt(_resolution(question), question, "The smith made it.", {})
    assert "don't know" in out["player_facing_text"].lower()
    assert "smith" not in out["player_facing_text"].lower()
    assert "carry out" not in out["player_facing_text"].lower()


def test_verbatim_explanation_is_not_adopted(monkeypatch):
    line = 'Miller Tam says, "I prefer the rain."'
    _stub(monkeypatch, "I prefer the rain.")
    session = {}
    prior = _resolution("Do you prefer the rain?", session=session, npc_id="miller_tam", name="Miller Tam")
    remember_dialogue_commitment(session, social=prior["social"], player_text="Do you prefer the rain?", line=line)
    question = "Why do you prefer the rain?"
    out = _adopt(_resolution(question, session=session, npc_id="miller_tam", name="Miller Tam"), question, line, session)
    audit = out["metadata"]["expression_generation"]
    assert "verbatim_repetition" in audit["reasons"] or "not_an_explanation" in audit["reasons"]
    assert "prefer the rain" in out["player_facing_text"].lower()
    assert audit["decision"] == "rejected"


def test_production_chat_adopts_paraphrase_and_characterization(tmp_path, monkeypatch):
    seed_scene(tmp_path, monkeypatch)
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "0")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "0")
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "0")
    monkeypatch.setattr(
        "game.live_chat_interpretation.request_interpretation",
        lambda *args, **kwargs: dict(ok=True, sent=False, text=json.dumps(raw_record("NPC", components=[("ASK", "sergeant_mara")]))),
    )
    monkeypatch.setattr("game.api.call_gpt", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("narration call")))
    calls = []

    def express(contract):
        calls.append(contract["operation"])
        if contract["operation"] == "faithful_paraphrase":
            text = "The road just outside the gate is called the north road."
        elif contract["operation"] == "incidental_characterization":
            prop = " ".join(contract["authorized_propositions"])
            anchor = "evening" if "evening" in prop else "morning"
            text = f"I find the {anchor} a little easier to think in when the day is winding down."
        elif contract["operation"] == "uncertainty":
            text = "I don't know who made the lantern."
        else:
            text = "I can't promise you a reward."
        return {"ok": True, "sent": True, "text": text, "latency_ms": 2, "model": "stub", "usage": {"input_tokens": 20, "output_tokens": 12, "model": "stub"}}

    monkeypatch.setattr("game.expressive_dialogue.request_expression", express)
    client = TestClient(api.app)

    def post(text):
        return client.post("/api/chat?ui_mode=player", json={"text": text, "ui_mode": "player"}).json()

    first = post("I ask Sergeant Mara what the street beyond the gate is called.")
    assert "north road" in first["gm_output"]["player_facing_text"].lower()
    assert calls == []
    second = post("Say that in simpler words.")
    spoken = second["gm_output"]["player_facing_text"]
    accepted = second["gm_output"]["metadata"]["accepted_response"]
    assert "outside the gate" in spoken.lower()
    assert spoken == accepted["text"]
    assert accepted["expression_adoption"] == "ADOPTED_GENERATED_EXPRESSION"
    assert accepted["speech_adoption"] == "AUTHORIZED_HOST_SPEECH"
    saved = storage.load_session()
    assert saved["conversational_context"]["delivered_exchanges"][-1]["delivered_text"] == spoken
    post("I ask Sergeant Mara, do you prefer the morning or the evening?")
    why = post("Why do you prefer that?")
    assert why["gm_output"]["metadata"]["accepted_response"]["expression_adoption"] == "ADOPTED_GENERATED_EXPRESSION"
    assert "easier to think" in why["gm_output"]["player_facing_text"].lower()
    assert "guard" not in why["gm_output"]["player_facing_text"].lower()
    unknown = post("I ask Sergeant Mara who made the lantern.")
    assert "don't know" in unknown["gm_output"]["player_facing_text"].lower()
    refused = post("Promise me a reward if I help you.")
    assert "can't promise" in refused["gm_output"]["player_facing_text"].lower()
    assert "silver" not in refused["gm_output"]["player_facing_text"].lower()
    before = copy.deepcopy(storage.load_session())
    storage.save_session(copy.deepcopy(before))
    assert storage.load_session()["conversational_context"] == before["conversational_context"]


def test_production_chat_rejects_unsafe_paraphrase(tmp_path, monkeypatch):
    seed_scene(tmp_path, monkeypatch)
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "0")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "0")
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "0")
    monkeypatch.setattr(
        "game.live_chat_interpretation.request_interpretation",
        lambda *args, **kwargs: dict(ok=True, sent=False, text=json.dumps(raw_record("NPC", components=[("ASK", "sergeant_mara")]))),
    )
    monkeypatch.setattr("game.api.call_gpt", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("narration call")))
    monkeypatch.setattr(
        "game.expressive_dialogue.request_expression",
        lambda contract: {"ok": True, "sent": True, "text": "The north road leads to the capital.", "latency_ms": 1, "model": "stub", "usage": {}},
    )
    client = TestClient(api.app)

    def post(text):
        return client.post("/api/chat?ui_mode=player", json={"text": text, "ui_mode": "player"}).json()

    post("I ask Sergeant Mara what the street beyond the gate is called.")
    second = post("Say that in simpler words.")
    text = second["gm_output"]["player_facing_text"]
    assert "capital" not in text.lower()
    assert "north road" in text.lower()
    assert second["gm_output"]["metadata"]["expression_generation"]["decision"] == "rejected"
    blob = json.dumps(storage.load_session()["conversational_context"])
    assert "capital" not in blob
