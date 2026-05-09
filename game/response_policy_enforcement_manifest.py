"""Declarative split-readiness map for response policy enforcement.

This module is intentionally metadata-only. It is not imported by runtime
enforcement code and must not call into ``game.gm`` helpers.
"""
from __future__ import annotations

from dataclasses import dataclass

METADATA_ONLY_PROJECTION = "metadata-only projection"
VALIDATION_ONLY = "validation-only"
TEXT_MUTATING_ENFORCEMENT = "text-mutating enforcement"
FALLBACK_PROVENANCE_RELEVANT_MUTATION = "fallback/provenance-relevant mutation"
LEGACY_AMBIGUOUS = "legacy/ambiguous"

RESPONSE_POLICY_ENFORCEMENT_CLASSIFICATIONS: tuple[str, ...] = (
    METADATA_ONLY_PROJECTION,
    VALIDATION_ONLY,
    TEXT_MUTATING_ENFORCEMENT,
    FALLBACK_PROVENANCE_RELEVANT_MUTATION,
    LEGACY_AMBIGUOUS,
)


@dataclass(frozen=True)
class ResponsePolicyEnforcementSubpath:
    key: str
    category: str
    policy_key: str
    helper_names: tuple[str, ...]
    mutates_player_facing_text: bool
    notes: str


REQUIRED_RESPONSE_POLICY_ENFORCEMENT_SUBPATHS: tuple[str, ...] = (
    "fallback_behavior_contract",
    "question_resolution_enforcement",
    "npc_response_contract_enforcement",
    "validator_voice_rewrite",
    "forbidden_generic_phrase_rewrite",
    "scene_momentum_passive_escalation",
    "social_response_structure_handling",
)


RESPONSE_POLICY_ENFORCEMENT_SUBPATHS: tuple[ResponsePolicyEnforcementSubpath, ...] = (
    ResponsePolicyEnforcementSubpath(
        key="fallback_behavior_contract",
        category=METADATA_ONLY_PROJECTION,
        policy_key="fallback_behavior",
        helper_names=(),
        mutates_player_facing_text=False,
        notes=(
            "Projects response_policy.fallback_behavior into metadata.emission_debug after "
            "enforcement passes complete."
        ),
    ),
    ResponsePolicyEnforcementSubpath(
        key="question_resolution_enforcement",
        category=TEXT_MUTATING_ENFORCEMENT,
        policy_key="must_answer",
        helper_names=("enforce_question_resolution_rule",),
        mutates_player_facing_text=True,
        notes=(
            "Prepends/appends grounded uncertainty answer text when a direct question was not "
            "answered; skipped for strict social emission turns."
        ),
    ),
    ResponsePolicyEnforcementSubpath(
        key="npc_response_contract_enforcement",
        category=TEXT_MUTATING_ENFORCEMENT,
        policy_key="prefer_specificity",
        helper_names=("enforce_npc_response_contract",),
        mutates_player_facing_text=True,
        notes=(
            "Adds a deterministic concrete next-step sentence when an NPC question response lacks "
            "required specificity; skipped for strict social emission turns."
        ),
    ),
    ResponsePolicyEnforcementSubpath(
        key="validator_voice_rewrite",
        category=FALLBACK_PROVENANCE_RELEVANT_MUTATION,
        policy_key="diegetic_only",
        helper_names=("enforce_no_validator_voice",),
        mutates_player_facing_text=True,
        notes=(
            "Removes validator/system voice. Direct-question rewrites route through uncertainty "
            "fallback rendering; non-question rewrites may use a world fallback line."
        ),
    ),
    ResponsePolicyEnforcementSubpath(
        key="forbidden_generic_phrase_rewrite",
        category=TEXT_MUTATING_ENFORCEMENT,
        policy_key="prefer_specificity",
        helper_names=("enforce_forbidden_generic_phrases",),
        mutates_player_facing_text=True,
        notes=(
            "Rewrites forbidden stock phrases into scene-anchored specificity using visible "
            "facts and known NPC names."
        ),
    ),
    ResponsePolicyEnforcementSubpath(
        key="scene_momentum_passive_escalation",
        category=FALLBACK_PROVENANCE_RELEVANT_MUTATION,
        policy_key="prefer_scene_momentum",
        helper_names=(
            "enforce_topic_pressure_escalation",
            "escalate_passive_scene",
            "enforce_scene_momentum",
        ),
        mutates_player_facing_text=True,
        notes=(
            "May append or replace text with topic pressure, passive pressure, or deterministic "
            "scene momentum fallback beats; skipped for strict social emission turns."
        ),
    ),
    ResponsePolicyEnforcementSubpath(
        key="social_response_structure_handling",
        category=LEGACY_AMBIGUOUS,
        policy_key="strict_social_emission_will_apply",
        helper_names=("strict_social_emission_will_apply",),
        mutates_player_facing_text=False,
        notes=(
            "This function does not enforce social response structure directly. It detects strict "
            "social turns and bypasses most text-mutating policy helpers so social exchange "
            "emission owns that structure elsewhere."
        ),
    ),
    ResponsePolicyEnforcementSubpath(
        key="state_update_validation",
        category=VALIDATION_ONLY,
        policy_key="forbid_state_invention",
        helper_names=("validate_gm_state_update",),
        mutates_player_facing_text=False,
        notes="Normalizes proposed state/update payloads and does not author player-facing prose.",
    ),
    ResponsePolicyEnforcementSubpath(
        key="secret_leak_guard",
        category=FALLBACK_PROVENANCE_RELEVANT_MUTATION,
        policy_key="forbid_secret_leak",
        helper_names=("guard_gm_output",),
        mutates_player_facing_text=True,
        notes=(
            "Sanitizes spoiler/secret leakage and may replace player-facing text with bounded "
            "uncertainty output; skipped for strict social emission turns."
        ),
    ),
    ResponsePolicyEnforcementSubpath(
        key="topic_progress_commit",
        category=METADATA_ONLY_PROJECTION,
        policy_key="post_enforcement",
        helper_names=("_commit_topic_progress",),
        mutates_player_facing_text=False,
        notes="Updates topic-progress tracking from the final enforced reply text.",
    ),
    ResponsePolicyEnforcementSubpath(
        key="policy_snapshot_and_applied_marker",
        category=METADATA_ONLY_PROJECTION,
        policy_key="post_enforcement",
        helper_names=(),
        mutates_player_facing_text=False,
        notes="Stores response_policy and marks metadata.response_policy_enforcement_applied.",
    ),
)


