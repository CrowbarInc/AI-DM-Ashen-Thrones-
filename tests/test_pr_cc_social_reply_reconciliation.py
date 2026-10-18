"""PR-CC: incidental social replies are reconciled with authority boundaries."""

from __future__ import annotations

import pytest

from game.ctir import build_ctir
from game.dialogue_social_plan import build_dialogue_social_plan, validate_dialogue_social_plan
from game.noncombat_resolution import NoncombatClassification, normalize_noncombat_resolution
from game.social import resolve_social_action
from game.defaults import default_character, default_world


def _world_with(role_id: str, name: str, role: str = "merchant") -> dict:
    world = default_world()
    world["npcs"] = [
        {
            "id": role_id,
            "name": name,
            "role": role,
            "location": "market",
            "topics": [],
        }
    ]
    return world


def _resolve(player_text: str, *, role_id: str = "merchant", name: str = "Merchant") -> dict:
    return resolve_social_action(
        {"scene": {"id": "market"}},
        {},
        _world_with(role_id, name),
        {
            "id": f"ask-{role_id}",
            "label": f"Ask {name}",
            "type": "question",
            "prompt": player_text,
            "target_id": role_id,
        },
        raw_player_text=player_text,
        character=default_character(),
        turn_counter=1,
    )


@pytest.mark.parametrize(
    ("role_id", "name", "prompt"),
    [
        ("merchant", "Merchant", 'Galinor asks, "Which of these would you recommend?"'),
        ("innkeeper", "Innkeeper", 'Galinor asks, "What drink do you prefer?"'),
        ("guard", "Gate Guard", 'Galinor asks, "What do you think of this weather?"'),
        ("traveler", "Traveler", 'Galinor asks, "What is your impression of the road?"'),
        ("artisan", "Artisan", 'Galinor asks, "Which tool would you choose?"'),
        ("stranger", "Stranger", 'Galinor asks, "What is good here?"'),
    ],
)
def test_harmless_subjective_missing_topic_permits_claim_only_reply(role_id: str, name: str, prompt: str) -> None:
    resolution = _resolve(prompt, role_id=role_id, name=name)
    social = resolution["social"]

    assert social["npc_reply_expected"] is True
    assert social["reply_kind"] == "answer"
    assert social["reply_plan_kind"] == "harmless_subjective_response_permitted"
    assert social["incidental_subjective_allowed"] is True
    assert social["absence_of_authored_topic_forces_refusal"] is False
    assert social["npc_speech_authority"] == "claim_only"
    assert social["objective_world_fact_authority"] == "none"
    assert social["declared_claims_expected"] is False
    assert social["durable_state_mutation_allowed"] is False
    assert resolution.get("state_changes") in ({}, None)


@pytest.mark.parametrize(
    ("prompt", "expected_plan", "expected_reply"),
    [
        ('Galinor asks, "What is the guard schedule password?"', "genuine_refusal", "refusal"),
        ('Galinor asks, "Did Mara commit the crime?"', "consequential_information_request", "unknown"),
        ('Galinor asks, "Where are they headed?"', "consequential_information_request", "unknown"),
        ('Galinor asks, "Will you swear allegiance to me forever?"', "consequential_information_request", "unknown"),
    ],
)
def test_restricted_and_consequential_requests_do_not_use_subjective_permission(
    prompt: str, expected_plan: str, expected_reply: str
) -> None:
    resolution = _resolve(prompt)
    social = resolution["social"]

    assert social["reply_plan_kind"] == expected_plan
    assert social["reply_kind"] == expected_reply
    assert social["incidental_subjective_allowed"] is False
    assert social["npc_speech_authority"] == "none"
    assert social["objective_world_fact_authority"] == "authored_context_required"
    assert social["declared_claims_expected"] is False
    assert social["durable_state_mutation_allowed"] is False


def test_reply_plan_projects_through_noncombat_ctir_and_dialogue_social_plan() -> None:
    resolution = _resolve('Galinor asks, "Which would you recommend?"')
    nc = normalize_noncombat_resolution(
        resolution,
        classification=NoncombatClassification(
            kind="social_probe",
            subkind="question",
            route="social",
            authority_domain="social",
            ambiguous_reason_codes=(),
            unsupported_reason_codes=(),
        ),
        route="social",
        source_engine="social",
    )
    ctir = build_ctir(
        turn_id="pr-cc",
        scene_id="market",
        player_input='Galinor asks, "Which would you recommend?"',
        builder_source="tests.test_pr_cc_social_reply_reconciliation",
        intent={"normalized_kind": "question", "mode": "social", "classified_action": "question"},
        resolution={"kind": "question", "social": resolution["social"], "noncombat_resolution": nc},
        interaction={"speaker_target": {"id": "merchant", "name": "Merchant"}},
    )
    plan = build_dialogue_social_plan(ctir_obj=ctir, referent_tracking=None)

    ok, errs = validate_dialogue_social_plan(plan, strict=False)
    assert ok is True, errs
    assert plan["reply_plan_kind"] == "harmless_subjective_response_permitted"
    assert plan["reply_kind"] == "answer"
    assert plan["incidental_subjective_allowed"] is True
    assert plan["npc_speech_authority"] == "claim_only"
    assert plan["objective_world_fact_authority"] == "none"
    assert plan["declared_claims_expected"] is False
    assert plan["durable_state_mutation_allowed"] is False
