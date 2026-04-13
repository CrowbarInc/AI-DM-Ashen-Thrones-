"""DTD3: report surfaces derive dead-turn visibility from FEM / gameplay_validation only."""

from __future__ import annotations

import pytest

from game.dead_turn_report_visibility import (
    SCHEMA_VERSION,
    build_dead_turn_run_report,
    enrich_playability_rollup_dict,
    markdown_dead_turn_header_block,
    per_turn_dead_turn_visibility,
)

pytestmark = pytest.mark.unit


def test_per_turn_row_reads_fem_only_no_reclassification() -> None:
    rec = {
        "_final_emission_meta": {
            "dead_turn": {
                "is_dead_turn": True,
                "dead_turn_class": "retry_terminal_fallback",
                "dead_turn_reason_codes": ["forced_retry_terminal_route"],
                "validation_playable": False,
                "manual_test_valid": False,
            }
        },
        "ok": True,
    }
    row = per_turn_dead_turn_visibility(rec, turn_index=2)
    assert row["dead_turn_detected"] is True
    assert row["dead_turn_class"] == "retry_terminal_fallback"
    assert "forced_retry_terminal_route" in row["dead_turn_reason_codes"]
    assert row["manual_test_valid"] is False
    assert row["excluded_from_scoring"] is True
    assert row["run_valid"] is False
    assert isinstance(row["invalidation_reason"], str) and "dead_turn" in row["invalidation_reason"]


def test_build_run_report_counts_indexes_and_banner() -> None:
    records = [
        {"turn_index": 0, "ok": True, "_final_emission_meta": {}},
        {
            "turn_index": 1,
            "ok": True,
            "_final_emission_meta": {
                "dead_turn": {
                    "is_dead_turn": True,
                    "dead_turn_class": "retry_terminal_fallback",
                    "dead_turn_reason_codes": ["upstream_api_error"],
                    "validation_playable": False,
                    "manual_test_valid": False,
                }
            },
        },
    ]
    rep = build_dead_turn_run_report(records)
    assert rep["schema_version"] == SCHEMA_VERSION
    assert rep["dead_turn_count"] == 1
    assert rep["dead_turn_indexes"] == [1]
    assert rep["dead_turn_turn_numbers_one_based"] == [2]
    assert rep["dead_turn_by_class"] == {"retry_terminal_fallback": 1}
    assert rep["banner"] == "DEAD TURN DETECTED — retry_terminal_fallback"
    assert rep["invalid_for_gameplay_conclusions"] is True
    assert "upstream fallback" in (rep.get("invalid_run_explanation") or "").lower()


def test_clean_run_no_banner_no_false_alarm_in_markdown() -> None:
    rep = build_dead_turn_run_report([{"turn_index": 0, "ok": True, "_final_emission_meta": {}}])
    assert rep["dead_turn_count"] == 0
    assert rep["banner"] is None
    md = markdown_dead_turn_header_block(rep)
    assert "DEAD TURN DETECTED" not in md
    assert "Dead turn detected" in md
    assert "Run valid for gameplay conclusions" in md


def test_enrich_playability_rollup_adds_indexes_from_nested_dead_turn() -> None:
    turns_out = [
        {
            "playability_eval": {
                "gameplay_validation": {
                    "run_valid": True,
                    "dead_turn_count": 0,
                    "dead_turn": {"is_dead_turn": False},
                }
            }
        },
        {
            "playability_eval": {
                "gameplay_validation": {
                    "run_valid": False,
                    "excluded_from_scoring": True,
                    "dead_turn_count": 1,
                    "dead_turn": {
                        "is_dead_turn": True,
                        "dead_turn_class": "upstream_api_failure",
                    },
                }
            }
        },
    ]
    base = {"run_valid": False, "dead_turn_count": 1, "excluded_from_scoring": True}
    enriched = enrich_playability_rollup_dict(turns_out, base)
    assert enriched["dead_turn_indexes"] == [1]
    assert enriched["dead_turn_by_class"] == {"upstream_api_failure": 1}
    assert enriched["dead_turn_banner"] == "DEAD TURN DETECTED — upstream_api_failure"
    assert enriched.get("invalid_run_explanation")


def test_gm_output_nested_fem_supported() -> None:
    rec = {
        "gm_output": {
            "_final_emission_meta": {
                "dead_turn": {
                    "is_dead_turn": True,
                    "dead_turn_class": "malformed_emergency_output",
                    "dead_turn_reason_codes": ["malformed_emergency_output"],
                    "validation_playable": False,
                    "manual_test_valid": False,
                }
            }
        },
        "ok": True,
    }
    row = per_turn_dead_turn_visibility(rec, turn_index=0)
    assert row["dead_turn_class"] == "malformed_emergency_output"
    assert row["dead_turn_detected"] is True


def test_markdown_banner_line_matches_first_dead_class() -> None:
    rep = build_dead_turn_run_report(
        [
            {
                "ok": True,
                "_final_emission_meta": {
                    "dead_turn": {
                        "is_dead_turn": True,
                        "dead_turn_class": "retry_terminal_fallback",
                        "dead_turn_reason_codes": ["x"],
                        "validation_playable": False,
                        "manual_test_valid": False,
                    }
                },
            }
        ]
    )
    md = markdown_dead_turn_header_block(rep)
    assert "> **DEAD TURN DETECTED — retry_terminal_fallback**" in md
    assert rep.get("invalid_run_explanation")


def test_chat_error_count_engine_failures() -> None:
    rep = build_dead_turn_run_report(
        [
            {"turn_index": 0, "ok": False, "_final_emission_meta": {}},
            {"turn_index": 1, "ok": True, "_final_emission_meta": {}},
        ]
    )
    assert rep["chat_error_count"] == 1
