"""Canonical Turn Intermediate Representation (CTIR).

CTIR is the **canonical resolved-turn meaning representation**: a single,
deterministic, JSON-serializable snapshot of what the engine resolved for one
turn. It is built **after** engine resolution and authoritative state mutation,
and **before** prompt construction.

CTIR deliberately contains **no prose and no narration content** (no player-facing
text, no model instructions, and no prompt fragments). It is **not** a narration
object, **not** a policy engine, and **not** a replacement for domain ownership in
engine modules.

When the runtime embeds ``resolution["noncombat_resolution"]`` (see
:mod:`game.noncombat_resolution`), CTIR carries a bounded root ``noncombat`` slice
built only from that contract (plus an empty transitional fallback when absent).

It does **not** duplicate canonical state owned elsewhere except for **bounded**
summaries and identifiers needed for downstream deterministic reads and tests.

Downstream readers (prompt assembly, gates, telemetry, tests) should **prefer**
CTIR over scanning raw engine, session, or world payloads.

Boundary note: :mod:`game.turn_packet` remains the compact packet / debug /
contracts object at the gate boundary. CTIR is a separate semantic layer; callers
may bridge small overlapping fields explicitly, but CTIR must not subsume the
turn packet contract.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

_CTIR_VERSION = 1

# Keys treated as prose-like when normalizing anchor-like mappings (dropped with notes).
_PROSE_LIKE_KEYS = frozenset(
    {
        "narration",
        "narrative",
        "prose",
        "story",
        "description",
        "text",
        "player_facing_text",
        "prompt",
        "system_prompt",
        "instructions",
    }
)

_MAX_ID_LIST = 64
_MAX_CHANGED_KEYS = 48
_MAX_STR_CLIP = 256
_MAX_DEPTH_DEFAULT = 3
_MAX_DICT_KEYS_SCAN = 32
_MAX_NONCOMBAT_ENTITIES = 32
_MAX_NONCOMBAT_FACTS = 32
_MAX_NONCOMBAT_AUTH_OUTPUTS = 16
_MAX_NONCOMBAT_REASON_CODES = 16


def ctir_version() -> int:
    """Return the active CTIR schema version (integer)."""
    return _CTIR_VERSION


def _as_str(v: Any) -> str:
    return str(v or "").strip()


def _sorted_unique_strs(items: Sequence[Any], *, limit: int) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for raw in items:
        s = _as_str(raw)
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
        if len(out) >= limit:
            break
    return sorted(out)


def _clip_str(s: str, *, max_len: int = _MAX_STR_CLIP) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def _is_json_serializable(obj: Any) -> bool:
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False


def _json_safe_atom(v: Any) -> Any:
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    return str(v)


def _bounded_mapping(
    m: Mapping[str, Any] | None,
    *,
    max_keys: int = _MAX_DICT_KEYS_SCAN,
    max_depth: int = _MAX_DEPTH_DEFAULT,
    depth: int = 0,
) -> Dict[str, Any]:
    """Shallow-bounded copy: only JSON-safe atoms and shallow dict/list structures."""
    if not isinstance(m, Mapping):
        return {}
    out: Dict[str, Any] = {}
    keys = sorted(m.keys(), key=lambda k: str(k))[:max_keys]
    for k in keys:
        sk = _as_str(k)
        if not sk:
            continue
        val = m.get(k)
        if depth >= max_depth:
            out[sk] = _json_safe_atom(val)
            continue
        if isinstance(val, Mapping):
            out[sk] = _bounded_mapping(val, max_keys=max_keys, max_depth=max_depth, depth=depth + 1)
        elif isinstance(val, (list, tuple)):
            seq: List[Any] = []
            for item in list(val)[:_MAX_ID_LIST]:
                if isinstance(item, Mapping):
                    seq.append(_bounded_mapping(item, max_keys=max_keys, max_depth=max_depth, depth=depth + 1))
                else:
                    seq.append(_json_safe_atom(item))
            out[sk] = seq
        else:
            out[sk] = _json_safe_atom(val)
    return out


def legacy_transitional_noncombat_from_resolution(raw: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Transitional CTIR ``noncombat`` fill when ``resolution["noncombat_resolution"]`` is absent.

    Intentionally returns an empty dict: do not reconstruct non-combat semantics from raw
    exploration/social keys or hint-like payloads. Callers attach ``noncombat_resolution`` at
    the runtime seam instead (:mod:`game.noncombat_resolution`).
    """
    _ = raw
    return {}


