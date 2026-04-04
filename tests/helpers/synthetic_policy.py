"""Synthetic-player infrastructure for tests/tooling only. No production imports from this module."""

from __future__ import annotations

import random
from typing import Iterable

from tests.helpers.synthetic_profiles import default_placeholder_profile
from tests.helpers.synthetic_types import SyntheticDecision, SyntheticProfile, SyntheticTurnView

# Weights align with profile fields:
# curiosity, risk_tolerance, social_bias, magic_bias, persistence, edge_case_bias, question_bias
_TemplateRow = tuple[str, str, tuple[float, float, float, float, float, float, float]]

_TEMPLATES: tuple[_TemplateRow, ...] = (
    (
        "I take a slow pass around the edges of the area before committing.",
        "cautious_survey",
        (0.95, 0.1, 0.15, 0.2, 0.65, 0.08, 0.45),
    ),
    (
        "I scan for exits, cover, and anything that does not match the story we were told.",
        "investigate_inconsistency",
        (0.88, 0.2, 0.22, 0.25, 0.75, 0.35, 0.55),
    ),
    (
        "I step in now and claim the initiative while the opening is still there.",
        "bold_push",
        (0.35, 0.95, 0.4, 0.15, 0.25, 0.2, 0.25),
    ),
    (
        "I address whoever seems to be in charge and ask plainly what they want from us.",
        "social_direct",
        (0.42, 0.35, 0.92, 0.12, 0.38, 0.15, 0.62),
    ),
    (
        "I keep the talk light, watch reactions, and probe for who is nervous.",
        "social_probe",
        (0.5, 0.3, 0.88, 0.18, 0.48, 0.22, 0.58),
    ),
    (
        "I quietly check whether anything here feels magically worked or recently dispelled.",
        "arcane_sense",
        (0.55, 0.25, 0.18, 0.95, 0.55, 0.4, 0.42),
    ),
    (
        "I ask for exact mechanical clarification on cover and opportunity attacks before I commit.",
        "rules_clarify",
        (0.25, 0.4, 0.22, 0.15, 0.35, 0.92, 0.78),
    ),
    (
        "I press on whether an edge case applies here and what the ruling is if it does.",
        "edge_case_press",
        (0.38, 0.48, 0.2, 0.22, 0.45, 0.9, 0.72),
    ),
    (
        "What exactly would happen if I tried that right now?",
        "hypothetical_question",
        # Low edge weight: social/question-led profiles keep this; rules-pokers prefer edge/rules rows.
        (0.62, 0.45, 0.42, 0.35, 0.4, 0.38, 0.92),
    ),
    (
        "I circle back to an earlier detail we skipped and insist we resolve it before moving on.",
        "persistence_followup",
        (0.58, 0.32, 0.38, 0.28, 0.9, 0.45, 0.68),
    ),
    (
        "I hang back, say little, and let someone else take point while I observe.",
        "hang_back",
        (0.4, 0.12, 0.25, 0.15, 0.55, 0.12, 0.32),
    ),
    (
        "I offer a concrete trade: safe passage for information we already have.",
        "negotiate_trade",
        (0.48, 0.55, 0.85, 0.2, 0.42, 0.28, 0.52),
    ),
)


def _stable_profile_tag(profile_id: str) -> int:
    """Process-stable tag (do not use built-in hash — it salts across interpreter runs)."""
    x = 2166136261
    for b in profile_id.encode("utf-8"):
        x ^= b
        x = (x * 16777619) & 0xFFFFFFFF
    return x


def _mix_seed(seed: int, turn_index: int, profile: SyntheticProfile) -> int:
    return (
        (int(seed) * 1_000_003)
        ^ (int(turn_index) * 917_633)
        ^ _stable_profile_tag(profile.profile_id)
        ^ 0x9E3779B9
    )


def _template_score(weights: tuple[float, ...], profile: SyntheticProfile) -> float:
    tendencies = (
        profile.curiosity,
        profile.risk_tolerance,
        profile.social_bias,
        profile.magic_bias,
        profile.persistence,
        profile.edge_case_bias,
        profile.question_bias,
    )
    return sum(w * t for w, t in zip(weights, tendencies, strict=True))


def _ranked_choices(
    profile: SyntheticProfile,
    rng: random.Random,
) -> list[tuple[float, str, str]]:
    ranked: list[tuple[float, str, str]] = []
    for text, slug, weights in _TEMPLATES:
        base = _template_score(weights, profile)
        noise = rng.random() * 0.02
        ranked.append((base + noise, text, slug))
    ranked.sort(key=lambda row: -row[0])
    return ranked


def _first_non_repeating(
    ranked: Iterable[tuple[float, str, str]],
    last_normalized: str,
) -> tuple[str, str] | None:
    for _, text, slug in ranked:
        if text.strip() != last_normalized:
            return text, slug
    return None


def decide_placeholder(view: SyntheticTurnView) -> SyntheticDecision:
    """
    Deterministic synthetic player line from profile + turn seed.

    Uses only fields appropriate for harness control (seed, profile, history, turn_index).
    ``snapshot`` is ignored in v1 so policies do not depend on debug-only payloads.
    """
    profile = view.profile or default_placeholder_profile()
    rng = random.Random(_mix_seed(view.seed, view.turn_index, profile))
    ranked = _ranked_choices(profile, rng)

    last = ""
    if view.player_text_history:
        last = view.player_text_history[-1].strip()

    picked = _first_non_repeating(ranked, last)
    if picked is None:
        text = "I pause, reconsider, and name one new concrete thing I examine next."
        slug = "stall_breaker"
    else:
        text, slug = picked

    text = text.strip() or "I state what I do next in one clear sentence."
    rationale = f"{profile.profile_id}:{slug}"
    return SyntheticDecision(player_text=text, rationale=rationale)
