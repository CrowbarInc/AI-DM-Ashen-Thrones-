"""Deterministic narrative planning artifact (Objective #2 foundation).

**Owner:** versioned, JSON-safe *Narrative Plan* construction and validation — a
bounded structural bridge between resolved-turn meaning (CTIR) and
expression-only narration (GPT). This module decides *what categories of
information* narration should respect, not *how* it is phrased.

**``allowable_entity_references`` (visibility-shaped, not focality):**

- **Contract — visible narration universe (outer boundary):** When callers pass
  ``published_entities`` (including ``[]``), each row is the strict published
  visibility slice. The plan field then lists **every** visible entity id in that
  slice (stable sorted order, capped by ``_MAX_ID_LIST``). It answers “which
  published handles may narration name this turn?”, **not** “whom should narration
  center on?”. Narrow turn focality lives in ``scene_anchors`` (e.g.
  ``active_interlocutor``, ``relevant_actors``, location tokens),
  ``narrative_mode`` / ``narrative_mode_contract``, ``active_pressures``,
  ``required_new_information``, ``role_allocation``, and ``narrative_roles``—consumers must not treat
  this list as a substitute for those fields.
- When ``published_entities`` is omitted (``None``), the field falls back to
  **CTIR-addressed** entity ids only (no visibility slice at the builder seam);
  integrated callers should normally pass the published slice from
  ``narration_visibility``.

**Derivative-only contract (non-negotiable):**

- Narrative Plan is a **deterministic projection** from CTIR (plus explicitly
  passed bounded slices: session interaction hints, public scene labels,
  published-entity allowlist, optional recent-event summaries, optional
  ``resolution_meta``). It is **never** a second semantic authority.
- **Objective N3 — ``narrative_roles``:** Abstract **composition-role** guidance
  (``location_anchor``, ``actor_anchor``, ``pressure``, ``hook``, ``consequence``)
  is a downstream **shaping** layer only: bounded bands, counts, closed-set
  signals, and structural kind-tags already validated under
  ``required_new_information``. It must **not** restate CTIR prose, embed prompt
  instructions, or re-adjudicate outcomes. On conflict, **CTIR** and shipped
  contracts (``narrative_mode_contract``, visibility slices) **win**; treat
  ``narrative_roles`` as expendable emphasis metadata. ``role_allocation`` remains
  the coarse integer emphasis axes; ``narrative_roles`` is the richer, still
  non-authoritative composition layer. Bounded one-step ``emphasis_band`` reinforcement
  for trusted plans is owned upstream by :func:`game.narrative_plan_upstream.apply_upstream_narrative_role_reemphasis`
  (bundle seam), not by this builder’s derivation rules.
- Callers must **not** use Narrative Plan as the source of truth for **state
  mutation, adjudication, routing, policy, or semantic resolution**. On any
  conflict between CTIR (or engine/session state CTIR represents) and a plan
  field, **CTIR wins**; the plan should be discarded or rebuilt from CTIR.
- Downstream prompt assembly may use the plan **only** as bounded structural
  guidance for narration shape (emphasis, anchors, category reminders). It must
  not reconstruct or override CTIR-rooted meaning.

**Not owner:** player- or GM-facing prose, prompt strings, instruction blocks,
model routing, or any text intended for LLM system/user messages.

**Not owner:** CTIR. CTIR remains the canonical resolved-turn semantics layer;
this module only consumes CTIR-shaped inputs and must not redefine resolution
meaning or duplicate CTIR sections as a second authority.

**Not owner:** final emission repairs, validators, or gate enforcement. Those
stay downstream of narration output.

**Not owner:** turn packet contracts, packet caching, or gate boundary snapshots
(:mod:`game.turn_packet`).

Downstream :mod:`game.prompt_context` (and similar) should treat plans built
here as *inputs* alongside CTIR, never as a replacement for CTIR or for prompt
authoring.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from game.ctir import looks_like_ctir
from game.narrative_mode_contract import (
    NARRATIVE_MODES,
    build_narrative_mode_contract,
    validate_narrative_mode_contract,
)
from game.opening_visible_fact_selection import opening_fact_primary_category

NARRATIVE_PLAN_VERSION = 1

# ``required_new_information[].kind`` values emitted by :func:`_derive_required_new_information` only.
# Used in strict validation so plans cannot carry invented semantic categories.
_REQUIRED_NEW_INFORMATION_KINDS = frozenset(
    {
        "resolution_kind",
        "outcome_type",
        "success_state",
        "state_change",
        "surfaced_clue",
        "authoritative_output_keys",
        "transition",
        "mutation",
        "consequence_atoms",
        "consequence_map",
    }
)

_MAX_STR_CLIP = 160
_MAX_ID_LIST = 48
_MAX_CODES = 64
_MAX_PRESSURE_BLOCK_KEYS = 16
_MAX_DEPTH_SCAN = 3

# Keys rejected anywhere in the plan tree (prose / prompt leakage guard).
_PROSE_INSTRUCTION_KEYS = frozenset(
    {
        "narration",
        "narrative",
        "narrative_text",
        "prose",
        "story",
        "description",
        "hint",
        "text",
        "player_facing_text",
        "prompt",
        "system_prompt",
        "user_prompt",
        "instructions",
        "instruction",
        "message",
        "messages",
    }
)

# Extra key names rejected under ``scene_opening`` (C1-A structural projection).
_SCENE_OPENING_PROSEISH_KEYS = frozenset(
    _PROSE_INSTRUCTION_KEYS
    | {
        "cinematic",
        "opener_line",
        "atmospheric",
        "neutral_opener",
        "fallback_opener",
        "fallback",
        "template",
    }
)

_SCENE_OPENING_REASONS = frozenset({"campaign_start", "scene_entry", "post_transition", "resume_entry", "none"})

_SCENE_OPENING_ALLOWED_TOP_KEYS = frozenset(
    {
        "opening_required",
        "opening_reason",
        "scene_id",
        "location_anchors",
        "actor_anchors",
        "active_pressures",
        "visible_fact_categories",
        "visible_fact_anchor_ids",
        "prohibited_content_codes",
        "derivation_codes",
        "validator",
    }
)

# Canonical machine codes only (expanded to instruction lines downstream in prompt assembly).
DEFAULT_SCENE_OPENING_PROHIBITED_CONTENT_CODES: Tuple[str, ...] = (
    "no_engine_role_label_as_proper_name",
    "no_unintroduced_offscene_npc_names",
    "no_backstage_plot_briefings",
    "no_hidden_gm_facts_as_immediate_perception",
    "no_unfounded_faction_control_claims",
)

_SCENE_OPENING_FALLBACK_MARKERS = (
    "neutral opener",
    "neutral_opener",
    "fallback opener",
    "fallback_opener",
    "fast_fallback",
    "template opener",
)


def narrative_plan_version() -> int:
    return NARRATIVE_PLAN_VERSION


def _as_str(v: Any) -> str:
    return str(v or "").strip()


def _clip(s: str, *, max_len: int = _MAX_STR_CLIP) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def _json_safe_atom(v: Any) -> Any:
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    return str(v)


def _sorted_unique_strs(items: Sequence[Any], *, limit: int) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for raw in items:
        s = _clip(_as_str(raw))
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
        if len(out) >= limit:
            break
    return sorted(out)


def _bounded_shallow_map(m: Mapping[str, Any] | None, *, max_keys: int) -> Dict[str, Any]:
    if not isinstance(m, Mapping):
        return {}
    out: Dict[str, Any] = {}
    keys = sorted(m.keys(), key=lambda k: str(k))[:max_keys]
    for k in keys:
        sk = _as_str(k)
        if not sk or sk.lower() in _PROSE_INSTRUCTION_KEYS:
            continue
        val = m.get(k)
        if isinstance(val, Mapping):
            out[sk] = _bounded_shallow_map(val, max_keys=max_keys)  # type: ignore[arg-type]
        elif isinstance(val, (list, tuple)):
            out[sk] = [_json_safe_atom(x) for x in list(val)[:_MAX_ID_LIST]]
        else:
            out[sk] = _json_safe_atom(val)
    return out


def _mapping(d: Any) -> Dict[str, Any]:
    return dict(d) if isinstance(d, Mapping) else {}


def _derive_scene_anchors(
    ctir: Mapping[str, Any],
    *,
    public_scene_slice: Mapping[str, Any] | None,
    session_interaction: Mapping[str, Any] | None,
) -> Tuple[Dict[str, Any], List[str]]:
    codes: List[str] = []
    ps = public_scene_slice if isinstance(public_scene_slice, Mapping) else {}
    si = session_interaction if isinstance(session_interaction, Mapping) else {}

    scene_id = _as_str(ctir.get("scene_id")) or None
    if not scene_id:
        scene_id = _as_str(ps.get("scene_id")) or None
    sm = _mapping(ctir.get("state_mutations")).get("scene")
    if isinstance(sm, Mapping) and not scene_id:
        scene_id = _as_str(sm.get("scene_id") or sm.get("activate_scene_id")) or None

    scene_name = _as_str(ps.get("scene_name") or ps.get("title")) or None
    if scene_name:
        scene_name = _clip(scene_name)
        codes.append("scene_name:public_slice")

    loc_raw = ps.get("location_tokens") or ps.get("location_anchors")
    if isinstance(loc_raw, (list, tuple)):
        location_anchors = _sorted_unique_strs(list(loc_raw), limit=16)
    elif isinstance(loc_raw, str) and loc_raw.strip():
        location_anchors = _sorted_unique_strs([loc_raw], limit=16)
    else:
        location_anchors = []

    ic = _mapping(ctir.get("interaction"))
    active_target = _as_str(ic.get("active_target_id")) or None
    if not active_target:
        active_target = _as_str(si.get("active_interaction_target_id")) or None
    if active_target:
        codes.append("active_target:resolved")

    interlocutor = active_target
    rt = ic.get("responder_target")
    if isinstance(rt, Mapping):
        rid = _as_str(rt.get("id") or rt.get("entity_id"))
        if rid:
            interlocutor = rid
            codes.append("interlocutor:responder_target")

    actors_out: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    for bucket_key in ("actors_speakers",):
        na = _mapping(ctir.get("narrative_anchors")).get(bucket_key)
        if not isinstance(na, list):
            continue
        for item in na[:_MAX_ID_LIST]:
            if not isinstance(item, Mapping):
                continue
            eid = _as_str(item.get("id") or item.get("entity_id"))
            if not eid or eid in seen_ids:
                continue
            seen_ids.add(eid)
            nm = _as_str(item.get("name") or item.get("display_name")) or None
            actors_out.append(
                {
                    "id": _clip(eid, max_len=96),
                    "name": _clip(nm, max_len=96) if nm else None,
                }
            )
            if len(actors_out) >= 24:
                break

    anchors = {
        "scene_id": scene_id,
        "scene_name": scene_name,
        "location_anchors": location_anchors,
        "active_interlocutor": _clip(interlocutor, max_len=96) if interlocutor else None,
        "active_target": _clip(active_target, max_len=96) if active_target else None,
        "relevant_actors": sorted(actors_out, key=lambda r: str(r.get("id") or "")),
    }
    return anchors, codes


def _derive_active_pressures(
    ctir: Mapping[str, Any],
    *,
    session_interaction: Mapping[str, Any] | None,
) -> Tuple[Dict[str, Any], List[str]]:
    codes: List[str] = []
    si = session_interaction if isinstance(session_interaction, Mapping) else {}
    res = _mapping(ctir.get("resolution"))
    nc = _mapping(ctir.get("noncombat"))
    nc_narr = nc.get("narration_constraints") if isinstance(nc.get("narration_constraints"), Mapping) else {}
    world = _mapping(ctir.get("world"))
    clues_block = _mapping(_mapping(ctir.get("state_mutations")).get("clues_leads"))

    pending: List[str] = []
    pl = si.get("pending_lead_ids")
    if isinstance(pl, (list, tuple)):
        pending.extend(_sorted_unique_strs(list(pl), limit=_MAX_ID_LIST))
    lid = clues_block.get("lead_ids")
    if isinstance(lid, (list, tuple)):
        pending.extend(_sorted_unique_strs(list(lid), limit=_MAX_ID_LIST))
    pending_lead_ids = _sorted_unique_strs(pending, limit=_MAX_ID_LIST)

    interaction_pressure = "none"
    soc = res.get("social")
    reply_expected = False
    if nc_narr and "npc_reply_expected" in nc_narr:
        reply_expected = bool(nc_narr.get("npc_reply_expected"))
    elif isinstance(soc, Mapping):
        reply_expected = bool(soc.get("npc_reply_expected"))
    if reply_expected:
        interaction_pressure = "reply_expected"
        codes.append("pressure:reply_expected")
    elif bool(nc.get("requires_check")) or bool(res.get("requires_check")) or bool(res.get("check_request")):
        interaction_pressure = "check_pending"
        codes.append("pressure:check_pending")

    tension_codes: List[str] = []
    rk_src = None
    if isinstance(nc_narr, Mapping):
        rk_src = nc_narr.get("reply_kind")
    if rk_src is None and isinstance(soc, Mapping):
        rk_src = soc.get("reply_kind")
    rk = _as_str(rk_src)
    if rk:
        tension_codes.append(_clip(f"social.reply_kind:{rk}", max_len=_MAX_STR_CLIP))
    intent = _mapping(ctir.get("intent"))
    if bool(intent.get("requires_check")):
        tension_codes.append("intent.requires_check")

    world_pressure: Dict[str, Any] | None = None
    wp = world.get("pressure")
    if isinstance(wp, Mapping):
        world_pressure = _bounded_shallow_map(wp, max_keys=_MAX_PRESSURE_BLOCK_KEYS)
        codes.append("world.pressure")
    elif wp is not None:
        world_pressure = {"value": _json_safe_atom(wp)}
        codes.append("world.pressure_atom")

    clock_summaries: List[Any] = []
    clocks = world.get("clocks")
    if isinstance(clocks, list):
        for c in clocks[:12]:
            if isinstance(c, Mapping):
                clock_summaries.append(_bounded_shallow_map(c, max_keys=8))
            else:
                clock_summaries.append(_json_safe_atom(c))
    elif isinstance(clocks, Mapping):
        clock_summaries.append(_bounded_shallow_map(clocks, max_keys=_MAX_PRESSURE_BLOCK_KEYS))

    ctx_codes = _sorted_unique_strs(
        [c for c in codes if c.startswith("pressure:") or c.startswith("world.")],
        limit=16,
    )

    return (
        {
            "pending_lead_ids": pending_lead_ids,
            "context_codes": ctx_codes,
            "interaction_pressure": interaction_pressure,
            "scene_tension_codes": _sorted_unique_strs(tension_codes, limit=16),
            "world_pressure": world_pressure,
            "clock_summaries": clock_summaries[:12],
        },
        codes,
    )


def _derive_required_new_information(ctir: Mapping[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    codes: List[str] = []
    items: List[Dict[str, Any]] = []
    res = _mapping(ctir.get("resolution"))
    sm = _mapping(ctir.get("state_mutations"))

    kind = _as_str(res.get("kind"))
    if kind:
        items.append({"kind": "resolution_kind", "value": _clip(kind, max_len=64)})
        codes.append("req:resolution_kind")

    ot = _as_str(res.get("outcome_type"))
    if ot:
        items.append({"kind": "outcome_type", "value": _clip(ot, max_len=64)})
        codes.append("req:outcome_type")

    ss = _as_str(res.get("success_state"))
    if ss:
        items.append({"kind": "success_state", "value": _clip(ss, max_len=64)})

    sc = res.get("state_changes")
    if isinstance(sc, Mapping):
        for key in sorted(sc.keys(), key=lambda x: str(x)):
            if bool(sc.get(key)):
                items.append({"kind": "state_change", "flag": _clip(_as_str(key), max_len=64)})
                codes.append("req:state_change")

    clue_id = res.get("clue_id")
    if clue_id is not None and _as_str(clue_id):
        items.append({"kind": "surfaced_clue", "clue_id": _clip(_as_str(clue_id), max_len=96)})
        codes.append("req:clue")

    auth = res.get("authoritative_outputs")
    if isinstance(auth, Mapping):
        keys = sorted(str(k) for k in auth.keys())[:16]
        if keys:
            items.append({"kind": "authoritative_output_keys", "keys": keys})
            codes.append("req:authoritative_outputs")

    rt = res.get("resolved_transition")
    if isinstance(rt, Mapping):
        items.append({"kind": "transition", "summary": _bounded_shallow_map(rt, max_keys=8)})
        codes.append("req:transition")
    elif rt is True or _as_str(res.get("target_scene_id")):
        tgt = _as_str(res.get("target_scene_id"))
        items.append({"kind": "transition", "target_scene_id": _clip(tgt, max_len=96) if tgt else None})
        codes.append("req:transition_target")

    for block_name in ("scene", "session", "combat"):
        block = sm.get(block_name)
        if not isinstance(block, Mapping):
            continue
        ck = block.get("changed_keys")
        if isinstance(ck, (list, tuple)):
            for key in _sorted_unique_strs(list(ck), limit=24):
                items.append({"kind": "mutation", "domain": block_name, "key": _clip(key, max_len=96)})
                codes.append("req:mutation")

    cons = res.get("consequences")
    if isinstance(cons, list) and cons:
        atoms = [_clip(_as_str(_json_safe_atom(x)), max_len=96) for x in cons[:12] if _as_str(_json_safe_atom(x))]
        if atoms:
            items.append({"kind": "consequence_atoms", "values": _sorted_unique_strs(atoms, limit=12)})
            codes.append("req:consequence_list")
    elif isinstance(cons, Mapping) and cons:
        items.append(
            {
                "kind": "consequence_map",
                "keys": sorted(str(k) for k in list(cons.keys())[:12]),
            }
        )
        codes.append("req:consequence_map")

    # Stable ordering: kind, then secondary fields
    def _sort_key(d: Mapping[str, Any]) -> Tuple[str, str]:
        return (_as_str(d.get("kind")), json.dumps(d, sort_keys=True))

    items_sorted = sorted(items, key=_sort_key)[:_MAX_ID_LIST]
    return items_sorted, codes


def _published_id_set(published_entities: Sequence[Mapping[str, Any]] | None) -> set[str]:
    out: set[str] = set()
    if not published_entities:
        return out
    for row in published_entities:
        if not isinstance(row, Mapping):
            continue
        eid = _as_str(row.get("entity_id") or row.get("id"))
        if eid:
            out.add(eid)
    return out


def _derive_allowable_entity_references(
    ctir: Mapping[str, Any],
    *,
    published_entities: Sequence[Mapping[str, Any]] | None,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Derive the visible narration-universe entity handle list (OPTION A).

    If *published_entities* is ``None``: emit CTIR-addressed entity ids only
    (interaction targets + ``narrative_anchors.actors_speakers``), sorted.

    If *published_entities* is provided (including ``[]``): treat it as the strict
    published-visibility allowlist. The result is the **full** allowlist (every
    row's id that passes bounds), merged with any CTIR descriptors for those same
    ids—**not** a CTIR-only subset. CTIR ids outside the allowlist are dropped.
    This field is an **outer boundary** for named handles; focality is elsewhere
    on the plan (``scene_anchors.active_interlocutor``, ``narrative_mode``, ``narrative_mode_contract``, etc.).
    """
    codes: List[str] = []
    publish_filter = published_entities is not None
    allow = _published_id_set(published_entities)
    codes.append("entity_filter:published_intersect" if publish_filter else "entity_filter:ctir_only")

    ic = _mapping(ctir.get("interaction"))
    candidates: Dict[str, Optional[str]] = {}

    def _add(eid: str, descriptor: Optional[str]) -> None:
        eid = _clip(_as_str(eid), max_len=96)
        if not eid:
            return
        if publish_filter and eid not in allow:
            return
        if eid not in candidates:
            candidates[eid] = _clip(_as_str(descriptor), max_len=96) if descriptor else None

    at = _as_str(ic.get("active_target_id"))
    if at:
        _add(at, None)

    for target_key in ("responder_target", "speaker_target"):
        t = ic.get(target_key)
        if isinstance(t, Mapping):
            eid = _as_str(t.get("id") or t.get("entity_id"))
            lab = _as_str(t.get("name") or t.get("display_name")) or None
            if eid:
                _add(eid, lab)

    na = _mapping(ctir.get("narrative_anchors")).get("actors_speakers")
    if isinstance(na, list):
        for item in na:
            if not isinstance(item, Mapping):
                continue
            eid = _as_str(item.get("id") or item.get("entity_id"))
            lab = _as_str(item.get("name") or item.get("display_name")) or None
            if eid:
                _add(eid, lab)

    if publish_filter:
        # Enumerate the full published visibility slice so the plan field reflects the
        # visible narration universe (OPTION A), not a CTIR-only focal subset.
        for row in published_entities or ():
            if not isinstance(row, Mapping):
                continue
            eid = _as_str(row.get("entity_id") or row.get("id"))
            if not eid or eid not in allow:
                continue
            lab = _as_str(row.get("display_name") or row.get("name")) or None
            _add(eid, lab)

    refs: List[Dict[str, Any]] = []
    for eid in sorted(candidates.keys()):
        refs.append({"entity_id": eid, "descriptor": candidates[eid]})
    return refs[:_MAX_ID_LIST], codes


