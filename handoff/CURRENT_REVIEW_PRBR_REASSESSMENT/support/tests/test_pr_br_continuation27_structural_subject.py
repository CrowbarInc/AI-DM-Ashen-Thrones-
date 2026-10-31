"""PR-BR C27: structural resolution subject and lossless operative context. Stubbed."""
from __future__ import annotations

import json
from pathlib import Path

from game.contract_adjudication_bridge import (
    select_resolver_family,
    structural_interaction_frame,
)
from game.incidental_entity import referential_person_nominal
from game.ordinary_semantic_ownership import select_ordinary_resolver
from game.resolution_contract import (
    PROVENANCE_EXCERPT_LIMIT,
    construct_resolution_contract,
    semantic_input_text,
)
from game.scene_destination_binding import resolve_authored_exit_from_player_travel
from game.structured_player_output import classify_model_output
from tests.test_pr_br_continuation21c_referential_head import TURN3
from tests.test_pr_br_continuation22_commitment import EXITS, H1, H2, H3, _contract as c22_contract
from tests.test_pr_br_continuation26_semantic_closure import T1, T4

ROOT = Path(__file__).resolve().parents[1]
C26_TURNS = ROOT / "artifacts" / "pr_br_continuation26" / "live" / "20261003T134953Z" / "turns.json"
PAD = (
    "Grey rain continues across the stones and the hour grows late while cloaks drip. "
    * 6
).strip()


def _turns() -> dict[int, str]:
    rows = json.loads(C26_TURNS.read_text(encoding="utf-8"))
    return {int(row["turn"]): row["raw_player_input"] for row in rows}


def _built(text: str):
    contract = construct_resolution_contract(player_text=text).as_dict()
    resolver, family = select_ordinary_resolver(contract)
    return contract, resolver, family


def _subject(text: str) -> str:
    contract, _resolver, _family = _built(text)
    return contract["construction"]["resolution_subject"]


def test_c26_turn3_quoted_ask_stays_social_despite_shelter():
    raw = _turns()[3]
    contract, resolver, family = _built(raw)
    construction = contract["construction"]
    assert contract["operation"] == "ask"
    assert construction["resolution_subject"] == "social"
    assert construction["resolution_subject_coherence"] == "canonicalized"
    assert family is None
    assert resolver == "social"
    assert structural_interaction_frame(
        raw,
        operation=contract["operation"],
        commitment=construction["commitment_status"],
    ) == "social_ask"
    assert "shelter" in raw.lower()
    assert select_resolver_family(contract) is None


def test_c26_turn4_keeps_the_terminal_ask():
    raw = _turns()[4]
    semantic = semantic_input_text(raw)
    contract, resolver, family = _built(raw)
    construction = contract["construction"]
    assert len(semantic) > PROVENANCE_EXCERPT_LIMIT
    assert contract["raw_input"] == semantic
    assert construction["semantic_input_length"] == len(semantic)
    assert construction["provenance_excerpt"] == semantic[:PROVENANCE_EXCERPT_LIMIT]
    assert "I ask if they have any more details" in contract["raw_input"]
    assert "I ask if they have any more details" not in construction["provenance_excerpt"]
    assert contract["operation"] == "ask"
    assert construction["resolution_subject"] == "social"
    assert family is None
    assert resolver == "social"


def test_d1_through_d8_structural_precedence():
    rows = [
        ("I ask the runner whether there is shelter nearby.", "ask", "social", None, "social_ask"),
        ("Is there shelter nearby?", "ask", "place_location", "place_location", "direct_place"),
        ("I ask the guard who is nearby.", "ask", "social", None, "social_ask"),
        ("Who is nearby?", "ask", "nearby_presence", "nearby_presence", "direct_presence"),
        ("I ask the guard whether I can climb the wall.", "ask", "social", None, "social_ask"),
        ("Can I climb the wall?", "ask", "feasibility", "feasibility", "direct_feasibility"),
        ("I ask the merchant where the harbor is.", "ask", "social", None, "social_ask"),
        ("Where is the harbor?", "ask", "place_location", "place_location", "direct_place"),
    ]
    assert len(rows) == 8
    for text, operation, subject, family, frame in rows:
        contract, resolver, got_family = _built(text)
        assert contract["operation"] == operation, text
        assert contract["construction"]["resolution_subject"] == subject, text
        assert got_family == family, text
        if family:
            assert resolver == "adjudication"
        else:
            assert resolver == "social"
        assert structural_interaction_frame(
            text,
            operation=contract["operation"],
            commitment=contract["construction"]["commitment_status"],
        ) == frame


