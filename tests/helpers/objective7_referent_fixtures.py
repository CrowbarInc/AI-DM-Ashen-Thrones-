"""JSON-safe stubs for Objective #7 referent seam tests (derivative fixtures only).

These dicts exercise ``validate_referent_clarity`` / emission-layer wiring; they are
not authoritative copies of live ``build_referent_tracking_artifact`` output unless
constructed by that builder in the test itself.
"""
from __future__ import annotations

from typing import Any

# Contract: ``turn_packet["referent_tracking_compact"]`` must stay a four-key mirror.
REFERENT_TRACKING_COMPACT_KEYS = frozenset(
    {
        "referent_artifact_version",
        "active_interaction_target",
        "referential_ambiguity_class",
        "ambiguity_risk",
    }
)


def referent_compact_mirror(
    *,
    version: int = 1,
    active_interaction_target: str | None = "npc_gate",
    referential_ambiguity_class: str = "none",
    ambiguity_risk: int = 12,
) -> dict[str, Any]:
    return {
        "referent_artifact_version": version,
        "active_interaction_target": active_interaction_target,
        "referential_ambiguity_class": referential_ambiguity_class,
        "ambiguity_risk": ambiguity_risk,
    }


def minimal_full_referent_artifact(**overrides: Any) -> dict[str, Any]:
    """Minimal mapping accepted as a *full* referent artifact by ``_is_full_referent_artifact``."""
    base: dict[str, Any] = {
        "version": 1,
        "referential_ambiguity_class": "none",
        "ambiguity_risk": 12,
        "active_interaction_target": "npc_gate",
        "active_entities": [
            {"entity_id": "npc_gate", "display_name": "Gate sergeant", "entity_kind": "npc", "roles": []},
        ],
        "active_entity_order": ["npc_gate"],
        "single_unambiguous_entity": {"entity_id": "npc_gate", "label": "Gate sergeant"},
        "allowed_named_references": [{"entity_id": "npc_gate", "display_name": "Gate sergeant"}],
        "safe_explicit_fallback_labels": [{"entity_id": "npc_gate", "safe_explicit_label": "Gate sergeant"}],
        "forbidden_or_unresolved_patterns": [],
        "pronoun_resolution": {
            "strategy": "explicit_structured",
            "buckets_by_entity": {"npc_gate": ["they_them"]},
            "explicit_sources": ["test"],
        },
        "interaction_target_continuity": {
            "prior_target_id": None,
            "current_target_id": "npc_gate",
            "signal_target_id": "npc_gate",
            "target_visible": True,
            "drift_detected": False,
            "signal_sources": [],
        },
        "continuity_subject": {"entity_id": "npc_gate", "display_name": "Gate sergeant", "source": "test"},
        "continuity_object": None,
        "debug": {
            "derivation_codes": [],
            "sources_used": [],
            "target_resolution_trace": [],
            "visible_entity_count": 1,
            "person_like_visible_count": 1,
            "memory_window_entity_ids": [],
            "conflicting_target_signals": False,
        },
    }
    base.update(overrides)
    return base
