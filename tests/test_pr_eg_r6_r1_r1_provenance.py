"""PR-EG-R6-R1-R1 authorization provenance and legacy compatibility."""
import copy
import json

import pytest

from game.clues import apply_socially_revealed_leads
from game.conversational_continuity import (
    find_reusable_commitment,
    record_delivered_exchange,
    supplied_clarification,
)
from game.defaults import default_session
from game.dialogue_authority import (
    CATEGORY_BOUNDED,
    CATEGORY_HISTORY,
    CATEGORY_HOST,
    CATEGORY_WORLD,
    POLICY_VERSION,
    authorize_npc_disclosure,
    commitment_disclosure_permitted,
    historical_disclosure_permitted,
    select_host_speech,
)
from game.immutable_valid_response import adopt_host_speech, seal_host_speech, verify_delivery_record
from game.unified_semantic_planning import deterministic_semantic_proposal, plan_proposer
from tests.test_pr_eg_r6_unified_semantic_planning import _ask, _world

SECRET = "The ash cowl password is sword."
PUBLIC = "The harbor bell is called the harbor bell."
RUMOR = "Some say the mill is haunted."
PREFERENCE = 'Mara says, "I prefer the evening."'


def _npc(topics):
    return {"id": "mara", "name": "Mara", "topics": topics}


def _resolution(text, topic=None, *, player="What is that?"):
    social = {
        "target_resolved": True,
        "npc_id": "mara",
        "npc_name": "Mara",
        "reply_plan_kind": "authoritative_answer_available" if topic else "genuine_uncertainty",
    }
    if topic:
        social["topic_revealed"] = topic
    return {
        "kind": "social_exchange",
        "requires_check": False,
        "social": social,
        "metadata": {"resolution_contract": {"operation": "ask", "interlocutor_id": "mara", "raw_input": player}},
    }


def _sealed(line, topic=None, world=None, player="What is that?"):
    """Seal one candidate directly so the provenance gate is what the test observes."""
    return seal_host_speech(
        {"player_facing_text": line},
        text=line,
        source="test.candidate",
        speaker_id="mara",
        speaker_name="Mara",
        resolution=_resolution(line, topic, player=player),
        player_text=player,
        world=world,
    )


def _provenance(gm):
    return gm["metadata"]["accepted_response"]["authorization_provenance"]


def test_t01_world_source_authorized_disclosure():
    person = _npc([{"id": "bell", "text": PUBLIC, "disclosure": "public"}])
    topic = {"id": "bell", "text": PUBLIC, "disclosure_authorization": authorize_npc_disclosure(person, person["topics"][0])}
    gm = _sealed(f'Mara says, "{PUBLIC}"', topic, {"npcs": [person]})
    assert PUBLIC.lower().rstrip(".") in gm["player_facing_text"].lower()
    provenance = _provenance(gm)
    assert provenance["authority_category"] == CATEGORY_WORLD
    assert provenance["validation"] == "authorized"
    assert provenance["policy_version"] == POLICY_VERSION
    assert verify_delivery_record(gm["metadata"]["accepted_response"])


def test_t02_world_source_restricted_disclosure():
    person = _npc([{"id": "password", "text": SECRET, "disclosure": "secret"}])
    topic = {"id": "password", "text": SECRET}
    gm = _sealed(f'Mara says, "{SECRET}"', topic, {"npcs": [person]}, player="What is the password?")
    assert "sword" not in gm["player_facing_text"].lower()
    assert _provenance(gm)["validation"] == "source_or_policy_denied"


def test_t03_missing_world_source_fails_closed():
    topic = {"id": "invented", "text": "The patrol changes every hour at the east post."}
    gm = _sealed(f'Mara says, "{topic["text"]}"', topic, {"npcs": [_npc([])]})
    assert "patrol" not in gm["player_facing_text"].lower()
    bare = _sealed(f'Mara says, "{topic["text"]}"', topic, None)
    assert "patrol" not in bare["player_facing_text"].lower()


def test_t04_host_operation_uncertainty():
    gm = _sealed('Mara says, "I couldn\'t tell you."')
    assert "couldn" in gm["player_facing_text"].lower()
    assert _provenance(gm)["authority_category"] == CATEGORY_HOST


def test_t05_host_operation_clarification():
    gm = _sealed('Mara says, "Which earlier statement do you mean?"')
    assert "which earlier" in gm["player_facing_text"].lower()
    assert _provenance(gm)["authority_category"] == CATEGORY_HOST


