"""Contract metadata registry for planner/prompt projection schemas.

This module defines canonical key sets for public prompt-facing artifacts (e.g. the
planner's narrative plan projection shipped in the prompt). It is **metadata only**:
it does not build, validate, repair, or derive any runtime artifacts.

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


def public_narrative_plan_prompt_top_keys() -> frozenset[str]:
    """Return canonical top-level keys for the prompt narrative plan projection."""

    return PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS

