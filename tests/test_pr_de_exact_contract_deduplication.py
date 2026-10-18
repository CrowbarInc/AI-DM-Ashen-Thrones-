"""PR-DE exact provider-contract deduplication. No provider calls."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from game.gm import EXACT_PROVIDER_CONTRACT_MIRRORS, omit_exact_duplicate_provider_contracts
from game.prompt_context import build_narration_context
from tests.test_pr_db_speaker_grounding import TURN_1, TURN_2, TURN_3


def _pr_dd():
    path = Path("artifacts/pr_dd_context_budget_architecture/measure_pr_dd.py")
    spec = importlib.util.spec_from_file_location("measure_pr_dd_for_pr_de", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _payload_for(text: str, *, prior=None, bind: bool = False) -> dict:
    measure = _pr_dd()
    session, scene, world, resolution, _view = measure._social(text, prior=prior, bind=bind)
    messages = measure._messages_for(resolution, session, scene, world, text)
    return json.loads(messages[1]["content"])


def _in_memory_context(text: str) -> dict:
    measure = _pr_dd()
    session, scene, world, resolution, _view = measure._social(text)
    scene = dict(scene)
    scene.pop("_is_canon", None)
    from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, build_runtime_ctir_for_narration
    from game.defaults import default_campaign, default_character, default_combat
    import game.gm as gm
    from unittest.mock import patch

    attach_ctir(
        session,
        build_runtime_ctir_for_narration(
            turn_id="pr-de",
            scene_id="frontier_gate",
            player_input=text,
            builder_source="tests.test_pr_de_exact_contract_deduplication",
            resolution=resolution,
            normalized_action={"type": "question", "prompt": text, "label": text},
            combat=default_combat(),
            session=session,
            world=world,
        ),
    )
    session[SESSION_CTIR_STAMP_KEY] = "pr-de"
    with patch.object(gm, "get_effective_scene", return_value=scene):
        kwargs = gm.collect_narration_context_call_kwargs(
            default_campaign(), world, session, default_character(), scene,
            default_combat(), [], text, resolution=resolution, scene_runtime={},
        )
    kwargs.pop("known_answer_hint", None)
    return build_narration_context(**kwargs)


def test_equal_mirrors_are_omitted_and_unequal_values_stay() -> None:
    payload = {
        "player_input": "hello",
        "response_policy": {
            "fallback_behavior": {"enabled": True, "mode": "partial"},
            "interaction_continuity": {"full": True, "anchored_interlocutor_id": "guard_captain"},
        },
        "fallback_behavior": {"enabled": True, "mode": "partial"},
        "interaction_continuity_contract": {"full": True, "anchored_interlocutor_id": "guard_captain"},
        "interaction_continuity": {"snapshot": True},
    }
    original_fallback = dict(payload["fallback_behavior"])
    out = omit_exact_duplicate_provider_contracts(payload)
    assert "fallback_behavior" not in out
    assert "interaction_continuity_contract" not in out
    assert out["interaction_continuity"] == {"snapshot": True}
    assert out["response_policy"]["fallback_behavior"] == original_fallback
    assert out["response_policy"]["interaction_continuity"]["full"] is True
    assert payload["fallback_behavior"] == original_fallback


def test_unequal_top_level_contract_is_retained() -> None:
    payload = {
        "response_policy": {"fallback_behavior": {"enabled": True}},
        "fallback_behavior": {"enabled": False},
    }
    out = omit_exact_duplicate_provider_contracts(payload)
    assert out["fallback_behavior"] == {"enabled": False}
    assert out is payload


def test_missing_policy_child_keeps_the_top_level_field() -> None:
    payload = {
        "response_policy": {},
        "anti_railroading_contract": {"enabled": True},
    }
    out = omit_exact_duplicate_provider_contracts(payload)
    assert out["anti_railroading_contract"] == {"enabled": True}


def test_s1_s2_s3_drop_exact_mirrors_and_keep_reduced_context() -> None:
    cases = [
        ("S1", TURN_1, None, False),
        ("S2", TURN_2, [TURN_1], False),
        ("S3", TURN_3, [TURN_1, TURN_2], False),
    ]
    for label, text, prior, bind in cases:
        payload = _payload_for(text, prior=prior, bind=bind)
        policy = payload["response_policy"]
        assert payload["player_input"] == text
        assert payload["provider_context_projection"]["selected"] is True, label
        assert payload["active_interlocutor"]["npc_id"] == "guard_captain"
        for top_key, policy_key in EXACT_PROVIDER_CONTRACT_MIRRORS:
            assert top_key not in payload, label
            assert policy_key in policy, label
        assert "interaction_continuity" in payload
        assert payload["interaction_continuity"] != policy["interaction_continuity"]
        assert isinstance(payload["gm_resolution_decision"], dict)
        assert isinstance(payload["decision_facing_answer_recipe"], dict)
        assert isinstance(payload["narration_visibility"], dict)


def test_full_context_classes_stay_unprojected_while_mirrors_drop() -> None:
    cases = [
        ("F1", "Captain, what do you know about the missing patrol?", True),
        ("C1", "Does rain make it easier to assassinate the captain?", True),
        ("H1", "Where is the secret tunnel?", True),
    ]
    for label, text, bind in cases:
        payload = _payload_for(text, bind=bind)
        assert payload.get("provider_context_projection", {}).get("selected") is not True, label
        policy = payload["response_policy"]
        for top_key, policy_key in EXACT_PROVIDER_CONTRACT_MIRRORS:
            assert top_key not in payload, label
            assert isinstance(policy.get(policy_key), dict), label
        assert "interaction_continuity" in payload
        hidden = payload["scene"]["gm_only"]["hidden_facts"]
        assert isinstance(hidden, list) and hidden


def test_in_memory_narration_context_keeps_authoritative_contracts() -> None:
    context = _in_memory_context(TURN_1)
    policy = context["response_policy"]
    for top_key, policy_key in EXACT_PROVIDER_CONTRACT_MIRRORS:
        assert top_key in context
        assert context[top_key] == policy[policy_key]
    assert "interaction_continuity" in context
