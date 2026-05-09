"""Canonical Narrative Realization / Prompt Realization authority ledger.

This module is intentionally declarative. It does not wire into runtime behavior,
construct prompts, or import production realization paths. The ledger names what
each layer may do with already-authorized Planner/CTIR content.
"""
from __future__ import annotations

from dataclasses import dataclass

SAFE = "SAFE"
BOUNDED = "BOUNDED"
SUSPICIOUS = "SUSPICIOUS"
LEGACY = "LEGACY"
UNKNOWN = "UNKNOWN"

FALLBACK_CLASSIFICATIONS: tuple[str, ...] = (
    SAFE,
    BOUNDED,
    SUSPICIOUS,
    LEGACY,
    UNKNOWN,
)


@dataclass(frozen=True)
class AuthorityProfile:
    layer_name: str
    allowed_authority: tuple[str, ...]
    forbidden_authority: tuple[str, ...]
    may_emit_player_facing_text: bool
    may_create_fallback_prose: bool
    may_read_raw_state_after_planner: bool
    requires_provenance_metadata: bool
    notes: str


@dataclass(frozen=True)
class FallbackFamily:
    owner_profile: str
    may_emit_player_facing_text: bool
    may_read_raw_state_after_planner: bool
    requires_provenance_metadata: bool
    classification: str
    allowed_use_summary: str
    forbidden_use_summary: str


GPT_REALIZATION_ALLOWED_AUTHORITY: tuple[str, ...] = (
    "wording",
    "cadence",
    "style",
    "sentence ordering within supplied constraints",
    "sensory presentation from supplied visible anchors",
    "dialogue form within supplied speaker and response contracts",
)

GPT_REALIZATION_FORBIDDEN_AUTHORITY: tuple[str, ...] = (
    "new facts",
    "new consequences",
    "new leads",
    "NPC motives not supplied",
    "NPC knowledge not supplied",
    "hidden information",
    "forced player actions",
    "clue meaning not supplied",
    "scene transitions not supplied",
    "fallback facts",
    "legality verdicts",
    "state mutation",
)

PROMPT_CONTEXT_ALLOWED_AUTHORITY: tuple[str, ...] = (
    "package approved artifacts",
    "format public prompt payload",
    "clip context windows",
    "attach debug metadata",
    "ship Planner/CTIR-derived contracts",
)

PROMPT_CONTEXT_FORBIDDEN_AUTHORITY: tuple[str, ...] = (
    "build narrative plans",
    "reconstruct scene semantics",
    "infer answer content",
    "invent opening prose",
    "create fallback exposition",
    "repair missing semantic structure",
    "decide response type",
)

FINAL_EMISSION_GATE_ALLOWED_AUTHORITY: tuple[str, ...] = (
    "validate deterministic legality constraints",
    "strip or block forbidden output",
    "select upstream-prepared emission when explicitly present",
    "apply sealed deterministic terminal fallback when registered",
    "attach legality/failure metadata",
)

FINAL_EMISSION_GATE_FORBIDDEN_AUTHORITY: tuple[str, ...] = (
    "improve prose for style",
    "invent missing semantics",
    "create new narrative beats",
    "reinterpret Planner obligations",
    "convert invalid GPT output into new story content",
    "compose opening fallback prose from raw state unless explicitly authorized",
)


