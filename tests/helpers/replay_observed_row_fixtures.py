"""Shared synthetic observed replay row factory (Cycle AO4).

Single authority for classifier probes, dashboard controlled failures, and
contract alignment helpers. Profiles preserve legacy default shapes from the
former ``observed_failure_row`` and ``failure_dashboard_fixtures._observed``.
"""
from __future__ import annotations

from typing import Any, Literal

from game.runtime_lineage_telemetry import make_runtime_lineage_event

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


def synthetic_rerun_turn(
    *,
    turn_index: int = 0,
    turn_id: str = "t01",
    route_kind: str | None = "dialogue",
    selected_speaker_id: str | None = "runner",
    fallback_family: str | None = None,
    fallback_owner: str | None = None,
    final_text: str = "The runner answers.",
    scaffold_leakage: bool | None = False,
    runtime_lineage_events: list[dict[str, Any]] | None = None,
    response_delta_checked: bool | None = None,
    response_delta_failed: bool | None = None,
    response_delta_repaired: bool | None = None,
    response_delta_kind: str | None = None,
    response_delta_echo_overlap_band: str | None = None,
) -> dict[str, Any]:
    """Synthetic observed turn for report-only rerun drift scorecard tests."""
    row: dict[str, Any] = {
        "turn_index": turn_index,
        "turn_id": turn_id,
        "route_kind": route_kind,
        "selected_speaker_id": selected_speaker_id,
        "fallback_family": fallback_family,
        "final_text": final_text,
        "runtime_lineage_events": list(runtime_lineage_events or []),
    }
    if fallback_owner is not None:
        row["sealed_fallback_owner_bucket"] = fallback_owner
    if scaffold_leakage is not None:
        row["scaffold_leakage"] = scaffold_leakage
    if response_delta_checked is not None:
        row["response_delta_checked"] = response_delta_checked
    if response_delta_failed is not None:
        row["response_delta_failed"] = response_delta_failed
    if response_delta_repaired is not None:
        row["response_delta_repaired"] = response_delta_repaired
    if response_delta_kind is not None:
        row["response_delta_kind"] = response_delta_kind
    if response_delta_echo_overlap_band is not None:
        row["response_delta_echo_overlap_band"] = response_delta_echo_overlap_band
    return row


def protected_speaker_failure_turn(
    *,
    include_replay_identity: bool = True,
    **overrides: Any,
) -> dict[str, Any]:
    """Canonical protected replay speaker-failure observed turn for dashboard reports."""
    row: dict[str, Any] = {
        "turn_index": 0,
        "source_path": "data/validation/scenario_spines/synthetic_fixture.json",
        "branch_id": "synthetic_branch",
        "turn_id": "synthetic_turn_01",
        "final_text": 'Gate Guard says, "No names."',
        "route_kind": "dialogue",
        "selected_speaker_id": "guard",
        "final_emitted_source": "generated_candidate",
        "fallback_family": None,
        "scaffold_leakage": False,
        "unavailable": [],
        "runtime_lineage_events": [
            make_runtime_lineage_event(
                event_kind="gate_outcome",
                stage="gate",
                owner="game.final_emission_gate",
                gate_path="accept_unchanged",
            )
        ],
        "trace": {
            "canonical_entry": {"target_actor_id": "runner"},
            "social_contract_trace": {"route_selected": "dialogue"},
        },
    }
    if not include_replay_identity:
        for key in ("source_path", "branch_id", "turn_id"):
            row.pop(key, None)
    row.update(overrides)
    return row
