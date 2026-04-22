"""Objective N4 — Acceptance Quality (runtime anti-collapse / playability floor).

Contract, pure validation, bounded subtractive repair, and compact trace assembly live in this
module. :mod:`game.final_emission_gate` owns orchestration and calls
:func:`validate_and_repair_acceptance_quality` as the single live seam.

**What N4 is**

N4 is a **runtime quality-floor** layer in the gate *family* of concerns: deterministic,
reason-code-driven checks that reject a narrow class of **playable** failures—outputs that can be
structurally “legal” under other contracts yet **collapse** into unplayable or over-authored
closures. It is **adjacent** to Narrative Authenticity (NA): NA owns anti-echo, follow-up signal
density, diegetic-shape, and rumor-adjacent heuristics where documented. N4 owns **anti-collapse /
floor** failure modes called out in the maintainer map: thin-but-valid emptiness, single-anchor
carries, abstract-only terminals, and plot-trailer style closes.

**What N4 is not**

- **Not scoring** — No numeric axes, no subjective “better prose” tiers, no aggregate quality
  scores in live enforcement.
- **Not a semantic author** — Repairs are **bounded, subtractive, and non-inventive** (trim / drop
  terminal sentence only when policy allows). The final emission boundary must not become a prose
  completion engine.
- **Not an evaluator replacement** — Offline playability / harness tooling remains **read-only** to
  live legality; N4 does not import evaluator modules or mirror their judgments.
- **Not a second NA** — No LLM judging, no freeform subjective scoring, no duplication of NA’s
  echo/filler/stagnation ownership.

**Ownership (this module vs gate)**

- **Contract resolution** — :func:`build_acceptance_quality_contract`: deterministic, JSON-shaped
  policy dict only; no text I/O.
- **Pure validation** — :func:`validate_acceptance_quality`: verdict + reason codes + evidence from
  candidate text + contract; no mutation of engine truth or emitted dicts.
- **Bounded repairs** — :func:`repair_acceptance_quality_minimal`: subtractive strategies only;
  callers must re-validate; live paths use :func:`validate_and_repair_acceptance_quality`.
- **Compact emission trace** — :func:`build_acceptance_quality_emission_trace`: stable slice for
  FEM merge (full validator evidence may be larger; see that function’s docstring).
- **Canonical orchestration** — :func:`validate_and_repair_acceptance_quality`: validate → repair
  (if failed) → **re-validate** → trace; final ``passed`` is always from a fresh validation pass.

**Detection targets (comments and heuristics)**

- **Thin-but-valid** — Few words, few **distinct signal families** (location, actor/entity,
  pressure/motion, concrete sensory/object/action); passes stricter contracts yet offers nothing to
  grab onto at the table.
- **Single-anchor collapse** — One salient noun/anchor token dominates the turn span (narrow
  window), so the whole beat hangs on a single repeated pivot.
- **Abstract-only ending** — Terminal sentence is mood/tension hand-waving (“the tension
  remains”, “the situation worsens”) without concrete grounding signals in that sentence.
- **Plot-trailer close** — Terminal line reads like marketing copy / next-episode stinger
  (deterministic phrase patterns), not situated play.

C2/C3/C4 boundaries: this module does **not** resolve CTIR meaning, ship prompt bundles, or own
``narrative_mode_contract`` derivation; it only consumes resolved policy shapes and candidate text
when validators run.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence, Tuple

from game.final_emission_text import _normalize_text

ACCEPTANCE_QUALITY_VERSION = 1

# Stable reason tokens for validator output and future FEM merge (gate-owned packaging).
ACCEPTANCE_QUALITY_EMPTY_TEXT = "acceptance_quality_empty_text"
ACCEPTANCE_QUALITY_CONTRACT_DISABLED = "acceptance_quality_contract_disabled"
ACCEPTANCE_QUALITY_THIN_GROUNDING_FLOOR = "acceptance_quality_thin_grounding_floor"
ACCEPTANCE_QUALITY_SINGLE_ANCHOR_COLLAPSE = "acceptance_quality_single_anchor_collapse"
ACCEPTANCE_QUALITY_ABSTRACT_ONLY_TERMINAL = "acceptance_quality_abstract_only_terminal"
ACCEPTANCE_QUALITY_PLOT_TRAILER_TERMINAL = "acceptance_quality_plot_trailer_terminal"

_TRAILER_PHRASE_PATTERNS_V1: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    (
        "everything_changes",
        re.compile(
            r"\b(?:nothing|everything)\s+(?:will\s+ever\s+be|is\s+about\s+to\s+be)\s+the\s+same\b",
            re.IGNORECASE,
        ),
    ),
    (
        "shadows_lengthen",
        re.compile(r"\b(?:shadows?|darkness)\s+(?:lengthen|deepen|gather)\b", re.IGNORECASE),
    ),
    (
        "little_do_they_know",
        re.compile(r"\b(?:little\s+do\s+(?:they|you)|unbeknownst)\b", re.IGNORECASE),
    ),
    (
        "game_is_afoot",
        re.compile(r"\b(?:game|war)\s+is\s+(?:afoot|only\s+beginning)\b", re.IGNORECASE),
    ),
    (
        "forces_align",
        re.compile(r"\b(?:forces|fates?)\s+(?:align|converge|collide)\b", re.IGNORECASE),
    ),
)

_TRAILER_PATTERN_TABLE: Dict[int, Tuple[Tuple[str, re.Pattern[str]], ...]] = {
    1: _TRAILER_PHRASE_PATTERNS_V1,
}

_ABSTRACT_ONLY_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    (
        "tension_remains",
        re.compile(
            r"^(?:[^.?!]*\b)?(?:the\s+)?tension\s+(?:remains|lingers|holds|thickens)\b[^.?!]*[.?!]\s*$",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "situation_worsens",
        re.compile(
            r"^(?:[^.?!]*\b)?(?:the\s+)?situation\s+(?:worsens|escalates|deteriorates)\b[^.?!]*[.?!]\s*$",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "stakes_rise_vague",
        re.compile(
            r"^(?:[^.?!]*\b)?(?:the\s+)?stakes?\s+(?:rise|grow|never\s+higher)\b[^.?!]*[.?!]\s*$",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "uncertainty_looms_vague",
        re.compile(
            r"^(?:[^.?!]*\b)?(?:uncertainty|dread)\s+(?:looms|gathers|deepens)\b[^.?!]*[.?!]\s*$",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
)

_STOPWORDS: frozenset[str] = frozenset(
    {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "if",
        "as",
        "at",
        "by",
        "for",
        "from",
        "in",
        "into",
        "of",
        "on",
        "to",
        "with",
        "you",
        "your",
        "their",
        "they",
        "them",
        "this",
        "that",
        "these",
        "those",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "it",
        "its",
    }
)

# Signal families: presence checks (multiple families beat fuzzy “richness”).
# Location tokens are noun-leaning; avoid bare ``keep`` (verb: "they keep watch") under IGNORECASE.
_FAMILY_LOCATION: re.Pattern[str] = re.compile(
    r"\b(?:room|hall|street|gate|dock|yard|square|market|wall|floor|ceiling|torch|door|window|"
    r"lane|road|bridge|river|harbor|wharf|quay|tavern|inn|chamber|court|battlements?|"
    r"checkpoint|barracks|alley|plaza|tower|the\s+keep|inner\s+keep|castle\s+keep|cellar|roof)\b",
    re.IGNORECASE,
)
_FAMILY_ACTOR: re.Pattern[str] = re.compile(
    r"\b(?:he|she|they)\s+(?:says|asks|mutters|snaps|nods|shrugs|gestures|points|turns|steps)\b|"
    r"\bthe\s+(?:captain|guard|guards|clerk|merchant|stranger|voice|figure|sergeant|watch)\b",
    re.IGNORECASE,
)
_FAMILY_PRESSURE: re.Pattern[str] = re.compile(
    r"\b(?:runs?|lunges?|draws?|strikes?|shouts?|pushes?|pulls?|retreats?|advances?|charges?|"
    r"collides?|panics?|trembles?|grips?|fires?|slashes?|parries?|breaks?|flees?|pursues?)\b",
    re.IGNORECASE,
)
_FAMILY_CONCRETE: re.Pattern[str] = re.compile(
    r"\b\d+\b|"
    r"\b(?:blood|steel|coin|coins?|ledger|keys?|knife|knives|rope|ashes?|smoke|mud|rain|dust|"
    r"iron|silver|gold|bronze|chest|crate|barrel|chain|manacles?)\b",
    re.IGNORECASE,
)

_FAMILY_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    ("location_physical", _FAMILY_LOCATION),
    ("actor_entity", _FAMILY_ACTOR),
    ("pressure_motion_conflict", _FAMILY_PRESSURE),
    ("concrete_sensory_object_action", _FAMILY_CONCRETE),
)

_FAMILY_BY_ID: Dict[str, re.Pattern[str]] = {fid: pat for fid, pat in _FAMILY_PATTERNS}


def _family_patterns_for_contract(contract: Mapping[str, Any]) -> Tuple[Tuple[str, re.Pattern[str]], ...]:
    """Subset and order of signal families from contract (deterministic; no hardcoded floor set)."""
    raw = contract.get("grounding_signal_family_ids")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or not raw:
        return _FAMILY_PATTERNS
    allowed = [str(x) for x in raw if str(x) in _FAMILY_BY_ID]
    if not allowed:
        return _FAMILY_PATTERNS
    return tuple((fid, _FAMILY_BY_ID[fid]) for fid in allowed)


def _count_families(text: str, families: Sequence[Tuple[str, re.Pattern[str]]]) -> Tuple[int, List[str]]:
    """Presence-only: each family counts at most once (not scoring)."""
    seen: List[str] = []
    for fid, pat in families:
        if pat.search(text):
            seen.append(fid)
    return len(seen), seen


def _significant_tokens(text: str) -> List[str]:
    raw = re.sub(r"[^\w\s]", " ", text.lower())
    out: List[str] = []
    for w in raw.split():
        if len(w) < 5 or w in _STOPWORDS:
            continue
        out.append(w)
    return out


def _split_sentences(norm_text: str) -> List[str]:
    if not norm_text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", norm_text.strip()) if s.strip()]


def _last_sentence(norm_text: str) -> str:
    sents = _split_sentences(norm_text)
    return sents[-1] if sents else ""


def _terminal_tail_text(norm_text: str, tail_n: int) -> str:
    sents = _split_sentences(norm_text)
    if not sents:
        return norm_text.strip()
    n = max(1, tail_n)
    return " ".join(sents[-n:]).strip()


def build_acceptance_quality_contract(
    *,
    enabled: bool = True,
    overrides: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build the N4 **Acceptance Quality** policy dict (contract resolution only).

    **Owns:** default field values, shallow merge of *overrides*, nested ``trace`` merge when both
    sides are mappings.

    **Returns:** A JSON-safe dict suitable for :func:`validate_acceptance_quality` and for the gate
    after planner overrides are merged.

    **Does not:** run validators, mutate candidate text, coerce unknown
    ``trailer_phrase_patterns_version`` values to a shipped table (unknown versions remain on the
    contract for observational handling in :func:`validate_acceptance_quality`).

    Thresholds are **narrow** predicates (signal-family counts, span heuristics)—not latent
    “quality” scoring or prose tiers.
    """
    base: Dict[str, Any] = {
        "enabled": bool(enabled),
        "version": ACCEPTANCE_QUALITY_VERSION,
        "require_grounding_floor": True,
        "forbid_single_anchor_collapse": True,
        "forbid_abstract_only_ending": True,
        "forbid_plot_trailer_close": True,
        "allow_minimal_tail_trim_repair": True,
        "allow_terminal_sentence_drop_repair": True,
        # At least this many distinct grounding families across the full candidate (when floor on).
        "minimum_grounding_signals": 2,
        # Collapse: require at least this many distinct significant tokens in the collapse window.
        "minimum_distinct_anchor_domains": 2,
        # Characters from the end of the candidate scanned for anchor repetition / density.
        "collapse_anchor_window": 220,
        # How many terminal sentences are eligible for abstract/trailer-only inspection (1 = last only).
        "abstract_tail_window": 1,
        "trailer_phrase_patterns_version": 1,
        "grounding_signal_family_ids": [fid for fid, _ in _FAMILY_PATTERNS],
        "trace": {
            "layer": "acceptance_quality",
            "n4_objective": True,
            "not_scoring": True,
            "not_evaluator": True,
        },
    }
    if isinstance(overrides, Mapping):
        for k, v in overrides.items():
            key = str(k)
            if key == "trace" and isinstance(v, Mapping) and isinstance(base.get("trace"), dict):
                merged = dict(base["trace"])
                merged.update(dict(v))
                base["trace"] = merged
            else:
                base[key] = v
    return base


