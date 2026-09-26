from __future__ import annotations

import pytest

from game.bounded_improvisation import (
    IMPROVISATION_AUTHORITY_KEY,
    accepted_bounded_improvisation_entries,
    attach_bounded_improvisation_evaluation,
    promote_accepted_bounded_improvisation,
    prompt_projection_for_bounded_improvisation,
    validate_bounded_improvisation_proposal,
)
from game.final_emission_narrative_authority import skip_narrative_authority_layer
import game.gm as _gm  # noqa: F401 - primes gm/gm_retry's circular import path.
from game.gm_retry import detect_retry_failures


pytestmark = pytest.mark.unit


def _scene() -> dict:
    return {
        "scene": {
            "id": "market_yard",
            "visible_facts": ["A soup seller works beside the covered pump."],
            "discoverable_clues": ["A coded mark is scratched under the pump handle."],
            "hidden_facts": ["The soup seller is a spy for the Cinder League."],
        }
    }


def _session() -> dict:
    return {"active_scene_id": "market_yard", "debug_traces": []}


def test_incidental_detail_promotes_and_projects_for_consistency():
    session = _session()
    scene = _scene()
    gm = {
        "player_facing_text": "The soup is barley, leek, and pepper broth.",
        "improvisation_proposals": [
            {
                "kind": "incidental_fact",
                "category": "food_composition",
                "content": "The soup is barley, leek, and pepper broth.",
                "scope": "scene",
                "consequence_level": "low",
                "source": "dm_improvisation",
            }
        ],
    }

    gm = attach_bounded_improvisation_evaluation(gm, session=session, scene=scene, world={}, resolution=None)
    result = promote_accepted_bounded_improvisation(gm, session=session, scene=scene, world={}, resolution=None)

    assert result["promoted_count"] == 1
    entries = accepted_bounded_improvisation_entries(session, scene_id="market_yard")
    assert entries[0]["kind"] == "incidental_fact"
    assert entries[0]["truth_status"] == "runtime_incidental"
    projection = prompt_projection_for_bounded_improvisation(session, scene_id="market_yard")
    assert projection["entries"][0]["content"] == "The soup is barley, leek, and pepper broth."


def test_npc_rumor_persists_as_claim_not_world_truth():
    session = _session()
    proposal = {
        "kind": "npc_claim",
        "category": "rumor",
        "content": "Travelers say wagons have gone missing beyond the old quarry.",
        "scope": "scene",
        "consequence_level": "low",
        "source": "npc:cart_driver",
        "speaker_id": "cart_driver",
        "epistemic_status": "hearsay",
    }
    gm = attach_bounded_improvisation_evaluation(
        {"player_facing_text": "A cart driver says wagons have gone missing beyond the old quarry.", "improvisation_proposals": [proposal]},
        session=session,
        scene=_scene(),
        world={},
        resolution={"kind": "question"},
    )
    promote_accepted_bounded_improvisation(gm, session=session, scene=_scene(), world={}, resolution={"kind": "question"})

    entry = accepted_bounded_improvisation_entries(session, scene_id="market_yard")[0]
    assert entry["kind"] == "npc_claim"
    assert entry["epistemic_status"] == "hearsay"
    assert entry["truth_status"] == "not_world_truth"


