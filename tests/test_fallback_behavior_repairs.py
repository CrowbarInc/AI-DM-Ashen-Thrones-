from __future__ import annotations

import pytest

from game.final_emission_repairs import _smooth_repaired_fallback_line, repair_fallback_behavior
from game.final_emission_validators import validate_fallback_behavior


pytestmark = pytest.mark.unit
_FORBIDDEN_META_BITS = (
    "unclear",
    "not settled",
    "move plays out",
    "move resolves",
    "unresolved",
    "insufficient",
    "information",
    "system",
)


def _fallback_contract(**overrides: object) -> dict:
    contract = {
        "enabled": True,
        "uncertainty_active": True,
        "uncertainty_sources": ["unknown_identity"],
        "uncertainty_mode": "scene_ambiguity",
        "allowed_behaviors": {
            "ask_clarifying_question": True,
            "hedge_appropriately": True,
            "provide_partial_information": True,
        },
        "disallowed_behaviors": {
            "invented_certainty": True,
            "fabricated_authority": True,
            "meta_system_explanations": True,
        },
        "diegetic_only": True,
        "max_clarifying_questions": 1,
        "prefer_partial_over_question": True,
        "require_partial_to_state_known_edge": True,
        "require_partial_to_state_unknown_edge": True,
        "require_partial_to_offer_next_lead": True,
        "allowed_hedge_forms": [
            "I can't swear to it, but",
            "From what I saw,",
            "As far as rumor goes,",
            "Looks like",
            "Hard to tell, but",
        ],
        "forbidden_hedge_forms": [
            "I lack enough information to answer confidently.",
            "The system cannot confirm that.",
            "Canon proves it.",
            "As an AI, I don't know.",
            "There is insufficient context available.",
        ],
        "allowed_authority_bases": [
            "direct_observation",
            "established_report",
            "rumor_marked_as_rumor",
            "visible_evidence",
        ],
        "forbidden_authority_bases": [
            "unsupported_named_culprit",
            "unsupported_exact_location",
            "unsupported_motive_as_fact",
            "unsupported_procedural_certainty",
            "system_or_canon_claims",
        ],
        "debug": {},
    }
    contract.update(overrides)
    return contract


def _repair(text: str, contract: dict | None = None) -> tuple[str, dict, dict]:
    ctr = contract or _fallback_contract()
    validation = validate_fallback_behavior(text, ctr)
    repaired, meta, _ = repair_fallback_behavior(text, ctr, validation)
    return repaired, meta, validation


def _assert_no_meta_bits(text: str) -> None:
    low = text.lower()
    for bit in _FORBIDDEN_META_BITS:
        assert bit not in low


def test_repaired_line_smoothing_merges_repeated_subject_nonanswer_clause() -> None:
    smoothed = _smooth_repaired_fallback_line(
        "Tavern Runner nods once. Tavern Runner does not answer at once."
    )

    low = smoothed.lower()
    assert "tavern runner nods once. tavern runner" not in low
    assert smoothed.count("Tavern Runner") == 1
    assert "does not answer at once" in low
    _assert_no_meta_bits(smoothed)


def test_repaired_line_smoothing_merges_repeated_subject_guarded_clause() -> None:
    smoothed = _smooth_repaired_fallback_line(
        "Guard Captain watches you. Guard Captain gives nothing away."
    )

    low = smoothed.lower()
    assert "guard captain watches you. guard captain" not in low
    assert smoothed.count("Guard Captain") == 1
    assert ("watches you and gives nothing away" in low or "watches you, but gives nothing away" in low)


def test_repaired_line_smoothing_preserves_grounded_detail_and_uncertainty_signal() -> None:
    smoothed = _smooth_repaired_fallback_line(
        "The captain keeps his eyes on the crowd. The captain gives you nothing yet. Check the customs arch."
    )

    low = smoothed.lower()
    assert "the captain keeps his eyes on the crowd. the captain" not in low
    assert "crowd" in low
    assert "gives you nothing yet" in low
    assert "customs arch" in low


def test_repaired_line_smoothing_avoids_ambiguous_pronouns_in_two_entity_case() -> None:
    raw = "Guard Captain looks to the Tavern Runner. Tavern Runner does not answer at once."
    assert _smooth_repaired_fallback_line(raw) == raw


