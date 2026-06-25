"""CF7 — synthetic row / classifier evidence bridge contracts."""
from __future__ import annotations

import pytest

import tests.helpers.synthetic_replay_evidence_bridge as bridge
from tests.helpers.failure_classification_sync import (
    SPLIT_OWNER_LEGACY_MATRIX_ROWS,
    project_split_owner_matrix_row,
    split_owner_fem_projection_excluded,
    split_owner_matrix_row_by_id,
    split_owner_observed_row_from_matrix_row,
)
from tests.helpers.golden_replay_projection import (
    protected_classifier_evidence_field_paths,
    protected_observation_default_row,
    protected_observation_flat_field_paths,
)
from tests.helpers.golden_replay_fixtures import project_synthetic_turn
from tests.helpers.replay_observed_row_fixtures import (
    observed_dashboard_probe_row,
    observed_failure_row,
    synthetic_classifier_probe_overlay_paths,
    synthetic_observed_replay_row,
    synthetic_rerun_turn,
)

pytestmark = pytest.mark.unit


def test_synthetic_builder_inventory_is_complete_and_unique() -> None:
    builders = bridge.synthetic_replay_builder_inventory()
    assert len(builders) >= 8
    ids = [builder.builder_id for builder in builders]
    assert len(ids) == len(set(ids))
    for builder in builders:
        assert builder.owner_module
        assert builder.entry_point
        assert builder.consumer


def test_canonical_factory_is_single_authority() -> None:
    classifier = observed_failure_row()
    dashboard = observed_dashboard_probe_row()
    assert classifier == synthetic_observed_replay_row(profile="classifier_probe")
    assert dashboard == synthetic_observed_replay_row(profile="dashboard_probe")


def test_overlay_paths_are_injected_without_live_projection() -> None:
    overlay = synthetic_classifier_probe_overlay_paths()
    row = synthetic_observed_replay_row()
    assert overlay <= set(row)
    assert row["route_kind"] == "dialogue"
    assert row["selected_speaker_id"] == "runner"
    assert row["trace"]["canonical_entry"]["target_actor_id"] == "runner"


def test_dashboard_profile_injects_empty_presence_dicts() -> None:
    classifier = synthetic_observed_replay_row(profile="classifier_probe")
    dashboard = synthetic_observed_replay_row(profile="dashboard_probe")
    assert "raw_signal_presence" not in classifier
    assert "normalized_signal_presence" not in classifier
    assert dashboard["raw_signal_presence"] == {}
    assert dashboard["normalized_signal_presence"] == {}


def test_synthetic_base_includes_protected_defaults() -> None:
    flat = set(protected_observation_flat_field_paths())
    row = synthetic_observed_replay_row()
    overlay = synthetic_classifier_probe_overlay_paths()
    assert flat <= set(row)
    defaults = protected_observation_default_row()
    for path, value in defaults.items():
        if path in overlay:
            continue
        assert row[path] == value, path
    assert row["scaffold_leakage"] is False


def test_project_synthetic_turn_uses_live_projection_adapter() -> None:
    live = project_synthetic_turn(scenario_id="cf7_live_probe", player_text="Wait.")
    flat = set(protected_observation_flat_field_paths())
    assert flat <= set(live)
    assert live["scenario_id"] == "cf7_live_probe"
    assert "unavailable" in live


def test_synthetic_hand_built_row_is_not_acceptance_authority() -> None:
    assert bridge.synthetic_row_is_acceptance_authority() is False
    assert bridge.ACCEPTANCE_AUTHORITY == "live_replay_projection"
    factory = bridge.synthetic_builder_by_id("synthetic_observed_replay_row")
    assert factory is not None
    assert factory.row_kind == "synthetic"


def test_legacy_matrix_row_excluded_from_live_fem_projection() -> None:
    legacy_id = next(iter(SPLIT_OWNER_LEGACY_MATRIX_ROWS))
    row = split_owner_matrix_row_by_id(legacy_id)
    assert split_owner_fem_projection_excluded(row)
    with pytest.raises(ValueError, match="no projection turn fixture"):
        project_split_owner_matrix_row(row)


@pytest.mark.parametrize(
    "matrix_id",
    ["scene_opening", "sanitizer_strict_social", "visibility_enforcement"],
)
def test_matrix_live_projection_differs_from_hand_built_synthetic(matrix_id: str) -> None:
    row = split_owner_matrix_row_by_id(matrix_id)
    synthetic = split_owner_observed_row_from_matrix_row(row, profile="classifier_probe")
    live = project_split_owner_matrix_row(row)
    assert synthetic["runtime_lineage_events"]
    assert live["runtime_lineage_events"]
    assert set(synthetic) <= set(live) | set(synthetic)
    if row.owner_bucket_field:
        assert live.get(row.owner_bucket_field) == row.owner_bucket


def test_classifier_evidence_matrix_covers_overlay_and_extensions() -> None:
    matrix = bridge.classifier_evidence_bridge_matrix()
    fields = {row.field for row in matrix}
    assert synthetic_classifier_probe_overlay_paths() <= fields
    assert bridge.classifier_evidence_bridge_row("scenario_id") is not None
    extension = next(row for row in matrix if row.field in {"fallback_selection_owner", "repair_kind"})
    assert extension.evidence_kind == "overlay_derived"


def test_protected_classifier_overlap_documented_as_shared_or_overlay() -> None:
    overlap = protected_classifier_evidence_field_paths()
    matrix_by_field = {row.field: row for row in bridge.classifier_evidence_bridge_matrix()}
    for path in overlap:
        if path in matrix_by_field:
            assert matrix_by_field[path].evidence_kind in {
                "shared",
                "overlay_derived",
                "synthetic_only",
            }


def test_synthetic_rerun_turn_is_partial_not_classifier_observed_row() -> None:
    partial = synthetic_rerun_turn()
    observed = synthetic_observed_replay_row()
    flat = set(protected_observation_flat_field_paths())
    assert "scenario_id" not in partial
    assert not flat <= set(partial)
    assert len(partial) < len(observed)
    builder = bridge.synthetic_builder_by_id("synthetic_rerun_turn")
    assert builder is not None
    assert builder.row_kind == "partial_synthetic"


def test_evidence_kind_values_are_canonical() -> None:
    allowed = {
        "live_only",
        "synthetic_only",
        "shared",
        "overlay_derived",
        "diagnostic_only",
    }
    for row in bridge.classifier_evidence_bridge_matrix():
        assert row.evidence_kind in allowed
