"""Deterministic author-time content lint (Objective #10).

Composes strict scene validation, heuristic scene lint, clue/schema checks, and graph
analysis into a single structured report. Not used on the gameplay hot path.

Bundle-level governance (Objective N2) adds a read-only cross-file index and optional
passes after scene-level work. :class:`ContentBundleSnapshot` records **loaded** scene
envelopes, optional ``world`` / ``campaign``, and a **materialized** world↔scene link
registry (``resolved_world_scene_link_registry_ids``) so subset runs stay auditable.
Message families include ``bundle.duplicate_id.*``, ``bundle.reference.*``,
``bundle.contradiction.*``, ``campaign.reference.*``, ``scene.reference.*``,
``clue.reference.*``, ``faction.reference.*``, and ``world_state.reference.*`` (see
:func:`lint_bundle_governance`).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Dict, List, Literal, Mapping, Optional, Sequence, Set, Tuple

from game import scene_graph
from game import scene_lint
from game import validation
from game.schema_contracts import adapt_legacy_clue, normalize_id, validate_clue
from game.utils import slugify

Severity = Literal["error", "warning"]


@dataclass
class ContentLintMessage:
    """One finding from the content lint pipeline (dict-serializable)."""

    severity: Severity
    code: str
    message: str
    scene_id: Optional[str] = None
    path: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None

    def as_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }
        if self.scene_id is not None:
            d["scene_id"] = self.scene_id
        if self.path is not None:
            d["path"] = self.path
        if self.evidence is not None:
            d["evidence"] = self.evidence
        return d


@dataclass
class ContentLintReport:
    ok: bool
    error_count: int
    warning_count: int
    messages: List[ContentLintMessage] = field(default_factory=list)
    scene_ids_checked: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "messages": [m.as_dict() for m in self.messages],
            "scene_ids_checked": list(self.scene_ids_checked),
        }


# ---------------------------------------------------------------------------
# Bundle / cross-system governance (Objective N2) — read-only index + passes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BundleIdOccurrence:
    """One authored id occurrence for duplicate/collision reporting (immutable)."""

    authored_id: str
    compare_key: str
    source_kind: str
    source_detail: str
    scene_id: Optional[str] = None


@dataclass(frozen=True)
class BundleContentIndex:
    """Derived registries from loaded scenes + optional world/campaign (read-only inputs)."""

    scene_envelope_ids: Tuple[str, ...]
    scene_inner_authored_id_by_envelope: Tuple[Tuple[str, str], ...]
    scene_inner_compare_key_by_envelope: Tuple[Tuple[str, str], ...]
    npc_occurrences: Tuple[BundleIdOccurrence, ...]
    faction_occurrences: Tuple[BundleIdOccurrence, ...]
    project_occurrences: Tuple[BundleIdOccurrence, ...]
    world_clue_registry_keys: Tuple[str, ...]
    world_clue_row_authored_id_by_key: Tuple[Tuple[str, str], ...]
    world_state_flag_keys: Tuple[str, ...]
    world_state_counter_keys: Tuple[str, ...]
    world_state_clock_outer_keys: Tuple[str, ...]
    world_state_clock_row_id_by_outer_key: Tuple[Tuple[str, str], ...]
    campaign_top_level_keys: Tuple[str, ...]


@dataclass(frozen=True)
class ContentBundleSnapshot:
    """Intermediate bundle model for cross-file lint (does not copy scene/world bodies).

    **Scope model (Objective N2)** — three layers the engine keeps explicit:

    1. **Loaded bundle scope** — ``scenes`` keys (``loaded_envelope_ids``), plus optional
       ``world`` / ``campaign`` bodies attached to this snapshot.
    2. **Reference registry scope** — scene ids that count as *known targets* for
       world↔scene bundle checks: loaded scene stems + inner ``scene.id`` values, unioned
       with ``world_scene_registry_ids`` when that argument was supplied to
       :func:`build_content_bundle` (full-disk stems in subset CLI runs, or any explicit
       superset from in-process callers). Materialized as the sorted set
       ``resolved_world_scene_link_registry_ids``.
    3. **Validation scope** — strict scene validation / graph use ``reference_known_scene_ids``
       and ``graph_known_scene_ids`` from :func:`lint_all_content`; bundle scene-link rules
       use ``resolved_world_scene_link_registry_ids`` only. There is no silent downgrade:
       unknown targets emit errors iff absent from (2).
    """

    scenes: Mapping[str, Mapping[str, Any]]
    world: Optional[Mapping[str, Any]]
    campaign: Optional[Mapping[str, Any]]
    index: BundleContentIndex
    #: Scene ids supplied as an explicit reference overlay (``None`` omitted at build → empty).
    #: For :func:`lint_all_content`, this is always the same universe as ``reference_known_scene_ids``
    #: (sorted), so bundle checks stay aligned with exit/action strict validation.
    world_scene_registry_ids: Tuple[str, ...] = ()
    #: Sorted envelope stems actually present in ``scenes`` (the loaded bundle).
    loaded_envelope_ids: Tuple[str, ...] = ()
    #: Sorted scene ids in the world↔scene link registry that are **not** derivable from
    #: loaded scene envelopes alone (disk-only stems in subset mode, etc.). Empty when the
    #: registry adds nothing beyond loaded-scene-derived ids.
    reference_registry_extension_ids: Tuple[str, ...] = ()
    #: Sorted union used for ``campaign.*`` / NPC scene-field bundle checks (reproducible).
    resolved_world_scene_link_registry_ids: Tuple[str, ...] = ()


def bundle_compare_id(value: Any) -> str:
    """Stable id key for duplicate detection (normalize_id only; preserves case rules of normalize_id)."""
    return normalize_id(value) or ""


def _read_scene_inner(envelope: Mapping[str, Any]) -> Mapping[str, Any]:
    inner = envelope.get("scene")
    return inner if isinstance(inner, dict) else {}


def build_bundle_content_index(
    scenes: Mapping[str, Mapping[str, Any]],
    *,
    world: Optional[Mapping[str, Any]] = None,
    campaign: Optional[Mapping[str, Any]] = None,
) -> BundleContentIndex:
    """Build derived indexes from *scenes* / *world* / *campaign* without mutating inputs."""
    scene_ids = tuple(sorted(scenes.keys()))
    inner_pairs: List[Tuple[str, str]] = []
    inner_cmp_pairs: List[Tuple[str, str]] = []
    for sid in scene_ids:
        env = scenes.get(sid) or {}
        inner = _read_scene_inner(env) if isinstance(env, dict) else {}
        raw_id = str(inner.get("id") or "").strip() if isinstance(inner, dict) else ""
        inner_pairs.append((sid, raw_id))
        inner_cmp_pairs.append((sid, bundle_compare_id(inner.get("id") if isinstance(inner, dict) else None)))

    npc_occ: List[BundleIdOccurrence] = []
    fac_occ: List[BundleIdOccurrence] = []
    proj_occ: List[BundleIdOccurrence] = []
    clue_keys: List[str] = []
    clue_id_pairs: List[Tuple[str, str]] = []
    flag_keys: List[str] = []
    counter_keys: List[str] = []
    clock_outer: List[str] = []
    clock_row_ids: List[Tuple[str, str]] = []

    if isinstance(world, dict):
        npcs = world.get("npcs") or []
        if isinstance(npcs, list):
            for i, row in enumerate(npcs):
                if not isinstance(row, dict):
                    continue
                aid = str(row.get("id") or "").strip()
                if not aid:
                    continue
                ck = bundle_compare_id(row.get("id"))
                if not ck:
                    continue
                npc_occ.append(
                    BundleIdOccurrence(
                        authored_id=aid,
                        compare_key=ck,
                        source_kind="world.npcs",
                        source_detail=f"[{i}]",
                        scene_id=None,
                    )
                )

        factions = world.get("factions") or []
        if isinstance(factions, list):
            for i, row in enumerate(factions):
                if not isinstance(row, dict):
                    continue
                aid = str(row.get("id") or "").strip() or str(row.get("name") or "").strip()
                if not aid:
                    continue
                ck = bundle_compare_id(row.get("id")) or bundle_compare_id(row.get("name"))
                if not ck:
                    continue
                fac_occ.append(
                    BundleIdOccurrence(
                        authored_id=aid,
                        compare_key=ck,
                        source_kind="world.factions",
                        source_detail=f"[{i}]",
                        scene_id=None,
                    )
                )

        projects = world.get("projects") or []
        if isinstance(projects, list):
            for i, row in enumerate(projects):
                if not isinstance(row, dict):
                    continue
                aid = str(row.get("id") or "").strip()
                if not aid:
                    continue
                ck = bundle_compare_id(row.get("id"))
                if not ck:
                    continue
                proj_occ.append(
                    BundleIdOccurrence(
                        authored_id=aid,
                        compare_key=ck,
                        source_kind="world.projects",
                        source_detail=f"[{i}]",
                        scene_id=None,
                    )
                )

        clues = world.get("clues")
        if isinstance(clues, dict):
            for k in sorted(clues.keys()):
                if not isinstance(k, str) or not k.strip():
                    continue
                ks = k.strip()
                clue_keys.append(ks)
                row = clues.get(k)
                row_id = ""
                if isinstance(row, dict):
                    row_id = str(row.get("id") or "").strip()
                clue_id_pairs.append((ks, row_id))

        ws = world.get("world_state")
        if isinstance(ws, dict):
            flags = ws.get("flags")
            if isinstance(flags, dict):
                flag_keys = sorted(str(x).strip() for x in flags.keys() if isinstance(x, str) and str(x).strip())
            counters = ws.get("counters")
            if isinstance(counters, dict):
                counter_keys = sorted(str(x).strip() for x in counters.keys() if isinstance(x, str) and str(x).strip())
            clocks = ws.get("clocks")
            if isinstance(clocks, dict):
                for name in sorted(clocks.keys()):
                    if not isinstance(name, str) or not name.strip():
                        continue
                    nm = name.strip()
                    clock_outer.append(nm)
                    entry = clocks.get(name)
                    rid = ""
                    if isinstance(entry, dict):
                        rid = str(entry.get("id") or "").strip()
                    clock_row_ids.append((nm, rid))

    camp_keys: Tuple[str, ...] = ()
    if isinstance(campaign, dict):
        camp_keys = tuple(sorted(k for k in campaign.keys() if isinstance(k, str)))

    return BundleContentIndex(
        scene_envelope_ids=scene_ids,
        scene_inner_authored_id_by_envelope=tuple(inner_pairs),
        scene_inner_compare_key_by_envelope=tuple(inner_cmp_pairs),
        npc_occurrences=tuple(sorted(npc_occ, key=lambda o: (o.compare_key, o.source_detail, o.authored_id))),
        faction_occurrences=tuple(sorted(fac_occ, key=lambda o: (o.compare_key, o.source_detail, o.authored_id))),
        project_occurrences=tuple(sorted(proj_occ, key=lambda o: (o.compare_key, o.source_detail, o.authored_id))),
        world_clue_registry_keys=tuple(clue_keys),
        world_clue_row_authored_id_by_key=tuple(clue_id_pairs),
        world_state_flag_keys=tuple(flag_keys),
        world_state_counter_keys=tuple(counter_keys),
        world_state_clock_outer_keys=tuple(clock_outer),
        world_state_clock_row_id_by_outer_key=tuple(clock_row_ids),
        campaign_top_level_keys=camp_keys,
    )


def build_content_bundle(
    scenes: Mapping[str, Mapping[str, Any]],
    *,
    world: Optional[Mapping[str, Any]] = None,
    campaign: Optional[Mapping[str, Any]] = None,
    world_scene_registry_ids: Optional[Sequence[str]] = None,
) -> ContentBundleSnapshot:
    """Assemble bundle snapshot + index (holds references to *scenes* / *world*; do not mutate during lint).

    Populates ``loaded_envelope_ids``, ``reference_registry_extension_ids``, and
    ``resolved_world_scene_link_registry_ids`` so subset vs full runs are reproducible from
    ``evidence`` alone. When ``world_scene_registry_ids`` is ``None``, the overlay is empty
    (loaded-scenes-only link registry).
    """
    idx = build_bundle_content_index(scenes, world=world, campaign=campaign)
    extra: Tuple[str, ...] = ()
    if world_scene_registry_ids is not None:
        extra = tuple(sorted({str(x).strip() for x in world_scene_registry_ids if str(x).strip()}))
    loaded = tuple(sorted(scenes.keys()))
    base = ContentBundleSnapshot(
        scenes=scenes,
        world=world,
        campaign=campaign,
        index=idx,
        world_scene_registry_ids=extra,
        loaded_envelope_ids=loaded,
        reference_registry_extension_ids=(),
        resolved_world_scene_link_registry_ids=(),
    )
    loaded_only = _bundle_scene_id_registry(base)
    resolved: Set[str] = set(loaded_only)
    resolved |= {str(x).strip() for x in base.world_scene_registry_ids if str(x).strip()}
    ext_ids = tuple(sorted(x for x in resolved if x not in loaded_only))
    return replace(
        base,
        reference_registry_extension_ids=ext_ids,
        resolved_world_scene_link_registry_ids=tuple(sorted(resolved)),
    )


def bundle_index_fingerprint(index: BundleContentIndex) -> Tuple[Any, ...]:
    """Deterministic tuple fingerprint for tests (stable ordering)."""
    return (
        index.scene_envelope_ids,
        index.scene_inner_authored_id_by_envelope,
        index.scene_inner_compare_key_by_envelope,
        tuple((o.authored_id, o.compare_key, o.source_kind, o.source_detail) for o in index.npc_occurrences),
        tuple((o.authored_id, o.compare_key, o.source_kind, o.source_detail) for o in index.faction_occurrences),
        tuple((o.authored_id, o.compare_key, o.source_kind, o.source_detail) for o in index.project_occurrences),
        index.world_clue_registry_keys,
        index.world_clue_row_authored_id_by_key,
        index.world_state_flag_keys,
        index.world_state_counter_keys,
        index.world_state_clock_outer_keys,
        index.world_state_clock_row_id_by_outer_key,
        index.campaign_top_level_keys,
    )


def _group_occurrences_by_compare_key(
    occ: Sequence[BundleIdOccurrence],
) -> Dict[str, List[BundleIdOccurrence]]:
    buckets: Dict[str, List[BundleIdOccurrence]] = {}
    for o in occ:
        if not o.compare_key:
            continue
        buckets.setdefault(o.compare_key, []).append(o)
    for k in buckets:
        buckets[k].sort(key=lambda x: (x.source_kind, x.source_detail, x.authored_id))
    return buckets


def lint_bundle_duplicate_ids(bundle: ContentBundleSnapshot) -> List[ContentLintMessage]:
    """Emit ``bundle.duplicate_id.*`` for duplicate ids within world lists (compare_key collision)."""
    out: List[ContentLintMessage] = []
    world = bundle.world

    def _emit(kind_code: str, label: str, bucket: List[BundleIdOccurrence]) -> None:
        if len(bucket) < 2:
            return
        evidence = {
            "compare_key": bucket[0].compare_key,
            "scope": f"bundle.world.{kind_code}",
            "occurrences": [
                {"authored_id": o.authored_id, "source": f"{o.source_kind}{o.source_detail}"} for o in bucket
            ],
        }
        out.append(
            ContentLintMessage(
                severity="error",
                code=f"bundle.duplicate_id.{kind_code}",
                message=f"Duplicate {label} id '{bucket[0].compare_key}' appears {len(bucket)} times in world bundle",
                scene_id=None,
                path=f"world.{kind_code}",
                evidence=evidence,
            )
        )

    if isinstance(world, dict):
        npc_b = _group_occurrences_by_compare_key(bundle.index.npc_occurrences)
        for _ck, rows in sorted(npc_b.items()):
            _emit("npc", "NPC", rows)

        fac_b = _group_occurrences_by_compare_key(bundle.index.faction_occurrences)
        for _ck, rows in sorted(fac_b.items()):
            _emit("faction", "faction", rows)

        proj_b = _group_occurrences_by_compare_key(bundle.index.project_occurrences)
        for _ck, rows in sorted(proj_b.items()):
            _emit("project", "project", rows)

    # Duplicate inner scene.id compare keys across different envelope stems (cross-file governance).
    inner_by_key: Dict[str, List[str]] = {}
    for env_id, cmp_id in bundle.index.scene_inner_compare_key_by_envelope:
        if not cmp_id:
            continue
        inner_by_key.setdefault(cmp_id, []).append(env_id)
    for ck in sorted(inner_by_key.keys()):
        stems = sorted(set(inner_by_key[ck]))
        if len(stems) < 2:
            continue
        authored = []
        for eid, raw in bundle.index.scene_inner_authored_id_by_envelope:
            if eid in stems and raw:
                authored.append(raw)
        out.append(
            ContentLintMessage(
                severity="warning",
                code="bundle.duplicate_id.scene",
                message=(
                    f"Multiple scene envelopes share inner scene.id compare key '{ck}': "
                    f"{', '.join(stems)}"
                ),
                scene_id=None,
                path="bundle.scenes",
                evidence={
                    "compare_key": ck,
                    "scope": "bundle.scenes.inner_id_collision",
                    "envelope_ids": stems,
                    "authored_inner_scene_ids": sorted(set(authored)) or stems,
                },
            )
        )

    return out


def lint_clue_world_registry_references(bundle: ContentBundleSnapshot) -> List[ContentLintMessage]:
    """``clue.reference.*`` — world.clues dict key vs row id consistency (read-only)."""
    out: List[ContentLintMessage] = []
    world = bundle.world
    if not isinstance(world, dict):
        return out
    clues = world.get("clues")
    if not isinstance(clues, dict):
        return out
    for reg_key, row_id in bundle.index.world_clue_row_authored_id_by_key:
        if not row_id:
            continue
        if row_id == reg_key:
            continue
        out.append(
            ContentLintMessage(
                severity="error",
                code="clue.reference.world_registry_key_mismatch",
                message=(
                    f"world.clues registry key '{reg_key}' does not match row id '{row_id}' "
                    "(ambiguous canonical clue id)"
                ),
                scene_id=None,
                path=f"world.clues[{reg_key}].id",
                evidence={"registry_key": reg_key, "row_id": row_id, "scope": "bundle.world.clues"},
            )
        )
    return out


def lint_faction_progression_uid_collisions(bundle: ContentBundleSnapshot) -> List[ContentLintMessage]:
    """``faction.reference.*`` — same progression compare key as runtime faction backbone (read-only heuristic)."""
    out: List[ContentLintMessage] = []
    buckets = _group_occurrences_by_compare_key(bundle.index.faction_occurrences)
    for ck, rows in sorted(buckets.items()):
        if len(rows) < 2:
            continue
        if len({r.authored_id for r in rows}) <= 1:
            # Identical authored ids: already ``bundle.duplicate_id.faction``.
            continue
        out.append(
            ContentLintMessage(
                severity="error",
                code="faction.reference.progression_uid_collision",
                message=(
                    f"Multiple faction rows resolve to the same bundle compare key '{ck}' "
                    f"({len(rows)} rows); runtime progression disambiguation may apply"
                ),
                scene_id=None,
                path="world.factions",
                evidence={
                    "compare_key": ck,
                    "scope": "bundle.world.factions",
                    "rows": [{"authored_id": r.authored_id, "source": f"{r.source_kind}{r.source_detail}"} for r in rows],
                },
            )
        )
    return out


def lint_world_state_registry_consistency(bundle: ContentBundleSnapshot) -> List[ContentLintMessage]:
    """``world_state.reference.*`` — clock outer key vs row ``id`` when both are present."""
    out: List[ContentLintMessage] = []
    for outer_key, row_id in bundle.index.world_state_clock_row_id_by_outer_key:
        if not row_id:
            continue
        if row_id == outer_key:
            continue
        out.append(
            ContentLintMessage(
                severity="error",
                code="world_state.reference.clock_key_row_id_mismatch",
                message=(
                    f"world_state.clocks['{outer_key}'].id is '{row_id}' "
                    f"(differs from outer key; ensure tooling agrees on canonical clock id)"
                ),
                scene_id=None,
                path=f"world.world_state.clocks[{outer_key}].id",
                evidence={"outer_key": outer_key, "row_id": row_id, "scope": "bundle.world.world_state.clocks"},
            )
        )
    return out


def _bundle_scene_id_registry(bundle: ContentBundleSnapshot) -> Set[str]:
    """Scene ids usable for world↔scene bundle checks: envelope stems + non-empty inner ``scene.id`` values."""
    reg: Set[str] = set()
    for stem in bundle.index.scene_envelope_ids:
        reg.add(str(stem).strip())
    for _env_id, inner_raw in bundle.index.scene_inner_authored_id_by_envelope:
        s = str(inner_raw or "").strip()
        if s:
            reg.add(s)
    return reg


def _world_link_scene_registry(bundle: ContentBundleSnapshot) -> Set[str]:
    """Union of loaded-scene ids and explicit ``world_scene_registry_ids`` (materialized on the snapshot)."""
    if bundle.resolved_world_scene_link_registry_ids:
        return set(bundle.resolved_world_scene_link_registry_ids)
    reg = _bundle_scene_id_registry(bundle)
    reg |= {str(x).strip() for x in bundle.world_scene_registry_ids if str(x).strip()}
    return reg


def _scene_link_bundle_scope_evidence(bundle: ContentBundleSnapshot) -> Dict[str, Any]:
    """Reproducible scope payload for world↔scene bundle checks (subset vs full)."""
    known = sorted(_world_link_scene_registry(bundle))
    return {
        "loaded_envelope_ids": list(bundle.loaded_envelope_ids),
        "reference_registry_extension_ids": list(bundle.reference_registry_extension_ids),
        "resolved_world_scene_link_registry_ids": known,
        "known_scene_ids": known,
        "validation_scope": "world_scene_link_registry",
    }


def _world_settlement_ids(world: Mapping[str, Any]) -> Set[str]:
    out: Set[str] = set()
    rows = world.get("settlements") or []
    if not isinstance(rows, list):
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        sid = str(row.get("id") or "").strip()
        if sid:
            out.add(sid)
    return out


def _world_faction_compare_keys(bundle: ContentBundleSnapshot) -> Set[str]:
    return {o.compare_key for o in bundle.index.faction_occurrences if o.compare_key}


def lint_campaign_scene_references(bundle: ContentBundleSnapshot) -> List[ContentLintMessage]:
    """``campaign.reference.*`` — ``starting_scene_id`` must appear in :func:`_world_link_scene_registry`."""
    out: List[ContentLintMessage] = []
    campaign = bundle.campaign
    if not isinstance(campaign, dict):
        return out
    raw = campaign.get("starting_scene_id")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return out
    sid = str(raw).strip()
    known = _world_link_scene_registry(bundle)
    if sid in known:
        return out
    ev = _scene_link_bundle_scope_evidence(bundle)
    ev["starting_scene_id"] = sid
    ev["scope"] = "bundle.campaign<->scenes"
    out.append(
        ContentLintMessage(
            severity="error",
            code="campaign.reference.starting_scene_unknown",
            message=(
                f"campaign.starting_scene_id '{sid}' is absent from the resolved world<->scene "
                f"link registry for this lint run (loaded scenes plus explicit reference ids)"
            ),
            scene_id=None,
            path="campaign.starting_scene_id",
            evidence=ev,
        )
    )
    return out


def lint_scene_world_npc_scene_links(bundle: ContentBundleSnapshot) -> List[ContentLintMessage]:
    """``scene.reference.*`` — NPC scene fields vs :func:`_world_link_scene_registry` (subset-safe when extended)."""
    out: List[ContentLintMessage] = []
    world = bundle.world
    if not isinstance(world, dict):
        return out
    reg = _world_link_scene_registry(bundle)
    npcs = world.get("npcs") or []
    if not isinstance(npcs, list):
        return out
    fields = ("location", "origin_scene_id", "scene_id")
    for i, row in enumerate(npcs):
        if not isinstance(row, dict):
            continue
        npc_id = str(row.get("id") or "").strip() or f"npcs[{i}]"
        for fld in fields:
            raw = row.get(fld)
            if raw is None or (isinstance(raw, str) and not raw.strip()):
                continue
            val = str(raw).strip()
            if val in reg:
                continue
            ev = _scene_link_bundle_scope_evidence(bundle)
            ev.update(
                {
                    "npc_id": npc_id,
                    "field": fld,
                    "value": val,
                    "scope": "bundle.world.npcs<->scenes",
                }
            )
            out.append(
                ContentLintMessage(
                    severity="error",
                    code="scene.reference.npc_scene_link_unknown",
                    message=(
                        f"world.npcs[{i}] ({npc_id!r}) field '{fld}' is '{val}', "
                        f"which is absent from the resolved world<->scene link registry for this lint run"
                    ),
                    scene_id=None,
                    path=f"world.npcs[{i}].{fld}",
                    evidence=ev,
                )
            )
    return out


def lint_scene_world_npc_affiliations(bundle: ContentBundleSnapshot) -> List[ContentLintMessage]:
    """``scene.reference.*`` — NPC ``affiliation`` must match a settlement id or faction compare id when non-empty."""
    out: List[ContentLintMessage] = []
    world = bundle.world
    if not isinstance(world, dict):
        return out
    settlements = _world_settlement_ids(world)
    fac_keys = _world_faction_compare_keys(bundle)
    allow = settlements | fac_keys
    npcs = world.get("npcs") or []
    if not isinstance(npcs, list):
        return out
    for i, row in enumerate(npcs):
        if not isinstance(row, dict):
            continue
        aff = row.get("affiliation")
        if aff is None or (isinstance(aff, str) and not aff.strip()):
            continue
        val = str(aff).strip()
        ck = bundle_compare_id(val)
        if val in allow or (ck and ck in fac_keys):
            continue
        npc_id = str(row.get("id") or "").strip() or f"npcs[{i}]"
        out.append(
            ContentLintMessage(
                severity="error",
                code="scene.reference.npc_affiliation_unknown",
                message=(
                    f"world.npcs[{i}] ({npc_id!r}) affiliation '{val}' does not match any "
                    f"world.settlements[].id or world.factions id/name key in this bundle"
                ),
                scene_id=None,
                path=f"world.npcs[{i}].affiliation",
                evidence={
                    "npc_id": npc_id,
                    "affiliation": val,
                    "scope": "bundle.world.npcs↔settlements|factions",
                    "settlement_ids": sorted(settlements),
                    "faction_compare_keys_sample": sorted(fac_keys)[:32],
                },
            )
        )
    return out


def lint_bundle_event_log_faction_sources(bundle: ContentBundleSnapshot) -> List[ContentLintMessage]:
    """``bundle.reference.*`` — ``world.event_log`` entries with ``faction_`` type must cite a known faction id."""
    out: List[ContentLintMessage] = []
    world = bundle.world
    if not isinstance(world, dict):
        return out
    log = world.get("event_log")
    if not isinstance(log, list):
        return out
    fac_ids: Set[str] = set()
    for o in bundle.index.faction_occurrences:
        if o.authored_id:
            fac_ids.add(str(o.authored_id).strip())
    for i, entry in enumerate(log):
        if not isinstance(entry, dict):
            continue
        et = str(entry.get("type") or "").strip().lower()
        if not et.startswith("faction_"):
            continue
        src = entry.get("source")
        if src is None or (isinstance(src, str) and not src.strip()):
            continue
        src_s = str(src).strip()
        if src_s in fac_ids:
            continue
        out.append(
            ContentLintMessage(
                severity="error",
                code="bundle.reference.event_log_source_unknown_faction",
                message=(
                    f"world.event_log[{i}] type '{et}' source '{src_s}' does not match any world.factions row id"
                ),
                scene_id=None,
                path=f"world.event_log[{i}].source",
                evidence={
                    "index": i,
                    "event_type": et,
                    "source": src_s,
                    "scope": "bundle.world.event_log↔factions",
                    "known_faction_authored_ids": sorted(fac_ids),
                },
            )
        )
    return out


def _stable_json_blob(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def lint_bundle_clue_registry_row_conflicts(bundle: ContentBundleSnapshot) -> List[ContentLintMessage]:
    """``bundle.contradiction.*`` — multiple ``world.clues`` keys share the same canonical row id with differing rows."""
    out: List[ContentLintMessage] = []
    world = bundle.world
    if not isinstance(world, dict):
        return out
    clues = world.get("clues")
    if not isinstance(clues, dict):
        return out
    by_compare_key: Dict[str, List[Tuple[str, str, Any]]] = {}
    for k in sorted(clues.keys()):
        if not isinstance(k, str) or not k.strip():
            continue
        row = clues.get(k)
        if not isinstance(row, dict):
            continue
        rid = str(row.get("id") or "").strip()
        if not rid:
            continue
        ck = bundle_compare_id(rid)
        if not ck:
            continue
        by_compare_key.setdefault(ck, []).append((k.strip(), rid, row))
    for ck in sorted(by_compare_key.keys()):
        triples = by_compare_key[ck]
        if len(triples) < 2:
            continue
        blobs = {_stable_json_blob(t[2]) for t in triples}
        if len(blobs) <= 1:
            continue
        keys = sorted(t[0] for t in triples)
        authored_ids = sorted({t[1] for t in triples})
        out.append(
            ContentLintMessage(
                severity="error",
                code="bundle.contradiction.clue_registry_row_conflict",
                message=(
                    f"world.clues defines incompatible rows for the same canonical clue id '{ck}' "
                    f"(registry keys {keys})"
                ),
                scene_id=None,
                path="world.clues",
                evidence={
                    "compare_key": ck,
                    "authored_row_ids": authored_ids,
                    "registry_keys": keys,
                    "scope": "bundle.world.clues",
                },
            )
        )
    return out


def lint_bundle_clue_scene_vs_world_definitions(bundle: ContentBundleSnapshot) -> List[ContentLintMessage]:
    """``bundle.contradiction.*`` — scene ``discoverable_clues`` id matches ``world.clues`` but ``text`` differs.

    Conflicting *world-only* definitions for the same canonical clue id across multiple registry
    keys are reported separately by :func:`lint_bundle_clue_registry_row_conflicts` to avoid
    duplicate messages for the same structural issue.
    """
    out: List[ContentLintMessage] = []
    world = bundle.world
    if not isinstance(world, dict):
        return out
    clues = world.get("clues")
    if not isinstance(clues, dict) or not clues:
        return out
    texts_by_ck: Dict[str, Set[str]] = {}
    for k in sorted(clues.keys()):
        if not isinstance(k, str) or not k.strip():
            continue
        row = clues.get(k)
        if not isinstance(row, dict):
            continue
        row_id = str(row.get("id") or "").strip() or k.strip()
        ck = bundle_compare_id(row_id)
        if not ck:
            continue
        txt = str(row.get("text") or "").strip()
        if not txt:
            continue
        texts_by_ck.setdefault(ck, set()).add(txt)

    world_text_by_ck: Dict[str, str] = {}
    for ck, texts in texts_by_ck.items():
        if len(texts) == 1:
            world_text_by_ck[ck] = next(iter(texts))

    for _env_id in sorted(bundle.scenes):
        env = bundle.scenes[_env_id]
        inner = _scene_inner(env if isinstance(env, dict) else {})
        if not inner:
            continue
        disc = inner.get("discoverable_clues") or []
        if not isinstance(disc, list):
            continue
        for idx, raw in enumerate(disc):
            if not isinstance(raw, dict):
                continue
            cid = str(raw.get("id") or "").strip()
            if not cid:
                continue
            ck = bundle_compare_id(cid)
            wtxt = world_text_by_ck.get(ck)
            if wtxt is None:
                continue
            stxt = str(raw.get("text") or "").strip()
            if not stxt or stxt == wtxt:
                continue
            inner_sid = str(inner.get("id") or _env_id).strip()
            out.append(
                ContentLintMessage(
                    severity="error",
                    code="bundle.contradiction.clue_scene_vs_world_definition",
                    message=(
                        f"Scene '{inner_sid}' discoverable_clues[{idx}] id '{cid}' matches a world.clues entry "
                        f"but clue text differs from the world row"
                    ),
                    scene_id=inner_sid,
                    path=f"scene.discoverable_clues[{idx}]",
                    evidence={
                        "clue_compare_key": ck,
                        "scene_text_excerpt": stxt[:200],
                        "world_text_excerpt": wtxt[:200],
                        "scope": "bundle.scene.discoverable_clues↔world.clues",
                    },
                )
            )
    return out


def lint_bundle_governance(bundle: ContentBundleSnapshot) -> List[ContentLintMessage]:
    """Run bundle-level passes after scene passes; merge is caller's responsibility."""
    parts: List[List[ContentLintMessage]] = [
        lint_bundle_duplicate_ids(bundle),
        lint_clue_world_registry_references(bundle),
        lint_faction_progression_uid_collisions(bundle),
        lint_world_state_registry_consistency(bundle),
        lint_campaign_scene_references(bundle),
        lint_scene_world_npc_scene_links(bundle),
        lint_scene_world_npc_affiliations(bundle),
        lint_bundle_event_log_faction_sources(bundle),
        lint_bundle_clue_registry_row_conflicts(bundle),
        lint_bundle_clue_scene_vs_world_definitions(bundle),
    ]
    return _merge_messages(parts)


