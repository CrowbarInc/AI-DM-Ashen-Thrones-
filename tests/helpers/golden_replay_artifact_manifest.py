"""Golden replay artifact retention manifest (CE6).

Read-side registry classifying ``artifacts/golden_replay/`` outputs by retention
policy. Does not write artifacts or change replay behavior.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tests.helpers.failure_dashboard_paths import (
    BUG_RECURRENCE_EVENT_LOG_JSON_PATH,
    BUG_RECURRENCE_HISTORY_JSON_PATH,
    BUG_RECURRENCE_HISTORY_MARKDOWN_PATH,
    BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH,
    FAILURE_DASHBOARD_ENV_VAR,
    LONG_SESSION_STABILITY_SCORECARD_ENV_VAR,
    LONG_SESSION_STABILITY_SCORECARD_JSON_PATH,
    LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH,
    OWNER_DRIFT_HOTSPOTS_JSON_PATH,
    OWNER_DRIFT_HOTSPOTS_MARKDOWN_PATH,
    OWNER_DRIFT_LONGITUDINAL_JSON_PATH,
    OWNER_DRIFT_LONGITUDINAL_MARKDOWN_PATH,
    OWNER_DRIFT_RISK_JSON_PATH,
    OWNER_DRIFT_RISK_MARKDOWN_PATH,
    OWNER_DRIFT_TRENDS_JSON_PATH,
    OWNER_DRIFT_TRENDS_MARKDOWN_PATH,
    PROTECTED_REPLAY_FAILURE_REPORT_PATH,
    RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH,
    RERUN_DRIFT_SCORECARD_ENV_VAR,
    RERUN_DRIFT_SCORECARD_JSON_PATH,
    RERUN_DRIFT_SCORECARD_MARKDOWN_PATH,
)

RETENTION_CANONICAL_VERSIONED_EVIDENCE = "canonical_versioned_evidence"
RETENTION_REPRODUCIBLE_LOCAL_OUTPUT = "reproducible_local_output"
RETENTION_TEMPORARY_SESSION_OUTPUT = "temporary_session_output"
RETENTION_HISTORICAL_BASELINE = "historical_baseline"
RETENTION_REDUNDANT_PAIRED_OUTPUT = "redundant_paired_output"

COMMIT_POLICY_COMMIT = "commit"
COMMIT_POLICY_LOCAL_ONLY = "local_only"
COMMIT_POLICY_BASELINE_FREEZE = "baseline_freeze"
COMMIT_POLICY_PAIRED_MIRROR = "paired_mirror"

GOLDEN_REPLAY_ARTIFACT_ROOT = Path("artifacts/golden_replay")
GOLDEN_REPLAY_ARTIFACT_README_PATH = GOLDEN_REPLAY_ARTIFACT_ROOT / "README.md"
GOLDEN_REPLAY_ARTIFACT_MANIFEST_DOC_PATH = GOLDEN_REPLAY_ARTIFACT_ROOT / "artifact_manifest.md"

REPLAY_MAINTENANCE_METRICS_JSON_PATH = GOLDEN_REPLAY_ARTIFACT_ROOT / "replay_maintenance_metrics.json"
REPLAY_MAINTENANCE_METRICS_MARKDOWN_PATH = GOLDEN_REPLAY_ARTIFACT_ROOT / "replay_maintenance_metrics.md"
PROTECTED_REPLAY_OBSERVATION_CORPUS_PATH = GOLDEN_REPLAY_ARTIFACT_ROOT / "replay_failure_corpus_observations.md"

LOCAL_REGENERABLE_ARTIFACT_PATHS: tuple[Path, ...] = (
    REPLAY_MAINTENANCE_METRICS_JSON_PATH,
    REPLAY_MAINTENANCE_METRICS_MARKDOWN_PATH,
    RERUN_DRIFT_SCORECARD_JSON_PATH,
    RERUN_DRIFT_SCORECARD_MARKDOWN_PATH,
    LONG_SESSION_STABILITY_SCORECARD_JSON_PATH,
    LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH,
)

PROTECTED_CANONICAL_EVIDENCE_PATHS: tuple[Path, ...] = (
    PROTECTED_REPLAY_FAILURE_REPORT_PATH,
    PROTECTED_REPLAY_OBSERVATION_CORPUS_PATH,
    GOLDEN_REPLAY_ARTIFACT_ROOT / "trend_window" / "manifest.json",
    GOLDEN_REPLAY_ARTIFACT_ROOT / "trend_window_2" / "manifest.json",
)


@dataclass(frozen=True)
class GoldenReplayArtifactFamily:
    """One artifact family under ``artifacts/golden_replay/``."""

    family_id: str
    retention_class: str
    owner_module: str
    paths: tuple[str, ...]
    regenerate_command: str
    commit_policy: str
    notes: str = ""


def _path_str(path: Path | str) -> str:
    return Path(path).as_posix()


def golden_replay_artifact_families() -> tuple[GoldenReplayArtifactFamily, ...]:
    """Return the canonical artifact-family retention registry."""
    env_dashboard = f"{FAILURE_DASHBOARD_ENV_VAR}=1 pytest"
    env_rerun = f"{RERUN_DRIFT_SCORECARD_ENV_VAR}=1 pytest"
    env_stability = f"{LONG_SESSION_STABILITY_SCORECARD_ENV_VAR}=1 pytest"
    return (
        GoldenReplayArtifactFamily(
            family_id="protected_replay_failure_report",
            retention_class=RETENTION_CANONICAL_VERSIONED_EVIDENCE,
            owner_module="tests.helpers.failure_dashboard_report",
            paths=(_path_str(PROTECTED_REPLAY_FAILURE_REPORT_PATH),),
            regenerate_command=env_dashboard,
            commit_policy=COMMIT_POLICY_COMMIT,
            notes="Curated protected-replay failure narrative; acceptance audit evidence.",
        ),
        GoldenReplayArtifactFamily(
            family_id="protected_replay_observation_corpus",
            retention_class=RETENTION_CANONICAL_VERSIONED_EVIDENCE,
            owner_module="tests.helpers.protected_replay_observation_corpus",
            paths=(_path_str(PROTECTED_REPLAY_OBSERVATION_CORPUS_PATH),),
            regenerate_command="python tools/expand_protected_replay_observations.py",
            commit_policy=COMMIT_POLICY_COMMIT,
            notes="Controlled observation expansion rows mapped to protected scenarios.",
        ),
        GoldenReplayArtifactFamily(
            family_id="bug_recurrence_history",
            retention_class=RETENTION_CANONICAL_VERSIONED_EVIDENCE,
            owner_module="tests.helpers.failure_dashboard_recurrence",
            paths=(
                _path_str(BUG_RECURRENCE_HISTORY_JSON_PATH),
                _path_str(BUG_RECURRENCE_HISTORY_MARKDOWN_PATH),
                _path_str(BUG_RECURRENCE_EVENT_LOG_JSON_PATH),
                _path_str(BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH),
                _path_str(RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH),
            ),
            regenerate_command=env_dashboard,
            commit_policy=COMMIT_POLICY_COMMIT,
            notes="High-churn operational snapshot; commit only on intentional recurrence refresh.",
        ),
        GoldenReplayArtifactFamily(
            family_id="bug_recurrence_legacy_baseline",
            retention_class=RETENTION_HISTORICAL_BASELINE,
            owner_module="tests.helpers.replay_bug_recurrence_history",
            paths=(_path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "bug_recurrence_event_log.legacy.json"),),
            regenerate_command="(frozen — do not regenerate)",
            commit_policy=COMMIT_POLICY_BASELINE_FREEZE,
            notes="Legacy recurrence event log retained for historical comparison.",
        ),
        GoldenReplayArtifactFamily(
            family_id="owner_drift_longitudinal",
            retention_class=RETENTION_REDUNDANT_PAIRED_OUTPUT,
            owner_module="tests.helpers.failure_dashboard_drift",
            paths=(
                _path_str(OWNER_DRIFT_LONGITUDINAL_JSON_PATH),
                _path_str(OWNER_DRIFT_LONGITUDINAL_MARKDOWN_PATH),
            ),
            regenerate_command=env_dashboard,
            commit_policy=COMMIT_POLICY_PAIRED_MIRROR,
            notes="JSON is machine source; Markdown is human mirror written atomically.",
        ),
        GoldenReplayArtifactFamily(
            family_id="owner_drift_hotspots",
            retention_class=RETENTION_REDUNDANT_PAIRED_OUTPUT,
            owner_module="tests.helpers.replay_drift_hotspots",
            paths=(
                _path_str(OWNER_DRIFT_HOTSPOTS_JSON_PATH),
                _path_str(OWNER_DRIFT_HOTSPOTS_MARKDOWN_PATH),
            ),
            regenerate_command=env_dashboard,
            commit_policy=COMMIT_POLICY_PAIRED_MIRROR,
            notes="High-churn paired output from drift hotspot aggregation.",
        ),
        GoldenReplayArtifactFamily(
            family_id="owner_drift_trends",
            retention_class=RETENTION_REDUNDANT_PAIRED_OUTPUT,
            owner_module="tests.helpers.replay_drift_trends",
            paths=(
                _path_str(OWNER_DRIFT_TRENDS_JSON_PATH),
                _path_str(OWNER_DRIFT_TRENDS_MARKDOWN_PATH),
            ),
            regenerate_command=env_dashboard,
            commit_policy=COMMIT_POLICY_PAIRED_MIRROR,
            notes="Trend window summaries paired with JSON source rows.",
        ),
        GoldenReplayArtifactFamily(
            family_id="owner_drift_risk",
            retention_class=RETENTION_REDUNDANT_PAIRED_OUTPUT,
            owner_module="tests.helpers.replay_drift_risk",
            paths=(
                _path_str(OWNER_DRIFT_RISK_JSON_PATH),
                _path_str(OWNER_DRIFT_RISK_MARKDOWN_PATH),
            ),
            regenerate_command=env_dashboard,
            commit_policy=COMMIT_POLICY_PAIRED_MIRROR,
            notes="Risk band rollups paired with JSON source rows.",
        ),
        GoldenReplayArtifactFamily(
            family_id="rerun_drift_scorecard",
            retention_class=RETENTION_REPRODUCIBLE_LOCAL_OUTPUT,
            owner_module="tests.helpers.failure_dashboard_drift",
            paths=(
                _path_str(RERUN_DRIFT_SCORECARD_JSON_PATH),
                _path_str(RERUN_DRIFT_SCORECARD_MARKDOWN_PATH),
            ),
            regenerate_command=env_rerun,
            commit_policy=COMMIT_POLICY_LOCAL_ONLY,
            notes="Opt-in rerun comparison scorecard; local/session output only.",
        ),
        GoldenReplayArtifactFamily(
            family_id="long_session_stability_scorecard",
            retention_class=RETENTION_REPRODUCIBLE_LOCAL_OUTPUT,
            owner_module="tests.helpers.failure_dashboard_stability",
            paths=(
                _path_str(LONG_SESSION_STABILITY_SCORECARD_JSON_PATH),
                _path_str(LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH),
            ),
            regenerate_command=env_stability,
            commit_policy=COMMIT_POLICY_LOCAL_ONLY,
            notes="Opt-in long-session stability scorecard; success-only writer branch.",
        ),
        GoldenReplayArtifactFamily(
            family_id="replay_maintenance_metrics",
            retention_class=RETENTION_REPRODUCIBLE_LOCAL_OUTPUT,
            owner_module="tools.replay_maintenance_metrics",
            paths=(
                _path_str(REPLAY_MAINTENANCE_METRICS_JSON_PATH),
                _path_str(REPLAY_MAINTENANCE_METRICS_MARKDOWN_PATH),
            ),
            regenerate_command="python tools/replay_maintenance_metrics.py",
            commit_policy=COMMIT_POLICY_LOCAL_ONLY,
            notes="CE1 concentration metrics; regenerable audit snapshot, not acceptance evidence.",
        ),
        GoldenReplayArtifactFamily(
            family_id="protected_replay_trend_window_bw",
            retention_class=RETENTION_HISTORICAL_BASELINE,
            owner_module="tests.helpers.protected_replay_trend_movement",
            paths=(
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "trend_window"),
            ),
            regenerate_command="python tools/run_protected_replay_trend.py (BW lane — frozen inputs)",
            commit_policy=COMMIT_POLICY_BASELINE_FREEZE,
            notes="BW immutable trend-window inputs including _storage run snapshots.",
        ),
        GoldenReplayArtifactFamily(
            family_id="protected_replay_trend_window_bz",
            retention_class=RETENTION_CANONICAL_VERSIONED_EVIDENCE,
            owner_module="tests.helpers.protected_replay_trend_movement",
            paths=(
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "trend_window_2"),
            ),
            regenerate_command="python tools/run_protected_replay_trend.py (BZ lane)",
            commit_policy=COMMIT_POLICY_COMMIT,
            notes="BZ movement outputs; commit when trend-window governance evidence changes.",
        ),
        GoldenReplayArtifactFamily(
            family_id="fallback_governance_reports",
            retention_class=RETENTION_CANONICAL_VERSIONED_EVIDENCE,
            owner_module="tests.helpers.runtime_lineage_reporting",
            paths=(
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_incidence_anomalies.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_incidence_anomalies.md"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_incidence_history.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_incidence_trends.md"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_maintenance_economics.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_maintenance_economics.md"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_maintenance_economics_summary.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_portfolio_benefit_report.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_portfolio_benefit_report.md"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_recurrence_report.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_recurrence_report.md"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_remediation_effectiveness.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_remediation_effectiveness.md"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_remediation_queue.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_remediation_queue.md"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_remediation_registry.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_risk_history.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_risk_report.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_risk_report.md"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_roi_report.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "fallback_roi_report.md"),
            ),
            regenerate_command="(report-family specific tools/tests — refresh intentionally)",
            commit_policy=COMMIT_POLICY_COMMIT,
            notes="Fallback portfolio governance snapshots; paired JSON/Markdown where present.",
        ),
        GoldenReplayArtifactFamily(
            family_id="fallback_incidence_baselines",
            retention_class=RETENTION_HISTORICAL_BASELINE,
            owner_module="tests.helpers.runtime_lineage_reporting",
            paths=(
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "bv1_fallback_incidence_report.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "bv1_fallback_incidence_report.md"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "bv1b_fallback_incidence_report.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "bv1b_fallback_incidence_report.md"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "bv1b_fallback_incidence_report.baseline.json"),
            ),
            regenerate_command="(frozen baseline lane — update only with explicit BV closeout)",
            commit_policy=COMMIT_POLICY_BASELINE_FREEZE,
            notes="BV incidence baselines including explicit .baseline.json companion.",
        ),
        GoldenReplayArtifactFamily(
            family_id="projection_governance_reports",
            retention_class=RETENTION_CANONICAL_VERSIONED_EVIDENCE,
            owner_module="tests.helpers.golden_replay_projection",
            paths=(
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "projection_coverage_report.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "projection_drift_watch_report.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "projection_drift_watch_report.md"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "projection_gap_reality_report.json"),
            ),
            regenerate_command="(projection governance refresh tools/tests)",
            commit_policy=COMMIT_POLICY_COMMIT,
            notes="Projection coverage/gap governance evidence; not pytest session scratch.",
        ),
    )


def golden_replay_artifact_family_by_id(family_id: str) -> GoldenReplayArtifactFamily | None:
    for family in golden_replay_artifact_families():
        if family.family_id == family_id:
            return family
    return None


def golden_replay_artifact_paths_by_commit_policy(policy: str) -> frozenset[str]:
    paths: set[str] = set()
    for family in golden_replay_artifact_families():
        if family.commit_policy == policy:
            paths.update(family.paths)
    return frozenset(paths)


def golden_replay_artifact_manifest_doc_paths() -> frozenset[str]:
    return frozenset(
        path
        for family in golden_replay_artifact_families()
        for path in family.paths
        if not path.endswith("/") and "*" not in path
    )


def failure_dashboard_canonical_paths_documented() -> bool:
    required = {
        _path_str(BUG_RECURRENCE_HISTORY_JSON_PATH),
        _path_str(BUG_RECURRENCE_HISTORY_MARKDOWN_PATH),
        _path_str(BUG_RECURRENCE_EVENT_LOG_JSON_PATH),
        _path_str(BUG_RECURRENCE_SESSION_DIAGNOSTIC_EVENT_LOG_JSON_PATH),
        _path_str(RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH),
        _path_str(PROTECTED_REPLAY_FAILURE_REPORT_PATH),
        _path_str(RERUN_DRIFT_SCORECARD_JSON_PATH),
        _path_str(RERUN_DRIFT_SCORECARD_MARKDOWN_PATH),
        _path_str(LONG_SESSION_STABILITY_SCORECARD_JSON_PATH),
        _path_str(LONG_SESSION_STABILITY_SCORECARD_MARKDOWN_PATH),
        _path_str(OWNER_DRIFT_LONGITUDINAL_JSON_PATH),
        _path_str(OWNER_DRIFT_LONGITUDINAL_MARKDOWN_PATH),
        _path_str(OWNER_DRIFT_HOTSPOTS_JSON_PATH),
        _path_str(OWNER_DRIFT_HOTSPOTS_MARKDOWN_PATH),
        _path_str(OWNER_DRIFT_TRENDS_JSON_PATH),
        _path_str(OWNER_DRIFT_TRENDS_MARKDOWN_PATH),
        _path_str(OWNER_DRIFT_RISK_JSON_PATH),
        _path_str(OWNER_DRIFT_RISK_MARKDOWN_PATH),
    }
    documented = golden_replay_artifact_manifest_doc_paths()
    return required <= documented
