"""Golden replay artifact retention manifest (CE6, CF6).

Read-side registry classifying ``artifacts/golden_replay/`` outputs by retention
policy and projection artifact importance. Does not write artifacts or change replay
behavior.
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
    FAILURE_DASHBOARD_LATEST_PATH,
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

IMPORTANCE_ACCEPTANCE_CRITICAL = "acceptance-critical"
IMPORTANCE_GOVERNANCE = "governance"
IMPORTANCE_DIAGNOSTIC = "diagnostic"
IMPORTANCE_ADVISORY = "advisory"
IMPORTANCE_DEVELOPER_CONVENIENCE = "developer_convenience"
IMPORTANCE_EPHEMERAL = "ephemeral"

PROJECTION_ARTIFACT_IMPORTANCE_VALUES: frozenset[str] = frozenset(
    {
        IMPORTANCE_ACCEPTANCE_CRITICAL,
        IMPORTANCE_GOVERNANCE,
        IMPORTANCE_DIAGNOSTIC,
        IMPORTANCE_ADVISORY,
        IMPORTANCE_DEVELOPER_CONVENIENCE,
        IMPORTANCE_EPHEMERAL,
    }
)

PROTECTED_REPLAY_MANIFEST_DOC_PATH = Path("docs/testing/protected_replay_manifest.md")

# BV3F/BV3B ``refresh_projection_artifacts()`` bundle — gap + drift only (not coverage).
PROJECTION_CORPUS_REFRESH_ARTIFACT_PATHS: frozenset[str] = frozenset(
    {
        "artifacts/golden_replay/projection_gap_reality_report.json",
        "artifacts/golden_replay/projection_drift_watch_report.json",
        "artifacts/golden_replay/projection_drift_watch_report.md",
    }
)

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
    importance: str
    generator: str
    consumer: str
    ci_required: bool
    regenerate_triggers: str
    review_owner: str
    test_owner: str
    governance_owner: str
    notes: str = ""


@dataclass(frozen=True)
class ProjectionGeneratedArtifact:
    """One generated projection artifact row (family or standalone)."""

    artifact_id: str
    paths: tuple[str, ...]
    importance: str
    generator: str
    consumer: str
    ci_required: bool
    owner_module: str
    review_owner: str
    test_owner: str
    governance_owner: str
    regenerate_triggers: str
    commit_policy: str
    notes: str = ""


def _path_str(path: Path | str) -> str:
    return Path(path).as_posix()


def golden_replay_artifact_families() -> tuple[GoldenReplayArtifactFamily, ...]:
    """Return the canonical artifact-family retention registry."""
    env_dashboard = f"{FAILURE_DASHBOARD_ENV_VAR}=1 pytest"
    env_rerun = f"{RERUN_DRIFT_SCORECARD_ENV_VAR}=1 pytest"
    env_stability = f"{LONG_SESSION_STABILITY_SCORECARD_ENV_VAR}=1 pytest"
    governance = "tests.helpers.golden_replay_artifact_manifest"
    return (
        GoldenReplayArtifactFamily(
            family_id="protected_replay_failure_report",
            retention_class=RETENTION_CANONICAL_VERSIONED_EVIDENCE,
            owner_module="tests.helpers.failure_dashboard_report",
            paths=(_path_str(PROTECTED_REPLAY_FAILURE_REPORT_PATH),),
            regenerate_command=env_dashboard,
            commit_policy=COMMIT_POLICY_COMMIT,
            importance=IMPORTANCE_DIAGNOSTIC,
            generator="tests.helpers.failure_dashboard_report::write_protected_replay_failure_report_if_present",
            consumer="protected replay closeout reviewers; CI failure upload",
            ci_required=False,
            regenerate_triggers="protected replay pytest failures with ASHEN_WRITE_FAILURE_DASHBOARD=1",
            review_owner="tests.helpers.failure_dashboard_report",
            test_owner="tests/test_failure_dashboard_controlled_failures.py",
            governance_owner=governance,
            notes="Curated protected-replay failure narrative; acceptance audit evidence when failures occur.",
        ),
        GoldenReplayArtifactFamily(
            family_id="protected_replay_observation_corpus",
            retention_class=RETENTION_CANONICAL_VERSIONED_EVIDENCE,
            owner_module="tests.helpers.protected_replay_observation_corpus",
            paths=(_path_str(PROTECTED_REPLAY_OBSERVATION_CORPUS_PATH),),
            regenerate_command="python tools/expand_protected_replay_observations.py",
            commit_policy=COMMIT_POLICY_COMMIT,
            importance=IMPORTANCE_GOVERNANCE,
            generator="tools/expand_protected_replay_observations.py",
            consumer="protected scenario observation expansion governance",
            ci_required=False,
            regenerate_triggers="explicit observation corpus expansion closeout",
            review_owner="tests.helpers.protected_replay_observation_corpus",
            test_owner="tests/test_protected_replay_observation_corpus.py",
            governance_owner=governance,
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
            importance=IMPORTANCE_DIAGNOSTIC,
            generator="tests.helpers.failure_dashboard_recurrence (via failure dashboard cascade)",
            consumer="recurrence triage; BZ trend movement baselines",
            ci_required=False,
            regenerate_triggers="ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest; optional trend tool --append-history",
            review_owner="tests.helpers.failure_dashboard_recurrence",
            test_owner="tests/test_replay_bug_class_recurrence.py",
            governance_owner=governance,
            notes="High-churn operational snapshot; commit only on intentional recurrence refresh.",
        ),
        GoldenReplayArtifactFamily(
            family_id="bug_recurrence_legacy_baseline",
            retention_class=RETENTION_HISTORICAL_BASELINE,
            owner_module="tests.helpers.replay_bug_recurrence_history",
            paths=(_path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "bug_recurrence_event_log.legacy.json"),),
            regenerate_command="(frozen — do not regenerate)",
            commit_policy=COMMIT_POLICY_BASELINE_FREEZE,
            importance=IMPORTANCE_GOVERNANCE,
            generator="(frozen historical import)",
            consumer="historical recurrence comparison",
            ci_required=False,
            regenerate_triggers="explicit BV/BQ baseline closeout only",
            review_owner="tests.helpers.replay_bug_recurrence_history",
            test_owner="tests/test_replay_bug_class_recurrence.py",
            governance_owner=governance,
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
            importance=IMPORTANCE_DIAGNOSTIC,
            generator="tests.helpers.failure_dashboard_drift (via failure dashboard cascade)",
            consumer="owner drift longitudinal review",
            ci_required=False,
            regenerate_triggers="ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest after protected failures",
            review_owner="tests.helpers.failure_dashboard_drift",
            test_owner="tests/test_failure_dashboard_drift.py",
            governance_owner=governance,
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
            importance=IMPORTANCE_DIAGNOSTIC,
            generator="tests.helpers.replay_drift_hotspots (via failure dashboard cascade)",
            consumer="owner drift hotspot triage",
            ci_required=False,
            regenerate_triggers="ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest after protected failures",
            review_owner="tests.helpers.replay_drift_hotspots",
            test_owner="tests/test_replay_drift_hotspots.py",
            governance_owner=governance,
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
            importance=IMPORTANCE_DIAGNOSTIC,
            generator="tests.helpers.replay_drift_trends (via failure dashboard cascade)",
            consumer="owner drift trend summaries",
            ci_required=False,
            regenerate_triggers="ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest after protected failures",
            review_owner="tests.helpers.replay_drift_trends",
            test_owner="tests/test_replay_drift_trends.py",
            governance_owner=governance,
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
            importance=IMPORTANCE_DIAGNOSTIC,
            generator="tests.helpers.replay_drift_risk (via failure dashboard cascade)",
            consumer="owner drift risk band rollups",
            ci_required=False,
            regenerate_triggers="ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest after protected failures",
            review_owner="tests.helpers.replay_drift_risk",
            test_owner="tests/test_replay_drift_risk.py",
            governance_owner=governance,
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
            importance=IMPORTANCE_DEVELOPER_CONVENIENCE,
            generator="tests.helpers.failure_dashboard_drift::write_rerun_drift_scorecard_artifacts",
            consumer="local rerun comparison during development",
            ci_required=False,
            regenerate_triggers="ASHEN_WRITE_RERUN_DRIFT_SCORECARD=1 pytest on success",
            review_owner="tests.helpers.failure_dashboard_drift",
            test_owner="tests/test_failure_dashboard_drift.py",
            governance_owner=governance,
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
            importance=IMPORTANCE_DEVELOPER_CONVENIENCE,
            generator="tests.helpers.failure_dashboard_stability::write_long_session_stability_scorecard_artifacts",
            consumer="local long-session stability review",
            ci_required=False,
            regenerate_triggers="ASHEN_WRITE_LONG_SESSION_STABILITY_SCORECARD=1 pytest on success",
            review_owner="tests.helpers.failure_dashboard_stability",
            test_owner="tests/test_failure_dashboard_stability.py",
            governance_owner=governance,
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
            importance=IMPORTANCE_DEVELOPER_CONVENIENCE,
            generator="tools/replay_maintenance_metrics.py",
            consumer="CE1 concentration metrics review",
            ci_required=False,
            regenerate_triggers="manual CE1 metrics refresh",
            review_owner="tools.replay_maintenance_metrics",
            test_owner="tests/test_replay_maintenance_metrics.py",
            governance_owner=governance,
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
            importance=IMPORTANCE_GOVERNANCE,
            generator="tools/run_protected_replay_trend.py",
            consumer="BW trend-window closeout tests; immutable comparison lane",
            ci_required=True,
            regenerate_triggers="explicit BW closeout only — not semantic projection edits",
            review_owner="tests.helpers.protected_replay_trend_movement",
            test_owner="tests/test_bw_protected_replay_trend_window_closeout.py",
            governance_owner=governance,
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
            importance=IMPORTANCE_GOVERNANCE,
            generator="tools/run_protected_replay_trend.py",
            consumer="BZ movement governance; recurrence/replay-key movement tests",
            ci_required=True,
            regenerate_triggers="explicit BZ trend-window refresh; not ordinary projection field edits",
            review_owner="tests.helpers.protected_replay_trend_movement",
            test_owner="tests/test_bz_protected_replay_trend_window_2.py",
            governance_owner=governance,
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
            importance=IMPORTANCE_ADVISORY,
            generator="tools/fallback_*.py family; tests/helpers/runtime_lineage_reporting",
            consumer="fallback portfolio governance closeouts",
            ci_required=False,
            regenerate_triggers="manual fallback governance tool runs; not CI or projection manifest edits",
            review_owner="tests.helpers.runtime_lineage_reporting",
            test_owner="tests/test_fallback_* governance suites",
            governance_owner=governance,
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
            importance=IMPORTANCE_GOVERNANCE,
            generator="tools/bv1b_fallback_incidence_validation.py (historical)",
            consumer="BV incidence baseline comparison",
            ci_required=False,
            regenerate_triggers="explicit BV closeout only",
            review_owner="tests.helpers.runtime_lineage_reporting",
            test_owner="tests/test_bv1_fallback_incidence_validation.py",
            governance_owner=governance,
            notes="BV incidence baselines including explicit .baseline.json companion.",
        ),
        GoldenReplayArtifactFamily(
            family_id="projection_coverage_report",
            retention_class=RETENTION_CANONICAL_VERSIONED_EVIDENCE,
            owner_module="tests.helpers.golden_replay_projection",
            paths=(_path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "projection_coverage_report.json"),),
            regenerate_command="python tools/fallback_projection_coverage_audit.py",
            commit_policy=COMMIT_POLICY_COMMIT,
            importance=IMPORTANCE_ADVISORY,
            generator="tools/fallback_projection_coverage_audit.py",
            consumer="BP2 projection coverage closeout readers",
            ci_required=False,
            regenerate_triggers="protected observation registry or projector shape catalog changes",
            review_owner="tests.helpers.golden_replay_projection",
            test_owner="tests/test_fallback_projection_coverage_audit.py",
            governance_owner=governance,
            notes="Shape-level projector coverage; not bundled in BV3F corpus refresh.",
        ),
        GoldenReplayArtifactFamily(
            family_id="projection_gap_reality_report",
            retention_class=RETENTION_CANONICAL_VERSIONED_EVIDENCE,
            owner_module="tests.helpers.golden_replay_projection",
            paths=(_path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "projection_gap_reality_report.json"),),
            regenerate_command="python tools/fallback_projection_gap_reality_audit.py",
            commit_policy=COMMIT_POLICY_COMMIT,
            importance=IMPORTANCE_ADVISORY,
            generator="tools/fallback_projection_gap_reality_audit.py",
            consumer="BP3 gap-reality audit readers; BV3F corpus refresh",
            ci_required=False,
            regenerate_triggers="artifacts/data corpus changes; BV3F refresh_projection_artifacts()",
            review_owner="tests.helpers.golden_replay_projection",
            test_owner="tests/test_fallback_projection_gap_reality_audit.py",
            governance_owner=governance,
            notes="Full-repo FEM scan; advisory only — not acceptance gate.",
        ),
        GoldenReplayArtifactFamily(
            family_id="projection_drift_watch_report",
            retention_class=RETENTION_CANONICAL_VERSIONED_EVIDENCE,
            owner_module="tests.helpers.golden_replay_projection",
            paths=(
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "projection_drift_watch_report.json"),
                _path_str(GOLDEN_REPLAY_ARTIFACT_ROOT / "projection_drift_watch_report.md"),
            ),
            regenerate_command="python tools/projection_drift_watch.py",
            commit_policy=COMMIT_POLICY_COMMIT,
            importance=IMPORTANCE_ADVISORY,
            generator="tools/projection_drift_watch.py",
            consumer="BP3 drift-watch closeout readers; BV3F corpus refresh",
            ci_required=False,
            regenerate_triggers="artifacts/data corpus changes; BV3F refresh_projection_artifacts()",
            review_owner="tests.helpers.golden_replay_projection",
            test_owner="tests/test_projection_drift_watch.py",
            governance_owner=governance,
            notes="Known BP3 watch-shape scan; paired JSON/Markdown advisory output.",
        ),
        GoldenReplayArtifactFamily(
            family_id="failure_dashboard_latest",
            retention_class=RETENTION_TEMPORARY_SESSION_OUTPUT,
            owner_module="tests.helpers.failure_dashboard_report",
            paths=(_path_str(FAILURE_DASHBOARD_LATEST_PATH),),
            regenerate_command=env_dashboard,
            commit_policy=COMMIT_POLICY_COMMIT,
            importance=IMPORTANCE_DIAGNOSTIC,
            generator="tests.helpers.failure_dashboard_report::write_failure_dashboard_artifact",
            consumer="local failure dashboard triage",
            ci_required=False,
            regenerate_triggers="ASHEN_WRITE_FAILURE_DASHBOARD=1 pytest",
            review_owner="tests.helpers.failure_dashboard_report",
            test_owner="tests/test_failure_dashboard_controlled_failures.py",
            governance_owner=governance,
            notes="Opt-in dashboard outside golden_replay/; tracked but high-churn.",
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


def _family_to_projection_artifact(family: GoldenReplayArtifactFamily) -> ProjectionGeneratedArtifact:
    return ProjectionGeneratedArtifact(
        artifact_id=family.family_id,
        paths=family.paths,
        importance=family.importance,
        generator=family.generator,
        consumer=family.consumer,
        ci_required=family.ci_required,
        owner_module=family.owner_module,
        review_owner=family.review_owner,
        test_owner=family.test_owner,
        governance_owner=family.governance_owner,
        regenerate_triggers=family.regenerate_triggers,
        commit_policy=family.commit_policy,
        notes=family.notes,
    )


def protected_replay_manifest_generated_artifact() -> ProjectionGeneratedArtifact:
    """Acceptance-critical generated section in the protected replay manifest."""
    governance = "tests.helpers.golden_replay_artifact_manifest"
    return ProjectionGeneratedArtifact(
        artifact_id="protected_replay_manifest_field_paths",
        paths=(_path_str(PROTECTED_REPLAY_MANIFEST_DOC_PATH),),
        importance=IMPORTANCE_ACCEPTANCE_CRITICAL,
        generator="tools/refresh_protected_replay_manifest.py",
        consumer="CI convergence-checks; protected replay manifest reviewers",
        ci_required=True,
        owner_module="tests.helpers.golden_replay_projection_manifest",
        review_owner="tests.helpers.golden_replay_projection_manifest",
        test_owner="tests/test_golden_replay_projection_manifest.py",
        governance_owner=governance,
        regenerate_triggers="protected observation registry or drift-bucket changes",
        commit_policy=COMMIT_POLICY_COMMIT,
        notes="Generated field-path table only; scenario prose is hand-maintained.",
    )


def projection_generated_artifact_inventory() -> tuple[ProjectionGeneratedArtifact, ...]:
    """Full CF6 inventory: golden-replay families plus standalone projection artifacts."""
    artifacts = [_family_to_projection_artifact(family) for family in golden_replay_artifact_families()]
    artifacts.append(protected_replay_manifest_generated_artifact())
    return tuple(artifacts)


def projection_acceptance_critical_artifacts() -> tuple[ProjectionGeneratedArtifact, ...]:
    return tuple(
        artifact
        for artifact in projection_generated_artifact_inventory()
        if artifact.importance == IMPORTANCE_ACCEPTANCE_CRITICAL
    )


def projection_artifact_by_id(artifact_id: str) -> ProjectionGeneratedArtifact | None:
    for artifact in projection_generated_artifact_inventory():
        if artifact.artifact_id == artifact_id:
            return artifact
    return None


def projection_corpus_refresh_artifact_paths_documented() -> bool:
    documented = golden_replay_artifact_manifest_doc_paths()
    return PROJECTION_CORPUS_REFRESH_ARTIFACT_PATHS <= documented


def failure_dashboard_cascade_family_ids() -> frozenset[str]:
    """Families regenerated together by the failure-dashboard writer cascade."""
    return frozenset(
        {
            "protected_replay_failure_report",
            "bug_recurrence_history",
            "owner_drift_longitudinal",
            "owner_drift_hotspots",
            "owner_drift_trends",
            "owner_drift_risk",
        }
    )