def test_h1_through_h6_direct_controls_stay_non_social():
    rows = [
        ("Is there shelter nearby?", "place_location", "place_location"),
        ("Who is nearby?", "nearby_presence", "nearby_presence"),
        ("Can I climb this wall?", "feasibility", "feasibility"),
        ("Where is the harbor?", "place_location", "place_location"),
        ("What does the inscription say?", "perception", None),
        ("Do I hear movement outside?", "perception", None),
    ]
    assert len(rows) == 6
    for text, subject, family in rows:
        contract, resolver, got_family = _built(text)
        assert contract["construction"]["resolution_subject"] == subject, text
        assert got_family == family, text
        assert resolver != "social" or family is None and subject == "social"
        assert structural_interaction_frame(
            text,
            operation=contract["operation"],
            commitment=contract["construction"]["commitment_status"],
        ) != "social_ask"


def test_topic_word_is_not_required_for_the_social_frame():
    quoted = (
        'I approach the lone figure in threadbare clothes, keeping my voice low. '
        '"Do you know what happened to the patrol? I need a dry room and some guidance."'
    )
    contract, _resolver, family = _built(quoted)
    assert "shelter" not in quoted.lower()
    assert contract["operation"] == "ask"
    assert contract["construction"]["resolution_subject"] == "social"
    assert family is None
    direct = _built("Is there a dry room nearby?")
    assert direct[0]["construction"]["resolution_subject"] == "place_location"
    assert direct[2] == "place_location"


def test_l1_through_l8_operative_clause_survives_position():
    ask = "I ask the runner what he knows about the patrol."
    cases = {
        "L1": ask + " " + PAD,
        "L2": PAD[:180] + " " + ask + " " + PAD[:180],
        "L3": PAD + " " + ask,
        "L4": PAD + " " + PAD + " " + ask,
        "L5": ask + " " + PAD + " " + PAD,
        "L6": (
            PAD
            + ' The figure says, "The yard is quiet tonight." '
            + 'I approach the runner and ask, "Did the patrol pass this way?"'
        ),
        "L7": "If the rain gets worse, I might leave later. " + PAD + " " + ask,
        "L8": "I turn the thought over and stay with it a while. " + PAD + " " + ask,
    }
    assert len(cases) == 8
    for label, text in cases.items():
        assert len(semantic_input_text(text)) > PROVENANCE_EXCERPT_LIMIT, label
        contract, resolver, family = _built(text)
        assert ask.split()[0] == "I"
        assert "ask" in contract["raw_input"].lower(), label
        assert contract["operation"] == "ask", label
        assert contract["construction"]["resolution_subject"] == "social", label
        assert contract["construction"]["commitment_status"] == "executed_now", label
        assert resolver == "social", label
        assert family is None, label
        assert contract["raw_input"] == semantic_input_text(text)


def test_m1_through_m5_clause_precedence():
    rows = [
        ("I consider heading to the harbor, but first ask the runner what he knows.", "ask", "social", "contemplated"),
        ("I ask the runner what he knows, then head for the harbor.", "ask", "social", "executed_now"),
        ("I hope to find shelter and ask the runner whether the patrol passed this way.", "ask", "social", "executed_now"),
        ("I ask about the patrol before deciding whether to seek shelter.", "ask", "social", "executed_now"),
        ("I look toward the harbor while asking the runner about the patrol.", "perceive", "perception", "executed_now"),
    ]
    assert len(rows) == 5
    for text, operation, subject, commitment in rows:
        contract, _resolver, family = _built(text)
        assert contract["operation"] == operation, text
        assert contract["construction"]["resolution_subject"] == subject, text
        assert contract["construction"]["commitment_status"] == commitment, text
        assert family != "place_location"