def normalize_noncombat_slice(noncombat_resolution: Any) -> Dict[str, Any]:
    """Project engine ``noncombat_resolution`` into a bounded CTIR ``noncombat`` slice (no prose).

    Thin mapping only—no re-interpretation of hints or domain-specific raw keys.
    """
    if not isinstance(noncombat_resolution, Mapping):
        return {}
    nc = noncombat_resolution
    out: Dict[str, Any] = {}
    fv = _as_str(nc.get("framework_version"))
    if fv:
        out["framework_version"] = fv
    kind = _as_str(nc.get("kind")) or None
    if kind:
        out["kind"] = kind
    sub = _as_str(nc.get("subkind")) or None
    if sub:
        out["subkind"] = sub
    ad = _as_str(nc.get("authority_domain")) or None
    if ad:
        out["authority_domain"] = ad
    if "deterministic_resolved" in nc:
        out["deterministic_resolved"] = bool(nc.get("deterministic_resolved"))
    if "requires_check" in nc:
        out["requires_check"] = bool(nc.get("requires_check"))
    cr = nc.get("check_request")
    if isinstance(cr, Mapping):
        out["check_request"] = _bounded_mapping(cr, max_depth=3)
    ot = _as_str(nc.get("outcome_type")) or None
    if ot:
        out["outcome_type"] = ot
    ss = _as_str(nc.get("success_state")) or None
    if ss:
        out["success_state"] = ss

    blocked = nc.get("blocked_reason_codes")
    amb = nc.get("ambiguous_reason_codes")
    unsup = nc.get("unsupported_reason_codes")
    rc: Dict[str, List[str]] = {}
    if isinstance(blocked, (list, tuple)):
        rc["blocked"] = _sorted_unique_strs(list(blocked), limit=_MAX_NONCOMBAT_REASON_CODES)
    if isinstance(amb, (list, tuple)):
        rc["ambiguous"] = _sorted_unique_strs(list(amb), limit=_MAX_NONCOMBAT_REASON_CODES)
    if isinstance(unsup, (list, tuple)):
        rc["unsupported"] = _sorted_unique_strs(list(unsup), limit=_MAX_NONCOMBAT_REASON_CODES)
    if rc:
        out["reason_codes"] = rc

    de = nc.get("discovered_entities")
    if isinstance(de, (list, tuple)):
        ent: List[Any] = []
        for item in list(de)[:_MAX_NONCOMBAT_ENTITIES]:
            if isinstance(item, Mapping):
                ent.append(_bounded_mapping(item, max_depth=2))
            else:
                ent.append(_json_safe_atom(item))
        if ent:
            out["discovered_entities"] = ent

    sf = nc.get("surfaced_facts")
    if isinstance(sf, (list, tuple)):
        facts = [_clip_str(_as_str(x)) for x in list(sf)[:_MAX_NONCOMBAT_FACTS] if _as_str(x)]
        if facts:
            out["surfaced_facts"] = facts

    st = nc.get("state_changes")
    if isinstance(st, Mapping) and st:
        out["state_changes"] = _bounded_mapping(st, max_depth=2)

    ao = nc.get("authoritative_outputs")
    if isinstance(ao, (list, tuple)):
        rows: List[Any] = []
        for item in list(ao)[:_MAX_NONCOMBAT_AUTH_OUTPUTS]:
            if isinstance(item, Mapping):
                rows.append(_bounded_mapping(item, max_depth=2))
            else:
                rows.append(_json_safe_atom(item))
        if rows:
            out["authoritative_outputs"] = rows

    narr = nc.get("narration_constraints")
    if isinstance(narr, Mapping) and narr:
        out["narration_constraints"] = _bounded_mapping(narr, max_depth=2)

    return out


