"""Objective 4 — canonical schema contracts, normalization, validation, and legacy adapters.

This module is the **single import surface** for canonical shapes and coercion rules
for engine payloads, world deltas, affordances, clues, projects, clocks, and scene
addressables. Runtime modules should gradually migrate here; legacy spellings are
accepted **only** through ``adapt_legacy_*`` helpers.

Debug / validation reasons use stable ``schema_contracts:<code>`` prefixes.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, FrozenSet, List, Mapping, MutableMapping, Optional, Tuple

RawDict = Dict[str, Any]
ValidationResult = Tuple[bool, List[str]]

# ---------------------------------------------------------------------------
# Shared normalization toolkit
# ---------------------------------------------------------------------------


def clean_optional_str(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    s = value.strip()
    return s or None


def normalize_enum(value: Any, allowed: FrozenSet[str], *, fallback: str) -> str:
    s = str(value or "").strip().lower()
    if s in allowed:
        return s
    return fallback


def normalize_str_list(value: Any, *, max_items: int = 256) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    if isinstance(value, (list, tuple)):
        out: List[str] = []
        for item in value:
            if isinstance(item, str):
                t = item.strip()
                if t:
                    out.append(t)
            elif item is not None:
                t = str(item).strip()
                if t:
                    out.append(t)
            if len(out) >= max_items:
                break
        return out
    t = str(value).strip()
    return [t] if t else []


def normalize_id(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    if isinstance(value, (int, float)):
        s = str(int(value)).strip()
        return s or None
    s = str(value).strip()
    return s or None


def merge_unknown_keys_into_metadata(
    raw: Mapping[str, Any],
    result: MutableMapping[str, Any],
    *,
    allowed: FrozenSet[str],
) -> None:
    """Copy keys from *raw* not in *allowed* onto ``result['metadata']['unknown_legacy_keys']``."""
    unknown: RawDict = {}
    for k, v in raw.items():
        if not isinstance(k, str):
            continue
        if k in allowed:
            continue
        unknown[k] = deepcopy(v)
    if not unknown:
        return
    meta = result.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
    bucket = meta.setdefault("unknown_legacy_keys", {})
    if isinstance(bucket, dict):
        bucket.update(unknown)
    result["metadata"] = meta


def drop_unknown_keys(
    raw: Mapping[str, Any],
    allowed: FrozenSet[str],
    *,
    park_unknown_in_metadata: bool = False,
    metadata_target: Optional[MutableMapping[str, Any]] = None,
) -> RawDict:
    """Return a shallow dict containing only *allowed* keys from *raw*.

    When ``park_unknown_in_metadata`` is true, unknown keys are copied onto
    ``metadata_target['unknown_legacy_keys']`` as a dict (never silently dropped).
    """
    out: RawDict = {}
    unknown: RawDict = {}
    for k, v in raw.items():
        if not isinstance(k, str):
            continue
        if k in allowed:
            out[k] = v
        else:
            unknown[k] = v
    if park_unknown_in_metadata and unknown:
        if metadata_target is not None:
            bucket = metadata_target.setdefault("unknown_legacy_keys", {})
            if isinstance(bucket, dict):
                bucket.update(unknown)
    return out


# ---------------------------------------------------------------------------
# Engine result (aligned with ``game.models`` exploration/combat/social)
# ---------------------------------------------------------------------------

# Note: runtime uses ``world_updates`` (plural), matching ``ExplorationEngineResult``.
ENGINE_RESULT_ALLOWED_TOP_KEYS: FrozenSet[str] = frozenset(
    {
        "kind",
        "action_id",
        "label",
        "prompt",
        "success",
        "hint",
        "resolved_transition",
        "target_scene_id",
        "clue_id",
        "discovered_clues",
        "world_updates",
        "state_changes",
        "metadata",
        "originating_scene_id",
        "interactable_id",
        "clue_text",
        "combat",
        "social",
        "skill_check",
        "check_request",
        "requires_check",
        # Combat legacy top-level mirrors (``CombatEngineResult.to_dict``)
        "hit",
        "damage",
        "round",
        "active_actor_id",
        "order",
    }
)


def _coerce_bool_or_none(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value == 0:
            return False
        if value == 1:
            return True
    return None


def normalize_engine_result(raw: Mapping[str, Any] | None) -> RawDict:
    """Return allowed engine-result keys with stable defaults (matches ``ExplorationEngineResult.to_dict`` presence rules)."""
    r = raw if isinstance(raw, dict) else {}
    success_raw = r.get("success")
    if success_raw is None:
        success_val: Any = None
    else:
        coerced = _coerce_bool_or_none(success_raw)
        success_val = coerced if coerced is not None else None

    d: RawDict = {
        "kind": str(r.get("kind") or "").strip(),
        "action_id": str(r.get("action_id") or "").strip(),
        "label": str(r.get("label") or "").strip(),
        "prompt": str(r.get("prompt") or "").strip(),
        "success": success_val,
        "resolved_transition": bool(r.get("resolved_transition")),
        "target_scene_id": clean_optional_str(r.get("target_scene_id")),
        "clue_id": clean_optional_str(r.get("clue_id")),
        "discovered_clues": normalize_str_list(r.get("discovered_clues")),
        "world_updates": deepcopy(r["world_updates"]) if isinstance(r.get("world_updates"), dict) else None,
        "state_changes": deepcopy(r["state_changes"]) if isinstance(r.get("state_changes"), dict) else {},
        "hint": str(r.get("hint") or "").strip(),
    }
    for opt in ("originating_scene_id", "interactable_id", "clue_text"):
        if opt in r and r.get(opt) is not None:
            d[opt] = clean_optional_str(r.get(opt))
    if isinstance(r.get("metadata"), dict) and r["metadata"]:
        d["metadata"] = deepcopy(r["metadata"])
    for sub in ("combat", "social", "skill_check", "check_request"):
        if isinstance(r.get(sub), dict) and r[sub]:
            d[sub] = deepcopy(r[sub])
    if "requires_check" in r:
        d["requires_check"] = bool(r.get("requires_check"))
    for legacy in ("hit", "damage", "round", "active_actor_id", "order"):
        if legacy in r:
            d[legacy] = r[legacy]
    merge_unknown_keys_into_metadata(r, d, allowed=ENGINE_RESULT_ALLOWED_TOP_KEYS)
    return drop_unknown_keys(d, ENGINE_RESULT_ALLOWED_TOP_KEYS, park_unknown_in_metadata=False)


ENGINE_RESULT_REQUIRED_KEYS: FrozenSet[str] = frozenset(
    {
        "kind",
        "action_id",
        "label",
        "prompt",
        "success",
        "resolved_transition",
        "target_scene_id",
        "clue_id",
        "discovered_clues",
        "world_updates",
        "state_changes",
        "hint",
    }
)


def validate_engine_result(d: Mapping[str, Any] | None) -> ValidationResult:
    reasons: List[str] = []
    if not isinstance(d, dict):
        return False, ["schema_contracts:engine_result:not_a_dict"]
    for k in d:
        if k not in ENGINE_RESULT_ALLOWED_TOP_KEYS:
            reasons.append(f"schema_contracts:engine_result:unknown_key:{k}")
    if reasons:
        return False, reasons
    for req in ENGINE_RESULT_REQUIRED_KEYS:
        if req not in d:
            reasons.append(f"schema_contracts:engine_result:missing_required:{req}")
    if not str(d.get("kind") or "").strip():
        reasons.append("schema_contracts:engine_result:empty_kind")
    if not str(d.get("action_id") or "").strip():
        reasons.append("schema_contracts:engine_result:empty_action_id")
    if "success" in d and d.get("success") is not None and not isinstance(d.get("success"), bool):
        reasons.append("schema_contracts:engine_result:invalid_success_type")
    if not isinstance(d.get("resolved_transition"), bool):
        reasons.append("schema_contracts:engine_result:invalid_resolved_transition_type")
    if d.get("discovered_clues") is not None and not isinstance(d.get("discovered_clues"), list):
        reasons.append("schema_contracts:engine_result:invalid_discovered_clues_type")
    if d.get("state_changes") is not None and not isinstance(d.get("state_changes"), dict):
        reasons.append("schema_contracts:engine_result:invalid_state_changes_type")
    if d.get("world_updates") is not None and not isinstance(d.get("world_updates"), dict):
        reasons.append("schema_contracts:engine_result:invalid_world_updates_type")
    if d.get("metadata") is not None and not isinstance(d.get("metadata"), dict):
        reasons.append("schema_contracts:engine_result:invalid_metadata_type")
    ok = not reasons
    return ok, reasons


def adapt_legacy_engine_result(raw: Mapping[str, Any] | None) -> RawDict:
    """Map legacy / alternate spellings into the shape ``normalize_engine_result`` expects.

    - ``world_update`` (singular) -> ``world_updates`` when ``world_updates`` absent.
    - ``transition_applied`` / ``resolved_transition`` booleans coerced together.
    """
    if not isinstance(raw, dict):
        return normalize_engine_result({})
    work = dict(raw)
    if "world_updates" not in work and isinstance(work.get("world_update"), dict):
        work["world_updates"] = work.pop("world_update")
    if "resolved_transition" not in work and "transition_applied" in work:
        work["resolved_transition"] = bool(work.get("transition_applied"))
    return normalize_engine_result(work)


def is_canonical_engine_result(d: Any) -> bool:
    ok, reasons = validate_engine_result(d if isinstance(d, dict) else None)
    if not ok:
        return False
    if not isinstance(d, dict):
        return False
    for k in d:
        if k not in ENGINE_RESULT_ALLOWED_TOP_KEYS:
            return False
    return True


# ---------------------------------------------------------------------------
# World update (patch-oriented contract; legacy GM / engine shapes adapted separately)
# ---------------------------------------------------------------------------

WORLD_UPDATE_ALLOWED_KEYS: FrozenSet[str] = frozenset(
    {
        "append_events",
        "flags_patch",
        "counters_patch",
        "clocks_patch",
        "projects_patch",
        "clues_patch",
        "npcs_patch",
        "leads_patch",
        "metadata",
    }
)


def _deepcopy_dict_mapping(m: Any) -> RawDict:
    return deepcopy(m) if isinstance(m, dict) else {}


def normalize_world_update(raw: Mapping[str, Any] | None) -> RawDict:
    r = raw if isinstance(raw, dict) else {}
    md_template: RawDict = {}
    filtered = drop_unknown_keys(
        r, WORLD_UPDATE_ALLOWED_KEYS, park_unknown_in_metadata=True, metadata_target=md_template
    )
    meta = deepcopy(r.get("metadata")) if isinstance(r.get("metadata"), dict) else {}
    u = md_template.get("unknown_legacy_keys")
    if isinstance(u, dict) and u:
        bucket = meta.setdefault("unknown_legacy_keys", {})
        if isinstance(bucket, dict):
            bucket.update(u)
    return {
        "append_events": list(filtered["append_events"])
        if isinstance(filtered.get("append_events"), list)
        else [],
        "flags_patch": _deepcopy_dict_mapping(filtered.get("flags_patch")),
        "counters_patch": _deepcopy_dict_mapping(filtered.get("counters_patch")),
        "clocks_patch": _deepcopy_dict_mapping(filtered.get("clocks_patch")),
        "projects_patch": [deepcopy(x) for x in filtered["projects_patch"]]
        if isinstance(filtered.get("projects_patch"), list)
        else [],
        "clues_patch": _deepcopy_dict_mapping(filtered.get("clues_patch")),
        "npcs_patch": [deepcopy(x) for x in filtered["npcs_patch"]]
        if isinstance(filtered.get("npcs_patch"), list)
        else [],
        "leads_patch": [deepcopy(x) for x in filtered["leads_patch"]]
        if isinstance(filtered.get("leads_patch"), list)
        else [],
        "metadata": meta,
    }


def validate_world_update(d: Mapping[str, Any] | None) -> ValidationResult:
    reasons: List[str] = []
    if not isinstance(d, dict):
        return False, ["schema_contracts:world_update:not_a_dict"]
    for k in d:
        if k not in WORLD_UPDATE_ALLOWED_KEYS:
            reasons.append(f"schema_contracts:world_update:unknown_key:{k}")
    if reasons:
        return False, reasons
    if not isinstance(d.get("append_events"), list):
        reasons.append("schema_contracts:world_update:append_events_not_list")
    if not isinstance(d.get("flags_patch"), dict):
        reasons.append("schema_contracts:world_update:flags_patch_not_dict")
    if not isinstance(d.get("counters_patch"), dict):
        reasons.append("schema_contracts:world_update:counters_patch_not_dict")
    if not isinstance(d.get("clocks_patch"), dict):
        reasons.append("schema_contracts:world_update:clocks_patch_not_dict")
    if not isinstance(d.get("projects_patch"), list):
        reasons.append("schema_contracts:world_update:projects_patch_not_list")
    if not isinstance(d.get("clues_patch"), dict):
        reasons.append("schema_contracts:world_update:clues_patch_not_dict")
    if not isinstance(d.get("npcs_patch"), list):
        reasons.append("schema_contracts:world_update:npcs_patch_not_list")
    if not isinstance(d.get("leads_patch"), list):
        reasons.append("schema_contracts:world_update:leads_patch_not_list")
    if d.get("metadata") is not None and not isinstance(d.get("metadata"), dict):
        reasons.append("schema_contracts:world_update:metadata_not_dict")
    return not reasons, reasons


def adapt_legacy_world_update(raw: Mapping[str, Any] | None) -> RawDict:
    """Adapt GM ``world_updates`` and exploration resolution fragments to canonical patches.

    Recognized legacy:
    - ``projects`` list -> ``projects_patch`` (entries preserved as dicts).
    - ``world_state`` with ``flags`` / ``counters`` / ``clocks`` -> respective *_patch.
    - ``set_flags`` / ``increment_counters`` / ``advance_clocks`` (engine resolution) ->
      ``flags_patch`` merge for set_flags; counter/clock deltas **only** in metadata
      (cannot be expressed as absolute patches without runtime read).
    """
    if not isinstance(raw, dict):
        return normalize_world_update({})
    md: RawDict = {}
    out: RawDict = {
        "append_events": normalize_str_list(raw.get("append_events")) if isinstance(raw.get("append_events"), list) else [],
        "flags_patch": {},
        "counters_patch": {},
        "clocks_patch": {},
        "projects_patch": [],
        "clues_patch": {},
        "npcs_patch": [],
        "leads_patch": [],
        "metadata": md,
    }
    if isinstance(raw.get("append_events"), list):
        ev: List[Any] = []
        for e in raw["append_events"]:
            if isinstance(e, dict):
                ev.append(deepcopy(e))
            elif isinstance(e, str) and e.strip():
                ev.append({"type": "note", "text": e.strip()})
        out["append_events"] = ev

    ws = raw.get("world_state")
    if isinstance(ws, dict):
        if isinstance(ws.get("flags"), dict):
            out["flags_patch"].update({k: v for k, v in ws["flags"].items() if isinstance(k, str) and k.strip() and not k.startswith("_")})
        if isinstance(ws.get("counters"), dict):
            for k, v in ws["counters"].items():
                if not isinstance(k, str) or not k.strip() or k.startswith("_"):
                    continue
                try:
                    out["counters_patch"][k] = int(v)
                except (TypeError, ValueError):
                    md.setdefault("legacy_rejected_counters", {})[k] = "schema_contracts:world_update:counter_not_int"
        if isinstance(ws.get("clocks"), dict):
            out["clocks_patch"].update(deepcopy(ws["clocks"]))

    if isinstance(raw.get("projects"), list):
        out["projects_patch"] = [deepcopy(p) for p in raw["projects"] if isinstance(p, dict)]

    sf = raw.get("set_flags")
    if isinstance(sf, dict):
        for k, v in sf.items():
            if isinstance(k, str) and k.strip() and not k.startswith("_"):
                out["flags_patch"][k] = v

    inc = raw.get("increment_counters")
    if isinstance(inc, dict) and inc:
        md["legacy_increment_counters"] = deepcopy(inc)

    adv = raw.get("advance_clocks")
    if isinstance(adv, dict) and adv:
        md["legacy_advance_clocks"] = deepcopy(adv)

    for copy_key in ("clues_patch", "npcs_patch", "leads_patch"):
        if isinstance(raw.get(copy_key), type(out[copy_key])):
            if copy_key.endswith("_patch") and isinstance(raw[copy_key], dict):
                out[copy_key] = deepcopy(raw[copy_key])
            elif isinstance(raw[copy_key], list):
                out[copy_key] = [deepcopy(x) for x in raw[copy_key]]

    if isinstance(raw.get("metadata"), dict):
        md.update(deepcopy(raw["metadata"]))

    # Park any remaining top-level legacy keys (e.g. assets, factions) so they are not silently dropped.
    _processed_incoming: FrozenSet[str] = frozenset(
        {
            "append_events",
            "world_state",
            "projects",
            "set_flags",
            "increment_counters",
            "advance_clocks",
            "clues_patch",
            "npcs_patch",
            "leads_patch",
            "metadata",
            "flags_patch",
            "counters_patch",
            "clocks_patch",
            "projects_patch",
        }
    )
    unk_bucket = md.setdefault("unknown_legacy_keys", {})
    if isinstance(unk_bucket, dict):
        for k, v in raw.items():
            if not isinstance(k, str) or k in _processed_incoming:
                continue
            unk_bucket[k] = deepcopy(v)

    return normalize_world_update(out)


def is_canonical_world_update(d: Any) -> bool:
    ok, _ = validate_world_update(d if isinstance(d, dict) else None)
    return ok


# ---------------------------------------------------------------------------
# Affordance
# ---------------------------------------------------------------------------

AFFORDANCE_ALLOWED_KEYS: FrozenSet[str] = frozenset(
    {"id", "type", "label", "prompt", "target_id", "target_kind", "target_scene_id", "target_location_id", "conditions", "metadata"}
)
AFFORDANCE_TYPES = frozenset(
    {"scene_transition", "investigate", "interact", "travel", "observe", "custom", "question", "talk", "speak", "persuade", "intimidate", "deceive"}
)


def normalize_affordance(raw: Mapping[str, Any] | None) -> RawDict:
    r = raw if isinstance(raw, dict) else {}
    meta = deepcopy(r.get("metadata")) if isinstance(r.get("metadata"), dict) else {}
    out: RawDict = {
        "id": normalize_id(r.get("id")) or "",
        "type": normalize_enum(r.get("type"), AFFORDANCE_TYPES, fallback="custom"),
        "label": str(r.get("label") or "").strip(),
        "prompt": str(r.get("prompt") or "").strip(),
        "target_id": clean_optional_str(r.get("target_id")),
        "target_kind": clean_optional_str(r.get("target_kind")),
        "target_scene_id": clean_optional_str(r.get("target_scene_id")),
        "target_location_id": clean_optional_str(r.get("target_location_id")),
        "conditions": deepcopy(r["conditions"]) if isinstance(r.get("conditions"), dict) else {},
        "metadata": meta,
    }
    merge_unknown_keys_into_metadata(r, out, allowed=AFFORDANCE_ALLOWED_KEYS)
    return drop_unknown_keys(out, AFFORDANCE_ALLOWED_KEYS, park_unknown_in_metadata=False)


def validate_affordance(d: Mapping[str, Any] | None) -> ValidationResult:
    reasons: List[str] = []
    if not isinstance(d, dict):
        return False, ["schema_contracts:affordance:not_a_dict"]
    for k in d:
        if k not in AFFORDANCE_ALLOWED_KEYS:
            reasons.append(f"schema_contracts:affordance:unknown_key:{k}")
    if not str(d.get("id") or "").strip():
        reasons.append("schema_contracts:affordance:empty_id")
    if not str(d.get("label") or "").strip():
        reasons.append("schema_contracts:affordance:empty_label")
    if d.get("conditions") is not None and not isinstance(d.get("conditions"), dict):
        reasons.append("schema_contracts:affordance:conditions_not_dict")
    if d.get("metadata") is not None and not isinstance(d.get("metadata"), dict):
        reasons.append("schema_contracts:affordance:metadata_not_dict")
    return not reasons, reasons


def adapt_legacy_affordance(raw: Mapping[str, Any] | None) -> RawDict:
    """Adapt ``normalize_scene_action`` / API camelCase into canonical snake_case."""
    if not isinstance(raw, dict):
        return normalize_affordance({})
    work: RawDict = dict(raw)
    # camelCase targets from scene_actions / clients
    if work.get("target_scene_id") is None:
        ts = work.get("targetSceneId")
        if ts is not None:
            work["target_scene_id"] = str(ts).strip() or None
    if work.get("target_id") is None:
        te = work.get("targetEntityId") or work.get("target_entity_id")
        if te is not None:
            work["target_id"] = str(te).strip() or None
    if work.get("target_location_id") is None:
        tl = work.get("targetLocationId") or work.get("target_location_id")
        if tl is not None:
            work["target_location_id"] = str(tl).strip() or None
    # Legacy category as type hint
    if not str(work.get("type") or "").strip():
        cat = str(work.get("category") or "").strip().lower()
        if cat:
            work["type"] = cat
    return normalize_affordance(work)


def is_canonical_affordance(d: Any) -> bool:
    ok, _ = validate_affordance(d if isinstance(d, dict) else None)
    return ok


# ---------------------------------------------------------------------------
# Interaction target / addressable
# ---------------------------------------------------------------------------

INTERACTION_TARGET_ALLOWED_KEYS: FrozenSet[str] = frozenset(
    {"id", "name", "scene_id", "kind", "address_roles", "aliases", "address_priority", "addressable", "metadata"}
)
ADDRESSABLE_KINDS = frozenset({"npc", "scene_actor", "crowd_actor"})


def normalize_interaction_target(raw: Mapping[str, Any] | None) -> RawDict:
    r = raw if isinstance(raw, dict) else {}
    roles = [s.strip().lower() for s in normalize_str_list(r.get("address_roles"))]
    aliases = normalize_str_list(r.get("aliases"))
    kind = normalize_enum(r.get("kind"), ADDRESSABLE_KINDS, fallback="scene_actor")
    ap = r.get("address_priority")
    try:
        address_priority = int(ap) if ap is not None else 100
    except (TypeError, ValueError):
        address_priority = 100
    addr = r.get("addressable")
    if addr is None:
        addressable = True
    else:
        addressable = bool(addr)
    meta = deepcopy(r.get("metadata")) if isinstance(r.get("metadata"), dict) else {}
    out = {
        "id": normalize_id(r.get("id")) or "",
        "name": str(r.get("name") or "").strip() or (normalize_id(r.get("id")) or ""),
        "scene_id": str(r.get("scene_id") or "").strip(),
        "kind": kind,
        "address_roles": roles,
        "aliases": aliases,
        "address_priority": address_priority,
        "addressable": addressable,
        "metadata": meta,
    }
    merge_unknown_keys_into_metadata(r, out, allowed=INTERACTION_TARGET_ALLOWED_KEYS)
    return drop_unknown_keys(out, INTERACTION_TARGET_ALLOWED_KEYS, park_unknown_in_metadata=False)


def validate_interaction_target(d: Mapping[str, Any] | None) -> ValidationResult:
    reasons: List[str] = []
    if not isinstance(d, dict):
        return False, ["schema_contracts:interaction_target:not_a_dict"]
    for k in d:
        if k not in INTERACTION_TARGET_ALLOWED_KEYS:
            reasons.append(f"schema_contracts:interaction_target:unknown_key:{k}")
    if not str(d.get("id") or "").strip():
        reasons.append("schema_contracts:interaction_target:empty_id")
    if not isinstance(d.get("address_roles"), list):
        reasons.append("schema_contracts:interaction_target:address_roles_not_list")
    if not isinstance(d.get("aliases"), list):
        reasons.append("schema_contracts:interaction_target:aliases_not_list")
    if not isinstance(d.get("address_priority"), int):
        reasons.append("schema_contracts:interaction_target:address_priority_not_int")
    if not isinstance(d.get("addressable"), bool):
        reasons.append("schema_contracts:interaction_target:addressable_not_bool")
    return not reasons, reasons


def adapt_legacy_interaction_target(raw: Mapping[str, Any] | None, *, scene_id_fallback: str = "") -> RawDict:
    """Normalize scene addressable / roster row; optional ``actor_id`` -> ``id`` only when unambiguous."""
    if not isinstance(raw, dict):
        return normalize_interaction_target({})
    work = dict(raw)
    if not normalize_id(work.get("id")):
        aid = normalize_id(work.get("actor_id"))
        if aid:
            work["id"] = aid
    if not str(work.get("scene_id") or "").strip() and scene_id_fallback:
        work["scene_id"] = scene_id_fallback
    meta = work.get("metadata") if isinstance(work.get("metadata"), dict) else {}
    for extra in ("role", "topics", "disposition"):
        if extra in work and extra not in meta:
            meta.setdefault("legacy_addressable_fields", {})[extra] = work[extra]
    work["metadata"] = meta
    return normalize_interaction_target(work)


def is_canonical_interaction_target(d: Any) -> bool:
    ok, _ = validate_interaction_target(d if isinstance(d, dict) else None)
    return ok


# ---------------------------------------------------------------------------
# Clue
# ---------------------------------------------------------------------------

CLUE_ALLOWED_KEYS: FrozenSet[str] = frozenset(
    {
        "id",
        "text",
        "state",
        "presentation",
        "source_scene_id",
        "canonical_lead_id",
        "leads_to_scene_id",
        "leads_to_npc_id",
        "lead_type",
        "metadata",
    }
)
CLUE_STATES = frozenset({"unknown", "hidden", "discoverable", "discovered", "surfaced"})
LEAD_TYPES = frozenset({"scene", "npc", "rumor", "generic", ""})


def normalize_clue(raw: Mapping[str, Any] | None) -> RawDict:
    r = raw if isinstance(raw, dict) else {}
    meta = deepcopy(r.get("metadata")) if isinstance(r.get("metadata"), dict) else {}
    cid = normalize_id(r.get("id"))
    text = str(r.get("text") or "").strip()
    out = {
        "id": cid or "",
        "text": text,
        "state": normalize_enum(r.get("state"), CLUE_STATES, fallback="unknown"),
        "presentation": clean_optional_str(r.get("presentation")),
        "source_scene_id": clean_optional_str(r.get("source_scene_id")),
        "canonical_lead_id": clean_optional_str(r.get("canonical_lead_id")),
        "leads_to_scene_id": clean_optional_str(r.get("leads_to_scene_id")),
        "leads_to_npc_id": clean_optional_str(r.get("leads_to_npc_id")),
        "lead_type": normalize_enum(r.get("lead_type"), LEAD_TYPES, fallback=""),
        "metadata": meta,
    }
    merge_unknown_keys_into_metadata(r, out, allowed=CLUE_ALLOWED_KEYS)
    return drop_unknown_keys(out, CLUE_ALLOWED_KEYS, park_unknown_in_metadata=False)


def validate_clue(d: Mapping[str, Any] | None) -> ValidationResult:
    reasons: List[str] = []
    if not isinstance(d, dict):
        return False, ["schema_contracts:clue:not_a_dict"]
    for k in d:
        if k not in CLUE_ALLOWED_KEYS:
            reasons.append(f"schema_contracts:clue:unknown_key:{k}")
    if not str(d.get("id") or "").strip():
        reasons.append("schema_contracts:clue:empty_id")
    if d.get("metadata") is not None and not isinstance(d.get("metadata"), dict):
        reasons.append("schema_contracts:clue:metadata_not_dict")
    return not reasons, reasons


def adapt_legacy_clue(raw: Any) -> RawDict:
    """Adapt string clues or ``game.gm.normalize_clue_record`` output to canonical clue."""
    if isinstance(raw, str):
        from game.utils import slugify

        text = raw.strip()
        cid = slugify(text or "clue")
        return normalize_clue({"id": cid, "text": text, "state": "discoverable"})
    if not isinstance(raw, dict):
        return normalize_clue({})
    work = dict(raw)
    if work.get("source_scene_id") is None:
        ss = work.get("source_scene") or work.get("sourceSceneId")
        if isinstance(ss, str) and ss.strip():
            work["source_scene_id"] = ss.strip()
        work.pop("source_scene", None)
        work.pop("sourceSceneId", None)
    if "leads_to_scene_id" not in work and isinstance(work.get("leads_to_scene"), str):
        work["leads_to_scene_id"] = work.pop("leads_to_scene").strip() or None
    if "leads_to_npc_id" not in work and isinstance(work.get("leads_to_npc"), str):
        work["leads_to_npc_id"] = work.pop("leads_to_npc").strip() or None
    if isinstance(work.get("leads_to_rumor"), str) and work["leads_to_rumor"].strip():
        meta = dict(work.get("metadata") or {})
        meta.setdefault("legacy_lead_rumor", work["leads_to_rumor"].strip())
        work["metadata"] = meta
        work["lead_type"] = work.get("lead_type") or "rumor"
        work.pop("leads_to_rumor", None)
    # reveal_requires / links_to -> metadata only
    meta = dict(work.get("metadata") or {})
    for legacy_key in ("reveal_requires", "links_to"):
        if legacy_key in work:
            meta[legacy_key] = deepcopy(work[legacy_key])
            work.pop(legacy_key, None)
    work["metadata"] = meta
    # ``type`` on persisted/world clues often carries engine :class:`~game.leads.LeadType` spellings.
    if work.get("type") is not None and not str(work.get("lead_type") or "").strip():
        meta2 = dict(work.get("metadata") or {})
        meta2["engine_lead_type"] = str(work.get("type") or "").strip().lower()
        work["metadata"] = meta2
        work.pop("type", None)
    if not work.get("state"):
        work["state"] = "discoverable"
    return normalize_clue(work)


def is_canonical_clue(d: Any) -> bool:
    ok, _ = validate_clue(d if isinstance(d, dict) else None)
    return ok


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

PROJECT_ALLOWED_KEYS: FrozenSet[str] = frozenset(
    {"id", "name", "category", "status", "progress", "target", "tags", "notes", "metadata"}
)


def normalize_project(raw: Mapping[str, Any] | None) -> RawDict:
    from game.projects import normalize_project_entry

    r = raw if isinstance(raw, dict) else {}
    base = normalize_project_entry(r)
    if not base:
        meta = deepcopy(r.get("metadata")) if isinstance(r.get("metadata"), dict) else {}
        return {
            "id": "",
            "name": "",
            "category": "infrastructure",
            "status": "active",
            "progress": 0,
            "target": 1,
            "tags": [],
            "notes": "",
            "metadata": meta,
        }
    meta = deepcopy(r.get("metadata")) if isinstance(r.get("metadata"), dict) else {}
    out = {**base, "metadata": meta}
    merge_unknown_keys_into_metadata(r, out, allowed=PROJECT_ALLOWED_KEYS)
    return drop_unknown_keys(out, PROJECT_ALLOWED_KEYS, park_unknown_in_metadata=False)


def validate_project(d: Mapping[str, Any] | None) -> ValidationResult:
    reasons: List[str] = []
    if not isinstance(d, dict):
        return False, ["schema_contracts:project:not_a_dict"]
    for k in d:
        if k not in PROJECT_ALLOWED_KEYS:
            reasons.append(f"schema_contracts:project:unknown_key:{k}")
    if not str(d.get("id") or "").strip():
        reasons.append("schema_contracts:project:empty_id")
    for nk in ("progress", "target"):
        if nk in d and not isinstance(d.get(nk), int):
            reasons.append(f"schema_contracts:project:{nk}_not_int")
    if d.get("tags") is not None and not isinstance(d.get("tags"), list):
        reasons.append("schema_contracts:project:tags_not_list")
    return not reasons, reasons


def adapt_legacy_project(raw: Mapping[str, Any] | None) -> RawDict:
    """Accept ``goal`` -> ``target`` and ``completed`` -> ``status`` via ``game.projects`` rules."""
    if not isinstance(raw, dict):
        return normalize_project({})
    work = dict(raw)
    if "target" not in work and "goal" in work:
        work["target"] = work.get("goal")
    if isinstance(work.get("status"), str) and work["status"].strip().lower() == "completed":
        work["status"] = "complete"
    return normalize_project(work)


def is_canonical_project(d: Any) -> bool:
    ok, _ = validate_project(d if isinstance(d, dict) else None)
    return ok


# ---------------------------------------------------------------------------
# Clock
# ---------------------------------------------------------------------------

CLOCK_ALLOWED_KEYS: FrozenSet[str] = frozenset({"id", "value", "min_value", "max_value", "scope", "metadata"})
CLOCK_SCOPES = frozenset({"world", "scene", "faction", "project", "generic", ""})


def normalize_clock(raw: Mapping[str, Any] | None) -> RawDict:
    r = raw if isinstance(raw, dict) else {}
    meta = deepcopy(r.get("metadata")) if isinstance(r.get("metadata"), dict) else {}
    cid = normalize_id(r.get("id"))
    try:
        value = int(r.get("value", 0))
    except (TypeError, ValueError):
        value = 0
    try:
        min_value = int(r.get("min_value", 0))
    except (TypeError, ValueError):
        min_value = 0
    try:
        max_value = int(r.get("max_value", 10))
    except (TypeError, ValueError):
        max_value = 10
    if max_value < 1:
        max_value = 1
    scope = normalize_enum(r.get("scope"), CLOCK_SCOPES, fallback="")
    out = {
        "id": cid or "",
        "value": value,
        "min_value": min_value,
        "max_value": max_value,
        "scope": scope,
        "metadata": meta,
    }
    merge_unknown_keys_into_metadata(r, out, allowed=CLOCK_ALLOWED_KEYS)
    return drop_unknown_keys(out, CLOCK_ALLOWED_KEYS, park_unknown_in_metadata=False)


def validate_clock(d: Mapping[str, Any] | None) -> ValidationResult:
    reasons: List[str] = []
    if not isinstance(d, dict):
        return False, ["schema_contracts:clock:not_a_dict"]
    for k in d:
        if k not in CLOCK_ALLOWED_KEYS:
            reasons.append(f"schema_contracts:clock:unknown_key:{k}")
    if not str(d.get("id") or "").strip():
        reasons.append("schema_contracts:clock:empty_id")
    for nk in ("value", "min_value", "max_value"):
        if nk in d and not isinstance(d.get(nk), int):
            reasons.append(f"schema_contracts:clock:{nk}_not_int")
    return not reasons, reasons


def adapt_legacy_clock(raw: Mapping[str, Any] | None) -> RawDict:
    """Map ``{name, progress, max}`` world_state clock rows into canonical clock."""
    if not isinstance(raw, dict):
        return normalize_clock({})
    work = dict(raw)
    if not work.get("id"):
        nm = normalize_id(work.get("name"))
        if nm:
            work["id"] = nm
    if "value" not in work and "progress" in work:
        work["value"] = work.get("progress")
    if work.get("max_value") in (None, 0, "") and "max" in work:
        work["max_value"] = work.get("max")
    return normalize_clock(work)


def is_canonical_clock(d: Any) -> bool:
    ok, _ = validate_clock(d if isinstance(d, dict) else None)
    return ok


def coerce_world_state_clock_row(clock_key: str, raw: Any) -> RawDict:
    """Normalize a ``world.world_state.clocks[clock_key]`` value (legacy ``progress``/``max`` or canonical)."""
    cid = normalize_id(clock_key) or (str(clock_key).strip() if isinstance(clock_key, str) else "")
    if not isinstance(raw, dict):
        return normalize_clock(
            {"id": cid, "value": 0, "min_value": 0, "max_value": 10, "scope": "world", "metadata": {}}
        )
    work = dict(raw)
    if not normalize_id(work.get("id")):
        work["id"] = cid
    if not str(work.get("scope") or "").strip():
        work["scope"] = "world"
    return normalize_clock(adapt_legacy_clock(work))


def world_clock_row_summary_line(clock_key: str, raw: Any) -> str | None:
    """``'{id}: value/max_value'`` for prompt summaries; accepts legacy stored rows."""
    if not isinstance(clock_key, str) or clock_key.startswith("_"):
        return None
    c = coerce_world_state_clock_row(clock_key, raw if isinstance(raw, dict) else {})
    return f"{c['id']}: {int(c['value'])}/{int(c['max_value'])}"