def test_u1_through_u20_structural_subject_matrix():
    rows = [
        ("I ask the runner whether there is shelter nearby.", "ask", "social", None, "social"),
        ("Is there shelter nearby?", "ask", "place_location", "place_location", "adjudication"),
        ("I ask the guard who is nearby.", "ask", "social", None, "social"),
        ("Who is nearby?", "ask", "nearby_presence", "nearby_presence", "adjudication"),
        ("I ask the guard whether I can climb the wall.", "ask", "social", None, "social"),
        ("Can I climb the wall?", "ask", "feasibility", "feasibility", "adjudication"),
        ("I ask the merchant where the harbor is.", "ask", "social", None, "social"),
        ("Where is the harbor?", "ask", "place_location", "place_location", "adjudication"),
        ("I ask the runner what happened to the patrol.", "ask", "social", None, "social"),
        ("What happened to the patrol?", "ask", "social", None, "social"),
        ("I ask the runner whether the road is safe.", "ask", "social", None, "social"),
        ("Where does this road lead?", "ask", "travel", None, "travel"),
        ("I ask the guard whether an attack is coming.", "ask", "social", None, "social"),
        ("I attack the bandit.", "act", "combat", None, "generation"),
        ("I ask the scribe what the inscription says.", "ask", "social", None, "social"),
        ("I inspect the inscription.", "inspect", "perception", None, "exploration"),
        ("I ask the runner what they hear.", "ask", "social", None, "social"),
        ("I listen for movement outside.", "perceive", "perception", None, "exploration"),
        ("I ask the runner about the patrol, the harbor, and any shelter nearby.", "ask", "social", None, "social"),
        ("I open the door and ask the guard what is inside.", "unresolved", "unspecified", None, "generation"),
    ]
    assert len(rows) == 20
    for text, operation, subject, family, resolver in rows:
        contract, got, got_family = _built(text)
        assert contract["operation"] == operation, text
        assert contract["construction"]["resolution_subject"] == subject, text
        assert got_family == family, text
        assert got == resolver, text


def test_long_context_matrix_has_twelve_positions():
    nuclei = [
        ("I ask the runner what he knows about the patrol.", "ask", "social", "executed_now"),
        ("I listen for movement outside.", "perceive", "perception", "executed_now"),
        ("I follow the road toward the old milestone.", "act", "travel", "executed_now"),
        ("I inspect the inscription.", "inspect", "perception", "executed_now"),
        ("Where is the harbor?", "ask", "place_location", "executed_now"),
        ("Who is nearby?", "ask", "nearby_presence", "executed_now"),
    ]
    built = []
    for nucleus, operation, subject, commitment in nuclei:
        built.append((nucleus + " " + PAD, operation, subject, commitment))
        built.append((PAD + " " + nucleus, operation, subject, commitment))
    assert len(built) == 12
    for text, operation, subject, commitment in built:
        contract, _resolver, family = _built(text)
        assert len(contract["raw_input"]) > PROVENANCE_EXCERPT_LIMIT
        assert contract["operation"] == operation, text[:60]
        assert contract["construction"]["resolution_subject"] == subject, text[:60]
        assert contract["construction"]["commitment_status"] == commitment, text[:60]
        if subject == "social":
            assert family is None
        if subject == "place_location":
            assert family == "place_location"


def test_randomized_length_property_keeps_the_contract_invariant():
    nuclei = [
        "I ask the runner what he knows about the patrol.",
        "Is there shelter nearby?",
        "Who is nearby?",
        "Can I climb the wall?",
        "I inspect the inscription.",
        "I listen for movement outside.",
        "I attack the bandit.",
        "I follow the road toward the old milestone.",
        "Where does this road lead?",
    ]
    variants = []
    for nucleus in nuclei:
        variants.append(nucleus + " " + PAD)
        variants.append(PAD + " " + nucleus)
        variants.append(PAD[:120] + " " + nucleus + " " + PAD[:120])
    assert len(variants) == 27
    for nucleus in nuclei:
        bare, _resolver, _family = _built(nucleus)
        for text in variants:
            if nucleus not in text:
                continue
            padded, _r, _f = _built(text)
            assert padded["operation"] == bare["operation"], nucleus
            assert padded["construction"]["resolution_subject"] == bare["construction"]["resolution_subject"]
            assert padded["construction"]["commitment_status"] == bare["construction"]["commitment_status"]
            assert padded["interlocutor_id"] == bare["interlocutor_id"]


