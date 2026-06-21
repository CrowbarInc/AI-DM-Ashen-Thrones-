"""Final-emission narrative authority layer (gate contract resolution + boundary apply).

Validator and contract construction remain in :mod:`game.narrative_authority`.
This module owns gate-layer resolution, metadata merge, narrow repair helpers, and
validate-only boundary application.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping

from game.final_emission_text_formatting import _normalize_text
from game.narrative_authority import (
    narrative_authority_prefers_roll_prompt,
    narrative_authority_repair_hints,
    validate_narrative_authority,
    _BRANCH_FRAMING_RE,
    _HIDDEN_FACT_CERTAINTY_RE,
    _INTENT_CERTAINTY_RE,
    _ROLL_PROMPT_RE,
    _mask_dialogue_spans,
    _outcome_assertion_hits,
    _player_asks_intent_or_read,
    _sentence_has_hedge,
    _split_sentences,
    _STRONG_OUTCOME_ASSERTION_RE,
)
from game.response_policy_contracts import _last_player_input
from game.social_exchange_policy import merged_player_prompt_for_gate


def is_shipped_full_narrative_authority_contract(candidate: Any) -> bool:
    """True for ``build_narrative_authority_contract`` payloads, not prompt_debug slim summaries."""
    if not isinstance(candidate, dict):
        return False
    if isinstance(candidate.get("debug_inputs"), dict):
        return True
    if isinstance(candidate.get("debug_flags"), dict) and isinstance(candidate.get("allowed_deferrals"), list):
        return True
    return False


def coerce_narrative_authority_contract_dict(maybe: Any) -> Dict[str, Any] | None:
    if is_shipped_full_narrative_authority_contract(maybe):
        return maybe
    return None


def resolve_narrative_authority_contract(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Prefer the full narration payload path; never substitute prompt_debug for validation."""
    if not isinstance(gm_output, dict):
        return None
    pol = gm_output.get("response_policy")
    if isinstance(pol, dict):
        hit = coerce_narrative_authority_contract_dict(pol.get("narrative_authority"))
        if hit:
            return hit
    for key in ("narration_payload", "prompt_payload", "_narration_payload"):
        pl = gm_output.get(key)
        if not isinstance(pl, dict):
            continue
        hit = coerce_narrative_authority_contract_dict(pl.get("narrative_authority"))
        if hit:
            return hit
        rp = pl.get("response_policy")
        if isinstance(rp, dict):
            hit = coerce_narrative_authority_contract_dict(rp.get("narrative_authority"))
            if hit:
                return hit
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        hit = coerce_narrative_authority_contract_dict(md.get("narrative_authority"))
        if hit:
            return hit
        rp = md.get("response_policy")
        if isinstance(rp, dict):
            hit = coerce_narrative_authority_contract_dict(rp.get("narrative_authority"))
            if hit:
                return hit
    tr = gm_output.get("trace")
    if isinstance(tr, dict):
        hit = coerce_narrative_authority_contract_dict(tr.get("narrative_authority"))
        if hit:
            return hit
        rp = tr.get("response_policy")
        if isinstance(rp, dict):
            hit = coerce_narrative_authority_contract_dict(rp.get("narrative_authority"))
            if hit:
                return hit
    return None


