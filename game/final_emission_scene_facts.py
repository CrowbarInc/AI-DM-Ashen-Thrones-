"""Runtime scene visible-fact extraction and augmentation helpers.

Pure visible-fact normalization and runtime contextual-lead augmentation for
visibility validation. Does not own gate validation ordering or fallback routing.
"""
from __future__ import annotations

from typing import Any, Dict, List

from game.anti_reset_emission_guard import _opening_scene_preference_active
from game.final_emission_text import _normalize_text
from game.storage import get_scene_runtime


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in items:
        if not isinstance(item, str) or not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _scene_inner(scene: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(scene, dict):
        return {}
    inner = scene.get("scene")
    if isinstance(inner, dict):
        return inner
    return scene


def _output_sentence(text: str) -> str:
    clean = _normalize_text(text)
    if not clean:
        return ""
    if clean[-1] not in ".!?":
        clean += "."
    return clean


def _scene_visible_facts(scene: Dict[str, Any] | None) -> List[str]:
    inner = _scene_inner(scene)
    raw = inner.get("visible_facts")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        clean = _output_sentence(item)
        if clean:
            out.append(clean)
    return _dedupe_preserve_order(out)


def _augment_scene_with_runtime_visible_leads(
    scene: Dict[str, Any] | None,
    *,
    session: Dict[str, Any] | None,
    scene_id: str,
) -> Dict[str, Any] | None:
    if not isinstance(scene, dict):
        return scene
    if not isinstance(session, dict):
        return scene
    if _opening_scene_preference_active(session):
        return scene
    sid = str(scene_id or "").strip()
    if not sid:
        return scene
    runtime = get_scene_runtime(session, sid)
    recent = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    if not isinstance(recent, list) or not recent:
        return scene

    extra_facts: List[str] = []
    for lead in recent[-4:]:
        if not isinstance(lead, dict):
            continue
        kind = str(lead.get("kind") or "").strip()
        if kind not in {"visible_suspicious_figure", "recent_named_figure", "visible_named_figure"}:
            continue
        subject = _normalize_text(lead.get("subject"))
        position = _normalize_text(lead.get("position"))
        if not subject:
            continue
        fact = f"{subject} lingers {position}" if position else f"{subject} lingers nearby"
        extra_facts.append(_output_sentence(fact))

    if not extra_facts:
        return scene

    if isinstance(scene.get("scene"), dict):
        outer = dict(scene)
        outer.pop("_is_canon", None)
        inner = dict(scene.get("scene") or {})
        existing = _scene_visible_facts(scene)
        inner["visible_facts"] = _dedupe_preserve_order(existing + extra_facts)
        outer["scene"] = inner
        return outer

    inner = dict(scene)
    inner.pop("_is_canon", None)
    existing = _scene_visible_facts(scene)
    inner["visible_facts"] = _dedupe_preserve_order(existing + extra_facts)
    return inner
