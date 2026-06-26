"""FEM packaging, read-side normalization, and FEM-centric observational projections.

**Authority (CG-5):** runtime-owned FEM dict shapes, merges, read helpers, and
registry consumption for fallback owner buckets (vocabulary sourced from
``final_emission_ownership_schema``). BS4 producer attribution **stamps**
(``producer_repair_kind``, owner-bucket fields) are runtime facts; attribution
contract **validates** stamped tokens when building inventory records.

**Does not own:** replay failure taxonomy, attribution unions/aliases, protected
observation paths, or recurrence keys. Registries:
``docs/audits/CG_attribution_contract_registry.md``,
``docs/audits/CG_failure_classification_authority_registry.md``

Canonical metadata-only owner.

:func:`game.final_emission_gate.apply_final_emission_gate` owns **orchestration** (layer order,
integration). This module owns **FEM dict shapes**, merges, slim NA traces, dead-turn
snapshots under ``_final_emission_meta["dead_turn"]``, and **read helpers** / sidecar accessors
— not gates, prompts, or API surfaces.

Shared **vocabulary** (phase/action/scope + event envelope) lives in :mod:`game.telemetry_vocab`.
**Raw semantics** for stage-diff snapshots/transitions and offline evaluator rows stay in
:mod:`game.stage_diff_telemetry` and :mod:`game.narrative_authenticity_eval`; helpers here
project FEM into canonical events via :func:`game.telemetry_vocab.build_telemetry_event` only.
Runtime lineage selection/outcome/repair/mutation events use the separate lightweight vocabulary from
:mod:`game.runtime_lineage_telemetry` via :func:`build_fem_runtime_lineage_events`.

Post-finalization, FEM is usually under ``gm_output["internal_state"]["emission_debug_lane"]``
(see :func:`package_emission_channel_sidecar`). Prefer :func:`read_final_emission_meta_dict` /
:func:`read_emission_debug_lane` over assuming top-level ``_final_emission_meta``.

Validator/repair **wiring** remains in :mod:`game.narrative_authenticity` and
:mod:`game.final_emission_repairs`; narrative-mode **output** legality is
:mod:`game.narrative_mode_contract`.

N4 (Acceptance Quality) orchestration and FEM merge are owned by :mod:`game.final_emission_gate`,
which calls :func:`game.acceptance_quality.validate_and_repair_acceptance_quality` once per wired
path. This module packages **metadata shapes** and observational read paths, not legality verdicts.
"""
from __future__ import annotations

import importlib
import re
from typing import Any, Dict, List, Mapping, MutableMapping

from game.final_emission_ownership_schema import (
    OPENING_FALLBACK_AUTH_UPSTREAM_PREPARED_SOURCES,
    OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES,
    OPENING_FALLBACK_OWNER_BUCKETS,
    OPENING_FALLBACK_OWNER_RETRY,
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_STRICT_SOCIAL,
    OPENING_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    SEALED_FALLBACK_OWNER_BUCKETS,
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    SEALED_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    SEALED_FALLBACK_OWNER_UNKNOWN_NONE,
    UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_PROVENANCE_PACKAGER,
    UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    VISIBILITY_FALLBACK_OWNER_BUCKETS,
    VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE,
    fallback_owner_bucket_registry_surface,
)
from game.final_emission_validators import (
    _default_response_type_debug as _validators_default_response_type_debug,
    _merge_response_type_meta as _validators_merge_response_type_meta,
    _response_type_decision_payload as _validators_response_type_decision_payload,
)
from game.state_channels import project_debug_payload
from game.telemetry_vocab import (
    TELEMETRY_ACTION_OBSERVED,
    TELEMETRY_ACTION_REPAIRED,
    TELEMETRY_ACTION_SKIPPED,
    TELEMETRY_ACTION_UNKNOWN,
    TELEMETRY_PHASE_GATE,
    TELEMETRY_SCOPE_TURN,
    build_telemetry_event,
    normalize_reason_list,
)

# --- Canonical key registries (telemetry-only; not policy) ---
# Vocabulary / envelope: :mod:`game.telemetry_vocab`. FEM shapes + read normalization: this module.
#

# Post-gate contract: debug/meta observability lives under gm_output["internal_state"] lanes.
INTERNAL_STATE_KEY: str = "internal_state"
EMISSION_DEBUG_LANE_KEY: str = "emission_debug_lane"
EMISSION_AUTHOR_LANE_KEY: str = "emission_author_lane"

# Canonical nested dict name for final-emission metadata (FEM). Legacy top-level fallback is supported
# at read time for mixed dicts/fixtures but is not the intended post-gate storage location.
FINAL_EMISSION_META_KEY: str = "_final_emission_meta"
DEBUG_NOTES_KEY: str = "debug_notes"
FINAL_EMISSION_MUTATION_LINEAGE_KEY: str = "final_emission_mutation_lineage"

# FEM subtrees / well-known nested keys.
FEM_DEAD_TURN_KEY: str = "dead_turn"


def ensure_final_emission_meta_dict(gm_output: MutableMapping[str, Any]) -> Dict[str, Any]:
    """Write-time helper: ensure and return the FEM dict on a gate-shaped ``gm_output`` mapping.

    This centralizes the canonical key spelling (``FINAL_EMISSION_META_KEY``) and avoids ad hoc
    get-or-create patterns scattered across gate/repair instrumentation.
    """
    if not isinstance(gm_output, MutableMapping):
        return {}
    meta = gm_output.get(FINAL_EMISSION_META_KEY)
    if not isinstance(meta, dict):
        meta = {}
        gm_output[FINAL_EMISSION_META_KEY] = meta
    return meta


