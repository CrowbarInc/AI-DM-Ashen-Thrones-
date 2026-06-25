"""CF5 — registry and extraction contract tests for golden replay projection."""
from __future__ import annotations

import pytest

from tests.helpers.golden_replay_fixtures import minimal_turn_payload, project_synthetic_turn
from tests.helpers.golden_replay_projection import (
    protected_observation_extraction_registry,
    protected_observation_extraction_source_by_path,
    protected_observation_field_paths,
    protected_observation_field_registry,
    protected_path_representation_errors,
    project_turn_observation,
)
from tests.helpers.golden_replay_projection_test_support import ak5_rich_projection_payload

pytestmark = pytest.mark.unit


def test_ak5_protected_observation_field_paths_are_sorted_unique():
    paths = protected_observation_field_paths()
    assert paths == tuple(sorted(set(paths)))
    assert len(paths) == len(protected_observation_field_registry())


def test_ao1_protected_extraction_registry_matches_observation_registry():
    registry_paths = {field.path for field in protected_observation_field_registry()}
    extraction_paths = set(protected_observation_extraction_registry())
    assert extraction_paths == registry_paths
    assert len(extraction_paths) == 41


def test_bl2_every_protected_field_has_registry_or_special_case_handling():
    """Each protected path must map to a registry source handled by flat or trace projection."""
    sources_by_path = protected_observation_extraction_source_by_path()
    registry_paths = {field.path for field in protected_observation_field_registry()}
    assert set(sources_by_path) == registry_paths

    flat_sources = {
        "resolution",
        "route",
        "speaker",
        "fem_flat",
        "sanitizer_trace",
        "sanitizer_lineage",
        "sanitizer_lineage_legacy",
        "fem_opening_bucket",
        "fallback_family",
        "final_text",
        "scaffold",
    }
    trace_sources = {"trace_leaf"}
    for path, source in sources_by_path.items():
        if "." in path:
            assert source in trace_sources, f"{path!r} must use trace_leaf source, got {source!r}"
            continue
        assert source in flat_sources, f"{path!r} must use flat registry source, got {source!r}"


def test_ak5_every_protected_path_is_projected_or_marked_unavailable():
    """Each protected registry path must appear on the observed turn or in unavailable."""
    sparse = project_turn_observation(
        minimal_turn_payload(
            scenario_id="ak5_sparse_projection",
            gm_text="Rain on the gate road.",
        )
    )
    assert protected_path_representation_errors(sparse) == []

    rich = project_synthetic_turn(
        scenario_id="ak5_rich_projection",
        gm_text="The runner says the patrol moved east.",
        player_text="Ask the runner.",
        resolution={"kind": "question", "social": {"npc_id": "runner"}},
        payload=ak5_rich_projection_payload(),
    )
    assert protected_path_representation_errors(rich) == []
