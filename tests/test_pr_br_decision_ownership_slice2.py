"""PR-BR slice 2: decision-owned fictional outcome authority.

Deterministic only. No gameplay/model calls.
"""
from __future__ import annotations

from game.bounded_improvisation import (
    INCIDENTAL_KIND,
    NPC_CLAIM_KIND,
    attach_bounded_improvisation_evaluation,
    promote_accepted_bounded_improvisation,
)
from game.gm_resolution_decision import (
    DECISION_METADATA_KEY,
    audit_narration_against_decision,
    audit_recursive_premise_consumption,
    attach_gm_resolution_decision,
    build_gm_resolution_decision,
)


BASE_SCENE = {
    "scene": {
        "id": "river_market",
        "summary": "A riverside market with a bridge, shrine, well, and warehouses.",
        "visible_facts": ["Rain darkens the river stones beside the market well."],
        "exits": [{"label": "Cross toward River Arch", "target_scene_id": "river_arch"}],
    }
}
BASE_WORLD = {"npcs": [{"id": "mason", "name": "Mira the Mason", "role": "mason"}]}
BASE_SESSION = {"active_scene_id": "river_market", "turn_counter": 4}


def _resolution(contract_id: str = "rc_slice2", operation: str = "inspect") -> dict:
    return {
        "kind": operation,
        "metadata": {
            "resolution_contract": {
                "contract_id": contract_id,
                "operation": operation,
                "dimensions": ["appearance"],
            }
        },
    }


def _decision(scene: dict | None = None, session: dict | None = None, resolution: dict | None = None) -> dict:
    res = resolution or _resolution()
    attach_gm_resolution_decision(
        res,
        session=session if session is not None else dict(BASE_SESSION),
        scene=scene or BASE_SCENE,
        world=BASE_WORLD,
    )
    return res["metadata"][DECISION_METADATA_KEY]


def _audit(text: str, decision: dict | None = None, scene: dict | None = None) -> dict:
    facts = (scene or BASE_SCENE)["scene"].get("visible_facts") or []
    return audit_narration_against_decision(
        text,
        decision=decision or _decision(scene=scene),
        authored_corpus="\n".join(facts),
    )


def test_novel_domain_unsupported_world_truth_is_blocked_without_gate_nouns():
    samples = [
        "The old bridge collapsed yesterday.",
        "The merchant belongs to a smuggling ring.",
        "There is a hidden crypt below the shrine.",
        "The well has been poisoned.",
        "The guild controls the warehouse.",
        "The healer treated the named fugitive before dawn.",
    ]
    for text in samples:
        audit = _audit(text)
        assert audit["hard_valid"] is False, text
        reasons = {reason for row in audit["violations"] for reason in row["reason_codes"]}
        assert "unowned_stateful_world_assertion" in reasons


def test_authored_novel_domain_world_truth_is_authorized_by_pre_narration_decision():
    scene = {
        "scene": {
            **BASE_SCENE["scene"],
            "visible_facts": [
                "The old bridge collapsed yesterday.",
                "The guild controls the warehouse.",
            ],
        }
    }
    decision = _decision(scene=scene)
    texts = " ".join(row["text"] for row in decision["proposed_facts"])
    assert "old bridge collapsed yesterday" in texts.lower()
    assert "guild controls the warehouse" in texts.lower()

    for text in ("The old bridge collapsed yesterday.", "The guild controls the warehouse."):
        audit = _audit(text, decision=decision, scene=scene)
        assert audit["hard_valid"] is True, audit
        assert audit["proposed_facts"][0]["authority"] == "world_truth"
        assert audit["proposed_facts"][0]["source_ref"].startswith("scene.visible_facts")


def test_npc_claim_version_remains_epistemic_not_world_truth():
    audit = _audit('Mira says, "I heard the old bridge might have collapsed yesterday, but I cannot verify it."')
    assert audit["hard_valid"] is True
    assert audit["proposed_facts"]
    row = audit["proposed_facts"][0]
    assert row["provenance"] == "npc_claim"
    assert row["authority"] == "claim_only"
    assert row["persistence"] == "claim_only"


