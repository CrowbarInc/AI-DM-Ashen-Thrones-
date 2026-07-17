"""Long-session fallback lineage and escalation summary coverage."""
from __future__ import annotations

import pytest

from game.ownership_projection_views import (
    OPENING_FAIL_CLOSED_CONTENT_OWNER,
    OPENING_FALLBACK_CONTENT_OWNER,
    OPENING_FALLBACK_SELECTION_OWNER,
    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
    SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_TRACE_SELECTION_OWNER_SHORT,
    SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
    SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_FALLBACK_SELECTION_OWNER,
    SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
    STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    VISIBILITY_FALLBACK_SELECTION_OWNER,
)
from game.final_emission_replay_projection import (
    SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION,
    SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
    SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL,
    SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE,
    SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
    SEALED_REPLACEMENT_SUBKIND_UNKNOWN,
)

from game.attribution_read_views import (
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
)
from tests.helpers.opening_fallback_evidence import (
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
)
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.failure_classifier import validate_failure_classification_row
from tests.helpers.failure_classification_sync import (
    assert_split_owner_matrix_fem_projection,
    assert_split_owner_matrix_lineage_event,
    classify_replay_probe_row,
    exact_value_drift_row,
    project_split_owner_matrix_row,
    split_owner_acceptance_matrix_rows,
    split_owner_fem_projection_excluded,
    split_owner_lineage_event_from_matrix_row,
    split_owner_observed_row_from_matrix_row,
)
from tests.helpers.golden_replay_api import (
    NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
    classify_golden_drift,
    format_golden_replay_debug,
    summarize_long_session_replay_observations,
)
from tests.helpers.golden_replay_fixtures import (
    fem_payload,
    minimal_gm_output_payload,
    project_synthetic_turn,
)
from tests.helpers.opening_fallback_evidence import (
    fail_closed_opening_fem_meta,
    successful_opening_fem_meta,
)

from tests.helpers.golden_replay_fallback_projection_helpers import (
    fallback_selected_event as _fallback_selected_event,
    mutation_event as _mutation_event,
)


