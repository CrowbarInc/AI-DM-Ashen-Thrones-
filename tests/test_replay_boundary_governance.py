"""Replay / projection ownership boundary governance (tests only).

This module owns **replay and acceptance-projection boundary locks** that keep golden replay,
protected observation manifests, and runtime vs acceptance projection modules separated from
gate orchestration and subsystem legality ownership (Cycles AO5, BI-8, BG-1).

This is **not** the global test-responsibility ownership registry. Registry identity,
inventory parity, and registry neighbor relationship assertions remain in
``tests/test_ownership_registry.py``.

Implementation helpers live in ``tests/ownership_guard_bi8_golden_replay_boundary.py`` and
``tests/helpers/golden_replay_projection.py``.

- **BI-8 golden replay boundary** (Cycle BI-8): golden replay remains a consumer/bridge, not
  a subsystem legality owner. Enforced by ``test_bi8_golden_replay_ownership_boundary_is_locked``.
- **BG-1 protected replay manifest parity** (Cycle BG-1): manifest generation stays
  registry-backed and parity-checked. Enforced by
  ``test_bg1_protected_replay_manifest_registry_parity``.
- **AO5 runtime vs acceptance projection split** (Cycle AO5): runtime lineage projection and
  acceptance observation projection stay separate modules. Enforced by
  ``test_ao5_runtime_and_acceptance_projection_modules_remain_separate``.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from tests.ownership_guard_bi8_golden_replay_boundary import (
    BI8_GOLDEN_REPLAY_OWNED_EXPORTS,
    collect_bi8_golden_replay_documentation_phrase_violations,
    collect_bi8_golden_replay_forbidden_export_violations,
    collect_bi8_golden_replay_forbidden_source_fragment_violations,
    load_bi8_golden_replay_target_sources,
    parse_bi8_golden_replay_api_exports,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_bi8_golden_replay_ownership_boundary_is_locked() -> None:
    """Cycle BI-8: replay remains an orchestration/observation bridge, not a subsystem owner."""
    target_sources = load_bi8_golden_replay_target_sources(_REPO_ROOT)
    combined_docs = '\n'.join(list(target_sources.values()))
    doc_violations = collect_bi8_golden_replay_documentation_phrase_violations(combined_docs)
    assert not doc_violations, '\n'.join(doc_violations)
    api_exports = parse_bi8_golden_replay_api_exports(target_sources)
    assert BI8_GOLDEN_REPLAY_OWNED_EXPORTS <= api_exports
    export_violations = collect_bi8_golden_replay_forbidden_export_violations(api_exports)
    assert not export_violations, '\n'.join(export_violations)
    helper_api_source = '\n'.join(
        (
            target_sources['tests/helpers/golden_replay.py'],
            target_sources['tests/helpers/golden_replay_api.py'],
        )
    )
    fragment_violations = collect_bi8_golden_replay_forbidden_source_fragment_violations(
        helper_api_source
    )
    assert not fragment_violations, '\n'.join(fragment_violations)


def test_bg1_protected_replay_manifest_registry_parity() -> None:
    """Cycle BG-1: manifest generation stays registry-backed and parity-checked."""
    import tests.helpers.golden_replay_projection as acceptance_projection

    spec = importlib.util.spec_from_file_location(
        'refresh_protected_replay_manifest',
        _REPO_ROOT / 'tools' / 'refresh_protected_replay_manifest.py',
    )
    assert spec is not None and spec.loader is not None
    refresh_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(refresh_mod)
    manifest_text = refresh_mod.MANIFEST_PATH.read_text(encoding='utf-8')
    assert acceptance_projection.protected_observation_manifest_registry_parity_errors(manifest_text) == []
    assert acceptance_projection.protected_observation_manifest_section_is_current(manifest_text)
    registry_paths = {field.path for field in acceptance_projection.protected_observation_field_registry()}
    assert registry_paths == set(acceptance_projection.protected_observation_field_paths())
    assert (
        tuple((path for path, _bucket in acceptance_projection.protected_observation_manifest_field_rows()))
        == acceptance_projection.protected_observation_field_paths()
    )
    registry_buckets = {
        field.path: field.drift_bucket
        for field in acceptance_projection.protected_observation_field_registry()
    }
    manifest_buckets = dict(acceptance_projection.protected_observation_manifest_field_rows())
    assert manifest_buckets == {
        path: acceptance_projection.protected_observation_drift_bucket(path)
        for path in acceptance_projection.protected_observation_field_paths()
    }
    for path, bucket in registry_buckets.items():
        assert acceptance_projection.protected_observation_drift_bucket(path) == bucket


def test_ao5_runtime_and_acceptance_projection_modules_remain_separate() -> None:
    """Cycle AO5: runtime lineage projection and acceptance observation projection stay split."""
    import game.final_emission_replay_projection as runtime_projection
    import tests.helpers.golden_replay_projection as acceptance_projection

    runtime_doc = (runtime_projection.__doc__ or '').lower()
    acceptance_doc = (acceptance_projection.__doc__ or '').lower()
    assert 'do not merge' in runtime_doc
    assert 'do not merge' in acceptance_doc
    assert 'golden_replay_projection' in runtime_doc
    assert 'final_emission_replay_projection' in acceptance_doc
    assert runtime_projection.__name__ == 'game.final_emission_replay_projection'
    assert acceptance_projection.__name__ == 'tests.helpers.golden_replay_projection'
    lineage_surface = runtime_projection.read_side_lineage_projection_surface()
    assert lineage_surface['mutation_lineage_key'] == 'final_emission_mutation_lineage'
    assert len(acceptance_projection.protected_observation_field_registry()) == len(
        acceptance_projection.protected_observation_field_paths()
    )
