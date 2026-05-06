"""Prompt-context **renderer and packager** for model-facing narration payloads.

Canonical owner for prompt-context assembly.

**CTIR-first seam:** For resolved turns, session-backed CTIR (see :mod:`game.ctir_runtime`) is the canonical
resolved-turn *meaning* snapshot. This module resolves it once per ``build_narration_context`` call via
``get_attached_ctir(session)`` and maps it through :func:`_ctir_to_prompt_semantics` and related overlays.
When CTIR exists, downstream contract code **consumes** that meaning—it must not re-decide outcomes already
encoded in CTIR, and this module must **not** invoke CTIR construction from :mod:`game.ctir`. When CTIR is absent, caller
``resolution`` / ``intent`` supply legacy fallback shapes only for that path. Bounded reads of canonical engine
state are reserved for data CTIR intentionally does not own (see call-site comments, e.g. roster/name
resolution).

**Semantic planning is upstream (C1):** For normal CTIR-backed narration, the session-attached
**narration plan bundle** from :mod:`game.narration_plan_bundle` (matching :data:`game.ctir_runtime.SESSION_CTIR_STAMP_KEY`)
is the **required** handoff for narrative plan structure and plan-adjacent ``renderer_inputs`` (including
``turn_packet`` / ``referent_tracking`` when present on the bundle). This module formats, clips, and
projects those shipped artifacts; it does **not** compute a narrative plan locally for that path, and a
missing or stamp-mismatched bundle is a visible seam failure (see ``narration_seam_audit`` / bounded traces),
not a silent replan from raw state.

Builds the structured prompt-context payload from game state before narration prompt
construction. Prompt bundles are **read-side instruction carriers** assembled from authoritative inputs—they are not
canonical stores for ``world_state`` or ``hidden_state``.

It is **not** the canonical owner for extracted lead-only helpers
(:mod:`game.prompt_context_leads`) and **not** the post-prompt contract-resolution owner
for emitted-response policy accessors (:mod:`game.response_policy_contracts`).

Prompt contracts still show transitional residue across adjacent helpers, so future
cleanup should converge those helpers toward this boundary rather than re-creating
co-owners.

Contract layers (orthogonal concerns):
- **narration_visibility** — which entities and published facts may be referenced.
- **narrative_authority** — what outcome, hidden-truth, and NPC-intent claims may be stated as
  certain (see ``build_narrative_authority_contract``); does not replace visibility rules.
- **scene_state_anchor** — mandatory grounding in present scene/speaker/action anchors.
- **answer_completeness** — direct-answer obligations, voice, and bounded-partial shape. Final emission
  **validates** and records failure/skip metadata only; it does not compose missing answers at the boundary
  (bounded deterministic lines live upstream, e.g. :mod:`game.upstream_response_repairs`).
- **response_delta** — shipped **structure** for follow-up net-new value pressure (see
  ``build_response_delta_contract``). The gate records canonical ``response_delta_*`` legality metadata
  via :mod:`game.final_emission_repairs` **without** reorder or echo-rewrite repair at the boundary; prompt
  assembly **consumes** engine/session inputs to build the contract shape—it does not issue parallel
  legality verdicts for delta.
- **fallback_behavior** — narrow graceful-degradation policy under meaningful uncertainty pressure;
  governs bounded partials, diegetic hedging, and the single-question fallback shape.
- **tone_escalation** — caps interpersonal hostility / escalation in narration from published inputs
  (see ``build_tone_escalation_contract`` in ``game.tone_escalation``).
- **anti_railroading** — player-agency and lead-surfacing policy (inspectable flags and surfaced lead ids;
  see ``build_anti_railroading_contract`` in ``game.anti_railroading``); does not replace lead registry facts.
- **context_separation** — ambient world pressure vs. local interaction focus (see ``build_context_separation_contract``
  in ``game.context_separation``); enforcement reads the shipped contract, not prompt prose alone.
- **player_facing_narration_purity** — forbid planner/UI/engine scaffolding in narration (see
  ``build_player_facing_narration_purity_contract`` in ``game.player_facing_narration_purity``).
- **social_response_structure** — dialogue-turn spoken shape and anti-monologue caps. The
  canonical prompt-facing public home for this shipped bundle surface remains this module;
  downstream policy helpers live in ``game.response_policy_contracts``; strict-social terminal shaping
  lives in :mod:`game.social_exchange_emission`. Final emission validates and records metadata only.
- **narrative_authenticity** — anti-echo between narration and spoken lines, minimum new-signal pressure on
  follow-ups, anti-filler heuristics, and diegetic integrity hints (see ``build_narrative_authenticity_contract``
  in ``game.narrative_authenticity``); gate validation in ``game.final_emission_repairs`` (no boundary NA rewrite).
- **interaction_continuity** — preserve conversational thread / interlocutor continuity across turns;
  do not silently drop or switch speakers without a break signal or explicit cue (see
  ``build_interaction_continuity_contract`` in ``game.interaction_continuity``); gate/repairs TBD.
- **conversational_memory_window** — bounded prior-turn selection for prompts (see
  :mod:`game.conversational_memory_window`); ``recent_log`` in the payload is derived from the selector output.
- **narrative_plan** — deterministic structural bridge from CTIR to narration (see
  :func:`game.narrative_planning.build_narrative_plan`). Built only upstream at the :mod:`game.narration_plan_bundle`
  seam for CTIR-backed turns; this module **consumes** the bundled full plan internally but ships only
  :func:`game.narration_plan_bundle.public_narrative_plan_projection_for_prompt` on the public payload (no local replan).
  Objective N3 ``narrative_roles`` (five bounded composition families under ``narrative_plan.narrative_roles``) is a
  first-class **composition aid** in prompt assembly: emphasis bands, closed-set signals, and counts only—never a
  script, ordering mandate, or alternate authority. It is **not** consulted for adjudication, routing, policy, or
  ``turn_summary`` / resolution semantics—those remain CTIR-first (when attached), ``response_policy``, and
  ``narration_visibility``. If CTIR and the plan ever disagree, **CTIR wins**; the plan is derivative and owned
  upstream from CTIR plus the same bounded slices passed into the builder (including shipped ``narration_obligations``
  and ``response_policy`` for the mode contract). Optional one-step ``emphasis_band`` nudges for weak N3 families
  are applied only upstream in :mod:`game.narration_plan_bundle` via
  :func:`game.narrative_plan_upstream.apply_upstream_narrative_role_reemphasis` (trusted plans only); this module may
  surface a compact reminder line when that trace is present—never as semantic or CTIR override.
- **referent_tracking** — JSON-safe referent/clause artifact from :func:`game.referent_tracking.build_referent_tracking_artifact`
  only. Owned by :mod:`game.referent_tracking`; this module calls that constructor once per build with the same bounded
  inputs already present at the prompt seam (visibility contract, speaker selection, interaction continuity contract,
  session interaction slice, narrative plan, turn packet snapshot). It does **not** re-derive targets or pronouns locally.
  Kept separate from CTIR, ``response_policy``, slim ``narration_visibility`` export, social routing, and planning truth.
  **N5:** Optional ``clause_referent_plan`` on the shipped artifact is consumed only as **read-side**
  ``referent_clause_prompt_hints`` (trimmed projection). Does not construct rows or override CTIR;
  see ``docs/clause_level_referent_tracking.md``.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Mapping, Sequence, Set
import re

from game.leads import (
    effective_lead_pressure_score,
    filter_pending_leads_for_active_follow_surface,
    get_lead,
    is_lead_terminal,
    LeadLifecycle,
    LeadStatus,
    LeadType,
    list_session_leads,
)
from game.social import (
    _social_turn_counter,
    explicit_player_topic_anchor_state,
    list_recent_npc_lead_discussions,
)
from game.storage import get_scene_state
from game.world import get_world_npc_by_id
from game.interaction_context import build_speaker_selection_contract, response_type_context_snapshot
from game.narration_visibility import _normalize_visibility_text, build_narration_visibility_contract
from game.opening_visible_fact_selection import (
    OPENING_NARRATION_VISIBLE_FACT_MAX,
    select_opening_narration_visible_facts_with_telemetry,
)
from game.opening_scene_realization import (
    build_opening_scene_realization,
    merge_opening_instructions,
    opening_realization_none,
    patch_opening_export_with_plan_scene_opening,
)
from game.anti_railroading import build_anti_railroading_contract
from game.context_separation import build_context_separation_contract
from game.player_facing_narration_purity import build_player_facing_narration_purity_contract
from game.scene_state_anchoring import build_scene_state_anchor_contract
from game.narrative_authority import build_narrative_authority_contract
from game.fallback_behavior import build_fallback_behavior_contract
from game.tone_escalation import build_tone_escalation_contract
from game.response_type_gating import derive_response_type_contract
from game.interaction_continuity import build_interaction_continuity_contract
from game.conversational_memory_window import (
    _extract_explicit_reintroductions,
    build_conversational_memory_window_contract,
    select_conversational_memory_window,
)
from game.response_policy_contracts import (
    build_social_response_structure_contract as _build_social_response_structure_contract_impl,
    peek_response_type_contract_from_resolution as _peek_response_type_contract_from_resolution_impl,
    _resolve_response_type_contract as _resolve_authoritative_response_type_contract_impl,
)
from game.turn_packet import build_turn_packet
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, get_attached_ctir
from game.narrative_plan_upstream import (
    SESSION_NARRATION_RESUME_ENTRY_PENDING_KEY,
    interaction_context_snapshot_from_ctir_semantics,
    pending_lead_ids_from_active_pending,
    session_interaction_slice_for_narrative_plan,
)
from game.narration_plan_bundle import (
    get_attached_narration_plan_bundle,
    get_narration_plan_bundle_stamp,
    public_narrative_plan_projection_for_prompt,
)
from game.planner_convergence import MISSING_NARRATIVE_PLAN_FOR_CTIR_TURN, NARRATIVE_PLAN_STAMP_MISMATCH
from game.world_progression import (
    build_prompt_world_progression_hints,
    compose_ctir_world_progression_slice,
    merge_progression_changed_node_signals,
)
from game.narrative_mode_contract import NARRATIVE_MODES, validate_narrative_mode_contract
from game.narrative_planning import (
    NARRATIVE_ROLE_FAMILY_KEYS,
    validate_action_outcome_plan_contract,
    validate_narrative_plan,
)
from game.referent_tracking import build_referent_tracking_artifact
from game.state_channels import (
    assert_no_debug_keys_in_prompt_payload,
    project_public_payload,
)
from game.planner_ctir_projection import (
    ANSWER_COMPLETENESS_PARTIAL_REASONS,
    CONCRETE_PAYLOAD_KINDS,
    EXPECTED_ANSWER_SHAPE,
    EXPECTED_ANSWER_VOICE,
    NPC_REPLY_KIND_VALUES,
    NO_VALIDATOR_VOICE_PROHIBITIONS,
    NO_VALIDATOR_VOICE_RULE,
    RESPONSE_RULE_PRIORITY,
    RULE_PRIORITY_COMPACT_INSTRUCTION,
    SOCIAL_REPLY_KINDS,
    UNCERTAINTY_ANSWER_SHAPE,
    UNCERTAINTY_CATEGORIES,
    UNCERTAINTY_SOURCES,
    _CLASSIFIER_ONLY_INTENT_KEYS,
    _answer_pressure_followup_details,
    _compute_follow_up_pressure,
    _compress_recent_log,
    _compress_scene_runtime,
    _compress_session,
    _ctir_to_prompt_semantics,
    _extract_npc_introduced_anchor_tokens,
    _session_view_overlay_from_ctir_interaction,
    _synthetic_follow_up_pressure_from_log,
    _world_progression_projection_for_prompt,
    build_active_interlocutor_export,
    build_answer_completeness_contract,
    build_response_delta_contract,
    build_response_policy,
    build_social_interlocutor_profile,
    canonical_interaction_target_npc_id,
    derive_narration_obligations,
    deterministic_interlocutor_answer_style_hints,
    question_detected_from_player_text,
)
from game.planner_head_state import build_planner_head_state

_build_narration_context_head_state = build_planner_head_state

# Configurable limits for deterministic, inspectable compression
MAX_RECENT_LOG = 5
MAX_RECENT_EVENTS = 5
MAX_GM_GUIDANCE = 3
MAX_WORLD_PRESSURES = 3
MAX_LOG_ENTRY_SNIPPET = 200
MAX_FOLLOW_UP_TOPIC_TOKENS = 6
MAX_RECENT_CONTEXTUAL_LEADS = 4
CONVERSATIONAL_MEMORY_SOFT_LIMIT = 12
CONVERSATIONAL_MEMORY_MAX_CANDIDATES = 36
_CONV_MEM_TITLE_TOPIC_RE = re.compile(r"[a-z]{4,}", re.IGNORECASE)


def _narrative_plan_prompt_debug_anchor(
    plan: Mapping[str, Any] | None,
    *,
    build_error: str | None = None,
) -> Dict[str, Any]:
    """Compact inspect-only mirror for ``prompt_debug`` (not authoritative; no plan blob duplication)."""
    if build_error:
        return {"present": False, "build_error": build_error[:500]}
    if not isinstance(plan, Mapping) or not plan:
        return {"present": False}
    dbg = plan.get("debug") if isinstance(plan.get("debug"), dict) else {}
    dc = dbg.get("derivation_codes")
    codes = [str(c) for c in (dc if isinstance(dc, list) else [])][:24]
    sa = plan.get("scene_anchors") if isinstance(plan.get("scene_anchors"), dict) else {}
    ap = plan.get("active_pressures") if isinstance(plan.get("active_pressures"), dict) else {}
    rni = plan.get("required_new_information") if isinstance(plan.get("required_new_information"), list) else []
    aer = plan.get("allowable_entity_references") if isinstance(plan.get("allowable_entity_references"), list) else []
    ra = sa.get("relevant_actors") if isinstance(sa.get("relevant_actors"), list) else []
    pl = ap.get("pending_lead_ids") if isinstance(ap.get("pending_lead_ids"), list) else []
    nmc = plan.get("narrative_mode_contract") if isinstance(plan.get("narrative_mode_contract"), dict) else None
    nmc_ok, nmc_reasons = validate_narrative_mode_contract(nmc)
    nmc_dbg: List[str] = []
    if isinstance(nmc, dict):
        _nmc_dbg = (nmc.get("debug") or {}).get("derivation_codes") if isinstance(nmc.get("debug"), dict) else None
        if isinstance(_nmc_dbg, list):
            nmc_dbg = [str(x) for x in _nmc_dbg[:16]]
    plan_nm = str(plan.get("narrative_mode") or "").strip() if isinstance(plan.get("narrative_mode"), str) else ""
    nmc_mode = str(nmc.get("mode") or "").strip() if isinstance(nmc, dict) else ""
    nmc_enabled = bool(nmc.get("enabled")) if isinstance(nmc, dict) and isinstance(nmc.get("enabled"), bool) else None
    plan_alias_match: bool | None = None
    if nmc_ok and isinstance(nmc, dict):
        plan_alias_match = plan_nm == nmc_mode
    _po = (nmc.get("prompt_obligations") if isinstance(nmc, dict) and isinstance(nmc.get("prompt_obligations"), dict) else {}) or {}
    _fm = nmc.get("forbidden_moves") if isinstance(nmc, dict) else None
    _fm_l = _fm if isinstance(_fm, list) else []
    nmc_ship_trace = None
    if isinstance(nmc, dict):
        nmc_ship_trace = {
            "mode": nmc_mode or None,
            "enabled": nmc_enabled,
            "contract_valid": bool(nmc_ok),
            "ob_keys_head": sorted(str(k) for k in _po.keys() if isinstance(k, str) and str(k).strip())[:6],
            "fm_head": sorted(
                {str(x).strip() for x in _fm_l if isinstance(x, str) and str(x).strip()}
            )[:6],
        }
    plan_validate_err = validate_narrative_plan(plan, strict=False) if isinstance(plan, Mapping) else "not_mapping"
    narrative_roles_skim = _narrative_roles_prompt_debug_skim(
        plan,
        plan_validation_error=plan_validate_err if isinstance(plan_validate_err, str) else None,
    )
    return {
        "present": True,
        "version": plan.get("version"),
        "narrative_mode": plan.get("narrative_mode"),
        "narrative_mode_contract_valid": bool(nmc_ok),
        "narrative_mode_contract_enabled": nmc_enabled,
        "narrative_mode_contract_validation_codes": list(nmc_reasons[:16]) if not nmc_ok else [],
        "narrative_mode_contract_derivation_codes": nmc_dbg,
        "narrative_plan_mode_alias_matches_contract_mode": plan_alias_match,
        "nmc_ship_trace": nmc_ship_trace,
        "role_allocation": plan.get("role_allocation") if isinstance(plan.get("role_allocation"), dict) else None,
        "derivation_codes": codes,
        "derivation_code_count": len(dc) if isinstance(dc, list) else 0,
        "counts": {
            "required_new_information": len(rni),
            "allowable_entity_references": len(aer),
            "relevant_actors": len(ra),
            "pending_lead_ids": len(pl),
        },
        "narrative_roles_skim": narrative_roles_skim,
        "narrative_plan_validation_error": (
            str(plan_validate_err)[:400] if isinstance(plan_validate_err, str) else plan_validate_err
        ),
    }


def _narrative_plan_roles_trustworthy(plan: Mapping[str, Any] | None) -> bool:
    """True when the full plan passes relaxed validation (harness-safe; no invented role repair)."""
    if not isinstance(plan, Mapping) or not plan:
        return False
    return validate_narrative_plan(plan, strict=False) is None


def _planner_convergence_consumer_debug_slice(
    *,
    ctir_present: bool,
    bundle_present: bool,
    stamp_matches: bool,
    narrative_plan_full: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Observability only (``prompt_debug`` lane): CTIR/bundle/stamp/plan validation for operators."""
    pve: str | None = None
    if isinstance(narrative_plan_full, Mapping) and narrative_plan_full:
        raw = validate_narrative_plan(narrative_plan_full, strict=False)
        pve = str(raw) if isinstance(raw, str) else None
    seam_codes: list[str] = []
    if ctir_present:
        if not bundle_present:
            seam_codes.append(MISSING_NARRATIVE_PLAN_FOR_CTIR_TURN)
        elif not stamp_matches:
            seam_codes.append(NARRATIVE_PLAN_STAMP_MISMATCH)
        elif not (isinstance(narrative_plan_full, Mapping) and narrative_plan_full):
            seam_codes.append(MISSING_NARRATIVE_PLAN_FOR_CTIR_TURN)
    return {
        "ctir_present": ctir_present,
        "bundle_present": bundle_present,
        "stamp_matches": stamp_matches,
        "plan_validation_error": pve,
        "seam_failure_codes": sorted(set(seam_codes)),
    }


