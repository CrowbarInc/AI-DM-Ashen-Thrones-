"""Planner input manifest — CTIR-backed narration planning (inspectable inventory).

This module is **documentation + runtime classification helpers only**. It does not
derive narration, mutate session state, or alter prompts.

**Scope:** inputs that feed

- :func:`game.narrative_planning.build_narrative_plan` (narrative plan construction),
- :func:`game.narrative_plan_upstream.compute_narrative_plan_for_bundle_from_head`,
- :func:`game.narration_plan_bundle.build_narration_plan_bundle`, and
- :func:`game.planner_head_state.build_planner_head_state` / planner-facing
  payload slices (see each row’s ``consumer`` field).

``Ownership layer`` is shorthand for who *authors* the datum at the seam (not who
formats it for JSON):

- **Engine** — authoritative simulation / resolution pipeline (bounded exports).
- **Planner** — deterministic structural projection from CTIR + bounded slices.
- **GPT** — model output (must **not** be a planner input on CTIR turns).
- **Gate** — emission / validation downstream of narration (not a planner feed).

**Classification:**

- **canonical_ctir** — attached CTIR object or fields promoted from CTIR for reads.
- **bounded_slice** — capped lists/structs (visibility, compressed logs, ids).
- **policy_contract** — closed-set or validated contract objects (response_policy,
  narration_obligations shards).
- **planner_derived** — outputs of ``build_narrative_plan`` / upstream repairs (derivative).
- **prompt_derived** — instruction strings / mode lines intended for the model (must not
  back-feed plan construction; listed for boundary clarity).
- **legacy_fallback** — non-CTIR resolution/session paths when CTIR is absent.
- **bounded_text_signal** — raw player text used only as a closed-policy input (e.g.
  response-type gating regexes), not as semantic reconstruction of CTIR.

See ``PHRASE_PATCH_AUDIT`` for heuristic / phrasing-sensitive logic that should
eventually map to explicit intent or obligation classes.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Final, Mapping

__all__ = [
    "BUILD_NARRATIVE_PLAN_PARAM_NAMES",
    "FORBIDDEN_PLANNER_SEMANTIC_CHANNELS",
    "InputClass",
    "InputSource",
    "OwnershipLayer",
    "PHRASE_PATCH_AUDIT",
    "PLANNER_INPUT_MANIFEST_ROWS",
    "manifest_row_ids",
    "summarize_planner_head_for_debug",
]

# Keys that must never appear as kwargs or narrative-plan inputs (GM/model prose channels).
FORBIDDEN_PLANNER_SEMANTIC_CHANNELS: Final[frozenset[str]] = frozenset(
    {
        "gm_output",
        "gm",
        "last_narration",
        "last_narration_text",
        "model_output",
        "narration_text",
        "upstream_narration",
        "player_facing_text_from_model",
        "raw_engine_transcript",
    }
)

# Parameters documented on build_narrative_plan — tests should stay aligned.
BUILD_NARRATIVE_PLAN_PARAM_NAMES: Final[tuple[str, ...]] = (
    "ctir",
    "session_interaction",
    "public_scene_slice",
    "published_entities",
    "recent_compressed_events",
    "resolution_meta",
    "turn_packet",
    "narration_obligations",
    "response_policy",
    "opening_visible_fact_strings",
)


class InputSource(str, Enum):
    """Provenance category for a planner-facing datum."""

    CTIR = "ctir"
    ENGINE_BOUNDED = "engine_bounded"
    PLANNER_DERIVED = "planner_derived"
    PROMPT_DERIVED = "prompt_derived"
    LEGACY_FALLBACK = "legacy_fallback"


class OwnershipLayer(str, Enum):
    """Authoring layer at the planning seam."""

    ENGINE = "engine"
    PLANNER = "planner"
    GPT = "gpt"
    GATE = "gate"


class InputClass(str, Enum):
    """How the input relates to authority and safety."""

    CANONICAL_CTIR = "canonical_ctir"
    BOUNDED_SLICE = "bounded_slice"
    POLICY_CONTRACT = "policy_contract"
    PLANNER_DERIVED = "planner_derived"
    PROMPT_DERIVED = "prompt_derived"
    LEGACY_FALLBACK = "legacy_fallback"
    BOUNDED_TEXT_SIGNAL = "bounded_text_signal"
    DUPLICATED_SEMANTIC_RECONSTRUCTION = "duplicated_semantic_reconstruction"


# Structured manifest rows for tooling, audits, and future UI.
# ``consumer`` names modules/functions that *read* this input for CTIR planning / bundle.
PLANNER_INPUT_MANIFEST_ROWS: Final[tuple[Mapping[str, Any], ...]] = (
    {
        "id": "attached_ctir",
        "path": "session → get_attached_ctir → ctir_obj",
        "consumer": "narration_plan_bundle.build_narration_plan_bundle, narrative_plan_upstream.compute_narrative_plan_for_bundle_from_head",
        "source": InputSource.CTIR.value,
        "ownership": OwnershipLayer.ENGINE.value,
        "classification": InputClass.CANONICAL_CTIR.value,
        "notes": "Sole semantic authority for resolved-turn meaning; passed as build_narrative_plan(ctir=...).",
    },
    {
        "id": "resolution_sem",
        "path": "build_planner_head_state: prompt_sem / resolution_sem from _ctir_to_prompt_semantics(ctir)",
        "consumer": "compute_narrative_plan_for_bundle_from_head, build_response_policy, derive_narration_obligations",
        "source": InputSource.CTIR.value,
        "ownership": OwnershipLayer.ENGINE.value,
        "classification": InputClass.CANONICAL_CTIR.value,
        "notes": "CTIR resolution promoted for engine-shaped reads; not raw free-form GM dict when CTIR attached.",
    },
    {
        "id": "interaction_sem",
        "path": "_ctir_to_prompt_semantics → interaction_sem",
        "consumer": "interaction_context_snapshot_from_ctir_semantics; peek/derive response_type_contract",
        "source": InputSource.CTIR.value,
        "ownership": OwnershipLayer.ENGINE.value,
        "classification": InputClass.CANONICAL_CTIR.value,
        "notes": "Compact interaction projection for RTC path.",
    },
    {
        "id": "visibility_contract",
        "path": "build_narration_visibility_contract → published_entities_slice_for_narrative_planning",
        "consumer": "compute_narrative_plan_for_bundle_from_head → build_narrative_plan(published_entities=...)",
        "source": InputSource.ENGINE_BOUNDED.value,
        "ownership": OwnershipLayer.ENGINE.value,
        "classification": InputClass.BOUNDED_SLICE.value,
        "notes": "Visibility-filtered entity ids/names; capped list.",
    },
    {
        "id": "public_scene_slice",
        "path": "public_scene + scene_state_anchor_contract → public_scene_slice_for_narrative_plan",
        "consumer": "compute_narrative_plan_for_bundle_from_head",
        "source": InputSource.ENGINE_BOUNDED.value,
        "ownership": OwnershipLayer.ENGINE.value,
        "classification": InputClass.BOUNDED_SLICE.value,
        "notes": "Public anchors/labels only; no hidden GM scene prose.",
    },
    {
        "id": "session_interaction_planning",
        "path": "session_view + pending_lead_ids → session_interaction_slice_for_narrative_plan",
        "consumer": "compute_narrative_plan_for_bundle_from_head → build_narrative_plan(session_interaction=...)",
        "source": InputSource.ENGINE_BOUNDED.value,
        "ownership": OwnershipLayer.ENGINE.value,
        "classification": InputClass.BOUNDED_SLICE.value,
        "notes": "Target id, pending leads, resume_entry flag — bounded.",
    },
    {
        "id": "recent_log_compact",
        "path": "_compress_recent_log(recent_log_for_prompt)",
        "consumer": "compute_narrative_plan_for_bundle_from_head → build_narrative_plan(recent_compressed_events=...)",
        "source": InputSource.ENGINE_BOUNDED.value,
        "ownership": OwnershipLayer.ENGINE.value,
        "classification": InputClass.BOUNDED_SLICE.value,
        "notes": "Structured compact rows, not raw chat prose.",
    },
    {
        "id": "narration_obligations",
        "path": "derive_narration_obligations(...)",
        "consumer": "build_narrative_plan(narration_obligations=...), narrative_mode_contract",
        "source": InputSource.ENGINE_BOUNDED.value,
        "ownership": OwnershipLayer.ENGINE.value,
        "classification": InputClass.POLICY_CONTRACT.value,
        "notes": "Obligation flags and modes for narration contract builder.",
    },
    {
        "id": "response_policy",
        "path": "build_response_policy(...); RTC may be injected in upstream",
        "consumer": "build_narrative_plan(response_policy=...), bundle renderer_inputs",
        "source": InputSource.ENGINE_BOUNDED.value,
        "ownership": OwnershipLayer.ENGINE.value,
        "classification": InputClass.POLICY_CONTRACT.value,
        "notes": "Includes response_type_contract when present; see bounded_text_signal for player_text path.",
    },
    {
        "id": "opening_visible_fact_strings",
        "path": "visible_facts_for_prompt when opening/resume gating in compute_narrative_plan_for_bundle_from_head",
        "consumer": "build_narrative_plan(opening_visible_fact_strings=...)",
        "source": InputSource.ENGINE_BOUNDED.value,
        "ownership": OwnershipLayer.ENGINE.value,
        "classification": InputClass.BOUNDED_SLICE.value,
        "notes": "Curated visible fact lines for scene_opening category anchors only (validated upstream).",
    },
    {
        "id": "player_text_rtc_fallback",
        "path": "user_text → derive_response_type_contract(raw_player_text=...) when peek_response_type_contract_from_resolution is None",
        "consumer": "compute_narrative_plan_for_bundle_from_head, narration_plan_bundle._assemble_plan_adjacent_renderer_inputs",
        "source": InputSource.ENGINE_BOUNDED.value,
        "ownership": OwnershipLayer.ENGINE.value,
        "classification": InputClass.BOUNDED_TEXT_SIGNAL.value,
        "notes": "Natural language; used only for closed-set response-type gating, not to reconstruct CTIR fields inside build_narrative_plan.",
    },
    {
        "id": "narrative_plan_output",
        "path": "build_narrative_plan → narrative_plan",
        "consumer": "public_narrative_plan_projection_for_prompt, prompt_context payload",
        "source": InputSource.PLANNER_DERIVED.value,
        "ownership": OwnershipLayer.PLANNER.value,
        "classification": InputClass.PLANNER_DERIVED.value,
        "notes": "Derivative structural bridge; CTIR wins on conflict.",
    },
    {
        "id": "world_progression_projection",
        "path": "_world_progression_projection_for_prompt → wp_projection (head)",
        "consumer": "narration_plan_bundle._assemble_plan_adjacent_renderer_inputs (turn_packet debug stats only)",
        "source": InputSource.ENGINE_BOUNDED.value,
        "ownership": OwnershipLayer.ENGINE.value,
        "classification": InputClass.BOUNDED_SLICE.value,
        "notes": "Pre-validated projection slice for compact counters; not fed into build_narrative_plan.",
    },
    {
        "id": "referent_tracking_bundle",
        "path": "build_referent_tracking_artifact(...) at bundle seam",
        "consumer": "bundle.renderer_inputs.referent_tracking; dialogue_social_plan",
        "source": InputSource.PLANNER_DERIVED.value,
        "ownership": OwnershipLayer.PLANNER.value,
        "classification": InputClass.BOUNDED_SLICE.value,
        "notes": "Constructed upstream from visibility + contracts + narrative_plan transport; not GM prose.",
    },
    {
        "id": "head_state_without_ctir",
        "path": "resolution/intent from caller when ctir_obj is None",
        "consumer": "build_planner_head_state",
        "source": InputSource.LEGACY_FALLBACK.value,
        "ownership": OwnershipLayer.ENGINE.value,
        "classification": InputClass.LEGACY_FALLBACK.value,
        "notes": "Non–CTIR-backed path; bundle returns empty plan (see narration_plan_bundle).",
    },
)

# --- Phrase / heuristic audit (generalization targets; no behavior changes here) ---

PHRASE_PATCH_AUDIT: Final[tuple[Mapping[str, Any], ...]] = (
    {
        "location": "game.narrative_planning",
        "artifact": "_SCENE_OPENING_FALLBACK_MARKERS",
        "kind": "phrase_patch",
        "behavior": "Substring match on lowercased derivation/code strings to detect 'fallback' opener indicators.",
        "generalize_to": "Explicit derivation_code or opening_quality_class from engine (failure locality / narration obligation).",
        "containment": "tests/test_planner_seam_fencing.py::test_scene_opening_fallback_marker_scan_is_non_authoritative",
    },
    {
        "location": "game.narrative_planning",
        "artifact": "_PROSE_INSTRUCTION_KEYS / _SCENE_OPENING_PROSEISH_KEYS",
        "kind": "legitimate_example",
        "behavior": "Reject prompt-shaped keys in JSON plan tree — structural guardrail.",
        "generalize_to": "n/a — keep as schema validation; optionally centralize with JSON-schema.",
    },
    {
        "location": "game.response_type_gating",
        "artifact": "_QUESTION_WORD_RE, _COURTEOUS_OR_PASSIVE_RE, _EXPLICIT_HOSTILE_TEXT_RE",
        "kind": "phrase_patch",
        "behavior": "Regex word lists classify player text for response-type and escalation guards.",
        "generalize_to": "player_intent_class / resolution.metadata.social_intent + authoritative combat flags (intent class + authority rule).",
        "containment": "tests/test_planner_seam_fencing.py::test_resolve_ctir_with_peek_skips_phrase_fallback_and_does_not_use_derive_player_channel; tests/test_planner_seam_fencing.py::test_resolve_non_ctir_enables_legacy_phrase_lane",
    },
    {
        "location": "game.narrative_plan_upstream",
        "artifact": "derive_response_type_contract(..., raw_player_text=user_text)",
        "kind": "narrow_scenario_patch",
        "behavior": "When RTC cannot be peeked from resolution, player text participates in gating.",
        "generalize_to": "Pre-validated response_type_contract on resolution (CTIR or engine) to remove text channel.",
        "containment": "tests/test_planner_seam_fencing.py::test_resolve_ctir_without_metadata_uses_suppressed_derive_not_player_phrase_regex (CTIR); legacy lane in test_resolve_non_ctir_enables_legacy_phrase_lane",
    },
    {
        "location": "game.prompt_context",
        "artifact": "human_adjacent_intent_family in resolution.metadata + prioritize_visible_facts_for_human_adjacent",
        "kind": "narrow_scenario_patch",
        "behavior": "Named intent family branches visibility ordering using player_text.",
        "generalize_to": "visibility_rule + affordance_focus_ids from engine (bounded projection).",
        "containment_deferred": "Full head_state integration is heavy; bounded lane is enforced by planner_head_state / prompt_context comment + opening_fact_telemetry['human_adjacent_bounded_visibility_reorder'].",
    },
    {
        "location": "game.narrative_plan_upstream",
        "artifact": "apply_upstream_narrative_role_reemphasis",
        "kind": "generalized_intent",
        "behavior": "Bumps emphasis_band from plan metadata signals — deterministic repair.",
        "generalize_to": "narration_obligation / composition_hint tier (already close to intended abstraction).",
    },
)


def summarize_planner_head_for_debug(head: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return lightweight, JSON-safe tags describing planner-relevant head state (tests / logs).

    Does not classify individual field semantics beyond presence and CTIR mode.
    """
    if not isinstance(head, Mapping):
        return {"error": "head_not_a_mapping", "ctir_attached": False}
    ctir = head.get("ctir_obj")
    ctir_attached = isinstance(ctir, dict) and bool(ctir)
    res_sem = head.get("resolution_sem")
    return {
        "ctir_attached": ctir_attached,
        # Empty dict is still an attached resolution projection (may be structurally empty).
        "has_resolution_sem": isinstance(res_sem, dict),
        "has_visibility_contract": isinstance(head.get("visibility_contract"), dict),
        "has_public_scene": isinstance(head.get("public_scene"), dict),
        "has_session_view": isinstance(head.get("session_view"), dict),
        "has_narration_obligations": isinstance(head.get("narration_obligations"), dict),
        "has_response_policy": isinstance(head.get("response_policy"), dict),
        "recent_log_compact_n": len(head.get("recent_log_compact") or [])
        if isinstance(head.get("recent_log_compact"), list)
        else 0,
        "visible_facts_for_prompt_n": len(head.get("visible_facts_for_prompt") or [])
        if isinstance(head.get("visible_facts_for_prompt"), list)
        else 0,
        "head_key_count": len(head),
    }


def manifest_row_ids() -> tuple[str, ...]:
    """Stable ids for ``PLANNER_INPUT_MANIFEST_ROWS``."""
    return tuple(str(r["id"]) for r in PLANNER_INPUT_MANIFEST_ROWS)
