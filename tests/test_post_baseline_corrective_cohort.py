"""CA6 post-baseline corrective cohort validation."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from tests.helpers.post_baseline_corrective_cohort import (
    POST_BASELINE_COHORT_FIELDS,
    POST_BASELINE_EXCLUSION_FIELDS,
    build_cohort_summary,
    load_post_baseline_cohort,
    load_post_baseline_exclusions,
    load_review_queue,
    validate_post_baseline_cohort,
    validate_post_baseline_partition,
    validate_required_columns,
    validate_unique_commit_hashes,
    write_ca6_reviewed_cohort_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
COHORT_CSV = REPO_ROOT / "docs" / "audits" / "CA_post_baseline_cohort.csv"
EXCLUSIONS_CSV = REPO_ROOT / "docs" / "audits" / "CA_post_baseline_exclusions.csv"
REVIEW_QUEUE_CSV = REPO_ROOT / "docs" / "audits" / "ca_review_queue.csv"
INVENTORY_JSON = REPO_ROOT / "artifacts" / "ca5_candidate_inventory.json"


def test_cohort_integrity():
    cohort = load_post_baseline_cohort(COHORT_CSV)
    exclusions = load_post_baseline_exclusions(EXCLUSIONS_CSV)
    queue = load_review_queue(REVIEW_QUEUE_CSV)

    assert validate_post_baseline_cohort(
        cohort_csv_path=COHORT_CSV,
        exclusions_csv_path=EXCLUSIONS_CSV,
        review_queue_path=REVIEW_QUEUE_CSV,
    ) == []
    assert validate_post_baseline_partition(cohort, exclusions, queue) == []
    assert all(row.reviewed for row in queue)
    assert all(row.qualifies is False for row in queue)


def test_exclusion_integrity():
    exclusions = load_post_baseline_exclusions(EXCLUSIONS_CSV)
    inventory = json.loads(INVENTORY_JSON.read_text(encoding="utf-8"))
    inventory_hashes = {row["commit_hash"] for row in inventory["candidates"]}

    assert len(exclusions) == inventory["candidate_count"] == 26
    assert {row.commit_hash for row in exclusions} == inventory_hashes
    assert all(row.exclusion_reason for row in exclusions)


def test_uniqueness():
    cohort = load_post_baseline_cohort(COHORT_CSV)
    exclusions = load_post_baseline_exclusions(EXCLUSIONS_CSV)
    queue = load_review_queue(REVIEW_QUEUE_CSV)

    assert validate_unique_commit_hashes([row.commit_hash for row in exclusions]) == []
    assert validate_unique_commit_hashes([row.commit_hash for row in queue]) == []
    assert validate_unique_commit_hashes([row.commit_hash for row in cohort]) == []


def test_schema_compliance():
    with COHORT_CSV.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        assert validate_required_columns(reader.fieldnames, POST_BASELINE_COHORT_FIELDS) == []

    with EXCLUSIONS_CSV.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        assert validate_required_columns(reader.fieldnames, POST_BASELINE_EXCLUSION_FIELDS) == []


def test_cohort_summary_counts():
    cohort = load_post_baseline_cohort(COHORT_CSV)
    exclusions = load_post_baseline_exclusions(EXCLUSIONS_CSV)
    queue = load_review_queue(REVIEW_QUEUE_CSV)
    summary = build_cohort_summary(cohort, exclusions, queue)

    assert summary["candidates_reviewed"] == 26
    assert summary["qualifying_fixes"] == 0
    assert summary["exclusions"] == 26
    assert summary["confidence_distribution"] == {}
    assert summary["repair_family_distribution"] == {}


def test_no_pending_review_rows():
    queue = load_review_queue(REVIEW_QUEUE_CSV)
    pending = [row for row in queue if not row.reviewed]
    assert pending == []


def test_ca6_report_generation(tmp_path):
    output = tmp_path / "ca6_reviewed_cohort_report.md"
    payload, markdown = write_ca6_reviewed_cohort_report(
        output,
        cohort_csv_path=COHORT_CSV,
        exclusions_csv_path=EXCLUSIONS_CSV,
        review_queue_path=REVIEW_QUEUE_CSV,
        repo_root=REPO_ROOT,
    )
    assert output.exists()
    assert payload["stats"]["candidates_reviewed"] == 26
    assert payload["readiness"]["review_complete"] is True
    assert payload["readiness"]["ready_for_measurement"] is False
    assert "## 1. Review Summary" in markdown
    assert "## 6. Cohort Readiness Assessment" in markdown


def test_validation_fails_when_review_incomplete(tmp_path):
    bad_queue = tmp_path / "bad_queue.csv"
    bad_queue.write_text(
        "commit_hash,reviewed,qualifies,confidence,defect_statement,repair_family,notes\n"
        "abc123,false,,,,,pending\n",
        encoding="utf-8",
    )
    errors = validate_post_baseline_cohort(
        cohort_csv_path=COHORT_CSV,
        exclusions_csv_path=EXCLUSIONS_CSV,
        review_queue_path=bad_queue,
    )
    assert any("reviewed=false" in err for err in errors)


def test_validation_fails_when_qualifying_row_missing_defect_statement(tmp_path):
    bad_cohort = tmp_path / "bad_cohort.csv"
    bad_cohort.write_text(
        "cohort_id,commit_hash,date,title,confidence,defect_statement,repair_family,review_notes\n"
        "CA-PB-01,abc123,2026-06-22,title,high,,routing,notes\n",
        encoding="utf-8",
    )
    errors = validate_post_baseline_cohort(
        cohort_csv_path=bad_cohort,
        exclusions_csv_path=EXCLUSIONS_CSV,
        review_queue_path=REVIEW_QUEUE_CSV,
    )
    assert any("missing defect_statement" in err for err in errors)
