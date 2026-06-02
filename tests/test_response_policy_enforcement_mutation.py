"""Mutation snapshots for ``game.response_policy_enforcement.apply_response_policy_enforcement``."""
from __future__ import annotations

import inspect
from contextlib import ExitStack
from unittest.mock import patch

import game.gm as gm_mod
import game.response_policy_enforcement as rpe_mod
import pytest

from game.gm import (
    GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED,
    _mark_response_policy_enforcement_applied,
    _normalize_response_policy_input,
    _project_fallback_behavior_contract_metadata,
    _snapshot_response_policy_and_project_fallback_contract,
    apply_response_policy_enforcement,
)
from game.realization_authority import FALLBACK_FAMILIES
from game.realization_provenance import REALIZATION_FALLBACK_FAMILY_FIELD
from game.response_policy_enforcement_manifest import (
    METADATA_ONLY_PROJECTION,
    REQUIRED_RESPONSE_POLICY_ENFORCEMENT_SUBPATHS,
    RESPONSE_POLICY_ENFORCEMENT_CLASSIFICATIONS,
    RESPONSE_POLICY_ENFORCEMENT_CONTRACT_HELPER_NAMES,
    RESPONSE_POLICY_ENFORCEMENT_GM_COMPAT_EXPORT_NAMES,
    RESPONSE_POLICY_ENFORCEMENT_ORCHESTRATION_SEQUENCE_FULL_POLICY,
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


def _scene_low_tension_surface() -> dict:
    """Scene snapshot without passive-pressure tension cues (for isolating momentum paths)."""
    return {
        "scene": {
            "id": "frontier_gate",
            "location": "Frontier Gate",
            "visible_facts": ["Empty cobbles stretch toward the gatehouse arch."],
            "hidden_facts": [],
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


def _session_topic_pressure_escalation_ready() -> dict:
    """Runtime state so topic-pressure escalation applies (repeat pressure + low progress)."""
    s = _neutral_session()
    rt = s["scene_runtime"]["frontier_gate"]
    rt["topic_pressure_current"] = {
        "topic_key": "missing_patrol",
        "speaker_key": "guard_captain",
        "interaction_kind": "social",
        "interaction_mode": "social",
        "social_intent_class": "social_exchange",
        "npc_name": "Captain Veyra",
    }
    rt["topic_pressure"] = {
        "missing_patrol": {
            "last_answer": "The eastern route is closed and guards refuse passes.",
            "speaker_targets": {
                "guard_captain": {
                    "repeat_count": 4,
                    "low_progress_streak": 0,
                    "patience": 3,
                },
            },
        },
    }
    rt["passive_action_streak"] = 0
    rt["momentum_exchanges_since"] = 0
    return s


def _session_passive_escalation_ready() -> dict:
    s = _neutral_session()
    rt = s["scene_runtime"]["frontier_gate"]
    rt["passive_action_streak"] = 2
    rt["momentum_exchanges_since"] = 0
    rt["momentum_next_due_in"] = 2
    return s


def _session_scene_momentum_due() -> dict:
    s = _neutral_session()
    rt = s["scene_runtime"]["frontier_gate"]
    rt["momentum_exchanges_since"] = 2
    rt["momentum_next_due_in"] = 2
    rt["passive_action_streak"] = 0
    return s


def _session_topic_progress_trackable() -> dict:
    """Valid topic-pressure context so ``_commit_topic_progress`` updates runtime."""
    s = _neutral_session()
    rt = s["scene_runtime"]["frontier_gate"]
    rt["topic_pressure_current"] = {
        "topic_key": "missing_patrol",
        "speaker_key": "__scene__",
        "interaction_kind": "social",
        "interaction_mode": "social",
        "social_intent_class": "social_exchange",
        "npc_name": "",
    }
    rt["topic_pressure"] = {
        "missing_patrol": {
            "last_answer": "",
            "progress_score_total": 0.0,
            "low_progress_streak": 0,
            "speaker_targets": {
                "__scene__": {
                    "repeat_count": 0,
                    "low_progress_streak": 0,
                    "patience": 3,
                },
            },
        },
    }
    return s


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
    scene_envelope: dict | None = None,
) -> dict:
    return apply_response_policy_enforcement(
        gm,
        response_policy=policy,
        player_text=player_text,
        scene_envelope=scene_envelope if scene_envelope is not None else _scene(),
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


def test_residual_inline_guard_secret_leak_keyword_sanitizes() -> None:
    """``guard_gm_output`` / keyword leak path (strict-social off for this fixture)."""
    base = _gm("The noble house ordered the curfew posted yesterday.")

    out = _apply(
        base,
        _policy(forbid_secret_leak=True),
        player_text="The noble house.",
        resolution={"kind": "observe", "prompt": "The noble house."},
        session=_neutral_session(),
    )

    assert out["player_facing_text"] != base["player_facing_text"]
    assert "noble house" not in out["player_facing_text"].lower()
    assert "spoiler_guard" in out["tags"]
    assert "spoiler_guard:" in out["debug_notes"]
    _assert_existing_metadata_preserved(out)


def test_residual_inline_enforce_scene_momentum_appends_fallback_when_due() -> None:
    """``enforce_scene_momentum`` due-bit snapshot (no passive/topic fixtures)."""
    base = _gm("Rain ticks against the gatehouse stones.")

    out = _apply(
        base,
        _policy(prefer_scene_momentum=True),
        player_text="I speak to the nearest guard about the road.",
        resolution={
            "kind": "observe",
            "prompt": "I speak to the nearest guard about the road.",
        },
        session=_session_scene_momentum_due(),
        scene_envelope=_scene_low_tension_surface(),
    )

    assert out["player_facing_text"] != base["player_facing_text"]
    assert "scene_momentum:enforced_fallback" in out["debug_notes"]
    assert any(t.startswith("scene_momentum:") for t in out["tags"])
    assert "passive_scene_pressure" not in out["tags"]
    _assert_existing_metadata_preserved(out)


def test_residual_inline_escalate_passive_scene_appends_under_passive_streak() -> None:
    base = _gm("Rain ticks.")

    out = _apply(
        base,
        _policy(prefer_scene_momentum=True),
        player_text="I wait.",
        resolution={"kind": "observe", "prompt": "I wait."},
        session=_session_passive_escalation_ready(),
    )

    assert "passive_scene_pressure" in out["tags"]
    assert "passive_scene_pressure:" in out["debug_notes"]
    assert out["player_facing_text"] != base["player_facing_text"]
    _assert_existing_metadata_preserved(out)


def test_residual_inline_topic_pressure_escalation_rewrites_under_pressure() -> None:
    """Topic-pressure beat uses ``adjudication_query`` so strict-social bypass does not skip."""
    base = _gm("I cannot say.")

    out = _apply(
        base,
        _policy(prefer_scene_momentum=True),
        player_text="Who patrols the east road?",
        resolution={
            "kind": "adjudication_query",
            "prompt": "Who patrols the east road?",
        },
        session=_session_topic_pressure_escalation_ready(),
    )

    assert out["player_facing_text"] != base["player_facing_text"]
    assert "topic_pressure_escalation" in out["tags"]
    assert "topic_pressure_escalation:" in out["debug_notes"]
    _assert_existing_metadata_preserved(out)


def test_residual_inline_commit_topic_progress_updates_runtime_when_context_present() -> None:
    session = _session_topic_progress_trackable()
    base = _gm("Fresh ink on the notice board.")

    out = _apply(base, _policy(), session=session)

    entry = session["scene_runtime"]["frontier_gate"]["topic_pressure"]["missing_patrol"]
    assert entry["last_answer"] == "Fresh ink on the notice board."[:480]
    assert out["player_facing_text"] == base["player_facing_text"]
    _assert_existing_metadata_preserved(out)


def test_residual_inline_commit_topic_progress_noop_without_topic_runtime() -> None:
    session = _neutral_session()

    _apply(_gm("Unused reply text."), _policy(), session=session)

    rt = session["scene_runtime"]["frontier_gate"]
    assert rt.get("topic_pressure") is None
    assert rt.get("topic_pressure_current") is None


def test_metadata_projection_helpers_match_documented_fallback_contract_shape() -> None:
    """Equivalence guard for extracted metadata helpers (no prose paths)."""
    contract = {
        "enabled": True,
        "uncertainty_active": True,
        "uncertainty_mode": "bounded_unknown",
        "uncertainty_sources": ["scene_context"],
        "allowed_behaviors": {"bounded_partial": True},
        "prefer_partial_over_question": True,
    }
    out: dict = {
        "player_facing_text": "unchanged prose",
        "metadata": {"existing_metadata": "kept"},
    }
    _snapshot_response_policy_and_project_fallback_contract(
        out,
        {"fallback_behavior": contract, "must_answer": False},
    )

    assert out["player_facing_text"] == "unchanged prose"
    assert out["response_policy"]["fallback_behavior"] == contract
    emitted = ((out.get("metadata") or {}).get("emission_debug") or {}).get("fallback_behavior_contract") or {}
    assert emitted["enabled"] is True
    assert emitted["uncertainty_active"] is True
    assert emitted["uncertainty_mode"] == "bounded_unknown"
    assert emitted["uncertainty_sources"] == ["scene_context"]
    assert emitted["allowed_behaviors"] == {"bounded_partial": True}
    assert emitted["prefer_partial_over_question"] is True

    out2: dict = {"metadata": {}}
    _project_fallback_behavior_contract_metadata(out2, contract)
    emitted2 = out2["metadata"]["emission_debug"]["fallback_behavior_contract"]
    assert emitted2 == emitted

    assert _normalize_response_policy_input(None) == {}
    assert _normalize_response_policy_input({"a": 1}) == {"a": 1}

    bare: dict = {"metadata": {}}
    _mark_response_policy_enforcement_applied(bare)
    assert bare["metadata"][GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED] is True


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


def test_contract_split_helpers_remain_exported_from_gm() -> None:
    """Rename guard: orchestration helpers must stay re-exported on ``game.gm`` (see manifest)."""
    for name in RESPONSE_POLICY_ENFORCEMENT_CONTRACT_HELPER_NAMES:
        obj = getattr(gm_mod, name, None)
        assert obj is not None, f"missing game.gm.{name}"
        assert callable(obj), f"game.gm.{name} must be callable"


def test_response_policy_enforcement_runtime_owner_compatibility_exports() -> None:
    """Cycle AI12: runtime owner owns symbols; ``game.gm`` re-exports identical objects."""
    assert set(RESPONSE_POLICY_ENFORCEMENT_CONTRACT_HELPER_NAMES) <= set(
        RESPONSE_POLICY_ENFORCEMENT_GM_COMPAT_EXPORT_NAMES
    )
    for name in RESPONSE_POLICY_ENFORCEMENT_GM_COMPAT_EXPORT_NAMES:
        owner_obj = getattr(rpe_mod, name, None)
        gm_obj = getattr(gm_mod, name, None)
        assert owner_obj is not None, f"missing game.response_policy_enforcement.{name}"
        assert gm_obj is not None, f"missing game.gm.{name} compatibility export"
        assert gm_obj is owner_obj, f"game.gm.{name} must be the same object as runtime owner"
        if name != "GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED":
            assert callable(owner_obj), f"game.response_policy_enforcement.{name} must be callable"


def test_cycle_ai_gm_has_no_response_policy_enforcement_implementations() -> None:
    """Cycle AI12: ``game.gm`` must not define enforcement bodies (compat re-exports only)."""
    for name in RESPONSE_POLICY_ENFORCEMENT_GM_COMPAT_EXPORT_NAMES:
        owner_obj = getattr(rpe_mod, name)
        if name == "GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED":
            assert rpe_mod.__dict__.get(name) == owner_obj
            continue
        assert inspect.getmodule(owner_obj) is rpe_mod, (
            f"game.response_policy_enforcement.{name} must be defined on the runtime owner module"
        )


def test_contract_metadata_projection_helpers_do_not_mutate_player_facing_text() -> None:
    """Projection helpers must not touch prose (Block Y boundary)."""
    pft = "Fixed prose line."
    out: dict = {"player_facing_text": pft, "metadata": {}}
    fb = {
        "enabled": True,
        "uncertainty_active": False,
        "uncertainty_mode": None,
        "uncertainty_sources": [],
        "allowed_behaviors": {},
        "prefer_partial_over_question": False,
    }
    gm_mod._project_fallback_behavior_contract_metadata(out, fb)
    assert out["player_facing_text"] == pft

    gm_mod._mark_response_policy_enforcement_applied(out)
    assert out["player_facing_text"] == pft

    gm_mod._snapshot_response_policy_and_project_fallback_contract(out, {"must_answer": False})
    assert out["player_facing_text"] == pft


def test_contract_orchestration_call_order_full_enabled_policy() -> None:
    """``apply_response_policy_enforcement`` invokes helpers in ``RESPONSE_RULE_PRIORITY`` order."""
    log: list[str] = []
    with ExitStack() as stack:
        for name in RESPONSE_POLICY_ENFORCEMENT_ORCHESTRATION_SEQUENCE_FULL_POLICY:
            orig = getattr(rpe_mod, name)
            def wrapper_factory(nn: str, oo):
                def _wrap(*a, **kw):
                    log.append(nn)
                    return oo(*a, **kw)
                return _wrap
            stack.enter_context(patch.object(rpe_mod, name, new=wrapper_factory(name, orig)))
        gm_mod.apply_response_policy_enforcement(
            _gm("Rain ticks against the gatehouse stones."),
            response_policy={
                "must_answer": True,
                "forbid_state_invention": True,
                "forbid_secret_leak": True,
                "diegetic_only": True,
                "no_validator_voice": {"enabled": True},
                "prefer_scene_momentum": True,
                "prefer_specificity": True,
            },
            player_text="I wait.",
            scene_envelope=_scene(),
            session=_neutral_session(),
            world=_world(),
            resolution={"kind": "observe", "prompt": "I wait."},
            discovered_clues=[],
        )
    assert log == list(RESPONSE_POLICY_ENFORCEMENT_ORCHESTRATION_SEQUENCE_FULL_POLICY)


def test_contract_topic_progress_commit_receives_post_enforcement_reply_text() -> None:
    """Topic commit runs after the enforcement loop; capture uses final ``player_facing_text``."""
    captured: list[str] = []
    orig_commit = rpe_mod._commit_topic_progress

    def capture_commit(
        *,
        session,
        scene_envelope,
        reply_text,
    ):
        captured.append(reply_text)
        return orig_commit(session=session, scene_envelope=scene_envelope, reply_text=reply_text)

    with patch.object(rpe_mod, "_commit_topic_progress", side_effect=capture_commit):
        out = gm_mod.apply_response_policy_enforcement(
            _gm("Rain ticks against the gatehouse stones."),
            response_policy=_policy(must_answer=True),
            player_text="Who signed the sealed order?",
            scene_envelope=_scene(),
            session=_neutral_session(),
            world=_world(),
            resolution={"kind": "adjudication_query", "prompt": "Who signed the sealed order?"},
            discovered_clues=[],
        )

    assert len(captured) == 1
    assert captured[0] == str(out.get("player_facing_text") or "")
    assert captured[0] != "Rain ticks against the gatehouse stones."


def test_contract_mutating_branches_preserve_expected_marker_style() -> None:
    """Regression guard: enforcement paths still attach category tags and debug substrings."""
    v_base = _gm("As an AI language model, I cannot determine that.")
    v_out = _apply(
        v_base,
        _policy(diegetic_only=True, no_validator_voice={"enabled": True}),
        player_text="I wait.",
        resolution={"kind": "observe", "prompt": "I wait."},
        session=_neutral_session(),
    )
    assert "validator_voice_rewrite" in v_out["tags"]
    assert "validator_voice_rewrite" in v_out["debug_notes"]

    g_base = _gm("A noble house ordered the curfew posted yesterday.")
    g_out = _apply(
        g_base,
        _policy(forbid_secret_leak=True),
        player_text="The noble house.",
        resolution={"kind": "observe", "prompt": "The noble house."},
        session=_neutral_session(),
    )
    assert "spoiler_guard" in g_out["tags"]
    assert "spoiler_guard:" in g_out["debug_notes"]
