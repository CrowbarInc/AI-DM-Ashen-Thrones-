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
  ``required_new_information``, and ``role_allocation``—consumers must not treat
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

    meta = _bounded_shallow_map(resolution_meta, max_keys=12) if resolution_meta else {}
    recent = _compress_recent_events(recent_compressed_events)

    derivation_codes = _merge_derivation_codes([c1, c2, c3, c4, c5])
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

    rni = plan.get("required_new_information")
    if isinstance(rni, list):
        for i, item in enumerate(rni):
            if not isinstance(item, Mapping):
                return f"required_new_information_not_mapping:{i}"
            kind = _as_str(item.get("kind"))
            if kind not in _REQUIRED_NEW_INFORMATION_KINDS:
                return f"required_new_information_unknown_kind:{kind!r}"

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

    return p
