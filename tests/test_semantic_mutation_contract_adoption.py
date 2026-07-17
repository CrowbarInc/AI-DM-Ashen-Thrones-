"""CU6 semantic mutation attribution contract adoption locks."""
from __future__ import annotations

import inspect

import pytest

import game.final_emission_meta as final_emission_meta
import game.runtime_lineage_telemetry as runtime_lineage_telemetry
import tests.helpers.failure_classifier as failure_classifier
import tests.helpers.golden_replay_projection as golden_replay_projection
from game.semantic_mutation_attribution import (
    SEMANTIC_MUTATION_WRITE_SITE_FAMILIES,
    reconcile_semantic_mutation_owner,
    validate_semantic_mutation_contract,
)
from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.failure_dashboard_report import render_failure_dashboard_markdown
from tests.helpers.golden_replay_fixtures import minimal_turn_payload
from tests.helpers.golden_replay_projection import project_turn_observation

pytestmark = pytest.mark.unit


def _selected_write_site() -> dict[str, object]:
    return {
        "write_site_family": "policy",
        "write_site_file": "game/response_policy_enforcement.py",
        "write_site_function": "_apply_diegetic_validator_voice_enforcement",
        "owner": "game.response_policy_enforcement",
        "selected_active_stream": True,
        "candidate_only": False,
        "before_semantic_hash": "before",
        "after_semantic_hash": "after",
    }


def _semantic_drift_row() -> dict[str, object]:
    return {
        "field_path": "final_text",
        "expected": "before",
        "actual": "after",
        "reason": "semantic text changed",
        "drift_bucket": "semantic_drift",
        "replay_tags": ["semantic_drift"],
    }


def test_cu6_major_consumers_call_governed_reconciliation_helper() -> None:
    consumer_sources = {
        "golden_replay_projection.project_turn_observation": inspect.getsource(
            golden_replay_projection.project_turn_observation
        ),
        "failure_classifier._authoritative_mutation_attribution": inspect.getsource(
            failure_classifier._authoritative_mutation_attribution
        ),
        "runtime_lineage_telemetry.summarize_runtime_lineage_events": inspect.getsource(
            runtime_lineage_telemetry.summarize_runtime_lineage_events
        ),
    }

    for source in consumer_sources.values():
        assert "reconcile_semantic_mutation_owner(" in source


def test_cu6_write_site_family_allowlist_is_contract_sourced() -> None:
    assert final_emission_meta.SEMANTIC_MUTATION_WRITE_SITE_FAMILIES is SEMANTIC_MUTATION_WRITE_SITE_FAMILIES
    source = inspect.getsource(final_emission_meta)
    assert "SEMANTIC_MUTATION_WRITE_SITE_FAMILIES: frozenset" not in source


def test_cu6_replay_write_site_selection_uses_contract_wrapper_not_local_filtering() -> None:
    source = inspect.getsource(golden_replay_projection.project_turn_observation)

    assert "selected_semantic_mutation_write_site(" in source
    assert "semantic_mutation_write_site_label(" in source
    assert "row.get(\"candidate_only\") is not True" not in source


def test_cu6_legacy_minimal_partial_and_candidate_only_payloads_still_reconcile() -> None:
    assert reconcile_semantic_mutation_owner(fem={}).authoritative_evidence_source is None
    assert reconcile_semantic_mutation_owner(
        fem={"semantic_mutation_write_sites": "legacy-not-a-list"}
    ).authoritative_evidence_source is None

    partial = reconcile_semantic_mutation_owner(
        fem={
            "semantic_mutation_write_sites": [
                {
                    "write_site_family": "repair",
                    "write_site_file": "game/upstream_response_repairs.py",
                    "selected_active_stream": True,
                    "candidate_only": False,
                }
            ]
        }
    )
    assert partial.authoritative_mutation_owner == "game/upstream_response_repairs.py"
    assert partial.authoritative_mutation_family == "repair"

    candidate_only = reconcile_semantic_mutation_owner(
        fem={
            "semantic_mutation_write_sites": [
                {
                    "write_site_family": "prompt",
                    "owner": "game.upstream_response_repairs",
                    "selected_active_stream": False,
                    "candidate_only": True,
                }
            ]
        },
        projection_metadata={
            "first_semantic_mutation_bucket": "sanitizer",
            "first_semantic_mutation_source": "projected.sanitizer",
            "first_semantic_mutation_owner": "game.output_sanitizer",
        },
    )
    assert candidate_only.authoritative_mutation_owner == "game.output_sanitizer"
    assert candidate_only.authoritative_evidence_source == "projection_inference"


def test_cu6_validator_tolerates_partial_metadata_without_runtime_failure() -> None:
    diagnostics = validate_semantic_mutation_contract(
        fem={
            "semantic_mutation_write_sites": [
                {
                    "write_site_family": "repair",
                    "write_site_file": "game/upstream_response_repairs.py",
                    "selected_active_stream": "yes",
                    "candidate_only": False,
                }
            ]
        }
    )

    assert diagnostics["valid"] is True
    assert diagnostics["warnings"][0]["code"] == "malformed_selected_active_stream"
    assert diagnostics["expected_attribution"]["authoritative_evidence_source"] is None


def test_cu6_reporting_surfaces_agree_for_identical_write_site_evidence() -> None:
    write_site = _selected_write_site()
    observed = project_turn_observation(
        minimal_turn_payload(
            scenario_id="cu6_reporting_consistency",
            gm_text="The guard lowers their voice.",
            fem_meta={"semantic_mutation_write_sites": [write_site]},
        )
    )
    classifier_row = classify_replay_failure(
        scenario_id="cu6_reporting_consistency",
        turn_index=0,
        observed_turn=observed,
        drift_rows=[_semantic_drift_row()],
    )[0]
    report = render_failure_dashboard_markdown(
        [classifier_row],
        generated_at="2026-06-29T00:00:00Z",
        command_used="pytest cu6",
    )

    for key in (
        "authoritative_mutation_owner",
        "authoritative_mutation_family",
        "authoritative_write_site",
        "authoritative_evidence_source",
        "used_projection_inference",
    ):
        assert classifier_row[key] == observed[key]

    assert "authoritative_owner=game.response_policy_enforcement" in report
    assert "authoritative_family=policy" in report
    assert "authoritative_evidence=write_site" in report
    assert "projection_inference=False" in report


def test_cu6_runtime_lineage_reporting_uses_same_reconciliation_for_lineage_evidence() -> None:
    events = [
        runtime_lineage_telemetry.make_runtime_lineage_event(
            event_kind="mutation",
            stage="gate",
            owner="game.final_emission_gate",
            mutation_kind="fallback_mutation",
        )
    ]
    summary = runtime_lineage_telemetry.summarize_runtime_lineage_events(events)
    reconciled = reconcile_semantic_mutation_owner(runtime_lineage=events)

    assert summary["first_mutation_owner"] == reconciled.authoritative_mutation_owner
    assert summary["first_mutation_family"] == reconciled.authoritative_mutation_family
    assert summary["first_mutation_evidence_type"] == reconciled.authoritative_evidence_source
    assert summary["first_mutation_inference_used"] == reconciled.used_projection_inference
