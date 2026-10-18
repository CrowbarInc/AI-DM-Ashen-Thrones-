"""Bound Slice 2 residual detectors so a raw-chat hang cannot hide in them.

Adversarial punctuation is split into hundreds of fragments. The full audit is
linear in fragment count. A single detector search on that text stays tiny.
"""
from __future__ import annotations

import time

from game import gm_resolution_decision as decision
from game.gm_resolution_decision import audit_narration_against_decision

_DECISION = {
    "proposed_facts": [],
    "permitted_state_mutations": [],
    "executable_obligations": {"primary": None, "supporting": [], "sequence": []},
}

_PATTERNS = (
    "_ACTOR_ATTRIBUTION_RE",
    "_EVENT_CAUSE_ATTRIBUTION_RE",
    "_EVENT_HISTORY_ASSERTION_RE",
    "_CAUSAL_RELATION_RE",
    "_EVIDENTIAL_RELATION_RE",
    "_CERTAINTY_UPGRADE_RE",
    "_DEFINITE_HISTORY_RE",
    "_POLAR_Q_RE",
    "_STATEFUL_ASSERTION_RE",
    "_QUOTE_SPAN_RE",
    "_SENTENCE_RE",
)


def _clock(fn) -> float:
    started = time.perf_counter()
    fn()
    return time.perf_counter() - started


def test_slice2_detector_searches_stay_bounded_on_adversarial_text():
    samples = {
        "short": "The guard nods once and says nothing about the toll.",
        "long": " ".join(["The guard nods once and says nothing about the toll."] * 400),
        "repeated_token": "bell " * 2000,
        "quoted": 'The runner says, "' + ("I heard a rumor. " * 300) + '"',
        "adversarial_punctuation": ("...?!," * 500) + " " + ('"' * 200),
    }
    search_timings: dict[str, float] = {}
    hostile = samples["adversarial_punctuation"]
    for code, compiled in decision._CONSEQUENTIAL_PATTERNS:
        search_timings[f"consequential:{code}"] = _clock(lambda compiled=compiled: compiled.search(hostile))
    for name in _PATTERNS:
        pattern = getattr(decision, name)
        search_timings[name] = _clock(lambda pattern=pattern: list(pattern.finditer(hostile)))
    slow_search = {name: elapsed for name, elapsed in search_timings.items() if elapsed >= 0.05}
    assert not slow_search, search_timings

    audit_timings = {
        name: _clock(lambda text=text: audit_narration_against_decision(text, decision=_DECISION, authored_corpus=""))
        for name, text in samples.items()
        if name != "adversarial_punctuation"
    }
    slow_audit = {name: elapsed for name, elapsed in audit_timings.items() if elapsed >= 0.25}
    assert not slow_audit, audit_timings

    punctuation_elapsed = _clock(
        lambda: audit_narration_against_decision(
            samples["adversarial_punctuation"],
            decision=_DECISION,
            authored_corpus="",
        )
    )
    # Hundreds of punctuation fragments, still linear. This ceiling catches a blow-up.
    assert punctuation_elapsed < 20.0, punctuation_elapsed
