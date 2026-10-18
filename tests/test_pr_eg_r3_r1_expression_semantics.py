"""PR-EG-R3-R1: authorized meaning, proposition identity, and answer sufficiency."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from game import api, storage
from game.conversational_continuity import (
    _best_exchange,
    continuity_directive,
    delivered_exchanges,
    recall_kind,
    record_delivered_exchange,
    supplied_clarification,
)
from game.dialogue_authority import (
    authorize_npc_disclosure,
    build_dialogue_authority,
    classify_answer_sufficiency,
    remember_dialogue_commitment,
    select_host_speech,
)
from game.expressive_dialogue import build_expression_contract, validate_expression
from game.immutable_valid_response import run_preserve_if_valid, seal_host_speech
from tests.test_pr_ef_gm_authority import raw_record, seed_scene

ROOT = Path(__file__).resolve().parents[1]
H = ROOT / "artifacts" / "pr_eg_r3_r1"
HOLDOUTS = json.loads((H / "frozen_holdouts.json").read_text(encoding="utf-8"))
FREEZE = json.loads((H / "freeze.json").read_text(encoding="utf-8"))
HISTORICAL = (
    "I prefer the evening because I find it a little easier to think "
    "when the day is winding down and everything feels calm and peaceful."
)
ROAD = "The street beyond the gate is the north road."
WATCH = "Guards watch the north gate throughout the night."


def _stub(monkeypatch, text):
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "0")
    calls = []

    def _request(contract):
        calls.append(contract)
        return {"ok": True, "sent": True, "text": text, "latency_ms": 1.0, "model": "stub",
                "usage": {"input_tokens": 11, "output_tokens": 8, "model": "stub"}}

    monkeypatch.setattr("game.expressive_dialogue.request_expression", _request)
    return calls


def _resolution(question, fact="", session=None, npc_id="sergeant_mara", name="Sergeant Mara", npc=None):
    social = dict(
        target_resolved=True, npc_id=npc_id, npc_name=name,
        reply_plan_kind="authoritative_answer_available" if fact else "genuine_uncertainty",
    )
    person = dict(npc) if isinstance(npc, dict) else None
    if fact:
        person = dict(person or {})
        person.setdefault("id", npc_id)
        person.setdefault("name", name)
        topics = [dict(item) for item in (person.get("topics") or []) if isinstance(item, dict)]
        if not any(item.get("text") == fact for item in topics):
            topics.append(dict(id="fact", text=fact, disclosure="public"))
        person["topics"] = topics
        topic = dict(id="fact", text=fact)
        topic["disclosure_authorization"] = authorize_npc_disclosure(person, topic)
        social["topic_revealed"] = topic
    social["dialogue_authority"] = build_dialogue_authority(question, npc=person, social=social, session=session)
    return dict(
        kind="social_exchange", requires_check=False, social=social,
        metadata=dict(resolution_contract=dict(operation="ask", interlocutor_id=npc_id, contract_id="r3r1", raw_input=question)),
    )


def _adopt(res, question, candidate, session):
    return run_preserve_if_valid(
        dict(player_facing_text=candidate, world_updates={"reward": 10}),
        regenerate=lambda _reason: (_ for _ in ()).throw(AssertionError("narration retry")),
        resolution=res, player_text=question, session=session,
    )


def _preference(session, question, established, npc_id="sergeant_mara", name="Sergeant Mara"):
    prior = _resolution("Do you prefer that?", session=session, npc_id=npc_id, name=name)
    remember_dialogue_commitment(session, social=prior["social"], player_text="Do you prefer that?", line=f'{name} says, "{established}"')


def test_t01_t02_authorized_preference_explanation_allows_harmless_grammar(monkeypatch):
    calls = _stub(monkeypatch, HISTORICAL)
    session = {}
    _preference(session, "Why do you prefer the evening?", "I prefer the evening.")
    question = "Why do you prefer the evening?"
    out = _adopt(_resolution(question, session=session), question, "Stranger says, \"The password is Winter.\"", session)
    audit = out["metadata"]["expression_generation"]
    meaning = audit["contract"]["permitted_meaning"]
    assert meaning["licensed_by"] == "established_preference"
    assert meaning["preference_anchor"] == "evening"
    assert meaning["external_world"] is False
    assert "everything" not in json.dumps(meaning)
    assert HISTORICAL not in json.dumps(meaning)
    assert audit["decision"] == "adopted"
    assert "everything" in out["player_facing_text"].lower()
    assert "peaceful" in out["player_facing_text"].lower()
    assert calls and calls[0]["proposition_id"]
    assert out["world_updates"] is None


def test_t03_t06_unauthorized_explanations_are_rejected(monkeypatch):
    _stub(monkeypatch, "I find the evening a little easier when things feel quiet.")
    session = {}
    _preference(session, "Why do you prefer the evening?", "I prefer the evening.")
    question = "Why do you prefer the evening?"
    res = _resolution(question, session=session)
    out = _adopt(res, question, 'Sergeant Mara says, "I prefer the evening."', session)
    contract = out["metadata"]["expression_generation"]["contract"]
    samples = {
        "T03": "I prefer the evening because the market closes early.",
        "T04": "I like the evening because the captain leaves me alone.",
        "T05": "I prefer the evening because the guards usually leave the north gate unattended.",
        "T06": "I prefer the evening and I promise you a reward.",
    }
    for label, candidate in samples.items():
        verdict = validate_expression(candidate, contract)
        assert verdict["adopt"] is False, label
        assert candidate.lower() not in out["player_facing_text"].lower()


def test_t07_t10_paraphrase_entity_alias_and_rumor():
    contract = build_expression_contract(
        player_text="Say that in simpler words.", speaker_name="Sergeant Mara", speaker_id="sergeant_mara",
        fallback_line=f'Sergeant Mara mutters, "Word is, {ROAD}"', fallback_source="delivered",
        forced_operation="faithful_paraphrase",
    )
    assert validate_expression("The road just outside the gate is called the north road.", contract)["adopt"] is True
    assert validate_expression("The road just outside the gate is called the north street.", contract)["adopt"] is False
    alias = build_expression_contract(
        player_text="Say that in simpler words.", speaker_name="Miller Os", speaker_id="miller_os",
        fallback_line='Miller Os says, "The lane beyond the mill is the harbor road."',
        fallback_source="delivered", forced_operation="faithful_paraphrase", entity_aliases=["harbour road"],
    )
    assert validate_expression("The lane past the mill is called the harbour road.", alias)["adopt"] is True
    assert validate_expression("The lane past the mill is called the ferry road.", alias)["adopt"] is False
    rumor = build_expression_contract(
        player_text="Say that in simpler words.", speaker_name="Sister Quen", speaker_id="sister_quen",
        fallback_line='Sister Quen says, "I have heard the council may own the ferry."',
        fallback_source="delivered", forced_operation="faithful_paraphrase",
    )
    assert validate_expression("I've heard the council may own the ferry.", rumor)["adopt"] is True
    assert validate_expression("The council owns the ferry.", rumor)["adopt"] is False
    assert validate_expression("Corporal Bren says the north road is outside the gate.", contract)["adopt"] is False


def test_t11_t18_proposition_identity_recall_and_ambiguity():
    session = {}
    social = dict(npc_id="sergeant_mara", npc_name="Sergeant Mara", topic_revealed=dict(id="road", text=ROAD),
                  dialogue_authority=dict(npc_id="sergeant_mara", npc_name="Sergeant Mara", subject="road"))
    first = record_delivered_exchange(session, player_text="What is the street called?", delivered_text=f'Sergeant Mara says, "Word is, {ROAD}"', social=social, turn=1)
    second = record_delivered_exchange(
        session, player_text="Say that in simpler words.",
        delivered_text='Sergeant Mara says, "The street just past the gate is called the north road."',
        social=dict(npc_id="sergeant_mara", npc_name="Sergeant Mara", proposition_id=first["proposition_id"],
                    dialogue_authority=dict(npc_id="sergeant_mara", npc_name="Sergeant Mara", proposition_id=first["proposition_id"], authorized_proposition=ROAD)),
        turn=2,
    )
    assert first["proposition_id"] == second["proposition_id"]
    assert first["delivered_text"] != second["delivered_text"]
    found = _best_exchange("What did you mean by the north road?", delivered_exchanges(session), "sergeant_mara")
    assert isinstance(found, dict)
    quoted = continuity_directive("GM, what exactly did Mara say about the road?", session=session, world={"npcs": []}, scene={})
    assert ROAD in quoted["line"]
    assert "The street just past the gate is called the north road." in quoted["line"]
    other = record_delivered_exchange(
        session, player_text="What is the other road?", delivered_text='Sergeant Mara says, "The western road is past the mill."',
        social=dict(npc_id="sergeant_mara", npc_name="Sergeant Mara", topic_revealed=dict(id="west", text="The western road is past the mill."),
                    dialogue_authority=dict(npc_id="sergeant_mara", npc_name="Sergeant Mara")),
        turn=3,
    )
    assert other["proposition_id"] != first["proposition_id"]
    assert _best_exchange("Repeat the road statement.", delivered_exchanges(session), "sergeant_mara") == "ambiguous"
    bren = record_delivered_exchange(
        session, player_text="What road?", delivered_text='Corporal Bren says, "The western road."',
        social=dict(npc_id="corporal_bren", npc_name="Corporal Bren", topic_revealed=dict(id="road", text="The western road.")),
        turn=4,
    )
    assert bren["proposition_id"] != first["proposition_id"]
    assert _best_exchange("GM, repeat what they said about the road.", delivered_exchanges(session)) == "ambiguous"
    assert recall_kind("What exactly did Mara say?") == "exact"
    assert recall_kind("Can Mara say that another way?") == "restatement"
    assert recall_kind("What did Mara say about the road?") == "subject"
    assert recall_kind("What did Mara mean by that?") == "explanation"
    assert "Which earlier remark" in supplied_clarification("Repeat the road statement.", session, "sergeant_mara", "Sergeant Mara")


def test_t19_t23_answer_sufficiency_and_refusal(monkeypatch):
    assert classify_answer_sufficiency("Do the guards watch the north gate at night?", WATCH) == "directly_answers"
    assert classify_answer_sufficiency("Is the north gate ever left unattended?", WATCH) == "partially_informs"
    assert classify_answer_sufficiency("Who made the lantern?", WATCH) == "does_not_answer"
    assert classify_answer_sufficiency("Who made the lantern?", "") == "unknown"
    npc = dict(id="sergeant_mara", name="Sergeant Mara", topics=[dict(id="watch", text=WATCH), dict(id="road", text=ROAD)])
    partial_q = "Is the north gate ever left unattended?"
    authority = build_dialogue_authority(partial_q, npc=npc, social=dict(npc_id="sergeant_mara", npc_name="Sergeant Mara", target_resolved=True))
    assert authority["answer_sufficiency"] == "partially_informs"
    assert authority["proposition_id"] == "topic:sergeant_mara:watch"
    line, source = select_host_speech(_resolution(partial_q, npc=npc) , player_text=partial_q)
    assert "throughout the night" in line.lower()
    assert "couldn't say" in line.lower()
    assert "never" not in line.lower()
    assert line.lower().strip().endswith('unattended."') or "unattended" in line.lower()
    direct = build_dialogue_authority("Do the guards watch the north gate at night?", social=dict(npc_id="sergeant_mara", npc_name="Sergeant Mara", topic_revealed=dict(id="watch", text=WATCH)))
    assert direct["answer_sufficiency"] == "directly_answers"
    unknown = build_dialogue_authority("Who made the lantern?", npc=npc, social=dict(npc_id="sergeant_mara", npc_name="Sergeant Mara"))
    assert unknown["answer_sufficiency"] == "unknown"
    assert "throughout the night" not in unknown["player_line"].lower()
    _stub(monkeypatch, "I can't promise you a reward.")
    refused = _adopt(_resolution("Promise me a reward if I help you."), "Promise me a reward if I help you.", "I will pay you ten silver.", {})
    assert "promise" in refused["player_facing_text"].lower()
    assert "silver" not in refused["player_facing_text"].lower()


def test_t24_t28_mixed_rejection_persistence_and_no_canonical_mutation(monkeypatch):
    calls = _stub(monkeypatch, "I find the evening peaceful because the guards leave the gate.")
    session = {}
    _preference(session, "Why do you prefer the evening?", "I prefer the evening.")
    question = "Why do you prefer the evening?"
    before = copy.deepcopy(session)
    out = _adopt(_resolution(question, session=session), question, 'Sergeant Mara says, "I find the evening peaceful because the guards leave the gate."', session)
    assert out["metadata"]["expression_generation"]["decision"] == "rejected"
    assert "guards" not in out["player_facing_text"].lower()
    assert out["world_updates"] is None
    sealed = seal_host_speech(
        {"player_facing_text": out["player_facing_text"]}, text=out["player_facing_text"], source="host",
        speaker_id="sergeant_mara", speaker_name="Sergeant Mara", resolution=out.get("resolution") or _resolution(question, session=session),
        player_text=question,
    )
    from game.expressive_dialogue import attach_expression_audit
    attach_expression_audit(sealed, out["metadata"]["expression_generation"])
    row = record_delivered_exchange(session, player_text=question, delivered_text=sealed["player_facing_text"], social=sealed.get("social") or {"npc_id": "sergeant_mara", "npc_name": "Sergeant Mara"}, adoption=sealed["metadata"]["accepted_response"])
    blob = json.dumps(session)
    assert "guards leave" not in blob
    assert calls[0]["candidate"] if False else out["metadata"]["expression_generation"]["candidate"] not in row["delivered_text"]
    assert session["conversational_context"]["dialogue_commitments"] == before.get("conversational_context", {}).get("dialogue_commitments", session["conversational_context"].get("dialogue_commitments"))
    storage_blob = json.loads(json.dumps(session))
    assert storage_blob["conversational_context"]["delivered_exchanges"][-1]["delivered_text"] == row["delivered_text"]
    assert out["metadata"]["expression_generation"]["calls"] == 1


def test_t29_t30_relevant_modules_keep_single_expression_call(monkeypatch):
    calls = _stub(monkeypatch, "The road just outside the gate is called the north road.")
    line = f'Sergeant Mara mutters, "Word is, {ROAD}"'
    decision = SimpleNamespace(reason="repeat_delivered_statement", communication_owner="NPC", proposed_target="sergeant_mara", context_references=["name:Sergeant Mara", "proposition_id=topic:sergeant_mara:road"])
    from game.expressive_dialogue import maybe_reword_continuity_line
    got, audit = maybe_reword_continuity_line({"player_facing_text": line}, decision, player_text="Say that in simpler words.")
    assert "north road" in got.lower()
    assert audit["calls"] == 1
    assert audit["contract"]["proposition_id"] == "topic:sergeant_mara:road"
    assert len(calls) == 1


def test_degree_grammar_can_modify_an_authorized_feeling(monkeypatch):
    _stub(monkeypatch, "I prefer the evening because it feels calmer and more peaceful to me.")
    session = {}
    _preference(session, "Why do you prefer the evening?", "I prefer the evening.")
    question = "Why do you prefer the evening?"
    out = _adopt(_resolution(question, session=session), question, "The password is Winter.", session)
    assert out["metadata"]["expression_generation"]["decision"] == "adopted"
    assert "more peaceful" in out["player_facing_text"].lower()
    contract = out["metadata"]["expression_generation"]["contract"]
    assert validate_expression(
        "I prefer the evening because it feels calmer and the world seems to slow down.",
        contract,
    )["adopt"] is False


def test_unestablished_preference_does_not_invent_a_premise(monkeypatch):
    calls = _stub(monkeypatch, HISTORICAL)
    contract = build_expression_contract(
        player_text="Why does the watch wear on you?", speaker_name="Sergeant Mara", speaker_id="sergeant_mara",
        fallback_line='Sergeant Mara says, "The watch wears on me. That is all."',
        fallback_source="conversational_continuity.bounded_personal_line",
    )
    assert contract is None
    assert calls == []


def test_partial_fact_reaches_the_player_without_topic_promotion(tmp_path, monkeypatch):
    from game.social import _next_topic_to_reveal, resolve_social_action
    seed_scene(tmp_path, monkeypatch)
    world = storage.load_world()
    session = storage.load_session()
    scene = storage.load_active_scene()
    npc = next(row for row in world["npcs"] if row["id"] == "sergeant_mara")
    npc.setdefault("topics", []).append(dict(id="night_watch", text=WATCH))
    storage.save_world(world)
    assert _next_topic_to_reveal(npc, {}, player_text="Is the north gate ever left unattended?") is None
    action = dict(id="ask", label="Ask Mara", type="question", prompt="Ask Mara", target_id="sergeant_mara")
    question = "Is the north gate ever left unattended?"
    first = resolve_social_action(scene, session, world, action, raw_player_text=question)
    assert first["social"]["topic_revealed"] is None
    out = _adopt(first, question, "The gate is never unattended.", session)
    text = out["player_facing_text"].lower()
    assert "throughout the night" in text
    assert "couldn't say" in text
    assert "never unattended" not in text
    assert "night_watch" not in (session.get("npc_runtime", {}).get("sergeant_mara", {}).get("revealed_topics") or [])
    assert out["world_updates"] is None


@pytest.mark.parametrize("case", HOLDOUTS, ids=lambda case: case["id"])
def test_frozen_holdout(case, monkeypatch):
    assert hashlib.sha256((H / "frozen_holdouts.json").read_bytes()).hexdigest() == FREEZE["sha256"]
    if case["kind"] == "characterization":
        calls = _stub(monkeypatch, case["candidate"])
        session = {}
        _preference(session, case["question"], case["established"], case["npc_id"], case["name"])
        out = _adopt(_resolution(case["question"], session=session, npc_id=case["npc_id"], name=case["name"]), case["question"], "The password is Winter.", session)
        text = out["player_facing_text"]
        audit = out["metadata"]["expression_generation"]
        assert (audit["decision"] == "adopted") is (case["expect"] == "adopt")
        if case["expect"] != "adopt":
            assert case["candidate"].lower() not in text.lower()
        assert calls
    elif case["kind"] == "paraphrase":
        _stub(monkeypatch, case["candidate"])
        from game.expressive_dialogue import maybe_reword_continuity_line
        decision = SimpleNamespace(reason="repeat_delivered_statement", communication_owner="NPC", proposed_target=case["npc_id"], context_references=[f"name:{case['name']}"])
        text, audit = maybe_reword_continuity_line({"player_facing_text": case["fallback"]}, decision, player_text=case["question"])
        assert (audit["decision"] == "adopted") is (case["expect"] == "adopt")
    elif case["kind"] == "alias":
        contract = build_expression_contract(
            player_text=case["question"], speaker_name=case["name"], speaker_id=case["npc_id"],
            fallback_line=f'{case["name"]} says, "{case["proposition"]}"', fallback_source="delivered",
            forced_operation="faithful_paraphrase", entity_aliases=case["aliases"],
        )
        verdict = validate_expression(case["candidate"], contract)
        text = case["candidate"] if verdict["adopt"] else case["proposition"]
        assert verdict["adopt"] is (case["expect"] == "adopt")
    elif case["kind"] == "rumor":
        contract = build_expression_contract(
            player_text=case["question"], speaker_name=case["name"], speaker_id=case["npc_id"],
            fallback_line=f'{case["name"]} says, "{case["proposition"]}"', fallback_source="delivered",
            forced_operation="faithful_paraphrase",
        )
        verdict = validate_expression(case["candidate"], contract)
        text = case["proposition"]
        assert verdict["adopt"] is False
    elif case["kind"] == "partial":
        npc = dict(id=case["npc_id"], name=case["name"], topics=[dict(id="watch", text=case["fact"])])
        authority = build_dialogue_authority(case["question"], npc=npc, social=dict(npc_id=case["npc_id"], npc_name=case["name"], target_resolved=True))
        text = authority["player_line"]
        assert authority["answer_sufficiency"] == "partially_informs"
    elif case["kind"] in {"equivalent", "distinct"}:
        session = {}
        ids = []
        for index, statement in enumerate(case["statements"], 1):
            topic = "same" if case["kind"] == "equivalent" else f"topic_{index}"
            social = dict(npc_id=case["npc_id"], npc_name=case["name"], topic_revealed=dict(id=topic, text=statement),
                          dialogue_authority=dict(npc_id=case["npc_id"], npc_name=case["name"]))
            if case["kind"] == "equivalent" and ids:
                social["proposition_id"] = ids[0]
                social["dialogue_authority"]["proposition_id"] = ids[0]
            row = record_delivered_exchange(session, player_text=case["question"], delivered_text=f'{case["name"]} says, "{statement}"', social=social, turn=index)
            ids.append(row["proposition_id"])
        found = _best_exchange(case["question"], delivered_exchanges(session), case["npc_id"])
        if case["expect"] == "ambiguous":
            text = supplied_clarification(case["question"], session, case["npc_id"], case["name"])
            assert found == "ambiguous"
        else:
            assert isinstance(found, dict)
            assert ids[0] == ids[1]
            text = supplied_clarification(case["question"], session, case["npc_id"], case["name"])
    else:
        session = {}
        record_delivered_exchange(
            session, player_text="What about the gate?", delivered_text=f'{case["name"]} says, "{case["statement"]}"',
            social=dict(npc_id=case["npc_id"], npc_name=case["name"], topic_revealed=dict(id="gate", text=case["statement"]),
                        dialogue_authority=dict(npc_id=case["npc_id"], npc_name=case["name"], subject="gate")),
            turn=1,
        )
        directive = continuity_directive(case["question"], session=session, world={"npcs": []}, scene={})
        text = directive["line"]
    for bit in case["required"]:
        assert bit.lower() in text.lower()
    for bit in case["forbidden"]:
        assert bit.lower() not in text.lower()


def test_production_chat_delivers_characterization(tmp_path, monkeypatch):
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
        lambda contract: {"ok": True, "sent": True, "text": HISTORICAL, "latency_ms": 2, "model": "stub",
                          "usage": {"input_tokens": 20, "output_tokens": 18, "model": "stub"}},
    )
    client = TestClient(api.app)

    def post(text):
        return client.post("/api/chat?ui_mode=player", json={"text": text, "ui_mode": "player"}).json()

    post("I ask Sergeant Mara, do you prefer the morning or the evening?")
    why = post("Why do you prefer the evening?")
    spoken = why["gm_output"]["player_facing_text"]
    accepted = why["gm_output"]["metadata"]["accepted_response"]
    assert "everything" in spoken.lower()
    assert "peaceful" in spoken.lower()
    assert spoken == accepted["text"]
    assert accepted["expression_adoption"] == "ADOPTED_GENERATED_EXPRESSION"
    assert "guard" not in spoken.lower()
    saved = storage.load_session()
    assert saved["conversational_context"]["delivered_exchanges"][-1]["delivered_text"] == spoken
    storage.save_session(copy.deepcopy(saved))
    assert storage.load_session()["conversational_context"] == saved["conversational_context"]
