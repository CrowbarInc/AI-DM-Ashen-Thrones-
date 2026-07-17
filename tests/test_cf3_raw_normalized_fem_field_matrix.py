"""CF3 — table-driven contracts for raw vs normalized FEM field families."""
from __future__ import annotations

import pytest

from game.final_emission_meta import normalize_final_emission_meta_for_observability
from game.final_emission_replay_projection import normalize_fem_for_replay_acceptance
from game.realization_provenance import REALIZATION_FALLBACK_FAMILY_FIELD

from tests.helpers.fem_normalization_contract import (
    build_fem_backed_field_matrix,
    fem_backed_protected_field_paths,
    normalize_fem_for_replay,
)
from tests.helpers.golden_replay_fixtures import fem_payload, minimal_gm_output_payload, project_synthetic_turn
from tests.helpers.golden_replay_projection import project_turn_observation
from tests.helpers.golden_replay_projection_extractors import (
    _extract_fem_flat_observed_fields,
    _fem_has_any_key,
)
from tests.helpers.golden_replay_projection_fallbacks import project_replay_fallback_family_from_fem
from tests.helpers.opening_fallback_evidence import opening_dual_family_fem_meta

pytestmark = pytest.mark.unit

_FEM_BACKED = fem_backed_protected_field_paths()
_MATRIX = build_fem_backed_field_matrix()


def test_cf3_fem_matrix_covers_all_fem_backed_protected_fields() -> None:
    assert len(_FEM_BACKED) == 20
    assert len(_MATRIX) == 20
    assert {row.protected_field for row in _MATRIX} == set(_FEM_BACKED)


def test_cf3_replay_normalization_adapter_delegates_to_meta_owner() -> None:
    raw = opening_dual_family_fem_meta(realization_family="upstream_prepared_emission")
    assert normalize_fem_for_replay_acceptance(raw) == normalize_final_emission_meta_for_observability(raw)


@pytest.mark.parametrize("path", _FEM_BACKED)
def test_cf3_normalization_preserves_flat_fem_key_values(path: str) -> None:
    """Observability normalization must not rewrite protected flat FEM stamps."""
    row = next(r for r in _MATRIX if r.protected_field == path)
    raw = opening_dual_family_fem_meta(
        realization_family="upstream_prepared_emission",
        final_emitted_source="generated_candidate",
        response_type_required="dialogue_response",
        upstream_prepared_emission_used=True,
        upstream_prepared_emission_valid=True,
        sealed_fallback_owner_bucket="strict-social-sealed",
        visibility_fallback_owner_bucket="opening-visibility",
    )
    normalized = normalize_fem_for_replay(raw)
    for key in row.raw_fem_keys:
        if key in raw:
            assert normalized.get(key) == raw.get(key), f"{path}.{key} value changed during normalization"


@pytest.mark.parametrize(
    "path",
    [row.protected_field for row in _MATRIX if row.normalized_presence_tracked],
)
def test_cf3_normalized_presence_tracked_fields_have_raw_and_normalized_keys(path: str) -> None:
    row = next(r for r in _MATRIX if r.protected_field == path)
    assert row.raw_presence_kind in {"fem_key", "fem_dual_family"}
    assert row.normalized_presence_tracked is True


def test_cf3_dual_fallback_family_keys_survive_normalization() -> None:
    raw = opening_dual_family_fem_meta(realization_family="legacy_diegetic_fallback")
    normalized = normalize_fem_for_replay(raw)
    assert normalized["fallback_family_used"] == "scene_opening"
    assert normalized[REALIZATION_FALLBACK_FAMILY_FIELD] == "legacy_diegetic_fallback"
    assert project_replay_fallback_family_from_fem(raw) == project_replay_fallback_family_from_fem(normalized)


def test_cf3_dead_turn_normalization_does_not_mutate_flat_fem_fields() -> None:
    raw = fem_payload(
        final_emitted_source="generated_candidate",
        dead_turn={"is_dead_turn": True, "validation_playable": False},
    )
    normalized = normalize_fem_for_replay(raw)
    assert normalized["final_emitted_source"] == "generated_candidate"
    assert isinstance(normalized["dead_turn"], dict)
    assert normalized["dead_turn"]["is_dead_turn"] is True


