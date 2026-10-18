"""Thin assembler smoke tests for golden replay projection (CF5 split).

Focused ownership suites live alongside this module:

- ``test_golden_replay_projection_registry.py``
- ``test_golden_replay_projection_manifest.py``
- ``test_golden_replay_projection_governance.py``
- ``test_golden_replay_projection_fallback_integration.py``
- ``test_golden_replay_projection_speaker_integration.py``
- ``test_golden_replay_projection_presence_integration.py``
- ``test_golden_replay_projection_metadata.py``
- ``test_golden_replay_projection_modules.py`` (module boundary governance)
- ``test_cf1_*`` / ``test_cf2_*`` / ``test_cf3_*`` / ``test_cf4_*`` (contract matrices)
"""
from __future__ import annotations

import pytest
import json

from tests.helpers.golden_replay_api import observed_turn_from_payload
from tests.helpers.golden_replay_fixtures import fem_payload, minimal_turn_payload
from tests.helpers.golden_replay_projection import (
    project_turn_observation,
    protected_observation_drift_bucket,
    protected_observation_field_paths,
)

pytestmark = pytest.mark.unit


def test_missing_sanitizer_mode_is_json_safe():
    observed = project_turn_observation(minimal_turn_payload(scenario_id="missing_sanitizer", gm_text="Quiet."))
    assert observed["sanitizer_mode"] is None
    assert observed["sanitizer_lineage_mode"] is None
    assert observed["sanitizer_lineage_legacy_rewrite_active"] is None
    assert "object object at" not in json.dumps(observed)


@pytest.mark.parametrize("tamper", ["none", "text", "digest", "speaker", "hard_validation"])
def test_sealed_delivery_replay_retains_integrity_and_speaker_checks(tamper):
    from game.immutable_valid_response import seal_delivery_contract
    from tests.helpers.golden_replay import assert_golden_turn_observation, protected_social_speaker_observation_expectation

    payload = minimal_turn_payload(scenario_id="sealed_delivery", gm_text='Runner says, "Hello."')
    gm = payload["payload"].setdefault("gm_output", {})
    record = {"immutable": True, "text": payload["snap"]["gm_text"], "speaker_id": "runner", "hard_validation": {"hard_valid": True}}
    gm["metadata"] = {"accepted_response": record}
    seal_delivery_contract(gm)
    # Replay uses the API's exported accepted record after its internal seal is removed.
    gm.pop("_final_delivery_seal")
    if tamper == "text":
        payload["snap"]["gm_text"] = "Altered delivery."
    elif tamper == "digest":
        record["integrity_digest"] = "bad"
    elif tamper == "speaker":
        record["speaker_id"] = "merchant"
        seal_delivery_contract(gm)
        gm.pop("_final_delivery_seal")
    elif tamper == "hard_validation":
        record["hard_validation"]["hard_valid"] = False
        seal_delivery_contract(gm)
        gm.pop("_final_delivery_seal")
    observed = project_turn_observation(payload)
    observed["selected_speaker_id"] = "runner"
    observed["unavailable"] = ["fallback_family", "response_type_candidate_ok", "response_type_required", "response_type_repair_used"]
    expectation = protected_social_speaker_observation_expectation("runner", accepted_delivery=observed["accepted_delivery"])
    if tamper == "none":
        assert_golden_turn_observation(observed, expectation)
    else:
        with pytest.raises(AssertionError):
            assert_golden_turn_observation(observed, expectation)


def test_legacy_speaker_expectation_still_requires_gate_telemetry():
    from tests.helpers.golden_replay import assert_golden_turn_observation, protected_social_speaker_observation_expectation

    with pytest.raises(AssertionError, match="response_type_candidate_ok"):
        assert_golden_turn_observation(
            {"final_text": "Hello.", "selected_speaker_id": "runner", "unavailable": ["response_type_candidate_ok"]},
            protected_social_speaker_observation_expectation("runner"),
        )


def test_golden_replay_projection_adapter_wires_observed_turn():
    turn_payload = minimal_turn_payload(
        scenario_id="projection_adapter",
        gm_text="Rain falls on the gate road.",
        fem_meta=fem_payload(
            response_type_required="neutral_narration",
            final_emitted_source="upstream_prepared_emission",
        ),
    )
    via_adapter = project_turn_observation(turn_payload)
    via_wrapper = observed_turn_from_payload(
        scenario_id=str(turn_payload["scenario_id"]),
        snap=dict(turn_payload["snap"]),
        payload=dict(turn_payload["payload"]),
    )
    assert via_adapter == via_wrapper
    paths = protected_observation_field_paths()
    registry_paths = protected_observation_field_paths()
    assert protected_observation_field_paths() == registry_paths
    assert len(paths) == len(set(paths))
    assert protected_observation_drift_bucket("fallback_family") == "structural_drift"
    assert protected_observation_drift_bucket("scaffold_leakage") == "semantic_drift"
    assert "final_emitted_source" in paths
    assert "scaffold_leakage" in paths
    assert "route_kind" in paths
    assert paths == tuple(sorted(set(paths)))


def test_assembler_smoke_observed_turn_envelope():
    """Minimal end-to-end smoke: assembler returns required diagnostic envelope keys."""
    observed = project_turn_observation(
        minimal_turn_payload(
            scenario_id="assembler_smoke",
            gm_text="Smoke test.",
        )
    )
    for key in (
        "scenario_id",
        "final_text",
        "trace",
        "unavailable",
        "raw_signal_presence",
        "normalized_signal_presence",
        "missing_source_by_field",
        "fem_raw_keys",
        "fem_normalized_keys",
        "speaker_projection_parity",
    ):
        assert key in observed
    assert observed["scenario_id"] == "assembler_smoke"
    assert isinstance(observed["trace"], dict)
