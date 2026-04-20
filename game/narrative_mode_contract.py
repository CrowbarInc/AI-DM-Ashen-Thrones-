"""Objective #6 — Narrative Mode Contract System.

This module builds a *derivative* (never authoritative) narrative-mode contract for a
single emitted segment. It is intentionally deterministic, JSON-safe, and compact:
it does not perform adjudication, does not mutate engine state, and never uses LLMs
for mode selection.

The contract is meant to be prompt-safe and machine-readable:
- exactly one mode is chosen for a segment
- no fallback to vague "generic narration" (use ``continuation`` instead)
- on conflict, CTIR / shipped response_policy remain authoritative; this contract
  is a downstream shaping hint only
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence, Tuple

NARRATIVE_MODE_CONTRACT_VERSION = 1

NARRATIVE_MODES = frozenset(
    {
        "opening",
        "continuation",
        "action_outcome",
        "dialogue",
        "transition",
        "exposition_answer",
    }
)

# Coarse optional buckets (kept small to remain stable + prompt-safe).
_MODE_FAMILY_BY_MODE = {
    "opening": "framing",
    "transition": "framing",
    "dialogue": "social",
    "exposition_answer": "answer",
    "action_outcome": "resolution",
    "continuation": "continuation",
}

# Bounded debug/signal codes. Keep codes symbolic; no prose paragraphs.
_MAX_SIGNAL_CODES = 16
_MAX_FORBIDDEN_MOVES = 16


def _as_str(v: Any) -> str:
    return str(v or "").strip()


def _is_json_serializable(obj: Any) -> bool:
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False


def _sorted_unique(items: Sequence[Any], *, limit: int) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for raw in items:
        s = _as_str(raw)
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
        if len(out) >= limit:
            break
    return sorted(out)


def _get_field(root: Mapping[str, Any] | None, dotted_path: str, default: Any = None) -> Any:
    """Resolve ``a.b.c`` on *root* as mapping-only traversal."""
    if not isinstance(root, Mapping) or not dotted_path:
        return default
    cur: Any = root
    for part in dotted_path.split("."):
        if not isinstance(cur, Mapping) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _truthy(root: Mapping[str, Any] | None, dotted_path: str) -> bool:
    return bool(_get_field(root, dotted_path, False))


def _skill_check_mapping_shows_resolved_roll(sc: Mapping[str, Any]) -> bool:
    """True when ``resolution.skill_check`` carries engine-resolved roll evidence (not DC-only config)."""
    if not isinstance(sc, Mapping) or not sc:
        return False
    succ = sc.get("success")
    if isinstance(succ, bool):
        return True
    roll = sc.get("roll")
    total = sc.get("total")
    if isinstance(roll, (int, float)) and isinstance(total, (int, float)):
        return True
    return False


def _normalize_prompt_obligations(raw: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Return prompt-safe obligations: dict[str, bool|list[str]] with stable ordering."""
    if not isinstance(raw, Mapping):
        return {}
    out: Dict[str, Any] = {}
    for k in sorted(raw.keys(), key=lambda x: str(x)):
        sk = _as_str(k)
        if not sk:
            continue
        v = raw.get(k)
        if isinstance(v, bool):
            out[sk] = v
            continue
        if isinstance(v, (list, tuple)):
            items: List[str] = []
            for item in list(v)[:64]:
                s = _as_str(item)
                if s:
                    items.append(s)
            out[sk] = items
            continue
        # Drop non prompt-safe values rather than stringify prose into the contract.
    return out


