"""Deterministic dialogue / social convergence plan (structural only).

Objective C1-D:
- Derivative-only from CTIR + bounded already-built social/speaker artifacts.
- Produces **no** player-facing prose and **no** prompt/instruction text.
- Does not move adjudication authority into the plan: CTIR remains semantic authority.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Dict, List, Optional, Sequence, Tuple


DIALOGUE_SOCIAL_PLAN_VERSION = 1

# Reject any prose-like / prompt-like fields from entering the plan surface.
_REJECT_FIELD_NAMES = frozenset(
    {
        "text",
        "prompt",
        "message",
        "dialogue_line",
        "dialogue",
        "narration",
        "instructions",
        "system_prompt",
        "player_facing_text",
        "gm_guidance",
    }
)

# Bounded contract vocabularies (no freeform tone/emotion prose).
REPLY_KINDS: frozenset[str] = frozenset({"answer", "explanation", "reaction", "refusal", "unknown"})
PRESSURE_STATES: frozenset[str] = frozenset({"none", "low", "moderate", "high"})
RELATIONSHIP_CODES: frozenset[str] = frozenset(
    {
        "unknown",
        "neutral",
        "friendly",
        "unfriendly",
        "hostile",
        "trust_low",
        "trust_high",
        "fear_low",
        "fear_high",
        "suspicion_low",
        "suspicion_high",
        "engagement_none",
        "engagement_engaged",
        "engagement_focused",
    }
)
TONE_CODES: frozenset[str] = frozenset(
    {
        "neutral",
        "warm",
        "cold",
        "guarded",
        "direct",
        "evasive",
        "threatening",
        "hostile",
        "deferential",
    }
)
PROHIBITED_CONTENT_CODES: frozenset[str] = frozenset(
    {
        "no_ooc_instructions",
        "no_prompt_text",
        "no_narrator_override",
        "no_player_agency_override",
    }
)


def _as_str(v: Any) -> str:
    return str(v or "").strip()


def _json_safe_atom(v: Any) -> Any:
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    return _as_str(v)


def _safe_list_str(items: Sequence[Any] | None, *, limit: int = 16) -> List[str]:
    out: List[str] = []
    if not isinstance(items, (list, tuple)):
        return out
    for raw in list(items)[:limit]:
        s = _as_str(raw)
        if s and s not in out:
            out.append(s)
    return out


def _pressure_state_from_engagement(engagement_level: str) -> str:
    el = _as_str(engagement_level).lower()
    if el == "focused":
        return "high"
    if el == "engaged":
        return "moderate"
    if el == "none":
        return "none"
    return "low" if el else "none"


def _tone_bounds_from_dialogue_intent(dialogue_intent: str) -> List[str]:
    # Intent-derived caps only; do not infer new NPC desire/goal.
    di = _as_str(dialogue_intent).lower()
    if di == "intimidate":
        return ["direct", "threatening"]
    if di == "persuade":
        return ["direct", "guarded"]
    if di == "deceive":
        return ["guarded", "evasive"]
    if di in ("question", "social_probe"):
        return ["neutral", "direct"]
    if di in ("barter", "recruit"):
        return ["direct", "guarded"]
    return ["neutral"]


def _pick_speaker_from_ctir_and_referents(
    ctir_obj: Mapping[str, Any] | None,
    referent_tracking: Mapping[str, Any] | None,
) -> Tuple[Optional[str], Optional[str], str, List[str]]:
    """Choose speaker id deterministically from already-owned artifacts.

    Order:
    - CTIR interaction.speaker_target.id/name (explicit engine semantic)
    - CTIR resolution.social.npc_id/npc_name (legacy direct social owner)
    - referent_tracking.continuity_subject.entity_id + display_name
    - referent_tracking.active_interaction_target (only if also in active_speaker_candidates)
    """
    derivation: List[str] = []

    ctir = ctir_obj if isinstance(ctir_obj, Mapping) else {}
    inter = ctir.get("interaction") if isinstance(ctir.get("interaction"), Mapping) else {}
    st = inter.get("speaker_target") if isinstance(inter.get("speaker_target"), Mapping) else {}

    sid = _as_str(st.get("id")) or None
    sname = _as_str(st.get("name")) or _as_str(st.get("display_name")) or None
    if sid:
        derivation.append("speaker:ctir.interaction.speaker_target")
        return sid, (sname or None), "ctir.interaction.speaker_target", derivation

    res = ctir.get("resolution") if isinstance(ctir.get("resolution"), Mapping) else {}
    soc = res.get("social") if isinstance(res.get("social"), Mapping) else {}
    sid2 = _as_str(soc.get("npc_id")) or None
    sname2 = _as_str(soc.get("npc_name")) or None
    if sid2:
        derivation.append("speaker:ctir.resolution.social.npc_id")
        return sid2, (sname2 or None), "ctir.resolution.social", derivation

    rt = referent_tracking if isinstance(referent_tracking, Mapping) else {}
    subj = rt.get("continuity_subject") if isinstance(rt.get("continuity_subject"), Mapping) else {}
    sid3 = _as_str(subj.get("entity_id")) or None
    sname3 = _as_str(subj.get("display_name")) or None
    if sid3:
        derivation.append("speaker:referent_tracking.continuity_subject")
        return sid3, (sname3 or None), "referent_tracking.continuity_subject", derivation

    tgt = _as_str(rt.get("active_interaction_target")) or None
    cands = rt.get("active_speaker_candidates")
    if tgt and isinstance(cands, list) and tgt in [_as_str(x) for x in cands]:
        derivation.append("speaker:referent_tracking.active_interaction_target")
        return tgt, None, "referent_tracking.active_interaction_target", derivation

    derivation.append("speaker:unresolved")
    return None, None, "unresolved", derivation


def build_dialogue_social_plan(
    *,
    ctir_obj: Mapping[str, Any] | None,
    referent_tracking: Mapping[str, Any] | None = None,
    bounded_session_hints: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build the structural dialogue/social plan dict (JSON-safe, deterministic).

    bounded_session_hints is optional and must be pre-bounded elsewhere (e.g. interaction context snapshot);
    this function will *not* parse raw player prose or inspect full session/world objects.
    """
    ctir = ctir_obj if isinstance(ctir_obj, Mapping) else {}
    res = ctir.get("resolution") if isinstance(ctir.get("resolution"), Mapping) else {}
    nc = ctir.get("noncombat") if isinstance(ctir.get("noncombat"), Mapping) else {}
    inter = ctir.get("interaction") if isinstance(ctir.get("interaction"), Mapping) else {}

    # Apply only when CTIR indicates a social probe / social kind resolution.
    kind = _as_str(res.get("kind")).lower()
    nc_kind = _as_str(nc.get("kind")).lower()
    nc_sub = _as_str(nc.get("subkind")).lower()
    is_social = (nc_kind == "social_probe") or (kind in ("question", "social_probe", "persuade", "intimidate", "deceive", "barter", "recruit"))

    speaker_id, speaker_name, speaker_source, speaker_deriv = _pick_speaker_from_ctir_and_referents(
        ctir, referent_tracking
    )

    # dialogue_intent is a classification label from CTIR/noncombat only (never inferred from prose).
    dialogue_intent = (nc_sub or kind) if is_social else None
    dialogue_intent = _as_str(dialogue_intent).lower() or None

    # reply_kind is allowed only as a bounded code.
    narr_constraints = nc.get("narration_constraints") if isinstance(nc.get("narration_constraints"), Mapping) else {}
    reply_kind = _as_str(narr_constraints.get("reply_kind") or res.get("reply_kind") or "").lower() or "unknown"
    if reply_kind not in REPLY_KINDS:
        reply_kind = "unknown"

    cont = inter.get("continuity_snapshot") if isinstance(inter.get("continuity_snapshot"), Mapping) else {}
    engagement_level = _as_str(cont.get("engagement_level") or "")
    pressure_state = _pressure_state_from_engagement(engagement_level) if is_social else "none"

    relationship_codes: List[str] = []
    if engagement_level:
        ec = f"engagement_{engagement_level.strip().lower()}"
        if ec in RELATIONSHIP_CODES:
            relationship_codes.append(ec)
    if not relationship_codes:
        relationship_codes.append("unknown")

    tone_bounds = [t for t in _tone_bounds_from_dialogue_intent(dialogue_intent or "") if t in TONE_CODES]
    if not tone_bounds:
        tone_bounds = ["neutral"]

    derivation_codes: List[str] = [
        "dialogue_social_plan:v1",
        *(speaker_deriv or []),
        "intent:ctir_only",
    ]
    if bounded_session_hints:
        derivation_codes.append("session_hints:bounded")
    if referent_tracking:
        derivation_codes.append("referent_tracking:consumed")

    prohibited = sorted(PROHIBITED_CONTENT_CODES)

    plan: Dict[str, Any] = {
        "version": DIALOGUE_SOCIAL_PLAN_VERSION,
        # Applies only when a concrete speaker is resolved. We intentionally do not
        # infer/guess a speaker from dialogue_intent alone.
        "applies": bool(is_social and speaker_id and dialogue_intent),
        "speaker_id": speaker_id,
        "speaker_name": speaker_name,
        "speaker_source": speaker_source,
        "dialogue_intent": dialogue_intent,
        "reply_kind": reply_kind,
        "pressure_state": pressure_state,
        "relationship_codes": relationship_codes,
        "tone_bounds": tone_bounds,
        "prohibited_content_codes": prohibited,
        "derivation_codes": sorted(set([_as_str(x) for x in derivation_codes if _as_str(x)])),
        "validator": {
            "validated": False,
            "errors": [],
            "reject_field_names": sorted(_REJECT_FIELD_NAMES),
            "allowed_reply_kinds": sorted(REPLY_KINDS),
            "allowed_pressure_states": sorted(PRESSURE_STATES),
            "allowed_tone_codes": sorted(TONE_CODES),
            "allowed_relationship_codes": sorted(RELATIONSHIP_CODES),
        },
    }
    # Optional bounded hints pass-through (must remain structural).
    if isinstance(bounded_session_hints, Mapping) and bounded_session_hints:
        # Keep only atoms and tiny bounded lists; never store full maps.
        plan["bounded_session_hints"] = {
            k: _json_safe_atom(v)
            for k, v in list(bounded_session_hints.items())[:12]
            if _as_str(k) and not isinstance(v, (dict, list, tuple))
        }

    validate_dialogue_social_plan(plan, strict=True)
    return plan