def test_post_contract_selection_does_not_repair_a_bad_subject():
    contract, _resolver, _family = _built("I ask the runner what he knows about the patrol.")
    assert contract["construction"]["resolution_subject"] == "social"
    assert select_resolver_family(contract) is None
    contract["construction"]["resolution_subject"] = "place_location"
    assert select_resolver_family(contract) == "place_location"


def test_structured_output_boundary_still_rejects_a_raw_envelope():
    leaked = '{"player_facing_text": "The gate holds.", "debug_notes": "hidden"}'
    parsed = classify_model_output(leaked)
    assert parsed["form"] == "structured"
    assert parsed["player_facing_text"] == "The gate holds."
    assert "debug_notes" not in parsed["player_facing_text"]
    broken = classify_model_output('{"player_facing_text": "cut')
    assert broken["form"] == "malformed"
    assert broken["player_facing_text"] == ""


def test_historical_t1_through_t10():
    turn3 = _turns()[3]
    turn4 = _turns()[4]
    c26_3, _r, family = _built(turn3)
    assert c26_3["construction"]["resolution_subject"] == "social"
    assert family is None
    c26_4, _r, family = _built(turn4)
    assert "I ask if they have any more details" in c26_4["raw_input"]
    assert c26_4["construction"]["resolution_subject"] == "social"
    assert family is None
    c25_1, resolver, _family = _built(T1)
    assert c25_1["operation"] == "ask" and resolver == "social"
    c25_4, _resolver, family = _built(T4)
    assert c25_4["operation"] == "ask"
    assert c25_4["construction"]["resolution_subject"] != "place_location"
    assert c25_4["construction"]["commitment_status"] == "contemplated"
    assert family is None
    who, _resolver, who_family = _built("Who is nearby?")
    supplies, _resolver, supplies_family = _built("I ask the runner if there are supplies nearby.")
    assert who["construction"]["resolution_subject"] == "nearby_presence"
    assert who_family == "nearby_presence"
    assert supplies["operation"] == "ask" and supplies_family is None
    listen = c22_contract(H1)
    assert listen.operation == "ask"
    assert "perceive" in listen.construction["secondary_operations"]
    assert "sound" not in listen.dimensions
    conditional = "If the tracks are fresh, I'll follow them toward the old milestone."
    held = _built(conditional)[0]
    assert held["construction"]["commitment_status"] != "executed_now"
    assert held["operation"] not in {"act", "follow"}
    assert resolve_authored_exit_from_player_travel(conditional, EXITS) is None
    serjeant = c22_contract(H3)
    assert serjeant.operation == "ask"
    assert "serjeant" in str(serjeant.construction["requested_addressee"]).lower()
    assert serjeant.interlocutor_id != "guard_captain"
    inspected = _built(TURN3)[0]
    assert inspected["operation"] == "inspect"
    assert referential_person_nominal("the muddy lane northwest of the crates") is None
    representatives = [
        "I ask a nearby porter whether the wagons are through.",
        "I inspect the footprints.",
        "I listen carefully at the door.",
        "I ask the guard what he saw.",
        "I examine the lock.",
        'I lean in, matching the captain\'s low voice. "Whose orders are these?"',
        "I look at the traveler.",
        "I ask the runner what he heard, and I watch his hands.",
        H2,
        "I approach the traveler.",
    ]
    assert len(representatives) == 10
    for text in representatives:
        contract, _resolver, family = _built(text)
        assert contract["contract_id"], text
        if contract["operation"] == "ask":
            assert contract["construction"]["resolution_subject"] == "social", text
            assert family is None
        if contract["operation"] in {"inspect", "perceive"}:
            assert contract["construction"]["resolution_subject"] == "perception", text
