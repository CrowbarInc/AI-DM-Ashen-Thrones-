"""Practical primary direct-owner suite for ``game.final_emission_repairs``.

This file owns direct helper/accessor semantics, repair materialization behavior, and
owner-level fallback/social-response-structure repair assertions. Downstream
fallback/gate/compatibility suites should consume repaired outputs and metadata
without re-owning helper semantics here.
"""

# === PRACTICAL OWNER SUITE ===
# This file is the canonical test home for:
# - repair derivation logic
# - helper/accessor semantics
# - repair materialization behavior
#
# All other suites must consume repaired outputs without re-owning logic.

from __future__ import annotations

import pytest

import game.final_emission_repairs as fer
from game.final_emission_repairs import (
    _collapse_multi_speaker_formatting,
    _flatten_list_like_dialogue,
)
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
    repaired, meta, _ = fer.repair_fallback_behavior(text, ctr, validation)
    return repaired, meta, validation


def _assert_no_meta_bits(text: str) -> None:
    low = text.lower()
    for bit in _FORBIDDEN_META_BITS:
        assert bit not in low


def test_repair_flattens_list_like_dialogue():
    raw = '- The east gate lies two hundred feet south along the market road.\n- Patrols chart that lane nightly.'
    out = _flatten_list_like_dialogue(raw)
    assert "- " not in out
    assert "east gate" in out.lower()
    assert "patrols" in out.lower()


def test_repair_collapses_multi_speaker_formatting():
    raw = (
        'Alice: "Short nod toward the east gate."\n'
        'Bob: "Patrols hold that lane until dusk, and the sergeant files tallies by lantern light."'
    )
    out = _collapse_multi_speaker_formatting(raw)
    assert "Alice:" not in out
    assert "Bob:" not in out
    assert "patrols" in out.lower()
    assert "sergeant" in out.lower()


def test_removed_semantic_dialogue_helpers_not_exported_from_repairs_module() -> None:
    for name in (
        "_merge_substantive_paragraphs",
        "_normalize_dialogue_cadence",
        "_restore_spoken_opening",
        "_smooth_repaired_fallback_line",
        "_synthesize_next_lead_phrase",
    ):
        assert not hasattr(fer, name), f"expected {name} removed from final_emission_repairs"


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
    assert meta["fallback_behavior_partial_used"] is False
    assert meta["final_emission_boundary_semantic_repair_disabled"] is True
    assert meta["final_emission_semantic_repair_skipped"] is True
    assert meta["final_emission_semantic_repair_skip_reason"] == (
        "repair_fallback_behavior_strip_only_no_template_synthesis"
    )
    assert "strip_meta_voice" in meta["fallback_behavior_repair_mode"]
    assert "bounded_partial" not in meta["fallback_behavior_repair_mode"]


def test_repair_removes_fabricated_authority_without_inventing_replacement_facts() -> None:
    """Strip-only: remove fabricated-authority framing; unsupported named claims stay for upstream."""
    repaired, meta, validation = _repair("The records show the culprit was Captain Verrick.")

    low = repaired.lower()
    assert validation["fabricated_authority_detected"] is True
    assert "records show" not in low
    assert "remove_fabricated_authority" in meta["fallback_behavior_repair_mode"]
    assert meta["fallback_behavior_partial_used"] is False
    assert meta.get("fallback_behavior_boundary_semantic_synthesis_skipped") is True


@pytest.mark.skip(reason="C2 Block C: fallback_behavior no longer synthesizes bounded-partial prose at the boundary")
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


@pytest.mark.skip(reason="C2 Block C: boundary no longer reshapes known/unknown edges via synthesis")
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


@pytest.mark.skip(reason="C2 Block C: boundary no longer injects unknown-edge template phrases")
def test_repair_adds_unknown_edge_when_contract_requires_it() -> None:
    repaired, meta, _ = _repair(
        "Check the ward clerk at the east gate office.",
        _fallback_contract(require_partial_to_offer_next_lead=False),
    )

    low = repaired.lower()
    assert "ward clerk" in low
    assert "hearsay" in low or "unclear" in low or "no name" in low or "don't know the name" in low
    assert meta["fallback_behavior_unknown_edge_added"] is True


