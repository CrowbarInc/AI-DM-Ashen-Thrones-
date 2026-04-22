"""Runtime seam invariants for Objective #11 Block B (validation layer separation).

These tests pin ownership boundaries without duplicating full integration suites. File splits under
``game.final_emission_*`` remain one canonical **gate** layer; imports here assert that fact.
"""

from __future__ import annotations

import ast
from pathlib import Path

from game import api as game_api
from game import final_emission_gate as feg
from game import validation_layer_contracts as vlc
from game.narrative_authenticity import (
    build_narrative_authenticity_contract,
    repair_narrative_authenticity_minimal,
)


def _collect_import_from_modules(source: str) -> set[str]:
    tree = ast.parse(source)
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name)
    return out


def test_response_delta_domain_maps_to_gate_layer() -> None:
    assert vlc.owner_layer_for_responsibility_domain("response_delta_enforcement_and_repair") == vlc.GATE
    assert vlc.is_legality_owner(vlc.GATE, domain_id="response_delta_enforcement_and_repair") is True


def test_na_shadow_reason_constant_is_stable_cross_module() -> None:
    assert vlc.NA_SHADOW_RESPONSE_DELTA_FAILURE_REASON == "follow_up_missing_signal_shadow_response_delta"


def test_na_repair_does_not_target_gate_owned_shadow_delta_reason() -> None:
    c = build_narrative_authenticity_contract()
    val = {"failure_reasons": [vlc.NA_SHADOW_RESPONSE_DELTA_FAILURE_REASON]}
    fixed = repair_narrative_authenticity_minimal(
        "The guard repeats the same answer without a new detail.",
        val,
        c,
        gm_output={},
    )
    assert fixed == (None, None)


def test_live_api_and_gate_do_not_import_offline_evaluator() -> None:
    """Evaluator scoring must stay read-only to live legality (no harness imports on hot paths)."""
    api_src = Path(game_api.__file__).read_text(encoding="utf-8")
    gate_src = Path(feg.__file__).read_text(encoding="utf-8")
    for label, src in (("game.api", api_src), ("game.final_emission_gate", gate_src)):
        assert "narrative_authenticity_eval" not in src, f"{label} must not import narrative_authenticity_eval"
        assert "evaluate_narrative_authenticity" not in src, f"{label} must not reference evaluate_narrative_authenticity"
    # Sanity: gate still wires canonical gate-local modules (same layer, not duplicate ownership).
    assert "final_emission_repairs" in gate_src
    assert "final_emission_validators" in gate_src


def test_legality_meta_keys_distinct_from_na_telemetry_keys() -> None:
    from game.final_emission_meta import NARRATIVE_AUTHENTICITY_FEM_KEYS

    rd_legality = set(_default_response_delta_meta_keys())
    na_fem = set(NARRATIVE_AUTHENTICITY_FEM_KEYS)
    assert not rd_legality & na_fem


def _default_response_delta_meta_keys() -> frozenset[str]:
    from game.final_emission_repairs import _default_response_delta_meta

    return frozenset(_default_response_delta_meta().keys())


def test_final_emission_gate_imports_are_gate_layer_not_evaluator() -> None:
    src = Path(feg.__file__).read_text(encoding="utf-8")
    modules = _collect_import_from_modules(src)
    assert any(m and m.startswith("game.final_emission_repairs") for m in modules)
    assert not any(m == "game.narrative_authenticity_eval" for m in modules)


def test_evaluator_read_only_predicate_matches_contract() -> None:
    assert vlc.classify_layer_read_only_non_enforcement(vlc.EVALUATOR) is True
    assert vlc.classify_layer_read_only_non_enforcement(vlc.GATE) is False


def test_planner_structure_without_truth_claim_on_response_delta_domain() -> None:
    assert vlc.is_structure_owner(vlc.PLANNER, domain_id="prompt_and_guard_structure") is True
    assert vlc.is_legality_owner(vlc.PLANNER, domain_id="response_delta_enforcement_and_repair") is False
