"""CF5 — registry and extraction contract tests for golden replay projection."""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

import tests.helpers.golden_replay_projection_extractors as extractors
import tests.helpers.golden_replay_projection_registry as registry_module
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

BACKUP_PATH = Path(__file__).resolve().parents[1] / "tests" / "helpers" / "golden_replay_projection.py.bak"


def _load_backup_module():
    source = BACKUP_PATH.read_text(encoding="utf-8")
    mod = types.ModuleType("golden_replay_projection_backup_for_registry")
    sys.modules[mod.__name__] = mod
    exec(compile(source, str(BACKUP_PATH), "exec"), mod.__dict__)
    return mod


def test_ak5_protected_observation_field_paths_are_sorted_unique():
    paths = protected_observation_field_paths()
    assert paths == tuple(sorted(set(paths)))
    assert len(paths) == len(protected_observation_field_registry())


def test_ao1_protected_extraction_registry_matches_observation_registry():
    registry_paths = {field.path for field in protected_observation_field_registry()}
    extraction_paths = set(protected_observation_extraction_registry())
    assert extraction_paths == registry_paths
    assert len(extraction_paths) == 41


def _spec_rows(registry):
    return tuple(
        (
            path,
            spec.path,
            spec.source,
            spec.fem_source_keys,
            spec.sanitizer_lineage_trace_key,
            spec.sanitizer_lineage_context_key,
            spec.trace_container,
            spec.raw_presence,
            spec.normalized_presence,
            spec.unavailable_key,
        )
        for path, spec in registry.items()
    )


def test_cl6_extraction_registry_contents_identical_to_backup():
    backup = _load_backup_module()
    assert _spec_rows(registry_module.protected_observation_extraction_registry()) == _spec_rows(
        backup.protected_observation_extraction_registry()
    )


def test_cl6_extraction_registry_ordering_unchanged_from_backup():
    backup = _load_backup_module()
    assert tuple(registry_module.protected_observation_extraction_registry()) == tuple(
        backup.protected_observation_extraction_registry()
    )


def test_cl6_every_protected_field_has_exactly_one_extraction_spec():
    registry = registry_module.protected_observation_extraction_registry()
    protected_paths = tuple(field.path for field in protected_observation_field_registry())

    assert tuple(registry) == protected_paths
    assert len(registry) == len(set(registry)) == len(protected_paths)
    assert all(path == spec.path for path, spec in registry.items())


def test_cl6_extractor_compatibility_reexports_registry_symbols():
    assert extractors._PROTECTED_EXTRACTION_SPECS is registry_module._PROTECTED_EXTRACTION_SPECS
    assert extractors._ProtectedExtractionSpec is registry_module._ProtectedExtractionSpec
    assert extractors._FlatObservedFieldExtractor is registry_module._FlatObservedFieldExtractor
    assert extractors._SanitizerLineageObservedExtractor is registry_module._SanitizerLineageObservedExtractor
    assert extractors.protected_observation_extraction_registry is (
        registry_module.protected_observation_extraction_registry
    )
    assert extractors.protected_observation_extraction_source_by_path is (
        registry_module.protected_observation_extraction_source_by_path
    )


def test_bl2_every_protected_field_has_registry_or_special_case_handling():
    """Each protected path must map to a registry source handled by flat or trace projection."""
    sources_by_path = protected_observation_extraction_source_by_path()
    registry_paths = {field.path for field in protected_observation_field_registry()}
    assert set(sources_by_path) == registry_paths

    flat_sources = registry_module.protected_flat_extraction_sources()
    trace_sources = registry_module.protected_trace_extraction_sources()
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
