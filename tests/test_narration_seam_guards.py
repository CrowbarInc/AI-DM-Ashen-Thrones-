"""Runtime seam guard helpers (Block C)."""

from __future__ import annotations

from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.narration_plan_bundle import attach_narration_plan_bundle
from game.narration_seam_guards import (
    NARRATION_PATH_MATRIX,
    REGISTERED_NARRATION_PATH_KINDS,
    annotate_narration_path_kind,
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


def test_path_matrix_covers_runtime_rows() -> None:
    kinds = {row["path"] for row in NARRATION_PATH_MATRIX}
    assert any("resolved_turn" in k for k in kinds)
    md = path_matrix_markdown()
    assert "CTIR-backed" in md
    assert len(md.splitlines()) >= 3


def test_registered_path_kinds_non_empty() -> None:
    assert len(REGISTERED_NARRATION_PATH_KINDS) >= 8