def test_consequential_mechanical_and_contradictory_proposals_reject():
    session = _session()
    scene = _scene()
    promote_accepted_bounded_improvisation(
        attach_bounded_improvisation_evaluation(
            {
                "improvisation_proposals": [
                    {
                        "kind": "incidental_fact",
                        "category": "food_composition",
                        "content": "The soup is barley, leek, and pepper broth.",
                        "scope": "scene",
                        "consequence_level": "low",
                    }
                ]
            },
            session=session,
            scene=scene,
            world={},
            resolution=None,
        ),
        session=session,
        scene=scene,
        world={},
        resolution=None,
    )

    unsafe_secret = validate_bounded_improvisation_proposal(
        {
            "kind": "incidental_fact",
            "category": "local_color",
            "content": "A secret passage under the pump leads to the duke's vault.",
            "scope": "scene",
            "consequence_level": "low",
        },
        session=session,
        scene=scene,
        world={},
    )
    mechanical = validate_bounded_improvisation_proposal(
        {
            "kind": "incidental_fact",
            "category": "mundane_service_detail",
            "content": "The bowl costs 3 cp and removes 1 hp of fatigue.",
            "scope": "scene",
            "consequence_level": "low",
        },
        session=session,
        scene=scene,
        world={},
    )
    contradiction = validate_bounded_improvisation_proposal(
        {
            "kind": "incidental_fact",
            "category": "food_composition",
            "content": "The soup is not barley, leek, and pepper broth.",
            "scope": "scene",
            "consequence_level": "low",
        },
        session=session,
        scene=scene,
        world={},
    )

    assert unsafe_secret.accepted is False
    assert "content:consequential_terms" in unsafe_secret.reason_codes
    assert mechanical.accepted is False
    assert "content:mechanical_authority" in mechanical.reason_codes
    assert contradiction.accepted is False
    assert "content:contradicts_existing" in contradiction.reason_codes


def test_final_emission_narrative_authority_accepts_valid_bounded_lane_only():
    gm = attach_bounded_improvisation_evaluation(
        {
            "player_facing_text": "The tea smells of mint and smoke.",
            "improvisation_proposals": [
                {
                    "kind": "incidental_fact",
                    "category": "sensory_detail",
                    "content": "The tea smells of mint and smoke.",
                    "scope": "scene",
                    "consequence_level": "low",
                }
            ],
        },
        session=_session(),
        scene=_scene(),
        world={},
        resolution=None,
    )
    assert skip_narrative_authority_layer(
        "The tea smells of mint and smoke.",
        {"enabled": True, "debug_inputs": {}},
        gm_output=gm,
        response_type_debug={},
    ) == "validated_bounded_improvisation"

    mixed = attach_bounded_improvisation_evaluation(
        {
            "player_facing_text": "The tea smells of mint and smoke. A secret cult owns the stall.",
            "improvisation_proposals": [
                {
                    "kind": "incidental_fact",
                    "category": "sensory_detail",
                    "content": "The tea smells of mint and smoke.",
                    "scope": "scene",
                    "consequence_level": "low",
                },
                {
                    "kind": "consequential_proposal",
                    "category": "local_color",
                    "content": "A secret cult owns the stall.",
                    "scope": "scene",
                    "consequence_level": "low",
                },
            ],
        },
        session=_session(),
        scene=_scene(),
        world={},
        resolution=None,
    )
    assert mixed[IMPROVISATION_AUTHORITY_KEY]["rejected_count"] == 1
    assert skip_narrative_authority_layer(
        "A secret cult owns the stall.",
        {"enabled": True, "debug_inputs": {}},
        gm_output=mixed,
        response_type_debug={},
    ) is None


def test_retry_does_not_collapse_valid_bounded_improvisation():
    gm = attach_bounded_improvisation_evaluation(
        {
            "player_facing_text": "The stablehand says the mare is called Chalk, a placid grey with a nicked ear.",
            "improvisation_proposals": [
                {
                    "kind": "incidental_fact",
                    "category": "background_npc_detail",
                    "content": "The mare is called Chalk, a placid grey with a nicked ear.",
                    "scope": "scene",
                    "consequence_level": "low",
                    "source": "npc:stablehand",
                    "speaker_id": "stablehand",
                }
            ],
        },
        session=_session(),
        scene=_scene(),
        world={"npcs": [{"id": "stablehand", "name": "Stablehand", "location": "market_yard"}]},
        resolution={"kind": "question", "prompt": "What can you tell me about that horse?"},
    )

    failures = detect_retry_failures(
        player_text="What can you tell me about that horse?",
        gm_reply=gm,
        scene_envelope=_scene(),
        session=_session(),
        world={"npcs": [{"id": "stablehand", "name": "Stablehand", "location": "market_yard"}]},
        resolution={"kind": "question", "prompt": "What can you tell me about that horse?"},
    )

    assert not [f for f in failures if f.get("failure_class") in {"unresolved_question", "npc_contract_failure", "scene_stall"}]
