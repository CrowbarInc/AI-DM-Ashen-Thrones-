"""Named long-session replay profiles consumed by golden replay tests.

These profiles are test fixtures for replay acceptance bands.  Stability
scorecard shape, owner-drift taxonomy, dashboard rendering, and lineage
reporting semantics are owned by their dedicated suites; golden replay only
passes these profiles into the shared assertion helper.
"""
from __future__ import annotations

from typing import Any

from tests.helpers.golden_replay_projection import (
    NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
    SEALED_REPLACEMENT_SUBKINDS,
)


FRONTIER_GATE_SOCIAL_INQUIRY_STABILITY_PROFILE: dict[str, Any] = {
    "result_turn_count": 25,
    "summary_equals": {"turn_count": 25},
    "no_scaffold_leakage": True,
    "summary_max": {
        "speaker_change_count": 2,
        "speaker_missing_count": 2,
        "fallback_turn_count": 1,
        "fallback_owner_change_count": 1,
        "route_change_count": 2,
    },
    "min_resolved_routes": 12,
    "session_health": {
        "equals": {"long_session_band": "long", "overall_passed": True},
        "classification_in": {"clean", "warning"},
    },
    "degradation": {
        "equals": {"progressive_degradation_detected": False},
        "absent_reason_codes": {
            "late_session_reset_or_amnesia",
            "rising_generic_filler_strong",
            "rising_generic_filler_progressive",
            "debug_leak_late_window",
            "referent_loss_late",
            "continuity_anchor_late_loss",
        },
    },
    "continuity_axes_passed": {"narrative_grounding", "branch_coherence"},
}

FRONTIER_GATE_SOCIAL_INQUIRY_LINEAGE_PROFILE: dict[str, Any] = {
    "fallback_frequency_total_max": 1,
    "event_kind_max": {"fallback_selected": 1, "mutation": 25},
    "mutation_kind_max": {"fallback_mutation": 1, "final_emission_mutation": 25},
    "allowed_recurring_keys": {
        "gate_outcome:gate:game.final_emission_gate:strict_social_accept",
        "mutation:gate:game.final_emission_gate:final_emission_mutation",
    },
    "max_recurring_event_count": 25,
}

FRONTIER_GATE_SOCIAL_INQUIRY_FALLBACK_ESCALATION_PROFILE: dict[str, Any] = {
    "equals": {
        "late_window_fallback_count": 0,
        "fallback_owner_change_count": 0,
        "fallback_lineage_owner_change_count": 0,
        "fallback_behavior_repair_count": 0,
        "sanitizer_fallback_count": 0,
        "escalation_warnings": [],
        "model_routing_escalation_observable": False,
    },
    "max": {
        "fallback_total_count": 1,
        "max_fallback_streak": 1,
        "response_type_repair_count": 1,
        "unavailable_with_fallback_count": 1,
        "fallback_selected_without_family_count": 1,
    },
}

FRONTIER_GATE_RESUME_STABILITY_PROFILE: dict[str, Any] = {
    "result_turn_count": 25,
    "summary_equals": {"turn_count": 25},
    "no_scaffold_leakage": True,
    "summary_max": {
        "speaker_change_count": 2,
        "speaker_missing_count": 2,
        "fallback_turn_count": 1,
        "fallback_owner_change_count": 1,
        "route_change_count": 2,
    },
    "session_health": {
        "equals": {"long_session_band": "long", "overall_passed": True},
        "classification_in": {"clean", "warning"},
    },
    "degradation": {
        "equals": {"progressive_degradation_detected": False},
        "absent_reason_codes": {
            "late_session_reset_or_amnesia",
            "rising_generic_filler_strong",
            "rising_generic_filler_progressive",
            "debug_leak_late_window",
            "referent_loss_late",
            "continuity_anchor_late_loss",
        },
    },
    "continuity_axes_passed": {"narrative_grounding", "branch_coherence"},
}

FRONTIER_GATE_RESUME_LINEAGE_PROFILE: dict[str, Any] = {
    "event_kind_max": {"fallback_selected": 1, "mutation": 25},
    "mutation_kind_max": {"fallback_mutation": 1, "final_emission_mutation": 25},
    "allowed_recurring_keys": {
        "gate_outcome:gate:game.final_emission_gate:strict_social_accept",
        "mutation:gate:game.final_emission_gate:final_emission_mutation",
    },
    "max_recurring_event_count": 25,
}