def _accept_path_layer_meta(meta: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return meta if isinstance(meta, Mapping) else {}


def infer_accept_path_final_emitted_source(
    initial_source: str,
    *,
    response_type_debug: Mapping[str, Any] | None = None,
    retry_output: bool = False,
    ac_layer_meta: Mapping[str, Any] | None = None,
    rd_layer_meta: Mapping[str, Any] | None = None,
    srs_layer_meta: Mapping[str, Any] | None = None,
    nat_layer_meta: Mapping[str, Any] | None = None,
    na_layer_meta: Mapping[str, Any] | None = None,
    te_layer_meta: Mapping[str, Any] | None = None,
    ar_layer_meta: Mapping[str, Any] | None = None,
    cs_layer_meta: Mapping[str, Any] | None = None,
    fb_layer_meta: Mapping[str, Any] | None = None,
    purity_layer_meta: Mapping[str, Any] | None = None,
    asp_layer_meta: Mapping[str, Any] | None = None,
    ffnc_layer_meta: Mapping[str, Any] | None = None,
) -> str:
    """Project accept-path ``final_emitted_source`` from layer repair telemetry (metadata only).

    Later overrides win in the same order as ``apply_final_emission_gate`` strict-social and
    generic accept branches. *initial_source* is branch-specific (strict-social ``details`` or
    generic ``generated_candidate``).
    """
    rtd = _accept_path_layer_meta(response_type_debug)
    ac = _accept_path_layer_meta(ac_layer_meta)
    rd = _accept_path_layer_meta(rd_layer_meta)
    srs = _accept_path_layer_meta(srs_layer_meta)
    nat = _accept_path_layer_meta(nat_layer_meta)
    na = _accept_path_layer_meta(na_layer_meta)
    te = _accept_path_layer_meta(te_layer_meta)
    ar = _accept_path_layer_meta(ar_layer_meta)
    cs = _accept_path_layer_meta(cs_layer_meta)
    fb = _accept_path_layer_meta(fb_layer_meta)
    purity = _accept_path_layer_meta(purity_layer_meta)
    asp = _accept_path_layer_meta(asp_layer_meta)
    ffnc = _accept_path_layer_meta(ffnc_layer_meta)

    source = str(initial_source or "")
    if rtd.get("response_type_repair_used"):
        source = str(rtd.get("response_type_repair_kind") or "response_type_contract_repair")
    if retry_output:
        source = "retry_output"
    if ac.get("answer_completeness_repaired"):
        source = str(ac.get("answer_completeness_repair_mode") or "answer_completeness_repair")
    if rd.get("response_delta_repaired"):
        source = str(rd.get("response_delta_repair_mode") or "response_delta_repair")
    if srs.get("social_response_structure_repair_applied") and srs.get("social_response_structure_passed"):
        source = str(
            srs.get("social_response_structure_repair_mode") or "social_response_structure_repair"
        )
    if nat.get("narrative_authenticity_repaired"):
        source = str(nat.get("narrative_authenticity_repair_mode") or "narrative_authenticity_repair")
    if na.get("narrative_authority_repaired"):
        source = str(na.get("narrative_authority_repair_mode") or "narrative_authority_repair")
    if te.get("tone_escalation_repaired"):
        source = str(te.get("tone_escalation_repair_mode") or "tone_escalation_repair")
    if ar.get("anti_railroading_repaired"):
        source = str(ar.get("anti_railroading_repair_mode") or "anti_railroading_repair")
    if cs.get("context_separation_repaired"):
        source = str(cs.get("context_separation_repair_mode") or "context_separation_repair")
    if fb.get("fallback_behavior_repaired"):
        source = str(fb.get("fallback_behavior_repair_mode") or "fallback_behavior_repair")
    if purity.get("player_facing_narration_purity_repaired"):
        source = "player_facing_narration_purity_repair"
    if asp.get("answer_shape_primacy_repaired"):
        source = str(asp.get("answer_shape_primacy_repair_mode") or "answer_shape_primacy_repair")
    if ffnc.get("fast_fallback_neutral_composition_repaired"):
        source = str(
            ffnc.get("fast_fallback_neutral_composition_repair_mode")
            or "fast_fallback_neutral_composition_repair"
        )
    return source


_NARRATION_CONSTRAINT_CODE_RE = re.compile(r"^[A-Za-z0-9_.:/-]+$")


def default_narration_constraint_debug() -> Dict[str, Any]:
    """Compact, sanitized narration-constraint diagnostics; not a full trace log."""
    return {
        "response_type": {
            "required": None,
            "contract_source": None,
            "candidate_ok": None,
            "repair_used": False,
            "repair_kind": None,
            "upstream_prepared_absent": None,
        },
        "visibility": {
            "contract_present": False,
            "decision_mode": None,
            "visible_entity_count": None,
            "withheld_fact_count": None,
            "reason_codes": [],
        },
        "speaker_selection": {
            "speaker_id": None,
            "speaker_name": None,
            "selection_source": None,
            "reason_code": None,
            "binding_confident": None,
        },
    }


def narration_constraint_small_str(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    clean = value.strip()
    if not clean or len(clean) > 64 or any(ch in clean for ch in "\r\n\t"):
        return None
    return clean


def narration_constraint_small_code(value: Any) -> str | None:
    clean = narration_constraint_small_str(value)
    if clean is None or _NARRATION_CONSTRAINT_CODE_RE.fullmatch(clean) is None:
        return None
    return clean


def narration_constraint_small_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def narration_constraint_reason_codes(*sources: Any, limit: int = 5) -> List[str]:
    """Keep only small stable codes; never surface raw hidden text or prompt fragments."""
    out: List[str] = []

    def _push(raw: Any) -> None:
        if len(out) >= limit:
            return
        if isinstance(raw, str):
            clean = narration_constraint_small_code(raw)
            if clean and clean not in out:
                out.append(clean)
            return
        if isinstance(raw, dict):
            _push(raw.get("reason_code"))
            _push(raw.get("reason_codes"))
            kind = raw.get("kind")
            if isinstance(kind, str):
                _push(kind)
            return
        if isinstance(raw, (list, tuple)):
            for item in raw:
                if len(out) >= limit:
                    break
                _push(item)

    for source in sources:
        _push(source)
        if len(out) >= limit:
            break
    return out[:limit]


def narration_constraint_visibility_mode(
    visibility_meta: Mapping[str, Any] | None,
    visibility_validation: Mapping[str, Any] | None,
) -> str | None:
    vm = visibility_meta if isinstance(visibility_meta, dict) else {}
    vv = visibility_validation if isinstance(visibility_validation, dict) else {}
    if vm.get("visibility_replacement_applied") is True:
        return "replaced"
    if vm.get("visibility_continuity_lead_exemption") is True:
        return "continuity_lead_exemption"
    if vm.get("visibility_validation_passed") is True:
        return "validated"
    if vm.get("visibility_validation_passed") is False:
        return "validation_failed"
    if isinstance(vv.get("ok"), bool):
        return "validated" if vv.get("ok") is True else "validation_failed"
    return None


def narration_constraint_binding_confident(
    speaker_selection_contract: Mapping[str, Any] | None,
    speaker_contract_enforcement: Mapping[str, Any] | None,
    speaker_binding_bridge: Mapping[str, Any] | None,
) -> bool | None:
    ssc = speaker_selection_contract if isinstance(speaker_selection_contract, dict) else {}
    sce = speaker_contract_enforcement if isinstance(speaker_contract_enforcement, dict) else {}
    bridge = speaker_binding_bridge if isinstance(speaker_binding_bridge, dict) else {}
    if bridge.get("malformed_attribution_detected") is True:
        return False

    candidate = sce.get("post_validation")
    if not isinstance(candidate, dict):
        candidate = sce.get("validation")
    details = candidate.get("details") if isinstance(candidate, dict) else {}
    signature = details.get("signature") if isinstance(details, dict) else {}
    confidence = narration_constraint_small_code(signature.get("confidence")) if isinstance(signature, dict) else None
    if confidence == "high":
        return True
    if confidence == "low":
        return False
    if ssc.get("continuity_locked") is True:
        return True
    if ssc.get("speaker_switch_allowed") is False and narration_constraint_small_str(ssc.get("primary_speaker_id")):
        return True
    return None


def narration_constraint_speaker_reason_code(
    speaker_selection_contract: Mapping[str, Any] | None,
    speaker_contract_enforcement: Mapping[str, Any] | None,
    speaker_binding_bridge: Mapping[str, Any] | None,
) -> str | None:
    ssc = speaker_selection_contract if isinstance(speaker_selection_contract, dict) else {}
    sce = speaker_contract_enforcement if isinstance(speaker_contract_enforcement, dict) else {}
    bridge = speaker_binding_bridge if isinstance(speaker_binding_bridge, dict) else {}
    candidate = sce.get("post_validation")
    if not isinstance(candidate, dict):
        candidate = sce.get("validation")
    ssc_debug = ssc.get("debug") if isinstance(ssc.get("debug"), dict) else {}
    grounded = (
        narration_constraint_small_code(sce.get("final_reason_code"))
        or narration_constraint_small_code(candidate.get("reason_code") if isinstance(candidate, dict) else None)
        or narration_constraint_small_code(bridge.get("speaker_reason_code"))
        or narration_constraint_small_code(ssc_debug.get("grounding_reason_code"))
        or narration_constraint_small_code(ssc.get("continuity_lock_reason"))
        or narration_constraint_small_code(ssc.get("speaker_switch_reason"))
    )
    if grounded:
        return grounded

    selection_source = narration_constraint_small_code(ssc.get("primary_speaker_source")) or narration_constraint_small_code(
        ssc_debug.get("authoritative_source")
    )
    if selection_source in {"explicit_target", "declared_action", "spoken_vocative", "vocative"}:
        return "speaker_from_explicit_target"
    if selection_source == "continuity":
        return "speaker_from_continuity"
    if not narration_constraint_small_str(ssc.get("primary_speaker_id")):
        return "speaker_unresolved"
    return None


def build_narration_constraint_debug(
    *,
    response_type_debug: Mapping[str, Any] | None = None,
    response_type_contract: Mapping[str, Any] | None = None,
    response_type_contract_source: str | None = None,
    narration_visibility: Mapping[str, Any] | None = None,
    visibility_meta: Mapping[str, Any] | None = None,
    visibility_validation: Mapping[str, Any] | None = None,
    speaker_selection_contract: Mapping[str, Any] | None = None,
    speaker_contract_enforcement: Mapping[str, Any] | None = None,
    speaker_binding_bridge: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a lightweight diagnostic surface; keep it compact, stable, and sanitized."""
    payload = default_narration_constraint_debug()

    rt_dbg = response_type_debug if isinstance(response_type_debug, dict) else {}
    rt_contract = response_type_contract if isinstance(response_type_contract, dict) else {}
    vis_contract = narration_visibility if isinstance(narration_visibility, dict) else {}
    vis_meta = visibility_meta if isinstance(visibility_meta, dict) else {}
    vis_validation_map = visibility_validation if isinstance(visibility_validation, dict) else {}
    ssc = speaker_selection_contract if isinstance(speaker_selection_contract, dict) else {}
    sce = speaker_contract_enforcement if isinstance(speaker_contract_enforcement, dict) else {}
    bridge = speaker_binding_bridge if isinstance(speaker_binding_bridge, dict) else {}

    rt_out = payload["response_type"]
    rt_out["required"] = narration_constraint_small_code(rt_dbg.get("response_type_required")) or narration_constraint_small_code(
        rt_contract.get("required_response_type")
    )
    rt_out["contract_source"] = narration_constraint_small_code(rt_dbg.get("response_type_contract_source")) or narration_constraint_small_code(
        response_type_contract_source
    )
    candidate_ok = rt_dbg.get("response_type_candidate_ok")
    rt_out["candidate_ok"] = candidate_ok if isinstance(candidate_ok, bool) else None
    rt_out["repair_used"] = bool(rt_dbg.get("response_type_repair_used"))
    rt_out["repair_kind"] = narration_constraint_small_code(rt_dbg.get("response_type_repair_kind"))
    absent = rt_dbg.get("response_type_upstream_prepared_absent")
    rt_out["upstream_prepared_absent"] = bool(absent) if isinstance(absent, bool) else None

    vis_out = payload["visibility"]
    vis_out["contract_present"] = bool(vis_contract)
    vis_out["decision_mode"] = narration_constraint_visibility_mode(vis_meta, vis_validation_map)
    vis_out["visible_entity_count"] = (
        len(vis_contract.get("visible_entity_ids"))
        if isinstance(vis_contract.get("visible_entity_ids"), list)
        else None
    )
    vis_out["withheld_fact_count"] = (
        len(vis_contract.get("hidden_fact_strings"))
        if isinstance(vis_contract.get("hidden_fact_strings"), list)
        else None
    )
    vis_reasons: List[str] = []
    if vis_meta.get("visibility_continuity_lead_exemption") is True:
        vis_reasons.append("continuity_lead_exemption")
    vis_reasons.extend(
        narration_constraint_reason_codes(
            vis_meta.get("visibility_violation_kinds"),
            vis_validation_map.get("reason_codes"),
            vis_validation_map.get("violations"),
            limit=5,
        )
    )
    vis_out["reason_codes"] = narration_constraint_reason_codes(vis_reasons, limit=5)

    sp_out = payload["speaker_selection"]
    candidate = sce.get("post_validation")
    if not isinstance(candidate, dict):
        candidate = sce.get("validation")
    sp_out["speaker_id"] = narration_constraint_small_str(ssc.get("primary_speaker_id")) or narration_constraint_small_str(
        candidate.get("canonical_speaker_id") if isinstance(candidate, dict) else None
    )
    sp_out["speaker_name"] = narration_constraint_small_str(ssc.get("primary_speaker_name")) or narration_constraint_small_str(
        candidate.get("canonical_speaker_name") if isinstance(candidate, dict) else None
    )
    ssc_debug = ssc.get("debug") if isinstance(ssc.get("debug"), dict) else {}
    sp_out["selection_source"] = narration_constraint_small_code(ssc.get("primary_speaker_source")) or narration_constraint_small_code(
        ssc_debug.get("authoritative_source")
    )
    sp_out["reason_code"] = narration_constraint_speaker_reason_code(ssc, sce, bridge)
    sp_out["binding_confident"] = narration_constraint_binding_confident(ssc, sce, bridge)

    return payload


def merge_narration_constraint_debug_meta(
    metadata: Dict[str, Any],
    debug_payload: Mapping[str, Any] | None,
) -> None:
    """Merge the compact narration diagnostics without disturbing unrelated metadata."""
    if not isinstance(metadata, dict):
        return
    if not isinstance(debug_payload, dict):
        debug_payload = {}

    emission_debug = metadata.setdefault("emission_debug", {})
    if not isinstance(emission_debug, dict):
        return

    # Keep this surface stable and sanitized; it is a summary view, not a full trace.
    merged = default_narration_constraint_debug()
    existing = emission_debug.get("narration_constraint_debug")
    existing_map = existing if isinstance(existing, dict) else {}
    for section_name, section_default in merged.items():
        existing_section = existing_map.get(section_name)
        payload_section = debug_payload.get(section_name)
        section = dict(section_default)
        if isinstance(existing_section, dict):
            section.update(existing_section)
        if isinstance(payload_section, dict):
            section.update(payload_section)
        merged[section_name] = section
    for extra_key, extra_value in existing_map.items():
        if extra_key not in merged:
            merged[extra_key] = extra_value
    for extra_key, extra_value in debug_payload.items():
        if extra_key not in merged:
            merged[extra_key] = extra_value
    emission_debug["narration_constraint_debug"] = merged


def _append_lineage_token(tokens: list[str], token: str) -> None:
    if token and token not in tokens:
        tokens.append(token)


def build_final_emission_mutation_lineage(
    meta: Mapping[str, Any] | None,
    *,
    sanitizer_trace: Mapping[str, Any] | None = None,
) -> list[str]:
    """Build a compact ordered visible-writer lineage from existing FEM/sanitizer telemetry.

    Metadata-only: this observes already-stamped repair/fallback/finalize fields and does not
    authorize or perform any text mutation.
    """
    if not isinstance(meta, Mapping):
        meta = {}
    trace = sanitizer_trace if isinstance(sanitizer_trace, Mapping) else {}
    existing_lineage = [str(x) for x in meta.get(FINAL_EMISSION_MUTATION_LINEAGE_KEY, []) if isinstance(x, str)]
    tokens: list[str] = []

    if (
        trace.get("sanitizer_lineage_mode") is not None
        or trace.get("sanitizer_boundary_mode") is not None
        or trace.get("sanitizer_lineage_changed_count") is not None
        or trace.get("sanitizer_empty_fallback_used") is not None
        or "pre_gate_sanitizer" in existing_lineage
    ):
        _append_lineage_token(tokens, "pre_gate_sanitizer")

    repair_kind = str(meta.get("response_type_repair_kind") or "").strip()
    final_source = str(meta.get("final_emitted_source") or "").strip()
    if meta.get("response_type_repair_used") is True or repair_kind:
        _append_lineage_token(tokens, "response_type_repair")
    if (
        meta.get("upstream_prepared_emission_used") is True
        or repair_kind in {"answer_upstream_prepared_repair", "action_outcome_upstream_prepared_repair"}
        or final_source in {"answer_upstream_prepared_repair", "action_outcome_upstream_prepared_repair"}
    ):
        _append_lineage_token(tokens, "prepared_emission_selection")
    if (
        meta.get("opening_recovered_via_fallback") is True
        or "opening" in repair_kind
        or "opening" in final_source
    ):
        _append_lineage_token(tokens, "opening_fallback_selection")
    if meta.get("fallback_behavior_repaired") is True or str(meta.get("fallback_behavior_repair_kind") or "").strip():
        _append_lineage_token(tokens, "fallback_behavior_repair")
    if meta.get("final_route") == "replaced":
        _append_lineage_token(tokens, "sealed_fallback_replacement")

    if (
        trace.get("sanitizer_empty_fallback_used") is True
        or trace.get("sanitizer_lineage_empty_fallback_used") is True
        or "sanitizer_empty_fallback" in existing_lineage
    ):
        _append_lineage_token(tokens, "sanitizer_empty_fallback")

    if meta.get("output_sanitization_applied") is True:
        _append_lineage_token(tokens, "finalize_html_strip")
    if meta.get("finalize_route_illegal_strip_applied") is True:
        _append_lineage_token(tokens, "finalize_route_illegal_strip")
    if (
        "final_emission_fast_path_used" in meta
        or meta.get("final_emission_boundary_semantic_repair_disabled") is True
        or meta.get("final_emission_finalize_semantic_repair_used") is not None
    ):
        _append_lineage_token(tokens, "finalize_packaging")
    if meta.get("post_gate_mutation_detected") is True:
        _append_lineage_token(tokens, "post_gate_mutation_detected")
    return tokens


def refresh_final_emission_mutation_lineage(
    meta: MutableMapping[str, Any],
    *,
    sanitizer_trace: Mapping[str, Any] | None = None,
) -> None:
    """Refresh ``final_emission_mutation_lineage`` in-place from already-stamped metadata."""
    if not isinstance(meta, MutableMapping):
        return
    meta[FINAL_EMISSION_MUTATION_LINEAGE_KEY] = build_final_emission_mutation_lineage(
        meta,
        sanitizer_trace=sanitizer_trace,
    )


def patch_final_emission_meta(gm_output: MutableMapping[str, Any], patch: Mapping[str, Any] | None) -> None:
    """Write-time helper: shallow-merge *patch* into ``_final_emission_meta`` (in place)."""
    if not isinstance(gm_output, MutableMapping):
        return
    if not isinstance(patch, Mapping) or not patch:
        return
    meta = ensure_final_emission_meta_dict(gm_output)
    meta.update(dict(patch))
    refresh_final_emission_mutation_lineage(meta)

# Dual fallback-family contract (Cycle AB): ``fallback_family_used`` is diegetic/template
# taxonomy; ``realization_fallback_family`` is governed provenance. Both may coexist on FEM.
# Read-side golden replay prefers diegetic first when projecting observed ``fallback_family``;
# observability normalization must preserve both keys without rewriting either taxonomy.
# Response-type debug fields (RTD1) that may be merged into FEM for observability.
FEM_RESPONSE_TYPE_KEYS: frozenset[str] = frozenset(
    {
        "response_type_required",
        "response_type_contract_source",
        "response_type_candidate_ok",
        "response_type_repair_used",
        "response_type_repair_kind",
        "response_type_rejection_reasons",
        "non_hostile_escalation_blocked",
        "response_type_upstream_prepared_absent",
        "upstream_prepared_emission_used",
        "upstream_prepared_emission_valid",
        "upstream_prepared_emission_source",
        "upstream_prepared_emission_reject_reason",
        "final_emission_boundary_repair_used",
        "final_emission_boundary_semantic_repair_disabled",
        "opening_validation_failed",
        "opening_failure_reasons",
        "opening_recovered_via_fallback",
        "opening_fallback_authorship_source",
        "sealed_fallback_owner_bucket",
        "fallback_family_used",
        "fallback_temporal_frame",
        "realization_fallback_family",
    }
)

# Upstream fast-fallback provenance trace on FEM (read-side observability only).
# Packaged by ``game.fallback_provenance_debug.record_final_emission_gate_exit`` (BK6
# stable provenance owner); not owner-bucket assignment, diegetic family, or prose authorship.
FEM_FALLBACK_PROVENANCE_TRACE_KEY: str = "fallback_provenance_trace"

# Canonical upstream API fast-fallback provenance field (BK6 metadata keys; owners in ownership schema).
UPSTREAM_FAST_FALLBACK_PROVENANCE_METADATA_KEY: str = "fallback_provenance"

UPSTREAM_FAST_FALLBACK_PROVENANCE_SELECTOR_KEYS: frozenset[str] = frozenset(
    {
        "source",
        "stage",
        "content_fingerprint",
        "selector_player_facing_text",
    }
)

UPSTREAM_FAST_FALLBACK_MUTATION_HINTS_FINALIZE_CONTAIN: frozenset[str] = frozenset(
    {
        "mutation_before_or_during_gate_entry",
        "mutation_inside_gate_or_finalize",
        "mutation_unknown",
    }
)


def upstream_fast_fallback_provenance_field_registry_surface() -> dict[str, object]:
    """Diagnostic registry surface for upstream fast-fallback provenance keys (BK6)."""
    return {
        "metadata_key": UPSTREAM_FAST_FALLBACK_PROVENANCE_METADATA_KEY,
        "fem_trace_key": FEM_FALLBACK_PROVENANCE_TRACE_KEY,
        "selector_keys": sorted(UPSTREAM_FAST_FALLBACK_PROVENANCE_SELECTOR_KEYS),
        "mutation_hints_finalize_contain": sorted(UPSTREAM_FAST_FALLBACK_MUTATION_HINTS_FINALIZE_CONTAIN),
        "selection_owner": UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
        "provenance_packager": UPSTREAM_FAST_FALLBACK_PROVENANCE_PACKAGER,
        "content_owner": UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    }


def upstream_fast_fallback_provenance_field_registry_parity_errors() -> list[str]:
    """Return internal parity errors when upstream fast-fallback provenance registries drift."""
    errors: list[str] = []
    surface = upstream_fast_fallback_provenance_field_registry_surface()
    if surface["metadata_key"] != UPSTREAM_FAST_FALLBACK_PROVENANCE_METADATA_KEY:
        errors.append("upstream_fast_fallback_provenance_metadata_key registry surface drift")
    if surface["fem_trace_key"] != FEM_FALLBACK_PROVENANCE_TRACE_KEY:
        errors.append("fem_fallback_provenance_trace_key registry surface drift")
    if frozenset(surface["selector_keys"]) != UPSTREAM_FAST_FALLBACK_PROVENANCE_SELECTOR_KEYS:
        errors.append("upstream_fast_fallback_provenance_selector_keys registry surface drift")
    if frozenset(surface["mutation_hints_finalize_contain"]) != UPSTREAM_FAST_FALLBACK_MUTATION_HINTS_FINALIZE_CONTAIN:
        errors.append("upstream_fast_fallback_mutation_hints_finalize_contain registry surface drift")
    return errors

# Read-side FEM/replay projection registry for opening fallback telemetry.
# Write-time result metadata is composed by
# ``game.final_emission_opening_fallback.build_opening_fallback_result_meta`` (AJ1);
# upstream composition layers use ``build_upstream_prepared_opening_composition_meta`` (AJ2).
# ``opening_fallback_projection_fields`` / ``apply_opening_fallback_projection_fields`` copy
# these keys only — they do not select fallback text or remap owner buckets.
OPENING_FALLBACK_PROJECTION_FIELDS: tuple[str, ...] = (
    "opening_fallback_context_source",
    "opening_fallback_basis_count",
    "opening_fallback_context_missing",
    "opening_fallback_failed_closed",
    "opening_curated_facts_present",
    "opening_curated_facts_count",
    "opening_curated_facts_source",
    "opening_selector_source_used",
    "opening_selector_selected_facts",
    "opening_curated_facts",
    "opening_final_fallback_basis",
    "opening_final_basis_matches_selector",
    "opening_fallback_authorship_source",
)

# Out-of-band opening fallback telemetry (CK Block 7/9): fail-closed selection stamps both keys on
# ``composition_meta`` (and ``response_type_debug`` via ``debug.update(fallback_meta)``). Only
# ``OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_RTD_MERGE_FIELDS`` reach FEM via
# ``merge_response_type_meta``; the additive alias ``opening_fallback_local_composition_disabled``
# is composition-meta / RTD-debug only and is intentionally **not** RTD-merged. Both are excluded
# from ``OPENING_FALLBACK_PROJECTION_FIELDS``. Observability/negative-invariant only — not
# authorship, not owner-bucket inputs, not golden replay protected observation paths. Key strings
# align with ``game.final_emission_opening_fallback.OPENING_FALLBACK_*_DISABLED_KEY`` constants.
OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS: tuple[str, ...] = (
    "opening_fallback_compatibility_local_disabled",
    "opening_fallback_local_composition_disabled",
)

# Canonical RTD→FEM merge subset (CK Block 9 quarantine: alias stays composition_meta-only).
OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_RTD_MERGE_FIELDS: tuple[str, ...] = (
    "opening_fallback_compatibility_local_disabled",
)

# Fail-closed opening fallback diagnostics (CK Block 8): negative-invariant keys stamped on
# composition_meta fail-closed paths and merged into FEM via ``merge_response_type_meta``.
# Not projection fields, not owner-bucket inputs, not golden replay protected paths.
# Key strings align with ``game.final_emission_opening_fallback.OPENING_FALLBACK_*`` constants.
OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS: tuple[str, ...] = (
    "opening_fallback_missing_upstream_prepared_payload",
    "opening_fallback_missing_curated_facts",
    "opening_fallback_upstream_payload_unusable",
    "opening_fallback_upstream_payload_recovered",
)

# Response-type debug merge field co-stamped by opening fail-closed paths (not ``opening_fallback_*``).
OPENING_FALLBACK_FAIL_CLOSED_RELATED_RESPONSE_TYPE_DEBUG_FIELDS: tuple[str, ...] = (
    "blocked_repair_kind",
)

# Union of every ``opening_fallback_*`` metadata key emitted on opening fallback paths.
OPENING_FALLBACK_EMITTED_METADATA_FIELDS: tuple[str, ...] = tuple(
    sorted(
        set(OPENING_FALLBACK_PROJECTION_FIELDS)
        | set(OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS)
        | set(OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS)
    )
)

# Primary classification registries (mutually disjoint partition of emitted keys).
_OPENING_FALLBACK_METADATA_CLASSIFICATION_REGISTRIES: tuple[tuple[str, ...], ...] = (
    OPENING_FALLBACK_PROJECTION_FIELDS,
    OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS,
    OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS,
)

# Canonical write-time result meta keys (authorship stamped separately by upstream/gate).
OPENING_FALLBACK_RESULT_META_FIELDS: tuple[str, ...] = tuple(
    key for key in OPENING_FALLBACK_PROJECTION_FIELDS if key != "opening_fallback_authorship_source"
)

# Context-extraction mirror keys (subset of result meta populated before composition).
_OPENING_FALLBACK_CONTEXT_ONLY_RESULT_FIELDS: frozenset[str] = frozenset(
    {
        "opening_fallback_failed_closed",
        "opening_curated_facts_present",
        "opening_curated_facts_count",
    }
)
OPENING_FALLBACK_CONTEXT_MIRROR_FIELDS: tuple[str, ...] = tuple(
    key
    for key in OPENING_FALLBACK_RESULT_META_FIELDS
    if key not in _OPENING_FALLBACK_CONTEXT_ONLY_RESULT_FIELDS
)

OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS: tuple[str, ...] = tuple(
    key
    for key in OPENING_FALLBACK_PROJECTION_FIELDS
    if key
    in {
        "opening_selector_source_used",
        "opening_selector_selected_facts",
        "opening_curated_facts",
        "opening_final_fallback_basis",
        "opening_final_basis_matches_selector",
    }
)

_OPENING_FALLBACK_BOOL_PROJECTION_FIELDS: frozenset[str] = frozenset(
    {
        "opening_fallback_context_missing",
        "opening_fallback_failed_closed",
        "opening_curated_facts_present",
        "opening_final_basis_matches_selector",
    }
)

_OPENING_FALLBACK_INT_PROJECTION_FIELDS: frozenset[str] = frozenset(
    {
        "opening_fallback_basis_count",
        "opening_curated_facts_count",
    }
)


from game.opening_deterministic_fallback import default_opening_fallback_context_mirror_values


def default_opening_fallback_fail_closed_result_meta() -> Dict[str, Any]:
    """Canonical fail-closed write-time result meta (``context is None`` path)."""
    return {
        "opening_fallback_context_source": "opening_curated_facts",
        "opening_fallback_basis_count": 0,
        "opening_fallback_context_missing": True,
        "opening_fallback_failed_closed": True,
        "opening_curated_facts_present": False,
        "opening_curated_facts_count": 0,
        "opening_curated_facts_source": "selector",
        "opening_selector_source_used": "none",
        "opening_selector_selected_facts": [],
        "opening_curated_facts": [],
        "opening_final_fallback_basis": [],
        "opening_final_basis_matches_selector": True,
    }


def opening_fallback_metadata_field_registry_surface() -> dict[str, object]:
    """Diagnostic registry surface for opening fallback metadata field lists (BK5/CK8)."""
    return {
        "opening_fallback_projection_fields": list(OPENING_FALLBACK_PROJECTION_FIELDS),
        "opening_fallback_out_of_band_telemetry_fields": list(
            OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS
        ),
        "opening_fallback_out_of_band_telemetry_rtd_merge_fields": list(
            OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_RTD_MERGE_FIELDS
        ),
        "opening_fallback_fail_closed_diagnostic_fields": list(
            OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS
        ),
        "opening_fallback_fail_closed_related_response_type_debug_fields": list(
            OPENING_FALLBACK_FAIL_CLOSED_RELATED_RESPONSE_TYPE_DEBUG_FIELDS
        ),
        "opening_fallback_emitted_metadata_fields": list(OPENING_FALLBACK_EMITTED_METADATA_FIELDS),
        "opening_fallback_result_meta_fields": list(OPENING_FALLBACK_RESULT_META_FIELDS),
        "opening_fallback_context_mirror_fields": list(OPENING_FALLBACK_CONTEXT_MIRROR_FIELDS),
        "opening_fallback_selector_debug_fields": list(OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS),
        "opening_fallback_bool_projection_fields": sorted(_OPENING_FALLBACK_BOOL_PROJECTION_FIELDS),
        "opening_fallback_int_projection_fields": sorted(_OPENING_FALLBACK_INT_PROJECTION_FIELDS),
    }


def opening_fallback_metadata_classification_parity_errors() -> list[str]:
    """Return parity errors when opening fallback metadata classification registries drift."""
    errors: list[str] = []
    union: set[str] = set()
    for index, registry in enumerate(_OPENING_FALLBACK_METADATA_CLASSIFICATION_REGISTRIES):
        keys = set(registry)
        if not keys:
            errors.append(f"opening fallback classification registry[{index}] must not be empty")
            continue
        overlap = union & keys
        if overlap:
            errors.append(
                "opening fallback metadata classification registries overlap: "
                + ", ".join(sorted(overlap))
            )
        union |= keys
    if union != set(OPENING_FALLBACK_EMITTED_METADATA_FIELDS):
        missing = sorted(set(OPENING_FALLBACK_EMITTED_METADATA_FIELDS) - union)
        extra = sorted(union - set(OPENING_FALLBACK_EMITTED_METADATA_FIELDS))
        if missing:
            errors.append(
                "opening fallback emitted metadata fields missing from classification registries: "
                + ", ".join(missing)
            )
        if extra:
            errors.append(
                "opening fallback classification registries contain non-emitted keys: "
                + ", ".join(extra)
            )
    from game.final_emission_opening_fallback import (
        OPENING_FALLBACK_COMPATIBILITY_LOCAL_DISABLED_KEY,
        OPENING_FALLBACK_LOCAL_COMPOSITION_DISABLED_KEY,
        OPENING_FALLBACK_MISSING_CURATED_FACTS_KEY,
        OPENING_FALLBACK_MISSING_UPSTREAM_PREPARED_PAYLOAD_KEY,
        OPENING_FALLBACK_UPSTREAM_PAYLOAD_RECOVERED_KEY,
        OPENING_FALLBACK_UPSTREAM_PAYLOAD_UNUSABLE_KEY,
    )

    constant_map = {
        OPENING_FALLBACK_COMPATIBILITY_LOCAL_DISABLED_KEY: OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS,
        OPENING_FALLBACK_LOCAL_COMPOSITION_DISABLED_KEY: OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS,
        OPENING_FALLBACK_MISSING_UPSTREAM_PREPARED_PAYLOAD_KEY: OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS,
        OPENING_FALLBACK_MISSING_CURATED_FACTS_KEY: OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS,
        OPENING_FALLBACK_UPSTREAM_PAYLOAD_UNUSABLE_KEY: OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS,
        OPENING_FALLBACK_UPSTREAM_PAYLOAD_RECOVERED_KEY: OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS,
    }
    for constant, registry in constant_map.items():
        if constant not in registry:
            errors.append(
                f"opening fallback writer constant {constant!r} missing from canonical registry"
            )
    dbg = default_response_type_debug({}, None)
    for key in OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS:
        if key not in dbg:
            errors.append(
                f"response-type debug defaults missing fail-closed diagnostic key: {key}"
            )
    for key in OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_RTD_MERGE_FIELDS:
        if key not in dbg:
            errors.append(
                f"response-type debug defaults missing out-of-band telemetry key: {key}"
            )
    alias_only = set(OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS) - set(
        OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_RTD_MERGE_FIELDS
    )
    if alias_only != {OPENING_FALLBACK_LOCAL_COMPOSITION_DISABLED_KEY}:
        errors.append(
            "opening fallback out-of-band telemetry RTD merge quarantine drift: "
            f"expected alias-only keys {OPENING_FALLBACK_LOCAL_COMPOSITION_DISABLED_KEY!r}, "
            f"got {sorted(alias_only)!r}"
        )
    if OPENING_FALLBACK_LOCAL_COMPOSITION_DISABLED_KEY in dbg:
        errors.append(
            "opening_fallback_local_composition_disabled must not appear in response-type debug "
            "defaults (composition-meta-only quarantine)"
        )
    for key in OPENING_FALLBACK_FAIL_CLOSED_RELATED_RESPONSE_TYPE_DEBUG_FIELDS:
        if key not in dbg:
            errors.append(
                f"response-type debug defaults missing related fail-closed debug key: {key}"
            )
    return errors


def opening_fallback_metadata_field_registry_parity_errors() -> list[str]:
    """Return internal parity errors when derived opening field registries drift."""
    errors: list[str] = []
    errors.extend(opening_fallback_metadata_classification_parity_errors())
    surface = opening_fallback_metadata_field_registry_surface()
    if tuple(surface["opening_fallback_projection_fields"]) != OPENING_FALLBACK_PROJECTION_FIELDS:
        errors.append("opening_fallback_projection_fields registry surface drift")
    if tuple(surface["opening_fallback_out_of_band_telemetry_fields"]) != OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS:
        errors.append("opening_fallback_out_of_band_telemetry_fields registry surface drift")
    if tuple(surface["opening_fallback_out_of_band_telemetry_rtd_merge_fields"]) != (
        OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_RTD_MERGE_FIELDS
    ):
        errors.append("opening_fallback_out_of_band_telemetry_rtd_merge_fields registry surface drift")
    if tuple(surface["opening_fallback_fail_closed_diagnostic_fields"]) != OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS:
        errors.append("opening_fallback_fail_closed_diagnostic_fields registry surface drift")
    if tuple(surface["opening_fallback_emitted_metadata_fields"]) != OPENING_FALLBACK_EMITTED_METADATA_FIELDS:
        errors.append("opening_fallback_emitted_metadata_fields registry surface drift")
    if tuple(surface["opening_fallback_result_meta_fields"]) != OPENING_FALLBACK_RESULT_META_FIELDS:
        errors.append("opening_fallback_result_meta_fields registry surface drift")
    if tuple(surface["opening_fallback_context_mirror_fields"]) != OPENING_FALLBACK_CONTEXT_MIRROR_FIELDS:
        errors.append("opening_fallback_context_mirror_fields registry surface drift")
    if tuple(surface["opening_fallback_selector_debug_fields"]) != OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS:
        errors.append("opening_fallback_selector_debug_fields registry surface drift")
    if set(OPENING_FALLBACK_RESULT_META_FIELDS) != set(default_opening_fallback_fail_closed_result_meta()):
        errors.append("default_opening_fallback_fail_closed_result_meta keys drift from OPENING_FALLBACK_RESULT_META_FIELDS")
    if set(OPENING_FALLBACK_CONTEXT_MIRROR_FIELDS) != set(default_opening_fallback_context_mirror_values()):
        errors.append("default_opening_fallback_context_mirror_values keys drift from OPENING_FALLBACK_CONTEXT_MIRROR_FIELDS")
    if not set(OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS).issubset(set(OPENING_FALLBACK_PROJECTION_FIELDS)):
        errors.append("OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS must be subset of OPENING_FALLBACK_PROJECTION_FIELDS")
    if not set(OPENING_FALLBACK_RESULT_META_FIELDS).issubset(set(OPENING_FALLBACK_PROJECTION_FIELDS)):
        errors.append("OPENING_FALLBACK_RESULT_META_FIELDS must be subset of OPENING_FALLBACK_PROJECTION_FIELDS")
    overlap = set(OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS) & set(OPENING_FALLBACK_PROJECTION_FIELDS)
    if overlap:
        errors.append(
            "OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS must be disjoint from OPENING_FALLBACK_PROJECTION_FIELDS"
        )
    if set(OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS) & set(OPENING_FALLBACK_RESULT_META_FIELDS):
        errors.append(
            "OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS must be disjoint from OPENING_FALLBACK_RESULT_META_FIELDS"
        )
    if not set(OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_RTD_MERGE_FIELDS).issubset(
        set(OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS)
    ):
        errors.append(
            "OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_RTD_MERGE_FIELDS must be subset of "
            "OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_FIELDS"
        )
    return errors


def opening_fallback_projection_fields(
    source: Mapping[str, Any] | None,
    *,
    coerce_for_fem: bool = False,
    include_authorship_source: bool = True,
) -> Dict[str, Any]:
    """Copy opening fallback projection fields from *source* without selecting or authoring fallback text."""
    src = source if isinstance(source, Mapping) else {}
    out: Dict[str, Any] = {}
    for key in OPENING_FALLBACK_PROJECTION_FIELDS:
        if key == "opening_fallback_authorship_source" and not include_authorship_source:
            continue
        value = src.get(key)
        if coerce_for_fem and key in _OPENING_FALLBACK_BOOL_PROJECTION_FIELDS:
            out[key] = bool(value)
        elif coerce_for_fem and key in _OPENING_FALLBACK_INT_PROJECTION_FIELDS:
            out[key] = int(value or 0)
        else:
            out[key] = value
    return out


def apply_opening_fallback_projection_fields(
    target: MutableMapping[str, Any],
    source: Mapping[str, Any] | None,
    *,
    coerce_for_fem: bool = False,
    include_authorship_source: bool = True,
) -> None:
    """Metadata-only shallow copy of opening fallback projection fields into *target*."""
    if not isinstance(target, MutableMapping):
        return
    target.update(
        opening_fallback_projection_fields(
            source,
            coerce_for_fem=coerce_for_fem,
            include_authorship_source=include_authorship_source,
        )
    )


# --- Canonical fallback owner-bucket registry (read-side vocabulary; not policy) ---
# Single source of bucket string values: :mod:`game.final_emission_ownership_schema`.
# Read-side bucket mappers: :mod:`game.final_emission_owner_bucket_views` (private aliases below).

def final_emission_meta_read_side_surface() -> dict[str, object]:
    """Summarize FEM read-side packaging keys and fallback owner bucket registries.

    Diagnostic only: does not read live turn payloads or drive gate orchestration.
    """
    registries = fallback_owner_bucket_registry_surface()
    return {
        "final_emission_meta_key": FINAL_EMISSION_META_KEY,
        "emission_debug_lane_key": EMISSION_DEBUG_LANE_KEY,
        "internal_state_key": INTERNAL_STATE_KEY,
        "final_emission_mutation_lineage_key": FINAL_EMISSION_MUTATION_LINEAGE_KEY,
        "opening_fallback_owner_buckets": sorted(OPENING_FALLBACK_OWNER_BUCKETS),
        "opening_fallback_metadata_field_registry": opening_fallback_metadata_field_registry_surface(),
        "upstream_fast_fallback_provenance_field_registry": upstream_fast_fallback_provenance_field_registry_surface(),
        "sealed_fallback_owner_buckets": sorted(SEALED_FALLBACK_OWNER_BUCKETS),
        "visibility_fallback_owner_buckets": sorted(VISIBILITY_FALLBACK_OWNER_BUCKETS),
        "fallback_owner_bucket_registries": registries,
        "sidecar_read_helpers_preferred": True,
    }


from game.final_emission_owner_bucket_views import (
    opening_fallback_owner_bucket_from_fields as _opening_fallback_owner_bucket_from_fields,
    opening_fallback_owner_bucket_from_meta as _opening_fallback_owner_bucket_from_meta,
    visibility_fallback_owner_bucket_from_fields as _visibility_fallback_owner_bucket_from_fields,
)

# --- BS4 producer attribution stamps (metadata-only; no routing or content changes) ---

PRODUCER_REPAIR_KIND_FIELD: str = "producer_repair_kind"

PRODUCER_REPAIR_KIND_VISIBILITY_ENFORCEMENT: str = "visibility_enforcement"
PRODUCER_REPAIR_KIND_FIRST_MENTION_ENFORCEMENT: str = "first_mention_enforcement"
PRODUCER_REPAIR_KIND_REFERENTIAL_CLARITY_ENFORCEMENT: str = "referential_clarity_enforcement"
PRODUCER_REPAIR_KIND_REFERENTIAL_CLARITY_LOCAL_SUBSTITUTION: str = "referential_clarity_local_substitution"
PRODUCER_REPAIR_KIND_PASSIVE_SCENE_CONCRETE_BEAT: str = "passive_scene_concrete_beat"
PRODUCER_REPAIR_KIND_SANITIZER_EMPTY_OUTPUT: str = "sanitizer_empty_output"
PRODUCER_REPAIR_KIND_SANITIZER_STRIP_ONLY: str = "sanitizer_strip_only"
PRODUCER_REPAIR_KIND_STRICT_SOCIAL_REPAIR: str = "strict_social_repair"
PRODUCER_REPAIR_KIND_FALLBACK_BEHAVIOR_REPAIR: str = "fallback_behavior_repair"


def stamp_producer_repair_kind(
    meta: MutableMapping[str, Any],
    repair_kind: str,
    *,
    overwrite: bool = False,
) -> None:
    """Stamp deterministic producer repair kind on FEM metadata without altering routing."""
    if not isinstance(meta, MutableMapping):
        return
    kind = str(repair_kind or "").strip()
    if not kind:
        return
    if not overwrite and str(meta.get(PRODUCER_REPAIR_KIND_FIELD) or "").strip():
        return
    meta[PRODUCER_REPAIR_KIND_FIELD] = kind


def stamp_opening_fallback_owner_bucket(meta: MutableMapping[str, Any]) -> None:
    """Stamp opening owner bucket when authorship/repair signals are already on *meta*."""
    if not isinstance(meta, MutableMapping):
        return
    if str(meta.get("opening_fallback_owner_bucket") or "").strip():
        return
    bucket = _opening_fallback_owner_bucket_from_meta(meta)
    if bucket:
        meta["opening_fallback_owner_bucket"] = bucket


def stamp_retry_terminal_fallback_producer_metadata(meta: MutableMapping[str, Any]) -> None:
    """Stamp retry owner bucket when retry terminal fallback family is already on *meta*."""
    if not isinstance(meta, MutableMapping):
        return
    from game.realization_provenance import REALIZATION_FALLBACK_FAMILY_FIELD, RETRY_TERMINAL_FALLBACK

    family = str(meta.get(REALIZATION_FALLBACK_FAMILY_FIELD) or "").strip()
    if family != RETRY_TERMINAL_FALLBACK:
        return
    if str(meta.get("opening_fallback_owner_bucket") or "").strip():
        return
    meta["opening_fallback_owner_bucket"] = OPENING_FALLBACK_OWNER_RETRY


def stamp_upstream_prepared_opening_producer_metadata(meta: MutableMapping[str, Any]) -> None:
    """Stamp opening owner bucket for upstream-prepared opening producer payloads."""
    if not isinstance(meta, MutableMapping):
        return
    stamp_opening_fallback_owner_bucket(meta)


def stamp_visibility_fallback_owner_bucket_from_fields(
    meta: MutableMapping[str, Any],
    *,
    fallback_pool: str | None = None,
    fallback_kind: str | None = None,
    final_emitted_source: str | None = None,
) -> None:
    """Stamp visibility owner bucket from already-known fallback selection fields.

    Hard-replacement orchestrators pair this with :func:`stamp_producer_repair_kind`
    for visibility/first-mention/referential paths (BU9 producer-stamp governance).
    """
    if not isinstance(meta, MutableMapping):
        return
    if str(meta.get("visibility_fallback_owner_bucket") or "").strip():
        return
    pool = str(fallback_pool or meta.get("visibility_fallback_pool") or "").strip()
    kind = str(fallback_kind or meta.get("visibility_fallback_kind") or "").strip()
    source = str(final_emitted_source or meta.get("final_emitted_source") or "").strip()
    bucket = _visibility_fallback_owner_bucket_from_fields(
        fallback_pool=pool,
        fallback_kind=kind,
        final_emitted_source=source,
    )
    if bucket:
        meta["visibility_fallback_owner_bucket"] = bucket


def apply_sanitizer_producer_attribution_to_fem(
    meta: MutableMapping[str, Any],
    sanitizer_trace: Mapping[str, Any] | None,
) -> None:
    """Copy sanitizer producer attribution stamps from trace into finalized FEM metadata."""
    if not isinstance(meta, MutableMapping):
        return
    trace = sanitizer_trace if isinstance(sanitizer_trace, Mapping) else {}
    repair_kind = str(trace.get(PRODUCER_REPAIR_KIND_FIELD) or "").strip()
    if repair_kind:
        stamp_producer_repair_kind(meta, repair_kind, overwrite=True)
    owner_bucket = str(trace.get("sealed_fallback_owner_bucket") or "").strip()
    if owner_bucket and not str(meta.get("sealed_fallback_owner_bucket") or "").strip():
        meta["sealed_fallback_owner_bucket"] = owner_bucket
    for key in (
        "sanitizer_empty_fallback_used",
        "sanitizer_lineage_empty_fallback_used",
        "sanitizer_strict_social_fallback_used",
        "sanitizer_empty_fallback_source",
        "sanitizer_strict_social_source",
        "sanitizer_empty_fallback_owner",
        "sanitizer_strict_social_selection_owner",
        "sanitizer_strict_social_prose_owner",
        "sanitizer_empty_fallback_owner_trace_short",
        "sanitizer_strict_social_selection_owner_trace_short",
        "sanitizer_strict_social_prose_owner_trace_short",
    ):
        if key in trace and meta.get(key) is None:
            meta[key] = trace.get(key)


# Stage-diff is intentionally bounded; it may project a compact NA subset for observability only.
# This is not a second owner of NA semantics; it is an explicitly-allowed projection surface.
STAGE_DIFF_ALLOWED_NA_PROJECTION_KEYS: frozenset[str] = frozenset(
    {
        "narrative_authenticity_reason_codes",
        "narrative_authenticity_skip_reason",
        "narrative_authenticity_status",
        "narrative_authenticity_rumor_relaxed_low_signal",
        # Optional: repair mode is observational and compact; stage-diff does not consume full evidence/metrics.
        "narrative_authenticity_repair_mode",
    }
)

# Evaluator/debug consumers may want a normalized FEM slice without importing every gate module.
# Prefix-based families are explicit registries (telemetry-only) and do not imply policy ownership here.
# ``acceptance_quality_*`` keys are legality-shaped N4 traces (reason codes + slim evidence), not numeric scores.
EVALUATOR_FEM_KEY_PREFIX_FAMILIES: tuple[str, ...] = (
    "answer_completeness_",
    "answer_exposition_plan_",
    "response_delta_",
    "social_response_structure_",
    "fallback_behavior_",
    "referent_",
    "narrative_authenticity_",
    "narrative_mode_output_",
    "acceptance_quality_",
    "response_type_",
    "fallback_",
)

# Explicit non-prefix evaluator keys (nested dicts / stable aliases).
EVALUATOR_FEM_EXPLICIT_KEYS: frozenset[str] = frozenset(
    {
        FEM_DEAD_TURN_KEY,
    }
)

# --- Response-type debug/meta shaping (metadata-only; orchestration decides when to attach) ---


def default_response_type_debug(contract: Dict[str, Any] | None, source: str | None) -> Dict[str, Any]:
    """Metadata-only helper for the canonical response-type debug dict (RTD1).

    This shapes *descriptive* fields used by the gate for observability and FEM merge, but does not
    decide whether the response-type contract should run or what repair is applied.
    """
    return _validators_default_response_type_debug(contract, source)


def merge_response_type_meta(meta: Dict[str, Any], debug: Dict[str, Any]) -> None:
    """Metadata-only merge of response-type debug fields into ``_final_emission_meta``."""
    _validators_merge_response_type_meta(meta, debug)


def response_type_decision_payload(debug: Dict[str, Any]) -> Dict[str, Any]:
    """Metadata-only compact view suitable for logs/telemetry sinks (stable keys)."""
    return _validators_response_type_decision_payload(debug)

# ``accepted_via`` values that can carry ``retry_exhausted`` / terminal flags from legitimate
# deterministic repairs without implying an upstream API / infra failure by themselves.
_LEGITIMATE_RESOLUTION_REPAIR_ACCEPTED_VIA: frozenset[str] = frozenset(
    {"social_resolution_repair", "nonsocial_resolution_repair"}
)

# Keys merged from NA layer debug into ``gm_output['_final_emission_meta']`` (contract-driven, stable names).
# Distinct from ``response_delta_*`` legality keys (gate delta layer) and from offline ``narrative_authenticity_eval``.
NARRATIVE_MODE_OUTPUT_FEM_KEYS: frozenset[str] = frozenset(
    {
        "narrative_mode_output_validator_version",
        "narrative_mode_output_checked",
        "narrative_mode_output_passed",
        "narrative_mode_output_mode",
        "narrative_mode_output_failure_reasons",
        "narrative_mode_output_repairable",
        "narrative_mode_output_observed_signals",
        "narrative_mode_output_skip_reason",
        "narrative_mode_contract_version",
        "narrative_mode_contract_mode",
    }
)


def default_narrative_mode_output_layer_meta() -> Dict[str, Any]:
    """Metadata-only defaults for C4 narrative-mode output validation (FEM merge)."""
    return {
        "narrative_mode_output_validator_version": None,
        "narrative_mode_output_checked": False,
        "narrative_mode_output_passed": True,
        "narrative_mode_output_mode": None,
        "narrative_mode_output_failure_reasons": [],
        "narrative_mode_output_repairable": False,
        "narrative_mode_output_observed_signals": {},
        "narrative_mode_output_skip_reason": None,
        "narrative_mode_contract_version": None,
        "narrative_mode_contract_mode": None,
    }


def merge_narrative_mode_output_into_final_emission_meta(meta: Dict[str, Any], nmo: Mapping[str, Any]) -> None:
    """Shallow-merge narrative-mode output trace fields into ``_final_emission_meta`` (in place)."""
    if not isinstance(meta, dict) or not isinstance(nmo, Mapping) or not nmo:
        return
    for k in NARRATIVE_MODE_OUTPUT_FEM_KEYS:
        if k not in nmo:
            continue
        v = nmo.get(k)
        if k == "narrative_mode_output_failure_reasons" and isinstance(v, (list, tuple)):
            meta[k] = [str(x) for x in v if str(x).strip()]
        elif k == "narrative_mode_output_observed_signals" and isinstance(v, Mapping):
            meta[k] = {str(k2): bool(v2) for k2, v2 in v.items()}
        elif k == "narrative_mode_output_skip_reason" and v is not None:
            meta[k] = str(v).strip() or None
        else:
            meta[k] = v


# Raw NA merge keys on FEM (gate/write path). ``failure_reasons`` mirrors validator ``failure_reasons``;
# ``reason_codes`` is the packaged list used in traces; both may coexist — canonical **events**
# merge them; do not delete either stable raw key.
NARRATIVE_AUTHENTICITY_FEM_KEYS: frozenset[str] = frozenset(
    {
        "narrative_authenticity_checked",
        "narrative_authenticity_failed",
        "narrative_authenticity_failure_reasons",
        "narrative_authenticity_repaired",
        "narrative_authenticity_repair_applied",
        "narrative_authenticity_repair_mode",
        "narrative_authenticity_repair_modes",
        "narrative_authenticity_skip_reason",
        "narrative_authenticity_reason_codes",
        "narrative_authenticity_metrics",
        "narrative_authenticity_evidence",
        "narrative_authenticity_status",
        "narrative_authenticity_trace",
        "narrative_authenticity_relaxation_flags",
        "narrative_authenticity_rumor_relaxed_low_signal",
    }
)


def default_narrative_authenticity_layer_meta() -> Dict[str, Any]:
    """Metadata-only owner for NA layer write-time defaults before merge/package steps."""
    return {
        "narrative_authenticity_checked": False,
        "narrative_authenticity_failed": False,
        "narrative_authenticity_failure_reasons": [],
        "narrative_authenticity_repaired": False,
        "narrative_authenticity_repair_applied": False,
        "narrative_authenticity_repair_mode": None,
        "narrative_authenticity_repair_modes": [],
        "narrative_authenticity_skip_reason": None,
        "narrative_authenticity_reason_codes": [],
        "narrative_authenticity_metrics": None,
        "narrative_authenticity_evidence": None,
        "narrative_authenticity_status": None,
        "narrative_authenticity_trace": None,
        "narrative_authenticity_relaxation_flags": None,
        "narrative_authenticity_rumor_relaxed_low_signal": False,
        "narrative_authenticity_boundary_semantic_repair_disabled": False,
    }


def package_emission_channel_sidecar(
    *,
    debug_top_level: Mapping[str, Any] | None,
    author_top_level: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Normalize debug/meta sidecar content stored under ``gm_output['internal_state']`` (author channel).

    Values are shallow copies suitable for deterministic inspection; not a second classifier.
    """
    out: dict[str, Any] = {}
    if isinstance(debug_top_level, Mapping) and debug_top_level:
        out["emission_debug_lane"] = dict(debug_top_level)
    if isinstance(author_top_level, Mapping) and author_top_level:
        out["emission_author_lane"] = dict(author_top_level)
    return out


def read_debug_notes_from_turn_payload(payload: Mapping[str, Any] | None) -> str:
    """Return concatenated ``debug_notes`` from an API envelope or a post-gate ``gm_output`` dict.

    Prefers ``gm_output_debug.emission_debug_lane`` when present (HTTP responses), then legacy
    top-level ``gm_output['debug_notes']``, then the emission debug lane on a gate-shaped dict.
    """
    if not isinstance(payload, Mapping):
        return ""
    dpkg = payload.get("gm_output_debug")
    if isinstance(dpkg, Mapping):
        lane = dpkg.get("emission_debug_lane")
        if isinstance(lane, Mapping):
            s = lane.get("debug_notes")
            if isinstance(s, str) and s.strip():
                return s
    gm = payload.get("gm_output")
    if isinstance(gm, Mapping):
        top = gm.get("debug_notes")
        if isinstance(top, str) and top.strip():
            return top
        lane2 = read_emission_debug_lane(gm)
        s2 = lane2.get("debug_notes")
        if isinstance(s2, str) and s2.strip():
            return s2
    if "player_facing_text" in payload:
        lane3 = read_emission_debug_lane(payload)
        s3 = lane3.get("debug_notes")
        if isinstance(s3, str):
            return str(s3)
    return ""


def read_emission_debug_lane(gm_output: Mapping[str, Any] | None) -> dict[str, Any]:
    """Shallow read of debug-classified top-level keys from a post-gate ``gm_output`` (or legacy mixed dict)."""
    if not isinstance(gm_output, Mapping):
        return {}
    internal = gm_output.get(INTERNAL_STATE_KEY)
    if isinstance(internal, Mapping):
        lane = internal.get(EMISSION_DEBUG_LANE_KEY)
        if isinstance(lane, Mapping):
            return dict(lane)
    return project_debug_payload(gm_output)


def read_final_emission_meta_dict(gm_output: Mapping[str, Any] | None) -> dict[str, Any]:
    """Read **raw** FEM dict from post-gate sidecar, else legacy top-level ``_final_emission_meta``.

    Returns a shallow copy of whatever the pipeline wrote (stable key names, but no
    coercion of nested subtrees). For **normalized** FEM intended for evaluator-style
    consumers, use :func:`normalize_final_emission_meta_for_observability` on the result.

    Precedence is **sidecar first** to align with the post-finalization contract. Legacy top-level
    FEM is accepted as a compatibility fallback for older/mixed dicts and unit fixtures.
    """
    if not isinstance(gm_output, Mapping):
        return {}
    lane = read_emission_debug_lane(gm_output)
    nested = lane.get(FINAL_EMISSION_META_KEY)
    if isinstance(nested, Mapping):
        return dict(nested)
    fem = gm_output.get(FINAL_EMISSION_META_KEY)
    return dict(fem) if isinstance(fem, Mapping) else {}


def read_emission_debug_lane_from_turn_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Read emission debug lane from an API envelope or a gate-shaped ``gm_output`` mapping.

    Ownership boundary:
    - **Write-time packaging** of sidecars is owned by :func:`game.final_emission_gate.apply_final_emission_gate`
      (via :func:`package_emission_channel_sidecar`).
    - **Read-time normalization** is owned here.
    - This function is observational-only and must not drive legality/routing.
    """
    if not isinstance(payload, Mapping):
        return {}
    dbg = payload.get("gm_output_debug")
    if isinstance(dbg, Mapping):
        lane = dbg.get(EMISSION_DEBUG_LANE_KEY)
        if isinstance(lane, Mapping):
            return dict(lane)
    gm = payload.get("gm_output")
    if not isinstance(gm, Mapping):
        gm = payload
    return read_emission_debug_lane(gm if isinstance(gm, Mapping) else None)


def read_final_emission_meta_from_turn_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Read **raw** FEM from an API envelope or gate-shaped ``gm_output`` (pure read-side).

    Same precedence and legacy fallback as :func:`read_final_emission_meta_dict`; does not
    normalize nested NA or dead-turn defaults — that is a separate observational step.
    """
    if not isinstance(payload, Mapping):
        return {}
    dbg_lane = read_emission_debug_lane_from_turn_payload(payload)
    nested = dbg_lane.get(FINAL_EMISSION_META_KEY)
    if isinstance(nested, Mapping):
        return dict(nested)
    gm = payload.get("gm_output")
    if not isinstance(gm, Mapping):
        gm = payload
    return read_final_emission_meta_dict(gm if isinstance(gm, Mapping) else None)


def merge_narrative_authenticity_into_final_emission_meta(meta: Dict[str, Any], na_dbg: Dict[str, Any]) -> None:
    """Metadata-only packager for NA fields into ``_final_emission_meta`` (in place)."""
    meta.update(
        {
            "narrative_authenticity_checked": bool(na_dbg.get("narrative_authenticity_checked")),
            "narrative_authenticity_failed": bool(na_dbg.get("narrative_authenticity_failed")),
            "narrative_authenticity_failure_reasons": list(na_dbg.get("narrative_authenticity_failure_reasons") or []),
            "narrative_authenticity_repaired": bool(na_dbg.get("narrative_authenticity_repaired")),
            "narrative_authenticity_repair_applied": bool(na_dbg.get("narrative_authenticity_repair_applied")),
            "narrative_authenticity_repair_mode": na_dbg.get("narrative_authenticity_repair_mode"),
            "narrative_authenticity_repair_modes": list(na_dbg.get("narrative_authenticity_repair_modes") or []),
            "narrative_authenticity_skip_reason": na_dbg.get("narrative_authenticity_skip_reason"),
            "narrative_authenticity_reason_codes": list(na_dbg.get("narrative_authenticity_reason_codes") or []),
            "narrative_authenticity_metrics": na_dbg.get("narrative_authenticity_metrics"),
            "narrative_authenticity_evidence": na_dbg.get("narrative_authenticity_evidence"),
            "narrative_authenticity_status": na_dbg.get("narrative_authenticity_status"),
            "narrative_authenticity_trace": na_dbg.get("narrative_authenticity_trace"),
            "narrative_authenticity_relaxation_flags": na_dbg.get("narrative_authenticity_relaxation_flags"),
            "narrative_authenticity_rumor_relaxed_low_signal": bool(
                na_dbg.get("narrative_authenticity_rumor_relaxed_low_signal")
            ),
            "narrative_authenticity_boundary_semantic_repair_disabled": bool(
                na_dbg.get("narrative_authenticity_boundary_semantic_repair_disabled")
            ),
        }
    )


def slim_na_metrics(metrics: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(metrics, Mapping):
        return {}
    out: Dict[str, Any] = {}
    for k, v in metrics.items():
        if v is None:
            continue
        if isinstance(v, float):
            out[str(k)] = round(v, 4)
        elif isinstance(v, (int, str, bool)):
            out[str(k)] = v
    return out


def slim_na_evidence(evidence: Mapping[str, Any] | None, *, max_str: int = 120, max_list: int = 6) -> Dict[str, Any]:
    if not isinstance(evidence, Mapping):
        return {}

    def clip(x: Any) -> Any:
        if isinstance(x, str) and len(x) > max_str:
            return x[: max(0, max_str - 1)] + "…"
        if isinstance(x, list):
            return [clip(i) for i in x[:max_list]]
        if isinstance(x, dict):
            return {str(k2): clip(v2) for k2, v2 in list(x.items())[:8]}
        return x

    return {str(k): clip(v) for k, v in evidence.items()}


def resolve_narrative_authenticity_emission_status(
    validation: Mapping[str, Any],
    *,
    repaired: bool,
    repair_failed: bool,
) -> str | None:
    """Terminal status for gate/meta (``pass`` / ``relaxed`` / ``repaired`` / ``fail``); None if unchecked or non-terminal."""
    checked = bool(validation.get("checked"))
    if not checked:
        return None
    if repaired:
        return "repaired"
    if repair_failed:
        return "fail"
    if bool(validation.get("passed")):
        return "relaxed" if bool(validation.get("rumor_realism_relaxed_low_signal")) else "pass"
    # Checked failure before a repair outcome is applied — omit status until the layer finishes.
    return None


def build_narrative_authenticity_trace_slice(
    validation: Mapping[str, Any] | None,
    *,
    contract: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Nested compact rumor / classifier context (contract trace + validation relaxation signals)."""
    trace_out: Dict[str, Any] = {}
    rumor_turn = False
    if isinstance(contract, Mapping):
        tr = contract.get("trace") if isinstance(contract.get("trace"), Mapping) else {}
        rumor_turn = bool(tr.get("rumor_turn_active"))
        if rumor_turn:
            trace_out["rumor_turn_active"] = True
            rrc = tr.get("rumor_turn_reason_codes")
            if isinstance(rrc, list) and rrc:
                trace_out["rumor_turn_reason_codes"] = [str(x) for x in rrc[:10] if str(x).strip()]
            rts = tr.get("rumor_trigger_spans")
            if isinstance(rts, list) and rts:
                trace_out["rumor_trigger_spans"] = rts[:6]
    if isinstance(validation, Mapping):
        if validation.get("rumor_realism_relaxed_low_signal"):
            trace_out["rumor_realism_relaxed_low_signal"] = True
        vflags = validation.get("rumor_realism_relaxation_flags")
        if isinstance(vflags, Mapping) and any(vflags.values()):
            trace_out["rumor_relaxation_flags"] = {str(k): bool(v) for k, v in vflags.items() if v}
    return trace_out


def build_narrative_authenticity_emission_trace(
    validation: Mapping[str, Any] | None,
    *,
    contract: Mapping[str, Any] | None = None,
    repaired: bool = False,
    repair_mode: str | None = None,
    repair_failed: bool = False,
) -> Dict[str, Any]:
    """Single **canonical write-time** NA telemetry bundle for ``_final_emission_meta`` (and layer debug dict).

    Shapes: contract trace slice, validation summary hooks (skip / reasons), slim metrics/evidence,
    terminal ``narrative_authenticity_status`` when defined, relaxation flags, repair mode list.
    """
    if not isinstance(validation, Mapping):
        return {}
    out: Dict[str, Any] = {}
    sr = validation.get("skip_reason")
    if isinstance(sr, str) and sr.strip():
        out["narrative_authenticity_skip_reason"] = sr.strip()
    checked = bool(validation.get("checked"))
    passed = bool(validation.get("passed"))
    reasons = [str(x) for x in (validation.get("failure_reasons") or []) if str(x).strip()]
    if reasons:
        out["narrative_authenticity_reason_codes"] = reasons
    metrics_obj = validation.get("metrics")
    rumor_turn = bool((metrics_obj or {}).get("rumor_turn_active")) if isinstance(metrics_obj, Mapping) else False
    if checked and (reasons or not passed or rumor_turn):
        out["narrative_authenticity_metrics"] = slim_na_metrics(validation.get("metrics"))
        out["narrative_authenticity_evidence"] = slim_na_evidence(validation.get("evidence"))
    status = resolve_narrative_authenticity_emission_status(
        validation, repaired=repaired, repair_failed=repair_failed
    )
    if status is not None:
        out["narrative_authenticity_status"] = status
    rf = validation.get("rumor_realism_relaxation_flags") if isinstance(validation, Mapping) else None
    if isinstance(rf, Mapping) and any(rf.values()):
        out["narrative_authenticity_relaxation_flags"] = {str(k): bool(v) for k, v in rf.items() if v}
    if bool(validation.get("rumor_realism_relaxed_low_signal")):
        out["narrative_authenticity_rumor_relaxed_low_signal"] = True
    slice_trace = build_narrative_authenticity_trace_slice(validation, contract=contract)
    if slice_trace:
        out["narrative_authenticity_trace"] = slice_trace
    if repair_mode:
        out["narrative_authenticity_repair_mode"] = repair_mode
        out["narrative_authenticity_repair_modes"] = [repair_mode]
    else:
        out["narrative_authenticity_repair_modes"] = []
    return out


def _tag_set(gm_output: Mapping[str, Any]) -> frozenset[str]:
    raw = gm_output.get("tags") if isinstance(gm_output.get("tags"), list) else []
    return frozenset(str(t).strip() for t in raw if isinstance(t, str) and str(t).strip())


def _upstream_api_error(md: Mapping[str, Any]) -> Dict[str, Any] | None:
    err = md.get("upstream_api_error")
    return dict(err) if isinstance(err, dict) and err else None


def _infra_error_tags(tags: frozenset[str]) -> bool:
    if "gpt_api_error_nonretryable" in tags:
        return True
    return any(t.startswith("upstream_api_failure:") for t in tags)


def _fast_fallback_lane(*, md: Mapping[str, Any], tags: frozenset[str]) -> bool:
    if str(md.get("latency_mode") or "").strip() == "fast_fallback":
        return True
    if "upstream_api_fast_fallback" in tags:
        return True
    if "fast_fallback" in tags:
        return True
    return False


def _forced_retry_terminal_route(gm_output: Mapping[str, Any]) -> bool:
    return str(gm_output.get("accepted_via") or "").strip() == "forced_fallback" and str(
        gm_output.get("final_route") or ""
    ).strip() == "forced_retry_fallback"


def _strong_infra_dead_signals(
    *,
    has_upstream: bool,
    fast_fallback_lane: bool,
    forced_terminal: bool,
    tags: frozenset[str],
) -> bool:
    """Explicit infra / API failure bundle (not merely ``retry_exhausted`` on a repair path)."""
    if has_upstream and (fast_fallback_lane or _infra_error_tags(tags) or forced_terminal):
        return True
    return False


def classify_dead_turn(gm_output: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Deterministic classifier: turns that did not run through the intended model path.

    Policy is intentionally narrow: generic ``forced_retry_fallback`` text or tags alone
    never mark a dead turn without explicit upstream / fast-fallback / forced-terminal
    metadata defined in this function.
    """
    base = {
        "is_dead_turn": False,
        "dead_turn_reason_codes": [],
        "dead_turn_class": "none",
        "validation_playable": True,
        "manual_test_valid": True,
    }
    if not isinstance(gm_output, Mapping):
        return dict(base)

    md = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
    tags = _tag_set(gm_output)
    upstream = _upstream_api_error(md)
    has_upstream = upstream is not None
    fast_fb = _fast_fallback_lane(md=md, tags=tags)
    forced_terminal = _forced_retry_terminal_route(gm_output)
    retry_bundle = gm_output.get("retry_exhausted") is True and gm_output.get("targeted_retry_terminal") is True
    malformed = md.get("malformed_emergency_output") is True

    reason_codes: list[str] = []
    if malformed:
        reason_codes.append("malformed_emergency_output")
    if has_upstream:
        reason_codes.append("upstream_api_error")
        fc = str((upstream or {}).get("failure_class") or "").strip()
        if fc:
            reason_codes.append(f"upstream_failure_class:{fc}")
    if fast_fb:
        reason_codes.append("fast_fallback_lane")
    if forced_terminal:
        reason_codes.append("forced_retry_terminal_route")
    if retry_bundle:
        reason_codes.append("retry_exhausted_targeted_retry_terminal")
    if _infra_error_tags(tags):
        reason_codes.append("infra_error_tags")

    if malformed:
        out = dict(base)
        out["is_dead_turn"] = True
        out["dead_turn_reason_codes"] = reason_codes
        out["dead_turn_class"] = "malformed_emergency_output"
        out["validation_playable"] = False
        out["manual_test_valid"] = False
        return out

    accepted = str(gm_output.get("accepted_via") or "").strip()
    if accepted in _LEGITIMATE_RESOLUTION_REPAIR_ACCEPTED_VIA:
        if not _strong_infra_dead_signals(
            has_upstream=has_upstream,
            fast_fallback_lane=fast_fb,
            forced_terminal=forced_terminal,
            tags=tags,
        ):
            return dict(base)

    is_dead = bool(
        has_upstream
        and (
            fast_fb
            or _infra_error_tags(tags)
            or (forced_terminal and retry_bundle)
        )
    )

    if not is_dead:
        return dict(base)

    dead_class = "upstream_api_failure"
    if forced_terminal and retry_bundle and (fast_fb or "retry_escape_hatch" in tags):
        dead_class = "retry_terminal_fallback"
    elif has_upstream and forced_terminal and not (retry_bundle and (fast_fb or "retry_escape_hatch" in tags)):
        dead_class = "forced_fallback_nonplayable"

    out = dict(base)
    out["is_dead_turn"] = True
    out["dead_turn_reason_codes"] = reason_codes
    out["dead_turn_class"] = dead_class
    out["validation_playable"] = False
    out["manual_test_valid"] = False
    return out


def package_dead_turn_snapshot_into_final_emission_meta(gm_output: MutableMapping[str, Any]) -> None:
    """Metadata-only dead-turn packager used by the gate at finalize time."""
    if not isinstance(gm_output, MutableMapping):
        return
    status = classify_dead_turn(gm_output)
    meta = gm_output.get("_final_emission_meta")
    if not isinstance(meta, dict):
        meta = {}
        gm_output["_final_emission_meta"] = meta
    meta["dead_turn"] = status


def merge_dead_turn_classification_into_final_emission_meta(gm_output: MutableMapping[str, Any]) -> None:
    """Compatibility residue alias for older call sites; canonical owner stays in this module."""
    package_dead_turn_snapshot_into_final_emission_meta(gm_output)


_DEAD_TURN_READ_DEFAULTS: Dict[str, Any] = {
    "is_dead_turn": False,
    "dead_turn_reason_codes": [],
    "dead_turn_class": "none",
    "validation_playable": True,
    "manual_test_valid": True,
}


def read_dead_turn_from_gm_output(gm_output: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Read-only view of DTD1 status from FEM ``dead_turn`` (sidecar or legacy top-level).

    Does **not** classify or merge; missing keys yield stable defaults (validation_playable=True).
    """
    out = dict(_DEAD_TURN_READ_DEFAULTS)
    if not isinstance(gm_output, Mapping):
        return out
    fem = read_final_emission_meta_dict(gm_output)
    if not fem:
        return out
    snap = fem.get("dead_turn")
    if not isinstance(snap, Mapping):
        return out
    if "is_dead_turn" in snap:
        out["is_dead_turn"] = bool(snap.get("is_dead_turn"))
    rc = snap.get("dead_turn_reason_codes")
    if isinstance(rc, list):
        out["dead_turn_reason_codes"] = [str(x) for x in rc if str(x).strip()]
    dc = snap.get("dead_turn_class")
    if isinstance(dc, str) and dc.strip():
        out["dead_turn_class"] = dc.strip()
    if "validation_playable" in snap:
        out["validation_playable"] = bool(snap.get("validation_playable"))
    if "manual_test_valid" in snap:
        out["manual_test_valid"] = bool(snap.get("manual_test_valid"))
    return out


def summarize_gameplay_validation_for_turn(dt: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Aggregate evaluation policy fields from a DTD1 ``dead_turn`` snapshot (already read from FEM)."""
    row = dict(dt or _DEAD_TURN_READ_DEFAULTS)
    validation_playable = bool(row.get("validation_playable", True))
    is_dead = bool(row.get("is_dead_turn"))
    excluded = not validation_playable
    dead_turn_count = 1 if is_dead else 0
    infra_failure_count = 1 if is_dead else 0
    invalidation_reason: str | None = None
    if excluded:
        if is_dead:
            cls = str(row.get("dead_turn_class") or "unknown").strip() or "unknown"
            invalidation_reason = f"excluded_from_score:dead_turn:{cls}"
        else:
            invalidation_reason = "excluded_from_score:non_playable_turn"
    return {
        "run_valid": not excluded,
        "excluded_from_scoring": excluded,
        "invalidation_reason": invalidation_reason,
        "dead_turn_count": dead_turn_count,
        "infra_failure_count": infra_failure_count,
        "dead_turn": dict(row),
    }


def normalize_merged_na_telemetry_for_eval(merged: Mapping[str, Any] | None) -> dict[str, Any]:
    """Read-side: shallow copy with stable empty mappings for nested NA telemetry (no policy inference).

    Input is typically a **raw** merged NA dict (FEM keys + optional harness overrides); output
    keeps the same keys but replaces ``None`` / non-mapping nested payloads with ``{}`` for
    metrics/trace/evidence/relaxation flags. Proof-layer consumers treat absent vs ``None`` nested
    dicts consistently without duplicating guards.
    """
    out = dict(merged or {})
    for k in (
        "narrative_authenticity_metrics",
        "narrative_authenticity_trace",
        "narrative_authenticity_evidence",
        "narrative_authenticity_relaxation_flags",
    ):
        v = out.get(k)
        if v is None or not isinstance(v, Mapping):
            out[str(k)] = {}
        else:
            out[str(k)] = dict(v)
    return out


def stage_diff_narrative_authenticity_projection(fem: Mapping[str, Any] | None) -> dict[str, Any]:
    """Curated NA projection allowed for bounded stage-diff observability.

    This returns a compact dict with a small, explicit key whitelist. It never returns raw,
    arbitrary pass-through JSON from FEM, and it does not infer legality.

    **Reason-list alias collapse (read-side):** FEM may carry both
    ``narrative_authenticity_reason_codes`` and ``narrative_authenticity_failure_reasons``.
    They are the same semantic family as gate ``failure_reasons`` vs packaged ``reason_codes``;
    this projection merges them into a **single** deduped ``narrative_authenticity_reason_codes``
    list so stage snapshots do not double-track codes. Raw FEM keys on disk are unchanged —
    only this bounded read surface collapses duplicates.
    """
    if not isinstance(fem, Mapping):
        return {}
    out: dict[str, Any] = {}
    merged_codes: list[str] = []
    merged_codes.extend(normalize_reason_list(fem.get("narrative_authenticity_reason_codes")))
    merged_codes.extend(normalize_reason_list(fem.get("narrative_authenticity_failure_reasons")))
    merged_codes = list(dict.fromkeys(merged_codes))[:16]

    for k in sorted(STAGE_DIFF_ALLOWED_NA_PROJECTION_KEYS):
        if k == "narrative_authenticity_reason_codes":
            if merged_codes:
                out[k] = [str(x) for x in merged_codes if str(x).strip()]
            continue
        v = fem.get(k)
        if v is None:
            continue
        if isinstance(v, bool):
            out[k] = v
        elif isinstance(v, str):
            out[k] = v
        elif isinstance(v, (int, float)):
            out[k] = v
        else:
            # Explicitly avoid widening the surface with nested dicts/lists.
            continue
    trace = fem.get("narrative_authenticity_trace")
    if isinstance(trace, Mapping) and "rumor_turn_active" in trace:
        out["rumor_turn_active"] = bool(trace.get("rumor_turn_active"))
    return out


def normalize_final_emission_meta_for_observability(fem: Mapping[str, Any] | None) -> dict[str, Any]:
    """Read-side **normalized** FEM view for observability (observational-only; no policy inference).

    **Raw vs normalized:** :func:`read_final_emission_meta_dict` returns pipeline-shaped FEM;
    this function returns a shallow-normalized copy with stable defaults for nested NA and
    dead-turn subtrees so offline tools need fewer null guards.

    - Pure function.
    - Fills missing nested dict/list fields deterministically for evaluator/debug consumers.
    - Does not broaden payloads with arbitrary pass-through keys; it only coerces known nested subtrees.
    """
    base = dict(fem or {}) if isinstance(fem, Mapping) else {}

    # Dead-turn subtree: fill stable defaults if absent or malformed.
    snap = base.get(FEM_DEAD_TURN_KEY)
    if not isinstance(snap, Mapping):
        base[FEM_DEAD_TURN_KEY] = dict(_DEAD_TURN_READ_DEFAULTS)
    else:
        merged = dict(_DEAD_TURN_READ_DEFAULTS)
        merged.update(dict(snap))
        base[FEM_DEAD_TURN_KEY] = merged

    # NA nested dicts: stable empty mappings (no policy inference).
    base = normalize_merged_na_telemetry_for_eval(base)

    # Ensure common NA lists are stable lists when present-but-nullish.
    for lk in ("narrative_authenticity_reason_codes", "narrative_authenticity_failure_reasons"):
        v = base.get(lk)
        if v is None:
            continue
        if not isinstance(v, list):
            base[lk] = []
        else:
            base[lk] = [str(x) for x in v if str(x).strip()]
    return base


_FEM_OBS_NA_SIGNAL_KEYS: frozenset[str] = frozenset(
    {
        "narrative_authenticity_checked",
        "narrative_authenticity_failed",
        "narrative_authenticity_repaired",
        "narrative_authenticity_repair_applied",
        "narrative_authenticity_skip_reason",
        "narrative_authenticity_status",
        "narrative_authenticity_reason_codes",
        "narrative_authenticity_failure_reasons",
        "narrative_authenticity_rumor_relaxed_low_signal",
    }
)

_FEM_OBS_AC_SIGNAL_KEYS: frozenset[str] = frozenset(
    {
        "answer_completeness_checked",
        "answer_completeness_failed",
        "answer_completeness_repaired",
        "answer_completeness_skip_reason",
        "answer_completeness_failure_reasons",
    }
)

_FEM_OBS_RD_SIGNAL_KEYS: frozenset[str] = frozenset(
    {
        "response_delta_checked",
        "response_delta_failed",
        "response_delta_repaired",
        "response_delta_skip_reason",
        "response_delta_failure_reasons",
    }
)

_FEM_OBS_FB_SIGNAL_KEYS: frozenset[str] = frozenset(
    {
        "fallback_behavior_contract_present",
        "fallback_behavior_checked",
        "fallback_behavior_failed",
        "fallback_behavior_repaired",
        "fallback_behavior_skip_reason",
        "fallback_behavior_failure_reasons",
        "fallback_behavior_uncertainty_active",
    }
)


def _fem_clip_str(value: Any, *, limit: int = 120) -> str | None:
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    if len(s) <= limit:
        return s
    return s[: max(0, limit - 1)] + "…"


def _fem_na_action(fem: Mapping[str, Any]) -> str:
    skip = fem.get("narrative_authenticity_skip_reason")
    if isinstance(skip, str) and skip.strip() and not bool(fem.get("narrative_authenticity_checked")):
        return TELEMETRY_ACTION_SKIPPED
    if bool(fem.get("narrative_authenticity_repaired")) or bool(fem.get("narrative_authenticity_repair_applied")):
        return TELEMETRY_ACTION_REPAIRED
    if bool(fem.get("narrative_authenticity_checked")):
        return TELEMETRY_ACTION_OBSERVED
    return TELEMETRY_ACTION_UNKNOWN


def _fem_layer_action(
    fem: Mapping[str, Any],
    *,
    checked_key: str,
    skip_key: str,
    repaired_key: str,
) -> str:
    skip = fem.get(skip_key)
    if isinstance(skip, str) and skip.strip() and not bool(fem.get(checked_key)):
        return TELEMETRY_ACTION_SKIPPED
    if bool(fem.get(repaired_key)):
        return TELEMETRY_ACTION_REPAIRED
    if bool(fem.get(checked_key)):
        return TELEMETRY_ACTION_OBSERVED
    return TELEMETRY_ACTION_UNKNOWN


def _fem_response_type_action(fem: Mapping[str, Any]) -> str:
    if bool(fem.get("response_type_repair_used")):
        return TELEMETRY_ACTION_REPAIRED
    if fem.get("response_type_candidate_ok") is False:
        return TELEMETRY_ACTION_SKIPPED
    if fem.get("response_type_required") is not None and str(fem.get("response_type_required") or "").strip():
        return TELEMETRY_ACTION_OBSERVED
    return TELEMETRY_ACTION_UNKNOWN


# Compatibility surface: runtime-lineage projection lives in final_emission_replay_projection;
# keep this import path stable for replay/dashboard consumers. Its event ``owner`` field
# currently means selector/application owner, while fallback authorship evidence remains in
# fields such as ``opening_fallback_authorship_source`` and ``opening_fallback_owner_bucket``.
# Successful opening fallback also projects additive split fields for selection/content owner.
from game.final_emission_replay_projection import build_fem_runtime_lineage_events


def build_fem_observability_events(fem: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    """Project FEM into a bounded list of canonical observational events (:mod:`game.telemetry_vocab`).

    ``phase`` is ``gate`` because FEM carries post-gate validator/repair traces, not because this
    function gates anything. Read-side only: no legality interpretation, no stage-diff/evaluator
    semantic ownership, no arbitrary FEM pass-through in ``data``. NA ``reasons`` merge
    ``narrative_authenticity_failure_reasons`` with ``narrative_authenticity_reason_codes``.
    """
    if not isinstance(fem, Mapping):
        return []

    events: list[dict[str, Any]] = []

    if any(k in fem for k in _FEM_OBS_NA_SIGNAL_KEYS):
        na_reasons = normalize_reason_list(fem.get("narrative_authenticity_failure_reasons")) + normalize_reason_list(
            fem.get("narrative_authenticity_reason_codes")
        )
        na_reasons = list(dict.fromkeys(na_reasons))[:16]
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner="narrative_authenticity",
                action=_fem_na_action(fem),
                reasons=na_reasons,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "checked": bool(fem.get("narrative_authenticity_checked")),
                    "failed": bool(fem.get("narrative_authenticity_failed")),
                    "repaired": bool(fem.get("narrative_authenticity_repaired"))
                    or bool(fem.get("narrative_authenticity_repair_applied")),
                    "status": _fem_clip_str(fem.get("narrative_authenticity_status"), limit=24),
                    "skip_reason": _fem_clip_str(fem.get("narrative_authenticity_skip_reason")),
                    "rumor_relaxed_low_signal": bool(fem.get("narrative_authenticity_rumor_relaxed_low_signal")),
                },
            )
        )

    if any(k in fem for k in _FEM_OBS_AC_SIGNAL_KEYS):
        ac_reasons = normalize_reason_list(fem.get("answer_completeness_failure_reasons"))[:16]
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner="answer_completeness",
                action=_fem_layer_action(
                    fem,
                    checked_key="answer_completeness_checked",
                    skip_key="answer_completeness_skip_reason",
                    repaired_key="answer_completeness_repaired",
                ),
                reasons=ac_reasons,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "checked": bool(fem.get("answer_completeness_checked")),
                    "failed": bool(fem.get("answer_completeness_failed")),
                    "repaired": bool(fem.get("answer_completeness_repaired")),
                    "repair_mode": _fem_clip_str(fem.get("answer_completeness_repair_mode")),
                    "skip_reason": _fem_clip_str(fem.get("answer_completeness_skip_reason")),
                    "expected_voice": _fem_clip_str(fem.get("answer_completeness_expected_voice")),
                },
            )
        )

    if any(k in fem for k in _FEM_OBS_RD_SIGNAL_KEYS):
        rd_reasons = normalize_reason_list(fem.get("response_delta_failure_reasons"))[:16]
        echo_ratio_raw = fem.get("response_delta_echo_overlap_ratio")
        echo_out: float | None
        if isinstance(echo_ratio_raw, bool) or echo_ratio_raw is None:
            echo_out = None
        elif isinstance(echo_ratio_raw, (int, float)):
            echo_out = float(echo_ratio_raw)
        else:
            echo_out = None
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner="response_delta",
                action=_fem_layer_action(
                    fem,
                    checked_key="response_delta_checked",
                    skip_key="response_delta_skip_reason",
                    repaired_key="response_delta_repaired",
                ),
                reasons=rd_reasons,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "checked": bool(fem.get("response_delta_checked")),
                    "failed": bool(fem.get("response_delta_failed")),
                    "repaired": bool(fem.get("response_delta_repaired")),
                    "kind_detected": _fem_clip_str(fem.get("response_delta_kind_detected"), limit=48),
                    "echo_overlap_ratio": echo_out,
                    "skip_reason": _fem_clip_str(fem.get("response_delta_skip_reason")),
                    "trigger_source": _fem_clip_str(fem.get("response_delta_trigger_source")),
                },
            )
        )

    if any(k in fem for k in _FEM_OBS_FB_SIGNAL_KEYS):
        fb_reasons = normalize_reason_list(fem.get("fallback_behavior_failure_reasons"))[:16]
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner="fallback_behavior",
                action=_fem_layer_action(
                    fem,
                    checked_key="fallback_behavior_checked",
                    skip_key="fallback_behavior_skip_reason",
                    repaired_key="fallback_behavior_repaired",
                ),
                reasons=fb_reasons,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "contract_present": bool(fem.get("fallback_behavior_contract_present")),
                    "checked": bool(fem.get("fallback_behavior_checked")),
                    "failed": bool(fem.get("fallback_behavior_failed")),
                    "repaired": bool(fem.get("fallback_behavior_repaired")),
                    "uncertainty_active": bool(fem.get("fallback_behavior_uncertainty_active")),
                    "repair_mode": _fem_clip_str(str(fem.get("fallback_behavior_repair_mode") or ""), limit=48),
                    "skip_reason": _fem_clip_str(fem.get("fallback_behavior_skip_reason")),
                    "clarifying_question_used": bool(fem.get("fallback_behavior_clarifying_question_used")),
                    "partial_used": bool(fem.get("fallback_behavior_partial_used")),
                },
            )
        )

    if any(k in fem for k in FEM_RESPONSE_TYPE_KEYS):
        rt_reasons = normalize_reason_list(fem.get("response_type_rejection_reasons"))[:16]
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner="response_type",
                action=_fem_response_type_action(fem),
                reasons=rt_reasons,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "required": _fem_clip_str(fem.get("response_type_required"), limit=48),
                    "contract_source": _fem_clip_str(fem.get("response_type_contract_source"), limit=64),
                    "candidate_ok": fem.get("response_type_candidate_ok"),
                    "repair_used": bool(fem.get("response_type_repair_used")),
                    "repair_kind": _fem_clip_str(fem.get("response_type_repair_kind"), limit=64),
                    "non_hostile_escalation_blocked": bool(fem.get("non_hostile_escalation_blocked")),
                },
            )
        )

    snap = fem.get(FEM_DEAD_TURN_KEY)
    if isinstance(snap, Mapping):
        rc = normalize_reason_list(snap.get("dead_turn_reason_codes"))[:8]
        events.append(
            build_telemetry_event(
                phase=TELEMETRY_PHASE_GATE,
                owner="dead_turn",
                action=TELEMETRY_ACTION_OBSERVED,
                reasons=rc,
                scope=TELEMETRY_SCOPE_TURN,
                data={
                    "is_dead_turn": bool(snap.get("is_dead_turn")),
                    "dead_turn_class": _fem_clip_str(snap.get("dead_turn_class"), limit=48) or "none",
                    "validation_playable": bool(snap.get("validation_playable", True)),
                    "manual_test_valid": bool(snap.get("manual_test_valid", True)),
                },
            )
        )

    # Hard cap: six curated domains; keep deterministic ordering already implied by append order.
    return events[:6]


