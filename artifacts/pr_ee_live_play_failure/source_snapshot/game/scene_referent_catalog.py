"""Canonical referents already present in scene, world, and discourse records.

This is an index for interpretation validation. It does not copy those records
into a second world model, and it does not read hidden facts.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence


def _clean(value: Any, *, limit: int = 120) -> str:
    return " ".join(str(value or "").split())[:limit]


def _aliases(row: Mapping[str, Any]) -> list[str]:
    found: list[str] = []
    for key in ("aliases", "address_roles"):
        raw = row.get(key)
        if not isinstance(raw, list):
            continue
        for item in raw:
            text = _clean(item, limit=80)
            if text and text not in found:
                found.append(text)
    return found


def _add(
    rows: list[dict[str, Any]],
    seen: set[tuple[str, str]],
    *,
    kind: str,
    ident: str,
    label: str,
    aliases: Sequence[str] = (),
    source: str,
) -> None:
    ident = _clean(ident, limit=80)
    label = _clean(label, limit=120) or ident
    if not ident and not label:
        return
    key = (kind, ident or label)
    alias_list = [item for item in aliases if _clean(item, limit=80)]
    if key in seen:
        for row in rows:
            if row["type"] == kind and row["id"] == (ident or label):
                for alias in alias_list:
                    if alias not in row["aliases"]:
                        row["aliases"].append(alias)
                return
        return
    seen.add(key)
    rows.append(
        {
            "type": kind,
            "id": ident or label,
            "label": label,
            "aliases": alias_list,
            "source": source,
        }
    )


def _scene_body(scene: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(scene, Mapping):
        return {}
    inner = scene.get("scene")
    if isinstance(inner, Mapping):
        return inner
    return scene


def _extend_object_rows(rows: list[dict[str, Any]], seen: set[tuple[str, str]], items: Any, *, source: str) -> None:
    if not isinstance(items, list):
        return
    for item in items:
        if isinstance(item, str):
            _add(rows, seen, kind="object", ident=item, label=item, source=source)
            continue
        if not isinstance(item, Mapping):
            continue
        ident = _clean(item.get("id") or item.get("target_id"), limit=80)
        label = _clean(item.get("label") or item.get("name") or ident, limit=120)
        _add(rows, seen, kind="object", ident=ident, label=label, aliases=_aliases(item), source=source)


def build_canonical_referent_catalog(
    *,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    scene_id: str | None = None,
) -> list[dict[str, Any]]:
    """Referents the validator may accept on this turn.

    Includes the current place, public exits, scene interactables and objects,
    and NPCs already on the scene roster. Discourse slots are added by the
    validator from the focus it already reads. Hidden facts are omitted.
    """
    body = _scene_body(scene)
    current = _clean(scene_id or body.get("id"), limit=80)
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    if current or body.get("location"):
        _add(
            rows,
            seen,
            kind="place",
            ident=current or _clean(body.get("location"), limit=80),
            label=_clean(body.get("location"), limit=120) or current,
            source="scene",
        )
    _extend_object_rows(rows, seen, body.get("interactables"), source="scene")
    _extend_object_rows(rows, seen, body.get("objects"), source="scene")
    exits = body.get("exits")
    if isinstance(exits, list):
        for exit_row in exits:
            if not isinstance(exit_row, Mapping):
                continue
            _add(
                rows,
                seen,
                kind="place",
                ident=_clean(exit_row.get("target_scene_id") or exit_row.get("id"), limit=80),
                label=_clean(exit_row.get("label") or exit_row.get("target_scene_id"), limit=120),
                source="scene",
            )
    addressables = body.get("addressables")
    if isinstance(addressables, list):
        for actor in addressables:
            if not isinstance(actor, Mapping):
                continue
            if actor.get("addressable") is False:
                continue
            _add(
                rows,
                seen,
                kind="interlocutor",
                ident=_clean(actor.get("id"), limit=80),
                label=_clean(actor.get("name") or actor.get("label") or actor.get("id"), limit=120),
                aliases=_aliases(actor),
                source="scene",
            )
    if current and isinstance(world, Mapping):
        from game.interaction_context import scene_npcs_in_active_scene

        envelope = scene if isinstance(scene, Mapping) and isinstance(scene.get("scene"), Mapping) else {"scene": dict(body)}
        for npc in scene_npcs_in_active_scene(envelope, dict(world)):
            if not isinstance(npc, Mapping):
                continue
            _add(
                rows,
                seen,
                kind="interlocutor",
                ident=_clean(npc.get("id"), limit=80),
                label=_clean(npc.get("name") or npc.get("id"), limit=120),
                aliases=_aliases(npc),
                source="scene",
            )
    from game.incidental_entity import incidental_catalog_rows

    for row in incidental_catalog_rows(session, current):
        _add(
            rows,
            seen,
            kind="interlocutor",
            ident=str(row.get("id") or ""),
            label=str(row.get("label") or ""),
            aliases=row.get("aliases") or (),
            source="bounded_incidental",
        )
    return rows
