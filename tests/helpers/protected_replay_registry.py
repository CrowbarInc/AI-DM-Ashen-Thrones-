"""Explicit protected replay scenario registry for BW corpus discoverability (test-only).

Golden Transcript Drift trend windows should enumerate scenarios from this registry
rather than inferring corpus membership from decomposed module layout alone.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

# BW trend-window dimensions (Golden Transcript Drift readiness).
BW_DIMENSION_ROUTE: Final[str] = "route"
BW_DIMENSION_SPEAKER: Final[str] = "speaker"
BW_DIMENSION_SOURCE: Final[str] = "source"
BW_DIMENSION_OWNER: Final[str] = "owner"
BW_DIMENSION_MUTATION: Final[str] = "mutation"
BW_DIMENSION_FINAL_TEXT: Final[str] = "final_text"

ALL_BW_DIMENSIONS: Final[tuple[str, ...]] = (
    BW_DIMENSION_ROUTE,
    BW_DIMENSION_SPEAKER,
    BW_DIMENSION_SOURCE,
    BW_DIMENSION_OWNER,
    BW_DIMENSION_MUTATION,
    BW_DIMENSION_FINAL_TEXT,
)

STRUCTURAL_INVARIANTS_MODULE: Final[str] = "tests/test_golden_replay_structural_invariants.py"
BX_SPEAKER_PARITY_MODULE: Final[str] = "tests/test_bx_speaker_identity_golden_replay.py"
LONG_SESSION_MODULE: Final[str] = "tests/test_golden_replay_long_session.py"
DIRECT_SEAM_MODULE: Final[str] = "tests/test_golden_replay_direct_seam.py"
SCENARIO_SPINE_MODULE: Final[str] = "tests/test_golden_replay_scenario_spine.py"


class ProtectionStatus(StrEnum):
    PROTECTED = "PROTECTED"
    SUPPORTING = "SUPPORTING"
    ADVISORY = "ADVISORY"
    DEPRECATED = "DEPRECATED"


@dataclass(frozen=True)
class ProtectedReplayScenarioEntry:
    scenario_id: str
    test_module: str
    test_name: str
    protection_status: ProtectionStatus
    bw_dimensions: tuple[str, ...]
    sort_key: str
    category: str = "END_TO_END_PROTECTED"

    @property
    def test_node_id(self) -> str:
        return f"{self.test_module}::{self.test_name}"


_REGISTRY: Final[tuple[ProtectedReplayScenarioEntry, ...]] = tuple(
    sorted(
        (
            ProtectedReplayScenarioEntry(
                scenario_id="directed_npc_question",
                test_module=STRUCTURAL_INVARIANTS_MODULE,
                test_name="test_golden_replay_directed_npc_question_structural_invariants",
                protection_status=ProtectionStatus.PROTECTED,
                bw_dimensions=(
                    BW_DIMENSION_ROUTE,
                    BW_DIMENSION_SPEAKER,
                    BW_DIMENSION_SOURCE,
                    BW_DIMENSION_FINAL_TEXT,
                ),
                sort_key="01_directed_npc_question",
                category="END_TO_END_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="lead_followup_with_dialogue_lock",
                test_module=STRUCTURAL_INVARIANTS_MODULE,
                test_name="test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants",
                protection_status=ProtectionStatus.PROTECTED,
                bw_dimensions=(
                    BW_DIMENSION_ROUTE,
                    BW_DIMENSION_SPEAKER,
                    BW_DIMENSION_SOURCE,
                    BW_DIMENSION_FINAL_TEXT,
                ),
                sort_key="02_lead_followup_with_dialogue_lock",
                category="END_TO_END_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="sanitizer_scaffold_leakage",
                test_module=STRUCTURAL_INVARIANTS_MODULE,
                test_name="test_golden_replay_sanitizer_scaffold_leakage_structural_invariants",
                protection_status=ProtectionStatus.PROTECTED,
                bw_dimensions=(
                    BW_DIMENSION_MUTATION,
                    BW_DIMENSION_FINAL_TEXT,
                ),
                sort_key="03_sanitizer_scaffold_leakage",
                category="END_TO_END_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="thin_answer_action_outcome_final_emission",
                test_module=STRUCTURAL_INVARIANTS_MODULE,
                test_name="test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants",
                protection_status=ProtectionStatus.PROTECTED,
                bw_dimensions=(
                    BW_DIMENSION_MUTATION,
                    BW_DIMENSION_SOURCE,
                    BW_DIMENSION_FINAL_TEXT,
                ),
                sort_key="04_thin_answer_action_outcome_final_emission",
                category="END_TO_END_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="vocative_override_after_prior_continuity",
                test_module=STRUCTURAL_INVARIANTS_MODULE,
                test_name="test_golden_replay_vocative_override_after_prior_continuity_structural_invariants",
                protection_status=ProtectionStatus.PROTECTED,
                bw_dimensions=(
                    BW_DIMENSION_ROUTE,
                    BW_DIMENSION_SPEAKER,
                    BW_DIMENSION_FINAL_TEXT,
                ),
                sort_key="05_vocative_override_after_prior_continuity",
                category="END_TO_END_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="wrong_speaker_strict_social_emission",
                test_module=STRUCTURAL_INVARIANTS_MODULE,
                test_name="test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants",
                protection_status=ProtectionStatus.PROTECTED,
                bw_dimensions=(
                    BW_DIMENSION_SPEAKER,
                    BW_DIMENSION_SOURCE,
                    BW_DIMENSION_FINAL_TEXT,
                ),
                sort_key="06_wrong_speaker_strict_social_emission",
                category="END_TO_END_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="bx5_guard_role_alias_guard_captain",
                test_module=BX_SPEAKER_PARITY_MODULE,
                test_name="test_bx5_protected_golden_role_alias_guard_to_guard_captain",
                protection_status=ProtectionStatus.PROTECTED,
                bw_dimensions=(
                    BW_DIMENSION_ROUTE,
                    BW_DIMENSION_SPEAKER,
                    BW_DIMENSION_FINAL_TEXT,
                ),
                sort_key="07_bx5_guard_role_alias_guard_captain",
                category="BX_SPEAKER_PARITY_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="bx5_guard_canonical_guard_captain",
                test_module=BX_SPEAKER_PARITY_MODULE,
                test_name="test_bx5_protected_golden_canonical_guard_captain",
                protection_status=ProtectionStatus.PROTECTED,
                bw_dimensions=(
                    BW_DIMENSION_ROUTE,
                    BW_DIMENSION_SPEAKER,
                    BW_DIMENSION_FINAL_TEXT,
                ),
                sort_key="08_bx5_guard_canonical_guard_captain",
                category="BX_SPEAKER_PARITY_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="bx5_guard_gate_guard_distinct",
                test_module=BX_SPEAKER_PARITY_MODULE,
                test_name="test_bx5_protected_golden_gate_guard_distinct_from_guard_captain",
                protection_status=ProtectionStatus.PROTECTED,
                bw_dimensions=(
                    BW_DIMENSION_ROUTE,
                    BW_DIMENSION_SPEAKER,
                    BW_DIMENSION_FINAL_TEXT,
                ),
                sort_key="09_bx5_guard_gate_guard_distinct",
                category="BX_SPEAKER_PARITY_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="bx5_guard_ambiguous_multi_guard",
                test_module=BX_SPEAKER_PARITY_MODULE,
                test_name="test_bx5_protected_golden_ambiguous_guard_no_false_parity",
                protection_status=ProtectionStatus.PROTECTED,
                bw_dimensions=(BW_DIMENSION_SPEAKER, BW_DIMENSION_FINAL_TEXT),
                sort_key="10_bx5_guard_ambiguous_multi_guard",
                category="BX_SPEAKER_PARITY_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="declared_alias_dialogue_plan",
                test_module=DIRECT_SEAM_MODULE,
                test_name="test_golden_direct_seam_declared_alias_dialogue_plan_structural_invariants",
                protection_status=ProtectionStatus.SUPPORTING,
                bw_dimensions=(
                    BW_DIMENSION_ROUTE,
                    BW_DIMENSION_SPEAKER,
                    BW_DIMENSION_SOURCE,
                ),
                sort_key="90_declared_alias_dialogue_plan",
                category="DIRECT_SEAM_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="opening_fallback_path",
                test_module=DIRECT_SEAM_MODULE,
                test_name="test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership",
                protection_status=ProtectionStatus.SUPPORTING,
                bw_dimensions=(
                    BW_DIMENSION_SOURCE,
                    BW_DIMENSION_OWNER,
                    BW_DIMENSION_MUTATION,
                ),
                sort_key="91_opening_fallback_path",
                category="DIRECT_SEAM_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="frontier_gate_social_inquiry_25_turn",
                test_module=LONG_SESSION_MODULE,
                test_name="test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability",
                protection_status=ProtectionStatus.SUPPORTING,
                bw_dimensions=ALL_BW_DIMENSIONS,
                sort_key="92_frontier_gate_social_inquiry_25_turn",
                category="END_TO_END_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="frontier_gate_social_inquiry_25_turn_resume_persistence",
                test_module=LONG_SESSION_MODULE,
                test_name="test_golden_replay_frontier_gate_social_inquiry_25_turn_resume_persistence_supporting",
                protection_status=ProtectionStatus.SUPPORTING,
                bw_dimensions=(
                    BW_DIMENSION_ROUTE,
                    BW_DIMENSION_SPEAKER,
                    BW_DIMENSION_SOURCE,
                    BW_DIMENSION_OWNER,
                    BW_DIMENSION_MUTATION,
                ),
                sort_key="93_frontier_gate_social_inquiry_25_turn_resume_persistence",
                category="END_TO_END_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="frontier_gate_direct_intrusion_25_turn",
                test_module=LONG_SESSION_MODULE,
                test_name="test_golden_replay_frontier_gate_direct_intrusion_25_turn_diagnostic_stability",
                protection_status=ProtectionStatus.SUPPORTING,
                bw_dimensions=(
                    BW_DIMENSION_ROUTE,
                    BW_DIMENSION_SPEAKER,
                    BW_DIMENSION_SOURCE,
                    BW_DIMENSION_OWNER,
                    BW_DIMENSION_MUTATION,
                ),
                sort_key="94_frontier_gate_direct_intrusion_25_turn",
                category="END_TO_END_PROTECTED",
            ),
            ProtectedReplayScenarioEntry(
                scenario_id="scenario_spine_three_branch",
                test_module=SCENARIO_SPINE_MODULE,
                test_name="test_golden_replay_scenario_spine_three_branch_structural_smoke",
                protection_status=ProtectionStatus.SUPPORTING,
                bw_dimensions=(
                    BW_DIMENSION_ROUTE,
                    BW_DIMENSION_SPEAKER,
                    BW_DIMENSION_FINAL_TEXT,
                ),
                sort_key="95_scenario_spine_three_branch",
                category="SUPPORTING_REPLAY",
            ),
        ),
        key=lambda entry: entry.sort_key,
    )
)


def protected_replay_registry() -> tuple[ProtectedReplayScenarioEntry, ...]:
    """Return the full replay scenario registry in stable sort-key order."""
    return _REGISTRY


def protected_replay_corpus() -> tuple[ProtectedReplayScenarioEntry, ...]:
    """Return acceptance-blocking protected replay scenarios for BW corpus enumeration."""
    return tuple(
        entry
        for entry in _REGISTRY
        if entry.protection_status is ProtectionStatus.PROTECTED
        and entry.category == "END_TO_END_PROTECTED"
    )


def bx_speaker_parity_corpus() -> tuple[ProtectedReplayScenarioEntry, ...]:
    """Return acceptance-blocking BX guard speaker parity scenarios (separate from BW trend window)."""
    return tuple(
        entry
        for entry in _REGISTRY
        if entry.protection_status is ProtectionStatus.PROTECTED
        and entry.category == "BX_SPEAKER_PARITY_PROTECTED"
    )


def protected_replay_corpus_test_node_ids() -> tuple[str, ...]:
    """Return pytest node IDs for the BW protected replay corpus."""
    return tuple(entry.test_node_id for entry in protected_replay_corpus())


def bx_speaker_parity_corpus_test_node_ids() -> tuple[str, ...]:
    """Return pytest node IDs for the BX speaker parity protected corpus."""
    return tuple(entry.test_node_id for entry in bx_speaker_parity_corpus())


def protected_replay_registry_validation_errors() -> list[str]:
    """Return registry invariant violations; empty when the registry is well-formed."""
    errors: list[str] = []
    entries = protected_replay_registry()
    scenario_ids = [entry.scenario_id for entry in entries]
    if len(scenario_ids) != len(set(scenario_ids)):
        dup = sorted({item for item in scenario_ids if scenario_ids.count(item) > 1})
        errors.append(f"duplicate scenario_id values: {dup!r}")

    node_ids = [entry.test_node_id for entry in entries]
    if len(node_ids) != len(set(node_ids)):
        dup = sorted({item for item in node_ids if node_ids.count(item) > 1})
        errors.append(f"duplicate test_node_id values: {dup!r}")

    sort_keys = [entry.sort_key for entry in entries]
    if sort_keys != sorted(sort_keys):
        errors.append("registry must be sorted by sort_key")

    if len(protected_replay_corpus()) != 6:
        errors.append(
            "protected replay corpus must contain exactly six short structural scenarios; "
            f"found {len(protected_replay_corpus())!r}"
        )

    if len(bx_speaker_parity_corpus()) != 4:
        errors.append(
            "BX speaker parity corpus must contain exactly four guard-matrix scenarios; "
            f"found {len(bx_speaker_parity_corpus())!r}"
        )

    for entry in entries:
        if not entry.bw_dimensions:
            errors.append(f"{entry.scenario_id!r} must declare at least one BW dimension")
        unknown = sorted(set(entry.bw_dimensions) - set(ALL_BW_DIMENSIONS))
        if unknown:
            errors.append(f"{entry.scenario_id!r} declares unknown BW dimensions: {unknown!r}")

    return errors
