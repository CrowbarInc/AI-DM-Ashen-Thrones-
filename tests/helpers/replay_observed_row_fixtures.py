"""Shared synthetic observed replay row factory (Cycle AO4).

Single authority for classifier probes, dashboard controlled failures, and
contract alignment helpers. Profiles preserve legacy default shapes from the
former ``observed_failure_row`` and ``failure_dashboard_fixtures._observed``.
"""
from __future__ import annotations

from typing import Any, Literal

SyntheticObservedRowProfile = Literal["classifier_probe", "dashboard_probe"]

_CLASSIFIER_PROBE_DEFAULTS: dict[str, Any] = {
    "scenario_id": "probe",
    "final_text_hash": "hash123",
}

_DASHBOARD_PROBE_DEFAULTS: dict[str, Any] = {
    "scenario_id": "controlled_probe",
    "final_text_hash": "probehash",
    "raw_signal_presence": {},
    "normalized_signal_presence": {},
}


def _base_synthetic_observed_replay_row() -> dict[str, Any]:
    """Return the shared observed-row baseline before profile defaults/overrides."""
    return {
        "scenario_id": "probe",
        "turn_index": 0,
        "final_text": "The runner answers.",
        "final_text_hash": "hash123",
        "route_kind": "dialogue",
        "selected_speaker_id": "runner",
        "final_emitted_source": "generated_candidate",
        "fallback_family": None,
        "fallback_temporal_frame": None,
        "opening_fallback_owner_bucket": None,
        "sealed_fallback_owner_bucket": None,
        "visibility_fallback_owner_bucket": None,
        "visibility_replacement_applied": None,
        "visibility_fallback_pool": None,
        "visibility_fallback_kind": None,
        "response_type_required": "dialogue_response",
        "response_type_repair_used": False,
        "response_type_repair_kind": None,
        "post_gate_mutation_detected": False,
        "strict_social_active": False,
        "speaker_contract_enforcement_reason": None,
        "fallback_behavior_repaired": False,
        "fallback_behavior_repair_kind": None,
        "sanitizer_mode": None,
        "sanitizer_event_count": None,
        "sanitizer_changed_count": None,
        "sanitizer_rewrite_used": None,
        "unavailable": [],
        "trace": {
            "canonical_entry": {"target_actor_id": "runner"},
            "social_contract_trace": {"route_selected": "dialogue"},
        },
    }


def synthetic_observed_replay_row(
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
    **overrides: Any,
) -> dict[str, Any]:
    """Return a synthetic observed replay row for classifier/dashboard probes."""
    row = _base_synthetic_observed_replay_row()
    if profile == "dashboard_probe":
        row.update(_DASHBOARD_PROBE_DEFAULTS)
    else:
        row.update(_CLASSIFIER_PROBE_DEFAULTS)
    row.update(overrides)
    return row


def observed_failure_row(**overrides: Any) -> dict[str, Any]:
    """Classifier-shaped synthetic observed replay row (legacy ``observed_failure_row``)."""
    return synthetic_observed_replay_row(profile="classifier_probe", **overrides)


def observed_dashboard_probe_row(**overrides: Any) -> dict[str, Any]:
    """Dashboard controlled-probe synthetic observed replay row (legacy ``_observed``)."""
    return synthetic_observed_replay_row(profile="dashboard_probe", **overrides)
