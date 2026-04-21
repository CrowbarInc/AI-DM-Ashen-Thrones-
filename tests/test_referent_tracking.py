"""Unit tests for deterministic referent tracking (Objective #7; no GPT, no prose parsing)."""

from __future__ import annotations

import json

import pytest

from game.referent_tracking import (
    REFERENT_TRACKING_ARTIFACT_VERSION,
    build_referent_tracking_artifact,
    referent_tracking_artifact_version,
    validate_referent_tracking_artifact,
)

pytestmark = pytest.mark.unit


def _vis(*, ids: list[str], names: list[str] | None = None, kinds: dict[str, str] | None = None, roles: dict[str, list[str]] | None = None, interlocutor: str | None = None) -> dict:
    names = names or []
    row: dict = {
        "visible_entity_ids": list(ids),
        "visible_entity_names": names if names else [f"name_{i}" for i in range(len(ids))],
        "scene_id": "scene_test",
    }
    if kinds:
        row["visible_entity_kinds"] = dict(kinds)
    if roles:
        row["visible_entity_roles"] = {k: list(v) for k, v in roles.items()}
    if interlocutor is not None:
        row["active_interlocutor_id"] = interlocutor
    return row


def test_version_constant() -> None:
    assert referent_tracking_artifact_version() == REFERENT_TRACKING_ARTIFACT_VERSION == 1


def test_single_visible_npc_single_clear_target() -> None:
    vis = _vis(ids=["npc_arya"], names=["Arya"], kinds={"npc_arya": "npc"})
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        session_interaction={"active_interaction_target_id": "npc_arya"},
        speaker_selection={
            "primary_speaker_id": "npc_arya",
            "allowed_speaker_ids": ["npc_arya"],
            "continuity_locked": True,
        },
    )
    assert validate_referent_tracking_artifact(art) is None
    assert art["active_interaction_target"] == "npc_arya"
    assert art["allowed_named_references"] == [{"entity_id": "npc_arya", "display_name": "Arya"}]
    assert art["single_unambiguous_entity"] == {
        "entity_id": "npc_arya",
        "label": "Arya",
        "case": "single_visible_person_like",
    }
    kinds = [x["entity_id"] for x in art["forbidden_or_unresolved_patterns"] if x.get("kind") == "target_id_not_visible"]
    assert kinds == []


def test_multiple_visible_npcs_same_role_pressure() -> None:
    vis = _vis(
        ids=["npc_a", "npc_b"],
        names=["Guard A", "Guard B"],
        kinds={"npc_a": "npc", "npc_b": "npc"},
        roles={"npc_a": ["guard"], "npc_b": ["guard"]},
    )
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        speaker_selection={"primary_speaker_id": "npc_a", "allowed_speaker_ids": ["npc_a"], "continuity_locked": True},
        session_interaction={"active_interaction_target_id": "npc_a"},
    )
    assert art["referential_ambiguity_class"] == "ambiguous_plural"
    assert art["ambiguity_risk"] >= 40
    assert any(p.get("kind") == "gendered_pronoun_uncertainty" for p in art["forbidden_or_unresolved_patterns"])


def test_no_social_target_visible_roster_present() -> None:
    vis = _vis(ids=["npc_x", "npc_y"], names=["X", "Y"], kinds={"npc_x": "npc", "npc_y": "npc"})
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        speaker_selection={"primary_speaker_id": None, "allowed_speaker_ids": []},
    )
    assert art["active_interaction_target"] is None
    assert {r["entity_id"] for r in art["allowed_named_references"]} == {"npc_x", "npc_y"}


def test_continuity_target_preserved_across_turns_no_drift() -> None:
    vis = _vis(ids=["npc_t"], names=["T"], kinds={"npc_t": "npc"})
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        session_interaction={"active_interaction_target_id": "npc_t"},
        prior_active_interaction_target_id="npc_t",
    )
    cont = art["interaction_target_continuity"]
    assert cont["drift_detected"] is False
    assert cont["prior_target_id"] == "npc_t"
    assert cont["current_target_id"] == "npc_t"
    assert not any(p.get("kind") == "interaction_target_drift" for p in art["forbidden_or_unresolved_patterns"])


def test_target_drift_detected() -> None:
    vis = _vis(ids=["npc_a", "npc_b"], names=["A", "B"], kinds={"npc_a": "npc", "npc_b": "npc"})
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        session_interaction={"active_interaction_target_id": "npc_b"},
        prior_active_interaction_target_id="npc_a",
    )
    assert art["interaction_target_continuity"]["drift_detected"] is True
    assert any(p.get("kind") == "interaction_target_drift" for p in art["forbidden_or_unresolved_patterns"])


def test_no_explicit_pronoun_certainty_multi_npc() -> None:
    vis = _vis(ids=["npc_1", "npc_2"], kinds={"npc_1": "npc", "npc_2": "npc"})
    art = build_referent_tracking_artifact(narration_visibility=vis)
    assert art["pronoun_resolution"]["strategy"] == "unresolved"
    assert art["pronoun_resolution"]["explicit_sources"] == []


