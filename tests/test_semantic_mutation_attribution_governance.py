"""CU5 semantic mutation attribution governance contract locks."""
from __future__ import annotations

import pytest

from game.semantic_mutation_attribution import (
    SEMANTIC_MUTATION_ATTRIBUTION_CONTRACT,
    SEMANTIC_MUTATION_EVIDENCE_PRECEDENCE,
    SEMANTIC_MUTATION_WRITE_SITE_FAMILIES,
    reconcile_semantic_mutation_owner,
    validate_semantic_mutation_contract,
)
from tests.helpers.failure_classifier import classify_replay_failure, validate_failure_classification_row
from tests.helpers.failure_dashboard_report import render_failure_dashboard_markdown
from tests.helpers.golden_replay_fixtures import minimal_turn_payload
from tests.helpers.golden_replay_projection import project_turn_observation, protected_observation_field_paths

pytestmark = pytest.mark.unit


def _selected_write_site(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "write_site_family": "fallback",
        "write_site_file": "game/fallback_provenance_debug.py",
        "write_site_function": "finalize_upstream_fallback_overwrite_containment",
        "owner": "game.fallback_provenance_debug",
        "before_semantic_hash": "before",
        "after_semantic_hash": "after",
        "selected_active_stream": True,
        "candidate_only": False,
    }
    row.update(overrides)
    return row


def _projection_trace(**overrides: object) -> dict[str, object]:
    trace: dict[str, object] = {
        "first_semantic_mutation_bucket": "sanitizer",
        "first_semantic_mutation_source": "projected.sanitizer",
        "first_semantic_mutation_owner": "game.output_sanitizer",
        "semantic_mutation_changed_count": 1,
    }
    trace.update(overrides)
    return trace


def _error_codes(result: dict[str, object]) -> set[str]:
    return {
        str(row.get("code"))
        for row in result.get("errors", [])
        if isinstance(row, dict)
    }


def test_cu5_contract_definition_names_governed_semantics() -> None:
    assert SEMANTIC_MUTATION_ATTRIBUTION_CONTRACT["evidence_precedence"] == SEMANTIC_MUTATION_EVIDENCE_PRECEDENCE
    assert SEMANTIC_MUTATION_EVIDENCE_PRECEDENCE[0] == "write_site"
    assert SEMANTIC_MUTATION_EVIDENCE_PRECEDENCE[-1] == "projection_inference"
    assert {"prompt", "policy", "sanitizer", "repair", "fallback", "final_emission"} <= (
        SEMANTIC_MUTATION_WRITE_SITE_FAMILIES
    )
    assert "candidate-only evidence can never become authoritative" in SEMANTIC_MUTATION_ATTRIBUTION_CONTRACT["guarantees"]


def test_cu5_exactly_one_authoritative_owner_for_emitted_mutation() -> None:
    fem = {"semantic_mutation_write_sites": [_selected_write_site()]}

    reconciled = reconcile_semantic_mutation_owner(
        fem=fem,
        projection_metadata=_projection_trace(),
    )
    validation = validate_semantic_mutation_contract(
        fem=fem,
        projection_metadata=_projection_trace(),
        projected_attribution=reconciled.as_dict(),
    )

    assert validation["valid"] is True
    assert reconciled.authoritative_mutation_owner == "game.fallback_provenance_debug"
    assert reconciled.authoritative_evidence_source == "write_site"
    assert reconciled.used_projection_inference is False


def test_cu5_no_authoritative_owner_when_no_mutation_exists() -> None:
    validation = validate_semantic_mutation_contract(fem={})

    assert validation["valid"] is True
    assert validation["expected_attribution"]["authoritative_mutation_owner"] is None
    assert validation["expected_attribution"]["authoritative_evidence_source"] is None


def test_cu5_candidate_only_records_never_become_authoritative() -> None:
    fem = {
        "semantic_mutation_write_sites": [
            _selected_write_site(
                owner="game.upstream_response_repairs",
                selected_active_stream=False,
                candidate_only=True,
            )
        ]
    }

    reconciled = reconcile_semantic_mutation_owner(fem=fem)
    validation = validate_semantic_mutation_contract(fem=fem)

    assert validation["valid"] is True
    assert reconciled.authoritative_mutation_owner is None
    assert reconciled.authoritative_evidence_source is None


def test_cu5_projection_inference_never_overrides_explicit_write_site_evidence() -> None:
    fem = {"semantic_mutation_write_sites": [_selected_write_site()]}
    validation = validate_semantic_mutation_contract(
        fem=fem,
        projection_metadata=_projection_trace(),
        projected_attribution={
            "authoritative_mutation_owner": "game.output_sanitizer",
            "authoritative_mutation_family": "sanitizer",
            "authoritative_evidence_source": "projection_inference",
            "authoritative_mutation_confidence": "inferred",
            "used_projection_inference": True,
        },
    )

    assert "invalid_precedence" in _error_codes(validation)
    assert "projection_inference_overrode_stronger_evidence" in _error_codes(validation)


def test_cu5_unknown_write_site_family_fails_validation() -> None:
    validation = validate_semantic_mutation_contract(
        fem={"semantic_mutation_write_sites": [_selected_write_site(write_site_family="unowned_new_family")]}
    )

    assert "invalid_write_site_family" in _error_codes(validation)


