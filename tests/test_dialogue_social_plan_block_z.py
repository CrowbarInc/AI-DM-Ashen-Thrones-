"""Block Z — Phase 2 pregate alias matching helper (unit-level)."""

from __future__ import annotations

import pytest

from game.dialogue_social_plan import (
    pregate_attributed_label_matches_dialogue_social_plan,
    validate_dialogue_social_plan,
)
from tests.helpers.dialogue_social_plan import make_valid_dialogue_social_plan

pytestmark = pytest.mark.unit


def test_block_z_helper_matches_canonical_speaker_id_and_name() -> None:
    plan = make_valid_dialogue_social_plan(speaker_id="tavern_runner", speaker_name="Tavern Runner")
    assert pregate_attributed_label_matches_dialogue_social_plan("tavern_runner", plan) is True
    assert pregate_attributed_label_matches_dialogue_social_plan("Tavern Runner", plan) is True


def test_block_z_helper_matches_allowed_pregate_label_exact_only() -> None:
    plan = make_valid_dialogue_social_plan(
        speaker_id="tavern_runner",
        speaker_name="Tavern Runner",
        dialogue_intent="question",
        allowed_pregate_speaker_labels=["Ragged stranger"],
        speaker_alias_resolution_source="manual_bundle_override",
    )
    assert pregate_attributed_label_matches_dialogue_social_plan("Ragged stranger", plan) is True
    assert pregate_attributed_label_matches_dialogue_social_plan("Ragged Stranger", plan) is True
    assert pregate_attributed_label_matches_dialogue_social_plan("Ragged", plan) is False


def test_block_z_helper_matches_writer_attribution_label() -> None:
    plan = make_valid_dialogue_social_plan(
        speaker_id="tavern_runner",
        speaker_name="Tavern Runner",
        dialogue_intent="question",
        writer_attribution_label="Ragged stranger",
        speaker_alias_resolution_source="manual_bundle_override",
    )
    assert pregate_attributed_label_matches_dialogue_social_plan("Ragged stranger", plan) is True


def test_block_z_plan_invalid_if_alias_data_without_provenance() -> None:
    plan = make_valid_dialogue_social_plan()
    plan["allowed_pregate_speaker_labels"] = ["X"]
    plan.pop("speaker_alias_resolution_source", None)
    ok, errs = validate_dialogue_social_plan(plan, strict=False)
    assert ok is False


def test_block_z_plan_invalid_if_inferred_from_provenance() -> None:
    plan = make_valid_dialogue_social_plan(
        allowed_pregate_speaker_labels=["A"],
        speaker_alias_resolution_source="manual_bundle_override",
    )
    plan["speaker_alias_resolution_source"] = "inferred_from_prose"
    ok, errs = validate_dialogue_social_plan(plan, strict=False)
    assert ok is False
