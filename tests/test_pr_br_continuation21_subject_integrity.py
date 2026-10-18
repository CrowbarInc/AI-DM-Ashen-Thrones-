"""PR-BR Continuation 21: inspection, speaker, incidental span, and identity.

Deterministic. Stubbed /api/chat does not call a paid model.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game.api import app
from game.defaults import default_campaign, default_character, default_combat, default_conditions, default_session, default_world
from game.discourse_state import DISCOURSE_FOCUS_KEY, commit_discourse_focus, read_discourse_focus
from game.immutable_valid_response import (
    PROVENANCE_INITIAL,
    PROVENANCE_REGENERATION,
    regeneration_feedback,
    run_preserve_if_valid,
    safe_nonresolution,
    semantic_equal,
    validate_generated_response,
)
from game.incidental_entity import referential_person_nominal
from game.interaction_completion import attributed_speaker_label
from game.proposition_authority import NPC_CLAIM_KIND, classify_propositions, unauthorized_authoritative_rules
from game.resolution_contract import construct_resolution_contract
from game.response_policy_enforcement import guard_gm_output
from game import storage
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage

ROOT = Path(__file__).resolve().parents[1]
SCENE = json.loads((ROOT / "data" / "scenes" / "frontier_gate.json").read_text(encoding="utf-8"))

RUNNER = {"id": "tavern_runner", "type": "interlocutor", "label": "Tavern Runner", "aliases": ["runner", "tavern runner"], "source": "scene"}
GUARD = {"id": "guard_captain", "type": "interlocutor", "label": "Guard Captain", "aliases": ["captain", "guard", "guard captain"], "source": "scene"}
STRANGER = {"id": "refugee", "type": "interlocutor", "label": "Ragged stranger", "aliases": ["stranger", "ragged stranger"], "source": "scene"}
NOTICE = {"id": "notice_board", "type": "object", "label": "Notice board", "aliases": ["notice", "board"], "source": "scene"}
CATALOG = [RUNNER, GUARD, STRANGER, NOTICE]

C10 = (
    "I cross the mud to the townhouse and look past the sky in the polished windows, "
    "checking for a lamp, a face, or any movement behind the glass, and I read whatever "
    "mark or crest is on the shut door."
)
D3 = (
    "I walk the few dozen paces to the old crates and check the muddy ruts for fresh "
    "boot prints or drag marks, then listen toward the underbrush for whatever is moving out there."
)
C8 = (
    "I let the silence stand and look into the knot of guards and refugees their eyes just left, "
    "picking out which face they lingered on and who went still when I spoke."
)
B2 = (
    "I keep my voice low and don't take the coin back yet. "
    '"Who saw those footprints, and how long ago? Did anyone from the gate actually go look, '
    'or is this just travelers talking?"'
)
D1 = (
    "I shoulder through the rain and the crowd to the notice board and read the fresh postings "
    "on the new taxes, the curfew, and the missing patrol, looking for names, places, and how "
    "recently the ink was put up."
)
WINDOW = (
    "The bright townhouse stands above the muddy square. No lamp is lit, and no face shows "
    "at the glass. The shut door bears a carved hawk crest."
)
PRINTS = (
    "The muddy ruts hold fresh boot prints and no drag line. Beyond the crates the underbrush rustles."
)
WEAR_ONLY = "The hinges are scuffed and frayed from long use."
CAPTAIN = (
    'The guard captain narrows their eyes. "No one from the gate watch has gone to look," they say quietly.'
)
RUNNER_ANSWER = 'The tavern runner says, "Travelers mentioned the prints this morning. I did not see them myself."'
STRANGER_SPEECH = (
    'The ragged stranger shrugs. "I can\'t say who exactly. They just keep to themselves."'
)
HEAD_SHAKE = "The guard shakes his head."
ELDRIN = (
    "The notice board warns that a patrol has gone missing; the roster lists the patrol leader's "
    "name, Eldrin Voss, and the ink is from this morning."
)
GROUNDED_CORPUS = "The missing patrol leader is Eldrin Voss. He took the northwest track."

# The 16 incorrect gate contracts and whether the defect caused the manual failure.
INCORRECT_CONTRACTS = (
    {"turn": "A5", "defect": "phrase bound as a person", "manual": "PASS", "causal": False, "family": "C incidental, compensated"},
    {"turn": "A8", "defect": "inherited junk target", "manual": "PASS", "causal": False, "family": "debt"},
    {"turn": "A10", "defect": "perceive board/wear while entering the tavern", "manual": "PASS", "causal": False, "family": "debt"},
    {"turn": "B5", "defect": "i lean in bound as a person", "manual": "PASS", "causal": False, "family": "C incidental, compensated"},
    {"turn": "B9", "defect": "ask bound the ragged stranger instead of the runner", "manual": "FAIL", "causal": True, "family": "B pre-seal catalog replacement"},
    {"turn": "C2", "defect": "yard phrase bound as a person, dimension wear", "manual": "PASS", "causal": False, "family": "C incidental, retry compensated"},
    {"turn": "C4", "defect": "perceive junk target; look-plus-question lost", "manual": "PASS", "causal": False, "family": "debt"},
    {"turn": "C8", "defect": "look classified as ask; clause bound as a person", "manual": "FAIL", "causal": True, "family": "B speaker plus C extraction"},
    {"turn": "C10", "defect": "perceive district/wear", "manual": "FAIL", "causal": True, "family": "A false wear dimension"},
    {"turn": "D2", "defect": "inspect board while the player looked for the track", "manual": "PASS", "causal": False, "family": "debt"},
    {"turn": "D3", "defect": "perceive board/wear; junk interlocutor", "manual": "FAIL", "causal": True, "family": "A false wear from marks"},
    {"turn": "D5", "defect": "perceive board", "manual": "PASS", "causal": False, "family": "debt"},
    {"turn": "D6", "defect": "ask with board target and junk interlocutor", "manual": "PASS", "causal": False, "family": "debt"},
    {"turn": "D7", "defect": "brush phrase bound as a person", "manual": "FAIL", "causal": True, "family": "deferred evasive figure"},
    {"turn": "D8", "defect": "act with board target", "manual": "FAIL", "causal": True, "family": "deferred evasive figure"},
    {"turn": "D9", "defect": "inspect board while the prose inspected the figure", "manual": "PASS", "causal": False, "family": "debt"},
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
    return {
        "active_scene_id": "frontier_gate",
        "turn_counter": 4,
        DISCOURSE_FOCUS_KEY: focus,
        "bounded_improvisation": {"entries": [], "incidental_entities": []},
    }


def _contract(text, session=None):
    return construct_resolution_contract(
        player_text=text,
        session=session if session is not None else _focus(),
        scene_id="frontier_gate",
        canonical_referents=CATALOG,
        scene=SCENE,
    )


def _binding(contract):
    return contract.construction["entity_binding"]


def _ask_contract(label="Tavern Runner", ident="tavern_runner"):
    return {
        "operation": "ask",
        "raw_input": "Who saw the prints?",
        "interlocutor_id": ident,
        "discourse_ref": {"type": "interlocutor", "id": ident, "label": label},
        "construction": {"entity_binding": {"status": "bound_canonical", "label": label}},
    }


def test_dimensionless_and_dimensional_inspections_complete_on_evidence():
    door = validate_generated_response(
        "The door's lower hinge is newer than the upper two, with bright scratches around the replacement pin.",
        contract={"operation": "inspect", "raw_input": "I inspect the door."},
        player_text="I inspect the door.",
    )
    assert door["hard_valid"] is True

    wear = validate_generated_response(
        "The hinges are scuffed and the lower pin is brighter than the others.",
        contract={"operation": "inspect", "raw_input": "I examine the hinges for signs of wear."},
        player_text="I examine the hinges for signs of wear.",
    )
    assert wear["hard_valid"] is True

    sound = validate_generated_response(
        "Nothing audible comes through the door. The lane outside is quiet.",
        contract={"operation": "perceive", "raw_input": "I listen at the door."},
        player_text="I listen at the door.",
    )
    assert sound["hard_valid"] is True
    assert "interaction_incomplete" not in sound["reasons"]

    wrong = validate_generated_response(
        WEAR_ONLY,
        contract={"operation": "perceive", "raw_input": "I listen at the door.", "dimension": "wear"},
        player_text="I listen at the door.",
    )
    assert wrong["hard_valid"] is False
    assert "interaction_incomplete" in wrong["reasons"]

    use = validate_generated_response(
        "The latch lifts a bar so the door can open from this side.",
        contract={"operation": "inspect", "raw_input": "I inspect the mechanism to work out what it is used for."},
        player_text="I inspect the mechanism to work out what it is used for.",
    )
    assert use["hard_valid"] is True

    marks = validate_generated_response(
        "The crate's side is blank. No crest, letters, or carved mark.",
        contract={"operation": "inspect", "raw_input": "I look over the crate for markings."},
        player_text="I look over the crate for markings.",
    )
    assert marks["hard_valid"] is True

    nothing = safe_nonresolution(
        {"operation": "inspect", "raw_input": "I inspect the door.", "dimension": "wear"},
        player_text="I inspect the door.",
    )
    assert "wear" not in nothing.lower()
    sound_safe = safe_nonresolution(
        {"operation": "perceive", "raw_input": "I listen at the door.", "dimension": "wear"},
        player_text="I listen at the door.",
    )
    assert "sound" in sound_safe
    assert "wear" not in sound_safe


def test_gate_inspection_replays_do_not_collapse_to_wear():
    c10 = _contract(C10, _focus(active_interlocutor=None))
    assert c10.operation == "perceive"
    assert c10.dimension != "wear"
    assert "wear" not in c10.dimensions
    accepted = validate_generated_response(WINDOW, contract=c10.as_dict(), player_text=C10)
    assert accepted["hard_valid"] is True
    assert "interaction_incomplete" not in accepted["reasons"]
    stale_wear = validate_generated_response(
        "The inspection establishes no further reliable detail about the wear.",
        contract=c10.as_dict(),
        player_text=C10,
    )
    assert stale_wear["hard_valid"] is False

    d3 = _contract(D3, _focus(active_interlocutor=None))
    assert d3.operation == "perceive"
    assert d3.dimension == "sound"
    assert _binding(d3)["status"] != "bound_incidental"
    heard = validate_generated_response(PRINTS, contract=d3.as_dict(), player_text=D3)
    assert heard["hard_valid"] is True
    missed = validate_generated_response(WEAR_ONLY, contract=d3.as_dict(), player_text=D3)
    assert "interaction_incomplete" in missed["reasons"]
    fallback = safe_nonresolution(d3.as_dict(), player_text=D3)
    assert "sound" in fallback
    assert "wear" not in fallback


def test_inspection_retry_keeps_the_same_contract():
    contract = {"operation": "perceive", "raw_input": "I listen at the door.", "dimension": "sound", "contract_id": "rc-sound"}
    resolution = {"kind": "question", "metadata": {"resolution_contract": contract}}

    def _retry(note):
        assert "interaction_incomplete" in note
        assert "dimension" in note
        return {"player_facing_text": "No sound comes through the door.", "metadata": {}}

    sealed = run_preserve_if_valid(
        {"player_facing_text": WEAR_ONLY, "metadata": {}},
        regenerate=_retry,
        resolution=resolution,
        player_text="I listen at the door.",
    )
    assert sealed["metadata"]["accepted_response"]["provenance"] == PROVENANCE_REGENERATION
    assert semantic_equal(sealed["player_facing_text"], "No sound comes through the door.")
    assert sealed["metadata"]["accepted_response"]["text"] == sealed["player_facing_text"]


def test_speaker_integrity_rejects_the_wrong_npc_and_keeps_a_head_shake():
    assert "guard captain" in attributed_speaker_label(CAPTAIN).lower()
    mismatch = validate_generated_response(
        CAPTAIN,
        contract=_ask_contract(),
        player_text=B2,
        referents=CATALOG,
    )
    assert mismatch["hard_valid"] is False
    assert "wrong_interlocutor" in mismatch["reasons"]
    note = regeneration_feedback(mismatch["reasons"])
    assert "wrong speaker" in note.lower()
    assert "bound interlocutor" in note.lower()

    shake = validate_generated_response(
        HEAD_SHAKE,
        contract=_ask_contract("Guard Captain", "guard_captain"),
        player_text="Can I enter?",
        referents=CATALOG,
    )
    assert shake["hard_valid"] is True

    look = validate_generated_response(
        STRANGER_SPEECH,
        contract={"operation": "perceive", "raw_input": "I look over the courtyard."},
        player_text="I look over the courtyard.",
        referents=CATALOG,
    )
    assert look["hard_valid"] is False
    assert "unsolicited_npc_speech" in look["reasons"]

    porter = validate_generated_response(
        'The porter says, "The wagons are through."',
        contract={
            "operation": "ask",
            "raw_input": "I ask the porter whether the wagons are through.",
            "construction": {"entity_binding": {"status": "bound_incidental", "label": "porter"}},
            "discourse_ref": {"type": "interlocutor", "id": "inc_porter", "label": "porter"},
        },
        player_text="I ask the porter whether the wagons are through.",
    )
    assert porter["hard_valid"] is True


def test_b2_and_c8_replays_reject_the_unrelated_speaker():
    session = _focus()
    b2 = _contract(B2, session)
    assert b2.operation == "ask"
    assert b2.interlocutor_id == "tavern_runner"
    rejected = validate_generated_response(CAPTAIN, contract=b2.as_dict(), player_text=B2, referents=CATALOG)
    assert rejected["hard_valid"] is False
    assert "wrong_interlocutor" in rejected["reasons"]

    resolution = {"kind": "question", "metadata": {"resolution_contract": b2.as_dict()}}
    sealed = run_preserve_if_valid(
        {"player_facing_text": CAPTAIN, "metadata": {}},
        regenerate=lambda _note: {"player_facing_text": CAPTAIN, "metadata": {}},
        resolution=resolution,
        player_text=B2,
        referents=CATALOG,
    )
    assert "guard captain" not in sealed["player_facing_text"].lower()
    assert semantic_equal(
        sealed["player_facing_text"],
        sealed["metadata"]["accepted_response"]["text"],
    )

    c8 = _contract(C8, session)
    assert c8.operation == "perceive"
    assert _binding(c8).get("label") != "they lingered on"
    speech = validate_generated_response(STRANGER_SPEECH, contract=c8.as_dict(), player_text=C8, referents=CATALOG)
    assert speech["hard_valid"] is False


def test_pre_seal_catalog_grimace_does_not_replace_the_candidate():
    scene = SCENE
    text = (
        '"You\'ll want the families tied longest to this place," the ragged stranger says. '
        "Noble houses like Verevin and the Ash Cowl both play dangerous games here."
    )
    resolution = {
        "kind": "question",
        "metadata": {"resolution_contract": {"operation": "ask", "raw_input": "Then point.", "contract_id": "rc-b9"}},
    }
    guarded = guard_gm_output(
        {"player_facing_text": text, "metadata": {}},
        scene,
        "Then point. Who here has those deeper roots?",
        session={"active_scene_id": "frontier_gate"},
        resolution=resolution,
    )
    assert "grimaces" not in guarded["player_facing_text"].lower()
    assert "verevi" in guarded["player_facing_text"].lower()
    assert guarded["metadata"]["content_leak_reasons"]

    sealed = run_preserve_if_valid(
        guarded,
        regenerate=lambda _note: {
            "player_facing_text": 'The ragged stranger says, "I cannot point to a name from what is settled here."',
            "metadata": {},
        },
        resolution=resolution,
        player_text="Then point. Who here has those deeper roots?",
        scene=scene,
    )
    assert "grimaces" not in sealed["player_facing_text"].lower()
    assert sealed["metadata"]["accepted_response"]["provenance"] == PROVENANCE_REGENERATION
    assert semantic_equal(sealed["player_facing_text"], sealed["metadata"]["accepted_response"]["text"])


def test_malformed_incidental_spans_are_rejected_and_roles_remain():
    rejected = (
        "they lingered on",
        "i lean in",
        "for crate yards",
        "exact coin modest fee so i",
        "underbrush for whatever is moving out there",
        "him",
        "the patrol",
        "the rumor",
        "the price",
    )
    for span in rejected:
        assert referential_person_nominal(span) is None, span

    kept = {
        "a porter": "porter",
        "the cloth merchant": "cloth merchant",
        "the tired porter carrying two crates": "tired porter",
        "the woman sweeping the steps": "woman",
        "one of the travelers": "one of the travelers",
        "a stable hand": "stable hand",
    }
    for span, label in kept.items():
        assert referential_person_nominal(span) == label

    session = _focus()
    porter = _contract("I ask a nearby porter whether the wagons are through.", session)
    assert _binding(porter)["status"] == "bound_incidental"
    assert "porter" in str(_binding(porter)["label"])
    commit_discourse_focus(session, contract=porter.as_dict(), scene_id="frontier_gate")
    pronoun = _contract("I ask him whether the line has moved.", session)
    assert pronoun.interlocutor_id == porter.interlocutor_id
    assert _binding(pronoun)["status"] != "bound_incidental" or _binding(pronoun)["label"] == _binding(porter)["label"]
    assert read_discourse_focus(session)["active_interlocutor"]["id"] == porter.interlocutor_id

    fresh = _focus()
    clause = _contract(
        "I look toward the underbrush for whatever is moving out there.",
        fresh,
    )
    assert _binding(clause)["status"] != "bound_incidental"
    commit_discourse_focus(fresh, contract=clause.as_dict(), scene_id="frontier_gate")
    rows = (fresh.get("bounded_improvisation") or {}).get("incidental_entities") or []
    assert rows == []


def test_consequential_identity_is_contextual():
    assert unauthorized_authoritative_rules(ELDRIN)
    assert unauthorized_authoritative_rules("The missing patrol leader is Eldrin Voss.")
    assert unauthorized_authoritative_rules("Mara is the Ash Compact spy.")
    hearsay = classify_propositions("I heard the patrol leader was called Voss.")
    assert hearsay[0]["kind"] == NPC_CLAIM_KIND
    assert unauthorized_authoritative_rules("I heard the patrol leader was called Voss.") == []
    assert unauthorized_authoritative_rules('The stable hand says, "I\'m Mara."') == []
    grounded = validate_generated_response(
        "The notice names the patrol leader as Eldrin Voss.",
        contract={"operation": "inspect", "raw_input": D1},
        player_text=D1,
        authored_corpus=GROUNDED_CORPUS,
    )
    assert "ungrounded_authoritative_rule" not in grounded["reasons"]

    d1 = _contract(D1, _focus(active_interlocutor=None))
    assert d1.operation in {"inspect", "perceive"}
    leaked = validate_generated_response(ELDRIN, contract=d1.as_dict(), player_text=D1, authored_corpus="")
    assert leaked["hard_valid"] is False
    assert "ungrounded_authoritative_rule" in leaked["reasons"]


def test_incorrect_gate_contracts_are_mapped_without_a_fifth_repair():
    assert len(INCORRECT_CONTRACTS) == 16
    causal = [row for row in INCORRECT_CONTRACTS if row["causal"]]
    assert len(causal) == 6
    assert {row["turn"] for row in causal} == {"B9", "C8", "C10", "D3", "D7", "D8"}
    deferred = [row for row in causal if row["family"].startswith("deferred")]
    assert {row["turn"] for row in deferred} == {"D7", "D8"}
    repaired = [row for row in causal if row not in deferred]
    assert {row["family"].split()[0] for row in repaired} <= {"A", "B"}


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


@pytest.fixture()
def chat(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    monkeypatch.setattr("game.api.call_gpt", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unpatched")))
    return TestClient(app)


def _player_text(user: str) -> str:
    try:
        payload = json.loads(user)
    except (TypeError, ValueError, json.JSONDecodeError):
        return user
    if isinstance(payload, dict):
        return str(payload.get("player_input") or payload.get("raw_player_input") or payload.get("raw_input") or user)
    return user


def test_raw_chat_stub_covers_the_ten_boundaries(chat, monkeypatch):
    def fake_gpt(messages, **kwargs):
        user = ""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                user = str(message.get("content") or "")
                break
        blob = " ".join(
            _player_text(str(message.get("content") or ""))
            for message in messages
            if isinstance(message, dict) and message.get("role") == "user"
        ).lower()
        current = _player_text(user).lower()
        retry = str(kwargs.get("retry_reason") or "") == "hard_invalid" or int(kwargs.get("retry_attempt") or 0) >= 1
        if "listen at the door" in blob:
            if retry:
                return _gm_response("No sound comes through the door.")
            return _gm_response("The hinges are scuffed and frayed.")
        if "inspect the door" in blob:
            return _gm_response("The door's lower hinge is newer than the upper two, with bright scratches around the pin.")
        if "ask the runner" in blob:
            if retry:
                return _gm_response('The tavern runner says, "I have not seen them."')
            return _gm_response('The guard captain says, "No one went."')
        if "can i enter" in blob:
            return _gm_response("The guard shakes his head.")
        if "look over the courtyard" in blob:
            return _gm_response('The ragged stranger says, "You should leave."')
        if "nearby porter" in blob:
            return _gm_response('The porter says, "The wagons are through."')
        if "underbrush for whatever" in blob:
            return _gm_response("The brush is still. Nothing answers from it.")
        if "whose name is on the roster" in blob:
            if retry:
                return _gm_response("The notice does not give a name for the missing patrol's leader.")
            return _gm_response("The roster lists the patrol leader's name, Eldrin Voss.")
        if "heard the patrol leader" in blob:
            return _gm_response("I heard the patrol leader was called Voss, but I do not know if that is right.")
        return _gm_response("The square holds its line.")

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)

    door = chat.post("/api/chat", json={"text": "I inspect the door."}).json()
    door_text = door["gm_output"]["player_facing_text"]
    assert "newer" in door_text.lower()
    assert door["gm_output"]["metadata"]["accepted_response"]["provenance"] == PROVENANCE_INITIAL
    assert semantic_equal(door_text, door["gm_output"]["metadata"]["accepted_response"]["text"])

    listen = chat.post("/api/chat", json={"text": "I listen at the door."}).json()
    listen_text = listen["gm_output"]["player_facing_text"].lower()
    assert "sound" in listen_text
    assert "scuffed" not in listen_text
    assert listen["gm_output"]["metadata"]["accepted_response"]["provenance"] == PROVENANCE_REGENERATION

    wrong = chat.post("/api/chat", json={"text": "I ask the runner who went to look."}).json()
    wrong_text = wrong["gm_output"]["player_facing_text"].lower()
    assert "guard captain" not in wrong_text
    assert wrong["gm_output"]["metadata"]["regeneration_invoked"] is True

    shake = chat.post("/api/chat", json={"text": "I ask the guard: can I enter?"}).json()
    assert "shakes his head" in shake["gm_output"]["player_facing_text"].lower()

    look = chat.post("/api/chat", json={"text": "I look over the courtyard."}).json()
    look_text = look["gm_output"]["player_facing_text"].lower()
    assert "ragged stranger says" not in look_text

    porter = chat.post("/api/chat", json={"text": "I ask a nearby porter whether the wagons are through."}).json()
    porter_contract = porter["resolution"]["metadata"]["resolution_contract"]
    assert porter_contract["construction"]["entity_binding"]["status"] == "bound_incidental"
    assert "porter" in porter["gm_output"]["player_facing_text"].lower()

    brush = chat.post("/api/chat", json={"text": "I look toward the underbrush for whatever is moving out there."}).json()
    brush_binding = brush["resolution"]["metadata"]["resolution_contract"]["construction"]["entity_binding"]
    assert brush_binding["status"] != "bound_incidental"

    roster = chat.post("/api/chat", json={"text": "I read the notice and ask whose name is on the roster."}).json()
    roster_text = roster["gm_output"]["player_facing_text"].lower()
    assert "eldrin" not in roster_text

    rumor = chat.post("/api/chat", json={"text": "I ask what you heard the patrol leader was called."}).json()
    rumor_text = rumor["gm_output"]["player_facing_text"]
    rumor_rows = classify_propositions(rumor_text)
    assert any(row["kind"] == NPC_CLAIM_KIND for row in rumor_rows)
    assert unauthorized_authoritative_rules(rumor_text) == []
