"""Contract tests for ``game.ui_mode_policy`` (Objective #15 foundation)."""

from __future__ import annotations

import pytest

from game.state_channels import AUTHOR_CHANNEL, DEBUG_CHANNEL, PUBLIC_CHANNEL
from game.ui_mode_policy import (
    AUTHOR_UI_MODE,
    DEBUG_UI_MODE,
    PLAYER_UI_MODE,
    TAB_CAMPAIGN,
    TAB_CHARACTER,
    TAB_DEBUG,
    TAB_PLAY,
    TAB_SCENE,
    TAB_WORLD,
    UiModePolicyError,
    allowed_state_channels_for_mode,
    assert_mode_allows_author_read,
    assert_mode_allows_author_write,
    assert_mode_allows_debug_read,
    assert_mode_allows_runtime_action,
    visible_tabs_for_mode,
)


def test_mode_to_allowed_state_channels_is_explicit_and_separated() -> None:
    assert allowed_state_channels_for_mode(PLAYER_UI_MODE) == frozenset({PUBLIC_CHANNEL})
    assert allowed_state_channels_for_mode(AUTHOR_UI_MODE) == frozenset({PUBLIC_CHANNEL, AUTHOR_CHANNEL})
    assert allowed_state_channels_for_mode(DEBUG_UI_MODE) == frozenset({PUBLIC_CHANNEL, DEBUG_CHANNEL})

    # Ensure author and debug are distinct, not interchangeable.
    assert AUTHOR_CHANNEL not in allowed_state_channels_for_mode(DEBUG_UI_MODE)
    assert DEBUG_CHANNEL not in allowed_state_channels_for_mode(AUTHOR_UI_MODE)


def test_mode_to_visible_tabs_is_deterministic() -> None:
    assert visible_tabs_for_mode(PLAYER_UI_MODE) == (TAB_PLAY, TAB_CHARACTER, TAB_WORLD)
    assert visible_tabs_for_mode(AUTHOR_UI_MODE) == (TAB_SCENE, TAB_CAMPAIGN, TAB_WORLD)
    assert visible_tabs_for_mode(DEBUG_UI_MODE) == (TAB_DEBUG,)


def test_player_mode_cannot_access_author_or_debug_capabilities() -> None:
    with pytest.raises(UiModePolicyError):
        assert_mode_allows_author_read(PLAYER_UI_MODE)
    with pytest.raises(UiModePolicyError):
        assert_mode_allows_author_write(PLAYER_UI_MODE)
    with pytest.raises(UiModePolicyError):
        assert_mode_allows_debug_read(PLAYER_UI_MODE)


def test_author_mode_allows_author_reads_and_writes_but_not_debug_or_runtime_actions() -> None:
    assert_mode_allows_author_read(AUTHOR_UI_MODE)
    assert_mode_allows_author_write(AUTHOR_UI_MODE)

    with pytest.raises(UiModePolicyError):
        assert_mode_allows_debug_read(AUTHOR_UI_MODE)
    with pytest.raises(UiModePolicyError):
        assert_mode_allows_runtime_action(AUTHOR_UI_MODE)


def test_debug_mode_allows_debug_reads_but_not_author_or_runtime_actions() -> None:
    assert_mode_allows_debug_read(DEBUG_UI_MODE)

    with pytest.raises(UiModePolicyError):
        assert_mode_allows_author_read(DEBUG_UI_MODE)
    with pytest.raises(UiModePolicyError):
        assert_mode_allows_author_write(DEBUG_UI_MODE)
    with pytest.raises(UiModePolicyError):
        assert_mode_allows_runtime_action(DEBUG_UI_MODE)


def test_fail_closed_on_unknown_mode() -> None:
    with pytest.raises(UiModePolicyError):
        allowed_state_channels_for_mode("unknown")
    with pytest.raises(UiModePolicyError):
        visible_tabs_for_mode("unknown")
    with pytest.raises(UiModePolicyError):
        assert_mode_allows_runtime_action("unknown")

