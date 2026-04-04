"""Unit tests for synthetic policy (harness only)."""
from __future__ import annotations

import pytest

from tests.helpers.synthetic_policy import decide_placeholder
from tests.helpers.synthetic_profiles import (
    profile_adversarial_rules_poker,
    profile_arcane_examiner,
    profile_bold_opportunist,
    profile_cautious_investigator,
    profile_social_prober,
)
from tests.helpers.synthetic_types import SyntheticDecision, SyntheticProfile, SyntheticTurnView

pytestmark = [pytest.mark.unit, pytest.mark.synthetic]

_PROFILES: tuple[SyntheticProfile, ...] = (
    profile_cautious_investigator(),
    profile_social_prober(),
    profile_arcane_examiner(),
    profile_bold_opportunist(),
    profile_adversarial_rules_poker(),
)


def test_decide_placeholder_returns_decision():
    view = SyntheticTurnView(turn_index=0, player_text_history=(), seed=1, profile=profile_cautious_investigator())
    out = decide_placeholder(view)
    assert isinstance(out, SyntheticDecision)
    assert out.player_text.strip()
    assert out.rationale.startswith("cautious_investigator:")


def test_determinism_fixed_seed_and_view():
    view = SyntheticTurnView(
        turn_index=3,
        player_text_history=("Earlier I checked the door.",),
        seed=404,
        profile=profile_social_prober(),
    )
    a = decide_placeholder(view)
    b = decide_placeholder(view)
    assert a.player_text == b.player_text
    assert a.rationale == b.rationale


def test_profiles_diverge_on_same_visible_context():
    base_kw = dict(turn_index=1, player_text_history=(), seed=99)
    texts = {
        decide_placeholder(SyntheticTurnView(**base_kw, profile=p)).player_text for p in _PROFILES
    }
    assert len(texts) == len(_PROFILES)


def test_player_text_never_whitespace_only():
    for seed in range(31):
        for profile in _PROFILES:
            view = SyntheticTurnView(
                turn_index=seed % 5,
                player_text_history=tuple(f"Prior line {i}." for i in range(seed % 3)),
                seed=seed,
                profile=profile,
            )
            out = decide_placeholder(view)
            assert out.player_text.strip()
            assert not out.player_text.isspace()


def test_snapshot_not_required():
    """Policy must not depend on snapshot or other internal-only view fields."""
    view = SyntheticTurnView(turn_index=0, player_text_history=(), seed=7, profile=profile_arcane_examiner())
    assert view.snapshot is None
    out = decide_placeholder(view)
    assert out.player_text.strip()


def test_repetition_avoids_immediate_duplicate_line():
    profile = profile_bold_opportunist()
    seed = 21
    first = decide_placeholder(
        SyntheticTurnView(turn_index=0, player_text_history=(), seed=seed, profile=profile)
    )
    second = decide_placeholder(
        SyntheticTurnView(
            turn_index=1,
            player_text_history=(first.player_text,),
            seed=seed,
            profile=profile,
        )
    )
    assert first.player_text.strip()
    assert second.player_text.strip()
    assert second.player_text != first.player_text