def _curated_stage_diff_surface_for_bundle(stage_diff: Mapping[str, Any] | None) -> dict[str, Any]:
    """Shallow-stable copies of bounded stage-diff lists only (no arbitrary metadata pass-through).

    Keys are iterated in sorted order so the returned dict is stable across process runs
    (``frozenset`` iteration order is not guaranteed). ``stage_diff`` itself is owned by
    :mod:`game.stage_diff_telemetry`; this helper only copies the bundle allow-list.
    """
    if not isinstance(stage_diff, Mapping):
        return {}
    sdt = importlib.import_module("game.stage_diff_telemetry")
    bundle_keys = getattr(sdt, "STAGE_DIFF_BUNDLE_SURFACE_KEYS", frozenset())

    out: dict[str, Any] = {}
    for key in sorted(bundle_keys):
        if key not in stage_diff:
            continue
        raw = stage_diff.get(key)
        if not isinstance(raw, list):
            continue
        if key == "snapshots":
            out[key] = [dict(s) if isinstance(s, Mapping) else s for s in raw]
        else:
            out[key] = [dict(t) if isinstance(t, Mapping) else t for t in raw]
    return out


def assemble_unified_observational_telemetry_bundle(
    *,
    fem: Mapping[str, Any] | None = None,
    stage_diff: Mapping[str, Any] | None = None,
    evaluator_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble normalized FEM plus observational event projections from read-side inputs.

    ``final_emission_meta`` / ``fem_observability_events`` are built here. Stage-diff lists and
    events come from :mod:`game.stage_diff_telemetry`; evaluator events from
    :mod:`game.narrative_authenticity_eval` (separate from the evaluator scoring dict).
    ``fem_runtime_lineage_events`` is a sibling H1/H2 projection rather than an element of the
    canonical ``phase``/``action`` envelope.

    Stage-diff and evaluator builders are loaded with :func:`importlib.import_module` to avoid
    static import cycles at module import time (same behavior as eager imports).

    Read-side only; telemetry must not drive gate decisions.
    """
    fem_norm = normalize_final_emission_meta_for_observability(fem if isinstance(fem, Mapping) else None)
    fem_events = build_fem_observability_events(fem_norm)
    fem_runtime_lineage_events = build_fem_runtime_lineage_events(fem_norm)

    sdt = importlib.import_module("game.stage_diff_telemetry")
    build_stage_diff_observability_events = getattr(sdt, "build_stage_diff_observability_events", lambda _: [])

    sd_in = stage_diff if isinstance(stage_diff, Mapping) else None
    sd_events = build_stage_diff_observability_events(sd_in)
    sd_surface = _curated_stage_diff_surface_for_bundle(sd_in)

    nae = importlib.import_module("game.narrative_authenticity_eval")
    build_evaluator_observability_events = getattr(nae, "build_evaluator_observability_events", lambda _: [])

    ev_in = evaluator_result if isinstance(evaluator_result, Mapping) else None
    ev_events = build_evaluator_observability_events(ev_in)

    return {
        "final_emission_meta": fem_norm,
        "fem_observability_events": fem_events,
        "fem_runtime_lineage_events": fem_runtime_lineage_events,
        "stage_diff_observability_events": sd_events,
        "evaluator_observability_events": ev_events,
        "stage_diff_surface": sd_surface,
    }


def normalized_observational_telemetry_bundle(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Produce a normalized, observational-only **payload slice** for evaluator/debug consumers.

    This is **not** :func:`assemble_unified_observational_telemetry_bundle` — it does not attach
    stage-diff or evaluator canonical event lists; it normalizes FEM reads from a turn/API
    envelope plus a few lane-level keys useful for proof tooling.

    Ownership boundaries:
    - **Write-time packaging** (what gets written into gm_output/internal_state) is owned by the gate.
    - **Read-time normalization** (stable empty subtrees + curated projections) is owned here.
    - This is explicitly **not** a policy/legality surface and must not be used to drive orchestration.
    """
    fem_raw = read_final_emission_meta_from_turn_payload(payload)
    fem = normalize_final_emission_meta_for_observability(fem_raw)
    lane = read_emission_debug_lane_from_turn_payload(payload)
    return {
        "final_emission_meta": fem,
        "dead_turn": dict(fem.get(FEM_DEAD_TURN_KEY) or _DEAD_TURN_READ_DEFAULTS),
        "debug_notes": read_debug_notes_from_turn_payload(payload),
        "stage_diff_na_projection": stage_diff_narrative_authenticity_projection(fem),
        # Keep the lane available for debugging, but never pass through arbitrary nested keys as canonical state.
        "emission_debug_lane_keys": sorted(str(k) for k in lane.keys()),
    }