def response_policy_enforcement_subpath_keys() -> tuple[str, ...]:
    return tuple(item.key for item in RESPONSE_POLICY_ENFORCEMENT_SUBPATHS)


# Contract guard (Blocks U–X): these ``game.gm`` symbols must remain importable;
# tests assert presence + orchestration order. Do not rename without updating tests/docs.
RESPONSE_POLICY_ENFORCEMENT_CONTRACT_HELPER_NAMES: tuple[str, ...] = (
    "_normalize_response_policy_input",
    "_scene_id_from_scene_envelope",
    "_init_response_policy_enforcement_state",
    "_apply_forbid_state_invention_validation",
    "_project_fallback_behavior_contract_metadata",
    "_snapshot_response_policy_and_project_fallback_contract",
    "_mark_response_policy_enforcement_applied",
    "_apply_must_answer_question_resolution_enforcement",
    "_apply_diegetic_validator_voice_enforcement",
    "_apply_prefer_specificity_text_enforcement",
    "_apply_forbid_secret_leak_guard",
    "_apply_topic_pressure_escalation_enforcement",
    "_apply_escalate_passive_scene_enforcement",
    "_apply_scene_momentum_enforcement",
    "_commit_topic_progress_after_enforcement",
)

# Expected invocation order when every orchestrated branch is enabled (strict-social off).
# Mirrors ``apply_response_policy_enforcement`` + ``RESPONSE_RULE_PRIORITY`` handling.
RESPONSE_POLICY_ENFORCEMENT_ORCHESTRATION_SEQUENCE_FULL_POLICY: tuple[str, ...] = (
    "_init_response_policy_enforcement_state",
    "_apply_must_answer_question_resolution_enforcement",
    "_apply_forbid_state_invention_validation",
    "_apply_forbid_secret_leak_guard",
    "_apply_diegetic_validator_voice_enforcement",
    "_apply_topic_pressure_escalation_enforcement",
    "_apply_escalate_passive_scene_enforcement",
    "_apply_scene_momentum_enforcement",
    "_apply_prefer_specificity_text_enforcement",
    "_commit_topic_progress_after_enforcement",
    "_snapshot_response_policy_and_project_fallback_contract",
    "_mark_response_policy_enforcement_applied",
)
