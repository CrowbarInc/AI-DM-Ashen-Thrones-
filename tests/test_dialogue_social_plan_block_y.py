"""Block Y — Phase 1 declared pregate alias schema (builder + validation only)."""

from __future__ import annotations

import pytest

from game.dialogue_social_plan import (
    SPEAKER_ALIAS_RESOLUTION_SOURCES,
    build_dialogue_social_plan,
    validate_dialogue_social_plan,
)
from tests.helpers.dialogue_social_plan import make_valid_dialogue_social_plan

pytestmark = pytest.mark.unit


def test_block_y_validate_accepts_optional_alias_fields_with_source() -> None:
    plan = make_valid_dialogue_social_plan(
        allowed_pregate_speaker_labels=["Ragged stranger"],
        speaker_alias_resolution_source="manual_bundle_override",
    )
    ok, errs = validate_dialogue_social_plan(plan, strict=False)
    assert ok is True, errs


def test_block_y_validate_rejects_alias_labels_without_resolution_source() -> None:
    plan = make_valid_dialogue_social_plan()
    plan["allowed_pregate_speaker_labels"] = ["Ragged stranger"]
    plan.pop("speaker_alias_resolution_source", None)
    ok, errs = validate_dialogue_social_plan(plan, strict=False)
    assert ok is False
    assert any("missing_required:speaker_alias_resolution_source" in e for e in errs)


def test_block_y_validate_rejects_unknown_resolution_source() -> None:
    plan = make_valid_dialogue_social_plan(
        writer_attribution_label="Ragged stranger",
        speaker_alias_resolution_source="manual_bundle_override",
    )
    plan["speaker_alias_resolution_source"] = "inferred_from_prose"
    ok, errs = validate_dialogue_social_plan(plan, strict=False)
    assert ok is False
    assert any("bad_speaker_alias_resolution_source" in e for e in errs)


def test_block_y_validate_legacy_plan_without_alias_fields() -> None:
    plan = make_valid_dialogue_social_plan()
    plan["validator"] = {"validated": False, "errors": []}
    ok, errs = validate_dialogue_social_plan(plan, strict=False)
    assert ok is True, errs


def test_block_y_builder_populates_from_continuity_snapshot_only() -> None:
    ctir = {
        "resolution": {"kind": "question"},
        "noncombat": {"kind": "social_probe", "subkind": "question"},
        "interaction": {
            "speaker_target": {"id": "npc_x", "name": "NPC X"},
            "continuity_snapshot": {
                "engagement_level": "engaged",
                "allowed_pregate_speaker_labels": ["Ragged stranger"],
                "writer_attribution_label": "Ragged stranger",
            },
        },
    }
    plan = build_dialogue_social_plan(ctir_obj=ctir, referent_tracking=None)
    assert plan.get("allowed_pregate_speaker_labels") == ["Ragged stranger"]
    assert plan.get("writer_attribution_label") == "Ragged stranger"
    assert plan.get("speaker_alias_resolution_source") == "continuity_snapshot"


def test_block_y_builder_merges_referent_tracking_when_continuity_empty() -> None:
    ctir = {
        "resolution": {"kind": "question"},
        "noncombat": {"kind": "social_probe", "subkind": "question"},
        "interaction": {"speaker_target": {"id": "npc_x", "name": "NPC X"}},
    }
    rt = {"allowed_pregate_speaker_labels": ["Alias One"], "writer_attribution_label": "Alias One"}
    plan = build_dialogue_social_plan(ctir_obj=ctir, referent_tracking=rt)
    assert plan.get("speaker_alias_resolution_source") == "referent_tracking"
    assert "Alias One" in (plan.get("allowed_pregate_speaker_labels") or [])


def test_block_y_builder_does_not_infer_aliases_when_upstream_empty() -> None:
    plan = build_dialogue_social_plan(ctir_obj=None, referent_tracking=None)
    assert "allowed_pregate_speaker_labels" not in plan
    assert "writer_attribution_label" not in plan
    assert "speaker_alias_resolution_source" not in plan


def test_block_y_resolution_sources_frozen_is_stable() -> None:
    assert "continuity_snapshot" in SPEAKER_ALIAS_RESOLUTION_SOURCES
    assert "referent_tracking" in SPEAKER_ALIAS_RESOLUTION_SOURCES
    assert "inferred_from_prose" not in SPEAKER_ALIAS_RESOLUTION_SOURCES


def test_block_y_unknown_top_level_keys_still_validate() -> None:
    """Document migration risk: allowlist tightening is Block Z / optional cleanup."""
    plan = make_valid_dialogue_social_plan()
    plan["future_unknown_field_xyz"] = True
    ok, errs = validate_dialogue_social_plan(plan, strict=False)
    assert ok is True, errs
