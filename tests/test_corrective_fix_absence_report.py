"""CA7 corrective fix absence report validation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.corrective_fix_absence_report import (
    EXCLUSION_CATEGORIES,
    build_corrective_fix_absence_report,
    build_exclusion_distribution,
    classify_exclusions,
    compute_candidate_yield,
    evaluate_qualification_sensitivity,
    load_baseline_summary,
    load_inventory_candidates,
    write_corrective_fix_absence_report,
)
from tests.helpers.post_baseline_corrective_cohort import (
    load_post_baseline_cohort,
    load_post_baseline_exclusions,
    load_review_queue,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
EXCLUSIONS_CSV = REPO_ROOT / "docs" / "audits" / "CA_post_baseline_exclusions.csv"
REVIEW_QUEUE_CSV = REPO_ROOT / "docs" / "audits" / "ca_review_queue.csv"
COHORT_CSV = REPO_ROOT / "docs" / "audits" / "CA_post_baseline_cohort.csv"
BASELINE_JSON = REPO_ROOT / "docs" / "baselines" / "ca_corrective_locality_baseline.json"
INVENTORY_JSON = REPO_ROOT / "artifacts" / "ca5_candidate_inventory.json"
CA6_REPORT = REPO_ROOT / "artifacts" / "ca6_reviewed_cohort_report.md"

CA7_EXPECTED_COUNTS = {
    "governance_work": 3,
    "observability_work": 1,
    "instrumentation_work": 5,
    "replay_work": 7,
    "ownership_work": 7,
    "decomposition_work": 3,
    "refactor_work": 0,
    "other": 0,
}


def test_exclusion_accounting_matches_review_queue():
    exclusions = load_post_baseline_exclusions(EXCLUSIONS_CSV)
    queue = load_review_queue(REVIEW_QUEUE_CSV)

    excluded_hashes = {row.commit_hash for row in exclusions}
    reviewed_false_hashes = {row.commit_hash for row in queue if row.qualifies is False}

    assert len(exclusions) == 26
    assert excluded_hashes == reviewed_false_hashes
    assert all(row.exclusion_reason for row in exclusions)


def test_exclusion_distribution_totals():
    exclusions = load_post_baseline_exclusions(EXCLUSIONS_CSV)
    classified = classify_exclusions(exclusions)
    distribution = build_exclusion_distribution(classified)

    assert distribution["total_exclusions"] == 26
    assert sum(distribution["counts"].values()) == 26
    assert distribution["counts"] == CA7_EXPECTED_COUNTS
    assert sum(distribution["percentages"].values()) == pytest.approx(100.0, abs=0.1)
    for category in EXCLUSION_CATEGORIES:
        assert len(distribution["by_category"][category]) == distribution["counts"][category]


def test_yield_calculations():
    queue = load_review_queue(REVIEW_QUEUE_CSV)
    cohort = load_post_baseline_cohort(COHORT_CSV)
    metrics = compute_candidate_yield(queue, len(cohort))

    assert metrics["reviewed_candidates"] == 26
    assert metrics["qualifying_fixes"] == 0
    assert metrics["candidate_to_fix_yield"] == 0.0
    assert metrics["primary_metric"] == "candidate_to_fix_yield"


def test_sensitivity_calculations():
    exclusions = load_post_baseline_exclusions(EXCLUSIONS_CSV)
    inventory = load_inventory_candidates(INVENTORY_JSON, repo_root=REPO_ROOT)
    analysis = evaluate_qualification_sensitivity(exclusions, inventory)

    strict = analysis["strict_interpretation"]
    relaxed = analysis["relaxed_interpretation"]

    assert strict["promoted_count"] == 0
    assert strict["promoted_commit_hashes"] == []
    assert relaxed["promoted_count"] == 9
    assert len(relaxed["promoted_commit_hashes"]) == 9
    assert all(
        inventory[commit_hash].production_files_touched > 0
        for commit_hash in relaxed["promoted_commit_hashes"]
    )
    assert len(analysis["candidates"]) == 26


def test_report_generation(tmp_path):
    output_md = tmp_path / "ca7_corrective_fix_absence_report.md"
    output_json = tmp_path / "ca7_corrective_fix_absence_report.json"

    report, markdown = write_corrective_fix_absence_report(
        md_output_path=output_md,
        json_output_path=output_json,
        exclusions_csv_path=EXCLUSIONS_CSV,
        review_queue_path=REVIEW_QUEUE_CSV,
        cohort_csv_path=COHORT_CSV,
        baseline_json_path=BASELINE_JSON,
        inventory_json_path=INVENTORY_JSON,
        ca6_report_path=CA6_REPORT,
        repo_root=REPO_ROOT,
    )

    assert output_md.exists()
    assert output_json.exists()
    assert report["yield_analysis"]["candidate_to_fix_yield"] == 0.0
    assert report["exclusion_distribution"]["counts"] == CA7_EXPECTED_COUNTS
    assert report["qualification_sensitivity"]["strict_interpretation"]["promoted_count"] == 0
    assert report["qualification_sensitivity"]["relaxed_interpretation"]["promoted_count"] == 9
    assert report["zero_fix_evidence"]["zero_fix_statement_defensible"] is True
    assert "## 1. Executive Summary" in markdown
    assert "## 6. Risks To Interpretation" in markdown

    persisted = json.loads(output_json.read_text(encoding="utf-8"))
    assert persisted["yield_analysis"] == report["yield_analysis"]


def test_build_report_from_inputs():
    exclusions = load_post_baseline_exclusions(EXCLUSIONS_CSV)
    queue = load_review_queue(REVIEW_QUEUE_CSV)
    cohort = load_post_baseline_cohort(COHORT_CSV)
    inventory = load_inventory_candidates(INVENTORY_JSON, repo_root=REPO_ROOT)
    baseline = load_baseline_summary(BASELINE_JSON, repo_root=REPO_ROOT)

    report = build_corrective_fix_absence_report(
        exclusions=exclusions,
        review_queue=queue,
        qualifying_fix_count=len(cohort),
        inventory=inventory,
        baseline=baseline,
        ca6_report_path="artifacts/ca6_reviewed_cohort_report.md",
    )

    assert report["schema_version"] == 1
    assert report["sources"]["baseline_json"] == "docs/baselines/ca_corrective_locality_baseline.json"
    assert report["zero_fix_evidence"]["ca4_baseline_end_date"] == "2026-05-20"
