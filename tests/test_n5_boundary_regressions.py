"""Objective N5 Block D: architecture boundary regressions (lock-in, not features).

Guards against drift into prose parsing, duplicate semantic/planner authority, or
unbounded gate repairs. Behavioral assertions preferred over internal symbol names.
"""

from __future__ import annotations

import copy
import importlib
import inspect
import json
from typing import Any

import pytest

from game.ctir_runtime import detach_ctir, get_attached_ctir
from game.final_emission_repairs import _apply_referent_clarity_emission_layer
from game.final_emission_validators import validate_referent_clarity
from game.narration_plan_bundle import build_narration_plan_bundle
from game.prompt_context import _project_clause_referent_prompt_hints, build_narration_context
from game.referent_tracking import build_referent_tracking_artifact, build_clause_referent_plan
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests
from tests.helpers.objective7_referent_fixtures import (
    REFERENT_TRACKING_COMPACT_KEYS,
    minimal_full_referent_artifact,
    referent_compact_mirror,
)
from tests.test_narrative_plan_prompt_regressions import (
    _anchors_empty,
    _attach_ctir,
    _base_narration_kwargs,
    _scene_envelope,
    _world_npcs,
)

pytestmark = pytest.mark.unit


def _vis(*, ids: list[str], names: list[str] | None = None, kinds: dict[str, str] | None = None) -> dict[str, Any]:
    names = names or [f"n{i}" for i in range(len(ids))]
    row: dict[str, Any] = {
        "visible_entity_ids": list(ids),
        "visible_entity_names": names,
        "scene_id": "scene_test",
    }
    if kinds:
        row["visible_entity_kinds"] = dict(kinds)
    return row


def test_referent_tracking_module_defines_clause_plan_builder_prompt_context_does_not() -> None:
    """Only referent_tracking owns construction helpers for clause rows."""
    import game.prompt_context as prompt_context

    assert callable(build_clause_referent_plan)
    assert getattr(prompt_context, "build_clause_referent_plan", None) is None


def test_build_referent_tracking_artifact_signature_excludes_emitted_narration_text_params() -> None:
    """Clause-capable builder stays on structured seams only (no free-form GM/player prose lane)."""
    sig = inspect.signature(build_referent_tracking_artifact)
    names = set(sig.parameters)
    prose_like = {
        "narration",
        "narrative_text",
        "emitted_text",
        "gm_output",
        "player_facing_text",
        "draft_narration",
    }
    assert not (names & prose_like)


def test_prompt_projection_omits_clause_hints_when_field_absent_or_empty() -> None:
    art = minimal_full_referent_artifact()
    art.pop("clause_referent_plan", None)
    assert _project_clause_referent_prompt_hints(art) is None

    art2 = minimal_full_referent_artifact(clause_referent_plan=[])
    assert _project_clause_referent_prompt_hints(art2) is None


def test_prompt_projection_labels_are_subset_of_artifact_clause_rows_only() -> None:
    """Hints are read-side slices of the canonical artifact, not an independent label source."""
    art = build_referent_tracking_artifact(
        narration_visibility=_vis(ids=["npc_a", "npc_b"], kinds={"npc_a": "npc", "npc_b": "npc"}),
        speaker_selection={"primary_speaker_id": "npc_a", "allowed_speaker_ids": ["npc_a"]},
        session_interaction={"active_interaction_target_id": "npc_b"},
    )
    assert art.get("clause_referent_plan")
    auth_per_row: list[set[str]] = []
    for row in art["clause_referent_plan"]:
        labs = {str(x).strip() for x in (row.get("allowed_explicit_labels") or []) if isinstance(x, str) and str(x).strip()}
        auth_per_row.append(labs)
    hints = _project_clause_referent_prompt_hints(art)
    assert hints
    for h in hints:
        projected = {str(x).strip() for x in (h.get("allowed_explicit_labels") or []) if isinstance(x, str)}
        assert projected
        assert any(projected <= row_auth for row_auth in auth_per_row if row_auth)


