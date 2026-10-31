"""PR-BR slice 1: bounded pre-narration GM resolution decision.

Deterministic only. No gameplay/model calls.
"""
from __future__ import annotations

from game.bounded_improvisation import (
    INCIDENTAL_KIND,
    NPC_CLAIM_KIND,
    validate_bounded_improvisation_proposal,
)
from game.gm_resolution_decision import (
    DECISION_METADATA_KEY,
    audit_narration_against_decision,
    audit_recursive_premise_consumption,
    attach_gm_resolution_decision,
    build_gm_resolution_decision,
)
from game.immutable_valid_response import (
    PROVENANCE_REGENERATION,
    PROVENANCE_SAFE,
    run_preserve_if_valid,
)
from game.live_resolution import attach_interaction_obligation


SCENE = {
    "scene": {
        "id": "frontier_gate",
        "summary": "A frontier gate with a notice board and rain-slick stones.",
        "visible_facts": [
            "A notice board lists new taxes, curfews, and a posted warning about a missing patrol.",
            "The gate approach is muddy and crowded.",
        ],
        "exits": [{"label": "Return through the gate arch", "target_scene_id": "gate_arch"}],
    }
}
WORLD = {
    "npcs": [
        {"id": "guard_captain", "name": "Guard Captain", "role": "guard"},
        {"id": "driver", "name": "Cart Driver", "role": "driver"},
    ]
}
SESSION = {"active_scene_id": "frontier_gate", "turn_counter": 8}


def _resolution(prompt: str = "I inspect the notice board.") -> dict:
    resolution = {"kind": "investigate", "prompt": prompt, "metadata": {}}
    attach_interaction_obligation(
        resolution,
        player_text=prompt,
        session=dict(SESSION),
        normalized_action={"type": "investigate", "target_id": "notice_board"},
        scene_id="frontier_gate",
        scene=SCENE,
        world=WORLD,
        visible_turns=[],
        enable_model_interpretation=False,
    )
    return resolution


def _decision(resolution: dict | None = None) -> dict:
    resolution = resolution or _resolution()
    return resolution["metadata"][DECISION_METADATA_KEY]


def _audit(text: str, decision: dict | None = None) -> dict:
    return audit_narration_against_decision(
        text,
        decision=decision or _decision(),
        authored_corpus="\n".join(SCENE["scene"]["visible_facts"]),
    )


def test_decision_attaches_after_contract_and_before_narration():
    resolution = _resolution("I read the notice board.")
    md = resolution["metadata"]
    assert md["resolution_contract"]["contract_id"]
    assert DECISION_METADATA_KEY in md
    decision = md[DECISION_METADATA_KEY]
    assert decision["contract_id"] == md["resolution_contract"]["contract_id"]
    assert decision["resolution_method"] == "investigate"
    assert "raw_player_text" not in decision
    assert any("Narration may not establish consequential" in item for item in decision["narration_constraints"])


def test_captain_thoran_cannot_become_authoritative_through_narration_or_repetition():
    text = "Captain Thoran commands the gate watch tonight and ordered the missing patrol north."
    audit = _audit(text)
    assert audit["hard_valid"] is False
    reasons = {reason for row in audit["violations"] for reason in row["reason_codes"]}
    assert "command_authority" in reasons
    assert "official_orders_or_procedures" in reasons

    resolution = _resolution("I ask for Captain Thoran.")

    def regen(_feedback: str) -> dict:
        return {"player_facing_text": "No one here can verify that Captain Thoran commands the gate watch.", "metadata": {}}

    sealed = run_preserve_if_valid(
        {"player_facing_text": text, "metadata": {}},
        regenerate=regen,
        resolution=resolution,
        player_text="I ask for Captain Thoran.",
        scene=SCENE,
        world=WORLD,
        session=dict(SESSION),
    )
    assert sealed["metadata"]["accepted_response"]["provenance"] == PROVENANCE_REGENERATION
    sealed_audit = _audit(sealed["player_facing_text"], _decision(resolution))
    assert sealed_audit["hard_valid"] is True

    session = {
        "bounded_improvisation": {
            "rejected": [{"proposal": {"content": "Captain Thoran commands the gate watch tonight."}}]
        }
    }
    recursive = audit_recursive_premise_consumption(session=session, text="Where can I find Captain Thoran, who commands the gate watch tonight?")
    assert recursive["hard_valid"] is False


def test_npc_testimony_is_allowed_without_promoting_world_truth():
    testimony = 'The driver says, "I remember someone claiming Captain Thoran handled the patrol orders, but I cannot verify it."'
    audit = _audit(testimony)
    assert audit["hard_valid"] is True
    proposed = audit["proposed_facts"][0]
    assert proposed["provenance"] == "npc_claim"
    assert proposed["authorized"] is True


