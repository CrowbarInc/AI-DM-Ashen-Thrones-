"""UI mode separation contract (Objective #15 foundation).

This module defines the canonical, deterministic rules for separating UI surfaces into:

- player: gameplay-only surface (no author scaffolding, no debug telemetry)
- author: content authoring surface (may read author-only fields; not a runtime operator surface)
- debug: operator/diagnostic surface (may read debug telemetry; not an authoring transport)

Important boundary notes:

- **Boundary enforcement, not state ownership**: this module does not own or mutate game state.
  Ownership remains with existing engine/state modules. This policy is intended to be consumed
  by API/endpoint layers and frontends so they don't re-derive rules ad hoc.
- **Author tools must not directly mutate runtime state**: authoring is content editing; runtime
  changes should happen through explicit workflows, not "author mode" as a blanket capability.
- **Debug tooling is observational/diagnostic**: debug mode is for telemetry/traces; it should
  not become the transport for author-only editing state by accident.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable, Tuple

from game.state_channels import AUTHOR_CHANNEL, DEBUG_CHANNEL, PUBLIC_CHANNEL

PLAYER_UI_MODE = "player"
AUTHOR_UI_MODE = "author"
DEBUG_UI_MODE = "debug"


class UiModePolicyError(ValueError):
    """Raised when an unknown UI mode is provided or a forbidden capability is used."""


@dataclass(frozen=True, slots=True)
class UiModePolicy:
    """Deterministic policy for a UI mode.

    The fields here are intentionally simple "answers" that higher layers can enforce.
    """

    mode: str
    visible_tabs: Tuple[str, ...]
    allowed_state_channels: FrozenSet[str]

    # Capability flags. These are enforcement seams for later blocks/endpoints.
    may_write_author_data: bool
    may_read_author_data: bool
    may_read_debug_data: bool
    may_trigger_runtime_actions: bool


# Canonical tab ids currently used by the frontend shell (`static/index.html`).
TAB_PLAY = "play"
TAB_CHARACTER = "character"
TAB_SCENE = "scene"
TAB_CAMPAIGN = "campaign"
TAB_WORLD = "world"
TAB_DEBUG = "debug"


def _as_frozenset(items: Iterable[str]) -> FrozenSet[str]:
    return frozenset(items)


_POLICIES: dict[str, UiModePolicy] = {
    PLAYER_UI_MODE: UiModePolicy(
        mode=PLAYER_UI_MODE,
        visible_tabs=(TAB_PLAY, TAB_CHARACTER, TAB_WORLD),
        allowed_state_channels=_as_frozenset((PUBLIC_CHANNEL,)),
        may_write_author_data=False,
        may_read_author_data=False,
        may_read_debug_data=False,
        may_trigger_runtime_actions=True,
    ),
    AUTHOR_UI_MODE: UiModePolicy(
        mode=AUTHOR_UI_MODE,
        visible_tabs=(TAB_SCENE, TAB_CAMPAIGN, TAB_WORLD),
        allowed_state_channels=_as_frozenset((PUBLIC_CHANNEL, AUTHOR_CHANNEL)),
        may_write_author_data=True,
        may_read_author_data=True,
        may_read_debug_data=False,
        may_trigger_runtime_actions=False,
    ),
    DEBUG_UI_MODE: UiModePolicy(
        mode=DEBUG_UI_MODE,
        visible_tabs=(TAB_DEBUG,),
        allowed_state_channels=_as_frozenset((PUBLIC_CHANNEL, DEBUG_CHANNEL)),
        may_write_author_data=False,
        may_read_author_data=False,
        may_read_debug_data=True,
        may_trigger_runtime_actions=False,
    ),
}


def get_ui_mode_policy(mode: str) -> UiModePolicy:
    """Return the canonical policy for *mode*.

    Fail-closed: unknown modes raise :class:`UiModePolicyError`.
    """

    try:
        return _POLICIES[mode]
    except KeyError as e:
        raise UiModePolicyError(f"unknown ui mode: {mode!r}") from e


def allowed_state_channels_for_mode(mode: str) -> FrozenSet[str]:
    """Return allowed top-level state channels for *mode*.

    Intended boundary:
    - player -> public only
    - author -> public + author
    - debug  -> public + debug

    Author and debug are intentionally **not** interchangeable.
    """

    return get_ui_mode_policy(mode).allowed_state_channels


def visible_tabs_for_mode(mode: str) -> Tuple[str, ...]:
    """Return the tab ids that should be visible for *mode* (deterministic)."""

    return get_ui_mode_policy(mode).visible_tabs


def assert_mode_allows_author_write(mode: str) -> None:
    """Fail closed if *mode* may not write author data."""

    p = get_ui_mode_policy(mode)
    if not p.may_write_author_data:
        raise UiModePolicyError(f"ui mode {mode!r} may not write author data")


def assert_mode_allows_author_read(mode: str) -> None:
    """Fail closed if *mode* may not read author-only fields (e.g. hidden_facts)."""

    p = get_ui_mode_policy(mode)
    if not p.may_read_author_data:
        raise UiModePolicyError(f"ui mode {mode!r} may not read author data")


def assert_mode_allows_debug_read(mode: str) -> None:
    """Fail closed if *mode* may not read debug telemetry/traces."""

    p = get_ui_mode_policy(mode)
    if not p.may_read_debug_data:
        raise UiModePolicyError(f"ui mode {mode!r} may not read debug data")


def assert_mode_allows_runtime_action(mode: str) -> None:
    """Fail closed if *mode* may not trigger runtime-affecting actions."""

    p = get_ui_mode_policy(mode)
    if not p.may_trigger_runtime_actions:
        raise UiModePolicyError(f"ui mode {mode!r} may not trigger runtime actions")


__all__ = (
    "PLAYER_UI_MODE",
    "AUTHOR_UI_MODE",
    "DEBUG_UI_MODE",
    "UiModePolicy",
    "UiModePolicyError",
    "TAB_PLAY",
    "TAB_CHARACTER",
    "TAB_SCENE",
    "TAB_CAMPAIGN",
    "TAB_WORLD",
    "TAB_DEBUG",
    "get_ui_mode_policy",
    "allowed_state_channels_for_mode",
    "visible_tabs_for_mode",
    "assert_mode_allows_author_write",
    "assert_mode_allows_author_read",
    "assert_mode_allows_debug_read",
    "assert_mode_allows_runtime_action",
)

