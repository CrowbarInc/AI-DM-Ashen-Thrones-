"""Tests for the declarative Narrative Realization authority ledger."""
from __future__ import annotations

import pytest

from game.realization_authority import (
    AUTHORITY_PROFILES,
    FALLBACK_FAMILIES,
    LEGACY,
    SAFE,
    SUSPICIOUS,
    fallback_family_owner,
    fallback_family_requires_metadata,
    get_authority_profile,
    get_fallback_family,
    known_authority_profile,
    known_fallback_family,
)

pytestmark = pytest.mark.unit

REQUIRED_AUTHORITY_PROFILES = {
    "gpt_realization",
    "prompt_context",
    "final_emission_gate",
    "gm_retry",
    "upstream_prepared_emission",
    "diegetic_fallback_narration",
    "api_emergency_realization",
}

REQUIRED_FALLBACK_FAMILIES = {
    "plan_backed_gpt_realization",
    "upstream_prepared_emission",
    "strict_social_deterministic_fallback",
    "planner_convergence_seam_failure",
    "gpt_budget_or_provider_failure",
    "retry_terminal_fallback",
    "gate_terminal_repair",
    "legacy_diegetic_fallback",
    "legacy_unclassified",
}


def _joined(values: tuple[str, ...]) -> str:
    return " | ".join(values).lower()


def test_all_required_authority_profiles_exist() -> None:
    assert REQUIRED_AUTHORITY_PROFILES <= set(AUTHORITY_PROFILES)
    for name in REQUIRED_AUTHORITY_PROFILES:
        profile = get_authority_profile(name)
        assert profile.layer_name == name
        assert known_authority_profile(name) is True


def test_all_required_fallback_families_exist() -> None:
    assert REQUIRED_FALLBACK_FAMILIES <= set(FALLBACK_FAMILIES)
    for name in REQUIRED_FALLBACK_FAMILIES:
        family = get_fallback_family(name)
        assert family.owner_profile in AUTHORITY_PROFILES
        assert known_fallback_family(name) is True


def test_gpt_allowed_authority_does_not_contain_truth_state_or_consequence_concepts() -> None:
    allowed = get_authority_profile("gpt_realization").allowed_authority
    assert allowed == (
        "wording",
        "cadence",
        "style",
        "sentence ordering within supplied constraints",
        "sensory presentation from supplied visible anchors",
        "dialogue form within supplied speaker and response contracts",
    )
    lowered = _joined(allowed)
    forbidden_fragments = ("truth", "state", "consequence", "fact", "lead", "outcome")
    for fragment in forbidden_fragments:
        assert fragment not in lowered


def test_gpt_forbidden_authority_includes_semantic_invention_concepts() -> None:
    forbidden = _joined(get_authority_profile("gpt_realization").forbidden_authority)
    for fragment in (
        "new facts",
        "new consequences",
        "new leads",
        "npc motives",
        "npc knowledge",
        "hidden information",
        "forced player actions",
        "clue meaning",
        "scene transitions",
        "fallback facts",
        "legality verdicts",
        "state mutation",
    ):
        assert fragment in forbidden


def test_prompt_context_forbidden_authority_includes_reconstruct_infer_repair_decide() -> None:
    forbidden = _joined(get_authority_profile("prompt_context").forbidden_authority)
    for fragment in ("reconstruct", "infer", "repair", "decide"):
        assert fragment in forbidden


def test_final_emission_gate_forbidden_authority_names_semantic_reconstruction() -> None:
    forbidden = _joined(get_authority_profile("final_emission_gate").forbidden_authority)
    for fragment in (
        "invent missing semantics",
        "reinterpret planner obligations",
        "compose opening fallback prose from raw state",
    ):
        assert fragment in forbidden


def test_every_player_facing_fallback_family_requires_provenance_metadata() -> None:
    for name, family in FALLBACK_FAMILIES.items():
        if family.may_emit_player_facing_text:
            assert fallback_family_requires_metadata(name) is True


def test_legacy_unclassified_exists() -> None:
    family = get_fallback_family("legacy_unclassified")
    assert family.classification != SAFE
    assert family.may_emit_player_facing_text is False


def test_legacy_diegetic_fallback_is_not_safe() -> None:
    family = get_fallback_family("legacy_diegetic_fallback")
    assert family.classification in (LEGACY, SUSPICIOUS)
    assert family.classification != SAFE


def test_upstream_prepared_emission_is_not_owned_by_final_emission_gate() -> None:
    assert fallback_family_owner("upstream_prepared_emission") == "upstream_prepared_emission"
    assert fallback_family_owner("upstream_prepared_emission") != "final_emission_gate"


def test_gate_terminal_repair_is_terminal_and_sealed_only() -> None:
    family = get_fallback_family("gate_terminal_repair")
    allowed = family.allowed_use_summary.lower()
    forbidden = family.forbidden_use_summary.lower()
    assert "terminal" in allowed
    assert "sealed" in allowed
    assert "only" in allowed
    assert "non-terminal" in forbidden
    assert "compose" in forbidden
    assert "reinterpret" in forbidden
