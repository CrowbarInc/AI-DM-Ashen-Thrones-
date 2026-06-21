"""Deterministic dialogue / social convergence plan (structural only).

Objective C1-D:
- Derivative-only from CTIR + bounded already-built social/speaker artifacts.
- Produces **no** player-facing prose and **no** prompt/instruction text.
- Does not move adjudication authority into the plan: CTIR remains semantic authority.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any, Dict, List, Optional, Sequence, Tuple

from game.final_emission_text_formatting import _normalize_text


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

# Phase 1 (Block Y): declared pregate alias provenance — never ``inferred_from_prose``.
SPEAKER_ALIAS_RESOLUTION_SOURCES: frozenset[str] = frozenset(
    {
        "continuity_snapshot",
        "referent_tracking",
        "interaction_continuity_contract",
        "manual_bundle_override",
    }
)

_ALIAS_LABEL_MAX_LEN = 128
_MAX_DECLARED_PREGATE_LABELS = 8


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


def _normalized_attribution_label(raw: Any) -> Optional[str]:
    """Bounded structural label from upstream maps — reject newline/control-heavy blobs."""
    t = _as_str(raw)
    if not t or len(t) > _ALIAS_LABEL_MAX_LEN:
        return None
    if any(c in t for c in "\n\r\t"):
        return None
    return t


def _labels_and_writer_from_alias_mapping(m: Mapping[str, Any]) -> Tuple[List[str], Optional[str]]:
    """Read optional Phase-1 keys only (declared upstream data)."""
    raw_list = m.get("allowed_pregate_speaker_labels")
    labels = (
        _safe_list_str(raw_list, limit=_MAX_DECLARED_PREGATE_LABELS)
        if isinstance(raw_list, (list, tuple))
        else []
    )
    wl = _normalized_attribution_label(m.get("writer_attribution_label"))
    return labels, wl


def _dedupe_labels_ci(labels: Sequence[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for raw in labels:
        s = _as_str(raw)
        if not s:
            continue
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
        if len(out) >= _MAX_DECLARED_PREGATE_LABELS:
            break
    return out


def _collect_declared_pregate_alias_fields(
    ctir_obj: Mapping[str, Any] | None,
    referent_tracking: Mapping[str, Any] | None,
) -> Tuple[List[str], Optional[str], Optional[str]]:
    """Return (allowed_pregate_speaker_labels, writer_attribution_label, speaker_alias_resolution_source).

    Populated only from **declared** CTIR / referent_tracking structure — no prose inference,
    no synthesizing aliases from entity ids or names.
    """
    ctir = ctir_obj if isinstance(ctir_obj, Mapping) else {}
    inter = ctir.get("interaction") if isinstance(ctir.get("interaction"), Mapping) else {}
    cont = inter.get("continuity_snapshot") if isinstance(inter.get("continuity_snapshot"), Mapping) else {}

    allowed: List[str] = []
    writer: Optional[str] = None
    primary_source: Optional[str] = None

    if isinstance(cont, Mapping):
        cl, cw = _labels_and_writer_from_alias_mapping(cont)
        if cl or cw:
            primary_source = "continuity_snapshot"
            allowed.extend(cl)
            writer = cw

    rt = referent_tracking if isinstance(referent_tracking, Mapping) else {}
    rtl, rtw = _labels_and_writer_from_alias_mapping(rt)
    if rtl or rtw:
        if primary_source is None:
            primary_source = "referent_tracking"
        for x in rtl:
            allowed.append(x)
        if writer is None:
            writer = rtw

    allowed = _dedupe_labels_ci(allowed)
    if not allowed and not writer:
        return [], None, None
    return allowed, writer, primary_source


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

    pregate_labels, pregate_writer, pregate_source = _collect_declared_pregate_alias_fields(
        ctir, referent_tracking
    )

    derivation_codes: List[str] = [
        "dialogue_social_plan:v1",
        *(speaker_deriv or []),
        "intent:ctir_only",
    ]
    if bounded_session_hints:
        derivation_codes.append("session_hints:bounded")
    if referent_tracking:
        derivation_codes.append("referent_tracking:consumed")
    if pregate_labels or pregate_writer:
        derivation_codes.append(f"speaker_alias_declared:{pregate_source or 'unknown'}")

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
            "allowed_speaker_alias_resolution_sources": sorted(SPEAKER_ALIAS_RESOLUTION_SOURCES),
        },
    }
    # Phase 1 (Block Y): optional declared pregate aliases — omit keys when absent (backward compatible).
    if pregate_labels:
        plan["allowed_pregate_speaker_labels"] = list(pregate_labels)
    if pregate_writer:
        plan["writer_attribution_label"] = pregate_writer
    if pregate_labels or pregate_writer:
        plan["speaker_alias_resolution_source"] = pregate_source or "referent_tracking"
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

    apl = plan.get("allowed_pregate_speaker_labels")
    has_list_labels = False
    if apl is not None:
        if not isinstance(apl, list):
            errors.append("allowed_pregate_speaker_labels_not_list")
        elif len(apl) > _MAX_DECLARED_PREGATE_LABELS:
            errors.append("allowed_pregate_speaker_labels_over_limit")
        else:
            for item in apl:
                if not _normalized_attribution_label(item):
                    errors.append("bad_allowed_pregate_speaker_label_item")
                    break
            else:
                has_list_labels = bool(apl)

    wal_raw = plan.get("writer_attribution_label")
    has_writer = bool(wal_raw is not None and _normalized_attribution_label(wal_raw))
    if wal_raw is not None and not has_writer:
        errors.append("bad_writer_attribution_label")

    alias_src = _as_str(plan.get("speaker_alias_resolution_source"))
    has_alias_data = bool(has_list_labels or has_writer)
    if has_alias_data and not alias_src:
        errors.append("missing_required:speaker_alias_resolution_source_when_alias_fields_present")
    if alias_src and alias_src not in SPEAKER_ALIAS_RESOLUTION_SOURCES:
        errors.append("bad_speaker_alias_resolution_source")
    if alias_src and not has_alias_data:
        errors.append("speaker_alias_resolution_source_without_alias_fields")

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


def pregate_attributed_label_matches_dialogue_social_plan(
    attributed_label: str,
    plan: Mapping[str, Any],
) -> bool:
    """Return True when *attributed_label* is explicitly allowed by the structural plan.

    **Exact token equality only** (case-fold on ASCII-ish speaker tokens): canonical
    ``speaker_id`` slug vs whitespace→underscore slug of the attributed fragment,
    canonical ``speaker_name``, declared ``writer_attribution_label``, or membership in
    ``allowed_pregate_speaker_labels``. No fuzzy matching and no inference from unrelated prose.
    """
    lab = _as_str(attributed_label)
    if not lab:
        return False
    ll = lab.strip().lower()
    ll_slug = ll.replace(" ", "_")

    sid = _as_str(plan.get("speaker_id")).strip().lower()
    sname = _as_str(plan.get("speaker_name")).strip().lower()

    if sid and ll_slug == sid:
        return True
    if sname and ll == sname:
        return True

    wal = _as_str(plan.get("writer_attribution_label")).strip().lower()
    if wal and ll == wal:
        return True

    raw = plan.get("allowed_pregate_speaker_labels")
    if isinstance(raw, list):
        for item in raw:
            if _as_str(item).strip().lower() == ll:
                return True
    return False


# --- Strict-social dialogue plan enforcement (BJ-30 owner) ---

_DIALOGUE_QUOTE_RE = re.compile(r'["“”][^"”]{2,}["“”]')
_DIALOGUE_SPEECH_VERB_RE = re.compile(
    r"\b(?:says|said|replies|replied|answers|answered|asks|asked|mutters|muttered|whispers|whispered|snaps|snapped|spits|spat|grunts|grunted)\b",
    re.IGNORECASE,
)
_DIALOGUE_NAME_COLON_RE = re.compile(r"(?:^|\n)\s*([A-Z][a-zA-Z]{1,24}(?:\s+[A-Z][a-zA-Z]{1,24}){0,2})\s*:\s*['\"“”]")
_DIALOGUE_SPEAKER_ATTR_RE = re.compile(
    r"\b([A-Z][a-zA-Z]{1,24}(?:\s+[A-Z][a-zA-Z]{1,24}){0,2})\s+(?:says|replies|answers|asks|mutters|whispers|snaps|spits|grunts)\b",
    re.IGNORECASE,
)
_DIALOGUE_SOCIAL_GLUE_RE = re.compile(
    r"\b(?:nods?|shrugs?|sighs?|hesitates?|pauses?|leans in|leans closer|glances|looks at you|meets your eyes)\b",
    re.IGNORECASE,
)
_BARE_SPEECH_ATTRIBUTION_SHELL_RE = re.compile(
    r"^\s*(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4}\s+)?"
    r"(?:says|replies|answers|mutters|asks|whispers|adds|continues)\s*\.?\s*$",
    re.IGNORECASE,
)


def dialogue_plan_trace_defaults() -> Dict[str, Any]:
    return {
        "dialogue_plan_checked": False,
        "dialogue_plan_required": False,
        "dialogue_plan_present": False,
        "dialogue_plan_valid": False,
        "dialogue_plan_failure_reasons": [],
        "dialogue_plan_repair_mode": None,
        "dialogue_plan_subtractive_strip_deferred": False,
    }


def extract_attributed_speaker_labels(text: str) -> List[str]:
    raw = str(text or "")
    labels: List[str] = []
    for m in _DIALOGUE_NAME_COLON_RE.finditer(raw):
        lab = str(m.group(1) or "").strip()
        if lab and lab not in labels:
            labels.append(lab)
    for m in _DIALOGUE_SPEAKER_ATTR_RE.finditer(raw):
        lab = str(m.group(1) or "").strip()
        if lab and lab not in labels:
            labels.append(lab)
    return labels[:8]


def dialogue_bearing_signals(text: str) -> Dict[str, Any]:
    t = str(text or "")
    low = t.lower()
    has_quotes = bool(_DIALOGUE_QUOTE_RE.search(t))
    has_speech_verb = bool(_DIALOGUE_SPEECH_VERB_RE.search(t))
    has_name_colon = bool(_DIALOGUE_NAME_COLON_RE.search(t))
    has_speaker_attr = bool(_DIALOGUE_SPEAKER_ATTR_RE.search(t))
    has_social_glue = bool(_DIALOGUE_SOCIAL_GLUE_RE.search(low))
    dialogue_present = bool(has_quotes or has_speech_verb or has_name_colon or has_speaker_attr)
    glue_present = bool(has_social_glue and (has_speaker_attr or has_name_colon or has_speech_verb))
    return {
        "dialogue_present": dialogue_present,
        "glue_present": glue_present,
        "has_quotes": has_quotes,
        "has_speech_verb": has_speech_verb,
        "has_name_colon": has_name_colon,
        "has_speaker_attr": has_speaker_attr,
        "attributed_speakers": extract_attributed_speaker_labels(t),
    }


def get_dialogue_social_plan_from_emission_debug(
    resolution: Mapping[str, Any] | None,
    eff_resolution: Mapping[str, Any] | None,
) -> Mapping[str, Any] | None:
    for res in (eff_resolution, resolution):
        md = res.get("metadata") if isinstance(res, Mapping) and isinstance(res.get("metadata"), Mapping) else None
        em = md.get("emission_debug") if isinstance(md, Mapping) and isinstance(md.get("emission_debug"), Mapping) else None
        dsp = em.get("dialogue_social_plan") if isinstance(em, Mapping) else None
        if isinstance(dsp, Mapping):
            return dsp
    return None


def strip_dialogue_from_text(text: str) -> str:
    raw = str(text or "")
    stripped = _DIALOGUE_QUOTE_RE.sub("", raw)
    stripped = re.sub(
        r"(?:^|\n)\s*[A-Z][a-zA-Z]{1,24}(?:\s+[A-Z][a-zA-Z]{1,24}){0,2}\s*:\s*",
        "\n",
        stripped,
    )
    stripped = re.sub(r"\s+", " ", stripped).strip()
    return _normalize_text(stripped)


def is_the_lowercase_role_mutters_comma_shell(text: str) -> bool:
    """Strip tail like ``The tavern runner mutters,`` after quote removal (comma breaks bare-shell RE)."""
    t = _normalize_text(str(text or "")).strip()
    if '"' in t or "'" in t or "\u201c" in t or "\u201d" in t:
        return False
    return bool(
        re.match(
            r"(?i)^the\s+[a-z][\w'-]*(?:\s+[a-z][\w'-]*){0,4}\s+mutters\s*,\s*$",
            t,
        )
    )


def strict_social_line_matches_terminal_emission_pool(text: str, resolution: Mapping[str, Any] | None) -> bool:
    """True when emitted text equals a deterministic strict-social terminal/minimal emergency line."""
    from game.social_exchange_fallback_catalog import (
        strict_social_ownership_terminal_fallback,
        text_is_strict_social_minimal_emergency_fallback,
    )

    if not isinstance(resolution, dict):
        return False
    t = _normalize_text(str(text or "")).strip()
    if not t:
        return False
    if text_is_strict_social_minimal_emergency_fallback(text, resolution):
        return True
    return _normalize_text(strict_social_ownership_terminal_fallback(resolution)).strip() == t


def is_bare_speech_attribution_shell_line(text: str) -> bool:
    """True when subtractive dialogue strip left only a speech-verb tail with no quoted/spoken payload."""
    t = _normalize_text(str(text or "")).strip()
    if not t:
        return True
    if '"' in t or "'" in t or "\u201c" in t or "\u201d" in t:
        return False
    return bool(_BARE_SPEECH_ATTRIBUTION_SHELL_RE.match(t))


def enforce_dialogue_plan_invariant_on_strict_social(
    text: str,
    *,
    resolution: Mapping[str, Any] | None,
    eff_resolution: Mapping[str, Any] | None,
    strict_social_active: bool,
    response_type_required: str | None,
) -> tuple[str, Dict[str, Any]]:
    trace = dialogue_plan_trace_defaults()
    if not strict_social_active:
        return text, trace

    sig = dialogue_bearing_signals(text)
    dialogue_present = bool(sig.get("dialogue_present")) or bool(sig.get("glue_present"))
    npc_reply_expected = False
    if isinstance(eff_resolution, Mapping):
        soc = eff_resolution.get("social") if isinstance(eff_resolution.get("social"), Mapping) else {}
        npc_reply_expected = bool(soc.get("npc_reply_expected"))

    required = bool(dialogue_present or npc_reply_expected or (str(response_type_required or "").strip().lower() == "dialogue"))
    trace["dialogue_plan_checked"] = True
    trace["dialogue_plan_required"] = required
    if not required:
        return text, trace

    dsp = get_dialogue_social_plan_from_emission_debug(resolution, eff_resolution)
    trace["dialogue_plan_present"] = bool(isinstance(dsp, Mapping))
    failure_reasons: List[str] = []
    if not isinstance(dsp, Mapping):
        failure_reasons.append("missing_dialogue_social_plan")
    else:
        if dsp.get("applies") is not True:
            failure_reasons.append("dialogue_social_plan_applies_false")
        if not str(dsp.get("speaker_id") or "").strip():
            failure_reasons.append("missing_required:speaker_id")
        if not str(dsp.get("dialogue_intent") or "").strip():
            failure_reasons.append("missing_required:dialogue_intent")
        ok, errs = validate_dialogue_social_plan(dsp, strict=False)
        if not ok:
            failure_reasons.extend([f"plan_invalid:{e}" for e in (errs or [])[:12]])

        attributed = [str(x).strip() for x in (sig.get("attributed_speakers") or []) if str(x).strip()]
        if attributed:
            for lab in attributed:
                if pregate_attributed_label_matches_dialogue_social_plan(lab, dsp):
                    continue
                if str(dsp.get("speaker_id") or "").strip() or str(dsp.get("speaker_name") or "").strip():
                    failure_reasons.append(f"attributed_speaker_mismatch:{lab}")
                    break

    failure_reasons = list(dict.fromkeys([str(r) for r in failure_reasons if str(r).strip()]))
    trace["dialogue_plan_failure_reasons"] = failure_reasons
    trace["dialogue_plan_valid"] = not bool(failure_reasons)

    if trace["dialogue_plan_valid"]:
        return text, trace

    repaired = strip_dialogue_from_text(text)
    trace["dialogue_plan_repair_mode"] = "subtractive_strip_dialogue"
    if not repaired.strip():
        sig0 = dialogue_bearing_signals(text)
        if bool(sig0.get("has_quotes")):
            # Quote-only or quote-stripping erased the only diegetic payload; keep the candidate for strict-social
            # writers / referential substitution rather than collapsing to ambient stall text.
            trace["dialogue_plan_repair_mode"] = "defer_empty_strip_preserving_quote_only_candidate"
            trace["dialogue_plan_subtractive_strip_deferred"] = True
            return text, trace
        trace["dialogue_plan_repair_mode"] = "fail_closed_no_dialogue"
        return "The moment passes without an answer.", trace
    if is_bare_speech_attribution_shell_line(repaired):
        # Stripping quoted speech would erase the only playable NPC line; defer to strict-social writer/fallbacks.
        trace["dialogue_plan_repair_mode"] = "defer_strip_preserving_dialogue_candidate"
        trace["dialogue_plan_subtractive_strip_deferred"] = True
        return text, trace
    if (
        isinstance(eff_resolution, Mapping)
        and str((eff_resolution.get("social") or {}).get("social_intent_class") or "").strip().lower()
        == "social_exchange"
        and '"' in str(text or "")
        and '"' not in str(repaired or "")
        and is_the_lowercase_role_mutters_comma_shell(str(repaired or ""))
    ):
        # ``The tavern runner mutters,`` tails lose the comma-attribution case for bare-shell detection;
        # preserve the clipped quoted line for strict-social restoration.
        trace["dialogue_plan_repair_mode"] = "defer_strip_preserving_dialogue_candidate"
        trace["dialogue_plan_subtractive_strip_deferred"] = True
        return text, trace
    # Subtractive strip removed quoted speech but left a pronoun-led beat tail (e.g. ``she insists``);
    # that tail is not an attributable ``<Name> says`` shell. Preserve the original for strict-social
    # writers / referential local repair. Do not defer for ``<NPC> says,`` shells: those are the
    # dialogue-plan fail-closed shape handled by returning ``repaired``.
    rep_tail = str(repaired or "").lstrip()
    if (
        isinstance(eff_resolution, Mapping)
        and str((eff_resolution.get("social") or {}).get("social_intent_class") or "").strip().lower()
        == "social_exchange"
        and bool((eff_resolution.get("social") or {}).get("npc_reply_expected"))
        and '"' in str(text or "")
        and '"' not in str(repaired or "")
        and bool(re.match(r"(?i)(?:they|he|she)\b", rep_tail))
    ):
        trace["dialogue_plan_repair_mode"] = "defer_strip_preserving_dialogue_candidate"
        trace["dialogue_plan_subtractive_strip_deferred"] = True
        return text, trace
    return repaired, trace

