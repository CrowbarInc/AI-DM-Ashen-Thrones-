"""CA4 corrective locality baseline lock validation."""
from __future__ import annotations

import json
from pathlib import Path

from tests.helpers.corrective_locality_baseline import (
    CA4_FROZEN_BASELINE,
    REQUIRED_BASELINE_FIELDS,
    REQUIRED_DISTORTION_FIELDS,
    extract_baseline_payload_from_ca3_report,
    load_baseline,
    validate_baseline,
    validate_baseline_matches_ca3_report,
    validate_baseline_matches_frozen_record,
    validate_baseline_reproducible_from_cohort,
    validate_baseline_schema,
    validate_required_fields,
    write_ca4_baseline_lock_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_JSON = REPO_ROOT / "docs" / "baselines" / "ca_corrective_locality_baseline.json"
CA3_JSON = REPO_ROOT / "artifacts" / "ca3_corrective_locality_report.json"
COHORT_CSV = REPO_ROOT / "docs" / "audits" / "CA_corrective_change_locality_cohort.csv"


def test_baseline_loads():
    baseline = load_baseline(BASELINE_JSON)
    assert baseline["baseline_version"] == 1
    assert baseline["comparison_ready"] is True
    assert baseline["cohort_size"] == 10


def test_required_fields_exist():
    baseline = load_baseline(BASELINE_JSON)
    assert validate_required_fields(baseline) == []
    for field in REQUIRED_BASELINE_FIELDS:
        assert field in baseline


def test_schema_validation_passes():
    baseline = load_baseline(BASELINE_JSON)
    assert validate_baseline_schema(baseline) == []


def test_values_match_ca3_report():
    baseline = load_baseline(BASELINE_JSON)
    ca3_report = json.loads(CA3_JSON.read_text(encoding="utf-8"))

    assert validate_baseline_matches_ca3_report(baseline, ca3_report) == []
    derived = extract_baseline_payload_from_ca3_report(ca3_report)
    assert derived["median_files_touched_raw"] == 12.5
    assert derived["median_files_touched_effective"] == 7.0
    assert derived["median_production_files"] == 2.5
    assert derived["median_test_files"] == 2.0
    assert derived["generated_artifact_distortion"]["median_distortion_pct"] == 44.0


def test_values_reproducible_from_cohort_authority():
    baseline = load_baseline(BASELINE_JSON)
    assert validate_baseline_reproducible_from_cohort(baseline, csv_path=COHORT_CSV) == []


def test_baseline_matches_frozen_record():
    baseline = load_baseline(BASELINE_JSON)
    assert validate_baseline_matches_frozen_record(baseline) == []
    assert baseline["max_files_touched"] == CA4_FROZEN_BASELINE["max_files_touched"]
    assert (
        baseline["repair_family_distribution"]["counts"]
        == CA4_FROZEN_BASELINE["repair_family_distribution"]["counts"]
    )


def test_full_baseline_validation_passes():
    assert validate_baseline(BASELINE_JSON, ca3_report_path=CA3_JSON, csv_path=COHORT_CSV) == []


def test_baseline_lock_report_generation(tmp_path):
    output = tmp_path / "ca4_baseline_lock_report.md"
    baseline, markdown = write_ca4_baseline_lock_report(
        output,
        baseline_path=BASELINE_JSON,
        ca3_report_path=CA3_JSON,
        csv_path=COHORT_CSV,
        repo_root=REPO_ROOT,
    )
    assert output.exists()
    assert baseline["primary_metric"] == "files_touched_per_fix"
    assert "Frozen baseline values" in markdown
    assert "Validation status:** PASS" in markdown


def test_validation_fails_when_required_metric_missing():
    broken = dict(CA4_FROZEN_BASELINE)
    broken.pop("median_files_touched_raw")
    assert any("missing required field" in err for err in validate_required_fields(broken))


def test_validation_fails_when_baseline_values_change_unexpectedly():
    baseline = load_baseline(BASELINE_JSON)
    mutated = dict(baseline)
    mutated["median_files_touched_raw"] = 999.0
    assert validate_baseline_matches_frozen_record(mutated) != []


def test_validation_fails_when_distortion_block_incomplete():
    baseline = load_baseline(BASELINE_JSON)
    broken = dict(baseline)
    broken["generated_artifact_distortion"] = {"raw_median": 12.5}
    errors = validate_baseline_schema(broken)
    assert any("generated_artifact_distortion missing" in err for err in errors)
    for field in REQUIRED_DISTORTION_FIELDS:
        if field != "raw_median":
            assert any(field in err for err in errors)