# Integer weights (sum = 100): dialogue, exposition, outcome_forward, transition.
# These keys are role_allocation emphasis axes only (Objective #2 planning weights), not Objective #6 ``narrative_mode`` labels.
# ``outcome_forward`` is planning emphasis for resolved-result / state-change salience—not ``action_outcome`` mode.
_ROLE_WEIGHTS_BY_MODE: Dict[str, Tuple[int, int, int, int]] = {
    "opening": (12, 62, 14, 12),
    "continuation": (28, 32, 22, 18),
    "action_outcome": (8, 20, 62, 10),
    "dialogue": (58, 22, 12, 8),
    "transition": (8, 18, 12, 62),
    "exposition_answer": (12, 66, 12, 10),
}


def _derive_role_allocation(mode: str) -> Dict[str, int]:
    w = _ROLE_WEIGHTS_BY_MODE.get(mode) or _ROLE_WEIGHTS_BY_MODE["continuation"]
    d, e, o, t = w
    return {
        "dialogue": d,
        "exposition": e,
        "outcome_forward": o,
        "transition": t,
    }


# --- Objective N3: abstract composition roles (``narrative_roles``) ---

_EMPHASIS_BANDS = frozenset({"minimal", "low", "moderate", "elevated", "high"})

# Canonical five-role order (N3); shared with prompt_debug / tests — do not reorder casually.
NARRATIVE_ROLE_FAMILY_KEYS: tuple[str, ...] = (
    "location_anchor",
    "actor_anchor",
    "pressure",
    "hook",
    "consequence",
)
_NARRATIVE_ROLE_TOP_KEYS = NARRATIVE_ROLE_FAMILY_KEYS

_INTERACTION_PRESSURE_VALUES = frozenset({"none", "reply_expected", "check_pending"})

_OUTCOME_FORWARD_TIERS = frozenset({"none", "low", "mid", "elevated", "max"})

_LOCATION_ANCHOR_SIGNALS = frozenset(
    {
        "has_scene_id",
        "has_scene_label",
        "has_location_tokens",
        "multi_location_token",
        "mode_biases_scene_reanchor",
        "mode_biases_scene_setting",
        "exposition_axis_elevated",
        "transition_axis_elevated",
    }
)

_ACTOR_ANCHOR_SIGNALS = frozenset(
    {
        "interlocutor_resolved",
        "active_target_resolved",
        "multi_relevant_actor",
        "multi_visible_entity_handles",
        "dialogue_mode",
        "action_outcome_mode",
    }
)

_PRESSURE_ROLE_SIGNALS = frozenset(
    {
        "reply_pressure",
        "check_pressure",
        "pending_leads_nonempty",
        "context_codes_nonempty",
        "tension_codes_nonempty",
        "world_pressure_present",
        "clocks_present",
    }
)

_HOOK_ROLE_SIGNALS = frozenset(
    {
        "required_information_nonempty",
        "multi_information_kinds",
        "contract_disabled",
        "prompt_obligations_nonempty",
    }
)

_CONSEQUENCE_ROLE_SIGNALS = frozenset(
    {
        "consequence_information_present",
        "state_or_mutation_information_present",
        "transition_information_present",
        "outcome_forward_tier_elevated_or_max",
    }
)

_CONSEQUENCE_INFORMATION_KINDS = frozenset({"consequence_atoms", "consequence_map"})
_STATE_OR_MUTATION_INFORMATION_KINDS = frozenset(
    {"state_change", "mutation", "success_state", "outcome_type", "resolution_kind"}
)
_TRANSITION_INFORMATION_KINDS = frozenset({"transition"})

_MAX_NARRATIVE_ROLE_SIGNALS = 12
_MAX_INFORMATION_KIND_TAGS = 8


def _band_from_score(score: int) -> str:
    s = max(0, min(100, int(score)))
    if s < 18:
        return "minimal"
    if s < 36:
        return "low"
    if s < 55:
        return "moderate"
    if s < 74:
        return "elevated"
    return "high"


def _outcome_forward_tier(role_allocation: Mapping[str, Any]) -> str:
    raw = role_allocation.get("outcome_forward") if isinstance(role_allocation, Mapping) else None
    o = int(raw) if isinstance(raw, int) else 0
    o = max(0, min(100, o))
    if o >= 58:
        return "max"
    if o >= 42:
        return "elevated"
    if o >= 24:
        return "mid"
    if o > 0:
        return "low"
    return "none"


