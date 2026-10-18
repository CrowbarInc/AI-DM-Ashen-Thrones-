"""PR-BR C26: contract sufficiency and post-contract semantic closure. Stubbed."""
from __future__ import annotations

from game.contract_adjudication_bridge import select_resolver_family
from game.gm import _safe_json
from game.immutable_valid_response import run_preserve_if_valid, validate_generated_response
from game.interpretation_proposal import (
    InterpretationProposal,
    SOURCE_MODEL,
    validate_interpretation_proposal,
)
from game.ordinary_semantic_ownership import select_ordinary_resolver
from game.resolution_contract import OP_ACT, OP_INSPECT, construct_resolution_contract
from game.structured_player_output import classify_model_output

T4 = (
    "I consider the tavern runner's words and decide to head toward the city harbor, "
    "hoping to find shelter despite the crowds. Along the way, I plan to watch for any "
    "signs of the guard captain or other officials I might approach for guidance."
)
T1 = (
    'I approach the ragged figure standing at the edge of the crowd and speak softly, '
    '"Traveler, what brings you to this gate in such foul weather? Have you heard any '
    "news or know what troubles this place?"
)
LEAK = (
    'The ragged stranger glances up. They say, "Foul weather."\n\n'
    '{\n  "player_facing_text": "The ragged stranger glances up.",\n'
    '  "tags": ["scene_momentum:new_information"],\n'
    '  "debug_notes": "internal"\n}'
)


def _built(text: str):
    contract = construct_resolution_contract(player_text=text).as_dict()
    resolver, family = select_ordinary_resolver(contract)
    return contract, resolver, family


def test_c25_turn4_contract_is_not_a_place_lookup():
    contract, resolver, family = _built(T4)
    construction = contract["construction"]
    assert contract["operation"] == "ask"
    assert construction["proposed_operation"] == "act"
    assert construction["commitment_status"] == "contemplated"
    assert construction["resolution_subject"] != "place_location"
    assert family != "place_location"
    assert resolver != "adjudication"
    assert select_resolver_family(contract) is None


def test_c25_turn1_model_act_cannot_become_authoritative():
    contract, resolver, _family = _built(T1)
    assert contract["operation"] == "ask"
    assert resolver == "social"
    proposal = InterpretationProposal(raw_input=T1, source=SOURCE_MODEL, primary_operation=OP_ACT)
    result = validate_interpretation_proposal(proposal, canonical_referents=[])
    assert result.status == "validated"
    assert result.authoritative_operation == "ask"


def test_d1_through_d8_distinctions():
    rows = [
        ("I ask the runner whether there is shelter nearby.", "ask", "social", None),
        ("Is there shelter nearby?", "ask", "adjudication", "place_location"),
        ("Where is the nearest inn?", "ask", "adjudication", "place_location"),
        ("I ask the innkeeper where the harbor is.", "ask", "social", None),
        ("Who is nearby?", "ask", "adjudication", "nearby_presence"),
        ("I ask the guard who is nearby.", "ask", "social", None),
        ("Can I climb the wall?", "ask", "adjudication", "feasibility"),
        ("I ask the guard whether I can climb the wall.", "ask", "social", None),
    ]
    assert len(rows) == 8
    for text, operation, resolver, family in rows:
        contract, got, got_family = _built(text)
        assert contract["operation"] == operation, text
        assert got == resolver, text
        assert got_family == family, text
        assert contract["construction"]["resolution_subject"]
        if resolver == "social":
            assert got_family is None


def test_j1_through_j6_controls():
    rows = [
        ('I approach the traveler and ask, "What brings you here?"', "ask", "social"),
        ('I tell the traveler, "Stay here."', "ask", "social"),
        ("I approach the traveler.", "act", "world_action"),
        ("I look at the traveler.", "inspect", "exploration"),
        ("I ask whether the traveler looks injured.", "ask", "social"),
    ]
    for text, operation, resolver in rows:
        contract, got, family = _built(text)
        assert contract["operation"] == operation, text
        assert got == resolver, text
        assert family is None
    bare = InterpretationProposal(raw_input="Traveler?", source=SOURCE_MODEL, primary_operation=OP_ACT)
    checked = validate_interpretation_proposal(bare, canonical_referents=[])
    assert checked.authoritative_operation != "ask" or checked.status != "validated" or bare.primary_operation == "act"
    contract, _resolver, _family = _built("Traveler?")
    assert contract["operation"] != "act" or contract["construction"]["resolution_subject"] != "place_location"


