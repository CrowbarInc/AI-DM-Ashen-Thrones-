"""PR-CE: ordinary subjective preference questions stay claim-only.

The classifier may authorize bounded NPC speech. It does not choose the words
the NPC must say, and preference grammar does not bypass restricted or
consequential information.
"""

from __future__ import annotations

import pytest

from game.ctir import build_ctir
from game.defaults import default_character, default_world
from game.dialogue_social_plan import build_dialogue_social_plan, validate_dialogue_social_plan
from game.noncombat_resolution import NoncombatClassification, normalize_noncombat_resolution
from game.social import apply_social_topic_escalation_to_resolution, resolve_social_action


def _world_with(role_id: str, name: str, role: str) -> dict:
    world = default_world()
    world["npcs"] = [
        {
            "id": role_id,
            "name": name,
            "role": role,
            "location": "market",
            "disposition": "neutral",
            "topics": [],
        }
    ]
    return world


def _resolve(player_text: str, *, role_id: str, name: str, role: str, session: dict | None = None) -> dict:
    world = _world_with(role_id, name, role)
    live_session = session if session is not None else {}
    return resolve_social_action(
        {"scene": {"id": "market", "visible_facts": [f"A {role} is here."]}},
        live_session,
        world,
        {
            "id": f"ask-{role_id}",
            "label": f"Ask {name}",
            "type": "question",
            "prompt": player_text,
            "target_id": role_id,
        },
        raw_player_text=player_text,
        character=default_character(),
        turn_counter=int(live_session.get("turn_counter") or 1),
    )


def _assert_claim_only_subjective(social: dict) -> None:
    assert social["reply_plan_kind"] == "harmless_subjective_response_permitted"
    assert social["incidental_subjective_allowed"] is True
    assert social["npc_speech_authority"] == "claim_only"
    assert social["objective_world_fact_authority"] == "none"
    assert social["durable_state_mutation_allowed"] is False
    assert social["declared_claims_expected"] is False
    assert social["absence_of_authored_topic_forces_refusal"] is False
    for key in ("authored_answer", "preference_value", "durable_preference", "npc_must_say"):
        assert key not in social


@pytest.mark.parametrize(
    ("role_id", "name", "role", "prompt"),
    [
        ("baker", "Baker", "baker", "Baker, which loaf do you usually keep for yourself?"),
        ("innkeeper", "Innkeeper", "innkeeper", "Innkeeper, which meal do you usually pick?"),
        ("merchant", "Merchant", "merchant", "Merchant, which cloth do you like best?"),
        ("artisan", "Artisan", "artisan", "Artisan, which timber do you usually choose?"),
        ("traveler", "Traveler", "traveler", "Traveler, which road do you usually take?"),
        ("guard", "Gate Guard", "guard", "Guard, which view of the square do you prefer?"),
    ],
)
def test_ordinary_preference_questions_permit_claim_only_speech(
    role_id: str, name: str, role: str, prompt: str
) -> None:
    resolution = _resolve(prompt, role_id=role_id, name=name, role=role)
    social = resolution["social"]

    _assert_claim_only_subjective(social)
    assert social["reply_kind"] == "answer"
    assert resolution.get("state_changes") in ({}, None)


@pytest.mark.parametrize(
    ("prompt", "expected_plan"),
    [
        ("Which secret guard schedule do you prefer?", "genuine_refusal"),
        ("Which restricted entrance would you choose?", "genuine_refusal"),
        ("Which confidential faction plan do you like best?", "genuine_refusal"),
        ("Which suspect do you think committed the murder?", "consequential_information_request"),
        ("Which official order would you recommend forging?", "consequential_information_request"),
        ("Which hidden quest objective would you select?", "consequential_information_request"),
    ],
)
def test_preference_wording_does_not_bypass_restricted_or_consequential_authority(
    prompt: str, expected_plan: str
) -> None:
    resolution = _resolve(prompt, role_id="clerk", name="Clerk", role="clerk")
    social = resolution["social"]

    assert social["reply_plan_kind"] == expected_plan
    assert social["incidental_subjective_allowed"] is False
    assert social["npc_speech_authority"] == "none"
    assert social["objective_world_fact_authority"] == "authored_context_required"
    assert social["durable_state_mutation_allowed"] is False
    assert social["declared_claims_expected"] is False