def test_narration_plan_bundle_transport_single_referent_root_ctir_unchanged() -> None:
    """Bundle is transport-only; CTIR is not rewritten; renderer_inputs carries one referent artifact."""
    world = _world_npcs(
        {"id": "npc_a", "name": "Alpha", "location": "s1"},
        {"id": "npc_b", "name": "Beta", "location": "s1"},
    )
    kw = _base_narration_kwargs(
        world=world,
        user_text="Alpha, what of Beta?",
        public_scene={"id": "s1", "visible_facts": [], "exits": [], "enemies": []},
        scene=_scene_envelope("s1"),
    )
    session = dict(kw["session"])
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_b",
        "active_interaction_kind": "question",
        "interaction_mode": "social",
    }
    _attach_ctir(
        session,
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={
            "interaction_mode": "social",
            "active_target_id": "npc_b",
            "responder_target": {"id": "npc_a", "name": "Alpha"},
        },
        narrative_anchors={
            **_anchors_empty(),
            "actors_speakers": [{"id": "npc_a", "name": "Alpha"}, {"id": "npc_b", "name": "Beta"}],
        },
    )
    ctir_snapshot = copy.deepcopy(get_attached_ctir(session))
    merged = {**kw, "session": session}
    ensure_narration_plan_bundle_for_manual_ctir_tests(session, merged)
    bundle = build_narration_plan_bundle(session=session, narration_context_kwargs=merged)
    try:
        assert get_attached_ctir(session) == ctir_snapshot
        ri = bundle.get("renderer_inputs") or {}
        referent_like = [k for k, v in ri.items() if isinstance(v, dict) and "version" in v and "active_entities" in v]
        assert referent_like == ["referent_tracking"]
        rt = ri["referent_tracking"]
        assert isinstance(rt, dict)
        if "clause_referent_plan" in rt:
            json.dumps(rt["clause_referent_plan"])
        tp = ri.get("turn_packet")
        if isinstance(tp, dict):
            compact = tp.get("referent_tracking_compact")
            if isinstance(compact, dict):
                assert set(compact.keys()) == REFERENT_TRACKING_COMPACT_KEYS
                assert "clause_referent_plan" not in compact
    finally:
        detach_ctir(session)