def test_cf3_malformed_dead_turn_filled_without_touching_projection_fields() -> None:
    raw = fem_payload(
        final_emitted_source="upstream_prepared_emission",
        response_type_required="dialogue_response",
    )
    raw["dead_turn"] = "not-a-mapping"
    observed = project_synthetic_turn(
        scenario_id="cf3_malformed_dead_turn",
        gm_text="Rain.",
        payload=minimal_gm_output_payload(fem_meta=raw),
    )
    assert observed["final_emitted_source"] == "upstream_prepared_emission"
    assert observed["raw_signal_presence"]["final_emitted_source"] is True
    assert observed["normalized_signal_presence"]["final_emitted_source"] is True


def test_cf3_rich_turn_raw_and_normalized_presence_parity() -> None:
    """When flat FEM keys exist, raw and normalized presence maps agree."""
    observed = project_synthetic_turn(
        scenario_id="cf3_presence_parity",
        gm_text="The runner speaks.",
        resolution={"kind": "question", "social": {"npc_id": "runner"}},
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(
                final_emitted_source="generated_candidate",
                response_type_required="dialogue_response",
                upstream_prepared_emission_used=True,
                upstream_prepared_emission_valid=True,
                fallback_family_used="social",
                realization_fallback_family="upstream_prepared_emission",
            ),
        ),
    )
    tracked = [
        "final_emitted_source",
        "response_type_required",
        "upstream_prepared_emission_used",
        "fallback_family",
    ]
    for field in tracked:
        assert observed["raw_signal_presence"][field] is True
        assert observed["normalized_signal_presence"][field] is True


def test_cf3_sparse_turn_fem_keys_absent_in_both_presence_maps() -> None:
    observed = project_turn_observation(
        {
            "scenario_id": "cf3_sparse_fem",
            "snap": {"gm_text": "Quiet.", "turn_index": 0},
            "payload": minimal_gm_output_payload(),
        }
    )
    unavailable_fields = {
        "final_emitted_source",
        "response_type_required",
        "fallback_family",
    }
    for field in unavailable_fields:
        assert observed["raw_signal_presence"][field] is False
        assert observed["normalized_signal_presence"][field] is False
        assert field in observed["unavailable"]
    assert observed["raw_signal_presence"]["upstream_prepared_emission_used"] is False
    assert observed["normalized_signal_presence"]["upstream_prepared_emission_used"] is False
    assert "upstream_prepared_emission_used" not in observed["unavailable"]


def test_cf3_projection_extracts_from_raw_fem_keys() -> None:
    raw = fem_payload(
        final_emitted_source="generated_candidate",
        response_type_repair_used=True,
        response_type_repair_kind="dialogue_minimal_repair",
    )
    flat = _extract_fem_flat_observed_fields(raw)
    assert flat["final_emitted_source"] == "generated_candidate"
    assert flat["response_type_repair_used"] is True
    assert flat["response_type_repair_kind"] == "dialogue_minimal_repair"


def test_cf3_final_emitted_source_multi_key_first_present_uses_raw_fem() -> None:
    raw = {
        "final_route": "replaced",
        "upstream_prepared_emission_source": "upstream_prepared_emission.prepared_text",
    }
    flat = _extract_fem_flat_observed_fields(raw)
    assert flat["final_emitted_source"] == "replaced"


def test_cf3_opening_owner_bucket_derived_not_normalized() -> None:
    observed = project_synthetic_turn(
        scenario_id="cf3_opening_bucket",
        gm_text="The gate opens.",
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(
                opening_recovered_via_fallback=True,
                opening_fallback_authorship_source="upstream_prepared_opening_fallback",
            ),
        ),
    )
    assert observed["opening_fallback_owner_bucket"] is not None
    assert "opening_fallback_owner_bucket" not in observed["unavailable"]


def test_cf3_na_list_coercion_does_not_add_protected_keys() -> None:
    raw = fem_payload(final_emitted_source="generated_candidate")
    raw["narrative_authenticity_failure_reasons"] = "not-a-list"
    normalized = normalize_fem_for_replay(raw)
    assert normalized["final_emitted_source"] == "generated_candidate"
    assert normalized["narrative_authenticity_failure_reasons"] == []
    assert "response_type_required" not in normalized or normalized.get("response_type_required") is None


def test_cf3_fem_has_any_key_matches_dual_family_presence() -> None:
    raw = opening_dual_family_fem_meta(realization_family="upstream_prepared_emission")
    keys = ("fallback_family_used", REALIZATION_FALLBACK_FAMILY_FIELD)
    assert _fem_has_any_key(raw, keys) is True
    assert _fem_has_any_key(normalize_fem_for_replay(raw), keys) is True