def validate_acceptance_quality(text: str, contract: Mapping[str, Any]) -> Dict[str, Any]:
    """Pure N4 validation: deterministic predicates in, structured verdict out.

    **Owns:** pass/fail, ordered ``failure_reasons`` / ``reason_codes``, and an ``evidence`` dict
    (diagnostic fields, not a quality score).

    **Does not:** repair text, call the gate or FEM, import offline evaluators, or treat
    ``passed`` as holistic “good writing.”

    N4 is an **anti-collapse / playability floor**: it may **fail** thin or trailer-style closures
    rather than inventing grounding or polishing vague lines. Reason codes stay **sparse** so
    evidence supports inspection without becoming a parallel scoring channel.

    *contract* is normally from :func:`build_acceptance_quality_contract` (optionally merged with
    planner overrides at the gate). When ``trailer_phrase_patterns_version`` has no matching
    pattern table, evidence records ``trailer_phrase_patterns_version_unresolved`` and trailer
    phrase checks are skipped (observational, not a hard config fault by design).
    """
    failure_reasons: List[str] = []
    evidence: Dict[str, Any] = {}

    if not bool(contract.get("enabled", True)):
        return {
            "passed": True,
            "failure_reasons": [],
            "reason_codes": [],
            "evidence": {"skipped": True, "reason": ACCEPTANCE_QUALITY_CONTRACT_DISABLED},
        }

    norm = _normalize_text(text)
    if not norm:
        failure_reasons.append(ACCEPTANCE_QUALITY_EMPTY_TEXT)
        return {
            "passed": False,
            "failure_reasons": list(failure_reasons),
            "reason_codes": list(failure_reasons),
            "evidence": {"normalized_len": 0},
        }

    fam_patterns = _family_patterns_for_contract(contract)
    min_fam = max(1, int(contract.get("minimum_grounding_signals") or 2))

    if bool(contract.get("require_grounding_floor", True)):
        fam_count, fam_ids = _count_families(norm, fam_patterns)
        evidence["grounding_signal_families"] = list(fam_ids)
        evidence["grounding_signal_family_count"] = fam_count
        if fam_count < min_fam:
            failure_reasons.append(ACCEPTANCE_QUALITY_THIN_GROUNDING_FLOOR)

    if bool(contract.get("forbid_single_anchor_collapse", True)):
        window = max(40, int(contract.get("collapse_anchor_window") or 220))
        tail = norm[-window:] if len(norm) > window else norm
        fam_tail_count, fam_tail_ids = _count_families(tail, fam_patterns)
        evidence["collapse_window_family_count"] = fam_tail_count
        evidence["collapse_window_family_ids"] = list(fam_tail_ids)
        toks = _significant_tokens(tail)
        evidence["collapse_window_tokens"] = sorted(set(toks))[:24]
        distinct = len(set(toks))
        min_dom = max(1, int(contract.get("minimum_distinct_anchor_domains") or 2))
        thin_grounding_tail = fam_tail_count < min_fam
        anchor_token_skew = False
        if toks:
            counts: MutableMapping[str, int] = {}
            for t in toks:
                counts[t] = counts.get(t, 0) + 1
            top = max(counts.values())
            if len(toks) >= 4 and distinct < min_dom:
                anchor_token_skew = True
            elif len(toks) >= 6 and top / len(toks) >= 0.55:
                anchor_token_skew = True
                evidence["collapse_top_token_share"] = round(top / len(toks), 3)
        if thin_grounding_tail and anchor_token_skew:
            failure_reasons.append(ACCEPTANCE_QUALITY_SINGLE_ANCHOR_COLLAPSE)

    tail_n = max(1, int(contract.get("abstract_tail_window") or 1))
    close_scan = _terminal_tail_text(norm, tail_n)
    last_sent = _last_sentence(norm)

    if bool(contract.get("forbid_abstract_only_ending", True)) and last_sent.strip():
        abstract_hits: List[str] = []
        ls = last_sent.strip()
        for label, pat in _ABSTRACT_ONLY_PATTERNS:
            if pat.match(ls):
                abstract_hits.append(label)
        fam_last, fam_last_ids = _count_families(ls, fam_patterns)
        if abstract_hits and fam_last == 0:
            failure_reasons.append(ACCEPTANCE_QUALITY_ABSTRACT_ONLY_TERMINAL)
            evidence["abstract_only_patterns"] = sorted(abstract_hits)
            evidence["terminal_sentence_family_count"] = fam_last
            evidence["terminal_sentence_family_ids"] = list(fam_last_ids)

    if bool(contract.get("forbid_plot_trailer_close", True)) and close_scan.strip():
        trailer_hits: List[str] = []
        ver = int(contract.get("trailer_phrase_patterns_version") or 1)
        patterns = _TRAILER_PATTERN_TABLE.get(ver)
        if patterns is None:
            evidence["trailer_phrase_patterns_version_unresolved"] = ver
        else:
            evidence["trailer_phrase_patterns_version"] = ver
            for label, pat in patterns:
                if pat.search(close_scan):
                    trailer_hits.append(label)
            if trailer_hits:
                failure_reasons.append(ACCEPTANCE_QUALITY_PLOT_TRAILER_TERMINAL)
                evidence["trailer_phrase_patterns"] = sorted(trailer_hits)

    # Stable, minimal reason ordering: fixed check order, first hit per code only.
    deduped: List[str] = []
    seen_r: set[str] = set()
    for code in failure_reasons:
        if code not in seen_r:
            seen_r.add(code)
            deduped.append(code)

    passed = not deduped
    return {
        "passed": passed,
        "failure_reasons": list(deduped),
        "reason_codes": list(deduped),
        "evidence": evidence,
    }


