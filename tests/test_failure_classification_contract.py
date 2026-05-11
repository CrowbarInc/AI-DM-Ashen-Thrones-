from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests.failure_classification_contract import (
    ALLOWED_FAILURE_CATEGORIES,
    ALLOWED_FAILURE_OWNERS,
    ALLOWED_FAILURE_SEVERITIES,
    MAJOR_OWNER_INVESTIGATION_TARGETS,
)
from tests.helpers.failure_classifier import validate_failure_classification_row
from tests.helpers.failure_dashboard_report import build_failure_dashboard_rows, render_failure_dashboard_markdown
from tests.test_failure_dashboard_controlled_failures import _classified_rows


def _valid_sample_row() -> dict[str, Any]:
    return build_failure_dashboard_rows(
        observed_turn={
            "scenario_id": "contract_sample",
            "turn_index": 0,
            "route_kind": "dialogue",
            "selected_speaker_id": "guard",
            "final_emitted_source": "generated_candidate",
            "fallback_family": None,
            "unavailable": [],
            "trace": {"canonical_entry": {"target_actor_id": "runner"}},
        },
        drift_rows=[
            {
                "field_path": "selected_speaker_id",
                "expected": "runner",
                "actual": "guard",
                "reason": "exact value mismatch",
                "drift_bucket": "structural_drift",
            }
        ],
        scenario_id="contract_sample",
        turn_index=0,
    )[0]


def test_controlled_probe_rows_validate_against_contract():
    rows = _classified_rows()
    assert rows
    for row in rows:
        assert validate_failure_classification_row(row) == []


def test_sample_classifier_row_validates_against_contract():
    assert validate_failure_classification_row(_valid_sample_row()) == []


@pytest.mark.parametrize(
    ("field", "value", "expected_error"),
    [
        ("category", "mystery", "invalid category"),
        ("severity", "catastrophic", "invalid severity"),
        ("primary_owner", None, "invalid primary_owner"),
        ("investigate_first", "", "investigate_first must be a non-empty string"),
    ],
)
def test_invalid_core_contract_fields_fail_validation(field, value, expected_error):
    row = _valid_sample_row()
    row[field] = value

    errors = validate_failure_classification_row(row)

    assert any(expected_error in error for error in errors)


def test_unknown_replay_tag_fails_unless_experimental():
    row = _valid_sample_row()
    row["replay_tags"] = ["structural_drift", "new_unreviewed_tag"]
    assert any("invalid replay_tag" in error for error in validate_failure_classification_row(row))

    row["replay_tags"] = ["structural_drift", "experimental:new_unreviewed_tag"]
    assert validate_failure_classification_row(row) == []


def test_missing_primary_owner_fails_validation():
    row = _valid_sample_row()
    del row["primary_owner"]

    errors = validate_failure_classification_row(row)

    assert "missing required field: primary_owner" in errors
    assert any("invalid primary_owner" in error for error in errors)


def test_dashboard_renderer_rejects_invalid_classification_rows():
    row = _valid_sample_row()
    row["category"] = "mystery"

    with pytest.raises(ValueError, match="invalid failure dashboard row"):
        render_failure_dashboard_markdown([row])


def test_dashboard_markdown_keeps_diagnostic_headers():
    report = render_failure_dashboard_markdown(
        [_valid_sample_row()],
        generated_at="2026-05-11T00:00:00Z",
        command_used="pytest contract",
    )

    for header in (
        "Scenario",
        "Turn",
        "Category",
        "Severity",
        "Primary Owner",
        "Secondary Owner",
        "Investigate First",
        "Replay Tags",
        "Evidence",
    ):
        assert header in report


def test_owner_matrix_and_schema_docs_cover_contract_taxonomy():
    root = Path(__file__).resolve().parents[1]
    owner_doc = (root / "audits" / "failure_owner_matrix.md").read_text(encoding="utf-8")
    schema_doc = (root / "audits" / "proposed_failure_classification_schema.md").read_text(encoding="utf-8")
    combined = f"{owner_doc}\n{schema_doc}"

    for owner in ALLOWED_FAILURE_OWNERS:
        if owner == "none":
            continue
        assert owner in combined

    for category in ALLOWED_FAILURE_CATEGORIES:
        assert f"`{category}`" in schema_doc or category in owner_doc

    for owner, target in MAJOR_OWNER_INVESTIGATION_TARGETS.items():
        assert owner
        assert target