def normalize_intent(raw: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Normalize ``intent`` (classifier / routing snapshot; no prose)."""
    r = raw if isinstance(raw, dict) else {}
    raw_text = _as_str(r.get("raw_text"))
    normalized_kind = _as_str(r.get("normalized_kind")) or None
    mode = _as_str(r.get("mode")) or None
    classified_action = _as_str(r.get("classified_action")) or None
    requires_check = bool(r.get("requires_check")) if "requires_check" in r else False
    check_request = r.get("check_request")
    if check_request is not None and not isinstance(check_request, Mapping):
        check_request = _json_safe_atom(check_request)
    elif isinstance(check_request, Mapping):
        check_request = _bounded_mapping(check_request, max_depth=2)
    else:
        check_request = None
    targets = r.get("targets")
    if isinstance(targets, (list, tuple)):
        tgt_list = [_json_safe_atom(x) for x in list(targets)[:_MAX_ID_LIST]]
    elif targets is None:
        tgt_list = []
    else:
        tgt_list = [_json_safe_atom(targets)]
    labels = r.get("labels")
    if isinstance(labels, (list, tuple)):
        label_list = [_json_safe_atom(x) for x in list(labels)[:_MAX_ID_LIST]]
    elif labels is None:
        label_list = []
    else:
        label_list = [_json_safe_atom(labels)]
    return {
        "raw_text": raw_text or None,
        "normalized_kind": normalized_kind,
        "mode": mode,
        "classified_action": classified_action,
        "requires_check": requires_check,
        "check_request": check_request,
        "targets": tgt_list,
        "labels": label_list,
    }


def normalize_resolution(raw: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Normalize ``resolution`` (engine outcome summary; no prose blobs)."""
    r = raw if isinstance(raw, dict) else {}
    nc = r.get("noncombat_resolution") if isinstance(r.get("noncombat_resolution"), Mapping) else None
    kind = _as_str(r.get("kind")) or None
    outcome_type = _as_str(r.get("outcome_type")) or None
    success_state = _as_str(r.get("success_state")) or None
    consequences = r.get("consequences")
    if isinstance(consequences, (list, tuple)):
        cons = [_json_safe_atom(x) for x in list(consequences)[:_MAX_ID_LIST]]
    elif isinstance(consequences, Mapping):
        cons = _bounded_mapping(consequences, max_depth=2)
    elif consequences is None:
        cons = []
    else:
        cons = [_json_safe_atom(consequences)]
    auth = r.get("authoritative_outputs")
    if isinstance(auth, Mapping):
        authoritative_outputs = _bounded_mapping(auth, max_depth=2)
    elif auth is None:
        authoritative_outputs = {}
    else:
        authoritative_outputs = {"value": _json_safe_atom(auth)}
    out: Dict[str, Any] = {
        "kind": kind,
        "outcome_type": outcome_type,
        "success_state": success_state,
        "consequences": cons,
        "authoritative_outputs": authoritative_outputs,
    }
    # Optional bounded engine mirrors preserved for CTIR-first prompt reads (no prose blobs).
    soc = r.get("social")
    if isinstance(soc, Mapping) and nc is None:
        out["social"] = _bounded_mapping(soc, max_depth=2)
    sc = r.get("state_changes")
    if isinstance(sc, Mapping):
        out["state_changes"] = {
            k: bool(sc.get(k))
            for k in ("scene_transition_occurred", "arrived_at_scene", "new_scene_context_available")
            if k in sc
        }
    if "requires_check" in r:
        out["requires_check"] = bool(r.get("requires_check"))
    cr = r.get("check_request")
    if isinstance(cr, Mapping):
        out["check_request"] = _bounded_mapping(cr, max_depth=3)
    sk = r.get("skill_check")
    if isinstance(sk, Mapping):
        out["skill_check"] = _bounded_mapping(sk, max_depth=2)
    md = r.get("metadata")
    if isinstance(md, Mapping):
        out["metadata"] = _bounded_mapping(md, max_depth=2)
    for atom_key in ("label", "action_id", "resolved_transition", "target_scene_id"):
        if atom_key in r and r.get(atom_key) is not None:
            if atom_key == "resolved_transition" and isinstance(r.get(atom_key), Mapping):
                out[atom_key] = _bounded_mapping(r[atom_key], max_depth=2)
            else:
                out[atom_key] = _json_safe_atom(r.get(atom_key))
    pr = r.get("prompt")
    if isinstance(pr, str) and pr.strip():
        out["prompt"] = _clip_str(_as_str(pr))

    # Canonical non-combat contract overlays resolution semantics when embedded by the runtime seam.
    if nc is not None:
        nco = _as_str(nc.get("outcome_type"))
        if nco:
            out["outcome_type"] = nco
        ncs = _as_str(nc.get("success_state"))
        if ncs:
            out["success_state"] = ncs
        if "requires_check" in nc:
            out["requires_check"] = bool(nc.get("requires_check"))
        cr_nc = nc.get("check_request")
        if isinstance(cr_nc, Mapping):
            out["check_request"] = _bounded_mapping(cr_nc, max_depth=3)
        elif not bool(nc.get("requires_check")):
            out.pop("check_request", None)
    return out


def normalize_state_mutations(raw: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Normalize bounded mutation summaries (never full state mirrors)."""
    r = raw if isinstance(raw, dict) else {}

    def _summary_block(key: str) -> Dict[str, Any]:
        block = r.get(key)
        if not isinstance(block, Mapping):
            return {}
        out: Dict[str, Any] = {}
        if "changed_keys" in block:
            ck = block.get("changed_keys")
            if isinstance(ck, (list, tuple)):
                out["changed_keys"] = _sorted_unique_strs(list(ck), limit=_MAX_CHANGED_KEYS)
            else:
                out["changed_keys"] = []
        for atom_key in ("scene_id", "activate_scene_id", "combat_active", "round", "phase"):
            if atom_key in block:
                out[atom_key] = _json_safe_atom(block.get(atom_key))
        if "clue_ids" in block:
            v = block.get("clue_ids")
            if isinstance(v, (list, tuple)):
                out["clue_ids"] = _sorted_unique_strs(list(v), limit=_MAX_ID_LIST)
        if "lead_ids" in block:
            v = block.get("lead_ids")
            if isinstance(v, (list, tuple)):
                out["lead_ids"] = _sorted_unique_strs(list(v), limit=_MAX_ID_LIST)
        if "flags" in block and isinstance(block.get("flags"), Mapping):
            out["flags"] = _bounded_mapping(block["flags"], max_depth=2)
        return out

    scene = _summary_block("scene")
    session = _summary_block("session")
    combat = _summary_block("combat")
    clues_leads = _summary_block("clues_leads")
    return {
        "scene": scene,
        "session": session,
        "combat": combat,
        "clues_leads": clues_leads,
    }


def normalize_interaction(raw: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Normalize ``interaction`` (resolved targets / mode / continuity snapshot)."""
    r = raw if isinstance(raw, dict) else {}
    active_target_id = _as_str(r.get("active_target_id")) or None
    interaction_mode = _as_str(r.get("interaction_mode")) or None
    interaction_kind = _as_str(r.get("interaction_kind")) or None
    continuity = r.get("continuity")
    if isinstance(continuity, Mapping):
        continuity_snapshot = _bounded_mapping(continuity, max_depth=2)
    else:
        continuity_snapshot = {}
    responder = r.get("responder_target")
    if isinstance(responder, Mapping):
        responder_target = _bounded_mapping(responder, max_depth=2)
    elif responder is None:
        responder_target = {}
    else:
        responder_target = {"id": _json_safe_atom(responder)}
    speaker = r.get("speaker_target")
    if isinstance(speaker, Mapping):
        speaker_target = _bounded_mapping(speaker, max_depth=2)
    elif speaker is None:
        speaker_target = {}
    else:
        speaker_target = {"id": _json_safe_atom(speaker)}
    return {
        "active_target_id": active_target_id,
        "interaction_mode": interaction_mode,
        "interaction_kind": interaction_kind,
        "continuity_snapshot": continuity_snapshot,
        "responder_target": responder_target,
        "speaker_target": speaker_target,
    }


def normalize_world(raw: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Normalize bounded world deltas resolved this turn (no full world dump)."""
    r = raw if isinstance(raw, dict) else {}
    out: Dict[str, Any] = {}
    for key in ("pressure", "clocks", "factions", "projects", "events"):
        if key not in r:
            continue
        val = r.get(key)
        if isinstance(val, (list, tuple)):
            lst: List[Any] = []
            for item in list(val)[:_MAX_ID_LIST]:
                if isinstance(item, Mapping):
                    lst.append(_bounded_mapping(item, max_depth=2))
                else:
                    lst.append(_json_safe_atom(item))
            out[key] = lst
        elif isinstance(val, Mapping):
            out[key] = _bounded_mapping(val, max_depth=2)
        else:
            out[key] = _json_safe_atom(val)
    if "notes" in r:
        n = r.get("notes")
        if isinstance(n, (list, tuple)):
            out["notes"] = _sorted_unique_strs(list(n), limit=8)
        else:
            s = _clip_str(_as_str(n), max_len=128)
            out["notes"] = [s] if s else []
    return out


def normalize_narrative_anchors(raw: Mapping[str, Any] | None) -> Tuple[Dict[str, Any], List[str]]:
    """Normalize non-prose anchor buckets; returns (anchors, normalization_notes)."""
    notes: List[str] = []
    r = raw if isinstance(raw, dict) else {}

    def _strip_prose(obj: Any, *, ctx: str) -> Any:
        if isinstance(obj, Mapping):
            d: Dict[str, Any] = {}
            for k, v in obj.items():
                sk = _as_str(k)
                if sk in _PROSE_LIKE_KEYS:
                    notes.append(f"dropped_prose_like_key:{ctx}.{sk}")
                    continue
                d[sk] = _strip_prose(v, ctx=f"{ctx}.{sk}")
            return d
        if isinstance(obj, (list, tuple)):
            return [_strip_prose(x, ctx=ctx) for x in list(obj)[:_MAX_ID_LIST]]
        return _json_safe_atom(obj)

    buckets = ("scene_framing", "actors_speakers", "outcomes", "uncertainty", "next_leads_affordances")
    out: Dict[str, Any] = {}
    for b in buckets:
        block = r.get(b)
        if block is None:
            out[b] = []
            continue
        if isinstance(block, (list, tuple)):
            cleaned: List[Any] = []
            for i, item in enumerate(list(block)[:_MAX_ID_LIST]):
                cleaned.append(_strip_prose(item, ctx=f"{b}[{i}]"))
            out[b] = cleaned
        elif isinstance(block, Mapping):
            out[b] = [_strip_prose(block, ctx=b)]
        else:
            out[b] = [_json_safe_atom(block)]
    return out, notes


def normalize_provenance(
    *,
    builder_source: str,
    source_modules: Sequence[str] | None,
    signals_used: Sequence[str] | None,
    retry_safe_flags: Mapping[str, Any] | None,
    extras: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Normalize ``provenance`` (builder identity, inputs, stable flags)."""
    src = _clip_str(_as_str(builder_source))
    mods = _sorted_unique_strs(list(source_modules or []), limit=_MAX_ID_LIST)
    sigs = _sorted_unique_strs(list(signals_used or []), limit=_MAX_ID_LIST)
    flags = _bounded_mapping(retry_safe_flags, max_depth=2) if isinstance(retry_safe_flags, Mapping) else {}
    ext = _bounded_mapping(extras, max_depth=2) if isinstance(extras, Mapping) else {}
    return {
        "builder_source": src or None,
        "source_modules": mods,
        "signals_used": sigs,
        "retry_safe_flags": flags,
        "extras": ext,
    }


def normalize_debug(
    *,
    missing_optional_sections: Sequence[str],
    normalization_notes: Sequence[str],
) -> Dict[str, Any]:
    """Normalize ``debug`` (diagnostics only; no policy)."""
    return {
        "missing_optional_sections": _sorted_unique_strs(list(missing_optional_sections), limit=_MAX_ID_LIST),
        "normalization_notes": [
            _clip_str(_as_str(x)) for x in list(normalization_notes)[:_MAX_ID_LIST] if _as_str(x)
        ],
    }


def _validate_required_build_inputs(
    *,
    turn_id: Any,
    scene_id: Any,
    player_input: Any,
    builder_source: Any,
) -> Tuple[Any, Optional[str], str, str]:
    """Return normalized required fields or raise for malformed types."""
    if not isinstance(player_input, str):
        raise TypeError("player_input must be str")
    if not isinstance(builder_source, str):
        raise TypeError("builder_source must be str")
    bs = _as_str(builder_source)
    if not bs:
        raise ValueError("builder_source must be non-empty")
    if scene_id is not None and not isinstance(scene_id, str):
        raise TypeError("scene_id must be str or None")
    sid = _as_str(scene_id) or None if scene_id is not None else None
    return turn_id, sid, player_input, bs


def build_ctir(
    *,
    turn_id: Any,
    scene_id: str | None,
    player_input: str,
    builder_source: str,
    intent: Mapping[str, Any] | None = None,
    resolution: Mapping[str, Any] | None = None,
    state_mutations: Mapping[str, Any] | None = None,
    interaction: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    narrative_anchors: Mapping[str, Any] | None = None,
    source_modules: Sequence[str] | None = None,
    signals_used: Sequence[str] | None = None,
    retry_safe_flags: Mapping[str, Any] | None = None,
    provenance_extras: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build the canonical CTIR dict for one resolved turn.

    Accepts only explicit, bounded inputs. Callers must pass summaries and ids,
    not whole session/world/engine objects.
    """
    tid, sid, pin, bsrc = _validate_required_build_inputs(
        turn_id=turn_id,
        scene_id=scene_id,
        player_input=player_input,
        builder_source=builder_source,
    )
    n_intent = normalize_intent(intent)
    r_res = resolution if isinstance(resolution, dict) else {}
    nc_src = r_res.get("noncombat_resolution")
    n_noncombat = normalize_noncombat_slice(nc_src)
    if not n_noncombat:
        n_noncombat = legacy_transitional_noncombat_from_resolution(r_res)
    n_resolution = normalize_resolution(resolution)
    n_state = normalize_state_mutations(state_mutations)
    n_interaction = normalize_interaction(interaction)
    n_world = normalize_world(world)
    n_anchors, anchor_notes = normalize_narrative_anchors(narrative_anchors)
    n_prov = normalize_provenance(
        builder_source=bsrc,
        source_modules=source_modules,
        signals_used=signals_used,
        retry_safe_flags=retry_safe_flags,
        extras=provenance_extras,
    )

    missing_optional: List[str] = []
    if intent is None:
        missing_optional.append("intent_input")
    if resolution is None:
        missing_optional.append("resolution_input")
    if state_mutations is None:
        missing_optional.append("state_mutations_input")
    if interaction is None:
        missing_optional.append("interaction_input")
    if world is None:
        missing_optional.append("world_input")
    if narrative_anchors is None:
        missing_optional.append("narrative_anchors_input")

    notes: List[str] = list(anchor_notes)
    if not _is_json_serializable(n_world):
        notes.append("world_normalization_unexpected_nonserializable")

    n_debug = normalize_debug(
        missing_optional_sections=missing_optional,
        normalization_notes=notes,
    )

    return {
        "version": _CTIR_VERSION,
        "turn_id": tid,
        "scene_id": sid,
        "player_input": pin,
        "intent": n_intent,
        "resolution": n_resolution,
        "noncombat": n_noncombat,
        "state_mutations": n_state,
        "interaction": n_interaction,
        "world": n_world,
        "narrative_anchors": n_anchors,
        "provenance": n_prov,
        "debug": n_debug,
    }


def looks_like_ctir(obj: Any) -> bool:
    """Return True if *obj* appears to be a CTIR root dict (tiny, deterministic)."""
    if not isinstance(obj, dict):
        return False
    if obj.get("version") != _CTIR_VERSION:
        return False
    required = (
        "turn_id",
        "scene_id",
        "player_input",
        "intent",
        "resolution",
        "noncombat",
        "state_mutations",
        "interaction",
        "world",
        "narrative_anchors",
        "provenance",
        "debug",
    )
    for k in required:
        if k not in obj:
            return False
    prov = obj.get("provenance")
    if not isinstance(prov, dict) or not _as_str(prov.get("builder_source")):
        return False
    nc = obj.get("noncombat")
    if nc is not None and not isinstance(nc, dict):
        return False
    return True


def get_ctir_section(ctir: Mapping[str, Any] | None, section: str, default: Any = None) -> Any:
    """Return *section* from *ctir* if present and mapping/list as stored; else *default*."""
    if not isinstance(ctir, dict) or not section:
        return default
    if section not in ctir:
        return default
    return ctir.get(section, default)


def get_ctir_field(ctir: Mapping[str, Any] | None, dotted_path: str, default: Any = None) -> Any:
    """Resolve a dot-separated path such as ``intent.mode`` on *ctir*."""
    if not isinstance(ctir, dict) or not dotted_path:
        return default
    cur: Any = ctir
    for part in dotted_path.split("."):
        if not isinstance(cur, Mapping):
            return default
        if part not in cur:
            return default
        cur = cur[part]
    return cur
