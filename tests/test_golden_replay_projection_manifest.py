"""CF5 — manifest parity tests for golden replay projection."""
from __future__ import annotations

import pytest

from tests.helpers.golden_replay_projection import (
    extract_protected_observation_manifest_section,
    protected_observation_field_registry,
    protected_observation_manifest_field_rows,
    protected_observation_manifest_section_is_current,
    render_protected_observation_manifest_section,
)
from tests.helpers.golden_replay_projection_test_support import load_manifest_refresh_tool

pytestmark = pytest.mark.unit


def test_protected_replay_manifest_matches_observation_registry():
    refresh_mod = load_manifest_refresh_tool()
    manifest_text = refresh_mod.MANIFEST_PATH.read_text(encoding="utf-8")
    expected = render_protected_observation_manifest_section()
    current = extract_protected_observation_manifest_section(manifest_text)

    assert current is not None, "protected replay manifest is missing generated protected_field_paths section"
    assert current == expected, (
        "protected replay manifest generated section is out of date; "
        "run: python tools/refresh_protected_replay_manifest.py --write"
    )
    assert protected_observation_manifest_section_is_current(manifest_text)
    assert render_protected_observation_manifest_section() == expected

    paths = tuple(sorted({field.path for field in protected_observation_field_registry()}))
    assert str(len(paths)) in current
    for field in protected_observation_field_registry():
        assert f"| `{field.path}` | `{field.drift_bucket}` |" in current


def test_ak5_manifest_generated_section_matches_registry():
    refresh_mod = load_manifest_refresh_tool()
    registry_paths = {field.path: field.drift_bucket for field in protected_observation_field_registry()}
    manifest_paths = dict(protected_observation_manifest_field_rows())

    assert set(registry_paths) == set(manifest_paths)
    for path, bucket in registry_paths.items():
        assert manifest_paths[path] == bucket
    assert protected_observation_manifest_section_is_current(
        refresh_mod.MANIFEST_PATH.read_text(encoding="utf-8")
    )
