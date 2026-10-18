"""Deterministic GM-output-aware simulated-player policy for validation tooling."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from tests.helpers.synthetic_types import SyntheticDecision


@dataclass(frozen=True)
class ReactiveScenario:
    scenario_id: str
    objective: str
    initial_action: str
    narrower_follow_up: str
    rephrased_follow_up: str
    observation_follow_up: str = ""
    contradiction_probe: str = ""
    established_fact_probe: str = ""
    knowledge_boundary_probe: str = ""
    return_to_topic_probe: str = ""
    degradation_probe: str = ""
    acceptance_markers: tuple[str, ...] = ()
    max_turns: int = 6
    max_attempts_per_intent: int = 3


@dataclass(frozen=True)
class ReactivePlayerConfig:
    strategy: str
    seed: int
    max_turns: int
    max_attempts_per_intent: int


@dataclass
class ReactivePlayerState:
    current_intent: str
    attempts_on_intent: int = 0
    selected_probe_keys: list[str] = field(default_factory=list)
    unresolved_intents: list[str] = field(default_factory=list)


_BOUNDARY_RE = re.compile(
    r"\b(?:i\s+(?:do not|don't)\s+know|cannot\s+know|can't\s+know|"
    r"cannot\s+answer[^.!?]{0,50}\bwhat\s+i\s+know|"
    r"won't\s+(?:say|tell)|refus(?:e|es|ed)|uncertain|not\s+sure|"
    r"no\s+one\s+knows|not\s+something\s+i\s+can\s+say|ask\s+(?:the|a)\s+\w+)\b",
    re.IGNORECASE,
)

_VISIBLE_NONANSWER_RE = re.compile(
    r"\b(?:i\s+(?:do not|don't)\s+know|cannot\s+answer|can't\s+answer|"
    r"nothing\s+new|look\s+again|closer\s+looking\s+yields\s+nothing|"
    r"not\s+enough\s+to\s+answer|what\s+do\s+you\s+mean|clarify)\b",
    re.IGNORECASE,
)


def _gate_status(evaluation: Mapping[str, Any], name: str) -> str:
    gates = evaluation.get("mandatory_gates")
    if not isinstance(gates, Mapping):
        return "UNCHECKED"
    gate = gates.get(name)
    return str(gate.get("status") or "UNCHECKED") if isinstance(gate, Mapping) else "UNCHECKED"


def _stable_choice(options: Sequence[tuple[str, str]], *, seed: int, turn_index: int) -> tuple[str, str]:
    if not options:
        return "", ""
    rng = random.Random((int(seed) * 1_000_003) ^ (turn_index * 917_633) ^ 0xA51E)
    return options[rng.randrange(len(options))]


def _probe_options(scenario: ReactiveScenario, used: set[str]) -> list[tuple[str, str]]:
    rows = (
        ("contradiction", scenario.contradiction_probe),
        ("established_fact", scenario.established_fact_probe),
        ("knowledge_boundary", scenario.knowledge_boundary_probe),
        ("return_to_topic", scenario.return_to_topic_probe),
        ("degradation", scenario.degradation_probe),
    )
    return [(key, text) for key, text in rows if text.strip() and key not in used]


def _has_scenario_evidence(scenario: ReactiveScenario, gm_text: str) -> bool:
    if not scenario.acceptance_markers:
        return True
    lowered = gm_text.lower()
    return any(marker.lower() in lowered for marker in scenario.acceptance_markers)


def _visible_response_seems_satisfactory(scenario: ReactiveScenario, gm_text: str) -> bool:
    if not gm_text.strip():
        return False
    if _VISIBLE_NONANSWER_RE.search(gm_text):
        return False
    return _has_scenario_evidence(scenario, gm_text)


def initial_decision(scenario: ReactiveScenario) -> SyntheticDecision:
    return SyntheticDecision(
        player_text=scenario.initial_action,
        rationale=f"initial_objective:{scenario.objective}",
    )


def decide_reactive_action(
    *,
    scenario: ReactiveScenario,
    config: ReactivePlayerConfig,
    state: ReactivePlayerState,
    turn_index: int,
    prior_gm_text: str,
    prior_evaluation: Mapping[str, Any],
) -> SyntheticDecision:
    """Choose the next bounded action from player-visible transcript evidence.

    ``prior_evaluation`` is accepted for artifact compatibility, but normal player
    cognition does not branch on evaluator labels or gate names.
    """
    _ = prior_evaluation

    if not str(prior_gm_text or "").strip():
        return SyntheticDecision(scenario.degradation_probe or scenario.rephrased_follow_up, "visible_missing_response:persist")

    legitimate_boundary = bool(_BOUNDARY_RE.search(prior_gm_text))
    if legitimate_boundary:
        return SyntheticDecision("", "legitimate_uncertainty_refusal_or_redirection", True, "legitimate_boundary")

    if _visible_response_seems_satisfactory(scenario, prior_gm_text):
        if config.strategy == "adversarial":
            options = _probe_options(scenario, set(state.selected_probe_keys))
            key, text = _stable_choice(options, seed=config.seed, turn_index=turn_index)
            if text:
                state.selected_probe_keys.append(key)
                state.attempts_on_intent = 0
                state.current_intent = key
                return SyntheticDecision(text, f"adversarial_probe:{key}:prior_semantic_pass")
        return SyntheticDecision("", "objective_satisfactorily_resolved", True, "objective_resolved")

    if state.attempts_on_intent >= config.max_attempts_per_intent:
        return SyntheticDecision("", "bounded_persistence_exhausted", True, "max_intent_attempts")

    state.attempts_on_intent += 1
    if state.current_intent not in state.unresolved_intents:
        state.unresolved_intents.append(state.current_intent)

    if scenario.observation_follow_up and re.search(r"\b(?:look|inspect|read|examine|notice|see)\b", scenario.initial_action, re.I):
        return SyntheticDecision(scenario.observation_follow_up, "observation_not_fulfilled:persist")

    if state.attempts_on_intent == 1:
        return SyntheticDecision(scenario.narrower_follow_up, "incomplete_or_vague_answer:demand_specificity")
    if state.attempts_on_intent == 2:
        return SyntheticDecision(scenario.rephrased_follow_up, "unresolved_intent:rephrase")
    text = scenario.return_to_topic_probe or scenario.rephrased_follow_up
    return SyntheticDecision(text, "thread_persistence:return_to_unresolved_objective")
