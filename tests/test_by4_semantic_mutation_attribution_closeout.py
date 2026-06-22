"""BY4 — semantic mutation attribution closeout regression guard."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.protected_semantic_mutation_measurement import (
    assert_probe_non_interference,
    protected_field_values,
)
from tests.helpers.semantic_mutation_attribution_closeout import (
    BY4_REPORT_SCHEMA_VERSION,
    measure_semantic_mutation_attribution_closeout,
    render_semantic_mutation_attribution_closeout_markdown,
)

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[1]
BY2_ARTIFACTS = REPO_ROOT / "artifacts" / "by2"
BY4_ARTIFACTS = REPO_ROOT / "artifacts" / "by4"


def _load_by2_baseline() -> dict | None:
    path = BY2_ARTIFACTS / "protected_semantic_mutation_report.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def test_by4_closeout_generator_regression_guard(tmp_path, monkeypatch) -> None:
    """Closeout generator runs with zero gaps, zero unknown sources, and probe non-interference."""
    result = measure_semantic_mutation_attribution_closeout(
        storage_root=tmp_path,
        monkeypatch=monkeypatch,
        by2_baseline=_load_by2_baseline(),
    )

    report = result["closeout_report"]
    final = report["final_measurement"]
    non_int = report["protected_replay_non_interference"]

    assert report["schema_version"] == BY4_REPORT_SCHEMA_VERSION
    assert final["attribution_gap_count"] == 0
    assert final["unknown_first_source_count"] == 0
    assert final["first_source_coverage_rate"] == 1.0
    assert report["by3_strict_social_gap_closure"]["gap_closed"] is True

    assert non_int["verified"] is True
    assert non_int["final_text_hash_stable"] is True
    assert non_int["protected_fields_stable"] is True

    assert_probe_non_interference(result["baseline_turns"], result["probed_turns"])
    for baseline, probed in zip(result["baseline_turns"], result["probed_turns"]):
        assert baseline.get("final_text_hash") == probed.get("final_text_hash")
        assert protected_field_values(baseline) == protected_field_values(probed)

    markdown = render_semantic_mutation_attribution_closeout_markdown(report)
    assert "How to rerun BY measurement" in markdown
    assert report["schema_promotion_recommendation"]["promote_to_protected_replay_schema_now"] is False


def test_by4_generate_repo_artifacts(tmp_path, monkeypatch) -> None:
    """Refresh artifacts/by4 closeout deliverables."""
    result = measure_semantic_mutation_attribution_closeout(
        storage_root=tmp_path,
        monkeypatch=monkeypatch,
        out_dir=BY4_ARTIFACTS,
        by2_baseline=_load_by2_baseline(),
    )

    report = result["closeout_report"]
    assert (BY4_ARTIFACTS / "semantic_mutation_attribution_closeout.json").is_file()
    assert (BY4_ARTIFACTS / "semantic_mutation_attribution_closeout.md").is_file()

    payload = json.loads(
        (BY4_ARTIFACTS / "semantic_mutation_attribution_closeout.json").read_text(encoding="utf-8")
    )
    assert payload["schema_version"] == BY4_REPORT_SCHEMA_VERSION
    assert payload["final_measurement"]["attribution_gap_count"] == 0
    assert payload["final_measurement"]["unknown_first_source_count"] == 0
