"""Objective N5: ``clause_referent_plan`` construction and strict validation."""

from __future__ import annotations

import json

import pytest

from game.referent_tracking import (
    REFERENT_TRACKING_ARTIFACT_VERSION,
    _MAX_STR_CLIP,
    build_referent_tracking_artifact,
    normalize_entity_id,
    validate_clause_referent_plan_row,
    validate_referent_tracking_artifact,
)

pytestmark = pytest.mark.unit


def _vis(
    *,
    ids: list[str],
    names: list[str] | None = None,
    kinds: dict[str, str] | None = None,
) -> dict:
    names = names or []
    row: dict = {
        "visible_entity_ids": list(ids),
        "visible_entity_names": names if names else [f"name_{i}" for i in range(len(ids))],
        "scene_id": "scene_test",
    }
    if kinds:
        row["visible_entity_kinds"] = dict(kinds)
    return row


def test_clause_plan_absent_when_no_structured_lanes() -> None:
    art = build_referent_tracking_artifact()
    assert "clause_referent_plan" not in art
    assert validate_referent_tracking_artifact(art) is None


def test_clause_plan_target_row_only_when_no_speaker_lane() -> None:
    vis = _vis(ids=["npc_t"], names=["T"], kinds={"npc_t": "npc"})
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        session_interaction={"active_interaction_target_id": "npc_t"},
    )
    plan = art.get("clause_referent_plan")
    assert plan is not None
    assert [r["clause_kind"] for r in plan] == ["interaction_target"]
    assert plan[0]["clause_id"] == "n5:interaction_target:0"
    assert plan[0]["preferred_object_id"] == "npc_t"
    assert plan[0]["object_candidate_ids"] == ["npc_t"]


def test_speaker_target_and_continuity_object_distinct_rows() -> None:
    vis = _vis(
        ids=["npc_a", "npc_b", "npc_c"],
        names=["A", "B", "C"],
        kinds={"npc_a": "npc", "npc_b": "npc", "npc_c": "npc"},
    )
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        speaker_selection={"primary_speaker_id": "npc_a", "allowed_speaker_ids": ["npc_a"]},
        session_interaction={"active_interaction_target_id": "npc_b"},
        structured_continuity_object={"entity_id": "npc_c", "object_kind": "item"},
    )
    plan = art.get("clause_referent_plan")
    assert plan is not None
    assert len(plan) == 3
    assert [r["clause_id"] for r in plan] == [
        "n5:speaker_subject:0",
        "n5:interaction_target:0",
        "n5:continuity_object:0",
    ]
    assert {r["clause_kind"] for r in plan} == {"speaker_subject", "interaction_target", "continuity_object"}


def test_multiple_visible_entities_ambiguity_class_on_speaker_slot() -> None:
    vis = _vis(
        ids=["npc_a", "npc_b"],
        names=["A", "B"],
        kinds={"npc_a": "npc", "npc_b": "npc"},
    )
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        speaker_selection={"primary_speaker_id": "npc_a", "allowed_speaker_ids": ["npc_a"]},
    )
    plan = art.get("clause_referent_plan")
    assert plan is not None
    speaker_row = plan[0]
    assert speaker_row["clause_kind"] == "speaker_subject"
    assert speaker_row["ambiguity_class"] == "ambiguous_plural"


def test_allowed_explicit_labels_are_authorized_and_clipped() -> None:
    long_name = "Z" * (_MAX_STR_CLIP + 40)
    vis = _vis(ids=["npc_x"], names=[long_name], kinds={"npc_x": "npc"})
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        speaker_selection={"primary_speaker_id": "npc_x", "allowed_speaker_ids": ["npc_x"]},
    )
    plan = art["clause_referent_plan"]
    labels = plan[0]["allowed_explicit_labels"]
    assert labels
    assert all(len(x) <= _MAX_STR_CLIP for x in labels)
    auth = {r["safe_explicit_label"] for r in art["safe_explicit_fallback_labels"]}
    assert set(labels).issubset(auth)


def test_artifact_validates_and_json_serializable_with_clause_plan() -> None:
    vis = _vis(ids=["npc_1", "npc_2"], kinds={"npc_1": "npc", "npc_2": "npc"})
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        speaker_selection={"primary_speaker_id": "npc_1", "allowed_speaker_ids": ["npc_1", "npc_2"]},
        ctir_addressed_entity_ids=["npc_1"],
    )
    assert "clause_referent_plan" in art
    assert validate_referent_tracking_artifact(art) is None
    s = json.dumps(art, sort_keys=True)
    assert "clause_referent_plan" in s
    roundtrip = json.loads(s)
    assert roundtrip["version"] == REFERENT_TRACKING_ARTIFACT_VERSION


def test_old_artifact_shape_without_clause_plan_still_validates() -> None:
    vis = _vis(ids=["npc_z"], kinds={"npc_z": "npc"})
    art = build_referent_tracking_artifact(narration_visibility=vis)
    art.pop("clause_referent_plan", None)
    assert "clause_referent_plan" not in art
    assert validate_referent_tracking_artifact(art, strict=True) is None


def test_validate_clause_row_rejects_unknown_keys() -> None:
    vis = _vis(ids=["e1"], kinds={"e1": "npc"})
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        session_interaction={"active_interaction_target_id": "e1"},
    )
    row = dict(art["clause_referent_plan"][0])
    row["extra_field"] = 1
    visible = {normalize_entity_id(r["entity_id"]) for r in art["active_entities"]}
    auth = {r["safe_explicit_label"] for r in art["safe_explicit_fallback_labels"]}
    err = validate_clause_referent_plan_row(row, visible_ids=visible, authorized_labels=auth)
    assert err and "unknown_keys" in err


def test_validate_clause_row_rejects_unauthorized_label() -> None:
    vis = _vis(ids=["e1"], kinds={"e1": "npc"})
    art = build_referent_tracking_artifact(
        narration_visibility=vis,
        session_interaction={"active_interaction_target_id": "e1"},
    )
    row = dict(art["clause_referent_plan"][0])
    row["allowed_explicit_labels"] = ["Totally Unauthorized Label"]
    visible = {normalize_entity_id(r["entity_id"]) for r in art["active_entities"]}
    auth = {r["safe_explicit_label"] for r in art["safe_explicit_fallback_labels"]}
    err = validate_clause_referent_plan_row(row, visible_ids=visible, authorized_labels=auth)
    assert err == "clause_row_label_not_authorized"
