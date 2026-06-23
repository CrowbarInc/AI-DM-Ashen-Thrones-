"""CA9 embedded corrective work attribution validation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.embedded_corrective_attribution import (
    ATTRIBUTION_CATEGORIES,
    build_attribution_concentration,
    build_embedded_candidate_records,
    build_exclusion_lookup,
    compute_embedded_corrective_share,
    extract_cycle_program_affiliation,
    load_ca8_report,
    load_embedded_candidates_from_ca8,
    write_embedded_corrective_attribution_report,
)
from tests.helpers.post_baseline_corrective_cohort import load_post_baseline_exclusions

REPO_ROOT = Path(__file__).resolve().parents[1]
CA8_JSON = REPO_ROOT / "artifacts" / "ca8_corrective_fix_availability_report.json"
EXCLUSIONS_CSV = REPO_ROOT / "docs" / "audits" / "CA_post_baseline_exclusions.csv"
REVIEW_QUEUE_CSV = REPO_ROOT / "docs" / "audits" / "ca_review_queue.csv"

CA9_EXPECTED_ATTRIBUTION_COUNTS = {
    "ownership_compression": 2,
    "replay_stabilization": 1,
    "fallback_consolidation": 3,
    "observability_expansion": 0,
    "decomposition": 3,
    "governance_enforcement": 0,
    "other": 0,
}

CA9_EXPECTED_CYCLES = {"AB", "AJ", "AM", "AO", "AP", "BK", "I", "P"}


def _embedded_records():
    ca8 = load_ca8_report(CA8_JSON, repo_root=REPO_ROOT)
    exclusions = load_post_baseline_exclusions(EXCLUSIONS_CSV)
    return build_embedded_candidate_records(
        load_embedded_candidates_from_ca8(ca8),
        build_exclusion_lookup(exclusions),
    )


def test_candidate_accounting():
    records = _embedded_records()

    assert len(records) == 9
    assert len({record.commit_hash for record in records}) == 9
    assert all(record.production_files_touched > 0 for record in records)
    assert all(record.cycle_program_affiliation in CA9_EXPECTED_CYCLES for record in records)
    assert all(record.attribution_category in ATTRIBUTION_CATEGORIES for record in records)
    assert all(record.embedded_corrective_rationale for record in records)


def test_attribution_totals():
    records = _embedded_records()
    concentration = build_attribution_concentration(records)

    assert concentration["total_embedded_candidates"] == 9
    assert concentration["counts"] == CA9_EXPECTED_ATTRIBUTION_COUNTS
    assert sum(concentration["counts"].values()) == 9
    for category in ATTRIBUTION_CATEGORIES:
        assert len(concentration["by_category"][category]) == concentration["counts"][category]


def test_share_calculations():
    share = compute_embedded_corrective_share(9, 0)

    assert share["embedded_corrective_work"] == 9
    assert share["explicit_corrective_fixes"] == 0
    assert share["embedded_corrective_share"] == 1.0
    assert share["primary_metric"] == "embedded_corrective_share"


def test_concentration_calculations():
    records = _embedded_records()
    concentration = build_attribution_concentration(records)

    assert concentration["largest_category"] == "decomposition"
    assert concentration["largest_category_count"] == 3
    assert concentration["largest_category_percentage"] == pytest.approx(33.33, abs=0.01)
    assert concentration["cumulative_top_categories"][-1]["cumulative_share"] == 1.0
    assert concentration["cumulative_top_categories"][-1]["count"] == 9
    assert concentration["cumulative_top_categories"][0]["categories"] == ["decomposition"]


def test_cycle_extraction_from_review_notes():
    assert extract_cycle_program_affiliation("BK: Fallback Ownership Compression", "cycle=BK") == "BK"
    assert extract_cycle_program_affiliation("Cycle I: Contract opening fallback authorship attribution", "cycle=I") == "I"
    assert extract_cycle_program_affiliation("Close Cycle AB fallback topology collapse", "cycle=AB") == "AB"


def test_report_generation(tmp_path):
    output_md = tmp_path / "ca9_embedded_corrective_attribution_report.md"
    output_json = tmp_path / "ca9_embedded_corrective_attribution_report.json"

    report, markdown = write_embedded_corrective_attribution_report(
        md_output_path=output_md,
        json_output_path=output_json,
        ca8_json_path=CA8_JSON,
        exclusions_csv_path=EXCLUSIONS_CSV,
        review_queue_path=REVIEW_QUEUE_CSV,
        repo_root=REPO_ROOT,
    )

    assert output_md.exists()
    assert output_json.exists()
    assert len(report["embedded_candidate_inventory"]) == 9
    assert report["attribution_categories"]["counts"] == CA9_EXPECTED_ATTRIBUTION_COUNTS
    assert report["embedded_corrective_share_analysis"]["embedded_corrective_share"] == 1.0
    assert report["concentration_analysis"]["largest_category"] == "decomposition"
    assert "## 1. Executive Summary" in markdown
    assert "## 6. Interpretation" in markdown

    persisted = json.loads(output_json.read_text(encoding="utf-8"))
    assert persisted["embedded_corrective_share_analysis"] == report["embedded_corrective_share_analysis"]
