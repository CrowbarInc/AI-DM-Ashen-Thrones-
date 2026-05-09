"""Mutation snapshots for ``game.gm.apply_response_policy_enforcement``."""
from __future__ import annotations

import pytest

from game.gm import (
    GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED,
    apply_response_policy_enforcement,
)
from game.realization_authority import FALLBACK_FAMILIES
from game.realization_provenance import REALIZATION_FALLBACK_FAMILY_FIELD
from game.response_policy_enforcement_manifest import (
    METADATA_ONLY_PROJECTION,
    REQUIRED_RESPONSE_POLICY_ENFORCEMENT_SUBPATHS,
    RESPONSE_POLICY_ENFORCEMENT_CLASSIFICATIONS,
    RESPONSE_POLICY_ENFORCEMENT_SUBPATHS,
    TEXT_MUTATING_ENFORCEMENT,
    response_policy_enforcement_subpath_keys,
)

pytestmark = pytest.mark.unit


def _scene() -> dict:
    return {
        "scene": {
            "id": "frontier_gate",
            "location": "Frontier Gate",
            "visible_facts": ["A notice board hangs beside the gatehouse arch."],
            "hidden_facts": ["Captain Veyra signed the sealed order."],
            "exits": [{"label": "East Road"}],
        }
    }


def _world() -> dict:
    return {
        "npcs": [
            {"id": "guard_captain", "name": "Captain Veyra", "location": "frontier_gate"},
        ]
    }


def _session() -> dict:
    return {
        "active_scene_id": "frontier_gate",
        "scene_runtime": {"frontier_gate": {}},
        "interaction_context": {
            "active_interaction_target_id": "guard_captain",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
            "engagement_level": "engaged",
            "conversation_privacy": None,
            "player_position_context": None,
        },
    }


