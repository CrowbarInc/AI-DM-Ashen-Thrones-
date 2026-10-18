"""C19 free-text authored facts: lexical paraphrase stays, residuals do not.

Deterministic only. No gameplay or model calls.
"""
from __future__ import annotations

import json
from pathlib import Path

from game.gm_resolution_decision import (
    DECISION_METADATA_KEY,
    attach_gm_resolution_decision,
    audit_narration_against_decision,
    authorized_observation_line,
)
from game.proposition_authority import classify_propositions

ROOT = Path(__file__).resolve().parents[1]
GATE_SCENE = ROOT / "data" / "scenes" / "frontier_gate.json"

SCHEDULE = "The city gate closes when the watch changes at the third bell."
FERRY = "The ferry leaves at noon."
SHOP = "The shop closes at sunset."
ROAD = "The northern road floods during heavy rain."


def _decision(fact: str, player: str, *, interlocutor: str | None = None, scene: dict | None = None) -> dict:
    contract = {
        "contract_id": "c19_free_text",
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
        scene=scene or {"scene": {"id": "frontier_gate", "visible_facts": [fact]}},
        world={"npcs": []},
    )
    return resolution["metadata"][DECISION_METADATA_KEY]


def _valid(text: str, decision: dict, corpus: str) -> bool:
    return bool(audit_narration_against_decision(text, decision=decision, authored_corpus=corpus)["hard_valid"])


def test_third_bell_free_text_keeps_empty_identity_and_lexical_paraphrase():
    player = "I ask the guard what hour the gate closes."
    decision = _decision(SCHEDULE, player, interlocutor="gate_guard")
    row = next(row for row in decision["proposed_facts"] if row["text"] == SCHEDULE)
    assert row["authorized"] is True
    assert row["semantic_identity"] == {}
    assert decision["outcome_classification"] == "epistemically_qualified"

    for text in (
        SCHEDULE,
        "The gate closes when the watch changes at the third bell.",
        "The city gate closes at the third bell.",
        "The gate closes at the third bell.",
    ):
        assert _valid(text, decision, SCHEDULE), text


def test_third_bell_residuals_do_not_inherit_the_authored_fact():
    player = "I ask the guard what hour the gate closes."
    decision = _decision(SCHEDULE, player, interlocutor="gate_guard")
    rejected = (
        "Travelers can still pass, but only until the watch changes at the third bell.",
        "After that, the gates close until morning.",
        (
            "Travelers can still pass, but only until the watch changes at the third bell. "
            "After that, the gates close until morning."
        ),
        "The city gate closes when the watch changes at the third bell, and travelers can still pass until morning.",
        "The city gate closes when the watch changes at the third bell until morning.",
    )
    for text in rejected:
        audit = audit_narration_against_decision(text, decision=decision, authored_corpus=SCHEDULE)
        assert audit["hard_valid"] is False, text
        assert any("proposition_authority" in row["reason_codes"] for row in audit["violations"]), text


def test_failed_retry_quotes_the_authored_schedule_and_not_the_scene():
    player = "I ask the guard what hour the gate closes."
    payload = json.loads(GATE_SCENE.read_text(encoding="utf-8"))
    payload["scene"]["visible_facts"].append(SCHEDULE)
    decision = _decision(SCHEDULE, player, interlocutor="gate_guard", scene=payload)
    line = authorized_observation_line(decision, player)
    assert line == SCHEDULE
    assert _valid(line, decision, SCHEDULE)


def test_shop_closing_paraphrase_stays_lexical():
    player = "When does the shop close?"
    decision = _decision(SHOP, player)
    assert _valid(SHOP, decision, SHOP)
    assert _valid("The shop closes at sunset.", decision, SHOP)
    shut = audit_narration_against_decision(
        "The shop shuts at sunset.",
        decision=decision,
        authored_corpus=SHOP,
    )
    assert shut["hard_valid"] is False
    assert any("proposition_authority" in row["reason_codes"] for row in shut["violations"])


def test_ferry_and_road_examples_follow_the_consequential_family_boundary():
    """Noon, boarding, and road use are not schedule/access families.

    Lexical restatement of the authored sentence is accepted. A synonym such as
    "departs" is not licensed by identity; it is simply outside the consequential
    detectors. Additions that do hit a consequential family stay unauthorized.
    """
    ferry = _decision(FERRY, "When does the ferry leave?")
    assert _valid(FERRY, ferry, FERRY)
    assert _valid("The ferry leaves at noon.", ferry, FERRY)
    depart = classify_propositions("The ferry departs at noon.", authored_corpus=FERRY)
    assert all(row["family"] in {"", "none", "incidental"} for row in depart)
    dusk = audit_narration_against_decision(
        "It returns at dusk.",
        decision=ferry,
        authored_corpus=FERRY,
    )
    assert dusk["hard_valid"] is False

    road = _decision(ROAD, "What happens to the northern road in the rain?")
    assert _valid(ROAD, road, ROAD)
    assert _valid("The northern road floods during heavy rain.", road, ROAD)