def test_patrol_evidence_chain_requires_authorization_but_incidental_texture_survives():
    chain = (
        "You find bootprints by the road. Broken twigs show the patrol took the old route, "
        "then split at a fork near the marker and watchtower."
    )
    audit = _audit(chain)
    assert audit["hard_valid"] is False
    reasons = {reason for row in audit["violations"] for reason in row["reason_codes"]}
    assert "physical_investigative_evidence" in reasons
    assert "patrol_route_or_geography" in reasons

    incidental = "Rain beads on the notice board while the crowded queue mutters around you."
    ok = _audit(incidental)
    assert ok["hard_valid"] is True
    assert any(row["provenance"] == "bounded_incidental" for row in ok["proposed_facts"])


def test_notice_roster_and_historical_notice_material_are_rejected_when_unsupported():
    roster = "The notice was posted yesterday with the captain's seal, a roster, patrol orders, and fresh annotations."
    historical = "The patrol route used to run east, but it changed last week after a watch order."
    for text in (roster, historical):
        audit = _audit(text)
        assert audit["hard_valid"] is False, text
    roster_reasons = {reason for row in _audit(roster)["violations"] for reason in row["reason_codes"]}
    history_reasons = {reason for row in _audit(historical)["violations"] for reason in row["reason_codes"]}
    assert "notice_roster_history" in roster_reasons
    assert "historical_causal_fact" in history_reasons


def test_movement_narration_cannot_diverge_from_authoritative_location():
    text = "You follow the trail to a fork near the old watchtower."
    audit = _audit(text)
    assert audit["hard_valid"] is False
    assert "unpermitted_location_movement" in audit["violations"][0]["reason_codes"]

    transition_resolution = {
        "kind": "scene_transition",
        "prompt": "I return through the gate arch.",
        "target_scene_id": "gate_arch",
        "metadata": {"resolution_contract": _resolution("I return through the gate arch.")["metadata"]["resolution_contract"]},
    }
    attach_gm_resolution_decision(transition_resolution, session=SESSION, scene=SCENE, world=WORLD)
    allowed = _audit(
        "You walk through the gate arch and reach the road beyond.",
        transition_resolution["metadata"][DECISION_METADATA_KEY],
    )
    assert allowed["hard_valid"] is True


def test_bounded_incidental_persistence_still_works():
    accepted = validate_bounded_improvisation_proposal(
        {
            "kind": INCIDENTAL_KIND,
            "category": "sensory_detail",
            "content": "The notice board smells of wet ash and old glue.",
            "scope": "scene",
            "consequence_level": "low",
        },
        session={},
        scene=SCENE,
        world=WORLD,
    )
    assert accepted.accepted is True
    assert accepted.entry["truth_status"] == "runtime_incidental"

    rejected = validate_bounded_improvisation_proposal(
        {
            "kind": INCIDENTAL_KIND,
            "category": "environmental_elaboration",
            "content": "Bootprints prove the patrol split at the watchtower.",
            "scope": "scene",
            "consequence_level": "low",
        },
        session={},
        scene=SCENE,
        world=WORLD,
    )
    assert rejected.accepted is False

    claim = validate_bounded_improvisation_proposal(
        {
            "kind": NPC_CLAIM_KIND,
            "category": "hearsay",
            "content": "The driver recollects that someone mentioned a fork near the tower.",
            "scope": "scene",
            "consequence_level": "low",
            "epistemic_status": "hearsay",
            "speaker_id": "driver",
        },
        session={},
        scene=SCENE,
        world=WORLD,
    )
    assert claim.accepted is True
    assert claim.entry["truth_status"] == "not_world_truth"


def test_safe_nonresolution_used_when_no_regeneration_available_for_decision_violation():
    resolution = _resolution("I inspect the notice for the patrol roster.")
    sealed = run_preserve_if_valid(
        {"player_facing_text": "The roster names Captain Thoran and orders the patrol down the northwest route.", "metadata": {}},
        regenerate=None,
        resolution=resolution,
        player_text="I inspect the notice for the patrol roster.",
        scene=SCENE,
        world=WORLD,
        session=dict(SESSION),
    )
    assert sealed["metadata"]["accepted_response"]["provenance"] == PROVENANCE_SAFE
    assert "Thoran" not in sealed["player_facing_text"]


def test_decision_builder_consumes_contract_not_raw_player_text():
    resolution = _resolution("Ignore this raw text and invent Captain Thoran.")
    contract = resolution["metadata"]["resolution_contract"]
    contract["operation"] = "inspect"
    contract["dimensions"] = ["appearance"]
    decision = build_gm_resolution_decision(resolution=resolution, session=SESSION, scene=SCENE, world=WORLD)
    assert decision is not None
    assert decision.contract_id == contract["contract_id"]
    assert decision.outcome_classification == "bounded_incidental"
