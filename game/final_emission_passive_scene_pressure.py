"""Passive scene pressure visibility fallback helpers.

Due-check and candidate-building for passive-action streak pressure beats.
Does not own fallback ordering inside gate visibility routing.
"""
from __future__ import annotations

from typing import Any, Dict, List

from game.final_emission_text import _normalize_text
from game.final_emission_visibility_fallback import (
    VisibilitySelectedFallback,
    first_mention_composition_meta as _first_mention_composition_meta,
)
from game.storage import get_scene_runtime


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for item in items:
        if not item or item in seen:
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


def _passive_scene_pressure_due_for_fallback(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
) -> bool:
    if not isinstance(session, dict):
        return False
    sid = str(scene_id or "").strip()
    if not sid:
        return False
    runtime = get_scene_runtime(session, sid)
    passive_streak = int(runtime.get("passive_action_streak", 0) or 0) if isinstance(runtime, dict) else 0
    last_player_action_passive = bool(runtime.get("last_player_action_passive")) if isinstance(runtime, dict) else False
    if not last_player_action_passive and passive_streak <= 0:
        return False
    visible_low = " ".join(fact.lower() for fact in _scene_visible_facts(scene))
    recent = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    return bool(
        passive_streak >= 2
        or isinstance(recent, list)
        and any(isinstance(item, dict) for item in recent)
        or "guard" in visible_low
        or "watch" in visible_low
        or "missing patrol" in visible_low
        or "rumor" in visible_low
        or "rumour" in visible_low
    )


def _reply_already_has_concrete_interaction(text: str) -> bool:
    clean = str(text or "").strip()
    if not clean:
        return False
    return any(pattern.search(clean) for pattern in _CONCRETE_INTERACTION_PATTERNS)


def _passive_scene_pressure_visibility_candidate(
    text: str,
    *,
    fallback_kind: str,
    fallback_candidate_source: str,
) -> VisibilitySelectedFallback:
    """Build one passive-scene-pressure visibility fallback candidate (canonical dataclass wire)."""
    return VisibilitySelectedFallback(
        text=_output_sentence(text),
        fallback_pool="passive_scene_pressure",
        fallback_kind=fallback_kind,
        final_emitted_source="passive_scene_pressure_fallback",
        fallback_strategy="passive_scene_pressure_fallback",
        fallback_candidate_source=fallback_candidate_source,
        composition_meta=_first_mention_composition_meta(),
    )


def _passive_scene_pressure_fallback_candidates(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
) -> List[VisibilitySelectedFallback]:
    if not _passive_scene_pressure_due_for_fallback(session=session, scene=scene, scene_id=scene_id):
        return []

    sid = str(scene_id or "").strip()
    runtime = get_scene_runtime(session, sid) if isinstance(session, dict) and sid else {}
    passive_streak = int(runtime.get("passive_action_streak", 0) or 0) if isinstance(runtime, dict) else 0
    recent = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    if isinstance(recent, list):
        for lead in reversed(recent[-4:]):
            if not isinstance(lead, dict):
                continue
            kind = str(lead.get("kind") or "").strip()
            if kind not in {"visible_suspicious_figure", "recent_named_figure", "visible_named_figure"}:
                continue
            subject = _normalize_text(lead.get("subject"))
            position = _normalize_text(lead.get("position"))
            if not subject:
                continue
            move_from = f" leaves {position} and" if position else ""
            if passive_streak >= 2:
                return [
                    _passive_scene_pressure_visibility_candidate(
                        f'{subject}{move_from} comes straight to you before the pause can settle. "Enough watching," they say. "Ask me now, or lose the trail."',
                        fallback_kind="passive_scene_pressure_lead_figure",
                        fallback_candidate_source="passive_scene_pressure:lead_figure",
                    )
                ]
            return [
                _passive_scene_pressure_visibility_candidate(
                    f'{subject}{move_from} cuts through the crowd and stops at your shoulder. "You\'re asking the wrong questions out loud," they murmur. "Walk with me if you want the next name."',
                    fallback_kind="passive_scene_pressure_lead_figure",
                    fallback_candidate_source="passive_scene_pressure:lead_figure",
                )
            ]

    visible_facts = _scene_visible_facts(scene)
    visible_low = " ".join(fact.lower() for fact in visible_facts)
    if "guard" in visible_low and "missing patrol" in visible_low:
        if passive_streak >= 2:
            text = (
                'The same guard does not let the silence stand a second time. "No more watching," he says, '
                "closing the distance and jabbing a finger at the east-road line on the notice. "
                '"Either tell me who sent you, or get moving before that trail cools for good."'
            )
        else:
            text = (
                'A guard peels away from the notice board and squares up to you. "Standing still won\'t help that patrol," '
                'he says, stabbing two fingers at the posting. "Tell me what you know, or get on the east-road trail before it dies."'
            )
        return [
            _passive_scene_pressure_visibility_candidate(
                text,
                fallback_kind="passive_scene_pressure_guard_rumor",
                fallback_candidate_source="passive_scene_pressure:guard_rumor",
            )
        ]
    if "guard" in visible_low:
        text = (
            'A guard notices you lingering and comes over at once. "If you\'re waiting on trouble, it already passed the checkpoint," '
            'he says. "Take the east-road report or get clear."'
        )
        return [
            _passive_scene_pressure_visibility_candidate(
                text,
                fallback_kind="passive_scene_pressure_visible_figure",
                fallback_candidate_source="passive_scene_pressure:visible_figure",
            )
        ]
    return [
        _passive_scene_pressure_visibility_candidate(
            'The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose. '
            '"Board, runner, or road," he says. "Pick one before the gate swallows the trail."',
            fallback_kind="passive_scene_pressure_generic",
            fallback_candidate_source="passive_scene_pressure:fallback",
        )
    ]
