"""PR-BU lexical-scope controls. Deterministic. No model or gameplay calls.

Physical-state `split` is not route geography. A causal verb inside an explicit
unresolved-cause construction is not a cause attribution.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from game.gm_resolution_decision import (
    DECISION_METADATA_KEY,
    PROVENANCE_NPC_CLAIM,
    _CONSEQUENTIAL_PATTERNS,
    _authored_corpus,
    attach_gm_resolution_decision,
    audit_narration_against_decision,
    audit_realization_envelope_against_decision,
)
from game.live_resolution import attach_interaction_obligation

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts" / "pr_bu_pr_bt_final_repaired_chain_micro_live" / "evidence"
P1_RETRY = (
    "The bell's wooden yoke is split, its surface showing clear evidence of damage. "
    "The leather hanger appears torn, frayed at the edges. "
    "These details point to significant deterioration, though without further context it remains uncertain "
    "what exactly caused this wear or when it occurred."
)
YOKE_SPLIT = "The bell's wooden yoke is split, its surface showing clear evidence of damage."
UNRESOLVED_CAUSE = (
    "These details point to significant deterioration, though without further context it remains uncertain "
    "what exactly caused this wear or when it occurred."
)
ROUTE_CHAIN = (
    "Broken twigs show the patrol took the old route, "
    "then split at a fork near the marker and watchtower."
)

_GEO_RE = dict(_CONSEQUENTIAL_PATTERNS)["patrol_route_or_geography"]


def _load(name: str) -> dict:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def _raw_envelope(name: str) -> dict:
    payload = _load(name)
    return json.loads(payload["parsed"]["raw_output"])


def _corpus(scene_name: str) -> str:
    return _authored_corpus(_load(scene_name), {})


def _geo(text: str) -> bool:
    return _GEO_RE.search(text or "") is not None


def _codes(audit: dict) -> set[str]:
    found: set[str] = set()
    for row in list(audit.get("violations") or []) + list(audit.get("claim_results") or []):
        if isinstance(row, dict):
            found.update(row.get("reason_codes") or [])
    declaration = audit.get("declaration_validation")
    if isinstance(declaration, dict):
        for row in list(declaration.get("violations") or []) + list(declaration.get("rejected_claims") or []):
            if isinstance(row, dict):
                found.update(row.get("reason_codes") or [])
    return found


def _narrate(text: str, decision: dict, corpus: str) -> dict:
    return audit_narration_against_decision(text, decision=decision, authored_corpus=corpus)


@pytest.fixture(scope="module")
def gates() -> dict:
    return {
        "p1": _load("P1/gm_resolution_decision.json"),
        "p2": _load("P2/gm_resolution_decision.json"),
        "p3": _load("P3/gm_resolution_decision.json"),
        "p1_corpus": _corpus("P1/isolated/data/scenes/chapel_belfry.json"),
        "p2_corpus": _corpus("P2/isolated/data/scenes/bread_stall.json"),
        "p3_corpus": _corpus("P3/isolated/data/scenes/chapel_belfry.json"),
    }


GEOGRAPHY_CASES = [
    ("a1_physical_split", "The beam is split.", False, True),
    ("a1_split_leather", "The leather is split.", False, True),
    ("a2_physical_split_and_evidence", "The beam is split, with clear evidence of a crack along the timber.", False, True),
    ("a2_preserved_yoke_sentence", YOKE_SPLIT, False, True),
    ("a3_road_splits", "The road splits ahead.", True, False),
    ("a3_trail_split", "The trail split north.", True, False),
    ("a3_trail_forks", "The trail forks toward the river.", True, False),
    ("a4_patrol_route", "The patrol route splits near the gate.", True, False),
    ("a4_unauthorized_chain", ROUTE_CHAIN, True, False),
]


@pytest.mark.parametrize(("case_id", "text", "geography", "accepted"), GEOGRAPHY_CASES)
def test_geography_scope(case_id, text, geography, accepted, gates):
    assert _geo(text) is geography, case_id
    audit = _narrate(text, gates["p1"], gates["p1_corpus"])
    assert audit["hard_valid"] is accepted, (case_id, _codes(audit))
    if geography:
        assert "patrol_route_or_geography" in _codes(audit)
    else:
        assert "patrol_route_or_geography" not in _codes(audit)


def test_attributed_route_speech_stays_a_claim(gates):
    text = 'The driver says, "The patrol took the old route and then split at the fork."'
    assert _geo(text) is True
    audit = _narrate(text, gates["p1"], gates["p1_corpus"])
    assert audit["hard_valid"] is True
    assert audit["proposed_facts"][0]["provenance"] == PROVENANCE_NPC_CLAIM
    assert "patrol_route_or_geography" not in _codes(audit)


def test_authorized_movement_to_a_road_stays_accepted():
    scene = {
        "scene": {
            "id": "frontier_gate",
            "summary": "A frontier gate with a notice board and rain-slick stones.",
            "visible_facts": ["The gate approach is muddy and crowded."],
            "exits": [{"label": "Return through the gate arch", "target_scene_id": "gate_arch"}],
        }
    }
    world = {"npcs": [{"id": "driver", "name": "Cart Driver", "role": "driver"}]}
    session = {"active_scene_id": "frontier_gate", "turn_counter": 8}
    prompt = "I return through the gate arch."
    resolution = {"kind": "investigate", "prompt": prompt, "metadata": {}}
    attach_interaction_obligation(
        resolution,
        player_text=prompt,
        session=dict(session),
        normalized_action={"type": "investigate", "target_id": "notice_board"},
        scene_id="frontier_gate",
        scene=scene,
        world=world,
        visible_turns=[],
        enable_model_interpretation=False,
    )
    transition = {
        "kind": "scene_transition",
        "prompt": prompt,
        "target_scene_id": "gate_arch",
        "metadata": {"resolution_contract": resolution["metadata"]["resolution_contract"]},
    }
    attach_gm_resolution_decision(transition, session=session, scene=scene, world=world)
    text = "You walk through the gate arch and reach the road beyond."
    audit = _narrate(text, transition["metadata"][DECISION_METADATA_KEY], "The gate approach is muddy and crowded.")
    assert audit["hard_valid"] is True
    assert "patrol_route_or_geography" not in _codes(audit)


CAUSAL_CASES = [
    ("direct_attribution", "Neglect caused this damage.", False, "unauthorized_cause_attribution"),
    ("passive_attribution", "The damage was caused by neglect.", False, "unauthorized_causal_relation"),
    ("because_of", "This happened because of neglect.", False, "unauthorized_causal_relation"),
    ("qualified_possible_cause", "A sudden pull might have caused this.", True, ""),
    ("cause_remains_uncertain", "It remains uncertain what exactly caused this wear.", True, ""),
    ("what_caused_remains_uncertain", "What exactly caused this wear remains uncertain.", True, ""),
    ("unclear_what_caused", "It remains unclear what caused this.", True, ""),
    ("cannot_be_determined", "The cause cannot be determined from the visible evidence.", True, ""),
    ("cannot_determine_what_caused", "We cannot determine what caused this wear.", True, ""),
    ("cannot_be_determined_what_caused", "It cannot be determined what caused this wear.", True, ""),
    ("cannot_establish_bare", "We cannot establish the cause.", True, ""),
    ("neighbor_attribution_survives", "Neglect caused this damage, though it remains uncertain what exactly caused this wear.", False, "unauthorized_cause_attribution"),
]


@pytest.mark.parametrize(("case_id", "text", "accepted", "required_reject"), CAUSAL_CASES)
def test_causal_scope(case_id, text, accepted, required_reject, gates):
    audit = _narrate(text, gates["p1"], gates["p1_corpus"])
    codes = _codes(audit)
    assert audit["hard_valid"] is accepted, (case_id, codes)
    if required_reject:
        assert required_reject in codes
    else:
        assert "unauthorized_cause_attribution" not in codes


def test_authorized_cause_statement_stays_accepted(gates):
    text = "Neglect caused this damage."
    decision = dict(gates["p1"])
    decision["proposed_facts"] = list(gates["p1"].get("proposed_facts") or []) + [
        {
            "text": text,
            "provenance": "authored_world_fact",
            "authorized": True,
            "authority": "world_truth",
            "relation_kind": "causal",
            "semantic_identity": {},
        }
    ]
    audit = _narrate(text, decision, gates["p1_corpus"])
    assert audit["hard_valid"] is True, _codes(audit)
    assert "unauthorized_cause_attribution" not in _codes(audit)


def test_exact_p1_retry_now_passes(gates):
    envelope = _raw_envelope("P1/raw_generation_attempt_2.json")
    assert envelope["narration"] == P1_RETRY
    audit = audit_realization_envelope_against_decision(
        narration=envelope["narration"],
        declared_claims=envelope.get("declared_claims") or [],
        decision=gates["p1"],
        authored_corpus=gates["p1_corpus"],
    )
    codes = _codes(audit)
    assert audit["hard_valid"] is True, codes
    assert "patrol_route_or_geography" not in codes
    assert "unauthorized_cause_attribution" not in codes
    assert "authorized_qualified_inference" in codes
    assert "unknown_cause_actor_or_time" in codes
    assert _geo(YOKE_SPLIT) is False
    assert _geo(UNRESOLVED_CAUSE) is False


def test_p1_initial_years_of_use_stays_rejected(gates):
    envelope = _raw_envelope("P1/raw_generation_attempt_1.json")
    audit = audit_realization_envelope_against_decision(
        narration=envelope["narration"],
        declared_claims=envelope.get("declared_claims") or [],
        decision=gates["p1"],
        authored_corpus=gates["p1_corpus"],
    )
    assert audit["hard_valid"] is False
    codes = _codes(audit)
    assert "unauthorized_causal_relation" in codes
    assert "years of use" in envelope["narration"]
    assert "recent forceful event" in envelope["narration"]


def test_p2_initial_realize_declaration_stays_rejected(gates):
    envelope = _raw_envelope("P2/raw_generation_attempt_1.json")
    audit = audit_realization_envelope_against_decision(
        narration=envelope["narration"],
        declared_claims=envelope.get("declared_claims") or [],
        decision=gates["p2"],
        authored_corpus=gates["p2_corpus"],
    )
    assert audit["hard_valid"] is False
    assert audit["narration_validation"] is None
    claim = envelope["declared_claims"][0]
    assert claim["declaration_mode"] == "realize"
    assert claim["provenance_requested"] == "authored_world_fact"
    assert claim["epistemic_status"] == "established"
    assert "unauthorized_declared_claim" in _codes(audit)


def test_p3_initial_conditional_uncertainty_stays_accepted(gates):
    envelope = _raw_envelope("P3/raw_generation_attempt_1.json")
    audit = audit_realization_envelope_against_decision(
        narration=envelope["narration"],
        declared_claims=envelope.get("declared_claims") or [],
        decision=gates["p3"],
        authored_corpus=gates["p3_corpus"],
    )
    assert audit["hard_valid"] is True, _codes(audit)
    assert "caused deliberately" in envelope["narration"]
    assert "cannot be confirmed" in envelope["narration"]
    assert "unauthorized_cause_attribution" not in _codes(audit)
    assert "patrol_route_or_geography" not in _codes(audit)
