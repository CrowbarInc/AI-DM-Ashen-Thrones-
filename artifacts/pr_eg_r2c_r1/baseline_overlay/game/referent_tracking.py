"""Deterministic referent / clause tracking artifact (Objective #7 foundation; N5 extension).

**Owner:** JSON-safe referent-tracking construction and validation — a **derivative-only**
bounded structural projection (pronoun risk, explicit referents, interaction-target
continuity). Does **not** mutate adjudication, routing, CTIR meaning, world truth, or
state-authority domains; not a second semantic authority.

**N5:** Optional ``clause_referent_plan`` is the only canonical artifact field for
per-slot referent metadata (**bounded structural aid**: ids, labels, flags). Built
here only — **not** a prose parser, narrative planner, or truth/meaning owner.
``game.prompt_context`` / gate code are **read-side** consumers only; contract:
``docs/clause_level_referent_tracking.md``. On conflict, CTIR, interaction, visibility,
and engine truth win; this module records bounded traces only.

**Not owner:** NLP parsing, prose resolution, prompt assembly, gate enforcement, or
orchestration. ``recent_structured_memory_entities`` must be pre-bounded structured
rows (explicit ids), not a semantic source of truth.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

REFERENT_TRACKING_ARTIFACT_VERSION = 1

_MAX_ID_LEN = 96
_MAX_STR_CLIP = 160
_MAX_ENTITY_LIST = 48
_MAX_CODES = 64
_MAX_MEMORY_ENTITIES = 12

_PERSON_LIKE_KINDS = frozenset(
    {"npc", "scene_actor", "creature", "humanoid", "person", "pc", "player"}
)

_VALID_PRONOUN_BUCKETS = frozenset({"he_him", "she_her", "they_them", "it_its", "unknown"})

# N5 optional ``clause_referent_plan`` lane (``docs/clause_level_referent_tracking.md``).
_MAX_CLAUSE_PLAN_ROWS = 8
_MAX_CLAUSE_CANDIDATES = 16
_MAX_CLAUSE_LABELS = 8
_MAX_CLAUSE_ID_LEN = 128

_CLAUSE_ROW_KEYS = frozenset(
    {
        "clause_id",
        "clause_kind",
        "subject_candidate_ids",
        "object_candidate_ids",
        "preferred_subject_id",
        "preferred_object_id",
        "allowed_explicit_labels",
        "risky_pronoun_buckets",
        "target_switch_sensitive",
        "ambiguity_class",
    }
)

_CLAUSE_KINDS = frozenset(
    {
        "speaker_subject",
        "interaction_target",
        "continuity_object",
        "addressed_entities",
    }
)

_CLAUSE_AMBIGUITY_CLASSES = frozenset({"none", "ambiguous_plural", "ambiguous_singular", "no_anchor"})

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


def referent_tracking_artifact_version() -> int:
    return REFERENT_TRACKING_ARTIFACT_VERSION


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


def _mapping(d: Any) -> Dict[str, Any]:
    return dict(d) if isinstance(d, Mapping) else {}


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


def json_safe_sanitize(value: Any, *, max_depth: int = 6, _depth: int = 0) -> Any:
    """Return a JSON-serializable copy with depth/list bounds (conservative)."""
    if _depth > max_depth:
        return None
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, Mapping):
        out: Dict[str, Any] = {}
        keys = sorted(value.keys(), key=lambda k: str(k))[:32]
        for k in keys:
            sk = _as_str(k)
            if not sk or sk.lower() in _PROSE_INSTRUCTION_KEYS:
                continue
            out[sk] = json_safe_sanitize(value[k], max_depth=max_depth, _depth=_depth + 1)
        return out
    if isinstance(value, (list, tuple)):
        return [json_safe_sanitize(x, max_depth=max_depth, _depth=_depth + 1) for x in list(value)[:_MAX_ENTITY_LIST]]
    return str(value)


def normalize_entity_id(raw: Any) -> str:
    return _clip(_as_str(raw), max_len=_MAX_ID_LEN)


def extract_visible_entity_slice(narration_visibility: Mapping[str, Any] | None) -> Tuple[List[str], Dict[str, str], Dict[str, str], Dict[str, List[str]]]:
    """Return (sorted_ids, id_to_name, id_to_kind, id_to_roles) from a visibility contract."""
    if not isinstance(narration_visibility, Mapping):
        return [], {}, {}, {}
    ids_raw = narration_visibility.get("visible_entity_ids") or []
    if not isinstance(ids_raw, list):
        return [], {}, {}, {}
    names = narration_visibility.get("visible_entity_names") if isinstance(narration_visibility.get("visible_entity_names"), list) else []
    kinds = narration_visibility.get("visible_entity_kinds") if isinstance(narration_visibility.get("visible_entity_kinds"), Mapping) else {}
    roles = narration_visibility.get("visible_entity_roles") if isinstance(narration_visibility.get("visible_entity_roles"), Mapping) else {}

    seen: set[str] = set()
    ordered: List[str] = []
    id_to_name: Dict[str, str] = {}
    id_to_kind: Dict[str, str] = {}
    id_to_roles: Dict[str, List[str]] = {}

    for i, raw in enumerate(ids_raw):
        eid = normalize_entity_id(raw)
        if not eid or eid in seen:
            continue
        seen.add(eid)
        ordered.append(eid)
        if i < len(names):
            nm = _clip(_as_str(names[i]), max_len=_MAX_STR_CLIP)
            if nm:
                id_to_name[eid] = nm
        k = kinds.get(eid) if isinstance(kinds, Mapping) else None
        if k is not None:
            id_to_kind[eid] = _clip(_as_str(k), max_len=64)
        rl = roles.get(eid) if isinstance(roles, Mapping) else None
        if isinstance(rl, (list, tuple)):
            id_to_roles[eid] = _sorted_unique_strs(list(rl), limit=8)

        if len(ordered) >= _MAX_ENTITY_LIST:
            break

    ordered_sorted = sorted(ordered)
    return ordered_sorted, id_to_name, id_to_kind, id_to_roles


def merge_descriptors_from_narrative_plan(
    visible_ids: Set[str],
    narrative_plan: Mapping[str, Any] | None,
    base_names: Dict[str, str],
) -> Dict[str, str]:
    """Merge display descriptors from plan rows; only ids in *visible_ids*."""
    names = dict(base_names)
    if not isinstance(narrative_plan, Mapping):
        return names
    aer = narrative_plan.get("allowable_entity_references")
    if not isinstance(aer, list):
        return names
    for row in aer:
        if not isinstance(row, Mapping):
            continue
        eid = normalize_entity_id(row.get("entity_id") or row.get("id"))
        if not eid or eid not in visible_ids:
            continue
        desc = _as_str(row.get("descriptor") or row.get("display_name") or row.get("name"))
        if desc:
            names[eid] = _clip(desc, max_len=_MAX_STR_CLIP)
    return names


def extract_interaction_target_signals(
    *,
    session_interaction: Mapping[str, Any] | None,
    interaction_continuity: Mapping[str, Any] | None,
    turn_packet: Mapping[str, Any] | None,
    narrative_plan: Mapping[str, Any] | None,
) -> List[Tuple[str, str]]:
    """Return list of (source_tag, entity_id_or_empty) in deterministic probe order."""
    out: List[Tuple[str, str]] = []
    si = _mapping(session_interaction)
    val = normalize_entity_id(si.get("active_interaction_target_id"))
    if val:
        out.append(("session_interaction.active_interaction_target_id", val))

    ic = _mapping(interaction_continuity)
    val = normalize_entity_id(ic.get("active_interaction_target_id"))
    if val:
        out.append(("interaction_continuity.active_interaction_target_id", val))

    tp = _mapping(turn_packet)
    route = _mapping(tp.get("route"))
    val = normalize_entity_id(route.get("active_target_id"))
    if val:
        out.append(("turn_packet.route.active_target_id", val))

    plan = _mapping(narrative_plan)
    sa = _mapping(plan.get("scene_anchors"))
    val = normalize_entity_id(sa.get("active_target"))
    if val:
        out.append(("narrative_plan.scene_anchors.active_target", val))
    val = normalize_entity_id(sa.get("active_interlocutor"))
    if val:
        out.append(("narrative_plan.scene_anchors.active_interlocutor", val))
    return out


def choose_active_interaction_target(signals: Sequence[Tuple[str, str]]) -> Tuple[Optional[str], List[str], List[str]]:
    """First non-empty wins; record all non-empty for conflict detection."""
    sources_used: List[str] = []
    ids: List[str] = []
    chosen: Optional[str] = None
    for src, eid in signals:
        if not eid:
            continue
        sources_used.append(src)
        ids.append(eid)
        if chosen is None:
            chosen = eid
    return chosen, sources_used, ids


def extract_speaker_candidate_ids(speaker_selection: Mapping[str, Any] | None) -> List[str]:
    if not isinstance(speaker_selection, Mapping):
        return []
    out: List[str] = []
    seen: set[str] = set()
    pid = normalize_entity_id(speaker_selection.get("primary_speaker_id"))
    if pid and pid not in seen:
        seen.add(pid)
        out.append(pid)
    allowed = speaker_selection.get("allowed_speaker_ids")
    if isinstance(allowed, (list, tuple)):
        for x in allowed:
            eid = normalize_entity_id(x)
            if eid and eid not in seen:
                seen.add(eid)
                out.append(eid)
    return out[:_MAX_ENTITY_LIST]


def build_pronoun_candidate_map(
    visible_ids: Sequence[str],
    *,
    explicit_buckets: Mapping[str, Sequence[Any]] | None,
    visibility_extension: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Deterministic pronoun bucket map: explicit structured only; else neutral ``they_them``."""
    ext = _mapping(visibility_extension)
    # Optional seam: visibility dict may carry ``visible_entity_pronoun_buckets`` (engine-owned).
    from_visibility: Dict[str, List[str]] = {}
    raw_vm = ext.get("visible_entity_pronoun_buckets")
    if isinstance(raw_vm, Mapping):
        for k, v in raw_vm.items():
            eid = normalize_entity_id(k)
            if not eid:
                continue
            buckets: List[str] = []
            if isinstance(v, (list, tuple)):
                for item in v:
                    b = _as_str(item).lower().replace(" ", "_")
                    if b in _VALID_PRONOUN_BUCKETS:
                        buckets.append(b)
            elif isinstance(v, str) and _as_str(v).lower().replace(" ", "_") in _VALID_PRONOUN_BUCKETS:
                buckets.append(_as_str(v).lower().replace(" ", "_"))
            if buckets:
                from_visibility[eid] = _sorted_unique_strs(buckets, limit=8)

    explicit_map: Dict[str, List[str]] = {}
    if isinstance(explicit_buckets, Mapping):
        for k, seq in explicit_buckets.items():
            eid = normalize_entity_id(k)
            if not eid:
                continue
            acc: List[str] = []
            if isinstance(seq, (list, tuple)):
                for item in seq:
                    b = _as_str(item).lower().replace(" ", "_")
                    if b in _VALID_PRONOUN_BUCKETS:
                        acc.append(b)
            if acc:
                explicit_map[eid] = _sorted_unique_strs(acc, limit=8)

    merged_explicit: Dict[str, List[str]] = {}
    for eid in sorted(set(from_visibility.keys()) | set(explicit_map.keys())):
        merged: List[str] = []
        seen: set[str] = set()
        for bucket in (from_visibility.get(eid) or []) + (explicit_map.get(eid) or []):
            if bucket not in seen:
                seen.add(bucket)
                merged.append(bucket)
        merged_explicit[eid] = sorted(merged)

    buckets_by_entity: Dict[str, List[str]] = {}
    strategy = "neutral_buckets"
    if merged_explicit:
        strategy = "explicit_structured"

    for eid in sorted(visible_ids):
        if eid in merged_explicit and merged_explicit[eid]:
            buckets_by_entity[eid] = list(merged_explicit[eid])
        else:
            buckets_by_entity[eid] = ["they_them"]

    explicit_sources: List[str] = []
    if from_visibility:
        explicit_sources.append("visibility.visible_entity_pronoun_buckets")
    if explicit_map:
        explicit_sources.append("kwargs.explicit_entity_pronoun_buckets")

    return {
        "strategy": strategy,
        "buckets_by_entity": buckets_by_entity,
        "explicit_sources": sorted(set(explicit_sources)),
    }


