"""Block X — contract pins for dialogue_social_plan migration / drift detection.

Phase 1 (Block Y) added optional declared-alias fields; pins stay backward-compatible.
"""

from __future__ import annotations

from game.dialogue_social_plan import validate_dialogue_social_plan

from tests.helpers.dialogue_social_plan import make_valid_dialogue_social_plan

import pytest

pytestmark = pytest.mark.unit


def test_block_x_plan_validate_requires_no_alias_fields_by_default() -> None:
    """Baseline: fixtures omit optional alias fields unless callers attach them."""
    plan = make_valid_dialogue_social_plan()
    assert "allowed_pregate_speaker_labels" not in plan
    assert "writer_attribution_label" not in plan
    assert "speaker_alias_resolution_source" not in plan
    ok, errs = validate_dialogue_social_plan(plan, strict=False)
    assert ok is True, errs


def test_block_x_validator_accepts_unknown_top_level_keys_without_error() -> None:
    """Migration risk pin: unknown keys are not rejected until an explicit allowlist ships."""
    plan = make_valid_dialogue_social_plan()
    plan["hypothetical_future_allowed_pregate_speaker_labels"] = ["Ragged stranger"]
    ok, errs = validate_dialogue_social_plan(plan, strict=False)
    assert ok is True, errs


def test_block_x_build_dialogue_social_plan_omits_aliases_without_upstream_declarations() -> None:
    """Pins builder: no declared upstream alias maps → optional alias keys omitted."""
    from game.dialogue_social_plan import build_dialogue_social_plan

    built = build_dialogue_social_plan(ctir_obj=None, referent_tracking=None, bounded_session_hints=None)
    assert "allowed_pregate_speaker_labels" not in built
    assert "writer_attribution_label" not in built
    assert "speaker_alias_resolution_source" not in built