@pytest.mark.skip(reason="C2 Block C: meta-voice diegetic rewrite removed from boundary fallback repair")
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
    repaired, meta, _ = fer.repair_fallback_behavior(
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


@pytest.mark.skip(reason="C2 Block C: meta-voice diegetic rewrite removed from boundary fallback repair")
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
    repaired, meta, _ = fer.repair_fallback_behavior(
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


@pytest.mark.skip(reason="C2 Block C: boundary no longer appends synthesized next-lead tails")
def test_repair_adds_next_lead_when_contract_requires_it_and_grounded_lead_exists() -> None:
    repaired, meta, _ = _repair("The culprit was Captain Verrick. Ask the ward clerk.")

    assert "ward clerk" in repaired.lower()
    assert meta["fallback_behavior_next_lead_added"] is True


@pytest.mark.skip(reason="C2 Block C: boundary no longer mints clarifying-question replacement text")
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


@pytest.mark.skip(reason="C2 Block C: boundary no longer collapses clarifying-question shapes")
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


def test_fallback_behavior_layer_revalidates_once_after_repair(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    orig_validate = fer.validate_fallback_behavior

    def spy_validate(*args, **kwargs):
        calls.append(str(args[0]))
        return orig_validate(*args, **kwargs)

    monkeypatch.setattr(fer, "validate_fallback_behavior", spy_validate)

    text, meta, extra = fer._apply_fallback_behavior_layer(
        "I don't have enough information to answer confidently. Check the ward clerk at the east gate office.",
        gm_output={"response_policy": {"fallback_behavior": _fallback_contract()}},
        resolution={"kind": "adjudication_query", "prompt": "No. Exactly who?"},
        strict_social_path=False,
    )

    assert len(calls) == 2
    assert calls[0].startswith("I don't have enough information")
    assert calls[1] == text
    assert meta["fallback_behavior_repaired"] is True
    assert meta["fallback_behavior_failed"] in (True, False)


@pytest.mark.skip(reason="C2 Block C: boundary strip-only cannot satisfy missing_allowed_fallback_shape without upstream synthesis")
def test_fallback_behavior_layer_retains_safest_repaired_text_when_revalidation_still_fails() -> None:
    text, meta, extra = fer._apply_fallback_behavior_layer(
        "They are under Dock Seven by the customs gate.",
        gm_output={
            "response_policy": {
                "fallback_behavior": _fallback_contract(
                    uncertainty_sources=["unknown_location"],
                    require_partial_to_state_known_edge=False,
                    require_partial_to_offer_next_lead=True,
                )
            }
        },
        resolution={"kind": "adjudication_query", "prompt": "No. Exactly who?"},
        strict_social_path=False,
    )

    low = text.lower()
    assert "dock seven" not in low
    assert "exact place is still unclear" in low or "don't know where" in low
    assert meta.get("fallback_behavior_repaired") is True
    assert meta.get("fallback_behavior_failed") is True
    assert meta.get("fallback_behavior_failure_reasons") == ["missing_allowed_fallback_shape"]
    assert extra == []


@pytest.mark.parametrize(
    ("raw", "prompt"),
    [
        ("The culprit was Captain Verrick at the gate.", "Who did it?"),
        ("They are at Dock Seven near the customs gate.", "Which dock exactly?"),
        ("There were 3 guards in the yard.", "How many were there?"),
    ],
)
def test_fallback_behavior_layer_leaves_grounded_answers_untouched_when_uncertainty_is_inactive(
    raw: str,
    prompt: str,
) -> None:
    text, meta, extra = fer._apply_fallback_behavior_layer(
        raw,
        gm_output={"response_policy": {"fallback_behavior": _fallback_contract(uncertainty_active=False)}},
        resolution={"kind": "adjudication_query", "prompt": prompt},
        strict_social_path=False,
    )

    assert text == raw
    assert meta.get("fallback_behavior_repaired") is False
    assert meta.get("fallback_behavior_skip_reason") == "uncertainty_inactive"
    assert extra == []


def test_fallback_behavior_layer_does_not_synthesize_without_contract_from_forceful_tone_alone() -> None:
    raw = "He slams a finger onto the patrol map and marks Dock Seven by the east gate."
    text, meta, extra = fer._apply_fallback_behavior_layer(
        raw,
        gm_output={},
        resolution={"kind": "adjudication_query", "prompt": "Which dock exactly?"},
        strict_social_path=False,
    )

    assert text == raw
    assert meta.get("fallback_behavior_contract_present") is False
    assert meta.get("fallback_behavior_checked") is False
    assert meta.get("fallback_behavior_skip_reason") == "no_contract"
    assert extra == []