def test_explicit_pronoun_buckets_strategy() -> None:
    vis = _vis(ids=["npc_1"], kinds={"npc_1": "npc"})
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        explicit_entity_pronoun_buckets={"npc_1": ["she_her"]},
    )
    assert art["pronoun_resolution"]["strategy"] == "explicit_structured"
    assert art["pronoun_resolution"]["buckets_by_entity"]["npc_1"] == ["she_her"]


def test_validate_rejects_malformed_artifact() -> None:
    base = build_referent_tracking_artifact(
        narration_visibility=_vis(ids=["npc_z"], kinds={"npc_z": "npc"}),
    )
    bad = dict(base)
    bad["version"] = 99
    assert validate_referent_tracking_artifact(bad, strict=True) == "bad_version"

    bad2 = dict(base)
    bad2["active_entities"] = "not_a_list"
    assert validate_referent_tracking_artifact(bad2, strict=True) == "bad_list:active_entities"

    bad3 = dict(base)
    bad3["pronoun_resolution"] = []
    assert validate_referent_tracking_artifact(bad3, strict=True) == "pronoun_resolution_not_mapping"

    bad4 = dict(base)
    bad4["continuity_subject"] = "oops"
    assert validate_referent_tracking_artifact(bad4, strict=True) == "bad_optional_mapping:continuity_subject"

    bad5 = dict(base)
    bad5["mystery"] = 1
    err = validate_referent_tracking_artifact(bad5, strict=True)
    assert err and err.startswith("unknown_keys:")


def test_deterministic_json_stable() -> None:
    vis = _vis(
        ids=["b_npc", "a_npc"],
        names=["B", "A"],
        kinds={"a_npc": "npc", "b_npc": "npc"},
        roles={"a_npc": ["merchant"], "b_npc": ["merchant"]},
    )
    kwargs = dict(
        narration_visibility=vis,
        session_interaction={"active_interaction_target_id": "a_npc"},
        speaker_selection={"allowed_speaker_ids": ["a_npc"], "primary_speaker_id": "a_npc"},
        narrative_plan={
            "scene_anchors": {"active_target": "a_npc", "active_interlocutor": "a_npc"},
            "allowable_entity_references": [
                {"entity_id": "a_npc", "descriptor": "Ann"},
                {"entity_id": "b_npc", "descriptor": "Ben"},
            ],
        },
    )
    j1 = json.dumps(build_referent_tracking_artifact(**kwargs), sort_keys=True)
    j2 = json.dumps(build_referent_tracking_artifact(**kwargs), sort_keys=True)
    assert j1 == j2
    art = json.loads(j1)
    order = art["active_entity_order"]
    assert order[0] == "a_npc"
    assert set(order) == {"a_npc", "b_npc"}


def test_no_offscene_ctir_ids_in_allowed_named_references() -> None:
    vis = _vis(ids=["npc_visible"], kinds={"npc_visible": "npc"})
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        ctir_addressed_entity_ids=["npc_visible", "npc_hidden_offscene"],
    )
    allowed_ids = {r["entity_id"] for r in art["allowed_named_references"]}
    assert allowed_ids == {"npc_visible"}
    assert "npc_hidden_offscene" not in allowed_ids
    assert any(
        p.get("kind") == "ctir_addressed_not_visible" and p.get("entity_id") == "npc_hidden_offscene"
        for p in art["forbidden_or_unresolved_patterns"]
    )


def test_memory_window_entity_not_visible_is_flagged_not_allowed() -> None:
    vis = _vis(ids=["npc_here"], kinds={"npc_here": "npc"})
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        recent_structured_memory_entities=[{"entity_id": "npc_elsewhere"}],
    )
    assert {r["entity_id"] for r in art["allowed_named_references"]} == {"npc_here"}
    assert "npc_elsewhere" in (art["debug"].get("memory_window_entity_ids") or [])
    assert any(p.get("kind") == "memory_entity_not_visible" for p in art["forbidden_or_unresolved_patterns"])


def test_target_signal_not_visible() -> None:
    vis = _vis(ids=["npc_in_scene"], kinds={"npc_in_scene": "npc"})
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        session_interaction={"active_interaction_target_id": "npc_offscene_only"},
    )
    assert art["active_interaction_target"] is None
    assert any(p.get("kind") == "target_id_not_visible" for p in art["forbidden_or_unresolved_patterns"])


def test_conflicting_target_signals_raise_ambiguity() -> None:
    vis = _vis(ids=["npc_a", "npc_b"], kinds={"npc_a": "npc", "npc_b": "npc"})
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        session_interaction={"active_interaction_target_id": "npc_a"},
        narrative_plan={"scene_anchors": {"active_target": "npc_b"}},
    )
    assert art["debug"]["conflicting_target_signals"] is True
    assert art["active_interaction_target"] == "npc_a"


def test_visibility_extension_pronoun_buckets() -> None:
    vis = _vis(ids=["npc_x"], kinds={"npc_x": "npc"})
    vis["visible_entity_pronoun_buckets"] = {"npc_x": ["they_them"]}
    art = build_referent_tracking_artifact(narration_visibility=vis)
    assert art["pronoun_resolution"]["strategy"] == "explicit_structured"
    assert "visibility.visible_entity_pronoun_buckets" in art["pronoun_resolution"]["explicit_sources"]