def test_repair_strips_meta_fallback_voice_while_preserving_grounded_content() -> None:
    repaired, meta, validation = _repair(
        "I don't have enough information to answer confidently. The east gate ledger points to the ward clerk."
    )

    low = repaired.lower()
    assert validation["meta_fallback_voice_detected"] is True
    assert "enough information" not in low
    assert "east gate" in low
    assert "ward clerk" in low
    assert meta["fallback_behavior_meta_voice_stripped"] is True
    assert meta["fallback_behavior_partial_used"] is True
    assert "strip_meta_voice" in meta["fallback_behavior_repair_mode"]
    assert "bounded_partial" in meta["fallback_behavior_repair_mode"]


@pytest.mark.xfail(reason="current identity repair strips authority language but still preserves unsupported named culprit text")
def test_repair_removes_fabricated_authority_without_inventing_replacement_facts() -> None:
    repaired, meta, validation = _repair("The records show the culprit was Captain Verrick.")

    low = repaired.lower()
    assert validation["fabricated_authority_detected"] is True
    assert "records show" not in low
    assert "captain verrick" not in low
    assert "no name" in low or "don't know the name" in low
    assert "remove_fabricated_authority" in meta["fallback_behavior_repair_mode"]
    assert meta["fallback_behavior_partial_used"] is True


@pytest.mark.parametrize(
    ("source", "raw", "forbidden", "expected"),
    [
        pytest.param(
            "unknown_identity",
            "The culprit was Captain Verrick. Check the ward clerk at the east gate office.",
            "captain verrick",
            ("no name", "don't know the name"),
            marks=pytest.mark.xfail(reason="current identity repair still preserves unsupported named culprit text"),
        ),
        (
            "unknown_location",
            "They are under Dock Seven. Check the harbor watch by the customs arch.",
            "dock seven",
            ("nothing in sight pins the place down", "don't know where"),
        ),
        (
            "unknown_motive",
            "He did it because he owed the Syndicate. Ask the bookkeeper about the debt ledger.",
            "owed the syndicate",
            ("they give nothing away about why", "don't know why", "guarded look"),
        ),
        (
            "unknown_feasibility",
            "It is safe. Check the patrol map at the watchhouse.",
            "it is safe",
            ("no one commits themselves at once", "does not answer at once", "gives you nothing yet"),
        ),
    ],
)
def test_repair_downgrades_unsupported_certainty_into_bounded_partial(
    source: str,
    raw: str,
    forbidden: str,
    expected: tuple[str, ...],
) -> None:
    repaired, meta, _ = _repair(raw, _fallback_contract(uncertainty_sources=[source]))

    low = repaired.lower()
    assert forbidden not in low
    assert any(fragment in low for fragment in expected)
    _assert_no_meta_bits(repaired)
    assert meta["fallback_behavior_partial_used"] is True
    assert "bounded_partial" in meta["fallback_behavior_repair_mode"]


def test_repair_preserves_known_edge_when_one_exists() -> None:
    repaired, meta, _ = _repair(
        "They crossed through the east market before they vanished. They are under Dock Seven.",
        _fallback_contract(
            uncertainty_sources=["unknown_location"],
            require_partial_to_offer_next_lead=False,
        ),
    )

    low = repaired.lower()
    assert "east market" in low
    assert "dock seven" not in low
    assert meta["fallback_behavior_known_edge_preserved"] is True


def test_repair_adds_unknown_edge_when_contract_requires_it() -> None:
    repaired, meta, _ = _repair(
        "Check the ward clerk at the east gate office.",
        _fallback_contract(require_partial_to_offer_next_lead=False),
    )

    low = repaired.lower()
    assert "ward clerk" in low
    assert "hearsay" in low or "unclear" in low or "no name" in low or "don't know the name" in low
    assert meta["fallback_behavior_unknown_edge_added"] is True