def _derive_mode_inputs(
    *,
    ctir: Mapping[str, Any] | None,
    turn_packet: Mapping[str, Any] | None,
    narration_obligations: Mapping[str, Any] | None,
    response_policy: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Extract a tiny set of resolved-turn signals for deterministic mode derivation."""
    c = ctir if isinstance(ctir, Mapping) else {}
    p = turn_packet if isinstance(turn_packet, Mapping) else {}
    ob = narration_obligations if isinstance(narration_obligations, Mapping) else {}
    rp = response_policy if isinstance(response_policy, Mapping) else {}

    # Prefer shipped response_policy where present (contract remains derivative).
    ac = rp.get("answer_completeness") if isinstance(rp.get("answer_completeness"), Mapping) else {}
    rtc = rp.get("response_type_contract") if isinstance(rp.get("response_type_contract"), Mapping) else {}
    required_response_type = _as_str(rtc.get("required_response_type")).lower() or None

    # CTIR resolution/state-change hints (bounded / already-resolved meaning).
    res_kind = _as_str(_get_field(c, "resolution.kind")).lower() or None
    requires_check = bool(_get_field(c, "resolution.requires_check", False))
    skill_check_obj = _get_field(c, "resolution.skill_check")
    skill_check_obj = skill_check_obj if isinstance(skill_check_obj, Mapping) else {}
    has_skill_check = bool(skill_check_obj)
    resolved_skill_check = _skill_check_mapping_shows_resolved_roll(skill_check_obj)
    has_combat = isinstance(_get_field(c, "resolution.combat"), Mapping)
    has_authoritative_outputs = bool(_get_field(c, "resolution.authoritative_outputs"))  # mapping->truthy ok
    outcome_type = _as_str(_get_field(c, "resolution.outcome_type")).lower() or None
    success_state = _as_str(_get_field(c, "resolution.success_state")).lower() or None

    state_changes = _get_field(c, "resolution.state_changes")
    state_changes = state_changes if isinstance(state_changes, Mapping) else {}
    scene_change = any(
        bool(state_changes.get(k))
        for k in ("scene_transition_occurred", "arrived_at_scene", "new_scene_context_available")
    ) or bool(_get_field(c, "resolution.resolved_transition", False))

    # Turn packet route hints (compact boundary surface).
    packet_resolution_kind = _as_str(p.get("resolution_kind")).lower() or None
    packet_route = p.get("route") if isinstance(p.get("route"), Mapping) else {}
    strict_social_expected = bool(packet_route.get("strict_social_expected")) if "strict_social_expected" in packet_route else None
    active_reply_kind = _as_str(packet_route.get("active_reply_kind")).lower() or None

    # Narration obligations (prompt-side resolved signals; not authoritative state).
    is_opening_scene = bool(ob.get("is_opening_scene"))
    must_advance_scene = bool(ob.get("must_advance_scene"))
    active_npc_reply_expected = bool(ob.get("active_npc_reply_expected"))
    suppress_non_social_emitters = bool(ob.get("suppress_non_social_emitters"))
    ob_reply_kind = _as_str(ob.get("active_npc_reply_kind")).lower() or None

    answer_required = bool(ac.get("answer_required"))
    answer_must_come_first = bool(ac.get("answer_must_come_first")) if "answer_must_come_first" in ac else False

    return {
        "is_opening_scene": is_opening_scene,
        "must_advance_scene": must_advance_scene,
        "scene_change": bool(scene_change),
        "active_npc_reply_expected": active_npc_reply_expected,
        "suppress_non_social_emitters": suppress_non_social_emitters,
        "required_response_type": required_response_type,
        "answer_required": answer_required,
        "answer_must_come_first": answer_must_come_first,
        "reply_kind": ob_reply_kind or active_reply_kind or None,
        "ctir_resolution_kind": res_kind,
        "packet_resolution_kind": packet_resolution_kind,
        "requires_check": bool(requires_check),
        "has_skill_check": bool(has_skill_check),
        "resolved_skill_check": bool(resolved_skill_check),
        "has_combat": bool(has_combat),
        "has_authoritative_outputs": bool(has_authoritative_outputs),
        "outcome_type": outcome_type,
        "success_state": success_state,
    }


def _looks_like_action_outcome(inputs: Mapping[str, Any]) -> bool:
    """Heuristic: this turn has an outcome to deliver (not merely a pending check prompt)."""
    if bool(inputs.get("requires_check")) and not bool(inputs.get("has_skill_check")):
        return False
    # Pending roll: ``skill_check`` may echo scene config ({dc, skill_id, ...}) before the engine resolves the roll.
    if (
        bool(inputs.get("requires_check"))
        and bool(inputs.get("has_skill_check"))
        and not bool(inputs.get("resolved_skill_check"))
    ):
        return False
    if bool(inputs.get("has_skill_check")) or bool(inputs.get("has_combat")):
        return True
    if _as_str(inputs.get("outcome_type")) or _as_str(inputs.get("success_state")):
        return True
    if bool(inputs.get("has_authoritative_outputs")):
        return True
    # Some engine kinds are inherently outcome-bearing when resolved.
    res_kind = _as_str(inputs.get("ctir_resolution_kind") or inputs.get("packet_resolution_kind")).lower()
    if res_kind in {
        "attack",
        "cast",
        "skill_check",
        "check",
        "save",
        "combat",
        "contest",
        "explore",
        "investigate",
        "interact",
    }:
        return True
    return False


def build_narrative_mode_contract(
    *,
    ctir: Mapping[str, Any] | None = None,
    turn_packet: Mapping[str, Any] | None = None,
    narration_obligations: Mapping[str, Any] | None = None,
    response_policy: Mapping[str, Any] | None = None,
    enabled: bool = True,
) -> Dict[str, Any]:
    """Build the canonical narrative-mode contract (derivative; deterministic).

    Inputs are already-resolved signals (CTIR / turn packet / prompt obligations / shipped policy).
    This function never mutates state and never re-decides adjudication.
    """
    if not enabled:
        return {
            "version": NARRATIVE_MODE_CONTRACT_VERSION,
            "enabled": False,
            "mode": "continuation",
            "mode_family": _MODE_FAMILY_BY_MODE["continuation"],
            "source_signals": [],
            "prompt_obligations": {},
            "forbidden_moves": ["no_generic_fallback"],
            "debug": {"derivation_codes": ["disabled"]},
        }

    inputs = _derive_mode_inputs(
        ctir=ctir,
        turn_packet=turn_packet,
        narration_obligations=narration_obligations,
        response_policy=response_policy,
    )

    derivation: List[str] = []

    # Deterministic priority order (exactly one mode):
    # 1) opening
    if bool(inputs.get("is_opening_scene")):
        mode = "opening"
        derivation.append("mode:opening:narration_obligations.is_opening_scene")
    # 2) transition
    elif bool(inputs.get("must_advance_scene")) or bool(inputs.get("scene_change")):
        mode = "transition"
        if bool(inputs.get("must_advance_scene")):
            derivation.append("mode:transition:narration_obligations.must_advance_scene")
        if bool(inputs.get("scene_change")):
            derivation.append("mode:transition:ctir.resolution.state_changes.scene_change")
    # 3) dialogue
    elif (
        _as_str(inputs.get("required_response_type")) == "dialogue"
        or bool(inputs.get("active_npc_reply_expected"))
        or bool(inputs.get("suppress_non_social_emitters"))
    ):
        mode = "dialogue"
        if _as_str(inputs.get("required_response_type")) == "dialogue":
            derivation.append("mode:dialogue:response_policy.response_type_contract.required_response_type=dialogue")
        if bool(inputs.get("active_npc_reply_expected")):
            derivation.append("mode:dialogue:narration_obligations.active_npc_reply_expected")
        if bool(inputs.get("suppress_non_social_emitters")):
            derivation.append("mode:dialogue:narration_obligations.suppress_non_social_emitters")
    # 4) exposition_answer
    elif bool(inputs.get("answer_required")):
        mode = "exposition_answer"
        derivation.append("mode:exposition_answer:response_policy.answer_completeness.answer_required")
    # 5) action_outcome
    elif _looks_like_action_outcome(inputs):
        mode = "action_outcome"
        derivation.append("mode:action_outcome:ctir.resolution.outcome_present")
    # 6) continuation
    else:
        mode = "continuation"
        derivation.append("mode:continuation:default_non_special")

    # Prompt obligations (machine readable, mode-specific, bounded).
    # Keep values as booleans/lists only; no prose.
    if mode == "opening":
        obligations = {
            "require_scene_grounding": True,
            "require_first_impression_framing": True,
            "suppress_mid_conversation_answer_shape": True,
        }
        forbidden = ["no_generic_fallback", "no_opening_tableau_reuse"]
    elif mode == "transition":
        obligations = {
            "foreground_scene_change": True,
            "allow_regrounding_new_location": True,
            "avoid_transition_without_scene_change": True,
        }
        forbidden = ["no_generic_fallback", "no_transition_without_scene_change"]
    elif mode == "dialogue":
        obligations = {
            "keep_reply_speaker_carried": True,
            "preserve_interlocutor_continuity": True,
            "suppress_scenic_recap_unless_scene_changes": True,
            "reply_kind": [inputs["reply_kind"]] if _as_str(inputs.get("reply_kind")) else [],
        }
        forbidden = ["no_generic_fallback", "no_dialogue_without_speaker_basis"]
    elif mode == "exposition_answer":
        obligations = {
            "answer_first": bool(inputs.get("answer_must_come_first") or inputs.get("answer_required")),
            "prioritize_information_delivery": True,
            "avoid_invented_action_resolution": True,
        }
        forbidden = ["no_generic_fallback", "no_answer_burying"]
    elif mode == "action_outcome":
        obligations = {
            "lead_with_outcome_signal": True,
            "preserve_state_change_salience": True,
            "avoid_exposition_before_result_lands": True,
        }
        forbidden = ["no_generic_fallback", "no_resultless_outcome"]
    else:  # continuation
        obligations = {
            "preserve_thread_continuity": True,
            "no_fresh_reopening_tableau": True,
            "prefer_forward_motion_over_recap": True,
        }
        forbidden = ["no_generic_fallback"]

    contract: Dict[str, Any] = {
        "version": NARRATIVE_MODE_CONTRACT_VERSION,
        "enabled": True,
        "mode": mode,
        "mode_family": _MODE_FAMILY_BY_MODE.get(mode),
        "source_signals": _sorted_unique(derivation, limit=_MAX_SIGNAL_CODES),
        "prompt_obligations": _normalize_prompt_obligations(obligations),
        "forbidden_moves": _sorted_unique(forbidden, limit=_MAX_FORBIDDEN_MOVES),
        "debug": {"derivation_codes": _sorted_unique(derivation, limit=_MAX_SIGNAL_CODES)},
    }
    return contract


def looks_like_narrative_mode_contract(obj: Any) -> bool:
    """Fast heuristic check for contract-like shape (not full validation)."""
    if not isinstance(obj, dict):
        return False
    if obj.get("version") != NARRATIVE_MODE_CONTRACT_VERSION:
        return False
    if not isinstance(obj.get("enabled"), bool):
        return False
    mode = _as_str(obj.get("mode"))
    if mode not in NARRATIVE_MODES:
        return False
    if "prompt_obligations" in obj and not isinstance(obj.get("prompt_obligations"), dict):
        return False
    if "forbidden_moves" in obj and not isinstance(obj.get("forbidden_moves"), list):
        return False
    return True


def validate_narrative_mode_contract(contract: Mapping[str, Any] | None) -> Tuple[bool, List[str]]:
    """Strict validator for narrative-mode contract shape + invariants.

    Returns (ok, reasons). Reasons are stable, symbolic codes.
    """
    reasons: List[str] = []
    if not isinstance(contract, Mapping):
        return False, ["narrative_mode_contract:not_a_mapping"]

    if contract.get("version") != NARRATIVE_MODE_CONTRACT_VERSION:
        reasons.append("narrative_mode_contract:bad_version")

    if not isinstance(contract.get("enabled"), bool):
        reasons.append("narrative_mode_contract:enabled_not_bool")

    mode = contract.get("mode")
    mode_s = mode.strip() if isinstance(mode, str) else ""
    if not isinstance(mode, str) or not mode_s:
        reasons.append("narrative_mode_contract:missing_mode")
    elif mode_s not in NARRATIVE_MODES:
        reasons.append(f"narrative_mode_contract:unknown_mode:{mode_s}")
    else:
        mf = contract.get("mode_family")
        if not isinstance(mf, str) or not mf.strip():
            reasons.append("narrative_mode_contract:missing_mode_family")
        elif mf.strip() != _MODE_FAMILY_BY_MODE.get(mode_s):
            reasons.append("narrative_mode_contract:mode_family_mismatch")

    # Reject multi-mode / contradictory structures.
    for forbidden_key in ("modes", "mode_flags", "selected_modes"):
        if forbidden_key in contract:
            reasons.append(f"narrative_mode_contract:forbidden_multi_mode_field:{forbidden_key}")

    po = contract.get("prompt_obligations")
    if po is not None and not isinstance(po, Mapping):
        reasons.append("narrative_mode_contract:prompt_obligations_not_mapping")
    elif isinstance(po, Mapping):
        for k, v in po.items():
            if not isinstance(k, str) or not k.strip():
                reasons.append("narrative_mode_contract:prompt_obligations_bad_key")
                break
            if isinstance(v, bool):
                continue
            if isinstance(v, list) and all(isinstance(x, str) for x in v):
                continue
            reasons.append(f"narrative_mode_contract:prompt_obligations_bad_value:{k}")
            break

    ss = contract.get("source_signals")
    if ss is not None and not isinstance(ss, list):
        reasons.append("narrative_mode_contract:source_signals_not_list")
    elif isinstance(ss, list) and any(not isinstance(x, str) for x in ss):
        reasons.append("narrative_mode_contract:source_signals_non_string")

    fm = contract.get("forbidden_moves")
    if fm is not None and not isinstance(fm, list):
        reasons.append("narrative_mode_contract:forbidden_moves_not_list")
    elif isinstance(fm, list):
        if any(not isinstance(x, str) or not x.strip() for x in fm):
            reasons.append("narrative_mode_contract:forbidden_moves_bad_item")
        # Hard invariant: no generic fallback.
        if "no_generic_fallback" not in set(x.strip() for x in fm if isinstance(x, str)):
            reasons.append("narrative_mode_contract:missing_no_generic_fallback_forbidden_move")

    dbg = contract.get("debug")
    if dbg is not None and not isinstance(dbg, Mapping):
        reasons.append("narrative_mode_contract:debug_not_mapping")
    elif isinstance(dbg, Mapping) and "derivation_codes" in dbg:
        dc = dbg.get("derivation_codes")
        if not isinstance(dc, list) or any(not isinstance(x, str) for x in dc):
            reasons.append("narrative_mode_contract:debug_derivation_codes_bad")

    if not _is_json_serializable(dict(contract)):
        reasons.append("narrative_mode_contract:not_json_serializable")

    return (not reasons), reasons