def _neutral_session() -> dict:
    session = _session()
    session["interaction_context"] = {
        "active_interaction_target_id": None,
        "active_interaction_kind": None,
        "interaction_mode": "none",
        "engagement_level": "none",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    return session


def _gm(text: str) -> dict:
    return {
        "player_facing_text": text,
        "tags": ["existing_tag"],
        "metadata": {"existing_metadata": "kept"},
        "debug_notes": "existing_debug",
        "scene_update": None,
        "world_updates": None,
    }


def _policy(**overrides: object) -> dict:
    policy = {
        "must_answer": False,
        "forbid_state_invention": False,
        "forbid_secret_leak": False,
        "diegetic_only": False,
        "prefer_scene_momentum": False,
        "prefer_specificity": False,
    }
    policy.update(overrides)
    return policy


def _apply(
    gm: dict,
    policy: dict,
    *,
    player_text: str = "I wait.",
    resolution: dict | None = None,
    session: dict | None = None,
) -> dict:
    return apply_response_policy_enforcement(
        gm,
        response_policy=policy,
        player_text=player_text,
        scene_envelope=_scene(),
        session=session or _session(),
        world=_world(),
        resolution=resolution,
        discovered_clues=[],
    )


def _assert_existing_metadata_preserved(out: dict) -> None:
    assert out["metadata"]["existing_metadata"] == "kept"
    assert out["metadata"][GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED] is True


def _assert_family_if_present(out: dict) -> None:
    families = []
    if out.get(REALIZATION_FALLBACK_FAMILY_FIELD):
        families.append(out[REALIZATION_FALLBACK_FAMILY_FIELD])
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    if md.get(REALIZATION_FALLBACK_FAMILY_FIELD):
        families.append(md[REALIZATION_FALLBACK_FAMILY_FIELD])
    for family in families:
        assert family in FALLBACK_FAMILIES


def _assert_no_realization_family(out: dict) -> None:
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in out
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in out["metadata"]


def test_response_policy_enforcement_pass_through_preserves_text_and_marks_applied() -> None:
    base = _gm("Rain ticks against the gatehouse stones.")

    out = _apply(base, _policy())

    assert out["player_facing_text"] == base["player_facing_text"]
    assert out["debug_notes"] == "existing_debug"
    assert out["tags"] == ["existing_tag"]
    _assert_existing_metadata_preserved(out)
    _assert_no_realization_family(out)


def test_response_policy_enforcement_question_resolution_mutation_records_reason() -> None:
    base = _gm("Rain ticks against the gatehouse stones.")

    out = _apply(
        base,
        _policy(must_answer=True),
        player_text="Who signed the sealed order?",
        resolution={"kind": "adjudication_query", "prompt": "Who signed the sealed order?"},
    )

    assert out["player_facing_text"] != base["player_facing_text"]
    assert out["player_facing_text"].endswith(base["player_facing_text"])
    assert "question_resolution_rule" in out["tags"]
    assert "question_resolution_rule:enforced" in out["debug_notes"]
    _assert_existing_metadata_preserved(out)
    _assert_no_realization_family(out)


def test_response_policy_enforcement_npc_contract_mutation_records_missing_specificity() -> None:
    base = _gm("I cannot say.")

    out = _apply(
        base,
        _policy(prefer_specificity=True),
        player_text="Who signed the order?",
        resolution={
            "kind": "adjudication_query",
            "prompt": "Who signed the order?",
            "social": {"npc_id": "guard_captain", "npc_name": "Captain Veyra"},
        },
    )

    assert out["player_facing_text"] != base["player_facing_text"]
    assert out["player_facing_text"].startswith("I cannot say.")
    assert "Next step:" in out["player_facing_text"]
    assert "npc_response_contract" in out["tags"]
    assert "npc_response_contract:enforced" in out["debug_notes"]
    _assert_existing_metadata_preserved(out)
    _assert_no_realization_family(out)


def test_response_policy_enforcement_fallback_behavior_contract_is_metadata_only_here() -> None:
    base = _gm("No name comes clear from what shows.")
    contract = {
        "enabled": True,
        "uncertainty_active": True,
        "uncertainty_mode": "bounded_unknown",
        "uncertainty_sources": ["scene_context"],
        "allowed_behaviors": {"bounded_partial": True},
        "prefer_partial_over_question": True,
    }

    out = _apply(base, _policy(fallback_behavior=contract))

    assert out["player_facing_text"] == base["player_facing_text"]
    emitted = ((out.get("metadata") or {}).get("emission_debug") or {}).get("fallback_behavior_contract") or {}
    assert emitted["enabled"] is True
    assert emitted["uncertainty_active"] is True
    assert emitted["uncertainty_mode"] == "bounded_unknown"
    assert emitted["uncertainty_sources"] == ["scene_context"]
    assert emitted["allowed_behaviors"] == {"bounded_partial": True}
    assert emitted["prefer_partial_over_question"] is True
    _assert_existing_metadata_preserved(out)
    _assert_no_realization_family(out)


def test_response_policy_enforcement_validator_voice_mutation_records_rewrite_reason() -> None:
    base = _gm("As an AI language model, I cannot determine that.")

    out = _apply(
        base,
        _policy(diegetic_only=True, no_validator_voice={"enabled": True}),
        player_text="I wait.",
        resolution={"kind": "observe", "prompt": "I wait."},
        session=_neutral_session(),
    )

    assert out["player_facing_text"] != base["player_facing_text"]
    assert "As an AI" not in out["player_facing_text"]
    assert "validator_voice_rewrite" in out["tags"]
    assert "validator_voice_rewrite" in out["debug_notes"]
    _assert_existing_metadata_preserved(out)
    _assert_family_if_present(out)


def test_response_policy_enforcement_generic_phrase_mutation_records_rewrite_reason() -> None:
    base = _gm("Trust is hard to come by.")

    out = _apply(
        base,
        _policy(prefer_specificity=True),
        player_text="I watch the gate.",
        resolution={"kind": "observe", "prompt": "I watch the gate."},
        session=_neutral_session(),
    )

    assert out["player_facing_text"] != base["player_facing_text"]
    assert "Trust is hard to come by" not in out["player_facing_text"]
    assert "forbidden_generic_rewrite" in out["tags"]
    assert "forbidden_generic_rewrite" in out["debug_notes"]
    _assert_existing_metadata_preserved(out)
    _assert_no_realization_family(out)


def test_response_policy_enforcement_manifest_classifies_required_subpaths() -> None:
    keys = response_policy_enforcement_subpath_keys()
    assert len(keys) == len(set(keys))
    assert set(REQUIRED_RESPONSE_POLICY_ENFORCEMENT_SUBPATHS) <= set(keys)

    by_key = {item.key: item for item in RESPONSE_POLICY_ENFORCEMENT_SUBPATHS}
    for item in RESPONSE_POLICY_ENFORCEMENT_SUBPATHS:
        assert item.category in RESPONSE_POLICY_ENFORCEMENT_CLASSIFICATIONS
        if item.category == METADATA_ONLY_PROJECTION:
            assert item.mutates_player_facing_text is False
        if item.category == TEXT_MUTATING_ENFORCEMENT:
            assert item.mutates_player_facing_text is True

    assert by_key["fallback_behavior_contract"].category == METADATA_ONLY_PROJECTION
    assert by_key["question_resolution_enforcement"].mutates_player_facing_text is True
    assert by_key["npc_response_contract_enforcement"].mutates_player_facing_text is True
    assert by_key["validator_voice_rewrite"].mutates_player_facing_text is True
    assert by_key["forbidden_generic_phrase_rewrite"].mutates_player_facing_text is True
    assert by_key["scene_momentum_passive_escalation"].mutates_player_facing_text is True
    assert by_key["social_response_structure_handling"].mutates_player_facing_text is False
