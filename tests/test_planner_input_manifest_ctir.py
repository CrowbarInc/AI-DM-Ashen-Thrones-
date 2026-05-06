"""CTIR planner input discipline — manifest alignment and channel boundaries."""

from __future__ import annotations

import inspect
from typing import Any
from unittest.mock import patch

import pytest

from game.ctir import build_ctir
from game.narrative_plan_upstream import compute_narrative_plan_for_bundle_from_head
from game.narrative_planning import build_narrative_plan
from game.planner_input_manifest import (
    BUILD_NARRATIVE_PLAN_PARAM_NAMES,
    FORBIDDEN_PLANNER_SEMANTIC_CHANNELS,
    PHRASE_PATCH_AUDIT,
    PLANNER_INPUT_MANIFEST_ROWS,
    manifest_row_ids,
    summarize_planner_head_for_debug,
)

pytestmark = pytest.mark.unit


def test_manifest_rows_have_unique_ids_and_required_fields() -> None:
    ids = [str(r["id"]) for r in PLANNER_INPUT_MANIFEST_ROWS]
    assert len(ids) == len(set(ids))
    for row in PLANNER_INPUT_MANIFEST_ROWS:
        assert row.get("path")
        assert row.get("consumer")
        assert row.get("classification")


def test_manifest_row_ids_helper_matches() -> None:
    assert manifest_row_ids() == tuple(str(r["id"]) for r in PLANNER_INPUT_MANIFEST_ROWS)


def test_build_narrative_plan_signature_matches_manifest_allowlist() -> None:
    sig = inspect.signature(build_narrative_plan)
    params = [p for p in sig.parameters.keys() if p != "kwargs"]
    assert params == list(BUILD_NARRATIVE_PLAN_PARAM_NAMES)


def test_build_narrative_plan_rejects_forbidden_channels_as_keyword() -> None:
    """Planner core API must not accept GM/model prose buckets as named parameters."""
    sig = inspect.signature(build_narrative_plan)
    names = set(sig.parameters.keys())
    assert not (names & FORBIDDEN_PLANNER_SEMANTIC_CHANNELS)


def test_phrase_patch_audit_entries_are_well_formed() -> None:
    for row in PHRASE_PATCH_AUDIT:
        assert row.get("location")
        assert row.get("artifact")
        assert row.get("kind")
        assert row.get("behavior")


def _minimal_ctir() -> dict[str, Any]:
    return build_ctir(
        turn_id=1,
        scene_id="t_scene",
        player_input="hello there",
        builder_source="tests.planner_input_manifest",
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
        resolution={"kind": "neutral_narration"},
        interaction={"active_target_id": "npc_x", "interaction_mode": "social"},
    )


def test_compute_bundle_plan_only_passes_manifest_kwarges_to_build(monkeypatch: pytest.MonkeyPatch) -> None:
    """Upstream bundle builder must not invent extra semantic channels into build_narrative_plan."""
    captured: dict[str, Any] = {}

    def _capture(**kwargs: Any) -> dict[str, Any]:
        captured.clear()
        captured.update(kwargs)
        return {"version": 1}

    monkeypatch.setattr("game.narrative_plan_upstream.build_narrative_plan", _capture)
    ctir = _minimal_ctir()
    head = {
        "ctir_obj": ctir,
        "resolution_sem": {"kind": "neutral_narration"},
        "interaction_sem": {"active_target_id": "npc_x", "interaction_mode": "social"},
        "response_policy": {"narrative_authority": "standard"},
        "visibility_contract": {"visible_entity_ids": ["npc_x"], "visible_entity_names": ["Guard"]},
        "public_scene": {"id": "t_scene", "name": "Market"},
        "scene_state_anchor_contract": {},
        "active_pending_leads": [],
        "session_view": {},
        "recent_log_compact": [{"turn_id": 1, "summary": "arrived"}],
        "narration_obligations": {},
    }
    compute_narrative_plan_for_bundle_from_head(head, user_text="Who goes there?")
    keys = set(captured.keys())
    assert keys <= set(BUILD_NARRATIVE_PLAN_PARAM_NAMES)
    assert not (keys & FORBIDDEN_PLANNER_SEMANTIC_CHANNELS)
    assert captured.get("ctir") is ctir


def test_summarize_planner_head_for_debug_smoke() -> None:
    summary = summarize_planner_head_for_debug({"ctir_obj": {"turn_id": 1}, "resolution_sem": {}})
    assert summary["ctir_attached"] is True
    assert summary["has_resolution_sem"] is True
    assert summary["head_key_count"] == 2


def test_summarize_planner_head_for_debug_rejects_non_mapping() -> None:
    bad = summarize_planner_head_for_debug(None)
    assert bad.get("error") == "head_not_a_mapping"


@patch("game.narrative_plan_upstream.build_narrative_plan")
def test_bundle_does_not_feed_raw_resolution_dict_when_ctir_present(
    mock_build: Any,
) -> None:
    """When CTIR is attached, plan construction consumes CTIR-shaped semantics, not parallel raw dicts."""
    ctir = _minimal_ctir()

    def _record(**kwargs: Any) -> dict[str, Any]:
        return {"version": 1}

    mock_build.side_effect = _record
    head = {
        "ctir_obj": ctir,
        "resolution_sem": {"kind": "neutral_narration", "_probe": "sem"},
        "interaction_sem": {},
        "response_policy": {"narrative_authority": "standard"},
        "visibility_contract": {"visible_entity_ids": [], "visible_entity_names": []},
        "public_scene": {"id": "t_scene"},
        "scene_state_anchor_contract": {},
        "active_pending_leads": [],
        "session_view": {},
        "recent_log_compact": [],
        "narration_obligations": {},
    }
    compute_narrative_plan_for_bundle_from_head(head, user_text="test")
    mock_build.assert_called_once()
    kwargs = mock_build.call_args.kwargs
    assert kwargs["ctir"] is ctir
    # Duplicate semantic reconstruction would imply passing a second full meaning blob;
    # only ctir carries canonical semantic structure here.
    assert "resolution" not in kwargs
    assert "gm_output" not in kwargs