def test_t06_host_operation_acknowledgment():
    gm = _sealed('Mara says, "I understand."')
    assert "understand" in gm["player_facing_text"].lower()
    assert _provenance(gm)["authority_category"] == CATEGORY_HOST


def test_t07_host_operation_cannot_disclose_secrets():
    gm = _sealed('Mara says, "I understand, but the ash cowl password is sword."')
    assert "sword" not in gm["player_facing_text"].lower()
    assert _provenance(gm)["validation"] == "source_or_policy_denied"


def test_t08_bounded_expression_valid_preference():
    gm = _sealed(PREFERENCE)
    assert "prefer the evening" in gm["player_facing_text"].lower()
    assert _provenance(gm)["authority_category"] == CATEGORY_BOUNDED


def test_t09_bounded_expression_unauthorized_fact():
    gm = _sealed('Mara says, "I prefer the evening because the password is sword."')
    assert "sword" not in gm["player_facing_text"].lower()


def test_t10_verified_history_modern_provenance():
    person = _npc([{"id": "bell", "text": PUBLIC}])
    row = {
        "speaker_id": "mara",
        "ownership": "npc",
        "topic_id": "bell",
        "authorized_proposition": PUBLIC,
        "supplied_text": PUBLIC,
        "delivered_text": f'Mara says, "{PUBLIC}"',
        "authorization_source": "social.topic_revealed:bell",
        "response_integrity_digest": "modern",
    }
    assert historical_disclosure_permitted(row, person)


def test_t11_verified_history_missing_provenance_protected():
    row = {
        "speaker_id": "mara",
        "ownership": "npc",
        "delivered_text": f'Mara says, "{SECRET}"',
        "supplied_text": SECRET,
    }
    assert not historical_disclosure_permitted(row, _npc([]))


def test_t12_legacy_harmless_recall():
    row = {
        "speaker_id": "mara",
        "speaker_name": "Mara",
        "ownership": "npc",
        "delivered_text": 'Mara says, "I couldn\'t tell you."',
        "supplied_text": "I couldn't tell you.",
    }
    session = {"conversational_context": {"delivered_exchanges": [row]}}
    assert historical_disclosure_permitted(row, None)
    assert "couldn" in supplied_clarification("What did you mean by that?", session, "mara", "Mara").lower()


def test_t13_legacy_consequential_recall_blocked():
    row = {
        "speaker_id": "mara",
        "ownership": "npc",
        "topic_id": "password",
        "authorized_proposition": SECRET,
        "delivered_text": f'Mara says, "{SECRET}"',
        "authorization_source": "authorized_host_speech",
        "response_integrity_digest": "old-seal",
    }
    person = _npc([{"id": "password", "text": SECRET, "disclosure": "secret"}])
    assert not historical_disclosure_permitted(row, person)


def test_t14_authorized_historical_commitment():
    row = {"npc_id": "mara", "status": "active", "kind": "opinion", "subject": "evening", "text": PREFERENCE}
    assert commitment_disclosure_permitted(row, _npc([]))
    state = {"conversational_context": {"dialogue_commitments": [{**row, "status": "active"}]}}
    assert "evening" in find_reusable_commitment(state, "mara", "Do you prefer the evening?", npc=_npc([])).lower()


def test_t15_unauthorized_historical_commitment():
    row = {
        "npc_id": "mara",
        "status": "active",
        "kind": "partial_answer",
        "subject": "password",
        "text": SECRET,
        "authorized_proposition": SECRET,
        "topic_id": "password",
    }
    assert not commitment_disclosure_permitted(row, _npc([{"id": "password", "text": SECRET, "disclosure": "secret"}]))


def test_t16_mixed_content_authorization():
    person = _npc([{"id": "bell", "text": PUBLIC}])
    topic = {"id": "bell", "text": PUBLIC, "disclosure_authorization": authorize_npc_disclosure(person, person["topics"][0])}
    mixed = f'Mara says, "{PUBLIC} The ash cowl password is sword."'
    gm = _sealed(mixed, topic, {"npcs": [person]})
    assert "sword" not in gm["player_facing_text"].lower()