AUTHORITY_PROFILES: dict[str, AuthorityProfile] = {
    "gpt_realization": AuthorityProfile(
        layer_name="gpt_realization",
        allowed_authority=GPT_REALIZATION_ALLOWED_AUTHORITY,
        forbidden_authority=GPT_REALIZATION_FORBIDDEN_AUTHORITY,
        may_emit_player_facing_text=True,
        may_create_fallback_prose=False,
        may_read_raw_state_after_planner=False,
        requires_provenance_metadata=True,
        notes=(
            "May turn supplied Planner/CTIR contracts into prose. It owns phrasing, not truth, "
            "state, legality, consequences, or fallback semantics."
        ),
    ),
    "prompt_context": AuthorityProfile(
        layer_name="prompt_context",
        allowed_authority=PROMPT_CONTEXT_ALLOWED_AUTHORITY,
        forbidden_authority=PROMPT_CONTEXT_FORBIDDEN_AUTHORITY,
        may_emit_player_facing_text=False,
        may_create_fallback_prose=False,
        may_read_raw_state_after_planner=False,
        requires_provenance_metadata=True,
        notes=(
            "Packages approved artifacts for the public prompt. It must not infer missing "
            "meaning or decide narrative obligations."
        ),
    ),
    "final_emission_gate": AuthorityProfile(
        layer_name="final_emission_gate",
        allowed_authority=FINAL_EMISSION_GATE_ALLOWED_AUTHORITY,
        forbidden_authority=FINAL_EMISSION_GATE_FORBIDDEN_AUTHORITY,
        may_emit_player_facing_text=True,
        may_create_fallback_prose=False,
        may_read_raw_state_after_planner=False,
        requires_provenance_metadata=True,
        notes=(
            "Validates and selects already-authorized text. Terminal fallback authority is "
            "limited to registered sealed deterministic text."
        ),
    ),
    "gm_retry": AuthorityProfile(
        layer_name="gm_retry",
        allowed_authority=(
            "retry using existing Planner/CTIR contracts",
            "preserve original obligations",
            "report retry failure metadata",
            "select registered retry terminal fallback",
        ),
        forbidden_authority=(
            "invent retry-only facts",
            "weaken Planner obligations",
            "replace missing answer semantics",
            "create unregistered terminal prose",
            "mutate state to satisfy failed narration",
        ),
        may_emit_player_facing_text=True,
        may_create_fallback_prose=False,
        may_read_raw_state_after_planner=False,
        requires_provenance_metadata=True,
        notes=(
            "Retry may re-attempt realization or select a registered terminal fallback. It "
            "does not become a second planner."
        ),
    ),
    "upstream_prepared_emission": AuthorityProfile(
        layer_name="upstream_prepared_emission",
        allowed_authority=(
            "emit Planner-backed prepared text",
            "carry explicit fallback provenance",
            "preserve supplied semantic scope",
            "satisfy registered response contracts",
        ),
        forbidden_authority=(
            "expand beyond prepared semantic scope",
            "hide fallback provenance",
            "override gate legality rejection",
            "invent unresolved consequences",
        ),
        may_emit_player_facing_text=True,
        may_create_fallback_prose=True,
        may_read_raw_state_after_planner=False,
        requires_provenance_metadata=True,
        notes=(
            "Owns prepared player-facing emission only when upstream planning explicitly "
            "authorized the text and its fallback scope."
        ),
    ),
    "diegetic_fallback_narration": AuthorityProfile(
        layer_name="diegetic_fallback_narration",
        allowed_authority=(
            "legacy bounded fallback rendering",
            "surface uncertainty without new facts",
            "preserve player agency",
            "attach fallback provenance",
        ),
        forbidden_authority=(
            "invent scene facts from raw state",
            "resolve hidden knowledge",
            "create new leads",
            "supply clue meaning",
            "mask legacy fallback as plan-backed narration",
        ),
        may_emit_player_facing_text=True,
        may_create_fallback_prose=True,
        may_read_raw_state_after_planner=True,
        requires_provenance_metadata=True,
        notes=(
            "Legacy fallback renderers are tolerated only as classified fallback seams and "
            "should be retired or narrowed behind explicit plans."
        ),
    ),
    "api_emergency_realization": AuthorityProfile(
        layer_name="api_emergency_realization",
        allowed_authority=(
            "emit sealed emergency failure text",
            "preserve existing public failure context",
            "attach emergency provenance metadata",
            "avoid semantic reconstruction",
        ),
        forbidden_authority=(
            "reconstruct authoritative state",
            "invent opening exposition",
            "create scene transitions",
            "decide action outcome",
            "synthesize fallback facts from raw state",
        ),
        may_emit_player_facing_text=True,
        may_create_fallback_prose=False,
        may_read_raw_state_after_planner=False,
        requires_provenance_metadata=True,
        notes=(
            "Emergency API realization is for explicit failure surfaces only, not narrative "
            "recovery from missing semantics."
        ),
    ),
}


