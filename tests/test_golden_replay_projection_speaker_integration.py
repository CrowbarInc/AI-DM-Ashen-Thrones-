"""CF5 — speaker parity integration tests through canonical projection assembler."""
from __future__ import annotations

import pytest

from tests.helpers.golden_replay_projection import (
    project_speaker_projection_parity,
    project_turn_observation,
    read_final_speaker_observation_for_replay,
)
from tests.helpers.golden_replay_projection_test_support import speaker_parity_turn_payload

pytestmark = pytest.mark.unit


def test_bx3_speaker_projection_parity_resolved_aligned() -> None:
    observed = project_turn_observation(
        speaker_parity_turn_payload(
            scenario_id="bx3_parity_resolved_aligned",
            selected_speaker_id="guard_captain",
            final_speaker_observation={
                "status": "resolved",
                "canonical_speaker_id": "guard_captain",
                "candidates": [],
            },
        )
    )
    parity = observed["speaker_projection_parity"]
    assert parity["status"] == "aligned"
    assert parity["selected_speaker_id"] == "guard_captain"
    assert parity["final_observed_speaker_id"] == "guard_captain"
    assert observed["selected_speaker_id"] == "guard_captain"


def test_bx3_speaker_projection_parity_resolved_mismatch() -> None:
    observed = project_turn_observation(
        speaker_parity_turn_payload(
            scenario_id="bx3_parity_resolved_mismatch",
            selected_speaker_id="guard_captain",
            final_speaker_observation={
                "status": "resolved",
                "canonical_speaker_id": "gate_guard",
                "candidates": [],
            },
        )
    )
    parity = observed["speaker_projection_parity"]
    assert parity["status"] == "mismatch"
    assert parity["selected_speaker_id"] == "guard_captain"
    assert parity["final_observed_speaker_id"] == "gate_guard"
    assert observed["selected_speaker_id"] == "guard_captain"


def test_bx3_speaker_projection_parity_ambiguous_with_selected_candidate() -> None:
    observed = project_turn_observation(
        speaker_parity_turn_payload(
            scenario_id="bx3_parity_ambiguous_selected",
            selected_speaker_id="guard_captain",
            final_speaker_observation={
                "status": "ambiguous",
                "canonical_speaker_id": None,
                "candidates": ["guard_captain", "gate_sentry"],
                "notes": ["routing_unresolved_contract_primary_present"],
            },
        )
    )
    parity = observed["speaker_projection_parity"]
    assert parity["status"] == "final_ambiguous"
    assert parity["selected_speaker_id"] == "guard_captain"
    assert parity["final_observed_speaker_id"] is None
    assert parity["final_observed_status"] == "ambiguous"
    assert observed["selected_speaker_id"] == "guard_captain"
    assert "replay_selected_speaker_legacy_preserved" in parity["notes"]


def test_bx3_speaker_projection_parity_unresolved_final_observation() -> None:
    observed = project_turn_observation(
        speaker_parity_turn_payload(
            scenario_id="bx3_parity_unresolved",
            selected_speaker_id="guard_captain",
            final_speaker_observation={
                "status": "unresolved",
                "canonical_speaker_id": None,
                "candidates": [],
            },
        )
    )
    parity = observed["speaker_projection_parity"]
    assert parity["status"] == "final_unresolved"
    assert parity["final_observed_status"] == "unresolved"
    assert observed["selected_speaker_id"] == "guard_captain"


def test_bx3_speaker_projection_parity_missing_final_observation() -> None:
    observed = project_turn_observation(
        speaker_parity_turn_payload(
            scenario_id="bx3_parity_missing_stamp",
            selected_speaker_id="guard_captain",
            final_speaker_observation=None,
        )
    )
    parity = observed["speaker_projection_parity"]
    assert parity["status"] == "missing_final_observation"
    assert parity["final_observed_status"] is None
    assert observed["selected_speaker_id"] == "guard_captain"


def test_bx3_project_speaker_projection_parity_unit_surface() -> None:
    aligned = project_speaker_projection_parity(
        selected_speaker_id="runner",
        selected_speaker_source="turn_trace.social_contract_trace",
        emission_debug_lane={
            "final_speaker_observation": {
                "status": "resolved",
                "canonical_speaker_id": "runner",
            }
        },
    )
    assert aligned["status"] == "aligned"
    assert read_final_speaker_observation_for_replay({}) is None