def score_ambiguity_risk(
    *,
    visible_ids: Sequence[str],
    id_to_kind: Mapping[str, str],
    id_to_roles: Mapping[str, List[str]],
    speaker_candidates: Sequence[str],
    conflicting_target_ids: bool,
    person_like_count: int,
    has_explicit_pronoun_structure: bool,
    role_pressure_duplicate: bool,
) -> int:
    score = 0
    if len(visible_ids) >= 2:
        score += 18
    if person_like_count >= 2:
        score += 28
    if len(speaker_candidates) > 1:
        score += 18
    if conflicting_target_ids:
        score += 22
    if person_like_count >= 2 and not has_explicit_pronoun_structure:
        score += 12
    if role_pressure_duplicate:
        score += 20
    return min(100, score)


def _person_like(eid: str, id_to_kind: Mapping[str, str]) -> bool:
    """Conservative: unknown kinds count as person-like; only obvious non-person kinds are excluded."""
    k = _as_str(id_to_kind.get(eid, "")).lower()
    non_person = {"object", "prop", "item", "structure", "location", "scenery"}
    return k not in non_person


def _referential_ambiguity_class(
    *,
    visible_ids: Sequence[str],
    person_like_count: int,
    continuity_subject_id: Optional[str],
    conflicting_targets: bool,
) -> str:
    if conflicting_targets:
        return "ambiguous_singular"
    if not visible_ids:
        return "no_anchor"
    if person_like_count == 0:
        return "no_anchor"
    if person_like_count == 1 and continuity_subject_id:
        return "none"
    if person_like_count > 1:
        return "ambiguous_plural"
    if not continuity_subject_id:
        return "ambiguous_singular"
    return "none"