def narrative_authority_prompt_debug_mirror(gm_output: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Compact upstream summary only (not valid as a shipped contract)."""
    if not isinstance(gm_output, dict):
        return None
    pd = gm_output.get("prompt_debug")
    if isinstance(pd, dict):
        sl = pd.get("narrative_authority")
        if isinstance(sl, dict):
            return sl
    md = gm_output.get("metadata")
    if isinstance(md, dict):
        em = md.get("emission_debug")
        if isinstance(em, dict):
            sl = em.get("narrative_authority_prompt_debug")
            if isinstance(sl, dict):
                return sl
    return None


def narrative_authority_policy_disabled(gm_output: Dict[str, Any] | None) -> bool:
    if not isinstance(gm_output, dict):
        return False
    pol = gm_output.get("response_policy")
    if not isinstance(pol, dict):
        return False
    if pol.get("forbid_unjustified_narrative_authority") is False:
        return True
    return False


def default_narrative_authority_meta() -> Dict[str, Any]:
    return {
        "narrative_authority_checked": False,
        "narrative_authority_failed": False,
        "narrative_authority_failure_reasons": [],
        "narrative_authority_repaired": False,
        "narrative_authority_repair_mode": None,
        "narrative_authority_skip_reason": None,
        "narrative_authority_deferral_mode": None,
        "narrative_authority_assertion_flags": {},
    }


def merge_narrative_authority_meta(meta: Dict[str, Any], na_dbg: Dict[str, Any]) -> None:
    if not na_dbg:
        return
    keys = (
        "narrative_authority_checked",
        "narrative_authority_failed",
        "narrative_authority_failure_reasons",
        "narrative_authority_repaired",
        "narrative_authority_repair_mode",
        "narrative_authority_skip_reason",
        "narrative_authority_deferral_mode",
        "narrative_authority_assertion_flags",
    )
    for k in keys:
        if k in na_dbg:
            meta[k] = na_dbg[k]


def merge_narrative_authority_into_emission_debug(
    out: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    eff_resolution: Dict[str, Any] | None,
    *,
    gate_meta: Dict[str, Any],
    gm_output: Dict[str, Any] | None,
) -> None:
    flat: Dict[str, Any] = {}
    for k, v in gate_meta.items():
        if not str(k).startswith("narrative_authority_"):
            continue
        flat[k] = v
    mirror = narrative_authority_prompt_debug_mirror(gm_output)
    full = resolve_narrative_authority_contract(gm_output)
    mirror_box: Dict[str, Any] = {}
    if isinstance(mirror, dict) and mirror:
        mirror_box["prompt_debug_mirror_present"] = True
        if isinstance(full, dict) and is_shipped_full_narrative_authority_contract(full):
            keys = (
                "enabled",
                "authoritative_outcome_available",
                "forbid_unresolved_outcome_assertions",
                "forbid_hidden_fact_assertions",
                "forbid_npc_intent_assertions_without_basis",
            )
            mismatch = any(mirror.get(k) != full.get(k) for k in keys)
            mirror_box["prompt_debug_mirror_mismatch_vs_shipped"] = bool(mismatch)

    def _patch_em(em: Any) -> None:
        if not isinstance(em, dict):
            return
        if mirror_box:
            base = em.get("narrative_authority")
            if isinstance(base, dict):
                em["narrative_authority"] = {**base, **mirror_box}
            else:
                em["narrative_authority"] = dict(mirror_box)
        for fk, fv in flat.items():
            em[fk] = fv

    if not flat and not mirror_box:
        return

    md_out = out.setdefault("metadata", {})
    if isinstance(md_out, dict):
        _patch_em(md_out.setdefault("emission_debug", {}))

    if isinstance(resolution, dict):
        md_r = resolution.setdefault("metadata", {})
        if isinstance(md_r, dict):
            _patch_em(md_r.setdefault("emission_debug", {}))

    if eff_resolution is not None and isinstance(eff_resolution.get("metadata"), dict):
        _patch_em(eff_resolution["metadata"].setdefault("emission_debug", {}))


def skip_narrative_authority_layer(
    text: Any,
    contract: Dict[str, Any] | None,
    *,
    gm_output: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any] | None,
) -> str | None:
    if response_type_debug is not None and response_type_debug.get("response_type_candidate_ok") is False:
        return "response_type_contract_failed"
    if narrative_authority_policy_disabled(gm_output):
        return "narrative_authority_policy_disabled"
    if not isinstance(contract, dict):
        return "no_full_contract"
    if not contract.get("enabled"):
        return "contract_disabled"
    if not isinstance(text, str):
        return "non_string_text"
    if not str(text).strip():
        return "empty_text"
    return None


def _na_outcome_sentence_span(raw: str) -> tuple[int, int, str] | None:
    masked_full = _mask_dialogue_spans(raw)
    for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
        msent = masked_full[start:end]
        if not str(msent).strip():
            continue
        if _sentence_has_hedge(sent):
            continue
        if _outcome_assertion_hits(sent, msent):
            return start, end, sent
    return None


def _na_hidden_fact_sentence_span(raw: str) -> tuple[int, int, str] | None:
    masked_full = _mask_dialogue_spans(raw)
    for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
        msent = masked_full[start:end]
        if _sentence_has_hedge(sent):
            continue
        if _HIDDEN_FACT_CERTAINTY_RE.search(msent.lower()):
            return start, end, sent
    return None


def _na_intent_sentence_span(
    raw: str,
    *,
    player_text: str | None,
    resolution: Dict[str, Any] | None,
) -> tuple[int, int, str] | None:
    res_prompt = (
        str((resolution or {}).get("prompt") or "").strip() if isinstance(resolution, dict) else ""
    )
    player_seeks = _player_asks_intent_or_read(player_text) or _player_asks_intent_or_read(res_prompt)
    masked_full = _mask_dialogue_spans(raw)
    for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
        msent = masked_full[start:end]
        low = msent.lower()
        if player_seeks and _sentence_has_hedge(sent):
            continue
        if player_seeks and _ROLL_PROMPT_RE.search(low):
            continue
        if _INTENT_CERTAINTY_RE.search(low):
            if player_seeks and (_sentence_has_hedge(sent) or _ROLL_PROMPT_RE.search(low)):
                continue
            return start, end, sent
    return None


def _na_replace_sentence(raw: str, start: int, end: int, replacement: str) -> str:
    rep = str(replacement or "").strip()
    before = raw[:start].rstrip()
    after = raw[end:].lstrip()
    parts = [p for p in (before, rep, after) if p]
    return _normalize_text(" ".join(parts))


def repair_narrative_authority_narrow(
    text: str,
    validation: Mapping[str, Any],
    *,
    resolution: Mapping[str, Any] | None,
    player_text: str | None,
) -> tuple[str | None, str | None]:
    flags = validation.get("assertion_flags") if isinstance(validation.get("assertion_flags"), dict) else {}
    if not flags or validation.get("passed") is True:
        return None, None

    narrative_authority_repair_hints(validation)

    repaired = str(text or "")
    modes: List[str] = []

    if flags.get("invented_outcome"):
        low_full = repaired.lower()
        if narrative_authority_prefers_roll_prompt(player_text, resolution) and not _ROLL_PROMPT_RE.search(
            low_full
        ):
            repaired = _normalize_text(
                repaired.rstrip()
                + " Make a skill check to see how that resolves before you treat the outcome as settled."
            )
            modes.append("invented_outcome_roll_prompt")
        elif _BRANCH_FRAMING_RE.search(low_full):
            span = _na_outcome_sentence_span(repaired)
            if span:
                start, end, _sent = span
                repaired = _na_replace_sentence(
                    repaired,
                    start,
                    end,
                    "Until the check resolves, leave that beat open rather than stating a result.",
                )
                modes.append("invented_outcome_branch_soften")
        else:
            span = _na_outcome_sentence_span(repaired)
            if span:
                start, end, _sent = span
                repaired = _na_replace_sentence(
                    repaired,
                    start,
                    end,
                    "You attempt it, but the outcome is not settled yet.",
                )
                modes.append("invented_outcome_uncertainty_replace")
            else:
                strong = _STRONG_OUTCOME_ASSERTION_RE.search(repaired)
                if strong:
                    repaired = (
                        repaired[: strong.start()]
                        + "You attempt it, but the outcome is not settled yet."
                        + repaired[strong.end() :]
                    )
                    repaired = _normalize_text(repaired)
                    modes.append("invented_outcome_span_soften")

    if flags.get("invented_hidden_fact"):
        span = _na_hidden_fact_sentence_span(repaired)
        if span:
            start, end, _sent = span
            repaired = _na_replace_sentence(
                repaired,
                start,
                end,
                "From what you can see, you can't pin the hidden cause down yet.",
            )
            modes.append("invented_hidden_fact_downgrade")

    if flags.get("invented_intent"):
        seek = _player_asks_intent_or_read(player_text) or _player_asks_intent_or_read(
            str((resolution or {}).get("prompt") or "").strip() if isinstance(resolution, Mapping) else ""
        )
        prefers = narrative_authority_prefers_roll_prompt(player_text, resolution)
        low_full = repaired.lower()
        if seek and prefers and not _ROLL_PROMPT_RE.search(low_full):
            repaired = _normalize_text(
                repaired.rstrip()
                + " Make an Insight check if you want a clearer read on motive—not as a hidden fact."
            )
            modes.append("invented_intent_insight_prompt")
        else:
            span = _na_intent_sentence_span(
                repaired,
                player_text=player_text,
                resolution=resolution if isinstance(resolution, dict) else None,
            )
            if span:
                start, end, _sent = span
                repaired = _na_replace_sentence(
                    repaired,
                    start,
                    end,
                    "You notice timing, posture, and wording—you can't treat that as proof of motive yet.",
                )
                modes.append("invented_intent_observable_cues")

    if not modes:
        return None, None
    return repaired, "|".join(modes)


def apply_narrative_authority_layer(
    text: str,
    *,
    gm_output: Dict[str, Any],
    resolution: Dict[str, Any] | None,
    strict_social_details: Dict[str, Any] | None,
    response_type_debug: Dict[str, Any],
    answer_completeness_meta: Dict[str, Any],
    session: Dict[str, Any] | None = None,
    scene_id: str = "",
) -> tuple[str, Dict[str, Any], List[str]]:
    _ = answer_completeness_meta
    strict_social_path = strict_social_details is not None
    contract = resolve_narrative_authority_contract(gm_output if isinstance(gm_output, dict) else None)

    meta = default_narrative_authority_meta()

    skip = skip_narrative_authority_layer(
        text,
        contract,
        gm_output=gm_output if isinstance(gm_output, dict) else None,
        response_type_debug=response_type_debug,
    )
    meta["narrative_authority_skip_reason"] = skip
    if skip:
        return text, meta, []

    assert contract is not None
    sid = str(scene_id or "").strip()
    player_text = merged_player_prompt_for_gate(
        resolution if isinstance(resolution, dict) else None,
        session if isinstance(session, dict) else None,
        sid,
    )
    if not str(player_text or "").strip():
        player_text = _last_player_input(
            resolution=resolution if isinstance(resolution, dict) else None,
            session=session if isinstance(session, dict) else None,
            scene_id=sid,
        )

    v0 = validate_narrative_authority(
        text,
        contract,
        resolution=resolution if isinstance(resolution, Mapping) else None,
        player_text=player_text,
    )
    meta["narrative_authority_checked"] = bool(v0.get("checked"))
    meta["narrative_authority_deferral_mode"] = v0.get("matched_deferral_mode")
    af = v0.get("assertion_flags")
    meta["narrative_authority_assertion_flags"] = dict(af) if isinstance(af, dict) else {}

    if not v0.get("checked") or v0.get("passed"):
        return text, meta, []

    meta["narrative_authority_failed"] = True
    meta["narrative_authority_failure_reasons"] = list(v0.get("failure_reasons") or [])
    meta["narrative_authority_boundary_semantic_repair_disabled"] = True

    extra: List[str] = []
    if not strict_social_path:
        extra.append("narrative_authority_unsatisfied_at_boundary_no_rewrite")
    meta["narrative_authority_failed"] = True
    return text, meta, extra
