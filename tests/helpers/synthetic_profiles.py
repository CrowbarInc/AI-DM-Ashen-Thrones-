"""Synthetic-player infrastructure for tests/tooling only. No production imports from this module."""

from __future__ import annotations

from dataclasses import replace

from tests.helpers.synthetic_types import SyntheticProfile


def profile_cautious_investigator() -> SyntheticProfile:
    return SyntheticProfile(
        profile_id="cautious_investigator",
        label="Cautious investigator",
        curiosity=0.85,
        risk_tolerance=0.22,
        social_bias=0.38,
        magic_bias=0.32,
        persistence=0.82,
        edge_case_bias=0.18,
        question_bias=0.78,
    )


def profile_social_prober() -> SyntheticProfile:
    return SyntheticProfile(
        profile_id="social_prober",
        label="Social prober",
        curiosity=0.55,
        risk_tolerance=0.48,
        social_bias=0.92,
        magic_bias=0.28,
        persistence=0.52,
        edge_case_bias=0.22,
        question_bias=0.88,
    )


def profile_arcane_examiner() -> SyntheticProfile:
    return SyntheticProfile(
        profile_id="arcane_examiner",
        label="Arcane examiner",
        curiosity=0.82,
        risk_tolerance=0.42,
        social_bias=0.32,
        magic_bias=0.96,
        persistence=0.72,
        edge_case_bias=0.52,
        question_bias=0.58,
    )


def profile_bold_opportunist() -> SyntheticProfile:
    return SyntheticProfile(
        profile_id="bold_opportunist",
        label="Bold opportunist",
        curiosity=0.44,
        risk_tolerance=0.92,
        social_bias=0.54,
        magic_bias=0.22,
        persistence=0.34,
        edge_case_bias=0.28,
        question_bias=0.32,
    )


def profile_adversarial_rules_poker() -> SyntheticProfile:
    return SyntheticProfile(
        profile_id="adversarial_rules_poker",
        label="Adversarial rules poker",
        curiosity=0.34,
        risk_tolerance=0.56,
        social_bias=0.28,
        magic_bias=0.18,
        persistence=0.4,
        edge_case_bias=0.96,
        question_bias=0.78,
    )


def default_placeholder_profile() -> SyntheticProfile:
    """Default harness profile: same tendencies as cautious_investigator, legacy id for runner tests."""
    base = profile_cautious_investigator()
    return replace(base, profile_id="placeholder", label="Default synthetic (cautious)")