def build_active_entity_order(
    *,
    visible_sorted: Sequence[str],
    primary_speaker: Optional[str],
    active_target: Optional[str],
    anchored_interlocutor: Optional[str],
    active_interlocutor_visibility: Optional[str],
    speaker_candidates: Sequence[str],
) -> List[str]:
    """Stable priority order: speakers/targets of opportunity first, then remaining ids sorted."""
    vis = set(visible_sorted)
    seq: List[str] = []
    seen: set[str] = set()

    def _push(eid: Optional[str]) -> None:
        if not eid or eid in seen:
            return
        if eid not in vis:
            return
        seen.add(eid)
        seq.append(eid)

    for eid in speaker_candidates:
        _push(normalize_entity_id(eid))
    _push(primary_speaker)
    _push(active_target)
    _push(anchored_interlocutor)
    _push(active_interlocutor_visibility)
    for eid in sorted(vis - seen):
        seq.append(eid)
    return seq[:_MAX_ENTITY_LIST]


def _safe_label_map_from_rows(safe_explicit_fallback_labels: Sequence[Mapping[str, Any]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for row in safe_explicit_fallback_labels:
        if not isinstance(row, Mapping):
            continue
        eid = normalize_entity_id(row.get("entity_id"))
        if not eid:
            continue
        lab = _clip(_as_str(row.get("safe_explicit_label")), max_len=_MAX_STR_CLIP)
        if lab:
            out[eid] = lab
    return out


def _union_pronoun_buckets_for_entities(
    entity_ids: Sequence[str],
    buckets_by_entity: Mapping[str, Any],
    *,
    limit: int = _MAX_CLAUSE_LABELS,
) -> List[str]:
    acc: List[str] = []
    seen: set[str] = set()
    for eid in sorted(set(normalize_entity_id(x) for x in entity_ids if _as_str(x))):
        if not eid:
            continue
        raw = buckets_by_entity.get(eid) if isinstance(buckets_by_entity, Mapping) else None
        if not isinstance(raw, (list, tuple)):
            continue
        for b in raw:
            bk = _as_str(b).lower().replace(" ", "_")
            if bk not in _VALID_PRONOUN_BUCKETS or bk in seen:
                continue
            seen.add(bk)
            acc.append(bk)
            if len(acc) >= limit:
                return acc
    return acc


def _allowed_explicit_labels_for_entities(
    entity_ids: Sequence[str],
    authorized_by_id: Mapping[str, str],
    *,
    limit: int = _MAX_CLAUSE_LABELS,
) -> List[str]:
    """Return sorted unique display strings authorized for *entity_ids* only (clipped, capped)."""
    out: List[str] = []
    seen: set[str] = set()
    for eid in sorted(set(normalize_entity_id(x) for x in entity_ids if _as_str(x))):
        if not eid:
            continue
        lab = authorized_by_id.get(eid)
        if not lab:
            continue
        cl = _clip(_as_str(lab), max_len=_MAX_STR_CLIP)
        if not cl or cl in seen:
            continue
        seen.add(cl)
        out.append(cl)
        if len(out) >= limit:
            break
    return out


def _clause_ambiguity_speaker_slot(
    *,
    person_like_count: int,
    speaker_candidates: Sequence[str],
    rac: str,
) -> str:
    if len(speaker_candidates) > 1:
        return "ambiguous_plural"
    if person_like_count >= 2:
        return "ambiguous_plural"
    if person_like_count == 0:
        return "no_anchor"
    if rac in _CLAUSE_AMBIGUITY_CLASSES and rac != "none":
        return rac
    return "none"


def _clause_ambiguity_target_slot(*, conflicting_targets: bool, rac: str) -> str:
    if conflicting_targets:
        return "ambiguous_singular"
    return rac if rac in _CLAUSE_AMBIGUITY_CLASSES else "no_anchor"


def _clause_ambiguity_continuity_object_slot(*, person_like_count: int, rac: str) -> str:
    if person_like_count >= 2:
        return "ambiguous_plural"
    return rac if rac in _CLAUSE_AMBIGUITY_CLASSES else "no_anchor"


def _clause_ambiguity_addressed_slot(*, addressed_visible_n: int, person_like_count: int, rac: str) -> str:
    if addressed_visible_n >= 2:
        return "ambiguous_plural"
    if addressed_visible_n == 1 and person_like_count >= 2:
        return "ambiguous_singular"
    if addressed_visible_n == 0:
        return "no_anchor"
    return rac if rac in _CLAUSE_AMBIGUITY_CLASSES else "none"


def _clause_row_target_switch_sensitive(*, conflicting_targets: bool, drift: bool) -> bool:
    return bool(conflicting_targets or drift)


def build_clause_referent_plan(
    *,
    visible_sorted: Sequence[str],
    active_speaker_candidates: Sequence[str],
    primary_speaker: Optional[str],
    active_interaction_target: Optional[str],
    continuity_object_entity_id: Optional[str],
    ctir_visible_addressed_ids: Sequence[str],
    conflicting_targets: bool,
    target_drift: bool,
    person_like_count: int,
    referential_ambiguity_class: str,
    buckets_by_entity: Mapping[str, Any],
    safe_label_by_entity_id: Mapping[str, str],
) -> List[Dict[str, Any]]:
    """N5: deterministic clause-slot rows from structured inputs only (not prose).

    Empty list → omit ``clause_referent_plan`` on the artifact. Stable row order:
    speaker_subject, interaction_target, continuity_object, addressed_entities.
    """
    vis_set = set(visible_sorted)
    rac = referential_ambiguity_class if referential_ambiguity_class in _CLAUSE_AMBIGUITY_CLASSES else "no_anchor"
    rows: List[Dict[str, Any]] = []

    speaker_cands = _sorted_unique_strs(
        [eid for eid in active_speaker_candidates if eid in vis_set],
        limit=_MAX_CLAUSE_CANDIDATES,
    )
    if not speaker_cands and primary_speaker and primary_speaker in vis_set:
        speaker_cands = [primary_speaker]

    if speaker_cands:
        subj = list(speaker_cands)
        pref_sub = primary_speaker if primary_speaker and primary_speaker in subj else None
        obj_cands: List[str] = []
        pref_obj: Optional[str] = None
        if active_interaction_target and active_interaction_target in vis_set:
            obj_cands = _sorted_unique_strs([active_interaction_target], limit=_MAX_CLAUSE_CANDIDATES)
            pref_obj = active_interaction_target
        slot_entities = subj + obj_cands
        rows.append(
            {
                "clause_id": "n5:speaker_subject:0",
                "clause_kind": "speaker_subject",
                "subject_candidate_ids": subj,
                "object_candidate_ids": obj_cands,
                "preferred_subject_id": pref_sub,
                "preferred_object_id": pref_obj,
                "allowed_explicit_labels": _allowed_explicit_labels_for_entities(
                    slot_entities, safe_label_by_entity_id, limit=_MAX_CLAUSE_LABELS
                ),
                "risky_pronoun_buckets": _union_pronoun_buckets_for_entities(
                    slot_entities, buckets_by_entity, limit=_MAX_CLAUSE_LABELS
                ),
                "target_switch_sensitive": _clause_row_target_switch_sensitive(
                    conflicting_targets=conflicting_targets, drift=target_drift
                ),
                "ambiguity_class": _clause_ambiguity_speaker_slot(
                    person_like_count=person_like_count,
                    speaker_candidates=subj,
                    rac=rac,
                ),
            }
        )

    if active_interaction_target and active_interaction_target in vis_set:
        subj = _sorted_unique_strs(
            [eid for eid in active_speaker_candidates if eid in vis_set],
            limit=_MAX_CLAUSE_CANDIDATES,
        )
        if not subj and primary_speaker and primary_speaker in vis_set:
            subj = [primary_speaker]
        obj_cands = _sorted_unique_strs([active_interaction_target], limit=_MAX_CLAUSE_CANDIDATES)
        slot_entities = subj + obj_cands
        rows.append(
            {
                "clause_id": "n5:interaction_target:0",
                "clause_kind": "interaction_target",
                "subject_candidate_ids": subj,
                "object_candidate_ids": obj_cands,
                "preferred_subject_id": primary_speaker if primary_speaker in subj else (subj[0] if len(subj) == 1 else None),
                "preferred_object_id": active_interaction_target,
                "allowed_explicit_labels": _allowed_explicit_labels_for_entities(
                    slot_entities, safe_label_by_entity_id, limit=_MAX_CLAUSE_LABELS
                ),
                "risky_pronoun_buckets": _union_pronoun_buckets_for_entities(
                    slot_entities, buckets_by_entity, limit=_MAX_CLAUSE_LABELS
                ),
                "target_switch_sensitive": _clause_row_target_switch_sensitive(
                    conflicting_targets=conflicting_targets, drift=target_drift
                ),
                "ambiguity_class": _clause_ambiguity_target_slot(conflicting_targets=conflicting_targets, rac=rac),
            }
        )

    co = normalize_entity_id(continuity_object_entity_id) or None
    if co and co in vis_set:
        subj = _sorted_unique_strs(
            [eid for eid in active_speaker_candidates if eid in vis_set],
            limit=_MAX_CLAUSE_CANDIDATES,
        )
        if not subj and primary_speaker and primary_speaker in vis_set:
            subj = [primary_speaker]
        obj_cands = _sorted_unique_strs([co], limit=_MAX_CLAUSE_CANDIDATES)
        slot_entities = subj + obj_cands
        rows.append(
            {
                "clause_id": "n5:continuity_object:0",
                "clause_kind": "continuity_object",
                "subject_candidate_ids": subj,
                "object_candidate_ids": obj_cands,
                "preferred_subject_id": primary_speaker if primary_speaker in subj else (subj[0] if len(subj) == 1 else None),
                "preferred_object_id": co,
                "allowed_explicit_labels": _allowed_explicit_labels_for_entities(
                    slot_entities, safe_label_by_entity_id, limit=_MAX_CLAUSE_LABELS
                ),
                "risky_pronoun_buckets": _union_pronoun_buckets_for_entities(
                    slot_entities, buckets_by_entity, limit=_MAX_CLAUSE_LABELS
                ),
                "target_switch_sensitive": _clause_row_target_switch_sensitive(
                    conflicting_targets=conflicting_targets, drift=target_drift
                ),
                "ambiguity_class": _clause_ambiguity_continuity_object_slot(person_like_count=person_like_count, rac=rac),
            }
        )

    addr = _sorted_unique_strs([x for x in ctir_visible_addressed_ids if normalize_entity_id(x) in vis_set], limit=_MAX_CLAUSE_CANDIDATES)
    if addr:
        slot_entities = list(addr)
        rows.append(
            {
                "clause_id": "n5:addressed_entities:0",
                "clause_kind": "addressed_entities",
                "subject_candidate_ids": list(addr),
                "object_candidate_ids": [],
                "preferred_subject_id": addr[0] if len(addr) == 1 else None,
                "preferred_object_id": None,
                "allowed_explicit_labels": _allowed_explicit_labels_for_entities(
                    slot_entities, safe_label_by_entity_id, limit=_MAX_CLAUSE_LABELS
                ),
                "risky_pronoun_buckets": _union_pronoun_buckets_for_entities(
                    slot_entities, buckets_by_entity, limit=_MAX_CLAUSE_LABELS
                ),
                "target_switch_sensitive": _clause_row_target_switch_sensitive(
                    conflicting_targets=conflicting_targets, drift=target_drift
                ),
                "ambiguity_class": _clause_ambiguity_addressed_slot(
                    addressed_visible_n=len(addr),
                    person_like_count=person_like_count,
                    rac=rac,
                ),
            }
        )

    return rows[:_MAX_CLAUSE_PLAN_ROWS]


def validate_clause_referent_plan_row(
    row: Any,
    *,
    visible_ids: Set[str],
    authorized_labels: Set[str],
) -> Optional[str]:
    """Strict validation for one ``clause_referent_plan`` row.

    ``visible_ids`` / ``authorized_labels`` must match the parent artifact's
    ``active_entities`` and ``safe_explicit_fallback_labels`` (normalized ids / labels).
    """
    if not isinstance(row, Mapping):
        return "clause_row_not_mapping"
    keys = set(row.keys())
    if keys - _CLAUSE_ROW_KEYS:
        return f"clause_row_unknown_keys:{sorted(keys - _CLAUSE_ROW_KEYS)}"

    cid = _clip(_as_str(row.get("clause_id")), max_len=_MAX_CLAUSE_ID_LEN)
    if not cid:
        return "clause_row_bad_clause_id"
    ck = _as_str(row.get("clause_kind"))
    if ck not in _CLAUSE_KINDS:
        return "clause_row_bad_clause_kind"

    for fld, lim in (
        ("subject_candidate_ids", _MAX_CLAUSE_CANDIDATES),
        ("object_candidate_ids", _MAX_CLAUSE_CANDIDATES),
        ("allowed_explicit_labels", _MAX_CLAUSE_LABELS),
        ("risky_pronoun_buckets", _MAX_CLAUSE_LABELS),
    ):
        raw = row.get(fld)
        if raw is None:
            continue
        if not isinstance(raw, list):
            return f"clause_row_bad_list:{fld}"
        if len(raw) > lim:
            return f"clause_row_list_too_long:{fld}"

    subj_ids: List[str] = []
    if row.get("subject_candidate_ids") is not None:
        for item in row["subject_candidate_ids"]:
            if not isinstance(item, str):
                return "clause_row_bad_subject_id_type"
            eid = normalize_entity_id(item)
            if not eid:
                return "clause_row_bad_subject_id_empty"
            subj_ids.append(eid)

    obj_ids: List[str] = []
    if row.get("object_candidate_ids") is not None:
        for item in row["object_candidate_ids"]:
            if not isinstance(item, str):
                return "clause_row_bad_object_id_type"
            eid = normalize_entity_id(item)
            if not eid:
                return "clause_row_bad_object_id_empty"
            obj_ids.append(eid)

    for eid in subj_ids + obj_ids:
        if eid not in visible_ids:
            return f"clause_row_id_not_visible:{eid}"

    ps = row.get("preferred_subject_id")
    if ps is not None and not isinstance(ps, str):
        return "clause_row_bad_preferred_subject_type"
    pe = normalize_entity_id(ps) if isinstance(ps, str) else ""
    if pe and pe not in subj_ids:
        return "clause_row_preferred_subject_not_in_candidates"
    if not subj_ids and pe:
        return "clause_row_preferred_subject_without_candidates"

    po = row.get("preferred_object_id")
    if po is not None and not isinstance(po, str):
        return "clause_row_bad_preferred_object_type"
    oe = normalize_entity_id(po) if isinstance(po, str) else ""
    if oe and oe not in obj_ids:
        return "clause_row_preferred_object_not_in_candidates"
    if not obj_ids and oe:
        return "clause_row_preferred_object_without_candidates"

    tss = row.get("target_switch_sensitive")
    if tss is not None and not isinstance(tss, bool):
        return "clause_row_bad_target_switch_sensitive"

    amb = row.get("ambiguity_class")
    if amb is not None:
        if _as_str(amb) not in _CLAUSE_AMBIGUITY_CLASSES:
            return "clause_row_bad_ambiguity_class"

    if row.get("allowed_explicit_labels") is not None:
        for lab in row["allowed_explicit_labels"]:
            if not isinstance(lab, str):
                return "clause_row_bad_label_type"
            cl = _clip(_as_str(lab), max_len=_MAX_STR_CLIP)
            if not cl:
                return "clause_row_empty_label"
            if cl not in authorized_labels:
                return "clause_row_label_not_authorized"

    if row.get("risky_pronoun_buckets") is not None:
        for x in row["risky_pronoun_buckets"]:
            if not isinstance(x, str):
                return "clause_row_bad_bucket_type"
        norm_buckets = [_as_str(x).lower().replace(" ", "_") for x in row["risky_pronoun_buckets"]]
        if row["risky_pronoun_buckets"] != norm_buckets:
            return "clause_row_buckets_not_normalized"
        for b in norm_buckets:
            if b not in _VALID_PRONOUN_BUCKETS:
                return "clause_row_bad_bucket"

    return None


def validate_referent_tracking_artifact(artifact: Any, *, strict: bool = True) -> Optional[str]:
    """Return error code string if invalid; else None."""
    if not isinstance(artifact, Mapping):
        return "artifact_not_mapping"
    if artifact.get("version") != REFERENT_TRACKING_ARTIFACT_VERSION:
        return "bad_version"
    allowed_roots = {
        "version",
        "active_entities",
        "active_entity_order",
        "active_interaction_target",
        "active_speaker_candidates",
        "continuity_subject",
        "continuity_object",
        "pronoun_resolution",
        "ambiguity_risk",
        "allowed_named_references",
        "forbidden_or_unresolved_patterns",
        "safe_explicit_fallback_labels",
        "single_unambiguous_entity",
        "referential_ambiguity_class",
        "interaction_target_continuity",
        "debug",
        "clause_referent_plan",
    }
    if strict:
        extra = set(artifact.keys()) - allowed_roots
        if extra:
            return f"unknown_keys:{sorted(extra)}"

    for key in (
        "active_entities",
        "active_entity_order",
        "active_speaker_candidates",
        "allowed_named_references",
        "forbidden_or_unresolved_patterns",
        "safe_explicit_fallback_labels",
    ):
        if not isinstance(artifact.get(key), list):
            return f"bad_list:{key}"

    if not isinstance(artifact.get("pronoun_resolution"), Mapping):
        return "pronoun_resolution_not_mapping"
    pr = artifact["pronoun_resolution"]
    if _as_str(pr.get("strategy")) not in ("neutral_buckets", "explicit_structured", "unresolved"):
        return "bad_pronoun_strategy"
    bbe = pr.get("buckets_by_entity")
    if not isinstance(bbe, Mapping):
        return "buckets_by_entity_not_mapping"

    if not isinstance(artifact.get("debug"), Mapping):
        return "debug_not_mapping"

    for fld in ("continuity_subject", "continuity_object", "single_unambiguous_entity", "interaction_target_continuity"):
        val = artifact.get(fld)
        if val is not None and not isinstance(val, Mapping):
            return f"bad_optional_mapping:{fld}"

    risk = artifact.get("ambiguity_risk")
    if not isinstance(risk, int) or risk < 0 or risk > 100:
        return "bad_ambiguity_risk"

    rac = artifact.get("referential_ambiguity_class")
    if rac not in ("none", "ambiguous_plural", "ambiguous_singular", "no_anchor"):
        return "bad_referential_ambiguity_class"

    crp = artifact.get("clause_referent_plan")
    if crp is not None:
        if not isinstance(crp, list):
            return "bad_clause_referent_plan:not_list"
        if len(crp) > _MAX_CLAUSE_PLAN_ROWS:
            return "bad_clause_referent_plan:too_many_rows"
        visible_entity_ids: Set[str] = set()
        for ae in artifact.get("active_entities") or []:
            if isinstance(ae, Mapping):
                eid = normalize_entity_id(ae.get("entity_id"))
                if eid:
                    visible_entity_ids.add(eid)
        auth_labels: Set[str] = set()
        for sl in artifact.get("safe_explicit_fallback_labels") or []:
            if isinstance(sl, Mapping):
                v = _clip(_as_str(sl.get("safe_explicit_label")), max_len=_MAX_STR_CLIP)
                if v:
                    auth_labels.add(v)
        for i, crow in enumerate(crp):
            cerr = validate_clause_referent_plan_row(
                crow,
                visible_ids=visible_entity_ids,
                authorized_labels=auth_labels,
            )
            if cerr:
                return f"bad_clause_referent_plan_row:{i}:{cerr}"

    try:
        json.dumps(artifact, sort_keys=True)
    except (TypeError, ValueError):
        return "not_json_serializable"

    return None


def build_referent_tracking_artifact(
    *,
    narration_visibility: Mapping[str, Any] | None = None,
    speaker_selection: Mapping[str, Any] | None = None,
    interaction_continuity: Mapping[str, Any] | None = None,
    session_interaction: Mapping[str, Any] | None = None,
    narrative_plan: Mapping[str, Any] | None = None,
    turn_packet: Mapping[str, Any] | None = None,
    ctir_addressed_entity_ids: Sequence[str] | None = None,
    recent_structured_memory_entities: Sequence[Mapping[str, Any]] | None = None,
    prior_active_interaction_target_id: str | None = None,
    explicit_entity_pronoun_buckets: Mapping[str, Sequence[str]] | None = None,
    structured_continuity_object: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Assemble the canonical referent-tracking artifact (deterministic, JSON-safe).

    All parameters are optional bounded slices already produced at authoritative
    seams. This function performs **no** session/world IO and does not parse
    free-form prose beyond reading string ids from structured rows.
    """
    sources_used: List[str] = []
    derivation_codes: List[str] = []

    vis_sorted, id_to_name, id_to_kind, id_to_roles = extract_visible_entity_slice(narration_visibility)
    visible_set = set(vis_sorted)
    if narration_visibility:
        sources_used.append("narration_visibility")
        derivation_codes.append("visibility:slice")

    id_to_name = merge_descriptors_from_narrative_plan(visible_set, narrative_plan, id_to_name)
    if narrative_plan:
        sources_used.append("narrative_plan")
        derivation_codes.append("plan:descriptor_merge")

    signals = extract_interaction_target_signals(
        session_interaction=session_interaction,
        interaction_continuity=interaction_continuity,
        turn_packet=turn_packet,
        narrative_plan=narrative_plan,
    )
    active_target_raw, target_sources, target_ids = choose_active_interaction_target(signals)
    if session_interaction:
        sources_used.append("session_interaction")
    if interaction_continuity:
        sources_used.append("interaction_continuity")
    if turn_packet:
        sources_used.append("turn_packet")
    derivation_codes.append("target:signals_collected")

    conflicting_targets = len(set(target_ids)) > 1
    if conflicting_targets:
        derivation_codes.append("target:signal_conflict")

    active_interaction_target: Optional[str] = None
    target_visible = False
    if active_target_raw:
        if active_target_raw in visible_set:
            active_interaction_target = active_target_raw
            target_visible = True
            derivation_codes.append("target:visible")
        else:
            derivation_codes.append("target:not_visible")

    forbidden: List[Dict[str, Any]] = []
    if active_target_raw and not target_visible:
        forbidden.append(
            {
                "kind": "target_id_not_visible",
                "entity_id": active_target_raw,
                "detail": "active_interaction_target_signal_not_in_visible_slice",
            }
        )

    if speaker_selection:
        sources_used.append("speaker_selection")
        derivation_codes.append("speaker:contract")

    speaker_ids = extract_speaker_candidate_ids(speaker_selection)
    active_speaker_candidates = _sorted_unique_strs(
        [eid for eid in speaker_ids if eid in visible_set],
        limit=_MAX_ENTITY_LIST,
    )

    ic = _mapping(interaction_continuity)
    anchored = normalize_entity_id(ic.get("anchored_interlocutor_id")) or None
    active_interlocutor_vis = None
    if isinstance(narration_visibility, Mapping):
        active_interlocutor_vis = normalize_entity_id(narration_visibility.get("active_interlocutor_id")) or None

    primary_speaker = None
    if isinstance(speaker_selection, Mapping):
        primary_speaker = normalize_entity_id(speaker_selection.get("primary_speaker_id")) or None

    continuity_subject_id: Optional[str] = None
    continuity_subject_source = "none"
    for cand, src in (
        (anchored if anchored in visible_set else None, "interaction_continuity.anchored_interlocutor_id"),
        (
            primary_speaker if primary_speaker in visible_set else None,
            "speaker_selection.primary_speaker_id",
        ),
        (active_interlocutor_vis if active_interlocutor_vis in visible_set else None, "narration_visibility.active_interlocutor_id"),
        (active_interaction_target, "resolved_active_interaction_target"),
    ):
        if cand:
            continuity_subject_id = cand
            continuity_subject_source = src
            break

    continuity_subject: Optional[Dict[str, Any]] = None
    if continuity_subject_id:
        continuity_subject = {
            "entity_id": continuity_subject_id,
            "display_name": id_to_name.get(continuity_subject_id),
            "source": continuity_subject_source,
        }

    continuity_object: Optional[Dict[str, Any]] = None
    if isinstance(structured_continuity_object, Mapping):
        oid = normalize_entity_id(structured_continuity_object.get("entity_id") or structured_continuity_object.get("object_entity_id"))
        if oid:
            continuity_object = {
                "entity_id": oid if oid in visible_set else None,
                "object_kind": _clip(_as_str(structured_continuity_object.get("object_kind")), max_len=64) or None,
                "visible": oid in visible_set,
            }
            sources_used.append("structured_continuity_object")
            if oid not in visible_set:
                forbidden.append(
                    {
                        "kind": "continuity_object_not_visible",
                        "entity_id": oid,
                        "detail": "structured_object_id_not_in_visible_slice",
                    }
                )

    person_like_ids = [eid for eid in vis_sorted if _person_like(eid, id_to_kind)]
    person_like_count = len(person_like_ids)

    role_pressure_duplicate = False
    if len(person_like_ids) >= 2:
        role_entity_counts: Dict[str, int] = {}
        for eid in person_like_ids:
            for r in id_to_roles.get(eid) or []:
                rk = _as_str(r).lower()
                if not rk:
                    continue
                role_entity_counts[rk] = role_entity_counts.get(rk, 0) + 1
        role_pressure_duplicate = any(c >= 2 for c in role_entity_counts.values())

    pronoun_map = build_pronoun_candidate_map(
        vis_sorted,
        explicit_buckets=explicit_entity_pronoun_buckets,
        visibility_extension=narration_visibility if isinstance(narration_visibility, Mapping) else None,
    )
    has_explicit_pronoun = pronoun_map.get("strategy") == "explicit_structured"

    ambiguity = score_ambiguity_risk(
        visible_ids=vis_sorted,
        id_to_kind=id_to_kind,
        id_to_roles=id_to_roles,
        speaker_candidates=active_speaker_candidates,
        conflicting_target_ids=conflicting_targets,
        person_like_count=person_like_count,
        has_explicit_pronoun_structure=has_explicit_pronoun,
        role_pressure_duplicate=role_pressure_duplicate,
    )

    rac = _referential_ambiguity_class(
        visible_ids=vis_sorted,
        person_like_count=person_like_count,
        continuity_subject_id=continuity_subject_id,
        conflicting_targets=conflicting_targets,
    )

    active_entity_order = build_active_entity_order(
        visible_sorted=vis_sorted,
        primary_speaker=primary_speaker,
        active_target=active_interaction_target,
        anchored_interlocutor=anchored if anchored in visible_set else None,
        active_interlocutor_visibility=active_interlocutor_vis if active_interlocutor_vis in visible_set else None,
        speaker_candidates=active_speaker_candidates,
    )

    active_entities: List[Dict[str, Any]] = []
    for eid in sorted(vis_sorted):
        active_entities.append(
            {
                "entity_id": eid,
                "display_name": id_to_name.get(eid),
                "entity_kind": id_to_kind.get(eid) or None,
                "roles": list(id_to_roles.get(eid) or []),
            }
        )

    allowed_named: List[Dict[str, Any]] = []
    for eid in sorted(vis_sorted):
        allowed_named.append({"entity_id": eid, "display_name": id_to_name.get(eid)})

    safe_labels: List[Dict[str, Any]] = []
    for eid in sorted(vis_sorted):
        label = id_to_name.get(eid) or eid
        safe_labels.append({"entity_id": eid, "safe_explicit_label": _clip(label, max_len=_MAX_STR_CLIP)})

    single_unambiguous: Optional[Dict[str, Any]] = None
    locked = bool(_mapping(speaker_selection).get("continuity_locked")) if isinstance(speaker_selection, Mapping) else False
    if len(person_like_ids) == 1:
        only = person_like_ids[0]
        single_unambiguous = {
            "entity_id": only,
            "label": id_to_name.get(only) or only,
            "case": "single_visible_person_like",
        }
    elif locked and len(active_speaker_candidates) == 1:
        only = active_speaker_candidates[0]
        single_unambiguous = {
            "entity_id": only,
            "label": id_to_name.get(only) or only,
            "case": "continuity_locked_single_speaker",
        }

    prior_tgt = normalize_entity_id(prior_active_interaction_target_id) or None
    drift = bool(prior_tgt and active_interaction_target and prior_tgt != active_interaction_target)
    interaction_target_continuity = {
        "prior_target_id": prior_tgt,
        "current_target_id": active_interaction_target,
        "signal_target_id": active_target_raw,
        "target_visible": target_visible,
        "drift_detected": drift,
        "signal_sources": list(target_sources),
    }
    if drift:
        derivation_codes.append("continuity:target_drift")
        forbidden.append(
            {
                "kind": "interaction_target_drift",
                "prior_target_id": prior_tgt,
                "current_target_id": active_interaction_target,
            }
        )

    if person_like_count >= 2 and not has_explicit_pronoun:
        forbidden.append(
            {
                "kind": "gendered_pronoun_uncertainty",
                "detail": "multiple_person_like_visible_without_explicit_pronoun_buckets",
            }
        )

    if rac in ("ambiguous_plural", "ambiguous_singular", "no_anchor") and not has_explicit_pronoun:
        forbidden.append({"kind": "pronoun_anchor_conservative", "referential_ambiguity_class": rac})

    ctir_norm: List[str] = []
    if ctir_addressed_entity_ids is not None:
        sources_used.append("ctir_addressed_entity_ids")
        ctir_norm = [normalize_entity_id(x) for x in ctir_addressed_entity_ids if _as_str(x)][: _MAX_ENTITY_LIST]
        for eid in sorted(set(ctir_norm)):
            if eid and eid not in visible_set:
                forbidden.append(
                    {
                        "kind": "ctir_addressed_not_visible",
                        "entity_id": eid,
                        "detail": "ctir_id_not_in_published_visibility",
                    }
                )

    memory_ids: List[str] = []
    if recent_structured_memory_entities:
        sources_used.append("recent_structured_memory_entities")
        for row in list(recent_structured_memory_entities)[:_MAX_MEMORY_ENTITIES]:
            if not isinstance(row, Mapping):
                continue
            mid = normalize_entity_id(row.get("entity_id") or row.get("id"))
            if mid:
                memory_ids.append(mid)
        memory_ids = _sorted_unique_strs(memory_ids, limit=_MAX_MEMORY_ENTITIES)
        for mid in memory_ids:
            if mid not in visible_set:
                forbidden.append(
                    {
                        "kind": "memory_entity_not_visible",
                        "entity_id": mid,
                        "detail": "structured_memory_id_not_in_visible_slice",
                    }
                )

    pronoun_resolution: Dict[str, Any] = {
        "strategy": pronoun_map["strategy"],
        "buckets_by_entity": dict(pronoun_map["buckets_by_entity"]),
        "explicit_sources": list(pronoun_map.get("explicit_sources") or []),
        "notes": "conservative_default_they_them_without_explicit_engine_buckets",
    }
    if pronoun_map["strategy"] == "neutral_buckets" and person_like_count >= 2:
        pronoun_resolution["strategy"] = "unresolved"
        pronoun_resolution["notes"] = "elevated_to_unresolved_multi_person_like_without_explicit_buckets"

    ctir_visible_for_clause = sorted({eid for eid in ctir_norm if eid and eid in visible_set})[:_MAX_CLAUSE_CANDIDATES]
    co_eid_clause: Optional[str] = None
    if isinstance(continuity_object, Mapping) and bool(continuity_object.get("visible")):
        cx = normalize_entity_id(continuity_object.get("entity_id"))
        if cx and cx in visible_set:
            co_eid_clause = cx

    bbe_final = pronoun_resolution.get("buckets_by_entity")
    if not isinstance(bbe_final, Mapping):
        bbe_final = {}

    safe_label_by_entity_id = _safe_label_map_from_rows(safe_labels)
    clause_plan = build_clause_referent_plan(
        visible_sorted=vis_sorted,
        active_speaker_candidates=active_speaker_candidates,
        primary_speaker=primary_speaker,
        active_interaction_target=active_interaction_target,
        continuity_object_entity_id=co_eid_clause,
        ctir_visible_addressed_ids=ctir_visible_for_clause,
        conflicting_targets=conflicting_targets,
        target_drift=drift,
        person_like_count=person_like_count,
        referential_ambiguity_class=rac,
        buckets_by_entity=bbe_final,
        safe_label_by_entity_id=safe_label_by_entity_id,
    )

    debug = {
        "derivation_codes": _sorted_unique_strs(derivation_codes, limit=_MAX_CODES),
        "sources_used": _sorted_unique_strs(sources_used, limit=_MAX_CODES),
        "target_resolution_trace": json_safe_sanitize(
            [{"source": s, "entity_id": e} for s, e in signals if e],
            max_depth=4,
        ),
        "visible_entity_count": len(vis_sorted),
        "person_like_visible_count": person_like_count,
        "memory_window_entity_ids": memory_ids,
        "conflicting_target_signals": conflicting_targets,
    }

    artifact: Dict[str, Any] = {
        "version": REFERENT_TRACKING_ARTIFACT_VERSION,
        "active_entities": active_entities,
        "active_entity_order": active_entity_order,
        "active_interaction_target": active_interaction_target,
        "active_speaker_candidates": active_speaker_candidates,
        "continuity_subject": continuity_subject,
        "continuity_object": continuity_object,
        "pronoun_resolution": pronoun_resolution,
        "ambiguity_risk": ambiguity,
        "allowed_named_references": allowed_named,
        "forbidden_or_unresolved_patterns": forbidden,
        "safe_explicit_fallback_labels": safe_labels,
        "single_unambiguous_entity": single_unambiguous,
        "referential_ambiguity_class": rac,
        "interaction_target_continuity": interaction_target_continuity,
        "debug": debug,
    }
    if clause_plan:
        artifact["clause_referent_plan"] = clause_plan

    err = validate_referent_tracking_artifact(artifact, strict=True)
    if err:
        raise ValueError(f"internal referent tracking artifact failed validation: {err}")
    return artifact
