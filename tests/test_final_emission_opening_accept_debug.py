"""BU2-C: opening-accepted-candidate debug ownership under final_emission_opening_fallback."""

from __future__ import annotations

import inspect
from typing import Any

import pytest

import game.final_emission_finalize as emission_finalize
import game.final_emission_non_strict_stack as non_strict_stack
import game.final_emission_opening_fallback as opening_fallback
import game.final_emission_terminal_pipeline as terminal_pipeline
from game.final_emission_boundary_contract import assert_final_emission_mutation_allowed
from game.observability_attribution_read import FINAL_EMISSION_META_KEY
from game.final_emission_text_formatting import _normalize_text

pytestmark = pytest.mark.unit


def _scene_opening_debug_preview(text: str, *, limit: int = 120) -> str:
    clean = _normalize_text(text)
    return (clean[:limit] + "…") if len(clean) > limit else clean


def _inline_patch_scene_opening_candidate_emission_debug(
    out: dict[str, Any],
    *,
    accepted_scene_opening_text: str | None,
) -> None:
    """Pre-BU2-C inline body preserved for equivalence checks."""
    if not isinstance(out, dict):
        return
    md = out.setdefault("metadata", {})
    if not isinstance(md, dict):
        md = {}
        out["metadata"] = md
    em = md.setdefault("emission_debug", {})
    if not isinstance(em, dict):
        em = {}
        md["emission_debug"] = em
    accepted = _normalize_text(accepted_scene_opening_text or "")
    emitted = _normalize_text(out.get("player_facing_text") or "")
    em["scene_opening_candidate_len"] = len(accepted)
    em["scene_opening_emitted_len"] = len(emitted)
    em["scene_opening_candidate_emitted_match"] = bool(accepted) and emitted == accepted
    em["scene_opening_accepted_candidate_promoted"] = bool(accepted) and emitted == accepted
    em["response_type_candidate_preview"] = _scene_opening_debug_preview(accepted)
    em["response_type_emitted_preview"] = _scene_opening_debug_preview(emitted)

    fem = out.get(FINAL_EMISSION_META_KEY)
    if isinstance(fem, dict):
        fem["response_type_candidate_preview"] = em["response_type_candidate_preview"]
        fem["response_type_emitted_preview"] = em["response_type_emitted_preview"]


def _inline_reassert_scene_opening_accepted_candidate(
    out: dict[str, Any],
    *,
    accepted_scene_opening_text: str | None,
    source: str,
) -> None:
    """Pre-BU2-C inline body preserved for equivalence checks."""
    accepted = _normalize_text(accepted_scene_opening_text or "")
    if not accepted:
        return
    if _normalize_text(out.get("player_facing_text") or "") != accepted:
        assert_final_emission_mutation_allowed(
            "restore_accepted_scene_opening_candidate",
            source=source,
        )
        out["player_facing_text"] = accepted
    _inline_patch_scene_opening_candidate_emission_debug(
        out,
        accepted_scene_opening_text=accepted,
    )
    assert _normalize_text(out.get("player_facing_text") or "") == accepted


def _sample_out(*, player_facing_text: str = "Rain on the gate.", accepted: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "player_facing_text": player_facing_text,
        "metadata": {"emission_debug": {}},
        FINAL_EMISSION_META_KEY: {},
    }
    if accepted is not None:
        out["_accepted"] = accepted
    return out


def test_patch_scene_opening_candidate_emission_debug_matches_inline_sequence() -> None:
    accepted = "Rain on the gate. Guards watch the choke."
    inline_out = _sample_out(player_facing_text=accepted, accepted=accepted)
    helper_out = _sample_out(player_facing_text=accepted, accepted=accepted)

    _inline_patch_scene_opening_candidate_emission_debug(
        inline_out,
        accepted_scene_opening_text=accepted,
    )
    opening_fallback.patch_scene_opening_candidate_emission_debug(
        helper_out,
        accepted_scene_opening_text=accepted,
    )

    assert inline_out == helper_out


def test_reassert_scene_opening_accepted_candidate_matches_inline_sequence() -> None:
    accepted = "Rain on the gate. Guards watch the choke."
    stale = "You stand at the gate."

    inline_out = _sample_out(player_facing_text=stale)
    helper_out = _sample_out(player_facing_text=stale)
    source = "test.reassert_scene_opening_accepted_candidate"

    _inline_reassert_scene_opening_accepted_candidate(
        inline_out,
        accepted_scene_opening_text=accepted,
        source=source,
    )
    opening_fallback.reassert_scene_opening_accepted_candidate(
        helper_out,
        accepted_scene_opening_text=accepted,
        source=source,
    )

    assert inline_out == helper_out


def test_reassert_scene_opening_accepted_candidate_noop_when_text_already_matches() -> None:
    accepted = "Rain on the gate."
    out = _sample_out(player_facing_text=accepted)

    opening_fallback.reassert_scene_opening_accepted_candidate(
        out,
        accepted_scene_opening_text=accepted,
        source="test.noop",
    )

    assert out["player_facing_text"] == accepted
    em = out["metadata"]["emission_debug"]
    assert em["scene_opening_candidate_emitted_match"] is True
    assert em["scene_opening_accepted_candidate_promoted"] is True


def test_non_strict_stack_delegates_opening_accept_debug_patch() -> None:
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    assert "opening_fallback.patch_scene_opening_candidate_emission_debug(" in nss_src
    assert "final_emission_finalize" not in nss_src
    assert nss_src.index("scene_opening_rt_contract_accept_path_promotes_candidate(") < nss_src.index(
        "opening_fallback.patch_scene_opening_candidate_emission_debug("
    )
    assert nss_src.index("opening_fallback.patch_scene_opening_candidate_emission_debug(") < nss_src.index(
        "_compute_scene_emit_integrity_assessment("
    )


def test_terminal_pipeline_delegates_opening_accept_reassert() -> None:
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "opening_fallback.reassert_scene_opening_accepted_candidate(" in tp_src
    assert "final_emission_finalize" not in tp_src
    assert tp_src.index("merge_narration_constraint_debug_into_outputs(") < tp_src.index(
        "opening_fallback.reassert_scene_opening_accepted_candidate("
    )


def test_finalize_delegates_opening_accept_reassert_at_exit() -> None:
    fin_src = inspect.getsource(emission_finalize.finalize_emission_output)
    assert "reassert_scene_opening_accepted_candidate(" in fin_src
    assert fin_src.index("strip_appended_route_illegal_contamination_sentences(") < fin_src.index(
        "reassert_scene_opening_accepted_candidate("
    )
    assert fin_src.index("reassert_scene_opening_accepted_candidate(") < fin_src.index(
        "package_dead_turn_snapshot_into_final_emission_meta("
    )