def repair_acceptance_quality_minimal(
    text: str,
    contract: Mapping[str, Any],
    *,
    failure_reasons: Sequence[str],
) -> Tuple[str, Dict[str, Any]]:
    """Apply **bounded subtractive** N4 repair; does not re-validate.

    **Owns:** optional whitespace normalization and optional drop of the **terminal sentence** when
    policy and failure codes allow; returns possibly updated text plus ``repair_applied`` /
    ``repair_modes`` metadata.

    **Does not:** add tokens, paraphrase, merge sentences into new meaning, or “improve” prose for
    subjective quality—those would smuggle authoring/scoring into the emission boundary. Thin
    grounding and single-anchor failures are never “fixed” by sentence surgery here.

    **Caller must** run :func:`validate_acceptance_quality` again on the returned text (the packaged
    path is :func:`validate_and_repair_acceptance_quality`).

    Allowed (strict): normalize internal whitespace; drop last sentence only for abstract-only /
    plot-trailer terminal codes when at least two sentences exist and the remainder is non-empty.
    """
    meta: Dict[str, Any] = {"repair_applied": False, "repair_modes": []}
    reasons = {str(r) for r in failure_reasons}

    if not bool(contract.get("enabled", True)):
        return text, meta

    raw_in = str(text or "")
    if bool(contract.get("allow_minimal_tail_trim_repair", True)):
        trimmed = _normalize_text(text)
        # Any run of whitespace normalized (including internal runs); still not “rewriting”.
        if trimmed != " ".join(raw_in.strip().split()):
            meta["repair_applied"] = True
            meta["repair_modes"].append("normalize_whitespace")
            text = trimmed

    drop_ok = bool(contract.get("allow_terminal_sentence_drop_repair", True))
    droppable = reasons & {
        ACCEPTANCE_QUALITY_ABSTRACT_ONLY_TERMINAL,
        ACCEPTANCE_QUALITY_PLOT_TRAILER_TERMINAL,
    }
    # Drop only for trailer/abstract-terminal codes — never “repair away” thin grounding, empty
    # text, or collapse via sentence surgery (would hide floor failures or invent structure).
    if drop_ok and droppable:
        norm = _normalize_text(text)
        sents = _split_sentences(norm)
        if len(sents) >= 2:
            new_text = " ".join(sents[:-1]).strip()
            remainder = _split_sentences(new_text)
            if new_text and remainder:
                meta["repair_applied"] = True
                meta["repair_modes"].append("drop_terminal_sentence")
                return new_text, meta

    return text, meta


