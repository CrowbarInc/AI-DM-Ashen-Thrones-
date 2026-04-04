"""Reusable synthetic session presets for tests and tooling (harness-only).

Each preset bundles only inputs that :func:`run_synthetic_session` already accepts.
Use :func:`dataclasses.replace` to tweak seed, ``max_turns``, or ``player_texts`` per test.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from tests.helpers.synthetic_profiles import (
    profile_adversarial_rules_poker,
    profile_arcane_examiner,
    profile_cautious_investigator,
    profile_social_prober,
)
from tests.helpers.synthetic_types import SyntheticProfile


@dataclass(frozen=True)
class SyntheticScenario:
    """Lightweight start/run bundle for ``run_synthetic_session``."""

    scenario_id: str
    profile_factory: Callable[[], SyntheticProfile]
    seed: int
    max_turns: int = 5
    player_texts: tuple[str, ...] = ()
    transcript_recommended: bool = False
    notes: str = ""
    regression_risk_class: str = ""

    def run_kwargs(self, *, use_fake_gm: bool) -> dict[str, Any]:
        """Keyword arguments for :func:`tests.helpers.synthetic_runner.run_synthetic_session`."""
        return {
            "profile": self.profile_factory(),
            "seed": self.seed,
            "max_turns": self.max_turns,
            "player_texts": self.player_texts,
            "use_fake_gm": use_fake_gm,
        }


def default_opening() -> SyntheticScenario:
    """Baseline cautious loop; aligned with primary fake-GM smoke rows."""
    return SyntheticScenario(
        scenario_id="default_opening",
        profile_factory=profile_cautious_investigator,
        seed=101,
        max_turns=5,
        player_texts=(),
        transcript_recommended=True,
        notes="Cautious investigator, policy-driven from turn 0.",
    )


def social_opening() -> SyntheticScenario:
    """High social bias; good for dialogue-heavy harness checks."""
    return SyntheticScenario(
        scenario_id="social_opening",
        profile_factory=profile_social_prober,
        seed=202,
        max_turns=5,
        player_texts=(),
        transcript_recommended=True,
        notes="Social prober; policy-driven from turn 0.",
    )


def investigation_opening() -> SyntheticScenario:
    """Seeds an investigative first line; remaining turns from policy."""
    return SyntheticScenario(
        scenario_id="investigation_opening",
        profile_factory=profile_cautious_investigator,
        seed=707,
        max_turns=5,
        player_texts=("I scan the ground for tracks and signs of recent passage.",),
        transcript_recommended=True,
        notes="First utterance fixed; useful when history seeding should be explicit.",
    )


def magic_anomaly_opening() -> SyntheticScenario:
    """Arcane-biased policy with an optional magic-focused seed line."""
    return SyntheticScenario(
        scenario_id="magic_anomaly_opening",
        profile_factory=profile_arcane_examiner,
        seed=808,
        max_turns=5,
        player_texts=(
            "I focus on the residual magic—what school or weave does it resemble?",
        ),
        transcript_recommended=False,
        notes="Prefer fake-GM smoke until transcript coverage is expanded; arcane examiner.",
    )


def friction_opening() -> SyntheticScenario:
    """Edge-case / rules-challenge bias; strong deterministic fake-GM signal."""
    return SyntheticScenario(
        scenario_id="friction_opening",
        profile_factory=profile_adversarial_rules_poker,
        seed=303,
        max_turns=5,
        player_texts=(),
        transcript_recommended=False,
        notes="Adversarial rules poker; policy-driven from turn 0.",
    )


def directed_social_opening() -> SyntheticScenario:
    """Directed social contact seed; validates social follow-up from policy turns."""
    return SyntheticScenario(
        scenario_id="directed_social_opening",
        profile_factory=profile_social_prober,
        seed=404,
        max_turns=5,
        player_texts=(
            "I approach the gate sergeant directly and ask who controls patrol assignments tonight.",
        ),
        transcript_recommended=True,
        notes="Lead-targeted social opener; useful for stable transcript soft checks.",
        regression_risk_class="directed_social_routing_confusion",
    )


def emergent_npc_opening() -> SyntheticScenario:
    """No scripted line; social profile should still surface NPC-facing probes."""
    return SyntheticScenario(
        scenario_id="emergent_npc_opening",
        profile_factory=profile_social_prober,
        seed=505,
        max_turns=5,
        player_texts=(),
        transcript_recommended=False,
        notes="Covers unscripted NPC emergence via social-bias policy behavior.",
        regression_risk_class="emergent_npc_addressability_redirect",
    )


def clue_followup_opening() -> SyntheticScenario:
    """Starts with a clue contradiction; checks investigative follow-up pressure."""
    return SyntheticScenario(
        scenario_id="clue_followup_opening",
        profile_factory=profile_cautious_investigator,
        seed=606,
        max_turns=5,
        player_texts=(
            "The ledger dates do not match the patrol story; I follow the discrepancy before moving on.",
        ),
        transcript_recommended=False,
        notes="Lead/clue continuity pressure with fixed contradiction seed.",
        regression_risk_class="lead_followup_contradiction_pressure",
    )


def retry_pressure_opening() -> SyntheticScenario:
    """Rules-pressure seed; exercises clarification/retry style policy responses."""
    return SyntheticScenario(
        scenario_id="retry_pressure_opening",
        profile_factory=profile_adversarial_rules_poker,
        seed=909,
        max_turns=5,
        player_texts=(
            "Before we proceed, I want the exact ruling and what changes if we retry this approach.",
        ),
        transcript_recommended=False,
        notes="Retry/repair pressure around edge-case clarification and ruling loops.",
        regression_risk_class="retry_fallback_clarification_pressure",
    )


# All preset factories in stable order (for iteration / stability tests).
PRESET_FACTORIES: tuple[Callable[[], SyntheticScenario], ...] = (
    default_opening,
    social_opening,
    investigation_opening,
    magic_anomaly_opening,
    friction_opening,
    directed_social_opening,
    emergent_npc_opening,
    clue_followup_opening,
    retry_pressure_opening,
)
