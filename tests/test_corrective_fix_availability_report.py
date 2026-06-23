"""CA8 corrective fix availability report validation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.corrective_fix_availability_report import (
    LATENT_ACTIVITY_CATEGORIES,
    analyze_exclusions,
    build_corrective_fix_availability_report,
    build_exclusion_composition,
    build_latent_activity_distribution,
    compute_corrective_availability_rate,
    load_ca7_report,
    write_corrective_fix_availability_report,
)
from tests.helpers.corrective_fix_absence_report import load_baseline_summary, load_inventory_candidates
from tests.helpers.post_baseline_corrective_cohort import (
    load_post_baseline_exclusions,
    load_review_queue,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
EXCLUSIONS_CSV = REPO_ROOT / "docs" / "audits" / "CA_post_baseline_exclusions.csv"
REVIEW_QUEUE_CSV = REPO_ROOT / "docs" / "audits" / "ca_review_queue.csv"
BASELINE_JSON = REPO_ROOT / "docs" / "baselines" / "ca_corrective_locality_baseline.json"
CA7_JSON = REPO_ROOT / "artifacts" / "ca7_corrective_fix_absence_report.json"
INVENTORY_JSON = REPO_ROOT / "artifacts" / "ca5_candidate_inventory.json"

CA8_EXPECTED_COMPOSITION = {
    "production_touching_exclusions": 9,
    "test_touching_exclusions": 25,
    "ownership_related_exclusions": 9,
    "replay_related_exclusions": 15,
    "governance_related_exclusions": 5,
    "instrumentation_related_exclusions": 6,
}

CA8_EXPECTED_LATENT_COUNTS = {
    "explicit_corrective_fixes": 0,
    "embedded_corrective_work": 9,
    "structural_prevention_work": 14,
    "pure_governance_work": 3,
}


def test_exclusion_accounting():
    exclusions = load_post_baseline_exclusions(EXCLUSIONS_CSV)
    inventory = load_inventory_candidates(INVENTORY_JSON, repo_root=REPO_ROOT)
    analyzed = analyze_exclusions(exclusions, inventory)

    assert len(analyzed) == 26
    assert len({row.commit_hash for row in analyzed}) == 26
    assert all(row.latent_activity_category in LATENT_ACTIVITY_CATEGORIES for row in analyzed)


def test_category_totals():
    exclusions = load_post_baseline_exclusions(EXCLUSIONS_CSV)
    inventory = load_inventory_candidates(INVENTORY_JSON, repo_root=REPO_ROOT)
    analyzed = analyze_exclusions(exclusions, inventory)
    composition = build_exclusion_composition(analyzed)
    latent = build_latent_activity_distribution(analyzed)

    assert composition["total_exclusions"] == 26
    assert composition["counts"] == CA8_EXPECTED_COMPOSITION
    assert latent["counts"] == CA8_EXPECTED_LATENT_COUNTS
    assert sum(latent["counts"].values()) == 26
    for category in LATENT_ACTIVITY_CATEGORIES:
        assert len(latent["by_category"][category]) == latent["counts"][category]


def test_availability_calculations():
    exclusions = load_post_baseline_exclusions(EXCLUSIONS_CSV)
    inventory = load_inventory_candidates(INVENTORY_JSON, repo_root=REPO_ROOT)
    latent = build_latent_activity_distribution(analyze_exclusions(exclusions, inventory))
    availability = compute_corrective_availability_rate(latent, 26)

    assert availability["explicit_corrective_fixes"] == 0
    assert availability["embedded_corrective_work"] == 9
    assert availability["reviewed_candidates"] == 26
    assert availability["corrective_availability_rate"] == 0.3462


def test_report_generation(tmp_path):
    output_md = tmp_path / "ca8_corrective_fix_availability_report.md"
    output_json = tmp_path / "ca8_corrective_fix_availability_report.json"

    report, markdown = write_corrective_fix_availability_report(
        md_output_path=output_md,
        json_output_path=output_json,
        ca7_json_path=CA7_JSON,
        exclusions_csv_path=EXCLUSIONS_CSV,
        review_queue_path=REVIEW_QUEUE_CSV,
        baseline_json_path=BASELINE_JSON,
        inventory_json_path=INVENTORY_JSON,
        repo_root=REPO_ROOT,
    )

    assert output_md.exists()
    assert output_json.exists()
    assert report["availability_analysis"]["corrective_availability_rate"] == 0.3462
    assert report["latent_activity_distribution"]["counts"] == CA8_EXPECTED_LATENT_COUNTS
    assert report["exclusion_composition"]["counts"] == CA8_EXPECTED_COMPOSITION
    assert "defects_absorbed_into_program_work" in report["availability_assessment"]["primary_causes"]
    assert "## 1. Executive Summary" in markdown
    assert "## 7. Risks And Limitations" in markdown

    persisted = json.loads(output_json.read_text(encoding="utf-8"))
    assert persisted["availability_analysis"] == report["availability_analysis"]


def test_build_report_from_inputs():
    exclusions = load_post_baseline_exclusions(EXCLUSIONS_CSV)
    queue = load_review_queue(REVIEW_QUEUE_CSV)
    inventory = load_inventory_candidates(INVENTORY_JSON, repo_root=REPO_ROOT)
    baseline = load_baseline_summary(BASELINE_JSON, repo_root=REPO_ROOT)
    ca7 = load_ca7_report(CA7_JSON, repo_root=REPO_ROOT)

    report = build_corrective_fix_availability_report(
        exclusions=exclusions,
        reviewed_candidates=sum(1 for row in queue if row.reviewed),
        inventory=inventory,
        baseline=baseline,
        ca7_report=ca7,
    )

    assert report["schema_version"] == 1
    assert report["sources"]["ca7_report_json"] == "artifacts/ca7_corrective_fix_absence_report.json"
    assert report["availability_assessment"]["observation_window_days"] == 27