def test_rejected_novel_premise_does_not_gain_authority_through_player_repetition():
    session = {
        "bounded_improvisation": {
            "rejected": [
                {
                    "proposal": {
                        "content": "The old bridge collapsed yesterday.",
                        "kind": "consequential_proposal",
                    }
                }
            ]
        }
    }
    recursive = audit_recursive_premise_consumption(
        session=session,
        text="If the old bridge collapsed yesterday, who repaired it?",
    )
    assert recursive["hard_valid"] is False

    decision = _decision(session=session)
    assert _audit("The old bridge collapsed yesterday.", decision=decision)["hard_valid"] is False


def test_accepted_incidental_and_npc_claim_project_into_next_decision_without_promotion():
    session = dict(BASE_SESSION)
    gm = attach_bounded_improvisation_evaluation(
        {
            "player_facing_text": 'The bridge rail is damp with rain. Mira says, "The well might be tainted."',
            "improvisation_proposals": [
                {
                    "kind": INCIDENTAL_KIND,
                    "category": "sensory_detail",
                    "content": "The bridge rail is damp with rain.",
                    "scope": "scene",
                    "consequence_level": "low",
                },
                {
                    "kind": NPC_CLAIM_KIND,
                    "category": "rumor",
                    "content": "The well might be tainted.",
                    "scope": "scene",
                    "consequence_level": "low",
                    "speaker_id": "mason",
                    "epistemic_status": "rumor",
                },
            ],
        },
        session=session,
        scene=BASE_SCENE,
        world=BASE_WORLD,
        resolution=_resolution(),
    )
    promoted = promote_accepted_bounded_improvisation(
        gm,
        session=session,
        scene=BASE_SCENE,
        world=BASE_WORLD,
        resolution=_resolution(),
    )
    assert promoted["promoted_count"] == 2

    decision = _decision(session=session)
    rows = {row["text"]: row for row in decision["proposed_facts"]}
    assert rows["The bridge rail is damp with rain."]["authority"] == "bounded_incidental"
    assert rows["The well might be tainted."]["authority"] == "claim_only"

    assert _audit("The bridge rail is damp with rain.", decision=decision)["hard_valid"] is True
    claim = _audit('Mira says, "The well might be tainted."', decision=decision)
    assert claim["hard_valid"] is True
    assert claim["proposed_facts"][0]["authority"] == "claim_only"
    assert _audit("The well is poisoned.", decision=decision)["hard_valid"] is False


def test_movement_is_pre_narration_state_outcome_not_posthoc_phrase_detection():
    blocked = _audit("You make your way across and arrive at River Arch.")
    assert blocked["hard_valid"] is False
    assert "unpermitted_location_movement" in blocked["violations"][0]["reason_codes"]

    transition = {
        "kind": "scene_transition",
        "target_scene_id": "river_arch",
        "metadata": {"resolution_contract": _resolution(operation="follow")["metadata"]["resolution_contract"]},
    }
    decision = _decision(resolution=transition)
    assert any(row["outcome_classification"] == "authorized_state_outcome" for row in decision["proposed_facts"])
    allowed = _audit("You make your way across and arrive at River Arch.", decision=decision)
    assert allowed["hard_valid"] is True


def test_decision_object_declares_unresolved_consequential_outcome_before_narration():
    decision = build_gm_resolution_decision(
        resolution=_resolution(operation="follow"),
        session=BASE_SESSION,
        scene=BASE_SCENE,
        world=BASE_WORLD,
    )
    assert decision is not None
    assert decision.outcome_classification == "consequentially_unresolved"
    assert decision.unresolved_consequential_questions == ["requested_consequence_not_established"]
    assert decision.authority_algorithm == "proposition_claim_control_v1"
