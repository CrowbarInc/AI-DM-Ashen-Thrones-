"""Routing notes for PR-DO. The existing router is not redesigned."""

from __future__ import annotations


def engine_channel_from_utterance(utterance: str) -> str | None:
    """Separate an explicit OOC prefix before gameplay routing.

    Unmarked corrections are not guessed.
    """
    if utterance.lstrip().upper().startswith("OOC:"):
        return "OUT_OF_CHARACTER_CORRECTION"
    return None


# Copied from artifacts/pr_dn_interpretation_robustness/PR-DN_routing_baseline.csv.
STORED_ROUTING = (
    {"scenario_id": "DN01", "refined_routed": True, "deterministic_quality": "FAIL", "category": "novel_compound"},
    {"scenario_id": "DN02", "refined_routed": True, "deterministic_quality": "FAIL", "category": "novel_compound"},
    {"scenario_id": "DN03", "refined_routed": True, "deterministic_quality": "FAIL", "category": "ambiguous_reference"},
    {"scenario_id": "DN04", "refined_routed": False, "deterministic_quality": "FAIL", "category": "ambiguous_reference_ooc_correction"},
    {"scenario_id": "DN05", "refined_routed": False, "deterministic_quality": "FAIL", "category": "unauthorized_world_fact"},
    {"scenario_id": "DN06", "refined_routed": False, "deterministic_quality": "FAIL", "category": "unauthorized_world_fact"},
    {"scenario_id": "DN07", "refined_routed": False, "deterministic_quality": "FAIL", "category": "direct_mechanical_override"},
    {"scenario_id": "DN08", "refined_routed": False, "deterministic_quality": "FAIL", "category": "direct_mechanical_override"},
    {"scenario_id": "DN09", "refined_routed": False, "deterministic_quality": "FAIL", "category": "unsupported_mechanic"},
    {"scenario_id": "DN10", "refined_routed": False, "deterministic_quality": "FAIL", "category": "unsupported_mechanic"},
    {"scenario_id": "DN11", "refined_routed": False, "deterministic_quality": "PASS", "category": "ordinary_control"},
    {"scenario_id": "DN12", "refined_routed": False, "deterministic_quality": "FAIL", "category": "ordinary_control_ooc_correction"},
)


def routing_assessment(utterances: dict[str, str]) -> list[dict]:
    rows = []
    for stored in STORED_ROUTING:
        utterance = utterances.get(stored["scenario_id"], "")
        prefix = engine_channel_from_utterance(utterance)
        rows.append(
            {
                **stored,
                "explicit_ooc_prefix": prefix == "OUT_OF_CHARACTER_CORRECTION",
                "separable_before_gameplay_routing": prefix == "OUT_OF_CHARACTER_CORRECTION",
            }
        )
    return rows