def _sorted_role_signals(raw: Sequence[str], *, allowed: frozenset[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for x in raw:
        sx = _as_str(x)
        if not sx or sx in seen or sx not in allowed:
            continue
        seen.add(sx)
        out.append(sx)
        if len(out) >= _MAX_NARRATIVE_ROLE_SIGNALS:
            break
    return sorted(out)


def derive_location_anchor_role(
    *,
    scene_anchors: Mapping[str, Any],
    narrative_mode: str,
    role_allocation: Mapping[str, Any],
) -> Tuple[Dict[str, Any], List[str]]:
    """Bounded composition hints for spatial/scene anchoring (N3)."""
    codes = ["nroles:location_anchor"]
    sa = scene_anchors if isinstance(scene_anchors, Mapping) else {}
    ra = role_allocation if isinstance(role_allocation, Mapping) else {}
    loc_raw = sa.get("location_anchors")
    loc_n = len(loc_raw) if isinstance(loc_raw, list) else 0
    loc_n = min(loc_n, 16)
    has_sid = bool(_as_str(sa.get("scene_id")))
    has_sname = bool(_as_str(sa.get("scene_name")))
    mode = _as_str(narrative_mode) or "continuation"
    expo = int(ra.get("exposition", 0)) if isinstance(ra.get("exposition"), int) else 0
    trans = int(ra.get("transition", 0)) if isinstance(ra.get("transition"), int) else 0

    signals: List[str] = []
    if has_sid:
        signals.append("has_scene_id")
    if has_sname:
        signals.append("has_scene_label")
    if loc_n:
        signals.append("has_location_tokens")
    if loc_n >= 2:
        signals.append("multi_location_token")
    if mode == "transition":
        signals.append("mode_biases_scene_reanchor")
    if mode == "opening":
        signals.append("mode_biases_scene_setting")
    if expo >= 50:
        signals.append("exposition_axis_elevated")
    if trans >= 45:
        signals.append("transition_axis_elevated")

    score = loc_n * 11 + (14 if has_sid else 0) + (12 if has_sname else 0)
    if mode == "transition":
        score += 38
    elif mode == "opening":
        score += 28
    elif mode == "exposition_answer":
        score += 22
    score += min(22, expo // 3)
    score += min(18, trans // 4)

    sig_f = _sorted_role_signals(signals, allowed=_LOCATION_ANCHOR_SIGNALS)
    band = _band_from_score(score)
    return (
        {
            "emphasis_band": band,
            "signals": sig_f,
            "location_token_n": loc_n,
            "scene_id_present": has_sid,
            "scene_label_present": has_sname,
        },
        codes,
    )


def derive_actor_anchor_role(
    *,
    scene_anchors: Mapping[str, Any],
    narrative_mode: str,
    allowable_entity_reference_n: int,
) -> Tuple[Dict[str, Any], List[str]]:
    """Bounded composition hints for actor / interlocutor anchoring (N3)."""
    codes = ["nroles:actor_anchor"]
    sa = scene_anchors if isinstance(scene_anchors, Mapping) else {}
    mode = _as_str(narrative_mode) or "continuation"
    interlocutor = _as_str(sa.get("active_interlocutor"))
    target = _as_str(sa.get("active_target"))
    rel = sa.get("relevant_actors") if isinstance(sa.get("relevant_actors"), list) else []
    rel_n = min(len(rel), 24)
    vis_n = max(0, min(int(allowable_entity_reference_n), _MAX_ID_LIST))

    signals: List[str] = []
    if interlocutor:
        signals.append("interlocutor_resolved")
    if target:
        signals.append("active_target_resolved")
    if rel_n >= 2:
        signals.append("multi_relevant_actor")
    if vis_n > 1:
        signals.append("multi_visible_entity_handles")
    if mode == "dialogue":
        signals.append("dialogue_mode")
    if mode == "action_outcome":
        signals.append("action_outcome_mode")

    score = (28 if interlocutor else 0) + (10 if target else 0) + min(24, rel_n * 6) + min(12, vis_n * 2)
    if mode == "dialogue":
        score += 34
    elif mode == "action_outcome":
        score += 18
    elif mode == "continuation" and interlocutor:
        score += 12

    sig_f = _sorted_role_signals(signals, allowed=_ACTOR_ANCHOR_SIGNALS)
    band = _band_from_score(score)
    return (
        {
            "emphasis_band": band,
            "signals": sig_f,
            "relevant_actor_n": rel_n,
            "interlocutor_present": bool(interlocutor),
            "visible_entity_handle_n": vis_n,
        },
        codes,
    )


def derive_pressure_role(
    *,
    active_pressures: Mapping[str, Any],
    narrative_mode: str,
) -> Tuple[Dict[str, Any], List[str]]:
    """Bounded composition hints for tension / obligation pressure (N3)."""
    codes = ["nroles:pressure"]
    ap = active_pressures if isinstance(active_pressures, Mapping) else {}
    mode = _as_str(narrative_mode) or "continuation"
    ip = _as_str(ap.get("interaction_pressure")) or "none"
    if ip not in _INTERACTION_PRESSURE_VALUES:
        ip = "none"
    pending = ap.get("pending_lead_ids") if isinstance(ap.get("pending_lead_ids"), list) else []
    p_n = min(len(pending), _MAX_ID_LIST)
    ctx = ap.get("context_codes") if isinstance(ap.get("context_codes"), list) else []
    tns = ap.get("scene_tension_codes") if isinstance(ap.get("scene_tension_codes"), list) else []
    ctx_n = min(len(ctx), _MAX_ID_LIST)
    tn_n = min(len(tns), 16)
    wp = ap.get("world_pressure")
    world_pressure_present = wp is not None and (bool(wp) if isinstance(wp, Mapping) else True)
    clocks = ap.get("clock_summaries") if isinstance(ap.get("clock_summaries"), list) else []
    clock_n = min(len(clocks), 12)

    signals: List[str] = []
    if ip == "reply_expected":
        signals.append("reply_pressure")
    if ip == "check_pending":
        signals.append("check_pressure")
    if p_n:
        signals.append("pending_leads_nonempty")
    if ctx_n:
        signals.append("context_codes_nonempty")
    if tn_n:
        signals.append("tension_codes_nonempty")
    if world_pressure_present:
        signals.append("world_pressure_present")
    if clock_n:
        signals.append("clocks_present")

    score = p_n * 5 + ctx_n * 3 + tn_n * 4 + (22 if ip != "none" else 0) + (16 if world_pressure_present else 0)
    score += min(14, clock_n * 3)
    if mode == "dialogue" and ip == "reply_expected":
        score += 12
    if mode == "action_outcome":
        score += 8

    sig_f = _sorted_role_signals(signals, allowed=_PRESSURE_ROLE_SIGNALS)
    band = _band_from_score(score)
    return (
        {
            "emphasis_band": band,
            "signals": sig_f,
            "interaction_pressure": ip,
            "pending_lead_n": p_n,
            "context_code_n": ctx_n,
            "tension_code_n": tn_n,
            "world_pressure_present": world_pressure_present,
            "clock_summary_n": clock_n,
        },
        codes,
    )


def derive_hook_role(
    *,
    required_new_information: Sequence[Mapping[str, Any]],
    narrative_mode_contract: Mapping[str, Any],
) -> Tuple[Dict[str, Any], List[str]]:
    """Bounded composition hints for forward-pull / novelty surfacing (N3)."""
    codes = ["nroles:hook"]
    rni = [x for x in required_new_information if isinstance(x, Mapping)]
    kinds: List[str] = []
    seen_k: set[str] = set()
    for row in rni:
        k = _as_str(row.get("kind"))
        if k and k in _REQUIRED_NEW_INFORMATION_KINDS and k not in seen_k:
            seen_k.add(k)
            kinds.append(k)
    kinds.sort()
    kind_tags = kinds[:_MAX_INFORMATION_KIND_TAGS]
    n_rni = min(len(rni), _MAX_ID_LIST)
    distinct_k = len(seen_k)

    nmc = narrative_mode_contract if isinstance(narrative_mode_contract, Mapping) else {}
    enabled = nmc.get("enabled")
    contract_disabled = isinstance(enabled, bool) and not enabled
    po = nmc.get("prompt_obligations") if isinstance(nmc.get("prompt_obligations"), Mapping) else {}
    po_n = len([k for k in po.keys() if isinstance(k, str) and _as_str(k)]) if isinstance(po, Mapping) else 0
    po_n = min(po_n, 48)

    signals: List[str] = []
    if n_rni:
        signals.append("required_information_nonempty")
    if distinct_k >= 2:
        signals.append("multi_information_kinds")
    if contract_disabled:
        signals.append("contract_disabled")
    if po_n:
        signals.append("prompt_obligations_nonempty")

    score = min(40, n_rni * 5) + min(28, distinct_k * 7) + (18 if po_n else 0)
    if contract_disabled:
        score = max(0, score - 12)

    sig_f = _sorted_role_signals(signals, allowed=_HOOK_ROLE_SIGNALS)
    band = _band_from_score(score)
    return (
        {
            "emphasis_band": band,
            "signals": sig_f,
            "required_new_information_n": n_rni,
            "distinct_information_kind_n": distinct_k,
            "information_kind_tags": kind_tags,
            "narrative_mode_contract_enabled": (bool(enabled) if isinstance(enabled, bool) else None),
            "prompt_obligation_key_n": po_n,
        },
        codes,
    )


def derive_consequence_role(
    *,
    required_new_information: Sequence[Mapping[str, Any]],
    role_allocation: Mapping[str, Any],
    narrative_mode: str,
) -> Tuple[Dict[str, Any], List[str]]:
    """Bounded composition hints for outcome / state-forward salience (N3)."""
    codes = ["nroles:consequence"]
    rni = [x for x in required_new_information if isinstance(x, Mapping)]
    kinds = {_as_str(x.get("kind")) for x in rni if _as_str(x.get("kind")) in _REQUIRED_NEW_INFORMATION_KINDS}
    has_cons = bool(kinds & _CONSEQUENCE_INFORMATION_KINDS)
    has_state = bool(kinds & _STATE_OR_MUTATION_INFORMATION_KINDS)
    has_tr = bool(kinds & _TRANSITION_INFORMATION_KINDS)

    tier = _outcome_forward_tier(role_allocation)
    mode = _as_str(narrative_mode) or "continuation"

    signals: List[str] = []
    if has_cons:
        signals.append("consequence_information_present")
    if has_state:
        signals.append("state_or_mutation_information_present")
    if has_tr:
        signals.append("transition_information_present")
    if tier in ("elevated", "max"):
        signals.append("outcome_forward_tier_elevated_or_max")

    score = (26 if has_cons else 0) + (22 if has_state else 0) + (20 if has_tr else 0)
    if tier == "max":
        score += 36
    elif tier == "elevated":
        score += 28
    elif tier == "mid":
        score += 16
    elif tier == "low":
        score += 8
    if mode == "action_outcome":
        score += 14
    elif mode == "transition":
        score += 10

    sig_f = _sorted_role_signals(signals, allowed=_CONSEQUENCE_ROLE_SIGNALS)
    band = _band_from_score(score)
    return (
        {
            "emphasis_band": band,
            "signals": sig_f,
            "outcome_forward_tier": tier,
            "has_consequence_information": has_cons,
            "has_state_or_mutation_information": has_state,
            "has_transition_information": has_tr,
        },
        codes,
    )


def derive_narrative_roles_composition(
    *,
    scene_anchors: Mapping[str, Any],
    active_pressures: Mapping[str, Any],
    required_new_information: Sequence[Mapping[str, Any]],
    narrative_mode: str,
    narrative_mode_contract: Mapping[str, Any],
    allowable_entity_references: Sequence[Mapping[str, Any]],
    role_allocation: Mapping[str, Any],
) -> Tuple[Dict[str, Any], List[str]]:
    """Assemble the full ``narrative_roles`` block in one deterministic pass (N3)."""
    aer_n = len([x for x in allowable_entity_references if isinstance(x, Mapping)])
    aer_n = min(aer_n, _MAX_ID_LIST)
    loc, c1 = derive_location_anchor_role(
        scene_anchors=scene_anchors, narrative_mode=narrative_mode, role_allocation=role_allocation
    )
    act, c2 = derive_actor_anchor_role(
        scene_anchors=scene_anchors, narrative_mode=narrative_mode, allowable_entity_reference_n=aer_n
    )
    prs, c3 = derive_pressure_role(active_pressures=active_pressures, narrative_mode=narrative_mode)
    hk, c4 = derive_hook_role(
        required_new_information=required_new_information, narrative_mode_contract=narrative_mode_contract
    )
    cns, c5 = derive_consequence_role(
        required_new_information=required_new_information,
        role_allocation=role_allocation,
        narrative_mode=narrative_mode,
    )
    merged = _merge_derivation_codes([c1, c2, c3, c4, c5])
    return (
        {
            "location_anchor": loc,
            "actor_anchor": act,
            "pressure": prs,
            "hook": hk,
            "consequence": cns,
        },
        merged,
    )


def narrative_roles_emphasis_band_map(narrative_roles: Mapping[str, Any] | None) -> dict[str, str]:
    """Return family → ``emphasis_band`` in canonical N3 order (harness / logs / quick diffs).

    Empty mapping when *narrative_roles* is missing or malformed. Omitted families are skipped
    (partial dicts are tolerated); only non-empty string bands are recorded.
    """
    if not isinstance(narrative_roles, Mapping):
        return {}
    out: dict[str, str] = {}
    for rk in NARRATIVE_ROLE_FAMILY_KEYS:
        sub = narrative_roles.get(rk)
        if not isinstance(sub, Mapping):
            continue
        b = sub.get("emphasis_band")
        if isinstance(b, str) and b.strip():
            out[rk] = b.strip()
    return out


def _validate_narrative_roles(nr: Any) -> Optional[str]:
    if not isinstance(nr, Mapping):
        return "narrative_roles_not_mapping"
    keys = set(nr.keys())
    if keys != set(_NARRATIVE_ROLE_TOP_KEYS):
        return f"narrative_roles_bad_keys:{sorted(keys)}"

    def _band_ok(b: Any) -> bool:
        return isinstance(b, str) and b in _EMPHASIS_BANDS

    def _sig_list(v: Any, allowed: frozenset[str]) -> Optional[str]:
        if not isinstance(v, list):
            return "signals_not_list"
        if len(v) > _MAX_NARRATIVE_ROLE_SIGNALS:
            return "signals_too_long"
        for i, s in enumerate(v):
            if not isinstance(s, str) or s not in allowed:
                return f"bad_signal:{i}"
        if v != sorted(v):
            return "signals_not_sorted"
        return None

    la = nr.get("location_anchor")
    if not isinstance(la, Mapping):
        return "location_anchor_not_mapping"
    la_keys = set(la.keys())
    if la_keys != {"emphasis_band", "signals", "location_token_n", "scene_id_present", "scene_label_present"}:
        return f"location_anchor_bad_keys:{sorted(la_keys)}"
    if not _band_ok(la.get("emphasis_band")):
        return "location_anchor_bad_band"
    err = _sig_list(la.get("signals"), _LOCATION_ANCHOR_SIGNALS)
    if err:
        return f"location_anchor_{err}"
    ltn = la.get("location_token_n")
    if not isinstance(ltn, int) or ltn < 0 or ltn > 16:
        return "location_anchor_bad_location_token_n"
    for fld in ("scene_id_present", "scene_label_present"):
        if not isinstance(la.get(fld), bool):
            return f"location_anchor_bad_bool:{fld}"

    aa = nr.get("actor_anchor")
    if not isinstance(aa, Mapping):
        return "actor_anchor_not_mapping"
    aa_keys = set(aa.keys())
    if aa_keys != {"emphasis_band", "signals", "relevant_actor_n", "interlocutor_present", "visible_entity_handle_n"}:
        return f"actor_anchor_bad_keys:{sorted(aa_keys)}"
    if not _band_ok(aa.get("emphasis_band")):
        return "actor_anchor_bad_band"
    err = _sig_list(aa.get("signals"), _ACTOR_ANCHOR_SIGNALS)
    if err:
        return f"actor_anchor_{err}"
    ran = aa.get("relevant_actor_n")
    if not isinstance(ran, int) or ran < 0 or ran > 24:
        return "actor_anchor_bad_relevant_actor_n"
    if not isinstance(aa.get("interlocutor_present"), bool):
        return "actor_anchor_bad_interlocutor_present"
    vhn = aa.get("visible_entity_handle_n")
    if not isinstance(vhn, int) or vhn < 0 or vhn > _MAX_ID_LIST:
        return "actor_anchor_bad_visible_entity_handle_n"

    pr = nr.get("pressure")
    if not isinstance(pr, Mapping):
        return "pressure_not_mapping"
    pr_keys = set(pr.keys())
    if pr_keys != {
        "emphasis_band",
        "signals",
        "interaction_pressure",
        "pending_lead_n",
        "context_code_n",
        "tension_code_n",
        "world_pressure_present",
        "clock_summary_n",
    }:
        return f"pressure_bad_keys:{sorted(pr_keys)}"
    if not _band_ok(pr.get("emphasis_band")):
        return "pressure_bad_band"
    err = _sig_list(pr.get("signals"), _PRESSURE_ROLE_SIGNALS)
    if err:
        return f"pressure_{err}"
    ip = pr.get("interaction_pressure")
    if not isinstance(ip, str) or ip not in _INTERACTION_PRESSURE_VALUES:
        return "pressure_bad_interaction_pressure"
    for fld, hi in (
        ("pending_lead_n", _MAX_ID_LIST),
        ("context_code_n", _MAX_ID_LIST),
        ("tension_code_n", 16),
        ("clock_summary_n", 12),
    ):
        vv = pr.get(fld)
        if not isinstance(vv, int) or vv < 0 or vv > hi:
            return f"pressure_bad_{fld}"
    if not isinstance(pr.get("world_pressure_present"), bool):
        return "pressure_bad_world_pressure_present"

    hk = nr.get("hook")
    if not isinstance(hk, Mapping):
        return "hook_not_mapping"
    hk_keys = set(hk.keys())
    if hk_keys != {
        "emphasis_band",
        "signals",
        "required_new_information_n",
        "distinct_information_kind_n",
        "information_kind_tags",
        "narrative_mode_contract_enabled",
        "prompt_obligation_key_n",
    }:
        return f"hook_bad_keys:{sorted(hk_keys)}"
    if not _band_ok(hk.get("emphasis_band")):
        return "hook_bad_band"
    err = _sig_list(hk.get("signals"), _HOOK_ROLE_SIGNALS)
    if err:
        return f"hook_{err}"
    rnin = hk.get("required_new_information_n")
    if not isinstance(rnin, int) or rnin < 0 or rnin > _MAX_ID_LIST:
        return "hook_bad_required_new_information_n"
    dkn = hk.get("distinct_information_kind_n")
    if not isinstance(dkn, int) or dkn < 0 or dkn > len(_REQUIRED_NEW_INFORMATION_KINDS):
        return "hook_bad_distinct_information_kind_n"
    ikt = hk.get("information_kind_tags")
    if not isinstance(ikt, list) or len(ikt) > _MAX_INFORMATION_KIND_TAGS:
        return "hook_bad_information_kind_tags"
    for i, tag in enumerate(ikt):
        if not isinstance(tag, str) or tag not in _REQUIRED_NEW_INFORMATION_KINDS:
            return f"hook_bad_information_kind_tag:{i}"
    if ikt != sorted(ikt):
        return "hook_information_kind_tags_not_sorted"
    nmc_en = hk.get("narrative_mode_contract_enabled")
    if nmc_en is not None and not isinstance(nmc_en, bool):
        return "hook_bad_narrative_mode_contract_enabled"
    pok = hk.get("prompt_obligation_key_n")
    if not isinstance(pok, int) or pok < 0 or pok > 48:
        return "hook_bad_prompt_obligation_key_n"

    cn = nr.get("consequence")
    if not isinstance(cn, Mapping):
        return "consequence_not_mapping"
    cn_keys = set(cn.keys())
    if cn_keys != {
        "emphasis_band",
        "signals",
        "outcome_forward_tier",
        "has_consequence_information",
        "has_state_or_mutation_information",
        "has_transition_information",
    }:
        return f"consequence_bad_keys:{sorted(cn_keys)}"
    if not _band_ok(cn.get("emphasis_band")):
        return "consequence_bad_band"
    err = _sig_list(cn.get("signals"), _CONSEQUENCE_ROLE_SIGNALS)
    if err:
        return f"consequence_{err}"
    oft = cn.get("outcome_forward_tier")
    if not isinstance(oft, str) or oft not in _OUTCOME_FORWARD_TIERS:
        return "consequence_bad_outcome_forward_tier"
    for fld in (
        "has_consequence_information",
        "has_state_or_mutation_information",
        "has_transition_information",
    ):
        if not isinstance(cn.get(fld), bool):
            return f"consequence_bad_bool:{fld}"

    return None


def _validate_narrative_roles_plan_slices(plan: Mapping[str, Any]) -> Optional[str]:
    """Ensure ``narrative_roles`` counters match sibling plan slices (anti-tamper, post-structural)."""
    nr = plan.get("narrative_roles")
    if not isinstance(nr, Mapping):
        return None
    sa = plan.get("scene_anchors")
    ap = plan.get("active_pressures")
    rni = plan.get("required_new_information")
    aer = plan.get("allowable_entity_references")
    nmc = plan.get("narrative_mode_contract")
    if not isinstance(sa, Mapping) or not isinstance(ap, Mapping):
        return "narrative_roles_slice_context_missing"

    la = nr.get("location_anchor")
    if isinstance(la, Mapping):
        loc = sa.get("location_anchors")
        loc_n = len(loc) if isinstance(loc, list) else 0
        if int(la.get("location_token_n", -1)) != min(loc_n, 16):
            return "narrative_roles_location_token_n_mismatch"
        if bool(la.get("scene_id_present")) != bool(_as_str(sa.get("scene_id"))):
            return "narrative_roles_scene_id_present_mismatch"
        if bool(la.get("scene_label_present")) != bool(_as_str(sa.get("scene_name"))):
            return "narrative_roles_scene_label_present_mismatch"

    aa = nr.get("actor_anchor")
    if isinstance(aa, Mapping):
        rel = sa.get("relevant_actors")
        rel_n = len(rel) if isinstance(rel, list) else 0
        if int(aa.get("relevant_actor_n", -1)) != min(rel_n, 24):
            return "narrative_roles_relevant_actor_n_mismatch"
        inter = bool(_as_str(sa.get("active_interlocutor")))
        if bool(aa.get("interlocutor_present")) != inter:
            return "narrative_roles_interlocutor_present_mismatch"
        aer_n = len([x for x in (aer if isinstance(aer, list) else []) if isinstance(x, Mapping)])
        if int(aa.get("visible_entity_handle_n", -1)) != min(aer_n, _MAX_ID_LIST):
            return "narrative_roles_visible_entity_handle_n_mismatch"

    pr = nr.get("pressure")
    if isinstance(pr, Mapping):
        ip_plan = _as_str(ap.get("interaction_pressure")) or "none"
        if ip_plan not in _INTERACTION_PRESSURE_VALUES:
            ip_plan = "none"
        if _as_str(pr.get("interaction_pressure")) != ip_plan:
            return "narrative_roles_interaction_pressure_mismatch"
        pl = ap.get("pending_lead_ids")
        pl_n = len(pl) if isinstance(pl, list) else 0
        if int(pr.get("pending_lead_n", -1)) != min(pl_n, _MAX_ID_LIST):
            return "narrative_roles_pending_lead_n_mismatch"
        ctx = ap.get("context_codes")
        ctx_n = len(ctx) if isinstance(ctx, list) else 0
        if int(pr.get("context_code_n", -1)) != min(ctx_n, _MAX_ID_LIST):
            return "narrative_roles_context_code_n_mismatch"
        tns = ap.get("scene_tension_codes")
        tn_n = len(tns) if isinstance(tns, list) else 0
        if int(pr.get("tension_code_n", -1)) != min(tn_n, 16):
            return "narrative_roles_tension_code_n_mismatch"
        wp = ap.get("world_pressure")
        wpp = wp is not None and (bool(wp) if isinstance(wp, Mapping) else True)
        if bool(pr.get("world_pressure_present")) != wpp:
            return "narrative_roles_world_pressure_present_mismatch"
        cl = ap.get("clock_summaries")
        cn = len(cl) if isinstance(cl, list) else 0
        if int(pr.get("clock_summary_n", -1)) != min(cn, 12):
            return "narrative_roles_clock_summary_n_mismatch"

    hk = nr.get("hook")
    if isinstance(hk, Mapping) and isinstance(rni, list):
        rni_maps = [x for x in rni if isinstance(x, Mapping)]
        if int(hk.get("required_new_information_n", -1)) != min(len(rni_maps), _MAX_ID_LIST):
            return "narrative_roles_required_new_information_n_mismatch"
        kinds_set = {
            _as_str(x.get("kind")) for x in rni_maps if _as_str(x.get("kind")) in _REQUIRED_NEW_INFORMATION_KINDS
        }
        if int(hk.get("distinct_information_kind_n", -1)) != len(kinds_set):
            return "narrative_roles_distinct_information_kind_n_mismatch"
        tags = hk.get("information_kind_tags")
        if isinstance(tags, list) and not set(tags).issubset(kinds_set):
            return "narrative_roles_hook_tags_not_subset_of_rni"

    if isinstance(hk, Mapping) and isinstance(nmc, Mapping):
        en = nmc.get("enabled")
        hook_en = hk.get("narrative_mode_contract_enabled")
        if hook_en is not None:
            if not isinstance(en, bool) or hook_en != en:
                return "narrative_roles_contract_enabled_mismatch"
        po = nmc.get("prompt_obligations")
        po_n = 0
        if isinstance(po, Mapping):
            po_n = len([k for k in po.keys() if isinstance(k, str) and _as_str(k)])
        po_n = min(po_n, 48)
        if int(hk.get("prompt_obligation_key_n", -1)) != po_n:
            return "narrative_roles_prompt_obligation_key_n_mismatch"

    cn = nr.get("consequence")
    if isinstance(cn, Mapping) and isinstance(rni, list):
        rni_maps = [x for x in rni if isinstance(x, Mapping)]
        kinds = {_as_str(x.get("kind")) for x in rni_maps if _as_str(x.get("kind")) in _REQUIRED_NEW_INFORMATION_KINDS}
        if bool(cn.get("has_consequence_information")) != bool(kinds & _CONSEQUENCE_INFORMATION_KINDS):
            return "narrative_roles_has_consequence_information_mismatch"
        if bool(cn.get("has_state_or_mutation_information")) != bool(kinds & _STATE_OR_MUTATION_INFORMATION_KINDS):
            return "narrative_roles_has_state_or_mutation_information_mismatch"
        if bool(cn.get("has_transition_information")) != bool(kinds & _TRANSITION_INFORMATION_KINDS):
            return "narrative_roles_has_transition_information_mismatch"

    return None


def _compress_recent_events(events: Sequence[Mapping[str, Any]] | None) -> List[Dict[str, Any]]:
    if not events:
        return []
    out: List[Dict[str, Any]] = []
    for ev in list(events)[:12]:
        if not isinstance(ev, Mapping):
            continue
        slim = _bounded_shallow_map(ev, max_keys=8)
        if slim:
            out.append(slim)
    return out


def _merge_derivation_codes(parts: Sequence[Sequence[str]]) -> List[str]:
    merged: List[str] = []
    seen: set[str] = set()
    for seq in parts:
        for c in seq:
            cc = _clip(_as_str(c), max_len=120)
            if not cc or cc in seen:
                continue
            seen.add(cc)
            merged.append(cc)
            if len(merged) >= _MAX_CODES:
                return merged
    return merged


def infer_scene_opening_reason(
    ctir: Mapping[str, Any],
    *,
    narration_obligations: Mapping[str, Any] | None = None,
    session_interaction: Mapping[str, Any] | None = None,
) -> str:
    """Closed-set ``opening_reason`` string (same rules as plan ``scene_opening``).

    Used at runtime seams (bundle audit) to know whether a turn requires a plan-backed
    ``scene_opening`` without duplicating ad-hoc opening detection outside this module.
    """
    r, _ = _derive_opening_reason(
        ctir, narration_obligations=narration_obligations, session_interaction=session_interaction
    )
    return r


def _derive_opening_reason(
    ctir: Mapping[str, Any],
    *,
    narration_obligations: Mapping[str, Any] | None,
    session_interaction: Mapping[str, Any] | None,
) -> Tuple[str, List[str]]:
    """Closed-set opening_reason from CTIR + narration_obligations + session_interaction only."""
    codes: List[str] = []
    no = narration_obligations if isinstance(narration_obligations, Mapping) else {}
    si = session_interaction if isinstance(session_interaction, Mapping) else {}
    res = _mapping(ctir.get("resolution"))
    sc = _mapping(res.get("state_changes"))

    if bool(si.get("resume_entry")):
        codes.append("opening_reason:resume_entry")
        return "resume_entry", codes

    action_id = _as_str(res.get("action_id"))
    campaign_start = bool(sc.get("opening_scene_turn")) or action_id == "campaign_start_opening_scene"
    if campaign_start:
        codes.append("opening_reason:campaign_start")
        return "campaign_start", codes

    has_tr = bool(res.get("resolved_transition")) or bool(_as_str(res.get("target_scene_id"))) or bool(
        sc.get("scene_transition_occurred") or sc.get("arrived_at_scene") or sc.get("new_scene_context_available")
    )
    if has_tr:
        codes.append("opening_reason:post_transition")
        return "post_transition", codes

    if bool(no.get("is_opening_scene")):
        codes.append("opening_reason:scene_entry")
        return "scene_entry", codes

    codes.append("opening_reason:none")
    return "none", codes


def _scene_opening_anchor_requirements(
    ctir: Mapping[str, Any],
    *,
    public_scene_slice: Mapping[str, Any] | None,
    scene_anchors: Mapping[str, Any],
) -> Tuple[bool, bool]:
    """(require_scene_id, require_location_anchors) when merged anchors / slices carry those signals."""
    ps = public_scene_slice if isinstance(public_scene_slice, Mapping) else {}
    sa = scene_anchors if isinstance(scene_anchors, Mapping) else {}
    need_sid = bool(
        _as_str(sa.get("scene_id")) or _as_str(ctir.get("scene_id")) or _as_str(ps.get("scene_id"))
    )
    loc_sa = sa.get("location_anchors") if isinstance(sa.get("location_anchors"), list) else []
    need_loc = any(bool(_as_str(x)) for x in loc_sa)
    if not need_loc:
        loc_raw = ps.get("location_tokens") or ps.get("location_anchors")
        if isinstance(loc_raw, (list, tuple)):
            need_loc = any(bool(_as_str(x)) for x in loc_raw)
        elif isinstance(loc_raw, str) and loc_raw.strip():
            need_loc = True
    return need_sid, need_loc


def _derive_scene_opening_actor_anchors(scene_anchors: Mapping[str, Any]) -> Tuple[List[Dict[str, Any]], List[str]]:
    codes: List[str] = []
    sa = scene_anchors if isinstance(scene_anchors, Mapping) else {}
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    inter = _as_str(sa.get("active_interlocutor"))
    if inter:
        eid = _clip(inter, max_len=96)
        out.append({"entity_id": eid, "anchor_role": "interlocutor"})
        seen.add(eid)
        codes.append("actor_anchor:interlocutor")
    rel = sa.get("relevant_actors") if isinstance(sa.get("relevant_actors"), list) else []
    for item in rel[:24]:
        if not isinstance(item, Mapping):
            continue
        eid = _clip(_as_str(item.get("id") or item.get("entity_id")), max_len=96)
        if not eid or eid in seen:
            continue
        seen.add(eid)
        out.append({"entity_id": eid, "anchor_role": "relevant_actor"})
        codes.append("actor_anchor:relevant_actor")
    out.sort(key=lambda r: (str(r.get("anchor_role")), str(r.get("entity_id"))))
    return out[:24], codes


def _visible_fact_opening_projection(
    opening_visible_fact_strings: Sequence[str] | None,
) -> Tuple[List[str], List[str], List[str]]:
    """Derive category tags + stable slot anchor ids from curated visible-fact strings (upstream-selected only)."""
    codes: List[str] = []
    if not opening_visible_fact_strings:
        return [], [], codes
    cats_acc: set[str] = set()
    anchors: List[str] = []
    for i, raw in enumerate(list(opening_visible_fact_strings)[:12]):
        if not isinstance(raw, str) or not raw.strip():
            continue
        norm = " ".join(raw.split())
        cat = opening_fact_primary_category(norm)
        cats_acc.add(cat)
        anchors.append(f"vf_slot:{i}")
        codes.append(f"visible_fact:cat:{cat}")
    return sorted(cats_acc), sorted(anchors), codes


def _deep_copy_jsonish(v: Any) -> Any:
    try:
        return json.loads(json.dumps(v, sort_keys=True))
    except (TypeError, ValueError):
        return v


def _derive_scene_opening(
    ctir: Mapping[str, Any],
    *,
    narration_obligations: Mapping[str, Any] | None,
    session_interaction: Mapping[str, Any] | None,
    public_scene_slice: Mapping[str, Any] | None,
    scene_anchors: Mapping[str, Any],
    active_pressures: Mapping[str, Any],
    opening_visible_fact_strings: Sequence[str] | None,
) -> Tuple[Dict[str, Any] | None, List[str]]:
    """Plan-owned structural scene opening (C1-A). No prose, prompts, or world paraphrase."""
    reason, r_codes = _derive_opening_reason(
        ctir, narration_obligations=narration_obligations, session_interaction=session_interaction
    )
    opening_required = reason != "none"
    if not opening_required:
        return None, r_codes

    ap_copy = _deep_copy_jsonish(active_pressures) if isinstance(active_pressures, Mapping) else {}
    if not isinstance(ap_copy, dict):
        ap_copy = {}

    loc_anchors = scene_anchors.get("location_anchors") if isinstance(scene_anchors.get("location_anchors"), list) else []
    loc_anchors = _sorted_unique_strs(loc_anchors, limit=16)

    sid = _as_str(scene_anchors.get("scene_id")) or None

    actor_anchors, a_codes = _derive_scene_opening_actor_anchors(scene_anchors)
    vf_cats, vf_ids, vf_codes = _visible_fact_opening_projection(opening_visible_fact_strings)

    prohibited = sorted(DEFAULT_SCENE_OPENING_PROHIBITED_CONTENT_CODES)

    so_codes = _merge_derivation_codes([r_codes, a_codes, vf_codes])
    so_obj: Dict[str, Any] = {
        "opening_required": True,
        "opening_reason": reason,
        "scene_id": sid,
        "location_anchors": loc_anchors,
        "actor_anchors": actor_anchors,
        "active_pressures": ap_copy,
        "visible_fact_categories": vf_cats,
        "visible_fact_anchor_ids": vf_ids,
        "prohibited_content_codes": prohibited,
        "derivation_codes": so_codes,
        "validator": {"ok": True, "issues": []},
    }
    v_issues = _validate_scene_opening_object(
        so_obj,
        ctir=ctir,
        public_scene_slice=public_scene_slice,
        plan_active_pressures=active_pressures if isinstance(active_pressures, Mapping) else {},
        scene_anchors=scene_anchors if isinstance(scene_anchors, Mapping) else {},
    )
    so_obj["validator"] = {"ok": not v_issues, "issues": v_issues}
    return so_obj, so_codes


def _scan_scene_opening_for_proseish_keys(obj: Any, *, prefix: str, depth: int) -> Optional[str]:
    if depth > _MAX_DEPTH_SCAN:
        return None
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            sk = _as_str(k).lower()
            if sk in _SCENE_OPENING_PROSEISH_KEYS:
                return f"{prefix}.{k}"
            hit = _scan_scene_opening_for_proseish_keys(v, prefix=f"{prefix}.{k}", depth=depth + 1)
            if hit:
                return hit
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            hit = _scan_scene_opening_for_proseish_keys(v, prefix=f"{prefix}[{i}]", depth=depth + 1)
            if hit:
                return hit
    elif isinstance(obj, str):
        low = obj.lower()
        for m in _SCENE_OPENING_FALLBACK_MARKERS:
            if m in low:
                return f"{prefix}:fallback_marker:{m}"
    return None


def _validate_scene_opening_object(
    so: Mapping[str, Any],
    *,
    ctir: Mapping[str, Any],
    public_scene_slice: Mapping[str, Any] | None,
    plan_active_pressures: Mapping[str, Any],
    scene_anchors: Mapping[str, Any],
) -> List[str]:
    """Return issue codes; empty means structurally valid under C1-A."""
    issues: List[str] = []
    if not isinstance(so, Mapping):
        return ["scene_opening_not_mapping"]
    keys = set(so.keys())
    if keys != _SCENE_OPENING_ALLOWED_TOP_KEYS:
        issues.append(f"scene_opening_bad_keys:{sorted(keys ^ _SCENE_OPENING_ALLOWED_TOP_KEYS)}")

    req = so.get("opening_required")
    if req is not True:
        issues.append("scene_opening_opening_required_not_true")

    reason = _as_str(so.get("opening_reason"))
    if reason not in _SCENE_OPENING_REASONS:
        issues.append(f"scene_opening_bad_reason:{reason!r}")

    prose = _scan_scene_opening_for_proseish_keys(so, prefix="scene_opening", depth=0)
    if prose:
        issues.append(f"scene_opening_proseish_key_path:{prose}")

    need_sid, need_loc = _scene_opening_anchor_requirements(
        ctir, public_scene_slice=public_scene_slice, scene_anchors=scene_anchors if isinstance(scene_anchors, Mapping) else {}
    )
    sid = _as_str(so.get("scene_id"))
    if need_sid and not sid:
        issues.append("scene_opening_missing_scene_id")
    anchor_sid = _as_str(scene_anchors.get("scene_id"))
    if anchor_sid and sid != anchor_sid:
        issues.append("scene_opening_scene_id_mismatch_scene_anchors")

    la = so.get("location_anchors")
    la_sa = scene_anchors.get("location_anchors") if isinstance(scene_anchors.get("location_anchors"), list) else []
    la_sa_norm = _sorted_unique_strs(la_sa, limit=16)
    if not isinstance(la, list):
        issues.append("scene_opening_location_anchors_not_list")
    else:
        la_so_norm = _sorted_unique_strs([_as_str(x) for x in la], limit=16)
        if need_loc and not la_so_norm:
            issues.append("scene_opening_missing_location_anchors")
        if need_loc and la_so_norm != la_sa_norm:
            issues.append("scene_opening_location_anchors_mismatch_scene_anchors")

    aa = so.get("actor_anchors")
    if not isinstance(aa, list):
        issues.append("scene_opening_actor_anchors_not_list")
    else:
        allowed_ids: set[str] = set()
        ic = _mapping(ctir.get("interaction"))
        for tid in (
            _as_str(ic.get("active_target_id")),
            _as_str((ic.get("responder_target") or {}).get("id") if isinstance(ic.get("responder_target"), Mapping) else ""),
            _as_str((ic.get("speaker_target") or {}).get("id") if isinstance(ic.get("speaker_target"), Mapping) else ""),
        ):
            if tid:
                allowed_ids.add(_clip(tid, max_len=96))
        na = _mapping(ctir.get("narrative_anchors")).get("actors_speakers")
        if isinstance(na, list):
            for item in na:
                if isinstance(item, Mapping):
                    eid = _as_str(item.get("id") or item.get("entity_id"))
                    if eid:
                        allowed_ids.add(_clip(eid, max_len=96))
        inter_sa = _as_str(scene_anchors.get("active_interlocutor"))
        tgt_sa = _as_str(scene_anchors.get("active_target"))
        if inter_sa:
            allowed_ids.add(_clip(inter_sa, max_len=96))
        if tgt_sa:
            allowed_ids.add(_clip(tgt_sa, max_len=96))
        for i, row in enumerate(aa):
            if not isinstance(row, Mapping):
                issues.append(f"scene_opening_actor_anchor_not_mapping:{i}")
                continue
            eid = _as_str(row.get("entity_id"))
            role = _as_str(row.get("anchor_role"))
            if role not in ("interlocutor", "relevant_actor"):
                issues.append(f"scene_opening_bad_anchor_role:{i}")
            if eid and allowed_ids and eid not in allowed_ids:
                issues.append(f"scene_opening_actor_not_in_ctir:{eid}")

    ap_so = so.get("active_pressures")
    if not isinstance(ap_so, Mapping):
        issues.append("scene_opening_active_pressures_not_mapping")
    else:
        try:
            if json.dumps(ap_so, sort_keys=True) != json.dumps(plan_active_pressures, sort_keys=True):
                issues.append("scene_opening_active_pressures_mismatch")
        except (TypeError, ValueError):
            issues.append("scene_opening_active_pressures_not_comparable")

    pcc = so.get("prohibited_content_codes")
    if not isinstance(pcc, list):
        issues.append("scene_opening_prohibited_codes_not_list")
    else:
        for i, c in enumerate(pcc):
            if not isinstance(c, str) or not c.strip():
                issues.append(f"scene_opening_bad_prohibited_code:{i}")
            low = str(c).lower()
            if any(m in low for m in _SCENE_OPENING_FALLBACK_MARKERS):
                issues.append(f"scene_opening_fallback_indicator_in_code:{i}")

    vfc = so.get("visible_fact_categories")
    if not isinstance(vfc, list) or len(vfc) > 12:
        issues.append("scene_opening_bad_visible_fact_categories")
    else:
        allowed_cats = frozenset({"A", "B", "C", "D", "E"})
        for i, c in enumerate(vfc):
            if not isinstance(c, str) or c not in allowed_cats:
                issues.append(f"scene_opening_bad_visible_fact_category:{i}")

    vf_ids = so.get("visible_fact_anchor_ids")
    if not isinstance(vf_ids, list) or len(vf_ids) > 12:
        issues.append("scene_opening_bad_visible_fact_anchor_ids")

    dc = so.get("derivation_codes")
    if not isinstance(dc, list):
        issues.append("scene_opening_derivation_codes_not_list")

    val = so.get("validator")
    if not isinstance(val, Mapping):
        issues.append("scene_opening_validator_not_mapping")

    return issues


def validate_scene_opening(
    scene_opening: Any,
    *,
    ctir: Mapping[str, Any],
    public_scene_slice: Mapping[str, Any] | None,
    plan_active_pressures: Mapping[str, Any],
    scene_anchors: Mapping[str, Any],
    opening_required: bool,
) -> Optional[str]:
    """Return first error code string, or None if valid for the given *opening_required* flag."""
    if not opening_required:
        if scene_opening is not None:
            return "scene_opening_must_be_null_when_not_required"
        return None
    if scene_opening is None:
        return "scene_opening_missing_when_required"
    if not isinstance(scene_opening, Mapping):
        return "scene_opening_not_mapping"
    issues = _validate_scene_opening_object(
        scene_opening,
        ctir=ctir,
        public_scene_slice=public_scene_slice,
        plan_active_pressures=plan_active_pressures,
        scene_anchors=scene_anchors,
    )
    if issues:
        return issues[0]
    val = scene_opening.get("validator") if isinstance(scene_opening.get("validator"), Mapping) else {}
    if not val.get("ok"):
        return "scene_opening_validator_failed"
    return None


def _validate_scene_opening_plan(plan: Mapping[str, Any]) -> Optional[str]:
    """Post-build plan coherence for ``scene_opening`` (no external CTIR argument)."""
    so = plan.get("scene_opening")
    nm = _as_str(plan.get("narrative_mode"))
    if so is None:
        if nm == "opening":
            return "scene_opening_missing_for_opening_mode"
        return None
    if not isinstance(so, Mapping):
        return "scene_opening_not_mapping"

    prose = _scan_scene_opening_for_proseish_keys(so, prefix="scene_opening", depth=0)
    if prose:
        return f"scene_opening_proseish:{prose}"

    keys = set(so.keys())
    if keys != _SCENE_OPENING_ALLOWED_TOP_KEYS:
        return f"scene_opening_bad_keys:{sorted(keys ^ _SCENE_OPENING_ALLOWED_TOP_KEYS)}"

    sa = plan.get("scene_anchors") if isinstance(plan.get("scene_anchors"), Mapping) else {}
    ap = plan.get("active_pressures") if isinstance(plan.get("active_pressures"), Mapping) else {}

    sid_sa = _as_str(sa.get("scene_id"))
    sid_so = _as_str(so.get("scene_id"))
    if sid_sa and sid_so != sid_sa:
        return "scene_opening_scene_id_mismatch_scene_anchors"

    la_sa = sa.get("location_anchors") if isinstance(sa.get("location_anchors"), list) else []
    la_so = so.get("location_anchors") if isinstance(so.get("location_anchors"), list) else []
    if _sorted_unique_strs(la_sa, limit=16) != _sorted_unique_strs(la_so, limit=16):
        return "scene_opening_location_anchors_mismatch_plan"

    try:
        if json.dumps(so.get("active_pressures"), sort_keys=True) != json.dumps(ap, sort_keys=True):
            return "scene_opening_active_pressures_mismatch_plan"
    except (TypeError, ValueError):
        return "scene_opening_active_pressures_not_json_comparable"

    reason = _as_str(so.get("opening_reason"))
    if reason not in _SCENE_OPENING_REASONS:
        return f"scene_opening_bad_reason:{reason!r}"

    val = so.get("validator")
    if isinstance(val, Mapping) and val.get("ok") is False:
        return "scene_opening_validator_failed"

    aer = plan.get("allowable_entity_references") if isinstance(plan.get("allowable_entity_references"), list) else []
    allowed: set[str] = set()
    for row in aer:
        if isinstance(row, Mapping):
            eid = _as_str(row.get("entity_id"))
            if eid:
                allowed.add(_clip(eid, max_len=96))
    for fld in ("active_interlocutor", "active_target"):
        x = _as_str(sa.get(fld))
        if x:
            allowed.add(_clip(x, max_len=96))
    aa = so.get("actor_anchors") if isinstance(so.get("actor_anchors"), list) else []
    if allowed:
        for row in aa:
            if not isinstance(row, Mapping):
                continue
            eid = _as_str(row.get("entity_id"))
            if eid and eid not in allowed:
                return f"scene_opening_actor_not_allowlisted:{eid}"

    pcc = so.get("prohibited_content_codes")
    if isinstance(pcc, list):
        for c in pcc:
            if not isinstance(c, str):
                continue
            low = str(c).lower()
            if any(m in low for m in _SCENE_OPENING_FALLBACK_MARKERS):
                return "scene_opening_fallback_indicator_in_code"

    return None


def build_narrative_plan(
    *,
    ctir: Mapping[str, Any],
    session_interaction: Mapping[str, Any] | None = None,
    public_scene_slice: Mapping[str, Any] | None = None,
    published_entities: Sequence[Mapping[str, Any]] | None = None,
    recent_compressed_events: Sequence[Mapping[str, Any]] | None = None,
    resolution_meta: Mapping[str, Any] | None = None,
    turn_packet: Mapping[str, Any] | None = None,
    narration_obligations: Mapping[str, Any] | None = None,
    response_policy: Mapping[str, Any] | None = None,
    opening_visible_fact_strings: Sequence[str] | None = None,
) -> Dict[str, Any]:
    """Assemble a deterministic narrative-plan dict from CTIR-centered inputs.

    **Optional inputs (callers must pass already-sanitized, bounded data only):**

    - ``session_interaction``: e.g. ``active_interaction_target_id``,
      ``pending_lead_ids`` — mirrors fields already used at the turn/prompt seam.
    - ``public_scene_slice``: ``scene_id``, ``scene_name`` / ``title``,
      ``location_tokens`` or ``location_anchors``.
    - ``published_entities``: rows ``{entity_id|id, display_name|name}``. When
      ``None``, ``allowable_entity_references`` lists CTIR-addressed entities only.
      When provided (including ``[]``), the field lists **every** id in this
      published visibility slice (sorted)—the visible narration **universe**, not
      a focal subset; CTIR-only ids outside the slice never appear.
    - ``recent_compressed_events``: small dict rows (turn summaries), not raw log
      prose.
    - ``resolution_meta``: optional bounded resolution-facing metadata dict; never
      prompt fragments.
    - ``turn_packet``, ``narration_obligations``, ``response_policy``: optional
      already-resolved seam slices passed through to
      :func:`game.narrative_mode_contract.build_narrative_mode_contract` only (no
      local mode re-derivation). Omitted branches default to empty mappings at the
      contract builder.
    - ``opening_visible_fact_strings``: optional curated public visible-fact lines
      (same order as the prompt seam) used only to emit ``scene_opening.visible_fact_*``
      category/slot anchors—never embedded as prose on the plan.

    This function does not load engine/session/world objects or hidden stores.
    """
    if not looks_like_ctir(ctir):
        raise ValueError("ctir must be a CTIR root dict (see game.ctir.looks_like_ctir)")

    scene_anchors, c1 = _derive_scene_anchors(
        ctir, public_scene_slice=public_scene_slice, session_interaction=session_interaction
    )
    active_pressures, c2 = _derive_active_pressures(ctir, session_interaction=session_interaction)
    required_new_information, c3 = _derive_required_new_information(ctir)
    allowable_entity_references, c4 = _derive_allowable_entity_references(
        ctir, published_entities=published_entities
    )
    narrative_mode_contract = build_narrative_mode_contract(
        ctir=ctir,
        turn_packet=turn_packet,
        narration_obligations=narration_obligations,
        response_policy=response_policy,
    )
    ok_contract, contract_reasons = validate_narrative_mode_contract(narrative_mode_contract)
    if not ok_contract:
        codes = "|".join(str(x) for x in (contract_reasons or [])[:16])
        raise ValueError(f"narrative_mode_contract_invalid|{codes}")
    narrative_mode = _as_str(narrative_mode_contract.get("mode"))
    c5 = list(narrative_mode_contract.get("source_signals") or [])
    if isinstance(narrative_mode_contract.get("debug"), Mapping):
        dbg_dc = narrative_mode_contract["debug"].get("derivation_codes")
        if isinstance(dbg_dc, list):
            c5 = list(dbg_dc)
    role_allocation = _derive_role_allocation(narrative_mode)
    narrative_roles, nr_codes = derive_narrative_roles_composition(
        scene_anchors=scene_anchors,
        active_pressures=active_pressures,
        required_new_information=required_new_information,
        narrative_mode=narrative_mode,
        narrative_mode_contract=narrative_mode_contract,
        allowable_entity_references=allowable_entity_references,
        role_allocation=role_allocation,
    )
    action_outcome, ao_codes = _derive_action_outcome(
        ctir,
        narrative_mode=narrative_mode,
    )
    scene_opening, so_codes = _derive_scene_opening(
        ctir,
        narration_obligations=narration_obligations,
        session_interaction=session_interaction,
        public_scene_slice=public_scene_slice,
        scene_anchors=scene_anchors,
        active_pressures=active_pressures,
        opening_visible_fact_strings=opening_visible_fact_strings,
    )

    meta = _bounded_shallow_map(resolution_meta, max_keys=12) if resolution_meta else {}
    recent = _compress_recent_events(recent_compressed_events)

    derivation_codes = _merge_derivation_codes([c1, c2, c3, c4, c5, nr_codes, ao_codes, so_codes])
    _po = (
        narrative_mode_contract.get("prompt_obligations")
        if isinstance(narrative_mode_contract.get("prompt_obligations"), Mapping)
        else {}
    )
    _fm = narrative_mode_contract.get("forbidden_moves")
    _fm_list = _fm if isinstance(_fm, list) else []
    nmc_ship_trace = {
        "mode": narrative_mode,
        "enabled": bool(narrative_mode_contract.get("enabled")),
        "contract_ok": True,
        "ob_keys_head": sorted(str(k) for k in _po.keys() if isinstance(k, str) and str(k).strip())[:6],
        "fm_head": sorted(
            {str(x).strip() for x in _fm_list if isinstance(x, str) and str(x).strip()}
        )[:6],
    }

    # Per-field classification (CTIR primacy — all plan fields are non-authoritative):
    # - version: bounded planning convenience (schema transport only).
    # - scene_anchors: direct derived projection (CTIR interaction/narrative_anchors/state_mutations.scene
    #   plus optional public_scene_slice / session_interaction for already-public labels and ids).
    # - active_pressures: direct derived projection (CTIR resolution/world/state_mutations plus optional
    #   session_interaction pending_lead_ids); not a duplicate policy engine.
    # - required_new_information: direct derived projection (categories mined from CTIR resolution
    #   and state_mutations only; kinds are closed-set in _REQUIRED_NEW_INFORMATION_KINDS).
    # - allowable_entity_references: visibility-shaped outer boundary (OPTION A). With published_entities:
    #   full published slice ids (+ CTIR descriptors for same ids); without: CTIR-addressed ids only.
    #   Not a focality list—use scene_anchors / narrative_mode / active_pressures / required_new_information /
    #   role_allocation for narrower structural focus.
    # - narrative_mode / narrative_mode_contract: derivative narrative-mode contract from
    #   :mod:`game.narrative_mode_contract` (CTIR + optional turn_packet / narration_obligations / response_policy);
    #   narrative_mode is the compact alias of narrative_mode_contract["mode"].
    # - role_allocation: bounded planning convenience (deterministic integer weights from narrative_mode).
    # - narrative_roles: Objective N3 abstract composition-role shaping (counts, closed-set signals,
    #   emphasis bands, structural kind-tags); downstream of scene_anchors, active_pressures,
    #   required_new_information, narrative_mode_contract, allowable_entity_references, role_allocation.
    # - scene_opening: C1-A plan-owned structural opening projection (prose-free); None when
    #   ``opening_reason`` is ``none``; otherwise CTIR + public/visibility-shaped inputs only.
    # - recent_compressed_events: bounded planning convenience (caller-supplied bounded summaries;
    #   not canonical turn history).
    # - resolution_meta: bounded planning convenience (optional caller metadata blob; never CTIR).
    # - debug.derivation_codes: bounded planning convenience (inspect-only provenance codes).
    plan: Dict[str, Any] = {
        "version": NARRATIVE_PLAN_VERSION,
        "scene_anchors": scene_anchors,
        "active_pressures": active_pressures,
        "required_new_information": required_new_information,
        "allowable_entity_references": allowable_entity_references,
        "narrative_mode": narrative_mode,
        "narrative_mode_contract": narrative_mode_contract,
        "role_allocation": role_allocation,
        "narrative_roles": narrative_roles,
        "action_outcome": action_outcome,
        "scene_opening": scene_opening,
        "recent_compressed_events": recent,
        "resolution_meta": meta,
        "debug": {
            "derivation_codes": derivation_codes,
            "nmc_ship_trace": nmc_ship_trace,
        },
    }
    err = validate_narrative_plan(plan, strict=True)
    if err:
        raise ValueError(f"internal narrative plan failed validation: {err}")
    return plan


def narrative_plan_matches_ctir_derivation(
    plan: Mapping[str, Any],
    *,
    ctir: Mapping[str, Any],
    session_interaction: Mapping[str, Any] | None = None,
    public_scene_slice: Mapping[str, Any] | None = None,
    published_entities: Sequence[Mapping[str, Any]] | None = None,
    recent_compressed_events: Sequence[Mapping[str, Any]] | None = None,
    resolution_meta: Mapping[str, Any] | None = None,
    turn_packet: Mapping[str, Any] | None = None,
    narration_obligations: Mapping[str, Any] | None = None,
    response_policy: Mapping[str, Any] | None = None,
    opening_visible_fact_strings: Sequence[str] | None = None,
) -> bool:
    """Return True iff *plan* is byte-identical to a fresh :func:`build_narrative_plan` for the same inputs.

    Narrow invariant helper: detects tampering or alternate-truth plans that no
    longer match CTIR-centered derivation. Does **not** replace
    :func:`looks_like_ctir` or engine validation.

    Pass the same optional ``turn_packet`` / ``narration_obligations`` / ``response_policy``
    arguments given to :func:`build_narrative_plan` when those slices were used to build the plan.
    """
    if not isinstance(plan, Mapping):
        return False
    if validate_narrative_plan(plan, strict=False):
        return False
    try:
        rebuilt = build_narrative_plan(
            ctir=ctir,
            session_interaction=session_interaction,
            public_scene_slice=public_scene_slice,
            published_entities=published_entities,
            recent_compressed_events=recent_compressed_events,
            resolution_meta=resolution_meta,
            turn_packet=turn_packet,
            narration_obligations=narration_obligations,
            response_policy=response_policy,
            opening_visible_fact_strings=opening_visible_fact_strings,
        )
    except ValueError:
        return False
    try:
        return json.dumps(plan, sort_keys=True) == json.dumps(rebuilt, sort_keys=True)
    except (TypeError, ValueError):
        return False


def _scan_for_banned_keys(obj: Any, *, prefix: str, depth: int) -> Optional[str]:
    if depth > _MAX_DEPTH_SCAN:
        return None
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            sk = _as_str(k).lower()
            if sk in _PROSE_INSTRUCTION_KEYS:
                return f"{prefix}.{k}"
            hit = _scan_for_banned_keys(v, prefix=f"{prefix}.{k}", depth=depth + 1)
            if hit:
                return hit
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            hit = _scan_for_banned_keys(v, prefix=f"{prefix}[{i}]", depth=depth + 1)
            if hit:
                return hit
    return None


def validate_narrative_plan(plan: Any, *, strict: bool = True) -> Optional[str]:
    """Return an error string if *plan* is invalid; else ``None``.

    With ``strict=True``, reject unknown top-level keys and any banned
    prose/prompt-like key names anywhere in the tree.
    """
    if not isinstance(plan, Mapping):
        return "plan_not_mapping"
    if plan.get("version") != NARRATIVE_PLAN_VERSION:
        return "bad_version"

    allowed_roots = {
        "version",
        "scene_anchors",
        "active_pressures",
        "required_new_information",
        "allowable_entity_references",
        "narrative_mode",
        "narrative_mode_contract",
        "role_allocation",
        "narrative_roles",
        "action_outcome",
        "scene_opening",
        "recent_compressed_events",
        "resolution_meta",
        "debug",
    }
    if strict:
        extra = set(plan.keys()) - allowed_roots
        if extra:
            return f"unknown_keys:{sorted(extra)}"

    if strict:
        banned = _scan_for_banned_keys(plan, prefix="plan", depth=0)
        if banned:
            return f"banned_key_path:{banned}"

    mode = plan.get("narrative_mode")
    if not isinstance(mode, str) or mode.strip() not in NARRATIVE_MODES:
        return "bad_narrative_mode"

    nmc = plan.get("narrative_mode_contract")
    if not isinstance(nmc, Mapping):
        return "missing_narrative_mode_contract"
    ok_nmc, nmc_reasons = validate_narrative_mode_contract(nmc)
    if not ok_nmc:
        code = nmc_reasons[0] if nmc_reasons else "unknown"
        return f"narrative_mode_contract_invalid:{code}"
    if _as_str(mode) != _as_str(nmc.get("mode")):
        return "narrative_mode_contract_mode_mismatch"

    ra = plan.get("role_allocation")
    if not isinstance(ra, Mapping):
        return "role_allocation_not_mapping"
    keys_needed = ("dialogue", "exposition", "outcome_forward", "transition")
    for k in keys_needed:
        if k not in ra:
            return f"role_allocation_missing:{k}"
        v = ra.get(k)
        if not isinstance(v, int) or v < 0 or v > 100:
            return f"role_allocation_bad_weight:{k}"
    if sum(int(ra[k]) for k in keys_needed) != 100:
        return "role_allocation_sum_not_100"

    nroles_err = _validate_narrative_roles(plan.get("narrative_roles"))
    if nroles_err:
        return nroles_err

    oft = None
    if isinstance(plan.get("narrative_roles"), Mapping):
        cons = plan["narrative_roles"].get("consequence") if isinstance(plan["narrative_roles"], Mapping) else None
        if isinstance(cons, Mapping):
            oft = cons.get("outcome_forward_tier")
    if oft is not None:
        if _outcome_forward_tier(ra) != oft:
            return "narrative_roles_outcome_forward_tier_mismatch_role_allocation"

    rni = plan.get("required_new_information")
    if isinstance(rni, list):
        for i, item in enumerate(rni):
            if not isinstance(item, Mapping):
                return f"required_new_information_not_mapping:{i}"
            kind = _as_str(item.get("kind"))
            if kind not in _REQUIRED_NEW_INFORMATION_KINDS:
                return f"required_new_information_unknown_kind:{kind!r}"

    nr = plan.get("narrative_roles")
    if isinstance(nr, Mapping):
        pinst = _validate_narrative_roles_plan_slices(plan)
        if pinst:
            return pinst

    so_err = _validate_scene_opening_plan(plan)
    if so_err:
        return so_err

    ao_err = _validate_action_outcome_plan(plan)
    if ao_err:
        return ao_err

    try:
        json.dumps(plan, sort_keys=True)
    except (TypeError, ValueError):
        return "not_json_serializable"

    return None


def normalize_narrative_plan(plan: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Return a copy with lists sorted, strings clipped, and bounds re-applied."""
    if not isinstance(plan, Mapping):
        return {}
    err = validate_narrative_plan(plan, strict=False)
    if err:
        return {}
    p = dict(plan)
    sa = _mapping(p.get("scene_anchors"))
    if sa:
        la = sa.get("location_anchors")
        if isinstance(la, list):
            sa["location_anchors"] = _sorted_unique_strs(la, limit=16)
        ra = sa.get("relevant_actors")
        if isinstance(ra, list):
            sa["relevant_actors"] = sorted(
                [
                    {
                        "id": _clip(_as_str(x.get("id")), max_len=96),
                        "name": _clip(_as_str(x.get("name")), max_len=96) if _as_str(x.get("name")) else None,
                    }
                    for x in ra
                    if isinstance(x, Mapping)
                ],
                key=lambda r: r["id"],
            )[:24]
        p["scene_anchors"] = sa

    ap = _mapping(p.get("active_pressures"))
    if ap:
        for fld in ("pending_lead_ids", "context_codes", "scene_tension_codes"):
            v = ap.get(fld)
            if isinstance(v, list):
                ap[fld] = _sorted_unique_strs(v, limit=_MAX_ID_LIST)
        p["active_pressures"] = ap

    rni = p.get("required_new_information")
    if isinstance(rni, list):
        def _rk(d: Mapping[str, Any]) -> Tuple[str, str]:
            return (_as_str(d.get("kind")), json.dumps(d, sort_keys=True))

        p["required_new_information"] = sorted((_mapping(x) for x in rni if isinstance(x, Mapping)), key=_rk)[
            :_MAX_ID_LIST
        ]

    aer = p.get("allowable_entity_references")
    if isinstance(aer, list):
        cleaned = []
        for x in aer:
            if not isinstance(x, Mapping):
                continue
            cleaned.append(
                {
                    "entity_id": _clip(_as_str(x.get("entity_id")), max_len=96),
                    "descriptor": _clip(_as_str(x.get("descriptor")), max_len=96)
                    if _as_str(x.get("descriptor"))
                    else None,
                }
            )
        p["allowable_entity_references"] = sorted(cleaned, key=lambda r: r["entity_id"])[:_MAX_ID_LIST]

    dbg = _mapping(p.get("debug"))
    if dbg.get("derivation_codes") is not None:
        dc = dbg.get("derivation_codes")
        if isinstance(dc, list):
            dbg["derivation_codes"] = _sorted_unique_strs(dc, limit=_MAX_CODES)
        p["debug"] = dbg

    nroles = p.get("narrative_roles")
    if isinstance(nroles, Mapping):
        fixed_nr: Dict[str, Any] = {}
        for rk in _NARRATIVE_ROLE_TOP_KEYS:
            sub = nroles.get(rk)
            if not isinstance(sub, Mapping):
                continue
            sub_d = dict(sub)
            sig = sub_d.get("signals")
            if isinstance(sig, list):
                if rk == "location_anchor":
                    allowed = _LOCATION_ANCHOR_SIGNALS
                elif rk == "actor_anchor":
                    allowed = _ACTOR_ANCHOR_SIGNALS
                elif rk == "pressure":
                    allowed = _PRESSURE_ROLE_SIGNALS
                elif rk == "hook":
                    allowed = _HOOK_ROLE_SIGNALS
                else:
                    allowed = _CONSEQUENCE_ROLE_SIGNALS
                sub_d["signals"] = sorted({str(x) for x in sig if str(x) in allowed})[:_MAX_NARRATIVE_ROLE_SIGNALS]
            if rk == "hook":
                ikt = sub_d.get("information_kind_tags")
                if isinstance(ikt, list):
                    sub_d["information_kind_tags"] = sorted(
                        {str(x) for x in ikt if str(x) in _REQUIRED_NEW_INFORMATION_KINDS}
                    )[:_MAX_INFORMATION_KIND_TAGS]
            fixed_nr[rk] = sub_d
        if len(fixed_nr) == len(_NARRATIVE_ROLE_TOP_KEYS):
            p["narrative_roles"] = fixed_nr

    so = p.get("scene_opening")
    if isinstance(so, Mapping):
        so_d = dict(so)
        lac = so_d.get("location_anchors")
        if isinstance(lac, list):
            so_d["location_anchors"] = _sorted_unique_strs(lac, limit=16)
        for fld in ("visible_fact_categories", "visible_fact_anchor_ids", "prohibited_content_codes", "derivation_codes"):
            v = so_d.get(fld)
            if isinstance(v, list):
                if fld == "prohibited_content_codes":
                    so_d[fld] = sorted({str(x).strip() for x in v if isinstance(x, str) and str(x).strip()})
                else:
                    so_d[fld] = sorted({str(x).strip() for x in v if isinstance(x, str) and str(x).strip()})
        aa = so_d.get("actor_anchors")
        if isinstance(aa, list):
            rows = []
            for x in aa:
                if not isinstance(x, Mapping):
                    continue
                rows.append(
                    {
                        "entity_id": _clip(_as_str(x.get("entity_id")), max_len=96),
                        "anchor_role": _clip(_as_str(x.get("anchor_role")), max_len=32),
                    }
                )
            so_d["actor_anchors"] = sorted(rows, key=lambda r: (str(r.get("anchor_role")), str(r.get("entity_id"))))
        p["scene_opening"] = so_d

    ao = p.get("action_outcome")
    if isinstance(ao, Mapping):
        p["action_outcome"] = _normalize_action_outcome(ao)

    return p


def _derive_action_outcome(
    ctir: Mapping[str, Any],
    *,
    narrative_mode: str,
) -> tuple[dict[str, Any], list[str]]:
    """Derive a deterministic, bounded, prose-free action_outcome block from CTIR only.

    This is a structural bridge: it carries mechanics/effects atoms for narration, but
    never asks the planner to re-adjudicate.
    """
    codes: list[str] = ["action_outcome:derive"]
    res = _mapping(ctir.get("resolution"))
    nc = _mapping(ctir.get("noncombat"))
    sm = _mapping(ctir.get("state_mutations"))

    mode = _as_str(narrative_mode) or "continuation"
    present = mode == "action_outcome"

    # Default empty-but-structured object (still JSON-safe).
    out: dict[str, Any] = {
        "present": bool(present),
        "source_kind": "unknown",
        "result": {
            "result_kind": _clip(_as_str(res.get("kind")), max_len=64) or None,
            "success_state": _clip(_as_str(res.get("success_state")), max_len=24) or None,
            "actor_id": None,
            "target_id": None,
            "action_id": _clip(_as_str(res.get("action_id")), max_len=128) or None,
            "roll_summary": {},
        },
        "effects": {
            "damage_dealt": 0,
            "healing_applied": 0,
            "conditions_applied": [],
            "conditions_removed": [],
            "combat_ended": False,
            "winner": None,
            "state_delta_keys": [],
        },
        "framing": {
            "emphasis": "standard",
            "reveal_policy": "respect_visibility",
            "allowed_certainty": "engine_only",
            "prohibited_codes": [
                "no_raw_roll_text",
                "no_hint_prompt_prose",
                "no_mechanics_interpretation",
            ],
        },
        "derivation_codes": [],
    }

    # State delta keys: stable, bounded projection.
    delta: list[str] = []
    for domain in ("scene", "session", "combat", "clues_leads"):
        block = sm.get(domain)
        if not isinstance(block, Mapping):
            continue
        ck = block.get("changed_keys")
        if isinstance(ck, (list, tuple)):
            for k in ck:
                sk = _clip(_as_str(k), max_len=96)
                if sk:
                    delta.append(f"{domain}.{sk}")
    out["effects"]["state_delta_keys"] = _sorted_unique_strs(delta, limit=48)

    # Source selection: combat > skill_check > environment/noncombat (from CTIR noncombat slice) > unknown.
    _nc_env_kinds = frozenset({"perception", "investigation", "exploration"})

    def _discovered_target_id(n: Mapping[str, Any]) -> Optional[str]:
        de = n.get("discovered_entities")
        if not isinstance(de, (list, tuple)):
            return None
        for pref in ("interactable", "object", "npc", "scene"):
            for item in de:
                if not isinstance(item, Mapping):
                    continue
                if _as_str(item.get("entity_kind")).lower() == pref:
                    eid = _as_str(item.get("entity_id"))
                    if eid:
                        return _clip(eid, max_len=96)
        return None

    def _roll_summary_from_nc_block(n: Mapping[str, Any]) -> dict[str, Any]:
        roll_out: dict[str, Any] = {}
        if isinstance(n.get("check_request"), Mapping):
            cr = n["check_request"]
            for rk in ("check_type", "skill", "difficulty", "reason"):
                vv = cr.get(rk)
                if vv is None or isinstance(vv, (bool, int, float)):
                    roll_out[rk] = vv
                elif isinstance(vv, str) and rk in ("check_type", "skill", "reason"):
                    roll_out[rk] = _clip(vv.strip(), max_len=96)
        ot = _as_str(n.get("outcome_type"))
        if ot:
            roll_out["outcome_type"] = _clip(ot, max_len=64)
        sub = _as_str(n.get("subkind"))
        if sub:
            roll_out["subkind"] = _clip(sub, max_len=64)
        return roll_out

    def _apply_structural_target_ids() -> None:
        iid = _as_str(res.get("interactable_id"))
        auth = res.get("authoritative_outputs")
        if not iid and isinstance(auth, Mapping):
            iid = _as_str(auth.get("interactable_id"))
        if iid:
            out["result"]["target_id"] = _clip(iid, max_len=96)
            return
        if nc:
            tid = _discovered_target_id(nc)
            if tid:
                out["result"]["target_id"] = tid

    combat = res.get("combat")
    if isinstance(combat, Mapping) and combat:
        out["source_kind"] = "combat"
        codes.append("action_outcome:source:combat")
        actor_id = _as_str(combat.get("actor_id"))
        target_id = _as_str(combat.get("target_id"))
        if actor_id:
            out["result"]["actor_id"] = _clip(actor_id, max_len=96)
        if target_id:
            out["result"]["target_id"] = _clip(target_id, max_len=96)
        # Rolls: numeric/bool atoms only.
        rolls = combat.get("rolls")
        if isinstance(rolls, Mapping):
            roll_out: dict[str, Any] = {}
            for rk in sorted(str(k) for k in rolls.keys())[:24]:
                vv = rolls.get(rk)
                if vv is None or isinstance(vv, (bool, int, float)):
                    roll_out[rk] = vv
                elif isinstance(vv, list):
                    roll_out[rk] = [x for x in vv[:24] if x is None or isinstance(x, (bool, int, float))]
            out["result"]["roll_summary"] = roll_out
        out["effects"]["damage_dealt"] = int(combat.get("damage_dealt") or 0) if isinstance(combat.get("damage_dealt"), (int, float)) else 0
        out["effects"]["healing_applied"] = int(combat.get("healing_applied") or 0) if isinstance(combat.get("healing_applied"), (int, float)) else 0
        for k in ("conditions_applied", "conditions_removed"):
            vv = combat.get(k)
            if isinstance(vv, list):
                out["effects"][k] = _sorted_unique_strs(vv, limit=24)
        out["effects"]["combat_ended"] = bool(combat.get("combat_ended")) if "combat_ended" in combat else False
        win = _as_str(combat.get("winner"))
        out["effects"]["winner"] = _clip(win, max_len=32) if win else None
    elif isinstance(res.get("skill_check"), Mapping) and res.get("skill_check"):
        out["source_kind"] = "skill_check"
        codes.append("action_outcome:source:skill_check")
        sk = res["skill_check"]
        roll_out_sc: dict[str, Any] = {}
        for rk in ("skill", "difficulty", "dc", "modifier", "roll", "total", "success"):
            if rk in sk:
                vv = sk.get(rk)
                if vv is None or isinstance(vv, (bool, int, float)):
                    roll_out_sc[rk] = vv
                elif isinstance(vv, str) and rk in ("skill",):
                    roll_out_sc[rk] = _clip(vv.strip(), max_len=64)
        out["result"]["roll_summary"] = roll_out_sc
        _apply_structural_target_ids()
    elif nc:
        nk = _as_str(nc.get("kind"))
        if nk in _nc_env_kinds:
            out["source_kind"] = "environment"
            codes.append("action_outcome:source:environment")
        else:
            out["source_kind"] = "noncombat"
            codes.append("action_outcome:source:noncombat")
        out["result"]["roll_summary"] = _roll_summary_from_nc_block(nc)
        _apply_structural_target_ids()

    out["derivation_codes"] = _merge_derivation_codes([codes])
    return out, codes


def _validate_action_outcome_object(ao: Any) -> Optional[str]:
    if ao is None:
        return None
    if not isinstance(ao, Mapping):
        return "action_outcome_not_mapping"
    keys = set(ao.keys())
    allowed = {"present", "source_kind", "result", "effects", "framing", "derivation_codes"}
    if keys != allowed:
        return f"action_outcome_bad_keys:{sorted(keys ^ allowed)}"
    if not isinstance(ao.get("present"), bool):
        return "action_outcome_present_not_bool"
    sk = _as_str(ao.get("source_kind"))
    if sk not in ("combat", "skill_check", "noncombat", "environment", "unknown"):
        return "action_outcome_bad_source_kind"
    res = ao.get("result")
    if not isinstance(res, Mapping):
        return "action_outcome_result_not_mapping"
    res_keys = set(res.keys())
    res_allowed = {"result_kind", "success_state", "actor_id", "target_id", "action_id", "roll_summary"}
    if res_keys != res_allowed:
        return f"action_outcome_result_bad_keys:{sorted(res_keys ^ res_allowed)}"
    for k in ("result_kind", "success_state", "actor_id", "target_id", "action_id"):
        v = res.get(k)
        if v is not None and not (isinstance(v, str) and v.strip() and len(v) <= 160):
            return f"action_outcome_result_bad_str:{k}"
        if isinstance(v, str) and v.strip().lower() in _PROSE_INSTRUCTION_KEYS:
            return f"action_outcome_result_prose_key_leak:{k}"
    rs = res.get("roll_summary")
    if not isinstance(rs, Mapping):
        return "action_outcome_roll_summary_not_mapping"
    if len(rs.keys()) > 32:
        return "action_outcome_roll_summary_too_many_keys"
    for k, v in rs.items():
        if not isinstance(k, str) or not k.strip() or len(k) > 64:
            return "action_outcome_roll_summary_bad_key"
        if isinstance(v, str):
            # Allow small enumerations like skill id; disallow prose.
            if len(v) > 96 or any(ch in v for ch in ("\n", "\r")):
                return "action_outcome_roll_summary_string_too_long"
        elif v is None or isinstance(v, (bool, int, float)):
            pass
        elif isinstance(v, list):
            if len(v) > 24:
                return "action_outcome_roll_summary_list_too_long"
            for item in v:
                if not (item is None or isinstance(item, (bool, int, float))):
                    return "action_outcome_roll_summary_list_bad_item"
        else:
            return "action_outcome_roll_summary_bad_value_type"
    eff = ao.get("effects")
    if not isinstance(eff, Mapping):
        return "action_outcome_effects_not_mapping"
    eff_allowed = {
        "damage_dealt",
        "healing_applied",
        "conditions_applied",
        "conditions_removed",
        "combat_ended",
        "winner",
        "state_delta_keys",
    }
    if set(eff.keys()) != eff_allowed:
        return f"action_outcome_effects_bad_keys:{sorted(set(eff.keys()) ^ eff_allowed)}"
    for k in ("damage_dealt", "healing_applied"):
        v = eff.get(k)
        if not isinstance(v, int) or v < 0 or v > 10_000:
            return f"action_outcome_effects_bad_int:{k}"
    for k in ("conditions_applied", "conditions_removed", "state_delta_keys"):
        v = eff.get(k)
        if not isinstance(v, list):
            return f"action_outcome_effects_{k}_not_list"
        if len(v) > 48:
            return f"action_outcome_effects_{k}_too_long"
        for item in v:
            if not isinstance(item, str) or not item.strip() or len(item) > 120:
                return f"action_outcome_effects_{k}_bad_item"
    if not isinstance(eff.get("combat_ended"), bool):
        return "action_outcome_effects_combat_ended_not_bool"
    win = eff.get("winner")
    if win is not None and not (isinstance(win, str) and win.strip() and len(win) <= 32):
        return "action_outcome_effects_bad_winner"
    framing = ao.get("framing")
    if not isinstance(framing, Mapping):
        return "action_outcome_framing_not_mapping"
    fr_allowed = {"emphasis", "reveal_policy", "allowed_certainty", "prohibited_codes"}
    if set(framing.keys()) != fr_allowed:
        return f"action_outcome_framing_bad_keys:{sorted(set(framing.keys()) ^ fr_allowed)}"
    for k in ("emphasis", "reveal_policy", "allowed_certainty"):
        v = framing.get(k)
        if not isinstance(v, str) or not v.strip() or len(v) > 64:
            return f"action_outcome_framing_bad_str:{k}"
    pc = framing.get("prohibited_codes")
    if not isinstance(pc, list) or len(pc) > 24:
        return "action_outcome_framing_prohibited_codes_bad"
    for item in pc:
        if not isinstance(item, str) or not item.strip() or len(item) > 96:
            return "action_outcome_framing_bad_prohibited_code"
    dc = ao.get("derivation_codes")
    if not isinstance(dc, list) or len(dc) > _MAX_CODES:
        return "action_outcome_derivation_codes_bad"
    for item in dc:
        if not isinstance(item, str) or not item.strip() or len(item) > 120:
            return "action_outcome_bad_derivation_code"
    return None


def _validate_action_outcome_plan(plan: Mapping[str, Any]) -> Optional[str]:
    mode = _as_str(plan.get("narrative_mode"))
    ao = plan.get("action_outcome")
    err = _validate_action_outcome_object(ao)
    if err:
        return err
    if mode == "action_outcome":
        if not isinstance(ao, Mapping):
            return "action_outcome_missing_for_action_outcome_mode"
        if ao.get("present") is not True:
            return "action_outcome_present_not_true_for_action_outcome_mode"
        # Require a bounded result structure: roll_summary must exist (may be empty mapping).
        res = ao.get("result") if isinstance(ao.get("result"), Mapping) else None
        if not isinstance(res, Mapping) or "roll_summary" not in res:
            return "action_outcome_missing_result_structure"
    return None


def validate_action_outcome_plan_contract(
    plan: Mapping[str, Any] | None,
    *,
    response_type_required: str | None = None,
) -> tuple[bool, list[str]]:
    """Enforce action_outcome readiness for narration prompt assembly (fail-closed seam input).

    When ``narrative_mode`` is ``action_outcome``, the plan must carry a validating
    ``action_outcome`` object (``present`` true, bounded ``result`` / ``effects`` / ``framing``),
    and the full plan must pass :func:`validate_narrative_plan` (relaxed strictness).

    ``response_type_required`` is accepted for API symmetry / tracing; structural
    enforcement is keyed off ``narrative_mode`` so continuation plans with a dormant
    ``action_outcome`` slice (``present: false``) stay valid alongside a response-type hint.

    Returns ``(ok, failure_reasons)`` where *failure_reasons* are machine-readable tokens
    suitable for ``narration_seam_audit`` / ``prompt_debug`` (never player-facing prose).
    """
    _ = str(response_type_required or "").strip().lower()
    if not isinstance(plan, Mapping):
        return True, []
    nm = _as_str(plan.get("narrative_mode"))
    if nm != "action_outcome":
        return True, []
    if not plan:
        return False, ["action_outcome_contract:plan_empty"]

    reasons: list[str] = []
    ao = plan.get("action_outcome")
    if ao is None:
        reasons.append("action_outcome_contract:missing_action_outcome")
    oerr = _validate_action_outcome_object(ao)
    if oerr:
        reasons.append(f"action_outcome_contract:{oerr}")
    if isinstance(ao, Mapping):
        if ao.get("present") is not True:
            reasons.append("action_outcome_contract:present_not_true")
        res = ao.get("result") if isinstance(ao.get("result"), Mapping) else None
        if not isinstance(res, Mapping) or "roll_summary" not in res:
            reasons.append("action_outcome_contract:missing_result_roll_summary")
        if not isinstance(ao.get("effects"), Mapping):
            reasons.append("action_outcome_contract:missing_effects")
        if not isinstance(ao.get("framing"), Mapping):
            reasons.append("action_outcome_contract:missing_framing")

    vp = validate_narrative_plan(plan, strict=False)
    if isinstance(vp, str) and vp.strip():
        reasons.append(f"action_outcome_contract:narrative_plan_invalid:{vp}")

    seen: set[str] = set()
    ordered: list[str] = []
    for tok in reasons:
        if tok not in seen:
            seen.add(tok)
            ordered.append(tok)
    return (len(ordered) == 0), ordered


def _normalize_action_outcome(ao: Mapping[str, Any]) -> dict[str, Any]:
    """Light normalization pass: sorts lists and clips strings (no semantic edits)."""
    out = dict(ao)
    # Derivation codes stable sorted unique.
    dc = out.get("derivation_codes")
    if isinstance(dc, list):
        out["derivation_codes"] = _sorted_unique_strs(dc, limit=_MAX_CODES)
    # Effects lists stable ordering.
    eff = out.get("effects")
    if isinstance(eff, Mapping):
        eff_d = dict(eff)
        for k in ("conditions_applied", "conditions_removed", "state_delta_keys"):
            v = eff_d.get(k)
            if isinstance(v, list):
                eff_d[k] = _sorted_unique_strs(v, limit=48)
        win = _as_str(eff_d.get("winner"))
        eff_d["winner"] = _clip(win, max_len=32) if win else None
        out["effects"] = eff_d
    # Result roll_summary: stable key ordering already via json dumps; keep as-is.
    res = out.get("result")
    if isinstance(res, Mapping):
        res_d = dict(res)
        for k in ("result_kind", "success_state", "actor_id", "target_id", "action_id"):
            v = _as_str(res_d.get(k))
            res_d[k] = _clip(v, max_len=160) if v else None
        out["result"] = res_d
    fr = out.get("framing")
    if isinstance(fr, Mapping):
        fr_d = dict(fr)
        pc = fr_d.get("prohibited_codes")
        if isinstance(pc, list):
            fr_d["prohibited_codes"] = _sorted_unique_strs(pc, limit=24)
        out["framing"] = fr_d
    return out