def test_cu5_invalid_precedence_ordering_fails_validation() -> None:
    runtime_lineage = [
        {
            "event_kind": "mutation",
            "owner": "game.runtime_lineage_telemetry",
            "mutation_kind": "runtime_mutation",
        }
    ]
    validation = validate_semantic_mutation_contract(
        fem={"semantic_mutation_write_sites": [_selected_write_site()]},
        runtime_lineage=runtime_lineage,
        projected_attribution={
            "authoritative_mutation_owner": "game.runtime_lineage_telemetry",
            "authoritative_mutation_family": "runtime_mutation",
            "authoritative_evidence_source": "runtime_lineage",
            "authoritative_mutation_confidence": "medium",
            "used_projection_inference": False,
        },
    )

    assert "invalid_precedence" in _error_codes(validation)
    assert "authoritative_owner_mismatch" in _error_codes(validation)


def test_cu5_malformed_attribution_metadata_is_diagnostic_not_runtime_failure() -> None:
    validation = validate_semantic_mutation_contract(
        fem={"semantic_mutation_write_sites": "legacy-not-a-list"},
        projected_attribution={"authoritative_evidence_source": "projection_inference"},
    )

    assert validation["valid"] is False
    assert validation["warnings"][0]["code"] == "malformed_write_sites"
    assert "invalid_precedence" in _error_codes(validation)


def test_cu5_replay_projection_authoritative_fields_match_reconciliation_and_remain_optional() -> None:
    write_site = _selected_write_site()
    observed = project_turn_observation(
        minimal_turn_payload(
            scenario_id="cu5_replay_governance",
            gm_text="The road bends toward the gate.",
            fem_meta={"semantic_mutation_write_sites": [write_site]},
            semantic_mutation_trace=_projection_trace(),
        )
    )

    validation = validate_semantic_mutation_contract(
        fem={"semantic_mutation_write_sites": [write_site]},
        projection_metadata=observed,
        projected_attribution=observed,
    )

    assert validation["valid"] is True
    assert observed["authoritative_mutation_owner"] == "game.fallback_provenance_debug"
    assert observed["authoritative_mutation_family"] == "fallback"
    assert observed["authoritative_evidence_source"] == "write_site"
    assert "authoritative_mutation_owner" not in protected_observation_field_paths()
    assert "semantic_mutation_write_sites" not in protected_observation_field_paths()


def test_cu5_classifier_preserves_routing_while_improving_attribution_evidence() -> None:
    observed = {
        "authoritative_mutation_owner": "game.fallback_provenance_debug",
        "authoritative_mutation_family": "fallback",
        "authoritative_write_site": "game/fallback_provenance_debug.py:finalize_upstream_fallback_overwrite_containment",
        "authoritative_evidence_source": "write_site",
        "authoritative_mutation_confidence": "high",
        "used_projection_inference": False,
    }
    rows = classify_replay_failure(
        scenario_id="cu5_classifier_governance",
        turn_index=0,
        observed_turn=observed,
        drift_rows=[
            {
                "field_path": "final_text",
                "expected": "before",
                "actual": "after",
                "reason": "semantic text changed",
                "drift_bucket": "semantic_drift",
                "replay_tags": ["semantic_drift"],
            }
        ],
    )
    row = rows[0]

    assert row["category"] == "semantic_mutation"
    assert row["severity"] == "critical"
    assert row["investigate_first"] == "game/stage_diff_telemetry.py"
    assert row["authoritative_mutation_owner"] == "game.fallback_provenance_debug"
    assert row["authoritative_evidence_source"] == "write_site"
    assert validate_failure_classification_row(row) == []


def test_cu5_dashboard_labels_inferred_attribution_and_never_promotes_candidate_only() -> None:
    candidate_only_observed = {
        "semantic_mutation_write_sites": [
            _selected_write_site(
                owner="game.upstream_response_repairs",
                selected_active_stream=False,
                candidate_only=True,
            )
        ],
        "first_semantic_mutation_bucket": "sanitizer",
        "first_semantic_mutation_source": "projected.sanitizer",
        "first_semantic_mutation_owner": "game.output_sanitizer",
    }
    rows = classify_replay_failure(
        scenario_id="cu5_dashboard_governance",
        turn_index=0,
        observed_turn=candidate_only_observed,
        drift_rows=[
            {
                "field_path": "final_text",
                "expected": "before",
                "actual": "after",
                "reason": "semantic text changed",
                "drift_bucket": "semantic_drift",
                "replay_tags": ["semantic_drift"],
            }
        ],
    )
    report = render_failure_dashboard_markdown(
        rows,
        generated_at="2026-06-28T00:00:00Z",
        command_used="pytest cu5",
    )

    assert rows[0]["authoritative_mutation_owner"] == "game.output_sanitizer"
    assert rows[0]["authoritative_evidence_source"] == "projection_inference"
    assert rows[0]["used_projection_inference"] is True
    assert "authoritative_evidence=projection_inference" in report
    assert "projection_inference=True" in report
    assert "authoritative_owner=game.upstream_response_repairs" not in report