FALLBACK_FAMILIES: dict[str, FallbackFamily] = {
    "plan_backed_gpt_realization": FallbackFamily(
        owner_profile="gpt_realization",
        may_emit_player_facing_text=True,
        may_read_raw_state_after_planner=False,
        requires_provenance_metadata=True,
        classification=SAFE,
        allowed_use_summary=(
            "Realize text from supplied Planner/CTIR obligations and visible anchors."
        ),
        forbidden_use_summary=(
            "Do not add facts, consequences, leads, hidden information, or fallback facts."
        ),
    ),
    "upstream_prepared_emission": FallbackFamily(
        owner_profile="upstream_prepared_emission",
        may_emit_player_facing_text=True,
        may_read_raw_state_after_planner=False,
        requires_provenance_metadata=True,
        classification=BOUNDED,
        allowed_use_summary=(
            "Emit explicitly prepared upstream text with its semantic scope and provenance."
        ),
        forbidden_use_summary=(
            "Do not let final_emission_gate author or expand this text after GPT failure."
        ),
    ),
    "strict_social_deterministic_fallback": FallbackFamily(
        owner_profile="upstream_prepared_emission",
        may_emit_player_facing_text=True,
        may_read_raw_state_after_planner=False,
        requires_provenance_metadata=True,
        classification=BOUNDED,
        allowed_use_summary=(
            "Use registered deterministic social fallback text for tightly scoped social failure."
        ),
        forbidden_use_summary=(
            "Do not answer unsupplied content, infer NPC knowledge, or create new social beats."
        ),
    ),
    "planner_convergence_seam_failure": FallbackFamily(
        owner_profile="api_emergency_realization",
        may_emit_player_facing_text=True,
        may_read_raw_state_after_planner=False,
        requires_provenance_metadata=True,
        classification=SUSPICIOUS,
        allowed_use_summary=(
            "Surface a sealed failure message when planner convergence did not produce "
            "realizable obligations."
        ),
        forbidden_use_summary=(
            "Do not reconstruct the missing plan, infer answer content, or fabricate scene truth."
        ),
    ),
    "gpt_budget_or_provider_failure": FallbackFamily(
        owner_profile="api_emergency_realization",
        may_emit_player_facing_text=True,
        may_read_raw_state_after_planner=False,
        requires_provenance_metadata=True,
        classification=BOUNDED,
        allowed_use_summary=(
            "Use sealed provider/budget failure prose or an explicitly prepared upstream emission."
        ),
        forbidden_use_summary=(
            "Do not compose diegetic story content from raw state to conceal provider failure."
        ),
    ),
    "retry_terminal_fallback": FallbackFamily(
        owner_profile="gm_retry",
        may_emit_player_facing_text=True,
        may_read_raw_state_after_planner=False,
        requires_provenance_metadata=True,
        classification=BOUNDED,
        allowed_use_summary=(
            "After retry exhaustion, select registered terminal fallback text with retry metadata."
        ),
        forbidden_use_summary=(
            "Do not write a new fallback answer or relax obligations because retry failed."
        ),
    ),
    "gate_terminal_repair": FallbackFamily(
        owner_profile="final_emission_gate",
        may_emit_player_facing_text=True,
        may_read_raw_state_after_planner=False,
        requires_provenance_metadata=True,
        classification=BOUNDED,
        allowed_use_summary=(
            "Terminal/sealed only: apply registered sealed deterministic terminal fallback text "
            "after legality failure."
        ),
        forbidden_use_summary=(
            "Not a non-terminal repair path; do not compose, improve, reinterpret, or add story "
            "content at the gate."
        ),
    ),
    "legacy_diegetic_fallback": FallbackFamily(
        owner_profile="diegetic_fallback_narration",
        may_emit_player_facing_text=True,
        may_read_raw_state_after_planner=True,
        requires_provenance_metadata=True,
        classification=LEGACY,
        allowed_use_summary=(
            "Temporarily classify old diegetic fallback renderers while retiring or replacing them."
        ),
        forbidden_use_summary=(
            "Do not treat legacy fallback prose as safe, plan-backed, or free to read raw state."
        ),
    ),
    "legacy_unclassified": FallbackFamily(
        owner_profile="api_emergency_realization",
        may_emit_player_facing_text=False,
        may_read_raw_state_after_planner=False,
        requires_provenance_metadata=False,
        classification=UNKNOWN,
        allowed_use_summary=(
            "Inventory placeholder for seams that have not yet received an authority decision."
        ),
        forbidden_use_summary=(
            "Do not emit player-facing text or ship runtime behavior under this classification."
        ),
    ),
}


def get_authority_profile(name: str) -> AuthorityProfile:
    return AUTHORITY_PROFILES[name]


def get_fallback_family(name: str) -> FallbackFamily:
    return FALLBACK_FAMILIES[name]


def known_authority_profile(name: str) -> bool:
    return name in AUTHORITY_PROFILES


def known_fallback_family(name: str) -> bool:
    return name in FALLBACK_FAMILIES


def fallback_family_requires_metadata(name: str) -> bool:
    return get_fallback_family(name).requires_provenance_metadata


def fallback_family_owner(name: str) -> str:
    return get_fallback_family(name).owner_profile