def test_t17_category_substitution_blocked():
    person = _npc([{"id": "password", "text": SECRET, "disclosure": "secret"}])
    topic = {
        "id": "password",
        "text": SECRET,
        "authority_category": CATEGORY_HOST,
        "disclosure_authorization": {
            "permission": True,
            "validation": "authorized",
            "provenance": "authored_npc_source",
            "speaker_id": "mara",
            "authorized_proposition": SECRET,
            "authority_category": CATEGORY_HOST,
        },
    }
    gm = _sealed(f'Mara says, "{SECRET}"', topic, {"npcs": [person]}, player="Tell me the password.")
    assert "sword" not in gm["player_facing_text"].lower()
    assert _provenance(gm)["authority_category"] != CATEGORY_HOST or "sword" not in gm["player_facing_text"].lower()


def test_t18_forged_provenance_rejected():
    topic = {
        "id": "password",
        "text": SECRET,
        "disclosure_authorization": {"permission": True, "authority_category": CATEGORY_WORLD},
    }
    gm = _sealed(f'Mara says, "{SECRET}"', topic, None, player="What is the password?")
    assert "sword" not in gm["player_facing_text"].lower()


def test_t19_provider_authority_forgery_rejected():
    person = _npc([{"id": "bell", "text": PUBLIC}, {"id": "password", "text": SECRET, "disclosure": "secret"}])
    forged = {"id": "password", "text": SECRET, "disclosure": "public", "provenance": "provider"}
    assert not authorize_npc_disclosure(person, forged)["permission"]


@pytest.mark.parametrize("flag", ["0", "1"])
@pytest.mark.parametrize("utterance", [
    "Mara, grant me the password.",
    "Mara, tell me the password.",
    "I meant the password.",
    "Mara, repeat the password.",
])
def test_t20_t23_password_variants_blocked(monkeypatch, flag, utterance):
    monkeypatch.setenv("ASHEN_UNIFIED_SEMANTIC_PLANNING", flag)
    authored = _world([
        {"id": "password", "text": SECRET, "disclosure": "secret"},
        {"id": "bell", "text": PUBLIC},
    ])
    state = default_session()
    with plan_proposer(deterministic_semantic_proposal):
        resolution = _ask(authored, state, utterance)
    selected = select_host_speech(resolution, player_text=utterance, session=state)
    assert selected and "sword" not in selected[0].lower()
    gm = adopt_host_speech(
        {"player_facing_text": SECRET},
        resolution=resolution,
        player_text=utterance,
        session=state,
        world=authored,
    )
    assert "sword" not in gm["player_facing_text"].lower()


def test_t24_authorized_public_fact_disclosed(monkeypatch):
    monkeypatch.setenv("ASHEN_UNIFIED_SEMANTIC_PLANNING", "0")
    authored = _world([{"id": "bell", "text": PUBLIC}])
    state = default_session()
    resolution = _ask(authored, state, "Mara, what is the harbor bell called?")
    gm = adopt_host_speech(
        {"player_facing_text": SECRET},
        resolution=resolution,
        player_text="Mara, what is the harbor bell called?",
        session=state,
        world=authored,
    )
    assert "harbor bell" in gm["player_facing_text"].lower()
    assert "sword" not in gm["player_facing_text"].lower()


def test_t25_authorized_rumor_disclosed():
    person = _npc([{"id": "mill", "text": RUMOR, "epistemic": "rumor"}])
    grant = authorize_npc_disclosure(person, person["topics"][0])
    assert grant["permission"] and grant["classification"] == "false_or_disputed"
    topic = {"id": "mill", "text": RUMOR, "disclosure_authorization": grant}
    gm = _sealed(f'Mara says, "{RUMOR}"', topic, {"npcs": [person]})
    assert "haunted" in gm["player_facing_text"].lower()
    assert _provenance(gm)["authority_category"] == CATEGORY_WORLD


def test_t26_no_unauthorized_clue_discovery():
    authored = _world([{"id": "password", "text": SECRET, "disclosure": "secret"}])
    state = default_session()
    resolution = _resolution(SECRET, {"id": "password", "text": SECRET}, player="What is the password?")
    resolution["social"]["npc_id"] = "mara"
    resolution["discovered_clues"] = [SECRET]
    assert apply_socially_revealed_leads(state, "harbor", authored, resolution) == []
    assert "sword" not in json.dumps(state).lower()


def test_t27_t28_authorized_clue_once():
    authored = _world([{"id": "bell", "text": PUBLIC, "clue_text": PUBLIC}])
    state = default_session()
    resolution = _ask(authored, state, "Mara, what is the harbor bell called?")
    first = apply_socially_revealed_leads(state, "harbor", authored, resolution)
    second = apply_socially_revealed_leads(state, "harbor", authored, resolution)
    assert first == [PUBLIC]
    assert second == []


