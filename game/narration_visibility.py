"""Engine-owned narration visibility contract (read-only).

Builds a conservative snapshot of what entities and scene-layer facts are in scope
for narration matching. Does not enforce, rewrite, or mutate runtime state.
"""
from __future__ import annotations

import re
import string
from typing import Any, Dict, List, Optional, Set

from game.interaction_context import (
    addressable_scene_npc_id_universe,
    canonical_scene_addressable_roster,
    inspect,
    npc_dict_by_id,
)

_ALLOWED_NARRATION_SOURCES: Dict[str, str] = {
    "entity_reference": "visible_or_addressable_only",
    "fact_assertion": "visible_only",
}


def _normalize_visibility_text(value: Any) -> str:
    """Lowercase, collapse whitespace, strip edge punctuation (conservative matching)."""
    if not isinstance(value, str):
        return ""
    text = " ".join(value.split()).strip().lower()
    if not text:
        return ""
    punct = string.punctuation
    while text and text[0] in punct:
        text = text[1:].lstrip().lower()
        text = " ".join(text.split()).strip()
    while text and text[-1] in punct:
        text = text[:-1].rstrip().lower()
        text = " ".join(text.split()).strip()
    return text


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _inner_scene(scene_envelope: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(scene_envelope, dict):
        return {}
    inner = scene_envelope.get("scene")
    if isinstance(inner, dict):
        return inner
    return {}


def _coerce_scene_envelope(scene: Dict[str, Any] | None) -> Dict[str, Any]:
    """Treat ``scene`` as a full envelope or wrap a bare inner scene dict."""
    if not isinstance(scene, dict):
        return {}
    if isinstance(scene.get("scene"), dict):
        return scene
    return {"scene": scene}


def _resolve_scene_id(scene_envelope: Dict[str, Any], session: Dict[str, Any] | None) -> str:
    sid = str(_inner_scene(scene_envelope).get("id") or "").strip()
    if sid:
        return sid
    if not isinstance(session, dict):
        return ""
    st = session.get("scene_state")
    if isinstance(st, dict):
        sid = str(st.get("active_scene_id") or "").strip()
    if not sid:
        sid = str(session.get("active_scene_id") or "").strip()
    return sid


def _collect_scene_visible_fact_strings(scene_envelope: Dict[str, Any]) -> List[str]:
    inner = _inner_scene(scene_envelope)
    raw = inner.get("visible_facts")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        norm = _normalize_visibility_text(item)
        if norm:
            out.append(norm)
    return _dedupe_preserve_order(out)


def _discoverable_entry_to_text(entry: Any) -> str:
    if isinstance(entry, dict):
        return str(entry.get("text") or "").strip()
    if isinstance(entry, str):
        return entry.strip()
    return ""


def _collect_scene_discoverable_fact_strings(scene_envelope: Dict[str, Any]) -> List[str]:
    inner = _inner_scene(scene_envelope)
    raw = inner.get("discoverable_clues")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        text = _discoverable_entry_to_text(item)
        norm = _normalize_visibility_text(text)
        if norm:
            out.append(norm)
    return _dedupe_preserve_order(out)


def _collect_scene_hidden_fact_strings(scene_envelope: Dict[str, Any]) -> List[str]:
    inner = _inner_scene(scene_envelope)
    raw = inner.get("hidden_facts")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        norm = _normalize_visibility_text(item)
        if norm:
            out.append(norm)
    return _dedupe_preserve_order(out)


def _alias_bucket_from_row(row: Dict[str, Any], entity_id: str) -> List[str]:
    bucket: List[str] = []
    name = str(row.get("name") or "").strip()
    if name:
        nn = _normalize_visibility_text(name)
        if nn:
            bucket.append(nn)
    aliases_in = row.get("aliases")
    if isinstance(aliases_in, list):
        for a in aliases_in:
            if not isinstance(a, str):
                continue
            an = _normalize_visibility_text(a)
            if an and an not in bucket:
                bucket.append(an)
    if bucket:
        return bucket
    fallback = _normalize_visibility_text(entity_id.replace("_", " ").replace("-", " "))
    return [fallback] if fallback else []


def _world_npc_rows_for_visibility(world: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    w = world if isinstance(world, dict) else {}
    raw = w.get("npcs")
    if not isinstance(raw, list) or not raw:
        from game.defaults import default_world

        raw = default_world().get("npcs") or []
    if not isinstance(raw, list):
        return []
    return [npc for npc in raw if isinstance(npc, dict)]


def _collect_contract_entity_alias_map(
    roster: List[Dict[str, Any]],
    world: Dict[str, Any] | None,
) -> Dict[str, List[str]]:
    """Normalized alias strings per entity id for deterministic reference validation."""
    by_id: Dict[str, List[str]] = {}
    for row in roster:
        if not isinstance(row, dict):
            continue
        eid = str(row.get("id") or "").strip()
        if not eid:
            continue
        bucket = _alias_bucket_from_row(row, eid)
        if bucket:
            by_id[eid] = bucket

    for npc in _world_npc_rows_for_visibility(world):
        eid = str(npc.get("id") or "").strip()
        if not eid:
            continue
        bucket = _alias_bucket_from_row(npc, eid)
        if not bucket:
            continue
        current = by_id.get(eid, [])
        merged = list(current)
        for alias in bucket:
            if alias not in merged:
                merged.append(alias)
        if merged:
            by_id[eid] = merged
    return by_id


def _normalized_phrase_in_text(normalized_text: str, phrase: str) -> bool:
    if not normalized_text or not phrase:
        return False
    if normalized_text == phrase:
        return True
    return bool(re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", normalized_text))


def _normalized_fact_match_kind(normalized_text: str, fact: str) -> Optional[str]:
    if not normalized_text or not fact:
        return None
    if normalized_text == fact:
        return "exact"
    if fact in normalized_text:
        return "substring"
    return None


def _fact_check_entry(kind: str, fact: str, match_kind: str) -> Dict[str, str]:
    return {
        "kind": kind,
        "fact": fact,
        "match_kind": match_kind,
    }


def validate_player_facing_visibility(
    text: str,
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> Dict[str, Any]:
    contract = build_narration_visibility_contract(session=session, scene=scene, world=world)
    normalized_text = _normalize_visibility_text(text)
    visible_ids = {
        str(raw).strip()
        for raw in (contract.get("visible_entity_ids") or [])
        if isinstance(raw, str) and str(raw).strip()
    }
    alias_map = contract.get("visible_entity_aliases") if isinstance(contract.get("visible_entity_aliases"), dict) else {}
    visible_facts = [
        str(raw).strip()
        for raw in (contract.get("visible_fact_strings") or [])
        if isinstance(raw, str) and str(raw).strip()
    ]
    visible_fact_set = set(visible_facts)
    hidden_facts = [
        str(raw).strip()
        for raw in (contract.get("hidden_fact_strings") or [])
        if isinstance(raw, str) and str(raw).strip()
    ]
    discoverable_facts = [
        str(raw).strip()
        for raw in (contract.get("discoverable_fact_strings") or [])
        if isinstance(raw, str) and str(raw).strip()
    ]

    violations: List[Dict[str, Any]] = []
    checked_entities: List[Dict[str, Any]] = []
    checked_facts: List[Dict[str, Any]] = []

    for entity_id, raw_aliases in alias_map.items():
        if not isinstance(entity_id, str) or not entity_id.strip() or not isinstance(raw_aliases, list):
            continue
        matched_aliases: List[str] = []
        for raw_alias in raw_aliases:
            if not isinstance(raw_alias, str):
                continue
            alias = _normalize_visibility_text(raw_alias)
            if alias and _normalized_phrase_in_text(normalized_text, alias) and alias not in matched_aliases:
                matched_aliases.append(alias)
        if not matched_aliases:
            continue
        checked_entities.append(
            {
                "entity_id": entity_id,
                "matched_aliases": matched_aliases,
            }
        )
        if entity_id not in visible_ids:
            violations.append(
                {
                    "kind": "unseen_entity_reference",
                    "token": matched_aliases[0],
                    "matched_entity_id": entity_id,
                    "matched_fact": None,
                }
            )

    seen_fact_checks: Set[tuple[str, str]] = set()
    for fact_kind, facts, illegal in (
        ("hidden_fact_strings", hidden_facts, True),
        ("discoverable_fact_strings", discoverable_facts, True),
        ("visible_fact_strings", visible_facts, False),
    ):
        for fact in facts:
            match_kind = _normalized_fact_match_kind(normalized_text, fact)
            if not match_kind:
                continue
            key = (fact_kind, fact)
            if key not in seen_fact_checks:
                checked_facts.append(_fact_check_entry(fact_kind, fact, match_kind))
                seen_fact_checks.add(key)
            if illegal and fact not in visible_fact_set:
                violations.append(
                    {
                        "kind": "undiscovered_fact_assertion",
                        "token": fact,
                        "matched_entity_id": None,
                        "matched_fact": fact,
                    }
                )

    return {
        "ok": not violations,
        "violations": violations,
        "visibility_checked_entities": checked_entities,
        "visibility_checked_facts": checked_facts,
    }


def _resolve_active_interlocutor_id(session: Dict[str, Any] | None) -> Optional[str]:
    if not isinstance(session, dict):
        return None
    ctx = inspect(session)
    tid = str(ctx.get("active_interaction_target_id") or "").strip()
    if tid:
        return tid
    st = session.get("scene_state")
    if isinstance(st, dict):
        il = str(st.get("current_interlocutor") or "").strip()
        if il:
            return il
    return None


def build_narration_visibility_contract(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Return a read-only, conservative narration visibility snapshot (no mutations)."""
    env = _coerce_scene_envelope(scene)
    sid = _resolve_scene_id(env, session)
    w = world if isinstance(world, dict) else None

    visible_ids_set = addressable_scene_npc_id_universe(session, env, w)
    visible_entity_ids = sorted(visible_ids_set)

    inner_for_roster = env.get("scene")
    roster = canonical_scene_addressable_roster(
        w or {},
        sid,
        scene_envelope=env if isinstance(inner_for_roster, dict) else None,
        session=session if isinstance(session, dict) else None,
    )

    alias_map = _collect_contract_entity_alias_map(roster, w)
    visible_entity_names: List[str] = []
    for eid in visible_entity_ids:
        names = alias_map.get(eid)
        if names:
            visible_entity_names.append(names[0])
        else:
            fallback = _normalize_visibility_text(eid.replace("_", " "))
            visible_entity_names.append(fallback or eid.lower())

    return {
        "scene_id": sid or None,
        "visible_entity_ids": list(visible_entity_ids),
        "visible_entity_names": visible_entity_names,
        "visible_entity_aliases": dict(alias_map),
        "active_interlocutor_id": _resolve_active_interlocutor_id(session),
        "visible_fact_strings": _collect_scene_visible_fact_strings(env),
        "discoverable_fact_strings": _collect_scene_discoverable_fact_strings(env),
        "hidden_fact_strings": _collect_scene_hidden_fact_strings(env),
        "allowed_narration_sources": dict(_ALLOWED_NARRATION_SOURCES),
    }
