"""Synthetic-player infrastructure for tests/tooling only. No production imports from this module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SyntheticProfile:
    """Identity and tuning knobs for a synthetic player (test harness)."""

    profile_id: str
    label: str = ""
    curiosity: float = 0.5
    risk_tolerance: float = 0.5
    social_bias: float = 0.5
    magic_bias: float = 0.5
    persistence: float = 0.5
    edge_case_bias: float = 0.5
    question_bias: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SyntheticTurnView:
    """Per-turn context passed into a synthetic policy (snapshots optional until wired)."""

    turn_index: int
    player_text_history: tuple[str, ...] = ()
    snapshot: dict[str, Any] | None = None
    seed: int = 0
    profile: SyntheticProfile | None = None


@dataclass
class SyntheticDecision:
    """One player utterance (or pass) chosen by the synthetic policy."""

    player_text: str
    rationale: str = ""
    stop_requested: bool = False
    stop_reason: str = ""


@dataclass
class SyntheticRunResult:
    """Outcome of a synthetic session run (minimal fields for scaffolding)."""

    profiles: tuple[SyntheticProfile, ...]
    decisions: tuple[SyntheticDecision, ...]
    snapshots: tuple[dict[str, Any], ...]
    ok: bool = True
    profile_name: str = ""
    seed: int = 0
    stop_reason: str = ""
    turn_views: tuple[dict[str, Any], ...] = ()
