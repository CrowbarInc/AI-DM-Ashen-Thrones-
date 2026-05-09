"""Lightweight helpers for realization fallback provenance metadata."""
from __future__ import annotations

from typing import Any, MutableMapping

from game.realization_authority import FALLBACK_FAMILIES

REALIZATION_FALLBACK_FAMILY_FIELD = "realization_fallback_family"

PLAN_BACKED_GPT_REALIZATION = "plan_backed_gpt_realization"
UPSTREAM_PREPARED_EMISSION = "upstream_prepared_emission"
STRICT_SOCIAL_DETERMINISTIC_FALLBACK = "strict_social_deterministic_fallback"
PLANNER_CONVERGENCE_SEAM_FAILURE = "planner_convergence_seam_failure"
GPT_BUDGET_OR_PROVIDER_FAILURE = "gpt_budget_or_provider_failure"
RETRY_TERMINAL_FALLBACK = "retry_terminal_fallback"
GATE_TERMINAL_REPAIR = "gate_terminal_repair"
LEGACY_DIEGETIC_FALLBACK = "legacy_diegetic_fallback"
LEGACY_UNCLASSIFIED = "legacy_unclassified"


def normalize_realization_fallback_family(value: str | None) -> str:
    """Return a known realization fallback family, defaulting ambiguous values to legacy_unclassified."""
    if value in FALLBACK_FAMILIES:
        return str(value)
    return LEGACY_UNCLASSIFIED


def attach_realization_fallback_family(meta: MutableMapping[str, Any], family: str) -> MutableMapping[str, Any]:
    """Attach normalized realization fallback family metadata in place and return *meta*."""
    meta[REALIZATION_FALLBACK_FAMILY_FIELD] = normalize_realization_fallback_family(family)
    return meta
