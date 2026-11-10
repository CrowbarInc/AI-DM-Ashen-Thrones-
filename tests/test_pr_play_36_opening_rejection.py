"""PR-PLAY-36: the captured PR-PLAY-35 opening, offline.

The provider response file is the live fixture and is not rewritten.
No provider client is constructed.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from game.api import _opening_scene_normalized_action_and_resolution
from game.clocks import advance_clock, get_or_init_clocks
from game.gm_resolution_decision import (
    _CONSEQUENTIAL_PATTERNS,
    _accepted_declaration_texture_realization,
    _authorized_statement_texts,
    _proposition_restates_statement,
    _token_set,
    _unlicensed_consequential_reasons,
    audit_narrated_claims,
    audit_realization_envelope_against_decision,
    decision_from_resolution,
)
from game.immutable_valid_response import validate_generated_response
from game.interaction_context import synchronize_scene_addressability
from game.live_resolution import attach_interaction_obligation
from game.world import advance_world_tick

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "artifacts" / "atgb" / "pr_play_35" / "live" / "20261102T011549Z-bd0c88693cd0"
EVIDENCE = RUN / "opening_response_evidence" / "e97b9ce72d9b494db77178582be66ceb-1.json"
BASELINE = RUN / "baseline" / "persistent"

NOTICE_SENTENCE = (
    "A notice board nearby lists new taxes, curfew rules, and a posted warning about a missing patrol."
)
CHOKE_SENTENCE = (
    "Refugees, wagons, and foot traffic clog the muddy approach; "
    "guards hold the choke tightly as the crowd presses in."
)
VISIBLE_NOTICE = "The notice board lists taxes, curfew rules, and a warning about a missing patrol."
SEED_NOTICE = "A notice board lists new taxes, curfews, and a posted warning about a missing patrol."
CHOKE_FACT = (
    "Refugees, wagons, and foot traffic clog the muddy approach; "
    "guards hold the choke while the crowd presses in."
)


def _load(name: str):
    return json.loads((BASELINE / name).read_text(encoding="utf-8"))


def _opening_decision():
    session = _load("session.json")["payload"]
    world = _load("world.json")
    scene = _load("scenes/frontier_gate.json")
    campaign = _load("campaign.json")
    synchronize_scene_addressability(session, scene, world)
    scene["scene_state"] = session.get("scene_state")
    session["turn_counter"] = int(session.get("turn_counter") or 0) + 1
    advance_world_tick(world, campaign)
    get_or_init_clocks(session)
    advance_clock(session, "time_pressure", 1)
    normalized, resolution = _opening_scene_normalized_action_and_resolution(
        scene=scene,
        player_text=None,
        internal_bootstrap=True,
    )
    attach_interaction_obligation(
        resolution,
        player_text=resolution.get("prompt") or "",
        session=session,
        normalized_action=normalized,
        scene_id="frontier_gate",
        scene=scene,
        world=world,
        visible_turns=[],
        enable_model_interpretation=False,
    )
    return session, scene, resolution, decision_from_resolution(resolution)


def _captured():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))["parsed_response"]


def _audit(narration: str, declared, decision):
    return audit_realization_envelope_against_decision(
        narration=narration,
        declared_claims=declared,
        decision=decision,
        authored_corpus="",
    )


def _replace(narration: str, old: str, new: str) -> str:
    assert old in narration
    return narration.replace(old, new, 1)


@pytest.fixture(scope="module")
def opening():
    session, scene, resolution, decision = _opening_decision()
    parsed = _captured()
    return {
        "session": session,
        "scene": scene,
        "resolution": resolution,
        "decision": decision,
        "parsed": parsed,
    }


def test_fixture_is_the_captured_nine_claim_opening(opening):
    parsed = opening["parsed"]
    assert len(parsed["narration"]) == 945
    assert parsed["narration"] == parsed["player_facing_text"]
    assert len(parsed["declared_claims"]) == 9
    assert [row["declaration_id"] for row in parsed["declared_claims"]] == [f"dc_{i}" for i in range(1, 10)]
    assert NOTICE_SENTENCE in parsed["narration"]
    assert CHOKE_SENTENCE in parsed["narration"]


def test_pre_repair_rules_identify_the_two_rejected_sentences(opening):
    """The strict restatement rule still marks these sentences as added wording.

    Before the repair, that gap produced notice_roster_history and
    undeclared_consequential_claim. The sentences are authorized blends, not
    new state.
    """
    decision = opening["decision"]
    statements = _authorized_statement_texts(decision)
    assert VISIBLE_NOTICE in statements
    assert SEED_NOTICE in statements
    assert CHOKE_FACT in statements
    notice_pattern = dict(_CONSEQUENTIAL_PATTERNS)["notice_roster_history"]
    assert notice_pattern.search(NOTICE_SENTENCE)
    assert not _proposition_restates_statement(NOTICE_SENTENCE, VISIBLE_NOTICE)
    assert not _proposition_restates_statement(NOTICE_SENTENCE, SEED_NOTICE)
    assert not any(
        notice_pattern.search(statement) and _proposition_restates_statement(NOTICE_SENTENCE, statement)
        for statement in statements
    )
    assert _token_set(NOTICE_SENTENCE) - (_token_set(VISIBLE_NOTICE) | _token_set(SEED_NOTICE)) == {"nearby"}
    assert _token_set(CHOKE_SENTENCE) - _token_set(CHOKE_FACT) == {"tightly"}
    assert not _proposition_restates_statement(CHOKE_SENTENCE, CHOKE_FACT)


def test_captured_declarations_match_authorized_claim_ids(opening):
    claims = {row["claim_id"]: row for row in opening["decision"]["realization_claims"]}
    for declared in opening["parsed"]["declared_claims"]:
        match = claims[declared["source_claim_id"]]
        assert match["text"] == declared["text"]
        assert match["provenance"] == "authored_world_fact"
        assert match["realization_role"] == "MUST_STATE"


def test_corrected_opening_is_accepted_and_deterministic(opening):
    parsed = opening["parsed"]
    decision = opening["decision"]
    first = _audit(parsed["narration"], parsed["declared_claims"], decision)
    second = _audit(parsed["narration"], parsed["declared_claims"], decision)
    assert first["declaration_validation"]["hard_valid"] is True
    assert first["declaration_validation"]["rejected_claims"] == []
    assert first["narration_validation"]["hard_valid"] is True
    assert first["violations"] == []
    assert first["hard_valid"] is True
    assert first == second
    verdict = validate_generated_response(
        parsed["narration"],
        decision=decision,
        declared_claims=parsed["declared_claims"],
        player_text="",
        resolution=opening["resolution"],
        authored_corpus="",
    )
    assert verdict["hard_valid"] is True
    assert verdict["reasons"] == []


def test_audit_does_not_mutate_decision_or_session(opening):
    decision = copy.deepcopy(opening["decision"])
    session = copy.deepcopy(opening["session"])
    before_decision = copy.deepcopy(decision)
    before_session = copy.deepcopy(session)
    parsed = opening["parsed"]
    _audit(parsed["narration"], parsed["declared_claims"], decision)
    assert decision == before_decision
    assert session == before_session


def test_genuine_unauthorized_claims_stay_rejected(opening):
    parsed = opening["parsed"]
    narration = parsed["narration"]
    declared = parsed["declared_claims"]
    decision = opening["decision"]
    replacements = {
        "posted_yesterday": _replace(
            narration,
            NOTICE_SENTENCE,
            "The notice was posted yesterday with the captain's seal, a roster of twelve names, "
            "and fresh annotations ordering the east road closed.",
        ),
        "grim_paraphrase": _replace(
            narration,
            NOTICE_SENTENCE,
            "The board itself lists grim new taxes, curfew regulations, and a posted warning "
            "about a patrol that has gone missing.",
        ),
        "yesterday_on_authorized_blend": _replace(
            narration,
            NOTICE_SENTENCE,
            "A notice board nearby lists new taxes, curfew rules, and a posted warning "
            "about a missing patrol yesterday.",
        ),
        "murdered_patrol": _replace(
            narration,
            NOTICE_SENTENCE,
            "A notice board lists a posted warning that Captain Thoran murdered the missing patrol.",
        ),
        "two_texture_words": _replace(
            narration,
            NOTICE_SENTENCE,
            "A notice board nearby lists new taxes, curfew rules, and a posted warning "
            "about a missing patrol tightly.",
        ),
        "quietly_is_not_texture": _replace(
            narration,
            CHOKE_SENTENCE,
            "Refugees, wagons, and foot traffic clog the muddy approach; "
            "guards hold the choke quietly as the crowd presses in.",
        ),
        "travel": narration + " You leave the gate and arrive at the market quarter.",
        "hidden_cache": narration + " You discover a hidden cache behind the notice board.",
        "item_transfer": narration + " The serjeant gives you a sealed letter.",
        "bootprints": narration + " You find bootprints by the road.",
        "route_change": narration + " The patrol route changed and split at the northwest fork.",
        "npc_command": narration + " The gate serjeant opens the gate and orders the watch to depart.",
    }
    for name, text in replacements.items():
        audit = _audit(text, declared, decision)
        assert audit["hard_valid"] is False, name
        assert audit["violations"], name


def test_repair_does_not_cover_undetected_state_sentences(opening):
    """Sentences the detector never classifies stay unclassified.

    The texture and blend rules do not grant them authority.
    """
    decision = opening["decision"]
    declared = opening["parsed"]["declared_claims"]
    samples = (
        "You take the serjeant's coin purse.",
        "The gate serjeant has been arrested.",
        "The missing-patrol quest is complete.",
        "An agent of a noble house is watching new arrivals from the square's edge.",
    )
    for sample in samples:
        assert _unlicensed_consequential_reasons(sample, decision) == []
        assert _accepted_declaration_texture_realization(sample, declared) is False
        claims = audit_narrated_claims(
            sample,
            decision=decision,
            authored_corpus="",
            response_text=sample,
        )
        assert claims == []
        assert not any(code for code, pattern in _CONSEQUENTIAL_PATTERNS if pattern.search(sample))


def test_exact_authorized_wording_remains_accepted(opening):
    parsed = opening["parsed"]
    narration = _replace(opening["parsed"]["narration"], NOTICE_SENTENCE, SEED_NOTICE)
    narration = _replace(narration, CHOKE_SENTENCE, CHOKE_FACT)
    audit = _audit(narration, parsed["declared_claims"], opening["decision"])
    assert audit["hard_valid"] is True
    assert audit["violations"] == []
