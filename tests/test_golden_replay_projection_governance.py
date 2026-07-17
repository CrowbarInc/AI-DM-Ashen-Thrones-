"""CF5 — governance and facade contract tests for golden replay projection."""
from __future__ import annotations

import inspect

import pytest

import tests.helpers.golden_replay_projection as projection
from tests.helpers.golden_replay_projection_test_support import load_manifest_refresh_tool
from tests.helpers.replay_observed_row_fixtures import synthetic_observed_replay_row

pytestmark = pytest.mark.unit


def test_bl5_replay_projection_closeout_governance():
    """BL closeout: canonical projection surface only; no deprecated duplicate helpers."""
    deprecated_names = (
        "protected_field_paths",
        "project_replay_turn_observation",
        "read_fem_meta_from_gate_output",
        "build_runtime_lineage_events_from_fem",
        "_build_raw_signal_presence",
        "_build_normalized_signal_presence",
        "_compute_unavailable_paths",
        "_build_missing_source_by_field",
    )
    for name in deprecated_names:
        assert not hasattr(projection, name), f"deprecated replay projection alias {name!r} must not remain"

    canonical_public = (
        "project_turn_observation",
        "protected_observation_field_paths",
        "protected_observation_field_registry",
        "protected_observation_extraction_registry",
        "protected_observation_default_row",
        "observed_projection_schema_defaults",
        "render_protected_observation_manifest_section",
        "extract_protected_observation_manifest_section",
        "protected_observation_manifest_section_is_current",
    )
    for name in canonical_public:
        assert hasattr(projection, name), f"missing canonical projection API {name!r}"
        assert callable(getattr(projection, name))

    assert len(projection.protected_observation_field_paths()) == 41
    assert len(projection.protected_observation_extraction_registry()) == 41
    assert hasattr(projection, "_build_projection_status")
    assert hasattr(projection, "_project_flat_protected_observed_fields")

    refresh_mod = load_manifest_refresh_tool()
    refresh_source = inspect.getsource(refresh_mod)
    assert "protected_observation_field_paths" in refresh_source
    assert "render_protected_observation_manifest_section" in refresh_source
    assert "extract_protected_observation_manifest_section" in refresh_source
    assert "protected_observation_manifest_registry_parity_errors" in refresh_source
    assert "protected_field_paths(" not in refresh_source

    flat_protected = set(projection.protected_observation_flat_field_paths())
    classifier_row = synthetic_observed_replay_row(profile="classifier_probe")
    dashboard_row = synthetic_observed_replay_row(profile="dashboard_probe")
    assert flat_protected == set(projection.protected_observation_default_row())
    assert flat_protected <= set(classifier_row)
    assert flat_protected <= set(dashboard_row)