def _scan_for_rejected_field_names(obj: Any, *, path: str = "") -> List[str]:
    errs: List[str] = []
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            sk = _as_str(k).lower()
            p = f"{path}.{sk}" if path else sk
            if sk in _REJECT_FIELD_NAMES:
                errs.append(f"rejected_field_name:{p}")
            errs.extend(_scan_for_rejected_field_names(v, path=p))
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:64]):
            errs.extend(_scan_for_rejected_field_names(item, path=f"{path}[{i}]"))
    return errs


def validate_dialogue_social_plan(plan: Mapping[str, Any] | None, *, strict: bool = True) -> Tuple[bool, List[str]]:
    """Validate the dialogue/social plan contract.

    Returns (ok, errors). When strict=True, raises ValueError on failure.
    """
    errors: List[str] = []
    if not isinstance(plan, Mapping):
        errors.append("plan_not_mapping")
        if strict:
            raise ValueError(";".join(errors))
        return False, errors

    if plan.get("version") != DIALOGUE_SOCIAL_PLAN_VERSION:
        errors.append("bad_version")

    applies = bool(plan.get("applies"))
    if applies:
        if not _as_str(plan.get("speaker_id")):
            errors.append("missing_required:speaker_id")
        if not _as_str(plan.get("dialogue_intent")):
            errors.append("missing_required:dialogue_intent")

    # No prose-like or prompt-like fields anywhere in the plan tree.
    errors.extend(_scan_for_rejected_field_names(plan))

    rk = _as_str(plan.get("reply_kind")).lower() or "unknown"
    if rk not in REPLY_KINDS:
        errors.append("bad_reply_kind")

    ps = _as_str(plan.get("pressure_state")).lower()
    if ps and ps not in PRESSURE_STATES:
        errors.append("bad_pressure_state")

    tb = plan.get("tone_bounds")
    if not isinstance(tb, list):
        errors.append("tone_bounds_not_list")
    else:
        for t in tb[:16]:
            ts = _as_str(t)
            if not ts or ts not in TONE_CODES:
                errors.append("bad_tone_code")
                break

    rc = plan.get("relationship_codes")
    if rc is not None:
        if not isinstance(rc, list):
            errors.append("relationship_codes_not_list")
        else:
            for x in rc[:24]:
                xs = _as_str(x)
                if not xs or xs not in RELATIONSHIP_CODES:
                    errors.append("bad_relationship_code")
                    break

    # Ensure JSON-safety.
    try:
        json.dumps(dict(plan), sort_keys=True)
    except (TypeError, ValueError):
        errors.append("not_json_serializable")

    # Validator block is mandatory.
    vb = plan.get("validator")
    if not isinstance(vb, Mapping):
        errors.append("missing_validator_block")

    ok = not errors
    # Mutate validator block in-place if dict-like (callers expect JSON-safe dict).
    if isinstance(vb, dict):
        vb["validated"] = ok
        vb["errors"] = list(errors)

    if strict and not ok:
        raise ValueError(";".join(errors))
    return ok, errors

