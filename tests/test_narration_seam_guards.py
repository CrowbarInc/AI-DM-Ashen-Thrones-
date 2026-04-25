"""Runtime seam guard helpers (Block C)."""

from __future__ import annotations

from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.narration_plan_bundle import attach_narration_plan_bundle
from game.narration_seam_guards import (
    NARRATION_PATH_MATRIX,
    REGISTERED_NARRATION_PATH_KINDS,
    annotate_narration_continuation_classification,
    annotate_narration_path_kind,
    classify_narration_continuation_path,
    enforce_plan_driven_continuation_invariant,
    path_matrix_markdown,
    require_narration_plan_bundle_for_ctir_turn,
)


def test_require_narration_plan_bundle_ok_when_bundle_matches() -> None:
    session: dict = {}
    stamp = "1:abc:def"
    session[SESSION_CTIR_STAMP_KEY] = stamp
    attach_ctir(session, {"version": 1, "semantics": {"x": 1}})
    attach_narration_plan_bundle(
        session,
        {
            "plan_metadata": {"ctir_stamp": stamp},
            "narrative_plan": {"narrative_mode": "continuation"},
            "renderer_inputs": {},
        },
    )
    session["_runtime_narration_plan_bundle_stamp_v1"] = stamp
    out = require_narration_plan_bundle_for_ctir_turn(session, turn_stamp=stamp, owner_module=__name__)
    assert out["ok"] is True
    detach_ctir(session)


def test_annotate_merges_narration_seam() -> None:
    gm: dict = {"metadata": {"narration_seam": {"prior": True}, "other": 1}}
    annotate_narration_path_kind(
        gm,
        path_kind="test_path",
        ctir_backed=True,
        bundle_required=True,
        plan_driven=True,
    )
    seam = gm["metadata"]["narration_seam"]
    assert seam["prior"] is True
    assert seam["path_kind"] == "test_path"


def test_continuation_annotation_preserves_enforcement_fields() -> None:
    session: dict = {"debug_traces": []}
    stamp = "1:cont:enforcement"
    session[SESSION_CTIR_STAMP_KEY] = stamp
    attach_ctir(session, {"version": 1, "resolution": {"kind": "observe", "state_changes": {"scene_transition_occurred": False}}})
    attach_narration_plan_bundle(
        session,
        {
            "plan_metadata": {"ctir_stamp": stamp, "planning_session_interaction": {}},
            "narrative_plan": {"narrative_mode": "continuation", "active_pressures": {}},
            "renderer_inputs": {"narration_obligations": {}},
        },
    )
    session["_runtime_narration_plan_bundle_stamp_v1"] = stamp
    gm: dict = {"metadata": {"narration_seam": {}}}
    annotate_narration_path_kind(
        gm,
        path_kind="resolved_turn_ctir_bundle",
        ctir_backed=True,
        bundle_required=True,
        plan_driven=True,
    )
    annotate_narration_continuation_classification(gm, session=session)
    enforce_plan_driven_continuation_invariant(
        gm, session=session, bundle_seam_requirement={"ok": True}, turn_stamp=stamp
    )
    # Re-annotate (should merge, not wipe enforcement fields)
    annotate_narration_continuation_classification(gm, session=session)
    cont = gm["metadata"]["narration_seam"]["continuation"]
    assert cont.get("continuation_plan_verified") is True
    assert cont.get("continuation_source") == "narrative_plan_bundle"
    assert cont.get("continuation_enforcement_applied") is True
    detach_ctir(session)


def test_path_matrix_covers_runtime_rows() -> None:
    kinds = {row["path"] for row in NARRATION_PATH_MATRIX}
    assert any("resolved_turn" in k for k in kinds)
    md = path_matrix_markdown()
    assert "CTIR-backed" in md
    assert len(md.splitlines()) >= 3


def test_registered_path_kinds_non_empty() -> None:
    assert len(REGISTERED_NARRATION_PATH_KINDS) >= 8


