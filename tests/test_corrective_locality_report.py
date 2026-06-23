"""CA3 corrective locality report validation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.corrective_change_locality_cohort import load_cohort, qualifying_rows
from tools.corrective_change_locality_report import (
    build_corrective_locality_report,
    compute_files_touched_per_fix_stats,
    compute_generated_artifact_distortion,
    compute_production_locality_stats,
    compute_repair_family_concentration,
    compute_test_locality_stats,
    qualifying_fix_measurements,
    write_corrective_locality_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
COHORT_CSV = REPO_ROOT / "docs" / "audits" / "CA_corrective_change_locality_cohort.csv"

CA3_EXPECTED_FILES_TOUCHED = {
    "cohort_size": 10,
    "median": 12.5,
    "mean": 87.7,
    "minimum": 5,
    "maximum": 538,
    "p75": 44.0,
    "p90": 248.2,
}

CA3_EXPECTED_PRODUCTION = {
    "median": 2.5,
    "mean": 3.6,
    "minimum": 1,
    "maximum": 9,
}

CA3_EXPECTED_TEST = {
    "median": 2.0,
    "mean": 2.4,
}

CA3_EXPECTED_DISTORTION = {
    "raw_median": 12.5,
    "effective_median": 7.0,
    "median_distortion_pct": 44.0,
    "polluted_fix_count": 3,
    "polluted_fix_pct": 30.0,
}

CA3_EXPECTED_FAMILY = {
    "largest_repair_family": "opening_fallback",
    "largest_repair_family_count": 6,
    "concentration_ratio": 0.6,
}


def test_exclusion_rows_omitted_from_report():
    rows = load_cohort(COHORT_CSV)
    fixes = qualifying_fix_measurements(rows)
    report = build_corrective_locality_report(rows)

    assert len(fixes) == 10
    assert all(fix.cohort_id != "EX-01" for fix in fixes)
    assert report["cohort_composition"]["exclusion_count"] == 1
    assert report["cohort_composition"]["exclusion_ids"] == ["EX-01"]
    assert len(report["qualifying_fixes"]) == 10


def test_statistics_match_authority_data():
    rows = load_cohort(COHORT_CSV)
    fixes = qualifying_fix_measurements(rows)
    report = build_corrective_locality_report(rows)

    for fix in fixes:
        authority = next(row for row in qualifying_rows(rows) if row.cohort_id == fix.cohort_id)
        assert fix.total_files_touched == authority.total_files_touched
        assert fix.production_files_touched == authority.production_files_touched
        assert fix.test_files_touched == authority.test_files_touched
        assert fix.generated_files_touched == authority.generated_files_touched
        assert fix.effective_files_touched == authority.effective_files_touched

    assert report["files_touched_per_fix"] == CA3_EXPECTED_FILES_TOUCHED
    assert report["production_locality"] == CA3_EXPECTED_PRODUCTION
    assert report["test_locality"] == CA3_EXPECTED_TEST


def test_medians_computed_correctly():
    rows = load_cohort(COHORT_CSV)
    fixes = qualifying_fix_measurements(rows)

    files_touched = compute_files_touched_per_fix_stats(fixes)
    production = compute_production_locality_stats(fixes)
    tests = compute_test_locality_stats(fixes)

    assert files_touched["median"] == 12.5
    assert files_touched["p75"] == 44.0
    assert files_touched["p90"] == 248.2
    assert production["median"] == 2.5
    assert tests["median"] == 2.0


def test_effective_locality_computed_correctly():
    rows = load_cohort(COHORT_CSV)
    fixes = qualifying_fix_measurements(rows)
    distortion = compute_generated_artifact_distortion(fixes)

    assert distortion["raw_median"] == 12.5
    assert distortion["effective_median"] == 7.0
    assert distortion["median_distortion_pct"] == 44.0
    assert distortion["polluted_fix_count"] == 3

    by_id = {row["cohort_id"]: row for row in distortion["by_commit"]}
    assert by_id["CA-07"]["effective_files_touched"] == 6
    assert by_id["CA-07"]["distortion_pct"] == pytest.approx(97.22, abs=0.01)
    assert by_id["CA-01"]["distortion_pct"] == 0.0


def test_repair_family_concentration():
    rows = load_cohort(COHORT_CSV)
    fixes = qualifying_fix_measurements(rows)
    families = compute_repair_family_concentration(fixes)

    assert families["largest_repair_family"] == CA3_EXPECTED_FAMILY["largest_repair_family"]
    assert families["largest_repair_family_count"] == CA3_EXPECTED_FAMILY["largest_repair_family_count"]
    assert families["concentration_ratio"] == CA3_EXPECTED_FAMILY["concentration_ratio"]
    assert families["counts"]["opening_fallback"] == 6


def test_report_generation_succeeds(tmp_path):
    md_output = tmp_path / "ca3_corrective_locality_report.md"
    json_output = tmp_path / "ca3_corrective_locality_report.json"

    report, markdown = write_corrective_locality_report(
        md_output_path=md_output,
        json_output_path=json_output,
        csv_path=COHORT_CSV,
        repo_root=REPO_ROOT,
    )

    assert md_output.exists()
    assert json_output.exists()
    assert report["schema_version"] == 1
    assert report["primary_metric"] == "files_touched_per_fix"
    assert "## 1. Executive Summary" in markdown
    assert "## 8. Full Cohort Table" in markdown

    loaded = json.loads(json_output.read_text(encoding="utf-8"))
    assert loaded["files_touched_per_fix"]["cohort_size"] == 10
    assert loaded["generated_artifact_distortion"]["effective_median"] == 7.0
