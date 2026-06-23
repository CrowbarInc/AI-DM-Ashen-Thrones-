"""CA2 corrective-change locality Git collector validation."""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.corrective_change_locality_cohort import load_cohort
from tests.helpers.corrective_change_locality_classifier import PATH_BUCKETS, validate_classification
from tools.corrective_change_locality import (
    collect_changed_paths,
    collect_cohort_locality,
    compute_locality_counts,
    inspect_commit_hash,
    load_reviewed_cohort,
    measure_commit_locality,
    validate_cohort_locality_collection,
    validate_measurement_against_authority,
    write_ca2_path_classification_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
COHORT_CSV = REPO_ROOT / "docs" / "audits" / "CA_corrective_change_locality_cohort.csv"


def test_cohort_rows_load_correctly():
    rows = load_reviewed_cohort(COHORT_CSV)
    assert len(rows) == 11
    assert sum(1 for row in rows if row.qualifies) == 10


def test_collector_handles_valid_commits():
    rows = load_reviewed_cohort(COHORT_CSV)
    collection = collect_cohort_locality(rows, repo_root=REPO_ROOT)
    assert len(collection.measurements) == 11
    for measurement in collection.measurements:
        assert measurement.total_changed_paths > 0
        assert validate_classification(measurement.classification) == []


def test_collector_rejects_missing_commits():
    with pytest.raises(ValueError, match="commit hash not found"):
        collect_changed_paths("0" * 40, repo_root=REPO_ROOT)


def test_inspect_commit_hash_requires_existing_object():
    rows = load_cohort(COHORT_CSV)
    assert inspect_commit_hash(rows[0].commit_hash, repo_root=REPO_ROOT) is True
    assert inspect_commit_hash("0" * 40, repo_root=REPO_ROOT) is False
    assert inspect_commit_hash("", repo_root=REPO_ROOT) is False


def test_classification_totals_reconcile_for_every_commit():
    rows = load_reviewed_cohort(COHORT_CSV)
    collection = collect_cohort_locality(rows, repo_root=REPO_ROOT)
    for measurement in collection.measurements:
        counts = measurement.bucket_counts
        assert sum(counts.values()) == measurement.total_changed_paths
        assert set(counts) == set(PATH_BUCKETS)


def test_collector_matches_ca1_authority_counts():
    rows = load_reviewed_cohort(COHORT_CSV)
    collection = collect_cohort_locality(rows, repo_root=REPO_ROOT)
    assert validate_cohort_locality_collection(rows, collection) == []


def test_measure_commit_locality_reconciles_with_git():
    rows = load_reviewed_cohort(COHORT_CSV)
    row = next(row for row in rows if row.cohort_id == "CA-01")
    paths = collect_changed_paths(row.commit_hash, repo_root=REPO_ROOT)
    summary = compute_locality_counts(paths)
    measurement = measure_commit_locality(row, repo_root=REPO_ROOT)

    assert measurement.total_changed_paths == len(paths)
    assert measurement.bucket_counts == summary.bucket_counts
    assert validate_measurement_against_authority(row, measurement) == []


def test_ca2_report_generation(tmp_path):
    output = tmp_path / "ca2_path_classification_report.md"
    collection, markdown = write_ca2_path_classification_report(
        output,
        csv_path=COHORT_CSV,
        repo_root=REPO_ROOT,
    )
    assert output.exists()
    assert "Bucket definitions" in markdown
    assert "Cohort-wide bucket totals" in markdown
    assert collection.cohort_wide_bucket_totals["unclassified"] == 0