def test_classify_ctir_bundle_continuation_plan_driven_when_not_opening() -> None:
    session: dict = {"debug_traces": []}
    stamp = "1:cont:ok"
    session[SESSION_CTIR_STAMP_KEY] = stamp
    # CTIR without transition-like opening signals.
    attach_ctir(
        session,
        {
            "version": 1,
            "resolution": {"kind": "observe", "state_changes": {"scene_transition_occurred": False}},
        },
    )
    attach_narration_plan_bundle(
        session,
        {
            "plan_metadata": {"ctir_stamp": stamp, "planning_session_interaction": {}},
            "narrative_plan": {"narrative_mode": "continuation", "active_pressures": {}},
            "renderer_inputs": {"narration_obligations": {}},
        },
    )
    session["_runtime_narration_plan_bundle_stamp_v1"] = stamp
    gm: dict = {"metadata": {}}
    annotate_narration_path_kind(
        gm,
        path_kind="resolved_turn_ctir_bundle",
        ctir_backed=True,
        bundle_required=True,
        plan_driven=True,
        emergency_nonplan_output=False,
    )
    annotate_narration_continuation_classification(gm, session=session)
    cont = gm["metadata"]["narration_seam"]["continuation"]
    assert cont["is_continuation_turn"] is True
    assert cont["continuation_path_kind"] in ("plan_driven_continuation", "pressure_driven_continuation")
    assert cont["requires_plan_driven_continuation"] is True
    assert cont["allows_nonplan_output"] is False
    assert any(str(x).startswith("opening_reason:") for x in cont["reason_codes"])
    detach_ctir(session)


def test_classify_scene_opening_is_not_continuation_turn() -> None:
    session: dict = {"debug_traces": []}
    stamp = "1:open:ok"
    session[SESSION_CTIR_STAMP_KEY] = stamp
    attach_ctir(
        session,
        {
            "version": 1,
            "resolution": {"kind": "observe", "state_changes": {"scene_transition_occurred": True}},
        },
    )
    attach_narration_plan_bundle(
        session,
        {
            "plan_metadata": {"ctir_stamp": stamp, "planning_session_interaction": {}},
            "narrative_plan": {
                "narrative_mode": "continuation",
                # Minimal scene_opening stub; validate_scene_opening is exercised elsewhere.
                "scene_opening": {"beat": "arrival", "focus": "establishing"},
                "active_pressures": {},
            },
            "renderer_inputs": {"narration_obligations": {"scene_opening_required": True}},
        },
    )
    session["_runtime_narration_plan_bundle_stamp_v1"] = stamp
    status = classify_narration_continuation_path(
        session=session,
        narration_seam={
            "path_kind": "resolved_turn_ctir_bundle",
            "ctir_backed": True,
            "bundle_required": True,
            "plan_driven": True,
            "emergency_nonplan_output": False,
            "explicit_nonplan_model_narration": False,
        },
    )
    assert status["is_continuation_turn"] is False
    assert status["continuation_path_kind"] is None
    assert "turn_is_scene_opening" in status["reason_codes"]
    detach_ctir(session)


def test_classify_explicit_nonplan_model_narration_not_marked_plan_driven() -> None:
    out = classify_narration_continuation_path(
        session=None,
        narration_seam={
            "path_kind": "non_resolution_model_narration",
            "ctir_backed": False,
            "bundle_required": False,
            "plan_driven": False,
            "emergency_nonplan_output": False,
            "explicit_nonplan_model_narration": True,
        },
    )
    assert out["is_continuation_turn"] is True
    assert out["continuation_path_kind"] == "explicit_nonplan_model_narration"
    assert out["requires_plan_driven_continuation"] is False
    assert out["allows_nonplan_output"] is True
    assert "seam_explicit_nonplan_model_narration" in out["reason_codes"]


def test_classify_emergency_terminal_fallback_is_emergency_nonplan() -> None:
    out = classify_narration_continuation_path(
        session=None,
        narration_seam={
            "path_kind": "resolved_turn_ctir_force_terminal_fallback",
            "ctir_backed": True,
            "bundle_required": True,
            "plan_driven": False,
            "emergency_nonplan_output": True,
            "explicit_nonplan_model_narration": False,
        },
    )
    assert out["is_continuation_turn"] is True
    assert out["continuation_path_kind"] == "emergency_nonplan_output"
    assert out["allows_nonplan_output"] is True
    assert "seam_emergency_nonplan_output" in out["reason_codes"]


def test_classification_json_safe_and_reason_codes_stable_strings() -> None:
    out = classify_narration_continuation_path(
        session=None,
        narration_seam={
            "path_kind": "engine_check_required_prompt",
            "ctir_backed": False,
            "bundle_required": False,
            "plan_driven": False,
            "emergency_nonplan_output": False,
            "explicit_nonplan_model_narration": False,
        },
    )
    assert isinstance(out["is_continuation_turn"], bool)
    assert (out["continuation_path_kind"] is None) or isinstance(out["continuation_path_kind"], str)
    assert isinstance(out["requires_plan_driven_continuation"], bool)
    assert isinstance(out["allows_nonplan_output"], bool)
    assert isinstance(out["reason_codes"], list)
    assert all(isinstance(x, str) for x in out["reason_codes"])