def test_compressed_prompt_payload_no_top_level_duplicate_clause_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No parallel root-level clause plan artifact beside referent_tracking on the narration payload."""
    world = _world_npcs({"id": "npc_x", "name": "Xavier", "location": "s1"})
    kw = _base_narration_kwargs(
        world=world,
        user_text="Xavier?",
        public_scene={"id": "s1", "visible_facts": [], "exits": [], "enemies": []},
        scene=_scene_envelope("s1"),
    )
    session = dict(kw["session"])
    session["interaction_context"] = {
        "active_interaction_target_id": "npc_x",
        "active_interaction_kind": "question",
        "interaction_mode": "social",
    }
    _attach_ctir(
        session,
        resolution={"kind": "question", "social": {"npc_reply_expected": True}},
        interaction={"interaction_mode": "social", "active_target_id": "npc_x"},
        narrative_anchors={**_anchors_empty(), "actors_speakers": [{"id": "npc_x", "name": "Xavier"}]},
    )
    merged = {**kw, "session": session, "include_non_public_prompt_keys": True}
    ensure_narration_plan_bundle_for_manual_ctir_tests(session, merged)

    from game import narration_visibility

    def _stub_contract(**_: Any) -> dict[str, Any]:
        return _vis(ids=["npc_x"], names=["Xavier"], kinds={"npc_x": "npc"})

    monkeypatch.setattr(narration_visibility, "build_narration_visibility_contract", _stub_contract)
    try:
        ctx = build_narration_context(**merged)
    finally:
        detach_ctir(session)

    assert "clause_referent_plan" not in ctx
    rt = ctx.get("referent_tracking")
    assert isinstance(rt, dict)
    if rt.get("clause_referent_plan"):
        assert isinstance(rt["clause_referent_plan"], list)
    hints = ctx.get("referent_clause_prompt_hints")
    if hints is None:
        assert rt.get("clause_referent_plan") in (None, [])
    else:
        assert isinstance(hints, list)
        assert all("clause_id" in row for row in hints)


def test_compact_only_validation_never_emits_clause_specific_categories() -> None:
    """Without a full artifact, gate observability does not fabricate clause-plan-driven categories."""
    compact = referent_compact_mirror(referential_ambiguity_class="ambiguous_plural", ambiguity_risk=80)
    r = validate_referent_clarity("He waits.", referent_tracking=None, referent_tracking_compact=compact)
    cats = [c for c in (r.get("referent_violation_categories") or []) if str(c).startswith("clause_")]
    assert cats == []


def test_repair_skips_unauthorized_clause_label_even_when_structurally_eligible() -> None:
    """Repairs never substitute labels not authorized on the full artifact."""
    art = minimal_full_referent_artifact(
        single_unambiguous_entity=None,
        referential_ambiguity_class="ambiguous_plural",
        continuity_subject={"entity_id": "npc_runner", "display_name": "Runner", "source": "test"},
        safe_explicit_fallback_labels=[
            {"entity_id": "npc_gate", "safe_explicit_label": "Gate sergeant"},
            {"entity_id": "npc_runner", "safe_explicit_label": "Runner"},
        ],
        allowed_named_references=[
            {"entity_id": "npc_gate", "display_name": "Gate sergeant"},
            {"entity_id": "npc_runner", "display_name": "Runner"},
        ],
        active_entities=[
            {"entity_id": "npc_gate", "display_name": "Gate sergeant", "entity_kind": "npc", "roles": []},
            {"entity_id": "npc_runner", "display_name": "Runner", "entity_kind": "npc", "roles": []},
        ],
        active_entity_order=["npc_gate", "npc_runner"],
        clause_referent_plan=[
            {
                "clause_id": "n5:speaker_subject:0",
                "clause_kind": "speaker_subject",
                "subject_candidate_ids": ["npc_gate"],
                "object_candidate_ids": [],
                "preferred_subject_id": "npc_gate",
                "preferred_object_id": None,
                "allowed_explicit_labels": ["Totally Unauthorized Label"],
                "risky_pronoun_buckets": ["he_him"],
                "target_switch_sensitive": False,
                "ambiguity_class": "ambiguous_plural",
            }
        ],
    )
    gm = {"prompt_context": {"referent_tracking": art}}
    text, dbg, _ = _apply_referent_clarity_emission_layer("They hesitate.", gm_output=gm)
    assert text == "They hesitate."
    assert dbg.get("referent_repair_applied") is False
    assert "Totally Unauthorized" not in text


def test_clause_sourced_repair_uses_minimal_single_pronoun_strategy() -> None:
    """Clause-driven repair stays the bounded first-pronoun substitution path (no paragraph rewrite)."""
    art = minimal_full_referent_artifact(
        single_unambiguous_entity=None,
        referential_ambiguity_class="ambiguous_plural",
        continuity_subject={"entity_id": "npc_runner", "display_name": "Runner", "source": "test"},
        safe_explicit_fallback_labels=[
            {"entity_id": "npc_gate", "safe_explicit_label": "Gate sergeant"},
            {"entity_id": "npc_runner", "safe_explicit_label": "Runner"},
        ],
        allowed_named_references=[
            {"entity_id": "npc_gate", "display_name": "Gate sergeant"},
            {"entity_id": "npc_runner", "display_name": "Runner"},
        ],
        active_entities=[
            {"entity_id": "npc_gate", "display_name": "Gate sergeant", "entity_kind": "npc", "roles": []},
            {"entity_id": "npc_runner", "display_name": "Runner", "entity_kind": "npc", "roles": []},
        ],
        active_entity_order=["npc_gate", "npc_runner"],
        clause_referent_plan=[
            {
                "clause_id": "n5:speaker_subject:0",
                "clause_kind": "speaker_subject",
                "subject_candidate_ids": ["npc_gate"],
                "object_candidate_ids": [],
                "preferred_subject_id": "npc_gate",
                "preferred_object_id": None,
                "allowed_explicit_labels": ["Gate sergeant"],
                "risky_pronoun_buckets": ["he_him"],
                "target_switch_sensitive": False,
                "ambiguity_class": "ambiguous_plural",
            }
        ],
    )
    gm = {"prompt_context": {"referent_tracking": art}}
    text, dbg, _ = _apply_referent_clarity_emission_layer("They wait. They leave.", gm_output=gm)
    assert text.startswith("Gate sergeant")
    assert ". They leave." in text or text.endswith("They leave.")
    assert dbg.get("referent_repair_strategy") == "replace_first_risky_pronoun_with_explicit_label"


def test_narration_plan_bundle_module_does_not_construct_clause_rows_directly() -> None:
    """Transport layer delegates clause plan construction to referent_tracking only."""
    src = inspect.getsource(importlib.import_module("game.narration_plan_bundle"))
    assert "build_clause_referent_plan" not in src


def test_clause_referent_plan_rows_bounded_and_json_safe_when_present() -> None:
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
    assert len(plan) <= 8
    json.dumps(plan)