def test_long_session_summary_preserves_sanitizer_upstream_fast_split_owner_lineage_stability() -> None:
    turns = [
        project_synthetic_turn(
            scenario_id="streak_sanitizer_split",
            gm_text="Silence.",
            player_text="Wait.",
            resolution={"kind": "observe"},
            payload=minimal_gm_output_payload(
                fem_meta=fem_payload(
                    final_emitted_source="generated_candidate",
                    sanitizer_empty_fallback_used=True,
                    sanitizer_empty_fallback_source="upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                    sanitizer_empty_fallback_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
                ),
                metadata={
                    "sanitizer_trace": {
                        "sanitizer_empty_fallback_used": True,
                        "sanitizer_empty_fallback_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                    }
                },
            ),
        ),
        project_synthetic_turn(
            scenario_id="streak_upstream_fast_split",
            gm_text="The road holds.",
            player_text="Wait again.",
            resolution={"kind": "observe"},
            fem_meta=fem_payload(
                final_emitted_source="generated_candidate",
                fallback_provenance_trace={
                    "source": "fallback",
                    "stage": "fallback_selector",
                    "content_fingerprint": "def456",
                    "gate_exit_vs_selector_match": True,
                },
            ),
        ),
    ]

    for turn in turns:
        fallback = _fallback_selected_event(turn)
        assert fallback["fallback_selection_owner"] in {
            SANITIZER_FALLBACK_SELECTION_OWNER,
            UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
        }
        assert fallback["fallback_content_owner"] in {
            SANITIZER_FALLBACK_SELECTION_OWNER,
            UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
        }

    summary = summarize_long_session_replay_observations(turns)
    lineage = summary["lineage_summary"]
    assert lineage["fallback_selection_owner_frequency"] == {
        SANITIZER_FALLBACK_SELECTION_OWNER: 1,
        UPSTREAM_FAST_FALLBACK_SELECTION_OWNER: 1,
    }
    assert lineage["fallback_content_owner_frequency"] == {
        SANITIZER_FALLBACK_SELECTION_OWNER: 1,
        UPSTREAM_FAST_FALLBACK_CONTENT_OWNER: 1,
    }
    assert lineage["fallback_frequency"]["sanitizer_empty_output"] == 1
    assert lineage["fallback_frequency"]["upstream_fast_fallback"] == 1


def test_long_session_summary_preserves_opening_family_split_owner_lineage_stability() -> None:
    turns = [
        project_synthetic_turn(
            scenario_id="streak_opening_scene",
            gm_text="The road opens.",
            player_text="Begin.",
            resolution={"kind": "scene_opening"},
            fem_meta=successful_opening_fem_meta(
                response_type_repair_kind="opening_deterministic_fallback",
                fallback_temporal_frame="first_impression",
            ),
        ),
        project_synthetic_turn(
            scenario_id="streak_opening_failed_closed",
            gm_text="[opening_fallback_failed_closed:no_curated_facts]",
            player_text="Begin again.",
            resolution={"kind": "scene_opening"},
            fem_meta=fail_closed_opening_fem_meta(
                opening_recovered_via_fallback=True,
                fallback_family_used="scene_opening",
            ),
        ),
    ]

    for turn in turns:
        fallback = _fallback_selected_event(turn)
        assert fallback["fallback_selection_owner"] == OPENING_FALLBACK_SELECTION_OWNER
        assert fallback["fallback_content_owner"] in {
            OPENING_FALLBACK_CONTENT_OWNER,
            OPENING_FAIL_CLOSED_CONTENT_OWNER,
        }
        assert fallback["fallback_owner_bucket"] in {
            OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
            OPENING_FALLBACK_OWNER_SEALED_GATE,
        }

    summary = summarize_long_session_replay_observations(turns)
    lineage = summary["lineage_summary"]
    assert lineage["fallback_selection_owner_frequency"] == {OPENING_FALLBACK_SELECTION_OWNER: 2}
    assert lineage["fallback_content_owner_frequency"] == {
        OPENING_FALLBACK_CONTENT_OWNER: 1,
        OPENING_FAIL_CLOSED_CONTENT_OWNER: 1,
    }
    assert lineage["fallback_owner_bucket_frequency"] == {
        OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED: 1,
        OPENING_FALLBACK_OWNER_SEALED_GATE: 1,
    }
    assert lineage["fallback_frequency"]["scene_opening"] == 1
    assert lineage["fallback_frequency"]["opening_failed_closed"] == 1


def test_long_session_summary_preserves_sealed_family_split_owner_lineage_stability() -> None:
    turns = [
        project_synthetic_turn(
            scenario_id="streak_sealed_global_scene",
            gm_text="The scene holds.",
            player_text="Wait.",
            resolution={"kind": "observe"},
            fem_meta=fem_payload(
                final_route="replaced",
                final_emitted_source="global_scene_fallback",
                sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
                realization_fallback_family="gate_terminal_repair",
            ),
        ),
        project_synthetic_turn(
            scenario_id="streak_sealed_social_interlocutor",
            gm_text="The runner stays quiet.",
            player_text="Ask again.",
            resolution={"kind": "question"},
            fem_meta=fem_payload(
                final_route="replaced",
                final_emitted_source="social_interlocutor_minimal_fallback",
                sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
                realization_fallback_family="gate_terminal_repair",
            ),
        ),
        project_synthetic_turn(
            scenario_id="streak_sealed_unknown",
            gm_text="The road closes.",
            player_text="Leave.",
            resolution={"kind": "action"},
            fem_meta=fem_payload(
                final_route="replaced",
                final_emitted_source="unclassified_terminal_fallback",
                sealed_fallback_owner_bucket="unknown-none",
                realization_fallback_family="gate_terminal_repair",
            ),
        ),
    ]

    for turn in turns:
        fallback = _fallback_selected_event(turn)
        assert fallback["fallback_selection_owner"] == SEALED_FALLBACK_SELECTION_OWNER
        assert fallback["fallback_content_owner"] in {
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
            STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
            SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
        }
        assert fallback["fallback_owner_bucket"] in {
            SEALED_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
            "unknown-none",
        }

    summary = summarize_long_session_replay_observations(turns)
    lineage = summary["lineage_summary"]
    assert lineage["fallback_selection_owner_frequency"] == {SEALED_FALLBACK_SELECTION_OWNER: 3}
    assert lineage["fallback_content_owner_frequency"] == {
        SEALED_FALLBACK_MODULE_CONTENT_OWNER: 1,
        STRICT_SOCIAL_FALLBACK_CONTENT_OWNER: 1,
        SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER: 1,
    }
    assert lineage["fallback_owner_bucket_frequency"] == {
        SEALED_FALLBACK_OWNER_SEALED_GATE: 1,
        SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED: 1,
        "unknown-none": 1,
    }
    assert lineage["fallback_frequency"][SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE] == 1
    assert lineage["fallback_frequency"][SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR] == 1
    assert lineage["fallback_frequency"][SEALED_REPLACEMENT_SUBKIND_UNKNOWN] == 1


def test_long_session_summary_treats_scene_action_fallback_speaker_absence_as_optional():
    turns = [
        {
            "turn_index": 0,
            "route_kind": "undecided",
            "response_type_required": "neutral_narration",
            "final_emitted_source": NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            "fallback_family": NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            "unavailable": ["selected_speaker_id"],
            "runtime_lineage_events": [
                make_runtime_lineage_event(
                    event_kind="fallback_selected",
                    stage="gate",
                    owner="game.final_emission_gate",
                    fallback_kind="sealed_or_global_replacement",
                )
            ],
        },
        {
            "turn_index": 1,
            "route_kind": "action",
            "response_type_required": "action_outcome",
            "final_emitted_source": "anti_reset_local_continuation_fallback",
            "fallback_family": "gate_terminal_repair",
            "unavailable": ["selected_speaker_id"],
            "runtime_lineage_events": [
                make_runtime_lineage_event(
                    event_kind="fallback_selected",
                    stage="gate",
                    owner="game.final_emission_gate",
                    fallback_kind="response_type_prepared_emission",
                )
            ],
        },
    ]

    fallback_escalation = summarize_long_session_replay_observations(turns)["fallback_escalation_summary"]

    assert fallback_escalation["unavailable_with_fallback_count"] == 2
    assert fallback_escalation["scene_action_speaker_optional_unavailable_count"] == 2
    assert fallback_escalation["blocking_unavailable_with_fallback_count"] == 0
    assert fallback_escalation["max_fallback_streak"] == 2
    assert fallback_escalation["max_scene_action_nonblocking_fallback_streak"] == 2
    assert fallback_escalation["max_blocking_fallback_streak"] == 0
    assert "fallback_streak_gt_1" not in fallback_escalation["escalation_warnings"]
    assert "unavailable_to_fallback_coupling_recurrence" not in fallback_escalation["escalation_warnings"]