_TRACE_EVIDENCE_KEYS: frozenset[str] = frozenset(
    {
        "grounding_signal_family_count",
        "grounding_signal_families",
        "terminal_sentence_family_count",
        "terminal_sentence_family_ids",
        "abstract_only_patterns",
        "trailer_phrase_patterns",
        "trailer_phrase_patterns_version",
        "trailer_phrase_patterns_version_unresolved",
        "collapse_top_token_share",
        "collapse_window_family_count",
        "skipped",
        "reason",
        "normalized_len",
    }
)


def _compact_trace_evidence(evidence: Mapping[str, Any]) -> Dict[str, Any]:
    """Whitelist + cap lists for FEM: full ``evidence`` can be verbose; traces stay bounded."""
    slim: Dict[str, Any] = {}
    for key in sorted(_TRACE_EVIDENCE_KEYS):
        if key not in evidence:
            continue
        val = evidence[key]
        if isinstance(val, list):
            slim[key] = list(val)[:8]
        else:
            slim[key] = val
    return slim


def build_acceptance_quality_emission_trace(
    contract: Mapping[str, Any],
    validation: Mapping[str, Any],
    repair: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build the compact **N4 emission trace** dict for FEM (not the full validation payload).

    **Owns:** stable top-level keys the gate copies into ``acceptance_quality_trace`` / flat
    ``acceptance_quality_*`` FEM fields: version, checked, passed, reason codes, repair flag, and
    **slim** evidence via :func:`_compact_trace_evidence`.

    **Does not:** replace :func:`validate_acceptance_quality` output; raw ``evidence`` on the
    validation dict may carry fields omitted here on purpose. Legality remains on the validation
    object; this bundle is for observability and downstream merge only.
    """
    rep = repair or {}
    return {
        "acceptance_quality_version": int(contract.get("version") or ACCEPTANCE_QUALITY_VERSION),
        "acceptance_quality_checked": bool(contract.get("enabled", True)),
        "acceptance_quality_passed": bool(validation.get("passed")),
        "acceptance_quality_reason_codes": list(validation.get("reason_codes") or []),
        "acceptance_quality_repair_applied": bool(rep.get("repair_applied")),
        "acceptance_quality_evidence": _compact_trace_evidence(dict(validation.get("evidence") or {})),
    }


def validate_and_repair_acceptance_quality(
    text: str,
    contract: Mapping[str, Any],
) -> Dict[str, Any]:
    """Canonical N4 loop: validate → bounded repair (if needed) → re-validate → compact trace.

    **Returns:** ``text`` (possibly unchanged or whitespace-normalized or terminal-sentence dropped),
    ``validation`` (final pass), ``repair`` meta, and ``acceptance_quality_emission_trace`` for FEM.

    **Does not:** broaden repair beyond :func:`repair_acceptance_quality_minimal`, seal ``passed``
    without a fresh :func:`validate_acceptance_quality` call, or interpret evidence as scores.

    Prefer this entrypoint over ad-hoc repair plus a stale validation dict.
    """
    initial = validate_acceptance_quality(text, contract)
    repair_meta: Dict[str, Any] = {"repair_applied": False, "repair_modes": []}
    current_text = text
    if initial.get("passed"):
        final = initial
    else:
        current_text, repair_meta = repair_acceptance_quality_minimal(
            text,
            contract,
            failure_reasons=list(initial.get("reason_codes") or []),
        )
        if repair_meta.get("repair_applied"):
            final = validate_acceptance_quality(current_text, contract)
        else:
            final = initial
    trace = build_acceptance_quality_emission_trace(contract, final, repair_meta)
    return {
        "text": current_text,
        "validation": final,
        "repair": repair_meta,
        "acceptance_quality_emission_trace": trace,
    }
