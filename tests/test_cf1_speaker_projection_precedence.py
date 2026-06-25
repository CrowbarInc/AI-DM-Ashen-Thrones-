"""CF1 — table-driven contracts for acceptance speaker projection precedence.

Locks ``_resolve_selected_speaker_id`` and ``read_final_speaker_observation_for_replay``
without exercising full ``project_turn_observation`` assembly.
"""
from __future__ import annotations

import pytest

from tests.helpers.golden_replay_projection_speaker import (
    _resolve_selected_speaker_id,
    read_final_speaker_observation_for_replay,
)

pytestmark = pytest.mark.unit


# --- Selected speaker ID precedence (trace → transcript → resolution.social) ---


@pytest.mark.parametrize(
    "trace,snap,social,expected_id,expected_source",
    [
        pytest.param(
            {"final_reply_owner": "npc_guard"},
            {},
            {},
            "npc_guard",
            "turn_trace.social_contract_trace",
            id="trace_final_reply_owner_wins",
        ),
        pytest.param(
            {"final_reply_owner": None, "reply_owner_actor_id": "npc_merchant"},
            {"interaction_context": {"active_interaction_target_id": "npc_other"}},
            {},
            "npc_merchant",
            "turn_trace.social_contract_trace",
            id="trace_reply_owner_when_final_reply_owner_null",
        ),
        pytest.param(
            {"reply_owner_actor_id": None, "visible_grounded_speaker": "npc_scribe"},
            {},
            {},
            "npc_scribe",
            "turn_trace.social_contract_trace",
            id="trace_visible_grounded_speaker_third",
        ),
        pytest.param(
            {},
            {"interaction_context": {"active_interaction_target_id": "npc_from_snap"}},
            {"npc_id": "npc_resolution"},
            "npc_from_snap",
            "interaction_context.active_interaction_target_id",
            id="transcript_target_when_trace_empty",
        ),
        pytest.param(
            {},
            {},
            {"npc_id": "npc_resolution_only"},
            "npc_resolution_only",
            "resolution.social.npc_id",
            id="resolution_social_npc_id_last_resort",
        ),
        pytest.param({}, {}, {}, None, None, id="all_sources_absent"),
        pytest.param(
            {"final_reply_owner": "trace_winner", "reply_owner_actor_id": "trace_loser"},
            {"interaction_context": {"active_interaction_target_id": "snap_loser"}},
            {"npc_id": "resolution_loser"},
            "trace_winner",
            "turn_trace.social_contract_trace",
            id="conflicting_trace_beats_snap_and_resolution",
        ),
        pytest.param(
            {"final_reply_owner": ""},
            {"interaction_context": {"active_interaction_target_id": "npc_snap"}},
            {},
            "",
            None,
            id="empty_string_trace_id_present_but_source_label_falsy",
        ),
    ],
)
def test_resolve_selected_speaker_id_precedence_matrix(
    trace: dict[str, object],
    snap: dict[str, object],
    social: dict[str, object],
    expected_id: object,
    expected_source: str | None,
) -> None:
    speaker_id, speaker_source = _resolve_selected_speaker_id(
        social_contract_trace=trace,
        snap=snap,
        social=social,
    )
    assert speaker_id == expected_id
    assert speaker_source == expected_source


# --- Final speaker observation read precedence (lane → gm_output → payload) ---


def _fso(status: str, speaker_id: str) -> dict[str, object]:
    return {"status": status, "canonical_speaker_id": speaker_id, "candidates": []}


def _gm_output_with_fso(obs: dict[str, object]) -> dict[str, object]:
    return {"metadata": {"emission_debug": {"final_speaker_observation": obs}}}


@pytest.mark.parametrize(
    "lane,payload,expected_speaker_id",
    [
        pytest.param(
            {"final_speaker_observation": _fso("resolved", "lane_npc")},
            {"gm_output": _gm_output_with_fso(_fso("resolved", "gm_npc"))},
            "lane_npc",
            id="emission_debug_lane_beats_gm_output",
        ),
        pytest.param(
            None,
            {"gm_output": _gm_output_with_fso(_fso("resolved", "gm_npc"))},
            "gm_npc",
            id="gm_output_metadata_when_lane_absent",
        ),
        pytest.param(
            None,
            _gm_output_with_fso(_fso("ambiguous", "payload_direct")),
            "payload_direct",
            id="payload_root_when_lane_and_gm_nested_absent",
        ),
        pytest.param(None, {}, None, id="all_sources_absent"),
        pytest.param(
            {"final_speaker_observation": "not_a_mapping"},
            {"gm_output": _gm_output_with_fso(_fso("resolved", "gm_npc"))},
            "gm_npc",
            id="malformed_lane_falls_through_to_gm_output",
        ),
        pytest.param(
            {"final_speaker_observation": None},
            {"gm_output": _gm_output_with_fso(_fso("unresolved", "gm_only"))},
            "gm_only",
            id="lane_null_falls_through",
        ),
    ],
)
def test_read_final_speaker_observation_for_replay_precedence_matrix(
    lane: dict[str, object] | None,
    payload: dict[str, object],
    expected_speaker_id: str | None,
) -> None:
    result = read_final_speaker_observation_for_replay(lane, payload=payload)
    if expected_speaker_id is None:
        assert result is None
    else:
        assert result is not None
        assert result.get("canonical_speaker_id") == expected_speaker_id
