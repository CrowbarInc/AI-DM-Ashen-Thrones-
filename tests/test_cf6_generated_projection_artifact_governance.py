"""CF6 — generated projection artifact governance contracts."""
from __future__ import annotations

import pytest

import tests.helpers.golden_replay_artifact_manifest as manifest_module

pytestmark = pytest.mark.unit


def test_projection_artifact_importance_values_are_canonical() -> None:
    for family in manifest_module.golden_replay_artifact_families():
        assert family.importance in manifest_module.PROJECTION_ARTIFACT_IMPORTANCE_VALUES
    for artifact in manifest_module.projection_generated_artifact_inventory():
        assert artifact.importance in manifest_module.PROJECTION_ARTIFACT_IMPORTANCE_VALUES


def test_every_artifact_family_has_single_owner_and_generator() -> None:
    for family in manifest_module.golden_replay_artifact_families():
        assert family.owner_module
        assert family.generator
        assert family.review_owner
        assert family.test_owner
        assert family.governance_owner
        assert family.regenerate_triggers
        assert family.consumer


def test_acceptance_critical_artifacts_are_ci_gated() -> None:
    critical = manifest_module.projection_acceptance_critical_artifacts()
    assert critical, "expected at least one acceptance-critical generated artifact"
    for artifact in critical:
        assert artifact.ci_required, f"{artifact.artifact_id} must be CI-required"
    ids = {artifact.artifact_id for artifact in critical}
    assert "protected_replay_manifest_field_paths" in ids


def test_advisory_and_diagnostic_artifacts_are_not_ci_required() -> None:
    non_acceptance = (
        manifest_module.IMPORTANCE_ADVISORY,
        manifest_module.IMPORTANCE_DIAGNOSTIC,
        manifest_module.IMPORTANCE_DEVELOPER_CONVENIENCE,
    )
    for artifact in manifest_module.projection_generated_artifact_inventory():
        if artifact.importance in non_acceptance:
            assert not artifact.ci_required, artifact.artifact_id


def test_local_only_families_are_developer_convenience() -> None:
    for family in manifest_module.golden_replay_artifact_families():
        if family.commit_policy == manifest_module.COMMIT_POLICY_LOCAL_ONLY:
            assert family.importance == manifest_module.IMPORTANCE_DEVELOPER_CONVENIENCE


def test_projection_corpus_refresh_bundle_is_documented_and_excludes_coverage() -> None:
    assert manifest_module.projection_corpus_refresh_artifact_paths_documented()
    coverage = manifest_module.golden_replay_artifact_family_by_id("projection_coverage_report")
    assert coverage is not None
    coverage_paths = set(coverage.paths)
    assert not coverage_paths & manifest_module.PROJECTION_CORPUS_REFRESH_ARTIFACT_PATHS


def test_failure_dashboard_cascade_families_share_dashboard_trigger() -> None:
    cascade_ids = manifest_module.failure_dashboard_cascade_family_ids()
    families = {
        family.family_id: family
        for family in manifest_module.golden_replay_artifact_families()
        if family.family_id in cascade_ids
    }
    assert len(families) == len(cascade_ids)
    for family in families.values():
        assert "ASHEN_WRITE_FAILURE_DASHBOARD=1" in family.regenerate_triggers


def test_projection_governance_reports_split_by_generator() -> None:
    gap = manifest_module.golden_replay_artifact_family_by_id("projection_gap_reality_report")
    drift = manifest_module.golden_replay_artifact_family_by_id("projection_drift_watch_report")
    coverage = manifest_module.golden_replay_artifact_family_by_id("projection_coverage_report")
    assert gap is not None and drift is not None and coverage is not None
    assert gap.generator != drift.generator != coverage.generator
    assert gap.importance == manifest_module.IMPORTANCE_ADVISORY
    assert drift.importance == manifest_module.IMPORTANCE_ADVISORY
    assert coverage.importance == manifest_module.IMPORTANCE_ADVISORY


def test_inventory_artifact_ids_are_unique() -> None:
    ids = [artifact.artifact_id for artifact in manifest_module.projection_generated_artifact_inventory()]
    assert len(ids) == len(set(ids))
