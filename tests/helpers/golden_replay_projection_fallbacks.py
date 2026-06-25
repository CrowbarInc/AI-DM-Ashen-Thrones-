"""Golden replay fallback-family read-side projection (CE5)."""
from __future__ import annotations

from typing import Any, Mapping

from game.final_emission_replay_projection import is_sealed_replacement_lineage_kind
from game.realization_provenance import REALIZATION_FALLBACK_FAMILY_FIELD

from tests.helpers.golden_replay_projection_fields import _first_present

NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY = "neutral_reply_speaker_grounding_bridge"

# Read-side FEM key precedence for golden-replay observed ``fallback_family``.
# Diegetic/template taxonomy wins when present; governed provenance is fallback only.
REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS: tuple[str, ...] = (
    "fallback_family_used",
    REALIZATION_FALLBACK_FAMILY_FIELD,
)
def _project_replay_fallback_family(
    fem: Mapping[str, Any],
    runtime_lineage_events: list[Mapping[str, Any]],
) -> str | None:
    """Return read-side diagnostic family for finalized fallback evidence missing a family field."""
    final_route = str(fem.get("final_route") or "").strip().lower()
    final_source = str(fem.get("final_emitted_source") or "").strip()
    if final_route != "replaced" or final_source != NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY:
        return None
    if any(
        event.get("event_kind") == "fallback_selected"
        and is_sealed_replacement_lineage_kind(event.get("fallback_kind"))
        for event in runtime_lineage_events
        if isinstance(event, Mapping)
    ):
        return NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY
    return None


def dual_fallback_family_replay_precedence_surface() -> dict[str, object]:
    """Document read-side golden-replay precedence for dual FEM fallback-family fields.

    Diagnostic only: does not read live payloads or mutate FEM.
    """
    return {
        "precedence_keys": list(REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS),
        "prefer_field": "fallback_family_used",
        "fallback_field": REALIZATION_FALLBACK_FAMILY_FIELD,
        "projector": "project_replay_fallback_family_from_fem",
        "read_side_only": True,
    }


def project_replay_fallback_family_from_fem(fem: Mapping[str, Any]) -> str | None:
    """Project golden replay ``fallback_family`` from FEM with diegetic-first preference.

    Read-side only: prefers ``fallback_family_used`` (diegetic/template taxonomy)
    and uses ``realization_fallback_family`` (governed provenance) only when the
    diegetic key is absent or null. Returns ``None`` when neither field is present.
    See :func:`dual_fallback_family_replay_precedence_surface`.
    """
    return _first_present(fem, REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS)


def _fem_has_any_key(fem: Mapping[str, Any], keys: tuple[str, ...]) -> bool:
    return any(key in fem for key in keys)


def _fem_dual_fallback_family_present(fem: Mapping[str, Any]) -> bool:
    return _fem_has_any_key(fem, REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS)
def _resolve_fallback_family(
    fem: Mapping[str, Any],
    runtime_lineage_events: list[Mapping[str, Any]],
) -> Any:
    fallback_family = project_replay_fallback_family_from_fem(fem)
    if fallback_family is None:
        fallback_family = _project_replay_fallback_family(fem, runtime_lineage_events)
    return fallback_family