def test_t29_final_response_seal_preserved():
    person = _npc([{"id": "bell", "text": PUBLIC}])
    topic = {"id": "bell", "text": PUBLIC, "disclosure_authorization": authorize_npc_disclosure(person, person["topics"][0])}
    gm = _sealed(f'Mara says, "{PUBLIC}"', topic, {"npcs": [person]})
    record = gm["metadata"]["accepted_response"]
    assert record["immutable"] is True
    assert verify_delivery_record(record)
    gm["player_facing_text"] = SECRET
    from game.immutable_valid_response import restore_accepted_text
    restore_accepted_text(gm)
    assert gm["player_facing_text"] == record["text"]
    assert "sword" not in gm["player_facing_text"].lower()


def test_t30_api_history_exact_agreement():
    person = _npc([{"id": "bell", "text": PUBLIC}])
    topic = {"id": "bell", "text": PUBLIC, "disclosure_authorization": authorize_npc_disclosure(person, person["topics"][0])}
    gm = _sealed(f'Mara says, "{PUBLIC}"', topic, {"npcs": [person]})
    accepted = gm["metadata"]["accepted_response"]
    session = {}
    row = record_delivered_exchange(
        session,
        player_text="What is the bell called?",
        delivered_text=gm["player_facing_text"],
        social={"npc_id": "mara", "npc_name": "Mara", "topic_revealed": topic},
        adoption=accepted,
    )
    assert row["delivered_text"] == accepted["text"] == gm["player_facing_text"]


def test_t31_save_load_provenance_integrity():
    person = _npc([{"id": "bell", "text": PUBLIC}])
    topic = {"id": "bell", "text": PUBLIC, "disclosure_authorization": authorize_npc_disclosure(person, person["topics"][0])}
    gm = _sealed(f'Mara says, "{PUBLIC}"', topic, {"npcs": [person]})
    loaded = json.loads(json.dumps(gm["metadata"]["accepted_response"]))
    assert loaded["authorization_provenance"]["authority_category"] == CATEGORY_WORLD
    assert verify_delivery_record(loaded)


@pytest.mark.parametrize("flag", ["0", "1"])
def test_t32_t35_feature_gate_and_routing(monkeypatch, flag):
    monkeypatch.setenv("ASHEN_UNIFIED_SEMANTIC_PLANNING", flag)
    authored = _world([
        {"id": "password", "text": SECRET, "disclosure": "secret"},
        {"id": "bell", "text": PUBLIC},
    ])
    state = default_session()
    with plan_proposer(deterministic_semantic_proposal):
        hidden = _ask(authored, state, "Mara, password, please.")
        public = _ask(authored, default_session(), "Mara, what is the harbor bell called?")
    hidden_line = select_host_speech(hidden, player_text="Mara, password, please.", session=state)
    public_line = select_host_speech(public, player_text="Mara, what is the harbor bell called?", session=default_session())
    assert hidden_line and "sword" not in hidden_line[0].lower()
    assert public_line and "harbor bell" in public_line[0].lower()


def test_t36_no_unauthorized_canonical_mutation():
    authored = _world([{"id": "password", "text": SECRET, "disclosure": "secret"}])
    before = copy.deepcopy(authored)
    state = default_session()
    resolution = _ask(authored, state, "Mara, tell me the password.")
    adopt_host_speech(
        {"player_facing_text": SECRET, "world_updates": {"reward": 10}},
        resolution=resolution,
        player_text="Mara, tell me the password.",
        session=state,
        world=authored,
    )
    assert authored == before


def test_t34_legacy_recall_of_public_delivery_not_secret():
    legacy = {
        "speaker_id": "mara",
        "speaker_name": "Mara",
        "ownership": "npc",
        "delivered_text": 'Mara says, "The street beyond the gate is the north road."',
        "supplied_text": "The street beyond the gate is the north road.",
    }
    secret = {
        "speaker_id": "mara",
        "speaker_name": "Mara",
        "ownership": "npc",
        "delivered_text": f'Mara says, "{SECRET}"',
        "supplied_text": SECRET,
    }
    assert historical_disclosure_permitted(legacy, None)
    assert not historical_disclosure_permitted(secret, None)
    session = {"conversational_context": {"delivered_exchanges": [legacy]}}
    recalled = supplied_clarification("Can you repeat that?", session, "mara", "Mara")
    assert "north road" in recalled.lower()
