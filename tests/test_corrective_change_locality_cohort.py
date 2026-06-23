"""CA1 corrective-change locality cohort authority validation."""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.corrective_change_locality_cohort import (
    COUNT_COLUMNS,
    REQUIRED_COLUMNS,
    load_cohort,
    validate_cohort,
    validate_cohort_id_uniqueness,
    validate_commit_hash_uniqueness,
    validate_no_missing_counts,
    validate_required_columns,
    validate_schema,
    write_ca1_cohort_authority_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
COHORT_CSV = REPO_ROOT / "docs" / "audits" / "CA_corrective_change_locality_cohort.csv"


def test_cohort_loads_successfully():
    rows = load_cohort(COHORT_CSV)
    assert len(rows) == 11


def test_ten_qualifying_entries_exist():
    rows = load_cohort(COHORT_CSV)
    qualifying = [row for row in rows if row.qualifies]
    assert len(qualifying) == 10


def test_exactly_one_exclusion_entry_exists():
    rows = load_cohort(COHORT_CSV)
    exclusions = [row for row in rows if not row.qualifies]
    assert len(exclusions) == 1
    assert exclusions[0].cohort_id == "EX-01"


def test_commit_hashes_are_unique():
    rows = load_cohort(COHORT_CSV)
    assert validate_commit_hash_uniqueness(rows) == []


def test_cohort_ids_are_unique():
    rows = load_cohort(COHORT_CSV)
    assert validate_cohort_id_uniqueness(rows) == []


def test_required_columns_exist():
    with COHORT_CSV.open(encoding="utf-8-sig", newline="") as handle:
        import csv

        reader = csv.DictReader(handle)
        assert validate_required_columns(reader.fieldnames) == []
        assert set(REQUIRED_COLUMNS).issubset(set(reader.fieldnames or []))


def test_no_missing_counts():
    rows = load_cohort(COHORT_CSV)
    assert validate_no_missing_counts(rows) == []
    for row in rows:
        for field in COUNT_COLUMNS:
            assert getattr(row, field) >= 0


def test_full_cohort_schema_validation_passes():
    rows = load_cohort(COHORT_CSV)
    assert validate_schema(rows) == []
    assert validate_cohort(COHORT_CSV) == []


def test_ca1_report_generation(tmp_path):
    output = tmp_path / "ca1_cohort_authority_report.md"
    summary, markdown = write_ca1_cohort_authority_report(
        output,
        csv_path=COHORT_CSV,
    )
    assert output.exists()
    assert summary["qualifying_count"] == 10
    assert summary["exclusion_count"] == 1
    assert "Confidence distribution" in markdown
    assert "Repair family distribution" in markdown
    assert "Recurrence evidence distribution" in markdown


def test_validate_cohort_fails_on_duplicate_commit_hash(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text(
        "\n".join(
            [
                ",".join(REQUIRED_COLUMNS),
                "CA-01,abc123,2026-03-21,title,true,high,defect,family,none,"
                "1,1,0,0,0,0,0,1,",
                "CA-02,abc123,2026-03-22,title2,true,high,defect2,family2,none,"
                "1,1,0,0,0,0,0,1,",
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate commit_hash"):
        write_ca1_cohort_authority_report(output_path=tmp_path / "report.md", csv_path=bad_csv)