def test_r1_through_r20_matrix():
    rows = [
        ("I ask the runner whether there is shelter nearby.", "social", None),
        ("Is there shelter nearby?", "adjudication", "place_location"),
        ("I ask the innkeeper where the harbor is.", "social", None),
        ("Where is the nearest inn?", "adjudication", "place_location"),
        ("I ask the guard who is nearby.", "social", None),
        ("Who is nearby?", "adjudication", "nearby_presence"),
        ("I ask the guard whether I can climb the wall.", "social", None),
        ("Can I climb the wall?", "adjudication", "feasibility"),
        ("I ask the runner whether the road is safe.", "social", None),
        ("Would the road lead to the milestone?", "adjudication", "feasibility"),
        ("I ask the runner what he heard, and I watch his hands.", "social", None),
        ("I ask the runner whether I should head for the harbor.", "social", None),
        ("I ask the guard whether I should attack the bandit.", "social", None),
        ("I attack the bandit.", "generation", None),
        ("If he draws, I attack the bandit.", "social", None),
        ("I inspect the guard's cloak.", "exploration", None),
        ("I walk toward the tavern.", "travel", None),
        (T4, "social", None),
        ("If the guard refuses, I'll look for shelter nearby.", "social", None),
        ("Please transmute the moon into cheese.", "social", None),
    ]
    assert len(rows) == 20
    for text, resolver, family in rows:
        contract, got, got_family = _built(text)
        assert got == resolver, text
        assert got_family == family, text
        subject = contract["construction"]["resolution_subject"]
        if family:
            assert subject == family
        else:
            assert subject not in {"place_location", "nearby_presence", "earshot", "feasibility"}


def test_s1_through_s10_malformed_proposals_do_not_stick():
    cases = [
        ('I approach the traveler and ask, "What brings you here?"', OP_ACT, "ask", "validated"),
        ("I ask the traveler what brings you here?", OP_ACT, "ask", "validated"),
        ('I tell the traveler, "The gate is shut."', OP_INSPECT, "ask", "validated"),
        ('I tell the traveler, "Stay here."', OP_ACT, "ask", "validated"),
        ("I approach the traveler.", "ask", "act", "validated"),
        ("I look at the traveler.", "ask", "inspect", "validated"),
        ("I listen to the traveler.", OP_ACT, "perceive", "validated"),
        ("I ask whether the traveler looks injured.", OP_INSPECT, "ask", "validated"),
        ('"What brings you here?"', OP_ACT, None, "validated"),
        ("I open the door and ask the guard what is inside.", OP_ACT, None, "abstained"),
    ]
    assert len(cases) == 10
    for text, proposed, expected, status in cases:
        result = validate_interpretation_proposal(
            InterpretationProposal(raw_input=text, source=SOURCE_MODEL, primary_operation=proposed),
            canonical_referents=[],
        )
        assert result.status == status, text
        if expected:
            assert result.authoritative_operation == expected, text
        if status == "abstained":
            assert result.authoritative_operation != proposed or proposed is None


def test_t1_through_t8_output_boundary():
    plain = classify_model_output('The gate creaks. He says: "Wait."')
    assert plain["form"] == "plain"
    assert "player_facing_text" not in plain["player_facing_text"]
    structured = classify_model_output('{"player_facing_text": "The gate holds.", "tags": ["ok"]}')
    assert structured["form"] == "structured"
    assert structured["player_facing_text"] == "The gate holds."
    extra = classify_model_output(
        '{"player_facing_text": "Rain on the gate.", "debug_notes": "hidden", "tags": ["x"]}'
    )
    assert extra["player_facing_text"] == "Rain on the gate."
    assert "debug_notes" not in extra["player_facing_text"]
    malformed = classify_model_output('{"player_facing_text": "cut')
    assert malformed["form"] == "malformed"
    assert malformed["player_facing_text"] == ""
    missing = classify_model_output('{"tags": ["x"], "debug_notes": "no prose", "scene_update": null}')
    assert missing["form"] == "malformed"
    embedded = classify_model_output(LEAK)
    assert embedded["form"] == "malformed"
    braces = classify_model_output("The chalk on the post reads {CLOSED} in the rain.")
    assert braces["form"] == "plain"
    assert "{CLOSED}" in braces["player_facing_text"]
    quoted = classify_model_output('The runner says: "No shelter here."')
    assert quoted["form"] == "plain"
    sealed = _safe_json(LEAK)
    assert sealed["player_facing_text"] == ""
    assert "player_facing_text" not in sealed["player_facing_text"]
    verdict = validate_generated_response(LEAK, contract={"operation": "ask", "contract_id": "rc"})
    assert verdict["hard_valid"] is False
    assert "structured_envelope" in verdict["reasons"]


def test_t9_t10_retry_keeps_the_contract_and_hides_the_envelope():
    contract = construct_resolution_contract(player_text="I ask the runner about the gate.").as_dict()
    resolution = {"metadata": {"resolution_contract": contract}}
    calls = {"n": 0}

    def _retry(_feedback: str):
        calls["n"] += 1
        parsed = _safe_json('{"player_facing_text": "The runner says, \\"The gate is shut.\\"", "debug_notes": "x"}')
        return parsed

    first = _safe_json(LEAK)
    sealed = run_preserve_if_valid(
        first,
        regenerate=_retry,
        resolution=resolution,
        player_text=contract["raw_input"],
    )
    assert calls["n"] == 1
    text = str(sealed.get("player_facing_text") or "")
    assert "debug_notes" not in text
    assert not text.strip().startswith("{")
    assert sealed["metadata"]["accepted_response"]["text"] == text

    def _bad(_feedback: str):
        return _safe_json('{"player_facing_text": ')

    again = run_preserve_if_valid(
        _safe_json(LEAK),
        regenerate=_bad,
        resolution=resolution,
        player_text=contract["raw_input"],
    )
    hidden = str(again.get("player_facing_text") or "")
    assert "player_facing_text" not in hidden
    assert again["metadata"]["accepted_response"]["contract"]["contract_id"] == contract["contract_id"]
    assert "{" not in hidden