def _narrative_roles_collapse_observability(
    nr: Mapping[str, Any],
    *,
    upstream_trace: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Inspect-only contrast snapshot for operators (not legality, scoring, or repair input).

    Fields are counts and a symbolic ``anchor_hint`` only:
    ``sig_families_n`` — role families with at least one non-empty signal string;
    ``low_band_n`` — families at ``minimal`` or ``low`` emphasis;
    ``reinforced_n`` — families listed in an applied upstream bump trace;
    ``max_band`` — coarsest emphasis tier seen across families;
    ``anchor_hint`` — ``high_band_vs_sparse_peers``, ``low_signal_coverage``, or ``none``.
    """
    low_min_bands = frozenset({"minimal", "low"})
    families_with_signals = 0
    low_or_minimal_n = 0
    band_max = "minimal"
    order = ("minimal", "low", "moderate", "elevated", "high")
    for rk in NARRATIVE_ROLE_FAMILY_KEYS:
        sub = nr.get(rk)
        if not isinstance(sub, Mapping):
            continue
        band = str(sub.get("emphasis_band") or "").strip() or "minimal"
        if band in low_min_bands:
            low_or_minimal_n += 1
        if band in order and order.index(band) > order.index(band_max):
            band_max = band
        sigs = sub.get("signals") if isinstance(sub.get("signals"), list) else []
        if any(isinstance(x, str) and str(x).strip() for x in sigs):
            families_with_signals += 1
    reinforced_n = 0
    if isinstance(upstream_trace, dict) and bool(upstream_trace.get("applied")):
        rf = upstream_trace.get("reinforced_families")
        if isinstance(rf, list):
            reinforced_n = len({str(x).strip() for x in rf if isinstance(x, str) and str(x).strip()})
    anchor_hint = "none"
    if band_max == "high" and low_or_minimal_n >= 3:
        anchor_hint = "high_band_vs_sparse_peers"
    elif families_with_signals <= 2 and low_or_minimal_n >= 3:
        anchor_hint = "low_signal_coverage"
    return {
        "sig_families_n": families_with_signals,
        "low_band_n": low_or_minimal_n,
        "reinforced_n": reinforced_n,
        "max_band": band_max if band_max in order else None,
        "anchor_hint": anchor_hint,
    }


def _narrative_roles_prompt_debug_skim(
    plan: Mapping[str, Any],
    *,
    plan_validation_error: str | None,
) -> Dict[str, Any]:
    """One-screen N3 glance: per-family band, signal count, short heads; upstream trace + collapse hint.

    Does not duplicate the full ``narrative_roles`` object; safe for ``prompt_debug`` only.
    """
    nr = plan.get("narrative_roles")
    if not isinstance(nr, Mapping):
        return {
            "present": False,
            "roles_struct_ok": False,
            "plan_validation_error_head": (plan_validation_error or "")[:180] or None,
        }
    roles_out: Dict[str, Any] = {}
    for rk in NARRATIVE_ROLE_FAMILY_KEYS:
        sub = nr.get(rk)
        if not isinstance(sub, Mapping):
            continue
        band = sub.get("emphasis_band")
        sigs = sub.get("signals") if isinstance(sub.get("signals"), list) else []
        sig_list = [str(x) for x in sigs if isinstance(x, str)]
        row: Dict[str, Any] = {
            "emphasis_band": band if isinstance(band, str) else None,
            "signal_n": len(sig_list),
            "signals_head": sig_list[:4],
        }
        if rk == "hook":
            tags = sub.get("information_kind_tags")
            if isinstance(tags, list):
                row["information_kind_tags_head"] = [str(x) for x in tags[:4] if isinstance(x, str)]
        if rk == "pressure":
            ip = sub.get("interaction_pressure")
            if isinstance(ip, str) and ip.strip():
                row["interaction_pressure"] = ip.strip()
        if rk == "consequence":
            oft = sub.get("outcome_forward_tier")
            if isinstance(oft, str) and oft.strip():
                row["outcome_forward_tier"] = oft.strip()
        roles_out[rk] = row
    struct_ok = plan_validation_error is None
    pl_debug = plan.get("debug") if isinstance(plan.get("debug"), dict) else {}
    raw_ur = pl_debug.get("n3_upstream_role_reemphasis")
    upstream_ur: dict[str, Any] | None = None
    if isinstance(raw_ur, dict):
        applied = bool(raw_ur.get("applied"))
        upstream_ur = {
            "applied": applied,
            "skip_reason": (str(raw_ur.get("skip_reason") or "").strip()[:48] or None) if not applied else None,
            "reinforced_families": sorted({str(x) for x in (raw_ur.get("reinforced_families") or []) if str(x).strip()})[
                :4
            ]
            if applied and isinstance(raw_ur.get("reinforced_families"), list)
            else None,
        }
    collapse_obs = _narrative_roles_collapse_observability(nr, upstream_trace=upstream_ur)
    return {
        "present": True,
        "roles_struct_ok": struct_ok,
        "families_shipped": sorted(roles_out.keys()),
        "roles": roles_out,
        "plan_validation_error_head": (plan_validation_error or "")[:180] or None,
        # Subset of plan.debug.n3_upstream_role_reemphasis for one-screen inspection.
        "upstream_role_reemphasis": upstream_ur,
        "collapse_observability": collapse_obs,
    }


_MAX_NARRATIVE_MODE_INSTRUCTIONS = 22
_MAX_NARRATIVE_MODE_CONTRACT_CODE_EMBED = 8


def _narrative_mode_instruction_prompt_debug(
    narrative_mode_contract: Mapping[str, Any] | None,
    *,
    instruction_lines: Sequence[str],
    narrative_plan_present: bool = False,
    plan_narrative_mode: str | None = None,
) -> Dict[str, Any]:
    """Compact inspect-only slice for ``prompt_debug`` (counts + symbolic codes only)."""
    lines = list(instruction_lines)
    if not isinstance(narrative_mode_contract, Mapping):
        return {
            "present": bool(lines),
            "mode": None,
            "contract_valid": False,
            "contract_enabled": None,
            "instruction_count": len(lines),
            "sample_prompt_obligation_keys": [],
            "sample_forbidden_moves": [],
            "plan_narrative_mode_field": (str(plan_narrative_mode).strip() or None) if plan_narrative_mode else None,
            "narrative_plan_present": bool(narrative_plan_present),
            "seam_codes": (["nmc_missing_contract"] if narrative_plan_present else []),
        }
    mode = str(narrative_mode_contract.get("mode") or "").strip() or None
    nmc_ok, nmc_reasons = validate_narrative_mode_contract(narrative_mode_contract)
    nmc_en = narrative_mode_contract.get("enabled")
    contract_enabled = bool(nmc_en) if isinstance(nmc_en, bool) else None
    po = (
        narrative_mode_contract.get("prompt_obligations")
        if isinstance(narrative_mode_contract.get("prompt_obligations"), Mapping)
        else {}
    )
    fm = narrative_mode_contract.get("forbidden_moves")
    fm_list = [str(x).strip() for x in (fm if isinstance(fm, list) else []) if isinstance(x, str) and str(x).strip()]
    ob_keys = sorted(str(k) for k in po.keys() if isinstance(k, str) and str(k).strip())[:8]
    pn = str(plan_narrative_mode or "").strip() or None
    drift = bool(pn and mode and pn != mode)
    seam_codes: List[str] = []
    if narrative_plan_present and not nmc_ok:
        seam_codes.append("nmc_contract_invalid|" + "|".join(str(x) for x in (nmc_reasons or [])[:8]))
    if narrative_plan_present and nmc_ok and drift:
        seam_codes.append(f"nmc_plan_field_drift|plan={pn}|contract={mode}")
    return {
        "present": bool(lines),
        "mode": mode,
        "contract_valid": bool(nmc_ok),
        "contract_enabled": contract_enabled,
        "instruction_count": len(lines),
        "sample_prompt_obligation_keys": ob_keys,
        "sample_forbidden_moves": sorted(set(fm_list))[:8],
        "plan_narrative_mode_field": pn,
        "narrative_plan_present": bool(narrative_plan_present),
        "seam_codes": seam_codes,
    }


def _nmc_continuation_delta_lines() -> List[str]:
    """Machine continuation lane (canonical default when no special mode applies)."""
    return [
        "struct:continuation:carry_active_thread_forward_without_reopening_a_fresh_intro_tableau",
        "struct:continuation:prefer_local_continuity_and_forward_motion_over_scene_wide_recap",
        "struct:continuation:suppress_language_that_resets_the_scene_like_a_first_shot_opening",
    ]


def _nmc_seam_floor_when_contract_unusable(*, reasons: Sequence[str] | None = None, missing: bool = False) -> List[str]:
    """Explicit continuation floor — not a mode-agnostic narration escape hatch."""
    head = (
        "struct:nmc_seam:narrative_mode_contract_missing"
        if missing
        else "struct:nmc_seam:narrative_mode_contract_invalid|" + "|".join(str(x) for x in (reasons or [])[:8])
    )
    out = [head, "struct:nmc_floor:use_continuation_lane_pending_gate_skip_on_c4"]
    out.extend(_nmc_continuation_delta_lines())
    return out[:_MAX_NARRATIVE_MODE_INSTRUCTIONS]


def _build_narrative_mode_instructions(
    *,
    narrative_mode_contract: Mapping[str, Any] | None,
    response_policy: Mapping[str, Any] | None,
    narration_obligations: Mapping[str, Any] | None,
    resolution_sem: Mapping[str, Any] | None,
    narrative_plan_present: bool = False,
    plan_narrative_mode: str | None = None,
) -> List[str]:
    """Bounded structural mode instructions derived from ``narrative_mode_contract`` only.

    Uses ``mode``, ``prompt_obligations``, and ``forbidden_moves`` from the integrated
    contract; does not infer a separate mode. Call after shipped slices (including
    ``response_policy.social_response_structure``) are attached when dialogue shaping
    must reflect that contract.

    ``narration_obligations`` / ``resolution_sem`` are accepted for seam symmetry with
    planning inputs; the integrated contract remains authoritative over local re-derivation.

    When ``narrative_plan_present`` is true (payload carries ``narrative_plan``), a missing
    or invalid contract is surfaced with compact ``struct:nmc_seam:*`` markers plus an
    explicit continuation floor — never an empty mode-guidance block.
    """
    _ = (narration_obligations, resolution_sem)
    if not isinstance(narrative_mode_contract, Mapping):
        if narrative_plan_present:
            return _nmc_seam_floor_when_contract_unusable(reasons=None, missing=True)
        return []
    ok, reasons = validate_narrative_mode_contract(narrative_mode_contract)
    if not ok:
        if narrative_plan_present:
            return _nmc_seam_floor_when_contract_unusable(reasons=list(reasons or []), missing=False)
        return []
    mode = str(narrative_mode_contract.get("mode") or "").strip()
    if mode not in NARRATIVE_MODES:
        if narrative_plan_present:
            return _nmc_seam_floor_when_contract_unusable(
                reasons=[f"narrative_mode_contract:unknown_mode:{mode}"], missing=False
            )
        return []
    po = (
        narrative_mode_contract.get("prompt_obligations")
        if isinstance(narrative_mode_contract.get("prompt_obligations"), Mapping)
        else {}
    )
    fm = narrative_mode_contract.get("forbidden_moves")
    fm_list = sorted(
        {
            str(x).strip()
            for x in (fm if isinstance(fm, list) else [])
            if isinstance(x, str) and str(x).strip()
        }
    )[:_MAX_NARRATIVE_MODE_CONTRACT_CODE_EMBED]

    rp = response_policy if isinstance(response_policy, Mapping) else {}
    ac = rp.get("answer_completeness") if isinstance(rp.get("answer_completeness"), Mapping) else {}
    srs = rp.get("social_response_structure") if isinstance(rp.get("social_response_structure"), Mapping) else {}

    out: List[str] = [
        "NARRATIVE MODE (STRUCTURAL DELTA): Canonical mode is `narrative_plan.narrative_mode_contract.mode` "
        f"({mode}); obey its prompt_obligations and forbidden_moves as machine codes. "
        "Shipped response_policy and CTIR win on any conflict.",
    ]
    seam_preface: List[str] = []
    if narrative_plan_present and narrative_mode_contract.get("enabled") is False:
        seam_preface.append("struct:nmc_contract:disabled|c4_gate_skips_nmo|shipped_continuation_lane")
    pn_field = str(plan_narrative_mode or "").strip()
    if narrative_plan_present and pn_field and pn_field != mode:
        seam_preface.append(f"struct:nmc_seam:plan_narrative_mode_field_drift|plan={pn_field}|contract={mode}")
    for i, line in enumerate(seam_preface):
        out.insert(1 + i, line)

    if mode == "opening":
        out.append("struct:opening:first_impression_and_immediate_location_salience")
        out.append(
            "struct:opening:distinct_from_continuation_establish_now_do_not_continue_mid_thread_tableau_as_a_fresh_opening"
        )
        if bool(ac.get("answer_required")):
            out.append(
                "struct:opening:answer_completeness_if_active_keep_the_core_reply_unburied_by_scene_paint"
            )
    elif mode == "continuation":
        out.extend(_nmc_continuation_delta_lines())
    elif mode == "action_outcome":
        out.append(
            "struct:action_outcome:lead_early_with_the_authoritative_result_signal_before_atmosphere_or_scene_setting_padding"
        )
        out.append("struct:action_outcome:foreground_state_change_salience")
        out.append(
            "struct:action_outcome:do_not_treat_unresolved_engine_check_prompts_as_if_the_outcome_already_landed"
        )
    elif mode == "dialogue":
        out.append("struct:dialogue:preserve_active_interlocutor_and_speaker_continuity")
        out.append("struct:dialogue:suppress_scenic_recap_unless_scene_change_signals_apply_this_turn")
        if bool(srs.get("enabled")):
            out.append(
                "struct:dialogue:social_response_structure_enabled_obey_shipped_response_policy_object_shape_only"
            )
    elif mode == "transition":
        out.append("struct:transition:foreground_departure_arrival_or_other_scene_change_motion")
        out.append("struct:transition:require_motion_or_spatial_change_signal_not_static_scene_hold")
        out.append(
            "struct:transition:allowed_reground_in_new_setting_distinct_from_static_mid_scene_continuation"
        )
    elif mode == "exposition_answer":
        out.append("struct:exposition_answer:lead_with_clear_information_when_answer_completeness_requires_it")
        out.append("struct:exposition_answer:prioritize_direct_information_delivery_over_mood_setting")
        out.append(
            "struct:exposition_answer:avoid_implying_a_mechanical_action_resolution_beat_if_none_occurred"
        )

    ob_lines: List[str] = []
    for k in sorted(str(x) for x in po.keys() if isinstance(x, str) and str(x).strip()):
        v = po.get(k)
        if v is True:
            ob_lines.append(f"struct:contract_obligation:{k}")
        elif isinstance(v, list) and v:
            items = sorted({str(x).strip() for x in v if isinstance(x, str) and str(x).strip()})[:4]
            if items:
                ob_lines.append(f"struct:contract_obligation:{k}:{'|'.join(items)}")
    out.extend(ob_lines[:6])

    if fm_list:
        out.append("struct:contract_forbidden_moves:" + "|".join(fm_list))

    return out[:_MAX_NARRATIVE_MODE_INSTRUCTIONS]


_NARRATIVE_PLAN_STRUCT_GUIDANCE: tuple[str, ...] = (
    "NARRATIVE PLAN (STRUCTURAL GUIDANCE): When top-level `narrative_plan` is present, prefer it for bounded structural "
    "shaping alongside existing contracts. It does not replace CTIR, response_policy, or narration_visibility; "
    "on any conflict, follow CTIR and the shipped contracts, not the plan.",
    "Narrative mode contract: `narrative_plan.narrative_mode_contract` is a deterministic, JSON-safe derivative of CTIR plus "
    "the same-turn shipped slices already used at this seam (`response_policy`, `narration_obligations`, optional `turn_packet`). "
    "It is downstream shaping guidance only—not adjudication and not a second authority over CTIR or policy.",
    "Anchoring: prefer `narrative_plan.scene_anchors` for scene/interlocutor grounding tokens together with "
    "`scene_state_anchor_contract` and narration visibility—do not contradict authoritative visibility.",
    "Momentum / pressure: prefer `narrative_plan.active_pressures` (pending lead ids, interaction_pressure, "
    "scene_tension_codes, world/clock summaries) together with `narration_obligations.scene_momentum_due` and registry slices.",
    "Must-carry novelty: surface categories listed in `narrative_plan.required_new_information` when they apply to this "
    "turn—without inventing facts beyond visibility and narrative authority.",
    "Entity handle boundaries: `narrative_plan.allowable_entity_references` is the visible narration-universe (outer boundary) "
    "for published entity_id handles when non-empty—not whom to focus on. Use `scene_anchors.active_interlocutor`, "
    "`scene_anchors` generally, `narrative_plan.narrative_mode`, `narrative_plan.narrative_mode_contract`, `active_pressures`, "
    "`required_new_information`, and `role_allocation` for narrower focality. narration_visibility remains the hard visibility scope—never reference entities outside both contracts.",
    "Scene opening (C1-A): when `narrative_plan.scene_opening` is present, treat it as the sole structural opener contract "
    "(anchors, closed-set opening_reason, visible_fact anchor ids/categories, prohibited_content_codes)—prose-free; pair with "
    "narration_visibility.visible_facts for observable lines. It does not replace CTIR or visibility.",
    "Narrative roles composition (N3): read `narrative_plan.narrative_roles` as five parallel composition hints—each carries "
    "`emphasis_band` plus closed-set `signals` (and small bounded counters/tags)—not prose beats. "
    "`location_anchor` biases physical/scene grounding; `actor_anchor` biases materially relevant actor presence; "
    "`pressure` biases current tension or unresolved obligation salience; `hook` biases clue/lead/opening or actionable salience "
    "aligned with `required_new_information` kind tags; `consequence` biases closing salience toward outcomes, state-forward edges, "
    "or transition-relevant information. These facets are optional salience dials: weave them where natural; no prescribed ordering, "
    "no beat checklist, no requirement to dedicate a paragraph or sentence slot to each family.",
    "N3 precedence: `narrative_roles` stays strictly subordinate to narration_visibility, narrative_authority (response_policy), "
    "the `NARRATIVE MODE (STRUCTURAL DELTA)` lines from `narrative_mode_contract`, answer_completeness, response_delta, "
    "social_response_structure / response_type_contract, interaction continuity, and every other shipped policy object—never override them.",
    "Mode deltas: follow the `NARRATIVE MODE (STRUCTURAL DELTA)` instruction lines derived from "
    "`narrative_plan.narrative_mode_contract` (machine prompt_obligations + forbidden_moves). "
    "Use `narrative_plan.role_allocation` integer weights only as bounded emphasis alongside that block—never as a substitute for shipped policy.",
)


def _narrative_plan_roles_trusted_lane() -> tuple[str, ...]:
    """Extra instruction only when the bundled plan validates (strict=False)—no synthetic repair of partial dicts."""
    return (
        "NARRATIVE ROLES (N3 supplemental): `narrative_plan.narrative_roles` on this payload passed structural validation as "
        "planning-only bounded data. Treat each family's `emphasis_band` and `signals` as optional shaping pressure together "
        "with `role_allocation`—not as mandatory beats, ordering rules, or replacements for CTIR or machine contracts.",
    )


def _narrative_plan_upstream_role_repair_instruction(plan: Mapping[str, Any] | None) -> tuple[str, ...]:
    """Single instruction line when the bundle applied capped upstream ``emphasis_band`` bumps (N3)."""
    if not isinstance(plan, Mapping):
        return ()
    dbg = plan.get("debug") if isinstance(plan.get("debug"), dict) else {}
    ur = dbg.get("n3_upstream_role_reemphasis")
    if not isinstance(ur, dict) or not ur.get("applied"):
        return ()
    fams = ur.get("reinforced_families")
    if not isinstance(fams, list) or not fams:
        return ()
    joined = ", ".join(sorted({str(x) for x in fams if str(x).strip()})[:5])
    return (
        "N3 bundle upstream: optional `emphasis_band` one-step bump for "
        f"{joined} (validated plan metadata only). CTIR, narration visibility, and shipped contracts still win on conflict; "
        "no new facts or policy.",
    )



NARRATION_VISIBILITY_MANDATORY_INSTRUCTIONS: tuple[str, ...] = (
    "VISIBILITY CONTRACT (MANDATORY): Use narration_visibility as the hard scope for entity references and factual assertions.",
    "You MUST NOT reference entities outside narration_visibility.visible_entities.",
    "You MUST NOT assert facts outside narration_visibility.visible_facts; only visible facts may be directly asserted.",
    "You MUST NOT reveal hidden or undiscovered facts.",
    "Discoverable facts may be hinted at (discoverable_hinting is true), but not asserted as confirmed truth.",
    "If uncertain whether something is visible or known, omit or reframe it.",
    "Only visible or addressable entities may act or speak.",
)

FIRST_MENTION_MANDATORY_INSTRUCTIONS: tuple[str, ...] = (
    "FIRST-MENTION CONTRACT (MANDATORY): Visibility scope controls who/what may be referenced; first-mention contract controls how first references are phrased.",
    "The first reference to any entity MUST be explicit.",
    "A first reference MUST use a visible name or a visible descriptor.",
    "A first reference MUST include grounding by location, behavior, or relation.",
    "Pronouns MAY be used only after explicit introduction.",
    "You MUST NOT use unearned familiarity phrases (for example, 'you recognize ...', 'you remember ...', 'you know this is ...') unless supported by narration_visibility.visible_facts.",
)

SCENE_STATE_ANCHOR_MANDATORY_INSTRUCTIONS: tuple[str, ...] = (
    "SCENE STATE ANCHOR (MANDATORY): Every response must visibly ground itself in the present scene through at least one of: "
    "current location, a current actor or speaker allowed by authoritative state (see scene_state_anchor_contract), "
    "or the player's immediate action (turn_summary + mechanical_resolution).",
    "Avoid floating, abstract, or scene-detached narration.",
)



def peek_response_type_contract_from_resolution(resolution: Any) -> Dict[str, Any] | None:
    """Canonical prompt-facing accessor for response-type contract peeking.

    ``game.prompt_context`` is the canonical prompt-contract owner and public bundle
    home. The implementation remains delegated to the downstream policy consumer
    module as compatibility residue; do not add prompt-contract semantics there.
    """
    return _peek_response_type_contract_from_resolution_impl(resolution)


def build_social_response_structure_contract(
    response_type_contract: Mapping[str, Any] | None = None,
    *,
    debug_inputs: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Canonical prompt-facing home for shipped ``social_response_structure``.

    Prompt-contract bundling belongs here. The implementation currently lives in
    the downstream policy consumer module as compatibility residue so existing
    imports continue to work without changing runtime behavior.
    """
    return _build_social_response_structure_contract_impl(
        response_type_contract,
        debug_inputs=debug_inputs,
    )


def _tone_escalation_prompt_debug_anchor(contract: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Compact mirror of tone_escalation contract for prompt_debug (inspectable, not authoritative)."""
    c = contract if isinstance(contract, dict) else {}
    reasons = c.get("justification_reasons")
    if not isinstance(reasons, list):
        reasons = []
    return {
        "enabled": c.get("enabled"),
        "active_speaker_id": c.get("active_speaker_id"),
        "base_tone": c.get("base_tone"),
        "max_allowed_tone": c.get("max_allowed_tone"),
        "allow_guarded_refusal": c.get("allow_guarded_refusal"),
        "allow_verbal_pressure": c.get("allow_verbal_pressure"),
        "allow_explicit_threat": c.get("allow_explicit_threat"),
        "allow_physical_hostility": c.get("allow_physical_hostility"),
        "allow_combat_initiation": c.get("allow_combat_initiation"),
        "justification_reasons": [str(x) for x in reasons if isinstance(x, str)],
    }


def _context_separation_prompt_debug_anchor(contract: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Compact mirror of context_separation contract for prompt_debug (inspectable, not authoritative)."""
    c = contract if isinstance(contract, dict) else {}
    df = c.get("debug_flags")
    if not isinstance(df, dict):
        df = {}
    pt = c.get("primary_topics")
    if not isinstance(pt, tuple):
        pt = ()
    return {
        "enabled": c.get("enabled"),
        "interaction_kind": c.get("interaction_kind"),
        "pressure_focus_allowed": df.get("pressure_focus_allowed"),
        "player_seeks_world_danger_info": df.get("player_seeks_world_danger_info"),
        "scene_summary_crisis": df.get("scene_summary_crisis"),
        "interaction_kind_worldish": df.get("interaction_kind_worldish"),
        "authoritative_or_consequence_relevant": df.get("authoritative_or_consequence_relevant"),
        "primary_topic_count": len(pt),
        "ambient_pressure_topic_count": len(c.get("ambient_pressure_topics") or ()),
    }


def _player_facing_narration_purity_prompt_debug_anchor(contract: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Compact mirror of player_facing_narration_purity contract for prompt_debug (inspectable, not authoritative)."""
    c = contract if isinstance(contract, dict) else {}
    return {
        "enabled": c.get("enabled"),
        "diegetic_only": c.get("diegetic_only"),
        "interaction_kind": c.get("interaction_kind"),
        "forbid_scaffold_headers": c.get("forbid_scaffold_headers"),
        "forbid_coaching_language": c.get("forbid_coaching_language"),
        "forbid_engine_choice_framing": c.get("forbid_engine_choice_framing"),
        "forbid_non_diegetic_action_prompting": c.get("forbid_non_diegetic_action_prompting"),
    }


def _social_response_structure_prompt_debug_anchor(contract: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Compact mirror of social_response_structure contract for prompt_debug (inspectable, not authoritative)."""
    c = contract if isinstance(contract, dict) else {}
    return {
        "enabled": c.get("enabled"),
        "applies_to_response_type": c.get("applies_to_response_type"),
        "require_spoken_dialogue_shape": c.get("require_spoken_dialogue_shape"),
        "max_contiguous_expository_lines": c.get("max_contiguous_expository_lines"),
        "max_dialogue_paragraphs_before_break": c.get("max_dialogue_paragraphs_before_break"),
        "prefer_single_speaker_turn": c.get("prefer_single_speaker_turn"),
        "forbid_bulleted_or_list_like_dialogue": c.get("forbid_bulleted_or_list_like_dialogue"),
    }


def _narrative_authenticity_prompt_debug_anchor(contract: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Compact mirror of narrative_authenticity for prompt_debug (inspectable, not authoritative)."""
    c = contract if isinstance(contract, dict) else {}
    tr = c.get("trace") if isinstance(c.get("trace"), Mapping) else {}
    rr = c.get("rumor_realism") if isinstance(c.get("rumor_realism"), Mapping) else {}
    return {
        "enabled": c.get("enabled"),
        "version": c.get("version"),
        "mode": c.get("mode"),
        "response_delta_contract_active": tr.get("response_delta_contract_active"),
        "topic_follow_up_active": tr.get("topic_follow_up_active"),
        "dialogue_shape_expected": tr.get("dialogue_shape_expected"),
        "rumor_realism_enabled": rr.get("enabled"),
        "rumor_turn_active": tr.get("rumor_turn_active"),
        "rumor_trigger_spans": list(tr.get("rumor_trigger_spans") or [])[:6],
    }


def _interaction_continuity_prompt_debug_anchor(contract: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Compact mirror of interaction_continuity contract for prompt_debug (inspectable, not authoritative)."""
    c = contract if isinstance(contract, dict) else {}
    dbg = c.get("debug") if isinstance(c.get("debug"), dict) else {}
    return {
        "enabled": c.get("enabled"),
        "continuity_strength": c.get("continuity_strength"),
        "anchored_interlocutor_id": c.get("anchored_interlocutor_id"),
        "drop_interlocutor_requires_explicit_break": c.get("drop_interlocutor_requires_explicit_break"),
        "speaker_switch_requires_explicit_cue": c.get("speaker_switch_requires_explicit_cue"),
        "source_of_anchor": dbg.get("source_of_anchor"),
        "scene_scope_validated": dbg.get("scene_scope_validated"),
    }




def _compress_campaign(campaign: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize campaign to essential narration context. No hidden/secret fields."""
    if not campaign or not isinstance(campaign, dict):
        return {'title': '', 'premise': '', 'character_role': '', 'gm_guidance': [], 'world_pressures': []}

    gm_guidance = campaign.get('gm_guidance') or []
    if isinstance(gm_guidance, list):
        gm_guidance = gm_guidance[:MAX_GM_GUIDANCE]
    else:
        gm_guidance = []

    world_pressures = campaign.get('world_pressures') or []
    if isinstance(world_pressures, list):
        world_pressures = world_pressures[:MAX_WORLD_PRESSURES]
    else:
        world_pressures = []

    return {
        'title': str(campaign.get('title', '') or '')[:200],
        'premise': str(campaign.get('premise', '') or '')[:500],
        'tone': str(campaign.get('tone', '') or '')[:200],
        'character_role': str(campaign.get('character_role', '') or '')[:300],
        'gm_guidance': gm_guidance,
        'world_pressures': world_pressures,
        'magic_style': str(campaign.get('magic_style', '') or '')[:300],
    }


def _compress_world(world: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize world: world_state + recent events + faction names. No full dumps."""
    if not world or not isinstance(world, dict):
        return {'world_state': {'flags': {}, 'counters': {}, 'clocks_summary': []}, 'recent_events': [], 'faction_names': []}

    ws = world.get('world_state') or {}
    if not isinstance(ws, dict):
        ws = {}
    flags = {k: v for k, v in (ws.get('flags') or {}).items() if isinstance(k, str) and not k.startswith('_')}
    counters = {k: v for k, v in (ws.get('counters') or {}).items() if isinstance(k, str) and not k.startswith('_')}
    from game.schema_contracts import world_clock_row_summary_line

    clocks_raw = ws.get('clocks') or {}
    clocks_summary: List[str] = []
    for k, c in clocks_raw.items():
        if not isinstance(k, str) or k.startswith('_') or not isinstance(c, dict):
            continue
        seg = world_clock_row_summary_line(k, c)
        if seg:
            clocks_summary.append(seg)
    world_state_view = {'flags': flags, 'counters': counters, 'clocks_summary': clocks_summary}

    event_log = world.get('event_log') or []
    recent_events: List[str] = []
    if isinstance(event_log, list):
        for entry in event_log[-MAX_RECENT_EVENTS:]:
            if isinstance(entry, dict) and isinstance(entry.get('text'), str):
                recent_events.append(entry['text'][:200])
            elif isinstance(entry, str):
                recent_events.append(entry[:200])

    factions = world.get('factions') or []
    faction_names: List[str] = []
    if isinstance(factions, list):
        for f in factions[:10]:
            if isinstance(f, dict) and isinstance(f.get('name'), str):
                faction_names.append(f['name'])

    prog_counts: Dict[str, int] | None = None
    if isinstance(world, dict):
        _wp = compose_ctir_world_progression_slice(
            world,
            changed_node_ids=merge_progression_changed_node_signals(
                resolution=None,
                world=world,
                session=None,
            ),
        )
        prog_counts = {
            "active_projects": len(_wp.get("active_projects") or []),
            "faction_pressure": len(_wp.get("faction_pressure") or []),
            "faction_agenda": len(_wp.get("faction_agenda") or []),
            "world_clocks": len(_wp.get("world_clocks") or []),
            "set_flags": len(_wp.get("set_flags") or []),
        }
    out: Dict[str, Any] = {
        'world_state': world_state_view,
        'recent_events': recent_events,
        'faction_names': faction_names,
    }
    if prog_counts is not None:
        out["progression_counts"] = prog_counts
    return out



def _infer_log_entry_source_turn(
    entry: Dict[str, Any],
    *,
    index_in_window: int,
    window_len: int,
    current_turn: int,
) -> int | None:
    """Best-effort turn index for a log entry; falls back to position vs session turn_counter."""
    lm = entry.get("log_meta") if isinstance(entry.get("log_meta"), dict) else {}
    for key in ("turn_counter", "turn", "session_turn_counter"):
        raw = lm.get(key)
        if raw is not None:
            try:
                return int(raw)
            except (TypeError, ValueError):
                pass
    res = entry.get("resolution")
    if isinstance(res, dict):
        for key in ("turn_counter", "turn"):
            raw = res.get(key)
            if raw is not None:
                try:
                    return int(raw)
                except (TypeError, ValueError):
                    pass
    if current_turn > 0 and window_len > 0:
        return int(current_turn) - int(window_len) + int(index_in_window)
    return None


def _memory_window_title_topic_tokens(title: str) -> List[str]:
    """Conservative tokens from a lead/title string (no invented entities)."""
    raw = str(title or "").strip().lower()
    if not raw:
        return []
    toks = [m.group(0).lower() for m in _CONV_MEM_TITLE_TOPIC_RE.finditer(raw)]
    out: List[str] = []
    seen: Set[str] = set()
    for t in toks:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= 8:
            break
    return out


def _memory_window_focus_topic_tokens(active_topic_anchor: Mapping[str, Any] | None) -> List[str]:
    if not isinstance(active_topic_anchor, Mapping):
        return []
    focus = str(active_topic_anchor.get("focus_fragment") or "").strip()
    if not focus:
        return []
    return _memory_window_title_topic_tokens(focus)


def _collect_interlocutor_lead_candidate_rows(
    interlocutor_lead_context: Mapping[str, Any] | None,
    *,
    max_rows: int,
) -> List[Dict[str, Any]]:
    if not isinstance(interlocutor_lead_context, Mapping):
        return []
    seen: Set[str] = set()
    out: List[Dict[str, Any]] = []
    for key in ("introduced_by_npc", "unacknowledged_from_npc", "recently_discussed_with_npc"):
        part = interlocutor_lead_context.get(key)
        if not isinstance(part, list):
            continue
        for row in part:
            if not isinstance(row, dict):
                continue
            lid = str(row.get("lead_id") or "").strip()
            if lid:
                if lid in seen:
                    continue
                seen.add(lid)
            out.append(row)
            if len(out) >= max_rows:
                return out
    return out


def _assemble_conversational_memory_candidates(
    *,
    recent_log_for_prompt: List[Dict[str, Any]],
    current_turn: int,
    runtime_compressed: Mapping[str, Any] | None,
    interlocutor_lead_context: Mapping[str, Any] | None,
    active_npc_id: str | None,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Build selector candidates + parallel extras (for legacy recent_log shape). Order: recent turns, leads, runtime."""
    candidates: List[Dict[str, Any]] = []
    extras: List[Dict[str, Any]] = []

    entries = (
        recent_log_for_prompt[-MAX_RECENT_LOG:]
        if isinstance(recent_log_for_prompt, list) and recent_log_for_prompt
        else []
    )
    window_len = len(entries)
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        log_meta = entry.get("log_meta") if isinstance(entry.get("log_meta"), dict) else {}
        player_input = str(log_meta.get("player_input", "") or entry.get("request", {}).get("chat", "") or "")[:300]
        gm_output = entry.get("gm_output") or {}
        gm_text = gm_output.get("player_facing_text", "") if isinstance(gm_output, dict) else ""
        gm_snippet = str(gm_text)[:MAX_LOG_ENTRY_SNIPPET] if isinstance(gm_text, str) else ""
        st = _infer_log_entry_source_turn(
            entry,
            index_in_window=idx,
            window_len=window_len,
            current_turn=current_turn,
        )
        text = f"P: {player_input} | G: {gm_snippet}"
        if len(text) > 520:
            text = text[:520]
        candidates.append(
            {
                "kind": "recent_turn",
                "entity_ids": [],
                "topic_tokens": [],
                "source_turn": st,
                "text": text,
            }
        )
        extras.append({"player_input": player_input, "gm_snippet": gm_snippet})

    npc_id = str(active_npc_id or "").strip()
    for row in _collect_interlocutor_lead_candidate_rows(
        interlocutor_lead_context,
        max_rows=8,
    ):
        title = str(row.get("title") or "").strip()
        lid = str(row.get("lead_id") or "").strip()
        disc = str(row.get("disclosure_level") or "").strip().lower() or "hinted"
        st_raw = row.get("last_discussed_turn")
        st: int | None
        try:
            st = int(st_raw) if st_raw is not None else None
        except (TypeError, ValueError):
            st = None
        if st is None:
            ft = row.get("first_discussed_turn")
            try:
                st = int(ft) if ft is not None else None
            except (TypeError, ValueError):
                st = None
        text = f"Lead {lid}: {title} ({disc})" if lid else f"Lead: {title} ({disc})"
        ent: List[str] = [npc_id] if npc_id else []
        candidates.append(
            {
                "kind": "npc_lead_discussion",
                "entity_ids": ent,
                "topic_tokens": _memory_window_title_topic_tokens(title),
                "source_turn": st,
                "text": text[:520],
            }
        )
        extras.append({"player_input": "", "gm_snippet": text})

    rt = runtime_compressed if isinstance(runtime_compressed, Mapping) else {}
    raw_ctx = rt.get("recent_contextual_leads")
    if isinstance(raw_ctx, list):
        for item in raw_ctx[-MAX_RECENT_CONTEXTUAL_LEADS:]:
            if not isinstance(item, dict):
                continue
            subject = str(item.get("subject") or "").strip()
            key = str(item.get("key") or "").strip()
            if not subject and not key:
                continue
            try:
                lt = int(item.get("last_turn", 0) or 0)
            except (TypeError, ValueError):
                lt = 0
            st2: int | None = lt if lt > 0 else None
            text2 = f"{subject} [{key}]".strip() if key else subject
            candidates.append(
                {
                    "kind": "contextual_thread",
                    "entity_ids": [],
                    "topic_tokens": _memory_window_title_topic_tokens(subject),
                    "source_turn": st2,
                    "text": text2[:520],
                }
            )
            extras.append({"player_input": "", "gm_snippet": text2[:MAX_LOG_ENTRY_SNIPPET]})

    while len(candidates) > CONVERSATIONAL_MEMORY_MAX_CANDIDATES:
        candidates.pop()
        extras.pop()

    return candidates, extras


def _recent_log_payload_from_selected_memory(
    selected: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    extras: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Map selected items to legacy recent_log rows (player_input + gm_snippet)."""
    out: List[Dict[str, Any]] = []
    for sel in selected:
        matched_i: int | None = None
        for i, c in enumerate(candidates):
            if (
                c.get("kind") == sel.get("kind")
                and c.get("source_turn") == sel.get("source_turn")
                and c.get("text") == sel.get("text")
            ):
                matched_i = i
                break
        if matched_i is None:
            out.append(
                {
                    "player_input": "",
                    "gm_snippet": str(sel.get("text") or "")[:MAX_LOG_ENTRY_SNIPPET],
                }
            )
            continue
        ex = extras[matched_i] if matched_i < len(extras) else {}
        if not isinstance(ex, dict):
            ex = {}
        pi = str(ex.get("player_input") or "")
        gm = str(ex.get("gm_snippet") or "")
        out.append({"player_input": pi, "gm_snippet": gm})
    return out


def _compress_combat(combat: Dict[str, Any]) -> Dict[str, Any] | None:
    """Include combat only when active; otherwise minimal/null."""
    if not combat or not isinstance(combat, dict):
        return None
    if not combat.get('in_combat'):
        return {'in_combat': False}
    return combat




def _build_turn_summary(
    user_text: str,
    resolution: Dict[str, Any] | None,
    intent: Dict[str, Any] | None,
    *,
    narrative_plan_mode: str | None = None,
    action_outcome_contract_blocked: bool = False,
) -> Dict[str, Any]:
    """Build a compact, structured summary of this turn for narration anchoring."""
    if action_outcome_contract_blocked:
        return {
            "action_outcome_contract_blocked": True,
            "action_descriptor": None,
            "resolution_kind": None,
            "action_id": None,
            "resolved_prompt": None,
            "intent_labels": [],
            "raw_player_input": str(user_text or ""),
            "raw_player_input_usage": (
                "action_outcome_contract_failed: do not narrate mechanics from resolution, hints, or rolls; "
                "use narration_seam_audit / prompt_debug only."
            ),
        }

    res = resolution if isinstance(resolution, dict) else {}
    res_kind = str(res.get('kind') or '').strip()
    res_label = str(res.get('label') or '').strip()
    res_action_id = str(res.get('action_id') or '').strip()
    # ``prompt`` can contain engine hint-like prose for some resolvers; treat it as
    # non-authoritative and avoid using it as the turn summary anchor when possible.
    res_prompt = ""
    if isinstance(res.get("label"), str) and str(res.get("label") or "").strip():
        res_prompt = ""
    else:
        res_prompt = str(res.get('prompt') or '').strip()

    labels = intent.get('labels') if isinstance(intent, dict) and isinstance(intent.get('labels'), list) else []
    labels = [str(label).strip() for label in labels if isinstance(label, str) and str(label).strip()]

    _nm = str(narrative_plan_mode or "").strip()
    if _nm == "action_outcome":
        # Plan-owned mechanics only; never echo engine hint/prompt/label prose as anchors.
        if res_kind:
            descriptor = res_kind.replace('_', ' ')
            if res_action_id:
                descriptor = f"{descriptor} ({res_action_id})".strip()
        elif labels:
            descriptor = labels[0].replace('_', ' ')
        else:
            descriptor = "resolved_action"
        return {
            'action_descriptor': descriptor,
            'resolution_kind': res_kind or None,
            'action_id': res_action_id or None,
            'resolved_prompt': None,
            'intent_labels': labels,
            'raw_player_input': str(user_text or ''),
            'raw_player_input_usage': (
                'Retain for exact wording and disambiguation only. '
                'Prefer action_descriptor + resolution_kind + mechanical_resolution for narration framing.'
            ),
        }

    if res_kind:
        descriptor = res_label or res_kind.replace('_', ' ')
    elif labels:
        descriptor = labels[0].replace('_', ' ')
    else:
        descriptor = 'general_action'

    return {
        'action_descriptor': descriptor,
        'resolution_kind': res_kind or None,
        'action_id': res_action_id or None,
        'resolved_prompt': res_prompt or None,
        'intent_labels': labels,
        'raw_player_input': str(user_text or ''),
        'raw_player_input_usage': (
            'Retain for exact wording and disambiguation only. '
            'Prefer action_descriptor + resolution_kind + mechanical_resolution for narration framing.'
        ),
    }


MANUAL_PLAY_COMPACT_VISIBLE_FACT_LIMIT = 5
MANUAL_PLAY_COMPACT_MEMORY_LIMIT = 6
MANUAL_PLAY_COMPACT_RECENT_LOG_LIMIT = 4


_EXPECTED_TRANSITION_NODE_KEYS: tuple[str, ...] = (
    "transition_required",
    "transition_type",
    "before_anchor",
    "after_anchor",
    "continuity_anchor_ids",
    "derivation_codes",
    "source_fields",
)


def _resolution_has_transition_signal(resolution_sem: Mapping[str, Any] | None) -> bool:
    """Seam-signal only (never used to synthesize transition payload)."""
    if not isinstance(resolution_sem, Mapping) or not resolution_sem:
        return False
    if bool(resolution_sem.get("resolved_transition")):
        return True
    kind = str(resolution_sem.get("kind") or "").strip().lower()
    if kind in {"scene_transition", "travel"}:
        return True
    if str(resolution_sem.get("target_scene_id") or "").strip():
        return True
    auth = resolution_sem.get("authoritative_outputs")
    if isinstance(auth, Mapping):
        if bool(auth.get("resolved_transition")) or str(auth.get("target_scene_id") or "").strip():
            return True
    return False


def _project_transition_node_for_prompt(
    narrative_plan: Mapping[str, Any] | None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Consume narrative_plan.transition_node as structured data only (no inference, no repair)."""
    if not isinstance(narrative_plan, Mapping) or not narrative_plan:
        return None, ["missing_narrative_plan"]
    raw = narrative_plan.get("transition_node")
    if raw is None:
        return None, ["missing_transition_node"]
    if not isinstance(raw, Mapping):
        return None, ["transition_node_not_mapping"]
    missing = [k for k in _EXPECTED_TRANSITION_NODE_KEYS if k not in raw]
    if missing:
        return None, ["transition_node_missing_keys:" + ",".join(missing[:16])]
    # Shallow structural typing only; do not "fix" or add anchors/ids.
    if not isinstance(raw.get("transition_required"), bool):
        return None, ["transition_node_bad_type:transition_required"]
    if not isinstance(raw.get("transition_type"), str):
        return None, ["transition_node_bad_type:transition_type"]
    if not isinstance(raw.get("before_anchor"), Mapping):
        return None, ["transition_node_bad_type:before_anchor"]
    if not isinstance(raw.get("after_anchor"), Mapping):
        return None, ["transition_node_bad_type:after_anchor"]
    if not isinstance(raw.get("continuity_anchor_ids"), list):
        return None, ["transition_node_bad_type:continuity_anchor_ids"]
    if not isinstance(raw.get("derivation_codes"), list):
        return None, ["transition_node_bad_type:derivation_codes"]
    if not isinstance(raw.get("source_fields"), list):
        return None, ["transition_node_bad_type:source_fields"]
    return dict(raw), []


def _should_use_manual_play_compact_prompt(
    *,
    prompt_profile: str,
    narration_obligations: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None,
    uncertainty_hint: Mapping[str, Any] | None,
    follow_up_pressure: Mapping[str, Any] | None,
    active_topic_anchor: Mapping[str, Any] | None,
) -> bool:
    if prompt_profile == "manual_play_compact":
        return True
    if prompt_profile != "manual_play_auto":
        return False
    obligations = narration_obligations if isinstance(narration_obligations, Mapping) else {}
    res = resolution if isinstance(resolution, Mapping) else {}
    if obligations.get("is_opening_scene") or obligations.get("must_advance_scene"):
        return False
    if res.get("requires_check"):
        return False
    if isinstance(uncertainty_hint, Mapping) and uncertainty_hint:
        return False
    if isinstance(active_topic_anchor, Mapping) and active_topic_anchor.get("active"):
        return False
    if isinstance(follow_up_pressure, Mapping) and follow_up_pressure:
        return False
    return True


def _compact_manual_play_instructions(
    *,
    mode_instruction: str,
    narration_obligations: Mapping[str, Any] | None,
    response_policy: Mapping[str, Any] | None,
    has_active_interlocutor: bool,
    social_authority: bool,
    has_scene_change_context: bool,
    naming_line: str | None,
    answer_style_hints: List[str],
    narrative_plan_present: bool = False,
    narrative_mode_instruction_lines: Sequence[str] | None = None,
) -> List[str]:
    obligations = narration_obligations if isinstance(narration_obligations, Mapping) else {}
    policy = response_policy if isinstance(response_policy, Mapping) else {}
    out: List[str] = [
        RULE_PRIORITY_COMPACT_INSTRUCTION,
        "Always answer the player first. Prefer a grounded partial answer over refusal. Never output meta explanations.",
        NO_VALIDATOR_VOICE_RULE,
        "Follow response_policy.rule_priority_order strictly. Use response_policy as the full authority for answer shape, continuity, and safety boundaries.",
    ]
    if has_active_interlocutor:
        out.append("Keep the active conversation primary over general scene recap.")
    if social_authority:
        out.append(
            "SOCIAL INTERACTION LOCK: The active interlocutor must carry the substantive reply. Do not replace the answer with ambient scene narration."
        )
    if obligations.get("active_npc_reply_expected"):
        out.append("If narration_obligations.active_npc_reply_expected is true, complete that NPC's substantive reply now.")
    if obligations.get("should_answer_active_npc"):
        out.append("Prioritize the active interlocutor's answer over broad scene description.")
    if obligations.get("avoid_input_echo") or obligations.get("avoid_player_action_restatement"):
        out.append("Do not restate or lightly paraphrase player_input. Continue forward with new information.")
    ac = policy.get("answer_completeness") if isinstance(policy.get("answer_completeness"), Mapping) else {}
    if ac.get("answer_required"):
        out.append("ANSWER COMPLETENESS: When response_policy.answer_completeness.answer_required is true, lead with the substantive answer in the first sentence.")
    rd = policy.get("response_delta") if isinstance(policy.get("response_delta"), Mapping) else {}
    if rd.get("enabled"):
        out.append("RESPONSE DELTA: Add net-new value. Do not merely restate the prior answer.")
    na = policy.get("narrative_authenticity") if isinstance(policy.get("narrative_authenticity"), Mapping) else {}
    if na.get("enabled"):
        out.append(
            "NARRATIVE AUTHENTICITY: Do not recycle the same surface clause from narration into quoted speech; "
            "prefer new signal on follow-ups; stay diegetic."
        )
    if naming_line:
        out.append(naming_line)
    if answer_style_hints:
        out.extend(list(answer_style_hints[:2]))
    out.append(
        "CONVERSATIONAL MEMORY WINDOW: Treat selected_conversational_memory as the active thread for this turn and do not revive omitted stale threads unless the player re-grounds them."
    )
    out.append(
        "POLICY TAIL: Obey response_policy.narrative_authority, narrative_authenticity, tone_escalation, anti_railroading, context_separation, player_facing_narration_purity, and scene anchoring without re-explaining them in narration."
    )
    if narrative_plan_present:
        out.append(
            "NARRATIVE PLAN: When `narrative_plan` is on the payload, use its scene_anchors, active_pressures, "
            "required_new_information, allowable_entity_references (visible handle boundary only—not focality), "
            "role_allocation weights, `scene_opening` when present (structural opener anchors only—no prose there), "
            "and `narrative_roles` emphasis_band/signals as optional composition hints—together with "
            "the `NARRATIVE MODE (STRUCTURAL DELTA)` lines—same precedence as full prompts (visibility and response_policy still win conflicts)."
        )
    if narrative_mode_instruction_lines:
        out.extend(list(narrative_mode_instruction_lines))
    out.append(mode_instruction)
    return out


def _project_clause_referent_prompt_hints(
    referent_tracking: Mapping[str, Any] | None,
    *,
    max_rows: int = 4,
) -> list[dict[str, Any]] | None:
    """Build ``referent_clause_prompt_hints`` from ``clause_referent_plan`` (read-side only).

    New dict rows; does not mutate *referent_tracking*. Subset of flags/labels already on
    the artifact — not a parser, planner, or CTIR mirror.
    """
    if not isinstance(referent_tracking, Mapping):
        return None
    raw = referent_tracking.get("clause_referent_plan")
    if not isinstance(raw, list) or not raw:
        return None
    scored: list[tuple[tuple[int, int, int, str], dict[str, Any]]] = []
    for row in raw:
        if not isinstance(row, Mapping):
            continue
        cid = str(row.get("clause_id") or "").strip()
        if not cid:
            continue
        amb = str(row.get("ambiguity_class") or "").strip().lower()
        amb_rank = {"ambiguous_plural": 3, "ambiguous_singular": 2, "no_anchor": 2, "none": 0}.get(amb, 1)
        tss = 1 if bool(row.get("target_switch_sensitive")) else 0
        buckets_raw = row.get("risky_pronoun_buckets") if isinstance(row.get("risky_pronoun_buckets"), list) else []
        norm_buckets: list[str] = []
        gendered_hits = 0
        for b in buckets_raw:
            if not isinstance(b, str):
                continue
            bk = str(b).strip().lower().replace(" ", "_")
            if bk in ("he_him", "she_her", "it_its"):
                gendered_hits = 1
            norm_buckets.append(bk)
        norm_buckets = sorted(dict.fromkeys(norm_buckets))[:6]
        labels = sorted(
            {
                str(x).strip()
                for x in (row.get("allowed_explicit_labels") or [])
                if isinstance(x, str) and str(x).strip()
            }
        )[:4]
        ck = str(row.get("clause_kind") or "").strip() or None
        explicit_anchor_preferred = bool(tss or amb_rank >= 2 or gendered_hits)
        scored.append(
            (
                (-tss, -amb_rank, -gendered_hits, cid),
                {
                    "clause_id": cid,
                    "clause_kind": ck,
                    "ambiguity_class": amb if amb else None,
                    "target_switch_sensitive": bool(tss),
                    "explicit_anchor_preferred": explicit_anchor_preferred,
                    "risky_pronoun_buckets": norm_buckets,
                    "allowed_explicit_labels": labels,
                },
            )
        )
    scored.sort(key=lambda x: x[0])
    out = [row for _, row in scored[: max(1, max_rows)]]
    return out or None


def build_narration_context(
    campaign: Dict[str, Any],
    world: Dict[str, Any],
    session: Dict[str, Any],
    character: Dict[str, Any],
    scene: Dict[str, Any],
    combat: Dict[str, Any],
    recent_log: List[Dict[str, Any]],
    user_text: str,
    resolution: Dict[str, Any] | None,
    scene_runtime: Dict[str, Any] | None,
    *,
    public_scene: Dict[str, Any],
    discoverable_clues: List[str],
    gm_only_hidden_facts: List[str],
    gm_only_discoverable_locked: List[str],
    discovered_clue_records: List[Dict[str, Any]],
    undiscovered_clue_records: List[Dict[str, Any]],
    pending_leads: List[Any],
    intent: Dict[str, Any],
    world_state_view: Dict[str, Any],
    mode_instruction: str,
    recent_log_for_prompt: List[Dict[str, Any]],
    uncertainty_hint: Dict[str, Any] | None = None,
    prompt_profile: str = "full",
    include_non_public_prompt_keys: bool = False,
) -> Dict[str, Any]:
    """Build a compressed narration context payload for GPT.

    Caller must precompute scene layers (public_scene, clues, hidden, etc.)
    and pass them in. This avoids duplicating _scene_layers logic and ensures
    hidden facts stay in gm_only only.

    Returns a dict suitable for JSON serialization as the user message content.

    Narration contracts are layered: visibility (reference scope), narrative_authority (certainty
    and assertion boundaries), scene_state_anchor (grounding), answer_completeness
    (answer-shape obligations), fallback_behavior (narrow uncertainty fallback shape),
    tone_escalation (interpersonal intensity caps), anti_railroading (player agency vs surfaced leads),
    context_separation (ambient pressure vs local exchange), and player_facing_narration_purity
    (no scaffold/menu/engine coaching in prose),
    and social_response_structure (dialogue-turn spoken shape when response type requires dialogue),
    narrative_authenticity (anti-echo / signal-density / diegetic-shape pressure shipped on response_policy),
    and interaction_continuity (thread / interlocutor anchoring snapshot for enforcement layers);
    see module docstring.

    By default the returned mapping is the **model-facing** bundle: top-level keys are
    shallow-projected through :func:`game.state_channels.project_public_payload` and
    checked with :func:`game.state_channels.assert_no_debug_keys_in_prompt_payload`.
    Set ``include_non_public_prompt_keys=True`` only for tests or tooling that must
    inspect builder-local mirrors such as ``prompt_debug`` (never for live model input).
    """
    assert not (isinstance(scene, dict) and scene.get("_is_canon")), (
        "Prompt built from canonical scene instead of effective scene"
    )
    # Head state through scene anchor: shared with :mod:`game.narration_plan_bundle` (renderer-only downstream).
    _head = _build_narration_context_head_state(
        campaign,
        world,
        session,
        character,
        scene,
        combat,
        recent_log,
        user_text,
        resolution,
        scene_runtime,
        public_scene=public_scene,
        discoverable_clues=discoverable_clues,
        gm_only_hidden_facts=gm_only_hidden_facts,
        gm_only_discoverable_locked=gm_only_discoverable_locked,
        discovered_clue_records=discovered_clue_records,
        undiscovered_clue_records=undiscovered_clue_records,
        pending_leads=pending_leads,
        intent=intent,
        world_state_view=world_state_view,
        mode_instruction=mode_instruction,
        recent_log_for_prompt=recent_log_for_prompt,
        uncertainty_hint=uncertainty_hint,
        prompt_profile=prompt_profile,
        include_non_public_prompt_keys=include_non_public_prompt_keys,
    )
    ctir_obj = _head["ctir_obj"]
    prompt_sem = _head["prompt_sem"]
    resolution_sem = _head["resolution_sem"]
    intent_sem = _head["intent_sem"]
    interaction_sem = _head["interaction_sem"]
    intent_for_scene_payload = _head["intent_for_scene_payload"]
    wp_projection = _head["wp_projection"]
    wp_hint_lines = _head["wp_hint_lines"]
    active_pending_leads = _head["active_pending_leads"]
    runtime = _head["runtime"]
    session_view = _head["session_view"]
    narration_obligations = _head["narration_obligations"]
    social_authority = _head["social_authority"]
    eff_uncertainty_hint = _head["eff_uncertainty_hint"]
    recent_log_compact = _head["recent_log_compact"]
    response_policy = _head["response_policy"]
    res = _head["res"]
    state_changes = _head["state_changes"]
    scene_advancement = _head["scene_advancement"]
    has_scene_change_context = _head["has_scene_change_context"]
    interaction_continuity = _head["interaction_continuity"]
    has_active_interlocutor = _head["has_active_interlocutor"]
    scene_pub_id = _head["scene_pub_id"]
    interlocutor_export = _head["interlocutor_export"]
    answer_style_hints_list = _head["answer_style_hints_list"]
    clue_records_all = _head["clue_records_all"]
    clue_visibility = _head["clue_visibility"]
    visibility_contract = _head["visibility_contract"]
    visible_facts_for_prompt = _head["visible_facts_for_prompt"]
    opening_inputs_are_curated = _head["opening_inputs_are_curated"]
    opening_fact_telemetry = _head["opening_fact_telemetry"]
    opening_selector_selected_facts = _head["opening_selector_selected_facts"]
    res_for_vis = _head["res_for_vis"]
    res_md_vis = _head["res_md_vis"]
    opening_scene_export = _head["opening_scene_export"]
    visible_facts_export = _head["visible_facts_export"]
    narration_visibility = _head["narration_visibility"]
    scene_state_anchor_contract = _head["scene_state_anchor_contract"]
    public_scene = _head["public_scene"]

    # Narrative plan (C1): CTIR-backed narration requires a stamp-matched session bundle; no local replan.
    narrative_plan: Dict[str, Any] | None = None
    narrative_plan_build_error: str | None = None
    _bundle = get_attached_narration_plan_bundle(session if isinstance(session, dict) else None)
    _ctir_stamp = str((session or {}).get(SESSION_CTIR_STAMP_KEY) or "").strip() if isinstance(session, dict) else ""
    _bundle_stamp = get_narration_plan_bundle_stamp(session if isinstance(session, dict) else None)
    _bundle_renderer_inputs: Dict[str, Any] = {}
    bundle_stamp_ok = False
    if ctir_obj is not None:
        bundle_stamp_ok = (
            isinstance(_bundle, dict)
            and bool(_bundle_stamp)
            and bool(_ctir_stamp)
            and _bundle_stamp == _ctir_stamp
        )
        if bundle_stamp_ok:
            np = _bundle.get("narrative_plan")
            narrative_plan = np if isinstance(np, dict) else None
            pm = _bundle.get("plan_metadata") if isinstance(_bundle.get("plan_metadata"), dict) else {}
            err_raw = pm.get("narration_plan_bundle_error")
            narrative_plan_build_error = str(err_raw).strip() if err_raw else None
            if narrative_plan is None and not narrative_plan_build_error:
                narrative_plan_build_error = "narration_plan_bundle_missing_plan"
            _ri = _bundle.get("renderer_inputs")
            _bundle_renderer_inputs = dict(_ri) if isinstance(_ri, dict) else {}
        else:
            narrative_plan = None
            if not _ctir_stamp:
                narrative_plan_build_error = "narration_plan_bundle_required:missing_ctir_stamp"
            elif not isinstance(_bundle, dict):
                narrative_plan_build_error = "narration_plan_bundle_required:bundle_absent"
            elif not _bundle_stamp or _bundle_stamp != _ctir_stamp:
                narrative_plan_build_error = "narration_plan_bundle_required:stamp_mismatch_or_stale"
            else:
                narrative_plan_build_error = "narration_plan_bundle_required"

    if (
        ctir_obj is not None
        and bundle_stamp_ok
        and isinstance(response_policy, dict)
        and isinstance(_bundle_renderer_inputs.get("response_policy"), dict)
    ):
        brp = _bundle_renderer_inputs["response_policy"]
        rtc_override = brp.get("response_type_contract")
        if isinstance(rtc_override, dict):
            response_policy["response_type_contract"] = copy.deepcopy(rtc_override)

    if isinstance(narrative_plan, dict) and isinstance(opening_scene_export, dict):
        patch_opening_export_with_plan_scene_opening(
            opening_scene_export,
            scene_opening=narrative_plan.get("scene_opening"),
        )

    # C1-B: prompt_context must not reconstruct continuation progression from raw state/logs.
    # A "verified CTIR-backed continuation" here means: CTIR attached, stamp-matched bundle,
    # and the attached plan projects a continuation-mode turn. (Block B enforcement happens upstream;
    # prompt_context is a renderer/packager only.)
    is_verified_ctir_continuation = bool(
        ctir_obj is not None
        and bundle_stamp_ok
        and isinstance(narrative_plan, dict)
        and str(narrative_plan.get("narrative_mode") or "").strip().lower() == "continuation"
    )

    prompt_debug_anchor = {
        "scene_state_anchor": {
            "enabled": bool(scene_state_anchor_contract.get("enabled")),
            "scene_id": scene_state_anchor_contract.get("scene_id"),
            "counts": {
                "location": len(scene_state_anchor_contract.get("location_tokens") or []),
                "actor": len(scene_state_anchor_contract.get("actor_tokens") or []),
                "player_action": len(scene_state_anchor_contract.get("player_action_tokens") or []),
            },
        },
        "opening_scene_realization": {
            "opening_mode": bool(opening_scene_export.get("opening_mode"))
            if isinstance(opening_scene_export, dict)
            else False,
            "validator": (opening_scene_export.get("contract") or {}).get("validator")
            if isinstance(opening_scene_export, dict) and isinstance(opening_scene_export.get("contract"), dict)
            else None,
        },
        "narrative_plan": _narrative_plan_prompt_debug_anchor(
            narrative_plan,
            build_error=narrative_plan_build_error,
        ),
        "world_progression": {
            "read_source": "ctir"
            if (
                ctir_obj is not None
                and isinstance((ctir_obj.get("world") or {}).get("progression"), dict)
            )
            else "backbone_fallback",
            "changed_node_count": len((wp_projection or {}).get("changed_node_ids") or []),
            "changed_node_ids_head": list((wp_projection or {}).get("changed_node_ids") or [])[:8],
            "active_projects_n": len((wp_projection or {}).get("active_projects") or []),
            "faction_pressure_n": len((wp_projection or {}).get("faction_pressure") or []),
            "faction_agenda_n": len((wp_projection or {}).get("faction_agenda") or []),
            "world_clocks_n": len((wp_projection or {}).get("world_clocks") or []),
            "set_flags_n": len((wp_projection or {}).get("set_flags") or []),
        },
        "planner_convergence_consumer": _planner_convergence_consumer_debug_slice(
            ctir_present=ctir_obj is not None,
            bundle_present=isinstance(_bundle, dict),
            stamp_matches=bundle_stamp_ok,
            narrative_plan_full=narrative_plan if isinstance(narrative_plan, dict) else None,
        ),
    }
    _cont_mode = (
        str((narrative_plan or {}).get("narrative_mode") or "").strip().lower()
        if isinstance(narrative_plan, dict)
        else ""
    )
    if is_verified_ctir_continuation:
        _progression_src = "narrative_plan_bundle"
    elif _cont_mode != "continuation":
        _progression_src = "not_continuation"
    elif ctir_obj is None:
        _progression_src = "legacy_non_ctir"
    else:
        _progression_src = "unavailable"
    prompt_debug_anchor["continuation_packaging"] = {
        "continuation_progression_source": _progression_src,
        "prompt_context_reconstructed_continuation": False,
        "continuation_plan_projection_used": bool(is_verified_ctir_continuation),
    }
    first_mention_contract: Dict[str, Any] = {
        "enabled": True,
        "requires_explicit_intro": True,
        "requires_grounding": True,
        "disallow_pronoun_first_reference": True,
        "disallow_unearned_familiarity": True,
    }

    narration_seam_audit: Dict[str, Any] | None = None
    if ctir_obj is not None and narrative_plan is None:
        narration_seam_audit = {
            "narrative_plan_mandatory_seam": True,
            "narrative_plan_present": False,
            "narration_plan_bundle_error": narrative_plan_build_error or "unknown_narrative_plan_failure",
            "semantic_bypass_blocked": True,
        }

    # Block B: prompt_context consumes transition_node as structured data only (no inference, no repair).
    transition_payload: dict[str, Any] | None = None
    transition_failure_codes: list[str] = []
    if isinstance(narrative_plan, Mapping):
        transition_payload, transition_failure_codes = _project_transition_node_for_prompt(narrative_plan)
    else:
        transition_payload, transition_failure_codes = (None, ["missing_narrative_plan"])

    transition_required = bool(transition_payload.get("transition_required")) if isinstance(transition_payload, dict) else False
    if isinstance(narration_obligations, dict):
        narration_obligations = {**narration_obligations, "must_advance_scene": bool(transition_required)}

    # Seam-failure metadata for missing/malformed transition_node and for blocked legacy inference paths.
    _transition_signal = _resolution_has_transition_signal(resolution_sem if isinstance(resolution_sem, Mapping) else None)
    _transition_missing = bool(_transition_signal and not isinstance(transition_payload, dict))
    _anchor_incomplete = False
    if isinstance(transition_payload, dict) and transition_required:
        ba = transition_payload.get("before_anchor") if isinstance(transition_payload.get("before_anchor"), Mapping) else {}
        aa = transition_payload.get("after_anchor") if isinstance(transition_payload.get("after_anchor"), Mapping) else {}
        _anchor_incomplete = not bool(ba) or not bool(aa)
    if _transition_missing or _anchor_incomplete or transition_failure_codes:
        tn_audit = {
            "transition_signal_present": bool(_transition_signal),
            "transition_node_present": isinstance(transition_payload, dict),
            "transition_node_failure_codes": list(transition_failure_codes[:16]) if transition_failure_codes else [],
            "transition_required": bool(transition_required),
            "blocked_inference_path": bool(_transition_missing),
            "incomplete_required_anchors": bool(_anchor_incomplete),
        }
        if isinstance(narration_seam_audit, dict):
            narration_seam_audit = {**narration_seam_audit, "transition_node_consumer": tn_audit}
        else:
            narration_seam_audit = {"transition_node_consumer": tn_audit}

    # prompt_debug lane: compact transition consumer mirror (inspect-only).
    prompt_debug_anchor["transition_node_consumer"] = {
        "present": isinstance(transition_payload, dict),
        "transition_signal_present": bool(_transition_signal),
        "failure_codes": list(transition_failure_codes[:16]) if transition_failure_codes else [],
        "blocked_inference_path": bool(_transition_missing),
        "required": bool(transition_required) if isinstance(transition_payload, dict) else None,
    }

    # C1-D: dialogue/social planning is shipped as a deterministic structural plan from the bundle.
    # For CTIR-backed social turns, do not locally infer speaker/intent/pressure/tone from logs or raw text.
    _dsp_required = bool(
        ctir_obj is not None
        and social_authority
        and bool(narration_obligations.get("active_npc_reply_expected"))
    )
    _dsp_raw = _bundle_renderer_inputs.get("dialogue_social_plan") if isinstance(_bundle_renderer_inputs, dict) else None
    _dsp_present = bool(ctir_obj is not None and bundle_stamp_ok and isinstance(_dsp_raw, dict))
    _dsp_missing_or_invalid = bool(_dsp_required and not _dsp_present)
    if _dsp_missing_or_invalid:
        _dsp_codes: List[str] = []
        if ctir_obj is None:
            _dsp_codes.append("ctir_absent")
        elif not bundle_stamp_ok:
            _dsp_codes.append("bundle_stamp_invalid_or_mismatch")
        elif not isinstance(_dsp_raw, dict):
            _dsp_codes.append("missing_dialogue_social_plan")
        else:
            _dsp_codes.append("unknown_dialogue_social_plan_failure")
        if isinstance(narration_seam_audit, dict):
            narration_seam_audit = {
                **narration_seam_audit,
                "dialogue_social_plan_contract_blocked": True,
                "dialogue_social_plan_present": False,
                "dialogue_social_plan_failure_codes": _dsp_codes[:16],
            }
        else:
            narration_seam_audit = {
                "dialogue_social_plan_contract_blocked": True,
                "dialogue_social_plan_present": False,
                "dialogue_social_plan_failure_codes": _dsp_codes[:16],
            }

    instructions: List[str] = (
        (
            [
                "WORLD SIMULATION (bounded engine slice): " + " | ".join(wp_hint_lines),
            ]
            if wp_hint_lines
            else []
        )
        + (
            [
                'Prioritize the active conversation over general scene recap.',
                'Do not fall back to base scene description unless the location materially changes, a new threat emerges, the player explicitly surveys the environment, or the scene needs a transition beat.',
            ]
            if has_active_interlocutor and narrative_plan is None
            else []
        )
    ) + [
        RULE_PRIORITY_COMPACT_INSTRUCTION,
        'Always answer the player. Prefer partial truth over refusal. Never output meta explanations.',
        NO_VALIDATOR_VOICE_RULE,
        'Follow response_policy.rule_priority_order strictly. Higher-priority rules override later ones.',
        'Treat response_policy.no_validator_voice as a hard narration-lane rule for standard narration.',
        (
            "ANSWER COMPLETENESS CONTRACT (MANDATORY): Obey response_policy.answer_completeness. "
            "When answer_required is true, answer_must_come_first requires the first sentence to deliver the substantive reply "
            "aligned with expected_answer_shape (direct, bounded_partial using an in-world limit from allowed_partial_reasons, "
            "or refusal_with_reason). Bounded partials must name the limiting reason in-character (uncertainty, lack_of_knowledge, or gated_information). "
            "When forbid_deflection or forbid_generic_nonanswer are true, evasive replies, scene filler before the core reply, and answering-with-a-question are invalid. "
            "When require_concrete_payload is true, include at least one handle from concrete_payload_any_of. "
            "Incomplete or hedged replies must still provide a usable specific or next_lead the player can pursue now."
        ),
        (
            "When response_policy.answer_completeness.expected_voice is npc, keep the turn NPC-carried for the substantive reply "
            "per active interlocutor; when narrator, still lead with the answer in the first sentence when answer_required is true."
        ),
        (
            "When response_policy.response_delta.enabled is true, the player is pressing the same topic again: do not merely restate "
            "the prior answer. Add net-new value via allowed_delta_kinds (new_information, refinement that narrows the prior claim, "
            "consequence, or clarified uncertainty—not paraphrase)."
        ),
        *NARRATION_VISIBILITY_MANDATORY_INSTRUCTIONS,
        *FIRST_MENTION_MANDATORY_INSTRUCTIONS,
        *SCENE_STATE_ANCHOR_MANDATORY_INSTRUCTIONS,
        *(
            [
                "OPERATOR / AUDIT — NARRATION PIPELINE: narrative_plan was mandatory for this CTIR-attached turn but is absent. "
                "Treat this as a visible pipeline failure (semantic_bypass_blocked in narration_seam_audit when present); "
                "obey CTIR + shipped response_policy for facts; do not invent an alternate structural plan from raw scene text.",
            ]
            if ctir_obj is not None and narrative_plan is None
            else []
        ),
        *(
            [
                "OPERATOR / AUDIT — DIALOGUE SOCIAL PLAN CONTRACT: dialogue_social_plan was required for this CTIR-backed social turn but is missing/invalid. "
                "Use narration_seam_audit.dialogue_social_plan_failure_codes for machine-readable trace; do not invent speaker/intent/tone/pressure or generic conversational glue to compensate.",
            ]
            if _dsp_missing_or_invalid
            else []
        ),
        *(
            [
                "DIALOGUE SOCIAL PLAN (HARD RULE): When top-level dialogue_social_plan is present, it is the ONLY dialogue/social planning source for this turn. "
                "You MUST NOT choose the speaker, decide NPC intent, infer pressure/tone, or add generic conversational glue. "
                "Express only the planned reply_kind and dialogue_intent for the shipped speaker, staying within pressure_state and tone_bounds; obey prohibited_content_codes and derivation_codes.",
            ]
            if (_dsp_required and _dsp_present)
            else []
        ),
        *(_NARRATIVE_PLAN_STRUCT_GUIDANCE if narrative_plan is not None else ()),
        *(_narrative_plan_roles_trusted_lane() if _narrative_plan_roles_trustworthy(narrative_plan) else ()),
        *(
            _narrative_plan_upstream_role_repair_instruction(narrative_plan)
            if _narrative_plan_roles_trustworthy(narrative_plan)
            else ()
        ),
        (
            "SCENE MOMENTUM RULE (HARD RULE): Every 2–3 exchanges, you MUST introduce exactly one of: "
            "new_information, new_actor_entering, environmental_change, time_pressure, consequence_or_opportunity. "
            "When you do, include exactly one tag in tags: "
            "scene_momentum:<kind> where kind is one of those five identifiers. "
            "If narration_obligations.scene_momentum_due is true, this turn MUST include a momentum beat and MUST include that tag."
        ),
        'Use campaign and world state to keep political and strategic continuity.',
        'Avoid generic dramatic filler and repeated warning phrases. Make NPC replies specific to the speaker and current situation.',
        'Forbidden generic phrases are disallowed: "In this city...", "Times are tough...", "Trust is hard to come by...", "You\'ll need to prove yourself..." — rewrite into specific names/locations/events.',
        'QUESTION RESOLUTION RULE (HARD RULE): Every direct player question MUST be answered explicitly before any additional dialogue. Structure: (1) Direct answer (first sentence), (2) Optional elaboration, (3) Optional hook. The GM/NPC MUST NOT deflect, generalize, or ask a new question before answering.',
        'If certainty is incomplete, classify the uncertainty with response_policy.uncertainty.categories and response_policy.uncertainty.sources, then compose it from response_policy.uncertainty.answer_shape: known_edge, unknown_edge, next_lead.',
        'Ground uncertainty with response_policy.uncertainty.context_inputs: uncertainty_hint.turn_context, uncertainty_hint.speaker, and uncertainty_hint.scene_snapshot.',
        'If uncertainty_hint.speaker.role is npc, keep the reply attributable to that NPC and limited to what they could plausibly know, hear, point to, or direct the player toward.',
        'If there is no active NPC speaker, keep uncertainty in diegetic narrator voice but anchor it to visible scene circumstances rather than generic omniscient wording.',
        'If social_intent_class remains social_exchange on an NPC-directed question, keep uncertainty speaker-grounded (npc_ignorance) instead of drifting into scene ambiguity.',
        'Frame uncertainty as world-facing limits only: who knows, what can be seen, what distance, darkness, rumor, missing witnesses, or incomplete clues prevent right now.',
        'Vary sentence count and cadence naturally; do not stamp the same three-sentence rhythm onto every uncertain answer.',
        'If no strong next lead exists, choose the strongest visible handle already in scene rather than giving generic investigative advice.',
        'PERCEPTION / INTENT ADJUDICATION RULE (HARD RULE): When the player asks for behavioral insight (e.g., nervous, lying, controlled), choose ONE dominant state (not mixed), give 1–2 concrete observable tells, and optionally map to a skill interpretation (Sense Motive, etc.). Failure: "mix of"/"seems like both" or pure emotional summary with no cues.',
        'If the player meaningfully moves to a new location, you may provide a new_scene_draft and/or activate_scene_id.',
        'If the player meaningfully changes the world, you may provide world_updates.',
        'If the player text implies a clear mechanical action, suggested_action may be filled for UI assistance, but narration remains primary.',
        'When interaction_continuity has an active target, treat that NPC as the default conversational counterpart.',
        'Non-addressed NPCs should not casually interject; if they interrupt, present it as a notable event with scene justification.',
        'If conversation_privacy or player_position_context implies private exchange (for example lowered_voice), reduce casual eavesdropping/interjection unless scene facts justify otherwise.',
        'Follow authoritative engine state for who is present, player positioning, scene transitions, and check outcomes; narrate outcomes without inventing structured results.',
        'Treat player input as an action declaration: default to third-person phrasing and preserve the user\'s expression format instead of rewriting it.',
        'Quoted in-character dialogue is valid inside an action declaration (for example: Galinor says, "Keep your voice down."); do not treat the quote alone as the entire action when surrounding action context exists.',
        'Follow narration_obligations as output requirements only: they shape wording and focus, but never grant authority to mutate state or decide mechanics.',
        'If narration_obligations.is_opening_scene is true, establish immediate environment plus actionable social/world hooks the player can engage now (see opening_narration_obligations, narrative_plan.scene_opening when present, and opening_scene_realization.contract narration_basis_visible_facts for diegetic first-shot shape).',
        'If narration_obligations.active_npc_reply_expected is true, complete the active NPC\'s substantive in-turn reply now unless a pending engine check prompt already takes precedence, or authoritative state indicates refusal/evasion/interruption/inability.',
        'If narration_obligations.should_answer_active_npc is true, prioritize the active interlocutor\'s reply and the immediate exchange over general scene recap.',
        'Use narration_obligations.active_npc_reply_kind as a compact reply-shape hint (answer, explanation, reaction, refusal).',
        'If narration_obligations.active_npc_reply_kind is refusal, make it substantive (clear boundary, brief reason, redirect, or consequence) rather than empty stalling.',
        'If the player asks a direct question, answer concretely (name, place, fact, or direction); if certainty is incomplete, provide the best grounded partial answer and state uncertainty in-character through witnesses, conditions, rumor, access, or incomplete observation; do not repeat prior information.',
        'NPC response contract: when an NPC is asked a question, include at least one of: (a) a specific person/place/faction, (b) a concrete next step the player can take, (c) directly usable info (time/location/condition/requirement). If the NPC lacks full information, give partial specifics or direct the player to a concrete source.',
        'When answering a player question, give a direct answer first. Do not replace the answer with narrative description.',
        'Use turn_summary and mechanical_resolution as primary narration anchors; treat player_input as supporting evidence for disambiguation, not as the sentence structure to mirror.',
        "Do not restate or paraphrase the player's input. Always continue forward with new information.",
        "Do not repeat the player's spoken line. React to it instead.",
        'If narration_obligations.avoid_input_echo or narration_obligations.avoid_player_action_restatement is true, do not restate or lightly paraphrase player_input (for example, "Galinor asks...") unless wording is required to disambiguate the target, quote, or procedural request.',
        'If narration_obligations.prefer_structured_turn_summary is true, continue from resolved world state, scene advancement, and NPC intent/reply obligations rather than narrating that "the player asks/says X."',
        'Keep the narration to 1-4 concise paragraphs.',
        mode_instruction,
    ]

    _opening_contract = opening_scene_export.get("contract") if isinstance(opening_scene_export, dict) else None
    if (
        narration_obligations.get("is_opening_scene")
        and isinstance(_opening_contract, dict)
        and _opening_contract.get("narration_basis_visible_facts") is not None
    ):
        merge_opening_instructions(instructions, contract=_opening_contract)

    if social_authority:
        _skip_instr = (
            "SCENE MOMENTUM RULE",
            "uncertainty_hint",
            "response_policy.uncertainty",
            "classify the uncertainty",
            "Ground uncertainty with",
            "Frame uncertainty as",
            "If uncertainty_hint",
        )
        instructions = [line for line in instructions if not any(m in line for m in _skip_instr)]
        instructions.append(
            "SOCIAL INTERACTION LOCK: Do not use ambient scene narration, scene-wide uncertainty pools, or momentum/pressure "
            "beats as the main voice. The active interlocutor must carry this turn (substantive reply, reaction, or refusal)."
        )

    # Legacy follow-up pressure is derived from recent_log (a continuity proxy). For CTIR-attached turns,
    # prompt_context must not invent continuity/progression signals from logs when the plan is missing or when
    # the plan is verified continuation (C1-B ownership).
    _ctir_plan_missing = bool(ctir_obj is not None and narrative_plan is None)
    if is_verified_ctir_continuation or _ctir_plan_missing:
        follow_up_log_pressure = None
        ap_for_prompt: dict[str, Any] = {}
    else:
        follow_up_log_pressure = _compute_follow_up_pressure(recent_log_compact, user_text)
        ap_for_prompt = _answer_pressure_followup_details(
            player_input=str(user_text or ""),
            recent_log_compact=list(recent_log_compact or []),
            narration_obligations=narration_obligations,
            session_view=session_view,
            answer_completeness=None,
        )
        if follow_up_log_pressure is None and ap_for_prompt.get("answer_pressure_followup_detected"):
            follow_up_log_pressure = _synthetic_follow_up_pressure_from_log(
                recent_log_compact, str(user_text or "")
            )
        if social_authority and not ap_for_prompt.get("answer_pressure_followup_detected"):
            follow_up_log_pressure = None

    active_topic_anchor = explicit_player_topic_anchor_state(str(user_text or ""))

    active_npc_id: str | None = None
    if isinstance(public_scene, Mapping):
        if isinstance(interlocutor_export, dict):
            _nid = str(interlocutor_export.get("npc_id") or "").strip()
            if _nid:
                active_npc_id = _nid
        if active_npc_id is None:
            _tid = session_view.get("active_interaction_target_id")
            if _tid and str(_tid).strip():
                active_npc_id = str(_tid).strip()

    lead_context = build_authoritative_lead_prompt_context(
        session=session,
        world=world,
        public_scene=public_scene,
        runtime=runtime,
        recent_log=recent_log_compact,
        active_npc_id=active_npc_id,
    )
    interlocutor_lead_context = build_interlocutor_lead_discussion_context(
        session=session,
        world=world,
        public_scene=public_scene,
        recent_log=recent_log_compact,
        active_npc_id=active_npc_id,
    )
    interlocutor_lead_behavior_hints = deterministic_interlocutor_lead_behavior_hints(
        interlocutor_lead_context
    )
    from_leads_pressure = lead_context.get("follow_up_pressure_from_leads")
    if not isinstance(from_leads_pressure, dict):
        from_leads_pressure = {
            "has_pursued": False,
            "has_stale": False,
            "npc_has_relevant": False,
            "has_escalated_threat": False,
            "has_newly_unlocked": False,
            "has_supersession_cleanup": False,
        }

    if follow_up_log_pressure:
        instructions = list(instructions) + [
            (
                "FOLLOW-UP ESCALATION RULE (HARD RULE): The player is pressing the same topic again (see follow_up_pressure). "
                "Do NOT recycle the same core lead from the previous answer. Escalate by doing AT LEAST TWO of the following: "
                "(1) add one new concrete detail (time, place, condition, count, or observable), "
                "(2) introduce a named person/place/faction/witness tied to the topic (with an in-world source), "
                "(3) narrow the boundary of the unknown (what is ruled out; what is now most likely; what would confirm it), "
                "(4) produce a more actionable immediate next step that uses the new detail. "
                "Preserve uncertainty, but uncertainty must evolve. Preserve speaker grounding."
            ),
            "Allowed repetition: one short anchor clause for continuity. Not allowed: re-stating the same underlying lead as the whole answer.",
        ]

    lead_instr: List[str] = [
        "LEAD REGISTRY (authoritative slice): Use top-level lead_context only as supplied—do not invent leads, facts, or journal summaries. "
        "Turn compact rows into light, actionable nudges (what could matter next), not recap.",
    ]
    # Quarantine progression guidance: for verified CTIR continuation, plan-owned anchors/pressures are the
    # only continuation progression source. Lead registry remains transportable support context, but must not
    # become a substitute continuation planner.
    if is_verified_ctir_continuation or (ctir_obj is not None and narrative_plan is None):
        instructions = list(instructions) + [
            "CTIR CONTINUATION PROGRESSION (HARD RULE): When CTIR is attached, treat `narrative_plan` "
            "(scene_anchors, active_pressures, required_new_information, narrative_mode_contract) as the sole "
            "continuation-progression guide when it is present. If the plan is missing, do not substitute "
            "recent_log, public_scene recap, or lead_context as a replacement continuity plan.",
            *lead_instr,
        ]
    else:
        lead_instr = lead_instr + [
            "When the player is clearly continuing an existing investigation thread, prefer lead_context.currently_pursued_lead as the primary thread anchor when it is non-null.",
            "When interaction_continuity names an active NPC, use lead_context.npc_relevant_leads to tie the exchange to registry-linked threads that list that NPC—without fabricating details beyond those rows.",
            "Use lead_context.urgent_or_stale_leads to surface unattended time pressure or stale threads as diegetic tension or reminders—only as implied by those rows; do not invent urgency.",
            "Use lead_context.recent_lead_changes for continuity with the latest registry state shifts (status, next_step, touches)—do not restate full buckets or dump all leads.",
            "follow_up_pressure.from_leads is boolean-only: has_pursued, has_stale, npc_has_relevant, has_escalated_threat, has_newly_unlocked, has_supersession_cleanup. Do not treat it as prose; use the matching lead_context lists/objects for specifics.",
            "If follow_up_pressure.from_leads.has_pursued is true, bias narration toward continuing that pursued thread when it fits the player's action.",
            "If follow_up_pressure.from_leads.has_stale is true, you may surface reminder, pressure, or unattended-thread beats that fit the scene—without inventing facts beyond lead_context.",
            "If follow_up_pressure.from_leads.npc_has_relevant is true, you may let the active NPC exchange reflect relevance to those threads—within knowledge_scope and without inventing registry facts.",
            "If follow_up_pressure.from_leads.has_escalated_threat is true, bias tension beats toward unattended threat rows in lead_context (escalation fields)—without inventing facts beyond those rows.",
            "If follow_up_pressure.from_leads.has_newly_unlocked is true, you may acknowledge a thread becoming available or unblocked when it fits the scene—grounded in unlocked_by_lead_id / recent_lead_changes only.",
            "If follow_up_pressure.from_leads.has_supersession_cleanup is true, avoid treating superseded obsoleted threads as primary pressure unless the player returns to them; prefer current non-terminal rows.",
        ]
        instructions = list(instructions) + lead_instr

    if social_authority and active_topic_anchor.get("active"):
        instructions = list(instructions) + [
            "ACTIVE TOPIC ANCHOR (HARD RULE): The player explicitly corrected or narrowed the conversational subject "
            "this turn. Answer that subject first in the active interlocutor's voice. Do not pivot back to "
            "lead_context.currently_pursued_lead, urgent_or_stale_leads, or unrelated registry mystery threads "
            "for convenience. Registry salience alone is not sufficient to override the clarified subject. "
            "A redirect is allowed only after a substantive answer—or honest refusal, evasion, or ignorance—on the "
            "asked subject.",
        ]

    if social_authority:
        if follow_up_log_pressure is not None:
            follow_up_pressure = {**follow_up_log_pressure, "from_leads": dict(from_leads_pressure)}
        else:
            follow_up_pressure = {"from_leads": dict(from_leads_pressure)}
    elif follow_up_log_pressure is not None:
        follow_up_pressure = {**follow_up_log_pressure, "from_leads": dict(from_leads_pressure)}
    elif any(from_leads_pressure.values()):
        follow_up_pressure = {"from_leads": dict(from_leads_pressure)}
    else:
        follow_up_pressure = None

    naming_line: str | None = None
    if interlocutor_export and str(interlocutor_export.get("npc_id") or "").strip():
        nid = str(interlocutor_export.get("npc_id") or "").strip()
        dn = str(interlocutor_export.get("display_name") or "").strip()
        naming_line = (
            f"NAMING CONTINUITY (engine): Active interlocutor canonical id is {nid!r}"
            + (f", display name {dn!r}" if dn else "")
            + ". Keep this name/title stable across turns unless engine state changes it; "
            "do not regress to generic unnamed incidental-crowd wording for this id."
        )
        instructions = list(instructions) + list(answer_style_hints_list) + [naming_line]

    soc_profile = build_social_interlocutor_profile(interlocutor_export)

    # Presentation-only scene id for speaker contract packaging (not narrative_mode / plan / CTIR).
    scene_id_for_speaker = scene_pub_id or (
        str((session.get("scene_state") or {}).get("active_scene_id") or "").strip()
        if isinstance(session, dict)
        else ""
    )
    speaker_selection = build_speaker_selection_contract(
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        scene_id_for_speaker,
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
    )
    tone_escalation_build_error: str | None = None
    try:
        tone_escalation_contract = build_tone_escalation_contract(
            session=session if isinstance(session, dict) else None,
            world=world if isinstance(world, dict) else None,
            scene_id=str(scene_id_for_speaker or "").strip(),
            resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
            speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
            scene_state_anchor_contract=scene_state_anchor_contract if isinstance(scene_state_anchor_contract, dict) else None,
            narration_visibility=visibility_contract if isinstance(visibility_contract, dict) else None,
            recent_log=list(recent_log_for_prompt or []),
        )
    except Exception as exc:
        tone_escalation_build_error = f"{type(exc).__name__}: {exc}"
        tone_escalation_contract = build_tone_escalation_contract(
            session=None,
            world=None,
            scene_id="",
            resolution=None,
            speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
            scene_state_anchor_contract=None,
            narration_visibility=None,
            recent_log=None,
        )
        tone_escalation_contract["scene_id"] = str(scene_id_for_speaker or "").strip()
        tone_escalation_contract["debug_reason"] = (
            f"prompt_context_tone_escalation_build_failed:{type(exc).__name__}"
        )
        _te_df = tone_escalation_contract.get("debug_flags")
        tone_escalation_contract["debug_flags"] = {
            **(_te_df if isinstance(_te_df, dict) else {}),
            "exception": str(exc),
        }
    response_policy["tone_escalation"] = tone_escalation_contract
    _te_dbg = _tone_escalation_prompt_debug_anchor(tone_escalation_contract)
    if tone_escalation_build_error is not None:
        _te_dbg = {**_te_dbg, "build_error": tone_escalation_build_error[:500]}
    prompt_debug_anchor["tone_escalation"] = _te_dbg

    _psid = str((speaker_selection or {}).get("primary_speaker_id") or "").strip()
    _allowed_ids = [
        str(x).strip()
        for x in ((speaker_selection or {}).get("allowed_speaker_ids") or [])
        if isinstance(x, str) and str(x).strip()
    ]
    _switch_ok = bool((speaker_selection or {}).get("speaker_switch_allowed"))
    _gff = bool((speaker_selection or {}).get("generic_fallback_forbidden"))
    _labels_preview = ", ".join(
        repr(x) for x in ((speaker_selection or {}).get("forbidden_fallback_labels") or [])[:8]
    )
    _speaker_contract_instr: List[str] = [
        "SPEAKER SELECTION CONTRACT (HARD RULE): Obey the top-level `speaker_selection` object. "
        "When `primary_speaker_id` is non-null, treat that NPC as the default voice for substantive quoted dialogue "
        "and in-character answers for this turn.",
    ]
    if not _allowed_ids:
        _speaker_contract_instr.append(
            "SPEAKER SELECTION CONTRACT (HARD RULE): `allowed_speaker_ids` is empty — do not attribute quoted speech to any NPC; "
            "remain narrator-neutral. Do not invent incidental speakers or crowd voices to answer for a missing interlocutor."
        )
    else:
        _speaker_contract_instr.append(
            f"SPEAKER SELECTION CONTRACT (HARD RULE): Only these NPC ids may carry quoted NPC dialogue this turn: {_allowed_ids!r}. "
            "Do not give spoken lines to anyone else (including newly invented characters)."
        )
        if not _switch_ok:
            _speaker_contract_instr.append(
                "SPEAKER SELECTION CONTRACT (HARD RULE): `speaker_switch_allowed` is false — do not move the substantive reply "
                "to a different NPC mid-turn. If `interruption_allowed` is true, a single explicit scene-event interruption may cut "
                "off the current speaker per `interruption_requires_scene_event`."
            )
    if _gff:
        _speaker_contract_instr.append(
            "SPEAKER SELECTION CONTRACT (HARD RULE): `generic_fallback_forbidden` is true — do not use generic unnamed stand-ins "
            f"(for example {_labels_preview}) as the answer source."
        )
    instructions = list(instructions) + _speaker_contract_instr

    # Machine-readable boundary only; exhaustive checks live outside this module (e.g. emission gate).
    # narration_visibility= full ``build_narration_visibility_contract`` snapshot (not the slim prompt export).
    narrative_authority_contract = build_narrative_authority_contract(
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
        narration_visibility=visibility_contract if isinstance(visibility_contract, dict) else None,
        scene_state_anchor_contract=scene_state_anchor_contract if isinstance(scene_state_anchor_contract, dict) else None,
        speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
        session_view=session_view if isinstance(session_view, dict) else None,
    )
    response_policy["narrative_authority"] = narrative_authority_contract
    response_policy["forbid_unjustified_narrative_authority"] = True

    prompt_debug_anchor["narrative_authority"] = {
        "enabled": narrative_authority_contract.get("enabled"),
        "authoritative_outcome_available": narrative_authority_contract.get("authoritative_outcome_available"),
        "success_state_available": narrative_authority_contract.get("success_state_available"),
        "mechanical_result_available": narrative_authority_contract.get("mechanical_result_available"),
        "forbid_unresolved_outcome_assertions": narrative_authority_contract.get(
            "forbid_unresolved_outcome_assertions"
        ),
        "forbid_hidden_fact_assertions": narrative_authority_contract.get("forbid_hidden_fact_assertions"),
        "forbid_npc_intent_assertions_without_basis": narrative_authority_contract.get(
            "forbid_npc_intent_assertions_without_basis"
        ),
        "preferred_deferral_order": list(narrative_authority_contract.get("preferred_deferral_order") or []),
    }

    follow_surface = session.get("follow_surface") if isinstance(session, dict) else None
    anti_railroading_contract = build_anti_railroading_contract(
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
        narration_obligations=narration_obligations,
        session_view=session_view if isinstance(session_view, dict) else None,
        scene_state_anchor_contract=scene_state_anchor_contract if isinstance(scene_state_anchor_contract, dict) else None,
        speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
        narrative_authority_contract=narrative_authority_contract if isinstance(narrative_authority_contract, dict) else None,
        prompt_leads=lead_context,
        active_pending_leads=active_pending_leads,
        follow_surface=follow_surface,
        player_text=str(user_text or ""),
    )
    response_policy["anti_railroading"] = anti_railroading_contract

    prompt_debug_anchor["anti_railroading"] = {
        "enabled": bool(anti_railroading_contract.get("enabled")),
        "surfaced_lead_count": len(anti_railroading_contract.get("surfaced_lead_ids") or []),
        "allow_directional_language_from_resolved_transition": anti_railroading_contract.get(
            "allow_directional_language_from_resolved_transition"
        ),
        "allow_exclusivity_from_authoritative_resolution": anti_railroading_contract.get(
            "allow_exclusivity_from_authoritative_resolution"
        ),
        "allow_commitment_language_when_player_explicitly_committed": anti_railroading_contract.get(
            "allow_commitment_language_when_player_explicitly_committed"
        ),
    }

    interaction_for_rtc = (
        interaction_context_snapshot_from_ctir_semantics(interaction_sem)
        if ctir_obj is not None
        else response_type_context_snapshot(session if isinstance(session, dict) else None)
    )
    _rtc_policy_early = response_policy.get("response_type_contract")
    _rtc_authoritative, _rtc_authoritative_source = _resolve_authoritative_response_type_contract_impl(
        {"response_policy": {"response_type_contract": _rtc_policy_early}} if isinstance(_rtc_policy_early, dict) else None,
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
        session=session if isinstance(session, dict) else None,
    )
    if isinstance(_rtc_authoritative, dict):
        rtc_for_social_structure = _rtc_authoritative
        rtc_source = _rtc_authoritative_source or "response_policy"
        response_policy["response_type_contract"] = copy.deepcopy(_rtc_authoritative)
    elif isinstance(_rtc_policy_early, dict):
        rtc_for_social_structure = _rtc_policy_early
        rtc_source = "response_policy"
    else:
        rtc_peeked = peek_response_type_contract_from_resolution(resolution_sem)
        rtc_source = "resolution.metadata" if rtc_peeked is not None else "derived"
        rtc_for_social_structure = rtc_peeked or derive_response_type_contract(
            segmented_turn=None,
            normalized_action=None,
            resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
            interaction_context=interaction_for_rtc,
            directed_social_entry=None,
            route_choice=None,
            raw_player_text=str(user_text or ""),
        ).to_dict()
    _rtc_required = str((rtc_for_social_structure or {}).get("required_response_type") or "").strip().lower()

    _plan_nm = (
        str((narrative_plan or {}).get("narrative_mode") or "").strip()
        if isinstance(narrative_plan, dict)
        else None
    )
    _ao_ok, _ao_reasons = validate_action_outcome_plan_contract(
        narrative_plan if isinstance(narrative_plan, dict) else None,
        response_type_required=_rtc_required or None,
    )
    # Structural action_outcome narration lane follows ``narrative_mode`` only (plan slice may
    # exist with ``present: false`` under continuation; response_type may still tag emission).
    _needs_ao_contract = _plan_nm == "action_outcome"
    # Fail-closed only on the CTIR-backed narration seam; legacy no-CTIR prompts keep prior resolution fallbacks.
    action_outcome_narration_blocked = bool(ctir_obj is not None and _needs_ao_contract and not _ao_ok)
    _ao_src_kind = None
    _ao_deriv_codes: List[str] = []
    if isinstance(narrative_plan, dict):
        _ao_blk = narrative_plan.get("action_outcome")
        if isinstance(_ao_blk, Mapping):
            _ao_src_kind = _ao_blk.get("source_kind")
            _dc = _ao_blk.get("derivation_codes")
            if isinstance(_dc, list):
                _ao_deriv_codes = [str(x) for x in _dc[:48] if isinstance(x, str) and str(x).strip()]
    prompt_debug_anchor["action_outcome_contract"] = {
        "action_outcome_plan_present": bool(
            isinstance(narrative_plan, dict) and isinstance(narrative_plan.get("action_outcome"), Mapping)
        ),
        "action_outcome_plan_valid": bool(_ao_ok),
        "action_outcome_plan_failure_reasons": list(_ao_reasons),
        "action_outcome_source_kind": _ao_src_kind,
        "action_outcome_derivation_codes": _ao_deriv_codes,
        "required_response_type": _rtc_required or None,
    }
    if action_outcome_narration_blocked:
        _ao_audit = {
            "action_outcome_contract_blocked": True,
            "semantic_bypass_blocked": True,
            "action_outcome_plan_failure_reasons": list(_ao_reasons),
        }
        if isinstance(narration_seam_audit, dict):
            narration_seam_audit = {**narration_seam_audit, **_ao_audit}
        else:
            narration_seam_audit = _ao_audit

    turn_summary_struct = _build_turn_summary(
        user_text,
        resolution_sem,
        intent_sem,
        narrative_plan_mode=_plan_nm,
        action_outcome_contract_blocked=action_outcome_narration_blocked,
    )
    _ts_parts = [
        str(turn_summary_struct.get("action_descriptor") or "").strip(),
        str(turn_summary_struct.get("resolution_kind") or "").strip(),
    ]
    _labels_ts = turn_summary_struct.get("intent_labels")
    if isinstance(_labels_ts, list) and _labels_ts:
        _ts_parts.append(", ".join(str(x).strip() for x in _labels_ts if isinstance(x, str) and str(x).strip()))
    turn_summary_for_contract = " ".join(p for p in _ts_parts if p).strip() or None

    scene_summary_for_contract: str | None = None
    if isinstance(public_scene, dict):
        scene_summary_for_contract = str(public_scene.get("summary") or "").strip() or None
    if not scene_summary_for_contract and isinstance(scene, dict):
        _inner = scene.get("scene")
        if isinstance(_inner, dict):
            scene_summary_for_contract = str(_inner.get("summary") or "").strip() or None

    session_view_for_separation: Dict[str, Any] = dict(session_view)
    if isinstance(world_state_view, dict):
        for _k in (
            "compressed_world_pressures",
            "world_pressures",
            "ambient_pressures",
            "surfaced_pressures",
            "surfaced_leads",
            "prompt_leads",
            "active_pending_leads",
            "leads_for_prompt",
        ):
            if _k in world_state_view and _k not in session_view_for_separation:
                session_view_for_separation[_k] = world_state_view[_k]

    compressed_world_pressures_arg: List[str] | None = None
    if isinstance(campaign, dict):
        _cwp_c = campaign.get("world_pressures")
        if isinstance(_cwp_c, list) and _cwp_c:
            compressed_world_pressures_arg = [
                str(x).strip() for x in _cwp_c if isinstance(x, str) and str(x).strip()
            ][:MAX_WORLD_PRESSURES]
    if compressed_world_pressures_arg is None and isinstance(world_state_view, dict):
        for _k in ("compressed_world_pressures", "world_pressures"):
            _raw_wp = world_state_view.get(_k)
            if isinstance(_raw_wp, list) and _raw_wp:
                compressed_world_pressures_arg = [
                    str(x).strip() for x in _raw_wp if isinstance(x, str) and str(x).strip()
                ][:MAX_WORLD_PRESSURES]
                break

    context_separation_contract = build_context_separation_contract(
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
        player_text=str(user_text or ""),
        session_view=session_view_for_separation,
        scene_envelope=scene if isinstance(scene, dict) else None,
        scene_summary=scene_summary_for_contract,
        turn_summary=turn_summary_for_contract,
        speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
        scene_state_anchor_contract=scene_state_anchor_contract if isinstance(scene_state_anchor_contract, dict) else None,
        narration_visibility=visibility_contract if isinstance(visibility_contract, dict) else None,
        tone_escalation_contract=tone_escalation_contract if isinstance(tone_escalation_contract, dict) else None,
        compressed_world_pressures=compressed_world_pressures_arg,
        prompt_leads=lead_context,
        active_pending_leads=active_pending_leads,
        follow_surface=follow_surface,
    )
    response_policy["context_separation"] = context_separation_contract
    prompt_debug_anchor["context_separation"] = _context_separation_prompt_debug_anchor(context_separation_contract)

    _pfnp_ik = session_view.get("active_interaction_kind")
    player_facing_narration_purity_contract = build_player_facing_narration_purity_contract(
        interaction_kind=str(_pfnp_ik).strip() if isinstance(_pfnp_ik, str) and str(_pfnp_ik).strip() else None,
        debug_inputs={"scene_id": scene_pub_id or None},
    )
    response_policy["player_facing_narration_purity"] = player_facing_narration_purity_contract
    prompt_debug_anchor["player_facing_narration_purity"] = _player_facing_narration_purity_prompt_debug_anchor(
        player_facing_narration_purity_contract
    )

    # Canonical prompt-contract owner path: ``game.prompt_context`` ships this
    # policy in the prompt bundle. The implementation remains delegated to the
    # downstream policy consumer module as compatibility residue only.
    # ``rtc_for_social_structure`` / ``rtc_source`` are resolved earlier (before
    # ``turn_summary``) for action_outcome contract enforcement.
    social_response_structure_contract = build_social_response_structure_contract(
        rtc_for_social_structure,
        debug_inputs={"scene_id": scene_pub_id or None, "response_type_contract_source": rtc_source},
    )
    response_policy["social_response_structure"] = social_response_structure_contract
    prompt_debug_anchor["social_response_structure"] = _social_response_structure_prompt_debug_anchor(
        social_response_structure_contract
    )

    interaction_continuity_contract = build_interaction_continuity_contract(
        session if isinstance(session, dict) else None,
        scene_id=scene_pub_id or None,
        scene_envelope=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
        response_type_contract=rtc_for_social_structure if isinstance(rtc_for_social_structure, dict) else None,
    )
    response_policy["interaction_continuity"] = interaction_continuity_contract
    prompt_debug_anchor["interaction_continuity"] = _interaction_continuity_prompt_debug_anchor(
        interaction_continuity_contract
    )

    _mechanical_for_policy: Dict[str, Any] | None
    if action_outcome_narration_blocked:
        _mechanical_for_policy = {}
    elif _needs_ao_contract and isinstance(narrative_plan, dict) and _ao_ok:
        _mechanical_for_policy = {"action_outcome": narrative_plan.get("action_outcome")}
    else:
        _mechanical_for_policy = resolution if isinstance(resolution, dict) else None

    fallback_behavior_contract = build_fallback_behavior_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        recent_log=recent_log_compact,
        turn_summary=turn_summary_struct,
        # Action-outcome readiness: plan-owned structure only; never raw resolution rescue when blocked.
        mechanical_resolution=_mechanical_for_policy,
        response_type_contract=rtc_for_social_structure if isinstance(rtc_for_social_structure, dict) else None,
        answer_completeness_contract=response_policy.get("answer_completeness"),
        narrative_authority_contract=narrative_authority_contract,
        interaction_continuity_contract=interaction_continuity_contract,
    )
    response_policy["fallback_behavior"] = fallback_behavior_contract
    prompt_debug_anchor["fallback_behavior"] = {
        "enabled": bool(fallback_behavior_contract.get("enabled")),
        "uncertainty_active": bool(fallback_behavior_contract.get("uncertainty_active")),
        "uncertainty_mode": fallback_behavior_contract.get("uncertainty_mode"),
        "uncertainty_sources": list(fallback_behavior_contract.get("uncertainty_sources") or []),
    }

    from game.narrative_authenticity import build_narrative_authenticity_contract

    narrative_authenticity_contract = build_narrative_authenticity_contract(
        response_delta=response_policy.get("response_delta"),
        answer_completeness=response_policy.get("answer_completeness"),
        fallback_behavior=fallback_behavior_contract,
        social_response_structure=social_response_structure_contract,
        response_type_contract=rtc_for_social_structure if isinstance(rtc_for_social_structure, dict) else None,
        follow_up_pressure=follow_up_pressure if isinstance(follow_up_pressure, Mapping) else None,
        recent_log_compact=recent_log_compact,
        player_text=str(user_text or ""),
    )
    response_policy["narrative_authenticity"] = narrative_authenticity_contract
    prompt_debug_anchor["narrative_authenticity"] = _narrative_authenticity_prompt_debug_anchor(
        narrative_authenticity_contract
    )

    _ic_dbg = interaction_continuity_contract.get("debug")
    _ic_dbg_map = _ic_dbg if isinstance(_ic_dbg, dict) else {}
    _source_of_activity_anchor = str(_ic_dbg_map.get("source_of_anchor") or "").strip()
    _vis_ids_raw = visibility_contract.get("visible_entity_ids") if isinstance(visibility_contract, dict) else []
    _active_scene_entity_ids = [
        str(x).strip() for x in (_vis_ids_raw if isinstance(_vis_ids_raw, list) else []) if isinstance(x, str) and str(x).strip()
    ]
    _alias_map = visibility_contract.get("visible_entity_aliases") if isinstance(visibility_contract, dict) else None
    if not isinstance(_alias_map, dict):
        _alias_map = {}
    _re_ent, _re_top, _re_dbg = _extract_explicit_reintroductions(
        str(user_text or ""),
        entity_alias_map=_alias_map,
        topic_anchor_tokens=_memory_window_focus_topic_tokens(active_topic_anchor),
        anchored_interlocutor_id=str(interaction_continuity_contract.get("anchored_interlocutor_id") or ""),
        active_interaction_target_id=str(interaction_continuity_contract.get("active_interaction_target_id") or ""),
    )
    conversational_memory_window = build_conversational_memory_window_contract(
        enabled=True,
        recent_turn_window=6,
        soft_memory_limit=CONVERSATIONAL_MEMORY_SOFT_LIMIT,
        stale_after_turns=18,
        active_scene_entity_ids=_active_scene_entity_ids,
        anchored_interlocutor_id=str(interaction_continuity_contract.get("anchored_interlocutor_id") or ""),
        active_interaction_target_id=str(interaction_continuity_contract.get("active_interaction_target_id") or ""),
        explicit_reintroduced_entity_ids=_re_ent,
        explicit_reintroduced_topics=_re_top,
        selection_debug=dict(_re_dbg) if isinstance(_re_dbg, dict) else {},
        source_of_activity_anchor=_source_of_activity_anchor or "interaction_continuity",
        source_of_recentness="session.turn_counter",
        source_of_reintroductions="player_text+visibility_aliases",
    )
    _mem_cands, _mem_extras = _assemble_conversational_memory_candidates(
        recent_log_for_prompt=list(recent_log_for_prompt or []),
        current_turn=int(session_view.get("turn_counter") or 0),
        runtime_compressed=runtime,
        interlocutor_lead_context=interlocutor_lead_context,
        active_npc_id=active_npc_id,
    )
    selected_conversational_memory = select_conversational_memory_window(
        _mem_cands,
        conversational_memory_window,
        current_turn=int(session_view.get("turn_counter") or 0),
    )
    recent_log_for_payload = _recent_log_payload_from_selected_memory(
        selected_conversational_memory,
        _mem_cands,
        _mem_extras,
    )
    prompt_debug_anchor["conversational_memory"] = {
        "candidate_count": len(_mem_cands),
        "selected_count": len(selected_conversational_memory),
    }
    # Shipped policy mirror for downstream inspection (same object as payload; no second selector).
    response_policy["conversational_memory_window"] = conversational_memory_window
    instructions = list(instructions) + [
        "CONVERSATIONAL MEMORY WINDOW: Treat `selected_conversational_memory` as the bounded active conversational thread for this turn—prioritize it over older or omitted chat material. "
        "Do not revive stale side threads unless the player explicitly re-grounds them (see `conversational_memory_window.explicit_reintroduced_*`). "
        "Omitted older material is background only—not an active unresolved obligation.",
    ]

    _narrative_authority_instr = [
        "NARRATIVE AUTHORITY (POLICY): Obey response_policy.narrative_authority for assertion boundaries; deterministic enforcement is authoritative. "
        "Do not assert unresolved outcomes as settled fact. "
        "Do not assert hidden causes or hidden truths as confirmed without basis in published visible/engine state. "
        "Do not assert NPC motives or intentions as fact without explicit basis. "
        "When certainty is unavailable, defer via a roll/check request, bounded uncertainty, or conditional/branch framing. "
        "Observable visible cues are allowed; omniscient conclusions are not.",
    ]
    _fallback_behavior_instr = [
        "FALLBACK BEHAVIOR (MANDATORY): When `fallback_behavior.uncertainty_active` is true, do not invent certainty and do not fabricate authority. "
        "Either give a bounded partial answer or, only when `fallback_behavior.allowed_behaviors.ask_clarifying_question` is true and a partial would mislead, ask one brief clarifying question. "
        "Keep uncertainty diegetic, state the strongest grounded known edge plus the unknown edge, and offer a natural next lead when possible.",
    ]
    _tone_escalation_instr = [
        "TONE / ESCALATION (POLICY): Obey response_policy.tone_escalation for interpersonal intensity; that object is the authority—do not override it from general scene mood. "
        "Do not introduce hostility, explicit threats, physical violence, or combat initiation unless the contract's allowances and published state support it. "
        "When a higher escalation tier is not allowed, prefer guarded refusal, scrutiny, urgency, consequence framing, or concrete social or procedural pressure. "
        "Topic pressure or conversational friction alone does not justify threats or violence.",
    ]
    _anti_railroading_instr = [
        "ANTI-RAILROADING (POLICY): Obey top-level anti_railroading_contract and response_policy.anti_railroading. "
        "Do not decide the player character's action for them. "
        "Do not turn a surfaced lead into a required path: leads may create options, pressure, urgency, or opportunities; "
        "they do not create main-plot gravity, destiny, or a single mandatory thread. "
        "Avoid mandatory-path phrasing such as 'only way,' 'must go,' or 'the story pulls you' unless authoritative state "
        "truly supports it (see allow_exclusivity_from_authoritative_resolution and allow_directional_language_from_resolved_transition on the contract). "
        "Differentiate: HARD WORLD CONSTRAINT — state a fixed situation or barrier plainly without selecting the player's next move; "
        "SALIENT LEAD — highlight as option, rumor, pressure, or opportunity, not fate; "
        "FORCED PLAYER DIRECTION — never narrate the PC's decision, compulsion to one destination, or one true path without basis. "
        "A hard world constraint may narrow what is possible; it must not auto-pick the player's response. "
        "Preserve momentum through consequences, openings, reactions, and constraints—not by seizing player action. "
        "Precedence (compact): player agency outranks momentum polish; authoritative constraints may narrow possibilities but must not choose the player's next move; "
        "surfaced leads may be highlighted without being made mandatory. "
        "Directional language is not globally banned—only unjustified forced direction. "
        "When anti_railroading_contract.allow_commitment_language_when_player_explicitly_committed is true, narration that follows "
        "the player's explicit commitment in player_input (movement or intent they stated) is allowed and expected where appropriate.",
    ]
    _context_separation_instr = [
        "CONTEXT SEPARATION (POLICY): Obey response_policy.context_separation for ambient world pressure versus local interaction focus; deterministic enforcement uses that shipped object. "
        "Keep the current interaction intent primary: answer or react to the local exchange first. "
        "Ambient background pressure may briefly color wording or add an optional hook; it must not replace the substantive reply, hijack topic, or substitute vague instability for a direct answer. "
        "Background tension alone must not harden interpersonal tone beyond what tone_escalation already allows. "
        "Letting broader ambient pressure lead the reply is allowed only when the player text, scene framing, a resolved consequence, or published pressure inputs make that focus immediately relevant—not from generic scene mood alone.",
    ]
    _player_facing_narration_purity_instr = [
        "PLAYER-FACING NARRATION PURITY (POLICY): Obey response_policy.player_facing_narration_purity; deterministic enforcement uses that shipped object. "
        "Speak only in player-facing diegetic prose. "
        "Do not expose internal consequence/opportunity labels, planner headings, or engine-facing scaffolding as narration. "
        "Do not present action coaching, prompts, or engine/UI guidance as if it were in-world text. "
        "Do not mention exits or choices as menu labels (for example 'the exit labeled …', 'your options are …', or bulleted/numbered choice lists). "
        "When branching paths exist, render them as what the character can see, hear, or infer in the moment—not as explicit instructions to the player.",
    ]
    _anchoring_polish_instr = [
        "SCENE ANCHORING (POLICY): After context separation and narration-purity constraints, keep grounding tight: use scene_state_anchor_contract tokens when tightening wording; do not use anchoring to smuggle extra ambient pressure.",
    ]
    _social_response_structure_instr = [
        "SOCIAL RESPONSE STRUCTURE (POLICY): When response_policy.social_response_structure.enabled is true, obey that object; deterministic enforcement will use it later. "
        "NPC/social lines should sound spoken, not essay-like: answer first, then at most one short supporting detail if needed; avoid stacked explanatory clauses. "
        "Brief action beats are allowed; keep quoted speech primary. Uncertainty or refusal stays conversational and in-world. "
        "No bullet-like or numbered-list dialogue.",
    ]
    _narrative_authenticity_instr = [
        "NARRATIVE AUTHENTICITY (POLICY): Obey response_policy.narrative_authenticity. "
        "Keep narrator-color beats from being pasted into quoted speech; at most one short continuity anchor if needed. "
        "On follow-up pressure turns, change stance, detail, uncertainty boundary, reaction, or next step—without inventing facts. "
        "Avoid generic non-answers when a substantive or bounded-partial reply is available; when fallback_behavior.uncertainty_active is true, brevity and honest limits override polish. "
        "When rumor_realism applies (see trace.rumor_turn_active), do not recycle recent narration or scene setup as quoted rumor without a hearsay realism signal (source limit, uncertainty, bias, or net-new detail).",
    ]
    _policy_tail: List[str] = (
        list(_tone_escalation_instr)
        + _narrative_authority_instr
        + _fallback_behavior_instr
        + _anti_railroading_instr
        + _context_separation_instr
        + _player_facing_narration_purity_instr
        + _anchoring_polish_instr
        + _narrative_authenticity_instr
    )
    if social_response_structure_contract.get("enabled"):
        _policy_tail = list(_policy_tail) + _social_response_structure_instr

    _np_for_mode = narrative_plan if isinstance(narrative_plan, dict) else None
    _pnm = str(_np_for_mode.get("narrative_mode") or "").strip() if isinstance(_np_for_mode, dict) else ""
    narrative_mode_instruction_lines = _build_narrative_mode_instructions(
        narrative_mode_contract=(
            narrative_plan.get("narrative_mode_contract") if isinstance(narrative_plan, dict) else None
        ),
        response_policy=response_policy,
        narration_obligations=narration_obligations,
        resolution_sem=resolution_sem if isinstance(resolution_sem, dict) else None,
        narrative_plan_present=_np_for_mode is not None,
        plan_narrative_mode=_pnm or None,
    )
    prompt_debug_anchor["narrative_mode_instructions"] = _narrative_mode_instruction_prompt_debug(
        narrative_plan.get("narrative_mode_contract") if isinstance(narrative_plan, dict) else None,
        instruction_lines=narrative_mode_instruction_lines,
        narrative_plan_present=_np_for_mode is not None,
        plan_narrative_mode=_pnm or None,
    )
    instructions = list(instructions) + list(narrative_mode_instruction_lines) + _policy_tail
    if action_outcome_narration_blocked:
        _ao_codes = "|".join(str(x) for x in (_ao_reasons or [])[:16])
        instructions = list(instructions) + [
            "OPERATOR / AUDIT — ACTION_OUTCOME CONTRACT: narrative_plan.action_outcome is missing or failed validation. "
            f"Machine-readable codes: {_ao_codes or 'unknown'}. "
            "narration_seam_audit.semantic_bypass_blocked is true for this turn. "
            "Do not narrate resolved mechanics, DCs, rolls, damage, or success from player_input, hints, prompts, or raw resolution text.",
        ]

    use_manual_play_compact = _should_use_manual_play_compact_prompt(
        prompt_profile=prompt_profile,
        narration_obligations=narration_obligations,
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
        uncertainty_hint=eff_uncertainty_hint if isinstance(eff_uncertainty_hint, Mapping) else None,
        follow_up_pressure=follow_up_pressure if isinstance(follow_up_pressure, Mapping) else None,
        active_topic_anchor=active_topic_anchor if isinstance(active_topic_anchor, Mapping) else None,
    )
    public_scene_for_prompt = dict(public_scene) if isinstance(public_scene, dict) else {}
    if narration_obligations.get("is_opening_scene") and isinstance(public_scene_for_prompt, dict):
        public_scene_for_prompt["visible_facts"] = list(visible_facts_export)
    if use_manual_play_compact:
        selected_conversational_memory = list(selected_conversational_memory[:MANUAL_PLAY_COMPACT_MEMORY_LIMIT])
        recent_log_for_payload = _recent_log_payload_from_selected_memory(
            selected_conversational_memory,
            _mem_cands,
            _mem_extras,
        )
        recent_log_for_payload = list(recent_log_for_payload[:MANUAL_PLAY_COMPACT_RECENT_LOG_LIMIT])
        visible_facts_export = list(visible_facts_export[:MANUAL_PLAY_COMPACT_VISIBLE_FACT_LIMIT])
        if isinstance(public_scene_for_prompt.get("visible_facts"), list):
            public_scene_for_prompt["visible_facts"] = list(
                public_scene_for_prompt.get("visible_facts")[:MANUAL_PLAY_COMPACT_VISIBLE_FACT_LIMIT]
            )
        instructions = _compact_manual_play_instructions(
            mode_instruction=mode_instruction,
            narration_obligations=narration_obligations,
            response_policy=response_policy,
            has_active_interlocutor=has_active_interlocutor,
            social_authority=social_authority,
            has_scene_change_context=has_scene_change_context,
            naming_line=naming_line if isinstance(naming_line, str) else None,
            answer_style_hints=list(answer_style_hints_list),
            narrative_plan_present=narrative_plan is not None,
            narrative_mode_instruction_lines=narrative_mode_instruction_lines,
        )
        prompt_debug_anchor["compact_prompt"] = {
            "enabled": True,
            "profile": "manual_play_compact",
            "visible_fact_limit": MANUAL_PLAY_COMPACT_VISIBLE_FACT_LIMIT,
            "selected_memory_limit": MANUAL_PLAY_COMPACT_MEMORY_LIMIT,
            "recent_log_limit": MANUAL_PLAY_COMPACT_RECENT_LOG_LIMIT,
            "selected_memory_count": len(selected_conversational_memory),
            "recent_log_count": len(recent_log_for_payload),
        }
    else:
        prompt_debug_anchor["compact_prompt"] = {
            "enabled": False,
            "profile": "full",
        }

    # Canonical snapshot for retry / gate contract lookup (not authoritative engine state).
    _btp = _bundle_renderer_inputs.get("turn_packet") if isinstance(_bundle_renderer_inputs, dict) else None
    _brt = _bundle_renderer_inputs.get("referent_tracking") if isinstance(_bundle_renderer_inputs, dict) else None
    _bdsp = _bundle_renderer_inputs.get("dialogue_social_plan") if isinstance(_bundle_renderer_inputs, dict) else None
    if ctir_obj is not None and bundle_stamp_ok and isinstance(_btp, dict) and isinstance(_brt, dict):
        _turn_packet = copy.deepcopy(_btp)
        referent_tracking = copy.deepcopy(_brt)
    else:
        _turn_packet = build_turn_packet(
            response_policy=response_policy,
            scene_id=scene_pub_id or None,
            player_text=str(user_text or ""),
            resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
            interaction_continuity=interaction_continuity,
            narration_obligations=narration_obligations,
            last_human_adjacent_continuity=(
                runtime.get("last_human_adjacent_continuity") if isinstance(runtime, dict) else None
            ),
            response_type=rtc_for_social_structure if isinstance(rtc_for_social_structure, dict) else None,
            sources_used=["prompt_context.build_compressed_narration_context"],
        )
        # Objective #7: single call into referent_tracking owner; visibility remains the narration_visibility *contract* slice.
        _plids_for_referent = pending_lead_ids_from_active_pending(active_pending_leads)
        _session_interaction_for_referent = session_interaction_slice_for_narrative_plan(
            session_view if isinstance(session_view, dict) else None,
            _plids_for_referent,
        )
        referent_tracking = build_referent_tracking_artifact(
            narration_visibility=visibility_contract if isinstance(visibility_contract, dict) else None,
            speaker_selection=speaker_selection if isinstance(speaker_selection, dict) else None,
            interaction_continuity=interaction_continuity_contract if isinstance(interaction_continuity_contract, dict) else None,
            session_interaction=_session_interaction_for_referent if _session_interaction_for_referent else None,
            narrative_plan=narrative_plan if isinstance(narrative_plan, dict) else None,
            turn_packet=_turn_packet if isinstance(_turn_packet, dict) else None,
        )
    if isinstance(_turn_packet, dict):
        _turn_packet["referent_tracking_compact"] = {
            "referent_artifact_version": referent_tracking.get("version"),
            "active_interaction_target": referent_tracking.get("active_interaction_target"),
            "referential_ambiguity_class": referent_tracking.get("referential_ambiguity_class"),
            "ambiguity_risk": referent_tracking.get("ambiguity_risk"),
        }
        _tp_dbg = _turn_packet.get("debug")
        if isinstance(_tp_dbg, dict):
            _turn_packet["debug"] = {
                **_tp_dbg,
                "world_progression": {
                    "changed_nodes_head": list((wp_projection or {}).get("changed_node_ids") or [])[:8],
                    "active_projects_n": len((wp_projection or {}).get("active_projects") or []),
                    "world_clocks_n": len((wp_projection or {}).get("world_clocks") or []),
                },
            }

    projected_narrative_plan = (
        None
        if action_outcome_narration_blocked
        else (
            public_narrative_plan_projection_for_prompt(narrative_plan)
            if isinstance(narrative_plan, dict) and narrative_plan
            else None
        )
    )

    def _validate_projected_answer_exposition_plan(obj: Any) -> str | None:
        if obj is None:
            return "missing"
        if not isinstance(obj, Mapping):
            return "not_mapping"
        for k in ("enabled", "answer_required"):
            if not isinstance(obj.get(k), bool):
                return f"missing_or_bad_bool:{k}"
        if not isinstance(obj.get("facts"), list):
            return "facts_not_list"
        for i, f in enumerate((obj.get("facts") or [])[:48]):
            if not isinstance(f, Mapping):
                return f"fact_not_mapping:{i}"
            if not str(f.get("id") or "").strip():
                return f"fact_missing_id:{i}"
            if not str(f.get("fact") or "").strip():
                return f"fact_missing_fact:{f.get('id')}"
            # Preserve plan-owned metadata; prompt_context must not "fix" these fields.
            for mk in ("source", "visibility", "certainty"):
                if not str(f.get(mk) or "").strip():
                    return f"fact_missing_meta:{mk}:{f.get('id')}"
        for req in ("constraints", "voice", "delivery"):
            if not isinstance(obj.get(req), Mapping):
                return f"missing_{req}"
        return None

    aep = (
        projected_narrative_plan.get("answer_exposition_plan")
        if isinstance(projected_narrative_plan, Mapping)
        else None
    )
    aep_err = _validate_projected_answer_exposition_plan(aep)
    aep_valid = aep_err is None
    ac_policy = (
        response_policy.get("answer_completeness")
        if isinstance(response_policy, dict) and isinstance(response_policy.get("answer_completeness"), Mapping)
        else {}
    )
    answer_required = bool((ac_policy or {}).get("answer_required"))
    prompt_debug_anchor["answer_exposition_plan_projection"] = {
        "present": aep is not None,
        "valid": bool(aep_valid),
        "validation_error": aep_err,
        "answer_required": bool(answer_required),
        "sourced_from": "public_narrative_plan_projection_for_prompt",
    }

    if isinstance(response_policy, dict) and isinstance(ac_policy, dict):
        # Mirror plan-owned answer facts into the shipped response-policy surface for downstream inspection.
        ac_policy["answer_exposition_plan"] = copy.deepcopy(aep) if aep_valid else None
        if not aep_valid:
            ac_policy["answer_exposition_plan_validation_error"] = aep_err
        response_policy["answer_completeness"] = ac_policy

    if answer_required and not aep_valid:
        # Visible seam: answer was required but the plan-owned answer facts did not reach the prompt.
        prompt_debug_anchor["answer_exposition_plan_seam"] = {
            "seam_open": True,
            "reason": "answer_required_but_missing_or_invalid_projected_answer_exposition_plan",
            "validation_error": aep_err,
        }

    payload: Dict[str, Any] = {
        'instructions': instructions,
        'dialogue_social_plan': (
            copy.deepcopy(_bdsp)
            if (ctir_obj is not None and bundle_stamp_ok and isinstance(_bdsp, dict))
            else None
        ),
        # Block B: structured transition payload sourced ONLY from narrative_plan.transition_node.
        'transition': copy.deepcopy(transition_payload) if isinstance(transition_payload, dict) else None,
        'narrative_plan': (
            None
            if action_outcome_narration_blocked
            else (
                public_narrative_plan_projection_for_prompt(narrative_plan)
                if isinstance(narrative_plan, dict) and narrative_plan
                else None
            )
        ),
        'speaker_selection': speaker_selection,
        'active_topic_anchor': active_topic_anchor,
        'interaction_continuity': interaction_continuity,
        'active_interlocutor': interlocutor_export,
        'social_context': {
            'interlocutor_profile': soc_profile,
            'answer_style_hints': list(answer_style_hints_list),
        },
        'turn_summary': turn_summary_struct,
        'recent_log': recent_log_for_payload,
        'conversational_memory_window': conversational_memory_window,
        'selected_conversational_memory': selected_conversational_memory,
        'player_input': str(user_text or ''),
        'follow_up_pressure': follow_up_pressure,
        'lead_context': lead_context,
        'interlocutor_lead_context': interlocutor_lead_context,
        'interlocutor_lead_behavior_hints': interlocutor_lead_behavior_hints,
        'response_policy': response_policy,
        'referent_tracking': referent_tracking,
        **(
            {'referent_clause_prompt_hints': h}
            if (h := _project_clause_referent_prompt_hints(referent_tracking if isinstance(referent_tracking, dict) else None))
            else {}
        ),
        'turn_packet': _turn_packet,
        'fallback_behavior': fallback_behavior_contract,
        'uncertainty_hint': eff_uncertainty_hint,
        'narration_obligations': narration_obligations,
        'opening_narration_obligations': (
            opening_scene_export.get("opening_narration_obligations")
            if isinstance(opening_scene_export, dict)
            else None
        ),
        'opening_scene_realization': opening_scene_export if isinstance(opening_scene_export, dict) else opening_realization_none(),
        'opening_inputs_are_curated': bool(opening_inputs_are_curated),
        'opening_selector_source_used': (
            opening_fact_telemetry.get("opening_fact_source_used")
            if isinstance(opening_fact_telemetry, dict)
            else "none"
        ),
        'opening_selector_selected_facts': list(opening_selector_selected_facts),
        'opening_curated_facts': list(opening_selector_selected_facts) if opening_inputs_are_curated else [],
        'opening_fact_telemetry': opening_fact_telemetry,
        'narration_visibility': narration_visibility,
        'scene_state_anchor_contract': scene_state_anchor_contract,
        'anti_railroading_contract': anti_railroading_contract,
        'context_separation_contract': context_separation_contract,
        'player_facing_narration_purity_contract': player_facing_narration_purity_contract,
        'social_response_structure_contract': social_response_structure_contract,
        'interaction_continuity_contract': interaction_continuity_contract,
        'prompt_debug': prompt_debug_anchor,
        'first_mention_contract': first_mention_contract,
        'discoverable_hinting': True,
        # Action-outcome readiness: ship plan ``action_outcome`` only when contract-valid; else seam-closed (no raw rescue).
        'mechanical_resolution': (
            None
            if action_outcome_narration_blocked
            else (
                {"action_outcome": narrative_plan.get("action_outcome")}
                if _needs_ao_contract and isinstance(narrative_plan, dict) and _ao_ok
                else resolution
            )
        ),
        'scene_advancement': scene_advancement,
        'session': session_view,
        'character': {
            'name': str(character.get('name', '') or ''),
            'role': str(campaign.get('character_role', '') or ''),
            'hp': character.get('hp'),
            'ac': character.get('ac'),
            'conditions': character.get('conditions', []),
            'attacks': character.get('attacks', []),
            'spells': character.get('spells', {}),
            'skills': character.get('skills', {}),
        }
        if character and isinstance(character, dict)
        else {'name': '', 'role': '', 'hp': {}, 'ac': {}, 'conditions': [], 'attacks': [], 'spells': {}, 'skills': {}},
        'combat': _compress_combat(combat),
        'world_state': world_state_view,
        'world': _compress_world(world),
        'world_progression_summary': list(wp_hint_lines),
        'campaign': _compress_campaign(campaign),
        'scene': {
            'public': public_scene_for_prompt if public_scene_for_prompt else public_scene,
            'discoverable_clues': discoverable_clues,
            'gm_only': {
                'hidden_facts': gm_only_hidden_facts,
                'discoverable_clues_locked': gm_only_discoverable_locked,
            },
            'clue_records': {'discovered': discovered_clue_records, 'undiscovered': undiscovered_clue_records},
            'visible_clues': discovered_clue_records,
            'discovered_clues': discovered_clue_records,
            'clue_visibility': clue_visibility,
            'pending_leads': active_pending_leads,
            'runtime': runtime,
            'intent': intent_for_scene_payload,
            'layering_rules': {
                'visible_facts': 'Only visible facts may be directly asserted; align with narration_visibility.visible_facts.',
                'discoverable_clues': 'Reveal only when player investigates/searches/questions/observes closely; with discoverable_hinting, hint without asserting as confirmed truth.',
                'hidden_facts': 'Never reveal directly; use only for implications, NPC behavior, atmosphere, indirect clues.',
            },
        },
        'player_expression_contract': {
            'default_action_style': 'third_person',
            'quoted_speech_allowed': True,
            'preserve_user_expression_format': True,
            'example': 'Galinor asks, "What changed at the north gate?" while examining the notice board.',
        },
    }
    if narration_obligations.get("is_opening_scene"):
        assert payload["opening_inputs_are_curated"] is True
    if narration_seam_audit is not None:
        payload["narration_seam_audit"] = narration_seam_audit
    if use_manual_play_compact:
        for key in (
            'fallback_behavior',
            'anti_railroading_contract',
            'context_separation_contract',
            'player_facing_narration_purity_contract',
            'social_response_structure_contract',
            'interaction_continuity_contract',
            'first_mention_contract',
        ):
            payload.pop(key, None)
    if include_non_public_prompt_keys:
        return payload
    shipped = project_public_payload(payload)
    assert_no_debug_keys_in_prompt_payload(shipped)
    return shipped

# Compatibility residue: ``prompt_context`` remains the public import home for
# these helpers while implementations live in support-only
# ``game.prompt_context_leads``. Do not add prompt-contract semantics there.
from game.prompt_context_leads import (
    INTERLOCUTOR_DISCUSSION_RECENCY_WINDOW,
    _lead_get,
    _lead_status_value,
    _lead_lifecycle_value,
    _lead_int,
    _lead_type_value,
    _lead_pressure_sort_key,
    _recent_change_signal_rank,
    _recent_lead_changes_sort_key,
    _compact_lead_row,
    build_authoritative_lead_prompt_context,
    _interlocutor_discussion_sort_key,
    _discussion_row_recently_discussed,
    build_interlocutor_lead_discussion_context,
    deterministic_interlocutor_lead_behavior_hints,
)