def _norm(s: str) -> str:
    return " ".join(str(s or "").lower().split())


def _scene_inner(envelope: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(envelope, dict):
        return {}
    inner = envelope.get("scene")
    return inner if isinstance(inner, dict) else {}


def _valid_clue_refs_extended(
    scene: Dict[str, Any],
    world: Optional[Dict[str, Any]],
) -> Set[str]:
    """Clue refs accepted for interactable ``reveals_clue`` (discoverable_clues + optional world.clues)."""
    refs: Set[str] = set()
    clues = scene.get("discoverable_clues") or []
    for c in clues:
        if isinstance(c, dict):
            cid = str(c.get("id") or "").strip()
            text = str(c.get("text") or "").strip()
            if cid:
                refs.add(cid)
                refs.add(slugify(cid) or "")
            if text:
                refs.add(text)
                refs.add(slugify(text) or "")
        elif isinstance(c, str) and c.strip():
            refs.add(c.strip())
            refs.add(slugify(c) or "")
    if world and isinstance(world.get("clues"), dict):
        for k in world["clues"]:
            if isinstance(k, str) and k.strip():
                ks = k.strip()
                refs.add(ks)
                refs.add(slugify(ks) or "")
    return refs


def _validation_issue_to_message(err: validation.SceneValidationError) -> ContentLintMessage:
    """Map strict validation issues to stable codes (mirrors :mod:`game.validation` rules)."""
    scene_id = str(err.scene_id or "")
    fld = str(err.field or "")
    msg = str(err)
    msg_l = msg.lower()

    if fld == "scene":
        code = "scene.missing_root"
    elif fld == "scene.id":
        if "missing" in msg_l or "empty" in msg_l:
            code = "scene.id.missing"
        else:
            code = "scene.id.mismatch"
    elif fld == "scene.location":
        code = "scene.missing_required_field"
    elif fld == "scene.summary":
        code = "scene.missing_required_field"
    elif "duplicate affordance action id" in msg_l:
        code = "action.duplicate_id"
    elif "exits" in fld and "target_scene_id" in fld:
        code = "exit.unknown_target"
    elif "actions" in fld and ("targetsceneid" in msg_l or "target_scene_id" in msg_l):
        code = "action.unknown_target_scene"
    elif "interactables" in fld and "not a dict" in msg_l:
        code = "interactable.invalid_shape"
    elif "interactables" in fld and "missing required field 'id'" in msg:
        code = "interactable.missing_id"
    elif "duplicate interactable" in msg_l:
        code = "interactable.duplicate_id"
    elif "references unknown clue" in msg_l:
        code = "interactable.unknown_clue_ref"
    else:
        code = "scene.validation"

    evidence: Dict[str, Any] = {"validation_field": fld}
    if code == "scene.missing_required_field":
        evidence["field"] = "location" if "location" in msg_l else "summary"

    return ContentLintMessage(
        severity="error",
        code=code,
        message=msg,
        scene_id=scene_id or None,
        path=fld or None,
        evidence=evidence,
    )


def lint_scene_structure(
    scene_envelope: Dict[str, Any],
    scene_id: str,
    known_scene_ids: Set[str],
) -> List[ContentLintMessage]:
    """Envelope + id + required fields (strict rules from :mod:`game.validation`)."""
    issues = validation.collect_scene_validation_issues(scene_envelope, scene_id, known_scene_ids)
    out: List[ContentLintMessage] = []
    for err in issues:
        m = _validation_issue_to_message(err)
        if m.code in (
            "scene.missing_root",
            "scene.id.missing",
            "scene.id.mismatch",
            "scene.missing_required_field",
        ):
            out.append(m)
    return out


def lint_scene_exits(
    scene_envelope: Dict[str, Any],
    scene_id: str,
    known_scene_ids: Set[str],
) -> List[ContentLintMessage]:
    """Exit targets, affordance transition targets, and duplicate affordance ids (strict)."""
    issues = validation.collect_scene_validation_issues(scene_envelope, scene_id, known_scene_ids)
    codes = ("exit.unknown_target", "action.unknown_target_scene", "action.duplicate_id")
    return [m for err in issues if (m := _validation_issue_to_message(err)).code in codes]


def lint_scene_interactables(
    scene_envelope: Dict[str, Any],
    scene_id: str,
    known_scene_ids: Set[str],
) -> List[ContentLintMessage]:
    """Interactable shape, ids, duplicates, runtime-strict clue refs on investigate."""
    issues = validation.collect_scene_validation_issues(scene_envelope, scene_id, known_scene_ids)
    codes = {
        "interactable.invalid_shape",
        "interactable.missing_id",
        "interactable.duplicate_id",
        "interactable.unknown_clue_ref",
    }
    return [m for err in issues if (m := _validation_issue_to_message(err)).code in codes]


def lint_scene_clue_integrity(
    scene_envelope: Dict[str, Any],
    scene_id: str,
    *,
    world: Optional[Dict[str, Any]] = None,
) -> List[ContentLintMessage]:
    """Structured clue ids, schema, overlap with hidden facts; author-only clue ref warnings."""
    out: List[ContentLintMessage] = []
    inner = _scene_inner(scene_envelope)
    if not inner:
        return out

    discoverable = inner.get("discoverable_clues") or []
    hidden = [str(v) for v in (inner.get("hidden_facts") or [])]
    norm_hidden = [_norm(v) for v in hidden]

    # Duplicate structured clue ids within the scene
    seen_clue_ids: Set[str] = set()
    for idx, raw in enumerate(discoverable):
        if not isinstance(raw, dict):
            continue
        cid = str(raw.get("id") or "").strip()
        if not cid:
            continue
        if cid in seen_clue_ids:
            out.append(
                ContentLintMessage(
                    severity="error",
                    code="clue.duplicate_id",
                    message=f"Duplicate discoverable_clues id '{cid}' in scene '{scene_id}'",
                    scene_id=scene_id,
                    path=f"scene.discoverable_clues[{idx}].id",
                    evidence={"clue_id": cid},
                )
            )
            continue
        seen_clue_ids.add(cid)

        adapted = adapt_legacy_clue(raw)
        ok, reasons = validate_clue(adapted)
        if not ok:
            out.append(
                ContentLintMessage(
                    severity="error",
                    code="clue.schema_invalid",
                    message=f"Invalid structured clue at index {idx} in scene '{scene_id}'",
                    scene_id=scene_id,
                    path=f"scene.discoverable_clues[{idx}]",
                    evidence={"reasons": list(reasons)},
                )
            )

    # Discoverable text contains hidden fact substring (deterministic; aligns with scene_lint heuristic)
    disc_texts: List[tuple[int, str, str]] = []
    for idx, raw in enumerate(discoverable):
        if isinstance(raw, str) and raw.strip():
            t = raw.strip()
            disc_texts.append((idx, t, _norm(t)))
        elif isinstance(raw, dict):
            t = raw.get("text")
            if isinstance(t, str) and t.strip():
                ts = t.strip()
                disc_texts.append((idx, ts, _norm(ts)))

    for idx, d_txt, d_norm in disc_texts:
        for h_norm in norm_hidden:
            if h_norm and h_norm in d_norm:
                out.append(
                    ContentLintMessage(
                        severity="warning",
                        code="clue.overlaps_hidden_fact",
                        message=f"Discoverable clue may directly mirror a hidden fact in scene '{scene_id}'",
                        scene_id=scene_id,
                        path=f"scene.discoverable_clues[{idx}]",
                        evidence={"discoverable": d_txt, "hidden_norm": h_norm},
                    )
                )
                break

    # Author-only: reveals_clue with clues present but non-investigate type and unresolved ref
    valid_refs = _valid_clue_refs_extended(inner, world)
    interactables = inner.get("interactables") or []
    for idx, i in enumerate(interactables):
        if not isinstance(i, dict):
            continue
        iid = str(i.get("id") or "interactable").strip()
        reveals = i.get("reveals_clue")
        if not reveals or not isinstance(reveals, str) or not reveals.strip():
            continue
        if not valid_refs:
            continue
        i_type = (i.get("type") or "").strip().lower()
        if i_type == "investigate":
            continue
        r_raw = reveals.strip()
        r_slug = slugify(r_raw) or ""
        if r_slug in valid_refs or r_raw in valid_refs:
            continue
        out.append(
            ContentLintMessage(
                severity="warning",
                code="interactable.clue_ref_non_investigate",
                message=(
                    f"Interactable '{iid}' has reveals_clue that does not resolve to a known clue "
                    f"(non-investigate types are not validated at runtime) in scene '{scene_id}'"
                ),
                scene_id=scene_id,
                path=f"scene.interactables[{idx}].reveals_clue",
                evidence={"interactable_id": iid, "reveals_clue": r_raw, "type": i_type or None},
            )
        )

    return out


def lint_scene_heuristic_warnings(
    scene_envelope: Dict[str, Any],
    scene_id: str,
    known_scene_ids: Set[str],
) -> List[ContentLintMessage]:
    """Translate :mod:`game.scene_lint` warnings into canonical codes (errors are covered by strict validation)."""
    raw = scene_lint.validate_scene(scene_envelope, known_scene_ids)
    inner = _scene_inner(scene_envelope)
    sid = str(inner.get("id") or scene_id or "<unknown>")
    out: List[ContentLintMessage] = []

    for w in raw.get("warnings") or []:
        wlow = str(w).lower()
        if "very similar to a visible fact" in wlow and "discoverable" in wlow:
            code = "clue.similar_to_visible"
        elif "very similar to a visible fact" in wlow and "hidden" in wlow:
            code = "hidden.similar_to_visible"
        elif "may directly state a hidden fact" in wlow:
            code = "clue.overlaps_hidden_fact"
        elif "no visible facts and no exits" in wlow:
            code = "scene.missing_player_anchor"
        elif "sensory grounding" in wlow:
            code = "scene.missing_sensory_grounding"
        else:
            code = "scene.heuristic_warning"
        out.append(
            ContentLintMessage(
                severity="warning",
                code=code,
                message=str(w),
                scene_id=sid if sid != "<unknown>" else str(scene_id),
                evidence={"source": "scene_lint"},
            )
        )

    # Dedupe clue.overlaps_hidden_fact if already emitted by clue pass (same scene)
    # Caller merges messages; optional dedupe in merge_report

    return out


def lint_scene_graph_connectivity(
    *,
    known_scene_ids: Set[str],
    load_scene_fn: Callable[[str], Dict[str, Any]],
    graph_seed_scene_ids: Optional[List[str]] = None,
) -> List[ContentLintMessage]:
    """Graph build, load/orphan hints, optional unreachable warnings (multi-scene aggregation)."""

    def _list_ids() -> List[str]:
        return sorted(known_scene_ids)

    messages: List[ContentLintMessage] = []

    graph = scene_graph.build_scene_graph(_list_ids, load_scene_fn)

    for sid in sorted(known_scene_ids):
        try:
            env = load_scene_fn(sid)
        except Exception as exc:  # noqa: BLE001 — author tooling surfaces load failures
            messages.append(
                ContentLintMessage(
                    severity="warning",
                    code="graph.scene_load_failed",
                    message=f"Could not load scene '{sid}' while building graph: {exc}",
                    scene_id=sid,
                    path="graph",
                    evidence={"error": str(exc)},
                )
            )
            continue
        inner = _scene_inner(env)
        if not inner:
            messages.append(
                ContentLintMessage(
                    severity="warning",
                    code="graph.missing_scene_body",
                    message=f"Scene '{sid}' envelope has no usable inner 'scene' for graph",
                    scene_id=sid,
                    path="scene",
                )
            )
            continue

    # Unreachable scenes from seeds (warning-only)
    seeds: List[str] = []
    if graph_seed_scene_ids is not None:
        seeds = [str(s).strip() for s in graph_seed_scene_ids if str(s).strip() in known_scene_ids]
    elif known_scene_ids:
        seeds = [sorted(known_scene_ids)[0]]

    if seeds:
        reachable: Set[str] = set()
        stack = list(seeds)
        while stack:
            cur = stack.pop()
            if cur in reachable:
                continue
            reachable.add(cur)
            for nxt in graph.get(cur, set()):
                if nxt not in reachable:
                    stack.append(nxt)
        for sid in sorted(known_scene_ids):
            if sid not in reachable:
                messages.append(
                    ContentLintMessage(
                        severity="warning",
                        code="graph.unreachable_scene",
                        message=f"Scene '{sid}' is not reachable from graph seeds {seeds!r}",
                        scene_id=sid,
                        path="graph",
                        evidence={"seeds": list(seeds)},
                    )
                )

    return messages


def _merge_messages(parts: List[List[ContentLintMessage]]) -> List[ContentLintMessage]:
    """Stable merge with dedupe on (severity, code, scene_id, path, message)."""
    seen: Set[tuple[Any, ...]] = set()
    out: List[ContentLintMessage] = []
    for group in parts:
        for m in group:
            key = (m.severity, m.code, m.scene_id, m.path, m.message)
            if key in seen:
                continue
            seen.add(key)
            out.append(m)
    return out


def lint_all_content(
    scenes: Dict[str, Dict[str, Any]],
    *,
    world: Optional[Dict[str, Any]] = None,
    campaign: Optional[Dict[str, Any]] = None,
    graph_seed_scene_ids: Optional[List[str]] = None,
    reference_known_scene_ids: Optional[Set[str]] = None,
    graph_known_scene_ids: Optional[Set[str]] = None,
) -> ContentLintReport:
    """Run all passes over an in-memory scene map (scene_id -> envelope).

    **Scopes (formal):**

    1. **Loaded bundle** — the ``scenes`` mapping plus optional ``world`` / ``campaign``.
       Per-scene passes only iterate ``scenes`` keys.

    2. **Reference registry** — ``reference_known_scene_ids`` when passed, else
       ``set(scenes.keys())``. Used for strict exit/action targets, heuristics, and (via
       :func:`build_content_bundle`) the bundle world↔scene link registry so subset runs
       do not false-positive on on-disk neighbors.

    3. **Validation** — scene strict rules use (2). Graph reachability uses
       ``graph_known_scene_ids`` (default (2)); pass ``set(scenes.keys())`` in subset mode
       so ``graph.unreachable_scene`` is evaluated only among loaded scenes. Bundle
       campaign/NPC scene fields use the same registry as (2); nothing is silently
       suppressed: an id errors only if missing from that resolved registry.

    ``campaign`` — optional campaign metadata dict for bundle checks (e.g.
    ``campaign.starting_scene_id`` when present); does not affect scene-only runs when omitted.
    """
    reference_known = set(reference_known_scene_ids) if reference_known_scene_ids is not None else set(scenes.keys())
    graph_known = set(graph_known_scene_ids) if graph_known_scene_ids is not None else set(reference_known)
    scene_ids_checked = sorted(scenes.keys())
    all_parts: List[List[ContentLintMessage]] = []

    for sid in scene_ids_checked:
        env = scenes[sid]
        issues = validation.collect_scene_validation_issues(env, sid, reference_known)
        all_parts.append([_validation_issue_to_message(e) for e in issues])
        all_parts.append(lint_scene_clue_integrity(env, sid, world=world))
        all_parts.append(lint_scene_heuristic_warnings(env, sid, reference_known))

    def _load(s: str) -> Dict[str, Any]:
        if s not in scenes:
            return {}
        return scenes[s]

    all_parts.append(
        lint_scene_graph_connectivity(
            known_scene_ids=graph_known,
            load_scene_fn=_load,
            graph_seed_scene_ids=graph_seed_scene_ids,
        )
    )

    bundle = build_content_bundle(
        scenes,
        world=world,
        campaign=campaign,
        world_scene_registry_ids=sorted(reference_known),
    )
    all_parts.append(lint_bundle_governance(bundle))

    messages = _merge_messages(all_parts)
    err = sum(1 for m in messages if m.severity == "error")
    warn = sum(1 for m in messages if m.severity == "warning")
    return ContentLintReport(
        ok=err == 0,
        error_count=err,
        warning_count=warn,
        messages=messages,
        scene_ids_checked=scene_ids_checked,
    )