def test_repair_rewrites_reason_is_still_unclear_into_diegetic_social_partial() -> None:
    contract = _fallback_contract(
        uncertainty_sources=["unknown_motive"],
        require_partial_to_state_known_edge=False,
        require_partial_to_offer_next_lead=False,
    )
    resolution = {
        "kind": "question",
        "prompt": "I offer the tavern runner a copper for the story.",
        "social": {
            "npc_id": "runner",
            "npc_name": "The Tavern Runner",
            "social_intent_class": "social_exchange",
        },
    }
    validation = validate_fallback_behavior("The reason is still unclear.", contract, resolution=resolution)
    repaired, meta, _ = repair_fallback_behavior(
        "The reason is still unclear.",
        contract,
        validation,
        resolution=resolution,
    )
    revalidated = validate_fallback_behavior(repaired, contract, resolution=resolution)

    low = repaired.lower()
    assert validation["meta_fallback_voice_detected"] is True
    assert ("eyes the copper" in low or "does not answer at once" in low or "guarded look" in low)
    _assert_no_meta_bits(repaired)
    assert meta["fallback_behavior_repaired"] is True
    assert "rewrite_meta_as_diegetic_partial" in meta["fallback_behavior_repair_mode"]
    assert revalidated["passed"] is True


def test_repair_rewrites_move_plays_out_line_into_diegetic_open_call_partial() -> None:
    contract = _fallback_contract(
        uncertainty_sources=["unknown_feasibility"],
        require_partial_to_state_known_edge=False,
        require_partial_to_offer_next_lead=False,
    )
    resolution = {
        "kind": "question",
        "prompt": "Anyone willing to talk if I toss a copper into the crowd?",
        "social": {
            "social_intent_class": "open_call",
        },
    }
    validation = validate_fallback_behavior(
        "That is not settled until the move plays out.",
        contract,
        resolution=resolution,
    )
    repaired, meta, _ = repair_fallback_behavior(
        "That is not settled until the move plays out.",
        contract,
        validation,
        resolution=resolution,
    )
    revalidated = validate_fallback_behavior(repaired, contract, resolution=resolution)

    low = repaired.lower()
    assert validation["meta_fallback_voice_detected"] is True
    assert ("no one answers at once" in low or "glance over" in low or "heads turn toward the copper" in low)
    _assert_no_meta_bits(repaired)
    assert meta["fallback_behavior_repaired"] is True
    assert "rewrite_meta_as_diegetic_partial" in meta["fallback_behavior_repair_mode"]
    assert revalidated["passed"] is True


@pytest.mark.xfail(reason="current identity repair path does not re-append the grounded lead after culprit downgrading")
def test_repair_adds_next_lead_when_contract_requires_it_and_grounded_lead_exists() -> None:
    repaired, meta, _ = _repair("The culprit was Captain Verrick. Ask the ward clerk.")

    assert "ward clerk" in repaired.lower()
    assert meta["fallback_behavior_next_lead_added"] is True


def test_repair_uses_a_single_diegetic_clarifying_question_only_when_partial_cannot_be_preserved() -> None:
    repaired, meta, validation = _repair(
        "I don't have enough information to answer confidently.",
        _fallback_contract(
            allowed_behaviors={
                "ask_clarifying_question": True,
                "hedge_appropriately": False,
                "provide_partial_information": False,
            },
            prefer_partial_over_question=False,
            require_partial_to_state_known_edge=False,
            require_partial_to_state_unknown_edge=False,
            require_partial_to_offer_next_lead=False,
        ),
    )

    assert validation["passed"] is False
    assert repaired == "Which one do you mean?"
    assert meta["fallback_behavior_clarifying_question_used"] is True
    assert meta["fallback_behavior_partial_used"] is False
    assert "clarifying_question" in meta["fallback_behavior_repair_mode"]


def test_repair_never_emits_more_than_one_brief_clarifying_question_when_capped() -> None:
    contract = _fallback_contract(
        allowed_behaviors={
            "ask_clarifying_question": True,
            "hedge_appropriately": False,
            "provide_partial_information": False,
        },
        prefer_partial_over_question=False,
        require_partial_to_state_known_edge=False,
        require_partial_to_state_unknown_edge=False,
        require_partial_to_offer_next_lead=False,
    )
    repaired, meta, _ = _repair(
        "Which one do you mean? Which place are you asking about?",
        contract,
    )
    revalidated = validate_fallback_behavior(repaired, contract)

    assert repaired.count("?") == 1
    assert revalidated["question_count"] == 1
    assert revalidated["passed"] is True
    assert meta["fallback_behavior_clarifying_question_used"] is True
