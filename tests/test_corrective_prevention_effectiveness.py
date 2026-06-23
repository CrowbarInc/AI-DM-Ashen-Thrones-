"""CA10 corrective prevention effectiveness validation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.corrective_prevention_effectiveness import (
    PREVENTION_CATEGORIES,
    build_category_concentration,
    build_corrective_prevention_effectiveness_report,
    classify_category_prevention_effectiveness,
    compute_category_prevention_signals,
    compute_preventive_absorption_ratio,
    embedded_candidates_by_category,
    load_ca7_report,
    load_ca8_report,
    load_ca9_report,
    write_corrective_prevention_effectiveness_report,
)
from tests.helpers.corrective_fix_absence_report import load_baseline_summary

REPO_ROOT = Path(__file__).resolve().parents[1]
CA7_JSON = REPO_ROOT / "artifacts" / "ca7_corrective_fix_absence_report.json"
CA8_JSON = REPO_ROOT / "artifacts" / "ca8_corrective_fix_availability_report.json"
CA9_JSON = REPO_ROOT / "artifacts" / "ca9_embedded_corrective_attribution_report.json"
BASELINE_JSON = REPO_ROOT / "docs" / "baselines" / "ca_corrective_locality_baseline.json"

CA10_EXPECTED_COUNTS = {
    "fallback_consolidation": 3,
    "decomposition": 3,
    "ownership_compression": 2,
    "replay_stabilization": 1,
}


def _reports():
    ca7 = load_ca7_report(CA7_JSON, repo_root=REPO_ROOT)
    ca8 = load_ca8_report(CA8_JSON, repo_root=REPO_ROOT)
    ca9 = load_ca9_report(CA9_JSON, repo_root=REPO_ROOT)
    baseline_summary = load_baseline_summary(BASELINE_JSON, repo_root=REPO_ROOT)
    baseline_payload = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    baseline = {
        **baseline_summary,
        "repair_family_distribution": baseline_payload.get("repair_family_distribution") or {},
    }
    return ca7, ca8, ca9, baseline


def test_ratio_calculations():
    ratio = compute_preventive_absorption_ratio(9, 0)

    assert ratio["embedded_corrective_work"] == 9
    assert ratio["explicit_corrective_fixes"] == 0
    assert ratio["embedded_share"] == 1.0
    assert ratio["preventive_absorption_ratio"] == 1.0
    assert ratio["primary_metric"] == "preventive_absorption_ratio"


def test_category_accounting():
    _ca7, ca8, ca9, baseline = _reports()
    category_map = embedded_candidates_by_category(ca9)

    assert sum(len(rows) for rows in category_map.values()) == 9
    assert {category: len(category_map[category]) for category in PREVENTION_CATEGORIES} == CA10_EXPECTED_COUNTS

    report = build_corrective_prevention_effectiveness_report(
        ca7_report=_ca7,
        ca8_report=ca8,
        ca9_report=ca9,
        baseline=baseline,
    )
    activity = report["embedded_corrective_activity"]
    assert activity["embedded_corrective_count"] == 9
    assert activity["explicit_corrective_count"] == 0
    assert activity["category_concentration"]["counts"] == CA10_EXPECTED_COUNTS
    assert activity["category_concentration"]["largest_category"] == "decomposition"


def test_assessment_generation():
    _ca7, ca8, ca9, baseline = _reports()
    report = build_corrective_prevention_effectiveness_report(
        ca7_report=_ca7,
        ca8_report=ca8,
        ca9_report=ca9,
        baseline=baseline,
    )

    assessments = report["category_assessments"]
    assert len(assessments) == 4
    by_category = {item["category"]: item for item in assessments}
    assert by_category["fallback_consolidation"]["classification"] == "likely_preventive"
    assert by_category["decomposition"]["classification"] == "likely_preventive"
    assert by_category["ownership_compression"]["classification"] == "likely_preventive"
    assert by_category["replay_stabilization"]["classification"] == "unclear"
    assert all(item["rationale"] for item in assessments)

    decomposition_signals = by_category["decomposition"]["prevention_signals"]
    assert decomposition_signals["production_touching_count"] == 3
    assert decomposition_signals["test_touching_count"] == 2


def test_concentration_calculations():
    concentration = build_category_concentration(CA10_EXPECTED_COUNTS, 9)

    assert concentration["largest_category_count"] == 3
    assert concentration["cumulative_top_categories"][-1]["cumulative_share"] == 1.0
    assert concentration["cumulative_top_categories"][0]["categories"] == ["decomposition"]


def test_category_prevention_signals():
    _ca7, _ca8, ca9, _baseline = _reports()
    category_map = embedded_candidates_by_category(ca9)
    signals = compute_category_prevention_signals(
        "fallback_consolidation",
        category_map["fallback_consolidation"],
    )

    assert signals.candidate_count == 3
    assert signals.production_touching_count == 3
    assert signals.test_touching_count == 3
    assert signals.ownership_involvement_count == 3


def test_report_generation(tmp_path):
    output_md = tmp_path / "ca10_corrective_prevention_effectiveness_report.md"
    output_json = tmp_path / "ca10_corrective_prevention_effectiveness_report.json"

    report, markdown = write_corrective_prevention_effectiveness_report(
        md_output_path=output_md,
        json_output_path=output_json,
        ca7_json_path=CA7_JSON,
        ca8_json_path=CA8_JSON,
        ca9_json_path=CA9_JSON,
        baseline_json_path=BASELINE_JSON,
        repo_root=REPO_ROOT,
    )

    assert output_md.exists()
    assert output_json.exists()
    assert report["preventive_absorption_ratio_analysis"]["preventive_absorption_ratio"] == 1.0
    assert len(report["category_assessments"]) == 4
    assert report["baseline_context"]["largest_repair_family"] == "opening_fallback"
    assert "## 1. Executive Summary" in markdown
    assert "## 7. Conclusion" in markdown

    persisted = json.loads(output_json.read_text(encoding="utf-8"))
    assert persisted["preventive_absorption_ratio_analysis"] == report["preventive_absorption_ratio_analysis"]
