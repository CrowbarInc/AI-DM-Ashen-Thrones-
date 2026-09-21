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
    """Choose the next bounded action from the preceding GM output and evaluator evidence."""
    semantic = str(prior_evaluation.get("semantic_result") or "UNCHECKED")
    malformed = _gate_status(prior_evaluation, "malformed_output")
    intent = _gate_status(prior_evaluation, "player_intent_addressed")

    if semantic == "INVALID_RUN":
        return SyntheticDecision("", "runtime_invalid", True, "invalid_run")
    if semantic == "UNCHECKED" or malformed == "UNCHECKED" or intent == "UNCHECKED":
        return SyntheticDecision("", "semantic_evaluation_unchecked", True, "evaluation_unchecked")

    legitimate_boundary = bool(_BOUNDARY_RE.search(prior_gm_text)) and malformed != "FAIL"
    if legitimate_boundary:
        return SyntheticDecision("", "legitimate_uncertainty_refusal_or_redirection", True, "legitimate_boundary")

    if semantic == "PASS" and _has_scenario_evidence(scenario, prior_gm_text):
        if config.strategy == "adversarial":
            options = _probe_options(scenario, set(state.selected_probe_keys))
            key, text = _stable_choice(options, seed=config.seed, turn_index=turn_index)
            if text:
                state.selected_probe_keys.append(key)
                state.attempts_on_intent = 0
                state.current_intent = key
                return SyntheticDecision(text, f"adversarial_probe:{key}:prior_semantic_pass")
        return SyntheticDecision("", "objective_satisfactorily_resolved", True, "objective_resolved")

    if semantic == "PASS":
        semantic = "FAIL"

    if state.attempts_on_intent >= config.max_attempts_per_intent:
        return SyntheticDecision("", "bounded_persistence_exhausted", True, "max_intent_attempts")

    state.attempts_on_intent += 1
    if state.current_intent not in state.unresolved_intents:
        state.unresolved_intents.append(state.current_intent)

    if malformed == "FAIL":
        text = scenario.degradation_probe or scenario.rephrased_follow_up
        return SyntheticDecision(text, "repeat_after_malformed_output")

    if scenario.observation_follow_up and re.search(r"\b(?:look|inspect|read|examine|notice|see)\b", scenario.initial_action, re.I):
        return SyntheticDecision(scenario.observation_follow_up, "observation_not_fulfilled:persist")

    if state.attempts_on_intent == 1:
        return SyntheticDecision(scenario.narrower_follow_up, "incomplete_or_vague_answer:demand_specificity")
    if state.attempts_on_intent == 2:
        return SyntheticDecision(scenario.rephrased_follow_up, "unresolved_intent:rephrase")
    text = scenario.return_to_topic_probe or scenario.rephrased_follow_up
    return SyntheticDecision(text, "thread_persistence:return_to_unresolved_objective")