def _project_plan(player_text: str, resolution: dict) -> dict:
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
        turn_id="pr-ce",
        scene_id="bread_stall",
        player_input=player_text,
        builder_source="tests.test_pr_ce_subjective_preference_classification",
        intent={"normalized_kind": "question", "mode": "social", "classified_action": "question"},
        resolution={"kind": "question", "social": resolution["social"], "noncombat_resolution": nc},
        interaction={"speaker_target": {"id": "baker", "name": "Baker"}},
    )
    plan = build_dialogue_social_plan(ctir_obj=ctir, referent_tracking=None)
    ok, errs = validate_dialogue_social_plan(plan, strict=False)
    assert ok is True, errs
    return plan


def pr_ca_replay_records() -> dict:
    world = _world_with("baker", "Baker", "baker")
    world["npcs"][0]["location"] = "bread_stall"
    world_before = [dict(row) for row in world["npcs"]]
    session: dict = {"turn_counter": 1}
    scene = {
        "scene": {
            "id": "bread_stall",
            "visible_facts": ["A baker stands beside loaves at a bread stall."],
            "addressables": [
                {"id": "baker", "name": "Baker", "addressable": True},
            ],
        }
    }
    turns = [
        "Baker, which loaf do you usually keep for yourself?",
        "Surely you have a favorite. What makes you reluctant to say?",
        "Fair enough. Which loaf would you recommend to someone who has never bought bread here?",
        "Thanks. I'll remember your recommendation.",
    ]
    evasive_replies = [
        "The baker says he prefers to keep that to himself.",
        "The baker says some things are better kept private.",
        "The baker declines to point to a loaf.",
    ]
    recent_log: list[dict] = []
    plans: list[dict] = []

    for index, player_text in enumerate(turns, start=1):
        session["turn_counter"] = index
        resolution = resolve_social_action(
            scene,
            session,
            world,
            {
                "id": f"pr-ca-t{index}",
                "label": "Ask Baker",
                "type": "question",
                "prompt": player_text,
                "target_id": "baker",
            },
            raw_player_text=player_text,
            character=default_character(),
            turn_counter=index,
        )
        apply_social_topic_escalation_to_resolution(
            world=world,
            session=session,
            scene=scene,
            user_text=player_text,
            resolution=resolution,
            recent_log=list(recent_log),
        )
        social = resolution["social"]
        plan = _project_plan(player_text, resolution)
        plans.append(
            {
                "turn": f"T{index}",
                "player_input": player_text,
                "prior_evasive_history_present": bool(recent_log),
                "social": social,
                "plan": plan,
                "state_changes": resolution.get("state_changes"),
            }
        )
        if index < 4:
            recent_log.append(
                {
                    "player_input": player_text,
                    "gm_snippet": evasive_replies[index - 1],
                }
            )

    runtime = session.get("npc_runtime") or {}
    baker_runtime = runtime.get("baker") or {}
    return {
        "world_before": world_before,
        "world_after": world["npcs"],
        "baker_runtime": baker_runtime,
        "recent_log": recent_log,
        "plans": plans,
    }


def test_pr_ca_replay_prefers_claim_only_speech_without_promoting_t4() -> None:
    replay = pr_ca_replay_records()
    plans = replay["plans"]
    world_before = replay["world_before"]
    baker_runtime = replay["baker_runtime"]

    assert plans[0]["prior_evasive_history_present"] is False
    assert all(item["prior_evasive_history_present"] is True for item in plans[1:])
    for item in plans[:3]:
        _assert_claim_only_subjective(item["social"])
        _assert_claim_only_subjective(item["plan"])
        assert item["social"]["reply_plan_kind"] == item["plan"]["reply_plan_kind"]

    t4_social = plans[3]["social"]
    t4_plan = plans[3]["plan"]
    assert t4_social["reply_plan_kind"] == "genuine_uncertainty"
    assert t4_plan["reply_plan_kind"] == "genuine_uncertainty"
    assert t4_social["incidental_subjective_allowed"] is False
    assert t4_social["npc_speech_authority"] == "none"
    assert t4_social["objective_world_fact_authority"] == "none"
    assert t4_social["durable_state_mutation_allowed"] is False
    assert t4_social["declared_claims_expected"] is False
    assert t4_plan["objective_world_fact_authority"] == "none"
    assert replay["world_after"] == world_before
    assert "preference" not in baker_runtime
    assert "favorite" not in baker_runtime
    assert baker_runtime.get("topics") in (None, [])
    assert not any(str(key).startswith("durable_preference") for key in baker_runtime)