FRONTIER_GATE_RESUME_FALLBACK_ESCALATION_PROFILE: dict[str, Any] = {
    "equals": {
        "late_window_fallback_count": 0,
        "fallback_owner_change_count": 0,
        "fallback_lineage_owner_change_count": 0,
        "fallback_behavior_repair_count": 0,
        "sanitizer_fallback_count": 0,
        "escalation_warnings": [],
        "model_routing_escalation_observable": False,
    },
    "max": {
        "fallback_total_count": 1,
        "max_fallback_streak": 1,
        "response_type_repair_count": 1,
        "unavailable_with_fallback_count": 1,
        "fallback_selected_without_family_count": 1,
    },
}

FRONTIER_GATE_DIRECT_INTRUSION_STABILITY_PROFILE: dict[str, Any] = {
    "result_turn_count": 25,
    "summary_equals": {
        "turn_count": 25,
        "fallback_turn_count": 7,
        "fallback_owner_change_count": 0,
    },
    "no_scaffold_leakage": True,
    "summary_max": {
        "route_change_count": 6,
        "speaker_change_count": 3,
        "speaker_missing_count": 20,
        "mutation_turn_count": 25,
    },
    "session_health": {
        "equals": {"long_session_band": "long", "overall_passed": True},
        "classification_in": {"clean", "warning"},
    },
    "degradation": {
        "equals": {"progressive_degradation_detected": False},
        "absent_reason_codes": {
            "late_session_reset_or_amnesia",
            "rising_generic_filler_strong",
            "rising_generic_filler_progressive",
            "debug_leak_late_window",
            "referent_loss_late",
            "continuity_anchor_late_loss",
        },
    },
    "continuity_axes_passed": {"narrative_grounding", "branch_coherence"},
}

FRONTIER_GATE_DIRECT_INTRUSION_LINEAGE_PROFILE: dict[str, Any] = {
    "event_kind_equals": {"fallback_selected": 7},
    "event_kind_max": {"mutation": 14, "speaker_repair": 1},
    "mutation_kind_max": {
        "fallback_mutation": 7,
        "final_emission_mutation": 4,
        "response_type_repair_mutation": 2,
        "speaker_repair_mutation": 1,
    },
    "allowed_recurring_keys": {
        "gate_outcome:gate:game.final_emission_gate:accept_unchanged",
        "mutation:gate:game.final_emission_gate:fallback_mutation",
        "fallback_selected:gate:game.final_emission_gate:sealed_or_global_replacement",
        "gate_outcome:gate:game.final_emission_gate:replaced_or_sealed",
        "gate_outcome:gate:game.final_emission_gate:strict_social_accept",
        "mutation:gate:game.final_emission_gate:final_emission_mutation",
        "fallback_selected:gate:game.final_emission_gate:response_type_prepared_emission",
        "gate_outcome:gate:game.final_emission_gate:prepared_repair",
        "mutation:gate:game.final_emission_gate:response_type_repair_mutation",
    }
    | {
        f"fallback_selected:gate:game.final_emission_gate:{subkind}"
        for subkind in SEALED_REPLACEMENT_SUBKINDS
    },
    "max_recurring_event_count": 25,
}

FRONTIER_GATE_DIRECT_INTRUSION_FALLBACK_ESCALATION_PROFILE: dict[str, Any] = {
    "equals": {
        "fallback_total_count": 7,
        "max_blocking_fallback_streak": 0,
        "fallback_owner_change_count": 0,
        "fallback_lineage_owner_change_count": 0,
        "fallback_behavior_repair_count": 0,
        "sanitizer_fallback_count": 0,
        "scene_action_speaker_optional_unavailable_count": 7,
        "blocking_unavailable_with_fallback_count": 0,
        "fallback_selected_without_family_count": 0,
        "escalation_warnings": [],
        "model_routing_escalation_observable": False,
    },
    "max": {
        "max_fallback_streak": 2,
        "max_scene_action_nonblocking_fallback_streak": 2,
        "late_window_fallback_count": 2,
        "response_type_repair_count": 2,
        "unavailable_with_fallback_count": 7,
    },
    "allowed_fallback_families": {
        NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
        "gate_terminal_repair",
    },
    "fallback_family_counts": {
        NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY: 4,
        "gate_terminal_repair": 3,
    },
}
