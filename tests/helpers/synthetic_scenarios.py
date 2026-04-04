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


def social_redirect_followup_opening() -> SyntheticScenario:
    """Seeded social destination redirect; policy turns should stay socially grounded."""
    return SyntheticScenario(
        scenario_id="social_redirect_followup_opening",
        profile_factory=profile_social_prober,
        seed=1110,
        max_turns=5,
        player_texts=(
            "The gate clerk redirects me to the duty sergeant; I follow and pick the conversation "
            "back up about tonight's patrol assignments.",
        ),
        transcript_recommended=False,
        notes="Redirect-then-reopen thread; pressures social follow-up after a destination shift.",
        regression_risk_class="social_destination_redirect_followup",
    )


def who_next_where_followup_opening() -> SyntheticScenario:
    """Who/where authority seed; pressures target-aware questioning across later turns."""
    return SyntheticScenario(
        scenario_id="who_next_where_followup_opening",
        profile_factory=profile_social_prober,
        seed=1120,
        max_turns=5,
        player_texts=(
            "Who can sign a curfew pass after dark, and where are they stationed right now?",
        ),
        transcript_recommended=True,
        notes="Explicit who/where social question; good for soft transcript policy-slug signal.",
        regression_risk_class="social_target_location_followup",
    )


def authority_switch_followup_opening() -> SyntheticScenario:
    """Authority figure changes mid-exchange; follow-ups should preserve addressable social pressure."""
    return SyntheticScenario(
        scenario_id="authority_switch_followup_opening",
        profile_factory=profile_social_prober,
        seed=1130,
        max_turns=5,
        player_texts=(
            "The visiting magistrate cuts across the harbormaster mid-sentence; I address the "
            "magistrate and restate my question about sealed cargo.",
        ),
        transcript_recommended=False,
        notes="Speaker/authority switch with restated question; continuity across policy turns.",
        regression_risk_class="social_authority_switch_continuity",
    )


def speaker_grounding_followup_opening() -> SyntheticScenario:
    """Pin a claim to the speaker; pressures grounded social follow-up rather than abstract drift."""
    return SyntheticScenario(
        scenario_id="speaker_grounding_followup_opening",
        profile_factory=profile_social_prober,
        seed=1140,
        max_turns=5,
        player_texts=(
            "They claimed the watch rotates at the bell—I turn to the speaker and press them on "
            "who actually rang it last night.",
        ),
        transcript_recommended=False,
        notes="Speaker-grounded contradiction pressure; social probe/direct follow-through.",
        regression_risk_class="social_speaker_grounding_followup",
    )


def lead_commitment_followthrough_opening() -> SyntheticScenario:
    """Seeded commitment to a working lead; policy turns should keep investigative momentum."""
    return SyntheticScenario(
        scenario_id="lead_commitment_followthrough_opening",
        profile_factory=profile_cautious_investigator,
        seed=6020,
        max_turns=5,
        player_texts=(
            "I treat the smuggler's dead drop as our working lead and commit the next stretch of "
            "time to tracing it without taking side quests.",
        ),
        transcript_recommended=True,
        notes="Lead commitment seed; post-opener turns pressure follow-through vs stalling.",
        regression_risk_class="lead_commitment_followthrough_stall",
    )


def npc_payoff_or_fallback_opening() -> SyntheticScenario:
    """NPC-mediated payoff vs fallback; policy turns should stay socially and procedurally engaged."""
    return SyntheticScenario(
        scenario_id="npc_payoff_or_fallback_opening",
        profile_factory=profile_social_prober,
        seed=6021,
        max_turns=5,
        player_texts=(
            "The informant either names the buyer or offers a safe fallback meeting; I pin them to "
            "which outcome we actually got and what we do next.",
        ),
        transcript_recommended=False,
        notes="Payoff/fallback fork after an NPC handoff; continuity across policy turns.",
        regression_risk_class="lead_npc_payoff_or_fallback_continuity",
    )


def obsolete_lead_pressure_opening() -> SyntheticScenario:
    """New information supersedes an old trail; policy should keep forward investigative pressure."""
    return SyntheticScenario(
        scenario_id="obsolete_lead_pressure_opening",
        profile_factory=profile_cautious_investigator,
        seed=6022,
        max_turns=5,
        player_texts=(
            "Fresh testimony supersedes yesterday's trail; I stop chasing the old lead and re-aim "
            "the investigation on what matters now.",
        ),
        transcript_recommended=False,
        notes="Obsolescence pivot seed; avoids narrating engine state—pressures player-side follow-up.",
        regression_risk_class="lead_obsolescence_pivot_pressure",
    )


def alternate_resolution_followup_opening() -> SyntheticScenario:
    """Player bypasses the expected route; later policy turns should preserve purposeful pressure."""
    return SyntheticScenario(
        scenario_id="alternate_resolution_followup_opening",
        profile_factory=profile_cautious_investigator,
        seed=6023,
        max_turns=5,
        player_texts=(
            "Rather than wait for the warrant, I take the side-alley approach; I keep pressure on "
            "the objective without reopening the front-door angle.",
        ),
        transcript_recommended=False,
        notes="Alternate resolution path; follow-up behavior after a deliberate route change.",
        regression_risk_class="lead_alternate_route_continuity",
    )


def advancement_signal_opening() -> SyntheticScenario:
    """Seeded GM/thread signal; post-opener policy should stay investigation- or action-forward."""
    return SyntheticScenario(
        scenario_id="advancement_signal_opening",
        profile_factory=profile_cautious_investigator,
        seed=7025,
        max_turns=5,
        player_texts=(
            "The sergeant points to fresh wheel ruts and a snapped latch on the postern; I treat "
            "that as the live thread and push the examination forward instead of re-litigating the gate.",
        ),
        transcript_recommended=False,
        notes="Advancement cue in opener; pressures continued survey/investigation/push after setup.",
        regression_risk_class="exploration_advancement_signal_stall",
    )


def conditional_affordance_opening() -> SyntheticScenario:
    """If/then affordance seed; policy turns should pick up a branch (social, trade, or persistence)."""
    return SyntheticScenario(
        scenario_id="conditional_affordance_opening",
        profile_factory=profile_social_prober,
        seed=7026,
        max_turns=5,
        player_texts=(
            "If the watch corporal signs the passage chit, I move immediately; if they refuse, I "
            "negotiate a witnessed escort instead of arguing in place.",
        ),
        transcript_recommended=False,
        notes="Conditional branch seed; follow-through vs dropping the fork after turn 0.",
        regression_risk_class="exploration_conditional_affordance_drop",
    )


def scene_transition_followup_opening() -> SyntheticScenario:
    """Location shift seed; post-opener behavior should stay forward (not hang-back-only re-asks)."""
    return SyntheticScenario(
        scenario_id="scene_transition_followup_opening",
        profile_factory=profile_cautious_investigator,
        seed=7027,
        max_turns=5,
        player_texts=(
            "We leave the gatehouse antechamber and step into the yard; I stop querying the clerk "
            "and re-orient on sightlines, cover, and what the open space reveals.",
        ),
        transcript_recommended=True,
        notes="Scene transition seed; progression/momentum after spatial movement.",
        regression_risk_class="exploration_scene_transition_followup_stall",
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
    social_redirect_followup_opening,
    who_next_where_followup_opening,
    authority_switch_followup_opening,
    speaker_grounding_followup_opening,
    lead_commitment_followthrough_opening,
    npc_payoff_or_fallback_opening,
    obsolete_lead_pressure_opening,
    alternate_resolution_followup_opening,
    advancement_signal_opening,
    conditional_affordance_opening,
    scene_transition_followup_opening,
)
