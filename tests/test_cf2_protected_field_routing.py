"""CF2 — table-driven contracts for protected field source/default/unavailable routing."""
from __future__ import annotations

import pytest

from tests.helpers.golden_replay_fixtures import minimal_turn_payload, project_synthetic_turn
from tests.helpers.golden_replay_projection import (
    observed_projection_schema_defaults,
    project_turn_observation,
    protected_observation_default_row,
    protected_observation_extraction_registry,
    protected_observation_field_registry,
    protected_observation_flat_field_paths,
)
from tests.helpers.golden_replay_projection_presence import (
    _missing_source_by_field_from_presence,
    protected_path_covered_by_unavailable,
    protected_path_representation_errors,
)
from tests.helpers.protected_field_routing_contract import (
    build_protected_field_routing_matrix,
    protected_field_routing_matrix_by_path,
)
from tests.helpers.replay_observed_row_fixtures import synthetic_observed_replay_row

pytestmark = pytest.mark.unit

_FLAT_DEFAULTS = protected_observation_default_row()
_MATRIX = protected_field_routing_matrix_by_path()

# Fields explicitly listed unavailable on a sparse turn (BL3 lock + CF2 extension).
_SPARSE_UNAVAILABLE = frozenset(
    {
        "fallback_family",
        "final_emitted_source",
        "response_type_candidate_ok",
        "response_type_repair_used",
        "response_type_required",
        "route_kind",
        "selected_speaker_id",
        "trace.canonical_entry",
        "trace.social_contract_trace",
        "trace.turn_trace",
    }
)


def test_cf2_routing_matrix_covers_every_protected_field() -> None:
    registry_paths = {field.path for field in protected_observation_field_registry()}
    matrix_paths = {row.field for row in build_protected_field_routing_matrix()}
    assert matrix_paths == registry_paths
    assert len(matrix_paths) == 41


def test_cf2_extraction_registry_and_routing_matrix_aligned() -> None:
    assert set(protected_observation_extraction_registry()) == set(_MATRIX)


def test_cf2_routing_matrix_rows_have_machine_readable_ownership_metadata() -> None:
    for path, row in _MATRIX.items():
        assert row.field == path
        assert row.field_name == path
        assert row.source_family
        assert row.source_path
        assert row.field_owner_group
        assert row.default_behavior in {
            "flat_default_none",
            "flat_default_empty_string",
            "flat_default_false",
            "nested_trace_no_flat_default",
        }
        assert row.unavailable_behavior in {
            "projected_none",
            "trace_container_empty",
            "covered_by_trace_container",
            "represented_when_null",
        }
        assert row.raw_presence_expectation in {
            "not_tracked",
            "route",
            "speaker",
            "fem_key",
            "fem_dual_family",
        }
        assert row.normalized_presence_expectation in {"tracked", "not_tracked"}
        assert row.projection_owner.startswith("extractor spec owner:")
        assert row.extractor_spec_owner.endswith("golden_replay_projection_registry._PROTECTED_EXTRACTION_SPECS")
        assert "golden_replay_projection_presence._build_projection_status" in row.presence_policy_owner
        assert "golden_replay_projection_presence._unavailable_paths_for_projection" in row.unavailable_policy_owner
        assert "golden_replay_projection_presence.protected_path_is_represented" in row.representation_policy_owner
        assert row.test_owner.endswith(".py")


def test_cf2_presence_expectation_keys_are_machine_readable() -> None:
    for row in _MATRIX.values():
        if row.raw_presence_expectation == "not_tracked":
            assert row.raw_presence_key is None
            assert row.missing_source_rule == "not tracked"
        else:
            assert row.raw_presence_key
            assert row.missing_source_rule != "not tracked"

        if row.normalized_presence_expectation == "tracked":
            assert row.normalized_source is not None
            assert row.normalized_presence_key == row.field
        else:
            assert row.normalized_presence_key is None


def test_cf2_unavailable_behavior_is_machine_readable() -> None:
    for row in _MATRIX.values():
        if row.unavailable_behavior in {"projected_none", "trace_container_empty"}:
            assert row.unavailable_key
            assert "unavailable" in row.unavailable_rule
        elif row.unavailable_behavior == "covered_by_trace_container":
            assert row.unavailable_key is None
            assert row.field.startswith("trace.")
        else:
            assert row.unavailable_behavior == "represented_when_null"
            assert row.unavailable_key is None


def test_cf2_known_owner_groups_are_declared_for_ambiguous_field_families() -> None:
    assert _MATRIX["fallback_family"].field_owner_group == "replay_fallback_family_projection"
    assert _MATRIX["opening_fallback_owner_bucket"].field_owner_group == "owner_bucket_read_views"
    assert _MATRIX["selected_speaker_id"].field_owner_group == "replay_speaker_projection"
    assert _MATRIX["trace.canonical_entry.target_actor_id"].field_owner_group == "replay_trace_projection"
    assert _MATRIX["response_type_required"].field_owner_group == "response_type_metadata"
    assert _MATRIX["upstream_prepared_emission_source"].field_owner_group == "upstream_prepared_emission_metadata"


@pytest.mark.parametrize("path", protected_observation_flat_field_paths())
def test_cf2_neutral_default_row_matrix(path: str) -> None:
    """Every flat protected path declares an explicit schema default."""
    default = _FLAT_DEFAULTS[path]
    row = _MATRIX[path]
    assert row.default == default
    if path == "scaffold_leakage":
        assert default is False
    elif path == "final_text":
        assert default == ""
    else:
        assert default is None


