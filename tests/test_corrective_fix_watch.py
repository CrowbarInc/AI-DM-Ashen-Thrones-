"""CA11 corrective fix watch validation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.corrective_fix_watch import (
    assess_cohort_readiness,
    build_corrective_fix_watch_report,
    compute_corrective_fix_emergence_rate,
    detect_new_qualifying_fixes,
    load_ca1_cohort_commit_hashes,
    load_ca10_report,
    write_corrective_fix_watch_report,
)
from tests.helpers.corrective_fix_absence_report import load_baseline_summary
from tests.helpers.post_baseline_corrective_cohort import ReviewQueueRow, load_review_queue

REPO_ROOT = Path(__file__).resolve().parents[1]
REVIEW_QUEUE_CSV = REPO_ROOT / "docs" / "audits" / "ca_review_queue.csv"
CA1_COHORT_CSV = REPO_ROOT / "docs" / "audits" / "CA_corrective_change_locality_cohort.csv"
BASELINE_JSON = REPO_ROOT / "docs" / "baselines" / "ca_corrective_locality_baseline.json"
CA10_JSON = REPO_ROOT / "artifacts" / "ca10_corrective_prevention_effectiveness_report.json"


def _row(
    commit_hash: str,
    *,
    reviewed: bool = True,
    qualifies: bool | None = False,
    confidence: str = "",
    defect_statement: str = "",
    repair_family: str = "",
    notes: str = "",
) -> ReviewQueueRow:
    return ReviewQueueRow(
        commit_hash=commit_hash,
        reviewed=reviewed,
        qualifies=qualifies,
        confidence=confidence,
        defect_statement=defect_statement,
        repair_family=repair_family,
        notes=notes,
    )


def test_duplicate_suppression_against_ca1_cohort():
    ca1_hashes = load_ca1_cohort_commit_hashes(CA1_COHORT_CSV, repo_root=REPO_ROOT)
    ca1_hash = next(iter(ca1_hashes))

    queue = [
        _row(
            ca1_hash,
            qualifies=True,
            confidence="high",
            defect_statement="already in cohort",
            repair_family="routing",
        ),
        _row(
            "newhash12345678901234567890123456789012345678",
            qualifies=True,
            confidence="medium",
            defect_statement="new defect",
            repair_family="opening_fallback",
        ),
    ]
    detected = detect_new_qualifying_fixes(queue, ca1_hashes)

    assert len(detected) == 1
    assert detected[0].commit_hash == "newhash12345678901234567890123456789012345678"


def test_readiness_state_transitions():
    assert assess_cohort_readiness(0)["state"] == "no_new_fixes"
    assert assess_cohort_readiness(0)["ready_for_ca12"] is False

    for count in (1, 2, 4):
        readiness = assess_cohort_readiness(count)
        assert readiness["state"] == "insufficient_sample"
        assert readiness["ready_for_ca12"] is False

    readiness = assess_cohort_readiness(5)
    assert readiness["state"] == "comparison_ready"
    assert readiness["ready_for_ca12"] is True

    readiness = assess_cohort_readiness(10)
    assert readiness["state"] == "comparison_ready"


def test_emergence_rate_calculations():
    metrics = compute_corrective_fix_emergence_rate(0, 26)
    assert metrics["corrective_fix_emergence_rate"] == 0.0
    assert metrics["new_qualifying_fixes"] == 0
    assert metrics["reviewed_candidates"] == 26

    metrics = compute_corrective_fix_emergence_rate(2, 10)
    assert metrics["corrective_fix_emergence_rate"] == 0.2

    metrics = compute_corrective_fix_emergence_rate(0, 0)
    assert metrics["corrective_fix_emergence_rate"] == 0.0


def test_report_generation_current_repository(tmp_path):
    output_md = tmp_path / "ca11_corrective_fix_watch_report.md"
    output_json = tmp_path / "ca11_corrective_fix_watch_report.json"

    report, markdown = write_corrective_fix_watch_report(
        md_output_path=output_md,
        json_output_path=output_json,
        review_queue_path=REVIEW_QUEUE_CSV,
        ca1_cohort_csv_path=CA1_COHORT_CSV,
        baseline_json_path=BASELINE_JSON,
        ca10_json_path=CA10_JSON,
        repo_root=REPO_ROOT,
    )

    assert output_md.exists()
    assert output_json.exists()
    assert report["watch_summary"]["qualifying_fixes_detected"] == 0
    assert report["watch_summary"]["total_reviewed_candidates"] == 26
    assert report["cohort_readiness"]["state"] == "no_new_fixes"
    assert report["emergence_analysis"]["corrective_fix_emergence_rate"] == 0.0
    assert "## Watch Summary" in markdown

    persisted = json.loads(output_json.read_text(encoding="utf-8"))
    assert persisted["cohort_readiness"] == report["cohort_readiness"]


def test_build_report_with_synthetic_qualifying_fixes():
    ca1_hashes = load_ca1_cohort_commit_hashes(CA1_COHORT_CSV, repo_root=REPO_ROOT)
    baseline = load_baseline_summary(BASELINE_JSON, repo_root=REPO_ROOT)
    ca10 = load_ca10_report(CA10_JSON, repo_root=REPO_ROOT)

    queue = load_review_queue(REVIEW_QUEUE_CSV)
    synthetic = [
        _row(
            f"synthetic{i:040d}",
            qualifies=True,
            confidence="high",
            defect_statement=f"defect {i}",
            repair_family="opening_fallback",
        )
        for i in range(5)
    ]
    report = build_corrective_fix_watch_report(
        review_queue=[*queue, *synthetic],
        ca1_commit_hashes=ca1_hashes,
        baseline=baseline,
        ca10_report=ca10,
    )

    assert report["watch_summary"]["qualifying_fixes_detected"] == 5
    assert report["cohort_readiness"]["state"] == "comparison_ready"
    assert report["emergence_analysis"]["corrective_fix_emergence_rate"] == pytest.approx(
        5 / 31, rel=1e-4
    )
