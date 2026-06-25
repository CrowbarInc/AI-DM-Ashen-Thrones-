from __future__ import annotations

from pathlib import Path

import pytest

import tests.helpers.failure_dashboard_paths as paths_module
import tests.helpers.golden_replay_artifact_manifest as manifest_module

REPO_ROOT = Path(__file__).resolve().parents[1]
GITIGNORE_PATH = REPO_ROOT / ".gitignore"
ARTIFACT_MANIFEST_DOC = REPO_ROOT / "artifacts" / "golden_replay" / "artifact_manifest.md"
ARTIFACT_README = REPO_ROOT / "artifacts" / "golden_replay" / "README.md"

FAILURE_DASHBOARD_CANONICAL_GOLDEN_REPLAY_PATHS: tuple[str, ...] = (
    paths_module.BUG_RECURRENCE_HISTORY_JSON_PATH.as_posix(),
    paths_module.BUG_RECURRENCE_HISTORY_MARKDOWN_PATH.as_posix(),
    paths_module.BUG_RECURRENCE_EVENT_LOG_JSON_PATH.as_posix(),
    paths_module.BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH.as_posix(),
    paths_module.RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH.as_posix(),
    paths_module.PROTECTED_REPLAY_FAILURE_REPORT_PATH.as_posix(),
    paths_module.RERUN_DRIFT_SCORECARD_JSON_PATH.as_posix(),
    paths_module.RERUN_DRIFT_SCORECARD_MARKDOWN_PATH.as_posix(),
    paths_module.LONG_SESSION_STABILITY_SCORECARD_JSON_PATH.as_posix(),
    paths_module.LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH.as_posix(),
    paths_module.OWNER_DRIFT_LONGITUDINAL_JSON_PATH.as_posix(),
    paths_module.OWNER_DRIFT_LONGITUDINAL_MARKDOWN_PATH.as_posix(),
    paths_module.OWNER_DRIFT_HOTSPOTS_JSON_PATH.as_posix(),
    paths_module.OWNER_DRIFT_HOTSPOTS_MARKDOWN_PATH.as_posix(),
    paths_module.OWNER_DRIFT_TRENDS_JSON_PATH.as_posix(),
    paths_module.OWNER_DRIFT_TRENDS_MARKDOWN_PATH.as_posix(),
    paths_module.OWNER_DRIFT_RISK_JSON_PATH.as_posix(),
    paths_module.OWNER_DRIFT_RISK_MARKDOWN_PATH.as_posix(),
)


def test_artifact_manifest_docs_exist() -> None:
    assert ARTIFACT_README.is_file()
    assert ARTIFACT_MANIFEST_DOC.is_file()


@pytest.mark.parametrize("family_id", [family.family_id for family in manifest_module.golden_replay_artifact_families()])
def test_artifact_manifest_doc_mentions_each_family(family_id: str) -> None:
    text = ARTIFACT_MANIFEST_DOC.read_text(encoding="utf-8")
    assert f"`{family_id}`" in text


def test_failure_dashboard_canonical_paths_are_documented_in_manifest_registry() -> None:
    assert manifest_module.failure_dashboard_canonical_paths_documented()
    documented = manifest_module.golden_replay_artifact_manifest_doc_paths()
    for path in FAILURE_DASHBOARD_CANONICAL_GOLDEN_REPLAY_PATHS:
        assert path in documented


def test_local_regenerable_paths_are_gitignored_and_manifest_local_only() -> None:
    gitignore = GITIGNORE_PATH.read_text(encoding="utf-8")
    local_only_paths = manifest_module.golden_replay_artifact_paths_by_commit_policy(
        manifest_module.COMMIT_POLICY_LOCAL_ONLY
    )
    assert local_only_paths
    for path in local_only_paths:
        assert path.replace("/", "\\") in gitignore or path in gitignore
    for family in manifest_module.golden_replay_artifact_families():
        if family.commit_policy == manifest_module.COMMIT_POLICY_LOCAL_ONLY:
            assert family.retention_class == manifest_module.RETENTION_REPRODUCIBLE_LOCAL_OUTPUT


def test_protected_canonical_evidence_is_not_local_only() -> None:
    local_only = manifest_module.golden_replay_artifact_paths_by_commit_policy(
        manifest_module.COMMIT_POLICY_LOCAL_ONLY
    )
    for path in manifest_module.PROTECTED_CANONICAL_EVIDENCE_PATHS:
        assert path.as_posix() not in local_only


def test_replay_maintenance_metrics_paths_use_local_only_policy() -> None:
    family = manifest_module.golden_replay_artifact_family_by_id("replay_maintenance_metrics")
    assert family is not None
    assert family.commit_policy == manifest_module.COMMIT_POLICY_LOCAL_ONLY
    assert manifest_module.REPLAY_MAINTENANCE_METRICS_JSON_PATH.as_posix() in family.paths
    assert manifest_module.REPLAY_MAINTENANCE_METRICS_MARKDOWN_PATH.as_posix() in family.paths


def test_artifact_family_ids_are_unique() -> None:
    ids = [family.family_id for family in manifest_module.golden_replay_artifact_families()]
    assert len(ids) == len(set(ids))