def test_cf2_synthetic_row_includes_schema_defaults_not_unavailable_mask() -> None:
    """Synthetic rows use defaults; they must not pretend unavailable fields were projected."""
    schema = observed_projection_schema_defaults()
    classifier = synthetic_observed_replay_row(profile="classifier_probe")
    dashboard = synthetic_observed_replay_row(profile="dashboard_probe")

    for path in protected_observation_flat_field_paths():
        assert path in schema
        assert classifier[path] is not None or _FLAT_DEFAULTS[path] is None
        assert dashboard[path] is not None or _FLAT_DEFAULTS[path] is None

    assert schema["unavailable"] == []
    assert "unavailable" not in classifier or classifier.get("unavailable") == []


def test_cf2_sparse_turn_unavailable_routing_matrix() -> None:
    observed = project_turn_observation(
        minimal_turn_payload(
            scenario_id="cf2_sparse_unavailable",
            gm_text="Rain on the gate road.",
        )
    )
    assert set(observed["unavailable"]) == _SPARSE_UNAVAILABLE
    for path in _SPARSE_UNAVAILABLE:
        if path.startswith("trace."):
            assert protected_path_covered_by_unavailable(path, frozenset(observed["unavailable"]))
        else:
            assert path in observed["unavailable"]
            assert observed[path] is None


def test_cf2_sparse_turn_null_fields_not_confused_with_unavailable() -> None:
    """Fields without unavailable_key project None but remain represented (not unavailable)."""
    observed = project_turn_observation(
        minimal_turn_payload(
            scenario_id="cf2_sparse_null_represented",
            gm_text="Quiet road.",
        )
    )
    represented_without_unavailable = (
        "resolution_kind",
        "opening_recovered_via_fallback",
        "sanitizer_empty_fallback_used",
        "final_text",
        "scaffold_leakage",
    )
    for path in represented_without_unavailable:
        assert path not in observed["unavailable"]
        assert protected_path_covered_by_unavailable(path, frozenset(observed["unavailable"])) is False
    assert observed["final_text"] == "Quiet road."
    assert observed["scaffold_leakage"] is False
    assert protected_path_representation_errors(observed) == []


def test_cf2_unavailable_vs_missing_source_distinction_on_sparse_turn() -> None:
    observed = project_turn_observation(
        minimal_turn_payload(
            scenario_id="cf2_sparse_missing_source",
            gm_text="Rain.",
        )
    )
    assert observed["missing_source_by_field"]["route_kind"] == "runtime_missing_raw_absent"
    assert observed["missing_source_by_field"]["final_emitted_source"] == "runtime_missing_raw_absent"
    assert observed["raw_signal_presence"]["route_kind"] is False
    assert observed["normalized_signal_presence"]["final_emitted_source"] is False
    assert "route_kind" in observed["unavailable"]
    assert observed["route_kind"] is None


@pytest.mark.parametrize(
    "raw_signal,normalized_signal,field,expected",
    [
        pytest.param(
            {"final_emitted_source": False},
            {},
            "final_emitted_source",
            "runtime_missing_raw_absent",
            id="raw_absent",
        ),
        pytest.param(
            {"final_emitted_source": True},
            {"final_emitted_source": True},
            "final_emitted_source",
            "projection_missing_raw_present",
            id="raw_and_normalized_present",
        ),
        pytest.param(
            {"final_emitted_source": True},
            {"final_emitted_source": False},
            "final_emitted_source",
            "normalized_view_missing_raw_present",
            id="normalization_gap",
        ),
        pytest.param(
            {"route_kind": True},
            {},
            "route_kind",
            "projection_missing_raw_present",
            id="raw_present_no_normalized_track",
        ),
    ],
)
def test_cf2_missing_source_by_field_routing_matrix(
    raw_signal: dict[str, bool],
    normalized_signal: dict[str, bool],
    field: str,
    expected: str,
) -> None:
    result = _missing_source_by_field_from_presence(raw_signal, normalized_signal)
    assert result[field] == expected


def test_cf2_rich_turn_clears_unavailable_for_fem_backed_fields() -> None:
    from tests.helpers.golden_replay_fixtures import fem_payload, minimal_gm_output_payload

    fem = fem_payload(
        final_emitted_source="generated_candidate",
        response_type_required="dialogue_response",
        response_type_repair_used=False,
        response_type_candidate_ok=True,
        fallback_family_used="social",
    )
    observed = project_synthetic_turn(
        scenario_id="cf2_rich_unavailable_cleared",
        gm_text="The runner speaks.",
        resolution={"kind": "question", "social": {"npc_id": "runner"}},
        payload=minimal_gm_output_payload(
            fem_meta=fem,
            metadata={
                "debug_traces": [
                    {
                        "turn_trace": {"social_contract_trace": {"route_selected": "dialogue"}},
                        "canonical_entry": {"target_actor_id": "runner"},
                    }
                ],
            },
        ),
    )
    for key in (
        "fallback_family",
        "final_emitted_source",
        "response_type_required",
        "route_kind",
        "selected_speaker_id",
    ):
        assert key not in observed["unavailable"]
    assert observed["fallback_family"] == "social"
    assert protected_path_representation_errors(observed) == []


def test_cf2_classifier_overlay_defaults_can_mask_absent_producer() -> None:
    """Document risk: synthetic classifier rows supply non-null values for probe fields."""
    row = synthetic_observed_replay_row(profile="classifier_probe")
    assert row["route_kind"] == "dialogue"
    assert row["selected_speaker_id"] == "runner"
    assert row["final_emitted_source"] == "generated_candidate"
    sparse = project_turn_observation(
        minimal_turn_payload(scenario_id="cf2_contrast", gm_text="Rain.")
    )
    assert sparse["route_kind"] is None
    assert sparse["selected_speaker_id"] is None
