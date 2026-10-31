"""Contract metadata registry for planner/prompt projection schemas.

This module defines canonical key sets for public prompt-facing artifacts (e.g. the
planner's narrative plan projection shipped in the prompt). It is **metadata only**:
it does not build, validate, repair, or derive any runtime artifacts.

It also lists canonical **emergency / deterministic strict-social fallback** telemetry
identifiers (``final_emitted_source`` and ``fallback_kind`` string values) discovered
in emission code paths. It does **not** build fallback text, select fallbacks, or
import gate/social emission modules.

The goal is to prevent schema drift between planner/projection code, audits, docs,
and tests by centralizing the expected contract key sets in a small leaf module.
"""

from __future__ import annotations

from typing import Final


# Top-level keys for the public prompt-facing narrative plan projection produced by:
# `game/narration_plan_bundle.py::public_narrative_plan_projection_for_prompt`
PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS: Final[frozenset[str]] = frozenset(
    {
        "version",
        "narrative_mode",
        "role_allocation",
        "scene_anchors",
        "active_pressures",
        "required_new_information",
        "allowable_entity_references",
        "narrative_roles",
        "narrative_mode_contract",
        "scene_opening",
        "action_outcome",
        "transition_node",
        "answer_exposition_plan",
    }
)

# ``final_emitted_source`` values used on strict-social / visibility paths that emit
# ``minimal_social_emergency_fallback_line`` or ``deterministic_social_fallback_line``
# (see ``game/final_emission_gate.py``, ``game/social_exchange_emission.py``).
EMERGENCY_FALLBACK_SOURCE_IDS: Final[frozenset[str]] = frozenset(
    {
        "deterministic_social_fallback",
        "minimal_social_emergency_fallback",
        "social_interlocutor_minimal_fallback",
    }
)

# ``fallback_kind`` values for the same strict-social deterministic / minimal pools
# (including kinds returned by ``deterministic_social_fallback_line``).
EMERGENCY_FALLBACK_KIND_IDS: Final[frozenset[str]] = frozenset(
    {
        "direct_answer_hint",
        "emergency_social_minimal",
        "explicit_ignorance",
        "interruption",
        "pressure_refusal",
        "refusal_evasion",
        "response_type_contract_social_emergency",
        "social_interlocutor_fallback",
        "visibility_minimal_social_fallback",
    }
)


def public_narrative_plan_prompt_top_keys() -> frozenset[str]:
    """Return canonical top-level keys for the prompt narrative plan projection."""

    return PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS


def emergency_fallback_source_ids() -> frozenset[str]:
    """Return canonical ``final_emitted_source`` IDs for emergency/deterministic social fallbacks."""

    return EMERGENCY_FALLBACK_SOURCE_IDS


def emergency_fallback_kind_ids() -> frozenset[str]:
    """Return canonical ``fallback_kind`` IDs for emergency/deterministic social fallbacks."""

    return EMERGENCY_FALLBACK_KIND_IDS

