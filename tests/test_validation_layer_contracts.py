"""Contract tests for ``game.validation_layer_contracts`` (Objective #11)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from game import validation_layer_contracts as vlc


def _module_source_path() -> Path:
    spec = vlc.__spec__
    assert spec is not None
    assert spec.origin is not None
    return Path(spec.origin)


def _collect_import_roots(source: str) -> set[str]:
    tree = ast.parse(source)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def test_na_shadow_response_delta_reason_token_stable() -> None:
    assert vlc.NA_SHADOW_RESPONSE_DELTA_FAILURE_REASON == "follow_up_missing_signal_shadow_response_delta"


def test_canonical_layer_ids_are_stable() -> None:
    assert vlc.CANONICAL_VALIDATION_LAYERS == (
        "engine",
        "planner",
        "gpt",
        "gate",
        "evaluator",
    )


def test_each_responsibility_domain_resolves_to_exactly_one_owner_layer() -> None:
    owners: set[str] = set()
    for spec in vlc.responsibility_domains():
        owner = vlc.owner_layer_for_responsibility_domain(spec.domain_id)
        owners.add(owner)
        vlc.assert_domain_maps_to_kind_owner(spec.domain_id)
        assert owner == vlc.canonical_layer_for_kind(spec.kind)
    assert owners == set(vlc.CANONICAL_VALIDATION_LAYERS)


def test_each_kind_maps_to_single_canonical_layer() -> None:
    for kind in vlc.RESPONSIBILITY_KINDS:
        layer = vlc.canonical_layer_for_kind(kind)
        assert layer in vlc.CANONICAL_VALIDATION_LAYERS


def test_forbidden_ownership_combinations_reject_non_canonical_pairs() -> None:
    for layer in vlc.CANONICAL_VALIDATION_LAYERS:
        for kind in vlc.RESPONSIBILITY_KINDS:
            canonical = vlc.KIND_TO_CANONICAL_LAYER[kind]
            forbidden = layer != canonical
            assert vlc.is_forbidden_layer_kind_claim(layer, kind) is forbidden
            if forbidden:
                with pytest.raises(AssertionError):
                    vlc.assert_layer_does_not_claim_forbidden_kind(layer, kind)
            else:
                vlc.assert_layer_does_not_claim_forbidden_kind(layer, kind)


def test_evaluator_read_only_non_enforcement() -> None:
    assert vlc.classify_layer_read_only_non_enforcement(vlc.EVALUATOR) is True
    for layer in vlc.CANONICAL_VALIDATION_LAYERS:
        expected = layer == vlc.EVALUATOR
        assert vlc.classify_layer_read_only_non_enforcement(layer) is expected


def test_gate_non_scoring_classification() -> None:
    assert vlc.classify_layer_non_scoring_gate(vlc.GATE) is True
    for layer in vlc.CANONICAL_VALIDATION_LAYERS:
        assert vlc.classify_layer_non_scoring_gate(layer) is (layer == vlc.GATE)


def test_gpt_non_truth_non_legality_expression() -> None:
    assert vlc.classify_layer_non_truth_non_legality_expression(vlc.GPT) is True
    assert vlc.is_expression_owner(vlc.GPT) is True
    assert vlc.is_truth_owner(vlc.GPT) is False
    assert vlc.is_legality_owner(vlc.GPT) is False


def test_planner_non_truth_authority() -> None:
    assert vlc.classify_layer_non_truth_authority_planner(vlc.PLANNER) is True
    assert vlc.is_structure_owner(vlc.PLANNER) is True
    assert vlc.is_truth_owner(vlc.PLANNER) is False


def test_predicates_with_optional_domain_id() -> None:
    domain = "world_simulation_and_persistence_truth"
    assert vlc.is_truth_owner(vlc.ENGINE, domain_id=domain) is True
    assert vlc.is_truth_owner(vlc.PLANNER, domain_id=domain) is False
    delta_domain = "response_delta_enforcement_and_repair"
    assert vlc.is_legality_owner(vlc.GATE, domain_id=delta_domain) is True


def test_forward_read_matrix_is_acyclic_under_canonical_order() -> None:
    order = list(vlc.CANONICAL_VALIDATION_LAYERS)
    for i, reader in enumerate(order):
        for j, writer in enumerate(order):
            if j > i:
                assert vlc.layer_may_read_layer(reader, writer) is False
            if j <= i:
                assert vlc.layer_may_read_layer(reader, writer) is True


def test_module_remains_import_light_no_game_imports() -> None:
    src = _module_source_path().read_text(encoding="utf-8")
    roots = _collect_import_roots(src)
    assert "game" not in roots


def test_forbidden_claims_tuple_matches_derived_set() -> None:
    derived = {
        (layer, kind)
        for layer in vlc.CANONICAL_VALIDATION_LAYERS
        for kind in vlc.RESPONSIBILITY_KINDS
        if layer != vlc.KIND_TO_CANONICAL_LAYER[kind]
    }
    assert set(vlc.forbidden_layer_kind_claims()) == derived


def test_narrative_mode_output_legality_domain_registered() -> None:
    spec = vlc.RESPONSIBILITY_DOMAIN_BY_ID.get("narrative_mode_output_legality_checks")
    assert spec is not None
    assert spec.kind == vlc.KIND_LEGALITY
    assert vlc.owner_layer_for_responsibility_domain("narrative_mode_output_legality_checks") == vlc.GATE
